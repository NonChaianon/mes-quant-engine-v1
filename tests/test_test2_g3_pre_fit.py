from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from mes_quant.exploration import l1_lr001, l1_tree001
from mes_quant.exploration import test2_diagnostics as diagnostics
from mes_quant.exploration import test2_evaluation as evaluation
from mes_quant.exploration import test2_stats as stats
from mes_quant.exploration.test2_evaluation import preflight_evaluation
from mes_quant.exploration.test2_g3_contract import (
    CELL12_FULL_COVERAGE_PASS,
    CELL12_STATUS_PATH_INTEGRITY_FAILURE,
    CELL12_STATUS_USABLE,
    DISPOSITION_DEFERRED_PENDING_G3F,
    DISPOSITION_INCONCLUSIVE_UNDERPOWERED,
    G3_AUTHORIZED_BASE_COMMIT,
    G3_BRANCH,
    G3F_STATUS,
    G3I_ALLOWED_CHANGED_FILES,
    PINNED_DOC_SHA256,
    SUPPORT_GATE_FAIL_UNDERPOWERED,
    SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
    TEST2_G3_PACKAGE_PATH,
    G3FNotAuthorizedError,
    assert_g3f_not_authorized,
    changed_file_firewall_failures,
    support_outcome,
)
from mes_quant.exploration.test2_g3_pre_fit import (
    G3P_PATH_BAR_BATCH_SIZE,
    G3PreFitEvidence,
    assemble_g3p_pre_fit_record,
    collect_g3p_pre_fit_evidence,
    pre_fit_only_guard,
    resolve_doc_bindings,
    terminal_witness_lines,
    write_g3p_pre_fit_record,
)
from mes_quant.exploration.test2_g3_pre_fit import (
    G3PreFitBoundaryError as PreFitBoundaryError,
)
from mes_quant.exploration.test2_l1_harness import (
    ArtifactMetadataEvidence,
    CanonicalArtifactPaths,
    Cell12PathExpectation,
    DecodedFrameIdentityEvidence,
    MetadataIdentityPreflight,
    VectorizedDataFramePathBarProvider,
    assemble_fold_evaluation_data,
    build_train_path_targets,
    prepare_train_inputs,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_RELEASE_MANIFEST_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    FROZEN_COLAB_MANIFEST_SHA256,
    ORDERED_FEATURE_CONTENT_SHA256,
    OUTER_TRAIN_ROLE,
    PATH_BAR_COUNT,
    RAW_DBN_SHA256,
)
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    build_streaming_request_set,
)
from mes_quant.exploration.test2_run_context import (
    FIT_STATUS_BLOCKED_FIT_NOT_AUTHORIZED,
    FIT_STATUS_SKIPPED_INCONCLUSIVE_UNDERPOWERED,
)
from mes_quant.exploration.test2_stats import SupportGateResult
from mes_quant.features.contract import FEATURE_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CODE_IDENTITY = "1" * 40
FIXED_AUDIT_UTC = "2026-08-23T00:00:00Z"

# ---------------------------------------------------------------------------
# Synthetic canonical-shaped fixture
#
# Everything below is generated in memory. No real DBN, Parquet, artifact, or
# numeric source row is opened anywhere in this module.
# ---------------------------------------------------------------------------

BASE_TICKS = 20_000  # 5,000.00 points on the 0.25 grid
SESSIONS_PER_YEAR = 24
DECISION_MINUTE_OFFSETS = (0, 15, 30)
SESSION_MINUTES = DECISION_MINUTE_OFFSETS[-1] + PATH_BAR_COUNT
FOLD_YEARS = (2021, 2022, 2023)
NATIVE_INSTRUMENT_ID = 123
# Minute 5 of session 0 belongs only to that session's 14:30 decision window,
# so dropping it makes exactly one decision's path incomplete.
DROPPED_SESSION_INDEX = 0
DROPPED_MINUTE = 5


def _level_ticks(session_index: int, minute: int) -> int:
    return BASE_TICKS + ((session_index * 7 + minute * 3) % 41) - 20


def _session_starts() -> tuple[datetime, ...]:
    starts: list[datetime] = []
    for year in FOLD_YEARS:
        cursor = datetime(year, 3, 1, 14, 30, tzinfo=UTC)
        collected = 0
        while collected < SESSIONS_PER_YEAR:
            if cursor.weekday() < 5:
                starts.append(cursor)
                collected += 1
            cursor += timedelta(days=1)
    return tuple(starts)


def _roles(year: int) -> tuple[str, str]:
    if year == 2021:
        return "TRAIN", "TRAIN"
    if year == 2022:
        return "VALIDATION", "TRAIN"
    return "UNUSED", "VALIDATION"


@lru_cache(maxsize=1)
def _synthetic_inputs() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Cell12PathExpectation]
]:
    session_starts = _session_starts()
    bar_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    assignment_rows: list[dict[str, object]] = []
    expectations: dict[str, Cell12PathExpectation] = {}

    for session_index, session_start in enumerate(session_starts):
        for minute in range(SESSION_MINUTES):
            if session_index == DROPPED_SESSION_INDEX and minute == DROPPED_MINUTE:
                continue
            level = _level_ticks(session_index, minute)
            bar_rows.append(
                {
                    "ts_event": session_start + timedelta(minutes=minute),
                    "open": level / 4.0,
                    "high": (level + 1) / 4.0,
                    "low": (level - 1) / 4.0,
                    "close": level / 4.0,
                    "instrument_id": NATIVE_INSTRUMENT_ID,
                }
            )

    decision_index = 0
    for session_index, session_start in enumerate(session_starts):
        role_2022, role_2023 = _roles(session_start.year)
        for entry_minute in DECISION_MINUTE_OFFSETS:
            identity = f"D{decision_index:05d}"
            decision_time = session_start + timedelta(minutes=entry_minute)
            entry_ticks = _level_ticks(session_index, entry_minute)
            endpoint_ticks = _level_ticks(session_index, entry_minute + PATH_BAR_COUNT - 1)
            path_minutes = range(entry_minute, entry_minute + PATH_BAR_COUNT)
            incomplete = session_index == DROPPED_SESSION_INDEX and (
                DROPPED_MINUTE in path_minutes
            )

            feature_row: dict[str, object] = {
                "decision_id": identity,
                "decision_time": decision_time,
                "nyse_session_date": session_start.date().isoformat(),
                "instrument_id": NATIVE_INSTRUMENT_ID,
                "outer_partition": OUTER_TRAIN_ROLE,
                "role_wf_2022": role_2022,
                "role_wf_2023": role_2023,
                "role_wf_2024": "UNUSED",
                "feature_row_usable": True,
                "feature_status": "USABLE",
                "feature_lookback_start_utc": decision_time - timedelta(days=2),
                "feature_max_source_time_utc": decision_time,
            }
            for position, name in enumerate(FEATURE_COLUMNS):
                feature_row[name] = float(position) + 0.001 * (decision_index % 29)
            feature_row["realized_vol_60m"] = 0.001 * ((decision_index % 17) + 1)
            feature_rows.append(feature_row)

            label_rows.append(
                {
                    "decision_id": identity,
                    "decision_time": decision_time,
                    "instrument_id": NATIVE_INSTRUMENT_ID,
                    "outer_partition": OUTER_TRAIN_ROLE,
                    "role_wf_2022": role_2022,
                    "role_wf_2023": role_2023,
                    "entry_reference_close": entry_ticks / 4.0,
                    "exit_reference_close_60m": endpoint_ticks / 4.0,
                }
            )
            assignment_rows.append(
                {
                    "decision_id": identity,
                    "decision_time": decision_time,
                    "instrument_id": NATIVE_INSTRUMENT_ID,
                    "outer_partition": OUTER_TRAIN_ROLE,
                    "role_wf_2022": role_2022,
                    "role_wf_2023": role_2023,
                }
            )

            if incomplete:
                expectations[identity] = Cell12PathExpectation(
                    decision_identity=identity,
                    path_status=CELL12_STATUS_PATH_INTEGRITY_FAILURE,
                    path_usable=False,
                    path_1m_present=PATH_BAR_COUNT - 1,
                    path_high_60m=None,
                    path_low_60m=None,
                    long_mfe_points_60m=None,
                    long_mae_points_60m=None,
                )
            else:
                levels = [_level_ticks(session_index, minute) for minute in path_minutes]
                high_ticks = max(levels) + 1
                low_ticks = min(levels) - 1
                expectations[identity] = Cell12PathExpectation(
                    decision_identity=identity,
                    path_status=CELL12_STATUS_USABLE,
                    path_usable=True,
                    path_1m_present=PATH_BAR_COUNT,
                    path_high_60m=high_ticks / 4.0,
                    path_low_60m=low_ticks / 4.0,
                    long_mfe_points_60m=max(high_ticks - entry_ticks, 0) / 4.0,
                    long_mae_points_60m=max(entry_ticks - low_ticks, 0) / 4.0,
                )
            decision_index += 1

    decoded = pd.DataFrame(bar_rows).set_index("ts_event")
    features = pd.DataFrame(feature_rows)
    labels = pd.DataFrame(label_rows)
    # Stand in for the marker `read_train_only_parquet` stamps after pushing the
    # `outer_partition == TRAIN` predicate into the physical Parquet read.
    for frame in (features, labels):
        frame.attrs["test2_physical_outer_partition_filter"] = OUTER_TRAIN_ROLE
    return features, labels, pd.DataFrame(assignment_rows), decoded, expectations


def _synthetic_metadata() -> MetadataIdentityPreflight:
    hashes = {
        "raw_dbn": RAW_DBN_SHA256,
        "cell8_assignments": CELL8_SPLIT_ASSIGNMENT_SHA256,
        "cell10_labels": CELL10_LABEL_SHA256,
        "cell12_paths": CELL12_PATH_SHA256,
        "cell14_features": FEATURE_ARTIFACT_SHA256,
    }
    return MetadataIdentityPreflight(
        release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
        artifacts=tuple(
            ArtifactMetadataEvidence(
                artifact_id=artifact_id,
                path=f"${{MES_G3_ARTIFACTS}}/{artifact_id}",
                byte_sha256=sha256,
                parquet_row_count=None if artifact_id == "raw_dbn" else 1,
                parquet_schema=(),
                manifest_artifact_id=artifact_id,
            )
            for artifact_id, sha256 in hashes.items()
        ),
        control_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
        ordered_feature_content_sha256_declared=ORDERED_FEATURE_CONTENT_SHA256,
    )


def _synthetic_decoded_identity() -> DecodedFrameIdentityEvidence:
    return DecodedFrameIdentityEvidence(
        content_sha256=DECODED_MES_1M_SHA256,
        row_count=2_551_123,
        timestamp_min_utc="2019-05-05T22:00:00+00:00",
        timestamp_max_utc="2026-07-31T20:59:00+00:00",
    )


@lru_cache(maxsize=1)
def _synthetic_evidence() -> G3PreFitEvidence:
    features, labels, assignments, decoded, expectations = _synthetic_inputs()
    prepared = prepare_train_inputs(features, labels, assignments=assignments)
    sealed = build_streaming_request_set(
        tuple(
            ParentDecision(
                decision.decision_identity,
                decision.decision_time_utc,
                OUTER_TRAIN_ROLE,
            )
            for decision in prepared.path_decisions
        ),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    provider = VectorizedDataFramePathBarProvider(
        decoded,
        sealed=sealed,
        expected_native_instruments={
            decision.decision_identity: decision.expected_native_instrument
            for decision in prepared.path_decisions
        },
    )
    targets = build_train_path_targets(
        sealed,
        prepared.path_decisions,
        provider,
        batch_size=G3P_PATH_BAR_BATCH_SIZE,
        cell12_expectations=expectations,
    )
    assembly = assemble_fold_evaluation_data(prepared, targets)
    return G3PreFitEvidence(
        metadata=_synthetic_metadata(),
        decoded_identity=_synthetic_decoded_identity(),
        cell14_run_binding={
            "resolved_features_run_id": "SYNTHETIC_RUN",
            "resolved_features_role": "canonical",
            "run_binding_status": "MATCHED_RELEASE_DECLARATION",
        },
        prepared=prepared,
        sealed=sealed,
        targets=targets,
        assembly=assembly,
        preflight=preflight_evaluation(assembly.folds),
    )


def _record(
    evidence: G3PreFitEvidence | None = None,
    **overrides: object,
) -> dict[str, object]:
    with pre_fit_only_guard() as guard:
        witness = guard.witness()
    arguments: dict[str, object] = {
        "code_identity": SYNTHETIC_CODE_IDENTITY,
        "branch": G3_BRANCH,
        "doc_bindings": resolve_doc_bindings(PROJECT_ROOT),
        "guard_witness": witness,
        "audit_written_utc": FIXED_AUDIT_UTC,
    }
    arguments.update(overrides)
    return assemble_g3p_pre_fit_record(evidence or _synthetic_evidence(), **arguments)


class G3ContractTests(unittest.TestCase):
    def test_allowlist_is_the_exact_eleven_file_g3i_surface(self) -> None:
        expected = {
            "docs/research/TEST2_G3_PACKAGE_V1.md",
            "src/mes_quant/exploration/test2_decode.py",
            "src/mes_quant/exploration/test2_g3_contract.py",
            "src/mes_quant/exploration/test2_g3_pre_fit.py",
            "src/mes_quant/exploration/test2_l1_harness.py",
            "src/mes_quant/exploration/test2_run_context.py",
            "tests/test_test2_decode.py",
            "tests/test_test2_g3_pre_fit.py",
            "tests/test_test2_l1_harness.py",
            "tests/test_test2_run_context.py",
            "tools/run_test2_g3p_pre_fit.py",
        }
        self.assertEqual(set(G3I_ALLOWED_CHANGED_FILES), expected)
        self.assertEqual(len(G3I_ALLOWED_CHANGED_FILES), 11)
        for relative in G3I_ALLOWED_CHANGED_FILES:
            self.assertTrue((PROJECT_ROOT / relative).is_file(), relative)

    def test_frozen_science_files_are_outside_the_allowlist(self) -> None:
        for protected in (
            "src/mes_quant/exploration/test2_target.py",
            "src/mes_quant/exploration/test2_stats.py",
            "src/mes_quant/exploration/test2_evaluation.py",
            "src/mes_quant/exploration/test2_metadata_preflight.py",
            "src/mes_quant/exploration/test2_diagnostics.py",
            "src/mes_quant/exploration/test2_request_set.py",
            "src/mes_quant/exploration/test2_path_contract.py",
        ):
            self.assertNotIn(protected, G3I_ALLOWED_CHANGED_FILES)

    def test_changed_file_firewall_reports_both_deviation_kinds(self) -> None:
        self.assertEqual(changed_file_firewall_failures(G3I_ALLOWED_CHANGED_FILES), ())
        failures = changed_file_firewall_failures(
            set(G3I_ALLOWED_CHANGED_FILES)
            | {"src/mes_quant/exploration/test2_target.py"}
        )
        self.assertEqual(len(failures), 1)
        self.assertIn("test2_target.py", failures[0])
        dropped = set(G3I_ALLOWED_CHANGED_FILES)
        dropped.discard("tools/run_test2_g3p_pre_fit.py")
        self.assertTrue(
            any("missing" in failure for failure in changed_file_firewall_failures(dropped))
        )

    def test_g3f_remains_unauthorized_and_unimplemented(self) -> None:
        self.assertEqual(G3F_STATUS, "NOT_AUTHORIZED")
        with self.assertRaisesRegex(G3FNotAuthorizedError, "NOT_AUTHORIZED"):
            assert_g3f_not_authorized()
        with self.assertRaises(G3FNotAuthorizedError):
            assert_g3f_not_authorized("PATHFULL001", fold="WF_2022")

    def test_support_outcome_never_authorizes_a_fit(self) -> None:
        self.assertEqual(
            support_outcome(True),
            (
                SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
                DISPOSITION_DEFERRED_PENDING_G3F,
                FIT_STATUS_BLOCKED_FIT_NOT_AUTHORIZED,
            ),
        )
        self.assertEqual(
            support_outcome(False),
            (
                SUPPORT_GATE_FAIL_UNDERPOWERED,
                DISPOSITION_INCONCLUSIVE_UNDERPOWERED,
                FIT_STATUS_SKIPPED_INCONCLUSIVE_UNDERPOWERED,
            ),
        )

    def test_document_bindings_match_the_tracked_repository(self) -> None:
        bindings = resolve_doc_bindings(PROJECT_ROOT)
        self.assertEqual(set(bindings), set(PINNED_DOC_SHA256))
        for relative in PINNED_DOC_SHA256:
            self.assertIs(bindings[relative]["match"], True)
        package = bindings[TEST2_G3_PACKAGE_PATH]
        self.assertEqual(package["expected"], PINNED_DOC_SHA256[TEST2_G3_PACKAGE_PATH])
        self.assertEqual(package["binding_status"], "PINNED_BEFORE_EXECUTION")

    def test_missing_tracked_document_fails_closed(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(PreFitBoundaryError, "document is missing"),
        ):
            resolve_doc_bindings(temporary)


class PreFitFitGuardTests(unittest.TestCase):
    def test_every_fit_bootstrap_and_economic_entry_point_is_blocked(self) -> None:
        blocked = (
            (evaluation, "fit_frozen_logistic"),
            (evaluation, "standardize_fold"),
            (evaluation, "run_authorized_train_evaluation"),
            (evaluation, "run_synthetic_evaluation"),
            (evaluation, "required_paired_bootstraps"),
            (evaluation, "build_economic_diagnostics"),
            (evaluation, "decide_continuation"),
            (stats, "paired_session_block_bootstrap"),
            (stats, "moving_block_indices"),
            (stats, "stepwise_average_precision"),
            (diagnostics, "build_economic_diagnostics"),
            (l1_lr001, "fit_frozen_logistic"),
            (l1_tree001, "fit_bounded_shallow_tree"),
        )
        with pre_fit_only_guard() as guard:
            for index, (module, name) in enumerate(blocked, start=1):
                with self.assertRaises(PreFitBoundaryError):
                    getattr(module, name)()
                self.assertEqual(guard.blocked_fit_calls, index)
            self.assertEqual(guard.witness()["guard_status"], "FAIL_BLOCKED_CALL_ATTEMPTED")

    def test_guard_restores_every_original_symbol_on_exit(self) -> None:
        originals = {
            (module.__name__, name): getattr(module, name)
            for module, name in (
                (evaluation, "fit_frozen_logistic"),
                (stats, "paired_session_block_bootstrap"),
                (diagnostics, "build_economic_diagnostics"),
                (l1_lr001, "fit_frozen_logistic"),
                (l1_tree001, "fit_bounded_shallow_tree"),
            )
        }
        with pre_fit_only_guard() as guard:
            self.assertNotEqual(
                evaluation.fit_frozen_logistic, originals[(evaluation.__name__, "fit_frozen_logistic")]
            )
            self.assertGreaterEqual(len(guard.installed_symbols), len(originals))
        self.assertEqual(
            evaluation.fit_frozen_logistic,
            originals[(evaluation.__name__, "fit_frozen_logistic")],
        )
        self.assertEqual(
            stats.paired_session_block_bootstrap,
            originals[(stats.__name__, "paired_session_block_bootstrap")],
        )
        self.assertEqual(
            l1_tree001.fit_bounded_shallow_tree,
            originals[(l1_tree001.__name__, "fit_bounded_shallow_tree")],
        )

    def test_guard_restores_symbols_when_a_required_symbol_is_missing(self) -> None:
        original_indices = stats.moving_block_indices
        original_fitter = evaluation.fit_frozen_logistic
        try:
            del stats.moving_block_indices
            with (
                self.assertRaisesRegex(PreFitBoundaryError, "fit-guard symbol is missing"),
                pre_fit_only_guard(),
            ):
                pass
        finally:
            stats.moving_block_indices = original_indices
        self.assertIs(stats.moving_block_indices, original_indices)
        # A partially installed guard must roll back every symbol it replaced
        # before the missing one, not leave the fit surface stubbed out.
        self.assertIs(evaluation.fit_frozen_logistic, original_fitter)

    def test_support_gate_evaluation_stays_available_inside_the_guard(self) -> None:
        evidence = _synthetic_evidence()
        with pre_fit_only_guard() as guard:
            preflight = preflight_evaluation(evidence.assembly.folds)
            self.assertEqual(guard.blocked_fit_calls, 0)
        self.assertEqual(preflight.real_models_fitted, 0)
        self.assertEqual(
            preflight.pooled_retained_sha256, evidence.preflight.pooled_retained_sha256
        )


class SyntheticPreFitEvidenceTests(unittest.TestCase):
    def test_synthetic_pipeline_reaches_the_support_gate_without_fitting(self) -> None:
        evidence = _synthetic_evidence()
        targets = evidence.targets
        self.assertEqual(targets.cell12_reconciliation_status, CELL12_FULL_COVERAGE_PASS)
        self.assertEqual(targets.cell12_absent_rows, 0)
        self.assertEqual(
            targets.cell12_expectation_rows, len(evidence.prepared.path_decisions)
        )
        self.assertEqual(targets.cell12_unusable_reconciled_rows, 1)
        self.assertEqual(
            targets.cell12_usable_reconciled_rows,
            len(evidence.prepared.path_decisions) - 1,
        )
        self.assertEqual(len(targets.path_metrics), len(targets.target_rows))
        self.assertEqual(targets.validation_path_bar_lookup_count, 0)
        self.assertEqual(targets.final_test_path_bar_lookup_count, 0)
        self.assertEqual(targets.missing_path_bar_keys, 1)
        self.assertEqual(targets.native_instrument_mismatch_keys, 0)
        self.assertTrue(evidence.prepared.cell8_role_binding_asserted)
        self.assertEqual(
            [fold.fold_id for fold in evidence.assembly.folds], ["WF_2022", "WF_2023"]
        )

    def test_unusable_cell12_row_reconciles_with_absent_numeric_fields(self) -> None:
        evidence = _synthetic_evidence()
        unusable = [
            metric
            for metric in evidence.targets.path_metrics
            if metric.cell12_path_usable is False
        ]
        self.assertEqual(len(unusable), 1)
        verdict = unusable[0]
        self.assertEqual(
            verdict.cell12_status,
            "EXACT_UNUSABLE_ABSENT_NUMERIC_FIELD_RECONCILIATION_PASS",
        )
        for value in (
            verdict.path_high_60m,
            verdict.path_low_60m,
            verdict.long_mfe_points_60m,
            verdict.long_mae_points_60m,
        ):
            self.assertIsNone(value)


class PreFitRecordTests(unittest.TestCase):
    def test_support_failure_records_inconclusive_underpowered_with_zero_fits(self) -> None:
        evidence = _synthetic_evidence()
        self.assertFalse(evidence.preflight.support_gate.passed)
        record = _record(evidence)
        self.assertEqual(record["disposition"], DISPOSITION_INCONCLUSIVE_UNDERPOWERED)
        self.assertEqual(record["support_gate"]["status"], SUPPORT_GATE_FAIL_UNDERPOWERED)
        self.assertEqual(
            record["fit_authorization"]["fit_status"],
            FIT_STATUS_SKIPPED_INCONCLUSIVE_UNDERPOWERED,
        )
        self.assertEqual(record["fit_authorization"]["real_models_fitted"], 0)
        self.assertTrue(record["support_gate"]["failures"])
        self.assertFalse(record["support_gate"]["floors_relaxed"])

    def test_support_pass_defers_to_g3f_and_still_records_zero_fits(self) -> None:
        evidence = _synthetic_evidence()
        passing = replace(
            evidence.preflight,
            support_gate=SupportGateResult(passed=True, failures=()),
        )
        record = _record(replace(evidence, preflight=passing))
        self.assertEqual(
            record["support_gate"]["status"], SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED
        )
        self.assertEqual(record["disposition"], DISPOSITION_DEFERRED_PENDING_G3F)
        fit_authorization = record["fit_authorization"]
        self.assertEqual(
            fit_authorization["fit_status"], FIT_STATUS_BLOCKED_FIT_NOT_AUTHORIZED
        )
        self.assertEqual(fit_authorization["real_models_fitted"], 0)
        self.assertEqual(fit_authorization["g3f_status"], G3F_STATUS)
        self.assertTrue(fit_authorization["stops_before_fit_on_support_pass"])
        self.assertTrue(fit_authorization["stops_before_fit_on_support_fail"])
        self.assertEqual(record["counters"]["real_models_fitted"], 0)
        self.assertEqual(record["counters"]["real_fold_fit_calls"], 0)
        self.assertEqual(record["counters"]["bootstrap_replicates"], 0)
        self.assertEqual(record["counters"]["economic_diagnostic_calls"], 0)

    def test_record_binds_branch_base_docs_identity_seal_and_counters(self) -> None:
        record = _record()
        self.assertEqual(record["branch"], G3_BRANCH)
        self.assertEqual(record["base_commit"], G3_AUTHORIZED_BASE_COMMIT)
        self.assertEqual(record["code_identity"], SYNTHETIC_CODE_IDENTITY)
        binding = record["authorization_binding"]
        self.assertEqual(
            set(binding["document_bindings"]),
            set(PINNED_DOC_SHA256),
        )
        self.assertEqual(
            sorted(binding["allowed_changed_files"]), sorted(G3I_ALLOWED_CHANGED_FILES)
        )
        self.assertEqual(
            record["metadata_identity"]["artifact_byte_sha256"]["raw_dbn"], RAW_DBN_SHA256
        )
        self.assertEqual(
            record["decoded_identity"]["content_sha256"], DECODED_MES_1M_SHA256
        )
        self.assertEqual(
            record["decoded_identity"]["decoded_content_status"],
            "RECOMPUTED_FULL_CANONICAL_CELL2_DECODE",
        )
        self.assertEqual(
            record["decoded_identity"]["hash_columns"],
            ["open", "high", "low", "close", "instrument_id"],
        )
        seal = record["request_seal"]
        self.assertEqual(
            seal["request_set_sha256"], _synthetic_evidence().sealed.request_set_sha256
        )
        self.assertEqual(seal["split_assignment_sha256"], CELL8_SPLIT_ASSIGNMENT_SHA256)
        self.assertEqual(seal["parent_role_scope"], "OUTER_TRAIN_ONLY")
        self.assertEqual(
            seal["sealed_key_count"], seal["sealed_decision_count"] * PATH_BAR_COUNT
        )
        self.assertTrue(record["train_access"]["cell8_role_binding_asserted"])
        self.assertTrue(record["train_access"]["feature_max_source_time_asserted"])
        self.assertEqual(record["validation_status"], "UNOPENED")
        self.assertEqual(record["final_test_status"], "SEALED")

    def test_record_is_aggregate_and_hash_only(self) -> None:
        record = _record()
        payload = json.dumps(record, sort_keys=True)
        for leaked in (
            "cut_points",
            "decision_identity",
            "improvement_vs_prior",
            "log_loss",
            "net_usd",
            "probability_long",
            "trades",
        ):
            self.assertNotIn(f'"{leaked}"', payload)
        for identity in ("D00000", "D00010"):
            self.assertNotIn(identity, payload)
        fold_coverage = record["coverage"]["folds"]["WF_2022"]
        self.assertIn("decile_grid_sha256", fold_coverage)
        self.assertNotIn("cut_points", fold_coverage)
        self.assertEqual(
            sum(
                bucket["total_rows"]
                for bucket in fold_coverage["strata_counts"].values()
            ),
            fold_coverage["total_rows"],
        )

    def test_record_hash_ignores_only_the_volatile_audit_timestamp(self) -> None:
        first = _record()
        second = _record(audit_written_utc="2099-01-01T00:00:00Z")
        self.assertEqual(first["record_sha256"], second["record_sha256"])
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertNotEqual(first["audit_written_utc"], second["audit_written_utc"])
        different = _record(code_identity="2" * 40)
        self.assertNotEqual(first["record_sha256"], different["record_sha256"])

    def test_terminal_witness_states_the_zero_fit_boundary(self) -> None:
        lines = terminal_witness_lines(_record())
        self.assertEqual(lines[0], "G3P_PRE_FIT_PASS_NO_FIT_EXECUTED")
        self.assertTrue(
            any(line.startswith("REAL_TRAIN_TARGET_PATH_ROWS_READ=") for line in lines)
        )
        self.assertTrue(any(line.startswith("TARGETS_CONSTRUCTED=") for line in lines))
        self.assertIn("BARRIER_SETS_CONSTRUCTED=1", lines)
        self.assertIn("SEARCH_BUDGET_MODELS_CONSUMED=0", lines)
        self.assertIn("REAL_MODELS_FITTED=0", lines)
        self.assertIn("REAL_FOLD_FIT_CALLS=0", lines)
        self.assertIn("BOOTSTRAP_REPLICATES=0", lines)
        self.assertIn("ECONOMIC_DIAGNOSTIC_CALLS=0", lines)
        self.assertIn("BLOCKED_FIT_CALLS=0", lines)
        self.assertIn("CELL12_ABSENT_ROWS=0", lines)
        self.assertIn("VALIDATION_ROWS_READ=0", lines)
        self.assertIn("FINAL_TEST=SEALED", lines)
        self.assertIn("G3F_STATUS=NOT_AUTHORIZED", lines)
        self.assertIn(f"DISPOSITION={DISPOSITION_INCONCLUSIVE_UNDERPOWERED}", lines)

    def test_terminal_witness_rejects_a_tampered_counter(self) -> None:
        record = _record()
        record["counters"] = {**record["counters"], "real_models_fitted": 1}
        with self.assertRaisesRegex(PreFitBoundaryError, "zero counters"):
            terminal_witness_lines(record)

    def test_wrong_branch_and_blocked_call_witness_fail_closed(self) -> None:
        with self.assertRaisesRegex(PreFitBoundaryError, "must execute on branch"):
            _record(branch="main")
        with pre_fit_only_guard() as guard:
            with self.assertRaises(PreFitBoundaryError):
                evaluation.fit_frozen_logistic()
            tainted = guard.witness()
        with self.assertRaisesRegex(PreFitBoundaryError, "blocked fit"):
            _record(guard_witness=tainted)

    def test_missing_cell12_coverage_is_rejected_without_an_absent_row_floor(self) -> None:
        evidence = _synthetic_evidence()
        starved = replace(
            evidence.targets,
            cell12_absent_rows=1,
            cell12_expectation_rows=evidence.targets.cell12_expectation_rows - 1,
            cell12_usable_reconciled_rows=evidence.targets.cell12_usable_reconciled_rows - 1,
        )
        with self.assertRaisesRegex(PreFitBoundaryError, "CELL12_ABSENT_ROWS"):
            _record(replace(evidence, targets=starved))
        unreconciled = replace(
            evidence.targets,
            cell12_reconciliation_status="NOT_PERFORMED_CELL12_NOT_SUPPLIED",
        )
        with self.assertRaisesRegex(PreFitBoundaryError, "full-coverage"):
            _record(replace(evidence, targets=unreconciled))

    def test_noncanonical_decoded_shape_stops_before_record_assembly(self) -> None:
        evidence = _synthetic_evidence()
        wrong_rows = replace(
            evidence.decoded_identity,
            row_count=evidence.decoded_identity.row_count - 1,
        )
        with self.assertRaisesRegex(PreFitBoundaryError, "row count"):
            _record(replace(evidence, decoded_identity=wrong_rows))
        wrong_range = replace(
            evidence.decoded_identity,
            timestamp_max_utc="2026-07-31T20:58:00+00:00",
        )
        with self.assertRaisesRegex(PreFitBoundaryError, "timestamp range"):
            _record(replace(evidence, decoded_identity=wrong_range))


class RecordOutputTests(unittest.TestCase):
    def test_record_is_written_exactly_once_per_run_directory(self) -> None:
        record = _record()
        with tempfile.TemporaryDirectory() as temporary:
            output = write_g3p_pre_fit_record(record, output_root=temporary)
            self.assertTrue(output.is_file())
            self.assertEqual(output.name, "pre_fit_support_record.json")
            self.assertEqual(output.parent.name, record["run_id"])
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["record_sha256"], record["record_sha256"])
            with self.assertRaises(FileExistsError):
                write_g3p_pre_fit_record(record, output_root=temporary)

    def test_malformed_run_id_is_refused(self) -> None:
        record = {**_record(), "run_id": "MES_T2_G2_DEADBEEF"}
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(PreFitBoundaryError, "malformed run_id"),
        ):
            write_g3p_pre_fit_record(record, output_root=temporary)


class CollectionBoundaryTests(unittest.TestCase):
    def test_non_canonical_artifact_filenames_stop_before_any_read(self) -> None:
        paths = CanonicalArtifactPaths(
            raw_dbn=Path("/synthetic/not_the_canonical_archive.dbn.zst"),
            cell8_assignments=Path("/synthetic/cell8_purged_split_assignments_v1.parquet"),
            cell10_labels=Path(
                "/synthetic/cell10_point_in_time_economic_labels_v1.parquet"
            ),
            cell12_paths=Path("/synthetic/cell12_development_path_outcomes_v1.parquet"),
            cell14_features=Path(
                "/synthetic/cell14_development_point_in_time_features_v1.parquet"
            ),
        )
        with self.assertRaisesRegex(PreFitBoundaryError, "MISSING_CANONICAL_ARTIFACT"):
            collect_g3p_pre_fit_evidence(
                paths,
                cell14_release_manifest_path=Path("/synthetic/cell14.json"),
                frozen_colab_manifest_path=Path("/synthetic/frozen.json"),
                cell14_run_id="SYNTHETIC_RUN",
            )


class VectorizedProviderEquivalenceTests(unittest.TestCase):
    def test_vectorized_provider_matches_the_scalar_counters(self) -> None:
        evidence = _synthetic_evidence()
        _, _, _, decoded, _ = _synthetic_inputs()
        provider = VectorizedDataFramePathBarProvider(
            decoded,
            sealed=evidence.sealed,
            expected_native_instruments={
                decision.decision_identity: NATIVE_INSTRUMENT_ID
                for decision in evidence.prepared.path_decisions
            },
        )
        self.assertEqual(provider.rows_examined, 0)
        expected_keys = len(evidence.sealed.decisions) * PATH_BAR_COUNT
        self.assertEqual(
            evidence.targets.real_train_target_path_rows_read
            + evidence.targets.missing_path_bar_keys,
            expected_keys,
        )
        self.assertTrue(np.isfinite(evidence.assembly.volatility_grids[0].cut_points).all())


if __name__ == "__main__":
    unittest.main()

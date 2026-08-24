from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from mes_quant.core.hashing import sha256_file
from mes_quant.exploration.test2_g3_contract import (
    CELL12_FULL_COVERAGE_PASS,
    CELL12_RECONCILIATION_UNUSABLE_PASS,
    CELL12_RECONCILIATION_USABLE_PASS,
    CELL12_STATUS_LABEL_UNUSABLE,
    CELL12_STATUS_PATH_INTEGRITY_FAILURE,
    CELL12_STATUS_SEALED_FINAL_TEST,
    CELL12_STATUS_USABLE,
)
from mes_quant.exploration.test2_l1_harness import (
    ArtifactMetadataEvidence,
    ArtifactPreflightSpec,
    CanonicalArtifactPaths,
    Cell12PathExpectation,
    DataFramePathBarProvider,
    DecodedFrameIdentityEvidence,
    MetadataIdentityPreflight,
    PathMetricReconciliation,
    PathTargetBuildResult,
    VectorizedDataFramePathBarProvider,
    assemble_fold_evaluation_data,
    build_real_l1_run_context,
    build_train_path_targets,
    canonical_metadata_preflight,
    decoded_frame_content_sha256,
    preflight_artifact_metadata,
    prepare_train_inputs,
    read_train_cell8_assignments,
    read_train_cell12_expectations,
    read_train_only_parquet,
    verify_decoded_frame_identity,
)
from mes_quant.exploration.test2_l1_harness import (
    Test2HarnessContractError as HarnessContractError,
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
    RAW_DBN_SHA256,
    VOLATILITY_DECILE_POLICY_ID,
)
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    RequestKey,
    build_streaming_request_set,
)
from mes_quant.exploration.test2_run_context import CoverageEvidence
from mes_quant.exploration.test2_target import (
    Disposition,
    PathTargetRow,
    PolicyAction,
    TargetCoverage,
)
from mes_quant.features.contract import FEATURE_COLUMNS, METADATA_COLUMNS


def _feature_and_label_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    decision_time = pd.Timestamp("2022-06-01T14:30:00Z")
    feature_row: dict[str, object] = {
        "decision_id": "A",
        "decision_time": decision_time,
        "nyse_session_date": decision_time.date(),
        "instrument_id": 123,
        "outer_partition": "TRAIN",
        "role_wf_2022": "VALIDATION",
        "role_wf_2023": "TRAIN",
        "role_wf_2024": "UNUSED",
        "feature_row_usable": True,
        "feature_status": "USABLE",
        "feature_lookback_start_utc": decision_time - pd.Timedelta(days=2),
        "feature_max_source_time_utc": decision_time,
    }
    for index, name in enumerate(FEATURE_COLUMNS):
        feature_row[name] = float(index)
    label_row = {
        "decision_id": "A",
        "decision_time": decision_time,
        "instrument_id": 123,
        "outer_partition": "TRAIN",
        "role_wf_2022": "VALIDATION",
        "role_wf_2023": "TRAIN",
        "entry_reference_close": 5_000.0,
        "exit_reference_close_60m": 5_001.0,
    }
    return pd.DataFrame([feature_row]), pd.DataFrame([label_row])


def _assignment_frame() -> pd.DataFrame:
    decision_time = pd.Timestamp("2022-06-01T14:30:00Z")
    return pd.DataFrame(
        [
            {
                "decision_id": "A",
                "decision_time": decision_time,
                "instrument_id": 123,
                "outer_partition": "TRAIN",
                "role_wf_2022": "VALIDATION",
                "role_wf_2023": "TRAIN",
            }
        ]
    )


def _usable_expectation(**overrides: object) -> Cell12PathExpectation:
    values: dict[str, object] = {
        "decision_identity": "A",
        "path_status": CELL12_STATUS_USABLE,
        "path_usable": True,
        "path_1m_present": 60,
        "path_high_60m": 5_004.0,
        "path_low_60m": 5_000.0,
        "long_mfe_points_60m": 4.0,
        "long_mae_points_60m": 0.0,
    }
    values.update(overrides)
    return Cell12PathExpectation(**values)


def _unusable_expectation(**overrides: object) -> Cell12PathExpectation:
    values: dict[str, object] = {
        "decision_identity": "A",
        "path_status": CELL12_STATUS_PATH_INTEGRITY_FAILURE,
        "path_usable": False,
        "path_1m_present": 59,
        "path_high_60m": None,
        "path_low_60m": None,
        "long_mfe_points_60m": None,
        "long_mae_points_60m": None,
    }
    values.update(overrides)
    return Cell12PathExpectation(**values)


def _sealed_and_path_frame(
    *,
    mismatch_offset: int | None = None,
    dropped_offset: int | None = None,
) -> tuple[object, pd.DataFrame]:
    decision_time = datetime(2022, 6, 1, 14, 30, tzinfo=UTC)
    sealed = build_streaming_request_set(
        (ParentDecision("A", decision_time, "TRAIN"),),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    rows = []
    for offset in range(60):
        if offset == dropped_offset:
            continue
        close = 5_001.0 if offset == 59 else 5_000.0
        high = 5_004.0 if offset == 5 else max(5_000.0, close)
        rows.append(
            {
                "ts_event": decision_time + timedelta(minutes=offset),
                "open": 5_000.0,
                "high": high,
                "low": 5_000.0,
                "close": close,
                "instrument_id": 999 if offset == mismatch_offset else 123,
            }
        )
    frame = pd.DataFrame(rows).set_index("ts_event")
    return sealed, frame


class MetadataPreflightTests(unittest.TestCase):
    def test_byte_manifest_and_footer_checks_read_zero_numeric_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.bin"
            raw.write_bytes(b"synthetic raw")
            table = root / "table.parquet"
            pd.DataFrame(
                {"outer_partition": ["TRAIN"], "decision_id": ["A"]}
            ).to_parquet(table, index=False)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "artifacts": [
                            {"id": "raw", "sha256": sha256_file(raw)},
                            {"id": "table", "sha256": sha256_file(table)},
                        ]
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            result = preflight_artifact_metadata(
                (
                    ArtifactPreflightSpec(
                        "raw", raw, sha256_file(raw), manifest_artifact_id="raw"
                    ),
                    ArtifactPreflightSpec(
                        "table",
                        table,
                        sha256_file(table),
                        ("outer_partition", "decision_id"),
                        "table",
                    ),
                ),
                release_manifest_path=manifest,
                expected_release_manifest_sha256=sha256_file(manifest),
            )
            self.assertEqual(result.numeric_values_read, 0)
            self.assertEqual(result.ordered_feature_content_status, "NOT_RECOMPUTED_METADATA_ONLY")
            self.assertEqual(result.artifacts[1].parquet_row_count, 1)

    def test_hash_mismatch_fails_before_footer_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "not_parquet.bin"
            artifact.write_bytes(b"bad")
            manifest = root / "manifest.json"
            manifest.write_text('{"artifacts": []}', encoding="utf-8")
            with self.assertRaisesRegex(HarnessContractError, "SHA-256 mismatch"):
                preflight_artifact_metadata(
                    (
                        ArtifactPreflightSpec(
                            "artifact", artifact, "0" * 64, ("decision_id",)
                        ),
                    ),
                    release_manifest_path=manifest,
                    expected_release_manifest_sha256=sha256_file(manifest),
                )

    def test_cell14_canonical_and_replay_audits_may_have_distinct_byte_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features.parquet"
            pd.DataFrame({"decision_id": ["A"]}).to_parquet(feature, index=False)
            manifest = root / "cell14.json"
            manifest.write_text(
                json.dumps(
                    {
                        "runs": {
                            "canonical": {
                                "artifacts": {
                                    "features": {"sha256": sha256_file(feature)},
                                    "audit": {"sha256": "a" * 64},
                                }
                            },
                            "replay": {
                                "artifacts": {
                                    "features": {"sha256": sha256_file(feature)},
                                    "audit": {"sha256": "b" * 64},
                                }
                            },
                        }
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            result = preflight_artifact_metadata(
                (
                    ArtifactPreflightSpec(
                        "feature",
                        feature,
                        sha256_file(feature),
                        ("decision_id",),
                        "features",
                    ),
                ),
                release_manifest_path=manifest,
                expected_release_manifest_sha256=sha256_file(manifest),
            )
            self.assertEqual(result.artifacts[0].byte_sha256, sha256_file(feature))

    def test_canonical_preflight_binds_both_tracked_manifests(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        paths = CanonicalArtifactPaths(
            *(Path("/synthetic") / name for name in ("raw", "cell8", "cell10", "cell12", "features"))
        )
        upstream_hashes = (
            ("raw_dbn", RAW_DBN_SHA256),
            ("cell8_assignments", CELL8_SPLIT_ASSIGNMENT_SHA256),
            ("cell10_labels", CELL10_LABEL_SHA256),
            ("cell12_paths", CELL12_PATH_SHA256),
        )
        upstream = MetadataIdentityPreflight(
            release_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
            artifacts=tuple(
                ArtifactMetadataEvidence(name, str(paths.raw_dbn), sha256, None, (), None)
                for name, sha256 in upstream_hashes
            ),
        )
        feature = MetadataIdentityPreflight(
            release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
            artifacts=(
                ArtifactMetadataEvidence(
                    "cell14_features",
                    str(paths.cell14_features),
                    FEATURE_ARTIFACT_SHA256,
                    None,
                    (),
                    "features",
                ),
            ),
        )
        with patch(
            "mes_quant.exploration.test2_l1_harness.preflight_artifact_metadata",
            side_effect=(upstream, feature),
        ):
            result = canonical_metadata_preflight(
                paths,
                cell14_release_manifest_path=(
                    project_root / "manifests/releases/cell14_local_release_v1.json"
                ),
                frozen_colab_manifest_path=(
                    project_root / "manifests/releases/frozen_colab_manifest_v1.json"
                ),
            )
        self.assertEqual(result.control_manifest_sha256, FROZEN_COLAB_MANIFEST_SHA256)
        self.assertEqual(
            result.ordered_feature_content_sha256_declared,
            ORDERED_FEATURE_CONTENT_SHA256,
        )


class DecodedIdentityTests(unittest.TestCase):
    def test_decoded_content_hash_is_value_sensitive(self) -> None:
        index = pd.DatetimeIndex(["2022-01-01T00:00:00Z"], name="ts_event")
        frame = pd.DataFrame(
            {
                "open": [1.0],
                "high": [2.0],
                "low": [0.5],
                "close": [1.5],
                "instrument_id": [123],
            },
            index=index,
        )
        expected = decoded_frame_content_sha256(frame)
        evidence = verify_decoded_frame_identity(frame, expected_sha256=expected)
        self.assertEqual(evidence.content_sha256, expected)
        self.assertEqual(evidence.row_count, 1)
        changed = frame.copy()
        changed.loc[index[0], "close"] = 1.75
        with self.assertRaisesRegex(HarnessContractError, "content SHA-256 mismatch"):
            verify_decoded_frame_identity(changed, expected_sha256=expected)


class TrainInputTests(unittest.TestCase):
    def test_parquet_reader_physically_filters_outer_train(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.parquet"
            pd.DataFrame(
                {
                    "outer_partition": ["TRAIN", "VALIDATION", "FINAL_TEST"],
                    "decision_id": ["A", "B", "C"],
                }
            ).to_parquet(path, index=False)
            frame = read_train_only_parquet(
                path,
                columns=("outer_partition", "decision_id"),
            )
            self.assertEqual(frame["decision_id"].tolist(), ["A"])
            self.assertEqual(
                frame.attrs["test2_physical_outer_partition_filter"],
                "TRAIN",
            )

    def test_prepare_asserts_pit_and_exact_role_binding(self) -> None:
        features, labels = _feature_and_label_frames()
        result = prepare_train_inputs(features, labels)
        self.assertTrue(result.feature_max_source_time_asserted)
        self.assertFalse(result.physical_train_predicate_asserted)
        self.assertEqual(result.path_decisions[0].expected_native_instrument, 123)
        self.assertEqual(
            tuple(column for column in features.columns if column in FEATURE_COLUMNS),
            FEATURE_COLUMNS,
        )
        self.assertEqual(tuple(column for column in features.columns if column in METADATA_COLUMNS), METADATA_COLUMNS)

    def test_prepare_rejects_future_feature_source_time(self) -> None:
        features, labels = _feature_and_label_frames()
        features.loc[0, "feature_max_source_time_utc"] += pd.Timedelta(minutes=1)
        with self.assertRaisesRegex(HarnessContractError, "exceeds decision_time"):
            prepare_train_inputs(features, labels)

    def test_prepare_rejects_feature_label_role_mismatch(self) -> None:
        features, labels = _feature_and_label_frames()
        labels.loc[0, "role_wf_2022"] = "TRAIN"
        with self.assertRaisesRegex(HarnessContractError, "role_wf_2022 mismatch"):
            prepare_train_inputs(features, labels)

    def test_fold_assembly_fits_deciles_before_target_retention(self) -> None:
        features, labels = _feature_and_label_frames()
        rows = []
        label_rows = []
        roles = (
            ("A", "2021-06-01T14:30:00Z", "TRAIN", "TRAIN", 0.1, 0),
            ("B", "2022-06-01T14:30:00Z", "VALIDATION", "TRAIN", 0.2, 1),
            ("C", "2023-06-01T14:30:00Z", "UNUSED", "VALIDATION", 0.3, 0),
        )
        for identity, timestamp, role_2022, role_2023, volatility, label in roles:
            feature_row = features.iloc[0].copy()
            feature_row["decision_id"] = identity
            feature_row["decision_time"] = pd.Timestamp(timestamp)
            feature_row["feature_max_source_time_utc"] = pd.Timestamp(timestamp)
            feature_row["nyse_session_date"] = pd.Timestamp(timestamp).date()
            feature_row["role_wf_2022"] = role_2022
            feature_row["role_wf_2023"] = role_2023
            feature_row["realized_vol_60m"] = volatility
            rows.append(feature_row)
            label_row = labels.iloc[0].copy()
            label_row["decision_id"] = identity
            label_row["decision_time"] = pd.Timestamp(timestamp)
            label_row["role_wf_2022"] = role_2022
            label_row["role_wf_2023"] = role_2023
            label_rows.append(label_row)
        prepared = prepare_train_inputs(pd.DataFrame(rows), pd.DataFrame(label_rows))
        target_rows = tuple(
            PathTargetRow(
                decision_identity=identity,
                disposition=(
                    Disposition.FAVORABLE_FIRST if label else Disposition.NEITHER_TOUCH
                ),
                retained=True,
                policy_action=PolicyAction.SCORED,
                path_long=label,
                first_touch_offset_minutes=5 if label else None,
                gross_move_points_60m=1.0,
                no_score_reason=None,
                instrument_id="MES",
                entry_reference_ticks=20_000,
            )
            for identity, _, _, _, _, label in roles
        )
        targets = PathTargetBuildResult(
            target_rows=target_rows,
            coverage=TargetCoverage(3, 1, 0, 2, 0, 0, 3, 0),
            path_metrics=(),
            request_set_sha256="a" * 64,
            real_train_target_path_rows_read=180,
            missing_path_bar_keys=0,
            native_instrument_mismatch_keys=0,
            validation_path_bar_lookup_count=0,
            final_test_path_bar_lookup_count=0,
        )
        assembly = assemble_fold_evaluation_data(prepared, targets)
        self.assertEqual([fold.fold_id for fold in assembly.folds], ["WF_2022", "WF_2023"])
        self.assertEqual(assembly.folds[0].holdout_row_ids, ("B",))
        self.assertEqual(assembly.folds[1].holdout_row_ids, ("C",))
        self.assertEqual(assembly.coverage.total_rows, 2)
        self.assertEqual(assembly.volatility_grids[0].training_row_count, 1)
        self.assertEqual(assembly.volatility_grids[1].training_row_count, 2)


class PathAdapterTests(unittest.TestCase):
    def test_verified_native_instrument_is_normalized_and_reconciled(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        result = build_train_path_targets(
            sealed,
            prepared.path_decisions,
            provider,
            batch_size=17,
            cell12_expectations={"A": _usable_expectation()},
        )
        self.assertEqual(result.target_rows[0].disposition, Disposition.FAVORABLE_FIRST)
        self.assertEqual(result.target_rows[0].instrument_id, "MES")
        self.assertEqual(result.path_metrics[0].cell12_status, "EXACT_TICK_RECONCILIATION_PASS")
        self.assertEqual(result.cell12_reconciliation_status, CELL12_FULL_COVERAGE_PASS)
        self.assertEqual(result.cell12_absent_rows, 0)
        self.assertEqual(result.cell12_expectation_rows, 1)
        self.assertEqual(result.cell12_usable_reconciled_rows, 1)
        self.assertEqual(result.cell12_unusable_reconciled_rows, 0)
        self.assertEqual(result.real_train_target_path_rows_read, 60)
        self.assertEqual(result.validation_path_bar_lookup_count, 0)
        self.assertEqual(result.final_test_path_bar_lookup_count, 0)

        with self.assertRaisesRegex(HarnessContractError, "outside the seal"):
            provider.fetch_path_bar_batch(
                (
                    RequestKey(
                        "A",
                        0,
                        datetime(2025, 1, 2, 14, 45, tzinfo=UTC),
                    ),
                ),
                request_set_sha256=sealed.request_set_sha256,
            )

    def test_native_instrument_mismatch_fails_closed_to_no_score(self) -> None:
        sealed, frame = _sealed_and_path_frame(mismatch_offset=9)
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        result = build_train_path_targets(
            sealed,
            prepared.path_decisions,
            provider,
            batch_size=60,
        )
        self.assertEqual(result.target_rows[0].disposition, Disposition.NO_SCORE)
        self.assertEqual(result.native_instrument_mismatch_keys, 1)
        self.assertEqual(result.missing_path_bar_keys, 0)
        self.assertEqual(
            result.cell12_reconciliation_status, "NOT_PERFORMED_CELL12_NOT_SUPPLIED"
        )

    def test_cell12_difference_fails_closed(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        with self.assertRaisesRegex(HarnessContractError, "differ from Cell 12"):
            build_train_path_targets(
                sealed,
                prepared.path_decisions,
                provider,
                batch_size=60,
                cell12_expectations={
                    "A": _usable_expectation(path_high_60m=5_003.75, long_mfe_points_60m=3.75)
                },
            )

    def test_cell12_unusable_row_reconciles_against_an_incomplete_recomputation(self) -> None:
        sealed, frame = _sealed_and_path_frame(dropped_offset=11)
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        result = build_train_path_targets(
            sealed,
            prepared.path_decisions,
            provider,
            batch_size=60,
            cell12_expectations={"A": _unusable_expectation()},
        )
        self.assertEqual(result.target_rows[0].disposition, Disposition.NO_SCORE)
        verdict = result.path_metrics[0]
        self.assertEqual(verdict.cell12_status, CELL12_RECONCILIATION_UNUSABLE_PASS)
        self.assertIsNone(verdict.path_high_60m)
        self.assertIsNone(verdict.long_mae_points_60m)
        self.assertFalse(verdict.cell12_path_usable)
        self.assertEqual(result.cell12_unusable_reconciled_rows, 1)
        self.assertEqual(result.cell12_usable_reconciled_rows, 0)
        self.assertEqual(result.cell12_absent_rows, 0)
        self.assertEqual(result.cell12_reconciliation_status, CELL12_FULL_COVERAGE_PASS)

    def test_cell12_usable_row_without_a_complete_path_fails_closed(self) -> None:
        sealed, frame = _sealed_and_path_frame(dropped_offset=11)
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        with self.assertRaisesRegex(HarnessContractError, "lacks a complete recomputed"):
            build_train_path_targets(
                sealed,
                prepared.path_decisions,
                provider,
                batch_size=60,
                cell12_expectations={"A": _usable_expectation()},
            )

    def test_cell12_unusable_row_with_a_scored_recomputation_fails_closed(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        with self.assertRaisesRegex(HarnessContractError, "recomputed a scored path"):
            build_train_path_targets(
                sealed,
                prepared.path_decisions,
                provider,
                batch_size=60,
                cell12_expectations={"A": _unusable_expectation()},
            )

    def test_cell12_coverage_must_equal_the_sealed_train_set_exactly(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)

        def build(expectations: dict[str, Cell12PathExpectation]) -> None:
            build_train_path_targets(
                sealed,
                prepared.path_decisions,
                DataFramePathBarProvider(
                    frame,
                    sealed=sealed,
                    expected_native_instruments={"A": 123},
                ),
                batch_size=60,
                cell12_expectations=expectations,
            )

        with self.assertRaisesRegex(HarnessContractError, "absent=1"):
            build({})
        with self.assertRaisesRegex(HarnessContractError, r"unexpected=\['B'\]"):
            build(
                {
                    "A": _usable_expectation(),
                    "B": _usable_expectation(decision_identity="B"),
                }
            )


class Cell12ExpectationContractTests(unittest.TestCase):
    def test_usable_row_requires_sixty_present_bars_and_finite_metrics(self) -> None:
        with self.assertRaisesRegex(HarnessContractError, "exactly 60 present"):
            _usable_expectation(path_1m_present=59)
        with self.assertRaisesRegex(HarnessContractError, "finite numeric path fields"):
            _usable_expectation(long_mae_points_60m=None)
        with self.assertRaisesRegex(HarnessContractError, "USABLE path status"):
            _usable_expectation(path_status=CELL12_STATUS_LABEL_UNUSABLE)

    def test_unusable_row_may_not_expose_numeric_path_fields(self) -> None:
        with self.assertRaisesRegex(HarnessContractError, "must not expose numeric"):
            _unusable_expectation(path_high_60m=5_004.0)
        with self.assertRaisesRegex(HarnessContractError, "complete one-minute path"):
            _unusable_expectation(path_1m_present=60)
        with self.assertRaisesRegex(HarnessContractError, "unexpected status"):
            _unusable_expectation(path_status="SOMETHING_ELSE")

    def test_sealed_final_test_status_can_never_appear_in_a_train_read(self) -> None:
        with self.assertRaisesRegex(HarnessContractError, "sealed Final-Test row"):
            _unusable_expectation(path_status=CELL12_STATUS_SEALED_FINAL_TEST)

    def test_train_reader_pushes_the_predicate_and_reads_status_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cell12.parquet"
            pd.DataFrame(
                {
                    "decision_id": ["A", "B", "C"],
                    "outer_partition": ["TRAIN", "TRAIN", "VALIDATION"],
                    "path_status": [
                        CELL12_STATUS_USABLE,
                        CELL12_STATUS_LABEL_UNUSABLE,
                        CELL12_STATUS_USABLE,
                    ],
                    "path_usable": [True, False, True],
                    "path_1m_present": [60.0, float("nan"), 60.0],
                    "path_high_60m": [5_004.0, float("nan"), 5_010.0],
                    "path_low_60m": [5_000.0, float("nan"), 5_002.0],
                    "long_mfe_points_60m": [4.0, float("nan"), 6.0],
                    "long_mae_points_60m": [0.0, float("nan"), 0.0],
                }
            ).to_parquet(path, index=False)
            expectations = read_train_cell12_expectations(path)
        self.assertEqual(set(expectations), {"A", "B"})
        self.assertTrue(expectations["A"].path_usable)
        self.assertEqual(expectations["A"].path_1m_present, 60)
        self.assertEqual(expectations["A"].long_mfe_points_60m, 4.0)
        self.assertFalse(expectations["B"].path_usable)
        self.assertIsNone(expectations["B"].path_1m_present)
        self.assertIsNone(expectations["B"].path_high_60m)


class Cell8CrossBindingTests(unittest.TestCase):
    def test_physical_cell8_read_filters_outer_train(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cell8.parquet"
            pd.DataFrame(
                {
                    "decision_id": ["A", "B"],
                    "decision_time": [
                        pd.Timestamp("2022-06-01T14:30:00Z"),
                        pd.Timestamp("2024-06-01T14:30:00Z"),
                    ],
                    "instrument_id": [123, 123],
                    "outer_partition": ["TRAIN", "VALIDATION"],
                    "role_wf_2022": ["VALIDATION", "UNUSED"],
                    "role_wf_2023": ["TRAIN", "UNUSED"],
                }
            ).to_parquet(path, index=False)
            frame = read_train_cell8_assignments(path)
        self.assertEqual(frame["decision_id"].tolist(), ["A"])
        self.assertEqual(frame.attrs["test2_physical_outer_partition_filter"], "TRAIN")

    def test_cross_assertion_binds_role_instrument_and_time(self) -> None:
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels, assignments=_assignment_frame())
        self.assertTrue(prepared.cell8_role_binding_asserted)
        without = prepare_train_inputs(features, labels)
        self.assertFalse(without.cell8_role_binding_asserted)

    def test_cross_assertion_rejects_each_mismatch(self) -> None:
        features, labels = _feature_and_label_frames()
        cases = (
            ({"role_wf_2022": "TRAIN"}, "role_wf_2022 mismatch"),
            ({"role_wf_2023": "VALIDATION"}, "role_wf_2023 mismatch"),
            ({"instrument_id": 999}, "instrument_id mismatch"),
            (
                {"decision_time": pd.Timestamp("2022-06-01T14:45:00Z")},
                "decision_time mismatch",
            ),
            ({"decision_id": "Z"}, "TRAIN decision sets differ"),
        )
        for overrides, message in cases:
            assignments = _assignment_frame()
            for column, value in overrides.items():
                assignments.loc[0, column] = value
            with self.assertRaisesRegex(HarnessContractError, message):
                prepare_train_inputs(features, labels, assignments=assignments)

    def test_cross_assertion_rejects_non_train_and_boundary_crossing_rows(self) -> None:
        features, labels = _feature_and_label_frames()
        non_train = _assignment_frame()
        non_train.loc[0, "outer_partition"] = "VALIDATION"
        with self.assertRaisesRegex(HarnessContractError, "contains non-TRAIN rows"):
            prepare_train_inputs(features, labels, assignments=non_train)
        late = _assignment_frame()
        late.loc[0, "decision_time"] = pd.Timestamp("2024-06-01T14:30:00Z")
        with self.assertRaisesRegex(HarnessContractError, "outer-Validation boundary"):
            prepare_train_inputs(features, labels, assignments=late)


class VectorizedProviderEquivalenceTests(unittest.TestCase):
    def _providers(
        self,
        frame: pd.DataFrame,
        sealed: object,
        expected: dict[str, object],
    ) -> tuple[DataFramePathBarProvider, VectorizedDataFramePathBarProvider]:
        return (
            DataFramePathBarProvider(
                frame, sealed=sealed, expected_native_instruments=expected
            ),
            VectorizedDataFramePathBarProvider(
                frame, sealed=sealed, expected_native_instruments=expected
            ),
        )

    def _assert_equivalent(
        self,
        frame: pd.DataFrame,
        expected: dict[str, object],
        *,
        mismatch_offset: int | None = None,
        dropped_offset: int | None = None,
    ) -> None:
        sealed, _ = _sealed_and_path_frame(
            mismatch_offset=mismatch_offset, dropped_offset=dropped_offset
        )
        scalar, vectorized = self._providers(frame, sealed, expected)
        keys = tuple(
            RequestKey(
                "A",
                offset,
                datetime(2022, 6, 1, 14, 30, tzinfo=UTC) + timedelta(minutes=offset),
            )
            for offset in range(60)
        )
        for batch_size in (7, 60):
            scalar_batches = [
                scalar.fetch_path_bar_batch(
                    keys[start : start + batch_size],
                    request_set_sha256=sealed.request_set_sha256,
                )
                for start in range(0, len(keys), batch_size)
            ]
            vector_batches = [
                vectorized.fetch_path_bar_batch(
                    keys[start : start + batch_size],
                    request_set_sha256=sealed.request_set_sha256,
                )
                for start in range(0, len(keys), batch_size)
            ]
            self.assertEqual(scalar_batches, vector_batches)
        self.assertEqual(scalar.rows_examined, vectorized.rows_examined)
        self.assertEqual(scalar.missing_keys, vectorized.missing_keys)
        self.assertEqual(
            scalar.instrument_mismatch_keys, vectorized.instrument_mismatch_keys
        )

    def test_element_equivalence_for_the_canonical_numeric_frame(self) -> None:
        _, frame = _sealed_and_path_frame()
        self._assert_equivalent(frame, {"A": 123})

    def test_element_equivalence_for_missing_and_mismatched_bars(self) -> None:
        _, frame = _sealed_and_path_frame(mismatch_offset=9, dropped_offset=13)
        self._assert_equivalent(
            frame, {"A": 123}, mismatch_offset=9, dropped_offset=13
        )

    def test_element_equivalence_for_a_string_instrument_column(self) -> None:
        _, frame = _sealed_and_path_frame()
        frame["instrument_id"] = frame["instrument_id"].astype(str)
        self._assert_equivalent(frame, {"A": "123"})

    def test_element_equivalence_when_extra_decoded_columns_are_present(self) -> None:
        _, frame = _sealed_and_path_frame()
        frame.insert(0, "rtype", 34)
        frame["volume"] = 10
        frame["symbol"] = "MESM2"
        self._assert_equivalent(frame, {"A": 123})

    def test_vectorized_provider_rejects_an_unsealed_key(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        provider = VectorizedDataFramePathBarProvider(
            frame, sealed=sealed, expected_native_instruments={"A": 123}
        )
        with self.assertRaisesRegex(HarnessContractError, "outside the seal"):
            provider.fetch_path_bar_batch(
                (RequestKey("A", 0, datetime(2025, 1, 2, 14, 45, tzinfo=UTC)),),
                request_set_sha256=sealed.request_set_sha256,
            )
        with self.assertRaisesRegex(HarnessContractError, "wrong sealed request hash"):
            provider.fetch_path_bar_batch((), request_set_sha256="0" * 64)
        self.assertEqual(provider.rows_examined, 0)


class RealRunContextTests(unittest.TestCase):
    @staticmethod
    def _metadata() -> MetadataIdentityPreflight:
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
                    path=f"/synthetic/{artifact_id}",
                    byte_sha256=sha256,
                    parquet_row_count=None,
                    parquet_schema=(),
                    manifest_artifact_id=None,
                )
                for artifact_id, sha256 in hashes.items()
            ),
            control_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
            ordered_feature_content_sha256_declared=ORDERED_FEATURE_CONTENT_SHA256,
        )

    @staticmethod
    def _decoded() -> DecodedFrameIdentityEvidence:
        return DecodedFrameIdentityEvidence(
            DECODED_MES_1M_SHA256,
            2_551_123,
            "2019-05-05T22:00:00+00:00",
            "2026-07-31T20:59:00+00:00",
        )

    @staticmethod
    def _targets() -> PathTargetBuildResult:
        row = PathTargetRow(
            decision_identity="A",
            disposition=Disposition.FAVORABLE_FIRST,
            retained=True,
            policy_action=PolicyAction.SCORED,
            path_long=1,
            first_touch_offset_minutes=5,
            gross_move_points_60m=1.0,
            no_score_reason=None,
            instrument_id="MES",
            entry_reference_ticks=20_000,
        )
        return PathTargetBuildResult(
            target_rows=(row,),
            coverage=TargetCoverage(1, 1, 0, 0, 0, 0, 1, 0),
            path_metrics=(
                PathMetricReconciliation(
                    "A",
                    5_004.0,
                    5_000.0,
                    4.0,
                    0.0,
                    CELL12_RECONCILIATION_USABLE_PASS,
                    CELL12_STATUS_USABLE,
                    True,
                ),
            ),
            request_set_sha256="c" * 64,
            real_train_target_path_rows_read=60,
            missing_path_bar_keys=0,
            native_instrument_mismatch_keys=0,
            validation_path_bar_lookup_count=0,
            final_test_path_bar_lookup_count=0,
            cell12_expectation_rows=1,
            cell12_absent_rows=0,
            cell12_usable_reconciled_rows=1,
            cell12_unusable_reconciled_rows=0,
            cell12_reconciliation_status=CELL12_FULL_COVERAGE_PASS,
        )

    @staticmethod
    def _coverage() -> CoverageEvidence:
        return CoverageEvidence(
            1,
            0,
            0,
            0,
            "ALL_OOF_ROWS_PRETARGET_FOLD_TRAIN_DECILES",
            {
                "policy_id": VOLATILITY_DECILE_POLICY_ID,
                "folds": {
                    "WF_2022": {"total_rows": 1},
                    "WF_2023": {"total_rows": 0},
                },
            },
        )

    def _build(self, **overrides: object) -> object:
        features, labels = _feature_and_label_frames()
        prepared = replace(
            prepare_train_inputs(features, labels, assignments=_assignment_frame()),
            physical_train_predicate_asserted=True,
        )
        arguments: dict[str, object] = {
            "metadata": self._metadata(),
            "prepared": prepared,
            "targets": self._targets(),
            "coverage": self._coverage(),
        }
        arguments.update(overrides)
        return build_real_l1_run_context(
            arguments["metadata"],
            arguments["prepared"],
            arguments["targets"],
            arguments["coverage"],
            decoded_identity=self._decoded(),
            authorization_identity="OWNER_TEST2_L1",
            authorization_record_sha256="d" * 64,
        )

    def test_real_context_requires_canonical_metadata_and_cell12_reconciliation(self) -> None:
        context = self._build()
        self.assertEqual(context.access_level, "L1_TRAIN_ONLY")
        self.assertIn("NOT_RECOMPUTED", context.source_identity.content_sha256_evidence)

    def test_real_context_rejects_a_wrong_coverage_scope(self) -> None:
        with self.assertRaisesRegex(HarnessContractError, "counter scope"):
            self._build(coverage=replace(self._coverage(), scope="ALL_FEATURE_VALID_OOF_ROWS"))

    def test_real_context_requires_the_cell8_cross_binding(self) -> None:
        features, labels = _feature_and_label_frames()
        prepared = replace(
            prepare_train_inputs(features, labels),
            physical_train_predicate_asserted=True,
        )
        with self.assertRaisesRegex(HarnessContractError, "Cell 8 role/instrument/time"):
            self._build(prepared=prepared)

    def test_real_context_requires_full_coverage_cell12_reconciliation(self) -> None:
        with self.assertRaisesRegex(HarnessContractError, "full-coverage Cell 12"):
            self._build(
                targets=replace(
                    self._targets(),
                    cell12_reconciliation_status="NOT_PERFORMED_CELL12_NOT_SUPPLIED",
                )
            )
        with self.assertRaisesRegex(HarnessContractError, "does not cover every sealed"):
            self._build(targets=replace(self._targets(), cell12_absent_rows=1))
        with self.assertRaisesRegex(HarnessContractError, "differs from the sealed"):
            self._build(targets=replace(self._targets(), cell12_expectation_rows=2))
        with self.assertRaisesRegex(HarnessContractError, "exact Cell 12 reconciliation"):
            self._build(targets=replace(self._targets(), path_metrics=()))
        with self.assertRaisesRegex(HarnessContractError, "exact Cell 12 reconciliation"):
            self._build(
                targets=replace(
                    self._targets(),
                    path_metrics=(
                        replace(
                            self._targets().path_metrics[0],
                            cell12_status="NOT_PERFORMED_CELL12_NOT_SUPPLIED",
                        ),
                    ),
                )
            )
        with self.assertRaisesRegex(HarnessContractError, "verdicts do not reconcile"):
            self._build(
                targets=replace(self._targets(), cell12_usable_reconciled_rows=0)
            )


if __name__ == "__main__":
    unittest.main()

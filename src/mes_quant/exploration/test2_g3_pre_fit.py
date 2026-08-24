"""Test 2 G3-P pre-fit evidence orchestration.

G3-P is the bounded gate between the frozen G2 metadata preflight and the still
unauthorized G3-F conditional fit. It may decode the canonical DBN, physically
read the outer-TRAIN Cell 8/10/12/14 rows, seal the ordered path request set,
construct the frozen target, reconcile Cell 12 exactly, and evaluate the frozen
support gate. It may not fit a model, draw a bootstrap replicate, or compute an
economic diagnostic — those calls are mechanically blocked for the whole run.

G3-P stops before fitting under **both** support outcomes:

```text
support gate fails  ->  INCONCLUSIVE_UNDERPOWERED
support gate passes ->  SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED
                        DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION
```

Neither outcome consumes a fit. `real_models_fitted` is `0` in every record this
module can produce, and the record can state a passing support gate truthfully
without implying that a fit occurred or is authorized.

The frozen science carries no CLI knobs: barriers, offsets, folds, MDE floors,
ESS/support floors, bootstrap seeds, and model definitions are all read from the
frozen contract modules and cannot be overridden from the command line.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

from mes_quant.core.hashing import (
    canonical_json_bytes,
    canonicalize_audit,
    sha256_bytes,
    sha256_file,
)
from mes_quant.exploration import l1_lr001 as _lr001
from mes_quant.exploration import l1_tree001 as _tree001
from mes_quant.exploration import test2_diagnostics as _diagnostics
from mes_quant.exploration import test2_evaluation as _evaluation
from mes_quant.exploration import test2_metadata_preflight as _g2
from mes_quant.exploration import test2_stats as _stats
from mes_quant.exploration.test2_decode import (
    CELL2_HASH_ALGORITHM,
    CELL2_HASH_COLUMNS,
    CELL2_HASH_INCLUDES_INDEX,
    CELL2_HASH_PROJECTION_ID,
    DECODED_CONTENT_STATUS_RECOMPUTED,
    databento_modules_loaded,
    decode_canonical_dbn,
)
from mes_quant.exploration.test2_evaluation import EvaluationPreflight, preflight_evaluation
from mes_quant.exploration.test2_g3_contract import (
    CELL12_COVERAGE_POLICY_ID,
    CELL12_FULL_COVERAGE_PASS,
    EXPECTED_DECODED_ROW_COUNT,
    EXPECTED_DECODED_TIMESTAMP_MAX_UTC,
    EXPECTED_DECODED_TIMESTAMP_MIN_UTC,
    G3_AUTHORIZED_BASE_COMMIT,
    G3_BRANCH,
    G3F_GATE_LITERAL,
    G3F_STATUS,
    G3I_ALLOWED_CHANGED_FILES,
    G3P_GATE_LITERAL,
    PINNED_DOC_BINDING_STATUS,
    PINNED_DOC_SHA256,
    changed_file_firewall_failures,
    support_outcome,
)
from mes_quant.exploration.test2_l1_harness import (
    CANONICAL_CELL8_FILENAME,
    CANONICAL_CELL10_FILENAME,
    CANONICAL_CELL12_FILENAME,
    CANONICAL_FEATURE_FILENAME,
    CANONICAL_RAW_DBN_FILENAME,
    CELL10_REQUIRED_COLUMNS,
    FEATURE_REQUIRED_COLUMNS,
    CanonicalArtifactPaths,
    DecodedFrameIdentityEvidence,
    FoldAssembly,
    MetadataIdentityPreflight,
    PathTargetBuildResult,
    PreparedTrainInputs,
    VectorizedDataFramePathBarProvider,
    assemble_fold_evaluation_data,
    build_real_l1_run_context,
    build_train_path_targets,
    canonical_metadata_preflight,
    prepare_train_inputs,
    read_train_cell8_assignments,
    read_train_cell12_expectations,
    read_train_only_parquet,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    EXPLORATION_SCOPE_ID,
    FINAL_TEST_BOUNDARY_UTC,
    FULL_MODEL_ID,
    NUISANCE_MODEL_ID,
    OUTER_TRAIN_ROLE,
    OUTER_VALIDATION_BOUNDARY_UTC,
    PATH_BAR_COUNT,
    STOP_TICKS,
    TAKE_PROFIT_TICKS,
    TICK_SIZE_POINTS,
)
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    StreamingSealedRequestSet,
    build_streaming_request_set,
)
from mes_quant.exploration.test2_run_context import CoverageEvidence
from mes_quant.exploration.test2_stats import FOLD_ORDER, EssSupportSummary

G3P_GATE_ID = "TEST2_G3P_PRE_FIT_EVIDENCE_V1"
G3P_RECORD_VERSION = "1.0"
G3P_ACCESS_LEVEL = "L1_TRAIN_ONLY_PRE_FIT_EVIDENCE_NO_FIT"
G3P_STATUS = "PASS"
G3P_RECORD_FILENAME = "pre_fit_support_record.json"
G3P_OUTPUT_SUBPATH = "artifacts/exploration/test2/g3p"

# Implementation constant, deliberately not a CLI knob: it only controls how the
# sealed 60x expansion is streamed to the provider, never what is requested.
G3P_PATH_BAR_BATCH_SIZE = 3_600

G3P_AUTHORIZATION_IDENTITY = "OWNER_TEST2_G3P_PRE_FIT_EVIDENCE_ONLY"
G3P_AUTHORIZATION_RECORD_SCOPE = "SHA256_OF_CANONICAL_G3P_AUTHORIZATION_BINDING_BLOCK"

_ZERO_COUNTERS = {
    "real_models_fitted": 0,
    "real_fold_fit_calls": 0,
    "synthetic_fitter_calls": 0,
    "bootstrap_replicates": 0,
    "economic_diagnostic_calls": 0,
    "blocked_fit_calls": 0,
    "validation_rows_read": 0,
    "final_test_rows_read": 0,
    "validation_path_bar_lookup_count": 0,
    "final_test_path_bar_lookup_count": 0,
    "cell12_absent_rows": 0,
    "search_budget_models_consumed": 0,
    "barrier_set_changes": 0,
    "model_definition_changes": 0,
    "support_floor_changes": 0,
}
_NOT_PERFORMED = (
    "model_fit",
    "paired_session_block_bootstrap",
    "economic_counterfactual",
    "calibration_search",
    "threshold_search",
    "feature_subset_search",
    "validation_access",
    "final_test_access",
    "database_operation",
    "target_derived_redesign",
)

# Row-level or fit-derived fields that may never reach a pre-fit support record.
_FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "beta",
        "coefficients",
        "cut_points",
        "decision_id",
        "decision_identity",
        "decision_time",
        "entry_reference_close",
        "holdout_row_ids",
        "improvement_vs_nuisance",
        "improvement_vs_prior",
        "log_loss",
        "long_mae_points_60m",
        "long_mfe_points_60m",
        "lower_bound_vs_nuisance",
        "lower_bound_vs_prior",
        "net_usd",
        "path_high_60m",
        "path_low_60m",
        "probability_long",
        "roc_auc",
        "statistics",
        "train_row_ids",
        "trades",
    }
)

# (owner module, attribute) pairs blocked for the whole G3-P run. Every symbol
# must exist; a missing symbol means the fit surface moved and the guard would
# silently stop covering it.
_BLOCKED_FIT_SYMBOLS = (
    (_lr001, "fit_frozen_logistic"),
    (_lr001, "evaluate_lr001_frame"),
    (_lr001, "run_lr001"),
    (_tree001, "fit_bounded_shallow_tree"),
    (_tree001, "predict_bounded_shallow_tree"),
    (_tree001, "evaluate_tree001_frame"),
    (_tree001, "run_tree001"),
    (_evaluation, "fit_frozen_logistic"),
    (_evaluation, "standardize_fold"),
    (_evaluation, "decide_continuation"),
    (_evaluation, "required_paired_bootstraps"),
    (_evaluation, "stepwise_average_precision"),
    (_evaluation, "build_economic_diagnostics"),
    (_evaluation, "_run_evaluation"),
    (_evaluation, "run_synthetic_evaluation"),
    (_evaluation, "run_authorized_train_evaluation"),
    (_stats, "paired_session_block_bootstrap"),
    (_stats, "required_paired_bootstraps"),
    (_stats, "moving_block_indices"),
    (_stats, "stepwise_average_precision"),
    (_diagnostics, "build_economic_diagnostics"),
    (_diagnostics, "_policy_counterfactual"),
)

_MODULE_LABELS = {
    id(_lr001): "l1_lr001",
    id(_tree001): "l1_tree001",
    id(_evaluation): "test2_evaluation",
    id(_stats): "test2_stats",
    id(_diagnostics): "test2_diagnostics",
}


class G3PreFitBoundaryError(RuntimeError):
    """Raised before G3-P could exceed pre-fit evidence authorization."""


def _git_sha(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise G3PreFitBoundaryError(f"{field_name} must be a lowercase 40-character Git SHA")
    return value


# ---------------------------------------------------------------------------
# Mechanical fit blocker
# ---------------------------------------------------------------------------


@dataclass
class _G3PFitGuard:
    blocked_fit_calls: int = 0
    installed_symbols: list[str] = field(default_factory=list)
    attempted_symbols: list[str] = field(default_factory=list)

    def reject(self, symbol: str) -> NoReturn:
        self.blocked_fit_calls += 1
        self.attempted_symbols.append(symbol)
        raise G3PreFitBoundaryError(
            f"G3-P pre-fit boundary blocked a fit/bootstrap/economic call: {symbol}"
        )

    def blocker(self, symbol: str):
        def blocked(*_args: object, **_kwargs: object) -> NoReturn:
            self.reject(symbol)

        return blocked

    def witness(self) -> dict[str, object]:
        return {
            "guard_id": "G3P_PRE_FIT_NO_FIT_NO_BOOTSTRAP_NO_ECONOMIC_V1",
            "installed_symbols": list(self.installed_symbols),
            "blocked_fit_calls": self.blocked_fit_calls,
            "attempted_symbols": list(self.attempted_symbols),
            "guard_status": (
                "PASS_NO_BLOCKED_CALLS"
                if self.blocked_fit_calls == 0
                else "FAIL_BLOCKED_CALL_ATTEMPTED"
            ),
            "g3f_gate": G3F_GATE_LITERAL,
            "g3f_status": G3F_STATUS,
        }


@contextmanager
def pre_fit_only_guard() -> Iterator[_G3PFitGuard]:
    """Block every fit, bootstrap, and economic diagnostic entry point."""

    guard = _G3PFitGuard()
    originals: list[tuple[object, str, object]] = []
    try:
        for owner, name in _BLOCKED_FIT_SYMBOLS:
            label = f"{_MODULE_LABELS[id(owner)]}.{name}"
            if not hasattr(owner, name):
                raise G3PreFitBoundaryError(
                    f"G3-P required fit-guard symbol is missing: {label}"
                )
            originals.append((owner, name, getattr(owner, name)))
            setattr(owner, name, guard.blocker(label))
            guard.installed_symbols.append(label)
        yield guard
    finally:
        for owner, name, original in reversed(originals):
            setattr(owner, name, original)


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G3PreFitEvidence:
    metadata: MetadataIdentityPreflight
    decoded_identity: DecodedFrameIdentityEvidence
    cell14_run_binding: Mapping[str, object]
    prepared: PreparedTrainInputs
    sealed: StreamingSealedRequestSet
    targets: PathTargetBuildResult
    assembly: FoldAssembly
    preflight: EvaluationPreflight


_EXPECTED_FILENAMES = {
    "raw_dbn": CANONICAL_RAW_DBN_FILENAME,
    "cell8_assignments": CANONICAL_CELL8_FILENAME,
    "cell10_labels": CANONICAL_CELL10_FILENAME,
    "cell12_paths": CANONICAL_CELL12_FILENAME,
    "cell14_features": CANONICAL_FEATURE_FILENAME,
}


def _assert_canonical_filenames(paths: CanonicalArtifactPaths) -> None:
    observed = {
        "raw_dbn": paths.raw_dbn,
        "cell8_assignments": paths.cell8_assignments,
        "cell10_labels": paths.cell10_labels,
        "cell12_paths": paths.cell12_paths,
        "cell14_features": paths.cell14_features,
    }
    for artifact_id, path in observed.items():
        expected = _EXPECTED_FILENAMES[artifact_id]
        if path.name != expected:
            raise G3PreFitBoundaryError(
                f"MISSING_CANONICAL_ARTIFACT: {artifact_id} requires filename {expected}"
            )


def collect_g3p_pre_fit_evidence(
    paths: CanonicalArtifactPaths,
    *,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
    cell14_run_id: str,
) -> G3PreFitEvidence:
    """Gather every pre-fit evidence object in the frozen G3-P order."""

    _assert_canonical_filenames(paths)
    metadata = canonical_metadata_preflight(
        paths,
        cell14_release_manifest_path=cell14_release_manifest_path,
        frozen_colab_manifest_path=frozen_colab_manifest_path,
    )
    # Reuse the already-frozen G2 release binding rather than restating it, so
    # the two gates cannot drift on which Cell 14 run is admissible.
    cell14_run_binding = _g2._cell14_run_binding(
        Path(cell14_release_manifest_path).expanduser().resolve(),
        selected_run_id=cell14_run_id,
        feature_path=paths.cell14_features,
    )

    decoded_frame, decoded_identity = decode_canonical_dbn(paths.raw_dbn)

    features = read_train_only_parquet(
        paths.cell14_features, columns=FEATURE_REQUIRED_COLUMNS
    )
    labels = read_train_only_parquet(paths.cell10_labels, columns=CELL10_REQUIRED_COLUMNS)
    assignments = read_train_cell8_assignments(paths.cell8_assignments)
    cell12_expectations = read_train_cell12_expectations(paths.cell12_paths)

    prepared = prepare_train_inputs(features, labels, assignments=assignments)
    sealed = build_streaming_request_set(
        tuple(
            ParentDecision(
                decision_identity=decision.decision_identity,
                decision_time_utc=decision.decision_time_utc,
                outer_partition=OUTER_TRAIN_ROLE,
            )
            for decision in prepared.path_decisions
        ),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    provider = VectorizedDataFramePathBarProvider(
        decoded_frame,
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
        cell12_expectations=cell12_expectations,
    )
    assembly = assemble_fold_evaluation_data(prepared, targets)
    preflight = preflight_evaluation(assembly.folds)
    return G3PreFitEvidence(
        metadata=metadata,
        decoded_identity=decoded_identity,
        cell14_run_binding=cell14_run_binding,
        prepared=prepared,
        sealed=sealed,
        targets=targets,
        assembly=assembly,
        preflight=preflight,
    )


# ---------------------------------------------------------------------------
# Aggregate, hash-only projections
# ---------------------------------------------------------------------------


def _ess_aggregate(summary: EssSupportSummary) -> dict[str, object]:
    return {
        "row_count": summary.row_count,
        "path_long_design_effect": summary.path_long.design_effect,
        "path_long_ess": summary.path_long.effective_sample_size,
        "gross_move_design_effect": summary.gross_move_points_60m.design_effect,
        "gross_move_ess": summary.gross_move_points_60m.effective_sample_size,
        "governing_design_effect": summary.governing_design_effect,
        "governing_ess": summary.governing_effective_sample_size,
        "raw_negative_count": summary.raw_negative_count,
        "raw_positive_count": summary.raw_positive_count,
        "effective_negative_support": summary.effective_negative_support,
        "effective_positive_support": summary.effective_positive_support,
        "status": summary.status,
    }


_STRATUM_COUNT_KEYS = (
    "total_rows",
    "retained_rows",
    "favorable_first_rows",
    "adverse_first_rows",
    "neither_touch_rows",
    "ambiguous_same_bar_rows",
    "no_score_rows",
)


def _stratum_counts(record: Mapping[str, object]) -> dict[str, int]:
    try:
        return {key: int(record[key]) for key in _STRATUM_COUNT_KEYS}
    except (KeyError, TypeError, ValueError) as exc:
        raise G3PreFitBoundaryError("coverage stratum counts are malformed") from exc


def _coverage_aggregate(coverage: CoverageEvidence) -> dict[str, object]:
    """Project coverage onto counts and grid hashes; never onto cut points."""

    payload = coverage.by_fold_decile
    folds = payload.get("folds")
    pooled = payload.get("pooled_strata_using_row_fold_grid")
    if not isinstance(folds, Mapping) or set(folds) != set(FOLD_ORDER):
        raise G3PreFitBoundaryError("coverage evidence lacks the exact fold identity")
    if not isinstance(pooled, Mapping):
        raise G3PreFitBoundaryError("coverage evidence lacks pooled strata")

    fold_aggregate: dict[str, object] = {}
    reconciled = 0
    for fold_id in FOLD_ORDER:
        entry = folds[fold_id]
        if not isinstance(entry, Mapping):
            raise G3PreFitBoundaryError("coverage fold entry is malformed")
        grid = entry.get("grid")
        strata = entry.get("strata")
        if not isinstance(grid, Mapping) or not isinstance(strata, Mapping):
            raise G3PreFitBoundaryError("coverage fold grid/strata are malformed")
        fold_total = int(entry["total_rows"])
        reconciled += fold_total
        fold_aggregate[fold_id] = {
            "total_rows": fold_total,
            "decile_grid_policy_id": str(grid["policy_id"]),
            "decile_grid_sha256": str(grid["grid_sha256"]),
            "decile_training_row_count": int(grid["training_row_count"]),
            "decile_assignment_rule": str(grid["assignment_rule"]),
            "empty_decile_buckets": [int(value) for value in grid["empty_decile_buckets"]],
            "degenerate_decile_grid": bool(grid["degenerate_decile_grid"]),
            "strata_counts": {
                str(bucket): _stratum_counts(record)
                for bucket, record in sorted(strata.items())
            },
        }
    if reconciled != coverage.total_rows:
        raise G3PreFitBoundaryError("coverage fold totals do not reconcile")
    return {
        "policy_id": str(payload.get("policy_id")),
        "counter_scope": coverage.scope,
        "total_rows": coverage.total_rows,
        "ambiguity_rows": coverage.ambiguity_rows,
        "missing_rows": coverage.missing_rows,
        "excluded_rows": coverage.excluded_rows,
        "folds": fold_aggregate,
        "pooled_strata_counts": {
            str(bucket): _stratum_counts(record)
            for bucket, record in sorted(pooled.items())
        },
    }


def _target_coverage_aggregate(targets: PathTargetBuildResult) -> dict[str, object]:
    coverage = targets.coverage
    return {
        "total_rows": coverage.total_rows,
        "favorable_first": coverage.favorable_first,
        "adverse_first": coverage.adverse_first,
        "neither_touch": coverage.neither_touch,
        "ambiguous_same_bar": coverage.ambiguous_same_bar,
        "no_score": coverage.no_score,
        "retained_rows": coverage.retained_rows,
        "flat_rows": coverage.flat_rows,
    }


def _cell12_aggregate(targets: PathTargetBuildResult) -> dict[str, object]:
    return {
        "coverage_policy_id": targets.cell12_coverage_policy_id,
        "reconciliation_status": targets.cell12_reconciliation_status,
        "expectation_rows": targets.cell12_expectation_rows,
        "absent_rows": targets.cell12_absent_rows,
        "usable_reconciled_rows": targets.cell12_usable_reconciled_rows,
        "unusable_reconciled_rows": targets.cell12_unusable_reconciled_rows,
        "verdict_rows": len(targets.path_metrics),
        "reconciliation_scope": (
            "EXACT_TICK_COMPARISON_FOR_USABLE_ROWS_AND_ABSENT_FIELD_"
            "AGREEMENT_FOR_UNUSABLE_ROWS"
        ),
    }


def _walk_record_keys(value: object) -> Iterator[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_record_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_record_keys(child)


def _assert_closed_record(record: Mapping[str, object]) -> None:
    forbidden = sorted(_FORBIDDEN_RECORD_KEYS.intersection(_walk_record_keys(record)))
    if forbidden:
        raise G3PreFitBoundaryError(
            "G3-P record contains forbidden row/fit fields: " + ", ".join(forbidden)
        )


def _record_sha256(record: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


# ---------------------------------------------------------------------------
# Record assembly
# ---------------------------------------------------------------------------


def resolve_doc_bindings(project_root: str | Path) -> dict[str, object]:
    """Bind every tracked authorization document to its pre-execution hash."""

    root = Path(project_root).expanduser().resolve()
    bindings: dict[str, object] = {}
    for relative, pinned in PINNED_DOC_SHA256.items():
        target = root / relative
        if not target.is_file():
            raise G3PreFitBoundaryError(f"tracked document is missing: {relative}")
        observed = sha256_file(target)
        if observed != pinned:
            raise G3PreFitBoundaryError(f"{relative} SHA-256 mismatch")
        bindings[relative] = {
            "expected": pinned,
            "observed": observed,
            "match": True,
            "binding_status": PINNED_DOC_BINDING_STATUS,
        }
    return bindings


def _authorization_binding(
    *,
    code_identity: str,
    branch: str,
    doc_bindings: Mapping[str, object],
) -> dict[str, object]:
    return {
        "gate_literal": G3P_GATE_LITERAL,
        "gate_id": G3P_GATE_ID,
        "record_version": G3P_RECORD_VERSION,
        "exploration_scope_id": EXPLORATION_SCOPE_ID,
        "base_commit": G3_AUTHORIZED_BASE_COMMIT,
        "branch": branch,
        "code_identity": code_identity,
        "allowed_changed_files": sorted(G3I_ALLOWED_CHANGED_FILES),
        "authorization_identity": G3P_AUTHORIZATION_IDENTITY,
        "document_bindings": dict(doc_bindings),
    }


def assemble_g3p_pre_fit_record(
    evidence: G3PreFitEvidence,
    *,
    code_identity: str,
    branch: str,
    doc_bindings: Mapping[str, object],
    guard_witness: Mapping[str, object],
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    """Build the aggregate/hash-only pre-fit support record.

    Both support outcomes stop before fitting. A passing support gate is
    recorded as `SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED` with zero fits and a
    deferred disposition; it never implies that G3-F became authorized.
    """

    _git_sha(code_identity, field_name="code_identity")
    if branch != G3_BRANCH:
        raise G3PreFitBoundaryError(f"G3-P must execute on branch {G3_BRANCH}")
    if int(guard_witness.get("blocked_fit_calls", -1)) != 0:
        raise G3PreFitBoundaryError("G3-P attempted a blocked fit/bootstrap/economic call")
    loaded_after_decode = databento_modules_loaded()

    targets = evidence.targets
    preflight = evidence.preflight
    if preflight.real_models_fitted != 0:
        raise G3PreFitBoundaryError("G3-P preflight reported a real model fit")
    if preflight.validation_rows_read != 0 or preflight.final_test_rows_read != 0:
        raise G3PreFitBoundaryError("G3-P preflight crossed a sealed outer boundary")
    if targets.cell12_reconciliation_status != CELL12_FULL_COVERAGE_PASS:
        raise G3PreFitBoundaryError("G3-P requires exact full-coverage Cell 12 reconciliation")
    if targets.cell12_absent_rows != 0:
        raise G3PreFitBoundaryError("G3-P requires CELL12_ABSENT_ROWS to be zero")
    if evidence.decoded_identity.row_count != EXPECTED_DECODED_ROW_COUNT:
        raise G3PreFitBoundaryError("decoded Cell 2 row count is not canonical")
    if (
        evidence.decoded_identity.timestamp_min_utc
        != EXPECTED_DECODED_TIMESTAMP_MIN_UTC
        or evidence.decoded_identity.timestamp_max_utc
        != EXPECTED_DECODED_TIMESTAMP_MAX_UTC
    ):
        raise G3PreFitBoundaryError("decoded Cell 2 timestamp range is not canonical")

    authorization_binding = _authorization_binding(
        code_identity=code_identity,
        branch=branch,
        doc_bindings=doc_bindings,
    )
    authorization_record_sha256 = sha256_bytes(
        canonical_json_bytes(canonicalize_audit(authorization_binding))
    )
    run_context = build_real_l1_run_context(
        evidence.metadata,
        evidence.prepared,
        targets,
        evidence.assembly.coverage,
        decoded_identity=evidence.decoded_identity,
        authorization_identity=G3P_AUTHORIZATION_IDENTITY,
        authorization_record_sha256=authorization_record_sha256,
    )
    support_gate_status, disposition, fit_status = support_outcome(
        bool(preflight.support_gate.passed)
    )
    context_record = run_context.as_record(real_models_fitted=0, fit_status=fit_status)
    if context_record["real_models_fitted"] != 0:
        raise G3PreFitBoundaryError("G3-P record cannot claim a real model fit")

    counters = dict(_ZERO_COUNTERS)
    counters["validation_rows_read"] = int(context_record["validation_rows_read"])
    counters["final_test_rows_read"] = int(context_record["final_test_rows_read"])
    counters["validation_path_bar_lookup_count"] = targets.validation_path_bar_lookup_count
    counters["final_test_path_bar_lookup_count"] = targets.final_test_path_bar_lookup_count
    counters["cell12_absent_rows"] = targets.cell12_absent_rows
    counters["blocked_fit_calls"] = int(guard_witness["blocked_fit_calls"])
    if counters != _ZERO_COUNTERS:
        raise G3PreFitBoundaryError("G3-P requires every blocked-access counter to be zero")

    record_core: dict[str, object] = {
        "gate_id": G3P_GATE_ID,
        "gate_literal": G3P_GATE_LITERAL,
        "record_version": G3P_RECORD_VERSION,
        "exploration_scope_id": EXPLORATION_SCOPE_ID,
        "base_commit": G3_AUTHORIZED_BASE_COMMIT,
        "branch": branch,
        "code_identity": code_identity,
        "access_level": G3P_ACCESS_LEVEL,
        "status": G3P_STATUS,
        "authorization_binding": authorization_binding,
        "authorization_record_sha256": authorization_record_sha256,
        "authorization_record_scope": G3P_AUTHORIZATION_RECORD_SCOPE,
        "harness_status": context_record["harness_status"],
        "source_identity": context_record["source_identity"],
        "role_assignment_identity": context_record["role_assignment_identity"],
        "metadata_identity": {
            "release_manifest_sha256": evidence.metadata.release_manifest_sha256,
            "control_manifest_sha256": evidence.metadata.control_manifest_sha256,
            "ordered_feature_content_sha256_declared": (
                evidence.metadata.ordered_feature_content_sha256_declared
            ),
            "artifact_byte_sha256": {
                artifact.artifact_id: artifact.byte_sha256
                for artifact in evidence.metadata.artifacts
            },
            "artifact_parquet_row_count": {
                artifact.artifact_id: artifact.parquet_row_count
                for artifact in evidence.metadata.artifacts
            },
        },
        "cell14_run_binding": dict(evidence.cell14_run_binding),
        "decoded_identity": {
            "content_sha256": evidence.decoded_identity.content_sha256,
            "row_count": evidence.decoded_identity.row_count,
            "timestamp_min_utc": evidence.decoded_identity.timestamp_min_utc,
            "timestamp_max_utc": evidence.decoded_identity.timestamp_max_utc,
            "hash_scope": evidence.decoded_identity.hash_scope,
            "hash_columns": list(CELL2_HASH_COLUMNS),
            "hash_includes_index": CELL2_HASH_INCLUDES_INDEX,
            "hash_algorithm": CELL2_HASH_ALGORITHM,
            "hash_projection_id": CELL2_HASH_PROJECTION_ID,
            "decoded_content_status": DECODED_CONTENT_STATUS_RECOMPUTED,
            "databento_modules_loaded": list(loaded_after_decode),
        },
        "request_seal": {
            "request_set_sha256": evidence.sealed.request_set_sha256,
            "split_assignment_sha256": evidence.sealed.split_assignment_sha256,
            "sealed_decision_count": len(evidence.sealed.decisions),
            "sealed_key_count": evidence.sealed.key_count,
            "path_bar_offsets": PATH_BAR_COUNT,
            "parent_role_scope": "OUTER_TRAIN_ONLY",
            "outer_validation_boundary_utc": (
                OUTER_VALIDATION_BOUNDARY_UTC.isoformat().replace("+00:00", "Z")
            ),
            "final_test_boundary_utc": (
                FINAL_TEST_BOUNDARY_UTC.isoformat().replace("+00:00", "Z")
            ),
            "hashed_before_lookup": True,
        },
        "train_access": {
            "physical_outer_train_predicate_asserted": (
                evidence.prepared.physical_train_predicate_asserted
            ),
            "cell8_role_binding_asserted": evidence.prepared.cell8_role_binding_asserted,
            "feature_max_source_time_asserted": bool(
                context_record["feature_max_source_time_asserted"]
            ),
            "availability_policy_id": evidence.prepared.availability_policy_id,
            "real_train_target_path_rows_read": int(
                context_record["real_train_target_path_rows_read"]
            ),
            "missing_path_bar_keys": int(context_record["missing_path_bar_keys"]),
            "native_instrument_mismatch_keys": int(
                context_record["native_instrument_mismatch_keys"]
            ),
        },
        "target_parameterization": {
            "take_profit_ticks": TAKE_PROFIT_TICKS,
            "stop_ticks": STOP_TICKS,
            "tick_size_points": TICK_SIZE_POINTS,
            "path_bar_offsets": PATH_BAR_COUNT,
            "target_identity": "PATH_LONG_FIRST_TOUCH_TP16_SL8_OFFSETS0_59_V1",
            "ambiguity_rule": "AMBIGUOUS_SAME_BAR_FAIL_CLOSED_EXCLUDE_AND_FLAT",
        },
        "target_coverage": _target_coverage_aggregate(targets),
        "cell12_reconciliation": _cell12_aggregate(targets),
        "coverage": _coverage_aggregate(evidence.assembly.coverage),
        "retained_identity": {
            "pooled_retained_sha256": preflight.pooled_retained_sha256,
            "folds": {
                fold.fold_id: {
                    "train_retained_sha256": fold.train_retained_sha256,
                    "holdout_retained_sha256": fold.holdout_retained_sha256,
                    "boundary_gap_minutes": fold.boundary_gap_minutes,
                    "embargo_minutes": 0,
                    "retained_rows": fold.retained_rows,
                    "retained_sessions": fold.retained_sessions,
                }
                for fold in preflight.folds
            },
        },
        "support_gate": {
            "status": support_gate_status,
            "passed": bool(preflight.support_gate.passed),
            "failures": list(preflight.support_gate.failures),
            "folds": {
                fold.fold_id: _ess_aggregate(fold.ess_support) for fold in preflight.folds
            },
            "pooled": _ess_aggregate(preflight.pooled_ess_support),
            "floor_policy_id": "FROZEN_TEST2_ESS_AND_CLASS_SUPPORT_FLOORS_V1",
            "floors_relaxed": False,
        },
        "fit_authorization": {
            "fit_status": context_record["fit_status"],
            "real_models_fitted": context_record["real_models_fitted"],
            "search_budget_models": 2,
            "frozen_model_definitions": [NUISANCE_MODEL_ID, FULL_MODEL_ID],
            "g3f_gate": G3F_GATE_LITERAL,
            "g3f_status": G3F_STATUS,
            "stops_before_fit_on_support_pass": True,
            "stops_before_fit_on_support_fail": True,
        },
        "search_budget": {
            "barrier_sets_constructed": 1,
            "frozen_model_definitions": 2,
            "models_consumed": 0,
            "fold_fit_calls_consumed": 0,
        },
        "counters": counters,
        "not_performed": list(_NOT_PERFORMED),
        "fit_guard_witness": dict(guard_witness),
        "cell12_coverage_policy_id": CELL12_COVERAGE_POLICY_ID,
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "disposition": disposition,
    }
    run_seed = sha256_bytes(canonical_json_bytes(canonicalize_audit(record_core)))
    record = {
        **record_core,
        "run_id": f"MES_T2_G3P_{run_seed[:16].upper()}",
        "audit_written_utc": audit_written_utc
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _assert_closed_record(record)
    record["record_sha256"] = _record_sha256(record)
    return record


# ---------------------------------------------------------------------------
# Create-once record output
# ---------------------------------------------------------------------------


def write_g3p_pre_fit_record(
    record: Mapping[str, object],
    *,
    output_root: str | Path,
) -> Path:
    """Publish the record exactly once under a fresh run directory."""

    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("MES_T2_G3P_"):
        raise G3PreFitBoundaryError("G3-P record has a malformed run_id")
    root = Path(output_root).expanduser().resolve()
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output = run_dir / G3P_RECORD_FILENAME
    descriptor = -1
    temporary_output: Path | None = None
    published = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{G3P_RECORD_FILENAME}.",
            suffix=".tmp",
            dir=run_dir,
        )
        temporary_output = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_output, output)
        published = True
        temporary_output.unlink()
        temporary_output = None
        directory_descriptor = os.open(run_dir, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_output is not None:
            temporary_output.unlink(missing_ok=True)
        if published:
            output.unlink(missing_ok=True)
        if run_dir.exists() and not any(run_dir.iterdir()):
            run_dir.rmdir()
        raise
    return output


def terminal_witness_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    counters = record.get("counters")
    support_gate = record.get("support_gate")
    cell12 = record.get("cell12_reconciliation")
    decoded = record.get("decoded_identity")
    fit_authorization = record.get("fit_authorization")
    train_access = record.get("train_access")
    target_coverage = record.get("target_coverage")
    request_seal = record.get("request_seal")
    search_budget = record.get("search_budget")
    if not all(
        isinstance(section, Mapping)
        for section in (
            counters,
            support_gate,
            cell12,
            decoded,
            fit_authorization,
            train_access,
            target_coverage,
            request_seal,
            search_budget,
        )
    ):
        raise G3PreFitBoundaryError("G3-P record witness sections are malformed")
    if counters != _ZERO_COUNTERS:
        raise G3PreFitBoundaryError("G3-P terminal witness requires the exact zero counters")
    if record.get("final_test_status") != "SEALED":
        raise G3PreFitBoundaryError("G3-P terminal witness requires Final Test to remain sealed")
    if fit_authorization.get("g3f_status") != G3F_STATUS:
        raise G3PreFitBoundaryError("G3-P terminal witness requires G3-F to remain unauthorized")
    if decoded.get("decoded_content_status") != DECODED_CONTENT_STATUS_RECOMPUTED:
        raise G3PreFitBoundaryError("G3-P terminal witness requires a recomputed decode")
    targets_constructed = int(target_coverage["total_rows"])
    sealed_decisions = int(request_seal["sealed_decision_count"])
    cell12_rows = int(cell12["expectation_rows"])
    if not targets_constructed == sealed_decisions == cell12_rows:
        raise G3PreFitBoundaryError("G3-P target/request/Cell 12 row counts do not reconcile")
    rows_read = int(train_access["real_train_target_path_rows_read"])
    missing_keys = int(train_access["missing_path_bar_keys"])
    if rows_read + missing_keys != int(request_seal["sealed_key_count"]):
        raise G3PreFitBoundaryError("G3-P path-read counters do not reconcile to the seal")
    if search_budget != {
        "barrier_sets_constructed": 1,
        "frozen_model_definitions": 2,
        "models_consumed": 0,
        "fold_fit_calls_consumed": 0,
    }:
        raise G3PreFitBoundaryError("G3-P search-budget witness is malformed")
    return (
        "G3P_PRE_FIT_PASS_NO_FIT_EXECUTED",
        f"REAL_TRAIN_TARGET_PATH_ROWS_READ={rows_read}",
        f"TARGETS_CONSTRUCTED={targets_constructed}",
        f"MISSING_PATH_BAR_KEYS={missing_keys}",
        (
            "NATIVE_INSTRUMENT_MISMATCH_KEYS="
            f"{train_access['native_instrument_mismatch_keys']}"
        ),
        f"CELL12_RECONCILED_ROWS={cell12_rows}",
        "BARRIER_SETS_CONSTRUCTED=1",
        "SEARCH_BUDGET_MODELS_CONSUMED=0",
        f"REAL_MODELS_FITTED={counters['real_models_fitted']}",
        f"REAL_FOLD_FIT_CALLS={counters['real_fold_fit_calls']}",
        f"BOOTSTRAP_REPLICATES={counters['bootstrap_replicates']}",
        f"ECONOMIC_DIAGNOSTIC_CALLS={counters['economic_diagnostic_calls']}",
        f"BLOCKED_FIT_CALLS={counters['blocked_fit_calls']}",
        f"DECODED_CONTENT_STATUS={decoded['decoded_content_status']}",
        f"CELL12_RECONCILIATION_STATUS={cell12['reconciliation_status']}",
        f"CELL12_ABSENT_ROWS={counters['cell12_absent_rows']}",
        f"VALIDATION_ROWS_READ={counters['validation_rows_read']}",
        f"FINAL_TEST={record['final_test_status']}",
        f"SUPPORT_GATE_STATUS={support_gate['status']}",
        f"DISPOSITION={record['disposition']}",
        f"G3F_STATUS={fit_authorization['g3f_status']}",
    )


# ---------------------------------------------------------------------------
# Git execution firewall
# ---------------------------------------------------------------------------


def _git_output(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_execution_context(project_root: Path) -> tuple[str, str]:
    branch = _git_output(project_root, "branch", "--show-current")
    if branch != G3_BRANCH:
        raise G3PreFitBoundaryError(f"G3-P must execute on branch {G3_BRANCH}")
    code_identity = _git_output(project_root, "rev-parse", "HEAD")
    _git_sha(code_identity, field_name="code_identity")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", G3_AUTHORIZED_BASE_COMMIT, code_identity],
        cwd=project_root,
        check=False,
    )
    if ancestor.returncode != 0:
        raise G3PreFitBoundaryError("G3-P code identity does not descend from the authorized base")
    changed_files = tuple(
        filter(
            None,
            _git_output(
                project_root,
                "diff",
                "--name-only",
                f"{G3_AUTHORIZED_BASE_COMMIT}..{code_identity}",
            ).splitlines(),
        )
    )
    failures = changed_file_firewall_failures(changed_files)
    if failures:
        raise G3PreFitBoundaryError(
            "G3-I changed-file firewall mismatch; " + "; ".join(failures)
        )
    tracked_status = _git_output(
        project_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
    )
    if tracked_status:
        raise G3PreFitBoundaryError("G3-P execution requires a clean tracked worktree")
    try:
        upstream_identity = _git_output(project_root, "rev-parse", "@{upstream}")
    except subprocess.CalledProcessError as exc:
        raise G3PreFitBoundaryError("G3-P branch must have a pushed upstream") from exc
    if upstream_identity != code_identity:
        raise G3PreFitBoundaryError("G3-P local and upstream code identities must match")
    return code_identity, branch


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Owner-only Test 2 G3-P pre-fit evidence run. The frozen science "
            "carries no command-line knobs."
        )
    )
    parser.add_argument("--gate", choices=(G3P_GATE_LITERAL,), required=True)
    parser.add_argument("--raw-dbn", type=Path, required=True)
    parser.add_argument("--cell8", type=Path, required=True)
    parser.add_argument("--cell10", type=Path, required=True)
    parser.add_argument("--cell12", type=Path, required=True)
    parser.add_argument("--cell14-features", type=Path, required=True)
    parser.add_argument("--cell14-run-id", required=True)
    parser.add_argument(
        "--cell14-manifest",
        type=Path,
        default=Path("manifests/releases/cell14_local_release_v1.json"),
    )
    parser.add_argument(
        "--frozen-manifest",
        type=Path,
        default=Path("manifests/releases/frozen_colab_manifest_v1.json"),
    )
    parser.add_argument("--output-root", type=Path, default=Path(G3P_OUTPUT_SUBPATH))
    return parser


def run_g3p_pre_fit(
    paths: CanonicalArtifactPaths,
    *,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
    cell14_run_id: str,
    code_identity: str,
    branch: str,
    doc_bindings: Mapping[str, object],
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    """Collect evidence and assemble the record with every fit path blocked."""

    with pre_fit_only_guard() as guard:
        evidence = collect_g3p_pre_fit_evidence(
            paths,
            cell14_release_manifest_path=cell14_release_manifest_path,
            frozen_colab_manifest_path=frozen_colab_manifest_path,
            cell14_run_id=cell14_run_id,
        )
        if guard.blocked_fit_calls != 0:
            raise G3PreFitBoundaryError("G3-P attempted a blocked call during collection")
        record = assemble_g3p_pre_fit_record(
            evidence,
            code_identity=code_identity,
            branch=branch,
            doc_bindings=doc_bindings,
            guard_witness=guard.witness(),
            audit_written_utc=audit_written_utc,
        )
    return record


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: str | Path | None = None,
) -> int:
    args = _parser().parse_args(argv)
    root = Path(project_root or Path.cwd()).expanduser().resolve()
    allowed_output_root = (root / G3P_OUTPUT_SUBPATH).resolve()
    output_root = (
        args.output_root.resolve()
        if args.output_root.is_absolute()
        else (root / args.output_root).resolve()
    )
    if output_root != allowed_output_root:
        raise G3PreFitBoundaryError(f"G3-P output_root must be exactly {allowed_output_root}")
    code_identity, branch = _git_execution_context(root)
    doc_bindings = resolve_doc_bindings(root)
    paths = CanonicalArtifactPaths(
        raw_dbn=args.raw_dbn,
        cell8_assignments=args.cell8,
        cell10_labels=args.cell10,
        cell12_paths=args.cell12,
        cell14_features=args.cell14_features,
    )
    record = run_g3p_pre_fit(
        paths,
        cell14_release_manifest_path=(root / args.cell14_manifest),
        frozen_colab_manifest_path=(root / args.frozen_manifest),
        cell14_run_id=args.cell14_run_id,
        code_identity=code_identity,
        branch=branch,
        doc_bindings=doc_bindings,
    )
    witness_lines = terminal_witness_lines(record)
    output = write_g3p_pre_fit_record(record, output_root=output_root)
    print(f"G3P_RECORD={output}")
    print(f"G3P_RECORD_SHA256={record['record_sha256']}")
    for line in witness_lines:
        print(line)
    return 0


__all__ = [
    "G3P_ACCESS_LEVEL",
    "G3P_GATE_ID",
    "G3P_GATE_LITERAL",
    "G3P_PATH_BAR_BATCH_SIZE",
    "G3PreFitBoundaryError",
    "G3PreFitEvidence",
    "assemble_g3p_pre_fit_record",
    "collect_g3p_pre_fit_evidence",
    "main",
    "pre_fit_only_guard",
    "resolve_doc_bindings",
    "run_g3p_pre_fit",
    "terminal_witness_lines",
    "write_g3p_pre_fit_record",
]

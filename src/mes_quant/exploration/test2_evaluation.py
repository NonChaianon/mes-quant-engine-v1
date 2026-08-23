from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

import numpy as np

from mes_quant.core.hashing import canonical_json_bytes, sha256_bytes
from mes_quant.exploration.l1_lr001 import (
    ARMIJO_CONSTANT,
    BACKTRACK_SHRINK,
    GRADIENT_TOL,
    L2_LAMBDA,
    MAX_ITERATIONS,
    MINIMUM_STEP,
    fit_frozen_logistic,
)
from mes_quant.exploration.test2_diagnostics import EconomicSignal, build_economic_diagnostics
from mes_quant.exploration.test2_g3f_contract import FoldFitBudget
from mes_quant.exploration.test2_path_contract import (
    CAPACITY_POLICY_ID,
    EXPLORATION_SCOPE_ID,
    FULL_MODEL_ID,
    MDE_VS_NUISANCE,
    MDE_VS_PRIOR,
    NUISANCE_FEATURES,
    NUISANCE_MODEL_ID,
    OUTER_VALIDATION_BOUNDARY_UTC,
    RELEASE_POLICY_ID,
    STOP_TICKS,
    TAKE_PROFIT_TICKS,
    TICK_SIZE_POINTS,
)
from mes_quant.exploration.test2_run_context import EvaluationRunContext
from mes_quant.exploration.test2_stats import (
    BOOTSTRAP_REPETITIONS,
    FOLD_ORDER,
    MASTER_SEED,
    DependenceRow,
    EssSupportSummary,
    PairedBootstrapResult,
    SessionLossAggregate,
    SupportGateResult,
    compute_ess_support,
    evaluate_support_floors,
    required_paired_bootstraps,
    stepwise_average_precision,
)
from mes_quant.exploration.test2_target import PathTargetRow
from mes_quant.features.contract import FEATURE_COLUMNS

PRIOR_MODEL_ID = "FOLD_TRAIN_PRIOR"
CONSUMER_ORDER = (PRIOR_MODEL_ID, NUISANCE_MODEL_ID, FULL_MODEL_ID)
MINIMUM_BOUNDARY_GAP_MINUTES = 60.0
MINIMUM_BOOTSTRAP_SESSIONS = 20
READY_FOR_SYNTHETIC_FIT = "READY_FOR_SYNTHETIC_FIT"
INCONCLUSIVE_UNDERPOWERED = "INCONCLUSIVE_UNDERPOWERED"
INTERESTING_ENOUGH_TO_CONTINUE = "INTERESTING_ENOUGH_TO_CONTINUE"
NOT_INTERESTING_ENOUGH = "NOT_INTERESTING_ENOUGH"


class Test2EvaluationContractError(ValueError):
    """Raised before fitting when a frozen Test 2 evaluation gate is violated."""


def _fit_with_authority(
    train: np.ndarray,
    labels: np.ndarray,
    *,
    model_id: str,
    fold_id: str,
    authority: FoldFitBudget,
) -> tuple[np.ndarray, Mapping[str, object]]:
    """Consume before fitting and expose only a coefficient identity afterward."""

    permit = authority.consume(model_id=model_id, fold_id=fold_id)
    beta, optimizer = fit_frozen_logistic(train, labels)
    coefficient_dimension = int(beta.size)
    identity_prefix = canonical_json_bytes(
        {
            "coefficient_dimension": coefficient_dimension,
            "fold_id": fold_id,
            "model_id": model_id,
        }
    )
    beta_sha256 = sha256_bytes(
        identity_prefix
        + np.ascontiguousarray(beta, dtype="<f8").tobytes(order="C")
    )
    gradient_norm = float(optimizer["gradient_inf_norm"])
    authority.complete_fit(
        permit,
        model_id=model_id,
        fold_id=fold_id,
        beta_sha256=beta_sha256,
        coefficient_dimension=coefficient_dimension,
        optimizer_converged=(
            np.isfinite(gradient_norm) and gradient_norm <= GRADIENT_TOL
        ),
    )
    return beta, optimizer


@dataclass(frozen=True)
class ConsumerRetainedIndex:
    train_row_ids: tuple[str, ...]
    holdout_row_ids: tuple[str, ...]


@dataclass(frozen=True)
class FoldEvaluationData:
    fold_id: str
    train_features: np.ndarray
    train_labels: Sequence[int]
    train_row_ids: tuple[str, ...]
    train_decision_times: tuple[datetime, ...]
    holdout_features: np.ndarray
    holdout_labels: Sequence[int]
    holdout_gross_move_points_60m: Sequence[float]
    holdout_row_ids: tuple[str, ...]
    holdout_decision_times: tuple[datetime, ...]
    holdout_session_ids: tuple[str, ...]
    consumer_indices: Mapping[str, ConsumerRetainedIndex]
    holdout_target_rows: tuple[PathTargetRow, ...] = ()


@dataclass(frozen=True)
class StandardizedFold:
    train: np.ndarray
    holdout: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    zero_variance_features: tuple[str, ...]


@dataclass(frozen=True)
class FoldPreflight:
    fold_id: str
    train_retained_sha256: str
    holdout_retained_sha256: str
    boundary_gap_minutes: float
    retained_rows: int
    retained_sessions: int
    ess_support: EssSupportSummary


@dataclass(frozen=True)
class EvaluationPreflight:
    status: str
    folds: tuple[FoldPreflight, ...]
    pooled_retained_sha256: str
    pooled_ess_support: EssSupportSummary
    support_gate: SupportGateResult
    validation_rows_read: int = 0
    final_test_rows_read: int = 0
    real_models_fitted: int = 0


@dataclass(frozen=True)
class ImprovementMetrics:
    improvement_vs_prior: float
    improvement_vs_nuisance: float


@dataclass(frozen=True)
class ContinuationDecision:
    disposition: str
    passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class FoldModelRun:
    fold_id: str
    prior_log_loss: float
    nuisance_log_loss: float
    full_log_loss: float
    nuisance_average_precision: float
    full_average_precision: float
    nuisance_optimizer: Mapping[str, object]
    full_optimizer: Mapping[str, object]


@dataclass(frozen=True)
class Test2Evaluation:
    preflight: EvaluationPreflight
    fold_runs: tuple[FoldModelRun, ...]
    bootstraps: tuple[PairedBootstrapResult, ...]
    decision: ContinuationDecision | None
    experiment_records: tuple[Mapping[str, object], ...]
    synthetic_fitter_calls: int
    pooled_primary_metrics: Mapping[str, float] = field(default_factory=dict)
    economic_diagnostic_calls: int = 0


SyntheticEvaluation = Test2Evaluation


def _validate_ids(values: tuple[str, ...], *, field: str) -> None:
    if not values:
        raise Test2EvaluationContractError(f"{field} must not be empty")
    if any(not isinstance(value, str) or not value for value in values):
        raise Test2EvaluationContractError(f"{field} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise Test2EvaluationContractError(f"{field} must be unique")


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Test2EvaluationContractError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _validated_times(
    values: tuple[datetime, ...],
    *,
    expected_rows: int,
    field: str,
) -> tuple[datetime, ...]:
    if len(values) != expected_rows:
        raise Test2EvaluationContractError(f"{field} row count mismatch")
    normalized = tuple(_utc(value, field=field) for value in values)
    if any(value >= OUTER_VALIDATION_BOUNDARY_UTC for value in normalized):
        raise Test2EvaluationContractError(f"{field} would open outer Validation or later")
    return normalized


def _binary_labels(values: Sequence[int], *, expected_rows: int, field: str) -> np.ndarray:
    labels = np.asarray(values)
    if labels.ndim != 1 or labels.size != expected_rows:
        raise Test2EvaluationContractError(f"{field} row count mismatch")
    if labels.dtype == np.bool_ or not np.isin(labels, (0, 1)).all():
        raise Test2EvaluationContractError(f"{field} must contain integer 0 or 1")
    return labels.astype(np.int8)


def _feature_matrix(values: np.ndarray, *, field: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_COLUMNS):
        raise Test2EvaluationContractError(f"{field} must have the frozen 29-feature width")
    if matrix.shape[0] == 0 or not np.isfinite(matrix).all():
        raise Test2EvaluationContractError(f"{field} must be non-empty and finite")
    return matrix


def _retained_hash(fold_id: str, role: str, row_ids: tuple[str, ...]) -> str:
    return sha256_bytes(canonical_json_bytes([[fold_id, role, row_id] for row_id in row_ids]))


def standardize_fold(
    train_features: np.ndarray,
    holdout_features: np.ndarray,
    *,
    feature_names: Sequence[str],
) -> StandardizedFold:
    train = np.asarray(train_features, dtype=np.float64)
    holdout = np.asarray(holdout_features, dtype=np.float64)
    names = tuple(feature_names)
    if train.ndim != 2 or holdout.ndim != 2:
        raise Test2EvaluationContractError("feature matrices must be two-dimensional")
    if not names or train.shape[1] != len(names) or holdout.shape[1] != len(names):
        raise Test2EvaluationContractError("feature names must exactly match matrix width")
    if len(set(names)) != len(names) or any(not isinstance(name, str) or not name for name in names):
        raise Test2EvaluationContractError("feature names must be unique non-empty strings")
    if train.shape[0] == 0 or holdout.shape[0] == 0:
        raise Test2EvaluationContractError("feature matrices must be non-empty")
    if not np.isfinite(train).all() or not np.isfinite(holdout).all():
        raise Test2EvaluationContractError("non-finite feature values reached preprocessing")

    mean = train.mean(axis=0)
    scale = train.std(axis=0, ddof=0)
    zero_mask = (~np.isfinite(scale)) | (scale <= np.finfo(np.float64).eps)
    scale = scale.copy()
    scale[zero_mask] = 1.0
    return StandardizedFold(
        train=(train - mean) / scale,
        holdout=(holdout - mean) / scale,
        mean=mean,
        scale=scale,
        zero_variance_features=tuple(
            name for name, is_zero in zip(names, zero_mask, strict=True) if is_zero
        ),
    )


def _validate_consumer_indices(fold: FoldEvaluationData) -> None:
    if set(fold.consumer_indices) != set(CONSUMER_ORDER):
        raise Test2EvaluationContractError(
            f"consumer indices must contain exactly {CONSUMER_ORDER}"
        )
    for consumer_id in CONSUMER_ORDER:
        retained = fold.consumer_indices[consumer_id]
        if not isinstance(retained, ConsumerRetainedIndex):
            raise Test2EvaluationContractError("consumer retained index type mismatch")
        if retained.train_row_ids != fold.train_row_ids:
            raise Test2EvaluationContractError(
                f"{fold.fold_id}/{consumer_id} TRAIN retained rows diverged"
            )
        if retained.holdout_row_ids != fold.holdout_row_ids:
            raise Test2EvaluationContractError(
                f"{fold.fold_id}/{consumer_id} holdout retained rows diverged"
            )


def _validate_holdout_targets(fold: FoldEvaluationData, holdout_labels: np.ndarray) -> None:
    if not fold.holdout_target_rows:
        return
    if len(fold.holdout_target_rows) != len(fold.holdout_row_ids):
        raise Test2EvaluationContractError("holdout target-row count mismatch")
    for row_id, label, gross_move, target in zip(
        fold.holdout_row_ids,
        holdout_labels,
        fold.holdout_gross_move_points_60m,
        fold.holdout_target_rows,
        strict=True,
    ):
        if not isinstance(target, PathTargetRow) or target.decision_identity != row_id:
            raise Test2EvaluationContractError("holdout target-row identity mismatch")
        if not target.retained or target.path_long != int(label):
            raise Test2EvaluationContractError("holdout target row is not the retained label")
        if target.gross_move_points_60m != float(gross_move):
            raise Test2EvaluationContractError("holdout target gross move mismatch")


def preflight_evaluation(folds: Sequence[FoldEvaluationData]) -> EvaluationPreflight:
    materialized = tuple(folds)
    if tuple(fold.fold_id for fold in materialized) != FOLD_ORDER:
        raise Test2EvaluationContractError(f"fold order must be exactly {FOLD_ORDER}")

    fold_results: list[FoldPreflight] = []
    fold_summaries: dict[str, EssSupportSummary] = {}
    pooled_dependence_rows: list[DependenceRow] = []
    pooled_identity_rows: list[list[str]] = []
    seen_holdout_ids: set[str] = set()
    for fold in materialized:
        train_matrix = _feature_matrix(fold.train_features, field=f"{fold.fold_id} TRAIN")
        holdout_matrix = _feature_matrix(
            fold.holdout_features, field=f"{fold.fold_id} holdout"
        )
        train_rows = train_matrix.shape[0]
        holdout_rows = holdout_matrix.shape[0]
        _binary_labels(fold.train_labels, expected_rows=train_rows, field="TRAIN labels")
        holdout_labels = _binary_labels(
            fold.holdout_labels, expected_rows=holdout_rows, field="holdout labels"
        )
        _validate_ids(fold.train_row_ids, field=f"{fold.fold_id} TRAIN row IDs")
        _validate_ids(fold.holdout_row_ids, field=f"{fold.fold_id} holdout row IDs")
        if len(fold.train_row_ids) != train_rows or len(fold.holdout_row_ids) != holdout_rows:
            raise Test2EvaluationContractError("retained row ID count does not match features")
        if set(fold.train_row_ids).intersection(fold.holdout_row_ids):
            raise Test2EvaluationContractError(f"{fold.fold_id} TRAIN and holdout overlap")
        repeated = seen_holdout_ids.intersection(fold.holdout_row_ids)
        if repeated:
            raise Test2EvaluationContractError("OOF holdout row IDs repeat across folds")
        seen_holdout_ids.update(fold.holdout_row_ids)
        train_times = _validated_times(
            fold.train_decision_times,
            expected_rows=train_rows,
            field=f"{fold.fold_id} TRAIN decision times",
        )
        holdout_times = _validated_times(
            fold.holdout_decision_times,
            expected_rows=holdout_rows,
            field=f"{fold.fold_id} holdout decision times",
        )
        boundary_gap = (min(holdout_times) - max(train_times)).total_seconds() / 60.0
        if boundary_gap < MINIMUM_BOUNDARY_GAP_MINUTES:
            raise Test2EvaluationContractError(
                f"{fold.fold_id} boundary gap is below 60 minutes"
            )
        if len(fold.holdout_session_ids) != holdout_rows:
            raise Test2EvaluationContractError("holdout session ID count mismatch")
        if any(not isinstance(value, str) or not value for value in fold.holdout_session_ids):
            raise Test2EvaluationContractError("holdout session IDs must be non-empty strings")
        session_count = len(set(fold.holdout_session_ids))
        if session_count < MINIMUM_BOOTSTRAP_SESSIONS:
            raise Test2EvaluationContractError(
                f"{fold.fold_id} requires at least 20 sessions for frozen diagnostics"
            )
        gross = np.asarray(fold.holdout_gross_move_points_60m, dtype=np.float64)
        if gross.ndim != 1 or gross.size != holdout_rows or not np.isfinite(gross).all():
            raise Test2EvaluationContractError("holdout gross-move rows must align and be finite")
        _validate_holdout_targets(fold, holdout_labels)
        _validate_consumer_indices(fold)

        dependence_rows = [
            DependenceRow(
                fold_id=fold.fold_id,
                session_id=session_id,
                decision_time=decision_time,
                path_long=int(label),
                gross_move_points_60m=float(gross_move),
            )
            for session_id, decision_time, label, gross_move in zip(
                fold.holdout_session_ids,
                holdout_times,
                holdout_labels,
                gross,
                strict=True,
            )
        ]
        summary = compute_ess_support(dependence_rows)
        fold_summaries[fold.fold_id] = summary
        pooled_dependence_rows.extend(dependence_rows)
        pooled_identity_rows.extend(
            [[fold.fold_id, "HOLDOUT", row_id] for row_id in fold.holdout_row_ids]
        )
        fold_results.append(
            FoldPreflight(
                fold_id=fold.fold_id,
                train_retained_sha256=_retained_hash(
                    fold.fold_id, "TRAIN", fold.train_row_ids
                ),
                holdout_retained_sha256=_retained_hash(
                    fold.fold_id, "HOLDOUT", fold.holdout_row_ids
                ),
                boundary_gap_minutes=boundary_gap,
                retained_rows=holdout_rows,
                retained_sessions=session_count,
                ess_support=summary,
            )
        )

    pooled_summary = compute_ess_support(pooled_dependence_rows)
    support_gate = evaluate_support_floors(fold_summaries, pooled_summary)
    return EvaluationPreflight(
        status=READY_FOR_SYNTHETIC_FIT if support_gate.passed else INCONCLUSIVE_UNDERPOWERED,
        folds=tuple(fold_results),
        pooled_retained_sha256=sha256_bytes(canonical_json_bytes(pooled_identity_rows)),
        pooled_ess_support=pooled_summary,
        support_gate=support_gate,
    )


def _finite_metric(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Test2EvaluationContractError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise Test2EvaluationContractError(f"{field} must be finite")
    return numeric


def decide_continuation(
    fold_metrics: Mapping[str, ImprovementMetrics],
    pooled_metrics: ImprovementMetrics,
    *,
    lower_bound_vs_prior: float,
    lower_bound_vs_nuisance: float,
    support_gate: SupportGateResult,
    governance_gates_passed: bool,
) -> ContinuationDecision:
    if set(fold_metrics) != set(FOLD_ORDER):
        raise Test2EvaluationContractError(f"fold metrics must contain exactly {FOLD_ORDER}")
    failures: list[str] = []
    for fold_id in FOLD_ORDER:
        metrics = fold_metrics[fold_id]
        prior = _finite_metric(metrics.improvement_vs_prior, field="improvement_vs_prior")
        nuisance = _finite_metric(
            metrics.improvement_vs_nuisance, field="improvement_vs_nuisance"
        )
        if prior <= MDE_VS_PRIOR:
            failures.append(f"{fold_id}: improvement versus prior did not exceed 0.0075")
        if nuisance <= MDE_VS_NUISANCE:
            failures.append(f"{fold_id}: improvement versus nuisance did not exceed 0.0075")
    pooled_prior = _finite_metric(
        pooled_metrics.improvement_vs_prior, field="pooled improvement_vs_prior"
    )
    pooled_nuisance = _finite_metric(
        pooled_metrics.improvement_vs_nuisance, field="pooled improvement_vs_nuisance"
    )
    if pooled_prior <= MDE_VS_PRIOR:
        failures.append("OOF_POOLED: improvement versus prior did not exceed 0.0075")
    if pooled_nuisance <= MDE_VS_NUISANCE:
        failures.append("OOF_POOLED: improvement versus nuisance did not exceed 0.0075")
    if _finite_metric(lower_bound_vs_prior, field="lower_bound_vs_prior") <= 0.0:
        failures.append("pooled lower bound versus prior did not exceed zero")
    if _finite_metric(lower_bound_vs_nuisance, field="lower_bound_vs_nuisance") <= 0.0:
        failures.append("pooled lower bound versus nuisance did not exceed zero")
    if not support_gate.passed:
        failures.extend(support_gate.failures)
    if governance_gates_passed is not True:
        failures.append("source/role/availability/ambiguity/access/search-budget gate failed")
    return ContinuationDecision(
        disposition=(INTERESTING_ENOUGH_TO_CONTINUE if not failures else NOT_INTERESTING_ENOUGH),
        passed=not failures,
        failures=tuple(failures),
    )


def _loss_from_logits(labels: np.ndarray, logits: np.ndarray) -> np.ndarray:
    losses = np.logaddexp(0.0, logits) - labels * logits
    if not np.isfinite(losses).all():
        raise Test2EvaluationContractError("non-finite binary log loss")
    return losses


def _probabilities(logits: np.ndarray) -> np.ndarray:
    values = np.exp(-np.logaddexp(0.0, -logits))
    if not np.isfinite(values).all():
        raise Test2EvaluationContractError("non-finite model probabilities")
    return values


def _roc_auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    positives = int(labels.sum())
    negatives = int(labels.size - positives)
    if positives == 0 or negatives == 0:
        return float("nan")
    order = np.argsort(probabilities, kind="stable")
    sorted_probabilities = probabilities[order]
    ranks = np.empty(labels.size, dtype=float)
    start = 0
    while start < labels.size:
        end = start + 1
        while end < labels.size and sorted_probabilities[end] == sorted_probabilities[start]:
            end += 1
        ranks[order[start:end]] = 0.5 * ((start + 1) + end)
        start = end
    rank_sum = float(ranks[labels == 1].sum())
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _ess_record(summary: EssSupportSummary) -> dict[str, object]:
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


def _linear_logits(features: np.ndarray, beta: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(features.shape[0]), features])
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        logits = design @ beta
    if not np.isfinite(logits).all():
        raise Test2EvaluationContractError("non-finite model logits")
    return logits


def _run_evaluation(
    folds: Sequence[FoldEvaluationData],
    *,
    timestamp_utc: datetime,
    code_identity: str,
    run_context: EvaluationRunContext,
    governance_gates_passed: bool = False,
    fold_fit_authority: FoldFitBudget | None = None,
) -> Test2Evaluation:
    """Run the frozen evaluator with an explicit, validated provenance context."""

    if not isinstance(run_context, EvaluationRunContext):
        raise Test2EvaluationContractError("run_context must be an EvaluationRunContext")
    real_non_fixture = not run_context.is_synthetic and not run_context.is_test_fixture
    if real_non_fixture and fold_fit_authority is None:
        raise Test2EvaluationContractError(
            "real TRAIN evaluation requires a fold-fit authority"
        )
    if not real_non_fixture and fold_fit_authority is not None:
        raise Test2EvaluationContractError(
            "synthetic or fixture evaluation cannot consume a real fold-fit authority"
        )
    if fold_fit_authority is not None and not isinstance(
        fold_fit_authority, FoldFitBudget
    ):
        raise Test2EvaluationContractError(
            "fold-fit authority must be a minted FoldFitBudget"
        )
    if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() is None:
        raise Test2EvaluationContractError("timestamp_utc must be timezone-aware")
    timestamp = timestamp_utc.astimezone(UTC)
    if not isinstance(code_identity, str) or not code_identity.strip():
        raise Test2EvaluationContractError("code_identity must be non-empty")
    materialized = tuple(folds)
    preflight = preflight_evaluation(materialized)
    if preflight.status == INCONCLUSIVE_UNDERPOWERED:
        context_record = run_context.as_record(
            real_models_fitted=0,
            fit_status="SKIPPED_INCONCLUSIVE_UNDERPOWERED",
        )
        timestamp_token = timestamp.strftime("%Y%m%dT%H%M%SZ")
        record = {
            "EXPERIMENT_ID": f"MES_TEST2_SUPPORT_GATE_{timestamp_token}",
            "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
            "EXPLORATION_SCOPE_ID": EXPLORATION_SCOPE_ID,
            "record_type": "TARGET_DERIVED_SUPPORT_GATE",
            "code_identity": code_identity.strip(),
            "access_level": context_record["access_level"],
            "harness_status": context_record["harness_status"],
            "authorization_identity": context_record["authorization_identity"],
            "authorization_record_sha256": context_record[
                "authorization_record_sha256"
            ],
            "source_identity": context_record["source_identity"],
            "role_assignment_identity": context_record["role_assignment_identity"],
            "request_set_sha256": context_record["request_set_sha256"],
            "retained_set_sha256": preflight.pooled_retained_sha256,
            "fold_ess_support": {
                fold.fold_id: _ess_record(fold.ess_support) for fold in preflight.folds
            },
            "pooled_ess_support": _ess_record(preflight.pooled_ess_support),
            "support_failures": preflight.support_gate.failures,
            "coverage_total_rows": context_record["total_rows"],
            "ambiguity_rows": context_record["ambiguity_rows"],
            "missing_rows": context_record["missing_rows"],
            "excluded_rows": context_record["excluded_rows"],
            "coverage_counter_scope": context_record["coverage_counter_scope"],
            "coverage_by_fold_decile": context_record["coverage_by_fold_decile"],
            "real_train_target_path_rows_read": context_record[
                "real_train_target_path_rows_read"
            ],
            "missing_path_bar_keys": context_record["missing_path_bar_keys"],
            "native_instrument_mismatch_keys": context_record[
                "native_instrument_mismatch_keys"
            ],
            "validation_rows_read": context_record["validation_rows_read"],
            "final_test_rows_read": context_record["final_test_rows_read"],
            "feature_max_source_time_asserted": context_record[
                "feature_max_source_time_asserted"
            ],
            "real_models_fitted": 0,
            "fit_status": context_record["fit_status"],
            "search_budget_models": 2,
            "governance_gates_passed": governance_gates_passed,
            "disposition": INCONCLUSIVE_UNDERPOWERED,
        }
        return Test2Evaluation(preflight, (), (), None, (record,), 0)
    if preflight.status != READY_FOR_SYNTHETIC_FIT:
        raise Test2EvaluationContractError("preflight is not ready for synthetic fitting")

    train_labels_by_fold: dict[str, np.ndarray] = {}
    for fold in materialized:
        labels = _binary_labels(
            fold.train_labels,
            expected_rows=len(fold.train_row_ids),
            field=f"{fold.fold_id} TRAIN labels",
        )
        prevalence = float(labels.mean())
        if prevalence <= 0.0 or prevalence >= 1.0:
            raise Test2EvaluationContractError(
                f"{fold.fold_id} TRAIN prior is degenerate"
            )
        train_labels_by_fold[fold.fold_id] = labels

    try:
        nuisance_indices = tuple(FEATURE_COLUMNS.index(name) for name in NUISANCE_FEATURES)
    except ValueError as exc:
        raise Test2EvaluationContractError(
            "frozen nuisance features are not exact members of the 29-feature catalog"
        ) from exc
    fold_runs: list[FoldModelRun] = []
    fold_metrics: dict[str, ImprovementMetrics] = {}
    fold_primary_results: dict[str, dict[str, float]] = {}
    session_tables: dict[str, tuple[SessionLossAggregate, ...]] = {}
    pooled_loss_sums = {"prior": 0.0, "nuisance": 0.0, "full": 0.0, "rows": 0}
    fitter_calls = 0
    optimizer_records: dict[str, dict[str, Mapping[str, object]]] = {
        NUISANCE_MODEL_ID: {}, FULL_MODEL_ID: {}
    }
    metric_records: dict[str, dict[str, dict[str, float]]] = {
        NUISANCE_MODEL_ID: {}, FULL_MODEL_ID: {}
    }
    economic_signals: list[EconomicSignal] = []
    if not run_context.is_synthetic and not all(
        fold.holdout_target_rows for fold in materialized
    ):
        raise Test2EvaluationContractError(
            "real L1 evaluation requires retained holdout target rows for economics"
        )
    for fold in materialized:
        train_labels = train_labels_by_fold[fold.fold_id]
        holdout_labels = np.asarray(fold.holdout_labels, dtype=np.int8)
        train = np.asarray(fold.train_features, dtype=np.float64)
        holdout = np.asarray(fold.holdout_features, dtype=np.float64)
        nuisance = standardize_fold(
            train[:, nuisance_indices],
            holdout[:, nuisance_indices],
            feature_names=tuple(FEATURE_COLUMNS[index] for index in nuisance_indices),
        )
        full = standardize_fold(train, holdout, feature_names=FEATURE_COLUMNS)
        if fold_fit_authority is None:
            nuisance_beta, nuisance_optimizer = fit_frozen_logistic(
                nuisance.train, train_labels
            )
        else:
            nuisance_beta, nuisance_optimizer = _fit_with_authority(
                nuisance.train,
                train_labels,
                model_id=NUISANCE_MODEL_ID,
                fold_id=fold.fold_id,
                authority=fold_fit_authority,
            )
        fitter_calls += 1
        if fold_fit_authority is None:
            full_beta, full_optimizer = fit_frozen_logistic(full.train, train_labels)
        else:
            full_beta, full_optimizer = _fit_with_authority(
                full.train,
                train_labels,
                model_id=FULL_MODEL_ID,
                fold_id=fold.fold_id,
                authority=fold_fit_authority,
            )
        fitter_calls += 1
        nuisance_logits = _linear_logits(nuisance.holdout, nuisance_beta)
        full_logits = _linear_logits(full.holdout, full_beta)
        prior_probability = float(train_labels.mean())
        prior_logit = math.log(prior_probability / (1.0 - prior_probability))
        prior_logits = np.full(holdout_labels.size, prior_logit)
        prior_losses = _loss_from_logits(holdout_labels, prior_logits)
        nuisance_losses = _loss_from_logits(holdout_labels, nuisance_logits)
        full_losses = _loss_from_logits(holdout_labels, full_logits)
        nuisance_probabilities = _probabilities(nuisance_logits)
        full_probabilities = _probabilities(full_logits)
        if fold.holdout_target_rows:
            economic_signals.extend(
                EconomicSignal(
                    fold_id=fold.fold_id,
                    decision_identity=row_id,
                    session_id=session_id,
                    decision_time=decision_time,
                    probability_long=float(probability),
                    target_row=target_row,
                )
                for row_id, session_id, decision_time, probability, target_row in zip(
                    fold.holdout_row_ids,
                    fold.holdout_session_ids,
                    fold.holdout_decision_times,
                    full_probabilities,
                    fold.holdout_target_rows,
                    strict=True,
                )
            )
        prior_mean = float(prior_losses.mean())
        nuisance_mean = float(nuisance_losses.mean())
        full_mean = float(full_losses.mean())
        fold_metrics[fold.fold_id] = ImprovementMetrics(
            prior_mean - full_mean, nuisance_mean - full_mean
        )
        fold_primary_results[fold.fold_id] = {
            "prior_log_loss": prior_mean,
            "nuisance_log_loss": nuisance_mean,
            "full_log_loss": full_mean,
            "improvement_vs_prior": prior_mean - full_mean,
            "improvement_vs_nuisance": nuisance_mean - full_mean,
            "nuisance_improvement_vs_prior": prior_mean - nuisance_mean,
        }
        optimizer_records[NUISANCE_MODEL_ID][fold.fold_id] = {
            **nuisance_optimizer,
            "zero_variance_features": nuisance.zero_variance_features,
        }
        optimizer_records[FULL_MODEL_ID][fold.fold_id] = {
            **full_optimizer,
            "zero_variance_features": full.zero_variance_features,
        }
        metric_records[NUISANCE_MODEL_ID][fold.fold_id] = {
            "log_loss": nuisance_mean,
            "brier_score": float(np.mean((nuisance_probabilities - holdout_labels) ** 2)),
            "roc_auc": _roc_auc(holdout_labels, nuisance_probabilities),
            "average_precision": stepwise_average_precision(
                holdout_labels, nuisance_probabilities
            ),
        }
        metric_records[FULL_MODEL_ID][fold.fold_id] = {
            "log_loss": full_mean,
            "brier_score": float(np.mean((full_probabilities - holdout_labels) ** 2)),
            "roc_auc": _roc_auc(holdout_labels, full_probabilities),
            "average_precision": stepwise_average_precision(
                holdout_labels, full_probabilities
            ),
        }
        fold_runs.append(
            FoldModelRun(
                fold.fold_id,
                prior_mean,
                nuisance_mean,
                full_mean,
                stepwise_average_precision(holdout_labels, nuisance_probabilities),
                stepwise_average_precision(holdout_labels, full_probabilities),
                optimizer_records[NUISANCE_MODEL_ID][fold.fold_id],
                optimizer_records[FULL_MODEL_ID][fold.fold_id],
            )
        )
        aggregates: list[SessionLossAggregate] = []
        first_time_by_session: dict[str, datetime] = {}
        for session_id, decision_time in zip(
            fold.holdout_session_ids, fold.holdout_decision_times, strict=True
        ):
            first_time_by_session[session_id] = min(
                first_time_by_session.get(session_id, decision_time), decision_time
            )
        for session_id in sorted(first_time_by_session, key=first_time_by_session.get):
            mask = np.asarray([value == session_id for value in fold.holdout_session_ids])
            aggregates.append(
                SessionLossAggregate(
                    fold.fold_id,
                    session_id,
                    int(mask.sum()),
                    float(prior_losses[mask].sum()),
                    float(nuisance_losses[mask].sum()),
                    float(full_losses[mask].sum()),
                )
            )
        session_tables[fold.fold_id] = tuple(aggregates)
        pooled_loss_sums["prior"] += float(prior_losses.sum())
        pooled_loss_sums["nuisance"] += float(nuisance_losses.sum())
        pooled_loss_sums["full"] += float(full_losses.sum())
        pooled_loss_sums["rows"] += holdout_labels.size

    bootstraps = required_paired_bootstraps(session_tables)
    primary = bootstraps[0]
    rows = pooled_loss_sums["rows"]
    pooled_metrics = ImprovementMetrics(
        (pooled_loss_sums["prior"] - pooled_loss_sums["full"]) / rows,
        (pooled_loss_sums["nuisance"] - pooled_loss_sums["full"]) / rows,
    )
    decision = decide_continuation(
        fold_metrics,
        pooled_metrics,
        lower_bound_vs_prior=primary.lower_bound_vs_prior,
        lower_bound_vs_nuisance=primary.lower_bound_vs_nuisance,
        support_gate=preflight.support_gate,
        governance_gates_passed=governance_gates_passed,
    )
    timestamp_token = timestamp.strftime("%Y%m%dT%H%M%SZ")
    fold_preflight_by_id = {fold.fold_id: fold for fold in preflight.folds}
    bootstrap_records = tuple(
        {
            "block_length_sessions": bootstrap.block_length,
            "repetitions": bootstrap.repetitions,
            "pooled_seed": bootstrap.pooled_seed,
            "fold_seeds": bootstrap.fold_seeds,
            "draw_identity_sha256": bootstrap.draw_identity_sha256,
            "method_id": "PAIRED_NONCIRCULAR_CONSECUTIVE_SESSION_MOVING_BLOCK_V1",
            "comparison_scope": "PATHFULL001_VS_PRIOR_AND_PATHNUISANCE001",
            "draw_pairing": "PRIOR_NUISANCE_FULL_IDENTICAL_INDICES_WITHIN_REPLICATE",
            "pooled_resampling": "FOLDS_INDEPENDENT_THEN_ROW_WEIGHTED_CONCATENATION",
            "remainder_rule": "CONCATENATE_THEN_TRUNCATE_NO_PAD_NO_WRAP",
            "lower_bound_vs_prior": bootstrap.lower_bound_vs_prior,
            "lower_bound_vs_nuisance": bootstrap.lower_bound_vs_nuisance,
            "percentile": bootstrap.percentile,
            "quantile_method": "linear",
        }
        for bootstrap in bootstraps
    )
    fixture_or_synthetic = run_context.is_synthetic or run_context.is_test_fixture
    real_models_fitted = 0 if fixture_or_synthetic else len((NUISANCE_MODEL_ID, FULL_MODEL_ID))
    real_fold_fits = 0 if fixture_or_synthetic else fitter_calls
    context_record = run_context.as_record(real_models_fitted=real_models_fitted)
    if economic_signals:
        economic_diagnostics = {
            "source_model_id": FULL_MODEL_ID,
            **build_economic_diagnostics(economic_signals),
        }
        economic_diagnostic_calls = 1
    else:
        economic_diagnostics = context_record["economic_diagnostics"]
        economic_diagnostic_calls = 0
    records = tuple(
        {
            "EXPERIMENT_ID": f"MES_TEST2_{model_id}_{timestamp_token}",
            "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
            "EXPLORATION_SCOPE_ID": EXPLORATION_SCOPE_ID,
            "model_id": model_id,
            "access_level": context_record["access_level"],
            "harness_status": context_record["harness_status"],
            "code_identity": code_identity.strip(),
            "identity_block": {
                "source_identity": context_record["source_identity"],
                "role_assignment_identity": context_record[
                    "role_assignment_identity"
                ],
                "feature_set_identity": sha256_bytes(
                    canonical_json_bytes(list(FEATURE_COLUMNS))
                ),
                "target_identity": "PATH_LONG_FIRST_TOUCH_TP16_SL8_OFFSETS0_59_V1",
                "cost_identity": "CONSERVATIVE_ROUND_TRIP_0.994_POINTS_4.97_USD",
                "environment_identity": (
                    f"NUMPY_{np.__version__}_PYTHON_API_"
                    f"{context_record['access_level']}"
                ),
                "authorization_identity": context_record[
                    "authorization_identity"
                ],
                "authorization_record_sha256": context_record[
                    "authorization_record_sha256"
                ],
                "request_set_sha256": context_record["request_set_sha256"],
            },
            "model_family": "L2_REGULARIZED_BINARY_LOGISTIC_REGRESSION",
            "fixed_parameters": {
                "l2_lambda": L2_LAMBDA,
                "max_iterations": MAX_ITERATIONS,
                "gradient_inf_tolerance": GRADIENT_TOL,
                "armijo_constant": ARMIJO_CONSTANT,
                "backtracking_shrink": BACKTRACK_SHRINK,
                "minimum_step": MINIMUM_STEP,
                "intercept": "FITTED_UNPENALIZED",
                "class_weighting": "NONE",
            },
            "preprocessing": "FOLD_LOCAL_TRAIN_MEAN_POPULATION_SD_ZERO_SCALE_TO_ONE",
            "retained_set_sha256": preflight.pooled_retained_sha256,
            "folds": FOLD_ORDER,
            "fold_preflight": {
                fold_id: {
                    "train_retained_sha256": fold_preflight_by_id[
                        fold_id
                    ].train_retained_sha256,
                    "holdout_retained_sha256": fold_preflight_by_id[
                        fold_id
                    ].holdout_retained_sha256,
                    "boundary_gap_minutes": fold_preflight_by_id[
                        fold_id
                    ].boundary_gap_minutes,
                    "embargo_minutes": 0,
                    "ess_support": _ess_record(
                        fold_preflight_by_id[fold_id].ess_support
                    ),
                }
                for fold_id in FOLD_ORDER
            },
            "pooled_ess_support": _ess_record(preflight.pooled_ess_support),
            "features": (
                tuple(FEATURE_COLUMNS[index] for index in nuisance_indices)
                if model_id == NUISANCE_MODEL_ID
                else tuple(FEATURE_COLUMNS)
            ),
            "optimizer": optimizer_records[model_id],
            "primary_metric": "OOF_BINARY_LOG_LOSS",
            "fold_metrics": metric_records[model_id],
            "primary_results": (
                {
                    "folds": fold_primary_results,
                    "pooled": {
                        "prior_log_loss": pooled_loss_sums["prior"] / rows,
                        "nuisance_log_loss": pooled_loss_sums["nuisance"] / rows,
                        "full_log_loss": pooled_loss_sums["full"] / rows,
                        "improvement_vs_prior": pooled_metrics.improvement_vs_prior,
                        "improvement_vs_nuisance": pooled_metrics.improvement_vs_nuisance,
                        "nuisance_improvement_vs_prior": (
                            pooled_loss_sums["prior"] - pooled_loss_sums["nuisance"]
                        )
                        / rows,
                    },
                    "scope": "PATHFULL001_CONTINUATION_GATE",
                }
                if model_id == FULL_MODEL_ID
                else {
                    "folds": {
                        fold_id: {
                            "prior_log_loss": values["prior_log_loss"],
                            "nuisance_log_loss": values["nuisance_log_loss"],
                            "nuisance_improvement_vs_prior": values[
                                "nuisance_improvement_vs_prior"
                            ],
                        }
                        for fold_id, values in fold_primary_results.items()
                    },
                    "pooled": {
                        "prior_log_loss": pooled_loss_sums["prior"] / rows,
                        "nuisance_log_loss": pooled_loss_sums["nuisance"] / rows,
                        "nuisance_improvement_vs_prior": (
                            pooled_loss_sums["prior"] - pooled_loss_sums["nuisance"]
                        )
                        / rows,
                    },
                    "scope": "PATHNUISANCE001_BASELINE_DIAGNOSTIC_ONLY",
                }
            ),
            "mde_vs_prior": MDE_VS_PRIOR,
            "mde_vs_nuisance": MDE_VS_NUISANCE,
            "diagnostic_probability_threshold": 0.5,
            "diagnostic_threshold_semantics": "COVERAGE_ONLY_NOT_ECONOMIC_BREAK_EVEN",
            "take_profit_ticks": TAKE_PROFIT_TICKS,
            "stop_ticks": STOP_TICKS,
            "tick_size_points": TICK_SIZE_POINTS,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_master_seed": MASTER_SEED,
            "bootstrap_quantile_method": "linear",
            "bootstrap": bootstrap_records,
            "effective_events_per_non_intercept_coefficient": {
                fold_id: min(
                    fold_preflight_by_id[fold_id].ess_support.effective_negative_support,
                    fold_preflight_by_id[fold_id].ess_support.effective_positive_support,
                )
                / (4 if model_id == NUISANCE_MODEL_ID else len(FEATURE_COLUMNS))
                for fold_id in FOLD_ORDER
            },
            "effective_events_below_10_disclosure": {
                fold_id: min(
                    fold_preflight_by_id[fold_id].ess_support.effective_negative_support,
                    fold_preflight_by_id[fold_id].ess_support.effective_positive_support,
                )
                / (4 if model_id == NUISANCE_MODEL_ID else len(FEATURE_COLUMNS))
                < 10.0
                for fold_id in FOLD_ORDER
            },
            "coverage_total_rows": context_record["total_rows"],
            "ambiguity_rows": context_record["ambiguity_rows"],
            "missing_rows": context_record["missing_rows"],
            "excluded_rows": context_record["excluded_rows"],
            "coverage_counter_scope": context_record["coverage_counter_scope"],
            "coverage_by_fold_decile": context_record[
                "coverage_by_fold_decile"
            ],
            "economic_diagnostics": (
                economic_diagnostics
                if model_id == FULL_MODEL_ID
                else {
                    "status": "NOT_COMPUTED_BASELINE_RECORD",
                    "source_model_id": None,
                }
            ),
            "search_budget_models": 2,
            "release_policy_id": RELEASE_POLICY_ID,
            "capacity_policy_id": CAPACITY_POLICY_ID,
            "real_train_target_path_rows_read": context_record[
                "real_train_target_path_rows_read"
            ],
            "missing_path_bar_keys": context_record["missing_path_bar_keys"],
            "native_instrument_mismatch_keys": context_record[
                "native_instrument_mismatch_keys"
            ],
            "validation_rows_read": context_record["validation_rows_read"],
            "final_test_rows_read": context_record["final_test_rows_read"],
            "feature_max_source_time_asserted": context_record[
                "feature_max_source_time_asserted"
            ],
            "real_models_fitted": context_record["real_models_fitted"],
            "run_synthetic_fitter_calls": fitter_calls if fixture_or_synthetic else 0,
            "model_synthetic_fitter_calls": (
                len(FOLD_ORDER) if fixture_or_synthetic else 0
            ),
            "run_real_fold_fitter_calls": real_fold_fits,
            "model_real_fold_fitter_calls": (
                len(FOLD_ORDER) if real_fold_fits else 0
            ),
            "governance_gates_passed": governance_gates_passed,
            "decision_failures": decision.failures,
            "disposition": (
                "BASELINE_NOT_ELIGIBLE"
                if model_id == NUISANCE_MODEL_ID
                else decision.disposition
            ),
        }
        for model_id in (NUISANCE_MODEL_ID, FULL_MODEL_ID)
    )
    return Test2Evaluation(
        preflight,
        tuple(fold_runs),
        bootstraps,
        decision,
        records,
        fitter_calls,
        {
            "prior_log_loss": pooled_loss_sums["prior"] / rows,
            "nuisance_log_loss": pooled_loss_sums["nuisance"] / rows,
            "full_log_loss": pooled_loss_sums["full"] / rows,
            "improvement_vs_prior": pooled_metrics.improvement_vs_prior,
            "improvement_vs_nuisance": pooled_metrics.improvement_vs_nuisance,
        },
        economic_diagnostic_calls,
    )


def run_synthetic_evaluation(
    folds: Sequence[FoldEvaluationData],
    *,
    timestamp_utc: datetime,
    code_identity: str,
    governance_gates_passed: bool = False,
) -> Test2Evaluation:
    """Exercise Test 2 using only caller-supplied synthetic in-memory rows."""

    return _run_evaluation(
        folds,
        timestamp_utc=timestamp_utc,
        code_identity=code_identity,
        run_context=EvaluationRunContext.synthetic(),
        governance_gates_passed=governance_gates_passed,
    )


def run_authorized_train_evaluation(
    folds: Sequence[FoldEvaluationData],
    *,
    timestamp_utc: datetime,
    code_identity: str,
    run_context: EvaluationRunContext,
    governance_gates_passed: bool,
    fold_fit_authority: FoldFitBudget | None = None,
) -> Test2Evaluation:
    """Run L1 only with a non-fixture TRAIN-only authorization context."""

    if run_context.is_synthetic or run_context.is_test_fixture:
        raise Test2EvaluationContractError(
            "authorized TRAIN evaluation requires a real non-fixture L1 context"
        )
    if governance_gates_passed is not True:
        raise Test2EvaluationContractError(
            "authorized TRAIN evaluation requires all governance gates to pass"
        )
    if fold_fit_authority is None:
        raise Test2EvaluationContractError(
            "authorized TRAIN evaluation requires a fold-fit authority"
        )
    return _run_evaluation(
        folds,
        timestamp_utc=timestamp_utc,
        code_identity=code_identity,
        run_context=run_context,
        governance_gates_passed=True,
        fold_fit_authority=fold_fit_authority,
    )

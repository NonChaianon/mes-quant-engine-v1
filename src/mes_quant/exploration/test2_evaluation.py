from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np

from mes_quant.core.hashing import canonical_json_bytes, sha256_bytes
from mes_quant.exploration.test2_path_contract import (
    FULL_MODEL_ID,
    MDE_VS_NUISANCE,
    MDE_VS_PRIOR,
    NUISANCE_MODEL_ID,
    OUTER_VALIDATION_BOUNDARY_UTC,
)
from mes_quant.exploration.test2_stats import (
    FOLD_ORDER,
    DependenceRow,
    EssSupportSummary,
    SupportGateResult,
    compute_ess_support,
    evaluate_support_floors,
)
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

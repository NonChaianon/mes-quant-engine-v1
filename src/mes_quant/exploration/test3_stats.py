from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import pairwise
from numbers import Integral, Real

import numpy as np

from mes_quant.exploration.test3_contract import (
    BOOTSTRAP_REPETITIONS,
    FOLD_ORDER,
    MASTER_SEED,
    PRIMARY_BLOCK_LENGTH,
    REAL_FOLD_FIT_BUDGET,
    RELATIVE_QLIKE_REDUCTION_FLOOR,
    REQUIRED_BLOCK_LENGTHS,
    TerminalDisposition,
)


class Test3StatsContractError(ValueError):
    """Raised when statistical inputs violate the frozen Test 3 contract."""

    __test__ = False


@dataclass(frozen=True)
class DependenceRow:
    fold_id: str
    session_id: str
    decision_time: datetime
    realized_variance: float


@dataclass(frozen=True)
class LagDiagnostic:
    lag: int
    pairs: int
    rho_observed: float | None
    rho_null: float
    excess: float | None


@dataclass(frozen=True)
class DependenceSummary:
    row_count: int
    lags: tuple[LagDiagnostic, ...]
    design_effect: float
    effective_sample_size: float
    status: str = "DESCRIPTIVE_NOT_A_PASS_GATE"


@dataclass(frozen=True)
class SessionImprovementAggregate:
    fold_id: str
    session_id: str
    session_date: date
    row_count: int
    improvement_sum: float


@dataclass(frozen=True)
class PairedBootstrapResult:
    block_length: int
    repetitions: int
    pooled_seed: int
    fold_seeds: tuple[tuple[str, int], ...]
    draw_identity_sha256: str
    replicate_improvements: tuple[float, ...]
    lower_bound: float
    percentile: float = 0.05


@dataclass(frozen=True)
class ContinuationInputs:
    assertions_passed: bool
    fold_mean_improvements: tuple[tuple[str, float], ...]
    pooled_mean_qlike_base: float
    pooled_mean_qlike_har: float
    primary_lower_bound: float
    real_fold_fit_calls: int
    underpowered: bool = False


@dataclass(frozen=True)
class ContinuationDecision:
    disposition: TerminalDisposition
    relative_qlike_reduction: float | None
    failures: tuple[str, ...]


def _finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise Test3StatsContractError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise Test3StatsContractError(f"{field} must be finite")
    return numeric


def qlike(actual_variance: Sequence[float], forecast_variance: Sequence[float]) -> np.ndarray:
    if len(actual_variance) != len(forecast_variance) or len(actual_variance) == 0:
        raise Test3StatsContractError("actual and forecast must have equal non-zero length")
    actual = np.asarray(actual_variance, dtype=np.float64)
    forecast = np.asarray(forecast_variance, dtype=np.float64)
    if not np.all(np.isfinite(actual)) or not np.all(np.isfinite(forecast)):
        raise Test3StatsContractError("QLIKE inputs must be finite")
    if np.any(actual <= 0.0) or np.any(forecast <= 0.0):
        raise Test3StatsContractError("QLIKE inputs must be strictly positive")
    ratio = actual / forecast
    losses = ratio - np.log(ratio) - 1.0
    if not np.all(np.isfinite(losses)):
        raise Test3StatsContractError("QLIKE output must be finite")
    return losses


def relative_qlike_reduction(mean_base: float, mean_har: float) -> float:
    base = _finite(mean_base, field="mean_base")
    har = _finite(mean_har, field="mean_har")
    if base <= 0.0:
        raise Test3StatsContractError("baseline mean QLIKE must be positive")
    if har < 0.0:
        raise Test3StatsContractError("challenger mean QLIKE must be non-negative")
    return (base - har) / base


def duan_smearing_factor(training_residuals: Sequence[float]) -> float:
    if len(training_residuals) == 0:
        raise Test3StatsContractError("training_residuals must be non-empty")
    residuals = np.asarray(training_residuals, dtype=np.float64)
    if not np.all(np.isfinite(residuals)):
        raise Test3StatsContractError("training_residuals must be finite")
    factor = float(np.mean(np.exp(residuals)))
    if not math.isfinite(factor) or factor <= 0.0:
        raise Test3StatsContractError("Duan smearing factor must be positive and finite")
    return factor


def back_transform_log_variance(
    predicted_log_variance: Sequence[float],
    smearing_factor: float,
) -> np.ndarray:
    factor = _finite(smearing_factor, field="smearing_factor")
    if factor <= 0.0:
        raise Test3StatsContractError("smearing_factor must be positive")
    predictions = np.asarray(predicted_log_variance, dtype=np.float64)
    if predictions.ndim != 1 or predictions.size == 0 or not np.all(np.isfinite(predictions)):
        raise Test3StatsContractError("predicted_log_variance must be finite, one-dimensional")
    forecasts = np.exp(predictions) * factor
    if not np.all(np.isfinite(forecasts)) or np.any(forecasts <= 0.0):
        raise Test3StatsContractError("back-transformed forecasts must be positive and finite")
    return forecasts


def overlap_null(lag: int) -> float:
    if isinstance(lag, bool) or not isinstance(lag, Integral) or not 1 <= int(lag) <= 8:
        raise Test3StatsContractError("lag must be an integer in 1..8")
    return max(1.0 - int(lag) / 4.0, 0.0)


def dependence_summary(rows: Iterable[DependenceRow]) -> DependenceSummary:
    materialized = tuple(rows)
    if not materialized:
        raise Test3StatsContractError("dependence audit requires at least one row")
    sessions: dict[tuple[str, str], list[DependenceRow]] = defaultdict(list)
    seen: set[tuple[str, str, datetime]] = set()
    for row in materialized:
        if not isinstance(row, DependenceRow):
            raise Test3StatsContractError("rows must contain DependenceRow")
        if row.fold_id not in FOLD_ORDER:
            raise Test3StatsContractError(f"fold_id must be one of {FOLD_ORDER}")
        if not isinstance(row.session_id, str) or not row.session_id:
            raise Test3StatsContractError("session_id must be non-empty")
        if row.decision_time.tzinfo is None or row.decision_time.utcoffset() is None:
            raise Test3StatsContractError("decision_time must be timezone-aware")
        variance = _finite(row.realized_variance, field="realized_variance")
        if variance <= 0.0:
            raise Test3StatsContractError("realized_variance must be strictly positive")
        key = (row.fold_id, row.session_id, row.decision_time)
        if key in seen:
            raise Test3StatsContractError("dependence keys must be unique")
        seen.add(key)
        sessions[(row.fold_id, row.session_id)].append(row)
    for session_rows in sessions.values():
        if any(
            current.decision_time <= previous.decision_time
            for previous, current in pairwise(session_rows)
        ):
            raise Test3StatsContractError("dependence rows must be chronological within session")

    diagnostics: list[LagDiagnostic] = []
    positive_rhos: list[float] = []
    for lag in range(1, 9):
        current_values: list[float] = []
        prior_values: list[float] = []
        expected_delta = timedelta(minutes=15 * lag)
        for session_rows in sessions.values():
            for index in range(lag, len(session_rows)):
                current = session_rows[index]
                prior = session_rows[index - lag]
                if current.decision_time - prior.decision_time != expected_delta:
                    continue
                current_values.append(float(current.realized_variance))
                prior_values.append(float(prior.realized_variance))
        observed: float | None = None
        if len(current_values) >= 2:
            current_array = np.asarray(current_values, dtype=np.float64)
            prior_array = np.asarray(prior_values, dtype=np.float64)
            if current_array.std() > 0.0 and prior_array.std() > 0.0:
                candidate = float(np.corrcoef(current_array, prior_array)[0, 1])
                if math.isfinite(candidate):
                    observed = candidate
                    positive_rhos.append(max(candidate, 0.0))
        null = overlap_null(lag)
        diagnostics.append(
            LagDiagnostic(
                lag=lag,
                pairs=len(current_values),
                rho_observed=observed,
                rho_null=null,
                excess=None if observed is None else observed - null,
            )
        )
    design_effect = max(1.0, 1.0 + 2.0 * sum(positive_rhos))
    return DependenceSummary(
        row_count=len(materialized),
        lags=tuple(diagnostics),
        design_effect=design_effect,
        effective_sample_size=len(materialized) / design_effect,
    )


def moving_block_indices(
    n_sessions: int,
    block_length: int,
    repetitions: int,
    rng: np.random.Generator,
) -> np.ndarray:
    for value, field in (
        (n_sessions, "n_sessions"),
        (block_length, "block_length"),
        (repetitions, "repetitions"),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral) or int(value) <= 0:
            raise Test3StatsContractError(f"{field} must be a positive integer")
    if block_length > n_sessions:
        raise Test3StatsContractError("block_length may not exceed n_sessions")
    blocks_needed = math.ceil(n_sessions / block_length)
    max_start = n_sessions - block_length
    draws = np.empty((repetitions, n_sessions), dtype=np.int32)
    for repetition in range(repetitions):
        starts = rng.integers(0, max_start + 1, size=blocks_needed)
        draws[repetition] = np.concatenate(
            [np.arange(start, start + block_length, dtype=np.int32) for start in starts]
        )[:n_sessions]
    return draws


def _validated_session_tables(
    fold_session_tables: Mapping[str, Iterable[SessionImprovementAggregate]],
    *,
    block_length: int,
) -> dict[str, tuple[SessionImprovementAggregate, ...]]:
    if tuple(fold_session_tables) != FOLD_ORDER:
        raise Test3StatsContractError(f"session tables must follow exact fold order {FOLD_ORDER}")
    validated: dict[str, tuple[SessionImprovementAggregate, ...]] = {}
    for fold_id in FOLD_ORDER:
        rows = tuple(fold_session_tables[fold_id])
        if len(rows) < block_length:
            raise Test3StatsContractError(f"{fold_id} has fewer sessions than block length")
        seen: set[str] = set()
        previous_date: date | None = None
        for row in rows:
            if not isinstance(row, SessionImprovementAggregate) or row.fold_id != fold_id:
                raise Test3StatsContractError("session aggregate fold identity mismatch")
            if not isinstance(row.session_id, str) or not row.session_id or row.session_id in seen:
                raise Test3StatsContractError("session ids must be unique and non-empty")
            if type(row.session_date) is not date:
                raise Test3StatsContractError("session_date must be a date")
            if previous_date is not None and row.session_date <= previous_date:
                raise Test3StatsContractError("sessions must be in strict chronological order")
            seen.add(row.session_id)
            previous_date = row.session_date
            if isinstance(row.row_count, bool) or not isinstance(row.row_count, Integral):
                raise Test3StatsContractError("row_count must be an integer")
            if row.row_count <= 0:
                raise Test3StatsContractError("row_count must be positive")
            _finite(row.improvement_sum, field="improvement_sum")
        validated[fold_id] = rows
    return validated


def paired_session_block_bootstrap(
    fold_session_tables: Mapping[str, Iterable[SessionImprovementAggregate]],
    *,
    block_length: int = PRIMARY_BLOCK_LENGTH,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    master_seed: int = MASTER_SEED,
) -> PairedBootstrapResult:
    if block_length not in REQUIRED_BLOCK_LENGTHS:
        raise Test3StatsContractError(f"block_length must be one of {REQUIRED_BLOCK_LENGTHS}")
    if repetitions != BOOTSTRAP_REPETITIONS:
        raise Test3StatsContractError("bootstrap repetitions are frozen at 2000")
    if master_seed != MASTER_SEED:
        raise Test3StatsContractError("bootstrap master seed is frozen at 20260809")
    tables = _validated_session_tables(fold_session_tables, block_length=block_length)
    pooled_seed = master_seed + 90_000 + block_length
    fold_seeds: list[tuple[str, int]] = []
    sampled_rows: list[np.ndarray] = []
    sampled_improvements: list[np.ndarray] = []
    hash_parts: list[bytes] = []
    for fold_index, fold_id in enumerate(FOLD_ORDER):
        fold_seed = pooled_seed + 1_000 * (fold_index + 1)
        fold_seeds.append((fold_id, fold_seed))
        draws = moving_block_indices(
            len(tables[fold_id]),
            block_length,
            repetitions,
            np.random.default_rng(fold_seed),
        )
        ordered_sessions = "".join(
            f"{row.session_date.isoformat()}|{row.session_id}\n" for row in tables[fold_id]
        ).encode("utf-8")
        hash_parts.extend(
            (
                fold_id.encode("utf-8"),
                ordered_sessions,
                np.asarray(draws.shape, dtype=np.int64).tobytes(),
                draws.tobytes(order="C"),
            )
        )
        row_counts = np.asarray([row.row_count for row in tables[fold_id]], dtype=np.float64)
        improvements = np.asarray(
            [row.improvement_sum for row in tables[fold_id]], dtype=np.float64
        )
        sampled_rows.append(row_counts[draws].sum(axis=1))
        sampled_improvements.append(improvements[draws].sum(axis=1))
    pooled_rows = np.sum(sampled_rows, axis=0)
    pooled_improvements = np.sum(sampled_improvements, axis=0) / pooled_rows
    lower_bound = float(np.quantile(pooled_improvements, 0.05))
    return PairedBootstrapResult(
        block_length=block_length,
        repetitions=repetitions,
        pooled_seed=pooled_seed,
        fold_seeds=tuple(fold_seeds),
        draw_identity_sha256=hashlib.sha256(b"".join(hash_parts)).hexdigest(),
        replicate_improvements=tuple(float(value) for value in pooled_improvements),
        lower_bound=lower_bound,
    )


def decide_continuation(inputs: ContinuationInputs) -> ContinuationDecision:
    if not isinstance(inputs, ContinuationInputs):
        raise Test3StatsContractError("inputs must be ContinuationInputs")
    if inputs.underpowered:
        if inputs.real_fold_fit_calls != 0:
            raise Test3StatsContractError("underpowered stop must occur before any fit")
        return ContinuationDecision(TerminalDisposition.UNDERPOWERED, None, ("underpowered",))
    if not inputs.assertions_passed:
        return ContinuationDecision(TerminalDisposition.INVALID, None, ("assertions_failed",))
    if inputs.real_fold_fit_calls != REAL_FOLD_FIT_BUDGET:
        return ContinuationDecision(TerminalDisposition.INVALID, None, ("fit_budget",))
    if tuple(fold_id for fold_id, _ in inputs.fold_mean_improvements) != FOLD_ORDER:
        raise Test3StatsContractError(f"fold improvements must follow exact order {FOLD_ORDER}")
    fold_values = tuple(
        _finite(value, field=f"{fold_id}_mean_improvement")
        for fold_id, value in inputs.fold_mean_improvements
    )
    lower_bound = _finite(inputs.primary_lower_bound, field="primary_lower_bound")
    relative = relative_qlike_reduction(
        inputs.pooled_mean_qlike_base,
        inputs.pooled_mean_qlike_har,
    )
    failures: list[str] = []
    for fold_id, value in zip(FOLD_ORDER, fold_values, strict=True):
        if value <= 0.0:
            failures.append(f"{fold_id}_improvement_not_positive")
    if relative < RELATIVE_QLIKE_REDUCTION_FLOOR:
        failures.append("relative_qlike_reduction_below_0.10")
    if lower_bound <= 0.0:
        failures.append("primary_lower_bound_not_positive")
    disposition = (
        TerminalDisposition.NOT_INTERESTING if failures else TerminalDisposition.INTERESTING
    )
    return ContinuationDecision(disposition, relative, tuple(failures))

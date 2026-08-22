from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from numbers import Integral, Real

import numpy as np

MASTER_SEED = 20260809
BOOTSTRAP_REPETITIONS = 2_000
PRIMARY_BLOCK_LENGTH = 5
DIAGNOSTIC_BLOCK_LENGTHS = (1, 20)
REQUIRED_BLOCK_LENGTHS = (PRIMARY_BLOCK_LENGTH, *DIAGNOSTIC_BLOCK_LENGTHS)
FOLD_ORDER = ("WF_2022", "WF_2023")
PER_FOLD_ESS_FLOOR = 1_000.0
POOLED_ESS_FLOOR = 2_000.0
PER_CLASS_EFFECTIVE_SUPPORT_FLOOR = 200.0


class Test2StatsContractError(ValueError):
    """Raised when a Test 2 statistical input violates the frozen protocol."""


@dataclass(frozen=True)
class DependenceRow:
    fold_id: str
    session_id: str
    decision_time: datetime
    path_long: int
    gross_move_points_60m: float


@dataclass(frozen=True)
class LagDiagnostic:
    lag: int
    pairs: int
    rho: float | None


@dataclass(frozen=True)
class OutcomeDependence:
    outcome_name: str
    row_count: int
    lags: tuple[LagDiagnostic, ...]
    design_effect: float
    effective_sample_size: float
    status: str = "DESCRIPTIVE_NOT_FOR_CI"


@dataclass(frozen=True)
class EssSupportSummary:
    row_count: int
    path_long: OutcomeDependence
    gross_move_points_60m: OutcomeDependence
    governing_design_effect: float
    governing_effective_sample_size: float
    raw_negative_count: int
    raw_positive_count: int
    effective_negative_support: float
    effective_positive_support: float
    status: str = "DESCRIPTIVE_NOT_FOR_CI"


@dataclass(frozen=True)
class SupportGateResult:
    passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class SessionLossAggregate:
    fold_id: str
    session_id: str
    row_count: int
    prior_loss_sum: float
    nuisance_loss_sum: float
    full_loss_sum: float


@dataclass(frozen=True)
class PairedBootstrapResult:
    block_length: int
    repetitions: int
    pooled_seed: int
    fold_seeds: tuple[tuple[str, int], ...]
    improvement_vs_prior: tuple[float, ...]
    improvement_vs_nuisance: tuple[float, ...]
    lower_bound_vs_prior: float
    lower_bound_vs_nuisance: float
    percentile: float = 0.05


def _finite_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise Test2StatsContractError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise Test2StatsContractError(f"{field} must be finite")
    return numeric


def _validated_dependence_rows(rows: Iterable[DependenceRow]) -> tuple[DependenceRow, ...]:
    materialized = tuple(rows)
    if not materialized:
        raise Test2StatsContractError("dependence diagnostics require at least one row")

    validated: list[DependenceRow] = []
    seen_keys: set[tuple[str, str, datetime]] = set()
    for row in materialized:
        if not isinstance(row, DependenceRow):
            raise Test2StatsContractError("each dependence row must be a DependenceRow")
        if not isinstance(row.fold_id, str) or not row.fold_id:
            raise Test2StatsContractError("fold_id must be a non-empty string")
        if not isinstance(row.session_id, str) or not row.session_id:
            raise Test2StatsContractError("session_id must be a non-empty string")
        if not isinstance(row.decision_time, datetime):
            raise Test2StatsContractError("decision_time must be a datetime")
        if row.decision_time.tzinfo is None or row.decision_time.utcoffset() is None:
            raise Test2StatsContractError("decision_time must be timezone-aware")
        if isinstance(row.path_long, bool) or not isinstance(row.path_long, Integral):
            raise Test2StatsContractError("path_long must be integer 0 or 1")
        if int(row.path_long) not in (0, 1):
            raise Test2StatsContractError("path_long must be integer 0 or 1")
        gross = _finite_number(row.gross_move_points_60m, field="gross_move_points_60m")
        key = (row.fold_id, row.session_id, row.decision_time)
        if key in seen_keys:
            raise Test2StatsContractError("dependence row keys must be unique")
        seen_keys.add(key)
        validated.append(
            DependenceRow(
                fold_id=row.fold_id,
                session_id=row.session_id,
                decision_time=row.decision_time,
                path_long=int(row.path_long),
                gross_move_points_60m=gross,
            )
        )
    return tuple(validated)


def _outcome_dependence(
    rows: tuple[DependenceRow, ...],
    *,
    outcome_name: str,
) -> OutcomeDependence:
    sessions: dict[tuple[str, str], list[DependenceRow]] = defaultdict(list)
    for row in rows:
        sessions[(row.fold_id, row.session_id)].append(row)
    for session_rows in sessions.values():
        session_rows.sort(key=lambda row: row.decision_time)

    lag_diagnostics: list[LagDiagnostic] = []
    positive_rhos: list[float] = []
    for lag in (1, 2, 3):
        current_values: list[float] = []
        prior_values: list[float] = []
        expected_delta = timedelta(minutes=15 * lag)
        for session_rows in sessions.values():
            for index in range(lag, len(session_rows)):
                current = session_rows[index]
                prior = session_rows[index - lag]
                if current.decision_time - prior.decision_time != expected_delta:
                    continue
                current_values.append(float(getattr(current, outcome_name)))
                prior_values.append(float(getattr(prior, outcome_name)))

        rho: float | None = None
        if len(current_values) >= 2:
            current_array = np.asarray(current_values, dtype=float)
            prior_array = np.asarray(prior_values, dtype=float)
            if current_array.std() > 0.0 and prior_array.std() > 0.0:
                candidate = float(np.corrcoef(current_array, prior_array)[0, 1])
                if math.isfinite(candidate):
                    rho = candidate
                    positive_rhos.append(max(candidate, 0.0))
        lag_diagnostics.append(LagDiagnostic(lag=lag, pairs=len(current_values), rho=rho))

    row_count = len(rows)
    design_effect = max(1.0, 1.0 + 2.0 * sum(positive_rhos))
    return OutcomeDependence(
        outcome_name=outcome_name,
        row_count=row_count,
        lags=tuple(lag_diagnostics),
        design_effect=design_effect,
        effective_sample_size=row_count / design_effect,
    )


def compute_ess_support(rows: Iterable[DependenceRow]) -> EssSupportSummary:
    """Apply the exact Cell 13 lag-1..3 diagnostic to both Test 2 outcomes."""

    validated = _validated_dependence_rows(rows)
    path = _outcome_dependence(validated, outcome_name="path_long")
    gross = _outcome_dependence(validated, outcome_name="gross_move_points_60m")
    governing_design_effect = max(path.design_effect, gross.design_effect)
    negative_count = sum(row.path_long == 0 for row in validated)
    positive_count = len(validated) - negative_count
    return EssSupportSummary(
        row_count=len(validated),
        path_long=path,
        gross_move_points_60m=gross,
        governing_design_effect=governing_design_effect,
        governing_effective_sample_size=len(validated) / governing_design_effect,
        raw_negative_count=negative_count,
        raw_positive_count=positive_count,
        effective_negative_support=negative_count / governing_design_effect,
        effective_positive_support=positive_count / governing_design_effect,
    )


def evaluate_support_floors(
    fold_summaries: Mapping[str, EssSupportSummary],
    pooled_summary: EssSupportSummary,
) -> SupportGateResult:
    if set(fold_summaries) != set(FOLD_ORDER) or len(fold_summaries) != len(FOLD_ORDER):
        raise Test2StatsContractError(f"fold summaries must contain exactly {FOLD_ORDER}")
    failures: list[str] = []
    for fold_id in FOLD_ORDER:
        summary = fold_summaries[fold_id]
        if summary.governing_effective_sample_size < PER_FOLD_ESS_FLOOR:
            failures.append(f"{fold_id}: governing ESS below {PER_FOLD_ESS_FLOOR:g}")
        if summary.effective_negative_support < PER_CLASS_EFFECTIVE_SUPPORT_FLOOR:
            failures.append(f"{fold_id}: effective class-0 support below 200")
        if summary.effective_positive_support < PER_CLASS_EFFECTIVE_SUPPORT_FLOOR:
            failures.append(f"{fold_id}: effective class-1 support below 200")
    if pooled_summary.governing_effective_sample_size < POOLED_ESS_FLOOR:
        failures.append(f"OOF_POOLED: governing ESS below {POOLED_ESS_FLOOR:g}")
    return SupportGateResult(passed=not failures, failures=tuple(failures))


def stepwise_average_precision(labels: Sequence[int], probabilities: Sequence[float]) -> float:
    """Return tie-grouped binary average precision using the stepwise PR integral."""

    if len(labels) != len(probabilities) or len(labels) == 0:
        raise Test2StatsContractError("labels and probabilities must have equal non-zero length")
    checked_labels: list[int] = []
    checked_probabilities: list[float] = []
    for label in labels:
        if isinstance(label, bool) or not isinstance(label, Integral):
            raise Test2StatsContractError("labels must contain only integer 0 or 1")
        if int(label) not in (0, 1):
            raise Test2StatsContractError("labels must contain only integer 0 or 1")
        checked_labels.append(int(label))
    for probability in probabilities:
        numeric = _finite_number(probability, field="probability")
        if not 0.0 <= numeric <= 1.0:
            raise Test2StatsContractError("probabilities must lie within [0, 1]")
        checked_probabilities.append(numeric)

    positives = sum(checked_labels)
    if positives == 0:
        return 0.0
    scores = np.asarray(checked_probabilities, dtype=float)
    targets = np.asarray(checked_labels, dtype=np.int8)
    order = np.argsort(-scores, kind="stable")
    scores = scores[order]
    targets = targets[order]
    group_ends = np.r_[np.flatnonzero(np.diff(scores)), len(scores) - 1]
    true_positives = np.cumsum(targets)[group_ends].astype(float)
    observations = group_ends.astype(float) + 1.0
    precision = true_positives / observations
    recall = true_positives / positives
    recall_increment = np.diff(np.r_[0.0, recall])
    return float(np.sum(recall_increment * precision))


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
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
            raise Test2StatsContractError(f"{field} must be a positive integer")
    if block_length > n_sessions:
        raise Test2StatsContractError("block_length may not exceed n_sessions")

    blocks_needed = math.ceil(n_sessions / block_length)
    max_start = n_sessions - block_length
    draws = np.empty((repetitions, n_sessions), dtype=np.int32)
    for repetition in range(repetitions):
        starts = rng.integers(0, max_start + 1, size=blocks_needed)
        indices = np.concatenate(
            [
                np.arange(start, start + block_length, dtype=np.int32)
                for start in starts
            ]
        )[:n_sessions]
        draws[repetition] = indices
    return draws


def _validated_session_tables(
    fold_session_tables: Mapping[str, Iterable[SessionLossAggregate]],
    *,
    block_length: int,
) -> dict[str, tuple[SessionLossAggregate, ...]]:
    if set(fold_session_tables) != set(FOLD_ORDER) or len(fold_session_tables) != len(FOLD_ORDER):
        raise Test2StatsContractError(f"session tables must contain exactly {FOLD_ORDER}")
    validated: dict[str, tuple[SessionLossAggregate, ...]] = {}
    for fold_id in FOLD_ORDER:
        rows = tuple(fold_session_tables[fold_id])
        if len(rows) < block_length:
            raise Test2StatsContractError(
                f"{fold_id} has fewer sessions than block_length={block_length}"
            )
        seen_sessions: set[str] = set()
        for row in rows:
            if not isinstance(row, SessionLossAggregate):
                raise Test2StatsContractError("each session row must be a SessionLossAggregate")
            if row.fold_id != fold_id:
                raise Test2StatsContractError("session row fold_id does not match its table")
            if not isinstance(row.session_id, str) or not row.session_id:
                raise Test2StatsContractError("session_id must be a non-empty string")
            if row.session_id in seen_sessions:
                raise Test2StatsContractError("session_id must be unique within each fold")
            seen_sessions.add(row.session_id)
            if isinstance(row.row_count, bool) or not isinstance(row.row_count, Integral):
                raise Test2StatsContractError("row_count must be an integer")
            if row.row_count <= 0:
                raise Test2StatsContractError("row_count must be positive")
            for field in ("prior_loss_sum", "nuisance_loss_sum", "full_loss_sum"):
                value = _finite_number(getattr(row, field), field=field)
                if value < 0.0:
                    raise Test2StatsContractError(f"{field} must be non-negative")
        validated[fold_id] = rows
    return validated


def paired_session_block_bootstrap(
    fold_session_tables: Mapping[str, Iterable[SessionLossAggregate]],
    *,
    block_length: int = PRIMARY_BLOCK_LENGTH,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    master_seed: int = MASTER_SEED,
) -> PairedBootstrapResult:
    if block_length not in REQUIRED_BLOCK_LENGTHS:
        raise Test2StatsContractError(f"block_length must be one of {REQUIRED_BLOCK_LENGTHS}")
    if repetitions != BOOTSTRAP_REPETITIONS:
        raise Test2StatsContractError("bootstrap repetitions are frozen at 2000")
    if master_seed != MASTER_SEED:
        raise Test2StatsContractError("bootstrap master seed is frozen at 20260809")
    tables = _validated_session_tables(fold_session_tables, block_length=block_length)

    pooled_seed = master_seed + 90_000 + block_length
    fold_seeds: list[tuple[str, int]] = []
    sampled_rows_parts: list[np.ndarray] = []
    sampled_prior_parts: list[np.ndarray] = []
    sampled_nuisance_parts: list[np.ndarray] = []
    sampled_full_parts: list[np.ndarray] = []
    for fold_index, fold_id in enumerate(FOLD_ORDER):
        fold_seed = pooled_seed + 1_000 * (fold_index + 1)
        fold_seeds.append((fold_id, fold_seed))
        rng = np.random.default_rng(fold_seed)
        rows = tables[fold_id]
        draws = moving_block_indices(len(rows), block_length, repetitions, rng)
        row_counts = np.asarray([row.row_count for row in rows], dtype=float)
        prior = np.asarray([row.prior_loss_sum for row in rows], dtype=float)
        nuisance = np.asarray([row.nuisance_loss_sum for row in rows], dtype=float)
        full = np.asarray([row.full_loss_sum for row in rows], dtype=float)
        sampled_rows_parts.append(row_counts[draws].sum(axis=1))
        sampled_prior_parts.append(prior[draws].sum(axis=1))
        sampled_nuisance_parts.append(nuisance[draws].sum(axis=1))
        sampled_full_parts.append(full[draws].sum(axis=1))

    sampled_rows = np.sum(sampled_rows_parts, axis=0)
    sampled_prior = np.sum(sampled_prior_parts, axis=0)
    sampled_nuisance = np.sum(sampled_nuisance_parts, axis=0)
    sampled_full = np.sum(sampled_full_parts, axis=0)
    improvement_vs_prior = (sampled_prior - sampled_full) / sampled_rows
    improvement_vs_nuisance = (sampled_nuisance - sampled_full) / sampled_rows
    lower_prior = float(np.quantile(improvement_vs_prior, 0.05))
    lower_nuisance = float(np.quantile(improvement_vs_nuisance, 0.05))
    return PairedBootstrapResult(
        block_length=block_length,
        repetitions=repetitions,
        pooled_seed=pooled_seed,
        fold_seeds=tuple(fold_seeds),
        improvement_vs_prior=tuple(float(value) for value in improvement_vs_prior),
        improvement_vs_nuisance=tuple(float(value) for value in improvement_vs_nuisance),
        lower_bound_vs_prior=lower_prior,
        lower_bound_vs_nuisance=lower_nuisance,
    )


def required_paired_bootstraps(
    fold_session_tables: Mapping[str, Iterable[SessionLossAggregate]],
) -> tuple[PairedBootstrapResult, ...]:
    materialized = {fold_id: tuple(rows) for fold_id, rows in fold_session_tables.items()}
    return tuple(
        paired_session_block_bootstrap(materialized, block_length=block_length)
        for block_length in REQUIRED_BLOCK_LENGTHS
    )

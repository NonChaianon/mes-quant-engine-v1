from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np

from mes_quant.core.hashing import canonical_json_bytes, sha256_bytes
from mes_quant.exploration.test2_path_contract import (
    CAPACITY_POLICY_ID,
    RELEASE_POLICY_ID,
    VOLATILITY_DECILE_POLICY_ID,
)
from mes_quant.exploration.test2_run_context import CoverageEvidence
from mes_quant.exploration.test2_stats import FOLD_ORDER
from mes_quant.exploration.test2_target import Disposition, PathTargetRow

MISSING_DECILE = "MISSING_DECILE"
DECILE_BUCKETS = tuple(str(index) for index in range(10)) + (MISSING_DECILE,)
DIAGNOSTIC_THRESHOLD = 0.5
MES_MULTIPLIER_USD_PER_POINT = 5.0
ROUND_TRIP_COST_USD = 4.97


class Test2DiagnosticContractError(ValueError):
    """Raised when a predeclared diagnostic rule would become adaptive or inconsistent."""


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Test2DiagnosticContractError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class VolatilityDecileGrid:
    fold_id: str
    training_row_count: int
    cut_points: tuple[float, ...]
    grid_sha256: str
    decile_edge_ties: tuple[tuple[int, int], ...]
    empty_decile_buckets: tuple[int, ...]
    degenerate_decile_grid: bool

    def __post_init__(self) -> None:
        if self.fold_id not in FOLD_ORDER:
            raise Test2DiagnosticContractError(f"fold_id must be one of {FOLD_ORDER}")
        if (
            isinstance(self.training_row_count, bool)
            or not isinstance(self.training_row_count, int)
            or self.training_row_count <= 0
        ):
            raise Test2DiagnosticContractError("training_row_count must be positive")
        if len(self.cut_points) != 9 or not np.isfinite(self.cut_points).all():
            raise Test2DiagnosticContractError("decile grid must contain nine finite cut points")
        if any(left > right for left, right in zip(self.cut_points, self.cut_points[1:])):
            raise Test2DiagnosticContractError("decile cut points must be nondecreasing")
        if len(self.grid_sha256) != 64:
            raise Test2DiagnosticContractError("decile grid SHA-256 is malformed")

    def bucket(self, value: float | None) -> str:
        if value is None:
            return MISSING_DECILE
        numeric = float(value)
        if not math.isfinite(numeric):
            return MISSING_DECILE
        return str(int(np.searchsorted(self.cut_points, numeric, side="right")))

    def as_record(self) -> dict[str, object]:
        return {
            "policy_id": VOLATILITY_DECILE_POLICY_ID,
            "fold_id": self.fold_id,
            "training_row_count": self.training_row_count,
            "cut_points": self.cut_points,
            "quantile_method": "linear",
            "assignment_rule": "SEARCHSORTED_RIGHT",
            "grid_sha256": self.grid_sha256,
            "decile_edge_ties": self.decile_edge_ties,
            "empty_decile_buckets": self.empty_decile_buckets,
            "degenerate_decile_grid": self.degenerate_decile_grid,
        }


def fit_volatility_decile_grid(
    fold_id: str,
    pretarget_training_values: Sequence[float],
) -> VolatilityDecileGrid:
    """Fit a target-blind fold-TRAIN grid before any target construction."""

    if fold_id not in FOLD_ORDER:
        raise Test2DiagnosticContractError(f"fold_id must be one of {FOLD_ORDER}")
    values = np.asarray(pretarget_training_values, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise Test2DiagnosticContractError(
            "pretarget training volatility values must be non-empty and finite"
        )
    cut_points = tuple(
        float(value)
        for value in np.quantile(
            values,
            np.arange(1, 10, dtype=np.float64) / 10.0,
            method="linear",
        )
    )
    tie_runs: list[tuple[int, int]] = []
    empty: set[int] = set()
    start = 0
    while start < len(cut_points):
        end = start + 1
        while end < len(cut_points) and cut_points[end] == cut_points[start]:
            end += 1
        multiplicity = end - start
        if multiplicity > 1:
            tie_runs.append((start + 1, multiplicity))
            empty.update(range(start + 1, end))
        start = end
    grid_sha256 = sha256_bytes(
        canonical_json_bytes([fold_id, int(values.size), list(cut_points)])
    )
    return VolatilityDecileGrid(
        fold_id=fold_id,
        training_row_count=int(values.size),
        cut_points=cut_points,
        grid_sha256=grid_sha256,
        decile_edge_ties=tuple(tie_runs),
        empty_decile_buckets=tuple(sorted(empty)),
        degenerate_decile_grid=cut_points[0] == cut_points[-1],
    )


@dataclass(frozen=True)
class CoverageObservation:
    fold_id: str
    decision_identity: str
    realized_vol_60m: float | None
    target_row: PathTargetRow
    feature_valid: bool = True

    def __post_init__(self) -> None:
        if self.fold_id not in FOLD_ORDER:
            raise Test2DiagnosticContractError(f"fold_id must be one of {FOLD_ORDER}")
        if not isinstance(self.decision_identity, str) or not self.decision_identity:
            raise Test2DiagnosticContractError("decision_identity must be non-empty")
        if self.target_row.decision_identity != self.decision_identity:
            raise Test2DiagnosticContractError("coverage target-row identity mismatch")
        if not isinstance(self.feature_valid, bool):
            raise Test2DiagnosticContractError("feature_valid must be boolean")


def _coverage_disposition(observation: CoverageObservation) -> Disposition:
    return (
        observation.target_row.disposition
        if observation.feature_valid
        else Disposition.NO_SCORE
    )


def _coverage_record(observations: Sequence[CoverageObservation]) -> dict[str, object]:
    dispositions = Counter(_coverage_disposition(observation) for observation in observations)
    no_score_reasons = Counter(
        (
            observation.target_row.no_score_reason.value
            if observation.feature_valid and observation.target_row.no_score_reason is not None
            else "INVALID_FEATURE_VECTOR"
        )
        for observation in observations
        if _coverage_disposition(observation) is Disposition.NO_SCORE
    )
    total = len(observations)
    retained = sum(
        observation.feature_valid and observation.target_row.retained
        for observation in observations
    )
    ambiguous = dispositions[Disposition.AMBIGUOUS_SAME_BAR]
    no_score = dispositions[Disposition.NO_SCORE]
    return {
        "total_rows": total,
        "retained_rows": retained,
        "favorable_first_rows": dispositions[Disposition.FAVORABLE_FIRST],
        "adverse_first_rows": dispositions[Disposition.ADVERSE_FIRST],
        "neither_touch_rows": dispositions[Disposition.NEITHER_TOUCH],
        "ambiguous_same_bar_rows": ambiguous,
        "no_score_rows": no_score,
        "no_score_by_reason": dict(sorted(no_score_reasons.items())),
        "retained_rate": 0.0 if total == 0 else retained / total,
        "ambiguous_rate": 0.0 if total == 0 else ambiguous / total,
        "no_score_rate": 0.0 if total == 0 else no_score / total,
    }


def build_coverage_evidence(
    observations: Iterable[CoverageObservation],
    grids: Mapping[str, VolatilityDecileGrid],
) -> CoverageEvidence:
    materialized = tuple(observations)
    if set(grids) != set(FOLD_ORDER):
        raise Test2DiagnosticContractError(f"grids must contain exactly {FOLD_ORDER}")
    if len({observation.decision_identity for observation in materialized}) != len(
        materialized
    ):
        raise Test2DiagnosticContractError("coverage decision identities must be unique")

    grouped: dict[tuple[str, str], list[CoverageObservation]] = defaultdict(list)
    for observation in materialized:
        grouped[
            (
                observation.fold_id,
                grids[observation.fold_id].bucket(observation.realized_vol_60m),
            )
        ].append(observation)

    by_fold: dict[str, object] = {}
    for fold_id in FOLD_ORDER:
        strata = {
            bucket: _coverage_record(grouped.get((fold_id, bucket), ()))
            for bucket in DECILE_BUCKETS
        }
        fold_total = sum(int(record["total_rows"]) for record in strata.values())
        expected_total = sum(
            observation.fold_id == fold_id for observation in materialized
        )
        if fold_total != expected_total:
            raise Test2DiagnosticContractError("fold decile coverage does not reconcile")
        by_fold[fold_id] = {
            "grid": grids[fold_id].as_record(),
            "strata": strata,
            "total_rows": fold_total,
        }

    pooled_strata = {
        bucket: _coverage_record(
            tuple(
                observation
                for fold_id in FOLD_ORDER
                for observation in grouped.get((fold_id, bucket), ())
            )
        )
        for bucket in DECILE_BUCKETS
    }
    if sum(int(record["total_rows"]) for record in pooled_strata.values()) != len(
        materialized
    ):
        raise Test2DiagnosticContractError("pooled decile coverage does not reconcile")
    ambiguous = sum(
        _coverage_disposition(observation) is Disposition.AMBIGUOUS_SAME_BAR
        for observation in materialized
    )
    missing = sum(
        _coverage_disposition(observation) is Disposition.NO_SCORE
        for observation in materialized
    )
    return CoverageEvidence(
        total_rows=len(materialized),
        ambiguity_rows=ambiguous,
        missing_rows=missing,
        excluded_rows=ambiguous + missing,
        scope="ALL_OOF_ROWS_PRETARGET_FOLD_TRAIN_DECILES",
        by_fold_decile={
            "policy_id": VOLATILITY_DECILE_POLICY_ID,
            "folds": by_fold,
            "pooled_strata_using_row_fold_grid": pooled_strata,
        },
    )


@dataclass(frozen=True)
class EconomicSignal:
    fold_id: str
    decision_identity: str
    session_id: str
    decision_time: datetime
    probability_long: float
    target_row: PathTargetRow

    def __post_init__(self) -> None:
        if self.fold_id not in FOLD_ORDER:
            raise Test2DiagnosticContractError(f"fold_id must be one of {FOLD_ORDER}")
        if not isinstance(self.decision_identity, str) or not self.decision_identity:
            raise Test2DiagnosticContractError("decision_identity must be non-empty")
        if not isinstance(self.session_id, str) or not self.session_id:
            raise Test2DiagnosticContractError("session_id must be non-empty")
        _utc(self.decision_time, field="decision_time")
        if not math.isfinite(float(self.probability_long)):
            raise Test2DiagnosticContractError("probability_long must be finite")
        if not 0.0 <= float(self.probability_long) <= 1.0:
            raise Test2DiagnosticContractError("probability_long must lie within [0,1]")
        if self.target_row.decision_identity != self.decision_identity:
            raise Test2DiagnosticContractError("economic target-row identity mismatch")


def _trade_net_usd(row: PathTargetRow) -> float:
    if row.disposition is Disposition.FAVORABLE_FIRST:
        gross_points = 4.0
    elif row.disposition is Disposition.ADVERSE_FIRST:
        gross_points = -2.0
    elif row.disposition is Disposition.NEITHER_TOUCH:
        if row.gross_move_points_60m is None:
            raise Test2DiagnosticContractError("neither-touch row is missing gross move")
        gross_points = float(row.gross_move_points_60m)
    else:
        raise Test2DiagnosticContractError("forced-FLAT row cannot be executed")
    return gross_points * MES_MULTIPLIER_USD_PER_POINT - ROUND_TRIP_COST_USD


def _policy_counterfactual(
    signals: Sequence[EconomicSignal],
    *,
    release_at_first_touch: bool,
) -> dict[str, object]:
    by_fold: dict[str, list[EconomicSignal]] = defaultdict(list)
    for signal in signals:
        by_fold[signal.fold_id].append(signal)

    executed: list[dict[str, object]] = []
    capacity_rejected = 0
    candidate_signals = 0
    for fold_id in FOLD_ORDER:
        active_until: datetime | None = None
        ordered = sorted(
            by_fold[fold_id],
            key=lambda signal: (
                _utc(signal.decision_time, field="decision_time"),
                signal.decision_identity,
            ),
        )
        for signal in ordered:
            decision_time = _utc(signal.decision_time, field="decision_time")
            row = signal.target_row
            eligible = (
                float(signal.probability_long) >= DIAGNOSTIC_THRESHOLD
                and row.retained
                and row.disposition
                in (
                    Disposition.FAVORABLE_FIRST,
                    Disposition.ADVERSE_FIRST,
                    Disposition.NEITHER_TOUCH,
                )
            )
            if not eligible:
                continue
            candidate_signals += 1
            if active_until is not None and active_until > decision_time:
                capacity_rejected += 1
                continue
            if (
                release_at_first_touch
                and row.first_touch_offset_minutes is not None
            ):
                release_time = decision_time + timedelta(
                    minutes=row.first_touch_offset_minutes + 1
                )
            else:
                release_time = decision_time + timedelta(minutes=60)
            active_until = release_time
            executed.append(
                {
                    "decision_identity": signal.decision_identity,
                    "fold_id": fold_id,
                    "session_id": signal.session_id,
                    "entry_time_utc": decision_time.isoformat().replace("+00:00", "Z"),
                    "release_time_utc": release_time.isoformat().replace("+00:00", "Z"),
                    "net_usd": _trade_net_usd(row),
                }
            )

    return {
        "candidate_long_signals": candidate_signals,
        "executed_trades": len(executed),
        "capacity_rejected_signals": capacity_rejected,
        "net_usd": float(sum(float(trade["net_usd"]) for trade in executed)),
        "round_trip_cost_usd": ROUND_TRIP_COST_USD,
        "diagnostic_probability_threshold": DIAGNOSTIC_THRESHOLD,
        "trades": tuple(executed),
    }


def build_economic_diagnostics(
    signals: Iterable[EconomicSignal],
) -> dict[str, object]:
    materialized = tuple(signals)
    if len({signal.decision_identity for signal in materialized}) != len(materialized):
        raise Test2DiagnosticContractError("economic decision identities must be unique")
    return {
        "primary": {
            "policy_id": RELEASE_POLICY_ID,
            **_policy_counterfactual(materialized, release_at_first_touch=True),
        },
        "capacity_sensitivity": {
            "policy_id": CAPACITY_POLICY_ID,
            **_policy_counterfactual(materialized, release_at_first_touch=False),
        },
        "semantics": (
            "TOUCH_DEFINED_CURRENT_DEPLOYMENT_COUNTERFACTUAL_NOT_HISTORICAL_FILL"
        ),
    }

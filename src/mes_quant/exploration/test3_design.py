from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from numbers import Real

from mes_quant.exploration.test3_contract import (
    MODEL_COLUMNS,
    MODEL_ORDER,
    FailureReason,
    RowStatus,
    TerminalDisposition,
)
from mes_quant.exploration.test3_target import TargetStatusRow


class Test3DesignContractError(ValueError):
    """Raised when predictor, eligibility, or design inputs violate the frozen contract."""

    __test__ = False


@dataclass(frozen=True)
class SyntheticPredictorRequest:
    decision_identity: str
    decision_time: datetime
    realized_vol_60m: float | None
    realized_vol_120m: float | None
    realized_vol_240m: float | None
    outer_partition: str = "TRAIN"


@dataclass(frozen=True)
class PredictorStatusRow:
    decision_identity: str
    decision_time: datetime
    status: str


@dataclass(frozen=True)
class PredictorStatusLedger:
    rows: tuple[PredictorStatusRow, ...]
    status_counts: tuple[tuple[str, int], ...]
    ordered_status_sha256: str
    terminal_disposition: TerminalDisposition | None
    target_or_path_rows_read: int = 0
    synthetic_in_memory_only: bool = True


@dataclass(frozen=True)
class Harmonic:
    slot: int
    n_slots: int
    session_sin: float
    session_cos: float


@dataclass(frozen=True)
class EligibilityResult:
    eligible_identities: tuple[str, ...]
    excluded_identities: tuple[str, ...]
    ordered_identity_sha256: str


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Test3DesignContractError(f"{field} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _identity(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Test3DesignContractError("decision_identity must be a non-empty string")
    return value


def _present_number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise Test3DesignContractError(f"{field} must be numeric when present")
    return float(value)


def _predictor_status(request: SyntheticPredictorRequest) -> str:
    values = (
        request.realized_vol_60m,
        request.realized_vol_120m,
        request.realized_vol_240m,
    )
    present = tuple(
        _present_number(value, field=f"realized_vol_{horizon}m")
        for value, horizon in zip(values, (60, 120, 240), strict=True)
        if value is not None
    )
    if any(not math.isfinite(value) for value in present):
        return FailureReason.PREDICTOR_NONFINITE.value
    if any(value <= 0.0 for value in present):
        return FailureReason.PREDICTOR_NONPOSITIVE.value
    if any(value is None for value in values):
        return RowStatus.PREDICTOR_UNUSABLE.value
    return RowStatus.PREDICTOR_USABLE.value


def _hash_predictor_rows(rows: tuple[PredictorStatusRow, ...]) -> str:
    payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}|{row.status}\n" for row in rows
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_synthetic_predictor_ledger(
    requests: Iterable[SyntheticPredictorRequest],
) -> PredictorStatusLedger:
    """Perform the G2-P domain contract on synthetic rows without any target input."""

    rows: list[PredictorStatusRow] = []
    seen: set[str] = set()
    previous_time: datetime | None = None
    for request in requests:
        if not isinstance(request, SyntheticPredictorRequest):
            raise Test3DesignContractError("requests must contain SyntheticPredictorRequest")
        identity = _identity(request.decision_identity)
        if identity in seen:
            raise Test3DesignContractError("decision_identity must be unique")
        decision_time = _utc(request.decision_time, field="decision_time")
        if previous_time is not None and decision_time <= previous_time:
            raise Test3DesignContractError("predictor requests must be strictly time ordered")
        if request.outer_partition != "TRAIN":
            raise Test3DesignContractError("G2-P may inspect only outer TRAIN predictors")
        seen.add(identity)
        previous_time = decision_time
        rows.append(
            PredictorStatusRow(
                decision_identity=identity,
                decision_time=decision_time,
                status=_predictor_status(request),
            )
        )

    frozen_rows = tuple(rows)
    counts = Counter(row.status for row in frozen_rows)
    failure_codes = {
        FailureReason.PREDICTOR_NONFINITE.value,
        FailureReason.PREDICTOR_NONPOSITIVE.value,
    }
    terminal = (
        TerminalDisposition.INVALID
        if any(counts[code] > 0 for code in failure_codes)
        else None
    )
    return PredictorStatusLedger(
        rows=frozen_rows,
        status_counts=tuple(sorted(counts.items())),
        ordered_status_sha256=_hash_predictor_rows(frozen_rows),
        terminal_disposition=terminal,
    )


def transformed_predictors(
    realized_vol_60m: float,
    realized_vol_120m: float,
    realized_vol_240m: float,
) -> tuple[float, float, float]:
    values = tuple(
        _present_number(value, field=f"realized_vol_{horizon}m")
        for value, horizon in zip(
            (realized_vol_60m, realized_vol_120m, realized_vol_240m),
            (60, 120, 240),
            strict=True,
        )
    )
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise Test3DesignContractError("all three volatility predictors must be finite and positive")
    return tuple(2.0 * math.log(value) for value in values)


def intraday_harmonic(
    decision_time: datetime,
    nyse_market_open_utc: datetime,
    nyse_market_close_utc: datetime,
) -> Harmonic:
    decision = _utc(decision_time, field="decision_time")
    market_open = _utc(nyse_market_open_utc, field="nyse_market_open_utc")
    market_close = _utc(nyse_market_close_utc, field="nyse_market_close_utc")
    minutes_since_open = (decision - market_open).total_seconds() / 60.0
    session_minutes = (market_close - market_open).total_seconds() / 60.0
    slot_value = (minutes_since_open - 15.0) / 15.0
    n_slots_value = (session_minutes - 60.0) / 15.0
    if not slot_value.is_integer() or not n_slots_value.is_integer():
        raise Test3DesignContractError("slot and n_slots must be exact integers")
    slot = int(slot_value)
    n_slots = int(n_slots_value)
    if n_slots <= 0 or not 0 <= slot < n_slots:
        raise Test3DesignContractError("harmonic slot lies outside the horizon-safe session")
    angle = 2.0 * math.pi * slot / n_slots
    return Harmonic(
        slot=slot,
        n_slots=n_slots,
        session_sin=math.sin(angle),
        session_cos=math.cos(angle),
    )


def design_values(
    model_id: str,
    *,
    realized_vol_60m: float,
    realized_vol_120m: float,
    realized_vol_240m: float,
    harmonic: Harmonic,
) -> tuple[float, ...]:
    if model_id not in MODEL_ORDER:
        raise Test3DesignContractError(f"model_id must be one of {MODEL_ORDER}")
    if not isinstance(harmonic, Harmonic):
        raise Test3DesignContractError("harmonic must be a Harmonic")
    x60, x120, x240 = transformed_predictors(
        realized_vol_60m,
        realized_vol_120m,
        realized_vol_240m,
    )
    values_by_name = {
        "intercept": 1.0,
        "X60": x60,
        "X120": x120,
        "X240": x240,
        "SESSION_SIN": harmonic.session_sin,
        "SESSION_COS": harmonic.session_cos,
    }
    return tuple(values_by_name[column] for column in MODEL_COLUMNS[model_id])


def common_eligibility(
    target_rows: Iterable[TargetStatusRow],
    predictor_rows: Iterable[PredictorStatusRow],
) -> EligibilityResult:
    targets = tuple(target_rows)
    predictors = tuple(predictor_rows)
    target_map = {(row.decision_identity, row.decision_time): row for row in targets}
    predictor_map = {(row.decision_identity, row.decision_time): row for row in predictors}
    if len(target_map) != len(targets) or len(predictor_map) != len(predictors):
        raise Test3DesignContractError("eligibility keys must be unique")
    if target_map.keys() != predictor_map.keys():
        raise Test3DesignContractError("target and predictor ledgers must have identical keys")

    terminal_codes = {
        FailureReason.TARGET_ZERO_VARIANCE.value,
        FailureReason.PREDICTOR_NONFINITE.value,
        FailureReason.PREDICTOR_NONPOSITIVE.value,
    }
    if any(row.status in terminal_codes for row in (*targets, *predictors)):
        raise Test3DesignContractError("common eligibility is forbidden after a terminal code")

    eligible: list[str] = []
    excluded: list[str] = []
    for target in targets:
        key = (target.decision_identity, target.decision_time)
        predictor = predictor_map[key]
        if (
            target.status == RowStatus.TARGET_USABLE.value
            and predictor.status == RowStatus.PREDICTOR_USABLE.value
        ):
            eligible.append(target.decision_identity)
        elif (
            target.status in {RowStatus.TARGET_USABLE.value, RowStatus.TARGET_UNUSABLE.value}
            and predictor.status
            in {RowStatus.PREDICTOR_USABLE.value, RowStatus.PREDICTOR_UNUSABLE.value}
        ):
            excluded.append(target.decision_identity)
        else:
            raise Test3DesignContractError("unknown row status in common eligibility")

    payload = "".join(f"{identity}\n" for identity in eligible).encode("utf-8")
    return EligibilityResult(
        eligible_identities=tuple(eligible),
        excluded_identities=tuple(excluded),
        ordered_identity_sha256=hashlib.sha256(payload).hexdigest(),
    )

from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from numbers import Integral, Real

from mes_quant.exploration.test3_contract import (
    TARGET_BAR_COUNT,
    TARGET_HORIZON_MINUTES,
    TARGET_INSTRUMENT_ID,
    TARGET_OFFSETS,
    FailureReason,
    RowStatus,
    TerminalDisposition,
)


class Test3TargetContractError(ValueError):
    """Raised when an in-memory target fixture violates the frozen target contract."""

    __test__ = False


@dataclass(frozen=True)
class SyntheticMinuteBar:
    minute_offset: int
    requested_timestamp_utc: datetime
    close: float
    instrument_id: str = TARGET_INSTRUMENT_ID


@dataclass(frozen=True)
class SyntheticTargetRequest:
    decision_identity: str
    decision_time: datetime
    entry_reference_close: float | None
    endpoint_close_60m: float | None
    bars: tuple[SyntheticMinuteBar, ...]
    outer_partition: str = "TRAIN"


@dataclass(frozen=True)
class TargetStatusRow:
    decision_identity: str
    decision_time: datetime
    label_end_time: datetime
    status: str
    rv_fwd_60: float | None
    log_rv_fwd_60: float | None


@dataclass(frozen=True)
class TargetStatusLedger:
    rows: tuple[TargetStatusRow, ...]
    status_counts: tuple[tuple[str, int], ...]
    ordered_status_sha256: str
    terminal_disposition: TerminalDisposition | None
    synthetic_in_memory_only: bool = True


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Test3TargetContractError(f"{field} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _identity(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Test3TargetContractError("decision_identity must be a non-empty string")
    return value


def _finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise Test3TargetContractError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise Test3TargetContractError(f"{field} must be finite")
    return numeric


def _positive(value: object, *, field: str) -> float:
    numeric = _finite(value, field=field)
    if numeric <= 0.0:
        raise Test3TargetContractError(f"{field} must be positive")
    return numeric


def _status_row(
    request: SyntheticTargetRequest,
    *,
    decision_time: datetime,
    status: str,
    rv_fwd_60: float | None = None,
    log_rv_fwd_60: float | None = None,
) -> TargetStatusRow:
    return TargetStatusRow(
        decision_identity=request.decision_identity,
        decision_time=decision_time,
        label_end_time=decision_time + timedelta(minutes=TARGET_HORIZON_MINUTES),
        status=status,
        rv_fwd_60=rv_fwd_60,
        log_rv_fwd_60=log_rv_fwd_60,
    )


def build_synthetic_target_row(request: SyntheticTargetRequest) -> TargetStatusRow:
    """Build one target row from a synthetic in-memory request; performs no I/O."""

    if not isinstance(request, SyntheticTargetRequest):
        raise Test3TargetContractError("request must be a SyntheticTargetRequest")
    _identity(request.decision_identity)
    decision_time = _utc(request.decision_time, field="decision_time")
    if request.outer_partition != "TRAIN":
        raise Test3TargetContractError("only outer TRAIN is eligible at Test 3")

    bars = tuple(request.bars)
    offsets: list[int] = []
    previous_offset = -1
    for bar in bars:
        if not isinstance(bar, SyntheticMinuteBar):
            raise Test3TargetContractError("bars must contain only SyntheticMinuteBar")
        if isinstance(bar.minute_offset, bool) or not isinstance(bar.minute_offset, Integral):
            raise Test3TargetContractError("minute_offset must be an integer")
        offset = int(bar.minute_offset)
        if offset in offsets:
            raise Test3TargetContractError("duplicate minute_offset")
        if offset <= previous_offset:
            raise Test3TargetContractError("minute offsets must be strictly ordered")
        if offset not in TARGET_OFFSETS:
            raise Test3TargetContractError("minute_offset must lie in 0..59")
        timestamp = _utc(bar.requested_timestamp_utc, field="requested_timestamp_utc")
        if timestamp != decision_time + timedelta(minutes=offset):
            raise Test3TargetContractError("requested timestamp does not match decision + offset")
        if bar.instrument_id != TARGET_INSTRUMENT_ID:
            raise Test3TargetContractError("native instrument mismatch")
        _positive(bar.close, field=f"close[{offset}]")
        offsets.append(offset)
        previous_offset = offset

    if request.entry_reference_close is None or request.endpoint_close_60m is None:
        return _status_row(
            request,
            decision_time=decision_time,
            status=RowStatus.TARGET_UNUSABLE.value,
        )
    if len(bars) != TARGET_BAR_COUNT or tuple(offsets) != TARGET_OFFSETS:
        return _status_row(
            request,
            decision_time=decision_time,
            status=RowStatus.TARGET_UNUSABLE.value,
        )

    entry = _positive(request.entry_reference_close, field="entry_reference_close")
    endpoint = _positive(request.endpoint_close_60m, field="endpoint_close_60m")
    closes = tuple(_positive(bar.close, field=f"close[{bar.minute_offset}]") for bar in bars)
    if closes[-1] != endpoint:
        raise Test3TargetContractError("offset-59 close does not exactly match +60m endpoint")

    prior = entry
    realized_variance = 0.0
    for close in closes:
        log_return = math.log(close / prior)
        realized_variance += log_return * log_return
        prior = close
    if not math.isfinite(realized_variance):
        raise Test3TargetContractError("RV_FWD_60 must be finite")
    if realized_variance == 0.0:
        return _status_row(
            request,
            decision_time=decision_time,
            status=FailureReason.TARGET_ZERO_VARIANCE.value,
            rv_fwd_60=0.0,
        )

    log_variance = math.log(realized_variance)
    if not math.isfinite(log_variance):
        raise Test3TargetContractError("log RV_FWD_60 must be finite")
    return _status_row(
        request,
        decision_time=decision_time,
        status=RowStatus.TARGET_USABLE.value,
        rv_fwd_60=realized_variance,
        log_rv_fwd_60=log_variance,
    )


def _hash_rows(rows: tuple[TargetStatusRow, ...]) -> str:
    payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}|"
        f"{row.label_end_time.isoformat()}|{row.status}\n"
        for row in rows
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_synthetic_target_ledger(
    requests: Iterable[SyntheticTargetRequest],
) -> TargetStatusLedger:
    """Seal every synthetic request even after zero variance; other defects fail immediately."""

    rows: list[TargetStatusRow] = []
    seen_identities: set[str] = set()
    previous_time: datetime | None = None
    for request in requests:
        if not isinstance(request, SyntheticTargetRequest):
            raise Test3TargetContractError("requests must contain SyntheticTargetRequest")
        identity = _identity(request.decision_identity)
        if identity in seen_identities:
            raise Test3TargetContractError("decision_identity must be unique")
        decision_time = _utc(request.decision_time, field="decision_time")
        if previous_time is not None and decision_time <= previous_time:
            raise Test3TargetContractError("requests must be strictly time ordered")
        seen_identities.add(identity)
        previous_time = decision_time
        rows.append(build_synthetic_target_row(request))

    frozen_rows = tuple(rows)
    counts = Counter(row.status for row in frozen_rows)
    terminal = (
        TerminalDisposition.INVALID
        if counts[FailureReason.TARGET_ZERO_VARIANCE.value] > 0
        else None
    )
    return TargetStatusLedger(
        rows=frozen_rows,
        status_counts=tuple(sorted(counts.items())),
        ordered_status_sha256=_hash_rows(frozen_rows),
        terminal_disposition=terminal,
    )

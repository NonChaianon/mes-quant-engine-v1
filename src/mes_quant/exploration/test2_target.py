from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from mes_quant.exploration.test2_path_contract import (
    PATH_OFFSETS,
    STOP_TICKS,
    TAKE_PROFIT_TICKS,
    TICK_SIZE_POINTS,
)

TARGET_INSTRUMENT_ID = "MES"


class PathTargetContractError(ValueError):
    """Raised when present path data violates the frozen target contract."""


class Disposition(StrEnum):
    FAVORABLE_FIRST = "FAVORABLE_FIRST"
    ADVERSE_FIRST = "ADVERSE_FIRST"
    NEITHER_TOUCH = "NEITHER_TOUCH"
    AMBIGUOUS_SAME_BAR = "AMBIGUOUS_SAME_BAR"
    NO_SCORE = "NO_SCORE"


class PolicyAction(StrEnum):
    SCORED = "SCORED"
    FLAT = "FLAT"


class NoScoreReason(StrEnum):
    MISSING_PATH_BAR = "MISSING_PATH_BAR"
    MISSING_ENTRY_REFERENCE = "MISSING_ENTRY_REFERENCE"


@dataclass(frozen=True)
class PathBar:
    minute_offset: int
    instrument_id: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float


@dataclass(frozen=True)
class PathTargetRequest:
    decision_identity: str
    entry_reference_close: float | None
    endpoint_close_60m: float | None
    bars: tuple[PathBar, ...]


@dataclass(frozen=True)
class PathTargetRow:
    decision_identity: str
    disposition: Disposition
    retained: bool
    policy_action: PolicyAction
    path_long: int | None
    first_touch_offset_minutes: int | None
    gross_move_points_60m: float | None
    no_score_reason: NoScoreReason | None
    instrument_id: str | None
    entry_reference_ticks: int | None


@dataclass(frozen=True)
class TargetCoverage:
    total_rows: int
    favorable_first: int
    adverse_first: int
    neither_touch: int
    ambiguous_same_bar: int
    no_score: int
    retained_rows: int
    flat_rows: int

    def __post_init__(self) -> None:
        counts = (
            self.total_rows,
            self.favorable_first,
            self.adverse_first,
            self.neither_touch,
            self.ambiguous_same_bar,
            self.no_score,
            self.retained_rows,
            self.flat_rows,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
            raise PathTargetContractError("coverage counts must be non-negative integers")
        disposition_total = (
            self.favorable_first
            + self.adverse_first
            + self.neither_touch
            + self.ambiguous_same_bar
            + self.no_score
        )
        if disposition_total != self.total_rows:
            raise PathTargetContractError("coverage dispositions do not sum to total rows")
        expected_retained = self.favorable_first + self.adverse_first + self.neither_touch
        if self.retained_rows != expected_retained:
            raise PathTargetContractError("retained-row count is inconsistent")
        expected_flat = self.ambiguous_same_bar + self.no_score
        if self.flat_rows != expected_flat:
            raise PathTargetContractError("forced-FLAT count is inconsistent")
        if self.retained_rows + self.flat_rows != self.total_rows:
            raise PathTargetContractError("retained and forced-FLAT rows do not cover all rows")


@dataclass(frozen=True)
class _TickBar:
    minute_offset: int
    instrument_id: str
    open_ticks: int
    high_ticks: int
    low_ticks: int
    close_ticks: int


def price_to_ticks(value: float, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PathTargetContractError(f"{field} must be a numeric price")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise PathTargetContractError(f"{field} must be finite")
    scaled = numeric * 4.0
    if not scaled.is_integer():
        raise PathTargetContractError(f"{field} must lie exactly on the 0.25-point tick grid")
    return int(scaled)


def ticks_to_points(ticks: int) -> float:
    if isinstance(ticks, bool) or not isinstance(ticks, int):
        raise PathTargetContractError("ticks must be an integer")
    return ticks * TICK_SIZE_POINTS


def _validate_decision_identity(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise PathTargetContractError("decision_identity must be a non-empty string")


def _validate_present_bars(bars: tuple[PathBar, ...]) -> tuple[_TickBar, ...]:
    if len(bars) > len(PATH_OFFSETS):
        raise PathTargetContractError("path contains more than 60 bars")

    seen_offsets: set[int] = set()
    tick_bars: list[_TickBar] = []
    expected_instrument: str | None = None
    for bar in bars:
        if not isinstance(bar, PathBar):
            raise PathTargetContractError("each path bar must be a PathBar")
        offset = bar.minute_offset
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise PathTargetContractError("minute_offset must be an integer")
        if offset not in PATH_OFFSETS:
            raise PathTargetContractError("minute_offset must be within 0..59")
        if offset in seen_offsets:
            raise PathTargetContractError("duplicate minute_offset")
        seen_offsets.add(offset)

        if not isinstance(bar.instrument_id, str) or not bar.instrument_id:
            raise PathTargetContractError("instrument_id must be a non-empty string")
        if bar.instrument_id != TARGET_INSTRUMENT_ID:
            raise PathTargetContractError("Test 2 instrument_id must be MES")
        if expected_instrument is None:
            expected_instrument = bar.instrument_id
        elif bar.instrument_id != expected_instrument:
            raise PathTargetContractError("path must contain exactly one instrument")

        open_ticks = price_to_ticks(bar.open_price, field=f"bar[{offset}].open_price")
        high_ticks = price_to_ticks(bar.high_price, field=f"bar[{offset}].high_price")
        low_ticks = price_to_ticks(bar.low_price, field=f"bar[{offset}].low_price")
        close_ticks = price_to_ticks(bar.close_price, field=f"bar[{offset}].close_price")
        if low_ticks > high_ticks:
            raise PathTargetContractError("bar low exceeds bar high")
        if not low_ticks <= open_ticks <= high_ticks:
            raise PathTargetContractError("bar open lies outside low/high")
        if not low_ticks <= close_ticks <= high_ticks:
            raise PathTargetContractError("bar close lies outside low/high")
        tick_bars.append(
            _TickBar(
                minute_offset=offset,
                instrument_id=bar.instrument_id,
                open_ticks=open_ticks,
                high_ticks=high_ticks,
                low_ticks=low_ticks,
                close_ticks=close_ticks,
            )
        )
    return tuple(sorted(tick_bars, key=lambda bar: bar.minute_offset))


def _is_complete(tick_bars: tuple[_TickBar, ...]) -> bool:
    return tuple(bar.minute_offset for bar in tick_bars) == PATH_OFFSETS


def _resolve_tick_bars(
    entry_ticks: int,
    tick_bars: tuple[_TickBar, ...],
) -> tuple[Disposition, int | None]:
    favorable_barrier = entry_ticks + TAKE_PROFIT_TICKS
    adverse_barrier = entry_ticks - STOP_TICKS
    for bar in tick_bars:
        favorable_touch = bar.high_ticks >= favorable_barrier
        adverse_touch = bar.low_ticks <= adverse_barrier
        if favorable_touch and adverse_touch:
            return Disposition.AMBIGUOUS_SAME_BAR, bar.minute_offset
        if favorable_touch:
            return Disposition.FAVORABLE_FIRST, bar.minute_offset
        if adverse_touch:
            return Disposition.ADVERSE_FIRST, bar.minute_offset
    return Disposition.NEITHER_TOUCH, None


def resolve_first_touch(
    entry_ticks: int,
    bars: tuple[PathBar, ...],
) -> tuple[Disposition, int | None]:
    if isinstance(entry_ticks, bool) or not isinstance(entry_ticks, int):
        raise PathTargetContractError("entry_ticks must be an integer")
    tick_bars = _validate_present_bars(bars)
    if not _is_complete(tick_bars):
        raise PathTargetContractError("resolve_first_touch requires exactly offsets 0..59")
    return _resolve_tick_bars(entry_ticks, tick_bars)


def _no_score_row(
    decision_identity: str,
    reason: NoScoreReason,
) -> PathTargetRow:
    return PathTargetRow(
        decision_identity=decision_identity,
        disposition=Disposition.NO_SCORE,
        retained=False,
        policy_action=PolicyAction.FLAT,
        path_long=None,
        first_touch_offset_minutes=None,
        gross_move_points_60m=None,
        no_score_reason=reason,
        instrument_id=None,
        entry_reference_ticks=None,
    )


def build_path_target_row(request: PathTargetRequest) -> PathTargetRow:
    _validate_decision_identity(request.decision_identity)
    tick_bars = _validate_present_bars(tuple(request.bars))
    entry_ticks = (
        None
        if request.entry_reference_close is None
        else price_to_ticks(request.entry_reference_close, field="entry_reference_close")
    )
    endpoint_ticks = (
        None
        if request.endpoint_close_60m is None
        else price_to_ticks(request.endpoint_close_60m, field="endpoint_close_60m")
    )

    if not _is_complete(tick_bars):
        return _no_score_row(request.decision_identity, NoScoreReason.MISSING_PATH_BAR)
    if endpoint_ticks is None:
        raise PathTargetContractError("complete path requires endpoint_close_60m")
    close_59_ticks = tick_bars[-1].close_ticks
    if close_59_ticks != endpoint_ticks:
        raise PathTargetContractError("offset-59 close does not match the +60m endpoint")
    if entry_ticks is None:
        return _no_score_row(
            request.decision_identity,
            NoScoreReason.MISSING_ENTRY_REFERENCE,
        )

    disposition, first_touch_offset = _resolve_tick_bars(entry_ticks, tick_bars)
    gross_move = ticks_to_points(close_59_ticks - entry_ticks)
    if disposition is Disposition.FAVORABLE_FIRST:
        path_long = 1
        retained = True
        policy_action = PolicyAction.SCORED
    elif disposition in (Disposition.ADVERSE_FIRST, Disposition.NEITHER_TOUCH):
        path_long = 0
        retained = True
        policy_action = PolicyAction.SCORED
    else:
        path_long = None
        retained = False
        policy_action = PolicyAction.FLAT
    return PathTargetRow(
        decision_identity=request.decision_identity,
        disposition=disposition,
        retained=retained,
        policy_action=policy_action,
        path_long=path_long,
        first_touch_offset_minutes=first_touch_offset,
        gross_move_points_60m=gross_move,
        no_score_reason=None,
        instrument_id=tick_bars[0].instrument_id,
        entry_reference_ticks=entry_ticks,
    )


def build_path_target_rows(
    requests: Iterable[PathTargetRequest],
) -> tuple[tuple[PathTargetRow, ...], TargetCoverage]:
    rows: list[PathTargetRow] = []
    seen_identities: set[str] = set()
    for request in requests:
        _validate_decision_identity(request.decision_identity)
        if request.decision_identity in seen_identities:
            raise PathTargetContractError("decision_identity must be unique")
        seen_identities.add(request.decision_identity)
        rows.append(build_path_target_row(request))

    frozen_rows = tuple(rows)
    counts = Counter(row.disposition for row in frozen_rows)
    coverage = TargetCoverage(
        total_rows=len(frozen_rows),
        favorable_first=counts[Disposition.FAVORABLE_FIRST],
        adverse_first=counts[Disposition.ADVERSE_FIRST],
        neither_touch=counts[Disposition.NEITHER_TOUCH],
        ambiguous_same_bar=counts[Disposition.AMBIGUOUS_SAME_BAR],
        no_score=counts[Disposition.NO_SCORE],
        retained_rows=sum(row.retained for row in frozen_rows),
        flat_rows=sum(row.policy_action is PolicyAction.FLAT for row in frozen_rows),
    )
    return frozen_rows, coverage


def l0_safety_counters() -> Mapping[str, int]:
    return {
        "real_train_target_path_rows_read": 0,
        "validation_path_rows_read": 0,
        "final_test_path_rows_read": 0,
        "models_fitted": 0,
        "existing_files_changed": 0,
    }

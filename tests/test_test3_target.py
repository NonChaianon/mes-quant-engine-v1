from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from mes_quant.exploration.test3_contract import FailureReason, RowStatus, TerminalDisposition
from mes_quant.exploration.test3_target import (
    SyntheticMinuteBar,
    SyntheticTargetRequest,
    Test3TargetContractError,
    build_synthetic_target_ledger,
    build_synthetic_target_row,
)


def _bars(decision_time: datetime, closes: tuple[float, ...]) -> tuple[SyntheticMinuteBar, ...]:
    return tuple(
        SyntheticMinuteBar(
            minute_offset=offset,
            requested_timestamp_utc=decision_time + timedelta(minutes=offset),
            close=close,
        )
        for offset, close in enumerate(closes)
    )


def _request(
    identity: str,
    decision_time: datetime,
    closes: tuple[float, ...],
    *,
    entry: float | None = 100.0,
    endpoint: float | None = None,
) -> SyntheticTargetRequest:
    return SyntheticTargetRequest(
        decision_identity=identity,
        decision_time=decision_time,
        entry_reference_close=entry,
        endpoint_close_60m=closes[-1] if endpoint is None and closes else endpoint,
        bars=_bars(decision_time, closes),
    )


def test_exact_sixty_post_decision_returns_build_positive_target() -> None:
    decision = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    closes = tuple(100.0 * math.exp(0.001 * (offset + 1)) for offset in range(60))
    row = build_synthetic_target_row(_request("d1", decision, closes))
    assert row.status == RowStatus.TARGET_USABLE.value
    assert row.label_end_time == decision + timedelta(minutes=60)
    assert row.rv_fwd_60 == pytest.approx(60 * 0.001**2)
    assert row.log_rv_fwd_60 == pytest.approx(math.log(60 * 0.001**2))


def test_missing_path_or_reference_is_nonterminal_unusable() -> None:
    decision = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    closes = tuple(100.0 + offset for offset in range(59))
    missing_path = build_synthetic_target_row(_request("d1", decision, closes, endpoint=159.0))
    assert missing_path.status == RowStatus.TARGET_UNUSABLE.value

    complete = tuple(100.0 + offset for offset in range(60))
    missing_reference = build_synthetic_target_row(
        _request("d2", decision, complete, entry=None)
    )
    assert missing_reference.status == RowStatus.TARGET_UNUSABLE.value


def test_zero_variance_completes_full_ledger_before_invalid_disposition() -> None:
    first_time = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    flat = (100.0,) * 60
    moving = tuple(100.0 * math.exp(0.001 * (offset + 1)) for offset in range(60))
    ledger = build_synthetic_target_ledger(
        (
            _request("zero", first_time, flat),
            _request("usable", first_time + timedelta(days=1), moving),
        )
    )
    assert len(ledger.rows) == 2
    assert ledger.rows[0].status == FailureReason.TARGET_ZERO_VARIANCE.value
    assert ledger.rows[1].status == RowStatus.TARGET_USABLE.value
    assert ledger.terminal_disposition is TerminalDisposition.INVALID
    assert len(ledger.ordered_status_sha256) == 64


def test_duplicate_unordered_timestamp_endpoint_and_partition_fail_closed() -> None:
    decision = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    closes = tuple(100.0 + offset for offset in range(60))
    request = _request("d1", decision, closes)

    duplicate = request.bars[:2] + (request.bars[1],) + request.bars[2:]
    with pytest.raises(Test3TargetContractError, match="duplicate"):
        build_synthetic_target_row(
            SyntheticTargetRequest("d1", decision, 100.0, closes[-1], duplicate)
        )

    wrong_time = list(request.bars)
    wrong_time[0] = SyntheticMinuteBar(0, decision + timedelta(minutes=1), closes[0])
    with pytest.raises(Test3TargetContractError, match="timestamp"):
        build_synthetic_target_row(
            SyntheticTargetRequest("d1", decision, 100.0, closes[-1], tuple(wrong_time))
        )

    with pytest.raises(Test3TargetContractError, match="endpoint"):
        build_synthetic_target_row(_request("d1", decision, closes, endpoint=999.0))

    with pytest.raises(Test3TargetContractError, match="outer TRAIN"):
        build_synthetic_target_row(
            SyntheticTargetRequest("d1", decision, 100.0, closes[-1], request.bars, "VALIDATION")
        )

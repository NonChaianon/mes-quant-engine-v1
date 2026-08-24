from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from mes_quant.exploration.test3_contract import FailureReason, RowStatus, TerminalDisposition
from mes_quant.exploration.test3_design import (
    PredictorStatusRow,
    SyntheticPredictorRequest,
    Test3DesignContractError,
    build_synthetic_predictor_ledger,
    common_eligibility,
    design_values,
    intraday_harmonic,
    transformed_predictors,
)
from mes_quant.exploration.test3_target import TargetStatusRow


def test_predictor_preflight_is_complete_target_blind_and_deterministic() -> None:
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    ledger = build_synthetic_predictor_ledger(
        (
            SyntheticPredictorRequest("ok", start, 1.0, 2.0, 3.0),
            SyntheticPredictorRequest("missing", start + timedelta(minutes=15), None, 2.0, 3.0),
            SyntheticPredictorRequest("nan", start + timedelta(minutes=30), 1.0, float("nan"), 3.0),
            SyntheticPredictorRequest("zero", start + timedelta(minutes=45), 1.0, 2.0, 0.0),
        )
    )
    assert tuple(row.status for row in ledger.rows) == (
        RowStatus.PREDICTOR_USABLE.value,
        RowStatus.PREDICTOR_UNUSABLE.value,
        FailureReason.PREDICTOR_NONFINITE.value,
        FailureReason.PREDICTOR_NONPOSITIVE.value,
    )
    assert ledger.terminal_disposition is TerminalDisposition.INVALID
    assert ledger.target_or_path_rows_read == 0
    assert not hasattr(ledger.rows[0], "realized_vol_60m")


def test_harmonic_is_early_close_aware_and_horizon_safe() -> None:
    market_open = datetime(2023, 1, 3, 14, 30, tzinfo=UTC)
    normal = intraday_harmonic(
        market_open + timedelta(minutes=15),
        market_open,
        datetime(2023, 1, 3, 21, 0, tzinfo=UTC),
    )
    early = intraday_harmonic(
        market_open + timedelta(minutes=15),
        market_open,
        datetime(2023, 1, 3, 18, 0, tzinfo=UTC),
    )
    assert (normal.slot, normal.n_slots) == (0, 22)
    assert (early.slot, early.n_slots) == (0, 10)
    with pytest.raises(Test3DesignContractError, match="outside"):
        intraday_harmonic(
            datetime(2023, 1, 3, 20, 15, tzinfo=UTC),
            market_open,
            datetime(2023, 1, 3, 21, 0, tzinfo=UTC),
        )


def test_transforms_and_model_column_order_are_frozen() -> None:
    market_open = datetime(2023, 1, 3, 14, 30, tzinfo=UTC)
    harmonic = intraday_harmonic(
        market_open + timedelta(minutes=30),
        market_open,
        datetime(2023, 1, 3, 21, 0, tzinfo=UTC),
    )
    x60, x120, x240 = transformed_predictors(1.0, 2.0, 4.0)
    assert (x60, x120, x240) == pytest.approx(
        (0.0, 2.0 * math.log(2), 2.0 * math.log(4))
    )
    assert design_values(
        "RVBASE001",
        realized_vol_60m=1.0,
        realized_vol_120m=2.0,
        realized_vol_240m=4.0,
        harmonic=harmonic,
    ) == pytest.approx((1.0, x60, harmonic.session_sin, harmonic.session_cos))
    assert len(
        design_values(
            "RVHAR001",
            realized_vol_60m=1.0,
            realized_vol_120m=2.0,
            realized_vol_240m=4.0,
            harmonic=harmonic,
        )
    ) == 6


def test_common_mask_uses_only_exact_usable_statuses() -> None:
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    target_rows = (
        TargetStatusRow("keep", start, start + timedelta(minutes=60), "TARGET_USABLE", 1.0, 0.0),
        TargetStatusRow(
            "drop",
            start + timedelta(minutes=15),
            start + timedelta(minutes=75),
            "TARGET_UNUSABLE",
            None,
            None,
        ),
    )
    predictor_rows = (
        PredictorStatusRow("keep", start, "PREDICTOR_USABLE"),
        PredictorStatusRow("drop", start + timedelta(minutes=15), "PREDICTOR_USABLE"),
    )
    result = common_eligibility(target_rows, predictor_rows)
    assert result.eligible_identities == ("keep",)
    assert result.excluded_identities == ("drop",)

    terminal = (PredictorStatusRow("keep", start, "PREDICTOR_NONPOSITIVE"), predictor_rows[1])
    with pytest.raises(Test3DesignContractError, match="forbidden"):
        common_eligibility(target_rows, terminal)

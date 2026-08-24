from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest

from mes_quant.exploration.test3_contract import TerminalDisposition
from mes_quant.exploration.test3_stats import (
    ContinuationInputs,
    DependenceRow,
    SessionImprovementAggregate,
    Test3StatsContractError,
    back_transform_log_variance,
    decide_continuation,
    dependence_summary,
    duan_smearing_factor,
    overlap_null,
    paired_session_block_bootstrap,
    qlike,
    relative_qlike_reduction,
)


def test_qlike_duan_and_back_transform_are_positive_finite() -> None:
    assert qlike((1.0, 2.0), (1.0, 2.0)) == pytest.approx((0.0, 0.0))
    factor = duan_smearing_factor((0.0, math.log(2.0)))
    assert factor == pytest.approx(1.5)
    assert back_transform_log_variance((0.0, math.log(2.0)), factor) == pytest.approx(
        (1.5, 3.0)
    )
    with pytest.raises(Test3StatsContractError, match="strictly positive"):
        qlike((0.0,), (1.0,))


def test_overlap_null_profile_and_dependence_do_not_cross_sessions() -> None:
    assert tuple(overlap_null(lag) for lag in range(1, 9)) == (
        0.75,
        0.5,
        0.25,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    )
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    rows = tuple(
        DependenceRow("WF_2022", "s1", start + timedelta(minutes=15 * index), float(index + 1))
        for index in range(9)
    ) + tuple(
        DependenceRow(
            "WF_2022",
            "s2",
            start + timedelta(days=1, minutes=15 * index),
            float(20 - index),
        )
        for index in range(9)
    )
    summary = dependence_summary(rows)
    assert summary.row_count == 18
    assert summary.lags[0].pairs == 16
    assert summary.lags[7].pairs == 2
    assert summary.design_effect >= 1.0
    assert summary.status == "DESCRIPTIVE_NOT_A_PASS_GATE"


def test_dependence_rejects_zero_variance_and_unordered_session_rows() -> None:
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    with pytest.raises(Test3StatsContractError, match="strictly positive"):
        dependence_summary((DependenceRow("WF_2022", "s1", start, 0.0),))
    with pytest.raises(Test3StatsContractError, match="chronological"):
        dependence_summary(
            (
                DependenceRow("WF_2022", "s1", start + timedelta(minutes=15), 2.0),
                DependenceRow("WF_2022", "s1", start, 1.0),
            )
        )


def _bootstrap_tables() -> dict[str, tuple[SessionImprovementAggregate, ...]]:
    return {
        fold_id: tuple(
            SessionImprovementAggregate(
                fold_id,
                f"{fold_id}-{index:02d}",
                date(2022 if fold_id == "WF_2022" else 2023, 1, 1)
                + timedelta(days=index),
                10,
                1.0,
            )
            for index in range(20)
        )
        for fold_id in ("WF_2022", "WF_2023")
    }


def test_bootstrap_freezes_seed_pairing_and_fifth_percentile() -> None:
    first = paired_session_block_bootstrap(_bootstrap_tables())
    second = paired_session_block_bootstrap(_bootstrap_tables())
    assert first.repetitions == 2_000
    assert first.block_length == 5
    assert first.pooled_seed == 20260809 + 90_000 + 5
    assert first.fold_seeds == (("WF_2022", first.pooled_seed + 1_000), ("WF_2023", first.pooled_seed + 2_000))
    assert first.draw_identity_sha256 == second.draw_identity_sha256
    assert first.lower_bound == pytest.approx(0.1)
    assert np.asarray(first.replicate_improvements) == pytest.approx(0.1)


def test_bootstrap_rejects_unordered_sessions_and_hashes_session_identity() -> None:
    tables = _bootstrap_tables()
    shuffled = dict(tables)
    shuffled["WF_2022"] = (
        tables["WF_2022"][1],
        tables["WF_2022"][0],
        *tables["WF_2022"][2:],
    )
    with pytest.raises(Test3StatsContractError, match="chronological"):
        paired_session_block_bootstrap(shuffled)

    renamed = dict(tables)
    first_row = tables["WF_2022"][0]
    renamed["WF_2022"] = (
        SessionImprovementAggregate(
            first_row.fold_id,
            "different-session-identity",
            first_row.session_date,
            first_row.row_count,
            first_row.improvement_sum,
        ),
        *tables["WF_2022"][1:],
    )
    assert (
        paired_session_block_bootstrap(tables).draw_identity_sha256
        != paired_session_block_bootstrap(renamed).draw_identity_sha256
    )


def test_gate_equality_rules_and_underpowered_stop_are_exact() -> None:
    passing = decide_continuation(
        ContinuationInputs(
            assertions_passed=True,
            fold_mean_improvements=(("WF_2022", 0.01), ("WF_2023", 0.02)),
            pooled_mean_qlike_base=10.0,
            pooled_mean_qlike_har=9.0,
            primary_lower_bound=0.001,
            real_fold_fit_calls=4,
        )
    )
    assert passing.disposition is TerminalDisposition.INTERESTING
    assert passing.relative_qlike_reduction == pytest.approx(0.10)

    equality_failure = decide_continuation(
        ContinuationInputs(
            assertions_passed=True,
            fold_mean_improvements=(("WF_2022", 0.0), ("WF_2023", 0.02)),
            pooled_mean_qlike_base=10.0,
            pooled_mean_qlike_har=9.0,
            primary_lower_bound=0.0,
            real_fold_fit_calls=4,
        )
    )
    assert equality_failure.disposition is TerminalDisposition.NOT_INTERESTING
    assert set(equality_failure.failures) == {
        "WF_2022_improvement_not_positive",
        "primary_lower_bound_not_positive",
    }

    underpowered = decide_continuation(
        ContinuationInputs(False, (), 0.0, 0.0, 0.0, 0, underpowered=True)
    )
    assert underpowered.disposition is TerminalDisposition.UNDERPOWERED
    with pytest.raises(Test3StatsContractError, match="non-negative"):
        relative_qlike_reduction(1.0, -0.01)

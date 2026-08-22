from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from mes_quant.exploration.test2_stats import (
    BOOTSTRAP_REPETITIONS,
    FOLD_ORDER,
    MASTER_SEED,
    DependenceRow,
    EssSupportSummary,
    OutcomeDependence,
    SessionLossAggregate,
    compute_ess_support,
    evaluate_support_floors,
    moving_block_indices,
    paired_session_block_bootstrap,
    required_paired_bootstraps,
    stepwise_average_precision,
)
from mes_quant.exploration.test2_stats import (
    Test2StatsContractError as StatsContractError,
)


def _dependence_rows(
    path: list[int],
    gross: list[float],
    *,
    fold_id: str = "WF_2022",
    session_id: str = "2022-01-03",
    start: datetime = datetime(2022, 1, 3, 14, 30, tzinfo=UTC),
) -> tuple[DependenceRow, ...]:
    return tuple(
        DependenceRow(
            fold_id=fold_id,
            session_id=session_id,
            decision_time=start + timedelta(minutes=15 * index),
            path_long=path_value,
            gross_move_points_60m=gross_value,
        )
        for index, (path_value, gross_value) in enumerate(zip(path, gross, strict=True))
    )


def _summary(ess: float, negative: float, positive: float) -> EssSupportSummary:
    outcome = OutcomeDependence(
        outcome_name="synthetic",
        row_count=2_000,
        lags=(),
        design_effect=1.0,
        effective_sample_size=ess,
    )
    return EssSupportSummary(
        row_count=2_000,
        path_long=outcome,
        gross_move_points_60m=outcome,
        governing_design_effect=1.0,
        governing_effective_sample_size=ess,
        raw_negative_count=1_000,
        raw_positive_count=1_000,
        effective_negative_support=negative,
        effective_positive_support=positive,
    )


def _session_tables(n_sessions: int = 20) -> dict[str, tuple[SessionLossAggregate, ...]]:
    tables: dict[str, tuple[SessionLossAggregate, ...]] = {}
    for fold_index, fold_id in enumerate(FOLD_ORDER):
        tables[fold_id] = tuple(
            SessionLossAggregate(
                fold_id=fold_id,
                session_id=f"{fold_id}-{index:02d}",
                row_count=1 + ((index + fold_index) % 4),
                prior_loss_sum=2.0 + 0.3 * index + fold_index,
                nuisance_loss_sum=1.5 + 0.2 * index + fold_index,
                full_loss_sum=1.0 + 0.1 * index + fold_index,
            )
            for index in range(n_sessions)
        )
    return tables


def test_cell13_ess_runs_both_outcomes_and_larger_design_effect_governs() -> None:
    rows = _dependence_rows([0, 0, 1, 1], [0.0, 1.0, 0.0, 1.0])
    result = compute_ess_support(rows)

    assert result.path_long.lags[0].pairs == 3
    assert result.path_long.lags[0].rho == pytest.approx(0.5)
    assert result.path_long.design_effect == pytest.approx(2.0)
    assert result.gross_move_points_60m.lags[0].rho == pytest.approx(-1.0)
    assert result.gross_move_points_60m.lags[1].rho == pytest.approx(1.0)
    assert result.gross_move_points_60m.design_effect == pytest.approx(3.0)
    assert result.governing_design_effect == pytest.approx(3.0)
    assert result.governing_effective_sample_size == pytest.approx(4.0 / 3.0)
    assert result.effective_negative_support == pytest.approx(2.0 / 3.0)
    assert result.effective_positive_support == pytest.approx(2.0 / 3.0)
    assert result.status == "DESCRIPTIVE_NOT_FOR_CI"


def test_ess_uses_exact_15_minute_pairs_and_never_crosses_session_or_fold() -> None:
    rows = list(_dependence_rows([0, 1], [0.0, 1.0]))
    rows.append(
        DependenceRow(
            fold_id="WF_2022",
            session_id="2022-01-04",
            decision_time=datetime(2022, 1, 4, 14, 45, tzinfo=UTC),
            path_long=1,
            gross_move_points_60m=2.0,
        )
    )
    rows.append(
        DependenceRow(
            fold_id="WF_2023",
            session_id="2022-01-03",
            decision_time=datetime(2022, 1, 3, 15, 0, tzinfo=UTC),
            path_long=0,
            gross_move_points_60m=3.0,
        )
    )
    result = compute_ess_support(reversed(rows))
    assert result.path_long.lags[0].pairs == 1
    assert result.path_long.lags[1].pairs == 0
    assert result.path_long.lags[2].pairs == 0


def test_pooled_ess_is_recomputed_instead_of_summing_fold_ess() -> None:
    fold_2022 = _dependence_rows([0, 0, 1, 1], [0.0, 0.0, 1.0, 1.0])
    fold_2023 = _dependence_rows(
        [0, 1, 0, 1],
        [0.0, 1.0, 0.0, 1.0],
        fold_id="WF_2023",
        session_id="2023-01-03",
        start=datetime(2023, 1, 3, 14, 30, tzinfo=UTC),
    )
    first = compute_ess_support(fold_2022)
    second = compute_ess_support(fold_2023)
    pooled = compute_ess_support((*fold_2022, *fold_2023))
    assert pooled.row_count == first.row_count + second.row_count
    assert not math.isclose(
        pooled.governing_effective_sample_size,
        first.governing_effective_sample_size + second.governing_effective_sample_size,
    )


def test_support_floor_equality_passes_and_any_below_floor_fails() -> None:
    fold_summaries = {
        "WF_2022": _summary(1_000.0, 200.0, 200.0),
        "WF_2023": _summary(1_000.0, 200.0, 200.0),
    }
    assert evaluate_support_floors(fold_summaries, _summary(2_000.0, 400.0, 400.0)).passed

    underpowered = {
        "WF_2022": _summary(999.999, 200.0, 200.0),
        "WF_2023": _summary(1_000.0, 199.999, 200.0),
    }
    result = evaluate_support_floors(underpowered, _summary(1_999.999, 400.0, 400.0))
    assert not result.passed
    assert len(result.failures) == 3


def test_support_gate_uses_computed_governing_ess_and_effective_support() -> None:
    def repeated_summary(session_count: int, fold_id: str) -> EssSupportSummary:
        rows = tuple(
            row
            for session_index in range(session_count)
            for row in _dependence_rows(
                [0, 0, 1, 1],
                [0.0, 1.0, 0.0, 1.0],
                fold_id=fold_id,
                session_id=f"{fold_id}-{session_index:04d}",
            )
        )
        return compute_ess_support(rows)

    ess_binding = repeated_summary(600, "WF_2022")
    support_binding = repeated_summary(250, "WF_2023")
    assert ess_binding.path_long.effective_sample_size == pytest.approx(1_200.0)
    assert ess_binding.governing_effective_sample_size == pytest.approx(800.0)
    assert support_binding.raw_negative_count == 500
    assert support_binding.raw_positive_count == 500
    assert support_binding.effective_negative_support == pytest.approx(500.0 / 3.0)
    assert support_binding.effective_positive_support == pytest.approx(500.0 / 3.0)

    result = evaluate_support_floors(
        {"WF_2022": ess_binding, "WF_2023": support_binding},
        _summary(2_000.0, 400.0, 400.0),
    )
    assert "WF_2022: governing ESS below 1000" in result.failures
    assert "WF_2023: effective class-0 support below 200" in result.failures
    assert "WF_2023: effective class-1 support below 200" in result.failures


def test_positive_lag_three_correlation_contributes_to_design_effect() -> None:
    values = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    result = compute_ess_support(_dependence_rows(values, [float(value) for value in values]))
    assert result.path_long.lags[2].pairs == 6
    assert result.path_long.lags[2].rho == pytest.approx(1.0)
    assert result.path_long.design_effect == pytest.approx(3.0)


def test_stepwise_average_precision_is_tie_safe_and_not_trapezoidal() -> None:
    labels = [1, 0, 1, 0]
    probabilities = [0.9, 0.8, 0.8, 0.1]
    expected_stepwise = 0.5 + 0.5 * (2.0 / 3.0)
    assert stepwise_average_precision(labels, probabilities) == pytest.approx(expected_stepwise)
    assert stepwise_average_precision([1, 0], [0.5, 0.5]) == pytest.approx(0.5)
    assert stepwise_average_precision([0, 1], [0.5, 0.5]) == pytest.approx(0.5)
    assert stepwise_average_precision([0, 0], [0.9, 0.1]) == 0.0
    assert stepwise_average_precision(np.array([1, 0]), np.array([0.7, 0.2])) == 1.0


class _FixedStarts:
    def integers(self, low: int, high: int, size: int) -> np.ndarray:
        assert (low, high, size) == (0, 3, 2)
        return np.asarray([2, 2])


def test_moving_blocks_are_non_circular_and_truncate_without_dropping_remainder() -> None:
    draws = moving_block_indices(5, 3, 1, _FixedStarts())
    assert draws.tolist() == [[2, 3, 4, 2, 3]]
    with pytest.raises(StatsContractError, match="may not exceed"):
        moving_block_indices(2, 3, 1, np.random.default_rng(1))


def test_bootstrap_freezes_seed_schedule_pairing_and_fifth_percentile() -> None:
    tables: dict[str, tuple[SessionLossAggregate, ...]] = {}
    for fold_id in FOLD_ORDER:
        tables[fold_id] = tuple(
            SessionLossAggregate(
                fold_id=fold_id,
                session_id=f"{fold_id}-{index}",
                row_count=index + 1,
                prior_loss_sum=0.30 * (index + 1),
                nuisance_loss_sum=0.20 * (index + 1),
                full_loss_sum=0.10 * (index + 1),
            )
            for index in range(5)
        )
    result = paired_session_block_bootstrap(tables)
    assert result.repetitions == BOOTSTRAP_REPETITIONS
    assert result.pooled_seed == MASTER_SEED + 90_000 + 5
    assert result.fold_seeds == (
        ("WF_2022", result.pooled_seed + 1_000),
        ("WF_2023", result.pooled_seed + 2_000),
    )
    assert len(result.draw_identity_sha256) == 64
    assert result.improvement_vs_prior == pytest.approx([0.2] * BOOTSTRAP_REPETITIONS)
    assert result.improvement_vs_nuisance == pytest.approx([0.1] * BOOTSTRAP_REPETITIONS)
    assert result.lower_bound_vs_prior == pytest.approx(0.2)
    assert result.lower_bound_vs_nuisance == pytest.approx(0.1)


def test_pooled_bootstrap_is_independent_by_fold_and_row_weighted() -> None:
    tables = _session_tables(20)
    result = paired_session_block_bootstrap(tables, block_length=1)

    sampled_totals = {
        name: np.zeros(BOOTSTRAP_REPETITIONS, dtype=float)
        for name in ("rows", "prior", "nuisance", "full")
    }
    for fold_index, fold_id in enumerate(FOLD_ORDER):
        seed = result.pooled_seed + 1_000 * (fold_index + 1)
        draws = moving_block_indices(20, 1, BOOTSTRAP_REPETITIONS, np.random.default_rng(seed))
        assert not np.array_equal(draws[0], draws[1])
        rows = tables[fold_id]
        sampled_totals["rows"] += np.asarray([row.row_count for row in rows])[draws].sum(
            axis=1
        )
        sampled_totals["prior"] += np.asarray(
            [row.prior_loss_sum for row in rows]
        )[draws].sum(axis=1)
        sampled_totals["nuisance"] += np.asarray(
            [row.nuisance_loss_sum for row in rows]
        )[draws].sum(axis=1)
        sampled_totals["full"] += np.asarray(
            [row.full_loss_sum for row in rows]
        )[draws].sum(axis=1)
    expected_prior = (
        sampled_totals["prior"] - sampled_totals["full"]
    ) / sampled_totals["rows"]
    expected_nuisance = (
        sampled_totals["nuisance"] - sampled_totals["full"]
    ) / sampled_totals["rows"]
    assert np.ptp(expected_prior) > 0.0
    assert np.ptp(expected_nuisance) > 0.0
    assert result.improvement_vs_prior == pytest.approx(expected_prior)
    assert result.improvement_vs_nuisance == pytest.approx(expected_nuisance)
    assert result.lower_bound_vs_prior == pytest.approx(
        np.quantile(expected_prior, 0.05)
    )
    assert result.lower_bound_vs_nuisance == pytest.approx(
        np.quantile(expected_nuisance, 0.05)
    )


def test_required_bootstraps_run_primary_and_both_diagnostics_without_reseeding() -> None:
    results = required_paired_bootstraps(_session_tables(20))
    assert [result.block_length for result in results] == [5, 1, 20]
    assert [result.pooled_seed for result in results] == [
        MASTER_SEED + 90_005,
        MASTER_SEED + 90_001,
        MASTER_SEED + 90_020,
    ]


@pytest.mark.parametrize(
    ("labels", "probabilities"),
    [([1], []), ([True], [0.5]), ([2], [0.5]), ([1], [1.1]), ([1], [float("nan")])],
)
def test_average_precision_rejects_invalid_inputs(labels, probabilities) -> None:
    with pytest.raises(StatsContractError):
        stepwise_average_precision(labels, probabilities)


def test_bootstrap_uses_frozen_fold_order_and_rejects_bad_tables_or_constants() -> None:
    canonical = _session_tables()
    reversed_tables = {"WF_2023": canonical["WF_2023"], "WF_2022": canonical["WF_2022"]}
    reversed_result = paired_session_block_bootstrap(reversed_tables)
    assert reversed_result.fold_seeds[0][0] == "WF_2022"
    with pytest.raises(StatsContractError, match="contain exactly"):
        paired_session_block_bootstrap({"WF_2022": canonical["WF_2022"]})
    with pytest.raises(StatsContractError, match="fewer sessions"):
        paired_session_block_bootstrap(_session_tables(4))
    with pytest.raises(StatsContractError, match="repetitions"):
        paired_session_block_bootstrap(_session_tables(), repetitions=100)
    with pytest.raises(StatsContractError, match="master seed"):
        paired_session_block_bootstrap(_session_tables(), master_seed=1)

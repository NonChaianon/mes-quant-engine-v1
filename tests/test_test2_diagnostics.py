from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

import numpy as np

from mes_quant.exploration.test2_diagnostics import (
    DECILE_BUCKETS,
    MISSING_DECILE,
    CoverageObservation,
    EconomicSignal,
    build_coverage_evidence,
    build_economic_diagnostics,
    fit_volatility_decile_grid,
)
from mes_quant.exploration.test2_diagnostics import (
    Test2DiagnosticContractError as DiagnosticContractError,
)
from mes_quant.exploration.test2_target import (
    Disposition,
    NoScoreReason,
    PathTargetRow,
    PolicyAction,
)


def _target(
    identity: str,
    disposition: Disposition,
    *,
    first_touch: int | None = None,
    gross_move: float | None = None,
) -> PathTargetRow:
    retained = disposition in (
        Disposition.FAVORABLE_FIRST,
        Disposition.ADVERSE_FIRST,
        Disposition.NEITHER_TOUCH,
    )
    return PathTargetRow(
        decision_identity=identity,
        disposition=disposition,
        retained=retained,
        policy_action=PolicyAction.SCORED if retained else PolicyAction.FLAT,
        path_long=(1 if disposition is Disposition.FAVORABLE_FIRST else 0)
        if retained
        else None,
        first_touch_offset_minutes=first_touch,
        gross_move_points_60m=gross_move,
        no_score_reason=(
            NoScoreReason.MISSING_PATH_BAR
            if disposition is Disposition.NO_SCORE
            else None
        ),
        instrument_id="MES" if retained else None,
        entry_reference_ticks=20_000 if retained else None,
    )


class VolatilityDecileTests(unittest.TestCase):
    def test_grid_uses_linear_quantiles_and_searchsorted_right(self) -> None:
        values = np.arange(100, dtype=float)
        grid = fit_volatility_decile_grid("WF_2022", values)
        expected = tuple(np.quantile(values, np.arange(1, 10) / 10, method="linear"))
        self.assertEqual(grid.cut_points, expected)
        self.assertEqual(grid.bucket(expected[0] - 0.01), "0")
        self.assertEqual(grid.bucket(expected[0]), "1")
        self.assertEqual(grid.bucket(float("nan")), MISSING_DECILE)
        self.assertEqual(grid.bucket(None), MISSING_DECILE)

    def test_duplicate_edges_are_retained_and_empty_buckets_are_recorded(self) -> None:
        grid = fit_volatility_decile_grid("WF_2023", np.ones(20))
        self.assertEqual(grid.cut_points, (1.0,) * 9)
        self.assertTrue(grid.degenerate_decile_grid)
        self.assertEqual(grid.empty_decile_buckets, tuple(range(1, 9)))
        self.assertEqual(grid.bucket(1.0), "9")

    def test_grid_rejects_nonfinite_training_values(self) -> None:
        with self.assertRaisesRegex(DiagnosticContractError, "finite"):
            fit_volatility_decile_grid("WF_2022", [1.0, float("nan")])


class CoverageTests(unittest.TestCase):
    def test_all_feature_valid_rows_are_counted_before_target_exclusion(self) -> None:
        grids = {
            "WF_2022": fit_volatility_decile_grid("WF_2022", np.arange(10, dtype=float)),
            "WF_2023": fit_volatility_decile_grid("WF_2023", np.arange(10, dtype=float)),
        }
        observations = (
            CoverageObservation(
                "WF_2022", "A", 0.0, _target("A", Disposition.FAVORABLE_FIRST, first_touch=2)
            ),
            CoverageObservation(
                "WF_2022", "B", None, _target("B", Disposition.AMBIGUOUS_SAME_BAR)
            ),
            CoverageObservation(
                "WF_2023", "C", 9.0, _target("C", Disposition.NO_SCORE)
            ),
            CoverageObservation(
                "WF_2023",
                "D",
                None,
                _target("D", Disposition.FAVORABLE_FIRST, first_touch=2),
                feature_valid=False,
            ),
        )
        evidence = build_coverage_evidence(observations, grids)
        self.assertEqual(evidence.total_rows, 4)
        self.assertEqual(evidence.ambiguity_rows, 1)
        self.assertEqual(evidence.missing_rows, 2)
        self.assertEqual(evidence.excluded_rows, 3)
        folds = evidence.by_fold_decile["folds"]
        self.assertEqual(folds["WF_2022"]["total_rows"], 2)
        self.assertEqual(
            folds["WF_2022"]["strata"][MISSING_DECILE]["ambiguous_same_bar_rows"],
            1,
        )
        pooled = evidence.by_fold_decile["pooled_strata_using_row_fold_grid"]
        self.assertEqual(sum(row["total_rows"] for row in pooled.values()), 4)
        self.assertEqual(
            pooled[MISSING_DECILE]["no_score_by_reason"]["INVALID_FEATURE_VECTOR"],
            1,
        )
        self.assertEqual(tuple(pooled), DECILE_BUCKETS)


class EconomicDiagnosticTests(unittest.TestCase):
    def test_release_at_touch_and_reserve_to_60m_are_both_reported(self) -> None:
        start = datetime(2023, 6, 1, 14, 30, tzinfo=UTC)
        signals = (
            EconomicSignal(
                "WF_2022",
                "A",
                "S1",
                start,
                0.9,
                _target("A", Disposition.FAVORABLE_FIRST, first_touch=5),
            ),
            EconomicSignal(
                "WF_2022",
                "B",
                "S1",
                start + timedelta(minutes=15),
                0.8,
                _target("B", Disposition.ADVERSE_FIRST, first_touch=3),
            ),
            EconomicSignal(
                "WF_2022",
                "C",
                "S1",
                start + timedelta(minutes=30),
                0.7,
                _target("C", Disposition.AMBIGUOUS_SAME_BAR),
            ),
        )
        diagnostics = build_economic_diagnostics(signals)
        primary = diagnostics["primary"]
        sensitivity = diagnostics["capacity_sensitivity"]
        self.assertEqual(primary["executed_trades"], 2)
        self.assertEqual(primary["capacity_rejected_signals"], 0)
        self.assertEqual(sensitivity["executed_trades"], 1)
        self.assertEqual(sensitivity["capacity_rejected_signals"], 1)
        self.assertAlmostEqual(primary["net_usd"], 0.06)
        self.assertAlmostEqual(sensitivity["net_usd"], 15.03)

    def test_ambiguous_and_no_score_rows_are_never_executed(self) -> None:
        now = datetime(2023, 6, 1, 14, 30, tzinfo=UTC)
        diagnostics = build_economic_diagnostics(
            (
                EconomicSignal(
                    "WF_2022",
                    "A",
                    "S",
                    now,
                    1.0,
                    _target("A", Disposition.AMBIGUOUS_SAME_BAR),
                ),
                EconomicSignal(
                    "WF_2022",
                    "B",
                    "S",
                    now,
                    1.0,
                    _target("B", Disposition.NO_SCORE),
                ),
            )
        )
        self.assertEqual(diagnostics["primary"]["executed_trades"], 0)
        self.assertEqual(diagnostics["capacity_sensitivity"]["executed_trades"], 0)

    def test_touch_capacity_releases_at_observable_bar_close(self) -> None:
        start = datetime(2023, 6, 1, 14, 30, tzinfo=UTC)
        diagnostics = build_economic_diagnostics(
            (
                EconomicSignal(
                    "WF_2022",
                    "A",
                    "S",
                    start,
                    0.9,
                    _target("A", Disposition.FAVORABLE_FIRST, first_touch=15),
                ),
                EconomicSignal(
                    "WF_2022",
                    "B",
                    "S",
                    start + timedelta(minutes=15),
                    0.9,
                    _target("B", Disposition.FAVORABLE_FIRST, first_touch=1),
                ),
            )
        )
        primary = diagnostics["primary"]
        self.assertEqual(primary["executed_trades"], 1)
        self.assertEqual(primary["capacity_rejected_signals"], 1)
        self.assertTrue(primary["trades"][0]["release_time_utc"].endswith("14:46:00Z"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.core.hashing import dataframe_content_sha256
from mes_quant.features.builder import (
    FeatureBuildError,
    FeatureConfig,
    build_development_features,
)
from mes_quant.features.contract import FEATURE_COLUMNS


def synthetic_session_inputs(
    *,
    session_date: str = "2024-01-02",
    market_open_utc: str = "2024-01-02T14:30:00Z",
    market_close_utc: str = "2024-01-02T21:00:00Z",
    early_close_session: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    market_open = pd.Timestamp(market_open_utc)
    market_close = pd.Timestamp(market_close_utc)
    decision_times = pd.date_range(
        market_open + pd.Timedelta(minutes=15),
        market_close - pd.Timedelta(minutes=60),
        freq="15min",
    )
    first_market_end = decision_times[0] - pd.Timedelta(minutes=240)
    market_end_times = pd.date_range(first_market_end, decision_times[-1], freq="15min")
    market_start_times = market_end_times - pd.Timedelta(minutes=15)

    sequence = np.arange(len(market_end_times), dtype="float64")
    close = (
        100.0
        + 0.18 * sequence
        + 0.11 * np.sin(sequence * 0.73)
        + 0.025 * np.square(sequence % 3)
    )
    open_ = close - 0.08 + 0.015 * (sequence % 2)
    high = np.maximum(open_, close) + 0.32
    low = np.minimum(open_, close) - 0.27
    volume = 100.0 + 6.0 * sequence + 4.0 * (sequence % 4)

    bars = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "instrument_id": np.repeat(101, len(market_end_times)),
            "active_1m_count": np.repeat(15, len(market_end_times)),
            "bar_complete_15m": np.repeat(True, len(market_end_times)),
            "crosses_roll": np.repeat(False, len(market_end_times)),
            "decision_time": market_end_times,
        },
        index=market_start_times,
    )
    bars.index.name = "ts_event"

    decision_ids = [f"DEV-{index:02d}" for index in range(len(decision_times))]
    universe = pd.DataFrame(
        {
            "decision_id": decision_ids,
            "decision_time": decision_times,
            "nyse_session_date": np.repeat(pd.Timestamp(session_date), len(decision_times)),
            "instrument_id": np.repeat(101, len(decision_times)),
            "nyse_market_open_utc": np.repeat(market_open, len(decision_times)),
            "nyse_market_close_utc": np.repeat(market_close, len(decision_times)),
            "early_close_session": np.repeat(early_close_session, len(decision_times)),
            "active_1m_count": np.repeat(15, len(decision_times)),
            "bar_complete_15m": np.repeat(True, len(decision_times)),
            "crosses_roll": np.repeat(False, len(decision_times)),
            "decision_eligible": np.repeat(True, len(decision_times)),
        }
    )
    assignments = pd.DataFrame(
        {
            "decision_id": decision_ids,
            "decision_time": decision_times,
            "nyse_session_date": np.repeat(pd.Timestamp(session_date), len(decision_times)),
            "instrument_id": np.repeat(101, len(decision_times)),
            "outer_partition": np.repeat("VALIDATION", len(decision_times)),
            "role_wf_2022": np.repeat("UNUSED", len(decision_times)),
            "role_wf_2023": np.repeat("UNUSED", len(decision_times)),
            "role_wf_2024": np.repeat("VALIDATION", len(decision_times)),
        }
    )
    return bars, universe, assignments


def build(
    bars: pd.DataFrame,
    universe: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    development_rows = int(
        assignments["outer_partition"].isin(["TRAIN", "VALIDATION"]).sum()
    )
    return build_development_features(
        bars,
        universe,
        assignments,
        config=FeatureConfig.for_testing(expected_development_rows=development_rows),
    ).features


def market_by_end_time(bars: pd.DataFrame) -> pd.DataFrame:
    return bars.sort_values("decision_time").set_index("decision_time")


class FeatureBuilderTests(unittest.TestCase):
    def test_feature_formulas_against_hand_calculation(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        result = build(bars, universe, assignments)
        row = result.iloc[-1]
        market = market_by_end_time(bars)
        decision_time = assignments["decision_time"].iloc[-1]
        fixed_window = market.loc[
            decision_time - pd.Timedelta(minutes=240) : decision_time
        ]
        closes = fixed_window["close"].to_numpy(dtype="float64")
        returns = np.log(closes[1:] / closes[:-1])

        self.assertTrue(row["feature_row_usable"])
        self.assertEqual(row["feature_status"], "PASS")
        self.assertEqual(row["feature_max_source_time_utc"], decision_time)

        for lag in range(4):
            self.assertAlmostEqual(
                row[f"ret_log_15m_lag{lag}"], returns[-1 - lag], places=14
            )
        for minutes, count in ((60, 4), (120, 8), (240, 16)):
            self.assertAlmostEqual(
                row[f"momentum_log_{minutes}m"],
                np.log(closes[-1] / closes[-1 - count]),
                places=14,
            )
            self.assertAlmostEqual(
                row[f"realized_vol_{minutes}m"],
                np.sqrt(np.sum(np.square(returns[-count:]))),
                places=14,
            )

        current = fixed_window.iloc[-1]
        self.assertAlmostEqual(
            row["bar_log_range_15m"], np.log(current["high"] / current["low"]), places=14
        )
        self.assertAlmostEqual(
            row["bar_log_body_15m"], np.log(current["close"] / current["open"]), places=14
        )
        self.assertAlmostEqual(
            row["bar_close_location"],
            (current["close"] - current["low"]) / (current["high"] - current["low"]),
            places=14,
        )
        self.assertAlmostEqual(row["log1p_volume_15m"], np.log1p(current["volume"]), places=14)
        self.assertAlmostEqual(
            row["volume_ratio_prev_60m"],
            current["volume"] / fixed_window["volume"].iloc[-5:-1].mean(),
            places=14,
        )
        self.assertAlmostEqual(
            row["volume_ratio_prev_240m"],
            current["volume"] / fixed_window["volume"].iloc[:-1].mean(),
            places=14,
        )

        expected_autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        self.assertAlmostEqual(row["return_autocorr_lag1_240m"], expected_autocorr, places=14)
        counts = np.array(
            [(returns < 0).sum(), (returns == 0).sum(), (returns > 0).sum()],
            dtype="float64",
        )
        probabilities = counts / 16.0
        expected_entropy = -sum(
            probability * np.log(probability)
            for probability in probabilities
            if probability > 0.0
        ) / np.log(3.0)
        self.assertAlmostEqual(row["sign_entropy_240m"], expected_entropy, places=14)

        self.assertEqual(row["minutes_since_nyse_open"], 330.0)
        self.assertEqual(row["minutes_to_horizon_safe_close"], 0.0)
        expected_angle = 2.0 * np.pi * 21.0 / 22.0
        self.assertAlmostEqual(row["decision_slot_sin"], np.sin(expected_angle), places=14)
        self.assertAlmostEqual(row["decision_slot_cos"], np.cos(expected_angle), places=14)
        self.assertEqual(row["weekday_1"], 1)
        self.assertEqual(sum(int(row[f"weekday_{day}"]) for day in range(5)), 1)
        self.assertEqual(row["early_close_session"], 0)
        self.assertEqual(set(FEATURE_COLUMNS), set(result.columns) & set(FEATURE_COLUMNS))

    def test_multi_decision_session_vwap_and_dynamic_lookback(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        result = build(bars, universe, assignments)
        market = market_by_end_time(bars)
        market_open = universe["nyse_market_open_utc"].iloc[0]

        for row_index in (0, 5, len(result) - 1):
            decision_time = assignments["decision_time"].iloc[row_index]
            session_window = market.loc[
                market_open + pd.Timedelta(minutes=15) : decision_time
            ]
            typical = (
                session_window["high"]
                + session_window["low"]
                + session_window["close"]
            ) / 3.0
            proxy = (typical * session_window["volume"]).sum() / session_window["volume"].sum()
            expected = np.log(session_window["close"].iloc[-1] / proxy)
            self.assertAlmostEqual(
                result.loc[row_index, "session_vwap_proxy_deviation"], expected, places=14
            )

            fixed_start = decision_time - pd.Timedelta(minutes=240)
            expected_start = min(fixed_start, market_open)
            self.assertEqual(
                result.loc[row_index, "feature_lookback_start_utc"], expected_start
            )

        self.assertEqual(
            result.iloc[-1]["feature_lookback_start_utc"],
            market_open,
        )

    def test_true_prefix_invariance_across_multiple_decisions(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        full = build(bars, universe, assignments)

        for cutoff in (0, 4, 10, len(assignments) - 1):
            cutoff_time = assignments["decision_time"].iloc[cutoff]
            prefix_bars = bars.loc[bars["decision_time"].le(cutoff_time)].copy()
            prefix_universe = universe.iloc[: cutoff + 1].copy()
            prefix_assignments = assignments.iloc[: cutoff + 1].copy()
            prefix = build(prefix_bars, prefix_universe, prefix_assignments)
            expected = full.iloc[: cutoff + 1].reset_index(drop=True)
            pd.testing.assert_frame_equal(prefix.reset_index(drop=True), expected)

    def test_future_append_and_perturbation_cannot_change_current_features(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        before = build(bars, universe, assignments)
        future_end = assignments["decision_time"].iloc[-1] + pd.Timedelta(minutes=15)
        future = bars.iloc[[-1]].copy()
        future.index = pd.DatetimeIndex(
            [future_end - pd.Timedelta(minutes=15)], name="ts_event"
        )
        future["decision_time"] = future_end
        future[["open", "high", "low", "close", "volume"]] = [
            9999.0,
            10001.0,
            9998.0,
            10000.0,
            999999.0,
        ]
        after = build(pd.concat([bars, future]), universe, assignments)
        pd.testing.assert_frame_equal(before, after)

    def test_missing_partial_and_roll_lookbacks_are_explicitly_unusable(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        oldest_index = bars.index[0]

        missing = build(bars.drop(index=oldest_index), universe, assignments)
        self.assertFalse(missing.loc[0, "feature_row_usable"])
        self.assertIn("MISSING_LOOKBACK_BAR", missing.loc[0, "feature_status"])
        self.assertTrue(pd.isna(missing.loc[0, "momentum_log_240m"]))

        partial_bars = bars.copy()
        partial_bars.loc[oldest_index, "active_1m_count"] = 14
        partial_bars.loc[oldest_index, "bar_complete_15m"] = False
        partial = build(partial_bars, universe, assignments)
        self.assertFalse(partial.loc[0, "feature_row_usable"])
        self.assertIn("PARTIAL_LOOKBACK_BAR", partial.loc[0, "feature_status"])

        roll_bars = bars.copy()
        roll_bars.loc[oldest_index, "crosses_roll"] = True
        roll = build(roll_bars, universe, assignments)
        self.assertFalse(roll.loc[0, "feature_row_usable"])
        self.assertIn("ROLL_OR_INSTRUMENT_CHANGE", roll.loc[0, "feature_status"])

    def test_regular_early_close_and_dst_calendar_semantics(self) -> None:
        regular = synthetic_session_inputs()
        regular_result = build(*regular)
        self.assertEqual(regular_result.iloc[0]["minutes_since_nyse_open"], 15.0)
        self.assertEqual(regular_result.iloc[-1]["minutes_to_horizon_safe_close"], 0.0)

        early = synthetic_session_inputs(
            session_date="2024-11-29",
            market_open_utc="2024-11-29T14:30:00Z",
            market_close_utc="2024-11-29T18:00:00Z",
            early_close_session=True,
        )
        early_result = build(*early)
        self.assertEqual(len(early_result), 10)
        self.assertTrue((early_result["early_close_session"] == 1).all())
        self.assertEqual(early_result.iloc[-1]["minutes_since_nyse_open"], 150.0)
        self.assertEqual(early_result.iloc[-1]["minutes_to_horizon_safe_close"], 0.0)

        after_dst = synthetic_session_inputs(
            session_date="2024-03-11",
            market_open_utc="2024-03-11T13:30:00Z",
            market_close_utc="2024-03-11T20:00:00Z",
        )
        dst_result = build(*after_dst)
        self.assertEqual(dst_result.iloc[0]["minutes_since_nyse_open"], 15.0)
        self.assertEqual(dst_result.iloc[-1]["minutes_to_horizon_safe_close"], 0.0)

    def test_invalid_calendar_metadata_is_rejected(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()

        misaligned_universe = universe.copy()
        misaligned_assignments = assignments.copy()
        misaligned_universe.loc[0, "decision_time"] += pd.Timedelta(minutes=1)
        misaligned_assignments.loc[0, "decision_time"] += pd.Timedelta(minutes=1)
        with self.assertRaisesRegex(FeatureBuildError, "15-minute NYSE session grid"):
            build(bars, misaligned_universe, misaligned_assignments)

        late_universe = universe.copy()
        late_assignments = assignments.copy()
        late_universe.loc[len(late_universe) - 1, "decision_time"] += pd.Timedelta(minutes=15)
        late_assignments.loc[len(late_assignments) - 1, "decision_time"] += pd.Timedelta(
            minutes=15
        )
        with self.assertRaisesRegex(FeatureBuildError, "horizon-safe"):
            build(bars, late_universe, late_assignments)

        inconsistent_universe = universe.copy()
        inconsistent_universe.loc[1, "early_close_session"] = True
        inconsistent_universe.loc[1, "nyse_market_close_utc"] = pd.Timestamp(
            "2024-01-02T18:00:00Z"
        )
        with self.assertRaisesRegex(FeatureBuildError, "changes within a session"):
            build(bars, inconsistent_universe, assignments)

    def test_deterministic_output_content_hash(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        first = build(bars.copy(), universe.copy(), assignments.copy())
        second = build(bars.copy(), universe.copy(), assignments.copy())
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(
            dataframe_content_sha256(first, index=False),
            dataframe_content_sha256(second, index=False),
        )
        self.assertTrue(
            first["feature_row_usable"].equals(first["feature_status"].eq("PASS"))
        )

    def test_final_test_assignment_never_becomes_a_feature_row(self) -> None:
        bars, universe, assignments = synthetic_session_inputs()
        final_open = pd.Timestamp("2025-01-02T14:30:00Z")
        final_time = final_open + pd.Timedelta(minutes=15)
        universe = pd.concat(
            [
                universe,
                pd.DataFrame(
                    {
                        "decision_id": ["FT-1"],
                        "decision_time": [final_time],
                        "nyse_session_date": [pd.Timestamp("2025-01-02")],
                        "instrument_id": [101],
                        "nyse_market_open_utc": [final_open],
                        "nyse_market_close_utc": [pd.Timestamp("2025-01-02T21:00:00Z")],
                        "early_close_session": [False],
                        "active_1m_count": [15],
                        "bar_complete_15m": [True],
                        "crosses_roll": [False],
                        "decision_eligible": [True],
                    }
                ),
            ],
            ignore_index=True,
        )
        assignments = pd.concat(
            [
                assignments,
                pd.DataFrame(
                    {
                        "decision_id": ["FT-1"],
                        "decision_time": [final_time],
                        "nyse_session_date": [pd.Timestamp("2025-01-02")],
                        "instrument_id": [101],
                        "outer_partition": ["FINAL_TEST"],
                        "role_wf_2022": ["UNUSED"],
                        "role_wf_2023": ["UNUSED"],
                        "role_wf_2024": ["UNUSED"],
                    }
                ),
            ],
            ignore_index=True,
        )
        result = build(bars, universe, assignments)
        self.assertEqual(len(result), 22)
        self.assertNotIn("FT-1", set(result["decision_id"]))


if __name__ == "__main__":
    unittest.main()

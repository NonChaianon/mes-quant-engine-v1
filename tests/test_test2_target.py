from __future__ import annotations

import inspect
import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import mes_quant.exploration.test2_target as target_module
from mes_quant.exploration.test2_path_contract import TICK_SIZE_POINTS
from mes_quant.exploration.test2_target import (
    Disposition,
    NoScoreReason,
    PathBar,
    PathTargetContractError,
    PathTargetRequest,
    PolicyAction,
    TargetCoverage,
    build_path_target_row,
    build_path_target_rows,
    l0_safety_counters,
    price_to_ticks,
)

ENTRY = 4000.0
_UNSET = object()


def _flat_path(
    entry: float = ENTRY,
    *,
    instrument_id: str = "MES",
) -> tuple[PathBar, ...]:
    return tuple(
        PathBar(
            minute_offset=offset,
            instrument_id=instrument_id,
            open_price=entry,
            high_price=entry,
            low_price=entry,
            close_price=entry,
        )
        for offset in range(60)
    )


def _with_bar(
    bars: tuple[PathBar, ...],
    offset: int,
    **changes: object,
) -> tuple[PathBar, ...]:
    updated = list(bars)
    updated[offset] = replace(updated[offset], **changes)
    return tuple(updated)


def _request(
    identity: str,
    *,
    entry: float | None = ENTRY,
    bars: tuple[PathBar, ...] | None = None,
    endpoint: float | None | object = _UNSET,
) -> PathTargetRequest:
    path = bars if bars is not None else _flat_path(ENTRY if entry is None else entry)
    if endpoint is _UNSET:
        close_59 = next(
            (bar.close_price for bar in path if bar.minute_offset == 59),
            None,
        )
    else:
        close_59 = endpoint
    return PathTargetRequest(
        decision_identity=identity,
        entry_reference_close=entry,
        endpoint_close_60m=close_59,
        bars=path,
    )


class Test2TargetDispositionTests(unittest.TestCase):
    def test_favorable_adverse_and_neither_dispositions(self) -> None:
        cases = (
            (
                "F",
                _with_bar(_flat_path(), 7, high_price=ENTRY + 4.0),
                Disposition.FAVORABLE_FIRST,
                1,
                7,
            ),
            (
                "A",
                _with_bar(_flat_path(), 7, low_price=ENTRY - 2.0),
                Disposition.ADVERSE_FIRST,
                0,
                7,
            ),
            ("N", _flat_path(), Disposition.NEITHER_TOUCH, 0, None),
        )
        for identity, bars, disposition, path_long, offset in cases:
            with self.subTest(disposition=disposition):
                row = build_path_target_row(_request(identity, bars=bars))
                self.assertEqual(row.disposition, disposition)
                self.assertEqual(row.path_long, path_long)
                self.assertEqual(row.first_touch_offset_minutes, offset)
                self.assertTrue(row.retained)
                self.assertEqual(row.policy_action, PolicyAction.SCORED)

    def test_same_bar_dual_touch_is_fail_closed_at_zero_and_later(self) -> None:
        for offset in (0, 11, 59):
            with self.subTest(offset=offset):
                bars = _with_bar(
                    _flat_path(),
                    offset,
                    high_price=ENTRY + 4.0,
                    low_price=ENTRY - 2.0,
                )
                row = build_path_target_row(_request(f"D{offset}", bars=bars))
                self.assertEqual(row.disposition, Disposition.AMBIGUOUS_SAME_BAR)
                self.assertIsNone(row.path_long)
                self.assertEqual(row.first_touch_offset_minutes, offset)
                self.assertFalse(row.retained)
                self.assertEqual(row.policy_action, PolicyAction.FLAT)
                self.assertIsNotNone(row.gross_move_points_60m)

    def test_barrier_equality_touches_and_one_tick_short_does_not(self) -> None:
        favorable = build_path_target_row(
            _request("F", bars=_with_bar(_flat_path(), 5, high_price=ENTRY + 4.0))
        )
        adverse = build_path_target_row(
            _request("A", bars=_with_bar(_flat_path(), 5, low_price=ENTRY - 2.0))
        )
        one_tick_short = _with_bar(
            _flat_path(),
            5,
            high_price=ENTRY + 3.75,
            low_price=ENTRY - 1.75,
        )
        neither = build_path_target_row(_request("N", bars=one_tick_short))
        self.assertEqual(favorable.disposition, Disposition.FAVORABLE_FIRST)
        self.assertEqual(adverse.disposition, Disposition.ADVERSE_FIRST)
        self.assertEqual(neither.disposition, Disposition.NEITHER_TOUCH)

    def test_prior_single_touch_wins_over_later_dual_touch(self) -> None:
        cases = (
            ("F", "high_price", ENTRY + 4.0, Disposition.FAVORABLE_FIRST),
            ("A", "low_price", ENTRY - 2.0, Disposition.ADVERSE_FIRST),
        )
        for identity, field, price, expected in cases:
            with self.subTest(expected=expected):
                bars = _with_bar(_flat_path(), 3, **{field: price})
                bars = _with_bar(
                    bars,
                    7,
                    high_price=ENTRY + 4.0,
                    low_price=ENTRY - 2.0,
                )
                row = build_path_target_row(_request(identity, bars=bars))
                self.assertEqual(row.disposition, expected)
                self.assertEqual(row.first_touch_offset_minutes, 3)

        dual_first = _with_bar(
            _flat_path(),
            3,
            high_price=ENTRY + 4.0,
            low_price=ENTRY - 2.0,
        )
        dual_first = _with_bar(dual_first, 7, high_price=ENTRY + 4.0)
        row = build_path_target_row(_request("D", bars=dual_first))
        self.assertEqual(row.disposition, Disposition.AMBIGUOUS_SAME_BAR)
        self.assertEqual(row.first_touch_offset_minutes, 3)

    def test_touch_offsets_zero_and_fifty_nine_remain_exact(self) -> None:
        for offset in (0, 59):
            with self.subTest(offset=offset):
                bars = _with_bar(_flat_path(), offset, high_price=ENTRY + 4.0)
                row = build_path_target_row(_request(f"D{offset}", bars=bars))
                self.assertEqual(row.first_touch_offset_minutes, offset)


class Test2TargetValidationTests(unittest.TestCase):
    def test_tick_conversion_accepts_exact_quarters_and_rejects_off_grid(self) -> None:
        self.assertEqual(TICK_SIZE_POINTS, 0.25)
        self.assertEqual(price_to_ticks(0.25, field="price"), 1)
        self.assertEqual(price_to_ticks(4123.25, field="price"), 16493)
        self.assertEqual(price_to_ticks(-2.5, field="price"), -10)
        for value in (4.001, 4.126):
            with self.subTest(value=value), self.assertRaisesRegex(
                PathTargetContractError, "tick grid"
            ):
                price_to_ticks(value, field="price")

    def test_nonfinite_and_off_grid_values_fail_in_every_input_surface(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                bars = _with_bar(_flat_path(), 1, high_price=value)
                with self.assertRaisesRegex(PathTargetContractError, "finite"):
                    build_path_target_row(_request("D", bars=bars))

        with self.assertRaisesRegex(PathTargetContractError, "tick grid"):
            build_path_target_row(_request("ENTRY", entry=4000.001))
        with self.assertRaisesRegex(PathTargetContractError, "tick grid"):
            build_path_target_row(_request("END", endpoint=4000.001))

    def test_small_and_negative_quarter_grid_paths_are_accepted(self) -> None:
        for entry in (0.25, -2.5):
            with self.subTest(entry=entry):
                row = build_path_target_row(
                    _request("D", entry=entry, bars=_flat_path(entry), endpoint=entry)
                )
                self.assertEqual(row.disposition, Disposition.NEITHER_TOUCH)
                self.assertEqual(row.gross_move_points_60m, 0.0)

    def test_endpoint_must_be_present_and_equal_in_integer_ticks(self) -> None:
        with self.assertRaisesRegex(PathTargetContractError, "requires endpoint"):
            build_path_target_row(_request("NONE", endpoint=None))
        with self.assertRaisesRegex(PathTargetContractError, "does not match"):
            build_path_target_row(_request("MISMATCH", endpoint=ENTRY + 0.25))
        row = build_path_target_row(_request("MATCH", endpoint=ENTRY))
        self.assertEqual(row.disposition, Disposition.NEITHER_TOUCH)

    def test_missing_path_is_no_score_but_present_corruption_is_hard(self) -> None:
        for missing_offset in (30, 59):
            with self.subTest(missing_offset=missing_offset):
                bars = tuple(bar for bar in _flat_path() if bar.minute_offset != missing_offset)
                row = build_path_target_row(_request("D", bars=bars, endpoint=None))
                self.assertEqual(row.disposition, Disposition.NO_SCORE)
                self.assertEqual(row.no_score_reason, NoScoreReason.MISSING_PATH_BAR)
                self.assertFalse(row.retained)
                self.assertEqual(row.policy_action, PolicyAction.FLAT)
                self.assertIsNone(row.first_touch_offset_minutes)
                self.assertIsNone(row.gross_move_points_60m)

        corrupt = tuple(bar for bar in _flat_path() if bar.minute_offset != 30)
        corrupt = _with_bar(corrupt, 1, high_price=ENTRY + 0.001)
        with self.assertRaisesRegex(PathTargetContractError, "tick grid"):
            build_path_target_row(_request("CORRUPT", bars=corrupt, endpoint=None))

    def test_missing_entry_is_no_score_with_payload_cleared(self) -> None:
        row = build_path_target_row(
            _request("D", entry=None, bars=_flat_path(), endpoint=ENTRY)
        )
        self.assertEqual(row.disposition, Disposition.NO_SCORE)
        self.assertEqual(row.no_score_reason, NoScoreReason.MISSING_ENTRY_REFERENCE)
        self.assertFalse(row.retained)
        self.assertEqual(row.policy_action, PolicyAction.FLAT)
        self.assertIsNone(row.instrument_id)
        self.assertIsNone(row.entry_reference_ticks)

    def test_duplicate_missing_out_of_range_and_noninteger_offsets_fail_closed(self) -> None:
        duplicate = list(_flat_path())
        duplicate[59] = replace(duplicate[59], minute_offset=5)
        cases = (
            ("duplicate", tuple(duplicate)),
            ("negative", (replace(_flat_path()[0], minute_offset=-1),)),
            ("sixty", _flat_path() + (replace(_flat_path()[0], minute_offset=60),)),
            ("float", (replace(_flat_path()[0], minute_offset=1.0),)),
        )
        for label, bars in cases:
            with self.subTest(label=label), self.assertRaises(PathTargetContractError):
                build_path_target_row(_request(label, bars=bars))

    def test_instrument_and_ohlc_corruption_fail_closed(self) -> None:
        mixed = _with_bar(_flat_path(), 12, instrument_id="MNQ")
        with self.assertRaisesRegex(PathTargetContractError, "must be MES"):
            build_path_target_row(_request("MIXED", bars=mixed))
        with self.assertRaisesRegex(PathTargetContractError, "must be MES"):
            build_path_target_row(_request("ALL_MNQ", bars=_flat_path(instrument_id="MNQ")))

        corruptions = (
            {"low_price": ENTRY + 0.25},
            {"high_price": ENTRY - 0.25},
            {"open_price": ENTRY + 0.25},
            {"close_price": ENTRY - 0.25},
        )
        for changes in corruptions:
            with self.subTest(changes=changes):
                bars = _with_bar(_flat_path(), 4, **changes)
                with self.assertRaises(PathTargetContractError):
                    build_path_target_row(_request("D", bars=bars))


class Test2TargetAccountingTests(unittest.TestCase):
    def test_gross_move_is_tick_derived_and_independent_of_disposition(self) -> None:
        bars = _with_bar(_flat_path(), 3, low_price=ENTRY - 2.0)
        bars = _with_bar(
            bars,
            59,
            high_price=ENTRY + 1.0,
            close_price=ENTRY + 1.0,
        )
        row = build_path_target_row(_request("POSITIVE_END", bars=bars))
        self.assertEqual(row.disposition, Disposition.ADVERSE_FIRST)
        self.assertEqual(row.gross_move_points_60m, 1.0)

        down = _with_bar(
            _flat_path(),
            59,
            low_price=ENTRY - 2.25,
            close_price=ENTRY - 2.25,
        )
        down_row = build_path_target_row(_request("DOWN", bars=down))
        self.assertEqual(down_row.gross_move_points_60m, -2.25)

    def test_batch_accounting_covers_all_dispositions(self) -> None:
        favorable = _with_bar(_flat_path(), 2, high_price=ENTRY + 4.0)
        adverse = _with_bar(_flat_path(), 2, low_price=ENTRY - 2.0)
        ambiguous = _with_bar(
            _flat_path(),
            2,
            high_price=ENTRY + 4.0,
            low_price=ENTRY - 2.0,
        )
        incomplete = tuple(bar for bar in _flat_path() if bar.minute_offset != 20)
        rows, coverage = build_path_target_rows(
            (
                _request("F", bars=favorable),
                _request("A", bars=adverse),
                _request("N"),
                _request("X", bars=ambiguous),
                _request("Z", bars=incomplete, endpoint=None),
            )
        )
        self.assertEqual(len(rows), 5)
        self.assertEqual(
            coverage,
            TargetCoverage(
                total_rows=5,
                favorable_first=1,
                adverse_first=1,
                neither_touch=1,
                ambiguous_same_bar=1,
                no_score=1,
                retained_rows=3,
                flat_rows=2,
            ),
        )

    def test_duplicate_batch_identity_and_bad_coverage_fail_closed(self) -> None:
        with self.assertRaisesRegex(PathTargetContractError, "unique"):
            build_path_target_rows((_request("D"), _request("D")))
        with self.assertRaisesRegex(PathTargetContractError, "do not sum"):
            TargetCoverage(
                total_rows=1,
                favorable_first=0,
                adverse_first=0,
                neither_touch=0,
                ambiguous_same_bar=0,
                no_score=0,
                retained_rows=0,
                flat_rows=0,
            )

    def test_safety_counters_firewall_and_purity(self) -> None:
        counters = l0_safety_counters()
        self.assertEqual(len(counters), 5)
        self.assertEqual(set(counters.values()), {0})

        source = inspect.getsource(target_module)
        for forbidden in (
            "pandas",
            "numpy",
            "pyarrow",
            "pathlib",
            "test2_request_set",
            "open(",
            "import requests",
            "from requests",
        ):
            self.assertNotIn(forbidden, source)

        request = _request("PURE", bars=_flat_path())
        self.assertEqual(build_path_target_row(request), build_path_target_row(request))


if __name__ == "__main__":
    unittest.main()

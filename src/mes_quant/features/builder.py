from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mes_quant.features.contract import (
    FEATURE_COLUMNS,
    FORBIDDEN_TARGET_TOKENS,
    METADATA_COLUMNS,
    POLICY_VERSION,
)
from mes_quant.labels.sealing import assert_no_final_test_rows, assert_target_columns_absent


class FeatureBuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeatureConfig:
    policy_version: str = POLICY_VERSION
    bar_minutes: int = 15
    maximum_lookback_bars: int = 16
    session_vwap_max_bars: int = 22
    expected_development_rows: int | None = 31_193
    development_partitions: tuple[str, ...] = ("TRAIN", "VALIDATION")
    final_test_start_year: int = 2025
    required_active_1m_count: int = 15
    decision_slot_count: int = 22
    session_timezone: str = "America/New_York"
    test_only_allow_noncanonical_row_count: bool = False

    @classmethod
    def from_json(cls, path: str | Path) -> FeatureConfig:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        expected_keys = {
            "policy_version",
            "bar_minutes",
            "maximum_lookback_bars",
            "session_vwap_max_bars",
            "expected_development_rows",
            "development_partitions",
            "final_test_start_year",
            "required_active_1m_count",
            "decision_slot_count",
            "session_timezone",
        }
        if set(payload) != expected_keys:
            raise FeatureBuildError(
                "Feature config keys mismatch; "
                f"missing={sorted(expected_keys - set(payload))}, "
                f"extra={sorted(set(payload) - expected_keys)}"
            )
        payload["development_partitions"] = tuple(payload["development_partitions"])
        config = cls(**payload)
        config.validate(production=True)
        return config

    @classmethod
    def for_testing(cls, *, expected_development_rows: int | None = None) -> FeatureConfig:
        return cls(
            expected_development_rows=expected_development_rows,
            test_only_allow_noncanonical_row_count=True,
        )

    def validate(self, *, production: bool = False) -> None:
        locked = {
            "policy_version": POLICY_VERSION,
            "bar_minutes": 15,
            "maximum_lookback_bars": 16,
            "session_vwap_max_bars": 22,
            "development_partitions": ("TRAIN", "VALIDATION"),
            "final_test_start_year": 2025,
            "required_active_1m_count": 15,
            "decision_slot_count": 22,
            "session_timezone": "America/New_York",
        }
        failures = [
            f"{name}={getattr(self, name)!r} (expected {expected!r})"
            for name, expected in locked.items()
            if getattr(self, name) != expected
        ]
        if self.expected_development_rows != 31_193 and not self.test_only_allow_noncanonical_row_count:
            failures.append(
                "expected_development_rows must be 31,193 outside explicit synthetic tests"
            )
        if production and (
            self.expected_development_rows != 31_193
            or self.test_only_allow_noncanonical_row_count
        ):
            failures.append("Production config cannot enable the synthetic row-count override")
        if failures:
            raise FeatureBuildError("Noncanonical V1 feature config:\n- " + "\n- ".join(failures))


@dataclass
class FeatureBuildResult:
    features: pd.DataFrame
    missingness_ledger: pd.DataFrame = field(default_factory=pd.DataFrame)
    diagnostics: dict[str, Any] = field(default_factory=dict)


ASSIGNMENT_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "role_wf_2024",
)

UNIVERSE_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "nyse_market_open_utc",
    "nyse_market_close_utc",
    "early_close_session",
    "active_1m_count",
    "bar_complete_15m",
    "crosses_roll",
    "decision_eligible",
)

BAR_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "instrument_id",
    "active_1m_count",
    "bar_complete_15m",
    "crosses_roll",
    "decision_time",
)


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise FeatureBuildError(f"{label} missing required columns: {', '.join(missing)}")


def _strict_bool(series: pd.Series, label: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.astype(bool)
    mapping = {
        True: True,
        False: False,
        "True": True,
        "False": False,
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }
    converted = series.map(mapping)
    if converted.isna().any():
        bad = sorted({str(value) for value in series[converted.isna()].unique()})
        raise FeatureBuildError(f"{label} contains non-boolean tokens: {bad}")
    return converted.astype(bool)


def _utc_nanoseconds(values: object) -> np.ndarray:
    """Return epoch nanoseconds even when pandas stores timestamps in microseconds."""

    index = pd.DatetimeIndex(pd.to_datetime(values, utc=True, errors="raise"))
    if hasattr(index, "as_unit"):
        index = index.as_unit("ns")
    return index.asi8


def _prepare_decisions(
    universe: pd.DataFrame,
    assignments: pd.DataFrame,
    config: FeatureConfig,
) -> pd.DataFrame:
    _require_columns(assignments, ASSIGNMENT_COLUMNS, "Cell 8 assignments")
    _require_columns(universe, UNIVERSE_COLUMNS, "Cell 7 universe")

    if assignments["decision_id"].isna().any() or universe["decision_id"].isna().any():
        raise FeatureBuildError("decision_id cannot be null")
    if assignments["decision_id"].duplicated().any():
        raise FeatureBuildError("Duplicate decision_id in Cell 8 assignments")
    if universe["decision_id"].duplicated().any():
        raise FeatureBuildError("Duplicate decision_id in Cell 7 universe")

    left = assignments.loc[:, ASSIGNMENT_COLUMNS].copy()
    right = universe.loc[:, UNIVERSE_COLUMNS].copy()
    left["decision_time"] = pd.to_datetime(left["decision_time"], utc=True, errors="raise")
    right["decision_time"] = pd.to_datetime(right["decision_time"], utc=True, errors="raise")
    left["nyse_session_date"] = pd.to_datetime(
        left["nyse_session_date"], errors="raise"
    ).dt.normalize()
    right["nyse_session_date"] = pd.to_datetime(
        right["nyse_session_date"], errors="raise"
    ).dt.normalize()

    merged = left.merge(
        right,
        on="decision_id",
        how="inner",
        validate="one_to_one",
        suffixes=("_assignment", "_universe"),
    )
    if len(merged) != len(assignments) or len(merged) != len(universe):
        raise FeatureBuildError("Cell 7 and Cell 8 decision IDs do not reconcile one-to-one")

    if not np.array_equal(
        _utc_nanoseconds(merged["decision_time_assignment"]),
        _utc_nanoseconds(merged["decision_time_universe"]),
    ):
        raise FeatureBuildError("Cell 7/8 decision_time mismatch")
    if not merged["nyse_session_date_assignment"].equals(
        merged["nyse_session_date_universe"]
    ):
        raise FeatureBuildError("Cell 7/8 NYSE session mismatch")
    if not merged["instrument_id_assignment"].astype("string").equals(
        merged["instrument_id_universe"].astype("string")
    ):
        raise FeatureBuildError("Cell 7/8 instrument mismatch")

    merged["decision_eligible"] = _strict_bool(
        merged["decision_eligible"], "decision_eligible"
    )
    merged["bar_complete_15m"] = _strict_bool(
        merged["bar_complete_15m"], "bar_complete_15m"
    )
    merged["crosses_roll"] = _strict_bool(merged["crosses_roll"], "crosses_roll")
    merged["early_close_session"] = _strict_bool(
        merged["early_close_session"], "early_close_session"
    )

    if not merged["decision_eligible"].all():
        raise FeatureBuildError("Ineligible row found in frozen Decision Universe")
    if not merged["bar_complete_15m"].all():
        raise FeatureBuildError("Partial current decision bar found in frozen Decision Universe")
    if merged["crosses_roll"].any():
        raise FeatureBuildError("Roll-cross current decision bar found in Decision Universe")
    active_current = pd.to_numeric(merged["active_1m_count"], errors="raise")
    if not active_current.eq(config.required_active_1m_count).all():
        raise FeatureBuildError("Current Decision Universe bar does not contain 15 active minutes")

    decisions = pd.DataFrame(
        {
            "decision_id": merged["decision_id"],
            "decision_time": merged["decision_time_assignment"],
            "nyse_session_date": merged["nyse_session_date_assignment"],
            "instrument_id": merged["instrument_id_assignment"],
            "outer_partition": merged["outer_partition"],
            "role_wf_2022": merged["role_wf_2022"],
            "role_wf_2023": merged["role_wf_2023"],
            "role_wf_2024": merged["role_wf_2024"],
            "nyse_market_open_utc": pd.to_datetime(
                merged["nyse_market_open_utc"], utc=True, errors="raise"
            ),
            "nyse_market_close_utc": pd.to_datetime(
                merged["nyse_market_close_utc"], utc=True, errors="raise"
            ),
            "early_close_session": merged["early_close_session"].astype(bool),
        }
    )
    decisions = decisions.loc[
        decisions["outer_partition"].isin(config.development_partitions)
    ].copy()
    decisions = decisions.sort_values(["decision_time", "decision_id"]).reset_index(drop=True)

    if config.expected_development_rows is not None and len(decisions) != int(
        config.expected_development_rows
    ):
        raise FeatureBuildError(
            "Development row count mismatch: "
            f"{len(decisions):,} != {config.expected_development_rows:,}"
        )
    if decisions["decision_id"].duplicated().any():
        raise FeatureBuildError("Duplicate Development decision_id")
    if decisions["decision_time"].duplicated().any():
        raise FeatureBuildError("Duplicate Development decision_time")

    minute_ns = pd.Timedelta(minutes=1).value
    elapsed_ns = _utc_nanoseconds(decisions["decision_time"]) - _utc_nanoseconds(
        decisions["nyse_market_open_utc"]
    )
    safe_remaining_ns = (
        _utc_nanoseconds(decisions["nyse_market_close_utc"])
        - pd.Timedelta(minutes=60).value
        - _utc_nanoseconds(decisions["decision_time"])
    )
    elapsed_minutes = elapsed_ns / minute_ns
    slot = (elapsed_minutes - 15.0) / 15.0
    if (elapsed_ns <= 0).any() or (safe_remaining_ns < 0).any():
        raise FeatureBuildError("Decision lies outside the horizon-safe NYSE session window")
    if np.any(elapsed_ns % pd.Timedelta(minutes=15).value != 0):
        raise FeatureBuildError("Decision is not aligned to the 15-minute NYSE session grid")
    if not np.all(np.isclose(slot, np.round(slot), rtol=0.0, atol=1e-12)):
        raise FeatureBuildError("Decision slot is not an integer")
    if np.any((slot < 0.0) | (slot >= config.decision_slot_count)):
        raise FeatureBuildError("Decision slot is outside the locked V1 range 0..21")

    local_dates = (
        decisions["decision_time"]
        .dt.tz_convert(config.session_timezone)
        .dt.tz_localize(None)
        .dt.normalize()
    )
    if not local_dates.equals(decisions["nyse_session_date"]):
        raise FeatureBuildError("NYSE session date does not match decision_time in New York")
    if decisions["nyse_session_date"].dt.weekday.ge(5).any():
        raise FeatureBuildError("Weekend session found in Development decisions")

    local_opens = decisions["nyse_market_open_utc"].dt.tz_convert(
        config.session_timezone
    )
    local_closes = decisions["nyse_market_close_utc"].dt.tz_convert(
        config.session_timezone
    )
    if not local_opens.dt.time.eq(time(9, 30)).all():
        raise FeatureBuildError("NYSE market open must be 09:30 America/New_York")
    expected_close_times = np.where(
        decisions["early_close_session"].to_numpy(), time(13, 0), time(16, 0)
    )
    if not np.array_equal(local_closes.dt.time.to_numpy(), expected_close_times):
        raise FeatureBuildError(
            "NYSE market close must be 16:00, or 13:00 for an early-close session"
        )

    session_consistency = decisions.groupby("nyse_session_date", sort=False).agg(
        open_count=("nyse_market_open_utc", "nunique"),
        close_count=("nyse_market_close_utc", "nunique"),
        early_close_count=("early_close_session", "nunique"),
    )
    if (session_consistency != 1).any(axis=None):
        raise FeatureBuildError("NYSE open/close/early-close metadata changes within a session")
    assert_no_final_test_rows(
        decisions,
        final_test_start_year=config.final_test_start_year,
    )
    return decisions


def _prepare_bars(
    bars: pd.DataFrame,
    decisions: pd.DataFrame,
    config: FeatureConfig,
) -> pd.DataFrame:
    _require_columns(bars, BAR_COLUMNS, "Cell 5 bars")
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise FeatureBuildError("Cell 5 bars require a DatetimeIndex of bar starts")
    result = bars.loc[:, BAR_COLUMNS].copy()
    result.index = pd.to_datetime(result.index, utc=True, errors="raise")
    result["decision_time"] = pd.to_datetime(result["decision_time"], utc=True, errors="raise")
    result = result.sort_index()
    if result.index.duplicated().any() or not result.index.is_monotonic_increasing:
        raise FeatureBuildError("Cell 5 bar-start index must be unique and sorted")
    if result["decision_time"].duplicated().any():
        raise FeatureBuildError("Cell 5 decision_time must be unique")
    expected_end = result.index + pd.Timedelta(minutes=config.bar_minutes)
    if not np.array_equal(
        _utc_nanoseconds(expected_end), _utc_nanoseconds(result["decision_time"])
    ):
        raise FeatureBuildError("Cell 5 decision_time is not bar_start + 15 minutes")

    result["bar_complete_15m"] = _strict_bool(
        result["bar_complete_15m"], "Cell 5 bar_complete_15m"
    )
    result["crosses_roll"] = _strict_bool(result["crosses_roll"], "Cell 5 crosses_roll")

    fixed_window_start = decisions["decision_time"].min() - pd.Timedelta(
        minutes=config.maximum_lookback_bars * config.bar_minutes
    )
    first_session_source = decisions["nyse_market_open_utc"].min()
    first_required = min(fixed_window_start, first_session_source)
    last_allowed = decisions["decision_time"].max()
    result = result.loc[
        result["decision_time"].between(first_required, last_allowed, inclusive="both")
    ].copy()
    if result.empty:
        raise FeatureBuildError("No Cell 5 bars remain in the Development feature window")
    if result["decision_time"].gt(last_allowed).any():
        raise FeatureBuildError("Market data after the final Development decision was returned")
    return result


def _take_numeric(source: np.ndarray, positions: np.ndarray) -> np.ndarray:
    result = np.full(positions.shape, np.nan, dtype="float64")
    present = positions >= 0
    result[present] = source[positions[present]].astype("float64", copy=False)
    return result


def _take_object(source: np.ndarray, positions: np.ndarray) -> np.ndarray:
    result = np.empty(positions.shape, dtype=object)
    result[:] = None
    present = positions >= 0
    result[present] = source[positions[present]]
    return result


def _take_bool(source: np.ndarray, positions: np.ndarray) -> np.ndarray:
    result = np.zeros(positions.shape, dtype=bool)
    present = positions >= 0
    result[present] = source[positions[present]].astype(bool, copy=False)
    return result


def _session_vwap_proxy(
    decisions: pd.DataFrame,
    market: pd.DataFrame,
    *,
    required_active_1m_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    result = np.full(len(decisions), np.nan, dtype="float64")
    valid_session = np.zeros(len(decisions), dtype=bool)
    decision_ns = _utc_nanoseconds(decisions["decision_time"])
    open_ns = _utc_nanoseconds(decisions["nyse_market_open_utc"])
    decision_instrument = decisions["instrument_id"].astype("string").to_numpy(dtype=object)
    step_ns = pd.Timedelta(minutes=15).value

    market_index = pd.DatetimeIndex(market["decision_time"])
    if hasattr(market_index, "as_unit"):
        market_index = market_index.as_unit("ns")
    market_high = pd.to_numeric(market["high"], errors="raise").to_numpy(dtype="float64")
    market_low = pd.to_numeric(market["low"], errors="raise").to_numpy(dtype="float64")
    market_close = pd.to_numeric(market["close"], errors="raise").to_numpy(dtype="float64")
    market_volume = pd.to_numeric(market["volume"], errors="raise").to_numpy(dtype="float64")
    market_active = pd.to_numeric(market["active_1m_count"], errors="raise").to_numpy()
    market_complete = market["bar_complete_15m"].to_numpy(dtype=bool)
    market_roll = market["crosses_roll"].to_numpy(dtype=bool)
    market_instrument = market["instrument_id"].astype("string").to_numpy(dtype=object)

    for indices in decisions.groupby("nyse_session_date", sort=False).indices.values():
        idx = np.asarray(indices, dtype="int64")
        session_open_ns = open_ns[idx[0]]
        final_slot_count = int((decision_ns[idx[-1]] - session_open_ns) // step_ns)
        expected_ns = session_open_ns + step_ns * np.arange(
            1, final_slot_count + 1, dtype="int64"
        )
        expected_times = pd.to_datetime(expected_ns, utc=True)
        positions = market_index.get_indexer(expected_times)
        present = positions >= 0

        highs = np.full(final_slot_count, np.nan, dtype="float64")
        lows = np.full(final_slot_count, np.nan, dtype="float64")
        closes = np.full(final_slot_count, np.nan, dtype="float64")
        volumes = np.full(final_slot_count, np.nan, dtype="float64")
        active = np.full(final_slot_count, np.nan, dtype="float64")
        complete = np.zeros(final_slot_count, dtype=bool)
        rolls = np.zeros(final_slot_count, dtype=bool)
        instruments = np.empty(final_slot_count, dtype=object)
        instruments[:] = None
        if present.any():
            selected = positions[present]
            highs[present] = market_high[selected]
            lows[present] = market_low[selected]
            closes[present] = market_close[selected]
            volumes[present] = market_volume[selected]
            active[present] = market_active[selected]
            complete[present] = market_complete[selected]
            rolls[present] = market_roll[selected]
            instruments[present] = market_instrument[selected]

        structurally_valid = (
            present
            & complete
            & (active == float(required_active_1m_count))
            & ~rolls
            & np.isfinite(highs)
            & np.isfinite(lows)
            & np.isfinite(closes)
            & np.isfinite(volumes)
            & (volumes >= 0.0)
        )
        typical = (highs + lows + closes) / 3.0

        for row in idx:
            slot_count = int((decision_ns[row] - session_open_ns) // step_ns)
            prefix = slice(0, slot_count)
            same_instrument = instruments[prefix] == decision_instrument[row]
            usable = structurally_valid[prefix].all() and same_instrument.all()
            if not usable:
                continue
            cumulative_volume = float(np.sum(volumes[prefix]))
            if cumulative_volume <= 0.0 or closes[slot_count - 1] <= 0.0:
                continue
            proxy = float(np.sum(typical[prefix] * volumes[prefix]) / cumulative_volume)
            if proxy <= 0.0:
                continue
            result[row] = np.log(closes[slot_count - 1] / proxy)
            valid_session[row] = True
    return result, valid_session


def build_development_features(
    bars: pd.DataFrame,
    universe: pd.DataFrame,
    assignments: pd.DataFrame,
    *,
    config: FeatureConfig | None = None,
) -> FeatureBuildResult:
    config = config or FeatureConfig()
    config.validate(production=False)

    decisions = _prepare_decisions(universe, assignments, config)
    market = _prepare_bars(bars, decisions, config)
    market = market.sort_values("decision_time").reset_index(drop=True)
    market_index = pd.DatetimeIndex(market["decision_time"])
    if hasattr(market_index, "as_unit"):
        market_index = market_index.as_unit("ns")

    decision_ns = _utc_nanoseconds(decisions["decision_time"])
    step_ns = pd.Timedelta(minutes=config.bar_minutes).value
    offsets = np.arange(config.maximum_lookback_bars, -1, -1, dtype="int64")
    wanted_ns = decision_ns[:, None] - offsets[None, :] * step_ns
    wanted = pd.to_datetime(wanted_ns.ravel(), utc=True)
    positions = market_index.get_indexer(wanted).reshape(wanted_ns.shape)
    present = positions >= 0

    opens = _take_numeric(pd.to_numeric(market["open"], errors="raise").to_numpy(), positions)
    highs = _take_numeric(pd.to_numeric(market["high"], errors="raise").to_numpy(), positions)
    lows = _take_numeric(pd.to_numeric(market["low"], errors="raise").to_numpy(), positions)
    closes = _take_numeric(pd.to_numeric(market["close"], errors="raise").to_numpy(), positions)
    volumes = _take_numeric(pd.to_numeric(market["volume"], errors="raise").to_numpy(), positions)
    instruments = _take_object(
        market["instrument_id"].astype("string").to_numpy(dtype=object), positions
    )
    active = _take_numeric(
        pd.to_numeric(market["active_1m_count"], errors="raise").to_numpy(), positions
    )
    complete_flag = _take_bool(market["bar_complete_15m"].to_numpy(), positions)
    crosses_roll = _take_bool(market["crosses_roll"].to_numpy(), positions)

    decision_instruments = decisions["instrument_id"].astype("string").to_numpy(dtype=object)
    same_instrument = present & (instruments == decision_instruments[:, None])
    complete = (
        present
        & complete_flag
        & (active == float(config.required_active_1m_count))
        & ~crosses_roll
    )
    valid = complete & same_instrument
    positive_close = closes > 0.0

    returns = np.full((len(decisions), 16), np.nan, dtype="float64")
    return_valid = valid[:, :-1] & valid[:, 1:] & positive_close[:, :-1] & positive_close[:, 1:]
    with np.errstate(divide="ignore", invalid="ignore"):
        raw_returns = np.log(closes[:, 1:] / closes[:, :-1])
    returns[return_valid] = raw_returns[return_valid]

    feature_values: dict[str, np.ndarray] = {}
    for lag in range(4):
        column = 15 - lag
        values = np.full(len(decisions), np.nan, dtype="float64")
        mask = return_valid[:, column]
        values[mask] = returns[mask, column]
        feature_values[f"ret_log_15m_lag{lag}"] = values

    for minutes, bars_count in ((60, 4), (120, 8), (240, 16)):
        start_close = 16 - bars_count
        window_valid = valid[:, start_close:].all(axis=1)
        positive = (closes[:, start_close] > 0.0) & (closes[:, 16] > 0.0)
        momentum = np.full(len(decisions), np.nan, dtype="float64")
        mask = window_valid & positive
        momentum[mask] = np.log(closes[mask, 16] / closes[mask, start_close])
        feature_values[f"momentum_log_{minutes}m"] = momentum

        start_return = 16 - bars_count
        return_window_ok = return_valid[:, start_return:].all(axis=1)
        realized = np.full(len(decisions), np.nan, dtype="float64")
        realized[return_window_ok] = np.sqrt(
            np.sum(np.square(returns[return_window_ok, start_return:]), axis=1)
        )
        feature_values[f"realized_vol_{minutes}m"] = realized

    current_valid = valid[:, 16]
    current_open = opens[:, 16]
    current_high = highs[:, 16]
    current_low = lows[:, 16]
    current_close = closes[:, 16]
    current_volume = volumes[:, 16]

    bar_range = np.full(len(decisions), np.nan, dtype="float64")
    mask = current_valid & (current_high > 0.0) & (current_low > 0.0)
    bar_range[mask] = np.log(current_high[mask] / current_low[mask])
    feature_values["bar_log_range_15m"] = bar_range

    bar_body = np.full(len(decisions), np.nan, dtype="float64")
    mask = current_valid & (current_open > 0.0) & (current_close > 0.0)
    bar_body[mask] = np.log(current_close[mask] / current_open[mask])
    feature_values["bar_log_body_15m"] = bar_body

    close_location = np.full(len(decisions), np.nan, dtype="float64")
    denominator = current_high - current_low
    mask = current_valid & (denominator > 0.0)
    close_location[mask] = (current_close[mask] - current_low[mask]) / denominator[mask]
    feature_values["bar_close_location"] = close_location

    log_volume = np.full(len(decisions), np.nan, dtype="float64")
    mask = current_valid & (current_volume >= 0.0)
    log_volume[mask] = np.log1p(current_volume[mask])
    feature_values["log1p_volume_15m"] = log_volume

    for minutes, previous_bars in ((60, 4), (240, 16)):
        start = 16 - previous_bars
        window_ok = valid[:, start:17].all(axis=1)
        previous_mean = np.mean(volumes[:, start:16], axis=1)
        ratio = np.full(len(decisions), np.nan, dtype="float64")
        mask = window_ok & (previous_mean > 0.0) & (current_volume >= 0.0)
        ratio[mask] = current_volume[mask] / previous_mean[mask]
        feature_values[f"volume_ratio_prev_{minutes}m"] = ratio

    vwap_proxy, vwap_valid = _session_vwap_proxy(
        decisions,
        market,
        required_active_1m_count=config.required_active_1m_count,
    )
    feature_values["session_vwap_proxy_deviation"] = vwap_proxy

    full_return_window = return_valid.all(axis=1)
    x = returns[:, :-1]
    y = returns[:, 1:]
    x_centered = np.zeros_like(x)
    y_centered = np.zeros_like(y)
    correlation_denominator = np.zeros(len(decisions), dtype="float64")
    if full_return_window.any():
        x_valid = x[full_return_window]
        y_valid = y[full_return_window]
        x_centered_valid = x_valid - x_valid.mean(axis=1, keepdims=True)
        y_centered_valid = y_valid - y_valid.mean(axis=1, keepdims=True)
        x_centered[full_return_window] = x_centered_valid
        y_centered[full_return_window] = y_centered_valid
        correlation_denominator[full_return_window] = np.sqrt(
            np.sum(np.square(x_centered_valid), axis=1)
            * np.sum(np.square(y_centered_valid), axis=1)
        )
    autocorr = np.full(len(decisions), np.nan, dtype="float64")
    mask = full_return_window & (correlation_denominator > 0.0)
    autocorr[mask] = (
        np.sum(x_centered[mask] * y_centered[mask], axis=1)
        / correlation_denominator[mask]
    )
    feature_values["return_autocorr_lag1_240m"] = autocorr

    entropy = np.full(len(decisions), np.nan, dtype="float64")
    if full_return_window.any():
        valid_returns = returns[full_return_window]
        counts = np.stack(
            [
                (valid_returns < 0.0).sum(axis=1),
                (valid_returns == 0.0).sum(axis=1),
                (valid_returns > 0.0).sum(axis=1),
            ],
            axis=1,
        ).astype("float64")
        probabilities = counts / 16.0
        with np.errstate(divide="ignore", invalid="ignore"):
            terms = np.where(probabilities > 0.0, probabilities * np.log(probabilities), 0.0)
        entropy[full_return_window] = -terms.sum(axis=1) / np.log(3.0)
    feature_values["sign_entropy_240m"] = entropy

    open_ns = _utc_nanoseconds(decisions["nyse_market_open_utc"])
    close_ns = _utc_nanoseconds(decisions["nyse_market_close_utc"])
    minutes_since_open = (decision_ns - open_ns) / pd.Timedelta(minutes=1).value
    minutes_to_safe_close = (
        close_ns - pd.Timedelta(minutes=60).value - decision_ns
    ) / pd.Timedelta(minutes=1).value
    slot = (minutes_since_open - 15.0) / 15.0
    angle = 2.0 * np.pi * slot / float(config.decision_slot_count)
    feature_values["minutes_since_nyse_open"] = minutes_since_open.astype("float64")
    feature_values["minutes_to_horizon_safe_close"] = minutes_to_safe_close.astype("float64")
    feature_values["decision_slot_sin"] = np.sin(angle)
    feature_values["decision_slot_cos"] = np.cos(angle)

    weekdays = decisions["nyse_session_date"].dt.weekday.to_numpy()
    for weekday in range(5):
        feature_values[f"weekday_{weekday}"] = (weekdays == weekday).astype("int8")
    feature_values["early_close_session"] = decisions["early_close_session"].astype(
        "int8"
    ).to_numpy()

    missing_implementation = sorted(set(FEATURE_COLUMNS) - set(feature_values))
    extra_implementation = sorted(set(feature_values) - set(FEATURE_COLUMNS))
    if missing_implementation or extra_implementation:
        raise FeatureBuildError(
            f"Feature registry/implementation mismatch; missing={missing_implementation}, "
            f"extra={extra_implementation}"
        )

    feature_frame = pd.DataFrame(
        {name: feature_values[name] for name in FEATURE_COLUMNS}, index=decisions.index
    )
    feature_frame[[f"weekday_{day}" for day in range(5)] + ["early_close_session"]] = (
        feature_frame[
            [f"weekday_{day}" for day in range(5)] + ["early_close_session"]
        ].astype("int8")
    )

    finite = np.isfinite(feature_frame.astype("float64").to_numpy()).all(axis=1)
    full_presence = present.all(axis=1)
    full_complete = (
        present
        & complete_flag
        & (active == float(config.required_active_1m_count))
    ).all(axis=1)
    full_same_instrument = same_instrument.all(axis=1)
    any_roll = crosses_roll.any(axis=1)
    zero_volume_denominator = (
        (valid[:, 12:17].all(axis=1) & (np.mean(volumes[:, 12:16], axis=1) <= 0.0))
        | (valid.all(axis=1) & (np.mean(volumes[:, :16], axis=1) <= 0.0))
    )
    zero_bar_range = current_valid & (denominator <= 0.0)
    zero_variance = full_return_window & (correlation_denominator <= 0.0)
    vwap_problem = ~vwap_valid

    statuses: list[str] = []
    for row in range(len(decisions)):
        reasons: list[str] = []
        if not full_presence[row]:
            reasons.append("MISSING_LOOKBACK_BAR")
        if full_presence[row] and not full_complete[row]:
            reasons.append("PARTIAL_LOOKBACK_BAR")
        if any_roll[row] or (full_presence[row] and not full_same_instrument[row]):
            reasons.append("ROLL_OR_INSTRUMENT_CHANGE")
        if zero_volume_denominator[row]:
            reasons.append("ZERO_VOLUME_DENOMINATOR")
        if zero_bar_range[row]:
            reasons.append("ZERO_BAR_RANGE")
        if zero_variance[row]:
            reasons.append("ZERO_VARIANCE_AUTOCORR")
        if vwap_problem[row]:
            reasons.append("SESSION_VWAP_INPUT_INVALID")
        if not finite[row] and not reasons:
            reasons.append("UNDECLARED_MISSING")
        statuses.append("PASS" if not reasons else "|".join(reasons))

    undeclared = sum("UNDECLARED_MISSING" in status for status in statuses)
    if undeclared:
        raise FeatureBuildError(f"{undeclared} rows contain unexplained missing features")

    output = decisions.loc[
        :,
        [
            "decision_id",
            "decision_time",
            "nyse_session_date",
            "instrument_id",
            "outer_partition",
            "role_wf_2022",
            "role_wf_2023",
            "role_wf_2024",
        ],
    ].copy()
    output["feature_row_usable"] = finite.astype(bool)
    output["feature_status"] = statuses
    fixed_window_start = output["decision_time"] - pd.Timedelta(
        minutes=config.maximum_lookback_bars * config.bar_minutes
    )
    session_source_start = decisions["nyse_market_open_utc"]
    output["feature_lookback_start_utc"] = pd.concat(
        [fixed_window_start, session_source_start], axis=1
    ).min(axis=1)
    output["feature_max_source_time_utc"] = output["decision_time"]
    output = pd.concat([output, feature_frame], axis=1)
    output = output.loc[:, list(METADATA_COLUMNS) + list(FEATURE_COLUMNS)]

    if output["feature_max_source_time_utc"].gt(output["decision_time"]).any():
        raise FeatureBuildError("A feature consumed information after decision_time")
    assert_no_final_test_rows(output, final_test_start_year=config.final_test_start_year)
    assert_target_columns_absent(output, FORBIDDEN_TARGET_TOKENS)

    missing_records: list[dict[str, object]] = []
    feature_matrix = output.loc[:, FEATURE_COLUMNS].astype("float64")
    for row_index, decision_id in enumerate(output["decision_id"]):
        missing_names = feature_matrix.columns[~np.isfinite(feature_matrix.iloc[row_index])]
        if len(missing_names) == 0:
            continue
        row_reasons = statuses[row_index].split("|")
        for feature_name in missing_names:
            if feature_name == "session_vwap_proxy_deviation":
                reason = "SESSION_VWAP_INPUT_INVALID"
            elif feature_name == "return_autocorr_lag1_240m" and zero_variance[row_index]:
                reason = "ZERO_VARIANCE_AUTOCORR"
            elif feature_name == "bar_close_location" and zero_bar_range[row_index]:
                reason = "ZERO_BAR_RANGE"
            elif feature_name.startswith("volume_ratio_") and zero_volume_denominator[row_index]:
                reason = "ZERO_VOLUME_DENOMINATOR"
            else:
                reason = next(
                    (
                        candidate
                        for candidate in row_reasons
                        if candidate
                        in {
                            "MISSING_LOOKBACK_BAR",
                            "PARTIAL_LOOKBACK_BAR",
                            "ROLL_OR_INSTRUMENT_CHANGE",
                        }
                    ),
                    "NONFINITE_OR_DOMAIN_INPUT",
                )
            missing_records.append(
                {
                    "decision_id": decision_id,
                    "feature_name": feature_name,
                    "missing_reason": reason,
                }
            )
    missingness_ledger = pd.DataFrame.from_records(
        missing_records,
        columns=["decision_id", "feature_name", "missing_reason"],
    )
    expected_missing = int((~np.isfinite(feature_matrix.to_numpy())).sum())
    if len(missingness_ledger) != expected_missing:
        raise FeatureBuildError("Every missing feature must have exactly one ledger record")
    if not missingness_ledger.empty and missingness_ledger.duplicated(
        ["decision_id", "feature_name"]
    ).any():
        raise FeatureBuildError("Duplicate feature missingness ledger record")
    usable_from_status = np.asarray([status == "PASS" for status in statuses], dtype=bool)
    if not np.array_equal(output["feature_row_usable"].to_numpy(), usable_from_status):
        raise FeatureBuildError("feature_row_usable and feature_status disagree")

    market_rows_after_max = int(
        market["decision_time"].gt(decisions["decision_time"].max()).sum()
    )
    observed_vwap_slots = (
        (
            _utc_nanoseconds(decisions["decision_time"])
            - _utc_nanoseconds(decisions["nyse_market_open_utc"])
        )
        // pd.Timedelta(minutes=config.bar_minutes).value
    )
    if int(observed_vwap_slots.max()) > config.session_vwap_max_bars:
        raise FeatureBuildError("Session VWAP lookback exceeds the locked V1 maximum")
    diagnostics = {
        "policy_version": config.policy_version,
        "development_rows": len(output),
        "feature_columns": len(FEATURE_COLUMNS),
        "feature_usable_rows": int(output["feature_row_usable"].sum()),
        "feature_unusable_rows": int((~output["feature_row_usable"]).sum()),
        "final_test_feature_rows": 0,
        "market_rows_after_development_max_returned": market_rows_after_max,
        "session_vwap_max_bars_observed": int(observed_vwap_slots.max()),
        "missing_feature_values": expected_missing,
        "missingness_ledger_rows": len(missingness_ledger),
        "maximum_source_time_lte_decision_time": True,
        "status_counts": output["feature_status"].value_counts(dropna=False).to_dict(),
    }
    return FeatureBuildResult(
        features=output,
        missingness_ledger=missingness_ledger,
        diagnostics=diagnostics,
    )

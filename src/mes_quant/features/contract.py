from __future__ import annotations

from dataclasses import asdict, dataclass

POLICY_VERSION = "MES_V1_FEATURES_1.0"

FORBIDDEN_TARGET_TOKENS = (
    "label",
    "target",
    "future",
    "mfe",
    "mae",
    "path_",
    "pnl",
    "profit",
    "baseline",
    "economic_",
    "cost_",
    "barrier",
    "gross_move",
    "gross_return",
    "net_return",
    "exit_reference",
    "outcome",
    "forward_return",
    "return_60m",
    "next_return",
    "trade_return",
    "realized_pnl",
)

METADATA_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "role_wf_2024",
    "feature_row_usable",
    "feature_status",
    "feature_lookback_start_utc",
    "feature_max_source_time_utc",
)


@dataclass(frozen=True)
class FeatureSpec:
    feature_name: str
    family: str
    formula_version: str
    formula: str
    source_columns: str
    availability_rule: str
    lookback_mode: str
    lookback_start_rule: str
    lookback_bars: int
    lookback_minutes: int
    includes_current_completed_bar: bool
    exact_grid_required: bool
    same_instrument_required: bool
    missingness_rule: str
    dtype: str = "float64"
    fit_required: bool = False
    model_eligible: bool = True
    partition_scope: str = "TRAIN_VALIDATION_ONLY"


def _spec(
    name: str,
    family: str,
    lookback_bars: int,
    sources: str,
    missingness: str = "MISSING_IF_REQUIRED_WINDOW_INVALID",
    *,
    formula: str = "V1",
    dtype: str = "float64",
    exact_grid: bool = True,
    same_instrument: bool = True,
    formula_text: str = "SEE_POLICY_SOURCE",
    lookback_mode: str = "FIXED",
    lookback_start_rule: str = "DECISION_TIME_MINUS_LOOKBACK",
    includes_current_bar: bool = True,
) -> FeatureSpec:
    return FeatureSpec(
        feature_name=name,
        family=family,
        formula_version=formula,
        formula=formula_text,
        source_columns=sources,
        availability_rule="COMPLETED_BAR_ENDING_AT_OR_BEFORE_DECISION_TIME",
        lookback_mode=lookback_mode,
        lookback_start_rule=lookback_start_rule,
        lookback_bars=lookback_bars,
        lookback_minutes=lookback_bars * 15,
        includes_current_completed_bar=includes_current_bar,
        exact_grid_required=exact_grid,
        same_instrument_required=same_instrument,
        missingness_rule=missingness,
        dtype=dtype,
    )


def feature_specs() -> tuple[FeatureSpec, ...]:
    specs: list[FeatureSpec] = []
    for lag in range(4):
        specs.append(
            _spec(
                f"ret_log_15m_lag{lag}",
                "RETURN",
                lag + 1,
                "close",
                formula_text=f"log(C[t-{lag}*15m]/C[t-{lag + 1}*15m])",
            )
        )
    for minutes, bars in ((60, 4), (120, 8), (240, 16)):
        specs.append(
            _spec(
                f"momentum_log_{minutes}m",
                "MOMENTUM",
                bars,
                "close",
                formula_text=f"log(C[t]/C[t-{minutes}m])",
            )
        )
        specs.append(
            _spec(
                f"realized_vol_{minutes}m",
                "VOLATILITY",
                bars,
                "close",
                formula_text=f"sqrt(sum(last {bars} log_return^2))",
            )
        )
    specs.extend(
        [
            _spec(
                "bar_log_range_15m",
                "BAR_SHAPE",
                0,
                "high,low",
                formula_text="log(H[t]/L[t])",
            ),
            _spec(
                "bar_log_body_15m",
                "BAR_SHAPE",
                0,
                "open,close",
                formula_text="log(C[t]/O[t])",
            ),
            _spec(
                "bar_close_location",
                "BAR_SHAPE",
                0,
                "high,low,close",
                "MISSING_IF_HIGH_EQUALS_LOW_OR_CURRENT_BAR_INVALID",
                formula_text="(C[t]-L[t])/(H[t]-L[t])",
            ),
            _spec(
                "log1p_volume_15m",
                "VOLUME",
                0,
                "volume",
                formula_text="log(1+V[t])",
            ),
            _spec(
                "volume_ratio_prev_60m",
                "VOLUME",
                4,
                "volume",
                "MISSING_IF_PREVIOUS_MEAN_ZERO_OR_WINDOW_INVALID",
                formula_text="V[t]/mean(V[t-15m:t-60m]); current excluded from denominator",
            ),
            _spec(
                "volume_ratio_prev_240m",
                "VOLUME",
                16,
                "volume",
                "MISSING_IF_PREVIOUS_MEAN_ZERO_OR_WINDOW_INVALID",
                formula_text="V[t]/mean(previous 16 volumes); current excluded from denominator",
            ),
            _spec(
                "session_vwap_proxy_deviation",
                "SESSION",
                22,
                "high,low,close,volume,nyse_market_open_utc",
                "MISSING_IF_SESSION_GRID_OR_CUMULATIVE_VOLUME_INVALID",
                formula_text="log(C[t]/(sum(((H+L+C)/3)*V)/sum(V))) from NYSE open through t",
                lookback_mode="SESSION_TO_DATE",
                lookback_start_rule="NYSE_SESSION_OPEN",
            ),
            _spec(
                "return_autocorr_lag1_240m",
                "DYNAMICS",
                16,
                "close",
                "MISSING_IF_ZERO_VARIANCE_OR_WINDOW_INVALID",
                formula_text="PearsonCorr(last16_returns[:-1],last16_returns[1:])",
            ),
            _spec(
                "sign_entropy_240m",
                "DYNAMICS",
                16,
                "close",
                formula_text="-sum(p_neg,p_zero,p_pos * log(p))/log(3) over last16 returns",
            ),
        ]
    )
    for name in (
        "minutes_since_nyse_open",
        "minutes_to_horizon_safe_close",
        "decision_slot_sin",
        "decision_slot_cos",
    ):
        specs.append(
            _spec(
                name,
                "CALENDAR",
                0,
                "decision_time,nyse_market_open_utc,nyse_market_close_utc",
                "MISSING_IF_CALENDAR_METADATA_INVALID",
                exact_grid=False,
                same_instrument=False,
                formula_text="Deterministic NYSE calendar transform at decision_time",
                includes_current_bar=False,
            )
        )
    for weekday in range(5):
        specs.append(
            _spec(
                f"weekday_{weekday}",
                "CALENDAR",
                0,
                "nyse_session_date",
                "NEVER_MISSING_AFTER_SESSION_DATE_VALIDATION",
                dtype="int8",
                exact_grid=False,
                same_instrument=False,
                formula_text=f"1[NYSE session weekday == {weekday}]",
                includes_current_bar=False,
            )
        )
    specs.append(
        _spec(
            "early_close_session",
            "CALENDAR",
            0,
            "early_close_session",
            "NEVER_MISSING_AFTER_CALENDAR_VALIDATION",
            dtype="int8",
            exact_grid=False,
            same_instrument=False,
            formula_text="1[NYSE session has an early close]",
            includes_current_bar=False,
        )
    )
    return tuple(specs)


FEATURE_COLUMNS = tuple(spec.feature_name for spec in feature_specs())


def registry_records(source_artifact_sha256: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for spec in feature_specs():
        record = asdict(spec)
        record["source_artifact"] = "CELL5_15M+C7_UNIVERSE+C8_ASSIGNMENTS"
        record["source_hashes"] = source_artifact_sha256
        records.append(record)
    return records

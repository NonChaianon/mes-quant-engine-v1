# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 5 — 1m → 15m RESAMPLE + DATA INTEGRITY AUDIT
# ============================================================
#
# PURPOSE
# -------
# 1) Resample canonical MES 1-minute data → 15-minute bars
# 2) Never forward-fill or create synthetic price bars
# 3) Count actual 1-minute observations inside every 15m bar
# 4) Preserve / restore instrument_id dtype
# 5) Detect mixed-contract (roll-crossing) 15m bars
# 6) Build a first data-integrity gate for V1 decision times
# 7) Audit partial bars inside 09:45–15:00 New York
# 8) Attach Databento dataset-condition flags
# 9) Compare degraded dates with actual MES observations
# 10) Audit early MES liquidity without choosing a cutoff yet
# 11) Cross-check clean 15m OHLCV against old audited parquet
#
# IMPORTANT
# ---------
# - This cell does NOT create features.
# - This cell does NOT create labels.
# - This cell does NOT remove degraded days automatically.
# - This cell does NOT choose a warm-up cutoff.
# - Raw-gap attribution belongs to CELL 6.
# ============================================================


# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone

import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 2) Project paths
# ------------------------------------------------------------

PROJECT_DIR = Path(
    "/content/drive/MyDrive/Quant_Lab"
)

DATA_DIR = (
    PROJECT_DIR
    / "Data"
)

CLEAN_DIR = (
    DATA_DIR
    / "MES_Clean_Pipeline_V1"
)


# ------------------------------------------------------------
# 3) Upstream audit / registry paths
# ------------------------------------------------------------

BASELINE_PATH = (
    CLEAN_DIR
    / "raw_source_baseline.json"
)

CELL3_AUDIT_PATH = (
    CLEAN_DIR
    / "cell3_supplemental_raw_audit.json"
)

CELL4_AUDIT_PATH = (
    CLEAN_DIR
    / "cell4_dataset_condition_audit.json"
)

CONDITION_PATH = (
    CLEAN_DIR
    / "databento_glbx_mdp3_condition_registry.csv"
)


# ------------------------------------------------------------
# 4) Old research artifact
#
# Optional.
# Used only for semantic cross-check.
# It is NOT the source of truth.
# ------------------------------------------------------------

OLD_15M_PATH = (
    DATA_DIR
    / "MES_2019_2026_15m.parquet"
)


# ------------------------------------------------------------
# 5) CELL 5 output artifacts
# ------------------------------------------------------------

MES_15M_PATH = (
    CLEAN_DIR
    / "MES_2019_2026_15m_clean.parquet"
)

CELL5_AUDIT_PATH = (
    CLEAN_DIR
    / "cell5_15m_resample_audit.json"
)

V1_PARTIAL_PATH = (
    CLEAN_DIR
    / "cell5_v1_clock_partial_bars.parquet"
)

DEGRADED_IMPACT_PATH = (
    CLEAN_DIR
    / "cell5_degraded_day_mes_impact.csv"
)

LAUNCH_LIQUIDITY_PATH = (
    CLEAN_DIR
    / "cell5_launch_liquidity_monthly.csv"
)


# ------------------------------------------------------------
# 6) Policy constants
# ------------------------------------------------------------

NY_TZ = "America/New_York"

RESAMPLE_RULE = "15min"

# V1 clock-only decision window
#
# IMPORTANT:
# Calendar / holidays / early closes are NOT applied here.
# Those belong to the next decision-universe layer.
#
# Decision time:
# 09:45 → 15:00 New York

V1_START_MINUTE = (
    9 * 60
    + 45
)

V1_END_MINUTE = (
    15 * 60
)


# ------------------------------------------------------------
# 7) Upstream artifact gates
# ------------------------------------------------------------

required_artifacts = [
    BASELINE_PATH,
    CELL3_AUDIT_PATH,
    CELL4_AUDIT_PATH,
    CONDITION_PATH,
]


for path in required_artifacts:

    if not path.exists():

        raise RuntimeError(
            "CELL 5 STOPPED — missing upstream artifact:\n"
            f"{path}\n\n"
            "Run CELL 0 → CELL 4 first."
        )


# ------------------------------------------------------------
# 8) mes_1m runtime gate
#
# mes_1m must come from canonical DBN decode in CELL 2.
# ------------------------------------------------------------

if "mes_1m" not in globals():

    raise RuntimeError(
        "CELL 5 STOPPED — mes_1m is not in memory.\n\n"
        "Run CELL 0 → CELL 4 first."
    )


if not isinstance(
    mes_1m,
    pd.DataFrame,
):

    raise RuntimeError(
        "CELL 5 STOPPED — mes_1m is not a pandas DataFrame."
    )


if not isinstance(
    mes_1m.index,
    pd.DatetimeIndex,
):

    raise RuntimeError(
        "CELL 5 STOPPED — mes_1m index is not DatetimeIndex."
    )


# ------------------------------------------------------------
# 9) Required raw columns
# ------------------------------------------------------------

REQUIRED_RAW_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "instrument_id",
]


missing_raw_columns = [
    col
    for col in REQUIRED_RAW_COLUMNS
    if col not in mes_1m.columns
]


if missing_raw_columns:

    raise RuntimeError(
        "CELL 5 STOPPED — missing raw columns:\n"
        + ", ".join(
            missing_raw_columns
        )
    )


# ------------------------------------------------------------
# 10) Raw timestamp integrity
# ------------------------------------------------------------

if not mes_1m.index.is_monotonic_increasing:

    raise RuntimeError(
        "CELL 5 STOPPED — raw timestamps are not monotonic."
    )


raw_duplicate_timestamps = int(
    mes_1m.index
    .duplicated()
    .sum()
)


if raw_duplicate_timestamps != 0:

    raise RuntimeError(
        "CELL 5 STOPPED — raw duplicate timestamps found: "
        f"{raw_duplicate_timestamps:,}"
    )


if mes_1m.index.tz is None:

    raise RuntimeError(
        "CELL 5 STOPPED — raw index has no timezone."
    )


if str(
    mes_1m.index.tz
).upper() != "UTC":

    raise RuntimeError(
        "CELL 5 STOPPED — raw timezone is not UTC."
    )


# ------------------------------------------------------------
# 11) Load CELL 4 audit
# ------------------------------------------------------------

with open(
    CELL4_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    cell4_audit = json.load(f)


if (
    cell4_audit.get(
        "registry_status"
    )
    != "AVAILABLE"
):

    raise RuntimeError(
        "CELL 5 STOPPED — Databento condition registry "
        "is not AVAILABLE."
    )


# ------------------------------------------------------------
# 12) Load Databento condition registry
# ------------------------------------------------------------

condition_df = pd.read_csv(
    CONDITION_PATH
)


required_condition_columns = {
    "date",
    "condition",
    "last_modified_date",
}


if not required_condition_columns.issubset(
    condition_df.columns
):

    raise RuntimeError(
        "CELL 5 STOPPED — condition registry columns incomplete."
    )


condition_df[
    "date"
] = (
    pd.to_datetime(
        condition_df[
            "date"
        ],
        utc=True,
    )
    .dt
    .floor(
        "D"
    )
)


condition_df[
    "condition"
] = (
    condition_df[
        "condition"
    ]
    .astype(str)
    .str
    .lower()
    .str
    .strip()
)


if condition_df[
    "date"
].duplicated().any():

    raise RuntimeError(
        "CELL 5 STOPPED — duplicate condition dates found."
    )


condition_map = (
    condition_df
    .set_index(
        "date"
    )[
        "condition"
    ]
)


# ------------------------------------------------------------
# 13) Resample OHLCV: 1m → 15m
#
# Databento ts_event represents bar START.
#
# Therefore:
#
# index 22:00 represents:
# [22:00, 22:15)
#
# decision_time becomes:
# 22:15
#
# No forward-fill.
# ------------------------------------------------------------

print(
    "CELL 5 — Resampling canonical MES 1m → 15m..."
)


ohlcv_15m = (

    mes_1m[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ]

    .resample(
        RESAMPLE_RULE,
        label="left",
        closed="left",
    )

    .agg(
        {
            "open":
                "first",

            "high":
                "max",

            "low":
                "min",

            "close":
                "last",

            "volume":
                "sum",
        }
    )
)


# ------------------------------------------------------------
# 14) Count actual raw 1m bars
#
# active_1m_count:
#
# 15 = complete 15-minute interval
#
# <15 = at least one expected minute does not have an
#       OHLCV trade record
#
# IMPORTANT:
# This does NOT by itself tell us WHY the minute is absent.
# ------------------------------------------------------------

active_1m_count = (

    mes_1m[
        "close"
    ]

    .resample(
        RESAMPLE_RULE,
        label="left",
        closed="left",
    )

    .count()
)


# ------------------------------------------------------------
# 15) Instrument aggregation
# ------------------------------------------------------------

instrument_first = (

    mes_1m[
        "instrument_id"
    ]

    .resample(
        RESAMPLE_RULE,
        label="left",
        closed="left",
    )

    .first()
)


instrument_count = (

    mes_1m[
        "instrument_id"
    ]

    .resample(
        RESAMPLE_RULE,
        label="left",
        closed="left",
    )

    .nunique()
)


# ------------------------------------------------------------
# 16) Assemble initial 15m dataframe
# ------------------------------------------------------------

mes_15m = (
    ohlcv_15m
    .copy()
)


mes_15m[
    "active_1m_count"
] = (
    active_1m_count
)


mes_15m[
    "instrument_id"
] = (
    instrument_first
)


mes_15m[
    "instrument_count"
] = (
    instrument_count
)


# ------------------------------------------------------------
# 17) Empty-bin audit
#
# Pandas resample creates clock bins even when there are
# no raw OHLCV observations.
#
# We count those BEFORE removing them.
# ------------------------------------------------------------

bins_before_drop = int(
    len(
        mes_15m
    )
)


empty_bin_mask = (
    mes_15m[
        "active_1m_count"
    ]
    .eq(
        0
    )
)


empty_bins = int(
    empty_bin_mask.sum()
)


# ------------------------------------------------------------
# 18) Remove truly empty bins
#
# We do NOT synthesize a price.
# ------------------------------------------------------------

mes_15m = (

    mes_15m.loc[
        ~empty_bin_mask
    ]

    .copy()
)


# ------------------------------------------------------------
# 19) Validate counts BEFORE dtype conversion
# ------------------------------------------------------------

if mes_15m[
    "instrument_id"
].isna().any():

    raise RuntimeError(
        "CELL 5 STOPPED — instrument_id contains NaN "
        "after empty-bin removal."
    )


if (
    mes_15m[
        "active_1m_count"
    ]
    .lt(
        1
    )
    .any()
):

    raise RuntimeError(
        "CELL 5 STOPPED — active_1m_count < 1 detected."
    )


if (
    mes_15m[
        "active_1m_count"
    ]
    .gt(
        15
    )
    .any()
):

    raise RuntimeError(
        "CELL 5 STOPPED — active_1m_count > 15 detected."
    )


# ------------------------------------------------------------
# 20) Restore semantic dtypes
#
# Why:
#
# Temporary empty bins can force Pandas to convert
# instrument_id:
#
# uint32 → float64
#
# Example:
#
# 7849 → 7849.0
#
# After empty bins are removed and NaN == 0,
# restore the original raw dtype.
# ------------------------------------------------------------

RAW_INSTRUMENT_DTYPE = (
    mes_1m[
        "instrument_id"
    ].dtype
)


mes_15m[
    "instrument_id"
] = (
    mes_15m[
        "instrument_id"
    ]
    .astype(
        RAW_INSTRUMENT_DTYPE
    )
)


mes_15m[
    "active_1m_count"
] = (
    mes_15m[
        "active_1m_count"
    ]
    .astype(
        "uint8"
    )
)


mes_15m[
    "instrument_count"
] = (
    mes_15m[
        "instrument_count"
    ]
    .astype(
        "uint8"
    )
)


# ------------------------------------------------------------
# 21) Roll-crossing flag
#
# True means one 15m bar contains >1 contract.
# ------------------------------------------------------------

mes_15m[
    "crosses_roll"
] = (
    mes_15m[
        "instrument_count"
    ]
    .gt(
        1
    )
)


# ------------------------------------------------------------
# 22) Decision time
#
# Index = bar start
# decision_time = bar end
# ------------------------------------------------------------

mes_15m[
    "decision_time"
] = (
    mes_15m.index
    +
    pd.Timedelta(
        minutes=15
    )
)


# ------------------------------------------------------------
# 23) New York decision time
#
# IMPORTANT:
# Series values require .dt.tz_convert(...)
# ------------------------------------------------------------

mes_15m[
    "decision_time_ny"
] = (
    mes_15m[
        "decision_time"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)


# ------------------------------------------------------------
# 24) Bar completeness
#
# Full bar:
# all 15 one-minute trade-bars exist
# ------------------------------------------------------------

mes_15m[
    "bar_complete_15m"
] = (
    mes_15m[
        "active_1m_count"
    ]
    .eq(
        15
    )
)


# ------------------------------------------------------------
# 25) First data-integrity policy
#
# A bar is structurally clean if:
#
# - complete 15/15
# - not mixed across futures contracts
# ------------------------------------------------------------

mes_15m[
    "data_integrity_ok"
] = (

    mes_15m[
        "bar_complete_15m"
    ]

    &

    ~mes_15m[
        "crosses_roll"
    ]
)


# ------------------------------------------------------------
# 26) V1 clock-only window
#
# This is NOT yet the final Decision Universe.
#
# NYSE calendar / holidays / early close comes later.
# ------------------------------------------------------------

decision_minute_ny = (

    mes_15m[
        "decision_time_ny"
    ]
    .dt.hour
    *
    60

    +

    mes_15m[
        "decision_time_ny"
    ]
    .dt.minute
)


mes_15m[
    "v1_clock_window"
] = (

    decision_minute_ny
    .between(
        V1_START_MINUTE,
        V1_END_MINUTE,
        inclusive="both",
    )
)


# ------------------------------------------------------------
# 27) Partial bars inside V1 clock window
# ------------------------------------------------------------

mes_15m[
    "v1_clock_partial"
] = (

    mes_15m[
        "v1_clock_window"
    ]

    &

    ~mes_15m[
        "bar_complete_15m"
    ]
)


# ------------------------------------------------------------
# 28) Integrity eligibility
#
# IMPORTANT POLICY:
#
# Partial bars remain in dataset as market context,
# but cannot become an ENTRY decision observation.
# ------------------------------------------------------------

mes_15m[
    "v1_clock_integrity_eligible"
] = (

    mes_15m[
        "v1_clock_window"
    ]

    &

    mes_15m[
        "data_integrity_ok"
    ]
)


# ------------------------------------------------------------
# 29) Attach Databento dataset-condition flag
#
# Registry date is interpreted in UTC.
#
# degraded is NOT automatic exclusion.
# ------------------------------------------------------------

bar_utc_day = pd.Series(
    mes_15m.index.floor(
        "D"
    ),
    index=mes_15m.index,
)


mes_15m[
    "dataset_condition_utc"
] = (
    bar_utc_day
    .map(
        condition_map
    )
)


missing_condition_count = int(
    mes_15m[
        "dataset_condition_utc"
    ]
    .isna()
    .sum()
)


if missing_condition_count != 0:

    raise RuntimeError(
        "CELL 5 STOPPED — missing Databento condition "
        f"for {missing_condition_count:,} 15m bars."
    )


mes_15m[
    "dataset_degraded_utc"
] = (
    mes_15m[
        "dataset_condition_utc"
    ]
    .eq(
        "degraded"
    )
)


# ------------------------------------------------------------
# 30) Structural audit
# ------------------------------------------------------------

failures = []


if not mes_15m.index.is_monotonic_increasing:

    failures.append(
        "15m index is not monotonic"
    )


duplicate_15m = int(
    mes_15m.index
    .duplicated()
    .sum()
)


if duplicate_15m != 0:

    failures.append(
        f"15m duplicate timestamps: {duplicate_15m}"
    )


# ------------------------------------------------------------
# 31) OHLCV NaN audit
# ------------------------------------------------------------

OHLCV_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]


ohlcv_nan_counts = {

    col:
        int(
            mes_15m[
                col
            ]
            .isna()
            .sum()
        )

    for col in OHLCV_COLUMNS
}


if sum(
    ohlcv_nan_counts.values()
) != 0:

    failures.append(
        "15m OHLCV contains NaN: "
        f"{ohlcv_nan_counts}"
    )


# ------------------------------------------------------------
# 32) OHLC consistency audit
# ------------------------------------------------------------

high_violation = int(
    (
        mes_15m[
            "high"
        ]
        <
        mes_15m[
            [
                "open",
                "close",
                "low",
            ]
        ]
        .max(
            axis=1
        )
    )
    .sum()
)


low_violation = int(
    (
        mes_15m[
            "low"
        ]
        >
        mes_15m[
            [
                "open",
                "close",
                "high",
            ]
        ]
        .min(
            axis=1
        )
    )
    .sum()
)


if high_violation != 0:

    failures.append(
        f"15m high violations: {high_violation}"
    )


if low_violation != 0:

    failures.append(
        f"15m low violations: {low_violation}"
    )


# ------------------------------------------------------------
# 33) Roll audit
#
# For this dataset we expect zero mixed-contract bars.
# ------------------------------------------------------------

roll_crossing_bars = int(
    mes_15m[
        "crosses_roll"
    ]
    .sum()
)


max_instruments_per_bar = int(
    mes_15m[
        "instrument_count"
    ]
    .max()
)


if roll_crossing_bars != 0:

    failures.append(
        "Mixed-contract 15m bars detected: "
        f"{roll_crossing_bars}"
    )


# ------------------------------------------------------------
# 34) instrument_id dtype hard gate
# ------------------------------------------------------------

clean_instrument_dtype = (
    mes_15m[
        "instrument_id"
    ].dtype
)


instrument_dtype_match = (
    clean_instrument_dtype
    ==
    RAW_INSTRUMENT_DTYPE
)


if not instrument_dtype_match:

    failures.append(
        "instrument_id dtype mismatch: "
        f"{clean_instrument_dtype} "
        f"!= {RAW_INSTRUMENT_DTYPE}"
    )


# ------------------------------------------------------------
# 35) Completeness statistics
# ------------------------------------------------------------

full_15m_bars = int(
    mes_15m[
        "bar_complete_15m"
    ]
    .sum()
)


partial_15m_bars = int(
    (
        ~mes_15m[
            "bar_complete_15m"
        ]
    )
    .sum()
)


active_count_distribution = (

    mes_15m[
        "active_1m_count"
    ]

    .value_counts()

    .sort_index()
)


# ------------------------------------------------------------
# 36) V1 clock integrity statistics
# ------------------------------------------------------------

v1_clock_bars = int(
    mes_15m[
        "v1_clock_window"
    ]
    .sum()
)


v1_partial_bars = int(
    mes_15m[
        "v1_clock_partial"
    ]
    .sum()
)


v1_integrity_eligible_bars = int(
    mes_15m[
        "v1_clock_integrity_eligible"
    ]
    .sum()
)


# ------------------------------------------------------------
# 37) Save V1 partial-bar examples
# ------------------------------------------------------------

partial_v1 = (

    mes_15m.loc[
        mes_15m[
            "v1_clock_partial"
        ],
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "active_1m_count",
            "instrument_id",
            "instrument_count",
            "crosses_roll",
            "dataset_condition_utc",
            "dataset_degraded_utc",
            "decision_time",
            "decision_time_ny",
        ],
    ]

    .copy()
)


partial_v1.to_parquet(
    V1_PARTIAL_PATH,
    index=True,
)


# ------------------------------------------------------------
# 38) Old 15m semantic cross-check
#
# IMPORTANT:
#
# Same row count alone is NOT enough.
#
# Compare:
# - row count
# - timestamps
# - open
# - high
# - low
# - close
# - volume
#
# observation-by-observation
# ------------------------------------------------------------

old_15m_check = {
    "status":
        "SKIPPED",

    "reason":
        "Old 15m parquet not found",
}


if OLD_15M_PATH.exists():

    old_15m = pd.read_parquet(
        OLD_15M_PATH
    )


    rows_equal = (
        len(
            old_15m
        )
        ==
        len(
            mes_15m
        )
    )


    index_equal = (

        isinstance(
            old_15m.index,
            pd.DatetimeIndex,
        )

        and

        rows_equal

        and

        old_15m.index.equals(
            mes_15m.index
        )
    )


    column_results = {}


    for col in OHLCV_COLUMNS:

        if col not in old_15m.columns:

            values_equal = False

        else:

            values_equal = (
                old_15m[
                    col
                ]
                .equals(
                    mes_15m[
                        col
                    ]
                )
            )


        column_results[
            col
        ] = {
            "values_equal":
                bool(
                    values_equal
                )
        }


    all_ohlcv_equal = all(

        result[
            "values_equal"
        ]

        for result
        in column_results.values()
    )


    old_15m_pass = (

        rows_equal
        and
        index_equal
        and
        all_ohlcv_equal
    )


    old_15m_check = {

        "status":
            (
                "PASS"
                if old_15m_pass
                else "FAIL"
            ),

        "rows_equal":
            bool(
                rows_equal
            ),

        "index_equal":
            bool(
                index_equal
            ),

        "columns":
            column_results,
    }


    if not old_15m_pass:

        failures.append(
            "Old 15m ↔ clean 15m semantic cross-check failed"
        )


    del old_15m


# ------------------------------------------------------------
# 39) MES daily raw statistics
#
# Used only to investigate Databento degraded dates.
# ------------------------------------------------------------

raw_daily = (

    mes_1m[
        [
            "close",
            "volume",
        ]
    ]

    .resample(
        "1D"
    )

    .agg(
        raw_1m_bars=(
            "close",
            "count",
        ),

        raw_volume=(
            "volume",
            "sum",
        ),
    )
)


# ------------------------------------------------------------
# 40) MES daily 15m statistics
# ------------------------------------------------------------

daily15 = pd.DataFrame(
    index=(
        mes_15m[
            "close"
        ]
        .resample(
            "1D"
        )
        .count()
        .index
    )
)


daily15[
    "bars_15m"
] = (
    mes_15m[
        "close"
    ]
    .resample(
        "1D"
    )
    .count()
)


daily15[
    "partial_15m_bars"
] = (
    (
        ~mes_15m[
            "bar_complete_15m"
        ]
    )
    .resample(
        "1D"
    )
    .sum()
)


daily15[
    "v1_clock_bars"
] = (
    mes_15m[
        "v1_clock_window"
    ]
    .resample(
        "1D"
    )
    .sum()
)


daily15[
    "v1_clock_partial_bars"
] = (
    mes_15m[
        "v1_clock_partial"
    ]
    .resample(
        "1D"
    )
    .sum()
)


# ------------------------------------------------------------
# 41) Databento degraded dates ↔ actual MES observations
#
# NOTE:
#
# Databento condition is dataset-level.
#
# We therefore do NOT assume degraded means MES is defective.
# ------------------------------------------------------------

degraded_condition_rows = (

    condition_df.loc[
        condition_df[
            "condition"
        ]
        .eq(
            "degraded"
        ),
        [
            "date",
            "condition",
            "last_modified_date",
        ],
    ]

    .copy()
)


degraded_days = (

    degraded_condition_rows

    .set_index(
        "date"
    )

    .join(
        raw_daily.join(
            daily15,
            how="outer",
        ),
        how="left",
    )

    .fillna(
        {
            "raw_1m_bars":
                0,

            "raw_volume":
                0,

            "bars_15m":
                0,

            "partial_15m_bars":
                0,

            "v1_clock_bars":
                0,

            "v1_clock_partial_bars":
                0,
        }
    )

    .reset_index()
)


degraded_days.to_csv(
    DEGRADED_IMPACT_PATH,
    index=False,
)


# ------------------------------------------------------------
# 42) Early MES liquidity diagnostic
#
# Diagnostic only.
#
# We do NOT decide:
# "remove first month"
# or
# "use ES instead"
#
# until the actual statistics are reviewed.
# ------------------------------------------------------------

liquidity_df = (
    mes_15m.copy()
)


liquidity_df[
    "ny_month"
] = (

    liquidity_df[
        "decision_time_ny"
    ]

    .dt
    .tz_localize(
        None
    )

    .dt
    .to_period(
        "M"
    )

    .astype(
        str
    )
)


liquidity_df[
    "range_points"
] = (
    liquidity_df[
        "high"
    ]
    -
    liquidity_df[
        "low"
    ]
)


# ------------------------------------------------------------
# 43) Monthly all-session liquidity statistics
# ------------------------------------------------------------

monthly_all = (

    liquidity_df

    .groupby(
        "ny_month"
    )

    .agg(
        all_bars=(
            "close",
            "size",
        ),

        all_median_volume=(
            "volume",
            "median",
        ),

        all_median_range_points=(
            "range_points",
            "median",
        ),
    )
)


# ------------------------------------------------------------
# 44) Monthly V1-clock liquidity statistics
# ------------------------------------------------------------

monthly_v1 = (

    liquidity_df.loc[
        liquidity_df[
            "v1_clock_window"
        ]
    ]

    .groupby(
        "ny_month"
    )

    .agg(
        v1_bars=(
            "close",
            "size",
        ),

        v1_partial_bars=(
            "v1_clock_partial",
            "sum",
        ),

        v1_median_volume=(
            "volume",
            "median",
        ),

        v1_p10_volume=(
            "volume",
            lambda s: float(
                s.quantile(
                    0.10
                )
            ),
        ),

        v1_median_range_points=(
            "range_points",
            "median",
        ),
    )
)


# ------------------------------------------------------------
# 45) Combine monthly liquidity audit
# ------------------------------------------------------------

launch_monthly = (
    monthly_all
    .join(
        monthly_v1,
        how="outer",
    )
)


launch_monthly[
    "v1_partial_pct"
] = (
    launch_monthly[
        "v1_partial_bars"
    ]
    /
    launch_monthly[
        "v1_bars"
    ]
    *
    100.0
)


launch_monthly.to_csv(
    LAUNCH_LIQUIDITY_PATH,
    index=True,
)


# ------------------------------------------------------------
# 46) Build CELL 5 audit artifact
# ------------------------------------------------------------

cell5_audit = {

    "audit_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),


    "resample": {

        "raw_rows":
            int(
                len(
                    mes_1m
                )
            ),

        "bins_before_drop":
            bins_before_drop,

        "empty_bins_dropped":
            empty_bins,

        "final_15m_bars":
            int(
                len(
                    mes_15m
                )
            ),

        "full_15m_bars":
            full_15m_bars,

        "partial_15m_bars":
            partial_15m_bars,

        "roll_crossing_bars":
            roll_crossing_bars,

        "maximum_instruments_per_bar":
            max_instruments_per_bar,

        "raw_instrument_dtype":
            str(
                RAW_INSTRUMENT_DTYPE
            ),

        "clean_instrument_dtype":
            str(
                clean_instrument_dtype
            ),

        "instrument_dtype_match":
            bool(
                instrument_dtype_match
            ),

        "active_1m_count_distribution": {

            str(
                int(k)
            ):
                int(v)

            for k, v
            in active_count_distribution.items()
        },
    },


    "v1_clock_integrity": {

        "definition":
            "decision_time_ny 09:45–15:00 before NYSE calendar",

        "clock_bars":
            v1_clock_bars,

        "partial_bars":
            v1_partial_bars,

        "integrity_eligible_bars":
            v1_integrity_eligible_bars,

        "policy":
            (
                "Partial bars are retained as context "
                "but are not decision-eligible."
            ),
    },


    "dataset_condition_impact": {

        "degraded_dates":
            int(
                len(
                    degraded_days
                )
            ),

        "automatic_exclusion":
            False,

        "table":
            str(
                DEGRADED_IMPACT_PATH
            ),
    },


    "launch_liquidity": {

        "automatic_warmup_cut":
            False,

        "table":
            str(
                LAUNCH_LIQUIDITY_PATH
            ),
    },


    "old_15m_cross_check":
        old_15m_check,


    "failures":
        failures,
}


# ------------------------------------------------------------
# 47) Save audit BEFORE hard gate
#
# Even a failure leaves forensic evidence.
# ------------------------------------------------------------

with open(
    CELL5_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        cell5_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 48) Hard gate
# ------------------------------------------------------------

if failures:

    print(
        "\nCELL 5 FAILURES"
    )

    print(
        "-" * 72
    )


    for failure in failures:

        print(
            " -",
            failure
        )


    raise RuntimeError(
        "\nCELL 5 15m INTEGRITY AUDIT: FAIL\n\n"
        "Audit artifact saved at:\n"
        f"{CELL5_AUDIT_PATH}"
    )


# ------------------------------------------------------------
# 49) Save clean 15m dataset
#
# Only after all structural hard gates pass.
# ------------------------------------------------------------

mes_15m.to_parquet(
    MES_15M_PATH,
    index=True,
)


# ------------------------------------------------------------
# 50) Compact output
#
# Deliberately avoid huge output dumps.
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "CELL 5 — 15m RESAMPLE + DATA INTEGRITY AUDIT"
)

print(
    "=" * 72
)


print(
    "\n[1] RESAMPLE"
)

print(
    "Raw 1m rows             :",
    f"{len(mes_1m):,}"
)

print(
    "15m bins before drop    :",
    f"{bins_before_drop:,}"
)

print(
    "Empty bins dropped      :",
    f"{empty_bins:,}"
)

print(
    "Final 15m bars          :",
    f"{len(mes_15m):,}"
)

print(
    "Full 15m bars           :",
    f"{full_15m_bars:,}"
)

print(
    "Partial 15m bars        :",
    f"{partial_15m_bars:,}"
)


print(
    "\n[2] CONTRACT / DTYPE"
)

print(
    "Roll-crossing bars      :",
    f"{roll_crossing_bars:,}"
)

print(
    "Max instruments / bar   :",
    max_instruments_per_bar
)

print(
    "Raw instrument_id dtype :",
    RAW_INSTRUMENT_DTYPE
)

print(
    "15m instrument_id dtype :",
    clean_instrument_dtype
)

print(
    "Dtype match             :",
    instrument_dtype_match
)


print(
    "\n[3] V1 CLOCK INTEGRITY — BEFORE NYSE CALENDAR"
)

print(
    "09:45–15:00 NY bars     :",
    f"{v1_clock_bars:,}"
)

print(
    "Partial V1-clock bars   :",
    f"{v1_partial_bars:,}"
)

print(
    "Integrity-eligible bars :",
    f"{v1_integrity_eligible_bars:,}"
)

print(
    "Policy                  : "
    "partial bars retained, "
    "but NOT decision-eligible"
)


print(
    "\n[4] ACTIVE 1m COUNT DISTRIBUTION"
)

print(
    active_count_distribution
    .to_string()
)


if v1_partial_bars > 0:

    print(
        "\n[5] FIRST 10 V1 PARTIAL BARS"
    )

    print(
        partial_v1
        .head(
            10
        )
        .to_string()
    )


print(
    "\n[6] DATABENTO DEGRADED DATES ↔ MES"
)

print(
    "Degraded dates          :",
    f"{len(degraded_days):,}"
)

print(
    degraded_days
    .to_string(
        index=False
    )
)


print(
    "\n[7] EARLY MES LIQUIDITY — FIRST 8 NY MONTHS"
)

print(
    launch_monthly
    .head(
        8
    )
    .to_string()
)


print(
    "\n[8] OLD 15m SEMANTIC CROSS-CHECK"
)

print(
    json.dumps(
        old_15m_check,
        indent=2,
        ensure_ascii=False,
    )
)


print(
    "\n[9] SAVED ARTIFACTS"
)

print(
    "Clean 15m parquet       :",
    MES_15M_PATH
)

print(
    "CELL 5 audit            :",
    CELL5_AUDIT_PATH
)

print(
    "V1 partial bars         :",
    V1_PARTIAL_PATH
)

print(
    "Degraded-date impact    :",
    DEGRADED_IMPACT_PATH
)

print(
    "Launch liquidity        :",
    LAUNCH_LIQUIDITY_PATH
)


print(
    "\n"
    + "=" * 72
)

print(
    "CELL 5 15m INTEGRITY AUDIT: PASS"
)

print(
    "=" * 72
)

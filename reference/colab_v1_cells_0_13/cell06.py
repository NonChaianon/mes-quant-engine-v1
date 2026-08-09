# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 6 — RAW GAP ATTRIBUTION AUDIT
# ============================================================
#
# PURPOSE
# -------
# อธิบาย raw timestamp gaps > 1 minute ที่ CELL 3 ตรวจพบ
#
# CELL นี้ทำ 7 เรื่อง:
#
# 1) Bind กับ gap events จาก CELL 3
# 2) แปลงเวลา gap เป็น America/New_York
# 3) ตรวจ clock pattern ของ CME:
#       - 16:15–16:30 ET trading halt
#       - 17:00–18:00 ET daily closed period
# 4) แยก weekend / multi-day / special-session candidates
# 5) Flag overlap กับ Databento degraded dates
# 6) ตรวจ gap ที่กระทบ V1 bar-input window
# 7) ยืนยันว่า 47 V1 partial bars จาก CELL 5
#    สามารถ trace กลับมายัง raw gap events ได้หรือไม่
#
# IMPORTANT
# ---------
# - Audit only
# - ไม่ forward-fill
# - ไม่ impute
# - ไม่ลบ raw rows
# - ไม่ลบ degraded days
# - ไม่กล่าวว่า short gap = data error
# - UNCLASSIFIED ต้องเป็น 0
#   แต่ไม่ได้หมายความว่า causal explanation = 100%
# ============================================================


# ------------------------------------------------------------
# Colab/Jupyter warning guard
#
# Prevent jupyter_client's Python 3.12 utcnow deprecation
# from recursively flooding cell output and making execution
# appear to run forever. This does not suppress pip stderr or
# any pipeline audit failure.
# ------------------------------------------------------------

import warnings as _warnings

_warnings.filterwarnings(
    "ignore",
    message=(
        r"datetime\.datetime\.utcnow\(\) is deprecated.*"
    ),
    category=DeprecationWarning,
    module=r"jupyter_client(\..*)?",
)


# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone, time, timedelta

import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 2) Paths
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


CELL3_AUDIT_PATH = (
    CLEAN_DIR
    / "cell3_supplemental_raw_audit.json"
)

CELL4_AUDIT_PATH = (
    CLEAN_DIR
    / "cell4_dataset_condition_audit.json"
)

CELL5_AUDIT_PATH = (
    CLEAN_DIR
    / "cell5_15m_resample_audit.json"
)

GAP_EVENTS_PATH = (
    CLEAN_DIR
    / "cell3_gap_events.parquet"
)

CONDITION_PATH = (
    CLEAN_DIR
    / "databento_glbx_mdp3_condition_registry.csv"
)

MES_15M_PATH = (
    CLEAN_DIR
    / "MES_2019_2026_15m_clean.parquet"
)


# ------------------------------------------------------------
# CELL 6 outputs
# ------------------------------------------------------------

CELL6_EVENTS_PATH = (
    CLEAN_DIR
    / "cell6_gap_attribution_events.parquet"
)

CELL6_SUMMARY_PATH = (
    CLEAN_DIR
    / "cell6_gap_attribution_summary.csv"
)

CELL6_CLOCK_PATTERNS_PATH = (
    CLEAN_DIR
    / "cell6_gap_clock_patterns.csv"
)

CELL6_V1_GAPS_PATH = (
    CLEAN_DIR
    / "cell6_v1_partial_gap_events.parquet"
)

CELL6_AUDIT_PATH = (
    CLEAN_DIR
    / "cell6_gap_attribution_audit.json"
)


# ------------------------------------------------------------
# 3) Constants
# ------------------------------------------------------------

NY_TZ = "America/New_York"

ONE_MINUTE = pd.Timedelta(
    minutes=1
)

ONE_NS = pd.Timedelta(
    nanoseconds=1
)


# ------------------------------------------------------------
# 4) Upstream artifact gates
# ------------------------------------------------------------

required_paths = [
    CELL3_AUDIT_PATH,
    CELL4_AUDIT_PATH,
    CELL5_AUDIT_PATH,
    GAP_EVENTS_PATH,
    CONDITION_PATH,
    MES_15M_PATH,
]


for path in required_paths:

    if not path.exists():

        raise RuntimeError(
            "CELL 6 STOPPED — missing upstream artifact:\n"
            f"{path}\n\n"
            "Run CELL 0 → CELL 5 first."
        )


# ------------------------------------------------------------
# 5) Load upstream audits
# ------------------------------------------------------------

with open(
    CELL3_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    cell3_audit = json.load(f)


with open(
    CELL4_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    cell4_audit = json.load(f)


with open(
    CELL5_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    cell5_audit = json.load(f)


# ------------------------------------------------------------
# 6) Upstream status gates
# ------------------------------------------------------------

expected_gap_count = (
    cell3_audit
    .get(
        "raw_gap_audit",
        {},
    )
    .get(
        "gap_gt_1_minute_events"
    )
)


if expected_gap_count is None:

    raise RuntimeError(
        "CELL 6 STOPPED — CELL 3 audit does not expose "
        "gap_gt_1_minute_events."
    )


if (
    cell4_audit.get(
        "registry_status"
    )
    !=
    "AVAILABLE"
):

    raise RuntimeError(
        "CELL 6 STOPPED — CELL 4 condition registry "
        "is not AVAILABLE."
    )


if (
    cell5_audit.get(
        "failures",
        [],
    )
    !=
    []
):

    raise RuntimeError(
        "CELL 6 STOPPED — CELL 5 audit contains failures."
    )


# ------------------------------------------------------------
# 7) Load raw gap-event table
#
# Important:
# This is the event-level artifact created by CELL 3.
# ------------------------------------------------------------

gaps = pd.read_parquet(
    GAP_EVENTS_PATH
)


REQUIRED_GAP_COLUMNS = {
    "prev_timestamp",
    "next_timestamp",
    "gap_minutes",
    "instrument_before",
    "instrument_after",
    "roll_boundary",
}


missing_gap_columns = (
    REQUIRED_GAP_COLUMNS
    -
    set(
        gaps.columns
    )
)


if missing_gap_columns:

    raise RuntimeError(
        "CELL 6 STOPPED — missing gap-event columns:\n"
        + ", ".join(
            sorted(
                missing_gap_columns
            )
        )
    )


# ------------------------------------------------------------
# 8) Normalize timestamps
# ------------------------------------------------------------

for col in [
    "prev_timestamp",
    "next_timestamp",
]:

    gaps[
        col
    ] = pd.to_datetime(
        gaps[
            col
        ],
        utc=True,
        errors="raise",
    )


gaps[
    "gap_minutes"
] = (
    pd.to_numeric(
        gaps[
            "gap_minutes"
        ],
        errors="raise",
    )
    .astype(
        "int64"
    )
)


# ------------------------------------------------------------
# 9) Bind exactly to CELL 3
# ------------------------------------------------------------

if (
    len(
        gaps
    )
    !=
    int(
        expected_gap_count
    )
):

    raise RuntimeError(
        "CELL 6 STOPPED — gap-event count mismatch.\n\n"
        f"Loaded : {len(gaps):,}\n"
        f"CELL 3 : {int(expected_gap_count):,}"
    )


if (
    gaps[
        "gap_minutes"
    ]
    .le(
        1
    )
    .any()
):

    raise RuntimeError(
        "CELL 6 STOPPED — gap_minutes <= 1 "
        "found in gap-event artifact."
    )


if (
    gaps[
        "next_timestamp"
    ]
    <=
    gaps[
        "prev_timestamp"
    ]
).any():

    raise RuntimeError(
        "CELL 6 STOPPED — non-positive gap interval."
    )


duplicate_gap_events = int(
    gaps[
        [
            "prev_timestamp",
            "next_timestamp",
        ]
    ]
    .duplicated()
    .sum()
)


if duplicate_gap_events != 0:

    raise RuntimeError(
        "CELL 6 STOPPED — duplicate gap endpoints: "
        f"{duplicate_gap_events:,}"
    )


# ------------------------------------------------------------
# 10) Verify stored gap_minutes against timestamps
# ------------------------------------------------------------

observed_gap_minutes = (

    (
        gaps[
            "next_timestamp"
        ]
        -
        gaps[
            "prev_timestamp"
        ]
    )

    /
    ONE_MINUTE
)


observed_gap_minutes = (
    observed_gap_minutes
    .astype(
        "int64"
    )
)


if not np.array_equal(
    observed_gap_minutes
    .to_numpy(),

    gaps[
        "gap_minutes"
    ]
    .to_numpy(),
):

    raise RuntimeError(
        "CELL 6 STOPPED — stored gap_minutes "
        "does not match timestamp difference."
    )


# ------------------------------------------------------------
# 11) Missing interval semantics
#
# Example:
#
# Existing:
# 10:00
# 10:02
#
# gap_minutes = 2
#
# Missing raw timestamp:
# 10:01
#
# Therefore:
# missing_minutes = gap_minutes - 1
# ------------------------------------------------------------

gaps[
    "missing_minutes"
] = (
    gaps[
        "gap_minutes"
    ]
    -
    1
)


gaps[
    "missing_start_utc"
] = (
    gaps[
        "prev_timestamp"
    ]
    +
    ONE_MINUTE
)


gaps[
    "missing_end_utc"
] = (
    gaps[
        "next_timestamp"
    ]
)


# ------------------------------------------------------------
# 12) Convert endpoints to New York
#
# DST is handled by timezone conversion.
# ------------------------------------------------------------

gaps[
    "prev_timestamp_ny"
] = (
    gaps[
        "prev_timestamp"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)


gaps[
    "next_timestamp_ny"
] = (
    gaps[
        "next_timestamp"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)


gaps[
    "missing_start_ny"
] = (
    gaps[
        "missing_start_utc"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)


gaps[
    "missing_end_ny"
] = (
    gaps[
        "missing_end_utc"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)


# ------------------------------------------------------------
# 13) Readable clock fields
# ------------------------------------------------------------

gaps[
    "prev_time_ny"
] = (
    gaps[
        "prev_timestamp_ny"
    ]
    .dt
    .strftime(
        "%H:%M"
    )
)


gaps[
    "next_time_ny"
] = (
    gaps[
        "next_timestamp_ny"
    ]
    .dt
    .strftime(
        "%H:%M"
    )
)


gaps[
    "prev_date_ny"
] = (
    gaps[
        "prev_timestamp_ny"
    ]
    .dt
    .strftime(
        "%Y-%m-%d"
    )
)


gaps[
    "next_date_ny"
] = (
    gaps[
        "next_timestamp_ny"
    ]
    .dt
    .strftime(
        "%Y-%m-%d"
    )
)


gaps[
    "same_ny_date"
] = (
    gaps[
        "prev_date_ny"
    ]
    .eq(
        gaps[
            "next_date_ny"
        ]
    )
)


# ------------------------------------------------------------
# 14) Load Databento condition registry
#
# Used only as an independent context flag.
# NOT proof that MES itself is defective.
# ------------------------------------------------------------

condition_df = pd.read_csv(
    CONDITION_PATH
)


condition_df[
    "date"
] = (
    pd.to_datetime(
        condition_df[
            "date"
        ],
        utc=True,
        errors="raise",
    )
    .dt
    .date
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


degraded_utc_dates = set(

    condition_df.loc[
        condition_df[
            "condition"
        ]
        .eq(
            "degraded"
        ),
        "date",
    ]
)


# ------------------------------------------------------------
# 15) Time-overlap helpers
#
# We classify CLOCK PATTERNS.
#
# This is deliberately different from saying:
# "we know the causal reason for every missing trade bar."
# ------------------------------------------------------------

def local_timestamp(
    day,
    hour,
    minute,
):

    return (
        pd.Timestamp(
            datetime.combine(
                day,
                time(
                    hour,
                    minute,
                ),
            )
        )
        .tz_localize(
            NY_TZ
        )
    )


def overlaps_local_window(
    start_utc,
    end_utc,
    start_hm,
    end_hm,
):

    if end_utc <= start_utc:

        return False


    start_local = (
        start_utc
        .tz_convert(
            NY_TZ
        )
    )


    end_local = (
        end_utc
        .tz_convert(
            NY_TZ
        )
    )


    last_local = (
        end_local
        -
        ONE_NS
    )


    day = (
        start_local
        .date()
    )


    last_day = (
        last_local
        .date()
    )


    while day <= last_day:

        window_start = (
            local_timestamp(
                day,
                *start_hm,
            )
        )


        window_end = (
            local_timestamp(
                day,
                *end_hm,
            )
        )


        if (
            start_local
            <
            window_end

            and

            end_local
            >
            window_start
        ):

            return True


        day += timedelta(
            days=1
        )


    return False


def overlaps_local_weekday_window(
    start_utc,
    end_utc,
    start_hm,
    end_hm,
):

    if end_utc <= start_utc:

        return False


    start_local = (
        start_utc
        .tz_convert(
            NY_TZ
        )
    )


    end_local = (
        end_utc
        .tz_convert(
            NY_TZ
        )
    )


    last_local = (
        end_local
        -
        ONE_NS
    )


    day = (
        start_local
        .date()
    )


    last_day = (
        last_local
        .date()
    )


    while day <= last_day:

        # Monday = 0 ... Friday = 4
        if day.weekday() < 5:

            window_start = (
                local_timestamp(
                    day,
                    *start_hm,
                )
            )


            window_end = (
                local_timestamp(
                    day,
                    *end_hm,
                )
            )


            if (
                start_local
                <
                window_end

                and

                end_local
                >
                window_start
            ):

                return True


        day += timedelta(
            days=1
        )


    return False


def touches_weekend_local(
    start_utc,
    end_utc,
):

    if end_utc <= start_utc:

        return False


    start_local = (
        start_utc
        .tz_convert(
            NY_TZ
        )
    )


    last_local = (
        end_utc
        .tz_convert(
            NY_TZ
        )
        -
        ONE_NS
    )


    day = (
        start_local
        .date()
    )


    last_day = (
        last_local
        .date()
    )


    while day <= last_day:

        if day.weekday() >= 5:

            return True


        day += timedelta(
            days=1
        )


    return False


def overlaps_degraded_utc_date(
    start_utc,
    end_utc,
):

    if end_utc <= start_utc:

        return False


    day = (
        start_utc
        .date()
    )


    last_day = (
        (
            end_utc
            -
            ONE_NS
        )
        .date()
    )


    while day <= last_day:

        if day in degraded_utc_dates:

            return True


        day += timedelta(
            days=1
        )


    return False


# ------------------------------------------------------------
# 16) Evaluate overlap flags
#
# CME clock references:
#
# 16:15–16:30 ET
#     scheduled intraday halt
#
# 17:00–18:00 ET
#     regular daily closed period
#
# V1 bar-input interval:
#
# 09:30–15:00 ET
#
# Why 09:30?
# A decision at 09:45 uses the 09:30–09:44 bar.
# ------------------------------------------------------------

gap_intervals = list(
    zip(
        gaps[
            "missing_start_utc"
        ],
        gaps[
            "missing_end_utc"
        ],
    )
)


gaps[
    "cme_1615_1630_overlap"
] = [

    overlaps_local_window(
        start,
        end,
        (16, 15),
        (16, 30),
    )

    for start, end
    in gap_intervals
]


gaps[
    "cme_1700_1800_overlap"
] = [

    overlaps_local_window(
        start,
        end,
        (17, 0),
        (18, 0),
    )

    for start, end
    in gap_intervals
]


gaps[
    "v1_bar_input_overlap"
] = [

    overlaps_local_weekday_window(
        start,
        end,
        (9, 30),
        (15, 0),
    )

    for start, end
    in gap_intervals
]


gaps[
    "touches_weekend_ny"
] = [

    touches_weekend_local(
        start,
        end,
    )

    for start, end
    in gap_intervals
]


gaps[
    "degraded_utc_date_overlap"
] = [

    overlaps_degraded_utc_date(
        start,
        end,
    )

    for start, end
    in gap_intervals
]


# ------------------------------------------------------------
# 17) Exact New York clock patterns
# ------------------------------------------------------------

prev_minute_ny = (

    gaps[
        "prev_timestamp_ny"
    ]
    .dt.hour
    *
    60

    +

    gaps[
        "prev_timestamp_ny"
    ]
    .dt.minute
)


next_minute_ny = (

    gaps[
        "next_timestamp_ny"
    ]
    .dt.hour
    *
    60

    +

    gaps[
        "next_timestamp_ny"
    ]
    .dt.minute
)


# ------------------------------------------------------------
# Exact CME halt:
#
# 16:14 raw bar exists
# 16:15–16:29 absent
# 16:30 raw bar exists
#
# Timestamp difference = 16 minutes
# ------------------------------------------------------------

gaps[
    "exact_cme_halt_pattern"
] = (

    gaps[
        "same_ny_date"
    ]

    &

    gaps[
        "gap_minutes"
    ]
    .eq(
        16
    )

    &

    prev_minute_ny
    .eq(
        16 * 60
        + 14
    )

    &

    next_minute_ny
    .eq(
        16 * 60
        + 30
    )
)


# ------------------------------------------------------------
# Exact regular daily close/reopen:
#
# 16:59 raw bar exists
# next raw bar = 18:00
#
# Timestamp difference = 61 minutes
# ------------------------------------------------------------

gaps[
    "exact_daily_closed_period_pattern"
] = (

    gaps[
        "same_ny_date"
    ]

    &

    gaps[
        "gap_minutes"
    ]
    .eq(
        61
    )

    &

    prev_minute_ny
    .eq(
        16 * 60
        + 59
    )

    &

    next_minute_ny
    .eq(
        18 * 60
    )
)


# ------------------------------------------------------------
# Longer same-day closure that reopens at 18:00
#
# Examples might include early/special closes.
#
# Candidate only:
# We do NOT label the holiday cause automatically.
# ------------------------------------------------------------

gaps[
    "special_close_to_1800_candidate"
] = (

    gaps[
        "same_ny_date"
    ]

    &

    gaps[
        "gap_minutes"
    ]
    .gt(
        61
    )

    &

    gaps[
        "gap_minutes"
    ]
    .lt(
        24 * 60
    )

    &

    next_minute_ny
    .eq(
        18 * 60
    )
)


# ------------------------------------------------------------
# 18) Primary attribution taxonomy
#
# IMPORTANT:
#
# Every event gets ONE primary category.
#
# Some categories are high-confidence schedule matches.
# Others are deliberately called "candidate".
#
# Therefore:
#
# UNCLASSIFIED = 0
#
# does NOT mean:
#
# causal uncertainty = 0
# ------------------------------------------------------------

gaps[
    "primary_attribution"
] = (
    "UNCLASSIFIED"
)


# ------------------------------------------------------------
# Priority 1:
# Weekend / multi-day closure
# ------------------------------------------------------------

multiday_closure_candidate = (

    gaps[
        "gap_minutes"
    ]
    .ge(
        24 * 60
    )
)


gaps.loc[
    multiday_closure_candidate,
    "primary_attribution",
] = (
    "WEEKEND_OR_MULTIDAY_CLOSURE_CANDIDATE"
)



# ------------------------------------------------------------
# Priority 2:
# Exact daily 17:00 → 18:00 closed period
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )

    &

    gaps[
        "exact_daily_closed_period_pattern"
    ],

    "primary_attribution",
] = (
    "CME_DAILY_CLOSED_PERIOD_EXACT"
)


# ------------------------------------------------------------
# Priority 3:
# Longer close that reopens at 18:00
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )

    &

    gaps[
        "special_close_to_1800_candidate"
    ],

    "primary_attribution",
] = (
    "SPECIAL_SESSION_CLOSE_TO_1800_CANDIDATE"
)


# ------------------------------------------------------------
# Priority 4:
# Exact 16:15 → 16:30 halt
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )

    &

    gaps[
        "exact_cme_halt_pattern"
    ],

    "primary_attribution",
] = (
    "CME_1615_1630_HALT_EXACT"
)


# ------------------------------------------------------------
# Priority 5:
# Gap overlaps halt but is longer than exact halt
#
# Example:
# no trade immediately before/after the scheduled halt.
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )

    &

    gaps[
        "cme_1615_1630_overlap"
    ],

    "primary_attribution",
] = (
    "CME_HALT_PLUS_ADJACENT_GAP_CANDIDATE"
)


# ------------------------------------------------------------
# Priority 6:
# Other > 61-minute intraday gap
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )

    &

    gaps[
        "gap_minutes"
    ]
    .gt(
        61
    ),

    "primary_attribution",
] = (
    "OTHER_INTRADAY_OR_SPECIAL_CLOSURE_CANDIDATE"
)


# ------------------------------------------------------------
# Priority 7:
# Remaining short gaps
#
# Because Databento OHLCV is trade-based,
# OHLCV alone cannot prove whether these are:
#
# - no-trade minutes
# - interruption
# - data-quality issue
#
# So we deliberately do NOT call them "errors".
# ------------------------------------------------------------

gaps.loc[
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    ),

    "primary_attribution",
] = (
    "SHORT_NO_TRADE_OR_DATA_GAP_CANDIDATE"
)


# ------------------------------------------------------------
# 19) Load clean 15m integrity artifact
#
# Main goal:
# connect raw gaps back to the V1 partial bars from CELL 5.
# ------------------------------------------------------------

mes_15m = pd.read_parquet(
    MES_15M_PATH
)


required_15m_columns = {
    "v1_clock_partial",
    "bar_complete_15m",
}


if not required_15m_columns.issubset(
    mes_15m.columns
):

    raise RuntimeError(
        "CELL 6 STOPPED — clean 15m file "
        "does not contain CELL 5 integrity columns."
    )


# ------------------------------------------------------------
# 20) Extract V1 partial 15m bars
# ------------------------------------------------------------

v1_partial_starts = (
    mes_15m.index[
        mes_15m[
            "v1_clock_partial"
        ]
        .astype(
            bool
        )
    ]
)


v1_partial_start_ns = (
    v1_partial_starts
    .asi8
)


v1_partial_end_ns = (

    v1_partial_start_ns
    +
    pd.Timedelta(
        minutes=15
    )
    .value
)


# ------------------------------------------------------------
# 21) Trace every raw gap to V1 partial bars
#
# There are only a small number of V1 partial bars,
# so this check is intentionally simple and auditable.
# ------------------------------------------------------------

explained_partial_mask = np.zeros(
    len(
        v1_partial_starts
    ),
    dtype=bool,
)


gap_hits_v1_partial = np.zeros(
    len(
        gaps
    ),
    dtype=bool,
)


for i, (
    missing_start,
    missing_end,
) in enumerate(
    zip(
        gaps[
            "missing_start_utc"
        ],
        gaps[
            "missing_end_utc"
        ],
    )
):

    start_ns = (
        missing_start.value
    )


    end_ns = (
        missing_end.value
    )


    overlap = (

        v1_partial_start_ns
        <
        end_ns

        &

        (
            v1_partial_end_ns
            >
            start_ns
        )
    )


    # Keep explicit parentheses for numpy boolean logic
    overlap = (

        (
            v1_partial_start_ns
            <
            end_ns
        )

        &

        (
            v1_partial_end_ns
            >
            start_ns
        )
    )


    if overlap.any():

        gap_hits_v1_partial[
            i
        ] = True


        explained_partial_mask |= overlap


gaps[
    "impacts_v1_partial_bar"
] = (
    gap_hits_v1_partial
)


# ------------------------------------------------------------
# 22) Cross-check against CELL 5
# ------------------------------------------------------------

expected_v1_partial = (

    cell5_audit
    .get(
        "v1_clock_integrity",
        {},
    )
    .get(
        "partial_bars"
    )
)


observed_v1_partial = int(
    len(
        v1_partial_starts
    )
)


explained_v1_partial = int(
    explained_partial_mask
    .sum()
)


unexplained_v1_partial = int(
    observed_v1_partial
    -
    explained_v1_partial
)


# ------------------------------------------------------------
# 23) Hard audit failures
# ------------------------------------------------------------

failures = []


if expected_v1_partial is None:

    failures.append(
        "CELL 5 audit missing V1 partial-bar count"
    )


elif (
    observed_v1_partial
    !=
    int(
        expected_v1_partial
    )
):

    failures.append(
        "Clean 15m V1 partial count mismatch: "
        f"{observed_v1_partial} "
        f"!= CELL 5 {int(expected_v1_partial)}"
    )


# ------------------------------------------------------------
# Strong traceability gate:
#
# Every V1 partial bar must trace to at least one raw gap.
# ------------------------------------------------------------

if unexplained_v1_partial != 0:

    failures.append(
        "V1 partial bars not linked to raw gap events: "
        f"{unexplained_v1_partial}"
    )


# ------------------------------------------------------------
# Every gap must belong to the taxonomy.
# ------------------------------------------------------------

unclassified_count = int(
    gaps[
        "primary_attribution"
    ]
    .eq(
        "UNCLASSIFIED"
    )
    .sum()
)


if unclassified_count != 0:

    failures.append(
        "Primary gap attribution has "
        f"{unclassified_count} UNCLASSIFIED events"
    )


short_gap_misclassified_as_multiday = int(
    (
        gaps[
            "primary_attribution"
        ]
        .eq(
            "WEEKEND_OR_MULTIDAY_CLOSURE_CANDIDATE"
        )

        &

        gaps[
            "gap_minutes"
        ]
        .lt(
            24 * 60
        )
    )
    .sum()
)


if short_gap_misclassified_as_multiday != 0:

    failures.append(
        "Short gaps incorrectly classified "
        "as multiday closure: "
        f"{short_gap_misclassified_as_multiday}"
    )


# ------------------------------------------------------------
# 24) Attribution summary
# ------------------------------------------------------------

summary = (

    gaps

    .groupby(
        "primary_attribution",
        dropna=False,
    )

    .agg(
        events=(
            "gap_minutes",
            "size",
        ),

        missing_minutes=(
            "missing_minutes",
            "sum",
        ),

        median_gap_minutes=(
            "gap_minutes",
            "median",
        ),

        max_gap_minutes=(
            "gap_minutes",
            "max",
        ),

        degraded_overlap_events=(
            "degraded_utc_date_overlap",
            "sum",
        ),

        v1_input_overlap_events=(
            "v1_bar_input_overlap",
            "sum",
        ),

        v1_partial_impact_events=(
            "impacts_v1_partial_bar",
            "sum",
        ),

        roll_boundary_events=(
            "roll_boundary",
            "sum",
        ),
    )

    .sort_values(
        [
            "events",
            "missing_minutes",
        ],
        ascending=[
            False,
            False,
        ],
    )

    .reset_index()
)


summary[
    "pct_of_gap_events"
] = (

    summary[
        "events"
    ]

    /
    len(
        gaps
    )

    *
    100.0
)


if (
    int(
        summary[
            "events"
        ]
        .sum()
    )
    !=
    len(
        gaps
    )
):

    failures.append(
        "Attribution summary does not sum "
        "to total gap events"
    )


# ------------------------------------------------------------
# 25) New York clock-pattern table
#
# This table is especially useful for explaining:
#
# 16-minute
# 61-minute
# 286-minute
# 301-minute
# etc.
# ------------------------------------------------------------

clock_patterns = (

    gaps

    .groupby(
        [
            "gap_minutes",
            "prev_time_ny",
            "next_time_ny",
            "primary_attribution",
        ],
        dropna=False,
    )

    .size()

    .rename(
        "count"
    )

    .reset_index()

    .sort_values(
        [
            "count",
            "gap_minutes",
        ],
        ascending=[
            False,
            True,
        ],
    )
)


# ------------------------------------------------------------
# 26) Save event-level artifacts
# ------------------------------------------------------------

gaps.to_parquet(
    CELL6_EVENTS_PATH,
    index=False,
)


summary.to_csv(
    CELL6_SUMMARY_PATH,
    index=False,
)


clock_patterns.to_csv(
    CELL6_CLOCK_PATTERNS_PATH,
    index=False,
)


gaps.loc[
    gaps[
        "impacts_v1_partial_bar"
    ]
].to_parquet(
    CELL6_V1_GAPS_PATH,
    index=False,
)


# ------------------------------------------------------------
# 27) Core result counts
# ------------------------------------------------------------

exact_halt_count = int(
    gaps[
        "exact_cme_halt_pattern"
    ]
    .sum()
)


exact_daily_closed_count = int(
    gaps[
        "exact_daily_closed_period_pattern"
    ]
    .sum()
)


special_close_1800_count = int(
    gaps[
        "special_close_to_1800_candidate"
    ]
    .sum()
)


degraded_overlap_count = int(
    gaps[
        "degraded_utc_date_overlap"
    ]
    .sum()
)


v1_input_overlap_count = int(
    gaps[
        "v1_bar_input_overlap"
    ]
    .sum()
)


roll_gap_count = int(
    gaps[
        "roll_boundary"
    ]
    .sum()
)


# ------------------------------------------------------------
# 28) Build forensic audit
# ------------------------------------------------------------

cell6_audit = {

    "audit_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),


    "input_binding": {

        "cell3_expected_gap_events":
            int(
                expected_gap_count
            ),

        "loaded_gap_events":
            int(
                len(
                    gaps
                )
            ),

        "cell5_expected_v1_partial_bars":
            (
                None
                if expected_v1_partial is None
                else int(
                    expected_v1_partial
                )
            ),

        "observed_v1_partial_bars":
            observed_v1_partial,
    },


    "schedule_clock_basis": {

        "timezone":
            NY_TZ,

        "regular_globex_hours_reference":
            "Sunday-Friday 18:00-17:00 ET",

        "intraday_halt_reference":
            "16:15-16:30 ET",

        "regular_daily_closed_period_reference":
            "17:00-18:00 ET",

        "classification_note":
            (
                "Exact clock matches are strong schedule "
                "attributions. Extended and short-gap "
                "categories are candidates, not causal proof "
                "from trade-based OHLCV alone."
            ),
    },


    "results": {

        "total_gap_events":
            int(
                len(
                    gaps
                )
            ),

        "total_missing_minutes":
            int(
                gaps[
                    "missing_minutes"
                ]
                .sum()
            ),

        "exact_cme_halt_events":
            exact_halt_count,

        "exact_daily_closed_period_events":
            exact_daily_closed_count,

        "special_close_to_1800_candidates":
            special_close_1800_count,

        "degraded_utc_date_overlap_events":
            degraded_overlap_count,

        "v1_bar_input_overlap_events":
            v1_input_overlap_count,

        "raw_gap_events_impacting_v1_partial_bars":
            int(
                gaps[
                    "impacts_v1_partial_bar"
                ]
                .sum()
            ),

        "v1_partial_bars_explained_by_raw_gaps":
            explained_v1_partial,

        "v1_partial_bars_unexplained_by_raw_gaps":
            unexplained_v1_partial,

        "roll_boundary_gap_events":
            roll_gap_count,

        "primary_unclassified_events":
            unclassified_count,
    },


    "policy": {

        "automatic_raw_row_deletion":
            False,

        "automatic_gap_imputation":
            False,

        "automatic_degraded_day_exclusion":
            False,

        "short_gap_causal_claim":
            False,
    },


    "artifacts": {

        "events":
            str(
                CELL6_EVENTS_PATH
            ),

        "summary":
            str(
                CELL6_SUMMARY_PATH
            ),

        "clock_patterns":
            str(
                CELL6_CLOCK_PATTERNS_PATH
            ),

        "v1_partial_gap_events":
            str(
                CELL6_V1_GAPS_PATH
            ),
    },


    "failures":
        failures,
}


# ------------------------------------------------------------
# 29) Save audit BEFORE hard gate
# ------------------------------------------------------------

with open(
    CELL6_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        cell6_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 30) Final hard gate
# ------------------------------------------------------------

if failures:

    print(
        "\nCELL 6 FAILURES"
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
        "\nCELL 6 GAP ATTRIBUTION AUDIT: FAIL\n"
        f"{CELL6_AUDIT_PATH}"
    )


# ------------------------------------------------------------
# 31) Compact output
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "CELL 6 — RAW GAP ATTRIBUTION AUDIT"
)

print(
    "=" * 72
)


print(
    "\n[1] INPUT BINDING"
)

print(
    "Gap events from CELL 3          :",
    f"{len(gaps):,}"
)

print(
    "V1 partial bars from CELL 5     :",
    f"{observed_v1_partial:,}"
)

print(
    "V1 partial bars explained       :",
    f"{explained_v1_partial:,}"
)

print(
    "V1 partial bars unexplained     :",
    f"{unexplained_v1_partial:,}"
)


print(
    "\n[2] HIGH-CONFIDENCE CLOCK PATTERNS"
)

print(
    "Exact 16:15–16:30 halt events   :",
    f"{exact_halt_count:,}"
)

print(
    "Exact 17:00–18:00 closed period :",
    f"{exact_daily_closed_count:,}"
)

print(
    "Special close → 18:00 candidate :",
    f"{special_close_1800_count:,}"
)


print(
    "\n[3] CONTEXT FLAGS"
)

print(
    "Degraded-date overlap events    :",
    f"{degraded_overlap_count:,}"
)

print(
    "V1 bar-input overlap events     :",
    f"{v1_input_overlap_count:,}"
)

print(
    "Roll-boundary gap events        :",
    f"{roll_gap_count:,}"
)


print(
    "\n[4] PRIMARY ATTRIBUTION SUMMARY"
)

print(
    summary
    .to_string(
        index=False
    )
)


print(
    "\n[5] TOP 20 NEW YORK CLOCK PATTERNS"
)

print(
    clock_patterns
    .head(
        20
    )
    .to_string(
        index=False
    )
)


print(
    "\n[6] POLICY"
)

print(
    "UNCLASSIFIED events             :",
    unclassified_count
)

print(
    "Automatic deletion              : False"
)

print(
    "Automatic imputation            : False"
)

print(
    "Short-gap causal claim          : False"
)


print(
    "\n[7] SAVED ARTIFACTS"
)

print(
    "Event-level attribution         :",
    CELL6_EVENTS_PATH
)

print(
    "Attribution summary             :",
    CELL6_SUMMARY_PATH
)

print(
    "Clock patterns                  :",
    CELL6_CLOCK_PATTERNS_PATH
)

print(
    "V1-impacting gap events         :",
    CELL6_V1_GAPS_PATH
)

print(
    "CELL 6 audit                    :",
    CELL6_AUDIT_PATH
)


print(
    "\n"
    + "=" * 72
)

print(
    "CELL 6 GAP ATTRIBUTION AUDIT: PASS"
)

print(
    "=" * 72
)

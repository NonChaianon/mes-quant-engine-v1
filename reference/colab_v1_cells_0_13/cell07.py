# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 7 — POINT-IN-TIME DECISION UNIVERSE
# ============================================================
#
# PURPOSE
# -------
# Freeze the timestamps at which MES V1 is allowed to make an
# entry decision before any feature, label, or model is built.
#
# POLICY
# ------
# 1) Decision time is the end of a completed 15-minute input bar.
# 2) Base clock window is 09:45–15:00 America/New_York.
# 3) NYSE regular sessions are a research/entry policy filter.
#    They are NOT treated as the authority for CME tradability.
# 4) A +60 minute research horizon must fit before the scheduled
#    NYSE close. On a normal 16:00 close the last decision is 15:00;
#    on a 13:00 early close the last decision is 12:00.
# 5) Partial or mixed-contract input bars remain in the ledger as
#    context but cannot become decision observations.
# 6) Databento degraded-date metadata is retained as a context flag;
#    it is NOT an automatic exclusion rule.
# 7) No future return or future-bar quality is used to decide whether
#    a timestamp belongs to the live point-in-time universe.
# ============================================================


# ------------------------------------------------------------
# Colab/Jupyter warning guard
# ------------------------------------------------------------

import warnings as _warnings

_warnings.filterwarnings(
    "ignore",
    message=(
        r"datetime\.datetime\.utcnow\(\) is deprecated.*"
    ),
    category=DeprecationWarning,
)


# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone

import hashlib
import json

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal


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


MES_15M_PATH = (
    CLEAN_DIR
    / "MES_2019_2026_15m_clean.parquet"
)

CELL4_AUDIT_PATH = (
    CLEAN_DIR
    / "cell4_dataset_condition_audit.json"
)

CELL5_AUDIT_PATH = (
    CLEAN_DIR
    / "cell5_15m_resample_audit.json"
)

CELL6_AUDIT_PATH = (
    CLEAN_DIR
    / "cell6_gap_attribution_audit.json"
)


# ------------------------------------------------------------
# CELL 7 outputs
# ------------------------------------------------------------

CELL7_UNIVERSE_PATH = (
    CLEAN_DIR
    / "cell7_decision_universe_v1.parquet"
)

CELL7_LEDGER_PATH = (
    CLEAN_DIR
    / "cell7_decision_universe_ledger.parquet"
)

CELL7_DAILY_PATH = (
    CLEAN_DIR
    / "cell7_decision_universe_daily_summary.csv"
)

CELL7_AUDIT_PATH = (
    CLEAN_DIR
    / "cell7_decision_universe_audit.json"
)


# ------------------------------------------------------------
# 3) Frozen V1 policy constants
# ------------------------------------------------------------

POLICY_VERSION = "MES_V1_DECISION_UNIVERSE_1.0"

NY_TZ = "America/New_York"
CALENDAR_NAME = "NYSE"

BAR_MINUTES = 15
LABEL_HORIZON_MINUTES = 60

V1_START_MINUTE = (
    9 * 60
    + 45
)

V1_END_MINUTE = (
    15 * 60
)


# ------------------------------------------------------------
# 4) Helpers
# ------------------------------------------------------------

def sha256_file(path, chunk_size=1024 * 1024):

    digest = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ------------------------------------------------------------
# 5) Upstream artifact gates
# ------------------------------------------------------------

required_paths = [
    MES_15M_PATH,
    CELL4_AUDIT_PATH,
    CELL5_AUDIT_PATH,
    CELL6_AUDIT_PATH,
]


for path in required_paths:

    if not path.exists():

        raise RuntimeError(
            "CELL 7 STOPPED — missing upstream artifact:\n"
            f"{path}\n\n"
            "Run CELL 0 → CELL 6 first."
        )


cell4_audit = load_json(
    CELL4_AUDIT_PATH
)

cell5_audit = load_json(
    CELL5_AUDIT_PATH
)

cell6_audit = load_json(
    CELL6_AUDIT_PATH
)


if (
    cell4_audit.get(
        "registry_status"
    )
    !=
    "AVAILABLE"
):

    raise RuntimeError(
        "CELL 7 STOPPED — CELL 4 condition registry "
        "is not AVAILABLE."
    )


if cell5_audit.get(
    "failures",
    [],
):

    raise RuntimeError(
        "CELL 7 STOPPED — CELL 5 audit contains failures."
    )


if cell6_audit.get(
    "failures",
    [],
):

    raise RuntimeError(
        "CELL 7 STOPPED — CELL 6 audit contains failures."
    )


if (
    cell6_audit
    .get(
        "results",
        {},
    )
    .get(
        "primary_unclassified_events"
    )
    !=
    0
):

    raise RuntimeError(
        "CELL 7 STOPPED — CELL 6 still has "
        "unclassified gap events."
    )


# ------------------------------------------------------------
# 6) Load the clean 15-minute dataset
# ------------------------------------------------------------

mes_15m = pd.read_parquet(
    MES_15M_PATH
)


REQUIRED_COLUMNS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "active_1m_count",
    "instrument_id",
    "instrument_count",
    "crosses_roll",
    "decision_time",
    "decision_time_ny",
    "bar_complete_15m",
    "data_integrity_ok",
    "v1_clock_window",
    "v1_clock_partial",
    "v1_clock_integrity_eligible",
    "dataset_condition_utc",
    "dataset_degraded_utc",
}


missing_columns = (
    REQUIRED_COLUMNS
    -
    set(
        mes_15m.columns
    )
)


if missing_columns:

    raise RuntimeError(
        "CELL 7 STOPPED — missing CELL 5 columns:\n"
        + ", ".join(
            sorted(
                missing_columns
            )
        )
    )


if not isinstance(
    mes_15m.index,
    pd.DatetimeIndex,
):

    raise RuntimeError(
        "CELL 7 STOPPED — 15m index is not DatetimeIndex."
    )


if mes_15m.index.tz is None:

    raise RuntimeError(
        "CELL 7 STOPPED — 15m index is timezone-naive."
    )


mes_15m = (
    mes_15m
    .sort_index()
    .copy()
)

mes_15m.index = (
    mes_15m.index
    .tz_convert(
        "UTC"
    )
)

mes_15m.index.name = (
    "bar_start_utc"
)


# ------------------------------------------------------------
# 7) Structural input gates
# ------------------------------------------------------------

if not mes_15m.index.is_monotonic_increasing:

    raise RuntimeError(
        "CELL 7 STOPPED — 15m index is not monotonic."
    )


duplicate_input_timestamps = int(
    mes_15m.index
    .duplicated()
    .sum()
)


if duplicate_input_timestamps != 0:

    raise RuntimeError(
        "CELL 7 STOPPED — duplicate 15m timestamps: "
        f"{duplicate_input_timestamps:,}"
    )


# ------------------------------------------------------------
# 8) Recompute point-in-time fields from the frozen index
# ------------------------------------------------------------

stored_decision_time = pd.to_datetime(
    mes_15m[
        "decision_time"
    ],
    utc=True,
    errors="raise",
)

expected_decision_time = (
    mes_15m.index
    +
    pd.Timedelta(
        minutes=BAR_MINUTES
    )
)


if not np.array_equal(
    stored_decision_time.array.asi8,
    expected_decision_time.asi8,
):

    raise RuntimeError(
        "CELL 7 STOPPED — decision_time does not equal "
        "bar_start_utc + 15 minutes."
    )


mes_15m[
    "decision_time"
] = expected_decision_time

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


recomputed_clock_window = (
    decision_minute_ny
    .between(
        V1_START_MINUTE,
        V1_END_MINUTE,
        inclusive="both",
    )
)


if not np.array_equal(
    recomputed_clock_window.to_numpy(
        dtype=bool
    ),
    mes_15m[
        "v1_clock_window"
    ]
    .astype(bool)
    .to_numpy(),
):

    raise RuntimeError(
        "CELL 7 STOPPED — stored v1_clock_window does not "
        "match the frozen 09:45–15:00 policy."
    )


recomputed_integrity_ok = (
    mes_15m[
        "active_1m_count"
    ]
    .eq(
        BAR_MINUTES
    )
    &
    ~mes_15m[
        "crosses_roll"
    ]
    .astype(bool)
)


if not np.array_equal(
    recomputed_integrity_ok.to_numpy(
        dtype=bool
    ),
    mes_15m[
        "data_integrity_ok"
    ]
    .astype(bool)
    .to_numpy(),
):

    raise RuntimeError(
        "CELL 7 STOPPED — stored data_integrity_ok does not "
        "match complete-bar / no-cross-roll policy."
    )


# ------------------------------------------------------------
# 9) Build the NYSE policy calendar
#
# The calendar is a research-session policy filter only.
# It is not a claim about whether MES traded on CME.
# ------------------------------------------------------------

first_ny_date = (
    mes_15m[
        "decision_time_ny"
    ]
    .min()
    .date()
)

last_ny_date = (
    mes_15m[
        "decision_time_ny"
    ]
    .max()
    .date()
)


nyse = mcal.get_calendar(
    CALENDAR_NAME
)

nyse_schedule = nyse.schedule(
    start_date=first_ny_date,
    end_date=last_ny_date,
)


for col in [
    "market_open",
    "market_close",
]:

    nyse_schedule[
        col
    ] = pd.to_datetime(
        nyse_schedule[
            col
        ],
        utc=True,
        errors="raise",
    )


nyse_schedule[
    "nyse_session_date"
] = (
    nyse_schedule.index.date
)


market_open_map = dict(
    zip(
        nyse_schedule[
            "nyse_session_date"
        ],
        nyse_schedule[
            "market_open"
        ],
    )
)

market_close_map = dict(
    zip(
        nyse_schedule[
            "nyse_session_date"
        ],
        nyse_schedule[
            "market_close"
        ],
    )
)


schedule_close_ny = (
    nyse_schedule[
        "market_close"
    ]
    .dt
    .tz_convert(
        NY_TZ
    )
)

schedule_close_minute_ny = (
    schedule_close_ny.dt.hour
    *
    60
    +
    schedule_close_ny.dt.minute
)


early_close_dates = set(
    nyse_schedule.loc[
        schedule_close_minute_ny
        <
        16 * 60,
        "nyse_session_date",
    ]
)


# ------------------------------------------------------------
# 10) Build the full clock-candidate ledger
# ------------------------------------------------------------

ledger_columns = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "active_1m_count",
    "instrument_id",
    "instrument_count",
    "crosses_roll",
    "decision_time",
    "decision_time_ny",
    "bar_complete_15m",
    "data_integrity_ok",
    "v1_clock_window",
    "v1_clock_partial",
    "dataset_condition_utc",
    "dataset_degraded_utc",
]


ledger = (
    mes_15m.loc[
        recomputed_clock_window,
        ledger_columns,
    ]
    .copy()
)

ledger.insert(
    0,
    "bar_start_utc",
    ledger.index,
)

ledger.reset_index(
    drop=True,
    inplace=True,
)


ledger[
    "nyse_session_date"
] = (
    ledger[
        "decision_time_ny"
    ]
    .dt.date
)

ledger[
    "nyse_market_open_utc"
] = pd.to_datetime(
    ledger[
        "nyse_session_date"
    ]
    .map(
        market_open_map
    ),
    utc=True,
)

ledger[
    "nyse_market_close_utc"
] = pd.to_datetime(
    ledger[
        "nyse_session_date"
    ]
    .map(
        market_close_map
    ),
    utc=True,
)

ledger[
    "nyse_policy_session"
] = (
    ledger[
        "nyse_market_open_utc"
    ]
    .notna()
    &
    ledger[
        "nyse_market_close_utc"
    ]
    .notna()
)

ledger[
    "policy_first_decision_utc"
] = (
    ledger[
        "nyse_market_open_utc"
    ]
    +
    pd.Timedelta(
        minutes=BAR_MINUTES
    )
)

ledger[
    "policy_last_decision_utc"
] = (
    ledger[
        "nyse_market_close_utc"
    ]
    -
    pd.Timedelta(
        minutes=LABEL_HORIZON_MINUTES
    )
)

ledger[
    "early_close_session"
] = (
    ledger[
        "nyse_session_date"
    ]
    .isin(
        early_close_dates
    )
)

ledger[
    "within_nyse_entry_policy"
] = (
    ledger[
        "nyse_policy_session"
    ]
    &
    ledger[
        "decision_time"
    ]
    .ge(
        ledger[
            "policy_first_decision_utc"
        ]
    )
    &
    ledger[
        "decision_time"
    ]
    .le(
        ledger[
            "policy_last_decision_utc"
        ]
    )
)

ledger[
    "input_bar_integrity_ok"
] = (
    ledger[
        "bar_complete_15m"
    ]
    .astype(bool)
    &
    ~ledger[
        "crosses_roll"
    ]
    .astype(bool)
)


# Degraded metadata is intentionally NOT in this expression.
ledger[
    "decision_eligible"
] = (
    ledger[
        "within_nyse_entry_policy"
    ]
    &
    ledger[
        "input_bar_integrity_ok"
    ]
)


# ------------------------------------------------------------
# 11) One primary reason per clock candidate
# ------------------------------------------------------------

ledger[
    "primary_exclusion_reason"
] = (
    "ELIGIBLE"
)


no_policy_session = (
    ~ledger[
        "nyse_policy_session"
    ]
)

before_policy_start = (
    ledger[
        "nyse_policy_session"
    ]
    &
    ledger[
        "decision_time"
    ]
    .lt(
        ledger[
            "policy_first_decision_utc"
        ]
    )
)

after_horizon_safe_close = (
    ledger[
        "nyse_policy_session"
    ]
    &
    ledger[
        "decision_time"
    ]
    .gt(
        ledger[
            "policy_last_decision_utc"
        ]
    )
)

input_bar_partial = (
    ~ledger[
        "bar_complete_15m"
    ]
    .astype(bool)
)

input_bar_crosses_roll = (
    ledger[
        "crosses_roll"
    ]
    .astype(bool)
)


ledger.loc[
    no_policy_session,
    "primary_exclusion_reason",
] = (
    "NO_NYSE_POLICY_SESSION"
)

ledger.loc[
    before_policy_start
    &
    ledger[
        "primary_exclusion_reason"
    ]
    .eq(
        "ELIGIBLE"
    ),
    "primary_exclusion_reason",
] = (
    "BEFORE_NYSE_POLICY_START"
)

ledger.loc[
    after_horizon_safe_close
    &
    ledger[
        "primary_exclusion_reason"
    ]
    .eq(
        "ELIGIBLE"
    ),
    "primary_exclusion_reason",
] = (
    "AFTER_HORIZON_SAFE_CLOSE"
)

ledger.loc[
    input_bar_partial
    &
    ledger[
        "primary_exclusion_reason"
    ]
    .eq(
        "ELIGIBLE"
    ),
    "primary_exclusion_reason",
] = (
    "INPUT_BAR_PARTIAL"
)

ledger.loc[
    input_bar_crosses_roll
    &
    ledger[
        "primary_exclusion_reason"
    ]
    .eq(
        "ELIGIBLE"
    ),
    "primary_exclusion_reason",
] = (
    "INPUT_BAR_CROSSES_ROLL"
)


# ------------------------------------------------------------
# 12) Stable decision identifier
# ------------------------------------------------------------

decision_time_key = (
    ledger[
        "decision_time"
    ]
    .dt
    .strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
)

ledger[
    "decision_id"
] = (
    decision_time_key
    +
    "|instrument_id="
    +
    ledger[
        "instrument_id"
    ]
    .astype(str)
)

ledger[
    "policy_version"
] = (
    POLICY_VERSION
)


# ------------------------------------------------------------
# 13) Freeze eligible decision observations
# ------------------------------------------------------------

universe_columns = [
    "decision_id",
    "policy_version",
    "bar_start_utc",
    "decision_time",
    "decision_time_ny",
    "nyse_session_date",
    "nyse_market_open_utc",
    "nyse_market_close_utc",
    "policy_first_decision_utc",
    "policy_last_decision_utc",
    "early_close_session",
    "instrument_id",
    "active_1m_count",
    "bar_complete_15m",
    "crosses_roll",
    "dataset_condition_utc",
    "dataset_degraded_utc",
    "decision_eligible",
]


decision_universe = (
    ledger.loc[
        ledger[
            "decision_eligible"
        ],
        universe_columns,
    ]
    .sort_values(
        "decision_time"
    )
    .reset_index(
        drop=True
    )
)


# ------------------------------------------------------------
# 14) Daily policy summary
# ------------------------------------------------------------

daily_summary = (
    ledger
    .groupby(
        "nyse_session_date",
        dropna=False,
    )
    .agg(
        clock_candidate_rows=(
            "decision_id",
            "size",
        ),
        nyse_policy_session_rows=(
            "nyse_policy_session",
            "sum",
        ),
        eligible_rows=(
            "decision_eligible",
            "sum",
        ),
        partial_input_rows=(
            "bar_complete_15m",
            lambda s: int(
                (~s.astype(bool)).sum()
            ),
        ),
        degraded_context_rows=(
            "dataset_degraded_utc",
            "sum",
        ),
        early_close_session=(
            "early_close_session",
            "max",
        ),
        first_candidate_time=(
            "decision_time",
            "min",
        ),
        last_candidate_time=(
            "decision_time",
            "max",
        ),
    )
    .reset_index()
)

daily_summary[
    "excluded_rows"
] = (
    daily_summary[
        "clock_candidate_rows"
    ]
    -
    daily_summary[
        "eligible_rows"
    ]
)


exclusion_summary = (
    ledger[
        "primary_exclusion_reason"
    ]
    .value_counts(
        dropna=False
    )
    .rename_axis(
        "primary_exclusion_reason"
    )
    .rename(
        "rows"
    )
    .reset_index()
)


# ------------------------------------------------------------
# 15) Hard audit gates
# ------------------------------------------------------------

failures = []


candidate_rows = int(
    len(
        ledger
    )
)

eligible_rows = int(
    len(
        decision_universe
    )
)

excluded_rows = int(
    candidate_rows
    -
    eligible_rows
)


cell5_clock_rows = (
    cell5_audit
    .get(
        "v1_clock_integrity",
        {},
    )
    .get(
        "clock_bars"
    )
)


if (
    cell5_clock_rows is not None
    and
    candidate_rows
    !=
    int(
        cell5_clock_rows
    )
):

    failures.append(
        "Clock-candidate count mismatch: "
        f"CELL 7 {candidate_rows:,} != "
        f"CELL 5 {int(cell5_clock_rows):,}"
    )


if candidate_rows != eligible_rows + excluded_rows:

    failures.append(
        "Candidate accounting does not reconcile."
    )


if int(
    ledger[
        "primary_exclusion_reason"
    ]
    .isna()
    .sum()
) != 0:

    failures.append(
        "Missing primary exclusion reason."
    )


reason_eligible_mask = (
    ledger[
        "primary_exclusion_reason"
    ]
    .eq(
        "ELIGIBLE"
    )
)


if not np.array_equal(
    reason_eligible_mask.to_numpy(),
    ledger[
        "decision_eligible"
    ]
    .to_numpy(),
):

    failures.append(
        "ELIGIBLE reason does not match decision_eligible."
    )


if int(
    decision_universe[
        "decision_time"
    ]
    .duplicated()
    .sum()
) != 0:

    failures.append(
        "Duplicate decision_time in frozen universe."
    )


if int(
    decision_universe[
        "decision_id"
    ]
    .duplicated()
    .sum()
) != 0:

    failures.append(
        "Duplicate decision_id in frozen universe."
    )


if not decision_universe[
    "decision_time"
].is_monotonic_increasing:

    failures.append(
        "Frozen universe is not time-sorted."
    )


eligible_partial_rows = int(
    (
        decision_universe[
            "bar_complete_15m"
        ]
        .astype(bool)
        ==
        False
    )
    .sum()
)


if eligible_partial_rows != 0:

    failures.append(
        "Partial input bars entered the frozen universe: "
        f"{eligible_partial_rows:,}"
    )


eligible_roll_cross_rows = int(
    decision_universe[
        "crosses_roll"
    ]
    .astype(bool)
    .sum()
)


if eligible_roll_cross_rows != 0:

    failures.append(
        "Mixed-contract input bars entered the frozen universe: "
        f"{eligible_roll_cross_rows:,}"
    )


eligible_outside_session = int(
    (
        ~ledger.loc[
            ledger[
                "decision_eligible"
            ],
            "within_nyse_entry_policy",
        ]
    )
    .sum()
)


if eligible_outside_session != 0:

    failures.append(
        "Eligible rows outside NYSE entry policy: "
        f"{eligible_outside_session:,}"
    )


eligible_after_safe_close = int(
    (
        ledger.loc[
            ledger[
                "decision_eligible"
            ],
            "decision_time",
        ]
        >
        ledger.loc[
            ledger[
                "decision_eligible"
            ],
            "policy_last_decision_utc",
        ]
    )
    .sum()
)


if eligible_after_safe_close != 0:

    failures.append(
        "Eligible decisions violate +60m close buffer: "
        f"{eligible_after_safe_close:,}"
    )


eligible_decision_minutes = (
    decision_universe[
        "decision_time"
    ]
    .dt.minute
)


off_grid_rows = int(
    (
        ~eligible_decision_minutes
        .isin(
            [
                0,
                15,
                30,
                45,
            ]
        )
    )
    .sum()
)


if off_grid_rows != 0:

    failures.append(
        "Eligible decisions are off the 15-minute grid: "
        f"{off_grid_rows:,}"
    )


if int(
    exclusion_summary[
        "rows"
    ]
    .sum()
) != candidate_rows:

    failures.append(
        "Exclusion summary does not sum to clock candidates."
    )


# ------------------------------------------------------------
# 16) Save versioned artifacts
# ------------------------------------------------------------

ledger = ledger.sort_values(
    "decision_time"
).reset_index(
    drop=True
)

decision_universe.to_parquet(
    CELL7_UNIVERSE_PATH,
    index=False,
)

ledger.to_parquet(
    CELL7_LEDGER_PATH,
    index=False,
)

daily_summary.to_csv(
    CELL7_DAILY_PATH,
    index=False,
)


artifact_hashes = {
    "input_mes_15m_sha256": sha256_file(
        MES_15M_PATH
    ),
    "cell4_audit_sha256": sha256_file(
        CELL4_AUDIT_PATH
    ),
    "cell5_audit_sha256": sha256_file(
        CELL5_AUDIT_PATH
    ),
    "cell6_audit_sha256": sha256_file(
        CELL6_AUDIT_PATH
    ),
    "decision_universe_sha256": sha256_file(
        CELL7_UNIVERSE_PATH
    ),
    "decision_ledger_sha256": sha256_file(
        CELL7_LEDGER_PATH
    ),
    "daily_summary_sha256": sha256_file(
        CELL7_DAILY_PATH
    ),
}


# ------------------------------------------------------------
# 17) Build and save the forensic audit
# ------------------------------------------------------------

partial_candidate_rows = int(
    (
        ~ledger[
            "bar_complete_15m"
        ]
        .astype(bool)
    )
    .sum()
)

degraded_candidate_rows = int(
    ledger[
        "dataset_degraded_utc"
    ]
    .astype(bool)
    .sum()
)

degraded_eligible_rows = int(
    decision_universe[
        "dataset_degraded_utc"
    ]
    .astype(bool)
    .sum()
)

early_close_candidate_rows = int(
    ledger[
        "early_close_session"
    ]
    .astype(bool)
    .sum()
)

early_close_eligible_rows = int(
    decision_universe[
        "early_close_session"
    ]
    .astype(bool)
    .sum()
)


cell7_audit = {
    "audit_written_utc": (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    ),
    "policy_version": POLICY_VERSION,
    "status": (
        "PASS"
        if not failures
        else "FAIL"
    ),
    "upstream_binding": {
        "cell4_registry_status": (
            cell4_audit.get(
                "registry_status"
            )
        ),
        "cell5_failures": (
            cell5_audit.get(
                "failures",
                [],
            )
        ),
        "cell6_failures": (
            cell6_audit.get(
                "failures",
                [],
            )
        ),
        "cell6_unclassified_gap_events": (
            cell6_audit
            .get(
                "results",
                {},
            )
            .get(
                "primary_unclassified_events"
            )
        ),
    },
    "decision_policy": {
        "bar_minutes": BAR_MINUTES,
        "decision_time_semantics": (
            "end of completed 15-minute input bar"
        ),
        "timezone": NY_TZ,
        "clock_window_inclusive": (
            "09:45–15:00 America/New_York"
        ),
        "calendar": CALENDAR_NAME,
        "calendar_role": (
            "research/entry policy filter; not CME "
            "tradability authority"
        ),
        "label_horizon_minutes": (
            LABEL_HORIZON_MINUTES
        ),
        "scheduled_close_buffer_applied": True,
        "partial_bar_decision_eligible": False,
        "mixed_contract_bar_decision_eligible": False,
        "degraded_date_auto_exclusion": False,
        "future_return_used_for_eligibility": False,
        "future_bar_quality_used_for_eligibility": False,
    },
    "counts": {
        "input_15m_rows": int(
            len(
                mes_15m
            )
        ),
        "clock_candidate_rows": candidate_rows,
        "eligible_decision_rows": eligible_rows,
        "excluded_clock_candidate_rows": excluded_rows,
        "eligible_sessions": int(
            decision_universe[
                "nyse_session_date"
            ]
            .nunique()
        ),
        "partial_clock_candidate_rows": partial_candidate_rows,
        "eligible_partial_rows": eligible_partial_rows,
        "eligible_roll_cross_rows": eligible_roll_cross_rows,
        "degraded_clock_candidate_rows": degraded_candidate_rows,
        "degraded_eligible_rows_retained": degraded_eligible_rows,
        "early_close_clock_candidate_rows": early_close_candidate_rows,
        "early_close_eligible_rows": early_close_eligible_rows,
    },
    "time_range": {
        "first_eligible_decision_utc": (
            None
            if decision_universe.empty
            else decision_universe[
                "decision_time"
            ]
            .min()
            .isoformat()
        ),
        "last_eligible_decision_utc": (
            None
            if decision_universe.empty
            else decision_universe[
                "decision_time"
            ]
            .max()
            .isoformat()
        ),
    },
    "primary_exclusion_summary": (
        exclusion_summary
        .to_dict(
            orient="records"
        )
    ),
    "artifacts": {
        "decision_universe": str(
            CELL7_UNIVERSE_PATH
        ),
        "decision_ledger": str(
            CELL7_LEDGER_PATH
        ),
        "daily_summary": str(
            CELL7_DAILY_PATH
        ),
    },
    "sha256": artifact_hashes,
    "failures": failures,
}


with open(
    CELL7_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        cell7_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 18) Final hard gate
# ------------------------------------------------------------

if failures:

    print(
        "\nCELL 7 FAILURES"
    )
    print(
        "-" * 72
    )

    for failure in failures:

        print(
            " -",
            failure,
        )

    raise RuntimeError(
        "\nCELL 7 DECISION UNIVERSE: FAIL\n"
        f"{CELL7_AUDIT_PATH}"
    )


# ------------------------------------------------------------
# 19) Compact output
# ------------------------------------------------------------

print(
    "\n"
    +
    "=" * 72
)
print(
    "CELL 7 — POINT-IN-TIME DECISION UNIVERSE"
)
print(
    "=" * 72
)

print(
    "\n[1] POLICY"
)
print(
    "Policy version             :",
    POLICY_VERSION,
)
print(
    "Decision clock             : 09:45–15:00 America/New_York"
)
print(
    "Label-horizon close buffer : +60 minutes"
)
print(
    "Calendar role              : NYSE policy filter, not CME authority"
)
print(
    "Degraded-date exclusion    : False"
)
print(
    "Future-data eligibility    : False"
)

print(
    "\n[2] UNIVERSE COUNTS"
)
print(
    "Input 15m rows             :",
    f"{len(mes_15m):,}",
)
print(
    "Clock candidates           :",
    f"{candidate_rows:,}",
)
print(
    "Eligible decisions         :",
    f"{eligible_rows:,}",
)
print(
    "Excluded candidates        :",
    f"{excluded_rows:,}",
)
print(
    "Eligible NYSE sessions     :",
    f"{decision_universe['nyse_session_date'].nunique():,}",
)

print(
    "\n[3] INTEGRITY / CONTEXT"
)
print(
    "Partial clock candidates   :",
    f"{partial_candidate_rows:,}",
)
print(
    "Eligible partial bars      :",
    eligible_partial_rows,
)
print(
    "Eligible roll-cross bars   :",
    eligible_roll_cross_rows,
)
print(
    "Degraded eligible retained :",
    f"{degraded_eligible_rows:,}",
)
print(
    "Early-close eligible rows  :",
    f"{early_close_eligible_rows:,}",
)

print(
    "\n[4] PRIMARY EXCLUSION SUMMARY"
)
print(
    exclusion_summary
    .to_string(
        index=False
    )
)

print(
    "\n[5] TIME RANGE"
)
print(
    "First eligible decision    :",
    decision_universe[
        "decision_time"
    ]
    .min(),
)
print(
    "Last eligible decision     :",
    decision_universe[
        "decision_time"
    ]
    .max(),
)

print(
    "\n[6] SAVED ARTIFACTS"
)
print(
    "Frozen decision universe   :",
    CELL7_UNIVERSE_PATH,
)
print(
    "Full candidate ledger      :",
    CELL7_LEDGER_PATH,
)
print(
    "Daily summary              :",
    CELL7_DAILY_PATH,
)
print(
    "CELL 7 audit               :",
    CELL7_AUDIT_PATH,
)
print(
    "Universe SHA256            :",
    artifact_hashes[
        "decision_universe_sha256"
    ],
)

print(
    "\n"
    +
    "=" * 72
)
print(
    "CELL 7 DECISION UNIVERSE: PASS"
)
print(
    "=" * 72
)

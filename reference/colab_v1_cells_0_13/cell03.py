# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 3 — Supplemental Raw Audit
# Provenance Gate + Zero-Volume + Raw Time-Gap Distribution
# ============================================================
#
# PURPOSE
# -------
# Cell นี้ปิด Data Audit ที่ยังค้างอยู่ก่อน resample 1m -> 15m
#
# ทำ 3 เรื่อง:
#
#   A) PROVENANCE HARD GATE
#      ยืนยันจาก DBN metadata ว่าไฟล์คือ:
#        dataset   = GLBX.MDP3
#        schema    = ohlcv-1m
#        stype_in  = continuous
#        stype_out = instrument_id
#        symbol    = MES.v.0
#        start     = 2019-04-15
#        end       = 2026-08-01 (exclusive)
#
#   B) ZERO-VOLUME AUDIT
#      OHLCV-1m ของ Databento เป็น trade-based bars
#      จึงตรวจว่ามี bar volume == 0 หรือไม่
#
#   C) RAW TIME-GAP AUDIT
#      วิเคราะห์ระยะห่างระหว่าง raw 1-minute records
#      ก่อนทำ resample
#
# IMPORTANT
# ---------
# - ไม่มีการดาวน์โหลด Market Data ใหม่
# - ไม่ forward-fill
# - ไม่ลบ gap
# - ไม่แก้ raw baseline เดิม
# - gap > 1 นาที ไม่ถือว่า data error อัตโนมัติ
# - Cell นี้เป็น AUDIT เท่านั้น
# ============================================================


# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone

import json
import re

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 2) Paths
# ------------------------------------------------------------

PROJECT_DIR = Path(
    "/content/drive/MyDrive/Quant_Lab"
)

DATA_DIR = (
    PROJECT_DIR /
    "Data"
)

CLEAN_OUTPUT_DIR = (
    DATA_DIR /
    "MES_Clean_Pipeline_V1"
)

RUNTIME_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "runtime_source_audit.json"
)

CELL2_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell2_raw_integrity_audit.json"
)

BASELINE_PATH = (
    CLEAN_OUTPUT_DIR /
    "raw_source_baseline.json"
)

CELL3_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell3_supplemental_raw_audit.json"
)

GAP_DISTRIBUTION_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell3_gap_distribution.csv"
)

GAP_EVENTS_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell3_gap_events.parquet"
)


# ------------------------------------------------------------
# 3) Upstream dependency gates
# ------------------------------------------------------------

required_files = [
    RUNTIME_AUDIT_PATH,
    CELL2_AUDIT_PATH,
    BASELINE_PATH,
]


for required_path in required_files:

    if not required_path.exists():

        raise RuntimeError(
            "CELL 3 STOPPED — missing upstream audit file:\n\n"
            f"{required_path}\n\n"
            "ให้ Run CELL 0 → CELL 1 → CELL 2 ก่อน"
        )


# ------------------------------------------------------------
# mes_1m ต้องมาจาก full DBN decode ใน CELL 2
# เราไม่ decode ซ้ำโดยไม่จำเป็น
# ------------------------------------------------------------

if "mes_1m" not in globals():

    raise RuntimeError(
        "CELL 3 STOPPED — mes_1m not found in runtime.\n\n"
        "ให้ Run CELL 2 ก่อน แล้ว Run CELL 3 "
        "โดยไม่ Restart session"
    )


if not isinstance(
    mes_1m,
    pd.DataFrame,
):

    raise RuntimeError(
        "CELL 3 STOPPED — mes_1m is not a DataFrame"
    )


if not isinstance(
    mes_1m.index,
    pd.DatetimeIndex,
):

    raise RuntimeError(
        "CELL 3 STOPPED — mes_1m index "
        "is not DatetimeIndex"
    )


# ------------------------------------------------------------
# 4) Load upstream audit artifacts
# ------------------------------------------------------------

with open(
    RUNTIME_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    runtime_audit = (
        json.load(f)
    )


with open(
    CELL2_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:

    cell2_audit = (
        json.load(f)
    )


with open(
    BASELINE_PATH,
    "r",
    encoding="utf-8",
) as f:

    baseline = (
        json.load(f)
    )


# ------------------------------------------------------------
# 5) Bind CELL 3 to exact frozen raw source
#
# Cell 3 ต้อง audit DBN identity เดียวกับ baseline
# ------------------------------------------------------------

runtime_raw = (
    runtime_audit[
        "raw_file"
    ]
)

baseline_raw = (
    baseline[
        "raw_file"
    ]
)


identity_failures = []


if (
    runtime_raw[
        "sha256"
    ]
    !=
    baseline_raw[
        "sha256"
    ]
):

    identity_failures.append(
        "Runtime raw SHA256 != frozen baseline SHA256"
    )


if (
    int(
        runtime_raw[
            "size_bytes"
        ]
    )
    !=
    int(
        baseline_raw[
            "size_bytes"
        ]
    )
):

    identity_failures.append(
        "Runtime raw size != frozen baseline size"
    )


if identity_failures:

    raise RuntimeError(
        "CELL 3 RAW IDENTITY GATE: FAIL\n\n"
        + "\n".join(
            identity_failures
        )
    )


# ------------------------------------------------------------
# 6) Metadata from CELL 1
# ------------------------------------------------------------

metadata = (
    runtime_audit.get(
        "dbn_metadata",
        {}
    )
)

mapping_summary = (
    runtime_audit
    .get(
        "dbn_metadata_bulky_summary",
        {}
    )
    .get(
        "mappings",
        {}
    )
)


# ------------------------------------------------------------
# 7) Normalization helpers
#
# รองรับทั้ง:
#   "ohlcv-1m"
#   "Schema.OHLCV_1M"
#
# และ:
#   "continuous"
#   "SType.CONTINUOUS"
# ------------------------------------------------------------

def normalize_token(value):

    if value is None:
        return None

    text = (
        str(value)
        .strip()
        .lower()
    )

    # ถ้าเป็น enum เช่น Schema.OHLCV_1M
    if "." in text:
        text = text.split(".")[-1]

    # ตัด punctuation เพื่อเทียบ semantic token
    return re.sub(
        r"[^a-z0-9]+",
        "",
        text,
    )


def normalize_dataset(value):

    if value is None:
        return None

    text = (
        str(value)
        .strip()
    )

    # รองรับ enum-like representation
    if text.lower().startswith("dataset."):

        text = (
            text
            .split(".", 1)[1]
        )

    return text.upper()


def normalize_symbols(value):

    if value is None:
        return []

    if isinstance(
        value,
        (list, tuple, set),
    ):

        return [
            str(x)
            for x in value
        ]

    return [
        str(value)
    ]


def metadata_timestamp_utc(value):

    if value is None:
        return None


    # DBN metadata อาจเก็บ timestamp เป็น integer nanoseconds
    if isinstance(
        value,
        (int, np.integer),
    ):

        return pd.to_datetime(
            int(value),
            unit="ns",
            utc=True,
        )


    # หรือเป็น string/datetime
    return pd.to_datetime(
        value,
        utc=True,
    )


# ------------------------------------------------------------
# 8) Expected provenance
# ------------------------------------------------------------

EXPECTED_PROVENANCE = {

    "dataset":
        "GLBX.MDP3",

    "schema":
        "ohlcv1m",

    "stype_in":
        "continuous",

    "stype_out":
        "instrumentid",

    "symbol":
        "MES.v.0",

    "start":
        pd.Timestamp(
            "2019-04-15T00:00:00Z"
        ),

    "end":
        pd.Timestamp(
            "2026-08-01T00:00:00Z"
        ),
}


# ------------------------------------------------------------
# 9) Observed provenance
# ------------------------------------------------------------

observed_dataset = (
    normalize_dataset(
        metadata.get(
            "dataset"
        )
    )
)

observed_schema = (
    normalize_token(
        metadata.get(
            "schema"
        )
    )
)

observed_stype_in = (
    normalize_token(
        metadata.get(
            "stype_in"
        )
    )
)

observed_stype_out = (
    normalize_token(
        metadata.get(
            "stype_out"
        )
    )
)

observed_symbols = (
    normalize_symbols(
        metadata.get(
            "symbols"
        )
    )
)


try:

    observed_start = (
        metadata_timestamp_utc(
            metadata.get(
                "start"
            )
        )
    )

except Exception as e:

    observed_start = None

    provenance_timestamp_start_error = (
        f"{type(e).__name__}: {e}"
    )

else:

    provenance_timestamp_start_error = None


try:

    observed_end = (
        metadata_timestamp_utc(
            metadata.get(
                "end"
            )
        )
    )

except Exception as e:

    observed_end = None

    provenance_timestamp_end_error = (
        f"{type(e).__name__}: {e}"
    )

else:

    provenance_timestamp_end_error = None


mapping_first_key = (
    mapping_summary.get(
        "first_symbol_key"
    )
)

mapping_last_key = (
    mapping_summary.get(
        "last_symbol_key"
    )
)


# ------------------------------------------------------------
# 10) Provenance hard gate
# ------------------------------------------------------------

provenance_checks = {

    "dataset":
        (
            observed_dataset
            ==
            EXPECTED_PROVENANCE[
                "dataset"
            ]
        ),

    "schema":
        (
            observed_schema
            ==
            EXPECTED_PROVENANCE[
                "schema"
            ]
        ),

    "stype_in":
        (
            observed_stype_in
            ==
            EXPECTED_PROVENANCE[
                "stype_in"
            ]
        ),

    "stype_out":
        (
            observed_stype_out
            ==
            EXPECTED_PROVENANCE[
                "stype_out"
            ]
        ),

    "symbol_in_metadata":
        (
            EXPECTED_PROVENANCE[
                "symbol"
            ]
            in
            observed_symbols
        ),

    "symbol_in_mapping_first":
        (
            str(
                mapping_first_key
            )
            ==
            EXPECTED_PROVENANCE[
                "symbol"
            ]
        ),

    "symbol_in_mapping_last":
        (
            str(
                mapping_last_key
            )
            ==
            EXPECTED_PROVENANCE[
                "symbol"
            ]
        ),

    "start":
        (
            observed_start
            ==
            EXPECTED_PROVENANCE[
                "start"
            ]
        ),

    "end_exclusive":
        (
            observed_end
            ==
            EXPECTED_PROVENANCE[
                "end"
            ]
        ),
}


failed_provenance = [

    key
    for key, passed
    in provenance_checks.items()

    if not passed
]


# ------------------------------------------------------------
# 11) Print actual provenance values
#
# รอบนี้เราไม่พิมพ์แค่ชื่อ field
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "DBN PROVENANCE HARD GATE"
)

print(
    "=" * 72
)


print(
    "dataset          :",
    metadata.get(
        "dataset"
    )
)

print(
    "schema           :",
    metadata.get(
        "schema"
    )
)

print(
    "stype_in         :",
    metadata.get(
        "stype_in"
    )
)

print(
    "stype_out        :",
    metadata.get(
        "stype_out"
    )
)

print(
    "symbols          :",
    metadata.get(
        "symbols"
    )
)

print(
    "start            :",
    observed_start
)

print(
    "end (exclusive)  :",
    observed_end
)

print(
    "mapping first key:",
    mapping_first_key
)

print(
    "mapping last key :",
    mapping_last_key
)


print(
    "\nProvenance checks:"
)


for (
    check_name,
    passed,
) in (
    provenance_checks.items()
):

    print(
        f"  {check_name:25s}",
        "PASS"
        if passed
        else "FAIL"
    )


if failed_provenance:

    raise RuntimeError(
        "\nCELL 3 PROVENANCE GATE: FAIL\n\n"
        "Failed fields:\n  - "
        +
        "\n  - ".join(
            failed_provenance
        )
        +
        "\n\n"
        "ห้าม resample จนกว่าจะตรวจ provenance จบ"
    )


print(
    "\nDBN PROVENANCE GATE: PASS"
)


# ------------------------------------------------------------
# 12) Zero-volume audit
# ------------------------------------------------------------

if "volume" not in mes_1m.columns:

    raise RuntimeError(
        "CELL 3 STOPPED — volume column not found"
    )


zero_volume_count = int(
    (
        mes_1m[
            "volume"
        ]
        ==
        0
    ).sum()
)


positive_volume_count = int(
    (
        mes_1m[
            "volume"
        ]
        >
        0
    ).sum()
)


print(
    "\n"
    + "=" * 72
)

print(
    "ZERO-VOLUME AUDIT"
)

print(
    "=" * 72
)


print(
    "Total bars       :",
    f"{len(mes_1m):,}"
)

print(
    "Volume > 0 bars  :",
    f"{positive_volume_count:,}"
)

print(
    "Volume == 0 bars :",
    f"{zero_volume_count:,}"
)


# สำหรับ raw Databento OHLCV-1m
# เราต้องการยืนยันว่าไม่มี synthetic zero-volume bar
if zero_volume_count != 0:

    raise RuntimeError(
        "\nCELL 3 ZERO-VOLUME GATE: FAIL\n\n"
        f"พบ volume == 0 จำนวน {zero_volume_count:,} bars\n\n"
        "ห้าม resample จนกว่าจะตรวจสาเหตุ"
    )


print(
    "ZERO-VOLUME GATE: PASS"
)


# ------------------------------------------------------------
# 13) Timestamp alignment audit
#
# OHLCV-1m timestamp ควรอยู่บน minute boundary
# ------------------------------------------------------------

MINUTE_NS = int(
    pd.Timedelta(
        minutes=1
    ).value
)


index_ns = (
    mes_1m.index.asi8
)


minute_alignment_violations = int(
    np.count_nonzero(
        index_ns
        %
        MINUTE_NS
    )
)


if minute_alignment_violations != 0:

    raise RuntimeError(
        "\nCELL 3 MINUTE-ALIGNMENT GATE: FAIL\n\n"
        f"พบ timestamp ที่ไม่ตรง minute boundary "
        f"{minute_alignment_violations:,} rows"
    )


# ------------------------------------------------------------
# 14) Calculate raw time gaps efficiently
#
# ใช้ numpy.diff บน nanoseconds
# ไม่สร้าง reindex / synthetic bars
# ------------------------------------------------------------

delta_ns = (
    np.diff(
        index_ns
    )
)


non_positive_gap_count = int(
    np.count_nonzero(
        delta_ns
        <=
        0
    )
)


if non_positive_gap_count != 0:

    raise RuntimeError(
        "\nCELL 3 GAP ORDER GATE: FAIL\n\n"
        f"พบ non-positive gaps "
        f"{non_positive_gap_count:,}"
    )


non_integer_minute_gap_count = int(
    np.count_nonzero(
        delta_ns
        %
        MINUTE_NS
    )
)


if non_integer_minute_gap_count != 0:

    raise RuntimeError(
        "\nCELL 3 GAP ALIGNMENT GATE: FAIL\n\n"
        f"พบ gap ที่ไม่ใช่จำนวนเต็มนาที "
        f"{non_integer_minute_gap_count:,}"
    )


gap_minutes = (
    delta_ns
    //
    MINUTE_NS
).astype(
    np.int64
)


# ------------------------------------------------------------
# 15) Gap distribution
# ------------------------------------------------------------

unique_gap_minutes, gap_counts = (
    np.unique(
        gap_minutes,
        return_counts=True,
    )
)


gap_distribution = pd.DataFrame(
    {
        "gap_minutes":
            unique_gap_minutes,

        "count":
            gap_counts,
    }
)


gap_distribution[
    "gap_duration"
] = pd.to_timedelta(
    gap_distribution[
        "gap_minutes"
    ],
    unit="m",
).astype(
    str
)


gap_distribution[
    "pct_of_transitions"
] = (
    gap_distribution[
        "count"
    ]
    /
    len(
        gap_minutes
    )
    *
    100.0
)


# เรียงตามจำนวนครั้งมากที่สุด
gap_distribution_by_count = (
    gap_distribution
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
    .reset_index(
        drop=True
    )
)


gap_distribution.to_csv(
    GAP_DISTRIBUTION_PATH,
    index=False,
)


# ------------------------------------------------------------
# 16) Gap summary
# ------------------------------------------------------------

one_minute_count = int(
    np.count_nonzero(
        gap_minutes
        ==
        1
    )
)


gap_gt_1_mask = (
    gap_minutes
    >
    1
)


gap_gt_1_count = int(
    np.count_nonzero(
        gap_gt_1_mask
    )
)


gap_gt_1_pct = (
    gap_gt_1_count
    /
    len(
        gap_minutes
    )
    *
    100.0
)


max_gap_minutes = int(
    gap_minutes.max()
)


# ------------------------------------------------------------
# 17) Build event-level gap table
#
# เก็บเฉพาะ transition ที่ > 1 นาที
# ------------------------------------------------------------

gap_positions = (
    np.flatnonzero(
        gap_gt_1_mask
    )
)


prev_positions = (
    gap_positions
)

next_positions = (
    gap_positions
    +
    1
)


gap_events = pd.DataFrame(
    {
        "prev_timestamp":
            mes_1m.index[
                prev_positions
            ],

        "next_timestamp":
            mes_1m.index[
                next_positions
            ],

        "gap_minutes":
            gap_minutes[
                gap_positions
            ],
    }
)


# ------------------------------------------------------------
# Instrument IDs around each gap
# ------------------------------------------------------------

if (
    "instrument_id"
    in mes_1m.columns
):

    instrument_values = (
        mes_1m[
            "instrument_id"
        ].to_numpy()
    )


    gap_events[
        "instrument_before"
    ] = (
        instrument_values[
            prev_positions
        ]
    )


    gap_events[
        "instrument_after"
    ] = (
        instrument_values[
            next_positions
        ]
    )


    gap_events[
        "roll_boundary"
    ] = (
        gap_events[
            "instrument_before"
        ].to_numpy()
        !=
        gap_events[
            "instrument_after"
        ].to_numpy()
    )


else:

    gap_events[
        "instrument_before"
    ] = None

    gap_events[
        "instrument_after"
    ] = None

    gap_events[
        "roll_boundary"
    ] = False


gap_events.to_parquet(
    GAP_EVENTS_PATH,
    index=False,
)


gap_events_crossing_roll = int(
    gap_events[
        "roll_boundary"
    ].sum()
)


# ------------------------------------------------------------
# 18) Specific gap sizes worth surfacing
#
# ไม่ hardcode ว่าต้องมีจำนวนเท่าใด
# แค่รายงาน observation จริง
# ------------------------------------------------------------

WATCH_GAPS_MINUTES = [
    2,
    3,
    16,
    61,
]


watch_gap_counts = {}


for minutes in WATCH_GAPS_MINUTES:

    watch_gap_counts[
        str(minutes)
    ] = int(
        np.count_nonzero(
            gap_minutes
            ==
            minutes
        )
    )


# ------------------------------------------------------------
# 19) Load roll facts from CELL 2 for cross-reference
# ------------------------------------------------------------

decoded_cell2 = (
    cell2_audit.get(
        "decoded",
        {}
    )
)


unique_instrument_ids = (
    decoded_cell2.get(
        "unique_instrument_ids"
    )
)

roll_transition_count = (
    decoded_cell2.get(
        "roll_transition_count"
    )
)

metadata_mapping_intervals = (
    decoded_cell2.get(
        "metadata_mapping_intervals"
    )
)


# ------------------------------------------------------------
# 20) Supplemental audit artifact
# ------------------------------------------------------------

cell3_audit = {

    "audit_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "raw_identity_binding": {

        "sha256":
            runtime_raw[
                "sha256"
            ],

        "size_bytes":
            int(
                runtime_raw[
                    "size_bytes"
                ]
            ),

        "matches_frozen_baseline":
            True,
    },


    "provenance": {

        "expected": {
            "dataset":
                EXPECTED_PROVENANCE[
                    "dataset"
                ],

            "schema":
                "ohlcv-1m",

            "stype_in":
                EXPECTED_PROVENANCE[
                    "stype_in"
                ],

            "stype_out":
                "instrument_id",

            "symbol":
                EXPECTED_PROVENANCE[
                    "symbol"
                ],

            "start":
                EXPECTED_PROVENANCE[
                    "start"
                ].isoformat(),

            "end_exclusive":
                EXPECTED_PROVENANCE[
                    "end"
                ].isoformat(),
        },


        "observed": {

            "dataset":
                metadata.get(
                    "dataset"
                ),

            "schema":
                metadata.get(
                    "schema"
                ),

            "stype_in":
                metadata.get(
                    "stype_in"
                ),

            "stype_out":
                metadata.get(
                    "stype_out"
                ),

            "symbols":
                metadata.get(
                    "symbols"
                ),

            "start":
                (
                    observed_start.isoformat()
                    if observed_start is not None
                    else None
                ),

            "end":
                (
                    observed_end.isoformat()
                    if observed_end is not None
                    else None
                ),

            "mapping_first_symbol":
                mapping_first_key,

            "mapping_last_symbol":
                mapping_last_key,

            "mapping_intervals":
                mapping_summary.get(
                    "total_mapping_intervals"
                ),
        },


        "checks":
            provenance_checks,

        "status":
            "PASS",
    },


    "zero_volume": {

        "total_bars":
            int(
                len(
                    mes_1m
                )
            ),

        "positive_volume_bars":
            positive_volume_count,

        "zero_volume_bars":
            zero_volume_count,

        "status":
            "PASS",
    },


    "raw_gap_audit": {

        "total_transitions":
            int(
                len(
                    gap_minutes
                )
            ),

        "one_minute_transitions":
            one_minute_count,

        "gap_gt_1_minute_events":
            gap_gt_1_count,

        "gap_gt_1_minute_pct":
            float(
                gap_gt_1_pct
            ),

        "maximum_gap_minutes":
            max_gap_minutes,

        "minute_alignment_violations":
            minute_alignment_violations,

        "non_integer_minute_gaps":
            non_integer_minute_gap_count,

        "non_positive_gaps":
            non_positive_gap_count,

        "watch_gap_counts":
            watch_gap_counts,

        "gap_events_crossing_roll":
            gap_events_crossing_roll,

        "distribution_file":
            str(
                GAP_DISTRIBUTION_PATH
            ),

        "event_file":
            str(
                GAP_EVENTS_PATH
            ),
    },


    "roll_cross_reference": {

        "unique_instrument_ids":
            unique_instrument_ids,

        "roll_transition_count":
            roll_transition_count,

        "metadata_mapping_intervals":
            metadata_mapping_intervals,
    },
}


with open(
    CELL3_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        cell3_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 21) Output — Raw gap distribution
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "RAW 1-MINUTE TIME-GAP AUDIT"
)

print(
    "=" * 72
)


print(
    "Total timestamp transitions :",
    f"{len(gap_minutes):,}"
)

print(
    "Exactly 1-minute transitions:",
    f"{one_minute_count:,}"
)

print(
    "Gap > 1 minute events       :",
    f"{gap_gt_1_count:,}"
)

print(
    "Gap > 1 minute %            :",
    f"{gap_gt_1_pct:.4f}%"
)

print(
    "Maximum observed gap        :",
    pd.Timedelta(
        minutes=max_gap_minutes
    )
)

print(
    "Minute alignment violations :",
    minute_alignment_violations
)

print(
    "Non-integer-minute gaps     :",
    non_integer_minute_gap_count
)

print(
    "Gap events crossing roll    :",
    gap_events_crossing_roll
)


# ------------------------------------------------------------
# 22) Output — watched gap sizes
# ------------------------------------------------------------

print(
    "\nSelected gap sizes:"
)


for minutes in WATCH_GAPS_MINUTES:

    count = (
        watch_gap_counts[
            str(minutes)
        ]
    )

    print(
        f"  {minutes:4d} minute gap : "
        f"{count:,}"
    )


# ------------------------------------------------------------
# 23) Output — most common gap durations
# ------------------------------------------------------------

print(
    "\nMost common gap durations:"
)


print(
    gap_distribution_by_count[
        [
            "gap_minutes",
            "gap_duration",
            "count",
            "pct_of_transitions",
        ]
    ]
    .head(15)
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 24) Example gap events
#
# แสดงเฉพาะตัวอย่างเพื่อให้มนุษย์อ่านได้
# full list ถูก save ลง parquet แล้ว
# ------------------------------------------------------------

print(
    "\nFirst 10 gap events (>1 minute):"
)


if len(
    gap_events
) > 0:

    print(
        gap_events
        .head(10)
        .to_string(
            index=False
        )
    )

else:

    print(
        "None"
    )


# ------------------------------------------------------------
# 25) Artifact locations
# ------------------------------------------------------------

print(
    "\n=== CELL 3 AUDIT ARTIFACTS ==="
)

print(
    "Supplemental audit :",
    CELL3_AUDIT_PATH
)

print(
    "Gap distribution   :",
    GAP_DISTRIBUTION_PATH
)

print(
    "Gap events         :",
    GAP_EVENTS_PATH
)


# ------------------------------------------------------------
# 26) Final gate
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "CELL 3 SUPPLEMENTAL RAW AUDIT: PASS"
)

print(
    "=" * 72
)

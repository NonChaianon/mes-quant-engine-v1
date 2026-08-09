# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 2 — Raw Decode, Integrity & DBN↔Parquet Cross-check
# ============================================================
#
# PURPOSE
# -------
# 1) Decode DBN ทั้งไฟล์
# 2) ตรวจโครงสร้างข้อมูล 1-minute
# 3) ตรวจ timestamp / duplicates / OHLCV / instrument_id
# 4) เทียบ DBN กับ parquet เก่าทีละ observation
# 5) บันทึก Raw Integrity Audit
# 6) Freeze raw_source_baseline.json อัตโนมัติเมื่อทุก Gate ผ่าน
#
# IMPORTANT
# ---------
# ไม่มีการดาวน์โหลด Market Data ใหม่
# ทุกอย่างอ่านจากไฟล์ใน Google Drive
# ============================================================
# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------
from datetime import datetime, timezone
from pathlib import Path
import gc
import json
import numpy as np
import pandas as pd
import databento as db
# ------------------------------------------------------------
# 2) Required paths
#
# ตั้งเองอีกครั้งเพื่อไม่พึ่งตัวแปรลอยจาก Runtime
# ------------------------------------------------------------
PROJECT_DIR = Path(
    "/content/drive/MyDrive/Quant_Lab"
)
DATA_DIR = (
    PROJECT_DIR /
    "Data"
)
MES_DBN_PATH = (
    DATA_DIR /
    "MES_2019_2026_1m.dbn.zst"
)
OLD_PARQUET_PATH = (
    DATA_DIR /
    "MES_2019_2026_1m.parquet"
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
# ------------------------------------------------------------
# 3) Dependency / source gates
# ------------------------------------------------------------
if not MES_DBN_PATH.exists():
    raise FileNotFoundError(
        "CELL 2 STOPPED — RAW DBN ไม่พบ\n\n"
        f"{MES_DBN_PATH}"
    )
if not RUNTIME_AUDIT_PATH.exists():
    raise RuntimeError(
        "CELL 2 STOPPED — ไม่พบ runtime_source_audit.json\n\n"
        "ให้ Run CELL 1 ให้ผ่านก่อน"
    )
HAS_OLD_PARQUET = (
    OLD_PARQUET_PATH.exists()
)
# ------------------------------------------------------------
# 4) Load CELL 1 audit
# ------------------------------------------------------------
with open(
    RUNTIME_AUDIT_PATH,
    "r",
    encoding="utf-8",
) as f:
    runtime_audit = (
        json.load(f)
    )
raw_identity = (
    runtime_audit[
        "raw_file"
    ]
)
# ------------------------------------------------------------
# 5) Full DBN decode
#
# ตรงนี้คือการอ่าน record จริงทั้งไฟล์
# ถ้า DBN / compression เสียจน decode ไม่ได้
# จะหยุดตรงนี้
# ------------------------------------------------------------
print(
    "Decoding full DBN file..."
)
try:
    dbn_store_cell2 = (
        db.DBNStore.from_file(
            MES_DBN_PATH
        )
    )
    mes_1m = (
        dbn_store_cell2.to_df()
    )
except Exception as e:
    raise RuntimeError(
        "FULL DBN DECODE FAILED\n\n"
        f"{type(e).__name__}: {e}\n\n"
        "Raw source ยังไม่ผ่าน integrity gate"
    ) from e
print(
    "DBN decode completed."
)
# ------------------------------------------------------------
# 6) General structure
# ------------------------------------------------------------
failures = []
decoded_rows = (
    len(mes_1m)
)
decoded_columns = (
    list(mes_1m.columns)
)
if decoded_rows == 0:
    failures.append(
        "Decoded DBN contains zero rows"
    )
if not isinstance(
    mes_1m.index,
    pd.DatetimeIndex,
):
    failures.append(
        "DBN index is not pandas.DatetimeIndex"
    )
# ------------------------------------------------------------
# 7) Timestamp audit
# ------------------------------------------------------------
if isinstance(
    mes_1m.index,
    pd.DatetimeIndex,
):
    index_name = (
        mes_1m.index.name
    )
    timezone_name = (
        str(mes_1m.index.tz)
        if mes_1m.index.tz is not None
        else None
    )
    first_ts = (
        mes_1m.index[0]
        if decoded_rows
        else None
    )
    last_ts = (
        mes_1m.index[-1]
        if decoded_rows
        else None
    )
    is_monotonic = (
        mes_1m.index.is_monotonic_increasing
    )
    duplicate_timestamps = int(
        mes_1m.index.duplicated().sum()
    )
    if mes_1m.index.tz is None:
        failures.append(
            "DBN timestamp index is timezone-naive"
        )
    elif (
        str(mes_1m.index.tz).upper()
        !=
        "UTC"
    ):
        failures.append(
            "DBN timestamp timezone is not UTC: "
            f"{mes_1m.index.tz}"
        )
    if not is_monotonic:
        failures.append(
            "DBN timestamps are not monotonic increasing"
        )
    if duplicate_timestamps != 0:
        failures.append(
            "DBN contains duplicate timestamps: "
            f"{duplicate_timestamps}"
        )
else:
    index_name = None
    timezone_name = None
    first_ts = None
    last_ts = None
    is_monotonic = False
    duplicate_timestamps = None
# ------------------------------------------------------------
# 8) Required market-data columns
# ------------------------------------------------------------
OHLCV_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]
CRITICAL_COLUMNS = [
    "instrument_id",
    *OHLCV_COLUMNS,
]
missing_critical_columns = [
    col
    for col in CRITICAL_COLUMNS
    if col not in mes_1m.columns
]
if missing_critical_columns:
    failures.append(
        "Missing critical DBN columns: "
        + ", ".join(
            missing_critical_columns
        )
    )
# ------------------------------------------------------------
# 9) OHLCV integrity
# ------------------------------------------------------------
ohlcv_nan_counts = {}
if not missing_critical_columns:
    ohlcv_nan_counts = {
        col:
            int(
                mes_1m[
                    col
                ].isna().sum()
            )
        for col in OHLCV_COLUMNS
    }
    total_ohlcv_nan = (
        sum(
            ohlcv_nan_counts.values()
        )
    )
    if total_ohlcv_nan != 0:
        failures.append(
            "OHLCV contains NaN values: "
            f"{ohlcv_nan_counts}"
        )
    # --------------------------------------------------------
    # Price structure
    #
    # ทุก bar:
    # high ต้องไม่ต่ำกว่า open/close/low
    # low ต้องไม่สูงกว่า open/close/high
    # --------------------------------------------------------
    high_violation = int(
        (
            (
                mes_1m["high"]
                <
                mes_1m[
                    ["open", "close", "low"]
                ].max(axis=1)
            )
        ).sum()
    )
    low_violation = int(
        (
            (
                mes_1m["low"]
                >
                mes_1m[
                    ["open", "close", "high"]
                ].min(axis=1)
            )
        ).sum()
    )
    negative_volume = int(
        (
            mes_1m["volume"]
            <
            0
        ).sum()
    )
    if high_violation:
        failures.append(
            f"OHLC high violations: {high_violation}"
        )
    if low_violation:
        failures.append(
            f"OHLC low violations: {low_violation}"
        )
    if negative_volume:
        failures.append(
            f"Negative volume rows: {negative_volume}"
        )
else:
    high_violation = None
    low_violation = None
    negative_volume = None
# ------------------------------------------------------------
# 10) Instrument / roll audit
# ------------------------------------------------------------
if (
    "instrument_id"
    in mes_1m.columns
):
    instrument_nan = int(
        mes_1m[
            "instrument_id"
        ].isna().sum()
    )
    unique_instruments = int(
        mes_1m[
            "instrument_id"
        ].nunique(
            dropna=True
        )
    )
    instrument_array = (
        mes_1m[
            "instrument_id"
        ].to_numpy()
    )
    if len(
        instrument_array
    ) > 1:
        roll_transition_count = int(
            np.count_nonzero(
                instrument_array[1:]
                !=
                instrument_array[:-1]
            )
        )
    else:
        roll_transition_count = 0
    if instrument_nan:
        failures.append(
            "instrument_id contains NaN: "
            f"{instrument_nan}"
        )
else:
    instrument_nan = None
    unique_instruments = None
    roll_transition_count = None
# ------------------------------------------------------------
# 11) Dtype record
#
# Dtype ถูกบันทึกไว้
# แต่ dtype ต่างกันกับ parquet
# ไม่ได้ถือว่า values ต่างกันโดยอัตโนมัติ
# ------------------------------------------------------------
dbn_dtypes = {
    col:
        str(dtype)
    for col, dtype
    in mes_1m.dtypes.items()
}
# ------------------------------------------------------------
# 12) DBN ↔ OLD PARQUET CROSS-CHECK
# ------------------------------------------------------------
cross_check = {
    "status":
        "SKIPPED",
    "reason":
        None,
    "compared_columns":
        [],
    "column_results":
        {},
    "index_equal":
        None,
    "rows_equal":
        None,
}
if HAS_OLD_PARQUET:
    print(
        "Loading old parquet for cross-check..."
    )
    try:
        old_1m = pd.read_parquet(
            OLD_PARQUET_PATH
        )
    except Exception as e:
        failures.append(
            "Old parquet could not be read: "
            f"{type(e).__name__}: {e}"
        )
        old_1m = None
    if old_1m is not None:
        cross_check[
            "status"
        ] = "RUNNING"
        # ----------------------------------------------------
        # Row-count comparison
        # ----------------------------------------------------
        cross_check[
            "dbn_rows"
        ] = int(
            len(mes_1m)
        )
        cross_check[
            "parquet_rows"
        ] = int(
            len(old_1m)
        )
        cross_check[
            "rows_equal"
        ] = (
            len(mes_1m)
            ==
            len(old_1m)
        )
        if not cross_check[
            "rows_equal"
        ]:
            failures.append(
                "DBN ↔ Parquet row count mismatch: "
                f"{len(mes_1m):,} vs {len(old_1m):,}"
            )
        # ----------------------------------------------------
        # Timestamp comparison
        # ----------------------------------------------------
        if (
            isinstance(
                old_1m.index,
                pd.DatetimeIndex,
            )
            and
            isinstance(
                mes_1m.index,
                pd.DatetimeIndex,
            )
            and
            len(old_1m)
            ==
            len(mes_1m)
        ):
            index_equal = bool(
                np.array_equal(
                    mes_1m.index.asi8,
                    old_1m.index.asi8,
                )
            )
        else:
            index_equal = False
        cross_check[
            "index_equal"
        ] = index_equal
        cross_check[
            "dbn_index_timezone"
        ] = (
            str(
                mes_1m.index.tz
            )
            if isinstance(
                mes_1m.index,
                pd.DatetimeIndex,
            )
            else None
        )
        cross_check[
            "parquet_index_timezone"
        ] = (
            str(
                old_1m.index.tz
            )
            if isinstance(
                old_1m.index,
                pd.DatetimeIndex,
            )
            else None
        )
        if not index_equal:
            failures.append(
                "DBN ↔ Parquet timestamp index mismatch"
            )
        # ----------------------------------------------------
        # Critical column availability
        # ----------------------------------------------------
        missing_dbn_compare = [
            col
            for col in CRITICAL_COLUMNS
            if col not in mes_1m.columns
        ]
        missing_parquet_compare = [
            col
            for col in CRITICAL_COLUMNS
            if col not in old_1m.columns
        ]
        cross_check[
            "missing_dbn_columns"
        ] = (
            missing_dbn_compare
        )
        cross_check[
            "missing_parquet_columns"
        ] = (
            missing_parquet_compare
        )
        if missing_dbn_compare:
            failures.append(
                "DBN cross-check columns missing: "
                + ", ".join(
                    missing_dbn_compare
                )
            )
        if missing_parquet_compare:
            failures.append(
                "Old parquet cross-check columns missing: "
                + ", ".join(
                    missing_parquet_compare
                )
            )
        # ----------------------------------------------------
        # Observation-by-observation comparison
        #
        # สำคัญ:
        # ใช้ .to_numpy()
        #
        # dtype ต่างกันไม่ทำให้ FAIL
        # ถ้าค่าจริงยังเท่ากัน
        # ----------------------------------------------------
        if (
            not missing_dbn_compare
            and
            not missing_parquet_compare
            and
            cross_check[
                "rows_equal"
            ]
            and
            index_equal
        ):
            cross_check[
                "compared_columns"
            ] = CRITICAL_COLUMNS.copy()
            for col in CRITICAL_COLUMNS:
                dbn_values = (
                    mes_1m[
                        col
                    ].to_numpy()
                )
                parquet_values = (
                    old_1m[
                        col
                    ].to_numpy()
                )
                try:
                    arrays_equal = bool(
                        np.array_equal(
                            dbn_values,
                            parquet_values,
                            equal_nan=True,
                        )
                    )
                except TypeError:
                    arrays_equal = bool(
                        np.array_equal(
                            dbn_values,
                            parquet_values,
                        )
                    )
                # --------------------------------------------
                # Count / sample mismatches
                # --------------------------------------------
                if arrays_equal:
                    mismatch_count = 0
                    mismatch_examples = []
                else:
                    # numeric comparison
                    if (
                        np.issubdtype(
                            dbn_values.dtype,
                            np.number,
                        )
                        and
                        np.issubdtype(
                            parquet_values.dtype,
                            np.number,
                        )
                    ):
                        equal_mask = (
                            dbn_values
                            ==
                            parquet_values
                        )
                        # NaN == NaN สำหรับ audit
                        try:
                            equal_mask = (
                                equal_mask
                                |
                                (
                                    np.isnan(
                                        dbn_values
                                    )
                                    &
                                    np.isnan(
                                        parquet_values
                                    )
                                )
                            )
                        except TypeError:
                            pass
                    else:
                        equal_mask = (
                            dbn_values
                            ==
                            parquet_values
                        )
                    mismatch_positions = (
                        np.flatnonzero(
                            ~equal_mask
                        )
                    )
                    mismatch_count = int(
                        len(
                            mismatch_positions
                        )
                    )
                    mismatch_examples = []
                    for pos in (
                        mismatch_positions[:5]
                    ):
                        mismatch_examples.append(
                            {
                                "position":
                                    int(pos),
                                "timestamp":
                                    str(
                                        mes_1m.index[
                                            pos
                                        ]
                                    ),
                                "dbn":
                                    str(
                                        dbn_values[
                                            pos
                                        ]
                                    ),
                                "parquet":
                                    str(
                                        parquet_values[
                                            pos
                                        ]
                                    ),
                            }
                        )
                cross_check[
                    "column_results"
                ][col] = {
                    "dbn_dtype":
                        str(
                            mes_1m[
                                col
                            ].dtype
                        ),
                    "parquet_dtype":
                        str(
                            old_1m[
                                col
                            ].dtype
                        ),
                    "values_equal":
                        arrays_equal,
                    "mismatch_count":
                        mismatch_count,
                    "examples":
                        mismatch_examples,
                }
                if not arrays_equal:
                    failures.append(
                        f"DBN ↔ Parquet values mismatch "
                        f"in '{col}': "
                        f"{mismatch_count:,} rows"
                    )
        # ----------------------------------------------------
        # Optional shared columns
        #
        # บันทึกไว้เพื่อดูว่าไฟล์สองฝั่งมี schema ต่างกันไหม
        # แต่ไม่ใช้เป็น Critical Gate
        # ----------------------------------------------------
        cross_check[
            "dbn_columns"
        ] = list(
            mes_1m.columns
        )
        cross_check[
            "parquet_columns"
        ] = list(
            old_1m.columns
        )
        # ----------------------------------------------------
        # Final cross-check state
        # ----------------------------------------------------
        parquet_related_failures = [
            failure
            for failure
            in failures
            if (
                "Parquet"
                in failure
                or
                "parquet"
                in failure
            )
        ]
        if parquet_related_failures:
            cross_check[
                "status"
            ] = "FAIL"
        else:
            cross_check[
                "status"
            ] = "PASS"
else:
    cross_check[
        "status"
    ] = "SKIPPED"
    cross_check[
        "reason"
    ] = (
        "Old parquet artifact not found"
    )
# ------------------------------------------------------------
# 13) Metadata / mapping consistency note
#
# ไม่ใช้เป็น hard assert เพราะ metadata request period
# อาจครอบคลุมช่วงที่ไม่มี market records
# ------------------------------------------------------------
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
mapping_intervals = (
    mapping_summary.get(
        "total_mapping_intervals"
    )
)
# ------------------------------------------------------------
# 14) Build Cell 2 audit
# ------------------------------------------------------------
cell2_audit = {
    "audit_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),
    "raw_file":
        raw_identity,
    "decoded": {
        "rows":
            int(
                decoded_rows
            ),
        "columns":
            decoded_columns,
        "dtypes":
            dbn_dtypes,
        "index_name":
            index_name,
        "timezone":
            timezone_name,
        "first_timestamp":
            (
                first_ts.isoformat()
                if first_ts is not None
                else None
            ),
        "last_timestamp":
            (
                last_ts.isoformat()
                if last_ts is not None
                else None
            ),
        "monotonic_increasing":
            bool(
                is_monotonic
            ),
        "duplicate_timestamps":
            duplicate_timestamps,
        "ohlcv_nan_counts":
            ohlcv_nan_counts,
        "high_violations":
            high_violation,
        "low_violations":
            low_violation,
        "negative_volume_rows":
            negative_volume,
        "instrument_id_nan":
            instrument_nan,
        "unique_instrument_ids":
            unique_instruments,
        "roll_transition_count":
            roll_transition_count,
        "metadata_mapping_intervals":
            mapping_intervals,
    },
    "dbn_vs_old_parquet":
        cross_check,
    "failures":
        failures,
}
# ------------------------------------------------------------
# 15) Save audit even if a gate fails
# ------------------------------------------------------------
with open(
    CELL2_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        cell2_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )
# ------------------------------------------------------------
# 16) Integrity gate
# ------------------------------------------------------------
if failures:
    print(
        "\n=== CELL 2 FAILURES ==="
    )
    for failure in failures:
        print(
            " -",
            failure
        )
    raise RuntimeError(
        "\nCELL 2 RAW INTEGRITY: FAIL\n\n"
        "Audit ถูกบันทึกไว้ที่:\n"
        f"{CELL2_AUDIT_PATH}\n\n"
        "ห้ามสร้าง baseline และห้ามไป Cell ถัดไป"
    )
# ------------------------------------------------------------
# 17) Freeze or verify baseline
#
# เขียน baseline หลังทุก Gate ผ่านแล้วเท่านั้น
# ------------------------------------------------------------
baseline_payload = {
    "baseline_version":
        1,
    "baseline_created_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),
    "raw_file":
        raw_identity,
    "decoded_integrity": {
        "rows":
            int(
                decoded_rows
            ),
        "first_timestamp":
            (
                first_ts.isoformat()
                if first_ts is not None
                else None
            ),
        "last_timestamp":
            (
                last_ts.isoformat()
                if last_ts is not None
                else None
            ),
        "timezone":
            timezone_name,
        "duplicate_timestamps":
            duplicate_timestamps,
        "ohlcv_nan_counts":
            ohlcv_nan_counts,
        "unique_instrument_ids":
            unique_instruments,
        "roll_transition_count":
            roll_transition_count,
    },
    "old_parquet_cross_check": {
        "status":
            cross_check[
                "status"
            ],
        "parquet_file":
            runtime_audit.get(
                "old_parquet_reference"
            ),
        "compared_columns":
            cross_check.get(
                "compared_columns",
                [],
            ),
    },
    "environment_at_freeze":
        runtime_audit.get(
            "environment"
        ),
}
if BASELINE_PATH.exists():
    with open(
        BASELINE_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        existing_baseline = (
            json.load(f)
        )
    existing_raw = (
        existing_baseline[
            "raw_file"
        ]
    )
    if (
        existing_raw[
            "sha256"
        ]
        !=
        raw_identity[
            "sha256"
        ]
    ):
        raise RuntimeError(
            "EXISTING BASELINE HASH DOES NOT MATCH CURRENT DBN"
        )
    if (
        int(
            existing_raw[
                "size_bytes"
            ]
        )
        !=
        int(
            raw_identity[
                "size_bytes"
            ]
        )
    ):
        raise RuntimeError(
            "EXISTING BASELINE SIZE DOES NOT MATCH CURRENT DBN"
        )
    existing_decoded = (
        existing_baseline.get(
            "decoded_integrity",
            {}
        )
    )
    baseline_checks = {
        "rows":
            int(
                decoded_rows
            ),
        "first_timestamp":
            (
                first_ts.isoformat()
                if first_ts is not None
                else None
            ),
        "last_timestamp":
            (
                last_ts.isoformat()
                if last_ts is not None
                else None
            ),
        "duplicate_timestamps":
            duplicate_timestamps,
    }
    for key, current_value in (
        baseline_checks.items()
    ):
        old_value = (
            existing_decoded.get(
                key
            )
        )
        if (
            old_value is not None
            and
            old_value != current_value
        ):
            raise RuntimeError(
                "EXISTING BASELINE DECODED "
                f"INTEGRITY MISMATCH: {key}\n"
                f"baseline={old_value}\n"
                f"current ={current_value}"
            )
    baseline_action = (
        "VERIFIED — existing baseline unchanged"
    )
else:
    # Atomic write:
    # เขียน temp ก่อน แล้วค่อย replace
    # ลดความเสี่ยง baseline ครึ่งไฟล์
    BASELINE_TEMP_PATH = (
        BASELINE_PATH.with_suffix(
            ".tmp"
        )
    )
    with open(
        BASELINE_TEMP_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            baseline_payload,
            f,
            indent=2,
            ensure_ascii=False,
        )
    BASELINE_TEMP_PATH.replace(
        BASELINE_PATH
    )
    baseline_action = (
        "CREATED — new immutable raw baseline"
    )
# ------------------------------------------------------------
# 18) Free old parquet from memory
#
# mes_1m จาก DBN ยังเก็บไว้
# เพราะ Cell ถัดไปจะใช้ต่อ
# ------------------------------------------------------------
if (
    "old_1m"
    in globals()
    and
    old_1m is not None
):
    del old_1m
    gc.collect()
# ------------------------------------------------------------
# 19) OUTPUT — decoded DBN
# ------------------------------------------------------------
print(
    "\n"
    + "=" * 70
)
print(
    "DBN FULL DECODE & RAW INTEGRITY"
)
print(
    "=" * 70
)
print(
    "Rows                  :",
    f"{decoded_rows:,}"
)
print(
    "First timestamp       :",
    first_ts
)
print(
    "Last timestamp        :",
    last_ts
)
print(
    "Timezone              :",
    timezone_name
)
print(
    "Monotonic timestamps  :",
    is_monotonic
)
print(
    "Duplicate timestamps  :",
    duplicate_timestamps
)
print(
    "\nOHLCV NaN counts:"
)
for col, count in (
    ohlcv_nan_counts.items()
):
    print(
        f"  {col:10s}",
        count
    )
print(
    "\nOHLC structure:"
)
print(
    "  high violations     :",
    high_violation
)
print(
    "  low violations      :",
    low_violation
)
print(
    "  negative volume     :",
    negative_volume
)
print(
    "\nInstrument / Roll:"
)
print(
    "  unique instrument_id:",
    unique_instruments
)
print(
    "  roll transitions    :",
    roll_transition_count
)
print(
    "  metadata intervals  :",
    mapping_intervals
)
# ------------------------------------------------------------
# 20) OUTPUT — DBN vs Parquet
# ------------------------------------------------------------
print(
    "\n=== DBN ↔ OLD PARQUET CROSS-CHECK ==="
)
print(
    "Status:",
    cross_check[
        "status"
    ]
)
if cross_check[
    "status"
] != "SKIPPED":
    print(
        "Rows equal :",
        cross_check[
            "rows_equal"
        ]
    )
    print(
        "Index equal:",
        cross_check[
            "index_equal"
        ]
    )
    for col in (
        cross_check.get(
            "compared_columns",
            []
        )
    ):
        result = (
            cross_check[
                "column_results"
            ][col]
        )
        print(
            f"  {col:15s}"
            f"values_equal="
            f"{result['values_equal']} "
            f"mismatch="
            f"{result['mismatch_count']:,} "
            f"dtype="
            f"{result['dbn_dtype']}"
            f" ↔ "
            f"{result['parquet_dtype']}"
        )
# ------------------------------------------------------------
# 21) OUTPUT — baseline
# ------------------------------------------------------------
print(
    "\n=== RAW SOURCE BASELINE ==="
)
print(
    baseline_action
)
print(
    "Baseline file:",
    BASELINE_PATH
)
print(
    "Cell 2 audit :",
    CELL2_AUDIT_PATH
)
print(
    "\n"
    + "=" * 70
)
print(
    "CELL 2 RAW INTEGRITY: PASS"
)
print(
    "=" * 70
)


# ------------------------------------------------------------
# CELL 2 INFRASTRUCTURE ADDENDUM — decoded-memory fingerprint
#
# This does not alter market data. It fingerprints the exact decoded
# frame held in this runtime so downstream path calculations can prove
# that they consumed the same Cell 2 object, not merely a frame with the
# same row count and endpoints.
# ------------------------------------------------------------
import hashlib as _cell2_hashlib

CELL2_PROVENANCE_POLICY_VERSION = "MES_V1_RAW_INTEGRITY_1.1"
CELL2_MEMORY_HASH_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "instrument_id",
]

_cell2_memory_row_hashes = pd.util.hash_pandas_object(
    mes_1m[CELL2_MEMORY_HASH_COLUMNS],
    index=True,
    categorize=False,
).to_numpy(dtype="uint64", copy=False)

_cell2_base_status = cell2_audit.get("status")
if _cell2_base_status not in {None, "PASS"} or cell2_audit.get("failures", []):
    raise RuntimeError(
        "CELL 2 PROVENANCE ADDENDUM STOPPED — base Cell 2 audit is not clean PASS."
    )

CELL2_MES_1M_CONTENT_SHA256 = _cell2_hashlib.sha256(
    _cell2_memory_row_hashes.tobytes()
).hexdigest()
del _cell2_memory_row_hashes

cell2_audit["status"] = "PASS"
cell2_audit["policy_version"] = CELL2_PROVENANCE_POLICY_VERSION
cell2_audit["decoded"]["content_sha256"] = CELL2_MES_1M_CONTENT_SHA256
cell2_audit["decoded"]["content_hash_columns"] = CELL2_MEMORY_HASH_COLUMNS
cell2_audit["decoded"]["content_hash_includes_index"] = True
cell2_audit["decoded"]["content_hash_algorithm"] = (
    "SHA256_OVER_PANDAS_UINT64_ROW_HASHES"
)

with open(CELL2_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        cell2_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )

print("Cell 2 decoded-memory SHA256:", CELL2_MES_1M_CONTENT_SHA256)
print("CELL 2 PROVENANCE ADDENDUM: PASS")

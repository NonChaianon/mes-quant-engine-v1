# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 4 — Databento Dataset Condition Registry
# ============================================================
#
# PURPOSE
# -------
# ขอ "สถานะคุณภาพข้อมูลรายวัน" ของ GLBX.MDP3 จาก Databento
#
# IMPORTANT
# ---------
# - ไม่ download MES OHLCV ใหม่
# - Raw market data ยังอ่านจาก Google Drive เท่านั้น
# - API key ใช้เฉพาะ Metadata request
# - Query สำเร็จแล้วจะ cache ลง Drive
# - รอบต่อไปใช้ cache ไม่ต้องเรียก API ซ้ำ
# ============================================================


# ------------------------------------------------------------
# 1) Imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone

import json
import hashlib

import pandas as pd
import databento as db


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

BASELINE_PATH = (
    CLEAN_OUTPUT_DIR /
    "raw_source_baseline.json"
)

CELL3_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell3_supplemental_raw_audit.json"
)

CONDITION_REGISTRY_PATH = (
    CLEAN_OUTPUT_DIR /
    "databento_glbx_mdp3_condition_registry.csv"
)

FLAGGED_CONDITIONS_PATH = (
    CLEAN_OUTPUT_DIR /
    "databento_glbx_mdp3_flagged_conditions.csv"
)

CONDITION_META_PATH = (
    CLEAN_OUTPUT_DIR /
    "databento_glbx_mdp3_condition_registry_meta.json"
)

CELL4_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "cell4_dataset_condition_audit.json"
)


# ------------------------------------------------------------
# 3) Upstream gates
# ------------------------------------------------------------

for required_path in [
    BASELINE_PATH,
    CELL3_AUDIT_PATH,
]:

    if not required_path.exists():

        raise RuntimeError(
            "CELL 4 STOPPED — missing upstream audit:\n\n"
            f"{required_path}\n\n"
            "Run CELL 0 → CELL 3 first."
        )


# ------------------------------------------------------------
# 4) Condition request
#
# Databento condition API ใช้ end_date แบบ inclusive
#
# Raw data request เดิม:
# start = 2019-04-15
# end   = 2026-08-01 exclusive
#
# ดังนั้น condition request:
# end_date = 2026-07-31 inclusive
# ------------------------------------------------------------

CONDITION_REQUEST = {
    "dataset": "GLBX.MDP3",
    "start_date": "2019-04-15",
    "end_date_inclusive": "2026-07-31",
}


VALID_CONDITIONS = {
    "available",
    "degraded",
    "pending",
    "missing",
}


# ------------------------------------------------------------
# 5) Historical warning evidence
# ------------------------------------------------------------

ORIGINAL_WARNING_EVIDENCE = {
    "known_flagged_dates": [
        "2020-02-27",
        "2020-02-28",
        "2020-06-30",
    ],

    "note":
        (
            "Original Databento warning was truncated. "
            "These dates are preserved only as known "
            "historical warning evidence."
        ),
}


# ------------------------------------------------------------
# 6) Helper — SHA256
# ------------------------------------------------------------

def sha256_file(path):

    digest = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(
                8 * 1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


# ------------------------------------------------------------
# 7) Helper — validate registry
# ------------------------------------------------------------

def validate_condition_registry(df):

    required_columns = {
        "date",
        "condition",
        "last_modified_date",
    }


    missing = (
        required_columns
        -
        set(df.columns)
    )


    if missing:

        raise RuntimeError(
            "Condition registry missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )


    work = df.copy()


    work["date"] = pd.to_datetime(
        work["date"],
        errors="raise",
    ).dt.date


    work["condition"] = (
        work["condition"]
        .astype(str)
        .str.lower()
        .str.strip()
    )


    invalid = (
        set(
            work["condition"]
        )
        -
        VALID_CONDITIONS
    )


    if invalid:

        raise RuntimeError(
            "Unknown Databento condition: "
            + ", ".join(
                sorted(invalid)
            )
        )


    duplicate_dates = int(
        work["date"]
        .duplicated()
        .sum()
    )


    if duplicate_dates:

        raise RuntimeError(
            "Duplicate condition dates: "
            f"{duplicate_dates}"
        )


    work = (
        work
        .sort_values("date")
        .reset_index(drop=True)
    )


    return work


# ------------------------------------------------------------
# 8) Prefer existing local cache
#
# ถ้ามี cache แล้ว:
# ไม่ใช้ API key
# ไม่เรียก Databento
# ------------------------------------------------------------

USE_CACHE = (
    CONDITION_REGISTRY_PATH.exists()
    and
    CONDITION_META_PATH.exists()
)


if USE_CACHE:

    print(
        "Existing condition registry cache found."
    )

    print(
        "Using Drive cache — Databento API will NOT be called."
    )


    condition_df = pd.read_csv(
        CONDITION_REGISTRY_PATH
    )


    condition_df = (
        validate_condition_registry(
            condition_df
        )
    )


    with open(
        CONDITION_META_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        registry_meta = (
            json.load(f)
        )


    registry_source = (
        "local_drive_cache"
    )


# ------------------------------------------------------------
# 9) No cache → read API key from Colab Secret
# ------------------------------------------------------------

else:

    print(
        "No local condition registry cache found."
    )


    try:

        from google.colab import userdata

        API_KEY = userdata.get(
            "DATABENTO_API_KEY"
        )


    except Exception as e:

        raise RuntimeError(
            "Cannot read Colab Secret "
            "'DATABENTO_API_KEY'.\n\n"
            "เปิด Secrets (รูปกุญแจ) ใน Colab "
            "แล้วเพิ่ม DATABENTO_API_KEY "
            "และเปิด Notebook access."
        ) from e


    if not API_KEY:

        raise RuntimeError(
            "DATABENTO_API_KEY is empty.\n\n"
            "เพิ่ม API key ใน Colab Secrets ก่อน."
        )


    print(
        "Databento API key detected securely."
    )

    print(
        "Querying dataset-condition metadata only..."
    )


    # --------------------------------------------------------
    # 10) Authenticated Databento metadata request
    #
    # นี่ไม่ใช่ market-data download
    # --------------------------------------------------------

    try:

        client = db.Historical(
            API_KEY
        )


        conditions = (
            client.metadata.get_dataset_condition(
                dataset=
                    CONDITION_REQUEST[
                        "dataset"
                    ],

                start_date=
                    CONDITION_REQUEST[
                        "start_date"
                    ],

                end_date=
                    CONDITION_REQUEST[
                        "end_date_inclusive"
                    ],
            )
        )


    except Exception as e:

        raise RuntimeError(
            "Databento condition metadata request failed.\n\n"
            f"{type(e).__name__}: {e}"
        ) from e


    # --------------------------------------------------------
    # 11) Validate API response
    # --------------------------------------------------------

    condition_df = pd.DataFrame(
        conditions
    )


    condition_df = (
        validate_condition_registry(
            condition_df
        )
    )


    # --------------------------------------------------------
    # 12) Save registry to Drive
    #
    # หลังจากนี้รอบต่อไปจะใช้ cache
    # --------------------------------------------------------

    condition_df.to_csv(
        CONDITION_REGISTRY_PATH,
        index=False,
    )


    retrieved_utc = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    registry_meta = {

        "request":
            CONDITION_REQUEST,

        "retrieved_utc":
            retrieved_utc,

        "source":
            (
                "Databento "
                "Historical.metadata."
                "get_dataset_condition"
            ),

        "registry_sha256":
            sha256_file(
                CONDITION_REGISTRY_PATH
            ),

        "original_warning_evidence":
            ORIGINAL_WARNING_EVIDENCE,
    }


    with open(
        CONDITION_META_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            registry_meta,
            f,
            indent=2,
            ensure_ascii=False,
        )


    registry_source = (
        "databento_metadata_api"
    )


    # ลบ reference ของ key ออกจากตัวแปร
    del API_KEY


# ------------------------------------------------------------
# 13) Analyze conditions
# ------------------------------------------------------------

condition_counts = {

    str(condition):
        int(count)

    for condition, count
    in (
        condition_df[
            "condition"
        ]
        .value_counts()
        .to_dict()
        .items()
    )
}


flagged_df = (

    condition_df[
        condition_df[
            "condition"
        ]
        !=
        "available"
    ]
    .copy()
)


flagged_df.to_csv(
    FLAGGED_CONDITIONS_PATH,
    index=False,
)


flagged_count = int(
    len(flagged_df)
)


# ------------------------------------------------------------
# 14) Compare with original warning evidence
# ------------------------------------------------------------

current_flagged_dates = set(
    flagged_df[
        "date"
    ].astype(str)
)


original_known_dates = set(
    ORIGINAL_WARNING_EVIDENCE[
        "known_flagged_dates"
    ]
)


warning_comparison = {

    "known_original_warning_dates":
        sorted(
            original_known_dates
        ),

    "still_flagged_now":
        sorted(
            original_known_dates
            &
            current_flagged_dates
        ),

    "not_currently_flagged":
        sorted(
            original_known_dates
            -
            current_flagged_dates
        ),
}


# ------------------------------------------------------------
# 15) Save CELL 4 audit
# ------------------------------------------------------------

cell4_audit = {

    "audit_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "request":
        CONDITION_REQUEST,

    "registry_status":
        "AVAILABLE",

    "registry_source":
        registry_source,

    "rows":
        int(
            len(condition_df)
        ),

    "condition_counts":
        condition_counts,

    "flagged_rows":
        flagged_count,

    "historical_warning_comparison":
        warning_comparison,

    "policy": {

        "condition_scope":
            "GLBX.MDP3 dataset-level",

        "automatic_mes_row_deletion":
            False,

        "automatic_mes_day_exclusion":
            False,
    },
}


with open(
    CELL4_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        cell4_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 16) Output
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "DATABENTO DATASET CONDITION REGISTRY"
)

print(
    "=" * 72
)


print(
    "Dataset         :",
    CONDITION_REQUEST[
        "dataset"
    ]
)

print(
    "Registry source :",
    registry_source
)

print(
    "Rows            :",
    f"{len(condition_df):,}"
)

print(
    "First date      :",
    condition_df[
        "date"
    ].min()
)

print(
    "Last date       :",
    condition_df[
        "date"
    ].max()
)


print(
    "\nCondition counts:"
)


for condition_name in [
    "available",
    "degraded",
    "pending",
    "missing",
]:

    print(
        f"  {condition_name:10s}:",
        f"{condition_counts.get(condition_name, 0):,}"
    )


print(
    "\nNon-available dates:",
    f"{flagged_count:,}"
)


if flagged_count:

    print(
        "\nFlagged dates:"
    )

    print(
        flagged_df
        .to_string(
            index=False
        )
    )


print(
    "\nOriginal-warning comparison:"
)

print(
    warning_comparison
)


print(
    "\nRegistry saved:"
)

print(
    CONDITION_REGISTRY_PATH
)

print(
    "\nCELL 4 audit:"
)

print(
    CELL4_AUDIT_PATH
)


print(
    "\n"
    + "=" * 72
)

print(
    "CELL 4 DATASET CONDITION REGISTRY: PASS"
)

print(
    "=" * 72
)

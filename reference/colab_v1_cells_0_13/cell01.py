# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 1 — Raw Source Identity & Provenance
# ============================================================
#
# PURPOSE
# -------
# CELL นี้ทำหน้าที่สร้าง "บัตรประจำตัว" ของข้อมูลต้นทาง
# ก่อนที่เราจะ decode ข้อมูลตลาดจริงใน CELL 2
#
# CELL นี้จะ:
#   1) ตรวจว่า dependency จาก CELL 0 พร้อมใช้งานจริง
#   2) Mount Google Drive
#   3) ระบุ DBN เป็น Raw Source of Truth
#   4) คำนวณ SHA-256 + file size + mtime ของ DBN
#   5) Fingerprint parquet เก่า ถ้ามี
#   6) อ่าน DBN metadata header
#   7) สรุป continuous-contract mappings แบบกระชับ
#   8) บันทึก Python / package environment
#   9) บันทึก pip freeze + pip check
#  10) ตรวจ frozen baseline ถ้ามีอยู่แล้ว
#  11) เขียน runtime_source_audit.json
#
# IMPORTANT
# ---------
# - ไม่มีการดึง Market Data ใหม่จาก Databento
# - ไม่มี Databento API call
# - DBN ใน Google Drive คือ Source of Truth
# - Parquet เก่าใช้เป็น cross-check เท่านั้น
# - CELL 2 จะเป็นคน decode DBN เต็มไฟล์และ freeze baseline
# ============================================================


# ------------------------------------------------------------
# 1) Standard-library imports
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError

import sys
import subprocess
import hashlib
import json


# ------------------------------------------------------------
# 2) Dependency gate
#
# CELL 0 ต้องทำให้ databento import ได้จริง
# ถ้าไม่ได้ ให้หยุดด้วยข้อความที่อ่านง่าย
# ------------------------------------------------------------

try:
    import databento as db

except ModuleNotFoundError as e:
    raise RuntimeError(
        "CELL 1 STOPPED — ไม่พบ package 'databento'\n\n"
        "ให้ทำตามลำดับนี้:\n"
        "1) Run CELL 0\n"
        "2) รอจนเห็น 'CELL 0 FINAL: PASS'\n"
        "3) ห้าม Restart session\n"
        "4) แล้ว Run CELL 1 ใหม่"
    ) from e


try:
    from google.colab import drive

except ModuleNotFoundError as e:
    raise RuntimeError(
        "CELL 1 ต้องรันใน Google Colab "
        "หรือ environment ที่เข้าถึง Google Drive ได้"
    ) from e


# ------------------------------------------------------------
# 3) Mount Google Drive
# ------------------------------------------------------------

drive.mount(
    "/content/drive"
)


# ------------------------------------------------------------
# 4) Project paths
# ------------------------------------------------------------

PROJECT_DIR = Path(
    "/content/drive/MyDrive/Quant_Lab"
)

DATA_DIR = (
    PROJECT_DIR /
    "Data"
)


# ------------------------------------------------------------
# RAW SOURCE OF TRUTH
# ------------------------------------------------------------

MES_DBN_PATH = (
    DATA_DIR /
    "MES_2019_2026_1m.dbn.zst"
)


# ------------------------------------------------------------
# Derived artifact จาก Notebook เก่า
#
# ไม่ใช่ Source of Truth
# CELL 2 จะใช้เทียบกับ DBN
# ------------------------------------------------------------

OLD_PARQUET_PATH = (
    DATA_DIR /
    "MES_2019_2026_1m.parquet"
)


# ------------------------------------------------------------
# Clean Pipeline output directory
# ------------------------------------------------------------

CLEAN_OUTPUT_DIR = (
    DATA_DIR /
    "MES_Clean_Pipeline_V1"
)

CLEAN_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ------------------------------------------------------------
# 5) Audit artifact paths
# ------------------------------------------------------------

RUNTIME_AUDIT_PATH = (
    CLEAN_OUTPUT_DIR /
    "runtime_source_audit.json"
)

PIP_FREEZE_PATH = (
    CLEAN_OUTPUT_DIR /
    "pip_freeze_snapshot.txt"
)

PIP_CHECK_PATH = (
    CLEAN_OUTPUT_DIR /
    "pip_check_snapshot.txt"
)

BASELINE_PATH = (
    CLEAN_OUTPUT_DIR /
    "raw_source_baseline.json"
)


# ------------------------------------------------------------
# 6) Historical request reference
#
# ค่านี้มาจาก Research Log เดิม
# ใช้เป็น reference เท่านั้น ไม่ใช่ proof
# ------------------------------------------------------------

LEGACY_REQUEST_REFERENCE = {
    "dataset": "GLBX.MDP3",
    "symbol": "MES.v.0",
    "stype_in": "continuous",
    "schema": "ohlcv-1m",
    "start": "2019-04-15",
    "end_exclusive": "2026-08-01",
    "continuous_rule": "volume",
    "continuous_rank": 0,
    "back_adjusted": False,
}


# ------------------------------------------------------------
# 7) Source existence gate
#
# DBN ไม่มี = ทำต่อไม่ได้
# Parquet ไม่มี = ยังทำต่อได้ แต่ CELL 2 จะ skip comparison
# ------------------------------------------------------------

if not MES_DBN_PATH.exists():
    raise FileNotFoundError(
        "RAW DBN SOURCE NOT FOUND\n\n"
        f"{MES_DBN_PATH}\n\n"
        "Pipeline stopped."
    )


HAS_OLD_PARQUET = (
    OLD_PARQUET_PATH.exists()
)


# ------------------------------------------------------------
# 8) Helper — installed package version
# ------------------------------------------------------------

def pkg_version(name):
    try:
        return version(name)

    except PackageNotFoundError:
        return "NOT INSTALLED"


# ------------------------------------------------------------
# 9) Helper — SHA-256
#
# อ่านเป็น chunk เพื่อไม่เอาไฟล์ทั้งหมดใส่ RAM
# ------------------------------------------------------------

def sha256_file(
    path,
    chunk_size=8 * 1024 * 1024,
):
    digest = hashlib.sha256()

    with open(path, "rb") as f:

        while True:
            chunk = f.read(
                chunk_size
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


# ------------------------------------------------------------
# 10) Helper — file identity
#
# mtime_utc = filesystem modification time
# ไม่เรียกว่า download time
# ------------------------------------------------------------

def file_identity(path):
    stat = path.stat()

    return {
        "path":
            str(path),

        "size_bytes":
            int(stat.st_size),

        "mtime_utc":
            datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ).isoformat(),

        "sha256":
            sha256_file(path),
    }


# ------------------------------------------------------------
# 11) Fingerprint DBN
# ------------------------------------------------------------

print(
    "Computing DBN SHA-256..."
)

raw_identity = (
    file_identity(
        MES_DBN_PATH
    )
)


# ------------------------------------------------------------
# 12) Fingerprint old parquet — OPTIONAL
# ------------------------------------------------------------

if HAS_OLD_PARQUET:

    print(
        "Computing old Parquet SHA-256..."
    )

    parquet_identity = (
        file_identity(
            OLD_PARQUET_PATH
        )
    )

else:

    parquet_identity = None


# ------------------------------------------------------------
# 13) Parse DBN header / metadata
#
# ถ้า header อ่านไม่ได้ CELL นี้ต้องหยุด
# ------------------------------------------------------------

try:

    dbn_store = (
        db.DBNStore.from_file(
            MES_DBN_PATH
        )
    )

    dbn_metadata = (
        dbn_store.metadata
    )

except Exception as e:

    raise RuntimeError(
        "DBN HEADER / METADATA PARSE FAILED\n\n"
        f"{type(e).__name__}: {e}\n\n"
        "ยังไม่อนุญาตให้ไป CELL 2"
    ) from e


# ------------------------------------------------------------
# 14) Helper — JSON-safe conversion
# ------------------------------------------------------------

def json_safe(value):

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        return {
            str(k):
                json_safe(v)

            for k, v
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            json_safe(v)
            for v in value
        ]

    # Enum / datetime / DBN-specific objects
    return str(value)


# ------------------------------------------------------------
# 15) Helper — summarize bulky metadata
#
# จุดสำคัญ:
# Databento mappings ของไฟล์นี้เป็น dict
#
# ตัวอย่างแนวคิด:
#
# {
#     "MES.v.0": [
#         contract interval 1,
#         contract interval 2,
#         ...
#     ]
# }
#
# ดังนั้น:
#
# symbol_key_count
#   = จำนวน continuous symbol keys
#
# total_mapping_intervals
#   = จำนวนช่วง contract จริงทั้งหมด
# ------------------------------------------------------------

def summarize_bulky_metadata(value):

    # ========================================================
    # CASE A — dict
    # ========================================================

    if isinstance(
        value,
        dict,
    ):

        symbol_key_count = len(value)

        if symbol_key_count == 0:

            return {
                "type":
                    "dict",

                "symbol_key_count":
                    0,

                "total_mapping_intervals":
                    0,

                "first_symbol_key":
                    None,

                "last_symbol_key":
                    None,

                "first_interval":
                    None,

                "last_interval":
                    None,
            }


        keys = list(
            value.keys()
        )

        first_key = (
            keys[0]
        )

        last_key = (
            keys[-1]
        )


        # ----------------------------------------------------
        # Count mapping intervals
        # ----------------------------------------------------

        total_mapping_intervals = 0

        for mapping_value in (
            value.values()
        ):

            if isinstance(
                mapping_value,
                (
                    list,
                    tuple,
                ),
            ):

                total_mapping_intervals += (
                    len(mapping_value)
                )

            else:

                total_mapping_intervals += 1


        # ----------------------------------------------------
        # First interval
        # ----------------------------------------------------

        first_value = (
            value[first_key]
        )

        if (
            isinstance(
                first_value,
                (
                    list,
                    tuple,
                ),
            )
            and
            len(first_value) > 0
        ):

            first_interval = (
                json_safe(
                    first_value[0]
                )
            )

        else:

            first_interval = (
                json_safe(
                    first_value
                )
            )


        # ----------------------------------------------------
        # Last interval
        # ----------------------------------------------------

        last_value = (
            value[last_key]
        )

        if (
            isinstance(
                last_value,
                (
                    list,
                    tuple,
                ),
            )
            and
            len(last_value) > 0
        ):

            last_interval = (
                json_safe(
                    last_value[-1]
                )
            )

        else:

            last_interval = (
                json_safe(
                    last_value
                )
            )


        return {
            "type":
                "dict",

            "symbol_key_count":
                symbol_key_count,

            "total_mapping_intervals":
                total_mapping_intervals,

            "first_symbol_key":
                json_safe(
                    first_key
                ),

            "last_symbol_key":
                json_safe(
                    last_key
                ),

            "first_interval":
                first_interval,

            "last_interval":
                last_interval,
        }


    # ========================================================
    # CASE B — list / tuple
    # ========================================================

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):

        count = len(value)

        return {
            "type":
                type(value).__name__,

            "count":
                count,

            "first":
                (
                    json_safe(
                        value[0]
                    )
                    if count
                    else None
                ),

            "last":
                (
                    json_safe(
                        value[-1]
                    )
                    if count
                    else None
                ),
        }


    # ========================================================
    # CASE C — unknown structure
    # ========================================================

    try:

        return {
            "type":
                type(value).__name__,

            "count":
                len(value),

            "representation":
                str(value)[:1000],
        }

    except Exception as e:

        return {
            "type":
                str(
                    type(value)
                ),

            "summary_error":
                str(e),
        }


# ------------------------------------------------------------
# 16) Extract DBN metadata
#
# mappings ไม่ dump ทั้งก้อน
# ------------------------------------------------------------

BULKY_FIELDS = {
    "mappings",
}

metadata_public = {}

metadata_bulky_summary = {}


for name in dir(
    dbn_metadata
):

    if name.startswith("_"):
        continue


    try:

        value = getattr(
            dbn_metadata,
            name,
        )

    except Exception:
        continue


    if callable(value):
        continue


    if name in BULKY_FIELDS:

        metadata_bulky_summary[
            name
        ] = summarize_bulky_metadata(
            value
        )

        continue


    metadata_public[
        name
    ] = json_safe(
        value
    )


# ------------------------------------------------------------
# 17) Environment snapshot
# ------------------------------------------------------------

ENV_TRACKED_PACKAGES = [
    "databento",
    "databento-dbn",
    "pandas-market-calendars",
    "exchange-calendars",
    "pandas",
    "numpy",
    "pyarrow",
    "zstandard",
    "toolz",
]


ENVIRONMENT = {
    "python":
        sys.version,

    "python_short":
        sys.version.split()[0],

    "packages": {
        name:
            pkg_version(name)

        for name
        in ENV_TRACKED_PACKAGES
    },
}


# ------------------------------------------------------------
# 18) pip freeze snapshot
#
# เป็น forensic record
# ไม่ใช่ requirements.txt
# ------------------------------------------------------------

try:

    freeze_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "freeze",
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )


    freeze_text = (
        freeze_result.stdout
    )


    PIP_FREEZE_PATH.write_text(
        freeze_text,
        encoding="utf-8",
    )


    ENVIRONMENT[
        "pip_freeze_file"
    ] = str(
        PIP_FREEZE_PATH
    )


    ENVIRONMENT[
        "pip_freeze_lines"
    ] = len(
        freeze_text.splitlines()
    )


    ENVIRONMENT[
        "pip_freeze_sha256"
    ] = hashlib.sha256(
        freeze_text.encode(
            "utf-8"
        )
    ).hexdigest()


except Exception as e:

    ENVIRONMENT[
        "pip_freeze_file"
    ] = None

    ENVIRONMENT[
        "pip_freeze_lines"
    ] = None

    ENVIRONMENT[
        "pip_freeze_sha256"
    ] = None

    ENVIRONMENT[
        "pip_freeze_error"
    ] = (
        f"{type(e).__name__}: {e}"
    )


# ------------------------------------------------------------
# 19) pip check snapshot
#
# Global conflicts อาจมีจาก Colab อยู่ก่อนแล้ว
# CELL 0 เป็นคนตัดสินว่า critical หรือไม่
# CELL 1 แค่บันทึกหลักฐาน
# ------------------------------------------------------------

pip_check_result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "check",
    ],
    capture_output=True,
    text=True,
)


pip_check_text = (
    (
        pip_check_result.stdout
        +
        "\n"
        +
        pip_check_result.stderr
    )
    .strip()
)


if not pip_check_text:

    pip_check_text = (
        "No broken requirements found."
    )


PIP_CHECK_PATH.write_text(
    pip_check_text + "\n",
    encoding="utf-8",
)


ENVIRONMENT[
    "pip_check_returncode"
] = (
    pip_check_result.returncode
)


ENVIRONMENT[
    "pip_check_file"
] = str(
    PIP_CHECK_PATH
)


ENVIRONMENT[
    "pip_check_sha256"
] = hashlib.sha256(
    pip_check_text.encode(
        "utf-8"
    )
).hexdigest()


# ------------------------------------------------------------
# 20) Baseline check
#
# ครั้งแรก baseline ยังไม่มี
# CELL 2 จะสร้างเมื่อ:
#
# DBN full decode
# + integrity audit
# + DBN↔Parquet comparison
#
# ผ่านแล้วเท่านั้น
# ------------------------------------------------------------

if BASELINE_PATH.exists():

    try:

        with open(
            BASELINE_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            baseline = (
                json.load(f)
            )


        baseline_raw = (
            baseline[
                "raw_file"
            ]
        )


        baseline_hash = (
            baseline_raw[
                "sha256"
            ]
        )


        baseline_size = (
            baseline_raw[
                "size_bytes"
            ]
        )


    except Exception as e:

        raise RuntimeError(
            "BASELINE FILE EXISTS BUT CANNOT BE READ\n\n"
            f"{type(e).__name__}: {e}"
        ) from e


    if (
        baseline_hash
        !=
        raw_identity[
            "sha256"
        ]
    ):

        raise RuntimeError(
            "RAW DBN HASH CHANGED\n\n"
            f"Baseline : {baseline_hash}\n"
            f"Current  : {raw_identity['sha256']}\n\n"
            "Pipeline stopped."
        )


    if (
        int(baseline_size)
        !=
        int(
            raw_identity[
                "size_bytes"
            ]
        )
    ):

        raise RuntimeError(
            "RAW DBN FILE SIZE CHANGED\n\n"
            f"Baseline : {baseline_size}\n"
            f"Current  : {raw_identity['size_bytes']}\n\n"
            "Pipeline stopped."
        )


    baseline_status = (
        "PASS — raw DBN matches frozen baseline"
    )


else:

    baseline_status = (
        "NOT FROZEN YET — CELL 2 AUDIT REQUIRED"
    )


# ------------------------------------------------------------
# 21) Runtime audit manifest
# ------------------------------------------------------------

runtime_audit = {

    "manifest_written_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "raw_file":
        raw_identity,

    "old_parquet_available":
        HAS_OLD_PARQUET,

    "old_parquet_reference":
        parquet_identity,

    "legacy_request_reference":
        LEGACY_REQUEST_REFERENCE,

    "dbn_metadata":
        metadata_public,

    "dbn_metadata_bulky_summary":
        metadata_bulky_summary,

    "environment":
        ENVIRONMENT,

    "baseline_status":
        baseline_status,
}


with open(
    RUNTIME_AUDIT_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        runtime_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 22) OUTPUT — Raw Source Identity
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 65
)

print(
    "RAW SOURCE IDENTITY"
)

print(
    "=" * 65
)


print(
    "DBN file       :",
    MES_DBN_PATH
)

print(
    "Size bytes     :",
    f"{raw_identity['size_bytes']:,}"
)

print(
    "SHA256         :",
    raw_identity[
        "sha256"
    ]
)

print(
    "File mtime UTC :",
    raw_identity[
        "mtime_utc"
    ]
)


# ------------------------------------------------------------
# 23) OUTPUT — Old Parquet
# ------------------------------------------------------------

print(
    "\n=== OLD PARQUET CROSS-CHECK ARTIFACT ==="
)


if HAS_OLD_PARQUET:

    print(
        "Status         : FOUND"
    )

    print(
        "Size bytes     :",
        f"{parquet_identity['size_bytes']:,}"
    )

    print(
        "SHA256         :",
        parquet_identity[
            "sha256"
        ]
    )


else:

    print(
        "Status         : NOT FOUND"
    )

    print(
        "CELL 2 DBN↔Parquet comparison "
        "จะถูกระบุเป็น SKIPPED"
    )


# ------------------------------------------------------------
# 24) OUTPUT — DBN Metadata
# ------------------------------------------------------------

print(
    "\n=== DBN METADATA ==="
)


print(
    "Metadata fields:"
)

print(
    sorted(
        metadata_public.keys()
    )
)


print(
    "\nBulky metadata summary:"
)

if metadata_bulky_summary:

    for (
        name,
        summary,
    ) in (
        metadata_bulky_summary.items()
    ):

        print(
            f"{name}:",
            summary
        )

else:

    print(
        "None"
    )


# ------------------------------------------------------------
# 25) OUTPUT — Environment
# ------------------------------------------------------------

print(
    "\n=== ENVIRONMENT ==="
)


print(
    "Python:",
    ENVIRONMENT[
        "python_short"
    ]
)


for (
    package_name,
    package_ver,
) in (
    ENVIRONMENT[
        "packages"
    ].items()
):

    print(
        f"  {package_name:30s}"
        f"{package_ver}"
    )


print(
    "\npip freeze SHA256:",
    ENVIRONMENT.get(
        "pip_freeze_sha256"
    )
)


print(
    "pip check return code:",
    ENVIRONMENT[
        "pip_check_returncode"
    ]
)


# ------------------------------------------------------------
# 26) OUTPUT — Baseline / Artifacts
# ------------------------------------------------------------

print(
    "\n=== BASELINE ==="
)

print(
    baseline_status
)


print(
    "\n=== AUDIT ARTIFACTS ==="
)

print(
    "Runtime manifest :",
    RUNTIME_AUDIT_PATH
)

print(
    "pip freeze       :",
    PIP_FREEZE_PATH
)

print(
    "pip check        :",
    PIP_CHECK_PATH
)


# ------------------------------------------------------------
# 27) Final gate
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 65
)

print(
    "CELL 1 LOCAL VALIDATION: PASS"
)

print(
    "=" * 65
)

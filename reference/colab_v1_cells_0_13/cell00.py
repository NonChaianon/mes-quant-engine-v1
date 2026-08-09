
# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 0 — Frozen Dependencies & Environment Validation
# ============================================================
#
# PURPOSE
# -------
# CELL นี้เป็นประตูด่านแรกของ Pipeline
#
# หน้าที่:
#   1) ติดตั้ง dependency หลักด้วย version ที่ผ่าน Discovery แล้ว
#   2) ตรวจว่า pip install สำเร็จจริง
#   3) ตรวจว่า package ที่ต้องใช้มีอยู่จริง
#   4) ตรวจว่า version ที่ติดตั้งจริงตรงกับ version ที่กำหนด
#   5) ตรวจ dependency conflict ก่อน/หลัง install
#   6) ตรวจว่า module ที่โหลดอยู่ใน RAM ไม่ขัดกับ version บน disk
#
# ถ้าด่านสำคัญใดไม่ผ่าน:
#   -> STOP
#   -> ห้ามไป CELL 1
#
# IMPORTANT
# ---------
# Version ด้านล่างมาจาก Discovery ที่รันจริงใน Colab
# ไม่ใช่ version ที่คาดเดา
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

)


# ------------------------------------------------------------
# 1) Frozen dependency versions
# ------------------------------------------------------------
#
# เรา pin package ที่มีผลโดยตรงต่อ:
#
# - การอ่าน DBN
# - Databento schema
# - Market calendar
# - NYSE schedule
#
# Dependency อื่น เช่น pandas / numpy / pyarrow
# จะถูกบันทึก version ใน CELL 1
# แต่ยังไม่ hard-pin ใน Colab V1
# ------------------------------------------------------------

PINNED = {
    "databento": "0.83.0",
    "databento-dbn": "0.65.0",
    "pandas-market-calendars": "5.4.0",
    "exchange-calendars": "4.13.2",
}


# ------------------------------------------------------------
# 2) Packages ที่ต้องรายงาน version
# ------------------------------------------------------------
#
# PINNED packages
# +
# dependency สำคัญที่อาจมีผลกับการคำนวณ/ไฟล์/calendar
# ------------------------------------------------------------

TRACKED_PACKAGES = [
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


# ------------------------------------------------------------
# 3) Modules ที่ต้องระวังเรื่อง stale runtime
# ------------------------------------------------------------
#
# ตัวอย่าง:
#
# pip บอกว่า pandas บน disk = version ใหม่
# แต่ Python runtime ยังถือ pandas version เก่าอยู่ใน RAM
#
# ถ้าเกิดแบบนั้น manifest จะโกหกว่าเราใช้ version ใหม่
# ทั้งที่ calculation จริงใช้ของเก่า
# ------------------------------------------------------------

RUNTIME_SENSITIVE = {
    "pandas": "pandas",
    "numpy": "numpy",
    "pyarrow": "pyarrow",
    "databento": "databento",
    "pandas-market-calendars": "pandas_market_calendars",
    "exchange-calendars": "exchange_calendars",
}


# ------------------------------------------------------------
# 4) Imports
# ------------------------------------------------------------

import sys
import re
import subprocess
import importlib

from importlib.metadata import (
    version,
    PackageNotFoundError,
)


# ------------------------------------------------------------
# 5) Helper — package version on disk
# ------------------------------------------------------------

def pkg_version(name):
    """
    อ่าน version ที่ติดตั้งอยู่จริงจาก package metadata
    โดยไม่พึ่ง __version__ ของ module
    """

    try:
        return version(name)

    except PackageNotFoundError:
        return "NOT INSTALLED"


# ------------------------------------------------------------
# 6) Helper — normalize package name
# ------------------------------------------------------------
#
# Python package names อาจเขียนได้หลายรูป:
#
# pandas_market_calendars
# pandas-market-calendars
#
# normalize เพื่อใช้ตอนตรวจข้อความ conflict
# ------------------------------------------------------------

def normalize_name(name):

    return re.sub(
        r"[-_.]+",
        "-",
        str(name).lower(),
    )


# ------------------------------------------------------------
# 7) Helper — pip check
# ------------------------------------------------------------
#
# pip check ตรวจว่า package ที่ติดตั้งอยู่
# มี dependency requirement ขัดกันหรือไม่
#
# คืนค่าเป็น set ของข้อความ conflict
# ------------------------------------------------------------

def pip_check_conflicts():

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "check",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return set()

    text = (
        result.stdout
        + "\n"
        + result.stderr
    )

    return {
        line.strip()
        for line in text.splitlines()
        if line.strip()
    }


# ------------------------------------------------------------
# 8) ตรวจ conflict ก่อน CELL 0 เปลี่ยน environment
# ------------------------------------------------------------
#
# จุดประสงค์:
#
# ถ้า Colab มี conflict อยู่ก่อนแล้ว
# เราต้องแยกออกจาก conflict ที่ CELL 0 สร้าง
# ------------------------------------------------------------

_conflicts_before = pip_check_conflicts()


print("=== PRE-INSTALL ENVIRONMENT ===")

print(
    "Python:",
    sys.version.split()[0]
)

print(
    "Existing dependency conflicts:",
    len(_conflicts_before)
)


if _conflicts_before:

    print(
        "\nConflicts ที่มีอยู่ก่อน CELL 0:"
    )

    for _line in sorted(
        _conflicts_before
    ):

        print(
            " ",
            _line
        )


# ------------------------------------------------------------
# 9) Build exact install specifications
# ------------------------------------------------------------

_specs = [
    f"{name}=={wanted_version}"
    for name, wanted_version
    in PINNED.items()
]


print(
    "\n=== FROZEN PACKAGE REQUEST ==="
)

for _spec in _specs:

    print(
        " ",
        _spec
    )


# ------------------------------------------------------------
# 10) Install pinned packages
# ------------------------------------------------------------
#
# ไม่ใช้:
#
#   !pip
#
# เพราะเราต้องการ return code จริง
#
# ไม่ใช้:
#
#   -q
#
# เพราะ resolver warning/error ต้องมองเห็นได้
# ------------------------------------------------------------

_install = subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        *_specs,
    ],
    capture_output=True,
    text=True,
)


# ------------------------------------------------------------
# 11) แสดง pip output
# ------------------------------------------------------------

if _install.stdout.strip():

    print(
        "\n=== PIP OUTPUT ==="
    )

    print(
        _install.stdout[-5000:]
    )


if _install.stderr.strip():

    print(
        "\n=== PIP WARNINGS / STDERR ==="
    )

    print(
        _install.stderr[-5000:]
    )


# ------------------------------------------------------------
# 12) Installation safety gate
# ------------------------------------------------------------

if _install.returncode != 0:

    raise RuntimeError(
        "\nCELL 0 FAILED: pip install ไม่สำเร็จ\n\n"
        "ห้ามไป CELL 1\n\n"
        "สาเหตุที่เป็นไปได้:\n"
        "- Colab เปลี่ยน Python version\n"
        "- pinned wheel ไม่มีสำหรับ Python รุ่นใหม่\n"
        "- dependency resolver เปลี่ยน\n"
        "- package ถูกถอนจาก repository\n\n"
        "ห้ามแก้เลข version เพื่อให้ผ่านทันที\n"
        "ต้องทำ Dependency Discovery/Audit ใหม่ก่อน"
    )


print(
    "\nPIP INSTALL RETURN CODE: PASS"
)


# ------------------------------------------------------------
# 13) Refresh import caches
# ------------------------------------------------------------

importlib.invalidate_caches()


# ------------------------------------------------------------
# 14) ตรวจ package presence + version จริง
# ------------------------------------------------------------

print(
    "\n=== INSTALLED VERSIONS ==="
)

print(
    f"{'python':30s}"
    f"{sys.version.split()[0]}"
)


for _name in TRACKED_PACKAGES:

    print(
        f"{_name:30s}"
        f"{pkg_version(_name)}"
    )


# ------------------------------------------------------------
# 15) Package presence gate
# ------------------------------------------------------------

for _name in PINNED:

    _installed = pkg_version(
        _name
    )

    if _installed == "NOT INSTALLED":

        raise RuntimeError(
            f"\nCELL 0 FAILED\n\n"
            f"Package ไม่ได้ถูกติดตั้ง: {_name}\n\n"
            "pip อาจรายงานการทำงานไม่ตรงกับ "
            "environment ปัจจุบัน\n\n"
            "ห้ามไป CELL 1"
        )


print(
    "\nPACKAGE PRESENCE CHECK: PASS"

)


# ------------------------------------------------------------
# 16) Exact version validation
# ------------------------------------------------------------
#
# สิ่งที่เราขอ:
#
#   databento==0.83.0
#
# ต้องเท่ากับสิ่งที่อยู่บน disk จริง
#
# ไม่เชื่อเพียงข้อความจาก pip
# ------------------------------------------------------------

for _name, _wanted in (
    PINNED.items()
):

    _installed = pkg_version(
        _name
    )

    if _installed != _wanted:

        raise RuntimeError(
            f"\nVERSION PIN NOT APPLIED: {_name}\n\n"
            f"ต้องการ : {_wanted}\n"
            f"ได้จริง : {_installed}\n\n"
            "ห้ามไป CELL 1\n\n"
            "ลอง Runtime > Restart session "
            "แล้วรัน CELL 0 ใหม่"
        )


print(
    "VERSION PIN VALIDATION: PASS"
)


# ------------------------------------------------------------
# 17) Dependency conflict หลัง install
# ------------------------------------------------------------

_conflicts_after = (
    pip_check_conflicts()
)

_new_conflicts = sorted(
    _conflicts_after
    -
    _conflicts_before
)


# ------------------------------------------------------------
# 18) แยก conflict:
#
# A) กระทบ package ที่เรา pin โดยตรง
#       -> STOP
#
# B) package อื่นใน Colab ecosystem
#       -> WARNING + บันทึก
#
# ตัวอย่างที่เราเคยพบ:
#
# ibis-framework ต้องการ toolz<1
# แต่ exchange-calendars ใช้ toolz>=1
#
# เราไม่ได้ใช้ ibis-framework ใน MES Pipeline
# จึงบันทึกเป็น environment warning
# ไม่ตีความว่า environment "ไม่มี conflict"
# ------------------------------------------------------------

_pinned_norm = {
    normalize_name(name)
    for name in PINNED
}


_critical_new_conflicts = []

_noncritical_new_conflicts = []


for _line in _new_conflicts:

    _line_norm = normalize_name(
        _line
    )

    _is_critical = any(
        package_name
        in _line_norm

        for package_name
        in _pinned_norm
    )

    if _is_critical:

        _critical_new_conflicts.append(
            _line
        )

    else:

        _noncritical_new_conflicts.append(
            _line
        )


# ------------------------------------------------------------
# 19) Non-critical conflicts
# ------------------------------------------------------------

if _noncritical_new_conflicts:

    print(
        "\n=== ENVIRONMENT WARNING ==="
    )

    print(
        "CELL 0 สร้าง conflict ใหม่ใน package "
        "ที่ Pipeline ไม่ได้ใช้โดยตรง:"
    )

    for _line in (
        _noncritical_new_conflicts
    ):

        print(
            " ",
            _line
        )

    print(
        "\nPipeline ยังเดินต่อได้ "
        "แต่ conflict นี้ต้องถูกเก็บใน Environment Audit"
    )


# ------------------------------------------------------------
# 20) Critical conflicts
# ------------------------------------------------------------

if _critical_new_conflicts:

    raise RuntimeError(
        "\nCELL 0 FAILED\n\n"
        "พบ dependency conflict ใหม่ "
        "ที่พัวพันกับ package หลักของ Pipeline:\n\n"
        + "\n".join(
            _critical_new_conflicts
        )
        + "\n\nห้ามไป CELL 1"
    )


print(
    "\nCRITICAL DEPENDENCY CONFLICT CHECK: PASS"
)


# ------------------------------------------------------------
# 21) รายงาน Global pip-check state
# ------------------------------------------------------------
#
# สำคัญ:
#
# PASS ด้านบนไม่ได้แปลว่า Colab ไม่มี conflict
#
# มันแปลว่า:
# "ไม่มี conflict ใหม่ที่กระทบ pinned pipeline packages"
# ------------------------------------------------------------

print(
    "\n=== GLOBAL PIP CHECK STATE ==="
)

print(
    "Conflicts before install:",
    len(_conflicts_before)
)

print(
    "Conflicts after install :",
    len(_conflicts_after)
)

print(
    "New conflicts           :",
    len(_new_conflicts)
)


if _conflicts_after:

    print(
        "\nCurrent global conflicts:"
    )

    for _line in sorted(
        _conflicts_after
    ):

        print(
            " ",
            _line
        )


# ------------------------------------------------------------
# 22) Runtime vs disk version check
# ------------------------------------------------------------
#
# importlib.metadata อ่าน version บน disk
#
# แต่ module ที่ถูก import ไปแล้วอาจยังค้าง version เก่า
# อยู่ใน RAM
#
# ถ้ามี mismatch:
#
# STOP
#
# เพราะ CELL 1 จะบันทึก Environment ผิด
# ------------------------------------------------------------

_stale_modules = []


for (
    _dist_name,
    _module_name,
) in RUNTIME_SENSITIVE.items():

    _module = sys.modules.get(
        _module_name
    )

    # module ยังไม่เคย import
    # จึงไม่มี stale runtime problem
    if _module is None:
        continue

    _loaded_version = getattr(
        _module,
        "__version__",
        None,
    )

    _disk_version = pkg_version(
        _dist_name
    )

    if (
        _loaded_version
        and
        _disk_version
        != "NOT INSTALLED"
        and
        str(_loaded_version)
        != str(_disk_version)
    ):

        _stale_modules.append(
            f"{_dist_name}: "
            f"loaded={_loaded_version}, "
            f"disk={_disk_version}"
        )


if _stale_modules:

    raise RuntimeError(
        "\nCELL 0 FAILED: STALE RUNTIME\n\n"
        "Python กำลังใช้ module คนละ version "
        "กับที่ติดตั้งอยู่บน disk:\n\n"
        + "\n".join(
            _stale_modules
        )
        + "\n\nให้เลือก:\n"
        "Runtime > Restart session\n"
        "แล้วรัน CELL 0 ใหม่\n\n"
        "ห้ามไป CELL 1 ก่อน"
    )


print(
    "RUNTIME / DISK VERSION MATCH: PASS"
)


# ------------------------------------------------------------
# 23) Final environment summary
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 55
)

print(
    "CELL 0 FINAL VALIDATION"
)

print(
    "=" * 55
)


print(
    "\nFrozen packages:"
)

for _name, _wanted in (
    PINNED.items()
):

    print(
        f"  {_name:30s}"
        f"{_wanted}"
    )


print(
    "\nFinal gates:"
)

print(
    "  pip install                 : PASS"
)

print(
    "  package presence            : PASS"
)

print(
    "  exact pinned versions       : PASS"
)

print(
    "  critical dependency conflict: PASS"
)

print(
    "  runtime/disk version match  : PASS"
)


print(
    "\nCELL 0 FINAL: PASS"
)

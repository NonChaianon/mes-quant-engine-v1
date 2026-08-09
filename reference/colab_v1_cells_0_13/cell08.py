# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 8 — PURGED CHRONOLOGICAL SPLITS
# ============================================================
#
# PURPOSE
# -------
# Freeze how the Cell 7 decision universe is divided through time
# before any feature, economic label, or model is fitted.
#
# This cell:
# 1) binds itself to the exact Cell 7 universe hash,
# 2) reserves 2025 onward as an untouched final test period,
# 3) creates expanding walk-forward validation folds for 2022–2024,
# 4) purges any training row whose +60m information interval reaches
#    into the following validation/test period,
# 5) records every assignment, boundary, count, and SHA-256 hash.
#
# IMPORTANT
# ---------
# label_end_time is used only to audit temporal overlap. No return,
# direction, P&L, or economic label is created in this cell.
# ============================================================

import warnings as _warnings

_warnings.filterwarnings(
    "ignore",
    message=r"datetime\.datetime\.utcnow\(\) is deprecated.*",
    category=DeprecationWarning,
)

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1) Paths and frozen policy
# ------------------------------------------------------------
PROJECT_DIR = Path("/content/drive/MyDrive/Quant_Lab")
CLEAN_DIR = PROJECT_DIR / "Data" / "MES_Clean_Pipeline_V1"

CELL7_UNIVERSE_PATH = CLEAN_DIR / "cell7_decision_universe_v1.parquet"
CELL7_AUDIT_PATH = CLEAN_DIR / "cell7_decision_universe_audit.json"

CELL8_ASSIGNMENTS_PATH = (
    CLEAN_DIR / "cell8_purged_split_assignments_v1.parquet"
)
CELL8_FOLDS_PATH = CLEAN_DIR / "cell8_walk_forward_folds_v1.csv"
CELL8_BOUNDARIES_PATH = CLEAN_DIR / "cell8_purge_boundaries_v1.csv"
CELL8_AUDIT_PATH = CLEAN_DIR / "cell8_purged_split_audit.json"

SPLIT_POLICY_VERSION = "MES_V1_PURGED_SPLIT_1.0"
EXPECTED_CELL7_POLICY = "MES_V1_DECISION_UNIVERSE_1.0"
LABEL_HORIZON_MINUTES = 60

# Stable calendar-year contract. Appending new data must not move
# these historical boundaries; it requires a new policy version.
OUTER_TRAIN_END_YEAR = 2023
OUTER_VALIDATION_YEAR = 2024
FINAL_TEST_START_YEAR = 2025

# Expanding train -> next calendar-year validation.
WALK_FORWARD_SPECS = [
    ("WF_2022", 2021, 2022),
    ("WF_2023", 2022, 2023),
    ("WF_2024", 2023, 2024),
]

# Embargo is deliberately not invented here. Purging is mandatory;
# any non-zero embargo remains an OPEN research decision.
EMBARGO_MINUTES = 0


# ------------------------------------------------------------
# 2) Helpers
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
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def iso_or_none(value):
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).isoformat()


# ------------------------------------------------------------
# 3) Upstream artifact and hash gates
# ------------------------------------------------------------
for required_path in [CELL7_UNIVERSE_PATH, CELL7_AUDIT_PATH]:
    if not required_path.exists():
        raise RuntimeError(
            "CELL 8 STOPPED — missing Cell 7 artifact:\n"
            f"{required_path}\n\n"
            "Run Cell 0 → Cell 7 first."
        )

cell7_audit = load_json(CELL7_AUDIT_PATH)

if cell7_audit.get("status") != "PASS":
    raise RuntimeError(
        "CELL 8 STOPPED — Cell 7 audit status is not PASS."
    )

if cell7_audit.get("failures", []):
    raise RuntimeError(
        "CELL 8 STOPPED — Cell 7 audit contains failures."
    )

if cell7_audit.get("policy_version") != EXPECTED_CELL7_POLICY:
    raise RuntimeError(
        "CELL 8 STOPPED — unexpected Cell 7 policy version:\n"
        f"{cell7_audit.get('policy_version')}"
    )

expected_cell7_hash = (
    cell7_audit
    .get("sha256", {})
    .get("decision_universe_sha256")
)
actual_cell7_hash = sha256_file(CELL7_UNIVERSE_PATH)

if not expected_cell7_hash:
    raise RuntimeError(
        "CELL 8 STOPPED — Cell 7 audit has no universe SHA-256."
    )

if actual_cell7_hash != expected_cell7_hash:
    raise RuntimeError(
        "CELL 8 STOPPED — Cell 7 universe hash mismatch.\n"
        f"Audit : {expected_cell7_hash}\n"
        f"Actual: {actual_cell7_hash}"
    )


# ------------------------------------------------------------
# 4) Load and validate the frozen decision universe
# ------------------------------------------------------------
universe = pd.read_parquet(CELL7_UNIVERSE_PATH)

required_columns = {
    "decision_id",
    "policy_version",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "bar_complete_15m",
    "crosses_roll",
    "decision_eligible",
    "dataset_degraded_utc",
}
missing_columns = required_columns - set(universe.columns)
if missing_columns:
    raise RuntimeError(
        "CELL 8 STOPPED — missing Cell 7 columns:\n"
        + ", ".join(sorted(missing_columns))
    )

universe = universe.copy()
universe["decision_time"] = pd.to_datetime(
    universe["decision_time"],
    utc=True,
    errors="raise",
)
universe["nyse_session_date"] = (
    pd.to_datetime(
        universe["nyse_session_date"],
        errors="raise",
    )
    .dt.date
)
universe = universe.sort_values("decision_time").reset_index(drop=True)

expected_rows = int(
    cell7_audit
    .get("counts", {})
    .get("eligible_decision_rows", -1)
)

structural_failures = []
if len(universe) != expected_rows:
    structural_failures.append(
        "Cell 7 row count does not match its audit: "
        f"{len(universe):,} != {expected_rows:,}"
    )
if universe.empty:
    structural_failures.append("Cell 7 universe is empty.")
if universe["decision_id"].duplicated().any():
    structural_failures.append("Duplicate decision_id in Cell 7 universe.")
if universe["decision_time"].duplicated().any():
    structural_failures.append("Duplicate decision_time in Cell 7 universe.")
if not universe["decision_time"].is_monotonic_increasing:
    structural_failures.append("Cell 7 universe is not time-sorted.")
if not universe["decision_eligible"].astype(bool).all():
    structural_failures.append("Ineligible row found in Cell 7 universe.")
if (~universe["bar_complete_15m"].astype(bool)).any():
    structural_failures.append("Partial bar found in Cell 7 universe.")
if universe["crosses_roll"].astype(bool).any():
    structural_failures.append("Roll-cross bar found in Cell 7 universe.")

if structural_failures:
    raise RuntimeError(
        "CELL 8 STOPPED — Cell 7 structural gate failed:\n- "
        + "\n- ".join(structural_failures)
    )


# ------------------------------------------------------------
# 5) Build immutable time assignments
# ------------------------------------------------------------
assignments = universe[
    [
        "decision_id",
        "decision_time",
        "nyse_session_date",
        "instrument_id",
        "dataset_degraded_utc",
    ]
].copy()

assignments["label_start_time"] = assignments["decision_time"]
assignments["label_end_time"] = (
    assignments["decision_time"]
    + pd.Timedelta(minutes=LABEL_HORIZON_MINUTES)
)

session_ts = pd.to_datetime(assignments["nyse_session_date"])
session_year = session_ts.dt.year

assignments["outer_partition"] = np.select(
    [
        session_year.le(OUTER_TRAIN_END_YEAR),
        session_year.eq(OUTER_VALIDATION_YEAR),
        session_year.ge(FINAL_TEST_START_YEAR),
    ],
    [
        "TRAIN",
        "VALIDATION",
        "FINAL_TEST",
    ],
    default="UNASSIGNED",
)


# ------------------------------------------------------------
# 6) Expanding walk-forward folds with overlap purging
# ------------------------------------------------------------
fold_rows = []
boundary_rows = []
failures = []

for fold_id, train_end_year, validation_year in WALK_FORWARD_SPECS:
    raw_train_mask = session_year.le(train_end_year)
    validation_mask = session_year.eq(validation_year)

    if not raw_train_mask.any():
        failures.append(f"{fold_id}: empty training period.")
        continue
    if not validation_mask.any():
        failures.append(f"{fold_id}: empty validation period.")
        continue

    validation_start = assignments.loc[
        validation_mask,
        "decision_time",
    ].min()

    # Purge train observations whose information interval touches or
    # crosses the first validation decision timestamp.
    purge_mask = (
        raw_train_mask
        & assignments["label_end_time"].ge(validation_start)
    )
    kept_train_mask = raw_train_mask & ~purge_mask

    role_column = "role_" + fold_id.lower()
    assignments[role_column] = "UNUSED"
    assignments.loc[kept_train_mask, role_column] = "TRAIN"
    assignments.loc[purge_mask, role_column] = "PURGED"
    assignments.loc[validation_mask, role_column] = "VALIDATION"

    max_kept_train_label_end = assignments.loc[
        kept_train_mask,
        "label_end_time",
    ].max()
    overlap_after_purge = int(
        assignments.loc[
            kept_train_mask,
            "label_end_time",
        ]
        .ge(validation_start)
        .sum()
    )

    if overlap_after_purge != 0:
        failures.append(
            f"{fold_id}: {overlap_after_purge:,} train labels "
            "still overlap validation after purging."
        )

    test_leakage_rows = int(
        (
            session_year.ge(FINAL_TEST_START_YEAR)
            & assignments[role_column].ne("UNUSED")
        ).sum()
    )
    if test_leakage_rows != 0:
        failures.append(
            f"{fold_id}: {test_leakage_rows:,} final-test rows leaked "
            "into walk-forward development."
        )

    train_sessions = int(
        assignments.loc[
            kept_train_mask,
            "nyse_session_date",
        ].nunique()
    )
    validation_sessions = int(
        assignments.loc[
            validation_mask,
            "nyse_session_date",
        ].nunique()
    )

    if train_sessions < 500:
        failures.append(
            f"{fold_id}: only {train_sessions:,} training sessions; "
            "minimum is 500."
        )
    if validation_sessions < 200:
        failures.append(
            f"{fold_id}: only {validation_sessions:,} validation "
            "sessions; minimum is 200."
        )

    natural_gap_minutes = (
        None
        if pd.isna(max_kept_train_label_end)
        else float(
            (
                validation_start
                - max_kept_train_label_end
            ).total_seconds()
            / 60.0
        )
    )

    fold_rows.append(
        {
            "fold_id": fold_id,
            "train_start_session": str(
                assignments.loc[
                    kept_train_mask,
                    "nyse_session_date",
                ].min()
            ),
            "train_end_session": str(
                assignments.loc[
                    kept_train_mask,
                    "nyse_session_date",
                ].max()
            ),
            "validation_start_session": str(
                assignments.loc[
                    validation_mask,
                    "nyse_session_date",
                ].min()
            ),
            "validation_end_session": str(
                assignments.loc[
                    validation_mask,
                    "nyse_session_date",
                ].max()
            ),
            "train_rows_before_purge": int(raw_train_mask.sum()),
            "purged_train_rows": int(purge_mask.sum()),
            "train_rows_after_purge": int(kept_train_mask.sum()),
            "validation_rows": int(validation_mask.sum()),
            "train_sessions": train_sessions,
            "validation_sessions": validation_sessions,
            "overlap_rows_after_purge": overlap_after_purge,
            "embargo_minutes": EMBARGO_MINUTES,
        }
    )

    boundary_rows.append(
        {
            "boundary_id": fold_id + "_VALIDATION_START",
            "left_role": "TRAIN",
            "right_role": "VALIDATION",
            "right_first_decision_utc": iso_or_none(validation_start),
            "left_last_label_end_after_purge_utc": iso_or_none(
                max_kept_train_label_end
            ),
            "purged_left_rows": int(purge_mask.sum()),
            "overlap_rows_after_purge": overlap_after_purge,
            "natural_gap_minutes_after_purge": natural_gap_minutes,
        }
    )


# ------------------------------------------------------------
# 7) Seal the final test boundary
# ------------------------------------------------------------
final_test_mask = assignments["outer_partition"].eq("FINAL_TEST")
development_mask = assignments["outer_partition"].isin(
    ["TRAIN", "VALIDATION"]
)

if not final_test_mask.any():
    failures.append("Final test period is empty.")
    final_test_start = pd.NaT
    pretest_purge_mask = pd.Series(False, index=assignments.index)
else:
    final_test_start = assignments.loc[
        final_test_mask,
        "decision_time",
    ].min()
    pretest_purge_mask = (
        development_mask
        & assignments["label_end_time"].ge(final_test_start)
    )

assignments["purged_before_final_test"] = pretest_purge_mask.astype(bool)
assignments["outer_modeling_eligible"] = (
    ~final_test_mask
    & ~assignments["purged_before_final_test"]
)

pretest_overlap_after = int(
    assignments.loc[
        development_mask
        & ~pretest_purge_mask,
        "label_end_time",
    ]
    .ge(final_test_start)
    .sum()
) if not pd.isna(final_test_start) else -1

if pretest_overlap_after != 0:
    failures.append(
        "Development labels still overlap final test after purging: "
        f"{pretest_overlap_after:,}"
    )

outer_counts = (
    assignments["outer_partition"]
    .value_counts()
    .reindex(
        ["TRAIN", "VALIDATION", "FINAL_TEST", "UNASSIGNED"],
        fill_value=0,
    )
)

if int(outer_counts["UNASSIGNED"]) != 0:
    failures.append(
        f"Unassigned outer rows: {int(outer_counts['UNASSIGNED']):,}"
    )
if int(outer_counts.sum()) != len(assignments):
    failures.append("Outer partition counts do not reconcile.")

final_test_sessions = int(
    assignments.loc[
        final_test_mask,
        "nyse_session_date",
    ].nunique()
)
if final_test_sessions < 250:
    failures.append(
        f"Final test has only {final_test_sessions:,} sessions; "
        "minimum is 250."
    )

max_dev_label_end = assignments.loc[
    development_mask & ~pretest_purge_mask,
    "label_end_time",
].max()
test_gap_minutes = (
    None
    if pd.isna(final_test_start) or pd.isna(max_dev_label_end)
    else float(
        (final_test_start - max_dev_label_end).total_seconds()
        / 60.0
    )
)

boundary_rows.append(
    {
        "boundary_id": "FINAL_TEST_START",
        "left_role": "MODEL_DEVELOPMENT",
        "right_role": "FINAL_TEST",
        "right_first_decision_utc": iso_or_none(final_test_start),
        "left_last_label_end_after_purge_utc": iso_or_none(
            max_dev_label_end
        ),
        "purged_left_rows": int(pretest_purge_mask.sum()),
        "overlap_rows_after_purge": pretest_overlap_after,
        "natural_gap_minutes_after_purge": test_gap_minutes,
    }
)


# ------------------------------------------------------------
# 8) Final audit gates
# ------------------------------------------------------------
if assignments["decision_id"].duplicated().any():
    failures.append("Duplicate decision_id in Cell 8 assignments.")
if len(assignments) != len(universe):
    failures.append("Cell 8 assignments changed the Cell 7 row count.")
if not assignments["decision_time"].is_monotonic_increasing:
    failures.append("Cell 8 assignments are not time-sorted.")
if int(assignments["label_end_time"].isna().sum()) != 0:
    failures.append("Missing label_end_time in Cell 8 assignments.")
if not assignments["label_end_time"].eq(
    assignments["decision_time"]
    + pd.Timedelta(minutes=LABEL_HORIZON_MINUTES)
).all():
    failures.append("Incorrect +60m label interval endpoint.")

folds = pd.DataFrame(fold_rows)
boundaries = pd.DataFrame(boundary_rows)

if len(folds) != len(WALK_FORWARD_SPECS):
    failures.append(
        f"Expected {len(WALK_FORWARD_SPECS)} walk-forward folds; "
        f"built {len(folds)}."
    )
if int(boundaries["overlap_rows_after_purge"].sum()) != 0:
    failures.append("A split boundary still has temporal overlap.")


# ------------------------------------------------------------
# 9) Save versioned artifacts and bind hashes
# ------------------------------------------------------------
assignments.to_parquet(
    CELL8_ASSIGNMENTS_PATH,
    index=False,
)
folds.to_csv(
    CELL8_FOLDS_PATH,
    index=False,
)
boundaries.to_csv(
    CELL8_BOUNDARIES_PATH,
    index=False,
)

artifact_hashes = {
    "input_cell7_universe_sha256": actual_cell7_hash,
    "input_cell7_audit_sha256": sha256_file(CELL7_AUDIT_PATH),
    "split_assignments_sha256": sha256_file(CELL8_ASSIGNMENTS_PATH),
    "walk_forward_folds_sha256": sha256_file(CELL8_FOLDS_PATH),
    "purge_boundaries_sha256": sha256_file(CELL8_BOUNDARIES_PATH),
}

partition_summary = []
for partition_name in ["TRAIN", "VALIDATION", "FINAL_TEST"]:
    mask = assignments["outer_partition"].eq(partition_name)
    partition_summary.append(
        {
            "outer_partition": partition_name,
            "rows": int(mask.sum()),
            "sessions": int(
                assignments.loc[mask, "nyse_session_date"].nunique()
            ),
            "first_session": str(
                assignments.loc[mask, "nyse_session_date"].min()
            ),
            "last_session": str(
                assignments.loc[mask, "nyse_session_date"].max()
            ),
            "first_decision_utc": iso_or_none(
                assignments.loc[mask, "decision_time"].min()
            ),
            "last_decision_utc": iso_or_none(
                assignments.loc[mask, "decision_time"].max()
            ),
        }
    )

cell8_audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": SPLIT_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell7_policy_version": cell7_audit.get("policy_version"),
        "cell7_status": cell7_audit.get("status"),
        "cell7_eligible_rows": expected_rows,
        "cell7_universe_sha256": actual_cell7_hash,
    },
    "split_contract": {
        "method": "calendar-year chronological expanding walk-forward",
        "outer_train_through_year": OUTER_TRAIN_END_YEAR,
        "outer_validation_year": OUTER_VALIDATION_YEAR,
        "final_test_from_year": FINAL_TEST_START_YEAR,
        "final_test_is_untouched": True,
        "label_horizon_minutes_for_purging": LABEL_HORIZON_MINUTES,
        "purge_rule": (
            "remove left-side observations when label_end_time >= "
            "first decision_time of the right-side period"
        ),
        "embargo_minutes": EMBARGO_MINUTES,
        "embargo_status": (
            "OPEN — no non-zero embargo is assumed; revisit after "
            "feature and label dependence analysis"
        ),
        "economic_label_created": False,
        "future_return_created": False,
    },
    "counts": {
        "decision_rows": int(len(assignments)),
        "decision_sessions": int(
            assignments["nyse_session_date"].nunique()
        ),
        "outer_train_rows": int(outer_counts["TRAIN"]),
        "outer_validation_rows": int(outer_counts["VALIDATION"]),
        "final_test_rows": int(outer_counts["FINAL_TEST"]),
        "final_test_sessions": final_test_sessions,
        "purged_before_final_test_rows": int(pretest_purge_mask.sum()),
        "walk_forward_folds": int(len(folds)),
        "total_fold_purged_rows": int(
            folds["purged_train_rows"].sum()
        ) if not folds.empty else 0,
        "boundary_overlap_rows_after_purge": int(
            boundaries["overlap_rows_after_purge"].sum()
        ),
    },
    "outer_partitions": partition_summary,
    "walk_forward_folds": folds.to_dict(orient="records"),
    "purge_boundaries": boundaries.to_dict(orient="records"),
    "artifacts": {
        "split_assignments": str(CELL8_ASSIGNMENTS_PATH),
        "walk_forward_folds": str(CELL8_FOLDS_PATH),
        "purge_boundaries": str(CELL8_BOUNDARIES_PATH),
    },
    "sha256": artifact_hashes,
    "failures": failures,
}

with open(CELL8_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        cell8_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 10) Final hard gate and compact output
# ------------------------------------------------------------
if failures:
    print("\nCELL 8 FAILURES")
    print("-" * 72)
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 8 PURGED CHRONOLOGICAL SPLITS: FAIL\n"
        f"{CELL8_AUDIT_PATH}"
    )

print("\n" + "=" * 72)
print("CELL 8 — PURGED CHRONOLOGICAL SPLITS")
print("=" * 72)

print("\n[1] UPSTREAM BINDING")
print("Cell 7 rows        :", f"{len(assignments):,}")
print("Cell 7 sessions    :", f"{assignments['nyse_session_date'].nunique():,}")
print("Cell 7 SHA256      :", actual_cell7_hash)

print("\n[2] OUTER PARTITIONS")
print(
    pd.DataFrame(partition_summary)[
        [
            "outer_partition",
            "rows",
            "sessions",
            "first_session",
            "last_session",
        ]
    ].to_string(index=False)
)

print("\n[3] WALK-FORWARD FOLDS")
print(
    folds[
        [
            "fold_id",
            "train_rows_after_purge",
            "validation_rows",
            "purged_train_rows",
            "overlap_rows_after_purge",
        ]
    ].to_string(index=False)
)

print("\n[4] PURGE / TEST SAFETY")
print(
    "Final-test rows                 :",
    f"{int(outer_counts['FINAL_TEST']):,}",
)
print(
    "Purged before final test        :",
    f"{int(pretest_purge_mask.sum()):,}",
)
print(
    "Boundary overlap after purging  :",
    int(boundaries["overlap_rows_after_purge"].sum()),
)
print("Embargo minutes                  :", EMBARGO_MINUTES)
print("Economic label created           : False")

print("\n[5] SAVED ARTIFACTS")
print("Split assignments :", CELL8_ASSIGNMENTS_PATH)
print("Fold manifest     :", CELL8_FOLDS_PATH)
print("Boundary audit    :", CELL8_BOUNDARIES_PATH)
print("Cell 8 audit      :", CELL8_AUDIT_PATH)
print("Assignments SHA256:", artifact_hashes["split_assignments_sha256"])

print("\n" + "=" * 72)
print("CELL 8 PURGED CHRONOLOGICAL SPLITS: PASS")
print("=" * 72)

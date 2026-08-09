# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 10 — POINT-IN-TIME +60m ECONOMIC LABELS
# ============================================================
#
# PURPOSE
# -------
# Build auditable +60-minute development labels only after the
# Decision Universe, chronological splits, purging, and cost contract
# have been frozen.
#
# This cell:
# 1) binds to the exact Cell 7 market-data hash,
# 2) binds to the exact Cell 8 assignment hash,
# 3) binds to the exact Cell 9 cost-scenario hash,
# 4) computes close-to-close +60m outcomes for Train/Validation only,
# 5) rejects labels with missing/partial/roll-mixed future paths,
# 6) creates LONG / SHORT / NO_TRADE labels after transaction costs,
# 7) leaves every Final Test outcome SEALED and uncomputed.
#
# IMPORTANT
# ---------
# Future-derived columns created here are TARGETS ONLY. They must
# never enter the online feature matrix or decision-time eligibility.
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
# 1) Paths and version contract
# ------------------------------------------------------------
PROJECT_DIR = Path("/content/drive/MyDrive/Quant_Lab")
CLEAN_DIR = PROJECT_DIR / "Data" / "MES_Clean_Pipeline_V1"

MES_15M_PATH = CLEAN_DIR / "MES_2019_2026_15m_clean.parquet"
CELL7_AUDIT_PATH = CLEAN_DIR / "cell7_decision_universe_audit.json"

CELL8_ASSIGNMENTS_PATH = (
    CLEAN_DIR / "cell8_purged_split_assignments_v1.parquet"
)
CELL8_AUDIT_PATH = CLEAN_DIR / "cell8_purged_split_audit.json"

CELL9_SCENARIOS_PATH = CLEAN_DIR / "cell9_cost_scenarios_v1.csv"
CELL9_AUDIT_PATH = CLEAN_DIR / "cell9_cost_model_audit.json"

CELL10_LABELS_PATH = (
    CLEAN_DIR / "cell10_point_in_time_economic_labels_v1.parquet"
)
CELL10_SUMMARY_PATH = (
    CLEAN_DIR / "cell10_development_label_summary_v1.csv"
)
CELL10_UNUSABLE_PATH = (
    CLEAN_DIR / "cell10_unusable_label_events_v1.parquet"
)
CELL10_AUDIT_PATH = CLEAN_DIR / "cell10_economic_label_audit.json"

LABEL_POLICY_VERSION = "MES_V1_ECONOMIC_LABELS_1.0"
EXPECTED_CELL7_POLICY = "MES_V1_DECISION_UNIVERSE_1.0"
EXPECTED_CELL8_POLICY = "MES_V1_PURGED_SPLIT_1.0"
EXPECTED_CELL9_POLICY = "MES_V1_COST_MODEL_1.0"

BAR_MINUTES = 15
LABEL_HORIZON_MINUTES = 60
HORIZON_BAR_COUNT = LABEL_HORIZON_MINUTES // BAR_MINUTES
CONTRACT_MULTIPLIER_USD_PER_POINT = 5.00


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


def safe_name(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


# ------------------------------------------------------------
# 3) Upstream artifact gates
# ------------------------------------------------------------
required_paths = [
    MES_15M_PATH,
    CELL7_AUDIT_PATH,
    CELL8_ASSIGNMENTS_PATH,
    CELL8_AUDIT_PATH,
    CELL9_SCENARIOS_PATH,
    CELL9_AUDIT_PATH,
]
for required_path in required_paths:
    if not required_path.exists():
        raise RuntimeError(
            "CELL 10 STOPPED — missing upstream artifact:\n"
            f"{required_path}\n\n"
            "Run Cell 0 → Cell 9 first."
        )

cell7_audit = load_json(CELL7_AUDIT_PATH)
cell8_audit = load_json(CELL8_AUDIT_PATH)
cell9_audit = load_json(CELL9_AUDIT_PATH)

upstream_specs = [
    (
        "Cell 7",
        cell7_audit,
        EXPECTED_CELL7_POLICY,
    ),
    (
        "Cell 8",
        cell8_audit,
        EXPECTED_CELL8_POLICY,
    ),
    (
        "Cell 9",
        cell9_audit,
        EXPECTED_CELL9_POLICY,
    ),
]

for cell_name, audit, expected_policy in upstream_specs:
    if audit.get("status") != "PASS":
        raise RuntimeError(
            f"CELL 10 STOPPED — {cell_name} status is not PASS."
        )
    if audit.get("failures", []):
        raise RuntimeError(
            f"CELL 10 STOPPED — {cell_name} contains failures."
        )
    if audit.get("policy_version") != expected_policy:
        raise RuntimeError(
            f"CELL 10 STOPPED — unexpected {cell_name} policy:\n"
            f"{audit.get('policy_version')}"
        )

expected_mes_15m_hash = (
    cell7_audit
    .get("sha256", {})
    .get("input_mes_15m_sha256")
)
expected_cell8_hash = (
    cell8_audit
    .get("sha256", {})
    .get("split_assignments_sha256")
)
expected_cell9_hash = (
    cell9_audit
    .get("sha256", {})
    .get("cost_scenarios_sha256")
)

actual_mes_15m_hash = sha256_file(MES_15M_PATH)
actual_cell8_hash = sha256_file(CELL8_ASSIGNMENTS_PATH)
actual_cell9_hash = sha256_file(CELL9_SCENARIOS_PATH)

hash_gates = [
    (
        "MES 15m",
        expected_mes_15m_hash,
        actual_mes_15m_hash,
    ),
    (
        "Cell 8 assignments",
        expected_cell8_hash,
        actual_cell8_hash,
    ),
    (
        "Cell 9 scenarios",
        expected_cell9_hash,
        actual_cell9_hash,
    ),
]

for artifact_name, expected_hash, actual_hash in hash_gates:
    if not expected_hash:
        raise RuntimeError(
            f"CELL 10 STOPPED — no expected hash for {artifact_name}."
        )
    if expected_hash != actual_hash:
        raise RuntimeError(
            f"CELL 10 STOPPED — {artifact_name} hash mismatch.\n"
            f"Audit : {expected_hash}\n"
            f"Actual: {actual_hash}"
        )


# ------------------------------------------------------------
# 4) Load the frozen assignments and cost scenarios
# ------------------------------------------------------------
assignments = pd.read_parquet(CELL8_ASSIGNMENTS_PATH)

required_assignment_columns = {
    "decision_id",
    "decision_time",
    "label_end_time",
    "nyse_session_date",
    "instrument_id",
    "dataset_degraded_utc",
    "outer_partition",
    "purged_before_final_test",
    "outer_modeling_eligible",
}
missing_assignment_columns = (
    required_assignment_columns
    - set(assignments.columns)
)
if missing_assignment_columns:
    raise RuntimeError(
        "CELL 10 STOPPED — missing Cell 8 columns:\n"
        + ", ".join(sorted(missing_assignment_columns))
    )

assignments = assignments.copy()
assignments["decision_time"] = pd.to_datetime(
    assignments["decision_time"],
    utc=True,
    errors="raise",
)
assignments["label_end_time"] = pd.to_datetime(
    assignments["label_end_time"],
    utc=True,
    errors="raise",
)
assignments = (
    assignments
    .sort_values("decision_time")
    .reset_index(drop=True)
)

expected_label_end_time = (
    assignments["decision_time"]
    + pd.Timedelta(minutes=LABEL_HORIZON_MINUTES)
)
if not np.array_equal(
    assignments["label_end_time"].array.asi8,
    expected_label_end_time.array.asi8,
):
    raise RuntimeError(
        "CELL 10 STOPPED — Cell 8 label_end_time is not +60m."
    )

expected_rows = int(
    cell8_audit
    .get("counts", {})
    .get("decision_rows", -1)
)
expected_final_test_rows = int(
    cell8_audit
    .get("counts", {})
    .get("final_test_rows", -1)
)

if len(assignments) != expected_rows:
    raise RuntimeError(
        "CELL 10 STOPPED — assignment row count mismatch."
    )
if assignments["decision_id"].duplicated().any():
    raise RuntimeError(
        "CELL 10 STOPPED — duplicate decision_id."
    )

cost_scenarios = pd.read_csv(CELL9_SCENARIOS_PATH)
required_cost_columns = {
    "scenario",
    "total_round_trip_usd",
    "break_even_ticks",
    "break_even_index_points",
    "primary_economic_gate",
}
missing_cost_columns = required_cost_columns - set(cost_scenarios.columns)
if missing_cost_columns:
    raise RuntimeError(
        "CELL 10 STOPPED — missing Cell 9 cost columns:\n"
        + ", ".join(sorted(missing_cost_columns))
    )

cost_scenarios = cost_scenarios.copy()
cost_scenarios["scenario"] = (
    cost_scenarios["scenario"].astype(str)
)
if cost_scenarios["scenario"].duplicated().any():
    raise RuntimeError(
        "CELL 10 STOPPED — duplicate cost scenario."
    )
if int(cost_scenarios["primary_economic_gate"].sum()) != 1:
    raise RuntimeError(
        "CELL 10 STOPPED — expected exactly one primary cost scenario."
    )

primary_scenario = str(
    cell9_audit
    .get("execution_cost_contract", {})
    .get("primary_economic_gate_scenario")
)
primary_cost_row = cost_scenarios.loc[
    cost_scenarios["scenario"].eq(primary_scenario)
]
if len(primary_cost_row) != 1:
    raise RuntimeError(
        "CELL 10 STOPPED — primary cost scenario is missing."
    )
primary_cost_row = primary_cost_row.iloc[0]


# ------------------------------------------------------------
# 5) Load the clean 15-minute reference prices
# ------------------------------------------------------------
price_columns = [
    "close",
    "decision_time",
    "instrument_id",
    "active_1m_count",
    "bar_complete_15m",
    "crosses_roll",
    "dataset_degraded_utc",
]
prices = pd.read_parquet(
    MES_15M_PATH,
    columns=price_columns,
)
prices = prices.copy()
prices["decision_time"] = pd.to_datetime(
    prices["decision_time"],
    utc=True,
    errors="raise",
)

if prices["decision_time"].duplicated().any():
    raise RuntimeError(
        "CELL 10 STOPPED — duplicate decision_time in 15m prices."
    )
if prices["close"].isna().any():
    raise RuntimeError(
        "CELL 10 STOPPED — missing close in 15m prices."
    )
if (prices["close"] <= 0).any():
    raise RuntimeError(
        "CELL 10 STOPPED — non-positive close in 15m prices."
    )

price_by_time = (
    prices
    .sort_values("decision_time")
    .set_index("decision_time")
)


# ------------------------------------------------------------
# 6) Map entry and future path for development rows only
#
# Final Test rows are deliberately excluded from every price lookup.
# ------------------------------------------------------------
labels = assignments.copy()

final_test_mask = labels["outer_partition"].eq("FINAL_TEST")
development_mask = labels["outer_partition"].isin(
    ["TRAIN", "VALIDATION"]
)

observed_final_test_rows = int(final_test_mask.sum())
if observed_final_test_rows != expected_final_test_rows:
    raise RuntimeError(
        "CELL 10 STOPPED — final-test count changed."
    )
if int((~development_mask & ~final_test_mask).sum()) != 0:
    raise RuntimeError(
        "CELL 10 STOPPED — unexpected outer partition."
    )

n_rows = len(labels)
dev_positions = np.flatnonzero(development_mask.to_numpy())
dev_times = labels.loc[
    development_mask,
    "decision_time",
]
entry_instrument_expected = (
    pd.to_numeric(
        labels.loc[development_mask, "instrument_id"],
        errors="raise",
    )
    .to_numpy(dtype=float)
)

entry_close = np.full(n_rows, np.nan, dtype=float)
exit_close = np.full(n_rows, np.nan, dtype=float)
entry_present = np.zeros(n_rows, dtype=bool)
entry_instrument_match = np.zeros(n_rows, dtype=bool)
target_present = np.zeros(n_rows, dtype=bool)
horizon_present_count = np.zeros(n_rows, dtype=np.int16)
horizon_complete_count = np.zeros(n_rows, dtype=np.int16)
horizon_crosses_roll = np.zeros(n_rows, dtype=bool)
horizon_instrument_changed = np.zeros(n_rows, dtype=bool)
horizon_degraded_context = np.zeros(n_rows, dtype=bool)

for step in range(HORIZON_BAR_COUNT + 1):
    lookup_times = pd.DatetimeIndex(
        dev_times
        + pd.Timedelta(minutes=step * BAR_MINUTES)
    )
    observed = price_by_time.reindex(lookup_times)

    observed_instrument = pd.to_numeric(
        observed["instrument_id"],
        errors="coerce",
    ).to_numpy(dtype=float)
    observed_close = pd.to_numeric(
        observed["close"],
        errors="coerce",
    ).to_numpy(dtype=float)

    present = (
        np.isfinite(observed_instrument)
        & np.isfinite(observed_close)
    )
    complete = (
        present
        & observed["bar_complete_15m"]
        .fillna(False)
        .astype(bool)
        .to_numpy()
        & observed["active_1m_count"]
        .fillna(0)
        .eq(BAR_MINUTES)
        .to_numpy()
    )
    crosses_roll = (
        observed["crosses_roll"]
        .fillna(False)
        .astype(bool)
        .to_numpy()
    )
    degraded = (
        observed["dataset_degraded_utc"]
        .fillna(False)
        .astype(bool)
        .to_numpy()
    )

    if step == 0:
        entry_close[dev_positions] = observed_close
        entry_present[dev_positions] = present
        entry_instrument_match[dev_positions] = (
            present
            & np.equal(
                observed_instrument,
                entry_instrument_expected,
            )
        )
    else:
        horizon_present_count[dev_positions] += present.astype(np.int16)
        horizon_complete_count[dev_positions] += complete.astype(np.int16)
        horizon_crosses_roll[dev_positions] |= crosses_roll
        horizon_instrument_changed[dev_positions] |= (
            present
            & ~np.equal(
                observed_instrument,
                entry_instrument_expected,
            )
        )
        horizon_degraded_context[dev_positions] |= degraded

        if step == HORIZON_BAR_COUNT:
            exit_close[dev_positions] = observed_close
            target_present[dev_positions] = present

labels["entry_reference_close"] = entry_close
labels["exit_reference_close_60m"] = exit_close
labels["horizon_bars_expected"] = HORIZON_BAR_COUNT
labels["horizon_bars_present"] = horizon_present_count
labels["horizon_bars_complete"] = horizon_complete_count
labels["horizon_crosses_roll"] = horizon_crosses_roll
labels["horizon_instrument_changed"] = horizon_instrument_changed
labels["horizon_degraded_context"] = horizon_degraded_context


# ------------------------------------------------------------
# 7) One primary label-status reason per row
# ------------------------------------------------------------
label_status = np.full(n_rows, "USABLE", dtype=object)
label_status[final_test_mask.to_numpy()] = "SEALED_FINAL_TEST"


def mark_status(mask, reason):
    active = mask & np.equal(label_status, "USABLE")
    label_status[active] = reason


dev = development_mask.to_numpy()
mark_status(
    dev & ~entry_present,
    "ENTRY_BAR_MISSING",
)
mark_status(
    dev & entry_present & ~entry_instrument_match,
    "ENTRY_INSTRUMENT_MISMATCH",
)
mark_status(
    dev & ~target_present,
    "TARGET_BAR_MISSING",
)
mark_status(
    dev & (horizon_present_count != HORIZON_BAR_COUNT),
    "HORIZON_BAR_MISSING",
)
mark_status(
    dev & (horizon_complete_count != HORIZON_BAR_COUNT),
    "HORIZON_BAR_PARTIAL",
)
mark_status(
    dev & horizon_crosses_roll,
    "HORIZON_CROSSES_ROLL",
)
mark_status(
    dev & horizon_instrument_changed,
    "HORIZON_INSTRUMENT_CHANGED",
)
mark_status(
    dev
    & (
        ~np.isfinite(entry_close)
        | ~np.isfinite(exit_close)
        | (entry_close <= 0)
        | (exit_close <= 0)
    ),
    "INVALID_REFERENCE_PRICE",
)

labels["label_status"] = label_status
labels["label_usable"] = labels["label_status"].eq("USABLE")

usable_mask = labels["label_usable"].to_numpy()
unusable_development_mask = dev & ~usable_mask


# ------------------------------------------------------------
# 8) Gross +60m outcome — usable development rows only
# ------------------------------------------------------------
gross_move_points = np.full(n_rows, np.nan, dtype=float)
gross_move_usd = np.full(n_rows, np.nan, dtype=float)

gross_move_points[usable_mask] = (
    exit_close[usable_mask]
    - entry_close[usable_mask]
)
gross_move_usd[usable_mask] = (
    gross_move_points[usable_mask]
    * CONTRACT_MULTIPLIER_USD_PER_POINT
)

labels["gross_move_points_60m"] = gross_move_points
labels["gross_move_usd_60m"] = gross_move_usd
labels["gross_direction_60m"] = "UNAVAILABLE"
labels.loc[final_test_mask, "gross_direction_60m"] = "SEALED"
labels.loc[
    labels["label_usable"]
    & labels["gross_move_points_60m"].gt(0),
    "gross_direction_60m",
] = "UP"
labels.loc[
    labels["label_usable"]
    & labels["gross_move_points_60m"].lt(0),
    "gross_direction_60m",
] = "DOWN"
labels.loc[
    labels["label_usable"]
    & labels["gross_move_points_60m"].eq(0),
    "gross_direction_60m",
] = "FLAT"


# ------------------------------------------------------------
# 9) Scenario-specific economic labels
#
# LONG     when gross move > +round-trip break-even points
# SHORT    when gross move < -round-trip break-even points
# NO_TRADE otherwise
# ------------------------------------------------------------
scenario_label_columns = []
scenario_long_net_columns = []
scenario_short_net_columns = []

for scenario in cost_scenarios.itertuples(index=False):
    scenario_name = str(scenario.scenario)
    suffix = safe_name(scenario_name)
    cost_usd = float(scenario.total_round_trip_usd)
    cost_points = float(scenario.break_even_index_points)

    long_net_column = f"long_net_usd_{suffix}"
    short_net_column = f"short_net_usd_{suffix}"
    label_column = f"economic_label_{suffix}"

    labels[long_net_column] = np.nan
    labels[short_net_column] = np.nan
    labels[label_column] = "UNAVAILABLE"
    labels.loc[final_test_mask, label_column] = "SEALED"

    labels.loc[
        labels["label_usable"],
        long_net_column,
    ] = (
        labels.loc[
            labels["label_usable"],
            "gross_move_usd_60m",
        ]
        - cost_usd
    )
    labels.loc[
        labels["label_usable"],
        short_net_column,
    ] = (
        -labels.loc[
            labels["label_usable"],
            "gross_move_usd_60m",
        ]
        - cost_usd
    )

    labels.loc[
        labels["label_usable"],
        label_column,
    ] = "NO_TRADE"
    labels.loc[
        labels["label_usable"]
        & labels["gross_move_points_60m"].gt(cost_points),
        label_column,
    ] = "LONG"
    labels.loc[
        labels["label_usable"]
        & labels["gross_move_points_60m"].lt(-cost_points),
        label_column,
    ] = "SHORT"

    scenario_label_columns.append(label_column)
    scenario_long_net_columns.append(long_net_column)
    scenario_short_net_columns.append(short_net_column)

primary_suffix = safe_name(primary_scenario)
primary_label_column = f"economic_label_{primary_suffix}"
primary_long_net_column = f"long_net_usd_{primary_suffix}"
primary_short_net_column = f"short_net_usd_{primary_suffix}"

labels["economic_label_primary"] = labels[primary_label_column]
labels["primary_net_if_traded_usd"] = np.nan
labels.loc[
    labels["economic_label_primary"].eq("LONG"),
    "primary_net_if_traded_usd",
] = labels.loc[
    labels["economic_label_primary"].eq("LONG"),
    primary_long_net_column,
]
labels.loc[
    labels["economic_label_primary"].eq("SHORT"),
    "primary_net_if_traded_usd",
] = labels.loc[
    labels["economic_label_primary"].eq("SHORT"),
    primary_short_net_column,
]
labels.loc[
    labels["economic_label_primary"].eq("NO_TRADE"),
    "primary_net_if_traded_usd",
] = 0.0


# ------------------------------------------------------------
# 10) Summaries — development only; test distribution stays sealed
# ------------------------------------------------------------
development_summary = (
    labels.loc[
        development_mask,
        [
            "outer_partition",
            "label_status",
            "economic_label_primary",
        ],
    ]
    .groupby(
        [
            "outer_partition",
            "label_status",
            "economic_label_primary",
        ],
        dropna=False,
    )
    .size()
    .rename("rows")
    .reset_index()
    .sort_values(
        [
            "outer_partition",
            "label_status",
            "economic_label_primary",
        ]
    )
    .reset_index(drop=True)
)

unusable_columns = [
    "decision_id",
    "decision_time",
    "label_end_time",
    "outer_partition",
    "instrument_id",
    "label_status",
    "horizon_bars_expected",
    "horizon_bars_present",
    "horizon_bars_complete",
    "horizon_crosses_roll",
    "horizon_instrument_changed",
    "horizon_degraded_context",
]
unusable_events = labels.loc[
    unusable_development_mask,
    unusable_columns,
].copy()


# ------------------------------------------------------------
# 11) Final hard gates
# ------------------------------------------------------------
failures = []

development_rows = int(development_mask.sum())
usable_development_rows = int(
    (development_mask & labels["label_usable"]).sum()
)
unusable_development_rows = int(
    development_rows - usable_development_rows
)

if len(labels) != expected_rows:
    failures.append("Cell 10 changed the assignment row count.")
if labels["decision_id"].duplicated().any():
    failures.append("Duplicate decision_id in Cell 10 labels.")
if not labels["decision_time"].is_monotonic_increasing:
    failures.append("Cell 10 labels are not time-sorted.")
if usable_development_rows + unusable_development_rows != development_rows:
    failures.append("Development label accounting does not reconcile.")
if len(unusable_events) != unusable_development_rows:
    failures.append("Unusable-event artifact count does not reconcile.")

if labels.loc[final_test_mask, "label_usable"].any():
    failures.append("Final Test row became label-usable.")
if not labels.loc[
    final_test_mask,
    "label_status",
].eq("SEALED_FINAL_TEST").all():
    failures.append("Final Test label status is not SEALED_FINAL_TEST.")
if not labels.loc[
    final_test_mask,
    "economic_label_primary",
].eq("SEALED").all():
    failures.append("Final Test primary labels are not SEALED.")

sensitive_numeric_columns = [
    "entry_reference_close",
    "exit_reference_close_60m",
    "gross_move_points_60m",
    "gross_move_usd_60m",
    "primary_net_if_traded_usd",
] + scenario_long_net_columns + scenario_short_net_columns

if labels.loc[
    final_test_mask,
    sensitive_numeric_columns,
].notna().any().any():
    failures.append("A future-derived numeric value entered Final Test rows.")

if labels.loc[
    labels["label_usable"],
    [
        "entry_reference_close",
        "exit_reference_close_60m",
        "gross_move_points_60m",
        "gross_move_usd_60m",
    ],
].isna().any().any():
    failures.append("Usable label has a missing outcome value.")

if not labels.loc[
    labels["label_usable"],
    "horizon_bars_present",
].eq(HORIZON_BAR_COUNT).all():
    failures.append("Usable label has a missing horizon bar.")
if not labels.loc[
    labels["label_usable"],
    "horizon_bars_complete",
].eq(HORIZON_BAR_COUNT).all():
    failures.append("Usable label has a partial horizon bar.")
if labels.loc[
    labels["label_usable"],
    "horizon_crosses_roll",
].any():
    failures.append("Usable label crosses a roll bar.")
if labels.loc[
    labels["label_usable"],
    "horizon_instrument_changed",
].any():
    failures.append("Usable label changes instrument inside +60m.")

allowed_development_labels = {
    "LONG",
    "SHORT",
    "NO_TRADE",
    "UNAVAILABLE",
}
observed_development_labels = set(
    labels.loc[
        development_mask,
        "economic_label_primary",
    ].unique()
)
if not observed_development_labels.issubset(allowed_development_labels):
    failures.append("Unexpected primary economic label.")

for scenario in cost_scenarios.itertuples(index=False):
    suffix = safe_name(scenario.scenario)
    cost_points = float(scenario.break_even_index_points)
    label_column = f"economic_label_{suffix}"
    long_net_column = f"long_net_usd_{suffix}"
    short_net_column = f"short_net_usd_{suffix}"

    usable = labels["label_usable"]
    long_mask = usable & labels[label_column].eq("LONG")
    short_mask = usable & labels[label_column].eq("SHORT")
    no_trade_mask = usable & labels[label_column].eq("NO_TRADE")

    if not labels.loc[
        long_mask,
        "gross_move_points_60m",
    ].gt(cost_points).all():
        failures.append(f"{scenario.scenario}: invalid LONG threshold.")
    if not labels.loc[
        short_mask,
        "gross_move_points_60m",
    ].lt(-cost_points).all():
        failures.append(f"{scenario.scenario}: invalid SHORT threshold.")
    if not labels.loc[
        long_mask,
        long_net_column,
    ].gt(0).all():
        failures.append(f"{scenario.scenario}: LONG net is not positive.")
    if not labels.loc[
        short_mask,
        short_net_column,
    ].gt(0).all():
        failures.append(f"{scenario.scenario}: SHORT net is not positive.")

    no_trade_gross = labels.loc[
        no_trade_mask,
        "gross_move_points_60m",
    ]
    if not (
        no_trade_gross.ge(-cost_points)
        & no_trade_gross.le(cost_points)
    ).all():
        failures.append(f"{scenario.scenario}: invalid NO_TRADE band.")

trade_mask = labels["economic_label_primary"].isin(
    ["LONG", "SHORT"]
)
if not labels.loc[
    trade_mask,
    "primary_net_if_traded_usd",
].gt(0).all():
    failures.append("Primary traded labels do not have positive net value.")
if not labels.loc[
    labels["economic_label_primary"].eq("NO_TRADE"),
    "primary_net_if_traded_usd",
].eq(0).all():
    failures.append("Primary NO_TRADE net value is not zero.")


# ------------------------------------------------------------
# 12) Save versioned artifacts and hashes
# ------------------------------------------------------------
labels.to_parquet(
    CELL10_LABELS_PATH,
    index=False,
)
development_summary.to_csv(
    CELL10_SUMMARY_PATH,
    index=False,
)
unusable_events.to_parquet(
    CELL10_UNUSABLE_PATH,
    index=False,
)

artifact_hashes = {
    "input_mes_15m_sha256": actual_mes_15m_hash,
    "input_cell8_assignments_sha256": actual_cell8_hash,
    "input_cell8_audit_sha256": sha256_file(CELL8_AUDIT_PATH),
    "input_cell9_scenarios_sha256": actual_cell9_hash,
    "input_cell9_audit_sha256": sha256_file(CELL9_AUDIT_PATH),
    "economic_labels_sha256": sha256_file(CELL10_LABELS_PATH),
    "development_summary_sha256": sha256_file(CELL10_SUMMARY_PATH),
    "unusable_events_sha256": sha256_file(CELL10_UNUSABLE_PATH),
}

primary_label_counts = (
    labels.loc[
        labels["label_usable"],
        "economic_label_primary",
    ]
    .value_counts()
    .reindex(
        ["LONG", "SHORT", "NO_TRADE"],
        fill_value=0,
    )
    .astype(int)
    .to_dict()
)
unusable_reason_counts = (
    labels.loc[
        unusable_development_mask,
        "label_status",
    ]
    .value_counts()
    .sort_index()
    .astype(int)
    .to_dict()
)

cell10_audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": LABEL_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell7_policy_version": cell7_audit.get("policy_version"),
        "cell8_policy_version": cell8_audit.get("policy_version"),
        "cell9_policy_version": cell9_audit.get("policy_version"),
        "mes_15m_sha256": actual_mes_15m_hash,
        "cell8_assignments_sha256": actual_cell8_hash,
        "cell9_cost_scenarios_sha256": actual_cell9_hash,
    },
    "label_contract": {
        "instrument": "MES continuous active contract",
        "decision_price": "close of completed 15m bar at decision_time",
        "exit_price": "close of completed 15m bar at decision_time +60m",
        "horizon_minutes": LABEL_HORIZON_MINUTES,
        "future_15m_bars_required": HORIZON_BAR_COUNT,
        "future_bar_completeness_required": True,
        "same_instrument_through_horizon_required": True,
        "roll_crossing_allowed": False,
        "degraded_date_auto_exclusion": False,
        "degraded_date_retained_as_context": True,
        "economic_label_rule": (
            "LONG if gross_points > cost_points; SHORT if gross_points "
            "< -cost_points; otherwise NO_TRADE"
        ),
        "threshold_strict": True,
        "contract_multiplier_usd_per_point": (
            CONTRACT_MULTIPLIER_USD_PER_POINT
        ),
        "primary_cost_scenario": primary_scenario,
        "primary_round_trip_cost_usd": float(
            primary_cost_row["total_round_trip_usd"]
        ),
        "primary_break_even_ticks": float(
            primary_cost_row["break_even_ticks"]
        ),
        "primary_break_even_index_points": float(
            primary_cost_row["break_even_index_points"]
        ),
    },
    "counts": {
        "decision_rows": int(len(labels)),
        "development_rows": development_rows,
        "train_rows": int(
            labels["outer_partition"].eq("TRAIN").sum()
        ),
        "validation_rows": int(
            labels["outer_partition"].eq("VALIDATION").sum()
        ),
        "final_test_rows_sealed": observed_final_test_rows,
        "usable_development_labels": usable_development_rows,
        "unusable_development_labels": unusable_development_rows,
        "primary_label_counts_development_only": primary_label_counts,
        "unusable_reason_counts_development_only": (
            unusable_reason_counts
        ),
        "usable_degraded_context_rows": int(
            labels.loc[
                labels["label_usable"],
                "horizon_degraded_context",
            ].sum()
        ),
    },
    "point_in_time_safety": {
        "future_fields_are_targets_only": True,
        "future_fields_allowed_as_features": False,
        "future_quality_used_for_decision_eligibility": False,
        "future_quality_used_for_label_usability_only": True,
        "final_test_price_lookup_performed": False,
        "final_test_outcomes_computed": False,
        "final_test_label_distribution_inspected": False,
        "model_fitted": False,
    },
    "cost_scenarios": cost_scenarios[
        [
            "scenario",
            "total_round_trip_usd",
            "break_even_ticks",
            "break_even_index_points",
            "primary_economic_gate",
        ]
    ].to_dict(orient="records"),
    "artifacts": {
        "economic_labels": str(CELL10_LABELS_PATH),
        "development_label_summary": str(CELL10_SUMMARY_PATH),
        "unusable_label_events": str(CELL10_UNUSABLE_PATH),
    },
    "sha256": artifact_hashes,
    "failures": failures,
}

with open(CELL10_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        cell10_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 13) Final hard gate and compact output
# ------------------------------------------------------------
if failures:
    print("\nCELL 10 FAILURES")
    print("-" * 72)
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 10 POINT-IN-TIME ECONOMIC LABELS: FAIL\n"
        f"{CELL10_AUDIT_PATH}"
    )

print("\n" + "=" * 72)
print("CELL 10 — POINT-IN-TIME +60m ECONOMIC LABELS")
print("=" * 72)

print("\n[1] UPSTREAM BINDING")
print("Decision rows                 :", f"{len(labels):,}")
print("Cell 8 assignments SHA256     :", actual_cell8_hash)
print("Cell 9 cost scenarios SHA256  :", actual_cell9_hash)

print("\n[2] LABEL CONTRACT")
print("Reference                     : completed 15m close → +60m close")
print("Required future bars          :", HORIZON_BAR_COUNT)
print("Same instrument required      : True")
print("Roll crossing allowed         : False")
print("Primary cost scenario         :", primary_scenario)
print(
    "Primary break-even           :",
    f"{float(primary_cost_row['break_even_ticks']):.3f} ticks / "
    f"{float(primary_cost_row['break_even_index_points']):.3f} points",
)

print("\n[3] DEVELOPMENT LABEL AVAILABILITY")
print("Train + Validation rows       :", f"{development_rows:,}")
print("Usable labels                 :", f"{usable_development_rows:,}")
print("Unusable labels               :", f"{unusable_development_rows:,}")
print("Unusable reasons              :", unusable_reason_counts)

print("\n[4] PRIMARY LABEL COUNTS — DEVELOPMENT ONLY")
for label_name in ["LONG", "SHORT", "NO_TRADE"]:
    print(
        f"{label_name:30s}:",
        f"{primary_label_counts[label_name]:,}",
    )

print("\n[5] FINAL TEST SAFETY")
print("Final-test rows               :", f"{observed_final_test_rows:,}")
print("Price lookup performed        : False")
print("Outcomes computed             : False")
print("Labels                        : SEALED")

print("\n[6] SAVED ARTIFACTS")
print("Economic labels :", CELL10_LABELS_PATH)
print("Label summary   :", CELL10_SUMMARY_PATH)
print("Unusable events :", CELL10_UNUSABLE_PATH)
print("Cell 10 audit   :", CELL10_AUDIT_PATH)
print("Labels SHA256   :", artifact_hashes["economic_labels_sha256"])

print("\n" + "=" * 72)
print("CELL 10 POINT-IN-TIME ECONOMIC LABELS: PASS")
print("=" * 72)

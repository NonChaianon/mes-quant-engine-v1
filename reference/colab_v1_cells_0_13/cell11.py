# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 11 — COST TEMPORALITY REGISTRY
# ============================================================
#
# PURPOSE
# -------
# Make the time meaning of Cell 9 explicit without inventing historical
# fees. Cell 9 remains a dated current-deployment cost snapshot. This
# cell creates a semantic sidecar that distinguishes:
#
# - CURRENT_DEPLOYMENT_COUNTERFACTUAL
# - STRESS_COUNTERFACTUAL
# - HISTORICAL_VINTAGE (OPEN; unavailable until sourced)
#
# No price, return, label distribution, prediction, or final-test
# outcome is read in this cell.
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1) Paths and policy
# ------------------------------------------------------------
PROJECT_DIR = Path("/content/drive/MyDrive/Quant_Lab")
CLEAN_DIR = PROJECT_DIR / "Data" / "MES_Clean_Pipeline_V1"

CELL9_PARAMETERS_PATH = CLEAN_DIR / "cell9_cost_parameters_v1.csv"
CELL9_SCENARIOS_PATH = CLEAN_DIR / "cell9_cost_scenarios_v1.csv"
CELL9_AUDIT_PATH = CLEAN_DIR / "cell9_cost_model_audit.json"

CELL11_SEMANTIC_SCENARIOS_PATH = (
    CLEAN_DIR / "cell11_cost_scenarios_semantic_v1.csv"
)
CELL11_VINTAGE_REGISTRY_PATH = (
    CLEAN_DIR / "cell11_fee_vintage_registry_v1.csv"
)
CELL11_AUDIT_PATH = CLEAN_DIR / "cell11_cost_temporality_audit.json"

COST_TEMPORALITY_POLICY_VERSION = "MES_V1_COST_TEMPORALITY_1.0"
EXPECTED_CELL9_POLICY = "MES_V1_COST_MODEL_1.0"


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


# ------------------------------------------------------------
# 3) Upstream gates
# ------------------------------------------------------------
required_paths = [
    CELL9_PARAMETERS_PATH,
    CELL9_SCENARIOS_PATH,
    CELL9_AUDIT_PATH,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
if missing_paths:
    raise RuntimeError(
        "CELL 11 STOPPED — missing Cell 9 artifacts:\n"
        + "\n".join(missing_paths)
        + "\n\nRun the corrected Cell 9 first."
    )

cell9_audit = load_json(CELL9_AUDIT_PATH)
if cell9_audit.get("status") != "PASS":
    raise RuntimeError("CELL 11 STOPPED — Cell 9 audit is not PASS.")
if cell9_audit.get("failures", []):
    raise RuntimeError("CELL 11 STOPPED — Cell 9 audit has failures.")
if cell9_audit.get("policy_version") != EXPECTED_CELL9_POLICY:
    raise RuntimeError(
        "CELL 11 STOPPED — unexpected Cell 9 policy version: "
        f"{cell9_audit.get('policy_version')}"
    )

expected_scenario_hash = (
    cell9_audit.get("sha256", {}).get("cost_scenarios_sha256")
)
actual_scenario_hash = sha256_file(CELL9_SCENARIOS_PATH)
if not expected_scenario_hash or expected_scenario_hash != actual_scenario_hash:
    raise RuntimeError(
        "CELL 11 STOPPED — Cell 9 scenario hash mismatch.\n"
        f"Audit : {expected_scenario_hash}\n"
        f"Actual: {actual_scenario_hash}"
    )

expected_parameter_hash = (
    cell9_audit.get("sha256", {}).get("cost_parameters_sha256")
)
actual_parameter_hash = sha256_file(CELL9_PARAMETERS_PATH)
if not expected_parameter_hash or expected_parameter_hash != actual_parameter_hash:
    raise RuntimeError(
        "CELL 11 STOPPED — Cell 9 parameter hash mismatch.\n"
        f"Audit : {expected_parameter_hash}\n"
        f"Actual: {actual_parameter_hash}"
    )


# ------------------------------------------------------------
# 4) Build explicit scenario semantics
# ------------------------------------------------------------
scenarios = pd.read_csv(CELL9_SCENARIOS_PATH)
parameters = pd.read_csv(CELL9_PARAMETERS_PATH)

required_scenario_columns = {
    "scenario",
    "status",
    "total_round_trip_usd",
    "direct_fee_round_trip_usd",
    "break_even_ticks",
    "break_even_index_points",
    "primary_economic_gate",
}
missing_columns = required_scenario_columns - set(scenarios.columns)
if missing_columns:
    raise RuntimeError(
        "CELL 11 STOPPED — missing cost-scenario columns:\n"
        + ", ".join(sorted(missing_columns))
    )

source_snapshot_date = str(
    cell9_audit.get("sources", {}).get("source_snapshot_date")
)
if source_snapshot_date in {"None", "", "nan"}:
    raise RuntimeError("CELL 11 STOPPED — Cell 9 source date is missing.")

semantic = scenarios.copy()
semantic["cost_view"] = np.where(
    semantic["scenario"].astype(str).eq("STRESS"),
    "STRESS",
    "CURRENT_DEPLOYMENT",
)
semantic["application_mode"] = "COUNTERFACTUAL_ALL_DEVELOPMENT_DATES"
semantic["fee_vintage_id"] = (
    "CURRENT_SNAPSHOT_" + source_snapshot_date.replace("-", "_")
)
semantic["source_observed_as_of"] = source_snapshot_date
semantic["historical_actual_claim"] = False
semantic["historical_matching_allowed"] = False
semantic["labels_allowed"] = True
semantic["semantic_status"] = "PROVISIONAL"
semantic["label_semantics"] = np.where(
    semantic["cost_view"].eq("STRESS"),
    "STRESS_COUNTERFACTUAL",
    "CURRENT_DEPLOYMENT_COUNTERFACTUAL",
)

semantic = semantic.sort_values(
    ["primary_economic_gate", "scenario"],
    ascending=[False, True],
).reset_index(drop=True)


# ------------------------------------------------------------
# 5) Effective-dated vintage registry
#
# The current snapshot is evidence of what was observed on one date.
# It is not assigned an invented historical effective interval.
# ------------------------------------------------------------
fee_sources = cell9_audit.get("sources", {})
fee_snapshot = cell9_audit.get("fee_snapshot", {})

vintage_rows = [
    {
        "vintage_id": "CURRENT_SNAPSHOT_" + source_snapshot_date.replace("-", "_"),
        "cost_view": "CURRENT_DEPLOYMENT",
        "observed_as_of": source_snapshot_date,
        "effective_from": pd.NA,
        "effective_to": pd.NA,
        "broker_entity": "IBKR_ENTITY_UNCONFIRMED",
        "pricing_plan": "MES_NON_MEMBER_LE_1000_MONTHLY_CONTRACTS",
        "volume_tier": "LE_1000_MONTHLY_CONTRACTS",
        "ibkr_execution_fee_per_side_usd": fee_snapshot.get(
            "ibkr_execution_fee_per_side_usd"
        ),
        "cme_exchange_fee_per_side_usd": fee_snapshot.get(
            "cme_exchange_fee_per_side_usd"
        ),
        "regulatory_fee_per_side_usd": fee_snapshot.get(
            "regulatory_fee_per_side_usd"
        ),
        "clearing_fee_per_side_usd": fee_snapshot.get(
            "clearing_fee_per_side_usd"
        ),
        "tax_or_entity_adjustment_per_side_usd": fee_snapshot.get(
            "tax_or_entity_adjustment_per_side_usd"
        ),
        "source_cme_fee_schedule": fee_sources.get("cme_fee_schedule"),
        "source_ibkr_commissions": fee_sources.get("ibkr_futures_commissions"),
        "source_ibkr_cme_recovery": fee_sources.get("ibkr_cme_fee_recovery"),
        "source_document_sha256": pd.NA,
        "eligible_for_historical_matching": False,
        "status": "PROVISIONAL_CURRENT_SNAPSHOT_ONLY",
        "notes": (
            "Observed current snapshot only; effective start/end and actual "
            "IBKR entity remain unverified."
        ),
    },
    {
        "vintage_id": "HISTORICAL_VINTAGE_UNAVAILABLE",
        "cost_view": "HISTORICAL_VINTAGE",
        "observed_as_of": pd.NA,
        "effective_from": pd.NA,
        "effective_to": pd.NA,
        "broker_entity": "OPEN",
        "pricing_plan": "OPEN",
        "volume_tier": "CAUSAL_MONTH_TO_DATE_VOLUME_REQUIRED",
        "ibkr_execution_fee_per_side_usd": np.nan,
        "cme_exchange_fee_per_side_usd": np.nan,
        "regulatory_fee_per_side_usd": np.nan,
        "clearing_fee_per_side_usd": np.nan,
        "tax_or_entity_adjustment_per_side_usd": np.nan,
        "source_cme_fee_schedule": "HISTORICAL_ARCHIVE_REQUIRED",
        "source_ibkr_commissions": "HISTORICAL_ARCHIVE_REQUIRED",
        "source_ibkr_cme_recovery": "HISTORICAL_ARCHIVE_REQUIRED",
        "source_document_sha256": pd.NA,
        "eligible_for_historical_matching": False,
        "status": "OPEN",
        "notes": (
            "No historical numeric value is invented. Historical labels stay "
            "disabled until sourced, non-overlapping vintages cover every "
            "development decision date."
        ),
    },
]
vintages = pd.DataFrame(vintage_rows)


# ------------------------------------------------------------
# 6) Hard semantic gates
# ------------------------------------------------------------
failures = []

allowed_views = {"CURRENT_DEPLOYMENT", "STRESS"}
if not set(semantic["cost_view"]).issubset(allowed_views):
    failures.append("Unexpected cost_view in semantic scenarios.")
if int(semantic["primary_economic_gate"].sum()) != 1:
    failures.append("Expected exactly one primary economic gate.")

primary = semantic.loc[semantic["primary_economic_gate"]]
if len(primary) != 1 or not primary["cost_view"].eq("CURRENT_DEPLOYMENT").all():
    failures.append("Primary gate is not exactly one CURRENT_DEPLOYMENT row.")
if semantic["historical_actual_claim"].astype(bool).any():
    failures.append("A current/stress scenario claims historical actuality.")
if semantic["historical_matching_allowed"].astype(bool).any():
    failures.append("Current snapshot was enabled for historical matching.")

numeric_cost_columns = [
    "total_round_trip_usd",
    "break_even_ticks",
    "break_even_index_points",
]
numeric_costs = semantic[numeric_cost_columns].apply(
    pd.to_numeric,
    errors="coerce",
)
if not np.isfinite(numeric_costs.to_numpy(dtype=float)).all():
    failures.append("Non-finite scenario cost detected.")
if numeric_costs.lt(0).any().any():
    failures.append("Negative scenario cost detected.")

stress_total = semantic.loc[
    semantic["cost_view"].eq("STRESS"),
    "total_round_trip_usd",
]
primary_total = float(primary.iloc[0]["total_round_trip_usd"])
if stress_total.empty or not stress_total.ge(primary_total).all():
    failures.append("Stress cost is below the primary current cost.")

historical_rows = vintages["cost_view"].eq("HISTORICAL_VINTAGE")
historical_numeric = vintages.loc[
    historical_rows,
    [
        "ibkr_execution_fee_per_side_usd",
        "cme_exchange_fee_per_side_usd",
        "regulatory_fee_per_side_usd",
        "clearing_fee_per_side_usd",
        "tax_or_entity_adjustment_per_side_usd",
    ],
]
if historical_numeric.notna().any().any():
    failures.append("An unsourced historical numeric fee was created.")
if vintages.loc[historical_rows, "eligible_for_historical_matching"].any():
    failures.append("Unavailable historical vintage was enabled.")

current_rows = vintages["cost_view"].eq("CURRENT_DEPLOYMENT")
current_component_columns = [
    "ibkr_execution_fee_per_side_usd",
    "cme_exchange_fee_per_side_usd",
    "regulatory_fee_per_side_usd",
    "clearing_fee_per_side_usd",
    "tax_or_entity_adjustment_per_side_usd",
]
current_components = vintages.loc[
    current_rows, current_component_columns
].apply(pd.to_numeric, errors="coerce")
if len(current_components) != 1:
    failures.append("Expected exactly one current fee-snapshot row.")
elif not np.isfinite(current_components.to_numpy(dtype=float)).all():
    failures.append("Current fee snapshot has a missing/non-finite component.")
elif current_components.lt(0).any().any():
    failures.append("Current fee snapshot has a negative component.")
else:
    component_direct_round_trip = float(
        2.0 * current_components.iloc[0].sum()
    )
    audited_direct_round_trip = float(
        fee_snapshot.get("direct_fee_round_trip_usd", np.nan)
    )
    fees_only_rows = semantic.loc[
        semantic["scenario"].astype(str).eq("FEES_ONLY")
    ]
    if len(fees_only_rows) != 1:
        failures.append("Expected exactly one FEES_ONLY scenario.")
        fees_only_direct_round_trip = np.nan
    else:
        fees_only_direct_round_trip = float(
            fees_only_rows.iloc[0]["direct_fee_round_trip_usd"]
        )
    if not np.isclose(
        component_direct_round_trip, audited_direct_round_trip, atol=1e-12
    ):
        failures.append("Current fee components do not reconcile to Cell 9 audit.")
    if np.isfinite(fees_only_direct_round_trip) and not np.isclose(
        component_direct_round_trip, fees_only_direct_round_trip, atol=1e-12
    ):
        failures.append("Current fee components do not reconcile to FEES_ONLY.")

if str(fee_snapshot.get("as_of")) != source_snapshot_date:
    failures.append("Fee snapshot date differs from the source snapshot date.")


# ------------------------------------------------------------
# 7) Save artifacts and audit
# ------------------------------------------------------------
semantic.to_csv(CELL11_SEMANTIC_SCENARIOS_PATH, index=False)
vintages.to_csv(CELL11_VINTAGE_REGISTRY_PATH, index=False)

artifact_hashes = {
    "input_cell9_parameters_sha256": actual_parameter_hash,
    "input_cell9_scenarios_sha256": actual_scenario_hash,
    "input_cell9_audit_sha256": sha256_file(CELL9_AUDIT_PATH),
    "semantic_scenarios_sha256": sha256_file(CELL11_SEMANTIC_SCENARIOS_PATH),
    "fee_vintage_registry_sha256": sha256_file(CELL11_VINTAGE_REGISTRY_PATH),
}

audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": COST_TEMPORALITY_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell9_policy_version": cell9_audit.get("policy_version"),
        "cell9_scenarios_sha256": actual_scenario_hash,
    },
    "semantic_contract": {
        "current_deployment": "PROVISIONAL_COUNTERFACTUAL",
        "stress": "PROVISIONAL_COUNTERFACTUAL",
        "historical_vintage": "OPEN",
        "historical_actual_labels_available": False,
        "historical_coverage_ratio": 0.0,
        "historical_labels_allowed": False,
        "current_snapshot_historical_matching_allowed": False,
        "volume_tier_rule": (
            "future historical implementation must use causal cumulative "
            "month-to-date contracts only"
        ),
    },
    "cell10_interpretation": {
        "existing_primary_label_status": "PROVISIONAL",
        "existing_primary_label_semantics": (
            "CURRENT_DEPLOYMENT_COUNTERFACTUAL; NOT HISTORICAL_ACTUAL_PNL"
        ),
    },
    "scenario_count": int(len(semantic)),
    "vintage_registry_rows": int(len(vintages)),
    "artifacts": {
        "semantic_scenarios": str(CELL11_SEMANTIC_SCENARIOS_PATH),
        "fee_vintage_registry": str(CELL11_VINTAGE_REGISTRY_PATH),
    },
    "sha256": artifact_hashes,
    "open_items": [
        "Collect effective-dated CME and IBKR historical fee sources.",
        "Confirm the user's IBKR legal entity, pricing plan, and taxes.",
        "Add historical bid/ask or a sourced regime proxy for execution costs.",
        "Rebuild historical-vintage labels only after 100% causal coverage.",
    ],
    "failures": failures,
}

with open(CELL11_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

if failures:
    print("\nCELL 11 FAILURES")
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 11 COST TEMPORALITY REGISTRY: FAIL\n"
        f"{CELL11_AUDIT_PATH}"
    )

print("\n" + "=" * 72)
print("CELL 11 — COST TEMPORALITY REGISTRY")
print("=" * 72)
print("Cell 9 scenario SHA256      :", actual_scenario_hash)
print("Current deployment semantics: PROVISIONAL COUNTERFACTUAL")
print("Stress semantics            : PROVISIONAL COUNTERFACTUAL")
print("Historical vintage          : OPEN")
print("Historical numeric invented : False")
print("Historical labels allowed   : False")
print("Semantic scenarios          :", CELL11_SEMANTIC_SCENARIOS_PATH)
print("Vintage registry            :", CELL11_VINTAGE_REGISTRY_PATH)
print("Cell 11 audit               :", CELL11_AUDIT_PATH)
print("\nCELL 11 COST TEMPORALITY REGISTRY: PASS")
print("=" * 72)

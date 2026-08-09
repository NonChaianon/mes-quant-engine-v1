# CELL 9 — RESEARCH COST MODEL CONTRACT
# ============================================================
#
# PURPOSE
# -------
# Freeze a transparent, versioned transaction-cost contract before
# any economic label, signal threshold, or model is finalized.
#
# This cell:
# 1) binds itself to the exact Cell 8 split-assignment hash,
# 2) records the official MES contract mechanics,
# 3) snapshots current low-volume IBKR/CME direct fees,
# 4) creates fees-only, base, conservative, and stress scenarios,
# 5) converts all-in round-trip cost to USD, ticks, and index points,
# 6) saves parameters, scenarios, hashes, sources, and audit gates.
#
# IMPORTANT
# ---------
# - No price return, direction label, P&L, or model is created here.
# - Final-test outcomes are not loaded or inspected.
# - Live fees depend on account entity, plan, volume, tax, and date.
#   Therefore fee and execution assumptions remain PROVISIONAL until
#   reconciled against the user's actual IBKR statement/fills.
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
# 1) Paths
# ------------------------------------------------------------
PROJECT_DIR = Path("/content/drive/MyDrive/Quant_Lab")
CLEAN_DIR = PROJECT_DIR / "Data" / "MES_Clean_Pipeline_V1"

CELL8_ASSIGNMENTS_PATH = (
    CLEAN_DIR / "cell8_purged_split_assignments_v1.parquet"
)
CELL8_AUDIT_PATH = CLEAN_DIR / "cell8_purged_split_audit.json"

CELL9_PARAMETERS_PATH = CLEAN_DIR / "cell9_cost_parameters_v1.csv"
CELL9_SCENARIOS_PATH = CLEAN_DIR / "cell9_cost_scenarios_v1.csv"
CELL9_AUDIT_PATH = CLEAN_DIR / "cell9_cost_model_audit.json"


# ------------------------------------------------------------
# 2) Version and official source snapshot
# ------------------------------------------------------------
COST_POLICY_VERSION = "MES_V1_COST_MODEL_1.0"
EXPECTED_CELL8_POLICY = "MES_V1_PURGED_SPLIT_1.0"
SOURCE_SNAPSHOT_DATE = "2026-08-09"

CME_CONTRACT_SOURCE = (
    "https://www.cmegroup.com/markets/equities/sp/"
    "micro-e-mini-sandp-500.contractSpecs.html"
)
CME_FEE_SOURCE = (
    "https://www.cmegroup.com/company/files/"
    "cme-fee-schedule-2026-02-01.pdf"
)
IBKR_COMMISSION_SOURCE = (
    "https://www.interactivebrokers.com/en/pricing/"
    "commissions-futures.php"
)
IBKR_CME_FEE_SOURCE = (
    "https://www.interactivebrokers.com/en/accounts/fees/CME.php"
)


# ------------------------------------------------------------
# 3) Frozen MES mechanics — official contract specification
# ------------------------------------------------------------
SYMBOL = "MES"
CURRENCY = "USD"
CONTRACT_MULTIPLIER_USD_PER_POINT = 5.00
TICK_SIZE_POINTS = 0.25
TICK_VALUE_USD = (
    CONTRACT_MULTIPLIER_USD_PER_POINT
    * TICK_SIZE_POINTS
)


# ------------------------------------------------------------
# 4) Dated direct-fee snapshot — PROVISIONAL
#
# Account/pricing assumptions:
# - non-member client,
# - IBKR Spot-Quoted/E-micro futures group containing MES,
# - <= 1,000 monthly contracts,
# - one contract, each side,
# - no give-up surcharge,
# - tax/entity adjustments not yet supplied by the user.
# ------------------------------------------------------------
IBKR_EXECUTION_FEE_PER_SIDE_USD = 0.25
CME_EXCHANGE_FEE_PER_SIDE_USD = 0.35
REGULATORY_FEE_PER_SIDE_USD = 0.01
CLEARING_FEE_PER_SIDE_USD = 0.00
TAX_OR_ENTITY_ADJUSTMENT_PER_SIDE_USD = 0.00

DIRECT_FEE_PER_SIDE_USD = (
    IBKR_EXECUTION_FEE_PER_SIDE_USD
    + CME_EXCHANGE_FEE_PER_SIDE_USD
    + REGULATORY_FEE_PER_SIDE_USD
    + CLEARING_FEE_PER_SIDE_USD
    + TAX_OR_ENTITY_ADJUSTMENT_PER_SIDE_USD
)
DIRECT_FEE_ROUND_TRIP_USD = 2.0 * DIRECT_FEE_PER_SIDE_USD

# V1 exits within +60 minutes and before the NYSE-policy close buffer,
# so no overnight-position fee is included in this intraday contract.
OVERNIGHT_FEE_ROUND_TRIP_USD = 0.00


# ------------------------------------------------------------
# 5) Scenario contract
#
# All tick inputs are per side. Spread is represented as half-spread
# paid on each marketable fill. Slippage, latency, and impact are kept
# separate so later real fills can replace each assumption cleanly.
# ------------------------------------------------------------
PRIMARY_ECONOMIC_GATE_SCENARIO = "CONSERVATIVE"

SCENARIO_INPUTS = [
    {
        "scenario": "FEES_ONLY",
        "purpose": "hard lower bound; not a tradable expectation",
        "spread_half_ticks_per_side": 0.00,
        "slippage_ticks_per_side": 0.00,
        "latency_ticks_per_side": 0.00,
        "market_impact_ticks_per_side": 0.00,
        "status": "PROVISIONAL",
    },
    {
        "scenario": "BASE",
        "purpose": "one-tick quoted spread plus modest adverse fill",
        "spread_half_ticks_per_side": 0.50,
        "slippage_ticks_per_side": 0.25,
        "latency_ticks_per_side": 0.00,
        "market_impact_ticks_per_side": 0.00,
        "status": "PROVISIONAL",
    },
    {
        "scenario": "CONSERVATIVE",
        "purpose": "primary economic gate before real fill calibration",
        "spread_half_ticks_per_side": 0.50,
        "slippage_ticks_per_side": 0.50,
        "latency_ticks_per_side": 0.25,
        "market_impact_ticks_per_side": 0.25,
        "status": "PROVISIONAL",
    },
    {
        "scenario": "STRESS",
        "purpose": "wider spread and adverse execution stress test",
        "spread_half_ticks_per_side": 1.00,
        "slippage_ticks_per_side": 1.00,
        "latency_ticks_per_side": 0.50,
        "market_impact_ticks_per_side": 0.50,
        "status": "PROVISIONAL",
    },
]


# ------------------------------------------------------------
# 6) Helpers
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
# 7) Bind to Cell 8 without inspecting outcomes
# ------------------------------------------------------------
for required_path in [CELL8_ASSIGNMENTS_PATH, CELL8_AUDIT_PATH]:
    if not required_path.exists():
        raise RuntimeError(
            "CELL 9 STOPPED — missing Cell 8 artifact:\n"
            f"{required_path}\n\n"
            "Run Cell 0 → Cell 8 first."
        )

cell8_audit = load_json(CELL8_AUDIT_PATH)

if cell8_audit.get("status") != "PASS":
    raise RuntimeError(
        "CELL 9 STOPPED — Cell 8 audit status is not PASS."
    )
if cell8_audit.get("failures", []):
    raise RuntimeError(
        "CELL 9 STOPPED — Cell 8 audit contains failures."
    )
if cell8_audit.get("policy_version") != EXPECTED_CELL8_POLICY:
    raise RuntimeError(
        "CELL 9 STOPPED — unexpected Cell 8 policy version:\n"
        f"{cell8_audit.get('policy_version')}"
    )

expected_cell8_hash = (
    cell8_audit
    .get("sha256", {})
    .get("split_assignments_sha256")
)
actual_cell8_hash = sha256_file(CELL8_ASSIGNMENTS_PATH)

if not expected_cell8_hash:
    raise RuntimeError(
        "CELL 9 STOPPED — Cell 8 audit has no assignments SHA-256."
    )
if actual_cell8_hash != expected_cell8_hash:
    raise RuntimeError(
        "CELL 9 STOPPED — Cell 8 assignments hash mismatch.\n"
        f"Audit : {expected_cell8_hash}\n"
        f"Actual: {actual_cell8_hash}"
    )

# Load assignment identifiers only. No market price, future return,
# label, prediction, or final-test performance is inspected.
assignment_columns = [
    "decision_id",
    "outer_partition",
]
assignments = pd.read_parquet(
    CELL8_ASSIGNMENTS_PATH,
    columns=assignment_columns,
)

expected_decision_rows = int(
    cell8_audit
    .get("counts", {})
    .get("decision_rows", -1)
)
expected_final_test_rows = int(
    cell8_audit
    .get("counts", {})
    .get("final_test_rows", -1)
)
observed_final_test_rows = int(
    assignments["outer_partition"]
    .eq("FINAL_TEST")
    .sum()
)

if len(assignments) != expected_decision_rows:
    raise RuntimeError(
        "CELL 9 STOPPED — Cell 8 assignment count mismatch."
    )
if assignments["decision_id"].duplicated().any():
    raise RuntimeError(
        "CELL 9 STOPPED — duplicate decision_id in Cell 8 assignments."
    )
if observed_final_test_rows != expected_final_test_rows:
    raise RuntimeError(
        "CELL 9 STOPPED — final-test row count changed."
    )


# ------------------------------------------------------------
# 8) Build the parameter registry
# ------------------------------------------------------------
parameter_rows = [
    {
        "parameter": "contract_multiplier_usd_per_point",
        "value": CONTRACT_MULTIPLIER_USD_PER_POINT,
        "unit": "USD/index_point/contract",
        "status": "LOCKED",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": CME_CONTRACT_SOURCE,
        "notes": "Official MES contract multiplier.",
    },
    {
        "parameter": "tick_size_points",
        "value": TICK_SIZE_POINTS,
        "unit": "index_points",
        "status": "LOCKED",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": CME_CONTRACT_SOURCE,
        "notes": "Official minimum outright price fluctuation.",
    },
    {
        "parameter": "tick_value_usd",
        "value": TICK_VALUE_USD,
        "unit": "USD/tick/contract",
        "status": "LOCKED",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": CME_CONTRACT_SOURCE,
        "notes": "Derived exactly as multiplier × tick size.",
    },
    {
        "parameter": "ibkr_execution_fee_per_side_usd",
        "value": IBKR_EXECUTION_FEE_PER_SIDE_USD,
        "unit": "USD/side/contract",
        "status": "PROVISIONAL",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": IBKR_COMMISSION_SOURCE,
        "notes": (
            "MES group; <=1,000 monthly contracts; verify account plan."
        ),
    },
    {
        "parameter": "cme_exchange_fee_per_side_usd",
        "value": CME_EXCHANGE_FEE_PER_SIDE_USD,
        "unit": "USD/side/contract",
        "status": "PROVISIONAL",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": IBKR_CME_FEE_SOURCE,
        "notes": "Non-member Micro E-mini futures recovery charge.",
    },
    {
        "parameter": "regulatory_fee_per_side_usd",
        "value": REGULATORY_FEE_PER_SIDE_USD,
        "unit": "USD/side/contract",
        "status": "PROVISIONAL",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": IBKR_CME_FEE_SOURCE,
        "notes": "NFA regulatory fee recovery charge shown by IBKR.",
    },
    {
        "parameter": "clearing_fee_per_side_usd",
        "value": CLEARING_FEE_PER_SIDE_USD,
        "unit": "USD/side/contract",
        "status": "PROVISIONAL",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": IBKR_COMMISSION_SOURCE,
        "notes": "Zero working assumption; reconcile to actual statement.",
    },
    {
        "parameter": "tax_or_entity_adjustment_per_side_usd",
        "value": TAX_OR_ENTITY_ADJUSTMENT_PER_SIDE_USD,
        "unit": "USD/side/contract",
        "status": "OPEN",
        "as_of": SOURCE_SNAPSHOT_DATE,
        "source": "USER_IBKR_STATEMENT_REQUIRED",
        "notes": "Depends on IBKR entity, residence, and applicable tax.",
    },
]

parameters = pd.DataFrame(parameter_rows)


# ------------------------------------------------------------
# 9) Calculate cost scenarios
# ------------------------------------------------------------
scenario_rows = []

for item in SCENARIO_INPUTS:
    spread_round_trip_usd = (
        2.0
        * item["spread_half_ticks_per_side"]
        * TICK_VALUE_USD
    )
    slippage_round_trip_usd = (
        2.0
        * item["slippage_ticks_per_side"]
        * TICK_VALUE_USD
    )
    latency_round_trip_usd = (
        2.0
        * item["latency_ticks_per_side"]
        * TICK_VALUE_USD
    )
    market_impact_round_trip_usd = (
        2.0
        * item["market_impact_ticks_per_side"]
        * TICK_VALUE_USD
    )

    total_round_trip_usd = (
        DIRECT_FEE_ROUND_TRIP_USD
        + OVERNIGHT_FEE_ROUND_TRIP_USD
        + spread_round_trip_usd
        + slippage_round_trip_usd
        + latency_round_trip_usd
        + market_impact_round_trip_usd
    )

    scenario_rows.append(
        {
            **item,
            "contracts": 1,
            "direct_fee_per_side_usd": DIRECT_FEE_PER_SIDE_USD,
            "direct_fee_round_trip_usd": DIRECT_FEE_ROUND_TRIP_USD,
            "spread_round_trip_usd": spread_round_trip_usd,
            "slippage_round_trip_usd": slippage_round_trip_usd,
            "latency_round_trip_usd": latency_round_trip_usd,
            "market_impact_round_trip_usd": (
                market_impact_round_trip_usd
            ),
            "overnight_fee_round_trip_usd": (
                OVERNIGHT_FEE_ROUND_TRIP_USD
            ),
            "total_round_trip_usd": total_round_trip_usd,
            "break_even_ticks": total_round_trip_usd / TICK_VALUE_USD,
            "break_even_index_points": (
                total_round_trip_usd
                / CONTRACT_MULTIPLIER_USD_PER_POINT
            ),
            "primary_economic_gate": (
                item["scenario"]
                == PRIMARY_ECONOMIC_GATE_SCENARIO
            ),
        }
    )

scenarios = pd.DataFrame(scenario_rows)

# Remove binary floating-point display noise from saved contracts
# (for example 3.0949999999999998 -> 3.095000).
scenario_round_columns = [
    "direct_fee_per_side_usd",
    "direct_fee_round_trip_usd",
    "spread_round_trip_usd",
    "slippage_round_trip_usd",
    "latency_round_trip_usd",
    "market_impact_round_trip_usd",
    "overnight_fee_round_trip_usd",
    "total_round_trip_usd",
    "break_even_ticks",
    "break_even_index_points",
]
scenarios[scenario_round_columns] = (
    scenarios[scenario_round_columns]
    .round(6)
)


# ------------------------------------------------------------
# 10) Hard cost-model gates
# ------------------------------------------------------------
failures = []

if not np.isclose(TICK_VALUE_USD, 1.25, atol=1e-12):
    failures.append("MES tick value is not exactly USD 1.25.")
if not np.isclose(DIRECT_FEE_PER_SIDE_USD, 0.61, atol=1e-12):
    failures.append("Direct fee snapshot does not sum to USD 0.61/side.")
if not np.isclose(DIRECT_FEE_ROUND_TRIP_USD, 1.22, atol=1e-12):
    failures.append("Direct round-trip fee is not USD 1.22.")

numeric_cost_columns = [
    "direct_fee_round_trip_usd",
    "spread_round_trip_usd",
    "slippage_round_trip_usd",
    "latency_round_trip_usd",
    "market_impact_round_trip_usd",
    "overnight_fee_round_trip_usd",
    "total_round_trip_usd",
    "break_even_ticks",
    "break_even_index_points",
]

if scenarios[numeric_cost_columns].isna().any().any():
    failures.append("Missing numeric value in cost scenarios.")
if (scenarios[numeric_cost_columns] < 0).any().any():
    failures.append("Negative cost component in scenario table.")
if scenarios["scenario"].duplicated().any():
    failures.append("Duplicate scenario name.")

expected_scenario_order = [
    "FEES_ONLY",
    "BASE",
    "CONSERVATIVE",
    "STRESS",
]
if scenarios["scenario"].tolist() != expected_scenario_order:
    failures.append("Scenario ordering/version contract changed.")

if not scenarios["total_round_trip_usd"].is_monotonic_increasing:
    failures.append("Scenario total costs are not monotonic.")
if int(scenarios["primary_economic_gate"].sum()) != 1:
    failures.append("Primary economic gate must select exactly one scenario.")
if PRIMARY_ECONOMIC_GATE_SCENARIO not in set(scenarios["scenario"]):
    failures.append("Primary economic gate scenario is missing.")

recomputed_total = (
    scenarios[
        [
            "direct_fee_round_trip_usd",
            "spread_round_trip_usd",
            "slippage_round_trip_usd",
            "latency_round_trip_usd",
            "market_impact_round_trip_usd",
            "overnight_fee_round_trip_usd",
        ]
    ].sum(axis=1)
)
if not np.allclose(
    recomputed_total.to_numpy(),
    scenarios["total_round_trip_usd"].to_numpy(),
    atol=1e-12,
):
    failures.append("Scenario components do not reconcile to total cost.")

if not np.allclose(
    (
        scenarios["break_even_index_points"]
        / TICK_SIZE_POINTS
    ).to_numpy(),
    scenarios["break_even_ticks"].to_numpy(),
    atol=1e-12,
):
    failures.append("Tick and index-point break-even conversions disagree.")

if observed_final_test_rows != 8654:
    failures.append(
        "Final-test protection count changed from the Cell 8 contract."
    )


# ------------------------------------------------------------
# 11) Save artifacts and hashes
# ------------------------------------------------------------
parameters.to_csv(
    CELL9_PARAMETERS_PATH,
    index=False,
)
scenarios.to_csv(
    CELL9_SCENARIOS_PATH,
    index=False,
)

artifact_hashes = {
    "input_cell8_assignments_sha256": actual_cell8_hash,
    "input_cell8_audit_sha256": sha256_file(CELL8_AUDIT_PATH),
    "cost_parameters_sha256": sha256_file(CELL9_PARAMETERS_PATH),
    "cost_scenarios_sha256": sha256_file(CELL9_SCENARIOS_PATH),
}

primary_row = scenarios.loc[
    scenarios["scenario"].eq(PRIMARY_ECONOMIC_GATE_SCENARIO)
].iloc[0]

cell9_audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": COST_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell8_policy_version": cell8_audit.get("policy_version"),
        "cell8_status": cell8_audit.get("status"),
        "cell8_decision_rows": expected_decision_rows,
        "cell8_final_test_rows": expected_final_test_rows,
        "cell8_assignments_sha256": actual_cell8_hash,
        "final_test_outcomes_inspected": False,
    },
    "contract_mechanics": {
        "symbol": SYMBOL,
        "currency": CURRENCY,
        "contract_multiplier_usd_per_point": (
            CONTRACT_MULTIPLIER_USD_PER_POINT
        ),
        "tick_size_points": TICK_SIZE_POINTS,
        "tick_value_usd": TICK_VALUE_USD,
        "status": "LOCKED",
    },
    "fee_snapshot": {
        "as_of": SOURCE_SNAPSHOT_DATE,
        "status": "PROVISIONAL",
        "account_assumption": (
            "IBKR non-member MES; <=1,000 monthly contracts; "
            "one contract per side"
        ),
        "ibkr_execution_fee_per_side_usd": (
            IBKR_EXECUTION_FEE_PER_SIDE_USD
        ),
        "cme_exchange_fee_per_side_usd": (
            CME_EXCHANGE_FEE_PER_SIDE_USD
        ),
        "regulatory_fee_per_side_usd": (
            REGULATORY_FEE_PER_SIDE_USD
        ),
        "clearing_fee_per_side_usd": CLEARING_FEE_PER_SIDE_USD,
        "tax_or_entity_adjustment_per_side_usd": (
            TAX_OR_ENTITY_ADJUSTMENT_PER_SIDE_USD
        ),
        "direct_fee_per_side_usd": DIRECT_FEE_PER_SIDE_USD,
        "direct_fee_round_trip_usd": DIRECT_FEE_ROUND_TRIP_USD,
        "historical_fee_vintage_handling": (
            "constant current snapshot for comparable research; "
            "historical fee reconstruction remains OPEN"
        ),
        "actual_statement_reconciliation": "OPEN",
    },
    "execution_cost_contract": {
        "order_style_reference": "marketable entry and exit",
        "quantity_contracts": 1,
        "spread_data_available": False,
        "spread_method": "scenario proxy; current OHLCV has no bid/ask",
        "slippage_method": "scenario proxy pending paper/live fills",
        "latency_method": "scenario proxy pending server telemetry",
        "market_impact_method": (
            "scenario proxy; not identified from 1-minute OHLCV"
        ),
        "primary_economic_gate_scenario": (
            PRIMARY_ECONOMIC_GATE_SCENARIO
        ),
        "primary_round_trip_cost_usd": float(
            primary_row["total_round_trip_usd"]
        ),
        "primary_break_even_ticks": float(
            primary_row["break_even_ticks"]
        ),
        "primary_break_even_index_points": float(
            primary_row["break_even_index_points"]
        ),
        "scenario_status": "PROVISIONAL",
    },
    "research_safety": {
        "economic_label_created": False,
        "future_return_created": False,
        "model_fitted": False,
        "final_test_outcomes_inspected": False,
        "cost_before_final_label_rule_satisfied": True,
    },
    "sources": {
        "cme_contract_specification": CME_CONTRACT_SOURCE,
        "cme_fee_schedule": CME_FEE_SOURCE,
        "ibkr_futures_commissions": IBKR_COMMISSION_SOURCE,
        "ibkr_cme_fee_recovery": IBKR_CME_FEE_SOURCE,
        "source_snapshot_date": SOURCE_SNAPSHOT_DATE,
    },
    "scenario_count": int(len(scenarios)),
    "scenarios": scenarios.to_dict(orient="records"),
    "artifacts": {
        "cost_parameters": str(CELL9_PARAMETERS_PATH),
        "cost_scenarios": str(CELL9_SCENARIOS_PATH),
    },
    "sha256": artifact_hashes,
    "open_items": [
        "Reconcile fees and tax with the user's actual IBKR entity/statement.",
        "Replace spread proxy when historical bid/ask data is available.",
        "Calibrate slippage, latency, and impact from paper/live fills.",
        "Revisit quantity scaling before trading more than one contract.",
    ],
    "failures": failures,
}

with open(CELL9_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        cell9_audit,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ------------------------------------------------------------
# 12) Final hard gate and compact output
# ------------------------------------------------------------
if failures:
    print("\nCELL 9 FAILURES")
    print("-" * 72)
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 9 RESEARCH COST MODEL: FAIL\n"
        f"{CELL9_AUDIT_PATH}"
    )

print("\n" + "=" * 72)
print("CELL 9 — RESEARCH COST MODEL CONTRACT")
print("=" * 72)

print("\n[1] UPSTREAM / TEST PROTECTION")
print("Cell 8 rows                  :", f"{len(assignments):,}")
print("Final-test rows protected    :", f"{observed_final_test_rows:,}")
print("Final-test outcomes inspected: False")
print("Cell 8 assignments SHA256    :", actual_cell8_hash)

print("\n[2] MES CONTRACT MECHANICS — LOCKED")
print("Multiplier                    : USD 5.00 / index point")
print("Tick size                     : 0.25 index points")
print("Tick value                    : USD 1.25 / contract")

print("\n[3] DIRECT FEE SNAPSHOT — PROVISIONAL")
print("IBKR execution / side         : USD 0.25")
print("CME exchange / side           : USD 0.35")
print("Regulatory / side             : USD 0.01")
print("Direct fee / side             :", f"USD {DIRECT_FEE_PER_SIDE_USD:.2f}")
print("Direct fee / round trip       :", f"USD {DIRECT_FEE_ROUND_TRIP_USD:.2f}")
print("Snapshot date                 :", SOURCE_SNAPSHOT_DATE)

print("\n[4] ONE-CONTRACT ROUND-TRIP SCENARIOS")
print(
    scenarios[
        [
            "scenario",
            "total_round_trip_usd",
            "break_even_ticks",
            "break_even_index_points",
            "primary_economic_gate",
        ]
    ].to_string(index=False)
)

print("\n[5] PRIMARY ECONOMIC GATE")
print("Scenario                      :", PRIMARY_ECONOMIC_GATE_SCENARIO)
print(
    "Round-trip cost               :",
    f"USD {float(primary_row['total_round_trip_usd']):.3f}",
)
print(
    "Break-even                    :",
    f"{float(primary_row['break_even_ticks']):.3f} ticks / "
    f"{float(primary_row['break_even_index_points']):.3f} points",
)

print("\n[6] SAVED ARTIFACTS")
print("Cost parameters :", CELL9_PARAMETERS_PATH)
print("Cost scenarios  :", CELL9_SCENARIOS_PATH)
print("Cell 9 audit    :", CELL9_AUDIT_PATH)
print("Scenario SHA256 :", artifact_hashes["cost_scenarios_sha256"])

print("\n" + "=" * 72)
print("CELL 9 RESEARCH COST MODEL: PASS")
print("=" * 72)

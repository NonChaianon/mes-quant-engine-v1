# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 13 — DEVELOPMENT-ONLY DEPENDENCE AUDIT & NAIVE BASELINES
# ============================================================
#
# PURPOSE
# -------
# Establish honest reference lines before any predictive model:
#
# - V1 action space is LONG / FLAT (SHORT remains diagnostic only).
# - A position is held for 60 minutes and positions do not overlap.
# - Every reported result is out-of-fold validation for 2022–2024.
# - Confidence intervals resample consecutive NYSE sessions, never rows.
# - Final Test stays sealed and is removed before aggregation.
#
# P&L uses the CURRENT_DEPLOYMENT_COUNTERFACTUAL cost view. It is not
# represented as historically realized P&L.
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1) Paths and locked evaluation policy
# ------------------------------------------------------------
PROJECT_DIR = Path("/content/drive/MyDrive/Quant_Lab")
CLEAN_DIR = PROJECT_DIR / "Data" / "MES_Clean_Pipeline_V1"

CELL8_AUDIT_PATH = CLEAN_DIR / "cell8_purged_split_audit.json"
CELL10_AUDIT_PATH = CLEAN_DIR / "cell10_economic_label_audit.json"
CELL11_SEMANTIC_SCENARIOS_PATH = (
    CLEAN_DIR / "cell11_cost_scenarios_semantic_v1.csv"
)
CELL11_AUDIT_PATH = CLEAN_DIR / "cell11_cost_temporality_audit.json"
CELL12_PATH_OUTCOMES_PATH = (
    CLEAN_DIR / "cell12_development_path_outcomes_v1.parquet"
)
CELL12_AUDIT_PATH = CLEAN_DIR / "cell12_path_outcomes_audit.json"

CELL13_EVENTS_PATH = (
    CLEAN_DIR / "cell13_development_oof_baseline_events_v1.parquet"
)
CELL13_DEPENDENCE_PATH = (
    CLEAN_DIR / "cell13_dependence_ess_audit_v1.csv"
)
CELL13_METRICS_PATH = (
    CLEAN_DIR / "cell13_naive_baseline_metrics_v1.csv"
)
CELL13_BOOTSTRAP_PATH = (
    CLEAN_DIR / "cell13_block_bootstrap_ci_v1.csv"
)
CELL13_AUDIT_PATH = CLEAN_DIR / "cell13_development_baseline_audit.json"

BASELINE_POLICY_VERSION = "MES_V1_DEPENDENCE_BASELINES_1.0"
EXPECTED_CELL8_POLICY = "MES_V1_PURGED_SPLIT_1.0"
EXPECTED_CELL10_POLICY = "MES_V1_ECONOMIC_LABELS_1.0"
EXPECTED_CELL11_POLICY = "MES_V1_COST_TEMPORALITY_1.0"
EXPECTED_CELL12_POLICY = "MES_V1_DEVELOPMENT_PATH_OUTCOMES_1.0"

ACTION_SPACE = "LONG_FLAT"
POSITION_POLICY = "NON_OVERLAPPING_60M"
HOLD_MINUTES = 60
EXIT_THEN_ENTRY_AT_SAME_TIMESTAMP = True
MASTER_SEED = 20260809
RANDOM_SENSITIVITY_SEEDS = 1000
BOOTSTRAP_REPETITIONS = 2000
BOOTSTRAP_BLOCK_LENGTHS = [1, 5, 20]
PRIMARY_BOOTSTRAP_BLOCK_SESSIONS = 5

FOLD_SPECS = [
    ("WF_2022", "role_wf_2022", 2022),
    ("WF_2023", "role_wf_2023", 2023),
    ("WF_2024", "role_wf_2024", 2024),
]


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


def safe_divide(numerator, denominator):
    return float(numerator / denominator) if denominator else np.nan


def strict_boolean(series, column_name):
    """Parse booleans without treating the string 'False' as truthy."""
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.astype(bool)

    tokens = series.astype("string").str.strip().str.lower()
    parsed = tokens.map({"true": True, "false": False})
    if parsed.isna().any():
        bad = sorted(tokens.loc[parsed.isna()].dropna().unique().tolist())
        raise RuntimeError(
            f"CELL 13 STOPPED — invalid boolean token in {column_name}: {bad}"
        )
    return parsed.astype(bool)


def finite_distribution_summary(values):
    """Summarize only finite replications; never warn on all-NaN Sharpe."""
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {
            "mean": np.nan,
            "p025": np.nan,
            "p975": np.nan,
            "valid_repetitions": 0,
            "status": "UNDEFINED_ZERO_VARIANCE",
        }
    return {
        "mean": float(finite.mean()),
        "p025": float(np.quantile(finite, 0.025)),
        "p975": float(np.quantile(finite, 0.975)),
        "valid_repetitions": int(finite.size),
        "status": "DEFINED",
    }


def classification_metrics(y_true, y_pred, prob_long):
    y_true = np.asarray(y_true, dtype=np.int8)
    y_pred = np.asarray(y_pred, dtype=np.int8)
    prob_long = np.asarray(prob_long, dtype=float)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    # Explicit zero_division=0 policy: an unpredicted class contributes
    # F1=0 to macro-F1; it is never silently dropped by nanmean.
    recall_long = tp / (tp + fn) if (tp + fn) else 0.0
    recall_flat = tn / (tn + fp) if (tn + fp) else 0.0
    precision_long = tp / (tp + fp) if (tp + fp) else 0.0
    precision_flat = tn / (tn + fn) if (tn + fn) else 0.0

    f1_long = (
        2.0 * precision_long * recall_long / (precision_long + recall_long)
        if (precision_long + recall_long)
        else 0.0
    )
    f1_flat = (
        2.0 * precision_flat * recall_flat / (precision_flat + recall_flat)
        if (precision_flat + recall_flat)
        else 0.0
    )

    clipped = np.clip(prob_long, 1e-12, 1.0 - 1e-12)
    log_loss = -np.mean(
        y_true * np.log(clipped) + (1 - y_true) * np.log(1 - clipped)
    )

    return {
        "rows": int(len(y_true)),
        "accuracy": float(np.mean(y_true == y_pred)),
        "balanced_accuracy": float((recall_long + recall_flat) / 2.0),
        "macro_f1": float((f1_long + f1_flat) / 2.0),
        "recall_enter_long": recall_long,
        "recall_flat": recall_flat,
        "predicted_long_coverage": float(np.mean(y_pred == 1)),
        "brier_score": float(np.mean((prob_long - y_true) ** 2)),
        "log_loss": float(log_loss),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def simulate_non_overlapping_long(valid_rows, predicted_long, cost_usd):
    rows = valid_rows.reset_index(drop=True).copy()
    predicted_long = np.asarray(predicted_long, dtype=bool)
    if len(predicted_long) != len(rows):
        raise RuntimeError("CELL 13 STOPPED — prediction length mismatch.")
    canonical_order = rows.sort_values(
        ["decision_time", "decision_id"], kind="stable"
    ).index.to_numpy()
    if not np.array_equal(canonical_order, np.arange(len(rows))):
        raise RuntimeError(
            "CELL 13 STOPPED — simulator input is not in canonical time/ID order."
        )

    executed = np.zeros(len(rows), dtype=bool)
    ignored = np.zeros(len(rows), dtype=bool)
    gross_pnl = np.zeros(len(rows), dtype=float)
    charged_cost = np.zeros(len(rows), dtype=float)
    net_pnl = np.zeros(len(rows), dtype=float)
    exit_times = pd.Series(pd.NaT, index=rows.index, dtype="datetime64[ns, UTC]")

    next_available = None
    for i, row in rows.iterrows():
        decision_time = row["decision_time"]
        if not predicted_long[i]:
            continue
        if next_available is not None and decision_time < next_available:
            ignored[i] = True
            continue

        exit_time = decision_time + pd.Timedelta(minutes=HOLD_MINUTES)
        executed[i] = True
        exit_times.iloc[i] = exit_time
        gross_pnl[i] = float(row["gross_move_usd_60m"])
        charged_cost[i] = float(cost_usd)
        net_pnl[i] = gross_pnl[i] - charged_cost[i]
        next_available = exit_time

    return {
        "rows": rows,
        "executed": executed,
        "ignored": ignored,
        "gross_pnl_usd": gross_pnl,
        "charged_cost_usd": charged_cost,
        "net_pnl_usd": net_pnl,
        "exit_time": exit_times,
    }


def economic_metrics(event_rows):
    sessions = (
        event_rows.groupby("nyse_session_date", sort=True)["net_pnl_usd"]
        .sum()
        .astype(float)
    )
    executed = event_rows["executed"].astype(bool)
    trade_net = event_rows.loc[executed, "net_pnl_usd"].astype(float)

    session_std = float(sessions.std(ddof=1)) if len(sessions) > 1 else np.nan
    annualized_sharpe = (
        float(np.sqrt(252.0) * sessions.mean() / session_std)
        if np.isfinite(session_std) and session_std > 0
        else np.nan
    )

    equity_values = sessions.cumsum().to_numpy(dtype=float)
    equity_with_origin = np.concatenate(([0.0], equity_values))
    running_peak = np.maximum.accumulate(equity_with_origin)
    drawdown = equity_with_origin - running_peak
    maximum_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    if len(sessions):
        tail_count = max(1, int(math.ceil(0.05 * len(sessions))))
        expected_shortfall_95 = float(np.sort(sessions.to_numpy())[:tail_count].mean())
    else:
        expected_shortfall_95 = np.nan

    wins = trade_net[trade_net > 0]
    losses = trade_net[trade_net < 0]
    profit_factor = (
        float(wins.sum() / abs(losses.sum()))
        if len(losses) and abs(losses.sum()) > 0
        else np.nan
    )

    return {
        "executed_trades": int(executed.sum()),
        "ignored_long_signals": int(event_rows["ignored_signal"].sum()),
        "gross_pnl_usd": float(event_rows["gross_pnl_usd"].sum()),
        "total_cost_usd": float(event_rows["charged_cost_usd"].sum()),
        "net_pnl_usd": float(event_rows["net_pnl_usd"].sum()),
        "mean_net_usd_per_trade": float(trade_net.mean()) if len(trade_net) else np.nan,
        "median_net_usd_per_trade": float(trade_net.median()) if len(trade_net) else np.nan,
        "trade_hit_rate": float((trade_net > 0).mean()) if len(trade_net) else np.nan,
        "profit_factor": profit_factor,
        "trades_per_session": safe_divide(int(executed.sum()), len(sessions)),
        "mean_session_net_usd": float(sessions.mean()) if len(sessions) else np.nan,
        "annualized_session_sharpe": annualized_sharpe,
        "maximum_drawdown_usd": maximum_drawdown,
        # This is signed lower-tail P&L (normally negative), not a positive loss.
        "session_lower_tail_mean_pnl_5pct_usd": expected_shortfall_95,
        "maximum_concurrent_positions": 1 if executed.any() else 0,
    }


def random_economic_sensitivity(valid_rows, random_draws, cost_usd):
    rows = valid_rows.sort_values("decision_time").reset_index(drop=True)
    times_ns = rows["decision_time"].astype("int64").to_numpy()
    gross = rows["gross_move_usd_60m"].to_numpy(dtype=float)
    session_codes, session_values = pd.factorize(
        rows["nyse_session_date"].astype(str), sort=True
    )
    hold_ns = int(pd.Timedelta(minutes=HOLD_MINUTES).value)

    total_net = np.zeros(len(random_draws), dtype=float)
    sharpe = np.full(len(random_draws), np.nan, dtype=float)
    max_drawdown = np.zeros(len(random_draws), dtype=float)

    for rep, prediction in enumerate(random_draws):
        session_net = np.zeros(len(session_values), dtype=float)
        next_available_ns = np.iinfo(np.int64).min
        for i in range(len(rows)):
            if prediction[i] and times_ns[i] >= next_available_ns:
                session_net[session_codes[i]] += gross[i] - cost_usd
                next_available_ns = times_ns[i] + hold_ns

        total_net[rep] = session_net.sum()
        session_std = session_net.std(ddof=1) if len(session_net) > 1 else np.nan
        if np.isfinite(session_std) and session_std > 0:
            sharpe[rep] = np.sqrt(252.0) * session_net.mean() / session_std

        equity = np.concatenate(([0.0], np.cumsum(session_net)))
        max_drawdown[rep] = np.min(equity - np.maximum.accumulate(equity))

    return {
        "net_pnl_usd": total_net,
        "annualized_session_sharpe": sharpe,
        "maximum_drawdown_usd": max_drawdown,
    }


def empirical_overlap_diagnostics(frame, fold_id):
    ordered = frame.sort_values(["nyse_session_date", "decision_time"]).copy()
    rows = []
    positive_rhos = []

    for lag in [1, 2, 3]:
        grouped = ordered.groupby("nyse_session_date", sort=False)
        prior_return = grouped["gross_move_points_60m"].shift(lag)
        prior_time = grouped["decision_time"].shift(lag)
        exact_pair = (
            ordered["decision_time"] - prior_time
        ).eq(pd.Timedelta(minutes=15 * lag))
        valid = exact_pair & prior_return.notna()

        if int(valid.sum()) >= 2:
            rho = float(
                np.corrcoef(
                    ordered.loc[valid, "gross_move_points_60m"].astype(float),
                    prior_return.loc[valid].astype(float),
                )[0, 1]
            )
        else:
            rho = np.nan
        if np.isfinite(rho):
            positive_rhos.append(max(rho, 0.0))
        rows.append(
            {
                "fold_id": fold_id,
                "diagnostic": f"return_autocorrelation_lag_{lag}",
                "value": rho,
                "pairs": int(valid.sum()),
                "status": "DESCRIPTIVE",
            }
        )

    n = int(len(ordered))
    design_effect = max(1.0, 1.0 + 2.0 * sum(positive_rhos))
    empirical_ess = n / design_effect

    concurrency_values = []
    for _, session in ordered.groupby("nyse_session_date", sort=False):
        times = session["decision_time"].sort_values().tolist()
        active_exits = []
        for timestamp in times:
            active_exits = [exit_time for exit_time in active_exits if exit_time > timestamp]
            active_exits.append(timestamp + pd.Timedelta(minutes=HOLD_MINUTES))
            concurrency_values.append(len(active_exits))

    rows.extend(
        [
            {
                "fold_id": fold_id,
                "diagnostic": "observed_design_effect_positive_rho_lags_1_3",
                "value": float(design_effect),
                "pairs": n,
                "status": "DESCRIPTIVE_NOT_FOR_CI",
            },
            {
                "fold_id": fold_id,
                "diagnostic": "observed_effective_sample_size",
                "value": float(empirical_ess),
                "pairs": n,
                "status": "DESCRIPTIVE_NOT_FOR_CI",
            },
            {
                "fold_id": fold_id,
                "diagnostic": "theoretical_n_div_4_reference",
                "value": float(n / 4.0),
                "pairs": n,
                "status": "REFERENCE_NOT_OBSERVED_FACT",
            },
            {
                "fold_id": fold_id,
                "diagnostic": "average_available_label_concurrency",
                "value": float(np.mean(concurrency_values)),
                "pairs": n,
                "status": "DESCRIPTIVE",
            },
            {
                "fold_id": fold_id,
                "diagnostic": "maximum_available_label_concurrency",
                "value": float(np.max(concurrency_values)),
                "pairs": n,
                "status": "DESCRIPTIVE",
            },
        ]
    )
    return rows


def moving_block_indices(n_sessions, block_length, repetitions, rng):
    if n_sessions <= 0:
        raise ValueError("No sessions for bootstrap.")
    effective_block = min(block_length, n_sessions)
    max_start = n_sessions - effective_block
    blocks_needed = int(math.ceil(n_sessions / effective_block))
    draws = np.empty((repetitions, n_sessions), dtype=np.int32)

    for rep in range(repetitions):
        starts = rng.integers(0, max_start + 1, size=blocks_needed)
        indices = np.concatenate(
            [
                np.arange(start, start + effective_block, dtype=np.int32)
                for start in starts
            ]
        )[:n_sessions]
        draws[rep] = indices
    return draws


# ------------------------------------------------------------
# 3) Upstream artifact and hash gates
# ------------------------------------------------------------
required_paths = [
    CELL8_AUDIT_PATH,
    CELL10_AUDIT_PATH,
    CELL11_SEMANTIC_SCENARIOS_PATH,
    CELL11_AUDIT_PATH,
    CELL12_PATH_OUTCOMES_PATH,
    CELL12_AUDIT_PATH,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
if missing_paths:
    raise RuntimeError(
        "CELL 13 STOPPED — missing upstream artifacts:\n"
        + "\n".join(missing_paths)
        + "\n\nRun Cell 0 → Cell 12 first."
    )

cell8_audit = load_json(CELL8_AUDIT_PATH)
cell10_audit = load_json(CELL10_AUDIT_PATH)
cell11_audit = load_json(CELL11_AUDIT_PATH)
cell12_audit = load_json(CELL12_AUDIT_PATH)

expected_versions = [
    (cell8_audit, EXPECTED_CELL8_POLICY, "Cell 8"),
    (cell10_audit, EXPECTED_CELL10_POLICY, "Cell 10"),
    (cell11_audit, EXPECTED_CELL11_POLICY, "Cell 11"),
    (cell12_audit, EXPECTED_CELL12_POLICY, "Cell 12"),
]
for audit, expected_version, name in expected_versions:
    if audit.get("status") != "PASS" or audit.get("failures", []):
        raise RuntimeError(f"CELL 13 STOPPED — {name} audit is not clean PASS.")
    if audit.get("policy_version") != expected_version:
        raise RuntimeError(
            f"CELL 13 STOPPED — unexpected {name} policy version: "
            f"{audit.get('policy_version')}"
        )

expected_path_hash = (
    cell12_audit.get("sha256", {}).get("path_outcomes_sha256")
)
actual_path_hash = sha256_file(CELL12_PATH_OUTCOMES_PATH)
if not expected_path_hash or expected_path_hash != actual_path_hash:
    raise RuntimeError("CELL 13 STOPPED — Cell 12 path hash mismatch.")

expected_semantic_hash = (
    cell11_audit.get("sha256", {}).get("semantic_scenarios_sha256")
)
actual_semantic_hash = sha256_file(CELL11_SEMANTIC_SCENARIOS_PATH)
if not expected_semantic_hash or expected_semantic_hash != actual_semantic_hash:
    raise RuntimeError("CELL 13 STOPPED — Cell 11 cost hash mismatch.")

cell10_labels_hash = (
    cell10_audit.get("sha256", {}).get("economic_labels_sha256")
)
cell12_cell10_labels_hash = (
    cell12_audit.get("upstream_binding", {}).get("cell10_labels_sha256")
)
if not cell10_labels_hash or cell12_cell10_labels_hash != cell10_labels_hash:
    raise RuntimeError(
        "CELL 13 STOPPED — Cell 12 path outcomes do not descend from the "
        "current Cell 10 labels."
    )

actual_cell10_audit_hash = sha256_file(CELL10_AUDIT_PATH)
cell12_cell10_audit_hash = (
    cell12_audit.get("sha256", {}).get("input_cell10_audit_sha256")
)
if cell12_cell10_audit_hash != actual_cell10_audit_hash:
    raise RuntimeError(
        "CELL 13 STOPPED — Cell 12 was not built from the current Cell 10 audit."
    )

cell10_cell9_hash = (
    cell10_audit.get("upstream_binding", {}).get(
        "cell9_cost_scenarios_sha256"
    )
)
cell11_cell9_hash = (
    cell11_audit.get("upstream_binding", {}).get("cell9_scenarios_sha256")
)
if not cell10_cell9_hash or cell10_cell9_hash != cell11_cell9_hash:
    raise RuntimeError(
        "CELL 13 STOPPED — Cell 10 labels and Cell 11 costs descend from "
        "different Cell 9 scenarios."
    )

cell10_cell8_hash = (
    cell10_audit.get("upstream_binding", {}).get(
        "cell8_assignments_sha256"
    )
)
cell8_assignment_hash = (
    cell8_audit.get("sha256", {}).get("split_assignments_sha256")
)
if not cell10_cell8_hash or cell10_cell8_hash != cell8_assignment_hash:
    raise RuntimeError(
        "CELL 13 STOPPED — Cell 10 fold assignments do not match Cell 8."
    )


# ------------------------------------------------------------
# 4) Select the explicitly counterfactual primary cost
# ------------------------------------------------------------
semantic_costs = pd.read_csv(CELL11_SEMANTIC_SCENARIOS_PATH)
required_cost_columns = {
    "scenario",
    "primary_economic_gate",
    "cost_view",
    "historical_actual_claim",
    "total_round_trip_usd",
    "break_even_index_points",
}
missing_cost_columns = required_cost_columns - set(semantic_costs.columns)
if missing_cost_columns:
    raise RuntimeError(
        "CELL 13 STOPPED — semantic cost schema is incomplete: "
        + ", ".join(sorted(missing_cost_columns))
    )
primary_gate_mask = strict_boolean(
    semantic_costs["primary_economic_gate"], "primary_economic_gate"
)
historical_claim_mask = strict_boolean(
    semantic_costs["historical_actual_claim"], "historical_actual_claim"
)
primary_cost = semantic_costs.loc[primary_gate_mask]
if len(primary_cost) != 1:
    raise RuntimeError("CELL 13 STOPPED — expected one primary cost row.")
primary_cost = primary_cost.iloc[0]

if primary_cost["cost_view"] != "CURRENT_DEPLOYMENT":
    raise RuntimeError("CELL 13 STOPPED — primary cost is not CURRENT_DEPLOYMENT.")
if bool(historical_claim_mask.loc[primary_cost.name]):
    raise RuntimeError("CELL 13 STOPPED — primary cost claims historical actuality.")

round_trip_cost_usd = float(primary_cost["total_round_trip_usd"])
primary_cost_scenario = str(primary_cost["scenario"])
primary_break_even_points = float(primary_cost["break_even_index_points"])
if not np.isfinite(round_trip_cost_usd) or round_trip_cost_usd < 0:
    raise RuntimeError("CELL 13 STOPPED — invalid primary round-trip cost.")
if not np.isfinite(primary_break_even_points) or primary_break_even_points < 0:
    raise RuntimeError("CELL 13 STOPPED — invalid primary break-even points.")

cell10_contract = cell10_audit.get("label_contract", {})
if str(cell10_contract.get("primary_cost_scenario")) != primary_cost_scenario:
    raise RuntimeError("CELL 13 STOPPED — Cell 10 primary scenario mismatch.")
if not np.isclose(
    float(cell10_contract.get("primary_round_trip_cost_usd", np.nan)),
    round_trip_cost_usd,
    atol=1e-12,
):
    raise RuntimeError("CELL 13 STOPPED — Cell 10 round-trip cost mismatch.")
if not np.isclose(
    float(cell10_contract.get("primary_break_even_index_points", np.nan)),
    primary_break_even_points,
    atol=1e-12,
):
    raise RuntimeError("CELL 13 STOPPED — Cell 10 break-even mismatch.")


# ------------------------------------------------------------
# 5) Load path outcomes; prove seal before dropping Final Test
# ------------------------------------------------------------
data = pd.read_parquet(CELL12_PATH_OUTCOMES_PATH)
required_columns = {
    "decision_id",
    "decision_time",
    "label_end_time",
    "nyse_session_date",
    "outer_partition",
    "label_status",
    "label_usable",
    "path_status",
    "path_usable",
    "long_mfe_points_60m",
    "long_mae_points_60m",
    "gross_move_points_60m",
    "gross_move_usd_60m",
    "economic_label_primary",
    *[role_column for _, role_column, _ in FOLD_SPECS],
}
missing_columns = required_columns - set(data.columns)
if missing_columns:
    raise RuntimeError(
        "CELL 13 STOPPED — missing required columns:\n"
        + ", ".join(sorted(missing_columns))
    )

data = data.copy()
data["decision_time"] = pd.to_datetime(data["decision_time"], utc=True)
data["label_end_time"] = pd.to_datetime(data["label_end_time"], utc=True)
data["label_usable"] = strict_boolean(data["label_usable"], "label_usable")
data["path_usable"] = strict_boolean(data["path_usable"], "path_usable")

decision_ids = data["decision_id"].astype("string").str.strip()
invalid_id_tokens = {"", "nan", "none", "null", "<na>"}
if decision_ids.isna().any() or decision_ids.str.lower().isin(invalid_id_tokens).any():
    raise RuntimeError("CELL 13 STOPPED — missing/blank validation decision ID.")
if decision_ids.duplicated().any():
    raise RuntimeError("CELL 13 STOPPED — decision IDs are not globally unique.")
data["decision_id"] = decision_ids
if data["decision_time"].isna().any() or data["decision_time"].duplicated().any():
    raise RuntimeError("CELL 13 STOPPED — decision timestamps are missing/duplicated.")

final_mask = data["outer_partition"].eq("FINAL_TEST")
expected_final_rows = int(
    cell12_audit.get("counts", {}).get("final_test_rows_sealed", -1)
)
if expected_final_rows != 8654 or int(final_mask.sum()) != expected_final_rows:
    raise RuntimeError("CELL 13 STOPPED — final-test row count changed.")
if not data.loc[final_mask, "label_status"].eq("SEALED_FINAL_TEST").all():
    raise RuntimeError("CELL 13 STOPPED — final-test label status is not SEALED.")
if not data.loc[final_mask, "path_status"].eq("SEALED_FINAL_TEST").all():
    raise RuntimeError("CELL 13 STOPPED — final-test path status is not SEALED.")
if not data.loc[final_mask, "economic_label_primary"].eq("SEALED").all():
    raise RuntimeError("CELL 13 STOPPED — final-test economic label is not SEALED.")

sealed_numeric = [
    "gross_move_points_60m",
    "gross_move_usd_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
]
if data.loc[final_mask, sealed_numeric].notna().any().any():
    raise RuntimeError("CELL 13 STOPPED — Final Test contains outcome numerics.")

# Final Test is discarded before any class count, prior, metric, or P&L.
development = data.loc[~final_mask].copy()
del data

usable_development_labels = set(
    development.loc[
        development["label_usable"], "economic_label_primary"
    ].dropna().astype(str)
)
allowed_development_labels = {"LONG", "SHORT", "NO_TRADE"}
if not usable_development_labels.issubset(allowed_development_labels):
    raise RuntimeError(
        "CELL 13 STOPPED — unexpected usable economic label: "
        + ", ".join(sorted(usable_development_labels - allowed_development_labels))
    )

development_session_year = pd.to_datetime(
    development["nyse_session_date"], errors="raise"
).dt.year
if development_session_year.ge(2025).any():
    raise RuntimeError("CELL 13 STOPPED — a 2025+ timestamp entered Development.")


# ------------------------------------------------------------
# 6) OOF baselines fold by fold
# ------------------------------------------------------------
event_frames = []
metric_rows = []
dependence_rows = []
validation_ids = []
boundary_failures = []
canonical_validation_sessions = {}

for fold_index, (fold_id, role_column, validation_year) in enumerate(FOLD_SPECS):
    canonical_validation_rows = development.loc[
        development[role_column].eq("VALIDATION")
    ].copy()
    if canonical_validation_rows.empty:
        raise RuntimeError(
            f"CELL 13 STOPPED — no canonical validation rows in {fold_id}."
        )
    canonical_year = pd.to_datetime(
        canonical_validation_rows["nyse_session_date"], errors="raise"
    ).dt.year
    if not canonical_year.eq(validation_year).all():
        raise RuntimeError(
            f"CELL 13 STOPPED — canonical validation year mismatch in {fold_id}."
        )
    canonical_sessions = sorted(
        canonical_validation_rows["nyse_session_date"].astype(str).unique().tolist()
    )
    canonical_validation_sessions[fold_id] = canonical_sessions

    train_mask = development[role_column].eq("TRAIN") & development["label_usable"]
    validation_mask = (
        development[role_column].eq("VALIDATION")
        & development["label_usable"]
        & development["path_usable"]
    )

    train = development.loc[train_mask].sort_values(
        ["decision_time", "decision_id"], kind="stable"
    ).copy()
    valid = development.loc[validation_mask].sort_values(
        ["decision_time", "decision_id"], kind="stable"
    ).copy()

    if train.empty or valid.empty:
        raise RuntimeError(f"CELL 13 STOPPED — empty train/validation in {fold_id}.")
    valid_session_year = pd.to_datetime(
        valid["nyse_session_date"], errors="raise"
    ).dt.year
    if not valid_session_year.eq(validation_year).all():
        raise RuntimeError(f"CELL 13 STOPPED — wrong validation year in {fold_id}.")
    observed_sessions = sorted(
        valid["nyse_session_date"].astype(str).unique().tolist()
    )
    if observed_sessions != canonical_sessions:
        missing_sessions = sorted(set(canonical_sessions) - set(observed_sessions))
        raise RuntimeError(
            f"CELL 13 STOPPED — usable outcomes do not cover every canonical "
            f"validation session in {fold_id}: {missing_sessions[:10]}"
        )
    if train["label_end_time"].max() >= valid["decision_time"].min():
        boundary_failures.append(f"{fold_id}: train label overlaps validation.")

    validation_ids.extend(valid["decision_id"].tolist())

    y_train = train["economic_label_primary"].eq("LONG").to_numpy(dtype=np.int8)
    y_valid = valid["economic_label_primary"].eq("LONG").to_numpy(dtype=np.int8)
    train_prior_long = float(y_train.mean())

    fold_rng = np.random.default_rng(MASTER_SEED + fold_index)
    random_prediction = fold_rng.random(len(valid)) < train_prior_long

    baseline_specs = [
        ("ALWAYS_FLAT", np.zeros(len(valid), dtype=np.int8), np.zeros(len(valid))),
        ("ALWAYS_LONG", np.ones(len(valid), dtype=np.int8), np.ones(len(valid))),
        (
            "TRAIN_PRIOR_PROBABILITY",
            np.full(len(valid), int(train_prior_long >= 0.5), dtype=np.int8),
            np.full(len(valid), train_prior_long, dtype=float),
        ),
        (
            "STRATIFIED_RANDOM_ACTION",
            random_prediction.astype(np.int8),
            np.full(len(valid), train_prior_long, dtype=float),
        ),
    ]

    random_sensitivity_rng = np.random.default_rng(
        MASTER_SEED + 100 + fold_index
    )
    random_draws = (
        random_sensitivity_rng.random(
            (RANDOM_SENSITIVITY_SEEDS, len(valid))
        )
        < train_prior_long
    )
    random_accuracy_distribution = np.mean(
        random_draws == y_valid[np.newaxis, :], axis=1
    )
    random_economic_distribution = random_economic_sensitivity(
        valid, random_draws, round_trip_cost_usd
    )
    random_accuracy_summary = finite_distribution_summary(
        random_accuracy_distribution
    )
    random_net_summary = finite_distribution_summary(
        random_economic_distribution["net_pnl_usd"]
    )
    random_sharpe_summary = finite_distribution_summary(
        random_economic_distribution["annualized_session_sharpe"]
    )
    random_drawdown_summary = finite_distribution_summary(
        random_economic_distribution["maximum_drawdown_usd"]
    )

    for strategy, prediction, probability in baseline_specs:
        class_result = classification_metrics(y_valid, prediction, probability)
        simulation = simulate_non_overlapping_long(
            valid, prediction == 1, round_trip_cost_usd
        )
        rows = simulation["rows"]

        event = pd.DataFrame(
            {
                "fold_id": fold_id,
                "validation_year": validation_year,
                "strategy": strategy,
                "decision_id": rows["decision_id"].astype(str).to_numpy(),
                "decision_time": rows["decision_time"].to_numpy(),
                "nyse_session_date": rows["nyse_session_date"].astype(str).to_numpy(),
                "target_action": np.where(y_valid == 1, "ENTER_LONG", "FLAT"),
                "predicted_action": np.where(prediction == 1, "ENTER_LONG", "FLAT"),
                "probability_enter_long": probability,
                "correct": (prediction == y_valid),
                "executed": simulation["executed"],
                "ignored_signal": simulation["ignored"],
                "exit_time": simulation["exit_time"].to_numpy(),
                "gross_pnl_usd": simulation["gross_pnl_usd"],
                "charged_cost_usd": simulation["charged_cost_usd"],
                "net_pnl_usd": simulation["net_pnl_usd"],
                "cost_semantics": "CURRENT_DEPLOYMENT_COUNTERFACTUAL",
            }
        )
        event_frames.append(event)

        economics = economic_metrics(event)
        metrics = {
            "fold_id": fold_id,
            "validation_year": validation_year,
            "strategy": strategy,
            "action_space": ACTION_SPACE,
            "position_policy": POSITION_POLICY,
            "train_prior_enter_long": train_prior_long,
            "round_trip_cost_usd": round_trip_cost_usd,
            "cost_semantics": "CURRENT_DEPLOYMENT_COUNTERFACTUAL",
            "classification_scope": "OPPORTUNITY_ROWS_BEFORE_POSITION_FILTER",
            **class_result,
            **economics,
        }
        if strategy == "STRATIFIED_RANDOM_ACTION":
            metrics.update(
                {
                    "random_1000_seed_accuracy_mean": random_accuracy_summary["mean"],
                    "random_1000_seed_accuracy_p025": random_accuracy_summary["p025"],
                    "random_1000_seed_accuracy_p975": random_accuracy_summary["p975"],
                    "random_1000_seed_net_pnl_mean": random_net_summary["mean"],
                    "random_1000_seed_net_pnl_p025": random_net_summary["p025"],
                    "random_1000_seed_net_pnl_p975": random_net_summary["p975"],
                    "random_1000_seed_sharpe_mean": random_sharpe_summary["mean"],
                    "random_1000_seed_sharpe_p025": random_sharpe_summary["p025"],
                    "random_1000_seed_sharpe_p975": random_sharpe_summary["p975"],
                    "random_1000_seed_sharpe_valid_repetitions": (
                        random_sharpe_summary["valid_repetitions"]
                    ),
                    "random_1000_seed_sharpe_status": random_sharpe_summary["status"],
                    "random_1000_seed_max_drawdown_mean": random_drawdown_summary["mean"],
                    "random_1000_seed_max_drawdown_p025": random_drawdown_summary["p025"],
                    "random_1000_seed_max_drawdown_p975": random_drawdown_summary["p975"],
                }
            )
        metric_rows.append(metrics)

    dependence_rows.extend(empirical_overlap_diagnostics(valid, fold_id))

if boundary_failures:
    raise RuntimeError("CELL 13 STOPPED — " + " | ".join(boundary_failures))
if len(validation_ids) != len(set(validation_ids)):
    raise RuntimeError("CELL 13 STOPPED — validation decision IDs repeat across folds.")

events = pd.concat(event_frames, ignore_index=True)
metrics = pd.DataFrame(metric_rows)
dependence = pd.DataFrame(dependence_rows)

# Pooled chronological OOF metrics are recomputed from concatenated
# validation events; fold Sharpe values are never averaged.
pooled_metric_rows = []
for strategy, pooled_events in events.groupby("strategy", sort=True):
    pooled_events = pooled_events.sort_values("decision_time").copy()
    pooled_y = pooled_events["target_action"].eq("ENTER_LONG").to_numpy(dtype=np.int8)
    pooled_prediction = pooled_events["predicted_action"].eq(
        "ENTER_LONG"
    ).to_numpy(dtype=np.int8)
    pooled_probability = pooled_events["probability_enter_long"].to_numpy(dtype=float)
    pooled_metric_rows.append(
        {
            "fold_id": "OOF_POOLED",
            "validation_year": "2022-2024",
            "strategy": strategy,
            "action_space": ACTION_SPACE,
            "position_policy": POSITION_POLICY,
            "train_prior_enter_long": np.nan,
            "round_trip_cost_usd": round_trip_cost_usd,
            "cost_semantics": "CURRENT_DEPLOYMENT_COUNTERFACTUAL",
            "classification_scope": "OPPORTUNITY_ROWS_BEFORE_POSITION_FILTER",
            **classification_metrics(
                pooled_y, pooled_prediction, pooled_probability
            ),
            **economic_metrics(pooled_events),
        }
    )
metrics = pd.concat(
    [metrics, pd.DataFrame(pooled_metric_rows)], ignore_index=True
)


# ------------------------------------------------------------
# 7) Session moving-block bootstrap
# ------------------------------------------------------------
bootstrap_rows = []


def append_bootstrap_summary(
    fold_id,
    validation_year,
    strategy,
    metric_name,
    block_length,
    seed,
    values,
):
    summary = finite_distribution_summary(values)
    bootstrap_rows.append(
        {
            "fold_id": fold_id,
            "validation_year": validation_year,
            "strategy": strategy,
            "metric": metric_name,
            "block_length_sessions": block_length,
            "repetitions": BOOTSTRAP_REPETITIONS,
            "valid_repetitions": summary["valid_repetitions"],
            "interval_status": summary["status"],
            "seed": seed,
            "estimate_bootstrap_mean": summary["mean"],
            "ci_95_lower": summary["p025"],
            "ci_95_upper": summary["p975"],
            "primary_ci": block_length == PRIMARY_BOOTSTRAP_BLOCK_SESSIONS,
        }
    )


strategy_names = sorted(events["strategy"].unique().tolist())
for fold_index, (fold_id, _, validation_year) in enumerate(FOLD_SPECS):
    fold_events = events.loc[events["fold_id"].eq(fold_id)].copy()
    sessions = canonical_validation_sessions[fold_id]

    session_metrics = (
        fold_events.groupby(["strategy", "nyse_session_date"], sort=True)
        .agg(
            correct_count=("correct", "sum"),
            row_count=("correct", "size"),
            net_pnl_usd=("net_pnl_usd", "sum"),
        )
        .reset_index()
    )

    for strategy in strategy_names:
        observed_strategy_sessions = sorted(
            session_metrics.loc[
                session_metrics["strategy"].eq(strategy), "nyse_session_date"
            ].astype(str).tolist()
        )
        if observed_strategy_sessions != sessions:
            raise RuntimeError(
                f"CELL 13 STOPPED — incomplete session table for "
                f"{fold_id}/{strategy}."
            )

    for block_length in BOOTSTRAP_BLOCK_LENGTHS:
        bootstrap_seed = MASTER_SEED + 1000 * (fold_index + 1) + block_length
        bootstrap_rng = np.random.default_rng(bootstrap_seed)
        draws = moving_block_indices(
            len(sessions),
            block_length,
            BOOTSTRAP_REPETITIONS,
            bootstrap_rng,
        )

        for strategy in strategy_names:
            table = (
                session_metrics.loc[session_metrics["strategy"].eq(strategy)]
                .set_index("nyse_session_date")
                .loc[sessions]
            )
            correct = table["correct_count"].to_numpy(dtype=float)
            row_count = table["row_count"].to_numpy(dtype=float)
            session_net = table["net_pnl_usd"].to_numpy(dtype=float)

            sampled_correct = correct[draws].sum(axis=1)
            sampled_rows = row_count[draws].sum(axis=1)
            sampled_accuracy = sampled_correct / sampled_rows
            sampled_session_net = session_net[draws]
            sampled_mean_session_net = sampled_session_net.mean(axis=1)
            sampled_std_session_net = sampled_session_net.std(axis=1, ddof=1)
            sampled_sharpe = np.full(
                BOOTSTRAP_REPETITIONS, np.nan, dtype=float
            )
            valid_std = sampled_std_session_net > 0
            sampled_sharpe[valid_std] = (
                np.sqrt(252.0)
                * sampled_mean_session_net[valid_std]
                / sampled_std_session_net[valid_std]
            )

            for metric_name, values in [
                ("accuracy", sampled_accuracy),
                ("mean_session_net_usd", sampled_mean_session_net),
                ("annualized_session_sharpe", sampled_sharpe),
            ]:
                append_bootstrap_summary(
                    fold_id,
                    validation_year,
                    strategy,
                    metric_name,
                    block_length,
                    bootstrap_seed,
                    values,
                )


# Headline pooled OOF intervals are assembled from independent, fold-bounded
# moving blocks. No sampled block is allowed to cross a walk-forward boundary.
for block_length in BOOTSTRAP_BLOCK_LENGTHS:
    pooled_seed = MASTER_SEED + 90000 + block_length
    fold_draws = {}
    fold_session_tables = {}
    for fold_index, (fold_id, _, _) in enumerate(FOLD_SPECS):
        fold_sessions = canonical_validation_sessions[fold_id]
        fold_rng = np.random.default_rng(
            pooled_seed + 1000 * (fold_index + 1)
        )
        fold_draws[fold_id] = moving_block_indices(
            len(fold_sessions),
            block_length,
            BOOTSTRAP_REPETITIONS,
            fold_rng,
        )
        fold_session_tables[fold_id] = (
            events.loc[events["fold_id"].eq(fold_id)]
            .groupby(["strategy", "nyse_session_date"], sort=True)
            .agg(
                correct_count=("correct", "sum"),
                row_count=("correct", "size"),
                net_pnl_usd=("net_pnl_usd", "sum"),
            )
            .reset_index()
        )

    for strategy in strategy_names:
        sampled_correct_parts = []
        sampled_row_parts = []
        sampled_session_net_parts = []

        for fold_id, _, _ in FOLD_SPECS:
            fold_sessions = canonical_validation_sessions[fold_id]
            table = (
                fold_session_tables[fold_id]
                .loc[lambda x: x["strategy"].eq(strategy)]
                .set_index("nyse_session_date")
                .loc[fold_sessions]
            )
            draws = fold_draws[fold_id]
            sampled_correct_parts.append(
                table["correct_count"].to_numpy(dtype=float)[draws].sum(axis=1)
            )
            sampled_row_parts.append(
                table["row_count"].to_numpy(dtype=float)[draws].sum(axis=1)
            )
            sampled_session_net_parts.append(
                table["net_pnl_usd"].to_numpy(dtype=float)[draws]
            )

        sampled_correct = np.sum(sampled_correct_parts, axis=0)
        sampled_rows = np.sum(sampled_row_parts, axis=0)
        sampled_accuracy = sampled_correct / sampled_rows
        sampled_session_net = np.concatenate(sampled_session_net_parts, axis=1)
        sampled_mean_session_net = sampled_session_net.mean(axis=1)
        sampled_std_session_net = sampled_session_net.std(axis=1, ddof=1)
        sampled_sharpe = np.full(BOOTSTRAP_REPETITIONS, np.nan, dtype=float)
        valid_std = sampled_std_session_net > 0
        sampled_sharpe[valid_std] = (
            np.sqrt(252.0)
            * sampled_mean_session_net[valid_std]
            / sampled_std_session_net[valid_std]
        )

        for metric_name, values in [
            ("accuracy", sampled_accuracy),
            ("mean_session_net_usd", sampled_mean_session_net),
            ("annualized_session_sharpe", sampled_sharpe),
        ]:
            append_bootstrap_summary(
                "OOF_POOLED",
                "2022-2024",
                strategy,
                metric_name,
                block_length,
                pooled_seed,
                values,
            )

bootstrap = pd.DataFrame(bootstrap_rows)


# ------------------------------------------------------------
# 8) Final integrity gates
# ------------------------------------------------------------
failures = []

if ACTION_SPACE != "LONG_FLAT":
    failures.append("V1 action space is not LONG_FLAT.")
if POSITION_POLICY != "NON_OVERLAPPING_60M":
    failures.append("Position policy is not NON_OVERLAPPING_60M.")
event_session_year = pd.to_datetime(
    events["nyse_session_date"], errors="raise"
).dt.year
if event_session_year.ge(2025).any():
    failures.append("A 2025+ timestamp entered baseline events.")
if events["decision_id"].isna().any():
    failures.append("Missing validation decision ID.")
if events["decision_id"].astype(str).str.strip().eq("").any():
    failures.append("Blank validation decision ID.")
if not events["cost_semantics"].eq(
    "CURRENT_DEPLOYMENT_COUNTERFACTUAL"
).all():
    failures.append("Baseline event has ambiguous cost semantics.")
if not events.loc[events["executed"], "exit_time"].eq(
    events.loc[events["executed"], "decision_time"]
    + pd.Timedelta(minutes=HOLD_MINUTES)
).all():
    failures.append("An executed exit is not exactly +60 minutes.")
if not np.allclose(
    events.loc[events["executed"], "net_pnl_usd"],
    events.loc[events["executed"], "gross_pnl_usd"]
    - events.loc[events["executed"], "charged_cost_usd"],
    atol=1e-12,
):
    failures.append("Executed action P&L does not reconcile.")
if not events.loc[events["executed"], "charged_cost_usd"].eq(
    round_trip_cost_usd
).all():
    failures.append("Round-trip cost was not charged once per executed trade.")
if events.loc[~events["executed"], "charged_cost_usd"].ne(0).any():
    failures.append("A non-executed decision was charged a cost.")
if metrics["maximum_concurrent_positions"].gt(1).any():
    failures.append("Non-overlap mode exceeded one concurrent position.")
if not metrics["classification_scope"].eq(
    "OPPORTUNITY_ROWS_BEFORE_POSITION_FILTER"
).all():
    failures.append("Classification metric scope is ambiguous.")

for (fold_id, strategy), group in events.groupby(
    ["fold_id", "strategy"], sort=True
):
    group = group.sort_values(["decision_time", "decision_id"], kind="stable")
    last_exit = None
    for row in group.itertuples(index=False):
        predicted_long = row.predicted_action == "ENTER_LONG"
        signal_accounted_for = bool(row.executed) ^ bool(row.ignored_signal)
        if predicted_long != signal_accounted_for:
            failures.append(
                f"{fold_id}/{strategy}: LONG signal is not exactly executed or ignored."
            )
            break
        if row.executed and not predicted_long:
            failures.append(f"{fold_id}/{strategy}: executed without LONG signal.")
            break
        if row.ignored_signal and (not predicted_long or row.executed):
            failures.append(f"{fold_id}/{strategy}: invalid ignored signal.")
            break
        if row.executed:
            if last_exit is not None and row.decision_time < last_exit:
                failures.append(f"{fold_id}/{strategy}: overlapping execution.")
                break
            last_exit = row.exit_time
        elif row.ignored_signal:
            if last_exit is None or row.decision_time >= last_exit:
                failures.append(
                    f"{fold_id}/{strategy}: ignored signal without open position."
                )
                break
expected_bootstrap_rows = (
    (len(FOLD_SPECS) + 1)
    * len(strategy_names)
    * len(BOOTSTRAP_BLOCK_LENGTHS)
    * 3
)
if len(bootstrap) != expected_bootstrap_rows:
    failures.append(
        f"Expected {expected_bootstrap_rows} bootstrap rows; observed {len(bootstrap)}."
    )
expected_primary_rows = (len(FOLD_SPECS) + 1) * len(strategy_names) * 3
if int(bootstrap["primary_ci"].sum()) != expected_primary_rows:
    failures.append("Primary five-session bootstrap intervals are incomplete.")

non_sharpe_bootstrap = bootstrap.loc[
    ~bootstrap["metric"].eq("annualized_session_sharpe")
]
if not non_sharpe_bootstrap["valid_repetitions"].eq(
    BOOTSTRAP_REPETITIONS
).all():
    failures.append("A non-Sharpe bootstrap interval lost finite replications.")
if not np.isfinite(
    non_sharpe_bootstrap[
        ["estimate_bootstrap_mean", "ci_95_lower", "ci_95_upper"]
    ].to_numpy(dtype=float)
).all():
    failures.append("A non-Sharpe bootstrap interval is non-finite.")

sharpe_bootstrap = bootstrap.loc[
    bootstrap["metric"].eq("annualized_session_sharpe")
]
undefined_sharpe = sharpe_bootstrap["valid_repetitions"].eq(0)
if not sharpe_bootstrap.loc[undefined_sharpe, "interval_status"].eq(
    "UNDEFINED_ZERO_VARIANCE"
).all():
    failures.append("Undefined Sharpe interval lacks an explicit status.")
defined_sharpe = ~undefined_sharpe
if not np.isfinite(
    sharpe_bootstrap.loc[
        defined_sharpe,
        ["estimate_bootstrap_mean", "ci_95_lower", "ci_95_upper"],
    ].to_numpy(dtype=float)
).all():
    failures.append("A defined Sharpe bootstrap interval is non-finite.")


# ------------------------------------------------------------
# 9) Save deterministic artifacts and audit
# ------------------------------------------------------------
numeric_metric_columns = metrics.select_dtypes(include=[np.number]).columns
metrics[numeric_metric_columns] = metrics[numeric_metric_columns].round(10)
dependence["value"] = dependence["value"].round(10)
numeric_bootstrap_columns = bootstrap.select_dtypes(include=[np.number]).columns
bootstrap[numeric_bootstrap_columns] = bootstrap[numeric_bootstrap_columns].round(10)

events.to_parquet(CELL13_EVENTS_PATH, index=False)
dependence.to_csv(CELL13_DEPENDENCE_PATH, index=False)
metrics.to_csv(CELL13_METRICS_PATH, index=False)
bootstrap.to_csv(CELL13_BOOTSTRAP_PATH, index=False)

artifact_hashes = {
    "input_cell8_audit_sha256": sha256_file(CELL8_AUDIT_PATH),
    "input_cell10_audit_sha256": sha256_file(CELL10_AUDIT_PATH),
    "input_cell11_semantic_costs_sha256": actual_semantic_hash,
    "input_cell11_audit_sha256": sha256_file(CELL11_AUDIT_PATH),
    "input_cell12_path_outcomes_sha256": actual_path_hash,
    "input_cell12_audit_sha256": sha256_file(CELL12_AUDIT_PATH),
    "baseline_events_sha256": sha256_file(CELL13_EVENTS_PATH),
    "dependence_audit_sha256": sha256_file(CELL13_DEPENDENCE_PATH),
    "baseline_metrics_sha256": sha256_file(CELL13_METRICS_PATH),
    "block_bootstrap_ci_sha256": sha256_file(CELL13_BOOTSTRAP_PATH),
}

audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": BASELINE_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell8_policy_version": cell8_audit.get("policy_version"),
        "cell10_policy_version": cell10_audit.get("policy_version"),
        "cell11_policy_version": cell11_audit.get("policy_version"),
        "cell12_policy_version": cell12_audit.get("policy_version"),
        "cell8_assignments_sha256": cell8_assignment_hash,
        "cell10_labels_sha256": cell10_labels_hash,
        "cell10_audit_sha256": actual_cell10_audit_hash,
        "cell11_semantic_costs_sha256": actual_semantic_hash,
        "cell12_path_outcomes_sha256": actual_path_hash,
    },
    "evaluation_contract": {
        "action_space": ACTION_SPACE,
        "short_action_allowed": False,
        "short_outcome_retained_as_diagnostic": True,
        "position_policy": POSITION_POLICY,
        "hold_minutes": HOLD_MINUTES,
        "exit_then_entry_at_same_timestamp": EXIT_THEN_ENTRY_AT_SAME_TIMESTAMP,
        "maximum_concurrent_positions": 1,
        "oof_validation_years": [2022, 2023, 2024],
        "final_test_used": False,
        "cost_scenario": primary_cost_scenario,
        "round_trip_cost_usd": round_trip_cost_usd,
        "cost_semantics": "CURRENT_DEPLOYMENT_COUNTERFACTUAL",
        "historical_actual_pnl_claim": False,
        "classification_scope": "OPPORTUNITY_ROWS_BEFORE_POSITION_FILTER",
        "session_universe": "ALL_CANONICAL_VALIDATION_SESSIONS",
        "missing_canonical_sessions_allowed": False,
    },
    "dependence_contract": {
        "decision_frequency_minutes": 15,
        "label_horizon_minutes": 60,
        "empirical_acf_lags": [1, 2, 3],
        "ess_status": "DESCRIPTIVE_ONLY",
        "n_div_4_status": "THEORETICAL_REFERENCE_ONLY",
        "confidence_interval_method": "CONSECUTIVE_SESSION_MOVING_BLOCK_BOOTSTRAP",
        "primary_block_length_sessions": PRIMARY_BOOTSTRAP_BLOCK_SESSIONS,
        "sensitivity_block_lengths_sessions": BOOTSTRAP_BLOCK_LENGTHS,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "master_seed": MASTER_SEED,
        "pooled_oof_blocks_cross_fold_boundaries": False,
    },
    "counts": {
        "unique_oof_validation_decisions": int(len(set(validation_ids))),
        "baseline_event_rows": int(len(events)),
        "strategies": int(events["strategy"].nunique()),
        "canonical_validation_sessions_by_fold": {
            fold_id: len(sessions)
            for fold_id, sessions in canonical_validation_sessions.items()
        },
        "final_test_rows_used": 0,
    },
    "artifacts": {
        "baseline_events": str(CELL13_EVENTS_PATH),
        "dependence_ess_audit": str(CELL13_DEPENDENCE_PATH),
        "naive_baseline_metrics": str(CELL13_METRICS_PATH),
        "block_bootstrap_ci": str(CELL13_BOOTSTRAP_PATH),
    },
    "sha256": artifact_hashes,
    "modeling_gate": {
        "naive_baselines_established": not failures,
        "model_fitted": False,
        "required_future_comparison": (
            "paired five-session block-bootstrap differences versus "
            "ALWAYS_FLAT, ALWAYS_LONG, and TRAIN_PRIOR_PROBABILITY"
        ),
    },
    "failures": failures,
}

with open(CELL13_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

if failures:
    print("\nCELL 13 FAILURES")
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 13 DEPENDENCE AUDIT & NAIVE BASELINES: FAIL\n"
        f"{CELL13_AUDIT_PATH}"
    )

display_columns = [
    "fold_id",
    "strategy",
    "accuracy",
    "balanced_accuracy",
    "predicted_long_coverage",
    "executed_trades",
    "ignored_long_signals",
    "net_pnl_usd",
    "annualized_session_sharpe",
    "maximum_drawdown_usd",
]

print("\n" + "=" * 72)
print("CELL 13 — DEVELOPMENT-ONLY DEPENDENCE AUDIT & NAIVE BASELINES")
print("=" * 72)
print("Action space              : LONG / FLAT")
print("Position policy           : NON-OVERLAPPING 60m")
print("Cost semantics            : CURRENT DEPLOYMENT COUNTERFACTUAL")
print("OOF validation years      : 2022, 2023, 2024")
print("Final-test rows used      : 0")
print("Bootstrap                 : 2,000 reps; 5-session primary")
print("\n[OOF BASELINES]")
print(metrics[display_columns].to_string(index=False))
print("\nBaseline events           :", CELL13_EVENTS_PATH)
print("Dependence audit          :", CELL13_DEPENDENCE_PATH)
print("Baseline metrics          :", CELL13_METRICS_PATH)
print("Block-bootstrap intervals :", CELL13_BOOTSTRAP_PATH)
print("Cell 13 audit             :", CELL13_AUDIT_PATH)
print("\nCELL 13 DEPENDENCE AUDIT & NAIVE BASELINES: PASS")
print("=" * 72)

# ============================================================
# MES QUANT PIPELINE V1 CLEAN
# CELL 12 — DEVELOPMENT-ONLY 1m PATH OUTCOMES
# ============================================================
#
# PURPOSE
# -------
# Preserve the locked +60m endpoint outcome from Cell 10 and add the
# path information that a risk/execution layer needs: MFE, MAE, and
# close-path drawdown. Triple-barrier labels are deliberately NOT
# created because stop/target parameters and same-bar ordering remain
# OPEN policy decisions.
#
# Final Test is never looked up in mes_1m. All final-test path fields
# remain NaN/NaT and categorical fields remain SEALED.
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

CELL2_AUDIT_PATH = CLEAN_DIR / "cell2_raw_integrity_audit.json"
CELL10_LABELS_PATH = (
    CLEAN_DIR / "cell10_point_in_time_economic_labels_v1.parquet"
)
CELL10_AUDIT_PATH = CLEAN_DIR / "cell10_economic_label_audit.json"

CELL12_PATH_OUTCOMES_PATH = (
    CLEAN_DIR / "cell12_development_path_outcomes_v1.parquet"
)
CELL12_STATUS_SUMMARY_PATH = (
    CLEAN_DIR / "cell12_path_status_summary_v1.csv"
)
CELL12_AUDIT_PATH = CLEAN_DIR / "cell12_path_outcomes_audit.json"

PATH_POLICY_VERSION = "MES_V1_DEVELOPMENT_PATH_OUTCOMES_1.0"
EXPECTED_CELL2_POLICY = "MES_V1_RAW_INTEGRITY_1.1"
EXPECTED_CELL10_POLICY = "MES_V1_ECONOMIC_LABELS_1.0"
PATH_MINUTES = 60
CONTRACT_MULTIPLIER_USD_PER_POINT = 5.0


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


def strict_boolean(series, column_name):
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.astype(bool)
    tokens = series.astype("string").str.strip().str.lower()
    parsed = tokens.map({"true": True, "false": False})
    if parsed.isna().any():
        bad = sorted(tokens.loc[parsed.isna()].dropna().unique().tolist())
        raise RuntimeError(
            f"CELL 12 STOPPED — invalid boolean token in {column_name}: {bad}"
        )
    return parsed.astype(bool)


# ------------------------------------------------------------
# 3) Upstream and same-runtime gates
# ------------------------------------------------------------
required_paths = [CELL2_AUDIT_PATH, CELL10_LABELS_PATH, CELL10_AUDIT_PATH]
missing_paths = [str(path) for path in required_paths if not path.exists()]
if missing_paths:
    raise RuntimeError(
        "CELL 12 STOPPED — missing upstream artifacts:\n"
        + "\n".join(missing_paths)
        + "\n\nRun Cell 0 → Cell 10 first."
    )

if "mes_1m" not in globals():
    raise RuntimeError(
        "CELL 12 STOPPED — canonical mes_1m is not in memory.\n\n"
        "Restart the session and Run All so Cell 2 decodes the canonical "
        "DBN in this same runtime."
    )
if not isinstance(mes_1m, pd.DataFrame):
    raise RuntimeError("CELL 12 STOPPED — mes_1m is not a DataFrame.")

cell2_audit = load_json(CELL2_AUDIT_PATH)
cell10_audit = load_json(CELL10_AUDIT_PATH)

if cell2_audit.get("status") != "PASS" or cell2_audit.get("failures", []):
    raise RuntimeError("CELL 12 STOPPED — Cell 2 audit is not clean PASS.")
if cell2_audit.get("policy_version") != EXPECTED_CELL2_POLICY:
    raise RuntimeError(
        "CELL 12 STOPPED — Cell 2 provenance addendum is missing."
    )
if cell10_audit.get("status") != "PASS":
    raise RuntimeError("CELL 12 STOPPED — Cell 10 audit is not PASS.")
if cell10_audit.get("failures", []):
    raise RuntimeError("CELL 12 STOPPED — Cell 10 audit has failures.")
if cell10_audit.get("policy_version") != EXPECTED_CELL10_POLICY:
    raise RuntimeError(
        "CELL 12 STOPPED — unexpected Cell 10 policy version: "
        f"{cell10_audit.get('policy_version')}"
    )

expected_label_hash = (
    cell10_audit.get("sha256", {}).get("economic_labels_sha256")
)
actual_label_hash = sha256_file(CELL10_LABELS_PATH)
if not expected_label_hash or expected_label_hash != actual_label_hash:
    raise RuntimeError(
        "CELL 12 STOPPED — Cell 10 label hash mismatch.\n"
        f"Audit : {expected_label_hash}\n"
        f"Actual: {actual_label_hash}"
    )


# ------------------------------------------------------------
# 4) Bind in-memory mes_1m to the Cell 2 audit
# ------------------------------------------------------------
required_1m_columns = {"open", "high", "low", "close", "instrument_id"}
missing_1m_columns = required_1m_columns - set(mes_1m.columns)
if missing_1m_columns:
    raise RuntimeError(
        "CELL 12 STOPPED — missing mes_1m columns:\n"
        + ", ".join(sorted(missing_1m_columns))
    )
if not isinstance(mes_1m.index, pd.DatetimeIndex):
    raise RuntimeError("CELL 12 STOPPED — mes_1m index is not DatetimeIndex.")
if mes_1m.index.tz is None:
    raise RuntimeError("CELL 12 STOPPED — mes_1m index is timezone-naive.")
if not mes_1m.index.is_monotonic_increasing:
    raise RuntimeError("CELL 12 STOPPED — mes_1m index is not sorted.")
if mes_1m.index.duplicated().any():
    raise RuntimeError("CELL 12 STOPPED — duplicate mes_1m timestamps.")

decoded_contract = cell2_audit.get("decoded", {})
expected_1m_rows = int(decoded_contract.get("rows", -1))
if len(mes_1m) != expected_1m_rows:
    raise RuntimeError(
        "CELL 12 STOPPED — mes_1m row count differs from Cell 2 audit."
    )

expected_first = pd.Timestamp(decoded_contract.get("first_timestamp"))
expected_last = pd.Timestamp(decoded_contract.get("last_timestamp"))
if mes_1m.index[0] != expected_first or mes_1m.index[-1] != expected_last:
    raise RuntimeError(
        "CELL 12 STOPPED — mes_1m endpoints differ from Cell 2 audit."
    )

raw_1m = mes_1m

# Strongly fingerprint the exact in-memory decoded frame consumed here.
# The raw DBN SHA in Cell 2 identifies the source file; this fingerprint
# identifies the decoded bytes actually used by the path calculation.
memory_hash_columns = ["open", "high", "low", "close", "instrument_id"]
memory_row_hashes = pd.util.hash_pandas_object(
    raw_1m[memory_hash_columns],
    index=True,
    categorize=False,
).to_numpy(dtype="uint64", copy=False)
mes_1m_memory_sha256 = hashlib.sha256(memory_row_hashes.tobytes()).hexdigest()
del memory_row_hashes

expected_memory_sha256 = decoded_contract.get("content_sha256")
runtime_memory_sha256 = globals().get("CELL2_MES_1M_CONTENT_SHA256")
if not expected_memory_sha256:
    raise RuntimeError("CELL 12 STOPPED — Cell 2 audit has no content SHA256.")
if runtime_memory_sha256 != expected_memory_sha256:
    raise RuntimeError(
        "CELL 12 STOPPED — the Cell 2 same-runtime fingerprint is missing/mismatched."
    )
if mes_1m_memory_sha256 != expected_memory_sha256:
    raise RuntimeError(
        "CELL 12 STOPPED — in-memory mes_1m content changed after Cell 2."
    )


# ------------------------------------------------------------
# 5) Load Cell 10 labels and prove the Final Test seal
# ------------------------------------------------------------
labels = pd.read_parquet(CELL10_LABELS_PATH)
required_label_columns = {
    "decision_id",
    "decision_time",
    "label_end_time",
    "nyse_session_date",
    "instrument_id",
    "outer_partition",
    "label_status",
    "label_usable",
    "entry_reference_close",
    "exit_reference_close_60m",
    "gross_move_points_60m",
    "gross_move_usd_60m",
    "economic_label_primary",
}
missing_label_columns = required_label_columns - set(labels.columns)
if missing_label_columns:
    raise RuntimeError(
        "CELL 12 STOPPED — missing Cell 10 columns:\n"
        + ", ".join(sorted(missing_label_columns))
    )

labels = labels.copy()
labels["decision_time"] = pd.to_datetime(
    labels["decision_time"], utc=True, errors="raise"
)
labels["label_end_time"] = pd.to_datetime(
    labels["label_end_time"], utc=True, errors="raise"
)
labels["label_usable"] = strict_boolean(labels["label_usable"], "label_usable")
labels = labels.sort_values("decision_time").reset_index(drop=True)

final_test_mask = labels["outer_partition"].eq("FINAL_TEST")
development_mask = labels["outer_partition"].isin(["TRAIN", "VALIDATION"])
usable_dev_mask = development_mask & labels["label_usable"]

expected_final_rows = int(
    cell10_audit.get("counts", {}).get("final_test_rows_sealed", -1)
)
observed_final_rows = int(final_test_mask.sum())
if observed_final_rows != expected_final_rows or observed_final_rows != 8654:
    raise RuntimeError("CELL 12 STOPPED — final-test row count changed.")
if not labels.loc[final_test_mask, "label_status"].eq(
    "SEALED_FINAL_TEST"
).all():
    raise RuntimeError("CELL 12 STOPPED — final-test status is not SEALED.")
if not labels.loc[final_test_mask, "economic_label_primary"].eq("SEALED").all():
    raise RuntimeError("CELL 12 STOPPED — final-test labels are not SEALED.")

sealed_numeric_columns = [
    "entry_reference_close",
    "exit_reference_close_60m",
    "gross_move_points_60m",
    "gross_move_usd_60m",
]
if labels.loc[final_test_mask, sealed_numeric_columns].notna().any().any():
    raise RuntimeError(
        "CELL 12 STOPPED — a future-derived numeric value exists in Final Test."
    )


# ------------------------------------------------------------
# 6) Allocate outputs; build lookup requests from Development only
# ------------------------------------------------------------
n_rows = len(labels)
dev_positions = np.flatnonzero(usable_dev_mask.to_numpy())
final_positions = np.flatnonzero(final_test_mask.to_numpy())
final_test_price_lookup_count = int(
    np.intersect1d(dev_positions, final_positions, assume_unique=True).size
    * PATH_MINUTES
)
if final_test_price_lookup_count != 0:
    raise RuntimeError("CELL 12 STOPPED — a Final Test row entered the price lookup.")
dev_times = labels.loc[usable_dev_mask, "decision_time"].reset_index(drop=True)
dev_instrument = pd.to_numeric(
    labels.loc[usable_dev_mask, "instrument_id"], errors="raise"
).to_numpy(dtype=np.int64)
dev_entry = pd.to_numeric(
    labels.loc[usable_dev_mask, "entry_reference_close"], errors="raise"
).to_numpy(dtype=float)
dev_endpoint = pd.to_numeric(
    labels.loc[usable_dev_mask, "exit_reference_close_60m"], errors="raise"
).to_numpy(dtype=float)

n_dev = len(dev_positions)
path_present = np.zeros(n_dev, dtype=np.int16)
path_instrument_changed = np.zeros(n_dev, dtype=bool)
path_high = np.full(n_dev, -np.inf, dtype=float)
path_low = np.full(n_dev, np.inf, dtype=float)
path_high_first_offset = np.full(n_dev, -1, dtype=np.int16)
path_low_first_offset = np.full(n_dev, -1, dtype=np.int16)
last_close = np.full(n_dev, np.nan, dtype=float)

running_peak_close = dev_entry.copy()
running_trough_close = dev_entry.copy()
long_close_max_drawdown = np.zeros(n_dev, dtype=float)
short_close_max_drawup = np.zeros(n_dev, dtype=float)
minutes_above_entry = np.zeros(n_dev, dtype=np.int16)
minutes_below_entry = np.zeros(n_dev, dtype=np.int16)
minutes_at_entry = np.zeros(n_dev, dtype=np.int16)


# ------------------------------------------------------------
# 7) Exact 1m path: bar starts t, t+1m, ..., t+59m
# ------------------------------------------------------------
for minute_offset in range(PATH_MINUTES):
    lookup_times = pd.DatetimeIndex(
        dev_times + pd.Timedelta(minutes=minute_offset)
    )
    observed = raw_1m.reindex(lookup_times)

    observed_instrument = pd.to_numeric(
        observed["instrument_id"], errors="coerce"
    ).to_numpy(dtype=float)
    observed_high = pd.to_numeric(
        observed["high"], errors="coerce"
    ).to_numpy(dtype=float)
    observed_low = pd.to_numeric(
        observed["low"], errors="coerce"
    ).to_numpy(dtype=float)
    observed_close = pd.to_numeric(
        observed["close"], errors="coerce"
    ).to_numpy(dtype=float)

    present = (
        np.isfinite(observed_instrument)
        & np.isfinite(observed_high)
        & np.isfinite(observed_low)
        & np.isfinite(observed_close)
    )
    instrument_match = present & np.equal(
        observed_instrument, dev_instrument.astype(float)
    )

    path_present += present.astype(np.int16)
    path_instrument_changed |= present & ~instrument_match

    new_high = instrument_match & (observed_high > path_high)
    new_low = instrument_match & (observed_low < path_low)
    path_high[new_high] = observed_high[new_high]
    path_low[new_low] = observed_low[new_low]
    path_high_first_offset[new_high] = minute_offset
    path_low_first_offset[new_low] = minute_offset

    valid_close = instrument_match & np.isfinite(observed_close)
    running_peak_close[valid_close] = np.maximum(
        running_peak_close[valid_close], observed_close[valid_close]
    )
    running_trough_close[valid_close] = np.minimum(
        running_trough_close[valid_close], observed_close[valid_close]
    )
    long_close_max_drawdown[valid_close] = np.maximum(
        long_close_max_drawdown[valid_close],
        running_peak_close[valid_close] - observed_close[valid_close],
    )
    short_close_max_drawup[valid_close] = np.maximum(
        short_close_max_drawup[valid_close],
        observed_close[valid_close] - running_trough_close[valid_close],
    )

    minutes_above_entry += (
        valid_close & (observed_close > dev_entry)
    ).astype(np.int16)
    minutes_below_entry += (
        valid_close & (observed_close < dev_entry)
    ).astype(np.int16)
    minutes_at_entry += (
        valid_close & np.isclose(observed_close, dev_entry, atol=1e-12)
    ).astype(np.int16)

    if minute_offset == PATH_MINUTES - 1:
        last_close[:] = observed_close


# ------------------------------------------------------------
# 8) Reconciliation and path metrics
# ------------------------------------------------------------
path_complete = path_present == PATH_MINUTES
endpoint_match = np.isclose(last_close, dev_endpoint, atol=1e-12, rtol=0.0)
path_usable_dev = (
    path_complete
    & ~path_instrument_changed
    & endpoint_match
    & np.isfinite(path_high)
    & np.isfinite(path_low)
)

failures = []
if not path_usable_dev.all():
    failures.append(
        "A Cell 10 usable development label lacks an exact 60-row 1m path."
    )
if not endpoint_match.all():
    failures.append("1m endpoint close does not match Cell 10 +60m close.")
if path_instrument_changed.any():
    failures.append("Instrument changed inside a usable 1m path.")

path_status = np.full(n_rows, "LABEL_UNUSABLE", dtype=object)
path_status[final_test_mask.to_numpy()] = "SEALED_FINAL_TEST"
path_status[dev_positions] = np.where(
    path_usable_dev, "USABLE", "PATH_INTEGRITY_FAILURE"
)

labels["path_status"] = path_status
labels["path_usable"] = False
labels.loc[dev_positions, "path_usable"] = path_usable_dev
labels["path_1m_expected"] = PATH_MINUTES
labels["path_1m_present"] = np.nan
labels.loc[dev_positions, "path_1m_present"] = path_present.astype(float)
labels["path_instrument_changed"] = pd.NA
labels.loc[dev_positions, "path_instrument_changed"] = path_instrument_changed

numeric_path_columns = [
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
    "short_mfe_points_60m",
    "short_mae_points_60m",
    "long_mfe_usd_60m",
    "long_mae_usd_60m",
    "short_mfe_usd_60m",
    "short_mae_usd_60m",
    "long_close_path_max_drawdown_points_60m",
    "short_close_path_max_drawup_points_60m",
    "minutes_above_entry",
    "minutes_below_entry",
    "minutes_at_entry",
]
for column in numeric_path_columns:
    labels[column] = np.nan

labels.loc[dev_positions, "path_high_60m"] = path_high
labels.loc[dev_positions, "path_low_60m"] = path_low

long_mfe = np.maximum(path_high - dev_entry, 0.0)
long_mae = np.maximum(dev_entry - path_low, 0.0)
short_mfe = long_mae.copy()
short_mae = long_mfe.copy()

labels.loc[dev_positions, "long_mfe_points_60m"] = long_mfe
labels.loc[dev_positions, "long_mae_points_60m"] = long_mae
labels.loc[dev_positions, "short_mfe_points_60m"] = short_mfe
labels.loc[dev_positions, "short_mae_points_60m"] = short_mae
labels.loc[dev_positions, "long_mfe_usd_60m"] = (
    long_mfe * CONTRACT_MULTIPLIER_USD_PER_POINT
)
labels.loc[dev_positions, "long_mae_usd_60m"] = (
    long_mae * CONTRACT_MULTIPLIER_USD_PER_POINT
)
labels.loc[dev_positions, "short_mfe_usd_60m"] = (
    short_mfe * CONTRACT_MULTIPLIER_USD_PER_POINT
)
labels.loc[dev_positions, "short_mae_usd_60m"] = (
    short_mae * CONTRACT_MULTIPLIER_USD_PER_POINT
)
labels.loc[
    dev_positions, "long_close_path_max_drawdown_points_60m"
] = long_close_max_drawdown
labels.loc[
    dev_positions, "short_close_path_max_drawup_points_60m"
] = short_close_max_drawup
labels.loc[dev_positions, "minutes_above_entry"] = minutes_above_entry
labels.loc[dev_positions, "minutes_below_entry"] = minutes_below_entry
labels.loc[dev_positions, "minutes_at_entry"] = minutes_at_entry

labels["path_high_first_bar_start"] = pd.Series(
    pd.NaT, index=labels.index, dtype="datetime64[ns, UTC]"
)
labels["path_low_first_bar_start"] = pd.Series(
    pd.NaT, index=labels.index, dtype="datetime64[ns, UTC]"
)
high_offset_valid = path_high_first_offset >= 0
low_offset_valid = path_low_first_offset >= 0
high_times = pd.Series(pd.NaT, index=np.arange(n_dev), dtype="datetime64[ns, UTC]")
low_times = pd.Series(pd.NaT, index=np.arange(n_dev), dtype="datetime64[ns, UTC]")
high_times.loc[high_offset_valid] = (
    dev_times.loc[high_offset_valid].reset_index(drop=True)
    + pd.to_timedelta(path_high_first_offset[high_offset_valid], unit="m")
).to_numpy()
low_times.loc[low_offset_valid] = (
    dev_times.loc[low_offset_valid].reset_index(drop=True)
    + pd.to_timedelta(path_low_first_offset[low_offset_valid], unit="m")
).to_numpy()
labels.loc[dev_positions, "path_high_first_bar_start"] = high_times.to_numpy()
labels.loc[dev_positions, "path_low_first_bar_start"] = low_times.to_numpy()

labels["triple_barrier_status"] = "OPEN_POLICY_NOT_LOCKED"
labels.loc[final_test_mask, "triple_barrier_status"] = "SEALED"


# ------------------------------------------------------------
# 9) Final hard gates
# ------------------------------------------------------------
if labels.loc[final_test_mask, numeric_path_columns].notna().any().any():
    failures.append("A path-derived numeric value entered Final Test.")
if labels.loc[
    final_test_mask,
    ["path_high_first_bar_start", "path_low_first_bar_start"],
].notna().any().any():
    failures.append("A path-derived timestamp entered Final Test.")
if labels.loc[final_test_mask, "path_usable"].any():
    failures.append("A Final Test row became path-usable.")
if not labels.loc[final_test_mask, "path_status"].eq(
    "SEALED_FINAL_TEST"
).all():
    failures.append("Final Test path status is not SEALED.")
if not labels.loc[usable_dev_mask, "path_usable"].all():
    failures.append("Not every usable development label has a usable path.")
if not labels.loc[usable_dev_mask, "path_1m_present"].eq(PATH_MINUTES).all():
    failures.append("A usable path does not contain exactly 60 one-minute bars.")
if not np.allclose(
    labels.loc[usable_dev_mask, "long_mfe_points_60m"],
    labels.loc[usable_dev_mask, "short_mae_points_60m"],
    atol=1e-12,
):
    failures.append("Long MFE and Short MAE symmetry failed.")
if not np.allclose(
    labels.loc[usable_dev_mask, "long_mae_points_60m"],
    labels.loc[usable_dev_mask, "short_mfe_points_60m"],
    atol=1e-12,
):
    failures.append("Long MAE and Short MFE symmetry failed.")


# ------------------------------------------------------------
# 10) Save artifacts and audit
# ------------------------------------------------------------
status_summary = (
    labels.groupby(["outer_partition", "path_status"], dropna=False)
    .size()
    .rename("rows")
    .reset_index()
)

labels.to_parquet(CELL12_PATH_OUTCOMES_PATH, index=False)
status_summary.to_csv(CELL12_STATUS_SUMMARY_PATH, index=False)

artifact_hashes = {
    "input_cell2_audit_sha256": sha256_file(CELL2_AUDIT_PATH),
    "input_cell10_labels_sha256": actual_label_hash,
    "input_cell10_audit_sha256": sha256_file(CELL10_AUDIT_PATH),
    "path_outcomes_sha256": sha256_file(CELL12_PATH_OUTCOMES_PATH),
    "path_status_summary_sha256": sha256_file(CELL12_STATUS_SUMMARY_PATH),
}

audit = {
    "audit_written_utc": datetime.now(timezone.utc).isoformat(),
    "policy_version": PATH_POLICY_VERSION,
    "status": "PASS" if not failures else "FAIL",
    "upstream_binding": {
        "cell10_policy_version": cell10_audit.get("policy_version"),
        "cell10_labels_sha256": actual_label_hash,
        "cell2_raw_file_sha256": cell2_audit.get("raw_file", {}).get("sha256"),
        "mes_1m_memory_sha256": mes_1m_memory_sha256,
        "mes_1m_rows_in_memory": int(len(raw_1m)),
        "mes_1m_first_timestamp": raw_1m.index[0].isoformat(),
        "mes_1m_last_timestamp": raw_1m.index[-1].isoformat(),
    },
    "path_contract": {
        "entry": "completed 15m close at decision_time",
        "one_minute_bar_start_offsets": "0..59 minutes after decision_time",
        "one_minute_rows_required": PATH_MINUTES,
        "endpoint_reconciliation": (
            "close of 1m bar starting t+59m equals Cell 10 +60m close"
        ),
        "same_instrument_required": True,
        "mfe_mae_before_cost": True,
        "triple_barrier_created": False,
        "triple_barrier_status": "OPEN",
        "same_1m_bar_barrier_order": "UNOBSERVABLE_WITH_OHLC; NEVER_GUESSED",
        "target_fields_allowed_as_features": False,
    },
    "counts": {
        "rows": int(len(labels)),
        "usable_development_paths": int(
            labels.loc[development_mask, "path_usable"].sum()
        ),
        "final_test_rows_sealed": observed_final_rows,
        "final_test_price_lookup_count": final_test_price_lookup_count,
    },
    "artifacts": {
        "path_outcomes": str(CELL12_PATH_OUTCOMES_PATH),
        "path_status_summary": str(CELL12_STATUS_SUMMARY_PATH),
    },
    "sha256": artifact_hashes,
    "open_items": [
        "Lock LONG/FLAT execution policy before converting outcomes to actions.",
        "Lock stop/target distances before any triple-barrier auxiliary label.",
        "Treat a 1m bar touching both barriers as AMBIGUOUS, never ordered.",
    ],
    "failures": failures,
}

with open(CELL12_AUDIT_PATH, "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

if failures:
    print("\nCELL 12 FAILURES")
    for failure in failures:
        print(" -", failure)
    raise RuntimeError(
        "\nCELL 12 DEVELOPMENT PATH OUTCOMES: FAIL\n"
        f"{CELL12_AUDIT_PATH}"
    )

print("\n" + "=" * 72)
print("CELL 12 — DEVELOPMENT-ONLY 1m PATH OUTCOMES")
print("=" * 72)
print("Cell 10 labels SHA256       :", actual_label_hash)
print("Development paths usable   :", f"{int(usable_dev_mask.sum()):,}")
print("Required 1m bars per path  :", PATH_MINUTES)
print("Endpoint mismatches         :", int((~endpoint_match).sum()))
print("Final-test lookup count     : 0")
print("Final-test path fields      : SEALED")
print("Triple barrier              : OPEN / NOT CREATED")
print("Path outcomes               :", CELL12_PATH_OUTCOMES_PATH)
print("Cell 12 audit               :", CELL12_AUDIT_PATH)
print("\nCELL 12 DEVELOPMENT PATH OUTCOMES: PASS")
print("=" * 72)

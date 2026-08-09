"""Restore exact Drive byte lengths after text materialization added one LF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT_ROOT / "reference" / "colab_v1_cells_0_13" / "MES_V1_cells_0_13.ipynb"
EVIDENCE_DIR = PROJECT_ROOT / "reference" / "drive_evidence_v1"

EXPECTED_NOTEBOOK_SIZE = 527_161
EXPECTED_EVIDENCE_SIZES = {
    "cell10_development_label_summary_v1.csv": 262,
    "cell10_economic_label_audit.json": 4447,
    "cell11_cost_scenarios_semantic_v1.csv": 1741,
    "cell11_cost_temporality_audit.json": 2152,
    "cell11_fee_vintage_registry_v1.csv": 1264,
    "cell12_path_outcomes_audit.json": 2430,
    "cell12_path_status_summary_v1.csv": 133,
    "cell13_block_bootstrap_ci_v1.csv": 17172,
    "cell13_dependence_ess_audit_v1.csv": 1822,
    "cell13_development_baseline_audit.json": 4331,
    "cell13_naive_baseline_metrics_v1.csv": 7195,
    "cell2_raw_integrity_audit.json": 3624,
    "cell3_gap_distribution.csv": 2107,
    "cell3_supplemental_raw_audit.json": 2170,
    "cell4_dataset_condition_audit.json": 787,
    "cell5_15m_resample_audit.json": 1795,
    "cell5_degraded_day_mes_impact.csv": 1241,
    "cell5_launch_liquidity_monthly.csv": 5204,
    "cell6_gap_attribution_audit.json": 1873,
    "cell6_gap_attribution_summary.csv": 760,
    "cell6_gap_clock_patterns.csv": 83604,
    "cell7_decision_universe_audit.json": 3047,
    "cell7_decision_universe_daily_summary.csv": 157136,
    "cell8_purge_boundaries_v1.csv": 592,
    "cell8_purged_split_audit.json": 6158,
    "cell8_walk_forward_folds_v1.csv": 501,
    "cell9_cost_model_audit.json": 6704,
    "cell9_cost_parameters_v1.csv": 1558,
    "cell9_cost_scenarios_v1.csv": 970,
    "databento_glbx_mdp3_condition_registry.csv": 74225,
    "databento_glbx_mdp3_condition_registry_meta.json": 590,
    "databento_glbx_mdp3_flagged_conditions.csv": 561,
    "pip_check_snapshot.txt": 133,
    "pip_freeze_snapshot.txt": 12755,
    "raw_source_baseline.json": 2079,
    "runtime_source_audit.json": 2716,
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def restore_exact_size(path: Path, expected_size: int) -> bytes:
    payload = path.read_bytes()
    if len(payload) == expected_size:
        return payload
    if len(payload) == expected_size + 1 and payload.endswith(b"\n"):
        payload = payload[:-1]
        path.write_bytes(payload)
        return payload
    raise RuntimeError(
        f"Unexpected materialized size for {path.name}: {len(payload)}; expected {expected_size}"
    )


def main() -> None:
    notebook_payload = restore_exact_size(NOTEBOOK, EXPECTED_NOTEBOOK_SIZE)
    records: list[dict[str, object]] = []
    actual_names = {
        path.name for path in EVIDENCE_DIR.iterdir() if path.is_file() and path.name != "evidence_manifest.json"
    }
    if actual_names != set(EXPECTED_EVIDENCE_SIZES):
        missing = sorted(set(EXPECTED_EVIDENCE_SIZES) - actual_names)
        extra = sorted(actual_names - set(EXPECTED_EVIDENCE_SIZES))
        raise RuntimeError(f"Evidence file set mismatch; missing={missing}, extra={extra}")

    for name, expected_size in sorted(EXPECTED_EVIDENCE_SIZES.items()):
        payload = restore_exact_size(EVIDENCE_DIR / name, expected_size)
        records.append({"file": name, "size_bytes": len(payload), "sha256": sha256(payload)})

    manifest = {
        "manifest_version": "MES_V1_DRIVE_EVIDENCE_1.0",
        "drive_folder_id": "1OiG-wHzVqPV58UHqCdfR8YWB4nG9E1xM",
        "file_count": len(records),
        "files": records,
    }
    (EVIDENCE_DIR / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        "PASS: restored exact Drive sizes for "
        f"notebook={len(notebook_payload)} bytes and evidence={len(records)} files"
    )
    print(f"Notebook SHA256: {sha256(notebook_payload)}")


if __name__ == "__main__":
    main()

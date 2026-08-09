from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_MANIFEST_VERSION = "MES_V1_FROZEN_COLAB_1.0"
EXPECTED_MANIFEST_STATUS = "PROVISIONAL_FULL_PARITY_PENDING_LOCAL_LARGE_ARTIFACTS"

EXPECTED_NOTEBOOK: dict[str, Any] = {
    "id": "1U3KJQJmTnt2bQyeQPfPybgZa9_VllMjG",
    "drive_size_bytes": 527161,
    "local_reference_file": "reference/colab_v1_cells_0_13/MES_V1_cells_0_13.ipynb",
    "local_reference_sha256": "59125e89c2aa05f34660b6b70194f98d99b561085354174911523cda402c0f53",
    "cell_order": list(range(14)),
    "execution_counts": list(range(37, 51)),
    "cell_source_manifest": "reference/colab_v1_cells_0_13/cell_sources_manifest.json",
    "cell_source_manifest_sha256": "c10b9cf8c6fe9923c9484f42442765e74a446123059583f3a9d183ad583074f6",
    "sha256s_file": "reference/colab_v1_cells_0_13/SHA256SUMS.txt",
    "sha256s_sha256": "78cffe3cdf3d7440a1342f40a1d483ea44514f1f5d2a23b9a52b53bcc5b8eb98",
}

EXPECTED_DRIVE: dict[str, Any] = {
    "artifact_folder_id": "1OiG-wHzVqPV58UHqCdfR8YWB4nG9E1xM",
    "small_evidence_reference": "reference/drive_evidence_v1/",
    "small_evidence_manifest": "reference/drive_evidence_v1/evidence_manifest.json",
    "small_evidence_manifest_sha256": "6cc4a64de2fb64ee5339475411df896c3f415050c4b7e876c9878dea4e585b62",
    "small_evidence_manifest_size_bytes": 6349,
    "small_evidence_file_count": 36,
}

EXPECTED_LOCKED_CONTRACTS: dict[str, Any] = {
    "instrument": "MES.v.0",
    "decision_frequency_minutes": 15,
    "label_horizon_minutes": 60,
    "action_space": "LONG_FLAT",
    "position_policy": "NON_OVERLAPPING_60M",
    "final_test_start_year": 2025,
    "final_test_rows": 8654,
    "final_test_status": "SEALED",
    "final_test_outcomes_allowed": False,
    "bootstrap_repetitions": 2000,
    "primary_bootstrap_block_sessions": 5,
    "master_seed": 20260809,
}

EXPECTED_GOLDEN_COUNTS: dict[str, int] = {
    "raw_rows": 2551123,
    "bars_15m": 170586,
    "decision_universe_rows": 39847,
    "outer_train_rows": 25685,
    "outer_validation_rows": 5508,
    "development_rows": 31193,
    "final_test_rows": 8654,
    "usable_labels_and_paths": 31165,
    "label_long": 15188,
    "label_short": 13147,
    "label_no_trade": 2830,
    "oof_decisions": 16494,
    "cell13_event_rows": 65976,
    "canonical_oof_sessions": 751,
    "cell13_final_test_rows_used": 0,
}

# These values are deliberately duplicated outside the JSON release manifest.  A
# manifest that rewrites its own hashes/counts therefore cannot validate itself.
EXPECTED_ARTIFACTS: dict[str, dict[str, Any]] = {
    "raw_dbn": {
        "producer": "SOURCE",
        "file": "MES_2019_2026_1m.dbn.zst",
        "size_bytes": 40078487,
        "sha256": "49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0",
        "parity_mode": "BYTE_EXACT",
        "upstream": [],
    },
    "decoded_memory_content": {
        "producer": "CELL_2",
        "file": None,
        "size_bytes": None,
        "sha256": "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584",
        "parity_mode": "PANDAS_UINT64_ROW_HASH_CONTENT",
        "upstream": ["raw_dbn"],
    },
    "cell5_bars_15m": {
        "producer": "CELL_5",
        "file": "MES_2019_2026_15m_clean.parquet",
        "size_bytes": 6904346,
        "sha256": "558723ed6965c23fb93a7abc61d65eee405dd9eb5f41a36a96c7b66bbc806dad",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["decoded_memory_content"],
    },
    "cell5_audit": {
        "producer": "CELL_5",
        "file": "cell5_15m_resample_audit.json",
        "size_bytes": 1795,
        "sha256": "0fd7aba3cca2f3ae88d24b048708517e4829302275ab25f90821ef2af2621c73",
        "parity_mode": "CANONICAL_JSON",
        "upstream": ["decoded_memory_content"],
    },
    "cell6_audit": {
        "producer": "CELL_6",
        "file": "cell6_gap_attribution_audit.json",
        "size_bytes": 1873,
        "sha256": "24d580e189feaf9e6f6ca6750dcf5a358ff551920f4dc3dda02892b87c3ec2b0",
        "parity_mode": "CANONICAL_JSON",
        "upstream": ["cell5_bars_15m"],
    },
    "cell7_universe": {
        "producer": "CELL_7",
        "file": "cell7_decision_universe_v1.parquet",
        "size_bytes": 1529761,
        "sha256": "f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["cell5_bars_15m", "cell5_audit", "cell6_audit"],
    },
    "cell7_audit": {
        "producer": "CELL_7",
        "file": "cell7_decision_universe_audit.json",
        "size_bytes": 3047,
        "sha256": "3e5f76d3ea3c91fe37bfb7f58235dc4c616da88b299a1d370a8a3c67653abf7e",
        "parity_mode": "CANONICAL_JSON",
        "upstream": ["cell7_universe"],
    },
    "cell8_assignments": {
        "producer": "CELL_8",
        "file": "cell8_purged_split_assignments_v1.parquet",
        "size_bytes": 1447931,
        "sha256": "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["cell7_universe", "cell7_audit"],
    },
    "cell8_audit": {
        "producer": "CELL_8",
        "file": "cell8_purged_split_audit.json",
        "size_bytes": 6158,
        "sha256": "add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a",
        "parity_mode": "CANONICAL_JSON",
        "upstream": ["cell8_assignments"],
    },
    "cell9_parameters": {
        "producer": "CELL_9",
        "file": "cell9_cost_parameters_v1.csv",
        "size_bytes": 1558,
        "sha256": "24d1953df9c497d991d3b6eb7a9c053046d0c7dbd2a006f4c4c03fbd02aab4f9",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell8_assignments"],
    },
    "cell9_scenarios": {
        "producer": "CELL_9",
        "file": "cell9_cost_scenarios_v1.csv",
        "size_bytes": 970,
        "sha256": "2248d59ff32361dff9c5df94bfdf8d7ad6942ee50ef3d6e1c6a3731779aeff4f",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell9_parameters"],
    },
    "cell10_labels": {
        "producer": "CELL_10",
        "file": "cell10_point_in_time_economic_labels_v1.parquet",
        "size_bytes": 2172575,
        "sha256": "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["cell5_bars_15m", "cell8_assignments", "cell9_scenarios"],
    },
    "cell11_semantic_costs": {
        "producer": "CELL_11",
        "file": "cell11_cost_scenarios_semantic_v1.csv",
        "size_bytes": 1741,
        "sha256": "7b3c619f1a8c4612d9a6b3df40f86136030baae616c4b0cd160e1651c2db0302",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell9_parameters", "cell9_scenarios"],
    },
    "cell11_fee_vintages": {
        "producer": "CELL_11",
        "file": "cell11_fee_vintage_registry_v1.csv",
        "size_bytes": 1264,
        "sha256": "47a1d87591fb0502f939d89718ee1c52fc21276461a8103841af98f0d61167e1",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell9_parameters"],
    },
    "cell12_paths": {
        "producer": "CELL_12",
        "file": "cell12_development_path_outcomes_v1.parquet",
        "size_bytes": 3223745,
        "sha256": "8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["decoded_memory_content", "cell10_labels"],
    },
    "cell13_events": {
        "producer": "CELL_13",
        "file": "cell13_development_oof_baseline_events_v1.parquet",
        "size_bytes": 606251,
        "sha256": "a745ad7dd8f39f9c4b90cafedb8ab6cd8242c0991c177698e86dbfad68bc7df4",
        "parity_mode": "BYTE_EXACT_AND_ORDERED_CONTENT",
        "upstream": ["cell8_assignments", "cell10_labels", "cell11_semantic_costs", "cell12_paths"],
    },
    "cell13_dependence": {
        "producer": "CELL_13",
        "file": "cell13_dependence_ess_audit_v1.csv",
        "size_bytes": 1822,
        "sha256": "113412d42ac08bd87c18cec014924252f9e53a0762fa061ca887598681344ded",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell13_events"],
    },
    "cell13_metrics": {
        "producer": "CELL_13",
        "file": "cell13_naive_baseline_metrics_v1.csv",
        "size_bytes": 7195,
        "sha256": "08d79380c2c8c78110089fa7e79946117dd3c22d12438ad52b8d53421299c541",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell13_events"],
    },
    "cell13_bootstrap": {
        "producer": "CELL_13",
        "file": "cell13_block_bootstrap_ci_v1.csv",
        "size_bytes": 17172,
        "sha256": "4725180e69e64a43b71a082e8f0b85e9b4238f81b98d892468060b71d394ed44",
        "parity_mode": "BYTE_EXACT",
        "upstream": ["cell13_events", "cell13_metrics"],
    },
}

EXPECTED_AUDIT_CANONICALIZATION: dict[str, Any] = {
    "version": "MES_AUDIT_CANONICAL_JSON_1.0",
    "parity_mode": "CANONICAL_JSON",
    "remove_exact_keys": ["audit_written_utc", "manifest_written_utc"],
    "normalize_colab_artifact_root_to": "${MES_ARTIFACT_ROOT}",
    "never_remove": [
        "status",
        "failures",
        "counts",
        "policy_version",
        "sha256",
        "upstream_binding",
    ],
}

EXPECTED_MIGRATION_RULES: dict[str, Any] = {
    "reference_cells_are_importable": False,
    "new_runs_may_overwrite_frozen_evidence": False,
    "large_artifacts_in_ordinary_git": False,
    "final_test_features_before_model_protocol_freeze": False,
    "cell14_allowed_upstream_ids": [
        "cell5_bars_15m",
        "cell5_audit",
        "cell7_universe",
        "cell7_audit",
        "cell8_assignments",
        "cell8_audit",
    ],
    "cell14_forbidden_producers": ["CELL_9", "CELL_10", "CELL_11", "CELL_12", "CELL_13"],
}


class ManifestError(RuntimeError):
    pass


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def artifact_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        raise ManifestError("Frozen release manifest requires a non-empty artifact list")
    index: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ManifestError("Every artifact must be a mapping")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ManifestError("Every artifact requires a non-empty string id")
        if artifact_id in index:
            raise ManifestError(f"Duplicate artifact id: {artifact_id}")
        index[artifact_id] = artifact
    return index


def _check_expected(failures: list[str], label: str, actual: Any, expected: dict[str, Any]) -> None:
    if not isinstance(actual, dict):
        failures.append(f"{label} must be a mapping")
        return
    for key, value in expected.items():
        if actual.get(key) != value:
            failures.append(f"{label}.{key} differs from the frozen V1 contract")


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate the exact, immutable MES V1 migration release contract.

    This is intentionally stricter than a general JSON-schema check.  The
    expected values live in code so an empty or self-rewritten JSON manifest
    cannot declare itself valid.
    """

    failures: list[str] = []
    if manifest.get("manifest_version") != EXPECTED_MANIFEST_VERSION:
        failures.append("Unexpected frozen manifest version")
    if manifest.get("status") != EXPECTED_MANIFEST_STATUS:
        failures.append("Migration status must remain PROVISIONAL until large-artifact parity")

    _check_expected(failures, "notebook", manifest.get("notebook"), EXPECTED_NOTEBOOK)
    _check_expected(failures, "drive", manifest.get("drive"), EXPECTED_DRIVE)
    _check_expected(
        failures, "locked_contracts", manifest.get("locked_contracts"), EXPECTED_LOCKED_CONTRACTS
    )
    _check_expected(
        failures, "golden_counts", manifest.get("golden_counts"), EXPECTED_GOLDEN_COUNTS
    )
    _check_expected(
        failures,
        "audit_canonicalization",
        manifest.get("audit_canonicalization"),
        EXPECTED_AUDIT_CANONICALIZATION,
    )
    _check_expected(
        failures, "migration_rules", manifest.get("migration_rules"), EXPECTED_MIGRATION_RULES
    )

    try:
        artifacts = artifact_index(manifest)
    except ManifestError as exc:
        failures.append(str(exc))
        artifacts = {}

    actual_ids = set(artifacts)
    expected_ids = set(EXPECTED_ARTIFACTS)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        failures.append(f"Frozen artifact id set mismatch; missing={missing}, extra={extra}")

    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            continue
        _check_expected(failures, f"artifacts[{artifact_id}]", artifact, expected)
        digest = artifact.get("sha256")
        if not SHA256_RE.fullmatch(str(digest)):
            failures.append(f"{artifact_id}: invalid SHA256")
        upstreams = artifact.get("upstream")
        if not isinstance(upstreams, list):
            failures.append(f"{artifact_id}: upstream must be a list")
            continue
        for upstream in upstreams:
            if upstream not in artifacts:
                failures.append(f"{artifact_id}: unresolved upstream {upstream}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(artifact_id: str) -> None:
        if artifact_id in visited:
            return
        if artifact_id in visiting:
            failures.append(f"Artifact DAG contains a cycle at {artifact_id}")
            return
        visiting.add(artifact_id)
        for upstream in artifacts[artifact_id].get("upstream", []):
            if upstream in artifacts:
                visit(upstream)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in artifacts:
        visit(artifact_id)

    if failures:
        raise ManifestError("Manifest validation failed:\n- " + "\n- ".join(failures))

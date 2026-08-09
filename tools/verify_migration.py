from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mes_quant.core.manifest import (
    EXPECTED_MANIFEST_STATUS,
    SHA256_RE,
    artifact_index,
    load_manifest,
    validate_manifest,
)

CHECKSUM_LINE_RE = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9_.-]+)$")
EXPECTED_SOURCE_REFERENCE_VERSION = "COLAB_CELLS_0_13_V1"
EXPECTED_EVIDENCE_VERSION = "MES_V1_DRIVE_EVIDENCE_1.0"


class VerificationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_file(relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise VerificationError(f"{label} must be a non-empty relative path")
    relative_path = Path(relative)
    if relative_path.is_absolute():
        raise VerificationError(f"{label} must be relative to the repository")
    resolved = (PROJECT_ROOT / relative_path).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise VerificationError(f"{label} escapes the repository")
    if not resolved.is_file():
        raise VerificationError(f"Missing {label}: {relative}")
    return resolved


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"Cannot parse {label}: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must contain a JSON object")
    return value


def _require_equal(
    payload: dict[str, Any], path: tuple[str, ...], expected: Any, label: str
) -> None:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise VerificationError(f"{label} missing required field {'.'.join(path)}")
        value = value[key]
    if value != expected:
        raise VerificationError(
            f"{label} field {'.'.join(path)} differs: expected {expected!r}, found {value!r}"
        )


def _normalized_source(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def _parse_sha256s(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise VerificationError("Frozen SHA256SUMS.txt is empty")
    for number, line in enumerate(lines, start=1):
        match = CHECKSUM_LINE_RE.fullmatch(line)
        if match is None:
            raise VerificationError(f"Malformed SHA256SUMS.txt line {number}")
        digest, filename = match.groups()
        if filename in result:
            raise VerificationError(f"Duplicate SHA256SUMS entry: {filename}")
        result[filename] = digest
    return result


def verify_notebook_reference(manifest: dict[str, Any]) -> None:
    notebook_contract = manifest["notebook"]
    notebook_path = _project_file(notebook_contract["local_reference_file"], "notebook reference")
    source_manifest_path = _project_file(
        notebook_contract["cell_source_manifest"], "cell source manifest"
    )
    checksums_path = _project_file(notebook_contract["sha256s_file"], "SHA256SUMS file")

    if notebook_path.stat().st_size != notebook_contract["drive_size_bytes"]:
        raise VerificationError("Frozen notebook byte size differs from the Drive freeze")
    if sha256(notebook_path) != notebook_contract["local_reference_sha256"]:
        raise VerificationError("Frozen notebook SHA256 differs from the release contract")
    if sha256(source_manifest_path) != notebook_contract["cell_source_manifest_sha256"]:
        raise VerificationError(
            "Frozen cell source manifest SHA256 differs from the release contract"
        )
    if sha256(checksums_path) != notebook_contract["sha256s_sha256"]:
        raise VerificationError("Frozen SHA256SUMS file differs from the release contract")

    source_manifest = _load_json(source_manifest_path, "cell source manifest")
    _require_equal(
        source_manifest,
        ("reference_version",),
        EXPECTED_SOURCE_REFERENCE_VERSION,
        "cell source manifest",
    )
    _require_equal(source_manifest, ("notebook_file",), notebook_path.name, "cell source manifest")
    _require_equal(
        source_manifest,
        ("notebook_local_sha256",),
        notebook_contract["local_reference_sha256"],
        "cell source manifest",
    )
    _require_equal(source_manifest, ("cell_order",), list(range(14)), "cell source manifest")
    _require_equal(
        source_manifest, ("execution_counts",), list(range(37, 51)), "cell source manifest"
    )

    cells = source_manifest.get("cells")
    if not isinstance(cells, list) or len(cells) != 14:
        raise VerificationError("Cell source manifest must contain exactly 14 cells")

    expected_filenames = {notebook_path.name} | {f"cell{index:02d}.py" for index in range(14)}
    checksum_entries = _parse_sha256s(checksums_path)
    if set(checksum_entries) != expected_filenames:
        raise VerificationError("SHA256SUMS must contain exactly the notebook and Cells 00..13")

    notebook = _load_json(notebook_path, "frozen notebook")
    notebook_cells = notebook.get("cells")
    if not isinstance(notebook_cells, list) or len(notebook_cells) != 14:
        raise VerificationError("Frozen notebook must contain exactly 14 cells")
    if checksum_entries[notebook_path.name] != sha256(notebook_path):
        raise VerificationError("Notebook digest in SHA256SUMS does not match the frozen notebook")

    seen_cells: set[int] = set()
    for expected_index, (record, notebook_cell) in enumerate(
        zip(cells, notebook_cells, strict=True)
    ):
        if not isinstance(record, dict):
            raise VerificationError(f"Cell source record {expected_index} is not a mapping")
        expected_filename = f"cell{expected_index:02d}.py"
        if record.get("cell") != expected_index or record.get("source_file") != expected_filename:
            raise VerificationError(f"Cell source record {expected_index} has wrong identity/order")
        if record.get("execution_count") != 37 + expected_index:
            raise VerificationError(
                f"Cell {expected_index} execution count differs from the freeze"
            )
        digest = record.get("normalized_source_sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise VerificationError(f"Cell {expected_index} source digest is malformed")
        if expected_index in seen_cells:
            raise VerificationError(f"Duplicate frozen cell record: {expected_index}")
        seen_cells.add(expected_index)

        source_path = source_manifest_path.parent / expected_filename
        if not source_path.is_file() or sha256(source_path) != digest:
            raise VerificationError(f"Frozen source changed: {expected_filename}")
        if checksum_entries[expected_filename] != digest:
            raise VerificationError(f"SHA256SUMS disagrees for {expected_filename}")
        if notebook_cell.get("cell_type") != "code":
            raise VerificationError(f"Notebook cell {expected_index} is not a code cell")
        if notebook_cell.get("execution_count") != 37 + expected_index:
            raise VerificationError(f"Notebook cell {expected_index} execution count differs")
        notebook_source = _normalized_source("".join(notebook_cell.get("source", [])))
        notebook_source_digest = hashlib.sha256(notebook_source.encode("utf-8")).hexdigest()
        if notebook_source_digest != digest:
            raise VerificationError(f"Notebook/source snapshot mismatch for Cell {expected_index}")

    notebook_text = notebook_path.read_text(encoding="utf-8")
    if "jupyter_client/session.py:203" in notebook_text:
        raise VerificationError("Historical warning flood found in frozen notebook")
    cell9 = (source_manifest_path.parent / "cell09.py").read_text(encoding="utf-8")
    if cell9.count("# CELL 9 — RESEARCH COST MODEL CONTRACT") != 1:
        raise VerificationError("Cell 9 header count is not one")
    if cell9.count("scenarios.to_csv(") != 1:
        raise VerificationError("Cell 9 writes scenarios more than once")


AUDIT_EXPECTATIONS: dict[str, list[tuple[tuple[str, ...], Any]]] = {
    "cell2_raw_integrity_audit.json": [
        (("policy_version",), "MES_V1_RAW_INTEGRITY_1.1"),
        (("decoded", "rows"), 2551123),
        (
            ("decoded", "content_sha256"),
            "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584",
        ),
        (("raw_file", "size_bytes"), 40078487),
        (
            ("raw_file", "sha256"),
            "49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0",
        ),
    ],
    "cell7_decision_universe_audit.json": [
        (("policy_version",), "MES_V1_DECISION_UNIVERSE_1.0"),
        (("counts", "input_15m_rows"), 170586),
        (("counts", "clock_candidate_rows"), 40621),
        (("counts", "eligible_decision_rows"), 39847),
        (("counts", "excluded_clock_candidate_rows"), 774),
        (("counts", "eligible_sessions"), 1820),
        (("counts", "partial_clock_candidate_rows"), 47),
        (("counts", "eligible_partial_rows"), 0),
        (
            ("sha256", "input_mes_15m_sha256"),
            "558723ed6965c23fb93a7abc61d65eee405dd9eb5f41a36a96c7b66bbc806dad",
        ),
        (
            ("sha256", "cell4_audit_sha256"),
            "17dec58345f7b92fd7628ac48a80eaeff9558b78ed5ceb60b2148eb18fb367db",
        ),
        (
            ("sha256", "cell5_audit_sha256"),
            "0fd7aba3cca2f3ae88d24b048708517e4829302275ab25f90821ef2af2621c73",
        ),
        (
            ("sha256", "cell6_audit_sha256"),
            "24d580e189feaf9e6f6ca6750dcf5a358ff551920f4dc3dda02892b87c3ec2b0",
        ),
        (
            ("sha256", "decision_universe_sha256"),
            "f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7",
        ),
    ],
    "cell8_purged_split_audit.json": [
        (("policy_version",), "MES_V1_PURGED_SPLIT_1.0"),
        (
            ("upstream_binding", "cell7_universe_sha256"),
            "f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7",
        ),
        (("split_contract", "final_test_is_untouched"), True),
        (("split_contract", "economic_label_created"), False),
        (("counts", "decision_rows"), 39847),
        (("counts", "outer_train_rows"), 25685),
        (("counts", "outer_validation_rows"), 5508),
        (("counts", "final_test_rows"), 8654),
        (("counts", "purged_before_final_test_rows"), 0),
        (("counts", "walk_forward_folds"), 3),
        (("counts", "total_fold_purged_rows"), 0),
        (("counts", "boundary_overlap_rows_after_purge"), 0),
        (
            ("sha256", "split_assignments_sha256"),
            "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        ),
    ],
    "cell9_cost_model_audit.json": [
        (("policy_version",), "MES_V1_COST_MODEL_1.0"),
        (
            ("upstream_binding", "cell8_assignments_sha256"),
            "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        ),
        (("upstream_binding", "final_test_outcomes_inspected"), False),
        (("research_safety", "final_test_outcomes_inspected"), False),
        (("scenario_count",), 4),
        (
            ("sha256", "cost_parameters_sha256"),
            "24d1953df9c497d991d3b6eb7a9c053046d0c7dbd2a006f4c4c03fbd02aab4f9",
        ),
        (
            ("sha256", "cost_scenarios_sha256"),
            "2248d59ff32361dff9c5df94bfdf8d7ad6942ee50ef3d6e1c6a3731779aeff4f",
        ),
    ],
    "cell10_economic_label_audit.json": [
        (("policy_version",), "MES_V1_ECONOMIC_LABELS_1.0"),
        (
            ("upstream_binding", "mes_15m_sha256"),
            "558723ed6965c23fb93a7abc61d65eee405dd9eb5f41a36a96c7b66bbc806dad",
        ),
        (
            ("upstream_binding", "cell8_assignments_sha256"),
            "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        ),
        (
            ("upstream_binding", "cell9_cost_scenarios_sha256"),
            "2248d59ff32361dff9c5df94bfdf8d7ad6942ee50ef3d6e1c6a3731779aeff4f",
        ),
        (("counts", "decision_rows"), 39847),
        (("counts", "development_rows"), 31193),
        (("counts", "train_rows"), 25685),
        (("counts", "validation_rows"), 5508),
        (("counts", "final_test_rows_sealed"), 8654),
        (("counts", "usable_development_labels"), 31165),
        (("counts", "primary_label_counts_development_only", "LONG"), 15188),
        (("counts", "primary_label_counts_development_only", "SHORT"), 13147),
        (("counts", "primary_label_counts_development_only", "NO_TRADE"), 2830),
        (("point_in_time_safety", "final_test_price_lookup_performed"), False),
        (("point_in_time_safety", "final_test_outcomes_computed"), False),
        (("point_in_time_safety", "final_test_label_distribution_inspected"), False),
        (
            ("sha256", "economic_labels_sha256"),
            "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0",
        ),
    ],
    "cell11_cost_temporality_audit.json": [
        (("policy_version",), "MES_V1_COST_TEMPORALITY_1.0"),
        (
            ("upstream_binding", "cell9_scenarios_sha256"),
            "2248d59ff32361dff9c5df94bfdf8d7ad6942ee50ef3d6e1c6a3731779aeff4f",
        ),
        (("semantic_contract", "historical_actual_labels_available"), False),
        (("semantic_contract", "historical_labels_allowed"), False),
        (
            ("sha256", "input_cell9_parameters_sha256"),
            "24d1953df9c497d991d3b6eb7a9c053046d0c7dbd2a006f4c4c03fbd02aab4f9",
        ),
        (
            ("sha256", "semantic_scenarios_sha256"),
            "7b3c619f1a8c4612d9a6b3df40f86136030baae616c4b0cd160e1651c2db0302",
        ),
        (
            ("sha256", "fee_vintage_registry_sha256"),
            "47a1d87591fb0502f939d89718ee1c52fc21276461a8103841af98f0d61167e1",
        ),
    ],
    "cell12_path_outcomes_audit.json": [
        (("policy_version",), "MES_V1_DEVELOPMENT_PATH_OUTCOMES_1.0"),
        (
            ("upstream_binding", "cell10_labels_sha256"),
            "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0",
        ),
        (
            ("upstream_binding", "cell2_raw_file_sha256"),
            "49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0",
        ),
        (
            ("upstream_binding", "mes_1m_memory_sha256"),
            "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584",
        ),
        (("counts", "usable_development_paths"), 31165),
        (("counts", "final_test_rows_sealed"), 8654),
        (("counts", "final_test_price_lookup_count"), 0),
        (
            ("sha256", "path_outcomes_sha256"),
            "8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941",
        ),
    ],
    "cell13_development_baseline_audit.json": [
        (("policy_version",), "MES_V1_DEPENDENCE_BASELINES_1.0"),
        (
            ("upstream_binding", "cell8_assignments_sha256"),
            "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        ),
        (
            ("upstream_binding", "cell10_labels_sha256"),
            "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0",
        ),
        (
            ("upstream_binding", "cell11_semantic_costs_sha256"),
            "7b3c619f1a8c4612d9a6b3df40f86136030baae616c4b0cd160e1651c2db0302",
        ),
        (
            ("upstream_binding", "cell12_path_outcomes_sha256"),
            "8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941",
        ),
        (("evaluation_contract", "action_space"), "LONG_FLAT"),
        (("evaluation_contract", "position_policy"), "NON_OVERLAPPING_60M"),
        (("evaluation_contract", "final_test_used"), False),
        (("dependence_contract", "primary_block_length_sessions"), 5),
        (("dependence_contract", "bootstrap_repetitions"), 2000),
        (("dependence_contract", "master_seed"), 20260809),
        (("counts", "unique_oof_validation_decisions"), 16494),
        (("counts", "baseline_event_rows"), 65976),
        (("counts", "strategies"), 4),
        (("counts", "canonical_validation_sessions_by_fold", "WF_2022"), 251),
        (("counts", "canonical_validation_sessions_by_fold", "WF_2023"), 250),
        (("counts", "canonical_validation_sessions_by_fold", "WF_2024"), 252),
        (("counts", "final_test_rows_used"), 0),
        (("modeling_gate", "model_fitted"), False),
        (
            ("sha256", "baseline_events_sha256"),
            "a745ad7dd8f39f9c4b90cafedb8ab6cd8242c0991c177698e86dbfad68bc7df4",
        ),
        (
            ("sha256", "dependence_audit_sha256"),
            "113412d42ac08bd87c18cec014924252f9e53a0762fa061ca887598681344ded",
        ),
        (
            ("sha256", "baseline_metrics_sha256"),
            "08d79380c2c8c78110089fa7e79946117dd3c22d12438ad52b8d53421299c541",
        ),
        (
            ("sha256", "block_bootstrap_ci_sha256"),
            "4725180e69e64a43b71a082e8f0b85e9b4238f81b98d892468060b71d394ed44",
        ),
    ],
}


def verify_drive_evidence(manifest: dict[str, Any]) -> None:
    drive_contract = manifest["drive"]
    evidence_manifest_path = _project_file(
        drive_contract["small_evidence_manifest"], "Drive evidence manifest"
    )
    if (
        evidence_manifest_path.stat().st_size
        != drive_contract["small_evidence_manifest_size_bytes"]
    ):
        raise VerificationError("Drive evidence manifest size differs from the release contract")
    if sha256(evidence_manifest_path) != drive_contract["small_evidence_manifest_sha256"]:
        raise VerificationError("Drive evidence manifest SHA256 differs from the release contract")

    evidence = _load_json(evidence_manifest_path, "Drive evidence manifest")
    _require_equal(
        evidence, ("manifest_version",), EXPECTED_EVIDENCE_VERSION, "Drive evidence manifest"
    )
    _require_equal(
        evidence,
        ("drive_folder_id",),
        drive_contract["artifact_folder_id"],
        "Drive evidence manifest",
    )
    _require_equal(
        evidence,
        ("file_count",),
        drive_contract["small_evidence_file_count"],
        "Drive evidence manifest",
    )
    records = evidence.get("files")
    if not isinstance(records, list) or len(records) != drive_contract["small_evidence_file_count"]:
        raise VerificationError("Drive evidence manifest file list/count mismatch")

    expected_names: set[str] = set()
    by_filename: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise VerificationError("Every Drive evidence record must be a mapping")
        filename = record.get("file")
        digest = record.get("sha256")
        size = record.get("size_bytes")
        if not isinstance(filename, str) or filename != Path(filename).name or not filename:
            raise VerificationError(f"Unsafe Drive evidence filename: {filename!r}")
        if filename in expected_names:
            raise VerificationError(f"Duplicate Drive evidence filename: {filename}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise VerificationError(f"Malformed Drive evidence digest: {filename}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise VerificationError(f"Malformed Drive evidence size: {filename}")
        expected_names.add(filename)
        by_filename[filename] = record

    evidence_dir = evidence_manifest_path.parent
    actual_names = {entry.name for entry in evidence_dir.iterdir()}
    expected_directory_names = expected_names | {evidence_manifest_path.name}
    if actual_names != expected_directory_names:
        missing = sorted(expected_directory_names - actual_names)
        extra = sorted(actual_names - expected_directory_names)
        raise VerificationError(
            f"Drive evidence directory mismatch; missing={missing}, extra={extra}"
        )

    for filename, record in by_filename.items():
        path = evidence_dir / filename
        if not path.is_file():
            raise VerificationError(f"Missing Drive evidence file: {filename}")
        if path.stat().st_size != record["size_bytes"]:
            raise VerificationError(f"Drive evidence size mismatch: {filename}")
        if sha256(path) != record["sha256"]:
            raise VerificationError(f"Drive evidence SHA256 mismatch: {filename}")

    # Bind any small evidence that is also a release artifact back to the
    # artifact DAG; a separate correct hash in each manifest is not sufficient.
    artifacts = artifact_index(manifest)
    for artifact_id, artifact in artifacts.items():
        filename = artifact.get("file")
        if filename not in by_filename:
            continue
        evidence_record = by_filename[filename]
        if artifact.get("sha256") != evidence_record["sha256"]:
            raise VerificationError(f"Release/evidence hash disagreement for {artifact_id}")
        if artifact.get("size_bytes") != evidence_record["size_bytes"]:
            raise VerificationError(f"Release/evidence size disagreement for {artifact_id}")

    for filename, expectations in AUDIT_EXPECTATIONS.items():
        if filename not in by_filename:
            raise VerificationError(f"Required frozen audit is absent: {filename}")
        payload = _load_json(evidence_dir / filename, filename)
        _require_equal(payload, ("status",), "PASS", filename)
        _require_equal(payload, ("failures",), [], filename)
        for field_path, expected in expectations:
            _require_equal(payload, field_path, expected, filename)


def verify_local_artifact_root(manifest: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    """Verify every known release artifact present and require all Cell 14 inputs.

    Absence of later Cells 9--13 artifacts is not an error: this gate proves
    local input parity for Cell 14, not full pipeline regeneration parity.
    """

    root = artifact_root.expanduser().resolve()
    if not root.is_dir():
        raise VerificationError(f"Artifact root is not a directory: {artifact_root}")

    artifacts = artifact_index(manifest)
    required_ids = manifest["migration_rules"]["cell14_allowed_upstream_ids"]
    if not isinstance(required_ids, list) or not required_ids:
        raise VerificationError("Cell 14 required input list is empty or malformed")

    verified_ids: list[str] = []
    verified_paths: dict[str, Path] = {}
    for artifact_id, artifact in artifacts.items():
        filename = artifact.get("file")
        if not isinstance(filename, str):
            continue
        if filename != Path(filename).name:
            raise VerificationError(f"Unsafe release artifact filename: {artifact_id}")
        path = root / filename
        if not path.exists():
            continue
        if not path.is_file():
            raise VerificationError(f"Local artifact is not a file: {filename}")
        expected_size = artifact.get("size_bytes")
        expected_digest = artifact.get("sha256")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool):
            raise VerificationError(f"No frozen byte size for local artifact {artifact_id}")
        if not isinstance(expected_digest, str) or not SHA256_RE.fullmatch(expected_digest):
            raise VerificationError(f"No frozen SHA256 for local artifact {artifact_id}")
        if path.stat().st_size != expected_size:
            raise VerificationError(f"Local artifact size mismatch: {filename}")
        if sha256(path) != expected_digest:
            raise VerificationError(f"Local artifact SHA256 mismatch: {filename}")
        verified_ids.append(artifact_id)
        verified_paths[artifact_id] = path

    missing_required = [
        artifact_id for artifact_id in required_ids if artifact_id not in verified_paths
    ]
    if missing_required:
        missing_files = [artifacts[artifact_id].get("file") for artifact_id in missing_required]
        raise VerificationError(
            "Artifact root is missing required Cell 14 inputs: "
            + ", ".join(
                f"{item_id} ({filename})"
                for item_id, filename in zip(missing_required, missing_files, strict=True)
            )
        )

    return {
        "artifact_root": str(root),
        "required_cell14_ids": list(required_ids),
        "verified_manifest_artifact_ids": verified_ids,
    }


def verify_all(
    artifact_root: Path | None = None, manifest_path: Path | None = None
) -> dict[str, Any] | None:
    if manifest_path is None:
        manifest_path = PROJECT_ROOT / "manifests" / "releases" / "frozen_colab_manifest_v1.json"
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    if manifest["status"] != EXPECTED_MANIFEST_STATUS:
        raise VerificationError(
            "Migration status may not be promoted without large-artifact parity"
        )
    verify_notebook_reference(manifest)
    verify_drive_evidence(manifest)
    if artifact_root is not None:
        return verify_local_artifact_root(manifest, artifact_root)
    return None


def print_verification_report(local_result: dict[str, Any] | None) -> None:
    print("PASS: frozen release manifest is bound to independent V1 constants")
    print("PASS: notebook, Cell 00..13 sources, source manifest, and SHA256SUMS are byte-verified")
    print("PASS: all 36 local Drive evidence files match their frozen SHA256 and size")
    print(
        "PASS: required audit policies, golden counts, upstream hashes, and final-test seals match"
    )
    if local_result is None:
        print("PROVISIONAL: local Cell 14 input parity was not requested; pass --artifact-root")
    else:
        required_count = len(local_result["required_cell14_ids"])
        verified_count = len(local_result["verified_manifest_artifact_ids"])
        print(
            "LOCAL LARGE INPUT PARITY PASS: "
            f"{required_count}/{required_count} required Cell 14 inputs and "
            f"{verified_count} present manifest artifacts are byte-exact"
        )
    print("OPEN: full Cell 14 regeneration/output parity has not yet been established")
    print("PROVISIONAL: the frozen migration release status remains unchanged")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the frozen MES V1 migration evidence")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "manifests" / "releases" / "frozen_colab_manifest_v1.json",
        help="frozen release manifest to verify",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="optional local folder containing exact release artifacts, including all six Cell 14 inputs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    local_result = verify_all(artifact_root=args.artifact_root, manifest_path=args.manifest)
    print_verification_report(local_result)


if __name__ == "__main__":
    main()

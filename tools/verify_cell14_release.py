from __future__ import annotations

import copy
import filecmp
import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST_PATH = PROJECT_ROOT / "manifests" / "releases" / "cell14_local_release_v1.json"
EXPECTED_RELEASE_MANIFEST_SHA256 = (
    "74bd9d009cca43368488eea245b7b3b64918edc354091ba82172aaab6803a197"
)
EXPECTED_RELEASE_MANIFEST_SIZE = 7036

CANONICAL_RUN_ID = "cell14_20260809T175203Z"
REPLAY_RUN_ID = "cell14_20260809T175217Z"

EXPECTED_STATUS = {
    "computation": "LOCKED",
    "development_data_artifact": "LOCKED",
    "deterministic_replay": "LOCKED",
    "candidate_feature_catalog": "PROVISIONAL",
    "model_transforms": "OPEN",
    "final_test_features": "SEALED_ZERO_ROWS",
}

EXPECTED_CONTROLS = {
    "frozen_colab_manifest": {
        "file": "manifests/releases/frozen_colab_manifest_v1.json",
        "sha256": "6f174e27ef6ccff9ce53d233469a47b0b1d12cb1c3fd23c263585935cc6eb15f",
    },
    "feature_config": {
        "file": "configs/v1/features_v1.json",
        "sha256": "ff1c1033a3b645a98e967441dd2fef01968ab8d33ce76d07415e3d8e1ecc480c",
    },
    "feature_contract_source": {
        "file": "src/mes_quant/features/contract.py",
        "sha256": "23b89e78a3658d5cf8809a7ca78cf99071efef66fadb0ce92c301cc57c07f05e",
    },
    "feature_builder_source": {
        "file": "src/mes_quant/features/builder.py",
        "sha256": "1971dcffb580aadac8292cf482b00608d2778f8b06e40cadc1fef149cb9976cc",
    },
    "feature_pipeline_source": {
        "file": "src/mes_quant/pipelines/feature_pipeline.py",
        "sha256": "71a377b758df8a8aeea5cd5b7914a602c864f65d9a57eeccde02a160566d38d1",
    },
}

EXPECTED_UPSTREAM_INPUTS = {
    "cell5_bars_15m": {
        "file": "artifacts/cache/source_v1/MES_2019_2026_15m_clean.parquet",
        "size_bytes": 6904346,
        "sha256": "558723ed6965c23fb93a7abc61d65eee405dd9eb5f41a36a96c7b66bbc806dad",
    },
    "cell5_audit": {
        "file": "artifacts/cache/source_v1/cell5_15m_resample_audit.json",
        "size_bytes": 1795,
        "sha256": "0fd7aba3cca2f3ae88d24b048708517e4829302275ab25f90821ef2af2621c73",
    },
    "cell7_universe": {
        "file": "artifacts/cache/source_v1/cell7_decision_universe_v1.parquet",
        "size_bytes": 1529761,
        "sha256": "f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7",
    },
    "cell7_audit": {
        "file": "artifacts/cache/source_v1/cell7_decision_universe_audit.json",
        "size_bytes": 3047,
        "sha256": "3e5f76d3ea3c91fe37bfb7f58235dc4c616da88b299a1d370a8a3c67653abf7e",
    },
    "cell8_assignments": {
        "file": "artifacts/cache/source_v1/cell8_purged_split_assignments_v1.parquet",
        "size_bytes": 1447931,
        "sha256": "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
    },
    "cell8_audit": {
        "file": "artifacts/cache/source_v1/cell8_purged_split_audit.json",
        "size_bytes": 6158,
        "sha256": "add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a",
    },
}

EXPECTED_POLICY = {
    "policy_version": "MES_V1_FEATURES_1.0",
    "input_cells": [5, 7, 8],
    "forbidden_input_cells": [9, 10, 11, 12, 13],
    "development_partitions": ["TRAIN", "VALIDATION"],
    "final_test_start_year": 2025,
    "target_cost_path_artifacts_opened": 0,
    "bar_minutes": 15,
    "maximum_rolling_lookback_bars": 16,
    "session_vwap_max_bars": 22,
    "exact_grid_required": True,
    "same_instrument_required": True,
    "imputation_allowed": False,
    "output_scaled": False,
}

EXPECTED_COUNTS = {
    "development_rows": 31193,
    "feature_columns": 29,
    "output_columns": 41,
    "feature_usable_rows": 30197,
    "feature_unusable_rows": 996,
    "final_test_feature_rows": 0,
    "market_rows_after_development_max_returned": 0,
    "session_vwap_max_bars_observed": 22,
    "missing_feature_values": 5703,
    "missingness_ledger_rows": 5703,
    "status_counts": {
        "PASS": 30197,
        "PARTIAL_LOOKBACK_BAR": 908,
        "PARTIAL_LOOKBACK_BAR|SESSION_VWAP_INPUT_INVALID": 50,
        "MISSING_LOOKBACK_BAR|SESSION_VWAP_INPUT_INVALID": 20,
        "SESSION_VWAP_INPUT_INVALID": 13,
        "MISSING_LOOKBACK_BAR": 5,
    },
}

COMMON_RUN_ARTIFACTS = {
    "features": {
        "filename": "cell14_development_point_in_time_features_v1.parquet",
        "size_bytes": 6194740,
        "sha256": "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452",
        "content_sha256": "dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d",
    },
    "registry": {
        "filename": "cell14_feature_registry_v1.csv",
        "size_bytes": 16998,
        "sha256": "7df68538d3e4a1447f1bca01396e3e141389decd196ba32faf04e34913107d95",
    },
    "status_summary": {
        "filename": "cell14_feature_status_summary_v1.csv",
        "size_bytes": 265,
        "sha256": "fbbe4574e74d80675b60e0e9f3131168fb48383ff0214a30fba8d3910aef5155",
    },
    "missingness_ledger": {
        "filename": "cell14_feature_missingness_ledger_v1.csv",
        "size_bytes": 464921,
        "sha256": "edd3c8269a62b4b2806bfb0ebe6aeb1a71e40e0306637d696a6d1a2298fbf461",
    },
}

AUDIT_RECORDS = {
    "canonical": {
        "run_id": CANONICAL_RUN_ID,
        "size_bytes": 8213,
        "sha256": "2adca2642c423ff634cb99de50f8fb5d0fc5f49d70188213021b9ee006ffdcd3",
    },
    "replay": {
        "run_id": REPLAY_RUN_ID,
        "size_bytes": 8213,
        "sha256": "687c308f920b96ffc3608741b1c22e12055fcb003db490f86267ad9ee01a7392",
    },
}

EXPECTED_DETERMINISM = {
    "byte_identical_artifact_ids": [
        "features",
        "registry",
        "status_summary",
        "missingness_ledger",
    ],
    "audit_excluded_reason": "run timestamp and absolute run path are expected to differ",
    "result": "PASS",
}

EXPECTED_FEATURE_CONTRACT = {
    "input_cells": [5, 7, 8],
    "forbidden_input_cells": [9, 10, 11, 12, 13],
    "target_cost_path_artifacts_opened": 0,
    "feature_partitions": ["TRAIN", "VALIDATION"],
    "final_test_feature_rows": 0,
    "maximum_rolling_lookback_bars": 16,
    "session_vwap_max_bars": 22,
    "bar_minutes": 15,
    "exact_grid_required": True,
    "same_instrument_required": True,
    "imputation_allowed": False,
    "output_scaled": False,
    "current_completed_bar_allowed": True,
    "live_fill_at_bar_close_guaranteed": False,
}

EXPECTED_TRUSTED_CONFIG = {
    "policy_version": "MES_V1_FEATURES_1.0",
    "bar_minutes": 15,
    "maximum_lookback_bars": 16,
    "session_vwap_max_bars": 22,
    "expected_development_rows": 31193,
    "development_partitions": ["TRAIN", "VALIDATION"],
    "final_test_start_year": 2025,
    "required_active_1m_count": 15,
    "decision_slot_count": 22,
    "session_timezone": "America/New_York",
    "test_only_allow_noncanonical_row_count": False,
}

EXPECTED_UPSTREAM_BINDING = {
    "manifest_version": "MES_V1_FROZEN_COLAB_1.0",
    "manifest_status": "PROVISIONAL_FULL_PARITY_PENDING_LOCAL_LARGE_ARTIFACTS",
    "manifest_file_sha256": EXPECTED_CONTROLS["frozen_colab_manifest"]["sha256"],
    "config_file_sha256": EXPECTED_CONTROLS["feature_config"]["sha256"],
    "cell5_bars_sha256": EXPECTED_UPSTREAM_INPUTS["cell5_bars_15m"]["sha256"],
    "cell5_audit_sha256": EXPECTED_UPSTREAM_INPUTS["cell5_audit"]["sha256"],
    "cell7_universe_sha256": EXPECTED_UPSTREAM_INPUTS["cell7_universe"]["sha256"],
    "cell7_audit_sha256": EXPECTED_UPSTREAM_INPUTS["cell7_audit"]["sha256"],
    "cell8_assignments_sha256": EXPECTED_UPSTREAM_INPUTS["cell8_assignments"]["sha256"],
    "cell8_audit_sha256": EXPECTED_UPSTREAM_INPUTS["cell8_audit"]["sha256"],
}

EXPECTED_CONTROL_HASHES = {
    "config_file_sha256": EXPECTED_CONTROLS["feature_config"]["sha256"],
    "manifest_file_sha256": EXPECTED_CONTROLS["frozen_colab_manifest"]["sha256"],
    "feature_contract_source_sha256": EXPECTED_CONTROLS["feature_contract_source"]["sha256"],
    "feature_builder_source_sha256": EXPECTED_CONTROLS["feature_builder_source"]["sha256"],
    "feature_pipeline_source_sha256": EXPECTED_CONTROLS["feature_pipeline_source"]["sha256"],
}

TRUSTED_INPUT_IDS = [
    "cell5_audit",
    "cell5_bars_15m",
    "cell7_audit",
    "cell7_universe",
    "cell8_assignments",
    "cell8_audit",
]
FORBIDDEN_ARTIFACT_IDS = [
    "cell10_labels",
    "cell11_fee_vintages",
    "cell11_semantic_costs",
    "cell12_paths",
    "cell13_bootstrap",
    "cell13_dependence",
    "cell13_events",
    "cell13_metrics",
    "cell9_parameters",
    "cell9_scenarios",
]
EXPECTED_ARTIFACT_ACCESS = {
    "trusted_input_allowlist": TRUSTED_INPUT_IDS,
    "byte_verified_artifact_ids": TRUSTED_INPUT_IDS,
    "parsed_artifact_ids": TRUSTED_INPUT_IDS,
    "actual_opened_artifact_ids": TRUSTED_INPUT_IDS,
    "forbidden_manifest_artifact_ids": FORBIDDEN_ARTIFACT_IDS,
    "forbidden_opened_artifact_ids": [],
    "forbidden_opened_artifact_count": 0,
}

EXPECTED_PHYSICAL_READS = {
    "cell8_assignments": {
        "physical_filter": {"outer_partition_in": ["TRAIN", "VALIDATION"]},
        "rows": 31193,
        "decision_time_min_utc": "2019-05-06T13:45:00+00:00",
        "decision_time_max_utc": "2024-12-31T20:00:00+00:00",
        "partitions": ["TRAIN", "VALIDATION"],
    },
    "cell7_universe": {
        "physical_filter": {
            "decision_time_gte_utc": "2019-05-06T13:45:00+00:00",
            "decision_time_lte_utc": "2024-12-31T20:00:00+00:00",
        },
        "rows": 31193,
        "decision_time_min_utc": "2019-05-06T13:45:00+00:00",
        "decision_time_max_utc": "2024-12-31T20:00:00+00:00",
    },
    "cell5_bars_15m": {
        "physical_filter": {
            "decision_time_gte_utc": "2019-05-06T08:15:00+00:00",
            "decision_time_lte_utc": "2024-12-31T20:00:00+00:00",
            "conservative_lookback_bars": 22,
            "conservative_lookback_minutes": 330,
        },
        "rows": 133251,
        "decision_time_min_utc": "2019-05-06T08:15:00+00:00",
        "decision_time_max_utc": "2024-12-31T20:00:00+00:00",
        "rows_at_or_after_final_test_boundary": 0,
    },
}

EXPECTED_AUDIT_COUNTS = {
    "policy_version": "MES_V1_FEATURES_1.0",
    "development_rows": 31193,
    "feature_columns": 29,
    "feature_usable_rows": 30197,
    "feature_unusable_rows": 996,
    "final_test_feature_rows": 0,
    "market_rows_after_development_max_returned": 0,
    "session_vwap_max_bars_observed": 22,
    "missing_feature_values": 5703,
    "missingness_ledger_rows": 5703,
    "maximum_source_time_lte_decision_time": True,
    "status_counts": EXPECTED_COUNTS["status_counts"],
}

EXPECTED_OUTPUT_HASHES = {
    "features_file_sha256": COMMON_RUN_ARTIFACTS["features"]["sha256"],
    "features_content_sha256": COMMON_RUN_ARTIFACTS["features"]["content_sha256"],
    "registry_sha256": COMMON_RUN_ARTIFACTS["registry"]["sha256"],
    "status_summary_sha256": COMMON_RUN_ARTIFACTS["status_summary"]["sha256"],
    "missingness_ledger_sha256": COMMON_RUN_ARTIFACTS["missingness_ledger"]["sha256"],
}

EXPECTED_UPSTREAM_AUDIT_STATUS = {
    "cell5_failures": [],
    "cell5_policy_version": None,
    "cell7_status": "PASS",
    "cell7_policy_version": "MES_V1_DECISION_UNIVERSE_1.0",
    "cell8_status": "PASS",
    "cell8_policy_version": "MES_V1_PURGED_SPLIT_1.0",
}

METADATA_COLUMNS = [
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "role_wf_2024",
    "feature_row_usable",
    "feature_status",
    "feature_lookback_start_utc",
    "feature_max_source_time_utc",
]


class Cell14ReleaseError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Cell14ReleaseError(f"Cannot parse JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Cell14ReleaseError(f"Expected a JSON object: {path}")
    return value


def _project_file(relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise Cell14ReleaseError(f"{label} requires a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise Cell14ReleaseError(f"{label} path must be repository-relative")
    resolved = (PROJECT_ROOT / candidate).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise Cell14ReleaseError(f"{label} path escapes the repository")
    if not resolved.is_file():
        raise Cell14ReleaseError(f"Missing {label}: {relative}")
    return resolved


def _expect(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise Cell14ReleaseError(f"{label} differs from the immutable Cell 14 V1 release")


def _expected_run(run_id: str, audit_size: int, audit_hash: str) -> dict[str, Any]:
    artifacts: dict[str, dict[str, Any]] = {}
    for artifact_id, common in COMMON_RUN_ARTIFACTS.items():
        record = {
            "file": f"artifacts/runs/{run_id}/{common['filename']}",
            "size_bytes": common["size_bytes"],
            "sha256": common["sha256"],
        }
        if artifact_id == "features":
            record["content_sha256"] = common["content_sha256"]
        artifacts[artifact_id] = record
    artifacts["audit"] = {
        "file": f"artifacts/runs/{run_id}/cell14_feature_audit.json",
        "size_bytes": audit_size,
        "sha256": audit_hash,
    }
    return {"run_id": run_id, "artifacts": artifacts}


EXPECTED_RUNS = {
    role: _expected_run(record["run_id"], record["size_bytes"], record["sha256"])
    for role, record in AUDIT_RECORDS.items()
}


def validate_release_manifest(manifest: dict[str, Any]) -> None:
    expected_top_level = {
        "manifest_version",
        "created_for_release_date",
        "status",
        "canonical_run_id",
        "replay_run_id",
        "controls",
        "upstream_inputs",
        "policy",
        "golden_counts",
        "runs",
        "deterministic_replay",
    }
    _expect("release top-level fields", set(manifest), expected_top_level)
    _expect("manifest_version", manifest.get("manifest_version"), "MES_V1_CELL14_LOCAL_RELEASE_1.0")
    _expect("created_for_release_date", manifest.get("created_for_release_date"), "2026-08-10")
    _expect("status", manifest.get("status"), EXPECTED_STATUS)
    _expect("canonical_run_id", manifest.get("canonical_run_id"), CANONICAL_RUN_ID)
    _expect("replay_run_id", manifest.get("replay_run_id"), REPLAY_RUN_ID)
    _expect("controls", manifest.get("controls"), EXPECTED_CONTROLS)
    _expect("upstream_inputs", manifest.get("upstream_inputs"), EXPECTED_UPSTREAM_INPUTS)
    _expect("policy", manifest.get("policy"), EXPECTED_POLICY)
    _expect("golden_counts", manifest.get("golden_counts"), EXPECTED_COUNTS)
    _expect("runs", manifest.get("runs"), EXPECTED_RUNS)
    _expect("deterministic_replay", manifest.get("deterministic_replay"), EXPECTED_DETERMINISM)


def verify_control_and_upstream_bytes(manifest: dict[str, Any]) -> None:
    for control_id, record in manifest["controls"].items():
        path = _project_file(record["file"], f"control {control_id}")
        if sha256(path) != record["sha256"]:
            raise Cell14ReleaseError(f"Control SHA256 mismatch: {control_id}")
    for artifact_id, record in manifest["upstream_inputs"].items():
        path = _project_file(record["file"], f"upstream input {artifact_id}")
        if path.stat().st_size != record["size_bytes"]:
            raise Cell14ReleaseError(f"Upstream size mismatch: {artifact_id}")
        if sha256(path) != record["sha256"]:
            raise Cell14ReleaseError(f"Upstream SHA256 mismatch: {artifact_id}")


def verify_run_bytes(manifest: dict[str, Any]) -> dict[str, dict[str, Path]]:
    paths: dict[str, dict[str, Path]] = {}
    expected_filenames = {record["filename"] for record in COMMON_RUN_ARTIFACTS.values()} | {
        "cell14_feature_audit.json"
    }
    for role, run in manifest["runs"].items():
        run_paths: dict[str, Path] = {}
        for artifact_id, record in run["artifacts"].items():
            path = _project_file(record["file"], f"{role} {artifact_id}")
            if path.parent.name != run["run_id"]:
                raise Cell14ReleaseError(f"{role} {artifact_id} is outside its frozen run")
            if path.stat().st_size != record["size_bytes"]:
                raise Cell14ReleaseError(f"{role} {artifact_id} size mismatch")
            if sha256(path) != record["sha256"]:
                raise Cell14ReleaseError(f"{role} {artifact_id} SHA256 mismatch")
            run_paths[artifact_id] = path
        actual_filenames = {entry.name for entry in next(iter(run_paths.values())).parent.iterdir()}
        if actual_filenames != expected_filenames:
            raise Cell14ReleaseError(f"{role} run directory has missing or unexpected files")
        paths[role] = run_paths

    for artifact_id in EXPECTED_DETERMINISM["byte_identical_artifact_ids"]:
        canonical = paths["canonical"][artifact_id]
        replay = paths["replay"][artifact_id]
        if not filecmp.cmp(canonical, replay, shallow=False):
            raise Cell14ReleaseError(f"Deterministic replay mismatch: {artifact_id}")
    return paths


def _verify_audit(audit: dict[str, Any], run_id: str) -> None:
    _expect("audit policy_version", audit.get("policy_version"), "MES_V1_FEATURES_1.0")
    _expect("audit status", audit.get("status"), "PASS")
    _expect("audit failures", audit.get("failures"), [])
    _expect("audit upstream_binding", audit.get("upstream_binding"), EXPECTED_UPSTREAM_BINDING)
    _expect("audit feature_contract", audit.get("feature_contract"), EXPECTED_FEATURE_CONTRACT)
    trusted_controls = audit.get("trusted_controls")
    if not isinstance(trusted_controls, dict):
        raise Cell14ReleaseError("Audit trusted_controls is missing")
    _expect("audit trusted config", trusted_controls.get("config"), EXPECTED_TRUSTED_CONFIG)
    _expect(
        "audit trusted source hashes",
        trusted_controls.get("control_sha256"),
        EXPECTED_CONTROL_HASHES,
    )
    _expect("audit artifact firewall", audit.get("artifact_access"), EXPECTED_ARTIFACT_ACCESS)
    _expect(
        "audit physical reads", audit.get("physical_development_reads"), EXPECTED_PHYSICAL_READS
    )
    _expect("audit counts", audit.get("counts"), EXPECTED_AUDIT_COUNTS)
    _expect("audit constant features", audit.get("constant_features"), [])
    _expect("audit output hashes", audit.get("sha256"), EXPECTED_OUTPUT_HASHES)
    _expect(
        "audit upstream audit status",
        audit.get("upstream_audit_status"),
        EXPECTED_UPSTREAM_AUDIT_STATUS,
    )

    artifact_paths = audit.get("artifacts")
    if not isinstance(artifact_paths, dict) or set(artifact_paths) != {
        "features",
        "registry",
        "status_summary",
        "missingness_ledger",
        "audit",
    }:
        raise Cell14ReleaseError("Audit artifact path set is malformed")
    expected_names = {
        "features": COMMON_RUN_ARTIFACTS["features"]["filename"],
        "registry": COMMON_RUN_ARTIFACTS["registry"]["filename"],
        "status_summary": COMMON_RUN_ARTIFACTS["status_summary"]["filename"],
        "missingness_ledger": COMMON_RUN_ARTIFACTS["missingness_ledger"]["filename"],
        "audit": "cell14_feature_audit.json",
    }
    for artifact_id, value in artifact_paths.items():
        if not isinstance(value, str):
            raise Cell14ReleaseError(f"Audit artifact path is not text: {artifact_id}")
        normalized = value.replace("\\", "/")
        if normalized.rsplit("/", 1)[-1] != expected_names[artifact_id]:
            raise Cell14ReleaseError(f"Audit artifact filename mismatch: {artifact_id}")
        if f"/{run_id}/" not in normalized:
            raise Cell14ReleaseError(f"Audit artifact is bound to the wrong run: {artifact_id}")


def _canonical_audit(audit: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(audit)
    value.pop("audit_written_utc", None)
    value["artifacts"] = {
        key: path.replace("\\", "/").rsplit("/", 1)[-1] for key, path in value["artifacts"].items()
    }
    return value


def verify_audits(run_paths: dict[str, dict[str, Path]]) -> None:
    audits: dict[str, dict[str, Any]] = {}
    for role, record in AUDIT_RECORDS.items():
        audit = _load_json(run_paths[role]["audit"])
        _verify_audit(audit, record["run_id"])
        audits[role] = audit
    if _canonical_audit(audits["canonical"]) != _canonical_audit(audits["replay"]):
        raise Cell14ReleaseError("Canonical and replay audits differ beyond timestamp/run path")


def verify_feature_artifact_semantics(run_paths: dict[str, dict[str, Path]]) -> dict[str, int]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise Cell14ReleaseError(
            "pandas/pyarrow are required for semantic Cell 14 release verification"
        ) from exc

    canonical = run_paths["canonical"]
    features = pd.read_parquet(canonical["features"])
    registry = pd.read_csv(canonical["registry"])
    ledger = pd.read_csv(canonical["missingness_ledger"], dtype=str)
    status_summary = pd.read_csv(canonical["status_summary"])

    if len(features) != EXPECTED_COUNTS["development_rows"]:
        raise Cell14ReleaseError("Feature row count differs from the frozen release")
    if len(features.columns) != EXPECTED_COUNTS["output_columns"]:
        raise Cell14ReleaseError("Feature output column count differs from the frozen release")
    if list(features.columns[: len(METADATA_COLUMNS)]) != METADATA_COLUMNS:
        raise Cell14ReleaseError("Feature metadata column order differs from the release")
    if features["decision_id"].isna().any() or not features["decision_id"].is_unique:
        raise Cell14ReleaseError("Feature decision_id must be non-null and unique")

    final_boundary = pd.Timestamp("2025-01-01", tz="UTC")
    if (
        features["decision_time"].isna().any()
        or (features["decision_time"] >= final_boundary).any()
    ):
        raise Cell14ReleaseError("Feature artifact contains a 2025+ decision row")
    session_boundary = pd.Timestamp("2025-01-01")
    if (
        features["nyse_session_date"].isna().any()
        or (features["nyse_session_date"] >= session_boundary).any()
    ):
        raise Cell14ReleaseError("Feature artifact contains a 2025+ session row")
    if set(features["outer_partition"].dropna().unique()) != {"TRAIN", "VALIDATION"}:
        raise Cell14ReleaseError("Feature artifact contains a non-development partition")
    source_time = features["feature_max_source_time_utc"]
    if source_time.isna().any() or (source_time > features["decision_time"]).any():
        raise Cell14ReleaseError("Feature source time exceeds decision time")

    usable_count = int(features["feature_row_usable"].sum())
    if usable_count != EXPECTED_COUNTS["feature_usable_rows"]:
        raise Cell14ReleaseError("Feature usable row count differs")
    if len(features) - usable_count != EXPECTED_COUNTS["feature_unusable_rows"]:
        raise Cell14ReleaseError("Feature unusable row count differs")

    if list(registry.columns).count("feature_name") != 1:
        raise Cell14ReleaseError("Feature registry feature_name column is malformed")
    feature_names = registry["feature_name"].tolist()
    if len(feature_names) != EXPECTED_COUNTS["feature_columns"] or len(set(feature_names)) != len(
        feature_names
    ):
        raise Cell14ReleaseError("Feature registry does not contain 29 unique candidates")
    if list(features.columns[len(METADATA_COLUMNS) :]) != feature_names:
        raise Cell14ReleaseError("Feature artifact and candidate registry columns differ")

    missing_pairs: set[tuple[str, str]] = set()
    missing_count = 0
    for feature_name in feature_names:
        missing_decisions = features.loc[features[feature_name].isna(), "decision_id"].astype(str)
        missing_count += len(missing_decisions)
        missing_pairs.update((decision_id, feature_name) for decision_id in missing_decisions)
    if missing_count != EXPECTED_COUNTS["missing_feature_values"]:
        raise Cell14ReleaseError("Feature null count differs from the frozen release")
    if len(missing_pairs) != missing_count:
        raise Cell14ReleaseError("Feature missing cells are not one-to-one")

    if list(ledger.columns) != ["decision_id", "feature_name", "missing_reason"]:
        raise Cell14ReleaseError("Missingness ledger schema differs")
    if len(ledger) != EXPECTED_COUNTS["missingness_ledger_rows"]:
        raise Cell14ReleaseError("Missingness ledger row count differs")
    if ledger[["decision_id", "feature_name", "missing_reason"]].isna().any().any():
        raise Cell14ReleaseError("Missingness ledger contains null keys/reasons")
    if (ledger["missing_reason"].str.strip() == "").any():
        raise Cell14ReleaseError("Missingness ledger contains an empty reason")
    if ledger.duplicated(["decision_id", "feature_name"]).any():
        raise Cell14ReleaseError("Missingness ledger contains duplicate feature cells")
    ledger_pairs = set(zip(ledger["decision_id"], ledger["feature_name"], strict=True))
    if ledger_pairs != missing_pairs:
        raise Cell14ReleaseError("Missingness ledger is not one-to-one with feature nulls")

    actual_status = {
        (bool(usable), str(status)): int(rows)
        for usable, status, rows in status_summary[
            ["feature_row_usable", "feature_status", "rows"]
        ].itertuples(index=False, name=None)
    }
    expected_status = {
        (bool(usable), str(status)): int(rows)
        for (usable, status), rows in features.groupby(
            ["feature_row_usable", "feature_status"], dropna=False
        )
        .size()
        .items()
    }
    if actual_status != expected_status:
        raise Cell14ReleaseError("Status summary is not an exact feature-row aggregation")

    return {
        "development_rows": len(features),
        "feature_columns": len(feature_names),
        "missing_pairs": len(missing_pairs),
        "final_test_rows": int((features["decision_time"] >= final_boundary).sum()),
        "source_time_violations": int((source_time > features["decision_time"]).sum()),
    }


def verify_all(manifest_path: Path = RELEASE_MANIFEST_PATH) -> dict[str, int]:
    if manifest_path.resolve() == RELEASE_MANIFEST_PATH.resolve():
        if manifest_path.stat().st_size != EXPECTED_RELEASE_MANIFEST_SIZE:
            raise Cell14ReleaseError("Cell 14 release manifest byte size differs")
        if sha256(manifest_path) != EXPECTED_RELEASE_MANIFEST_SHA256:
            raise Cell14ReleaseError("Cell 14 release manifest SHA256 differs")
    manifest = _load_json(manifest_path)
    validate_release_manifest(manifest)
    verify_control_and_upstream_bytes(manifest)
    run_paths = verify_run_bytes(manifest)
    verify_audits(run_paths)
    return verify_feature_artifact_semantics(run_paths)


def main() -> None:
    result = verify_all()
    print("PASS: immutable Cell 14 local release manifest and all control/upstream bytes match")
    print("PASS: canonical and replay audits satisfy the input/final-test firewalls")
    print("PASS: both runs' four data artifacts are byte-identical and independently hashed")
    print(
        "PASS: 31,193 Development rows, 0 Final Test rows, 0 source-time violations, "
        f"and {result['missing_pairs']:,} one-to-one missingness records"
    )
    print("LOCKED: Cell 14 computation and Development data artifact")
    print("PROVISIONAL: candidate feature catalog")
    print("OPEN: fold-specific model transforms, selection, scaling, and imputation policy")


if __name__ == "__main__":
    main()

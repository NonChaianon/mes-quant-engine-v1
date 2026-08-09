from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from mes_quant.core.hashing import dataframe_content_sha256, sha256_file
from mes_quant.core.manifest import artifact_index, load_manifest, validate_manifest
from mes_quant.features.builder import FeatureConfig, build_development_features
from mes_quant.features.contract import FEATURE_COLUMNS, POLICY_VERSION, registry_records

INPUT_FILES = {
    "cell5_bars_15m": "MES_2019_2026_15m_clean.parquet",
    "cell5_audit": "cell5_15m_resample_audit.json",
    "cell7_universe": "cell7_decision_universe_v1.parquet",
    "cell7_audit": "cell7_decision_universe_audit.json",
    "cell8_assignments": "cell8_purged_split_assignments_v1.parquet",
    "cell8_audit": "cell8_purged_split_audit.json",
}

EXPECTED_INPUT_PRODUCERS = {
    "cell5_bars_15m": "CELL_5",
    "cell5_audit": "CELL_5",
    "cell7_universe": "CELL_7",
    "cell7_audit": "CELL_7",
    "cell8_assignments": "CELL_8",
    "cell8_audit": "CELL_8",
}

FORBIDDEN_INPUT_CELLS = (9, 10, 11, 12, 13)
FORBIDDEN_INPUT_PRODUCERS = {f"CELL_{cell}" for cell in FORBIDDEN_INPUT_CELLS}

OUTPUT_FILES = {
    "features": "cell14_development_point_in_time_features_v1.parquet",
    "registry": "cell14_feature_registry_v1.csv",
    "status_summary": "cell14_feature_status_summary_v1.csv",
    "missingness_ledger": "cell14_feature_missingness_ledger_v1.csv",
    "audit": "cell14_feature_audit.json",
}


class FeaturePipelineError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iso_utc(value: object) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat()


def _source_hashes() -> dict[str, str]:
    pipeline_source = Path(__file__).resolve()
    package_root = pipeline_source.parents[1]
    sources = {
        "feature_contract_source_sha256": package_root / "features" / "contract.py",
        "feature_builder_source_sha256": package_root / "features" / "builder.py",
        "feature_pipeline_source_sha256": pipeline_source,
    }
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FeaturePipelineError("Missing Cell 14 source file(s): " + ", ".join(missing))
    return {name: sha256_file(path) for name, path in sources.items()}


def _validate_manifest_contract(manifest: dict[str, Any], config: FeatureConfig) -> None:
    if manifest.get("manifest_version") != "MES_V1_FROZEN_COLAB_1.0":
        raise FeaturePipelineError("Unexpected frozen-release manifest version")

    locked = manifest.get("locked_contracts", {})
    expected_locked = {
        "decision_frequency_minutes": config.bar_minutes,
        "final_test_start_year": config.final_test_start_year,
        "final_test_outcomes_allowed": False,
    }
    for key, expected in expected_locked.items():
        if locked.get(key) != expected:
            raise FeaturePipelineError(
                f"Frozen manifest contract mismatch for {key}: "
                f"{locked.get(key)!r} != {expected!r}"
            )

    development_rows = manifest.get("golden_counts", {}).get("development_rows")
    if development_rows != config.expected_development_rows:
        raise FeaturePipelineError(
            "Frozen manifest Development count does not match the Cell 14 config"
        )


def _assert_clean_audit(
    audit: dict[str, Any],
    *,
    label: str,
    expected_policy: str | None = None,
) -> None:
    failures = audit.get("failures", [])
    if failures:
        raise FeaturePipelineError(f"{label} records failures: {failures}")
    if "status" in audit and audit["status"] != "PASS":
        raise FeaturePipelineError(f"{label} status is not PASS")
    if expected_policy is not None and audit.get("policy_version") != expected_policy:
        raise FeaturePipelineError(
            f"{label} policy mismatch: {audit.get('policy_version')} != {expected_policy}"
        )


def _verify_inputs(
    artifact_root: Path,
    manifest: dict[str, Any],
    access_log: dict[str, list[str]],
) -> tuple[
    dict[str, Path],
    dict[str, str],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    index = artifact_index(manifest)
    missing_ids = sorted(set(INPUT_FILES) - set(index))
    if missing_ids:
        raise FeaturePipelineError(
            "Frozen manifest lacks required Cell 14 artifact IDs: " + ", ".join(missing_ids)
        )

    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for artifact_id, filename in INPUT_FILES.items():
        metadata = index[artifact_id]
        if metadata.get("file") != filename:
            raise FeaturePipelineError(
                f"{artifact_id} manifest filename mismatch: "
                f"{metadata.get('file')!r} != {filename!r}"
            )
        expected_producer = EXPECTED_INPUT_PRODUCERS[artifact_id]
        if metadata.get("producer") != expected_producer:
            raise FeaturePipelineError(
                f"{artifact_id} producer mismatch: "
                f"{metadata.get('producer')!r} != {expected_producer!r}"
            )
        path = artifact_root / filename
        if not path.is_file():
            raise FeaturePipelineError(f"Missing required input: {path}")
        access_log["byte_verified_artifact_ids"].append(artifact_id)
        actual = sha256_file(path)
        expected = metadata["sha256"]
        if actual != expected:
            raise FeaturePipelineError(
                f"{artifact_id} SHA256 mismatch:\nexpected={expected}\nactual={actual}"
            )
        paths[artifact_id] = path
        hashes[artifact_id] = actual

    audits = {
        "cell5": _load_json(paths["cell5_audit"]),
        "cell7": _load_json(paths["cell7_audit"]),
        "cell8": _load_json(paths["cell8_audit"]),
    }
    access_log["parsed_artifact_ids"].extend(
        ["cell5_audit", "cell7_audit", "cell8_audit"]
    )
    _assert_clean_audit(audits["cell5"], label="Cell 5 audit")
    _assert_clean_audit(
        audits["cell7"],
        label="Cell 7 audit",
        expected_policy="MES_V1_DECISION_UNIVERSE_1.0",
    )
    _assert_clean_audit(
        audits["cell8"],
        label="Cell 8 audit",
        expected_policy="MES_V1_PURGED_SPLIT_1.0",
    )

    if audits["cell7"]["sha256"]["input_mes_15m_sha256"] != hashes["cell5_bars_15m"]:
        raise FeaturePipelineError("Cell 7 is not bound to the supplied Cell 5 bars")
    if audits["cell7"]["sha256"]["cell5_audit_sha256"] != hashes["cell5_audit"]:
        raise FeaturePipelineError("Cell 7 is not bound to the supplied Cell 5 audit")
    if audits["cell7"]["sha256"]["decision_universe_sha256"] != hashes[
        "cell7_universe"
    ]:
        raise FeaturePipelineError("Cell 7 universe hash is inconsistent with its audit")
    if audits["cell8"]["upstream_binding"]["cell7_universe_sha256"] != hashes[
        "cell7_universe"
    ]:
        raise FeaturePipelineError("Cell 8 is not bound to the supplied Cell 7 universe")
    if audits["cell8"]["sha256"]["input_cell7_audit_sha256"] != hashes["cell7_audit"]:
        raise FeaturePipelineError("Cell 8 is not bound to the supplied Cell 7 audit")
    if audits["cell8"]["sha256"]["split_assignments_sha256"] != hashes[
        "cell8_assignments"
    ]:
        raise FeaturePipelineError("Cell 8 assignment hash is inconsistent with its audit")
    split_contract = audits["cell8"].get("split_contract", {})
    if split_contract.get("final_test_is_untouched") is not True:
        raise FeaturePipelineError("Cell 8 does not assert an untouched Final Test")
    if split_contract.get("final_test_from_year") != 2025:
        raise FeaturePipelineError("Cell 8 Final Test start year is not the locked 2025 boundary")
    return paths, hashes, audits, index


def _read_development_inputs(
    paths: dict[str, Path],
    config: FeatureConfig,
    access_log: dict[str, list[str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    partition_filter = [
        [("outer_partition", "==", partition)]
        for partition in config.development_partitions
    ]
    assignments = pd.read_parquet(
        paths["cell8_assignments"],
        filters=partition_filter,
    )
    access_log["parsed_artifact_ids"].append("cell8_assignments")
    required_assignment_columns = {"decision_id", "outer_partition", "decision_time"}
    if not required_assignment_columns.issubset(assignments.columns):
        raise FeaturePipelineError("Cell 8 assignments lack Development firewall columns")
    if len(assignments) != config.expected_development_rows:
        raise FeaturePipelineError(
            "Physical Cell 8 Development read returned the wrong row count: "
            f"{len(assignments):,} != {config.expected_development_rows:,}"
        )
    if assignments[list(required_assignment_columns)].isna().any().any():
        raise FeaturePipelineError("Cell 8 Development identity/partition/time contains nulls")
    partitions = sorted(assignments["outer_partition"].astype(str).unique().tolist())
    if partitions != sorted(config.development_partitions):
        raise FeaturePipelineError(f"Unexpected loaded Cell 8 partitions: {partitions}")

    assignment_times = pd.to_datetime(assignments["decision_time"], utc=True, errors="raise")
    development_start = assignment_times.min()
    development_end = assignment_times.max()
    final_test_boundary = pd.Timestamp(
        year=config.final_test_start_year,
        month=1,
        day=1,
        tz="UTC",
    )
    if development_end >= final_test_boundary:
        raise FeaturePipelineError("Physical Cell 8 read crossed the Final Test time boundary")

    time_filter = [
        ("decision_time", ">=", development_start.to_pydatetime()),
        ("decision_time", "<=", development_end.to_pydatetime()),
    ]
    universe = pd.read_parquet(paths["cell7_universe"], filters=time_filter)
    access_log["parsed_artifact_ids"].append("cell7_universe")
    if not {"decision_id", "decision_time"}.issubset(universe.columns):
        raise FeaturePipelineError("Cell 7 universe lacks Development firewall columns")
    universe_times = pd.to_datetime(universe["decision_time"], utc=True, errors="raise")
    if universe_times.isna().any() or universe_times.min() < development_start:
        raise FeaturePipelineError("Physical Cell 7 read returned pre-Development rows")
    if universe_times.max() > development_end:
        raise FeaturePipelineError("Physical Cell 7 read returned post-Development rows")
    if len(universe) != len(assignments):
        raise FeaturePipelineError("Physical Cell 7/8 Development row counts differ")
    if set(universe["decision_id"].astype(str)) != set(assignments["decision_id"].astype(str)):
        raise FeaturePipelineError("Physical Cell 7/8 Development IDs differ")

    physical_lookback_bars = max(
        config.maximum_lookback_bars,
        config.session_vwap_max_bars,
    )
    first_market_time = development_start - pd.Timedelta(
        minutes=physical_lookback_bars * config.bar_minutes
    )
    market_filter = [
        ("decision_time", ">=", first_market_time.to_pydatetime()),
        ("decision_time", "<=", development_end.to_pydatetime()),
    ]
    bars = pd.read_parquet(paths["cell5_bars_15m"], filters=market_filter)
    access_log["parsed_artifact_ids"].append("cell5_bars_15m")
    if "decision_time" not in bars.columns or bars.empty:
        raise FeaturePipelineError("Physical Cell 5 Development read returned no usable time column")
    loaded_bar_times = pd.to_datetime(bars["decision_time"], utc=True, errors="raise")
    if loaded_bar_times.isna().any() or loaded_bar_times.min() < first_market_time:
        raise FeaturePipelineError("The Cell 5 filtered read returned pre-predicate market rows")
    if loaded_bar_times.max() > development_end:
        raise FeaturePipelineError("The Cell 5 filtered read returned post-Development market rows")
    if loaded_bar_times.max() >= final_test_boundary:
        raise FeaturePipelineError("The Cell 5 filtered read crossed the Final Test boundary")

    loaded = {
        "cell8_assignments": {
            "physical_filter": {
                "outer_partition_in": list(config.development_partitions),
            },
            "rows": len(assignments),
            "decision_time_min_utc": _iso_utc(assignment_times.min()),
            "decision_time_max_utc": _iso_utc(assignment_times.max()),
            "partitions": partitions,
        },
        "cell7_universe": {
            "physical_filter": {
                "decision_time_gte_utc": _iso_utc(development_start),
                "decision_time_lte_utc": _iso_utc(development_end),
            },
            "rows": len(universe),
            "decision_time_min_utc": _iso_utc(universe_times.min()),
            "decision_time_max_utc": _iso_utc(universe_times.max()),
        },
        "cell5_bars_15m": {
            "physical_filter": {
                "decision_time_gte_utc": _iso_utc(first_market_time),
                "decision_time_lte_utc": _iso_utc(development_end),
                "conservative_lookback_bars": physical_lookback_bars,
                "conservative_lookback_minutes": (
                    physical_lookback_bars * config.bar_minutes
                ),
            },
            "rows": len(bars),
            "decision_time_min_utc": _iso_utc(loaded_bar_times.min()),
            "decision_time_max_utc": _iso_utc(loaded_bar_times.max()),
            "rows_at_or_after_final_test_boundary": int(
                loaded_bar_times.ge(final_test_boundary).sum()
            ),
        },
    }
    return bars, universe, assignments, loaded


def _new_output_directory(run_root: Path) -> Path:
    run_id = datetime.now(UTC).strftime("cell14_%Y%m%dT%H%M%SZ")
    output = run_root / run_id
    if output.exists():
        raise FeaturePipelineError(f"Refusing to overwrite an existing run: {output}")
    output.mkdir(parents=True, exist_ok=False)
    return output


def run_feature_pipeline(
    *,
    artifact_root: str | Path,
    run_root: str | Path,
    manifest_path: str | Path,
    config_path: str | Path,
) -> Path:
    artifact_root = Path(artifact_root).expanduser().resolve()
    run_root = Path(run_root).expanduser().resolve()
    manifest_path = Path(manifest_path).expanduser().resolve()
    config_path = Path(config_path).expanduser().resolve()

    if not manifest_path.is_file():
        raise FeaturePipelineError(f"Missing frozen manifest: {manifest_path}")
    if not config_path.is_file():
        raise FeaturePipelineError(f"Missing Cell 14 config: {config_path}")

    config = FeatureConfig.from_json(config_path)
    config.validate(production=True)

    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    _validate_manifest_contract(manifest, config)
    control_hashes = {
        "config_file_sha256": sha256_file(config_path),
        "manifest_file_sha256": sha256_file(manifest_path),
        **_source_hashes(),
    }

    access_log: dict[str, list[str]] = {
        "byte_verified_artifact_ids": [],
        "parsed_artifact_ids": [],
    }
    paths, input_hashes, audits, manifest_index = _verify_inputs(
        artifact_root,
        manifest,
        access_log,
    )
    bars, universe, assignments, loaded_inputs = _read_development_inputs(
        paths,
        config,
        access_log,
    )

    opened_artifact_ids = sorted(
        set(access_log["byte_verified_artifact_ids"])
        | set(access_log["parsed_artifact_ids"])
    )
    forbidden_manifest_artifact_ids = sorted(
        artifact_id
        for artifact_id, metadata in manifest_index.items()
        if metadata.get("producer") in FORBIDDEN_INPUT_PRODUCERS
    )
    forbidden_opened_artifact_ids = sorted(
        set(opened_artifact_ids) & set(forbidden_manifest_artifact_ids)
    )
    if forbidden_opened_artifact_ids:
        raise FeaturePipelineError(
            "Forbidden Cell 9-13 artifacts were opened: "
            + ", ".join(forbidden_opened_artifact_ids)
        )
    if set(opened_artifact_ids) != set(INPUT_FILES):
        raise FeaturePipelineError(
            "Actual Cell 14 artifact access differs from the trusted input allowlist"
        )

    build = build_development_features(
        bars,
        universe,
        assignments,
        config=config,
    )
    features = build.features
    missingness_ledger = build.missingness_ledger
    diagnostic_missing_rows = int(build.diagnostics.get("missingness_ledger_rows", -1))
    diagnostic_missing_values = int(build.diagnostics.get("missing_feature_values", -1))
    if diagnostic_missing_rows != len(missingness_ledger):
        raise FeaturePipelineError(
            "Builder missingness-ledger diagnostic does not equal the ledger row count"
        )
    if diagnostic_missing_values != len(missingness_ledger):
        raise FeaturePipelineError(
            "Builder missing-feature count does not equal the ledger row count"
        )
    required_ledger_columns = {"decision_id", "feature_name", "missing_reason"}
    if set(missingness_ledger.columns) != required_ledger_columns:
        raise FeaturePipelineError("Unexpected Cell 14 missingness-ledger schema")
    if missingness_ledger.duplicated(["decision_id", "feature_name"]).any():
        raise FeaturePipelineError("Duplicate decision/feature in Cell 14 missingness ledger")

    constant_features = [
        name for name in FEATURE_COLUMNS if features[name].dropna().nunique() <= 1
    ]
    if constant_features:
        raise FeaturePipelineError(
            "Constant or empty candidate features detected: " + ", ".join(constant_features)
        )
    if len(features) != 31_193:
        raise FeaturePipelineError("Cell 14 must contain exactly 31,193 Development decisions")
    if not features["decision_id"].is_unique or not features["decision_time"].is_unique:
        raise FeaturePipelineError("Cell 14 decision identity is not unique")
    expected_ids = set(assignments["decision_id"].astype(str))
    actual_ids = set(features["decision_id"].astype(str))
    if actual_ids != expected_ids:
        raise FeaturePipelineError("Cell 14 IDs do not exactly reconcile with Cell 8 Development")

    source_hash_string = json.dumps(
        {
            "cell5_bars_15m": input_hashes["cell5_bars_15m"],
            "cell7_universe": input_hashes["cell7_universe"],
            "cell8_assignments": input_hashes["cell8_assignments"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    registry = pd.DataFrame(registry_records(source_hash_string))
    status_summary = (
        features.groupby(["feature_row_usable", "feature_status"], dropna=False)
        .size()
        .rename("rows")
        .reset_index()
        .sort_values(["feature_row_usable", "feature_status"], ascending=[False, True])
    )

    ending_control_hashes = {
        "config_file_sha256": sha256_file(config_path),
        "manifest_file_sha256": sha256_file(manifest_path),
        **_source_hashes(),
    }
    if ending_control_hashes != control_hashes:
        raise FeaturePipelineError("Cell 14 config/manifest/source changed during the run")

    output = _new_output_directory(run_root)
    output_paths = {name: output / filename for name, filename in OUTPUT_FILES.items()}

    features.to_parquet(output_paths["features"], index=False)
    registry.to_csv(output_paths["registry"], index=False, lineterminator="\n")
    status_summary.to_csv(output_paths["status_summary"], index=False, lineterminator="\n")
    missingness_ledger.to_csv(
        output_paths["missingness_ledger"],
        index=False,
        lineterminator="\n",
    )

    output_hashes = {
        "features_file_sha256": sha256_file(output_paths["features"]),
        "features_content_sha256": dataframe_content_sha256(features, index=False),
        "registry_sha256": sha256_file(output_paths["registry"]),
        "status_summary_sha256": sha256_file(output_paths["status_summary"]),
        "missingness_ledger_sha256": sha256_file(output_paths["missingness_ledger"]),
    }
    audit = {
        "audit_written_utc": datetime.now(UTC).isoformat(),
        "policy_version": POLICY_VERSION,
        "status": "PASS",
        "upstream_binding": {
            "manifest_version": manifest.get("manifest_version"),
            "manifest_status": manifest.get("status"),
            "manifest_file_sha256": control_hashes["manifest_file_sha256"],
            "config_file_sha256": control_hashes["config_file_sha256"],
            "cell5_bars_sha256": input_hashes["cell5_bars_15m"],
            "cell5_audit_sha256": input_hashes["cell5_audit"],
            "cell7_universe_sha256": input_hashes["cell7_universe"],
            "cell7_audit_sha256": input_hashes["cell7_audit"],
            "cell8_assignments_sha256": input_hashes["cell8_assignments"],
            "cell8_audit_sha256": input_hashes["cell8_audit"],
        },
        "feature_contract": {
            "input_cells": [5, 7, 8],
            "forbidden_input_cells": list(FORBIDDEN_INPUT_CELLS),
            "target_cost_path_artifacts_opened": len(forbidden_opened_artifact_ids),
            "feature_partitions": list(config.development_partitions),
            "final_test_feature_rows": 0,
            "maximum_rolling_lookback_bars": config.maximum_lookback_bars,
            "session_vwap_max_bars": config.session_vwap_max_bars,
            "bar_minutes": config.bar_minutes,
            "exact_grid_required": True,
            "same_instrument_required": True,
            "imputation_allowed": False,
            "output_scaled": False,
            "current_completed_bar_allowed": True,
            "live_fill_at_bar_close_guaranteed": False,
        },
        "trusted_controls": {
            "config": asdict(config),
            "control_sha256": control_hashes,
        },
        "artifact_access": {
            "trusted_input_allowlist": sorted(INPUT_FILES),
            "byte_verified_artifact_ids": sorted(
                set(access_log["byte_verified_artifact_ids"])
            ),
            "parsed_artifact_ids": sorted(set(access_log["parsed_artifact_ids"])),
            "actual_opened_artifact_ids": opened_artifact_ids,
            "forbidden_manifest_artifact_ids": forbidden_manifest_artifact_ids,
            "forbidden_opened_artifact_ids": forbidden_opened_artifact_ids,
            "forbidden_opened_artifact_count": len(forbidden_opened_artifact_ids),
        },
        "physical_development_reads": loaded_inputs,
        "counts": build.diagnostics,
        "constant_features": constant_features,
        "artifacts": {name: str(path) for name, path in output_paths.items()},
        "sha256": output_hashes,
        "upstream_audit_status": {
            "cell5_failures": audits["cell5"].get("failures", []),
            "cell5_policy_version": audits["cell5"].get("policy_version"),
            "cell7_status": audits["cell7"].get("status"),
            "cell7_policy_version": audits["cell7"].get("policy_version"),
            "cell8_status": audits["cell8"].get("status"),
            "cell8_policy_version": audits["cell8"].get("policy_version"),
        },
        "open_items": [
            "Feature redundancy and stability selection",
            "Fold-specific scaling and missing-value policy",
            "Execution delay and achievable live fill price",
            "Final Test transformation after the full model protocol freezes",
        ],
        "failures": [],
    }
    output_paths["audit"].write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output

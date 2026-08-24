from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

import pyarrow.dataset as pads

from mes_quant.core.hashing import canonical_json_bytes, canonicalize_audit, sha256_bytes
from mes_quant.exploration import test2_l1_harness as _harness
from mes_quant.exploration.test2_l1_harness import (
    CanonicalArtifactPaths,
    MetadataIdentityPreflight,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_RELEASE_MANIFEST_SHA256,
    EXPLORATION_SCOPE_ID,
    FEATURE_ARTIFACT_SHA256,
    FROZEN_COLAB_MANIFEST_SHA256,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
)

G2_GATE_LITERAL = "G2_CANONICAL_METADATA_ONLY"
G2_GATE_ID = "TEST2_G2_CANONICAL_METADATA_PREFLIGHT_V1"
G2_RECORD_VERSION = "1.0"
G2_ACCESS_LEVEL = "L0_METADATA_ONLY_NO_ROW_VALUES"
G2_STATUS = "PASS"
G2_BASE_COMMIT = "99daf97e4f7cb1a1d1d0e02f743cf1b164b49201"
G2_BRANCH = "research/test2-g2-metadata-preflight-v1"

G2_ALLOWED_CHANGED_FILES = frozenset(
    {
        "docs/research/TEST2_G2_METADATA_PREFLIGHT_PACKAGE_V1.md",
        "src/mes_quant/exploration/test2_metadata_preflight.py",
        "tests/test_test2_metadata_preflight.py",
        "tools/run_test2_g2_metadata_preflight.py",
    }
)

_EXPECTED_FILENAMES = {
    "raw_dbn": _harness.CANONICAL_RAW_DBN_FILENAME,
    "cell8_assignments": _harness.CANONICAL_CELL8_FILENAME,
    "cell10_labels": _harness.CANONICAL_CELL10_FILENAME,
    "cell12_paths": _harness.CANONICAL_CELL12_FILENAME,
    "cell14_features": _harness.CANONICAL_FEATURE_FILENAME,
}
_EXPECTED_HASHES = {
    "raw_dbn": RAW_DBN_SHA256,
    "cell8_assignments": CELL8_SPLIT_ASSIGNMENT_SHA256,
    "cell10_labels": CELL10_LABEL_SHA256,
    "cell12_paths": CELL12_PATH_SHA256,
    "cell14_features": FEATURE_ARTIFACT_SHA256,
}
_ZERO_COUNTERS = {
    "numeric_values_read": 0,
    "parquet_row_groups_read": 0,
    "parquet_column_statistics_read": 0,
    "decoded_dbn_messages_read": 0,
    "real_train_target_path_rows_read": 0,
    "validation_rows_read": 0,
    "final_test_rows_read": 0,
    "targets_constructed": 0,
    "real_models_fitted": 0,
}
_NOT_PERFORMED = (
    "decoded_dbn_value_hash",
    "ordered_feature_content_recompute",
    "target_construction",
    "cell12_numeric_reconciliation",
    "model_fit",
    "validation_access",
    "final_test_access",
    "database_operation",
)
_FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "statistics",
        "min",
        "max",
        "min_value",
        "max_value",
        "null_count",
        "distinct_count",
        "key_value_metadata",
    }
)


class G2BoundaryError(RuntimeError):
    """Raised before G2 could exceed metadata-only authorization."""


def _git_sha(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise G2BoundaryError(f"{field} must be a lowercase 40-character Git SHA")
    return value


def _loaded_modules(prefix: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name in sys.modules
            if name == prefix or name.startswith(prefix + ".")
        )
    )


def _assert_dbn_modules_absent(*, phase: str) -> None:
    loaded = _loaded_modules("databento") + _loaded_modules("databento_dbn")
    if loaded:
        raise G2BoundaryError(
            f"DBN decoder modules loaded during G2 {phase}: {', '.join(loaded)}"
        )


@dataclass
class _G2ReadGuard:
    forbidden_calls: int = 0
    installed_symbols: list[str] = field(default_factory=list)

    def reject(self, symbol: str) -> NoReturn:
        self.forbidden_calls += 1
        raise G2BoundaryError(f"G2 metadata-only boundary blocked call: {symbol}")

    def blocker(self, symbol: str):
        def blocked(*_args: object, **_kwargs: object) -> NoReturn:
            self.reject(symbol)

        return blocked


@dataclass(frozen=True)
class _FooterMetadataOnly:
    num_rows: int
    guard: _G2ReadGuard

    def __getattr__(self, name: str) -> NoReturn:
        self.guard.reject(f"ParquetFile.metadata.{name}")


@dataclass(frozen=True)
class _SchemaNamesOnly:
    names: tuple[str, ...]
    guard: _G2ReadGuard

    def __getattr__(self, name: str) -> NoReturn:
        self.guard.reject(f"ParquetFile.schema_arrow.{name}")


@dataclass(frozen=True)
class _FooterOnlyParquetFile:
    schema_arrow: _SchemaNamesOnly
    metadata: _FooterMetadataOnly
    guard: _G2ReadGuard

    def __getattr__(self, name: str) -> NoReturn:
        self.guard.reject(f"ParquetFile.{name}")


@contextmanager
def _metadata_only_read_guard() -> Iterator[_G2ReadGuard]:
    """Expose only schema names and footer row counts to the G1 preflight."""

    guard = _G2ReadGuard()
    original_parquet_file = _harness.pq.ParquetFile
    originals: list[tuple[object, str, object]] = []

    def install_required(
        owner: object,
        name: str,
        replacement: object,
        *,
        label: str,
    ) -> None:
        if not hasattr(owner, name):
            raise G2BoundaryError(f"G2 required guard symbol is missing: {label}")
        originals.append((owner, name, getattr(owner, name)))
        setattr(owner, name, replacement)
        guard.installed_symbols.append(label)

    def footer_only_parquet_file(*args: object, **kwargs: object) -> _FooterOnlyParquetFile:
        parquet = original_parquet_file(*args, **kwargs)
        names = tuple(parquet.schema_arrow.names)
        num_rows = int(parquet.metadata.num_rows)
        return _FooterOnlyParquetFile(
            schema_arrow=_SchemaNamesOnly(names, guard),
            metadata=_FooterMetadataOnly(num_rows, guard),
            guard=guard,
        )

    try:
        install_required(
            _harness.pq,
            "ParquetFile",
            footer_only_parquet_file,
            label="pyarrow.parquet.ParquetFile.footer_only_proxy",
        )
        for symbol in (
            "read_table",
            "read_pandas",
            "read_metadata",
            "read_schema",
            "ParquetDataset",
            "ParquetWriter",
            "write_table",
            "write_metadata",
            "write_to_dataset",
        ):
            label = f"pyarrow.parquet.{symbol}"
            install_required(_harness.pq, symbol, guard.blocker(label), label=label)
        for symbol in ("dataset", "write_dataset"):
            label = f"pyarrow.dataset.{symbol}"
            install_required(pads, symbol, guard.blocker(label), label=label)
        install_required(
            _harness.pd,
            "read_parquet",
            guard.blocker("pandas.read_parquet"),
            label="pandas.read_parquet",
        )
        install_required(
            _harness.pd.util,
            "hash_pandas_object",
            guard.blocker("pandas.util.hash_pandas_object"),
            label="pandas.util.hash_pandas_object",
        )
        for symbol in (
            "decoded_frame_content_sha256",
            "verify_decoded_frame_identity",
            "read_train_only_parquet",
            "prepare_train_inputs",
            "build_train_path_targets",
            "assemble_fold_evaluation_data",
            "build_real_l1_run_context",
        ):
            label = f"test2_l1_harness.{symbol}"
            install_required(_harness, symbol, guard.blocker(label), label=label)
        yield guard
    finally:
        for owner, name, original in reversed(originals):
            setattr(owner, name, original)


def _canonical_paths(paths: CanonicalArtifactPaths) -> dict[str, Path]:
    return {
        "raw_dbn": paths.raw_dbn,
        "cell8_assignments": paths.cell8_assignments,
        "cell10_labels": paths.cell10_labels,
        "cell12_paths": paths.cell12_paths,
        "cell14_features": paths.cell14_features,
    }


def _assert_canonical_filenames(paths: CanonicalArtifactPaths) -> None:
    for artifact_id, path in _canonical_paths(paths).items():
        expected = _EXPECTED_FILENAMES[artifact_id]
        if path.name != expected:
            raise G2BoundaryError(
                f"MISSING_CANONICAL_ARTIFACT: {artifact_id} requires filename {expected}"
            )


def _binding(expected: str, observed: str, *, field: str) -> dict[str, object]:
    match = expected == observed
    if not match:
        raise G2BoundaryError(f"{field} identity mismatch")
    return {"expected": expected, "observed": observed, "match": True}


def _normalized_artifact_record(
    artifact: Mapping[str, object],
    *,
    source_path: Path,
) -> dict[str, object]:
    artifact_id = artifact.get("artifact_id")
    if not isinstance(artifact_id, str) or artifact_id not in _EXPECTED_HASHES:
        raise G2BoundaryError("G2 preflight returned a non-canonical artifact ID")
    schema = artifact.get("parquet_schema")
    if not isinstance(schema, (tuple, list)) or any(
        not isinstance(name, str) for name in schema
    ):
        raise G2BoundaryError(f"{artifact_id} returned a malformed Parquet schema")
    row_count = artifact.get("parquet_row_count")
    if row_count is not None and (
        isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0
    ):
        raise G2BoundaryError(f"{artifact_id} returned a malformed footer row count")
    return {
        "artifact_id": artifact_id,
        "path": f"${{MES_G2_ARTIFACTS}}/{artifact_id}/{source_path.name}",
        "byte_sha256": artifact.get("byte_sha256"),
        "size_bytes": source_path.stat().st_size,
        "parquet_row_count": row_count,
        "parquet_schema": list(schema),
        "manifest_artifact_id": artifact.get("manifest_artifact_id"),
        "footer_scope": "SCHEMA_NAMES_AND_NUM_ROWS_ONLY_NO_STATISTICS",
    }


def _walk_record_keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_record_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_record_keys(child)


def _assert_closed_record(record: Mapping[str, object]) -> None:
    forbidden = sorted(_FORBIDDEN_RECORD_KEYS.intersection(_walk_record_keys(record)))
    if forbidden:
        raise G2BoundaryError(
            "G2 record contains forbidden footer/value fields: " + ", ".join(forbidden)
        )
    if "request_set_sha256" in set(_walk_record_keys(record)):
        raise G2BoundaryError("G2 record must not contain a request-set identity")


def _cell14_run_binding(
    manifest_path: Path,
    *,
    selected_run_id: str,
    feature_path: Path,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise G2BoundaryError("Cell 14 release manifest root must be an object")
    canonical_run_id = manifest.get("canonical_run_id")
    replay_run_id = manifest.get("replay_run_id")
    if not isinstance(canonical_run_id, str) or not isinstance(replay_run_id, str):
        raise G2BoundaryError("Cell 14 release run IDs are malformed")
    allowed = {canonical_run_id, replay_run_id}
    if selected_run_id not in allowed:
        raise G2BoundaryError("cell14_run_id is not canonical or replay in the release")
    role = "canonical" if selected_run_id == canonical_run_id else "replay"
    runs = manifest.get("runs")
    if not isinstance(runs, dict):
        raise G2BoundaryError("Cell 14 release runs are malformed")
    run = runs.get(role)
    if not isinstance(run, dict):
        raise G2BoundaryError("Cell 14 selected run declaration is malformed")
    artifacts = run.get("artifacts")
    if not isinstance(artifacts, dict):
        raise G2BoundaryError("Cell 14 selected run artifacts are malformed")
    declared = artifacts.get("features")
    if not isinstance(declared, dict):
        raise G2BoundaryError("Cell 14 selected feature declaration is malformed")
    if run.get("run_id") != selected_run_id:
        raise G2BoundaryError("Cell 14 selected run ID is not bound to the release")
    if declared.get("sha256") != FEATURE_ARTIFACT_SHA256:
        raise G2BoundaryError("Cell 14 selected run has a different feature byte hash")
    declared_path = declared.get("file")
    if not isinstance(declared_path, str) or Path(declared_path).name != feature_path.name:
        raise G2BoundaryError("Cell 14 selected run has a different feature filename")
    return {
        "canonical_run_id": canonical_run_id,
        "replay_run_id": replay_run_id,
        "resolved_features_run_id": selected_run_id,
        "resolved_features_role": role,
        "declared_feature_path": f"${{REPOSITORY}}/{declared_path}",
        "run_binding_status": "MATCHED_RELEASE_DECLARATION",
    }


def _record_sha256(record: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    canonical = canonicalize_audit(without_hash)
    return sha256_bytes(canonical_json_bytes(canonical))


def build_g2_metadata_preflight_record(
    paths: CanonicalArtifactPaths,
    *,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
    cell14_run_id: str,
    code_identity: str,
    branch: str,
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    """Run the already-frozen G1 metadata preflight under a stricter G2 guard."""

    _git_sha(code_identity, field="code_identity")
    if branch != G2_BRANCH:
        raise G2BoundaryError(f"G2 must execute on branch {G2_BRANCH}")
    _assert_canonical_filenames(paths)
    _assert_dbn_modules_absent(phase="entry")
    with _metadata_only_read_guard() as guard:
        preflight = _harness.canonical_metadata_preflight(
            paths,
            cell14_release_manifest_path=cell14_release_manifest_path,
            frozen_colab_manifest_path=frozen_colab_manifest_path,
        )
    _assert_dbn_modules_absent(phase="exit")
    if guard.forbidden_calls != 0:
        raise G2BoundaryError("G2 attempted a forbidden reader call")
    if not isinstance(preflight, MetadataIdentityPreflight):
        raise G2BoundaryError("G2 preflight returned an unexpected record type")
    if preflight.numeric_values_read != 0:
        raise G2BoundaryError("G2 preflight reported numeric row values")
    if (
        preflight.ordered_feature_content_status != "NOT_RECOMPUTED_METADATA_ONLY"
        or preflight.decoded_content_status != "NOT_RECOMPUTED_METADATA_ONLY"
    ):
        raise G2BoundaryError("G2 preflight misstates a numeric-content recomputation")

    source_paths = _canonical_paths(paths)
    raw_artifacts = tuple(artifact.as_record() for artifact in preflight.artifacts)
    observed_ids = tuple(str(item.get("artifact_id")) for item in raw_artifacts)
    if observed_ids != tuple(_EXPECTED_HASHES):
        raise G2BoundaryError("G2 preflight did not return the exact five artifacts")
    artifacts = [
        _normalized_artifact_record(
            artifact,
            source_path=source_paths[str(artifact["artifact_id"])],
        )
        for artifact in raw_artifacts
    ]
    observed = {str(item["artifact_id"]): str(item["byte_sha256"]) for item in artifacts}
    expected_identity_binding = {
        artifact_id: _binding(
            expected,
            observed[artifact_id],
            field=artifact_id,
        )
        for artifact_id, expected in _EXPECTED_HASHES.items()
    }
    expected_identity_binding.update(
        {
            "cell14_release_manifest": _binding(
                CELL14_RELEASE_MANIFEST_SHA256,
                preflight.release_manifest_sha256,
                field="cell14_release_manifest",
            ),
            "frozen_colab_manifest": _binding(
                FROZEN_COLAB_MANIFEST_SHA256,
                str(preflight.control_manifest_sha256),
                field="frozen_colab_manifest",
            ),
            "ordered_feature_content_declared": _binding(
                ORDERED_FEATURE_CONTENT_SHA256,
                str(preflight.ordered_feature_content_sha256_declared),
                field="ordered_feature_content_declared",
            ),
        }
    )
    cell14_binding = _cell14_run_binding(
        Path(cell14_release_manifest_path).expanduser().resolve(),
        selected_run_id=cell14_run_id,
        feature_path=paths.cell14_features,
    )
    preflight_record = {
        "release_manifest_sha256": preflight.release_manifest_sha256,
        "control_manifest_sha256": preflight.control_manifest_sha256,
        "ordered_feature_content_sha256_declared": (
            preflight.ordered_feature_content_sha256_declared
        ),
        "artifacts": artifacts,
        "numeric_values_read": preflight.numeric_values_read,
        "ordered_feature_content_status": preflight.ordered_feature_content_status,
        "decoded_content_status": preflight.decoded_content_status,
        "parquet_footer_scope": "SCHEMA_NAMES_AND_NUM_ROWS_ONLY_NO_STATISTICS",
    }
    record_core: dict[str, object] = {
        "gate_id": G2_GATE_ID,
        "record_version": G2_RECORD_VERSION,
        "exploration_scope_id": EXPLORATION_SCOPE_ID,
        "base_commit": G2_BASE_COMMIT,
        "code_identity": code_identity,
        "branch": branch,
        "access_level": G2_ACCESS_LEVEL,
        "status": G2_STATUS,
        "preflight": preflight_record,
        "expected_identity_binding": expected_identity_binding,
        "cell14_run_binding": cell14_binding,
        "counters": dict(_ZERO_COUNTERS),
        "not_performed": list(_NOT_PERFORMED),
        "forbidden_module_witness": {
            "databento_modules_loaded": [],
            "databento_dbn_modules_loaded": [],
            "forbidden_reader_calls": guard.forbidden_calls,
            "installed_guard_symbols": list(guard.installed_symbols),
            "guard_status": "PASS_NO_FORBIDDEN_CALLS",
        },
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "g3_status": "NOT_AUTHORIZED",
    }
    run_seed = sha256_bytes(canonical_json_bytes(canonicalize_audit(record_core)))
    record = {
        **record_core,
        "run_id": f"MES_T2_G2_{run_seed[:16].upper()}",
        "audit_written_utc": audit_written_utc
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _assert_closed_record(record)
    record["record_sha256"] = _record_sha256(record)
    return record


def write_g2_metadata_preflight_record(
    record: Mapping[str, object],
    *,
    output_root: str | Path,
) -> Path:
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("MES_T2_G2_"):
        raise G2BoundaryError("G2 record has a malformed run_id")
    root = Path(output_root).expanduser().resolve()
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output = run_dir / "metadata_preflight_record.json"
    descriptor = -1
    temporary_output: Path | None = None
    published = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".metadata_preflight_record.",
            suffix=".tmp",
            dir=run_dir,
        )
        temporary_output = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_output, output)
        published = True
        temporary_output.unlink()
        temporary_output = None
        directory_descriptor = os.open(run_dir, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_output is not None:
            temporary_output.unlink(missing_ok=True)
        if published:
            output.unlink(missing_ok=True)
        if run_dir.exists() and not any(run_dir.iterdir()):
            run_dir.rmdir()
        raise
    return output


def _git_output(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_execution_context(project_root: Path) -> tuple[str, str]:
    branch = _git_output(project_root, "branch", "--show-current")
    if branch != G2_BRANCH:
        raise G2BoundaryError(f"G2 must execute on branch {G2_BRANCH}")
    code_identity = _git_output(project_root, "rev-parse", "HEAD")
    _git_sha(code_identity, field="code_identity")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", G2_BASE_COMMIT, code_identity],
        cwd=project_root,
        check=False,
    )
    if ancestor.returncode != 0:
        raise G2BoundaryError("G2 code identity does not descend from the authorized base")
    changed_files = frozenset(
        filter(
            None,
            _git_output(
                project_root,
                "diff",
                "--name-only",
                f"{G2_BASE_COMMIT}..{code_identity}",
            ).splitlines(),
        )
    )
    if changed_files != G2_ALLOWED_CHANGED_FILES:
        unexpected = sorted(changed_files.difference(G2_ALLOWED_CHANGED_FILES))
        missing = sorted(G2_ALLOWED_CHANGED_FILES.difference(changed_files))
        raise G2BoundaryError(
            "G2 changed-file firewall mismatch; "
            f"unexpected={unexpected}; missing={missing}"
        )
    tracked_status = _git_output(
        project_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
    )
    if tracked_status:
        raise G2BoundaryError("G2 execution requires a clean tracked worktree")
    try:
        upstream_identity = _git_output(project_root, "rev-parse", "@{upstream}")
    except subprocess.CalledProcessError as exc:
        raise G2BoundaryError("G2 branch must have a pushed upstream") from exc
    if upstream_identity != code_identity:
        raise G2BoundaryError("G2 local and upstream code identities must match")
    return code_identity, branch


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Owner-only Test 2 G2 canonical metadata preflight."
    )
    parser.add_argument("--gate", choices=(G2_GATE_LITERAL,), required=True)
    parser.add_argument("--raw-dbn", type=Path, required=True)
    parser.add_argument("--cell8", type=Path, required=True)
    parser.add_argument("--cell10", type=Path, required=True)
    parser.add_argument("--cell12", type=Path, required=True)
    parser.add_argument("--cell14-features", type=Path, required=True)
    parser.add_argument("--cell14-run-id", required=True)
    parser.add_argument(
        "--cell14-manifest",
        type=Path,
        default=Path("manifests/releases/cell14_local_release_v1.json"),
    )
    parser.add_argument(
        "--frozen-manifest",
        type=Path,
        default=Path("manifests/releases/frozen_colab_manifest_v1.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/exploration/test2/g2"),
    )
    return parser


def _terminal_witness_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    counters = record.get("counters")
    preflight = record.get("preflight")
    if not isinstance(counters, dict) or not isinstance(preflight, dict):
        raise G2BoundaryError("G2 record witness sections are malformed")
    if counters != _ZERO_COUNTERS:
        raise G2BoundaryError("G2 terminal witness requires the exact zero counters")
    expected_statuses = {
        "decoded_content_status": "NOT_RECOMPUTED_METADATA_ONLY",
        "ordered_feature_content_status": "NOT_RECOMPUTED_METADATA_ONLY",
    }
    for key, expected in expected_statuses.items():
        if preflight.get(key) != expected:
            raise G2BoundaryError(f"G2 terminal witness status mismatch: {key}")
    if record.get("final_test_status") != "SEALED":
        raise G2BoundaryError("G2 terminal witness requires Final Test to remain sealed")
    if record.get("g3_status") != "NOT_AUTHORIZED":
        raise G2BoundaryError("G2 terminal witness requires G3 to remain unauthorized")
    return (
        "G2_METADATA_PREFLIGHT_PASS_NO_NUMERIC_ROW_VALUES_READ",
        f"NUMERIC_VALUES_READ={counters['numeric_values_read']}",
        f"PARQUET_ROW_GROUPS_READ={counters['parquet_row_groups_read']}",
        (
            "PARQUET_COLUMN_STATISTICS_READ="
            f"{counters['parquet_column_statistics_read']}"
        ),
        f"DECODED_CONTENT_STATUS={preflight['decoded_content_status']}",
        (
            "ORDERED_FEATURE_CONTENT_STATUS="
            f"{preflight['ordered_feature_content_status']}"
        ),
        f"TARGETS_CONSTRUCTED={counters['targets_constructed']}",
        f"REAL_MODELS_FITTED={counters['real_models_fitted']}",
        f"VALIDATION_ROWS_READ={counters['validation_rows_read']}",
        f"FINAL_TEST={record['final_test_status']}",
        f"G3_STATUS={record['g3_status']}",
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: str | Path | None = None,
) -> int:
    args = _parser().parse_args(argv)
    root = Path(project_root or Path.cwd()).expanduser().resolve()
    allowed_output_root = (root / "artifacts/exploration/test2/g2").resolve()
    output_root = (
        (root / args.output_root).resolve()
        if not args.output_root.is_absolute()
        else args.output_root.resolve()
    )
    if output_root != allowed_output_root:
        raise G2BoundaryError(
            f"G2 output_root must be exactly {allowed_output_root}"
        )
    code_identity, branch = _git_execution_context(root)
    paths = CanonicalArtifactPaths(
        raw_dbn=args.raw_dbn,
        cell8_assignments=args.cell8,
        cell10_labels=args.cell10,
        cell12_paths=args.cell12,
        cell14_features=args.cell14_features,
    )
    record = build_g2_metadata_preflight_record(
        paths,
        cell14_release_manifest_path=(root / args.cell14_manifest),
        frozen_colab_manifest_path=(root / args.frozen_manifest),
        cell14_run_id=args.cell14_run_id,
        code_identity=code_identity,
        branch=branch,
    )
    witness_lines = _terminal_witness_lines(record)
    output = write_g2_metadata_preflight_record(record, output_root=output_root)
    print(f"G2_RECORD={output}")
    print(f"G2_RECORD_SHA256={record['record_sha256']}")
    for line in witness_lines:
        print(line)
    return 0


__all__ = [
    "G2_ACCESS_LEVEL",
    "G2_ALLOWED_CHANGED_FILES",
    "G2_BASE_COMMIT",
    "G2_BRANCH",
    "G2_GATE_LITERAL",
    "G2BoundaryError",
    "build_g2_metadata_preflight_record",
    "main",
    "write_g2_metadata_preflight_record",
]

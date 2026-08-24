from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, NoReturn

import pyarrow.parquet as pq

from mes_quant.core.hashing import canonical_json_bytes, canonicalize_audit, sha256_bytes
from mes_quant.exploration.test3_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_FEATURE_FILE_SHA256,
    CELL14_ORDERED_FEATURE_SHA256,
    FOLD_ORDER,
    MODEL_COLUMNS,
    MODEL_ORDER,
    PROJECT_BUDGET_ID,
    PROJECT_BUDGET_SHA256,
    PROTOCOL_ID,
    PROTOCOL_SHA256,
    RATIFICATION_RECORD_COMMIT,
    RATIFIED_COMMIT,
    RAW_DBN_SHA256,
    TARGET_SPACE_ID,
    TARGET_SPACE_STATE,
)

G2_AUTHORIZATION_ID = "AUTH_TEST3_G2_METADATA_ONLY_20260824"
G2_AUTHORIZATION_TOKEN = "OWNER_AUTHORIZED_TEST3_G2_METADATA_ONLY_20260824"
G2_AUTHORIZATION_DOCUMENT_SHA256 = (
    "5b74295d9b14d3a7de1445b8b5baaa884bfdcdea92c62dfd376aa53d2aa7ea5e"
)
G2_AUTHORIZATION_DOCUMENT = (
    "docs/research/TEST3_G2_METADATA_PREFLIGHT_AUTHORIZATION_V1.md"
)
G2_GATE_LITERAL = "G2_TEST3_CANONICAL_METADATA_ONLY"
G2_GATE_ID = "MES_TEST3_G2_METADATA_PREFLIGHT_V1"
G2_RECORD_VERSION = "1.0"
G2_ACCESS_LEVEL = "G2_METADATA_ONLY_NO_NUMERIC_ROW_VALUES"
G2_BASE_COMMIT = "b16d025dd84b590a8a441c05232e6f761ee7f9bf"
G2_BRANCH = "research/test3-g2-metadata-preflight-v1"
G2_SOURCE_PR_NUMBER = 47
G2_SOURCE_PR_HEAD = RATIFICATION_RECORD_COMMIT

FROZEN_COLAB_MANIFEST_SHA256 = (
    "6f174e27ef6ccff9ce53d233469a47b0b1d12cb1c3fd23c263585935cc6eb15f"
)
CELL14_RELEASE_MANIFEST_SHA256 = (
    "74bd9d009cca43368488eea245b7b3b64918edc354091ba82172aaab6803a197"
)
DECODED_MES_1M_SHA256 = (
    "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584"
)
DECODED_MES_1M_ROW_COUNT = 2_551_123

G2_ALLOWED_CHANGED_FILES = frozenset(
    {
        G2_AUTHORIZATION_DOCUMENT,
        "docs/research/TEST3_G2_METADATA_PREFLIGHT_PACKAGE_V1.md",
        "src/mes_quant/exploration/test3_metadata_preflight.py",
        "tests/test_test3_metadata_preflight.py",
        "tools/run_test3_g2_metadata_preflight.py",
    }
)

_DOCUMENT_BINDINGS = {
    "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md": PROTOCOL_SHA256,
    "docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md": PROJECT_BUDGET_SHA256,
    "docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md": (
        "383243c73b3d4ba35878ff5119366e0c05dadd8e7ea32ec5bb90d3b2375675ec"
    ),
    "docs/research/TEST3_L0_CODE_ONLY_AUTHORIZATION_V1.md": (
        "5747fb5b58c528557e02692e574170a9deb5e53491243b10f14d56c580ba14ca"
    ),
    "docs/research/TEST3_L0_IMPLEMENTATION_PACKAGE_V1.md": (
        "e34a42c5fa34e0a1470e2e15539e3f60159ab4b9fcee485723d1ba2b6ac257e0"
    ),
    G2_AUTHORIZATION_DOCUMENT: G2_AUTHORIZATION_DOCUMENT_SHA256,
}

_CELL8_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
)
_CELL10_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "entry_reference_close",
    "exit_reference_close_60m",
)
_CELL12_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
)
_CELL14_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "realized_vol_60m",
    "realized_vol_120m",
    "realized_vol_240m",
    "minutes_since_nyse_open",
)


@dataclass(frozen=True)
class ArtifactSpec:
    artifact_id: str
    filename: str
    expected_sha256: str
    manifest_artifact_id: str
    required_columns: tuple[str, ...] = ()


_ARTIFACT_SPECS = (
    ArtifactSpec(
        "raw_dbn", "MES_2019_2026_1m.dbn.zst", RAW_DBN_SHA256, "raw_dbn"
    ),
    ArtifactSpec(
        "cell8_assignments",
        "cell8_purged_split_assignments_v1.parquet",
        CELL8_SPLIT_ASSIGNMENT_SHA256,
        "cell8_assignments",
        _CELL8_REQUIRED_COLUMNS,
    ),
    ArtifactSpec(
        "cell10_labels",
        "cell10_point_in_time_economic_labels_v1.parquet",
        CELL10_LABEL_SHA256,
        "cell10_labels",
        _CELL10_REQUIRED_COLUMNS,
    ),
    ArtifactSpec(
        "cell12_paths",
        "cell12_development_path_outcomes_v1.parquet",
        CELL12_PATH_SHA256,
        "cell12_paths",
        _CELL12_REQUIRED_COLUMNS,
    ),
    ArtifactSpec(
        "cell14_features",
        "cell14_development_point_in_time_features_v1.parquet",
        CELL14_FEATURE_FILE_SHA256,
        "features",
        _CELL14_REQUIRED_COLUMNS,
    ),
)

_SAFETY_COUNTERS = {
    "numeric_row_values_read": 0,
    "parquet_data_row_groups_read": 0,
    "parquet_row_group_objects_accessed": 0,
    "parquet_column_statistics_accessed": 0,
    "decoded_dbn_messages_read": 0,
    "g2p_train_predictor_rows_read": 0,
    "g2p_validation_predictor_rows_read": 0,
    "g2p_final_test_predictor_rows_read": 0,
    "g2p_target_or_path_rows_read": 0,
    "outer_train_target_rows_read": 0,
    "outer_validation_target_rows_read": 0,
    "final_test_target_rows_read": 0,
    "targets_constructed": 0,
    "real_fold_fit_calls": 0,
    "real_models_fitted": 0,
    "real_bootstrap_replicates": 0,
}

_NOT_COMPUTED = {
    "target_and_reason_counts": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "eligibility_and_reason_counts": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "fold_and_session_counts": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "target_and_request_hashes": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "fit_permits_and_completions": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "coefficient_identities": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "duan_factors": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "qlike_results": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "dependence_results": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "bootstrap_draw_identity": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "terminal_scientific_disposition": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
}

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
        "request_set_sha256",
        "target_sha256",
        "beta",
        "coefficient",
        "forecast",
    }
)

_AUTHORIZATION_KEY = object()


class Test3G2BoundaryError(RuntimeError):
    """Raised before Test 3 G2 could exceed metadata-only authority."""


@dataclass(frozen=True)
class _FileIdentity:
    device: int
    inode: int
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class _GitContext:
    code_identity: str
    tree_identity: str
    branch: str
    upstream_identity: str


@dataclass(frozen=True)
class _ObservedAuthorization:
    authorization_id: str
    document_sha256: str
    code_identity: str
    tree_identity: str
    reservation_path: Path
    reservation_file_sha256: str
    _verification_key: object


def _fail(message: str) -> NoReturn:
    raise Test3G2BoundaryError(message)


def _git_sha(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(f"{field} must be a lowercase 40-character Git SHA")
    return value


def _assert_authorization_token(token: str) -> None:
    if token != G2_AUTHORIZATION_TOKEN:
        _fail("Test 3 G2 Owner authorization token mismatch")


def _file_identity(value: os.stat_result) -> _FileIdentity:
    return _FileIdentity(value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


@contextmanager
def _open_regular_file(path: str | Path) -> Iterator[BinaryIO]:
    expanded = Path(path).expanduser()
    try:
        link_status = expanded.lstat()
    except OSError as exc:
        raise Test3G2BoundaryError(f"missing artifact: {path}") from exc
    if stat.S_ISLNK(link_status.st_mode):
        _fail(f"symlink artifacts are forbidden: {path}")
    candidate = expanded.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise Test3G2BoundaryError(f"cannot open artifact read-only: {path}") from exc
    stream = os.fdopen(descriptor, "rb", closefd=True)
    try:
        before_status = os.fstat(stream.fileno())
        if not stat.S_ISREG(before_status.st_mode):
            _fail(f"artifact is not a regular file: {path}")
        before = _file_identity(before_status)
        yield stream
        after = _file_identity(os.fstat(stream.fileno()))
        if after != before:
            _fail(f"artifact changed while inspected: {path}")
    finally:
        stream.close()


def _hash_stream(stream: BinaryIO) -> tuple[str, int]:
    stream.seek(0)
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        total += len(chunk)
    stream.seek(0)
    return digest.hexdigest(), total


def _hash_regular_file(path: str | Path) -> tuple[str, int]:
    with _open_regular_file(path) as stream:
        return _hash_stream(stream)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"manifest contains duplicate key: {key}")
        result[key] = value
    return result


def _read_manifest(
    path: str | Path, *, expected_sha256: str
) -> tuple[dict[str, object], int]:
    with _open_regular_file(path) as stream:
        observed, size = _hash_stream(stream)
        if observed != expected_sha256:
            _fail(f"manifest SHA-256 mismatch: {Path(path).name}")
        if size > 10 * 1024 * 1024:
            _fail("manifest exceeds bounded metadata size")
        payload = stream.read()
    try:
        parsed = json.loads(payload.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Test3G2BoundaryError("manifest is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        _fail("manifest root must be an object")
    return parsed, size


def _manifest_artifact_map(manifest: Mapping[str, object]) -> dict[str, dict[str, object]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        _fail("frozen manifest artifacts are malformed")
    result: dict[str, dict[str, object]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            _fail("frozen manifest artifact is malformed")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or artifact_id in result:
            _fail("frozen manifest artifact IDs are malformed")
        result[artifact_id] = artifact
    return result


def _inspect_artifact(path: Path, spec: ArtifactSpec) -> dict[str, object]:
    if path.name != spec.filename:
        _fail(f"{spec.artifact_id} requires filename {spec.filename}")
    with _open_regular_file(path) as stream:
        observed_sha256, size_bytes = _hash_stream(stream)
        if observed_sha256 != spec.expected_sha256:
            _fail(f"{spec.artifact_id} SHA-256 mismatch")
        schema: tuple[str, ...] = ()
        num_rows: int | None = None
        num_row_groups: int | None = None
        if spec.required_columns:
            stream.seek(0)
            parquet = pq.ParquetFile(stream)
            schema = tuple(parquet.schema_arrow.names)
            missing = sorted(set(spec.required_columns).difference(schema))
            if missing:
                _fail(f"{spec.artifact_id} footer lacks: {', '.join(missing)}")
            num_rows = int(parquet.metadata.num_rows)
            num_row_groups = int(parquet.metadata.num_row_groups)
            if num_rows < 0 or num_row_groups < 0:
                _fail(f"{spec.artifact_id} footer counts are invalid")
    return {
        "artifact_id": spec.artifact_id,
        "path": f"${{MES_G2_ARTIFACTS}}/{spec.artifact_id}/{spec.filename}",
        "byte_sha256": observed_sha256,
        "size_bytes": size_bytes,
        "parquet_schema_names": list(schema),
        "parquet_total_rows": num_rows,
        "parquet_total_row_groups": num_row_groups,
        "manifest_artifact_id": spec.manifest_artifact_id,
        "footer_scope": "SCHEMA_NAMES_TOTAL_ROWS_TOTAL_ROW_GROUPS_ONLY",
    }


def _binding(expected: str, observed: object, *, field: str) -> dict[str, object]:
    if observed != expected:
        _fail(f"{field} identity mismatch")
    return {"expected": expected, "observed": observed, "match": True}


def _verify_document_bindings(project_root: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for relative_path, expected in _DOCUMENT_BINDINGS.items():
        observed, _size = _hash_regular_file(project_root / relative_path)
        result[relative_path] = {
            **_binding(expected, observed, field=relative_path),
            "binding_status": "PINNED_BEFORE_METADATA_ACCESS",
        }
    return result


def _verify_manifests(
    *,
    project_root: Path,
    frozen_manifest_path: Path,
    cell14_manifest_path: Path,
    cell14_run_id: str,
    artifacts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    expected_frozen = (
        project_root / "manifests/releases/frozen_colab_manifest_v1.json"
    ).resolve()
    expected_cell14 = (
        project_root / "manifests/releases/cell14_local_release_v1.json"
    ).resolve()
    if frozen_manifest_path.expanduser().resolve() != expected_frozen:
        _fail("frozen manifest must use the exact repository path")
    if cell14_manifest_path.expanduser().resolve() != expected_cell14:
        _fail("Cell 14 manifest must use the exact repository path")
    frozen, frozen_size = _read_manifest(
        frozen_manifest_path, expected_sha256=FROZEN_COLAB_MANIFEST_SHA256
    )
    release, release_size = _read_manifest(
        cell14_manifest_path, expected_sha256=CELL14_RELEASE_MANIFEST_SHA256
    )
    observed = {str(item["artifact_id"]): item for item in artifacts}
    frozen_artifacts = _manifest_artifact_map(frozen)
    for spec in _ARTIFACT_SPECS[:4]:
        declaration = frozen_artifacts.get(spec.manifest_artifact_id)
        if not isinstance(declaration, dict):
            _fail(f"frozen manifest lacks {spec.manifest_artifact_id}")
        if declaration.get("file") != spec.filename:
            _fail(f"frozen manifest filename mismatch: {spec.artifact_id}")
        _binding(
            spec.expected_sha256,
            declaration.get("sha256"),
            field=f"frozen manifest {spec.artifact_id}",
        )
        _binding(
            spec.expected_sha256,
            observed[spec.artifact_id].get("byte_sha256"),
            field=f"observed {spec.artifact_id}",
        )
    decoded = frozen_artifacts.get("decoded_memory_content")
    if not isinstance(decoded, dict):
        _fail("frozen manifest lacks decoded-memory identity")
    _binding(
        DECODED_MES_1M_SHA256,
        decoded.get("sha256"),
        field="declared decoded MES 1m content",
    )
    golden_counts = frozen.get("golden_counts")
    if not isinstance(golden_counts, dict):
        _fail("frozen manifest lacks golden counts")
    if golden_counts.get("raw_rows") != DECODED_MES_1M_ROW_COUNT:
        _fail("frozen manifest decoded row-count declaration mismatch")

    controls = release.get("controls")
    frozen_control = controls.get("frozen_colab_manifest") if isinstance(controls, dict) else None
    if not isinstance(frozen_control, dict):
        _fail("Cell 14 release lacks frozen-manifest control")
    _binding(
        FROZEN_COLAB_MANIFEST_SHA256,
        frozen_control.get("sha256"),
        field="Cell 14 frozen-manifest control",
    )
    canonical_run_id = release.get("canonical_run_id")
    replay_run_id = release.get("replay_run_id")
    if cell14_run_id not in {canonical_run_id, replay_run_id}:
        _fail("Cell 14 run is neither canonical nor replay")
    role = "canonical" if cell14_run_id == canonical_run_id else "replay"
    runs = release.get("runs")
    run = runs.get(role) if isinstance(runs, dict) else None
    run_artifacts = run.get("artifacts") if isinstance(run, dict) else None
    feature = run_artifacts.get("features") if isinstance(run_artifacts, dict) else None
    if not isinstance(feature, dict) or run.get("run_id") != cell14_run_id:
        _fail("Cell 14 selected-run declaration is malformed")
    expected_feature_path = (
        f"artifacts/runs/{cell14_run_id}/"
        "cell14_development_point_in_time_features_v1.parquet"
    )
    if feature.get("file") != expected_feature_path:
        _fail("Cell 14 selected feature path mismatch")
    _binding(
        CELL14_FEATURE_FILE_SHA256,
        feature.get("sha256"),
        field="Cell 14 feature bytes",
    )
    _binding(
        CELL14_ORDERED_FEATURE_SHA256,
        feature.get("content_sha256"),
        field="Cell 14 ordered feature declaration",
    )
    _binding(
        CELL14_FEATURE_FILE_SHA256,
        observed["cell14_features"].get("byte_sha256"),
        field="observed Cell 14 feature bytes",
    )
    return {
        "frozen_colab_manifest": {
            "path": "${REPOSITORY}/manifests/releases/frozen_colab_manifest_v1.json",
            "byte_sha256": FROZEN_COLAB_MANIFEST_SHA256,
            "size_bytes": frozen_size,
        },
        "cell14_release_manifest": {
            "path": "${REPOSITORY}/manifests/releases/cell14_local_release_v1.json",
            "byte_sha256": CELL14_RELEASE_MANIFEST_SHA256,
            "size_bytes": release_size,
        },
        "decoded_mes_1m": {
            "content_sha256_declared": DECODED_MES_1M_SHA256,
            "row_count_declared": DECODED_MES_1M_ROW_COUNT,
            "status": "DECLARED_NOT_RECOMPUTED_METADATA_ONLY",
        },
        "cell14_run": {
            "canonical_run_id": canonical_run_id,
            "replay_run_id": replay_run_id,
            "selected_run_id": cell14_run_id,
            "selected_role": role,
            "ordered_feature_content_sha256_declared": (
                CELL14_ORDERED_FEATURE_SHA256
            ),
            "status": "DECLARED_NOT_RECOMPUTED_METADATA_ONLY",
        },
    }


def _loaded_modules(prefix: str) -> tuple[str, ...]:
    return tuple(
        sorted(name for name in sys.modules if name == prefix or name.startswith(prefix + "."))
    )


def _assert_forbidden_modules_absent(*, phase: str) -> None:
    forbidden_prefixes = (
        "databento",
        "databento_dbn",
        "mes_quant.exploration.test2_l1_harness",
        "mes_quant.exploration.test3_target",
        "mes_quant.exploration.test3_design",
        "mes_quant.exploration.test3_stats",
        "mes_quant.exploration.l1_lr001",
        "mes_quant.exploration.l1_tree001",
    )
    loaded = tuple(
        module for prefix in forbidden_prefixes for module in _loaded_modules(prefix)
    )
    if loaded:
        _fail(f"forbidden modules loaded during {phase}: {', '.join(loaded)}")


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
        _fail("G2 record contains forbidden scientific/value fields: " + ", ".join(forbidden))
    if record.get("safety_counters") != _SAFETY_COUNTERS:
        _fail("G2 record requires exact zero safety counters")
    if record.get("not_computed") != _NOT_COMPUTED:
        _fail("G2 record must preserve explicit not-computed dispositions")


def _record_sha256(record: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


def _assert_observed_authorization(
    authorization: _ObservedAuthorization,
    *,
    code_identity: str,
    tree_identity: str,
) -> None:
    if (
        not isinstance(authorization, _ObservedAuthorization)
        or authorization._verification_key is not _AUTHORIZATION_KEY
        or authorization.authorization_id != G2_AUTHORIZATION_ID
        or authorization.document_sha256 != G2_AUTHORIZATION_DOCUMENT_SHA256
        or authorization.code_identity != code_identity
        or authorization.tree_identity != tree_identity
    ):
        _fail("G2 requires a verified, consumed Owner authorization")


def build_g2_metadata_preflight_record(
    artifact_paths: Mapping[str, Path],
    *,
    project_root: str | Path,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
    cell14_run_id: str,
    git_context: _GitContext,
    authorization: _ObservedAuthorization,
    document_bindings: Mapping[str, object],
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    """Build aggregate Test 3 G2 evidence without decoding a row value."""

    _assert_observed_authorization(
        authorization,
        code_identity=git_context.code_identity,
        tree_identity=git_context.tree_identity,
    )
    if git_context.branch != G2_BRANCH:
        _fail(f"G2 must execute on branch {G2_BRANCH}")
    if set(artifact_paths) != {spec.artifact_id for spec in _ARTIFACT_SPECS}:
        _fail("G2 requires the exact five canonical artifact paths")
    _assert_forbidden_modules_absent(phase="G2 entry")
    artifacts = [
        _inspect_artifact(Path(artifact_paths[spec.artifact_id]), spec)
        for spec in _ARTIFACT_SPECS
    ]
    manifest_bindings = _verify_manifests(
        project_root=Path(project_root).expanduser().resolve(),
        frozen_manifest_path=Path(frozen_colab_manifest_path),
        cell14_manifest_path=Path(cell14_release_manifest_path),
        cell14_run_id=cell14_run_id,
        artifacts=artifacts,
    )
    _assert_forbidden_modules_absent(phase="G2 exit")

    record_core: dict[str, object] = {
        "gate_id": G2_GATE_ID,
        "record_version": G2_RECORD_VERSION,
        "protocol_id": PROTOCOL_ID,
        "project_budget_id": PROJECT_BUDGET_ID,
        "target_space_id": TARGET_SPACE_ID,
        "target_space_state": TARGET_SPACE_STATE,
        "ratified_commit": RATIFIED_COMMIT,
        "ratification_record_commit": RATIFICATION_RECORD_COMMIT,
        "base_commit": G2_BASE_COMMIT,
        "execution_commit": git_context.code_identity,
        "execution_tree": git_context.tree_identity,
        "branch": git_context.branch,
        "upstream_commit": git_context.upstream_identity,
        "local_upstream_equal": git_context.code_identity == git_context.upstream_identity,
        "access_level": G2_ACCESS_LEVEL,
        "status": "PASS",
        "authorization_binding": {
            "authorization_id": authorization.authorization_id,
            "authorization_document_sha256": authorization.document_sha256,
            "authorization_token_sha256": hashlib.sha256(
                G2_AUTHORIZATION_TOKEN.encode("utf-8")
            ).hexdigest(),
            "reservation_path": (
                "${REPOSITORY}/artifacts/exploration/test3/g2/authorization/"
                + authorization.reservation_path.name
            ),
            "reservation_file_sha256": authorization.reservation_file_sha256,
            "reservation_status": "CONSUMED_BEFORE_ARTIFACT_ACCESS",
            "document_bindings": dict(document_bindings),
        },
        "repository_strategy": {
            "source_pr_number": G2_SOURCE_PR_NUMBER,
            "source_pr_head_commit": G2_SOURCE_PR_HEAD,
            "source_pr_state_at_authorization": "OPEN_DRAFT_UNMERGED",
            "execution_strategy": "DIRECT_DESCENDANT_BRANCH_NO_MERGE",
            "merge_authorized": False,
            "changed_file_allowlist": sorted(G2_ALLOWED_CHANGED_FILES),
        },
        "frozen_definitions": {
            "predictor_order": [
                "realized_vol_60m",
                "realized_vol_120m",
                "realized_vol_240m",
            ],
            "model_order": list(MODEL_ORDER),
            "model_columns": {model: list(MODEL_COLUMNS[model]) for model in MODEL_ORDER},
            "fold_order": list(FOLD_ORDER),
            "definition_status": "FROZEN_NOT_EVALUATED_METADATA_ONLY",
        },
        "artifacts": artifacts,
        "manifest_bindings": manifest_bindings,
        "allowed_metadata_counters": {
            "artifact_byte_hashes_computed": len(artifacts),
            "manifest_files_parsed": 2,
            "parquet_footers_opened": sum(
                item["parquet_total_rows"] is not None for item in artifacts
            ),
            "parquet_total_row_groups_declared": sum(
                int(item["parquet_total_row_groups"] or 0) for item in artifacts
            ),
        },
        "safety_counters": dict(_SAFETY_COUNTERS),
        "not_computed": dict(_NOT_COMPUTED),
        "decoded_content_status": "DECLARED_NOT_RECOMPUTED_METADATA_ONLY",
        "ordered_feature_content_status": "DECLARED_NOT_RECOMPUTED_METADATA_ONLY",
        "target_space_consumption_status": "NOT_CONSUMED_METADATA_ONLY",
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "live_execution_status": "DISABLED",
        "g2p_status": "NOT_AUTHORIZED",
        "g3p_status": "NOT_AUTHORIZED",
        "g3f_status": "NOT_AUTHORIZED",
    }
    run_seed = sha256_bytes(canonical_json_bytes(canonicalize_audit(record_core)))
    record = {
        **record_core,
        "run_id": f"MES_T3_G2_{run_seed[:16].upper()}",
        "audit_written_utc": audit_written_utc
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _assert_closed_record(record)
    record["record_sha256"] = _record_sha256(record)
    return record


def _atomic_create_json(path: Path, payload: Mapping[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                _fail("create-once evidence write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    observed, _size = _hash_regular_file(path)
    return observed


def _consume_authorization(
    *,
    project_root: Path,
    output_root: Path,
    git_context: _GitContext,
    authorization_token: str,
) -> _ObservedAuthorization:
    _assert_authorization_token(authorization_token)
    observed, _size = _hash_regular_file(project_root / G2_AUTHORIZATION_DOCUMENT)
    _binding(
        G2_AUTHORIZATION_DOCUMENT_SHA256,
        observed,
        field="G2 Owner authorization document",
    )
    reservation_path = (
        output_root
        / "authorization"
        / f"{G2_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
    )
    reservation = {
        "authorization_id": G2_AUTHORIZATION_ID,
        "authorization_document_sha256": G2_AUTHORIZATION_DOCUMENT_SHA256,
        "execution_commit": git_context.code_identity,
        "execution_tree": git_context.tree_identity,
        "branch": git_context.branch,
        "status": "CONSUMED_BEFORE_ARTIFACT_ACCESS",
        "consumed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    try:
        reservation_sha256 = _atomic_create_json(reservation_path, reservation)
    except FileExistsError as exc:
        raise Test3G2BoundaryError("Test 3 G2 authorization is already consumed") from exc
    return _ObservedAuthorization(
        authorization_id=G2_AUTHORIZATION_ID,
        document_sha256=G2_AUTHORIZATION_DOCUMENT_SHA256,
        code_identity=git_context.code_identity,
        tree_identity=git_context.tree_identity,
        reservation_path=reservation_path,
        reservation_file_sha256=reservation_sha256,
        _verification_key=_AUTHORIZATION_KEY,
    )


def write_failure_summary_if_consumed(
    *,
    project_root: str | Path,
    error: BaseException,
) -> Path | None:
    """Create a scrubbed durable summary only after the reservation exists."""

    root = Path(project_root).expanduser().resolve()
    authorization_root = root / "artifacts/exploration/test3/g2/authorization"
    reservation = authorization_root / (
        f"{G2_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
    )
    if not reservation.is_file():
        return None
    failure = authorization_root / (
        f"{G2_AUTHORIZATION_DOCUMENT_SHA256}.failure.json"
    )
    payload = {
        "authorization_id": G2_AUTHORIZATION_ID,
        "authorization_document_sha256": G2_AUTHORIZATION_DOCUMENT_SHA256,
        "error_class": type(error).__name__,
        "status": "FAILED_AFTER_AUTHORIZATION_CONSUMPTION_NO_RETRY",
        "failed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "raw_error_message_committed": False,
    }
    try:
        _atomic_create_json(failure, payload)
    except FileExistsError:
        pass
    return failure


def write_g2_metadata_preflight_record(
    record: Mapping[str, object], *, output_root: str | Path
) -> tuple[Path, str]:
    _assert_closed_record(record)
    if record.get("record_sha256") != _record_sha256(record):
        _fail("G2 record semantic SHA-256 mismatch before publication")
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("MES_T3_G2_"):
        _fail("G2 record has a malformed run_id")
    root = Path(output_root).expanduser().resolve()
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    output = run_dir / "metadata_preflight_record.json"
    descriptor = -1
    temporary_output: Path | None = None
    published = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".metadata_preflight_record.", suffix=".tmp", dir=run_dir
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
        with _open_regular_file(output) as stream:
            file_sha256, _size = _hash_stream(stream)
            parsed = json.loads(
                stream.read().decode("utf-8"), object_pairs_hook=_strict_object
            )
        if not isinstance(parsed, dict) or parsed.get("record_sha256") != _record_sha256(parsed):
            _fail("published G2 record failed semantic reread verification")
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
    return output, file_sha256


def _git_output(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _assert_no_untracked_import_surface(project_root: Path) -> None:
    tracked = frozenset(
        filter(
            None,
            _git_output(
                project_root, "ls-files", "--", "src", "tests", "tools"
            ).splitlines(),
        )
    )
    candidates: set[str] = set()
    for args in (
        ("ls-files", "--others", "--exclude-standard", "--", "src", "tests", "tools"),
        (
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--",
            "src",
            "tests",
            "tools",
        ),
    ):
        candidates.update(filter(None, _git_output(project_root, *args).splitlines()))
    importable_suffixes = {".py", ".pyc", ".pyo", ".so", ".dylib", ".pth"}

    def is_tracked_source_cache(path: str) -> bool:
        candidate = Path(path)
        if candidate.suffix != ".pyc" or candidate.parent.name != "__pycache__":
            return False
        module_name = candidate.name.split(".", 1)[0]
        source = candidate.parent.parent / f"{module_name}.py"
        return source.as_posix() in tracked

    importable = sorted(
        path
        for path in candidates
        if Path(path).suffix in importable_suffixes
        and not is_tracked_source_cache(path)
    )
    if importable:
        _fail(f"untracked or ignored importable code present: {importable}")


def _git_execution_context(project_root: Path) -> _GitContext:
    branch = _git_output(project_root, "branch", "--show-current")
    if branch != G2_BRANCH:
        _fail(f"G2 must execute on branch {G2_BRANCH}")
    code_identity = _git_sha(_git_output(project_root, "rev-parse", "HEAD"), field="HEAD")
    tree_identity = _git_sha(
        _git_output(project_root, "rev-parse", "HEAD^{tree}"), field="HEAD tree"
    )
    commit_count = _git_output(
        project_root, "rev-list", "--count", f"{G2_BASE_COMMIT}..{code_identity}"
    )
    if commit_count != "1":
        _fail("G2 execution commit must be the single direct child of the authorized base")
    head_with_parents = _git_output(
        project_root, "rev-list", "--parents", "-n", "1", code_identity
    ).split()
    if head_with_parents != [code_identity, G2_BASE_COMMIT]:
        _fail("G2 execution commit must have exactly the authorized base as its parent")
    for ancestor_identity, label in (
        (RATIFIED_COMMIT, "ratified protocol commit"),
        (RATIFICATION_RECORD_COMMIT, "ratification record commit"),
        (G2_BASE_COMMIT, "authorized G2 base"),
    ):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor_identity, code_identity],
            cwd=project_root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            _fail(f"G2 code identity lacks {label} ancestry")
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
        _fail(f"G2 changed-file firewall mismatch; unexpected={unexpected}; missing={missing}")
    tracked_status = _git_output(
        project_root, "status", "--porcelain=v1", "--untracked-files=no"
    )
    if tracked_status:
        _fail("G2 execution requires a clean tracked worktree")
    _assert_no_untracked_import_surface(project_root)
    try:
        upstream_identity = _git_sha(
            _git_output(project_root, "rev-parse", "@{upstream}"), field="upstream"
        )
    except subprocess.CalledProcessError as exc:
        raise Test3G2BoundaryError("G2 branch must have a pushed upstream") from exc
    if upstream_identity != code_identity:
        _fail("G2 local and upstream code identities must match")
    upstream_reference = _git_output(
        project_root, "rev-parse", "--symbolic-full-name", "@{upstream}"
    )
    expected_upstream = f"refs/remotes/origin/{G2_BRANCH}"
    if upstream_reference != expected_upstream:
        _fail(f"G2 upstream must be exactly {expected_upstream}")
    return _GitContext(code_identity, tree_identity, branch, upstream_identity)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Owner-authorized Test 3 G2 metadata-only preflight."
    )
    parser.add_argument("--gate", choices=(G2_GATE_LITERAL,), required=True)
    parser.add_argument("--authorization-token", required=True)
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
        default=Path("artifacts/exploration/test3/g2"),
    )
    return parser


def _terminal_witness_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    counters = record.get("safety_counters")
    if counters != _SAFETY_COUNTERS:
        _fail("G2 witness requires exact zero safety counters")
    expected = {
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "live_execution_status": "DISABLED",
        "g2p_status": "NOT_AUTHORIZED",
        "g3p_status": "NOT_AUTHORIZED",
        "g3f_status": "NOT_AUTHORIZED",
    }
    for field, value in expected.items():
        if record.get(field) != value:
            _fail(f"G2 witness status mismatch: {field}")
    return (
        "TEST3_G2_METADATA_PREFLIGHT_PASS_NO_NUMERIC_ROW_VALUES_READ",
        f"NUMERIC_ROW_VALUES_READ={counters['numeric_row_values_read']}",
        f"PARQUET_DATA_ROW_GROUPS_READ={counters['parquet_data_row_groups_read']}",
        (
            "PARQUET_ROW_GROUP_OBJECTS_ACCESSED="
            f"{counters['parquet_row_group_objects_accessed']}"
        ),
        (
            "PARQUET_COLUMN_STATISTICS_ACCESSED="
            f"{counters['parquet_column_statistics_accessed']}"
        ),
        f"DECODED_DBN_MESSAGES_READ={counters['decoded_dbn_messages_read']}",
        f"G2P_TRAIN_PREDICTOR_ROWS_READ={counters['g2p_train_predictor_rows_read']}",
        (
            "G2P_VALIDATION_PREDICTOR_ROWS_READ="
            f"{counters['g2p_validation_predictor_rows_read']}"
        ),
        (
            "G2P_FINAL_TEST_PREDICTOR_ROWS_READ="
            f"{counters['g2p_final_test_predictor_rows_read']}"
        ),
        f"G2P_TARGET_OR_PATH_ROWS_READ={counters['g2p_target_or_path_rows_read']}",
        f"OUTER_TRAIN_TARGET_ROWS_READ={counters['outer_train_target_rows_read']}",
        (
            "OUTER_VALIDATION_TARGET_ROWS_READ="
            f"{counters['outer_validation_target_rows_read']}"
        ),
        f"FINAL_TEST_TARGET_ROWS_READ={counters['final_test_target_rows_read']}",
        f"TARGETS_CONSTRUCTED={counters['targets_constructed']}",
        f"REAL_FOLD_FIT_CALLS={counters['real_fold_fit_calls']}",
        f"REAL_MODELS_FITTED={counters['real_models_fitted']}",
        f"REAL_BOOTSTRAP_REPLICATES={counters['real_bootstrap_replicates']}",
        f"VALIDATION_STATUS={record['validation_status']}",
        f"FINAL_TEST_STATUS={record['final_test_status']}",
        f"LIVE_EXECUTION_STATUS={record['live_execution_status']}",
        f"G2P_STATUS={record['g2p_status']}",
        f"G3P_STATUS={record['g3p_status']}",
        f"G3F_STATUS={record['g3f_status']}",
    )


def main(
    argv: Sequence[str] | None = None, *, project_root: str | Path | None = None
) -> int:
    args = _parser().parse_args(argv)
    _assert_authorization_token(args.authorization_token)
    root = Path(project_root or Path.cwd()).expanduser().resolve()
    allowed_output_root = (root / "artifacts/exploration/test3/g2").resolve()
    output_root = (
        (root / args.output_root).resolve()
        if not args.output_root.is_absolute()
        else args.output_root.resolve()
    )
    if output_root != allowed_output_root:
        _fail(f"G2 output_root must be exactly {allowed_output_root}")
    git_context = _git_execution_context(root)
    document_bindings = _verify_document_bindings(root)
    _assert_forbidden_modules_absent(phase="pre-reservation")
    authorization = _consume_authorization(
        project_root=root,
        output_root=output_root,
        git_context=git_context,
        authorization_token=args.authorization_token,
    )
    paths = {
        "raw_dbn": args.raw_dbn,
        "cell8_assignments": args.cell8,
        "cell10_labels": args.cell10,
        "cell12_paths": args.cell12,
        "cell14_features": args.cell14_features,
    }
    record = build_g2_metadata_preflight_record(
        paths,
        project_root=root,
        cell14_release_manifest_path=root / args.cell14_manifest,
        frozen_colab_manifest_path=root / args.frozen_manifest,
        cell14_run_id=args.cell14_run_id,
        git_context=git_context,
        authorization=authorization,
        document_bindings=document_bindings,
    )
    witness_lines = _terminal_witness_lines(record)
    output, file_sha256 = write_g2_metadata_preflight_record(
        record, output_root=output_root
    )
    print(f"G2_RECORD={output}")
    print(f"G2_RECORD_SHA256={record['record_sha256']}")
    print(f"G2_RECORD_FILE_SHA256={file_sha256}")
    print(f"G2_AUTHORIZATION_RESERVATION={authorization.reservation_path}")
    print(f"G2_AUTHORIZATION_RESERVATION_SHA256={authorization.reservation_file_sha256}")
    for line in witness_lines:
        print(line)
    return 0


__all__ = [
    "G2_ALLOWED_CHANGED_FILES",
    "G2_AUTHORIZATION_ID",
    "G2_AUTHORIZATION_TOKEN",
    "G2_BASE_COMMIT",
    "G2_BRANCH",
    "G2_GATE_LITERAL",
    "Test3G2BoundaryError",
    "build_g2_metadata_preflight_record",
    "main",
    "write_failure_summary_if_consumed",
    "write_g2_metadata_preflight_record",
]

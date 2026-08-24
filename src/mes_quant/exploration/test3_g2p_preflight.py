from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, NoReturn

import pyarrow as pa
import pyarrow.parquet as pq

from mes_quant.core import hashing as hashing_module
from mes_quant.core.hashing import canonical_json_bytes, canonicalize_audit, sha256_bytes
from mes_quant.exploration import test3_contract as contract_module
from mes_quant.exploration.test3_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL14_FEATURE_FILE_SHA256,
    CELL14_ORDERED_FEATURE_SHA256,
    PROJECT_BUDGET_ID,
    PROJECT_BUDGET_SHA256,
    PROTOCOL_ID,
    PROTOCOL_SHA256,
    RATIFICATION_RECORD_COMMIT,
    RATIFIED_COMMIT,
    TARGET_SPACE_ID,
    TARGET_SPACE_STATE,
    FailureReason,
    RowStatus,
)

G2P_AUTHORIZATION_ID = "AUTH_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824"
G2P_AUTHORIZATION_TOKEN = (
    "OWNER_AUTHORIZED_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824"
)
G2P_AUTHORIZATION_DOCUMENT = (
    "docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_AUTHORIZATION_V1.md"
)
G2P_AUTHORIZATION_DOCUMENT_SHA256 = (
    "6042c4e6b9fff928facb41dc5fba2997908bfd7aefb0f6714fd6d9b0630fadcc"
)
G2P_PACKAGE_DOCUMENT = (
    "docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_PACKAGE_V1.md"
)
G2P_PACKAGE_DOCUMENT_SHA256 = (
    "537d89621786bf8588131db04021194a8286fc4eb53286faae226276f03b1b8f"
)
G2P_REPAIR_AMENDMENT_DOCUMENT = (
    "docs/research/TEST3_G2P_PROVEN_DEFECT_REPAIR_AMENDMENT_V1.md"
)
G2P_REPAIR_AMENDMENT_DOCUMENT_SHA256 = (
    "135fed474c115269421bf9f59cf838f58609b4d6cf83aee2a2118b195cb13fa6"
)
G2P_PROOF_TEST = "tests/test_test3_g2p_proven_defect.py"
G2P_PROOF_TEST_SHA256 = (
    "ffe8a2c18f034a8c5280bba488cbb11a2dbcac617284e1be0a268d717ef19b4c"
)
G2P_GATE_LITERAL = "G2P_TEST3_SINGLE_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT"
G2P_GATE_ID = "MES_TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT_V1"
G2P_RECORD_VERSION = "1.0"
G2P_ACCESS_LEVEL = "G2P_TARGET_BLIND_OUTER_TRAIN_PREDICTORS_ONLY"
G2P_REPAIR_LINEAGE_ID = "MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1"
G2P_SUCCESSOR_ORDINAL = 1
G2P_SUCCESSOR_LIMIT = 1
LEDGER_HASH_PROJECTION_ID = "MES_TEST3_PREDICTOR_LEDGER_PIPE_UTF8_V1"
LEDGER_HASH_SERIALIZATION = (
    "UTF8_SOURCE_ORDER_DECISION_ID_PIPE_UTC_ISOFORMAT_PLUS_OPTIONAL_STATUS_LF"
)
G2P_BASE_COMMIT = "2d4fccf4ac2040e8e908bfadda27b81b3663afad"
G2P_BASE_TREE = "9b07390a40a4720fe0a64c97cb982cf0345a8207"
G2P_BRANCH = "research/test3-g2p-proven-defect-successor-v1"

G2P_PREDECESSOR_PACKAGE_COMMIT = "485bfa16a6567b5c54e91b7cc72e7f1be58775a9"
G2P_PREDECESSOR_PACKAGE_TREE = "86e7f382586d0155ec058a148a83be858768cf4d"
G2P_PREDECESSOR_EVIDENCE_COMMIT = "f0a3387f077ac30c99287601adeb81014068ff08"
G2P_PREDECESSOR_EVIDENCE_TREE = "ac415152ba6eca60c50907c7fe1dc42460bf7a4b"
G2P_PREDECESSOR_AUTHORIZATION_ID = (
    "AUTH_TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_20260824"
)
G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT = (
    "docs/research/TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_AUTHORIZATION_V1.md"
)
G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256 = (
    "2651c917a1480a74dfa7300cc6b11a3208828b41b74f726240224dcb783cce98"
)
G2P_PREDECESSOR_PACKAGE_DOCUMENT = (
    "docs/research/TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_PACKAGE_V1.md"
)
G2P_PREDECESSOR_PACKAGE_DOCUMENT_SHA256 = (
    "584cd0623463e79803b69df15646e9e30db1a78944e067d0bff87d69409b11c2"
)
G2P_PREDECESSOR_RESERVATION_RECORD = (
    "artifacts/exploration/test3/g2p/authorization/"
    f"{G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
)
G2P_PREDECESSOR_RESERVATION_SHA256 = (
    "2cf1ce922a012045af9959265b613df662727e268c8797f9555ee19072c9c68c"
)
G2P_PREDECESSOR_FAILURE_RECORD = (
    "artifacts/exploration/test3/g2p/authorization/"
    f"{G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256}.failure.json"
)
G2P_PREDECESSOR_FAILURE_SHA256 = (
    "9b9f7f7824c89af2fa32de3cda00cfa38a519795a6c88bae6a6201d89717a439"
)
G2P_REPAIR_RESERVATION_RECORD = (
    "artifacts/exploration/test3/g2p/repair/"
    f"{G2P_REPAIR_LINEAGE_ID}.consumed.json"
)
G2P_REPAIR_FAILURE_RECORD = (
    "artifacts/exploration/test3/g2p/repair/"
    f"{G2P_REPAIR_LINEAGE_ID}.failure.json"
)

G2_IMPLEMENTATION_COMMIT = "4572b97c577f4445641f2b0e0b84549b0ae1b78c"
G2_EVIDENCE_COMMIT = "21c42de47deeb8fac1da9208fdbc8ad4fa6369ca"
G2_EVIDENCE_RECORD = (
    "artifacts/exploration/test3/g2/MES_T3_G2_0F9A89A4A5C74EAD/"
    "metadata_preflight_record.json"
)
G2_EVIDENCE_RECORD_SHA256 = (
    "ef8d24d59dd5fcc6a36fba7766c9237f19e31db52ca3c9d67a700a5d41198cf6"
)
G2_EVIDENCE_SEMANTIC_SHA256 = (
    "3d87467c273847a8a8443bb2d535a5c1c7ecca50a0370f731ad6d688f81fad52"
)
G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256 = (
    "5b74295d9b14d3a7de1445b8b5baaa884bfdcdea92c62dfd376aa53d2aa7ea5e"
)
G2_RESERVATION_RECORD = (
    "artifacts/exploration/test3/g2/authorization/"
    f"{G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
)
G2_RESERVATION_FILE_SHA256 = (
    "0b8f019a20d5af2d2b4e65ab2bfcd402340ffe31413fe7a3adc060fb52efb696"
)

CELL8_FILENAME = "cell8_purged_split_assignments_v1.parquet"
CELL14_FILENAME = "cell14_development_point_in_time_features_v1.parquet"
CELL8_CANONICAL_RELATIVE_PATH = "artifacts/cache/source_v1/" + CELL8_FILENAME
CELL14_CANONICAL_RELATIVE_PATH = (
    "artifacts/runs/cell14_20260809T175203Z/" + CELL14_FILENAME
)
EXPECTED_OUTER_TRAIN_ROWS = 25_685
OUTER_VALIDATION_BOUNDARY_UTC = datetime(2024, 1, 2, 14, 45, tzinfo=UTC)

CONTROL_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
)
PREDICTOR_COLUMNS = (
    "realized_vol_60m",
    "realized_vol_120m",
    "realized_vol_240m",
)

G2P_ALLOWED_CHANGED_FILES = frozenset(
    {
        G2P_AUTHORIZATION_DOCUMENT,
        G2P_PACKAGE_DOCUMENT,
        "src/mes_quant/exploration/test3_g2p_preflight.py",
        "tests/test_test3_g2p_preflight.py",
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
    "docs/research/TEST3_G2_METADATA_PREFLIGHT_AUTHORIZATION_V1.md": (
        G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256
    ),
    "docs/research/TEST3_G2_METADATA_PREFLIGHT_PACKAGE_V1.md": (
        "3d0926a2fd7dc63d2b50cea8cc653921c4a936de9cc83c410147195a7eb390b1"
    ),
    G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT: (
        G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256
    ),
    G2P_PREDECESSOR_PACKAGE_DOCUMENT: G2P_PREDECESSOR_PACKAGE_DOCUMENT_SHA256,
    G2P_REPAIR_AMENDMENT_DOCUMENT: G2P_REPAIR_AMENDMENT_DOCUMENT_SHA256,
    G2P_PROOF_TEST: G2P_PROOF_TEST_SHA256,
    G2P_AUTHORIZATION_DOCUMENT: G2P_AUTHORIZATION_DOCUMENT_SHA256,
    G2P_PACKAGE_DOCUMENT: G2P_PACKAGE_DOCUMENT_SHA256,
}

_STATUS_ORDER = (
    RowStatus.PREDICTOR_USABLE.value,
    RowStatus.PREDICTOR_UNUSABLE.value,
    FailureReason.PREDICTOR_NONFINITE.value,
    FailureReason.PREDICTOR_NONPOSITIVE.value,
)
_ZERO_COUNTERS = {
    "cell8_validation_control_rows_read": 0,
    "cell8_final_test_control_rows_read": 0,
    "cell14_validation_control_rows_read": 0,
    "cell14_final_test_control_rows_read": 0,
    "cell10_rows_read": 0,
    "cell12_rows_read": 0,
    "raw_dbn_messages_decoded": 0,
    "non_allowlisted_cell14_value_columns_read": 0,
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
_INVARIANT_ZERO_COUNTER_KEYS = frozenset(
    {
        "cell10_rows_read",
        "cell12_rows_read",
        "raw_dbn_messages_decoded",
        "g2p_target_or_path_rows_read",
        "outer_train_target_rows_read",
        "outer_validation_target_rows_read",
        "final_test_target_rows_read",
        "targets_constructed",
        "real_fold_fit_calls",
        "real_models_fitted",
        "real_bootstrap_replicates",
    }
)
_NOT_COMPUTED = {
    "target_and_reason_counts": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "common_eligibility": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "target_and_request_hashes": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "fold_and_session_counts": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "fit_permits_and_completions": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "coefficient_identities": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "duan_factors": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "qlike_results": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "dependence_results": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
    "bootstrap_draw_identity": "NOT_COMPUTED_STAGE_NOT_AUTHORIZED",
}
_FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "decision_id",
        "decision_time",
        "predictor_value",
        "predictor_values",
        "raw_values",
        "distribution",
        "quantile",
        "min",
        "max",
        "minimum",
        "maximum",
        "mean",
        "median",
        "std",
        "histogram",
        "variance",
        "rows",
        "identities",
        "timestamps",
        "target_sha256",
        "request_set_sha256",
        "beta",
        "coefficient",
        "forecast",
    }
)
_AUTHORIZATION_KEY = object()


class Test3G2PBoundaryError(RuntimeError):
    """Raised before G2-P may exceed its target-blind TRAIN boundary."""


class Test3G2PInvalidEvidenceError(Test3G2PBoundaryError):
    """Raised when pinned source or ledger evidence violates the frozen protocol."""

    def __init__(self, category: str, *, projection_access_attested: bool = True) -> None:
        self.category = category
        self.projection_access_attested = projection_access_attested
        super().__init__(f"G2-P protocol-invalid evidence: {category}")


@dataclass(frozen=True)
class _FileIdentity:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


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


@dataclass(frozen=True)
class _PredictorStatus:
    decision_identity: str
    decision_time: datetime
    status: str


@dataclass(frozen=True)
class _Ledger:
    rows: tuple[_PredictorStatus, ...]
    status_counts: Mapping[str, int]
    ordered_identity_sha256: str
    ordered_identity_status_sha256: str
    terminal_failure_present: bool


def _fail(message: str) -> NoReturn:
    raise Test3G2PBoundaryError(message)


def _invalid_evidence(
    category: str, *, projection_access_attested: bool = True
) -> NoReturn:
    raise Test3G2PInvalidEvidenceError(
        category,
        projection_access_attested=projection_access_attested,
    )


def _file_identity(value: os.stat_result) -> _FileIdentity:
    return _FileIdentity(
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _absolute_lexical_path(path: str | Path, *, field: str) -> Path:
    expanded = os.path.expanduser(os.fspath(path))
    if not os.path.isabs(expanded):
        _fail(f"{field} must be an absolute path")
    return Path(os.path.abspath(expanded))


def _secure_directory_flags() -> int:
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required) or os.open not in os.supports_dir_fd:
        _fail("secure dir-FD path traversal is unavailable")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@contextmanager
def _open_directory_chain(path: str | Path, *, create: bool = False) -> Iterator[int]:
    candidate = _absolute_lexical_path(path, field="directory path")
    flags = _secure_directory_flags()
    descriptor = os.open(candidate.anchor, flags)
    try:
        for component in candidate.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise Test3G2PBoundaryError(
                        f"missing directory component: {component}"
                    ) from None
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise Test3G2PBoundaryError(
                        f"symlink or non-directory ancestor is forbidden: {component}"
                    ) from exc
                raise
            os.close(descriptor)
            descriptor = child
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            _fail("secure directory traversal did not end at a directory")
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def _open_regular_file(path: str | Path) -> Iterator[BinaryIO]:
    candidate = _absolute_lexical_path(path, field="input file")
    with _open_directory_chain(candidate.parent) as parent_descriptor:
        flags = os.O_RDONLY | os.O_NOFOLLOW
        try:
            descriptor = os.open(candidate.name, flags, dir_fd=parent_descriptor)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOENT, errno.ENOTDIR}:
                raise Test3G2PBoundaryError(
                    f"missing, symlinked, or invalid input file: {path}"
                ) from exc
            raise
        stream = os.fdopen(descriptor, "rb", closefd=True)
        try:
            before_status = os.fstat(stream.fileno())
            if not stat.S_ISREG(before_status.st_mode):
                _fail(f"file is not regular: {path}")
            before = _file_identity(before_status)
            yield stream
            if _file_identity(os.fstat(stream.fileno())) != before:
                _fail(f"file changed while inspected: {path}")
        finally:
            stream.close()


def _hash_stream(stream: BinaryIO) -> tuple[str, int]:
    stream.seek(0)
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
    stream.seek(0)
    return digest.hexdigest(), size


def _hash_regular_file(path: str | Path) -> tuple[str, int]:
    with _open_regular_file(path) as stream:
        return _hash_stream(stream)


def _regular_file_exists_no_follow(path: str | Path) -> bool:
    candidate = _absolute_lexical_path(path, field="existence-check path")
    try:
        with _open_directory_chain(candidate.parent) as directory:
            try:
                value = os.stat(candidate.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                return False
    except Test3G2PBoundaryError as exc:
        if str(exc).startswith("missing directory component:"):
            return False
        raise
    if stat.S_ISLNK(value.st_mode):
        _fail(f"symlinked evidence file is forbidden: {candidate.name}")
    if not stat.S_ISREG(value.st_mode):
        _fail(f"evidence path is not a regular file: {candidate.name}")
    return True


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"JSON contains duplicate key: {key}")
        result[key] = value
    return result


def _strict_json_file(
    path: str | Path, *, expected_sha256: str
) -> tuple[dict[str, object], int]:
    with _open_regular_file(path) as stream:
        observed, size = _hash_stream(stream)
        if observed != expected_sha256:
            _fail(f"JSON byte SHA-256 mismatch: {Path(path).name}")
        if size > 10 * 1024 * 1024:
            _fail("JSON evidence exceeds bounded size")
        payload = stream.read()
    try:
        parsed = json.loads(payload.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Test3G2PBoundaryError("evidence is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        _fail("evidence JSON root must be an object")
    return parsed, size


def _binding(expected: str, observed: object, *, field: str) -> dict[str, object]:
    if observed != expected:
        _fail(f"{field} identity mismatch")
    return {"expected": expected, "observed": observed, "match": True}


def _record_sha256(record: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


def _verify_g2_evidence(project_root: Path) -> dict[str, object]:
    record, size = _strict_json_file(
        project_root / G2_EVIDENCE_RECORD,
        expected_sha256=G2_EVIDENCE_RECORD_SHA256,
    )
    if record.get("record_sha256") != G2_EVIDENCE_SEMANTIC_SHA256:
        _fail("G2 evidence semantic SHA-256 pin mismatch")
    if _record_sha256(record) != G2_EVIDENCE_SEMANTIC_SHA256:
        _fail("G2 evidence semantic SHA-256 recomputation mismatch")
    expected_fields = {
        "status": "PASS",
        "execution_commit": G2_IMPLEMENTATION_COMMIT,
        "branch": "research/test3-g2-metadata-preflight-v1",
        "g2p_status": "NOT_AUTHORIZED",
        "target_space_consumption_status": "NOT_CONSUMED_METADATA_ONLY",
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
    }
    for field, expected in expected_fields.items():
        if record.get(field) != expected:
            _fail(f"G2 evidence field mismatch: {field}")
    counters = record.get("safety_counters")
    if not isinstance(counters, dict) or any(value != 0 for value in counters.values()):
        _fail("G2 evidence safety counters are not all zero")
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, list):
        _fail("G2 evidence artifact bindings are malformed")
    observed = {
        item.get("artifact_id"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
    }
    for artifact_id, expected_sha256 in (
        ("cell8_assignments", CELL8_SPLIT_ASSIGNMENT_SHA256),
        ("cell14_features", CELL14_FEATURE_FILE_SHA256),
    ):
        item = observed.get(artifact_id)
        if not isinstance(item, dict) or item.get("byte_sha256") != expected_sha256:
            _fail(f"G2 evidence lacks exact {artifact_id} binding")

    reservation, reservation_size = _strict_json_file(
        project_root / G2_RESERVATION_RECORD,
        expected_sha256=G2_RESERVATION_FILE_SHA256,
    )
    if (
        reservation.get("status") != "CONSUMED_BEFORE_ARTIFACT_ACCESS"
        or reservation.get("execution_commit") != G2_IMPLEMENTATION_COMMIT
        or reservation.get("authorization_document_sha256")
        != G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256
    ):
        _fail("G2 reservation binding mismatch")
    return {
        "evidence_commit": G2_EVIDENCE_COMMIT,
        "implementation_commit": G2_IMPLEMENTATION_COMMIT,
        "record_path": "${REPOSITORY}/" + G2_EVIDENCE_RECORD,
        "record_file_sha256": G2_EVIDENCE_RECORD_SHA256,
        "record_semantic_sha256": G2_EVIDENCE_SEMANTIC_SHA256,
        "record_size_bytes": size,
        "reservation_path": "${REPOSITORY}/" + G2_RESERVATION_RECORD,
        "reservation_file_sha256": G2_RESERVATION_FILE_SHA256,
        "reservation_size_bytes": reservation_size,
        "binding_status": "EXACT_COMMITTED_G2_EVIDENCE_VERIFIED_BEFORE_G2P_ACCESS",
    }


def _verify_predecessor_invalid_evidence(project_root: Path) -> dict[str, object]:
    expected_lineage = (
        (
            G2P_PREDECESSOR_PACKAGE_COMMIT,
            G2_EVIDENCE_COMMIT,
            G2P_PREDECESSOR_PACKAGE_TREE,
        ),
        (
            G2P_PREDECESSOR_EVIDENCE_COMMIT,
            G2P_PREDECESSOR_PACKAGE_COMMIT,
            G2P_PREDECESSOR_EVIDENCE_TREE,
        ),
        (G2P_BASE_COMMIT, G2P_PREDECESSOR_EVIDENCE_COMMIT, G2P_BASE_TREE),
    )
    for commit, parent, tree in expected_lineage:
        parents = _git_output(
            project_root, "rev-list", "--parents", "-n", "1", commit
        ).split()
        if parents != [commit, parent]:
            _fail(f"repair lineage parent mismatch: {commit}")
        if _git_output(project_root, "rev-parse", f"{commit}^{{tree}}") != tree:
            _fail(f"repair lineage tree mismatch: {commit}")

    reservation, reservation_size = _strict_json_file(
        project_root / G2P_PREDECESSOR_RESERVATION_RECORD,
        expected_sha256=G2P_PREDECESSOR_RESERVATION_SHA256,
    )
    reservation_expected = {
        "authorization_id": G2P_PREDECESSOR_AUTHORIZATION_ID,
        "authorization_document_sha256": (
            G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256
        ),
        "execution_commit": G2P_PREDECESSOR_PACKAGE_COMMIT,
        "execution_tree": G2P_PREDECESSOR_PACKAGE_TREE,
        "branch": "research/test3-g2p-predictor-preflight-v1",
        "status": "CONSUMED_BEFORE_PREDICTOR_ACCESS",
    }
    for field, expected in reservation_expected.items():
        if reservation.get(field) != expected:
            _fail(f"predecessor reservation field mismatch: {field}")

    failure, failure_size = _strict_json_file(
        project_root / G2P_PREDECESSOR_FAILURE_RECORD,
        expected_sha256=G2P_PREDECESSOR_FAILURE_SHA256,
    )
    failure_expected = {
        "authorization_id": G2P_PREDECESSOR_AUTHORIZATION_ID,
        "authorization_document_sha256": (
            G2P_PREDECESSOR_AUTHORIZATION_DOCUMENT_SHA256
        ),
        "status": "PROTOCOL_INVALID_EVIDENCE_AFTER_CONSUMPTION_NO_RETRY",
        "terminal_disposition": "INVALID_EVIDENCE",
        "invalid_evidence_category": "DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT",
        "ledger_status": "NOT_SEALED_SOURCE_OR_LEDGER_MISMATCH",
        "cause_audit_status": "REQUIRED_BEFORE_TARGET_SPACE_STATE_TRANSITION",
        "target_space_state": "LOCKED / RESERVED",
        "target_space_consumption_status": (
            "NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT"
        ),
        "projection_access_attested": True,
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "live_execution_status": "DISABLED",
        "g3p_status": "NOT_AUTHORIZED",
        "g3f_status": "NOT_AUTHORIZED",
    }
    for field, expected in failure_expected.items():
        if failure.get(field) != expected:
            _fail(f"predecessor failure field mismatch: {field}")
    counters = failure.get("protected_surface_counters")
    if (
        not isinstance(counters, dict)
        or set(counters) != set(_ZERO_COUNTERS)
        or any(value != 0 for value in counters.values())
    ):
        _fail("predecessor failure protected counters are not exact zeroes")

    return {
        "repair_lineage_id": G2P_REPAIR_LINEAGE_ID,
        "proof_commit": G2P_BASE_COMMIT,
        "proof_tree": G2P_BASE_TREE,
        "predecessor_package_commit": G2P_PREDECESSOR_PACKAGE_COMMIT,
        "predecessor_package_tree": G2P_PREDECESSOR_PACKAGE_TREE,
        "predecessor_evidence_commit": G2P_PREDECESSOR_EVIDENCE_COMMIT,
        "predecessor_evidence_tree": G2P_PREDECESSOR_EVIDENCE_TREE,
        "reservation_path": "${REPOSITORY}/" + G2P_PREDECESSOR_RESERVATION_RECORD,
        "reservation_file_sha256": G2P_PREDECESSOR_RESERVATION_SHA256,
        "reservation_size_bytes": reservation_size,
        "failure_path": "${REPOSITORY}/" + G2P_PREDECESSOR_FAILURE_RECORD,
        "failure_file_sha256": G2P_PREDECESSOR_FAILURE_SHA256,
        "failure_size_bytes": failure_size,
        "invalid_evidence_category": "DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT",
        "protected_surface_counters_all_zero": True,
        "target_space_consumed": False,
        "binding_status": "EXACT_PROVEN_DEFECT_PREDECESSOR_VERIFIED_BEFORE_SUCCESSOR",
    }


def _verify_document_bindings(project_root: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for relative_path, expected in _DOCUMENT_BINDINGS.items():
        observed, _size = _hash_regular_file(project_root / relative_path)
        result[relative_path] = {
            **_binding(expected, observed, field=relative_path),
            "binding_status": "PINNED_BEFORE_G2P_ACCESS",
        }
    return result


def _normalized_time(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid_evidence(f"{field.upper()}_NOT_TIMEZONE_AWARE")
    return value.astimezone(UTC)


def _normalized_identity(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        _invalid_evidence("DECISION_ID_MISSING_OR_INVALID")
    if any(delimiter in value for delimiter in ("\r", "\n")):
        _invalid_evidence("DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT")
    return value


def _normalized_instrument(value: object) -> str:
    if value is None or isinstance(value, bool):
        _invalid_evidence("INSTRUMENT_ID_MISSING_OR_INVALID")
    if isinstance(value, (int, float)):
        numeric = float(value)
        if not math.isfinite(numeric):
            _invalid_evidence("INSTRUMENT_ID_NONFINITE")
        if numeric.is_integer():
            return str(int(numeric))
    return str(value)


def _read_train_projection(
    stream: BinaryIO,
    *,
    columns: tuple[str, ...],
    field: str,
) -> pa.Table:
    stream.seek(0)
    table = pq.read_table(
        stream,
        columns=list(columns),
        filters=[("outer_partition", "==", "TRAIN")],
        use_threads=False,
    )
    if table.num_rows != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid_evidence(
            f"{field.upper().replace(' ', '_')}_ROW_COUNT_MISMATCH",
            projection_access_attested=False,
        )
    if tuple(table.column_names) != columns:
        _invalid_evidence(
            f"{field.upper().replace(' ', '_')}_PROJECTION_MISMATCH",
            projection_access_attested=False,
        )
    if table.column("outer_partition").to_pylist() != [
        "TRAIN"
    ] * EXPECTED_OUTER_TRAIN_ROWS:
        _invalid_evidence(
            f"{field.upper().replace(' ', '_')}_NON_TRAIN_ROW_EXPOSED",
            projection_access_attested=False,
        )
    return table


def _control_projection(rows: Sequence[Mapping[str, object]]) -> tuple[tuple[object, ...], ...]:
    normalized: list[tuple[object, ...]] = []
    seen_ids: set[str] = set()
    seen_times: set[datetime] = set()
    previous_time: datetime | None = None
    for row in rows:
        identity = _normalized_identity(row.get("decision_id"))
        decision_time = _normalized_time(row.get("decision_time"), field="decision_time")
        if identity in seen_ids or decision_time in seen_times:
            _invalid_evidence("TRAIN_CONTROL_IDENTITY_OR_TIME_DUPLICATE")
        if previous_time is not None and decision_time <= previous_time:
            _invalid_evidence("TRAIN_CONTROL_SOURCE_ORDER_INVERSION")
        if row.get("outer_partition") != "TRAIN":
            _invalid_evidence("NON_TRAIN_CONTROL_ROW_EXPOSED")
        roles = (row.get("role_wf_2022"), row.get("role_wf_2023"))
        if any(role not in {"TRAIN", "VALIDATION", "UNUSED"} for role in roles):
            _invalid_evidence("TRAIN_CONTROL_FOLD_ROLE_INVALID")
        if decision_time >= OUTER_VALIDATION_BOUNDARY_UTC:
            _invalid_evidence("TRAIN_CONTROL_CROSSES_OUTER_VALIDATION")
        seen_ids.add(identity)
        seen_times.add(decision_time)
        previous_time = decision_time
        normalized.append(
            (
                identity,
                decision_time,
                _normalized_instrument(row.get("instrument_id")),
                "TRAIN",
                *roles,
            )
        )
    if len(normalized) != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid_evidence("TRAIN_CONTROL_LEDGER_INCOMPLETE")
    return tuple(normalized)


def _as_predictor(value: object, *, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _invalid_evidence(f"{field.upper()}_TYPE_INVALID")
    return float(value)


def _feature_rows_with_null_contract(table: pa.Table) -> list[dict[str, object]]:
    null_masks = {
        column: table.column(column).is_null().to_pylist() for column in PREDICTOR_COLUMNS
    }
    rows = table.to_pylist()
    for index, row in enumerate(rows):
        for column in PREDICTOR_COLUMNS:
            if bool(null_masks[column][index]) != (row.get(column) is None):
                _invalid_evidence("ARROW_VALIDITY_BITMAP_EXPOSURE_MISMATCH")
    return rows


def _classify(values: tuple[float | None, float | None, float | None]) -> str:
    present = tuple(value for value in values if value is not None)
    if any(not math.isfinite(value) for value in present):
        return FailureReason.PREDICTOR_NONFINITE.value
    if any(value <= 0.0 for value in present):
        return FailureReason.PREDICTOR_NONPOSITIVE.value
    if any(value is None for value in values):
        return RowStatus.PREDICTOR_UNUSABLE.value
    return RowStatus.PREDICTOR_USABLE.value


def _build_ledger(
    controls: tuple[tuple[object, ...], ...],
    feature_rows: Sequence[Mapping[str, object]],
) -> _Ledger:
    if len(controls) != len(feature_rows):
        _invalid_evidence("CELL14_PREDICTOR_CONTROL_ROW_COUNT_MISMATCH")
    statuses: list[_PredictorStatus] = []
    for control, row in zip(controls, feature_rows, strict=True):
        values = tuple(
            _as_predictor(row.get(column), field=column) for column in PREDICTOR_COLUMNS
        )
        statuses.append(
            _PredictorStatus(
                decision_identity=str(control[0]),
                decision_time=control[1],
                status=_classify(values),
            )
        )
    rows = tuple(statuses)
    counts = Counter(row.status for row in rows)
    status_counts = {status: int(counts[status]) for status in _STATUS_ORDER}
    identity_payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}\n" for row in rows
    ).encode("utf-8")
    status_payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}|{row.status}\n"
        for row in rows
    ).encode("utf-8")
    terminal = bool(
        status_counts[FailureReason.PREDICTOR_NONFINITE.value]
        or status_counts[FailureReason.PREDICTOR_NONPOSITIVE.value]
    )
    return _Ledger(
        rows=rows,
        status_counts=status_counts,
        ordered_identity_sha256=hashlib.sha256(identity_payload).hexdigest(),
        ordered_identity_status_sha256=hashlib.sha256(status_payload).hexdigest(),
        terminal_failure_present=terminal,
    )


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
        _fail("G2-P record contains forbidden row/value fields: " + ", ".join(forbidden))
    counters = record.get("safety_counters")
    ledger = record.get("predictor_status_ledger")
    predictor_definition = record.get("frozen_predictor_definition")
    if (
        not isinstance(counters, dict)
        or not isinstance(ledger, dict)
        or not isinstance(predictor_definition, dict)
    ):
        _fail("G2-P record counters/ledger are malformed")
    expected_rows = predictor_definition.get("outer_train_rows")
    if isinstance(expected_rows, bool) or not isinstance(expected_rows, int) or expected_rows <= 0:
        _fail("G2-P record outer-TRAIN declaration is malformed")
    if expected_rows != EXPECTED_OUTER_TRAIN_ROWS:
        _fail("G2-P record outer-TRAIN declaration differs from the frozen count")
    for field, expected in _ZERO_COUNTERS.items():
        if counters.get(field) != expected:
            _fail(f"G2-P zero counter mismatch: {field}")
    if counters.get("g2p_train_predictor_rows_read") != expected_rows:
        _fail("G2-P TRAIN predictor row counter is incomplete")
    if ledger.get("row_count") != expected_rows:
        _fail("G2-P predictor ledger row count is incomplete")
    counts = ledger.get("status_counts")
    if not isinstance(counts, dict) or set(counts) != set(_STATUS_ORDER):
        _fail("G2-P status-count key set is incomplete")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in counts.values()
    ):
        _fail("G2-P status counts must be nonnegative integers")
    if sum(counts.values()) != expected_rows:
        _fail("G2-P status counts do not cover every TRAIN identity")
    if record.get("not_computed") != _NOT_COMPUTED:
        _fail("G2-P record lacks explicit later-stage dispositions")


def build_g2p_record(
    *,
    cell8_path: str | Path,
    cell14_path: str | Path,
    git_context: _GitContext,
    authorization: _ObservedAuthorization,
    document_bindings: Mapping[str, object],
    g2_evidence_binding: Mapping[str, object],
    predecessor_failure_binding: Mapping[str, object],
    runtime_binding: Mapping[str, object],
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    if (
        not isinstance(authorization, _ObservedAuthorization)
        or authorization._verification_key is not _AUTHORIZATION_KEY
        or authorization.authorization_id != G2P_AUTHORIZATION_ID
        or authorization.document_sha256 != G2P_AUTHORIZATION_DOCUMENT_SHA256
        or authorization.code_identity != git_context.code_identity
        or authorization.tree_identity != git_context.tree_identity
    ):
        _fail("G2-P requires verified consumed Owner authorization")
    if git_context.branch != G2P_BRANCH:
        _fail(f"G2-P must execute on branch {G2P_BRANCH}")
    if git_context.code_identity != git_context.upstream_identity:
        _fail("G2-P record requires local/upstream equality")
    cell8 = Path(cell8_path)
    cell14 = Path(cell14_path)
    if cell8.name != CELL8_FILENAME or cell14.name != CELL14_FILENAME:
        _fail("G2-P requires exact canonical artifact filenames")

    _assert_forbidden_modules_absent(phase="immediately before artifact open")
    with ExitStack() as stack:
        cell8_stream = stack.enter_context(_open_regular_file(cell8))
        cell14_stream = stack.enter_context(_open_regular_file(cell14))
        cell8_sha, cell8_size = _hash_stream(cell8_stream)
        cell14_sha, cell14_size = _hash_stream(cell14_stream)
        if cell8_sha != CELL8_SPLIT_ASSIGNMENT_SHA256:
            _invalid_evidence("CELL8_BYTE_SHA256_MISMATCH")
        if cell14_sha != CELL14_FEATURE_FILE_SHA256:
            _invalid_evidence("CELL14_BYTE_SHA256_MISMATCH")
        cell8_table = _read_train_projection(
            cell8_stream,
            columns=CONTROL_COLUMNS,
            field="Cell 8 control projection",
        )
        _assert_forbidden_modules_absent(phase="after Cell 8 projection")
        cell14_table = _read_train_projection(
            cell14_stream,
            columns=(*CONTROL_COLUMNS, *PREDICTOR_COLUMNS),
            field="Cell 14 predictor projection",
        )
        _assert_forbidden_modules_absent(phase="after Cell 14 projection")
        cell8_post_sha, cell8_post_size = _hash_stream(cell8_stream)
        cell14_post_sha, cell14_post_size = _hash_stream(cell14_stream)
        if (cell8_post_sha, cell8_post_size) != (cell8_sha, cell8_size):
            _fail("Cell 8 bytes changed during projection")
        if (cell14_post_sha, cell14_post_size) != (cell14_sha, cell14_size):
            _fail("Cell 14 bytes changed during projection")

    cell8_controls = _control_projection(cell8_table.to_pylist())
    cell14_rows = _feature_rows_with_null_contract(cell14_table)
    cell14_controls = _control_projection(cell14_rows)
    if cell8_controls != cell14_controls:
        _invalid_evidence("CELL8_CELL14_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH")
    control_binding_sha256 = sha256_bytes(
        canonical_json_bytes(
            [
                [
                    row[0],
                    row[1].isoformat(),
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                ]
                for row in cell8_controls
            ]
        )
    )
    ledger = _build_ledger(cell14_controls, cell14_rows)
    _assert_forbidden_modules_absent(phase="after complete predictor ledger")
    stage_status = (
        "G2P_SUCCESSOR_TERMINAL_INVALID_EVIDENCE"
        if ledger.terminal_failure_present
        else "G2P_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT_PASS"
    )
    terminal_disposition = (
        "INVALID_EVIDENCE"
        if ledger.terminal_failure_present
        else "NOT_COMPUTED_STAGE_NOT_AUTHORIZED"
    )
    counters = {
        "cell8_train_control_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "cell14_train_control_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "g2p_train_predictor_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "g2p_predictor_cells_inspected": EXPECTED_OUTER_TRAIN_ROWS * len(PREDICTOR_COLUMNS),
        **_ZERO_COUNTERS,
    }
    record_core: dict[str, object] = {
        "gate_id": G2P_GATE_ID,
        "record_version": G2P_RECORD_VERSION,
        "protocol_id": PROTOCOL_ID,
        "project_budget_id": PROJECT_BUDGET_ID,
        "target_space_id": TARGET_SPACE_ID,
        "target_space_state": (
            "CLOSED_UNCONSUMED" if ledger.terminal_failure_present else TARGET_SPACE_STATE
        ),
        "ratified_commit": RATIFIED_COMMIT,
        "ratification_record_commit": RATIFICATION_RECORD_COMMIT,
        "base_commit": G2P_BASE_COMMIT,
        "execution_commit": git_context.code_identity,
        "execution_tree": git_context.tree_identity,
        "branch": git_context.branch,
        "upstream_commit": git_context.upstream_identity,
        "local_upstream_equal": git_context.code_identity == git_context.upstream_identity,
        "access_level": G2P_ACCESS_LEVEL,
        "status": "COMPLETE",
        "stage_status": stage_status,
        "terminal_disposition": terminal_disposition,
        "cause_audit_status": (
            "SUCCESSOR_FAILED_TEST3_TERMINAL_NO_RETRY"
            if ledger.terminal_failure_present
            else "PROVEN_DEFECT_REPAIRED_NO_FURTHER_SUCCESSOR"
        ),
        "authorization_binding": {
            "authorization_id": authorization.authorization_id,
            "authorization_document_sha256": authorization.document_sha256,
            "authorization_token_sha256": hashlib.sha256(
                G2P_AUTHORIZATION_TOKEN.encode("utf-8")
            ).hexdigest(),
            "repair_lineage_id": G2P_REPAIR_LINEAGE_ID,
            "successor_ordinal": G2P_SUCCESSOR_ORDINAL,
            "successor_limit": G2P_SUCCESSOR_LIMIT,
            "reservation_path": "${REPOSITORY}/" + G2P_REPAIR_RESERVATION_RECORD,
            "reservation_file_sha256": authorization.reservation_file_sha256,
            "reservation_status": "CONSUMED_BEFORE_PREDICTOR_ACCESS",
            "document_bindings": dict(document_bindings),
        },
        "g2_evidence_binding": dict(g2_evidence_binding),
        "proven_defect_predecessor_binding": dict(predecessor_failure_binding),
        "runtime_binding": dict(runtime_binding),
        "repository_strategy": {
            "execution_strategy": "DIRECT_DESCENDANT_BRANCH_NO_MERGE",
            "merge_authorized": False,
            "changed_file_allowlist": sorted(G2P_ALLOWED_CHANGED_FILES),
        },
        "frozen_predictor_definition": {
            "predictor_order": list(PREDICTOR_COLUMNS),
            "status_order": list(_STATUS_ORDER),
            "outer_train_rows": EXPECTED_OUTER_TRAIN_ROWS,
            "cell14_ordered_feature_sha256_declared": CELL14_ORDERED_FEATURE_SHA256,
            "global_usability_or_status_fields_read": False,
        },
        "source_bindings": {
            "cell8": {
                "path": "${MES_G2P_ARTIFACTS}/cell8/" + CELL8_FILENAME,
                "byte_sha256": cell8_sha,
                "size_bytes": cell8_size,
            },
            "cell14": {
                "path": "${MES_G2P_ARTIFACTS}/cell14/" + CELL14_FILENAME,
                "byte_sha256": cell14_sha,
                "size_bytes": cell14_size,
            },
            "outer_train_control_binding_sha256": control_binding_sha256,
        },
        "predictor_status_ledger": {
            "hash_projection_id": LEDGER_HASH_PROJECTION_ID,
            "hash_serialization": LEDGER_HASH_SERIALIZATION,
            "row_count": len(ledger.rows),
            "status_counts": dict(ledger.status_counts),
            "ordered_identity_sha256": ledger.ordered_identity_sha256,
            "ordered_identity_status_sha256": ledger.ordered_identity_status_sha256,
            "raw_predictor_values_persisted": False,
            "per_row_identities_persisted": False,
        },
        "counter_semantics": {
            "rows_read": "APPLICATION_EXPOSED_ROWS",
            "validation_predictor_values_exposed_to_python": 0,
            "parquet_compressed_byte_or_internal_page_decode_exclusion_claimed": False,
        },
        "safety_counters": counters,
        "not_computed": dict(_NOT_COMPUTED),
        "target_space_consumption_status": (
            "CLOSED_UNCONSUMED_SUCCESSOR_FAILED"
            if ledger.terminal_failure_present
            else "NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT"
        ),
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "live_execution_status": "DISABLED",
        "g3p_status": "NOT_AUTHORIZED",
        "g3f_status": "NOT_AUTHORIZED",
    }
    run_seed = sha256_bytes(canonical_json_bytes(canonicalize_audit(record_core)))
    record = {
        **record_core,
        "run_id": f"MES_T3_G2P_{run_seed[:16].upper()}",
        "audit_written_utc": audit_written_utc
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _assert_closed_record(record)
    record["record_sha256"] = _record_sha256(record)
    return record


def _atomic_create_json(path: Path, payload: Mapping[str, object]) -> str:
    candidate = _absolute_lexical_path(path, field="create-once JSON path")
    with _open_directory_chain(candidate.parent, create=True) as directory:
        descriptor = os.open(
            candidate.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        try:
            encoded = (
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    _fail("create-once write made no progress")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(directory)
    return _hash_regular_file(candidate)[0]


def _consume_authorization(
    *,
    project_root: Path,
    output_root: Path,
    git_context: _GitContext,
    authorization_token: str,
) -> _ObservedAuthorization:
    if authorization_token != G2P_AUTHORIZATION_TOKEN:
        _fail("G2-P Owner authorization token mismatch")
    observed, _size = _hash_regular_file(project_root / G2P_AUTHORIZATION_DOCUMENT)
    _binding(
        G2P_AUTHORIZATION_DOCUMENT_SHA256,
        observed,
        field="G2-P Owner authorization document",
    )
    expected_output_root = project_root / "artifacts/exploration/test3/g2p"
    if output_root != expected_output_root:
        _fail("G2-P successor output root differs from the fixed repair lineage")
    reservation_path = project_root / G2P_REPAIR_RESERVATION_RECORD
    payload = {
        "authorization_id": G2P_AUTHORIZATION_ID,
        "authorization_document_sha256": G2P_AUTHORIZATION_DOCUMENT_SHA256,
        "authorization_token_sha256": hashlib.sha256(
            G2P_AUTHORIZATION_TOKEN.encode("utf-8")
        ).hexdigest(),
        "repair_lineage_id": G2P_REPAIR_LINEAGE_ID,
        "successor_ordinal": G2P_SUCCESSOR_ORDINAL,
        "successor_limit": G2P_SUCCESSOR_LIMIT,
        "proof_commit": G2P_BASE_COMMIT,
        "execution_commit": git_context.code_identity,
        "execution_tree": git_context.tree_identity,
        "branch": git_context.branch,
        "predecessor_evidence_commit": G2P_PREDECESSOR_EVIDENCE_COMMIT,
        "predecessor_reservation_sha256": G2P_PREDECESSOR_RESERVATION_SHA256,
        "predecessor_failure_sha256": G2P_PREDECESSOR_FAILURE_SHA256,
        "status": "CONSUMED_BEFORE_PREDICTOR_ACCESS",
        "consumed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    try:
        reservation_sha256 = _atomic_create_json(reservation_path, payload)
    except FileExistsError as exc:
        raise Test3G2PBoundaryError("G2-P authorization is already consumed") from exc
    return _ObservedAuthorization(
        authorization_id=G2P_AUTHORIZATION_ID,
        document_sha256=G2P_AUTHORIZATION_DOCUMENT_SHA256,
        code_identity=git_context.code_identity,
        tree_identity=git_context.tree_identity,
        reservation_path=reservation_path,
        reservation_file_sha256=reservation_sha256,
        _verification_key=_AUTHORIZATION_KEY,
    )


def write_failure_summary_if_consumed(
    *, project_root: str | Path, error: BaseException
) -> Path | None:
    root = _absolute_lexical_path(project_root, field="project root")
    reservation = root / G2P_REPAIR_RESERVATION_RECORD
    if not _regular_file_exists_no_follow(reservation):
        return None
    failure = root / G2P_REPAIR_FAILURE_RECORD
    payload = {
        "authorization_id": G2P_AUTHORIZATION_ID,
        "authorization_document_sha256": G2P_AUTHORIZATION_DOCUMENT_SHA256,
        "repair_lineage_id": G2P_REPAIR_LINEAGE_ID,
        "successor_ordinal": G2P_SUCCESSOR_ORDINAL,
        "successor_limit": G2P_SUCCESSOR_LIMIT,
        "error_class": type(error).__name__,
        "failed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "raw_error_message_committed": False,
    }
    if isinstance(error, Test3G2PInvalidEvidenceError):
        if error.projection_access_attested:
            protected_counters: dict[str, object] = dict(_ZERO_COUNTERS)
            validation_status = "UNOPENED"
            final_test_status = "SEALED"
        else:
            protected_counters = {
                key: (
                    0
                    if key in _INVARIANT_ZERO_COUNTER_KEYS
                    else "NOT_ATTESTED_DUE_TO_INVALID_PROJECTION"
                )
                for key in _ZERO_COUNTERS
            }
            validation_status = "ACCESS_BREACH_FAIL_CLOSED"
            final_test_status = "ACCESS_BREACH_FAIL_CLOSED"
        payload.update(
            {
                "status": "PROTOCOL_INVALID_EVIDENCE_AFTER_CONSUMPTION_NO_RETRY",
                "terminal_disposition": "INVALID_EVIDENCE",
                "invalid_evidence_category": error.category,
                "ledger_status": "NOT_SEALED_SOURCE_OR_LEDGER_MISMATCH",
                "cause_audit_status": "SUCCESSOR_FAILED_TEST3_TERMINAL_NO_RETRY",
                "target_space_state": "CLOSED_UNCONSUMED",
                "target_space_consumption_status": (
                    "CLOSED_UNCONSUMED_SUCCESSOR_FAILED"
                ),
                "projection_access_attested": error.projection_access_attested,
                "protected_surface_counters": protected_counters,
                "validation_status": validation_status,
                "final_test_status": final_test_status,
                "live_execution_status": "DISABLED",
                "g3p_status": "NOT_AUTHORIZED",
                "g3f_status": "NOT_AUTHORIZED",
            }
        )
    else:
        protected_counters = {
            key: (
                0
                if key in _INVARIANT_ZERO_COUNTER_KEYS
                else "NOT_ATTESTED_DUE_TO_EXECUTION_FAILURE"
            )
            for key in _ZERO_COUNTERS
        }
        payload.update(
            {
                "status": "FAILED_AFTER_SUCCESSOR_AUTHORIZATION_CONSUMPTION_NO_RETRY",
                "terminal_disposition": "EXECUTION_FAILURE",
                "failure_category": (
                    "UNCLASSIFIED_EXECUTION_FAILURE_AFTER_CONSUMPTION"
                ),
                "ledger_status": "NOT_ATTESTED_DUE_TO_EXECUTION_FAILURE",
                "cause_audit_status": "SUCCESSOR_FAILED_TEST3_TERMINAL_NO_RETRY",
                "target_space_state": "CLOSED_UNCONSUMED",
                "target_space_consumption_status": (
                    "CLOSED_UNCONSUMED_SUCCESSOR_FAILED"
                ),
                "projection_access_attested": False,
                "protected_surface_counters": protected_counters,
                "validation_status": "ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED",
                "final_test_status": "ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED",
                "live_execution_status": "DISABLED",
                "g3p_status": "NOT_AUTHORIZED",
                "g3f_status": "NOT_AUTHORIZED",
            }
        )
    try:
        _atomic_create_json(failure, payload)
    except FileExistsError:
        pass
    return failure


def write_g2p_record(
    record: Mapping[str, object], *, output_root: str | Path
) -> tuple[Path, str]:
    _assert_closed_record(record)
    if record.get("record_sha256") != _record_sha256(record):
        _fail("G2-P record semantic SHA-256 mismatch before publication")
    run_id = record.get("run_id")
    if (
        not isinstance(run_id, str)
        or len(run_id) != len("MES_T3_G2P_") + 16
        or not run_id.startswith("MES_T3_G2P_")
        or any(character not in "0123456789ABCDEF" for character in run_id[-16:])
    ):
        _fail("G2-P record run_id is malformed")
    root = _absolute_lexical_path(output_root, field="G2-P output root")
    run_dir = root / run_id
    output = run_dir / "predictor_preflight_record.json"
    with _open_directory_chain(root, create=True) as root_descriptor:
        os.mkdir(run_id, mode=0o700, dir_fd=root_descriptor)
        os.fsync(root_descriptor)
    try:
        file_sha256 = _atomic_create_json(output, record)
        parsed, _size = _strict_json_file(
            output,
            expected_sha256=file_sha256,
        )
        if parsed.get("record_sha256") != _record_sha256(parsed):
            _fail("published G2-P record failed semantic reread")
    except Exception:
        try:
            with _open_directory_chain(run_dir) as run_descriptor:
                try:
                    os.unlink(output.name, dir_fd=run_descriptor)
                except FileNotFoundError:
                    pass
                os.fsync(run_descriptor)
            with _open_directory_chain(root) as root_descriptor:
                try:
                    os.rmdir(run_id, dir_fd=root_descriptor)
                except OSError:
                    pass
                os.fsync(root_descriptor)
        except Test3G2PBoundaryError:
            pass
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


def _git_sha(value: str, *, field: str) -> str:
    if (
        len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(f"{field} must be a lowercase 40-character Git SHA")
    return value


def _assert_no_untracked_import_surface(project_root: Path) -> None:
    tracked = frozenset(
        filter(
            None,
            _git_output(project_root, "ls-files", "--", "src", "tests", "tools").splitlines(),
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

    def tracked_source_cache(path: str) -> bool:
        candidate = Path(path)
        if candidate.suffix != ".pyc" or candidate.parent.name != "__pycache__":
            return False
        module_name = candidate.name.split(".", 1)[0]
        source = candidate.parent.parent / f"{module_name}.py"
        return source.as_posix() in tracked

    importable = sorted(
        path
        for path in candidates
        if Path(path).suffix in importable_suffixes and not tracked_source_cache(path)
    )
    if importable:
        _fail(f"untracked or ignored importable code present: {importable}")


def _git_execution_context(project_root: Path) -> _GitContext:
    branch = _git_output(project_root, "branch", "--show-current")
    if branch != G2P_BRANCH:
        _fail(f"G2-P must execute on branch {G2P_BRANCH}")
    code_identity = _git_sha(_git_output(project_root, "rev-parse", "HEAD"), field="HEAD")
    tree_identity = _git_sha(
        _git_output(project_root, "rev-parse", "HEAD^{tree}"), field="HEAD tree"
    )
    parents = _git_output(
        project_root, "rev-list", "--parents", "-n", "1", code_identity
    ).split()
    if parents != [code_identity, G2P_BASE_COMMIT]:
        _fail("G2-P implementation must be one direct-child commit of the authorized base")
    changed = frozenset(
        filter(
            None,
            _git_output(
                project_root,
                "diff",
                "--name-only",
                f"{G2P_BASE_COMMIT}..{code_identity}",
            ).splitlines(),
        )
    )
    if changed != G2P_ALLOWED_CHANGED_FILES:
        _fail(
            "G2-P changed-file firewall mismatch; "
            f"unexpected={sorted(changed - G2P_ALLOWED_CHANGED_FILES)}; "
            f"missing={sorted(G2P_ALLOWED_CHANGED_FILES - changed)}"
        )
    tracked_status = _git_output(
        project_root, "status", "--porcelain=v1", "--untracked-files=no"
    )
    if tracked_status:
        _fail("G2-P execution requires a clean tracked worktree")
    _assert_no_untracked_import_surface(project_root)
    try:
        upstream = _git_sha(
            _git_output(project_root, "rev-parse", "@{upstream}"),
            field="upstream",
        )
    except subprocess.CalledProcessError as exc:
        raise Test3G2PBoundaryError("G2-P branch must have a pushed upstream") from exc
    if upstream != code_identity:
        _fail("G2-P local and upstream commits differ")
    upstream_ref = _git_output(
        project_root, "rev-parse", "--symbolic-full-name", "@{upstream}"
    )
    expected_ref = f"refs/remotes/origin/{G2P_BRANCH}"
    if upstream_ref != expected_ref:
        _fail(f"G2-P upstream must be exactly {expected_ref}")
    return _GitContext(code_identity, tree_identity, branch, upstream)


def _assert_isolated_runtime() -> None:
    required_flags = {
        "isolated": 1,
        "safe_path": True,
        "no_user_site": 1,
        "ignore_environment": 1,
        "dont_write_bytecode": 1,
    }
    for field, expected in required_flags.items():
        if getattr(sys.flags, field, None) != expected:
            _fail(f"G2-P requires isolated Python -I -B ({field})")
    forbidden_entries = {"", os.getcwd(), str(Path(os.getcwd()) / "tools")}
    if forbidden_entries.intersection(sys.path):
        _fail("isolated Python sys.path contains cwd or tools")


def _module_origin(module: object, *, field: str) -> Path:
    file_value = getattr(module, "__file__", None)
    specification = getattr(module, "__spec__", None)
    origin_value = getattr(specification, "origin", None)
    if not isinstance(file_value, str) or not isinstance(origin_value, str):
        _fail(f"{field} lacks a concrete module origin")
    file_path = _absolute_lexical_path(file_value, field=f"{field} __file__")
    origin_path = _absolute_lexical_path(origin_value, field=f"{field} spec origin")
    if file_path != origin_path:
        _fail(f"{field} file/spec origins differ")
    return file_path


def _assert_runtime_module_origins(project_root: Path) -> dict[str, object]:
    expected_repo_modules = {
        "g2p": project_root / "src/mes_quant/exploration/test3_g2p_preflight.py",
        "core_hashing": project_root / "src/mes_quant/core/hashing.py",
        "test3_contract": project_root / "src/mes_quant/exploration/test3_contract.py",
    }
    observed_repo_modules = {
        "g2p": _module_origin(sys.modules[__name__], field="G2-P module"),
        "core_hashing": _module_origin(hashing_module, field="core hashing module"),
        "test3_contract": _module_origin(contract_module, field="Test 3 contract module"),
    }
    for label, expected in expected_repo_modules.items():
        if observed_repo_modules[label] != expected:
            _fail(f"{label} module origin is outside the exact repository source path")
        relative = expected.relative_to(project_root).as_posix()
        tracked_blob = _git_output(project_root, "rev-parse", f"HEAD:{relative}")
        working_blob = _git_output(project_root, "hash-object", relative)
        if tracked_blob != working_blob:
            _fail(f"{label} working bytes differ from the execution commit")

    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    pyarrow_root = (
        _absolute_lexical_path(sys.prefix, field="virtual environment")
        / "lib"
        / python_version
        / "site-packages"
        / "pyarrow"
    )
    pa_origin = _module_origin(pa, field="PyArrow module")
    pq_origin = _module_origin(pq, field="PyArrow Parquet module")
    try:
        pa_origin.relative_to(pyarrow_root)
        pq_origin.relative_to(pyarrow_root)
    except ValueError as exc:
        raise Test3G2PBoundaryError("PyArrow module origin is outside the exact venv") from exc
    if pa.__version__ != "18.1.0":
        _fail("G2-P requires pinned PyArrow 18.1.0")
    if pq.read_table.__module__ != "pyarrow.parquet.core" or pq.read_table.__name__ != "read_table":
        _fail("PyArrow read_table callable provenance mismatch")
    expected_executable = project_root / ".venv/bin/python"
    if _absolute_lexical_path(sys.executable, field="Python executable") != expected_executable:
        _fail("G2-P requires the repository virtual-environment Python")
    if canonical_json_bytes.__module__ != "mes_quant.core.hashing":
        _fail("canonical JSON callable provenance mismatch")
    if RowStatus.__module__ != "mes_quant.exploration.test3_contract":
        _fail("Test 3 contract enum provenance mismatch")
    return {
        "python_executable": "${REPOSITORY}/.venv/bin/python",
        "python_isolated": True,
        "python_safe_path": True,
        "python_no_user_site": True,
        "python_ignore_environment": True,
        "python_dont_write_bytecode": True,
        "pyarrow_version": pa.__version__,
        "module_origins": {
            "g2p": "${REPOSITORY}/src/mes_quant/exploration/test3_g2p_preflight.py",
            "core_hashing": "${REPOSITORY}/src/mes_quant/core/hashing.py",
            "test3_contract": "${REPOSITORY}/src/mes_quant/exploration/test3_contract.py",
            "pyarrow": "${VENV_SITE_PACKAGES}/pyarrow/__init__.py",
            "pyarrow_parquet": "${VENV_SITE_PACKAGES}/pyarrow/parquet/__init__.py",
        },
    }


def _loaded_modules(prefix: str) -> tuple[str, ...]:
    return tuple(
        sorted(name for name in sys.modules if name == prefix or name.startswith(prefix + "."))
    )


def _assert_forbidden_modules_absent(*, phase: str) -> None:
    prefixes = (
        "databento",
        "databento_dbn",
        "mes_quant.exploration.test2_l1_harness",
        "mes_quant.exploration.test2_g3_pre_fit",
        "mes_quant.exploration.test3_target",
        "mes_quant.exploration.test3_design",
        "mes_quant.exploration.test3_stats",
        "mes_quant.exploration.test3_evaluation",
        "mes_quant.exploration.l1_lr001",
        "mes_quant.exploration.l1_tree001",
        "scipy",
        "sklearn",
        "statsmodels",
        "xgboost",
        "lightgbm",
    )
    loaded = tuple(module for prefix in prefixes for module in _loaded_modules(prefix))
    if loaded:
        _fail(f"forbidden modules loaded during {phase}: {', '.join(loaded)}")


def _terminal_witness_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    _assert_closed_record(record)
    counters = record["safety_counters"]
    assert isinstance(counters, dict)
    ledger = record["predictor_status_ledger"]
    assert isinstance(ledger, dict)
    return (
        "TEST3_G2P_TARGET_BLIND_TRAIN_PREDICTOR_PREFLIGHT_COMPLETE",
        f"G2P_STAGE_STATUS={record['stage_status']}",
        f"TERMINAL_DISPOSITION={record['terminal_disposition']}",
        f"CELL8_VALIDATION_CONTROL_ROWS_READ={counters['cell8_validation_control_rows_read']}",
        f"CELL8_FINAL_TEST_CONTROL_ROWS_READ={counters['cell8_final_test_control_rows_read']}",
        f"CELL14_VALIDATION_CONTROL_ROWS_READ={counters['cell14_validation_control_rows_read']}",
        f"CELL14_FINAL_TEST_CONTROL_ROWS_READ={counters['cell14_final_test_control_rows_read']}",
        f"CELL10_ROWS_READ={counters['cell10_rows_read']}",
        f"CELL12_ROWS_READ={counters['cell12_rows_read']}",
        f"RAW_DBN_MESSAGES_DECODED={counters['raw_dbn_messages_decoded']}",
        (
            "NON_ALLOWLISTED_CELL14_VALUE_COLUMNS_READ="
            f"{counters['non_allowlisted_cell14_value_columns_read']}"
        ),
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
        f"PREDICTOR_USABLE={ledger['status_counts'][RowStatus.PREDICTOR_USABLE.value]}",
        f"PREDICTOR_UNUSABLE={ledger['status_counts'][RowStatus.PREDICTOR_UNUSABLE.value]}",
        (
            "PREDICTOR_NONFINITE="
            f"{ledger['status_counts'][FailureReason.PREDICTOR_NONFINITE.value]}"
        ),
        (
            "PREDICTOR_NONPOSITIVE="
            f"{ledger['status_counts'][FailureReason.PREDICTOR_NONPOSITIVE.value]}"
        ),
        f"VALIDATION_STATUS={record['validation_status']}",
        f"FINAL_TEST_STATUS={record['final_test_status']}",
        f"LIVE_EXECUTION_STATUS={record['live_execution_status']}",
        (
            "TARGET_SPACE_CONSUMPTION_STATUS="
            f"{record['target_space_consumption_status']}"
        ),
        f"G3P_STATUS={record['g3p_status']}",
        f"G3F_STATUS={record['g3f_status']}",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Owner-authorized Test 3 G2-P target-blind predictor preflight."
    )
    parser.add_argument("--gate", choices=(G2P_GATE_LITERAL,), required=True)
    parser.add_argument("--authorization-token", required=True)
    parser.add_argument("--cell8", type=Path, required=True)
    parser.add_argument("--cell14-features", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/exploration/test3/g2p"),
    )
    return parser


def _validate_cli_artifact_paths(
    cell8: Path,
    cell14: Path,
    *,
    project_root: Path,
) -> tuple[Path, Path]:
    validated: list[Path] = []
    for candidate, expected_relative, field in (
        (cell8, CELL8_CANONICAL_RELATIVE_PATH, "Cell 8"),
        (cell14, CELL14_CANONICAL_RELATIVE_PATH, "Cell 14"),
    ):
        expanded = Path(os.path.expanduser(os.fspath(candidate)))
        if not expanded.is_absolute():
            _fail(f"{field} artifact path must be absolute")
        lexical = _absolute_lexical_path(expanded, field=f"{field} artifact")
        expected = project_root / expected_relative
        if lexical != expected:
            _fail(f"{field} artifact requires the exact pinned canonical path")
        validated.append(lexical)
    return validated[0], validated[1]


def main(
    argv: Sequence[str] | None = None, *, project_root: str | Path | None = None
) -> int:
    _assert_isolated_runtime()
    args = _parser().parse_args(argv)
    if args.authorization_token != G2P_AUTHORIZATION_TOKEN:
        _fail("G2-P Owner authorization token mismatch")
    root = _absolute_lexical_path(
        project_root or Path.cwd(), field="G2-P project root"
    )
    allowed_output = root / "artifacts/exploration/test3/g2p"
    output_root = (
        _absolute_lexical_path(root / args.output_root, field="G2-P output root")
        if not args.output_root.is_absolute()
        else _absolute_lexical_path(args.output_root, field="G2-P output root")
    )
    if output_root != allowed_output:
        _fail(f"G2-P output root must be exactly {allowed_output}")
    cell8_path, cell14_path = _validate_cli_artifact_paths(
        args.cell8,
        args.cell14_features,
        project_root=root,
    )
    _assert_forbidden_modules_absent(phase="entry")
    git_context = _git_execution_context(root)
    runtime_binding = _assert_runtime_module_origins(root)
    documents = _verify_document_bindings(root)
    g2_evidence = _verify_g2_evidence(root)
    predecessor_failure = _verify_predecessor_invalid_evidence(root)
    _assert_forbidden_modules_absent(phase="pre-reservation")
    authorization = _consume_authorization(
        project_root=root,
        output_root=output_root,
        git_context=git_context,
        authorization_token=args.authorization_token,
    )
    record = build_g2p_record(
        cell8_path=cell8_path,
        cell14_path=cell14_path,
        git_context=git_context,
        authorization=authorization,
        document_bindings=documents,
        g2_evidence_binding=g2_evidence,
        predecessor_failure_binding=predecessor_failure,
        runtime_binding=runtime_binding,
    )
    _assert_forbidden_modules_absent(phase="post-ledger")
    output, file_sha256 = write_g2p_record(record, output_root=output_root)
    print(f"G2P_RECORD={output}")
    print(f"G2P_RECORD_SHA256={record['record_sha256']}")
    print(f"G2P_RECORD_FILE_SHA256={file_sha256}")
    print(f"G2P_AUTHORIZATION_RESERVATION={authorization.reservation_path}")
    print(f"G2P_AUTHORIZATION_RESERVATION_SHA256={authorization.reservation_file_sha256}")
    for line in _terminal_witness_lines(record):
        print(line)
    return 0


__all__ = [
    "CONTROL_COLUMNS",
    "EXPECTED_OUTER_TRAIN_ROWS",
    "G2P_ALLOWED_CHANGED_FILES",
    "G2P_AUTHORIZATION_DOCUMENT_SHA256",
    "G2P_AUTHORIZATION_ID",
    "G2P_AUTHORIZATION_TOKEN",
    "G2P_BASE_COMMIT",
    "G2P_BRANCH",
    "G2P_GATE_LITERAL",
    "PREDICTOR_COLUMNS",
    "Test3G2PBoundaryError",
    "build_g2p_record",
    "main",
    "write_failure_summary_if_consumed",
    "write_g2p_record",
]

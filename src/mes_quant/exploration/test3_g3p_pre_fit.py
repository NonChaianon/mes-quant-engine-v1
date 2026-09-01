"""Test 3 G3-P TRAIN-only target/support pre-fit orchestration.

This module is the first Test 3 stage permitted to expose numeric target/path values.
It seals the complete outer-TRAIN request identity before provider access, persists the
target-space consumption fact before the first target value is exposed, constructs the
frozen RV_FWD_60 ledger, and stops before every fit/evaluation surface.
"""

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
from collections import Counter, defaultdict
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import BinaryIO, NoReturn

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from mes_quant.core.hashing import canonical_json_bytes, canonicalize_audit, sha256_bytes
from mes_quant.exploration import test3_g3f_one_shot as _test3_g3f
from mes_quant.exploration import test3_stats as _test3_stats
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    RequestKey,
    StreamingSealedRequestSet,
    build_streaming_request_set,
    iter_path_bar_batches,
)
from mes_quant.exploration.test3_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_FEATURE_FILE_SHA256,
    CELL14_ORDERED_FEATURE_SHA256,
    DECODED_MES_1M_SHA256,
    FOLD_ORDER,
    FROZEN_HOLDOUT_COUNTS,
    MODEL_COLUMNS,
    MODEL_ORDER,
    PROJECT_BUDGET_ID,
    PROJECT_BUDGET_SHA256,
    PROTOCOL_ID,
    PROTOCOL_SHA256,
    RATIFICATION_RECORD_COMMIT,
    RATIFIED_COMMIT,
    RAW_DBN_SHA256,
    TARGET_BAR_COUNT,
    TARGET_HORIZON_MINUTES,
    TARGET_SPACE_ID,
    FailureReason,
    RowStatus,
)
from mes_quant.exploration.test3_design import (
    Harmonic,
    PredictorStatusRow,
    common_eligibility,
    design_values,
    intraday_harmonic,
)
from mes_quant.exploration.test3_stats import DependenceRow, dependence_summary
from mes_quant.exploration.test3_target import TargetStatusRow
from mes_quant.governance.execution_hardening.boundary import (
    BoundaryValidationError,
    normalize_integral_flag,
)

G3P_GATE_LITERAL = "G3P_TEST3_TRAIN_TARGET_SUPPORT_PREFIT"
G3P_GATE_ID = "MES_TEST3_G3P_TRAIN_PREFIT_V1"
G3P_RECORD_VERSION = "1.0"
G3P_ACCESS_LEVEL = "TRAIN_TARGET_SUPPORT_PREFIT_ZERO_FIT"
G3P_AUTHORIZATION_ID = "AUTH_TEST3_G3P_TRAIN_PREFIT_20260825"
G3P_AUTHORIZATION_TOKEN = "OWNER_AUTHORIZED_TEST3_G3P_TRAIN_PREFIT_20260825"
G3P_AUTHORIZATION_DOCUMENT = (
    "docs/research/TEST3_G3P_TRAIN_PREFIT_AUTHORIZATION_V1.md"
)
G3P_AUTHORIZATION_DOCUMENT_SHA256 = (
    "5be7e82b904c9057639ff17af39b4c0627c0c937cecd84f979eb1b37bc1653eb"
)
G3P_PACKAGE_DOCUMENT = "docs/research/TEST3_G3P_TRAIN_PREFIT_PACKAGE_V1.md"
G3P_PACKAGE_DOCUMENT_SHA256 = (
    "fc3d150340ce5f0db6fc3ae06f3149cdb981f7e874d9cf76c948882a42661294"
)
G3P_BASE_COMMIT = "a1ea24445f575c5d267d6bfe410cc7acd034b74f"
G3P_BASE_TREE = "ce20f1ecafb3a58fece522cb04048ffef9b628a8"
G3P_BRANCH = "research/test3-g3p-pre-fit-v1"
G3P_OUTPUT_SUBPATH = "artifacts/exploration/test3/g3p"
G3P_RECORD_FILENAME = "pre_fit_support_record.json"
G3P_BATCH_SIZE = 3_600
EXPECTED_OUTER_TRAIN_ROWS = 25_685
OUTER_VALIDATION_BOUNDARY_UTC = datetime(2024, 1, 2, 14, 45, tzinfo=UTC)

CELL2_HASH_COLUMNS = ("open", "high", "low", "close", "instrument_id")
CELL2_HASH_ALGORITHM = "SHA256_OVER_PANDAS_UINT64_ROW_HASHES"
CELL2_HASH_INCLUDES_INDEX = True
CELL2_HASH_PROJECTION_ID = "CELL2_MEMORY_HASH_COLUMNS_ORDERED_UTC_TS_EVENT_INDEX_V1"
DECODED_CONTENT_STATUS_RECOMPUTED = "RECOMPUTED_FULL_CANONICAL_CELL2_DECODE"
DECODE_SCOPE = "FULL_CANONICAL_DECODED_FRAME_IDENTITY_ONLY_NOT_PATH_LOOKUP"
CELL12_STATUS_USABLE = "USABLE"
CELL12_STATUS_PATH_INTEGRITY_FAILURE = "PATH_INTEGRITY_FAILURE"
CELL12_STATUS_LABEL_UNUSABLE = "LABEL_UNUSABLE"
CELL12_STATUS_SEALED_FINAL_TEST = "SEALED_FINAL_TEST"
CELL12_UNUSABLE_STATUSES = frozenset(
    {CELL12_STATUS_PATH_INTEGRITY_FAILURE, CELL12_STATUS_LABEL_UNUSABLE}
)

_FORBIDDEN_RUNTIME_MODULE_PREFIXES = (
    "mes_quant.exploration.l1_lr001",
    "mes_quant.exploration.l1_tree001",
    "mes_quant.exploration.test2_diagnostics",
    "mes_quant.exploration.test2_evaluation",
    "mes_quant.exploration.test2_g3_pre_fit",
    "mes_quant.exploration.test2_l1_harness",
    "mes_quant.exploration.test2_stats",
    "mes_quant.exploration.test2_target",
    "mes_quant.exploration.test3_g2p_preflight",
    "exchange_calendars",
    "pandas_market_calendars",
    "scipy",
    "sklearn",
    "statsmodels",
)

G2P_EVIDENCE_COMMIT = "a1ea24445f575c5d267d6bfe410cc7acd034b74f"
G2P_EXECUTION_COMMIT = "37552b84ab38a27b3bbd699e83da379a8b396b1b"
G2P_EXECUTION_TREE = "eb361eab45327a5f349c95defa7b5ec6f0083712"
G2P_RECORD_PATH = (
    "artifacts/exploration/test3/g2p/MES_T3_G2P_D9DBB6F304D1777B/"
    "predictor_preflight_record.json"
)
G2P_RECORD_FILE_SHA256 = (
    "0676929253404e0e617ca7a6fa75f31bb9cdc0b6bec9f1b36c144b07705e3e89"
)
G2P_RECORD_SEMANTIC_SHA256 = (
    "ce56c5668cd2c1bafd1840ef49494c561c43d4aa90ed45767f01eeb3093e088e"
)
G2P_RESERVATION_PATH = (
    "artifacts/exploration/test3/g2p/repair/"
    "MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1.consumed.json"
)
G2P_RESERVATION_SHA256 = (
    "8040981b79ad5281830bc43b3d82dff1cb7b272cf839256b741799aa6b2527e2"
)

AUTHORIZATION_RESERVATION_PATH = (
    "artifacts/exploration/test3/g3p/authorization/"
    f"{G3P_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
)
REQUEST_SET_WITNESS_PATH = (
    "artifacts/exploration/test3/g3p/request-set/"
    f"{G3P_AUTHORIZATION_DOCUMENT_SHA256}.sealed.json"
)
TARGET_SPACE_WITNESS_PATH = (
    "artifacts/exploration/test3/g3p/target-space/TARGET_SPACE_003.consumed.json"
)
FAILURE_RECORD_PATH = (
    "artifacts/exploration/test3/g3p/authorization/"
    f"{G3P_AUTHORIZATION_DOCUMENT_SHA256}.failure.json"
)

RAW_DBN_FILENAME = "MES_2019_2026_1m.dbn.zst"
CELL8_FILENAME = "cell8_purged_split_assignments_v1.parquet"
CELL10_FILENAME = "cell10_point_in_time_economic_labels_v1.parquet"
CELL12_FILENAME = "cell12_development_path_outcomes_v1.parquet"
CELL14_FILENAME = "cell14_development_point_in_time_features_v1.parquet"

_CANONICAL_RELATIVE_PATHS = {
    "raw_dbn": "artifacts/cache/source_v1/" + RAW_DBN_FILENAME,
    "cell8": "artifacts/cache/source_v1/" + CELL8_FILENAME,
    "cell10": "artifacts/cache/source_v1/" + CELL10_FILENAME,
    "cell12": "artifacts/cache/source_v1/" + CELL12_FILENAME,
    "cell14": "artifacts/runs/cell14_20260809T175203Z/" + CELL14_FILENAME,
}

CONTROL_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
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
CALENDAR_COLUMNS = (
    "minutes_since_nyse_open",
    "minutes_to_horizon_safe_close",
    "early_close_session",
)
CELL10_COLUMNS = (
    *CONTROL_COLUMNS,
    "entry_reference_close",
    "exit_reference_close_60m",
)
CELL12_COLUMNS = (
    *CONTROL_COLUMNS,
    "entry_reference_close",
    "exit_reference_close_60m",
    "path_status",
    "path_usable",
    "path_1m_present",
    "path_instrument_changed",
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
)
CELL14_COLUMNS = (*CONTROL_COLUMNS, *PREDICTOR_COLUMNS, *CALENDAR_COLUMNS)

G3P_ALLOWED_CHANGED_FILES = frozenset(
    {
        G3P_AUTHORIZATION_DOCUMENT,
        G3P_PACKAGE_DOCUMENT,
        "src/mes_quant/exploration/test3_g3p_pre_fit.py",
        "tests/test_test3_g3p_pre_fit.py",
        "tools/run_test3_g3p_pre_fit.py",
    }
)

_DOCUMENT_BINDINGS = {
    "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md": PROTOCOL_SHA256,
    "docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md": PROJECT_BUDGET_SHA256,
    "docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md": (
        "383243c73b3d4ba35878ff5119366e0c05dadd8e7ea32ec5bb90d3b2375675ec"
    ),
    "docs/research/TEST3_G2P_PROVEN_DEFECT_REPAIR_AMENDMENT_V1.md": (
        "135fed474c115269421bf9f59cf838f58609b4d6cf83aee2a2118b195cb13fa6"
    ),
    "tests/test_test3_g2p_proven_defect.py": (
        "ffe8a2c18f034a8c5280bba488cbb11a2dbcac617284e1be0a268d717ef19b4c"
    ),
    "docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_AUTHORIZATION_V1.md": (
        "6042c4e6b9fff928facb41dc5fba2997908bfd7aefb0f6714fd6d9b0630fadcc"
    ),
    "docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_PACKAGE_V1.md": (
        "537d89621786bf8588131db04021194a8286fc4eb53286faae226276f03b1b8f"
    ),
    G3P_AUTHORIZATION_DOCUMENT: G3P_AUTHORIZATION_DOCUMENT_SHA256,
    G3P_PACKAGE_DOCUMENT: G3P_PACKAGE_DOCUMENT_SHA256,
}

_STATUS_ORDER = (
    RowStatus.PREDICTOR_USABLE.value,
    RowStatus.PREDICTOR_UNUSABLE.value,
    FailureReason.PREDICTOR_NONFINITE.value,
    FailureReason.PREDICTOR_NONPOSITIVE.value,
)
_TARGET_STATUS_ORDER = (
    RowStatus.TARGET_USABLE.value,
    RowStatus.TARGET_UNUSABLE.value,
    FailureReason.TARGET_ZERO_VARIANCE.value,
)

_FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "beta",
        "coefficients",
        "decision_id",
        "decision_identity",
        "decision_time",
        "entry_reference_close",
        "exit_reference_close_60m",
        "forecast",
        "forecast_variance",
        "holdout_row_ids",
        "log_rv_fwd_60",
        "predictor_values",
        "qlike",
        "raw_target_values",
        "realized_vol_120m",
        "realized_vol_240m",
        "realized_vol_60m",
        "rv_fwd_60",
        "train_row_ids",
    }
)

_NOT_COMPUTED = {
    "model_fit": "NOT_AUTHORIZED_G3P",
    "coefficient_outputs": "NOT_AUTHORIZED_G3P",
    "forecast_outputs": "NOT_AUTHORIZED_G3P",
    "duan_smearing": "NOT_AUTHORIZED_G3P",
    "qlike_results": "NOT_AUTHORIZED_G3P",
    "bootstrap": "NOT_AUTHORIZED_G3P",
    "economic_diagnostic": "NOT_AUTHORIZED_G3P",
    "validation": "UNOPENED",
    "final_test": "SEALED",
}

_RECORD_TOP_LEVEL_KEYS = frozenset(
    {
        "access_level",
        "audit_written_utc",
        "authorization_binding",
        "base_commit",
        "branch",
        "cell12_reconciliation",
        "counter_semantics",
        "decoded_identity",
        "disposition",
        "execution_commit",
        "execution_tree",
        "final_test_status",
        "fit_authorization",
        "fit_guard",
        "frozen_definitions",
        "g2p_predecessor_binding",
        "g3f_status",
        "gate_id",
        "live_execution_status",
        "local_upstream_equal",
        "not_computed",
        "predictor_ledger_reproduction",
        "project_budget_id",
        "protocol_id",
        "provider_counters",
        "ratification_record_commit",
        "ratified_commit",
        "record_sha256",
        "record_version",
        "request_set_binding",
        "run_id",
        "runtime_binding",
        "safety_counters",
        "source_bindings",
        "stage_status",
        "status",
        "support_evidence",
        "target_space_consumption",
        "target_space_id",
        "target_space_state",
        "target_status_ledger",
        "upstream_commit",
        "validation_status",
    }
)


class Test3G3PBoundaryError(RuntimeError):
    """Raised before G3-P can misstate target-aware pre-fit evidence."""


class Test3G3PInvalidEvidenceError(Test3G3PBoundaryError):
    """Typed terminal source/contract failure."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(f"G3-P invalid evidence: {category}")


def _fail(message: str) -> NoReturn:
    raise Test3G3PBoundaryError(message)


def _invalid(category: str) -> NoReturn:
    raise Test3G3PInvalidEvidenceError(category)


def _absolute(path: str | Path, *, field_name: str) -> Path:
    expanded = Path(os.path.expanduser(os.fspath(path)))
    if not expanded.is_absolute():
        _fail(f"{field_name} must be an absolute path")
    return Path(os.path.abspath(expanded))


def _secure_directory_flags() -> int:
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required) or os.open not in os.supports_dir_fd:
        _fail("secure dir-FD path traversal is unavailable")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@contextmanager
def _open_directory_chain(path: str | Path, *, create: bool = False) -> Iterator[int]:
    candidate = _absolute(path, field_name="directory path")
    flags = _secure_directory_flags()
    descriptor = os.open(candidate.anchor, flags)
    try:
        for component in candidate.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise Test3G3PBoundaryError(
                        f"missing directory component: {component}"
                    ) from None
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                os.fsync(descriptor)
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise Test3G3PBoundaryError(
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


def _sha256_stream(stream: BinaryIO) -> tuple[str, int]:
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


@contextmanager
def _open_regular_file(path: str | Path) -> Iterator[BinaryIO]:
    candidate = _absolute(path, field_name="input file")
    with _open_directory_chain(candidate.parent) as parent_descriptor:
        try:
            descriptor = os.open(
                candidate.name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=parent_descriptor,
            )
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOENT, errno.ENOTDIR}:
                raise Test3G3PBoundaryError(
                    f"missing, symlinked, or invalid input file: {candidate.name}"
                ) from exc
            raise
        stream = os.fdopen(descriptor, "rb", closefd=True)
        try:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                _fail(f"input is not a regular file: {candidate.name}")
            yield stream
            after = os.fstat(stream.fileno())
            if (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                _fail(f"input changed while inspected: {candidate.name}")
        finally:
            stream.close()


def _regular_file_exists_no_follow(path: str | Path) -> bool:
    candidate = _absolute(path, field_name="existence-check path")
    try:
        with _open_directory_chain(candidate.parent) as directory:
            try:
                value = os.stat(candidate.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                return False
    except Test3G3PBoundaryError as exc:
        if str(exc).startswith("missing directory component:"):
            return False
        raise
    if stat.S_ISLNK(value.st_mode):
        _fail(f"symlinked evidence file is forbidden: {candidate.name}")
    if not stat.S_ISREG(value.st_mode):
        _fail(f"evidence path is not a regular file: {candidate.name}")
    return True


def _hash_file(path: str | Path) -> tuple[str, int]:
    with _open_regular_file(path) as stream:
        return _sha256_stream(stream)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"JSON contains duplicate key: {key}")
        result[key] = value
    return result


def _strict_json(path: str | Path, *, expected_sha256: str) -> dict[str, object]:
    with _open_regular_file(path) as stream:
        observed, size = _sha256_stream(stream)
        if observed != expected_sha256:
            _fail(f"JSON byte SHA-256 mismatch: {Path(path).name}")
        if size > 10 * 1024 * 1024:
            _fail("JSON evidence exceeds bounded size")
        payload = stream.read()
    parsed = json.loads(payload.decode("utf-8"), object_pairs_hook=_strict_object)
    if not isinstance(parsed, dict):
        _fail("evidence JSON root must be an object")
    return parsed


def _atomic_create_json(path: str | Path, payload: Mapping[str, object]) -> str:
    candidate = _absolute(path, field_name="create-once JSON path")
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
    return _hash_file(candidate)[0]


def _record_sha256(record: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


def _assert_forbidden_modules_absent(*, phase: str) -> None:
    loaded = sorted(
        name
        for name in sys.modules
        if any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in _FORBIDDEN_RUNTIME_MODULE_PREFIXES
        )
    )
    if loaded:
        _fail(f"forbidden runtime module loaded at {phase}: {loaded}")


def _assert_isolated_runtime() -> None:
    required_flags = {
        "isolated": 1,
        "safe_path": True,
        "no_user_site": 1,
        "ignore_environment": 1,
        "dont_write_bytecode": 1,
    }
    for field_name, expected in required_flags.items():
        if getattr(sys.flags, field_name, None) != expected:
            _fail(f"G3-P requires isolated Python -I -B ({field_name})")
    forbidden_entries = {"", os.getcwd(), str(Path(os.getcwd()) / "tools")}
    if forbidden_entries.intersection(sys.path):
        _fail("isolated Python sys.path contains cwd or tools")


def _module_origin(module: object, *, field_name: str) -> Path:
    file_value = getattr(module, "__file__", None)
    specification = getattr(module, "__spec__", None)
    origin_value = getattr(specification, "origin", None)
    if not isinstance(file_value, str) or not isinstance(origin_value, str):
        _fail(f"{field_name} lacks a concrete module origin")
    file_path = _absolute(file_value, field_name=f"{field_name} __file__")
    origin_path = _absolute(origin_value, field_name=f"{field_name} spec origin")
    if file_path != origin_path:
        _fail(f"{field_name} file/spec origins differ")
    return file_path


def _assert_runtime_module_origins(root: Path) -> dict[str, object]:
    try:
        import databento as databento_module
        import databento_dbn as databento_dbn_module
    except ImportError as exc:
        raise Test3G3PBoundaryError(
            "pinned Databento dependencies are unavailable before reservation"
        ) from exc
    expected_repo_modules = {
        "g3p": root / "src/mes_quant/exploration/test3_g3p_pre_fit.py",
        "core_hashing": root / "src/mes_quant/core/hashing.py",
        "test2_request_set": root / "src/mes_quant/exploration/test2_request_set.py",
        "test3_contract": root / "src/mes_quant/exploration/test3_contract.py",
        "test3_design": root / "src/mes_quant/exploration/test3_design.py",
        "test3_stats": root / "src/mes_quant/exploration/test3_stats.py",
        "test3_target": root / "src/mes_quant/exploration/test3_target.py",
    }
    module_names = {
        "g3p": __name__,
        "core_hashing": "mes_quant.core.hashing",
        "test2_request_set": "mes_quant.exploration.test2_request_set",
        "test3_contract": "mes_quant.exploration.test3_contract",
        "test3_design": "mes_quant.exploration.test3_design",
        "test3_stats": "mes_quant.exploration.test3_stats",
        "test3_target": "mes_quant.exploration.test3_target",
    }
    for label, expected in expected_repo_modules.items():
        observed = _module_origin(sys.modules[module_names[label]], field_name=label)
        if observed != expected:
            _fail(f"{label} module origin is outside the exact repository source path")
        relative = expected.relative_to(root).as_posix()
        if _git_output(root, "rev-parse", f"HEAD:{relative}") != _git_output(
            root, "hash-object", relative
        ):
            _fail(f"{label} working bytes differ from the execution commit")
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = (
        _absolute(sys.prefix, field_name="virtual environment")
        / "lib"
        / python_version
        / "site-packages"
    )
    site_modules = (
        ("numpy", np),
        ("pandas", pd),
        ("pyarrow", pa),
        ("parquet", pq),
        ("databento", databento_module),
        ("databento_dbn", databento_dbn_module),
    )
    for label, module in site_modules:
        try:
            _module_origin(module, field_name=label).relative_to(site_packages)
        except ValueError as exc:
            raise Test3G3PBoundaryError(
                f"{label} module origin is outside the exact virtual environment"
            ) from exc
    versions = {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "pyarrow": pa.__version__,
        "databento": distribution_version("databento"),
        "databento-dbn": distribution_version("databento-dbn"),
    }
    expected_versions = {
        "numpy": "2.0.2",
        "pandas": "2.2.2",
        "pyarrow": "18.1.0",
        "databento": "0.83.0",
        "databento-dbn": "0.65.0",
    }
    if versions != expected_versions:
        _fail(f"G3-P runtime dependency mismatch: {versions}")
    if _absolute(sys.executable, field_name="Python executable") != root / ".venv/bin/python":
        _fail("G3-P requires the repository virtual-environment Python")
    return {
        "python_executable": "${REPOSITORY}/.venv/bin/python",
        "python_isolated": True,
        "python_safe_path": True,
        "dependency_versions": versions,
        "repository_module_origins_verified": list(expected_repo_modules),
        "site_package_origins_verified": [label for label, _module in site_modules],
    }


def _databento_modules_loaded() -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name in sys.modules
            if name in {"databento", "databento_dbn"}
            or name.startswith(("databento.", "databento_dbn."))
        )
    )


@dataclass(frozen=True)
class DecodedIdentityEvidence:
    content_sha256: str
    row_count: int
    timestamp_min_utc: str
    timestamp_max_utc: str
    databento_modules_loaded: tuple[str, ...]


def _normalize_decoded_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.columns.has_duplicates:
        _invalid("DECODED_FRAME_TYPE_OR_DUPLICATE_COLUMN_INVALID")
    if isinstance(frame.index, pd.DatetimeIndex):
        indexed = frame
    elif "ts_event" in frame.columns:
        indexed = frame.set_index("ts_event")
    else:
        _invalid("DECODED_FRAME_TS_EVENT_INDEX_MISSING")
    missing = sorted(set(CELL2_HASH_COLUMNS).difference(indexed.columns))
    if missing:
        _invalid("DECODED_FRAME_HASH_COLUMNS_MISSING")
    index = indexed.index
    if not isinstance(index, pd.DatetimeIndex):
        _invalid("DECODED_FRAME_INDEX_NOT_DATETIME")
    if index.name != "ts_event" or index.tz is None or str(index.tz).upper() != "UTC":
        _invalid("DECODED_FRAME_UTC_INDEX_CONTRACT_MISMATCH")
    if index.has_duplicates or not index.is_monotonic_increasing:
        _invalid("DECODED_FRAME_INDEX_ORDER_OR_UNIQUENESS_MISMATCH")
    projected = indexed.loc[:, list(CELL2_HASH_COLUMNS)]
    if projected.empty or projected.isna().to_numpy().any():
        _invalid("DECODED_FRAME_EMPTY_OR_MISSING_HASH_VALUE")
    return projected


def _decoded_content_sha256(frame: pd.DataFrame) -> str:
    if tuple(frame.columns) != CELL2_HASH_COLUMNS:
        _invalid("DECODED_FRAME_COLUMN_ORDER_MISMATCH")
    hashed = pd.util.hash_pandas_object(
        frame.loc[:, list(CELL2_HASH_COLUMNS)],
        index=True,
        categorize=False,
    ).to_numpy(dtype=np.uint64, copy=False)
    return hashlib.sha256(hashed.tobytes()).hexdigest()


def decode_canonical_dbn(path: str | Path) -> tuple[pd.DataFrame, DecodedIdentityEvidence]:
    source = _absolute(path, field_name="canonical raw DBN")
    observed, _size = _hash_file(source)
    if observed != RAW_DBN_SHA256:
        _invalid("RAW_DBN_BYTE_SHA256_MISMATCH")
    try:
        import databento as _databento
    except ImportError as exc:  # pragma: no cover - pinned dependency in canonical runtime
        raise Test3G3PBoundaryError("pinned databento dependency is unavailable") from exc
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    databento_root = (
        _absolute(sys.prefix, field_name="virtual environment")
        / "lib"
        / python_version
        / "site-packages"
    )
    try:
        _module_origin(_databento, field_name="databento").relative_to(databento_root)
    except ValueError as exc:
        raise Test3G3PBoundaryError(
            "Databento module origin is outside the exact virtual environment"
        ) from exc
    if _databento.__version__ != "0.83.0":
        _fail("G3-P requires pinned Databento 0.83.0")
    decoded = _databento.DBNStore.from_file(source).to_df()
    frame = _normalize_decoded_frame(decoded)
    content_sha = _decoded_content_sha256(frame)
    if content_sha != DECODED_MES_1M_SHA256:
        _invalid("DECODED_CONTENT_SHA256_MISMATCH")
    timestamps = pd.DatetimeIndex(frame.index).tz_convert("UTC")
    return frame, DecodedIdentityEvidence(
        content_sha,
        len(frame),
        timestamps.min().isoformat(),
        timestamps.max().isoformat(),
        _databento_modules_loaded(),
    )


def _walk_keys(value: object) -> Iterator[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _expect_mapping_keys(
    value: object,
    expected: set[str] | frozenset[str],
    *,
    path: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        observed = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        _fail(f"G3-P record schema mismatch at {path}: observed={observed}")
    return value


def _assert_dependence_schema(value: object, *, path: str) -> None:
    section = _expect_mapping_keys(
        value,
        {"row_count", "lags", "design_effect", "effective_sample_size", "status"},
        path=path,
    )
    lags = section["lags"]
    if not isinstance(lags, list) or len(lags) != 8:
        _fail(f"G3-P dependence lag schema mismatch at {path}")
    for index, item in enumerate(lags):
        _expect_mapping_keys(
            item,
            {"lag", "pairs", "rho_observed", "rho_null", "excess"},
            path=f"{path}.lags[{index}]",
        )


def _assert_support_schema(value: object) -> None:
    if not isinstance(value, Mapping):
        _fail("G3-P support evidence is not a mapping")
    if value.get("status") == "NOT_COMPUTED_TARGET_ZERO_VARIANCE_TERMINAL":
        _expect_mapping_keys(
            value,
            {"status", "common_eligibility", "folds", "dependence"},
            path="support_evidence",
        )
        return
    support = _expect_mapping_keys(
        value,
        {
            "common_eligibility",
            "folds",
            "pooled_disjoint_oof_dependence",
            "harmonic_n_slots_observations",
            "harmonic_external_calendar_library_used",
            "structural_failures",
            "support_gate_status",
        },
        path="support_evidence",
    )
    _expect_mapping_keys(
        support["common_eligibility"],
        {
            "eligible_rows",
            "excluded_rows",
            "ordered_eligible_identity_sha256",
            "only_exact_usable_statuses",
        },
        path="support_evidence.common_eligibility",
    )
    folds = _expect_mapping_keys(
        support["folds"],
        set(FOLD_ORDER),
        path="support_evidence.folds",
    )
    fold_keys = {
        "pre_eligibility_holdout_rows",
        "eligible_train_rows",
        "eligible_holdout_rows",
        "holdout_session_count",
        "train_label_end_max_utc",
        "train_decision_max_utc",
        "holdout_start_utc",
        "boundary_gap_minutes_label_end_to_decision",
        "boundary_gap_minutes_decision_to_decision",
        "embargo_minutes",
        "models",
        "dependence",
    }
    rank_keys = {
        "row_count",
        "column_count",
        "rank",
        "full_rank",
        "singular_values",
        "condition_number",
        "finite",
    }
    for fold_id in FOLD_ORDER:
        fold = _expect_mapping_keys(
            folds[fold_id],
            fold_keys,
            path=f"support_evidence.folds.{fold_id}",
        )
        models = _expect_mapping_keys(
            fold["models"],
            set(MODEL_ORDER),
            path=f"support_evidence.folds.{fold_id}.models",
        )
        for model_id in MODEL_ORDER:
            rank = _expect_mapping_keys(
                models[model_id],
                rank_keys,
                path=f"support_evidence.folds.{fold_id}.models.{model_id}",
            )
            singular_values = rank["singular_values"]
            if not isinstance(singular_values, list) or len(singular_values) != len(
                MODEL_COLUMNS[model_id]
            ):
                _fail(f"G3-P singular-value schema mismatch for {fold_id}/{model_id}")
        _assert_dependence_schema(
            fold["dependence"],
            path=f"support_evidence.folds.{fold_id}.dependence",
        )
    _assert_dependence_schema(
        support["pooled_disjoint_oof_dependence"],
        path="support_evidence.pooled_disjoint_oof_dependence",
    )
    slots = _expect_mapping_keys(
        support["harmonic_n_slots_observations"],
        set(support["harmonic_n_slots_observations"]),
        path="support_evidence.harmonic_n_slots_observations",
    )
    if not slots or not set(slots).issubset({"10", "22"}):
        _fail("G3-P harmonic aggregate schema contains a non-frozen slot")
    failures = support["structural_failures"]
    if not isinstance(failures, list) or not all(isinstance(item, str) for item in failures):
        _fail("G3-P structural failure schema is malformed")


def _assert_success_record_schema(record: Mapping[str, object]) -> None:
    def section(name: str, keys: set[str]) -> Mapping[str, object]:
        return _expect_mapping_keys(record.get(name), keys, path=name)

    authorization = section(
        "authorization_binding",
        {
            "authorization_id",
            "authorization_document_sha256",
            "authorization_reservation_path",
            "authorization_reservation_sha256",
            "document_bindings",
        },
    )
    documents = _expect_mapping_keys(
        authorization["document_bindings"],
        set(_DOCUMENT_BINDINGS),
        path="authorization_binding.document_bindings",
    )
    for name in _DOCUMENT_BINDINGS:
        _expect_mapping_keys(
            documents[name],
            {"expected", "observed", "size_bytes", "match"},
            path=f"authorization_binding.document_bindings.{name}",
        )
    g2p = section(
        "g2p_predecessor_binding",
        {
            "evidence_commit",
            "execution_commit",
            "execution_tree",
            "record_path",
            "record_file_sha256",
            "record_semantic_sha256",
            "reservation_path",
            "reservation_sha256",
            "predictor_status_ledger",
            "outer_train_control_binding_sha256",
            "binding_status",
        },
    )
    ledger = _expect_mapping_keys(
        g2p["predictor_status_ledger"],
        {
            "hash_projection_id",
            "hash_serialization",
            "ordered_identity_sha256",
            "ordered_identity_status_sha256",
            "per_row_identities_persisted",
            "raw_predictor_values_persisted",
            "row_count",
            "status_counts",
        },
        path="g2p_predecessor_binding.predictor_status_ledger",
    )
    _expect_mapping_keys(
        ledger["status_counts"],
        set(_STATUS_ORDER),
        path="g2p_predecessor_binding.predictor_status_ledger.status_counts",
    )
    sources = section(
        "source_bindings",
        {"raw_dbn", "cell8", "cell10", "cell12", "cell14", "pre_target_support_contract"},
    )
    artifact_keys = {
        "filename",
        "byte_sha256",
        "size_bytes",
        "schema_names",
        "total_rows",
        "row_groups",
        "numeric_rows_read_during_preflight",
    }
    for artifact_id in ("raw_dbn", "cell8", "cell10", "cell12", "cell14"):
        _expect_mapping_keys(
            sources[artifact_id],
            artifact_keys,
            path=f"source_bindings.{artifact_id}",
        )
    pre_target = _expect_mapping_keys(
        sources["pre_target_support_contract"],
        {
            "status",
            "frozen_pre_eligibility_holdout_counts",
            "harmonic_n_slots_all_outer_train",
            "early_close_rows",
            "external_calendar_library_used",
        },
        path="source_bindings.pre_target_support_contract",
    )
    _expect_mapping_keys(
        pre_target["frozen_pre_eligibility_holdout_counts"],
        set(FOLD_ORDER),
        path="source_bindings.pre_target_support_contract.holdout_counts",
    )
    slots = pre_target["harmonic_n_slots_all_outer_train"]
    if not isinstance(slots, Mapping) or not slots or not set(slots).issubset({"10", "22"}):
        _fail("G3-P pre-target harmonic schema is malformed")
    runtime = section(
        "runtime_binding",
        {
            "python_executable",
            "python_isolated",
            "python_safe_path",
            "dependency_versions",
            "repository_module_origins_verified",
            "site_package_origins_verified",
        },
    )
    _expect_mapping_keys(
        runtime["dependency_versions"],
        {"numpy", "pandas", "pyarrow", "databento", "databento-dbn"},
        path="runtime_binding.dependency_versions",
    )
    definitions = section(
        "frozen_definitions",
        {
            "target_id",
            "target_horizon_minutes",
            "predictor_columns_ordered",
            "calendar_columns_ordered",
            "model_order",
            "ordered_model_definitions",
        },
    )
    _expect_mapping_keys(
        definitions["ordered_model_definitions"],
        set(MODEL_ORDER),
        path="frozen_definitions.ordered_model_definitions",
    )
    section(
        "decoded_identity",
        {
            "content_sha256",
            "row_count",
            "timestamp_min_utc",
            "timestamp_max_utc",
            "content_status",
            "hash_projection_id",
            "hash_columns",
            "hash_algorithm",
            "hash_includes_index",
            "decode_scope",
            "databento_modules_loaded",
        },
    )
    section(
        "counter_semantics",
        {"rows_read", "decode_scope", "decoded_frame_partition_filtering_claimed", "protected_target_rows"},
    )
    section(
        "request_set_binding",
        {
            "request_set_sha256",
            "parent_count",
            "request_key_count",
            "outer_validation_request_count",
            "final_test_request_count",
            "path_bar_offsets",
            "hashed_and_persisted_before_provider_lookup",
            "witness_path",
            "witness_sha256",
        },
    )
    section(
        "target_space_consumption",
        {
            "status",
            "witness_path",
            "witness_sha256",
            "retry_authorized",
            "successor_available",
            "repair_lineage_exhausted",
        },
    )
    predictor = section(
        "predictor_ledger_reproduction",
        {
            "row_count",
            "status_counts",
            "ordered_identity_sha256",
            "ordered_identity_status_sha256",
            "cell14_ordered_feature_sha256_declared",
            "matches_committed_g2p",
            "raw_values_persisted",
        },
    )
    _expect_mapping_keys(
        predictor["status_counts"],
        set(_STATUS_ORDER),
        path="predictor_ledger_reproduction.status_counts",
    )
    target = section(
        "target_status_ledger",
        {
            "row_count",
            "status_counts",
            "ordered_identity_time_status_sha256",
            "raw_values_persisted",
            "per_row_identities_persisted",
        },
    )
    _expect_mapping_keys(
        target["status_counts"],
        set(_TARGET_STATUS_ORDER),
        path="target_status_ledger.status_counts",
    )
    section(
        "cell12_reconciliation",
        {"status", "expectation_rows", "usable_rows", "unusable_rows", "absent_rows"},
    )
    section(
        "provider_counters",
        {"rows_examined", "missing_request_keys", "native_instrument_mismatch_keys"},
    )
    _assert_support_schema(record.get("support_evidence"))
    section(
        "fit_guard",
        {"guard_id", "installed_symbols", "blocked_fit_calls", "attempted_symbols", "status"},
    )
    section(
        "fit_authorization",
        {"status", "fit_permits_issued", "fit_completions", "coefficient_identities"},
    )
    section(
        "safety_counters",
        {
            "cell8_train_control_rows_read",
            "cell14_train_predictor_calendar_rows_read",
            "cell10_train_target_reference_rows_read",
            "cell12_train_path_rows_read",
            "outer_train_target_path_keys_read",
            "outer_train_target_rows_read",
            "targets_constructed",
            "outer_validation_target_rows_read",
            "final_test_target_rows_read",
            "real_fold_fit_calls",
            "real_models_fitted",
            "real_coefficients_computed",
            "real_forecasts_computed",
            "qlike_evaluations",
            "duan_factors_computed",
            "real_bootstrap_replicates",
            "economic_diagnostic_calls",
            "blocked_fit_calls",
            "outer_validation_predictor_rows_read",
            "final_test_predictor_rows_read",
        },
    )
    section("not_computed", set(_NOT_COMPUTED))


def _assert_closed_record(record: Mapping[str, object]) -> None:
    if record.get("gate_id") == G3P_GATE_ID:
        observed_top_level = frozenset(record)
        expected_top_level = (
            _RECORD_TOP_LEVEL_KEYS
            if "record_sha256" in record
            else _RECORD_TOP_LEVEL_KEYS - {"record_sha256"}
        )
        if observed_top_level != expected_top_level:
            _fail(
                "G3-P record top-level schema mismatch: "
                f"missing={sorted(expected_top_level - observed_top_level)}, "
                f"unexpected={sorted(observed_top_level - expected_top_level)}"
            )
        _assert_success_record_schema(record)

    def assert_bounded(value: object, *, path: str) -> None:
        if isinstance(value, Mapping):
            if len(value) > 128:
                _fail(f"G3-P record mapping exceeds aggregate bound at {path}")
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > 256:
                    _fail(f"G3-P record has an invalid mapping key at {path}")
                assert_bounded(child, path=f"{path}.{key}")
            return
        if isinstance(value, (list, tuple)):
            if len(value) > 128:
                _fail(f"G3-P record sequence exceeds aggregate bound at {path}")
            for index, child in enumerate(value):
                assert_bounded(child, path=f"{path}[{index}]")
            return
        if isinstance(value, str):
            if len(value) > 1_024:
                _fail(f"G3-P record string exceeds aggregate bound at {path}")
            return
        if value is None or isinstance(value, (bool, int)):
            return
        if isinstance(value, float) and math.isfinite(value):
            return
        _fail(f"G3-P record contains unsupported or nonfinite value at {path}")

    assert_bounded(record, path="record")
    forbidden = sorted(_FORBIDDEN_RECORD_KEYS.intersection(_walk_keys(record)))
    if forbidden:
        _fail("G3-P record contains forbidden row/value fields: " + ", ".join(forbidden))
    counters = record.get("safety_counters")
    if not isinstance(counters, Mapping):
        _fail("G3-P record lacks safety counters")
    for key in (
        "outer_validation_target_rows_read",
        "final_test_target_rows_read",
        "real_fold_fit_calls",
        "real_models_fitted",
        "real_coefficients_computed",
        "real_forecasts_computed",
        "qlike_evaluations",
        "duan_factors_computed",
        "real_bootstrap_replicates",
        "economic_diagnostic_calls",
        "blocked_fit_calls",
        "outer_validation_predictor_rows_read",
        "final_test_predictor_rows_read",
    ):
        if counters.get(key) != 0:
            _fail(f"G3-P protected counter is nonzero: {key}")


def _git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_sha(value: str, *, field_name: str) -> str:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        _fail(f"{field_name} must be a lowercase 40-character Git SHA")
    return value


def _assert_no_untracked_import_surface(root: Path) -> None:
    tracked = frozenset(
        filter(
            None,
            _git_output(root, "ls-files", "--", "src", "tests", "tools").splitlines(),
        )
    )
    candidates: set[str] = set()
    for arguments in (
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
        candidates.update(filter(None, _git_output(root, *arguments).splitlines()))
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


@dataclass(frozen=True)
class GitContext:
    commit: str
    tree: str
    branch: str
    upstream: str


def _git_context(root: Path) -> GitContext:
    commit = _git_sha(_git_output(root, "rev-parse", "HEAD"), field_name="HEAD")
    tree = _git_sha(_git_output(root, "rev-parse", "HEAD^{tree}"), field_name="HEAD tree")
    branch = _git_output(root, "branch", "--show-current")
    if branch != G3P_BRANCH:
        _fail(f"G3-P must execute on branch {G3P_BRANCH}")
    parents = _git_output(root, "rev-list", "--parents", "-n", "1", commit).split()
    if parents != [commit, G3P_BASE_COMMIT]:
        _fail("G3-P execution commit must be one direct child of the exact base")
    if _git_output(root, "rev-parse", f"{G3P_BASE_COMMIT}^{{tree}}") != G3P_BASE_TREE:
        _fail("G3-P base tree identity mismatch")
    changed = frozenset(
        line
        for line in _git_output(root, "diff", "--name-only", G3P_BASE_COMMIT, "HEAD").splitlines()
        if line
    )
    if changed != G3P_ALLOWED_CHANGED_FILES:
        _fail(
            "G3-P changed-file firewall mismatch: "
            f"missing={sorted(G3P_ALLOWED_CHANGED_FILES - changed)}, "
            f"unexpected={sorted(changed - G3P_ALLOWED_CHANGED_FILES)}"
        )
    if _git_output(root, "status", "--porcelain", "--untracked-files=no"):
        _fail("G3-P requires a clean tracked worktree")
    _assert_no_untracked_import_surface(root)
    try:
        upstream = _git_sha(
            _git_output(root, "rev-parse", "@{upstream}"),
            field_name="upstream",
        )
    except subprocess.CalledProcessError as exc:
        raise Test3G3PBoundaryError("G3-P branch must have a pushed upstream") from exc
    if upstream != commit:
        _fail("G3-P requires local/upstream commit equality")
    upstream_ref = _git_output(root, "rev-parse", "--symbolic-full-name", "@{upstream}")
    expected_ref = f"refs/remotes/origin/{G3P_BRANCH}"
    if upstream_ref != expected_ref:
        _fail(f"G3-P upstream must be exactly {expected_ref}")
    return GitContext(commit, tree, branch, upstream)


def _verify_documents(root: Path) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for relative, expected in _DOCUMENT_BINDINGS.items():
        observed, size = _hash_file(root / relative)
        if observed != expected:
            _fail(f"tracked document SHA-256 mismatch: {relative}")
        bindings[relative] = {
            "expected": expected,
            "observed": observed,
            "size_bytes": size,
            "match": True,
        }
    return bindings


def _verify_g2p_evidence(root: Path) -> dict[str, object]:
    parents = _git_output(
        root, "rev-list", "--parents", "-n", "1", G2P_EVIDENCE_COMMIT
    ).split()
    if parents != [G2P_EVIDENCE_COMMIT, G2P_EXECUTION_COMMIT]:
        _fail("G2-P evidence ancestry mismatch")
    if _git_output(root, "rev-parse", f"{G2P_EXECUTION_COMMIT}^{{tree}}") != G2P_EXECUTION_TREE:
        _fail("G2-P execution tree mismatch")
    record = _strict_json(root / G2P_RECORD_PATH, expected_sha256=G2P_RECORD_FILE_SHA256)
    if record.get("record_sha256") != G2P_RECORD_SEMANTIC_SHA256:
        _fail("G2-P semantic hash pin mismatch")
    if _record_sha256(record) != G2P_RECORD_SEMANTIC_SHA256:
        _fail("G2-P semantic hash recomputation mismatch")
    expected = {
        "execution_commit": G2P_EXECUTION_COMMIT,
        "execution_tree": G2P_EXECUTION_TREE,
        "stage_status": "G2P_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT_PASS",
        "target_space_consumption_status": "NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT",
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "g3p_status": "NOT_AUTHORIZED",
        "g3f_status": "NOT_AUTHORIZED",
    }
    for field_name, value in expected.items():
        if record.get(field_name) != value:
            _fail(f"G2-P evidence field mismatch: {field_name}")
    ledger = record.get("predictor_status_ledger")
    if not isinstance(ledger, Mapping):
        _fail("G2-P evidence predictor ledger is malformed")
    source_bindings = record.get("source_bindings")
    if not isinstance(source_bindings, Mapping):
        _fail("G2-P evidence source bindings are malformed")
    control_binding = source_bindings.get("outer_train_control_binding_sha256")
    if not isinstance(control_binding, str) or len(control_binding) != 64:
        _fail("G2-P evidence control binding is malformed")
    reservation = _strict_json(
        root / G2P_RESERVATION_PATH,
        expected_sha256=G2P_RESERVATION_SHA256,
    )
    if (
        reservation.get("execution_commit") != G2P_EXECUTION_COMMIT
        or reservation.get("status") != "CONSUMED_BEFORE_PREDICTOR_ACCESS"
    ):
        _fail("G2-P reservation binding mismatch")
    return {
        "evidence_commit": G2P_EVIDENCE_COMMIT,
        "execution_commit": G2P_EXECUTION_COMMIT,
        "execution_tree": G2P_EXECUTION_TREE,
        "record_path": "${REPOSITORY}/" + G2P_RECORD_PATH,
        "record_file_sha256": G2P_RECORD_FILE_SHA256,
        "record_semantic_sha256": G2P_RECORD_SEMANTIC_SHA256,
        "reservation_path": "${REPOSITORY}/" + G2P_RESERVATION_PATH,
        "reservation_sha256": G2P_RESERVATION_SHA256,
        "predictor_status_ledger": dict(ledger),
        "outer_train_control_binding_sha256": control_binding,
        "binding_status": "EXACT_COMMITTED_G2P_PASS_VERIFIED",
    }


@dataclass(frozen=True)
class ObservedAuthorization:
    reservation_path: Path
    reservation_sha256: str


def _consume_authorization(
    root: Path,
    *,
    git_context: GitContext,
    authorization_token: str,
) -> ObservedAuthorization:
    if authorization_token != G3P_AUTHORIZATION_TOKEN:
        _fail("G3-P Owner authorization token mismatch")
    observed, _size = _hash_file(root / G3P_AUTHORIZATION_DOCUMENT)
    if observed != G3P_AUTHORIZATION_DOCUMENT_SHA256:
        _fail("G3-P Owner authorization document mismatch")
    reservation = root / AUTHORIZATION_RESERVATION_PATH
    payload = {
        "authorization_id": G3P_AUTHORIZATION_ID,
        "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
        "authorization_token_sha256": hashlib.sha256(
            G3P_AUTHORIZATION_TOKEN.encode("utf-8")
        ).hexdigest(),
        "base_commit": G3P_BASE_COMMIT,
        "execution_commit": git_context.commit,
        "execution_tree": git_context.tree,
        "branch": git_context.branch,
        "g2p_evidence_commit": G2P_EVIDENCE_COMMIT,
        "status": "CONSUMED_BEFORE_ANY_SOURCE_ARTIFACT_ACCESS",
        "consumed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "retry_authorized": False,
        "merge_authorized": False,
    }
    try:
        digest = _atomic_create_json(reservation, payload)
    except FileExistsError as exc:
        raise Test3G3PBoundaryError("G3-P authorization is already consumed") from exc
    return ObservedAuthorization(reservation, digest)


@dataclass(frozen=True)
class ArtifactPaths:
    raw_dbn: Path
    cell8: Path
    cell10: Path
    cell12: Path
    cell14: Path


def _validate_canonical_paths(root: Path, paths: ArtifactPaths) -> None:
    observed = {
        "raw_dbn": paths.raw_dbn,
        "cell8": paths.cell8,
        "cell10": paths.cell10,
        "cell12": paths.cell12,
        "cell14": paths.cell14,
    }
    for artifact_id, path in observed.items():
        if path != root / _CANONICAL_RELATIVE_PATHS[artifact_id]:
            _fail(f"{artifact_id} requires the exact repo-local canonical path")


_ARTIFACT_SPECS = {
    "raw_dbn": (RAW_DBN_FILENAME, RAW_DBN_SHA256, ()),
    "cell8": (CELL8_FILENAME, CELL8_SPLIT_ASSIGNMENT_SHA256, CONTROL_COLUMNS),
    "cell10": (CELL10_FILENAME, CELL10_LABEL_SHA256, CELL10_COLUMNS),
    "cell12": (CELL12_FILENAME, CELL12_PATH_SHA256, CELL12_COLUMNS),
    "cell14": (CELL14_FILENAME, CELL14_FEATURE_FILE_SHA256, CELL14_COLUMNS),
}


def _preflight_sources(paths: ArtifactPaths) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for artifact_id, path in (
        ("raw_dbn", paths.raw_dbn),
        ("cell8", paths.cell8),
        ("cell10", paths.cell10),
        ("cell12", paths.cell12),
        ("cell14", paths.cell14),
    ):
        filename, expected_sha, columns = _ARTIFACT_SPECS[artifact_id]
        if path.name != filename:
            _fail(f"{artifact_id} requires canonical filename {filename}")
        observed, size = _hash_file(path)
        if observed != expected_sha:
            _invalid(f"{artifact_id.upper()}_BYTE_SHA256_MISMATCH")
        schema_names: list[str] = []
        total_rows: int | None = None
        row_groups: int | None = None
        if columns:
            with _open_regular_file(path) as stream:
                parquet = pq.ParquetFile(stream)
                schema_names = list(parquet.schema_arrow.names)
                missing = sorted(set(columns).difference(schema_names))
                if missing:
                    _invalid(f"{artifact_id.upper()}_SCHEMA_MISSING_{'_'.join(missing)}")
                total_rows = int(parquet.metadata.num_rows)
                row_groups = int(parquet.metadata.num_row_groups)
        bindings[artifact_id] = {
            "filename": filename,
            "byte_sha256": observed,
            "size_bytes": size,
            "schema_names": schema_names,
            "total_rows": total_rows,
            "row_groups": row_groups,
            "numeric_rows_read_during_preflight": 0,
        }
    return bindings


def _read_train_projection(
    path: Path,
    *,
    expected_sha256: str,
    columns: tuple[str, ...],
    field_name: str,
) -> pa.Table:
    with _open_regular_file(path) as stream:
        before_sha, before_size = _sha256_stream(stream)
        if before_sha != expected_sha256:
            _invalid(f"{field_name.upper()}_BYTE_SHA256_MISMATCH")
        table = pq.read_table(
            stream,
            columns=list(columns),
            filters=[("outer_partition", "==", "TRAIN")],
            use_threads=False,
        )
        after_sha, after_size = _sha256_stream(stream)
    if (after_sha, after_size) != (before_sha, before_size):
        _fail(f"{field_name} changed during projection")
    if table.num_rows != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid(f"{field_name.upper()}_TRAIN_ROW_COUNT_MISMATCH")
    if tuple(table.column_names) != columns:
        _invalid(f"{field_name.upper()}_PROJECTION_MISMATCH")
    if table.column("outer_partition").to_pylist() != ["TRAIN"] * EXPECTED_OUTER_TRAIN_ROWS:
        _invalid(f"{field_name.upper()}_NON_TRAIN_ROW_EXPOSED")
    return table


def _utc(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(f"{field_name.upper()}_INVALID")
    return value.astimezone(UTC)


def _identity(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        _invalid("DECISION_ID_MISSING_OR_INVALID")
    if "\r" in value or "\n" in value:
        _invalid("DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT")
    return value


def _instrument(value: object) -> str:
    if value is None or isinstance(value, bool):
        _invalid("INSTRUMENT_ID_MISSING_OR_INVALID")
    if isinstance(value, (int, float, np.integer, np.floating)):
        numeric = float(value)
        if not math.isfinite(numeric):
            _invalid("INSTRUMENT_ID_NONFINITE")
        if numeric.is_integer():
            return str(int(numeric))
    return str(value)


def _session(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        return value
    _invalid("NYSE_SESSION_DATE_INVALID")


@dataclass(frozen=True)
class ControlRow:
    identity: str
    timestamp: datetime
    session_id: str
    instrument: str
    role_2022: str
    role_2023: str


def _control_rows(table: pa.Table, *, field_name: str) -> tuple[ControlRow, ...]:
    rows: list[ControlRow] = []
    seen_ids: set[str] = set()
    seen_times: set[datetime] = set()
    previous: tuple[datetime, str] | None = None
    for raw in table.select(CONTROL_COLUMNS).to_pylist():
        identity = _identity(raw.get("decision_id"))
        timestamp = _utc(raw.get("decision_time"), field_name="decision_time")
        order_key = (timestamp, identity)
        if identity in seen_ids or timestamp in seen_times:
            _invalid(f"{field_name.upper()}_CONTROL_DUPLICATE")
        if previous is not None and order_key <= previous:
            _invalid(f"{field_name.upper()}_CONTROL_SOURCE_ORDER_INVERSION")
        if raw.get("outer_partition") != "TRAIN" or timestamp >= OUTER_VALIDATION_BOUNDARY_UTC:
            _invalid(f"{field_name.upper()}_NON_TRAIN_CONTROL")
        roles = (str(raw.get("role_wf_2022")), str(raw.get("role_wf_2023")))
        if any(role not in {"TRAIN", "VALIDATION", "UNUSED"} for role in roles):
            _invalid(f"{field_name.upper()}_FOLD_ROLE_INVALID")
        rows.append(
            ControlRow(
                identity,
                timestamp,
                _session(raw.get("nyse_session_date")),
                _instrument(raw.get("instrument_id")),
                roles[0],
                roles[1],
            )
        )
        seen_ids.add(identity)
        seen_times.add(timestamp)
        previous = order_key
    if len(rows) != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid(f"{field_name.upper()}_CONTROL_INCOMPLETE")
    return tuple(rows)


def _control_binding(rows: Sequence[ControlRow]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            [
                [
                    row.identity,
                    row.timestamp.isoformat(),
                    row.instrument,
                    "TRAIN",
                    row.role_2022,
                    row.role_2023,
                ]
                for row in rows
            ]
        )
    )


def _optional_number(value: object, *, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        _invalid(f"{field_name.upper()}_TYPE_INVALID")
    return float(value)


def _required_finite(value: object, *, field_name: str) -> float:
    numeric = _optional_number(value, field_name=field_name)
    if numeric is None or not math.isfinite(numeric):
        _invalid(f"{field_name.upper()}_NONFINITE_OR_MISSING")
    return numeric


def _normalize_early_close_session(value: object) -> bool:
    """Normalize one producer ``early_close_session`` flag to the local boolean contract.

    Native ``bool`` and ``numpy.bool_`` producers keep their existing accepted contract
    unchanged. Producer-side integral ``0``/``1`` flags (for example Arrow ``int8``) are the
    known Cell 14 consumer landmine; they are normalized through the shared boundary helper
    instead of being rejected. Every other input — non-integral, float, string, null/missing and
    out-of-domain integral — fails closed with exactly ``EARLY_CLOSE_SESSION_TYPE_INVALID``.
    """

    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    try:
        return normalize_integral_flag(value)
    except BoundaryValidationError:
        _invalid("EARLY_CLOSE_SESSION_TYPE_INVALID")


@dataclass(frozen=True)
class PredictorData:
    status_rows: tuple[PredictorStatusRow, ...]
    values: Mapping[str, tuple[float | None, float | None, float | None]]
    calendar: Mapping[str, tuple[float, float, bool]]
    status_counts: Mapping[str, int]
    ordered_identity_sha256: str
    ordered_identity_status_sha256: str


def _predictor_data(
    table: pa.Table,
    controls: tuple[ControlRow, ...],
    *,
    expected_ledger: Mapping[str, object],
) -> PredictorData:
    rows = table.to_pylist()
    statuses: list[PredictorStatusRow] = []
    values_by_id: dict[str, tuple[float | None, float | None, float | None]] = {}
    calendar_by_id: dict[str, tuple[float, float, bool]] = {}
    for control, raw in zip(controls, rows, strict=True):
        values = tuple(
            _optional_number(raw.get(column), field_name=column)
            for column in PREDICTOR_COLUMNS
        )
        present = tuple(value for value in values if value is not None)
        if any(not math.isfinite(value) for value in present):
            status = FailureReason.PREDICTOR_NONFINITE.value
        elif any(value <= 0.0 for value in present):
            status = FailureReason.PREDICTOR_NONPOSITIVE.value
        elif any(value is None for value in values):
            status = RowStatus.PREDICTOR_UNUSABLE.value
        else:
            status = RowStatus.PREDICTOR_USABLE.value
        statuses.append(PredictorStatusRow(control.identity, control.timestamp, status))
        values_by_id[control.identity] = values
        minutes_since = _required_finite(
            raw.get("minutes_since_nyse_open"),
            field_name="minutes_since_nyse_open",
        )
        minutes_to_safe = _required_finite(
            raw.get("minutes_to_horizon_safe_close"),
            field_name="minutes_to_horizon_safe_close",
        )
        early_flag = _normalize_early_close_session(raw.get("early_close_session"))
        calendar_by_id[control.identity] = (minutes_since, minutes_to_safe, early_flag)
    status_rows = tuple(statuses)
    counts_raw = Counter(row.status for row in status_rows)
    counts = {status: int(counts_raw[status]) for status in _STATUS_ORDER}
    identity_payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}\n" for row in status_rows
    ).encode("utf-8")
    status_payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}|{row.status}\n"
        for row in status_rows
    ).encode("utf-8")
    identity_sha = hashlib.sha256(identity_payload).hexdigest()
    status_sha = hashlib.sha256(status_payload).hexdigest()
    expected = {
        "row_count": len(status_rows),
        "status_counts": counts,
        "ordered_identity_sha256": identity_sha,
        "ordered_identity_status_sha256": status_sha,
    }
    for field_name, observed in expected.items():
        if expected_ledger.get(field_name) != observed:
            _invalid(f"G2P_PREDICTOR_LEDGER_{field_name.upper()}_MISMATCH")
    if counts[FailureReason.PREDICTOR_NONFINITE.value] or counts[
        FailureReason.PREDICTOR_NONPOSITIVE.value
    ]:
        _invalid("G2P_TERMINAL_PREDICTOR_STATUS_REAPPEARED")
    return PredictorData(
        status_rows,
        values_by_id,
        calendar_by_id,
        counts,
        identity_sha,
        status_sha,
    )


def _persist_request_set_witness(
    root: Path,
    *,
    sealed: StreamingSealedRequestSet,
    git_context: GitContext,
    authorization: ObservedAuthorization,
) -> tuple[Path, str]:
    if sealed.validation_path_bar_lookup_count or sealed.final_test_path_bar_lookup_count:
        _fail("protected request count is nonzero before request-set witness")
    path = root / REQUEST_SET_WITNESS_PATH
    payload = {
        "gate_id": G3P_GATE_ID,
        "authorization_id": G3P_AUTHORIZATION_ID,
        "authorization_reservation_sha256": authorization.reservation_sha256,
        "execution_commit": git_context.commit,
        "execution_tree": git_context.tree,
        "cell8_split_assignment_sha256": CELL8_SPLIT_ASSIGNMENT_SHA256,
        "request_set_sha256": sealed.request_set_sha256,
        "parent_count": len(sealed.decisions),
        "request_key_count": sealed.key_count,
        "outer_validation_request_count": sealed.validation_path_bar_lookup_count,
        "final_test_request_count": sealed.final_test_path_bar_lookup_count,
        "per_key_identities_persisted": False,
        "status": "SEALED_AND_PERSISTED_BEFORE_PROVIDER_ACCESS",
        "sealed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    try:
        digest = _atomic_create_json(path, payload)
    except FileExistsError as exc:
        raise Test3G3PBoundaryError("G3-P request-set witness already exists") from exc
    return path, digest


def _consume_target_space(
    root: Path,
    *,
    sealed: StreamingSealedRequestSet,
    git_context: GitContext,
    authorization_reservation_sha256: str,
    request_witness_sha256: str,
) -> tuple[Path, str]:
    path = root / TARGET_SPACE_WITNESS_PATH
    payload = {
        "target_space_id": TARGET_SPACE_ID,
        "target_space_state": "CONSUMED",
        "authorization_id": G3P_AUTHORIZATION_ID,
        "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
        "authorization_reservation_sha256": authorization_reservation_sha256,
        "execution_commit": git_context.commit,
        "execution_tree": git_context.tree,
        "request_set_sha256": sealed.request_set_sha256,
        "request_set_witness_sha256": request_witness_sha256,
        "status": "CONSUMED_IMMEDIATELY_BEFORE_FIRST_NUMERIC_TARGET_OR_PATH_READ",
        "consumed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "retry_authorized": False,
        "replacement_target_authorized": False,
    }
    try:
        digest = _atomic_create_json(path, payload)
    except FileExistsError as exc:
        raise Test3G3PBoundaryError("TARGET_SPACE_003 is already consumed") from exc
    return path, digest


@dataclass(frozen=True)
class TargetReference:
    entry: float | None
    endpoint: float | None


@dataclass(frozen=True)
class Cell12Expectation:
    entry: float | None
    endpoint: float | None
    path_status: str
    path_usable: bool
    path_1m_present: int | None
    path_instrument_changed: bool | None
    path_high: float | None
    path_low: float | None
    long_mfe: float | None
    long_mae: float | None


def _references(table: pa.Table, controls: tuple[ControlRow, ...]) -> dict[str, TargetReference]:
    result: dict[str, TargetReference] = {}
    for control, raw in zip(controls, table.to_pylist(), strict=True):
        result[control.identity] = TargetReference(
            _optional_number(raw.get("entry_reference_close"), field_name="entry_reference_close"),
            _optional_number(
                raw.get("exit_reference_close_60m"),
                field_name="exit_reference_close_60m",
            ),
        )
    return result


def _strict_bool(value: object, *, field_name: str) -> bool:
    if not isinstance(value, (bool, np.bool_)):
        _invalid(f"{field_name.upper()}_TYPE_INVALID")
    return bool(value)


def _optional_count(value: object, *, field_name: str) -> int | None:
    numeric = _optional_number(value, field_name=field_name)
    if numeric is None:
        return None
    if not math.isfinite(numeric) or not numeric.is_integer() or numeric < 0:
        _invalid(f"{field_name.upper()}_INVALID")
    return int(numeric)


def _cell12_expectations(
    table: pa.Table,
    controls: tuple[ControlRow, ...],
) -> dict[str, Cell12Expectation]:
    result: dict[str, Cell12Expectation] = {}
    for control, raw in zip(controls, table.to_pylist(), strict=True):
        status = str(raw.get("path_status"))
        usable = _strict_bool(raw.get("path_usable"), field_name="path_usable")
        if status == CELL12_STATUS_SEALED_FINAL_TEST:
            _invalid("CELL12_SEALED_FINAL_TEST_ROW_EXPOSED")
        if usable and status != CELL12_STATUS_USABLE:
            _invalid("CELL12_USABLE_STATUS_MISMATCH")
        if not usable and status not in CELL12_UNUSABLE_STATUSES:
            _invalid("CELL12_UNUSABLE_STATUS_MISMATCH")
        numeric = tuple(
            _optional_number(raw.get(column), field_name=column)
            for column in (
                "path_high_60m",
                "path_low_60m",
                "long_mfe_points_60m",
                "long_mae_points_60m",
            )
        )
        present = _optional_count(raw.get("path_1m_present"), field_name="path_1m_present")
        instrument_changed_raw = raw.get("path_instrument_changed")
        if status == CELL12_STATUS_LABEL_UNUSABLE and instrument_changed_raw is None:
            instrument_changed = None
        else:
            instrument_changed = _strict_bool(
                instrument_changed_raw,
                field_name="path_instrument_changed",
            )
        if usable:
            if present != TARGET_BAR_COUNT or any(
                value is None or not math.isfinite(value) for value in numeric
            ):
                _invalid("CELL12_USABLE_NUMERIC_CONTRACT_MISMATCH")
        else:
            if any(value is not None for value in numeric):
                _invalid("CELL12_UNUSABLE_NUMERIC_FIELDS_PRESENT")
            if status == CELL12_STATUS_PATH_INTEGRITY_FAILURE and (
                present is None or not 0 <= present < TARGET_BAR_COUNT
            ):
                _invalid("CELL12_UNUSABLE_PATH_COUNT_CONTRACT_MISMATCH")
            if status == CELL12_STATUS_LABEL_UNUSABLE and (
                present is not None and not 0 <= present <= TARGET_BAR_COUNT
            ):
                _invalid("CELL12_LABEL_UNUSABLE_PATH_COUNT_CONTRACT_MISMATCH")
        result[control.identity] = Cell12Expectation(
            _optional_number(raw.get("entry_reference_close"), field_name="entry_reference_close"),
            _optional_number(
                raw.get("exit_reference_close_60m"),
                field_name="exit_reference_close_60m",
            ),
            status,
            usable,
            present,
            instrument_changed,
            numeric[0],
            numeric[1],
            numeric[2],
            numeric[3],
        )
    return result


@dataclass(frozen=True)
class ObservedBar:
    offset: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float


def _same_instrument(observed: object, expected: str) -> bool:
    if pd.isna(observed):
        return False
    if isinstance(observed, (int, float, np.integer, np.floating)):
        numeric = float(observed)
        return math.isfinite(numeric) and _instrument(numeric) == expected
    return str(observed) == expected


class SealedFrameProvider:
    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        sealed: StreamingSealedRequestSet,
        instruments: Mapping[str, str],
    ) -> None:
        required = ("open", "high", "low", "close", "instrument_id")
        if tuple(frame.columns) != required:
            _invalid("DECODED_PROVIDER_PROJECTION_MISMATCH")
        if set(instruments) != {item.decision_identity for item in sealed.decisions}:
            _invalid("PROVIDER_INSTRUMENT_MAP_COVERAGE_MISMATCH")
        self._frame = frame
        self._index = pd.DatetimeIndex(frame.index).tz_convert("UTC")
        self._values = frame.loc[:, list(required)].to_numpy()
        self._sealed_hash = sealed.request_set_sha256
        self._times = {
            item.decision_identity: item.decision_time_utc.astimezone(UTC)
            for item in sealed.decisions
        }
        self._instruments = dict(instruments)
        self.rows_examined = 0
        self.missing_keys = 0
        self.instrument_mismatch_keys = 0

    def fetch_path_bar_batch(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> Mapping[RequestKey, ObservedBar]:
        if request_set_sha256 != self._sealed_hash:
            _invalid("PROVIDER_REQUEST_SET_SHA256_MISMATCH")
        requested: list[datetime] = []
        for key in request_keys:
            parent_time = self._times.get(key.decision_identity)
            normalized = key.requested_timestamp_utc.astimezone(UTC)
            if (
                parent_time is None
                or key.minute_offset not in range(TARGET_BAR_COUNT)
                or normalized != parent_time + timedelta(minutes=key.minute_offset)
            ):
                _invalid("PROVIDER_UNSEALED_OR_MALFORMED_KEY")
            requested.append(normalized)
        if not requested:
            return {}
        positions = self._index.get_indexer(pd.DatetimeIndex(requested).tz_convert("UTC"))
        result: dict[RequestKey, ObservedBar] = {}
        for key, position in zip(request_keys, positions, strict=True):
            if position < 0:
                self.missing_keys += 1
                continue
            self.rows_examined += 1
            row = self._values[position]
            if not _same_instrument(row[4], self._instruments[key.decision_identity]):
                self.instrument_mismatch_keys += 1
                _invalid("NATIVE_INSTRUMENT_MISMATCH")
            result[key] = ObservedBar(
                key.minute_offset,
                float(row[0]),
                float(row[1]),
                float(row[2]),
                float(row[3]),
            )
        return result


def _positive(value: object, *, field_name: str) -> float:
    numeric = _required_finite(value, field_name=field_name)
    if numeric <= 0.0:
        _invalid(f"{field_name.upper()}_NONPOSITIVE")
    return numeric


def _ticks(value: object, *, field_name: str) -> int:
    numeric = _required_finite(value, field_name=field_name)
    scaled = numeric * 4.0
    if not scaled.is_integer():
        _invalid(f"{field_name.upper()}_OFF_TICK_GRID")
    return int(scaled)


def _target_row(
    control: ControlRow,
    reference: TargetReference,
    bars: tuple[ObservedBar, ...],
) -> TargetStatusRow:
    label_end = control.timestamp + timedelta(minutes=TARGET_HORIZON_MINUTES)
    if reference.entry is None or reference.endpoint is None or len(bars) != TARGET_BAR_COUNT:
        return TargetStatusRow(
            control.identity,
            control.timestamp,
            label_end,
            RowStatus.TARGET_UNUSABLE.value,
            None,
            None,
        )
    offsets = tuple(bar.offset for bar in bars)
    if offsets != tuple(range(TARGET_BAR_COUNT)):
        _invalid("TARGET_PATH_KEY_ORDER_OR_DUPLICATE_DEFECT")
    entry = _positive(reference.entry, field_name="entry_reference_close")
    endpoint = _positive(reference.endpoint, field_name="exit_reference_close_60m")
    closes = tuple(_positive(bar.close_price, field_name="path_close") for bar in bars)
    if closes[-1] != endpoint:
        _invalid("TARGET_ENDPOINT_MISMATCH")
    variance = 0.0
    prior = entry
    for close in closes:
        return_value = math.log(close / prior)
        variance += return_value * return_value
        prior = close
    if not math.isfinite(variance):
        _invalid("TARGET_VARIANCE_NONFINITE")
    if variance == 0.0:
        return TargetStatusRow(
            control.identity,
            control.timestamp,
            label_end,
            FailureReason.TARGET_ZERO_VARIANCE.value,
            0.0,
            None,
        )
    log_variance = math.log(variance)
    if not math.isfinite(log_variance):
        _invalid("TARGET_LOG_VARIANCE_NONFINITE")
    return TargetStatusRow(
        control.identity,
        control.timestamp,
        label_end,
        RowStatus.TARGET_USABLE.value,
        variance,
        log_variance,
    )


def _reconcile_cell12(
    reference: TargetReference,
    expectation: Cell12Expectation,
    bars: tuple[ObservedBar, ...],
) -> str:
    if reference.entry != expectation.entry or reference.endpoint != expectation.endpoint:
        _invalid("CELL10_CELL12_REFERENCE_MISMATCH")
    complete = (
        len(bars) == TARGET_BAR_COUNT
        and reference.entry is not None
        and reference.endpoint is not None
    )
    if expectation.path_status == CELL12_STATUS_LABEL_UNUSABLE:
        return "LABEL_UNUSABLE_NOT_USED_AS_TEST3_PATH_ATTESTATION"
    if expectation.path_status == CELL12_STATUS_PATH_INTEGRITY_FAILURE:
        if expectation.path_1m_present != len(bars):
            _invalid("CELL12_PATH_INTEGRITY_PRESENT_COUNT_MISMATCH")
        if complete:
            _invalid("CELL12_PATH_INTEGRITY_ROW_RECOMPUTED_COMPLETE_PATH")
        return "EXACT_PATH_INTEGRITY_FAILURE_COUNT_RECONCILIATION_PASS"
    if not expectation.path_usable:
        _invalid("CELL12_UNUSABLE_STATUS_RECONCILIATION_UNREACHABLE")
    if expectation.path_instrument_changed is not False:
        _invalid("CELL12_USABLE_ROW_DECLARES_INSTRUMENT_CHANGE")
    if not complete:
        _invalid("CELL12_USABLE_ROW_RECOMPUTED_INCOMPLETE_PATH")
    assert reference.entry is not None
    observed = (
        max(_ticks(bar.high_price, field_name="path_high") for bar in bars),
        min(_ticks(bar.low_price, field_name="path_low") for bar in bars),
    )
    entry_ticks = _ticks(reference.entry, field_name="entry_reference_close")
    observed_metrics = (
        observed[0],
        observed[1],
        max(observed[0] - entry_ticks, 0),
        max(entry_ticks - observed[1], 0),
    )
    expected_metrics = (
        _ticks(expectation.path_high, field_name="cell12_path_high"),
        _ticks(expectation.path_low, field_name="cell12_path_low"),
        _ticks(expectation.long_mfe, field_name="cell12_long_mfe"),
        _ticks(expectation.long_mae, field_name="cell12_long_mae"),
    )
    if observed_metrics != expected_metrics:
        _invalid("CELL12_EXACT_TICK_RECONCILIATION_MISMATCH")
    return "EXACT_TICK_RECONCILIATION_PASS"


@dataclass(frozen=True)
class TargetBuildResult:
    rows: tuple[TargetStatusRow, ...]
    variance_by_identity: Mapping[str, float]
    status_counts: Mapping[str, int]
    ordered_status_sha256: str
    usable_cell12_rows: int
    unusable_cell12_rows: int
    provider_rows_examined: int
    missing_request_keys: int
    instrument_mismatch_keys: int


def _build_targets(
    sealed: StreamingSealedRequestSet,
    controls: tuple[ControlRow, ...],
    references: Mapping[str, TargetReference],
    cell12: Mapping[str, Cell12Expectation],
    provider: SealedFrameProvider,
) -> TargetBuildResult:
    control_by_id = {row.identity: row for row in controls}
    identities = set(control_by_id)
    if set(references) != identities or set(cell12) != identities:
        _invalid("TARGET_REFERENCE_OR_CELL12_COVERAGE_MISMATCH")
    bars_by_id: dict[str, list[ObservedBar]] = defaultdict(list)
    target_rows: list[TargetStatusRow] = []
    variances: dict[str, float] = {}
    reconciliation_counts: Counter[str] = Counter()
    processed_keys = 0
    finalized = 0

    def finalize_through(stop: int) -> None:
        nonlocal finalized
        while finalized < stop:
            parent = sealed.decisions[finalized]
            identity = parent.decision_identity
            bars = tuple(sorted(bars_by_id.pop(identity, ()), key=lambda bar: bar.offset))
            reference = references[identity]
            reconciliation = _reconcile_cell12(reference, cell12[identity], bars)
            reconciliation_counts[reconciliation] += 1
            row = _target_row(control_by_id[identity], reference, bars)
            target_rows.append(row)
            if row.rv_fwd_60 is not None:
                variances[identity] = float(row.rv_fwd_60)
            finalized += 1

    for batch in iter_path_bar_batches(sealed, provider, batch_size=G3P_BATCH_SIZE):
        for key, bar in batch.items():
            bars_by_id[key.decision_identity].append(bar)
        processed_keys += min(G3P_BATCH_SIZE, sealed.key_count - processed_keys)
        finalize_through(processed_keys // TARGET_BAR_COUNT)
    if processed_keys != sealed.key_count:
        _invalid("SEALED_REQUEST_TRAVERSAL_INCOMPLETE")
    finalize_through(len(sealed.decisions))
    if bars_by_id:
        _invalid("PATH_BATCH_RETENTION_DID_NOT_DRAIN")
    rows = tuple(target_rows)
    counts_raw = Counter(row.status for row in rows)
    counts = {status: int(counts_raw[status]) for status in _TARGET_STATUS_ORDER}
    payload = "".join(
        f"{row.decision_identity}|{row.decision_time.isoformat()}|"
        f"{row.label_end_time.isoformat()}|{row.status}\n"
        for row in rows
    ).encode("utf-8")
    return TargetBuildResult(
        rows,
        variances,
        counts,
        hashlib.sha256(payload).hexdigest(),
        reconciliation_counts["EXACT_TICK_RECONCILIATION_PASS"],
        (
            reconciliation_counts["LABEL_UNUSABLE_NOT_USED_AS_TEST3_PATH_ATTESTATION"]
            + reconciliation_counts[
                "EXACT_PATH_INTEGRITY_FAILURE_COUNT_RECONCILIATION_PASS"
            ]
        ),
        provider.rows_examined,
        provider.missing_keys,
        provider.instrument_mismatch_keys,
    )


@dataclass(frozen=True)
class FitGuard:
    installed: tuple[str, ...]
    blocked_fit_calls: int
    attempted: tuple[str, ...]


@dataclass
class _MutableFitGuard:
    installed: list[str] = field(default_factory=list)
    blocked_fit_calls: int = 0
    attempted: list[str] = field(default_factory=list)

    def block(self, name: str):
        def rejected(*_args: object, **_kwargs: object) -> NoReturn:
            self.blocked_fit_calls += 1
            self.attempted.append(name)
            raise Test3G3PBoundaryError(f"G3-P blocked unauthorized surface: {name}")

        return rejected

    def witness(self) -> FitGuard:
        return FitGuard(tuple(self.installed), self.blocked_fit_calls, tuple(self.attempted))


_BLOCKED_SYMBOLS = (
    (np.linalg, "lstsq", "numpy.linalg.lstsq"),
    (np.linalg, "solve", "numpy.linalg.solve"),
    (np.linalg, "pinv", "numpy.linalg.pinv"),
    (np.linalg, "inv", "numpy.linalg.inv"),
    (np.linalg, "qr", "numpy.linalg.qr"),
    (_test3_stats, "qlike", "test3.qlike"),
    (_test3_stats, "relative_qlike_reduction", "test3.relative_qlike_reduction"),
    (_test3_stats, "duan_smearing_factor", "test3.duan_smearing_factor"),
    (_test3_stats, "back_transform_log_variance", "test3.back_transform"),
    (_test3_stats, "moving_block_indices", "test3.moving_block_indices"),
    (_test3_stats, "paired_session_block_bootstrap", "test3.bootstrap"),
    (_test3_stats, "decide_continuation", "test3.decide_continuation"),
)


@contextmanager
def pre_fit_only_guard() -> Iterator[_MutableFitGuard]:
    guard = _MutableFitGuard()
    originals: list[tuple[object, str, object]] = []
    try:
        for owner, attribute, label in _BLOCKED_SYMBOLS:
            if not hasattr(owner, attribute):
                _fail(f"required zero-fit guard symbol is missing: {label}")
            originals.append((owner, attribute, getattr(owner, attribute)))
            setattr(owner, attribute, guard.block(label))
            guard.installed.append(label)
        yield guard
    finally:
        for owner, attribute, original in reversed(originals):
            setattr(owner, attribute, original)


def _harmonic_for(
    control: ControlRow,
    calendar: tuple[float, float, bool],
):
    minutes_since, minutes_to_safe, _early = calendar
    market_open = control.timestamp - timedelta(minutes=minutes_since)
    market_close = control.timestamp + timedelta(minutes=minutes_to_safe + 60.0)
    return intraday_harmonic(control.timestamp, market_open, market_close)


def _pre_target_support_contract(
    controls: tuple[ControlRow, ...],
    predictor: PredictorData,
) -> tuple[Mapping[str, Harmonic], Mapping[str, object]]:
    holdout_counts = {
        "WF_2022": sum(row.role_2022 == "VALIDATION" for row in controls),
        "WF_2023": sum(row.role_2023 == "VALIDATION" for row in controls),
    }
    if holdout_counts != dict(FROZEN_HOLDOUT_COUNTS):
        _invalid("FROZEN_PRE_ELIGIBILITY_HOLDOUT_COUNTS_MISMATCH")
    harmonics: dict[str, Harmonic] = {}
    slot_counts: Counter[int] = Counter()
    early_close_rows = 0
    for control in controls:
        calendar = predictor.calendar[control.identity]
        harmonic = _harmonic_for(control, calendar)
        expected_slots = 10 if calendar[2] else 22
        if harmonic.n_slots != expected_slots:
            _invalid("EARLY_CLOSE_HARMONIC_SLOT_CONTRACT_MISMATCH")
        harmonics[control.identity] = harmonic
        slot_counts[harmonic.n_slots] += 1
        early_close_rows += int(calendar[2])
    return harmonics, {
        "status": "PASS_BEFORE_TARGET_SPACE_CONSUMPTION",
        "frozen_pre_eligibility_holdout_counts": holdout_counts,
        "harmonic_n_slots_all_outer_train": {
            str(key): int(value) for key, value in sorted(slot_counts.items())
        },
        "early_close_rows": early_close_rows,
        "external_calendar_library_used": False,
    }


def _design_rank_record(matrix: np.ndarray, *, column_count: int) -> dict[str, object]:
    if matrix.ndim != 2 or matrix.shape[1] != column_count or matrix.shape[0] == 0:
        _invalid("TRAIN_DESIGN_SHAPE_INVALID")
    if not np.all(np.isfinite(matrix)):
        _invalid("TRAIN_DESIGN_NONFINITE")
    singular = np.linalg.svd(matrix, compute_uv=False, full_matrices=False)
    rank = int(np.linalg.matrix_rank(matrix))
    smallest = float(singular[-1])
    largest = float(singular[0])
    condition = None if smallest == 0.0 else largest / smallest
    return {
        "row_count": int(matrix.shape[0]),
        "column_count": column_count,
        "rank": rank,
        "full_rank": rank == column_count,
        "singular_values": [float(value) for value in singular],
        "condition_number": condition,
        "finite": bool(np.isfinite(matrix).all()),
    }


def _dependence_record(summary) -> dict[str, object]:
    return {
        "row_count": summary.row_count,
        "lags": [
            {
                "lag": item.lag,
                "pairs": item.pairs,
                "rho_observed": item.rho_observed,
                "rho_null": item.rho_null,
                "excess": item.excess,
            }
            for item in summary.lags
        ],
        "design_effect": summary.design_effect,
        "effective_sample_size": summary.effective_sample_size,
        "status": summary.status,
    }


def _support_evidence(
    controls: tuple[ControlRow, ...],
    predictor: PredictorData,
    targets: TargetBuildResult,
    harmonic_by_identity: Mapping[str, Harmonic],
) -> tuple[dict[str, object], str, str]:
    eligibility = common_eligibility(targets.rows, predictor.status_rows)
    eligible = set(eligibility.eligible_identities)
    target_by_id = {row.decision_identity: row for row in targets.rows}
    fold_records: dict[str, object] = {}
    pooled_dependence: list[DependenceRow] = []
    pooled_ids: set[str] = set()
    structural_failures: list[str] = []
    slot_counts: Counter[int] = Counter()
    for row in controls:
        if row.identity not in eligible:
            continue
        harmonic = harmonic_by_identity[row.identity]
        if harmonic.n_slots not in {10, 22}:
            _invalid("HARMONIC_N_SLOTS_OUTSIDE_FROZEN_NORMAL_OR_EARLY_CLOSE_SET")
        slot_counts[harmonic.n_slots] += 1

    for fold_id in FOLD_ORDER:
        role_attribute = "role_2022" if fold_id == "WF_2022" else "role_2023"
        pre_holdout = [row for row in controls if getattr(row, role_attribute) == "VALIDATION"]
        if len(pre_holdout) != FROZEN_HOLDOUT_COUNTS[fold_id]:
            _invalid(f"{fold_id}_FROZEN_HOLDOUT_COUNT_MISMATCH")
        train_rows = [
            row
            for row in controls
            if row.identity in eligible and getattr(row, role_attribute) == "TRAIN"
        ]
        holdout_rows = [
            row
            for row in controls
            if row.identity in eligible and getattr(row, role_attribute) == "VALIDATION"
        ]
        if not train_rows or not holdout_rows:
            structural_failures.append(f"{fold_id}:EMPTY_ELIGIBLE_PARTITION")
            continue
        train_label_end_max = max(
            target_by_id[row.identity].label_end_time for row in train_rows
        )
        train_decision_max = max(row.timestamp for row in train_rows)
        holdout_start = min(row.timestamp for row in holdout_rows)
        label_end_gap = (holdout_start - train_label_end_max).total_seconds() / 60.0
        decision_gap = (holdout_start - train_decision_max).total_seconds() / 60.0
        if (
            train_label_end_max >= holdout_start
            or label_end_gap < 60.0
            or decision_gap < 60.0
        ):
            _invalid(f"{fold_id}_PURGE_BOUNDARY_FAILURE")
        session_order = tuple(dict.fromkeys(row.session_id for row in holdout_rows))
        if len(session_order) < 20:
            structural_failures.append(f"{fold_id}:HOLDOUT_SESSIONS_LT_20")
        model_records: dict[str, object] = {}
        for model_id in MODEL_ORDER:
            rows_values: list[tuple[float, ...]] = []
            for row in train_rows:
                values = predictor.values[row.identity]
                if any(value is None for value in values):
                    _invalid("ELIGIBLE_ROW_HAS_MISSING_PREDICTOR")
                harmonic = harmonic_by_identity[row.identity]
                rows_values.append(
                    design_values(
                        model_id,
                        realized_vol_60m=float(values[0]),
                        realized_vol_120m=float(values[1]),
                        realized_vol_240m=float(values[2]),
                        harmonic=harmonic,
                    )
                )
            matrix = np.asarray(rows_values, dtype=np.float64)
            rank_record = _design_rank_record(
                matrix,
                column_count=len(MODEL_COLUMNS[model_id]),
            )
            if rank_record["row_count"] <= rank_record["column_count"]:
                structural_failures.append(f"{fold_id}:{model_id}:ROWS_NOT_GT_COLUMNS")
            if not rank_record["full_rank"]:
                structural_failures.append(f"{fold_id}:{model_id}:RANK_DEFICIENT")
            model_records[model_id] = rank_record
        dependence_rows = [
            DependenceRow(
                fold_id,
                row.session_id,
                row.timestamp,
                targets.variance_by_identity[row.identity],
            )
            for row in holdout_rows
        ]
        if pooled_ids.intersection(row.identity for row in holdout_rows):
            _invalid("POOLED_OOF_FOLD_IDENTITY_OVERLAP")
        pooled_ids.update(row.identity for row in holdout_rows)
        pooled_dependence.extend(dependence_rows)
        fold_records[fold_id] = {
            "pre_eligibility_holdout_rows": len(pre_holdout),
            "eligible_train_rows": len(train_rows),
            "eligible_holdout_rows": len(holdout_rows),
            "holdout_session_count": len(session_order),
            "train_label_end_max_utc": train_label_end_max.isoformat(),
            "train_decision_max_utc": train_decision_max.isoformat(),
            "holdout_start_utc": holdout_start.isoformat(),
            "boundary_gap_minutes_label_end_to_decision": label_end_gap,
            "boundary_gap_minutes_decision_to_decision": decision_gap,
            "embargo_minutes": 0,
            "models": model_records,
            "dependence": _dependence_record(dependence_summary(dependence_rows)),
        }
    pooled = _dependence_record(dependence_summary(pooled_dependence))
    support_passed = not structural_failures
    record = {
        "common_eligibility": {
            "eligible_rows": len(eligibility.eligible_identities),
            "excluded_rows": len(eligibility.excluded_identities),
            "ordered_eligible_identity_sha256": eligibility.ordered_identity_sha256,
            "only_exact_usable_statuses": True,
        },
        "folds": fold_records,
        "pooled_disjoint_oof_dependence": pooled,
        "harmonic_n_slots_observations": {
            str(key): int(value) for key, value in sorted(slot_counts.items())
        },
        "harmonic_external_calendar_library_used": False,
        "structural_failures": structural_failures,
        "support_gate_status": (
            "G3P_SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED"
            if support_passed
            else "G3P_SUPPORT_GATE_FAIL_UNDERPOWERED"
        ),
    }
    disposition = (
        "DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION"
        if support_passed
        else "UNDERPOWERED_STOP"
    )
    g3f_status = "NOT_AUTHORIZED_OWNER_DECISION_REQUIRED" if support_passed else "TERMINAL"
    return record, disposition, g3f_status


def _fit_guard_record(guard: _MutableFitGuard) -> dict[str, object]:
    witness = guard.witness()
    return {
        "guard_id": "TEST3_G3P_ZERO_FIT_GUARD_V1",
        "installed_symbols": list(witness.installed),
        "blocked_fit_calls": witness.blocked_fit_calls,
        "attempted_symbols": list(witness.attempted),
        "status": (
            "PASS_NO_BLOCKED_CALLS"
            if witness.blocked_fit_calls == 0
            else "FAIL_BLOCKED_CALL_ATTEMPTED"
        ),
    }


def _assemble_record_with_controls(
    *,
    controls: tuple[ControlRow, ...],
    git_context: GitContext,
    authorization: ObservedAuthorization,
    documents: Mapping[str, object],
    g2p_binding: Mapping[str, object],
    source_bindings: Mapping[str, object],
    runtime_binding: Mapping[str, object],
    sealed: StreamingSealedRequestSet,
    request_witness: tuple[Path, str],
    target_witness: tuple[Path, str],
    decoded_evidence,
    predictor: PredictorData,
    targets: TargetBuildResult,
    guard: _MutableFitGuard,
    harmonic_by_identity: Mapping[str, Harmonic],
) -> dict[str, object]:
    if len(targets.rows) != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid("TARGET_LEDGER_ROW_COUNT_MISMATCH")
    if targets.provider_rows_examined + targets.missing_request_keys != sealed.key_count:
        _invalid("PROVIDER_READ_PLUS_MISSING_DOES_NOT_RECONCILE_TO_SEALED_KEYS")
    if targets.usable_cell12_rows + targets.unusable_cell12_rows != EXPECTED_OUTER_TRAIN_ROWS:
        _invalid("CELL12_RECONCILIATION_VERDICT_COUNT_MISMATCH")
    if guard.blocked_fit_calls != 0:
        _fail("G3-P record assembly blocked after an unauthorized computation attempt")
    zero_variance = targets.status_counts[FailureReason.TARGET_ZERO_VARIANCE.value]
    if zero_variance:
        support: dict[str, object] = {
            "status": "NOT_COMPUTED_TARGET_ZERO_VARIANCE_TERMINAL",
            "common_eligibility": "NOT_COMPUTED",
            "folds": "NOT_COMPUTED",
            "dependence": "NOT_COMPUTED",
        }
        disposition = "INVALID_EVIDENCE"
        stage_status = "G3P_TARGET_LEDGER_TERMINAL_INVALID_EVIDENCE"
        g3f_status = "TERMINAL"
    else:
        support, disposition, g3f_status = _support_evidence(
            controls,
            predictor,
            targets,
            harmonic_by_identity,
        )
        stage_status = (
            "G3P_SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED"
            if disposition == "DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION"
            else "G3P_SUPPORT_GATE_FAIL_UNDERPOWERED"
        )
    counters = {
        "cell8_train_control_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "cell14_train_predictor_calendar_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "cell10_train_target_reference_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "cell12_train_path_rows_read": EXPECTED_OUTER_TRAIN_ROWS,
        "outer_train_target_path_keys_read": targets.provider_rows_examined,
        "outer_train_target_rows_read": len(targets.rows),
        "targets_constructed": len(targets.rows),
        "outer_validation_target_rows_read": 0,
        "final_test_target_rows_read": 0,
        "real_fold_fit_calls": 0,
        "real_models_fitted": 0,
        "real_coefficients_computed": 0,
        "real_forecasts_computed": 0,
        "qlike_evaluations": 0,
        "duan_factors_computed": 0,
        "real_bootstrap_replicates": 0,
        "economic_diagnostic_calls": 0,
        "blocked_fit_calls": 0,
        "outer_validation_predictor_rows_read": 0,
        "final_test_predictor_rows_read": 0,
    }
    core: dict[str, object] = {
        "gate_id": G3P_GATE_ID,
        "record_version": G3P_RECORD_VERSION,
        "protocol_id": PROTOCOL_ID,
        "project_budget_id": PROJECT_BUDGET_ID,
        "target_space_id": TARGET_SPACE_ID,
        "target_space_state": "CONSUMED",
        "ratified_commit": RATIFIED_COMMIT,
        "ratification_record_commit": RATIFICATION_RECORD_COMMIT,
        "base_commit": G3P_BASE_COMMIT,
        "execution_commit": git_context.commit,
        "execution_tree": git_context.tree,
        "branch": git_context.branch,
        "upstream_commit": git_context.upstream,
        "local_upstream_equal": True,
        "access_level": G3P_ACCESS_LEVEL,
        "status": "COMPLETE",
        "stage_status": stage_status,
        "disposition": disposition,
        "authorization_binding": {
            "authorization_id": G3P_AUTHORIZATION_ID,
            "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
            "authorization_reservation_path": "${REPOSITORY}/"
            + AUTHORIZATION_RESERVATION_PATH,
            "authorization_reservation_sha256": authorization.reservation_sha256,
            "document_bindings": dict(documents),
        },
        "g2p_predecessor_binding": dict(g2p_binding),
        "source_bindings": dict(source_bindings),
        "runtime_binding": dict(runtime_binding),
        "frozen_definitions": {
            "target_id": "RV_FWD_60",
            "target_horizon_minutes": TARGET_HORIZON_MINUTES,
            "predictor_columns_ordered": list(PREDICTOR_COLUMNS),
            "calendar_columns_ordered": list(CALENDAR_COLUMNS),
            "model_order": list(MODEL_ORDER),
            "ordered_model_definitions": {
                model_id: list(MODEL_COLUMNS[model_id]) for model_id in MODEL_ORDER
            },
        },
        "decoded_identity": {
            "content_sha256": decoded_evidence.content_sha256,
            "row_count": decoded_evidence.row_count,
            "timestamp_min_utc": decoded_evidence.timestamp_min_utc,
            "timestamp_max_utc": decoded_evidence.timestamp_max_utc,
            "content_status": DECODED_CONTENT_STATUS_RECOMPUTED,
            "hash_projection_id": CELL2_HASH_PROJECTION_ID,
            "hash_columns": list(CELL2_HASH_COLUMNS),
            "hash_algorithm": CELL2_HASH_ALGORITHM,
            "hash_includes_index": CELL2_HASH_INCLUDES_INDEX,
            "decode_scope": DECODE_SCOPE,
            "databento_modules_loaded": list(decoded_evidence.databento_modules_loaded),
        },
        "counter_semantics": {
            "rows_read": "APPLICATION_EXPOSED_ROWS",
            "decode_scope": DECODE_SCOPE,
            "decoded_frame_partition_filtering_claimed": False,
            "protected_target_rows": "SEALED_REQUEST_KEY_LOOKUPS_ONLY",
        },
        "request_set_binding": {
            "request_set_sha256": sealed.request_set_sha256,
            "parent_count": len(sealed.decisions),
            "request_key_count": sealed.key_count,
            "outer_validation_request_count": sealed.validation_path_bar_lookup_count,
            "final_test_request_count": sealed.final_test_path_bar_lookup_count,
            "path_bar_offsets": TARGET_BAR_COUNT,
            "hashed_and_persisted_before_provider_lookup": True,
            "witness_path": "${REPOSITORY}/" + REQUEST_SET_WITNESS_PATH,
            "witness_sha256": request_witness[1],
        },
        "target_space_consumption": {
            "status": "CONSUMED_BEFORE_FIRST_NUMERIC_TARGET_OR_PATH_READ",
            "witness_path": "${REPOSITORY}/" + TARGET_SPACE_WITNESS_PATH,
            "witness_sha256": target_witness[1],
            "retry_authorized": False,
            "successor_available": False,
            "repair_lineage_exhausted": True,
        },
        "predictor_ledger_reproduction": {
            "row_count": len(predictor.status_rows),
            "status_counts": dict(predictor.status_counts),
            "ordered_identity_sha256": predictor.ordered_identity_sha256,
            "ordered_identity_status_sha256": predictor.ordered_identity_status_sha256,
            "cell14_ordered_feature_sha256_declared": CELL14_ORDERED_FEATURE_SHA256,
            "matches_committed_g2p": True,
            "raw_values_persisted": False,
        },
        "target_status_ledger": {
            "row_count": len(targets.rows),
            "status_counts": dict(targets.status_counts),
            "ordered_identity_time_status_sha256": targets.ordered_status_sha256,
            "raw_values_persisted": False,
            "per_row_identities_persisted": False,
        },
        "cell12_reconciliation": {
            "status": "EXACT_FULL_TRAIN_COVERAGE_RECONCILIATION_PASS",
            "expectation_rows": EXPECTED_OUTER_TRAIN_ROWS,
            "usable_rows": targets.usable_cell12_rows,
            "unusable_rows": targets.unusable_cell12_rows,
            "absent_rows": 0,
        },
        "provider_counters": {
            "rows_examined": targets.provider_rows_examined,
            "missing_request_keys": targets.missing_request_keys,
            "native_instrument_mismatch_keys": targets.instrument_mismatch_keys,
        },
        "support_evidence": support,
        "fit_guard": _fit_guard_record(guard),
        "fit_authorization": {
            "status": "BLOCKED_G3P_FIT_NOT_AUTHORIZED",
            "fit_permits_issued": 0,
            "fit_completions": 0,
            "coefficient_identities": [],
        },
        "safety_counters": counters,
        "not_computed": dict(_NOT_COMPUTED),
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "live_execution_status": "DISABLED",
        "g3f_status": g3f_status,
    }
    seed = sha256_bytes(canonical_json_bytes(canonicalize_audit(core)))
    record = {
        **core,
        "run_id": f"MES_T3_G3P_{seed[:16].upper()}",
        "audit_written_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _assert_closed_record(record)
    record["record_sha256"] = _record_sha256(record)
    return record


def write_g3p_record(record: Mapping[str, object], *, output_root: str | Path) -> Path:
    if record.get("gate_id") != G3P_GATE_ID:
        _fail("G3-P record gate identity mismatch")
    _assert_closed_record(record)
    if record.get("record_sha256") != _record_sha256(record):
        _fail("G3-P record semantic SHA-256 mismatch before publication")
    run_id = record.get("run_id")
    if (
        not isinstance(run_id, str)
        or len(run_id) != len("MES_T3_G3P_") + 16
        or not run_id.startswith("MES_T3_G3P_")
        or any(character not in "0123456789ABCDEF" for character in run_id[-16:])
    ):
        _fail("G3-P run_id is malformed")
    root = _absolute(output_root, field_name="G3-P output root")
    run_dir = root / run_id
    output = run_dir / G3P_RECORD_FILENAME
    with _open_directory_chain(root, create=True) as root_descriptor:
        os.mkdir(run_id, mode=0o700, dir_fd=root_descriptor)
        os.fsync(root_descriptor)
    try:
        file_sha256 = _atomic_create_json(output, record)
        parsed = _strict_json(output, expected_sha256=file_sha256)
        if parsed.get("record_sha256") != _record_sha256(parsed):
            _fail("published G3-P record failed semantic reread")
        _assert_closed_record(parsed)
    except Exception:
        try:
            with _open_directory_chain(run_dir) as run_descriptor:
                try:
                    os.unlink(G3P_RECORD_FILENAME, dir_fd=run_descriptor)
                except FileNotFoundError:
                    pass
                os.fsync(run_descriptor)
            with _open_directory_chain(root) as root_descriptor:
                try:
                    os.rmdir(run_id, dir_fd=root_descriptor)
                except OSError:
                    pass
                os.fsync(root_descriptor)
        except Test3G3PBoundaryError:
            pass
        raise
    return output


def write_failure_summary_if_reserved(
    *, project_root: str | Path, error: BaseException
) -> Path | None:
    root = _absolute(project_root, field_name="G3-P project root")
    reservation = root / AUTHORIZATION_RESERVATION_PATH
    if not _regular_file_exists_no_follow(reservation):
        return None
    failure = root / FAILURE_RECORD_PATH
    witness_integrity = "VERIFIED"
    request_sealed = False
    target_consumed = False
    try:
        reservation_sha256, _size = _hash_file(reservation)
        reservation_record = _strict_json(
            reservation,
            expected_sha256=reservation_sha256,
        )
        reservation_expected = {
            "authorization_id": G3P_AUTHORIZATION_ID,
            "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
            "authorization_token_sha256": hashlib.sha256(
                G3P_AUTHORIZATION_TOKEN.encode("utf-8")
            ).hexdigest(),
            "base_commit": G3P_BASE_COMMIT,
            "branch": G3P_BRANCH,
            "g2p_evidence_commit": G2P_EVIDENCE_COMMIT,
            "status": "CONSUMED_BEFORE_ANY_SOURCE_ARTIFACT_ACCESS",
            "retry_authorized": False,
            "merge_authorized": False,
        }
        if any(reservation_record.get(key) != value for key, value in reservation_expected.items()):
            _fail("G3-P failure boundary found an invalid authorization reservation")
        execution_commit = _git_sha(
            str(reservation_record.get("execution_commit")),
            field_name="reserved execution commit",
        )
        execution_tree = _git_sha(
            str(reservation_record.get("execution_tree")),
            field_name="reserved execution tree",
        )
        request_path = root / REQUEST_SET_WITNESS_PATH
        request_sha256: str | None = None
        request_set_sha256: str | None = None
        if _regular_file_exists_no_follow(request_path):
            request_sha256, _size = _hash_file(request_path)
            request_record = _strict_json(request_path, expected_sha256=request_sha256)
            request_expected = {
                "gate_id": G3P_GATE_ID,
                "authorization_id": G3P_AUTHORIZATION_ID,
                "authorization_reservation_sha256": reservation_sha256,
                "execution_commit": execution_commit,
                "execution_tree": execution_tree,
                "cell8_split_assignment_sha256": CELL8_SPLIT_ASSIGNMENT_SHA256,
                "parent_count": EXPECTED_OUTER_TRAIN_ROWS,
                "request_key_count": EXPECTED_OUTER_TRAIN_ROWS * TARGET_BAR_COUNT,
                "outer_validation_request_count": 0,
                "final_test_request_count": 0,
                "per_key_identities_persisted": False,
                "status": "SEALED_AND_PERSISTED_BEFORE_PROVIDER_ACCESS",
            }
            if any(request_record.get(key) != value for key, value in request_expected.items()):
                _fail("G3-P failure boundary found an invalid request-set witness")
            request_set_sha256 = str(request_record.get("request_set_sha256"))
            if len(request_set_sha256) != 64 or any(
                character not in "0123456789abcdef" for character in request_set_sha256
            ):
                _fail("G3-P failure boundary found a malformed request-set SHA-256")
            request_sealed = True
        target_path = root / TARGET_SPACE_WITNESS_PATH
        if _regular_file_exists_no_follow(target_path):
            if not request_sealed or request_sha256 is None or request_set_sha256 is None:
                _fail("G3-P target witness exists without a verified request witness")
            target_sha256, _size = _hash_file(target_path)
            target_record = _strict_json(target_path, expected_sha256=target_sha256)
            target_expected = {
                "target_space_id": TARGET_SPACE_ID,
                "target_space_state": "CONSUMED",
                "authorization_id": G3P_AUTHORIZATION_ID,
                "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
                "authorization_reservation_sha256": reservation_sha256,
                "execution_commit": execution_commit,
                "execution_tree": execution_tree,
                "request_set_sha256": request_set_sha256,
                "request_set_witness_sha256": request_sha256,
                "status": "CONSUMED_IMMEDIATELY_BEFORE_FIRST_NUMERIC_TARGET_OR_PATH_READ",
                "retry_authorized": False,
                "replacement_target_authorized": False,
            }
            if any(target_record.get(key) != value for key, value in target_expected.items()):
                _fail("G3-P failure boundary found an invalid target-space witness")
            target_consumed = True
    except Exception:  # noqa: BLE001 - failure evidence must degrade conservatively
        witness_integrity = "NOT_ATTESTED_INVALID_OR_INCOMPLETE_WITNESS_CHAIN"
        request_sealed = False
        target_consumed = False
    typed_invalid = isinstance(error, Test3G3PInvalidEvidenceError)
    if witness_integrity != "VERIFIED":
        failure_status = (
            "PROTOCOL_INVALID_EVIDENCE_TARGET_ACCESS_NOT_ATTESTED_NO_RETRY"
            if typed_invalid
            else "EXECUTION_FAILURE_TARGET_ACCESS_NOT_ATTESTED_NO_RETRY"
        )
    elif typed_invalid and target_consumed:
        failure_status = "PROTOCOL_INVALID_EVIDENCE_AFTER_TARGET_CONSUMPTION_NO_RETRY"
    elif typed_invalid:
        failure_status = "PROTOCOL_INVALID_EVIDENCE_BEFORE_TARGET_ACCESS_NO_RETRY"
    elif target_consumed:
        failure_status = "EXECUTION_FAILURE_AFTER_TARGET_CONSUMPTION_NO_RETRY"
    else:
        failure_status = "EXECUTION_FAILURE_BEFORE_TARGET_ACCESS_NO_RETRY"
    payload: dict[str, object] = {
        "authorization_id": G3P_AUTHORIZATION_ID,
        "authorization_document_sha256": G3P_AUTHORIZATION_DOCUMENT_SHA256,
        "status": failure_status,
        "terminal_disposition": "INVALID_EVIDENCE" if typed_invalid else "EXECUTION_FAILURE",
        "error_class": type(error).__name__,
        "invalid_evidence_category": (
            error.category
            if typed_invalid
            else "UNCLASSIFIED_EXECUTION_FAILURE"
        ),
        "raw_error_message_committed": False,
        "witness_chain_integrity": witness_integrity,
        "request_set_witness_present": request_sealed,
        "target_space_state": (
            "CONSUMED"
            if target_consumed
            else "LOCKED / RESERVED"
            if witness_integrity == "VERIFIED"
            else "CONSUMED_OR_NOT_ATTESTED_FAIL_CLOSED"
        ),
        "target_space_consumption_witness_present": target_consumed,
        "retry_authorized": False,
        "replacement_target_authorized": False,
        "repair_lineage_exhausted": True,
        "real_fold_fit_calls": 0,
        "real_models_fitted": 0,
        "real_bootstrap_replicates": 0,
        "economic_diagnostic_calls": 0,
        "validation_status": "ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED",
        "final_test_status": "ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED",
        "test3_status": "TERMINAL_NO_RETRY",
        "g3p_status": "TERMINAL_NO_RETRY",
        "g3f_status": "TERMINAL_NOT_AUTHORIZED",
        "failed_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    try:
        _atomic_create_json(failure, payload)
    except FileExistsError as exc:
        raise Test3G3PBoundaryError(
            "G3-P failure record already exists; overwrite and retry are forbidden"
        ) from exc
    return failure


def _terminal_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    counters = record["safety_counters"]
    targets = record["target_status_ledger"]
    provider = record["provider_counters"]
    assert isinstance(counters, Mapping)
    assert isinstance(targets, Mapping)
    assert isinstance(provider, Mapping)
    return (
        "TEST3_G3P_TRAIN_TARGET_SUPPORT_PREFIT_COMPLETE",
        f"G3P_STAGE_STATUS={record['stage_status']}",
        f"DISPOSITION={record['disposition']}",
        f"TARGET_SPACE_STATE={record['target_space_state']}",
        f"OUTER_TRAIN_TARGET_PATH_KEYS_READ={counters['outer_train_target_path_keys_read']}",
        f"OUTER_TRAIN_TARGET_ROWS_READ={counters['outer_train_target_rows_read']}",
        f"TARGETS_CONSTRUCTED={counters['targets_constructed']}",
        f"TARGET_USABLE={targets['status_counts'][RowStatus.TARGET_USABLE.value]}",
        f"TARGET_UNUSABLE={targets['status_counts'][RowStatus.TARGET_UNUSABLE.value]}",
        (
            "TARGET_ZERO_VARIANCE="
            f"{targets['status_counts'][FailureReason.TARGET_ZERO_VARIANCE.value]}"
        ),
        f"MISSING_REQUEST_KEYS={provider['missing_request_keys']}",
        f"NATIVE_INSTRUMENT_MISMATCH_KEYS={provider['native_instrument_mismatch_keys']}",
        f"REAL_FOLD_FIT_CALLS={counters['real_fold_fit_calls']}",
        f"REAL_MODELS_FITTED={counters['real_models_fitted']}",
        f"REAL_BOOTSTRAP_REPLICATES={counters['real_bootstrap_replicates']}",
        f"OUTER_VALIDATION_TARGET_ROWS_READ={counters['outer_validation_target_rows_read']}",
        f"FINAL_TEST_TARGET_ROWS_READ={counters['final_test_target_rows_read']}",
        f"VALIDATION_STATUS={record['validation_status']}",
        f"FINAL_TEST_STATUS={record['final_test_status']}",
        f"G3F_STATUS={record['g3f_status']}",
    )


G3P_IN_MEMORY_HANDOFF_ID = "TEST3_G3P_TO_G3F_STRICT_IN_PROCESS_ROW_HANDOFF_V1"
G3P_IN_MEMORY_HANDOFF_PERSISTENCE = (
    "FORBIDDEN_NO_DISK_NO_CACHE_NO_LOG_NO_SERIALIZATION_NO_SPILL_NO_IPC"
)


def _bind_reviewed_g3f_delivery():
    """Claim the single reviewed G3-F delivery handle once, at import, into a closure.

    There is no arbitrary or metadata-based receiver boundary left: G3-P never accepts a
    callback, never authorizes by ``__module__``/``__qualname__`` strings, and keeps no
    module-level receiver global that a wrapper, callable object or metadata spoof could be
    patched into. The exact handle and the exact G3-F module-instance marker are captured here
    at import; the delivery below calls only that captured function.

    The claim is one-time. If the handle was already claimed, if G3-F was reloaded or replaced,
    or if the two stages disagree about the handoff identity, this fails closed at import rather
    than degrading to a weaker boundary.

    Honest limit: a Python closure is not secret, and arbitrary in-process code can still reach
    these cells by reflection. What this removes is every ordinary substitution surface.
    """

    if G3P_IN_MEMORY_HANDOFF_ID != _test3_g3f.EXPECTED_HANDOFF_ID:
        _fail("in-memory G3-P handoff identity does not match the reviewed G3-F stage")
    handle, marker = _test3_g3f._claim_g3p_delivery_handle()
    module = _test3_g3f

    def _deliver_in_memory_handoff(
        *,
        controls: tuple[ControlRow, ...],
        predictor: PredictorData,
        targets: TargetBuildResult,
        harmonic_by_identity: Mapping[str, Harmonic],
    ) -> None:
        """Hand the live rows to the captured reviewed G3-F handle and retain nothing.

        The captured G3-F module-instance marker is rechecked against the live module before any
        row or field is touched, so a reloaded or replaced G3-F instance fails closed first. The
        captured handle is then entered in two stages: its first stage is called with only the
        exact marker and the exact handoff identity, before any predictor, target or harmonic
        field expression is evaluated, so a refused or already spent delivery stops there. Only
        the private second-stage closure it returns is given the row fields, and G3-P still
        accepts no arbitrary receiver, supplier or callback. The canonical handoff object is
        minted and consumed inside that closure, so nothing here can hold, wrap or replay it. No
        file, temporary spill, serialization, log line or inter-process channel is created, and
        whatever the second stage returns is discarded rather than stored, recorded or returned.
        """

        if getattr(module, "_MODULE_INSTANCE_MARKER", None) is not marker:
            raise Test3G3PBoundaryError(
                "the reviewed G3-F module instance was reloaded or replaced"
            )
        supply = handle(marker, handoff_id=G3P_IN_MEMORY_HANDOFF_ID)
        supply(
            controls=controls,
            predictor_status_rows=predictor.status_rows,
            predictor_values=predictor.values,
            target_status_rows=targets.rows,
            target_variance_by_identity=targets.variance_by_identity,
            harmonic_by_identity=harmonic_by_identity,
        )

    return _deliver_in_memory_handoff


_deliver_in_memory_handoff = _bind_reviewed_g3f_delivery()

del _bind_reviewed_g3f_delivery


def run_g3p(
    *,
    root: Path,
    paths: ArtifactPaths,
    git_context: GitContext,
    authorization: ObservedAuthorization,
    documents: Mapping[str, object],
    g2p_binding: Mapping[str, object],
    runtime_binding: Mapping[str, object],
    deliver_to_g3f: bool = False,
) -> dict[str, object]:
    source_bindings = _preflight_sources(paths)
    cell8_table = _read_train_projection(
        paths.cell8,
        expected_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        columns=CONTROL_COLUMNS,
        field_name="cell8",
    )
    cell14_table = _read_train_projection(
        paths.cell14,
        expected_sha256=CELL14_FEATURE_FILE_SHA256,
        columns=CELL14_COLUMNS,
        field_name="cell14",
    )
    cell8_controls = _control_rows(cell8_table, field_name="cell8")
    cell14_controls = _control_rows(cell14_table, field_name="cell14")
    if cell8_controls != cell14_controls:
        _invalid("CELL8_CELL14_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH")
    if _control_binding(cell8_controls) != g2p_binding.get(
        "outer_train_control_binding_sha256"
    ):
        _invalid("G2P_OUTER_TRAIN_CONTROL_BINDING_SHA256_MISMATCH")
    expected_ledger = g2p_binding.get("predictor_status_ledger")
    if not isinstance(expected_ledger, Mapping):
        _fail("G2-P binding lacks predictor ledger")
    predictor = _predictor_data(
        cell14_table,
        cell14_controls,
        expected_ledger=expected_ledger,
    )
    harmonic_by_identity, pre_target_support = _pre_target_support_contract(
        cell8_controls,
        predictor,
    )
    source_bindings = {
        **source_bindings,
        "pre_target_support_contract": pre_target_support,
    }
    sealed = build_streaming_request_set(
        tuple(
            ParentDecision(row.identity, row.timestamp, "TRAIN") for row in cell8_controls
        ),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    request_witness = _persist_request_set_witness(
        root,
        sealed=sealed,
        git_context=git_context,
        authorization=authorization,
    )
    with pre_fit_only_guard() as guard:
        _assert_forbidden_modules_absent(phase="immediately before target consumption")
        target_witness = _consume_target_space(
            root,
            sealed=sealed,
            git_context=git_context,
            authorization_reservation_sha256=authorization.reservation_sha256,
            request_witness_sha256=request_witness[1],
        )
        cell10_table = _read_train_projection(
            paths.cell10,
            expected_sha256=CELL10_LABEL_SHA256,
            columns=CELL10_COLUMNS,
            field_name="cell10",
        )
        cell12_table = _read_train_projection(
            paths.cell12,
            expected_sha256=CELL12_PATH_SHA256,
            columns=CELL12_COLUMNS,
            field_name="cell12",
        )
        cell10_controls = _control_rows(cell10_table, field_name="cell10")
        cell12_controls = _control_rows(cell12_table, field_name="cell12")
        if cell8_controls != cell10_controls or cell8_controls != cell12_controls:
            _invalid("CELL8_CELL10_CELL12_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH")
        references = _references(cell10_table, cell10_controls)
        expectations = _cell12_expectations(cell12_table, cell12_controls)
        decoded_frame, decoded_evidence = decode_canonical_dbn(paths.raw_dbn)
        _assert_forbidden_modules_absent(phase="after canonical decode")
        if decoded_evidence.content_sha256 != DECODED_MES_1M_SHA256:
            _invalid("DECODED_CONTENT_SHA256_MISMATCH")
        provider = SealedFrameProvider(
            decoded_frame,
            sealed=sealed,
            instruments={row.identity: row.instrument for row in cell8_controls},
        )
        targets = _build_targets(
            sealed,
            cell8_controls,
            references,
            expectations,
            provider,
        )
        _assert_forbidden_modules_absent(phase="after target ledger")
        record = _assemble_record_with_controls(
            controls=cell8_controls,
            git_context=git_context,
            authorization=authorization,
            documents=documents,
            g2p_binding=g2p_binding,
            source_bindings=source_bindings,
            runtime_binding=runtime_binding,
            sealed=sealed,
            request_witness=request_witness,
            target_witness=target_witness,
            decoded_evidence=decoded_evidence,
            predictor=predictor,
            targets=targets,
            guard=guard,
            harmonic_by_identity=harmonic_by_identity,
        )
        _assert_forbidden_modules_absent(phase="after record assembly")
    # The delivery deliberately runs after the zero-fit guard has been removed, so the captured
    # reviewed G3-F delivery handle and any later authorized real fit behind it are not blocked
    # by the temporarily patched linear-algebra symbols. Every G3-P record, counter, gate and
    # witness above is already complete and unchanged at this point.
    if deliver_to_g3f:
        _deliver_in_memory_handoff(
            controls=cell8_controls,
            predictor=predictor,
            targets=targets,
            harmonic_by_identity=harmonic_by_identity,
        )
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Owner-authorized Test 3 G3-P TRAIN pre-fit")
    parser.add_argument("--gate", choices=(G3P_GATE_LITERAL,), required=True)
    parser.add_argument("--authorization-token", required=True)
    parser.add_argument("--raw-dbn", type=Path, required=True)
    parser.add_argument("--cell8", type=Path, required=True)
    parser.add_argument("--cell10", type=Path, required=True)
    parser.add_argument("--cell12", type=Path, required=True)
    parser.add_argument("--cell14-features", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path(G3P_OUTPUT_SUBPATH))
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: str | Path | None = None,
) -> int:
    _assert_isolated_runtime()
    args = _parser().parse_args(argv)
    if args.authorization_token != G3P_AUTHORIZATION_TOKEN:
        _fail("G3-P Owner authorization token mismatch")
    _assert_forbidden_modules_absent(phase="entry")
    root = _absolute(project_root or Path.cwd(), field_name="G3-P project root")
    output_root = (
        _absolute(root / args.output_root, field_name="G3-P output root")
        if not args.output_root.is_absolute()
        else _absolute(args.output_root, field_name="G3-P output root")
    )
    if output_root != root / G3P_OUTPUT_SUBPATH:
        _fail("G3-P output root differs from the fixed evidence root")
    paths = ArtifactPaths(
        _absolute(args.raw_dbn, field_name="raw DBN"),
        _absolute(args.cell8, field_name="Cell 8"),
        _absolute(args.cell10, field_name="Cell 10"),
        _absolute(args.cell12, field_name="Cell 12"),
        _absolute(args.cell14_features, field_name="Cell 14"),
    )
    _validate_canonical_paths(root, paths)
    git_context = _git_context(root)
    runtime_binding = _assert_runtime_module_origins(root)
    documents = _verify_documents(root)
    g2p_binding = _verify_g2p_evidence(root)
    authorization = _consume_authorization(
        root,
        git_context=git_context,
        authorization_token=args.authorization_token,
    )
    record = run_g3p(
        root=root,
        paths=paths,
        git_context=git_context,
        authorization=authorization,
        documents=documents,
        g2p_binding=g2p_binding,
        runtime_binding=runtime_binding,
    )
    output = write_g3p_record(record, output_root=output_root)
    print(f"G3P_RECORD={output}")
    print(f"G3P_RECORD_SHA256={record['record_sha256']}")
    print(f"G3P_RECORD_FILE_SHA256={_hash_file(output)[0]}")
    print(f"G3P_AUTHORIZATION_RESERVATION={authorization.reservation_path}")
    print(f"G3P_AUTHORIZATION_RESERVATION_SHA256={authorization.reservation_sha256}")
    for line in _terminal_lines(record):
        print(line)
    return 0


__all__ = [
    "G3P_ALLOWED_CHANGED_FILES",
    "G3P_AUTHORIZATION_DOCUMENT_SHA256",
    "G3P_AUTHORIZATION_ID",
    "G3P_AUTHORIZATION_TOKEN",
    "G3P_BASE_COMMIT",
    "G3P_BRANCH",
    "G3P_GATE_LITERAL",
    "G3P_IN_MEMORY_HANDOFF_ID",
    "Test3G3PBoundaryError",
    "Test3G3PInvalidEvidenceError",
    "main",
    "pre_fit_only_guard",
    "run_g3p",
    "write_failure_summary_if_reserved",
    "write_g3p_record",
]

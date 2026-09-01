"""Prepare or verify the closed Test 3 one-shot activation envelope.

This tool is deliberately data-free.  It reads a closed preparation plan, the reviewed
Test 3 source contracts, the ratified protocol document and the exact six reviewed
implementation files.  It never imports the Test 3 runtime modules, invokes a loader or
runner, reaches a provider, reads scientific data, or creates runtime evidence.

``check`` and ``verify-existing`` are static and non-claiming.  ``create`` is implemented
for a later separately authorized invocation; this preparation slice must not invoke it
against the repository.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import secrets
import stat
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import NoReturn

PLAN_SCHEMA_VERSION = "MES_TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_PLAN_V1"
PLAN_CLASSIFICATION = "PREPARATION_ONLY_NOT_ACTIVATION / NO_AUTHORITY"
PLAN_PATH = "configs/research/test3_one_shot_real_train_activation_plan_v1.json"
PROTOCOL_PATH = "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md"
CONTRACT_PATH = "src/mes_quant/exploration/test3_contract.py"
G3P_PATH = "src/mes_quant/exploration/test3_g3p_pre_fit.py"
G3F_PATH = "src/mes_quant/exploration/test3_g3f_one_shot.py"
ACTIVATION_OUTPUT_PATH = "docs/research/TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V1.json"

OVERRIDE_ID = "TEST3_ONE_SHOT_REAL_TRAIN_OVERRIDE_V1"
RECOVERY_LINEAGE_ID = "TEST3_ONE_SHOT_REAL_TRAIN_RECOVERY_V1"
EVIDENCE_ROOT = "artifacts/test3_one_shot_real_train_v1"
EVIDENCE_NAMESPACE = "TEST3_ONE_SHOT_REAL_TRAIN_V1_ATTEMPT_001"
RESERVATION_NAME = "00_execution_authority_reservation.json"
PERMIT_NAMES = (
    "01_fit_permit_RVBASE001_WF_2022.json",
    "02_fit_permit_RVHAR001_WF_2022.json",
    "03_fit_permit_RVBASE001_WF_2023.json",
    "04_fit_permit_RVHAR001_WF_2023.json",
)
TERMINAL_NAME = "05_terminal.json"

PLAN_KEYS = frozenset(
    {
        "activation_names",
        "classification",
        "g3p_witness_paths",
        "implementation_paths",
        "omitted_bindings",
        "prohibitions",
        "schema_version",
    }
)
ACTIVATION_NAME_KEYS = frozenset(
    {
        "activation_output_path",
        "evidence_namespace",
        "evidence_root",
        "override_id",
        "permit_names",
        "recovery_lineage_id",
        "reservation_name",
        "terminal_name",
    }
)
G3P_WITNESS_KEYS = frozenset({"request_witness", "target_witness"})
OMITTED_BINDING_KEYS = frozenset(
    {"activation_payload_digest_omitted", "implementation_digests_omitted"}
)
PROHIBITION_KEYS = frozenset(
    {"activation", "protected_access", "reservation", "scientific_execution"}
)
EXPECTED_ENVELOPE_KEYS = frozenset(
    {"activation_payload", "activation_payload_sha256"}
)
EXPECTED_PAYLOAD_KEYS = frozenset(
    {
        "fit_permit_budget",
        "implementation_path_sha256",
        "implementation_paths",
        "override_id",
        "protocol_id",
        "protocol_sha256",
        "recovery_lineage_id",
        "runtime_evidence",
        "target_space_id",
    }
)
EXPECTED_RUNTIME_EVIDENCE_KEYS = frozenset(
    {"namespace", "permit_names", "reservation_name", "root", "terminal_name"}
)

MAX_JSON_BYTES = 1 * 1024 * 1024
MAX_SOURCE_BYTES = 32 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024


class ActivationPreparationError(RuntimeError):
    """A stable fail-closed preparation error."""


def _fail(message: str) -> NoReturn:
    raise ActivationPreparationError(message)


def _require_secure_platform() -> None:
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required_flags):
        _fail("secure descriptor-rooted traversal is unavailable")
    required_dir_fd = (os.open, os.stat, os.link, os.unlink)
    if any(function not in os.supports_dir_fd for function in required_dir_fd):
        _fail("required descriptor-relative filesystem operations are unavailable")
    if os.listdir not in os.supports_fd:
        _fail("descriptor-relative directory inspection is unavailable")


def _canonical_json_bytes(value: object) -> bytes:
    """Match the reviewed G3-F canonical JSON representation exactly."""

    _assert_closed_json(value, field="document")
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _assert_closed_json(value: object, *, field: str) -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail(f"{field} contains a nonfinite number")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                _fail(f"{field} contains a non-string key")
            _assert_closed_json(child, field=f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_closed_json(child, field=f"{field}[{index}]")
        return
    _fail(f"{field} is not a closed JSON value")


def _reject_duplicate_keys(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"JSON contains a duplicate key: {key}")
        result[key] = value
    return result


def _reject_constant(name: str) -> NoReturn:
    _fail(f"JSON contains the forbidden nonfinite constant {name}")


def _parse_closed_json(raw: bytes, *, label: str) -> object:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ActivationPreparationError(f"{label} is not UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except ActivationPreparationError:
        raise
    except (TypeError, ValueError) as exc:
        raise ActivationPreparationError(f"{label} is not closed JSON") from exc
    _assert_closed_json(value, field=label)
    return value


def _relative_parts(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        _fail(f"{label} must be a non-empty repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value:
        _fail(f"{label} must be a normalized repository-relative POSIX path")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        _fail(f"{label} contains an empty or dotted component")
    return tuple(parts)


def _open_repository_root(root: Path) -> int:
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw.startswith("/") or "\x00" in raw:
        _fail("repository root must be an absolute local path")
    if os.path.normpath(raw) != raw:
        _fail("repository root must be normalized")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        descriptors.append(os.open("/", flags))
        for component in PurePosixPath(raw).parts[1:]:
            descriptors.append(os.open(component, flags, dir_fd=descriptors[-1]))
        result = os.dup(descriptors[-1])
    except OSError as exc:
        raise ActivationPreparationError(
            "repository root is missing, symlinked, or not a directory"
        ) from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return result


def _open_parent(
    root_fd: int,
    relative: str,
    *,
    allow_missing: bool = False,
) -> tuple[int, str] | None:
    parts = _relative_parts(relative, label="repository path")
    descriptor = os.dup(root_fd)
    try:
        for component in parts[:-1]:
            try:
                successor = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if allow_missing:
                    os.close(descriptor)
                    return None
                raise
            os.close(descriptor)
            descriptor = successor
        return descriptor, parts[-1]
    except OSError as exc:
        os.close(descriptor)
        raise ActivationPreparationError(
            f"repository path parent is missing, symlinked, or unsafe: {relative}"
        ) from exc


def _read_regular(root_fd: int, relative: str, *, limit: int, label: str) -> bytes:
    opened = _open_parent(root_fd, relative)
    if opened is None:
        _fail(f"{label} is missing")
    parent_fd, name = opened
    try:
        try:
            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        except OSError as exc:
            raise ActivationPreparationError(
                f"{label} is missing, symlinked, or unreadable"
            ) from exc
        try:
            status = os.fstat(file_fd)
            if not stat.S_ISREG(status.st_mode):
                _fail(f"{label} is not a regular file")
            if status.st_size > limit:
                _fail(f"{label} exceeds the bounded read size")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(file_fd, READ_CHUNK_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    _fail(f"{label} changed beyond the bounded read size")
                chunks.append(chunk)
            observed = os.fstat(file_fd)
            if (observed.st_dev, observed.st_ino, observed.st_size) != (
                status.st_dev,
                status.st_ino,
                status.st_size,
            ):
                _fail(f"{label} changed while it was read")
            return b"".join(chunks)
        finally:
            os.close(file_fd)
    finally:
        os.close(parent_fd)


def _path_exists(root_fd: int, relative: str) -> bool:
    opened = _open_parent(root_fd, relative, allow_missing=True)
    if opened is None:
        return False
    parent_fd, name = opened
    try:
        try:
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise ActivationPreparationError(
                f"could not inspect repository path: {relative}"
            ) from exc
        return True
    finally:
        os.close(parent_fd)


def _literal(node: ast.AST, *, field: str) -> object:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, bool)):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_literal(item, field=field) for item in node.elts)
    if isinstance(node, ast.List):
        return [_literal(item, field=field) for item in node.elts]
    if isinstance(node, (ast.Set, ast.Dict)):
        try:
            return ast.literal_eval(node)
        except (ValueError, TypeError) as exc:
            raise ActivationPreparationError(f"{field} is not a closed literal") from exc
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        and len(node.args) == 1
        and not node.keywords
    ):
        value = _literal(node.args[0], field=field)
        if not isinstance(value, (set, tuple, list)):
            _fail(f"{field} has an invalid frozenset literal")
        return frozenset(value)
    _fail(f"{field} is not a supported closed source literal")


def _source_assignments(raw: bytes, *, label: str) -> dict[str, ast.AST]:
    try:
        tree = ast.parse(raw, filename=label)
    except SyntaxError as exc:
        raise ActivationPreparationError(f"{label} is not valid Python source") from exc
    values: dict[str, ast.AST] = {}
    duplicates: set[str] = set()
    for statement in tree.body:
        name: str | None = None
        value: ast.AST | None = None
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            name, value = statement.target.id, statement.value
        elif isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                name, value = target.id, statement.value
        if name is not None and value is not None:
            if name in values:
                duplicates.add(name)
            values[name] = value
    if duplicates:
        _fail(f"{label} reassigns required source constants")
    return values


def _required_literal(assignments: Mapping[str, ast.AST], name: str, *, label: str) -> object:
    node = assignments.get(name)
    if node is None:
        _fail(f"{label} is missing required constant {name}")
    return _literal(node, field=f"{label}:{name}")


def _reviewed_contract(root_fd: int) -> dict[str, object]:
    contract_raw = _read_regular(
        root_fd, CONTRACT_PATH, limit=MAX_SOURCE_BYTES, label="Test 3 contract source"
    )
    g3p_raw = _read_regular(
        root_fd, G3P_PATH, limit=MAX_SOURCE_BYTES, label="reviewed G3-P source"
    )
    g3f_raw = _read_regular(
        root_fd, G3F_PATH, limit=MAX_SOURCE_BYTES, label="reviewed G3-F source"
    )
    contract = _source_assignments(contract_raw, label=CONTRACT_PATH)
    g3p = _source_assignments(g3p_raw, label=G3P_PATH)
    g3f = _source_assignments(g3f_raw, label=G3F_PATH)

    protocol_id = _required_literal(contract, "PROTOCOL_ID", label=CONTRACT_PATH)
    protocol_digest = _required_literal(contract, "PROTOCOL_SHA256", label=CONTRACT_PATH)
    target_space_id = _required_literal(contract, "TARGET_SPACE_ID", label=CONTRACT_PATH)
    fit_budget = _required_literal(contract, "REAL_FOLD_FIT_BUDGET", label=CONTRACT_PATH)
    if not isinstance(protocol_id, str) or not isinstance(target_space_id, str):
        _fail("reviewed protocol and target-space identities must be strings")
    if not _is_digest(protocol_digest):
        _fail("reviewed protocol digest constant is not lowercase SHA-256")
    if isinstance(fit_budget, bool) or not isinstance(fit_budget, int) or fit_budget != 4:
        _fail("reviewed real fit-permit budget is not exactly four")

    reviewed_paths = _required_literal(
        g3f, "REVIEWED_IMPLEMENTATION_PATHS", label=G3F_PATH
    )
    envelope_keys = _required_literal(g3f, "ACTIVATION_ENVELOPE_KEYS", label=G3F_PATH)
    payload_keys = _required_literal(g3f, "ACTIVATION_PAYLOAD_KEYS", label=G3F_PATH)
    runtime_keys = _required_literal(g3f, "RUNTIME_EVIDENCE_KEYS", label=G3F_PATH)
    claim_suffix = _required_literal(g3f, "_ACTIVATION_CLAIM_SUFFIX", label=G3F_PATH)
    if not isinstance(reviewed_paths, tuple) or not all(
        isinstance(item, str) for item in reviewed_paths
    ):
        _fail("reviewed implementation paths are not one literal ordered tuple")
    if frozenset(envelope_keys) != EXPECTED_ENVELOPE_KEYS:
        _fail("reviewed activation envelope schema drifted")
    if frozenset(payload_keys) != EXPECTED_PAYLOAD_KEYS:
        _fail("reviewed activation payload schema drifted")
    if frozenset(runtime_keys) != EXPECTED_RUNTIME_EVIDENCE_KEYS:
        _fail("reviewed runtime-evidence schema drifted")
    if not isinstance(claim_suffix, str) or not claim_suffix:
        _fail("reviewed activation-claim suffix is invalid")

    recovery_root = _required_literal(
        g3p, "G3P_RECOVERY_OUTPUT_SUBPATH", label=G3P_PATH
    )
    request_name = _required_literal(
        g3p, "G3P_RECOVERY_REQUEST_WITNESS", label=G3P_PATH
    )
    target_name = _required_literal(
        g3p, "G3P_RECOVERY_TARGET_WITNESS", label=G3P_PATH
    )
    if not all(isinstance(item, str) for item in (recovery_root, request_name, target_name)):
        _fail("reviewed G3-P recovery witness constants are invalid")
    request_witness = f"{recovery_root}/{RECOVERY_LINEAGE_ID}/{request_name}"
    target_witness = f"{recovery_root}/{RECOVERY_LINEAGE_ID}/{target_name}"
    for label, relative in (
        ("request witness", request_witness),
        ("target witness", target_witness),
    ):
        _relative_parts(relative, label=label)

    protocol_raw = _read_regular(
        root_fd, PROTOCOL_PATH, limit=MAX_SOURCE_BYTES, label="ratified protocol document"
    )
    observed_protocol_digest = hashlib.sha256(protocol_raw).hexdigest()
    if observed_protocol_digest != protocol_digest:
        _fail("ratified protocol document bytes do not match the reviewed contract")

    return {
        "claim_suffix": claim_suffix,
        "fit_budget": fit_budget,
        "implementation_paths": reviewed_paths,
        "protocol_id": protocol_id,
        "protocol_sha256": protocol_digest,
        "request_witness": request_witness,
        "target_space_id": target_space_id,
        "target_witness": target_witness,
    }


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validated_plan(root_fd: int, contract: Mapping[str, object]) -> dict[str, object]:
    raw = _read_regular(root_fd, PLAN_PATH, limit=MAX_JSON_BYTES, label="activation plan")
    value = _parse_closed_json(raw, label="activation plan")
    if not isinstance(value, dict) or frozenset(value) != PLAN_KEYS:
        _fail("activation plan does not have the exact closed top-level schema")
    if raw != _canonical_json_bytes(value):
        _fail("activation plan is not exact canonical JSON")
    if value["schema_version"] != PLAN_SCHEMA_VERSION:
        _fail("activation plan schema version is unsupported")
    if value["classification"] != PLAN_CLASSIFICATION:
        _fail("activation plan classification is not preparation-only/no-authority")

    names = value["activation_names"]
    if not isinstance(names, dict) or frozenset(names) != ACTIVATION_NAME_KEYS:
        _fail("activation plan naming block is not closed")
    expected_names = {
        "activation_output_path": ACTIVATION_OUTPUT_PATH,
        "evidence_namespace": EVIDENCE_NAMESPACE,
        "evidence_root": EVIDENCE_ROOT,
        "override_id": OVERRIDE_ID,
        "permit_names": list(PERMIT_NAMES),
        "recovery_lineage_id": RECOVERY_LINEAGE_ID,
        "reservation_name": RESERVATION_NAME,
        "terminal_name": TERMINAL_NAME,
    }
    if names != expected_names:
        _fail("activation plan naming block drifted")

    witnesses = value["g3p_witness_paths"]
    if not isinstance(witnesses, dict) or frozenset(witnesses) != G3P_WITNESS_KEYS:
        _fail("activation plan G3-P witness block is not closed")
    expected_witnesses = {
        "request_witness": contract["request_witness"],
        "target_witness": contract["target_witness"],
    }
    if witnesses != expected_witnesses:
        _fail("activation plan G3-P witness paths are not mechanically derived")

    paths = value["implementation_paths"]
    if not isinstance(paths, list) or tuple(paths) != contract["implementation_paths"]:
        _fail("activation plan does not bind the exact ordered implementation paths")
    for index, relative in enumerate(paths):
        _relative_parts(relative, label=f"implementation_paths[{index}]")

    omitted = value["omitted_bindings"]
    if (
        not isinstance(omitted, dict)
        or frozenset(omitted) != OMITTED_BINDING_KEYS
        or any(item is not True for item in omitted.values())
    ):
        _fail("activation plan must omit both digest bindings")
    prohibitions = value["prohibitions"]
    if (
        not isinstance(prohibitions, dict)
        or frozenset(prohibitions) != PROHIBITION_KEYS
        or any(item is not True for item in prohibitions.values())
    ):
        _fail("activation plan must preserve every preparation prohibition")
    return value


def _implementation_digests(
    root_fd: int, implementation_paths: Sequence[object]
) -> tuple[str, ...]:
    digests: list[str] = []
    for index, relative in enumerate(implementation_paths):
        if not isinstance(relative, str):
            _fail(f"implementation path {index} is not a string")
        raw = _read_regular(
            root_fd,
            relative,
            limit=MAX_SOURCE_BYTES,
            label=f"reviewed implementation path {index + 1}",
        )
        digests.append(hashlib.sha256(raw).hexdigest())
    return tuple(digests)


def _expected_envelope(
    root_fd: int, plan: Mapping[str, object], contract: Mapping[str, object]
) -> dict[str, object]:
    names = plan["activation_names"]
    if not isinstance(names, Mapping):
        _fail("activation plan naming block disappeared")
    paths = plan["implementation_paths"]
    if not isinstance(paths, list):
        _fail("activation plan implementation paths disappeared")
    payload: dict[str, object] = {
        "fit_permit_budget": contract["fit_budget"],
        "implementation_path_sha256": list(_implementation_digests(root_fd, paths)),
        "implementation_paths": list(paths),
        "override_id": names["override_id"],
        "protocol_id": contract["protocol_id"],
        "protocol_sha256": contract["protocol_sha256"],
        "recovery_lineage_id": names["recovery_lineage_id"],
        "runtime_evidence": {
            "namespace": names["evidence_namespace"],
            "permit_names": list(names["permit_names"]),
            "reservation_name": names["reservation_name"],
            "root": names["evidence_root"],
            "terminal_name": names["terminal_name"],
        },
        "target_space_id": contract["target_space_id"],
    }
    if frozenset(payload) != EXPECTED_PAYLOAD_KEYS:
        _fail("constructed activation payload is not closed")
    runtime = payload["runtime_evidence"]
    if not isinstance(runtime, dict) or frozenset(runtime) != EXPECTED_RUNTIME_EVIDENCE_KEYS:
        _fail("constructed runtime-evidence block is not closed")
    payload_digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    envelope = {
        "activation_payload": payload,
        "activation_payload_sha256": payload_digest,
    }
    if frozenset(envelope) != EXPECTED_ENVELOPE_KEYS:
        _fail("constructed activation envelope is not closed")
    reparsed = _parse_closed_json(_canonical_json_bytes(envelope), label="in-memory envelope")
    if reparsed != envelope:
        _fail("constructed activation envelope failed canonical revalidation")
    return envelope


def _absence_paths(plan: Mapping[str, object], contract: Mapping[str, object]) -> tuple[str, ...]:
    names = plan["activation_names"]
    if not isinstance(names, Mapping):
        _fail("activation plan naming block disappeared")
    root = str(names["evidence_root"])
    namespace = str(names["evidence_namespace"])
    reservation = str(names["reservation_name"])
    claim = f"{root}/{namespace}/{reservation}{contract['claim_suffix']}"
    recovery_directory = "/".join(
        (
            str(contract["request_witness"]).rsplit("/", 1)[0],
        )
    )
    paths = (
        ACTIVATION_OUTPUT_PATH,
        root,
        f"{root}/{namespace}",
        claim,
        recovery_directory,
        str(contract["request_witness"]),
        str(contract["target_witness"]),
    )
    for index, relative in enumerate(paths):
        _relative_parts(relative, label=f"absence path {index}")
    return paths


def _require_absent(
    root_fd: int,
    plan: Mapping[str, object],
    contract: Mapping[str, object],
    *,
    include_activation: bool,
) -> None:
    for relative in _absence_paths(plan, contract):
        if not include_activation and relative == ACTIVATION_OUTPUT_PATH:
            continue
        if _path_exists(root_fd, relative):
            _fail(f"prohibited activation or evidence path already exists: {relative}")


def _reject_additional_activation_candidates(root_fd: int) -> None:
    """Reject sibling files that could masquerade as another V1 activation candidate."""

    opened = _open_parent(root_fd, ACTIVATION_OUTPUT_PATH)
    if opened is None:
        _fail("activation output parent is missing")
    parent_fd, expected_name = opened
    try:
        prefix = expected_name.removesuffix(".json")
        for name in os.listdir(parent_fd):
            is_candidate = name.startswith(
                (prefix, f".{expected_name}.private-")
            )
            if name != expected_name and is_candidate:
                _fail(f"an additional activation candidate exists: {name}")
    except OSError as exc:
        raise ActivationPreparationError(
            "activation output directory could not be inspected"
        ) from exc
    finally:
        os.close(parent_fd)


def _publish_exclusive(root_fd: int, relative: str, payload: bytes) -> None:
    opened = _open_parent(root_fd, relative)
    if opened is None:
        _fail("activation output parent is missing")
    parent_fd, name = opened
    staging_name: str | None = None
    staging_fd: int | None = None
    published = False
    try:
        for _attempt in range(32):
            candidate = f".{name}.private-{os.getpid()}-{secrets.token_hex(8)}"
            try:
                staging_fd = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o400,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            staging_name = candidate
            break
        if staging_fd is None or staging_name is None:
            _fail("could not allocate a private activation staging file")
        view = memoryview(payload)
        while view:
            written = os.write(staging_fd, view)
            if written <= 0:
                _fail("activation staging write made no progress")
            view = view[written:]
        os.fsync(staging_fd)
        os.close(staging_fd)
        staging_fd = None
        try:
            os.link(
                staging_name,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise ActivationPreparationError(
                "activation output already exists; create-once publication is refused"
            ) from exc
        published = True
        os.fsync(parent_fd)
    except ActivationPreparationError:
        raise
    except OSError as exc:
        disposition = " after publication; durability is unknown" if published else ""
        raise ActivationPreparationError(
            f"activation publication failed{disposition}"
        ) from exc
    finally:
        if staging_fd is not None:
            os.close(staging_fd)
        if staging_name is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError as exc:
                raise ActivationPreparationError(
                    "activation staging cleanup or directory durability failed"
                ) from exc
        os.close(parent_fd)


def run_mode(mode: str, *, repository_root: Path) -> None:
    """Run one closed static or publication mode."""

    if mode not in {"check", "create", "verify-existing"}:
        _fail("mode must be exactly check, create, or verify-existing")
    _require_secure_platform()
    root_fd = _open_repository_root(repository_root)
    try:
        contract = _reviewed_contract(root_fd)
        plan = _validated_plan(root_fd, contract)
        envelope = _expected_envelope(root_fd, plan, contract)
        _reject_additional_activation_candidates(root_fd)
        if mode == "verify-existing":
            raw = _read_regular(
                root_fd,
                ACTIVATION_OUTPUT_PATH,
                limit=MAX_JSON_BYTES,
                label="existing activation output",
            )
            observed = _parse_closed_json(raw, label="existing activation output")
            if not isinstance(observed, dict) or frozenset(observed) != EXPECTED_ENVELOPE_KEYS:
                _fail("existing activation output does not have the closed envelope schema")
            expected_raw = _canonical_json_bytes(envelope)
            if observed != envelope or raw != expected_raw:
                _fail("existing activation output does not match current exact bindings")
            _require_absent(root_fd, plan, contract, include_activation=False)
            return
        _require_absent(root_fd, plan, contract, include_activation=True)
        if mode == "create":
            _publish_exclusive(root_fd, ACTIVATION_OUTPUT_PATH, _canonical_json_bytes(envelope))
    finally:
        os.close(root_fd)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically prepare or verify the closed Test 3 activation envelope."
    )
    parser.add_argument("--mode", choices=("check", "create", "verify-existing"), required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        run_mode(args.mode, repository_root=args.repository_root)
    except ActivationPreparationError as exc:
        print(f"TEST3_ACTIVATION_PREPARATION_ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print(
            "TEST3_ACTIVATION_PREPARATION_ERROR: local filesystem operation failed",
            file=sys.stderr,
        )
        return 2
    print(f"TEST3_ACTIVATION_PREPARATION_{args.mode.upper().replace('-', '_')}_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

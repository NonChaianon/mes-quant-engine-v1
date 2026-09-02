"""Create or verify the closed, Git-bound Test 3 one-shot V2 activation.

This strict-stdlib tool is data-free.  It reads only the V2 plan, Owner authorization,
ratified protocol, Test 3 contract and exact six implementation paths.  It never imports a
Test 3 runtime module, runner, provider or data package and never creates runtime evidence.
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
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import NoReturn

SCHEMA_VERSION = "MES_TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_PLAN_V2"
CLASSIFICATION = "OWNER_AUTHORIZED_V2_ONE_SHOT_ACTIVATION_PLAN"
PLAN_PATH = "configs/research/test3_one_shot_real_train_activation_plan_v2.json"
OUTPUT_PATH = "docs/research/TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V2.json"
OWNER_AUTHORIZATION_PATH = (
    "docs/research/TEST3_ONE_SHOT_REAL_TRAIN_EXECUTION_AUTHORIZATION_V2.md"
)
PROTOCOL_PATH = "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md"
CONTRACT_PATH = "src/mes_quant/exploration/test3_contract.py"
G3P_PATH = "src/mes_quant/exploration/test3_g3p_pre_fit.py"
G3F_PATH = "src/mes_quant/exploration/test3_g3f_one_shot.py"

ACTIVATION_VERSION = "MES_TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V2"
ACTIVATION_ID = "TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V2"
SYMBOLIC_REF = "refs/heads/governance/test3-one-shot-real-train-v2"
ORIGIN_REF = "refs/remotes/origin/governance/test3-one-shot-real-train-v2"
OVERRIDE_ID = "TEST3_ONE_SHOT_REAL_TRAIN_OVERRIDE_V2"
RECOVERY_LINEAGE_ID = "TEST3_ONE_SHOT_REAL_TRAIN_RECOVERY_V2"
EVIDENCE_ROOT = "artifacts/test3_one_shot_real_train_v2"
EVIDENCE_NAMESPACE = "TEST3_ONE_SHOT_REAL_TRAIN_V2_ATTEMPT_001"
RESERVATION_NAME = "00_execution_authority_reservation.json"
PERMIT_NAMES = (
    "01_fit_permit_RVBASE001_WF_2022.json",
    "02_fit_permit_RVHAR001_WF_2022.json",
    "03_fit_permit_RVBASE001_WF_2023.json",
    "04_fit_permit_RVHAR001_WF_2023.json",
)
TERMINAL_NAME = "05_terminal.json"
IMPLEMENTATION_PATHS = (
    "src/mes_quant/exploration/test3_g3p_pre_fit.py",
    "tests/test_test3_g3p_pre_fit.py",
    "src/mes_quant/exploration/test3_g3f_one_shot.py",
    "tests/test_test3_g3f_one_shot.py",
    "tools/run_test3_one_shot_scientific_recovery.py",
    "tests/test_run_test3_one_shot_scientific_recovery.py",
)

ENVELOPE_KEYS = frozenset({"activation_payload", "activation_payload_sha256"})
PAYLOAD_KEYS = frozenset(
    {
        "activation_id",
        "activation_version",
        "fit_permit_budget",
        "git_binding",
        "implementation_path_sha256",
        "implementation_paths",
        "override_id",
        "owner_authorization",
        "protocol_id",
        "protocol_sha256",
        "recovery_lineage_id",
        "runtime_evidence",
        "target_space_id",
    }
)
RUNTIME_KEYS = frozenset(
    {"namespace", "permit_names", "reservation_name", "root", "terminal_name"}
)
GIT_KEYS = frozenset({"head", "origin_ref", "symbolic_ref", "tree"})
OWNER_KEYS = frozenset({"path", "sha256"})
MAX_BYTES = 32 * 1024 * 1024
JSON_MAX_BYTES = 1 * 1024 * 1024


class ActivationV2Error(RuntimeError):
    """Stable fail-closed V2 activation error."""


def _fail(message: str) -> NoReturn:
    raise ActivationV2Error(message)


def _canonical(value: object) -> bytes:
    _closed(value, field="document")
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


def _closed(value: object, *, field: str) -> None:
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
            _closed(child, field=f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _closed(child, field=f"{field}[{index}]")
        return
    _fail(f"{field} is not closed JSON")


def _pairs(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"JSON contains duplicate key {key}")
        result[key] = value
    return result


def _constant(name: str) -> NoReturn:
    _fail(f"JSON contains nonfinite constant {name}")


def _parse(raw: bytes, *, label: str) -> object:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise ActivationV2Error(f"{label} is not closed UTF-8 JSON") from exc
    _closed(value, field=label)
    return value


def _parts(relative: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        _fail(f"{label} is not a repository-relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or str(path) != relative or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        _fail(f"{label} is unsafe or non-normalized")
    return tuple(path.parts)


def _open_root(root: Path) -> int:
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw.startswith("/") or os.path.normpath(raw) != raw:
        _fail("repository root must be an exact absolute normalized path")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        descriptors.append(os.open("/", flags))
        for component in PurePosixPath(raw).parts[1:]:
            descriptors.append(os.open(component, flags, dir_fd=descriptors[-1]))
        return os.dup(descriptors[-1])
    except OSError as exc:
        raise ActivationV2Error("repository root is missing, symlinked or unsafe") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _open_parent(root_fd: int, relative: str, *, missing_ok: bool = False) -> tuple[int, str] | None:
    parts = _parts(relative, label="repository path")
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
                if missing_ok:
                    os.close(descriptor)
                    return None
                raise
            os.close(descriptor)
            descriptor = successor
        return descriptor, parts[-1]
    except OSError as exc:
        os.close(descriptor)
        raise ActivationV2Error(f"unsafe parent for {relative}") from exc


def _read(root_fd: int, relative: str, *, limit: int, label: str) -> bytes:
    opened = _open_parent(root_fd, relative)
    if opened is None:
        _fail(f"{label} is missing")
    parent, name = opened
    try:
        try:
            handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError as exc:
            raise ActivationV2Error(f"{label} is missing, symlinked or unreadable") from exc
        try:
            before = os.fstat(handle)
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                _fail(f"{label} is not a bounded regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(handle, 65_536)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    _fail(f"{label} exceeded its read bound")
                chunks.append(chunk)
            after = os.fstat(handle)
            if (before.st_dev, before.st_ino, before.st_size) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
            ):
                _fail(f"{label} changed while read")
            return b"".join(chunks)
        finally:
            os.close(handle)
    finally:
        os.close(parent)


def _exists(root_fd: int, relative: str) -> bool:
    opened = _open_parent(root_fd, relative, missing_ok=True)
    if opened is None:
        return False
    parent, name = opened
    try:
        try:
            os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True
    finally:
        os.close(parent)


def _source_literals(raw: bytes, *, label: str) -> dict[str, object]:
    try:
        tree = ast.parse(raw, filename=label)
    except SyntaxError as exc:
        raise ActivationV2Error(f"{label} is invalid Python") from exc
    result: dict[str, object] = {}
    for statement in tree.body:
        name: str | None = None
        node: ast.AST | None = None
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            name, node = statement.target.id, statement.value
        elif isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            name, node = statement.targets[0].id, statement.value
        if name is not None and node is not None:
            try:
                result[name] = ast.literal_eval(node)
            except (ValueError, TypeError):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "frozenset"
                    and len(node.args) == 1
                    and not node.keywords
                ):
                    try:
                        result[name] = frozenset(ast.literal_eval(node.args[0]))
                    except (ValueError, TypeError):
                        continue
    return result


def _contract(root_fd: int) -> dict[str, object]:
    contract = _source_literals(
        _read(root_fd, CONTRACT_PATH, limit=MAX_BYTES, label="Test 3 contract"),
        label=CONTRACT_PATH,
    )
    required = ("PROTOCOL_ID", "PROTOCOL_SHA256", "TARGET_SPACE_ID", "REAL_FOLD_FIT_BUDGET")
    if any(name not in contract for name in required):
        _fail("Test 3 contract is missing a required literal")
    protocol_digest = contract["PROTOCOL_SHA256"]
    if not _digest(protocol_digest):
        _fail("protocol digest constant is invalid")
    protocol_raw = _read(root_fd, PROTOCOL_PATH, limit=MAX_BYTES, label="ratified protocol")
    if hashlib.sha256(protocol_raw).hexdigest() != protocol_digest:
        _fail("ratified protocol bytes drifted")
    if contract["REAL_FOLD_FIT_BUDGET"] != 4:
        _fail("fit-permit budget is not exactly four")
    g3f = _source_literals(
        _read(root_fd, G3F_PATH, limit=MAX_BYTES, label="G3-F implementation"),
        label=G3F_PATH,
    )
    expected_g3f = {
        "ACTIVATION_ENVELOPE_KEYS": ENVELOPE_KEYS,
        "ACTIVATION_V2_EVIDENCE_NAMESPACE": EVIDENCE_NAMESPACE,
        "ACTIVATION_V2_EVIDENCE_ROOT": EVIDENCE_ROOT,
        "ACTIVATION_V2_GIT_BINDING_KEYS": GIT_KEYS,
        "ACTIVATION_V2_ID": ACTIVATION_ID,
        "ACTIVATION_V2_ORIGIN_REF": ORIGIN_REF,
        "ACTIVATION_V2_OUTPUT_PATH": OUTPUT_PATH,
        "ACTIVATION_V2_OVERRIDE_ID": OVERRIDE_ID,
        "ACTIVATION_V2_OWNER_AUTHORIZATION_KEYS": OWNER_KEYS,
        "ACTIVATION_V2_OWNER_AUTHORIZATION_PATH": OWNER_AUTHORIZATION_PATH,
        "ACTIVATION_V2_PAYLOAD_KEYS": PAYLOAD_KEYS,
        "ACTIVATION_V2_PERMIT_NAMES": PERMIT_NAMES,
        "ACTIVATION_V2_RECOVERY_LINEAGE_ID": RECOVERY_LINEAGE_ID,
        "ACTIVATION_V2_RESERVATION_NAME": RESERVATION_NAME,
        "ACTIVATION_V2_SYMBOLIC_REF": SYMBOLIC_REF,
        "ACTIVATION_V2_TERMINAL_NAME": TERMINAL_NAME,
        "ACTIVATION_V2_VERSION": ACTIVATION_VERSION,
        "REVIEWED_IMPLEMENTATION_PATHS": IMPLEMENTATION_PATHS,
        "RUNTIME_EVIDENCE_KEYS": RUNTIME_KEYS,
    }
    if any(g3f.get(name) != expected for name, expected in expected_g3f.items()):
        _fail("the reviewed G3-F V2 loader contract drifted from this generator")
    return contract


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _expected_plan(root_fd: int, contract: Mapping[str, object]) -> dict[str, object]:
    g3p = _source_literals(
        _read(root_fd, G3P_PATH, limit=MAX_BYTES, label="G3-P implementation"),
        label=G3P_PATH,
    )
    recovery_root = g3p.get("G3P_RECOVERY_OUTPUT_SUBPATH")
    request_name = g3p.get("G3P_RECOVERY_REQUEST_WITNESS")
    target_name = g3p.get("G3P_RECOVERY_TARGET_WITNESS")
    if not all(isinstance(item, str) for item in (recovery_root, request_name, target_name)):
        _fail("G3-P recovery witness literals are unavailable")
    return {
        "activation_id": ACTIVATION_ID,
        "activation_names": {
            "activation_output_path": OUTPUT_PATH,
            "evidence_namespace": EVIDENCE_NAMESPACE,
            "evidence_root": EVIDENCE_ROOT,
            "override_id": OVERRIDE_ID,
            "permit_names": list(PERMIT_NAMES),
            "recovery_lineage_id": RECOVERY_LINEAGE_ID,
            "reservation_name": RESERVATION_NAME,
            "terminal_name": TERMINAL_NAME,
        },
        "activation_version": ACTIVATION_VERSION,
        "classification": CLASSIFICATION,
        "g3p_witness_paths": {
            "request_witness": f"{recovery_root}/{RECOVERY_LINEAGE_ID}/{request_name}",
            "target_witness": f"{recovery_root}/{RECOVERY_LINEAGE_ID}/{target_name}",
        },
        "git_binding_refs": {"origin_ref": ORIGIN_REF, "symbolic_ref": SYMBOLIC_REF},
        "implementation_paths": list(IMPLEMENTATION_PATHS),
        "omitted_bindings": {
            "activation_payload_digest_omitted": True,
            "git_object_ids_omitted": True,
            "implementation_digests_omitted": True,
            "owner_authorization_digest_omitted": True,
        },
        "owner_authorization_path": OWNER_AUTHORIZATION_PATH,
        "prohibitions": {
            "data_or_target_access": True,
            "evidence_or_namespace_creation": True,
            "fit": True,
            "loader_or_reservation": True,
            "provider_access": True,
            "validation_or_final_test": True,
        },
        "schema_version": SCHEMA_VERSION,
    }


def _git(root: Path, *arguments: str, allow_empty: bool = False) -> str:
    env = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
    }
    try:
        completed = subprocess.run(
            ("git", "-C", os.fspath(root), *arguments),
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            env=env,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActivationV2Error("Git state could not be machine-resolved") from exc
    if completed.returncode != 0:
        _fail("Git state predicate failed")
    try:
        value = completed.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ActivationV2Error("Git output was not ASCII") from exc
    if (not allow_empty and not value) or "\n" in value or "\r" in value:
        _fail("Git state did not resolve to one bounded line")
    return value


def _git_binding(root: Path) -> dict[str, str]:
    symbolic = _git(root, "symbolic-ref", "-q", "HEAD")
    head = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "--verify", "HEAD^{tree}")
    origin = _git(root, "rev-parse", "--verify", f"{ORIGIN_REF}^{{commit}}")
    dirty = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
        allow_empty=True,
    )
    if symbolic != SYMBOLIC_REF or head != origin or dirty:
        _fail("symbolic ref, origin equality, or clean tracked/index predicate failed")
    return {"head": head, "origin_ref": ORIGIN_REF, "symbolic_ref": symbolic, "tree": tree}


def _envelope(root_fd: int, root: Path, contract: Mapping[str, object]) -> dict[str, object]:
    owner_raw = _read(root_fd, OWNER_AUTHORIZATION_PATH, limit=MAX_BYTES, label="Owner authorization")
    digests = [
        hashlib.sha256(_read(root_fd, path, limit=MAX_BYTES, label=f"implementation {index + 1}")).hexdigest()
        for index, path in enumerate(IMPLEMENTATION_PATHS)
    ]
    payload = {
        "activation_id": ACTIVATION_ID,
        "activation_version": ACTIVATION_VERSION,
        "fit_permit_budget": contract["REAL_FOLD_FIT_BUDGET"],
        "git_binding": _git_binding(root),
        "implementation_path_sha256": digests,
        "implementation_paths": list(IMPLEMENTATION_PATHS),
        "override_id": OVERRIDE_ID,
        "owner_authorization": {
            "path": OWNER_AUTHORIZATION_PATH,
            "sha256": hashlib.sha256(owner_raw).hexdigest(),
        },
        "protocol_id": contract["PROTOCOL_ID"],
        "protocol_sha256": contract["PROTOCOL_SHA256"],
        "recovery_lineage_id": RECOVERY_LINEAGE_ID,
        "runtime_evidence": {
            "namespace": EVIDENCE_NAMESPACE,
            "permit_names": list(PERMIT_NAMES),
            "reservation_name": RESERVATION_NAME,
            "root": EVIDENCE_ROOT,
            "terminal_name": TERMINAL_NAME,
        },
        "target_space_id": contract["TARGET_SPACE_ID"],
    }
    if frozenset(payload) != PAYLOAD_KEYS:
        _fail("constructed V2 payload is not closed")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    envelope = {"activation_payload": payload, "activation_payload_sha256": digest}
    if frozenset(envelope) != ENVELOPE_KEYS:
        _fail("constructed V2 envelope is not closed")
    return envelope


def _require_absent(root_fd: int, plan: Mapping[str, object], *, include_output: bool) -> None:
    witnesses = plan["g3p_witness_paths"]
    paths = (
        OUTPUT_PATH,
        EVIDENCE_ROOT,
        f"{EVIDENCE_ROOT}/{EVIDENCE_NAMESPACE}",
        str(witnesses["request_witness"]).rsplit("/", 1)[0],
        str(witnesses["request_witness"]),
        str(witnesses["target_witness"]),
    )
    for relative in paths:
        if relative == OUTPUT_PATH and not include_output:
            continue
        if _exists(root_fd, relative):
            _fail(f"activation or evidence path already exists: {relative}")


def _publish(root_fd: int, payload: bytes) -> None:
    opened = _open_parent(root_fd, OUTPUT_PATH)
    if opened is None:
        _fail("activation output parent is missing")
    parent, name = opened
    staging: str | None = None
    handle: int | None = None
    try:
        for _ in range(32):
            candidate = f".{name}.private-{os.getpid()}-{secrets.token_hex(8)}"
            try:
                handle = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o400,
                    dir_fd=parent,
                )
            except FileExistsError:
                continue
            staging = candidate
            break
        if handle is None or staging is None:
            _fail("private activation staging allocation failed")
        view = memoryview(payload)
        while view:
            count = os.write(handle, view)
            if count <= 0:
                _fail("activation staging write made no progress")
            view = view[count:]
        os.fsync(handle)
        os.close(handle)
        handle = None
        try:
            os.link(staging, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        except FileExistsError as exc:
            raise ActivationV2Error("activation output already exists") from exc
        os.fsync(parent)
    except OSError as exc:
        raise ActivationV2Error("exclusive activation publication failed") from exc
    finally:
        if handle is not None:
            os.close(handle)
        if staging is not None:
            try:
                os.unlink(staging, dir_fd=parent)
                os.fsync(parent)
            except OSError as exc:
                raise ActivationV2Error("activation staging cleanup failed") from exc
        os.close(parent)


def run_mode(mode: str, *, repository_root: Path) -> None:
    if mode not in {"check", "create", "verify-existing"}:
        _fail("mode must be check, create, or verify-existing")
    if any(not hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        _fail("secure descriptor-rooted traversal is unavailable")
    root_fd = _open_root(repository_root)
    try:
        contract = _contract(root_fd)
        expected_plan = _expected_plan(root_fd, contract)
        plan_raw = _read(root_fd, PLAN_PATH, limit=JSON_MAX_BYTES, label="V2 activation plan")
        plan = _parse(plan_raw, label="V2 activation plan")
        if plan != expected_plan or plan_raw != _canonical(expected_plan):
            _fail("V2 activation plan drifted or is noncanonical")
        envelope = _envelope(root_fd, repository_root, contract)
        if mode == "verify-existing":
            observed_raw = _read(root_fd, OUTPUT_PATH, limit=JSON_MAX_BYTES, label="V2 activation")
            observed = _parse(observed_raw, label="V2 activation")
            if observed != envelope or observed_raw != _canonical(envelope):
                _fail("existing V2 activation does not match current exact bindings")
            _require_absent(root_fd, plan, include_output=False)
            return
        _require_absent(root_fd, plan, include_output=True)
        if mode == "create":
            _publish(root_fd, _canonical(envelope))
    finally:
        os.close(root_fd)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or verify the Test 3 V2 activation")
    parser.add_argument("--mode", choices=("check", "create", "verify-existing"), required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        run_mode(args.mode, repository_root=args.repository_root)
    except (ActivationV2Error, OSError) as exc:
        print(f"TEST3_ACTIVATION_V2_ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"TEST3_ACTIVATION_V2_{args.mode.upper().replace('-', '_')}_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

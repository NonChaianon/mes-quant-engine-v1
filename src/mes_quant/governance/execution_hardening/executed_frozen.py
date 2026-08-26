"""Checkout-safe integrity verification for executed-frozen documents."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

REGISTRY_PATH = Path("configs/governance/executed_frozen_registry_v1.json")
REGISTRY_SCHEMA = "MES_EXECUTED_FROZEN_REGISTRY_SCHEMA_V1"
REGISTRY_ID = "EXECUTED_FROZEN_BYTE_INTEGRITY_V1"
REGISTRY_STATUS = "OWNER_AUTHORIZED_PHASE_A_CHECKOUT_INTEGRITY"

MANDATORY_FIRST_PATH = "docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md"
MANDATORY_FIRST_SHA256 = "7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105"

SURFACE_MAP_PATH = Path("configs/governance/rehearsal_surface_map_v5.json")
SURFACE_MAP_SHA256 = "87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a"
TRANSITION_ROWS_PATH = Path("configs/governance/execution_hardening_transition_rows_v3.json")
TRANSITION_ROWS_SHA256 = "00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1"
TIME_POLICY_PATH = Path("configs/governance/execution_hardening_time_policy_v1.json")
TIME_POLICY_SHA256 = "e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e"
PRODUCTION_SURFACE_MANIFEST_PATH = Path(
    "configs/governance/execution_hardening_production_surface_manifest_v2.json"
)
PRODUCTION_SURFACE_MANIFEST_SHA256 = (
    "3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a"
)

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SHA1_PATTERN = re.compile(r"[0-9a-f]{40}")
_TOP_LEVEL_FIELDS = frozenset({"schema_version", "registry_id", "status", "entries"})
_ENTRY_FIELDS = frozenset({"path", "authoritative_sha256", "authority_evidence"})
_EVIDENCE_FIELDS = frozenset({"role", "path", "sha256"})

PHASE_A = "PHASE_A"
PHASE_B = "PHASE_B"
_PHASE_A_SURFACE_INDICES = (1, 2, 3, *range(6, 25), *range(26, 32))
_PHASE_B_SURFACE_INDICES = (4, 5, 25, *range(32, 38))


class ExecutedFrozenIntegrityError(RuntimeError):
    """The registry or a registered document failed closed."""


@dataclass(frozen=True)
class AuthorityEvidenceIdentity:
    """Hash-bound provenance identity; its referenced file is never opened here."""

    role: str
    path: str
    sha256: str


@dataclass(frozen=True)
class ExecutedFrozenEntry:
    path: str
    authoritative_sha256: str
    authority_evidence: tuple[AuthorityEvidenceIdentity, ...]


@dataclass(frozen=True)
class ExecutedFrozenRegistry:
    schema_version: str
    registry_id: str
    status: str
    entries: tuple[ExecutedFrozenEntry, ...]


@dataclass(frozen=True)
class ExecutedFrozenVerification:
    registry_id: str
    checked_paths: tuple[str, ...]
    observed_sha256: tuple[str, ...]


@dataclass(frozen=True)
class CompanionSpec:
    path: Path
    sha256: str
    identity_field: str
    identity_value: str


@dataclass(frozen=True)
class CompanionVerification:
    checked_paths: tuple[str, ...]
    observed_sha256: tuple[str, ...]
    observed_identities: tuple[str, ...]


@dataclass(frozen=True)
class ProtectedSurfaceSnapshot:
    activation_tree: str
    paths: tuple[str, ...]
    observed_sha256: tuple[str, ...]
    canonical_sha256: str


@dataclass(frozen=True)
class GitFirewallVerification:
    phase: str
    base_commit: str
    head_commit: str
    changed_paths: tuple[str, ...]
    staged_paths: tuple[str, ...]


PHASE_A_COMPANION_SPECS = (
    CompanionSpec(
        path=SURFACE_MAP_PATH,
        sha256=SURFACE_MAP_SHA256,
        identity_field="surface_map_id",
        identity_value="REHEARSAL_SURFACE_MAP_V5",
    ),
    CompanionSpec(
        path=TRANSITION_ROWS_PATH,
        sha256=TRANSITION_ROWS_SHA256,
        identity_field="schema_version",
        identity_value="MES_EXECUTION_TRANSITION_ROW_ENUM_V3",
    ),
    CompanionSpec(
        path=TIME_POLICY_PATH,
        sha256=TIME_POLICY_SHA256,
        identity_field="policy_id",
        identity_value="MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1",
    ),
    CompanionSpec(
        path=PRODUCTION_SURFACE_MANIFEST_PATH,
        sha256=PRODUCTION_SURFACE_MANIFEST_SHA256,
        identity_field="manifest_id",
        identity_value="EXECUTION_HARDENING_PRODUCTION_SURFACE_MANIFEST_V2",
    ),
)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def _canonical_relative_utf8_path(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\x00" in value
        or "\r" in value
        or "\n" in value
    ):
        raise ExecutedFrozenIntegrityError(f"{field} must be a canonical POSIX UTF-8 path")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ExecutedFrozenIntegrityError(f"{field} must be strict UTF-8") from exc
    path = PurePosixPath(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts or value != path.as_posix():
        raise ExecutedFrozenIntegrityError(f"{field} is not a canonical relative path")
    return value


def _validate_relative_checkout_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ExecutedFrozenIntegrityError(f"{field} must be a non-empty POSIX path")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ExecutedFrozenIntegrityError(f"{field} must be ASCII") from exc
    path = PurePosixPath(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts or value != path.as_posix():
        raise ExecutedFrozenIntegrityError(f"{field} is not a canonical relative path")
    return value


def _closed_object(value: object, expected_fields: frozenset[str], *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected_fields:
        raise ExecutedFrozenIntegrityError(f"{label} closed field set mismatch")
    return value


def _json_without_duplicate_keys(data: bytes, *, label: str) -> Mapping[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, value in pairs:
            if key in payload:
                raise ValueError(f"duplicate JSON key: {key}")
            payload[key] = value
        return payload

    try:
        payload = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ExecutedFrozenIntegrityError(f"PHASE_A_COMPANION_JSON_INVALID:{label}") from exc
    if not isinstance(payload, Mapping):
        raise ExecutedFrozenIntegrityError(f"PHASE_A_COMPANION_JSON_INVALID:{label}")
    return payload


def _safe_checkout_file(root: Path, relative_path: str, *, label: str) -> Path:
    unresolved = root / relative_path
    cursor = root
    for part in PurePosixPath(relative_path).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ExecutedFrozenIntegrityError(f"{label}_SYMLINK:{relative_path}")
    try:
        candidate = unresolved.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExecutedFrozenIntegrityError(f"{label}_MISSING:{relative_path}") from exc
    if root not in candidate.parents or not candidate.is_file():
        raise ExecutedFrozenIntegrityError(f"{label}_UNSAFE:{relative_path}")
    return candidate


def verify_phase_a_companions(repo_root: Path) -> CompanionVerification:
    """Verify all four co-ratified companions before any reservation-capable operation."""

    root = repo_root.resolve(strict=True)
    checked: list[str] = []
    observed_hashes: list[str] = []
    observed_identities: list[str] = []
    for spec in PHASE_A_COMPANION_SPECS:
        path = spec.path.as_posix()
        candidate = _safe_checkout_file(root, path, label="PHASE_A_COMPANION")
        data = candidate.read_bytes()
        observed = hashlib.sha256(data).hexdigest()
        if observed != spec.sha256:
            raise ExecutedFrozenIntegrityError(
                f"PHASE_A_COMPANION_HASH_MISMATCH:{path}:"
                f"expected={spec.sha256}:observed={observed}"
            )
        payload = _json_without_duplicate_keys(data, label=path)
        if payload.get(spec.identity_field) != spec.identity_value:
            raise ExecutedFrozenIntegrityError(f"PHASE_A_COMPANION_IDENTITY_MISMATCH:{path}")
        checked.append(path)
        observed_hashes.append(observed)
        observed_identities.append(spec.identity_value)
    return CompanionVerification(
        checked_paths=tuple(checked),
        observed_sha256=tuple(observed_hashes),
        observed_identities=tuple(observed_identities),
    )


def _run_git(repo_root: Path, *args: str, allowed_returncodes: Sequence[int] = (0,)) -> bytes:
    process = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        capture_output=True,
        check=False,
    )
    if process.returncode not in allowed_returncodes:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ExecutedFrozenIntegrityError(
            f"GIT_INSPECTION_FAILED:{args[0] if args else 'UNKNOWN'}:{detail}"
        )
    return process.stdout


def _decode_nul_paths(data: bytes, *, field: str) -> tuple[str, ...]:
    if data and not data.endswith(b"\x00"):
        raise ExecutedFrozenIntegrityError(f"{field} is not NUL terminated")
    raw_paths = data[:-1].split(b"\x00") if data else []
    paths: list[str] = []
    for raw_path in raw_paths:
        try:
            decoded = raw_path.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ExecutedFrozenIntegrityError(f"{field} contains non-UTF-8 path bytes") from exc
        paths.append(_canonical_relative_utf8_path(decoded, field=field))
    return tuple(paths)


def _matches_manifest_pattern(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return PurePosixPath(path).match(pattern)


def _protected_paths(paths: Sequence[str], manifest: Mapping[str, Any]) -> tuple[str, ...]:
    patterns = manifest.get("tracked_path_patterns")
    excluded = manifest.get("excluded_rehearsal_namespace")
    if (
        not isinstance(patterns, list)
        or not patterns
        or not all(isinstance(pattern, str) and pattern for pattern in patterns)
        or not isinstance(excluded, str)
        or not excluded.endswith("/**")
    ):
        raise ExecutedFrozenIntegrityError("PRODUCTION_SURFACE_MANIFEST_SEMANTICS_INVALID")
    selected = {
        path
        for path in paths
        if not _matches_manifest_pattern(path, excluded)
        and any(_matches_manifest_pattern(path, pattern) for pattern in patterns)
    }
    return tuple(sorted(selected, key=lambda value: value.encode("utf-8")))


def _load_verified_production_surface_manifest(root: Path) -> Mapping[str, Any]:
    verify_phase_a_companions(root)
    candidate = _safe_checkout_file(
        root,
        PRODUCTION_SURFACE_MANIFEST_PATH.as_posix(),
        label="PHASE_A_COMPANION",
    )
    return _json_without_duplicate_keys(
        candidate.read_bytes(),
        label=PRODUCTION_SURFACE_MANIFEST_PATH.as_posix(),
    )


def capture_protected_surface_snapshot(
    repo_root: Path,
    *,
    activation_tree: str,
    require_clean_worktree: bool = True,
) -> ProtectedSurfaceSnapshot:
    """Hash actual protected working-tree files discovered from an exact Git tree."""

    root = repo_root.resolve(strict=True)
    if _SHA1_PATTERN.fullmatch(activation_tree) is None:
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_ACTIVATION_TREE_INVALID")
    object_type = _run_git(root, "cat-file", "-t", activation_tree).decode().strip()
    if object_type != "tree":
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_ACTIVATION_TREE_INVALID")
    manifest = _load_verified_production_surface_manifest(root)
    tree_paths = _decode_nul_paths(
        _run_git(root, "ls-tree", "-r", "--name-only", "-z", activation_tree),
        field="activation tree path",
    )
    protected_tree_paths = _protected_paths(tree_paths, manifest)

    index_paths = _decode_nul_paths(
        _run_git(root, "ls-files", "-z"),
        field="index path",
    )
    protected_index_paths = _protected_paths(index_paths, manifest)
    if protected_index_paths != protected_tree_paths:
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_PATH_SET_CHANGED")

    untracked_paths = _decode_nul_paths(
        _run_git(root, "ls-files", "--others", "-z"),
        field="untracked path",
    )
    protected_untracked = _protected_paths(untracked_paths, manifest)
    if protected_untracked:
        raise ExecutedFrozenIntegrityError(
            "PROTECTED_SURFACE_UNTRACKED_EXTRA:" + ",".join(protected_untracked)
        )

    observed: list[str] = []
    canonical_rows: list[bytes] = []
    for path in protected_tree_paths:
        candidate = _safe_checkout_file(root, path, label="PROTECTED_SURFACE")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        observed.append(digest)
        canonical_rows.append(f"{path}\t{digest}\n".encode())

    if require_clean_worktree:
        status = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all", "-z")
        if status:
            raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_DIRTY_WORKTREE")

    canonical_bytes = b"".join(canonical_rows)
    return ProtectedSurfaceSnapshot(
        activation_tree=activation_tree,
        paths=protected_tree_paths,
        observed_sha256=tuple(observed),
        canonical_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
    )


def compare_protected_surface_snapshots(
    before: ProtectedSurfaceSnapshot,
    after: ProtectedSurfaceSnapshot,
) -> None:
    """Require identical actual path and byte-hash manifests across the guarded window."""

    if not isinstance(before, ProtectedSurfaceSnapshot) or not isinstance(
        after, ProtectedSurfaceSnapshot
    ):
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_SNAPSHOT_TYPE_INVALID")
    for snapshot in (before, after):
        if (
            _SHA1_PATTERN.fullmatch(snapshot.activation_tree) is None
            or len(snapshot.paths) != len(snapshot.observed_sha256)
            or tuple(sorted(snapshot.paths, key=lambda value: value.encode("utf-8")))
            != snapshot.paths
            or len(set(snapshot.paths)) != len(snapshot.paths)
            or not all(_is_sha256(digest) for digest in snapshot.observed_sha256)
        ):
            raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_SNAPSHOT_INVALID")
        canonical = b"".join(
            f"{path}\t{digest}\n".encode()
            for path, digest in zip(snapshot.paths, snapshot.observed_sha256, strict=True)
        )
        if hashlib.sha256(canonical).hexdigest() != snapshot.canonical_sha256:
            raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_SNAPSHOT_INVALID")
    if before.activation_tree != after.activation_tree:
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_ACTIVATION_TREE_CHANGED")
    if before.paths != after.paths:
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_PATH_SET_CHANGED")
    if (
        before.observed_sha256 != after.observed_sha256
        or before.canonical_sha256 != after.canonical_sha256
    ):
        raise ExecutedFrozenIntegrityError("PROTECTED_SURFACE_BYTE_HASH_CHANGED")


def _parse_name_status(data: bytes, *, field: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if data and not data.endswith(b"\x00"):
        raise ExecutedFrozenIntegrityError(f"{field} is not NUL terminated")
    fields = data[:-1].split(b"\x00") if data else []
    parsed: list[tuple[str, tuple[str, ...]]] = []
    index = 0
    while index < len(fields):
        try:
            status = fields[index].decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise ExecutedFrozenIntegrityError(f"{field} status is not ASCII") from exc
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if not status or index + path_count > len(fields):
            raise ExecutedFrozenIntegrityError(f"{field} is malformed")
        paths: list[str] = []
        for raw_path in fields[index : index + path_count]:
            try:
                path = raw_path.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise ExecutedFrozenIntegrityError(f"{field} path is not UTF-8") from exc
            paths.append(_canonical_relative_utf8_path(path, field=field))
        index += path_count
        parsed.append((status, tuple(paths)))
    return tuple(parsed)


def _surface_map_phase_paths(root: Path, phase: str) -> frozenset[str]:
    verify_phase_a_companions(root)
    surface_path = _safe_checkout_file(
        root,
        SURFACE_MAP_PATH.as_posix(),
        label="PHASE_A_COMPANION",
    )
    payload = _json_without_duplicate_keys(surface_path.read_bytes(), label=SURFACE_MAP_PATH.as_posix())
    raw_paths = payload.get("implementation_source_paths")
    if (
        not isinstance(raw_paths, list)
        or len(raw_paths) != 37
        or len(set(raw_paths)) != 37
        or not all(isinstance(path, str) for path in raw_paths)
    ):
        raise ExecutedFrozenIntegrityError("SURFACE_MAP_PATH_UNION_INVALID")
    paths = tuple(
        _canonical_relative_utf8_path(path, field="surface map path") for path in raw_paths
    )
    phase_a = frozenset(paths[index - 1] for index in _PHASE_A_SURFACE_INDICES)
    phase_b = frozenset(paths[index - 1] for index in _PHASE_B_SURFACE_INDICES)
    if (
        len(phase_a) != 28
        or len(phase_b) != 9
        or phase_a & phase_b
        or phase_a | phase_b != frozenset(paths)
    ):
        raise ExecutedFrozenIntegrityError("SURFACE_MAP_PHASE_PARTITION_INVALID")
    if phase == PHASE_A:
        return phase_a
    if phase == PHASE_B:
        return phase_b
    raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_PHASE_INVALID")


def verify_git_change_firewall(
    repo_root: Path,
    *,
    phase: str,
    base_commit: str,
    head_commit: str,
) -> GitFirewallVerification:
    """Validate committed and staged paths against one exact Surface-Map phase partition."""

    root = repo_root.resolve(strict=True)
    if _SHA1_PATTERN.fullmatch(base_commit) is None or _SHA1_PATTERN.fullmatch(head_commit) is None:
        raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_COMMIT_ID_INVALID")
    for commit in (base_commit, head_commit):
        if _run_git(root, "cat-file", "-t", commit).decode().strip() != "commit":
            raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_COMMIT_ID_INVALID")
    if _run_git(root, "rev-parse", "HEAD").decode().strip() != head_commit:
        raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_HEAD_MISMATCH")
    _run_git(
        root,
        "merge-base",
        "--is-ancestor",
        base_commit,
        head_commit,
        allowed_returncodes=(0,),
    )
    allowed = _surface_map_phase_paths(root, phase)
    changed_statuses = _parse_name_status(
        _run_git(
            root,
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            base_commit,
            head_commit,
        ),
        field="committed change",
    )
    staged_statuses = _parse_name_status(
        _run_git(root, "diff", "--cached", "--name-status", "-z", "--find-renames"),
        field="staged change",
    )

    changed: list[str] = []
    for status, paths in changed_statuses:
        kind = status[0]
        if kind in {"D", "R", "C"}:
            raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_DELETION_OR_RENAME_FORBIDDEN")
        if kind not in {"A", "M"} or len(paths) != 1:
            raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_STATUS_FORBIDDEN")
        path = paths[0]
        if path not in allowed:
            raise ExecutedFrozenIntegrityError(f"CHANGE_FIREWALL_OUT_OF_PHASE:{path}")
        changed.append(path)

    staged: list[str] = []
    for status, paths in staged_statuses:
        kind = status[0]
        if kind in {"D", "R", "C"}:
            raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_DELETION_OR_RENAME_FORBIDDEN")
        if kind not in {"A", "M"} or len(paths) != 1:
            raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_STATUS_FORBIDDEN")
        path = paths[0]
        if path not in allowed:
            raise ExecutedFrozenIntegrityError(f"CHANGE_FIREWALL_STAGED_OUT_OF_PHASE:{path}")
        staged.append(path)
    if staged:
        raise ExecutedFrozenIntegrityError("CHANGE_FIREWALL_STAGED_NOT_EMPTY")

    return GitFirewallVerification(
        phase=phase,
        base_commit=base_commit,
        head_commit=head_commit,
        changed_paths=tuple(sorted(changed, key=lambda value: value.encode("utf-8"))),
        staged_paths=(),
    )


def parse_executed_frozen_registry(payload: object) -> ExecutedFrozenRegistry:
    """Parse the closed registry without opening any authority-evidence artifact."""

    root = _closed_object(payload, _TOP_LEVEL_FIELDS, label="registry")
    if root["schema_version"] != REGISTRY_SCHEMA:
        raise ExecutedFrozenIntegrityError("registry schema mismatch")
    if root["registry_id"] != REGISTRY_ID:
        raise ExecutedFrozenIntegrityError("registry identity mismatch")
    if root["status"] != REGISTRY_STATUS:
        raise ExecutedFrozenIntegrityError("registry status mismatch")

    raw_entries = root["entries"]
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ExecutedFrozenIntegrityError("registry entries must be a non-empty list")

    entries: list[ExecutedFrozenEntry] = []
    seen_paths: set[str] = set()
    for index, raw_entry in enumerate(raw_entries):
        entry = _closed_object(raw_entry, _ENTRY_FIELDS, label=f"entry[{index}]")
        path = _validate_relative_checkout_path(entry["path"], field=f"entry[{index}].path")
        if path in seen_paths:
            raise ExecutedFrozenIntegrityError(f"duplicate registered path: {path}")
        if not _is_sha256(entry["authoritative_sha256"]):
            raise ExecutedFrozenIntegrityError(f"entry[{index}] SHA-256 is invalid")

        raw_evidence = entry["authority_evidence"]
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise ExecutedFrozenIntegrityError(f"entry[{index}] authority evidence is empty")
        evidence: list[AuthorityEvidenceIdentity] = []
        seen_roles: set[str] = set()
        seen_evidence_paths: set[str] = set()
        for evidence_index, raw_identity in enumerate(raw_evidence):
            identity = _closed_object(
                raw_identity,
                _EVIDENCE_FIELDS,
                label=f"entry[{index}].authority_evidence[{evidence_index}]",
            )
            role = identity["role"]
            if not isinstance(role, str) or not role or not role.isascii():
                raise ExecutedFrozenIntegrityError("authority-evidence role must be ASCII")
            evidence_path = _validate_relative_checkout_path(
                identity["path"],
                field=f"entry[{index}].authority_evidence[{evidence_index}].path",
            )
            if role in seen_roles or evidence_path in seen_evidence_paths:
                raise ExecutedFrozenIntegrityError("duplicate authority-evidence identity")
            if not _is_sha256(identity["sha256"]):
                raise ExecutedFrozenIntegrityError("authority-evidence SHA-256 is invalid")
            seen_roles.add(role)
            seen_evidence_paths.add(evidence_path)
            evidence.append(
                AuthorityEvidenceIdentity(
                    role=role,
                    path=evidence_path,
                    sha256=str(identity["sha256"]),
                )
            )

        seen_paths.add(path)
        entries.append(
            ExecutedFrozenEntry(
                path=path,
                authoritative_sha256=str(entry["authoritative_sha256"]),
                authority_evidence=tuple(evidence),
            )
        )

    if (
        entries[0].path != MANDATORY_FIRST_PATH
        or entries[0].authoritative_sha256 != MANDATORY_FIRST_SHA256
    ):
        raise ExecutedFrozenIntegrityError("mandatory first executed-frozen entry mismatch")

    return ExecutedFrozenRegistry(
        schema_version=str(root["schema_version"]),
        registry_id=str(root["registry_id"]),
        status=str(root["status"]),
        entries=tuple(entries),
    )


def load_executed_frozen_registry(
    repo_root: Path,
    registry_path: Path = REGISTRY_PATH,
) -> ExecutedFrozenRegistry:
    """Load only the checkout registry configuration from below ``repo_root``."""

    root = repo_root.resolve(strict=True)
    unresolved = root / registry_path
    if unresolved.is_symlink():
        raise ExecutedFrozenIntegrityError("registry path escapes checkout or is a symlink")
    candidate = unresolved.resolve(strict=True)
    if root not in candidate.parents:
        raise ExecutedFrozenIntegrityError("registry path escapes checkout or is a symlink")
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExecutedFrozenIntegrityError("registry is unreadable or invalid JSON") from exc
    return parse_executed_frozen_registry(payload)


def verify_executed_frozen_registry(
    repo_root: Path,
    registry_path: Path = REGISTRY_PATH,
) -> ExecutedFrozenVerification:
    """Hash registered documents without reading the bound authority-evidence artifacts."""

    root = repo_root.resolve(strict=True)
    registry = load_executed_frozen_registry(root, registry_path)
    checked: list[str] = []
    observed: list[str] = []
    for entry in registry.entries:
        unresolved = root / entry.path
        if unresolved.is_symlink():
            raise ExecutedFrozenIntegrityError(f"registered path is unsafe: {entry.path}")
        candidate = unresolved.resolve(strict=True)
        if root not in candidate.parents or not candidate.is_file():
            raise ExecutedFrozenIntegrityError(f"registered path is unsafe: {entry.path}")
        actual_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual_sha256 != entry.authoritative_sha256:
            raise ExecutedFrozenIntegrityError(
                f"executed-frozen byte drift: {entry.path}: "
                f"expected {entry.authoritative_sha256}, observed {actual_sha256}"
            )
        checked.append(entry.path)
        observed.append(actual_sha256)

    return ExecutedFrozenVerification(
        registry_id=registry.registry_id,
        checked_paths=tuple(checked),
        observed_sha256=tuple(observed),
    )

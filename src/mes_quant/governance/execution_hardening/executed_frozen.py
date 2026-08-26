"""Checkout-safe integrity verification for executed-frozen documents."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

REGISTRY_PATH = Path("configs/governance/executed_frozen_registry_v1.json")
REGISTRY_SCHEMA = "MES_EXECUTED_FROZEN_REGISTRY_SCHEMA_V1"
REGISTRY_ID = "EXECUTED_FROZEN_BYTE_INTEGRITY_V1"
REGISTRY_STATUS = "OWNER_AUTHORIZED_PHASE_A_CHECKOUT_INTEGRITY"

MANDATORY_FIRST_PATH = "docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md"
MANDATORY_FIRST_SHA256 = "7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105"

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_TOP_LEVEL_FIELDS = frozenset({"schema_version", "registry_id", "status", "entries"})
_ENTRY_FIELDS = frozenset({"path", "authoritative_sha256", "authority_evidence"})
_EVIDENCE_FIELDS = frozenset({"role", "path", "sha256"})


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


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


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

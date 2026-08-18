from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

_MANIFEST_PATH = Path("configs/governance/PROTECTED_SURFACE_MANIFEST_V1.json")
_LIMITS_PATH = Path("configs/governance/ANALYZER_LIMITS_V1.json")
_RECORD_SCHEMA_PATH = Path("configs/governance/CLASSIFICATION_RECORD_SCHEMA_V1.json")

EXPECTED_SHA256 = {
    _MANIFEST_PATH: "5B958ACEB8466E76C292C65558121E32899E902640CEABF96D2047A0AED031C3",
    _LIMITS_PATH: "0C3E67C7C03294C70755F37263C245A1A0512B1D85D0D66EA5018995A7FF5DB2",
    _RECORD_SCHEMA_PATH: "34A80E3731F60BCC809A204CA280A73E67F55D44535BC28A68672B171BF14BA9",
}


class FrozenInputError(RuntimeError):
    """Raised when a frozen governance control input is missing or identity-invalid."""


@dataclass(frozen=True)
class FrozenInputs:
    protected_surface_manifest: dict[str, Any]
    analyzer_limits: dict[str, Any]
    classification_record_schema: dict[str, Any]
    protected_surface_manifest_sha256: str
    analyzer_limits_sha256: str
    classification_record_schema_sha256: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FrozenInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_exact_json(repo_root: Path, relative_path: Path) -> tuple[dict[str, Any], str]:
    path = repo_root / relative_path
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise FrozenInputError(f"cannot read frozen input: {relative_path}") from exc

    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise FrozenInputError(f"byte policy failure: {relative_path}")

    actual_sha256 = hashlib.sha256(data).hexdigest().upper()
    expected_sha256 = EXPECTED_SHA256[relative_path]
    if actual_sha256 != expected_sha256:
        raise FrozenInputError(
            f"frozen input SHA-256 mismatch for {relative_path}: "
            f"{actual_sha256} != {expected_sha256}"
        )

    try:
        payload = json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrozenInputError(f"invalid frozen JSON: {relative_path}") from exc
    if not isinstance(payload, dict):
        raise FrozenInputError(f"frozen JSON root must be object: {relative_path}")
    return payload, actual_sha256


def load_frozen_inputs(repo_root: str | Path) -> FrozenInputs:
    root = Path(repo_root)
    manifest, manifest_sha = _load_exact_json(root, _MANIFEST_PATH)
    limits, limits_sha = _load_exact_json(root, _LIMITS_PATH)
    record_schema, record_schema_sha = _load_exact_json(root, _RECORD_SCHEMA_PATH)

    if manifest.get("schema") != "PROTECTED_SURFACE_MANIFEST_V1":
        raise FrozenInputError("protected-surface manifest schema identity mismatch")
    if limits.get("schema") != "ANALYZER_LIMITS_V1":
        raise FrozenInputError("analyzer-limits schema identity mismatch")
    if record_schema.get("$id") != "MES_CLASSIFICATION_RECORD_SCHEMA_V1":
        raise FrozenInputError("classification-record schema identity mismatch")

    return FrozenInputs(
        protected_surface_manifest=manifest,
        analyzer_limits=limits,
        classification_record_schema=record_schema,
        protected_surface_manifest_sha256=manifest_sha,
        analyzer_limits_sha256=limits_sha,
        classification_record_schema_sha256=record_schema_sha,
    )

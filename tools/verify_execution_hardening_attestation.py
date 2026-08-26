from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

READY_SCHEMA = "MES_EXECUTION_HARDENING_ATTESTATION_READY_V1"
READY_STATUS = "PHASE_B_ACTIVATION_PREREQUISITES_READY"
SHA1_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ActivationReadiness:
    ready: bool
    reason_code: str
    sentinel_path: str
    trusted_root_path: str
    trusted_root_sha256: str
    activation_commit: str
    activation_tree: str
    source_ref: str
    sentinel_present: bool
    sentinel_schema_valid: bool
    trusted_root_present: bool
    trusted_root_hash_valid: bool
    activation_binding_valid: bool
    source_ref_valid: bool
    network_used: bool = False
    oidc_minted: bool = False
    signing_invoked: bool = False
    attestation_accepted: bool = False
    authority_granted: bool = False

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def _json_without_duplicate_keys(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key, value in pairs:
            if key in payload:
                raise ValueError(f"DUPLICATE_JSON_KEY:{key}")
            payload[key] = value
        return payload

    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(payload, dict):
        raise TypeError("READY_SENTINEL_MUST_BE_JSON_OBJECT")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate_activation_readiness(
    *,
    sentinel_path: Path,
    trusted_root_path: Path,
    trusted_root_sha256: str,
    activation_commit: str,
    activation_tree: str,
    source_ref: str,
) -> ActivationReadiness:
    """Check local Phase-B prerequisites without accepting trust or granting authority."""

    common = {
        "sentinel_path": sentinel_path.as_posix(),
        "trusted_root_path": trusted_root_path.as_posix(),
        "trusted_root_sha256": trusted_root_sha256,
        "activation_commit": activation_commit,
        "activation_tree": activation_tree,
        "source_ref": source_ref,
    }
    if not sentinel_path.is_file():
        return ActivationReadiness(
            ready=False,
            reason_code="ATTESTATION_READY_SENTINEL_MISSING_PHASE_A",
            sentinel_present=False,
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **common,
        )
    try:
        sentinel = _json_without_duplicate_keys(sentinel_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ActivationReadiness(
            ready=False,
            reason_code="ATTESTATION_READY_SENTINEL_INVALID",
            sentinel_present=True,
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **common,
        )

    sentinel_schema_valid = (
        sentinel.get("schema_version") == READY_SCHEMA
        and sentinel.get("status") == READY_STATUS
        and sentinel.get("phase") == "PHASE_B"
        and sentinel.get("ready") is True
    )
    trusted_root_present = trusted_root_path.is_file()
    expected_hash_valid = SHA256_PATTERN.fullmatch(trusted_root_sha256) is not None
    trusted_root_hash_valid = (
        trusted_root_present
        and expected_hash_valid
        and _sha256(trusted_root_path) == trusted_root_sha256
        and sentinel.get("trusted_root_path") == trusted_root_path.as_posix()
        and sentinel.get("trusted_root_sha256") == trusted_root_sha256
    )
    activation_binding_valid = (
        SHA1_PATTERN.fullmatch(activation_commit) is not None
        and SHA1_PATTERN.fullmatch(activation_tree) is not None
        and sentinel.get("activation_commit") == activation_commit
        and sentinel.get("activation_tree") == activation_tree
    )
    source_ref_valid = (
        source_ref == "refs/heads/main" and sentinel.get("source_ref") == source_ref
    )
    checks = (
        sentinel_schema_valid,
        trusted_root_hash_valid,
        activation_binding_valid,
        source_ref_valid,
    )
    ready = all(checks)
    if ready:
        reason_code = "PHASE_B_ACTIVATION_PREREQUISITES_SATISFIED_NO_AUTHORITY_GRANTED"
    elif not sentinel_schema_valid:
        reason_code = "ATTESTATION_READY_SENTINEL_INVALID"
    elif not trusted_root_hash_valid:
        reason_code = "ATTESTATION_TRUSTED_ROOT_BINDING_MISMATCH"
    elif not activation_binding_valid:
        reason_code = "ATTESTATION_ACTIVATION_BINDING_MISMATCH"
    else:
        reason_code = "ATTESTATION_SOURCE_REF_MISMATCH"
    return ActivationReadiness(
        ready=ready,
        reason_code=reason_code,
        sentinel_present=True,
        sentinel_schema_valid=sentinel_schema_valid,
        trusted_root_present=trusted_root_present,
        trusted_root_hash_valid=trusted_root_hash_valid,
        activation_binding_valid=activation_binding_valid,
        source_ref_valid=source_ref_valid,
        **common,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check local activation readiness without OIDC, network, signing, or trust."
    )
    parser.add_argument("--ready-sentinel", type=Path, required=True)
    parser.add_argument("--trusted-root", type=Path, required=True)
    parser.add_argument("--trusted-root-sha256", required=True)
    parser.add_argument("--activation-commit", required=True)
    parser.add_argument("--activation-tree", required=True)
    parser.add_argument("--source-ref", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = evaluate_activation_readiness(
        sentinel_path=args.ready_sentinel,
        trusted_root_path=args.trusted_root,
        trusted_root_sha256=args.trusted_root_sha256,
        activation_commit=args.activation_commit,
        activation_tree=args.activation_tree,
        source_ref=args.source_ref,
    )
    print(json.dumps(result.to_mapping(), separators=(",", ":"), sort_keys=True))
    return 0 if result.ready else 3


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

READY_SCHEMA = "MES_EXECUTION_HARDENING_ATTESTATION_READY_V1"
READY_STATUS = "PHASE_B_ACTIVATION_PREREQUISITES_READY"
DECISION_C_AUTHORIZATION_RELATIVE_PATH = Path(
    "docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_OWNER_ACTIVATION_V1.md"
)
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
    checkout_commit: str | None
    checkout_tree: str | None
    checkout_source_ref: str | None
    checkout_binding_valid: bool
    decision_c_authorization_path: str
    decision_c_authorization_sha256: str
    decision_c_authorization_present: bool
    decision_c_authorization_safe_regular_file: bool
    decision_c_authorization_hash_valid: bool
    decision_c_authorization_binding_valid: bool
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


def _resolve_safe_regular_file(
    repository_root: Path,
    relative_path: Path,
) -> tuple[bool, bool, Path | None]:
    """Resolve a fixed checkout path while rejecting every symlink component."""

    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        return False, False, None
    if not root.is_dir() or relative_path.is_absolute() or ".." in relative_path.parts:
        return False, False, None

    candidate = root
    for index, part in enumerate(relative_path.parts):
        candidate = candidate / part
        try:
            mode = candidate.lstat().st_mode
        except OSError:
            return False, False, None
        if stat.S_ISLNK(mode):
            return True, False, None
        is_last = index == len(relative_path.parts) - 1
        if (is_last and not stat.S_ISREG(mode)) or (not is_last and not stat.S_ISDIR(mode)):
            return True, False, None

    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return True, False, None
    if root not in resolved.parents or not resolved.is_file():
        return True, False, None
    return True, True, resolved


def _checkout_identity(repository_root: Path) -> tuple[str | None, str | None]:
    """Read the checked-out commit/tree with fixed, non-mutating Git arguments.

    GitHub Actions checks out an exact commit in detached-HEAD mode, so a symbolic branch name is
    not a property of the checkout.  The workflow's event/ref predicate supplies the independent
    ``refs/heads/main`` gate; this helper binds the actual bytes through commit and tree.
    """

    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        return None, None
    commands = (
        ("rev-parse", "HEAD"),
        ("rev-parse", "HEAD^{tree}"),
    )
    values: list[str] = []
    for command in commands:
        try:
            completed = subprocess.run(
                ("git", "-C", str(root), *command),
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None, None
        value = completed.stdout.strip()
        if not value or "\n" in value or "\r" in value:
            return None, None
        values.append(value)
    return values[0], values[1]


def evaluate_activation_readiness(
    *,
    repository_root: Path,
    sentinel_path: Path,
    trusted_root_path: Path,
    trusted_root_sha256: str,
    activation_commit: str,
    activation_tree: str,
    source_ref: str,
    decision_c_authorization_sha256: str,
) -> ActivationReadiness:
    """Check local Phase-B prerequisites without accepting trust or granting authority."""

    checkout_commit, checkout_tree = _checkout_identity(repository_root)
    activation_binding_valid = (
        SHA1_PATTERN.fullmatch(activation_commit) is not None
        and SHA1_PATTERN.fullmatch(activation_tree) is not None
    )
    checkout_binding_valid = (
        checkout_commit == activation_commit
        and checkout_tree == activation_tree
        and activation_binding_valid
    )
    common = {
        "sentinel_path": sentinel_path.as_posix(),
        "trusted_root_path": trusted_root_path.as_posix(),
        "trusted_root_sha256": trusted_root_sha256,
        "activation_commit": activation_commit,
        "activation_tree": activation_tree,
        "source_ref": source_ref,
        "checkout_commit": checkout_commit,
        "checkout_tree": checkout_tree,
        "checkout_source_ref": None,
        "checkout_binding_valid": checkout_binding_valid,
        "decision_c_authorization_path": (
            DECISION_C_AUTHORIZATION_RELATIVE_PATH.as_posix()
        ),
        "decision_c_authorization_sha256": decision_c_authorization_sha256,
    }
    (
        decision_c_present,
        decision_c_safe_regular_file,
        decision_c_path,
    ) = _resolve_safe_regular_file(
        repository_root,
        DECISION_C_AUTHORIZATION_RELATIVE_PATH,
    )
    decision_c_common = {
        "decision_c_authorization_present": decision_c_present,
        "decision_c_authorization_safe_regular_file": decision_c_safe_regular_file,
    }
    if not decision_c_present:
        return ActivationReadiness(
            ready=False,
            reason_code="DECISION_C_AUTHORIZATION_MISSING",
            decision_c_authorization_hash_valid=False,
            decision_c_authorization_binding_valid=False,
            sentinel_present=sentinel_path.is_file(),
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **decision_c_common,
            **common,
        )
    if not decision_c_safe_regular_file or decision_c_path is None:
        return ActivationReadiness(
            ready=False,
            reason_code="DECISION_C_AUTHORIZATION_UNSAFE",
            decision_c_authorization_hash_valid=False,
            decision_c_authorization_binding_valid=False,
            sentinel_present=sentinel_path.is_file(),
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **decision_c_common,
            **common,
        )
    decision_c_hash_valid = (
        SHA256_PATTERN.fullmatch(decision_c_authorization_sha256) is not None
        and _sha256(decision_c_path) == decision_c_authorization_sha256
    )
    if not decision_c_hash_valid:
        return ActivationReadiness(
            ready=False,
            reason_code="DECISION_C_AUTHORIZATION_SHA256_MISMATCH",
            decision_c_authorization_hash_valid=False,
            decision_c_authorization_binding_valid=False,
            sentinel_present=sentinel_path.is_file(),
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **decision_c_common,
            **common,
        )
    if not sentinel_path.is_file():
        return ActivationReadiness(
            ready=False,
            reason_code="ATTESTATION_READY_SENTINEL_MISSING_PHASE_A",
            decision_c_authorization_hash_valid=True,
            decision_c_authorization_binding_valid=False,
            sentinel_present=False,
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **decision_c_common,
            **common,
        )
    try:
        sentinel = _json_without_duplicate_keys(sentinel_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ActivationReadiness(
            ready=False,
            reason_code="ATTESTATION_READY_SENTINEL_INVALID",
            decision_c_authorization_hash_valid=True,
            decision_c_authorization_binding_valid=False,
            sentinel_present=True,
            sentinel_schema_valid=False,
            trusted_root_present=trusted_root_path.is_file(),
            trusted_root_hash_valid=False,
            activation_binding_valid=False,
            source_ref_valid=False,
            **decision_c_common,
            **common,
        )

    sentinel_schema_valid = (
        sentinel.get("schema_version") == READY_SCHEMA
        and sentinel.get("status") == READY_STATUS
        and sentinel.get("phase") == "PHASE_B"
        and sentinel.get("ready") is True
    )
    decision_c_binding_valid = (
        sentinel.get("decision_c_authorization_path")
        == DECISION_C_AUTHORIZATION_RELATIVE_PATH.as_posix()
        and sentinel.get("decision_c_authorization_sha256")
        == decision_c_authorization_sha256
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
    source_ref_valid = (
        source_ref == "refs/heads/main"
        and sentinel.get("source_ref") == source_ref
    )
    checks = (
        decision_c_binding_valid,
        sentinel_schema_valid,
        trusted_root_hash_valid,
        activation_binding_valid,
        checkout_binding_valid,
        source_ref_valid,
    )
    ready = all(checks)
    if ready:
        reason_code = "PHASE_B_ACTIVATION_PREREQUISITES_SATISFIED_NO_AUTHORITY_GRANTED"
    elif not decision_c_binding_valid:
        reason_code = "DECISION_C_AUTHORIZATION_BINDING_MISMATCH"
    elif not sentinel_schema_valid:
        reason_code = "ATTESTATION_READY_SENTINEL_INVALID"
    elif not trusted_root_hash_valid:
        reason_code = "ATTESTATION_TRUSTED_ROOT_BINDING_MISMATCH"
    elif not activation_binding_valid:
        reason_code = "ATTESTATION_ACTIVATION_BINDING_MISMATCH"
    elif not checkout_binding_valid:
        reason_code = "ATTESTATION_CHECKOUT_BINDING_MISMATCH"
    else:
        reason_code = "ATTESTATION_SOURCE_REF_MISMATCH"
    return ActivationReadiness(
        ready=ready,
        reason_code=reason_code,
        decision_c_authorization_hash_valid=True,
        decision_c_authorization_binding_valid=decision_c_binding_valid,
        sentinel_present=True,
        sentinel_schema_valid=sentinel_schema_valid,
        trusted_root_present=trusted_root_present,
        trusted_root_hash_valid=trusted_root_hash_valid,
        activation_binding_valid=activation_binding_valid,
        source_ref_valid=source_ref_valid,
        **decision_c_common,
        **common,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check local activation readiness without OIDC, network, signing, or trust."
    )
    parser.add_argument("--ready-sentinel", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--trusted-root", type=Path, required=True)
    parser.add_argument("--trusted-root-sha256", required=True)
    parser.add_argument("--decision-c-authorization-sha256", required=True)
    parser.add_argument("--activation-commit", required=True)
    parser.add_argument("--activation-tree", required=True)
    parser.add_argument("--source-ref", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = evaluate_activation_readiness(
        repository_root=args.repository_root,
        sentinel_path=args.ready_sentinel,
        trusted_root_path=args.trusted_root,
        trusted_root_sha256=args.trusted_root_sha256,
        activation_commit=args.activation_commit,
        activation_tree=args.activation_tree,
        source_ref=args.source_ref,
        decision_c_authorization_sha256=args.decision_c_authorization_sha256,
    )
    print(json.dumps(result.to_mapping(), separators=(",", ":"), sort_keys=True))
    return 0 if result.ready else 3


if __name__ == "__main__":
    raise SystemExit(main())

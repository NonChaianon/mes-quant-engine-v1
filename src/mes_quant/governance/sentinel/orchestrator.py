from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from mes_quant.governance.classification.frozen_inputs import (
    FrozenInputError,
    load_frozen_inputs,
)
from mes_quant.governance.classification.git_delta import (
    DeltaEntry,
    GitDeltaError,
    canonical_git_tree_delta,
)
from mes_quant.governance.classification.relation import (
    CandidateRelation,
    CandidateRelationError,
    validate_candidate_relation,
)

from .manifest_guard import (
    ManifestGuardError,
    ManifestGuardResult,
    detect_manifest_weakening,
)
from .sentinel import (
    GovernanceSentinelError,
    GovernanceSentinelResult,
    evaluate_governance_paths,
)


class GovernanceSentinelOrchestrationError(RuntimeError):
    """Raised when trusted Git-object Sentinel evaluation cannot complete."""


@dataclass(frozen=True)
class GovernanceSentinelRun:
    """Deterministic Phase-A pre-classification Sentinel result."""

    relation: CandidateRelation
    canonical_tree_delta: tuple[DeltaEntry, ...]
    sentinel_result: GovernanceSentinelResult
    manifest_guard_result: ManifestGuardResult | None


_MANIFEST_PATH = (
    b"configs/governance/"
    b"PROTECTED_SURFACE_MANIFEST_V1.json"
)


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


def _git_argv(
    repo: str | Path,
    *args: str,
) -> list[str]:
    return [
        "git",
        "--no-replace-objects",
        "-C",
        str(repo),
        *args,
    ]


def _positive_limit(
    limits: dict[str, Any],
    name: str,
) -> int:
    value = limits.get(name)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise GovernanceSentinelOrchestrationError(
            f"invalid governed analyzer limit: {name}"
        )

    return value


def _changed_paths(
    delta: tuple[DeltaEntry, ...],
) -> tuple[bytes, ...]:
    paths: set[bytes] = set()

    for entry in delta:
        if entry.old_path_bytes is not None:
            paths.add(entry.old_path_bytes)

        if entry.new_path_bytes is not None:
            paths.add(entry.new_path_bytes)

    if not paths:
        raise GovernanceSentinelOrchestrationError(
            "candidate tree delta contains no changed paths"
        )

    return tuple(sorted(paths))


def _manifest_delta_entry(
    delta: tuple[DeltaEntry, ...],
) -> DeltaEntry | None:
    matches = tuple(
        entry
        for entry in delta
        if (
            entry.old_path_bytes == _MANIFEST_PATH
            or entry.new_path_bytes == _MANIFEST_PATH
        )
    )

    if not matches:
        return None

    if len(matches) != 1:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest has ambiguous tree-delta identity"
        )

    return matches[0]


def _read_blob_bounded(
    repo: str | Path,
    blob_sha1: str,
    *,
    max_blob_bytes: int,
) -> bytes:
    try:
        size_result = subprocess.run(
            _git_argv(
                repo,
                "cat-file",
                "-s",
                blob_sha1,
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_env(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GovernanceSentinelOrchestrationError(
            "cannot establish candidate manifest blob size"
        ) from exc

    raw_size = size_result.stdout.strip()

    try:
        size = int(raw_size)
    except ValueError as exc:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest blob size is invalid"
        ) from exc

    if size < 0 or size > max_blob_bytes:
        raise GovernanceSentinelOrchestrationError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_blob_bytes={max_blob_bytes}"
        )

    try:
        blob_result = subprocess.run(
            _git_argv(
                repo,
                "cat-file",
                "blob",
                blob_sha1,
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GovernanceSentinelOrchestrationError(
            "cannot read candidate manifest Git blob"
        ) from exc

    data = blob_result.stdout

    if len(data) != size:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest blob size changed during read"
        )

    return data


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise GovernanceSentinelOrchestrationError(
                f"duplicate candidate manifest JSON key: {key}"
            )

        result[key] = value

    return result


def _validate_json_limits(
    value: Any,
    *,
    max_depth: int,
    max_scalar_bytes: int,
    max_collection_cardinality: int,
    depth: int = 0,
) -> None:
    if depth > max_depth:
        raise GovernanceSentinelOrchestrationError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_config_nesting_depth={max_depth}"
        )

    if isinstance(value, dict):
        if len(value) > max_collection_cardinality:
            raise GovernanceSentinelOrchestrationError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                "max_collection_cardinality="
                f"{max_collection_cardinality}"
            )

        for key, child in value.items():
            if not isinstance(key, str):
                raise GovernanceSentinelOrchestrationError(
                    "candidate manifest object keys must be strings"
                )

            if (
                len(key.encode("utf-8"))
                > max_scalar_bytes
            ):
                raise GovernanceSentinelOrchestrationError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    f"max_scalar_bytes={max_scalar_bytes}"
                )

            _validate_json_limits(
                child,
                max_depth=max_depth,
                max_scalar_bytes=max_scalar_bytes,
                max_collection_cardinality=(
                    max_collection_cardinality
                ),
                depth=depth + 1,
            )

        return

    if isinstance(value, list):
        if len(value) > max_collection_cardinality:
            raise GovernanceSentinelOrchestrationError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                "max_collection_cardinality="
                f"{max_collection_cardinality}"
            )

        for child in value:
            _validate_json_limits(
                child,
                max_depth=max_depth,
                max_scalar_bytes=max_scalar_bytes,
                max_collection_cardinality=(
                    max_collection_cardinality
                ),
                depth=depth + 1,
            )

        return

    if isinstance(value, str):
        if (
            len(value.encode("utf-8"))
            > max_scalar_bytes
        ):
            raise GovernanceSentinelOrchestrationError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_scalar_bytes={max_scalar_bytes}"
            )

        return

    if value is None or isinstance(value, bool):
        return

    if isinstance(value, int) and not isinstance(value, bool):
        return

    raise GovernanceSentinelOrchestrationError(
        "candidate manifest contains unsupported JSON scalar"
    )


def _parse_candidate_manifest(
    data: bytes,
    *,
    limits: dict[str, Any],
) -> dict[str, Any]:
    if (
        data.startswith(b"\xef\xbb\xbf")
        or b"\r" in data
        or not data.endswith(b"\n")
    ):
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest byte-policy failure"
        )

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest is not UTF-8"
        ) from exc

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        json.JSONDecodeError,
        RecursionError,
    ) as exc:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest JSON parse failure"
        ) from exc

    if not isinstance(payload, dict):
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest root must be an object"
        )

    _validate_json_limits(
        payload,
        max_depth=_positive_limit(
            limits,
            "max_config_nesting_depth",
        ),
        max_scalar_bytes=_positive_limit(
            limits,
            "max_scalar_bytes",
        ),
        max_collection_cardinality=_positive_limit(
            limits,
            "max_collection_cardinality",
        ),
    )

    try:
        canonical = (
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("ascii")
            + b"\n"
        )
    except (TypeError, UnicodeEncodeError) as exc:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest canonicalization failure"
        ) from exc

    if canonical != data:
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest is not canonical V1 JSON"
        )

    return payload


def _candidate_manifest(
    repo: str | Path,
    entry: DeltaEntry,
    *,
    limits: dict[str, Any],
) -> dict[str, Any]:
    if entry.operation == "DELETE":
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest deletion is prohibited"
        )

    if (
        entry.new_blob_sha1 is None
        or entry.new_mode != "100644"
        or entry.new_object_type != "blob"
    ):
        raise GovernanceSentinelOrchestrationError(
            "candidate manifest must be a regular 100644 Git blob"
        )

    data = _read_blob_bounded(
        repo,
        entry.new_blob_sha1,
        max_blob_bytes=_positive_limit(
            limits,
            "max_blob_bytes",
        ),
    )

    return _parse_candidate_manifest(
        data,
        limits=limits,
    )


def run_governance_sentinel(
    repo: str | Path,
    *,
    authority_commit_sha1: str,
    base_commit_sha1: str,
    head_commit_sha1: str,
) -> GovernanceSentinelRun:
    """Run pre-classification governance interception from Git objects.

    Hard boundaries:

    - predecessor/base authority only;
    - candidate bytes read from immutable Git blobs;
    - no candidate checkout;
    - no candidate execution/import;
    - no network;
    - no repository or remote mutation;
    - no merge authorization.
    """

    if authority_commit_sha1 != base_commit_sha1:
        raise GovernanceSentinelOrchestrationError(
            "V1 predecessor authority must equal candidate base"
        )

    try:
        relation = validate_candidate_relation(
            repo,
            base_commit_sha1=base_commit_sha1,
            head_commit_sha1=head_commit_sha1,
        )

        if (
            relation.base_commit_sha1
            != authority_commit_sha1
        ):
            raise GovernanceSentinelOrchestrationError(
                "resolved candidate base disagrees "
                "with predecessor authority"
            )

        frozen = load_frozen_inputs(
            repo,
            authority_commit_sha1=authority_commit_sha1,
        )

        max_tree_delta_entries = _positive_limit(
            frozen.analyzer_limits,
            "max_tree_delta_entries",
        )

        delta = canonical_git_tree_delta(
            repo,
            base_commit_sha1=relation.base_commit_sha1,
            head_commit_sha1=relation.head_commit_sha1,
            max_tree_delta_entries=max_tree_delta_entries,
        )

        paths = _changed_paths(delta)

        sentinel_result = evaluate_governance_paths(
            paths,
            frozen.protected_surface_manifest,
        )

        manifest_entry = _manifest_delta_entry(
            delta
        )

        manifest_guard_result: (
            ManifestGuardResult | None
        ) = None

        if manifest_entry is not None:
            candidate_manifest = _candidate_manifest(
                repo,
                manifest_entry,
                limits=frozen.analyzer_limits,
            )

            manifest_guard_result = (
                detect_manifest_weakening(
                    frozen.protected_surface_manifest,
                    candidate_manifest,
                )
            )

    except GovernanceSentinelOrchestrationError:
        raise
    except (
        CandidateRelationError,
        FrozenInputError,
        GitDeltaError,
        GovernanceSentinelError,
        ManifestGuardError,
    ) as exc:
        raise GovernanceSentinelOrchestrationError(
            "governance Sentinel orchestration failed closed"
        ) from exc

    return GovernanceSentinelRun(
        relation=relation,
        canonical_tree_delta=delta,
        sentinel_result=sentinel_result,
        manifest_guard_result=manifest_guard_result,
    )

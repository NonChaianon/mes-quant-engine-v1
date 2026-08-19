from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable

from .classification_decision import (
    ClassificationDecision,
    derive_classification_decision,
)
from .frozen_inputs import (
    FrozenInputs,
    load_frozen_inputs,
)
from .git_delta import (
    DeltaEntry,
    canonical_git_tree_delta,
)
from .path_classification import (
    PathClassification,
    classify_paths,
)
from .record import (
    canonical_record_bytes as serialize_canonical_record,
)
from .record_builder import build_classification_record
from .reference_candidate import (
    ReferenceCandidateAnalysis,
    analyze_reference_candidate,
)
from .relation import (
    CandidateRelation,
    validate_candidate_relation,
)

_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
_TOOLCHAIN_DIGEST_RE = re.compile(
    r"^sha256:[0-9a-f]{64}$"
)


class ClassifierOrchestrationError(RuntimeError):
    """Raised when trusted end-to-end classification cannot complete."""


@dataclass(frozen=True)
class TrustedAnalyzerIdentities:
    """Governed identities supplied by the trusted runtime boundary.

    At SPEC_FREEZE these identities are not yet activated as merge
    authority. This object only binds them into an observe/report result.
    """

    classifier_implementation_sha256: str
    analyzer_config_sha256: str
    analyzer_toolchain_digest: str


@dataclass(frozen=True)
class ClassifierRun:
    """Complete in-memory observe/report-only classifier result."""

    relation: CandidateRelation
    frozen_inputs: FrozenInputs
    canonical_tree_delta: tuple[DeltaEntry, ...]
    path_classification: PathClassification
    reference_analysis: ReferenceCandidateAnalysis
    decision: ClassificationDecision
    record: dict[str, Any]
    canonical_record_bytes: bytes


def _validate_trusted_identities(
    identities: TrustedAnalyzerIdentities,
) -> None:
    if not isinstance(
        identities,
        TrustedAnalyzerIdentities,
    ):
        raise ClassifierOrchestrationError(
            "trusted identities must use TrustedAnalyzerIdentities"
        )

    for value, name in (
        (
            identities.classifier_implementation_sha256,
            "classifier_implementation_sha256",
        ),
        (
            identities.analyzer_config_sha256,
            "analyzer_config_sha256",
        ),
    ):
        if (
            not isinstance(value, str)
            or _SHA256_RE.fullmatch(value) is None
        ):
            raise ClassifierOrchestrationError(
                f"{name} must be uppercase 64-hex SHA-256"
            )

    if (
        not isinstance(
            identities.analyzer_toolchain_digest,
            str,
        )
        or _TOOLCHAIN_DIGEST_RE.fullmatch(
            identities.analyzer_toolchain_digest
        )
        is None
    ):
        raise ClassifierOrchestrationError(
            "analyzer_toolchain_digest must be "
            "sha256:<lowercase-64-hex>"
        )


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
        raise ClassifierOrchestrationError(
            f"invalid governed analyzer limit: {name}"
        )

    return value


def _changed_paths(
    delta: Iterable[DeltaEntry],
) -> tuple[bytes, ...]:
    paths: set[bytes] = set()

    for entry in delta:
        if entry.old_path_bytes is not None:
            paths.add(entry.old_path_bytes)

        if entry.new_path_bytes is not None:
            paths.add(entry.new_path_bytes)

    if not paths:
        raise ClassifierOrchestrationError(
            "candidate tree delta contains no changed paths"
        )

    return tuple(sorted(paths))


def classify_candidate(
    repo: str | Path,
    *,
    authority_commit_sha1: str,
    base_commit_sha1: str,
    head_commit_sha1: str,
    trusted_identities: TrustedAnalyzerIdentities,
) -> ClassifierRun:
    """Run the complete classifier without persistence or mutation.

    Candidate content is consumed only through the underlying immutable
    Git-object readers. This function does not:

    - execute or import candidate code;
    - write evidence or other files;
    - mutate Git refs or repository state;
    - access the network;
    - approve or perform a merge;
    - activate enforcement or Integration Actor authority.
    """

    _validate_trusted_identities(
        trusted_identities
    )

    relation = validate_candidate_relation(
        repo,
        base_commit_sha1=base_commit_sha1,
        head_commit_sha1=head_commit_sha1,
    )

    if authority_commit_sha1 != relation.base_commit_sha1:
        raise ClassifierOrchestrationError(
            "V1 frozen-input authority commit must equal candidate base"
        )

    frozen = load_frozen_inputs(
        repo,
        authority_commit_sha1=authority_commit_sha1,
    )

    if (
        frozen.authority_commit_sha1
        != relation.base_commit_sha1
    ):
        raise ClassifierOrchestrationError(
            "resolved frozen-input authority does not equal candidate base"
        )

    max_tree_delta_entries = _positive_limit(
        frozen.analyzer_limits,
        "max_tree_delta_entries",
    )

    max_record_bytes = _positive_limit(
        frozen.analyzer_limits,
        "max_record_bytes",
    )

    delta = canonical_git_tree_delta(
        repo,
        base_commit_sha1=relation.base_commit_sha1,
        head_commit_sha1=relation.head_commit_sha1,
        max_tree_delta_entries=max_tree_delta_entries,
    )

    changed_paths = _changed_paths(delta)

    path_result = classify_paths(
        changed_paths,
        frozen.protected_surface_manifest,
    )

    reference_result = analyze_reference_candidate(
        repo,
        base_commit_sha1=relation.base_commit_sha1,
        head_commit_sha1=relation.head_commit_sha1,
        canonical_tree_delta=delta,
        manifest=frozen.protected_surface_manifest,
        limits=frozen.analyzer_limits,
    )

    decision = derive_classification_decision(
        path_result,
        reference_result.combined,
    )

    record = build_classification_record(
        base_commit_sha1=relation.base_commit_sha1,
        head_commit_sha1=relation.head_commit_sha1,
        merge_base_sha1=relation.merge_base_sha1,
        base_tree_sha1=relation.base_tree_sha1,
        head_tree_sha1=relation.head_tree_sha1,
        canonical_tree_delta=delta,
        classifier_spec_sha256=(
            frozen.classifier_spec_sha256
        ),
        classifier_implementation_sha256=(
            trusted_identities
            .classifier_implementation_sha256
        ),
        protected_surface_manifest_sha256=(
            frozen.protected_surface_manifest_sha256
        ),
        classification_record_schema_sha256=(
            frozen.classification_record_schema_sha256
        ),
        analyzer_config_sha256=(
            trusted_identities.analyzer_config_sha256
        ),
        analyzer_toolchain_digest=(
            trusted_identities.analyzer_toolchain_digest
        ),
        analyzer_limits_sha256=(
            frozen.analyzer_limits_sha256
        ),
        decision=decision,
        reference_analysis=reference_result.combined,
        schema=frozen.classification_record_schema,
    )

    encoded = serialize_canonical_record(
        record,
        schema=frozen.classification_record_schema,
        max_record_bytes=max_record_bytes,
    )

    return ClassifierRun(
        relation=relation,
        frozen_inputs=frozen,
        canonical_tree_delta=delta,
        path_classification=path_result,
        reference_analysis=reference_result,
        decision=decision,
        record=record,
        canonical_record_bytes=encoded,
    )

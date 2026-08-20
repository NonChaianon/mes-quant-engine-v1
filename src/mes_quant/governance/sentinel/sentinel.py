from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .manifest_guard import (
    ManifestGuardError,
    ManifestGuardResult,
    validate_predecessor_manifest,
)


class GovernanceSentinelError(RuntimeError):
    """Raised when governance safety evaluation cannot complete safely."""


@dataclass(frozen=True)
class GovernanceFacts:
    """Immutable governance evidence for the classification decision layer."""

    bootstrap_surface_hit: bool
    manifest_weakening_detected: bool
    weakening_details: tuple[str, ...]


_BOOTSTRAP_GOVERNANCE_IMPLEMENTATION_PREFIX = (
    b"src/mes_quant/governance/"
)


def _validated_paths(
    changed_paths: Iterable[bytes],
) -> tuple[bytes, ...]:
    try:
        values = tuple(
            changed_paths
        )
    except TypeError as exc:
        raise GovernanceSentinelError(
            "changed_paths must be iterable"
        ) from exc

    if not values:
        raise GovernanceSentinelError(
            "at least one changed path "
            "is required"
        )

    for path in values:
        if (
            not isinstance(path, bytes)
            or not path
        ):
            raise GovernanceSentinelError(
                "changed paths must be "
                "non-empty raw Git bytes"
            )

    return tuple(
        sorted(set(values))
    )


def evaluate_governance_facts(
    changed_paths: Iterable[bytes],
    predecessor_manifest: dict[str, Any],
    manifest_guard_result: ManifestGuardResult | None,
) -> GovernanceFacts:
    """Validate authority and produce facts without owning class routing.

    Predecessor authority is validated before facts are derived. Candidate
    manifest bytes are represented only by a trusted manifest-guard result.
    Ordinary classification is mandatory and is not controlled here.
    """

    try:
        validate_predecessor_manifest(
            predecessor_manifest
        )
    except ManifestGuardError as exc:
        raise GovernanceSentinelError(
            "invalid predecessor governance "
            "authority"
        ) from exc

    paths = _validated_paths(
        changed_paths
    )

    if (
        manifest_guard_result is not None
        and not isinstance(
            manifest_guard_result,
            ManifestGuardResult,
        )
    ):
        raise GovernanceSentinelError(
            "manifest guard result must use ManifestGuardResult"
        )

    bootstrap_surface_hit = any(
        path.startswith(
            _BOOTSTRAP_GOVERNANCE_IMPLEMENTATION_PREFIX
        )
        for path in paths
    )

    weakening_detected = (
        manifest_guard_result is not None
        and manifest_guard_result.weakening_detected
    )

    return GovernanceFacts(
        bootstrap_surface_hit=bootstrap_surface_hit,
        manifest_weakening_detected=(
            weakening_detected
        ),
        weakening_details=(
            manifest_guard_result.reasons
            if manifest_guard_result is not None
            else ()
        ),
    )

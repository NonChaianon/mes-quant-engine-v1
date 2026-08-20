from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .manifest_guard import (
    ManifestGuardError,
    validate_predecessor_manifest,
)


class GovernanceSentinelError(RuntimeError):
    """Raised when governance interception cannot complete safely."""


@dataclass(frozen=True)
class GovernanceSentinelResult:
    """Deterministic pre-classification governance interception."""

    intercepted: bool
    ordinary_classifier_allowed: bool
    detected_classes: tuple[str, ...]
    reasons: tuple[str, ...]


_CLASS_ORDER = (
    "GOVERNANCE_AMENDMENT",
    "CROSS_BOUNDARY",
)

_BOOTSTRAP_GOVERNANCE_IMPLEMENTATION_PREFIXES = (
    b"src/mes_quant/governance/",
)


def _manifest_ascii_values(
    manifest: dict[str, Any],
    field: str,
) -> tuple[bytes, ...]:
    value = manifest.get(field)

    if not isinstance(value, list):
        raise GovernanceSentinelError(
            "invalid predecessor manifest "
            f"field: {field}"
        )

    result: list[bytes] = []

    for entry in value:
        if (
            not isinstance(entry, str)
            or not entry
        ):
            raise GovernanceSentinelError(
                "invalid predecessor manifest "
                f"entry: {field}"
            )

        try:
            encoded = entry.encode(
                "ascii"
            )
        except UnicodeEncodeError as exc:
            raise GovernanceSentinelError(
                "non-ASCII predecessor manifest "
                f"entry: {field}"
            ) from exc

        result.append(encoded)

    return tuple(result)


def _matches_exact(
    path: bytes,
    values: tuple[bytes, ...],
) -> bool:
    return path in values


def _matches_prefix(
    path: bytes,
    values: tuple[bytes, ...],
) -> bool:
    return any(
        path.startswith(prefix)
        for prefix in values
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


def evaluate_governance_paths(
    changed_paths: Iterable[bytes],
    predecessor_manifest: dict[str, Any],
) -> GovernanceSentinelResult:
    """Intercept governance subjects before ordinary classification.

    Predecessor authority is validated before any path decision.
    Candidate-controlled manifest bytes are not inputs to this function.
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

    governance_exact = (
        _manifest_ascii_values(
            predecessor_manifest,
            "governance_control_exact_paths",
        )
    )

    governance_prefixes = (
        _manifest_ascii_values(
            predecessor_manifest,
            "governance_control_prefixes",
        )
    )

    byte_policy_exact = (
        _manifest_ascii_values(
            predecessor_manifest,
            "byte_policy_exact_paths",
        )
    )

    ci_prefixes = (
        _manifest_ascii_values(
            predecessor_manifest,
            "ci_control_prefixes",
        )
    )

    classes: set[str] = set()
    reasons: set[str] = set()

    for path in paths:
        governance_control = (
            _matches_exact(
                path,
                governance_exact,
            )
            or _matches_prefix(
                path,
                governance_prefixes,
            )
            or _matches_exact(
                path,
                byte_policy_exact,
            )
        )

        ci_control = _matches_prefix(
            path,
            ci_prefixes,
        )

        bootstrap_implementation = (
            _matches_prefix(
                path,
                _BOOTSTRAP_GOVERNANCE_IMPLEMENTATION_PREFIXES,
            )
        )

        if governance_control:
            classes.add(
                "GOVERNANCE_AMENDMENT"
            )

            reasons.add(
                "governance-control:"
                + path.hex()
            )

        if ci_control:
            classes.update(
                {
                    "GOVERNANCE_AMENDMENT",
                    "CROSS_BOUNDARY",
                }
            )

            reasons.add(
                "ci-control:"
                + path.hex()
            )

        if bootstrap_implementation:
            classes.add(
                "GOVERNANCE_AMENDMENT"
            )

            reasons.add(
                "bootstrap-governance-implementation:"
                + path.hex()
            )

    ordered_classes = tuple(
        name
        for name in _CLASS_ORDER
        if name in classes
    )

    intercepted = (
        "GOVERNANCE_AMENDMENT"
        in classes
    )

    return GovernanceSentinelResult(
        intercepted=intercepted,
        ordinary_classifier_allowed=(
            not intercepted
        ),
        detected_classes=ordered_classes,
        reasons=tuple(
            sorted(reasons)
        ),
    )

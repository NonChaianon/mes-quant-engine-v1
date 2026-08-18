from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

CLASS_ORDER = (
    "GOVERNANCE_AMENDMENT",
    "UX_ONLY",
    "QUANT_ENGINE",
    "CROSS_BOUNDARY",
)


class PathClassificationError(RuntimeError):
    """Raised when Phase-1 path classification cannot prove frozen manifest coverage."""


_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")


@dataclass(frozen=True)
class PathClassification:
    detected_classes: tuple[str, ...]
    reasons: tuple[str, ...]


def _ascii_bytes(values: list[str]) -> tuple[bytes, ...]:
    return tuple(value.encode("ascii") for value in values)


def _matches_exact(path: bytes, values: list[str]) -> bool:
    return path in _ascii_bytes(values)


def _matches_prefix(path: bytes, values: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in _ascii_bytes(values))


def _ordered(classes: set[str]) -> tuple[str, ...]:
    return tuple(name for name in CLASS_ORDER if name in classes)


def _phase1_quant_module_is_path_covered(
    module: str,
    manifest: dict[str, Any],
) -> bool:
    """Prove that a protected module is already covered by a frozen Quant path rule."""

    if not isinstance(module, str) or _MODULE_RE.fullmatch(module) is None:
        raise PathClassificationError(f"invalid protected_quant_modules entry: {module!r}")

    module_path = module.replace(".", "/")
    source_prefix = f"src/{module_path}/".encode("ascii")
    source_file = f"src/{module_path}.py".encode("ascii")

    quant_prefixes = _ascii_bytes(manifest["protected_quant_prefixes"])
    quant_exact = _ascii_bytes(manifest["protected_quant_exact_paths"])

    return (
        any(
            source_prefix.startswith(prefix) or source_file.startswith(prefix)
            for prefix in quant_prefixes
        )
        or source_file in quant_exact
    )


def _validate_phase1_manifest_coverage(manifest: dict[str, Any]) -> None:
    """Fail closed for semantic categories that Phase 1 does not directly analyze."""

    protected_symbols = manifest["protected_symbols"]
    if protected_symbols:
        raise PathClassificationError(
            "protected_symbols require semantic/reference analysis unavailable in Phase 1"
        )

    uncovered_modules = tuple(
        module
        for module in manifest["protected_quant_modules"]
        if not _phase1_quant_module_is_path_covered(module, manifest)
    )
    if uncovered_modules:
        raise PathClassificationError(
            "protected_quant_modules lack Phase-1 protected path coverage: "
            + ", ".join(uncovered_modules)
        )


def classify_paths(
    paths: tuple[bytes, ...] | list[bytes],
    manifest: dict[str, Any],
) -> PathClassification:
    """Classify raw Git paths using only frozen Phase-1 manifest path rules.

    This is deliberately conservative. Capability/reference proof is Phase 2, so an otherwise
    unclassified path becomes CROSS_BOUNDARY. UX_ONLY is unreachable while the frozen
    presentation boundary is empty.
    """

    _validate_phase1_manifest_coverage(manifest)

    classes: set[str] = set()
    reasons: list[str] = []

    for path in paths:
        if not isinstance(path, bytes) or not path:
            raise ValueError("paths must be non-empty raw Git path bytes")

        governance = (
            _matches_exact(path, manifest["governance_control_exact_paths"])
            or _matches_prefix(path, manifest["governance_control_prefixes"])
            or _matches_exact(path, manifest["byte_policy_exact_paths"])
        )
        ci = _matches_prefix(path, manifest["ci_control_prefixes"])
        quant = (
            _matches_exact(path, manifest["protected_quant_exact_paths"])
            or _matches_prefix(path, manifest["protected_quant_prefixes"])
            or _matches_prefix(path, manifest["protected_artifact_prefixes"])
            or _matches_prefix(path, manifest["protected_schema_prefixes"])
        )
        dependency = _matches_exact(path, manifest["dependency_manifest_exact_paths"])
        execution = _matches_prefix(path, manifest["execution_sensitive_prefixes"])

        if governance:
            classes.add("GOVERNANCE_AMENDMENT")
            reasons.append(f"governance:{path.hex()}")
        if ci:
            classes.update({"GOVERNANCE_AMENDMENT", "CROSS_BOUNDARY"})
            reasons.append(f"ci-control:{path.hex()}")
        if quant:
            classes.add("QUANT_ENGINE")
            reasons.append(f"quant:{path.hex()}")
        if dependency:
            classes.add("CROSS_BOUNDARY")
            reasons.append(f"dependency:{path.hex()}")
        if execution and not governance and not quant:
            classes.add("CROSS_BOUNDARY")
            reasons.append(f"execution-sensitive:{path.hex()}")

        if not any((governance, ci, quant, dependency, execution)):
            classes.add("CROSS_BOUNDARY")
            reasons.append(f"narrower-class-unproven:{path.hex()}")

    if not paths:
        raise ValueError("at least one changed path is required")

    presentation_empty = (
        not manifest["presentation_roots"] and not manifest["read_only_adapter_modules"]
    )
    if presentation_empty and "UX_ONLY" in classes:
        raise AssertionError(
            "UX_ONLY must be unreachable with an empty frozen presentation boundary"
        )

    return PathClassification(
        detected_classes=_ordered(classes),
        reasons=tuple(sorted(reasons)),
    )

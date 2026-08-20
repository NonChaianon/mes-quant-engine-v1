from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ManifestGuardError(RuntimeError):
    """Raised when predecessor-authority manifest comparison is unsafe."""


@dataclass(frozen=True)
class ManifestGuardResult:
    """Deterministic predecessor-to-candidate manifest comparison."""

    weakening_detected: bool
    reasons: tuple[str, ...]


_LIST_FIELDS = (
    "byte_policy_exact_paths",
    "ci_control_prefixes",
    "dependency_manifest_exact_paths",
    "execution_sensitive_prefixes",
    "governance_control_exact_paths",
    "governance_control_prefixes",
    "presentation_roots",
    "protected_artifact_prefixes",
    "protected_quant_exact_paths",
    "protected_quant_modules",
    "protected_quant_prefixes",
    "protected_schema_prefixes",
    "protected_symbols",
    "read_only_adapter_modules",
    "static_spec_freeze_paths",
)

_MONOTONIC_PROTECTION_FIELDS = (
    "byte_policy_exact_paths",
    "ci_control_prefixes",
    "dependency_manifest_exact_paths",
    "execution_sensitive_prefixes",
    "governance_control_exact_paths",
    "governance_control_prefixes",
    "protected_artifact_prefixes",
    "protected_quant_exact_paths",
    "protected_quant_modules",
    "protected_quant_prefixes",
    "protected_schema_prefixes",
    "protected_symbols",
    "static_spec_freeze_paths",
)

_CAPABILITY_BOUNDARY_FIELDS = (
    "presentation_roots",
    "read_only_adapter_modules",
)

_REQUIRED_FIELDS = frozenset(
    (
        *_LIST_FIELDS,
        "manifest_version",
        "match_semantics",
        "schema",
    )
)

_EXPECTED_SCHEMA = "PROTECTED_SURFACE_MANIFEST_V1"

_EXPECTED_MANIFEST_VERSION = (
    "PROTECTED_SURFACE_MANIFEST_V1"
)

_EXPECTED_MATCH_SEMANTICS = {
    "module": (
        "exact_or_descendant_dotted_module_match"
    ),
    "path_exact": (
        "raw_git_path_bytes_equal_ascii_manifest_path_bytes"
    ),
    "path_prefix": (
        "raw_git_path_bytes_startswith_ascii_manifest_prefix_bytes"
    ),
    "symbol": (
        "exact_fully_qualified_module_colon_qualname_match"
    ),
    "unicode_normalization": "NONE",
}


def _validate_string_list(
    manifest: dict[str, Any],
    field: str,
) -> tuple[str, ...]:
    value = manifest.get(field)

    if not isinstance(value, list):
        raise ManifestGuardError(
            f"{field} must be a list"
        )

    result: list[str] = []
    seen: set[str] = set()

    for entry in value:
        if (
            not isinstance(entry, str)
            or not entry
        ):
            raise ManifestGuardError(
                f"{field} entries must be "
                "non-empty strings"
            )

        try:
            entry.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ManifestGuardError(
                f"{field} entries must be ASCII"
            ) from exc

        if entry in seen:
            raise ManifestGuardError(
                f"{field} contains duplicate entry: "
                f"{entry}"
            )

        seen.add(entry)
        result.append(entry)

    return tuple(result)


def _validate_manifest_shape(
    manifest: dict[str, Any],
) -> None:
    if not isinstance(manifest, dict):
        raise ManifestGuardError(
            "manifest root must be an object"
        )

    actual_fields = frozenset(
        manifest.keys()
    )

    missing = _REQUIRED_FIELDS.difference(
        actual_fields
    )

    extra = actual_fields.difference(
        _REQUIRED_FIELDS
    )

    if missing:
        raise ManifestGuardError(
            "manifest missing required fields: "
            + ", ".join(sorted(missing))
        )

    if extra:
        raise ManifestGuardError(
            "manifest contains unknown fields: "
            + ", ".join(sorted(extra))
        )

    for field in _LIST_FIELDS:
        _validate_string_list(
            manifest,
            field,
        )

    manifest_version = manifest[
        "manifest_version"
    ]

    if (
        not isinstance(manifest_version, str)
        or not manifest_version
    ):
        raise ManifestGuardError(
            "manifest_version must be "
            "a non-empty string"
        )

    schema = manifest["schema"]

    if (
        not isinstance(schema, str)
        or not schema
    ):
        raise ManifestGuardError(
            "schema must be a non-empty string"
        )

    match_semantics = manifest[
        "match_semantics"
    ]

    if not isinstance(
        match_semantics,
        dict,
    ):
        raise ManifestGuardError(
            "match_semantics must be an object"
        )

    for key, value in match_semantics.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or not value
        ):
            raise ManifestGuardError(
                "match_semantics must contain "
                "non-empty string keys and values"
            )


def validate_predecessor_manifest(
    manifest: dict[str, Any],
) -> None:
    """Fail closed unless predecessor authority has exact V1 semantics."""

    _validate_manifest_shape(
        manifest
    )

    if (
        manifest["schema"]
        != _EXPECTED_SCHEMA
    ):
        raise ManifestGuardError(
            "predecessor manifest schema "
            "identity mismatch"
        )

    if (
        manifest["manifest_version"]
        != _EXPECTED_MANIFEST_VERSION
    ):
        raise ManifestGuardError(
            "predecessor manifest version "
            "identity mismatch"
        )

    if (
        manifest["match_semantics"]
        != _EXPECTED_MATCH_SEMANTICS
    ):
        raise ManifestGuardError(
            "predecessor match semantics "
            "identity mismatch"
        )


def detect_manifest_weakening(
    predecessor_manifest: dict[str, Any],
    candidate_manifest: dict[str, Any],
) -> ManifestGuardResult:
    """Detect protection or capability-boundary weakening.

    The predecessor manifest is authority.

    Candidate bytes may request an amendment, but they never define the
    authority used to decide whether their own amendment weakens V1.
    """

    validate_predecessor_manifest(
        predecessor_manifest
    )

    _validate_manifest_shape(
        candidate_manifest
    )

    reasons: set[str] = set()

    for field in _MONOTONIC_PROTECTION_FIELDS:
        predecessor_values = set(
            _validate_string_list(
                predecessor_manifest,
                field,
            )
        )

        candidate_values = set(
            _validate_string_list(
                candidate_manifest,
                field,
            )
        )

        removed = (
            predecessor_values
            - candidate_values
        )

        for value in sorted(removed):
            reasons.add(
                f"removed:{field}:{value}"
            )

    for field in _CAPABILITY_BOUNDARY_FIELDS:
        predecessor_values = set(
            _validate_string_list(
                predecessor_manifest,
                field,
            )
        )

        candidate_values = set(
            _validate_string_list(
                candidate_manifest,
                field,
            )
        )

        if (
            candidate_values
            != predecessor_values
        ):
            reasons.add(
                f"changed:{field}"
            )

    if (
        candidate_manifest["match_semantics"]
        != predecessor_manifest[
            "match_semantics"
        ]
    ):
        reasons.add(
            "changed:match_semantics"
        )

    if (
        candidate_manifest["schema"]
        != predecessor_manifest["schema"]
    ):
        reasons.add(
            "changed:schema"
        )

    if (
        candidate_manifest[
            "manifest_version"
        ]
        != predecessor_manifest[
            "manifest_version"
        ]
    ):
        reasons.add(
            "changed:manifest_version"
        )

    ordered_reasons = tuple(
        sorted(reasons)
    )

    return ManifestGuardResult(
        weakening_detected=bool(
            ordered_reasons
        ),
        reasons=ordered_reasons,
    )

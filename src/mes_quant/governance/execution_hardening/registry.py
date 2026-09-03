"""Closed production/rehearsal registry predicates for synthetic Tier-1 fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, runtime_checkable

EXECUTION_SCHEMA = "MES_EXECUTION_RECORD_SCHEMA_V1"
REHEARSAL_RECORD_KIND = "REHEARSAL"
REHEARSAL_EVIDENCE_CLASS = "SYNTHETIC_REHEARSAL"
PRODUCTION_EVIDENCE_CLASS = "REAL_GOVERNED_EXECUTION"
REHEARSAL_TARGET_STATE = "NOT_APPLICABLE_SYNTHETIC_REHEARSAL"
REHEARSAL_AUTHORITY_STATE = "REHEARSAL_ONLY_NO_SCIENTIFIC_AUTHORITY"
REHEARSAL_TRUST_ROOT = "MES_REHEARSAL_EPHEMERAL_SHA256_SEAL_ROOT_V1"
FIXTURE_TRUST_ROOT = "MES_TEST_FIXTURE_PRODUCTION_TRUST_ROOT_V1"
RUNTIME_PRODUCTION_TRUST_ROOT = "NOT_YET_RATIFIED_PRODUCTION_TRUST_ROOT"
NO_SOURCE_ARTIFACT_ACCESSED = "NO_SOURCE_ARTIFACT_ACCESSED"
NON_EVIDENTIARY_FIXTURE_ID = "NON_EVIDENTIARY_TIER1_FIXTURE"

REHEARSAL_CONTAMINATION = "REHEARSAL_CONTAMINATION_STOP"
PRODUCTION_CONTAMINATION = "PRODUCTION_CONTAMINATION_STOP"
PRODUCTION_BINDING_INVALID = "PRODUCTION_BINDING_MISSING_OR_UNKNOWN_STOP"
SOURCE_SENTINEL_INVALID = "NO_SOURCE_ARTIFACT_ACCESSED_INVALID_STOP"
PRODUCTION_TRUST_REJECTED = "PRODUCTION_TRUST_ROOT_REJECTED_STOP"
REHEARSAL_BINDING_INVALID = "REHEARSAL_BINDING_INVALID_STOP"
REHEARSAL_TRANSITION_INVALID = "REHEARSAL_TRANSITION_INVALID_STOP"

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

_PRODUCTION_RECORD_KINDS = frozenset({"PRECONDITION_STOP", "STAGE_SUCCESS", "STAGE_TERMINAL"})
_PRODUCTION_TARGET_STATES = frozenset(
    {
        "LOCKED_UNRESERVED",
        "LOCKED_RESERVED_NOT_CONSUMED",
        "CONSUMED",
        "CLOSED_UNCONSUMED",
        "ACCESS_NOT_ATTESTED_FAIL_CLOSED",
    }
)
_PRODUCTION_AUTHORITY_STATES = frozenset(
    {
        "NOT_AUTHORIZED",
        "REVIEW_PENDING",
        "AUTHORIZED_UNUSED",
        "RESERVATION_CONSUMED",
        "COMPLETED_SEALED",
        "TERMINAL_NO_RETRY",
        "NOT_ATTESTED_FAIL_CLOSED",
    }
)
_REHEARSAL_STAGES = (
    "CONTRACT",
    "METADATA",
    "PRE_TARGET",
    "TARGET_PREFIT",
    "FIT",
    "SEALED",
)

PRODUCTION_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_kind",
        "evidence_class",
        "synthetic",
        "scientific_inference_authorized",
        "target_access_state",
        "execution_authority_state",
        "execution_authorization_reservation_consumed",
        "protocol_id",
        "run_id",
        "artifact_path",
        "source_binding",
        "source_access_guard",
        "source_artifact_reads",
        "source_schema_contract_sha256",
        "sealing_trust_root",
    }
)

REHEARSAL_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_kind",
        "evidence_class",
        "synthetic",
        "scientific_inference_authorized",
        "target_access_state",
        "execution_authority_state",
        "execution_authorization_reservation_consumed",
        "rehearsal_stage",
        "rehearsal_surface_map_id",
        "rehearsal_surface_map_path",
        "rehearsal_surface_map_sha256",
        "sealing_trust_root",
        "protocol_id",
        "run_id",
        "artifact_path",
    }
)

_REHEARSAL_ONLY_FIELDS = REHEARSAL_RECORD_FIELDS.difference(PRODUCTION_RECORD_FIELDS)


class RegistryValidationError(ValueError):
    """A registry predicate stopped before accepting the candidate record."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code


@runtime_checkable
class ProductionTrustPolicy(Protocol):
    """Mandatory injected production trust-root predicate."""

    policy_id: str

    def accepts(self, sealing_trust_root: str, *, in_memory: bool) -> bool:
        """Return whether the root is acceptable in this evaluation context."""


@dataclass(frozen=True)
class InMemoryProductionFixturePolicy:
    """Canonical same-core production fixture policy; never valid for persistence."""

    policy_id: str = "MES_TEST_FIXTURE_PRODUCTION_POLICY_V1"

    def accepts(self, sealing_trust_root: str, *, in_memory: bool) -> bool:
        return in_memory and sealing_trust_root == FIXTURE_TRUST_ROOT


@dataclass(frozen=True)
class RuntimeRejectAllProductionPolicy:
    """Phase-A runtime production policy: every candidate is rejected."""

    policy_id: str = "NOT_YET_RATIFIED_PRODUCTION_POLICY"

    def accepts(self, sealing_trust_root: str, *, in_memory: bool) -> bool:
        del sealing_trust_root, in_memory
        return False


@dataclass(frozen=True)
class RegistryAcceptance:
    """Positive own-class result; it is not a persisted registry entry."""

    record_class: str
    record_sha256: str
    persistence_authorized: bool = False


@dataclass(frozen=True)
class NonEvidentiaryFixtureSeal:
    """Create-once Tier-1 fixture result that is explicitly not evidence."""

    fixture_identity: str
    path: Path
    sha256: str
    evidence: bool = False
    authority: bool = False


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def _is_closed_bool(value: object) -> bool:
    return isinstance(value, bool)


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def canonical_record_bytes(record: Mapping[str, object]) -> bytes:
    """Return deterministic JSON bytes without writing or sealing a record."""

    return (
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _acceptance(record_class: str, record: Mapping[str, object]) -> RegistryAcceptance:
    return RegistryAcceptance(
        record_class=record_class,
        record_sha256=hashlib.sha256(canonical_record_bytes(record)).hexdigest(),
    )


def _is_rehearsal_namespace(path: object) -> bool:
    return isinstance(path, str) and path.startswith("artifacts/rehearsal/")


def _has_rehearsal_marker(record: Mapping[str, object]) -> bool:
    return (
        bool(set(record).intersection(_REHEARSAL_ONLY_FIELDS))
        or record.get("record_kind") == REHEARSAL_RECORD_KIND
        or record.get("evidence_class") == REHEARSAL_EVIDENCE_CLASS
        or record.get("synthetic") is True
        or record.get("target_access_state") == REHEARSAL_TARGET_STATE
        or record.get("execution_authority_state") == REHEARSAL_AUTHORITY_STATE
        or (
            isinstance(record.get("protocol_id"), str)
            and str(record["protocol_id"]).startswith("REHEARSAL_")
        )
        or (
            isinstance(record.get("run_id"), str)
            and str(record["run_id"]).startswith("REHEARSAL_")
        )
        or _is_rehearsal_namespace(record.get("artifact_path"))
        or record.get("sealing_trust_root") == REHEARSAL_TRUST_ROOT
    )


def validate_production_record(
    record: Mapping[str, object],
    *,
    trust_policy: ProductionTrustPolicy,
    in_memory: bool,
) -> RegistryAcceptance:
    """Run the one production predicate used by fixture and runtime policies."""

    if not isinstance(record, Mapping):
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "record must be an object")
    if _has_rehearsal_marker(record):
        raise RegistryValidationError(REHEARSAL_CONTAMINATION, "rehearsal marker detected")
    if set(record) != PRODUCTION_RECORD_FIELDS:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "closed field set mismatch")

    if record["schema_version"] != EXECUTION_SCHEMA:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "schema mismatch")
    if record["record_kind"] not in _PRODUCTION_RECORD_KINDS:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "record kind mismatch")
    if record["evidence_class"] != PRODUCTION_EVIDENCE_CLASS or record["synthetic"] is not False:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "production markers invalid")
    if not _is_closed_bool(record["scientific_inference_authorized"]):
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "scientific flag is not boolean")
    if record["target_access_state"] not in _PRODUCTION_TARGET_STATES:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "target state invalid")
    if record["execution_authority_state"] not in _PRODUCTION_AUTHORITY_STATES:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "authority state invalid")
    if not _is_closed_bool(record["execution_authorization_reservation_consumed"]):
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "reservation flag invalid")

    for field in ("protocol_id", "run_id", "artifact_path"):
        if not isinstance(record[field], str) or not record[field]:
            raise RegistryValidationError(PRODUCTION_BINDING_INVALID, f"{field} missing")
    if _is_rehearsal_namespace(record["artifact_path"]):
        raise RegistryValidationError(REHEARSAL_CONTAMINATION, "rehearsal namespace detected")

    source_binding = record["source_binding"]
    source_guard = record["source_access_guard"]
    source_reads = record["source_artifact_reads"]
    source_schema_hash = record["source_schema_contract_sha256"]
    if not _is_nonnegative_int(source_reads):
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "source read count invalid")

    if source_binding == NO_SOURCE_ARTIFACT_ACCESSED:
        sentinel_valid = (
            source_guard == "PRE_SOURCE_NO_ACCESS_VERIFIED"
            and source_reads == 0
            and source_schema_hash is None
            and record["target_access_state"]
            in {
                "LOCKED_UNRESERVED",
                "LOCKED_RESERVED_NOT_CONSUMED",
                "CLOSED_UNCONSUMED",
            }
        )
        if not sentinel_valid:
            raise RegistryValidationError(SOURCE_SENTINEL_INVALID, "closed sentinel misused")
    else:
        if (
            not _is_sha256(source_binding)
            or source_guard != "SOURCE_CONTRACT_BOUND"
            or not _is_sha256(source_schema_hash)
            or source_binding != source_schema_hash
        ):
            raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "source contract invalid")

    sealing_root = record["sealing_trust_root"]
    if not isinstance(sealing_root, str) or not sealing_root:
        raise RegistryValidationError(PRODUCTION_BINDING_INVALID, "sealing root missing")
    if not trust_policy.accepts(sealing_root, in_memory=in_memory):
        raise RegistryValidationError(PRODUCTION_TRUST_REJECTED, "trust policy rejected root")

    return _acceptance("PRODUCTION", record)


def _valid_rehearsal_artifact_path(record: Mapping[str, object]) -> bool:
    path = record["artifact_path"]
    if not isinstance(path, str):
        return False
    pure_path = PurePosixPath(path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return False
    expected_prefix = (
        "artifacts",
        "rehearsal",
        str(record["protocol_id"]),
        str(record["run_id"]),
    )
    return len(pure_path.parts) > len(expected_prefix) and pure_path.parts[:4] == expected_prefix


def validate_rehearsal_record(record: Mapping[str, object]) -> RegistryAcceptance:
    """Accept only the closed synthetic-rehearsal class."""

    if not isinstance(record, Mapping):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "record must be an object")
    if (
        record.get("record_kind") in _PRODUCTION_RECORD_KINDS
        or record.get("evidence_class") == PRODUCTION_EVIDENCE_CLASS
        or record.get("synthetic") is False
        or record.get("target_access_state") in _PRODUCTION_TARGET_STATES
        or record.get("execution_authority_state") in _PRODUCTION_AUTHORITY_STATES
    ):
        raise RegistryValidationError(PRODUCTION_CONTAMINATION, "production marker detected")
    if set(record) != REHEARSAL_RECORD_FIELDS:
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "closed field set mismatch")

    exact_values = {
        "schema_version": EXECUTION_SCHEMA,
        "record_kind": REHEARSAL_RECORD_KIND,
        "evidence_class": REHEARSAL_EVIDENCE_CLASS,
        "synthetic": True,
        "scientific_inference_authorized": False,
        "target_access_state": REHEARSAL_TARGET_STATE,
        "execution_authority_state": REHEARSAL_AUTHORITY_STATE,
        "sealing_trust_root": REHEARSAL_TRUST_ROOT,
    }
    if any(record[field] != value for field, value in exact_values.items()):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "rehearsal marker mismatch")
    if not _is_closed_bool(record["execution_authorization_reservation_consumed"]):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "reservation flag invalid")
    if record["rehearsal_stage"] not in _REHEARSAL_STAGES:
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "stage invalid")

    surface_map_id = record["rehearsal_surface_map_id"]
    surface_map_path = record["rehearsal_surface_map_path"]
    if not isinstance(surface_map_id, str) or not surface_map_id.startswith("REHEARSAL_SURFACE_MAP_V"):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "surface-map ID invalid")
    if (
        not isinstance(surface_map_path, str)
        or not surface_map_path.startswith("configs/governance/rehearsal_surface_map_v")
        or not surface_map_path.endswith(".json")
        or not _is_sha256(record["rehearsal_surface_map_sha256"])
    ):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "surface-map binding invalid")

    for field in ("protocol_id", "run_id"):
        if not isinstance(record[field], str) or not record[field].startswith("REHEARSAL_"):
            raise RegistryValidationError(REHEARSAL_BINDING_INVALID, f"{field} invalid")
    if not _valid_rehearsal_artifact_path(record):
        raise RegistryValidationError(REHEARSAL_BINDING_INVALID, "artifact namespace invalid")

    return _acceptance("REHEARSAL", record)


def validate_rehearsal_progression(
    previous: Mapping[str, object],
    current: Mapping[str, object],
) -> None:
    """Prove stage ordering and the isolated reservation boolean's monotonicity."""

    validate_rehearsal_record(previous)
    validate_rehearsal_record(current)
    identity_fields = (
        "protocol_id",
        "run_id",
        "rehearsal_surface_map_id",
        "rehearsal_surface_map_path",
        "rehearsal_surface_map_sha256",
    )
    if any(previous[field] != current[field] for field in identity_fields):
        raise RegistryValidationError(REHEARSAL_TRANSITION_INVALID, "lineage identity changed")
    if (
        previous["execution_authorization_reservation_consumed"] is True
        and current["execution_authorization_reservation_consumed"] is False
    ):
        raise RegistryValidationError(REHEARSAL_TRANSITION_INVALID, "reservation flag regressed")
    if _REHEARSAL_STAGES.index(str(current["rehearsal_stage"])) < _REHEARSAL_STAGES.index(
        str(previous["rehearsal_stage"])
    ):
        raise RegistryValidationError(REHEARSAL_TRANSITION_INVALID, "stage regressed")


def create_non_evidentiary_fixture(
    destination: Path,
    payload: bytes,
    *,
    pytest_temp_root: Path,
    fixture_identity: str,
) -> NonEvidentiaryFixtureSeal:
    """Exclusive-create and reread a Tier-1 fixture outside evidence namespaces."""

    if fixture_identity != NON_EVIDENTIARY_FIXTURE_ID:
        raise ValueError("fixture identity is not NON_EVIDENTIARY_TIER1_FIXTURE")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")

    root = pytest_temp_root.resolve(strict=True)
    candidate = destination.resolve(strict=False)
    if candidate == root or root not in candidate.parents:
        raise ValueError("fixture destination escapes pytest temporary root")
    if "artifacts" in candidate.parts and "rehearsal" in candidate.parts:
        raise ValueError("Tier-1 fixture may not enter the rehearsal evidence namespace")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(payload)
    reread = destination.read_bytes()
    if reread != payload:
        raise RuntimeError("fixture reread mismatch")

    return NonEvidentiaryFixtureSeal(
        fixture_identity=fixture_identity,
        path=destination,
        sha256=hashlib.sha256(reread).hexdigest(),
    )

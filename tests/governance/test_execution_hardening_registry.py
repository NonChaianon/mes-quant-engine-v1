from __future__ import annotations

import copy
from pathlib import Path

import pytest

from mes_quant.governance.execution_hardening import registry


def _production_record() -> dict[str, object]:
    return {
        "schema_version": registry.EXECUTION_SCHEMA,
        "record_kind": "PRECONDITION_STOP",
        "evidence_class": registry.PRODUCTION_EVIDENCE_CLASS,
        "synthetic": False,
        "scientific_inference_authorized": False,
        "target_access_state": "LOCKED_UNRESERVED",
        "execution_authority_state": "NOT_AUTHORIZED",
        "execution_authorization_reservation_consumed": False,
        "protocol_id": "MES_PRODUCTION_FIXTURE_V1",
        "run_id": "MES_FIXTURE_RUN_001",
        "artifact_path": "IN_MEMORY_ONLY_NOT_EMITTED",
        "source_binding": registry.NO_SOURCE_ARTIFACT_ACCESSED,
        "source_access_guard": "PRE_SOURCE_NO_ACCESS_VERIFIED",
        "source_artifact_reads": 0,
        "source_schema_contract_sha256": None,
        "sealing_trust_root": registry.FIXTURE_TRUST_ROOT,
    }


def _rehearsal_record(*, consumed: bool = False, stage: str = "CONTRACT") -> dict[str, object]:
    return {
        "schema_version": registry.EXECUTION_SCHEMA,
        "record_kind": registry.REHEARSAL_RECORD_KIND,
        "evidence_class": registry.REHEARSAL_EVIDENCE_CLASS,
        "synthetic": True,
        "scientific_inference_authorized": False,
        "target_access_state": registry.REHEARSAL_TARGET_STATE,
        "execution_authority_state": registry.REHEARSAL_AUTHORITY_STATE,
        "execution_authorization_reservation_consumed": consumed,
        "rehearsal_stage": stage,
        "rehearsal_surface_map_id": "REHEARSAL_SURFACE_MAP_V5",
        "rehearsal_surface_map_path": "configs/governance/rehearsal_surface_map_v5.json",
        "rehearsal_surface_map_sha256": "8" * 64,
        "sealing_trust_root": registry.REHEARSAL_TRUST_ROOT,
        "protocol_id": "REHEARSAL_EXECUTION_HARDENING_V1",
        "run_id": "REHEARSAL_RUN_001",
        "artifact_path": (
            "artifacts/rehearsal/REHEARSAL_EXECUTION_HARDENING_V1/"
            "REHEARSAL_RUN_001/record.json"
        ),
    }


def _reason(exc_info: pytest.ExceptionInfo[registry.RegistryValidationError]) -> str:
    return exc_info.value.reason_code


def test_same_production_core_passes_fixture_policy_and_stops_runtime_policy() -> None:
    record = _production_record()

    accepted = registry.validate_production_record(
        record,
        trust_policy=registry.InMemoryProductionFixturePolicy(),
        in_memory=True,
    )
    assert accepted.record_class == "PRODUCTION"
    assert not accepted.persistence_authorized

    with pytest.raises(registry.RegistryValidationError) as exc_info:
        registry.validate_production_record(
            record,
            trust_policy=registry.RuntimeRejectAllProductionPolicy(),
            in_memory=False,
        )
    assert _reason(exc_info) == registry.PRODUCTION_TRUST_REJECTED


def test_registries_reject_opposite_classes() -> None:
    with pytest.raises(registry.RegistryValidationError) as production_exc:
        registry.validate_production_record(
            _rehearsal_record(),
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )
    assert _reason(production_exc) == registry.REHEARSAL_CONTAMINATION

    with pytest.raises(registry.RegistryValidationError) as rehearsal_exc:
        registry.validate_rehearsal_record(_production_record())
    assert _reason(rehearsal_exc) == registry.PRODUCTION_CONTAMINATION


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("record_kind", "PRECONDITION_STOP"),
        ("evidence_class", registry.PRODUCTION_EVIDENCE_CLASS),
        ("synthetic", False),
        ("target_access_state", "LOCKED_UNRESERVED"),
        ("execution_authority_state", "NOT_AUTHORIZED"),
        ("protocol_id", "MES_PROTOCOL"),
        ("run_id", "MES_RUN"),
        ("artifact_path", "artifacts/governance/record.json"),
        ("sealing_trust_root", registry.FIXTURE_TRUST_ROOT),
    ],
)
def test_each_single_rehearsal_marker_mutation_still_cannot_enter_production(
    field: str,
    replacement: object,
) -> None:
    candidate = _rehearsal_record()
    candidate[field] = replacement

    with pytest.raises(registry.RegistryValidationError):
        registry.validate_production_record(
            candidate,
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )


def test_combined_marker_removal_still_rejects_rehearsal_trust_root() -> None:
    candidate = _production_record()
    candidate["sealing_trust_root"] = registry.REHEARSAL_TRUST_ROOT

    with pytest.raises(registry.RegistryValidationError) as exc_info:
        registry.validate_production_record(
            candidate,
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )
    assert _reason(exc_info) == registry.REHEARSAL_CONTAMINATION


@pytest.mark.parametrize(
    "field",
    [
        "source_binding",
        "source_access_guard",
        "sealing_trust_root",
        "protocol_id",
        "run_id",
        "artifact_path",
    ],
)
def test_missing_positive_production_binding_fails_closed(field: str) -> None:
    candidate = _production_record()
    del candidate[field]

    with pytest.raises(registry.RegistryValidationError) as exc_info:
        registry.validate_production_record(
            candidate,
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )
    assert _reason(exc_info) == registry.PRODUCTION_BINDING_INVALID


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("source_access_guard", "SOURCE_CONTRACT_BOUND"),
        ("source_artifact_reads", 1),
        ("source_schema_contract_sha256", "1" * 64),
        ("target_access_state", "CONSUMED"),
        ("target_access_state", "ACCESS_NOT_ATTESTED_FAIL_CLOSED"),
    ],
)
def test_no_source_sentinel_is_closed_and_guarded(field: str, replacement: object) -> None:
    candidate = _production_record()
    candidate[field] = replacement

    with pytest.raises(registry.RegistryValidationError) as exc_info:
        registry.validate_production_record(
            candidate,
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )
    assert _reason(exc_info) == registry.SOURCE_SENTINEL_INVALID


def test_source_contract_hash_requires_exact_guard_and_binding() -> None:
    candidate = _production_record()
    candidate["source_binding"] = "5" * 64
    candidate["source_access_guard"] = "SOURCE_CONTRACT_BOUND"
    candidate["source_schema_contract_sha256"] = "5" * 64

    accepted = registry.validate_production_record(
        candidate,
        trust_policy=registry.InMemoryProductionFixturePolicy(),
        in_memory=True,
    )
    assert accepted.record_class == "PRODUCTION"


def test_rehearsal_progression_accepts_monotone_reservation_and_stage() -> None:
    before = _rehearsal_record(consumed=False, stage="CONTRACT")
    after = _rehearsal_record(consumed=True, stage="METADATA")

    assert registry.validate_rehearsal_record(before).record_class == "REHEARSAL"
    assert registry.validate_rehearsal_record(after).record_class == "REHEARSAL"
    registry.validate_rehearsal_progression(before, after)


def test_rehearsal_progression_rejects_boolean_or_stage_regression() -> None:
    consumed = _rehearsal_record(consumed=True, stage="METADATA")
    boolean_regression = _rehearsal_record(consumed=False, stage="METADATA")
    stage_regression = _rehearsal_record(consumed=True, stage="CONTRACT")

    with pytest.raises(registry.RegistryValidationError) as boolean_exc:
        registry.validate_rehearsal_progression(consumed, boolean_regression)
    assert _reason(boolean_exc) == registry.REHEARSAL_TRANSITION_INVALID

    with pytest.raises(registry.RegistryValidationError) as stage_exc:
        registry.validate_rehearsal_progression(consumed, stage_regression)
    assert _reason(stage_exc) == registry.REHEARSAL_TRANSITION_INVALID


def test_non_evidentiary_fixture_is_create_once_reread_and_hash_verified(tmp_path: Path) -> None:
    destination = tmp_path / "fixtures" / "record.json"
    payload = registry.canonical_record_bytes(_rehearsal_record())

    seal = registry.create_non_evidentiary_fixture(
        destination,
        payload,
        pytest_temp_root=tmp_path,
        fixture_identity=registry.NON_EVIDENTIARY_FIXTURE_ID,
    )

    assert destination.read_bytes() == payload
    assert len(seal.sha256) == 64
    assert not seal.evidence
    assert not seal.authority
    with pytest.raises(FileExistsError):
        registry.create_non_evidentiary_fixture(
            destination,
            payload,
            pytest_temp_root=tmp_path,
            fixture_identity=registry.NON_EVIDENTIARY_FIXTURE_ID,
        )


def test_non_evidentiary_fixture_cannot_escape_or_enter_rehearsal_namespace(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        registry.create_non_evidentiary_fixture(
            tmp_path.parent / "escape.json",
            b"fixture",
            pytest_temp_root=tmp_path,
            fixture_identity=registry.NON_EVIDENTIARY_FIXTURE_ID,
        )
    with pytest.raises(ValueError):
        registry.create_non_evidentiary_fixture(
            tmp_path / "artifacts" / "rehearsal" / "record.json",
            b"fixture",
            pytest_temp_root=tmp_path,
            fixture_identity=registry.NON_EVIDENTIARY_FIXTURE_ID,
        )


def test_unknown_field_rejected_by_both_closed_schemas() -> None:
    production = copy.deepcopy(_production_record())
    production["unknown"] = 1
    rehearsal = copy.deepcopy(_rehearsal_record())
    rehearsal["unknown"] = 1

    with pytest.raises(registry.RegistryValidationError):
        registry.validate_production_record(
            production,
            trust_policy=registry.InMemoryProductionFixturePolicy(),
            in_memory=True,
        )
    with pytest.raises(registry.RegistryValidationError):
        registry.validate_rehearsal_record(rehearsal)

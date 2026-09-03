from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from mes_quant.governance.execution_hardening.records import (
    EXECUTION_RECORD_SCHEMA_VERSION,
    PROTOCOL_RELATIVE_PATH,
    REHEARSAL_EXECUTION_AUTHORITY_STATE,
    REHEARSAL_TARGET_ACCESS_STATE,
    TRANSITION_COMPANION_RELATIVE_PATH,
    ExecutionRecord,
    RecordReasonCode,
    RecordValidationError,
    apply_transition,
    load_transition_contract,
    validate_execution_record,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _assert_reason(error: pytest.ExceptionInfo[RecordValidationError], code: RecordReasonCode) -> None:
    assert error.value.reason_code is code
    assert str(error.value).startswith(f"{code.value}:")


@pytest.fixture(scope="module")
def contract():
    return load_transition_contract(PROJECT_ROOT)


def test_transition_companion_is_sha_bound_and_markdown_equivalent(contract) -> None:
    assert len(contract.target_states) == 5
    assert len(contract.execution_states) == 7
    assert len(contract.target_rows) == 14
    assert len(contract.execution_rows) == 20
    assert sum(len(row.from_states) for row in contract.target_rows) == 18
    assert sum(len(row.from_states) for row in contract.execution_rows) == 22
    assert [row.source_line for row in contract.target_rows] == list(range(123, 137))
    assert [row.source_line for row in contract.execution_rows] == list(range(142, 162))
    assert len(contract.reason_mapping_assertions) == 4


def _copy_transition_inputs(destination: Path) -> None:
    for relative_path in (PROTOCOL_RELATIVE_PATH, TRANSITION_COMPANION_RELATIVE_PATH):
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative_path, target)


def test_protocol_byte_drift_rejects_before_transition_use(tmp_path: Path) -> None:
    _copy_transition_inputs(tmp_path)
    protocol = tmp_path / PROTOCOL_RELATIVE_PATH
    protocol.write_bytes(protocol.read_bytes() + b" ")
    with pytest.raises(RecordValidationError) as error:
        load_transition_contract(tmp_path)
    _assert_reason(error, RecordReasonCode.TRANSITION_PROTOCOL_SHA256_MISMATCH)


def test_companion_byte_drift_rejects_before_transition_use(tmp_path: Path) -> None:
    _copy_transition_inputs(tmp_path)
    companion = tmp_path / TRANSITION_COMPANION_RELATIVE_PATH
    payload = json.loads(companion.read_text(encoding="utf-8"))
    payload["target_access"]["protocol_rows"][0]["event_text"] += " changed"
    companion.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RecordValidationError) as error:
        load_transition_contract(tmp_path)
    _assert_reason(error, RecordReasonCode.TRANSITION_COMPANION_SHA256_MISMATCH)


def test_all_target_allowed_pairs_and_exact_52_complements(contract) -> None:
    allowed = {
        (state, row.event_id): row.transition_map[state]
        for row in contract.target_rows
        for state in row.from_states
    }
    rejected = 0
    for row in contract.target_rows:
        for state in contract.target_states:
            pair = (state, row.event_id)
            if pair in allowed:
                result = apply_transition(
                    contract,
                    ledger="target_access",
                    current_state=state,
                    event_id=row.event_id,
                    execution_authorization_reservation_consumed=False,
                    missing_access_reason_code=(
                        "REQUIRED_ACCESS_EVIDENCE_UNAVAILABLE"
                        if row.event_id == "TARGET_ROW_131"
                        else None
                    ),
                )
                assert result.state == allowed[pair]
                assert result.execution_authorization_reservation_consumed is False
            else:
                with pytest.raises(RecordValidationError) as error:
                    apply_transition(
                        contract,
                        ledger="target_access",
                        current_state=state,
                        event_id=row.event_id,
                        execution_authorization_reservation_consumed=False,
                    )
                _assert_reason(error, RecordReasonCode.INVALID_TRANSITION)
                rejected += 1
    assert len(allowed) == 18
    assert rejected == 52


def test_all_execution_allowed_pairs_and_exact_118_complements(contract) -> None:
    allowed = {
        (state, row.event_id): row.transition_map[state]
        for row in contract.execution_rows
        for state in row.from_states
    }
    rejected = 0
    for row in contract.execution_rows:
        for state in contract.execution_states:
            pair = (state, row.event_id)
            if pair in allowed:
                result = apply_transition(
                    contract,
                    ledger="execution_authority",
                    current_state=state,
                    event_id=row.event_id,
                    execution_authorization_reservation_consumed=(
                        state in {"RESERVATION_CONSUMED", "COMPLETED_SEALED"}
                        or (state == "TERMINAL_NO_RETRY" and row.event_id == "AUTH_ROW_152")
                    ),
                )
                assert result.state == allowed[pair]
            else:
                with pytest.raises(RecordValidationError) as error:
                    apply_transition(
                        contract,
                        ledger="execution_authority",
                        current_state=state,
                        event_id=row.event_id,
                        execution_authorization_reservation_consumed=(
                            state in {"RESERVATION_CONSUMED", "COMPLETED_SEALED"}
                        ),
                    )
                _assert_reason(error, RecordReasonCode.INVALID_TRANSITION)
                rejected += 1
    assert len(allowed) == 22
    assert rejected == 118


def test_unknown_event_and_ledger_reject(contract) -> None:
    with pytest.raises(RecordValidationError) as event_error:
        apply_transition(
            contract,
            ledger="target_access",
            current_state="LOCKED_UNRESERVED",
            event_id="UNKNOWN",
            execution_authorization_reservation_consumed=False,
        )
    _assert_reason(event_error, RecordReasonCode.INVALID_TRANSITION)

    with pytest.raises(RecordValidationError) as ledger_error:
        apply_transition(
            contract,
            ledger="combined",
            current_state="LOCKED_UNRESERVED",
            event_id="TARGET_ROW_123",
            execution_authorization_reservation_consumed=False,
        )
    _assert_reason(ledger_error, RecordReasonCode.INVALID_TRANSITION)


def test_reservation_consumption_is_monotone_and_reason_is_exact(contract) -> None:
    authorized = apply_transition(
        contract,
        ledger="execution_authority",
        current_state="AUTHORIZED_UNUSED",
        event_id="AUTH_ROW_154",
        execution_authorization_reservation_consumed=False,
    )
    assert authorized.state == "RESERVATION_CONSUMED"
    assert authorized.execution_authorization_reservation_consumed is True

    unauthorized = apply_transition(
        contract,
        ledger="execution_authority",
        current_state="REVIEW_PENDING",
        event_id="AUTH_ROW_151",
        execution_authorization_reservation_consumed=False,
    )
    assert unauthorized.state == "TERMINAL_NO_RETRY"
    assert unauthorized.execution_authorization_reservation_consumed is True
    assert (
        unauthorized.reason_code
        == RecordReasonCode.UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION.value
    )

    later = apply_transition(
        contract,
        ledger="execution_authority",
        current_state="TERMINAL_NO_RETRY",
        event_id="AUTH_ROW_152",
        execution_authorization_reservation_consumed=True,
    )
    assert later.execution_authorization_reservation_consumed is True
    assert later.reason_code == unauthorized.reason_code

    with pytest.raises(RecordValidationError) as inconsistent_source:
        apply_transition(
            contract,
            ledger="execution_authority",
            current_state="REVIEW_PENDING",
            event_id="AUTH_ROW_145",
            execution_authorization_reservation_consumed=True,
        )
    _assert_reason(
        inconsistent_source,
        RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH,
    )


def test_reason_qualifiers_are_machine_observable(contract) -> None:
    with pytest.raises(RecordValidationError) as missing:
        apply_transition(
            contract,
            ledger="target_access",
            current_state="CONSUMED",
            event_id="TARGET_ROW_131",
            execution_authorization_reservation_consumed=False,
        )
    _assert_reason(missing, RecordReasonCode.TRANSITION_REASON_CODE_REQUIRED)

    target = apply_transition(
        contract,
        ledger="target_access",
        current_state="CONSUMED",
        event_id="TARGET_ROW_131",
        execution_authorization_reservation_consumed=False,
        missing_access_reason_code="REQUIRED_ACCESS_EVIDENCE_UNAVAILABLE",
    )
    assert target.state == "CONSUMED"
    assert target.reason_code == "REQUIRED_ACCESS_EVIDENCE_UNAVAILABLE"

    attempt = apply_transition(
        contract,
        ledger="execution_authority",
        current_state="REVIEW_PENDING",
        event_id="AUTH_ROW_149",
        execution_authorization_reservation_consumed=False,
    )
    assert attempt.state == "REVIEW_PENDING"
    assert attempt.individual_attempt_stops is True


def _production_record(**overrides: object) -> ExecutionRecord:
    values: dict[str, object] = {
        "schema_version": EXECUTION_RECORD_SCHEMA_VERSION,
        "record_kind": "PRECONDITION_STOP",
        "target_access_state": "LOCKED_RESERVED_NOT_CONSUMED",
        "execution_authority_state": "REVIEW_PENDING",
        "execution_authorization_reservation_consumed": False,
    }
    values.update(overrides)
    return ExecutionRecord(**values)  # type: ignore[arg-type]


def test_execution_record_keeps_ledgers_independent() -> None:
    validate_execution_record(_production_record())
    validate_execution_record(
        _production_record(
            target_access_state="CONSUMED",
            execution_authority_state="NOT_AUTHORIZED",
        )
    )
    validate_execution_record(
        _production_record(
            target_access_state="LOCKED_UNRESERVED",
            execution_authority_state="TERMINAL_NO_RETRY",
        )
    )


def test_production_and_rehearsal_states_cannot_cross_classes() -> None:
    with pytest.raises(RecordValidationError) as production_error:
        validate_execution_record(
            _production_record(target_access_state=REHEARSAL_TARGET_ACCESS_STATE)
        )
    _assert_reason(production_error, RecordReasonCode.TARGET_ACCESS_STATE_INVALID)

    rehearsal = ExecutionRecord(
        schema_version=EXECUTION_RECORD_SCHEMA_VERSION,
        record_kind="REHEARSAL",
        target_access_state=REHEARSAL_TARGET_ACCESS_STATE,
        execution_authority_state=REHEARSAL_EXECUTION_AUTHORITY_STATE,
        execution_authorization_reservation_consumed=False,
    )
    validate_execution_record(rehearsal)

    with pytest.raises(RecordValidationError) as rehearsal_error:
        validate_execution_record(
            ExecutionRecord(
                schema_version=EXECUTION_RECORD_SCHEMA_VERSION,
                record_kind="REHEARSAL",
                target_access_state="LOCKED_UNRESERVED",
                execution_authority_state=REHEARSAL_EXECUTION_AUTHORITY_STATE,
                execution_authorization_reservation_consumed=False,
            )
        )
    _assert_reason(rehearsal_error, RecordReasonCode.TARGET_ACCESS_STATE_INVALID)


def test_reservation_boolean_must_match_authority_state() -> None:
    with pytest.raises(RecordValidationError) as false_state_error:
        validate_execution_record(
            _production_record(execution_authorization_reservation_consumed=True)
        )
    _assert_reason(false_state_error, RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH)

    with pytest.raises(RecordValidationError) as true_state_error:
        validate_execution_record(
            _production_record(
                execution_authority_state="RESERVATION_CONSUMED",
                execution_authorization_reservation_consumed=False,
            )
        )
    _assert_reason(true_state_error, RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH)


def test_attempt_ledger_schema_is_closed_and_two_ledger_explicit() -> None:
    schema_path = (
        PROJECT_ROOT / "configs/governance/execution_hardening_attempt_ledger_schema_v1.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["target_access_state"]["const"] == (
        "NOT_APPLICABLE_SYNTHETIC_REHEARSAL"
    )
    assert schema["properties"]["execution_authority_state"]["const"] == (
        "REHEARSAL_ONLY_NO_SCIENTIFIC_AUTHORITY"
    )
    assert schema["properties"]["execution_authorization_reservation_consumed"] == {
        "type": "boolean"
    }
    assert {
        "target_access_state",
        "execution_authority_state",
        "execution_authorization_reservation_consumed",
    }.issubset(schema["required"])
    false_branch = schema["allOf"][0]["then"]["properties"]["attempt_outcome"]["enum"]
    true_branch = schema["allOf"][1]["then"]["properties"]["attempt_outcome"]["enum"]
    assert "TERMINAL_NO_RETRY" in false_branch
    assert "TERMINAL_NO_RETRY" in true_branch
    assert "COMPLETED_SEALED" not in false_branch
    assert "OPEN" not in true_branch

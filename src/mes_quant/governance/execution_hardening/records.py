"""Closed execution records and transition validation for Execution Hardening V1."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

EXECUTION_RECORD_SCHEMA_VERSION = "MES_EXECUTION_RECORD_SCHEMA_V1"
PROTOCOL_SHA256 = "697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7"
TRANSITION_COMPANION_SHA256 = (
    "00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1"
)
PROTOCOL_RELATIVE_PATH = Path("docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md")
TRANSITION_COMPANION_RELATIVE_PATH = Path(
    "configs/governance/execution_hardening_transition_rows_v3.json"
)

PRODUCTION_RECORD_KINDS = frozenset(
    {"PRECONDITION_STOP", "STAGE_SUCCESS", "STAGE_TERMINAL"}
)
REHEARSAL_RECORD_KIND = "REHEARSAL"
TARGET_ACCESS_STATES = (
    "LOCKED_UNRESERVED",
    "LOCKED_RESERVED_NOT_CONSUMED",
    "CONSUMED",
    "CLOSED_UNCONSUMED",
    "ACCESS_NOT_ATTESTED_FAIL_CLOSED",
)
REHEARSAL_TARGET_ACCESS_STATE = "NOT_APPLICABLE_SYNTHETIC_REHEARSAL"
EXECUTION_AUTHORITY_STATES = (
    "NOT_AUTHORIZED",
    "REVIEW_PENDING",
    "AUTHORIZED_UNUSED",
    "RESERVATION_CONSUMED",
    "COMPLETED_SEALED",
    "TERMINAL_NO_RETRY",
    "NOT_ATTESTED_FAIL_CLOSED",
)
REHEARSAL_EXECUTION_AUTHORITY_STATE = "REHEARSAL_ONLY_NO_SCIENTIFIC_AUTHORITY"

_FALSE_ONLY_AUTHORITY_STATES = frozenset(
    {"NOT_AUTHORIZED", "REVIEW_PENDING", "AUTHORIZED_UNUSED", "NOT_ATTESTED_FAIL_CLOSED"}
)
_TRUE_ONLY_AUTHORITY_STATES = frozenset({"RESERVATION_CONSUMED", "COMPLETED_SEALED"})
_RESERVATION_CONSUMPTION_EVENT_IDS = frozenset(
    {"AUTH_ROW_151", "AUTH_ROW_152", "AUTH_ROW_154"}
)
_STATE_TOKEN_RE = re.compile(r"[A-Z][A-Z0-9_]+")


class RecordReasonCode(StrEnum):
    """Closed machine reasons emitted by this module."""

    EXECUTION_RECORD_SCHEMA_INVALID = "EXECUTION_RECORD_SCHEMA_INVALID"
    EXECUTION_RECORD_KIND_INVALID = "EXECUTION_RECORD_KIND_INVALID"
    TARGET_ACCESS_STATE_INVALID = "TARGET_ACCESS_STATE_INVALID"
    EXECUTION_AUTHORITY_STATE_INVALID = "EXECUTION_AUTHORITY_STATE_INVALID"
    RESERVATION_BOOLEAN_TYPE_INVALID = "RESERVATION_BOOLEAN_TYPE_INVALID"
    RESERVATION_BOOLEAN_STATE_MISMATCH = "RESERVATION_BOOLEAN_STATE_MISMATCH"
    RESERVATION_BOOLEAN_EVENT_MISMATCH = "RESERVATION_BOOLEAN_EVENT_MISMATCH"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    TRANSITION_COMPANION_SHA256_MISMATCH = "TRANSITION_COMPANION_SHA256_MISMATCH"
    TRANSITION_PROTOCOL_SHA256_MISMATCH = "TRANSITION_PROTOCOL_SHA256_MISMATCH"
    TRANSITION_COMPANION_INVALID = "TRANSITION_COMPANION_INVALID"
    TRANSITION_PROTOCOL_EQUIVALENCE_FAILED = "TRANSITION_PROTOCOL_EQUIVALENCE_FAILED"
    TRANSITION_REASON_CODE_REQUIRED = "TRANSITION_REASON_CODE_REQUIRED"
    UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION = (
        "UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION"
    )


class RecordValidationError(ValueError):
    """Fail-closed record/transition error with an exact reason code."""

    def __init__(self, reason_code: RecordReasonCode, detail: str) -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code.value}: {detail}")


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """The closed two-ledger core required in every governed execution record."""

    schema_version: str
    record_kind: str
    target_access_state: str
    execution_authority_state: str
    execution_authorization_reservation_consumed: bool


def validate_execution_record(record: ExecutionRecord) -> None:
    """Validate the two ledgers independently and reject cross-class marker mixing."""

    if not isinstance(record, ExecutionRecord) or (
        record.schema_version != EXECUTION_RECORD_SCHEMA_VERSION
    ):
        raise RecordValidationError(
            RecordReasonCode.EXECUTION_RECORD_SCHEMA_INVALID,
            "record must use MES_EXECUTION_RECORD_SCHEMA_V1",
        )
    if not isinstance(record.execution_authorization_reservation_consumed, bool):
        raise RecordValidationError(
            RecordReasonCode.RESERVATION_BOOLEAN_TYPE_INVALID,
            "reservation-consumed fact must be bool",
        )

    if record.record_kind == REHEARSAL_RECORD_KIND:
        if record.target_access_state != REHEARSAL_TARGET_ACCESS_STATE:
            raise RecordValidationError(
                RecordReasonCode.TARGET_ACCESS_STATE_INVALID,
                "rehearsal records require the rehearsal-only target-access state",
            )
        if record.execution_authority_state != REHEARSAL_EXECUTION_AUTHORITY_STATE:
            raise RecordValidationError(
                RecordReasonCode.EXECUTION_AUTHORITY_STATE_INVALID,
                "rehearsal records require the non-scientific authority state",
            )
        return

    if not isinstance(record.record_kind, str) or record.record_kind not in PRODUCTION_RECORD_KINDS:
        raise RecordValidationError(
            RecordReasonCode.EXECUTION_RECORD_KIND_INVALID,
            "record_kind is outside the closed production/rehearsal set",
        )
    if (
        not isinstance(record.target_access_state, str)
        or record.target_access_state not in TARGET_ACCESS_STATES
    ):
        raise RecordValidationError(
            RecordReasonCode.TARGET_ACCESS_STATE_INVALID,
            "production record uses an unknown or rehearsal target-access state",
        )
    if (
        not isinstance(record.execution_authority_state, str)
        or record.execution_authority_state not in EXECUTION_AUTHORITY_STATES
    ):
        raise RecordValidationError(
            RecordReasonCode.EXECUTION_AUTHORITY_STATE_INVALID,
            "production record uses an unknown or rehearsal authority state",
        )

    consumed = record.execution_authorization_reservation_consumed
    if record.execution_authority_state in _FALSE_ONLY_AUTHORITY_STATES and consumed:
        raise RecordValidationError(
            RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH,
            "pre-reservation authority state cannot erase its unused meaning",
        )
    if record.execution_authority_state in _TRUE_ONLY_AUTHORITY_STATES and not consumed:
        raise RecordValidationError(
            RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH,
            "post-reservation authority state requires the monotone consumed fact",
        )


@dataclass(frozen=True, slots=True)
class TransitionRow:
    event_id: str
    source_line: int
    event_text: str
    from_states: tuple[str, ...]
    to_by_from: tuple[tuple[str, str], ...]

    @property
    def transition_map(self) -> dict[str, str]:
        return dict(self.to_by_from)


@dataclass(frozen=True, slots=True)
class TransitionContract:
    target_states: tuple[str, ...]
    execution_states: tuple[str, ...]
    target_rows: tuple[TransitionRow, ...]
    execution_rows: tuple[TransitionRow, ...]
    reason_mapping_assertions: tuple[dict[str, Any], ...]
    protocol_sha256: str
    companion_sha256: str

    def rows(self, ledger: str) -> tuple[TransitionRow, ...]:
        if ledger == "target_access":
            return self.target_rows
        if ledger == "execution_authority":
            return self.execution_rows
        raise RecordValidationError(
            RecordReasonCode.INVALID_TRANSITION,
            f"unknown ledger {ledger!r}",
        )

    def states(self, ledger: str) -> tuple[str, ...]:
        if ledger == "target_access":
            return self.target_states
        if ledger == "execution_authority":
            return self.execution_states
        raise RecordValidationError(
            RecordReasonCode.INVALID_TRANSITION,
            f"unknown ledger {ledger!r}",
        )


@dataclass(frozen=True, slots=True)
class TransitionResult:
    state: str
    execution_authorization_reservation_consumed: bool
    reason_code: str | None
    individual_attempt_stops: bool


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_COMPANION_INVALID,
                f"duplicate JSON member {key!r}",
            )
        result[key] = value
    return result


def _decode_companion(data: bytes) -> dict[str, Any]:
    try:
        decoded = json.loads(data, object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "transition companion is not strict JSON",
        ) from exc
    if not isinstance(decoded, dict):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "transition companion root must be an object",
        )
    return decoded


def _strip_inline_code_delimiters(cell: str) -> str:
    result: list[str] = []
    in_code = False
    for character in cell.strip(" \t"):
        if character == "`":
            in_code = not in_code
            continue
        result.append(character)
    if in_code:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            "unclosed Markdown inline-code delimiter",
        )
    return "".join(result)


def _protocol_cells(line: str, source_line: int) -> tuple[str, str, str]:
    if not line.startswith("|") or not line.endswith("|"):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            f"protocol line {source_line} is not a Markdown data row",
        )
    raw_cells = line[1:-1].split("|")
    if len(raw_cells) != 3:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            f"protocol line {source_line} does not have exactly three cells",
        )
    return tuple(_strip_inline_code_delimiters(cell) for cell in raw_cells)  # type: ignore[return-value]


def _states_from_cell(cell: str, allowed_states: tuple[str, ...], source_line: int) -> list[str]:
    states = [token for token in _STATE_TOKEN_RE.findall(cell) if token in allowed_states]
    if not states or len(states) != len(set(states)):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            f"protocol line {source_line} has invalid From-state expansion",
        )
    return states


def _to_by_from(
    to_cell: str,
    from_states: list[str],
    allowed_states: tuple[str, ...],
    source_line: int,
) -> dict[str, str]:
    if to_cell.startswith("unchanged"):
        return {state: state for state in from_states}
    match = _STATE_TOKEN_RE.match(to_cell)
    if match is None or match.group(0) not in allowed_states:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            f"protocol line {source_line} has invalid To state",
        )
    destination = match.group(0)
    return {state: destination for state in from_states}


def _parse_rows(
    section: Any,
    *,
    expected_states: tuple[str, ...],
    protocol_lines: list[str],
    expected_prefix: str,
    expected_line_range: range,
) -> tuple[TransitionRow, ...]:
    if not isinstance(section, dict) or set(section) != {"states", "protocol_rows"}:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            f"{expected_prefix} section is not closed",
        )
    if section["states"] != list(expected_states) or not isinstance(section["protocol_rows"], list):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            f"{expected_prefix} state set/order differs from the protocol",
        )

    rows: list[TransitionRow] = []
    expected_lines = list(expected_line_range)
    if len(section["protocol_rows"]) != len(expected_lines):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            f"{expected_prefix} companion row count differs",
        )

    for item, source_line in zip(section["protocol_rows"], expected_lines, strict=True):
        if not isinstance(item, dict) or set(item) != {
            "event_id",
            "source_line",
            "event_text",
            "from",
            "to_by_from",
        }:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_COMPANION_INVALID,
                f"{expected_prefix} row {source_line} has unknown/missing fields",
            )
        event_id = f"{expected_prefix}_ROW_{source_line}"
        if item["event_id"] != event_id or item["source_line"] != source_line:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
                f"companion row identity does not match protocol line {source_line}",
            )
        from_cell, event_cell, to_cell = _protocol_cells(
            protocol_lines[source_line - 1], source_line
        )
        from_states = _states_from_cell(from_cell, expected_states, source_line)
        to_by_from = _to_by_from(to_cell, from_states, expected_states, source_line)
        if item["event_text"] != event_cell:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
                f"event text mismatch at protocol line {source_line}",
            )
        if item["from"] != from_states or item["to_by_from"] != to_by_from:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
                f"mechanical From/To expansion mismatch at line {source_line}",
            )
        rows.append(
            TransitionRow(
                event_id=event_id,
                source_line=source_line,
                event_text=event_cell,
                from_states=tuple(from_states),
                to_by_from=tuple(to_by_from.items()),
            )
        )
    return tuple(rows)


_EXPECTED_REASON_ASSERTIONS: tuple[dict[str, Any], ...] = (
    {
        "source_line": 131,
        "requirement": (
            "identity transition remains unchanged and the terminal record reports missing "
            "access evidence in its reason code"
        ),
    },
    {
        "source_line": 149,
        "requirement": (
            "the invalid attempt stops individually while the package remains REVIEW_PENDING "
            "only under the row's stated remaining-attempt and no-reservation/no-access conditions"
        ),
    },
    {
        "source_line": 151,
        "reason_code": "UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION",
    },
    {
        "source_line": 152,
        "reason_code": "UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION",
        "inheritance": "same unauthorized-reservation reason as source line 151",
    },
)

_EXPECTED_TO_QUALIFIERS = {
    131: "unchanged; record missing evidence in the reason code",
    149: "REVIEW_PENDING; individual attempt stops",
    151: "TERMINAL_NO_RETRY; reason UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION",
    152: "TERMINAL_NO_RETRY; same unauthorized-reservation reason",
}


def _validate_reason_assertions(
    payload: dict[str, Any], protocol_lines: list[str]
) -> tuple[dict[str, Any], ...]:
    assertions = payload.get("reason_mapping_assertions")
    if assertions != list(_EXPECTED_REASON_ASSERTIONS):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            "reason-mapping assertions differ from the ratified companion",
        )
    for source_line, expected_to_cell in _EXPECTED_TO_QUALIFIERS.items():
        _, _, actual_to_cell = _protocol_cells(protocol_lines[source_line - 1], source_line)
        if actual_to_cell != expected_to_cell:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
                f"To-cell qualifier mismatch at protocol line {source_line}",
            )
    return tuple(assertions)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_transition_contract(repository_root: Path | None = None) -> TransitionContract:
    """Load only the co-ratified companion and prove exact Markdown equivalence."""

    root = (repository_root or _project_root()).resolve()
    companion_bytes = (root / TRANSITION_COMPANION_RELATIVE_PATH).read_bytes()
    protocol_bytes = (root / PROTOCOL_RELATIVE_PATH).read_bytes()

    companion_sha256 = hashlib.sha256(companion_bytes).hexdigest()
    if companion_sha256 != TRANSITION_COMPANION_SHA256:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_SHA256_MISMATCH,
            "transition companion does not match the co-ratified SHA-256",
        )
    protocol_sha256 = hashlib.sha256(protocol_bytes).hexdigest()
    if protocol_sha256 != PROTOCOL_SHA256:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_SHA256_MISMATCH,
            "governing protocol does not match the co-ratified SHA-256",
        )

    payload = _decode_companion(companion_bytes)
    required_top_level = {
        "schema_version",
        "status",
        "authority",
        "supersedes_for_future_authorization_only",
        "governing_protocol_id",
        "governing_protocol_path",
        "governing_protocol_sha256",
        "source_extraction_rule",
        "equivalence_rule",
        "unknown_event_policy",
        "target_access",
        "execution_authority",
        "reason_mapping_assertions",
        "required_equivalence_test",
    }
    if set(payload) != required_top_level:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "transition companion top-level field set is not closed",
        )
    if (
        payload["schema_version"] != "MES_EXECUTION_TRANSITION_ROW_ENUM_V3"
        or payload["governing_protocol_id"] != "MES_EXECUTION_HARDENING_PROTOCOL_V1"
        or payload["governing_protocol_path"] != PROTOCOL_RELATIVE_PATH.as_posix()
        or payload["governing_protocol_sha256"] != PROTOCOL_SHA256
        or payload["unknown_event_policy"] != "REJECT_INVALID_TRANSITION"
    ):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "transition companion identity/binding/policy mismatch",
        )

    protocol_lines = protocol_bytes.decode("utf-8", errors="strict").splitlines()
    target_rows = _parse_rows(
        payload["target_access"],
        expected_states=TARGET_ACCESS_STATES,
        protocol_lines=protocol_lines,
        expected_prefix="TARGET",
        expected_line_range=range(123, 137),
    )
    execution_section = payload["execution_authority"]
    if not isinstance(execution_section, dict):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "execution-authority section must be an object",
        )
    execution_section = dict(execution_section)
    reservation_rule = execution_section.pop("reservation_boolean_rule", None)
    if reservation_rule != (
        "false changes to true on any actual execution-authorization reservation consumption "
        "and never returns to false"
    ):
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_COMPANION_INVALID,
            "reservation boolean rule differs from the ratified companion",
        )
    execution_rows = _parse_rows(
        execution_section,
        expected_states=EXECUTION_AUTHORITY_STATES,
        protocol_lines=protocol_lines,
        expected_prefix="AUTH",
        expected_line_range=range(142, 162),
    )
    if sum(len(row.from_states) for row in target_rows) != 18:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            "target transition expansion is not exactly 18 triples",
        )
    if sum(len(row.from_states) for row in execution_rows) != 22:
        raise RecordValidationError(
            RecordReasonCode.TRANSITION_PROTOCOL_EQUIVALENCE_FAILED,
            "execution transition expansion is not exactly 22 triples",
        )
    reason_assertions = _validate_reason_assertions(payload, protocol_lines)
    return TransitionContract(
        target_states=TARGET_ACCESS_STATES,
        execution_states=EXECUTION_AUTHORITY_STATES,
        target_rows=target_rows,
        execution_rows=execution_rows,
        reason_mapping_assertions=reason_assertions,
        protocol_sha256=protocol_sha256,
        companion_sha256=companion_sha256,
    )


def apply_transition(
    contract: TransitionContract,
    *,
    ledger: str,
    current_state: str,
    event_id: str,
    execution_authorization_reservation_consumed: bool,
    missing_access_reason_code: str | None = None,
) -> TransitionResult:
    """Apply one finite event without inferring or granting authority."""

    if not isinstance(execution_authorization_reservation_consumed, bool):
        raise RecordValidationError(
            RecordReasonCode.RESERVATION_BOOLEAN_TYPE_INVALID,
            "reservation-consumed fact must be bool",
        )
    if not isinstance(current_state, str) or not isinstance(event_id, str):
        raise RecordValidationError(
            RecordReasonCode.INVALID_TRANSITION,
            "transition state and event must be strings",
        )
    if ledger == "execution_authority":
        if current_state in _FALSE_ONLY_AUTHORITY_STATES and (
            execution_authorization_reservation_consumed
        ):
            raise RecordValidationError(
                RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH,
                "pre-reservation authority state cannot carry a consumed reservation",
            )
        if current_state in _TRUE_ONLY_AUTHORITY_STATES and not (
            execution_authorization_reservation_consumed
        ):
            raise RecordValidationError(
                RecordReasonCode.RESERVATION_BOOLEAN_STATE_MISMATCH,
                "post-reservation authority state requires the consumed reservation fact",
            )

    rows = {row.event_id: row for row in contract.rows(ledger)}
    row = rows.get(event_id)
    if row is None or current_state not in row.transition_map:
        raise RecordValidationError(
            RecordReasonCode.INVALID_TRANSITION,
            f"unlisted transition ({ledger}, {current_state}, {event_id})",
        )

    next_state = row.transition_map[current_state]
    consumed = execution_authorization_reservation_consumed
    reason_code: str | None = None
    individual_attempt_stops = event_id == "AUTH_ROW_149"

    if ledger == "execution_authority" and event_id in _RESERVATION_CONSUMPTION_EVENT_IDS:
        consumed = True
        if event_id in {"AUTH_ROW_151", "AUTH_ROW_152"}:
            reason_code = RecordReasonCode.UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION.value
    if ledger == "target_access" and event_id == "TARGET_ROW_131":
        if not missing_access_reason_code:
            raise RecordValidationError(
                RecordReasonCode.TRANSITION_REASON_CODE_REQUIRED,
                "TARGET_ROW_131 requires a non-empty missing-evidence reason code",
            )
        reason_code = missing_access_reason_code

    if ledger == "execution_authority":
        if next_state in _FALSE_ONLY_AUTHORITY_STATES and consumed:
            raise RecordValidationError(
                RecordReasonCode.RESERVATION_BOOLEAN_EVENT_MISMATCH,
                "non-consumption transition produced an impossible consumed fact",
            )
        if next_state in _TRUE_ONLY_AUTHORITY_STATES and not consumed:
            raise RecordValidationError(
                RecordReasonCode.RESERVATION_BOOLEAN_EVENT_MISMATCH,
                "consumption transition failed to preserve the consumed fact",
            )

    return TransitionResult(
        state=next_state,
        execution_authorization_reservation_consumed=consumed,
        reason_code=reason_code,
        individual_attempt_stops=individual_attempt_stops,
    )

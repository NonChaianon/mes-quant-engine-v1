"""Pure Phase-A implementation of the Section 6.1 reviewer gate.

This module deliberately performs no network, OIDC, Sigstore, or signing operation.  A
caller must inject a trust policy.  Phase A provides an in-memory fixture policy and a
runtime reject-all policy only; neither can create execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

REVIEW_PENDING = "REVIEW_PENDING"
NOT_ATTESTED_FAIL_CLOSED = "NOT_ATTESTED_FAIL_CLOSED"
TERMINAL_NO_RETRY = "TERMINAL_NO_RETRY"

MISSING = "REVIEW_ATTESTATION_MISSING_STOP_BEFORE_RESERVATION"
PACKAGE_MISMATCH = "REVIEW_ATTESTATION_PACKAGE_MISMATCH_STOP_BEFORE_RESERVATION"
NO_VERDICT = "REVIEW_ATTESTATION_NO_VERDICT_STOP_BEFORE_RESERVATION"
REJECTED = "REVIEW_ATTESTATION_REJECTED_STOP_BEFORE_RESERVATION"
EXPIRED = "REVIEW_ATTESTATION_EXPIRED_STOP_BEFORE_RESERVATION"
SIGNER_INVALID = "REVIEW_ATTESTATION_SIGNER_INVALID_STOP_BEFORE_RESERVATION"
REVIEWER_MISMATCH = "REVIEW_ATTESTATION_REVIEWER_IDENTITY_MISMATCH_STOP_BEFORE_RESERVATION"
REPORT_MISMATCH = "REVIEW_ATTESTATION_REPORT_BINDING_MISMATCH_STOP_BEFORE_RESERVATION"
PACKET_MODE_INVALID = "REVIEW_ATTESTATION_PACKET_MODE_INVALID_STOP_BEFORE_RESERVATION"
REPLAY = "REVIEW_ATTESTATION_REPLAY_STOP_BEFORE_RESERVATION"
PASS = "REVIEW_ATTESTATION_GATE_PASS_OWNER_AUTHORIZATION_STILL_REQUIRED"

FULL_GOVERNED = "FULL_GOVERNED"
MAXIMUM_TOKEN_AGE_SECONDS = 300
MAXIMUM_CLOCK_SKEW_SECONDS = 60
MAXIMUM_ATTESTATION_AGE_SECONDS = 1800

AUTHORIZATION_RELEVANT_FIELDS = frozenset(
    {
        "repository_identity",
        "branch",
        "commit",
        "tree",
        "diff_base",
        "exact_allowlist",
        "ordered_file_sha256_values",
        "reviewer_identity",
        "provider",
        "model",
        "tool_runtime_version",
        "review_role",
        "clause_packet_sha256",
        "clause_packet_operating_mode",
        "report_sha256",
        "verdict",
        "blocker_count",
        "high_count",
        "completion_status",
        "issued_timestamp",
        "bounded_expiry",
        "trusted_time_source_identity",
        "trusted_signature_or_service_receipt",
    }
)

_PACKAGE_FIELDS = (
    "repository_identity",
    "branch",
    "commit",
    "tree",
    "diff_base",
)
_REVIEWER_FIELDS = (
    "reviewer_identity",
    "provider",
    "model",
    "tool_runtime_version",
    "review_role",
)
_REPORT_FIELDS = (
    "clause_packet_sha256",
    "report_sha256",
)
_SIGNER_AND_TIME_FIELDS = (
    "trusted_signature_or_service_receipt",
    "trusted_time_source_identity",
    "issued_timestamp",
    "bounded_expiry",
)
_VERDICT_FIELDS = (
    "verdict",
    "blocker_count",
    "high_count",
    "completion_status",
)


@dataclass(frozen=True)
class AttestationExpectation:
    """Exact identities that a Section 6.1 attestation must bind."""

    repository_identity: str
    branch: str
    commit: str
    tree: str
    diff_base: str
    exact_allowlist: tuple[str, ...]
    ordered_file_sha256_values: tuple[str, ...]
    reviewer_identity: str
    provider: str
    model: str
    tool_runtime_version: str
    review_role: str
    clause_packet_sha256: str
    report_sha256: str
    trusted_time_source_identity: str


@dataclass(frozen=True)
class AttestationDecision:
    """Fail-closed pre-reservation result with no implied Owner authority."""

    passed: bool
    reason_code: str
    execution_authority_state: str
    reservation_created: bool = False
    owner_authority_implied: bool = False


@runtime_checkable
class AttestationTrustPolicy(Protocol):
    """Injected trust predicate; implementations must not perform hidden I/O."""

    policy_id: str
    runtime_authority_enabled: bool

    def accepts(self, receipt: str) -> bool:
        """Return whether an already-verified receipt is accepted by this policy."""


@dataclass(frozen=True)
class InMemoryAttestationTrustPolicy:
    """Exact receipt matcher for deterministic Tier-1 fixtures only."""

    expected_receipt: str
    policy_id: str = "MES_TEST_FIXTURE_ATTESTATION_POLICY_V1"
    runtime_authority_enabled: bool = False

    def accepts(self, receipt: str) -> bool:
        return bool(receipt) and receipt == self.expected_receipt


@dataclass(frozen=True)
class RuntimeRejectAllAttestationPolicy:
    """Phase-A runtime posture: no trusted signer/root has been activated."""

    policy_id: str = "NOT_YET_RATIFIED_ATTESTATION_TRUST_ROOT"
    runtime_authority_enabled: bool = False

    def accepts(self, receipt: str) -> bool:
        del receipt
        return False


def _failure_state(attempts_remaining: int) -> str:
    return REVIEW_PENDING if attempts_remaining > 0 else NOT_ATTESTED_FAIL_CLOSED


def _stop(reason_code: str, attempts_remaining: int) -> AttestationDecision:
    return AttestationDecision(
        passed=False,
        reason_code=reason_code,
        execution_authority_state=_failure_state(attempts_remaining),
    )


def _closed_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _closed_timestamp(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sequence_matches(value: object, expected: tuple[str, ...]) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value) and tuple(
        value
    ) == expected


def _expectation_value(expectation: AttestationExpectation, field: str) -> object:
    return getattr(expectation, field)


def _missing_field_outcome(missing: set[str]) -> str:
    """Map missing V1 fields to the exact Section 6.1 failure class."""

    if "clause_packet_operating_mode" in missing:
        return PACKET_MODE_INVALID
    if missing.intersection(_SIGNER_AND_TIME_FIELDS):
        return SIGNER_INVALID
    if missing.intersection(_REVIEWER_FIELDS):
        return REVIEWER_MISMATCH
    if missing.intersection(_REPORT_FIELDS):
        return REPORT_MISMATCH
    if missing.intersection(_VERDICT_FIELDS):
        return NO_VERDICT
    return PACKAGE_MISMATCH


def evaluate_pre_reservation_attestation(
    attestation: Mapping[str, object] | None,
    *,
    expectation: AttestationExpectation,
    trust_policy: AttestationTrustPolicy,
    current_iat: int,
    current_time_token_age_seconds: int,
    attempts_remaining: int,
    replayed_receipts: frozenset[str] = frozenset(),
) -> AttestationDecision:
    """Evaluate all Section 6.1 outcomes without creating a reservation.

    ``current_iat`` represents the already issuer/audience/signature-verified GitHub OIDC
    ``iat`` supplied by the caller.  Phase A tests it as an integer fixture; this function
    never obtains a token or contacts an identity provider.
    """

    if not _closed_nonnegative_int(attempts_remaining):
        raise ValueError("attempts_remaining must be a non-negative integer")

    if attestation is None:
        return _stop(MISSING, attempts_remaining)

    if not isinstance(attestation, Mapping):
        return _stop(PACKAGE_MISMATCH, attempts_remaining)
    actual_fields = set(attestation)
    extra_fields = actual_fields.difference(AUTHORIZATION_RELEVANT_FIELDS)
    if extra_fields:
        return _stop(PACKAGE_MISMATCH, attempts_remaining)
    missing_fields = AUTHORIZATION_RELEVANT_FIELDS.difference(actual_fields)
    if missing_fields:
        return _stop(_missing_field_outcome(missing_fields), attempts_remaining)

    for field in _PACKAGE_FIELDS:
        if attestation[field] != _expectation_value(expectation, field):
            return _stop(PACKAGE_MISMATCH, attempts_remaining)

    if not _sequence_matches(attestation["exact_allowlist"], expectation.exact_allowlist):
        return _stop(PACKAGE_MISMATCH, attempts_remaining)
    if not _sequence_matches(
        attestation["ordered_file_sha256_values"],
        expectation.ordered_file_sha256_values,
    ):
        return _stop(PACKAGE_MISMATCH, attempts_remaining)

    completion_status = attestation["completion_status"]
    verdict = attestation["verdict"]
    if completion_status in {"TIMEOUT", "NO_VERDICT"} or verdict == "NO_VERDICT":
        return _stop(NO_VERDICT, attempts_remaining)
    if completion_status != "COMPLETED" or verdict not in {"PASS", "REJECTED"}:
        return _stop(NO_VERDICT, attempts_remaining)

    receipt = attestation["trusted_signature_or_service_receipt"]
    if not isinstance(receipt, str) or not trust_policy.accepts(receipt):
        return _stop(SIGNER_INVALID, attempts_remaining)
    if trust_policy.runtime_authority_enabled:
        # No Phase-A policy is allowed to claim runtime authority.
        return _stop(SIGNER_INVALID, attempts_remaining)

    if attestation["trusted_time_source_identity"] != expectation.trusted_time_source_identity:
        return _stop(SIGNER_INVALID, attempts_remaining)
    if (
        not _closed_nonnegative_int(current_time_token_age_seconds)
        or current_time_token_age_seconds > MAXIMUM_TOKEN_AGE_SECONDS
        or not _closed_timestamp(current_iat)
    ):
        return _stop(SIGNER_INVALID, attempts_remaining)

    for field in _REVIEWER_FIELDS:
        if attestation[field] != _expectation_value(expectation, field):
            return _stop(REVIEWER_MISMATCH, attempts_remaining)

    for field in _REPORT_FIELDS:
        if attestation[field] != _expectation_value(expectation, field):
            return _stop(REPORT_MISMATCH, attempts_remaining)

    if attestation["clause_packet_operating_mode"] != FULL_GOVERNED:
        return _stop(PACKET_MODE_INVALID, attempts_remaining)

    if receipt in replayed_receipts:
        return _stop(REPLAY, attempts_remaining)

    issued_at = attestation["issued_timestamp"]
    bounded_expiry = attestation["bounded_expiry"]
    if not _closed_timestamp(issued_at) or not _closed_timestamp(bounded_expiry):
        return _stop(SIGNER_INVALID, attempts_remaining)
    if (
        issued_at > current_iat + MAXIMUM_CLOCK_SKEW_SECONDS
        or current_iat >= bounded_expiry
        or current_iat - issued_at > MAXIMUM_ATTESTATION_AGE_SECONDS
    ):
        return _stop(EXPIRED, attempts_remaining)

    blocker_count = attestation["blocker_count"]
    high_count = attestation["high_count"]
    if not _closed_nonnegative_int(blocker_count) or not _closed_nonnegative_int(high_count):
        return _stop(REJECTED, attempts_remaining)
    if verdict == "REJECTED" or blocker_count > 0 or high_count > 0:
        return AttestationDecision(
            passed=False,
            reason_code=REJECTED,
            execution_authority_state=TERMINAL_NO_RETRY,
        )

    return AttestationDecision(
        passed=True,
        reason_code=PASS,
        execution_authority_state=REVIEW_PENDING,
    )

from __future__ import annotations

import copy

import pytest

from mes_quant.governance.execution_hardening import attestation


def _expectation() -> attestation.AttestationExpectation:
    return attestation.AttestationExpectation(
        repository_identity="NonChaianon/mes-quant-engine-v1",
        branch="refs/heads/governance/execution-hardening-step3-v1",
        commit="a" * 40,
        tree="b" * 40,
        diff_base="c" * 40,
        exact_allowlist=("a.py", "b.py"),
        ordered_file_sha256_values=(f"a.py\t{'1' * 64}", f"b.py\t{'2' * 64}"),
        reviewer_identity="EXECUTION_HARDENING_DETERMINISTIC_REVIEWER_V1",
        provider="GitHub Actions OIDC / Sigstore",
        model="NONE_DETERMINISTIC_RULE_ENGINE",
        tool_runtime_version="gh 2.97.0",
        review_role="SECTION6_DETERMINISTIC_RELEASE_REVIEWER",
        clause_packet_sha256="3" * 64,
        report_sha256="4" * 64,
        trusted_time_source_identity="MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1",
    )


def _valid_attestation() -> dict[str, object]:
    expected = _expectation()
    return {
        "repository_identity": expected.repository_identity,
        "branch": expected.branch,
        "commit": expected.commit,
        "tree": expected.tree,
        "diff_base": expected.diff_base,
        "exact_allowlist": list(expected.exact_allowlist),
        "ordered_file_sha256_values": list(expected.ordered_file_sha256_values),
        "reviewer_identity": expected.reviewer_identity,
        "provider": expected.provider,
        "model": expected.model,
        "tool_runtime_version": expected.tool_runtime_version,
        "review_role": expected.review_role,
        "clause_packet_sha256": expected.clause_packet_sha256,
        "clause_packet_operating_mode": "FULL_GOVERNED",
        "report_sha256": expected.report_sha256,
        "verdict": "PASS",
        "blocker_count": 0,
        "high_count": 0,
        "completion_status": "COMPLETED",
        "issued_timestamp": 1_000,
        "bounded_expiry": 2_000,
        "trusted_time_source_identity": expected.trusted_time_source_identity,
        "trusted_signature_or_service_receipt": "fixture-receipt",
    }


def _evaluate(
    candidate: dict[str, object] | None,
    *,
    attempts_remaining: int,
    trust_policy: attestation.AttestationTrustPolicy | None = None,
    current_iat: int = 1_100,
    token_age: int = 0,
    replayed: frozenset[str] = frozenset(),
) -> attestation.AttestationDecision:
    return attestation.evaluate_pre_reservation_attestation(
        candidate,
        expectation=_expectation(),
        trust_policy=trust_policy
        or attestation.InMemoryAttestationTrustPolicy("fixture-receipt"),
        current_iat=current_iat,
        current_time_token_age_seconds=token_age,
        attempts_remaining=attempts_remaining,
        replayed_receipts=replayed,
    )


@pytest.mark.parametrize(
    ("attempts_remaining", "expected_state"),
    [(1, attestation.REVIEW_PENDING), (0, attestation.NOT_ATTESTED_FAIL_CLOSED)],
)
def test_missing_attestation_has_both_attempt_budget_outcomes(
    attempts_remaining: int,
    expected_state: str,
) -> None:
    decision = _evaluate(None, attempts_remaining=attempts_remaining)

    assert not decision.passed
    assert decision.reason_code == attestation.MISSING
    assert decision.execution_authority_state == expected_state
    assert not decision.reservation_created


def _package_mismatch(candidate: dict[str, object]) -> None:
    candidate["commit"] = "f" * 40


def _signer_invalid(candidate: dict[str, object]) -> None:
    candidate["trusted_signature_or_service_receipt"] = "wrong-receipt"


def _reviewer_mismatch(candidate: dict[str, object]) -> None:
    candidate["reviewer_identity"] = "OTHER_REVIEWER"


def _report_mismatch(candidate: dict[str, object]) -> None:
    candidate["report_sha256"] = "9" * 64


def _packet_mode_invalid(candidate: dict[str, object]) -> None:
    candidate["clause_packet_operating_mode"] = "LIGHT_ADVISORY"


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (_package_mismatch, attestation.PACKAGE_MISMATCH),
        (_signer_invalid, attestation.SIGNER_INVALID),
        (_reviewer_mismatch, attestation.REVIEWER_MISMATCH),
        (_report_mismatch, attestation.REPORT_MISMATCH),
        (_packet_mode_invalid, attestation.PACKET_MODE_INVALID),
    ],
)
@pytest.mark.parametrize(
    ("attempts_remaining", "expected_state"),
    [(1, attestation.REVIEW_PENDING), (0, attestation.NOT_ATTESTED_FAIL_CLOSED)],
)
def test_invalid_outcomes_close_attempt_and_respect_remaining_budget(
    mutator,
    reason: str,
    attempts_remaining: int,
    expected_state: str,
) -> None:
    candidate = _valid_attestation()
    mutator(candidate)

    decision = _evaluate(candidate, attempts_remaining=attempts_remaining)

    assert not decision.passed
    assert decision.reason_code == reason
    assert decision.execution_authority_state == expected_state
    assert not decision.reservation_created


@pytest.mark.parametrize(
    ("attempts_remaining", "expected_state"),
    [(1, attestation.REVIEW_PENDING), (0, attestation.NOT_ATTESTED_FAIL_CLOSED)],
)
def test_no_verdict_has_both_attempt_budget_outcomes(
    attempts_remaining: int,
    expected_state: str,
) -> None:
    candidate = _valid_attestation()
    candidate["completion_status"] = "TIMEOUT"
    candidate["verdict"] = "NO_VERDICT"

    decision = _evaluate(candidate, attempts_remaining=attempts_remaining)

    assert decision.reason_code == attestation.NO_VERDICT
    assert decision.execution_authority_state == expected_state


@pytest.mark.parametrize(
    ("attempts_remaining", "expected_state"),
    [(1, attestation.REVIEW_PENDING), (0, attestation.NOT_ATTESTED_FAIL_CLOSED)],
)
def test_expired_attestation_has_both_lineage_outcomes(
    attempts_remaining: int,
    expected_state: str,
) -> None:
    candidate = _valid_attestation()

    decision = _evaluate(candidate, attempts_remaining=attempts_remaining, current_iat=2_000)

    assert decision.reason_code == attestation.EXPIRED
    assert decision.execution_authority_state == expected_state


@pytest.mark.parametrize("field", ["blocker_count", "high_count"])
def test_rejected_verdict_is_terminal_and_cannot_retry(field: str) -> None:
    candidate = _valid_attestation()
    candidate[field] = 1

    decision = _evaluate(candidate, attempts_remaining=4)

    assert decision.reason_code == attestation.REJECTED
    assert decision.execution_authority_state == attestation.TERMINAL_NO_RETRY
    assert not decision.reservation_created


@pytest.mark.parametrize(
    ("attempts_remaining", "expected_state"),
    [(1, attestation.REVIEW_PENDING), (0, attestation.NOT_ATTESTED_FAIL_CLOSED)],
)
def test_receipt_replay_has_both_attempt_budget_outcomes(
    attempts_remaining: int,
    expected_state: str,
) -> None:
    decision = _evaluate(
        _valid_attestation(),
        attempts_remaining=attempts_remaining,
        replayed=frozenset({"fixture-receipt"}),
    )

    assert decision.reason_code == attestation.REPLAY
    assert decision.execution_authority_state == expected_state


def test_closed_field_set_rejects_missing_and_unknown_fields() -> None:
    missing = _valid_attestation()
    del missing["tree"]
    unknown = _valid_attestation()
    unknown["attempt_id"] = "not-an-authorization-relevant-v1-field"

    assert _evaluate(missing, attempts_remaining=1).reason_code == attestation.PACKAGE_MISMATCH
    assert _evaluate(unknown, attempts_remaining=1).reason_code == attestation.PACKAGE_MISMATCH


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("clause_packet_operating_mode", attestation.PACKET_MODE_INVALID),
        ("trusted_signature_or_service_receipt", attestation.SIGNER_INVALID),
        ("reviewer_identity", attestation.REVIEWER_MISMATCH),
        ("report_sha256", attestation.REPORT_MISMATCH),
        ("verdict", attestation.NO_VERDICT),
    ],
)
def test_missing_specialized_field_uses_its_section_6_1_reason(
    field: str,
    reason: str,
) -> None:
    candidate = _valid_attestation()
    del candidate[field]

    decision = _evaluate(candidate, attempts_remaining=1)

    assert decision.reason_code == reason
    assert decision.execution_authority_state == attestation.REVIEW_PENDING
    assert not decision.reservation_created


def test_invalid_trusted_time_source_and_stale_time_token_reject_signer() -> None:
    wrong_source = _valid_attestation()
    wrong_source["trusted_time_source_identity"] = "LOCAL_CLOCK"

    assert _evaluate(wrong_source, attempts_remaining=1).reason_code == attestation.SIGNER_INVALID
    assert (
        _evaluate(
            _valid_attestation(),
            attempts_remaining=1,
            token_age=attestation.MAXIMUM_TOKEN_AGE_SECONDS + 1,
        ).reason_code
        == attestation.SIGNER_INVALID
    )


def test_runtime_policy_rejects_fixture_receipt_without_oidc_or_signing() -> None:
    decision = _evaluate(
        _valid_attestation(),
        attempts_remaining=1,
        trust_policy=attestation.RuntimeRejectAllAttestationPolicy(),
    )

    assert decision.reason_code == attestation.SIGNER_INVALID
    assert not decision.reservation_created


def test_valid_exact_pass_stays_review_pending_and_creates_no_authority() -> None:
    decision = _evaluate(_valid_attestation(), attempts_remaining=1)

    assert decision.passed
    assert decision.reason_code == attestation.PASS
    assert decision.execution_authority_state == attestation.REVIEW_PENDING
    assert not decision.reservation_created
    assert not decision.owner_authority_implied


def test_expected_sequences_are_order_sensitive() -> None:
    candidate = copy.deepcopy(_valid_attestation())
    candidate["exact_allowlist"] = list(reversed(candidate["exact_allowlist"]))

    assert _evaluate(candidate, attempts_remaining=1).reason_code == attestation.PACKAGE_MISMATCH

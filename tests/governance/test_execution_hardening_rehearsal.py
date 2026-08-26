from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from mes_quant.governance.execution_hardening.rehearsal import (
    HANDLE_INJECTION_STOP,
    TIER1_FIXTURE_IDENTITY,
    TIER1_PASS,
    Cell12State,
    Tier1Fixture,
    default_tier1_fixture,
    evaluate_tier1_fixture,
    phase_a_runtime_rehearsal_stop,
)
from tools.build_execution_hardening_review_report import (
    build_non_authoritative_review_report,
)
from tools.run_execution_hardening_rehearsal import main as rehearsal_runner_main
from tools.verify_execution_hardening_attestation import (
    READY_SCHEMA,
    READY_STATUS,
    evaluate_activation_readiness,
)


def _assert_protected(outcome) -> None:
    assert set(outcome.protected_counters.as_mapping().values()) == {0}
    assert outcome.output_path is None
    assert outcome.output_emitted is False
    assert outcome.live_tier2_reservation_created is False
    assert outcome.live_tier2_reservation_consumed is False
    assert outcome.tier2_eligible is False


def _fixture_with_predictor(value: float) -> Tier1Fixture:
    fixture = default_tier1_fixture()
    predictors = list(fixture.predictors)
    predictors[3] = value
    return replace(fixture, predictors=tuple(predictors))


def test_clean_tier1_happy_path_is_prefit_only_and_non_evidentiary() -> None:
    first = evaluate_tier1_fixture(default_tier1_fixture())
    second = evaluate_tier1_fixture(default_tier1_fixture())

    assert first == second
    assert first.status == "PASS"
    assert first.stage == "TARGET_PREFIT"
    assert first.reason_code == TIER1_PASS
    assert first.fixture_identity == TIER1_FIXTURE_IDENTITY
    assert first.predictor_ledger_count == 8
    assert first.request_count == 8
    assert first.target_ledger_count == 8
    assert first.common_mask_created is True
    assert len(first.folds) == 2
    assert set(first.folds[0].row_indices).isdisjoint(first.folds[1].row_indices)
    assert first.design_rank == 4
    assert first.minimum_fold_support_observed == 4
    assert first.harmonic_basis_sha256 == second.harmonic_basis_sha256
    _assert_protected(first)


@pytest.mark.parametrize("predictor", [0.0, -0.25])
def test_nonpositive_predictor_stops_before_target_access(predictor: float) -> None:
    outcome = evaluate_tier1_fixture(_fixture_with_predictor(predictor))

    assert outcome.status == "STOP"
    assert outcome.stage == "PRE_TARGET"
    assert outcome.reason_code == "PREDICTOR_NONPOSITIVE"
    assert outcome.predictor_ledger_count == 8
    assert outcome.predictor_ledger_sha256 is not None
    assert outcome.request_count == 0
    assert outcome.target_ledger_count == 0
    assert outcome.common_mask_created is False
    _assert_protected(outcome)


@pytest.mark.parametrize("predictor", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_predictor_stops_with_complete_predictor_ledger(predictor: float) -> None:
    outcome = evaluate_tier1_fixture(_fixture_with_predictor(predictor))

    assert outcome.reason_code == "PREDICTOR_NONFINITE"
    assert outcome.predictor_ledger_count == 8
    assert outcome.predictor_ledger_sha256 is not None
    assert outcome.target_ledger_count == 0
    _assert_protected(outcome)


def test_zero_variance_target_stops_after_target_ledger_before_mask() -> None:
    fixture = default_tier1_fixture()
    fixture = replace(fixture, target_values=tuple(0.5 for _ in fixture.target_values))

    outcome = evaluate_tier1_fixture(fixture)

    assert outcome.status == "STOP"
    assert outcome.stage == "TARGET_PREFIT"
    assert outcome.reason_code == "TARGET_ZERO_VARIANCE"
    assert outcome.request_count == 8
    assert outcome.request_sha256 is not None
    assert outcome.target_ledger_count == 8
    assert outcome.target_ledger_sha256 is not None
    assert outcome.common_mask_created is False
    assert outcome.common_mask_rows == ()
    assert outcome.folds == ()
    assert outcome.harmonic_basis_sha256 is None
    assert outcome.design_rank is None
    _assert_protected(outcome)


def test_nullable_cell12_combinations_and_reason_codes_are_preserved() -> None:
    fixture = default_tier1_fixture()
    states = (
        Cell12State("LABEL_USABLE", None, None, None),
        Cell12State("LABEL_USABLE", None, 2, 0.1),
        Cell12State("LABEL_USABLE", False, None, 0.2),
        Cell12State("LABEL_USABLE", False, 3, None),
        Cell12State("LABEL_USABLE", True, 4, 0.3),
        Cell12State("LABEL_UNUSABLE", None, None, None),
        Cell12State("PATH_REFERENCE_MISSING", None, 0, None),
        Cell12State("LABEL_USABLE", False, 1, 0.4),
    )

    outcome = evaluate_tier1_fixture(replace(fixture, cell12_states=states))

    assert outcome.status == "PASS"
    assert outcome.cell12_reason_codes == tuple(state.label_reason for state in states)
    assert 5 not in outcome.common_mask_rows
    _assert_protected(outcome)


def test_common_mask_folds_harmonic_rank_and_support_are_deterministic() -> None:
    fixture = default_tier1_fixture()
    fixture = replace(
        fixture,
        target_values=(0.2, None, 0.3, 0.4, 0.5, 0.7, 0.9, 1.1),
        row_eligible=(True, True, False, True, True, True, True, True),
        minimum_fold_support=2,
    )

    outcome = evaluate_tier1_fixture(fixture)

    assert outcome.status == "PASS"
    assert outcome.common_mask_rows == (0, 3, 4, 5, 6, 7)
    assert outcome.folds[0].row_indices == (0, 3, 4)
    assert outcome.folds[1].row_indices == (5, 6, 7)
    assert outcome.harmonic_basis_sha256 is not None
    assert outcome.design_rank == 4
    _assert_protected(outcome)


def test_insufficient_fold_support_stops_without_output() -> None:
    fixture = replace(default_tier1_fixture(), minimum_fold_support=5)

    outcome = evaluate_tier1_fixture(fixture)

    assert outcome.reason_code == "FOLD_SUPPORT_INSUFFICIENT"
    assert outcome.common_mask_created is True
    assert len(outcome.folds) == 2
    assert outcome.minimum_fold_support_observed == 4
    _assert_protected(outcome)


def test_rank_deficiency_stops_without_fit_or_output() -> None:
    fixture = default_tier1_fixture()
    fixture = replace(fixture, predictors=tuple(1.0 for _ in fixture.predictors))

    outcome = evaluate_tier1_fixture(fixture)

    assert outcome.reason_code == "DESIGN_RANK_DEFICIENT"
    assert outcome.common_mask_created is True
    assert len(outcome.folds) == 2
    assert outcome.harmonic_basis_sha256 is not None
    assert outcome.design_rank == 3
    assert outcome.protected_counters.phase_a_hardening_runtime_synthetic_fold_fit_calls == 0
    _assert_protected(outcome)


def test_handle_injection_stops_before_any_ledger_or_reservation() -> None:
    fixture = replace(
        default_tier1_fixture(),
        injected_handles={"production_evidence_registry": object()},
    )

    outcome = evaluate_tier1_fixture(fixture)

    assert outcome.reason_code == HANDLE_INJECTION_STOP
    assert outcome.stage == "CONTRACT"
    assert outcome.predictor_ledger_count == 0
    assert outcome.request_count == 0
    assert outcome.target_ledger_count == 0
    _assert_protected(outcome)


def test_wrong_identity_and_length_mismatch_fail_closed() -> None:
    wrong_identity = replace(default_tier1_fixture(), fixture_identity="REHEARSAL_EVIDENCE")
    wrong_length = replace(default_tier1_fixture(), row_eligible=(True,))

    identity_outcome = evaluate_tier1_fixture(wrong_identity)
    length_outcome = evaluate_tier1_fixture(wrong_length)

    assert identity_outcome.reason_code == "TIER1_FIXTURE_IDENTITY_INVALID"
    assert length_outcome.reason_code == "SYNTHETIC_FIXTURE_LENGTH_MISMATCH"
    _assert_protected(identity_outcome)
    _assert_protected(length_outcome)


def test_phase_a_runtime_runner_is_unconditionally_disabled(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "must-not-exist.json"

    return_code = rehearsal_runner_main(["--output", str(output_path)])

    captured = capsys.readouterr()
    assert return_code == 2
    assert captured.out == ""
    assert "TIER2_RUNTIME_REHEARSAL_NOT_AUTHORIZED_PHASE_A" in captured.err
    assert not output_path.exists()
    _assert_protected(phase_a_runtime_rehearsal_stop())


def test_non_authoritative_report_rejects_output_and_reservation() -> None:
    outcome = evaluate_tier1_fixture(default_tier1_fixture())
    report = build_non_authoritative_review_report((outcome,))

    assert report["report_kind"] == "NON_AUTHORITATIVE_TIER1_ENGINEERING_REPORT"
    assert report["evidence"] is False
    assert report["attestation"] is False
    assert report["authority_granted"] is False
    assert set(report["protected_counters"].values()) == {0}

    with pytest.raises(ValueError, match="PERSISTED_OUTPUT"):
        build_non_authoritative_review_report((replace(outcome, output_emitted=True),))
    with pytest.raises(ValueError, match="LIVE_TIER2_RESERVATION"):
        build_non_authoritative_review_report(
            (replace(outcome, live_tier2_reservation_created=True),)
        )


def test_activation_readiness_missing_sentinel_is_machine_readable(tmp_path: Path) -> None:
    result = evaluate_activation_readiness(
        sentinel_path=tmp_path / "missing.json",
        trusted_root_path=tmp_path / "missing-root.jsonl",
        trusted_root_sha256="0" * 64,
        activation_commit="1" * 40,
        activation_tree="2" * 40,
        source_ref="refs/heads/main",
    )

    assert result.ready is False
    assert result.reason_code == "ATTESTATION_READY_SENTINEL_MISSING_PHASE_A"
    assert result.network_used is False
    assert result.oidc_minted is False
    assert result.signing_invoked is False
    assert result.attestation_accepted is False
    assert result.authority_granted is False


def test_activation_readiness_checks_exact_local_bindings_without_granting_authority(
    tmp_path: Path,
) -> None:
    trusted_root = tmp_path / "trusted-root.jsonl"
    trusted_root.write_bytes(b'{"root":"synthetic-test-only"}\n')
    trusted_root_sha256 = hashlib.sha256(trusted_root.read_bytes()).hexdigest()
    activation_commit = "1" * 40
    activation_tree = "2" * 40
    source_ref = "refs/heads/main"
    sentinel = tmp_path / "ready.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema_version": READY_SCHEMA,
                "status": READY_STATUS,
                "phase": "PHASE_B",
                "ready": True,
                "trusted_root_path": trusted_root.as_posix(),
                "trusted_root_sha256": trusted_root_sha256,
                "activation_commit": activation_commit,
                "activation_tree": activation_tree,
                "source_ref": source_ref,
            },
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = evaluate_activation_readiness(
        sentinel_path=sentinel,
        trusted_root_path=trusted_root,
        trusted_root_sha256=trusted_root_sha256,
        activation_commit=activation_commit,
        activation_tree=activation_tree,
        source_ref=source_ref,
    )

    assert result.ready is True
    assert result.reason_code == "PHASE_B_ACTIVATION_PREREQUISITES_SATISFIED_NO_AUTHORITY_GRANTED"
    assert result.attestation_accepted is False
    assert result.authority_granted is False
    assert result.network_used is False
    assert result.oidc_minted is False
    assert result.signing_invoked is False


def test_activation_readiness_fails_closed_on_trusted_root_hash_mismatch(
    tmp_path: Path,
) -> None:
    trusted_root = tmp_path / "trusted-root.jsonl"
    trusted_root.write_text("root\n", encoding="utf-8")
    sentinel = tmp_path / "ready.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema_version": READY_SCHEMA,
                "status": READY_STATUS,
                "phase": "PHASE_B",
                "ready": True,
                "trusted_root_path": trusted_root.as_posix(),
                "trusted_root_sha256": "0" * 64,
                "activation_commit": "1" * 40,
                "activation_tree": "2" * 40,
                "source_ref": "refs/heads/main",
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_activation_readiness(
        sentinel_path=sentinel,
        trusted_root_path=trusted_root,
        trusted_root_sha256="0" * 64,
        activation_commit="1" * 40,
        activation_tree="2" * 40,
        source_ref="refs/heads/main",
    )

    assert result.ready is False
    assert result.reason_code == "ATTESTATION_TRUSTED_ROOT_BINDING_MISMATCH"
    assert result.authority_granted is False

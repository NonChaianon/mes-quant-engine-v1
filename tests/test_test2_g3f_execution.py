from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mes_quant.exploration.test2_evaluation import (
    ContinuationDecision,
    EvaluationPreflight,
    FoldModelRun,
    FoldPreflight,
)
from mes_quant.exploration.test2_evaluation import Test2Evaluation as EvaluationResult
from mes_quant.exploration.test2_g3_contract import (
    DISPOSITION_DEFERRED_PENDING_G3F,
    G3F_GATE_LITERAL,
    SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
)
from mes_quant.exploration.test2_g3f_contract import (
    EXPECTED_FOLD_FIT_PAIRS,
    G3F_EXECUTION_BRANCH,
    PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256,
    PINNED_G3P_FILE_SHA256,
    PINNED_G3P_RECORD_SHA256,
    PINNED_G3P_RUN_ID,
    G3FContractError,
    VerifiedG3PBinding,
    aggregate_record_sha256,
    mint_fold_fit_budget,
    validate_aggregate_record,
    verify_pinned_g3p_record_file,
)
from mes_quant.exploration.test2_g3f_execution import (
    G3FExecutionBoundaryError,
    assemble_g3f_record,
    git_execution_context,
    reserve_g3f_run,
    run_g3f_conditional_fit,
    terminal_witness_lines,
    verify_code_only_authorization_document,
    verify_real_execution_authorization_document,
    write_g3f_record,
)
from mes_quant.exploration.test2_g3f_execution import (
    main as g3f_main,
)
from mes_quant.exploration.test2_path_contract import FULL_MODEL_ID
from mes_quant.exploration.test2_run_context import EvaluationRunContext
from mes_quant.exploration.test2_stats import (
    EssSupportSummary,
    PairedBootstrapResult,
    SupportGateResult,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _identity(seed: int) -> str:
    return f"{seed:064x}"


def _passing_g3p_record() -> dict[str, object]:
    return {
        "run_id": PINNED_G3P_RUN_ID,
        "record_sha256": PINNED_G3P_RECORD_SHA256,
        "status": "PASS",
        "disposition": DISPOSITION_DEFERRED_PENDING_G3F,
        "support_gate": {
            "passed": True,
            "status": SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
        },
        "counters": {
            "real_models_fitted": 0,
            "real_fold_fit_calls": 0,
            "bootstrap_replicates": 0,
            "economic_diagnostic_calls": 0,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        },
    }


def _verified_binding():
    record = _passing_g3p_record()
    with (
        patch.object(Path, "is_file", return_value=True),
        patch.object(Path, "read_text", return_value=json.dumps(record)),
        patch(
            "mes_quant.exploration.test2_g3f_contract.sha256_file",
            return_value=PINNED_G3P_FILE_SHA256,
        ),
        patch(
            "mes_quant.exploration.test2_g3f_contract.g3p_record_semantic_sha256",
            return_value=PINNED_G3P_RECORD_SHA256,
        ),
    ):
        return verify_pinned_g3p_record_file("/synthetic/g3p.json")


def _complete_budget(seed: int):
    identity = _identity(seed)
    budget = mint_fold_fit_budget(
        gate_literal=G3F_GATE_LITERAL,
        authorization_identity_sha256=identity,
        g3p_binding=_verified_binding(),
    )
    for ordinal, (model_id, fold_id) in enumerate(EXPECTED_FOLD_FIT_PAIRS, start=1):
        permit = budget.consume(model_id=model_id, fold_id=fold_id)
        budget.complete_fit(
            permit,
            model_id=model_id,
            fold_id=fold_id,
            beta_sha256=f"{ordinal + seed:064x}",
            coefficient_dimension=30 if model_id == FULL_MODEL_ID else 5,
            optimizer_converged=True,
        )
    return identity, budget


def _support(row_count: int, ess: float):
    summary = Mock(spec=EssSupportSummary)
    summary.row_count = row_count
    summary.governing_effective_sample_size = ess
    summary.effective_negative_support = ess * 0.6
    summary.effective_positive_support = ess * 0.4
    return summary


def _evaluation() -> EvaluationResult:
    folds = (
        FoldPreflight("WF_2022", "a" * 64, "b" * 64, 60.0, 2_000, 50, _support(2_000, 1_200.0)),
        FoldPreflight("WF_2023", "c" * 64, "d" * 64, 60.0, 2_100, 50, _support(2_100, 1_250.0)),
    )
    preflight = EvaluationPreflight(
        status="READY_FOR_SYNTHETIC_FIT",
        folds=folds,
        pooled_retained_sha256="e" * 64,
        pooled_ess_support=_support(4_100, 2_450.0),
        support_gate=SupportGateResult(True, ()),
    )
    runs = (
        FoldModelRun("WF_2022", 0.69, 0.68, 0.67, 0.5, 0.51, {}, {}),
        FoldModelRun("WF_2023", 0.70, 0.69, 0.68, 0.5, 0.51, {}, {}),
    )
    bootstraps = tuple(
        PairedBootstrapResult(
            block_length=block,
            repetitions=2_000,
            pooled_seed=100 + block,
            fold_seeds=(("WF_2022", 1), ("WF_2023", 2)),
            draw_identity_sha256=f"{block:064x}",
            improvement_vs_prior=(0.02,),
            improvement_vs_nuisance=(0.01,),
            lower_bound_vs_prior=0.001,
            lower_bound_vs_nuisance=0.001,
        )
        for block in (5, 1, 20)
    )
    records = tuple(
        {
            "real_models_fitted": 2,
            "run_real_fold_fitter_calls": 4,
            "run_synthetic_fitter_calls": 0,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        }
        for _ in range(2)
    )
    return EvaluationResult(
        preflight,
        runs,
        bootstraps,
        ContinuationDecision("NOT_INTERESTING_ENOUGH", False, ("MDE",)),
        records,
        4,
        {
            "prior_log_loss": 0.6951219512195121,
            "nuisance_log_loss": 0.6851219512195121,
            "full_log_loss": 0.6751219512195121,
            "improvement_vs_prior": 0.02,
            "improvement_vs_nuisance": 0.01,
        },
    )


def _run_context(*, synthetic: bool = False):
    context = Mock(spec=EvaluationRunContext)
    context.is_synthetic = synthetic
    context.is_test_fixture = False
    return context


def _assemble(seed: int, *, synthetic: bool = False):
    identity, budget = _complete_budget(seed)
    context = _run_context(synthetic=synthetic)
    return assemble_g3f_record(
        _evaluation(),
        budget=budget,
        run_context=context,
        g3p_binding=_verified_binding(),
        code_identity="1" * 40,
        branch=G3F_EXECUTION_BRANCH,
        authorization_sha256=identity,
        request_set_sha256="f" * 64,
        audit_written_utc="2026-08-23T00:00:00Z",
    )


def test_owner_authorization_document_is_byte_pinned() -> None:
    assert (
        verify_code_only_authorization_document(PROJECT_ROOT)
        == PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256
    )


def test_real_execution_authorization_is_mechanically_closed() -> None:
    with pytest.raises(G3FExecutionBoundaryError, match="NOT_AUTHORIZED"):
        verify_real_execution_authorization_document(PROJECT_ROOT)


def test_git_context_cross_checks_branch_upstream_allowlist_and_pins() -> None:
    head = "1" * 40

    def fake_git_output(_root: Path, *args: str) -> str:
        outputs = {
            ("rev-parse", "HEAD"): head,
            ("branch", "--show-current"): G3F_EXECUTION_BRANCH,
            ("rev-parse", "@{upstream}"): head,
            ("status", "--porcelain"): "",
            ("merge-base", "--is-ancestor", "d3d0455a4299f0dc881974029d457a4197ef321d", head): "",
            ("diff", "--name-only", f"d3d0455a4299f0dc881974029d457a4197ef321d..{head}"): "allowed",
        }
        return outputs[args]

    with (
        patch(
            "mes_quant.exploration.test2_g3f_execution._git_output",
            side_effect=fake_git_output,
        ),
        patch(
            "mes_quant.exploration.test2_g3f_execution.execution_changed_file_firewall_failures",
            return_value=(),
        ) as changed_firewall,
        patch(
            "mes_quant.exploration.test2_g3f_execution.protected_surface_failures",
            return_value=(),
        ) as protected_firewall,
        patch(
            "mes_quant.exploration.test2_g3f_execution.verify_code_only_authorization_document",
            return_value=PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256,
        ) as code_only_authorization,
    ):
        assert git_execution_context(PROJECT_ROOT) == (head, G3F_EXECUTION_BRANCH)
    changed_firewall.assert_called_once_with(("allowed",))
    protected_firewall.assert_called_once()
    code_only_authorization.assert_called_once()


def test_main_rejects_noncanonical_output_before_git_or_artifact_access(
    tmp_path: Path,
) -> None:
    argv = [
        "--gate",
        G3F_GATE_LITERAL,
        "--g3p-record",
        "g3p.json",
        "--raw-dbn",
        "raw.dbn",
        "--cell8",
        "cell8.parquet",
        "--cell10",
        "cell10.parquet",
        "--cell12",
        "cell12.parquet",
        "--cell14-features",
        "cell14.parquet",
        "--cell14-run-id",
        "CELL14",
        "--output-root",
        str(tmp_path),
    ]
    with (
        patch(
            "mes_quant.exploration.test2_g3f_execution.git_execution_context"
        ) as git_context,
        pytest.raises(G3FExecutionBoundaryError, match="output_root"),
    ):
        g3f_main(argv, project_root=PROJECT_ROOT)
    git_context.assert_not_called()


def test_runner_rechecks_git_and_real_authorization_before_prerequisite_access() -> None:
    with (
        patch(
            "mes_quant.exploration.test2_g3f_execution.git_execution_context",
            return_value=("1" * 40, G3F_EXECUTION_BRANCH),
        ) as git_context,
        patch(
            "mes_quant.exploration.test2_g3f_execution.verify_real_execution_authorization_document",
            side_effect=G3FExecutionBoundaryError(
                "G3-F real execution remains NOT_AUTHORIZED"
            ),
        ) as verify_execution_authorization,
        patch(
            "mes_quant.exploration.test2_g3f_execution.verify_pinned_g3p_record_file"
        ) as verify_g3p,
        pytest.raises(G3FExecutionBoundaryError, match="NOT_AUTHORIZED"),
    ):
        run_g3f_conditional_fit(
            Mock(),
            project_root=PROJECT_ROOT,
            gate_literal=G3F_GATE_LITERAL,
            g3p_record_path="g3p.json",
            cell14_release_manifest_path="cell14.json",
            frozen_colab_manifest_path="frozen.json",
            cell14_run_id="CELL14",
            output_root="output",
        )
    git_context.assert_called_once_with(PROJECT_ROOT)
    verify_execution_authorization.assert_called_once_with(PROJECT_ROOT)
    verify_g3p.assert_not_called()


def test_aggregate_record_is_closed_and_contains_no_coefficient_values() -> None:
    record = _assemble(200)
    validate_aggregate_record(record)
    assert record["record_sha256"] == aggregate_record_sha256(record)
    encoded = json.dumps(record, sort_keys=True)
    assert '"beta"' not in encoded
    assert "decision_identity" not in encoded
    assert "trades" not in encoded
    assert record["fit_budget"]["real_fold_fit_calls"] == 4


def test_synthetic_context_cannot_mint_a_real_record() -> None:
    with pytest.raises(G3FExecutionBoundaryError, match="real context"):
        _assemble(201, synthetic=True)


def test_unverified_g3p_binding_cannot_mint_a_record() -> None:
    identity, budget = _complete_budget(208)
    forged = VerifiedG3PBinding(
        run_id=PINNED_G3P_RUN_ID,
        record_sha256=PINNED_G3P_RECORD_SHA256,
        file_sha256=PINNED_G3P_FILE_SHA256,
        disposition=DISPOSITION_DEFERRED_PENDING_G3F,
        _verification_key=object(),
    )
    with pytest.raises(G3FContractError, match="pinned verifier"):
        assemble_g3f_record(
            _evaluation(),
            budget=budget,
            run_context=_run_context(),
            g3p_binding=forged,
            code_identity="1" * 40,
            branch=G3F_EXECUTION_BRANCH,
            authorization_sha256=identity,
            request_set_sha256="f" * 64,
        )


def test_evaluator_counter_mismatch_fails_closed() -> None:
    identity, budget = _complete_budget(202)
    evaluation = _evaluation()
    bad_records = (dict(evaluation.experiment_records[0]), dict(evaluation.experiment_records[1]))
    bad_records[0]["run_real_fold_fitter_calls"] = 3
    corrupted = EvaluationResult(
        evaluation.preflight,
        evaluation.fold_runs,
        evaluation.bootstraps,
        evaluation.decision,
        bad_records,
        evaluation.synthetic_fitter_calls,
        evaluation.pooled_primary_metrics,
    )
    with pytest.raises(G3FExecutionBoundaryError, match="cross-bind"):
        assemble_g3f_record(
            corrupted,
            budget=budget,
            run_context=_run_context(),
            g3p_binding=_verified_binding(),
            code_identity="1" * 40,
            branch=G3F_EXECUTION_BRANCH,
            authorization_sha256=identity,
            request_set_sha256="f" * 64,
        )


def test_create_once_writer_rejects_second_publication(tmp_path: Path) -> None:
    record = _assemble(203)
    run_directory = reserve_g3f_run(
        output_root=tmp_path,
        run_id=str(record["run_id"]),
        code_identity=str(record["code_identity"]),
        authorization_sha256=str(
            record["authorization_binding"]["identity_sha256"]
        ),
        g3p_record_sha256=PINNED_G3P_RECORD_SHA256,
    )
    first = write_g3f_record(record, run_directory=run_directory)
    assert first.is_file()
    with pytest.raises(FileExistsError):
        write_g3f_record(record, run_directory=run_directory)
    assert first.is_file()


def test_run_identity_is_reserved_before_any_second_fit_attempt(tmp_path: Path) -> None:
    record = _assemble(205)
    kwargs = {
        "output_root": tmp_path,
        "run_id": str(record["run_id"]),
        "code_identity": str(record["code_identity"]),
        "authorization_sha256": str(
            record["authorization_binding"]["identity_sha256"]
        ),
        "g3p_record_sha256": PINNED_G3P_RECORD_SHA256,
    }
    reserve_g3f_run(**kwargs)
    with pytest.raises(FileExistsError):
        reserve_g3f_run(**kwargs)


def test_writer_rejects_a_reservation_that_does_not_cross_bind(tmp_path: Path) -> None:
    record = _assemble(207)
    run_directory = reserve_g3f_run(
        output_root=tmp_path,
        run_id=str(record["run_id"]),
        code_identity=str(record["code_identity"]),
        authorization_sha256=str(
            record["authorization_binding"]["identity_sha256"]
        ),
        g3p_record_sha256=PINNED_G3P_RECORD_SHA256,
    )
    reservation_path = run_directory / "execution_reservation.json"
    reservation = json.loads(reservation_path.read_text(encoding="utf-8"))
    reservation["code_identity"] = "2" * 40
    reservation_path.write_text(
        json.dumps(reservation, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(G3FExecutionBoundaryError, match="cross-bind"):
        write_g3f_record(record, run_directory=run_directory)
    assert not (run_directory / "conditional_fit_record.json").exists()


def test_terminal_witness_is_derived_from_record() -> None:
    lines = terminal_witness_lines(_assemble(206))
    assert "REAL_FOLD_FIT_CALLS=4" in lines
    assert "BOOTSTRAP_REPETITIONS_PER_BLOCK=2000" in lines
    assert "BOOTSTRAP_BLOCK_COUNT=3" in lines
    assert "BOOTSTRAP_REPLICATES_TOTAL=6000" in lines


def test_record_branch_is_exact() -> None:
    identity, budget = _complete_budget(204)
    with pytest.raises(G3FExecutionBoundaryError, match="branch"):
        assemble_g3f_record(
            _evaluation(),
            budget=budget,
            run_context=_run_context(),
            g3p_binding=_verified_binding(),
            code_identity="1" * 40,
            branch="research/wrong",
            authorization_sha256=identity,
            request_set_sha256="f" * 64,
        )

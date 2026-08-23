from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mes_quant.core.hashing import canonical_json_bytes, sha256_bytes, sha256_file
from mes_quant.exploration.test2_diagnostics import (
    DIAGNOSTIC_THRESHOLD,
    MES_MULTIPLIER_USD_PER_POINT,
    ROUND_TRIP_COST_USD,
)
from mes_quant.exploration.test2_evaluation import (
    READY_FOR_SYNTHETIC_FIT,
    Test2Evaluation,
    run_authorized_train_evaluation,
)
from mes_quant.exploration.test2_g3_contract import G3F_GATE_LITERAL
from mes_quant.exploration.test2_g3_pre_fit import collect_g3p_pre_fit_evidence
from mes_quant.exploration.test2_g3f_contract import (
    G3F_ECONOMIC_SEMANTICS,
    G3F_EXECUTION_BASE_COMMIT,
    G3F_EXECUTION_BRANCH,
    G3F_EXECUTION_STATUS,
    G3F_OMITTED_LEDGER_PREIMAGE,
    G3F_SUPPORT_STATUS,
    G3F_THRESHOLD_SEMANTICS,
    MAX_REAL_FOLD_FIT_CALLS,
    MAX_REAL_MODELS,
    PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256,
    PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256,
    PINNED_G3P_RECORD_SHA256,
    PINNED_G3P_RUN_ID,
    FoldFitBudget,
    VerifiedG3PBinding,
    aggregate_record_sha256,
    assert_verified_g3p_binding,
    execution_changed_file_firewall_failures,
    mint_fold_fit_budget,
    protected_surface_failures,
    scientific_contract_witness,
    validate_aggregate_record,
    verify_pinned_g3p_record_file,
)
from mes_quant.exploration.test2_l1_harness import (
    CanonicalArtifactPaths,
    build_real_l1_run_context,
)
from mes_quant.exploration.test2_path_contract import (
    CAPACITY_POLICY_ID,
    FULL_MODEL_ID,
    RELEASE_POLICY_ID,
)
from mes_quant.exploration.test2_run_context import EvaluationRunContext
from mes_quant.exploration.test2_stats import (
    BOOTSTRAP_REPETITIONS,
    DIAGNOSTIC_BLOCK_LENGTHS,
    FOLD_ORDER,
    PRIMARY_BLOCK_LENGTH,
    REQUIRED_BLOCK_LENGTHS,
)

G3F_EXECUTION_GATE_ID = "TEST2_G3F_CONDITIONAL_FIT_EXECUTION_V1"
G3F_RECORD_FILENAME = "conditional_fit_record.json"
G3F_OUTPUT_SUBPATH = "artifacts/exploration/test2/g3f"
G3F_CODE_ONLY_AUTHORIZATION_RELATIVE_PATH = (
    "docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md"
)
G3F_REAL_EXECUTION_AUTHORIZATION_RELATIVE_PATH = (
    "docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md"
)
G3F_RESERVATION_FILENAME = "execution_reservation.json"
G3F_AUTHORIZATION_SUBDIRECTORY = "authorization"
G3F_AUTHORIZATION_SENTINEL_SUFFIX = ".consumed.json"
G3F_SUCCESS_WITNESS_FILENAME = "execution_success_witness.txt"
G3F_FAILURE_WITNESS_FILENAME = "execution_failure_witness.json"
G3F_REAL_EXECUTION_STATUS_DECLARATION = (
    "**Execution status:** `OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY`"
)
_EXECUTION_AUTHORIZATION_KEY = object()


class G3FExecutionBoundaryError(RuntimeError):
    """Raised before an execution package can exceed its exact authorization."""


@dataclass(frozen=True)
class VerifiedExecutionAuthorization:
    identity_sha256: str
    status: str
    _verification_key: object


@dataclass(frozen=True)
class RunIdentityInputs:
    code_identity: str
    branch: str
    authorization_identity_sha256: str
    authorization_status: str
    g3p_record_sha256: str
    pooled_retained_sha256: str
    request_set_sha256: str


def verify_code_only_authorization_document(project_root: str | Path) -> str:
    path = Path(project_root).resolve() / G3F_CODE_ONLY_AUTHORIZATION_RELATIVE_PATH
    if not path.is_file():
        raise G3FExecutionBoundaryError("pinned G3-F Owner authorization is missing")
    observed = sha256_file(path)
    if observed != PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256:
        raise G3FExecutionBoundaryError("G3-F code-only authorization SHA-256 mismatch")
    return observed


def verify_real_execution_authorization_document(
    project_root: str | Path,
) -> VerifiedExecutionAuthorization:
    """Mint an observed token only from the exact byte-pinned Owner decision."""

    expected = PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256
    if expected is None or G3F_EXECUTION_STATUS != (
        "OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY"
    ):
        raise G3FExecutionBoundaryError("G3-F real execution remains NOT_AUTHORIZED")
    path = Path(project_root).resolve() / G3F_REAL_EXECUTION_AUTHORIZATION_RELATIVE_PATH
    if not path.is_file():
        raise G3FExecutionBoundaryError("pinned G3-F real execution authorization is missing")
    body = path.read_text(encoding="utf-8")
    observed = sha256_file(path)
    if observed != expected:
        raise G3FExecutionBoundaryError(
            "G3-F real execution authorization SHA-256 mismatch"
        )
    if body.count(G3F_REAL_EXECUTION_STATUS_DECLARATION) != 1:
        raise G3FExecutionBoundaryError(
            "G3-F real execution authorization status declaration mismatch"
        )
    return VerifiedExecutionAuthorization(
        observed,
        G3F_EXECUTION_STATUS,
        _EXECUTION_AUTHORIZATION_KEY,
    )


def assert_verified_execution_authorization(
    authorization: VerifiedExecutionAuthorization,
) -> None:
    if (
        not isinstance(authorization, VerifiedExecutionAuthorization)
        or authorization._verification_key is not _EXECUTION_AUTHORIZATION_KEY
        or authorization.identity_sha256
        != PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256
        or authorization.status != G3F_EXECUTION_STATUS
    ):
        raise G3FExecutionBoundaryError(
            "G3-F authorization was not minted by the pinned verifier"
        )


def _git_output(project_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ("git", "-C", str(project_root), *args),
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def git_execution_context(project_root: str | Path) -> tuple[str, str]:
    """Verify exact branch/upstream/diff/pins before any artifact read or fit."""

    root = Path(project_root).resolve()
    head = _git_output(root, "rev-parse", "HEAD")
    branch = _git_output(root, "branch", "--show-current")
    upstream = _git_output(root, "rev-parse", "@{upstream}")
    if branch != G3F_EXECUTION_BRANCH:
        raise G3FExecutionBoundaryError("G3-F execution branch mismatch")
    if head != upstream:
        raise G3FExecutionBoundaryError("G3-F local and upstream commits differ")
    if _git_output(root, "status", "--porcelain"):
        raise G3FExecutionBoundaryError("G3-F worktree is not clean")
    try:
        _git_output(root, "merge-base", "--is-ancestor", G3F_EXECUTION_BASE_COMMIT, head)
    except subprocess.CalledProcessError as error:
        raise G3FExecutionBoundaryError(
            "G3-F HEAD does not descend from the authorized base"
        ) from error
    changed = tuple(
        line
        for line in _git_output(
            root,
            "diff",
            "--name-only",
            f"{G3F_EXECUTION_BASE_COMMIT}..{head}",
        ).splitlines()
        if line
    )
    failures = execution_changed_file_firewall_failures(changed)
    if failures:
        raise G3FExecutionBoundaryError(
            "G3-F changed-file firewall failed: " + "; ".join(failures)
        )
    protected = protected_surface_failures(root)
    if protected:
        raise G3FExecutionBoundaryError(
            "G3-F protected-surface firewall failed: " + "; ".join(protected)
        )
    verify_code_only_authorization_document(root)
    return head, branch


def _support_item(summary: Any) -> dict[str, object]:
    return {
        "row_count": int(summary.row_count),
        "governing_ess": float(summary.governing_effective_sample_size),
        "effective_negative_support": float(summary.effective_negative_support),
        "effective_positive_support": float(summary.effective_positive_support),
    }


def _assert_real_evaluation_witness(
    evaluation: Test2Evaluation,
    *,
    budget_witness: Mapping[str, object],
    run_context: EvaluationRunContext,
) -> None:
    if not isinstance(run_context, EvaluationRunContext):
        raise G3FExecutionBoundaryError("G3-F fitted record requires a run context")
    if run_context.is_synthetic or run_context.is_test_fixture:
        raise G3FExecutionBoundaryError("G3-F fitted record requires a real context")
    if evaluation.synthetic_fitter_calls != MAX_REAL_FOLD_FIT_CALLS:
        raise G3FExecutionBoundaryError("evaluator fitter-call witness is not exactly four")
    if (
        budget_witness.get("real_fold_fit_calls") != MAX_REAL_FOLD_FIT_CALLS
        or budget_witness.get("real_models_fitted") != MAX_REAL_MODELS
    ):
        raise G3FExecutionBoundaryError("sealed budget real-fit counters are invalid")
    if len(evaluation.experiment_records) != MAX_REAL_MODELS:
        raise G3FExecutionBoundaryError("evaluator did not produce two model records")
    for record in evaluation.experiment_records:
        expected = {
            "real_models_fitted": MAX_REAL_MODELS,
            "run_real_fold_fitter_calls": MAX_REAL_FOLD_FIT_CALLS,
            "run_synthetic_fitter_calls": 0,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        }
        if any(record.get(key) != value for key, value in expected.items()):
            raise G3FExecutionBoundaryError(
                "evaluator realness/access counters do not cross-bind"
            )


def _pooled_metrics(evaluation: Test2Evaluation) -> dict[str, object]:
    rows = sum(item.retained_rows for item in evaluation.preflight.folds)
    if rows <= 0:
        raise G3FExecutionBoundaryError("pooled metrics require retained rows")
    required = {
        "prior_log_loss",
        "nuisance_log_loss",
        "full_log_loss",
        "improvement_vs_prior",
        "improvement_vs_nuisance",
    }
    if set(evaluation.pooled_primary_metrics) != required:
        raise G3FExecutionBoundaryError("evaluator pooled aggregate witness is incomplete")
    return {
        "row_count": rows,
        **{
            key: float(evaluation.pooled_primary_metrics[key])
            for key in sorted(required)
        },
        "retained_sha256": evaluation.preflight.pooled_retained_sha256,
    }


def _run_id_seed(inputs: RunIdentityInputs) -> str:
    digest = sha256_bytes(
        canonical_json_bytes(
            {
                "authorization_sha256": inputs.authorization_identity_sha256,
                "authorization_status": inputs.authorization_status,
                "branch": inputs.branch,
                "code_identity": inputs.code_identity,
                "g3p_record_sha256": inputs.g3p_record_sha256,
                "pooled_retained_sha256": inputs.pooled_retained_sha256,
                "request_set_sha256": inputs.request_set_sha256,
            }
        )
    )
    return f"MES_T2_G3F_{digest[:16].upper()}"


def canonical_g3f_output_root(project_root: str | Path) -> Path:
    return (Path(project_root).resolve() / G3F_OUTPUT_SUBPATH).resolve()


def consume_g3f_execution_authorization(
    *,
    canonical_output_root: str | Path,
    authorization: VerifiedExecutionAuthorization,
    run_identity: RunIdentityInputs,
) -> Path:
    """Durably consume one authorization before reservation, minting, or fit."""

    assert_verified_execution_authorization(authorization)
    if (
        run_identity.authorization_identity_sha256 != authorization.identity_sha256
        or run_identity.authorization_status != authorization.status
    ):
        raise G3FExecutionBoundaryError(
            "G3-F run identity diverged from execution authorization"
        )
    root = Path(canonical_output_root).resolve()
    authorization_directory = root / G3F_AUTHORIZATION_SUBDIRECTORY
    authorization_directory.mkdir(parents=True, exist_ok=True)
    sentinel = authorization_directory / (
        f"{authorization.identity_sha256}{G3F_AUTHORIZATION_SENTINEL_SUFFIX}"
    )
    payload = {
        "status": "OWNER_AUTHORIZATION_CONSUMED_BEFORE_FIT",
        "authorization_identity_sha256": authorization.identity_sha256,
        "authorization_status": authorization.status,
        "branch": run_identity.branch,
        "code_identity": run_identity.code_identity,
        "g3p_record_sha256": run_identity.g3p_record_sha256,
        "pooled_retained_sha256": run_identity.pooled_retained_sha256,
        "request_set_sha256": run_identity.request_set_sha256,
    }
    descriptor = os.open(sentinel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    directory_descriptor = os.open(authorization_directory, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
    return sentinel


def reserve_g3f_run(
    *,
    output_root: str | Path,
    run_id: str,
    code_identity: str,
    authorization_sha256: str,
    authorization_status: str,
    g3p_record_sha256: str,
) -> Path:
    """Consume the cross-process run identity before minting or fitting."""

    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_directory = root / run_id
    run_directory.mkdir(exist_ok=False)
    reservation = {
        "status": "RESERVED_BEFORE_FIT_AUTHORIZATION_CONSUMED",
        "run_id": run_id,
        "code_identity": code_identity,
        "authorization_identity_sha256": authorization_sha256,
        "authorization_status": authorization_status,
        "g3p_record_sha256": g3p_record_sha256,
    }
    output = run_directory / G3F_RESERVATION_FILENAME
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(reservation, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    directory_descriptor = os.open(run_directory, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
    return run_directory


def _economic_policy_projection(
    value: object,
    *,
    expected_policy_id: str,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise G3FExecutionBoundaryError("economic policy diagnostics are missing")
    expected_keys = {
        "candidate_long_signals",
        "capacity_rejected_signals",
        "diagnostic_probability_threshold",
        "executed_trades",
        "net_usd",
        "policy_id",
        "round_trip_cost_usd",
        "trades",
    }
    if set(value) != expected_keys or value.get("policy_id") != expected_policy_id:
        raise G3FExecutionBoundaryError("economic policy diagnostic schema mismatch")
    if (
        value.get("round_trip_cost_usd") != ROUND_TRIP_COST_USD
        or value.get("diagnostic_probability_threshold") != DIAGNOSTIC_THRESHOLD
    ):
        raise G3FExecutionBoundaryError("economic policy constants diverged")
    ledger = value.get("trades")
    if not isinstance(ledger, (list, tuple)):
        raise G3FExecutionBoundaryError("economic policy ledger is missing")
    ledger_rows: list[list[object]] = []
    per_fold = {
        fold_id: {"executed_trades": 0, "net_usd": 0.0}
        for fold_id in FOLD_ORDER
    }
    trade_nets: list[float] = []
    expected_trade_keys = {
        "decision_identity",
        "entry_time_utc",
        "fold_id",
        "net_usd",
        "release_time_utc",
        "session_id",
    }
    for trade in ledger:
        if not isinstance(trade, Mapping) or set(trade) != expected_trade_keys:
            raise G3FExecutionBoundaryError("economic policy ledger schema mismatch")
        fold_id = trade.get("fold_id")
        if fold_id not in FOLD_ORDER:
            raise G3FExecutionBoundaryError("economic policy ledger fold mismatch")
        net_usd = float(trade["net_usd"])
        if not math.isfinite(net_usd):
            raise G3FExecutionBoundaryError("economic policy ledger net is non-finite")
        per_fold[str(fold_id)]["executed_trades"] += 1
        per_fold[str(fold_id)]["net_usd"] += net_usd
        trade_nets.append(net_usd)
        ledger_rows.append(
            [
                trade["decision_identity"],
                fold_id,
                trade["session_id"],
                trade["entry_time_utc"],
                trade["release_time_utc"],
                net_usd,
            ]
        )
    raw_counts = (
        value["executed_trades"],
        value["candidate_long_signals"],
        value["capacity_rejected_signals"],
    )
    if any(
        isinstance(item, bool) or not isinstance(item, int) or item < 0
        for item in raw_counts
    ):
        raise G3FExecutionBoundaryError(
            "economic policy counts must be non-negative integers"
        )
    executed, candidates, rejected = raw_counts
    if (
        min(executed, candidates, rejected) < 0
        or executed != len(ledger_rows)
        or candidates != executed + rejected
    ):
        raise G3FExecutionBoundaryError("economic policy counts do not reconcile")
    pooled_net_usd = float(value["net_usd"])
    if not math.isfinite(pooled_net_usd) or not math.isclose(
        pooled_net_usd,
        sum(trade_nets),
        rel_tol=1e-12,
        abs_tol=1e-9,
    ):
        raise G3FExecutionBoundaryError("economic policy net USD does not reconcile")
    return {
        "policy_id": expected_policy_id,
        "candidate_long_signals": candidates,
        "executed_trades": executed,
        "capacity_rejected_signals": rejected,
        "net_usd": pooled_net_usd,
        "round_trip_cost_usd": ROUND_TRIP_COST_USD,
        "diagnostic_probability_threshold": DIAGNOSTIC_THRESHOLD,
        "per_fold": per_fold,
        "trade_net_dispersion": {
            "minimum_net_usd": min(trade_nets) if trade_nets else None,
            "maximum_net_usd": max(trade_nets) if trade_nets else None,
            "positive_count": sum(value > 0.0 for value in trade_nets),
            "negative_count": sum(value < 0.0 for value in trade_nets),
            "zero_count": sum(value == 0.0 for value in trade_nets),
        },
        "omitted_ledger_sha256": sha256_bytes(canonical_json_bytes(ledger_rows)),
    }


def _economic_summary(evaluation: Test2Evaluation) -> dict[str, object]:
    if evaluation.economic_diagnostic_calls != 1:
        raise G3FExecutionBoundaryError(
            "G3-F requires exactly one observed economic diagnostic call"
        )
    full_records = [
        record
        for record in evaluation.experiment_records
        if record.get("model_id") == FULL_MODEL_ID
    ]
    if len(full_records) != 1:
        raise G3FExecutionBoundaryError("G3-F requires exactly one full-model record")
    full_record = full_records[0]
    diagnostics = full_record.get("economic_diagnostics")
    if not isinstance(diagnostics, Mapping) or set(diagnostics) != {
        "capacity_sensitivity",
        "primary",
        "semantics",
        "source_model_id",
    }:
        raise G3FExecutionBoundaryError("full-model economic diagnostics are incomplete")
    if (
        diagnostics.get("source_model_id") != FULL_MODEL_ID
        or diagnostics.get("semantics") != G3F_ECONOMIC_SEMANTICS
        or full_record.get("diagnostic_threshold_semantics")
        != G3F_THRESHOLD_SEMANTICS
    ):
        raise G3FExecutionBoundaryError("economic diagnostic semantics mismatch")
    primary = _economic_policy_projection(
        diagnostics.get("primary"), expected_policy_id=RELEASE_POLICY_ID
    )
    sensitivity = _economic_policy_projection(
        diagnostics.get("capacity_sensitivity"),
        expected_policy_id=CAPACITY_POLICY_ID,
    )
    if primary["candidate_long_signals"] != sensitivity["candidate_long_signals"]:
        raise G3FExecutionBoundaryError("economic policy candidate counts diverged")
    return {
        "source_model_id": FULL_MODEL_ID,
        "semantics": G3F_ECONOMIC_SEMANTICS,
        "threshold_semantics": G3F_THRESHOLD_SEMANTICS,
        "economic_diagnostic_calls": 1,
        "economic_policy_evaluations": 2,
        "mes_multiplier_usd_per_point": MES_MULTIPLIER_USD_PER_POINT,
        "omitted_ledger_preimage": G3F_OMITTED_LEDGER_PREIMAGE,
        "primary": primary,
        "capacity_sensitivity": sensitivity,
    }


def assemble_g3f_record(
    evaluation: Test2Evaluation,
    *,
    budget: FoldFitBudget,
    run_context: EvaluationRunContext,
    g3p_binding: VerifiedG3PBinding,
    execution_authorization: VerifiedExecutionAuthorization,
    run_identity: RunIdentityInputs,
    audit_written_utc: str | None = None,
) -> dict[str, object]:
    """Project evaluator output into the closed aggregate-only G3-F schema."""

    assert_verified_execution_authorization(execution_authorization)
    assert_verified_g3p_binding(g3p_binding)
    if (
        run_identity.authorization_identity_sha256
        != execution_authorization.identity_sha256
        or run_identity.authorization_status != execution_authorization.status
        or run_identity.g3p_record_sha256 != g3p_binding.record_sha256
        or run_identity.pooled_retained_sha256
        != evaluation.preflight.pooled_retained_sha256
        or run_identity.branch != G3F_EXECUTION_BRANCH
    ):
        raise G3FExecutionBoundaryError("G3-F frozen run identity does not cross-bind")
    budget.seal()
    witness = budget.witness()
    _assert_real_evaluation_witness(
        evaluation,
        budget_witness=witness,
        run_context=run_context,
    )
    if evaluation.decision is None or evaluation.decision.disposition not in {
        "INTERESTING_ENOUGH_TO_CONTINUE",
        "NOT_INTERESTING_ENOUGH",
    }:
        raise G3FExecutionBoundaryError("G3-F evaluation has no terminal fit disposition")
    if (
        evaluation.preflight.support_gate.passed is not True
        or evaluation.preflight.support_gate.failures
    ):
        raise G3FExecutionBoundaryError("G3-F support gate is not an exact pass")
    if tuple(item.fold_id for item in evaluation.fold_runs) != FOLD_ORDER:
        raise G3FExecutionBoundaryError("G3-F fold-result order mismatch")
    preflight = {item.fold_id: item for item in evaluation.preflight.folds}
    fold_metrics = {
        item.fold_id: {
            "row_count": preflight[item.fold_id].retained_rows,
            "prior_log_loss": float(item.prior_log_loss),
            "nuisance_log_loss": float(item.nuisance_log_loss),
            "full_log_loss": float(item.full_log_loss),
            "improvement_vs_prior": float(item.prior_log_loss - item.full_log_loss),
            "improvement_vs_nuisance": float(
                item.nuisance_log_loss - item.full_log_loss
            ),
            "retained_sha256": preflight[item.fold_id].holdout_retained_sha256,
        }
        for item in evaluation.fold_runs
    }
    primary = next(
        (
            item
            for item in evaluation.bootstraps
            if item.block_length == PRIMARY_BLOCK_LENGTH
        ),
        None,
    )
    if (
        primary is None
        or tuple(item.block_length for item in evaluation.bootstraps)
        != REQUIRED_BLOCK_LENGTHS
        or any(
            item.repetitions != BOOTSTRAP_REPETITIONS
            for item in evaluation.bootstraps
        )
    ):
        raise G3FExecutionBoundaryError("G3-F required bootstrap set is incomplete")
    draw_identity = sha256_bytes(
        canonical_json_bytes(
            [
                [item.block_length, item.draw_identity_sha256]
                for item in evaluation.bootstraps
            ]
        )
    )
    completed = witness["completed_fits"]
    assert isinstance(completed, list)
    run_id = _run_id_seed(run_identity)
    record: dict[str, object] = {
        "gate_literal": G3F_GATE_LITERAL,
        "status": "PASS",
        "audit_written_utc": audit_written_utc
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "branch": run_identity.branch,
        "code_identity": run_identity.code_identity,
        "run_id": run_id,
        "disposition": evaluation.decision.disposition,
        "fit_budget": witness,
        "authorization_binding": {
            "identity_sha256": execution_authorization.identity_sha256,
            "status": execution_authorization.status,
        },
        "g3p_binding": {
            "run_id": PINNED_G3P_RUN_ID,
            "record_sha256": PINNED_G3P_RECORD_SHA256,
            "disposition": g3p_binding.disposition,
        },
        "scientific_contract": scientific_contract_witness(),
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "access_counters": {
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        },
        "fold_metrics": fold_metrics,
        "pooled_metrics": _pooled_metrics(evaluation),
        "economic_summary": _economic_summary(evaluation),
        "bootstrap_summary": {
            "primary_lower_bound_vs_prior": float(primary.lower_bound_vs_prior),
            "primary_lower_bound_vs_nuisance": float(
                primary.lower_bound_vs_nuisance
            ),
            "draw_identity_sha256": draw_identity,
            "repetitions": int(primary.repetitions),
            "primary_block_length": int(primary.block_length),
            "diagnostic_block_lengths": list(DIAGNOSTIC_BLOCK_LENGTHS),
            "diagnostic_lower_bounds": [
                [
                    int(item.block_length),
                    float(item.lower_bound_vs_prior),
                    float(item.lower_bound_vs_nuisance),
                ]
                for item in evaluation.bootstraps
                if item.block_length in DIAGNOSTIC_BLOCK_LENGTHS
            ],
        },
        "optimizer_summary": {
            "converged_fit_count": len(completed),
            "beta_sha256": [item["beta_sha256"] for item in completed],
            "coefficient_dimensions": [
                item["coefficient_dimension"] for item in completed
            ],
        },
        "support_summary": {
            "status": G3F_SUPPORT_STATUS,
            "floors_relaxed": False,
            "folds": {
                item.fold_id: _support_item(item.ess_support)
                for item in evaluation.preflight.folds
            },
            "pooled": _support_item(evaluation.preflight.pooled_ess_support),
        },
    }
    validate_aggregate_record(record)
    record["record_sha256"] = aggregate_record_sha256(record)
    validate_aggregate_record(record)
    return record


def write_g3f_record(
    record: Mapping[str, Any],
    *,
    run_directory: str | Path,
) -> Path:
    validate_aggregate_record(record)
    expected_sha = aggregate_record_sha256(record)
    if record.get("record_sha256") != expected_sha:
        raise G3FExecutionBoundaryError("G3-F aggregate record SHA-256 mismatch")
    run_id = str(record["run_id"])
    reserved = Path(run_directory).resolve()
    reservation_path = reserved / G3F_RESERVATION_FILENAME
    if reserved.name != run_id or not reservation_path.is_file():
        raise G3FExecutionBoundaryError("G3-F run directory was not reserved before fit")
    try:
        reservation = json.loads(reservation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise G3FExecutionBoundaryError("G3-F reservation is unreadable") from error
    authorization = record["authorization_binding"]
    g3p_binding = record["g3p_binding"]
    if not isinstance(authorization, Mapping) or not isinstance(g3p_binding, Mapping):
        raise G3FExecutionBoundaryError("G3-F record bindings are invalid")
    expected_reservation = {
        "status": "RESERVED_BEFORE_FIT_AUTHORIZATION_CONSUMED",
        "run_id": run_id,
        "code_identity": record["code_identity"],
        "authorization_identity_sha256": authorization["identity_sha256"],
        "authorization_status": authorization["status"],
        "g3p_record_sha256": g3p_binding["record_sha256"],
    }
    if reservation != expected_reservation:
        raise G3FExecutionBoundaryError("G3-F reservation does not cross-bind")
    output = reserved / G3F_RECORD_FILENAME
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(record, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        directory_descriptor = os.open(reserved, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        if output.exists():
            output.unlink()
        raise
    return output


def terminal_witness_lines(record: Mapping[str, object]) -> tuple[str, ...]:
    validate_aggregate_record(record)
    budget = record["fit_budget"]
    bootstrap = record["bootstrap_summary"]
    counters = record["access_counters"]
    economic = record["economic_summary"]
    assert isinstance(budget, Mapping)
    assert isinstance(bootstrap, Mapping)
    assert isinstance(counters, Mapping)
    assert isinstance(economic, Mapping)
    repetitions = int(bootstrap["repetitions"])
    diagnostic_blocks = bootstrap["diagnostic_block_lengths"]
    assert isinstance(diagnostic_blocks, list)
    total_replicates = repetitions * (1 + len(diagnostic_blocks))
    return (
        "G3F_CONDITIONAL_FIT_COMPLETE",
        f"REAL_FOLD_FIT_CALLS={budget['real_fold_fit_calls']}",
        f"REAL_MODELS_FITTED={budget['real_models_fitted']}",
        f"BOOTSTRAP_REPETITIONS_PER_BLOCK={repetitions}",
        f"BOOTSTRAP_BLOCK_COUNT={1 + len(diagnostic_blocks)}",
        f"BOOTSTRAP_REPLICATES_TOTAL={total_replicates}",
        f"ECONOMIC_DIAGNOSTIC_CALLS={economic['economic_diagnostic_calls']}",
        f"ECONOMIC_POLICY_EVALUATIONS={economic['economic_policy_evaluations']}",
        f"DISPOSITION={record['disposition']}",
        f"VALIDATION_ROWS_READ={counters['validation_rows_read']}",
        f"FINAL_TEST={record['final_test_status']}",
    )


def run_g3f_conditional_fit(
    paths: CanonicalArtifactPaths,
    *,
    project_root: str | Path,
    gate_literal: str,
    g3p_record_path: str | Path,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
    cell14_run_id: str,
    output_root: str | Path,
) -> tuple[dict[str, object], Path]:
    root = Path(project_root).resolve()
    canonical_output_root = canonical_g3f_output_root(root)
    if Path(output_root).resolve() != canonical_output_root:
        raise G3FExecutionBoundaryError(
            f"G3-F output_root must be exactly {canonical_output_root}"
        )
    if gate_literal != G3F_GATE_LITERAL:
        raise G3FExecutionBoundaryError("G3-F execution gate literal mismatch")
    code_identity, branch = git_execution_context(root)
    execution_authorization = verify_real_execution_authorization_document(root)
    assert_verified_execution_authorization(execution_authorization)
    authorization_sha256 = execution_authorization.identity_sha256
    g3p_binding = verify_pinned_g3p_record_file(g3p_record_path)
    evidence = collect_g3p_pre_fit_evidence(
        paths,
        cell14_release_manifest_path=cell14_release_manifest_path,
        frozen_colab_manifest_path=frozen_colab_manifest_path,
        cell14_run_id=cell14_run_id,
    )
    if evidence.preflight.status != READY_FOR_SYNTHETIC_FIT:
        raise G3FExecutionBoundaryError(
            "G3-F recomputed preflight is not the exact fit-ready status"
        )
    run_context = build_real_l1_run_context(
        evidence.metadata,
        evidence.prepared,
        evidence.targets,
        evidence.assembly.coverage,
        decoded_identity=evidence.decoded_identity,
        authorization_identity=G3F_EXECUTION_GATE_ID,
        authorization_record_sha256=authorization_sha256,
    )
    run_identity = RunIdentityInputs(
        code_identity=code_identity,
        branch=branch,
        authorization_identity_sha256=execution_authorization.identity_sha256,
        authorization_status=execution_authorization.status,
        g3p_record_sha256=g3p_binding.record_sha256,
        pooled_retained_sha256=evidence.preflight.pooled_retained_sha256,
        request_set_sha256=evidence.targets.request_set_sha256,
    )
    run_id = _run_id_seed(run_identity)
    consume_g3f_execution_authorization(
        canonical_output_root=canonical_output_root,
        authorization=execution_authorization,
        run_identity=run_identity,
    )
    run_directory = reserve_g3f_run(
        output_root=canonical_output_root,
        run_id=run_id,
        code_identity=code_identity,
        authorization_sha256=authorization_sha256,
        authorization_status=execution_authorization.status,
        g3p_record_sha256=g3p_binding.record_sha256,
    )
    budget = mint_fold_fit_budget(
        gate_literal=G3F_GATE_LITERAL,
        authorization_identity_sha256=authorization_sha256,
        g3p_binding=g3p_binding,
    )
    evaluation = run_authorized_train_evaluation(
        evidence.assembly.folds,
        timestamp_utc=datetime.now(UTC),
        code_identity=code_identity,
        run_context=run_context,
        governance_gates_passed=True,
        fold_fit_authority=budget,
    )
    record = assemble_g3f_record(
        evaluation,
        budget=budget,
        run_context=run_context,
        g3p_binding=g3p_binding,
        execution_authorization=execution_authorization,
        run_identity=run_identity,
    )
    if record["run_id"] != run_id:
        raise G3FExecutionBoundaryError("reserved and assembled G3-F run IDs differ")
    output = write_g3f_record(record, run_directory=run_directory)
    return record, output


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Owner-only Test 2 G3-F conditional fit; no science knobs."
    )
    parser.add_argument("--gate", choices=(G3F_GATE_LITERAL,), required=True)
    parser.add_argument("--g3p-record", type=Path, required=True)
    parser.add_argument("--raw-dbn", type=Path, required=True)
    parser.add_argument("--cell8", type=Path, required=True)
    parser.add_argument("--cell10", type=Path, required=True)
    parser.add_argument("--cell12", type=Path, required=True)
    parser.add_argument("--cell14-features", type=Path, required=True)
    parser.add_argument("--cell14-run-id", required=True)
    parser.add_argument(
        "--cell14-manifest",
        type=Path,
        default=Path("manifests/releases/cell14_local_release_v1.json"),
    )
    parser.add_argument(
        "--frozen-manifest",
        type=Path,
        default=Path("manifests/releases/frozen_colab_manifest_v1.json"),
    )
    parser.add_argument("--output-root", type=Path, default=Path(G3F_OUTPUT_SUBPATH))
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: str | Path | None = None,
) -> int:
    args = _parser().parse_args(argv)
    root = Path(project_root or Path.cwd()).resolve()
    allowed_output_root = (root / G3F_OUTPUT_SUBPATH).resolve()
    output_root = (
        args.output_root.resolve()
        if args.output_root.is_absolute()
        else (root / args.output_root).resolve()
    )
    if output_root != allowed_output_root:
        raise G3FExecutionBoundaryError(
            f"G3-F output_root must be exactly {allowed_output_root}"
        )
    paths = CanonicalArtifactPaths(
        raw_dbn=args.raw_dbn,
        cell8_assignments=args.cell8,
        cell10_labels=args.cell10,
        cell12_paths=args.cell12,
        cell14_features=args.cell14_features,
    )
    record, output = run_g3f_conditional_fit(
        paths,
        project_root=root,
        gate_literal=args.gate,
        g3p_record_path=args.g3p_record,
        cell14_release_manifest_path=root / args.cell14_manifest,
        frozen_colab_manifest_path=root / args.frozen_manifest,
        cell14_run_id=args.cell14_run_id,
        output_root=output_root,
    )
    print(f"G3F_RECORD={output}")
    print(f"G3F_RECORD_SHA256={record['record_sha256']}")
    for line in terminal_witness_lines(record):
        print(line)
    return 0


__all__ = [
    "G3FExecutionBoundaryError",
    "RunIdentityInputs",
    "VerifiedExecutionAuthorization",
    "assemble_g3f_record",
    "assert_verified_execution_authorization",
    "canonical_g3f_output_root",
    "consume_g3f_execution_authorization",
    "git_execution_context",
    "main",
    "reserve_g3f_run",
    "run_g3f_conditional_fit",
    "terminal_witness_lines",
    "verify_code_only_authorization_document",
    "verify_real_execution_authorization_document",
    "write_g3f_record",
]

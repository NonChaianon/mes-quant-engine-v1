"""Import-safe runner for the Test 3 one-shot scientific-recovery lineage.

The status gate stops before every real surface: it performs no data, provider, target,
reservation or fit action, creates nothing, and names no runtime evidence root, namespace or
filename, because that naming belongs exclusively to the separate exact Owner activation.

The execution gate closes the future real TRAIN call graph in strict order: verify the Owner
activation envelope and the current reviewed six-path bytes, exclusively reserve the execution
authority, run the fresh capability-bound G3-P recovery pre-fit, hand support-pass rows to the
reviewed G3-F stage strictly in process, and let that stage perform the four internal ordered
least-squares fits behind four durable permits before it writes the one terminal record.  This
runner never names an evidence path, never receives an eligible row, never chooses an estimator
and never creates an activation file.  It cannot execute today: no activation file exists and
creating one is not authorized.

Importing this module has no side effect; all work happens inside ``main``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

GATE_LITERAL = "TEST3_ONE_SHOT_PRE_ACTIVATION_STATUS"
EXECUTION_GATE_LITERAL = "TEST3_ONE_SHOT_OWNER_ACTIVATED_REAL_TRAIN"
PRE_ACTIVATION_STOP = "PRE_ACTIVATION_STOP_NO_DATA_NO_PROVIDER_NO_TARGET_NO_RESERVATION_NO_FIT"
UNDERPOWERED_STOP = "UNDERPOWERED_STOP"
INVALID_EVIDENCE = "INVALID_EVIDENCE"

#: The exact ordered artifact arguments the execution gate forwards, unchanged, to G3-P.
ARTIFACT_ARGUMENTS = ("raw_dbn", "cell8", "cell10", "cell12", "cell14_features")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report the Test 3 one-shot pre-activation stop state, or run the one "
            "Owner-activated real TRAIN recovery. Execution requires a separate exact Owner "
            "activation file that this runner may never create."
        )
    )
    parser.add_argument(
        "--gate",
        choices=(GATE_LITERAL, EXECUTION_GATE_LITERAL),
        required=True,
    )
    parser.add_argument("--activation-file", type=Path, default=None)
    parser.add_argument("--repository-root", type=Path, default=None)
    for name in ARTIFACT_ARGUMENTS:
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, default=None)
    return parser


def _status_lines() -> tuple[str, ...]:
    import mes_quant.exploration.test3_g3f_one_shot as g3f

    status = g3f.describe_pre_activation_stop()
    pairs = ",".join(f"{model_id}/{fold_id}" for model_id, fold_id in status["pair_order"])
    return (
        f"TEST3_ONE_SHOT_STATE={PRE_ACTIVATION_STOP}",
        f"MODULE_ID={status['module_id']}",
        f"ACTIVATION_STATE={status['activation_state']}",
        "OWNER_ACTIVATION=ABSENT_NOT_AUTHORIZED",
        f"ORDERED_MODEL_FOLD_PAIRS={pairs}",
        f"FIT_PERMIT_BUDGET={status['fit_permit_budget']}",
        f"PERMITS_UNREPLENISHED={status['permits_unreplenished']}",
        f"ROW_HANDOFF={status['handoff']}",
        f"EVIDENCE_NAMING={status['evidence_naming']}",
        f"DATA_ACCESS={status['data_access']}",
        f"PROVIDER_ACCESS={status['provider_access']}",
        f"TARGET_ACCESS={status['target_access']}",
        f"TARGET_SPACE_RESERVATION={status['target_space_reservation']}",
        f"REAL_FITS={status['real_fits']}",
        f"ESTIMATOR={status['estimator']}",
        "BOOTSTRAP_BLOCK_ORDER="
        + ",".join(str(block) for block in status["bootstrap_plan"]),
        f"BOOTSTRAP_REPLICATES={status['bootstrap_replicates']}",
        f"MIN_HOLDOUT_SESSIONS={status['min_holdout_sessions']}",
        "REQUIRED_ACF_LAGS="
        + ",".join(str(lag) for lag in status["required_acf_lags"]),
        f"VALIDATION_STATUS={status['validation']}",
        f"FINAL_TEST_STATUS={status['final_test']}",
        "REAL_FOLD_FIT_CALLS=0",
        "EVIDENCE_FILES_WRITTEN=0",
    )


def _absolute(value: object, *, label: str) -> Path:
    if not isinstance(value, Path):
        raise SystemExit(f"--{label} is required for the execution gate")
    resolved = Path(value).expanduser()
    if not resolved.is_absolute():
        raise SystemExit(f"--{label} must be an absolute path")
    return resolved


def _terminal_once(g3f, authority, *, disposition: str, reason: str, binding: dict):
    """Attempt exactly one terminal record; a written terminal is never retried."""

    try:
        return g3f.record_terminal_stop(
            authority,
            disposition=disposition,
            reasons=(reason,),
            source_binding=binding,
        )
    except Exception:  # noqa: BLE001 - a written terminal must never be retried or replaced
        try:
            return g3f.execution_authority_report(authority)
        except Exception:  # noqa: BLE001 - the failure is already terminal
            return None


def _execution_lines(report: object, cleanup: object, status: str) -> tuple[str, ...]:
    lines = [f"TEST3_ONE_SHOT_EXECUTION_STATE={status}"]
    if isinstance(report, dict):
        counters = report.get("counters", {})
        lines.extend(
            (
                f"DISPOSITION={report.get('disposition')}",
                f"RECOVERY_LINEAGE_ID={report.get('recovery_lineage_id')}",
                f"RESERVATION_NAME={report.get('reservation_name')}",
                f"TERMINAL_NAME={report.get('terminal_name')}",
                f"TERMINAL_RECORD_SHA256={report.get('terminal_record_sha256')}",
                f"TERMINAL_FILE_SHA256={report.get('terminal_file_sha256')}",
                f"REAL_FOLD_FIT_CALLS={counters.get('real_fold_fit_calls')}",
                f"REAL_MODELS_FITTED={counters.get('real_models_fitted')}",
                f"REAL_COEFFICIENTS_COMPUTED={counters.get('real_coefficients_computed')}",
                f"REAL_BOOTSTRAP_REPLICATES={counters.get('real_bootstrap_replicates')}",
                f"VALIDATION_STATUS={report.get('validation_status')}",
                f"FINAL_TEST_STATUS={report.get('final_test_status')}",
            )
        )
    else:
        lines.append("TERMINAL_RECORD=ABSENT_STOPPED_BEFORE_RESERVATION")
    if isinstance(cleanup, dict):
        lines.extend(
            (
                f"CLEANUP_SCOPE={cleanup.get('scope')}",
                f"CLEANUP_RECORDS_DELETED={cleanup.get('durable_records_deleted')}",
                f"CLEANUP_RECORDS_MUTATED={cleanup.get('durable_records_mutated')}",
                f"CLEANUP_MEMORY_ERASURE_CLAIMED={cleanup.get('memory_erasure_claimed')}",
            )
        )
    return tuple(lines)


def _execute(args: argparse.Namespace) -> int:
    """Close the exact real call graph in strict order behind one durable reservation."""

    import mes_quant.exploration.test3_g3f_one_shot as g3f
    import mes_quant.exploration.test3_g3p_pre_fit as g3p

    root = _absolute(args.repository_root, label="repository-root")
    activation = _absolute(args.activation_file, label="activation-file")
    artifacts = g3p.ArtifactPaths(
        *(_absolute(getattr(args, name), label=name.replace("_", "-"))
          for name in ARTIFACT_ARGUMENTS)
    )

    # 1. Verify the activation envelope, replay state and current six-path bytes. Nothing
    #    protected is reachable until this returns, and no activation file is ever created here.
    capability = g3f.load_owner_activation_capability(str(activation), repository_root=str(root))

    # 2. Publish the durable execution-authority reservation before any source/target access.
    authority = g3f.open_execution_authority(capability)
    report: object = None
    cleanup: object = None
    status = "COMPLETED"
    try:
        # 3-5. Fresh G3-P recovery, in-process handoff, four internal fits and one terminal.
        outcome = g3p.run_g3p_recovery(
            root=root,
            paths=artifacts,
            execution_authority=authority,
        )
        if not outcome["rows_delivered"]:
            failures = tuple(outcome["structural_failures"]) or ("G3P_RECOVERY_SUPPORT_FAILURE",)
            g3f.record_terminal_stop(
                authority,
                disposition=UNDERPOWERED_STOP,
                reasons=failures,
                source_binding=outcome,
            )
            status = UNDERPOWERED_STOP
        report = g3f.execution_authority_report(authority)
    except Exception as error:  # noqa: BLE001 - exactly one terminal, then a truthful status
        status = INVALID_EVIDENCE
        report = _terminal_once(
            g3f,
            authority,
            disposition=INVALID_EVIDENCE,
            reason=f"{type(error).__name__}: {error}",
            binding={"stage": "TEST3_ONE_SHOT_RECOVERY", "failed_after_reservation": True},
        )
    finally:
        cleanup = g3f.close_execution_authority(authority)
    for line in _execution_lines(report, cleanup, status):
        print(line)
    return 0 if status == "COMPLETED" else 1


def main(argv: list[str] | None = None) -> int:
    """Report the closed pre-activation stop, or run the one Owner-activated recovery."""

    args = _parser().parse_args(argv)
    if args.gate == EXECUTION_GATE_LITERAL:
        return _execute(args)
    for line in _status_lines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

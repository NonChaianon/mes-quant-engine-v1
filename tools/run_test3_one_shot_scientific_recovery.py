"""Import-safe status runner for the Test 3 one-shot scientific-recovery lineage.

This runner deliberately stops before every real surface.  It performs no data, provider,
target, reservation or fit action, creates no directory or file, and names no runtime evidence
root, namespace or filename: that naming belongs exclusively to the separate later Owner
activation.  Importing this module has no side effect; all work happens inside ``main``.
"""

from __future__ import annotations

import argparse
import sys

GATE_LITERAL = "TEST3_ONE_SHOT_PRE_ACTIVATION_STATUS"
PRE_ACTIVATION_STOP = "PRE_ACTIVATION_STOP_NO_DATA_NO_PROVIDER_NO_TARGET_NO_RESERVATION_NO_FIT"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report the Test 3 one-shot pre-activation stop state. This runner cannot "
            "execute a real run; execution requires a separate exact Owner activation."
        )
    )
    parser.add_argument("--gate", choices=(GATE_LITERAL,), required=True)
    return parser


def _status_lines() -> tuple[str, ...]:
    from mes_quant.exploration.test3_g3f_one_shot import describe_pre_activation_stop

    status = describe_pre_activation_stop()
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
        f"VALIDATION_STATUS={status['validation']}",
        f"FINAL_TEST_STATUS={status['final_test']}",
        "REAL_FOLD_FIT_CALLS=0",
        "EVIDENCE_FILES_WRITTEN=0",
    )


def main(argv: list[str] | None = None) -> int:
    """Print the closed pre-activation stop status; no real surface is touched."""

    _parser().parse_args(argv)
    for line in _status_lines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

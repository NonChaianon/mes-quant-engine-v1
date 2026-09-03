from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from mes_quant.governance.execution_hardening.rehearsal import (
    PHASE_A_MODE,
    phase_a_runtime_rehearsal_stop,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail-closed Phase-A placeholder for the future Tier-2 rehearsal runner."
    )
    parser.add_argument(
        "--output",
        help="forbidden in Phase A; accepted only so the refusal is deterministic",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _parser().parse_args(argv)
    outcome = phase_a_runtime_rehearsal_stop()
    diagnostic = {
        "phase_a_mode": PHASE_A_MODE,
        "status": outcome.status,
        "stage": outcome.stage,
        "reason_code": outcome.reason_code,
        "artifact_created": False,
        "live_tier2_reservation_created": False,
        "live_tier2_reservation_consumed": False,
        "authority_granted": False,
    }
    print(
        json.dumps(diagnostic, allow_nan=False, separators=(",", ":"), sort_keys=True),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict

from mes_quant.governance.execution_hardening.rehearsal import (
    PHASE_A_MODE,
    TIER1_FIXTURE_IDENTITY,
    ProtectedCounters,
    Tier1Outcome,
    default_tier1_fixture,
    evaluate_tier1_fixture,
)

REPORT_SCHEMA = "MES_EXECUTION_HARDENING_PHASE_A_TIER1_REPORT_V1"


def build_non_authoritative_review_report(outcomes: Sequence[Tier1Outcome]) -> dict[str, object]:
    """Build a deterministic in-memory engineering report, never an attestation."""

    if not outcomes:
        raise ValueError("TIER1_REPORT_REQUIRES_AT_LEAST_ONE_OUTCOME")
    for outcome in outcomes:
        if outcome.fixture_identity != TIER1_FIXTURE_IDENTITY:
            raise ValueError("TIER1_REPORT_FIXTURE_IDENTITY_INVALID")
        outcome.protected_counters.assert_zero()
        if outcome.output_emitted or outcome.output_path is not None:
            raise ValueError("TIER1_REPORT_REJECTS_PERSISTED_OUTPUT")
        if outcome.live_tier2_reservation_created or outcome.live_tier2_reservation_consumed:
            raise ValueError("TIER1_REPORT_REJECTS_LIVE_TIER2_RESERVATION")

    counters = ProtectedCounters()
    counters.assert_zero()
    return {
        "schema_version": REPORT_SCHEMA,
        "phase_a_mode": PHASE_A_MODE,
        "fixture_identity": TIER1_FIXTURE_IDENTITY,
        "report_kind": "NON_AUTHORITATIVE_TIER1_ENGINEERING_REPORT",
        "evidence": False,
        "attestation": False,
        "authority_granted": False,
        "scientific_inference_authorized": False,
        "outcome_count": len(outcomes),
        "outcomes": [outcome.to_mapping() for outcome in outcomes],
        "protected_counters": asdict(counters),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a non-authoritative Phase-A Tier-1 report in memory."
    )
    parser.add_argument(
        "--phase-a-tier1-self-check",
        action="store_true",
        help="evaluate the deterministic in-memory fixture; creates no evidence or files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.phase_a_tier1_self_check:
        raise SystemExit("PHASE_A_TIER1_SELF_CHECK_FLAG_REQUIRED")
    outcome = evaluate_tier1_fixture(default_tier1_fixture())
    report = build_non_authoritative_review_report((outcome,))
    print(json.dumps(report, allow_nan=False, separators=(",", ":"), sort_keys=True))
    return 0 if outcome.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

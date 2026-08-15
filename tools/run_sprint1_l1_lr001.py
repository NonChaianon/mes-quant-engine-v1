from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from mes_quant.exploration.l1_lr001 import (
    FIRST_L1_EXPERIMENT_ID,
    L1_AUTHORIZATION_TOKEN,
    preflight_artifacts,
    run_lr001,
)


def _git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Governed TRAIN-only runner for MES Sprint-1 LR001."
    )
    parser.add_argument("--mode", choices=("preflight", "execute"), required=True)
    parser.add_argument("--features-path", required=True)
    parser.add_argument("--labels-path", required=True)
    parser.add_argument(
        "--output-root",
        default="artifacts/exploration/sprint1",
        help="Local ignored output root; experiment ID is appended automatically.",
    )
    parser.add_argument(
        "--authorization-token",
        default="",
        help="Required only for execute mode; must match the frozen owner authorization token.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.mode == "preflight":
        result = preflight_artifacts(args.features_path, args.labels_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        print("LR001_PREFLIGHT_PASS_NO_TARGET_ROWS_DESERIALIZED")
        return 0

    if args.authorization_token != L1_AUTHORIZATION_TOKEN:
        raise SystemExit(
            "Execution blocked: pass the exact frozen --authorization-token for Issue #26."
        )

    evaluation = run_lr001(
        features_path=args.features_path,
        labels_path=args.labels_path,
        output_root=Path(args.output_root),
        authorization_token=args.authorization_token,
        code_identity=_git_head(),
    )
    record = evaluation.experiment_record
    result = record["result"]
    sample = record["sample"]
    print(f"EXPERIMENT_ID={FIRST_L1_EXPERIMENT_ID}")
    print(f"N_RAW_OUTER_TRAIN={sample['N_raw_outer_train']}")
    print(f"N_ELIGIBLE={sample['N_eligible']}")
    print(f"N_SESSIONS_ELIGIBLE={sample['N_sessions_eligible']}")
    print(f"BASELINE_OOF_LOG_LOSS={result['baseline_oof_log_loss']:.12f}")
    print(f"CANDIDATE_OOF_LOG_LOSS={result['candidate_oof_log_loss']:.12f}")
    print(f"LOG_LOSS_IMPROVEMENT={result['LOG_LOSS_IMPROVEMENT']:.12f}")
    print(
        "MEDIAN_FOLD_LOG_LOSS_IMPROVEMENT="
        f"{result['median_fold_log_loss_improvement']:.12f}"
    )
    print(f"DISPOSITION={record['disposition']}")
    print("VALIDATION_OUTCOMES=UNOPENED")
    print("FINAL_TEST=SEALED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

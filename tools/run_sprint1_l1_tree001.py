from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from mes_quant.exploration.l1_tree001 import (
    TREE001_EXECUTION_STATUS,
    preflight_artifacts,
    run_tree001,
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
        description="Governed TRAIN-only runner for MES Sprint-1 TREE001."
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
        help="Execute mode remains disabled until separate owner authorization is activated.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.mode == "preflight":
        result = preflight_artifacts(args.features_path, args.labels_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        print("TREE001_PREFLIGHT_PASS_NO_TARGET_ROWS_DESERIALIZED")
        print(f"TREE001_EXECUTION_STATUS={TREE001_EXECUTION_STATUS}")
        return 0

    evaluation = run_tree001(
        features_path=Path(args.features_path),
        labels_path=Path(args.labels_path),
        output_root=Path(args.output_root),
        authorization_token=args.authorization_token,
        code_identity=_git_head(),
    )
    record = evaluation.experiment_record
    result = record["result"]
    sample = record["sample"]
    print(f"EXPERIMENT_ID={record['EXPERIMENT_ID']}")
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

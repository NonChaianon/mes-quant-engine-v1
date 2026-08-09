from __future__ import annotations

import argparse
import runpy
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def verify_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify frozen MES migration evidence")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=_project_root() / "manifests" / "releases" / "frozen_colab_manifest_v1.json",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="optional folder containing exact release artifacts and all six Cell 14 inputs",
    )
    args = parser.parse_args(argv)

    verifier_path = _project_root() / "tools" / "verify_migration.py"
    if not verifier_path.is_file():
        raise RuntimeError(
            "The full migration verifier is unavailable. Run this command from the MES repository "
            "checkout; structural-only verification is intentionally not reported as PASS."
        )
    verifier = runpy.run_path(str(verifier_path))
    result = verifier["verify_all"](artifact_root=args.artifact_root, manifest_path=args.manifest)
    verifier["print_verification_report"](result)
    return 0


def build_features_main(argv: list[str] | None = None) -> int:
    from mes_quant.pipelines.feature_pipeline import run_feature_pipeline

    parser = argparse.ArgumentParser(description="Build Cell 14 Development-only features")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=_project_root() / "artifacts" / "runs")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=_project_root() / "manifests" / "releases" / "frozen_colab_manifest_v1.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_project_root() / "configs" / "v1" / "features_v1.json",
    )
    args = parser.parse_args(argv)
    output = run_feature_pipeline(
        artifact_root=args.artifact_root,
        run_root=args.run_root,
        manifest_path=args.manifest,
        config_path=args.config,
    )
    print(f"PASS: Cell 14 artifacts written to {output}")
    return 0

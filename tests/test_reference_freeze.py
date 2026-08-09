from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = PROJECT_ROOT / "reference" / "colab_v1_cells_0_13"
sys.path.insert(0, str(PROJECT_ROOT))

from mes_quant.core.manifest import load_manifest
from tools.freeze_colab_reference import ensure_reference_outputs_writable
from tools.verify_migration import (
    VerificationError,
    verify_all,
    verify_local_artifact_root,
)


class ReferenceFreezeTests(unittest.TestCase):
    def test_all_cells_are_frozen_and_hash_valid(self) -> None:
        manifest = json.loads((REFERENCE / "cell_sources_manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["cell_order"], list(range(14)))
        self.assertEqual(manifest["execution_counts"], list(range(37, 51)))
        for cell in manifest["cells"]:
            payload = (REFERENCE / cell["source_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), cell["normalized_source_sha256"])

    def test_cell9_has_one_active_implementation(self) -> None:
        source = (REFERENCE / "cell09.py").read_text("utf-8")
        self.assertEqual(source.count("# CELL 9 — RESEARCH COST MODEL CONTRACT"), 1)
        self.assertEqual(source.count("scenarios.to_csv("), 1)

    def test_notebook_has_no_warning_flood(self) -> None:
        source = (REFERENCE / "MES_V1_cells_0_13.ipynb").read_text("utf-8")
        self.assertNotIn("jupyter_client/session.py:203", source)

    def test_complete_frozen_migration_evidence_verifies(self) -> None:
        verify_all()

    def test_release_binds_source_and_evidence_manifests(self) -> None:
        release = json.loads(
            (PROJECT_ROOT / "manifests" / "releases" / "frozen_colab_manifest_v1.json").read_text(
                "utf-8"
            )
        )
        source_manifest = REFERENCE / "cell_sources_manifest.json"
        checksum_file = REFERENCE / "SHA256SUMS.txt"
        evidence_manifest = PROJECT_ROOT / release["drive"]["small_evidence_manifest"]
        self.assertEqual(
            hashlib.sha256(source_manifest.read_bytes()).hexdigest(),
            release["notebook"]["cell_source_manifest_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(checksum_file.read_bytes()).hexdigest(),
            release["notebook"]["sha256s_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(evidence_manifest.read_bytes()).hexdigest(),
            release["drive"]["small_evidence_manifest_sha256"],
        )
        self.assertEqual(
            evidence_manifest.stat().st_size,
            release["drive"]["small_evidence_manifest_size_bytes"],
        )

    def test_freeze_outputs_are_create_only_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            existing = Path(temp_dir) / "cell00.py"
            existing.write_text("already frozen\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "create-only"):
                ensure_reference_outputs_writable([existing], replace_existing_reference=False)

    def test_explicit_replace_flag_unlocks_version_bump(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            existing = Path(temp_dir) / "cell00.py"
            existing.write_text("already frozen\n", encoding="utf-8")
            ensure_reference_outputs_writable([existing], replace_existing_reference=True)

    def test_local_cell14_inputs_when_cache_is_available(self) -> None:
        artifact_root = PROJECT_ROOT / "artifacts" / "cache" / "source_v1"
        if not artifact_root.is_dir():
            self.skipTest("Optional local large-artifact cache is absent")
        result = verify_all(artifact_root=artifact_root)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result["required_cell14_ids"]), 6)
        self.assertTrue(
            set(result["required_cell14_ids"]).issubset(result["verified_manifest_artifact_ids"])
        )

    def test_local_artifact_gate_rejects_missing_cell14_inputs(self) -> None:
        manifest = load_manifest(
            PROJECT_ROOT / "manifests" / "releases" / "frozen_colab_manifest_v1.json"
        )
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertRaisesRegex(VerificationError, "missing required Cell 14 inputs"),
        ):
            verify_local_artifact_root(manifest, Path(temp_dir))


if __name__ == "__main__":
    unittest.main()

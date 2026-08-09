from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.core.manifest import (
    ManifestError,
    artifact_index,
    load_manifest,
    validate_manifest,
)


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = PROJECT_ROOT / "manifests" / "releases" / "frozen_colab_manifest_v1.json"
        self.manifest = load_manifest(self.path)

    def test_manifest_is_structurally_valid(self) -> None:
        validate_manifest(self.manifest)

    def test_golden_final_test_seal(self) -> None:
        self.assertEqual(self.manifest["golden_counts"]["final_test_rows"], 8654)
        self.assertEqual(self.manifest["locked_contracts"]["final_test_status"], "SEALED")
        self.assertFalse(self.manifest["locked_contracts"]["final_test_outcomes_allowed"])
        self.assertEqual(self.manifest["golden_counts"]["cell13_final_test_rows_used"], 0)

    def test_artifact_dag_contains_required_lineage(self) -> None:
        artifacts = artifact_index(self.manifest)
        self.assertEqual(
            artifacts["cell8_assignments"]["upstream"], ["cell7_universe", "cell7_audit"]
        )
        self.assertIn("cell12_paths", artifacts["cell13_events"]["upstream"])
        self.assertNotIn(
            "cell10_labels", self.manifest["migration_rules"]["cell14_allowed_upstream_ids"]
        )

    def test_json_round_trip(self) -> None:
        serialized = json.dumps(self.manifest, sort_keys=True)
        self.assertEqual(json.loads(serialized)["manifest_version"], "MES_V1_FROZEN_COLAB_1.0")

    def test_empty_self_declared_manifest_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["artifacts"] = []
        with self.assertRaises(ManifestError):
            validate_manifest(candidate)

    def test_manifest_cannot_promote_itself_without_large_artifacts(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["status"] = "LOCKED"
        with self.assertRaises(ManifestError):
            validate_manifest(candidate)

    def test_golden_count_rewrite_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["golden_counts"]["decision_universe_rows"] = 1
        with self.assertRaises(ManifestError):
            validate_manifest(candidate)

    def test_artifact_hash_or_lineage_rewrite_is_rejected(self) -> None:
        for field, replacement in (
            ("sha256", "0" * 64),
            ("upstream", []),
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.manifest)
                artifact_index(candidate)["cell13_events"][field] = replacement
                with self.assertRaises(ManifestError):
                    validate_manifest(candidate)

    def test_reference_digest_rewrite_is_rejected(self) -> None:
        for section, field in (
            ("notebook", "local_reference_sha256"),
            ("notebook", "cell_source_manifest_sha256"),
            ("notebook", "sha256s_sha256"),
            ("drive", "small_evidence_manifest_sha256"),
        ):
            with self.subTest(section=section, field=field):
                candidate = copy.deepcopy(self.manifest)
                candidate[section][field] = "0" * 64
                with self.assertRaises(ManifestError):
                    validate_manifest(candidate)


if __name__ == "__main__":
    unittest.main()

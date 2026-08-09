from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.verify_cell14_release import (
    CANONICAL_RUN_ID,
    EXPECTED_RELEASE_MANIFEST_SHA256,
    EXPECTED_RELEASE_MANIFEST_SIZE,
    RELEASE_MANIFEST_PATH,
    REPLAY_RUN_ID,
    Cell14ReleaseError,
    sha256,
    validate_release_manifest,
    verify_all,
)


class Cell14ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(RELEASE_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.result = verify_all()

    def test_full_release_verification_and_semantic_gates(self) -> None:
        self.assertEqual(self.result["development_rows"], 31193)
        self.assertEqual(self.result["feature_columns"], 29)
        self.assertEqual(self.result["missing_pairs"], 5703)
        self.assertEqual(self.result["final_test_rows"], 0)
        self.assertEqual(self.result["source_time_violations"], 0)

    def test_release_manifest_is_byte_frozen(self) -> None:
        self.assertEqual(RELEASE_MANIFEST_PATH.stat().st_size, EXPECTED_RELEASE_MANIFEST_SIZE)
        self.assertEqual(sha256(RELEASE_MANIFEST_PATH), EXPECTED_RELEASE_MANIFEST_SHA256)

    def test_release_statuses_are_deliberately_distinct(self) -> None:
        status = self.manifest["status"]
        self.assertEqual(status["computation"], "LOCKED")
        self.assertEqual(status["development_data_artifact"], "LOCKED")
        self.assertEqual(status["candidate_feature_catalog"], "PROVISIONAL")
        self.assertEqual(status["model_transforms"], "OPEN")
        self.assertEqual(status["final_test_features"], "SEALED_ZERO_ROWS")

    def test_release_manifest_cannot_self_rewrite_contracts(self) -> None:
        mutations = [
            (("status", "candidate_feature_catalog"), "LOCKED"),
            (("golden_counts", "development_rows"), 1),
            (("policy", "final_test_start_year"), 2026),
            (("controls", "feature_builder_source", "sha256"), "0" * 64),
            (("upstream_inputs", "cell8_assignments", "sha256"), "0" * 64),
            (("runs", "canonical", "artifacts", "features", "sha256"), "0" * 64),
            (("deterministic_replay", "result"), "OPEN"),
        ]
        for keys, replacement in mutations:
            with self.subTest(keys=keys):
                candidate = copy.deepcopy(self.manifest)
                target = candidate
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = replacement
                with self.assertRaises(Cell14ReleaseError):
                    validate_release_manifest(candidate)

    def test_canonical_and_replay_ids_and_non_audit_hashes_match(self) -> None:
        self.assertEqual(self.manifest["canonical_run_id"], CANONICAL_RUN_ID)
        self.assertEqual(self.manifest["replay_run_id"], REPLAY_RUN_ID)
        canonical = self.manifest["runs"]["canonical"]["artifacts"]
        replay = self.manifest["runs"]["replay"]["artifacts"]
        for artifact_id in self.manifest["deterministic_replay"]["byte_identical_artifact_ids"]:
            with self.subTest(artifact_id=artifact_id):
                self.assertEqual(
                    canonical[artifact_id]["size_bytes"], replay[artifact_id]["size_bytes"]
                )
                self.assertEqual(canonical[artifact_id]["sha256"], replay[artifact_id]["sha256"])

    def test_both_audits_preserve_final_test_and_input_firewalls(self) -> None:
        for role, run in self.manifest["runs"].items():
            with self.subTest(role=role):
                audit = json.loads(
                    (PROJECT_ROOT / run["artifacts"]["audit"]["file"]).read_text("utf-8")
                )
                self.assertEqual(audit["status"], "PASS")
                self.assertEqual(audit["failures"], [])
                self.assertEqual(audit["feature_contract"]["input_cells"], [5, 7, 8])
                self.assertEqual(
                    audit["feature_contract"]["forbidden_input_cells"], [9, 10, 11, 12, 13]
                )
                self.assertEqual(audit["artifact_access"]["forbidden_opened_artifact_count"], 0)
                self.assertEqual(audit["counts"]["final_test_feature_rows"], 0)
                self.assertTrue(audit["counts"]["maximum_source_time_lte_decision_time"])


if __name__ == "__main__":
    unittest.main()

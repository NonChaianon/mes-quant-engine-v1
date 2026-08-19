from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import (
    FrozenInputError,
    load_frozen_inputs,
)
from mes_quant.governance.classification.record import (
    RecordValidationError,
    canonical_record_bytes,
    validate_record,
)

from tests.governance._frozen_fixture import (
    FROZEN_JSON_PATHS,
    FrozenAuthorityFixture,
    read_frozen_bytes,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class ClassificationRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority_fixture = FrozenAuthorityFixture(PROJECT_ROOT)
        cls.frozen = load_frozen_inputs(
            cls.authority_fixture.repo,
            authority_commit_sha1=cls.authority_fixture.authority_commit,
        )
        cls.schema = cls.frozen.classification_record_schema

    @classmethod
    def tearDownClass(cls) -> None:
        cls.authority_fixture.close()

    def valid_record(self) -> dict[str, object]:
        closure = {
            "reachable_protected": True,
            "unresolved_count": 0,
            "visited_nodes": 1,
            "visited_edges": 0,
        }
        return {
            "schema_version": "CLASSIFICATION_RECORD_V1",
            "repository_id": 1329447686,
            "repository_node_id": "R_kgDOTz3DBg",
            "base_commit_sha1": "1" * 40,
            "head_commit_sha1": "2" * 40,
            "merge_base_sha1": "1" * 40,
            "base_tree_sha1": "3" * 40,
            "head_tree_sha1": "4" * 40,
            "canonical_tree_delta": [],
            "classifier_spec_sha256": "A" * 64,
            "classifier_implementation_sha256": "B" * 64,
            "protected_surface_manifest_sha256": (
                self.frozen.protected_surface_manifest_sha256
            ),
            "classification_record_schema_sha256": (
                self.frozen.classification_record_schema_sha256
            ),
            "analyzer_config_sha256": "C" * 64,
            "analyzer_toolchain_digest": "sha256:" + "d" * 64,
            "analyzer_limits_sha256": self.frozen.analyzer_limits_sha256,
            "classification_outcome": "CLASSIFIED",
            "detected_classes": ["QUANT_ENGINE"],
            "forward_closure_summary": closure,
            "reverse_closure_summary": closure,
            "reference_scan_summary": {
                "scan_complete": True,
                "scanned_tracked_objects": 1,
                "supported_reference_files": 1,
                "unsupported_reference_files": 0,
                "failed_reference_files": 0,
            },
            "unresolved_nodes": [],
            "unsupported_reference_file_types": [],
            "required_gate_union": [
                "INDEPENDENT_AUDITOR_REVIEW",
                "MACHINE_CHECKS",
                "OWNER_AUTHORIZATION",
            ],
            "failure_state": "NONE",
        }

    def test_valid_record_is_deterministic_and_canonical(self) -> None:
        record = self.valid_record()
        encoded_a = canonical_record_bytes(
            record,
            schema=self.schema,
            max_record_bytes=self.frozen.analyzer_limits["max_record_bytes"],
        )
        encoded_b = canonical_record_bytes(
            copy.deepcopy(record),
            schema=self.schema,
            max_record_bytes=self.frozen.analyzer_limits["max_record_bytes"],
        )
        self.assertEqual(encoded_a, encoded_b)
        self.assertTrue(encoded_a.endswith(b"\n"))
        self.assertNotIn(b"\r", encoded_a)
        self.assertEqual(json.loads(encoded_a), record)

    def test_serializer_rejects_nan_even_if_validation_is_bypassed(self) -> None:
        with mock.patch(
            "mes_quant.governance.classification.record.validate_record",
            return_value=None,
        ):
            with self.assertRaises(RecordValidationError):
                canonical_record_bytes(
                    {"value": float("nan")},
                    schema=self.schema,
                    max_record_bytes=self.frozen.analyzer_limits["max_record_bytes"],
                )

    def test_unknown_field_is_rejected(self) -> None:
        record = self.valid_record()
        record["unexpected"] = "no"
        with self.assertRaises(RecordValidationError):
            validate_record(record, self.schema)

    def test_ambiguous_requires_cross_boundary(self) -> None:
        record = self.valid_record()
        record["classification_outcome"] = "AMBIGUOUS"
        with self.assertRaises(RecordValidationError):
            validate_record(record, self.schema)

        record["detected_classes"] = ["CROSS_BOUNDARY"]
        validate_record(record, self.schema)

    def test_failure_state_is_none_only(self) -> None:
        record = self.valid_record()
        record["failure_state"] = "CLASSIFIER_FAILURE"
        with self.assertRaises(RecordValidationError):
            validate_record(record, self.schema)

    def test_frozen_inputs_are_bound_to_authority_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            _git(repo, "config", "user.name", "MES Test")
            _git(repo, "config", "user.email", "mes-test@example.invalid")

            for relative_path in FROZEN_JSON_PATHS:
                destination = repo / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(read_frozen_bytes(PROJECT_ROOT, relative_path))

            _git(repo, "add", ".")
            _git(repo, "commit", "-q", "-m", "authority")
            authority = _git(repo, "rev-parse", "HEAD")

            loaded = load_frozen_inputs(repo, authority_commit_sha1=authority)
            self.assertEqual(loaded.authority_commit_sha1, authority)

            limits_path = repo / "configs/governance/ANALYZER_LIMITS_V1.json"
            limits_path.write_bytes(limits_path.read_bytes() + b" ")

            loaded_again = load_frozen_inputs(repo, authority_commit_sha1=authority)
            self.assertEqual(
                loaded_again.analyzer_limits_sha256,
                loaded.analyzer_limits_sha256,
            )

            _git(repo, "add", "configs/governance/ANALYZER_LIMITS_V1.json")
            _git(repo, "commit", "-q", "-m", "tamper")
            tampered = _git(repo, "rev-parse", "HEAD")
            _git(repo, "replace", authority, tampered)

            loaded_with_replace_ref = load_frozen_inputs(
                repo,
                authority_commit_sha1=authority,
            )
            self.assertEqual(
                loaded_with_replace_ref.analyzer_limits_sha256,
                loaded.analyzer_limits_sha256,
            )

            with self.assertRaises(FrozenInputError):
                load_frozen_inputs(repo, authority_commit_sha1=tampered)


if __name__ == "__main__":
    unittest.main()

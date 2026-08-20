from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import load_frozen_inputs
from mes_quant.governance.sentinel.manifest_guard import detect_manifest_weakening
from mes_quant.governance.sentinel.sentinel import (
    GovernanceSentinelError,
    evaluate_governance_paths,
)
from tests.governance._frozen_fixture import FrozenAuthorityFixture


class SentinelAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = FrozenAuthorityFixture(PROJECT_ROOT)
        cls.manifest = load_frozen_inputs(
            cls.fixture.repo,
            authority_commit_sha1=cls.fixture.authority_commit,
        ).protected_surface_manifest

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.close()

    def test_bad_predecessor_schema_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["schema"] = "UNTRUSTED_SCHEMA"

        with self.assertRaises(GovernanceSentinelError):
            evaluate_governance_paths(
                [b"src/mes_quant/features/builder.py"],
                manifest,
            )

    def test_changed_match_semantics_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["match_semantics"]["unicode_normalization"] = "NFC"

        with self.assertRaises(GovernanceSentinelError):
            evaluate_governance_paths(
                [b"src/mes_quant/features/builder.py"],
                manifest,
            )

    def test_unknown_predecessor_field_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["candidate_defined_authority"] = True

        with self.assertRaises(GovernanceSentinelError):
            evaluate_governance_paths(
                [b"src/mes_quant/features/builder.py"],
                manifest,
            )

    def test_duplicate_predecessor_entry_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        value = manifest["governance_control_exact_paths"][0]
        manifest["governance_control_exact_paths"].append(value)

        with self.assertRaises(GovernanceSentinelError):
            evaluate_governance_paths(
                [b"src/mes_quant/features/builder.py"],
                manifest,
            )

    def test_adding_presentation_root_is_weakening(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["presentation_roots"].append("web/")

        result = detect_manifest_weakening(
            self.manifest,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "changed:presentation_roots",
            result.reasons,
        )

    def test_adding_read_only_adapter_is_weakening(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["read_only_adapter_modules"].append(
            "mes_quant.presentation"
        )

        result = detect_manifest_weakening(
            self.manifest,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "changed:read_only_adapter_modules",
            result.reasons,
        )


if __name__ == "__main__":
    unittest.main()

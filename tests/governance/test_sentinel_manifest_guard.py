from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import (
    load_frozen_inputs,
)
from mes_quant.governance.sentinel.manifest_guard import (
    ManifestGuardError,
    detect_manifest_weakening,
)
from tests.governance._frozen_fixture import FrozenAuthorityFixture


class ManifestGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority_fixture = FrozenAuthorityFixture(PROJECT_ROOT)
        cls.predecessor = load_frozen_inputs(
            cls.authority_fixture.repo,
            authority_commit_sha1=cls.authority_fixture.authority_commit,
        ).protected_surface_manifest

    @classmethod
    def tearDownClass(cls) -> None:
        cls.authority_fixture.close()

    def test_identical_manifest_is_not_weakening(self) -> None:
        candidate = copy.deepcopy(self.predecessor)

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertFalse(result.weakening_detected)
        self.assertEqual(result.reasons, ())

    def test_removing_governance_exact_path_is_weakening(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.predecessor)

        removed = (
            "docs/governance/"
            "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
        )

        candidate["governance_control_exact_paths"].remove(
            removed
        )

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "removed:governance_control_exact_paths:"
            + removed,
            result.reasons,
        )

    def test_narrowing_protected_quant_prefix_is_weakening(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.predecessor)

        candidate["protected_quant_prefixes"].remove(
            "src/mes_quant/"
        )
        candidate["protected_quant_prefixes"].append(
            "src/mes_quant/features/"
        )

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "removed:protected_quant_prefixes:"
            "src/mes_quant/",
            result.reasons,
        )

    def test_removing_static_spec_freeze_path_is_weakening(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.predecessor)

        removed = (
            "configs/governance/"
            "ANALYZER_LIMITS_V1.json"
        )

        candidate["static_spec_freeze_paths"].remove(
            removed
        )

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "removed:static_spec_freeze_paths:"
            + removed,
            result.reasons,
        )

    def test_additive_protection_is_not_weakening(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.predecessor)

        candidate[
            "governance_control_exact_paths"
        ].append(
            "src/mes_quant/governance/sentinel/sentinel.py"
        )

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertFalse(result.weakening_detected)
        self.assertEqual(result.reasons, ())

    def test_match_semantics_change_is_weakening(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.predecessor)

        candidate["match_semantics"][
            "unicode_normalization"
        ] = "NFC"

        result = detect_manifest_weakening(
            self.predecessor,
            candidate,
        )

        self.assertTrue(result.weakening_detected)
        self.assertIn(
            "changed:match_semantics",
            result.reasons,
        )

    def test_invalid_manifest_shape_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.predecessor)

        candidate[
            "governance_control_exact_paths"
        ] = "not-a-list"

        with self.assertRaises(ManifestGuardError):
            detect_manifest_weakening(
                self.predecessor,
                candidate,
            )


if __name__ == "__main__":
    unittest.main()

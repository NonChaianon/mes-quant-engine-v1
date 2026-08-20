from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import (
    load_frozen_inputs,
)
from mes_quant.governance.sentinel.sentinel import (
    GovernanceSentinelError,
    evaluate_governance_paths,
)
from tests.governance._frozen_fixture import FrozenAuthorityFixture


class GovernanceSentinelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority_fixture = FrozenAuthorityFixture(PROJECT_ROOT)
        cls.manifest = load_frozen_inputs(
            cls.authority_fixture.repo,
            authority_commit_sha1=cls.authority_fixture.authority_commit,
        ).protected_surface_manifest

    @classmethod
    def tearDownClass(cls) -> None:
        cls.authority_fixture.close()

    def test_frozen_spec_path_intercepts_before_ordinary_classifier(
        self,
    ) -> None:
        result = evaluate_governance_paths(
            [
                b"docs/governance/"
                b"CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
            ],
            self.manifest,
        )

        self.assertTrue(result.intercepted)
        self.assertFalse(result.ordinary_classifier_allowed)
        self.assertEqual(
            result.detected_classes,
            ("GOVERNANCE_AMENDMENT",),
        )
        self.assertTrue(
            any(
                reason.startswith("governance-control:")
                for reason in result.reasons
            )
        )

    def test_ci_control_intercepts_and_retains_cross_boundary(
        self,
    ) -> None:
        result = evaluate_governance_paths(
            [b".github/workflows/quant-ci-v1.yml"],
            self.manifest,
        )

        self.assertTrue(result.intercepted)
        self.assertFalse(result.ordinary_classifier_allowed)
        self.assertEqual(
            result.detected_classes,
            (
                "GOVERNANCE_AMENDMENT",
                "CROSS_BOUNDARY",
            ),
        )

    def test_classifier_implementation_is_governance_subject(
        self,
    ) -> None:
        result = evaluate_governance_paths(
            [
                b"src/mes_quant/governance/"
                b"classification/classifier.py"
            ],
            self.manifest,
        )

        self.assertTrue(result.intercepted)
        self.assertFalse(result.ordinary_classifier_allowed)
        self.assertIn(
            "GOVERNANCE_AMENDMENT",
            result.detected_classes,
        )
        self.assertTrue(
            any(
                reason.startswith(
                    "bootstrap-governance-implementation:"
                )
                for reason in result.reasons
            )
        )

    def test_sentinel_implementation_is_governance_subject(
        self,
    ) -> None:
        result = evaluate_governance_paths(
            [
                b"src/mes_quant/governance/"
                b"sentinel/sentinel.py"
            ],
            self.manifest,
        )

        self.assertTrue(result.intercepted)
        self.assertFalse(result.ordinary_classifier_allowed)
        self.assertIn(
            "GOVERNANCE_AMENDMENT",
            result.detected_classes,
        )

    def test_ordinary_quant_path_is_not_governance_intercepted(
        self,
    ) -> None:
        result = evaluate_governance_paths(
            [b"src/mes_quant/features/builder.py"],
            self.manifest,
        )

        self.assertFalse(result.intercepted)
        self.assertTrue(result.ordinary_classifier_allowed)
        self.assertEqual(result.detected_classes, ())
        self.assertEqual(result.reasons, ())

    def test_invalid_path_fails_closed(self) -> None:
        cases = (
            [],
            [b""],
            ["src/mes_quant/features/builder.py"],
        )

        for paths in cases:
            with self.subTest(paths=paths):
                with self.assertRaises(GovernanceSentinelError):
                    evaluate_governance_paths(
                        paths,
                        self.manifest,
                    )


if __name__ == "__main__":
    unittest.main()

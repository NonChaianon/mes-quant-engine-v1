from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import (
    load_frozen_inputs,
)
from mes_quant.governance.sentinel.manifest_guard import (
    ManifestGuardResult,
)
from mes_quant.governance.sentinel.sentinel import (
    GovernanceSentinelError,
    evaluate_governance_facts,
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

    def test_frozen_spec_path_is_not_a_bootstrap_fact(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [
                b"docs/governance/"
                b"CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
            ],
            self.manifest,
            None,
        )

        self.assertFalse(
            result.bootstrap_surface_hit
        )
        self.assertFalse(
            result.manifest_weakening_detected
        )

    def test_ci_control_is_left_to_ordinary_classification(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [b".github/workflows/quant-ci-v1.yml"],
            self.manifest,
            None,
        )

        self.assertFalse(
            result.bootstrap_surface_hit
        )

    def test_classifier_implementation_sets_bootstrap_fact(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [
                b"src/mes_quant/governance/"
                b"classification/classifier.py"
            ],
            self.manifest,
            None,
        )

        self.assertTrue(
            result.bootstrap_surface_hit
        )

    def test_sentinel_implementation_sets_bootstrap_fact(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [
                b"src/mes_quant/governance/"
                b"sentinel/sentinel.py"
            ],
            self.manifest,
            None,
        )

        self.assertTrue(
            result.bootstrap_surface_hit
        )

    def test_entire_governance_package_sets_bootstrap_fact(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [
                b"src/mes_quant/governance/"
                b"future_control.py"
            ],
            self.manifest,
            None,
        )

        self.assertTrue(
            result.bootstrap_surface_hit
        )

    def test_ordinary_quant_path_has_no_governance_fact(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [b"src/mes_quant/features/builder.py"],
            self.manifest,
            None,
        )

        self.assertFalse(
            result.bootstrap_surface_hit
        )
        self.assertEqual(
            result.weakening_details,
            (),
        )

    def test_manifest_weakening_is_returned_as_evidence(
        self,
    ) -> None:
        result = evaluate_governance_facts(
            [b"configs/governance/PROTECTED_SURFACE_MANIFEST_V1.json"],
            self.manifest,
            ManifestGuardResult(
                weakening_detected=True,
                reasons=("removed:test",),
            ),
        )

        self.assertTrue(
            result.manifest_weakening_detected
        )
        self.assertEqual(
            result.weakening_details,
            ("removed:test",),
        )

    def test_invalid_path_fails_closed(self) -> None:
        cases = (
            [],
            [b""],
            ["src/mes_quant/features/builder.py"],
        )

        for paths in cases:
            with self.subTest(paths=paths):
                with self.assertRaises(GovernanceSentinelError):
                    evaluate_governance_facts(
                        paths,
                        self.manifest,
                        None,
                    )


if __name__ == "__main__":
    unittest.main()

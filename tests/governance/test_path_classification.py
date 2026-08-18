from __future__ import annotations

import copy
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import load_frozen_inputs
from mes_quant.governance.classification.path_classification import (
    PathClassificationError,
    classify_paths,
)

from tests.governance._frozen_fixture import FrozenAuthorityFixture


class PathClassificationTests(unittest.TestCase):
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

    def test_governance_path(self) -> None:
        result = classify_paths(
            [b"docs/governance/CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"],
            self.manifest,
        )
        self.assertEqual(result.detected_classes, ("GOVERNANCE_AMENDMENT",))

    def test_ci_path_is_governance_and_cross_boundary(self) -> None:
        result = classify_paths([b".github/workflows/quant-ci-v1.yml"], self.manifest)
        self.assertEqual(
            result.detected_classes, ("GOVERNANCE_AMENDMENT", "CROSS_BOUNDARY")
        )

    def test_quant_path(self) -> None:
        result = classify_paths([b"src/mes_quant/features/builder.py"], self.manifest)
        self.assertEqual(result.detected_classes, ("QUANT_ENGINE",))

    def test_dependency_and_quant_union(self) -> None:
        result = classify_paths([b"pyproject.toml"], self.manifest)
        self.assertEqual(result.detected_classes, ("QUANT_ENGINE", "CROSS_BOUNDARY"))

    def test_execution_sensitive_unprotected_is_cross_boundary(self) -> None:
        result = classify_paths([b"tools/example.py"], self.manifest)
        self.assertEqual(result.detected_classes, ("CROSS_BOUNDARY",))

    def test_unmatched_path_is_conservatively_cross_boundary(self) -> None:
        result = classify_paths([b"README.md"], self.manifest)
        self.assertEqual(result.detected_classes, ("CROSS_BOUNDARY",))

    def test_uncovered_protected_quant_module_fails_closed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["protected_quant_modules"] = ["some_external_pkg.core"]

        with self.assertRaises(PathClassificationError):
            classify_paths([b"external_pkg/core.py"], manifest)

    def test_nonempty_protected_symbols_fail_closed_in_phase1(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["protected_symbols"] = ["mes_quant.core:SomeSymbol"]

        with self.assertRaises(PathClassificationError):
            classify_paths([b"src/mes_quant/core.py"], manifest)

    def test_ux_only_is_unreachable_with_empty_boundary(self) -> None:
        for path in (b"README.md", b"docs/example.md", b"web/index.html"):
            with self.subTest(path=path):
                result = classify_paths([path], self.manifest)
                self.assertNotIn("UX_ONLY", result.detected_classes)


if __name__ == "__main__":
    unittest.main()

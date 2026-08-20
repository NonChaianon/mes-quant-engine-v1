from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.classification_decision import (
    ClassificationDecisionError,
    derive_classification_decision,
)
from mes_quant.governance.classification.path_classification import (
    PathClassification,
)
from mes_quant.governance.classification.reference_analysis import (
    AnalysisUnresolvedNode,
    ReferenceScanSummary,
    ReferenceSnapshotAnalysis,
)
from mes_quant.governance.classification.reference_graph import (
    BidirectionalGraphAnalysis,
    ClosureSummary,
)
from mes_quant.governance.sentinel.sentinel import GovernanceFacts

NO_GOVERNANCE_FACTS = GovernanceFacts(
    bootstrap_surface_hit=False,
    manifest_weakening_detected=False,
    weakening_details=(),
)


def _closure(
    *,
    reachable_protected: bool = False,
    unresolved_count: int = 0,
) -> ClosureSummary:
    return ClosureSummary(
        reachable_protected=reachable_protected,
        unresolved_count=unresolved_count,
        visited_nodes=1,
        visited_edges=0,
    )


def _analysis(
    *,
    forward_protected: bool = False,
    reverse_protected: bool = False,
    unresolved_nodes=(),
    unsupported_types=(),
    scan_complete: bool = True,
    failed_reference_files: int = 0,
) -> ReferenceSnapshotAnalysis:
    return ReferenceSnapshotAnalysis(
        reference_scan_summary=ReferenceScanSummary(
            scan_complete=scan_complete,
            scanned_tracked_objects=1,
            supported_reference_files=1,
            unsupported_reference_files=len(unsupported_types),
            failed_reference_files=failed_reference_files,
        ),
        graph_analysis=BidirectionalGraphAnalysis(
            forward=_closure(
                reachable_protected=forward_protected,
                unresolved_count=len(unresolved_nodes),
            ),
            reverse=_closure(
                reachable_protected=reverse_protected,
                unresolved_count=0,
            ),
        ),
        unresolved_nodes=tuple(unresolved_nodes),
        unsupported_reference_file_types=tuple(unsupported_types),
        protected_nodes=(b"protected.py",),
    )


class ClassificationDecisionTests(unittest.TestCase):
    def test_forward_protected_reachability_adds_quant_engine(self) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("CROSS_BOUNDARY",),
                reasons=("narrower-class-unproven:00",),
            ),
            _analysis(
                forward_protected=True,
            ),
            NO_GOVERNANCE_FACTS,
        )

        self.assertEqual(
            decision.classification_outcome,
            "CLASSIFIED",
        )
        self.assertEqual(
            decision.detected_classes,
            ("QUANT_ENGINE", "CROSS_BOUNDARY"),
        )
        self.assertIn(
            "INDEPENDENT_AUDITOR_REVIEW",
            decision.required_gate_union,
        )
        self.assertIn(
            "OWNER_AUTHORIZATION",
            decision.required_gate_union,
        )

    def test_reverse_protected_reachability_adds_quant_engine(self) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("CROSS_BOUNDARY",),
                reasons=("execution-sensitive:00",),
            ),
            _analysis(
                reverse_protected=True,
            ),
            NO_GOVERNANCE_FACTS,
        )

        self.assertIn(
            "QUANT_ENGINE",
            decision.detected_classes,
        )
        self.assertIn(
            "protected-reaches-changed",
            decision.reasons,
        )

    def test_unresolved_reference_is_ambiguous_cross_boundary(self) -> None:
        unresolved = AnalysisUnresolvedNode(
            path_bytes=b"app/view.py",
            reason_code="DYNAMIC_IMPORT",
            reference_kind="DYNAMIC",
        )

        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("CROSS_BOUNDARY",),
                reasons=("narrower-class-unproven:00",),
            ),
            _analysis(
                unresolved_nodes=(unresolved,),
            ),
            NO_GOVERNANCE_FACTS,
        )

        self.assertEqual(
            decision.classification_outcome,
            "AMBIGUOUS",
        )
        self.assertIn(
            "CROSS_BOUNDARY",
            decision.detected_classes,
        )
        self.assertIn(
            "narrower-capability-separation-unproven",
            decision.reasons,
        )

    def test_unsupported_reference_type_is_ambiguous_cross_boundary(self) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("CROSS_BOUNDARY",),
                reasons=("narrower-class-unproven:00",),
            ),
            _analysis(
                unsupported_types=("yaml",),
            ),
            NO_GOVERNANCE_FACTS,
        )

        self.assertEqual(
            decision.classification_outcome,
            "AMBIGUOUS",
        )
        self.assertIn(
            "CROSS_BOUNDARY",
            decision.detected_classes,
        )

    def test_governance_and_quant_gate_union_is_union_not_precedence_erasure(self) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=(
                    "GOVERNANCE_AMENDMENT",
                    "QUANT_ENGINE",
                ),
                reasons=("governance:00", "quant:00"),
            ),
            _analysis(),
            NO_GOVERNANCE_FACTS,
        )

        self.assertEqual(
            decision.detected_classes,
            (
                "GOVERNANCE_AMENDMENT",
                "QUANT_ENGINE",
            ),
        )
        self.assertEqual(
            decision.required_gate_union,
            (
                "GOVERNANCE_BOOTSTRAP_GATE",
                "MACHINE_CHECKS",
                "INDEPENDENT_AUDITOR_REVIEW",
                "OWNER_AUTHORIZATION",
            ),
        )
    def test_ux_only_cannot_coexist_with_protected_class(self) -> None:
        with self.assertRaisesRegex(
            ClassificationDecisionError,
            "UX_ONLY cannot coexist",
        ):
            derive_classification_decision(
                PathClassification(
                    detected_classes=(
                        "UX_ONLY",
                        "QUANT_ENGINE",
                    ),
                    reasons=("test",),
                ),
                _analysis(),
                NO_GOVERNANCE_FACTS,
            )

    def test_incomplete_reference_scan_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ClassificationDecisionError,
            "incomplete reference scan",
        ):
            derive_classification_decision(
                PathClassification(
                    detected_classes=("CROSS_BOUNDARY",),
                    reasons=("test",),
                ),
                _analysis(
                    scan_complete=False,
                ),
                NO_GOVERNANCE_FACTS,
            )

    def test_failed_reference_scan_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ClassificationDecisionError,
            "failed reference scan",
        ):
            derive_classification_decision(
                PathClassification(
                    detected_classes=("CROSS_BOUNDARY",),
                    reasons=("test",),
                ),
                _analysis(
                    failed_reference_files=1,
                ),
                NO_GOVERNANCE_FACTS,
            )

    def test_bootstrap_fact_adds_governance_without_erasing_quant(
        self,
    ) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("QUANT_ENGINE",),
                reasons=("quant:00",),
            ),
            _analysis(),
            GovernanceFacts(
                bootstrap_surface_hit=True,
                manifest_weakening_detected=False,
                weakening_details=(),
            ),
        )

        self.assertEqual(
            decision.detected_classes,
            (
                "GOVERNANCE_AMENDMENT",
                "QUANT_ENGINE",
            ),
        )
        self.assertEqual(
            decision.required_gate_union,
            (
                "GOVERNANCE_BOOTSTRAP_GATE",
                "MACHINE_CHECKS",
                "INDEPENDENT_AUDITOR_REVIEW",
                "OWNER_AUTHORIZATION",
            ),
        )

    def test_manifest_weakening_fact_is_not_a_class_source(
        self,
    ) -> None:
        decision = derive_classification_decision(
            PathClassification(
                detected_classes=("QUANT_ENGINE",),
                reasons=("quant:00",),
            ),
            _analysis(),
            GovernanceFacts(
                bootstrap_surface_hit=False,
                manifest_weakening_detected=True,
                weakening_details=("removed:test",),
            ),
        )

        self.assertEqual(
            decision.detected_classes,
            ("QUANT_ENGINE",),
        )


if __name__ == "__main__":
    unittest.main()

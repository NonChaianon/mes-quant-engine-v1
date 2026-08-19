from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tests.governance._frozen_fixture import read_frozen_bytes

from mes_quant.governance.classification.classification_decision import (
    ClassificationDecision,
)
from mes_quant.governance.classification.git_delta import DeltaEntry
from mes_quant.governance.classification.record import (
    canonical_record_bytes,
)
from mes_quant.governance.classification.record_builder import (
    RecordBuilderError,
    build_classification_record,
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


SCHEMA_PATH = Path(
    "configs/governance/CLASSIFICATION_RECORD_SCHEMA_V1.json"
)

SCHEMA = json.loads(
    read_frozen_bytes(
        PROJECT_ROOT,
        SCHEMA_PATH,
    ).decode("utf-8")
)

MAX_RECORD_BYTES = 33_554_432

BASE = "1" * 40
HEAD = "2" * 40
MERGE_BASE = BASE
BASE_TREE = "3" * 40
HEAD_TREE = "4" * 40

SHA256_A = "A" * 64
SHA256_B = "B" * 64
SHA256_C = "C" * 64
SHA256_D = "D" * 64
SHA256_E = "E" * 64
SHA256_F = "F" * 64

TOOLCHAIN = "sha256:" + ("a" * 64)


def _delta() -> tuple[DeltaEntry, ...]:
    return (
        DeltaEntry(
            operation="MODIFY",
            old_path_bytes=b"app/view.py",
            new_path_bytes=b"app/view.py",
            old_blob_sha1="5" * 40,
            new_blob_sha1="6" * 40,
            old_mode="100644",
            new_mode="100644",
            old_object_type="blob",
            new_object_type="blob",
        ),
    )


def _closure(
    *,
    reachable: bool = False,
    unresolved: int = 0,
) -> ClosureSummary:
    return ClosureSummary(
        reachable_protected=reachable,
        unresolved_count=unresolved,
        visited_nodes=2,
        visited_edges=1,
    )


def _analysis(
    *,
    unresolved_nodes=(),
    unsupported_types=(),
    scan_complete: bool = True,
    failed_reference_files: int = 0,
) -> ReferenceSnapshotAnalysis:
    return ReferenceSnapshotAnalysis(
        reference_scan_summary=ReferenceScanSummary(
            scan_complete=scan_complete,
            scanned_tracked_objects=12,
            supported_reference_files=5,
            unsupported_reference_files=len(unsupported_types),
            failed_reference_files=failed_reference_files,
        ),
        graph_analysis=BidirectionalGraphAnalysis(
            forward=_closure(
                reachable=True,
                unresolved=len(unresolved_nodes),
            ),
            reverse=_closure(),
        ),
        unresolved_nodes=tuple(unresolved_nodes),
        unsupported_reference_file_types=tuple(
            unsupported_types
        ),
        protected_nodes=(
            b"src/mes_quant/features/builder.py",
        ),
    )


def _decision(
    *,
    outcome: str = "CLASSIFIED",
    classes=("QUANT_ENGINE",),
    gates=None,
) -> ClassificationDecision:
    class_set = set(classes)

    if gates is None:
        gate_set: set[str] = set()

        if "GOVERNANCE_AMENDMENT" in class_set:
            gate_set.add(
                "GOVERNANCE_BOOTSTRAP_GATE"
            )

        if class_set.intersection(
            {
                "UX_ONLY",
                "QUANT_ENGINE",
                "CROSS_BOUNDARY",
            }
        ):
            gate_set.add(
                "MACHINE_CHECKS"
            )

        if class_set.intersection(
            {
                "UX_ONLY",
                "CROSS_BOUNDARY",
            }
        ):
            gate_set.add(
                "CHATGPT_ARCHITECTURE_REVIEW"
            )

        if class_set.intersection(
            {
                "QUANT_ENGINE",
                "CROSS_BOUNDARY",
            }
        ):
            gate_set.update(
                {
                    "INDEPENDENT_AUDITOR_REVIEW",
                    "OWNER_AUTHORIZATION",
                }
            )

        gate_order = (
            "GOVERNANCE_BOOTSTRAP_GATE",
            "MACHINE_CHECKS",
            "CHATGPT_ARCHITECTURE_REVIEW",
            "INDEPENDENT_AUDITOR_REVIEW",
            "OWNER_AUTHORIZATION",
        )

        gates = tuple(
            gate
            for gate in gate_order
            if gate in gate_set
        )

    return ClassificationDecision(
        classification_outcome=outcome,
        detected_classes=tuple(classes),
        required_gate_union=tuple(gates),
        reasons=("test-evidence",),
    )


def _build(
    *,
    decision: ClassificationDecision | None = None,
    analysis: ReferenceSnapshotAnalysis | None = None,
):
    return build_classification_record(
        base_commit_sha1=BASE,
        head_commit_sha1=HEAD,
        merge_base_sha1=MERGE_BASE,
        base_tree_sha1=BASE_TREE,
        head_tree_sha1=HEAD_TREE,
        canonical_tree_delta=_delta(),
        classifier_spec_sha256=SHA256_A,
        classifier_implementation_sha256=SHA256_B,
        protected_surface_manifest_sha256=SHA256_C,
        classification_record_schema_sha256=SHA256_D,
        analyzer_config_sha256=SHA256_E,
        analyzer_toolchain_digest=TOOLCHAIN,
        analyzer_limits_sha256=SHA256_F,
        decision=decision or _decision(),
        reference_analysis=analysis or _analysis(),
        schema=SCHEMA,
    )


class RecordBuilderTests(unittest.TestCase):
    def test_builds_record_against_exact_frozen_schema(self) -> None:
        record = _build()

        self.assertEqual(
            record["schema_version"],
            "CLASSIFICATION_RECORD_V1",
        )
        self.assertEqual(
            record["base_commit_sha1"],
            BASE,
        )
        self.assertEqual(
            record["head_commit_sha1"],
            HEAD,
        )
        self.assertEqual(
            record["classification_outcome"],
            "CLASSIFIED",
        )
        self.assertEqual(
            record["detected_classes"],
            ["QUANT_ENGINE"],
        )
        self.assertEqual(
            record["failure_state"],
            "NONE",
        )
        self.assertEqual(
            len(record["canonical_tree_delta"]),
            1,
        )

    def test_unresolved_evidence_is_bound_into_ambiguous_record(self) -> None:
        unresolved = AnalysisUnresolvedNode(
            path_bytes=b"app/view.py",
            reason_code="DYNAMIC_IMPORT",
            reference_kind="DYNAMIC",
        )

        record = _build(
            decision=_decision(
                outcome="AMBIGUOUS",
                classes=("QUANT_ENGINE", "CROSS_BOUNDARY"),
            ),
            analysis=_analysis(
                unresolved_nodes=(unresolved,),
                unsupported_types=("yaml",),
            ),
        )

        self.assertEqual(
            record["classification_outcome"],
            "AMBIGUOUS",
        )
        self.assertIn(
            "CROSS_BOUNDARY",
            record["detected_classes"],
        )
        self.assertEqual(
            record["unresolved_nodes"][0]["reason_code"],
            "DYNAMIC_IMPORT",
        )
        self.assertEqual(
            record["unsupported_reference_file_types"],
            ["yaml"],
        )

    def test_ambiguous_without_cross_boundary_is_rejected(self) -> None:
        unresolved = AnalysisUnresolvedNode(
            path_bytes=b"app/view.py",
            reason_code="DYNAMIC_IMPORT",
            reference_kind="DYNAMIC",
        )

        with self.assertRaisesRegex(
            RecordBuilderError,
            "does not match reference evidence",
        ):
            _build(
                decision=_decision(
                    outcome="AMBIGUOUS",
                    classes=("QUANT_ENGINE",),
                ),
                analysis=_analysis(
                    unresolved_nodes=(unresolved,),
                ),
            )

    def test_decision_cannot_hide_reference_uncertainty(self) -> None:
        unresolved = AnalysisUnresolvedNode(
            path_bytes=b"app/view.py",
            reason_code="DYNAMIC_IMPORT",
            reference_kind="DYNAMIC",
        )

        with self.assertRaisesRegex(
            RecordBuilderError,
            "does not match reference evidence",
        ):
            _build(
                decision=_decision(
                    outcome="CLASSIFIED",
                    classes=("QUANT_ENGINE",),
                ),
                analysis=_analysis(
                    unresolved_nodes=(unresolved,),
                ),
            )

    def test_decision_cannot_hide_protected_reachability(self) -> None:
        with self.assertRaisesRegex(
            RecordBuilderError,
            "does not match reference evidence",
        ):
            _build(
                decision=_decision(
                    classes=("CROSS_BOUNDARY",),
                ),
                analysis=_analysis(),
            )

    def test_gate_union_must_match_detected_classes(self) -> None:
        with self.assertRaisesRegex(
            RecordBuilderError,
            "does not match reference evidence",
        ):
            _build(
                decision=_decision(
                    classes=("QUANT_ENGINE",),
                    gates=("MACHINE_CHECKS",),
                ),
                analysis=_analysis(),
            )

    def test_incomplete_scan_cannot_build_canonical_record(self) -> None:
        with self.assertRaisesRegex(
            RecordBuilderError,
            "complete successful reference scan",
        ):
            _build(
                analysis=_analysis(
                    scan_complete=False,
                )
            )

        with self.assertRaisesRegex(
            RecordBuilderError,
            "complete successful reference scan",
        ):
            _build(
                analysis=_analysis(
                    failed_reference_files=1,
                )
            )

    def test_canonical_bytes_are_deterministic_and_metadata_free(self) -> None:
        first = canonical_record_bytes(
            _build(),
            schema=SCHEMA,
            max_record_bytes=MAX_RECORD_BYTES,
        )
        second = canonical_record_bytes(
            _build(),
            schema=SCHEMA,
            max_record_bytes=MAX_RECORD_BYTES,
        )

        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertNotIn(b'"timestamp"', first)
        self.assertNotIn(b'"pid"', first)
        self.assertNotIn(b'"hostname"', first)
        self.assertNotIn(b'"random"', first)


if __name__ == "__main__":
    unittest.main()

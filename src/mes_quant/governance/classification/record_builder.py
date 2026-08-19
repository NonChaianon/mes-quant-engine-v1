from __future__ import annotations

import base64
from typing import Any, Iterable

from .classification_decision import (
    ClassificationDecision,
    ClassificationDecisionError,
    validate_classification_decision,
)
from .git_delta import DeltaEntry
from .record import validate_record
from .reference_analysis import ReferenceSnapshotAnalysis

REPOSITORY_ID = 1329447686
REPOSITORY_NODE_ID = "R_kgDOTz3DBg"


class RecordBuilderError(RuntimeError):
    """Raised when deterministic classifier facts cannot form a canonical record."""


def _closure_record(summary: Any) -> dict[str, object]:
    return {
        "reachable_protected": summary.reachable_protected,
        "unresolved_count": summary.unresolved_count,
        "visited_nodes": summary.visited_nodes,
        "visited_edges": summary.visited_edges,
    }


def _reference_scan_record(
    analysis: ReferenceSnapshotAnalysis,
) -> dict[str, object]:
    summary = analysis.reference_scan_summary

    return {
        "scan_complete": summary.scan_complete,
        "scanned_tracked_objects": summary.scanned_tracked_objects,
        "supported_reference_files": summary.supported_reference_files,
        "unsupported_reference_files": summary.unsupported_reference_files,
        "failed_reference_files": summary.failed_reference_files,
    }


def _unresolved_records(
    analysis: ReferenceSnapshotAnalysis,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    for item in analysis.unresolved_nodes:
        records.append(
            {
                "path_bytes_base64": base64.b64encode(
                    item.path_bytes
                ).decode("ascii"),
                "reason_code": item.reason_code,
                "reference_kind": item.reference_kind,
            }
        )

    return records


def build_classification_record(
    *,
    base_commit_sha1: str,
    head_commit_sha1: str,
    merge_base_sha1: str,
    base_tree_sha1: str,
    head_tree_sha1: str,
    canonical_tree_delta: Iterable[DeltaEntry],
    classifier_spec_sha256: str,
    classifier_implementation_sha256: str,
    protected_surface_manifest_sha256: str,
    classification_record_schema_sha256: str,
    analyzer_config_sha256: str,
    analyzer_toolchain_digest: str,
    analyzer_limits_sha256: str,
    decision: ClassificationDecision,
    reference_analysis: ReferenceSnapshotAnalysis,
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Build and validate one deterministic CLASSIFICATION_RECORD_V1.

    This function performs no persistence, remote mutation, merge decision,
    evidence write, candidate execution, or network access.
    """

    if (
        not reference_analysis.reference_scan_summary.scan_complete
        or reference_analysis.reference_scan_summary.failed_reference_files != 0
    ):
        raise RecordBuilderError(
            "canonical record requires a complete successful reference scan"
        )

    try:
        validate_classification_decision(
            decision,
            reference_analysis,
        )
    except ClassificationDecisionError as exc:
        raise RecordBuilderError(
            "classification decision does not match reference evidence"
        ) from exc

    delta_records = [
        entry.to_record()
        for entry in canonical_tree_delta
    ]

    record: dict[str, Any] = {
        "schema_version": "CLASSIFICATION_RECORD_V1",
        "repository_id": REPOSITORY_ID,
        "repository_node_id": REPOSITORY_NODE_ID,
        "base_commit_sha1": base_commit_sha1,
        "head_commit_sha1": head_commit_sha1,
        "merge_base_sha1": merge_base_sha1,
        "base_tree_sha1": base_tree_sha1,
        "head_tree_sha1": head_tree_sha1,
        "canonical_tree_delta": delta_records,
        "classifier_spec_sha256": classifier_spec_sha256,
        "classifier_implementation_sha256": classifier_implementation_sha256,
        "protected_surface_manifest_sha256": protected_surface_manifest_sha256,
        "classification_record_schema_sha256": classification_record_schema_sha256,
        "analyzer_config_sha256": analyzer_config_sha256,
        "analyzer_toolchain_digest": analyzer_toolchain_digest,
        "analyzer_limits_sha256": analyzer_limits_sha256,
        "classification_outcome": decision.classification_outcome,
        "detected_classes": list(decision.detected_classes),
        "forward_closure_summary": _closure_record(
            reference_analysis.graph_analysis.forward
        ),
        "reverse_closure_summary": _closure_record(
            reference_analysis.graph_analysis.reverse
        ),
        "reference_scan_summary": _reference_scan_record(
            reference_analysis
        ),
        "unresolved_nodes": _unresolved_records(
            reference_analysis
        ),
        "unsupported_reference_file_types": list(
            reference_analysis.unsupported_reference_file_types
        ),
        "required_gate_union": list(
            decision.required_gate_union
        ),
        "failure_state": "NONE",
    }

    validate_record(record, schema)

    return record

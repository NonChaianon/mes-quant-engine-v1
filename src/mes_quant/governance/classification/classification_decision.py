from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..sentinel.sentinel import GovernanceFacts
from .path_classification import CLASS_ORDER, PathClassification
from .reference_analysis import ReferenceSnapshotAnalysis

GATE_ORDER = (
    "GOVERNANCE_BOOTSTRAP_GATE",
    "MACHINE_CHECKS",
    "CHATGPT_ARCHITECTURE_REVIEW",
    "INDEPENDENT_AUDITOR_REVIEW",
    "OWNER_AUTHORIZATION",
)

_CLASS_GATES = {
    "GOVERNANCE_AMENDMENT": {
        "GOVERNANCE_BOOTSTRAP_GATE",
    },
    "UX_ONLY": {
        "MACHINE_CHECKS",
        "CHATGPT_ARCHITECTURE_REVIEW",
    },
    "QUANT_ENGINE": {
        "MACHINE_CHECKS",
        "INDEPENDENT_AUDITOR_REVIEW",
        "OWNER_AUTHORIZATION",
    },
    "CROSS_BOUNDARY": {
        "MACHINE_CHECKS",
        "CHATGPT_ARCHITECTURE_REVIEW",
        "INDEPENDENT_AUDITOR_REVIEW",
        "OWNER_AUTHORIZATION",
    },
}


class ClassificationDecisionError(RuntimeError):
    """Raised when Phase-2 classification facts cannot form a safe decision."""


@dataclass(frozen=True)
class ClassificationDecision:
    classification_outcome: str
    detected_classes: tuple[str, ...]
    required_gate_union: tuple[str, ...]
    reasons: tuple[str, ...]


def _ordered_classes(classes: Iterable[str]) -> tuple[str, ...]:
    values = set(classes)

    unknown = values.difference(CLASS_ORDER)

    if unknown:
        raise ClassificationDecisionError(
            "unknown classification token: "
            + ", ".join(sorted(unknown))
        )

    return tuple(
        name
        for name in CLASS_ORDER
        if name in values
    )


def _required_gates(
    classes: tuple[str, ...],
) -> tuple[str, ...]:
    gates: set[str] = set()

    for class_name in classes:
        try:
            gates.update(_CLASS_GATES[class_name])
        except KeyError as exc:
            raise ClassificationDecisionError(
                f"no gate mapping for class: {class_name}"
            ) from exc

    return tuple(
        gate
        for gate in GATE_ORDER
        if gate in gates
    )


def _semantic_uncertainty(
    reference_analysis: ReferenceSnapshotAnalysis,
) -> bool:
    forward = reference_analysis.graph_analysis.forward
    reverse = reference_analysis.graph_analysis.reverse

    return bool(
        reference_analysis.unresolved_nodes
        or reference_analysis.unsupported_reference_file_types
        or forward.unresolved_count
        or reverse.unresolved_count
    )


def validate_classification_decision(
    decision: ClassificationDecision,
    reference_analysis: ReferenceSnapshotAnalysis,
) -> None:
    """Require decision fields to agree with exact reference evidence."""

    if not isinstance(
        decision,
        ClassificationDecision,
    ):
        raise ClassificationDecisionError(
            "decision must be ClassificationDecision"
        )

    scan = reference_analysis.reference_scan_summary

    if not scan.scan_complete:
        raise ClassificationDecisionError(
            "incomplete reference scan cannot produce a decision"
        )

    if scan.failed_reference_files != 0:
        raise ClassificationDecisionError(
            "failed reference scan cannot produce a canonical decision"
        )

    canonical_classes = _ordered_classes(
        decision.detected_classes
    )

    if not canonical_classes:
        raise ClassificationDecisionError(
            "classification must produce at least one class"
        )

    if canonical_classes != decision.detected_classes:
        raise ClassificationDecisionError(
            "detected_classes must be canonical, ordered, and unique"
        )

    forward = reference_analysis.graph_analysis.forward
    reverse = reference_analysis.graph_analysis.reverse

    if (
        forward.reachable_protected
        or reverse.reachable_protected
    ) and "QUANT_ENGINE" not in canonical_classes:
        raise ClassificationDecisionError(
            "protected reachability requires QUANT_ENGINE"
        )

    semantic_uncertainty = _semantic_uncertainty(
        reference_analysis
    )

    if (
        semantic_uncertainty
        and "CROSS_BOUNDARY" not in canonical_classes
    ):
        raise ClassificationDecisionError(
            "semantic uncertainty requires CROSS_BOUNDARY"
        )

    expected_outcome = (
        "AMBIGUOUS"
        if semantic_uncertainty
        else "CLASSIFIED"
    )

    if decision.classification_outcome != expected_outcome:
        raise ClassificationDecisionError(
            "classification_outcome disagrees with reference evidence"
        )

    if (
        "UX_ONLY" in canonical_classes
        and (
            "QUANT_ENGINE" in canonical_classes
            or "CROSS_BOUNDARY" in canonical_classes
            or "GOVERNANCE_AMENDMENT"
            in canonical_classes
        )
    ):
        raise ClassificationDecisionError(
            "UX_ONLY cannot coexist with a conflicting protected class"
        )

    expected_gates = _required_gates(
        canonical_classes
    )

    if decision.required_gate_union != expected_gates:
        raise ClassificationDecisionError(
            "required_gate_union disagrees with detected_classes"
        )


def derive_classification_decision(
    path_classification: PathClassification,
    reference_analysis: ReferenceSnapshotAnalysis,
    governance_facts: GovernanceFacts,
) -> ClassificationDecision:
    """Combine deterministic path and capability/reference evidence.

    This layer routes evidence only. It never approves merge or mutates
    repository or remote state.
    """

    if not reference_analysis.reference_scan_summary.scan_complete:
        raise ClassificationDecisionError(
            "incomplete reference scan cannot produce a decision"
        )

    if reference_analysis.reference_scan_summary.failed_reference_files != 0:
        raise ClassificationDecisionError(
            "failed reference scan cannot produce a canonical decision"
        )

    if not isinstance(
        governance_facts,
        GovernanceFacts,
    ):
        raise ClassificationDecisionError(
            "governance_facts must use GovernanceFacts"
        )

    classes = set(path_classification.detected_classes)
    reasons = set(path_classification.reasons)

    if governance_facts.bootstrap_surface_hit:
        classes.add("GOVERNANCE_AMENDMENT")
        reasons.add("bootstrap-governance-surface")

    forward = reference_analysis.graph_analysis.forward
    reverse = reference_analysis.graph_analysis.reverse

    if forward.reachable_protected:
        classes.add("QUANT_ENGINE")
        reasons.add("forward-reaches-protected")

    if reverse.reachable_protected:
        classes.add("QUANT_ENGINE")
        reasons.add("protected-reaches-changed")

    semantic_uncertainty = _semantic_uncertainty(
        reference_analysis
    )

    if semantic_uncertainty:
        classes.add("CROSS_BOUNDARY")
        reasons.add("narrower-capability-separation-unproven")

    ordered_classes = _ordered_classes(classes)

    if not ordered_classes:
        raise ClassificationDecisionError(
            "classification must produce at least one class"
        )

    if (
        "UX_ONLY" in ordered_classes
        and (
            "QUANT_ENGINE" in ordered_classes
            or "CROSS_BOUNDARY" in ordered_classes
            or "GOVERNANCE_AMENDMENT" in ordered_classes
        )
    ):
        raise ClassificationDecisionError(
            "UX_ONLY cannot coexist with a conflicting protected class"
        )

    outcome = (
        "AMBIGUOUS"
        if semantic_uncertainty
        else "CLASSIFIED"
    )

    if outcome == "AMBIGUOUS" and "CROSS_BOUNDARY" not in ordered_classes:
        raise ClassificationDecisionError(
            "AMBIGUOUS must include CROSS_BOUNDARY"
        )

    decision = ClassificationDecision(
        classification_outcome=outcome,
        detected_classes=ordered_classes,
        required_gate_union=_required_gates(
            ordered_classes
        ),
        reasons=tuple(sorted(reasons)),
    )

    validate_classification_decision(
        decision,
        reference_analysis,
    )

    return decision

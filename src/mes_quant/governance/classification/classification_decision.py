from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

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


def derive_classification_decision(
    path_classification: PathClassification,
    reference_analysis: ReferenceSnapshotAnalysis,
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

    classes = set(path_classification.detected_classes)
    reasons = set(path_classification.reasons)

    forward = reference_analysis.graph_analysis.forward
    reverse = reference_analysis.graph_analysis.reverse

    if forward.reachable_protected:
        classes.add("QUANT_ENGINE")
        reasons.add("forward-reaches-protected")

    if reverse.reachable_protected:
        classes.add("QUANT_ENGINE")
        reasons.add("protected-reaches-changed")

    semantic_uncertainty = bool(
        reference_analysis.unresolved_nodes
        or reference_analysis.unsupported_reference_file_types
        or forward.unresolved_count
        or reverse.unresolved_count
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

    return ClassificationDecision(
        classification_outcome=outcome,
        detected_classes=ordered_classes,
        required_gate_union=_required_gates(
            ordered_classes
        ),
        reasons=tuple(sorted(reasons)),
    )

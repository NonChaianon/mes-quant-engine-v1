"""Closed, non-authoritative execution-hardening contract surfaces.

Phase A exposes deterministic validators only. Importing this package does not create
execution authority, consume a reservation, or access an artifact.
"""

from .boundary import (
    ArrowFieldContract,
    BoundaryReasonCode,
    BoundaryValidationError,
    DomainRule,
    OrderedArrowSchemaContract,
    consumer_rehearsal,
    identity_bytes,
    normalize_integral_flag,
    require_finite_scalar,
    validate_ordered_arrow_schema,
)
from .records import (
    ExecutionRecord,
    RecordReasonCode,
    RecordValidationError,
    TransitionContract,
    TransitionResult,
    apply_transition,
    load_transition_contract,
    validate_execution_record,
)

__all__ = [
    "ArrowFieldContract",
    "BoundaryReasonCode",
    "BoundaryValidationError",
    "DomainRule",
    "ExecutionRecord",
    "OrderedArrowSchemaContract",
    "RecordReasonCode",
    "RecordValidationError",
    "TransitionContract",
    "TransitionResult",
    "apply_transition",
    "consumer_rehearsal",
    "identity_bytes",
    "load_transition_contract",
    "normalize_integral_flag",
    "require_finite_scalar",
    "validate_execution_record",
    "validate_ordered_arrow_schema",
]

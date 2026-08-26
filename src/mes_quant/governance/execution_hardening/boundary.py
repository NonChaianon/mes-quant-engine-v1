"""Versioned shared boundary checks for synthetic Tier 1 contract rehearsal.

This module accepts in-memory values only. It has no filesystem or scientific-runner adapter and
cannot read a real artifact, construct a scientific target, or fit a model.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from numbers import Integral, Real
from typing import Any

import pyarrow as pa

NON_EVIDENTIARY_TIER1_FIXTURE = "NON_EVIDENTIARY_TIER1_FIXTURE"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class BoundaryReasonCode(StrEnum):
    """Closed reason codes emitted by the shared boundary validator."""

    IDENTITY_TYPE_INVALID = "IDENTITY_TYPE_INVALID"
    IDENTITY_UTF8_INVALID = "IDENTITY_UTF8_INVALID"
    IDENTITY_EMPTY = "IDENTITY_EMPTY"
    IDENTITY_CRLF_FORBIDDEN = "IDENTITY_CRLF_FORBIDDEN"
    FINITE_SCALAR_TYPE_INVALID = "FINITE_SCALAR_TYPE_INVALID"
    FINITE_SCALAR_REQUIRED = "FINITE_SCALAR_REQUIRED"
    INTEGRAL_BOOLEAN_TYPE_INVALID = "INTEGRAL_BOOLEAN_TYPE_INVALID"
    INTEGRAL_BOOLEAN_DOMAIN_INVALID = "INTEGRAL_BOOLEAN_DOMAIN_INVALID"
    ARROW_SCHEMA_TYPE_INVALID = "ARROW_SCHEMA_TYPE_INVALID"
    ARROW_SCHEMA_CONTRACT_INVALID = "ARROW_SCHEMA_CONTRACT_INVALID"
    ARROW_SCHEMA_CONTRACT_MISMATCH = "ARROW_SCHEMA_CONTRACT_MISMATCH"
    CONSUMER_REHEARSAL_FIXTURE_INVALID = "CONSUMER_REHEARSAL_FIXTURE_INVALID"
    CONSUMER_REHEARSAL_CONSUMER_INVALID = "CONSUMER_REHEARSAL_CONSUMER_INVALID"
    CONSUMER_REHEARSAL_EMPTY = "CONSUMER_REHEARSAL_EMPTY"
    CONSUMER_REHEARSAL_NULLABILITY_INVALID = "CONSUMER_REHEARSAL_NULLABILITY_INVALID"
    CONSUMER_REHEARSAL_VALUE_INVALID = "CONSUMER_REHEARSAL_VALUE_INVALID"


class BoundaryValidationError(ValueError):
    """Fail-closed boundary error carrying one exact machine reason code."""

    def __init__(self, reason_code: BoundaryReasonCode, detail: str) -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code.value}: {detail}")


def identity_bytes(value: str | bytes) -> bytes:
    """Return the exact UTF-8 bytes without stripping or Unicode normalization.

    The pipe byte is ordinary identity content. CR and LF are the only forbidden characters in
    this shared grammar; downstream stages may impose separately ratified constraints.
    """

    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise BoundaryValidationError(
                BoundaryReasonCode.IDENTITY_UTF8_INVALID,
                "identity is not strict UTF-8",
            ) from exc
    elif isinstance(value, bytes):
        encoded = value
        try:
            decoded = encoded.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise BoundaryValidationError(
                BoundaryReasonCode.IDENTITY_UTF8_INVALID,
                "identity bytes are not strict UTF-8",
            ) from exc
        if decoded.encode("utf-8") != encoded:
            raise BoundaryValidationError(
                BoundaryReasonCode.IDENTITY_UTF8_INVALID,
                "identity bytes do not round-trip through strict UTF-8",
            )
    else:
        raise BoundaryValidationError(
            BoundaryReasonCode.IDENTITY_TYPE_INVALID,
            "identity must be str or bytes",
        )

    if not encoded:
        raise BoundaryValidationError(
            BoundaryReasonCode.IDENTITY_EMPTY,
            "identity must be non-empty",
        )
    if b"\r" in encoded or b"\n" in encoded:
        raise BoundaryValidationError(
            BoundaryReasonCode.IDENTITY_CRLF_FORBIDDEN,
            "identity contains CR or LF",
        )
    return encoded


def require_finite_scalar(value: Real) -> float:
    """Classify a scalar as finite while rejecting booleans and string coercion."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise BoundaryValidationError(
            BoundaryReasonCode.FINITE_SCALAR_TYPE_INVALID,
            "value must be a real numeric scalar and not bool",
        )
    normalized = float(value)
    if not math.isfinite(normalized):
        raise BoundaryValidationError(
            BoundaryReasonCode.FINITE_SCALAR_REQUIRED,
            "numeric scalar must be finite",
        )
    return normalized


def normalize_integral_flag(value: Integral) -> bool:
    """Normalize the exact integral domain ``{0, 1}`` to bool."""

    if not isinstance(value, Integral):
        raise BoundaryValidationError(
            BoundaryReasonCode.INTEGRAL_BOOLEAN_TYPE_INVALID,
            "flag must be an integral scalar",
        )
    normalized = int(value)
    if normalized not in (0, 1):
        raise BoundaryValidationError(
            BoundaryReasonCode.INTEGRAL_BOOLEAN_DOMAIN_INVALID,
            "integral flag domain is exactly {0, 1}",
        )
    return bool(normalized)


class DomainRule(StrEnum):
    """Closed semantic rules available to the shared consumer rehearsal."""

    NONE = "NONE"
    IDENTITY_UTF8_NO_CRLF = "IDENTITY_UTF8_NO_CRLF"
    FINITE_SCALAR = "FINITE_SCALAR"
    INTEGRAL_BOOLEAN_01 = "INTEGRAL_BOOLEAN_01"


@dataclass(frozen=True, slots=True)
class ArrowFieldContract:
    """One ordered Arrow consumer-projection field."""

    name: str
    logical_type: str
    nullable: bool
    domain_rule: DomainRule
    producer_contract_version: str
    producer_contract_sha256: str


@dataclass(frozen=True, slots=True)
class OrderedArrowSchemaContract:
    """Closed ordered projection plus its producer identity."""

    fields: tuple[ArrowFieldContract, ...]

    def canonical_bytes(self) -> bytes:
        payload = {
            "schema_version": "MES_ORDERED_ARROW_SCHEMA_CONTRACT_V1",
            "fields": [
                {
                    "name": field.name,
                    "logical_type": field.logical_type,
                    "nullable": field.nullable,
                    "domain_rule": field.domain_rule.value,
                    "producer_contract_version": field.producer_contract_version,
                    "producer_contract_sha256": field.producer_contract_sha256,
                }
                for field in self.fields
            ],
        }
        return (
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            + "\n"
        ).encode("utf-8")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _validate_contract(contract: OrderedArrowSchemaContract) -> None:
    if not isinstance(contract, OrderedArrowSchemaContract) or not contract.fields:
        raise BoundaryValidationError(
            BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
            "schema contract must contain at least one field",
        )

    names: set[str] = set()
    for index, field in enumerate(contract.fields):
        if not isinstance(field, ArrowFieldContract):
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
                f"field {index} is not ArrowFieldContract",
            )
        if not isinstance(field.name, str) or not field.name or field.name in names:
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
                f"field {index} has empty or duplicate name",
            )
        names.add(field.name)
        if (
            not isinstance(field.logical_type, str)
            or not field.logical_type
            or not isinstance(field.nullable, bool)
            or not isinstance(field.domain_rule, DomainRule)
        ):
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
                f"field {field.name} has invalid type/nullability contract",
            )
        if (
            not isinstance(field.producer_contract_version, str)
            or not field.producer_contract_version
        ):
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
                f"field {field.name} lacks producer contract version",
            )
        if (
            not isinstance(field.producer_contract_sha256, str)
            or _SHA256_RE.fullmatch(field.producer_contract_sha256) is None
        ):
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
                f"field {field.name} has invalid producer contract SHA-256",
            )


def validate_ordered_arrow_schema(
    schema: pa.Schema,
    contract: OrderedArrowSchemaContract,
) -> str:
    """Validate exact field order, logical types, and nullability without reading values."""

    _validate_contract(contract)
    if not isinstance(schema, pa.Schema):
        raise BoundaryValidationError(
            BoundaryReasonCode.ARROW_SCHEMA_TYPE_INVALID,
            "schema must be pyarrow.Schema",
        )

    if len(schema) != len(contract.fields):
        raise BoundaryValidationError(
            BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_MISMATCH,
            "projected field count differs from the frozen contract",
        )

    for index, (actual, expected) in enumerate(zip(schema, contract.fields, strict=True)):
        if (
            actual.name != expected.name
            or str(actual.type) != expected.logical_type
            or actual.nullable is not expected.nullable
        ):
            raise BoundaryValidationError(
                BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_MISMATCH,
                "field mismatch at index "
                f"{index}: actual=({actual.name},{actual.type},{actual.nullable}) "
                f"expected=({expected.name},{expected.logical_type},{expected.nullable})",
            )
    return contract.sha256


def _normalize_value(value: Any, field: ArrowFieldContract) -> Any:
    if value is None:
        if field.nullable:
            return None
        raise BoundaryValidationError(
            BoundaryReasonCode.CONSUMER_REHEARSAL_NULLABILITY_INVALID,
            f"non-nullable field {field.name} contains null",
        )

    try:
        if field.domain_rule is DomainRule.NONE:
            return value
        if field.domain_rule is DomainRule.IDENTITY_UTF8_NO_CRLF:
            return identity_bytes(value).decode("utf-8")
        if field.domain_rule is DomainRule.FINITE_SCALAR:
            return require_finite_scalar(value)
        if field.domain_rule is DomainRule.INTEGRAL_BOOLEAN_01:
            return normalize_integral_flag(value)
    except BoundaryValidationError:
        raise
    except (TypeError, ValueError, OverflowError) as exc:
        raise BoundaryValidationError(
            BoundaryReasonCode.CONSUMER_REHEARSAL_VALUE_INVALID,
            f"field {field.name} could not be normalized",
        ) from exc

    raise BoundaryValidationError(
        BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID,
        f"field {field.name} has unknown domain rule",
    )


def consumer_rehearsal(
    table: pa.Table | pa.RecordBatch,
    contract: OrderedArrowSchemaContract,
    consumer: Callable[[Mapping[str, Any]], Any],
    *,
    fixture_identity: str,
) -> tuple[Any, ...]:
    """Exercise an in-memory consumer with at least one type-correct synthetic Arrow row."""

    if fixture_identity != NON_EVIDENTIARY_TIER1_FIXTURE:
        raise BoundaryValidationError(
            BoundaryReasonCode.CONSUMER_REHEARSAL_FIXTURE_INVALID,
            "consumer rehearsal accepts only the non-evidentiary Tier 1 fixture identity",
        )
    if not callable(consumer):
        raise BoundaryValidationError(
            BoundaryReasonCode.CONSUMER_REHEARSAL_CONSUMER_INVALID,
            "consumer rehearsal requires a callable adapter",
        )
    if not isinstance(table, (pa.Table, pa.RecordBatch)):
        raise BoundaryValidationError(
            BoundaryReasonCode.ARROW_SCHEMA_TYPE_INVALID,
            "consumer rehearsal requires pyarrow.Table or RecordBatch",
        )

    validate_ordered_arrow_schema(table.schema, contract)
    if table.num_rows == 0:
        raise BoundaryValidationError(
            BoundaryReasonCode.CONSUMER_REHEARSAL_EMPTY,
            "zero-row consumer rehearsal is forbidden",
        )

    outputs: list[Any] = []
    for row_index in range(table.num_rows):
        row: dict[str, Any] = {}
        for column_index, field in enumerate(contract.fields):
            value = table.column(column_index)[row_index].as_py()
            row[field.name] = _normalize_value(value, field)
        outputs.append(consumer(row))
    return tuple(outputs)

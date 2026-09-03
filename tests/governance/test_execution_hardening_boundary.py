from __future__ import annotations

import math

import pyarrow as pa
import pytest

from mes_quant.governance.execution_hardening.boundary import (
    NON_EVIDENTIARY_TIER1_FIXTURE,
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

PRODUCER_SHA256 = "a" * 64


def _field(
    name: str,
    logical_type: str,
    nullable: bool,
    domain_rule: DomainRule,
) -> ArrowFieldContract:
    return ArrowFieldContract(
        name=name,
        logical_type=logical_type,
        nullable=nullable,
        domain_rule=domain_rule,
        producer_contract_version="SYNTHETIC_PRODUCER_V1",
        producer_contract_sha256=PRODUCER_SHA256,
    )


def _contract() -> OrderedArrowSchemaContract:
    return OrderedArrowSchemaContract(
        fields=(
            _field("identity", "string", False, DomainRule.IDENTITY_UTF8_NO_CRLF),
            _field("early_close_session", "int8", False, DomainRule.INTEGRAL_BOOLEAN_01),
            _field("metric", "double", False, DomainRule.FINITE_SCALAR),
            _field("path_instrument_changed", "int8", True, DomainRule.INTEGRAL_BOOLEAN_01),
        )
    )


def _schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("identity", pa.string(), nullable=False),
            pa.field("early_close_session", pa.int8(), nullable=False),
            pa.field("metric", pa.float64(), nullable=False),
            pa.field("path_instrument_changed", pa.int8(), nullable=True),
        ]
    )


def _table(*, flags: list[int] | None = None) -> pa.Table:
    values = flags or [0, 1]
    return pa.Table.from_arrays(
        [
            pa.array(["MES|2026-08-26", "MES|2026-08-27"], type=pa.string()),
            pa.array(values, type=pa.int8()),
            pa.array([1.25, 2.5], type=pa.float64()),
            pa.array([None, 1], type=pa.int8()),
        ],
        schema=_schema(),
    )


def _assert_reason(error: pytest.ExceptionInfo[BoundaryValidationError], code: BoundaryReasonCode) -> None:
    assert error.value.reason_code is code
    assert str(error.value).startswith(f"{code.value}:")


def test_identity_preserves_pipe_and_utf8_bytes_exactly() -> None:
    identity = "MES|ก่อนเปิด|2026"
    assert identity_bytes(identity) == identity.encode("utf-8")
    assert identity_bytes(identity.encode("utf-8")) == identity.encode("utf-8")


@pytest.mark.parametrize("value", ["MES\n2026", "MES\r2026", b"MES\r\n2026"])
def test_identity_rejects_cr_or_lf_with_exact_reason(value: str | bytes) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        identity_bytes(value)
    _assert_reason(error, BoundaryReasonCode.IDENTITY_CRLF_FORBIDDEN)


def test_identity_rejects_empty_and_invalid_utf8_without_normalization() -> None:
    with pytest.raises(BoundaryValidationError) as empty:
        identity_bytes("")
    _assert_reason(empty, BoundaryReasonCode.IDENTITY_EMPTY)

    with pytest.raises(BoundaryValidationError) as invalid:
        identity_bytes(b"\xff")
    _assert_reason(invalid, BoundaryReasonCode.IDENTITY_UTF8_INVALID)


@pytest.mark.parametrize("value", [0, -7, 1.5, 10**30])
def test_finite_scalar_accepts_real_finite_values(value: float) -> None:
    assert math.isfinite(require_finite_scalar(value))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_finite_scalar_rejects_nonfinite(value: float) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        require_finite_scalar(value)
    _assert_reason(error, BoundaryReasonCode.FINITE_SCALAR_REQUIRED)


@pytest.mark.parametrize("value", ["1", object(), True])
def test_finite_scalar_rejects_coercion_and_bool(value: object) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        require_finite_scalar(value)  # type: ignore[arg-type]
    _assert_reason(error, BoundaryReasonCode.FINITE_SCALAR_TYPE_INVALID)


def test_integral_flag_normalizes_exact_zero_one_domain() -> None:
    assert normalize_integral_flag(0) is False
    assert normalize_integral_flag(1) is True
    assert normalize_integral_flag(False) is False
    assert normalize_integral_flag(True) is True


@pytest.mark.parametrize("value", [-1, 2, 127])
def test_integral_flag_rejects_outside_domain(value: int) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        normalize_integral_flag(value)
    _assert_reason(error, BoundaryReasonCode.INTEGRAL_BOOLEAN_DOMAIN_INVALID)


@pytest.mark.parametrize("value", [0.0, 1.0, "1"])
def test_integral_flag_rejects_nonintegral_types(value: object) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        normalize_integral_flag(value)  # type: ignore[arg-type]
    _assert_reason(error, BoundaryReasonCode.INTEGRAL_BOOLEAN_TYPE_INVALID)


def test_schema_contract_pins_order_type_nullability_and_producer_identity() -> None:
    contract = _contract()
    assert validate_ordered_arrow_schema(_schema(), contract) == contract.sha256
    assert len(contract.sha256) == 64

    reordered = pa.schema(list(reversed(_schema())))
    with pytest.raises(BoundaryValidationError) as order_error:
        validate_ordered_arrow_schema(reordered, contract)
    _assert_reason(order_error, BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_MISMATCH)

    wrong_type = _schema().set(1, pa.field("early_close_session", pa.bool_(), nullable=False))
    with pytest.raises(BoundaryValidationError) as type_error:
        validate_ordered_arrow_schema(wrong_type, contract)
    _assert_reason(type_error, BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_MISMATCH)

    wrong_nullability = _schema().set(0, pa.field("identity", pa.string(), nullable=True))
    with pytest.raises(BoundaryValidationError) as null_error:
        validate_ordered_arrow_schema(wrong_nullability, contract)
    _assert_reason(null_error, BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_MISMATCH)


def test_contract_rejects_bad_or_duplicate_producer_bindings() -> None:
    bad_hash = OrderedArrowSchemaContract(
        fields=(
            ArrowFieldContract(
                name="identity",
                logical_type="string",
                nullable=False,
                domain_rule=DomainRule.IDENTITY_UTF8_NO_CRLF,
                producer_contract_version="V1",
                producer_contract_sha256="not-a-hash",
            ),
        )
    )
    with pytest.raises(BoundaryValidationError) as hash_error:
        validate_ordered_arrow_schema(pa.schema([pa.field("identity", pa.string(), False)]), bad_hash)
    _assert_reason(hash_error, BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID)

    duplicate = OrderedArrowSchemaContract(fields=(_contract().fields[0], _contract().fields[0]))
    with pytest.raises(BoundaryValidationError) as duplicate_error:
        validate_ordered_arrow_schema(
            pa.schema(
                [
                    pa.field("identity", pa.string(), False),
                    pa.field("identity", pa.string(), False),
                ]
            ),
            duplicate,
        )
    _assert_reason(duplicate_error, BoundaryReasonCode.ARROW_SCHEMA_CONTRACT_INVALID)


def test_nonempty_consumer_rehearsal_uses_scalar_types_and_preserves_nullability() -> None:
    rows = consumer_rehearsal(
        _table(),
        _contract(),
        lambda row: dict(row),
        fixture_identity=NON_EVIDENTIARY_TIER1_FIXTURE,
    )
    assert rows == (
        {
            "identity": "MES|2026-08-26",
            "early_close_session": False,
            "metric": 1.25,
            "path_instrument_changed": None,
        },
        {
            "identity": "MES|2026-08-27",
            "early_close_session": True,
            "metric": 2.5,
            "path_instrument_changed": True,
        },
    )


def test_zero_row_consumer_rehearsal_is_forbidden() -> None:
    empty = pa.Table.from_batches([], schema=_schema())
    with pytest.raises(BoundaryValidationError) as error:
        consumer_rehearsal(
            empty,
            _contract(),
            lambda row: row,
            fixture_identity=NON_EVIDENTIARY_TIER1_FIXTURE,
        )
    _assert_reason(error, BoundaryReasonCode.CONSUMER_REHEARSAL_EMPTY)


@pytest.mark.parametrize("invalid_flag", [-1, 2])
def test_consumer_rehearsal_rejects_integral_flag_landmines(invalid_flag: int) -> None:
    with pytest.raises(BoundaryValidationError) as error:
        consumer_rehearsal(
            _table(flags=[invalid_flag, 1]),
            _contract(),
            lambda row: row,
            fixture_identity=NON_EVIDENTIARY_TIER1_FIXTURE,
        )
    _assert_reason(error, BoundaryReasonCode.INTEGRAL_BOOLEAN_DOMAIN_INVALID)


def test_consumer_rehearsal_rejects_untrusted_fixture_identity() -> None:
    with pytest.raises(BoundaryValidationError) as error:
        consumer_rehearsal(
            _table(),
            _contract(),
            lambda row: row,
            fixture_identity="REAL_DATA",
        )
    _assert_reason(error, BoundaryReasonCode.CONSUMER_REHEARSAL_FIXTURE_INVALID)


def test_consumer_rehearsal_requires_callable_adapter() -> None:
    with pytest.raises(BoundaryValidationError) as error:
        consumer_rehearsal(
            _table(),
            _contract(),
            None,  # type: ignore[arg-type]
            fixture_identity=NON_EVIDENTIARY_TIER1_FIXTURE,
        )
    _assert_reason(error, BoundaryReasonCode.CONSUMER_REHEARSAL_CONSUMER_INVALID)

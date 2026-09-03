from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

PHASE_A_MODE = "TIER1_ONLY_NON_AUTHORITATIVE"
TIER1_FIXTURE_IDENTITY = "NON_EVIDENTIARY_TIER1_FIXTURE"
TIER1_PASS = "TIER1_CONTRACT_PASS_NO_RUNTIME_EXECUTION"
TIER2_NOT_AUTHORIZED = "TIER2_RUNTIME_REHEARSAL_NOT_AUTHORIZED_PHASE_A"
HANDLE_INJECTION_STOP = "PRODUCTION_HANDLE_INJECTION_STOP_BEFORE_RESERVATION"


@dataclass(frozen=True)
class ProtectedCounters:
    """Counters whose Phase-A value is required to remain exactly zero."""

    live_tier2_reservations_created: int = 0
    live_tier2_reservations_consumed: int = 0
    tier2_attempts: int = 0
    runtime_rehearsal_runner_executions: int = 0
    persisted_attempt_ledgers: int = 0
    emitted_or_persisted_or_sealed_or_uploaded_or_attested_or_registered_rehearsal_records: int = (
        0
    )
    phase_a_hardening_runtime_synthetic_models_fitted: int = 0
    phase_a_hardening_runtime_synthetic_fold_fit_calls: int = 0
    phase_a_hardening_runtime_synthetic_bootstrap_replicates: int = 0
    phase_a_hardening_runtime_synthetic_economic_diagnostic_calls: int = 0
    phase_a_hardening_runtime_synthetic_economic_policy_evaluations: int = 0
    real_artifact_metadata_reads: int = 0
    real_row_group_or_statistics_or_numeric_value_reads: int = 0
    real_target_or_path_reads: int = 0
    real_targets_constructed: int = 0
    real_models_or_fold_fits: int = 0
    real_bootstrap_replicates: int = 0
    real_economic_diagnostic_calls: int = 0
    validation_reads: int = 0
    final_test_reads: int = 0
    production_scientific_outputs: int = 0
    hypothesis_slots_consumed: int = 0

    def as_mapping(self) -> dict[str, int]:
        return asdict(self)

    def assert_zero(self) -> None:
        nonzero = {name: value for name, value in self.as_mapping().items() if value != 0}
        if nonzero:
            raise ValueError(f"PHASE_A_PROTECTED_COUNTER_NONZERO: {nonzero}")


@dataclass(frozen=True)
class Cell12State:
    """Synthetic-only Cell 12 consumer state used by Tier-1 fixtures."""

    label_reason: str = "LABEL_USABLE"
    path_instrument_changed: bool | None = False
    path_count: int | None = 1
    path_metric: float | None = 1.0


@dataclass(frozen=True)
class Tier1Fixture:
    """A non-evidentiary, in-memory representation of the pre-fit contract."""

    fixture_identity: str
    predictors: tuple[float, ...]
    target_values: tuple[float | None, ...]
    session_coordinates: tuple[int, ...]
    cell12_states: tuple[Cell12State, ...]
    row_eligible: tuple[bool, ...]
    injected_handles: Mapping[str, object] = field(default_factory=dict)
    minimum_fold_support: int = 2
    minimum_design_rank: int = 4


@dataclass(frozen=True)
class SyntheticFold:
    fold_id: str
    row_indices: tuple[int, ...]


@dataclass(frozen=True)
class Tier1Outcome:
    fixture_identity: str
    status: str
    stage: str
    reason_code: str
    protected_counters: ProtectedCounters
    predictor_ledger_count: int = 0
    predictor_ledger_sha256: str | None = None
    request_count: int = 0
    request_sha256: str | None = None
    target_ledger_count: int = 0
    target_ledger_sha256: str | None = None
    cell12_reason_codes: tuple[str, ...] = ()
    common_mask_created: bool = False
    common_mask_rows: tuple[int, ...] = ()
    folds: tuple[SyntheticFold, ...] = ()
    harmonic_basis_sha256: str | None = None
    design_rank: int | None = None
    minimum_fold_support_observed: int | None = None
    output_path: None = None
    output_emitted: bool = False
    live_tier2_reservation_created: bool = False
    live_tier2_reservation_consumed: bool = False
    tier2_eligible: bool = False

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["protected_counters"] = self.protected_counters.as_mapping()
        return payload


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def default_tier1_fixture() -> Tier1Fixture:
    target_values = (0.20, 0.33, 0.24, 0.48, 0.31, 0.56, 0.37, 0.63)
    return Tier1Fixture(
        fixture_identity=TIER1_FIXTURE_IDENTITY,
        predictors=(1.0, 1.4, 2.1, 2.8, 3.6, 4.7, 6.1, 7.9),
        target_values=target_values,
        session_coordinates=tuple(range(len(target_values))),
        cell12_states=tuple(Cell12State() for _ in target_values),
        row_eligible=tuple(True for _ in target_values),
    )


def _scalar_token(value: float | None) -> Mapping[str, Any]:
    if value is None:
        return {"kind": "NULL"}
    number = float(value)
    if math.isnan(number):
        return {"kind": "NONFINITE", "value": "NAN"}
    if number == math.inf:
        return {"kind": "NONFINITE", "value": "POSITIVE_INFINITY"}
    if number == -math.inf:
        return {"kind": "NONFINITE", "value": "NEGATIVE_INFINITY"}
    return {"kind": "FINITE", "value": number}


def _stop(
    fixture: Tier1Fixture,
    *,
    stage: str,
    reason_code: str,
    predictor_count: int = 0,
    predictor_sha256: str | None = None,
    request_count: int = 0,
    request_sha256: str | None = None,
    target_count: int = 0,
    target_sha256: str | None = None,
    cell12_reason_codes: tuple[str, ...] = (),
    common_mask_created: bool = False,
    common_mask_rows: tuple[int, ...] = (),
    folds: tuple[SyntheticFold, ...] = (),
    harmonic_basis_sha256: str | None = None,
    design_rank: int | None = None,
    minimum_fold_support_observed: int | None = None,
) -> Tier1Outcome:
    counters = ProtectedCounters()
    counters.assert_zero()
    return Tier1Outcome(
        fixture_identity=fixture.fixture_identity,
        status="STOP",
        stage=stage,
        reason_code=reason_code,
        protected_counters=counters,
        predictor_ledger_count=predictor_count,
        predictor_ledger_sha256=predictor_sha256,
        request_count=request_count,
        request_sha256=request_sha256,
        target_ledger_count=target_count,
        target_ledger_sha256=target_sha256,
        cell12_reason_codes=cell12_reason_codes,
        common_mask_created=common_mask_created,
        common_mask_rows=common_mask_rows,
        folds=folds,
        harmonic_basis_sha256=harmonic_basis_sha256,
        design_rank=design_rank,
        minimum_fold_support_observed=minimum_fold_support_observed,
    )


def _matrix_rank(rows: Sequence[Sequence[float]], *, tolerance: float = 1e-12) -> int:
    matrix = [list(map(float, row)) for row in rows]
    if not matrix:
        return 0
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("SYNTHETIC_DESIGN_MATRIX_WIDTH_MISMATCH")

    rank = 0
    column = 0
    while rank < len(matrix) and column < width:
        pivot = max(range(rank, len(matrix)), key=lambda index: abs(matrix[index][column]))
        if abs(matrix[pivot][column]) <= tolerance:
            column += 1
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        pivot_value = matrix[rank][column]
        matrix[rank] = [value / pivot_value for value in matrix[rank]]
        for row_index, row in enumerate(matrix):
            if row_index == rank:
                continue
            factor = row[column]
            if abs(factor) <= tolerance:
                continue
            matrix[row_index] = [
                value - factor * pivot_component
                for value, pivot_component in zip(row, matrix[rank], strict=True)
            ]
        rank += 1
        column += 1
    return rank


def evaluate_tier1_fixture(fixture: Tier1Fixture) -> Tier1Outcome:
    """Evaluate only the deterministic pre-fit Tier-1 contract.

    This function intentionally has no fitter, bootstrap, economic-diagnostic, reservation,
    evidence, registry, signing, network, or production-handle dependency.
    """

    if fixture.fixture_identity != TIER1_FIXTURE_IDENTITY:
        return _stop(
            fixture,
            stage="CONTRACT",
            reason_code="TIER1_FIXTURE_IDENTITY_INVALID",
        )
    if fixture.injected_handles:
        return _stop(fixture, stage="CONTRACT", reason_code=HANDLE_INJECTION_STOP)

    row_count = len(fixture.predictors)
    lengths = {
        row_count,
        len(fixture.target_values),
        len(fixture.session_coordinates),
        len(fixture.cell12_states),
        len(fixture.row_eligible),
    }
    if len(lengths) != 1 or row_count == 0:
        return _stop(
            fixture,
            stage="CONTRACT",
            reason_code="SYNTHETIC_FIXTURE_LENGTH_MISMATCH",
        )

    predictor_rows = [
        {"row_index": index, "predictor": _scalar_token(value)}
        for index, value in enumerate(fixture.predictors)
    ]
    predictor_sha256 = canonical_sha256(predictor_rows)
    for value in fixture.predictors:
        if not math.isfinite(float(value)):
            return _stop(
                fixture,
                stage="PRE_TARGET",
                reason_code="PREDICTOR_NONFINITE",
                predictor_count=row_count,
                predictor_sha256=predictor_sha256,
            )
        if float(value) <= 0.0:
            return _stop(
                fixture,
                stage="PRE_TARGET",
                reason_code="PREDICTOR_NONPOSITIVE",
                predictor_count=row_count,
                predictor_sha256=predictor_sha256,
            )

    requests = [
        {"ordinal": index, "request_id": f"SYNTHETIC_REQUEST_{index:04d}"}
        for index in range(row_count)
    ]
    request_sha256 = canonical_sha256(requests)
    reason_codes = tuple(state.label_reason for state in fixture.cell12_states)
    target_rows = [
        {
            "ordinal": index,
            "request_id": requests[index]["request_id"],
            "target": _scalar_token(fixture.target_values[index]),
            "cell12": asdict(fixture.cell12_states[index]),
        }
        for index in range(row_count)
    ]
    target_sha256 = canonical_sha256(target_rows)
    finite_usable_targets = [
        float(value)
        for value, state, eligible in zip(
            fixture.target_values,
            fixture.cell12_states,
            fixture.row_eligible,
            strict=True,
        )
        if value is not None
        and math.isfinite(float(value))
        and state.label_reason == "LABEL_USABLE"
        and eligible
    ]
    if len(finite_usable_targets) < 2:
        return _stop(
            fixture,
            stage="TARGET_PREFIT",
            reason_code="TARGET_INSUFFICIENT_SUPPORT",
            predictor_count=row_count,
            predictor_sha256=predictor_sha256,
            request_count=row_count,
            request_sha256=request_sha256,
            target_count=row_count,
            target_sha256=target_sha256,
            cell12_reason_codes=reason_codes,
        )
    if max(finite_usable_targets) == min(finite_usable_targets):
        return _stop(
            fixture,
            stage="TARGET_PREFIT",
            reason_code="TARGET_ZERO_VARIANCE",
            predictor_count=row_count,
            predictor_sha256=predictor_sha256,
            request_count=row_count,
            request_sha256=request_sha256,
            target_count=row_count,
            target_sha256=target_sha256,
            cell12_reason_codes=reason_codes,
        )

    common_mask_rows = tuple(
        index
        for index, (value, state, eligible) in enumerate(
            zip(
                fixture.target_values,
                fixture.cell12_states,
                fixture.row_eligible,
                strict=True,
            )
        )
        if eligible
        and value is not None
        and math.isfinite(float(value))
        and state.label_reason == "LABEL_USABLE"
    )
    midpoint = len(common_mask_rows) // 2
    folds = (
        SyntheticFold("SYNTHETIC_FOLD_0", common_mask_rows[:midpoint]),
        SyntheticFold("SYNTHETIC_FOLD_1", common_mask_rows[midpoint:]),
    )
    if set(folds[0].row_indices) & set(folds[1].row_indices):
        return _stop(
            fixture,
            stage="TARGET_PREFIT",
            reason_code="SYNTHETIC_FOLD_OVERLAP",
            predictor_count=row_count,
            predictor_sha256=predictor_sha256,
            request_count=row_count,
            request_sha256=request_sha256,
            target_count=row_count,
            target_sha256=target_sha256,
            cell12_reason_codes=reason_codes,
            common_mask_created=True,
            common_mask_rows=common_mask_rows,
            folds=folds,
        )
    minimum_support = min(len(fold.row_indices) for fold in folds)
    if minimum_support < fixture.minimum_fold_support:
        return _stop(
            fixture,
            stage="TARGET_PREFIT",
            reason_code="FOLD_SUPPORT_INSUFFICIENT",
            predictor_count=row_count,
            predictor_sha256=predictor_sha256,
            request_count=row_count,
            request_sha256=request_sha256,
            target_count=row_count,
            target_sha256=target_sha256,
            cell12_reason_codes=reason_codes,
            common_mask_created=True,
            common_mask_rows=common_mask_rows,
            folds=folds,
            minimum_fold_support_observed=minimum_support,
        )

    selected_coordinates = [fixture.session_coordinates[index] for index in common_mask_rows]
    origin = min(selected_coordinates)
    period = max(selected_coordinates) - origin + 1
    harmonic_rows = [
        {
            "row_index": index,
            "sin": math.sin(2.0 * math.pi * (coordinate - origin) / period),
            "cos": math.cos(2.0 * math.pi * (coordinate - origin) / period),
        }
        for index, coordinate in zip(common_mask_rows, selected_coordinates, strict=True)
    ]
    harmonic_sha256 = canonical_sha256(harmonic_rows)
    design_rows = [
        (
            1.0,
            float(fixture.predictors[index]),
            float(harmonic["sin"]),
            float(harmonic["cos"]),
        )
        for index, harmonic in zip(common_mask_rows, harmonic_rows, strict=True)
    ]
    design_rank = _matrix_rank(design_rows)
    if design_rank < fixture.minimum_design_rank:
        return _stop(
            fixture,
            stage="TARGET_PREFIT",
            reason_code="DESIGN_RANK_DEFICIENT",
            predictor_count=row_count,
            predictor_sha256=predictor_sha256,
            request_count=row_count,
            request_sha256=request_sha256,
            target_count=row_count,
            target_sha256=target_sha256,
            cell12_reason_codes=reason_codes,
            common_mask_created=True,
            common_mask_rows=common_mask_rows,
            folds=folds,
            harmonic_basis_sha256=harmonic_sha256,
            design_rank=design_rank,
            minimum_fold_support_observed=minimum_support,
        )

    counters = ProtectedCounters()
    counters.assert_zero()
    return Tier1Outcome(
        fixture_identity=fixture.fixture_identity,
        status="PASS",
        stage="TARGET_PREFIT",
        reason_code=TIER1_PASS,
        protected_counters=counters,
        predictor_ledger_count=row_count,
        predictor_ledger_sha256=predictor_sha256,
        request_count=row_count,
        request_sha256=request_sha256,
        target_ledger_count=row_count,
        target_ledger_sha256=target_sha256,
        cell12_reason_codes=reason_codes,
        common_mask_created=True,
        common_mask_rows=common_mask_rows,
        folds=folds,
        harmonic_basis_sha256=harmonic_sha256,
        design_rank=design_rank,
        minimum_fold_support_observed=minimum_support,
    )


def phase_a_runtime_rehearsal_stop() -> Tier1Outcome:
    """Return the mandatory Phase-A stop without executing any fixture or runner."""

    fixture = default_tier1_fixture()
    return _stop(fixture, stage="CONTRACT", reason_code=TIER2_NOT_AUTHORIZED)

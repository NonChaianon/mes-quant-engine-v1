"""Test 3 G3-F one-shot fit orchestration for the single new TRAIN lineage.

Classification
--------------
``PRE_ACTIVATION_NOT_AUTHORIZED``.  Implementation and tests only.

This module holds the fixed model/fold order, the four unreplenished fit permits, the
consume-before-callback rule, the poison-on-failure rule and the refusal of any fifth request
before a fifth callback can start.  It stops before every real surface: it opens no data file,
reaches no provider, reads or constructs no target, makes no reservation and performs no real
fit until a separate exact Owner activation supplies its own material.

The G3-P to G3-F row handoff is strictly in-memory inside one process.  The canonical handoff
type, its object-identity registry and its mint/consume functions exist only as cells of one
module closure: no handoff object, constructor, registry or raw row adapter is reachable from
the module surface or named in ``__all__``.  G3-P claims exactly one one-time delivery handle,
bound to this module instance by an opaque identity marker, and that handle mints and consumes
the canonical handoff internally so it never escapes.  No caller-supplied callback, wrapper,
metadata spoof, mapping, duck-typed stand-in, replay, second claim or replaced/reloaded module
instance can present rows to this stage, and no row is ever written, cached, logged,
serialized, spilled or sent between processes.

Real mode is gated by a closure-held verified activation capability.  The only route that can
ever issue one is the public local activation-file loader, which validates one closed UTF-8
JSON document, machine-computes the current bytes of the exact ordered six reviewed
implementation paths under a caller-supplied repository root, requires the fixed four-fit
budget, and carries the later-supplied runtime evidence names without this module ever holding
their values.  The loader is terminal and one-attempt per module instance: it arms and spends
at entry, so a failed validation stays refused and any second call is refused whatever it is
given.  After validation, and before it returns a capability, it atomically claims the
activation under the activation-bound runtime-evidence root/namespace/reservation_name using
``O_CREAT | O_EXCL`` with no overwrite, then fsyncs the claim file and its directory.  That
exclusive claim is an activation replay claim, not a target-space reservation; an existing
claim, a missing or symlinked claim directory, or any publication or durability ambiguity is a
terminal refusal.  Acceptance later requires the exact issued capability object, not its type
or serial, and the six-path recheck uses closure-captured values rather than any field reread
from the caller's object.

Those bounded reads and that single exclusive claim are the entire filesystem surface of this
module.  It opens no data artifact, reaches no provider, reads or constructs no target, makes
no target-space reservation and performs no fit.

Honest limits.  This is local capability discipline; it is neither cryptographic secrecy nor
Owner authentication, which remains with the separate exact Owner activation.  A Python closure
is not secret: arbitrary in-process code can still reach cell contents by reflection.  What
these controls do give is that no ordinary module-surface call, wrapper, copy, mapping, duck
type, serial reuse or replay can obtain rows or real-mode authority, and that persistent replay
protection depends on the exclusive activation claim being retained on disk.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from numbers import Real
from typing import Final, NoReturn

import numpy as np

from mes_quant.exploration.test3_contract import (
    FOLD_ORDER,
    MODEL_COLUMNS,
    MODEL_ORDER,
    REAL_FOLD_FIT_BUDGET,
    TARGET_HORIZON_MINUTES,
)
from mes_quant.exploration.test3_design import (
    Harmonic,
    Test3DesignContractError,
    common_eligibility,
    design_values,
)

ONE_SHOT_MODULE_ID: Final[str] = "MES_TEST3_G3F_ONE_SHOT_REAL_TRAIN_V1"

#: The only handoff identity this stage accepts, produced in-process by G3-P.
EXPECTED_HANDOFF_ID: Final[str] = "TEST3_G3P_TO_G3F_STRICT_IN_PROCESS_ROW_HANDOFF_V1"

#: Runtime evidence naming is deferred in full to the separate later Owner activation.
EVIDENCE_NAMING: Final[str] = "DEFERRED_TO_SEPARATE_OWNER_ACTIVATION"

#: Exact ordered model/fold pairs; two frozen models by two frozen folds.
EXPECTED_PAIR_ORDER: Final[tuple[tuple[str, str], ...]] = tuple(
    (model_id, fold_id) for fold_id in FOLD_ORDER for model_id in MODEL_ORDER
)

#: Lifetime allocation: exactly four unreplenished real fit permits.
FIT_PERMIT_BUDGET: Final[int] = REAL_FOLD_FIT_BUDGET

FOLD_ROLE_ATTRIBUTES: Final[Mapping[str, str]] = {
    "WF_2022": "role_wf_2022",
    "WF_2023": "role_wf_2023",
}
ROLE_TRAIN: Final[str] = "TRAIN"
ROLE_HOLDOUT: Final[str] = "VALIDATION"
ROLE_UNUSED: Final[str] = "UNUSED"
FOLD_ROLES: Final[frozenset[str]] = frozenset({ROLE_TRAIN, ROLE_HOLDOUT, ROLE_UNUSED})
MIN_BOUNDARY_GAP_MINUTES: Final[int] = 60

#: Import prefixes this stage must never reach, enforced statically by its tests.
FORBIDDEN_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "asyncio",
    "boto3",
    "botocore",
    "databento",
    "databento_dbn",
    "exchange_calendars",
    "ftplib",
    "glob",
    "http",
    "httpx",
    "logging",
    "pandas",
    "pandas_market_calendars",
    "pathlib",
    "pickle",
    "polars",
    "pyarrow",
    "requests",
    "scipy",
    "shutil",
    "sklearn",
    "smtplib",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "ssl",
    "statsmodels",
    "subprocess",
    "sys",
    "tempfile",
    "urllib",
    "mes_quant.cli",
    "mes_quant.data",
    "mes_quant.governance",
    "mes_quant.io",
    "mes_quant.exploration.test2_request_set",
    "mes_quant.exploration.test3_g3p_pre_fit",
)

#: The exact closed set of module roots this stage may import, enforced statically by its tests.
#: ``hashlib``, ``json``, ``os`` and ``stat`` exist only for the read-only local verification of
#: the activation file and of the reviewed six-path bytes; nothing here can write.
ALLOWED_IMPORT_ROOTS: Final[frozenset[str]] = frozenset(
    {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "enum",
        "hashlib",
        "json",
        "math",
        "mes_quant.exploration.test3_contract",
        "mes_quant.exploration.test3_design",
        "numbers",
        "numpy",
        "os",
        "stat",
        "typing",
    }
)

#: Counters that must remain exactly zero for every pre-activation inert run.
PROTECTED_COUNTER_FIELDS: Final[tuple[str, ...]] = (
    "real_fold_fit_calls",
    "real_models_fitted",
    "real_coefficients_computed",
    "real_target_or_path_rows_read",
    "real_targets_constructed",
    "real_forecasts_computed",
    "real_qlike_evaluations",
    "real_bootstrap_replicates",
    "validation_rows_read",
    "final_test_rows_read",
    "provider_calls",
    "target_space_reservations",
    "filesystem_reads",
    "filesystem_writes",
    "network_calls",
    "evidence_files_written",
    "scientific_claims_made",
)

#: The exact ordered six reviewed implementation paths, relative to a repository root.
#: These are implementation paths only; they are not, and must never become, evidence names.
REVIEWED_IMPLEMENTATION_PATHS: Final[tuple[str, ...]] = (
    "src/mes_quant/exploration/test3_g3p_pre_fit.py",
    "tests/test_test3_g3p_pre_fit.py",
    "src/mes_quant/exploration/test3_g3f_one_shot.py",
    "tests/test_test3_g3f_one_shot.py",
    "tools/run_test3_one_shot_scientific_recovery.py",
    "tests/test_run_test3_one_shot_scientific_recovery.py",
)

#: The closed top-level key set of a local activation file.
ACTIVATION_DOCUMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "activation_document_sha256",
        "fit_permit_budget",
        "implementation_paths",
        "owner_activation_id",
        "reviewed_path_sha256",
        "runtime_evidence",
    }
)

#: The closed key set of the later-supplied runtime evidence naming block.
RUNTIME_EVIDENCE_KEYS: Final[frozenset[str]] = frozenset(
    {"namespace", "permit_names", "reservation_name", "root", "terminal_name"}
)

#: Bounded read sizes; nothing larger is ever read into memory.
ACTIVATION_FILE_MAX_BYTES: Final[int] = 1 * 1024 * 1024
REVIEWED_FILE_MAX_BYTES: Final[int] = 16 * 1024 * 1024

_NAME_CHARACTERS: Final[frozenset[str]] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_."
)
_MAX_NAME_LENGTH: Final[int] = 128

#: Fixed, deterministic naming and content of the exclusive activation replay claim.  The claim
#: is an in-process replay control only; it is not a target-space reservation, carries no
#: scientific value, and is never read back as evidence.
_ACTIVATION_CLAIM_SUFFIX: Final[str] = ".activation-replay-claim"
_ACTIVATION_CLAIM_MARKER: Final[str] = "MES_TEST3_G3F_ACTIVATION_REPLAY_CLAIM_V1"
_ACTIVATION_CLAIM_SCOPE: Final[str] = (
    "NO_SCIENTIFIC_CONTENT_NO_TARGET_ACCESS_NO_RESERVATION_NO_FIT"
)


class Test3G3FOneShotError(RuntimeError):
    """Base fail-closed error for the one-shot G3-F stage."""


class Test3G3FPreActivationStop(Test3G3FOneShotError):
    """Raised when a real surface is requested before a separate exact Owner activation."""


class Test3G3FPermitError(Test3G3FOneShotError):
    """Raised when the unreplenished four-permit contract would be violated."""


def _error(message: str) -> Test3G3FOneShotError:
    return Test3G3FOneShotError(message)


def _stop(message: str) -> NoReturn:
    raise Test3G3FPreActivationStop(message)


class ExecutionMode(StrEnum):
    """The only two execution modes; the real mode requires a separate exact activation."""

    PRE_ACTIVATION_INERT = "PRE_ACTIVATION_INERT_REHEARSAL"
    OWNER_ACTIVATED_REAL = "OWNER_ACTIVATED_ONE_SHOT_REAL_TRAIN"


class RowOrigin(StrEnum):
    """Closed row provenance; real fits accept only the in-process G3-P handoff."""

    G3P_IN_PROCESS_HANDOFF = "G3P_IN_PROCESS_HANDOFF"
    SYNTHETIC_IN_MEMORY = "SYNTHETIC_IN_MEMORY"


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _error(f"{field} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _identity(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{field} must be a non-empty string")
    return value


def _positive_finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise _error(f"{field} must be a non-boolean real number")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise _error(f"{field} must be finite and strictly positive")
    return numeric


@dataclass(frozen=True, slots=True)
class OneShotEligibleRow:
    """One immutable in-memory eligible outer-TRAIN row; never persisted or serialized."""

    decision_identity: str
    decision_time_utc: datetime
    session_id: str
    role_wf_2022: str
    role_wf_2023: str
    harmonic: Harmonic
    rv_fwd_60: float
    realized_vol_60m: float
    realized_vol_120m: float
    realized_vol_240m: float
    origin: RowOrigin

    def __post_init__(self) -> None:
        _identity(self.decision_identity, field="decision_identity")
        _identity(self.session_id, field="session_id")
        _utc(self.decision_time_utc, field="decision_time_utc")
        if not isinstance(self.harmonic, Harmonic):
            raise _error("harmonic must be a frozen Harmonic")
        if not isinstance(self.origin, RowOrigin):
            raise _error("origin must be a RowOrigin")
        for attribute in FOLD_ROLE_ATTRIBUTES.values():
            role = getattr(self, attribute)
            if not isinstance(role, str) or role not in FOLD_ROLES:
                raise _error(f"{attribute} must be one of {sorted(FOLD_ROLES)}")
        _positive_finite(self.rv_fwd_60, field="rv_fwd_60")
        for horizon in (60, 120, 240):
            _positive_finite(
                getattr(self, f"realized_vol_{horizon}m"),
                field=f"realized_vol_{horizon}m",
            )

    @property
    def label_end_time_utc(self) -> datetime:
        return self.decision_time_utc + timedelta(minutes=TARGET_HORIZON_MINUTES)

    def fold_role(self, fold_id: str) -> str:
        if fold_id not in FOLD_ROLE_ATTRIBUTES:
            raise _error(f"fold_id must be one of {FOLD_ORDER}")
        return str(getattr(self, FOLD_ROLE_ATTRIBUTES[fold_id]))


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _serial_of(value: object) -> int | None:
    serial = getattr(value, "serial", None)
    if isinstance(serial, bool) or not isinstance(serial, int):
        return None
    return serial


@dataclass(frozen=True, slots=True)
class OneShotFitPermit:
    """Single-use witness for exactly one model/fold fit."""

    model_id: str
    fold_id: str
    ordinal: int
    budget_nonce: object


class OneShotFitPermitBudget:
    """Ordered, unreplenished, fail-closed budget of exactly four fit permits.

    A permit is consumed immediately before its callback runs, so an attempted fit always
    spends its permit.  Any failure poisons the budget permanently and no permit is ever
    replaced, refunded or reissued.  A fifth request is refused before a fifth callback can
    start, whatever else has happened to the budget.
    """

    __slots__ = (
        "_callback_starts",
        "_consumed",
        "_failure_reason",
        "_nonce",
        "_poisoned",
        "_refused_requests",
        "_sealed",
        "_started_ordinals",
        "_validated_ordinals",
    )

    def __init__(self) -> None:
        self._callback_starts = 0
        self._consumed: list[tuple[str, str]] = []
        self._failure_reason: str | None = None
        self._nonce = object()
        self._poisoned = False
        self._refused_requests = 0
        self._sealed = False
        self._started_ordinals: set[int] = set()
        self._validated_ordinals: set[int] = set()

    @property
    def consumed_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._consumed)

    @property
    def permits_consumed(self) -> int:
        return len(self._consumed)

    @property
    def permits_remaining(self) -> int:
        return FIT_PERMIT_BUDGET - len(self._consumed)

    @property
    def callback_starts(self) -> int:
        return self._callback_starts

    @property
    def validated_outputs(self) -> int:
        return len(self._validated_ordinals)

    @property
    def refused_requests(self) -> int:
        return self._refused_requests

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    @property
    def sealed(self) -> bool:
        return self._sealed

    @property
    def failure_reason(self) -> str | None:
        return self._failure_reason

    def _poison(self, message: str) -> NoReturn:
        self._poisoned = True
        self._failure_reason = message
        raise Test3G3FPermitError(message)

    def _own_permit(self, permit: object) -> OneShotFitPermit:
        if not isinstance(permit, OneShotFitPermit) or permit.budget_nonce is not self._nonce:
            self._poison("permit was not minted by this budget")
        return permit

    def consume(self, *, model_id: str, fold_id: str) -> OneShotFitPermit:
        """Consume the next exact ordered permit before its callback is invoked."""

        if len(self._consumed) >= FIT_PERMIT_BUDGET:
            self._refused_requests += 1
            raise Test3G3FPermitError(
                "the fifth fit request is refused before any fifth callback"
            )
        if self._sealed:
            raise Test3G3FPermitError("the fit permit budget is sealed")
        if self._poisoned:
            raise Test3G3FPermitError("the fit permit budget is poisoned")
        if len(self._validated_ordinals) != len(self._consumed):
            self._poison("the preceding permit has no validated output")
        expected = EXPECTED_PAIR_ORDER[len(self._consumed)]
        observed = (model_id, fold_id)
        if observed != expected:
            self._poison(f"unexpected pair order: expected={expected}, observed={observed}")
        self._consumed.append(expected)
        return OneShotFitPermit(
            model_id=model_id,
            fold_id=fold_id,
            ordinal=len(self._consumed),
            budget_nonce=self._nonce,
        )

    def start_callback(self, permit: OneShotFitPermit) -> None:
        """Record that the fit callback bound to ``permit`` is about to run."""

        if self._sealed or self._poisoned:
            raise Test3G3FPermitError("the fit permit budget is closed")
        owned = self._own_permit(permit)
        if owned.ordinal != len(self._consumed):
            self._poison("permit is stale or out of sequence")
        if owned.ordinal in self._started_ordinals:
            self._poison("permit callback is single-use")
        self._started_ordinals.add(owned.ordinal)
        self._callback_starts += 1

    def record_validated_output(self, permit: OneShotFitPermit) -> None:
        """Record that the output bound to ``permit`` passed every structural check."""

        if self._sealed or self._poisoned:
            raise Test3G3FPermitError("the fit permit budget is closed")
        owned = self._own_permit(permit)
        if owned.ordinal not in self._started_ordinals:
            self._poison("a validated output requires a started callback")
        if owned.ordinal in self._validated_ordinals:
            self._poison("permit output is single-use")
        self._validated_ordinals.add(owned.ordinal)

    def fail(self, permit: object, *, reason: str) -> None:
        """Poison the budget after a consumed permit failed; there is no replacement."""

        ordinal = permit.ordinal if isinstance(permit, OneShotFitPermit) else 0
        self._poisoned = True
        self._failure_reason = f"ordinal={ordinal}:{reason}"

    def seal(self) -> None:
        """Irreversibly close a complete budget; anything incomplete fails closed."""

        if self._sealed:
            raise Test3G3FPermitError("the fit permit budget is already sealed")
        if self._poisoned:
            raise Test3G3FPermitError("a poisoned fit permit budget cannot be sealed")
        ordinals = set(range(1, FIT_PERMIT_BUDGET + 1))
        complete = (
            tuple(self._consumed) == EXPECTED_PAIR_ORDER
            and self._callback_starts == FIT_PERMIT_BUDGET
            and self._started_ordinals == ordinals
            and self._validated_ordinals == ordinals
        )
        if not complete:
            self._poisoned = True
            self._failure_reason = "incomplete permit cross-product"
            raise Test3G3FPermitError("cannot seal an incomplete permit cross-product")
        self._sealed = True


@dataclass(frozen=True, slots=True)
class OneShotFoldPartition:
    fold_id: str
    train_indices: tuple[int, ...]
    holdout_indices: tuple[int, ...]
    holdout_sessions: tuple[str, ...]
    train_label_end_max_utc: datetime
    holdout_decision_min_utc: datetime
    boundary_gap_minutes: float


@dataclass(frozen=True, slots=True)
class OneShotFitResult:
    model_id: str
    fold_id: str
    ordinal: int
    column_names: tuple[str, ...]
    coefficient_dimension: int
    rank: int
    train_row_count: int
    holdout_row_count: int


@dataclass(frozen=True, slots=True)
class OneShotCounters:
    permits_consumed: int
    fit_callback_starts: int
    fit_outputs_validated: int
    refused_fit_requests: int
    real_fold_fit_calls: int = 0
    real_models_fitted: int = 0
    real_coefficients_computed: int = 0
    real_target_or_path_rows_read: int = 0
    real_targets_constructed: int = 0
    real_forecasts_computed: int = 0
    real_qlike_evaluations: int = 0
    real_bootstrap_replicates: int = 0
    validation_rows_read: int = 0
    final_test_rows_read: int = 0
    provider_calls: int = 0
    target_space_reservations: int = 0
    filesystem_reads: int = 0
    filesystem_writes: int = 0
    network_calls: int = 0
    evidence_files_written: int = 0
    scientific_claims_made: int = 0


def assert_zero_protected_counters(counters: OneShotCounters) -> None:
    """Fail closed unless every protected real/scientific counter is exactly zero."""

    if not isinstance(counters, OneShotCounters):
        raise _error("counters must be OneShotCounters")
    nonzero = sorted(name for name in PROTECTED_COUNTER_FIELDS if getattr(counters, name) != 0)
    if nonzero:
        raise _error(f"protected counters must all be zero: {nonzero}")


@dataclass(frozen=True, slots=True)
class OneShotFitReport:
    module_id: str
    mode: ExecutionMode
    activation_state: str
    evidence_naming: str
    pair_order: tuple[tuple[str, str], ...]
    fits: tuple[OneShotFitResult, ...]
    partitions: Mapping[str, OneShotFoldPartition]
    counters: OneShotCounters


def describe_pre_activation_stop() -> Mapping[str, object]:
    """Return the closed, data-free pre-activation stop facts for this stage."""

    return {
        "module_id": ONE_SHOT_MODULE_ID,
        "activation_state": ExecutionMode.PRE_ACTIVATION_INERT.value,
        "pair_order": EXPECTED_PAIR_ORDER,
        "fit_permit_budget": FIT_PERMIT_BUDGET,
        "permits_unreplenished": True,
        "handoff": "STRICTLY_IN_MEMORY_SAME_PROCESS_NO_PERSISTENCE",
        "evidence_naming": EVIDENCE_NAMING,
        "data_access": "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION",
        "provider_access": "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION",
        "target_access": "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION",
        "target_space_reservation": "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION",
        "real_fits": "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION",
        "validation": "UNOPENED",
        "final_test": "SEALED",
        "protected_counters": PROTECTED_COUNTER_FIELDS,
    }


def build_design_matrix(model_id: str, rows: Iterable[OneShotEligibleRow]) -> np.ndarray:
    """Build the frozen ordered design matrix through the existing design definition."""

    if model_id not in MODEL_ORDER:
        raise _error(f"model_id must be one of {MODEL_ORDER}")
    materialized = tuple(rows)
    if not materialized:
        raise _error("design construction requires at least one row")
    values: list[tuple[float, ...]] = []
    for row in materialized:
        if not isinstance(row, OneShotEligibleRow):
            raise _error("rows must contain only OneShotEligibleRow")
        try:
            values.append(
                design_values(
                    model_id,
                    realized_vol_60m=row.realized_vol_60m,
                    realized_vol_120m=row.realized_vol_120m,
                    realized_vol_240m=row.realized_vol_240m,
                    harmonic=row.harmonic,
                )
            )
        except Test3DesignContractError as exc:
            raise _error(f"invalid design row {row.decision_identity}: {exc}") from exc
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.shape != (len(materialized), len(MODEL_COLUMNS[model_id])):
        raise _error("design matrix shape does not match the frozen model definition")
    if not np.all(np.isfinite(matrix)):
        raise _error("design matrix must be finite")
    return matrix


def build_response_vector(rows: Iterable[OneShotEligibleRow]) -> np.ndarray:
    """Derive the frozen response ``Y = ln(rv_fwd_60)``; no precomputed response is accepted."""

    materialized = tuple(rows)
    if not materialized:
        raise _error("response construction requires at least one row")
    response = np.asarray(
        [math.log(_positive_finite(row.rv_fwd_60, field="rv_fwd_60")) for row in materialized],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(response)):
        raise _error("response vector must be finite")
    return response


def _fold_partition(
    fold_id: str,
    rows: tuple[OneShotEligibleRow, ...],
) -> OneShotFoldPartition:
    train_indices: list[int] = []
    holdout_indices: list[int] = []
    holdout_sessions: list[str] = []
    for index, row in enumerate(rows):
        role = row.fold_role(fold_id)
        if role == ROLE_TRAIN:
            train_indices.append(index)
        elif role == ROLE_HOLDOUT:
            holdout_indices.append(index)
            if not holdout_sessions or holdout_sessions[-1] != row.session_id:
                holdout_sessions.append(row.session_id)
    if not train_indices or not holdout_indices:
        raise _error(f"{fold_id} requires non-empty train and holdout partitions")
    train_label_end_max = max(rows[index].label_end_time_utc for index in train_indices)
    train_decision_max = max(rows[index].decision_time_utc for index in train_indices)
    holdout_decision_min = min(rows[index].decision_time_utc for index in holdout_indices)
    if train_label_end_max >= holdout_decision_min:
        raise _error(f"{fold_id} purge failed before the first holdout decision time")
    gap_minutes = (holdout_decision_min - train_decision_max).total_seconds() / 60.0
    if gap_minutes < MIN_BOUNDARY_GAP_MINUTES:
        raise _error(
            f"{fold_id} boundary gap must be at least {MIN_BOUNDARY_GAP_MINUTES} minutes"
        )
    return OneShotFoldPartition(
        fold_id=fold_id,
        train_indices=tuple(train_indices),
        holdout_indices=tuple(holdout_indices),
        holdout_sessions=tuple(holdout_sessions),
        train_label_end_max_utc=train_label_end_max,
        holdout_decision_min_utc=holdout_decision_min,
        boundary_gap_minutes=gap_minutes,
    )


def _validate_rows(
    rows: Iterable[OneShotEligibleRow],
    *,
    mode: ExecutionMode,
) -> tuple[OneShotEligibleRow, ...]:
    materialized = tuple(rows)
    if not materialized:
        raise _error("at least one eligible row is required")
    required_origin = (
        RowOrigin.G3P_IN_PROCESS_HANDOFF
        if mode is ExecutionMode.OWNER_ACTIVATED_REAL
        else RowOrigin.SYNTHETIC_IN_MEMORY
    )
    seen: set[str] = set()
    previous: datetime | None = None
    for row in materialized:
        if not isinstance(row, OneShotEligibleRow):
            raise _error("rows must contain only OneShotEligibleRow")
        if row.origin is not required_origin:
            raise _error(f"{mode.value} accepts only {required_origin.value} rows")
        if row.decision_identity in seen:
            raise _error(f"decision_identity must be unique: {row.decision_identity}")
        seen.add(row.decision_identity)
        if previous is not None and row.decision_time_utc <= previous:
            raise _error("rows must be in strict chronological order with unique times")
        previous = row.decision_time_utc
    return materialized


def _validated_fit_output(output: object, *, model_id: str, fold_id: str) -> tuple[int, int]:
    expected = len(MODEL_COLUMNS[model_id])
    if not isinstance(output, tuple) or len(output) != 4:
        raise _error(f"{model_id}/{fold_id} fit callback must return the lstsq 4-tuple")
    beta = np.asarray(output[0], dtype=np.float64)
    if beta.ndim != 1 or beta.size != expected or not np.all(np.isfinite(beta)):
        raise _error(f"{model_id}/{fold_id} coefficients must be {expected} finite values")
    rank_value = output[2]
    if isinstance(rank_value, bool) or not isinstance(rank_value, (int, np.integer)):
        raise _error(f"{model_id}/{fold_id} reported rank must be an integer")
    rank = int(rank_value)
    if rank != expected:
        raise _error(f"{model_id}/{fold_id} fitted design must be full rank")
    singular = np.asarray(output[3], dtype=np.float64)
    if singular.ndim != 1 or singular.size != expected:
        raise _error(f"{model_id}/{fold_id} must report {expected} singular values")
    if not np.all(np.isfinite(singular)) or np.any(singular <= 0.0):
        raise _error(f"{model_id}/{fold_id} singular values must be finite and positive")
    return int(beta.size), rank


def _read_regular_file_bytes(path: str, *, limit: int, label: str) -> bytes:
    """Read one existing, non-symlinked, bounded regular file; nothing else is opened."""

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise _error(f"{label} is missing, symlinked or unreadable") from exc
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode):
            raise _error(f"{label} is not a regular file")
        if status.st_size > limit:
            raise _error(f"{label} exceeds the bounded read size")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def _absolute_directory(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or not os.path.isabs(value):
        raise _error(f"{label} must be an absolute path string")
    normalized = os.path.normpath(value)
    try:
        status = os.lstat(normalized)
    except OSError as exc:
        raise _error(f"{label} is missing or unreadable") from exc
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise _error(f"{label} must be an existing non-symlinked directory")
    return normalized


def _absolute_file(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or not os.path.isabs(value):
        raise _error(f"{label} must be an absolute path string")
    normalized = os.path.normpath(value)
    try:
        status = os.lstat(normalized)
    except OSError as exc:
        raise _error(f"{label} is missing or unreadable") from exc
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise _error(f"{label} must be an existing non-symlinked regular file")
    return normalized


def _repository_file(root: str, relative: object) -> str:
    """Resolve one plain relative implementation path under ``root``; no alias may escape."""

    if not isinstance(relative, str) or not relative or relative.strip() != relative:
        raise _error("each reviewed implementation path must be a clean relative string")
    if "\\" in relative or relative.startswith("/") or os.path.isabs(relative):
        raise _error(f"reviewed implementation path must be relative: {relative}")
    segments = relative.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        raise _error(f"reviewed implementation path has an empty or dotted segment: {relative}")
    current = root
    last = len(segments) - 1
    for index, segment in enumerate(segments):
        current = os.path.join(current, segment)
        try:
            status = os.lstat(current)
        except OSError as exc:
            raise _error(f"reviewed implementation path is missing: {relative}") from exc
        if stat.S_ISLNK(status.st_mode):
            raise _error(f"symlinked reviewed implementation path is forbidden: {relative}")
        if index == last:
            if not stat.S_ISREG(status.st_mode):
                raise _error(f"reviewed implementation path is not a regular file: {relative}")
        elif not stat.S_ISDIR(status.st_mode):
            raise _error(f"reviewed implementation path has a non-directory ancestor: {relative}")
    return current


def _observed_reviewed_digests(root: str) -> tuple[str, ...]:
    """Machine-compute the current bytes of the exact ordered six reviewed paths."""

    return tuple(
        hashlib.sha256(
            _read_regular_file_bytes(
                _repository_file(root, relative),
                limit=REVIEWED_FILE_MAX_BYTES,
                label=f"reviewed implementation file {relative}",
            )
        ).hexdigest()
        for relative in REVIEWED_IMPLEMENTATION_PATHS
    )


def _activation_claim_bytes(activation_file_sha256: str) -> bytes:
    """Build the deterministic, non-scientific activation replay marker.

    The marker is fully determined by the activation file bytes.  It carries no row, target,
    path, coefficient, timestamp or other scientific value, and it is never read back as
    evidence by this module.
    """

    return (
        f"{_ACTIVATION_CLAIM_MARKER}\n{activation_file_sha256}\n{_ACTIVATION_CLAIM_SCOPE}\n"
    ).encode()


def _claim_activation_once(
    root: str,
    *,
    evidence_root: str,
    namespace: str,
    reservation_name: str,
    payload: bytes,
) -> str:
    """Atomically claim one activation inside an existing, non-symlinked directory.

    This is an activation replay claim, not a target-space reservation.  Every path component
    below ``root`` must already exist and must not be a symlink: nothing here creates, renames
    or removes a directory, and the traversal uses directory descriptors with ``O_NOFOLLOW`` so
    a symlinked component cannot redirect it.  The claim itself is created with
    ``O_CREAT | O_EXCL`` and is never overwritten, and the claim file and its directory are both
    fsynced before the caller may receive a capability.  An existing claim, an unusable claim
    directory, or any publication or durability ambiguity is a terminal refusal.
    """

    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in os.supports_dir_fd
    ):
        raise _error("the activation claim requires secure directory-descriptor traversal")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        try:
            descriptors.append(os.open(root, directory_flags))
        except OSError as exc:
            raise _error("the activation claim root directory is unusable") from exc
        for segment in (*evidence_root.split("/"), namespace):
            try:
                descriptors.append(
                    os.open(segment, directory_flags, dir_fd=descriptors[-1])
                )
            except OSError as exc:
                raise _error(
                    "the activation claim directory is missing, symlinked or not a directory"
                ) from exc
        parent = descriptors[-1]
        if not stat.S_ISDIR(os.fstat(parent).st_mode):
            raise _error(
                "the activation claim directory is missing, symlinked or not a directory"
            )
        name = reservation_name + _ACTIVATION_CLAIM_SUFFIX
        try:
            claim = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
                dir_fd=parent,
            )
        except FileExistsError as exc:
            raise _error("this activation is already claimed; replay is refused") from exc
        except OSError as exc:
            raise _error("the activation claim could not be created exclusively") from exc
        try:
            view = memoryview(payload)
            while view:
                progress = os.write(claim, view)
                if progress <= 0:
                    raise _error("the activation claim made no write progress")
                view = view[progress:]
            os.fsync(claim)
        except OSError as exc:
            raise _error("the activation claim could not be published durably") from exc
        finally:
            os.close(claim)
        try:
            os.fsync(parent)
        except OSError as exc:
            raise _error(
                "the activation claim directory could not be published durably"
            ) from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return name


def _reject_json_constant(name: str) -> NoReturn:
    raise _error(f"the activation file must not contain the nonfinite constant {name}")


def _reject_duplicate_keys(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _error(f"the activation file contains a duplicate key: {key}")
        result[key] = value
    return result


def _assert_finite(value: object, *, field: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _assert_finite(child, field=f"{field}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, field=f"{field}[{index}]")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise _error(f"the activation file contains a nonfinite number at {field}")


def _evidence_name(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > _MAX_NAME_LENGTH:
        raise _error(f"runtime evidence {field} must be a bounded non-empty string")
    if value in {".", ".."} or not set(value).issubset(_NAME_CHARACTERS):
        raise _error(f"runtime evidence {field} contains a forbidden character")
    return value


def _evidence_root(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > _MAX_NAME_LENGTH:
        raise _error("runtime evidence root must be a bounded non-empty string")
    if "\\" in value or value.startswith("/") or os.path.isabs(value):
        raise _error("runtime evidence root must be a relative path")
    segments = value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise _error("runtime evidence root has an empty or dotted segment")
    if any(not set(segment).issubset(_NAME_CHARACTERS) for segment in segments):
        raise _error("runtime evidence root contains a forbidden character")
    return value


def _validated_runtime_evidence(value: object) -> tuple[tuple[str, object], ...]:
    """Validate the later-supplied evidence naming without holding any expected value."""

    if not isinstance(value, Mapping) or set(value) != set(RUNTIME_EVIDENCE_KEYS):
        raise _error("the activation must carry the exact closed runtime evidence key set")
    root = _evidence_root(value["root"])
    namespace = _evidence_name(value["namespace"], field="namespace")
    reservation = _evidence_name(value["reservation_name"], field="reservation_name")
    terminal = _evidence_name(value["terminal_name"], field="terminal_name")
    declared = value["permit_names"]
    if not isinstance(declared, list) or len(declared) != FIT_PERMIT_BUDGET:
        raise _error(f"the activation must name exactly {FIT_PERMIT_BUDGET} fit permits")
    permits = tuple(
        _evidence_name(item, field=f"permit_names[{index}]")
        for index, item in enumerate(declared)
    )
    names = (root, namespace, reservation, terminal, *permits)
    if len(set(names)) != len(names):
        raise _error("runtime evidence names must not collide")
    return (
        ("namespace", namespace),
        ("permit_names", permits),
        ("reservation_name", reservation),
        ("root", root),
        ("terminal_name", terminal),
    )


def _build_closed_activation_and_handoff_state_machine() -> tuple[object, ...]:
    """Create the whole activation and handoff state machine inside one closure.

    The canonical handoff type, the verified activation capability type, both object-identity
    registries, the serial counter, the closure key and the verified repository root/digests are
    cells of this closure only.  The values returned are an opaque module-instance identity
    marker, the public activation loader, the private activation acceptor used by
    :func:`run_one_shot_fits`, the private one-time G3-P delivery claim and a read-only
    non-authoritative state reporter.  The factory itself is deleted from the module namespace
    immediately after it runs, so no module-level mint or open route survives import.

    This is local capability discipline, not secrecy: a Python closure is not immune to
    arbitrary in-process reflection.  What it does give is that no ordinary module-surface call,
    wrapper, copy, mapping, duck type, serial reuse or replay can obtain rows or real-mode
    authority.
    """

    closure_key = object()
    module_marker = object()
    serial_counter = [0]
    handoff_registry: dict[int, str] = {}
    activation_registry: dict[int, str] = {}
    verified_root: list[str] = []
    verified_digests: list[tuple[str, ...]] = []
    loader_state: dict[str, object] = {"armed": True, "issued": None}
    delivery_state: dict[str, bool] = {"claimed": False, "armed": True}
    issued_state = "ISSUED"
    spent_state = "SPENT"

    def next_serial() -> int:
        serial_counter[0] += 1
        return serial_counter[0]

    class _ClosureBound:
        """Immutable, unserializable, redacted base for every closure-bound object."""

        __slots__ = ()

        def __setattr__(self, name: str, value: object) -> NoReturn:
            raise _error(f"{type(self).__name__} is immutable")

        def __delattr__(self, name: str) -> NoReturn:
            raise _error(f"{type(self).__name__} is immutable")

        def __reduce__(self) -> NoReturn:
            raise _error(f"{type(self).__name__} must never be serialized")

        def __getstate__(self) -> NoReturn:
            raise _error(f"{type(self).__name__} must never be serialized")

        def __repr__(self) -> str:
            return f"<{type(self).__name__} REDACTED_IN_MEMORY_ONLY>"

        __str__ = __repr__

    class _G3PRowHandoff(_ClosureBound):
        """The one canonical strictly in-process G3-P to G3-F row handoff."""

        __slots__ = (
            "controls",
            "handoff_id",
            "harmonic_by_identity",
            "predictor_status_rows",
            "predictor_values",
            "serial",
            "target_status_rows",
            "target_variance_by_identity",
        )

        def __init__(self, key: object, /, **fields: object) -> None:
            if key is not closure_key:
                raise _error("direct construction of the canonical G3-P handoff is forbidden")
            if set(fields) != set(type(self).__slots__):
                raise _error("the canonical G3-P handoff requires its exact closed field set")
            for name in type(self).__slots__:
                object.__setattr__(self, name, fields[name])

    class _VerifiedOwnerActivationCapability(_ClosureBound):
        """Single-use capability proving one locally verified and claimed activation file."""

        __slots__ = (
            "activation_document_sha256",
            "activation_file_sha256",
            "fit_permit_budget",
            "owner_activation_id",
            "repository_root",
            "reviewed_digests",
            "runtime_evidence",
            "serial",
        )

        def __init__(self, key: object, /, **fields: object) -> None:
            if key is not closure_key:
                raise _error(
                    "direct construction of the Owner activation capability is forbidden"
                )
            if set(fields) != set(type(self).__slots__):
                raise _error("the Owner activation capability requires its exact field set")
            for name in type(self).__slots__:
                object.__setattr__(self, name, fields[name])

    def rows_from_handoff(handoff: object) -> tuple[OneShotEligibleRow, ...]:
        """Adapt the one canonical handoff into ordered eligible rows.

        This adapter is reachable only from the delivery handle below.  The exact canonical type
        and its object-identity state are checked before any field is read, so a duck-typed,
        mapping, wrapper, exact-type-but-unminted or replayed stand-in is refused before any row
        or field access and before any eligibility or design work.  Nothing is read from or
        written to any file, cache, log or channel.
        """

        if type(handoff) is not _G3PRowHandoff:
            _stop("only the exact canonical in-process G3-P handoff type is accepted")
        serial = _serial_of(handoff)
        if serial is None or handoff_registry.get(serial) != issued_state:
            _stop("the canonical G3-P handoff is absent, unissued or already consumed")
        handoff_registry[serial] = spent_state
        if getattr(handoff, "handoff_id", None) != EXPECTED_HANDOFF_ID:
            _stop("only the exact in-process G3-P handoff identity is accepted")

        eligibility = common_eligibility(
            handoff.target_status_rows,
            handoff.predictor_status_rows,
        )
        eligible = set(eligibility.eligible_identities)
        variance_by_identity = handoff.target_variance_by_identity
        harmonic_by_identity = handoff.harmonic_by_identity
        predictor_values = handoff.predictor_values

        rows: list[OneShotEligibleRow] = []
        for control in handoff.controls:
            identity = getattr(control, "identity", None)
            if identity not in eligible:
                continue
            values = predictor_values[identity]
            if any(value is None for value in values):
                raise _error("an eligible row has a missing predictor value")
            rows.append(
                OneShotEligibleRow(
                    decision_identity=identity,
                    decision_time_utc=_utc(control.timestamp, field="decision_time_utc"),
                    session_id=str(control.session_id),
                    role_wf_2022=str(control.role_2022),
                    role_wf_2023=str(control.role_2023),
                    harmonic=harmonic_by_identity[identity],
                    rv_fwd_60=float(variance_by_identity[identity]),
                    realized_vol_60m=float(values[0]),
                    realized_vol_120m=float(values[1]),
                    realized_vol_240m=float(values[2]),
                    origin=RowOrigin.G3P_IN_PROCESS_HANDOFF,
                )
            )
        if not rows:
            raise _error("the in-memory handoff produced no eligible row")
        return tuple(rows)

    def deliver_g3p_rows(
        marker: object,
        /,
        *,
        handoff_id: str,
    ) -> Callable[..., tuple[OneShotEligibleRow, ...]]:
        """The first stage of the one reviewed, one-time G3-P delivery handle.

        This stage carries no row field at all: it accepts only this exact module instance's
        identity marker, which is an identity check and not a credential, and the exact handoff
        identity.  It verifies the marker, then checks and spends the one-time delivery state
        before it returns, so a wrong marker, a second first-stage call or an abandoned
        first-stage closure all stay fail-closed and nothing can be retried behind them.  A
        wrong handoff identity is refused only after the delivery state is already spent.

        Only after this stage returns does the caller hold the private second-stage closure that
        alone accepts row fields, so no predictor, target or harmonic field expression has to be
        evaluated before this refusal can happen.
        """

        if marker is not module_marker:
            _stop("the G3-P delivery handle requires this exact G3-F module instance")
        if not delivery_state["armed"]:
            _stop("the one-time G3-P delivery handle is already spent")
        delivery_state["armed"] = False
        if handoff_id != EXPECTED_HANDOFF_ID:
            _stop("only the exact in-process G3-P handoff identity is accepted")
        supply_state: dict[str, bool] = {"armed": True}

        def supply_g3p_rows(
            *,
            controls: tuple[object, ...],
            predictor_status_rows: tuple[object, ...],
            predictor_values: Mapping[str, object],
            target_status_rows: tuple[object, ...],
            target_variance_by_identity: Mapping[str, float],
            harmonic_by_identity: Mapping[str, Harmonic],
        ) -> tuple[OneShotEligibleRow, ...]:
            """The private second stage; it alone accepts the row fields, exactly once.

            It is one-use and fail-closed: it spends itself before any payload field is
            validated or read, so a second invocation is refused before any row, mapping or
            field is touched.  The canonical handoff is then minted and consumed here through
            the internal adapter, so it never escapes and cannot be held, wrapped, copied or
            replayed.  A non-tuple/non-mapping payload is refused before any row or field is
            read.  No caller-supplied supplier or callback exists on this path.
            """

            if not supply_state["armed"]:
                _stop("the one-time G3-P row supply is already spent")
            supply_state["armed"] = False
            for name, sequence in (
                ("controls", controls),
                ("predictor_status_rows", predictor_status_rows),
                ("target_status_rows", target_status_rows),
            ):
                if not isinstance(sequence, tuple):
                    raise _error(f"{name} must be an in-memory tuple")
            for name, mapping in (
                ("predictor_values", predictor_values),
                ("target_variance_by_identity", target_variance_by_identity),
                ("harmonic_by_identity", harmonic_by_identity),
            ):
                if not isinstance(mapping, Mapping):
                    raise _error(f"{name} must be an in-memory mapping")
            serial = next_serial()
            handoff = _G3PRowHandoff(
                closure_key,
                serial=serial,
                handoff_id=handoff_id,
                controls=controls,
                predictor_status_rows=predictor_status_rows,
                predictor_values=predictor_values,
                target_status_rows=target_status_rows,
                target_variance_by_identity=target_variance_by_identity,
                harmonic_by_identity=harmonic_by_identity,
            )
            handoff_registry[serial] = issued_state
            return rows_from_handoff(handoff)

        return supply_g3p_rows

    def claim_g3p_delivery_handle() -> tuple[object, object]:
        """Hand the single reviewed G3-P delivery handle and marker over exactly once."""

        if delivery_state["claimed"]:
            raise _error("the one-time G3-P delivery handle is already claimed")
        delivery_state["claimed"] = True
        return deliver_g3p_rows, module_marker

    def load_owner_activation_capability(
        activation_path: object,
        *,
        repository_root: object,
    ) -> object:
        """Verify, exclusively claim, and issue one single-use activation capability.

        This is the only route in this module that can ever issue a capability, and it is
        terminal and one-attempt per module instance: it arms and spends at entry, so a failed
        validation remains refused and any second call is refused whether the input is identical
        or different.

        The file must be a bounded, non-symlinked, regular, closed UTF-8 JSON object with no
        duplicate key and no nonfinite number.  It must declare the exact ordered six reviewed
        implementation paths, whose current bytes are machine-computed under ``repository_root``
        and compared here, the fixed four-fit budget, and the later-supplied runtime evidence
        names, whose values this module never holds in advance.  After validation, and before a
        capability exists, the activation is atomically claimed under its own runtime evidence
        root/namespace/reservation_name; an existing claim or any publication or durability
        ambiguity refuses terminally.

        No data, provider, target or target-space surface is touched and no fit is performed or
        authorized here.  The loader binds bytes, structure, single use and replay; it does not
        and cannot establish Owner identity.
        """

        if not loader_state["armed"]:
            raise _error(
                "the local activation loader is one-attempt per module instance and is spent"
            )
        loader_state["armed"] = False
        root = _absolute_directory(repository_root, label="repository root")
        path = _absolute_file(activation_path, label="the activation file")
        raw = _read_regular_file_bytes(
            path,
            limit=ACTIVATION_FILE_MAX_BYTES,
            label="the activation file",
        )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise _error("the activation file must be closed UTF-8 text") from exc
        try:
            document = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_json_constant,
            )
        except ValueError as exc:
            raise _error("the activation file must be one closed JSON object") from exc
        if not isinstance(document, dict) or set(document) != set(ACTIVATION_DOCUMENT_KEYS):
            raise _error("the activation file must carry the exact closed top-level key set")
        _assert_finite(document, field="activation")
        _identity(document["owner_activation_id"], field="owner_activation_id")
        if not _is_sha256(document["activation_document_sha256"]):
            raise _error("activation_document_sha256 must be a lowercase 64-hex digest")
        budget = document["fit_permit_budget"]
        if (
            isinstance(budget, bool)
            or not isinstance(budget, int)
            or budget != FIT_PERMIT_BUDGET
        ):
            raise _error(f"the lifetime fit budget is exactly {FIT_PERMIT_BUDGET}")
        declared_paths = document["implementation_paths"]
        if (
            not isinstance(declared_paths, list)
            or tuple(declared_paths) != REVIEWED_IMPLEMENTATION_PATHS
        ):
            raise _error("the activation must bind the exact ordered six implementation paths")
        declared_digests = document["reviewed_path_sha256"]
        if (
            not isinstance(declared_digests, list)
            or len(declared_digests) != len(REVIEWED_IMPLEMENTATION_PATHS)
            or not all(_is_sha256(item) for item in declared_digests)
        ):
            raise _error("the activation must bind the reviewed bytes of all six paths")
        observed = _observed_reviewed_digests(root)
        if observed != tuple(declared_digests):
            raise _error("the current six-path bytes do not match the activation")
        evidence = _validated_runtime_evidence(document["runtime_evidence"])
        names = dict(evidence)
        activation_file_sha256 = hashlib.sha256(raw).hexdigest()
        _claim_activation_once(
            root,
            evidence_root=str(names["root"]),
            namespace=str(names["namespace"]),
            reservation_name=str(names["reservation_name"]),
            payload=_activation_claim_bytes(activation_file_sha256),
        )
        serial = next_serial()
        capability = _VerifiedOwnerActivationCapability(
            closure_key,
            activation_document_sha256=document["activation_document_sha256"],
            activation_file_sha256=activation_file_sha256,
            fit_permit_budget=budget,
            owner_activation_id=document["owner_activation_id"],
            repository_root=root,
            reviewed_digests=observed,
            runtime_evidence=evidence,
            serial=serial,
        )
        activation_registry[serial] = issued_state
        verified_root.append(root)
        verified_digests.append(observed)
        loader_state["issued"] = capability
        return capability

    def accept_and_consume_activation(activation: object) -> None:
        """Accept only the exact issued capability object, spend it, and recheck the bytes.

        Acceptance is by object identity, not by type or serial, so a copy, a directly built
        object, a duck type, a mapping, a dataclass with the same fields or a reused serial is
        refused.  The six-path recheck uses the closure-captured repository root and digests, so
        ``object.__setattr__`` on the capability cannot redirect it.  Everything here happens
        before row validation, before any design or response math, before any permit is consumed
        and before any callback.
        """

        if activation is None:
            _stop(
                "a real one-shot TRAIN fit requires a separate exact Owner activation bound to "
                "the reviewed bytes of all six paths"
            )
        issued = loader_state["issued"]
        if issued is None or activation is not issued:
            _stop(
                "activation material must be the exact capability object issued by the local "
                "activation-file loader"
            )
        if type(activation) is not _VerifiedOwnerActivationCapability:
            _stop("activation material must be a verified Owner activation capability")
        serial = _serial_of(activation)
        if serial is None or activation_registry.get(serial) != issued_state:
            _stop("the Owner activation capability is absent, unissued or already consumed")
        activation_registry[serial] = spent_state
        if not verified_root or not verified_digests:
            _stop("the Owner activation capability carries no verified six-path binding")
        if _observed_reviewed_digests(verified_root[0]) != verified_digests[0]:
            _stop("the reviewed six-path bytes drifted after the activation was verified")

    def local_state_report() -> Mapping[str, object]:
        """Return a read-only, explicitly non-authoritative view of local lifecycle state.

        This reporter exists for adversarial tests and local diagnosis only.  It carries no
        authority, proves nothing about Owner intent, and exposes no row, field, name, digest or
        capability object.
        """

        return {
            "authority": "NON_AUTHORITATIVE_LOCAL_IN_PROCESS_OBSERVATION_ONLY",
            "activation_loader_armed": bool(loader_state["armed"]),
            "activation_capability_issued": loader_state["issued"] is not None,
            "activation_capability_spent": spent_state in activation_registry.values(),
            "delivery_handle_claimed": bool(delivery_state["claimed"]),
            "delivery_handle_armed": bool(delivery_state["armed"]),
            "handoffs_created": len(handoff_registry),
            "handoffs_spent": sum(
                1 for value in handoff_registry.values() if value == spent_state
            ),
        }

    return (
        module_marker,
        load_owner_activation_capability,
        accept_and_consume_activation,
        claim_g3p_delivery_handle,
        local_state_report,
    )


#: Opaque per-import identity marker.  It is an identity check for the G3-P delivery binding,
#: never a credential, and it proves nothing about Owner intent.
(
    _MODULE_INSTANCE_MARKER,
    load_owner_activation_capability,
    _accept_and_consume_activation,
    _claim_g3p_delivery_handle,
    _local_state_report,
) = _build_closed_activation_and_handoff_state_machine()

del _build_closed_activation_and_handoff_state_machine


FitCallback = Callable[[np.ndarray, np.ndarray], object]


def run_one_shot_fits(
    rows: Iterable[OneShotEligibleRow],
    *,
    mode: ExecutionMode,
    fit_callback: FitCallback,
    activation: object | None = None,
    budget: OneShotFitPermitBudget | None = None,
) -> OneShotFitReport:
    """Run the exact four ordered model/fold fits behind four unreplenished permits.

    Every permit is consumed immediately before its callback runs, so an attempted fit always
    spends it.  Any failure poisons the budget without replacement or retry, and a fifth request
    is refused before a fifth callback can start.  Real mode requires the exact capability
    object issued by the local activation loader: a missing, directly constructed, copied,
    mapping, dataclass, duck-typed, serial-reused or replayed capability, a capability whose
    fields were redirected with ``object.__setattr__``, and any drift in the reviewed six-path
    bytes all stop before row validation, before any design or response math, before any permit
    is consumed and before any callback.  This function itself reaches no provider, reads or
    constructs no target and makes no reservation.
    """

    if not isinstance(mode, ExecutionMode):
        raise _error("mode must be an ExecutionMode")
    if mode is ExecutionMode.OWNER_ACTIVATED_REAL:
        _accept_and_consume_activation(activation)
    elif activation is not None:
        _stop("activation material must not be supplied to a pre-activation inert run")
    if not callable(fit_callback):
        raise _error("fit_callback must be callable")

    materialized = _validate_rows(rows, mode=mode)
    partitions = {fold_id: _fold_partition(fold_id, materialized) for fold_id in FOLD_ORDER}
    first, second = (partitions[fold_id] for fold_id in FOLD_ORDER)
    if set(first.holdout_indices) & set(second.holdout_indices):
        raise _error("fold holdouts must be disjoint")

    response = build_response_vector(materialized)
    designs = {model_id: build_design_matrix(model_id, materialized) for model_id in MODEL_ORDER}
    active_budget = OneShotFitPermitBudget() if budget is None else budget
    if not isinstance(active_budget, OneShotFitPermitBudget):
        raise _error("budget must be a OneShotFitPermitBudget")

    fits: list[OneShotFitResult] = []
    for model_id, fold_id in EXPECTED_PAIR_ORDER:
        partition = partitions[fold_id]
        train_index = np.asarray(partition.train_indices, dtype=np.int64)
        train_design = designs[model_id][train_index]
        train_response = response[train_index]
        columns = len(MODEL_COLUMNS[model_id])
        if train_design.shape[0] <= columns:
            raise _error(f"{model_id}/{fold_id} training rows must exceed fitted columns")
        permit = active_budget.consume(model_id=model_id, fold_id=fold_id)
        active_budget.start_callback(permit)
        try:
            output = fit_callback(train_design, train_response)
        except Exception:
            active_budget.fail(permit, reason="fit_callback_raised")
            raise
        try:
            dimension, rank = _validated_fit_output(output, model_id=model_id, fold_id=fold_id)
        except Exception:
            active_budget.fail(permit, reason="fit_output_validation_failed")
            raise
        active_budget.record_validated_output(permit)
        fits.append(
            OneShotFitResult(
                model_id=model_id,
                fold_id=fold_id,
                ordinal=permit.ordinal,
                column_names=MODEL_COLUMNS[model_id],
                coefficient_dimension=dimension,
                rank=rank,
                train_row_count=int(train_design.shape[0]),
                holdout_row_count=len(partition.holdout_indices),
            )
        )
    active_budget.seal()

    real = mode is ExecutionMode.OWNER_ACTIVATED_REAL
    counters = OneShotCounters(
        permits_consumed=active_budget.permits_consumed,
        fit_callback_starts=active_budget.callback_starts,
        fit_outputs_validated=active_budget.validated_outputs,
        refused_fit_requests=active_budget.refused_requests,
        real_fold_fit_calls=len(fits) if real else 0,
        real_models_fitted=len(fits) if real else 0,
        real_coefficients_computed=len(fits) if real else 0,
    )
    if not real:
        assert_zero_protected_counters(counters)

    return OneShotFitReport(
        module_id=ONE_SHOT_MODULE_ID,
        mode=mode,
        activation_state=(
            "OWNER_ACTIVATED" if real else ExecutionMode.PRE_ACTIVATION_INERT.value
        ),
        evidence_naming=EVIDENCE_NAMING,
        pair_order=EXPECTED_PAIR_ORDER,
        fits=tuple(fits),
        partitions=partitions,
        counters=counters,
    )


__all__ = [
    "ACTIVATION_DOCUMENT_KEYS",
    "ACTIVATION_FILE_MAX_BYTES",
    "ALLOWED_IMPORT_ROOTS",
    "EVIDENCE_NAMING",
    "EXPECTED_HANDOFF_ID",
    "EXPECTED_PAIR_ORDER",
    "FIT_PERMIT_BUDGET",
    "FOLD_ROLES",
    "FOLD_ROLE_ATTRIBUTES",
    "FORBIDDEN_IMPORT_PREFIXES",
    "MIN_BOUNDARY_GAP_MINUTES",
    "ONE_SHOT_MODULE_ID",
    "PROTECTED_COUNTER_FIELDS",
    "REVIEWED_FILE_MAX_BYTES",
    "REVIEWED_IMPLEMENTATION_PATHS",
    "RUNTIME_EVIDENCE_KEYS",
    "ExecutionMode",
    "OneShotCounters",
    "OneShotEligibleRow",
    "OneShotFitPermit",
    "OneShotFitPermitBudget",
    "OneShotFitReport",
    "OneShotFitResult",
    "OneShotFoldPartition",
    "RowOrigin",
    "Test3G3FOneShotError",
    "Test3G3FPermitError",
    "Test3G3FPreActivationStop",
    "assert_zero_protected_counters",
    "build_design_matrix",
    "build_response_vector",
    "describe_pre_activation_stop",
    "load_owner_activation_capability",
    "run_one_shot_fits",
]

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

Real execution completion.  After the activation capability exists, one execution-authority
reservation is created atomically and durably under the activation-named runtime evidence, and
nothing scientific may happen before that reservation is published.  The reservation is the only
route to the four ordered durable fit permits and to the single terminal record.  Real fits are
performed by this module with internal ``numpy.linalg.lstsq(..., rcond=None)`` on float64
matrices: real mode accepts no fit callback at all, and the legacy injectable callback survives
only in the explicitly inert synthetic rehearsal.  Coefficients, fold/model-local Duan smearing,
positive unclipped out-of-sample forecasts, QLIKE, the three frozen paired session-block
bootstraps and the frozen continuation gate all run in this process, and only closed, row-free
summaries ever leave it.  The semantic elementwise regions -- Duan smearing, the back-transform,
QLIKE, the relative reduction and the bootstrap arithmetic -- run with NumPy overflow, divide and
invalid errors raised rather than warned about, so no ``RuntimeWarning`` escapes them.  The
BLAS/LAPACK-backed least-squares call deliberately carries no such error policy, because a
floating-point status flag set by a blocked and vectorized backend kernel describes that kernel
rather than the correctness of the returned coefficients; its result is instead validated
immediately for exact expected shape, float64 conversion and finiteness.  The two prediction
products are not BLAS-backed at all: they are computed by one explicit checked float64
matrix-vector kernel that validates operand compatibility first, evaluates a deterministic
``numpy.einsum`` contraction with overflow and invalid operations raised, and then proves the
exact dimension, shape and finiteness of the product.  Both routes fail identically: the raised
error follows the ordinary failure route
into the single ``INVALID_EVIDENCE`` terminal, and a permit that was already spent stays
consumed, poisoned and unreplaced.  Nothing suppresses a warning, clips a value or floors a
forecast.

Honest limits.  This is local capability discipline; it is neither cryptographic secrecy nor
Owner authentication, which remains with the separate exact Owner activation.  A Python closure
is not secret: arbitrary in-process code can still reach cell contents by reflection.  What
these controls do give is that no ordinary module-surface call, wrapper, copy, mapping, duck
type, serial reuse or replay can obtain rows or real-mode authority, and that persistent replay
protection depends on the exclusive activation claim and the reservation being retained on disk.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from numbers import Real
from typing import Final, NoReturn

import numpy as np

from mes_quant.exploration.test3_contract import (
    BOOTSTRAP_REPETITIONS,
    FOLD_ORDER,
    MASTER_SEED,
    MODEL_COLUMNS,
    MODEL_ORDER,
    PRIMARY_BLOCK_LENGTH,
    PROTOCOL_ID,
    PROTOCOL_SHA256,
    REAL_FOLD_FIT_BUDGET,
    RELATIVE_QLIKE_REDUCTION_FLOOR,
    REQUIRED_BLOCK_LENGTHS,
    TARGET_HORIZON_MINUTES,
    TARGET_SPACE_ID,
    TerminalDisposition,
)
from mes_quant.exploration.test3_design import (
    Harmonic,
    Test3DesignContractError,
    common_eligibility,
    design_values,
)
from mes_quant.exploration.test3_stats import (
    ContinuationInputs,
    DependenceRow,
    SessionImprovementAggregate,
    Test3StatsContractError,
    back_transform_log_variance,
    decide_continuation,
    dependence_summary,
    duan_smearing_factor,
    paired_session_block_bootstrap,
    qlike,
    relative_qlike_reduction,
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

#: Frozen holdout calendar year per fold; a holdout row from another year is structural.
FOLD_HOLDOUT_YEARS: Final[Mapping[str, int]] = {"WF_2022": 2022, "WF_2023": 2023}

#: Frozen structural prefit minima; failing any of these is ``UNDERPOWERED_STOP`` before a fit.
MIN_HOLDOUT_SESSIONS: Final[int] = 20
REQUIRED_ACF_LAGS: Final[tuple[int, ...]] = tuple(range(1, 9))

#: Frozen bootstrap plan: block lengths 5, 1 and 20 in that order, 2,000 replicates each.
BOOTSTRAP_BLOCK_ORDER: Final[tuple[int, ...]] = REQUIRED_BLOCK_LENGTHS
EXPECTED_BOOTSTRAP_REPLICATES: Final[int] = BOOTSTRAP_REPETITIONS * len(BOOTSTRAP_BLOCK_ORDER)

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
        "mes_quant.exploration.test3_stats",
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

#: The closed top-level key set of the activation envelope.  The envelope carries nothing but
#: one nested payload and the digest of that payload, so the digest can never cover itself or
#: any envelope field.
ACTIVATION_ENVELOPE_KEYS: Final[frozenset[str]] = frozenset(
    {"activation_payload", "activation_payload_sha256"}
)

#: The closed key set of the nested activation payload.  The payload alone is digested.
ACTIVATION_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "fit_permit_budget",
        "implementation_path_sha256",
        "implementation_paths",
        "override_id",
        "protocol_id",
        "protocol_sha256",
        "recovery_lineage_id",
        "runtime_evidence",
        "target_space_id",
    }
)

#: Spent identities that a fresh recovery lineage may never reuse or re-credit.
FORBIDDEN_HISTORICAL_IDENTITIES: Final[frozenset[str]] = frozenset(
    {
        "AUTH_TEST3_G3P_TRAIN_PREFIT_20260825",
        "MES_TEST3_G3P_TRAIN_PREFIT_V1",
        "OWNER_AUTHORIZED_TEST3_G3P_TRAIN_PREFIT_20260825",
        "TEST3_G3P_TRAIN_TARGET_SUPPORT_PREFIT",
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

#: Closed record kinds; every durable runtime record declares exactly one of them.
RESERVATION_RECORD_KIND: Final[str] = "TEST3_ONE_SHOT_EXECUTION_AUTHORITY_RESERVATION_V1"
PERMIT_RECORD_KIND: Final[str] = "TEST3_ONE_SHOT_FIT_PERMIT_V1"
TERMINAL_RECORD_KIND: Final[str] = "TEST3_ONE_SHOT_TERMINAL_V1"

RESERVATION_STATUS: Final[str] = (
    "RESERVED_AND_DURABLE_BEFORE_ANY_SOURCE_PROVIDER_OR_TARGET_ACCESS"
)
VALIDATION_STATUS: Final[str] = "UNOPENED"
FINAL_TEST_STATUS: Final[str] = "SEALED"


class Test3G3FOneShotError(RuntimeError):
    """Base fail-closed error for the one-shot G3-F stage."""


class Test3G3FPreActivationStop(Test3G3FOneShotError):
    """Raised when a real surface is requested before a separate exact Owner activation."""


class Test3G3FPermitError(Test3G3FOneShotError):
    """Raised when the unreplenished four-permit contract would be violated."""


class Test3G3FUnderpoweredStop(Test3G3FOneShotError):
    """Raised for a pre-fit structural minimum failure, always before any permit or fit."""


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
        "estimator": "INTERNAL_NUMPY_LINALG_LSTSQ_RCOND_NONE_NO_CALLBACK_IN_REAL_MODE",
        "bootstrap_plan": BOOTSTRAP_BLOCK_ORDER,
        "bootstrap_replicates": EXPECTED_BOOTSTRAP_REPLICATES,
        "min_holdout_sessions": MIN_HOLDOUT_SESSIONS,
        "required_acf_lags": REQUIRED_ACF_LAGS,
        "validation": VALIDATION_STATUS,
        "final_test": FINAL_TEST_STATUS,
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


def _finite_float64_vector(value: object, *, expected_size: int, label: str) -> np.ndarray:
    """Prove one linear-algebra result immediately, without any floating-point error policy.

    The BLAS/LAPACK-backed least-squares call is not wrapped in :func:`_strict_numerics`, because
    a backend status flag is not evidence about the value that was returned.  Its correctness is
    established here instead: the result must convert exactly to float64, must have exactly one
    dimension of exactly the expected length, and must be finite in every entry.  Anything else
    raises the ordinary fail-closed error, so the spent permit stays consumed, poisoned and
    unreplaced and exactly one ``INVALID_EVIDENCE`` terminal is written without retry.  Nothing
    here clips, floors, widens a tolerance or absorbs a value.

    :func:`_checked_matrix_vector_product` reuses this same proof as the final step of the
    explicit prediction kernel, so a product and a fitted coefficient vector are held to one
    identical dimension, shape, dtype and finiteness contract.
    """

    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size < 1:
        raise _error(f"{label} requires a positive expected size")
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise _error(f"{label} must convert exactly to float64") from exc
    if array.dtype != np.dtype(np.float64):
        raise _error(f"{label} must convert exactly to float64")
    if array.ndim != 1 or array.shape != (expected_size,):
        raise _error(f"{label} must be one-dimensional with exactly {expected_size} values")
    if not np.all(np.isfinite(array)):
        raise _error(f"{label} must be finite")
    return array


def _checked_matrix_vector_product(
    matrix: object,
    vector: object,
    *,
    expected_rows: int,
    label: str,
) -> np.ndarray:
    """Compute one float64 matrix-vector product explicitly, with no BLAS and no status flag.

    This is the single prediction kernel for both the fitted TRAIN log-variance and the holdout
    log-variance.  It deliberately avoids ``@``, :func:`numpy.matmul` and every other BLAS-backed
    route.  A blocked and vectorized backend kernel evaluates padding lanes and partial products
    that never reach the returned result, and it sets the hardware floating-point status flags for
    them; NumPy then reports those flags as ``RuntimeWarning`` divide, overflow or invalid
    conditions even for a well-conditioned product whose returned values are exact and finite.
    Such a warning describes the backend, not the arithmetic this stage asked for, and it must
    neither fail a valid fit nor be silenced by a warning filter.

    The kernel therefore proceeds in three explicit steps and nothing else:

    1. Operand compatibility is validated **before** any arithmetic: both operands must convert
       exactly to float64, the matrix must be two-dimensional with exactly ``expected_rows`` rows
       and at least one column, and its column count must equal the vector length.  An
       incompatible pair is a defect and is refused before a single product is formed.
    2. The contraction is evaluated as ``numpy.einsum("ij,j->i", ..., optimize=False)``, a
       deterministic explicit sum of products with no optimization or BLAS dispatch, under a
       narrowly relevant ``numpy.errstate(over="raise", invalid="raise")``.  The state covers only
       this one contraction, so a genuine overflow or invalid operation in the requested
       arithmetic raises ``FloatingPointError`` instead of escaping as a warning.
    3. The product is proved immediately by :func:`_finite_float64_vector` for exact dimension,
       shape, float64 dtype and finiteness.

    Both failure routes are the ordinary fail-closed route: the raised error propagates, the
    permit that was already spent stays consumed, poisoned and unreplaced, and exactly one
    ``INVALID_EVIDENCE`` terminal is written without retry.  Nothing here suppresses a warning,
    clips, floors, widens a tolerance or absorbs an exception, and the frozen
    ``numpy.linalg.lstsq(rcond=None)`` estimator is untouched by this kernel.
    """

    if isinstance(expected_rows, bool) or not isinstance(expected_rows, int) or expected_rows < 1:
        raise _error(f"{label} requires a positive expected row count")
    try:
        left = np.asarray(matrix, dtype=np.float64)
        right = np.asarray(vector, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise _error(f"{label} operands must convert exactly to float64") from exc
    if left.dtype != np.dtype(np.float64) or right.dtype != np.dtype(np.float64):
        raise _error(f"{label} operands must convert exactly to float64")
    if left.ndim != 2 or right.ndim != 1:
        raise _error(f"{label} needs a two-dimensional matrix and a one-dimensional vector")
    if left.shape[0] != expected_rows:
        raise _error(f"{label} matrix must have exactly {expected_rows} rows")
    if left.shape[1] < 1:
        raise _error(f"{label} matrix must have at least one column")
    if left.shape[1] != right.shape[0]:
        raise _error(
            f"{label} matrix columns ({int(left.shape[1])}) must equal the vector length "
            f"({int(right.shape[0])})"
        )
    with np.errstate(over="raise", invalid="raise"):
        product = np.einsum("ij,j->i", left, right, optimize=False)
    return _finite_float64_vector(product, expected_size=expected_rows, label=label)


def _underpowered(message: str) -> NoReturn:
    raise Test3G3FUnderpoweredStop(message)


def _session_date(row: OneShotEligibleRow) -> date:
    """Derive the frozen NYSE session date from the G3-P session identity."""

    try:
        parsed = date.fromisoformat(row.session_id)
    except ValueError as exc:
        raise _error(f"session_id must be an ISO session date: {row.session_id}") from exc
    if type(parsed) is not date:
        raise _error("session_date must be an exact date")
    return parsed


def _recovery_partition(
    fold_id: str,
    rows: tuple[OneShotEligibleRow, ...],
) -> OneShotFoldPartition:
    """Partition one fold under the full frozen structural minima.

    This is the recovery-only partition.  It keeps every rule of the shared partition -- purge,
    the 60-minute wall-clock boundary gap and non-empty partitions -- and adds the frozen holdout
    calendar year and the 20-ordered-session minimum.  Any failure here is ``UNDERPOWERED_STOP``
    and happens before any permit, matrix decomposition or fit.
    """

    try:
        partition = _fold_partition(fold_id, rows)
    except Test3G3FOneShotError as exc:
        _underpowered(f"{fold_id} structural partition failed: {exc}")
    expected_year = FOLD_HOLDOUT_YEARS[fold_id]
    for index in partition.holdout_indices:
        if rows[index].decision_time_utc.year != expected_year:
            _underpowered(
                f"{fold_id} holdout row {rows[index].decision_identity} is not in calendar "
                f"year {expected_year}"
            )
    if len(partition.holdout_sessions) < MIN_HOLDOUT_SESSIONS:
        _underpowered(
            f"{fold_id} requires at least {MIN_HOLDOUT_SESSIONS} ordered holdout sessions, "
            f"observed {len(partition.holdout_sessions)}"
        )
    return partition


def _dependence_record(
    fold_id: str,
    rows: tuple[OneShotEligibleRow, ...],
    indices: tuple[int, ...],
    *,
    label: str,
) -> tuple[tuple[DependenceRow, ...], dict[str, object]]:
    """Compute the frozen within-session ACF profile and require lags 1..8 to be defined."""

    dependence_rows = tuple(
        DependenceRow(
            fold_id,
            rows[index].session_id,
            rows[index].decision_time_utc,
            rows[index].rv_fwd_60,
        )
        for index in indices
    )
    return dependence_rows, _summarize_dependence(dependence_rows, label=label)


def _summarize_dependence(
    dependence_rows: tuple[DependenceRow, ...],
    *,
    label: str,
) -> dict[str, object]:
    try:
        summary = dependence_summary(dependence_rows)
    except Test3StatsContractError as exc:
        _underpowered(f"{label} dependence audit failed: {exc}")
    observed = {item.lag: item for item in summary.lags}
    for lag in REQUIRED_ACF_LAGS:
        item = observed.get(lag)
        if item is None or item.rho_observed is None or not math.isfinite(item.rho_observed):
            _underpowered(f"{label} required ACF lag {lag} is undefined")
    return {
        "row_count": summary.row_count,
        "design_effect": summary.design_effect,
        "effective_sample_size": summary.effective_sample_size,
        "status": summary.status,
        "lags": [
            {
                "lag": item.lag,
                "pairs": item.pairs,
                "rho_observed": item.rho_observed,
                "rho_null": item.rho_null,
                "excess": item.excess,
            }
            for item in summary.lags
        ],
    }


def _strict_numerics() -> np.errstate:
    """Return the strict NumPy error state for the semantic elementwise regions.

    Overflow, division by zero and invalid operations are raised as ``FloatingPointError``
    instead of being warned about, ignored or absorbed.  Nothing here suppresses a warning,
    clips a value or floors a forecast: a raised error travels the ordinary failure route, so
    the permit that was already spent stays consumed, poisoned and unreplaced and exactly one
    ``INVALID_EVIDENCE`` terminal is written without retry.

    The scope of this state is deliberately semantic.  It guards the elementwise exponential,
    division and logarithm arithmetic this module performs itself -- the residual difference,
    the fold/model-local Duan exponential, the back-transform, QLIKE, the relative reduction and
    the bootstrap arithmetic -- where a raised floating-point condition really is a defect in
    the quantity being computed.

    It is never placed around ``numpy.linalg.lstsq``.  That call runs inside a BLAS/LAPACK backend
    whose blocked and vectorized inner kernels set hardware floating-point status flags for lanes
    and partial products that never reach the returned result, so a flag observed there describes
    the backend rather than the correctness of the fit, and treating it as a semantic error
    misclassifies a valid result as a failure.  Its coefficients are instead proved immediately
    and explicitly by :func:`_finite_float64_vector`, and an invalid result fails closed on
    exactly the same route.

    It is not placed around the train/holdout predictions either, because those no longer use a
    BLAS-backed product at all.  :func:`_checked_matrix_vector_product` owns them and carries its
    own narrowly scoped raised state over one deterministic explicit contraction, so a genuine
    overflow or invalid operation in the requested arithmetic still raises rather than warning,
    while an unrelated backend lane flag can no longer be produced.

    Gradual underflow is left at the NumPy default disposition for the same reason: a subnormal
    or flushed intermediate is an IEEE status, not a defect.  Every required output is proved by
    an explicit strictly-positive and finite check rather than by an underflow flag.
    """

    return np.errstate(over="raise", divide="raise", invalid="raise", under="ignore")


def _numerical_identity() -> dict[str, object]:
    """Report the NumPy and LAPACK identity without printing anything."""

    build: dict[str, object] = {}
    try:
        configuration = np.show_config(mode="dicts")
        dependencies = configuration.get("Build Dependencies", {})
        for name in ("blas", "lapack"):
            entry = dependencies.get(name, {})
            build[name] = {
                "name": str(entry.get("name", "UNAVAILABLE")),
                "version": str(entry.get("version", "UNAVAILABLE")),
            }
    except Exception:  # noqa: BLE001 - identity disclosure degrades, it never fails a run
        build = {"blas": "UNAVAILABLE", "lapack": "UNAVAILABLE"}
    return {
        "numpy_version": str(np.__version__),
        "float_dtype": "float64",
        "estimator": "numpy.linalg.lstsq(rcond=None)",
        "build_dependencies": build,
    }


def _singular_rank(matrix: np.ndarray) -> tuple[int, np.ndarray]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    if singular.size == 0 or not np.all(np.isfinite(singular)):
        _underpowered("training design singular values must be finite")
    tolerance = max(matrix.shape) * float(np.finfo(np.float64).eps) * float(singular[0])
    return int(np.count_nonzero(singular > tolerance)), singular


@dataclass(frozen=True, slots=True)
class _PrefitStructure:
    """The complete structural prefit state; it exists only before any permit or fit."""

    rows: tuple[OneShotEligibleRow, ...]
    partitions: Mapping[str, OneShotFoldPartition]
    designs: Mapping[str, np.ndarray]
    response: np.ndarray
    dependence: Mapping[str, object]


def _prefit_structure(rows: Iterable[OneShotEligibleRow]) -> _PrefitStructure:
    """Run every structural minimum before a permit may be created or a fit may start."""

    materialized = _validate_rows(rows, mode=ExecutionMode.OWNER_ACTIVATED_REAL)
    partitions = {fold_id: _recovery_partition(fold_id, materialized) for fold_id in FOLD_ORDER}
    first, second = (partitions[fold_id] for fold_id in FOLD_ORDER)
    if set(first.holdout_indices) & set(second.holdout_indices):
        _underpowered("fold holdouts must be disjoint before pooled out-of-fold support")
    pooled_rows: list[DependenceRow] = []
    dependence: dict[str, object] = {}
    for fold_id in FOLD_ORDER:
        fold_rows, record = _dependence_record(
            fold_id,
            materialized,
            partitions[fold_id].holdout_indices,
            label=fold_id,
        )
        dependence[fold_id] = record
        pooled_rows.extend(fold_rows)
    dependence["pooled_disjoint_oof"] = _summarize_dependence(
        tuple(pooled_rows),
        label="pooled disjoint out-of-fold",
    )
    response = build_response_vector(materialized)
    designs = {model_id: build_design_matrix(model_id, materialized) for model_id in MODEL_ORDER}
    for model_id, fold_id in EXPECTED_PAIR_ORDER:
        index = np.asarray(partitions[fold_id].train_indices, dtype=np.int64)
        train_design = designs[model_id][index]
        columns = len(MODEL_COLUMNS[model_id])
        if train_design.shape[0] <= columns:
            _underpowered(
                f"{model_id}/{fold_id} training rows ({train_design.shape[0]}) must exceed "
                f"fitted columns ({columns})"
            )
        rank, _singular = _singular_rank(train_design)
        if rank != columns:
            _underpowered(
                f"{model_id}/{fold_id} training design is rank deficient: rank={rank}, "
                f"columns={columns}"
            )
    return _PrefitStructure(
        rows=materialized,
        partitions=partitions,
        designs=designs,
        response=response,
        dependence=dependence,
    )


def _session_tables(
    oof: Mapping[str, Mapping[str, object]],
) -> dict[str, tuple[SessionImprovementAggregate, ...]]:
    """Aggregate ordered per-session improvement sums and row counts, fold by fold."""

    tables: dict[str, tuple[SessionImprovementAggregate, ...]] = {}
    for fold_id in FOLD_ORDER:
        fold = oof[fold_id]
        order: list[str] = []
        counts: dict[str, int] = {}
        sums: dict[str, float] = {}
        dates: dict[str, date] = {}
        for session_id, session_date, improvement in zip(
            fold["session_ids"], fold["session_dates"], fold["improvement"], strict=True
        ):
            if session_id not in counts:
                order.append(session_id)
                counts[session_id] = 0
                sums[session_id] = 0.0
                dates[session_id] = session_date
            elif dates[session_id] != session_date:
                raise _error(f"session {session_id} has an inconsistent session date")
            counts[session_id] += 1
            sums[session_id] += float(improvement)
        tables[fold_id] = tuple(
            SessionImprovementAggregate(
                fold_id=fold_id,
                session_id=session_id,
                session_date=dates[session_id],
                row_count=counts[session_id],
                improvement_sum=sums[session_id],
            )
            for session_id in order
        )
    return tables


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


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


def _create_record_once(
    root: str,
    *,
    evidence_root: str,
    namespace: str,
    name: str,
    payload: bytes,
    label: str,
) -> str:
    """Atomically and durably create one named record inside an existing directory.

    This is the single write surface of this module.  It publishes the activation replay claim,
    the execution-authority reservation, each ordered fit permit and the one terminal record.
    Every path component below ``root`` must already exist and must not be a symlink: nothing
    here creates, renames or removes a directory, and the traversal uses directory descriptors
    with ``O_NOFOLLOW`` so a symlinked component cannot redirect it.  The record itself is
    created with ``O_CREAT | O_EXCL`` and is never overwritten or truncated, and both the record
    and its directory are fsynced before the caller may proceed.  An existing name, an unusable
    directory, or any publication or durability ambiguity is a terminal refusal.
    """

    descriptors = _open_namespace_directory(root, evidence_root, namespace, label=label)
    try:
        parent = descriptors[-1]
        try:
            handle = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
                dir_fd=parent,
            )
        except FileExistsError as exc:
            raise _error(f"{label} already exists; create-once is never overwritten") from exc
        except OSError as exc:
            raise _error(f"{label} could not be created exclusively") from exc
        try:
            view = memoryview(payload)
            while view:
                progress = os.write(handle, view)
                if progress <= 0:
                    raise _error(f"{label} made no write progress")
                view = view[progress:]
            os.fsync(handle)
        except OSError as exc:
            raise _error(f"{label} could not be published durably") from exc
        finally:
            os.close(handle)
        try:
            os.fsync(parent)
        except OSError as exc:
            raise _error(f"{label} directory could not be published durably") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return name


def _open_namespace_directory(
    root: str,
    evidence_root: str,
    namespace: str,
    *,
    label: str,
) -> list[int]:
    """Open the evidence namespace by directory descriptor; the caller closes every result."""

    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in os.supports_dir_fd
    ):
        raise _error(f"{label} requires secure directory-descriptor traversal")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        try:
            descriptors.append(os.open(root, directory_flags))
        except OSError as exc:
            raise _error(f"{label} root directory is unusable") from exc
        for segment in (*evidence_root.split("/"), namespace):
            try:
                descriptors.append(os.open(segment, directory_flags, dir_fd=descriptors[-1]))
            except OSError as exc:
                raise _error(
                    f"{label} directory is missing, symlinked or not a directory"
                ) from exc
        if not stat.S_ISDIR(os.fstat(descriptors[-1]).st_mode):
            raise _error(f"{label} directory is missing, symlinked or not a directory")
    except BaseException:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    return descriptors


def _read_record_once(
    root: str,
    *,
    evidence_root: str,
    namespace: str,
    name: str,
    label: str,
) -> bytes:
    """Read back one published record through the same non-symlinked namespace traversal."""

    descriptors = _open_namespace_directory(root, evidence_root, namespace, label=label)
    try:
        try:
            handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
        except OSError as exc:
            raise _error(f"{label} is missing, symlinked or unreadable") from exc
        try:
            status = os.fstat(handle)
            if not stat.S_ISREG(status.st_mode):
                raise _error(f"{label} is not a regular file")
            if status.st_size > ACTIVATION_FILE_MAX_BYTES:
                raise _error(f"{label} exceeds the bounded read size")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(handle, 65_536)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(handle)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return b"".join(chunks)


def _claim_activation_once(
    root: str,
    *,
    evidence_root: str,
    namespace: str,
    reservation_name: str,
    payload: bytes,
) -> str:
    """Atomically claim one activation; this is a replay claim, not a reservation."""

    return _create_record_once(
        root,
        evidence_root=evidence_root,
        namespace=namespace,
        name=reservation_name + _ACTIVATION_CLAIM_SUFFIX,
        payload=payload,
        label="the activation replay claim",
    )


def _assert_json_closed(value: object, *, field: str) -> object:
    """Fail closed unless ``value`` is a closed, finite, deterministic JSON structure."""

    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _error(f"record field {field} must be finite")
        return value
    if isinstance(value, Mapping):
        for key in value:
            if not isinstance(key, str):
                raise _error(f"record field {field} has a non-string key")
        return {key: _assert_json_closed(value[key], field=f"{field}.{key}") for key in value}
    if isinstance(value, (list, tuple)):
        return [
            _assert_json_closed(item, field=f"{field}[{index}]")
            for index, item in enumerate(value)
        ]
    raise _error(f"record field {field} is not a closed JSON value")


def _canonical_bytes(value: object) -> bytes:
    """Serialize one closed structure to the single canonical UTF-8 byte form."""

    return (
        json.dumps(
            _assert_json_closed(value, field="record"),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_digest(value: object) -> str:
    """Digest the canonical bytes of one closed structure; never text typed by hand."""

    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _coefficient_sha256(beta: object) -> str:
    """Digest coefficients as little-endian float64 C-order bytes, never as text."""

    array = np.ascontiguousarray(np.asarray(beta, dtype="<f8").reshape(-1))
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        raise _error("coefficient digest requires a finite one-dimensional vector")
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


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
    verified_binding: list[dict[str, object]] = []
    authority_registry: dict[int, dict[str, object]] = {}
    authority_state: dict[str, object] = {"armed": True, "issued": None, "state": None}
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
            "activation_file_sha256",
            "activation_payload_sha256",
            "fit_permit_budget",
            "override_id",
            "recovery_lineage_id",
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
            delivered = rows_from_handoff(handoff)
            state = authority_state["state"]
            if state is None:
                return delivered
            # Real mode: the rows never leave this closure.  They go straight into the
            # activation-bound numerical pipeline and only a closed, row-free summary survives.
            run_real_pipeline(delivered, state)
            return None

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
        if not isinstance(document, dict) or set(document) != set(ACTIVATION_ENVELOPE_KEYS):
            raise _error("the activation file must carry the exact closed envelope key set")
        _assert_finite(document, field="activation")
        payload = document["activation_payload"]
        if not isinstance(payload, dict) or set(payload) != set(ACTIVATION_PAYLOAD_KEYS):
            raise _error("the activation payload must carry the exact closed key set")
        declared_payload_sha256 = document["activation_payload_sha256"]
        if not _is_sha256(declared_payload_sha256):
            raise _error("activation_payload_sha256 must be a lowercase 64-hex digest")
        payload_sha256 = _canonical_digest(payload)
        if payload_sha256 != declared_payload_sha256:
            raise _error("the activation digest does not cover the exact nested payload")
        canonical = _canonical_bytes(
            {"activation_payload": payload, "activation_payload_sha256": payload_sha256}
        )
        if raw != canonical:
            raise _error("the activation file is not the exact canonical UTF-8 envelope")
        lineage = _identity(payload["recovery_lineage_id"], field="recovery_lineage_id")
        override = _identity(payload["override_id"], field="override_id")
        for label, value in (("recovery_lineage_id", lineage), ("override_id", override)):
            if len(value) > _MAX_NAME_LENGTH or not set(value).issubset(_NAME_CHARACTERS):
                raise _error(f"{label} must be a bounded closed-alphabet identity")
            if value in FORBIDDEN_HISTORICAL_IDENTITIES:
                raise _error(f"{label} may not reuse a spent historical identity")
        if payload["protocol_id"] != PROTOCOL_ID:
            raise _error("the activation must bind the exact ratified protocol identity")
        if payload["protocol_sha256"] != PROTOCOL_SHA256:
            raise _error("the activation must bind the exact ratified protocol bytes")
        if payload["target_space_id"] != TARGET_SPACE_ID:
            raise _error("the activation must bind the exact frozen target space")
        budget = payload["fit_permit_budget"]
        if (
            isinstance(budget, bool)
            or not isinstance(budget, int)
            or budget != FIT_PERMIT_BUDGET
        ):
            raise _error(f"the lifetime fit budget is exactly {FIT_PERMIT_BUDGET}")
        declared_paths = payload["implementation_paths"]
        if (
            not isinstance(declared_paths, list)
            or tuple(declared_paths) != REVIEWED_IMPLEMENTATION_PATHS
        ):
            raise _error("the activation must bind the exact ordered six implementation paths")
        declared_digests = payload["implementation_path_sha256"]
        if (
            not isinstance(declared_digests, list)
            or len(declared_digests) != len(REVIEWED_IMPLEMENTATION_PATHS)
            or not all(_is_sha256(item) for item in declared_digests)
        ):
            raise _error("the activation must bind the reviewed bytes of all six paths")
        observed = _observed_reviewed_digests(root)
        if observed != tuple(declared_digests):
            raise _error("the current six-path bytes do not match the activation")
        evidence = _validated_runtime_evidence(payload["runtime_evidence"])
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
            activation_file_sha256=activation_file_sha256,
            activation_payload_sha256=payload_sha256,
            fit_permit_budget=budget,
            override_id=override,
            recovery_lineage_id=lineage,
            repository_root=root,
            reviewed_digests=observed,
            runtime_evidence=evidence,
            serial=serial,
        )
        activation_registry[serial] = issued_state
        verified_root.append(root)
        verified_digests.append(observed)
        verified_binding.append(
            {
                "activation_file_sha256": activation_file_sha256,
                "activation_payload_sha256": payload_sha256,
                "evidence_namespace": str(names["namespace"]),
                "evidence_root": str(names["root"]),
                "fit_permit_budget": budget,
                "implementation_path_sha256": list(observed),
                "implementation_paths": list(REVIEWED_IMPLEMENTATION_PATHS),
                "override_id": override,
                "permit_names": list(names["permit_names"]),
                "protocol_id": PROTOCOL_ID,
                "protocol_sha256": PROTOCOL_SHA256,
                "recovery_lineage_id": lineage,
                "reservation_name": str(names["reservation_name"]),
                "target_space_id": TARGET_SPACE_ID,
                "terminal_name": str(names["terminal_name"]),
            }
        )
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

    class _ExecutionAuthority(_ClosureBound):
        """Opaque witness of one durable execution-authority reservation.

        It carries nothing but its serial: every reservation fact lives in the closure, so no
        field on this object can be redirected to change what is written or rechecked.
        """

        __slots__ = ("serial",)

        def __init__(self, key: object, /, **fields: object) -> None:
            if key is not closure_key:
                raise _error("direct construction of the execution authority is forbidden")
            if set(fields) != set(type(self).__slots__):
                raise _error("the execution authority requires its exact closed field set")
            for name in type(self).__slots__:
                object.__setattr__(self, name, fields[name])

    def publish_record(
        state: Mapping[str, object],
        *,
        name: str,
        payload: Mapping[str, object],
        label: str,
    ) -> str:
        """Create one durable record exactly once, then reread and verify it semantically."""

        expected = _assert_json_closed(payload, field="record")
        body = _canonical_bytes(expected)
        _create_record_once(
            str(state["root"]),
            evidence_root=str(state["evidence_root"]),
            namespace=str(state["namespace"]),
            name=name,
            payload=body,
            label=label,
        )
        observed = _read_record_once(
            str(state["root"]),
            evidence_root=str(state["evidence_root"]),
            namespace=str(state["namespace"]),
            name=name,
            label=label,
        )
        if observed != body:
            raise _error(f"{label} failed its byte-exact reread")
        try:
            parsed = json.loads(
                observed.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_json_constant,
            )
        except ValueError as exc:
            raise _error(f"{label} reread is not one closed JSON object") from exc
        if parsed != expected:
            raise _error(f"{label} semantic reread rejects the published content")
        return hashlib.sha256(body).hexdigest()

    def resolve_authority(authority: object) -> dict[str, object]:
        issued = authority_state["issued"]
        if issued is None or authority is not issued:
            _stop(
                "execution authority must be the exact object returned by "
                "open_execution_authority"
            )
        if type(authority) is not _ExecutionAuthority:
            _stop("execution authority must be a verified execution authority")
        serial = _serial_of(authority)
        state = authority_registry.get(serial) if serial is not None else None
        if state is None:
            _stop("the execution authority is absent or already released")
        return state

    def open_execution_authority(activation: object) -> object:
        """Accept the activation and publish one durable execution-authority reservation.

        This runs before any source, provider, target, target-space, permit or fit surface.  It
        spends the exact issued activation capability, rechecks the reviewed six-path bytes from
        closure-captured values, then exclusively creates the activation-named reservation and
        rereads it.  The activation replay claim taken by the loader is not this reservation.
        """

        if not authority_state["armed"]:
            raise _error(
                "the execution authority is one-attempt per module instance and is spent"
            )
        authority_state["armed"] = False
        accept_and_consume_activation(activation)
        binding = dict(verified_binding[0])
        state: dict[str, object] = {
            "root": verified_root[0],
            "evidence_root": binding["evidence_root"],
            "namespace": binding["evidence_namespace"],
            "reservation_name": binding["reservation_name"],
            "permit_names": list(binding["permit_names"]),
            "terminal_name": binding["terminal_name"],
            "binding": binding,
            "permits_created": [],
            "terminal_attempted": False,
            "terminal_written": False,
            "report": None,
            "released": False,
            "closed": False,
        }
        reservation = {
            "record_kind": RESERVATION_RECORD_KIND,
            "module_id": ONE_SHOT_MODULE_ID,
            "activation_binding": binding,
            "pair_order": [f"{model}/{fold}" for model, fold in EXPECTED_PAIR_ORDER],
            "status": RESERVATION_STATUS,
            "retry_authorized": False,
            "replacement_authorized": False,
            "validation_status": VALIDATION_STATUS,
            "final_test_status": FINAL_TEST_STATUS,
        }
        state["reservation_sha256"] = publish_record(
            state,
            name=str(state["reservation_name"]),
            payload=reservation,
            label="the execution-authority reservation",
        )
        serial = next_serial()
        authority = _ExecutionAuthority(closure_key, serial=serial)
        authority_registry[serial] = state
        authority_state["issued"] = authority
        authority_state["state"] = state
        return authority

    def assert_execution_authority_reserved(authority: object) -> Mapping[str, object]:
        """Prove one durable reservation exists; the predecessor stage calls this first."""

        state = resolve_authority(authority)
        if state["closed"]:
            _stop("the execution authority is already closed")
        if not _is_sha256(state.get("reservation_sha256")):
            _stop("no durable execution-authority reservation exists")
        binding = dict(state["binding"])
        binding["reservation_name"] = state["reservation_name"]
        binding["reservation_sha256"] = state["reservation_sha256"]
        binding["reservation_status"] = RESERVATION_STATUS
        return binding

    def terminal_payload(
        state: dict[str, object],
        *,
        disposition: str,
        reasons: tuple[str, ...],
        source_binding: Mapping[str, object],
        permits: Mapping[str, object],
        fits: list[dict[str, object]],
        metrics: Mapping[str, object] | None,
        bootstrap: list[dict[str, object]],
        sign_diagnostic: Mapping[str, object] | None,
        gates: Mapping[str, object] | None,
        counters: Mapping[str, object],
        cleanup: Mapping[str, object],
    ) -> dict[str, object]:
        body = {
            "record_kind": TERMINAL_RECORD_KIND,
            "module_id": ONE_SHOT_MODULE_ID,
            "activation_binding": dict(state["binding"]),
            "reservation": {
                "name": state["reservation_name"],
                "sha256": state["reservation_sha256"],
                "status": RESERVATION_STATUS,
            },
            "source_and_g3p_binding": dict(source_binding),
            "pair_order": [f"{model}/{fold}" for model, fold in EXPECTED_PAIR_ORDER],
            "permits": dict(permits),
            "fits": fits,
            "metrics": dict(metrics) if metrics is not None else None,
            "bootstrap": bootstrap,
            "sign_diagnostic": dict(sign_diagnostic) if sign_diagnostic is not None else None,
            "gates": dict(gates) if gates is not None else None,
            "disposition": disposition,
            "reasons": list(reasons),
            "counters": dict(counters),
            "cleanup": dict(cleanup),
            "validation_status": VALIDATION_STATUS,
            "final_test_status": FINAL_TEST_STATUS,
            "retry_authorized": False,
        }
        body["terminal_record_sha256"] = _canonical_digest(body)
        return body

    def cleanup_observation(state: dict[str, object]) -> dict[str, object]:
        """Report exactly what cleanup does; it never claims memory erasure or deletion."""

        return {
            "scope": "CLOSES_DESCRIPTORS_AND_RELEASES_LIVE_REFERENCES_ONLY",
            "open_descriptors": 0,
            "live_row_references_released": bool(state["released"]),
            "durable_records_deleted": 0,
            "durable_records_mutated": 0,
            "memory_erasure_claimed": False,
        }

    def write_terminal(
        state: dict[str, object],
        *,
        disposition: str,
        reasons: tuple[str, ...],
        source_binding: Mapping[str, object],
        permits: Mapping[str, object],
        fits: list[dict[str, object]],
        metrics: Mapping[str, object] | None,
        bootstrap: list[dict[str, object]],
        sign_diagnostic: Mapping[str, object] | None,
        gates: Mapping[str, object] | None,
        counters: Mapping[str, object],
    ) -> dict[str, object]:
        if state["terminal_attempted"]:
            raise _error("the one-shot terminal record is attempted exactly once")
        state["terminal_attempted"] = True
        state["released"] = True
        payload = terminal_payload(
            state,
            disposition=disposition,
            reasons=reasons,
            source_binding=source_binding,
            permits=permits,
            fits=fits,
            metrics=metrics,
            bootstrap=bootstrap,
            sign_diagnostic=sign_diagnostic,
            gates=gates,
            counters=counters,
            cleanup=cleanup_observation(state),
        )
        state["terminal_sha256"] = publish_record(
            state,
            name=str(state["terminal_name"]),
            payload=payload,
            label="the one-shot terminal record",
        )
        state["terminal_written"] = True
        state["report"] = {
            "disposition": disposition,
            "reasons": list(reasons),
            "counters": dict(counters),
            "permits": dict(permits),
            "reservation_name": state["reservation_name"],
            "terminal_name": state["terminal_name"],
            "terminal_record_sha256": payload["terminal_record_sha256"],
            "terminal_file_sha256": state["terminal_sha256"],
            "recovery_lineage_id": state["binding"]["recovery_lineage_id"],
            "validation_status": VALIDATION_STATUS,
            "final_test_status": FINAL_TEST_STATUS,
        }
        return payload

    def stop_counters(budget: OneShotFitPermitBudget | None) -> dict[str, object]:
        return {
            "permits_created": 0,
            "permits_consumed": 0 if budget is None else budget.permits_consumed,
            "real_fold_fit_calls": 0,
            "real_models_fitted": 0,
            "real_coefficients_computed": 0,
            "duan_factors_computed": 0,
            "real_forecasts_computed": 0,
            "real_qlike_evaluations": 0,
            "real_bootstrap_replicates": 0,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        }

    def record_terminal_stop(
        authority: object,
        *,
        disposition: str,
        reasons: Iterable[str],
        source_binding: Mapping[str, object],
    ) -> Mapping[str, object]:
        """Write the single terminal record for a stop that produced no validated fit."""

        state = resolve_authority(authority)
        if disposition not in {
            TerminalDisposition.UNDERPOWERED.value,
            TerminalDisposition.INVALID.value,
        }:
            raise _error("a stop terminal must be UNDERPOWERED_STOP or INVALID_EVIDENCE")
        counters = stop_counters(None)
        counters["permits_created"] = len(list(state["permits_created"]))
        write_terminal(
            state,
            disposition=disposition,
            reasons=tuple(str(reason) for reason in reasons),
            source_binding=source_binding,
            permits={
                "names": list(state["permit_names"]),
                "created": len(list(state["permits_created"])),
                "consumed": 0,
                "callback_starts": 0,
                "validated_outputs": 0,
                "refused_requests": 0,
                "poisoned": False,
                "sealed": False,
            },
            fits=[],
            metrics=None,
            bootstrap=[],
            sign_diagnostic=None,
            gates=None,
            counters=counters,
        )
        return dict(state["report"])

    def complete_real_execution(
        structure: _PrefitStructure,
        state: dict[str, object],
        budget: OneShotFitPermitBudget,
        source_binding: Mapping[str, object],
    ) -> None:
        """Publish four ordered permits, run four internal fits, and close the terminal."""

        identity = _numerical_identity()
        fits: list[dict[str, object]] = []
        forecasts: dict[tuple[str, str], np.ndarray] = {}
        for ordinal, (model_id, fold_id) in enumerate(EXPECTED_PAIR_ORDER, start=1):
            partition = structure.partitions[fold_id]
            train_index = np.asarray(partition.train_indices, dtype=np.int64)
            holdout_index = np.asarray(partition.holdout_indices, dtype=np.int64)
            train_design = np.ascontiguousarray(
                structure.designs[model_id][train_index], dtype=np.float64
            )
            train_response = np.ascontiguousarray(
                structure.response[train_index], dtype=np.float64
            )
            holdout_design = np.ascontiguousarray(
                structure.designs[model_id][holdout_index], dtype=np.float64
            )
            permit_name = str(state["permit_names"][ordinal - 1])
            publish_record(
                state,
                name=permit_name,
                payload={
                    "record_kind": PERMIT_RECORD_KIND,
                    "module_id": ONE_SHOT_MODULE_ID,
                    "recovery_lineage_id": state["binding"]["recovery_lineage_id"],
                    "reservation_name": state["reservation_name"],
                    "reservation_sha256": state["reservation_sha256"],
                    "ordinal": ordinal,
                    "model_id": model_id,
                    "fold_id": fold_id,
                    "column_names": list(MODEL_COLUMNS[model_id]),
                    "train_row_count": int(train_design.shape[0]),
                    "holdout_row_count": int(holdout_design.shape[0]),
                    "estimator": "numpy.linalg.lstsq(rcond=None)",
                    "replacement_authorized": False,
                    "status": "PERMIT_DURABLE_BEFORE_ITS_LEAST_SQUARES_CALL",
                },
                label=f"fit permit {ordinal}",
            )
            state["permits_created"].append(permit_name)
            permit = budget.consume(model_id=model_id, fold_id=fold_id)
            budget.start_callback(permit)
            try:
                # The frozen estimator runs in its BLAS/LAPACK backend with no surrounding
                # floating-point error policy; its result is proved explicitly just below.
                output = np.linalg.lstsq(train_design, train_response, rcond=None)
            except Exception:
                budget.fail(permit, reason="internal_least_squares_raised")
                raise
            try:
                beta, _residual_sums, rank, singular = output
                dimension, validated_rank = _validated_fit_output(
                    (beta, _residual_sums, rank, singular),
                    model_id=model_id,
                    fold_id=fold_id,
                )
                coefficients = _finite_float64_vector(
                    beta,
                    expected_size=len(MODEL_COLUMNS[model_id]),
                    label=f"{model_id}/{fold_id} least-squares coefficients",
                )
                # Neither prediction uses a BLAS-backed product. Each is one explicit checked
                # float64 contraction: operand compatibility is validated first, the requested
                # arithmetic raises overflow and invalid conditions instead of warning, and the
                # product is then proved for exact dimension, shape and finiteness.
                train_fitted = _checked_matrix_vector_product(
                    train_design,
                    coefficients,
                    expected_rows=int(train_design.shape[0]),
                    label=f"{model_id}/{fold_id} fitted TRAIN log-variance",
                )
                holdout_fitted = _checked_matrix_vector_product(
                    holdout_design,
                    coefficients,
                    expected_rows=int(holdout_design.shape[0]),
                    label=f"{model_id}/{fold_id} holdout log-variance",
                )
                with _strict_numerics():
                    # The semantic elementwise region: the residual difference, the fold and
                    # model-local Duan exponential and the back-transform.
                    residuals = train_response - train_fitted
                    smear = duan_smearing_factor(residuals)
                    forecast = back_transform_log_variance(holdout_fitted, smear)
                smear = _positive_finite(
                    smear, field=f"{model_id}/{fold_id} Duan smearing factor"
                )
                forecast = _finite_float64_vector(
                    forecast,
                    expected_size=int(holdout_design.shape[0]),
                    label=f"{model_id}/{fold_id} holdout forecast",
                )
                if not np.all(forecast > 0.0):
                    raise _error(f"{model_id}/{fold_id} forecasts must be strictly positive")
            except Exception:
                budget.fail(permit, reason="fit_output_validation_failed")
                raise
            budget.record_validated_output(permit)
            forecasts[(model_id, fold_id)] = forecast
            singular_values = [
                float(value) for value in np.asarray(singular, dtype=np.float64)
            ]
            smallest = singular_values[-1]
            fits.append(
                {
                    "ordinal": ordinal,
                    "permit_name": permit_name,
                    "model_id": model_id,
                    "fold_id": fold_id,
                    "column_names": list(MODEL_COLUMNS[model_id]),
                    "coefficients": [float(value) for value in np.asarray(beta)],
                    "coefficient_dimension": dimension,
                    "coefficient_sha256": _coefficient_sha256(beta),
                    "rank": validated_rank,
                    "singular_values": singular_values,
                    "condition_number": (
                        None if smallest == 0.0 else singular_values[0] / smallest
                    ),
                    "duan_smearing_factor": float(smear),
                    "duan_scope": "FOLD_AND_MODEL_LOCAL_TRAIN_RESIDUALS_ONLY",
                    "forecast_floor_or_clipping_applied": False,
                    "train_row_count": int(train_design.shape[0]),
                    "holdout_row_count": int(holdout_design.shape[0]),
                    "numerical_identity": identity,
                }
            )
        budget.seal()

        base_model, har_model = MODEL_ORDER
        oof: dict[str, dict[str, object]] = {}
        fold_metrics: list[dict[str, object]] = []
        pooled_base_parts: list[np.ndarray] = []
        pooled_har_parts: list[np.ndarray] = []
        for fold_id in FOLD_ORDER:
            partition = structure.partitions[fold_id]
            holdout_rows = tuple(structure.rows[index] for index in partition.holdout_indices)
            actual = np.asarray([row.rv_fwd_60 for row in holdout_rows], dtype=np.float64)
            with _strict_numerics():
                # QLIKE ratios, logarithms and fold means raise every floating-point error.
                losses_base = qlike(actual, forecasts[(base_model, fold_id)])
                losses_har = qlike(actual, forecasts[(har_model, fold_id)])
                improvement = losses_base - losses_har
                fold_mean_base = float(losses_base.mean())
                fold_mean_har = float(losses_har.mean())
                fold_mean_improvement = float(improvement.mean())
            oof[fold_id] = {
                "session_ids": [row.session_id for row in holdout_rows],
                "session_dates": [_session_date(row) for row in holdout_rows],
                "improvement": [float(value) for value in improvement],
            }
            pooled_base_parts.append(losses_base)
            pooled_har_parts.append(losses_har)
            fold_metrics.append(
                {
                    "fold_id": fold_id,
                    "row_count": int(actual.size),
                    "session_count": len(partition.holdout_sessions),
                    "mean_qlike_base": fold_mean_base,
                    "mean_qlike_har": fold_mean_har,
                    "mean_improvement": fold_mean_improvement,
                    "weighting": "ROW_WEIGHTED_MEAN_OVER_FOLD_HOLDOUT_ROWS",
                }
            )
        with _strict_numerics():
            # Pooled out-of-fold aggregation and the relative reduction raise every error.
            pooled_base = np.concatenate(pooled_base_parts)
            pooled_har = np.concatenate(pooled_har_parts)
            pooled_improvement = pooled_base - pooled_har
            pooled_mean_base = float(pooled_base.mean())
            pooled_mean_har = float(pooled_har.mean())
            pooled_mean_improvement = float(pooled_improvement.mean())
            relative = relative_qlike_reduction(pooled_mean_base, pooled_mean_har)
        tables = _session_tables(oof)
        bootstrap: list[dict[str, object]] = []
        for block_length in BOOTSTRAP_BLOCK_ORDER:
            with _strict_numerics():
                # Every paired session-block replicate is drawn and reduced under raised errors.
                result = paired_session_block_bootstrap(
                    tables,
                    block_length=block_length,
                    repetitions=BOOTSTRAP_REPETITIONS,
                    master_seed=MASTER_SEED,
                )
            bootstrap.append(
                {
                    "block_length": result.block_length,
                    "repetitions": result.repetitions,
                    "master_seed": MASTER_SEED,
                    "pooled_seed": result.pooled_seed,
                    "fold_seeds": [[fold_id, seed] for fold_id, seed in result.fold_seeds],
                    "draw_identity_sha256": result.draw_identity_sha256,
                    "percentile": result.percentile,
                    "lower_bound": result.lower_bound,
                    "role": (
                        "PRIMARY" if result.block_length == PRIMARY_BLOCK_LENGTH else "DIAGNOSTIC"
                    ),
                }
            )
        if [entry["block_length"] for entry in bootstrap] != list(BOOTSTRAP_BLOCK_ORDER):
            raise _error("the bootstrap block order is frozen at 5, 1 and 20")
        primary = next(
            entry for entry in bootstrap if entry["block_length"] == PRIMARY_BLOCK_LENGTH
        )
        twenty = next(entry for entry in bootstrap if entry["block_length"] == 20)
        sign_diagnostic = {
            "primary_block_length": PRIMARY_BLOCK_LENGTH,
            "primary_lower_bound_sign": _sign(float(primary["lower_bound"])),
            "twenty_session_lower_bound_sign": _sign(float(twenty["lower_bound"])),
            "sign_changed": _sign(float(twenty["lower_bound"]))
            != _sign(float(primary["lower_bound"])),
            "effect": "MANDATORY_DISCLOSURE_ONLY_NOT_A_GATE",
        }
        decision = decide_continuation(
            ContinuationInputs(
                assertions_passed=True,
                fold_mean_improvements=tuple(
                    (str(entry["fold_id"]), float(entry["mean_improvement"]))
                    for entry in fold_metrics
                ),
                pooled_mean_qlike_base=pooled_mean_base,
                pooled_mean_qlike_har=pooled_mean_har,
                primary_lower_bound=float(primary["lower_bound"]),
                real_fold_fit_calls=len(fits),
                underpowered=False,
            )
        )
        pooled_rows = int(pooled_base.size)
        counters = {
            "permits_created": len(list(state["permits_created"])),
            "permits_consumed": budget.permits_consumed,
            "real_fold_fit_calls": len(fits),
            "real_models_fitted": len(MODEL_ORDER),
            "real_coefficients_computed": len(fits),
            "duan_factors_computed": len(fits),
            "real_forecasts_computed": pooled_rows * len(MODEL_ORDER),
            "real_qlike_evaluations": pooled_rows * len(MODEL_ORDER),
            "real_bootstrap_replicates": BOOTSTRAP_REPETITIONS * len(bootstrap),
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        }
        expected_counters = {
            "permits_created": FIT_PERMIT_BUDGET,
            "permits_consumed": FIT_PERMIT_BUDGET,
            "real_fold_fit_calls": FIT_PERMIT_BUDGET,
            "real_models_fitted": 2,
            "real_coefficients_computed": FIT_PERMIT_BUDGET,
            "duan_factors_computed": FIT_PERMIT_BUDGET,
            "real_bootstrap_replicates": EXPECTED_BOOTSTRAP_REPLICATES,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        }
        for name, expected in expected_counters.items():
            if counters[name] != expected:
                raise _error(f"counter {name} is not the frozen value {expected}")
        if counters["real_forecasts_computed"] != counters["real_qlike_evaluations"]:
            raise _error("forecast and QLIKE counts must agree with the pooled out-of-fold rows")
        write_terminal(
            state,
            disposition=decision.disposition.value,
            reasons=tuple(decision.failures),
            source_binding=source_binding,
            permits={
                "names": list(state["permit_names"]),
                "created": len(list(state["permits_created"])),
                "consumed": budget.permits_consumed,
                "callback_starts": budget.callback_starts,
                "validated_outputs": budget.validated_outputs,
                "refused_requests": budget.refused_requests,
                "poisoned": budget.poisoned,
                "sealed": budget.sealed,
                "unreplenished": True,
            },
            fits=fits,
            metrics={
                "dependence": dict(structure.dependence),
                "folds": fold_metrics,
                "pooled": {
                    "row_count": pooled_rows,
                    "mean_qlike_base": pooled_mean_base,
                    "mean_qlike_har": pooled_mean_har,
                    "mean_improvement": pooled_mean_improvement,
                    "relative_qlike_reduction": relative,
                },
                "sessions": [
                    {
                        "fold_id": aggregate.fold_id,
                        "session_id": aggregate.session_id,
                        "session_date": aggregate.session_date.isoformat(),
                        "row_count": aggregate.row_count,
                        "improvement_sum": aggregate.improvement_sum,
                    }
                    for fold_id in FOLD_ORDER
                    for aggregate in tables[fold_id]
                ],
            },
            bootstrap=bootstrap,
            sign_diagnostic=sign_diagnostic,
            gates={
                "fold_mean_improvement_strictly_positive": {
                    str(entry["fold_id"]): float(entry["mean_improvement"]) > 0.0
                    for entry in fold_metrics
                },
                "relative_qlike_reduction": relative,
                "relative_qlike_reduction_floor": RELATIVE_QLIKE_REDUCTION_FLOOR,
                "relative_qlike_reduction_passes": relative >= RELATIVE_QLIKE_REDUCTION_FLOOR,
                "primary_lower_bound": float(primary["lower_bound"]),
                "primary_lower_bound_strictly_positive": float(primary["lower_bound"]) > 0.0,
                "four_and_only_four_real_fits": len(fits) == FIT_PERMIT_BUDGET,
                "equality_policy": (
                    "FOLD_AND_PRIMARY_BOUND_EQUALITY_FAILS_RELATIVE_REDUCTION_EQUALITY_PASSES"
                ),
            },
            counters=counters,
        )

    def run_real_pipeline(
        rows: tuple[OneShotEligibleRow, ...],
        state: dict[str, object],
    ) -> None:
        """Run the whole real numerical pipeline behind the durable reservation.

        The structural prefit runs first and, if it fails, stops with ``UNDERPOWERED_STOP``
        before any permit exists and before any decomposition or fit.  Otherwise each ordered
        durable permit is published before its own internal ``numpy.linalg.lstsq`` call, and any
        later defect writes exactly one ``INVALID_EVIDENCE`` terminal without retry.
        """

        if state["terminal_attempted"]:
            _stop("the one-shot terminal has already been attempted; there is no retry")
        source_binding = dict(state.get("source_binding") or {})
        try:
            structure = _prefit_structure(rows)
        except Exception as exc:
            # Precedence: a structural or undefined-ACF prefit failure is UNDERPOWERED_STOP with
            # zero permits and zero fits; any other prefit defect is INVALID_EVIDENCE. Either
            # way exactly one terminal is attempted and nothing is retried.
            write_terminal(
                state,
                disposition=(
                    TerminalDisposition.UNDERPOWERED.value
                    if isinstance(exc, Test3G3FUnderpoweredStop)
                    else TerminalDisposition.INVALID.value
                ),
                reasons=(f"{type(exc).__name__}: {exc}",),
                source_binding=source_binding,
                permits={
                    "names": list(state["permit_names"]),
                    "created": 0,
                    "consumed": 0,
                    "callback_starts": 0,
                    "validated_outputs": 0,
                    "refused_requests": 0,
                    "poisoned": False,
                    "sealed": False,
                },
                fits=[],
                metrics=None,
                bootstrap=[],
                sign_diagnostic=None,
                gates=None,
                counters=stop_counters(None),
            )
            raise
        budget = OneShotFitPermitBudget()
        try:
            complete_real_execution(structure, state, budget, source_binding)
        except Exception as exc:
            if not state["terminal_attempted"]:
                counters = stop_counters(budget)
                counters["permits_created"] = len(list(state["permits_created"]))
                counters["permits_consumed"] = budget.permits_consumed
                write_terminal(
                    state,
                    disposition=TerminalDisposition.INVALID.value,
                    reasons=(f"{type(exc).__name__}: {exc}",),
                    source_binding=source_binding,
                    permits={
                        "names": list(state["permit_names"]),
                        "created": len(list(state["permits_created"])),
                        "consumed": budget.permits_consumed,
                        "callback_starts": budget.callback_starts,
                        "validated_outputs": budget.validated_outputs,
                        "refused_requests": budget.refused_requests,
                        "poisoned": budget.poisoned,
                        "sealed": budget.sealed,
                    },
                    fits=[],
                    metrics=None,
                    bootstrap=[],
                    sign_diagnostic=None,
                    gates=None,
                    counters=counters,
                )
            raise

    def execution_authority_report(authority: object) -> Mapping[str, object]:
        """Return the closed, row-free terminal summary; no eligible row ever leaves here."""

        state = resolve_authority(authority)
        report = state["report"]
        if report is None:
            _stop("no terminal record has been written for this execution authority")
        return dict(report)

    def close_execution_authority(authority: object) -> Mapping[str, object]:
        """Close descriptors and release live references; never delete or mutate a record."""

        state = resolve_authority(authority)
        state["released"] = True
        state["closed"] = True
        state["source_binding"] = None
        return cleanup_observation(state)

    def bind_source_evidence(
        authority: object,
        source_binding: Mapping[str, object],
    ) -> None:
        """Record the predecessor source/G3-P binding that the terminal must carry."""

        state = resolve_authority(authority)
        if state["terminal_attempted"]:
            _stop("the source binding cannot change after the terminal was attempted")
        state["source_binding"] = _assert_json_closed(source_binding, field="source_binding")

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
            "execution_authority_armed": bool(authority_state["armed"]),
            "execution_authority_open": authority_state["issued"] is not None,
            "reservations_created": sum(
                1
                for value in authority_registry.values()
                if _is_sha256(value.get("reservation_sha256"))
            ),
            "permits_created": sum(
                len(list(value["permits_created"])) for value in authority_registry.values()
            ),
            "terminals_written": sum(
                1 for value in authority_registry.values() if value["terminal_written"]
            ),
            "validation_status": VALIDATION_STATUS,
            "final_test_status": FINAL_TEST_STATUS,
        }

    return (
        module_marker,
        load_owner_activation_capability,
        accept_and_consume_activation,
        claim_g3p_delivery_handle,
        local_state_report,
        open_execution_authority,
        assert_execution_authority_reserved,
        bind_source_evidence,
        record_terminal_stop,
        execution_authority_report,
        close_execution_authority,
    )


#: Opaque per-import identity marker.  It is an identity check for the G3-P delivery binding,
#: never a credential, and it proves nothing about Owner intent.
(
    _MODULE_INSTANCE_MARKER,
    load_owner_activation_capability,
    _accept_and_consume_activation,
    _claim_g3p_delivery_handle,
    _local_state_report,
    open_execution_authority,
    assert_execution_authority_reserved,
    bind_source_evidence,
    record_terminal_stop,
    execution_authority_report,
    close_execution_authority,
) = _build_closed_activation_and_handoff_state_machine()

del _build_closed_activation_and_handoff_state_machine


FitCallback = Callable[[np.ndarray, np.ndarray], object]


def run_one_shot_fits(
    rows: Iterable[OneShotEligibleRow],
    *,
    mode: ExecutionMode,
    fit_callback: FitCallback | None = None,
    activation: object | None = None,
    budget: OneShotFitPermitBudget | None = None,
) -> OneShotFitReport:
    """Run the exact four ordered model/fold fits behind four unreplenished permits.

    This entrypoint is the inert synthetic structural rehearsal, and the injectable
    ``fit_callback`` exists only for it.  Real mode has no arbitrary fit callback at all: a real
    run is refused here after the activation is checked and must go through the
    activation-bound, reservation-backed recovery pipeline, which uses internal
    ``numpy.linalg.lstsq(..., rcond=None)`` only.

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
        _stop(
            "a real one-shot TRAIN run has no arbitrary fit callback; it runs only through the "
            "activation-bound reservation pipeline with internal numpy.linalg.lstsq(rcond=None)"
        )
    if activation is not None:
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

    # Only the inert mode can reach this point, so every real/scientific counter stays zero.
    counters = OneShotCounters(
        permits_consumed=active_budget.permits_consumed,
        fit_callback_starts=active_budget.callback_starts,
        fit_outputs_validated=active_budget.validated_outputs,
        refused_fit_requests=active_budget.refused_requests,
    )
    assert_zero_protected_counters(counters)

    return OneShotFitReport(
        module_id=ONE_SHOT_MODULE_ID,
        mode=mode,
        activation_state=ExecutionMode.PRE_ACTIVATION_INERT.value,
        evidence_naming=EVIDENCE_NAMING,
        pair_order=EXPECTED_PAIR_ORDER,
        fits=tuple(fits),
        partitions=partitions,
        counters=counters,
    )


__all__ = [
    "ACTIVATION_ENVELOPE_KEYS",
    "ACTIVATION_FILE_MAX_BYTES",
    "ACTIVATION_PAYLOAD_KEYS",
    "ALLOWED_IMPORT_ROOTS",
    "BOOTSTRAP_BLOCK_ORDER",
    "EVIDENCE_NAMING",
    "EXPECTED_BOOTSTRAP_REPLICATES",
    "EXPECTED_HANDOFF_ID",
    "EXPECTED_PAIR_ORDER",
    "FINAL_TEST_STATUS",
    "FIT_PERMIT_BUDGET",
    "FOLD_HOLDOUT_YEARS",
    "FOLD_ROLES",
    "FOLD_ROLE_ATTRIBUTES",
    "FORBIDDEN_HISTORICAL_IDENTITIES",
    "FORBIDDEN_IMPORT_PREFIXES",
    "MIN_BOUNDARY_GAP_MINUTES",
    "MIN_HOLDOUT_SESSIONS",
    "ONE_SHOT_MODULE_ID",
    "PERMIT_RECORD_KIND",
    "PROTECTED_COUNTER_FIELDS",
    "REQUIRED_ACF_LAGS",
    "RESERVATION_RECORD_KIND",
    "RESERVATION_STATUS",
    "REVIEWED_FILE_MAX_BYTES",
    "REVIEWED_IMPLEMENTATION_PATHS",
    "RUNTIME_EVIDENCE_KEYS",
    "TERMINAL_RECORD_KIND",
    "VALIDATION_STATUS",
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
    "Test3G3FUnderpoweredStop",
    "assert_execution_authority_reserved",
    "assert_zero_protected_counters",
    "bind_source_evidence",
    "build_design_matrix",
    "build_response_vector",
    "close_execution_authority",
    "describe_pre_activation_stop",
    "execution_authority_report",
    "load_owner_activation_capability",
    "open_execution_authority",
    "record_terminal_stop",
    "run_one_shot_fits",
]

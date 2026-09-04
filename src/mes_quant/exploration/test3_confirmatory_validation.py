"""Test 3 confirmatory-validation implementation V1 — pure, local and data-free.

Classification:
``IMPLEMENTATION_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION /
NOT_ACTIVATION``

Contract of record. The single contract realised here is the co-ratified pair

* ``docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md``
  ("Protocol V1"), and
* ``docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md``
  ("Signed Bootstrap Erratum V1"),

which Erratum Section 8 requires to be applied together and never apart. Nothing
in this module ratifies, activates or interprets that contract; the exact
ratified bytes control, and this module is only a mechanical realisation of them.

What this module contains, in Protocol order:

1. a closed-schema runtime-identity binder and exact comparator (Protocol V1
   Section 5.5 runtime binding);
2. exact feature-identity and common-eligible row-identity binding for BASE and
   HAR, so that no anonymous shape-only matrix can enter the deployment stage;
3. a complete pre-fit rank and identity gate that runs strictly **before** any
   ``numpy.linalg.lstsq`` call, before any fit permit and before any fit
   counter, as Protocol V1 Section 7.1 trigger group A requires;
4. pure ``float64`` BASE/HAR deployment math with the model-local Duan rule of
   Sections 0.1.4 item 2, 0.1.5 item 2 and 3.3;
5. QLIKE row losses and stored-order left-fold decision metrics exactly as
   Sections 5.1, 5.2, 5.3 and 5.5 items 1 to 3 prescribe, with every
   authoritative intermediate required to be finite;
6. the frozen Validation bootstrap over the exact ordered block lengths
   ``(5, 1, 20)`` with 2,000 replications each and the frozen seed schedule of
   Sections 5.4 and 5.5 items 4 and 5, with the Erratum Section 4 replicate rule
   that the denominator must be positive and finite while each stored replicate
   must be finite with sign unconstrained;
7. the integrity-before-support terminal classification of Sections 7, 7.1,
   7.1.1 and 7.2, including the exact within-session ACF algorithm whose session
   table is **derived** from the materialized rows and reconciled against any
   declared count, and the disclosure-only design effect and ESS;
8. pure ``C0``/``C0V`` readiness assessments that perform no input or output.
   ``C0V`` independently re-verifies both deployment seals but is always a
   pre-start procedural refusal because this implementation-only slice cannot
   mint or authenticate the separate Owner Grant 2; and
9. a fixed deterministic synthetic golden projection whose replay is compared
   **byte for byte against the ratified tooling-binding document bytes** rather
   than against a second copy of its own current output.

What this module is not. It performs no filesystem, network, provider, target,
evidence or data access of any kind; it imports nothing outside the Python
standard library and NumPy; it fits nothing on real data; it issues no
reservation, permit, activation, ``C0``, ``C0V`` or Validation-opening witness;
it opens no Validation and no Final Test; and it makes no scientific claim.
Every value it returns is derived from its caller's in-memory operands or from
its own closed-form synthetic constants. The ratified binding document is never
read by this module: its exact bytes are supplied by the caller and are then
verified against their own recorded canonical digest before any comparison.

No digest, commit, tree, blob or other identifier is written into this file by
hand. Every digest this module reports is recomputed at run time from exact
bytes.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from numbers import Integral, Real
from types import MappingProxyType
from typing import Any

import numpy

# --------------------------------------------------------------------------
# Frozen identity of this implementation slice
# --------------------------------------------------------------------------

MODULE_ID = "MES_TEST3_CONFIRMATORY_VALIDATION_IMPLEMENTATION_V1"
CLASSIFICATION = (
    "IMPLEMENTATION_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION / NOT_ACTIVATION"
)
DATA_POLICY = "DATA_FREE_NO_PROVIDER_TARGET_EVIDENCE_ACCESS"
NETWORK_POLICY = "LOCAL_ONLY_NO_NETWORK"

CONTRACT_DOCUMENTS_ORDERED: tuple[str, ...] = (
    "docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md",
    "docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md",
)
CONTRACT_RULE = "PROTOCOL_V1_AND_SIGNED_BOOTSTRAP_ERRATUM_V1_ARE_ONE_INSEPARABLE_CONTRACT"

IMPLEMENTATION_GUARANTEES: tuple[str, ...] = (
    "DATA_FREE",
    "NO_FILESYSTEM_IO",
    "NO_NETWORK",
    "NO_PROVIDER_ACCESS",
    "NO_TARGET_ACCESS",
    "NO_EVIDENCE_ACCESS",
    "NO_MODEL_IMPORT_FOR_REAL_DATA",
    "NO_ACTIVATION",
    "NO_C0_OR_C0V_AUTHORITY",
    "NO_RESERVATION_OR_PERMIT_ISSUANCE",
    "NO_VALIDATION_OPENING_WITNESS",
    "NO_FINAL_TEST_ACCESS",
    "NO_SCIENTIFIC_CLAIM",
)

# --------------------------------------------------------------------------
# Frozen scientific constants carried forward unchanged
# --------------------------------------------------------------------------

MODEL_ORDER: tuple[str, ...] = ("RVBASE001", "RVHAR001")
BASE_MODEL_ID = "RVBASE001"
HAR_MODEL_ID = "RVHAR001"
MODEL_COLUMNS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "RVBASE001": ("intercept", "X60", "SESSION_SIN", "SESSION_COS"),
        "RVHAR001": ("intercept", "X60", "X120", "X240", "SESSION_SIN", "SESSION_COS"),
    }
)

CONFIRMATORY_FIT_BUDGET_ID = "CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1"
CONFIRMATORY_FIT_BUDGET = 2

MASTER_SEED = 20260809
POOLED_SEED_OFFSET = 90_000
PARTITION_SEED_STEP = 1_000
VALIDATION_PARTITION_INDEX = 0
BOOTSTRAP_REPLICATIONS = 2_000
PRIMARY_BLOCK_LENGTH = 5
DIAGNOSTIC_BLOCK_LENGTHS: tuple[int, ...] = (1, 20)
BOOTSTRAP_BLOCK_LENGTHS_ORDERED: tuple[int, ...] = (
    PRIMARY_BLOCK_LENGTH,
    *DIAGNOSTIC_BLOCK_LENGTHS,
)
BOOTSTRAP_QUANTILE = 0.05
BOOTSTRAP_QUANTILE_METHOD = "linear"

RELATIVE_QLIKE_REDUCTION_FLOOR = 0.10
MINIMUM_VALIDATION_SESSIONS = 20

ACF_LAGS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8)
ACF_SPACING_MINUTES = 15
ACF_MINIMUM_PAIRS = 2
ACF_SUPPORT_UNDEFINED_REASON = "ACF_LAG_SUPPORT_UNDEFINED"
PURGE_GAP_MINUTES = 60

REPLICATE_SIGN_POLICY = (
    "DENOMINATOR_POSITIVE_AND_FINITE_REPLICATE_FINITE_WITH_SIGN_UNCONSTRAINED"
)
DUAN_BASIS = "MODEL_LOCAL_COMMON_ELIGIBLE_FULL_OUTER_TRAIN_RESIDUALS_OF_ONE_DEPLOYMENT_FIT"

# --------------------------------------------------------------------------
# Governed error surface
# --------------------------------------------------------------------------


class Test3ConfirmatoryValidationError(ValueError):
    """Raised when an operand violates the co-ratified confirmatory contract."""

    __test__ = False


def _fail(detail: str) -> Test3ConfirmatoryValidationError:
    return Test3ConfirmatoryValidationError(detail)


# --------------------------------------------------------------------------
# Deterministic serialization helpers (pure, in memory)
# --------------------------------------------------------------------------


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    raise _fail(f"unsupported serialization member type: {type(value).__name__}")


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize a payload deterministically: sorted keys, no spaces, no final LF."""

    text = json.dumps(
        _json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return text.encode("utf-8")


def governed_binding_canonical_bytes(payload: Any) -> bytes:
    """Reproduce the governed canonical form used by the ratified tooling binding.

    The ratified binding document was rendered by the reviewed prerequisite tool
    through the governed helper ``src/mes_quant/core/hashing.py``. That helper
    serializes with ``ensure_ascii=False``, sorted keys, compact separators and
    exactly one trailing newline. Reproducing that exact form here is what makes
    the golden comparison a byte-for-byte check of the ratified artifact rather
    than a paraphrase of it.
    """

    text = json.dumps(
        _json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Recompute a digest from exact bytes; no digest is ever supplied by hand."""

    if not isinstance(data, (bytes, bytearray)):
        raise _fail("digest input must be exact bytes")
    return hashlib.sha256(bytes(data)).hexdigest()


def float_hex(value: float) -> str:
    """Record a float without decimal rounding, so bitwise identity is preserved."""

    return float(value).hex()


# --------------------------------------------------------------------------
# Closed runtime-identity schema, binder and exact comparator
# --------------------------------------------------------------------------

FLOAT64_HEX_FIELDS_ORDERED: tuple[str, ...] = (
    "eps",
    "epsneg",
    "tiny",
    "max",
    "min",
    "resolution",
)
FLOAT64_INT_FIELDS_ORDERED: tuple[str, ...] = (
    "nmant",
    "nexp",
    "machep",
    "negep",
    "iexp",
    "maxexp",
    "minexp",
)
FLOAT_INFO_FLOAT_FIELDS_ORDERED: tuple[str, ...] = ("epsilon", "max", "min")
FLOAT_INFO_INT_FIELDS_ORDERED: tuple[str, ...] = (
    "dig",
    "mant_dig",
    "max_10_exp",
    "max_exp",
    "min_10_exp",
    "min_exp",
    "radix",
    "rounds",
)
REQUIRED_FLOAT_INFO_KEYS: frozenset[str] = frozenset(
    [f"{name}_hex" for name in FLOAT_INFO_FLOAT_FIELDS_ORDERED]
    + list(FLOAT_INFO_INT_FIELDS_ORDERED)
)

RUNTIME_IDENTITY_SCHEMA: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "python",
        (
            "implementation",
            "version",
            "version_full",
            "api_version",
            "hexversion",
            "cache_tag",
            "maxsize",
            "float_repr_style",
            "executable",
            "executable_resolved",
            "float_info",
        ),
    ),
    ("numpy", ("version", "build_config")),
    (
        "platform",
        ("system", "release", "version", "machine", "processor", "byteorder", "libc"),
    ),
    (
        "float64",
        (
            "dtype_str",
            "itemsize",
            "byteorder",
            *(f"{name}_hex" for name in FLOAT64_HEX_FIELDS_ORDERED),
            *FLOAT64_INT_FIELDS_ORDERED,
        ),
    ),
    (
        "rng",
        (
            "bit_generator_module",
            "bit_generator_class",
            "generator_class",
            "pcg64_module",
            "pcg64_class",
        ),
    ),
)

RUNTIME_IDENTITY_TEXT_FIELDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("python", "implementation"),
        ("python", "version"),
        ("python", "version_full"),
        ("python", "cache_tag"),
        ("python", "float_repr_style"),
        ("python", "executable"),
        ("python", "executable_resolved"),
        ("numpy", "version"),
        ("platform", "system"),
        ("platform", "release"),
        ("platform", "version"),
        ("platform", "machine"),
        ("platform", "processor"),
        ("platform", "byteorder"),
        ("float64", "dtype_str"),
        ("float64", "byteorder"),
        ("rng", "bit_generator_module"),
        ("rng", "bit_generator_class"),
        ("rng", "generator_class"),
        ("rng", "pcg64_module"),
        ("rng", "pcg64_class"),
    }
    | {("float64", f"{name}_hex") for name in FLOAT64_HEX_FIELDS_ORDERED}
)

RUNTIME_IDENTITY_INTEGER_FIELDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("python", "api_version"),
        ("python", "hexversion"),
        ("python", "maxsize"),
        ("float64", "itemsize"),
    }
    | {("float64", name) for name in FLOAT64_INT_FIELDS_ORDERED}
)

# Exactly one recorded text field may legitimately be empty: some platforms
# supply no processor string at all, and inventing one would be a false identity.
RUNTIME_IDENTITY_EMPTY_TEXT_ALLOWED: frozenset[tuple[str, str]] = frozenset(
    {("platform", "processor")}
)


def _float_info_defects(value: Any, *, label: str) -> list[str]:
    defects: list[str] = []
    if not isinstance(value, Mapping):
        return [f"{label}_FLOAT_INFO_IS_NOT_A_MAPPING"]
    if set(value) != REQUIRED_FLOAT_INFO_KEYS:
        return [f"{label}_FLOAT_INFO_FIELD_SET_IS_NOT_THE_CLOSED_SCHEMA"]
    for name in FLOAT_INFO_FLOAT_FIELDS_ORDERED:
        item = value[f"{name}_hex"]
        if not isinstance(item, str) or not item:
            defects.append(f"{label}_FLOAT_INFO_HEX_FIELD_IS_MALFORMED:{name}")
            continue
        try:
            float.fromhex(item)
        except ValueError:
            defects.append(f"{label}_FLOAT_INFO_HEX_FIELD_IS_NOT_A_FLOAT_LITERAL:{name}")
    for name in FLOAT_INFO_INT_FIELDS_ORDERED:
        item = value[name]
        if not isinstance(item, int) or isinstance(item, bool):
            defects.append(f"{label}_FLOAT_INFO_INTEGER_FIELD_IS_MALFORMED:{name}")
    return defects


def runtime_identity_defects(identity: Any, *, label: str) -> tuple[str, ...]:
    """Return the ordered closed-schema defects of one runtime identity.

    The schema is closed in both directions: a missing group or field and an
    undeclared group or field are equally nonconforming, so no recorded value can
    escape validation and no invented value can be accepted.
    """

    if not isinstance(identity, Mapping):
        return (f"{label}_IDENTITY_IS_NOT_A_MAPPING",)
    declared = {group for group, _fields in RUNTIME_IDENTITY_SCHEMA}
    if set(identity) != declared:
        return (f"{label}_IDENTITY_GROUP_SET_IS_NOT_THE_CLOSED_SCHEMA",)

    defects: list[str] = []
    for group, fields in RUNTIME_IDENTITY_SCHEMA:
        section = identity[group]
        if not isinstance(section, Mapping):
            defects.append(f"{label}_IDENTITY_GROUP_IS_NOT_A_MAPPING:{group}")
            continue
        if set(section) != set(fields):
            defects.append(f"{label}_IDENTITY_FIELD_SET_IS_NOT_THE_CLOSED_SCHEMA:{group}")
            continue
        for name in fields:
            value = section[name]
            key = (group, name)
            if key in RUNTIME_IDENTITY_TEXT_FIELDS:
                if not isinstance(value, str):
                    defects.append(f"{label}_IDENTITY_FIELD_IS_NOT_TEXT:{group}.{name}")
                elif not value and key not in RUNTIME_IDENTITY_EMPTY_TEXT_ALLOWED:
                    defects.append(f"{label}_IDENTITY_FIELD_IS_EMPTY:{group}.{name}")
                continue
            if key in RUNTIME_IDENTITY_INTEGER_FIELDS:
                if not isinstance(value, int) or isinstance(value, bool):
                    defects.append(f"{label}_IDENTITY_FIELD_IS_NOT_AN_INTEGER:{group}.{name}")
                continue
            if value is None or value == "" or value == [] or value == {}:
                defects.append(f"{label}_IDENTITY_FIELD_IS_ABSENT_OR_EMPTY:{group}.{name}")
    if not defects:
        libc = identity["platform"]["libc"]
        if not isinstance(libc, list) or not all(isinstance(item, str) for item in libc):
            defects.append(f"{label}_IDENTITY_PLATFORM_LIBC_IS_MALFORMED")
        build_config = identity["numpy"]["build_config"]
        if not isinstance(build_config, (Mapping, list)):
            defects.append(f"{label}_IDENTITY_NUMPY_BUILD_CONFIG_IS_NOT_STRUCTURED")
        defects.extend(_float_info_defects(identity["python"]["float_info"], label=label))
    return tuple(dict.fromkeys(defects))


def require_closed_runtime_identity(identity: Any, *, label: str = "RUNTIME") -> None:
    """Raise unless the supplied identity conforms exactly to the closed schema."""

    defects = runtime_identity_defects(identity, label=label)
    if defects:
        raise _fail(f"runtime identity is nonconforming: {defects[0]}")


@dataclass(frozen=True)
class RuntimeIdentityComparison:
    """The result of one exact runtime-identity comparison."""

    conforming: bool
    equal: bool
    defects: tuple[str, ...]
    first_difference: str | None
    sealed_sha256: str | None
    observed_sha256: str | None


def compare_runtime_identities(
    sealed: Any,
    observed: Any,
    *,
    sealed_label: str = "SEALED",
    observed_label: str = "OBSERVED",
) -> RuntimeIdentityComparison:
    """Compare two closed-schema identities by exact canonical bytes.

    Equality is byte equality of the canonical serialization. The first
    differing declared field is reported in schema order so a refusal can name a
    cause without weakening the exact-equality requirement.
    """

    defects = (
        *runtime_identity_defects(sealed, label=sealed_label),
        *runtime_identity_defects(observed, label=observed_label),
    )
    if defects:
        return RuntimeIdentityComparison(
            conforming=False,
            equal=False,
            defects=defects,
            first_difference=None,
            sealed_sha256=None,
            observed_sha256=None,
        )

    first_difference: str | None = None
    for group, fields in RUNTIME_IDENTITY_SCHEMA:
        for name in fields:
            left = canonical_json_bytes(sealed[group][name])
            right = canonical_json_bytes(observed[group][name])
            if left != right:
                first_difference = f"{group}.{name}"
                break
        if first_difference is not None:
            break

    sealed_bytes = canonical_json_bytes(sealed)
    observed_bytes = canonical_json_bytes(observed)
    return RuntimeIdentityComparison(
        conforming=True,
        equal=sealed_bytes == observed_bytes,
        defects=(),
        first_difference=first_difference,
        sealed_sha256=sha256_hex(sealed_bytes),
        observed_sha256=sha256_hex(observed_bytes),
    )


# --------------------------------------------------------------------------
# float64 operand discipline
# --------------------------------------------------------------------------


def _require_positive_integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) <= 0:
        raise _fail(f"{name} must be a positive integer")
    return int(value)


def require_float64_vector(array: Any, *, name: str) -> numpy.ndarray:
    """Require a one-dimensional, C-contiguous, finite ``float64`` vector."""

    if not isinstance(array, numpy.ndarray):
        raise _fail(f"{name} must be a numpy.ndarray")
    if array.dtype != numpy.dtype(numpy.float64):
        raise _fail(f"{name} must carry dtype float64")
    if array.ndim != 1 or array.size == 0:
        raise _fail(f"{name} must be a non-empty one-dimensional vector")
    if not array.flags["C_CONTIGUOUS"]:
        raise _fail(f"{name} must be C-contiguous")
    if not bool(numpy.all(numpy.isfinite(array))):
        raise _fail(f"{name} must be finite")
    return array


def require_float64_matrix(array: Any, *, name: str) -> numpy.ndarray:
    """Require a two-dimensional, C-contiguous, finite ``float64`` design matrix."""

    if not isinstance(array, numpy.ndarray):
        raise _fail(f"{name} must be a numpy.ndarray")
    if array.dtype != numpy.dtype(numpy.float64):
        raise _fail(f"{name} must carry dtype float64")
    if array.ndim != 2 or array.size == 0:
        raise _fail(f"{name} must be a non-empty two-dimensional matrix")
    if not array.flags["C_CONTIGUOUS"]:
        raise _fail(f"{name} must be C-contiguous")
    if not bool(numpy.all(numpy.isfinite(array))):
        raise _fail(f"{name} must be finite")
    return array


def left_fold(values: Any) -> numpy.float64:
    """Reduce in stored order with ``acc = numpy.float64(acc + value)``.

    Protocol V1 Section 5.5 item 2 prohibits parallel, BLAS, tree, pairwise,
    reordered and compensated summation, ``Decimal`` and higher precision, so
    this strict left fold is the only authoritative reduction.
    """

    accumulator = numpy.float64(0.0)
    for value in values:
        accumulator = numpy.float64(accumulator + value)
    return accumulator


def require_finite(value: Any, *, name: str) -> float:
    """Require one authoritative numerical intermediate to be finite."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise _fail(f"{name} must be a real number")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise _fail(f"{name} must be finite")
    return numeric


# --------------------------------------------------------------------------
# Exact feature identities and exact common-eligible row identities
# --------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class DeploymentDesign:
    """One model's ordered design, bound to exact feature and row identities.

    Protocol V1 Section 1 fixes the ordered design columns of ``RVBASE001`` and
    ``RVHAR001``, and Section 1 "Eligibility" requires BASE and HAR to be
    estimated and evaluated on exactly the same eligible rows. An anonymous
    shape-only matrix cannot express either requirement, so every design carries
    its exact ordered feature identities and its exact ordered common-eligible
    row identities and is checked against them.
    """

    model_id: str
    feature_names: tuple[str, ...]
    row_identities: tuple[str, ...]
    matrix: numpy.ndarray = field(repr=False)


@dataclass(frozen=True, eq=False)
class CommonEligibleTrainSample:
    """One shared common-eligible outer-TRAIN sample for both frozen models."""

    row_identities: tuple[str, ...]
    log_target: numpy.ndarray = field(repr=False)
    designs: tuple[DeploymentDesign, ...] = ()


def row_identity_defects(identities: Any, *, label: str) -> tuple[str, ...]:
    """Return the ordered defects of one exact row-identity sequence."""

    if isinstance(identities, (str, bytes)) or not isinstance(identities, Sequence):
        return (f"{label}_ROW_IDENTITIES_ARE_NOT_A_SEQUENCE",)
    values = tuple(identities)
    defects: list[str] = []
    if not values:
        defects.append(f"{label}_ROW_IDENTITIES_ARE_EMPTY")
    if not all(isinstance(item, str) and item for item in values):
        defects.append(f"{label}_ROW_IDENTITY_IS_NOT_A_NON_EMPTY_STRING")
    elif len(set(values)) != len(values):
        defects.append(f"{label}_ROW_IDENTITIES_ARE_NOT_UNIQUE")
    return tuple(dict.fromkeys(defects))


def row_identity_sha256(identities: Sequence[str]) -> str:
    """Recompute the exact ordered row-identity digest from bytes."""

    return sha256_hex(canonical_json_bytes(list(identities)))


def bind_deployment_design(
    model_id: str,
    feature_names: Sequence[str],
    row_identities: Sequence[str],
    matrix: numpy.ndarray,
) -> DeploymentDesign:
    """Bind one design to its exact ordered feature and row identities.

    This binder raises rather than returning defects: it is the constructor a
    conforming caller uses. The independent gate in
    :func:`precheck_deployment_designs` re-derives every one of these facts from
    the record itself, so a hand-built nonconforming record cannot slip past.
    """

    if model_id not in MODEL_ORDER:
        raise _fail(f"model_id must be one of {MODEL_ORDER}")
    names = tuple(feature_names)
    if names != MODEL_COLUMNS[model_id]:
        raise _fail(
            f"{model_id} feature identities and order must equal {MODEL_COLUMNS[model_id]}"
        )
    identities = tuple(row_identities)
    defects = row_identity_defects(identities, label=model_id)
    if defects:
        raise _fail(f"{model_id} row identities are nonconforming: {defects[0]}")
    bound = require_float64_matrix(matrix, name=f"{model_id} design")
    if bound.shape != (len(identities), len(names)):
        raise _fail(f"{model_id} design extent must equal its row and feature identities")
    return DeploymentDesign(
        model_id=model_id,
        feature_names=names,
        row_identities=identities,
        matrix=bound,
    )


def bind_common_eligible_train_sample(
    row_identities: Sequence[str],
    log_target: numpy.ndarray,
    designs: Sequence[DeploymentDesign],
) -> CommonEligibleTrainSample:
    """Bind one shared common-eligible sample for BASE and HAR, in that order."""

    identities = tuple(row_identities)
    defects = row_identity_defects(identities, label="COMMON_ELIGIBLE")
    if defects:
        raise _fail(f"common-eligible row identities are nonconforming: {defects[0]}")
    target = require_float64_vector(log_target, name="common-eligible log target")
    if int(target.shape[0]) != len(identities):
        raise _fail("the log target must carry exactly one value per common-eligible row")
    ordered = tuple(designs)
    if tuple(item.model_id for item in ordered) != MODEL_ORDER:
        raise _fail(f"designs must be supplied in the exact model order {MODEL_ORDER}")
    for design in ordered:
        if design.feature_names != MODEL_COLUMNS[design.model_id]:
            raise _fail(f"{design.model_id} feature identities or order are nonconforming")
        if design.row_identities != identities:
            raise _fail(
                f"{design.model_id} row identities must equal the shared common-eligible set"
            )
    return CommonEligibleTrainSample(
        row_identities=identities, log_target=target, designs=ordered
    )


# --------------------------------------------------------------------------
# Pre-fit rank and identity gate — strictly before any solve, permit or counter
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DesignPrecheck:
    """One model's pre-fit identity and rank observation, taken before any solve."""

    model_id: str
    feature_names: tuple[str, ...]
    row_count: int
    fitted_columns: int
    prefit_rank: int
    prefit_singular_values: tuple[float, ...]
    prefit_condition_number: float | None


@dataclass(frozen=True)
class DeploymentPrecheck:
    """The complete pre-fit gate for both models.

    ``may_fit`` is the only door to a solve. It is false whenever any exact
    identity check or any Protocol V1 Section 7.1 group A structural trigger
    fires, and it is evaluated for **both** models before a single
    ``numpy.linalg.lstsq`` call, a single permit, or a single fit counter.
    """

    row_count: int
    row_identity_sha256: str | None
    prechecks: tuple[DesignPrecheck, ...]
    identity_defects: tuple[str, ...]
    structural_triggers: tuple[str, ...]
    may_fit: bool


def _prefit_singular_values(matrix: numpy.ndarray) -> numpy.ndarray:
    return numpy.asarray(numpy.linalg.svd(matrix, compute_uv=False), dtype=numpy.float64)


def _prefit_rank(singular: numpy.ndarray, rows: int, columns: int) -> int:
    """Rank under the exact ``rcond=None`` convention used by ``lstsq``."""

    if singular.size == 0:
        return 0
    largest = numpy.float64(singular[0])
    tolerance = numpy.float64(
        largest * numpy.float64(max(rows, columns)) * numpy.finfo(numpy.float64).eps
    )
    return int(numpy.count_nonzero(singular > tolerance))


def precheck_deployment_designs(sample: Any) -> DeploymentPrecheck:
    """Re-derive every identity and rank fact before any solve may be reached.

    Nothing here consumes a permit, increments a fit counter or calls
    ``numpy.linalg.lstsq``. Exact-identity failures are integrity defects
    (Section 7.2 tier 1). Row-count and rank failures are the exhaustive Section
    7.1 group A structural triggers and are reported separately, because they
    must stop the stage with ``0/2`` permits consumed and zero fits performed.
    """

    if not isinstance(sample, CommonEligibleTrainSample):
        raise _fail("sample must be a CommonEligibleTrainSample record")

    identity: list[str] = []
    structural: list[str] = []
    identities = tuple(sample.row_identities)
    identity.extend(row_identity_defects(identities, label="COMMON_ELIGIBLE"))

    target = sample.log_target
    if not isinstance(target, numpy.ndarray) or target.dtype != numpy.dtype(numpy.float64):
        identity.append("COMMON_ELIGIBLE_LOG_TARGET_IS_NOT_A_FLOAT64_ARRAY")
    elif target.ndim != 1 or int(target.shape[0]) != len(identities):
        identity.append("COMMON_ELIGIBLE_LOG_TARGET_EXTENT_DOES_NOT_MATCH_ROW_IDENTITIES")
    elif not bool(numpy.all(numpy.isfinite(target))):
        identity.append("COMMON_ELIGIBLE_LOG_TARGET_IS_NOT_FINITE")

    designs = tuple(sample.designs)
    if tuple(getattr(item, "model_id", None) for item in designs) != MODEL_ORDER:
        identity.append("DESIGNS_ARE_NOT_EXACTLY_BASE_THEN_HAR_IN_DECLARED_ORDER")
        designs = ()

    prechecks: list[DesignPrecheck] = []
    for design in designs:
        model_id = design.model_id
        columns = MODEL_COLUMNS[model_id]
        if tuple(design.feature_names) != columns:
            identity.append(f"FEATURE_IDENTITIES_OR_ORDER_NONCONFORMING:{model_id}")
            continue
        if tuple(design.row_identities) != identities:
            identity.append(f"COMMON_ELIGIBLE_ROW_IDENTITIES_DIFFER_FROM_SHARED_SET:{model_id}")
            continue
        matrix = design.matrix
        if (
            not isinstance(matrix, numpy.ndarray)
            or matrix.dtype != numpy.dtype(numpy.float64)
            or matrix.ndim != 2
        ):
            identity.append(f"DESIGN_IS_NOT_A_TWO_DIMENSIONAL_FLOAT64_MATRIX:{model_id}")
            continue
        if not matrix.flags["C_CONTIGUOUS"]:
            identity.append(f"DESIGN_IS_NOT_C_CONTIGUOUS:{model_id}")
            continue
        if matrix.shape != (len(identities), len(columns)):
            identity.append(f"DESIGN_EXTENT_DOES_NOT_MATCH_BOUND_IDENTITIES:{model_id}")
            continue
        if not bool(numpy.all(numpy.isfinite(matrix))):
            identity.append(f"DESIGN_IS_NOT_FINITE:{model_id}")
            continue
        try:
            singular = _prefit_singular_values(matrix)
        except Exception:  # noqa: BLE001 - map every SVD failure to the closed pre-fit defect.
            identity.append(f"PREFIT_SINGULAR_VALUE_DECOMPOSITION_FAILED:{model_id}")
            continue
        if not bool(numpy.all(numpy.isfinite(singular))):
            identity.append(f"PREFIT_SINGULAR_VALUES_ARE_NOT_FINITE:{model_id}")
            continue
        rows = int(matrix.shape[0])
        fitted = len(columns)
        rank = _prefit_rank(singular, rows, fitted)
        smallest = float(singular[-1]) if singular.size else 0.0
        condition = float(singular[0] / singular[-1]) if smallest > 0.0 else None
        if condition is not None and not math.isfinite(condition):
            condition = None
        if rows <= fitted:
            structural.append(f"PREFIT_ROWS_NOT_GREATER_THAN_FITTED_COLUMNS:{model_id}")
        if rank < fitted:
            structural.append(f"PREFIT_DESIGN_RANK_DEFICIENT:{model_id}")
        prechecks.append(
            DesignPrecheck(
                model_id=model_id,
                feature_names=columns,
                row_count=rows,
                fitted_columns=fitted,
                prefit_rank=rank,
                prefit_singular_values=tuple(float(value) for value in singular),
                prefit_condition_number=condition,
            )
        )

    identity_defects = tuple(dict.fromkeys(identity))
    structural_triggers = tuple(dict.fromkeys(structural))
    complete = len(prechecks) == len(MODEL_ORDER)
    if not complete and not identity_defects:
        identity_defects = ("PREFIT_GATE_DID_NOT_COVER_BOTH_FROZEN_MODELS",)
    return DeploymentPrecheck(
        row_count=len(identities),
        row_identity_sha256=(
            row_identity_sha256(identities) if identities and not identity_defects else None
        ),
        prechecks=tuple(prechecks),
        identity_defects=identity_defects,
        structural_triggers=structural_triggers,
        may_fit=complete and not identity_defects and not structural_triggers,
    )


# --------------------------------------------------------------------------
# BASE / HAR deployment fits and model-local Duan
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DeploymentFit:
    """One sealed confirmatory deployment fit and its model-local Duan factor."""

    model_id: str
    columns: tuple[str, ...]
    row_identity_sha256: str
    coefficients: tuple[float, ...]
    coefficients_hex: tuple[str, ...]
    rank: int
    singular_values: tuple[float, ...]
    condition_number: float
    train_row_count: int
    duan_factor: float
    duan_factor_hex: str
    duan_basis: str = DUAN_BASIS


def deployment_forecast(fit: DeploymentFit, design: DeploymentDesign) -> numpy.ndarray:
    """Back-transform one model's log-variance prediction with its own Duan factor.

    The scoring design must carry that model's exact ordered feature identities;
    a shape-compatible matrix with different or reordered features is refused.
    """

    if not isinstance(fit, DeploymentFit) or not isinstance(design, DeploymentDesign):
        raise _fail("a sealed fit and a bound scoring design are required")
    if design.model_id != fit.model_id:
        raise _fail("the scoring design must belong to this exact model")
    if design.feature_names != fit.columns or fit.columns != MODEL_COLUMNS[fit.model_id]:
        raise _fail(f"{fit.model_id} scoring feature identities or order are nonconforming")
    matrix = require_float64_matrix(design.matrix, name=f"{fit.model_id} scoring design")
    if matrix.shape != (len(design.row_identities), len(fit.columns)):
        raise _fail(f"{fit.model_id} scoring design extent must equal its bound identities")
    coefficients = numpy.ascontiguousarray(fit.coefficients, dtype=numpy.float64)
    predicted = matrix @ coefficients
    if not bool(numpy.all(numpy.isfinite(predicted))):
        raise _fail(f"{fit.model_id} log-scale predictions must be finite")
    forecasts = numpy.ascontiguousarray(
        numpy.exp(predicted) * numpy.float64(fit.duan_factor), dtype=numpy.float64
    )
    if not bool(numpy.all(numpy.isfinite(forecasts))) or bool(numpy.any(forecasts <= 0.0)):
        raise _fail(f"{fit.model_id} forecasts must be positive and finite")
    return forecasts


# --------------------------------------------------------------------------
# Independent seal verification; Owner Grant 2 is intentionally unavailable
# --------------------------------------------------------------------------

SEAL_VERIFICATION_BASIS = "INDEPENDENTLY_RE_DERIVED_FROM_THE_SEALED_FIT_RECORDS"
SEPARATE_OWNER_GRANT_2_REFUSAL = "SEPARATE_OWNER_GRANT_2_NOT_AVAILABLE_IN_IMPLEMENTATION_SLICE"


def deployment_seal_digest(fits: Sequence[DeploymentFit]) -> str:
    """Recompute the exact seal digest from the sealed fit records themselves.

    The digest covers the model order, ordered feature identities, the exact
    bitwise coefficient and Duan records, the bound row-identity digest and the
    Duan basis. It is never supplied by a caller and never typed by hand.
    """

    payload = [
        {
            "model_id": fit.model_id,
            "columns": list(fit.columns),
            "coefficients_hex": list(fit.coefficients_hex),
            "duan_factor_hex": fit.duan_factor_hex,
            "duan_basis": fit.duan_basis,
            "row_identity_sha256": fit.row_identity_sha256,
            "train_row_count": fit.train_row_count,
            "rank": fit.rank,
        }
        for fit in fits
    ]
    return sha256_hex(canonical_json_bytes(payload))


@dataclass(frozen=True)
class DeploymentSealVerification:
    """The result of one independent verification of both deployment seals."""

    model_ids: tuple[str, ...]
    defects: tuple[str, ...]
    seals_verified: int
    seal_digest: str | None
    verified: bool
    basis: str = SEAL_VERIFICATION_BASIS


def verify_deployment_seals(fits: Sequence[DeploymentFit]) -> DeploymentSealVerification:
    """Independently verify both seals from the sealed fit records themselves.

    Protocol V1 Section 3.3 requires both model artifacts to be sealed and
    verifiable before any Validation access. Verification here re-derives every
    checked fact from the records; it never accepts a caller's assertion that a
    seal verified.
    """

    ordered = tuple(fits)
    if not all(isinstance(item, DeploymentFit) for item in ordered):
        return DeploymentSealVerification(
            model_ids=(),
            defects=("SEALED_RECORDS_ARE_NOT_DEPLOYMENT_FITS",),
            seals_verified=0,
            seal_digest=None,
            verified=False,
        )
    model_ids = tuple(fit.model_id for fit in ordered)
    if model_ids != MODEL_ORDER:
        return DeploymentSealVerification(
            model_ids=model_ids,
            defects=("SEALED_MODEL_SET_IS_NOT_EXACTLY_BASE_THEN_HAR",),
            seals_verified=0,
            seal_digest=None,
            verified=False,
        )

    defects: list[str] = []
    for fit in ordered:
        columns = MODEL_COLUMNS[fit.model_id]
        if fit.columns != columns:
            defects.append(f"SEAL_COLUMNS_NONCONFORMING:{fit.model_id}")
        if len(fit.coefficients) != len(columns) or len(fit.coefficients_hex) != len(columns):
            defects.append(f"SEAL_COEFFICIENT_EXTENT_NONCONFORMING:{fit.model_id}")
        if not all(math.isfinite(value) for value in fit.coefficients):
            defects.append(f"SEAL_COEFFICIENTS_NONFINITE:{fit.model_id}")
        if len(fit.coefficients) == len(fit.coefficients_hex) and any(
            float_hex(value) != recorded
            for value, recorded in zip(fit.coefficients, fit.coefficients_hex, strict=False)
        ):
            defects.append(f"SEAL_COEFFICIENT_HEX_RECORD_DOES_NOT_RECONCILE:{fit.model_id}")
        if not math.isfinite(fit.duan_factor) or fit.duan_factor <= 0.0:
            defects.append(f"SEAL_DUAN_FACTOR_NOT_POSITIVE_AND_FINITE:{fit.model_id}")
        elif float_hex(fit.duan_factor) != fit.duan_factor_hex:
            defects.append(f"SEAL_DUAN_FACTOR_HEX_RECORD_DOES_NOT_RECONCILE:{fit.model_id}")
        if fit.duan_basis != DUAN_BASIS:
            defects.append(f"SEAL_DUAN_BASIS_NONCONFORMING:{fit.model_id}")
        if fit.rank != len(columns):
            defects.append(f"SEAL_RANK_IS_NOT_FULL_COLUMN_RANK:{fit.model_id}")
        if fit.train_row_count <= len(columns):
            defects.append(f"SEAL_TRAIN_ROWS_NOT_GREATER_THAN_FITTED_COLUMNS:{fit.model_id}")
        if not isinstance(fit.row_identity_sha256, str) or len(fit.row_identity_sha256) != 64:
            defects.append(f"SEAL_ROW_IDENTITY_DIGEST_IS_MALFORMED:{fit.model_id}")

    identity_digests = {fit.row_identity_sha256 for fit in ordered}
    if len(identity_digests) != 1:
        defects.append("SEALED_MODELS_WERE_NOT_ESTIMATED_ON_THE_SAME_ELIGIBLE_ROWS")
    duan_factors = {fit.duan_factor_hex for fit in ordered}
    if len(duan_factors) != len(ordered):
        defects.append("SEALED_DUAN_FACTORS_ARE_NOT_MODEL_LOCAL")

    ordered_defects = tuple(dict.fromkeys(defects))
    verified = not ordered_defects
    return DeploymentSealVerification(
        model_ids=model_ids,
        defects=ordered_defects,
        seals_verified=len(ordered) if verified else 0,
        seal_digest=deployment_seal_digest(ordered) if verified else None,
        verified=verified,
    )


@dataclass(frozen=True)
class DeploymentFitLedger:
    """Truthful permit-at-attempt accounting for the two ordered deployment fits."""

    budget_id: str
    permit_budget: int
    permits_consumed: int
    fits_attempted: int
    fits_succeeded: int
    fits_ordered: tuple[DeploymentFit, ...]
    seals_verified: int
    precheck: DeploymentPrecheck
    seal_verification: DeploymentSealVerification | None
    integrity_defects: tuple[str, ...]
    structural_triggers: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    terminal_class: TerminalClass | None
    validation_state: str


def run_ordered_deployment_fits(sample: Any) -> DeploymentFitLedger:
    """Run the pre-fit gate first, then at most two fits, BASE first then HAR.

    Order of operations is the control. The complete identity and rank gate for
    **both** models runs before any permit is consumed, before any fit counter
    moves and before ``numpy.linalg.lstsq`` is reachable at all. A group A stop
    therefore occurs with ``0/2`` permits consumed and zero fits performed, and
    an exact-identity defect is integrity, never structural.

    Once the gate opens, each attempt consumes one permit from the distinct
    ``CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1`` 2/2 budget at attempt, not at
    success. A failed fit consumes its permit, terminates the stage at
    ``INVALID_EVIDENCE`` with Validation unopened, and is never replaced: there
    is no third fit, no repair fit, no re-fit and no retry.
    """

    precheck = precheck_deployment_designs(sample)
    if precheck.identity_defects:
        return DeploymentFitLedger(
            budget_id=CONFIRMATORY_FIT_BUDGET_ID,
            permit_budget=CONFIRMATORY_FIT_BUDGET,
            permits_consumed=0,
            fits_attempted=0,
            fits_succeeded=0,
            fits_ordered=(),
            seals_verified=0,
            precheck=precheck,
            seal_verification=None,
            integrity_defects=precheck.identity_defects,
            structural_triggers=(),
            failure_reasons=precheck.identity_defects,
            terminal_class=TerminalClass.INVALID_EVIDENCE,
            validation_state="UNOPENED",
        )
    if precheck.structural_triggers:
        return DeploymentFitLedger(
            budget_id=CONFIRMATORY_FIT_BUDGET_ID,
            permit_budget=CONFIRMATORY_FIT_BUDGET,
            permits_consumed=0,
            fits_attempted=0,
            fits_succeeded=0,
            fits_ordered=(),
            seals_verified=0,
            precheck=precheck,
            seal_verification=None,
            integrity_defects=(),
            structural_triggers=precheck.structural_triggers,
            failure_reasons=precheck.structural_triggers,
            terminal_class=TerminalClass.UNDERPOWERED_STOP,
            validation_state="UNOPENED",
        )

    def solve_admitted_model(
        design: DeploymentDesign,
        observation: DesignPrecheck,
    ) -> DeploymentFit:
        """Solve one model only inside the already-admitted two-model stage.

        This lexical helper deliberately has no module-level callable surface.
        The complete identity/rank gate above has admitted both frozen models,
        and the caller increments permit-at-attempt accounting before entering
        this helper. There is consequently no public precheck-accepting solve
        bypass around :func:`run_ordered_deployment_fits`.
        """

        columns = MODEL_COLUMNS[design.model_id]
        if design.model_id != observation.model_id:
            raise _fail("the pre-fit observation must belong to this exact model")
        if design.feature_names != columns or observation.feature_names != columns:
            raise _fail(f"{design.model_id} feature identities or order are nonconforming")
        if tuple(design.row_identities) != tuple(sample.row_identities):
            raise _fail(f"{design.model_id} rows are not the admitted common-eligible rows")
        matrix = require_float64_matrix(design.matrix, name=f"{design.model_id} design")
        target = require_float64_vector(sample.log_target, name=f"{design.model_id} log target")
        if matrix.shape != (len(design.row_identities), len(columns)):
            raise _fail(f"{design.model_id} design extent must equal its bound identities")
        if int(target.shape[0]) != int(matrix.shape[0]):
            raise _fail(f"{design.model_id} design and log target must have equal row counts")
        if (
            observation.row_count != int(matrix.shape[0])
            or observation.fitted_columns != len(columns)
            or observation.prefit_rank != len(columns)
            or observation.row_count <= len(columns)
        ):
            raise _fail(f"{design.model_id} was not admitted by the pre-fit rank gate")

        solution, _residual_sum, rank, singular = numpy.linalg.lstsq(
            matrix, target, rcond=None
        )
        coefficients = numpy.ascontiguousarray(solution, dtype=numpy.float64)
        if coefficients.shape != (len(columns),):
            raise _fail(
                f"{design.model_id} coefficient vector does not match its ordered columns"
            )
        if not bool(numpy.all(numpy.isfinite(coefficients))):
            raise _fail(f"{design.model_id} coefficients must be finite")
        if int(rank) != observation.prefit_rank:
            raise _fail(f"{design.model_id} solved rank disagrees with the pre-fit rank gate")
        singular_values = numpy.asarray(singular, dtype=numpy.float64)
        if singular_values.size != len(columns) or not bool(
            numpy.all(numpy.isfinite(singular_values))
        ):
            raise _fail(f"{design.model_id} singular values must be complete and finite")
        if not bool(numpy.all(singular_values > 0.0)):
            raise _fail(f"{design.model_id} singular values must be strictly positive")
        condition_number = require_finite(
            float(singular_values[0] / singular_values[-1]),
            name=f"{design.model_id} condition number",
        )
        if condition_number <= 0.0:
            raise _fail(f"{design.model_id} condition number must be positive")

        residuals = target - matrix @ coefficients
        if not bool(numpy.all(numpy.isfinite(residuals))):
            raise _fail(f"{design.model_id} residuals must be finite")
        exponentiated = numpy.exp(residuals)
        if not bool(numpy.all(numpy.isfinite(exponentiated))):
            raise _fail(f"{design.model_id} exponentiated residuals must be finite")
        duan_factor = require_finite(
            float(numpy.mean(exponentiated)), name=f"{design.model_id} Duan factor"
        )
        if duan_factor <= 0.0:
            raise _fail(f"{design.model_id} Duan factor must be positive")

        return DeploymentFit(
            model_id=design.model_id,
            columns=columns,
            row_identity_sha256=row_identity_sha256(design.row_identities),
            coefficients=tuple(float(value) for value in coefficients),
            coefficients_hex=tuple(float_hex(value) for value in coefficients),
            rank=int(rank),
            singular_values=tuple(float(value) for value in singular_values),
            condition_number=condition_number,
            train_row_count=int(matrix.shape[0]),
            duan_factor=duan_factor,
            duan_factor_hex=float_hex(duan_factor),
        )

    observed = {item.model_id: item for item in precheck.prechecks}
    designs = {design.model_id: design for design in sample.designs}
    fits: list[DeploymentFit] = []
    failures: list[str] = []
    permits = 0
    attempted = 0
    for model_id in MODEL_ORDER:
        if permits >= CONFIRMATORY_FIT_BUDGET:
            failures.append("CONFIRMATORY_FIT_BUDGET_EXHAUSTED")
            break
        permits += 1
        attempted += 1
        try:
            fits.append(solve_admitted_model(designs[model_id], observed[model_id]))
        except Exception as error:  # noqa: BLE001 - every fit failure consumes its permit.
            # A failed or nonconvergent fit consumes its permit and may not be
            # replaced: every failure class terminates the stage identically.
            failures.append(f"DEPLOYMENT_FIT_FAILED:{model_id}:{type(error).__name__}")
            break

    verification: DeploymentSealVerification | None = None
    if not failures:
        verification = verify_deployment_seals(tuple(fits))
        failures.extend(verification.defects)
    ordered_failures = tuple(dict.fromkeys(failures))
    seals_verified = verification.seals_verified if verification is not None else 0
    return DeploymentFitLedger(
        budget_id=CONFIRMATORY_FIT_BUDGET_ID,
        permit_budget=CONFIRMATORY_FIT_BUDGET,
        permits_consumed=permits,
        fits_attempted=attempted,
        fits_succeeded=len(fits),
        fits_ordered=tuple(fits),
        seals_verified=seals_verified,
        precheck=precheck,
        seal_verification=verification,
        integrity_defects=ordered_failures,
        structural_triggers=(),
        failure_reasons=ordered_failures,
        terminal_class=TerminalClass.INVALID_EVIDENCE if ordered_failures else None,
        validation_state="UNOPENED",
    )


# --------------------------------------------------------------------------
# QLIKE row losses and stored-order decision metrics
# --------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class RowLosses:
    """The three authoritative per-row ``float64`` vectors, in stored row order."""

    row_count: int
    loss_base: numpy.ndarray = field(repr=False)
    loss_har: numpy.ndarray = field(repr=False)
    difference: numpy.ndarray = field(repr=False)


def compute_row_losses(
    actual: numpy.ndarray, forecast_base: numpy.ndarray, forecast_har: numpy.ndarray
) -> RowLosses:
    """Materialize the exact Section 5.5 item 1 ufunc sequence, in one order.

    ``d_i`` is BASE minus HAR, so a positive value favours ``RVHAR001``. Every
    input, intermediate and output is ``float64`` and every one of them is
    required to be finite before it is stored.
    """

    a = require_float64_vector(actual, name="actual variance")
    f_base = require_float64_vector(forecast_base, name="BASE forecast")
    f_har = require_float64_vector(forecast_har, name="HAR forecast")
    if not (a.shape == f_base.shape == f_har.shape):
        raise _fail("actual and both forecast vectors must have equal extent")
    for array, name in ((a, "actual variance"), (f_base, "BASE forecast"), (f_har, "HAR forecast")):
        if bool(numpy.any(array <= 0.0)):
            raise _fail(f"{name} must be strictly positive")

    with numpy.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        r_base = a / f_base
        loss_base = r_base - numpy.log(r_base) - numpy.float64(1.0)
        r_har = a / f_har
        loss_har = r_har - numpy.log(r_har) - numpy.float64(1.0)
        difference = loss_base - loss_har

    for array, name in (
        (r_base, "BASE loss ratio"),
        (r_har, "HAR loss ratio"),
        (loss_base, "BASE row loss"),
        (loss_har, "HAR row loss"),
        (difference, "row improvement"),
    ):
        if not bool(numpy.all(numpy.isfinite(array))):
            raise _fail(f"{name} must be finite")
    return RowLosses(
        row_count=int(a.shape[0]),
        loss_base=numpy.ascontiguousarray(loss_base),
        loss_har=numpy.ascontiguousarray(loss_har),
        difference=numpy.ascontiguousarray(difference),
    )


@dataclass(frozen=True)
class DecisionMetrics:
    """The equal-row-weighted decision statistics and their bitwise records."""

    row_count: int
    mean_base: float
    mean_har: float
    mean_difference: float
    relative_qlike_reduction: float | None
    mean_base_hex: str
    mean_har_hex: str
    mean_difference_hex: str
    relative_qlike_reduction_hex: str | None
    scored: bool
    undefined_reasons: tuple[str, ...]
    aggregation: str = "EQUAL_ROW_WEIGHTED_MEAN_OVER_COMMON_ELIGIBLE_ROWS"


def compute_decision_metrics(losses: RowLosses) -> DecisionMetrics:
    """Reduce each vector separately by stored-order left fold, then divide by ``N``.

    ``D`` is the direct reduction of ``d``; the mathematical identity
    ``D = M_BASE - M_HAR`` is deliberately not asserted bitwise. The relative
    reduction is exactly ``float64(float64(M_BASE - M_HAR) / M_BASE)``. Every
    aggregate weights each eligible row equally: mean-of-session-means and every
    other equal-session weighting are prohibited.

    Every authoritative intermediate is checked for finiteness: the three
    accumulators, ``M_BASE``, ``M_HAR``, ``D`` and the relative reduction. A
    nonfinite ``D`` makes the stage unscored; it is never silently carried into a
    gate comparison.
    """

    if not isinstance(losses, RowLosses):
        raise _fail("losses must be a RowLosses record")
    count = numpy.float64(losses.row_count)
    if not (numpy.isfinite(count) and count > numpy.float64(0.0)):
        raise _fail("the common-eligible row count must be positive and finite")

    accumulators = {
        "BASE_ROW_LOSS": left_fold(losses.loss_base),
        "HAR_ROW_LOSS": left_fold(losses.loss_har),
        "ROW_IMPROVEMENT": left_fold(losses.difference),
    }
    reasons: list[str] = []
    for name, accumulator in accumulators.items():
        if not numpy.isfinite(accumulator):
            reasons.append(f"{name}_ACCUMULATOR_NOT_FINITE")

    mean_base = numpy.float64(accumulators["BASE_ROW_LOSS"] / count)
    mean_har = numpy.float64(accumulators["HAR_ROW_LOSS"] / count)
    mean_difference = numpy.float64(accumulators["ROW_IMPROVEMENT"] / count)

    if not numpy.isfinite(mean_difference):
        reasons.append("MEAN_DIFFERENCE_D_NOT_FINITE")
    if not (numpy.isfinite(mean_base) and mean_base > numpy.float64(0.0)):
        reasons.append("MEAN_BASE_NOT_FINITE_AND_STRICTLY_POSITIVE")
    if not (numpy.isfinite(mean_har) and mean_har >= numpy.float64(0.0)):
        reasons.append("MEAN_HAR_NOT_FINITE_AND_NON_NEGATIVE")

    relative: numpy.float64 | None = None
    if not reasons:
        relative = numpy.float64(numpy.float64(mean_base - mean_har) / mean_base)
        if not numpy.isfinite(relative):
            reasons.append("RELATIVE_QLIKE_REDUCTION_NOT_FINITE")
            relative = None

    ordered_reasons = tuple(dict.fromkeys(reasons))
    return DecisionMetrics(
        row_count=losses.row_count,
        mean_base=float(mean_base),
        mean_har=float(mean_har),
        mean_difference=float(mean_difference),
        relative_qlike_reduction=None if relative is None else float(relative),
        mean_base_hex=float_hex(mean_base),
        mean_har_hex=float_hex(mean_har),
        mean_difference_hex=float_hex(mean_difference),
        relative_qlike_reduction_hex=None if relative is None else float_hex(relative),
        scored=not ordered_reasons,
        undefined_reasons=ordered_reasons,
    )


# --------------------------------------------------------------------------
# Session aggregates
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionAggregate:
    """One session's row count and stored-order improvement sum."""

    session_id: str
    row_count: int
    improvement_sum: float
    improvement_sum_hex: str


@dataclass(frozen=True, eq=False)
class SessionAggregates:
    """The strict chronological session table used by the frozen bootstrap."""

    sessions: tuple[SessionAggregate, ...]
    row_counts: numpy.ndarray = field(repr=False)
    improvement_sums: numpy.ndarray = field(repr=False)

    @property
    def session_count(self) -> int:
        return len(self.sessions)


def build_session_aggregates(
    session_ids: Sequence[str], difference: numpy.ndarray
) -> SessionAggregates:
    """Group stored rows by first chronological occurrence, preserving row order.

    Sessions must be contiguous and non-repeating: once a session's block of rows
    ends, that session identity may never reappear. A returning identity would
    mean the stored order is not the strict chronological session order the
    bootstrap assumes, so it is refused rather than silently merged.

    Each ``n_s`` is a positive integer and each ``S_s`` is the stored-order
    ``float64`` left fold over that session's ``d`` values.
    """

    values = require_float64_vector(difference, name="row improvement")
    identifiers = tuple(session_ids)
    if len(identifiers) != int(values.shape[0]):
        raise _fail("session identities and row improvements must have equal extent")

    ordered: list[tuple[str, list[numpy.float64]]] = []
    seen: set[str] = set()
    for identity, value in zip(identifiers, values, strict=True):
        if not isinstance(identity, str) or not identity:
            raise _fail("session identity must be a non-empty string")
        if ordered and ordered[-1][0] == identity:
            ordered[-1][1].append(value)
            continue
        if identity in seen:
            raise _fail(f"session rows must be contiguous and non-repeating: {identity}")
        seen.add(identity)
        ordered.append((identity, [value]))

    aggregates: list[SessionAggregate] = []
    sums: list[float] = []
    counts: list[int] = []
    for identity, session_values in ordered:
        total = left_fold(session_values)
        if not numpy.isfinite(total):
            raise _fail(f"session improvement sum must be finite: {identity}")
        aggregates.append(
            SessionAggregate(
                session_id=identity,
                row_count=len(session_values),
                improvement_sum=float(total),
                improvement_sum_hex=float_hex(total),
            )
        )
        sums.append(float(total))
        counts.append(len(session_values))

    return SessionAggregates(
        sessions=tuple(aggregates),
        row_counts=numpy.ascontiguousarray(counts, dtype=numpy.int64),
        improvement_sums=numpy.ascontiguousarray(sums, dtype=numpy.float64),
    )


# --------------------------------------------------------------------------
# Frozen Validation bootstrap
# --------------------------------------------------------------------------


def pooled_seed(block_length: int) -> int:
    """``pooled_seed = master_seed + 90000 + L``."""

    length = _require_positive_integer(block_length, name="block_length")
    return MASTER_SEED + POOLED_SEED_OFFSET + length


def validation_seed(block_length: int) -> int:
    """``validation_seed = pooled_seed + 1000``.

    Validation is the sole partition of this stage and sits at zero-based
    partition index ``0``, which is exactly why its offset is one ``1000`` step.
    """

    return pooled_seed(block_length) + PARTITION_SEED_STEP * (VALIDATION_PARTITION_INDEX + 1)


def build_draw_matrix(
    n_sessions: int, block_length: int, replications: int, seed: int
) -> numpy.ndarray:
    """Build one C-contiguous ``int32`` draw matrix exactly as Section 5.5 item 4.

    One fresh ``numpy.random.default_rng(seed)`` per block length; exactly one
    ``rng.integers`` call per replicate; non-circular expansion by
    ``numpy.arange``; concatenation in returned order; truncation to
    ``N_sessions``. Bulk generation, shared RNG state between block lengths,
    reseeding, skipping, redrawing and every other RNG call are prohibited.
    """

    sessions = _require_positive_integer(n_sessions, name="n_sessions")
    length = _require_positive_integer(block_length, name="block_length")
    repeats = _require_positive_integer(replications, name="replications")
    if isinstance(seed, bool) or not isinstance(seed, Integral) or int(seed) < 0:
        raise _fail("seed must be a non-negative integer")
    if sessions < length:
        raise _fail("n_sessions must be greater than or equal to the block length")

    blocks_needed = -(-sessions // length)
    generator = numpy.random.default_rng(int(seed))
    matrix = numpy.zeros((repeats, sessions), dtype=numpy.int32)
    for replicate in range(repeats):
        starts = generator.integers(
            low=0,
            high=sessions - length + 1,
            size=blocks_needed,
            dtype=numpy.int64,
            endpoint=False,
        )
        expanded = numpy.concatenate(
            [
                numpy.arange(int(start), int(start) + length, dtype=numpy.int32)
                for start in starts
            ]
        )
        matrix[replicate, :] = expanded[:sessions]
    return numpy.ascontiguousarray(matrix)


def compute_replicate_vector(
    improvement_sums: numpy.ndarray, row_counts: numpy.ndarray, draw_matrix: numpy.ndarray
) -> numpy.ndarray:
    """Reduce each replicate exactly as Section 5.5 item 5, as amended.

    Signed Bootstrap Erratum V1 Section 4 supersedes exactly one requirement:
    the denominator must be positive and finite, and each stored ``D_star[r]``
    must be finite with sign unconstrained. A replicate never becomes
    ``INVALID_EVIDENCE`` solely because of its sign.
    """

    sums = require_float64_vector(improvement_sums, name="session improvement sums")
    if not isinstance(row_counts, numpy.ndarray) or row_counts.dtype != numpy.dtype(numpy.int64):
        raise _fail("session row counts must be an int64 numpy.ndarray")
    if row_counts.shape != sums.shape:
        raise _fail("session row counts and improvement sums must have equal extent")
    if bool(numpy.any(row_counts <= 0)):
        raise _fail("every session row count must be a positive integer")
    if not isinstance(draw_matrix, numpy.ndarray) or draw_matrix.dtype != numpy.dtype(numpy.int32):
        raise _fail("draw matrix must be an int32 numpy.ndarray")
    if draw_matrix.ndim != 2 or draw_matrix.shape[1] != sums.shape[0]:
        raise _fail("draw matrix must carry exactly one column per session")
    if bool(numpy.any(draw_matrix < 0)) or bool(numpy.any(draw_matrix >= sums.shape[0])):
        raise _fail("draw matrix indices must address existing sessions")

    replicates = numpy.zeros(int(draw_matrix.shape[0]), dtype=numpy.float64)
    counts_as_float = row_counts.astype(numpy.float64)
    for index in range(int(draw_matrix.shape[0])):
        selected = draw_matrix[index]
        numerator = left_fold(sums[selected])
        denominator = left_fold(counts_as_float[selected])
        if not numpy.isfinite(numerator):
            raise _fail("replicate numerator must be finite")
        if not (numpy.isfinite(denominator) and denominator > numpy.float64(0.0)):
            raise _fail("replicate denominator must be positive and finite")
        value = numpy.float64(numerator / denominator)
        if not numpy.isfinite(value):
            raise _fail("each stored replicate must be finite")
        replicates[index] = value
    return numpy.ascontiguousarray(replicates)


@dataclass(frozen=True, eq=False)
class BootstrapBlockResult:
    """One block length's frozen bootstrap run and its one-sided lower bound."""

    block_length: int
    role: str
    validation_seed: int
    pooled_seed: int
    replications: int
    blocks_needed: int
    lower_bound: float
    lower_bound_hex: str
    negative_replicates: int
    zero_replicates: int
    positive_replicates: int
    draw_matrix: numpy.ndarray = field(repr=False)
    replicates: numpy.ndarray = field(repr=False)
    sign_policy: str = REPLICATE_SIGN_POLICY


def run_frozen_validation_bootstrap(
    aggregates: SessionAggregates,
) -> tuple[BootstrapBlockResult, ...]:
    """Run exactly three bootstraps, in the exact order ``(5, 1, 20)``.

    Block length 5 is the primary; 1 and 20 are diagnostics only and never
    override, replace, rescue or become the primary. There is no redraw, no
    reseed and no best-of-seeds.
    """

    if not isinstance(aggregates, SessionAggregates):
        raise _fail("aggregates must be a SessionAggregates record")
    sessions = aggregates.session_count
    if sessions <= 0:
        raise _fail("the session table must not be empty")

    results: list[BootstrapBlockResult] = []
    for block_length in BOOTSTRAP_BLOCK_LENGTHS_ORDERED:
        if sessions < block_length:
            raise _fail("N_sessions must be greater than or equal to every block length")
        seed = validation_seed(block_length)
        matrix = build_draw_matrix(sessions, block_length, BOOTSTRAP_REPLICATIONS, seed)
        replicates = compute_replicate_vector(
            aggregates.improvement_sums, aggregates.row_counts, matrix
        )
        bound = numpy.quantile(
            replicates, numpy.float64(BOOTSTRAP_QUANTILE), method=BOOTSTRAP_QUANTILE_METHOD
        )
        if not numpy.isfinite(bound):
            raise _fail("the bootstrap lower bound must be finite")
        results.append(
            BootstrapBlockResult(
                block_length=int(block_length),
                role="PRIMARY" if block_length == PRIMARY_BLOCK_LENGTH else "DIAGNOSTIC",
                validation_seed=seed,
                pooled_seed=pooled_seed(block_length),
                replications=BOOTSTRAP_REPLICATIONS,
                blocks_needed=-(-sessions // block_length),
                lower_bound=float(bound),
                lower_bound_hex=float_hex(bound),
                negative_replicates=int(numpy.count_nonzero(replicates < 0.0)),
                zero_replicates=int(numpy.count_nonzero(replicates == 0.0)),
                positive_replicates=int(numpy.count_nonzero(replicates > 0.0)),
                draw_matrix=matrix,
                replicates=replicates,
            )
        )
    return tuple(results)


def primary_block_result(
    results: Sequence[BootstrapBlockResult],
) -> BootstrapBlockResult:
    """Return the primary 5-session result; a diagnostic is never promoted."""

    if tuple(item.block_length for item in results) != BOOTSTRAP_BLOCK_LENGTHS_ORDERED:
        raise _fail(
            f"bootstrap results must follow the exact order {BOOTSTRAP_BLOCK_LENGTHS_ORDERED}"
        )
    primary = [item for item in results if item.role == "PRIMARY"]
    if len(primary) != 1 or primary[0].block_length != PRIMARY_BLOCK_LENGTH:
        raise _fail("exactly one primary 5-session result is required")
    return primary[0]


# --------------------------------------------------------------------------
# Exact within-session RV_FWD_60 ACF, with a derived session table
# --------------------------------------------------------------------------


def rho_null(lag: int) -> float:
    """``rho_null(k) = max(1 - k/4, 0)`` for ``k`` in ``1..8``."""

    if isinstance(lag, bool) or not isinstance(lag, Integral) or int(lag) not in ACF_LAGS:
        raise _fail("lag must be an integer in 1..8")
    return max(1.0 - int(lag) / 4.0, 0.0)


@dataclass(frozen=True)
class AcfRow:
    """One materialized common-eligible Validation row for the ACF."""

    session_id: str
    decision_time: datetime
    rv_fwd_60: float


@dataclass(frozen=True)
class AcfLagResult:
    """One lag's pooled pair count, correlation and disclosure values."""

    lag: int
    pair_count: int
    rho_observed: float | None
    rho_null: float
    excess: float | None
    support_reason: str | None


@dataclass(frozen=True)
class AcfAssessment:
    """The complete ACF assessment, separating integrity from structural support.

    ``session_ids_ordered``, ``session_row_counts`` and ``unique_session_count``
    are **derived** from the materialized rows themselves. They are the only
    session counts the group B minimum-session gate ever reads, so no independent
    caller scalar can satisfy that gate.
    """

    row_count: int
    session_ids_ordered: tuple[str, ...]
    session_row_counts: tuple[int, ...]
    lags: tuple[AcfLagResult, ...]
    integrity_defects: tuple[str, ...]
    support_undefined_lags: tuple[int, ...]
    design_effect: float | None
    effective_sample_size: float | None
    session_basis: str = "DERIVED_FROM_STRICTLY_CHRONOLOGICAL_CONTIGUOUS_NON_REPEATING_ROWS"
    disclosure: str = "DESIGN_EFFECT_AND_ESS_ARE_DISCLOSURE_ONLY_AND_NEVER_A_GATE"

    @property
    def unique_session_count(self) -> int:
        return len(self.session_ids_ordered)


def _empty_acf(row_count: int, defects: Sequence[str]) -> AcfAssessment:
    return AcfAssessment(
        row_count=row_count,
        session_ids_ordered=(),
        session_row_counts=(),
        lags=(),
        integrity_defects=tuple(dict.fromkeys(defects)),
        support_undefined_lags=(),
        design_effect=None,
        effective_sample_size=None,
    )


def assess_within_session_acf(rows: Sequence[AcfRow]) -> AcfAssessment:
    """Run the exact Section 7.1.1 algorithm; no fallback may be substituted.

    Materialization requires unique ``(session_id, decision_time)`` keys,
    timezone-aware timestamps, finite strictly positive ``RV_FWD_60`` values,
    strict chronological row order, and session blocks that are contiguous and
    non-repeating. The session table is then derived from those rows, so the
    session count reported here is an observation rather than a declaration.

    Missing support is recorded as an absent correlation with the non-numeric
    reason ``ACF_LAG_SUPPORT_UNDEFINED``. ``NaN``, infinity and sentinel numbers
    are never used to represent missing support, and a nonfinite correlation
    obtained after sufficient nonzero-spread support was present is an integrity
    defect rather than missing support.
    """

    materialized = tuple(rows)
    for row in materialized:
        if not isinstance(row, AcfRow):
            raise _fail("rows must contain AcfRow values")
    if not materialized:
        return _empty_acf(0, ("ACF_MATERIALIZATION_IS_EMPTY",))

    defects: list[str] = []
    grouped: list[tuple[str, list[AcfRow]]] = []
    started: set[str] = set()
    seen: set[tuple[str, datetime]] = set()
    previous: datetime | None = None
    for row in materialized:
        if not isinstance(row.session_id, str) or not row.session_id:
            defects.append("ACF_SESSION_IDENTITY_IS_EMPTY")
            continue
        moment = row.decision_time
        if (
            not isinstance(moment, datetime)
            or moment.tzinfo is None
            or moment.utcoffset() is None
        ):
            defects.append("ACF_DECISION_TIME_IS_NOT_TIMEZONE_AWARE")
            continue
        value = row.rv_fwd_60
        if isinstance(value, bool) or not isinstance(value, Real):
            defects.append("ACF_RV_FWD_60_IS_NOT_NUMERIC")
            continue
        numeric = float(value)
        if not math.isfinite(numeric):
            defects.append("ACF_RV_FWD_60_IS_NONFINITE")
        elif numeric <= 0.0:
            defects.append("ACF_RV_FWD_60_IS_NONPOSITIVE")
        key = (row.session_id, moment)
        if key in seen:
            defects.append("ACF_DUPLICATE_SESSION_DECISION_KEY")
        seen.add(key)
        if previous is not None and moment <= previous:
            defects.append("VALIDATION_ROWS_NOT_STRICTLY_CHRONOLOGICAL")
        previous = moment
        if grouped and grouped[-1][0] == row.session_id:
            grouped[-1][1].append(row)
            continue
        if row.session_id in started:
            defects.append("ACF_SESSION_ROWS_ARE_NOT_CONTIGUOUS_AND_NON_REPEATING")
            continue
        started.add(row.session_id)
        grouped.append((row.session_id, [row]))

    if defects:
        return _empty_acf(len(materialized), defects)

    session_ids = tuple(identity for identity, _rows in grouped)
    session_counts = tuple(len(session_rows) for _identity, session_rows in grouped)
    if sum(session_counts) != len(materialized):
        return _empty_acf(
            len(materialized), ("ACF_DERIVED_SESSION_TABLE_DOES_NOT_RECONCILE_WITH_ROWS",)
        )

    lags: list[AcfLagResult] = []
    undefined: list[int] = []
    positive_rhos: list[float] = []
    for lag in ACF_LAGS:
        expected = timedelta(minutes=ACF_SPACING_MINUTES * lag)
        current_values: list[float] = []
        prior_values: list[float] = []
        for _identity, session_rows in grouped:
            for index in range(lag, len(session_rows)):
                current = session_rows[index]
                prior = session_rows[index - lag]
                if current.decision_time - prior.decision_time != expected:
                    continue
                current_values.append(float(current.rv_fwd_60))
                prior_values.append(float(prior.rv_fwd_60))

        pair_count = len(current_values)
        null = rho_null(lag)
        if pair_count < ACF_MINIMUM_PAIRS:
            lags.append(
                AcfLagResult(lag, pair_count, None, null, None, ACF_SUPPORT_UNDEFINED_REASON)
            )
            undefined.append(lag)
            continue
        current_array = numpy.asarray(current_values, dtype=numpy.float64)
        prior_array = numpy.asarray(prior_values, dtype=numpy.float64)
        if (
            float(numpy.std(current_array, ddof=0)) == 0.0
            or float(numpy.std(prior_array, ddof=0)) == 0.0
        ):
            lags.append(
                AcfLagResult(lag, pair_count, None, null, None, ACF_SUPPORT_UNDEFINED_REASON)
            )
            undefined.append(lag)
            continue
        try:
            observed = float(numpy.corrcoef(current_array, prior_array)[0, 1])
        except Exception:  # noqa: BLE001 - map every correlation failure to a stable defect.
            defects.append(f"ACF_CORRELATION_RAISED_AT_LAG_{lag}")
            continue
        if not math.isfinite(observed):
            defects.append(f"ACF_CORRELATION_NONFINITE_AT_LAG_{lag}")
            continue
        lags.append(AcfLagResult(lag, pair_count, observed, null, observed - null, None))
        positive_rhos.append(max(observed, 0.0))

    if defects:
        return AcfAssessment(
            row_count=len(materialized),
            session_ids_ordered=session_ids,
            session_row_counts=session_counts,
            lags=tuple(lags),
            integrity_defects=tuple(dict.fromkeys(defects)),
            support_undefined_lags=tuple(undefined),
            design_effect=None,
            effective_sample_size=None,
        )

    design_effect: float | None = None
    effective: float | None = None
    if not undefined and len(lags) == len(ACF_LAGS):
        design_effect = max(1.0, 1.0 + 2.0 * sum(positive_rhos))
        effective = len(materialized) / design_effect
    return AcfAssessment(
        row_count=len(materialized),
        session_ids_ordered=session_ids,
        session_row_counts=session_counts,
        lags=tuple(lags),
        integrity_defects=(),
        support_undefined_lags=tuple(undefined),
        design_effect=design_effect,
        effective_sample_size=effective,
    )


# --------------------------------------------------------------------------
# Structural support, counters and terminal classification
# --------------------------------------------------------------------------


class TerminalClass(StrEnum):
    """The four scientific terminal classes; every one of them is no-retry."""

    CONFIRMED = "CONFIRMED_ON_OUTER_VALIDATION_FINAL_TEST_PROTOCOL_ELIGIBLE"
    NOT_CONFIRMED = "NOT_CONFIRMED_ON_OUTER_VALIDATION_TEST3_TERMINAL"
    UNDERPOWERED_STOP = "UNDERPOWERED_STOP"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


@dataclass(frozen=True)
class ValidationSupport:
    """Group B support, after the opening and ledgers but strictly before scoring.

    The gate reads ``derived_common_eligible_rows`` and
    ``derived_unique_sessions``, both taken from the ACF materialization. The
    declared values exist only to be reconciled: a declared count that does not
    equal the derived count is an integrity defect, never a way to satisfy the
    minimum-session gate.
    """

    acf: AcfAssessment
    declared_common_eligible_rows: int
    declared_unique_sessions: int
    derived_common_eligible_rows: int
    derived_unique_sessions: int
    reconciliation_defects: tuple[str, ...]
    basis: str = "GATES_READ_DERIVED_SESSION_COUNTS_ONLY_NEVER_A_CALLER_SCALAR"


def build_validation_support(
    acf: AcfAssessment,
    *,
    declared_common_eligible_rows: int,
    declared_unique_sessions: int,
) -> ValidationSupport:
    """Derive group B support from the ACF and reconcile every declared count."""

    if not isinstance(acf, AcfAssessment):
        raise _fail("acf must be an AcfAssessment record")
    for value, name in (
        (declared_common_eligible_rows, "declared_common_eligible_rows"),
        (declared_unique_sessions, "declared_unique_sessions"),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
            raise _fail(f"{name} must be a non-negative integer")

    derived_rows = int(acf.row_count)
    derived_sessions = int(acf.unique_session_count)
    defects: list[str] = []
    if int(declared_common_eligible_rows) != derived_rows:
        defects.append("DECLARED_COMMON_ELIGIBLE_ROW_COUNT_DOES_NOT_RECONCILE_WITH_DERIVED_ROWS")
    if int(declared_unique_sessions) != derived_sessions:
        defects.append("DECLARED_SESSION_COUNT_DOES_NOT_RECONCILE_WITH_DERIVED_SESSIONS")
    return ValidationSupport(
        acf=acf,
        declared_common_eligible_rows=int(declared_common_eligible_rows),
        declared_unique_sessions=int(declared_unique_sessions),
        derived_common_eligible_rows=derived_rows,
        derived_unique_sessions=derived_sessions,
        reconciliation_defects=tuple(dict.fromkeys(defects)),
    )


def validation_support_integrity_defects(support: ValidationSupport) -> tuple[str, ...]:
    """Return the tier 1 defects carried by one group B support record."""

    if not isinstance(support, ValidationSupport):
        raise _fail("support must be a ValidationSupport record")
    defects = [*support.acf.integrity_defects, *support.reconciliation_defects]
    if support.derived_common_eligible_rows != int(support.acf.row_count):
        defects.append("DERIVED_ROW_COUNT_DOES_NOT_MATCH_THE_ACF_MATERIALIZATION")
    if support.derived_unique_sessions != int(support.acf.unique_session_count):
        defects.append("DERIVED_SESSION_COUNT_DOES_NOT_MATCH_THE_ACF_MATERIALIZATION")
    return tuple(dict.fromkeys(defects))


def assess_validation_support(support: ValidationSupport) -> tuple[str, ...]:
    """Return the ordered group B triggers; an empty tuple means support holds.

    Every count used here is re-read from the ACF materialization, so a caller
    that declares twenty sessions over three real sessions fails both the
    reconciliation check and this gate.
    """

    if not isinstance(support, ValidationSupport):
        raise _fail("support must be a ValidationSupport record")
    rows = int(support.acf.row_count)
    sessions = int(support.acf.unique_session_count)
    triggers: list[str] = []
    if rows <= 0:
        triggers.append("VALIDATION_COMMON_ELIGIBLE_SET_IS_EMPTY")
    if sessions < MINIMUM_VALIDATION_SESSIONS:
        triggers.append("FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS")
    if support.acf.support_undefined_lags:
        triggers.append(ACF_SUPPORT_UNDEFINED_REASON)
    return tuple(dict.fromkeys(triggers))


@dataclass(frozen=True)
class ConfirmatoryCounters:
    """The exact counters that Section 6 criterion 4 requires to reconcile."""

    fits_attempted: int
    fits_succeeded: int
    permits_consumed: int
    seals_verified: int
    validation_openings: int
    validation_stage_train_requests: int = 0
    final_test_requests: int = 0
    final_test_reads: int = 0
    extra_accesses: int = 0
    final_test_state: str = "SEALED"


def reconcile_counters(counters: ConfirmatoryCounters) -> tuple[str, ...]:
    """Return the ordered counter, integrity and budget defects, if any."""

    if not isinstance(counters, ConfirmatoryCounters):
        raise _fail("counters must be a ConfirmatoryCounters record")
    defects: list[str] = []
    if counters.permits_consumed != counters.fits_attempted:
        defects.append("PERMITS_CONSUMED_DO_NOT_EQUAL_FIT_ATTEMPTS")
    if counters.fits_attempted != CONFIRMATORY_FIT_BUDGET:
        defects.append("FIT_ATTEMPTS_ARE_NOT_EXACTLY_TWO")
    if counters.fits_succeeded != CONFIRMATORY_FIT_BUDGET:
        defects.append("FIT_SUCCESSES_ARE_NOT_EXACTLY_TWO")
    if counters.permits_consumed > CONFIRMATORY_FIT_BUDGET:
        defects.append("CONFIRMATORY_FIT_BUDGET_EXCEEDED")
    if counters.seals_verified != len(MODEL_ORDER):
        defects.append("BOTH_MODEL_SEALS_ARE_NOT_VERIFIED")
    if counters.validation_openings != 1:
        defects.append("VALIDATION_OPENINGS_ARE_NOT_EXACTLY_ONE")
    if counters.validation_stage_train_requests != 0:
        defects.append("VALIDATION_STAGE_TRAIN_REQUEST_COUNT_IS_NONZERO")
    if counters.final_test_requests != 0:
        defects.append("FINAL_TEST_REQUEST_COUNT_IS_NONZERO")
    if counters.final_test_reads != 0:
        defects.append("FINAL_TEST_READ_COUNT_IS_NONZERO")
    if counters.extra_accesses != 0:
        defects.append("EXTRA_ACCESS_COUNT_IS_NONZERO")
    if counters.final_test_state != "SEALED":
        defects.append("FINAL_TEST_IS_NOT_SEALED")
    return tuple(dict.fromkeys(defects))


def assess_partition_integrity(
    *, max_train_label_end_time: datetime, min_validation_decision_time: datetime
) -> tuple[str, ...]:
    """Purge and boundary defects are always integrity, never group B.

    A non-strict TRAIN-label/Validation-decision boundary and a wall-clock gap
    below 60 minutes are ``INVALID_EVIDENCE`` regardless of when they are
    discovered.
    """

    for moment, name in (
        (max_train_label_end_time, "max_train_label_end_time"),
        (min_validation_decision_time, "min_validation_decision_time"),
    ):
        if (
            not isinstance(moment, datetime)
            or moment.tzinfo is None
            or moment.utcoffset() is None
        ):
            raise _fail(f"{name} must be a timezone-aware datetime")
    defects: list[str] = []
    if not max_train_label_end_time < min_validation_decision_time:
        defects.append("TRAIN_LABEL_END_NOT_STRICTLY_BEFORE_VALIDATION_DECISION")
    gap = min_validation_decision_time - max_train_label_end_time
    if gap < timedelta(minutes=PURGE_GAP_MINUTES):
        defects.append("VALIDATION_PURGE_GAP_BELOW_60_MINUTES")
    return tuple(dict.fromkeys(defects))


@dataclass(frozen=True)
class PassAssessment:
    """The four joint Section 6 PASS criteria and their asymmetric equality rule."""

    criteria: tuple[tuple[str, bool], ...]
    passed: bool
    failures: tuple[str, ...]


def evaluate_pass_criteria(
    metrics: DecisionMetrics,
    primary_lower_bound: float,
    counter_defects: Sequence[str] = (),
) -> PassAssessment:
    """Apply the four criteria jointly on the primary 5-session configuration.

    Equality fails criterion 1, equality fails criterion 3, and equality passes
    criterion 2. Criteria are never relaxed, reweighted or re-derived after
    seeing the result. ``D`` must be finite before it is compared at all.
    """

    if not isinstance(metrics, DecisionMetrics):
        raise _fail("metrics must be a DecisionMetrics record")
    if isinstance(primary_lower_bound, bool) or not isinstance(primary_lower_bound, Real):
        raise _fail("primary_lower_bound must be numeric")
    bound = require_finite(primary_lower_bound, name="primary_lower_bound")

    difference_finite = math.isfinite(metrics.mean_difference)
    mean_difference_positive = (
        metrics.scored and difference_finite and metrics.mean_difference > 0.0
    )
    relative = metrics.relative_qlike_reduction
    relative_meets_floor = (
        metrics.scored
        and relative is not None
        and math.isfinite(relative)
        and relative >= RELATIVE_QLIKE_REDUCTION_FLOOR
    )
    bound_positive = bound > 0.0
    counters_reconcile = not tuple(counter_defects)

    criteria = (
        ("D_STRICTLY_GREATER_THAN_ZERO", mean_difference_positive),
        ("RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10", relative_meets_floor),
        ("PRIMARY_LOWER_BOUND_STRICTLY_GREATER_THAN_ZERO", bound_positive),
        ("COUNTERS_INTEGRITY_AND_BUDGET_RECONCILE", counters_reconcile),
    )
    failures = tuple(name for name, satisfied in criteria if not satisfied)
    return PassAssessment(criteria=criteria, passed=not failures, failures=failures)


@dataclass(frozen=True)
class TerminalClassification:
    """One terminal class, its precedence tier and its ordered reasons."""

    terminal_class: TerminalClass
    tier: int
    reasons: tuple[str, ...]
    retry: str = "TERMINAL_NO_RETRY"


def classify_confirmatory_terminal(
    *,
    integrity_defects: Sequence[str] = (),
    deployment_precheck: DeploymentPrecheck | None = None,
    validation_support: ValidationSupport | None = None,
    pass_assessment: PassAssessment | None = None,
) -> TerminalClassification:
    """Apply the Section 7.2 precedence, integrity first and without exception.

    Tier 1 integrity always wins: if two descriptions could both appear to
    apply, the class is ``INVALID_EVIDENCE``. Tier 2 structural support is
    evaluated only after integrity passes, and no numerical failure and no
    implementation defect may enter it. Tier 3 scoring runs only after every
    structural gate has passed, and any failure after scoring has started is
    ``INVALID_EVIDENCE``.

    Group A triggers arrive as a :class:`DeploymentPrecheck`, which is the same
    record that gates the solve, so the class and the gate can never disagree.
    """

    integrity = list(dict.fromkeys(str(item) for item in integrity_defects))
    if deployment_precheck is not None:
        if not isinstance(deployment_precheck, DeploymentPrecheck):
            raise _fail("deployment_precheck must be a DeploymentPrecheck record")
        integrity.extend(deployment_precheck.identity_defects)
    if validation_support is not None:
        integrity.extend(validation_support_integrity_defects(validation_support))
    integrity = list(dict.fromkeys(integrity))
    if integrity:
        return TerminalClassification(TerminalClass.INVALID_EVIDENCE, 1, tuple(integrity))

    structural: list[str] = []
    if deployment_precheck is not None:
        structural.extend(deployment_precheck.structural_triggers)
    if validation_support is not None:
        structural.extend(assess_validation_support(validation_support))
    structural = list(dict.fromkeys(structural))
    if structural:
        return TerminalClassification(TerminalClass.UNDERPOWERED_STOP, 2, tuple(structural))

    if pass_assessment is None:
        return TerminalClassification(
            TerminalClass.INVALID_EVIDENCE, 1, ("SCORING_RESULT_IS_ABSENT",)
        )
    if not isinstance(pass_assessment, PassAssessment):
        raise _fail("pass_assessment must be a PassAssessment record")
    if pass_assessment.passed:
        return TerminalClassification(TerminalClass.CONFIRMED, 5, ())
    return TerminalClassification(
        TerminalClass.NOT_CONFIRMED, 4, tuple(pass_assessment.failures)
    )


# --------------------------------------------------------------------------
# Fixed deterministic synthetic golden projection
# --------------------------------------------------------------------------

GOLDEN_PROJECTION_ID = "MES_TEST3_CONFIRMATORY_GOLDEN_PROJECTION_V1"
GOLDEN_PROJECTION_SESSION_COUNT = 24
GOLDEN_PROJECTION_CONTENT = "SYNTHETIC_ONLY"
GOLDEN_PROJECTION_STORAGE = "IN_MEMORY_ONLY"


def golden_projection_session_row_counts() -> tuple[int, ...]:
    """The fixed synthetic session extents; no operand may vary them."""

    return tuple(4 + (index % 3) for index in range(GOLDEN_PROJECTION_SESSION_COUNT))


def golden_projection_inputs() -> tuple[
    tuple[str, ...], numpy.ndarray, numpy.ndarray, numpy.ndarray
]:
    """Build the closed-form synthetic operands; no data or provider is touched."""

    counts = golden_projection_session_row_counts()
    identifiers: list[str] = []
    for session, size in enumerate(counts):
        identifiers.extend([f"SYNTHETIC_SESSION_{session:02d}"] * size)
    total = sum(counts)
    index = numpy.arange(total, dtype=numpy.int64)
    actual = 1.0 + ((index * 7) % 13) / 16.0
    base = 1.0 + ((index * 5) % 11) / 16.0
    har = 1.0 + ((index * 3) % 17) / 32.0
    return (
        tuple(identifiers),
        numpy.ascontiguousarray(actual, dtype=numpy.float64),
        numpy.ascontiguousarray(base, dtype=numpy.float64),
        numpy.ascontiguousarray(har, dtype=numpy.float64),
    )


def build_golden_projection() -> tuple[dict[str, Any], bytes]:
    """Materialize the fixed projection once and return its record and raw bytes.

    The raw material is the exact concatenation of the C-order bytes of every
    authoritative array, in the same fixed order the reviewed prerequisite tool
    used when it produced the ratified golden fixture, so the two are directly
    comparable byte for byte.
    """

    identifiers, actual, base, har = golden_projection_inputs()
    losses = compute_row_losses(actual, base, har)
    metrics = compute_decision_metrics(losses)
    if not metrics.scored:
        raise _fail("the fixed golden projection must score")
    aggregates = build_session_aggregates(identifiers, losses.difference)
    if aggregates.session_count != GOLDEN_PROJECTION_SESSION_COUNT:
        raise _fail("the fixed golden projection session count is nonconforming")
    results = run_frozen_validation_bootstrap(aggregates)

    raw_parts = [
        actual.tobytes(order="C"),
        base.tobytes(order="C"),
        har.tobytes(order="C"),
        losses.loss_base.tobytes(order="C"),
        losses.loss_har.tobytes(order="C"),
        losses.difference.tobytes(order="C"),
        aggregates.row_counts.tobytes(order="C"),
        aggregates.improvement_sums.tobytes(order="C"),
    ]
    blocks: list[dict[str, Any]] = []
    for result in results:
        matrix = result.draw_matrix
        raw_parts.append(matrix.tobytes(order="C"))
        raw_parts.append(result.replicates.tobytes(order="C"))
        blocks.append(
            {
                "block_length": result.block_length,
                "role": result.role,
                "pooled_seed": result.pooled_seed,
                "validation_seed": result.validation_seed,
                "replications": result.replications,
                "blocks_needed": result.blocks_needed,
                "draw_matrix_sha256": sha256_hex(matrix.tobytes(order="C")),
                "replicate_vector_sha256": sha256_hex(result.replicates.tobytes(order="C")),
                "negative_replicates": result.negative_replicates,
                "zero_replicates": result.zero_replicates,
                "positive_replicates": result.positive_replicates,
                "lower_bound_hex": result.lower_bound_hex,
            }
        )

    raw = b"".join(raw_parts)
    record: dict[str, Any] = {
        "projection_id": GOLDEN_PROJECTION_ID,
        "content": GOLDEN_PROJECTION_CONTENT,
        "storage": GOLDEN_PROJECTION_STORAGE,
        "session_count": aggregates.session_count,
        "row_count": losses.row_count,
        "master_seed": MASTER_SEED,
        "block_lengths_ordered": list(BOOTSTRAP_BLOCK_LENGTHS_ORDERED),
        "replications": BOOTSTRAP_REPLICATIONS,
        "inputs_sha256": {
            "actual": sha256_hex(actual.tobytes(order="C")),
            "forecast_base": sha256_hex(base.tobytes(order="C")),
            "forecast_har": sha256_hex(har.tobytes(order="C")),
        },
        "row_losses_sha256": {
            "loss_base": sha256_hex(losses.loss_base.tobytes(order="C")),
            "loss_har": sha256_hex(losses.loss_har.tobytes(order="C")),
            "difference": sha256_hex(losses.difference.tobytes(order="C")),
        },
        "means_hex": {
            "mean_base": metrics.mean_base_hex,
            "mean_har": metrics.mean_har_hex,
            "mean_difference": metrics.mean_difference_hex,
            "relative_qlike_reduction": metrics.relative_qlike_reduction_hex,
        },
        "session_aggregates_sha256": {
            "row_counts": sha256_hex(aggregates.row_counts.tobytes(order="C")),
            "improvement_sums": sha256_hex(aggregates.improvement_sums.tobytes(order="C")),
        },
        "blocks_ordered": blocks,
        "raw_material_byte_count": len(raw),
        "raw_material_sha256": sha256_hex(raw),
        "sign_policy": REPLICATE_SIGN_POLICY,
    }
    return record, raw


# --------------------------------------------------------------------------
# Byte-for-byte comparison against the ratified tooling binding
# --------------------------------------------------------------------------

RATIFIED_TOOLING_BINDING_SCHEMA = "MES_TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1"
RATIFIED_TOOLING_BINDING_RELATIVE_PATH = (
    "docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json"
)
RATIFIED_BINDING_DOCUMENT_KEYS: frozenset[str] = frozenset(
    {"schema", "payload", "payload_sha256"}
)
RATIFIED_FIXTURE_CONTENT = "SYNTHETIC_ONLY"
RATIFIED_FIXTURE_REPLAY = "EXACT_BYTEWISE_REPLAY_VERIFIED"
RATIFIED_FIXTURE_STORAGE = "IN_MEMORY_AND_INSIDE_PATH3_ONLY"
GOLDEN_COMPARISON_BASIS = (
    "RECOMPUTED_PROJECTION_COMPARED_BYTE_FOR_BYTE_WITH_THE_RATIFIED_TOOLING_BINDING"
)


@dataclass(frozen=True)
class GoldenBindingVerification:
    """One comparison of the recomputed projection with the ratified binding bytes.

    ``verified`` is true only when the supplied document bytes are exactly the
    governed canonical rendering of their own payload, the recorded
    ``payload_sha256`` reconciles with that payload, the internal bytewise replay
    of the projection agrees with itself, and every ratified golden-fixture field
    equals the recomputed field. ``verification_token`` is recomputed from the
    record's own substantive fields, so a record whose fields were altered after
    construction no longer matches its token.
    """

    projection_id: str
    binding_schema: str | None
    binding_document_sha256: str
    binding_payload_sha256: str | None
    observed_raw_sha256: str | None
    replay_mismatches: tuple[str, ...]
    binding_mismatches: tuple[str, ...]
    verified: bool
    verification_token: str
    basis: str = GOLDEN_COMPARISON_BASIS


def golden_binding_verification_token(
    *,
    projection_id: str,
    binding_schema: str | None,
    binding_document_sha256: str,
    binding_payload_sha256: str | None,
    observed_raw_sha256: str | None,
    replay_mismatches: Sequence[str],
    binding_mismatches: Sequence[str],
    verified: bool,
) -> str:
    """Recompute the token that binds a verification record to its own fields."""

    return sha256_hex(
        canonical_json_bytes(
            {
                "projection_id": projection_id,
                "binding_schema": binding_schema,
                "binding_document_sha256": binding_document_sha256,
                "binding_payload_sha256": binding_payload_sha256,
                "observed_raw_sha256": observed_raw_sha256,
                "replay_mismatches": list(replay_mismatches),
                "binding_mismatches": list(binding_mismatches),
                "verified": bool(verified),
                "basis": GOLDEN_COMPARISON_BASIS,
            }
        )
    )


def _compare_digest_map(
    label: str,
    recomputed: Mapping[str, Any],
    ratified: Any,
    names: Sequence[tuple[str, str]],
) -> list[str]:
    if not isinstance(ratified, Mapping):
        return [f"RATIFIED_FIXTURE_SECTION_IS_NOT_A_MAPPING:{label}"]
    mismatches: list[str] = []
    for recomputed_key, ratified_key in names:
        if ratified.get(ratified_key) != recomputed.get(recomputed_key):
            mismatches.append(f"RATIFIED_FIXTURE_FIELD_DIFFERS:{label}.{ratified_key}")
    return mismatches


def _compare_golden_fixture(record: Mapping[str, Any], fixture: Any) -> list[str]:
    if not isinstance(fixture, Mapping):
        return ["RATIFIED_BINDING_HAS_NO_GOLDEN_FIXTURE_SECTION"]
    mismatches: list[str] = []

    spec = fixture.get("spec")
    if not isinstance(spec, Mapping):
        mismatches.append("RATIFIED_FIXTURE_SPEC_IS_NOT_A_MAPPING")
    else:
        if spec.get("content") != RATIFIED_FIXTURE_CONTENT:
            mismatches.append("RATIFIED_FIXTURE_CONTENT_IS_NOT_SYNTHETIC_ONLY")
        if spec.get("master_seed") != MASTER_SEED:
            mismatches.append("RATIFIED_FIXTURE_MASTER_SEED_DIFFERS")
        if spec.get("replications") != BOOTSTRAP_REPLICATIONS:
            mismatches.append("RATIFIED_FIXTURE_REPLICATIONS_DIFFER")
        if list(spec.get("block_lengths_ordered") or ()) != list(
            BOOTSTRAP_BLOCK_LENGTHS_ORDERED
        ):
            mismatches.append("RATIFIED_FIXTURE_BLOCK_LENGTH_ORDER_DIFFERS")
        if spec.get("session_count") != record["session_count"]:
            mismatches.append("RATIFIED_FIXTURE_SESSION_COUNT_DIFFERS")

    if fixture.get("storage") != RATIFIED_FIXTURE_STORAGE:
        mismatches.append("RATIFIED_FIXTURE_STORAGE_DIFFERS")
    if fixture.get("replay") != RATIFIED_FIXTURE_REPLAY:
        mismatches.append("RATIFIED_FIXTURE_REPLAY_STATE_DIFFERS")
    if fixture.get("row_count") != record["row_count"]:
        mismatches.append("RATIFIED_FIXTURE_ROW_COUNT_DIFFERS")
    if fixture.get("raw_material_sha256") != record["raw_material_sha256"]:
        mismatches.append("RATIFIED_FIXTURE_RAW_MATERIAL_DIGEST_DIFFERS")

    mismatches.extend(
        _compare_digest_map(
            "inputs_sha256",
            record["inputs_sha256"],
            fixture.get("inputs_sha256"),
            (
                ("actual", "actual"),
                ("forecast_base", "forecast_base"),
                ("forecast_har", "forecast_har"),
            ),
        )
    )
    mismatches.extend(
        _compare_digest_map(
            "row_losses_sha256",
            record["row_losses_sha256"],
            fixture.get("row_losses_sha256"),
            (("loss_base", "loss_base"), ("loss_har", "loss_har"), ("difference", "difference")),
        )
    )
    mismatches.extend(
        _compare_digest_map(
            "session_aggregates_sha256",
            record["session_aggregates_sha256"],
            fixture.get("session_aggregates_sha256"),
            (("row_counts", "row_counts"), ("improvement_sums", "improvement_sums")),
        )
    )
    mismatches.extend(
        _compare_digest_map(
            "means_hex",
            record["means_hex"],
            fixture.get("means_hex"),
            (
                ("mean_base", "mean_base"),
                ("mean_har", "mean_har"),
                ("mean_difference", "mean_difference"),
                ("relative_qlike_reduction", "relative_reduction"),
            ),
        )
    )

    ratified_blocks = fixture.get("blocks_ordered")
    recomputed_blocks = list(record["blocks_ordered"])
    if not isinstance(ratified_blocks, list) or len(ratified_blocks) != len(recomputed_blocks):
        mismatches.append("RATIFIED_FIXTURE_BLOCK_EXTENT_DIFFERS")
        return mismatches
    for ratified_block, recomputed_block in zip(ratified_blocks, recomputed_blocks, strict=True):
        if not isinstance(ratified_block, Mapping):
            mismatches.append("RATIFIED_FIXTURE_BLOCK_IS_NOT_A_MAPPING")
            continue
        length = recomputed_block["block_length"]
        for recomputed_key, ratified_key in (
            ("block_length", "block_length"),
            ("validation_seed", "validation_seed"),
            ("blocks_needed", "blocks_needed"),
            ("draw_matrix_sha256", "draw_matrix_sha256"),
            ("replicate_vector_sha256", "replicate_vector_sha256"),
            ("lower_bound_hex", "quantile_hex"),
        ):
            if ratified_block.get(ratified_key) != recomputed_block[recomputed_key]:
                mismatches.append(
                    f"RATIFIED_FIXTURE_BLOCK_FIELD_DIFFERS:{length}.{ratified_key}"
                )
    return mismatches


def verify_golden_projection_against_ratified_binding(
    binding_document_bytes: bytes,
) -> GoldenBindingVerification:
    """Compare the recomputed projection with the ratified tooling-binding bytes.

    The caller supplies the exact bytes of
    ``docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json``. This
    module never reads a file. Before any comparison, those bytes are required to
    be exactly the governed canonical rendering of their own payload and to carry
    a ``payload_sha256`` that reconciles with that payload, so a mutated,
    reformatted or substituted document is rejected rather than compared.

    Regenerating the current projection twice is retained as an internal
    determinism check, but it is no longer the acceptance criterion: acceptance
    requires equality with the ratified fixture fields recorded in the binding.
    """

    if not isinstance(binding_document_bytes, (bytes, bytearray)):
        raise _fail("the ratified binding must be supplied as exact bytes")
    document_bytes = bytes(binding_document_bytes)
    document_sha256 = sha256_hex(document_bytes)

    binding_mismatches: list[str] = []
    schema: str | None = None
    payload_digest: str | None = None
    payload: Any = None
    try:
        document = json.loads(document_bytes.decode("utf-8"))
    except Exception:  # noqa: BLE001 - malformed binding bytes fail closed uniformly.
        document = None
        binding_mismatches.append("RATIFIED_BINDING_IS_NOT_DECODABLE_CANONICAL_JSON")

    if document is not None:
        if not isinstance(document, Mapping) or set(document) != set(
            RATIFIED_BINDING_DOCUMENT_KEYS
        ):
            binding_mismatches.append("RATIFIED_BINDING_DOCUMENT_KEY_SET_IS_NOT_CLOSED")
        else:
            schema = document.get("schema") if isinstance(document.get("schema"), str) else None
            payload = document.get("payload")
            payload_digest = document.get("payload_sha256")
            if schema != RATIFIED_TOOLING_BINDING_SCHEMA:
                binding_mismatches.append("RATIFIED_BINDING_SCHEMA_DIFFERS")
            if governed_binding_canonical_bytes(document) != document_bytes:
                binding_mismatches.append(
                    "RATIFIED_BINDING_BYTES_ARE_NOT_THE_GOVERNED_CANONICAL_RENDERING"
                )
            if not isinstance(payload, Mapping):
                binding_mismatches.append("RATIFIED_BINDING_PAYLOAD_IS_NOT_A_MAPPING")
            elif payload.get("schema") != RATIFIED_TOOLING_BINDING_SCHEMA:
                binding_mismatches.append("RATIFIED_BINDING_PAYLOAD_SCHEMA_DIFFERS")
            elif sha256_hex(governed_binding_canonical_bytes(payload)) != payload_digest:
                binding_mismatches.append("RATIFIED_BINDING_PAYLOAD_DIGEST_DOES_NOT_RECONCILE")

    first_record, first_raw = build_golden_projection()
    second_record, second_raw = build_golden_projection()
    replay_mismatches: list[str] = []
    if first_raw != second_raw:
        replay_mismatches.append("RECOMPUTED_RAW_MATERIAL_BYTES_DIFFER")
    if canonical_json_bytes(first_record) != canonical_json_bytes(second_record):
        replay_mismatches.append("RECOMPUTED_PROJECTION_RECORD_BYTES_DIFFER")

    if not binding_mismatches and isinstance(payload, Mapping):
        binding_mismatches.extend(
            _compare_golden_fixture(first_record, payload.get("golden_fixture"))
        )

    ordered_replay = tuple(dict.fromkeys(replay_mismatches))
    ordered_binding = tuple(dict.fromkeys(binding_mismatches))
    verified = not ordered_replay and not ordered_binding
    observed_raw = sha256_hex(first_raw)
    token = golden_binding_verification_token(
        projection_id=GOLDEN_PROJECTION_ID,
        binding_schema=schema,
        binding_document_sha256=document_sha256,
        binding_payload_sha256=payload_digest if isinstance(payload_digest, str) else None,
        observed_raw_sha256=observed_raw,
        replay_mismatches=ordered_replay,
        binding_mismatches=ordered_binding,
        verified=verified,
    )
    return GoldenBindingVerification(
        projection_id=GOLDEN_PROJECTION_ID,
        binding_schema=schema,
        binding_document_sha256=document_sha256,
        binding_payload_sha256=payload_digest if isinstance(payload_digest, str) else None,
        observed_raw_sha256=observed_raw,
        replay_mismatches=ordered_replay,
        binding_mismatches=ordered_binding,
        verified=verified,
        verification_token=token,
    )


def golden_binding_refusal_reasons(verification: Any) -> tuple[str, ...]:
    """Return the ordered reasons a golden-binding verification cannot be relied on."""

    if not isinstance(verification, GoldenBindingVerification):
        reason = "GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_ABSENT_OR_NOT_A_VERIFICATION_RECORD"
        return (reason,)
    reasons: list[str] = []
    expected = golden_binding_verification_token(
        projection_id=verification.projection_id,
        binding_schema=verification.binding_schema,
        binding_document_sha256=verification.binding_document_sha256,
        binding_payload_sha256=verification.binding_payload_sha256,
        observed_raw_sha256=verification.observed_raw_sha256,
        replay_mismatches=verification.replay_mismatches,
        binding_mismatches=verification.binding_mismatches,
        verified=verification.verified,
    )
    if (
        verification.basis != GOLDEN_COMPARISON_BASIS
        or verification.verification_token != expected
    ):
        reasons.append("GOLDEN_FIXTURE_BINDING_VERIFICATION_TOKEN_DOES_NOT_RECONCILE")
    if verification.projection_id != GOLDEN_PROJECTION_ID:
        reasons.append("GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_FOR_ANOTHER_PROJECTION")
    if verification.binding_schema != RATIFIED_TOOLING_BINDING_SCHEMA:
        reasons.append("GOLDEN_FIXTURE_BINDING_SCHEMA_IS_NOT_THE_RATIFIED_SCHEMA")
    if (
        verification.replay_mismatches
        or verification.binding_mismatches
        or not verification.verified
    ):
        reasons.append("GOLDEN_FIXTURE_BYTEWISE_REPLAY_FAILED")
    return tuple(dict.fromkeys(reasons))


# --------------------------------------------------------------------------
# Pure C0 / C0V refusal assessment (no input, no output, no authority)
# --------------------------------------------------------------------------

C0_CHECKPOINT = "C0"
C0V_CHECKPOINT = "C0V"
CHECKPOINT_PASS = "PASS"
PRE_START_PROCEDURAL_REFUSAL = "PRE_START_PROCEDURAL_REFUSAL"
PRE_START_CLASSIFICATION = (
    "PRE_START_PROCEDURAL_ASSESSMENT_BEFORE_SCIENTIFIC_TERMINAL_CLASS_CLOSURE"
)
CHECKPOINT_EFFECT = "NO_RESERVATION_NO_PERMIT_NO_WITNESS_NO_ACCESS_NO_FIT"

C0_REFUSAL_REASONS: tuple[str, ...] = (
    "SEALED_IDENTITY_SCHEMA_NONCONFORMING",
    "RE_RECORD_IDENTITY_SCHEMA_NONCONFORMING",
    "IMMEDIATE_RE_RECORD_NOT_EXACTLY_EQUAL_TO_SEALED_IDENTITY",
    "GOLDEN_FIXTURE_BYTEWISE_REPLAY_FAILED",
    "GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_ABSENT_OR_NOT_A_VERIFICATION_RECORD",
    "GOLDEN_FIXTURE_BINDING_VERIFICATION_TOKEN_DOES_NOT_RECONCILE",
    "GOLDEN_FIXTURE_BINDING_SCHEMA_IS_NOT_THE_RATIFIED_SCHEMA",
    "GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_FOR_ANOTHER_PROJECTION",
)

C0V_ADDITIONAL_REFUSAL_REASONS: tuple[str, ...] = (
    "SEALED_C0V_IDENTITY_NOT_EXACTLY_EQUAL_TO_SEALED_C0_IDENTITY",
    "SEALED_DEPLOYMENT_FITS_ARE_ABSENT_OR_NONCONFORMING",
    "DEPLOYMENT_SEALS_NOT_INDEPENDENTLY_VERIFIED",
    "SUPPLIED_SEAL_VERIFICATION_IS_NOT_BOUND_TO_THESE_EXACT_SEALED_FITS",
    SEPARATE_OWNER_GRANT_2_REFUSAL,
)


@dataclass(frozen=True)
class RuntimeCheckpointAssessment:
    """A pure ``C0`` or ``C0V`` assessment that grants nothing whatsoever.

    ``terminal_class`` is permanently ``None``: Protocol V1 Sections 3.0, 4, 5.5
    and 7 place ``C0`` and ``C0V`` refusal strictly before scientific
    terminal-class closure, so a refusal here is never one of the four terminal
    classes. A passing assessment is equally powerless: it creates no
    reservation, permit, witness or access, and any later act requires separate
    Owner authority.
    """

    checkpoint: str
    outcome: str
    refusal_reasons: tuple[str, ...]
    identity_comparisons: tuple[tuple[str, RuntimeIdentityComparison], ...]
    permits_consumed: int
    fits_performed: int
    validation_state: str
    witness_created: bool
    authorizes_refit: bool
    terminal_class: None
    classification: str
    effect: str
    seal_digest: str | None = None
    grant_id: str | None = None

    @property
    def refused(self) -> bool:
        return self.outcome == PRE_START_PROCEDURAL_REFUSAL


def _checkpoint_result(
    checkpoint: str,
    reasons: Sequence[str],
    comparisons: Sequence[tuple[str, RuntimeIdentityComparison]],
    *,
    seal_digest: str | None = None,
    grant_id: str | None = None,
) -> RuntimeCheckpointAssessment:
    ordered = tuple(dict.fromkeys(reasons))
    return RuntimeCheckpointAssessment(
        checkpoint=checkpoint,
        outcome=PRE_START_PROCEDURAL_REFUSAL if ordered else CHECKPOINT_PASS,
        refusal_reasons=ordered,
        identity_comparisons=tuple(comparisons),
        permits_consumed=0,
        fits_performed=0,
        validation_state="UNOPENED",
        witness_created=False,
        authorizes_refit=False,
        terminal_class=None,
        classification=PRE_START_CLASSIFICATION,
        effect=CHECKPOINT_EFFECT,
        seal_digest=None if ordered else seal_digest,
        grant_id=None if ordered else grant_id,
    )


def assess_c0(
    *,
    sealed_identity: Any,
    pre_permit_identity: Any,
    golden_binding_verification: Any,
) -> RuntimeCheckpointAssessment:
    """Assess the data-free ``C0`` execution preflight without performing it.

    ``C0`` create-once binds the execution runtime identity, immediately
    re-records it before any reservation or permit, requires exact equality, and
    bytewise replays the frozen golden fixture against the ratified binding.
    Refusal consumes ``0/2`` permits, performs zero fits and keeps Validation
    ``UNOPENED``. The golden replay is supplied as a verification record produced
    by :func:`verify_golden_projection_against_ratified_binding`; a caller
    boolean is not accepted.
    """

    comparison = compare_runtime_identities(
        sealed_identity,
        pre_permit_identity,
        sealed_label="C0_SEALED",
        observed_label="C0_RE_RECORD",
    )
    reasons: list[str] = []
    if not comparison.conforming:
        if any(item.startswith("C0_SEALED") for item in comparison.defects):
            reasons.append("SEALED_IDENTITY_SCHEMA_NONCONFORMING")
        if any(item.startswith("C0_RE_RECORD") for item in comparison.defects):
            reasons.append("RE_RECORD_IDENTITY_SCHEMA_NONCONFORMING")
    elif not comparison.equal:
        reasons.append("IMMEDIATE_RE_RECORD_NOT_EXACTLY_EQUAL_TO_SEALED_IDENTITY")
    reasons.extend(golden_binding_refusal_reasons(golden_binding_verification))
    return _checkpoint_result(
        C0_CHECKPOINT, reasons, (("C0_SEALED_VERSUS_C0_RE_RECORD", comparison),)
    )


def assess_c0v(
    *,
    sealed_c0_identity: Any,
    sealed_c0v_identity: Any,
    pre_witness_identity: Any,
    golden_binding_verification: Any,
    sealed_fits: Any,
    seal_verification: Any,
    untrusted_grant2_claim: Any = None,
) -> RuntimeCheckpointAssessment:
    """Assess the data-free ``C0V`` scoring preflight without performing it.

    This implementation-only function can establish mechanical readiness from
    the runtime equalities, ratified golden replay and exact sealed fits, but it
    cannot mint or authenticate Owner Grant 2. It therefore always returns the
    closed ``SEPARATE_OWNER_GRANT_2_NOT_AVAILABLE_IN_IMPLEMENTATION_SLICE``
    refusal, even when every mechanical prerequisite is conforming.

    ``untrusted_grant2_claim`` exists only so adversarial callers can prove that
    booleans, mappings, citations, digest lookalikes and arbitrary objects are
    all powerless. It is never inspected for authority and can never set
    ``grant_id``. Refusal creates no witness, causes no Validation access and
    authorizes no refit.
    """

    against_c0 = compare_runtime_identities(
        sealed_c0_identity,
        sealed_c0v_identity,
        sealed_label="C0_SEALED",
        observed_label="C0V_SEALED",
    )
    against_self = compare_runtime_identities(
        sealed_c0v_identity,
        pre_witness_identity,
        sealed_label="C0V_SEALED",
        observed_label="C0V_RE_RECORD",
    )
    reasons: list[str] = []
    defects = (*against_c0.defects, *against_self.defects)
    if defects:
        if any(item.startswith(("C0_SEALED", "C0V_SEALED")) for item in defects):
            reasons.append("SEALED_IDENTITY_SCHEMA_NONCONFORMING")
        if any(item.startswith("C0V_RE_RECORD") for item in defects):
            reasons.append("RE_RECORD_IDENTITY_SCHEMA_NONCONFORMING")
    else:
        if not against_c0.equal:
            reasons.append("SEALED_C0V_IDENTITY_NOT_EXACTLY_EQUAL_TO_SEALED_C0_IDENTITY")
        if not against_self.equal:
            reasons.append("IMMEDIATE_RE_RECORD_NOT_EXACTLY_EQUAL_TO_SEALED_IDENTITY")
    reasons.extend(golden_binding_refusal_reasons(golden_binding_verification))

    observed_digest: str | None = None
    fits: tuple[Any, ...] = ()
    if isinstance(sealed_fits, (str, bytes)) or not isinstance(sealed_fits, Sequence):
        reasons.append("SEALED_DEPLOYMENT_FITS_ARE_ABSENT_OR_NONCONFORMING")
    else:
        fits = tuple(sealed_fits)
        if len(fits) != len(MODEL_ORDER) or not all(
            isinstance(item, DeploymentFit) for item in fits
        ):
            reasons.append("SEALED_DEPLOYMENT_FITS_ARE_ABSENT_OR_NONCONFORMING")
        else:
            independent = verify_deployment_seals(fits)
            if not independent.verified or independent.seals_verified != len(MODEL_ORDER):
                reasons.append("DEPLOYMENT_SEALS_NOT_INDEPENDENTLY_VERIFIED")
            else:
                observed_digest = independent.seal_digest

    if observed_digest is not None and (
        not isinstance(seal_verification, DeploymentSealVerification)
        or not seal_verification.verified
        or seal_verification.seals_verified != len(MODEL_ORDER)
        or seal_verification.model_ids != MODEL_ORDER
        or seal_verification.basis != SEAL_VERIFICATION_BASIS
        or seal_verification.seal_digest != observed_digest
    ):
        reasons.append("SUPPLIED_SEAL_VERIFICATION_IS_NOT_BOUND_TO_THESE_EXACT_SEALED_FITS")

    # This value is intentionally unused: there is no local carrier type or
    # binder that can turn a caller-created object into Owner Grant 2 authority.
    _ = untrusted_grant2_claim
    reasons.append(SEPARATE_OWNER_GRANT_2_REFUSAL)

    return _checkpoint_result(
        C0V_CHECKPOINT,
        reasons,
        (
            ("C0_SEALED_VERSUS_C0V_SEALED", against_c0),
            ("C0V_SEALED_VERSUS_C0V_RE_RECORD", against_self),
        ),
        seal_digest=observed_digest,
        grant_id=None,
    )


__all__ = [
    "ACF_LAGS",
    "ACF_MINIMUM_PAIRS",
    "ACF_SPACING_MINUTES",
    "ACF_SUPPORT_UNDEFINED_REASON",
    "BASE_MODEL_ID",
    "BOOTSTRAP_BLOCK_LENGTHS_ORDERED",
    "BOOTSTRAP_QUANTILE",
    "BOOTSTRAP_QUANTILE_METHOD",
    "BOOTSTRAP_REPLICATIONS",
    "C0V_ADDITIONAL_REFUSAL_REASONS",
    "C0_REFUSAL_REASONS",
    "CLASSIFICATION",
    "CONFIRMATORY_FIT_BUDGET",
    "CONFIRMATORY_FIT_BUDGET_ID",
    "CONTRACT_DOCUMENTS_ORDERED",
    "CONTRACT_RULE",
    "DATA_POLICY",
    "DIAGNOSTIC_BLOCK_LENGTHS",
    "DUAN_BASIS",
    "GOLDEN_COMPARISON_BASIS",
    "GOLDEN_PROJECTION_ID",
    "GOLDEN_PROJECTION_SESSION_COUNT",
    "HAR_MODEL_ID",
    "IMPLEMENTATION_GUARANTEES",
    "MASTER_SEED",
    "MINIMUM_VALIDATION_SESSIONS",
    "MODEL_COLUMNS",
    "MODEL_ORDER",
    "MODULE_ID",
    "NETWORK_POLICY",
    "PRIMARY_BLOCK_LENGTH",
    "PURGE_GAP_MINUTES",
    "RATIFIED_TOOLING_BINDING_RELATIVE_PATH",
    "RATIFIED_TOOLING_BINDING_SCHEMA",
    "RELATIVE_QLIKE_REDUCTION_FLOOR",
    "REPLICATE_SIGN_POLICY",
    "RUNTIME_IDENTITY_SCHEMA",
    "SEAL_VERIFICATION_BASIS",
    "SEPARATE_OWNER_GRANT_2_REFUSAL",
    "AcfAssessment",
    "AcfLagResult",
    "AcfRow",
    "BootstrapBlockResult",
    "CommonEligibleTrainSample",
    "ConfirmatoryCounters",
    "DecisionMetrics",
    "DeploymentDesign",
    "DeploymentFit",
    "DeploymentFitLedger",
    "DeploymentPrecheck",
    "DeploymentSealVerification",
    "DesignPrecheck",
    "GoldenBindingVerification",
    "PassAssessment",
    "RowLosses",
    "RuntimeCheckpointAssessment",
    "RuntimeIdentityComparison",
    "SessionAggregate",
    "SessionAggregates",
    "TerminalClass",
    "TerminalClassification",
    "Test3ConfirmatoryValidationError",
    "ValidationSupport",
    "assess_c0",
    "assess_c0v",
    "assess_partition_integrity",
    "assess_validation_support",
    "assess_within_session_acf",
    "bind_common_eligible_train_sample",
    "bind_deployment_design",
    "build_draw_matrix",
    "build_golden_projection",
    "build_session_aggregates",
    "build_validation_support",
    "canonical_json_bytes",
    "classify_confirmatory_terminal",
    "compare_runtime_identities",
    "compute_decision_metrics",
    "compute_replicate_vector",
    "compute_row_losses",
    "deployment_forecast",
    "deployment_seal_digest",
    "evaluate_pass_criteria",
    "float_hex",
    "golden_binding_refusal_reasons",
    "golden_binding_verification_token",
    "golden_projection_inputs",
    "golden_projection_session_row_counts",
    "governed_binding_canonical_bytes",
    "left_fold",
    "pooled_seed",
    "precheck_deployment_designs",
    "primary_block_result",
    "reconcile_counters",
    "require_closed_runtime_identity",
    "require_finite",
    "require_float64_matrix",
    "require_float64_vector",
    "rho_null",
    "row_identity_defects",
    "row_identity_sha256",
    "run_frozen_validation_bootstrap",
    "run_ordered_deployment_fits",
    "runtime_identity_defects",
    "sha256_hex",
    "validation_seed",
    "validation_support_integrity_defects",
    "verify_deployment_seals",
    "verify_golden_projection_against_ratified_binding",
]

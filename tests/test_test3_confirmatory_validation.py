"""Synthetic tests for the Test 3 confirmatory-validation implementation V1.

Every scientific operand below is a closed-form synthetic constant built inside
this file or by the implementation module itself. No test reads, writes or
otherwise touches any data, provider, target, evidence, partition, row or
runtime artifact surface; no test opens a network connection; and no test
creates a file. Exactly one governed repository file is read besides the module
source: the ratified tooling binding
``docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json``, whose
exact bytes are the comparison root for the golden projection.

The implementation module is loaded directly from its own source file, on its
own, so that these tests observe exactly the closed standard-library-and-NumPy
import surface the module claims.

The tests are grouped in Protocol order: module surface, serialization, closed
runtime binding and comparison, exact feature and row identity binding, the
pre-fit rank and identity gate, BASE/HAR deployment fits and model-local Duan,
independent seal verification and the deliberately unavailable Owner Grant 2, the pure
``C0``/``C0V`` refusal assessments, QLIKE row losses and stored-order decision
metrics, session aggregates, the frozen ``(5, 1, 20)`` bootstrap with the
signed-replicate erratum, the exact within-session ACF with its derived session
table, integrity-before-support precedence, and the golden projection compared
byte for byte against the ratified binding.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import json
import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import numpy
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_SOURCE = (
    REPOSITORY_ROOT / "src" / "mes_quant" / "exploration" / "test3_confirmatory_validation.py"
)
RATIFIED_BINDING_SOURCE = (
    REPOSITORY_ROOT
    / "docs"
    / "research"
    / "TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json"
)
IMPLEMENTATION_MODULE_NAME = "test3_confirmatory_validation_under_test"

# The module claims a closed standard-library-and-NumPy import surface. These
# are the only module names it may import, and the only module objects that may
# appear in its namespace after loading.
ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "enum",
        "hashlib",
        "json",
        "math",
        "numbers",
        "numpy",
        "types",
        "typing",
    }
)
ALLOWED_NAMESPACE_MODULES = frozenset({"hashlib", "json", "math", "numpy"})

# Names whose presence anywhere in the implementation's referenced identifiers
# would contradict its data-free, no-I/O, no-network guarantees.
FORBIDDEN_SOURCE_NAMES = frozenset(
    {
        "open",
        "os",
        "io",
        "pathlib",
        "Path",
        "shutil",
        "socket",
        "urllib",
        "requests",
        "http",
        "subprocess",
        "pickle",
        "sqlite3",
        "pandas",
        "pyarrow",
        "databento",
        "write_text",
        "write_bytes",
        "mkdir",
        "makedirs",
        "read_text",
        "read_bytes",
        "urlopen",
        "connect",
        "__import__",
        "eval",
        "exec",
    }
)


def _load_implementation() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        IMPLEMENTATION_MODULE_NAME, IMPLEMENTATION_SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[IMPLEMENTATION_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


impl = _load_implementation()
IMPLEMENTATION_TREE = ast.parse(IMPLEMENTATION_SOURCE.read_bytes().decode("utf-8"))
RATIFIED_BINDING_BYTES = RATIFIED_BINDING_SOURCE.read_bytes()


# --------------------------------------------------------------------------
# Synthetic operand builders
# --------------------------------------------------------------------------


def synthetic_identity(marker: str = "A") -> dict[str, object]:
    """One conforming, entirely invented closed-schema runtime identity."""

    return {
        "python": {
            "implementation": "SyntheticPython",
            "version": "0.0.0",
            "version_full": f"SyntheticPython 0.0.0 {marker}",
            "api_version": 0,
            "hexversion": 0,
            "cache_tag": "synthetic-0",
            "maxsize": 1,
            "float_repr_style": "short",
            "executable": "/synthetic/bin/python",
            "executable_resolved": "/synthetic/bin/python",
            "float_info": {
                "epsilon_hex": float(2.0**-52).hex(),
                "max_hex": (1.0).hex(),
                "min_hex": (0.5).hex(),
                "dig": 15,
                "mant_dig": 53,
                "max_10_exp": 308,
                "max_exp": 1024,
                "min_10_exp": -307,
                "min_exp": -1021,
                "radix": 2,
                "rounds": 1,
            },
        },
        "numpy": {
            "version": "0.0.0",
            "build_config": {"blas": "synthetic", "lapack": "synthetic"},
        },
        "platform": {
            "system": "Synthetic",
            "release": "0",
            "version": "0",
            "machine": "synthetic",
            "processor": "",
            "byteorder": "little",
            "libc": ["synthetic", "0"],
        },
        "float64": {
            "dtype_str": "<f8",
            "itemsize": 8,
            "byteorder": "=",
            "eps_hex": float(2.0**-52).hex(),
            "epsneg_hex": float(2.0**-53).hex(),
            "tiny_hex": float(2.0**-1022).hex(),
            "max_hex": (1.0).hex(),
            "min_hex": (-1.0).hex(),
            "resolution_hex": (1e-15).hex(),
            "nmant": 52,
            "nexp": 11,
            "machep": -52,
            "negep": -53,
            "iexp": 11,
            "maxexp": 1024,
            "minexp": -1021,
        },
        "rng": {
            "bit_generator_module": "synthetic.random._pcg64",
            "bit_generator_class": "PCG64",
            "generator_class": "synthetic.random.Generator",
            "pcg64_module": "synthetic.random._pcg64",
            "pcg64_class": "PCG64",
        },
    }


def synthetic_columns(count: int = 120) -> dict[str, numpy.ndarray]:
    index = numpy.arange(count, dtype=numpy.float64)
    angle = 2.0 * math.pi * (index % 24.0) / 24.0
    return {
        "intercept": numpy.ones(count, dtype=numpy.float64),
        "X60": 0.10 + 0.010 * ((index * 7.0) % 11.0),
        "X120": 0.20 + 0.011 * ((index * 5.0) % 13.0),
        "X240": 0.30 + 0.012 * ((index * 3.0) % 17.0),
        "SESSION_SIN": numpy.sin(angle),
        "SESSION_COS": numpy.cos(angle),
        "WOBBLE": 0.01 * (((index * 11.0) % 7.0) - 3.0),
    }


def synthetic_row_identities(count: int = 120) -> tuple[str, ...]:
    return tuple(f"SYNTHETIC_TRAIN_ROW_{position:04d}" for position in range(count))


def design_matrix(columns: dict[str, numpy.ndarray], names: tuple[str, ...]) -> numpy.ndarray:
    return numpy.ascontiguousarray(
        numpy.column_stack([columns[name] for name in names]), dtype=numpy.float64
    )


def synthetic_log_target(columns: dict[str, numpy.ndarray]) -> numpy.ndarray:
    return numpy.ascontiguousarray(
        0.50
        + 0.30 * columns["X60"]
        + 0.20 * columns["X120"]
        + 0.10 * columns["X240"]
        + 0.05 * columns["SESSION_SIN"]
        - 0.04 * columns["SESSION_COS"]
        + columns["WOBBLE"],
        dtype=numpy.float64,
    )


def synthetic_sample(count: int = 120) -> object:
    columns = synthetic_columns(count)
    identities = synthetic_row_identities(count)
    designs = [
        impl.bind_deployment_design(
            model_id,
            impl.MODEL_COLUMNS[model_id],
            identities,
            design_matrix(columns, impl.MODEL_COLUMNS[model_id]),
        )
        for model_id in impl.MODEL_ORDER
    ]
    return impl.bind_common_eligible_train_sample(
        identities, synthetic_log_target(columns), designs
    )


def rank_deficient_sample(count: int = 120) -> object:
    columns = synthetic_columns(count)
    identities = synthetic_row_identities(count)
    collapsed = dict(columns)
    collapsed["SESSION_SIN"] = columns["intercept"]
    collapsed["SESSION_COS"] = columns["intercept"]
    designs = [
        impl.bind_deployment_design(
            model_id,
            impl.MODEL_COLUMNS[model_id],
            identities,
            design_matrix(collapsed, impl.MODEL_COLUMNS[model_id]),
        )
        for model_id in impl.MODEL_ORDER
    ]
    return impl.bind_common_eligible_train_sample(
        identities, synthetic_log_target(columns), designs
    )


def mismatched_identity_sample(count: int = 120) -> object:
    columns = synthetic_columns(count)
    identities = synthetic_row_identities(count)
    other = tuple(f"OTHER_{name}" for name in identities)
    base = impl.bind_deployment_design(
        impl.BASE_MODEL_ID,
        impl.MODEL_COLUMNS[impl.BASE_MODEL_ID],
        identities,
        design_matrix(columns, impl.MODEL_COLUMNS[impl.BASE_MODEL_ID]),
    )
    har = impl.bind_deployment_design(
        impl.HAR_MODEL_ID,
        impl.MODEL_COLUMNS[impl.HAR_MODEL_ID],
        other,
        design_matrix(columns, impl.MODEL_COLUMNS[impl.HAR_MODEL_ID]),
    )
    return impl.CommonEligibleTrainSample(
        row_identities=identities,
        log_target=synthetic_log_target(columns),
        designs=(base, har),
    )


def synthetic_acf_rows(
    *,
    sessions: int = 3,
    per_session: int = 12,
    constant: bool = False,
    interleaved: bool = False,
) -> tuple[object, ...]:
    start = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    rows = []
    for session in range(sessions):
        session_start = start + timedelta(days=session)
        for step in range(per_session):
            identity = f"SESSION_{session:02d}"
            if interleaved and step % 2 == 1:
                identity = "SESSION_ALT"
            rows.append(
                impl.AcfRow(
                    session_id=identity,
                    decision_time=session_start + timedelta(minutes=15 * step),
                    rv_fwd_60=1.0 if constant else 1.0 + ((session * per_session + step) % 5) / 8.0,
                )
            )
    return tuple(rows)


def synthetic_session_aggregates(*, sign: float) -> object:
    identifiers: list[str] = []
    values: list[float] = []
    for session in range(24):
        for row in range(4):
            identifiers.append(f"S{session:02d}")
            values.append(sign * (0.001 + 0.0001 * row))
    difference = numpy.ascontiguousarray(values, dtype=numpy.float64)
    return impl.build_session_aggregates(tuple(identifiers), difference)


@pytest.fixture(scope="module")
def sample() -> object:
    return synthetic_sample()


@pytest.fixture(scope="module")
def deployment_ledger(sample: object) -> object:
    return impl.run_ordered_deployment_fits(sample)


@pytest.fixture(scope="module")
def golden_verification() -> object:
    return impl.verify_golden_projection_against_ratified_binding(RATIFIED_BINDING_BYTES)


@pytest.fixture(scope="module")
def golden_projection() -> tuple[dict[str, object], bytes]:
    return impl.build_golden_projection()


# --------------------------------------------------------------------------
# Module surface and closed import discipline
# --------------------------------------------------------------------------


def test_module_classification_is_capability_only() -> None:
    assert impl.MODULE_ID == "MES_TEST3_CONFIRMATORY_VALIDATION_IMPLEMENTATION_V1"
    for token in ("IMPLEMENTATION_CAPABILITY_ONLY", "NOT_C0", "NOT_C0V", "NOT_ACTIVATION"):
        assert token in impl.CLASSIFICATION
    assert impl.DATA_POLICY == "DATA_FREE_NO_PROVIDER_TARGET_EVIDENCE_ACCESS"
    assert impl.NETWORK_POLICY == "LOCAL_ONLY_NO_NETWORK"
    for guarantee in (
        "DATA_FREE",
        "NO_FILESYSTEM_IO",
        "NO_NETWORK",
        "NO_ACTIVATION",
        "NO_C0_OR_C0V_AUTHORITY",
        "NO_RESERVATION_OR_PERMIT_ISSUANCE",
        "NO_VALIDATION_OPENING_WITNESS",
        "NO_FINAL_TEST_ACCESS",
        "NO_SCIENTIFIC_CLAIM",
    ):
        assert guarantee in impl.IMPLEMENTATION_GUARANTEES


def test_contract_of_record_is_the_inseparable_co_ratified_pair() -> None:
    assert impl.CONTRACT_DOCUMENTS_ORDERED == (
        "docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md",
        "docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md",
    )
    assert impl.CONTRACT_RULE == (
        "PROTOCOL_V1_AND_SIGNED_BOOTSTRAP_ERRATUM_V1_ARE_ONE_INSEPARABLE_CONTRACT"
    )


def test_frozen_scientific_constants_are_carried_forward_unchanged() -> None:
    assert impl.MODEL_ORDER == ("RVBASE001", "RVHAR001")
    assert impl.MODEL_COLUMNS["RVBASE001"] == (
        "intercept",
        "X60",
        "SESSION_SIN",
        "SESSION_COS",
    )
    assert impl.MODEL_COLUMNS["RVHAR001"] == (
        "intercept",
        "X60",
        "X120",
        "X240",
        "SESSION_SIN",
        "SESSION_COS",
    )
    assert impl.MASTER_SEED == 20260809
    assert impl.BOOTSTRAP_REPLICATIONS == 2000
    assert impl.BOOTSTRAP_BLOCK_LENGTHS_ORDERED == (5, 1, 20)
    assert impl.PRIMARY_BLOCK_LENGTH == 5
    assert impl.DIAGNOSTIC_BLOCK_LENGTHS == (1, 20)
    assert impl.BOOTSTRAP_QUANTILE == 0.05
    assert impl.BOOTSTRAP_QUANTILE_METHOD == "linear"
    assert impl.RELATIVE_QLIKE_REDUCTION_FLOOR == 0.10
    assert impl.MINIMUM_VALIDATION_SESSIONS == 20
    assert impl.ACF_LAGS == (1, 2, 3, 4, 5, 6, 7, 8)
    assert impl.ACF_SPACING_MINUTES == 15
    assert impl.ACF_MINIMUM_PAIRS == 2
    assert impl.PURGE_GAP_MINUTES == 60
    assert impl.CONFIRMATORY_FIT_BUDGET == 2
    assert impl.CONFIRMATORY_FIT_BUDGET_ID == "CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1"


def test_implementation_imports_only_stdlib_and_numpy() -> None:
    roots: set[str] = set()
    for node in ast.walk(IMPLEMENTATION_TREE):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative imports would open the package surface"
            assert node.module is not None
            roots.add(node.module.split(".")[0])
    assert roots <= ALLOWED_IMPORT_ROOTS


def test_implementation_namespace_holds_no_unexpected_module() -> None:
    present = {
        name for name, value in vars(impl).items() if isinstance(value, ModuleType)
    }
    assert present == set(ALLOWED_NAMESPACE_MODULES)


def test_implementation_references_no_io_network_or_data_surface() -> None:
    referenced: set[str] = set()
    for node in ast.walk(IMPLEMENTATION_TREE):
        if isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            referenced.add(node.attr)
    assert not (referenced & FORBIDDEN_SOURCE_NAMES)


def test_declared_public_surface_is_complete_and_duplicate_free() -> None:
    exported = list(impl.__all__)
    assert len(exported) == len(set(exported))
    for name in exported:
        assert hasattr(impl, name), name


# --------------------------------------------------------------------------
# Deterministic serialization
# --------------------------------------------------------------------------


def test_canonical_json_bytes_are_sorted_compact_and_unterminated() -> None:
    payload = {"b": 1, "a": [2, 3]}
    assert impl.canonical_json_bytes(payload) == b'{"a":[2,3],"b":1}'


def test_governed_binding_canonical_bytes_match_the_governed_helper_form() -> None:
    payload = {"b": 1, "a": [2, 3]}
    assert impl.governed_binding_canonical_bytes(payload) == b'{"a":[2,3],"b":1}\n'


def test_canonical_json_bytes_refuse_nonfinite_and_unsupported_members() -> None:
    with pytest.raises(ValueError):
        impl.canonical_json_bytes({"x": float("nan")})
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.canonical_json_bytes({"x": {1, 2}})


def test_sha256_hex_requires_exact_bytes() -> None:
    assert impl.sha256_hex(b"") == impl.sha256_hex(bytearray())
    assert len(impl.sha256_hex(b"abc")) == 64
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.sha256_hex("abc")


def test_float_hex_preserves_bitwise_identity() -> None:
    for value in (0.0, -0.0, 0.1, 1e-300, 2.0**-1022):
        assert float.fromhex(impl.float_hex(value)) == value


def test_require_finite_refuses_nonfinite_and_non_numeric_values() -> None:
    assert impl.require_finite(1.5, name="x") == 1.5
    for bad in (float("nan"), float("inf"), -float("inf")):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.require_finite(bad, name="x")
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.require_finite(True, name="x")


# --------------------------------------------------------------------------
# Closed runtime-identity schema and comparator
# --------------------------------------------------------------------------


def test_closed_schema_accepts_a_conforming_identity() -> None:
    assert impl.runtime_identity_defects(synthetic_identity(), label="X") == ()
    impl.require_closed_runtime_identity(synthetic_identity())


def test_closed_schema_rejects_missing_extra_and_mistyped_members() -> None:
    missing_group = synthetic_identity()
    del missing_group["rng"]
    assert impl.runtime_identity_defects(missing_group, label="X")[0].endswith(
        "IDENTITY_GROUP_SET_IS_NOT_THE_CLOSED_SCHEMA"
    )

    extra_group = synthetic_identity()
    extra_group["extra"] = {}
    assert impl.runtime_identity_defects(extra_group, label="X")

    extra_field = synthetic_identity()
    extra_field["rng"]["surprise"] = "1"
    assert impl.runtime_identity_defects(extra_field, label="X")

    mistyped = synthetic_identity()
    mistyped["python"]["api_version"] = "1013"
    assert impl.runtime_identity_defects(mistyped, label="X")

    boolean_integer = synthetic_identity()
    boolean_integer["float64"]["itemsize"] = True
    assert impl.runtime_identity_defects(boolean_integer, label="X")

    assert impl.runtime_identity_defects(["not", "a", "mapping"], label="X") == (
        "X_IDENTITY_IS_NOT_A_MAPPING",
    )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.require_closed_runtime_identity(None)


def test_only_the_processor_text_field_may_be_empty() -> None:
    empty_processor = synthetic_identity()
    empty_processor["platform"]["processor"] = ""
    assert impl.runtime_identity_defects(empty_processor, label="X") == ()

    empty_machine = synthetic_identity()
    empty_machine["platform"]["machine"] = ""
    assert impl.runtime_identity_defects(empty_machine, label="X")


def test_malformed_float_info_is_a_closed_schema_defect() -> None:
    not_a_mapping = synthetic_identity()
    not_a_mapping["python"]["float_info"] = []
    assert impl.runtime_identity_defects(not_a_mapping, label="X")

    bad_hex = synthetic_identity()
    bad_hex["python"]["float_info"]["max_hex"] = "not-a-float"
    assert impl.runtime_identity_defects(bad_hex, label="X")

    bad_integer = synthetic_identity()
    bad_integer["python"]["float_info"]["radix"] = 2.0
    assert impl.runtime_identity_defects(bad_integer, label="X")

    bad_keys = synthetic_identity()
    del bad_keys["python"]["float_info"]["dig"]
    assert impl.runtime_identity_defects(bad_keys, label="X")


def test_comparator_reports_exact_equality_and_the_first_difference() -> None:
    equal = impl.compare_runtime_identities(synthetic_identity(), synthetic_identity())
    assert equal.conforming and equal.equal and equal.first_difference is None
    assert equal.sealed_sha256 == equal.observed_sha256

    drifted = impl.compare_runtime_identities(
        synthetic_identity("A"), synthetic_identity("B")
    )
    assert drifted.conforming and not drifted.equal
    assert drifted.first_difference == "python.version_full"
    assert drifted.sealed_sha256 != drifted.observed_sha256


def test_comparator_reports_the_first_difference_in_schema_order() -> None:
    observed = synthetic_identity()
    observed["python"]["implementation"] = "Other"
    observed["rng"]["pcg64_class"] = "Other"
    comparison = impl.compare_runtime_identities(synthetic_identity(), observed)
    assert comparison.first_difference == "python.implementation"


def test_comparator_refuses_nonconforming_operands_without_digests() -> None:
    broken = synthetic_identity()
    del broken["numpy"]
    comparison = impl.compare_runtime_identities(synthetic_identity(), broken)
    assert not comparison.conforming
    assert not comparison.equal
    assert comparison.sealed_sha256 is None and comparison.observed_sha256 is None
    assert comparison.defects


# --------------------------------------------------------------------------
# Exact feature identities and exact common-eligible row identities
# --------------------------------------------------------------------------


def test_bound_designs_carry_exact_feature_identities_and_order() -> None:
    columns = synthetic_columns()
    identities = synthetic_row_identities()
    names = impl.MODEL_COLUMNS[impl.BASE_MODEL_ID]
    bound = impl.bind_deployment_design(
        impl.BASE_MODEL_ID, names, identities, design_matrix(columns, names)
    )
    assert bound.feature_names == names
    assert bound.row_identities == identities

    reordered = (names[1], names[0], names[2], names[3])
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(
            impl.BASE_MODEL_ID, reordered, identities, design_matrix(columns, reordered)
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(
            impl.BASE_MODEL_ID,
            ("intercept", "X60", "X120", "SESSION_COS"),
            identities,
            design_matrix(columns, ("intercept", "X60", "X120", "SESSION_COS")),
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(
            "RVOTHER001", names, identities, design_matrix(columns, names)
        )


def test_bound_designs_refuse_malformed_row_identities() -> None:
    columns = synthetic_columns()
    names = impl.MODEL_COLUMNS[impl.BASE_MODEL_ID]
    matrix = design_matrix(columns, names)
    duplicated = ("A",) * 120
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(impl.BASE_MODEL_ID, names, duplicated, matrix)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(
            impl.BASE_MODEL_ID, names, ("",) + synthetic_row_identities()[1:], matrix
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_deployment_design(
            impl.BASE_MODEL_ID, names, synthetic_row_identities(119), matrix
        )


def test_row_identity_helpers_are_exact() -> None:
    assert impl.row_identity_defects(("A", "B"), label="X") == ()
    assert impl.row_identity_defects(("A", "A"), label="X") == ("X_ROW_IDENTITIES_ARE_NOT_UNIQUE",)
    assert impl.row_identity_defects((), label="X") == ("X_ROW_IDENTITIES_ARE_EMPTY",)
    assert impl.row_identity_defects("AB", label="X") == ("X_ROW_IDENTITIES_ARE_NOT_A_SEQUENCE",)
    assert impl.row_identity_sha256(("A", "B")) == impl.sha256_hex(
        impl.canonical_json_bytes(["A", "B"])
    )
    assert impl.row_identity_sha256(("A", "B")) != impl.row_identity_sha256(("B", "A"))


def test_base_and_har_must_share_the_exact_common_eligible_rows() -> None:
    columns = synthetic_columns()
    identities = synthetic_row_identities()
    other = tuple(f"OTHER_{name}" for name in identities)
    base = impl.bind_deployment_design(
        impl.BASE_MODEL_ID,
        impl.MODEL_COLUMNS[impl.BASE_MODEL_ID],
        identities,
        design_matrix(columns, impl.MODEL_COLUMNS[impl.BASE_MODEL_ID]),
    )
    har = impl.bind_deployment_design(
        impl.HAR_MODEL_ID,
        impl.MODEL_COLUMNS[impl.HAR_MODEL_ID],
        other,
        design_matrix(columns, impl.MODEL_COLUMNS[impl.HAR_MODEL_ID]),
    )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_common_eligible_train_sample(
            identities, synthetic_log_target(columns), (base, har)
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.bind_common_eligible_train_sample(
            identities, synthetic_log_target(columns), (har, base)
        )


# --------------------------------------------------------------------------
# The pre-fit rank and identity gate
# --------------------------------------------------------------------------


def test_prefit_gate_opens_only_for_a_conforming_sample(sample: object) -> None:
    precheck = impl.precheck_deployment_designs(sample)
    assert precheck.may_fit
    assert precheck.identity_defects == ()
    assert precheck.structural_triggers == ()
    assert tuple(item.model_id for item in precheck.prechecks) == impl.MODEL_ORDER
    for item in precheck.prechecks:
        assert item.prefit_rank == item.fitted_columns
        assert item.row_count == 120
        assert item.prefit_condition_number is not None
    assert precheck.row_identity_sha256 == impl.row_identity_sha256(sample.row_identities)


def test_rank_deficiency_is_a_group_a_structural_trigger() -> None:
    precheck = impl.precheck_deployment_designs(rank_deficient_sample())
    assert not precheck.may_fit
    assert precheck.identity_defects == ()
    assert any(
        item.startswith("PREFIT_DESIGN_RANK_DEFICIENT") for item in precheck.structural_triggers
    )


def test_row_shortage_is_a_group_a_structural_trigger() -> None:
    precheck = impl.precheck_deployment_designs(synthetic_sample(6))
    assert not precheck.may_fit
    assert any(
        item.startswith("PREFIT_ROWS_NOT_GREATER_THAN_FITTED_COLUMNS")
        for item in precheck.structural_triggers
    )


def test_identity_drift_is_integrity_not_structural() -> None:
    precheck = impl.precheck_deployment_designs(mismatched_identity_sample())
    assert not precheck.may_fit
    assert any(
        item.startswith("COMMON_ELIGIBLE_ROW_IDENTITIES_DIFFER_FROM_SHARED_SET")
        for item in precheck.identity_defects
    )
    assert precheck.row_identity_sha256 is None


def test_prefit_gate_refuses_a_missing_or_reordered_model(sample: object) -> None:
    single = impl.CommonEligibleTrainSample(
        row_identities=sample.row_identities,
        log_target=sample.log_target,
        designs=(sample.designs[0],),
    )
    assert "DESIGNS_ARE_NOT_EXACTLY_BASE_THEN_HAR_IN_DECLARED_ORDER" in (
        impl.precheck_deployment_designs(single).identity_defects
    )
    swapped = impl.CommonEligibleTrainSample(
        row_identities=sample.row_identities,
        log_target=sample.log_target,
        designs=(sample.designs[1], sample.designs[0]),
    )
    assert impl.precheck_deployment_designs(swapped).identity_defects
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.precheck_deployment_designs({"designs": ()})


def test_no_solve_permit_or_counter_precedes_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """The decisive adversarial check: ``lstsq`` must be unreachable before the gate."""

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("numpy.linalg.lstsq was reached before the pre-fit gate")

    monkeypatch.setattr(numpy.linalg, "lstsq", explode)
    for candidate in (rank_deficient_sample(), mismatched_identity_sample(), synthetic_sample(6)):
        ledger = impl.run_ordered_deployment_fits(candidate)
        assert ledger.permits_consumed == 0
        assert ledger.fits_attempted == 0
        assert ledger.fits_succeeded == 0
        assert ledger.fits_ordered == ()
        assert ledger.seals_verified == 0
        assert ledger.seal_verification is None
        assert ledger.validation_state == "UNOPENED"


def test_group_a_stop_and_identity_stop_carry_the_right_terminal_class() -> None:
    structural = impl.run_ordered_deployment_fits(rank_deficient_sample())
    assert structural.terminal_class == impl.TerminalClass.UNDERPOWERED_STOP
    assert structural.structural_triggers and not structural.integrity_defects

    integrity = impl.run_ordered_deployment_fits(mismatched_identity_sample())
    assert integrity.terminal_class == impl.TerminalClass.INVALID_EVIDENCE
    assert integrity.integrity_defects and not integrity.structural_triggers


# --------------------------------------------------------------------------
# Deployment fits and model-local Duan
# --------------------------------------------------------------------------


def test_ordered_deployment_fits_consume_exactly_two_permits(deployment_ledger: object) -> None:
    assert deployment_ledger.budget_id == "CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1"
    assert deployment_ledger.permit_budget == 2
    assert deployment_ledger.permits_consumed == 2
    assert deployment_ledger.fits_attempted == 2
    assert deployment_ledger.fits_succeeded == 2
    assert deployment_ledger.seals_verified == 2
    assert deployment_ledger.terminal_class is None
    assert deployment_ledger.validation_state == "UNOPENED"
    assert tuple(fit.model_id for fit in deployment_ledger.fits_ordered) == impl.MODEL_ORDER


def test_recorded_diagnostics_agree_with_the_prefit_gate(deployment_ledger: object) -> None:
    observed = {item.model_id: item for item in deployment_ledger.precheck.prechecks}
    for fit in deployment_ledger.fits_ordered:
        assert fit.rank == observed[fit.model_id].prefit_rank == len(fit.columns)
        assert fit.train_row_count == observed[fit.model_id].row_count
        assert len(fit.singular_values) == len(fit.columns)
        assert math.isfinite(fit.condition_number) and fit.condition_number > 0.0


def test_duan_factors_are_model_local_and_never_shared(deployment_ledger: object) -> None:
    base_fit, har_fit = deployment_ledger.fits_ordered
    assert base_fit.duan_basis == har_fit.duan_basis == impl.DUAN_BASIS
    assert base_fit.duan_factor > 0.0 and har_fit.duan_factor > 0.0
    assert base_fit.duan_factor != har_fit.duan_factor
    assert float.fromhex(base_fit.duan_factor_hex) == base_fit.duan_factor
    assert base_fit.row_identity_sha256 == har_fit.row_identity_sha256


def test_duan_factor_is_the_exact_mean_of_exponentiated_own_residuals(
    sample: object, deployment_ledger: object
) -> None:
    for fit, design in zip(deployment_ledger.fits_ordered, sample.designs, strict=True):
        coefficients = numpy.ascontiguousarray(fit.coefficients, dtype=numpy.float64)
        residuals = sample.log_target - design.matrix @ coefficients
        assert fit.duan_factor == float(numpy.mean(numpy.exp(residuals)))


def test_deployment_forecast_applies_only_its_own_duan_factor(
    sample: object, deployment_ledger: object
) -> None:
    base_fit, har_fit = deployment_ledger.fits_ordered
    base_design, har_design = sample.designs
    forecast = impl.deployment_forecast(base_fit, base_design)
    coefficients = numpy.ascontiguousarray(base_fit.coefficients, dtype=numpy.float64)
    expected = numpy.exp(base_design.matrix @ coefficients) * numpy.float64(base_fit.duan_factor)
    assert numpy.array_equal(forecast, expected)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.deployment_forecast(base_fit, har_design)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.deployment_forecast(har_fit, base_design)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.deployment_forecast(base_fit, base_design.matrix)


def test_no_public_or_module_level_precheck_accepting_solve_bypass_exists() -> None:
    tree = ast.parse(IMPLEMENTATION_SOURCE.read_bytes().decode("utf-8"))
    top_level = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "fit_deployment_model" not in top_level
    assert "fit_deployment_model" not in impl.__all__
    assert not hasattr(impl, "fit_deployment_model")
    for name, function in top_level.items():
        parameters = {
            argument.arg for argument in (*function.args.posonlyargs, *function.args.args)
        }
        if "precheck" in parameters or "observation" in parameters:
            assert name == "precheck_deployment_designs"

    run = top_level["run_ordered_deployment_fits"]
    all_lstsq = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "lstsq"
    ]
    nested_lstsq = [
        node
        for node in ast.walk(run)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "lstsq"
    ]
    assert len(all_lstsq) == len(nested_lstsq) == 1


def test_a_failed_fit_consumes_its_permit_and_is_never_replaced(
    sample: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def failing(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise numpy.linalg.LinAlgError("synthetic deployment failure")

    monkeypatch.setattr(numpy.linalg, "lstsq", failing)
    ledger = impl.run_ordered_deployment_fits(sample)
    assert calls == 1
    assert ledger.permits_consumed == 1
    assert ledger.fits_attempted == 1
    assert ledger.fits_succeeded == 0
    assert ledger.seals_verified == 0
    assert ledger.terminal_class == impl.TerminalClass.INVALID_EVIDENCE
    assert ledger.validation_state == "UNOPENED"
    assert any(item.startswith("DEPLOYMENT_FIT_FAILED") for item in ledger.failure_reasons)


# --------------------------------------------------------------------------
# Independent seal verification and the distinct Grant 2 prerequisite
# --------------------------------------------------------------------------


def test_seal_verification_is_independently_derived(deployment_ledger: object) -> None:
    verification = impl.verify_deployment_seals(deployment_ledger.fits_ordered)
    assert verification.verified
    assert verification.seals_verified == 2
    assert verification.model_ids == impl.MODEL_ORDER
    assert verification.basis == impl.SEAL_VERIFICATION_BASIS
    assert verification.seal_digest == impl.deployment_seal_digest(
        deployment_ledger.fits_ordered
    )
    assert verification.seal_digest == deployment_ledger.seal_verification.seal_digest


def test_seal_verification_names_every_defect(deployment_ledger: object) -> None:
    base_fit, har_fit = deployment_ledger.fits_ordered
    assert impl.verify_deployment_seals(()).defects == (
        "SEALED_MODEL_SET_IS_NOT_EXACTLY_BASE_THEN_HAR",
    )
    assert impl.verify_deployment_seals((har_fit, base_fit)).defects == (
        "SEALED_MODEL_SET_IS_NOT_EXACTLY_BASE_THEN_HAR",
    )
    assert impl.verify_deployment_seals(("not-a-fit", har_fit)).defects == (
        "SEALED_RECORDS_ARE_NOT_DEPLOYMENT_FITS",
    )

    for mutation, expected in (
        ({"columns": ("intercept",)}, "SEAL_COLUMNS_NONCONFORMING"),
        ({"duan_factor": 0.0}, "SEAL_DUAN_FACTOR_NOT_POSITIVE_AND_FINITE"),
        ({"duan_factor": float("inf")}, "SEAL_DUAN_FACTOR_NOT_POSITIVE_AND_FINITE"),
        ({"duan_basis": "OTHER"}, "SEAL_DUAN_BASIS_NONCONFORMING"),
        ({"rank": 1}, "SEAL_RANK_IS_NOT_FULL_COLUMN_RANK"),
        ({"train_row_count": 1}, "SEAL_TRAIN_ROWS_NOT_GREATER_THAN_FITTED_COLUMNS"),
        ({"row_identity_sha256": "short"}, "SEAL_ROW_IDENTITY_DIGEST_IS_MALFORMED"),
        ({"duan_factor_hex": "0x1.0p+0"}, "SEAL_DUAN_FACTOR_HEX_RECORD_DOES_NOT_RECONCILE"),
    ):
        broken = dataclasses.replace(base_fit, **mutation)
        verification = impl.verify_deployment_seals((broken, har_fit))
        assert not verification.verified
        assert verification.seal_digest is None
        assert any(defect.startswith(expected) for defect in verification.defects)

    shared = dataclasses.replace(
        har_fit,
        duan_factor=base_fit.duan_factor,
        duan_factor_hex=base_fit.duan_factor_hex,
    )
    assert "SEALED_DUAN_FACTORS_ARE_NOT_MODEL_LOCAL" in impl.verify_deployment_seals(
        (base_fit, shared)
    ).defects

    foreign = dataclasses.replace(har_fit, row_identity_sha256=impl.row_identity_sha256(("X",)))
    assert "SEALED_MODELS_WERE_NOT_ESTIMATED_ON_THE_SAME_ELIGIBLE_ROWS" in (
        impl.verify_deployment_seals((base_fit, foreign)).defects
    )


def test_implementation_slice_exports_no_grant_two_minter_or_carrier() -> None:
    for name in (
        "Grant2Prerequisite",
        "bind_grant2_prerequisite",
        "GRANT2_ID",
        "GRANT2_REQUIRED_CITATIONS_ORDERED",
    ):
        assert name not in impl.__all__
        assert not hasattr(impl, name)


# --------------------------------------------------------------------------
# Golden projection compared byte for byte against the ratified binding
# --------------------------------------------------------------------------


def test_recomputed_projection_matches_the_ratified_binding(golden_verification: object) -> None:
    assert golden_verification.verified, (
        golden_verification.replay_mismatches,
        golden_verification.binding_mismatches,
    )
    assert golden_verification.replay_mismatches == ()
    assert golden_verification.binding_mismatches == ()
    assert golden_verification.projection_id == impl.GOLDEN_PROJECTION_ID
    assert golden_verification.binding_schema == impl.RATIFIED_TOOLING_BINDING_SCHEMA
    assert golden_verification.basis == impl.GOLDEN_COMPARISON_BASIS
    assert golden_verification.binding_document_sha256 == impl.sha256_hex(
        RATIFIED_BINDING_BYTES
    )
    assert impl.golden_binding_refusal_reasons(golden_verification) == ()


def test_the_comparison_is_against_the_ratified_fixture_not_a_second_copy(
    golden_verification: object, golden_projection: tuple[dict[str, object], bytes]
) -> None:
    record, raw = golden_projection
    document = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    fixture = document["payload"]["golden_fixture"]
    assert golden_verification.observed_raw_sha256 == impl.sha256_hex(raw)
    assert fixture["raw_material_sha256"] == record["raw_material_sha256"]
    assert fixture["row_count"] == record["row_count"]
    assert fixture["inputs_sha256"] == record["inputs_sha256"]
    assert fixture["row_losses_sha256"] == record["row_losses_sha256"]
    assert fixture["session_aggregates_sha256"] == record["session_aggregates_sha256"]
    assert fixture["means_hex"]["relative_reduction"] == (
        record["means_hex"]["relative_qlike_reduction"]
    )
    for ratified, recomputed in zip(
        fixture["blocks_ordered"], record["blocks_ordered"], strict=True
    ):
        assert ratified["block_length"] == recomputed["block_length"]
        assert ratified["validation_seed"] == recomputed["validation_seed"]
        assert ratified["blocks_needed"] == recomputed["blocks_needed"]
        assert ratified["draw_matrix_sha256"] == recomputed["draw_matrix_sha256"]
        assert ratified["replicate_vector_sha256"] == recomputed["replicate_vector_sha256"]
        assert ratified["quantile_hex"] == recomputed["lower_bound_hex"]


def test_a_one_byte_mutation_of_the_ratified_binding_is_refused() -> None:
    mutated = bytearray(RATIFIED_BINDING_BYTES)
    mutated[-2] = mutated[-2] ^ 0x01
    verification = impl.verify_golden_projection_against_ratified_binding(bytes(mutated))
    assert not verification.verified
    assert verification.binding_mismatches
    assert impl.golden_binding_refusal_reasons(verification)


def test_a_drifted_fixture_digest_in_the_binding_is_refused() -> None:
    document = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    payload = document["payload"]
    payload["golden_fixture"]["raw_material_sha256"] = "0" * 64
    document["payload_sha256"] = impl.sha256_hex(
        impl.governed_binding_canonical_bytes(payload)
    )
    rendered = impl.governed_binding_canonical_bytes(document)
    verification = impl.verify_golden_projection_against_ratified_binding(rendered)
    assert not verification.verified
    assert "RATIFIED_FIXTURE_RAW_MATERIAL_DIGEST_DIFFERS" in verification.binding_mismatches


def test_a_non_canonical_or_unreconciled_binding_is_refused() -> None:
    document = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    spaced = (json.dumps(document, sort_keys=True) + "\n").encode("utf-8")
    spaced_verification = impl.verify_golden_projection_against_ratified_binding(spaced)
    assert "RATIFIED_BINDING_BYTES_ARE_NOT_THE_GOVERNED_CANONICAL_RENDERING" in (
        spaced_verification.binding_mismatches
    )

    forged = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    forged["payload_sha256"] = "0" * 64
    rendered = impl.governed_binding_canonical_bytes(forged)
    digest_verification = impl.verify_golden_projection_against_ratified_binding(rendered)
    assert "RATIFIED_BINDING_PAYLOAD_DIGEST_DOES_NOT_RECONCILE" in (
        digest_verification.binding_mismatches
    )

    wrong_schema = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    wrong_schema["schema"] = "OTHER"
    schema_verification = impl.verify_golden_projection_against_ratified_binding(
        impl.governed_binding_canonical_bytes(wrong_schema)
    )
    assert "RATIFIED_BINDING_SCHEMA_DIFFERS" in schema_verification.binding_mismatches

    extra_key = json.loads(RATIFIED_BINDING_BYTES.decode("utf-8"))
    extra_key["extra"] = 1
    key_verification = impl.verify_golden_projection_against_ratified_binding(
        impl.governed_binding_canonical_bytes(extra_key)
    )
    assert "RATIFIED_BINDING_DOCUMENT_KEY_SET_IS_NOT_CLOSED" in (
        key_verification.binding_mismatches
    )

    assert impl.verify_golden_projection_against_ratified_binding(
        b"not json"
    ).binding_mismatches == ("RATIFIED_BINDING_IS_NOT_DECODABLE_CANONICAL_JSON",)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.verify_golden_projection_against_ratified_binding("not bytes")


def test_a_verification_record_cannot_be_edited_after_construction(
    golden_verification: object,
) -> None:
    forged = dataclasses.replace(
        golden_verification, verified=True, binding_mismatches=(), replay_mismatches=()
    )
    forged = dataclasses.replace(forged, binding_schema="OTHER")
    reasons = impl.golden_binding_refusal_reasons(forged)
    assert "GOLDEN_FIXTURE_BINDING_VERIFICATION_TOKEN_DOES_NOT_RECONCILE" in reasons
    assert "GOLDEN_FIXTURE_BINDING_SCHEMA_IS_NOT_THE_RATIFIED_SCHEMA" in reasons
    assert impl.golden_binding_refusal_reasons(True) == (
        "GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_ABSENT_OR_NOT_A_VERIFICATION_RECORD",
    )
    assert impl.golden_binding_refusal_reasons(None)


def test_golden_projection_inputs_are_fixed_and_synthetic(
    golden_projection: tuple[dict[str, object], bytes],
) -> None:
    record, raw = golden_projection
    identifiers, actual, base, har = impl.golden_projection_inputs()
    assert impl.golden_projection_session_row_counts() == tuple(
        4 + (index % 3) for index in range(24)
    )
    assert len(identifiers) == actual.size == base.size == har.size == record["row_count"]
    assert record["content"] == "SYNTHETIC_ONLY"
    assert record["storage"] == "IN_MEMORY_ONLY"
    assert record["session_count"] == impl.GOLDEN_PROJECTION_SESSION_COUNT
    assert record["raw_material_byte_count"] == len(raw)
    assert record["raw_material_sha256"] == impl.sha256_hex(raw)
    assert record["sign_policy"] == impl.REPLICATE_SIGN_POLICY


# --------------------------------------------------------------------------
# Pure C0 / C0V refusal assessments
# --------------------------------------------------------------------------


def _assert_grants_nothing(assessment: object) -> None:
    assert assessment.terminal_class is None
    assert assessment.permits_consumed == 0
    assert assessment.fits_performed == 0
    assert assessment.validation_state == "UNOPENED"
    assert assessment.witness_created is False
    assert assessment.authorizes_refit is False
    assert assessment.classification == impl.PRE_START_CLASSIFICATION
    assert assessment.effect == impl.CHECKPOINT_EFFECT


def test_c0_pass_grants_nothing_at_all(golden_verification: object) -> None:
    assessment = impl.assess_c0(
        sealed_identity=synthetic_identity(),
        pre_permit_identity=synthetic_identity(),
        golden_binding_verification=golden_verification,
    )
    assert assessment.checkpoint == "C0"
    assert assessment.outcome == impl.CHECKPOINT_PASS
    assert not assessment.refused
    assert assessment.refusal_reasons == ()
    _assert_grants_nothing(assessment)


def test_c0_refuses_on_runtime_mismatch_and_consumes_no_permit(
    golden_verification: object,
) -> None:
    assessment = impl.assess_c0(
        sealed_identity=synthetic_identity("A"),
        pre_permit_identity=synthetic_identity("B"),
        golden_binding_verification=golden_verification,
    )
    assert assessment.refused
    assert "IMMEDIATE_RE_RECORD_NOT_EXACTLY_EQUAL_TO_SEALED_IDENTITY" in (
        assessment.refusal_reasons
    )
    _assert_grants_nothing(assessment)


def test_c0_requires_the_ratified_golden_binding_not_a_caller_boolean(
    golden_verification: object,
) -> None:
    for substitute in (True, False, None, "VERIFIED", 1):
        assessment = impl.assess_c0(
            sealed_identity=synthetic_identity(),
            pre_permit_identity=synthetic_identity(),
            golden_binding_verification=substitute,
        )
        assert assessment.refused
        assert "GOLDEN_FIXTURE_BINDING_VERIFICATION_IS_ABSENT_OR_NOT_A_VERIFICATION_RECORD" in (
            assessment.refusal_reasons
        )
        _assert_grants_nothing(assessment)

    mutated = bytearray(RATIFIED_BINDING_BYTES)
    mutated[-2] = mutated[-2] ^ 0x01
    failed = impl.verify_golden_projection_against_ratified_binding(bytes(mutated))
    assessment = impl.assess_c0(
        sealed_identity=synthetic_identity(),
        pre_permit_identity=synthetic_identity(),
        golden_binding_verification=failed,
    )
    assert assessment.refused
    assert "GOLDEN_FIXTURE_BYTEWISE_REPLAY_FAILED" in assessment.refusal_reasons
    assert golden_verification.verified


def test_c0_reports_schema_defects_on_either_side(golden_verification: object) -> None:
    broken = synthetic_identity()
    del broken["numpy"]
    sealed_defect = impl.assess_c0(
        sealed_identity=broken,
        pre_permit_identity=synthetic_identity(),
        golden_binding_verification=golden_verification,
    )
    assert "SEALED_IDENTITY_SCHEMA_NONCONFORMING" in sealed_defect.refusal_reasons
    record_defect = impl.assess_c0(
        sealed_identity=synthetic_identity(),
        pre_permit_identity=broken,
        golden_binding_verification=golden_verification,
    )
    assert "RE_RECORD_IDENTITY_SCHEMA_NONCONFORMING" in record_defect.refusal_reasons


def _c0v(
    golden_verification: object,
    fits: object,
    seal_verification: object,
    claim: object = None,
    *,
    sealed_c0v: object = None,
    pre_witness: object = None,
) -> object:
    return impl.assess_c0v(
        sealed_c0_identity=synthetic_identity(),
        sealed_c0v_identity=sealed_c0v or synthetic_identity(),
        pre_witness_identity=pre_witness or synthetic_identity(),
        golden_binding_verification=golden_verification,
        sealed_fits=fits,
        seal_verification=seal_verification,
        untrusted_grant2_claim=claim,
    )


def test_c0v_correct_seals_are_readiness_only_without_owner_grant_two(
    golden_verification: object, deployment_ledger: object
) -> None:
    fits = deployment_ledger.fits_ordered
    verification = impl.verify_deployment_seals(fits)
    assessment = _c0v(golden_verification, fits, verification)
    assert assessment.checkpoint == "C0V"
    assert assessment.refused
    assert assessment.refusal_reasons == (impl.SEPARATE_OWNER_GRANT_2_REFUSAL,)
    assert assessment.seal_digest is None
    assert assessment.grant_id is None
    _assert_grants_nothing(assessment)


def test_c0v_cannot_be_satisfied_by_any_caller_grant_two_spoof(
    golden_verification: object, deployment_ledger: object
) -> None:
    fits = deployment_ledger.fits_ordered
    verification = impl.verify_deployment_seals(fits)

    class Lookalike:
        grant_id = "GRANT_2"
        cited_supersessions = ("citation-a", "citation-b")
        seal_digest = verification.seal_digest

    for spoof in (
        True,
        False,
        {"grant_id": "GRANT_2", "seal_digest": verification.seal_digest},
        ("citation-a", "citation-b"),
        verification.seal_digest,
        Lookalike(),
    ):
        assessment = _c0v(golden_verification, fits, verification, spoof)
        assert assessment.refused
        assert impl.SEPARATE_OWNER_GRANT_2_REFUSAL in assessment.refusal_reasons
        assert assessment.grant_id is None
        assert assessment.seal_digest is None
        _assert_grants_nothing(assessment)

    everything_asserted = _c0v(golden_verification, True, True, True)
    assert "SEALED_DEPLOYMENT_FITS_ARE_ABSENT_OR_NONCONFORMING" in (
        everything_asserted.refusal_reasons
    )

    forged_verification = dataclasses.replace(
        impl.verify_deployment_seals(()), verified=True, seals_verified=2, seal_digest="0" * 64
    )
    forged = _c0v(golden_verification, fits, forged_verification, None)
    assert forged.refused
    assert "SUPPLIED_SEAL_VERIFICATION_IS_NOT_BOUND_TO_THESE_EXACT_SEALED_FITS" in (
        forged.refusal_reasons
    )


def test_c0v_refuses_unverifiable_or_foreign_seals(
    golden_verification: object, deployment_ledger: object
) -> None:
    base_fit, har_fit = deployment_ledger.fits_ordered
    verification = impl.verify_deployment_seals((base_fit, har_fit))

    single = _c0v(golden_verification, (base_fit,), verification)
    assert "SEALED_DEPLOYMENT_FITS_ARE_ABSENT_OR_NONCONFORMING" in single.refusal_reasons

    broken = dataclasses.replace(har_fit, duan_basis="OTHER")
    unverifiable = _c0v(golden_verification, (base_fit, broken), verification)
    assert "DEPLOYMENT_SEALS_NOT_INDEPENDENTLY_VERIFIED" in unverifiable.refusal_reasons
    assert unverifiable.seal_digest is None

    other_fits = impl.run_ordered_deployment_fits(synthetic_sample(140)).fits_ordered
    foreign_verification = impl.verify_deployment_seals(other_fits)
    reused = _c0v(golden_verification, (base_fit, har_fit), foreign_verification)
    assert "SUPPLIED_SEAL_VERIFICATION_IS_NOT_BOUND_TO_THESE_EXACT_SEALED_FITS" in (
        reused.refusal_reasons
    )


def test_c0v_requires_identity_equality_with_the_sealed_c0_identity(
    golden_verification: object, deployment_ledger: object
) -> None:
    fits = deployment_ledger.fits_ordered
    verification = impl.verify_deployment_seals(fits)
    drifted = _c0v(
        golden_verification,
        fits,
        verification,
        sealed_c0v=synthetic_identity("B"),
        pre_witness=synthetic_identity("B"),
    )
    assert drifted.refused
    assert "SEALED_C0V_IDENTITY_NOT_EXACTLY_EQUAL_TO_SEALED_C0_IDENTITY" in (
        drifted.refusal_reasons
    )
    self_drift = _c0v(
        golden_verification, fits, verification, pre_witness=synthetic_identity("C")
    )
    assert "IMMEDIATE_RE_RECORD_NOT_EXACTLY_EQUAL_TO_SEALED_IDENTITY" in (
        self_drift.refusal_reasons
    )


def test_checkpoint_refusal_is_never_a_scientific_terminal_class(
    golden_verification: object,
) -> None:
    refusals = (
        impl.assess_c0(
            sealed_identity=synthetic_identity("A"),
            pre_permit_identity=synthetic_identity("B"),
            golden_binding_verification=golden_verification,
        ),
        _c0v(golden_verification, True, True, True),
    )
    for assessment in refusals:
        assert assessment.refused
        assert assessment.terminal_class is None
        assert assessment.outcome == impl.PRE_START_PROCEDURAL_REFUSAL
        assert assessment.classification == impl.PRE_START_CLASSIFICATION
        for value in impl.TerminalClass:
            assert value.value not in assessment.refusal_reasons


# --------------------------------------------------------------------------
# float64 operand discipline and QLIKE decision metrics
# --------------------------------------------------------------------------


def test_float64_vector_and_matrix_discipline_is_enforced() -> None:
    good = numpy.ascontiguousarray([1.0, 2.0], dtype=numpy.float64)
    assert impl.require_float64_vector(good, name="v") is good
    for bad in (
        [1.0, 2.0],
        numpy.asarray([1, 2], dtype=numpy.int64),
        numpy.asarray([], dtype=numpy.float64),
        numpy.asarray([[1.0, 2.0]], dtype=numpy.float64),
        numpy.asarray([1.0, numpy.nan], dtype=numpy.float64),
        numpy.asarray([1.0, 2.0, 3.0, 4.0], dtype=numpy.float64)[::2],
    ):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.require_float64_vector(bad, name="v")

    matrix = numpy.ascontiguousarray([[1.0, 2.0], [3.0, 4.0]], dtype=numpy.float64)
    assert impl.require_float64_matrix(matrix, name="m") is matrix
    for bad in (
        good,
        numpy.asarray([[1, 2]], dtype=numpy.int64),
        numpy.asarray([[numpy.inf, 1.0]], dtype=numpy.float64),
        matrix.T,
    ):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.require_float64_matrix(bad, name="m")


def test_left_fold_is_a_strict_stored_order_traversal() -> None:
    values = numpy.ascontiguousarray([1e16, -1e16, 1.0], dtype=numpy.float64)
    expected = numpy.float64(0.0)
    for value in values:
        expected = numpy.float64(expected + value)
    assert impl.left_fold(values) == expected
    assert impl.left_fold(values) != impl.left_fold(values[::-1])
    assert impl.left_fold(numpy.asarray([], dtype=numpy.float64)) == numpy.float64(0.0)


def test_qlike_row_losses_match_the_exact_ufunc_sequence() -> None:
    actual = numpy.ascontiguousarray([1.0, 2.0, 3.0], dtype=numpy.float64)
    base = numpy.ascontiguousarray([0.9, 2.2, 2.5], dtype=numpy.float64)
    har = numpy.ascontiguousarray([1.1, 1.9, 3.3], dtype=numpy.float64)
    losses = impl.compute_row_losses(actual, base, har)
    r_base = actual / base
    r_har = actual / har
    assert numpy.array_equal(
        losses.loss_base, r_base - numpy.log(r_base) - numpy.float64(1.0)
    )
    assert numpy.array_equal(losses.loss_har, r_har - numpy.log(r_har) - numpy.float64(1.0))
    assert numpy.array_equal(losses.difference, losses.loss_base - losses.loss_har)
    assert losses.row_count == 3


def test_qlike_identity_forecast_is_exactly_zero_loss() -> None:
    actual = numpy.ascontiguousarray([0.5, 1.5, 2.5], dtype=numpy.float64)
    losses = impl.compute_row_losses(actual, actual, actual)
    assert numpy.all(losses.loss_base == 0.0)
    assert numpy.all(losses.difference == 0.0)
    metrics = impl.compute_decision_metrics(losses)
    assert metrics.mean_base == 0.0 and metrics.mean_difference == 0.0
    assert not metrics.scored
    assert "MEAN_BASE_NOT_FINITE_AND_STRICTLY_POSITIVE" in metrics.undefined_reasons


def test_row_improvement_sign_favours_har_when_har_is_closer() -> None:
    actual = numpy.ascontiguousarray([1.0], dtype=numpy.float64)
    far = numpy.ascontiguousarray([2.0], dtype=numpy.float64)
    near = numpy.ascontiguousarray([1.01], dtype=numpy.float64)
    assert impl.compute_row_losses(actual, far, near).difference[0] > 0.0
    assert impl.compute_row_losses(actual, near, far).difference[0] < 0.0


def test_row_losses_refuse_nonpositive_nonfinite_and_mismatched_operands() -> None:
    actual = numpy.ascontiguousarray([1.0, 2.0], dtype=numpy.float64)
    for bad in (
        numpy.ascontiguousarray([0.0, 1.0], dtype=numpy.float64),
        numpy.ascontiguousarray([-1.0, 1.0], dtype=numpy.float64),
        numpy.ascontiguousarray([numpy.inf, 1.0], dtype=numpy.float64),
        numpy.ascontiguousarray([1.0], dtype=numpy.float64),
    ):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.compute_row_losses(actual, bad, actual)
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.compute_row_losses(actual, actual, bad)


def test_decision_metrics_are_stored_order_left_folds_divided_by_n() -> None:
    actual = numpy.ascontiguousarray([1.0, 2.0, 3.0, 4.0], dtype=numpy.float64)
    base = numpy.ascontiguousarray([0.5, 1.0, 1.5, 2.0], dtype=numpy.float64)
    har = numpy.ascontiguousarray([0.9, 1.9, 2.9, 3.9], dtype=numpy.float64)
    losses = impl.compute_row_losses(actual, base, har)
    metrics = impl.compute_decision_metrics(losses)
    count = numpy.float64(losses.row_count)
    assert metrics.mean_base == float(numpy.float64(impl.left_fold(losses.loss_base) / count))
    assert metrics.mean_har == float(numpy.float64(impl.left_fold(losses.loss_har) / count))
    assert metrics.mean_difference == float(
        numpy.float64(impl.left_fold(losses.difference) / count)
    )
    assert metrics.scored
    assert metrics.relative_qlike_reduction == float(
        numpy.float64(
            numpy.float64(numpy.float64(metrics.mean_base) - numpy.float64(metrics.mean_har))
            / numpy.float64(metrics.mean_base)
        )
    )
    assert float.fromhex(metrics.mean_difference_hex) == metrics.mean_difference
    assert metrics.aggregation == "EQUAL_ROW_WEIGHTED_MEAN_OVER_COMMON_ELIGIBLE_ROWS"
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.compute_decision_metrics("not-a-record")


def test_a_nonfinite_d_makes_the_stage_unscored() -> None:
    nonfinite = numpy.ascontiguousarray([numpy.inf] * 4, dtype=numpy.float64)
    losses = impl.RowLosses(
        row_count=4,
        loss_base=numpy.ascontiguousarray([1.0, 1.0, 1.0, 1.0], dtype=numpy.float64),
        loss_har=numpy.ascontiguousarray([0.5, 0.5, 0.5, 0.5], dtype=numpy.float64),
        difference=nonfinite,
    )
    metrics = impl.compute_decision_metrics(losses)
    assert not metrics.scored
    assert "ROW_IMPROVEMENT_ACCUMULATOR_NOT_FINITE" in metrics.undefined_reasons
    assert "MEAN_DIFFERENCE_D_NOT_FINITE" in metrics.undefined_reasons
    assert metrics.relative_qlike_reduction is None


def test_equal_row_weighting_is_not_mean_of_session_means() -> None:
    identifiers = ("A", "A", "A", "B")
    difference = numpy.ascontiguousarray([1.0, 1.0, 1.0, 5.0], dtype=numpy.float64)
    aggregates = impl.build_session_aggregates(identifiers, difference)
    row_weighted = float(impl.left_fold(difference) / numpy.float64(4))
    session_means = sum(
        item.improvement_sum / item.row_count for item in aggregates.sessions
    ) / len(aggregates.sessions)
    assert row_weighted != session_means


# --------------------------------------------------------------------------
# Session aggregates
# --------------------------------------------------------------------------


def test_session_aggregates_follow_first_occurrence_and_preserve_row_order() -> None:
    identifiers = ("A", "A", "B", "B", "B")
    difference = numpy.ascontiguousarray([1.0, 2.0, 3.0, 4.0, 5.0], dtype=numpy.float64)
    aggregates = impl.build_session_aggregates(identifiers, difference)
    assert tuple(item.session_id for item in aggregates.sessions) == ("A", "B")
    assert tuple(item.row_count for item in aggregates.sessions) == (2, 3)
    assert aggregates.session_count == 2
    assert aggregates.row_counts.dtype == numpy.dtype(numpy.int64)
    assert aggregates.improvement_sums.dtype == numpy.dtype(numpy.float64)
    assert aggregates.sessions[0].improvement_sum == 3.0
    assert float.fromhex(aggregates.sessions[1].improvement_sum_hex) == 12.0


def test_session_rows_must_be_contiguous_and_non_repeating() -> None:
    difference = numpy.ascontiguousarray([1.0, 2.0, 3.0], dtype=numpy.float64)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_session_aggregates(("A", "B", "A"), difference)


def test_session_aggregates_refuse_malformed_identities_and_extents() -> None:
    difference = numpy.ascontiguousarray([1.0, 2.0], dtype=numpy.float64)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_session_aggregates(("A",), difference)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_session_aggregates(("A", ""), difference)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_session_aggregates(("A", 2), difference)


# --------------------------------------------------------------------------
# Frozen Validation bootstrap
# --------------------------------------------------------------------------


def test_frozen_seed_schedule_is_exact() -> None:
    for length in impl.BOOTSTRAP_BLOCK_LENGTHS_ORDERED:
        assert impl.pooled_seed(length) == impl.MASTER_SEED + 90000 + length
        assert impl.validation_seed(length) == impl.pooled_seed(length) + 1000
    assert impl.validation_seed(5) == 20351814
    for bad in (0, -1, 1.5, True, "5"):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.pooled_seed(bad)


def test_draw_matrix_is_deterministic_non_circular_and_bounded() -> None:
    matrix = impl.build_draw_matrix(24, 5, 10, impl.validation_seed(5))
    again = impl.build_draw_matrix(24, 5, 10, impl.validation_seed(5))
    assert numpy.array_equal(matrix, again)
    assert matrix.dtype == numpy.dtype(numpy.int32)
    assert matrix.shape == (10, 24)
    assert matrix.flags["C_CONTIGUOUS"]
    assert int(matrix.min()) >= 0 and int(matrix.max()) <= 23
    row = matrix[0]
    for start in range(0, 20, 5):
        block = row[start : start + 5]
        assert list(block) == list(range(int(block[0]), int(block[0]) + 5))
        assert int(block[0]) <= 24 - 5


def test_draw_matrices_do_not_share_rng_state_between_block_lengths() -> None:
    first = impl.build_draw_matrix(24, 5, 4, impl.validation_seed(5))
    second = impl.build_draw_matrix(24, 1, 4, impl.validation_seed(1))
    assert not numpy.array_equal(first[:, :1], second[:, :1])


def test_draw_matrix_refuses_malformed_extents() -> None:
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_draw_matrix(3, 5, 10, 1)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_draw_matrix(24, 5, 0, 1)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_draw_matrix(24, 5, 10, -1)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_draw_matrix(24, 5, 10, True)


def test_negative_zero_and_positive_finite_replicates_are_all_admitted() -> None:
    counts = numpy.ascontiguousarray([2, 2, 2], dtype=numpy.int64)
    draw = numpy.ascontiguousarray([[0, 1, 2], [0, 0, 0], [2, 2, 2]], dtype=numpy.int32)
    for sums, expected_sign in (
        ([-1.0, -1.0, -1.0], -1.0),
        ([0.0, 0.0, 0.0], 0.0),
        ([1.0, 1.0, 1.0], 1.0),
    ):
        vector = impl.compute_replicate_vector(
            numpy.ascontiguousarray(sums, dtype=numpy.float64), counts, draw
        )
        assert vector.dtype == numpy.dtype(numpy.float64)
        assert bool(numpy.all(numpy.isfinite(vector)))
        assert bool(numpy.all(numpy.sign(vector) == expected_sign))


def test_replicate_denominator_must_be_positive_and_finite() -> None:
    sums = numpy.ascontiguousarray([1.0, 1.0], dtype=numpy.float64)
    draw = numpy.ascontiguousarray([[0, 1]], dtype=numpy.int32)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.compute_replicate_vector(
            sums, numpy.ascontiguousarray([0, 1], dtype=numpy.int64), draw
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.compute_replicate_vector(
            sums, numpy.ascontiguousarray([-1, 1], dtype=numpy.int64), draw
        )


def test_replicate_vector_refuses_malformed_draw_matrices() -> None:
    sums = numpy.ascontiguousarray([1.0, 1.0], dtype=numpy.float64)
    counts = numpy.ascontiguousarray([1, 1], dtype=numpy.int64)
    for bad in (
        numpy.ascontiguousarray([[0, 1]], dtype=numpy.int64),
        numpy.ascontiguousarray([0, 1], dtype=numpy.int32),
        numpy.ascontiguousarray([[0, 1, 0]], dtype=numpy.int32),
        numpy.ascontiguousarray([[0, 2]], dtype=numpy.int32),
        numpy.ascontiguousarray([[-1, 1]], dtype=numpy.int32),
    ):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.compute_replicate_vector(sums, counts, bad)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.compute_replicate_vector(
            sums, numpy.ascontiguousarray([1.0, 1.0], dtype=numpy.float64), sums
        )


@pytest.fixture(scope="module")
def negative_bootstrap() -> tuple[object, ...]:
    return impl.run_frozen_validation_bootstrap(synthetic_session_aggregates(sign=-1.0))


def test_bootstrap_runs_exactly_three_ordered_block_lengths(
    negative_bootstrap: tuple[object, ...],
) -> None:
    assert tuple(item.block_length for item in negative_bootstrap) == (5, 1, 20)
    assert tuple(item.role for item in negative_bootstrap) == (
        "PRIMARY",
        "DIAGNOSTIC",
        "DIAGNOSTIC",
    )
    for item in negative_bootstrap:
        assert item.replications == 2000
        assert item.validation_seed == impl.validation_seed(item.block_length)
        assert item.pooled_seed == impl.pooled_seed(item.block_length)
        assert item.blocks_needed == -(-24 // item.block_length)
        assert item.sign_policy == impl.REPLICATE_SIGN_POLICY
        assert item.replicates.shape == (2000,)
        assert item.draw_matrix.shape == (2000, 24)


def test_an_all_negative_sample_is_scored_not_invalidated(
    negative_bootstrap: tuple[object, ...],
) -> None:
    primary = impl.primary_block_result(negative_bootstrap)
    assert primary.block_length == 5
    assert primary.negative_replicates == 2000
    assert primary.zero_replicates == 0 and primary.positive_replicates == 0
    assert math.isfinite(primary.lower_bound) and primary.lower_bound < 0.0
    assert float.fromhex(primary.lower_bound_hex) == primary.lower_bound


def test_bootstrap_lower_bound_uses_the_single_authoritative_quantile_call(
    negative_bootstrap: tuple[object, ...],
) -> None:
    for item in negative_bootstrap:
        assert item.lower_bound == float(
            numpy.quantile(item.replicates, numpy.float64(0.05), method="linear")
        )


def test_primary_block_result_is_never_replaced_by_a_diagnostic(
    negative_bootstrap: tuple[object, ...],
) -> None:
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.primary_block_result(tuple(reversed(negative_bootstrap)))
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.primary_block_result(negative_bootstrap[:1])


def test_bootstrap_refuses_a_table_smaller_than_a_block_length() -> None:
    identifiers = tuple(f"S{index:02d}" for index in range(10))
    difference = numpy.ascontiguousarray([0.1] * 10, dtype=numpy.float64)
    aggregates = impl.build_session_aggregates(identifiers, difference)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.run_frozen_validation_bootstrap(aggregates)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.run_frozen_validation_bootstrap("not-a-table")


# --------------------------------------------------------------------------
# Exact within-session ACF and its derived session table
# --------------------------------------------------------------------------


def test_rho_null_is_exact_and_domain_bound() -> None:
    assert impl.rho_null(1) == 0.75
    assert impl.rho_null(4) == 0.0
    assert impl.rho_null(8) == 0.0
    for bad in (0, 9, -1, 1.0, True, "1"):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.rho_null(bad)


def test_supported_acf_defines_every_lag_and_discloses_design_effect() -> None:
    assessment = impl.assess_within_session_acf(synthetic_acf_rows())
    assert assessment.integrity_defects == ()
    assert assessment.support_undefined_lags == ()
    assert len(assessment.lags) == 8
    assert assessment.row_count == 36
    assert assessment.session_ids_ordered == ("SESSION_00", "SESSION_01", "SESSION_02")
    assert assessment.session_row_counts == (12, 12, 12)
    assert assessment.unique_session_count == 3
    assert assessment.session_basis.startswith("DERIVED_FROM_STRICTLY_CHRONOLOGICAL")
    for item in assessment.lags:
        assert item.rho_observed is not None and math.isfinite(item.rho_observed)
        assert item.support_reason is None
        assert item.excess == item.rho_observed - impl.rho_null(item.lag)
        assert item.pair_count == 3 * (12 - item.lag)
    expected = max(
        1.0, 1.0 + 2.0 * sum(max(item.rho_observed, 0.0) for item in assessment.lags)
    )
    assert assessment.design_effect == expected
    assert assessment.effective_sample_size == assessment.row_count / expected
    assert assessment.disclosure.startswith("DESIGN_EFFECT_AND_ESS_ARE_DISCLOSURE_ONLY")


def test_zero_spread_is_missing_support_and_never_a_sentinel_number() -> None:
    assessment = impl.assess_within_session_acf(synthetic_acf_rows(constant=True))
    assert assessment.integrity_defects == ()
    assert assessment.support_undefined_lags == impl.ACF_LAGS
    for item in assessment.lags:
        assert item.rho_observed is None
        assert item.excess is None
        assert item.support_reason == "ACF_LAG_SUPPORT_UNDEFINED"
    assert assessment.design_effect is None
    assert assessment.effective_sample_size is None


def test_fewer_than_two_pairs_is_missing_support() -> None:
    assessment = impl.assess_within_session_acf(synthetic_acf_rows(sessions=1, per_session=2))
    assert assessment.integrity_defects == ()
    assert assessment.support_undefined_lags == impl.ACF_LAGS
    assert assessment.unique_session_count == 1


def test_only_exact_fifteen_minute_multiples_are_paired() -> None:
    start = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    rows = (
        impl.AcfRow("S", start, 1.0),
        impl.AcfRow("S", start + timedelta(minutes=16), 2.0),
        impl.AcfRow("S", start + timedelta(minutes=33), 3.0),
    )
    assessment = impl.assess_within_session_acf(rows)
    assert assessment.lags[0].pair_count == 0
    assert assessment.lags[0].support_reason == "ACF_LAG_SUPPORT_UNDEFINED"


def test_pairs_are_never_formed_across_sessions() -> None:
    start = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    rows = (
        impl.AcfRow("A", start, 1.0),
        impl.AcfRow("B", start + timedelta(minutes=15), 2.0),
        impl.AcfRow("C", start + timedelta(minutes=30), 3.0),
    )
    assessment = impl.assess_within_session_acf(rows)
    assert assessment.unique_session_count == 3
    assert all(item.pair_count == 0 for item in assessment.lags)


def test_acf_integrity_defects_are_reported_without_any_lag_result() -> None:
    start = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    cases = {
        "ACF_DECISION_TIME_IS_NOT_TIMEZONE_AWARE": (
            impl.AcfRow("S", start.replace(tzinfo=None), 1.0),
        ),
        "ACF_RV_FWD_60_IS_NONFINITE": (impl.AcfRow("S", start, float("nan")),),
        "ACF_RV_FWD_60_IS_NONPOSITIVE": (impl.AcfRow("S", start, 0.0),),
        "ACF_RV_FWD_60_IS_NOT_NUMERIC": (impl.AcfRow("S", start, "1.0"),),
        "ACF_SESSION_IDENTITY_IS_EMPTY": (impl.AcfRow("", start, 1.0),),
        "ACF_DUPLICATE_SESSION_DECISION_KEY": (
            impl.AcfRow("S", start, 1.0),
            impl.AcfRow("S", start, 2.0),
        ),
        "VALIDATION_ROWS_NOT_STRICTLY_CHRONOLOGICAL": (
            impl.AcfRow("S", start + timedelta(minutes=15), 1.0),
            impl.AcfRow("S", start, 2.0),
        ),
        "ACF_SESSION_ROWS_ARE_NOT_CONTIGUOUS_AND_NON_REPEATING": (
            impl.AcfRow("A", start, 1.0),
            impl.AcfRow("B", start + timedelta(minutes=15), 2.0),
            impl.AcfRow("A", start + timedelta(minutes=30), 3.0),
        ),
    }
    for expected, rows in cases.items():
        assessment = impl.assess_within_session_acf(rows)
        assert expected in assessment.integrity_defects, expected
        assert assessment.lags == ()
        assert assessment.design_effect is None
    assert impl.assess_within_session_acf(
        synthetic_acf_rows(interleaved=True)
    ).integrity_defects
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.assess_within_session_acf(("not-a-row",))


def test_empty_materialization_is_an_integrity_defect() -> None:
    assessment = impl.assess_within_session_acf(())
    assert assessment.integrity_defects == ("ACF_MATERIALIZATION_IS_EMPTY",)
    assert assessment.unique_session_count == 0
    assert assessment.row_count == 0


# --------------------------------------------------------------------------
# Derived group B support
# --------------------------------------------------------------------------


def test_group_b_gates_read_derived_counts_only() -> None:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=3))
    honest = impl.build_validation_support(
        acf, declared_common_eligible_rows=36, declared_unique_sessions=3
    )
    assert honest.reconciliation_defects == ()
    assert honest.derived_unique_sessions == 3
    assert honest.derived_common_eligible_rows == 36
    assert honest.basis == "GATES_READ_DERIVED_SESSION_COUNTS_ONLY_NEVER_A_CALLER_SCALAR"
    assert "FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS" in (
        impl.assess_validation_support(honest)
    )

    overstated = impl.build_validation_support(
        acf, declared_common_eligible_rows=36, declared_unique_sessions=20
    )
    assert "DECLARED_SESSION_COUNT_DOES_NOT_RECONCILE_WITH_DERIVED_SESSIONS" in (
        overstated.reconciliation_defects
    )
    assert "FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS" in (
        impl.assess_validation_support(overstated)
    )
    assert "DECLARED_SESSION_COUNT_DOES_NOT_RECONCILE_WITH_DERIVED_SESSIONS" in (
        impl.validation_support_integrity_defects(overstated)
    )


def test_group_b_gate_is_satisfied_only_by_twenty_real_sessions() -> None:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=20))
    support = impl.build_validation_support(
        acf,
        declared_common_eligible_rows=acf.row_count,
        declared_unique_sessions=acf.unique_session_count,
    )
    assert acf.unique_session_count == 20
    assert impl.assess_validation_support(support) == ()
    assert impl.validation_support_integrity_defects(support) == ()


def test_a_forged_derived_count_is_an_integrity_defect() -> None:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=3))
    support = impl.build_validation_support(
        acf, declared_common_eligible_rows=36, declared_unique_sessions=3
    )
    forged = dataclasses.replace(
        support, derived_unique_sessions=20, declared_unique_sessions=20
    )
    assert "DERIVED_SESSION_COUNT_DOES_NOT_MATCH_THE_ACF_MATERIALIZATION" in (
        impl.validation_support_integrity_defects(forged)
    )
    assert "FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS" in (
        impl.assess_validation_support(forged)
    )


def test_validation_support_builder_refuses_malformed_operands() -> None:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=1))
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_validation_support(
            "not-an-acf", declared_common_eligible_rows=1, declared_unique_sessions=1
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_validation_support(
            acf, declared_common_eligible_rows=-1, declared_unique_sessions=1
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.build_validation_support(
            acf, declared_common_eligible_rows=1, declared_unique_sessions=True
        )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.assess_validation_support("not-a-record")
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.validation_support_integrity_defects("not-a-record")


def test_an_empty_common_eligible_set_is_a_group_b_trigger() -> None:
    empty = impl.assess_within_session_acf(())
    support = impl.build_validation_support(
        empty, declared_common_eligible_rows=0, declared_unique_sessions=0
    )
    assert "VALIDATION_COMMON_ELIGIBLE_SET_IS_EMPTY" in impl.assess_validation_support(support)
    assert impl.validation_support_integrity_defects(support)


# --------------------------------------------------------------------------
# Counters, partition integrity and PASS criteria
# --------------------------------------------------------------------------


def test_counter_reconciliation_names_every_breach() -> None:
    reconciled = impl.ConfirmatoryCounters(
        fits_attempted=2,
        fits_succeeded=2,
        permits_consumed=2,
        seals_verified=2,
        validation_openings=1,
    )
    assert impl.reconcile_counters(reconciled) == ()
    for mutation, expected in (
        ({"permits_consumed": 1}, "PERMITS_CONSUMED_DO_NOT_EQUAL_FIT_ATTEMPTS"),
        ({"fits_attempted": 3, "permits_consumed": 3}, "FIT_ATTEMPTS_ARE_NOT_EXACTLY_TWO"),
        ({"fits_succeeded": 1}, "FIT_SUCCESSES_ARE_NOT_EXACTLY_TWO"),
        ({"seals_verified": 1}, "BOTH_MODEL_SEALS_ARE_NOT_VERIFIED"),
        ({"validation_openings": 2}, "VALIDATION_OPENINGS_ARE_NOT_EXACTLY_ONE"),
        (
            {"validation_stage_train_requests": 1},
            "VALIDATION_STAGE_TRAIN_REQUEST_COUNT_IS_NONZERO",
        ),
        ({"final_test_requests": 1}, "FINAL_TEST_REQUEST_COUNT_IS_NONZERO"),
        ({"final_test_reads": 1}, "FINAL_TEST_READ_COUNT_IS_NONZERO"),
        ({"extra_accesses": 1}, "EXTRA_ACCESS_COUNT_IS_NONZERO"),
        ({"final_test_state": "OPEN"}, "FINAL_TEST_IS_NOT_SEALED"),
    ):
        assert expected in impl.reconcile_counters(
            dataclasses.replace(reconciled, **mutation)
        )
    assert "CONFIRMATORY_FIT_BUDGET_EXCEEDED" in impl.reconcile_counters(
        dataclasses.replace(reconciled, fits_attempted=3, permits_consumed=3)
    )
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.reconcile_counters("not-a-record")


def test_partition_integrity_requires_a_strict_boundary_and_a_full_purge_gap() -> None:
    train_end = datetime(2023, 12, 29, 21, 0, tzinfo=UTC)
    assert impl.assess_partition_integrity(
        max_train_label_end_time=train_end,
        min_validation_decision_time=train_end + timedelta(minutes=60),
    ) == ()
    assert "VALIDATION_PURGE_GAP_BELOW_60_MINUTES" in impl.assess_partition_integrity(
        max_train_label_end_time=train_end,
        min_validation_decision_time=train_end + timedelta(minutes=59),
    )
    equal = impl.assess_partition_integrity(
        max_train_label_end_time=train_end, min_validation_decision_time=train_end
    )
    assert "TRAIN_LABEL_END_NOT_STRICTLY_BEFORE_VALIDATION_DECISION" in equal
    assert "VALIDATION_PURGE_GAP_BELOW_60_MINUTES" in equal
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.assess_partition_integrity(
            max_train_label_end_time=train_end.replace(tzinfo=None),
            min_validation_decision_time=train_end,
        )


def _metrics(difference: float, relative: float | None, *, scored: bool = True) -> object:
    return impl.DecisionMetrics(
        row_count=1,
        mean_base=1.0,
        mean_har=0.5,
        mean_difference=difference,
        relative_qlike_reduction=relative,
        mean_base_hex=impl.float_hex(1.0),
        mean_har_hex=impl.float_hex(0.5),
        mean_difference_hex=impl.float_hex(difference),
        relative_qlike_reduction_hex=None if relative is None else impl.float_hex(relative),
        scored=scored,
        undefined_reasons=() if scored else ("SYNTHETIC",),
    )


def test_pass_criteria_equality_handling_is_asymmetric_by_design() -> None:
    passing = impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ())
    assert passing.passed and passing.failures == ()
    assert [name for name, _ in passing.criteria] == [
        "D_STRICTLY_GREATER_THAN_ZERO",
        "RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10",
        "PRIMARY_LOWER_BOUND_STRICTLY_GREATER_THAN_ZERO",
        "COUNTERS_INTEGRITY_AND_BUDGET_RECONCILE",
    ]
    zero_d = impl.evaluate_pass_criteria(_metrics(0.0, 0.10), 0.001, ())
    assert "D_STRICTLY_GREATER_THAN_ZERO" in zero_d.failures
    assert "RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10" not in zero_d.failures
    zero_bound = impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.0, ())
    assert "PRIMARY_LOWER_BOUND_STRICTLY_GREATER_THAN_ZERO" in zero_bound.failures
    below = impl.evaluate_pass_criteria(_metrics(0.5, 0.0999999), 0.001, ())
    assert "RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10" in below.failures
    breached = impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ("DEFECT",))
    assert "COUNTERS_INTEGRITY_AND_BUDGET_RECONCILE" in breached.failures


def test_pass_criteria_refuse_unscored_metrics_and_malformed_bounds() -> None:
    unscored = impl.evaluate_pass_criteria(_metrics(0.5, 0.10, scored=False), 0.001, ())
    assert not unscored.passed
    assert "D_STRICTLY_GREATER_THAN_ZERO" in unscored.failures
    assert "RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10" in unscored.failures
    nonfinite = impl.evaluate_pass_criteria(_metrics(float("nan"), 0.10), 0.001, ())
    assert "D_STRICTLY_GREATER_THAN_ZERO" in nonfinite.failures
    for bad in (float("nan"), float("inf"), True, "1.0"):
        with pytest.raises(impl.Test3ConfirmatoryValidationError):
            impl.evaluate_pass_criteria(_metrics(0.5, 0.10), bad, ())
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.evaluate_pass_criteria("not-a-record", 0.001, ())


# --------------------------------------------------------------------------
# Integrity-before-support precedence
# --------------------------------------------------------------------------


def _supported_validation(sessions: int = 20) -> object:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=sessions))
    return impl.build_validation_support(
        acf,
        declared_common_eligible_rows=acf.row_count,
        declared_unique_sessions=acf.unique_session_count,
    )


def test_integrity_wins_whenever_both_descriptions_could_apply() -> None:
    classification = impl.classify_confirmatory_terminal(
        integrity_defects=("SYNTHETIC_INTEGRITY_DEFECT",),
        deployment_precheck=impl.precheck_deployment_designs(rank_deficient_sample()),
        validation_support=_supported_validation(3),
        pass_assessment=impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ()),
    )
    assert classification.terminal_class == impl.TerminalClass.INVALID_EVIDENCE
    assert classification.tier == 1
    assert classification.reasons[0] == "SYNTHETIC_INTEGRITY_DEFECT"
    assert classification.retry == "TERMINAL_NO_RETRY"


def test_identity_defects_and_reconciliation_defects_are_promoted_into_tier_one() -> None:
    acf = impl.assess_within_session_acf(synthetic_acf_rows(sessions=3))
    overstated = impl.build_validation_support(
        acf, declared_common_eligible_rows=36, declared_unique_sessions=20
    )
    classification = impl.classify_confirmatory_terminal(
        deployment_precheck=impl.precheck_deployment_designs(mismatched_identity_sample()),
        validation_support=overstated,
    )
    assert classification.terminal_class == impl.TerminalClass.INVALID_EVIDENCE
    assert classification.tier == 1
    assert "DECLARED_SESSION_COUNT_DOES_NOT_RECONCILE_WITH_DERIVED_SESSIONS" in (
        classification.reasons
    )


def test_structural_support_is_evaluated_only_after_integrity_passes() -> None:
    group_a = impl.classify_confirmatory_terminal(
        deployment_precheck=impl.precheck_deployment_designs(rank_deficient_sample()),
        pass_assessment=impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ()),
    )
    assert group_a.terminal_class == impl.TerminalClass.UNDERPOWERED_STOP
    assert group_a.tier == 2
    assert any(item.startswith("PREFIT_DESIGN_RANK_DEFICIENT") for item in group_a.reasons)

    group_b = impl.classify_confirmatory_terminal(
        validation_support=_supported_validation(3),
        pass_assessment=impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ()),
    )
    assert group_b.terminal_class == impl.TerminalClass.UNDERPOWERED_STOP
    assert "FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS" in group_b.reasons


def test_scored_results_close_at_tier_four_or_five() -> None:
    support = _supported_validation()
    confirmed = impl.classify_confirmatory_terminal(
        validation_support=support,
        pass_assessment=impl.evaluate_pass_criteria(_metrics(0.5, 0.10), 0.001, ()),
    )
    assert confirmed.terminal_class == impl.TerminalClass.CONFIRMED
    assert confirmed.tier == 5 and confirmed.reasons == ()
    not_confirmed = impl.classify_confirmatory_terminal(
        validation_support=support,
        pass_assessment=impl.evaluate_pass_criteria(_metrics(0.0, 0.10), 0.001, ()),
    )
    assert not_confirmed.terminal_class == impl.TerminalClass.NOT_CONFIRMED
    assert not_confirmed.tier == 4
    assert "D_STRICTLY_GREATER_THAN_ZERO" in not_confirmed.reasons


def test_a_missing_scoring_result_is_invalid_evidence_not_underpowered() -> None:
    classification = impl.classify_confirmatory_terminal(
        validation_support=_supported_validation()
    )
    assert classification.terminal_class == impl.TerminalClass.INVALID_EVIDENCE
    assert classification.reasons == ("SCORING_RESULT_IS_ABSENT",)
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.classify_confirmatory_terminal(pass_assessment="not-a-record")
    with pytest.raises(impl.Test3ConfirmatoryValidationError):
        impl.classify_confirmatory_terminal(deployment_precheck="not-a-record")


def test_every_terminal_class_is_no_retry_and_the_set_is_exactly_four() -> None:
    assert {item.value for item in impl.TerminalClass} == {
        "CONFIRMED_ON_OUTER_VALIDATION_FINAL_TEST_PROTOCOL_ELIGIBLE",
        "NOT_CONFIRMED_ON_OUTER_VALIDATION_TEST3_TERMINAL",
        "UNDERPOWERED_STOP",
        "INVALID_EVIDENCE",
    }
    classification = impl.classify_confirmatory_terminal(
        integrity_defects=("SYNTHETIC",)
    )
    assert classification.retry == "TERMINAL_NO_RETRY"

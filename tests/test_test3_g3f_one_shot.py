"""Data-free adversarial tests for the Test 3 G3-F one-shot stage.

Every test here is in-memory only, except for synthetic files created under a per-test
temporary path to exercise the local activation-file loader and its exclusive activation replay
claim. No test reads a data artifact, reaches a provider, requests or constructs a target, makes
a target-space reservation, performs a real fit, or writes anything outside a per-test temporary
path. Every name used for a synthetic runtime evidence value is a per-test placeholder and is
never an actual activation value, and every synthetic claim lives under ``tmp_path``.

The activation loader and the G3-P delivery handle are both one-attempt per module instance, so
adversarial cases load independent in-memory instances of the module rather than spending the
imported one.
"""

from __future__ import annotations

import ast
import copy
import functools
import hashlib
import importlib.util
import itertools
import json
import math
import pickle
import sys
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pytest

_PACKAGE_PARTS = ("mes_quant", "exploration")


def _prepend_worktree_source_path() -> None:
    """Select this worktree's ``src`` tree before importing ``mes_quant``."""

    candidate = Path(__file__).resolve().parents[1] / "src"
    if not (candidate / "mes_quant" / "__init__.py").is_file():
        return

    entry = str(candidate)
    sys.path[:] = [item for item in sys.path if item != entry]
    sys.path.insert(0, entry)

    for depth in range(1, len(_PACKAGE_PARTS) + 1):
        module = sys.modules.get(".".join(_PACKAGE_PARTS[:depth]))
        search_path = getattr(module, "__path__", None)
        package_directory = candidate.joinpath(*_PACKAGE_PARTS[:depth])
        if not isinstance(search_path, list) or not package_directory.is_dir():
            continue
        location = str(package_directory)
        if location not in search_path:
            search_path.insert(0, location)


_prepend_worktree_source_path()

from mes_quant.exploration import test3_g3f_one_shot as g3f
from mes_quant.exploration.test3_contract import (
    BOOTSTRAP_REPETITIONS,
    FOLD_ORDER,
    MASTER_SEED,
    MODEL_COLUMNS,
    MODEL_ORDER,
    PROTOCOL_ID,
    PROTOCOL_SHA256,
    RELATIVE_QLIKE_REDUCTION_FLOOR,
    TARGET_SPACE_ID,
    RowStatus,
    TerminalDisposition,
)
from mes_quant.exploration.test3_design import Harmonic, PredictorStatusRow
from mes_quant.exploration.test3_stats import (
    ContinuationInputs,
    SessionImprovementAggregate,
    decide_continuation,
    duan_smearing_factor,
    paired_session_block_bootstrap,
    qlike,
)
from mes_quant.exploration.test3_target import TargetStatusRow

_BASE = datetime(2022, 1, 3, 15, 0, tzinfo=UTC)

_INSTANCE_COUNTER = itertools.count()


def _fresh_g3f_module():
    """Load an independent in-memory instance of the G3-F module.

    The activation loader and the G3-P delivery handle are each one-attempt per module instance,
    so every adversarial case needs its own instance. Each instance gets a unique private module
    name; the imported ``g3f`` instance is never spent by these tests.
    """

    name = f"_test3_g3f_adversarial_instance_{next(_INSTANCE_COUNTER)}"
    specification = importlib.util.spec_from_file_location(name, g3f.__file__)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _write_reviewed_tree(root: Path) -> tuple[str, ...]:
    """Create six synthetic stand-ins for the reviewed implementation paths."""

    digests: list[str] = []
    for index, relative in enumerate(g3f.REVIEWED_IMPLEMENTATION_PATHS):
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = f"# synthetic reviewed bytes {index}\n"
        target.write_text(payload, encoding="utf-8")
        digests.append(hashlib.sha256(payload.encode("utf-8")).hexdigest())
    return tuple(digests)


def _canonical(value: object) -> bytes:
    """The one canonical UTF-8 serialization; every digest below is machine-computed."""

    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _runtime_evidence(**overrides: object) -> dict[str, object]:
    evidence: dict[str, object] = {
        "root": "synthetic-placeholder-root",
        "namespace": "synthetic-placeholder-namespace",
        "reservation_name": "synthetic-placeholder-reservation",
        "permit_names": [f"synthetic-placeholder-permit-{index}" for index in (1, 2, 3, 4)],
        "terminal_name": "synthetic-placeholder-terminal",
    }
    evidence.update(overrides)
    return evidence


def _activation_payload(digests: tuple[str, ...], **overrides: object) -> dict[str, object]:
    """Build a synthetic activation payload; every value here is a test placeholder."""

    payload: dict[str, object] = {
        "recovery_lineage_id": "SYNTHETIC-PLACEHOLDER-LINEAGE-001",
        "override_id": "SYNTHETIC-PLACEHOLDER-OVERRIDE-001",
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": PROTOCOL_SHA256,
        "target_space_id": TARGET_SPACE_ID,
        "fit_permit_budget": 4,
        "implementation_paths": list(g3f.REVIEWED_IMPLEMENTATION_PATHS),
        "implementation_path_sha256": list(digests),
        "runtime_evidence": _runtime_evidence(),
    }
    payload.update(overrides)
    return payload


def _envelope(payload: object, *, digest: str | None = None) -> dict[str, object]:
    """Wrap one payload in the closed envelope with a machine-computed payload digest."""

    return {
        "activation_payload": payload,
        "activation_payload_sha256": (
            hashlib.sha256(_canonical(payload)).hexdigest() if digest is None else digest
        ),
    }


def _write_activation(path: Path, payload: object, *, digest: str | None = None) -> str:
    path.write_bytes(_canonical(_envelope(payload, digest=digest)))
    return str(path)


def _claim_directory(root: Path, payload: Mapping[str, object]) -> Path:
    """Locate the synthetic evidence namespace; it never leaves ``tmp_path``."""

    evidence = payload["runtime_evidence"]
    assert isinstance(evidence, Mapping)
    return root.joinpath(*str(evidence["root"]).split("/"), str(evidence["namespace"]))


def _claim_path(root: Path, payload: Mapping[str, object]) -> Path:
    evidence = payload["runtime_evidence"]
    assert isinstance(evidence, Mapping)
    return _claim_directory(root, payload) / (
        str(evidence["reservation_name"]) + g3f._ACTIVATION_CLAIM_SUFFIX
    )


def _record_path(root: Path, payload: Mapping[str, object], name: str) -> Path:
    return _claim_directory(root, payload) / name


def _prepared_activation(
    tmp_path: Path,
    *,
    name: str = "synthetic-repository",
    create_claim_directory: bool = True,
    **overrides: object,
) -> tuple[Path, str, tuple[str, ...], dict[str, object]]:
    """Create one synthetic repository, activation file and (optionally) claim directory."""

    root = tmp_path / name
    root.mkdir()
    digests = _write_reviewed_tree(root)
    payload = _activation_payload(digests, **overrides)
    if create_claim_directory:
        _claim_directory(root, payload).mkdir(parents=True, exist_ok=True)
    activation = _write_activation(tmp_path / f"{name}-activation-file", payload)
    return root, activation, digests, payload


def _harmonic(index: int) -> Harmonic:
    n_slots = 22
    slot = index % n_slots
    angle = 2.0 * math.pi * slot / n_slots
    return Harmonic(
        slot=slot,
        n_slots=n_slots,
        session_sin=math.sin(angle),
        session_cos=math.cos(angle),
    )


def _synthetic_rows(origin=None, *, module=g3f) -> tuple[object, ...]:
    """Ten shared training rows plus two disjoint, purged holdout blocks."""

    if origin is None:
        origin = module.RowOrigin.SYNTHETIC_IN_MEMORY
    blocks = (
        (10, "TRAIN", "TRAIN", 0),
        (8, "VALIDATION", "UNUSED", 5),
        (8, "UNUSED", "VALIDATION", 10),
    )
    rows: list[object] = []
    index = 0
    for count, role_2022, role_2023, day_offset in blocks:
        for offset in range(count):
            moment = _BASE + timedelta(days=day_offset, minutes=15 * offset)
            rows.append(
                module.OneShotEligibleRow(
                    decision_identity=f"{moment.isoformat()}|instrument_id=12345",
                    decision_time_utc=moment,
                    session_id=moment.date().isoformat(),
                    role_wf_2022=role_2022,
                    role_wf_2023=role_2023,
                    harmonic=_harmonic(index),
                    rv_fwd_60=0.5 + 0.01 * index,
                    realized_vol_60m=0.4 + 0.01 * index,
                    realized_vol_120m=0.5 + 0.01 * index,
                    realized_vol_240m=0.6 + 0.01 * index,
                    origin=origin,
                )
            )
            index += 1
    return tuple(rows)


class _InertFitCallback:
    """A callback that estimates nothing; it returns a structurally valid inert 4-tuple."""

    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.calls = 0
        self.permits_at_call: list[int] = []
        self.fail_on_call = fail_on_call
        self.budget: g3f.OneShotFitPermitBudget | None = None

    def __call__(self, design: np.ndarray, response: np.ndarray) -> object:
        self.calls += 1
        if self.budget is not None:
            self.permits_at_call.append(self.budget.permits_consumed)
        if self.fail_on_call is not None and self.calls == self.fail_on_call:
            raise ValueError("inert callback failure")
        columns = int(design.shape[1])
        return (
            np.zeros(columns, dtype=np.float64),
            np.zeros(1, dtype=np.float64),
            columns,
            np.ones(columns, dtype=np.float64),
        )


def _inert_report() -> tuple[g3f.OneShotFitReport, g3f.OneShotFitPermitBudget, _InertFitCallback]:
    budget = g3f.OneShotFitPermitBudget()
    callback = _InertFitCallback()
    callback.budget = budget
    report = g3f.run_one_shot_fits(
        _synthetic_rows(),
        mode=g3f.ExecutionMode.PRE_ACTIVATION_INERT,
        fit_callback=callback,
        budget=budget,
    )
    return report, budget, callback


def test_model_fold_order_and_unreplenished_budget_are_frozen() -> None:
    assert g3f.EXPECTED_PAIR_ORDER == (
        ("RVBASE001", "WF_2022"),
        ("RVHAR001", "WF_2022"),
        ("RVBASE001", "WF_2023"),
        ("RVHAR001", "WF_2023"),
    )
    assert g3f.EXPECTED_PAIR_ORDER == tuple(
        (model_id, fold_id) for fold_id in FOLD_ORDER for model_id in MODEL_ORDER
    )
    assert g3f.FIT_PERMIT_BUDGET == 4
    assert len(g3f.EXPECTED_PAIR_ORDER) == g3f.FIT_PERMIT_BUDGET


def test_handoff_identity_matches_the_g3p_producer() -> None:
    from mes_quant.exploration import test3_g3p_pre_fit as g3p

    assert g3f.EXPECTED_HANDOFF_ID == g3p.G3P_IN_MEMORY_HANDOFF_ID


def test_inert_run_consumes_four_permits_in_the_exact_frozen_order() -> None:
    report, budget, callback = _inert_report()

    assert budget.consumed_pairs == g3f.EXPECTED_PAIR_ORDER
    assert budget.permits_consumed == 4
    assert budget.callback_starts == 4
    assert budget.validated_outputs == 4
    assert budget.permits_remaining == 0
    assert budget.sealed is True
    assert budget.poisoned is False
    assert callback.calls == 4
    assert tuple((fit.model_id, fit.fold_id) for fit in report.fits) == g3f.EXPECTED_PAIR_ORDER
    assert tuple(fit.ordinal for fit in report.fits) == (1, 2, 3, 4)
    for fit in report.fits:
        assert fit.column_names == MODEL_COLUMNS[fit.model_id]
        assert fit.coefficient_dimension == len(MODEL_COLUMNS[fit.model_id])
        assert fit.rank == len(MODEL_COLUMNS[fit.model_id])


def test_inert_run_keeps_every_protected_counter_at_zero() -> None:
    report, _budget, _callback = _inert_report()

    g3f.assert_zero_protected_counters(report.counters)
    for name in g3f.PROTECTED_COUNTER_FIELDS:
        assert getattr(report.counters, name) == 0
    assert report.counters.permits_consumed == 4
    assert report.counters.fit_callback_starts == 4
    assert report.counters.fit_outputs_validated == 4
    assert report.counters.refused_fit_requests == 0
    assert report.evidence_naming == "DEFERRED_TO_SEPARATE_OWNER_ACTIVATION"


def test_each_permit_is_consumed_before_its_own_callback_starts() -> None:
    _report, _budget, callback = _inert_report()

    # The permit for ordinal N is already spent when callback N runs.
    assert callback.permits_at_call == [1, 2, 3, 4]


def test_fifth_request_is_refused_before_any_fifth_callback() -> None:
    budget = g3f.OneShotFitPermitBudget()
    for model_id, fold_id in g3f.EXPECTED_PAIR_ORDER:
        permit = budget.consume(model_id=model_id, fold_id=fold_id)
        budget.start_callback(permit)
        budget.record_validated_output(permit)

    with pytest.raises(g3f.Test3G3FPermitError, match="fifth fit request is refused"):
        budget.consume(model_id=MODEL_ORDER[0], fold_id=FOLD_ORDER[0])

    assert budget.permits_consumed == 4
    assert budget.callback_starts == 4
    assert budget.refused_requests == 1

    budget.seal()
    with pytest.raises(g3f.Test3G3FPermitError, match="fifth fit request is refused"):
        budget.consume(model_id=MODEL_ORDER[0], fold_id=FOLD_ORDER[0])
    assert budget.callback_starts == 4
    assert budget.refused_requests == 2


def test_a_failed_fit_consumes_its_permit_and_poisons_the_budget() -> None:
    budget = g3f.OneShotFitPermitBudget()
    callback = _InertFitCallback(fail_on_call=2)
    callback.budget = budget

    with pytest.raises(ValueError, match="inert callback failure"):
        g3f.run_one_shot_fits(
            _synthetic_rows(),
            mode=g3f.ExecutionMode.PRE_ACTIVATION_INERT,
            fit_callback=callback,
            budget=budget,
        )

    assert budget.permits_consumed == 2
    assert budget.callback_starts == 2
    assert budget.validated_outputs == 1
    assert budget.poisoned is True
    assert budget.sealed is False
    assert budget.failure_reason == "ordinal=2:fit_callback_raised"

    # No permit is replaced, refunded or reissued after a failure.
    with pytest.raises(g3f.Test3G3FPermitError, match="poisoned"):
        budget.consume(model_id=MODEL_ORDER[0], fold_id=FOLD_ORDER[1])
    with pytest.raises(g3f.Test3G3FPermitError, match="poisoned"):
        budget.seal()
    assert budget.permits_consumed == 2


def test_out_of_order_pair_poisons_the_budget() -> None:
    budget = g3f.OneShotFitPermitBudget()
    with pytest.raises(g3f.Test3G3FPermitError, match="unexpected pair order"):
        budget.consume(model_id=MODEL_ORDER[1], fold_id=FOLD_ORDER[0])
    assert budget.poisoned is True
    assert budget.permits_consumed == 0


def test_real_mode_stops_before_any_data_provider_target_or_fit() -> None:
    budget = g3f.OneShotFitPermitBudget()
    callback = _InertFitCallback()

    with pytest.raises(g3f.Test3G3FPreActivationStop, match="separate exact Owner activation"):
        g3f.run_one_shot_fits(
            _synthetic_rows(g3f.RowOrigin.G3P_IN_PROCESS_HANDOFF),
            mode=g3f.ExecutionMode.OWNER_ACTIVATED_REAL,
            fit_callback=callback,
            budget=budget,
        )

    assert callback.calls == 0
    assert budget.permits_consumed == 0
    assert budget.callback_starts == 0
    assert budget.poisoned is False


def test_inert_mode_refuses_activation_material_and_handoff_rows() -> None:
    with pytest.raises(g3f.Test3G3FPreActivationStop):
        g3f.run_one_shot_fits(
            _synthetic_rows(),
            mode=g3f.ExecutionMode.PRE_ACTIVATION_INERT,
            fit_callback=_InertFitCallback(),
            activation=object(),
        )
    with pytest.raises(g3f.Test3G3FOneShotError):
        g3f.run_one_shot_fits(
            _synthetic_rows(g3f.RowOrigin.G3P_IN_PROCESS_HANDOFF),
            mode=g3f.ExecutionMode.PRE_ACTIVATION_INERT,
            fit_callback=_InertFitCallback(),
        )


#: Every module-level mint route, capability class, adapter and registry that must be gone.
_FORBIDDEN_MODULE_ATTRIBUTES = (
    "OwnerActivation",
    "_ACTIVATION_REGISTRY",
    "_ExecutionAuthority",
    "_G3PHandoffCapability",
    "_G3PRowHandoff",
    "_HANDOFF_REGISTRY",
    "_SERIAL_COUNTER",
    "_VerifiedOwnerActivationCapability",
    "_build_closed_activation_and_handoff_state_machine",
    "_build_private_machinery",
    "_consume_activation_capability",
    "_mint_activation_capability",
    "_mint_row_handoff",
    "_next_serial",
    "_open_handoff_capability",
    "_recheck_reviewed_bytes",
    "_require_activation",
    "deliver_g3p_row_handoff",
    "rows_from_in_memory_handoff",
)

_EXPECTED_PUBLIC_SURFACE = (
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
)


def test_no_module_level_mint_factory_capability_class_or_registry_remains() -> None:
    """The public loader is the only surviving route that can ever issue a capability."""

    for name in _FORBIDDEN_MODULE_ATTRIBUTES:
        assert not hasattr(g3f, name), name
        assert name not in g3f.__all__, name

    # No module-level name advertises a mint, open, capability or registry route at all.
    for name in dir(g3f):
        lowered = name.lower()
        assert "mint" not in lowered, name
        assert "registry" not in lowered, name
        assert "capability" not in lowered or name == "load_owner_activation_capability", name

    # No module-level mutable container can hold serials, states or issued objects.
    mutable = {
        name
        for name, value in vars(g3f).items()
        if isinstance(value, (dict, list, set)) and not name.startswith("__")
    }
    assert mutable == {"FOLD_HOLDOUT_YEARS", "FOLD_ROLE_ATTRIBUTES"}

    # The only bare sentinel object is the non-authoritative module-instance identity marker.
    bare = {name for name, value in vars(g3f).items() if type(value) is object}
    assert bare == {"_MODULE_INSTANCE_MARKER"}

    # The public surface is exactly the reviewed one; it was not broadened.
    assert tuple(g3f.__all__) == _EXPECTED_PUBLIC_SURFACE
    for name in g3f.__all__:
        assert hasattr(g3f, name), name


class _TripwireRowSource:
    """A row source that may never be iterated on a refused activation path.

    ``run_one_shot_fits`` accepts or refuses the activation before it materializes any row, so a
    correct refusal never reaches ``__iter__``.  The attempt is recorded *before* it raises, so
    the observation survives even if some caller were to swallow the error.
    """

    def __init__(self, tripped: list[str]) -> None:
        self._tripped = tripped

    def __iter__(self):
        self._tripped.append("row_iteration")
        raise AssertionError("a refused activation path iterated the row source")


def _real_mode_stop(
    activation: object,
    *,
    module=g3f,
    match: str | None = None,
) -> None:
    """Attempt a real-mode run and prove it stopped before rows, math, permits and callbacks.

    The row argument is a tripwire whose first iteration fails the test, so every refused
    activation case proves the refusal happened before any row was read at all.
    """

    budget = module.OneShotFitPermitBudget()
    callback = _InertFitCallback()
    callback.budget = budget
    tripped: list[str] = []

    def _forbidden_design(*_args: object, **_kwargs: object) -> object:
        tripped.append("build_design_matrix")
        raise AssertionError("design math ran on a refused activation path")

    def _forbidden_response(*_args: object, **_kwargs: object) -> object:
        tripped.append("build_response_vector")
        raise AssertionError("response math ran on a refused activation path")

    original = (module.build_design_matrix, module.build_response_vector)
    module.build_design_matrix = _forbidden_design
    module.build_response_vector = _forbidden_response
    try:
        with pytest.raises(module.Test3G3FPreActivationStop, match=match):
            module.run_one_shot_fits(
                _TripwireRowSource(tripped),
                mode=module.ExecutionMode.OWNER_ACTIVATED_REAL,
                fit_callback=callback,
                activation=activation,
                budget=budget,
            )
    finally:
        module.build_design_matrix, module.build_response_vector = original

    assert tripped == []
    assert callback.calls == 0
    assert budget.permits_consumed == 0
    assert budget.callback_starts == 0
    assert budget.validated_outputs == 0
    assert budget.poisoned is False


def test_direct_dataclass_dict_duck_and_serial_copies_cannot_enable_real_mode(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, activation, digests, _document = _prepared_activation(tmp_path)
    capability = module.load_owner_activation_capability(activation, repository_root=str(root))
    capability_type = type(capability)
    serial = capability.serial

    @dataclass(frozen=True)
    class _DataclassActivation:
        serial: int
        repository_root: str
        reviewed_digests: tuple[str, ...]
        fit_permit_budget: int = 4
        recovery_lineage_id: str = "SYNTHETIC-PLACEHOLDER-LINEAGE-001"
        override_id: str = "SYNTHETIC-PLACEHOLDER-OVERRIDE-001"
        activation_payload_sha256: str = "0" * 64
        activation_file_sha256: str = "1" * 64
        runtime_evidence: tuple[object, ...] = ()

    class _DuckActivation:
        """A duck type that copies the real serial and the real verified fields."""

        def __init__(self) -> None:
            self.serial = serial
            self.repository_root = str(root)
            self.reviewed_digests = digests
            self.fit_permit_budget = 4
            self.recovery_lineage_id = "SYNTHETIC-PLACEHOLDER-LINEAGE-001"
            self.override_id = "SYNTHETIC-PLACEHOLDER-OVERRIDE-001"
            self.activation_payload_sha256 = "0" * 64
            self.activation_file_sha256 = "1" * 64
            self.runtime_evidence = ()

    hostiles = (
        None,
        object(),
        _DuckActivation(),
        _DataclassActivation(serial, str(root), digests),
        {
            "serial": serial,
            "repository_root": str(root),
            "reviewed_digests": list(digests),
            "fit_permit_budget": 4,
        },
        object.__new__(capability_type),
    )
    for hostile in hostiles:
        _real_mode_stop(hostile, module=module)

    # None of the refused attempts spent the one genuinely issued capability.
    report = module._local_state_report()
    assert report["activation_capability_issued"] is True
    assert report["activation_capability_spent"] is False
    assert report["authority"] == "NON_AUTHORITATIVE_LOCAL_IN_PROCESS_OBSERVATION_ONLY"

    # The capability type itself is not reachable from the module surface.
    assert not hasattr(module, capability_type.__name__)
    assert capability_type.__name__ not in vars(module)
    with pytest.raises(module.Test3G3FOneShotError, match="direct construction"):
        capability_type(
            object(),
            activation_file_sha256="1" * 64,
            activation_payload_sha256="0" * 64,
            fit_permit_budget=4,
            override_id="A",
            recovery_lineage_id="B",
            repository_root=str(root),
            reviewed_digests=digests,
            runtime_evidence=(),
            serial=serial,
        )


def test_object_setattr_cannot_redirect_the_six_path_recheck(tmp_path: Path) -> None:
    """The recheck uses closure-captured values, never fields reread from the object."""

    module = _fresh_g3f_module()
    root, activation, _digests, _document = _prepared_activation(tmp_path)
    capability = module.load_owner_activation_capability(activation, repository_root=str(root))

    # A second, byte-identical tree that would satisfy the capability's own declared fields.
    pristine, _activation, pristine_digests, _doc = _prepared_activation(
        tmp_path,
        name="pristine-repository",
    )
    assert pristine_digests == capability.reviewed_digests

    drifted = root.joinpath(*module.REVIEWED_IMPLEMENTATION_PATHS[2].split("/"))
    drifted.write_text("# drifted synthetic bytes\n", encoding="utf-8")

    # ``__setattr__`` is refused outright, and the low-level bypass changes nothing that counts.
    with pytest.raises(module.Test3G3FOneShotError, match="immutable"):
        capability.repository_root = str(pristine)
    object.__setattr__(capability, "repository_root", str(pristine))
    object.__setattr__(capability, "reviewed_digests", pristine_digests)

    _real_mode_stop(capability, module=module, match="drifted")


def test_reviewed_byte_drift_after_load_stops_before_math_permits_or_callbacks(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, activation, _digests, _document = _prepared_activation(tmp_path)
    capability = module.load_owner_activation_capability(activation, repository_root=str(root))

    drifted = root.joinpath(*module.REVIEWED_IMPLEMENTATION_PATHS[2].split("/"))
    drifted.write_text("# drifted synthetic bytes\n", encoding="utf-8")

    _real_mode_stop(capability, module=module, match="drifted")


def test_wrong_reviewed_bytes_never_issue_a_capability(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, _activation, digests, _payload = _prepared_activation(tmp_path)
    forged = _write_activation(
        tmp_path / "forged-bytes",
        _activation_payload(digests, implementation_path_sha256=["a" * 64] * 6),
    )
    with pytest.raises(module.Test3G3FOneShotError, match="do not match the activation"):
        module.load_owner_activation_capability(forged, repository_root=str(root))
    assert module._local_state_report()["activation_capability_issued"] is False
    _real_mode_stop(None, module=module)


@dataclass(frozen=True)
class _StubControl:
    identity: str
    timestamp: datetime
    session_id: str
    role_2022: str
    role_2023: str


class _StubHandoff:
    """A source of synthetic in-memory row values only.

    This object is never accepted by the stage: only its raw field values may ever be delivered,
    and only through the exact one-time reviewed delivery handle.
    """

    def __init__(self, *, handoff_id: str) -> None:
        moments = tuple(_BASE + timedelta(minutes=15 * offset) for offset in range(3))
        identities = tuple(f"{moment.isoformat()}|instrument_id=12345" for moment in moments)
        statuses = (
            RowStatus.TARGET_USABLE.value,
            RowStatus.TARGET_USABLE.value,
            RowStatus.TARGET_UNUSABLE.value,
        )
        predictor_statuses = (
            RowStatus.PREDICTOR_USABLE.value,
            RowStatus.PREDICTOR_USABLE.value,
            RowStatus.PREDICTOR_UNUSABLE.value,
        )
        self.handoff_id = handoff_id
        self.controls = tuple(
            _StubControl(identity, moment, moment.date().isoformat(), "TRAIN", "VALIDATION")
            for identity, moment in zip(identities, moments, strict=True)
        )
        self.predictor_status_rows = tuple(
            PredictorStatusRow(identity, moment, status)
            for identity, moment, status in zip(
                identities, moments, predictor_statuses, strict=True
            )
        )
        self.predictor_values = {identity: (0.4, 0.5, 0.6) for identity in identities}
        self.target_status_rows = tuple(
            TargetStatusRow(
                identity,
                moment,
                moment + timedelta(minutes=60),
                status,
                1.5,
                math.log(1.5),
            )
            for identity, moment, status in zip(identities, moments, statuses, strict=True)
        )
        self.target_variance_by_identity = {identity: 1.5 for identity in identities}
        self.harmonic_by_identity = {
            identity: _harmonic(index) for index, identity in enumerate(identities)
        }


def _handoff_fields(stub: _StubHandoff) -> dict[str, object]:
    return {
        "controls": stub.controls,
        "predictor_status_rows": stub.predictor_status_rows,
        "predictor_values": stub.predictor_values,
        "target_status_rows": stub.target_status_rows,
        "target_variance_by_identity": stub.target_variance_by_identity,
        "harmonic_by_identity": stub.harmonic_by_identity,
    }


class _TripwireRow:
    """Any attribute access on a refused path is an immediate test failure."""

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"row field {name!r} was accessed on a refused path")


class _TripwireMapping(Mapping):
    """A row mapping whose contents may never be read on a refused path."""

    def __getitem__(self, key: object) -> object:
        raise AssertionError(f"mapping key {key!r} was read on a refused path")

    def __iter__(self):
        raise AssertionError("a refused path iterated a row mapping")

    def __len__(self) -> int:
        raise AssertionError("a refused path measured a row mapping")


def _tripwire_fields() -> dict[str, object]:
    """Payload whose every row and field access fails the test that touches it."""

    return {
        "controls": (_TripwireRow(),),
        "predictor_status_rows": (_TripwireRow(),),
        "predictor_values": _TripwireMapping(),
        "target_status_rows": (_TripwireRow(),),
        "target_variance_by_identity": _TripwireMapping(),
        "harmonic_by_identity": _TripwireMapping(),
    }


def test_the_one_time_delivery_handle_is_the_only_row_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _fresh_g3f_module()
    handle, marker = module._claim_g3p_delivery_handle()
    fields = _handoff_fields(_StubHandoff(handoff_id=module.EXPECTED_HANDOFF_ID))

    # The first stage takes only the exact marker and handoff identity; it carries no row field.
    supply = handle(marker, handoff_id=module.EXPECTED_HANDOFF_ID)
    rows = supply(**fields)

    assert len(rows) == 2  # the unusable third row is not eligible
    assert all(row.origin is module.RowOrigin.G3P_IN_PROCESS_HANDOFF for row in rows)
    assert [row.decision_time_utc for row in rows] == sorted(
        row.decision_time_utc for row in rows
    )

    # The returned second stage is one-use: a second call is refused before any payload read.
    with pytest.raises(module.Test3G3FPreActivationStop, match="row supply is already spent"):
        supply(**_tripwire_fields())

    report = module._local_state_report()
    assert report["handoffs_created"] == 1
    assert report["handoffs_spent"] == 1
    assert report["delivery_handle_claimed"] is True
    assert report["delivery_handle_armed"] is False
    # The intake is strictly in-memory: no file, spill, cache or IPC artifact is created.
    assert list(tmp_path.rglob("*")) == []


def test_a_second_claim_a_second_delivery_and_a_wrong_identity_are_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    module = _fresh_g3f_module()
    handle, marker = module._claim_g3p_delivery_handle()
    with pytest.raises(module.Test3G3FOneShotError, match="already claimed"):
        module._claim_g3p_delivery_handle()

    # A wrong handoff identity is refused at first-stage entry, where no row field exists yet.
    with pytest.raises(module.Test3G3FPreActivationStop, match="handoff identity"):
        handle(marker, handoff_id="OTHER")
    # A refused delivery still spends the one-time handle; there is no retry behind it.
    with pytest.raises(module.Test3G3FPreActivationStop, match="already spent"):
        handle(marker, handoff_id=module.EXPECTED_HANDOFF_ID)
    assert module._local_state_report()["handoffs_created"] == 0

    delivered = _fresh_g3f_module()
    good_handle, good_marker = delivered._claim_g3p_delivery_handle()
    fields = _handoff_fields(_StubHandoff(handoff_id=delivered.EXPECTED_HANDOFF_ID))
    good_supply = good_handle(good_marker, handoff_id=delivered.EXPECTED_HANDOFF_ID)
    assert len(good_supply(**fields)) == 2
    with pytest.raises(delivered.Test3G3FPreActivationStop, match="already spent"):
        good_handle(good_marker, handoff_id=delivered.EXPECTED_HANDOFF_ID)
    with pytest.raises(delivered.Test3G3FPreActivationStop, match="row supply is already spent"):
        good_supply(**_tripwire_fields())

    # An abandoned first-stage closure never rearms the one-time first stage either.
    abandoned = _fresh_g3f_module()
    abandoned_handle, abandoned_marker = abandoned._claim_g3p_delivery_handle()
    abandoned_supply = abandoned_handle(
        abandoned_marker,
        handoff_id=abandoned.EXPECTED_HANDOFF_ID,
    )
    assert callable(abandoned_supply)
    with pytest.raises(abandoned.Test3G3FPreActivationStop, match="already spent"):
        abandoned_handle(abandoned_marker, handoff_id=abandoned.EXPECTED_HANDOFF_ID)
    assert abandoned._local_state_report()["handoffs_created"] == 0
    assert list(tmp_path.rglob("*")) == []


def test_wrong_marker_metadata_spoof_and_replaced_instance_refuse_before_any_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _fresh_g3f_module()
    other = _fresh_g3f_module()
    handle, _marker = module._claim_g3p_delivery_handle()
    _other_handle, other_marker = other._claim_g3p_delivery_handle()

    class _MetadataSpoof:
        """A token carrying the delivery handle's own metadata but not its identity."""

        __module__ = handle.__module__
        __qualname__ = handle.__qualname__

    hostile_markers = (
        None,
        object(),
        other_marker,
        other._MODULE_INSTANCE_MARKER,
        _MetadataSpoof(),
        module,
        module.__name__,
    )
    for hostile_marker in hostile_markers:
        with pytest.raises(
            module.Test3G3FPreActivationStop,
            match="exact G3-F module instance",
        ):
            handle(hostile_marker, handoff_id=module.EXPECTED_HANDOFF_ID)

    # A refused marker never spends the handle and never creates a handoff.
    report = module._local_state_report()
    assert report["delivery_handle_armed"] is True
    assert report["handoffs_created"] == 0

    # Metadata is no longer an authorization surface anywhere: a wrapper carrying the exact
    # handle metadata is still a different object, and only the exact object is ever called.
    @functools.wraps(handle)
    def wrapper(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("a wrapper reached the delivery path")

    assert wrapper.__qualname__ == handle.__qualname__
    assert wrapper.__module__ == handle.__module__
    assert wrapper is not handle
    assert list(tmp_path.rglob("*")) == []


def test_the_private_handoff_never_escapes_or_is_reconstructible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _fresh_g3f_module()
    handle, marker = module._claim_g3p_delivery_handle()
    fields = _handoff_fields(_StubHandoff(handoff_id=module.EXPECTED_HANDOFF_ID))

    rows = handle(marker, handoff_id=module.EXPECTED_HANDOFF_ID)(**fields)

    # Only ordinary immutable eligible rows come back; the handoff is already spent inside.
    assert all(isinstance(row, module.OneShotEligibleRow) for row in rows)
    for row in rows:
        with pytest.raises(AttributeError):
            row.rv_fwd_60 = 2.0

    # No module surface exposes the handoff object, its type, its constructor or its registry.
    for name, value in vars(module).items():
        assert type(value).__name__ != "_G3PRowHandoff", name
        assert not (
            isinstance(value, type) and value.__name__ in {"_G3PRowHandoff", "_ClosureBound"}
        ), name
    for name in _FORBIDDEN_MODULE_ATTRIBUTES:
        assert not hasattr(module, name), name
    assert tuple(module.__all__) == _EXPECTED_PUBLIC_SURFACE
    assert module._local_state_report()["handoffs_spent"] == 1
    assert list(tmp_path.rglob("*")) == []


def test_the_issued_capability_is_redacted_and_unserializable(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, activation, _digests, _document = _prepared_activation(tmp_path)

    capability = module.load_owner_activation_capability(activation, repository_root=str(root))

    for rendered in (repr(capability), str(capability), f"{capability}"):
        assert "REDACTED_IN_MEMORY_ONLY" in rendered
        assert str(root) not in rendered
    for serializer in (pickle.dumps, copy.copy, copy.deepcopy):
        with pytest.raises(module.Test3G3FOneShotError, match="never be serialized"):
            serializer(capability)
    with pytest.raises(TypeError):
        json.dumps(capability)


def test_activation_loader_issues_one_capability_and_claims_it_exclusively(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, activation, digests, document = _prepared_activation(tmp_path)

    capability = module.load_owner_activation_capability(activation, repository_root=str(root))

    assert capability.reviewed_digests == digests
    assert capability.fit_permit_budget == module.FIT_PERMIT_BUDGET == 4

    claim = _claim_path(root, document)
    assert claim.is_file() and not claim.is_symlink()
    lines = claim.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "MES_TEST3_G3F_ACTIVATION_REPLAY_CLAIM_V1"
    assert lines[1] == hashlib.sha256(Path(activation).read_bytes()).hexdigest()
    assert lines[2] == "NO_SCIENTIFIC_CONTENT_NO_TARGET_ACCESS_NO_RESERVATION_NO_FIT"

    report = module._local_state_report()
    assert report["activation_loader_armed"] is False
    assert report["activation_capability_issued"] is True
    assert report["activation_capability_spent"] is False

    # Issuing performs no data, target, provider, target-space or fit work at all.
    module._accept_and_consume_activation(capability)
    assert module._local_state_report()["activation_capability_spent"] is True
    with pytest.raises(module.Test3G3FPreActivationStop, match="already consumed"):
        module._accept_and_consume_activation(capability)


def test_a_second_activation_load_is_refused_for_identical_and_different_input(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, activation, _digests, _document = _prepared_activation(tmp_path)

    first = module.load_owner_activation_capability(activation, repository_root=str(root))

    with pytest.raises(module.Test3G3FOneShotError, match="one-attempt"):
        module.load_owner_activation_capability(activation, repository_root=str(root))

    other_root, other_activation, _other_digests, other_document = _prepared_activation(
        tmp_path,
        name="second-repository",
    )
    with pytest.raises(module.Test3G3FOneShotError, match="one-attempt"):
        module.load_owner_activation_capability(
            other_activation,
            repository_root=str(other_root),
        )

    # The refused second activation was never even claimed, and only one capability exists.
    assert not _claim_path(other_root, other_document).exists()
    assert module._local_state_report()["activation_capability_issued"] is True
    module._accept_and_consume_activation(first)


def test_a_failed_validation_leaves_the_loader_permanently_refused(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, activation, digests, document = _prepared_activation(tmp_path)
    hostile = _write_activation(
        tmp_path / "hostile-budget",
        _activation_payload(digests, fit_permit_budget=5),
    )

    with pytest.raises(module.Test3G3FOneShotError, match="lifetime fit budget"):
        module.load_owner_activation_capability(hostile, repository_root=str(root))
    with pytest.raises(module.Test3G3FOneShotError, match="one-attempt"):
        module.load_owner_activation_capability(activation, repository_root=str(root))

    assert not _claim_path(root, document).exists()
    assert module._local_state_report()["activation_capability_issued"] is False
    _real_mode_stop(None, module=module)


def test_a_pre_existing_replay_claim_refuses_the_activation(tmp_path: Path) -> None:
    """A prior process already claimed this activation; the replay is terminal."""

    module = _fresh_g3f_module()
    root, activation, _digests, document = _prepared_activation(tmp_path)
    claim = _claim_path(root, document)
    prior = b"PRIOR_SYNTHETIC_PROCESS_CLAIM\n"
    claim.write_bytes(prior)

    with pytest.raises(module.Test3G3FOneShotError, match="already exists"):
        module.load_owner_activation_capability(activation, repository_root=str(root))

    assert claim.read_bytes() == prior  # the claim is never overwritten
    assert module._local_state_report()["activation_capability_issued"] is False
    _real_mode_stop(None, module=module)


def test_a_second_module_instance_cannot_replay_a_claimed_activation(tmp_path: Path) -> None:
    """Replay protection survives the module instance: the on-disk claim is what refuses.

    The first independent instance verifies and exclusively claims a synthetic activation.  A
    second, wholly independent instance is then given the identical activation bytes and the
    identical repository root, which is exactly the replay a fresh process would attempt.  The
    canonical imported module is never reloaded or spent here.
    """

    first = _fresh_g3f_module()
    root, activation, digests, document = _prepared_activation(
        tmp_path,
        name="cross-instance-replay-repository",
    )

    capability = first.load_owner_activation_capability(activation, repository_root=str(root))
    assert capability.reviewed_digests == digests
    assert first._local_state_report()["activation_capability_issued"] is True

    claim = _claim_path(root, document)
    claimed_bytes = claim.read_bytes()
    assert claim.is_file() and not claim.is_symlink()

    second = _fresh_g3f_module()
    with pytest.raises(second.Test3G3FOneShotError, match="already exists"):
        second.load_owner_activation_capability(activation, repository_root=str(root))

    # The persistent claim is never rewritten, extended or truncated by the refused replay.
    assert claim.read_bytes() == claimed_bytes
    assert claim.is_file() and not claim.is_symlink()

    # The replaying instance holds no capability, and its real mode still stops before any row.
    assert second._local_state_report()["activation_capability_issued"] is False
    _real_mode_stop(None, module=second)

    # The refused replay did not spend, share or disturb the one genuinely issued capability.
    first_report = first._local_state_report()
    assert first_report["activation_capability_issued"] is True
    assert first_report["activation_capability_spent"] is False


def test_claim_collisions_and_unsafe_claim_directories_are_terminal(tmp_path: Path) -> None:
    # A missing claim directory is a refusal; nothing is created to satisfy it.
    absent = _fresh_g3f_module()
    root, activation, _digests, document = _prepared_activation(
        tmp_path,
        name="absent-directory",
        create_claim_directory=False,
    )
    with pytest.raises(absent.Test3G3FOneShotError, match="claim directory"):
        absent.load_owner_activation_capability(activation, repository_root=str(root))
    assert not _claim_directory(root, document).exists()

    # A symlinked claim directory cannot be traversed, and its target stays untouched.
    linked = _fresh_g3f_module()
    root2, activation2, _d2, document2 = _prepared_activation(
        tmp_path,
        name="linked-directory",
        create_claim_directory=False,
    )
    outside = tmp_path / "outside-claim-target"
    outside.mkdir()
    directory = _claim_directory(root2, document2)
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.symlink_to(outside, target_is_directory=True)
    with pytest.raises(linked.Test3G3FOneShotError, match="claim directory"):
        linked.load_owner_activation_capability(activation2, repository_root=str(root2))
    assert list(outside.iterdir()) == []

    # A directory sitting at the claim name collides exclusively and is never replaced.
    collision = _fresh_g3f_module()
    root3, activation3, _d3, document3 = _prepared_activation(
        tmp_path,
        name="collision-directory",
    )
    _claim_path(root3, document3).mkdir()
    with pytest.raises(collision.Test3G3FOneShotError, match="already exists"):
        collision.load_owner_activation_capability(activation3, repository_root=str(root3))
    assert _claim_path(root3, document3).is_dir()

    # A symlink sitting at the claim name is refused and its target is never created.
    symlinked = _fresh_g3f_module()
    root4, activation4, _d4, document4 = _prepared_activation(
        tmp_path,
        name="symlinked-claim",
    )
    never = tmp_path / "never-created-claim-target"
    _claim_path(root4, document4).symlink_to(never)
    with pytest.raises(symlinked.Test3G3FOneShotError, match="already exists"):
        symlinked.load_owner_activation_capability(activation4, repository_root=str(root4))
    assert not never.exists()

    for module in (absent, linked, collision, symlinked):
        assert module._local_state_report()["activation_capability_issued"] is False
        _real_mode_stop(None, module=module)


def test_activation_loader_refuses_every_hostile_document(tmp_path: Path) -> None:
    root, _activation, digests, document = _prepared_activation(tmp_path)
    paths = list(g3f.REVIEWED_IMPLEMENTATION_PATHS)

    hostile_payloads = (
        _activation_payload(digests, fit_permit_budget=5),
        _activation_payload(digests, fit_permit_budget=True),
        _activation_payload(digests, recovery_lineage_id=""),
        _activation_payload(digests, override_id=""),
        _activation_payload(digests, recovery_lineage_id="lineage/with/separators"),
        _activation_payload(
            digests,
            recovery_lineage_id=min(g3f.FORBIDDEN_HISTORICAL_IDENTITIES),
        ),
        _activation_payload(digests, protocol_id="MES_TEST3_SOMETHING_ELSE"),
        _activation_payload(digests, protocol_sha256="7" * 64),
        _activation_payload(digests, target_space_id="TARGET_SPACE_999"),
        _activation_payload(digests, implementation_paths=paths[:5]),
        _activation_payload(digests, implementation_paths=[*paths, "tools/extra.py"]),
        _activation_payload(digests, implementation_paths=[paths[1], paths[0], *paths[2:]]),
        _activation_payload(digests, implementation_paths=[*paths[:5], "tools/other.py"]),
        _activation_payload(digests, implementation_path_sha256=list(digests[:5])),
        _activation_payload(digests, implementation_path_sha256=["4" * 64] * 6),
        _activation_payload(digests, runtime_evidence={"root": "only"}),
        _activation_payload(
            digests,
            runtime_evidence=_runtime_evidence(
                reservation_name="synthetic-placeholder-namespace"
            ),
        ),
        _activation_payload(
            digests,
            runtime_evidence=_runtime_evidence(
                permit_names=["synthetic-placeholder-permit-1"] * 4
            ),
        ),
        _activation_payload(digests, runtime_evidence=_runtime_evidence(root="../escape")),
        _activation_payload(digests, runtime_evidence=_runtime_evidence(namespace="")),
        _activation_payload(
            digests,
            runtime_evidence=_runtime_evidence(
                permit_names=[f"synthetic-placeholder-permit-{i}" for i in (1, 2, 3)]
            ),
        ),
    )
    for index, hostile in enumerate(hostile_payloads):
        module = _fresh_g3f_module()
        path = _write_activation(tmp_path / f"hostile-{index}", hostile)
        with pytest.raises(module.Test3G3FOneShotError):
            module.load_owner_activation_capability(path, repository_root=str(root))
        assert module._local_state_report()["activation_capability_issued"] is False

    missing = _fresh_g3f_module()
    accepted = _activation_payload(digests)
    accepted.pop("runtime_evidence")
    path = _write_activation(tmp_path / "hostile-missing-key", accepted)
    with pytest.raises(missing.Test3G3FOneShotError, match="closed key set"):
        missing.load_owner_activation_capability(path, repository_root=str(root))

    additional = _fresh_g3f_module()
    extra = _activation_payload(digests)
    extra["unexpected"] = "value"
    path = _write_activation(tmp_path / "hostile-extra-key", extra)
    with pytest.raises(additional.Test3G3FOneShotError, match="closed key set"):
        additional.load_owner_activation_capability(path, repository_root=str(root))

    # An envelope that carries anything beyond the payload and its digest is refused, and a
    # digest that does not cover the exact nested payload is refused.
    broadened = _fresh_g3f_module()
    envelope = _envelope(_activation_payload(digests))
    envelope["extra_envelope_field"] = "value"
    path = tmp_path / "hostile-envelope-key"
    path.write_bytes(_canonical(envelope))
    with pytest.raises(broadened.Test3G3FOneShotError, match="closed envelope key set"):
        broadened.load_owner_activation_capability(str(path), repository_root=str(root))

    forged = _fresh_g3f_module()
    path = _write_activation(
        tmp_path / "hostile-forged-digest",
        _activation_payload(digests),
        digest="b" * 64,
    )
    with pytest.raises(forged.Test3G3FOneShotError, match="does not cover the exact nested"):
        forged.load_owner_activation_capability(path, repository_root=str(root))

    # A digest that covers the envelope rather than only the payload is refused, which is
    # exactly the self-referential shape this envelope replaces.
    self_referential = _fresh_g3f_module()
    payload = _activation_payload(digests)
    placeholder = _envelope(payload, digest="0" * 64)
    path = tmp_path / "hostile-self-referential"
    path.write_bytes(
        _canonical(
            _envelope(payload, digest=hashlib.sha256(_canonical(placeholder)).hexdigest())
        )
    )
    with pytest.raises(
        self_referential.Test3G3FOneShotError,
        match="does not cover the exact nested",
    ):
        self_referential.load_owner_activation_capability(
            str(path),
            repository_root=str(root),
        )

    # Valid JSON with a correct payload digest is still refused unless the bytes are canonical.
    noncanonical = _fresh_g3f_module()
    path = tmp_path / "hostile-noncanonical"
    path.write_text(
        json.dumps(_envelope(_activation_payload(digests)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(noncanonical.Test3G3FOneShotError, match="canonical UTF-8 envelope"):
        noncanonical.load_owner_activation_capability(str(path), repository_root=str(root))

    # No capability was issued and no activation was claimed, so a real run still stops with
    # zero permits and no callback.
    assert not _claim_path(root, document).exists()
    for module in (missing, additional):
        assert module._local_state_report()["activation_capability_issued"] is False
    _real_mode_stop(None)


def test_activation_loader_refuses_duplicate_keys_nonfinite_and_invalid_utf8(
    tmp_path: Path,
) -> None:
    root, _activation, digests, document = _prepared_activation(tmp_path)
    body = _canonical(_envelope(_activation_payload(digests))).decode("utf-8")

    duplicate = '{"activation_payload_sha256":"' + "0" * 64 + '",' + body[1:]
    duplicate_path = tmp_path / "duplicate-keys"
    duplicate_path.write_text(duplicate, encoding="utf-8")

    nonfinite_path = tmp_path / "nonfinite"
    nonfinite_path.write_text(
        body.replace('"fit_permit_budget":4', '"fit_permit_budget":NaN'),
        encoding="utf-8",
    )

    overflow_path = tmp_path / "overflow"
    overflow_path.write_text(
        body.replace('"fit_permit_budget":4', '"fit_permit_budget":1e999'),
        encoding="utf-8",
    )

    invalid_path = tmp_path / "invalid-utf8"
    invalid_path.write_bytes(body.encode("utf-8") + b"\xff\xfe")

    truncated_path = tmp_path / "not-json"
    truncated_path.write_text("[1, 2, 3]\n", encoding="utf-8")

    cases = (
        (duplicate_path, "duplicate key"),
        (nonfinite_path, "nonfinite"),
        (overflow_path, "nonfinite"),
        (invalid_path, "UTF-8"),
        (truncated_path, None),
    )
    for path, match in cases:
        module = _fresh_g3f_module()
        with pytest.raises(module.Test3G3FOneShotError, match=match):
            module.load_owner_activation_capability(str(path), repository_root=str(root))
        assert module._local_state_report()["activation_capability_issued"] is False

    assert not _claim_path(root, document).exists()
    _real_mode_stop(None)


def test_activation_loader_refuses_symlinked_relative_and_nonregular_inputs(
    tmp_path: Path,
) -> None:
    root, activation, _digests, document = _prepared_activation(tmp_path)

    linked = tmp_path / "linked-activation"
    linked.symlink_to(Path(activation))
    directory = tmp_path / "activation-directory"
    directory.mkdir()
    linked_root = tmp_path / "linked-repository"
    linked_root.symlink_to(root)

    cases = (
        (str(linked), str(root), "non-symlinked regular file"),
        (str(directory), str(root), "non-symlinked regular file"),
        ("synthetic-repository-activation-file", str(root), "absolute path string"),
        (activation, "synthetic-repository", "absolute path string"),
        (activation, str(linked_root), "non-symlinked directory"),
    )
    for activation_path, repository_root, match in cases:
        module = _fresh_g3f_module()
        with pytest.raises(module.Test3G3FOneShotError, match=match):
            module.load_owner_activation_capability(
                activation_path,
                repository_root=repository_root,
            )
        assert module._local_state_report()["activation_capability_issued"] is False

    for hostile in ("/etc/hosts", "../outside.py", "src/../../escape.py", "src\\windows.py"):
        with pytest.raises(g3f.Test3G3FOneShotError):
            g3f._repository_file(str(root), hostile)

    replaced = root.joinpath(*g3f.REVIEWED_IMPLEMENTATION_PATHS[0].split("/"))
    replaced.unlink()
    replaced.symlink_to(root.joinpath(*g3f.REVIEWED_IMPLEMENTATION_PATHS[1].split("/")))
    symlinked = _fresh_g3f_module()
    with pytest.raises(
        symlinked.Test3G3FOneShotError,
        match="symlinked reviewed implementation path",
    ):
        symlinked.load_owner_activation_capability(activation, repository_root=str(root))

    replaced.unlink()
    replaced.mkdir()
    directory_path = _fresh_g3f_module()
    with pytest.raises(directory_path.Test3G3FOneShotError, match="not a regular file"):
        directory_path.load_owner_activation_capability(activation, repository_root=str(root))

    assert not _claim_path(root, document).exists()
    _real_mode_stop(None)


def _filesystem_rename_surfaces(source: str) -> list[str]:
    # Renaming/replacing a filesystem entry is rejected semantically, not by raw substring: an
    # explanatory sentence or an ordinary non-filesystem string ``.replace`` call is not a write
    # surface, while a real ``os`` call, a directly imported alias or a dynamic lookup is.
    filesystem_rename_names = frozenset({"rename", "renames", "replace"})
    tree = ast.parse(source)
    os_module_names = {
        alias.asname or "os"
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "os"
    }
    rename_surfaces: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr in filesystem_rename_names
            and isinstance(node.value, ast.Name)
            and node.value.id in os_module_names
        ):
            rename_surfaces.append(f"{node.value.id}.{node.attr}")
        elif isinstance(node, ast.ImportFrom) and node.module == "os" and node.level == 0:
            rename_surfaces.extend(
                f"import:os.{alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                for alias in node.names
                if alias.name in filesystem_rename_names
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in os_module_names
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value in filesystem_rename_names
        ):
            rename_surfaces.append(f"getattr:{node.args[1].value}")
    return rename_surfaces


def test_filesystem_rename_detector_resolves_original_imported_names_and_aliases() -> None:
    assert _filesystem_rename_surfaces(
        "from os import replace as move\nmove('source', 'destination')\n"
    ) == ["import:os.replace as move"]
    assert _filesystem_rename_surfaces(
        "import os as operating_system\noperating_system.rename('source', 'destination')\n"
    ) == ["operating_system.rename"]
    assert _filesystem_rename_surfaces(
        "message = 'rename and replace are prohibited'\ncleaned = 'ordinary'.replace('o', 'a')\n"
    ) == []


def test_module_imports_only_the_closed_allowlist_and_writes_only_the_activation_claim() -> None:
    source_path = Path(g3f.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            imported.add(node.module)

    assert imported <= g3f.ALLOWED_IMPORT_ROOTS
    for name in imported:
        for prefix in g3f.FORBIDDEN_IMPORT_PREFIXES:
            assert name != prefix and not name.startswith(prefix + ".")

    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in called
    assert "eval" not in called and "exec" not in called

    for forbidden in (
        "artifacts/",
        ".json",
        ".parquet",
        "Path(",
        "pickle.",
        "O_RDWR",
        "O_APPEND",
        "O_TRUNC",
        "os.remove",
        "os.unlink",
        "os.mkdir",
        "makedirs",
        "print(",
    ):
        assert forbidden not in source

    assert _filesystem_rename_surfaces(source) == []

    # There is exactly one write surface in the whole module: the exclusive, non-overwriting
    # create-once record writer that publishes the activation replay claim, the reservation, the
    # four ordered permits and the one terminal. One create, one write loop, and exactly two
    # fsyncs for the record and its directory.
    assert source.count("os.O_CREAT") == 1
    assert source.count("os.O_EXCL") == 1
    assert source.count("os.write(") == 1
    assert source.count("os.fsync(") == 2
    assert source.count("def _create_record_once(") == 1


# ---------------------------------------------------------------------------------------------
# Real execution completion.
#
# Every fixture below is synthetic and in memory, and every durable record lives under a
# per-test ``tmp_path``. No test here reads a data artifact, reaches a provider, requests or
# constructs a real target, consumes the real target space, or creates a real activation file.
# ---------------------------------------------------------------------------------------------

_SESSION_ROWS = 9
_TRAIN_SESSIONS = 30

#: The injected overlapping TRAIN session opens five hours earlier than an ordinary session, so
#: every injected row carries a unique identity and a unique decision time on a date that is also
#: a holdout date. The synthetic duplicate rejection of the stage is left completely intact; the
#: fixture simply stops shadowing it so the intended purge gate is the control that fires.
_OVERLAP_TRAIN_OPEN_OFFSET_MINUTES = -300

#: Deterministic low-discrepancy multipliers. They give three effectively uncorrelated predictor
#: sequences plus one unexplained response component, so the synthetic design is well conditioned
#: and full rank without any random generator.
_LOW_DISCREPANCY_MULTIPLIERS = (
    0.6180339887498949,
    0.4142135623730951,
    0.7320508075688772,
    0.2360679774997897,
)

#: A finite, full-rank, but nearly collinear synthetic TRAIN ``X60`` column. The spread stays far
#: above the frozen rank tolerance, so the structural prefit passes and least squares legitimately
#: returns a huge finite coefficient.
_DEGENERATE_VOL_60M = 0.5
_DEGENERATE_X60_SPREAD = 1.0e-9


def _unit(index: int, multiplier: float) -> float:
    """One deterministic low-discrepancy value in ``[0, 1)``; no random generator is used."""

    return math.fmod(float(index) * multiplier, 1.0)


def _recovery_values(
    index: int,
    harmonic: Harmonic,
    *,
    degenerate: bool,
) -> tuple[tuple[float, float, float], float]:
    """Well-conditioned synthetic predictors and one strictly positive forward variance.

    The three volatilities come from independent low-discrepancy sequences, so the frozen design
    ``2 * ln(vol)`` stays full rank and far from collinear, and the response is a mild linear
    function of that design plus one unexplained component. ``degenerate`` keeps every value
    finite and positive but compresses ``X60`` into a ``1e-9`` band around a constant, which is
    the controlled adversarial condition that makes least squares return a huge finite result.
    """

    u60, u120, u240, u_noise = (
        _unit(index, multiplier) for multiplier in _LOW_DISCREPANCY_MULTIPLIERS
    )
    vol_60m = 0.25 + 0.55 * u60
    vol_120m = 0.30 + 0.45 * u120
    vol_240m = 0.35 + 0.40 * u240
    if degenerate:
        vol_60m = _DEGENERATE_VOL_60M * math.exp(0.5 * _DEGENERATE_X60_SPREAD * u_noise)
    x60, x120, x240 = (2.0 * math.log(value) for value in (vol_60m, vol_120m, vol_240m))
    log_variance = (
        -3.4
        + 0.20 * x60
        + 0.12 * x120
        + 0.08 * x240
        + 0.05 * harmonic.session_sin
        + 0.04 * harmonic.session_cos
        + 0.30 * (u_noise - 0.5)
    )
    return (vol_60m, vol_120m, vol_240m), math.exp(log_variance)


def _recovery_specs(
    *,
    holdout_2022_sessions: int = 22,
    holdout_2023_sessions: int = 24,
    train_sessions: int = _TRAIN_SESSIONS,
    wrong_holdout_year: bool = False,
    overlapping_train_session: bool = False,
) -> list[tuple[date, str, str, int]]:
    """Ordered ``(session_date, role_wf_2022, role_wf_2023, session_open_offset)`` specs."""

    specs: list[tuple[date, str, str, int]] = [
        (date(2021, 1, 4) + timedelta(days=index), "TRAIN", "TRAIN", 0)
        for index in range(train_sessions)
    ]
    if overlapping_train_session:
        specs.append(
            (date(2022, 3, 10), "TRAIN", "TRAIN", _OVERLAP_TRAIN_OPEN_OFFSET_MINUTES)
        )
    specs.extend(
        (date(2022, 3, 1) + timedelta(days=index), "VALIDATION", "UNUSED", 0)
        for index in range(holdout_2022_sessions)
    )
    specs.extend(
        (
            date(2023, 3, 1) + timedelta(days=index),
            "UNUSED",
            "VALIDATION",
            0,
        )
        for index in range(holdout_2023_sessions)
    )
    if wrong_holdout_year:
        specs = [
            (
                session_date,
                role_2022,
                "VALIDATION" if role_2022 == "VALIDATION" else role_2023,
                open_offset,
            )
            for session_date, role_2022, role_2023, open_offset in specs
        ]
    return sorted(specs, key=lambda item: (item[0], item[3]))


def _recovery_fields(
    *,
    rows_per_session: int = _SESSION_ROWS,
    train_rows_per_session: int | None = None,
    degenerate_train_predictors: bool = False,
    **spec_options: object,
) -> dict[str, object]:
    """Build one synthetic, structurally sufficient G3-P delivery payload."""

    controls: list[_StubControl] = []
    predictor_rows: list[PredictorStatusRow] = []
    target_rows: list[TargetStatusRow] = []
    values: dict[str, tuple[float, float, float]] = {}
    variances: dict[str, float] = {}
    harmonics: dict[str, Harmonic] = {}
    index = 0
    for session_date, role_2022, role_2023, open_offset in _recovery_specs(**spec_options):
        session_open = datetime.combine(session_date, time(14, 45), tzinfo=UTC) + timedelta(
            minutes=open_offset
        )
        is_train = (role_2022, role_2023) == ("TRAIN", "TRAIN")
        session_rows = rows_per_session
        if train_rows_per_session is not None and is_train:
            session_rows = train_rows_per_session
        for slot in range(session_rows):
            moment = session_open + timedelta(minutes=15 * slot)
            identity = f"{moment.isoformat()}|instrument_id=12345"
            angle = 2.0 * math.pi * slot / 22
            harmonic = Harmonic(
                slot=slot,
                n_slots=22,
                session_sin=math.sin(angle),
                session_cos=math.cos(angle),
            )
            predictors, variance = _recovery_values(
                index,
                harmonic,
                degenerate=degenerate_train_predictors and is_train,
            )
            controls.append(
                _StubControl(
                    identity,
                    moment,
                    session_date.isoformat(),
                    role_2022,
                    role_2023,
                )
            )
            predictor_rows.append(
                PredictorStatusRow(identity, moment, RowStatus.PREDICTOR_USABLE.value)
            )
            target_rows.append(
                TargetStatusRow(
                    identity,
                    moment,
                    moment + timedelta(minutes=60),
                    RowStatus.TARGET_USABLE.value,
                    variance,
                    math.log(variance),
                )
            )
            values[identity] = predictors
            variances[identity] = variance
            harmonics[identity] = harmonic
            index += 1
    return {
        "controls": tuple(controls),
        "predictor_status_rows": tuple(predictor_rows),
        "predictor_values": values,
        "target_status_rows": tuple(target_rows),
        "target_variance_by_identity": variances,
        "harmonic_by_identity": harmonics,
    }


def _prepared_execution(
    tmp_path: Path,
    module,
    *,
    name: str = "recovery-repository",
) -> tuple[Path, dict[str, object], object]:
    """Verify a synthetic activation and open one durable execution authority."""

    root, activation, _digests, payload = _prepared_activation(tmp_path, name=name)
    capability = module.load_owner_activation_capability(activation, repository_root=str(root))
    authority = module.open_execution_authority(capability)
    return root, payload, authority


def _deliver(module, fields: Mapping[str, object]) -> object:
    handle, marker = module._claim_g3p_delivery_handle()
    return handle(marker, handoff_id=module.EXPECTED_HANDOFF_ID)(**fields)


def _recovery_rows(module, fields: Mapping[str, object]) -> tuple[object, ...]:
    """Rebuild, in the same order, the eligible rows the stage derives from one payload.

    Every synthetic row here is usable, so this mirrors the stage's own ordered intake and lets a
    test recompute a pair's TRAIN quantities from the delivered values alone.
    """

    values = fields["predictor_values"]
    variances = fields["target_variance_by_identity"]
    harmonics = fields["harmonic_by_identity"]
    return tuple(
        module.OneShotEligibleRow(
            decision_identity=control.identity,
            decision_time_utc=control.timestamp,
            session_id=control.session_id,
            role_wf_2022=control.role_2022,
            role_wf_2023=control.role_2023,
            harmonic=harmonics[control.identity],
            rv_fwd_60=float(variances[control.identity]),
            realized_vol_60m=float(values[control.identity][0]),
            realized_vol_120m=float(values[control.identity][1]),
            realized_vol_240m=float(values[control.identity][2]),
            origin=module.RowOrigin.G3P_IN_PROCESS_HANDOFF,
        )
        for control in fields["controls"]
    )


def _read_record(root: Path, payload: Mapping[str, object], name: str) -> dict:
    return json.loads(_record_path(root, payload, name).read_text(encoding="utf-8"))


def _evidence(payload: Mapping[str, object]) -> Mapping[str, object]:
    evidence = payload["runtime_evidence"]
    assert isinstance(evidence, Mapping)
    return evidence


def test_full_real_trace_reserves_fits_and_writes_exactly_one_terminal(tmp_path: Path) -> None:
    """verify -> reservation -> handoff -> four internal fits -> metrics -> terminal."""

    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    evidence = _evidence(payload)

    binding = module.assert_execution_authority_reserved(authority)
    assert binding["reservation_status"] == module.RESERVATION_STATUS
    assert binding["protocol_id"] == PROTOCOL_ID
    assert binding["target_space_id"] == TARGET_SPACE_ID
    reservation = _read_record(root, payload, str(evidence["reservation_name"]))
    assert reservation["record_kind"] == module.RESERVATION_RECORD_KIND
    assert reservation["validation_status"] == "UNOPENED"
    assert reservation["final_test_status"] == "SEALED"

    # No permit and no terminal may exist before a single row moves.
    for name in (*evidence["permit_names"], evidence["terminal_name"]):
        assert not _record_path(root, payload, str(name)).exists()

    module.bind_source_evidence(
        authority,
        {"stage": "SYNTHETIC_G3P_STAND_IN", "rows_delivered": True},
    )
    assert _deliver(module, _recovery_fields()) is None  # no raw row returns to the caller

    terminal = _read_record(root, payload, str(evidence["terminal_name"]))
    assert terminal["record_kind"] == module.TERMINAL_RECORD_KIND
    assert terminal["disposition"] in {item.value for item in TerminalDisposition}
    assert terminal["disposition"] not in {"UNDERPOWERED_STOP", "INVALID_EVIDENCE"}
    assert terminal["pair_order"] == [
        "RVBASE001/WF_2022",
        "RVHAR001/WF_2022",
        "RVBASE001/WF_2023",
        "RVHAR001/WF_2023",
    ]
    assert terminal["permits"] == {
        "names": list(evidence["permit_names"]),
        "created": 4,
        "consumed": 4,
        "callback_starts": 4,
        "validated_outputs": 4,
        "refused_requests": 0,
        "poisoned": False,
        "sealed": True,
        "unreplenished": True,
    }
    assert terminal["counters"] == {
        "permits_created": 4,
        "permits_consumed": 4,
        "real_fold_fit_calls": 4,
        "real_models_fitted": 2,
        "real_coefficients_computed": 4,
        "duan_factors_computed": 4,
        "real_forecasts_computed": terminal["metrics"]["pooled"]["row_count"] * 2,
        "real_qlike_evaluations": terminal["metrics"]["pooled"]["row_count"] * 2,
        "real_bootstrap_replicates": 6_000,
        "validation_rows_read": 0,
        "final_test_rows_read": 0,
    }
    assert terminal["validation_status"] == "UNOPENED"
    assert terminal["final_test_status"] == "SEALED"
    assert terminal["source_and_g3p_binding"]["stage"] == "SYNTHETIC_G3P_STAND_IN"

    # Every ordered permit exists, each bound to its own pair and to the reservation.
    for ordinal, name in enumerate(evidence["permit_names"], start=1):
        permit = _read_record(root, payload, str(name))
        assert permit["record_kind"] == module.PERMIT_RECORD_KIND
        assert permit["ordinal"] == ordinal
        assert permit["reservation_sha256"] == binding["reservation_sha256"]
        model_id, fold_id = module.EXPECTED_PAIR_ORDER[ordinal - 1]
        assert (permit["model_id"], permit["fold_id"]) == (model_id, fold_id)
        assert permit["estimator"] == "numpy.linalg.lstsq(rcond=None)"

    report = module.execution_authority_report(authority)
    assert report["disposition"] == terminal["disposition"]
    assert report["terminal_record_sha256"] == terminal["terminal_record_sha256"]

    cleanup = module.close_execution_authority(authority)
    assert cleanup["durable_records_deleted"] == 0
    assert cleanup["durable_records_mutated"] == 0
    assert cleanup["memory_erasure_claimed"] is False
    assert _record_path(root, payload, str(evidence["terminal_name"])).is_file()


def test_terminal_digest_is_machine_computed_and_not_self_referential(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())
    terminal = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))

    declared = terminal.pop("terminal_record_sha256")
    assert hashlib.sha256(_canonical(terminal)).hexdigest() == declared
    # The digest of the whole published record is necessarily a different value.
    terminal["terminal_record_sha256"] = declared
    assert hashlib.sha256(_canonical(terminal)).hexdigest() != declared


def test_recorded_fits_use_the_frozen_estimator_pair_order_and_coefficient_bytes(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())
    terminal = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))

    assert len(terminal["fits"]) == 4
    for ordinal, fit in enumerate(terminal["fits"], start=1):
        model_id, fold_id = module.EXPECTED_PAIR_ORDER[ordinal - 1]
        assert (fit["ordinal"], fit["model_id"], fit["fold_id"]) == (ordinal, model_id, fold_id)
        assert fit["column_names"] == list(MODEL_COLUMNS[model_id])
        assert fit["coefficient_dimension"] == len(MODEL_COLUMNS[model_id])
        assert fit["rank"] == len(MODEL_COLUMNS[model_id])
        assert len(fit["singular_values"]) == len(MODEL_COLUMNS[model_id])
        assert fit["condition_number"] is not None and fit["condition_number"] > 0.0
        assert fit["train_row_count"] > len(MODEL_COLUMNS[model_id])
        assert fit["numerical_identity"]["estimator"] == "numpy.linalg.lstsq(rcond=None)"
        assert fit["numerical_identity"]["numpy_version"] == np.__version__
        assert fit["forecast_floor_or_clipping_applied"] is False
        expected = hashlib.sha256(
            np.ascontiguousarray(
                np.asarray(fit["coefficients"], dtype="<f8").reshape(-1)
            ).tobytes(order="C")
        ).hexdigest()
        assert fit["coefficient_sha256"] == expected


def test_coefficient_digest_is_little_endian_float64_c_order_bytes_never_text() -> None:
    beta = np.array([1.5, -2.25, 0.0, 7.125, 1e-9, -3.0], dtype=np.float64)
    expected = hashlib.sha256(
        np.ascontiguousarray(np.asarray(beta, dtype="<f8").reshape(-1)).tobytes(order="C")
    ).hexdigest()

    assert g3f._coefficient_sha256(beta) == expected
    assert g3f._coefficient_sha256(list(beta)) == expected
    assert g3f._coefficient_sha256(np.asfortranarray(beta)) == expected
    assert g3f._coefficient_sha256(beta) != hashlib.sha256(
        json.dumps([float(value) for value in beta]).encode("utf-8")
    ).hexdigest()
    with pytest.raises(g3f.Test3G3FOneShotError):
        g3f._coefficient_sha256(np.array([1.0, math.nan], dtype=np.float64))


def test_duan_is_fold_and_model_local_and_forecasts_are_unclipped(tmp_path: Path) -> None:
    """Four separately computed model/fold-local factors, never four numerically unique values.

    The frozen contract requires one Duan factor per model/fold pair, computed from that pair's
    own TRAIN residuals. Symmetric fold TRAIN populations can legitimately give the same model
    equal factors in both folds, so numeric inequality is not required and is not asserted. Each
    factor is instead recomputed mechanically from that pair's TRAIN design and response and the
    coefficients recorded for it.
    """

    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    fields = _recovery_fields()
    _deliver(module, fields)
    terminal = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))

    factors = {
        (fit["model_id"], fit["fold_id"]): fit["duan_smearing_factor"]
        for fit in terminal["fits"]
    }
    # Exactly the four ordered model/fold keys, each carrying one positive finite factor.
    assert len(terminal["fits"]) == 4
    assert set(factors) == set(module.EXPECTED_PAIR_ORDER)
    assert len(factors) == 4
    for factor in factors.values():
        assert factor > 0.0 and math.isfinite(factor)

    rows = _recovery_rows(module, fields)
    response = module.build_response_vector(rows)
    designs = {model_id: module.build_design_matrix(model_id, rows) for model_id in MODEL_ORDER}
    for fit in terminal["fits"]:
        model_id = str(fit["model_id"])
        fold_id = str(fit["fold_id"])
        train = [index for index, row in enumerate(rows) if row.fold_role(fold_id) == "TRAIN"]
        # The factor is scoped to this pair's own fold TRAIN population, never to holdout rows.
        assert len(train) == fit["train_row_count"]
        assert len(train) < len(rows)
        beta = np.asarray(fit["coefficients"], dtype=np.float64)
        # The oracle recomputes the fitted values through the same explicit checked kernel the
        # module uses, so the comparison is against the identical arithmetic and the oracle
        # cannot emit a BLAS backend ``RuntimeWarning`` of its own.
        fitted = module._checked_matrix_vector_product(
            designs[model_id][train],
            beta,
            expected_rows=len(train),
            label=f"{model_id}/{fold_id} oracle fitted TRAIN log-variance",
        )
        residuals = response[train] - fitted
        assert fit["duan_smearing_factor"] == pytest.approx(
            float(np.mean(np.exp(residuals))), rel=1e-12, abs=1e-15
        )
        assert fit["duan_scope"] == "FOLD_AND_MODEL_LOCAL_TRAIN_RESIDUALS_ONLY"
        assert fit["forecast_floor_or_clipping_applied"] is False


def test_a_huge_finite_least_squares_result_raises_instead_of_warning(tmp_path: Path) -> None:
    """Adversarial numerics: finite inputs, a huge finite fit, and no escaping warning.

    The synthetic TRAIN ``X60`` column is compressed into a ``1e-9`` band, which stays full rank
    under the frozen prefit but makes least squares return a huge finite coefficient. The extreme
    result then leaves the representable range, and the stage must fail closed into its single
    ``INVALID_EVIDENCE`` terminal rather than emit a NumPy ``RuntimeWarning``, clip, floor or
    absorb the value.

    Two fail-closed routes are equally correct here and both are asserted as one closed set: the
    checked prediction kernel raises ``FloatingPointError`` from its own narrowly scoped raised
    state, or it proves the product non-finite and raises the module's ordinary error, or the
    guarded semantic Duan/back-transform region raises ``FloatingPointError``. Which route fires
    depends on where the extreme magnitude first leaves the range; the terminal, the counters and
    the spent, poisoned, unreplaced permit asserted below are identical either way. What is *not*
    permitted, and is asserted explicitly, is a ``Warning`` escaping instead of an error.
    """

    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module, name="numerical-repository")
    evidence = _evidence(payload)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})

    fields = _recovery_fields(degenerate_train_predictors=True)
    # Every delivered input is finite and strictly positive; only the fit result is extreme.
    for predictors in fields["predictor_values"].values():
        assert all(math.isfinite(value) and value > 0.0 for value in predictors)
    for variance in fields["target_variance_by_identity"].values():
        assert math.isfinite(variance) and variance > 0.0

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises((FloatingPointError, module.Test3G3FOneShotError)) as extreme:
            _deliver(module, fields)
    # An error, never a warning promoted to an error, and never an underpowered pre-fit stop:
    # the permit was already spent, so this must be the post-permit fail-closed route.
    assert not isinstance(extreme.value, Warning)
    assert not isinstance(extreme.value, module.Test3G3FUnderpoweredStop)

    terminal = _read_record(root, payload, str(evidence["terminal_name"]))
    assert terminal["disposition"] == "INVALID_EVIDENCE"
    assert terminal["fits"] == []
    assert terminal["bootstrap"] == []
    assert terminal["metrics"] is None
    assert terminal["gates"] is None

    counters = terminal["counters"]
    # Nothing succeeded downstream of the failed fit.
    assert counters["real_fold_fit_calls"] == 0
    assert counters["real_forecasts_computed"] == 0
    assert counters["real_qlike_evaluations"] == 0
    assert counters["real_bootstrap_replicates"] == 0
    assert counters["duan_factors_computed"] == 0

    # The issued permit was consumed before its own least-squares call and is never replaced.
    assert counters["permits_created"] == 1
    assert counters["permits_consumed"] == 1
    assert terminal["permits"]["consumed"] == 1
    assert terminal["permits"]["callback_starts"] == 1
    assert terminal["permits"]["validated_outputs"] == 0
    assert terminal["permits"]["poisoned"] is True
    assert terminal["permits"]["sealed"] is False

    # Exactly one terminal and exactly one permit exist beside the claim and the reservation.
    assert {entry.name for entry in _claim_directory(root, payload).iterdir()} == {
        str(evidence["reservation_name"]) + module._ACTIVATION_CLAIM_SUFFIX,
        str(evidence["reservation_name"]),
        str(evidence["permit_names"][0]),
        str(evidence["terminal_name"]),
    }
    assert module.execution_authority_report(authority)["disposition"] == "INVALID_EVIDENCE"
    with pytest.raises(module.Test3G3FOneShotError, match="attempted exactly once"):
        module.record_terminal_stop(
            authority,
            disposition="INVALID_EVIDENCE",
            reasons=("synthetic retry",),
            source_binding={"stage": "SYNTHETIC_RETRY"},
        )


# ---------------------------------------------------------------------------------------------
# Numerical error-state policy.
#
# The strict state is a semantic control, not a backend control. It guards the elementwise
# exponential, division and logarithm arithmetic this stage performs itself, and it is never
# placed around the BLAS/LAPACK-backed least-squares call, whose coefficients are proved
# immediately for exact shape, float64 conversion and finiteness.
#
# The two predictions are no longer BLAS-backed products at all. One explicit checked float64
# kernel validates operand compatibility, evaluates a deterministic non-optimized ``einsum``
# contraction under its own narrowly scoped raised overflow/invalid state, and then proves the
# product. That removes the backend lane flags that made a valid, well-conditioned fit emit a
# ``RuntimeWarning``, while keeping a genuine extreme product on the fail-closed route.
# ---------------------------------------------------------------------------------------------


def _strict_numeric_contexts(source: str) -> list[ast.With]:
    """Every ``with _strict_numerics():`` block in the module source."""

    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.With)
        and any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id == "_strict_numerics"
            for item in node.items
        )
    ]


def _matmul_nodes(node: ast.AST) -> list[ast.BinOp]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.MatMult)
    ]


def _attribute_calls(node: ast.AST, attribute: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == attribute
    ]


def _lstsq_calls(node: ast.AST) -> list[ast.Call]:
    return _attribute_calls(node, "lstsq")


def test_the_frozen_estimator_is_never_placed_under_the_strict_semantic_state() -> None:
    """Structural proof: no BLAS/LAPACK-backed operation sits inside the strict semantic state.

    A blocked, vectorized backend kernel sets hardware floating-point status flags for lanes and
    partial products that never reach the returned result, so a flag observed there describes the
    backend rather than the correctness of the fit. The strict state must therefore cover only
    the elementwise arithmetic this stage performs itself.
    """

    source = Path(g3f.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    # The frozen estimator is still present, exactly once and unchanged.
    assert len(_lstsq_calls(tree)) == 1

    # Four semantic regions stay guarded: Duan and back-transform, per-fold QLIKE, the pooled
    # relative reduction and the bootstrap arithmetic. The estimator is in none of them.
    contexts = _strict_numeric_contexts(source)
    assert len(contexts) == 4
    for context in contexts:
        assert _lstsq_calls(context) == []


def test_no_blas_backed_product_remains_and_one_explicit_einsum_kernel_replaces_them() -> None:
    """Structural proof of the causal fix: the prediction products are not BLAS-backed.

    ``@`` and :func:`numpy.matmul` both dispatch to a blocked, vectorized backend that raises
    hardware floating-point status flags for lanes and partial products which never reach the
    returned result. NumPy surfaces those flags as ``RuntimeWarning`` divide, overflow or invalid
    conditions even outside any ``errstate``, which is exactly what failed a valid fit. The module
    must therefore contain no matrix-multiplication operator and no ``matmul`` call at all, and
    exactly one deterministic non-optimized ``einsum`` contraction in their place.
    """

    source = Path(g3f.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert _matmul_nodes(tree) == []
    assert _attribute_calls(tree, "matmul") == []
    assert _attribute_calls(tree, "dot") == []
    assert _attribute_calls(tree, "tensordot") == []

    einsum_calls = _attribute_calls(tree, "einsum")
    assert len(einsum_calls) == 1
    call = einsum_calls[0]
    # The subscript is the explicit matrix-vector contraction, given positionally and literally.
    assert isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == "ij,j->i"
    # Optimization is disabled, so no BLAS/tensordot path can be selected behind the subscript.
    optimize = [keyword for keyword in call.keywords if keyword.arg == "optimize"]
    assert len(optimize) == 1
    assert isinstance(optimize[0].value, ast.Constant)
    assert optimize[0].value.value is False

    # The contraction sits inside its own narrowly scoped raised state, not the semantic state,
    # so a genuine overflow or invalid operation in the requested arithmetic still raises.
    for context in _strict_numeric_contexts(source):
        assert _attribute_calls(context, "einsum") == []

    guards = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        and any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Attribute)
            and item.context_expr.func.attr == "errstate"
            for item in node.items
        )
    ]
    assert len(guards) == 1
    guard = guards[0]
    # The guard covers exactly the one contraction and nothing else, in particular not lstsq.
    assert len(_attribute_calls(guard, "einsum")) == 1
    assert _lstsq_calls(guard) == []
    assert _matmul_nodes(guard) == []
    guard_call = guard.items[0].context_expr
    assert isinstance(guard_call, ast.Call)
    states = {
        keyword.arg: keyword.value.value
        for keyword in guard_call.keywords
        if isinstance(keyword.value, ast.Constant)
    }
    # Only the two conditions that are genuinely relevant to a product are raised here; nothing
    # is set to "ignore", suppressed, or handed to a warning filter or np.seterr.
    assert states == {"over": "raise", "invalid": "raise"}


def test_the_strict_state_raises_over_divide_and_invalid_but_not_gradual_underflow() -> None:
    """Semantic overflow, division by zero and invalid operations still raise, never warn."""

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with g3f._strict_numerics():
            with pytest.raises(FloatingPointError):
                np.exp(np.array([1.0e6], dtype=np.float64))
            with pytest.raises(FloatingPointError):
                np.divide(np.array([1.0], dtype=np.float64), np.array([0.0], dtype=np.float64))
            with pytest.raises(FloatingPointError):
                np.log(np.array([-1.0], dtype=np.float64))
            # Gradual underflow is an IEEE status, not a semantic defect. It neither raises nor
            # escapes as a warning; the required outputs stay guarded by the explicit
            # strictly-positive and finite checks instead.
            underflowed = np.multiply(
                np.array([1.0e-320], dtype=np.float64),
                np.array([1.0e-10], dtype=np.float64),
            )

    assert float(underflowed[0]) == 0.0


def test_every_linear_algebra_result_is_proved_for_shape_float64_and_finiteness() -> None:
    """The replacement control is an explicit validation, never a clip, floor or absorption."""

    accepted = g3f._finite_float64_vector([1.0, -2.5], expected_size=2, label="probe")
    assert accepted.dtype == np.dtype(np.float64)
    assert accepted.shape == (2,)

    for rejected in (
        [1.0],
        [1.0, 2.0, 3.0],
        [[1.0, 2.0]],
        [1.0, math.inf],
        [1.0, -math.inf],
        [1.0, math.nan],
    ):
        with pytest.raises(g3f.Test3G3FOneShotError):
            g3f._finite_float64_vector(rejected, expected_size=2, label="probe")


def test_the_checked_kernel_computes_the_exact_product_without_a_runtime_warning() -> None:
    """The replacement prediction kernel is exact, deterministic and warning-free."""

    design = np.array([[1.0, -2.0, 0.5], [3.0, 0.25, -4.0]], dtype=np.float64)
    coefficients = np.array([2.0, -1.0, 8.0], dtype=np.float64)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        product = g3f._checked_matrix_vector_product(
            design, coefficients, expected_rows=2, label="probe"
        )

    assert product.dtype == np.dtype(np.float64)
    assert product.shape == (2,)
    # Exact expected values; no clipping, floor, tolerance widening or absorption is applied.
    assert product.tolist() == [8.0, -26.25]
    # Deterministic: the same operands give byte-identical results on repetition.
    assert g3f._checked_matrix_vector_product(
        design, coefficients, expected_rows=2, label="probe"
    ).tolist() == product.tolist()


def test_the_checked_kernel_validates_compatibility_before_it_computes_anything() -> None:
    """Dimension, shape and dtype compatibility are refused before a single product is formed."""

    design = np.array([[1.0, -2.0], [1.0, -3.0]], dtype=np.float64)
    coefficients = np.array([1.0, 2.0], dtype=np.float64)

    rejected: tuple[tuple[object, object, int], ...] = (
        # A vector length that does not match the matrix column count.
        (design, np.array([1.0, 2.0, 3.0], dtype=np.float64), 2),
        # A one-dimensional "matrix" and a two-dimensional "vector".
        (np.array([1.0, 2.0], dtype=np.float64), coefficients, 2),
        (design, np.array([[1.0], [2.0]], dtype=np.float64), 2),
        # A row count that does not match the declared expectation.
        (design, coefficients, 3),
        # A matrix with no columns to contract over.
        (np.zeros((2, 0), dtype=np.float64), np.zeros(0, dtype=np.float64), 2),
        # Operands that do not convert exactly to float64.
        (np.array([["a", "b"], ["c", "d"]]), coefficients, 2),
    )
    for matrix, vector, expected_rows in rejected:
        with pytest.raises(g3f.Test3G3FOneShotError):
            g3f._checked_matrix_vector_product(
                matrix, vector, expected_rows=expected_rows, label="probe"
            )

    for bad_rows in (0, -1, True):
        with pytest.raises(g3f.Test3G3FOneShotError):
            g3f._checked_matrix_vector_product(
                design, coefficients, expected_rows=bad_rows, label="probe"
            )


def test_the_checked_kernel_fails_closed_on_an_extreme_product_and_never_warns() -> None:
    """An extreme product raises into the ordinary fail-closed route instead of warning.

    Either the narrowly scoped raised state stops the contraction with ``FloatingPointError`` or
    the immediate finiteness proof rejects the product with the module's ordinary error. Both are
    the same fail-closed route; neither clips, floors, absorbs or reads a backend status flag.
    """

    design = np.array([[1.0, -2.0], [1.0, -3.0]], dtype=np.float64)
    coefficients = np.full(2, np.finfo(np.float64).max, dtype=np.float64)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises((FloatingPointError, g3f.Test3G3FOneShotError)) as extreme:
            g3f._checked_matrix_vector_product(
                design, coefficients, expected_rows=2, label="probe"
            )
    assert not isinstance(extreme.value, Warning)

    # A non-finite operand is refused on the same route rather than propagated.
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises((FloatingPointError, g3f.Test3G3FOneShotError)) as nonfinite:
            g3f._checked_matrix_vector_product(
                design,
                np.array([math.inf, 1.0], dtype=np.float64),
                expected_rows=2,
                label="probe",
            )
    assert not isinstance(nonfinite.value, Warning)


def test_the_normal_synthetic_path_completes_four_ordered_fits_without_a_runtime_warning(
    tmp_path: Path,
) -> None:
    """The well-conditioned synthetic path must not be failed by a backend status flag."""

    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        assert _deliver(module, _recovery_fields()) is None

    terminal = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))
    assert terminal["disposition"] not in {"UNDERPOWERED_STOP", "INVALID_EVIDENCE"}
    assert [(str(fit["model_id"]), str(fit["fold_id"])) for fit in terminal["fits"]] == list(
        module.EXPECTED_PAIR_ORDER
    )
    assert terminal["permits"]["consumed"] == 4
    assert terminal["permits"]["callback_starts"] == 4
    assert terminal["permits"]["validated_outputs"] == 4
    assert terminal["permits"]["poisoned"] is False
    assert terminal["permits"]["sealed"] is True
    assert terminal["counters"]["real_fold_fit_calls"] == 4
    assert terminal["counters"]["real_bootstrap_replicates"] == 6_000
    for fit in terminal["fits"]:
        assert fit["duan_smearing_factor"] > 0.0
        assert math.isfinite(float(fit["duan_smearing_factor"]))
        assert fit["forecast_floor_or_clipping_applied"] is False


def _stub_lstsq(beta_for: Callable[[int], np.ndarray]) -> Callable[..., tuple]:
    """A stubbed frozen estimator that returns one chosen coefficient vector.

    Everything else it reports is structurally valid, so each case below isolates exactly one
    defective linear-algebra result rather than a rank, singular-value or arity defect.
    """

    def stub(design: np.ndarray, response: np.ndarray, rcond: object = None) -> tuple:
        columns = int(np.asarray(design).shape[1])
        return (
            beta_for(columns),
            np.zeros(0, dtype=np.float64),
            columns,
            np.full(columns, 2.0, dtype=np.float64),
        )

    return stub


@pytest.mark.parametrize(
    "beta_for",
    [
        pytest.param(
            lambda columns: np.full(columns, math.nan, dtype=np.float64),
            id="nonfinite_coefficients",
        ),
        pytest.param(
            lambda columns: np.zeros((columns, 1), dtype=np.float64),
            id="wrong_dimensionality",
        ),
        pytest.param(
            lambda columns: np.full(columns, np.finfo(np.float64).max, dtype=np.float64),
            id="overflowing_matrix_products",
        ),
    ],
)
def test_an_invalid_linear_algebra_result_stops_at_one_invalid_evidence_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    beta_for: Callable[[int], np.ndarray],
) -> None:
    """A non-finite or wrongly shaped linear-algebra result must fail closed, not pass through.

    The first permit is consumed before its own least-squares call, so it stays consumed and the
    budget stays poisoned and unreplaced. Exactly one ``INVALID_EVIDENCE`` terminal is written,
    nothing downstream of the failed fit runs, and there is no retry.
    """

    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    evidence = _evidence(payload)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    monkeypatch.setattr(np.linalg, "lstsq", _stub_lstsq(beta_for))

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        with pytest.raises(module.Test3G3FOneShotError):
            _deliver(module, _recovery_fields())

    terminal = _read_record(root, payload, str(evidence["terminal_name"]))
    assert terminal["disposition"] == "INVALID_EVIDENCE"
    assert terminal["fits"] == []
    assert terminal["bootstrap"] == []
    assert terminal["metrics"] is None
    assert terminal["gates"] is None

    counters = terminal["counters"]
    assert counters["permits_created"] == 1
    assert counters["permits_consumed"] == 1
    assert counters["real_fold_fit_calls"] == 0
    assert counters["duan_factors_computed"] == 0
    # Nothing downstream of the failed fit ran: no forecast, no QLIKE and no bootstrap.
    assert counters["real_forecasts_computed"] == 0
    assert counters["real_qlike_evaluations"] == 0
    assert counters["real_bootstrap_replicates"] == 0

    assert terminal["permits"]["consumed"] == 1
    assert terminal["permits"]["callback_starts"] == 1
    assert terminal["permits"]["validated_outputs"] == 0
    assert terminal["permits"]["poisoned"] is True
    assert terminal["permits"]["sealed"] is False

    # Exactly one terminal and exactly one permit exist beside the claim and the reservation.
    assert {entry.name for entry in _claim_directory(root, payload).iterdir()} == {
        str(evidence["reservation_name"]) + module._ACTIVATION_CLAIM_SUFFIX,
        str(evidence["reservation_name"]),
        str(evidence["permit_names"][0]),
        str(evidence["terminal_name"]),
    }
    assert module.execution_authority_report(authority)["disposition"] == "INVALID_EVIDENCE"
    with pytest.raises(module.Test3G3FOneShotError, match="attempted exactly once"):
        module.record_terminal_stop(
            authority,
            disposition="INVALID_EVIDENCE",
            reasons=("synthetic retry",),
            source_binding={"stage": "SYNTHETIC_RETRY"},
        )


def test_fold_and_pooled_metrics_are_row_weighted_with_unequal_fold_sizes(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())
    metrics = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))["metrics"]

    folds = {entry["fold_id"]: entry for entry in metrics["folds"]}
    assert list(folds) == list(FOLD_ORDER)
    first, second = (folds[fold_id] for fold_id in FOLD_ORDER)
    assert first["row_count"] != second["row_count"]  # the weighting has to matter
    assert first["session_count"] >= 20 and second["session_count"] >= 20

    pooled = metrics["pooled"]
    assert pooled["row_count"] == first["row_count"] + second["row_count"]
    weighted = (
        first["mean_improvement"] * first["row_count"]
        + second["mean_improvement"] * second["row_count"]
    ) / pooled["row_count"]
    assert pooled["mean_improvement"] == pytest.approx(weighted, rel=1e-12, abs=1e-15)
    assert pooled["mean_improvement"] == pytest.approx(
        pooled["mean_qlike_base"] - pooled["mean_qlike_har"], rel=1e-12, abs=1e-15
    )
    assert pooled["relative_qlike_reduction"] == pytest.approx(
        (pooled["mean_qlike_base"] - pooled["mean_qlike_har"]) / pooled["mean_qlike_base"],
        rel=1e-12,
    )

    sessions = metrics["sessions"]
    assert sum(entry["row_count"] for entry in sessions) == pooled["row_count"]
    assert [entry["fold_id"] for entry in sessions] == sorted(
        (entry["fold_id"] for entry in sessions),
        key=lambda fold_id: FOLD_ORDER.index(fold_id),
    )


def test_bootstrap_order_seeds_draws_and_sign_diagnostic_are_reproducible(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())
    terminal = _read_record(root, payload, str(_evidence(payload)["terminal_name"]))

    bootstrap = terminal["bootstrap"]
    assert [entry["block_length"] for entry in bootstrap] == [5, 1, 20]
    assert [entry["role"] for entry in bootstrap] == ["PRIMARY", "DIAGNOSTIC", "DIAGNOSTIC"]
    assert len({entry["draw_identity_sha256"] for entry in bootstrap}) == 3

    tables = {
        fold_id: tuple(
            SessionImprovementAggregate(
                fold_id=fold_id,
                session_id=entry["session_id"],
                session_date=date.fromisoformat(entry["session_date"]),
                row_count=entry["row_count"],
                improvement_sum=entry["improvement_sum"],
            )
            for entry in terminal["metrics"]["sessions"]
            if entry["fold_id"] == fold_id
        )
        for fold_id in FOLD_ORDER
    }
    for entry in bootstrap:
        assert entry["repetitions"] == BOOTSTRAP_REPETITIONS == 2_000
        assert entry["master_seed"] == MASTER_SEED
        assert entry["pooled_seed"] == MASTER_SEED + 90_000 + entry["block_length"]
        assert entry["fold_seeds"] == [
            [fold_id, entry["pooled_seed"] + 1_000 * (index + 1)]
            for index, fold_id in enumerate(FOLD_ORDER)
        ]
        assert entry["percentile"] == 0.05
        replay = paired_session_block_bootstrap(
            tables,
            block_length=entry["block_length"],
            repetitions=BOOTSTRAP_REPETITIONS,
            master_seed=MASTER_SEED,
        )
        assert replay.draw_identity_sha256 == entry["draw_identity_sha256"]
        assert replay.lower_bound == entry["lower_bound"]

    def sign(value: float) -> int:
        return 0 if value == 0.0 else (1 if value > 0.0 else -1)

    diagnostic = terminal["sign_diagnostic"]
    assert diagnostic["primary_block_length"] == 5
    assert diagnostic["primary_lower_bound_sign"] == sign(bootstrap[0]["lower_bound"])
    assert diagnostic["twenty_session_lower_bound_sign"] == sign(bootstrap[2]["lower_bound"])
    assert diagnostic["sign_changed"] == (
        diagnostic["twenty_session_lower_bound_sign"]
        != diagnostic["primary_lower_bound_sign"]
    )
    assert diagnostic["effect"] == "MANDATORY_DISCLOSURE_ONLY_NOT_A_GATE"
    # The disclosure never enters the gate block.
    assert "sign" not in json.dumps(terminal["gates"])


def test_continuation_gate_equalities_follow_the_frozen_protocol() -> None:
    def decide(**overrides: object):
        arguments: dict[str, object] = {
            "assertions_passed": True,
            "fold_mean_improvements": (("WF_2022", 0.5), ("WF_2023", 0.5)),
            # Binary-stable inputs: 10.0 and 9.0 are exact float64 values, their difference is
            # exactly 1.0, and 1.0 / 10.0 is exactly the frozen 0.10 threshold float. The
            # previous 1.0 / 0.9 pair computed a value just below the threshold, which tested the
            # subtraction rather than the boundary.
            "pooled_mean_qlike_base": 10.0,
            "pooled_mean_qlike_har": 9.0,
            "primary_lower_bound": 0.25,
            "real_fold_fit_calls": 4,
        }
        arguments.update(overrides)
        return decide_continuation(ContinuationInputs(**arguments))

    # Relative reduction of exactly 0.10 passes the materiality boundary. No epsilon, tolerance,
    # rounding, decimal type or changed gate policy is involved: the computed float is bit-for-bit
    # the frozen threshold, so this proves the inclusive equality of the frozen gate.
    passing = decide()
    assert passing.relative_qlike_reduction == RELATIVE_QLIKE_REDUCTION_FLOOR
    assert passing.relative_qlike_reduction == 0.10
    assert passing.disposition is TerminalDisposition.INTERESTING

    # Anything strictly below the same frozen threshold still fails; the gate is unchanged.
    below = decide(pooled_mean_qlike_har=9.000001)
    assert below.relative_qlike_reduction < RELATIVE_QLIKE_REDUCTION_FLOOR
    assert below.disposition is TerminalDisposition.NOT_INTERESTING
    assert "relative_qlike_reduction_below_0.10" in below.failures

    # A fold mean improvement of exactly zero fails.
    zero_fold = decide(fold_mean_improvements=(("WF_2022", 0.0), ("WF_2023", 0.5)))
    assert zero_fold.disposition is TerminalDisposition.NOT_INTERESTING
    assert "WF_2022_improvement_not_positive" in zero_fold.failures

    # A primary lower bound of exactly zero fails.
    zero_bound = decide(primary_lower_bound=0.0)
    assert zero_bound.disposition is TerminalDisposition.NOT_INTERESTING
    assert "primary_lower_bound_not_positive" in zero_bound.failures

    # Anything other than exactly four validated fits is invalid evidence, never a scientific
    # result, and an underpowered stop must carry zero fits.
    assert decide(real_fold_fit_calls=3).disposition is TerminalDisposition.INVALID
    assert decide(real_fold_fit_calls=5).disposition is TerminalDisposition.INVALID
    assert (
        decide_continuation(
            ContinuationInputs(
                assertions_passed=True,
                fold_mean_improvements=(("WF_2022", 0.5), ("WF_2023", 0.5)),
                pooled_mean_qlike_base=1.0,
                pooled_mean_qlike_har=0.9,
                primary_lower_bound=0.25,
                real_fold_fit_calls=0,
                underpowered=True,
            )
        ).disposition
        is TerminalDisposition.UNDERPOWERED
    )


def test_qlike_and_duan_helpers_match_the_frozen_definitions() -> None:
    actual = np.array([0.5, 1.25, 2.0], dtype=np.float64)
    forecast = np.array([0.4, 1.5, 2.0], dtype=np.float64)
    ratio = actual / forecast
    assert np.allclose(qlike(actual, forecast), ratio - np.log(ratio) - 1.0)
    residuals = np.array([-0.25, 0.0, 0.5], dtype=np.float64)
    assert duan_smearing_factor(residuals) == pytest.approx(float(np.mean(np.exp(residuals))))


@pytest.mark.parametrize(
    ("label", "options"),
    (
        ("nineteen_sessions", {"holdout_2022_sessions": 19}),
        ("undefined_acf_lags", {"rows_per_session": 2}),
        (
            "rows_not_greater_than_columns",
            {"train_sessions": 1, "train_rows_per_session": 5},
        ),
        ("wrong_holdout_year", {"wrong_holdout_year": True}),
        ("overlap_and_purge_failure", {"overlapping_train_session": True}),
    ),
)
def test_structural_prefit_failures_stop_before_any_permit_or_fit(
    tmp_path: Path,
    label: str,
    options: dict,
) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module, name=f"prefit-{label}")
    evidence = _evidence(payload)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})

    fields = _recovery_fields(**options)
    # The injected rows are always distinct rows, so the intended structural gate fires instead
    # of an identity or timestamp duplicate being rejected first.
    identities = [control.identity for control in fields["controls"]]
    times = [control.timestamp for control in fields["controls"]]
    assert len(set(identities)) == len(identities)
    assert len(set(times)) == len(times)

    with pytest.raises(module.Test3G3FUnderpoweredStop):
        _deliver(module, fields)

    # Not one permit was created, so not one least-squares call could have happened.
    for name in evidence["permit_names"]:
        assert not _record_path(root, payload, str(name)).exists()
    terminal = _read_record(root, payload, str(evidence["terminal_name"]))
    assert terminal["disposition"] == "UNDERPOWERED_STOP"
    assert terminal["fits"] == []
    assert terminal["bootstrap"] == []
    assert terminal["metrics"] is None
    assert terminal["gates"] is None
    assert terminal["counters"]["permits_created"] == 0
    assert terminal["counters"]["real_fold_fit_calls"] == 0
    assert terminal["counters"]["real_bootstrap_replicates"] == 0
    assert terminal["validation_status"] == "UNOPENED"
    assert terminal["final_test_status"] == "SEALED"
    assert module.execution_authority_report(authority)["disposition"] == "UNDERPOWERED_STOP"
    if label == "overlap_and_purge_failure":
        # A TRAIN label end that reaches into the holdout window is stopped by the purge gate.
        assert "purge failed before the first holdout decision time" in terminal["reasons"][0]


def test_real_mode_has_no_arbitrary_fit_callback(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, activation, _digests, _payload = _prepared_activation(tmp_path)
    capability = module.load_owner_activation_capability(activation, repository_root=str(root))
    callback = _InertFitCallback()

    with pytest.raises(
        module.Test3G3FPreActivationStop,
        match="no arbitrary fit callback",
    ):
        module.run_one_shot_fits(
            _synthetic_rows(module.RowOrigin.G3P_IN_PROCESS_HANDOFF, module=module),
            mode=module.ExecutionMode.OWNER_ACTIVATED_REAL,
            fit_callback=callback,
            activation=capability,
        )
    assert callback.calls == 0
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert source.count("np.linalg.lstsq(") == 1
    assert "rcond=None" in source


def test_the_terminal_is_attempted_once_and_never_retried(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    evidence = _evidence(payload)
    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())

    before = _record_path(root, payload, str(evidence["terminal_name"])).read_bytes()
    with pytest.raises(module.Test3G3FOneShotError, match="attempted exactly once"):
        module.record_terminal_stop(
            authority,
            disposition="INVALID_EVIDENCE",
            reasons=("synthetic retry",),
            source_binding={"stage": "SYNTHETIC_RETRY"},
        )
    assert _record_path(root, payload, str(evidence["terminal_name"])).read_bytes() == before

    # No temporary, partial or row-bearing artifact was ever created beside the closed records.
    expected = {
        str(evidence["reservation_name"]) + module._ACTIVATION_CLAIM_SUFFIX,
        str(evidence["reservation_name"]),
        str(evidence["terminal_name"]),
        *(str(name) for name in evidence["permit_names"]),
    }
    assert {entry.name for entry in _claim_directory(root, payload).iterdir()} == expected


def test_reservation_permits_and_terminal_are_create_once_and_reread_semantically(
    tmp_path: Path,
) -> None:
    module = _fresh_g3f_module()
    root, payload, authority = _prepared_execution(tmp_path, module)
    evidence = _evidence(payload)

    # A second execution authority is refused for this module instance.
    with pytest.raises(module.Test3G3FOneShotError, match="one-attempt"):
        module.open_execution_authority(object())

    # Replay survives the process: a second, wholly independent instance given the identical
    # activation bytes is refused by the persisted claim before it can reach a reservation, and
    # the already published reservation is never overwritten.
    published = _record_path(root, payload, str(evidence["reservation_name"])).read_bytes()
    second = _fresh_g3f_module()
    with pytest.raises(second.Test3G3FOneShotError, match="already exists"):
        second.load_owner_activation_capability(
            str(tmp_path / "recovery-repository-activation-file"),
            repository_root=str(root),
        )
    assert _record_path(root, payload, str(evidence["reservation_name"])).read_bytes() == published

    module.bind_source_evidence(authority, {"stage": "SYNTHETIC_G3P_STAND_IN"})
    _deliver(module, _recovery_fields())

    # Every published record is exactly its own canonical serialization, so a forged, reordered,
    # duplicated or padded byte would not survive the reread the writer already performed.
    for name in (
        str(evidence["reservation_name"]),
        *(str(item) for item in evidence["permit_names"]),
        str(evidence["terminal_name"]),
    ):
        raw = _record_path(root, payload, name).read_bytes()
        assert raw == _canonical(json.loads(raw.decode("utf-8")))


def test_a_stop_terminal_refuses_any_scientific_disposition(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    _root, _payload, authority = _prepared_execution(tmp_path, module)
    for disposition in (
        "INTERESTING_ENOUGH_FOR_CONFIRMATORY_PROTOCOL",
        "NOT_INTERESTING_ENOUGH",
        "SOMETHING_ELSE",
    ):
        with pytest.raises(module.Test3G3FOneShotError, match="stop terminal"):
            module.record_terminal_stop(
                authority,
                disposition=disposition,
                reasons=("synthetic",),
                source_binding={"stage": "SYNTHETIC"},
            )


def test_no_authority_exists_before_a_verified_activation(tmp_path: Path) -> None:
    module = _fresh_g3f_module()
    for hostile in (None, object(), "authority", {"serial": 1}):
        with pytest.raises(module.Test3G3FPreActivationStop):
            module.assert_execution_authority_reserved(hostile)
        with pytest.raises(module.Test3G3FPreActivationStop):
            module.execution_authority_report(hostile)
    assert list(tmp_path.rglob("*")) == []

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
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    FOLD_ORDER,
    MODEL_COLUMNS,
    MODEL_ORDER,
    RowStatus,
)
from mes_quant.exploration.test3_design import Harmonic, PredictorStatusRow
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


def _activation_document(digests: tuple[str, ...], **overrides: object) -> dict[str, object]:
    """Build a synthetic activation document; every value here is a test placeholder."""

    document: dict[str, object] = {
        "owner_activation_id": "SYNTHETIC_PLACEHOLDER_NOT_OWNER_EVIDENCE",
        "activation_document_sha256": "0" * 64,
        "fit_permit_budget": 4,
        "implementation_paths": list(g3f.REVIEWED_IMPLEMENTATION_PATHS),
        "reviewed_path_sha256": list(digests),
        "runtime_evidence": {
            "root": "synthetic-placeholder-root",
            "namespace": "synthetic-placeholder-namespace",
            "reservation_name": "synthetic-placeholder-reservation",
            "permit_names": [f"synthetic-placeholder-permit-{index}" for index in (1, 2, 3, 4)],
            "terminal_name": "synthetic-placeholder-terminal",
        },
    }
    document.update(overrides)
    return document


def _write_activation(path: Path, document: object) -> str:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _claim_directory(root: Path, document: Mapping[str, object]) -> Path:
    """Locate the synthetic activation-claim directory; it never leaves ``tmp_path``."""

    evidence = document["runtime_evidence"]
    assert isinstance(evidence, Mapping)
    return root.joinpath(*str(evidence["root"]).split("/"), str(evidence["namespace"]))


def _claim_path(root: Path, document: Mapping[str, object]) -> Path:
    evidence = document["runtime_evidence"]
    assert isinstance(evidence, Mapping)
    return _claim_directory(root, document) / (
        str(evidence["reservation_name"]) + g3f._ACTIVATION_CLAIM_SUFFIX
    )


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
    document = _activation_document(digests, **overrides)
    if create_claim_directory:
        _claim_directory(root, document).mkdir(parents=True, exist_ok=True)
    activation = _write_activation(tmp_path / f"{name}-activation-file", document)
    return root, activation, digests, document


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
    assert mutable == {"FOLD_ROLE_ATTRIBUTES"}

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
        owner_activation_id: str = "SYNTHETIC_PLACEHOLDER_NOT_OWNER_EVIDENCE"
        activation_document_sha256: str = "0" * 64
        activation_file_sha256: str = "1" * 64
        runtime_evidence: tuple[object, ...] = ()

    class _DuckActivation:
        """A duck type that copies the real serial and the real verified fields."""

        def __init__(self) -> None:
            self.serial = serial
            self.repository_root = str(root)
            self.reviewed_digests = digests
            self.fit_permit_budget = 4
            self.owner_activation_id = "SYNTHETIC_PLACEHOLDER_NOT_OWNER_EVIDENCE"
            self.activation_document_sha256 = "0" * 64
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
            activation_document_sha256="0" * 64,
            activation_file_sha256="1" * 64,
            fit_permit_budget=4,
            owner_activation_id="A",
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
    root, _activation, digests, _document = _prepared_activation(tmp_path)
    forged = _write_activation(
        tmp_path / "forged-bytes",
        _activation_document(digests, reviewed_path_sha256=["a" * 64] * 6),
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
        _activation_document(digests, fit_permit_budget=5),
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

    with pytest.raises(module.Test3G3FOneShotError, match="already claimed"):
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
    with pytest.raises(second.Test3G3FOneShotError, match="already claimed"):
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
    with pytest.raises(collision.Test3G3FOneShotError, match="already claimed"):
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
    with pytest.raises(symlinked.Test3G3FOneShotError, match="already claimed"):
        symlinked.load_owner_activation_capability(activation4, repository_root=str(root4))
    assert not never.exists()

    for module in (absent, linked, collision, symlinked):
        assert module._local_state_report()["activation_capability_issued"] is False
        _real_mode_stop(None, module=module)


def test_activation_loader_refuses_every_hostile_document(tmp_path: Path) -> None:
    root, _activation, digests, document = _prepared_activation(tmp_path)
    paths = list(g3f.REVIEWED_IMPLEMENTATION_PATHS)

    hostile_documents = (
        _activation_document(digests, fit_permit_budget=5),
        _activation_document(digests, fit_permit_budget=True),
        _activation_document(digests, activation_document_sha256="not-a-digest"),
        _activation_document(digests, owner_activation_id=""),
        _activation_document(digests, implementation_paths=paths[:5]),
        _activation_document(digests, implementation_paths=[*paths, "tools/extra.py"]),
        _activation_document(digests, implementation_paths=[paths[1], paths[0], *paths[2:]]),
        _activation_document(digests, implementation_paths=[*paths[:5], "tools/other.py"]),
        _activation_document(digests, reviewed_path_sha256=list(digests[:5])),
        _activation_document(digests, reviewed_path_sha256=["4" * 64] * 6),
        _activation_document(digests, runtime_evidence={"root": "only"}),
        _activation_document(
            digests,
            runtime_evidence={
                "root": "synthetic-placeholder-root",
                "namespace": "synthetic-placeholder-namespace",
                "reservation_name": "synthetic-placeholder-namespace",
                "permit_names": [f"synthetic-placeholder-permit-{i}" for i in (1, 2, 3, 4)],
                "terminal_name": "synthetic-placeholder-terminal",
            },
        ),
        _activation_document(
            digests,
            runtime_evidence={
                "root": "synthetic-placeholder-root",
                "namespace": "synthetic-placeholder-namespace",
                "reservation_name": "synthetic-placeholder-reservation",
                "permit_names": ["synthetic-placeholder-permit-1"] * 4,
                "terminal_name": "synthetic-placeholder-terminal",
            },
        ),
        _activation_document(
            digests,
            runtime_evidence={
                "root": "../escape",
                "namespace": "synthetic-placeholder-namespace",
                "reservation_name": "synthetic-placeholder-reservation",
                "permit_names": [f"synthetic-placeholder-permit-{i}" for i in (1, 2, 3, 4)],
                "terminal_name": "synthetic-placeholder-terminal",
            },
        ),
        _activation_document(
            digests,
            runtime_evidence={
                "root": "synthetic-placeholder-root",
                "namespace": "",
                "reservation_name": "synthetic-placeholder-reservation",
                "permit_names": [f"synthetic-placeholder-permit-{i}" for i in (1, 2, 3, 4)],
                "terminal_name": "synthetic-placeholder-terminal",
            },
        ),
        _activation_document(
            digests,
            runtime_evidence={
                "root": "synthetic-placeholder-root",
                "namespace": "synthetic-placeholder-namespace",
                "reservation_name": "synthetic-placeholder-reservation",
                "permit_names": [f"synthetic-placeholder-permit-{i}" for i in (1, 2, 3)],
                "terminal_name": "synthetic-placeholder-terminal",
            },
        ),
    )
    for index, hostile in enumerate(hostile_documents):
        module = _fresh_g3f_module()
        path = _write_activation(tmp_path / f"hostile-{index}", hostile)
        with pytest.raises(module.Test3G3FOneShotError):
            module.load_owner_activation_capability(path, repository_root=str(root))
        assert module._local_state_report()["activation_capability_issued"] is False

    missing = _fresh_g3f_module()
    accepted = _activation_document(digests)
    accepted.pop("runtime_evidence")
    path = _write_activation(tmp_path / "hostile-missing-key", accepted)
    with pytest.raises(missing.Test3G3FOneShotError, match="closed top-level key set"):
        missing.load_owner_activation_capability(path, repository_root=str(root))

    additional = _fresh_g3f_module()
    extra = _activation_document(digests)
    extra["unexpected"] = "value"
    path = _write_activation(tmp_path / "hostile-extra-key", extra)
    with pytest.raises(additional.Test3G3FOneShotError, match="closed top-level key set"):
        additional.load_owner_activation_capability(path, repository_root=str(root))

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
    body = json.dumps(_activation_document(digests), indent=2, sort_keys=True)

    duplicate = "{\n" + '  "fit_permit_budget": 4,\n' + body[1:].lstrip()
    duplicate_path = tmp_path / "duplicate-keys"
    duplicate_path.write_text(duplicate, encoding="utf-8")

    nonfinite_path = tmp_path / "nonfinite"
    nonfinite_path.write_text(
        body.replace('"fit_permit_budget": 4', '"fit_permit_budget": NaN'),
        encoding="utf-8",
    )

    overflow_path = tmp_path / "overflow"
    overflow_path.write_text(
        body.replace('"fit_permit_budget": 4', '"fit_permit_budget": 1e999'),
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

    # The single write surface is the exclusive, non-overwriting activation replay claim: one
    # create, one write loop, and exactly two fsyncs for the file and its directory.
    assert source.count("os.O_CREAT") == 1
    assert source.count("os.O_EXCL") == 1
    assert source.count("os.write(") == 1
    assert source.count("os.fsync(") == 2

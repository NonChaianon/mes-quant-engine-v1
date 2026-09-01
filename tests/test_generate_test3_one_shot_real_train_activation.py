"""Synthetic-only tests for the Test 3 activation preparation generator."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPOSITORY_ROOT / "tools/generate_test3_one_shot_real_train_activation.py"
G3F_SOURCE_PATH = REPOSITORY_ROOT / "src/mes_quant/exploration/test3_g3f_one_shot.py"


def _load_generator() -> ModuleType:
    name = f"test3_activation_generator_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_generator()


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _plan() -> dict[str, object]:
    return {
        "activation_names": {
            "activation_output_path": GENERATOR.ACTIVATION_OUTPUT_PATH,
            "evidence_namespace": GENERATOR.EVIDENCE_NAMESPACE,
            "evidence_root": GENERATOR.EVIDENCE_ROOT,
            "override_id": GENERATOR.OVERRIDE_ID,
            "permit_names": list(GENERATOR.PERMIT_NAMES),
            "recovery_lineage_id": GENERATOR.RECOVERY_LINEAGE_ID,
            "reservation_name": GENERATOR.RESERVATION_NAME,
            "terminal_name": GENERATOR.TERMINAL_NAME,
        },
        "classification": GENERATOR.PLAN_CLASSIFICATION,
        "g3p_witness_paths": {
            "request_witness": (
                "artifacts/exploration/test3/g3p-recovery/"
                f"{GENERATOR.RECOVERY_LINEAGE_ID}/request_set.sealed.json"
            ),
            "target_witness": (
                "artifacts/exploration/test3/g3p-recovery/"
                f"{GENERATOR.RECOVERY_LINEAGE_ID}/target_space.consumed.json"
            ),
        },
        "implementation_paths": [
            "src/mes_quant/exploration/test3_g3p_pre_fit.py",
            "tests/test_test3_g3p_pre_fit.py",
            "src/mes_quant/exploration/test3_g3f_one_shot.py",
            "tests/test_test3_g3f_one_shot.py",
            "tools/run_test3_one_shot_scientific_recovery.py",
            "tests/test_run_test3_one_shot_scientific_recovery.py",
        ],
        "omitted_bindings": {
            "activation_payload_digest_omitted": True,
            "implementation_digests_omitted": True,
        },
        "prohibitions": {
            "activation": True,
            "protected_access": True,
            "reservation": True,
            "scientific_execution": True,
        },
        "schema_version": GENERATOR.PLAN_SCHEMA_VERSION,
    }


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _synthetic_repository(root: Path) -> dict[str, object]:
    protocol = b"synthetic ratified protocol fixture\n"
    protocol_digest = hashlib.sha256(protocol).hexdigest()
    plan = _plan()

    contract = (
        "PROTOCOL_ID = 'MES_SYNTHETIC_TEST3_PROTOCOL_V1'\n"
        f"PROTOCOL_SHA256 = {protocol_digest!r}\n"
        "TARGET_SPACE_ID = 'TARGET_SPACE_SYNTHETIC'\n"
        "REAL_FOLD_FIT_BUDGET = 4\n"
    ).encode()
    g3p = (
        b"G3P_RECOVERY_OUTPUT_SUBPATH = 'artifacts/exploration/test3/g3p-recovery'\n"
        b"G3P_RECOVERY_REQUEST_WITNESS = 'request_set.sealed.json'\n"
        b"G3P_RECOVERY_TARGET_WITNESS = 'target_space.consumed.json'\n"
    )
    g3f = (
        "from typing import Final\n"
        "REVIEWED_IMPLEMENTATION_PATHS: Final[tuple[str, ...]] = "
        f"{tuple(plan['implementation_paths'])!r}\n"
        "ACTIVATION_ENVELOPE_KEYS: Final[frozenset[str]] = "
        "frozenset({'activation_payload', 'activation_payload_sha256'})\n"
        "ACTIVATION_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset({"
        "'fit_permit_budget', 'implementation_path_sha256', 'implementation_paths', "
        "'override_id', 'protocol_id', 'protocol_sha256', 'recovery_lineage_id', "
        "'runtime_evidence', 'target_space_id'})\n"
        "RUNTIME_EVIDENCE_KEYS: Final[frozenset[str]] = frozenset({"
        "'namespace', 'permit_names', 'reservation_name', 'root', 'terminal_name'})\n"
        "_ACTIVATION_CLAIM_SUFFIX: Final[str] = '.activation-replay-claim'\n"
    ).encode()

    files: dict[str, bytes] = {
        GENERATOR.PLAN_PATH: _canonical(plan),
        GENERATOR.PROTOCOL_PATH: protocol,
        GENERATOR.CONTRACT_PATH: contract,
        GENERATOR.G3P_PATH: g3p,
        GENERATOR.G3F_PATH: g3f,
        "tests/test_test3_g3p_pre_fit.py": b"# synthetic G3-P test fixture\n",
        "tests/test_test3_g3f_one_shot.py": b"# synthetic G3-F test fixture\n",
        "tools/run_test3_one_shot_scientific_recovery.py": b"# synthetic runner fixture\n",
        "tests/test_run_test3_one_shot_scientific_recovery.py": (
            b"# synthetic runner test fixture\n"
        ),
    }
    for relative, payload in files.items():
        _write(root / relative, payload)
    return {
        "plan": plan,
        "protocol_digest": protocol_digest,
        "protocol_id": "MES_SYNTHETIC_TEST3_PROTOCOL_V1",
        "target_space_id": "TARGET_SPACE_SYNTHETIC",
    }


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


@contextmanager
def _fresh_g3f() -> Iterator[ModuleType]:
    name = f"synthetic_g3f_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, G3F_SOURCE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(name, None)


def test_check_is_static_deterministic_and_creates_nothing(tmp_path: Path) -> None:
    _synthetic_repository(tmp_path)
    before = _tree_bytes(tmp_path)

    GENERATOR.run_mode("check", repository_root=tmp_path)
    first = _tree_bytes(tmp_path)
    GENERATOR.run_mode("check", repository_root=tmp_path)

    assert first == before
    assert _tree_bytes(tmp_path) == before
    assert not (tmp_path / GENERATOR.ACTIVATION_OUTPUT_PATH).exists()


def test_create_is_deterministic_exclusive_and_does_not_create_evidence(
    tmp_path: Path,
) -> None:
    fixture = _synthetic_repository(tmp_path)
    GENERATOR.run_mode("create", repository_root=tmp_path)
    output = tmp_path / GENERATOR.ACTIVATION_OUTPUT_PATH
    raw = output.read_bytes()
    document = json.loads(raw)
    payload = document["activation_payload"]

    assert raw == _canonical(document)
    assert set(document) == set(GENERATOR.EXPECTED_ENVELOPE_KEYS)
    assert set(payload) == set(GENERATOR.EXPECTED_PAYLOAD_KEYS)
    assert set(payload["runtime_evidence"]) == set(GENERATOR.EXPECTED_RUNTIME_EVIDENCE_KEYS)
    assert payload["protocol_id"] == fixture["protocol_id"]
    assert payload["protocol_sha256"] == fixture["protocol_digest"]
    assert payload["target_space_id"] == fixture["target_space_id"]
    assert payload["fit_permit_budget"] == 4
    assert document["activation_payload_sha256"] == hashlib.sha256(
        _canonical(payload)
    ).hexdigest()
    assert not (tmp_path / GENERATOR.EVIDENCE_ROOT).exists()
    assert not (
        tmp_path
        / "artifacts/exploration/test3/g3p-recovery"
        / GENERATOR.RECOVERY_LINEAGE_ID
    ).exists()
    with pytest.raises(GENERATOR.ActivationPreparationError, match="already exists"):
        GENERATOR.run_mode("create", repository_root=tmp_path)


def test_equivalent_synthetic_repositories_produce_identical_envelopes(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _synthetic_repository(first)
    _synthetic_repository(second)

    GENERATOR.run_mode("create", repository_root=first)
    GENERATOR.run_mode("create", repository_root=second)

    assert (first / GENERATOR.ACTIVATION_OUTPUT_PATH).read_bytes() == (
        second / GENERATOR.ACTIVATION_OUTPUT_PATH
    ).read_bytes()


def test_verify_existing_is_read_only_and_rejects_byte_drift(tmp_path: Path) -> None:
    _synthetic_repository(tmp_path)
    GENERATOR.run_mode("create", repository_root=tmp_path)
    before = _tree_bytes(tmp_path)

    GENERATOR.run_mode("verify-existing", repository_root=tmp_path)
    assert _tree_bytes(tmp_path) == before

    implementation = tmp_path / _plan()["implementation_paths"][-1]
    implementation.write_bytes(implementation.read_bytes() + b"# drift\n")
    with pytest.raises(GENERATOR.ActivationPreparationError, match="current exact bindings"):
        GENERATOR.run_mode("verify-existing", repository_root=tmp_path)


def test_verify_existing_rejects_absence_and_noncanonical_or_forged_output(
    tmp_path: Path,
) -> None:
    _synthetic_repository(tmp_path)
    with pytest.raises(GENERATOR.ActivationPreparationError, match="missing"):
        GENERATOR.run_mode("verify-existing", repository_root=tmp_path)

    GENERATOR.run_mode("create", repository_root=tmp_path)
    output = tmp_path / GENERATOR.ACTIVATION_OUTPUT_PATH
    document = json.loads(output.read_bytes())
    output.chmod(0o600)
    output.write_text(json.dumps(document, indent=2), encoding="utf-8")
    with pytest.raises(GENERATOR.ActivationPreparationError, match="does not match"):
        GENERATOR.run_mode("verify-existing", repository_root=tmp_path)


@pytest.mark.parametrize(
    "mutation",
    (
        "unknown-key",
        "missing-key",
        "reordered-paths",
        "manual-binding",
        "path-escape",
    ),
)
def test_plan_schema_and_binding_material_are_closed(tmp_path: Path, mutation: str) -> None:
    _synthetic_repository(tmp_path)
    plan_path = tmp_path / GENERATOR.PLAN_PATH
    plan = json.loads(plan_path.read_bytes())
    if mutation == "unknown-key":
        plan["unknown"] = True
    elif mutation == "missing-key":
        del plan["prohibitions"]
    elif mutation == "reordered-paths":
        plan["implementation_paths"] = list(reversed(plan["implementation_paths"]))
    elif mutation == "manual-binding":
        plan["omitted_bindings"]["implementation_digests_omitted"] = False
    else:
        plan["activation_names"]["activation_output_path"] = "../escape.json"
    plan_path.write_bytes(_canonical(plan))

    with pytest.raises(GENERATOR.ActivationPreparationError):
        GENERATOR.run_mode("check", repository_root=tmp_path)


def test_duplicate_and_noncanonical_plan_json_are_refused(tmp_path: Path) -> None:
    _synthetic_repository(tmp_path)
    plan_path = tmp_path / GENERATOR.PLAN_PATH
    original = plan_path.read_text(encoding="utf-8")
    duplicate = original.replace(
        '{"activation_names":',
        '{"schema_version":"duplicate","activation_names":',
        1,
    )
    plan_path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(GENERATOR.ActivationPreparationError, match="duplicate"):
        GENERATOR.run_mode("check", repository_root=tmp_path)

    plan_path.write_text(json.dumps(_plan(), indent=2), encoding="utf-8")
    with pytest.raises(GENERATOR.ActivationPreparationError, match="canonical"):
        GENERATOR.run_mode("check", repository_root=tmp_path)


def test_missing_symlinked_and_colliding_inputs_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    missing.mkdir()
    _synthetic_repository(missing)
    (missing / GENERATOR.G3P_PATH).unlink()
    with pytest.raises(GENERATOR.ActivationPreparationError, match="missing"):
        GENERATOR.run_mode("check", repository_root=missing)

    linked = tmp_path / "linked"
    linked.mkdir()
    _synthetic_repository(linked)
    source = linked / GENERATOR.G3P_PATH
    target = linked / "synthetic-target.py"
    target.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(target)
    with pytest.raises(GENERATOR.ActivationPreparationError, match="symlinked"):
        GENERATOR.run_mode("check", repository_root=linked)

    collision = tmp_path / "collision"
    collision.mkdir()
    _synthetic_repository(collision)
    _write(collision / GENERATOR.ACTIVATION_OUTPUT_PATH, b"collision")
    with pytest.raises(GENERATOR.ActivationPreparationError, match="already exists"):
        GENERATOR.run_mode("check", repository_root=collision)

    additional = tmp_path / "additional"
    additional.mkdir()
    _synthetic_repository(additional)
    _write(
        additional
        / "docs/research/TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V1.copy.json",
        b"not an activation",
    )
    with pytest.raises(GENERATOR.ActivationPreparationError, match="additional activation"):
        GENERATOR.run_mode("check", repository_root=additional)


def test_check_and_verify_never_call_loader_or_runner(tmp_path: Path) -> None:
    _synthetic_repository(tmp_path)
    source = GENERATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert not imported_roots.intersection({"mes_quant", "subprocess", "socket", "urllib"})
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "load_owner_activation_capability" not in calls
    assert "run_g3p_recovery" not in calls

    GENERATOR.run_mode("check", repository_root=tmp_path)
    GENERATOR.run_mode("create", repository_root=tmp_path)
    before = _tree_bytes(tmp_path)
    GENERATOR.run_mode("verify-existing", repository_root=tmp_path)
    assert _tree_bytes(tmp_path) == before


def test_synthetic_envelope_is_compatible_with_one_fresh_loader_instance(
    tmp_path: Path,
) -> None:
    fixture = _synthetic_repository(tmp_path)
    GENERATOR.run_mode("create", repository_root=tmp_path)
    claim_directory = tmp_path / GENERATOR.EVIDENCE_ROOT / GENERATOR.EVIDENCE_NAMESPACE
    claim_directory.mkdir(parents=True)

    with _fresh_g3f() as module:
        module.PROTOCOL_ID = fixture["protocol_id"]
        module.PROTOCOL_SHA256 = fixture["protocol_digest"]
        module.TARGET_SPACE_ID = fixture["target_space_id"]
        module.FIT_PERMIT_BUDGET = 4
        module.REVIEWED_IMPLEMENTATION_PATHS = tuple(_plan()["implementation_paths"])
        capability = module.load_owner_activation_capability(
            str(tmp_path / GENERATOR.ACTIVATION_OUTPUT_PATH),
            repository_root=str(tmp_path),
        )
        assert capability is not None

    claim = claim_directory / (
        GENERATOR.RESERVATION_NAME + ".activation-replay-claim"
    )
    assert claim.is_file()
    assert claim.resolve().is_relative_to(tmp_path.resolve())


def test_cli_rejects_unknown_mode_without_writing(tmp_path: Path) -> None:
    _synthetic_repository(tmp_path)
    before = _tree_bytes(tmp_path)
    with pytest.raises(GENERATOR.ActivationPreparationError, match="mode must be exactly"):
        GENERATOR.run_mode("run", repository_root=tmp_path)
    assert _tree_bytes(tmp_path) == before

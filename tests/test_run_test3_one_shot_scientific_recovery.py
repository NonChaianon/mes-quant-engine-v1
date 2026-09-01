"""Data-free tests for the Test 3 one-shot pre-activation status runner.

The runner must be import-safe, must stop before every data, provider, target, reservation and
fit surface, must name no runtime evidence root, namespace or filename, and must create no file.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

_RUNNER_NAME = "run_test3_one_shot_scientific_recovery"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_RUNNER_PATH = _REPOSITORY_ROOT / "tools" / f"{_RUNNER_NAME}.py"
_PACKAGE_PARTS = ("mes_quant", "exploration")


def _prepend_worktree_source_path() -> None:
    """Select this worktree's ``src`` tree before the runner imports ``mes_quant``."""

    candidate = _REPOSITORY_ROOT / "src"
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


def _load_runner() -> object:
    """Import the runner from its file without leaving bytecode or other residue."""

    _prepend_worktree_source_path()
    specification = importlib.util.spec_from_file_location(_RUNNER_NAME, _RUNNER_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        specification.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def test_importing_the_runner_has_no_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    module = _load_runner()

    assert callable(module.main)
    assert module.GATE_LITERAL == "TEST3_ONE_SHOT_PRE_ACTIVATION_STATUS"
    assert list(tmp_path.rglob("*")) == []


def test_runner_reports_the_pre_activation_stop_and_creates_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _load_runner()

    assert module.main(["--gate", module.GATE_LITERAL]) == 0

    printed = capsys.readouterr().out
    lines = dict(
        line.split("=", 1) for line in printed.splitlines() if "=" in line
    )
    assert lines["TEST3_ONE_SHOT_STATE"] == (
        "PRE_ACTIVATION_STOP_NO_DATA_NO_PROVIDER_NO_TARGET_NO_RESERVATION_NO_FIT"
    )
    assert lines["OWNER_ACTIVATION"] == "ABSENT_NOT_AUTHORIZED"
    assert lines["ORDERED_MODEL_FOLD_PAIRS"] == (
        "RVBASE001/WF_2022,RVHAR001/WF_2022,RVBASE001/WF_2023,RVHAR001/WF_2023"
    )
    assert lines["FIT_PERMIT_BUDGET"] == "4"
    assert lines["PERMITS_UNREPLENISHED"] == "True"
    assert lines["EVIDENCE_NAMING"] == "DEFERRED_TO_SEPARATE_OWNER_ACTIVATION"
    assert lines["REAL_FOLD_FIT_CALLS"] == "0"
    assert lines["EVIDENCE_FILES_WRITTEN"] == "0"
    assert lines["VALIDATION_STATUS"] == "UNOPENED"
    assert lines["FINAL_TEST_STATUS"] == "SEALED"
    for key in (
        "DATA_ACCESS",
        "PROVIDER_ACCESS",
        "TARGET_ACCESS",
        "TARGET_SPACE_RESERVATION",
        "REAL_FITS",
    ):
        assert lines[key] == "NOT_AUTHORIZED_BEFORE_SEPARATE_OWNER_ACTIVATION"
    assert list(tmp_path.rglob("*")) == []


def test_runner_has_no_unknown_gate_or_hidden_execution_switch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _load_runner()

    for argv in (
        [],
        ["--gate", "SOMETHING_ELSE"],
        ["--gate", module.GATE_LITERAL, "--execute"],
        ["--gate", module.GATE_LITERAL, "--activate"],
        ["--gate", module.GATE_LITERAL, "--fit"],
        ["--gate", module.EXECUTION_GATE_LITERAL, "--force"],
    ):
        with pytest.raises(SystemExit) as exit_state:
            module.main(argv)
        assert exit_state.value.code == 2
    assert list(tmp_path.rglob("*")) == []


def test_execution_gate_requires_every_bound_input_and_creates_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The execution gate is unusable today: no activation file exists and none may be made."""

    monkeypatch.chdir(tmp_path)
    module = _load_runner()

    with pytest.raises(SystemExit) as exit_state:
        module.main(["--gate", module.EXECUTION_GATE_LITERAL])
    assert "repository-root" in str(exit_state.value)
    assert list(tmp_path.rglob("*")) == []

    # A complete argument set still cannot execute, because the activation file is absent and
    # this runner may never create one.
    absent = tmp_path / "no-such-activation-file"
    arguments = [
        "--gate",
        module.EXECUTION_GATE_LITERAL,
        "--activation-file",
        str(absent),
        "--repository-root",
        str(tmp_path),
    ]
    for name in module.ARTIFACT_ARGUMENTS:
        arguments.extend((f"--{name.replace('_', '-')}", str(tmp_path / name)))

    from mes_quant.exploration.test3_g3f_one_shot import Test3G3FOneShotError

    with pytest.raises(Test3G3FOneShotError, match="activation file"):
        module.main(arguments)
    assert not absent.exists()
    assert list(tmp_path.rglob("*")) == []


def test_execution_gate_refuses_relative_paths_before_any_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    module = _load_runner()

    arguments = [
        "--gate",
        module.EXECUTION_GATE_LITERAL,
        "--activation-file",
        "relative-activation",
        "--repository-root",
        str(tmp_path),
    ]
    for name in module.ARTIFACT_ARGUMENTS:
        arguments.extend((f"--{name.replace('_', '-')}", str(tmp_path / name)))

    with pytest.raises(SystemExit) as exit_state:
        module.main(arguments)
    assert "absolute" in str(exit_state.value)
    assert list(tmp_path.rglob("*")) == []


def test_runner_source_names_no_evidence_path_and_imports_no_data_surface() -> None:
    source = _RUNNER_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "artifacts/",
        ".json",
        ".parquet",
        ".dbn",
        "open(",
        ".write(",
        "mkdir",
        "TARGET_SPACE_003",
        "databento",
        "pandas",
        "pyarrow",
        "requests",
        "socket",
        "lstsq",
        "rcond",
        "bootstrap(",
    ):
        assert forbidden not in source

    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)

    assert imported == {
        "__future__",
        "argparse",
        "pathlib",
        "sys",
        "mes_quant.exploration.test3_g3f_one_shot",
        "mes_quant.exploration.test3_g3p_pre_fit",
    }


def test_runner_never_names_evidence_and_never_chooses_the_estimator() -> None:
    """Evidence naming and the estimator both belong to the activation and to G3-F."""

    source = _RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    # The runner only sequences the reviewed stages; it performs no scientific work itself.
    assert {
        "load_owner_activation_capability",
        "open_execution_authority",
        "run_g3p_recovery",
        "record_terminal_stop",
        "execution_authority_report",
        "close_execution_authority",
    } <= calls
    for forbidden in ("consume", "seal", "fit", "lstsq", "reserve", "deliver"):
        assert forbidden not in {call.lower() for call in calls}

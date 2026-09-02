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


def _synthetic_execution_fixture(tmp_path: Path, module: object) -> tuple[Path, Path]:
    """Create only inert runtime-origin and malformed-activation files under ``tmp_path``."""

    root = tmp_path / "synthetic-execution-repository"
    for relative in (
        "tools/run_test3_one_shot_scientific_recovery.py",
        "src/mes_quant/exploration/test3_g3p_pre_fit.py",
        "src/mes_quant/exploration/test3_g3f_one_shot.py",
    ):
        path = root.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# inert synthetic runtime-origin fixture\n", encoding="utf-8")
    activation = root / "docs/research/TEST3_ONE_SHOT_REAL_TRAIN_ACTIVATION_V2.json"
    activation.parent.mkdir(parents=True, exist_ok=True)
    activation.write_text("{}\n", encoding="utf-8")
    module.__file__ = str(root / "tools/run_test3_one_shot_scientific_recovery.py")
    return root, activation


def _execution_arguments(module: object, root: Path, activation: Path) -> list[str]:
    arguments = [
        "--gate",
        module.EXECUTION_GATE_LITERAL,
        "--activation-file",
        str(activation),
        "--repository-root",
        str(root),
    ]
    for name in module.ARTIFACT_ARGUMENTS:
        arguments.extend((f"--{name.replace('_', '-')}", str(root / f"synthetic-{name}")))
    return arguments


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
    """A fully synthetic malformed activation fails without touching live V2 surfaces."""

    monkeypatch.chdir(tmp_path)
    module = _load_runner()

    with pytest.raises(SystemExit) as exit_state:
        module.main(["--gate", module.EXECUTION_GATE_LITERAL])
    assert "repository-root" in str(exit_state.value)
    assert list(tmp_path.rglob("*")) == []

    root, activation = _synthetic_execution_fixture(tmp_path, module)
    from mes_quant.exploration import test3_g3f_one_shot as runtime_g3f
    from mes_quant.exploration import test3_g3p_pre_fit as runtime_g3p
    from mes_quant.exploration.test3_g3f_one_shot import Test3G3FOneShotError

    monkeypatch.setattr(
        runtime_g3p,
        "__file__",
        str(root / "src/mes_quant/exploration/test3_g3p_pre_fit.py"),
    )
    monkeypatch.setattr(
        runtime_g3f,
        "__file__",
        str(root / "src/mes_quant/exploration/test3_g3f_one_shot.py"),
    )
    with pytest.raises(Test3G3FOneShotError, match="closed envelope"):
        module.main(_execution_arguments(module, root, activation))
    assert not (root / "artifacts/test3_one_shot_real_train_v2").exists()


@pytest.mark.parametrize("origin_failure", ("wrong", "symlink"))
def test_runtime_origin_failure_precedes_v2_loader_and_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    origin_failure: str,
) -> None:
    module = _load_runner()
    root, activation = _synthetic_execution_fixture(tmp_path, module)
    from mes_quant.exploration import test3_g3f_one_shot as runtime_g3f
    from mes_quant.exploration import test3_g3p_pre_fit as runtime_g3p

    g3p_path = root / "src/mes_quant/exploration/test3_g3p_pre_fit.py"
    g3f_path = root / "src/mes_quant/exploration/test3_g3f_one_shot.py"
    monkeypatch.setattr(runtime_g3p, "__file__", str(g3p_path))
    monkeypatch.setattr(runtime_g3f, "__file__", str(g3f_path))
    if origin_failure == "wrong":
        wrong = tmp_path / "wrong-g3p-origin.py"
        wrong.write_text("# wrong synthetic origin\n", encoding="utf-8")
        monkeypatch.setattr(runtime_g3p, "__file__", str(wrong))
    else:
        outside = tmp_path / "outside-g3f-origin.py"
        outside.write_text("# outside synthetic origin\n", encoding="utf-8")
        g3f_path.unlink()
        g3f_path.symlink_to(outside)

    loader_calls = 0

    def loader_tripwire(*_args: object, **_kwargs: object) -> object:
        nonlocal loader_calls
        loader_calls += 1
        raise AssertionError("V2 loader reached after a runtime-origin failure")

    monkeypatch.setattr(runtime_g3f, "load_owner_activation_capability_v2", loader_tripwire)
    with pytest.raises(SystemExit, match="runtime module"):
        module.main(_execution_arguments(module, root, activation))

    assert loader_calls == 0
    assert not (root / "artifacts/test3_one_shot_real_train_v2").exists()


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
        "os",
        "pathlib",
        "stat",
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
        "load_owner_activation_capability_v2",
        "open_execution_authority",
        "run_g3p_recovery",
        "record_terminal_stop",
        "execution_authority_report",
        "close_execution_authority",
    } <= calls
    for forbidden in ("consume", "seal", "fit", "lstsq", "reserve", "deliver"):
        assert forbidden not in {call.lower() for call in calls}


@pytest.mark.parametrize("disposition", ("UNDERPOWERED_STOP", "INVALID_EVIDENCE"))
def test_existing_terminal_disposition_is_preserved_without_redundant_write(
    disposition: str,
) -> None:
    module = _load_runner()

    class ExistingTerminal:
        @staticmethod
        def execution_authority_report(_authority: object) -> dict[str, object]:
            return {"disposition": disposition}

        @staticmethod
        def record_terminal_stop(*_args: object, **_kwargs: object) -> object:
            raise AssertionError("existing terminal must not be written again")

    report, status = module._preserve_or_record_invalid_terminal(
        ExistingTerminal(), object(), RuntimeError("synthetic stop")
    )
    assert report == {"disposition": disposition}
    assert status == disposition


def test_missing_terminal_records_invalid_once_without_io() -> None:
    module = _load_runner()
    calls: list[str] = []

    class MissingTerminal:
        @staticmethod
        def execution_authority_report(_authority: object) -> dict[str, object]:
            raise RuntimeError("no terminal")

        @staticmethod
        def record_terminal_stop(
            _authority: object,
            *,
            disposition: str,
            reasons: tuple[str, ...],
            source_binding: dict[str, object],
        ) -> dict[str, object]:
            calls.append(disposition)
            assert reasons == ("RuntimeError: synthetic defect",)
            assert source_binding["failed_after_reservation"] is True
            return {"disposition": disposition}

    report, status = module._preserve_or_record_invalid_terminal(
        MissingTerminal(), object(), RuntimeError("synthetic defect")
    )
    assert report == {"disposition": "INVALID_EVIDENCE"}
    assert status == "INVALID_EVIDENCE"
    assert calls == ["INVALID_EVIDENCE"]


def test_terminal_publication_and_report_failure_is_truthful_after_reservation() -> None:
    """Ambiguous post-reservation failure never claims a pre-reservation stop."""

    module = _load_runner()
    calls = {"publication": 0, "report": 0}

    class UnavailableTerminal:
        @staticmethod
        def execution_authority_report(_authority: object) -> dict[str, object]:
            calls["report"] += 1
            raise RuntimeError("synthetic report retrieval failure")

        @staticmethod
        def record_terminal_stop(*_args: object, **_kwargs: object) -> object:
            calls["publication"] += 1
            raise RuntimeError("synthetic terminal publication failure")

    report, status = module._preserve_or_record_invalid_terminal(
        UnavailableTerminal(), object(), RuntimeError("synthetic recovery failure")
    )
    lines = module._execution_lines(report, None, status)

    assert report is None
    assert status == "INVALID_EVIDENCE"
    assert calls == {"publication": 1, "report": 2}
    assert "TERMINAL_REPORT=UNAVAILABLE_AFTER_RESERVATION_OR_PUBLICATION_FAILURE" in lines
    assert "TARGET_OR_PERMIT_CONSUMPTION=UNKNOWN_NOT_CLAIMED" in lines
    assert not any("BEFORE_RESERVATION" in line for line in lines)

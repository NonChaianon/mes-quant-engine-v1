"""Adversarial tests for the fixed synthetic Test 3 confirmatory-validation runner.

These tests exercise the runner's boundaries rather than its arithmetic: the
closed command line, the mandatory result label and claim guard, refusal of
preloaded or forged cached modules, refusal of symlinked or substituted source
origins, detection of module-origin drift, and the absence of any repository
write or any data, provider, target or evidence path operand.

No test reads, writes or otherwise touches any data, provider, target or
evidence surface, and no test writes anywhere in the repository. The only
filesystem writes are inside ``pytest``'s temporary directory, and they exist
solely to build the adversarial origins the runner must refuse.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import numpy
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNNER_SOURCE = REPOSITORY_ROOT / "tools" / "run_test3_confirmatory_validation.py"
IMPLEMENTATION_SOURCE = (
    REPOSITORY_ROOT / "src" / "mes_quant" / "exploration" / "test3_confirmatory_validation.py"
)
RATIFIED_BINDING_SOURCE = (
    REPOSITORY_ROOT
    / "docs"
    / "research"
    / "TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json"
)
RUNNER_MODULE_NAME = "run_test3_confirmatory_validation_under_test"

# Identifiers whose presence would contradict the runner's no-write, no-network,
# no-operand guarantees. Reading its own governed source and the ratified
# binding is permitted, so ``read_bytes`` is deliberately absent from this set.
FORBIDDEN_RUNNER_NAMES = frozenset(
    {
        "open",
        "os",
        "write_text",
        "write_bytes",
        "mkdir",
        "makedirs",
        "unlink",
        "rmtree",
        "rename",
        "touch",
        "chmod",
        "symlink_to",
        "system",
        "popen",
        "Popen",
        "socket",
        "urlopen",
        "urllib",
        "requests",
        "subprocess",
        "shutil",
        "pandas",
        "pyarrow",
        "databento",
        "getenv",
        "environ",
        "eval",
        "exec",
        "__import__",
    }
)


def _forbidden_runner_references(tree: ast.AST) -> frozenset[str]:
    """Return semantic forbidden references without conflating platform.system."""

    imports: dict[str, str] = {}
    violations: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                imports[alias.asname or root] = root
                if root in FORBIDDEN_RUNNER_NAMES:
                    violations.add(f"IMPORT:{root}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".", 1)[0]
            if root in FORBIDDEN_RUNNER_NAMES:
                violations.add(f"IMPORT_FROM:{root}")
            for alias in node.names:
                imports[alias.asname or alias.name] = f"{root}.{alias.name}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_RUNNER_NAMES:
            violations.add(f"NAME:{node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_RUNNER_NAMES:
            owner = node.value.id if isinstance(node.value, ast.Name) else None
            resolved_owner = imports.get(owner, owner) if owner is not None else None
            if node.attr == "system" and resolved_owner == "platform":
                continue
            violations.add(f"ATTRIBUTE:{node.attr}")
    return frozenset(violations)


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(RUNNER_MODULE_NAME, RUNNER_SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[RUNNER_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


runner = _load_runner()
RUNNER_TREE = ast.parse(RUNNER_SOURCE.read_bytes().decode("utf-8"))


def _run_isolated(
    tmp_path: Path,
    *,
    flags: tuple[str, ...] = ("-B", "-I"),
    arguments: tuple[str, ...] = ("--self-check",),
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ) if environment is None else dict(environment)
    return subprocess.run(
        [sys.executable, *flags, str(RUNNER_SOURCE), *arguments],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.fixture(autouse=True)
def clean_implementation_cache() -> Any:
    """Keep the runner's private module name clear before and after every test."""

    sys.modules.pop(runner.IMPLEMENTATION_MODULE_NAME, None)
    yield
    sys.modules.pop(runner.IMPLEMENTATION_MODULE_NAME, None)


# --------------------------------------------------------------------------
# Closed command line
# --------------------------------------------------------------------------


def test_the_only_accepted_token_is_the_fixed_self_check_mode() -> None:
    assert runner.parse_arguments(["--self-check"]) == "--self-check"
    assert runner.parse_arguments(("--self-check",)) == "--self-check"


def test_every_other_argument_vector_is_refused() -> None:
    rejected = (
        [],
        ["--self-check", "--self-check"],
        ["--self-check=1"],
        ["--selfcheck"],
        ["--Self-Check"],
        ["self-check"],
        [""],
        [None],
        [b"--self-check"],
        ["--self-check", "artifacts/exploration/test3"],
        ["--output", "artifacts/run.json"],
        ["--input", "data/market.parquet"],
        ["--evidence", "artifacts/exploration"],
        "--self-check",
        b"--self-check",
        None,
        {"mode": "--self-check"},
        42,
    )
    for argv in rejected:
        with pytest.raises(runner.RunnerRefusal) as caught:
            runner.parse_arguments(argv)
        assert caught.value.code == "ARGUMENTS_NONCONFORMING"


def test_no_data_provider_target_or_evidence_operand_exists_in_the_source() -> None:
    assert _forbidden_runner_references(RUNNER_TREE) == frozenset()
    assert runner.SELF_CHECK_MODE == "--self-check"
    for guarantee in (
        "NO_INPUT_PATH_OPERAND",
        "NO_OUTPUT_PATH_OPERAND",
        "NO_DATA_PROVIDER_OR_TARGET_PATH_OPERAND",
        "NO_EVIDENCE_PATH_OPERAND",
        "NO_REPOSITORY_WRITE_OF_ANY_KIND",
        "NO_NETWORK",
    ):
        assert guarantee in runner.RUNNER_GUARANTEES


def test_semantic_ast_guard_allows_platform_system_but_refuses_os_system_aliases() -> None:
    accepted = ast.parse("import platform\nplatform.system()\n")
    assert _forbidden_runner_references(accepted) == frozenset()
    refused_sources = (
        "import os\nos.system('x')\n",
        "import os as platform\nplatform.system('x')\n",
        "from os import system\nsystem('x')\n",
        "from os import system as move\nmove('x')\n",
        "system('x')\n",
    )
    for source in refused_sources:
        assert _forbidden_runner_references(ast.parse(source))


def test_numpy_is_not_imported_at_module_load_time() -> None:
    imports = []
    for node in RUNNER_TREE.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "numpy" not in imports
    assert runner.numpy is None


def test_the_runner_only_ever_names_its_two_governed_read_paths() -> None:
    assert runner.IMPLEMENTATION_SOURCE_PARTS == (
        "src",
        "mes_quant",
        "exploration",
        "test3_confirmatory_validation.py",
    )
    assert runner.RATIFIED_BINDING_PARTS == (
        "docs",
        "research",
        "TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
    )
    root = runner.runner_root()
    assert root == REPOSITORY_ROOT
    assert root.joinpath(*runner.IMPLEMENTATION_SOURCE_PARTS) == IMPLEMENTATION_SOURCE
    assert root.joinpath(*runner.RATIFIED_BINDING_PARTS) == RATIFIED_BINDING_SOURCE


# --------------------------------------------------------------------------
# Result label and claim guard
# --------------------------------------------------------------------------


def test_every_emitted_line_carries_the_local_synthetic_data_free_label() -> None:
    assert runner.RESULT_LABEL == "LOCAL_SYNTHETIC_DATA_FREE_IMPLEMENTATION_ONLY"
    line = runner.labelled("CHECK 01 SOMETHING: PASS: detail")
    assert line.startswith(f"{runner.RESULT_LABEL}: {runner.RUNNER_NAME}: ")


def test_the_claim_guard_refuses_every_forbidden_claim_token() -> None:
    for token in runner.FORBIDDEN_RESULT_CLAIM_TOKENS:
        with pytest.raises(runner.RunnerRefusal) as caught:
            runner.assert_no_claim(f"CHECK 01 {token}")
        assert caught.value.code == "RESULT_LABEL_NONCONFORMING"
        with pytest.raises(runner.RunnerRefusal):
            runner.labelled(f"prefix {token.lower()} suffix")
    with pytest.raises(runner.RunnerRefusal):
        runner.assert_no_claim(None)


def test_the_runners_own_vocabulary_is_claim_free() -> None:
    vocabulary = [
        runner.RESULT_LABEL,
        runner.SELF_CHECK_COMPLETE_TOKEN,
        runner.LOCAL_RUNTIME_ORIGIN_DISPOSITION,
        runner.NO_CLAIM_TOKEN,
        runner.CLASSIFICATION,
        runner.RUNNER_NAME,
        runner.SELF_CHECK_MODE,
        *runner.RUNNER_GUARANTEES,
        *runner.ERROR_CODES,
    ]
    for text in vocabulary:
        assert runner.assert_no_claim(text) == text


def test_the_no_claim_token_denies_every_named_authority() -> None:
    token = runner.NO_CLAIM_TOKEN
    for denial in (
        "NOT_ACTIVATION",
        "NOT_AN_EXECUTION_OR_SCORING_CHECKPOINT",
        "NOT_A_RESERVATION",
        "NOT_A_FIT_PERMIT",
        "NOT_A_WITNESS",
        "NO_OWNER_GRANT_2",
        "NO_C0V",
        "VALIDATION_REMAINS_UNOPENED",
        "ASSERTS_NO_SCIENTIFIC_RESULT",
    ):
        assert denial in token


# --------------------------------------------------------------------------
# Hardened startup, module cache, origin and drift refusals
# --------------------------------------------------------------------------


def test_missing_b_or_i_refuses_before_implementation_import(tmp_path: Path) -> None:
    for flags in (("-I",), ("-B",)):
        completed = _run_isolated(tmp_path, flags=flags)
        assert completed.returncode == 2
        assert "STARTUP_FLAGS_NONCONFORMING" in completed.stderr
        assert runner.SELF_CHECK_COMPLETE_TOKEN not in completed.stdout


def test_symlinked_runner_lexical_origin_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    link = tmp_path / runner.RUNNER_SOURCE_NAME
    link.symlink_to(RUNNER_SOURCE)
    monkeypatch.setattr(runner, "__file__", str(link))
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner._lexical_runner_path()
    assert caught.value.code == "RUNNER_ORIGIN_NONCONFORMING"


def test_hostile_pythonpath_is_ignored_by_the_isolated_success_path(tmp_path: Path) -> None:
    hostile = tmp_path / "hostile"
    (hostile / "numpy").mkdir(parents=True)
    (hostile / "numpy" / "__init__.py").write_text(
        'raise RuntimeError("hostile numpy imported")\n', encoding="utf-8"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(hostile)
    completed = _run_isolated(tmp_path, environment=env)
    assert completed.returncode == 0, completed.stderr
    assert runner.SELF_CHECK_COMPLETE_TOKEN in completed.stdout
    assert "hostile numpy imported" not in completed.stderr


def test_any_preloaded_numpy_or_submodule_is_refused() -> None:
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.load_trusted_numpy()
    assert caught.value.code == "NUMPY_CACHE_NONCONFORMING"


def test_symlinked_or_irregular_numpy_origin_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "real.py"
    target.write_text("# synthetic\n", encoding="utf-8")
    link = tmp_path / "linked.py"
    link.symlink_to(target)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner._regular_non_symlink_origin(str(link))
    assert caught.value.code == "NUMPY_ORIGIN_NONCONFORMING"
    with pytest.raises(runner.RunnerRefusal):
        runner._regular_non_symlink_origin(str(tmp_path))


def test_numpy_cache_origin_and_version_drift_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "numpy"
    package.mkdir()
    paths = []
    modules = []
    for name in ("__init__.py", "linalg.py", "random.py"):
        path = package / name
        path.write_text("# synthetic\n", encoding="utf-8")
        module = ModuleType(f"synthetic_{name}")
        module.__file__ = str(path)
        module.__spec__ = SimpleNamespace(origin=str(path))
        paths.append(str(path))
        modules.append(module)
    modules[0].__version__ = "synthetic-version"
    modules[0].__path__ = [str(package)]
    modules[0].__spec__ = SimpleNamespace(
        origin=paths[0], submodule_search_locations=[str(package)]
    )
    snapshot = (*modules, tuple(paths), "synthetic-version", package)
    monkeypatch.setattr(runner, "_NUMPY_SNAPSHOT", snapshot)
    for name, module in zip(("numpy", "numpy.linalg", "numpy.random"), modules, strict=True):
        monkeypatch.setitem(sys.modules, name, module)
    runner.revalidate_numpy_snapshot()

    monkeypatch.setitem(sys.modules, "numpy.linalg", ModuleType("replacement"))
    with pytest.raises(runner.RunnerRefusal) as cache_failure:
        runner.revalidate_numpy_snapshot()
    assert cache_failure.value.code == "NUMPY_CACHE_NONCONFORMING"
    monkeypatch.setitem(sys.modules, "numpy.linalg", modules[1])

    modules[0].__version__ = "drifted"
    with pytest.raises(runner.RunnerRefusal) as version_failure:
        runner.revalidate_numpy_snapshot()
    assert version_failure.value.code == "NUMPY_ORIGIN_NONCONFORMING"
    modules[0].__version__ = "synthetic-version"
    modules[2].__spec__ = SimpleNamespace(origin=str(package / "other.py"))
    with pytest.raises(runner.RunnerRefusal) as origin_failure:
        runner.revalidate_numpy_snapshot()
    assert origin_failure.value.code == "NUMPY_ORIGIN_NONCONFORMING"


def test_mutated_ratified_runtime_identity_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "numpy", numpy)
    document = json.loads(RATIFIED_BINDING_SOURCE.read_bytes())
    document["payload"]["runtime_identity_binding"]["identity"]["numpy"]["version"] = "drift"
    mutated = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.require_ratified_runtime_identity(mutated)
    assert caught.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_a_preloaded_or_forged_cached_module_is_refused() -> None:
    forged = ModuleType(runner.IMPLEMENTATION_MODULE_NAME)
    forged.MODULE_ID = runner.EXPECTED_MODULE_ID
    forged.CLASSIFICATION = runner.CLASSIFICATION
    sys.modules[runner.IMPLEMENTATION_MODULE_NAME] = forged
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.implementation_module()
    assert caught.value.code == "MODULE_CACHE_NONCONFORMING"
    assert sys.modules[runner.IMPLEMENTATION_MODULE_NAME] is forged


def test_a_symlinked_source_origin_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    (fake_root / "src" / "mes_quant" / "exploration").mkdir(parents=True)
    link = fake_root / "src" / "mes_quant" / "exploration" / IMPLEMENTATION_SOURCE.name
    link.symlink_to(IMPLEMENTATION_SOURCE)
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.implementation_module()
    assert caught.value.code == "IMPLEMENTATION_ORIGIN_NONCONFORMING"
    assert runner.IMPLEMENTATION_MODULE_NAME not in sys.modules


def test_a_symlinked_parent_directory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    (fake_root / "src" / "mes_quant").mkdir(parents=True)
    (fake_root / "src" / "mes_quant" / "exploration").symlink_to(
        IMPLEMENTATION_SOURCE.parent, target_is_directory=True
    )
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.implementation_module()
    assert caught.value.code == "IMPLEMENTATION_ORIGIN_NONCONFORMING"


def test_an_absent_or_irregular_origin_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    (fake_root / "src" / "mes_quant" / "exploration").mkdir(parents=True)
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.resolve_governed_file(
            runner.IMPLEMENTATION_SOURCE_PARTS, "IMPLEMENTATION_ORIGIN_NONCONFORMING"
        )
    assert caught.value.code == "IMPLEMENTATION_ORIGIN_NONCONFORMING"

    directory = fake_root / "src" / "mes_quant" / "exploration" / IMPLEMENTATION_SOURCE.name
    directory.mkdir()
    with pytest.raises(runner.RunnerRefusal):
        runner.resolve_governed_file(
            runner.IMPLEMENTATION_SOURCE_PARTS, "IMPLEMENTATION_ORIGIN_NONCONFORMING"
        )


def test_module_origin_drift_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    target = fake_root / "src" / "mes_quant" / "exploration"
    target.mkdir(parents=True)
    substituted = target / IMPLEMENTATION_SOURCE.name
    substituted.write_text(
        'MODULE_ID = "IMPOSTOR"\nCLASSIFICATION = "IMPOSTOR"\n', encoding="utf-8"
    )
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.implementation_module()
    assert caught.value.code == "IMPLEMENTATION_ORIGIN_NONCONFORMING"
    assert runner.IMPLEMENTATION_MODULE_NAME not in sys.modules


def test_an_unloadable_source_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    target = fake_root / "src" / "mes_quant" / "exploration"
    target.mkdir(parents=True)
    (target / IMPLEMENTATION_SOURCE.name).write_text("def (\n", encoding="utf-8")
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.implementation_module()
    assert caught.value.code == "IMPLEMENTATION_IMPORT_NONCONFORMING"
    assert runner.IMPLEMENTATION_MODULE_NAME not in sys.modules


def test_a_missing_ratified_binding_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    (fake_root / "docs" / "research").mkdir(parents=True)
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.read_ratified_binding_bytes()
    assert caught.value.code == "RATIFIED_BINDING_ORIGIN_NONCONFORMING"


def test_a_symlinked_ratified_binding_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "worktree"
    (fake_root / "docs" / "research").mkdir(parents=True)
    (fake_root / "docs" / "research" / RATIFIED_BINDING_SOURCE.name).symlink_to(
        RATIFIED_BINDING_SOURCE
    )
    monkeypatch.setattr(runner, "runner_root", lambda: fake_root)
    with pytest.raises(runner.RunnerRefusal) as caught:
        runner.read_ratified_binding_bytes()
    assert caught.value.code == "RATIFIED_BINDING_ORIGIN_NONCONFORMING"


def test_the_governed_origin_is_accepted_and_the_module_identity_is_bound() -> None:
    module = runner.implementation_module()
    assert module.MODULE_ID == runner.EXPECTED_MODULE_ID
    assert module.CLASSIFICATION == runner.CLASSIFICATION
    assert Path(module.__file__).resolve() == IMPLEMENTATION_SOURCE
    assert module.__spec__.origin == str(IMPLEMENTATION_SOURCE)
    assert sys.modules[runner.IMPLEMENTATION_MODULE_NAME] is module
    assert runner.read_ratified_binding_bytes() == RATIFIED_BINDING_SOURCE.read_bytes()


# --------------------------------------------------------------------------
# End-to-end behaviour of the closed self-check
# --------------------------------------------------------------------------


def test_the_isolated_self_check_completes_and_leaves_no_source_bytecode(tmp_path: Path) -> None:
    pycache = IMPLEMENTATION_SOURCE.parent / "__pycache__"
    before = set(pycache.glob("test3_confirmatory_validation*.pyc")) if pycache.exists() else set()
    completed = _run_isolated(tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    lines = [line for line in completed.stdout.splitlines() if line]
    assert lines, "the self-check must emit at least one line"
    for line in lines:
        assert line.startswith(f"{runner.RESULT_LABEL}: {runner.RUNNER_NAME}: ")
        assert runner.assert_no_claim(line) == line
    assert any(runner.SELF_CHECK_COMPLETE_TOKEN in line for line in lines)
    assert any(runner.NO_CLAIM_TOKEN in line for line in lines)
    assert all(": FAIL: " not in line for line in lines)
    after = set(pycache.glob("test3_confirmatory_validation*.pyc")) if pycache.exists() else set()
    assert after == before


def test_every_named_check_reports_a_pass_from_an_isolated_process(tmp_path: Path) -> None:
    completed = _run_isolated(tmp_path)
    assert completed.returncode == 0, completed.stderr
    checks = [line for line in completed.stdout.splitlines() if ": CHECK " in line]
    assert len(checks) >= 14
    for expected in (
        "RATIFIED_GOLDEN_BINDING_BYTEWISE_MATCH",
        "A_ONE_BYTE_MUTATION_OF_THE_RATIFIED_BINDING_IS_REFUSED",
        "RANK_AND_IDENTITY_GATES_PRECEDE_ANY_SOLVE",
        "SCORING_READINESS_NEVER_MINTS_OR_AUTHENTICATES_OWNER_GRANT_2",
        "DERIVED_SESSION_COUNT_GATE_IGNORES_CALLER_SCALARS",
        "EVERY_AUTHORITATIVE_INTERMEDIATE_MUST_BE_FINITE",
        "INTEGRITY_BEFORE_SUPPORT_PRECEDENCE",
        "ASYMMETRIC_EQUALITY_BOUNDARIES",
    ):
        assert any(expected in line for line in checks), expected
    assert all(": PASS: " in line for line in checks)


def test_a_nonconforming_argument_vector_exits_two_with_a_labelled_refusal(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert runner.main(["--output", "artifacts/run.json"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"{runner.RESULT_LABEL}: {runner.RUNNER_NAME}: ")
    assert "ARGUMENTS_NONCONFORMING" in captured.err
    assert runner.assert_no_claim(captured.err.strip()) == captured.err.strip()


def test_a_failing_named_check_exits_two_without_claiming_anything(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(_module: Any, _binding: bytes) -> tuple[tuple[str, bool, str], ...]:
        return (("SYNTHETIC_CHECK", False, "deliberate synthetic failure"),)

    module = object()
    monkeypatch.setattr(runner, "require_hardened_startup", lambda: REPOSITORY_ROOT)
    monkeypatch.setattr(runner, "load_trusted_numpy", lambda: numpy)
    monkeypatch.setattr(runner, "read_ratified_binding_bytes", lambda: b"binding")
    monkeypatch.setattr(runner, "require_ratified_runtime_identity", lambda _raw: None)
    monkeypatch.setattr(runner, "implementation_module", lambda: module)
    monkeypatch.setattr(runner, "revalidate_numpy_snapshot", lambda: None)
    monkeypatch.setattr(runner, "run_self_check", failing)
    assert runner.main(["--self-check"]) == 2
    captured = capsys.readouterr()
    assert "SYNTHETIC_CHECK: FAIL:" in captured.out
    assert "SELF_CHECK_FAILED" in captured.err
    assert runner.SELF_CHECK_COMPLETE_TOKEN not in captured.out
    for line in captured.out.splitlines() + captured.err.splitlines():
        if line:
            assert line.startswith(runner.RESULT_LABEL)


def test_an_internal_failure_is_reported_without_a_traceback(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def exploding(_module: Any, _binding: bytes) -> tuple[tuple[str, bool, str], ...]:
        raise ZeroDivisionError("synthetic")

    module = object()
    monkeypatch.setattr(runner, "require_hardened_startup", lambda: REPOSITORY_ROOT)
    monkeypatch.setattr(runner, "load_trusted_numpy", lambda: numpy)
    monkeypatch.setattr(runner, "read_ratified_binding_bytes", lambda: b"binding")
    monkeypatch.setattr(runner, "require_ratified_runtime_identity", lambda _raw: None)
    monkeypatch.setattr(runner, "implementation_module", lambda: module)
    monkeypatch.setattr(runner, "revalidate_numpy_snapshot", lambda: None)
    monkeypatch.setattr(runner, "run_self_check", exploding)
    assert runner.main(["--self-check"]) == 2
    captured = capsys.readouterr()
    assert "INTERNAL_NONCONFORMANCE: ZeroDivisionError" in captured.err
    assert "Traceback" not in captured.err

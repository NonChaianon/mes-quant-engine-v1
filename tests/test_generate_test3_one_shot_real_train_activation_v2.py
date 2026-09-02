"""Data-free tests for the standalone Test 3 V2 activation generator."""

from __future__ import annotations

import ast
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPOSITORY_ROOT / "tools/generate_test3_one_shot_real_train_activation_v2.py"


def _load_generator():
    specification = importlib.util.spec_from_file_location(
        "_test3_activation_v2_generator", GENERATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _fixture_repository(tmp_path: Path, generator) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    required = {
        generator.PLAN_PATH,
        generator.OWNER_AUTHORIZATION_PATH,
        generator.PROTOCOL_PATH,
        generator.CONTRACT_PATH,
        generator.G3P_PATH,
        generator.G3F_PATH,
        *generator.IMPLEMENTATION_PATHS,
    }
    for relative in required:
        source = REPOSITORY_ROOT.joinpath(*relative.split("/"))
        destination = root.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "synthetic@example.invalid")
    _git(root, "config", "user.name", "Synthetic Test")
    _git(root, "checkout", "-q", "-b", "governance/test3-one-shot-real-train-v2")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "synthetic V2 generator fixture")
    _git(root, "update-ref", generator.ORIGIN_REF, "HEAD")
    return root


def test_check_is_deterministic_and_data_free(tmp_path: Path) -> None:
    generator = _load_generator()
    root = _fixture_repository(tmp_path, generator)

    generator.run_mode("check", repository_root=root)
    generator.run_mode("check", repository_root=root)

    assert not (root / generator.OUTPUT_PATH).exists()
    assert not (root / generator.EVIDENCE_ROOT).exists()


def test_create_is_exclusive_and_verify_existing_is_read_only(tmp_path: Path) -> None:
    generator = _load_generator()
    root = _fixture_repository(tmp_path, generator)

    generator.run_mode("create", repository_root=root)
    activation = root / generator.OUTPUT_PATH
    before = activation.read_bytes()
    generator.run_mode("verify-existing", repository_root=root)
    assert activation.read_bytes() == before
    assert not (root / generator.EVIDENCE_ROOT).exists()

    with pytest.raises(generator.ActivationV2Error):
        generator.run_mode("create", repository_root=root)
    assert activation.read_bytes() == before


@pytest.mark.parametrize("drift", ("owner", "implementation", "git"))
def test_verify_refuses_owner_git_or_implementation_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    generator = _load_generator()
    root = _fixture_repository(tmp_path, generator)
    generator.run_mode("create", repository_root=root)

    if drift == "owner":
        path = root / generator.OWNER_AUTHORIZATION_PATH
        path.write_bytes(path.read_bytes() + b"synthetic drift\n")
    elif drift == "implementation":
        path = root / generator.IMPLEMENTATION_PATHS[0]
        path.write_bytes(path.read_bytes() + b"# synthetic drift\n")
    else:
        marker = root / "synthetic-git-drift"
        marker.write_text("drift\n", encoding="utf-8")
        _git(root, "add", marker.name)
        _git(root, "commit", "-q", "-m", "synthetic Git drift")

    with pytest.raises(generator.ActivationV2Error):
        generator.run_mode("verify-existing", repository_root=root)


def test_unsafe_plan_symlink_is_refused_without_output(tmp_path: Path) -> None:
    generator = _load_generator()
    root = _fixture_repository(tmp_path, generator)
    plan = root / generator.PLAN_PATH
    outside = tmp_path / "outside-plan"
    outside.write_bytes(plan.read_bytes())
    plan.unlink()
    plan.symlink_to(outside)

    with pytest.raises(generator.ActivationV2Error, match="symlinked"):
        generator.run_mode("check", repository_root=root)
    assert not (root / generator.OUTPUT_PATH).exists()


def test_generator_imports_only_stdlib_and_no_runtime_or_data_surface() -> None:
    source = GENERATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)

    assert not any(name.startswith("mes_quant") for name in imported)
    assert imported <= {
        "__future__",
        "argparse",
        "ast",
        "collections.abc",
        "hashlib",
        "json",
        "math",
        "os",
        "pathlib",
        "secrets",
        "stat",
        "subprocess",
        "sys",
        "typing",
    }
    for forbidden in (
        "databento",
        "pandas",
        "pyarrow",
        "requests",
        "socket",
        "load_owner_activation_capability",
    ):
        assert forbidden not in source

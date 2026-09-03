"""Synthetic tests for the Test 3 confirmatory-validation preparation tool.

Every test runs against a throwaway synthetic Git repository under pytest
``tmp_path``. Because every mode accepts exactly one output value, the synthetic
repositories use that same relative path, but always rooted in ``tmp_path``: no
test reads, writes or otherwise touches the real repository binding artifact,
and no test opens any data, provider, target or evidence surface.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.machinery
import importlib.util
import itertools
import json
import marshal
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy
import pytest

REAL_REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_RELATIVE_PATH = "tools/prepare_test3_confirmatory_validation_prerequisites.py"
TESTS_RELATIVE_PATH = "tests/test_prepare_test3_confirmatory_validation_prerequisites.py"
GOVERNED_RELATIVE_PATHS = (
    "src/mes_quant/core/hashing.py",
    "src/mes_quant/governance/classification/reference_objects.py",
    "src/mes_quant/exploration/test3_contract.py",
)
PACKAGE_INIT_RELATIVE_PATHS = (
    "src/mes_quant/__init__.py",
    "src/mes_quant/core/__init__.py",
    "src/mes_quant/governance/__init__.py",
    "src/mes_quant/governance/classification/__init__.py",
    "src/mes_quant/exploration/__init__.py",
)
RECORD_RELATIVE_PATH = "docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md"
PROTOCOL_ID = "MES_TEST3_RV60_HAR_RISK_EDGE_V1"
PROTOCOL_RELATIVE_PATH = "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md"
BUDGET_ID = "MES_PROJECT_TARGET_SPACE_BUDGET_V1"
BUDGET_RELATIVE_PATH = "docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md"
# Every mode accepts exactly one output value. The synthetic repositories below
# therefore use that same relative path *inside pytest tmp_path only*; the real
# repository artifact is never named as an operand, read or written.
OUTPUT_RELATIVE_PATH = "docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json"
FIXTURE_STORAGE_LITERAL = "IN_MEMORY_AND_INSIDE_PATH3_ONLY"
REJECTED_OUTPUT_VALUES = (
    "../escape.json",
    "docs/research/../../escape.json",
    "docs/research/binding.txt",
    "docs/research/SYNTHETIC_TOOLING_BINDING_TMP.json",
    "docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V2.json",
    "./docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
    "docs/research//TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
    "DOCS/RESEARCH/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
    "tools/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
)

SYNTHETIC_PROTOCOL_BYTES = b"# Synthetic parent protocol\n\nSynthetic bytes for tooling tests.\n"
SYNTHETIC_BUDGET_BYTES = b"# Synthetic parent budget\n\nSynthetic bytes for tooling tests.\n"

_MODULE_COUNTER = itertools.count()


# --------------------------------------------------------------------------
# Synthetic repository construction
# --------------------------------------------------------------------------


def _git(repo: Path, *arguments: str) -> str:
    environment = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "Synthetic Fixture",
        "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
        "GIT_COMMITTER_NAME": "Synthetic Fixture",
        "GIT_COMMITTER_EMAIL": "synthetic@example.invalid",
    }
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Synthetic Fixture",
            "-c",
            "user.email=synthetic@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout.strip()


def record_text(commit: str, rows: tuple[tuple[str, str, str], ...]) -> str:
    body = "\n".join(f"| `{identity}` | `{path}` | `{digest}` |" for identity, path, digest in rows)
    return (
        "# Synthetic Owner Co-Ratification Record\n"
        "\n"
        "Record ID: `SYNTHETIC_TEST_RECORD`\n"
        "\n"
        f"Ratified commit: `{commit}`\n"
        "\n"
        "## 1. Co-ratified artifacts\n"
        "\n"
        "| Identity | Path | SHA-256 at ratified commit |\n"
        "| --- | --- | --- |\n"
        f"{body}\n"
        "\n"
        "## 2. Synthetic tail\n"
        "\n"
        "Synthetic preparation fixture only.\n"
    )


def default_rows(protocol_digest: str, budget_digest: str) -> tuple[tuple[str, str, str], ...]:
    return (
        (PROTOCOL_ID, PROTOCOL_RELATIVE_PATH, protocol_digest),
        (BUDGET_ID, BUDGET_RELATIVE_PATH, budget_digest),
    )


def build_synthetic_repository(root: Path, *, budget_as_symlink: bool = False) -> Path:
    """Create a two-commit synthetic repository mirroring the bound layout."""

    repo = root / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")

    for relative in ("tools", "tests", "docs/research"):
        (repo / relative).mkdir(parents=True, exist_ok=True)
    for relative in PACKAGE_INIT_RELATIVE_PATHS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'"""Synthetic package stub."""\n')
    for relative in (*GOVERNED_RELATIVE_PATHS, TOOL_RELATIVE_PATH, TESTS_RELATIVE_PATH):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REAL_REPO_ROOT / relative, target)

    (repo / PROTOCOL_RELATIVE_PATH).write_bytes(SYNTHETIC_PROTOCOL_BYTES)
    if budget_as_symlink:
        (repo / BUDGET_RELATIVE_PATH).symlink_to(Path(PROTOCOL_RELATIVE_PATH).name)
    else:
        (repo / BUDGET_RELATIVE_PATH).write_bytes(SYNTHETIC_BUDGET_BYTES)

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic parents")
    ratified_commit = _git(repo, "rev-parse", "HEAD")

    protocol_digest = hashlib.sha256(SYNTHETIC_PROTOCOL_BYTES).hexdigest()
    budget_digest = hashlib.sha256(SYNTHETIC_BUDGET_BYTES).hexdigest()
    (repo / RECORD_RELATIVE_PATH).write_bytes(
        record_text(ratified_commit, default_rows(protocol_digest, budget_digest)).encode("utf-8")
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic ratification record")
    return repo


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_import_state():
    saved_path = list(sys.path)
    saved_meta_path = list(sys.meta_path)
    saved_modules = set(sys.modules)
    try:
        yield
    finally:
        sys.path[:] = saved_path
        sys.meta_path[:] = saved_meta_path
        for name in [key for key in sys.modules if key not in saved_modules]:
            if name.startswith(("_mes_governed_", "_synthetic_tool_")):
                del sys.modules[name]


@pytest.fixture(scope="session")
def _prepared_repository(tmp_path_factory) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git is required to build the synthetic repository")
    return build_synthetic_repository(tmp_path_factory.mktemp("prepared"))


@pytest.fixture()
def repo(_prepared_repository: Path, tmp_path: Path) -> Path:
    target = (tmp_path / "repo").resolve()
    shutil.copytree(_prepared_repository, target, symlinks=True)
    return target


def load_tool(repo: Path):
    path = repo / TOOL_RELATIVE_PATH
    name = f"_synthetic_tool_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def tool(repo: Path):
    return load_tool(repo)


@pytest.fixture()
def helpers(tool, repo: Path):
    return tool.load_governed_helpers(repo)


def target_for(tool, repo: Path):
    """Resolve the single authorized output inside the synthetic repository."""

    return tool.resolve_output_path(repo, tool.BINDING_RELATIVE_PATH)


def visible_files(repo: Path) -> set[str]:
    return {
        str(path.relative_to(repo))
        for path in repo.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repo).parts
    }


# --------------------------------------------------------------------------
# Closed arguments
# --------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["check", "create", "verify-existing"])
def test_parse_arguments_accepts_each_closed_mode(tool, mode: str) -> None:
    assert tool.parse_arguments([mode, "--output", OUTPUT_RELATIVE_PATH]) == (
        mode,
        OUTPUT_RELATIVE_PATH,
    )


def test_the_only_authorized_output_is_the_exact_binding_path(tool) -> None:
    assert tool.BINDING_RELATIVE_PATH == OUTPUT_RELATIVE_PATH
    assert tool.AUTHORIZED_TOOLING_PATHS[2] == OUTPUT_RELATIVE_PATH
    assert tool.FIXTURE_STORAGE == FIXTURE_STORAGE_LITERAL


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["check"],
        ["check", "--output"],
        ["check", "--output", "a.json", "--extra"],
        ["check", "-o", "a.json"],
        ["check", "--out", "a.json"],
        ["CHECK", "--output", "a.json"],
        ["verify_existing", "--output", "a.json"],
        ["rehearse", "--output", "a.json"],
        ["check", "--output", " a.json"],
        ["check", "--output", ""],
    ],
)
def test_parse_arguments_rejects_nonconforming(tool, argv: list[str]) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.parse_arguments(argv)
    assert raised.value.code == "ARGUMENTS_NONCONFORMING"


# --------------------------------------------------------------------------
# Ratification record parsing
# --------------------------------------------------------------------------


def _valid_record_text() -> str:
    return record_text("0" * 40, default_rows("a" * 64, "b" * 64))


def test_parse_ratification_record_success(tool) -> None:
    record = tool.parse_ratification_record(_valid_record_text().encode("utf-8"))
    assert record.ratified_commit == "0" * 40
    assert [row.artifact_id for row in record.rows] == [PROTOCOL_ID, BUDGET_ID]
    assert [row.path for row in record.rows] == [PROTOCOL_RELATIVE_PATH, BUDGET_RELATIVE_PATH]
    assert [row.recorded_sha256 for row in record.rows] == ["a" * 64, "b" * 64]


def _drop_commit(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("Ratified commit"))


def _duplicate_commit(text: str) -> str:
    return text.replace(
        f"Ratified commit: `{'0' * 40}`\n",
        f"Ratified commit: `{'0' * 40}`\nRatified commit: `{'1' * 40}`\n",
    )


def _no_sections(text: str) -> str:
    """Actually remove every section heading, not merely the document title."""

    lines = text.splitlines()
    assert any(line.startswith("## ") for line in lines)
    stripped = [line for line in lines if not line.startswith("## ")]
    assert not any(line.startswith("## ") for line in stripped)
    return "\n".join(stripped) + "\n"


def _commit_in_body(text: str) -> str:
    return text.replace(
        "Synthetic preparation fixture only.", f"Ratified commit: `{'0' * 40}`"
    )


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_drop_commit, id="missing_commit"),
        pytest.param(_duplicate_commit, id="duplicate_commit"),
        pytest.param(_commit_in_body, id="commit_outside_preamble"),
        pytest.param(lambda text: text.replace("0" * 40, "0" * 7), id="abbreviated_commit"),
        pytest.param(lambda text: text.replace("0" * 40, "0" * 39 + "Z"), id="malformed_commit"),
        pytest.param(lambda text: text.replace("a" * 64, "a" * 63), id="abbreviated_digest"),
        pytest.param(lambda text: text.replace("a" * 64, "A" * 64), id="uppercase_digest"),
        pytest.param(
            lambda text: text.replace(
                f"| `{BUDGET_ID}`", f"| `{PROTOCOL_ID}`"
            ),
            id="duplicate_identity",
        ),
        pytest.param(
            lambda text: text.replace(f"| `{BUDGET_ID}`", "| `MES_UNKNOWN_ARTIFACT_V1`"),
            id="missing_required_identity",
        ),
        pytest.param(
            lambda text: text.replace(PROTOCOL_RELATIVE_PATH, "docs/research/OTHER.md"),
            id="mismatched_path",
        ),
        pytest.param(
            lambda text: text.replace(
                "## 2. Synthetic tail",
                f"| `MES_EXTRA_V1` | `docs/research/EXTRA.md` | `{'c' * 64}` |\n\n## 2. Synthetic tail",
            ),
            id="extra_row",
        ),
        pytest.param(
            lambda text: text.replace("| Identity | Path | SHA-256 at ratified commit |\n", ""),
            id="missing_header",
        ),
        pytest.param(
            lambda text: text.replace("| --- | --- | --- |\n", ""),
            id="missing_separator",
        ),
        pytest.param(
            lambda text: text.replace("## 1. Co-ratified artifacts", "## 9. Elsewhere"),
            id="missing_section_one",
        ),
        pytest.param(_no_sections, id="no_sections"),
    ],
)
def test_parse_ratification_record_rejects(tool, mutate) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.parse_ratification_record(mutate(_valid_record_text()).encode("utf-8"))
    assert raised.value.code == "RATIFICATION_RECORD_NONCONFORMING"


def test_parse_ratification_record_rejects_non_utf8(tool) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.parse_ratification_record(b"\xff\xfe not utf-8")
    assert raised.value.code == "RATIFICATION_RECORD_NONCONFORMING"


# --------------------------------------------------------------------------
# Git object selection
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FakeObject:
    path_bytes: bytes
    mode: str
    object_type: str
    object_sha1: str


def _entry(path: str, mode: str = "100644", object_type: str = "blob") -> FakeObject:
    return FakeObject(
        path_bytes=path.encode("utf-8"),
        mode=mode,
        object_type=object_type,
        object_sha1="0" * 40,
    )


def test_select_unique_blob_success(tool) -> None:
    objects = (_entry("docs/other.md"), _entry(PROTOCOL_RELATIVE_PATH))
    assert tool.select_unique_blob(objects, PROTOCOL_RELATIVE_PATH).mode == "100644"


@pytest.mark.parametrize(
    "objects",
    [
        pytest.param((), id="missing"),
        pytest.param((_entry("docs/other.md"),), id="absent_path"),
        pytest.param(
            (_entry(PROTOCOL_RELATIVE_PATH), _entry(PROTOCOL_RELATIVE_PATH)), id="duplicate"
        ),
        pytest.param((_entry(PROTOCOL_RELATIVE_PATH, mode="120000"),), id="symlink_entry"),
        pytest.param(
            (_entry(PROTOCOL_RELATIVE_PATH, mode="160000", object_type="commit"),),
            id="gitlink_entry",
        ),
        pytest.param(
            (
                FakeObject(
                    path_bytes=PROTOCOL_RELATIVE_PATH.encode("utf-8"),
                    mode="100644",
                    object_type="blob",
                    object_sha1="not-a-sha1",
                ),
            ),
            id="malformed_identity",
        ),
    ],
)
def test_select_unique_blob_rejects(tool, objects) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.select_unique_blob(objects, PROTOCOL_RELATIVE_PATH)
    assert raised.value.code == "GIT_REFERENCE_NONCONFORMING"


# --------------------------------------------------------------------------
# Import provenance
# --------------------------------------------------------------------------


class FakeEditableFinder:
    """Stand-in for an ambient editable-install meta-path finder."""

    def find_spec(self, fullname, path=None, target=None):
        """Match the finder protocol and claim nothing."""


FakeEditableFinder.__module__ = "__editable___mes_quant_finder"


def test_import_provenance_closes_ambient_editable_install(tool, repo: Path, tmp_path) -> None:
    shadow = tmp_path / "fake-site-packages"
    (shadow / "mes_quant").mkdir(parents=True)
    (shadow / "mes_quant" / "__init__.py").write_text('"""ambient shadow."""\n')
    sys.path.insert(0, str(shadow))
    finder = FakeEditableFinder()
    sys.meta_path.insert(0, finder)

    loaded = tool.load_governed_helpers(repo)

    assert sys.path[0] == str(repo / "src")
    assert str(shadow) not in sys.path
    assert finder not in sys.meta_path
    assert not any(
        getattr(type(item), "__module__", "").startswith("__editable__") for item in sys.meta_path
    )
    assert not any(
        name == "mes_quant" or name.startswith("mes_quant.") for name in sys.modules
    )
    assert list(loaded.origins.values()) == list(GOVERNED_RELATIVE_PATHS)
    assert sys.modules["_mes_governed_hashing"].__file__ == str(
        repo / "src/mes_quant/core/hashing.py"
    )
    assert callable(loaded.sha256_bytes) and callable(loaded.frozen_contract_sha256)


def _delete_governed_module(repo: Path) -> None:
    (repo / GOVERNED_RELATIVE_PATHS[0]).unlink()


def _symlink_governed_module(repo: Path) -> None:
    path = repo / GOVERNED_RELATIVE_PATHS[0]
    payload = path.read_bytes()
    path.unlink()
    real = repo / "src/mes_quant/core/_hashing_real.py"
    real.write_bytes(payload)
    path.symlink_to(real.name)


def _remove_package_init(repo: Path) -> None:
    (repo / "src/mes_quant/__init__.py").unlink()


def _remove_src_root(repo: Path) -> None:
    shutil.rmtree(repo / "src")


@pytest.mark.parametrize(
    "hostile",
    [
        pytest.param(_delete_governed_module, id="module_absent"),
        pytest.param(_symlink_governed_module, id="module_is_symlink"),
        pytest.param(_remove_package_init, id="package_origin_unprovable"),
        pytest.param(_remove_src_root, id="src_root_absent"),
    ],
)
def test_import_provenance_rejects_hostile_origins(tool, repo: Path, tmp_path, hostile) -> None:
    shadow = tmp_path / "fake-site-packages"
    (shadow / "mes_quant").mkdir(parents=True)
    (shadow / "mes_quant" / "__init__.py").write_text('"""ambient shadow."""\n')
    sys.path.insert(0, str(shadow))
    hostile(repo)

    with pytest.raises(tool.PreparationError) as raised:
        tool.load_governed_helpers(repo)
    assert raised.value.code == "IMPORT_PROVENANCE_NONCONFORMING"


def test_governed_helper_bytes_drift_is_refused(tool, repo: Path, helpers) -> None:
    path = repo / GOVERNED_RELATIVE_PATHS[0]
    path.write_bytes(path.read_bytes() + b"\n# synthetic worktree drift\n")
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_binding_payload(repo, helpers)
    assert raised.value.code == "GOVERNED_HELPER_BYTES_DRIFT"


def test_pre_execution_verification_binds_every_allowed_helper(tool, repo: Path) -> None:
    bindings = tool.verify_governed_helper_blobs(repo)
    assert [binding["path"] for binding in bindings.values()] == list(GOVERNED_RELATIVE_PATHS)
    for relative, binding in zip(GOVERNED_RELATIVE_PATHS, bindings.values(), strict=True):
        assert binding["object_type"] == "blob"
        assert binding["mode"] in {"100644", "100755"}
        assert len(binding["blob_sha1"]) == 40
        assert binding["byte_count"] == len((repo / relative).read_bytes())
        assert binding["verification"] == (
            "WORKTREE_BYTES_EQUAL_TRACKED_HEAD_BLOB_BEFORE_ANY_HELPER_EXECUTION"
        )
    loaded = tool.load_governed_helpers(repo)
    assert dict(loaded.pre_exec_blob_bindings) == bindings


def _execution_marker_injection(marker: Path) -> bytes:
    """Module-level bytes that would create a marker file if they ever executed."""

    return (
        "\n"
        f"with open({str(marker)!r}, 'w', encoding='utf-8') as _hostile_stream:\n"
        "    _hostile_stream.write('EXECUTED')\n"
    ).encode()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_mutated_governed_helper_never_executes(
    tool, repo: Path, tmp_path: Path, index: int
) -> None:
    """A helper mutated before load must fail stably and never run one byte."""

    marker = tmp_path / f"hostile_helper_execution_{index}.marker"
    path = repo / GOVERNED_RELATIVE_PATHS[index]
    path.write_bytes(path.read_bytes() + _execution_marker_injection(marker))

    with pytest.raises(tool.PreparationError) as raised:
        tool.load_governed_helpers(repo)

    assert raised.value.code == "GOVERNED_HELPER_BYTES_DRIFT"
    assert not marker.exists()
    assert not any(name.startswith("_mes_governed_") for name in sys.modules)


def test_verified_helper_sources_retain_the_exact_executed_bytes(tool, repo: Path) -> None:
    """The retained bytes, their binding and the executed module must agree."""

    verified = tool.verify_governed_helper_sources(repo)
    assert [source.relative_path for source in verified.values()] == list(
        GOVERNED_RELATIVE_PATHS
    )
    for relative, source in zip(GOVERNED_RELATIVE_PATHS, verified.values(), strict=True):
        assert source.source_bytes == (repo / relative).read_bytes()
        assert source.binding["path"] == relative
        assert source.binding["byte_count"] == len(source.source_bytes)

    assert tool.verify_governed_helper_blobs(repo) == {
        alias: dict(source.binding) for alias, source in verified.items()
    }

    loaded = tool.load_governed_helpers(repo)
    assert dict(loaded.pre_exec_blob_bindings) == {
        alias: dict(source.binding) for alias, source in verified.items()
    }
    for alias, source in verified.items():
        module = sys.modules[f"_mes_governed_{alias}"]
        assert module.__file__ == str(repo / source.relative_path)
    assert loaded.sha256_bytes(b"MES") == hashlib.sha256(b"MES").hexdigest()


def test_post_verification_path_swap_cannot_execute_unverified_bytes(
    tool, repo: Path, tmp_path: Path, capsys
) -> None:
    """A helper path swapped after verification never contributes one byte."""

    marker = tmp_path / "post_verification_path_swap.marker"
    relative = GOVERNED_RELATIVE_PATHS[0]
    source_path = repo / relative
    verified = tool.verify_governed_helper_sources(repo)
    original_bytes = verified["hashing"].source_bytes
    assert original_bytes == source_path.read_bytes()

    # The adversary swaps the proven path after it was verified.
    source_path.write_bytes(original_bytes + _execution_marker_injection(marker))
    assert source_path.read_bytes() != original_bytes

    module = tool._load_module_from_verified_bytes(
        "hashing", source_path, original_bytes, ("sha256_bytes", "canonical_json_bytes")
    )

    assert not marker.exists()
    assert module.__name__ == "_mes_governed_hashing"
    assert module.__file__ == str(source_path)
    assert module.sha256_bytes(b"MES") == hashlib.sha256(b"MES").hexdigest()

    # The same drift still fails before any binding is published.
    before = visible_files(repo)
    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "GOVERNED_HELPER_BYTES_DRIFT" in captured.err
    assert not marker.exists()
    assert visible_files(repo) == before
    assert not (repo / OUTPUT_RELATIVE_PATH).exists()


def _poison_eligible_cached_bytecode(source_path: Path, marker: Path) -> Path:
    """Write a timestamp-eligible ``__pycache__`` entry carrying hostile code."""

    hostile = compile(
        source_path.read_bytes() + _execution_marker_injection(marker),
        str(source_path),
        "exec",
        dont_inherit=True,
    )
    cache = Path(importlib.util.cache_from_source(str(source_path)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    info = os.stat(source_path)
    header = importlib.util.MAGIC_NUMBER + struct.pack(
        "<III", 0, int(info.st_mtime) & 0xFFFFFFFF, info.st_size & 0xFFFFFFFF
    )
    cache.write_bytes(header + marshal.dumps(hostile))
    return cache


def _poisoned_cache_is_eligible(source_path: Path, probe_marker: Path) -> bool:
    """Prove the poisoned cache really would be used by the stdlib source loader."""

    name = f"_pyc_eligibility_probe_{next(_MODULE_COUNTER)}"
    loader = importlib.machinery.SourceFileLoader(name, str(source_path))
    spec = importlib.util.spec_from_file_location(name, source_path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with contextlib.suppress(Exception):
        loader.exec_module(module)
    sys.modules.pop(name, None)
    return probe_marker.exists()


def test_poisoned_eligible_cached_bytecode_never_executes(
    tool, repo: Path, tmp_path: Path
) -> None:
    """An eligible poisoned ``.pyc`` cannot substitute unverified module code."""

    relative = GOVERNED_RELATIVE_PATHS[0]
    source_path = repo / relative
    verified = tool.verify_governed_helper_sources(repo)
    original_bytes = verified["hashing"].source_bytes

    probe_marker = tmp_path / "poisoned_pyc_probe.marker"
    _poison_eligible_cached_bytecode(source_path, probe_marker)
    if not _poisoned_cache_is_eligible(source_path, probe_marker):
        pytest.skip("cached bytecode is not eligible for the stdlib loader here")
    probe_marker.unlink()

    marker = tmp_path / "poisoned_pyc_execution.marker"
    _poison_eligible_cached_bytecode(source_path, marker)

    module = tool._load_module_from_verified_bytes(
        "hashing", source_path, original_bytes, ("sha256_bytes", "canonical_json_bytes")
    )
    assert not marker.exists()
    assert module.__name__ == "_mes_governed_hashing"
    assert module.__file__ == str(source_path)
    assert module.sha256_bytes(b"MES") == hashlib.sha256(b"MES").hexdigest()

    # The full governed load is equally unaffected, and the path is not drifted.
    helpers = tool.load_governed_helpers(repo)
    assert not marker.exists()
    assert source_path.read_bytes() == original_bytes
    assert helpers.sha256_bytes(b"MES") == hashlib.sha256(b"MES").hexdigest()
    assert tool.build_binding_payload(repo, helpers)["governed_helper_bindings_ordered"][0][
        "path"
    ] == relative


def test_untracked_governed_helper_is_refused_before_load(
    tool, repo: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "hostile_untracked_helper.marker"
    path = repo / GOVERNED_RELATIVE_PATHS[2]
    payload = path.read_bytes() + _execution_marker_injection(marker)
    path.unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic helper removal")
    path.write_bytes(payload)

    with pytest.raises(tool.PreparationError) as raised:
        tool.load_governed_helpers(repo)

    assert raised.value.code == "GIT_REFERENCE_NONCONFORMING"
    assert not marker.exists()
    assert not any(name.startswith("_mes_governed_") for name in sys.modules)


# --------------------------------------------------------------------------
# Historical parent verification against local Git objects
# --------------------------------------------------------------------------


def _write_record_at(repo: Path, commit: str, rows: tuple[tuple[str, str, str], ...]) -> None:
    """Commit exactly one changed record that cites the given commit."""

    (repo / RECORD_RELATIVE_PATH).write_bytes(record_text(commit, rows).encode("utf-8"))
    entries = [entry for entry in _git(repo, "status", "--porcelain", "-z").split("\x00") if entry]
    assert len(entries) == 1
    assert entries[0].endswith(RECORD_RELATIVE_PATH)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic record variant")


def _rewrite_record(repo: Path, rows: tuple[tuple[str, str, str], ...]) -> None:
    _write_record_at(repo, _git(repo, "rev-parse", "HEAD~1"), rows)


def test_parent_record_and_blobs_verify(tool, repo: Path, helpers) -> None:
    commit = tool.resolve_head_commit(repo)
    objects = tool.list_commit_objects(helpers, repo, commit)
    _entry_found, record_bytes = tool.read_tracked_blob(
        helpers, repo, objects, RECORD_RELATIVE_PATH
    )
    record = tool.parse_ratification_record(record_bytes)
    bindings = tool.verify_historical_parents(helpers, repo, record)

    assert record.ratified_commit == _git(repo, "rev-parse", "HEAD~1")
    assert [binding["artifact_id"] for binding in bindings] == [PROTOCOL_ID, BUDGET_ID]
    for binding in bindings:
        assert binding["computed_sha256"] == binding["recorded_sha256"]
        assert binding["object_type"] == "blob"
        assert binding["verification"] == "EXACT_BLOB_BYTES_EQUAL_RECORDED_DIGEST"


def test_parent_blob_digest_mismatch_is_refused(tool, repo: Path, helpers) -> None:
    wrong_digest = hashlib.sha256(SYNTHETIC_PROTOCOL_BYTES + b"drift").hexdigest()
    _rewrite_record(
        repo,
        default_rows(wrong_digest, hashlib.sha256(SYNTHETIC_BUDGET_BYTES).hexdigest()),
    )
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_binding_payload(repo, helpers)
    assert raised.value.code == "PARENT_BLOB_NONCONFORMING"


def test_parent_path_absent_at_ratified_commit_is_refused(tool, repo: Path, helpers) -> None:
    """The cited commit itself must carry both parents, so cite a removal commit."""

    (repo / BUDGET_RELATIVE_PATH).unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic removal")
    removal_commit = _git(repo, "rev-parse", "HEAD")
    assert BUDGET_RELATIVE_PATH not in _git(
        repo, "ls-tree", "-r", "--name-only", removal_commit
    ).splitlines()

    _write_record_at(
        repo,
        removal_commit,
        default_rows(
            hashlib.sha256(SYNTHETIC_PROTOCOL_BYTES).hexdigest(),
            hashlib.sha256(SYNTHETIC_BUDGET_BYTES).hexdigest(),
        ),
    )
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_binding_payload(repo, helpers)
    assert raised.value.code == "GIT_REFERENCE_NONCONFORMING"


def test_symlinked_parent_object_is_refused(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required to build the synthetic repository")
    repo = build_synthetic_repository(tmp_path / "symlinked", budget_as_symlink=True)
    tool = load_tool(repo)
    helpers = tool.load_governed_helpers(repo)
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_binding_payload(repo, helpers)
    assert raised.value.code in {"GIT_REFERENCE_NONCONFORMING", "PARENT_BLOB_NONCONFORMING"}


# --------------------------------------------------------------------------
# Frozen contract self-consistency
# --------------------------------------------------------------------------


def _exact_contract_digest(payload) -> str:
    """Recompute the frozen digest from bytes with the module's exact semantics."""

    serialized = json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert not serialized.endswith(b"\n")
    return hashlib.sha256(serialized).hexdigest()


def test_contract_self_check_recomputes_the_frozen_digest_from_bytes(tool, helpers) -> None:
    payload = helpers.frozen_contract_payload()
    recomputed = _exact_contract_digest(payload)
    assert recomputed == helpers.frozen_contract_sha256()

    contract = tool.build_contract_self_check(helpers)
    assert contract["frozen_contract_recomputed_sha256"] == recomputed
    assert contract["frozen_contract_sha256"] == recomputed
    assert contract["frozen_contract_payload_exact_serialization"] == (
        "JSON_DUMPS_PLAIN_PAYLOAD_SORT_KEYS_COMMA_COLON_UTF8_NO_FINAL_LF"
    )
    assert contract["frozen_contract_payload_exact_byte_count"] == len(
        tool.test3_contract_canonical_bytes(payload)
    )
    assert contract["self_consistency"] == (
        "RECOMPUTED_PAYLOAD_DIGEST_EQUALS_FROZEN_CONTRACT_SHA256"
    )


def test_contract_self_check_passes_and_pins_the_fixture_spec(tool, helpers) -> None:
    contract = tool.build_contract_self_check(helpers)
    assert len(contract["frozen_contract_sha256"]) == 64
    assert len(contract["frozen_contract_payload_canonical_sha256"]) == 64
    parameters = contract["bootstrap_parameters"]
    spec = tool.fixture_spec_from_contract(parameters)
    assert spec.master_seed == parameters["master_seed"]
    assert spec.replications == parameters["bootstrap_repetitions"]
    assert list(spec.block_lengths) == parameters["bootstrap_blocks_ordered"]
    assert spec.session_count >= max(spec.block_lengths)


def _unstable_payload_helpers(tool, helpers):
    counter = itertools.count()

    def payload():
        return {
            "master_seed": 1,
            "bootstrap_repetitions": 2,
            "bootstrap_blocks": (5, 1, 20),
            "drift": next(counter),
        }

    return dataclasses.replace(helpers, frozen_contract_payload=payload)


def _unstable_digest_helpers(tool, helpers):
    counter = itertools.count()
    return dataclasses.replace(
        helpers, frozen_contract_sha256=lambda: f"{next(counter):064d}"
    )


def _malformed_digest_helpers(tool, helpers):
    return dataclasses.replace(helpers, frozen_contract_sha256=lambda: "not-a-digest")


def _self_consistent_helpers(helpers, payload):
    """Replace the payload and recompute its digest from bytes, so the pair agrees."""

    return dataclasses.replace(
        helpers,
        frozen_contract_payload=lambda: payload,
        frozen_contract_sha256=lambda: _exact_contract_digest(payload),
    )


def _wrong_but_well_formed_digest_helpers(tool, helpers):
    """A stable, well-formed, machine-computed digest that is not the real one."""

    payload = helpers.frozen_contract_payload()
    wrong = hashlib.sha256(b"MES_SYNTHETIC_WRONG_BUT_WELL_FORMED_CONTRACT_DIGEST").hexdigest()
    assert len(wrong) == 64
    assert wrong != _exact_contract_digest(payload)
    return dataclasses.replace(helpers, frozen_contract_sha256=lambda: wrong)


def _missing_parameter_helpers(tool, helpers):
    return _self_consistent_helpers(
        helpers, {"bootstrap_repetitions": 2, "bootstrap_blocks": [5]}
    )


def _invalid_blocks_helpers(tool, helpers):
    return _self_consistent_helpers(
        helpers,
        {"master_seed": 1, "bootstrap_repetitions": 2, "bootstrap_blocks": [5, 0]},
    )


def _unsupported_member_helpers(tool, helpers):
    return dataclasses.replace(
        helpers, frozen_contract_payload=lambda: {"master_seed": object()}
    )


@pytest.mark.parametrize(
    "build_helpers",
    [
        pytest.param(_unstable_payload_helpers, id="nondeterministic_payload"),
        pytest.param(_unstable_digest_helpers, id="nondeterministic_digest"),
        pytest.param(_malformed_digest_helpers, id="malformed_digest"),
        pytest.param(
            _wrong_but_well_formed_digest_helpers, id="stable_wrong_well_formed_digest"
        ),
        pytest.param(_missing_parameter_helpers, id="missing_master_seed"),
        pytest.param(_invalid_blocks_helpers, id="invalid_block_length"),
        pytest.param(_unsupported_member_helpers, id="unsupported_payload_member"),
    ],
)
def test_contract_self_check_rejects_mismatch(tool, helpers, build_helpers) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_contract_self_check(build_helpers(tool, helpers))
    assert raised.value.code == "CONTRACT_SELF_CHECK_NONCONFORMING"


# --------------------------------------------------------------------------
# Runtime identity
# --------------------------------------------------------------------------


def test_runtime_identity_is_complete_and_equal_on_re_record(tool, helpers) -> None:
    binding = tool.build_runtime_identity_binding(helpers)
    assert binding["equality"] == "CREATE_TIME_RECORD_AND_IMMEDIATE_RE_RECORD_EXACTLY_EQUAL"
    assert len(binding["identity_sha256"]) == 64
    first = tool.build_runtime_identity()
    second = tool.build_runtime_identity()
    assert helpers.canonical_json_bytes(first) == helpers.canonical_json_bytes(second)


def test_runtime_identity_records_the_actual_python_executable(tool, helpers) -> None:
    resolved = Path(sys.executable).resolve(strict=True)
    identity = tool.build_runtime_identity()
    python_section = identity["python"]

    assert python_section["executable"] == sys.executable
    assert Path(python_section["executable"]).is_absolute()
    assert python_section["executable_resolved"] == str(resolved)
    assert resolved.is_absolute()
    assert resolved.is_file()
    assert tool.build_python_executable_identity() == {
        "executable": sys.executable,
        "executable_resolved": str(resolved),
    }

    tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    tool.require_python_executable_identity(python_section)
    assert tool.build_runtime_identity()["python"] == python_section


def test_declared_runtime_identity_shape_covers_every_recorded_field(tool, helpers) -> None:
    identity = tool.build_runtime_identity()
    declared = dict(tool.REQUIRED_RUNTIME_IDENTITY_SHAPE)

    assert set(identity) == set(declared)
    for group, fields in declared.items():
        assert len(set(fields)) == len(fields)
        assert set(identity[group]) == set(fields)
    assert {"executable", "executable_resolved", "hexversion", "maxsize", "float_repr_style"} <= (
        set(declared["python"])
    )
    assert "processor" in declared["platform"]
    assert "byteorder" in declared["float64"]
    tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)


def test_runtime_identity_permits_an_empty_platform_processor(tool, helpers) -> None:
    """Some platforms supply no processor text; inventing one would be a false identity."""

    assert tool.RUNTIME_IDENTITY_EMPTY_TEXT_ALLOWED == frozenset({("platform", "processor")})
    identity = tool.build_runtime_identity()
    identity["platform"]["processor"] = ""
    tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda identity: identity["python"].pop("executable"), id="missing_executable"
        ),
        pytest.param(
            lambda identity: identity["python"].pop("executable_resolved"),
            id="missing_resolved_executable",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"executable": "python3"}),
            id="relative_executable",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"executable": ""}),
            id="empty_executable",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"executable": 3}),
            id="type_wrong_executable",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"executable_resolved": None}),
            id="type_wrong_resolved_executable",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"undeclared": "x"}),
            id="undeclared_python_field",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"maxsize": "many"}),
            id="type_wrong_maxsize",
        ),
        pytest.param(
            lambda identity: identity["python"].update({"hexversion": True}),
            id="boolean_hexversion",
        ),
        pytest.param(
            lambda identity: identity["platform"].update({"machine": ""}),
            id="empty_platform_machine",
        ),
        pytest.param(
            lambda identity: identity["platform"].update({"processor": None}),
            id="type_wrong_processor",
        ),
        pytest.param(
            lambda identity: identity["platform"].update({"libc": "glibc"}),
            id="type_wrong_libc",
        ),
        pytest.param(
            lambda identity: identity["float64"].update({"byteorder": ""}),
            id="empty_float64_byteorder",
        ),
        pytest.param(
            lambda identity: identity.update({"undeclared_group": {"a": 1}}),
            id="undeclared_group",
        ),
    ],
)
def test_require_complete_runtime_identity_rejects_identity_defects(
    tool, helpers, mutate
) -> None:
    identity = tool.build_runtime_identity()
    mutate(identity)
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_rejects_a_nonexistent_resolved_executable(
    tool, helpers, tmp_path: Path
) -> None:
    identity = tool.build_runtime_identity()
    identity["python"]["executable_resolved"] = str((tmp_path / "absent-python").resolve())
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_rejects_a_nonregular_resolved_executable(
    tool, helpers, tmp_path: Path
) -> None:
    identity = tool.build_runtime_identity()
    identity["python"]["executable_resolved"] = str(tmp_path.resolve())
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_rejects_a_drifted_resolved_executable(
    tool, helpers, tmp_path: Path
) -> None:
    """A real regular file that is not this interpreter is still refused."""

    other = tmp_path / "other-python"
    other.write_bytes(b"#!/bin/sh\nexit 0\n")
    other.chmod(0o755)
    identity = tool.build_runtime_identity()
    identity["python"]["executable_resolved"] = str(other.resolve())
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_executable_drift_between_records_is_refused(
    tool, helpers, monkeypatch
) -> None:
    counter = itertools.count()
    original = tool.build_runtime_identity

    def drifting():
        identity = original()
        identity["python"]["executable"] = f"{identity['python']['executable']}.{next(counter)}"
        return identity

    monkeypatch.setattr(tool, "build_runtime_identity", drifting)
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_runtime_identity_binding(helpers)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_float_info_uses_an_explicit_ordered_field_map(tool) -> None:
    recorded = tool.build_float_info_map()
    assert set(recorded) == set(tool.REQUIRED_FLOAT_INFO_KEYS)
    assert set(recorded) == {
        *(f"{name}_hex" for name in tool.FLOAT_INFO_FLOAT_FIELDS_ORDERED),
        *tool.FLOAT_INFO_INT_FIELDS_ORDERED,
    }
    for name in tool.FLOAT_INFO_FLOAT_FIELDS_ORDERED:
        assert float.fromhex(recorded[f"{name}_hex"]) == getattr(sys.float_info, name)
    for name in tool.FLOAT_INFO_INT_FIELDS_ORDERED:
        assert recorded[name] == getattr(sys.float_info, name)
    assert tool.build_runtime_identity()["python"]["float_info"] == recorded
    tool.require_complete_float_info(recorded)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda info: info.pop("radix"), id="missing_int_field"),
        pytest.param(lambda info: info.pop("epsilon_hex"), id="missing_hex_field"),
        pytest.param(lambda info: info.update({"extra": 1}), id="extra_field"),
        pytest.param(lambda info: info.update({"epsilon_hex": ""}), id="empty_hex_field"),
        pytest.param(
            lambda info: info.update({"max_hex": "not-a-float-hex"}), id="malformed_hex_field"
        ),
        pytest.param(lambda info: info.update({"radix": "2"}), id="non_integer_field"),
        pytest.param(lambda info: info.update({"rounds": True}), id="boolean_field"),
    ],
)
def test_require_complete_float_info_rejects(tool, mutate) -> None:
    recorded = tool.build_float_info_map()
    mutate(recorded)
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_float_info(recorded)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


def test_runtime_identity_mismatch_is_refused(tool, helpers, monkeypatch) -> None:
    counter = itertools.count()
    original = tool.build_runtime_identity

    def drifting():
        identity = original()
        identity["platform"]["release"] = f"{identity['platform']['release']}-{next(counter)}"
        return identity

    monkeypatch.setattr(tool, "build_runtime_identity", drifting)
    with pytest.raises(tool.PreparationError) as raised:
        tool.build_runtime_identity_binding(helpers)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda identity: identity.pop("rng"), id="missing_rng_group"),
        pytest.param(lambda identity: identity["python"].pop("version"), id="missing_python_field"),
        pytest.param(
            lambda identity: identity["python"].update({"float_info": {}}),
            id="empty_float_info",
        ),
        pytest.param(
            lambda identity: identity["python"]["float_info"].pop("radix"),
            id="incomplete_float_info",
        ),
        pytest.param(
            lambda identity: identity["float64"].update({"eps_hex": ""}), id="empty_float64_field"
        ),
        pytest.param(
            lambda identity: identity["numpy"].update({"build_config": {"only": "cpu"}}),
            id="missing_blas_lapack_identity",
        ),
    ],
)
def test_require_complete_runtime_identity_rejects(tool, helpers, mutate) -> None:
    identity = tool.build_runtime_identity()
    mutate(identity)
    with pytest.raises(tool.PreparationError) as raised:
        tool.require_complete_runtime_identity(identity, helpers.canonical_json_bytes)
    assert raised.value.code == "RUNTIME_IDENTITY_NONCONFORMING"


# --------------------------------------------------------------------------
# Deterministic synthetic golden fixture
# --------------------------------------------------------------------------


def small_spec(tool, **overrides):
    defaults = {
        "session_count": 25,
        "master_seed": 101,
        "replications": 6,
        "block_lengths": (5, 1, 20),
    }
    defaults.update(overrides)
    return tool.GoldenFixtureSpec(**defaults)


def test_golden_fixture_is_deterministic_and_replays_bytewise(tool, helpers) -> None:
    spec = small_spec(tool)
    first_record, first_raw = tool.generate_golden_fixture(spec, helpers)
    second_record, second_raw = tool.generate_golden_fixture(spec, helpers)
    assert first_raw == second_raw
    assert helpers.canonical_json_bytes(first_record) == helpers.canonical_json_bytes(
        second_record
    )

    verified = tool.verify_golden_fixture_replay(spec, helpers)
    assert verified["replay"] == "EXACT_BYTEWISE_REPLAY_VERIFIED"
    assert verified["storage"] == tool.FIXTURE_STORAGE == FIXTURE_STORAGE_LITERAL
    assert [block["block_length"] for block in verified["blocks_ordered"]] == [5, 1, 20]
    for block in verified["blocks_ordered"]:
        assert block["validation_seed"] == spec.master_seed + 90000 + block["block_length"] + 1000


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"master_seed": 102}, id="altered_seed"),
        pytest.param({"session_count": 26}, id="altered_session_count"),
        pytest.param({"replications": 7}, id="altered_replications"),
    ],
)
def test_golden_fixture_changes_when_inputs_change(tool, helpers, overrides) -> None:
    baseline, _raw = tool.generate_golden_fixture(small_spec(tool), helpers)
    altered, _altered_raw = tool.generate_golden_fixture(small_spec(tool, **overrides), helpers)
    assert baseline["raw_material_sha256"] != altered["raw_material_sha256"]


def test_altered_replay_is_refused(tool, helpers, monkeypatch) -> None:
    counter = itertools.count()
    original = tool.synthetic_inputs

    def drifting(spec):
        counts, actual, base, har = original(spec)
        if next(counter) > 0:
            actual = numpy.ascontiguousarray(actual + numpy.float64(0.5))
        return counts, actual, base, har

    monkeypatch.setattr(tool, "synthetic_inputs", drifting)
    with pytest.raises(tool.PreparationError) as raised:
        tool.verify_golden_fixture_replay(small_spec(tool), helpers)
    assert raised.value.code == "GOLDEN_FIXTURE_NONCONFORMING"


def test_fixture_spec_requires_enough_sessions(tool) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool._draw_matrix(small_spec(tool, session_count=3), 20)
    assert raised.value.code == "GOLDEN_FIXTURE_NONCONFORMING"


# --------------------------------------------------------------------------
# Tripwires
# --------------------------------------------------------------------------


def test_network_tripwire_blocks_then_restores(tool) -> None:
    import socket

    original = socket.socket
    with tool.governed_runtime_tripwires():
        with pytest.raises(tool.PreparationError) as raised:
            socket.socket()
        assert raised.value.code == "NETWORK_ACCESS_BLOCKED"
        with pytest.raises(tool.PreparationError):
            socket.getaddrinfo("localhost", 80)
    assert socket.socket is original


@pytest.mark.parametrize(
    "fullname",
    [
        "requests",
        "urllib.request",
        "http.client",
        "pandas",
        "boto3",
        "databento",
        "mes_quant",
        "mes_quant.exploration.sprint1",
        "mes_quant.exploration.test3_contract",
    ],
)
def test_forbidden_import_tripwire_blocks(tool, fullname: str) -> None:
    guard = tool.ForbiddenImportGuard()
    assert guard.is_forbidden(fullname) is True
    with pytest.raises(tool.PreparationError) as raised:
        guard.find_spec(fullname)
    assert raised.value.code == "FORBIDDEN_IMPORT_BLOCKED"


@pytest.mark.parametrize("fullname", ["json", "pathlib", "numpy", "_mes_governed_hashing"])
def test_forbidden_import_tripwire_allows_closed_surface(tool, fullname: str) -> None:
    guard = tool.ForbiddenImportGuard()
    assert guard.is_forbidden(fullname) is False
    assert guard.find_spec(fullname) is None


# --------------------------------------------------------------------------
# Output-path discipline
# --------------------------------------------------------------------------


def test_resolve_output_path_accepts_only_the_exact_binding_path(tool, repo: Path) -> None:
    resolved = tool.resolve_output_path(repo, OUTPUT_RELATIVE_PATH)
    assert resolved.relative_path == OUTPUT_RELATIVE_PATH
    assert resolved.path == repo / OUTPUT_RELATIVE_PATH
    assert resolved.parent_parts == ("docs", "research")
    assert resolved.name == Path(OUTPUT_RELATIVE_PATH).name


@pytest.mark.parametrize("raw", REJECTED_OUTPUT_VALUES)
def test_resolve_output_path_rejects_every_alternative(tool, repo: Path, raw: str) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.resolve_output_path(repo, raw)
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"


def test_resolve_output_path_rejects_the_absolute_form(tool, repo: Path) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.resolve_output_path(repo, str(repo / OUTPUT_RELATIVE_PATH))
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"


@pytest.mark.parametrize("mode", ["check", "create", "verify-existing"])
def test_every_mode_refuses_a_fourth_repository_path(tool, repo: Path, capsys, mode: str) -> None:
    before = visible_files(repo)
    for raw in REJECTED_OUTPUT_VALUES:
        assert tool.main([mode, "--output", raw]) == 2
        captured = capsys.readouterr()
        assert "OUTPUT_PATH_NONCONFORMING" in captured.err
        assert captured.out == ""
    assert visible_files(repo) == before


def test_absent_output_parent_is_refused(tool, repo: Path) -> None:
    shutil.rmtree(repo / "docs" / "research")
    with pytest.raises(tool.PreparationError) as raised:
        tool.resolve_output_path(repo, OUTPUT_RELATIVE_PATH)
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"


def test_symlinked_output_parent_is_refused(tool, repo: Path) -> None:
    outside = repo.parent / "outside"
    outside.mkdir()
    shutil.rmtree(repo / "docs" / "research")
    (repo / "docs" / "research").symlink_to(outside, target_is_directory=True)
    with pytest.raises(tool.PreparationError) as raised:
        tool.resolve_output_path(repo, OUTPUT_RELATIVE_PATH)
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"
    assert list(outside.iterdir()) == []


def test_existing_output_symlink_is_refused(tool, repo: Path) -> None:
    elsewhere = repo / "docs" / "research" / "elsewhere.json"
    elsewhere.write_text("{}\n")
    link = repo / OUTPUT_RELATIVE_PATH
    link.symlink_to(elsewhere.name)
    with pytest.raises(tool.PreparationError) as raised:
        tool.resolve_output_path(repo, OUTPUT_RELATIVE_PATH)
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"


def test_output_parent_swapped_to_a_symlink_writes_nothing_outside(tool, repo: Path) -> None:
    """Adversarial parent swap after resolution must not write outside the repository."""

    outside = repo.parent / "outside"
    outside.mkdir()
    target = target_for(tool, repo)
    assert target.path == repo / OUTPUT_RELATIVE_PATH

    shutil.rmtree(repo / "docs" / "research")
    (repo / "docs" / "research").symlink_to(outside, target_is_directory=True)

    with pytest.raises(tool.PreparationError) as raised:
        tool.write_exclusive(target, b'{"synthetic":true}\n')
    assert raised.value.code == "OUTPUT_PATH_NONCONFORMING"
    assert list(outside.iterdir()) == []
    assert not (outside / Path(OUTPUT_RELATIVE_PATH).name).exists()


def test_output_parent_swapped_to_a_fresh_directory_stays_inside(tool, repo: Path) -> None:
    """A swapped real parent is still reached from the repository descriptor root."""

    outside = repo.parent / "outside"
    outside.mkdir()
    target = target_for(tool, repo)
    shutil.rmtree(repo / "docs" / "research")
    (repo / "docs" / "research").mkdir()

    tool.write_exclusive(target, b'{"synthetic":true}\n')

    assert (repo / OUTPUT_RELATIVE_PATH).read_bytes() == b'{"synthetic":true}\n'
    assert list(outside.iterdir()) == []
    with pytest.raises(tool.PreparationError) as raised:
        tool.write_exclusive(target, b'{"synthetic":true}\n')
    assert raised.value.code == "OUTPUT_EXISTS"


# --------------------------------------------------------------------------
# Mode behaviour
# --------------------------------------------------------------------------


def test_check_verifies_without_writing_anything(tool, repo: Path, capsys) -> None:
    before = visible_files(repo)
    assert tool.main(["check", "--output", OUTPUT_RELATIVE_PATH]) == 0
    captured = capsys.readouterr()
    assert "CHECK_PASS" in captured.out
    assert tool.CLASSIFICATION in captured.out
    assert captured.err == ""
    assert visible_files(repo) == before
    assert not (repo / OUTPUT_RELATIVE_PATH).exists()


def test_create_is_exclusive_and_verify_existing_is_read_only(tool, repo: Path, capsys) -> None:
    output = repo / OUTPUT_RELATIVE_PATH
    before = visible_files(repo)

    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 0
    assert "CREATE_PASS" in capsys.readouterr().out
    created_bytes = output.read_bytes()
    assert visible_files(repo) - before == {OUTPUT_RELATIVE_PATH}

    assert tool.main(["verify-existing", "--output", OUTPUT_RELATIVE_PATH]) == 0
    assert "VERIFY_EXISTING_PASS" in capsys.readouterr().out
    assert output.read_bytes() == created_bytes
    assert visible_files(repo) - before == {OUTPUT_RELATIVE_PATH}

    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 2
    assert "OUTPUT_EXISTS" in capsys.readouterr().err
    assert output.read_bytes() == created_bytes

    assert tool.main(["check", "--output", OUTPUT_RELATIVE_PATH]) == 2
    assert "OUTPUT_EXISTS" in capsys.readouterr().err
    assert output.read_bytes() == created_bytes


def test_created_binding_is_canonical_and_self_describing(tool, repo: Path, helpers) -> None:
    output = repo / OUTPUT_RELATIVE_PATH
    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 0

    content = output.read_bytes()
    document = json.loads(content)
    assert helpers.canonical_json_bytes(document) == content
    assert set(document) == {"schema", "payload", "payload_sha256"}
    payload = document["payload"]
    assert payload["classification"] == tool.CLASSIFICATION
    assert payload["data_policy"] == tool.DATA_POLICY
    assert payload["network_policy"] == tool.NETWORK_POLICY
    assert payload["modes_closed_ordered"] == list(tool.MODES)
    assert payload["golden_fixture"]["storage"] == tool.FIXTURE_STORAGE
    assert payload["golden_fixture"]["replay"] == "EXACT_BYTEWISE_REPLAY_VERIFIED"
    assert payload["repository_binding"]["base_commit"] == tool.resolve_head_commit(repo)
    assert [
        binding["path"] for binding in payload["governed_helper_bindings_ordered"]
    ] == list(GOVERNED_RELATIVE_PATHS)
    assert payload["tool_binding"]["path"] == TOOL_RELATIVE_PATH
    assert payload["tests_binding"]["path"] == TESTS_RELATIVE_PATH
    assert [
        binding["pre_exec_verification"]
        for binding in payload["governed_helper_bindings_ordered"]
    ] == ["WORKTREE_BYTES_EQUAL_TRACKED_HEAD_BLOB_BEFORE_ANY_HELPER_EXECUTION"] * 3
    contract = payload["test3_contract_self_check"]
    assert contract["frozen_contract_recomputed_sha256"] == contract["frozen_contract_sha256"]
    assert contract["frozen_contract_sha256"] == _exact_contract_digest(
        helpers.frozen_contract_payload()
    )


def test_created_binding_never_publishes_governed_helper_source_bytes(
    tool, repo: Path
) -> None:
    """Path 3 carries helper identities and digests only, never raw source bytes."""

    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 0
    content = (repo / OUTPUT_RELATIVE_PATH).read_bytes()
    document = json.loads(content)

    for relative in GOVERNED_RELATIVE_PATHS:
        assert (repo / relative).read_bytes()[:80] not in content
    for binding in document["payload"]["governed_helper_bindings_ordered"]:
        assert set(binding) == {
            "path",
            "sha256",
            "byte_count",
            "git_state",
            "blob_sha1",
            "alias",
            "allowed_symbols_ordered",
            "pre_exec_verification",
        }
    assert "source_bytes" not in json.dumps(document)


def test_created_binding_records_the_runtime_executable_identity(tool, repo: Path) -> None:
    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 0
    document = json.loads((repo / OUTPUT_RELATIVE_PATH).read_bytes())
    python_section = document["payload"]["runtime_identity_binding"]["identity"]["python"]
    assert python_section["executable"] == sys.executable
    assert python_section["executable_resolved"] == str(Path(sys.executable).resolve(strict=True))
    assert document["payload"]["runtime_identity_binding"]["equality"] == (
        "CREATE_TIME_RECORD_AND_IMMEDIATE_RE_RECORD_EXACTLY_EQUAL"
    )


def test_verify_existing_detects_a_recomputation_mismatch(tool, repo: Path, helpers) -> None:
    output = repo / OUTPUT_RELATIVE_PATH
    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 0

    document = json.loads(output.read_bytes())
    document["payload"]["golden_fixture"]["row_count"] += 1
    document["payload_sha256"] = helpers.sha256_bytes(
        helpers.canonical_json_bytes(document["payload"])
    )
    output.write_bytes(helpers.canonical_json_bytes(document))

    with pytest.raises(tool.PreparationError) as raised:
        tool.run_verify_existing(repo, target_for(tool, repo), helpers)
    assert raised.value.code == "BINDING_MISMATCH"


def _stub_document(tool, helpers) -> dict:
    payload = {"schema": tool.SCHEMA, "classification": tool.CLASSIFICATION}
    return {
        "schema": tool.SCHEMA,
        "payload": payload,
        "payload_sha256": helpers.sha256_bytes(helpers.canonical_json_bytes(payload)),
    }


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            lambda tool, helpers, document: helpers.canonical_json_bytes(document).replace(
                b'"payload_sha256":"', b'"payload_sha256":"0'
            ),
            "BINDING_MISMATCH",
            id="digest_tamper",
        ),
        pytest.param(
            lambda tool, helpers, document: json.dumps(document, indent=2).encode("utf-8"),
            "BINDING_NONCANONICAL",
            id="noncanonical_bytes",
        ),
        pytest.param(
            lambda tool, helpers, document: b"{ not json",
            "BINDING_NONCANONICAL",
            id="not_json",
        ),
        pytest.param(
            lambda tool, helpers, document: helpers.canonical_json_bytes(
                {**document, "extra": 1}
            ),
            "BINDING_NONCANONICAL",
            id="unexpected_structure",
        ),
        pytest.param(
            lambda tool, helpers, document: helpers.canonical_json_bytes(
                {**document, "schema": "OTHER"}
            ),
            "BINDING_MISMATCH",
            id="schema_tamper",
        ),
        pytest.param(
            lambda tool, helpers, document: _reclassified(tool, helpers, document),
            "BINDING_MISMATCH",
            id="classification_tamper",
        ),
    ],
)
def test_verify_existing_structural_failures(tool, repo: Path, helpers, mutate, expected) -> None:
    output = repo / OUTPUT_RELATIVE_PATH
    output.write_bytes(mutate(tool, helpers, _stub_document(tool, helpers)))
    with pytest.raises(tool.PreparationError) as raised:
        tool.run_verify_existing(repo, target_for(tool, repo), helpers)
    assert raised.value.code == expected


def _reclassified(tool, helpers, document) -> bytes:
    payload = {**document["payload"], "classification": "NOT_THE_AUTHORIZED_CLASSIFICATION"}
    return helpers.canonical_json_bytes(
        {
            "schema": tool.SCHEMA,
            "payload": payload,
            "payload_sha256": helpers.sha256_bytes(helpers.canonical_json_bytes(payload)),
        }
    )


def test_verify_existing_requires_the_artifact(tool, repo: Path, helpers) -> None:
    with pytest.raises(tool.PreparationError) as raised:
        tool.run_verify_existing(repo, target_for(tool, repo), helpers)
    assert raised.value.code == "OUTPUT_MISSING"


# --------------------------------------------------------------------------
# Stable governed error surface
# --------------------------------------------------------------------------


def _network_offender():
    import socket

    socket.create_connection(("localhost", 9))
    raise AssertionError("the network tripwire must refuse before any connection")


def _forbidden_import_offender():
    importlib.import_module("databento")
    raise AssertionError("the import tripwire must refuse before any resolution")


@pytest.mark.parametrize(
    ("offender", "expected"),
    [
        pytest.param(_network_offender, "NETWORK_ACCESS_BLOCKED", id="network"),
        pytest.param(
            _forbidden_import_offender, "FORBIDDEN_IMPORT_BLOCKED", id="forbidden_import"
        ),
    ],
)
def test_main_tripwires_stop_a_governed_operation_and_create_no_output(
    tool, repo: Path, capsys, monkeypatch, offender, expected
) -> None:
    """An attempted network or forbidden import inside a governed operation stops."""

    assert "databento" not in sys.modules
    before = visible_files(repo)
    monkeypatch.setattr(tool, "build_runtime_identity", offender)

    assert tool.main(["create", "--output", OUTPUT_RELATIVE_PATH]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert len(captured.err.strip().splitlines()) == 1
    assert expected in captured.err
    assert visible_files(repo) == before
    assert not (repo / OUTPUT_RELATIVE_PATH).exists()
    assert "databento" not in sys.modules


def test_main_reports_one_stable_line_without_a_traceback(tool, repo: Path, capsys) -> None:
    (repo / GOVERNED_RELATIVE_PATHS[0]).unlink()
    assert tool.main(["check", "--output", OUTPUT_RELATIVE_PATH]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert len(captured.err.strip().splitlines()) == 1
    assert "IMPORT_PROVENANCE_NONCONFORMING" in captured.err
    assert not (repo / OUTPUT_RELATIVE_PATH).exists()


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        pytest.param(["rehearse", "--output", "docs/research/x.json"], "ARGUMENTS_NONCONFORMING"),
        pytest.param(["check", "--output", "../escape.json"], "OUTPUT_PATH_NONCONFORMING"),
    ],
)
def test_main_maps_failures_to_stable_codes(tool, repo: Path, capsys, argv, expected) -> None:
    before = visible_files(repo)
    assert tool.main(argv) == 2
    captured = capsys.readouterr()
    assert expected in captured.err
    assert "Traceback" not in captured.err
    assert visible_files(repo) == before


def test_error_codes_are_declared_and_unique(tool) -> None:
    assert len(set(tool.ERROR_CODES)) == len(tool.ERROR_CODES)
    assert list(tool.ERROR_CODES) == sorted(tool.ERROR_CODES)

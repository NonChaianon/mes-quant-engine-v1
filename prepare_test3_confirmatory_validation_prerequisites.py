"""Prepare and bind the Test 3 confirmatory-validation tooling prerequisites.

Classification:
``TOOLING_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION / NOT_ACTIVATION``

This tool is local-only, data-free and no-network. It performs, in order:

1. closed-argument parsing of the three ordered modes ``check``, ``create`` and
   ``verify-existing``;
2. governed-helper import provenance closure (repository ``src`` root forced to
   the front, ambient editable/site-package origins rejected, module origins
   proven equal to the exact three allowed paths, and, before any governed
   helper byte is executed, an independent standard-library-plus-local-Git
   proof that each allowed path is a regular tracked blob at the
   machine-resolved current ``HEAD`` whose worktree bytes equal that blob);
   the verified byte sequences are retained in memory and are the only bytes
   compiled and executed, so no helper source path is reopened for execution
   and no cached bytecode can substitute unverified module-level code;
3. local Git-object verification of the Owner co-ratification record and of the
   two required parent protocol/budget blobs at the commit parsed from that
   record;
4. the mandatory supplementary Test 3 frozen-contract payload/digest
   self-consistency check;
5. complete runtime-identity generation with immediate re-record equality;
6. deterministic in-memory synthetic golden-fixture generation with exact
   bytewise replay; and
7. descriptor-rooted, no-symlink resolution of the one exact authorized output
   relative path, followed by exclusive no-overwrite creation, or read-only
   verification, of that single binding artifact.

It never accesses data, providers, targets or evidence, never imports a real
scientific runner, never stages/commits/pushes, never overwrites its output and
never creates any auxiliary artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import stat
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import util as importlib_util
from importlib.machinery import PathFinder
from pathlib import Path
from typing import Any

import numpy

# --------------------------------------------------------------------------
# Frozen tooling constants
# --------------------------------------------------------------------------

TOOL_NAME = "prepare_test3_confirmatory_validation_prerequisites"
SCHEMA = "MES_TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1"
CLASSIFICATION = (
    "TOOLING_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION / NOT_ACTIVATION"
)
DATA_POLICY = "DATA_FREE_NO_PROVIDER_TARGET_EVIDENCE_ACCESS"
NETWORK_POLICY = "LOCAL_ONLY_NO_NETWORK"
FIXTURE_STORAGE = "IN_MEMORY_AND_INSIDE_PATH3_ONLY"

MODES: tuple[str, ...] = ("check", "create", "verify-existing")
OUTPUT_FLAG = "--output"

TOOL_RELATIVE_PATH = "tools/prepare_test3_confirmatory_validation_prerequisites.py"
TESTS_RELATIVE_PATH = "tests/test_prepare_test3_confirmatory_validation_prerequisites.py"
BINDING_RELATIVE_PATH = "docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json"
AUTHORIZED_TOOLING_PATHS: tuple[str, ...] = (
    TOOL_RELATIVE_PATH,
    TESTS_RELATIVE_PATH,
    BINDING_RELATIVE_PATH,
)

SRC_RELATIVE_ROOT = "src"
PACKAGE_ROOT_NAME = "mes_quant"

GOVERNED_MODULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "hashing",
        "src/mes_quant/core/hashing.py",
        ("sha256_bytes", "canonical_json_bytes"),
    ),
    (
        "reference_objects",
        "src/mes_quant/governance/classification/reference_objects.py",
        ("list_tracked_objects", "read_blob_bytes"),
    ),
    (
        "test3_contract",
        "src/mes_quant/exploration/test3_contract.py",
        ("frozen_contract_payload", "frozen_contract_sha256"),
    ),
)

RATIFICATION_RECORD_RELATIVE_PATH = (
    "docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md"
)
REQUIRED_PARENT_ARTIFACTS: tuple[tuple[str, str], ...] = (
    (
        "MES_TEST3_RV60_HAR_RISK_EDGE_V1",
        "docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md",
    ),
    (
        "MES_PROJECT_TARGET_SPACE_BUDGET_V1",
        "docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md",
    ),
)

MAX_TRACKED_OBJECTS = 100_000
MAX_BLOB_BYTES = 8 * 1024 * 1024
REGULAR_FILE_MODES = frozenset({"100644", "100755"})

FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "boto3",
        "botocore",
        "databento",
        "ftplib",
        "http",
        "httpx",
        "pandas",
        "requests",
        "scipy",
        "sklearn",
        "smtplib",
        "socketserver",
        "statsmodels",
        "telnetlib",
        "urllib",
        "urllib3",
        "xmlrpc",
    }
)

SYNTHETIC_SESSION_COUNT = 24

_HEX40_RE = re.compile(r"[0-9a-f]{40}")
_HEX40_BYTES_RE = re.compile(rb"[0-9a-f]{40}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_RATIFIED_COMMIT_RE = re.compile(r"Ratified commit: `([0-9a-f]{40})`")
_TABLE_HEADER_RE = re.compile(r"\| Identity \| Path \| SHA-256[^|]*\|")
_TABLE_SEPARATOR_RE = re.compile(r"\|(?: -+ \|)+")
_TABLE_ROW_RE = re.compile(r"\| `([^`|]+)` \| `([^`|]+)` \| `([0-9a-f]{64})` \|")
_SECTION_ONE_RE = re.compile(r"## 1\. .*")

# ``sys.float_info`` is a structseq, so it carries no supported ``_asdict``
# contract. The two ordered maps below are the explicit, closed field list that
# is recorded and validated instead.
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

_DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)
_FILE_CREATE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)
_FILE_READ_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
_OUTPUT_MODE = 0o644
MAX_BINDING_BYTES = MAX_BLOB_BYTES

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

PYTHON_EXECUTABLE_FIELD = "executable"
PYTHON_EXECUTABLE_RESOLVED_FIELD = "executable_resolved"

# The declared shape is the closed contract for the recorded identity: it names
# every group and every field the recorder actually writes, so a recorded field
# can never escape validation and an undeclared field can never be accepted.
REQUIRED_RUNTIME_IDENTITY_SHAPE: tuple[tuple[str, tuple[str, ...]], ...] = (
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
            PYTHON_EXECUTABLE_FIELD,
            PYTHON_EXECUTABLE_RESOLVED_FIELD,
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

# Exactly one recorded text field may legitimately be empty: some platforms
# supply no processor string at all, and inventing one would be a false
# identity. Every other declared text field must be nonempty.
RUNTIME_IDENTITY_EMPTY_TEXT_ALLOWED: frozenset[tuple[str, str]] = frozenset(
    {("platform", "processor")}
)

RUNTIME_IDENTITY_TEXT_FIELDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("python", "implementation"),
        ("python", "version"),
        ("python", "version_full"),
        ("python", "cache_tag"),
        ("python", "float_repr_style"),
        ("python", PYTHON_EXECUTABLE_FIELD),
        ("python", PYTHON_EXECUTABLE_RESOLVED_FIELD),
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


# --------------------------------------------------------------------------
# Stable governed error surface
# --------------------------------------------------------------------------


class PreparationError(RuntimeError):
    """Single governed failure type carrying one stable machine code."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


ERROR_CODES: tuple[str, ...] = (
    "ARGUMENTS_NONCONFORMING",
    "BINDING_MISMATCH",
    "BINDING_NONCANONICAL",
    "CONTRACT_SELF_CHECK_NONCONFORMING",
    "FORBIDDEN_IMPORT_BLOCKED",
    "GIT_REFERENCE_NONCONFORMING",
    "GOLDEN_FIXTURE_NONCONFORMING",
    "GOVERNED_HELPER_BYTES_DRIFT",
    "IMPORT_PROVENANCE_NONCONFORMING",
    "INTERNAL_NONCONFORMANCE",
    "NETWORK_ACCESS_BLOCKED",
    "OUTPUT_EXISTS",
    "OUTPUT_MISSING",
    "OUTPUT_PATH_NONCONFORMING",
    "PARENT_BLOB_NONCONFORMING",
    "RATIFICATION_RECORD_NONCONFORMING",
    "RUNTIME_IDENTITY_NONCONFORMING",
)


def _guarded(code: str, detail: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run one governed call and convert any foreign exception into a stable code."""

    try:
        return func(*args, **kwargs)
    except PreparationError:
        raise
    except Exception as exc:  # stable governed surface, never a raw traceback  # noqa: BLE001
        raise PreparationError(code, f"{detail}: {type(exc).__name__}") from None


# --------------------------------------------------------------------------
# Network and forbidden-import tripwires
# --------------------------------------------------------------------------

_BLOCKED_SOCKET_ATTRIBUTES = (
    "socket",
    "socketpair",
    "create_connection",
    "create_server",
    "getaddrinfo",
    "gethostbyname",
)


class ForbiddenImportGuard:
    """Meta-path guard that refuses network, data and scientific-runner imports."""

    @staticmethod
    def is_forbidden(fullname: str) -> bool:
        if fullname == PACKAGE_ROOT_NAME or fullname.startswith(PACKAGE_ROOT_NAME + "."):
            return True
        return fullname.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: object | None = None,
    ) -> None:
        if self.is_forbidden(fullname):
            raise PreparationError(
                "FORBIDDEN_IMPORT_BLOCKED",
                f"import of {fullname} is outside the closed tooling surface",
            )


@contextmanager
def governed_runtime_tripwires() -> Iterator[None]:
    """Block network surfaces and forbidden imports for the enclosed region."""

    def _blocked_network(*_args: Any, **_kwargs: Any) -> Any:
        raise PreparationError(
            "NETWORK_ACCESS_BLOCKED",
            "the tooling is local-only and must not open any network surface",
        )

    saved = {
        name: getattr(socket, name)
        for name in _BLOCKED_SOCKET_ATTRIBUTES
        if hasattr(socket, name)
    }
    guard = ForbiddenImportGuard()
    for name in saved:
        setattr(socket, name, _blocked_network)
    sys.meta_path.insert(0, guard)
    try:
        yield
    finally:
        for name, original in saved.items():
            setattr(socket, name, original)
        if guard in sys.meta_path:
            sys.meta_path.remove(guard)


# --------------------------------------------------------------------------
# Governed helper loading with proven import provenance
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GovernedHelpers:
    """The six closed governed callables plus their proven module origins."""

    sha256_bytes: Callable[[bytes], str]
    canonical_json_bytes: Callable[[Any], bytes]
    list_tracked_objects: Callable[..., Sequence[Any]]
    read_blob_bytes: Callable[..., bytes]
    frozen_contract_payload: Callable[[], Mapping[str, Any]]
    frozen_contract_sha256: Callable[[], str]
    origins: Mapping[str, str]
    pre_exec_blob_bindings: Mapping[str, Mapping[str, Any]]


def _reject_symlinked_path(root: Path, path: Path, code: str) -> None:
    if root.is_symlink():
        raise PreparationError(code, "repository root is a symlink")
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise PreparationError(code, f"path escapes the repository root: {path.name}") from None
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PreparationError(code, f"symlinked path component is refused: {part}")


def _force_repository_src_root(src_root: Path) -> None:
    """Purge ambient providers of the package and force the repository src root first."""

    for name in [key for key in sys.modules if key == PACKAGE_ROOT_NAME
                 or key.startswith(PACKAGE_ROOT_NAME + ".")]:
        del sys.modules[name]

    retained_finders = []
    for finder in sys.meta_path:
        owner = getattr(type(finder), "__module__", "") or ""
        own_name = getattr(finder, "__name__", "") or ""
        if owner.startswith("__editable__") or own_name.startswith("__editable__"):
            continue
        retained_finders.append(finder)
    sys.meta_path[:] = retained_finders

    src_text = str(src_root)
    retained_paths = []
    for entry in sys.path:
        if entry == src_text:
            continue
        try:
            shadow = Path(entry) / PACKAGE_ROOT_NAME / "__init__.py"
            if shadow.exists():
                continue
        except OSError:
            continue
        retained_paths.append(entry)
    sys.path[:] = [src_text, *retained_paths]


def _prove_package_origin(src_root: Path) -> None:
    expected_init = src_root / PACKAGE_ROOT_NAME / "__init__.py"
    spec = _guarded(
        "IMPORT_PROVENANCE_NONCONFORMING",
        "package origin lookup failed",
        PathFinder.find_spec,
        PACKAGE_ROOT_NAME,
        sys.path,
    )
    if spec is None or spec.origin is None:
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            f"{PACKAGE_ROOT_NAME} is not resolvable from the repository src root",
        )
    origin = spec.origin
    lowered = origin.lower()
    if "site-packages" in lowered or "dist-packages" in lowered or ".egg" in lowered:
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            "ambient site-package or editable-install origin is refused",
        )
    if origin != str(expected_init):
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            "resolved package origin is not the repository src root",
        )
    locations = list(spec.submodule_search_locations or ())
    if locations != [str(src_root / PACKAGE_ROOT_NAME)]:
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            "package search locations are not exactly the repository package directory",
        )


# --------------------------------------------------------------------------
# Independent pre-execution helper verification (standard library + local Git)
# --------------------------------------------------------------------------


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["LC_ALL"] = "C"
    return environment


def _git_capture(repo_root: Path, arguments: Sequence[str]) -> bytes:
    """Run one read-only local Git query; no network and no repository mutation."""

    try:
        completed = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(repo_root), *arguments],
            check=True,
            capture_output=True,
            env=_git_environment(),
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING",
            f"local read-only Git query failed: {type(exc).__name__}",
        ) from None
    return completed.stdout


def git_blob_identity(data: bytes) -> str:
    """Compute the Git blob identity of exact bytes; no identifier is ever typed."""

    digest = hashlib.new("sha1", b"blob %d\0" % len(data))
    digest.update(data)
    return digest.hexdigest()


def _parse_ls_tree_records(output: bytes) -> dict[bytes, tuple[str, str, str]]:
    """Parse NUL-delimited ``ls-tree`` records without trusting any helper code."""

    entries: dict[bytes, tuple[str, str, str]] = {}
    for field in output.split(b"\0"):
        if not field:
            continue
        header, separator, path_bytes = field.partition(b"\t")
        if not separator or not path_bytes:
            raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed tree record")
        pieces = header.split(b" ")
        if len(pieces) != 3:
            raise PreparationError(
                "GIT_REFERENCE_NONCONFORMING", "malformed tree record header"
            )
        mode, object_type, object_sha1 = pieces
        if _HEX40_BYTES_RE.fullmatch(object_sha1) is None:
            raise PreparationError(
                "GIT_REFERENCE_NONCONFORMING", "malformed tree object identity"
            )
        if path_bytes in entries:
            raise PreparationError("GIT_REFERENCE_NONCONFORMING", "duplicate tree record")
        entries[path_bytes] = (
            mode.decode("ascii", "replace"),
            object_type.decode("ascii", "replace"),
            object_sha1.decode("ascii"),
        )
    return entries


@dataclass(frozen=True)
class VerifiedHelperSource:
    """One verified helper: the exact proven bytes plus its machine binding.

    ``source_bytes`` is the byte sequence that was hashed and compared against
    the tracked HEAD blob. It is the only byte sequence that is ever compiled
    and executed, so a path swapped after verification, or an eligible cached
    bytecode file, cannot change what actually runs.
    """

    alias: str
    relative_path: str
    source_bytes: bytes
    binding: dict[str, Any]


def verify_governed_helper_sources(repo_root: Path) -> dict[str, VerifiedHelperSource]:
    """Prove each allowed helper path is an unmodified tracked blob at current HEAD.

    This runs before any governed helper module is executed and uses only the
    Python standard library and read-only local Git queries, so drifted or
    hostile helper bytes can never take part in their own verification. The
    exact verified bytes are retained in memory next to their binding and are
    handed to the loader, so the verified bytes and the executed bytes are the
    same bytes.
    """

    head_commit = resolve_head_commit(repo_root)
    if _HEX40_RE.fullmatch(head_commit) is None:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", "HEAD is not a 40-hex commit identity"
        )
    relative_paths = [relative for _alias, relative, _symbols in GOVERNED_MODULES]
    entries = _parse_ls_tree_records(
        _git_capture(
            repo_root,
            ("ls-tree", "-r", "-z", "--full-tree", head_commit, "--", *relative_paths),
        )
    )

    verified: dict[str, VerifiedHelperSource] = {}
    for alias, relative_path, _symbols in GOVERNED_MODULES:
        found = entries.get(relative_path.encode("utf-8"))
        if found is None:
            raise PreparationError(
                "GIT_REFERENCE_NONCONFORMING",
                f"governed helper is not tracked at HEAD: {relative_path}",
            )
        mode, object_type, object_sha1 = found
        if object_type != "blob" or mode not in REGULAR_FILE_MODES:
            raise PreparationError(
                "GIT_REFERENCE_NONCONFORMING",
                f"governed helper is not a regular tracked blob: {relative_path}",
            )
        worktree_bytes = _guarded(
            "GOVERNED_HELPER_BYTES_DRIFT",
            f"cannot read governed helper bytes: {relative_path}",
            (repo_root / relative_path).read_bytes,
        )
        if len(worktree_bytes) > MAX_BLOB_BYTES:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"governed helper exceeds the frozen byte ceiling: {relative_path}",
            )
        computed = _guarded(
            "GIT_REFERENCE_NONCONFORMING",
            "cannot compute the local Git blob identity",
            git_blob_identity,
            worktree_bytes,
        )
        if computed != object_sha1:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"worktree bytes differ from the tracked HEAD blob: {relative_path}",
            )
        verified[alias] = VerifiedHelperSource(
            alias=alias,
            relative_path=relative_path,
            source_bytes=worktree_bytes,
            binding={
                "path": relative_path,
                "blob_sha1": object_sha1,
                "mode": mode,
                "object_type": object_type,
                "byte_count": len(worktree_bytes),
                "verification": (
                    "WORKTREE_BYTES_EQUAL_TRACKED_HEAD_BLOB_BEFORE_ANY_HELPER_EXECUTION"
                ),
            },
        )
    return verified


def verify_governed_helper_blobs(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Return only the publishable machine bindings of the verified helpers.

    The verified source bytes stay in memory inside
    :func:`verify_governed_helper_sources` and are never published, so no raw
    helper source byte can reach the single authorized output artifact.
    """

    return {
        alias: dict(source.binding)
        for alias, source in verify_governed_helper_sources(repo_root).items()
    }


def _load_module_from_verified_bytes(
    alias: str, path: Path, source_bytes: bytes, symbols: Sequence[str]
) -> Any:
    """Compile and execute exactly the pre-verified bytes in a private namespace.

    The helper source path is never reopened here and
    ``SourceFileLoader.exec_module`` is never called, so neither a path swapped
    after verification nor an eligible cached bytecode file can substitute
    unverified module-level code. The path supplies origin metadata only.
    """

    spec = importlib_util.spec_from_file_location(f"_mes_governed_{alias}", path)
    if spec is None or spec.loader is None or spec.origin != str(path):
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            f"cannot bind {alias} to its exact allowed path",
        )
    module = importlib_util.module_from_spec(spec)
    if getattr(module, "__file__", None) != str(path):
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            f"prepared origin of {alias} is not the exact allowed path",
        )
    code = _guarded(
        "IMPORT_PROVENANCE_NONCONFORMING",
        f"cannot compile the verified bytes of governed module {alias}",
        compile,
        source_bytes,
        str(path),
        "exec",
        dont_inherit=True,
    )
    sys.modules[spec.name] = module
    try:
        _guarded(
            "IMPORT_PROVENANCE_NONCONFORMING",
            f"cannot execute governed module {alias}",
            exec,
            code,
            module.__dict__,
        )
        if getattr(module, "__file__", None) != str(path):
            raise PreparationError(
                "IMPORT_PROVENANCE_NONCONFORMING",
                f"imported origin of {alias} is not the exact allowed path",
            )
        for symbol in symbols:
            member = getattr(module, symbol, None)
            if not callable(member):
                raise PreparationError(
                    "IMPORT_PROVENANCE_NONCONFORMING",
                    f"governed symbol {alias}.{symbol} is absent or not callable",
                )
    except PreparationError:
        sys.modules.pop(spec.name, None)
        raise
    return module


def load_governed_helpers(repo_root: Path) -> GovernedHelpers:
    """Close the ambient editable-install provenance risk, then load the three modules."""

    src_root = repo_root / SRC_RELATIVE_ROOT
    if not src_root.is_dir():
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING", "repository src root is absent"
        )
    _reject_symlinked_path(repo_root, src_root, "IMPORT_PROVENANCE_NONCONFORMING")

    modules: dict[str, Any] = {}
    origins: dict[str, str] = {}
    for alias, relative_path, symbols in GOVERNED_MODULES:
        path = repo_root / relative_path
        _reject_symlinked_path(repo_root, path, "IMPORT_PROVENANCE_NONCONFORMING")
        if not path.is_file():
            raise PreparationError(
                "IMPORT_PROVENANCE_NONCONFORMING",
                f"governed module is absent: {relative_path}",
            )
        origins[alias] = relative_path
        modules[alias] = path

    # Independent standard-library-plus-local-Git proof, before any helper byte
    # is executed, that every allowed helper path is an unmodified tracked blob.
    # The proven bytes are retained and are the bytes that will be executed.
    verified_sources = verify_governed_helper_sources(repo_root)
    if set(verified_sources) != set(origins):
        raise PreparationError(
            "GOVERNED_HELPER_BYTES_DRIFT",
            "pre-execution helper verification does not cover every allowed path",
        )
    for alias, relative_path in origins.items():
        if verified_sources[alias].relative_path != relative_path:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"pre-execution helper verification is not bound to the allowed path: {alias}",
            )
    pre_exec_blob_bindings = {
        alias: dict(source.binding) for alias, source in verified_sources.items()
    }

    _force_repository_src_root(src_root)
    if sys.path[0] != str(src_root):
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING",
            "repository src root is not first on the import path",
        )
    _prove_package_origin(src_root)

    loaded = {
        alias: _load_module_from_verified_bytes(
            alias, modules[alias], verified_sources[alias].source_bytes, symbols
        )
        for alias, _relative_path, symbols in GOVERNED_MODULES
    }
    return GovernedHelpers(
        sha256_bytes=loaded["hashing"].sha256_bytes,
        canonical_json_bytes=loaded["hashing"].canonical_json_bytes,
        list_tracked_objects=loaded["reference_objects"].list_tracked_objects,
        read_blob_bytes=loaded["reference_objects"].read_blob_bytes,
        frozen_contract_payload=loaded["test3_contract"].frozen_contract_payload,
        frozen_contract_sha256=loaded["test3_contract"].frozen_contract_sha256,
        origins=dict(origins),
        pre_exec_blob_bindings=pre_exec_blob_bindings,
    )


# --------------------------------------------------------------------------
# Local Git reference resolution and object selection
# --------------------------------------------------------------------------


def resolve_git_dir(repo_root: Path) -> Path:
    candidate = repo_root / ".git"
    if candidate.is_dir():
        return candidate
    if candidate.is_file():
        text = _guarded(
            "GIT_REFERENCE_NONCONFORMING", "cannot read .git file", candidate.read_text, "utf-8"
        ).strip()
        prefix = "gitdir: "
        if not text.startswith(prefix):
            raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed .git file")
        pointer = Path(text[len(prefix) :].strip())
        if not pointer.is_absolute():
            pointer = repo_root / pointer
        pointer = pointer.resolve()
        if not pointer.is_dir():
            raise PreparationError(
                "GIT_REFERENCE_NONCONFORMING", "linked git directory is absent"
            )
        return pointer
    raise PreparationError("GIT_REFERENCE_NONCONFORMING", "repository has no git directory")


def resolve_common_git_dir(git_dir: Path) -> Path:
    """Resolve the shared object/ref directory of a linked worktree, if any."""

    pointer_file = git_dir / "commondir"
    if not pointer_file.is_file():
        return git_dir
    text = _guarded(
        "GIT_REFERENCE_NONCONFORMING", "cannot read commondir", pointer_file.read_text, "utf-8"
    ).strip()
    if not text:
        raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed commondir file")
    pointer = Path(text)
    if not pointer.is_absolute():
        pointer = git_dir / pointer
    pointer = pointer.resolve()
    if not pointer.is_dir():
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", "shared git directory is absent"
        )
    return pointer


def resolve_head_commit(repo_root: Path) -> str:
    """Read the base commit from local refs; no identifier is ever supplied by hand."""

    git_dir = resolve_git_dir(repo_root)
    head_file = git_dir / "HEAD"
    if not head_file.is_file():
        raise PreparationError("GIT_REFERENCE_NONCONFORMING", "HEAD is absent")
    head = _guarded(
        "GIT_REFERENCE_NONCONFORMING", "cannot read HEAD", head_file.read_text, "utf-8"
    ).strip()
    if _HEX40_RE.fullmatch(head):
        return head
    if not head.startswith("ref: "):
        raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed HEAD content")
    ref = head[len("ref: ") :].strip()
    if not ref.startswith("refs/") or ".." in ref or ref.endswith("/"):
        raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed HEAD symbolic ref")

    # A linked worktree keeps HEAD in its own git directory while branch refs
    # live in the shared common directory, so both roots are searched in order.
    common_git_dir = resolve_common_git_dir(git_dir)
    search_roots = [git_dir]
    if common_git_dir != git_dir:
        search_roots.append(common_git_dir)

    for root in search_roots:
        loose = root.joinpath(*ref.split("/"))
        if loose.is_file() and not loose.is_symlink():
            value = _guarded(
                "GIT_REFERENCE_NONCONFORMING", "cannot read ref", loose.read_text, "utf-8"
            ).strip()
            if not _HEX40_RE.fullmatch(value):
                raise PreparationError("GIT_REFERENCE_NONCONFORMING", "malformed ref content")
            return value

    matches: list[str] = []
    for root in search_roots:
        packed = root / "packed-refs"
        if not packed.is_file():
            continue
        packed_text = _guarded(
            "GIT_REFERENCE_NONCONFORMING", "cannot read packed-refs", packed.read_text, "utf-8"
        )
        for line in packed_text.splitlines():
            if not line or line.startswith(("#", "^")):
                continue
            parts = line.split(" ")
            if len(parts) == 2 and parts[1] == ref and _HEX40_RE.fullmatch(parts[0]):
                matches.append(parts[0])
    if len(matches) != 1:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", "HEAD does not resolve to exactly one commit"
        )
    return matches[0]


def list_commit_objects(helpers: GovernedHelpers, repo_root: Path, commit: str) -> Sequence[Any]:
    if not _HEX40_RE.fullmatch(commit):
        raise PreparationError("GIT_REFERENCE_NONCONFORMING", "commit is not a 40-hex identity")
    return _guarded(
        "GIT_REFERENCE_NONCONFORMING",
        "cannot enumerate the commit tree",
        helpers.list_tracked_objects,
        repo_root,
        commit_sha1=commit,
        max_tracked_objects=MAX_TRACKED_OBJECTS,
    )


def select_unique_blob(objects: Sequence[Any], relative_path: str) -> Any:
    """Require exactly one tracked regular-file blob at the exact path."""

    wanted = relative_path.encode("utf-8")
    matches = [entry for entry in objects if entry.path_bytes == wanted]
    if not matches:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", f"path is absent from the commit tree: {relative_path}"
        )
    if len(matches) > 1:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", f"duplicate tree entries for path: {relative_path}"
        )
    entry = matches[0]
    if entry.object_type != "blob" or entry.mode not in REGULAR_FILE_MODES:
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING",
            f"tree entry is not a regular-file blob: {relative_path}",
        )
    if not _HEX40_RE.fullmatch(entry.object_sha1):
        raise PreparationError(
            "GIT_REFERENCE_NONCONFORMING", f"malformed object identity for: {relative_path}"
        )
    return entry


def read_tracked_blob(
    helpers: GovernedHelpers, repo_root: Path, objects: Sequence[Any], relative_path: str
) -> tuple[Any, bytes]:
    entry = select_unique_blob(objects, relative_path)
    blob = _guarded(
        "GIT_REFERENCE_NONCONFORMING",
        f"cannot read blob for {relative_path}",
        helpers.read_blob_bytes,
        repo_root,
        blob_sha1=entry.object_sha1,
        max_blob_bytes=MAX_BLOB_BYTES,
    )
    return entry, blob


# --------------------------------------------------------------------------
# Owner co-ratification record parsing and historical parent verification
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ParentRow:
    artifact_id: str
    path: str
    recorded_sha256: str


@dataclass(frozen=True)
class RatificationRecord:
    ratified_commit: str
    rows: tuple[ParentRow, ...]


def parse_ratification_record(record_bytes: bytes) -> RatificationRecord:
    """Parse the exact-byte record preamble and Section 1 by exact field identity."""

    def fail(detail: str) -> PreparationError:
        return PreparationError("RATIFICATION_RECORD_NONCONFORMING", detail)

    try:
        text = record_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise fail("record bytes are not valid UTF-8") from None

    lines = text.splitlines()
    heading_positions = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not heading_positions:
        raise fail("record has no sections")

    preamble = lines[: heading_positions[0]]
    body = lines[heading_positions[0] :]
    commit_lines = [line for line in preamble if line.startswith("Ratified commit")]
    if len(commit_lines) != 1:
        raise fail("exactly one preamble Ratified commit field is required")
    if any(line.startswith("Ratified commit") for line in body):
        raise fail("Ratified commit field is duplicated outside the preamble")
    commit_match = _RATIFIED_COMMIT_RE.fullmatch(commit_lines[0])
    if commit_match is None:
        raise fail("Ratified commit field is malformed or abbreviated")
    ratified_commit = commit_match.group(1)

    section_starts = [
        index for index in heading_positions if _SECTION_ONE_RE.fullmatch(lines[index])
    ]
    if len(section_starts) != 1:
        raise fail("exactly one Section 1 heading is required")
    start = section_starts[0]
    following = [index for index in heading_positions if index > start]
    end = following[0] if following else len(lines)
    section_one = lines[start:end]

    table = [line for line in section_one if line.startswith("|")]
    if len(table) != 2 + len(REQUIRED_PARENT_ARTIFACTS):
        raise fail("Section 1 table does not carry exactly the two required rows")
    if _TABLE_HEADER_RE.fullmatch(table[0]) is None:
        raise fail("Section 1 table header is malformed")
    if _TABLE_SEPARATOR_RE.fullmatch(table[1]) is None:
        raise fail("Section 1 table separator is malformed")

    parsed: dict[str, ParentRow] = {}
    for line in table[2:]:
        row_match = _TABLE_ROW_RE.fullmatch(line)
        if row_match is None:
            raise fail("Section 1 table row is malformed or abbreviated")
        artifact_id, path, digest = row_match.groups()
        if artifact_id in parsed:
            raise fail(f"duplicate Section 1 row for identity: {artifact_id}")
        parsed[artifact_id] = ParentRow(
            artifact_id=artifact_id, path=path, recorded_sha256=digest
        )

    rows: list[ParentRow] = []
    for expected_id, expected_path in REQUIRED_PARENT_ARTIFACTS:
        row = parsed.get(expected_id)
        if row is None:
            raise fail(f"required Section 1 identity is absent: {expected_id}")
        if row.path != expected_path:
            raise fail(f"Section 1 path mismatch for identity: {expected_id}")
        rows.append(row)
    if len(parsed) != len(rows):
        raise fail("Section 1 carries an extra artifact row")

    return RatificationRecord(ratified_commit=ratified_commit, rows=tuple(rows))


def verify_historical_parents(
    helpers: GovernedHelpers, repo_root: Path, record: RatificationRecord
) -> list[dict[str, Any]]:
    """Resolve both parent paths as blobs at the parsed commit and hash exact bytes."""

    objects = list_commit_objects(helpers, repo_root, record.ratified_commit)
    bindings: list[dict[str, Any]] = []
    for row in record.rows:
        entry, blob = read_tracked_blob(helpers, repo_root, objects, row.path)
        computed = helpers.sha256_bytes(blob)
        if computed != row.recorded_sha256:
            raise PreparationError(
                "PARENT_BLOB_NONCONFORMING",
                f"exact blob bytes do not match the recorded digest for {row.artifact_id}",
            )
        bindings.append(
            {
                "artifact_id": row.artifact_id,
                "path": row.path,
                "recorded_sha256": row.recorded_sha256,
                "computed_sha256": computed,
                "blob_sha1": entry.object_sha1,
                "mode": entry.mode,
                "object_type": entry.object_type,
                "byte_count": len(blob),
                "verification": "EXACT_BLOB_BYTES_EQUAL_RECORDED_DIGEST",
            }
        )
    return bindings


# --------------------------------------------------------------------------
# Frozen Test 3 contract self-consistency (only the two named functions)
# --------------------------------------------------------------------------


def _json_safe(value: Any, *, strict: bool) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item, strict=strict) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, strict=strict) for item in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        return str(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if strict:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING",
            f"unsupported frozen payload member type: {type(value).__name__}",
        )
    return str(value)


TEST3_CONTRACT_SERIALIZATION = "JSON_DUMPS_PLAIN_PAYLOAD_SORT_KEYS_COMMA_COLON_UTF8_NO_FINAL_LF"


def test3_contract_canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    """Reproduce the exact ``test3_contract`` digest serialization semantics.

    ``json.dumps`` of the plain payload with ``sort_keys=True`` and
    ``separators=(",", ":")``, encoded as UTF-8 with no final line feed.
    """

    plain = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen contract payload is not a plain mapping",
        dict,
        payload,
    )
    text = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen contract payload is not JSON serializable",
        json.dumps,
        plain,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded = text.encode("utf-8")
    if encoded.endswith(b"\n"):
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING",
            "frozen contract serialization must not carry a final line feed",
        )
    return encoded


def build_contract_self_check(helpers: GovernedHelpers) -> dict[str, Any]:
    """Prove the frozen payload and its digest are self-consistent.

    The payload is taken twice, serialized with the exact ``test3_contract``
    semantics, and the machine-recomputed digest of those bytes must equal the
    module's own ``frozen_contract_sha256``.
    """

    first = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen_contract_payload failed",
        helpers.frozen_contract_payload,
    )
    second = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen_contract_payload failed",
        helpers.frozen_contract_payload,
    )
    canonical_first = helpers.canonical_json_bytes(_json_safe(first, strict=True))
    canonical_second = helpers.canonical_json_bytes(_json_safe(second, strict=True))
    if canonical_first != canonical_second:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING", "frozen contract payload is not deterministic"
        )

    digest_first = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen_contract_sha256 failed",
        helpers.frozen_contract_sha256,
    )
    digest_second = _guarded(
        "CONTRACT_SELF_CHECK_NONCONFORMING",
        "frozen_contract_sha256 failed",
        helpers.frozen_contract_sha256,
    )
    if digest_first != digest_second:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING", "frozen contract digest is not deterministic"
        )
    if not isinstance(digest_first, str) or _HEX64_RE.fullmatch(digest_first) is None:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING", "frozen contract digest is malformed"
        )

    exact_first = test3_contract_canonical_bytes(first)
    exact_second = test3_contract_canonical_bytes(second)
    if exact_first != exact_second:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING",
            "frozen contract exact serialization is not deterministic",
        )
    recomputed_sha256 = helpers.sha256_bytes(exact_first)
    if recomputed_sha256 != digest_first:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING",
            "machine-recomputed frozen payload digest is not frozen_contract_sha256",
        )

    payload = _json_safe(first, strict=True)
    return {
        "basis": "MACHINE_RECOMPUTED_PAYLOAD_BYTES_AND_MODULE_DIGEST_SELF_CONSISTENCY",
        "scope": "HISTORICAL_EXPLORATORY_VOCABULARY_ONLY_NOT_A_TRUST_ROOT",
        "frozen_contract_payload_canonical_sha256": helpers.sha256_bytes(canonical_first),
        "frozen_contract_payload_byte_count": len(canonical_first),
        "frozen_contract_payload_exact_serialization": TEST3_CONTRACT_SERIALIZATION,
        "frozen_contract_payload_exact_byte_count": len(exact_first),
        "frozen_contract_recomputed_sha256": recomputed_sha256,
        "frozen_contract_sha256": digest_first,
        "self_consistency": "RECOMPUTED_PAYLOAD_DIGEST_EQUALS_FROZEN_CONTRACT_SHA256",
        "bootstrap_parameters": extract_contract_parameters(payload),
    }


def extract_contract_parameters(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Read the frozen bootstrap parameters that pin the synthetic golden fixture."""

    def require_int(key: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise PreparationError(
                "CONTRACT_SELF_CHECK_NONCONFORMING",
                f"frozen contract field is absent or invalid: {key}",
            )
        return value

    blocks = payload.get("bootstrap_blocks")
    if not isinstance(blocks, (list, tuple)) or not blocks:
        raise PreparationError(
            "CONTRACT_SELF_CHECK_NONCONFORMING", "frozen contract bootstrap_blocks is invalid"
        )
    block_lengths: list[int] = []
    for block in blocks:
        if not isinstance(block, int) or isinstance(block, bool) or block < 1:
            raise PreparationError(
                "CONTRACT_SELF_CHECK_NONCONFORMING",
                "frozen contract bootstrap_blocks carries an invalid length",
            )
        block_lengths.append(block)
    return {
        "master_seed": require_int("master_seed"),
        "bootstrap_repetitions": require_int("bootstrap_repetitions"),
        "bootstrap_blocks_ordered": block_lengths,
    }


# --------------------------------------------------------------------------
# Complete runtime identity
# --------------------------------------------------------------------------


def _numpy_build_config() -> Any:
    config_module = getattr(numpy, "__config__", None)
    if config_module is None:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "numpy build configuration is unavailable"
        )
    show = getattr(config_module, "show", None)
    if callable(show):
        try:
            dicts = show(mode="dicts")
        except TypeError:
            dicts = None
        if dicts:
            return _json_safe(dicts, strict=False)
    legacy = {
        name: getattr(config_module, name)
        for name in dir(config_module)
        if name.endswith("_info")
    }
    if not legacy:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "numpy build configuration is unavailable"
        )
    return _json_safe(legacy, strict=False)


def build_float_info_map() -> dict[str, Any]:
    """Record ``sys.float_info`` through an explicit ordered field map.

    ``sys.float_info`` is a structseq without a supported ``_asdict`` contract,
    so each recorded field is named, read and type-checked explicitly.
    """

    info = sys.float_info
    recorded: dict[str, Any] = {}
    for name in FLOAT_INFO_FLOAT_FIELDS_ORDERED:
        value = getattr(info, name, None)
        if not isinstance(value, float):
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"sys.float_info float field is absent or not a float: {name}",
            )
        recorded[f"{name}_hex"] = value.hex()
    for name in FLOAT_INFO_INT_FIELDS_ORDERED:
        value = getattr(info, name, None)
        if not isinstance(value, int) or isinstance(value, bool):
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"sys.float_info integer field is absent or not an integer: {name}",
            )
        recorded[name] = int(value)
    return recorded


def require_complete_float_info(float_info: Any) -> None:
    """Validate the nested float_info field set, key by key, with exact types."""

    if not isinstance(float_info, Mapping):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "runtime identity float_info is not a mapping"
        )
    if set(float_info) != REQUIRED_FLOAT_INFO_KEYS:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "runtime identity float_info field set is not exactly the required map",
        )
    for name in FLOAT_INFO_FLOAT_FIELDS_ORDERED:
        value = float_info[f"{name}_hex"]
        if not isinstance(value, str) or not value:
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"runtime identity float_info hex field is malformed: {name}",
            )
        _guarded(
            "RUNTIME_IDENTITY_NONCONFORMING",
            f"runtime identity float_info hex field is not a float hex literal: {name}",
            float.fromhex,
            value,
        )
    for name in FLOAT_INFO_INT_FIELDS_ORDERED:
        value = float_info[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"runtime identity float_info integer field is malformed: {name}",
            )


def build_python_executable_identity() -> dict[str, str]:
    """Bind the identity to the actual interpreter that is running this tool.

    Both the raw ``sys.executable`` value and its strict resolution are
    recorded, so a relative, absent or later-swapped interpreter path cannot be
    published as a valid runtime identity.
    """

    executable = sys.executable
    if not isinstance(executable, str) or not executable:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "sys.executable is absent or empty"
        )
    candidate = Path(executable)
    if not candidate.is_absolute():
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "sys.executable is not an absolute path"
        )
    resolved = _guarded(
        "RUNTIME_IDENTITY_NONCONFORMING",
        "sys.executable does not resolve strictly to an existing path",
        candidate.resolve,
        strict=True,
    )
    if not resolved.is_file():
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "the resolved sys.executable is not an existing regular file",
        )
    return {
        PYTHON_EXECUTABLE_FIELD: executable,
        PYTHON_EXECUTABLE_RESOLVED_FIELD: str(resolved),
    }


def require_python_executable_identity(python_section: Mapping[str, Any]) -> None:
    """Validate the recorded interpreter identity against this machine."""

    executable = python_section[PYTHON_EXECUTABLE_FIELD]
    resolved = python_section[PYTHON_EXECUTABLE_RESOLVED_FIELD]
    for label, value in (
        (PYTHON_EXECUTABLE_FIELD, executable),
        (PYTHON_EXECUTABLE_RESOLVED_FIELD, resolved),
    ):
        if not isinstance(value, str) or not value:
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"runtime identity python.{label} is absent, empty or not text",
            )
        if not Path(value).is_absolute():
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"runtime identity python.{label} is not an absolute path",
            )
    entry = _guarded(
        "RUNTIME_IDENTITY_NONCONFORMING",
        "the recorded resolved python executable cannot be inspected",
        os.stat,
        resolved,
    )
    if not stat.S_ISREG(entry.st_mode):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "the recorded resolved python executable is not a regular file",
        )
    strict = _guarded(
        "RUNTIME_IDENTITY_NONCONFORMING",
        "the recorded python executable does not resolve strictly",
        Path(executable).resolve,
        strict=True,
    )
    if str(strict) != resolved:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "the recorded python executable does not resolve to the recorded resolved path",
        )


def build_runtime_identity() -> dict[str, Any]:
    """Record the complete current execution identity required before any boundary."""

    finfo = numpy.finfo(numpy.float64)
    dtype = numpy.dtype(numpy.float64)
    generator = numpy.random.default_rng(0)
    bit_generator = generator.bit_generator
    float_info = build_float_info_map()
    return {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_full": sys.version,
            "api_version": sys.api_version,
            "hexversion": sys.hexversion,
            "cache_tag": str(sys.implementation.cache_tag),
            "maxsize": sys.maxsize,
            "float_repr_style": sys.float_repr_style,
            **build_python_executable_identity(),
            "float_info": float_info,
        },
        "numpy": {
            "version": str(numpy.__version__),
            "build_config": _numpy_build_config(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "byteorder": sys.byteorder,
            "libc": list(platform.libc_ver()),
        },
        "float64": {
            "dtype_str": dtype.str,
            "itemsize": int(dtype.itemsize),
            "byteorder": dtype.byteorder,
            **{
                f"{name}_hex": float(getattr(finfo, name)).hex()
                for name in FLOAT64_HEX_FIELDS_ORDERED
            },
            **{name: int(getattr(finfo, name)) for name in FLOAT64_INT_FIELDS_ORDERED},
        },
        "rng": {
            "bit_generator_module": type(bit_generator).__module__,
            "bit_generator_class": type(bit_generator).__qualname__,
            "generator_class": f"{type(generator).__module__}.{type(generator).__qualname__}",
            "pcg64_module": numpy.random.PCG64.__module__,
            "pcg64_class": numpy.random.PCG64.__qualname__,
        },
    }


def require_complete_runtime_identity(
    identity: Mapping[str, Any], canonical_json_bytes: Callable[[Any], bytes]
) -> None:
    if not isinstance(identity, Mapping):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "runtime identity is not a mapping"
        )
    if set(identity) != {group for group, _fields in REQUIRED_RUNTIME_IDENTITY_SHAPE}:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "runtime identity group set is not exactly the declared map",
        )
    for group, fields in REQUIRED_RUNTIME_IDENTITY_SHAPE:
        section = identity[group]
        if not isinstance(section, Mapping):
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING", f"runtime identity group is absent: {group}"
            )
        if set(section) != set(fields):
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"runtime identity field set is not exactly the declared map: {group}",
            )
        for field in fields:
            value = section[field]
            key = (group, field)
            if key in RUNTIME_IDENTITY_TEXT_FIELDS:
                if not isinstance(value, str):
                    raise PreparationError(
                        "RUNTIME_IDENTITY_NONCONFORMING",
                        f"runtime identity field is not text: {group}.{field}",
                    )
                if not value and key not in RUNTIME_IDENTITY_EMPTY_TEXT_ALLOWED:
                    raise PreparationError(
                        "RUNTIME_IDENTITY_NONCONFORMING",
                        f"runtime identity field is absent or empty: {group}.{field}",
                    )
                continue
            if key in RUNTIME_IDENTITY_INTEGER_FIELDS:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise PreparationError(
                        "RUNTIME_IDENTITY_NONCONFORMING",
                        f"runtime identity field is not an integer: {group}.{field}",
                    )
                continue
            if value in (None, "", [], {}):
                raise PreparationError(
                    "RUNTIME_IDENTITY_NONCONFORMING",
                    f"runtime identity field is absent or empty: {group}.{field}",
                )
    python_section = identity["python"]
    require_python_executable_identity(python_section)
    require_complete_float_info(python_section["float_info"])
    libc = identity["platform"]["libc"]
    if not isinstance(libc, list) or not all(isinstance(item, str) for item in libc):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING", "runtime identity platform.libc is malformed"
        )
    build_config = identity["numpy"]["build_config"]
    if not isinstance(build_config, (Mapping, list)):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "runtime identity numpy build configuration is not a structured record",
        )
    config_text = canonical_json_bytes(build_config).decode("utf-8").lower()
    for required in ("blas", "lapack"):
        if required not in config_text:
            raise PreparationError(
                "RUNTIME_IDENTITY_NONCONFORMING",
                f"numpy build configuration omits the {required} identity",
            )


def build_runtime_identity_binding(helpers: GovernedHelpers) -> dict[str, Any]:
    """Record the identity, immediately re-record it, and require exact equality."""

    first = build_runtime_identity()
    require_complete_runtime_identity(first, helpers.canonical_json_bytes)
    canonical_first = helpers.canonical_json_bytes(first)
    second = build_runtime_identity()
    require_complete_runtime_identity(second, helpers.canonical_json_bytes)
    canonical_second = helpers.canonical_json_bytes(second)
    if canonical_first != canonical_second:
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "immediate runtime-identity re-record is not exactly equal",
        )
    digest_first = helpers.sha256_bytes(canonical_first)
    if digest_first != helpers.sha256_bytes(canonical_second):
        raise PreparationError(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "immediate runtime-identity re-record digest is not exactly equal",
        )
    return {
        "identity": first,
        "identity_sha256": digest_first,
        "equality": "CREATE_TIME_RECORD_AND_IMMEDIATE_RE_RECORD_EXACTLY_EQUAL",
        "scope": "TOOLING_RUNTIME_ONLY_NOT_C0_NOT_C0V",
    }


# --------------------------------------------------------------------------
# Deterministic synthetic golden fixture (in memory and inside path 3 only)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GoldenFixtureSpec:
    session_count: int
    master_seed: int
    replications: int
    block_lengths: tuple[int, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "content": "SYNTHETIC_ONLY",
            "session_count": self.session_count,
            "master_seed": self.master_seed,
            "replications": self.replications,
            "block_lengths_ordered": list(self.block_lengths),
        }


def fixture_spec_from_contract(parameters: Mapping[str, Any]) -> GoldenFixtureSpec:
    block_lengths = tuple(int(block) for block in parameters["bootstrap_blocks_ordered"])
    spec = GoldenFixtureSpec(
        session_count=SYNTHETIC_SESSION_COUNT,
        master_seed=int(parameters["master_seed"]),
        replications=int(parameters["bootstrap_repetitions"]),
        block_lengths=block_lengths,
    )
    if spec.session_count < max(spec.block_lengths):
        raise PreparationError(
            "GOLDEN_FIXTURE_NONCONFORMING",
            "synthetic session count is smaller than the largest block length",
        )
    return spec


def _session_row_counts(spec: GoldenFixtureSpec) -> list[int]:
    return [4 + (index % 3) for index in range(spec.session_count)]


def synthetic_inputs(
    spec: GoldenFixtureSpec,
) -> tuple[list[int], numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """Build the closed-form synthetic row inputs; no data or provider is touched."""

    counts = _session_row_counts(spec)
    total = sum(counts)
    index = numpy.arange(total, dtype=numpy.int64)
    actual = 1.0 + ((index * 7) % 13) / 16.0
    base = 1.0 + ((index * 5) % 11) / 16.0
    har = 1.0 + ((index * 3) % 17) / 32.0
    return (
        counts,
        numpy.ascontiguousarray(actual, dtype=numpy.float64),
        numpy.ascontiguousarray(base, dtype=numpy.float64),
        numpy.ascontiguousarray(har, dtype=numpy.float64),
    )


def _left_fold(values: Any) -> numpy.float64:
    accumulator = numpy.float64(0.0)
    for value in values:
        accumulator = numpy.float64(accumulator + value)
    return accumulator


def _draw_matrix(spec: GoldenFixtureSpec, block_length: int) -> tuple[int, numpy.ndarray]:
    sessions = spec.session_count
    if sessions < block_length:
        raise PreparationError(
            "GOLDEN_FIXTURE_NONCONFORMING", "session count is smaller than the block length"
        )
    validation_seed = spec.master_seed + 90000 + block_length + 1000
    blocks_needed = -(-sessions // block_length)
    generator = numpy.random.default_rng(validation_seed)
    matrix = numpy.zeros((spec.replications, sessions), dtype=numpy.int32)
    for replicate in range(spec.replications):
        starts = generator.integers(
            low=0,
            high=sessions - block_length + 1,
            size=blocks_needed,
            dtype=numpy.int64,
            endpoint=False,
        )
        expanded = numpy.concatenate(
            [
                numpy.arange(int(start), int(start) + block_length, dtype=numpy.int32)
                for start in starts
            ]
        )
        matrix[replicate, :] = expanded[:sessions]
    return validation_seed, numpy.ascontiguousarray(matrix)


def generate_golden_fixture(
    spec: GoldenFixtureSpec, helpers: GovernedHelpers
) -> tuple[dict[str, Any], bytes]:
    """Materialize the synthetic fixture exactly once and return its record and raw bytes."""

    counts, actual, base, har = synthetic_inputs(spec)
    with numpy.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        ratio_base = actual / base
        losses_base = ratio_base - numpy.log(ratio_base) - numpy.float64(1.0)
        ratio_har = actual / har
        losses_har = ratio_har - numpy.log(ratio_har) - numpy.float64(1.0)
        differences = losses_base - losses_har

    row_count = int(differences.shape[0])
    mean_base = numpy.float64(_left_fold(losses_base) / numpy.float64(row_count))
    mean_har = numpy.float64(_left_fold(losses_har) / numpy.float64(row_count))
    mean_difference = numpy.float64(_left_fold(differences) / numpy.float64(row_count))
    if not (numpy.isfinite(mean_base) and mean_base > numpy.float64(0.0)):
        raise PreparationError(
            "GOLDEN_FIXTURE_NONCONFORMING", "synthetic baseline mean is not finite and positive"
        )
    relative = numpy.float64(numpy.float64(mean_base - mean_har) / mean_base)

    session_sums = numpy.zeros(spec.session_count, dtype=numpy.float64)
    session_counts = numpy.asarray(counts, dtype=numpy.int64)
    cursor = 0
    for session, size in enumerate(counts):
        session_sums[session] = _left_fold(differences[cursor : cursor + size])
        cursor += size

    raw_parts = [
        actual.tobytes(order="C"),
        base.tobytes(order="C"),
        har.tobytes(order="C"),
        losses_base.tobytes(order="C"),
        losses_har.tobytes(order="C"),
        differences.tobytes(order="C"),
        session_counts.tobytes(order="C"),
        session_sums.tobytes(order="C"),
    ]

    blocks: list[dict[str, Any]] = []
    for block_length in spec.block_lengths:
        validation_seed, matrix = _draw_matrix(spec, block_length)
        replicates = numpy.zeros(spec.replications, dtype=numpy.float64)
        for replicate in range(spec.replications):
            selected = matrix[replicate]
            numerator = _left_fold(session_sums[selected])
            denominator = _left_fold(session_counts[selected].astype(numpy.float64))
            if not (numpy.isfinite(denominator) and denominator > numpy.float64(0.0)):
                raise PreparationError(
                    "GOLDEN_FIXTURE_NONCONFORMING",
                    "synthetic replicate denominator is not finite and positive",
                )
            replicates[replicate] = numpy.float64(numerator / denominator)
        if not bool(numpy.all(numpy.isfinite(replicates))):
            raise PreparationError(
                "GOLDEN_FIXTURE_NONCONFORMING", "synthetic replicate vector is not finite"
            )
        replicates = numpy.ascontiguousarray(replicates)
        quantile = numpy.quantile(replicates, numpy.float64(0.05), method="linear")
        raw_parts.append(matrix.tobytes(order="C"))
        raw_parts.append(replicates.tobytes(order="C"))
        blocks.append(
            {
                "block_length": int(block_length),
                "validation_seed": int(validation_seed),
                "blocks_needed": -(-spec.session_count // block_length),
                "draw_matrix_sha256": helpers.sha256_bytes(matrix.tobytes(order="C")),
                "replicate_vector_sha256": helpers.sha256_bytes(replicates.tobytes(order="C")),
                "quantile_hex": float(quantile).hex(),
            }
        )

    record = {
        "spec": spec.as_payload(),
        "storage": FIXTURE_STORAGE,
        "row_count": row_count,
        "inputs_sha256": {
            "actual": helpers.sha256_bytes(actual.tobytes(order="C")),
            "forecast_base": helpers.sha256_bytes(base.tobytes(order="C")),
            "forecast_har": helpers.sha256_bytes(har.tobytes(order="C")),
        },
        "row_losses_sha256": {
            "loss_base": helpers.sha256_bytes(losses_base.tobytes(order="C")),
            "loss_har": helpers.sha256_bytes(losses_har.tobytes(order="C")),
            "difference": helpers.sha256_bytes(differences.tobytes(order="C")),
        },
        "means_hex": {
            "mean_base": float(mean_base).hex(),
            "mean_har": float(mean_har).hex(),
            "mean_difference": float(mean_difference).hex(),
            "relative_reduction": float(relative).hex(),
        },
        "session_aggregates_sha256": {
            "row_counts": helpers.sha256_bytes(session_counts.tobytes(order="C")),
            "improvement_sums": helpers.sha256_bytes(session_sums.tobytes(order="C")),
        },
        "blocks_ordered": blocks,
    }
    raw = b"".join(raw_parts)
    record["raw_material_sha256"] = helpers.sha256_bytes(raw)
    return record, raw


def verify_golden_fixture_replay(
    spec: GoldenFixtureSpec, helpers: GovernedHelpers
) -> dict[str, Any]:
    """Generate the fixture twice and require exact bytewise and record equality."""

    first_record, first_raw = generate_golden_fixture(spec, helpers)
    second_record, second_raw = generate_golden_fixture(spec, helpers)
    if first_raw != second_raw:
        raise PreparationError(
            "GOLDEN_FIXTURE_NONCONFORMING", "bytewise replay of the golden fixture differs"
        )
    if helpers.canonical_json_bytes(first_record) != helpers.canonical_json_bytes(second_record):
        raise PreparationError(
            "GOLDEN_FIXTURE_NONCONFORMING", "golden fixture record is not deterministic"
        )
    first_record["replay"] = "EXACT_BYTEWISE_REPLAY_VERIFIED"
    return first_record


# --------------------------------------------------------------------------
# Binding payload assembly
# --------------------------------------------------------------------------


def _file_binding(
    helpers: GovernedHelpers,
    repo_root: Path,
    objects: Sequence[Any],
    relative_path: str,
    *,
    tracked_required: bool,
) -> dict[str, Any]:
    path = repo_root / relative_path
    _reject_symlinked_path(repo_root, path, "IMPORT_PROVENANCE_NONCONFORMING")
    if not path.is_file():
        raise PreparationError(
            "IMPORT_PROVENANCE_NONCONFORMING", f"bound file is absent: {relative_path}"
        )
    current = _guarded(
        "IMPORT_PROVENANCE_NONCONFORMING",
        f"cannot read {relative_path}",
        path.read_bytes,
    )
    binding: dict[str, Any] = {
        "path": relative_path,
        "sha256": helpers.sha256_bytes(current),
        "byte_count": len(current),
    }
    wanted = relative_path.encode("utf-8")
    tracked = any(entry.path_bytes == wanted for entry in objects)
    if not tracked:
        if tracked_required:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"governed module is untracked at the base commit: {relative_path}",
            )
        binding["git_state"] = "UNTRACKED_AT_BASE_COMMIT"
        binding["blob_sha1"] = None
        return binding

    entry, blob = read_tracked_blob(helpers, repo_root, objects, relative_path)
    if blob != current:
        code = "GOVERNED_HELPER_BYTES_DRIFT" if tracked_required else "BINDING_MISMATCH"
        raise PreparationError(
            code, f"worktree bytes differ from the base-commit blob: {relative_path}"
        )
    binding["git_state"] = "TRACKED_AND_EQUAL_TO_BASE_COMMIT_BLOB"
    binding["blob_sha1"] = entry.object_sha1
    return binding


def build_binding_payload(repo_root: Path, helpers: GovernedHelpers) -> dict[str, Any]:
    """Run every mandatory capability and return the complete deterministic payload."""

    base_commit = resolve_head_commit(repo_root)
    objects = list_commit_objects(helpers, repo_root, base_commit)

    governed_bindings = []
    for alias, relative_path, symbols in GOVERNED_MODULES:
        if helpers.origins.get(alias) != relative_path:
            raise PreparationError(
                "IMPORT_PROVENANCE_NONCONFORMING",
                f"loaded origin for {alias} is not the exact allowed path",
            )
        binding = _file_binding(
            helpers, repo_root, objects, relative_path, tracked_required=True
        )
        pre_exec = helpers.pre_exec_blob_bindings.get(alias)
        if not isinstance(pre_exec, Mapping) or pre_exec.get("path") != relative_path:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"pre-execution helper verification is absent for {alias}",
            )
        if pre_exec.get("blob_sha1") != binding["blob_sha1"]:
            raise PreparationError(
                "GOVERNED_HELPER_BYTES_DRIFT",
                f"pre-execution helper blob identity changed for {alias}",
            )
        binding["alias"] = alias
        binding["allowed_symbols_ordered"] = list(symbols)
        binding["pre_exec_verification"] = pre_exec["verification"]
        governed_bindings.append(binding)

    tool_binding = _file_binding(
        helpers, repo_root, objects, TOOL_RELATIVE_PATH, tracked_required=False
    )
    tests_binding = _file_binding(
        helpers, repo_root, objects, TESTS_RELATIVE_PATH, tracked_required=False
    )

    record_entry, record_bytes = read_tracked_blob(
        helpers, repo_root, objects, RATIFICATION_RECORD_RELATIVE_PATH
    )
    record = parse_ratification_record(record_bytes)
    parent_bindings = verify_historical_parents(helpers, repo_root, record)

    contract = build_contract_self_check(helpers)
    runtime = build_runtime_identity_binding(helpers)
    spec = fixture_spec_from_contract(contract["bootstrap_parameters"])
    fixture = verify_golden_fixture_replay(spec, helpers)

    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "data_policy": DATA_POLICY,
        "network_policy": NETWORK_POLICY,
        "modes_closed_ordered": list(MODES),
        "authorized_tooling_paths_ordered": list(AUTHORIZED_TOOLING_PATHS),
        "tool_binding": tool_binding,
        "tests_binding": tests_binding,
        "governed_helper_bindings_ordered": governed_bindings,
        "repository_binding": {
            "base_commit": base_commit,
            "ratification_record": {
                "path": RATIFICATION_RECORD_RELATIVE_PATH,
                "blob_sha1": record_entry.object_sha1,
                "sha256": helpers.sha256_bytes(record_bytes),
                "byte_count": len(record_bytes),
            },
        },
        "historical_parent_binding": {
            "ratified_commit": record.ratified_commit,
            "resolution": "GIT_OBJECTS_AT_PARSED_COMMIT_NOT_CURRENT_WORKTREE",
            "artifacts_ordered": parent_bindings,
        },
        "test3_contract_self_check": contract,
        "runtime_identity_binding": runtime,
        "golden_fixture": fixture,
    }


def render_binding_document(helpers: GovernedHelpers, payload: Mapping[str, Any]) -> bytes:
    canonical_payload = helpers.canonical_json_bytes(payload)
    document = {
        "schema": SCHEMA,
        "payload": payload,
        "payload_sha256": helpers.sha256_bytes(canonical_payload),
    }
    return helpers.canonical_json_bytes(document)


# --------------------------------------------------------------------------
# Closed arguments and output-path discipline
# --------------------------------------------------------------------------


def parse_arguments(argv: Sequence[str]) -> tuple[str, str]:
    """Accept exactly ``<mode> --output <path>`` and nothing else.

    Only the shape is decided here; every mode then accepts exactly one output
    value, the frozen ``BINDING_RELATIVE_PATH``, enforced by
    :func:`resolve_output_path`.
    """

    arguments = list(argv)
    if len(arguments) != 3:
        raise PreparationError(
            "ARGUMENTS_NONCONFORMING",
            "exactly one mode and one --output value are required",
        )
    mode, flag, output = arguments
    if mode not in MODES:
        raise PreparationError(
            "ARGUMENTS_NONCONFORMING", f"mode must be one of {'|'.join(MODES)}"
        )
    if flag != OUTPUT_FLAG:
        raise PreparationError("ARGUMENTS_NONCONFORMING", "the only accepted flag is --output")
    if not output or output.strip() != output:
        raise PreparationError("ARGUMENTS_NONCONFORMING", "--output value is malformed")
    return mode, output


@dataclass(frozen=True)
class OutputTarget:
    """The one authorized output, kept as repository root plus exact relative path."""

    repo_root: Path
    relative_path: str
    parent_parts: tuple[str, ...]
    name: str
    path: Path


def _output_fail(detail: str) -> PreparationError:
    return PreparationError("OUTPUT_PATH_NONCONFORMING", detail)


@contextmanager
def opened_output_parent(repo_root: Path, parent_parts: Sequence[str]) -> Iterator[int]:
    """Walk to the output parent by descriptor, never following a symlink.

    Every component is opened relative to the previously opened descriptor with
    ``O_NOFOLLOW`` and ``O_DIRECTORY`` where the platform supports them, so a
    parent swapped between validation and creation cannot redirect the write.
    """

    if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
        raise _output_fail("descriptor-rooted output traversal is unavailable")
    if repo_root.is_symlink():
        raise _output_fail("repository root is a symlink")
    try:
        current = os.open(repo_root, _DIRECTORY_OPEN_FLAGS)
    except OSError as exc:
        raise _output_fail(f"cannot open the repository root: {type(exc).__name__}") from None
    try:
        root_info = os.fstat(current)
        if not stat.S_ISDIR(root_info.st_mode):
            raise _output_fail("repository root is not a directory")
        for component in parent_parts:
            if not component or component in {".", ".."} or "/" in component:
                raise _output_fail("output parent component is nonconforming")
            try:
                entry = os.stat(component, dir_fd=current, follow_symlinks=False)
            except OSError:
                raise _output_fail("output parent directory is absent") from None
            if stat.S_ISLNK(entry.st_mode):
                raise _output_fail("symlinked output parent component is refused")
            if not stat.S_ISDIR(entry.st_mode):
                raise _output_fail("output parent component is not a directory")
            try:
                opened = os.open(component, _DIRECTORY_OPEN_FLAGS, dir_fd=current)
            except OSError as exc:
                raise _output_fail(
                    f"cannot open the output parent component: {type(exc).__name__}"
                ) from None
            os.close(current)
            current = opened
            info = os.fstat(current)
            if not stat.S_ISDIR(info.st_mode):
                raise _output_fail("output parent component is not a directory")
            if info.st_dev != root_info.st_dev:
                raise _output_fail("output parent leaves the repository device")
        yield current
    finally:
        os.close(current)


def resolve_output_path(repo_root: Path, raw_output: str) -> OutputTarget:
    """Accept only the one exact authorized relative path, resolved by descriptor."""

    if raw_output != BINDING_RELATIVE_PATH:
        raise _output_fail("the only accepted output is the exact authorized binding path")
    parts = tuple(BINDING_RELATIVE_PATH.split("/"))
    parent_parts, name = parts[:-1], parts[-1]
    with opened_output_parent(repo_root, parent_parts) as parent_fd:
        try:
            entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            entry = None
        except OSError as exc:
            raise _output_fail(
                f"cannot inspect the binding artifact: {type(exc).__name__}"
            ) from None
        if entry is not None:
            if stat.S_ISLNK(entry.st_mode):
                raise _output_fail("output path is a symlink")
            if not stat.S_ISREG(entry.st_mode):
                raise _output_fail("output path is not a regular file")
    return OutputTarget(
        repo_root=repo_root,
        relative_path=BINDING_RELATIVE_PATH,
        parent_parts=parent_parts,
        name=name,
        path=repo_root.joinpath(*parts),
    )


def output_exists(target: OutputTarget) -> bool:
    """Report presence of the exact output entry without following any symlink."""

    with opened_output_parent(target.repo_root, target.parent_parts) as parent_fd:
        try:
            os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise _output_fail(
                f"cannot inspect the binding artifact: {type(exc).__name__}"
            ) from None
        return True


def _read_from_parent(parent_fd: int, name: str) -> bytes:
    flags = _FILE_READ_FLAGS
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        raise PreparationError("OUTPUT_MISSING", "the binding artifact is absent") from None
    except OSError as exc:
        raise _output_fail(
            f"cannot open the binding artifact: {type(exc).__name__}"
        ) from None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise _output_fail("the binding artifact is not a regular file")
        if info.st_size > MAX_BINDING_BYTES:
            raise _output_fail("the binding artifact exceeds the frozen byte ceiling")
        chunks: list[bytes] = []
        total = 0
        while True:
            try:
                chunk = os.read(descriptor, 65536)
            except OSError:
                raise _output_fail("cannot read the binding artifact") from None
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BINDING_BYTES:
                raise _output_fail("the binding artifact exceeds the frozen byte ceiling")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def read_output_bytes(target: OutputTarget) -> bytes:
    """Read the existing artifact through the same no-symlink descriptor root."""

    with opened_output_parent(target.repo_root, target.parent_parts) as parent_fd:
        return _read_from_parent(parent_fd, target.name)


def write_exclusive(target: OutputTarget, content: bytes) -> None:
    """Create the single artifact exclusively, relative to the safely opened parent.

    The parent is re-walked by descriptor at write time, the final entry is
    created with ``O_EXCL`` and ``O_NOFOLLOW`` relative to that descriptor, an
    existing artifact is never overwritten, and every descriptor is closed on
    every path.
    """

    with opened_output_parent(target.repo_root, target.parent_parts) as parent_fd:
        try:
            descriptor = os.open(target.name, _FILE_CREATE_FLAGS, _OUTPUT_MODE, dir_fd=parent_fd)
        except FileExistsError:
            raise PreparationError(
                "OUTPUT_EXISTS", "the binding artifact already exists and is never overwritten"
            ) from None
        except OSError as exc:
            raise _output_fail(
                f"cannot create the binding artifact: {type(exc).__name__}"
            ) from None
        try:
            stream = os.fdopen(descriptor, "wb")
        except OSError:
            os.close(descriptor)
            raise _output_fail("cannot open the created binding artifact") from None
        try:
            with stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError:
            raise _output_fail("cannot write the binding artifact") from None
        if _read_from_parent(parent_fd, target.name) != content:
            raise PreparationError(
                "BINDING_MISMATCH", "written binding bytes do not match the generated bytes"
            )


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------


def run_check(repo_root: Path, output: OutputTarget, helpers: GovernedHelpers) -> str:
    if output_exists(output):
        raise PreparationError(
            "OUTPUT_EXISTS", "check runs only before the exclusive create of the artifact"
        )
    payload = build_binding_payload(repo_root, helpers)
    render_binding_document(helpers, payload)
    return "CHECK_PASS"


def run_create(repo_root: Path, output: OutputTarget, helpers: GovernedHelpers) -> str:
    if output_exists(output):
        raise PreparationError(
            "OUTPUT_EXISTS", "the binding artifact already exists and is never overwritten"
        )
    payload = build_binding_payload(repo_root, helpers)
    write_exclusive(output, render_binding_document(helpers, payload))
    return "CREATE_PASS"


def run_verify_existing(repo_root: Path, output: OutputTarget, helpers: GovernedHelpers) -> str:
    content = read_output_bytes(output)
    document = _guarded(
        "BINDING_NONCANONICAL", "binding artifact is not valid JSON", json.loads, content
    )
    if not isinstance(document, dict) or set(document) != {"schema", "payload", "payload_sha256"}:
        raise PreparationError("BINDING_NONCANONICAL", "binding artifact structure is unexpected")
    if helpers.canonical_json_bytes(document) != content:
        raise PreparationError(
            "BINDING_NONCANONICAL", "binding artifact bytes are not canonical JSON"
        )
    if document["schema"] != SCHEMA:
        raise PreparationError("BINDING_MISMATCH", "binding artifact schema is unexpected")

    recorded_payload = document["payload"]
    if not isinstance(recorded_payload, dict):
        raise PreparationError("BINDING_NONCANONICAL", "binding payload is not an object")
    recorded_canonical = helpers.canonical_json_bytes(recorded_payload)
    if helpers.sha256_bytes(recorded_canonical) != document["payload_sha256"]:
        raise PreparationError(
            "BINDING_MISMATCH", "recorded payload digest does not match the recorded payload"
        )
    if recorded_payload.get("classification") != CLASSIFICATION:
        raise PreparationError("BINDING_MISMATCH", "binding classification is nonconforming")

    current_canonical = helpers.canonical_json_bytes(build_binding_payload(repo_root, helpers))
    if current_canonical != recorded_canonical:
        raise PreparationError(
            "BINDING_MISMATCH", "recomputed binding payload differs from the recorded payload"
        )
    return "VERIFY_EXISTING_PASS"


MODE_RUNNERS: Mapping[str, Callable[[Path, OutputTarget, GovernedHelpers], str]] = {
    "check": run_check,
    "create": run_create,
    "verify-existing": run_verify_existing,
}


def execute_mode(
    mode: str, repo_root: Path, output: OutputTarget, helpers: GovernedHelpers
) -> str:
    runner = MODE_RUNNERS.get(mode)
    if runner is None:
        raise PreparationError("ARGUMENTS_NONCONFORMING", f"unsupported mode: {mode}")
    return runner(repo_root, output, helpers)


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        with governed_runtime_tripwires():
            mode, raw_output = parse_arguments(arguments)
            repo_root = repository_root()
            output = resolve_output_path(repo_root, raw_output)
            helpers = load_governed_helpers(repo_root)
            status = execute_mode(mode, repo_root, output, helpers)
    except PreparationError as error:
        sys.stderr.write(f"{TOOL_NAME}: {error.code}: {error.detail}\n")
        return 2
    except Exception as error:  # stable governed surface, never a raw traceback  # noqa: BLE001
        sys.stderr.write(f"{TOOL_NAME}: INTERNAL_NONCONFORMANCE: {type(error).__name__}\n")
        return 2
    sys.stdout.write(f"{TOOL_NAME}: {status}: {CLASSIFICATION}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

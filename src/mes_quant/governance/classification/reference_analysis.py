from __future__ import annotations

from dataclasses import dataclass
import posixpath
import re
from typing import Any, Iterable

from .reference_graph import (
    BidirectionalGraphAnalysis,
    analyze_bidirectional_graph,
)
from .reference_objects import (
    TrackedObject,
    list_tracked_objects,
    read_blob_bytes,
)
from .reference_parsers import (
    ReferenceParseError,
    StaticReference,
    parse_reference_file,
    reference_file_type,
)
from .reference_resolution import (
    PythonModuleIndex,
    ReferenceResolutionError,
    build_python_module_index,
    protected_module_nodes,
    resolve_module_reference,
)


_PROTECTED_SYMBOL_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*:"
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)


class ReferenceAnalysisError(RuntimeError):
    """Raised when a mandatory repository reference scan cannot complete."""


@dataclass(frozen=True, order=True)
class AnalysisUnresolvedNode:
    path_bytes: bytes
    reason_code: str
    reference_kind: str


@dataclass(frozen=True)
class ReferenceScanSummary:
    scan_complete: bool
    scanned_tracked_objects: int
    supported_reference_files: int
    unsupported_reference_files: int
    failed_reference_files: int


@dataclass(frozen=True)
class ReferenceSnapshotAnalysis:
    reference_scan_summary: ReferenceScanSummary
    graph_analysis: BidirectionalGraphAnalysis
    unresolved_nodes: tuple[AnalysisUnresolvedNode, ...]
    unsupported_reference_file_types: tuple[str, ...]
    protected_nodes: tuple[bytes, ...]
    graph_node_count: int = 0
    graph_edge_count: int = 0


def _limit(
    limits: dict[str, Any],
    name: str,
    *,
    allow_zero: bool = False,
) -> int:
    value = limits.get(name)
    minimum = 0 if allow_zero else 1

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
    ):
        raise ReferenceAnalysisError(
            f"invalid governed analyzer limit: {name}"
        )

    return value


def _ascii_manifest_bytes(values: Iterable[str]) -> tuple[bytes, ...]:
    result: list[bytes] = []

    for value in values:
        if not isinstance(value, str):
            raise ReferenceAnalysisError(
                "manifest path entry must be string"
            )

        try:
            result.append(value.encode("ascii"))
        except UnicodeEncodeError as exc:
            raise ReferenceAnalysisError(
                "manifest path entries must be ASCII"
            ) from exc

    return tuple(result)


def _matches_exact_or_prefix(
    path: bytes,
    *,
    exact: tuple[bytes, ...],
    prefixes: tuple[bytes, ...],
) -> bool:
    return (
        path in exact
        or any(path.startswith(prefix) for prefix in prefixes)
    )


def _protected_path_nodes(
    tracked_objects: tuple[TrackedObject, ...],
    manifest: dict[str, Any],
) -> set[bytes]:
    quant_exact = _ascii_manifest_bytes(
        manifest["protected_quant_exact_paths"]
    )
    quant_prefixes = _ascii_manifest_bytes(
        manifest["protected_quant_prefixes"]
    )
    artifact_prefixes = _ascii_manifest_bytes(
        manifest["protected_artifact_prefixes"]
    )
    schema_prefixes = _ascii_manifest_bytes(
        manifest["protected_schema_prefixes"]
    )

    protected: set[bytes] = set()

    for item in tracked_objects:
        path = item.path_bytes

        if _matches_exact_or_prefix(
            path,
            exact=quant_exact,
            prefixes=(
                *quant_prefixes,
                *artifact_prefixes,
                *schema_prefixes,
            ),
        ):
            protected.add(path)

    return protected


def _protected_symbol_nodes(
    protected_symbols: Iterable[str],
    module_index: PythonModuleIndex,
) -> set[bytes]:
    """Resolve protected symbol authorities to their exact module nodes."""

    protected: set[bytes] = set()

    for symbol in protected_symbols:
        if (
            not isinstance(symbol, str)
            or _PROTECTED_SYMBOL_RE.fullmatch(
                symbol
            )
            is None
        ):
            raise ReferenceAnalysisError(
                "invalid protected symbol identity: "
                f"{symbol!r}"
            )

        module_name, _qualname = (
            symbol.split(":", 1)
        )

        paths = resolve_module_reference(
            module_name,
            module_index,
        )

        if not paths:
            raise ReferenceAnalysisError(
                "protected symbol module cannot be resolved: "
                f"{module_name}"
            )

        # V1 conservatively protects the containing module node.
        protected.update(paths)

    return protected

def _unsupported_reference_type(path: bytes) -> str | None:
    """Identify readable file types that can consume references but lack a parser."""

    if path.startswith(b".github/workflows/") and path.endswith(
        (b".yaml", b".yml")
    ):
        return "github-actions-yaml"

    if path.endswith((b".yaml", b".yml")):
        return "yaml"

    if path.endswith((b".sh", b".bash", b".zsh")):
        return "shell"

    basename = path.rsplit(b"/", 1)[-1]

    if basename in {
        b"Dockerfile",
        b"Containerfile",
        b"Makefile",
        b"makefile",
        b"GNUmakefile",
    }:
        return "build-system"

    if (
        basename == b".gitmodules"
        or basename.startswith(b".env")
        or path.endswith((b".ini", b".cfg"))
    ):
        return "package-config"

    return None


def _local_module_roots(
    module_index: PythonModuleIndex,
) -> frozenset[str]:
    return frozenset(
        module.split(".", 1)[0]
        for module in module_index.module_to_paths
    )


def _canonical_repository_path(
    raw_path: bytes,
) -> bytes | None:
    """Normalize POSIX separators only; never normalize Unicode or case."""

    if (
        not raw_path
        or b"\x00" in raw_path
        or raw_path.startswith(b"/")
    ):
        return None

    normalized = posixpath.normpath(raw_path)

    if (
        normalized in {b".", b".."}
        or normalized.startswith(b"../")
        or normalized.startswith(b"/")
    ):
        return None

    return normalized


def _resolve_path_literal(
    value: str,
    tracked_paths: frozenset[bytes],
    *,
    source_path: bytes,
) -> tuple[bytes, ...]:
    """Resolve both repository-root and source-relative inert path facts."""

    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError:
        return ()

    candidates: set[bytes] = set()

    direct = _canonical_repository_path(raw)

    if direct is not None:
        candidates.add(direct)

    if raw.startswith(b"./"):
        stripped = _canonical_repository_path(
            raw[2:]
        )

        if stripped is not None:
            candidates.add(stripped)

    source_directory = posixpath.dirname(
        source_path
    )

    source_relative = _canonical_repository_path(
        posixpath.join(
            source_directory,
            raw,
        )
    )

    if source_relative is not None:
        candidates.add(source_relative)

    return tuple(
        sorted(
            candidate
            for candidate in candidates
            if candidate in tracked_paths
        )
    )


def _resolve_relative_module_name(
    value: str,
    *,
    source_path: bytes,
    module_index: PythonModuleIndex,
) -> str | None:
    """Resolve a Python relative-import identity from the actual Git tree."""

    if not value.startswith("."):
        return value

    level = len(value) - len(
        value.lstrip(".")
    )
    remainder = value[level:]

    source_module = (
        module_index.path_to_module.get(
            source_path
        )
    )

    if source_module is None:
        return None

    if (
        source_path == b"__init__.py"
        or source_path.endswith(
            b"/__init__.py"
        )
    ):
        package_parts = source_module.split(".")
    else:
        package_parts = (
            source_module.split(".")[:-1]
        )

    if not package_parts:
        return None

    ascend = level - 1

    if ascend >= len(package_parts):
        return None

    if ascend:
        package_parts = package_parts[
            : len(package_parts) - ascend
        ]

    if remainder:
        package_parts.extend(
            remainder.split(".")
        )

    resolved = ".".join(package_parts)

    return resolved or None



def _reference_targets(
    reference: StaticReference,
    *,
    source_path: bytes,
    tracked_paths: frozenset[bytes],
    module_index: PythonModuleIndex,
    local_roots: frozenset[str],
) -> tuple[tuple[bytes, ...], bool]:
    """Return resolved target paths and whether a local reference was unresolved."""

    if reference.reference_kind in {
        "MODULE_NAME",
        "IMPORT",
    }:
        value = reference.value

        if (
            reference.reference_kind == "IMPORT"
            and value.startswith(".")
        ):
            resolved_relative = (
                _resolve_relative_module_name(
                    value,
                    source_path=source_path,
                    module_index=module_index,
                )
            )

            if resolved_relative is None:
                return (), True

            value = resolved_relative

        paths = resolve_module_reference(
            value,
            module_index,
        )

        if paths:
            return paths, False

        root = value.split(".", 1)[0]

        return (), root in local_roots

    if reference.reference_kind == "SYMBOL_NAME":
        if ":" not in reference.value:
            return (), True

        module_name, qualname = (
            reference.value.split(":", 1)
        )

        if module_name.startswith("."):
            resolved_relative = (
                _resolve_relative_module_name(
                    module_name,
                    source_path=source_path,
                    module_index=module_index,
                )
            )

            if resolved_relative is None:
                return (), True

            module_name = resolved_relative

        resolved_paths: set[bytes] = set(
            resolve_module_reference(
                module_name,
                module_index,
            )
        )

        first_qualname_component = (
            qualname.split(".", 1)[0]
        )

        possible_submodule = (
            f"{module_name}."
            f"{first_qualname_component}"
        )

        resolved_paths.update(
            resolve_module_reference(
                possible_submodule,
                module_index,
            )
        )

        if resolved_paths:
            return (
                tuple(sorted(resolved_paths)),
                False,
            )

        root = module_name.split(".", 1)[0]

        return (), root in local_roots

    if reference.reference_kind == "PATH_LITERAL":
        paths = _resolve_path_literal(
            reference.value,
            tracked_paths,
            source_path=source_path,
        )

        return paths, False

    return (), False


def analyze_reference_snapshot(
    repo: str,
    *,
    commit_sha1: str,
    changed_nodes: Iterable[bytes],
    manifest: dict[str, Any],
    limits: dict[str, Any],
) -> ReferenceSnapshotAnalysis:
    """Analyze one immutable repository snapshot as hostile inert data."""

    max_tracked_objects = _limit(
        limits,
        "max_tracked_objects",
    )
    max_blob_bytes = _limit(
        limits,
        "max_blob_bytes",
    )
    max_ast_nodes = _limit(
        limits,
        "max_ast_nodes",
    )
    max_parse_depth = _limit(
        limits,
        "max_parse_depth",
    )
    max_config_nesting_depth = _limit(
        limits,
        "max_config_nesting_depth",
    )
    max_scalar_bytes = _limit(
        limits,
        "max_scalar_bytes",
    )
    max_collection_cardinality = _limit(
        limits,
        "max_collection_cardinality",
    )
    max_graph_nodes = _limit(
        limits,
        "max_graph_nodes",
    )
    max_graph_edges = _limit(
        limits,
        "max_graph_edges",
        allow_zero=True,
    )
    max_unresolved_nodes = _limit(
        limits,
        "max_unresolved_nodes",
        allow_zero=True,
    )
    max_unsupported_types = _limit(
        limits,
        "max_unsupported_reference_file_types",
    )

    tracked_objects = list_tracked_objects(
        repo,
        commit_sha1=commit_sha1,
        max_tracked_objects=max_tracked_objects,
    )

    tracked_paths = frozenset(
        item.path_bytes
        for item in tracked_objects
    )

    module_index = build_python_module_index(
        tracked_objects
    )
    local_roots = _local_module_roots(
        module_index
    )

    protected: set[bytes] = _protected_path_nodes(
        tracked_objects,
        manifest,
    )

    try:
        protected.update(
            protected_module_nodes(
                manifest["protected_quant_modules"],
                module_index,
            )
        )
    except ReferenceResolutionError as exc:
        raise ReferenceAnalysisError(
            "protected module resolution failed"
        ) from exc

    protected.update(
        _protected_symbol_nodes(
            manifest["protected_symbols"],
            module_index,
        )
    )

    adjacency: dict[bytes, set[bytes]] = {
        path: set()
        for path in tracked_paths
    }

    unresolved: set[AnalysisUnresolvedNode] = set()
    unsupported_types: set[str] = set()

    supported_files = 0
    unsupported_files = 0

    for item in tracked_objects:
        path = item.path_bytes

        if item.mode == "160000":
            unresolved.add(
                AnalysisUnresolvedNode(
                    path_bytes=path,
                    reason_code="UNRESOLVED_REFERENCE",
                    reference_kind="LOCAL_DEPENDENCY",
                )
            )
            continue

        if item.object_type != "blob":
            raise ReferenceAnalysisError(
                "non-gitlink tracked object must be a blob"
            )

        data = read_blob_bytes(
            repo,
            blob_sha1=item.object_sha1,
            max_blob_bytes=max_blob_bytes,
        )

        if item.mode == "120000":
            targets = _resolve_path_literal(
                data.decode("utf-8", "surrogateescape"),
                tracked_paths,
                source_path=path,
            )
            adjacency[path].update(targets)

            if not targets:
                unresolved.add(
                    AnalysisUnresolvedNode(
                        path_bytes=path,
                        reason_code="UNRESOLVED_REFERENCE",
                        reference_kind="PATH_LITERAL",
                    )
                )

            continue

        file_type = reference_file_type(path)

        if file_type in {"PYTHON", "JSON", "TOML"}:
            try:
                parsed = parse_reference_file(
                    path,
                    data,
                    max_ast_nodes=max_ast_nodes,
                    max_parse_depth=max_parse_depth,
                    max_config_nesting_depth=(
                        max_config_nesting_depth
                    ),
                    max_scalar_bytes=max_scalar_bytes,
                    max_collection_cardinality=max_collection_cardinality,
                )
            except ReferenceParseError as exc:
                raise ReferenceAnalysisError(
                    f"mandatory reference parse failed for {path!r}"
                ) from exc

            supported_files += 1

            for entry in parsed.unresolved:
                unresolved.add(
                    AnalysisUnresolvedNode(
                        path_bytes=path,
                        reason_code=entry.reason_code,
                        reference_kind=entry.reference_kind,
                    )
                )

            for reference in parsed.references:
                targets, unresolved_local = _reference_targets(
                    reference,
                    source_path=path,
                    tracked_paths=tracked_paths,
                    module_index=module_index,
                    local_roots=local_roots,
                )

                adjacency[path].update(targets)

                if unresolved_local:
                    unresolved.add(
                        AnalysisUnresolvedNode(
                            path_bytes=path,
                            reason_code="UNRESOLVED_MODULE",
                            reference_kind=reference.reference_kind,
                        )
                    )

            continue

        unsupported_type = _unsupported_reference_type(
            path
        )

        if unsupported_type is not None:
            unsupported_files += 1
            unsupported_types.add(unsupported_type)

            if len(unsupported_types) > max_unsupported_types:
                raise ReferenceAnalysisError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    "max_unsupported_reference_file_types="
                    f"{max_unsupported_types}"
                )

    if len(unresolved) > max_unresolved_nodes:
        raise ReferenceAnalysisError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_unresolved_nodes={max_unresolved_nodes}"
        )

    changed = tuple(
        sorted(set(changed_nodes))
    )

    if not changed:
        raise ReferenceAnalysisError(
            "at least one changed node is required"
        )

    unresolved_paths = tuple(
        sorted(
            {
                node.path_bytes
                for node in unresolved
            }
        )
    )

    canonical_adjacency = {
        source: tuple(sorted(targets))
        for source, targets in sorted(
            adjacency.items()
        )
    }

    graph_nodes: set[bytes] = set(
        canonical_adjacency
    )

    graph_edge_count = 0

    for targets in canonical_adjacency.values():
        graph_nodes.update(targets)
        graph_edge_count += len(targets)

    graph_nodes.update(changed)
    graph_nodes.update(protected)
    graph_nodes.update(unresolved_paths)

    graph_node_count = len(graph_nodes)

    if graph_node_count > max_graph_nodes:
        raise ReferenceAnalysisError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_nodes={max_graph_nodes}"
        )

    if graph_edge_count > max_graph_edges:
        raise ReferenceAnalysisError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_edges={max_graph_edges}"
        )

    graph_analysis = analyze_bidirectional_graph(
        canonical_adjacency,
        changed_nodes=changed,
        protected_nodes=tuple(sorted(protected)),
        unresolved_nodes=unresolved_paths,
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
        max_unresolved_nodes=max_unresolved_nodes,
    )

    return ReferenceSnapshotAnalysis(
        reference_scan_summary=ReferenceScanSummary(
            scan_complete=True,
            scanned_tracked_objects=len(tracked_objects),
            supported_reference_files=supported_files,
            unsupported_reference_files=unsupported_files,
            failed_reference_files=0,
        ),
        graph_analysis=graph_analysis,
        unresolved_nodes=tuple(sorted(unresolved)),
        unsupported_reference_file_types=tuple(
            sorted(unsupported_types)
        ),
        protected_nodes=tuple(sorted(protected)),
        graph_node_count=graph_node_count,
        graph_edge_count=graph_edge_count,
    )

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


class ReferenceGraphError(RuntimeError):
    """Raised when bounded reference-graph analysis cannot complete safely."""


@dataclass(frozen=True)
class ClosureSummary:
    reachable_protected: bool
    unresolved_count: int
    visited_nodes: int
    visited_edges: int


@dataclass(frozen=True)
class BidirectionalGraphAnalysis:
    forward: ClosureSummary
    reverse: ClosureSummary


def _positive_integer(value: int, name: str) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise ReferenceGraphError(
            f"{name} must be a positive integer"
        )


def _nonnegative_integer(
    value: int,
    name: str,
) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise ReferenceGraphError(
            f"{name} must be a non-negative integer"
        )


def _validate_node(node: bytes) -> bytes:
    if not isinstance(node, bytes) or not node:
        raise ReferenceGraphError(
            "graph nodes must be non-empty raw Git path bytes"
        )

    return node


def _canonical_graph(
    adjacency: Mapping[bytes, Iterable[bytes]],
    *,
    extra_nodes: Iterable[bytes],
    max_graph_nodes: int,
    max_graph_edges: int,
) -> dict[bytes, tuple[bytes, ...]]:
    nodes: set[bytes] = set()
    edges: set[tuple[bytes, bytes]] = set()

    for source, targets in adjacency.items():
        source = _validate_node(source)
        nodes.add(source)

        for target in targets:
            target = _validate_node(target)
            nodes.add(target)
            edges.add((source, target))

            if len(edges) > max_graph_edges:
                raise ReferenceGraphError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    f"max_graph_edges={max_graph_edges}"
                )

        if len(nodes) > max_graph_nodes:
            raise ReferenceGraphError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_graph_nodes={max_graph_nodes}"
            )

    for node in extra_nodes:
        nodes.add(_validate_node(node))

        if len(nodes) > max_graph_nodes:
            raise ReferenceGraphError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_graph_nodes={max_graph_nodes}"
            )

    canonical: dict[bytes, list[bytes]] = {
        node: []
        for node in sorted(nodes)
    }

    for source, target in sorted(edges):
        canonical[source].append(target)

    return {
        node: tuple(targets)
        for node, targets in canonical.items()
    }


def _reverse_graph(
    graph: Mapping[bytes, tuple[bytes, ...]],
) -> dict[bytes, tuple[bytes, ...]]:
    reverse: dict[bytes, list[bytes]] = {
        node: []
        for node in graph
    }

    for source in sorted(graph):
        for target in graph[source]:
            reverse[target].append(source)

    return {
        node: tuple(sorted(sources))
        for node, sources in reverse.items()
    }


def _closure(
    graph: Mapping[bytes, tuple[bytes, ...]],
    *,
    starts: tuple[bytes, ...],
    targets: frozenset[bytes],
    unresolved_nodes: frozenset[bytes],
    max_graph_nodes: int,
    max_graph_edges: int,
    max_unresolved_nodes: int,
) -> ClosureSummary:
    visited: set[bytes] = set()
    unresolved_seen: set[bytes] = set()
    visited_edges = 0

    stack = list(reversed(sorted(starts)))

    while stack:
        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)

        if len(visited) > max_graph_nodes:
            raise ReferenceGraphError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_graph_nodes={max_graph_nodes}"
            )

        if node in unresolved_nodes:
            unresolved_seen.add(node)

            if len(unresolved_seen) > max_unresolved_nodes:
                raise ReferenceGraphError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    f"max_unresolved_nodes={max_unresolved_nodes}"
                )

        for target in graph.get(node, ()):
            visited_edges += 1

            if visited_edges > max_graph_edges:
                raise ReferenceGraphError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    f"max_graph_edges={max_graph_edges}"
                )

            if target not in visited:
                stack.append(target)

    return ClosureSummary(
        reachable_protected=bool(
            visited.intersection(targets)
        ),
        unresolved_count=len(unresolved_seen),
        visited_nodes=len(visited),
        visited_edges=visited_edges,
    )


def analyze_bidirectional_graph(
    adjacency: Mapping[bytes, Iterable[bytes]],
    *,
    changed_nodes: Iterable[bytes],
    protected_nodes: Iterable[bytes],
    unresolved_nodes: Iterable[bytes] = (),
    max_graph_nodes: int,
    max_graph_edges: int,
    max_unresolved_nodes: int,
) -> BidirectionalGraphAnalysis:
    """Run deterministic bounded forward and reverse reachability.

    Forward:
        changed node -> protected capability.

    Reverse:
        protected capability -> changed node.

    Candidate content is not executed here. Inputs are already-resolved
    inert graph facts produced by trusted analyzers.
    """

    _positive_integer(
        max_graph_nodes,
        "max_graph_nodes",
    )
    _nonnegative_integer(
        max_graph_edges,
        "max_graph_edges",
    )
    _nonnegative_integer(
        max_unresolved_nodes,
        "max_unresolved_nodes",
    )

    changed = tuple(
        sorted(
            {
                _validate_node(node)
                for node in changed_nodes
            }
        )
    )
    protected = tuple(
        sorted(
            {
                _validate_node(node)
                for node in protected_nodes
            }
        )
    )
    unresolved = frozenset(
        _validate_node(node)
        for node in unresolved_nodes
    )

    if not changed:
        raise ReferenceGraphError(
            "at least one changed node is required"
        )

    graph = _canonical_graph(
        adjacency,
        extra_nodes=(
            *changed,
            *protected,
            *unresolved,
        ),
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
    )

    forward = _closure(
        graph,
        starts=changed,
        targets=frozenset(protected),
        unresolved_nodes=unresolved,
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
        max_unresolved_nodes=max_unresolved_nodes,
    )

    reverse_result = _closure(
        graph,
        starts=protected,
        targets=frozenset(changed),
        unresolved_nodes=unresolved,
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
        max_unresolved_nodes=max_unresolved_nodes,
    )

    return BidirectionalGraphAnalysis(
        forward=forward,
        reverse=reverse_result,
    )

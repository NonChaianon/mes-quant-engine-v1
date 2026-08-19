from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .git_delta import DeltaEntry
from .reference_analysis import (
    AnalysisUnresolvedNode,
    ReferenceScanSummary,
    ReferenceSnapshotAnalysis,
    analyze_reference_snapshot,
)
from .reference_graph import (
    BidirectionalGraphAnalysis,
    ClosureSummary,
)


class ReferenceCandidateError(RuntimeError):
    """Raised when BASE/HEAD reference analysis cannot complete safely."""


@dataclass(frozen=True)
class ReferenceCandidateAnalysis:
    """Separate epoch analyses plus their conservative candidate projection."""

    base_changed_nodes: tuple[bytes, ...]
    head_changed_nodes: tuple[bytes, ...]
    base_snapshot: ReferenceSnapshotAnalysis | None
    head_snapshot: ReferenceSnapshotAnalysis | None
    combined: ReferenceSnapshotAnalysis


@dataclass(frozen=True)
class _CandidateBudgets:
    tracked_objects: int
    graph_nodes: int
    graph_edges: int
    unresolved_nodes: int


def _limit(
    limits: dict[str, Any],
    name: str,
) -> int:
    value = limits.get(name)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise ReferenceCandidateError(
            f"invalid governed analyzer limit: {name}"
        )

    return value


def _changed_nodes(
    canonical_tree_delta: Iterable[DeltaEntry],
) -> tuple[
    tuple[DeltaEntry, ...],
    tuple[bytes, ...],
    tuple[bytes, ...],
]:
    entries = tuple(canonical_tree_delta)

    if not entries:
        raise ReferenceCandidateError(
            "candidate tree delta must not be empty"
        )

    base_nodes: set[bytes] = set()
    head_nodes: set[bytes] = set()

    for entry in entries:
        if not isinstance(entry, DeltaEntry):
            raise ReferenceCandidateError(
                "canonical_tree_delta contains invalid entry"
            )

        if entry.old_path_bytes is not None:
            base_nodes.add(entry.old_path_bytes)

        if entry.new_path_bytes is not None:
            head_nodes.add(entry.new_path_bytes)

    if not base_nodes and not head_nodes:
        raise ReferenceCandidateError(
            "candidate delta contains no analyzable path"
        )

    return (
        entries,
        tuple(sorted(base_nodes)),
        tuple(sorted(head_nodes)),
    )


def _analyze_epoch(
    repo: str | Path,
    *,
    commit_sha1: str,
    changed_nodes: tuple[bytes, ...],
    manifest: dict[str, Any],
    limits: dict[str, Any],
    budgets: _CandidateBudgets,
) -> tuple[
    ReferenceSnapshotAnalysis | None,
    _CandidateBudgets,
]:
    if not changed_nodes:
        return None, budgets

    if budgets.tracked_objects < 1:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            "max_tracked_objects"
        )

    if budgets.graph_nodes < 1:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            "max_graph_nodes"
        )

    epoch_limits = dict(limits)
    epoch_limits["max_tracked_objects"] = (
        budgets.tracked_objects
    )
    epoch_limits["max_graph_nodes"] = (
        budgets.graph_nodes
    )
    epoch_limits["max_graph_edges"] = (
        budgets.graph_edges
    )
    epoch_limits["max_unresolved_nodes"] = (
        budgets.unresolved_nodes
    )

    analysis = analyze_reference_snapshot(
        str(repo),
        commit_sha1=commit_sha1,
        changed_nodes=changed_nodes,
        manifest=manifest,
        limits=epoch_limits,
    )

    consumed_tracked = (
        analysis.reference_scan_summary
        .scanned_tracked_objects
    )
    consumed_graph_nodes = (
        analysis.graph_node_count
    )
    consumed_graph_edges = (
        analysis.graph_edge_count
    )
    consumed_unresolved = len(
        analysis.unresolved_nodes
    )

    remaining = _CandidateBudgets(
        tracked_objects=(
            budgets.tracked_objects
            - consumed_tracked
        ),
        graph_nodes=(
            budgets.graph_nodes
            - consumed_graph_nodes
        ),
        graph_edges=(
            budgets.graph_edges
            - consumed_graph_edges
        ),
        unresolved_nodes=(
            budgets.unresolved_nodes
            - consumed_unresolved
        ),
    )

    if min(
        remaining.tracked_objects,
        remaining.graph_nodes,
        remaining.graph_edges,
        remaining.unresolved_nodes,
    ) < 0:
        raise ReferenceCandidateError(
            "candidate resource-budget accounting failure"
        )

    return analysis, remaining

def _combine_closure(
    summaries: tuple[ClosureSummary, ...],
    *,
    max_graph_nodes: int,
    max_graph_edges: int,
    max_unresolved_nodes: int,
) -> ClosureSummary:
    visited_nodes = sum(
        summary.visited_nodes
        for summary in summaries
    )
    visited_edges = sum(
        summary.visited_edges
        for summary in summaries
    )
    unresolved_count = sum(
        summary.unresolved_count
        for summary in summaries
    )

    if visited_nodes > max_graph_nodes:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_nodes={max_graph_nodes}"
        )

    if visited_edges > max_graph_edges:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_edges={max_graph_edges}"
        )

    if unresolved_count > max_unresolved_nodes:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_unresolved_nodes={max_unresolved_nodes}"
        )

    return ClosureSummary(
        reachable_protected=any(
            summary.reachable_protected
            for summary in summaries
        ),
        unresolved_count=unresolved_count,
        visited_nodes=visited_nodes,
        visited_edges=visited_edges,
    )


def _combine_snapshots(
    snapshots: tuple[ReferenceSnapshotAnalysis, ...],
    *,
    limits: dict[str, Any],
) -> ReferenceSnapshotAnalysis:
    if not snapshots:
        raise ReferenceCandidateError(
            "candidate analysis produced no snapshot"
        )

    max_tracked_objects = _limit(
        limits,
        "max_tracked_objects",
    )
    max_graph_nodes = _limit(
        limits,
        "max_graph_nodes",
    )
    max_graph_edges = _limit(
        limits,
        "max_graph_edges",
    )
    max_unresolved_nodes = _limit(
        limits,
        "max_unresolved_nodes",
    )
    max_unsupported_types = _limit(
        limits,
        "max_unsupported_reference_file_types",
    )

    graph_node_count = sum(
        snapshot.graph_node_count
        for snapshot in snapshots
    )
    graph_edge_count = sum(
        snapshot.graph_edge_count
        for snapshot in snapshots
    )
    unresolved_resource_count = sum(
        len(snapshot.unresolved_nodes)
        for snapshot in snapshots
    )

    if graph_node_count > max_graph_nodes:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_nodes={max_graph_nodes}"
        )

    if graph_edge_count > max_graph_edges:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_graph_edges={max_graph_edges}"
        )

    if unresolved_resource_count > max_unresolved_nodes:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_unresolved_nodes={max_unresolved_nodes}"
        )

    scanned = sum(
        snapshot.reference_scan_summary
        .scanned_tracked_objects
        for snapshot in snapshots
    )
    supported = sum(
        snapshot.reference_scan_summary
        .supported_reference_files
        for snapshot in snapshots
    )
    unsupported = sum(
        snapshot.reference_scan_summary
        .unsupported_reference_files
        for snapshot in snapshots
    )
    failed = sum(
        snapshot.reference_scan_summary
        .failed_reference_files
        for snapshot in snapshots
    )

    if scanned > max_tracked_objects:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_tracked_objects={max_tracked_objects}"
        )

    if supported > max_tracked_objects:
        raise ReferenceCandidateError(
            "supported-reference count exceeds "
            "candidate scan budget"
        )

    if unsupported > max_tracked_objects:
        raise ReferenceCandidateError(
            "unsupported-reference count exceeds "
            "candidate scan budget"
        )

    unresolved_nodes: set[
        AnalysisUnresolvedNode
    ] = set()

    unsupported_types: set[str] = set()
    protected_nodes: set[bytes] = set()

    for snapshot in snapshots:
        unresolved_nodes.update(
            snapshot.unresolved_nodes
        )
        unsupported_types.update(
            snapshot.unsupported_reference_file_types
        )
        protected_nodes.update(
            snapshot.protected_nodes
        )

    if len(unresolved_nodes) > max_unresolved_nodes:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_unresolved_nodes={max_unresolved_nodes}"
        )

    if len(unsupported_types) > max_unsupported_types:
        raise ReferenceCandidateError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            "max_unsupported_reference_file_types="
            f"{max_unsupported_types}"
        )

    forward = _combine_closure(
        tuple(
            snapshot.graph_analysis.forward
            for snapshot in snapshots
        ),
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
        max_unresolved_nodes=max_unresolved_nodes,
    )

    reverse = _combine_closure(
        tuple(
            snapshot.graph_analysis.reverse
            for snapshot in snapshots
        ),
        max_graph_nodes=max_graph_nodes,
        max_graph_edges=max_graph_edges,
        max_unresolved_nodes=max_unresolved_nodes,
    )

    return ReferenceSnapshotAnalysis(
        reference_scan_summary=ReferenceScanSummary(
            scan_complete=all(
                snapshot.reference_scan_summary
                .scan_complete
                for snapshot in snapshots
            ),
            scanned_tracked_objects=scanned,
            supported_reference_files=supported,
            unsupported_reference_files=unsupported,
            failed_reference_files=failed,
        ),
        graph_analysis=BidirectionalGraphAnalysis(
            forward=forward,
            reverse=reverse,
        ),
        unresolved_nodes=tuple(
            sorted(unresolved_nodes)
        ),
        unsupported_reference_file_types=tuple(
            sorted(unsupported_types)
        ),
        protected_nodes=tuple(
            sorted(protected_nodes)
        ),
        graph_node_count=graph_node_count,
        graph_edge_count=graph_edge_count,
    )


def analyze_reference_candidate(
    repo: str | Path,
    *,
    base_commit_sha1: str,
    head_commit_sha1: str,
    canonical_tree_delta: Iterable[DeltaEntry],
    manifest: dict[str, Any],
    limits: dict[str, Any],
) -> ReferenceCandidateAnalysis:
    """Analyze BASE and HEAD independently, then combine conservatively.

    The two epoch graphs are never unioned. A protected or unresolved
    condition observed in either exact snapshot survives in the combined
    candidate result.
    """

    (
        _entries,
        base_changed_nodes,
        head_changed_nodes,
    ) = _changed_nodes(
        canonical_tree_delta
    )

    budgets = _CandidateBudgets(
        tracked_objects=_limit(
            limits,
            "max_tracked_objects",
        ),
        graph_nodes=_limit(
            limits,
            "max_graph_nodes",
        ),
        graph_edges=_limit(
            limits,
            "max_graph_edges",
        ),
        unresolved_nodes=_limit(
            limits,
            "max_unresolved_nodes",
        ),
    )

    base_snapshot, budgets = _analyze_epoch(
        repo,
        commit_sha1=base_commit_sha1,
        changed_nodes=base_changed_nodes,
        manifest=manifest,
        limits=limits,
        budgets=budgets,
    )

    head_snapshot, budgets = _analyze_epoch(
        repo,
        commit_sha1=head_commit_sha1,
        changed_nodes=head_changed_nodes,
        manifest=manifest,
        limits=limits,
        budgets=budgets,
    )

    snapshots = tuple(
        snapshot
        for snapshot in (
            base_snapshot,
            head_snapshot,
        )
        if snapshot is not None
    )

    combined = _combine_snapshots(
        snapshots,
        limits=limits,
    )

    return ReferenceCandidateAnalysis(
        base_changed_nodes=base_changed_nodes,
        head_changed_nodes=head_changed_nodes,
        base_snapshot=base_snapshot,
        head_snapshot=head_snapshot,
        combined=combined,
    )

from __future__ import annotations

from pathlib import Path
import random
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.reference_graph import (
    ReferenceGraphError,
    analyze_bidirectional_graph,
)


LIMITS = {
    "max_graph_nodes": 100,
    "max_graph_edges": 100,
    "max_unresolved_nodes": 100,
}


class ReferenceGraphTests(unittest.TestCase):
    def test_forward_closure_reaches_protected_capability(self) -> None:
        result = analyze_bidirectional_graph(
            {
                b"ui.py": (b"adapter.py",),
                b"adapter.py": (b"src/mes_quant/features/builder.py",),
            },
            changed_nodes=(b"ui.py",),
            protected_nodes=(b"src/mes_quant/features/builder.py",),
            **LIMITS,
        )

        self.assertTrue(result.forward.reachable_protected)
        self.assertEqual(result.forward.visited_nodes, 3)
        self.assertEqual(result.forward.visited_edges, 2)

    def test_reverse_protected_reachability_reaches_changed_node(self) -> None:
        result = analyze_bidirectional_graph(
            {
                b"src/mes_quant/features/builder.py": (b"adapter.py",),
                b"adapter.py": (b"ui.py",),
            },
            changed_nodes=(b"ui.py",),
            protected_nodes=(b"src/mes_quant/features/builder.py",),
            **LIMITS,
        )

        self.assertFalse(result.forward.reachable_protected)
        self.assertTrue(result.reverse.reachable_protected)

    def test_disconnected_graph_proves_no_reachability(self) -> None:
        result = analyze_bidirectional_graph(
            {
                b"ui.py": (b"view.py",),
                b"src/mes_quant/features/builder.py": (b"quant_helper.py",),
            },
            changed_nodes=(b"ui.py",),
            protected_nodes=(b"src/mes_quant/features/builder.py",),
            **LIMITS,
        )

        self.assertFalse(result.forward.reachable_protected)
        self.assertFalse(result.reverse.reachable_protected)
        self.assertEqual(result.forward.unresolved_count, 0)
        self.assertEqual(result.reverse.unresolved_count, 0)

    def test_unresolved_nodes_are_counted_in_reachable_closure(self) -> None:
        result = analyze_bidirectional_graph(
            {
                b"ui.py": (b"dynamic.py",),
            },
            changed_nodes=(b"ui.py",),
            protected_nodes=(b"protected.py",),
            unresolved_nodes=(b"dynamic.py",),
            **LIMITS,
        )

        self.assertEqual(result.forward.unresolved_count, 1)
        self.assertFalse(result.forward.reachable_protected)

    def test_result_is_deterministic_under_input_reordering(self) -> None:
        edges = [
            (b"a.py", b"b.py"),
            (b"a.py", b"c.py"),
            (b"b.py", b"protected.py"),
            (b"c.py", b"d.py"),
        ]

        expected = None

        for seed in range(50):
            shuffled = list(edges)
            random.Random(seed).shuffle(shuffled)

            adjacency: dict[bytes, list[bytes]] = {}

            for source, target in shuffled:
                adjacency.setdefault(source, []).append(target)

            result = analyze_bidirectional_graph(
                adjacency,
                changed_nodes=(b"a.py",),
                protected_nodes=(b"protected.py",),
                **LIMITS,
            )

            if expected is None:
                expected = result
            else:
                self.assertEqual(result, expected)

    def test_graph_node_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            analyze_bidirectional_graph(
                {
                    b"a": (b"b",),
                    b"b": (b"c",),
                },
                changed_nodes=(b"a",),
                protected_nodes=(b"c",),
                max_graph_nodes=2,
                max_graph_edges=100,
                max_unresolved_nodes=100,
            )

    def test_graph_edge_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            analyze_bidirectional_graph(
                {
                    b"a": (b"b", b"c"),
                },
                changed_nodes=(b"a",),
                protected_nodes=(b"c",),
                max_graph_nodes=100,
                max_graph_edges=1,
                max_unresolved_nodes=100,
            )

    def test_unresolved_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            analyze_bidirectional_graph(
                {
                    b"a": (b"u1",),
                    b"u1": (b"u2",),
                },
                changed_nodes=(b"a",),
                protected_nodes=(b"protected",),
                unresolved_nodes=(b"u1", b"u2"),
                max_graph_nodes=100,
                max_graph_edges=100,
                max_unresolved_nodes=1,
            )

    def test_zero_edge_and_unresolved_budgets_are_valid_when_unused(self) -> None:
        result = analyze_bidirectional_graph(
            {},
            changed_nodes=(b"changed",),
            protected_nodes=(b"protected",),
            max_graph_nodes=10,
            max_graph_edges=0,
            max_unresolved_nodes=0,
        )

        self.assertEqual(
            result.forward.visited_edges,
            0,
        )
        self.assertEqual(
            result.forward.unresolved_count,
            0,
        )

    def test_zero_edge_budget_fails_when_an_edge_exists(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "max_graph_edges=0",
        ):
            analyze_bidirectional_graph(
                {
                    b"changed": (b"protected",),
                },
                changed_nodes=(b"changed",),
                protected_nodes=(b"protected",),
                max_graph_nodes=10,
                max_graph_edges=0,
                max_unresolved_nodes=0,
            )

    def test_zero_unresolved_budget_fails_when_unresolved_is_reached(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "max_unresolved_nodes=0",
        ):
            analyze_bidirectional_graph(
                {},
                changed_nodes=(b"changed",),
                protected_nodes=(b"protected",),
                unresolved_nodes=(b"changed",),
                max_graph_nodes=10,
                max_graph_edges=0,
                max_unresolved_nodes=0,
            )

    def test_node_limit_stops_target_consumption_immediately(
        self,
    ) -> None:
        def targets():
            yield b"target-one"
            yield b"target-two"
            raise AssertionError(
                "target iterable consumed after node-limit failure"
            )

        with self.assertRaisesRegex(
            ReferenceGraphError,
            "max_graph_nodes=2",
        ):
            analyze_bidirectional_graph(
                {
                    b"source": targets(),
                },
                changed_nodes=(b"source",),
                protected_nodes=(b"protected",),
                max_graph_nodes=2,
                max_graph_edges=10,
                max_unresolved_nodes=0,
            )

    def test_invalid_empty_changed_set_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceGraphError,
            "at least one changed node",
        ):
            analyze_bidirectional_graph(
                {},
                changed_nodes=(),
                protected_nodes=(b"protected",),
                **LIMITS,
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

import numpy as np

from mes_quant.exploration.l1_tree001 import (
    QUANTILE_METHOD,
    SPLIT_QUANTILES,
    TreeNode,
    fit_bounded_shallow_tree,
    tree_to_dict,
)
from mes_quant.features.contract import FEATURE_COLUMNS


def _hierarchical_tree_data(n_per_quadrant: int = 300) -> tuple[np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    labels: list[int] = []
    rates = {
        (-1.0, -1.0): 0.10,
        (-1.0, 1.0): 0.35,
        (1.0, -1.0): 0.65,
        (1.0, 1.0): 0.90,
    }
    for (x0, x1), rate in rates.items():
        n_long = int(round(n_per_quadrant * rate))
        for index in range(n_per_quadrant):
            row = [0.0] * len(FEATURE_COLUMNS)
            row[0] = x0
            row[1] = x1
            rows.append(row)
            labels.append(1 if index < n_long else 0)
    return np.asarray(rows, dtype=np.float64), np.asarray(labels, dtype=np.int8)


class TREE001HardeningTests(unittest.TestCase):
    def test_minimum_child_rule_is_actually_enforced(self) -> None:
        # Root N=1000 => frozen minimum child size is 250. The only useful
        # split isolates 200 rows, so TREE001 must refuse it even though the
        # labels are otherwise perfectly separable by feature 0.
        x = np.zeros((1000, len(FEATURE_COLUMNS)), dtype=np.float64)
        x[:200, 0] = 0.0
        x[200:, 0] = 1.0
        y = np.r_[np.zeros(200, dtype=np.int8), np.ones(800, dtype=np.int8)]

        tree = fit_bounded_shallow_tree(x, y)

        self.assertTrue(tree.is_leaf)
        self.assertEqual(tree.n_rows, 1000)
        self.assertEqual(tree.n_long, 800)

    def test_repeated_fit_is_structurally_deterministic(self) -> None:
        x, y = _hierarchical_tree_data()

        first = fit_bounded_shallow_tree(x, y)
        second = fit_bounded_shallow_tree(x, y)

        self.assertEqual(tree_to_dict(first), tree_to_dict(second))

    def test_every_internal_threshold_is_a_quantile_of_rows_reaching_that_node(self) -> None:
        x, y = _hierarchical_tree_data()
        tree = fit_bounded_shallow_tree(x, y)

        def assert_node(node: TreeNode, node_x: np.ndarray) -> None:
            if node.is_leaf:
                return
            self.assertIsNotNone(node.feature_index)
            self.assertIsNotNone(node.quantile_order)
            self.assertIsNotNone(node.threshold)
            self.assertIsNotNone(node.left)
            self.assertIsNotNone(node.right)

            feature_index = int(node.feature_index)
            quantile_order = int(node.quantile_order)
            values = node_x[:, feature_index]
            expected = float(
                np.quantile(
                    values,
                    SPLIT_QUANTILES[quantile_order],
                    method=QUANTILE_METHOD,
                )
            )
            self.assertEqual(float(node.threshold), expected)

            left_mask = values <= float(node.threshold)
            self.assertEqual(int(left_mask.sum()), int(node.left_rows))
            self.assertEqual(int((~left_mask).sum()), int(node.right_rows))
            assert_node(node.left, node_x[left_mask])
            assert_node(node.right, node_x[~left_mask])

        assert_node(tree, x)


if __name__ == "__main__":
    unittest.main()

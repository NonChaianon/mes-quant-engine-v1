from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.exploration.l1_lr001 import L1AccessError, preflight_artifacts, prepare_joined_train_frame
from mes_quant.exploration.l1_tree001 import (
    DIAGNOSTIC_LONG_THRESHOLD,
    FINAL_NO_EDGE_DISPOSITION,
    MAX_DEPTH,
    MAX_TERMINAL_LEAVES,
    MIN_CHILD_ABSOLUTE,
    MIN_CHILD_ROOT_FRACTION,
    MODEL_FAMILY_CATEGORY,
    MODEL_IMPLEMENTATION_ID,
    QUANTILE_METHOD,
    SPLIT_QUANTILES,
    TREE001_CANDIDATE_ID,
    TREE001_EXECUTION_STATUS,
    TREE001_EXPERIMENT_ID,
    _fit_predict_fold,
    _fresh_run_dir,
    _minimum_child_rows,
    _tree_leaf_count,
    _tree_max_depth,
    evaluate_tree001_frame,
    fit_bounded_shallow_tree,
    predict_bounded_shallow_tree,
    run_tree001,
    tree_to_dict,
)
from mes_quant.features.contract import FEATURE_COLUMNS


def _synthetic_frames(rows_per_year: int = 360) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    row_index = 0
    for year in (2020, 2021, 2022, 2023):
        dates = pd.date_range(f"{year}-01-01", periods=rows_per_year, freq="D", tz="UTC")
        for within_year, decision_time in enumerate(dates):
            signal = -1.0 if within_year % 2 == 0 else 1.0
            decision_id = f"D{row_index:06d}"
            if year <= 2021:
                role_2022 = "TRAIN"
            elif year == 2022:
                role_2022 = "VALIDATION"
            else:
                role_2022 = "UNUSED"
            if year <= 2022:
                role_2023 = "TRAIN"
            else:
                role_2023 = "VALIDATION"

            feature_row: dict[str, object] = {
                "decision_id": decision_id,
                "decision_time": decision_time,
                "nyse_session_date": decision_time.date(),
                "outer_partition": "TRAIN",
                "role_wf_2022": role_2022,
                "role_wf_2023": role_2023,
                "feature_row_usable": True,
            }
            for feature_index, feature_name in enumerate(FEATURE_COLUMNS):
                feature_row[feature_name] = signal if feature_index == 0 else 0.0
            feature_rows.append(feature_row)
            label_rows.append(
                {
                    "decision_id": decision_id,
                    "decision_time": decision_time,
                    "label_end_time": decision_time + pd.Timedelta(minutes=60),
                    "nyse_session_date": decision_time.date(),
                    "outer_partition": "TRAIN",
                    "role_wf_2022": role_2022,
                    "role_wf_2023": role_2023,
                    "label_usable": True,
                    "economic_label_primary": "LONG" if signal > 0 else "NO_TRADE",
                }
            )
            row_index += 1
    return pd.DataFrame(feature_rows), pd.DataFrame(label_rows)


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


class TREE001GovernanceTests(unittest.TestCase):
    def test_identity_and_numerical_spec_are_frozen(self) -> None:
        self.assertEqual(TREE001_EXPERIMENT_ID, "MES_S1_TREE001_20260815T192900Z")
        self.assertEqual(TREE001_CANDIDATE_ID, "TREE001")
        self.assertEqual(MODEL_FAMILY_CATEGORY, "SHALLOW_TREE")
        self.assertEqual(MODEL_IMPLEMENTATION_ID, "BOUNDED_SHALLOW_DECISION_TREE")
        self.assertEqual(MAX_DEPTH, 2)
        self.assertEqual(MAX_TERMINAL_LEAVES, 4)
        self.assertEqual(SPLIT_QUANTILES, (0.20, 0.40, 0.60, 0.80))
        self.assertEqual(QUANTILE_METHOD, "linear")
        self.assertEqual(MIN_CHILD_ABSOLUTE, 250)
        self.assertEqual(MIN_CHILD_ROOT_FRACTION, 0.05)
        self.assertEqual(DIAGNOSTIC_LONG_THRESHOLD, 0.5)

    def test_real_execution_is_disabled_before_any_path_access(self) -> None:
        self.assertEqual(TREE001_EXECUTION_STATUS, "DISABLED_PENDING_OWNER_AUTHORIZATION")
        with self.assertRaisesRegex(L1AccessError, "disabled pending separate owner authorization"):
            run_tree001(
                features_path="definitely_missing_features.parquet",
                labels_path="definitely_missing_labels.parquet",
                output_root="unused",
                authorization_token="anything",
                code_identity="synthetic-test",
            )

    def test_preflight_preserves_exact_hash_gate_without_target_row_loading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature_path = Path(tmp) / "features.parquet"
            label_path = Path(tmp) / "labels.parquet"
            pd.DataFrame({"outer_partition": ["TRAIN"]}).to_parquet(feature_path, index=False)
            pd.DataFrame({"outer_partition": ["TRAIN"]}).to_parquet(label_path, index=False)
            with self.assertRaisesRegex(L1AccessError, "Cell 14 feature SHA-256 mismatch"):
                preflight_artifacts(feature_path, label_path)

    def test_experiment_output_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / TREE001_EXPERIMENT_ID
            run_dir.mkdir()
            with self.assertRaisesRegex(L1AccessError, "cannot be overwritten"):
                _fresh_run_dir(tmp)

    def test_wf_2024_target_aware_holdout_is_rejected(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        with self.assertRaisesRegex(L1AccessError, "outer Validation"):
            _fit_predict_fold(
                frame,
                fold_id="WF_2024",
                role_column="role_wf_2023",
                validation_year=2024,
            )


class TREE001ModelTests(unittest.TestCase):
    def test_minimum_child_uses_root_count(self) -> None:
        self.assertEqual(_minimum_child_rows(1000), 250)
        self.assertEqual(_minimum_child_rows(6000), 300)

    def test_laplace_leaf_probability_is_persisted(self) -> None:
        x = np.zeros((600, len(FEATURE_COLUMNS)), dtype=float)
        y = np.r_[np.ones(420, dtype=np.int8), np.zeros(180, dtype=np.int8)]
        tree = fit_bounded_shallow_tree(x, y)
        self.assertTrue(tree.is_leaf)
        self.assertAlmostEqual(tree.probability_long, 421 / 602)
        serialized = tree_to_dict(tree)
        self.assertEqual(serialized["n_rows"], 600)
        self.assertEqual(serialized["n_long"], 420)

    def test_no_split_when_improvement_is_not_positive(self) -> None:
        x = np.zeros((800, len(FEATURE_COLUMNS)), dtype=float)
        x[:, 0] = np.arange(800, dtype=float)
        y = np.tile(np.asarray([0, 1], dtype=np.int8), 400)
        tree = fit_bounded_shallow_tree(x, y)
        self.assertTrue(tree.is_leaf)

    def test_deterministic_tie_break_prefers_earliest_feature(self) -> None:
        n_rows = 800
        signal = np.r_[np.full(400, -1.0), np.full(400, 1.0)]
        x = np.zeros((n_rows, len(FEATURE_COLUMNS)), dtype=float)
        x[:, 0] = signal
        x[:, 1] = signal
        y = (signal > 0).astype(np.int8)
        tree = fit_bounded_shallow_tree(x, y)
        self.assertFalse(tree.is_leaf)
        self.assertEqual(tree.feature_index, 0)
        self.assertEqual(tree.feature_name, FEATURE_COLUMNS[0])

    def test_tree_respects_depth_and_leaf_bounds(self) -> None:
        x, y = _hierarchical_tree_data()
        tree = fit_bounded_shallow_tree(x, y)
        self.assertLessEqual(_tree_max_depth(tree), 2)
        self.assertLessEqual(_tree_leaf_count(tree), 4)
        self.assertEqual(_tree_max_depth(tree), 2)
        self.assertEqual(_tree_leaf_count(tree), 4)

    def test_holdout_values_cannot_change_fitted_tree(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        first = _fit_predict_fold(
            frame,
            fold_id="WF_2022",
            role_column="role_wf_2022",
            validation_year=2022,
        )
        changed = frame.copy()
        holdout_mask = changed["role_wf_2022_feature"].astype(str).eq("VALIDATION")
        changed.loc[holdout_mask, FEATURE_COLUMNS[0]] = np.linspace(-1e9, 1e9, holdout_mask.sum())
        second = _fit_predict_fold(
            changed,
            fold_id="WF_2022",
            role_column="role_wf_2022",
            validation_year=2022,
        )
        self.assertEqual(tree_to_dict(first.tree), tree_to_dict(second.tree))

    def test_prediction_uses_left_le_right_gt_convention(self) -> None:
        n_rows = 800
        signal = np.r_[np.full(400, -1.0), np.full(400, 1.0)]
        x = np.zeros((n_rows, len(FEATURE_COLUMNS)), dtype=float)
        x[:, 0] = signal
        y = (signal > 0).astype(np.int8)
        tree = fit_bounded_shallow_tree(x, y)
        holdout = np.zeros((3, len(FEATURE_COLUMNS)), dtype=float)
        holdout[:, 0] = [tree.threshold, tree.threshold - 1.0, tree.threshold + 1.0]
        probabilities = predict_bounded_shallow_tree(tree, holdout)
        self.assertEqual(probabilities[0], probabilities[1])
        self.assertNotEqual(probabilities[0], probabilities[2])

    def test_synthetic_tree001_end_to_end_improves_primary_metric(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_tree001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 20, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        result = evaluation.experiment_record["result"]
        self.assertGreater(result["LOG_LOSS_IMPROVEMENT"], 0.0)
        self.assertGreater(result["median_fold_log_loss_improvement"], 0.0)
        self.assertTrue(result["interesting_enough_to_continue"])
        self.assertEqual(evaluation.experiment_record["disposition"], "INTERESTING_ENOUGH_TO_CONTINUE")
        self.assertEqual([fold.validation_year for fold in evaluation.fold_runs], [2022, 2023])

    def test_record_persists_tree_structure_and_access_boundaries(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_tree001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 20, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        record = evaluation.experiment_record
        fold_record = record["diagnostics_tree001"]["folds"][0]
        split = fold_record["tree_structure"]["split"]
        self.assertIn("feature_index", split)
        self.assertIn("feature_name", split)
        self.assertIn("threshold", split)
        self.assertIn("split_improvement", split)
        self.assertIn("left_rows", split)
        self.assertIn("right_rows", split)
        self.assertEqual(record["information_access"]["validation_outcomes"], "UNOPENED")
        self.assertEqual(record["information_access"]["final_test"], "SEALED")
        self.assertEqual(record["information_access"]["gross_pnl_future_columns"], "NOT_READ")
        self.assertEqual(record["search_budget"]["target_aware_candidate_budget"], 2)
        self.assertFalse(record["search_budget"]["small_feature_rule_tested"])

    def test_failed_candidate_uses_addendum_scope_limited_disposition(self) -> None:
        self.assertEqual(FINAL_NO_EDGE_DISPOSITION, "NO_USABLE_EDGE_IDENTIFIED_IN_TESTED_SPRINT_1_SCOPE")


if __name__ == "__main__":
    unittest.main()

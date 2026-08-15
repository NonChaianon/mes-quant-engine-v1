from __future__ import annotations

import ast
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.exploration.sprint1 import (
    ALLOWED_MODEL_FAMILIES,
    BREAK_EVEN_INDEX_POINTS,
    COST_ASSUMPTION_ID,
    EXPLORATION_SCOPE_ID,
    HARNESS_EXECUTION_STATUS,
    MES_MULTIPLIER_USD_POINT,
    NO_EDGE_IN_SCOPE,
    PRIMARY_METRIC,
    REALIZED_TRAIN_LABEL_IO_IMPLEMENTED,
    ROUND_TRIP_COST_USD,
    TARGET_MAPPING,
    TARGET_MAPPING_VERSION,
    ExperimentSpec,
    FoldEvaluationInput,
    SprintHarnessError,
    assert_unique_experiment_id,
    binary_log_loss,
    brier_score,
    build_experiment_history_record,
    evaluate_fold,
    evaluate_sprint,
)
from mes_quant.features.contract import FEATURE_COLUMNS


class Sprint1HarnessContractTests(unittest.TestCase):
    def test_protocol_constants_are_frozen(self) -> None:
        self.assertEqual(
            EXPLORATION_SCOPE_ID,
            "MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M",
        )
        self.assertEqual(PRIMARY_METRIC, "OOF_BINARY_LOG_LOSS")
        self.assertEqual(
            TARGET_MAPPING,
            {"LONG": 1, "SHORT": 0, "NO_TRADE": 0},
        )
        self.assertEqual(
            TARGET_MAPPING_VERSION,
            "MES_V1_EDGE_SPRINT_1_LONG_FLAT_BINARY_V1",
        )
        self.assertEqual(
            COST_ASSUMPTION_ID,
            "CELL10_CONSERVATIVE_RT_USD_4_97_POINTS_0_994_V1",
        )
        self.assertEqual(ROUND_TRIP_COST_USD, 4.97)
        self.assertEqual(BREAK_EVEN_INDEX_POINTS, 0.994)
        self.assertEqual(MES_MULTIPLIER_USD_POINT, 5.0)
        self.assertEqual(HARNESS_EXECUTION_STATUS, "DRY_RUN_ONLY_L0")
        self.assertFalse(REALIZED_TRAIN_LABEL_IO_IMPLEMENTED)
        self.assertIn("REGULARIZED_LOGISTIC_REGRESSION", ALLOWED_MODEL_FAMILIES)
        self.assertIn("SHALLOW_TREE", ALLOWED_MODEL_FAMILIES)
        self.assertIn("SHALLOW_TREE_ENSEMBLE", ALLOWED_MODEL_FAMILIES)
        self.assertIn("SMALL_FEATURE_RULE", ALLOWED_MODEL_FAMILIES)

    def _valid_spec(self, **overrides: object) -> ExperimentSpec:
        values: dict[str, object] = {
            "experiment_id": "S1_SYNTHETIC_001",
            "hypothesis": "Synthetic probabilities improve fold-correct log loss.",
            "feature_subset": (FEATURE_COLUMNS[0], FEATURE_COLUMNS[1]),
            "model_family": "REGULARIZED_LOGISTIC_REGRESSION",
            "parameters": {"C_grid": [0.1, 1.0, 10.0]},
            "fold_definition": "SYNTHETIC_TIME_ORDERED_OOF",
        }
        values.update(overrides)
        return ExperimentSpec(**values)

    def test_valid_experiment_spec(self) -> None:
        spec = self._valid_spec()
        self.assertEqual(spec.primary_metric, PRIMARY_METRIC)
        self.assertEqual(spec.exploration_scope_id, EXPLORATION_SCOPE_ID)

    def test_unknown_feature_is_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "non-authorized Cell 14"):
            self._valid_spec(feature_subset=("future_return_60m",))

    def test_duplicate_feature_is_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "duplicates"):
            self._valid_spec(feature_subset=(FEATURE_COLUMNS[0], FEATURE_COLUMNS[0]))

    def test_unknown_model_family_is_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "outside Sprint 1"):
            self._valid_spec(model_family="HMM")

    def test_primary_metric_cannot_be_rewritten(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "primary metric is frozen"):
            self._valid_spec(primary_metric="ROC_AUC")

    def test_duplicate_experiment_id_is_rejected_against_history(self) -> None:
        spec = self._valid_spec()
        with self.assertRaisesRegex(SprintHarnessError, "duplicate EXPERIMENT_ID"):
            assert_unique_experiment_id(spec.experiment_id, [spec.experiment_id])

    def test_non_json_parameter_metadata_is_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "JSON-compatible"):
            self._valid_spec(parameters={"bad": object()})


class Sprint1MetricTests(unittest.TestCase):
    def test_invalid_labels_are_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "only 0/1"):
            binary_log_loss([0, 2], [0.2, 0.8])

    def test_invalid_probabilities_are_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "within \[0, 1\]"):
            brier_score([0, 1], [-0.1, 1.1])

    def test_non_finite_probabilities_are_rejected(self) -> None:
        with self.assertRaisesRegex(SprintHarnessError, "non-finite"):
            binary_log_loss([0, 1], [0.2, np.nan])

    def test_fold_correct_prior_uses_only_supplied_training_labels(self) -> None:
        zero_prior = evaluate_fold(
            FoldEvaluationInput(
                fold_id="FOLD_ZERO_PRIOR",
                train_labels=[0, 0, 0, 0],
                holdout_labels=[0, 1],
                candidate_probabilities=[0.25, 0.75],
            )
        )
        one_prior = evaluate_fold(
            FoldEvaluationInput(
                fold_id="FOLD_ONE_PRIOR",
                train_labels=[1, 1, 1, 1],
                holdout_labels=[0, 1],
                candidate_probabilities=[0.25, 0.75],
            )
        )
        self.assertEqual(zero_prior.train_long_rate, 0.0)
        self.assertEqual(one_prior.train_long_rate, 1.0)
        self.assertNotEqual(zero_prior.baseline_log_loss, one_prior.baseline_log_loss)

    def test_better_candidate_passes_strict_continuation_rule(self) -> None:
        evaluation = evaluate_sprint(
            [
                FoldEvaluationInput(
                    fold_id="FOLD_A",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=[0, 1, 0, 1],
                    candidate_probabilities=[0.1, 0.9, 0.1, 0.9],
                ),
                FoldEvaluationInput(
                    fold_id="FOLD_B",
                    train_labels=[1, 0, 1, 0],
                    holdout_labels=[1, 0, 1, 0],
                    candidate_probabilities=[0.9, 0.1, 0.9, 0.1],
                ),
            ]
        )
        self.assertGreater(evaluation.log_loss_improvement, 0.0)
        self.assertGreater(evaluation.median_fold_log_loss_improvement, 0.0)
        self.assertTrue(evaluation.interesting_enough_to_continue)
        self.assertEqual(evaluation.disposition, "INTERESTING_ENOUGH_TO_CONTINUE")

    def test_equality_to_zero_does_not_pass(self) -> None:
        evaluation = evaluate_sprint(
            [
                FoldEvaluationInput(
                    fold_id="FOLD_EQUAL",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=[0, 1, 1, 0],
                    candidate_probabilities=[0.5, 0.5, 0.5, 0.5],
                )
            ]
        )
        self.assertEqual(evaluation.log_loss_improvement, 0.0)
        self.assertEqual(evaluation.median_fold_log_loss_improvement, 0.0)
        self.assertFalse(evaluation.interesting_enough_to_continue)
        self.assertEqual(evaluation.disposition, NO_EDGE_IN_SCOPE)

    def test_positive_overall_with_non_positive_median_does_not_pass(self) -> None:
        good_labels = [0, 1] * 50
        good_probabilities = [0.01, 0.99] * 50
        evaluation = evaluate_sprint(
            [
                FoldEvaluationInput(
                    fold_id="BIG_GOOD_FOLD",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=good_labels,
                    candidate_probabilities=good_probabilities,
                ),
                FoldEvaluationInput(
                    fold_id="SMALL_BAD_FOLD_1",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=[0, 1],
                    candidate_probabilities=[0.6, 0.4],
                ),
                FoldEvaluationInput(
                    fold_id="SMALL_BAD_FOLD_2",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=[1, 0],
                    candidate_probabilities=[0.4, 0.6],
                ),
            ]
        )
        self.assertGreater(evaluation.log_loss_improvement, 0.0)
        self.assertLessEqual(evaluation.median_fold_log_loss_improvement, 0.0)
        self.assertFalse(evaluation.interesting_enough_to_continue)
        self.assertEqual(evaluation.disposition, NO_EDGE_IN_SCOPE)


class Sprint1ExperimentHistoryTests(unittest.TestCase):
    def test_history_record_contains_minimum_governance_fields(self) -> None:
        spec = ExperimentSpec(
            experiment_id="S1_SYNTHETIC_LOG_001",
            hypothesis="Synthetic candidate should beat the prior baseline.",
            feature_subset=(FEATURE_COLUMNS[0],),
            model_family="SMALL_FEATURE_RULE",
            parameters={"rule": "synthetic_test_only"},
            fold_definition="SYNTHETIC_TIME_ORDERED_OOF",
        )
        evaluation = evaluate_sprint(
            [
                FoldEvaluationInput(
                    fold_id="FOLD_A",
                    train_labels=[0, 1, 0, 1],
                    holdout_labels=[0, 1],
                    candidate_probabilities=[0.1, 0.9],
                )
            ]
        )
        record = build_experiment_history_record(
            spec,
            evaluation,
            timestamp_utc=datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        required = {
            "EXPERIMENT_ID",
            "timestamp_utc",
            "EXPLORATION_SCOPE_ID",
            "hypothesis",
            "feature_subset",
            "target_mapping_version",
            "target_mapping",
            "cost_assumption_reference",
            "model_family",
            "parameters",
            "fold_definition",
            "primary_metric",
            "diagnostics",
            "result",
            "disposition",
            "code_identity",
        }
        self.assertTrue(required.issubset(record))
        self.assertEqual(record["primary_metric"], PRIMARY_METRIC)
        self.assertEqual(record["harness_execution_status"], "DRY_RUN_ONLY_L0")

    def test_new_exploration_package_has_no_real_data_reader_calls(self) -> None:
        forbidden_calls = {
            "open",
            "read_csv",
            "read_parquet",
            "read_pickle",
            "read_feather",
            "read_sql",
            "read_json",
            "urlopen",
        }
        exploration_dir = PROJECT_ROOT / "src" / "mes_quant" / "exploration"
        violations: list[str] = []
        for path in sorted(exploration_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                else:
                    continue
                if call_name in forbidden_calls:
                    violations.append(f"{path.name}:{call_name}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.exploration.l1_lr001 import (
    ARMIJO_CONSTANT,
    BACKTRACK_SHRINK,
    CALIBRATION_BINS,
    DIAGNOSTIC_LONG_THRESHOLD,
    FIRST_L1_EXPERIMENT_ID,
    FOLD_SPECS,
    GRADIENT_TOL,
    L1_AUTHORIZATION_TOKEN,
    L1AccessError,
    L2_LAMBDA,
    LABEL_COLUMNS,
    MAX_ITERATIONS,
    MINIMUM_STEP,
    NumericalExperimentError,
    _read_train_only_parquet,
    evaluate_lr001_frame,
    fit_frozen_logistic,
    preflight_artifacts,
    prepare_joined_train_frame,
    run_lr001,
)
from mes_quant.exploration.sprint1 import EXPLORATION_SCOPE_ID, PRIMARY_METRIC
from mes_quant.features.contract import FEATURE_COLUMNS


def _synthetic_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    row_index = 0
    for year in (2020, 2021, 2022, 2023):
        for day in range(1, 31):
            decision_time = pd.Timestamp(
                year=year,
                month=6,
                day=day,
                hour=15,
                tz="UTC",
            )
            signal = -1.0 if day % 2 == 0 else 1.0
            decision_id = f"D{row_index:04d}"
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


class LR001GovernanceTests(unittest.TestCase):
    def test_experiment_identity_and_train_only_folds_are_frozen(self) -> None:
        self.assertEqual(FIRST_L1_EXPERIMENT_ID, "MES_S1_LR001_20260815T095100Z")
        self.assertEqual(
            FOLD_SPECS,
            (
                ("WF_2022", "role_wf_2022", 2022),
                ("WF_2023", "role_wf_2023", 2023),
            ),
        )
        self.assertTrue(all(year < 2024 for _, _, year in FOLD_SPECS))
        self.assertEqual(EXPLORATION_SCOPE_ID, "MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M")
        self.assertEqual(PRIMARY_METRIC, "OOF_BINARY_LOG_LOSS")

    def test_fixed_lr001_numerical_policy_is_frozen(self) -> None:
        self.assertEqual(L2_LAMBDA, 0.001)
        self.assertEqual(MAX_ITERATIONS, 50)
        self.assertEqual(GRADIENT_TOL, 1e-8)
        self.assertEqual(ARMIJO_CONSTANT, 1e-4)
        self.assertEqual(BACKTRACK_SHRINK, 0.5)
        self.assertEqual(MINIMUM_STEP, 2.0**-20)
        self.assertEqual(DIAGNOSTIC_LONG_THRESHOLD, 0.5)
        self.assertEqual(CALIBRATION_BINS, 10)

    def test_label_reader_does_not_request_pnl_or_future_outcome_columns(self) -> None:
        lowered = [column.lower() for column in LABEL_COLUMNS]
        forbidden = ("gross", "pnl", "net_", "exit_reference", "future_return")
        self.assertEqual(
            [column for column in lowered if any(token in column for token in forbidden)],
            [],
        )

    def test_authorization_token_blocks_before_any_path_access(self) -> None:
        with self.assertRaisesRegex(L1AccessError, "authorization token mismatch"):
            run_lr001(
                features_path="definitely_missing_features.parquet",
                labels_path="definitely_missing_labels.parquet",
                output_root="unused",
                authorization_token="WRONG",
                code_identity="synthetic-test",
            )
        self.assertEqual(L1_AUTHORIZATION_TOKEN, "OWNER_AUTHORIZED_L1_SPRINT1_20260815")


class LR001TrainFrameTests(unittest.TestCase):
    def test_train_only_reader_pushes_partition_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.parquet"
            pd.DataFrame(
                {
                    "outer_partition": ["TRAIN", "VALIDATION", "TRAIN"],
                    "decision_id": ["A", "B", "C"],
                }
            ).to_parquet(path, index=False)
            frame = _read_train_only_parquet(
                path,
                columns=("outer_partition", "decision_id"),
            )
            self.assertEqual(frame["decision_id"].tolist(), ["A", "C"])
            self.assertEqual(set(frame["outer_partition"]), {"TRAIN"})

    def test_preflight_rejects_noncanonical_hash_before_row_loading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature_path = Path(tmp) / "features.parquet"
            label_path = Path(tmp) / "labels.parquet"
            pd.DataFrame({"outer_partition": ["TRAIN"]}).to_parquet(feature_path, index=False)
            pd.DataFrame({"outer_partition": ["TRAIN"]}).to_parquet(label_path, index=False)
            with self.assertRaisesRegex(L1AccessError, "Cell 14 feature SHA-256 mismatch"):
                preflight_artifacts(feature_path, label_path)

    def test_prepare_rejects_any_non_train_partition(self) -> None:
        features, labels = _synthetic_frames()
        labels.loc[0, "outer_partition"] = "VALIDATION"
        with self.assertRaisesRegex(L1AccessError, "non-TRAIN"):
            prepare_joined_train_frame(
                features,
                labels,
                enforce_canonical_train_count=False,
            )

    def test_prepare_maps_long_to_one_and_short_no_trade_to_zero(self) -> None:
        features, labels = _synthetic_frames()
        labels.loc[0, "economic_label_primary"] = "SHORT"
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        target_by_id = frame.set_index("decision_id")["sprint1_target"]
        self.assertEqual(int(target_by_id.loc["D0000"]), 0)
        self.assertEqual(int(target_by_id.loc["D0001"]), 0)
        self.assertEqual(int(target_by_id.loc["D0002"]), 1)

    def test_prepare_rejects_mismatched_decision_time(self) -> None:
        features, labels = _synthetic_frames()
        labels.loc[0, "decision_time"] = labels.loc[0, "decision_time"] + pd.Timedelta(minutes=15)
        labels.loc[0, "label_end_time"] = labels.loc[0, "decision_time"] + pd.Timedelta(minutes=60)
        with self.assertRaisesRegex(L1AccessError, "mismatch in decision_time"):
            prepare_joined_train_frame(
                features,
                labels,
                enforce_canonical_train_count=False,
            )


class LR001ModelTests(unittest.TestCase):
    def test_frozen_logistic_rejects_nonbinary_labels(self) -> None:
        x = np.zeros((3, len(FEATURE_COLUMNS)), dtype=float)
        with self.assertRaisesRegex(NumericalExperimentError, "not binary"):
            fit_frozen_logistic(x, [0, 1, 2])

    def test_synthetic_lr001_improves_primary_metric(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_lr001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        result = evaluation.experiment_record["result"]
        self.assertGreater(result["LOG_LOSS_IMPROVEMENT"], 0.0)
        self.assertGreater(result["median_fold_log_loss_improvement"], 0.0)
        self.assertTrue(result["interesting_enough_to_continue"])
        self.assertEqual(
            evaluation.experiment_record["disposition"],
            "INTERESTING_ENOUGH_TO_CONTINUE",
        )

    def test_only_2022_and_2023_holdouts_are_evaluated(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_lr001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        self.assertEqual([fold.validation_year for fold in evaluation.fold_runs], [2022, 2023])
        self.assertEqual([fold.holdout_rows for fold in evaluation.fold_runs], [30, 30])

    def test_zero_variance_features_are_retained_and_reported(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_lr001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        zero_features = evaluation.fold_runs[0].optimizer["zero_variance_features"]
        self.assertEqual(len(zero_features), len(FEATURE_COLUMNS) - 1)
        self.assertNotIn(FEATURE_COLUMNS[0], zero_features)

    def test_overlap_boundary_fails_closed(self) -> None:
        features, labels = _synthetic_frames()
        first_2022 = labels.loc[
            pd.to_datetime(labels["nyse_session_date"]).dt.year.eq(2022), "decision_time"
        ].min()
        last_2021_index = labels.loc[
            pd.to_datetime(labels["nyse_session_date"]).dt.year.eq(2021)
        ].index.max()
        labels.loc[last_2021_index, "label_end_time"] = first_2022
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        with self.assertRaisesRegex(L1AccessError, "overlap"):
            evaluate_lr001_frame(
                frame,
                timestamp_utc=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
                code_identity="synthetic-test-commit",
            )

    def test_record_preserves_l1_and_sealed_boundaries(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        evaluation = evaluate_lr001_frame(
            frame,
            timestamp_utc=datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc),
            code_identity="synthetic-test-commit",
        )
        record = evaluation.experiment_record
        self.assertEqual(record["EXPERIMENT_ID"], FIRST_L1_EXPERIMENT_ID)
        self.assertEqual(record["observed_access_level"], "L1")
        self.assertEqual(record["information_access"]["validation_outcomes"], "UNOPENED")
        self.assertEqual(record["information_access"]["final_test"], "SEALED")
        self.assertEqual(record["information_access"]["gross_pnl_future_columns"], "NOT_READ")
        self.assertEqual(record["sample"]["horizon_minutes"], 60)
        self.assertEqual(record["sample"]["decision_spacing_minutes"], 15)
        self.assertEqual(record["sample"]["overlap_scale_layers_heuristic"], 4)

    def test_non_utc_timestamp_is_rejected(self) -> None:
        features, labels = _synthetic_frames()
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=False,
        )
        with self.assertRaisesRegex(Exception, "timezone-aware UTC"):
            evaluate_lr001_frame(
                frame,
                timestamp_utc=datetime(2026, 8, 15, 10, 0),
                code_identity="synthetic-test-commit",
            )


if __name__ == "__main__":
    unittest.main()

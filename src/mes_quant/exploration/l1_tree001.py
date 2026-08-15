from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from mes_quant.exploration.l1_lr001 import (
    EXPECTED_CELL10_LABEL_SHA256,
    EXPECTED_CELL14_FEATURE_SHA256,
    FEATURE_METADATA_COLUMNS,
    FOLD_SPECS,
    LABEL_COLUMNS,
    L1AccessError,
    NumericalExperimentError,
    _calibration_summary,
    _pr_auc,
    _read_train_only_parquet,
    _roc_auc,
    _json_safe,
    preflight_artifacts,
    prepare_joined_train_frame,
)
from mes_quant.exploration.sprint1 import (
    COST_ASSUMPTION_ID,
    EXPLORATION_SCOPE_ID,
    PRIMARY_METRIC,
    ExperimentSpec,
    FoldEvaluationInput,
    SprintHarnessError,
    build_experiment_history_record,
    evaluate_sprint,
)
from mes_quant.features.contract import FEATURE_COLUMNS

TREE001_EXPERIMENT_ID = "MES_S1_TREE001_20260815T192900Z"
TREE001_CANDIDATE_ID = "TREE001"
MODEL_FAMILY_CATEGORY = "SHALLOW_TREE"
MODEL_IMPLEMENTATION_ID = "BOUNDED_SHALLOW_DECISION_TREE"
FOLD_DEFINITION = "CELL8_WF_2022_WF_2023_OUTER_TRAIN_ONLY_PURGED_60M"

MAX_DEPTH = 2
MAX_TERMINAL_LEAVES = 4
SPLIT_QUANTILES = (0.20, 0.40, 0.60, 0.80)
QUANTILE_METHOD = "linear"
MIN_CHILD_ABSOLUTE = 250
MIN_CHILD_ROOT_FRACTION = 0.05
DIAGNOSTIC_LONG_THRESHOLD = 0.5
CALIBRATION_BINS = 10
FINAL_NO_EDGE_DISPOSITION = "NO_USABLE_EDGE_IDENTIFIED_IN_TESTED_SPRINT_1_SCOPE"

TREE001_EXECUTION_STATUS = "DISABLED_PENDING_OWNER_AUTHORIZATION"
TREE001_AUTHORIZATION_TOKEN = ""


@dataclass(frozen=True)
class SplitCandidate:
    improvement: float
    feature_index: int
    feature_name: str
    quantile_order: int
    quantile: float
    threshold: float
    left_rows: int
    right_rows: int


@dataclass(frozen=True)
class TreeNode:
    depth: int
    n_rows: int
    n_long: int
    probability_long: float
    feature_index: int | None = None
    feature_name: str | None = None
    quantile_order: int | None = None
    quantile: float | None = None
    threshold: float | None = None
    split_improvement: float | None = None
    left_rows: int | None = None
    right_rows: int | None = None
    left: TreeNode | None = None
    right: TreeNode | None = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


@dataclass(frozen=True)
class TreeFoldRun:
    fold_id: str
    role_column: str
    validation_year: int
    train_rows: int
    holdout_rows: int
    train_sessions: int
    holdout_sessions: int
    train_long_rate: float
    holdout_long_rate: float
    min_child_rows: int
    probabilities: np.ndarray
    holdout_labels: np.ndarray
    holdout_decision_ids: tuple[str, ...]
    roc_auc: float
    pr_auc: float
    predicted_long_coverage: float
    calibration: tuple[dict[str, object], ...]
    tree: TreeNode


@dataclass(frozen=True)
class TREE001Evaluation:
    experiment_record: dict[str, object]
    fold_runs: tuple[TreeFoldRun, ...]


def _binary_labels(values: Sequence[int | float], *, name: str) -> np.ndarray:
    try:
        labels = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise NumericalExperimentError(f"{name} must be numeric binary labels") from exc
    if labels.ndim != 1 or labels.size == 0:
        raise NumericalExperimentError(f"{name} must be a non-empty one-dimensional array")
    if not np.isfinite(labels).all() or not np.isin(labels, (0.0, 1.0)).all():
        raise NumericalExperimentError(f"{name} must contain finite 0/1 labels")
    return labels.astype(np.int8, copy=False)


def _leaf_probability(labels: np.ndarray) -> float:
    n_rows = int(labels.size)
    n_long = int(labels.sum())
    return (n_long + 1.0) / (n_rows + 2.0)


def _constant_log_loss(labels: np.ndarray, probability: float) -> float:
    if not 0.0 < probability < 1.0:
        raise NumericalExperimentError("Laplace-smoothed probability escaped (0, 1)")
    return float(
        -np.mean(labels * math.log(probability) + (1 - labels) * math.log1p(-probability))
    )


def _minimum_child_rows(root_train_rows: int) -> int:
    if root_train_rows <= 0:
        raise NumericalExperimentError("root TRAIN row count must be positive")
    return max(MIN_CHILD_ABSOLUTE, math.ceil(MIN_CHILD_ROOT_FRACTION * root_train_rows))


def _candidate_thresholds(values: np.ndarray) -> tuple[tuple[int, float, float], ...]:
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise NumericalExperimentError("Split-threshold values must be finite one-dimensional data")
    thresholds: list[tuple[int, float, float]] = []
    seen: set[float] = set()
    for quantile_order, quantile in enumerate(SPLIT_QUANTILES):
        threshold = float(np.quantile(values, quantile, method=QUANTILE_METHOD))
        if not np.isfinite(threshold) or threshold in seen:
            continue
        seen.add(threshold)
        thresholds.append((quantile_order, quantile, threshold))
    return tuple(thresholds)


def _best_split(
    x: np.ndarray,
    y: np.ndarray,
    *,
    min_child_rows: int,
) -> SplitCandidate | None:
    parent_probability = _leaf_probability(y)
    parent_loss = _constant_log_loss(y, parent_probability)
    candidates: list[SplitCandidate] = []

    for feature_index, feature_name in enumerate(FEATURE_COLUMNS):
        values = x[:, feature_index]
        for quantile_order, quantile, threshold in _candidate_thresholds(values):
            left_mask = values <= threshold
            left_rows = int(left_mask.sum())
            right_rows = int(y.size - left_rows)
            if left_rows < min_child_rows or right_rows < min_child_rows:
                continue
            left_y = y[left_mask]
            right_y = y[~left_mask]
            left_loss = _constant_log_loss(left_y, _leaf_probability(left_y))
            right_loss = _constant_log_loss(right_y, _leaf_probability(right_y))
            children_loss = (left_rows * left_loss + right_rows * right_loss) / y.size
            improvement = float(parent_loss - children_loss)
            if not np.isfinite(improvement) or improvement <= 0.0:
                continue
            candidates.append(
                SplitCandidate(
                    improvement=improvement,
                    feature_index=feature_index,
                    feature_name=feature_name,
                    quantile_order=quantile_order,
                    quantile=quantile,
                    threshold=threshold,
                    left_rows=left_rows,
                    right_rows=right_rows,
                )
            )

    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            -item.improvement,
            item.feature_index,
            item.quantile_order,
            item.threshold,
        ),
    )


def fit_bounded_shallow_tree(
    train_x: np.ndarray,
    train_y: Sequence[int | float],
) -> TreeNode:
    x = np.asarray(train_x, dtype=np.float64)
    y = _binary_labels(train_y, name="train_y")
    if x.ndim != 2 or x.shape[0] != y.size or x.shape[1] != len(FEATURE_COLUMNS):
        raise NumericalExperimentError("TREE001 TRAIN feature shape must be rows x locked29")
    if not np.isfinite(x).all():
        raise NumericalExperimentError("TREE001 TRAIN features contain non-finite values")

    root_train_rows = int(y.size)
    min_child_rows = _minimum_child_rows(root_train_rows)

    def build(node_x: np.ndarray, node_y: np.ndarray, depth: int) -> TreeNode:
        n_rows = int(node_y.size)
        n_long = int(node_y.sum())
        probability = _leaf_probability(node_y)
        if depth >= MAX_DEPTH or n_rows < 2 * min_child_rows:
            return TreeNode(
                depth=depth,
                n_rows=n_rows,
                n_long=n_long,
                probability_long=probability,
            )

        split = _best_split(node_x, node_y, min_child_rows=min_child_rows)
        if split is None:
            return TreeNode(
                depth=depth,
                n_rows=n_rows,
                n_long=n_long,
                probability_long=probability,
            )

        left_mask = node_x[:, split.feature_index] <= split.threshold
        left = build(node_x[left_mask], node_y[left_mask], depth + 1)
        right = build(node_x[~left_mask], node_y[~left_mask], depth + 1)
        return TreeNode(
            depth=depth,
            n_rows=n_rows,
            n_long=n_long,
            probability_long=probability,
            feature_index=split.feature_index,
            feature_name=split.feature_name,
            quantile_order=split.quantile_order,
            quantile=split.quantile,
            threshold=split.threshold,
            split_improvement=split.improvement,
            left_rows=split.left_rows,
            right_rows=split.right_rows,
            left=left,
            right=right,
        )

    tree = build(x, y, 0)
    if _tree_max_depth(tree) > MAX_DEPTH or _tree_leaf_count(tree) > MAX_TERMINAL_LEAVES:
        raise NumericalExperimentError("TREE001 structural bound was violated")
    return tree


def _tree_leaf_count(node: TreeNode) -> int:
    if node.is_leaf:
        return 1
    if node.left is None or node.right is None:
        raise NumericalExperimentError("TREE001 internal node is missing a child")
    return _tree_leaf_count(node.left) + _tree_leaf_count(node.right)


def _tree_max_depth(node: TreeNode) -> int:
    if node.is_leaf:
        return node.depth
    if node.left is None or node.right is None:
        raise NumericalExperimentError("TREE001 internal node is missing a child")
    return max(_tree_max_depth(node.left), _tree_max_depth(node.right))


def predict_bounded_shallow_tree(tree: TreeNode, holdout_x: np.ndarray) -> np.ndarray:
    x = np.asarray(holdout_x, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != len(FEATURE_COLUMNS):
        raise NumericalExperimentError("TREE001 holdout feature shape must be rows x locked29")
    if not np.isfinite(x).all():
        raise NumericalExperimentError("TREE001 holdout features contain non-finite values")

    probabilities = np.empty(x.shape[0], dtype=np.float64)
    for row_index, row in enumerate(x):
        node = tree
        while not node.is_leaf:
            if (
                node.feature_index is None
                or node.threshold is None
                or node.left is None
                or node.right is None
            ):
                raise NumericalExperimentError("TREE001 internal node is incomplete")
            node = node.left if row[node.feature_index] <= node.threshold else node.right
        probabilities[row_index] = node.probability_long
    if not np.isfinite(probabilities).all():
        raise NumericalExperimentError("TREE001 produced non-finite probabilities")
    return probabilities


def tree_to_dict(node: TreeNode) -> dict[str, object]:
    record: dict[str, object] = {
        "depth": node.depth,
        "n_rows": node.n_rows,
        "n_long": node.n_long,
        "probability_long": node.probability_long,
        "is_leaf": node.is_leaf,
    }
    if node.is_leaf:
        return record
    if (
        node.feature_index is None
        or node.feature_name is None
        or node.quantile_order is None
        or node.quantile is None
        or node.threshold is None
        or node.split_improvement is None
        or node.left_rows is None
        or node.right_rows is None
        or node.left is None
        or node.right is None
    ):
        raise NumericalExperimentError("TREE001 internal node cannot be serialized")
    record["split"] = {
        "feature_index": node.feature_index,
        "feature_name": node.feature_name,
        "quantile_order": node.quantile_order,
        "quantile": node.quantile,
        "threshold": node.threshold,
        "comparison": "LEFT_IF_X_LE_THRESHOLD_ELSE_RIGHT",
        "split_improvement": node.split_improvement,
        "left_rows": node.left_rows,
        "right_rows": node.right_rows,
    }
    record["left"] = tree_to_dict(node.left)
    record["right"] = tree_to_dict(node.right)
    return record


def _fit_predict_fold(
    frame: pd.DataFrame,
    *,
    fold_id: str,
    role_column: str,
    validation_year: int,
) -> TreeFoldRun:
    if validation_year >= 2024:
        raise L1AccessError(f"{fold_id} would open outer Validation or later")
    role = frame[f"{role_column}_feature"].astype(str)
    train_mask = frame["sprint1_eligible"] & role.eq("TRAIN")
    holdout_mask = frame["sprint1_eligible"] & role.eq("VALIDATION")
    train = frame.loc[train_mask].copy()
    holdout = frame.loc[holdout_mask].copy()
    if train.empty or holdout.empty:
        raise L1AccessError(f"{fold_id} has empty TRAIN or holdout after usability gates")

    holdout_years = pd.to_datetime(holdout["nyse_session_date_feature"], errors="raise").dt.year
    if not holdout_years.eq(validation_year).all():
        raise L1AccessError(f"{fold_id} holdout is not confined to {validation_year}")
    if train["label_end_time"].max() >= holdout["decision_time_label"].min():
        raise L1AccessError(f"{fold_id} +60m training labels overlap its holdout boundary")

    train_x = train.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    holdout_x = holdout.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    train_y = train["sprint1_target"].to_numpy(dtype=np.int8)
    holdout_y = holdout["sprint1_target"].to_numpy(dtype=np.int8)
    tree = fit_bounded_shallow_tree(train_x, train_y)
    probabilities = predict_bounded_shallow_tree(tree, holdout_x)

    return TreeFoldRun(
        fold_id=fold_id,
        role_column=role_column,
        validation_year=validation_year,
        train_rows=int(len(train)),
        holdout_rows=int(len(holdout)),
        train_sessions=int(train["nyse_session_date_feature"].nunique()),
        holdout_sessions=int(holdout["nyse_session_date_feature"].nunique()),
        train_long_rate=float(train_y.mean()),
        holdout_long_rate=float(holdout_y.mean()),
        min_child_rows=_minimum_child_rows(len(train)),
        probabilities=probabilities,
        holdout_labels=holdout_y,
        holdout_decision_ids=tuple(holdout["decision_id"].astype(str).tolist()),
        roc_auc=_roc_auc(holdout_y, probabilities),
        pr_auc=_pr_auc(holdout_y, probabilities),
        predicted_long_coverage=float(np.mean(probabilities >= DIAGNOSTIC_LONG_THRESHOLD)),
        calibration=_calibration_summary(holdout_y, probabilities),
        tree=tree,
    )


def evaluate_tree001_frame(
    frame: pd.DataFrame,
    *,
    timestamp_utc: datetime,
    code_identity: str,
) -> TREE001Evaluation:
    if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() != timedelta(0):
        raise SprintHarnessError("timestamp_utc must be timezone-aware UTC")
    code_identity = code_identity.strip()
    if not code_identity:
        raise L1AccessError("code_identity must be non-empty")

    fold_runs = tuple(
        _fit_predict_fold(
            frame,
            fold_id=fold_id,
            role_column=role_column,
            validation_year=validation_year,
        )
        for fold_id, role_column, validation_year in FOLD_SPECS
    )
    seen_holdout_ids: set[str] = set()
    fold_inputs: list[FoldEvaluationInput] = []
    fold_diagnostics: list[dict[str, object]] = []
    for fold in fold_runs:
        repeated = seen_holdout_ids.intersection(fold.holdout_decision_ids)
        if repeated:
            raise L1AccessError("OOF holdout decision IDs repeat across folds")
        seen_holdout_ids.update(fold.holdout_decision_ids)

        role = frame[f"{fold.role_column}_feature"].astype(str)
        train_mask = frame["sprint1_eligible"] & role.eq("TRAIN")
        train_labels = frame.loc[train_mask, "sprint1_target"].to_numpy(dtype=np.int8)
        fold_inputs.append(
            FoldEvaluationInput(
                fold_id=fold.fold_id,
                train_labels=train_labels,
                holdout_labels=fold.holdout_labels,
                candidate_probabilities=fold.probabilities,
            )
        )
        fold_diagnostics.append(
            {
                "fold_id": fold.fold_id,
                "role_column": fold.role_column,
                "validation_year": fold.validation_year,
                "train_rows": fold.train_rows,
                "holdout_rows": fold.holdout_rows,
                "train_sessions": fold.train_sessions,
                "holdout_sessions": fold.holdout_sessions,
                "train_long_rate": fold.train_long_rate,
                "holdout_long_rate": fold.holdout_long_rate,
                "min_child_rows": fold.min_child_rows,
                "roc_auc": fold.roc_auc,
                "pr_auc": fold.pr_auc,
                "predicted_long_coverage_p_ge_0_5": fold.predicted_long_coverage,
                "calibration": list(fold.calibration),
                "tree_leaf_count": _tree_leaf_count(fold.tree),
                "tree_max_depth": _tree_max_depth(fold.tree),
                "tree_structure": tree_to_dict(fold.tree),
            }
        )

    sprint_evaluation = evaluate_sprint(fold_inputs)
    pooled_labels = np.concatenate([fold.holdout_labels for fold in fold_runs])
    pooled_probabilities = np.concatenate([fold.probabilities for fold in fold_runs])
    spec = ExperimentSpec(
        experiment_id=TREE001_EXPERIMENT_ID,
        hypothesis=(
            "A bounded depth-2 nonlinear partition of the locked29 Cell 14 feature universe "
            "improves TRAIN-only OOF binary log loss versus the fold-correct TRAIN prior."
        ),
        feature_subset=tuple(FEATURE_COLUMNS),
        model_family=MODEL_FAMILY_CATEGORY,
        parameters={
            "candidate_implementation_id": MODEL_IMPLEMENTATION_ID,
            "feature_count": len(FEATURE_COLUMNS),
            "max_depth": MAX_DEPTH,
            "max_terminal_leaves": MAX_TERMINAL_LEAVES,
            "split_quantiles": list(SPLIT_QUANTILES),
            "quantile_method": QUANTILE_METHOD,
            "split_comparison": "LEFT_IF_X_LE_THRESHOLD_ELSE_RIGHT",
            "min_child_absolute": MIN_CHILD_ABSOLUTE,
            "min_child_root_fraction": MIN_CHILD_ROOT_FRACTION,
            "leaf_probability": "LAPLACE_(N_LONG+1)/(N_NODE+2)",
            "split_objective": "WEIGHTED_TRAIN_BINARY_LOG_LOSS",
            "tie_break": [
                "LARGER_SPLIT_IMPROVEMENT",
                "LOWER_FEATURE_INDEX",
                "LOWER_QUANTILE_ORDER",
                "LOWER_NUMERIC_THRESHOLD",
            ],
            "preprocessing": "NONE_NO_SCALING_NO_IMPUTATION",
            "diagnostic_long_threshold": DIAGNOSTIC_LONG_THRESHOLD,
            "calibration_bins": CALIBRATION_BINS,
        },
        fold_definition=FOLD_DEFINITION,
    )
    record = build_experiment_history_record(
        spec,
        sprint_evaluation,
        timestamp_utc=timestamp_utc,
        code_identity=code_identity,
    )
    if not sprint_evaluation.interesting_enough_to_continue:
        record["disposition"] = FINAL_NO_EDGE_DISPOSITION
    record.update(
        {
            "observed_access_level": "L1",
            "authorization_reference": "Issue #28; real execution requires separate owner authorization",
            "candidate_id": TREE001_CANDIDATE_ID,
            "candidate_model_family": MODEL_IMPLEMENTATION_ID,
            "artifact_identity": {
                "cell14_feature_sha256_expected": EXPECTED_CELL14_FEATURE_SHA256,
                "cell10_label_sha256_expected": EXPECTED_CELL10_LABEL_SHA256,
            },
            "sample": {
                "N_raw_outer_train": int(len(frame)),
                "N_eligible": int(frame["sprint1_eligible"].sum()),
                "N_sessions_eligible": int(
                    frame.loc[frame["sprint1_eligible"], "nyse_session_date_feature"].nunique()
                ),
                "horizon_minutes": 60,
                "decision_spacing_minutes": 15,
                "overlap_scale_layers_heuristic": 4,
                "overlap_scale_is_proven_ess": False,
            },
            "diagnostics_tree001": {
                "pooled_roc_auc": _roc_auc(pooled_labels, pooled_probabilities),
                "pooled_pr_auc": _pr_auc(pooled_labels, pooled_probabilities),
                "pooled_predicted_long_coverage_p_ge_0_5": float(
                    np.mean(pooled_probabilities >= DIAGNOSTIC_LONG_THRESHOLD)
                ),
                "pooled_calibration": list(
                    _calibration_summary(pooled_labels, pooled_probabilities)
                ),
                "folds": fold_diagnostics,
                "always_flat_reference": {
                    "action": "FLAT",
                    "executed_trades": 0,
                    "net_pnl_usd": 0.0,
                    "note": "Identity reference only; no gross/P&L target column was opened.",
                },
            },
            "search_budget": {
                "target_aware_candidate_number": 2,
                "target_aware_candidate_budget": 2,
                "final_sprint1_candidate": True,
                "small_feature_rule_tested": False,
                "additional_sprint1_candidate_after_tree001": "FORBIDDEN",
            },
            "information_access": {
                "train_realized_labels": "OPENED_L1",
                "validation_outcomes": "UNOPENED",
                "final_test": "SEALED",
                "gross_pnl_future_columns": "NOT_READ",
            },
        }
    )
    return TREE001Evaluation(experiment_record=record, fold_runs=fold_runs)


def _assert_execution_authorized(authorization_token: str) -> None:
    if TREE001_EXECUTION_STATUS != "ENABLED":
        raise L1AccessError("TREE001 real execution is disabled pending separate owner authorization")
    if not TREE001_AUTHORIZATION_TOKEN or authorization_token != TREE001_AUTHORIZATION_TOKEN:
        raise L1AccessError("TREE001 explicit authorization token mismatch")


def _fresh_run_dir(output_root: str | Path) -> Path:
    run_dir = Path(output_root).expanduser().resolve() / TREE001_EXPERIMENT_ID
    if run_dir.exists():
        raise L1AccessError(
            f"EXPERIMENT_ID output already exists and cannot be overwritten: {run_dir}"
        )
    return run_dir


def run_tree001(
    *,
    features_path: str | Path,
    labels_path: str | Path,
    output_root: str | Path,
    authorization_token: str,
    code_identity: str,
    timestamp_utc: datetime | None = None,
) -> TREE001Evaluation:
    _assert_execution_authorized(authorization_token)
    code_identity = code_identity.strip()
    if not code_identity:
        raise L1AccessError("code_identity must be non-empty")

    preflight = preflight_artifacts(features_path, labels_path)
    run_dir = _fresh_run_dir(output_root)
    run_dir.mkdir(parents=True, exist_ok=False)
    pre_access = {
        "EXPERIMENT_ID": TREE001_EXPERIMENT_ID,
        "EXPLORATION_SCOPE_ID": EXPLORATION_SCOPE_ID,
        "primary_metric": PRIMARY_METRIC,
        "cost_assumption_reference": COST_ASSUMPTION_ID,
        "authorization_status": TREE001_EXECUTION_STATUS,
        "code_identity": code_identity,
        "preflight": preflight,
        "status": "PRE_ACCESS_MANIFEST_WRITTEN",
    }
    (run_dir / "pre_access_manifest.json").write_text(
        json.dumps(pre_access, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    try:
        feature_file = Path(str(preflight["features_path"]))
        label_file = Path(str(preflight["labels_path"]))
        features = _read_train_only_parquet(
            feature_file,
            columns=tuple(FEATURE_METADATA_COLUMNS) + tuple(FEATURE_COLUMNS),
        )
        labels = _read_train_only_parquet(label_file, columns=LABEL_COLUMNS)
        frame = prepare_joined_train_frame(
            features,
            labels,
            enforce_canonical_train_count=True,
        )
        evaluation = evaluate_tree001_frame(
            frame,
            timestamp_utc=timestamp_utc or datetime.now(timezone.utc),
            code_identity=code_identity,
        )
        (run_dir / "experiment_record.json").write_text(
            json.dumps(
                _json_safe(evaluation.experiment_record),
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return evaluation
    except Exception as exc:
        failure = {
            "EXPERIMENT_ID": TREE001_EXPERIMENT_ID,
            "EXPLORATION_SCOPE_ID": EXPLORATION_SCOPE_ID,
            "status": "FAILED",
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "validation_outcomes": "UNOPENED_BY_DESIGN",
            "final_test": "SEALED_BY_DESIGN",
        }
        (run_dir / "failure_record.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise

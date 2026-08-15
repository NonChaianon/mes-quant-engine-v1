from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from mes_quant.features.contract import FEATURE_COLUMNS

EXPLORATION_SCOPE_ID = "MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M"
TARGET_MAPPING_VERSION = "MES_V1_EDGE_SPRINT_1_LONG_FLAT_BINARY_V1"
TARGET_MAPPING = {
    "LONG": 1,
    "SHORT": 0,
    "NO_TRADE": 0,
}
COST_ASSUMPTION_ID = "CELL10_CONSERVATIVE_RT_USD_4_97_POINTS_0_994_V1"
ROUND_TRIP_COST_USD = 4.97
BREAK_EVEN_INDEX_POINTS = 0.994
MES_MULTIPLIER_USD_POINT = 5.0
PRIMARY_METRIC = "OOF_BINARY_LOG_LOSS"
HARNESS_EXECUTION_STATUS = "DRY_RUN_ONLY_L0"
REALIZED_TRAIN_LABEL_IO_IMPLEMENTED = False

ALLOWED_MODEL_FAMILIES = (
    "REGULARIZED_LOGISTIC_REGRESSION",
    "SHALLOW_TREE",
    "SHALLOW_TREE_ENSEMBLE",
    "SMALL_FEATURE_RULE",
)

INTERESTING_ENOUGH = "INTERESTING_ENOUGH_TO_CONTINUE"
NO_EDGE_IN_SCOPE = "NO_USABLE_EDGE_IDENTIFIED_IN_SPRINT_1_SCOPE"

_FLOAT64_EPS = float(np.finfo(np.float64).eps)
_EXPERIMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


class SprintHarnessError(ValueError):
    """Raised when a Sprint-1 dry-run contract is violated."""


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    hypothesis: str
    feature_subset: tuple[str, ...]
    model_family: str
    parameters: Mapping[str, object]
    fold_definition: str
    primary_metric: str = PRIMARY_METRIC
    exploration_scope_id: str = EXPLORATION_SCOPE_ID
    target_mapping_version: str = TARGET_MAPPING_VERSION
    cost_assumption_reference: str = COST_ASSUMPTION_ID

    def __post_init__(self) -> None:
        experiment_id = self.experiment_id.strip()
        hypothesis = self.hypothesis.strip()
        fold_definition = self.fold_definition.strip()
        feature_subset = tuple(self.feature_subset)

        if not _EXPERIMENT_ID_PATTERN.fullmatch(experiment_id):
            raise SprintHarnessError(
                "EXPERIMENT_ID must be 3-128 safe characters and start with alphanumeric"
            )
        if not hypothesis:
            raise SprintHarnessError("hypothesis must be non-empty")
        if not fold_definition:
            raise SprintHarnessError("fold_definition must be non-empty")
        if not feature_subset:
            raise SprintHarnessError("feature_subset must be non-empty")
        if len(set(feature_subset)) != len(feature_subset):
            raise SprintHarnessError("feature_subset contains duplicates")

        unknown_features = sorted(set(feature_subset) - set(FEATURE_COLUMNS))
        if unknown_features:
            raise SprintHarnessError(
                "feature_subset contains non-authorized Cell 14 features: "
                + ", ".join(unknown_features)
            )
        if self.model_family not in ALLOWED_MODEL_FAMILIES:
            raise SprintHarnessError(f"model_family is outside Sprint 1: {self.model_family}")
        if self.primary_metric != PRIMARY_METRIC:
            raise SprintHarnessError("Sprint 1 primary metric is frozen")
        if self.exploration_scope_id != EXPLORATION_SCOPE_ID:
            raise SprintHarnessError("EXPLORATION_SCOPE_ID is frozen")
        if self.target_mapping_version != TARGET_MAPPING_VERSION:
            raise SprintHarnessError("target mapping version is frozen")
        if self.cost_assumption_reference != COST_ASSUMPTION_ID:
            raise SprintHarnessError("cost assumption reference is frozen")

        parameter_dict = dict(self.parameters)
        if any(not isinstance(key, str) or not key for key in parameter_dict):
            raise SprintHarnessError("parameter keys must be non-empty strings")
        try:
            json.dumps(parameter_dict, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise SprintHarnessError("parameters must be finite JSON-compatible metadata") from exc

        object.__setattr__(self, "experiment_id", experiment_id)
        object.__setattr__(self, "hypothesis", hypothesis)
        object.__setattr__(self, "fold_definition", fold_definition)
        object.__setattr__(self, "feature_subset", feature_subset)
        object.__setattr__(self, "parameters", parameter_dict)


@dataclass(frozen=True)
class FoldEvaluationInput:
    fold_id: str
    train_labels: Sequence[int | float]
    holdout_labels: Sequence[int | float]
    candidate_probabilities: Sequence[float]


@dataclass(frozen=True)
class FoldEvaluationResult:
    fold_id: str
    n_train: int
    n_holdout: int
    train_long_rate: float
    baseline_log_loss: float
    candidate_log_loss: float
    log_loss_improvement: float
    baseline_brier: float
    candidate_brier: float
    brier_improvement: float


@dataclass(frozen=True)
class SprintEvaluation:
    n_folds: int
    n_holdout_total: int
    baseline_oof_log_loss: float
    candidate_oof_log_loss: float
    log_loss_improvement: float
    median_fold_log_loss_improvement: float
    baseline_oof_brier: float
    candidate_oof_brier: float
    brier_improvement: float
    interesting_enough_to_continue: bool
    disposition: str
    folds: tuple[FoldEvaluationResult, ...]


def assert_unique_experiment_id(
    experiment_id: str,
    existing_experiment_ids: Iterable[str],
) -> None:
    existing = {str(value) for value in existing_experiment_ids}
    if experiment_id in existing:
        raise SprintHarnessError(f"duplicate EXPERIMENT_ID: {experiment_id}")


def _binary_labels(values: Sequence[int | float], *, name: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise SprintHarnessError(f"{name} must be numeric binary labels") from exc
    if array.ndim != 1 or array.size == 0:
        raise SprintHarnessError(f"{name} must be a non-empty one-dimensional array")
    if not np.isfinite(array).all():
        raise SprintHarnessError(f"{name} contains non-finite labels")
    if not np.isin(array, (0.0, 1.0)).all():
        raise SprintHarnessError(f"{name} must contain only 0/1")
    return array.astype(np.int8, copy=False)


def _probabilities(values: Sequence[float], *, name: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise SprintHarnessError(f"{name} must be numeric probabilities") from exc
    if array.ndim != 1 or array.size == 0:
        raise SprintHarnessError(f"{name} must be a non-empty one-dimensional array")
    if not np.isfinite(array).all():
        raise SprintHarnessError(f"{name} contains non-finite probabilities")
    if ((array < 0.0) | (array > 1.0)).any():
        raise SprintHarnessError(f"{name} must stay within [0, 1]")
    return array


def binary_log_loss(
    labels: Sequence[int | float],
    probabilities: Sequence[float],
) -> float:
    y_true = _binary_labels(labels, name="labels")
    prob = _probabilities(probabilities, name="probabilities")
    if y_true.size != prob.size:
        raise SprintHarnessError("label/probability length mismatch")

    clipped = np.clip(prob, _FLOAT64_EPS, 1.0 - _FLOAT64_EPS)
    losses = -(y_true * np.log(clipped) + (1 - y_true) * np.log1p(-clipped))
    return float(np.mean(losses))


def brier_score(
    labels: Sequence[int | float],
    probabilities: Sequence[float],
) -> float:
    y_true = _binary_labels(labels, name="labels")
    prob = _probabilities(probabilities, name="probabilities")
    if y_true.size != prob.size:
        raise SprintHarnessError("label/probability length mismatch")
    return float(np.mean((prob - y_true) ** 2))


def evaluate_fold(fold: FoldEvaluationInput) -> FoldEvaluationResult:
    fold_id = fold.fold_id.strip()
    if not fold_id:
        raise SprintHarnessError("fold_id must be non-empty")

    train_labels = _binary_labels(fold.train_labels, name=f"{fold_id}.train_labels")
    holdout_labels = _binary_labels(fold.holdout_labels, name=f"{fold_id}.holdout_labels")
    candidate_probabilities = _probabilities(
        fold.candidate_probabilities,
        name=f"{fold_id}.candidate_probabilities",
    )
    if holdout_labels.size != candidate_probabilities.size:
        raise SprintHarnessError(f"{fold_id} holdout/prediction length mismatch")

    train_long_rate = float(np.mean(train_labels))
    baseline_probabilities = np.full(
        holdout_labels.size,
        train_long_rate,
        dtype=np.float64,
    )
    baseline_log_loss = binary_log_loss(holdout_labels, baseline_probabilities)
    candidate_log_loss = binary_log_loss(holdout_labels, candidate_probabilities)
    baseline_brier = brier_score(holdout_labels, baseline_probabilities)
    candidate_brier = brier_score(holdout_labels, candidate_probabilities)

    return FoldEvaluationResult(
        fold_id=fold_id,
        n_train=int(train_labels.size),
        n_holdout=int(holdout_labels.size),
        train_long_rate=train_long_rate,
        baseline_log_loss=baseline_log_loss,
        candidate_log_loss=candidate_log_loss,
        log_loss_improvement=baseline_log_loss - candidate_log_loss,
        baseline_brier=baseline_brier,
        candidate_brier=candidate_brier,
        brier_improvement=baseline_brier - candidate_brier,
    )


def evaluate_sprint(folds: Sequence[FoldEvaluationInput]) -> SprintEvaluation:
    if not folds:
        raise SprintHarnessError("at least one OOF fold is required")

    fold_ids = [fold.fold_id.strip() for fold in folds]
    if len(set(fold_ids)) != len(fold_ids):
        raise SprintHarnessError("fold IDs must be unique")

    results: list[FoldEvaluationResult] = []
    all_labels: list[np.ndarray] = []
    all_candidate: list[np.ndarray] = []
    all_baseline: list[np.ndarray] = []

    for fold in folds:
        result = evaluate_fold(fold)
        train_labels = _binary_labels(fold.train_labels, name=f"{result.fold_id}.train_labels")
        holdout_labels = _binary_labels(
            fold.holdout_labels,
            name=f"{result.fold_id}.holdout_labels",
        )
        candidate = _probabilities(
            fold.candidate_probabilities,
            name=f"{result.fold_id}.candidate_probabilities",
        )
        baseline = np.full(
            holdout_labels.size,
            float(np.mean(train_labels)),
            dtype=np.float64,
        )
        results.append(result)
        all_labels.append(holdout_labels)
        all_candidate.append(candidate)
        all_baseline.append(baseline)

    labels = np.concatenate(all_labels)
    candidate_probabilities = np.concatenate(all_candidate)
    baseline_probabilities = np.concatenate(all_baseline)

    baseline_log_loss = binary_log_loss(labels, baseline_probabilities)
    candidate_log_loss = binary_log_loss(labels, candidate_probabilities)
    overall_improvement = baseline_log_loss - candidate_log_loss
    median_fold_improvement = float(
        np.median([result.log_loss_improvement for result in results])
    )

    baseline_brier = brier_score(labels, baseline_probabilities)
    candidate_brier = brier_score(labels, candidate_probabilities)
    continuation = overall_improvement > 0.0 and median_fold_improvement > 0.0

    return SprintEvaluation(
        n_folds=len(results),
        n_holdout_total=int(labels.size),
        baseline_oof_log_loss=baseline_log_loss,
        candidate_oof_log_loss=candidate_log_loss,
        log_loss_improvement=overall_improvement,
        median_fold_log_loss_improvement=median_fold_improvement,
        baseline_oof_brier=baseline_brier,
        candidate_oof_brier=candidate_brier,
        brier_improvement=baseline_brier - candidate_brier,
        interesting_enough_to_continue=continuation,
        disposition=INTERESTING_ENOUGH if continuation else NO_EDGE_IN_SCOPE,
        folds=tuple(results),
    )


def build_experiment_history_record(
    spec: ExperimentSpec,
    evaluation: SprintEvaluation,
    *,
    timestamp_utc: datetime,
    code_identity: str,
) -> dict[str, object]:
    if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() != timedelta(0):
        raise SprintHarnessError("timestamp_utc must be timezone-aware UTC")
    code_identity = code_identity.strip()
    if not code_identity:
        raise SprintHarnessError("code_identity must be non-empty")

    fold_records = [
        {
            "fold_id": fold.fold_id,
            "n_train": fold.n_train,
            "n_holdout": fold.n_holdout,
            "train_long_rate": fold.train_long_rate,
            "baseline_log_loss": fold.baseline_log_loss,
            "candidate_log_loss": fold.candidate_log_loss,
            "log_loss_improvement": fold.log_loss_improvement,
            "baseline_brier": fold.baseline_brier,
            "candidate_brier": fold.candidate_brier,
            "brier_improvement": fold.brier_improvement,
        }
        for fold in evaluation.folds
    ]

    return {
        "EXPERIMENT_ID": spec.experiment_id,
        "timestamp_utc": timestamp_utc.isoformat().replace("+00:00", "Z"),
        "EXPLORATION_SCOPE_ID": spec.exploration_scope_id,
        "hypothesis": spec.hypothesis,
        "feature_subset": list(spec.feature_subset),
        "target_mapping_version": spec.target_mapping_version,
        "target_mapping": dict(TARGET_MAPPING),
        "cost_assumption_reference": spec.cost_assumption_reference,
        "model_family": spec.model_family,
        "parameters": dict(spec.parameters),
        "fold_definition": spec.fold_definition,
        "primary_metric": spec.primary_metric,
        "diagnostics": {
            "baseline_oof_brier": evaluation.baseline_oof_brier,
            "candidate_oof_brier": evaluation.candidate_oof_brier,
            "brier_improvement": evaluation.brier_improvement,
            "folds": fold_records,
        },
        "result": {
            "n_folds": evaluation.n_folds,
            "n_holdout_total": evaluation.n_holdout_total,
            "baseline_oof_log_loss": evaluation.baseline_oof_log_loss,
            "candidate_oof_log_loss": evaluation.candidate_oof_log_loss,
            "LOG_LOSS_IMPROVEMENT": evaluation.log_loss_improvement,
            "median_fold_log_loss_improvement": (
                evaluation.median_fold_log_loss_improvement
            ),
            "interesting_enough_to_continue": evaluation.interesting_enough_to_continue,
        },
        "disposition": evaluation.disposition,
        "code_identity": code_identity,
        "harness_execution_status": HARNESS_EXECUTION_STATUS,
    }

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from mes_quant.exploration.sprint1 import (
    COST_ASSUMPTION_ID,
    EXPLORATION_SCOPE_ID,
    PRIMARY_METRIC,
    TARGET_MAPPING,
    ExperimentSpec,
    FoldEvaluationInput,
    SprintHarnessError,
    build_experiment_history_record,
    evaluate_sprint,
)
from mes_quant.features.contract import FEATURE_COLUMNS

FIRST_L1_EXPERIMENT_ID = "MES_S1_LR001_20260815T095100Z"
L1_AUTHORIZATION_TOKEN = "OWNER_AUTHORIZED_L1_SPRINT1_20260815"

EXPECTED_CELL14_FEATURE_SHA256 = (
    "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452"
)
EXPECTED_CELL10_LABEL_SHA256 = (
    "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0"
)
EXPECTED_OUTER_TRAIN_ROWS = 25685

L2_LAMBDA = 0.001
MAX_ITERATIONS = 50
GRADIENT_TOL = 1e-8
ARMIJO_CONSTANT = 1e-4
BACKTRACK_SHRINK = 0.5
MINIMUM_STEP = 2.0**-20
DIAGNOSTIC_LONG_THRESHOLD = 0.5
CALIBRATION_BINS = 10

FOLD_SPECS = (
    ("WF_2022", "role_wf_2022", 2022),
    ("WF_2023", "role_wf_2023", 2023),
)

FEATURE_METADATA_COLUMNS = (
    "decision_id",
    "decision_time",
    "nyse_session_date",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "feature_row_usable",
)
LABEL_COLUMNS = (
    "decision_id",
    "decision_time",
    "label_end_time",
    "nyse_session_date",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "label_usable",
    "economic_label_primary",
)

MODEL_FAMILY = "REGULARIZED_LOGISTIC_REGRESSION"
FOLD_DEFINITION = "CELL8_WF_2022_WF_2023_OUTER_TRAIN_ONLY_PURGED_60M"


class L1AccessError(RuntimeError):
    """Raised when the authorized TRAIN-only access boundary is violated."""


class NumericalExperimentError(RuntimeError):
    """Raised when the frozen LR001 numerical path cannot complete."""


@dataclass(frozen=True)
class FoldRun:
    fold_id: str
    role_column: str
    validation_year: int
    train_rows: int
    holdout_rows: int
    train_sessions: int
    holdout_sessions: int
    train_long_rate: float
    holdout_long_rate: float
    probabilities: np.ndarray
    holdout_labels: np.ndarray
    holdout_decision_ids: tuple[str, ...]
    roc_auc: float
    pr_auc: float
    predicted_long_coverage: float
    calibration: tuple[dict[str, object], ...]
    optimizer: dict[str, object]


@dataclass(frozen=True)
class LR001Evaluation:
    experiment_record: dict[str, object]
    fold_runs: tuple[FoldRun, ...]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _strict_boolean(series: pd.Series, *, name: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.astype(bool)
    tokens = series.astype("string").str.strip().str.lower()
    parsed = tokens.map({"true": True, "false": False})
    if parsed.isna().any():
        bad = sorted(tokens.loc[parsed.isna()].dropna().unique().tolist())
        raise L1AccessError(f"{name} contains invalid boolean tokens: {bad}")
    return parsed.astype(bool)


def preflight_artifacts(
    features_path: str | Path,
    labels_path: str | Path,
) -> dict[str, object]:
    """Verify exact artifact identity and schema without deserializing target rows."""
    feature_file = Path(features_path).expanduser().resolve()
    label_file = Path(labels_path).expanduser().resolve()
    for name, path in (("Cell 14 features", feature_file), ("Cell 10 labels", label_file)):
        if not path.is_file():
            raise L1AccessError(f"{name} artifact does not exist: {path}")

    feature_hash = sha256_file(feature_file)
    label_hash = sha256_file(label_file)
    if feature_hash != EXPECTED_CELL14_FEATURE_SHA256:
        raise L1AccessError(
            "Cell 14 feature SHA-256 mismatch: "
            f"{feature_hash} != {EXPECTED_CELL14_FEATURE_SHA256}"
        )
    if label_hash != EXPECTED_CELL10_LABEL_SHA256:
        raise L1AccessError(
            "Cell 10 label SHA-256 mismatch: "
            f"{label_hash} != {EXPECTED_CELL10_LABEL_SHA256}"
        )

    feature_schema = set(pq.ParquetFile(feature_file).schema.names)
    label_schema = set(pq.ParquetFile(label_file).schema.names)
    required_feature = set(FEATURE_METADATA_COLUMNS) | set(FEATURE_COLUMNS)
    required_label = set(LABEL_COLUMNS)
    missing_feature = sorted(required_feature - feature_schema)
    missing_label = sorted(required_label - label_schema)
    if missing_feature:
        raise L1AccessError("Cell 14 artifact missing columns: " + ", ".join(missing_feature))
    if missing_label:
        raise L1AccessError("Cell 10 artifact missing columns: " + ", ".join(missing_label))

    return {
        "features_path": str(feature_file),
        "labels_path": str(label_file),
        "cell14_feature_sha256": feature_hash,
        "cell10_label_sha256": label_hash,
        "status": "PREFLIGHT_PASS_NO_TARGET_ROWS_DESERIALIZED",
    }


def _read_train_only_parquet(path: Path, *, columns: Sequence[str]) -> pd.DataFrame:
    frame = pd.read_parquet(
        path,
        columns=list(columns),
        filters=[("outer_partition", "==", "TRAIN")],
        engine="pyarrow",
    )
    if "outer_partition" not in frame.columns:
        raise L1AccessError("TRAIN-only reader did not return outer_partition")
    if frame.empty:
        raise L1AccessError(f"TRAIN-only read returned zero rows: {path}")
    partitions = set(frame["outer_partition"].astype(str).unique().tolist())
    if partitions != {"TRAIN"}:
        raise L1AccessError(
            "TRAIN-only predicate failed; returned partitions: " + ", ".join(sorted(partitions))
        )
    return frame


def load_authorized_train_artifacts(
    features_path: str | Path,
    labels_path: str | Path,
) -> pd.DataFrame:
    preflight = preflight_artifacts(features_path, labels_path)
    feature_file = Path(str(preflight["features_path"]))
    label_file = Path(str(preflight["labels_path"]))
    features = _read_train_only_parquet(
        feature_file,
        columns=tuple(FEATURE_METADATA_COLUMNS) + tuple(FEATURE_COLUMNS),
    )
    labels = _read_train_only_parquet(label_file, columns=LABEL_COLUMNS)
    return prepare_joined_train_frame(
        features,
        labels,
        enforce_canonical_train_count=True,
    )


def prepare_joined_train_frame(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    enforce_canonical_train_count: bool,
) -> pd.DataFrame:
    required_feature = set(FEATURE_METADATA_COLUMNS) | set(FEATURE_COLUMNS)
    required_label = set(LABEL_COLUMNS)
    missing_feature = sorted(required_feature - set(features.columns))
    missing_label = sorted(required_label - set(labels.columns))
    if missing_feature:
        raise L1AccessError("Cell 14 TRAIN frame missing columns: " + ", ".join(missing_feature))
    if missing_label:
        raise L1AccessError("Cell 10 TRAIN frame missing columns: " + ", ".join(missing_label))

    features = features.copy()
    labels = labels.copy()
    for name, frame in (("features", features), ("labels", labels)):
        partitions = set(frame["outer_partition"].astype(str).unique().tolist())
        if partitions != {"TRAIN"}:
            raise L1AccessError(f"{name} frame contains non-TRAIN partitions: {sorted(partitions)}")
        if frame["decision_id"].duplicated().any():
            raise L1AccessError(f"{name} frame contains duplicate decision_id")
        if enforce_canonical_train_count and len(frame) != EXPECTED_OUTER_TRAIN_ROWS:
            raise L1AccessError(
                f"{name} TRAIN row count changed: {len(frame)} != {EXPECTED_OUTER_TRAIN_ROWS}"
            )

    features["decision_id"] = features["decision_id"].astype(str)
    labels["decision_id"] = labels["decision_id"].astype(str)
    features["decision_time"] = pd.to_datetime(features["decision_time"], utc=True, errors="raise")
    labels["decision_time"] = pd.to_datetime(labels["decision_time"], utc=True, errors="raise")
    labels["label_end_time"] = pd.to_datetime(labels["label_end_time"], utc=True, errors="raise")
    features["nyse_session_date"] = pd.to_datetime(
        features["nyse_session_date"], errors="raise"
    ).dt.date
    labels["nyse_session_date"] = pd.to_datetime(
        labels["nyse_session_date"], errors="raise"
    ).dt.date
    features["feature_row_usable"] = _strict_boolean(
        features["feature_row_usable"], name="feature_row_usable"
    )
    labels["label_usable"] = _strict_boolean(labels["label_usable"], name="label_usable")

    merged = features.merge(
        labels,
        on="decision_id",
        how="inner",
        validate="one_to_one",
        suffixes=("_feature", "_label"),
    )
    if len(merged) != len(features) or len(merged) != len(labels):
        raise L1AccessError("Cell 14 / Cell 10 TRAIN decision_id sets do not match one-to-one")

    for logical_name, left, right in (
        ("decision_time", "decision_time_feature", "decision_time_label"),
        ("nyse_session_date", "nyse_session_date_feature", "nyse_session_date_label"),
        ("outer_partition", "outer_partition_feature", "outer_partition_label"),
        ("role_wf_2022", "role_wf_2022_feature", "role_wf_2022_label"),
        ("role_wf_2023", "role_wf_2023_feature", "role_wf_2023_label"),
    ):
        if not merged[left].equals(merged[right]):
            raise L1AccessError(f"Cell 14 / Cell 10 mismatch in {logical_name}")

    if not merged["outer_partition_feature"].eq("TRAIN").all():
        raise L1AccessError("Merged frame escaped outer TRAIN")
    expected_label_end = merged["decision_time_label"] + pd.Timedelta(minutes=60)
    if not np.array_equal(merged["label_end_time"].array.asi8, expected_label_end.array.asi8):
        raise L1AccessError("Cell 10 label_end_time is not exactly +60m")

    usable_label_tokens = set(
        merged.loc[merged["label_usable"], "economic_label_primary"].astype(str).unique().tolist()
    )
    if not usable_label_tokens.issubset(set(TARGET_MAPPING)):
        raise L1AccessError(
            "Unexpected usable economic labels: " + ", ".join(sorted(usable_label_tokens))
        )

    eligible = merged["feature_row_usable"] & merged["label_usable"]
    if not eligible.any():
        raise L1AccessError("No rows are jointly feature-usable and label-usable")
    feature_matrix = merged.loc[eligible, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    if not np.isfinite(feature_matrix).all():
        raise L1AccessError("Eligible TRAIN feature matrix contains non-finite values")

    merged["sprint1_eligible"] = eligible
    merged["sprint1_target"] = np.nan
    mapped = merged.loc[eligible, "economic_label_primary"].astype(str).map(TARGET_MAPPING)
    if mapped.isna().any():
        raise L1AccessError("Sprint-1 target mapping produced missing values")
    merged.loc[eligible, "sprint1_target"] = mapped.to_numpy(dtype=np.int8)
    return merged.sort_values(
        ["decision_time_feature", "decision_id"], kind="stable"
    ).reset_index(drop=True)


def _standardize(
    train_x: np.ndarray,
    holdout_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    if train_x.ndim != 2 or holdout_x.ndim != 2:
        raise NumericalExperimentError("Feature matrices must be two-dimensional")
    if train_x.shape[1] != len(FEATURE_COLUMNS) or holdout_x.shape[1] != len(FEATURE_COLUMNS):
        raise NumericalExperimentError("Feature matrix width is not locked29")
    if not np.isfinite(train_x).all() or not np.isfinite(holdout_x).all():
        raise NumericalExperimentError("Non-finite feature values reached model preprocessing")

    mean = train_x.mean(axis=0)
    scale = train_x.std(axis=0, ddof=0)
    zero_mask = (~np.isfinite(scale)) | (scale <= np.finfo(np.float64).eps)
    scale = scale.copy()
    scale[zero_mask] = 1.0
    train_z = (train_x - mean) / scale
    holdout_z = (holdout_x - mean) / scale
    zero_features = tuple(
        name for name, is_zero in zip(FEATURE_COLUMNS, zero_mask, strict=True) if is_zero
    )
    return train_z, holdout_z, zero_features


def _sigmoid(logits: np.ndarray) -> np.ndarray:
    return np.exp(-np.logaddexp(0.0, -logits))


def _objective(design: np.ndarray, labels: np.ndarray, beta: np.ndarray) -> float:
    logits = design @ beta
    data_loss = np.mean(np.logaddexp(0.0, logits) - labels * logits)
    penalty = 0.5 * L2_LAMBDA * float(beta[1:] @ beta[1:])
    return float(data_loss + penalty)


def fit_frozen_logistic(
    train_x: np.ndarray,
    train_y: Sequence[int | float],
) -> tuple[np.ndarray, dict[str, object]]:
    labels = np.asarray(train_y, dtype=np.float64)
    if labels.ndim != 1 or labels.size != train_x.shape[0]:
        raise NumericalExperimentError("Training label shape mismatch")
    if not np.isin(labels, (0.0, 1.0)).all():
        raise NumericalExperimentError("Training labels are not binary")

    design = np.column_stack([np.ones(train_x.shape[0]), train_x])
    beta = np.zeros(design.shape[1], dtype=np.float64)
    penalty_diag = np.ones(design.shape[1], dtype=np.float64)
    penalty_diag[0] = 0.0
    accepted_iteration = 0
    gradient_norm = math.inf

    for iteration in range(1, MAX_ITERATIONS + 1):
        probabilities = _sigmoid(design @ beta)
        gradient = design.T @ (probabilities - labels) / labels.size
        gradient += L2_LAMBDA * penalty_diag * beta
        gradient_norm = float(np.max(np.abs(gradient)))
        if not np.isfinite(gradient_norm):
            raise NumericalExperimentError("Non-finite logistic gradient")
        if gradient_norm <= GRADIENT_TOL:
            accepted_iteration = iteration - 1
            break

        weights = probabilities * (1.0 - probabilities)
        hessian = (design.T * weights) @ design / labels.size
        hessian += np.diag(L2_LAMBDA * penalty_diag)
        try:
            newton_step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError as exc:
            raise NumericalExperimentError("Frozen logistic Hessian solve failed") from exc

        direction = -newton_step
        directional_derivative = float(gradient @ direction)
        if not np.isfinite(directional_derivative) or directional_derivative >= 0.0:
            raise NumericalExperimentError("Frozen Newton direction is not a descent direction")

        current_objective = _objective(design, labels, beta)
        step = 1.0
        accepted = False
        while step >= MINIMUM_STEP:
            candidate_beta = beta + step * direction
            candidate_objective = _objective(design, labels, candidate_beta)
            bound = current_objective + ARMIJO_CONSTANT * step * directional_derivative
            if np.isfinite(candidate_objective) and candidate_objective <= bound:
                beta = candidate_beta
                accepted = True
                accepted_iteration = iteration
                break
            step *= BACKTRACK_SHRINK
        if not accepted:
            raise NumericalExperimentError("Frozen logistic line search failed")
    else:
        probabilities = _sigmoid(design @ beta)
        gradient = design.T @ (probabilities - labels) / labels.size
        gradient += L2_LAMBDA * penalty_diag * beta
        gradient_norm = float(np.max(np.abs(gradient)))
        if gradient_norm > GRADIENT_TOL:
            raise NumericalExperimentError(
                f"Frozen logistic did not converge in {MAX_ITERATIONS} iterations"
            )

    return beta, {
        "iterations": accepted_iteration,
        "gradient_inf_norm": gradient_norm,
        "objective": _objective(design, labels, beta),
    }


def _roc_auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=np.int8)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    positives = int(labels.sum())
    negatives = int(labels.size - positives)
    if positives == 0 or negatives == 0:
        return float("nan")

    order = np.argsort(probabilities, kind="mergesort")
    sorted_prob = probabilities[order]
    ranks = np.empty(labels.size, dtype=np.float64)
    start = 0
    while start < labels.size:
        end = start + 1
        while end < labels.size and sorted_prob[end] == sorted_prob[start]:
            end += 1
        average_rank = 0.5 * ((start + 1) + end)
        ranks[order[start:end]] = average_rank
        start = end
    rank_sum = float(ranks[labels == 1].sum())
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _pr_auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=np.int8)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    positives = int(labels.sum())
    if positives == 0:
        return float("nan")
    order = np.argsort(-probabilities, kind="mergesort")
    sorted_labels = labels[order]
    sorted_prob = probabilities[order]
    tp = np.cumsum(sorted_labels == 1)
    fp = np.cumsum(sorted_labels == 0)
    distinct = np.r_[sorted_prob[1:] != sorted_prob[:-1], True]
    tp = tp[distinct].astype(np.float64)
    fp = fp[distinct].astype(np.float64)
    recall = np.r_[0.0, tp / positives]
    precision = np.r_[1.0, tp / (tp + fp)]
    return float(np.trapezoid(precision, recall))


def _calibration_summary(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> tuple[dict[str, object], ...]:
    bin_index = np.minimum(
        (probabilities * CALIBRATION_BINS).astype(int), CALIBRATION_BINS - 1
    )
    records: list[dict[str, object]] = []
    for index in range(CALIBRATION_BINS):
        mask = bin_index == index
        if not mask.any():
            continue
        records.append(
            {
                "bin": index,
                "lower": index / CALIBRATION_BINS,
                "upper": (index + 1) / CALIBRATION_BINS,
                "rows": int(mask.sum()),
                "mean_probability_long": float(probabilities[mask].mean()),
                "observed_long_rate": float(labels[mask].mean()),
            }
        )
    return tuple(records)


def _fit_predict_fold(
    frame: pd.DataFrame,
    *,
    fold_id: str,
    role_column: str,
    validation_year: int,
) -> FoldRun:
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

    train_x_raw = train.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    holdout_x_raw = holdout.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    train_y = train["sprint1_target"].to_numpy(dtype=np.int8)
    holdout_y = holdout["sprint1_target"].to_numpy(dtype=np.int8)
    train_x, holdout_x, zero_features = _standardize(train_x_raw, holdout_x_raw)
    beta, optimizer = fit_frozen_logistic(train_x, train_y)
    probabilities = _sigmoid(
        np.column_stack([np.ones(holdout_x.shape[0]), holdout_x]) @ beta
    )
    if not np.isfinite(probabilities).all():
        raise NumericalExperimentError(f"{fold_id} produced non-finite probabilities")
    optimizer = {**optimizer, "zero_variance_features": list(zero_features)}

    return FoldRun(
        fold_id=fold_id,
        role_column=role_column,
        validation_year=validation_year,
        train_rows=int(len(train)),
        holdout_rows=int(len(holdout)),
        train_sessions=int(train["nyse_session_date_feature"].nunique()),
        holdout_sessions=int(holdout["nyse_session_date_feature"].nunique()),
        train_long_rate=float(train_y.mean()),
        holdout_long_rate=float(holdout_y.mean()),
        probabilities=probabilities,
        holdout_labels=holdout_y,
        holdout_decision_ids=tuple(holdout["decision_id"].astype(str).tolist()),
        roc_auc=_roc_auc(holdout_y, probabilities),
        pr_auc=_pr_auc(holdout_y, probabilities),
        predicted_long_coverage=float(np.mean(probabilities >= DIAGNOSTIC_LONG_THRESHOLD)),
        calibration=_calibration_summary(holdout_y, probabilities),
        optimizer=optimizer,
    )


def evaluate_lr001_frame(
    frame: pd.DataFrame,
    *,
    timestamp_utc: datetime,
    code_identity: str,
) -> LR001Evaluation:
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
                "roc_auc": fold.roc_auc,
                "pr_auc": fold.pr_auc,
                "predicted_long_coverage_p_ge_0_5": fold.predicted_long_coverage,
                "calibration": list(fold.calibration),
                "optimizer": fold.optimizer,
            }
        )

    sprint_evaluation = evaluate_sprint(fold_inputs)
    pooled_labels = np.concatenate([fold.holdout_labels for fold in fold_runs])
    pooled_probabilities = np.concatenate([fold.probabilities for fold in fold_runs])
    spec = ExperimentSpec(
        experiment_id=FIRST_L1_EXPERIMENT_ID,
        hypothesis=(
            "Fixed L2-regularized logistic regression on the locked29 Cell 14 feature universe "
            "improves TRAIN-only OOF binary log loss versus the fold-correct TRAIN prior."
        ),
        feature_subset=tuple(FEATURE_COLUMNS),
        model_family=MODEL_FAMILY,
        parameters={
            "feature_count": len(FEATURE_COLUMNS),
            "preprocessing": "FOLD_LOCAL_ZSCORE_DDOF0_NO_IMPUTATION",
            "l2_lambda": L2_LAMBDA,
            "solver": "DETERMINISTIC_NEWTON_IRLS_BACKTRACKING",
            "max_iterations": MAX_ITERATIONS,
            "gradient_inf_norm_tolerance": GRADIENT_TOL,
            "armijo_constant": ARMIJO_CONSTANT,
            "backtracking_shrink": BACKTRACK_SHRINK,
            "minimum_step": MINIMUM_STEP,
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
    record.update(
        {
            "observed_access_level": "L1",
            "authorization_reference": "Owner chat authorization 2026-08-15 / Issue #26",
            "candidate_id": "LR001",
            "artifact_identity": {
                "cell14_feature_sha256_expected": EXPECTED_CELL14_FEATURE_SHA256,
                "cell10_label_sha256_expected": EXPECTED_CELL10_LABEL_SHA256,
            },
            "sample": {
                "N_raw_outer_train": int(len(frame)),
                "N_eligible": int(frame["sprint1_eligible"].sum()),
                "N_sessions_eligible": int(
                    frame.loc[
                        frame["sprint1_eligible"], "nyse_session_date_feature"
                    ].nunique()
                ),
                "horizon_minutes": 60,
                "decision_spacing_minutes": 15,
                "overlap_scale_layers_heuristic": 4,
                "overlap_scale_is_proven_ess": False,
            },
            "diagnostics_lr001": {
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
            "information_access": {
                "train_realized_labels": "OPENED_L1",
                "validation_outcomes": "UNOPENED",
                "final_test": "SEALED",
                "gross_pnl_future_columns": "NOT_READ",
            },
        }
    )
    return LR001Evaluation(experiment_record=record, fold_runs=fold_runs)


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    return value


def run_lr001(
    *,
    features_path: str | Path,
    labels_path: str | Path,
    output_root: str | Path,
    authorization_token: str,
    code_identity: str,
    timestamp_utc: datetime | None = None,
) -> LR001Evaluation:
    if authorization_token != L1_AUTHORIZATION_TOKEN:
        raise L1AccessError("Explicit L1 authorization token mismatch")
    code_identity = code_identity.strip()
    if not code_identity:
        raise L1AccessError("code_identity must be non-empty")

    preflight = preflight_artifacts(features_path, labels_path)
    root = Path(output_root).expanduser().resolve()
    run_dir = root / FIRST_L1_EXPERIMENT_ID
    if run_dir.exists():
        raise L1AccessError(
            f"EXPERIMENT_ID output already exists and cannot be overwritten: {run_dir}"
        )
    run_dir.mkdir(parents=True, exist_ok=False)
    pre_access = {
        "EXPERIMENT_ID": FIRST_L1_EXPERIMENT_ID,
        "EXPLORATION_SCOPE_ID": EXPLORATION_SCOPE_ID,
        "primary_metric": PRIMARY_METRIC,
        "cost_assumption_reference": COST_ASSUMPTION_ID,
        "authorization": L1_AUTHORIZATION_TOKEN,
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
        evaluation = evaluate_lr001_frame(
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
            "EXPERIMENT_ID": FIRST_L1_EXPERIMENT_ID,
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

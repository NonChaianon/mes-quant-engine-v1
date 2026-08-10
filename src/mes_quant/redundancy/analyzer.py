"""Stage B feature redundancy and stability analysis."""

from __future__ import annotations

import pandas as pd

from mes_quant.redundancy.contract import (
    COMMON_COHORT_POLICY,
    FOLD_ROLE_COLUMNS,
    HARD_REDUNDANCY_PEARSON_ABS,
    HARD_REDUNDANCY_SPEARMAN_ABS,
    POLICY_STATUS,
    POLICY_VERSION,
    REVIEW_CORRELATION_ABS,
)


def assert_stage_b_contract_locked() -> None:
    """Stop immediately if Stage B policy is not locked."""

    if POLICY_STATUS != "LOCKED_EXECUTABLE":
        raise RuntimeError(
            f"Stage B policy must be LOCKED_EXECUTABLE, got {POLICY_STATUS!r}"
        )


def get_train_mask(df: pd.DataFrame, fold_role_column: str) -> pd.Series:
    """Return rows that belong to TRAIN for one walk-forward fold."""

    if fold_role_column not in FOLD_ROLE_COLUMNS:
        raise ValueError(f"Unknown fold role column: {fold_role_column}")

    if fold_role_column not in df.columns:
        raise KeyError(f"Missing required column: {fold_role_column}")

    return df[fold_role_column].eq("TRAIN")
def get_common_complete_case_train_mask(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> pd.Series:
    """Select TRAIN rows where every candidate feature is available."""

    if COMMON_COHORT_POLICY != "FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD":
        raise RuntimeError(
            f"Unsupported common cohort policy: {COMMON_COHORT_POLICY!r}"
        )

    missing_columns = [
        column for column in feature_columns if column not in df.columns
    ]

    if missing_columns:
        raise KeyError(
            f"Missing candidate feature columns: {missing_columns}"
        )

    train_mask = get_train_mask(df, fold_role_column)
    complete_case_mask = df[feature_columns].notna().all(axis=1)

    return train_mask & complete_case_mask
def compute_fold_correlations(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute Pearson, Spearman, and pairwise sample counts on TRAIN only."""

    common_mask = get_common_complete_case_train_mask(
        df=df,
        fold_role_column=fold_role_column,
        feature_columns=feature_columns,
    )

    train_complete = df.loc[common_mask, feature_columns]

    pearson = train_complete.corr(method="pearson")
    spearman = train_complete.corr(method="spearman")

    notna = train_complete.notna().astype("int64")
    pairwise_counts = notna.T @ notna

    return pearson, spearman, pairwise_counts
def classify_pair_redundancy(
    pearson_value: float,
    spearman_value: float,
) -> str:
    """Classify one feature pair using the locked Stage B thresholds."""

    abs_pearson = abs(pearson_value)
    abs_spearman = abs(spearman_value)

    if (
        abs_pearson >= HARD_REDUNDANCY_PEARSON_ABS
        and abs_spearman >= HARD_REDUNDANCY_SPEARMAN_ABS
    ):
        return "HARD_REDUNDANCY"

    if (
        abs_pearson >= REVIEW_CORRELATION_ABS
        or abs_spearman >= REVIEW_CORRELATION_ABS
    ):
        return "REVIEW"

    return "DISTINCT"
def build_pairwise_redundancy_table(
    pearson: pd.DataFrame,
    spearman: pd.DataFrame,
    pairwise_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Build one row per unique feature pair."""

    rows: list[dict[str, object]] = []
    features = list(pearson.columns)

    for i, feature_a in enumerate(features):
        for feature_b in features[i + 1 :]:
            pearson_value = float(pearson.loc[feature_a, feature_b])
            spearman_value = float(spearman.loc[feature_a, feature_b])
            sample_count = int(pairwise_counts.loc[feature_a, feature_b])

            rows.append(
                {
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "pearson": pearson_value,
                    "spearman": spearman_value,
                    "sample_count": sample_count,
                    "classification": classify_pair_redundancy(
                        pearson_value=pearson_value,
                        spearman_value=spearman_value,
                    ),
                }
            )

    return pd.DataFrame(rows)
def analyze_one_fold(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Run the locked Stage B redundancy analysis for one TRAIN fold."""

    assert_stage_b_contract_locked()

    pearson, spearman, pairwise_counts = compute_fold_correlations(
        df=df,
        fold_role_column=fold_role_column,
        feature_columns=feature_columns,
    )

    result = build_pairwise_redundancy_table(
        pearson=pearson,
        spearman=spearman,
        pairwise_counts=pairwise_counts,
    )

    result.insert(0, "fold_role_column", fold_role_column)
    result.insert(1, "policy_version", POLICY_VERSION)

    return result
def analyze_all_folds(
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Run Stage B redundancy analysis across all locked TRAIN folds."""

    fold_results = []

    for fold_role_column in FOLD_ROLE_COLUMNS:
        fold_result = analyze_one_fold(
            df=df,
            fold_role_column=fold_role_column,
            feature_columns=feature_columns,
        )
        fold_results.append(fold_result)

    return pd.concat(fold_results, ignore_index=True)
def build_fold_coverage_summary(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Summarize TRAIN coverage before redundancy statistics."""

    train_mask = get_train_mask(df, fold_role_column)

    train_rows = int(train_mask.sum())

    complete_case_mask = get_common_complete_case_train_mask(
        df=df,
        fold_role_column=fold_role_column,
        feature_columns=feature_columns,
    )

    complete_rows = int(complete_case_mask.sum())
    incomplete_rows = train_rows - complete_rows

    coverage_pct = (
        complete_rows / train_rows * 100.0
        if train_rows > 0
        else 0.0
    )

    return pd.DataFrame(
        [
            {
                "fold_role_column": fold_role_column,
                "train_rows": train_rows,
                "complete_feature_rows": complete_rows,
                "incomplete_feature_rows": incomplete_rows,
                "complete_coverage_pct": coverage_pct,
            }
        ]
    )
def build_all_fold_coverage_summary(
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Build coverage summary across all locked TRAIN folds."""

    summaries = []

    for fold_role_column in FOLD_ROLE_COLUMNS:
        summary = build_fold_coverage_summary(
            df=df,
            fold_role_column=fold_role_column,
            feature_columns=feature_columns,
        )
        summaries.append(summary)

    return pd.concat(summaries, ignore_index=True)
def build_feature_missingness_summary(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Summarize missingness for each feature inside one TRAIN fold."""

    train_mask = get_train_mask(df, fold_role_column)
    train_df = df.loc[train_mask, feature_columns]

    rows = []

    for feature in feature_columns:
        total_rows = len(train_df)
        missing_rows = int(train_df[feature].isna().sum())
        available_rows = total_rows - missing_rows

        availability_pct = (
            available_rows / total_rows * 100.0
            if total_rows > 0
            else 0.0
        )

        rows.append(
            {
                "fold_role_column": fold_role_column,
                "feature": feature,
                "train_rows": total_rows,
                "available_rows": available_rows,
                "missing_rows": missing_rows,
                "availability_pct": availability_pct,
            }
        )

    return pd.DataFrame(rows)
def build_all_fold_feature_missingness_summary(
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Build feature-level missingness summary across all TRAIN folds."""

    summaries = []

    for fold_role_column in FOLD_ROLE_COLUMNS:
        summary = build_feature_missingness_summary(
            df=df,
            fold_role_column=fold_role_column,
            feature_columns=feature_columns,
        )
        summaries.append(summary)

    return pd.concat(summaries, ignore_index=True)
def check_momentum_60m_identity(
    df: pd.DataFrame,
    momentum_column: str = "momentum_log_60m",
    return_columns: tuple[str, str, str, str] = (
        "log_return_lag_0",
        "log_return_lag_1",
        "log_return_lag_2",
        "log_return_lag_3",
    ),
) -> pd.DataFrame:
    """Check the known identity: 60m momentum equals four 15m log returns."""

    required_columns = (momentum_column, *return_columns)

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise KeyError(f"Missing semantic-check columns: {missing_columns}")

    valid_mask = df[list(required_columns)].notna().all(axis=1)
    valid_df = df.loc[valid_mask, list(required_columns)]

    reconstructed = valid_df[list(return_columns)].sum(axis=1)
    absolute_error = (valid_df[momentum_column] - reconstructed).abs()

    max_absolute_error = (
        float(absolute_error.max())
        if not absolute_error.empty
        else float("nan")
    )

    identity_pass = (
        max_absolute_error <= 1e-12
        if not absolute_error.empty
        else False
    )

    return pd.DataFrame(
        [
            {
                "semantic_check": "MOMENTUM_60M_EQUALS_RETURN_LAGS_0_TO_3",
                "rows_checked": len(valid_df),
                "max_absolute_error": max_absolute_error,
                "identity_pass": identity_pass,
            }
        ]
    )
def check_weekday_dummy_identity(
    df: pd.DataFrame,
    weekday_columns: tuple[str, ...] = (
        "weekday_monday",
        "weekday_tuesday",
        "weekday_wednesday",
        "weekday_thursday",
        "weekday_friday",
    ),
) -> pd.DataFrame:
    """Check that weekday dummy variables sum to one."""

    missing_columns = [
        column for column in weekday_columns if column not in df.columns
    ]

    if missing_columns:
        raise KeyError(f"Missing semantic-check columns: {missing_columns}")

    valid_mask = df[list(weekday_columns)].notna().all(axis=1)
    valid_df = df.loc[valid_mask, list(weekday_columns)]

    row_sums = valid_df.sum(axis=1)
    absolute_error = (row_sums - 1.0).abs()

    max_absolute_error = (
        float(absolute_error.max())
        if not absolute_error.empty
        else float("nan")
    )

    identity_pass = (
        max_absolute_error <= 1e-12
        if not absolute_error.empty
        else False
    )

    return pd.DataFrame(
        [
            {
                "semantic_check": "WEEKDAY_DUMMIES_SUM_TO_ONE",
                "rows_checked": len(valid_df),
                "max_absolute_error": max_absolute_error,
                "identity_pass": identity_pass,
            }
        ]
    )

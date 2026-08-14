"""Stage B feature redundancy and stability analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mes_quant.redundancy.contract import (
    COMMON_COHORT_POLICY,
    FOLD_ROLE_COLUMNS,
    HARD_REDUNDANCY_PEARSON_ABS,
    HARD_REDUNDANCY_SPEARMAN_ABS,
    POLICY_VERSION,
    REVIEW_CORRELATION_ABS,
    SEMANTIC_IDENTITY_TOLERANCE,
)



# STEP_14A_SEMANTIC_RUNTIME_V1_1

_REQUIRED_SEMANTIC_FIELDS = {
    "check_id",
    "check_type",
    "features",
    "dependent_features",
    "determining_features",
    "scope",
    "decision_effect",
    "implementation_key",
    "dependency_group",
    "required_drop_count",
    "protect_determining_features",
    "rationale",
}


_SUPPORTED_PHASE_A_DECISION_EFFECTS = {
    "DROP_DEPENDENT_KEEP_DETERMINING",
    "RETAIN_DERIVED_NONLINEAR_REPRESENTATION",
    "DROP_ONE_DETERMINISTIC_REFERENCE_KEEP_FOUR_DIMENSIONS",
    "RETAIN_BOTH_PAIRED_REPRESENTATION",
    "PHASE_C_HARD_MAY_DROP_ONLY_UNPROTECTED_MEMBER",
}


_CANONICAL_METADATA_FIELDS = (
    "feature",
    "lookback_mode",
    "lookback_bars",
    "lookback_minutes",
    "lookback_start_rule",
)


def _expected_check_type_shape(
    check_type: str,
) -> tuple[bool, bool, int | None]:
    """Return the locked Section 13.2 structural shape."""

    if check_type == "EXACT_LINEAR_DERIVED_IDENTITY":
        return True, True, 1

    if check_type == "EXACT_NONLINEAR_DERIVED_REPRESENTATION":
        return True, True, 0

    if check_type == "EXACT_AFFINE_DERIVED_IDENTITY":
        return True, True, 1

    if check_type == "EXACT_AFFINE_DEPENDENCY":
        return False, False, 1

    if check_type == "PAIRED_NONLINEAR_REPRESENTATION":
        return False, False, 0

    if check_type == "EMPIRICAL_NEAR_IDENTITY":
        return False, False, None

    raise ValueError(
        f"Unknown Stage B semantic check_type: {check_type!r}"
    )


def validate_semantic_registry(
    registry: dict[str, object],
) -> None:
    """Validate the Stage B semantic registry fail-closed."""

    if not isinstance(registry, dict):
        raise TypeError(
            "Semantic registry must be a dict."
        )

    required_top_level = {
        "policy_version",
        "registry_status",
        "source_contract",
        "semantic_checks",
    }

    missing_top = required_top_level.difference(registry)

    if missing_top:
        raise ValueError(
            "Semantic registry missing top-level fields: "
            f"{sorted(missing_top)}"
        )

    checks = registry["semantic_checks"]

    if not isinstance(checks, list):
        raise TypeError(
            "semantic_checks must be a list."
        )

    if not checks:
        raise ValueError(
            "semantic_checks must not be empty."
        )

    seen_check_ids: set[str] = set()
    seen_implementation_keys: set[str] = set()
    seen_dependency_groups: set[str] = set()

    for entry in checks:
        if not isinstance(entry, dict):
            raise TypeError(
                "Every semantic check must be a dict."
            )

        missing = (
            _REQUIRED_SEMANTIC_FIELDS
            .difference(entry)
        )

        if missing:
            raise ValueError(
                "Semantic check missing required fields: "
                f"{sorted(missing)}"
            )

        check_id = entry["check_id"]
        check_type = entry["check_type"]
        features = entry["features"]
        dependent = entry["dependent_features"]
        determining = entry["determining_features"]
        scope = entry["scope"]
        decision_effect = entry[
            "decision_effect"
        ]
        implementation_key = entry["implementation_key"]
        dependency_group = entry["dependency_group"]
        drop_count = entry["required_drop_count"]
        protect = entry[
            "protect_determining_features"
        ]

        for name, value in [
            ("check_id", check_id),
            ("check_type", check_type),
            (
                "implementation_key",
                implementation_key,
            ),
            (
                "decision_effect",
                decision_effect,
            ),
            (
                "dependency_group",
                dependency_group,
            ),
        ]:
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"{name} must be a non-empty string."
                )

        if (
            decision_effect
            not in _SUPPORTED_PHASE_A_DECISION_EFFECTS
        ):
            raise ValueError(
                "Unsupported Phase A decision_effect: "
                f"{decision_effect!r}"
            )

        if "|" in dependency_group:
            raise ValueError(
                "dependency_group may not contain "
                "reserved delimiter '|'."
            )

        if not isinstance(features, list) or not features:
            raise ValueError(
                "features must be a non-empty list."
            )

        if not isinstance(dependent, list):
            raise TypeError(
                "dependent_features must be a list."
            )

        if not isinstance(determining, list):
            raise TypeError(
                "determining_features must be a list."
            )

        if not isinstance(protect, bool):
            raise TypeError(
                "protect_determining_features "
                "must be bool."
            )

        if scope != "TRAIN_PER_FOLD":
            raise ValueError(
                f"Unsupported semantic scope: {scope!r}"
            )

        if not set(dependent).issubset(features):
            raise ValueError(
                "dependent_features must be "
                "contained in features."
            )

        if not set(determining).issubset(features):
            raise ValueError(
                "determining_features must be "
                "contained in features."
            )

        if len(features) != len(set(features)):
            raise ValueError(
                "Duplicate feature inside semantic "
                f"check {check_id!r}."
            )

        (
            dependent_required,
            determining_required,
            expected_drop_count,
        ) = _expected_check_type_shape(
            str(check_type)
        )

        if bool(dependent) != dependent_required:
            raise ValueError(
                f"{check_id}: dependent_features "
                f"violates {check_type} "
                "structural invariant."
            )

        if (
            bool(determining)
            != determining_required
        ):
            raise ValueError(
                f"{check_id}: determining_features "
                f"violates {check_type} "
                "structural invariant."
            )

        if drop_count != expected_drop_count:
            raise ValueError(
                f"{check_id}: required_drop_count="
                f"{drop_count!r} does not match "
                f"{check_type} requirement "
                f"{expected_drop_count!r}."
            )

        if check_id in seen_check_ids:
            raise ValueError(
                f"Duplicate check_id: {check_id!r}"
            )

        if (
            implementation_key
            in seen_implementation_keys
        ):
            raise ValueError(
                "Duplicate implementation_key: "
                f"{implementation_key!r}"
            )

        if (
            dependency_group
            in seen_dependency_groups
        ):
            raise ValueError(
                "Duplicate dependency_group: "
                f"{dependency_group!r}"
            )

        seen_check_ids.add(check_id)
        seen_implementation_keys.add(
            implementation_key
        )
        seen_dependency_groups.add(
            dependency_group
        )


def derive_protected_features(
    registry: dict[str, object],
) -> tuple[str, ...]:
    """Derive BASE protection mechanically from registry order."""

    validate_semantic_registry(registry)

    protected: list[str] = []

    for entry in registry["semantic_checks"]:
        if not entry[
            "protect_determining_features"
        ]:
            continue

        for feature in entry[
            "determining_features"
        ]:
            if feature not in protected:
                protected.append(feature)

    return tuple(protected)


def _semantic_available_frame(
    df: pd.DataFrame,
    entry: dict[str, object],
) -> pd.DataFrame:
    """Return rows where all required check features are present."""

    features = list(entry["features"])

    missing_columns = [
        feature
        for feature in features
        if feature not in df.columns
    ]

    if missing_columns:
        raise KeyError(
            "Missing semantic-check columns: "
            f"{missing_columns}"
        )

    return df.loc[
        df[features].notna().all(axis=1),
        features,
    ]


def _floating_identity_result(
    *,
    entry: dict[str, object],
    actual: pd.Series,
    reconstructed: pd.Series,
    tolerance: float,
) -> dict[str, object]:
    """Build diagnostics for one floating-point identity."""

    if len(actual) != len(reconstructed):
        raise RuntimeError(
            "Identity vectors have different lengths."
        )

    error = (
        actual.astype("float64")
        - reconstructed.astype("float64")
    ).abs()

    finite = np.isfinite(
        error.to_numpy(dtype="float64")
    )

    non_finite_count = int(
        (~finite).sum()
    )

    if len(error) == 0:
        max_error = float("nan")
        fail_count = 0
        identity_pass = False

    else:
        finite_error = error.iloc[
            np.flatnonzero(finite)
        ]

        max_error = (
            float(finite_error.max())
            if not finite_error.empty
            else float("nan")
        )

        fail_count = int(
            (finite_error > tolerance).sum()
        )

        identity_pass = (
            non_finite_count == 0
            and fail_count == 0
        )

    return {
        "check_id": entry["check_id"],
        "check_type": entry["check_type"],
        "rows_checked": int(len(error)),
        "max_absolute_error": max_error,
        "tolerance": float(tolerance),
        "fail_count": fail_count,
        "non_finite_count": non_finite_count,
        "identity_pass": bool(identity_pass),
    }


def check_momentum_60m_telescoping_identity(
    df: pd.DataFrame,
    entry: dict[str, object],
    *,
    tolerance: float = SEMANTIC_IDENTITY_TOLERANCE,
) -> dict[str, object]:
    """Verify momentum from its registry-defined return basis."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    dependent = list(
        entry["dependent_features"]
    )

    determining = list(
        entry["determining_features"]
    )

    if (
        len(dependent) != 1
        or len(determining) != 4
    ):
        raise ValueError(
            "Momentum identity requires one "
            "dependent and four determining features."
        )

    reconstructed = frame[
        determining
    ].sum(axis=1)

    return _floating_identity_result(
        entry=entry,
        actual=frame[dependent[0]],
        reconstructed=reconstructed,
        tolerance=tolerance,
    )


def check_realized_vol_60m_representation(
    df: pd.DataFrame,
    entry: dict[str, object],
    *,
    tolerance: float = SEMANTIC_IDENTITY_TOLERANCE,
) -> dict[str, object]:
    """Verify the canonical four-return volatility representation."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    dependent = list(
        entry["dependent_features"]
    )

    determining = list(
        entry["determining_features"]
    )

    if (
        len(dependent) != 1
        or len(determining) != 4
    ):
        raise ValueError(
            "Realized-vol identity requires one "
            "dependent and four determining features."
        )

    squared = (
        frame[determining]
        .astype("float64")
        .pow(2)
        .sum(axis=1)
    )

    reconstructed = np.sqrt(
        squared
    )

    return _floating_identity_result(
        entry=entry,
        actual=frame[dependent[0]],
        reconstructed=reconstructed,
        tolerance=tolerance,
    )


def check_horizon_safe_close_affine_identity(
    df: pd.DataFrame,
    entry: dict[str, object],
) -> dict[str, object]:
    """Verify the exact affine safe-close relationship."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    dependent = list(
        entry["dependent_features"]
    )

    determining = list(
        entry["determining_features"]
    )

    if (
        len(dependent) != 1
        or len(determining) != 2
    ):
        raise ValueError(
            "Safe-close identity requires one "
            "dependent and two determining features."
        )

    minutes_since_open = determining[0]
    early_close = determining[1]

    reconstructed = (
        330
        - frame[minutes_since_open]
        - 180 * frame[early_close]
    )

    actual = frame[dependent[0]]

    exact_equal = actual.eq(
        reconstructed
    )

    error = (
        actual.astype("float64")
        - reconstructed.astype("float64")
    ).abs()

    non_finite_count = int(
        (
            ~np.isfinite(
                error.to_numpy(
                    dtype="float64"
                )
            )
        ).sum()
    )

    return {
        "check_id": entry["check_id"],
        "check_type": entry["check_type"],
        "rows_checked": int(len(frame)),
        "max_absolute_error": (
            float(error.max())
            if not error.empty
            else float("nan")
        ),
        "fail_count": int(
            (~exact_equal).sum()
        ),
        "non_finite_count": non_finite_count,
        "identity_pass": bool(
            len(frame) > 0
            and non_finite_count == 0
            and exact_equal.all()
        ),
        "validation_mode": "EXACT_FUNCTIONAL",
    }


def check_weekday_one_hot_affine_dependency(
    df: pd.DataFrame,
    entry: dict[str, object],
) -> dict[str, object]:
    """Verify registry weekday dummies sum exactly to one."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    features = list(
        entry["features"]
    )

    row_sum = frame[
        features
    ].sum(axis=1)

    exact_equal = row_sum.eq(1)

    error = (
        row_sum - 1
    ).abs()

    return {
        "check_id": entry["check_id"],
        "check_type": entry["check_type"],
        "rows_checked": int(len(frame)),
        "max_absolute_error": (
            float(error.max())
            if not error.empty
            else float("nan")
        ),
        "fail_count": int(
            (~exact_equal).sum()
        ),
        "identity_pass": bool(
            len(frame) > 0
            and exact_equal.all()
        ),
        "validation_mode": "EXACT_CATEGORICAL",
    }


def check_decision_slot_unit_circle(
    df: pd.DataFrame,
    entry: dict[str, object],
    *,
    tolerance: float = SEMANTIC_IDENTITY_TOLERANCE,
) -> dict[str, object]:
    """Verify the paired sine/cosine unit-circle identity."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    features = list(
        entry["features"]
    )

    if len(features) != 2:
        raise ValueError(
            "Decision-slot representation "
            "requires exactly two features."
        )

    reconstructed = (
        frame[features[0]]
        .astype("float64")
        .pow(2)
        + frame[features[1]]
        .astype("float64")
        .pow(2)
    )

    actual = pd.Series(
        1.0,
        index=frame.index,
        dtype="float64",
    )

    return _floating_identity_result(
        entry=entry,
        actual=actual,
        reconstructed=reconstructed,
        tolerance=tolerance,
    )


def check_lag0_bar_body_empirical_pair(
    df: pd.DataFrame,
    entry: dict[str, object],
) -> dict[str, object]:
    """Measure the empirical near-identity pair without deciding."""

    frame = _semantic_available_frame(
        df,
        entry,
    )

    features = list(
        entry["features"]
    )

    if len(features) != 2:
        raise ValueError(
            "Empirical near-identity check "
            "requires exactly two features."
        )

    if len(frame) < 2:
        pearson = float("nan")
        spearman = float("nan")

    else:
        correlations = frame[
            features
        ]

        pearson = float(
            correlations.corr(
                method="pearson"
            ).iloc[0, 1]
        )

        spearman = float(
            correlations.corr(
                method="spearman"
            ).iloc[0, 1]
        )

    return {
        "check_id": entry["check_id"],
        "check_type": entry["check_type"],
        "rows_checked": int(len(frame)),
        "pearson": pearson,
        "spearman": spearman,
        "automatic_decision": None,
        "classification": (
            "EMPIRICAL_EVIDENCE_ONLY"
        ),
    }




# STEP_14B_ZERO_VARIANCE_AND_SVD_RUNTIME_V1_1


def compute_zero_variance_diagnostics(
    df: pd.DataFrame,
    fold_role_column: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Report zero variance separately on full TRAIN and the
    common complete-case TRAIN cohort.

    Only full-TRAIN zero variance may later authorize an
    automatic ZERO_VARIANCE_NO_INFORMATION drop.
    """

    if not feature_columns:
        raise ValueError(
            "feature_columns must not be empty."
        )

    if len(feature_columns) != len(set(feature_columns)):
        raise ValueError(
            "feature_columns contains duplicates."
        )

    missing_columns = [
        feature
        for feature in feature_columns
        if feature not in df.columns
    ]

    if missing_columns:
        raise KeyError(
            f"Missing candidate feature columns: {missing_columns}"
        )

    train_mask = get_train_mask(
        df,
        fold_role_column,
    )

    common_mask = get_common_complete_case_train_mask(
        df=df,
        fold_role_column=fold_role_column,
        feature_columns=feature_columns,
    )

    full_train = df.loc[
        train_mask,
        feature_columns,
    ]

    common_train = df.loc[
        common_mask,
        feature_columns,
    ]

    rows: list[dict[str, object]] = []

    for feature in feature_columns:
        full_values = full_train[
            feature
        ].dropna()

        common_values = common_train[
            feature
        ]

        full_available_rows = int(
            len(full_values)
        )

        common_rows = int(
            len(common_values)
        )

        full_unique_count = int(
            full_values.nunique(
                dropna=True
            )
        )

        common_unique_count = int(
            common_values.nunique(
                dropna=True
            )
        )

        full_zero_variance = bool(
            full_available_rows > 0
            and full_unique_count <= 1
        )

        common_zero_variance = bool(
            common_rows > 0
            and common_unique_count <= 1
        )

        rows.append(
            {
                "fold_role_column": fold_role_column,
                "feature": feature,
                "full_train_rows": int(
                    train_mask.sum()
                ),
                "full_train_available_rows": (
                    full_available_rows
                ),
                "full_train_unique_count": (
                    full_unique_count
                ),
                "full_train_zero_variance": (
                    full_zero_variance
                ),
                "common_cohort_rows": (
                    common_rows
                ),
                "common_cohort_unique_count": (
                    common_unique_count
                ),
                "common_cohort_zero_variance": (
                    common_zero_variance
                ),
            }
        )

    return pd.DataFrame(rows)


def resolve_zero_variance_base_decision(
    *,
    full_train_zero_by_fold: dict[str, bool],
    common_cohort_zero_by_fold: dict[str, bool],
    semantic_basis_protected: bool,
) -> dict[str, object]:
    """
    Resolve the locked automatic zero-variance decision.

    Common-cohort degeneracy is diagnostic only.
    """

    required_folds = tuple(
        FOLD_ROLE_COLUMNS
    )

    for name, mapping in [
        (
            "full_train_zero_by_fold",
            full_train_zero_by_fold,
        ),
        (
            "common_cohort_zero_by_fold",
            common_cohort_zero_by_fold,
        ),
    ]:
        if set(mapping) != set(required_folds):
            raise ValueError(
                f"{name} must contain exactly "
                f"{list(required_folds)}."
            )

        for fold, value in mapping.items():
            if not isinstance(value, bool):
                raise TypeError(
                    f"{name}[{fold!r}] must be bool."
                )

    if not isinstance(
        semantic_basis_protected,
        bool,
    ):
        raise TypeError(
            "semantic_basis_protected must be bool."
        )

    full_train_zero_all_folds = all(
        full_train_zero_by_fold[
            fold
        ]
        for fold in required_folds
    )

    common_zero_all_folds = all(
        common_cohort_zero_by_fold[
            fold
        ]
        for fold in required_folds
    )

    if semantic_basis_protected:
        return {
            "base_decision": "KEEP",
            "decision_basis": (
                "SEMANTIC_BASIS_PROTECTED"
            ),
            "full_train_zero_all_folds": (
                full_train_zero_all_folds
            ),
            "common_cohort_zero_all_folds": (
                common_zero_all_folds
            ),
        }

    if full_train_zero_all_folds:
        return {
            "base_decision": "DROP_REDUNDANT",
            "decision_basis": (
                "ZERO_VARIANCE_NO_INFORMATION"
            ),
            "full_train_zero_all_folds": True,
            "common_cohort_zero_all_folds": (
                common_zero_all_folds
            ),
        }

    return {
        "base_decision": "KEEP",
        "decision_basis": (
            "FULL_TRAIN_ZERO_VARIANCE_NOT_MET"
        ),
        "full_train_zero_all_folds": False,
        "common_cohort_zero_all_folds": (
            common_zero_all_folds
        ),
    }


def build_standardized_matrix(
    *,
    frame: pd.DataFrame,
    feature_columns: list[str],
) -> np.ndarray:
    """
    Build the locked float64, ddof=0 standardized matrix
    used for exact-rank SVD diagnostics.
    """

    if not feature_columns:
        raise ValueError(
            "feature_columns must not be empty."
        )

    if len(feature_columns) != len(set(feature_columns)):
        raise ValueError(
            "feature_columns contains duplicates."
        )

    missing_columns = [
        feature
        for feature in feature_columns
        if feature not in frame.columns
    ]

    if missing_columns:
        raise KeyError(
            f"Missing standardized-matrix columns: {missing_columns}"
        )

    if len(frame) == 0:
        raise ValueError(
            "Cannot standardize an empty frame."
        )

    matrix = frame[
        feature_columns
    ].to_numpy(
        dtype=np.float64,
        copy=True,
    )

    if matrix.ndim != 2:
        raise RuntimeError(
            "Standardization input is not 2-D."
        )

    if not np.isfinite(matrix).all():
        raise ValueError(
            "Standardization requires finite complete-case values."
        )

    means = matrix.mean(
        axis=0,
        dtype=np.float64,
    )

    standard_deviations = matrix.std(
        axis=0,
        ddof=0,
        dtype=np.float64,
    )

    if not np.isfinite(
        standard_deviations
    ).all():
        raise ValueError(
            "Non-finite standard deviation."
        )

    if np.any(
        standard_deviations == 0.0
    ):
        raise ValueError(
            "Zero-variance columns must be resolved "
            "before standardized SVD."
        )

    standardized = (
        matrix - means
    ) / standard_deviations

    standardized = np.asarray(
        standardized,
        dtype=np.float64,
    )

    if not np.isfinite(
        standardized
    ).all():
        raise ValueError(
            "Standardized matrix contains non-finite values."
        )

    return standardized


def compute_svd_diagnostics(
    standardized_matrix: np.ndarray,
) -> dict[str, object]:
    """
    Compute one deterministic float64 singular-value spectrum
    and derive rank from the locked numerical tolerance.
    """

    matrix = np.asarray(
        standardized_matrix,
        dtype=np.float64,
    )

    if matrix.ndim != 2:
        raise ValueError(
            "SVD matrix must be two-dimensional."
        )

    n_rows, n_columns = matrix.shape

    if n_rows == 0 or n_columns == 0:
        raise ValueError(
            "SVD matrix must be non-empty."
        )

    if not np.isfinite(matrix).all():
        raise ValueError(
            "SVD matrix contains non-finite values."
        )

    singular_values = np.linalg.svd(
        matrix,
        full_matrices=False,
        compute_uv=False,
    ).astype(
        np.float64,
        copy=False,
    )

    if singular_values.size == 0:
        raise RuntimeError(
            "SVD returned no singular values."
        )

    sigma_max = float(
        singular_values[0]
    )

    rank_tolerance = float(
        max(n_rows, n_columns)
        * np.finfo(np.float64).eps
        * sigma_max
    )

    rank = int(
        np.count_nonzero(
            singular_values
            > rank_tolerance
        )
    )

    deficiency = int(
        n_columns - rank
    )

    return {
        "matrix_shape": (
            int(n_rows),
            int(n_columns),
        ),
        "singular_values": [
            float(value)
            for value in singular_values
        ],
        "sigma_max": sigma_max,
        "rank_tolerance": (
            rank_tolerance
        ),
        "rank": rank,
        "deficiency": deficiency,
        "dtype": "float64",
        "standardization_ddof": 0,
    }




def _select_phase_a_semantic_rank_basis(
    *,
    frame,
    feature_columns,
    semantic_reference_order,
):
    """Build numerical evidence for one registry-authorized Phase-A basis.

    This helper has no generic Phase-B decision authority.  Its excluded
    members become semantic drops only in ``_resolve_phase_a_relationship``
    after the locked registry selects the explicit Phase-A decision effect.
    """

    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(
        feature_columns,
        (list, tuple),
    ):
        raise TypeError(
            "feature_columns must be a list or tuple."
        )

    if not isinstance(
        semantic_reference_order,
        (list, tuple),
    ):
        raise TypeError(
            "semantic_reference_order must be a list or tuple."
        )

    candidates = list(
        feature_columns
    )
    ordered_candidates = list(
        semantic_reference_order
    )

    if not candidates:
        raise ValueError(
            "feature_columns must not be empty."
        )

    if (
        len(candidates)
        != len(set(candidates))
    ):
        raise ValueError(
            "feature_columns contains duplicates."
        )

    if (
        len(ordered_candidates)
        != len(set(ordered_candidates))
    ):
        raise ValueError(
            "semantic_reference_order contains duplicates."
        )

    if (
        len(ordered_candidates)
        != len(candidates)
        or set(ordered_candidates)
        != set(candidates)
    ):
        raise ValueError(
            "semantic_reference_order must contain each candidate exactly once."
        )

    original_matrix = build_standardized_matrix(
        frame=frame,
        feature_columns=candidates,
    )
    original_diagnostics = compute_svd_diagnostics(
        original_matrix
    )
    original_rank = int(
        original_diagnostics[
            "rank"
        ]
    )

    if original_rank <= 0:
        raise RuntimeError(
            "Phase-A semantic-basis candidate rank must be positive."
        )

    retained: list[str] = []
    redundant: list[str] = []
    current_rank = 0

    for candidate in ordered_candidates:
        proposed = [
            *retained,
            candidate,
        ]
        proposed_matrix = build_standardized_matrix(
            frame=frame,
            feature_columns=proposed,
        )
        proposed_diagnostics = compute_svd_diagnostics(
            proposed_matrix
        )
        proposed_rank = int(
            proposed_diagnostics[
                "rank"
            ]
        )

        if proposed_rank > current_rank:
            retained.append(
                candidate
            )
            current_rank = proposed_rank
        else:
            redundant.append(
                candidate
            )

    if not retained:
        raise RuntimeError(
            "Phase-A semantic-basis selection retained no features."
        )

    final_matrix = build_standardized_matrix(
        frame=frame,
        feature_columns=retained,
    )
    final_diagnostics = compute_svd_diagnostics(
        final_matrix
    )
    final_rank = int(
        final_diagnostics[
            "rank"
        ]
    )
    required_redundant_count = int(
        len(candidates)
        - original_rank
    )

    if len(redundant) != required_redundant_count:
        raise RuntimeError(
            "Phase-A semantic-basis excluded count does not equal k-r."
        )

    if len(retained) != original_rank:
        raise RuntimeError(
            "Phase-A semantic-basis retained count does not equal rank."
        )

    if final_rank != original_rank:
        raise RuntimeError(
            "Phase-A semantic-basis final rank does not preserve original rank."
        )

    return {
        "feature_count": len(
            candidates
        ),
        "original_rank": original_rank,
        "retained_features": tuple(
            retained
        ),
        "excluded_features": tuple(
            redundant
        ),
        "redundant_dimension_count": (
            required_redundant_count
        ),
        "final_retained_rank": final_rank,
        "original_svd_diagnostics": (
            original_diagnostics
        ),
        "final_svd_diagnostics": (
            final_diagnostics
        ),
    }


# ISSUE_9_GENERIC_RANK_DISCOVERY_CLASSIFIER_V1_2


def _validate_exact_fold_mapping(
    *,
    name: str,
    mapping: dict[str, object],
) -> tuple[str, ...]:
    """Require exactly the locked walk-forward fold keys."""

    if not isinstance(mapping, dict):
        raise TypeError(
            f"{name} must be a dict."
        )

    required_folds = tuple(
        FOLD_ROLE_COLUMNS
    )

    if set(mapping) != set(required_folds):
        raise ValueError(
            f"{name} must contain exactly "
            f"{list(required_folds)}."
        )

    return required_folds


def classify_generic_rank_discovery(
    *,
    component_features: list[str] | tuple[str, ...],
    discovery_status: str,
) -> dict[str, object]:
    """Classify frozen V1.2 generic-rank evidence without selecting a basis.

    This pure classifier is deliberately not wired into ``run_stage_b``.
    Issue #9 does not authorize full Phase-B production execution.  It only
    removes the former numerical-basis deletion authority and makes the
    already-frozen OPEN/HARD_FAIL boundary executable in isolation.

    ``component_dispositions`` is diagnostic.  An OPEN disposition may be
    represented as a feature-level OPEN state, while HARD_FAIL stops the run
    and must never be released as a feature-level BASE decision.
    """

    from . import contract as _contract

    if not isinstance(component_features, (list, tuple)):
        raise TypeError(
            "component_features must be a list or tuple."
        )

    members = tuple(component_features)
    if not members:
        raise ValueError(
            "component_features must not be empty."
        )

    if any(
        not isinstance(feature, str) or not feature
        for feature in members
    ):
        raise ValueError(
            "component_features must contain non-empty strings."
        )

    if len(members) != len(set(members)):
        raise ValueError(
            "component_features contains duplicates."
        )

    if not isinstance(discovery_status, str):
        raise TypeError(
            "discovery_status must be str."
        )

    if discovery_status in _contract.GENERIC_RANK_OPEN_STATUSES:
        decision_class = "OPEN"
        stage_c_release_allowed = False
    elif discovery_status in _contract.GENERIC_RANK_HARD_FAIL_STATUSES:
        decision_class = "HARD_FAIL"
        stage_c_release_allowed = False
    else:
        raise ValueError(
            "Unsupported generic rank discovery_status."
        )

    if _contract.GENERIC_RANK_DIRECT_DROP_AUTHORIZED is not False:
        raise RuntimeError(
            "Generic rank/SVD direct DROP authority must remain disabled."
        )

    if (
        _contract.GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN
        is not False
    ):
        raise RuntimeError(
            "Environment change must not resolve generic rank OPEN."
        )

    return {
        "discovery_status": discovery_status,
        "component_features": members,
        "decision_class": decision_class,
        "component_dispositions": {
            feature: decision_class
            for feature in members
        },
        "direct_drop_authorized": False,
        "dropped_features": (),
        "stage_c_release_allowed": stage_c_release_allowed,
        "environment_change_resolves_open": False,
    }


def classify_cohort_sensitivity(
    *,
    primary_hard_by_fold: dict[str, bool],
    pairwise_stats_by_fold: dict[
        str,
        dict[str, object],
    ],
) -> dict[str, object]:
    """
    Confirm or veto a primary empirical HARD result
    on pairwise-available TRAIN rows.

    Sensitivity evidence cannot independently create DROP.
    """

    required_folds = _validate_exact_fold_mapping(
        name="primary_hard_by_fold",
        mapping=primary_hard_by_fold,
    )

    _validate_exact_fold_mapping(
        name="pairwise_stats_by_fold",
        mapping=pairwise_stats_by_fold,
    )

    for fold in required_folds:
        if not isinstance(
            primary_hard_by_fold[fold],
            bool,
        ):
            raise TypeError(
                "primary_hard_by_fold"
                f"[{fold!r}] must be bool."
            )

    required_stat_fields = {
        "pairwise_available_rows",
        "feature_a_zero_variance",
        "feature_b_zero_variance",
        "pearson",
        "spearman",
    }

    pairwise_hard_by_fold: dict[
        str,
        bool,
    ] = {}

    sensitivity_available_by_fold: dict[
        str,
        bool,
    ] = {}

    for fold in required_folds:
        stats = pairwise_stats_by_fold[
            fold
        ]

        if not isinstance(stats, dict):
            raise TypeError(
                "Each pairwise sensitivity record "
                "must be a dict."
            )

        missing = (
            required_stat_fields
            .difference(stats)
        )

        if missing:
            raise ValueError(
                f"{fold}: missing pairwise fields "
                f"{sorted(missing)}"
            )

        rows = stats[
            "pairwise_available_rows"
        ]

        if (
            not isinstance(rows, int)
            or isinstance(rows, bool)
            or rows < 0
        ):
            raise ValueError(
                f"{fold}: pairwise_available_rows "
                "must be a non-negative int."
            )

        zero_a = stats[
            "feature_a_zero_variance"
        ]

        zero_b = stats[
            "feature_b_zero_variance"
        ]

        if not isinstance(zero_a, bool):
            raise TypeError(
                f"{fold}: feature_a_zero_variance "
                "must be bool."
            )

        if not isinstance(zero_b, bool):
            raise TypeError(
                f"{fold}: feature_b_zero_variance "
                "must be bool."
            )

        try:
            pearson = float(
                stats["pearson"]
            )
            spearman = float(
                stats["spearman"]
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{fold}: correlation values "
                "must be numeric."
            ) from exc

        available = bool(
            rows >= 2
            and not zero_a
            and not zero_b
            and np.isfinite(pearson)
            and np.isfinite(spearman)
        )

        sensitivity_available_by_fold[
            fold
        ] = available

        pairwise_hard_by_fold[
            fold
        ] = bool(
            available
            and abs(pearson)
            >= HARD_REDUNDANCY_PEARSON_ABS
            and abs(spearman)
            >= HARD_REDUNDANCY_SPEARMAN_ABS
        )

    primary_hard_all_folds = all(
        primary_hard_by_fold[
            fold
        ]
        for fold in required_folds
    )

    sensitivity_available_all_folds = all(
        sensitivity_available_by_fold[
            fold
        ]
        for fold in required_folds
    )

    pairwise_hard_all_folds = all(
        pairwise_hard_by_fold[
            fold
        ]
        for fold in required_folds
    )

    if not sensitivity_available_all_folds:
        return {
            "cohort_sensitivity_status": (
                "COHORT_SENSITIVITY_UNAVAILABLE"
            ),
            "primary_hard_all_folds": (
                primary_hard_all_folds
            ),
            "sensitivity_available_by_fold": (
                sensitivity_available_by_fold
            ),
            "pairwise_hard_by_fold": (
                pairwise_hard_by_fold
            ),
            "pairwise_hard_all_folds": False,
            "empirical_drop_eligible": False,
            "base_decision": "KEEP",
            "decision_basis": (
                "EMPIRICAL_DROP_VETOED_"
                "COHORT_SENSITIVITY_UNAVAILABLE"
            ),
        }

    if pairwise_hard_all_folds:
        sensitivity_status = (
            "COHORT_SENSITIVITY_SUPPORTED"
        )
    else:
        sensitivity_status = (
            "COHORT_SENSITIVITY_CONFLICT"
        )

    if (
        primary_hard_all_folds
        and pairwise_hard_all_folds
    ):
        return {
            "cohort_sensitivity_status": (
                sensitivity_status
            ),
            "primary_hard_all_folds": True,
            "sensitivity_available_by_fold": (
                sensitivity_available_by_fold
            ),
            "pairwise_hard_by_fold": (
                pairwise_hard_by_fold
            ),
            "pairwise_hard_all_folds": True,
            "empirical_drop_eligible": True,
            "base_decision": (
                "DROP_REDUNDANT"
            ),
            "decision_basis": (
                "EMPIRICAL_HARD_REDUNDANCY_"
                "CONFIRMED_PAIRWISE"
            ),
        }

    if (
        primary_hard_all_folds
        and not pairwise_hard_all_folds
    ):
        return {
            "cohort_sensitivity_status": (
                "COHORT_SENSITIVITY_CONFLICT"
            ),
            "primary_hard_all_folds": True,
            "sensitivity_available_by_fold": (
                sensitivity_available_by_fold
            ),
            "pairwise_hard_by_fold": (
                pairwise_hard_by_fold
            ),
            "pairwise_hard_all_folds": False,
            "empirical_drop_eligible": False,
            "base_decision": "KEEP",
            "decision_basis": (
                "EMPIRICAL_DROP_VETOED_COHORT_SENSITIVITY"
            ),
        }

    return {
        "cohort_sensitivity_status": (
            sensitivity_status
        ),
        "primary_hard_all_folds": False,
        "sensitivity_available_by_fold": (
            sensitivity_available_by_fold
        ),
        "pairwise_hard_by_fold": (
            pairwise_hard_by_fold
        ),
        "pairwise_hard_all_folds": (
            pairwise_hard_all_folds
        ),
        "empirical_drop_eligible": False,
        "base_decision": "KEEP",
        "decision_basis": (
            "PRIMARY_HARD_NOT_ALL_FOLDS"
        ),
    }


def resolve_phase_c_direct_substitute(
    *,
    candidate: str,
    retained_features: list[str],
    protected_features: set[str],
    pair_status_by_retained: dict[str, str],
) -> dict[str, object]:
    """
    Resolve one direct Phase-C substitute without
    transitive redundancy propagation.
    """

    if (
        not isinstance(candidate, str)
        or not candidate
    ):
        raise ValueError(
            "candidate must be a non-empty string."
        )

    if not isinstance(
        retained_features,
        list,
    ):
        raise TypeError(
            "retained_features must be a list."
        )

    if len(
        retained_features
    ) != len(
        set(retained_features)
    ):
        raise ValueError(
            "retained_features contains duplicates."
        )

    for feature in retained_features:
        if (
            not isinstance(feature, str)
            or not feature
        ):
            raise ValueError(
                "Every retained feature must "
                "be a non-empty string."
            )

    if not isinstance(
        protected_features,
        (set, frozenset),
    ):
        raise TypeError(
            "protected_features must be a set "
            "or frozenset."
        )

    if not isinstance(
        pair_status_by_retained,
        dict,
    ):
        raise TypeError(
            "pair_status_by_retained must be a dict."
        )

    if candidate in protected_features:
        return {
            "candidate": candidate,
            "base_decision": "KEEP",
            "decision_basis": (
                "SEMANTIC_BASIS_PROTECTED"
            ),
            "direct_substitute": None,
        }

    if candidate in retained_features:
        return {
            "candidate": candidate,
            "base_decision": "KEEP",
            "decision_basis": (
                "CANDIDATE_ALREADY_RETAINED"
            ),
            "direct_substitute": None,
        }

    allowed_statuses = {
        "COHORT_SENSITIVITY_SUPPORTED",
        "COHORT_SENSITIVITY_CONFLICT",
        "COHORT_SENSITIVITY_UNAVAILABLE",
        "DISTINCT",
        "REVIEW",
    }

    direct_substitutes: list[str] = []

    for retained in retained_features:
        status = pair_status_by_retained.get(
            retained
        )

        if status is None:
            continue

        if status not in allowed_statuses:
            raise ValueError(
                f"Unknown Phase-C pair status "
                f"for {retained!r}: {status!r}"
            )

        if (
            status
            == "COHORT_SENSITIVITY_SUPPORTED"
        ):
            direct_substitutes.append(
                retained
            )

    if len(direct_substitutes) == 1:
        substitute = direct_substitutes[0]

        return {
            "candidate": candidate,
            "base_decision": (
                "DROP_REDUNDANT"
            ),
            "decision_basis": (
                "EMPIRICAL_DIRECT_SUBSTITUTE"
            ),
            "direct_substitute": (
                substitute
            ),
        }

    if len(direct_substitutes) > 1:
        return {
            "candidate": candidate,
            "base_decision": "KEEP",
            "decision_basis": (
                "MULTIPLE_DIRECT_SUBSTITUTES_REVIEW"
            ),
            "direct_substitute": None,
        }

    return {
        "candidate": candidate,
        "base_decision": "KEEP",
        "decision_basis": (
            "NO_DIRECT_RETAINED_SUBSTITUTE"
        ),
        "direct_substitute": None,
    }




# STEP_14D_PHASE0_FIREWALL_RUNTIME_V1_1


def _validate_stage_b_control_binding(
    *,
    markdown_bytes: bytes,
    semantic_registry_bytes: bytes,
    expected_markdown_sha256: str,
    expected_registry_sha256: str,
    python_policy_version: str,
    python_policy_status: str,
    markdown_policy_version: str,
    markdown_policy_status: str,
    registry_policy_version: str,
    registry_status: str,
    registry_source_contract: str,
) -> dict[str, object]:
    """
    Fail closed unless the three Stage-B control layers
    agree and the locked files match their raw-byte pins.
    """

    import hashlib

    from . import contract as _contract

    if not isinstance(markdown_bytes, bytes):
        raise TypeError(
            "markdown_bytes must be raw bytes."
        )

    if not isinstance(
        semantic_registry_bytes,
        bytes,
    ):
        raise TypeError(
            "semantic_registry_bytes must be raw bytes."
        )

    markdown_sha256 = hashlib.sha256(
        markdown_bytes
    ).hexdigest()

    registry_sha256 = hashlib.sha256(
        semantic_registry_bytes
    ).hexdigest()

    for name, value in [
        (
            "expected_markdown_sha256",
            expected_markdown_sha256,
        ),
        (
            "expected_registry_sha256",
            expected_registry_sha256,
        ),
    ]:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(
                char not in "0123456789abcdef"
                for char in value.lower()
            )
        ):
            raise ValueError(
                f"{name} must be a 64-character SHA256."
            )

    if (
        markdown_sha256
        != expected_markdown_sha256.lower()
    ):
        raise RuntimeError(
            "Locked Markdown raw-byte SHA256 mismatch."
        )

    if (
        registry_sha256
        != expected_registry_sha256.lower()
    ):
        raise RuntimeError(
            "Locked semantic-registry raw-byte "
            "SHA256 mismatch."
        )

    expected_version = (
        _contract.POLICY_VERSION
    )

    versions = {
        "python": python_policy_version,
        "markdown": markdown_policy_version,
        "registry": registry_policy_version,
    }

    for layer, value in versions.items():
        if value != expected_version:
            raise RuntimeError(
                f"{layer} policy version mismatch: "
                f"{value!r}"
            )

    statuses = {
        "python": python_policy_status,
        "markdown": markdown_policy_status,
        "registry": registry_status,
    }

    for layer, value in statuses.items():
        if value != "LOCKED_EXECUTABLE":
            raise RuntimeError(
                f"{layer} policy status is not "
                f"LOCKED_EXECUTABLE: {value!r}"
            )

    if (
        registry_source_contract
        != _contract.MARKDOWN_CONTRACT_PATH
    ):
        raise RuntimeError(
            "Semantic registry source_contract "
            "does not bind to the locked Markdown path."
        )

    return {
        "markdown_sha256": markdown_sha256,
        "registry_sha256": registry_sha256,
        "policy_version": expected_version,
        "policy_status": "LOCKED_EXECUTABLE",
        "registry_source_contract": (
            registry_source_contract
        ),
        "control_binding_valid": True,
    }


def _validate_canonical_feature_registry(
    *,
    registry_rows: list[dict[str, object]],
    artifact_feature_order: list[str],
) -> dict[str, object]:
    """
    Enforce the canonical 29-feature membership, order,
    and V1.1 lookback metadata semantics.
    """

    if not isinstance(registry_rows, list):
        raise TypeError(
            "registry_rows must be a list."
        )

    if len(registry_rows) != 29:
        raise RuntimeError(
            "Canonical Stage B candidate registry "
            "must contain exactly 29 rows."
        )

    metadata_fields = _CANONICAL_METADATA_FIELDS
    required_fields = set(
        metadata_fields
    )

    canonical_order: list[str] = []
    canonical_metadata: list[tuple[object, ...]] = []

    for index, row in enumerate(
        registry_rows
    ):
        if not isinstance(row, dict):
            raise TypeError(
                "Every canonical registry row "
                "must be a dict."
            )

        missing = (
            required_fields
            .difference(row)
        )

        if missing:
            raise RuntimeError(
                f"Registry row {index} missing "
                f"required fields: {sorted(missing)}"
            )

        feature = row["feature"]

        if (
            not isinstance(feature, str)
            or not feature
        ):
            raise ValueError(
                f"Registry row {index} has "
                "invalid feature name."
            )

        canonical_order.append(
            feature
        )

        mode = row[
            "lookback_mode"
        ]

        bars = row[
            "lookback_bars"
        ]

        minutes = row[
            "lookback_minutes"
        ]

        start_rule = row[
            "lookback_start_rule"
        ]

        if mode not in {
            "FIXED",
            "SESSION_TO_DATE",
        }:
            raise RuntimeError(
                f"{feature}: unsupported "
                f"lookback_mode {mode!r}"
            )

        for name, value in [
            (
                "lookback_bars",
                bars,
            ),
            (
                "lookback_minutes",
                minutes,
            ),
        ]:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise RuntimeError(
                    f"{feature}: {name} must be "
                    "a non-negative integer."
                )

        if mode == "FIXED":
            if (
                (bars == 0)
                != (minutes == 0)
            ):
                raise RuntimeError(
                    f"{feature}: FIXED zero lookback "
                    "must be 0 bars / 0 minutes together."
                )

            # STEP_14G3B3B_CANONICAL_FIXED_LOOKBACK_COMPATIBILITY
            #
            # Canonical FIXED features may preserve their
            # descriptive lookback_start_rule metadata.
            #
            # Locked V1.1 does not require this field to be
            # null for FIXED features. Do not rewrite or erase
            # canonical metadata merely to satisfy validation.
            if start_rule is None:
                start_rule_missing = True

            elif isinstance(
                start_rule,
                str,
            ):
                start_rule_missing = (
                    not start_rule.strip()
                )

            else:
                try:
                    start_rule_missing = bool(
                        pd.isna(
                            start_rule
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    start_rule_missing = False

                if not start_rule_missing:
                    raise RuntimeError(
                        f"{feature}: FIXED "
                        "lookback_start_rule must be "
                        "a string or missing."
                    )

        else:
            if (
                bars <= 0
                or minutes <= 0
            ):
                raise RuntimeError(
                    f"{feature}: SESSION_TO_DATE "
                    "requires positive bars/minutes."
                )

            if (
                not isinstance(start_rule, str)
                or not start_rule.strip()
            ):
                raise RuntimeError(
                    f"{feature}: SESSION_TO_DATE "
                    "requires a non-empty start rule."
                )

        canonical_metadata.append(
            tuple(
                row[field]
                for field in metadata_fields
            )
        )

    if (
        len(canonical_order)
        != len(set(canonical_order))
    ):
        raise RuntimeError(
            "Canonical registry contains "
            "duplicate feature names."
        )

    if not isinstance(
        artifact_feature_order,
        list,
    ):
        raise TypeError(
            "artifact_feature_order must be a list."
        )

    if len(artifact_feature_order) != 29:
        raise RuntimeError(
            "Artifact must expose exactly "
            "29 candidate features."
        )

    if (
        len(artifact_feature_order)
        != len(set(artifact_feature_order))
    ):
        raise RuntimeError(
            "Artifact feature order contains duplicates."
        )

    if (
        artifact_feature_order
        != canonical_order
    ):
        raise RuntimeError(
            "Artifact candidate membership/order "
            "does not exactly match canonical registry."
        )

    return {
        "candidate_count": 29,
        "canonical_feature_order": tuple(
            canonical_order
        ),
        "canonical_feature_metadata": tuple(
            canonical_metadata
        ),
        "membership_exact": True,
        "order_exact": True,
        "lookback_metadata_valid": True,
    }


def _validate_forbidden_inputs(
    *,
    opened_fields: list[str],
    opened_cells: list[int],
    final_test_rows_opened: int,
) -> dict[str, object]:
    """
    Reject target/future/P&L/execution information,
    non-whitelisted cells, and any Final Test opening.
    """

    if not isinstance(
        opened_fields,
        list,
    ):
        raise TypeError(
            "opened_fields must be a list."
        )

    if not isinstance(
        opened_cells,
        list,
    ):
        raise TypeError(
            "opened_cells must be a list."
        )

    if (
        not isinstance(
            final_test_rows_opened,
            int,
        )
        or isinstance(
            final_test_rows_opened,
            bool,
        )
        or final_test_rows_opened < 0
    ):
        raise ValueError(
            "final_test_rows_opened must be "
            "a non-negative int."
        )

    forbidden_exact = {
        "label",
        "target",
        "future_price",
        "future_close",
        "future_close_60m",
        "future_return_60m",
        "forward_return_60m",
        "gross_pnl",
        "net_pnl",
        "execution_outcome",
    }

    forbidden_fields: list[str] = []

    for field in opened_fields:
        if (
            not isinstance(field, str)
            or not field
        ):
            raise ValueError(
                "Every opened field must be "
                "a non-empty string."
            )

        normalized = field.lower()

        forbidden = bool(
            normalized in forbidden_exact
            or normalized.startswith(
                "future_"
            )
            or normalized.startswith(
                "forward_"
            )
            or normalized.endswith(
                "_pnl"
            )
            or normalized.startswith(
                "label_"
            )
            or normalized.startswith(
                "target_"
            )
            or normalized.startswith(
                "execution_outcome"
            )
        )

        if forbidden:
            forbidden_fields.append(
                field
            )

    if forbidden_fields:
        raise RuntimeError(
            "Forbidden Stage B input fields opened: "
            f"{forbidden_fields}"
        )

    allowed_cells = {
        8,
        14,
    }

    for cell in opened_cells:
        if (
            not isinstance(cell, int)
            or isinstance(cell, bool)
        ):
            raise ValueError(
                "opened_cells must contain integers."
            )

        if cell not in allowed_cells:
            raise RuntimeError(
                f"Cell {cell} is outside the "
                "Stage B input whitelist."
            )

    if (
        len(opened_cells)
        != len(set(opened_cells))
    ):
        raise RuntimeError(
            "opened_cells contains duplicates."
        )

    if final_test_rows_opened != 0:
        raise RuntimeError(
            "Final Test must remain sealed: "
            f"{final_test_rows_opened} rows were opened."
        )

    return {
        "opened_fields": tuple(
            opened_fields
        ),
        "opened_cells": tuple(
            opened_cells
        ),
        "final_test_rows_opened": 0,
        "forbidden_input_gate_pass": True,
    }


def _validate_fold_coverage(
    *,
    fold_complete_rows: dict[str, int],
    fold_train_rows: dict[str, int],
    yearly_coverage: dict[int, float],
    yearly_review_acknowledged: bool,
) -> dict[str, object]:
    """
    Require exactly three locked TRAIN folds,
    >=90% complete-case coverage in every fold,
    and explicit acknowledgment for years below 90%.
    """

    required_folds = (
        _validate_exact_fold_mapping(
            name="fold_complete_rows",
            mapping=fold_complete_rows,
        )
    )

    _validate_exact_fold_mapping(
        name="fold_train_rows",
        mapping=fold_train_rows,
    )

    if not isinstance(
        yearly_review_acknowledged,
        bool,
    ):
        raise TypeError(
            "yearly_review_acknowledged "
            "must be bool."
        )

    coverage_by_fold: dict[
        str,
        float,
    ] = {}

    for fold in required_folds:
        complete_rows = (
            fold_complete_rows[
                fold
            ]
        )

        train_rows = (
            fold_train_rows[
                fold
            ]
        )

        for name, value in [
            (
                "complete_rows",
                complete_rows,
            ),
            (
                "train_rows",
                train_rows,
            ),
        ]:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{fold}: {name} must be "
                    "a non-negative int."
                )

        if train_rows <= 0:
            raise RuntimeError(
                f"{fold}: TRAIN row count "
                "must be positive."
            )

        if complete_rows > train_rows:
            raise RuntimeError(
                f"{fold}: complete rows exceed "
                "TRAIN rows."
            )

        coverage = (
            complete_rows
            / train_rows
        )

        coverage_by_fold[
            fold
        ] = float(
            coverage
        )

        if coverage < 0.90:
            raise RuntimeError(
                f"{fold}: full-29 complete-case "
                f"coverage {coverage:.6f} "
                "is below the 90% execution floor."
            )

    if (
        not isinstance(
            yearly_coverage,
            dict,
        )
        or not yearly_coverage
    ):
        raise ValueError(
            "yearly_coverage must be "
            "a non-empty dict."
        )

    normalized_yearly: dict[
        int,
        float,
    ] = {}

    review_years: list[int] = []

    for year, coverage in (
        yearly_coverage.items()
    ):
        if (
            not isinstance(year, int)
            or isinstance(year, bool)
        ):
            raise ValueError(
                "yearly_coverage keys "
                "must be integer years."
            )

        if (
            not isinstance(
                coverage,
                (int, float),
            )
            or isinstance(
                coverage,
                bool,
            )
            or not np.isfinite(
                float(coverage)
            )
        ):
            raise ValueError(
                f"{year}: invalid yearly coverage."
            )

        coverage_float = float(
            coverage
        )

        if not (
            0.0
            <= coverage_float
            <= 1.0
        ):
            raise ValueError(
                f"{year}: yearly coverage "
                "must be between 0 and 1."
            )

        normalized_yearly[
            year
        ] = coverage_float

        if coverage_float < 0.90:
            review_years.append(
                year
            )

    review_required = bool(
        review_years
    )

    if (
        review_required
        and not yearly_review_acknowledged
    ):
        raise RuntimeError(
            "YEARLY_CONCENTRATION_REVIEW_REQUIRED: "
            f"years below 90% = {sorted(review_years)}"
        )

    return {
        "fold_coverage_gate_pass": True,
        "fold_coverage": (
            coverage_by_fold
        ),
        "fold_coverage_floor": 0.90,
        "yearly_coverage": (
            normalized_yearly
        ),
        "years_below_90": tuple(
            sorted(review_years)
        ),
        "YEARLY_CONCENTRATION_REVIEW_REQUIRED": (
            review_required
        ),
        "YEARLY_CONCENTRATION_REVIEW_STATUS": (
            "ACKNOWLEDGED"
            if review_required
            else "NOT_REQUIRED"
        ),
    }


def _canonical_orient_pair(
    *,
    feature_x: str,
    feature_y: str,
    canonical_order: list[str],
) -> tuple[str, str]:
    """
    Orient a feature pair deterministically by
    canonical registry order.
    """

    if not isinstance(
        canonical_order,
        list,
    ):
        raise TypeError(
            "canonical_order must be a list."
        )

    if (
        len(canonical_order)
        != len(set(canonical_order))
    ):
        raise RuntimeError(
            "canonical_order contains duplicates."
        )

    index = {
        feature: position
        for position, feature
        in enumerate(
            canonical_order
        )
    }

    for feature in [
        feature_x,
        feature_y,
    ]:
        if feature not in index:
            raise RuntimeError(
                f"Feature {feature!r} is not "
                "in canonical registry order."
            )

    if feature_x == feature_y:
        raise ValueError(
            "A redundancy pair requires "
            "two distinct features."
        )

    if (
        index[feature_x]
        < index[feature_y]
    ):
        return (
            feature_x,
            feature_y,
        )

    return (
        feature_y,
        feature_x,
    )




def _serialize_relationship_ids(
    *,
    identifiers: object,
    ordered_universe: list[str],
) -> str:
    """
    Serialize one relationship-class ID collection
    deterministically using governing universe order.
    """

    if not isinstance(
        ordered_universe,
        list,
    ):
        raise TypeError(
            "ordered_universe must be a list."
        )

    if (
        len(ordered_universe)
        != len(set(ordered_universe))
    ):
        raise ValueError(
            "ordered_universe contains duplicates."
        )

    for identifier in ordered_universe:
        if (
            not isinstance(identifier, str)
            or not identifier
            or "|" in identifier
        ):
            raise ValueError(
                "ordered_universe contains "
                "an invalid identifier."
            )

    if isinstance(
        identifiers,
        str,
    ):
        raise TypeError(
            "identifiers must be a collection, "
            "not one serialized string."
        )

    if not isinstance(
        identifiers,
        (list, tuple, set, frozenset),
    ):
        raise TypeError(
            "identifiers must be a list, tuple, "
            "set, or frozenset."
        )

    values = list(
        identifiers
    )

    for identifier in values:
        if (
            not isinstance(identifier, str)
            or not identifier
            or "|" in identifier
        ):
            raise ValueError(
                "Relationship identifiers must "
                "be non-empty strings without '|'."
            )

    if len(values) != len(set(values)):
        raise ValueError(
            "Duplicate relationship identifier."
        )

    universe_set = set(
        ordered_universe
    )

    unknown = [
        identifier
        for identifier in values
        if identifier not in universe_set
    ]

    if unknown:
        raise ValueError(
            "Unknown relationship identifiers: "
            f"{unknown}"
        )

    selected = set(
        values
    )

    ordered = [
        identifier
        for identifier in ordered_universe
        if identifier in selected
    ]

    return "|".join(
        ordered
    )


def _validate_serialized_multi_id_field(
    *,
    field_name: str,
    value: object,
) -> None:
    """
    Validate syntax of one already-serialized multi-ID field.

    Class membership/order is validated upstream when the
    relationship-specific ordered universe is available.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string."
        )

    if value == "":
        return

    if (
        value.startswith("|")
        or value.endswith("|")
        or "||" in value
    ):
        raise ValueError(
            f"{field_name} has invalid delimiter syntax."
        )

    identifiers = value.split(
        "|"
    )

    if any(
        not identifier
        for identifier in identifiers
    ):
        raise ValueError(
            f"{field_name} contains an empty ID."
        )

    if len(
        identifiers
    ) != len(
        set(identifiers)
    ):
        raise ValueError(
            f"{field_name} contains duplicate IDs."
        )


def _validate_feature_decision_registry_row(
    *,
    row: dict[str, object],
) -> dict[str, object]:
    """
    Validate the feature-level decision-registry schema.

    required_drop_count is deliberately not a feature-level
    scalar in V1.2.
    """

    if not isinstance(row, dict):
        raise TypeError(
            "row must be a dict."
        )

    required_fields = (
        "feature",
        "base_decision",
        "decision_basis",
        "semantic_dependency_groups",
        "exact_set_dependency_groups",
        "empirical_pair_ids",
        "semantic_basis_protected",
        "chosen_representative_or_basis",
        "direct_substitute",
        "group_cohort_rank_status",
        "cohort_sensitivity_status",
        "linear_overlay_decision",
        "tree_overlay_decision",
        "reason",
    )

    missing = [
        field
        for field in required_fields
        if field not in row
    ]

    if missing:
        raise ValueError(
            "Decision-registry row missing fields: "
            f"{missing}"
        )

    if "required_drop_count" in row:
        raise ValueError(
            "required_drop_count is relationship-level "
            "evidence and may not be collapsed into a "
            "feature-level scalar."
        )

    feature = row[
        "feature"
    ]

    if (
        not isinstance(feature, str)
        or not feature
    ):
        raise ValueError(
            "feature must be a non-empty string."
        )

    allowed_base_decisions = {
        "KEEP",
        "DROP_REDUNDANT",
        "OPEN",
    }

    if (
        row[
            "base_decision"
        ]
        not in allowed_base_decisions
    ):
        raise ValueError(
            "Invalid BASE decision: "
            f"{row['base_decision']!r}"
        )

    decision_basis = row[
        "decision_basis"
    ]

    if (
        not isinstance(decision_basis, str)
        or not decision_basis
    ):
        raise ValueError(
            "decision_basis must be "
            "a non-empty string."
        )

    for field_name in [
        "semantic_dependency_groups",
        "exact_set_dependency_groups",
        "empirical_pair_ids",
    ]:
        _validate_serialized_multi_id_field(
            field_name=field_name,
            value=row[field_name],
        )

    if not isinstance(
        row[
            "semantic_basis_protected"
        ],
        bool,
    ):
        raise TypeError(
            "semantic_basis_protected must be bool."
        )

    for field_name in [
        "chosen_representative_or_basis",
        "direct_substitute",
        "group_cohort_rank_status",
        "cohort_sensitivity_status",
    ]:
        value = row[
            field_name
        ]

        if (
            value is not None
            and (
                not isinstance(value, str)
                or not value
            )
        ):
            raise ValueError(
                f"{field_name} must be None "
                "or a non-empty string."
            )

    if row["exact_set_dependency_groups"]:
        from . import contract as _contract

        if row["base_decision"] != "OPEN":
            raise RuntimeError(
                "Generic Phase-B exact-set relationships may release only "
                "OPEN feature states; direct KEEP/DROP is forbidden."
            )

        for field_name in (
            "chosen_representative_or_basis",
            "direct_substitute",
        ):
            if row[field_name] is not None:
                raise RuntimeError(
                    "Generic Phase-B exact-set relationships may not select "
                    f"{field_name}."
                )

        if (
            row["group_cohort_rank_status"]
            not in _contract.GENERIC_RANK_OPEN_STATUSES
        ):
            raise RuntimeError(
                "Generic Phase-B OPEN row must record an authorized OPEN "
                "discovery status."
            )

    for field_name in [
        "linear_overlay_decision",
        "tree_overlay_decision",
    ]:
        value = row[
            field_name
        ]

        if (
            not isinstance(value, str)
            or not value
        ):
            raise ValueError(
                f"{field_name} must be "
                "a non-empty string."
            )

    reason = row[
        "reason"
    ]

    if (
        not isinstance(reason, str)
        or not reason
    ):
        raise ValueError(
            "reason must be a non-empty string."
        )

    return {
        "decision_registry_row_valid": True,
        "feature": feature,
        "base_decision": row[
            "base_decision"
        ],
        "required_fields": required_fields,
    }


def _validate_stage_c_readiness(
    *,
    decision_rows: list[dict[str, object]],
    yearly_review_required: bool,
    yearly_review_status: str,
    phase_c_rank_loss_review_required: bool,
    phase_c_rank_loss_review_status: str,
) -> dict[str, object]:
    """
    Enforce the target-blind gate before Stage C may
    open labels.
    """

    if not isinstance(
        decision_rows,
        list,
    ):
        raise TypeError(
            "decision_rows must be a list."
        )

    if not decision_rows:
        raise ValueError(
            "decision_rows must not be empty."
        )

    allowed_base_decisions = {
        "KEEP",
        "DROP_REDUNDANT",
        "OPEN",
    }

    open_features: list[str] = []

    for index, row in enumerate(
        decision_rows
    ):
        if not isinstance(row, dict):
            raise TypeError(
                f"decision_rows[{index}] "
                "must be a dict."
            )

        if "base_decision" not in row:
            raise ValueError(
                f"decision_rows[{index}] "
                "missing base_decision."
            )

        decision = row[
            "base_decision"
        ]

        if decision not in (
            allowed_base_decisions
        ):
            raise ValueError(
                f"decision_rows[{index}] "
                f"has invalid BASE state {decision!r}."
            )

        if (
            row.get("exact_set_dependency_groups")
            and decision != "OPEN"
        ):
            raise RuntimeError(
                f"decision_rows[{index}] encodes a forbidden generic "
                "Phase-B direct KEEP/DROP state."
            )

        if decision == "OPEN":
            feature = row.get(
                "feature",
                f"row_{index}",
            )

            open_features.append(
                str(feature)
            )

    open_count = len(
        open_features
    )

    if open_count != 0:
        raise RuntimeError(
            "Stage C blocked: "
            f"OPEN count = {open_count}; "
            f"features = {open_features}"
        )

    for name, value in [
        (
            "yearly_review_required",
            yearly_review_required,
        ),
        (
            "phase_c_rank_loss_review_required",
            phase_c_rank_loss_review_required,
        ),
    ]:
        if not isinstance(value, bool):
            raise TypeError(
                f"{name} must be bool."
            )

    def _validate_ack(
        *,
        required: bool,
        status: str,
        gate_name: str,
    ) -> None:
        if not isinstance(status, str):
            raise TypeError(
                f"{gate_name} status must be a string."
            )

        if required:
            if status != "ACKNOWLEDGED":
                raise RuntimeError(
                    f"{gate_name} requires "
                    "target-blind ACKNOWLEDGED status."
                )

            return

        if status not in {
            "NOT_REQUIRED",
            "ACKNOWLEDGED",
        }:
            raise RuntimeError(
                f"{gate_name} is not required but "
                f"has invalid status {status!r}."
            )

    _validate_ack(
        required=yearly_review_required,
        status=yearly_review_status,
        gate_name=(
            "YEARLY_CONCENTRATION_REVIEW"
        ),
    )

    _validate_ack(
        required=phase_c_rank_loss_review_required,
        status=phase_c_rank_loss_review_status,
        gate_name=(
            "PHASE_C_RANK_LOSS_REVIEW"
        ),
    )

    return {
        "open_count": 0,
        "open_features": tuple(),
        "yearly_review_required": (
            yearly_review_required
        ),
        "yearly_review_status": (
            yearly_review_status
        ),
        "phase_c_rank_loss_review_required": (
            phase_c_rank_loss_review_required
        ),
        "phase_c_rank_loss_review_status": (
            phase_c_rank_loss_review_status
        ),
        "stage_c_ready": True,
    }




# STEP_14F1_PRIMARY_EMPIRICAL_RUNTIME_V1_1


def _compute_empirical_pair_stats(
    *,
    frame: pd.DataFrame,
    feature_a: str,
    feature_b: str,
) -> dict[str, object]:
    """
    Compute Pearson/Spearman evidence on the pair-specific
    complete-case cohort only.

    This helper computes evidence only. It does not authorize
    an empirical DROP.
    """

    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "frame must be a pandas DataFrame."
        )

    for name, feature in [
        ("feature_a", feature_a),
        ("feature_b", feature_b),
    ]:
        if (
            not isinstance(feature, str)
            or not feature
        ):
            raise ValueError(
                f"{name} must be a non-empty string."
            )

        if feature not in frame.columns:
            raise KeyError(
                f"{feature!r} is absent from frame."
            )

    if feature_a == feature_b:
        raise ValueError(
            "Empirical pair requires two distinct features."
        )

    pair = frame[
        [
            feature_a,
            feature_b,
        ]
    ].dropna(
        how="any"
    )

    pairwise_available_rows = int(
        len(pair)
    )

    if pairwise_available_rows > 0:
        try:
            matrix = pair.to_numpy(
                dtype=np.float64,
                copy=True,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Empirical pair features must be numeric."
            ) from exc

        if not np.isfinite(
            matrix
        ).all():
            raise ValueError(
                "Empirical pair contains non-finite values."
            )

    feature_a_zero_variance = bool(
        pairwise_available_rows > 0
        and pair[
            feature_a
        ].nunique(
            dropna=True
        )
        <= 1
    )

    feature_b_zero_variance = bool(
        pairwise_available_rows > 0
        and pair[
            feature_b
        ].nunique(
            dropna=True
        )
        <= 1
    )

    if (
        pairwise_available_rows < 2
        or feature_a_zero_variance
        or feature_b_zero_variance
    ):
        pearson = float("nan")
        spearman = float("nan")

    else:
        pearson = float(
            pair[
                [
                    feature_a,
                    feature_b,
                ]
            ]
            .corr(
                method="pearson"
            )
            .iloc[0, 1]
        )

        spearman = float(
            pair[
                [
                    feature_a,
                    feature_b,
                ]
            ]
            .corr(
                method="spearman"
            )
            .iloc[0, 1]
        )

    return {
        "feature_a": feature_a,
        "feature_b": feature_b,
        "pairwise_available_rows": (
            pairwise_available_rows
        ),
        "feature_a_zero_variance": (
            feature_a_zero_variance
        ),
        "feature_b_zero_variance": (
            feature_b_zero_variance
        ),
        "pearson": pearson,
        "spearman": spearman,
    }


def _classify_primary_empirical_pair(
    *,
    stats_by_fold: dict[
        str,
        dict[str, object],
    ],
) -> dict[str, object]:
    """
    Classify primary empirical redundancy across the
    three locked TRAIN folds.

    HARD:
      abs(Pearson) >= HARD threshold AND
      abs(Spearman) >= HARD threshold
      in every TRAIN fold.

    REVIEW:
      HARD is not satisfied across all folds, but at least
      one fold has either metric at or above REVIEW threshold.

    DISTINCT:
      neither condition above.

    Primary HARD remains evidence only and cannot create
    DROP without the locked pairwise sensitivity check.
    """

    required_folds = (
        _validate_exact_fold_mapping(
            name="stats_by_fold",
            mapping=stats_by_fold,
        )
    )

    required_fields = {
        "pairwise_available_rows",
        "feature_a_zero_variance",
        "feature_b_zero_variance",
        "pearson",
        "spearman",
    }

    primary_available_by_fold: dict[
        str,
        bool,
    ] = {}

    primary_hard_by_fold: dict[
        str,
        bool,
    ] = {}

    primary_review_by_fold: dict[
        str,
        bool,
    ] = {}

    for fold in required_folds:
        stats = stats_by_fold[
            fold
        ]

        if not isinstance(
            stats,
            dict,
        ):
            raise TypeError(
                f"{fold}: stats must be a dict."
            )

        missing = (
            required_fields
            .difference(stats)
        )

        if missing:
            raise ValueError(
                f"{fold}: missing empirical fields "
                f"{sorted(missing)}"
            )

        rows = stats[
            "pairwise_available_rows"
        ]

        if (
            not isinstance(rows, int)
            or isinstance(rows, bool)
            or rows < 0
        ):
            raise ValueError(
                f"{fold}: pairwise_available_rows "
                "must be a non-negative int."
            )

        zero_a = stats[
            "feature_a_zero_variance"
        ]

        zero_b = stats[
            "feature_b_zero_variance"
        ]

        if not isinstance(
            zero_a,
            bool,
        ):
            raise TypeError(
                f"{fold}: feature_a_zero_variance "
                "must be bool."
            )

        if not isinstance(
            zero_b,
            bool,
        ):
            raise TypeError(
                f"{fold}: feature_b_zero_variance "
                "must be bool."
            )

        try:
            pearson = float(
                stats[
                    "pearson"
                ]
            )

            spearman = float(
                stats[
                    "spearman"
                ]
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{fold}: empirical correlations "
                "must be numeric."
            ) from exc

        available = bool(
            rows >= 2
            and not zero_a
            and not zero_b
            and np.isfinite(
                pearson
            )
            and np.isfinite(
                spearman
            )
        )

        primary_available_by_fold[
            fold
        ] = available

        hard = bool(
            available
            and abs(
                pearson
            )
            >= HARD_REDUNDANCY_PEARSON_ABS
            and abs(
                spearman
            )
            >= HARD_REDUNDANCY_SPEARMAN_ABS
        )

        review = bool(
            available
            and (
                abs(
                    pearson
                )
                >= REVIEW_CORRELATION_ABS
                or abs(
                    spearman
                )
                >= REVIEW_CORRELATION_ABS
            )
        )

        primary_hard_by_fold[
            fold
        ] = hard

        primary_review_by_fold[
            fold
        ] = review

    primary_hard_all_folds = all(
        primary_hard_by_fold[
            fold
        ]
        for fold in required_folds
    )

    primary_review_any_fold = any(
        primary_review_by_fold[
            fold
        ]
        for fold in required_folds
    )

    if primary_hard_all_folds:
        classification = "HARD"
        decision_basis = (
            "PRIMARY_HARD_REQUIRES_PAIRWISE_SENSITIVITY"
        )

    elif primary_review_any_fold:
        classification = "REVIEW"
        decision_basis = (
            "PRIMARY_REVIEW_TARGET_BLIND_KEEP"
        )

    else:
        classification = "DISTINCT"
        decision_basis = (
            "PRIMARY_DISTINCT"
        )

    return {
        "primary_classification": (
            classification
        ),
        "primary_available_by_fold": (
            primary_available_by_fold
        ),
        "primary_hard_by_fold": (
            primary_hard_by_fold
        ),
        "primary_review_by_fold": (
            primary_review_by_fold
        ),
        "primary_hard_all_folds": (
            primary_hard_all_folds
        ),
        "primary_review_any_fold": (
            primary_review_any_fold
        ),
        # Primary evidence alone never authorizes DROP.
        "empirical_drop_eligible": False,
        "base_decision": "KEEP",
        "decision_basis": (
            decision_basis
        ),
    }




# STEP_14F2_SPEARMAN_COMPLETE_LINKAGE_CLUSTERING_RUNTIME_V1_1


def _spearman_distance_matrix(
    *,
    spearman_correlation: pd.DataFrame,
    canonical_order: list[str],
) -> pd.DataFrame:
    """
    Convert a canonical Spearman correlation matrix into
    the locked clustering distance:

        distance = 1 - abs(Spearman rho)

    Clustering is descriptive/review evidence only.
    """

    if not isinstance(
        spearman_correlation,
        pd.DataFrame,
    ):
        raise TypeError(
            "spearman_correlation must be a pandas DataFrame."
        )

    if not isinstance(
        canonical_order,
        list,
    ):
        raise TypeError(
            "canonical_order must be a list."
        )

    if not canonical_order:
        raise ValueError(
            "canonical_order must not be empty."
        )

    if len(
        canonical_order
    ) != len(
        set(canonical_order)
    ):
        raise ValueError(
            "canonical_order contains duplicates."
        )

    for feature in canonical_order:
        if (
            not isinstance(feature, str)
            or not feature
        ):
            raise ValueError(
                "canonical_order contains an invalid feature."
            )

    if (
        list(spearman_correlation.index)
        != canonical_order
    ):
        raise RuntimeError(
            "Spearman correlation index does not exactly "
            "match canonical feature order."
        )

    if (
        list(spearman_correlation.columns)
        != canonical_order
    ):
        raise RuntimeError(
            "Spearman correlation columns do not exactly "
            "match canonical feature order."
        )

    if (
        spearman_correlation.shape[0]
        != spearman_correlation.shape[1]
    ):
        raise RuntimeError(
            "Spearman correlation matrix must be square."
        )

    try:
        matrix = spearman_correlation.to_numpy(
            dtype=np.float64,
            copy=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Spearman correlation matrix must be numeric."
        ) from exc

    if not np.isfinite(
        matrix
    ).all():
        raise RuntimeError(
            "Spearman correlation matrix contains "
            "non-finite values."
        )

    if np.any(
        matrix < -1.0
    ) or np.any(
        matrix > 1.0
    ):
        raise RuntimeError(
            "Spearman correlation values must lie "
            "between -1 and 1."
        )

    if not np.allclose(
        matrix,
        matrix.T,
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Spearman correlation matrix must be symmetric."
        )

    if not np.allclose(
        np.diag(matrix),
        np.ones(
            len(canonical_order),
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Spearman correlation diagonal must equal 1."
        )

    distance = (
        1.0
        - np.abs(matrix)
    )

    # Remove harmless floating-point residue on the diagonal.
    np.fill_diagonal(
        distance,
        0.0,
    )

    return pd.DataFrame(
        distance,
        index=canonical_order,
        columns=canonical_order,
        dtype="float64",
    )


def _complete_linkage_clusters(
    *,
    distance_matrix: pd.DataFrame,
    canonical_order: list[str],
    cut_distance: float = 0.10,
) -> tuple[tuple[str, ...], ...]:
    """
    Deterministic agglomerative complete-linkage clustering.

    The distance between two clusters is the maximum
    pairwise distance between their members.

    A merge is permitted only when that complete-linkage
    distance is <= the locked cut distance.

    This prevents single-linkage-style transitive chaining.
    """

    if not isinstance(
        distance_matrix,
        pd.DataFrame,
    ):
        raise TypeError(
            "distance_matrix must be a pandas DataFrame."
        )

    if not isinstance(
        canonical_order,
        list,
    ):
        raise TypeError(
            "canonical_order must be a list."
        )

    if not canonical_order:
        raise ValueError(
            "canonical_order must not be empty."
        )

    if len(
        canonical_order
    ) != len(
        set(canonical_order)
    ):
        raise ValueError(
            "canonical_order contains duplicates."
        )

    if (
        list(distance_matrix.index)
        != canonical_order
        or list(distance_matrix.columns)
        != canonical_order
    ):
        raise RuntimeError(
            "Distance matrix must exactly follow "
            "canonical feature order."
        )

    try:
        matrix = distance_matrix.to_numpy(
            dtype=np.float64,
            copy=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Distance matrix must be numeric."
        ) from exc

    if not np.isfinite(
        matrix
    ).all():
        raise RuntimeError(
            "Distance matrix contains non-finite values."
        )

    if np.any(
        matrix < 0.0
    ):
        raise RuntimeError(
            "Distance matrix contains negative values."
        )

    if not np.allclose(
        matrix,
        matrix.T,
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Distance matrix must be symmetric."
        )

    if not np.allclose(
        np.diag(matrix),
        np.zeros(
            len(canonical_order),
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError(
            "Distance matrix diagonal must equal zero."
        )

    if (
        not isinstance(
            cut_distance,
            (int, float),
        )
        or isinstance(
            cut_distance,
            bool,
        )
    ):
        raise TypeError(
            "cut_distance must be numeric."
        )

    cut = float(
        cut_distance
    )

    if (
        not np.isfinite(cut)
        or cut < 0.0
    ):
        raise ValueError(
            "cut_distance must be finite and non-negative."
        )

    canonical_index = {
        feature: position
        for position, feature
        in enumerate(
            canonical_order
        )
    }

    clusters: list[
        tuple[str, ...]
    ] = [
        (feature,)
        for feature in canonical_order
    ]

    def cluster_key(
        cluster: tuple[str, ...],
    ) -> tuple[int, ...]:
        return tuple(
            canonical_index[
                feature
            ]
            for feature in cluster
        )

    def complete_distance(
        cluster_a: tuple[str, ...],
        cluster_b: tuple[str, ...],
    ) -> float:
        values = [
            float(
                distance_matrix.loc[
                    feature_a,
                    feature_b,
                ]
            )
            for feature_a in cluster_a
            for feature_b in cluster_b
        ]

        return float(
            max(values)
        )

    while True:
        merge_candidates: list[
            tuple[
                float,
                tuple[int, ...],
                tuple[int, ...],
                int,
                int,
            ]
        ] = []

        for i in range(
            len(clusters)
        ):
            for j in range(
                i + 1,
                len(clusters),
            ):
                cluster_a = clusters[
                    i
                ]

                cluster_b = clusters[
                    j
                ]

                distance = (
                    complete_distance(
                        cluster_a,
                        cluster_b,
                    )
                )

                # Locked cut boundary is inclusive.
                if distance <= cut:
                    merge_candidates.append(
                        (
                            distance,
                            cluster_key(
                                cluster_a
                            ),
                            cluster_key(
                                cluster_b
                            ),
                            i,
                            j,
                        )
                    )

        if not merge_candidates:
            break

        merge_candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            )
        )

        _, _, _, i, j = (
            merge_candidates[0]
        )

        merged = tuple(
            sorted(
                (
                    *clusters[i],
                    *clusters[j],
                ),
                key=lambda feature: (
                    canonical_index[
                        feature
                    ]
                ),
            )
        )

        next_clusters = [
            cluster
            for position, cluster
            in enumerate(
                clusters
            )
            if position not in {
                i,
                j,
            }
        ]

        next_clusters.append(
            merged
        )

        clusters = sorted(
            next_clusters,
            key=cluster_key,
        )

    return tuple(
        clusters
    )


def _classify_cluster_review_evidence(
    *,
    cluster_members: tuple[str, ...],
) -> dict[str, object]:
    """
    Convert one cluster into descriptive REVIEW evidence.

    Clustering never authorizes automatic DROP and never
    overrides semantic, exact-set, or HARD empirical rules.
    """

    if not isinstance(
        cluster_members,
        tuple,
    ):
        raise TypeError(
            "cluster_members must be a tuple."
        )

    if not cluster_members:
        raise ValueError(
            "cluster_members must not be empty."
        )

    if len(
        cluster_members
    ) != len(
        set(cluster_members)
    ):
        raise ValueError(
            "cluster_members contains duplicates."
        )

    for feature in cluster_members:
        if (
            not isinstance(feature, str)
            or not feature
        ):
            raise ValueError(
                "cluster_members contains an invalid feature."
            )

    review_required = bool(
        len(cluster_members) > 1
    )

    classification = (
        "CLUSTER_REVIEW"
        if review_required
        else "CLUSTER_SINGLETON"
    )

    return {
        "cluster_members": (
            cluster_members
        ),
        "cluster_size": int(
            len(cluster_members)
        ),
        "review_required": (
            review_required
        ),
        "classification": (
            classification
        ),
        # Cluster evidence is descriptive only.
        "drop_allowed": False,
        "empirical_drop_eligible": False,
        "base_decision": "KEEP",
        "decision_basis": (
            "CLUSTER_REVIEW_ONLY"
            if review_required
            else "CLUSTER_SINGLETON"
        ),
    }




# STEP_14G1_DETERMINISTIC_PRODUCTION_OUTPUT_RUNTIME_V1_1


def _required_stage_b_output_filenames(
) -> tuple[str, ...]:
    """
    Return the seven locked Stage B V1.1 artifact names
    in deterministic contract order.
    """

    return (
        "stage_b_feature_coverage_v1.csv",
        "stage_b_semantic_dependency_ledger_v1.csv",
        "stage_b_fold_correlations_v1.parquet",
        "stage_b_set_level_diagnostics_v1.csv",
        "stage_b_redundancy_clusters_v1.csv",
        "stage_b_feature_decision_registry_v1.csv",
        "stage_b_redundancy_audit.json",
    )


def _sha256_bytes(
    raw_bytes: bytes,
) -> str:
    """
    Hash exact serialized bytes without newline,
    encoding, or text normalization.
    """

    import hashlib

    if not isinstance(
        raw_bytes,
        bytes,
    ):
        raise TypeError(
            "raw_bytes must be bytes."
        )

    return hashlib.sha256(
        raw_bytes
    ).hexdigest()


def _serialize_stage_b_csv_bytes(
    *,
    frame: pd.DataFrame,
    field_order: list[str],
    row_sort_by: list[str],
) -> bytes:
    """
    Serialize one Stage B CSV artifact deterministically.

    Locked implementation profile:
      - UTF-8
      - LF line endings
      - explicit field order
      - explicit deterministic row sort
      - no pandas index column
    """

    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(
        field_order,
        list,
    ):
        raise TypeError(
            "field_order must be a list."
        )

    if not field_order:
        raise ValueError(
            "field_order must not be empty."
        )

    if len(
        field_order
    ) != len(
        set(field_order)
    ):
        raise ValueError(
            "field_order contains duplicates."
        )

    if not isinstance(
        row_sort_by,
        list,
    ):
        raise TypeError(
            "row_sort_by must be a list."
        )

    if not row_sort_by:
        raise ValueError(
            "row_sort_by must explicitly define "
            "deterministic row ordering."
        )

    if len(
        row_sort_by
    ) != len(
        set(row_sort_by)
    ):
        raise ValueError(
            "row_sort_by contains duplicates."
        )

    for field in (
        field_order
        + row_sort_by
    ):
        if (
            not isinstance(field, str)
            or not field
        ):
            raise ValueError(
                "CSV field names must be "
                "non-empty strings."
            )

    actual_columns = list(
        frame.columns
    )

    if set(
        actual_columns
    ) != set(
        field_order
    ):
        raise RuntimeError(
            "CSV frame schema does not exactly match "
            "the declared field_order."
        )

    unknown_sort_fields = [
        field
        for field in row_sort_by
        if field not in field_order
    ]

    if unknown_sort_fields:
        raise RuntimeError(
            "row_sort_by contains fields outside "
            f"the schema: {unknown_sort_fields}"
        )

    ordered = (
        frame.loc[
            :,
            field_order,
        ]
        .sort_values(
            by=row_sort_by,
            kind="mergesort",
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    text = ordered.to_csv(
        index=False,
        columns=field_order,
        lineterminator="\n",
    )

    if "\r\n" in text:
        raise RuntimeError(
            "CSV serialization produced CRLF."
        )

    if not text.endswith(
        "\n"
    ):
        raise RuntimeError(
            "CSV serialization must terminate "
            "with exactly an LF profile."
        )

    return text.encode(
        "utf-8"
    )


def _serialize_stage_b_json_bytes(
    *,
    payload: object,
) -> bytes:
    """
    Serialize canonical Stage B JSON bytes.

    Dictionary keys are sorted recursively by json.dumps.
    Lists retain their already-governed upstream order.
    Non-standard NaN/Infinity JSON values are forbidden.
    """

    import json

    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            allow_nan=False,
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Payload is not valid canonical Stage B JSON."
        ) from exc

    text += "\n"

    if "\r\n" in text:
        raise RuntimeError(
            "JSON serialization produced CRLF."
        )

    return text.encode(
        "utf-8"
    )


def _validate_stage_b_output_bundle(
    *,
    artifacts: dict[str, bytes],
) -> dict[str, object]:
    """
    Require exactly the seven locked Stage B outputs.

    This validation concerns the serialized in-memory bundle.
    It does not write production files.
    """

    if not isinstance(
        artifacts,
        dict,
    ):
        raise TypeError(
            "artifacts must be a dict."
        )

    required = (
        _required_stage_b_output_filenames()
    )

    actual = set(
        artifacts
    )

    required_set = set(
        required
    )

    missing = [
        name
        for name in required
        if name not in actual
    ]

    extra = sorted(
        actual.difference(
            required_set
        )
    )

    if missing or extra:
        raise RuntimeError(
            "Stage B output bundle mismatch. "
            f"missing={missing}, extra={extra}"
        )

    for name in required:
        raw = artifacts[
            name
        ]

        if not isinstance(
            raw,
            bytes,
        ):
            raise TypeError(
                f"{name}: serialized artifact "
                "must be raw bytes."
            )

    return {
        "output_bundle_valid": True,
        "artifact_count": int(
            len(required)
        ),
        "artifact_order": (
            required
        ),
    }


def _build_stage_b_output_hash_manifest(
    *,
    artifacts: dict[str, bytes],
    policy_version: str,
    control_hashes: dict[str, str],
    upstream_hashes: dict[str, str],
) -> dict[str, object]:
    """
    Build the external non-recursive output-hash manifest.

    The seven serialized Stage B artifacts are hashed as
    exact raw bytes, including the audit JSON artifact.

    This manifest is returned by production orchestration;
    it is not one of the seven self-referential artifacts.
    """

    from . import contract as _contract

    _validate_stage_b_output_bundle(
        artifacts=artifacts,
    )

    if policy_version != _contract.POLICY_VERSION:
        raise RuntimeError(
            "Output manifest policy version mismatch."
        )

    def _validated_hash_mapping(
        *,
        name: str,
        mapping: dict[str, str],
    ) -> dict[str, str]:
        if (
            not isinstance(
                mapping,
                dict,
            )
            or not mapping
        ):
            raise ValueError(
                f"{name} must be a non-empty dict."
            )

        normalized = {}

        for key in sorted(
            mapping
        ):
            value = mapping[
                key
            ]

            if (
                not isinstance(key, str)
                or not key
            ):
                raise ValueError(
                    f"{name} contains invalid key."
                )

            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(
                    char
                    not in "0123456789abcdef"
                    for char in value.lower()
                )
            ):
                raise ValueError(
                    f"{name}[{key!r}] is not "
                    "a valid SHA256 string."
                )

            normalized[
                key
            ] = value.lower()

        return normalized

    normalized_controls = (
        _validated_hash_mapping(
            name="control_hashes",
            mapping=control_hashes,
        )
    )

    normalized_upstream = (
        _validated_hash_mapping(
            name="upstream_hashes",
            mapping=upstream_hashes,
        )
    )

    output_hashes = {
        filename: _sha256_bytes(
            artifacts[
                filename
            ]
        )
        for filename in (
            _required_stage_b_output_filenames()
        )
    }

    return {
        "policy_version": (
            policy_version
        ),
        "csv_serialization_policy_id": (
            _contract
            .STAGE_B_CSV_SERIALIZATION_POLICY_ID
        ),
        "json_serialization_policy_id": (
            _contract
            .STAGE_B_JSON_SERIALIZATION_POLICY_ID
        ),
        "audit_hash_policy_id": (
            _contract
            .STAGE_B_AUDIT_HASH_POLICY_ID
        ),
        "control_hashes": (
            normalized_controls
        ),
        "upstream_hashes": (
            normalized_upstream
        ),
        "output_hashes": (
            output_hashes
        ),
    }




# STEP_14G1B_PARQUET_AND_AUDIT_SCHEMA_RUNTIME_V1_1


def _serialize_stage_b_parquet_bytes(
    *,
    frame: pd.DataFrame,
    field_order: list[str],
    row_sort_by: list[str],
) -> bytes:
    """
    Deterministically serialize the Stage B Parquet artifact.

    Profile:
      - explicit schema/column order
      - explicit stable row order
      - no pandas index
      - pyarrow engine
      - ZSTD compression
      - dictionary encoding disabled
      - fixed writer options

    Library versions must be recorded by production audit
    because Parquet writer metadata may be library-version
    sensitive even under a fixed writer profile.
    """

    import io

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "Stage B deterministic Parquet serialization "
            "requires pyarrow."
        ) from exc

    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(
        field_order,
        list,
    ):
        raise TypeError(
            "field_order must be a list."
        )

    if not field_order:
        raise ValueError(
            "field_order must not be empty."
        )

    if len(
        field_order
    ) != len(
        set(field_order)
    ):
        raise ValueError(
            "field_order contains duplicates."
        )

    if not isinstance(
        row_sort_by,
        list,
    ):
        raise TypeError(
            "row_sort_by must be a list."
        )

    if not row_sort_by:
        raise ValueError(
            "row_sort_by must explicitly define "
            "deterministic row ordering."
        )

    if len(
        row_sort_by
    ) != len(
        set(row_sort_by)
    ):
        raise ValueError(
            "row_sort_by contains duplicates."
        )

    for field in (
        field_order
        + row_sort_by
    ):
        if (
            not isinstance(field, str)
            or not field
        ):
            raise ValueError(
                "Parquet field names must be "
                "non-empty strings."
            )

    actual_columns = list(
        frame.columns
    )

    if set(
        actual_columns
    ) != set(
        field_order
    ):
        raise RuntimeError(
            "Parquet frame schema does not exactly "
            "match declared field_order."
        )

    unknown_sort_fields = [
        field
        for field in row_sort_by
        if field not in field_order
    ]

    if unknown_sort_fields:
        raise RuntimeError(
            "row_sort_by contains fields outside "
            f"the declared schema: {unknown_sort_fields}"
        )

    ordered = (
        frame.loc[
            :,
            field_order,
        ]
        .sort_values(
            by=row_sort_by,
            kind="mergesort",
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    table = pa.Table.from_pandas(
        ordered,
        preserve_index=False,
    )

    sink = io.BytesIO()

    pq.write_table(
        table,
        sink,
        compression="zstd",
        compression_level=3,
        use_dictionary=False,
        write_statistics=True,
        version="2.6",
        data_page_version="1.0",
    )

    raw = sink.getvalue()

    if not raw.startswith(
        b"PAR1"
    ):
        raise RuntimeError(
            "Serialized Parquet bytes lack "
            "the expected PAR1 header."
        )

    if not raw.endswith(
        b"PAR1"
    ):
        raise RuntimeError(
            "Serialized Parquet bytes lack "
            "the expected PAR1 footer."
        )

    return raw


def _required_stage_b_audit_fields(
) -> tuple[str, ...]:
    """
    Return the locked ?43 minimum audit metadata fields.

    Additional target-blind reproducibility metadata is
    permitted, but these fields may not be omitted.
    """

    return (
        "policy_version",
        "markdown_sha256",
        "semantic_registry_sha256",
        "locked_markdown_git_commit",
        "python_policy_status",
        "cell14_artifact_hashes",
        "cell14_registry_hash",
        "canonical_candidate_count",
        "feature_order_validation",
        "lookback_metadata_validation",
        "common_cohort_coverage_by_fold",
        "full29_yearly_coverage",
        "yearly_low_coverage_flags",
        "yearly_concentration_review_required",
        "yearly_concentration_review_status",
        "shared_240m_missingness_summary",
        "full29_incomplete_row_count",
        "shared_240m_incomplete_row_count",
        "session_to_date_vwap_only_incomplete_row_count",
        "unexplained_full29_incomplete_row_count",
        "fold_coverage_gate_result",
        "final_test_rows_opened",
        "forbidden_inputs_opened",
        "empirical_threshold_provenance",
        "coverage_threshold_provenance",
        "semantic_registry_completeness",
        "semantic_registry_structural_invariant_result",
        "markdown_json_joint_audit_status",
        "prelock_identity_validation_result",
        "prelock_final_test_firewall_result",
        "protected_semantic_basis_features",
        "derived_protected_set_feature_list",
        "protected_set_sentinel_result",
        "full_train_zero_variance_diagnostics",
        "common_cohort_zero_variance_diagnostics",
        "phase_a_decisions",
        "generic_phase_b_group_available_verification_results",
        "generic_phase_b_component_dispositions",
        "generic_phase_b_open_component_count",
        "generic_phase_b_hard_fail_count",
        "generic_phase_b_direct_drop_count",
        "phase_b_rank",
        "phase_c_rank",
        "phase_c_rank_loss",
        "phase_c_rank_loss_review_required",
        "phase_c_rank_loss_review_status",
        "primary_hard_pair_count",
        "cohort_sensitivity_supported_count",
        "cohort_sensitivity_conflict_count",
        "cohort_sensitivity_unavailable_count",
        "empirical_drops_vetoed_by_cohort_sensitivity",
        "full_set_condition_number",
        "post_phase_a_condition_number",
        "clustering_metric",
        "clustering_linkage",
        "clustering_cut",
        "open_count",
        "base_feature_count",
        "linear_overlay_feature_count",
        "tree_overlay_feature_count",
        "unique_stage_c_mask_count",
        "multi_value_serialization_policy_id",
        "output_hashes",
    )


def _validate_stage_b_audit_payload(
    *,
    payload: dict[str, object],
) -> dict[str, object]:
    """
    Validate the locked minimum Stage B audit schema.

    This is a structural/safety validator. Additional
    target-blind metadata is allowed.

    Under the non-recursive audit policy, audit JSON stores
    hashes for its six sibling artifacts. The external
    manifest produced after audit serialization hashes all
    seven Stage B artifacts, including the audit JSON itself.
    """

    from . import contract as _contract

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(
            "payload must be a dict."
        )

    required = (
        _required_stage_b_audit_fields()
    )

    missing = [
        field
        for field in required
        if field not in payload
    ]

    if missing:
        raise RuntimeError(
            "Stage B audit payload is missing "
            f"required fields: {missing}"
        )

    if payload[
        "policy_version"
    ] != _contract.POLICY_VERSION:
        raise RuntimeError(
            "Audit payload policy_version mismatch."
        )

    if payload[
        "python_policy_status"
    ] != "LOCKED_EXECUTABLE":
        raise RuntimeError(
            "Production audit must record "
            "python_policy_status=LOCKED_EXECUTABLE."
        )

    if payload[
        "canonical_candidate_count"
    ] != 29:
        raise RuntimeError(
            "Audit canonical candidate count must be 29."
        )

    if payload[
        "feature_order_validation"
    ] is not True:
        raise RuntimeError(
            "Audit feature-order validation did not pass."
        )

    if payload[
        "lookback_metadata_validation"
    ] is not True:
        raise RuntimeError(
            "Audit lookback validation did not pass."
        )

    if payload[
        "fold_coverage_gate_result"
    ] is not True:
        raise RuntimeError(
            "Audit fold-coverage gate did not pass."
        )

    if payload[
        "final_test_rows_opened"
    ] != 0:
        raise RuntimeError(
            "Audit records Final Test rows opened."
        )

    if payload[
        "forbidden_inputs_opened"
    ] != 0:
        raise RuntimeError(
            "Audit records forbidden inputs opened."
        )

    if payload[
        "unexplained_full29_incomplete_row_count"
    ] != 0:
        raise RuntimeError(
            "Audit contains unexplained full-29 "
            "incomplete rows."
        )

    if payload[
        "semantic_registry_completeness"
    ] is not True:
        raise RuntimeError(
            "Audit semantic registry completeness failed."
        )

    if payload[
        "semantic_registry_structural_invariant_result"
    ] is not True:
        raise RuntimeError(
            "Audit semantic registry structural "
            "invariants failed."
        )

    if payload[
        "markdown_json_joint_audit_status"
    ] != "PASS":
        raise RuntimeError(
            "Audit Markdown/JSON joint audit is not PASS."
        )

    if payload[
        "prelock_identity_validation_result"
    ] != "PASS":
        raise RuntimeError(
            "Audit pre-lock identity validation "
            "is not PASS."
        )

    if payload[
        "prelock_final_test_firewall_result"
    ] != "PASS":
        raise RuntimeError(
            "Audit pre-lock Final Test firewall "
            "is not PASS."
        )

    if payload[
        "protected_set_sentinel_result"
    ] is not True:
        raise RuntimeError(
            "Audit protected-set sentinel failed."
        )

    generic_direct_drop_count = payload[
        "generic_phase_b_direct_drop_count"
    ]
    if (
        not isinstance(generic_direct_drop_count, int)
        or isinstance(generic_direct_drop_count, bool)
        or generic_direct_drop_count != 0
    ):
        raise RuntimeError(
            "Audit records forbidden generic Phase-B direct DROP authority."
        )

    dispositions = payload[
        "generic_phase_b_component_dispositions"
    ]
    if not isinstance(dispositions, (list, tuple)):
        raise TypeError(
            "Audit generic Phase-B component dispositions must be a list or tuple."
        )

    for field in (
        "generic_phase_b_open_component_count",
        "generic_phase_b_hard_fail_count",
    ):
        value = payload[field]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise RuntimeError(
                f"Audit {field} must be a non-negative int."
            )

    yearly_review_required = payload[
        "yearly_concentration_review_required"
    ]

    yearly_review_status = payload[
        "yearly_concentration_review_status"
    ]

    if (
        yearly_review_required is True
        and yearly_review_status
        != "ACKNOWLEDGED"
    ):
        raise RuntimeError(
            "Required yearly concentration review "
            "has not been acknowledged."
        )

    rank_review_required = payload[
        "phase_c_rank_loss_review_required"
    ]

    rank_review_status = payload[
        "phase_c_rank_loss_review_status"
    ]

    if (
        rank_review_required is True
        and rank_review_status
        != "ACKNOWLEDGED"
    ):
        raise RuntimeError(
            "Required Phase-C rank-loss review "
            "has not been acknowledged."
        )

    if payload[
        "clustering_metric"
    ] != "1-ABS_SPEARMAN":
        raise RuntimeError(
            "Audit clustering metric mismatch."
        )

    if payload[
        "clustering_linkage"
    ] != "COMPLETE":
        raise RuntimeError(
            "Audit clustering linkage mismatch."
        )

    try:
        clustering_cut = float(
            payload[
                "clustering_cut"
            ]
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            "Audit clustering cut is invalid."
        ) from exc

    if abs(
        clustering_cut
        - 0.10
    ) > 1e-12:
        raise RuntimeError(
            "Audit clustering cut mismatch."
        )

    if payload[
        "multi_value_serialization_policy_id"
    ] != (
        _contract
        .STAGE_B_MULTI_VALUE_SERIALIZATION_POLICY_ID
    ):
        raise RuntimeError(
            "Audit multi-value serialization "
            "policy identifier mismatch."
        )

    unique_mask_count = payload[
        "unique_stage_c_mask_count"
    ]

    if (
        not isinstance(
            unique_mask_count,
            int,
        )
        or isinstance(
            unique_mask_count,
            bool,
        )
        or unique_mask_count < 0
        or unique_mask_count > 3
    ):
        raise RuntimeError(
            "Audit unique Stage-C mask count "
            "must lie between 0 and 3."
        )

    sibling_outputs = (
        _required_stage_b_output_filenames()[:-1]
    )

    output_hashes = payload[
        "output_hashes"
    ]

    if not isinstance(
        output_hashes,
        dict,
    ):
        raise TypeError(
            "Audit output_hashes must be a dict."
        )

    if set(
        output_hashes
    ) != set(
        sibling_outputs
    ):
        raise RuntimeError(
            "Audit output_hashes must contain exactly "
            "the six sibling Stage B artifacts."
        )

    def _is_sha256(
        value: object,
    ) -> bool:
        return bool(
            isinstance(
                value,
                str,
            )
            and len(value) == 64
            and all(
                char in "0123456789abcdef"
                for char in value.lower()
            )
        )

    for filename in sibling_outputs:
        if not _is_sha256(
            output_hashes[
                filename
            ]
        ):
            raise RuntimeError(
                f"Audit output hash for {filename} "
                "is not a valid SHA256."
            )

    for field in [
        "markdown_sha256",
        "semantic_registry_sha256",
        "cell14_registry_hash",
    ]:
        if not _is_sha256(
            payload[
                field
            ]
        ):
            raise RuntimeError(
                f"Audit {field} is not "
                "a valid SHA256."
            )

    cell14_hashes = payload[
        "cell14_artifact_hashes"
    ]

    if (
        not isinstance(
            cell14_hashes,
            dict,
        )
        or not cell14_hashes
    ):
        raise RuntimeError(
            "Audit cell14_artifact_hashes must "
            "be a non-empty dict."
        )

    for key, value in (
        cell14_hashes.items()
    ):
        if (
            not isinstance(key, str)
            or not key
            or not _is_sha256(value)
        ):
            raise RuntimeError(
                "Audit contains an invalid "
                "Cell 14 artifact hash."
            )

    return {
        "audit_payload_valid": True,
        "required_field_count": int(
            len(required)
        ),
        "audit_output_hash_names": (
            sibling_outputs
        ),
        "additional_metadata_fields": tuple(
            sorted(
                set(payload).difference(
                    required
                )
            )
        ),
    }




# STEP_14G2C_MINIMAL_V1_1_PREREQUISITE_RUNTIME


def _reconcile_full29_missingness(
    *,
    frame: pd.DataFrame,
    canonical_features: list[str],
    shared_240m_features: list[str],
    session_to_date_feature: str,
    status_column: str,
) -> dict[str, object]:
    """
    Reconcile full-feature missingness by row-level
    availability components.

    A shared 240-minute availability failure is one
    row-level component even though five canonical
    240-minute features are simultaneously unavailable.

    SESSION_TO_DATE VWAP-only rows form the second
    independently reconciled component.

    Any remaining incomplete row stays explicitly
    unexplained. Nothing is imputed or silently removed.
    """

    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "frame must be a pandas DataFrame."
        )

    for name, values in [
        (
            "canonical_features",
            canonical_features,
        ),
        (
            "shared_240m_features",
            shared_240m_features,
        ),
    ]:
        if not isinstance(
            values,
            list,
        ):
            raise TypeError(
                f"{name} must be a list."
            )

        if not values:
            raise ValueError(
                f"{name} must not be empty."
            )

        if len(
            values
        ) != len(
            set(values)
        ):
            raise ValueError(
                f"{name} contains duplicates."
            )

        if any(
            (
                not isinstance(
                    value,
                    str,
                )
                or not value
            )
            for value in values
        ):
            raise ValueError(
                f"{name} must contain "
                "non-empty strings."
            )

    if not isinstance(
        session_to_date_feature,
        str,
    ) or not session_to_date_feature:
        raise ValueError(
            "session_to_date_feature must be "
            "a non-empty string."
        )

    if not isinstance(
        status_column,
        str,
    ) or not status_column:
        raise ValueError(
            "status_column must be "
            "a non-empty string."
        )

    if not set(
        shared_240m_features
    ).issubset(
        canonical_features
    ):
        raise RuntimeError(
            "shared_240m_features must be "
            "canonical features."
        )

    if (
        session_to_date_feature
        not in canonical_features
    ):
        raise RuntimeError(
            "session_to_date_feature must be "
            "a canonical feature."
        )

    required_columns = set(
        canonical_features
    ) | {
        status_column,
    }

    missing_columns = sorted(
        required_columns.difference(
            frame.columns
        )
    )

    if missing_columns:
        raise RuntimeError(
            "Missing required reconciliation columns: "
            f"{missing_columns}"
        )

    candidate_frame = frame.loc[
        :,
        canonical_features,
    ]

    incomplete_mask = (
        candidate_frame
        .isna()
        .any(
            axis=1
        )
    )

    shared_mask = (
        frame.loc[
            :,
            shared_240m_features,
        ]
        .isna()
        .all(
            axis=1
        )
        & incomplete_mask
    )

    non_session_features = [
        feature
        for feature in canonical_features
        if feature
        != session_to_date_feature
    ]

    session_only_mask = (
        frame[
            session_to_date_feature
        ].isna()
        & frame.loc[
            :,
            non_session_features,
        ]
        .notna()
        .all(
            axis=1
        )
        & incomplete_mask
    )

    explained_mask = (
        shared_mask
        | session_only_mask
    )

    unexplained_mask = (
        incomplete_mask
        & ~explained_mask
    )

    full29_incomplete = int(
        incomplete_mask.sum()
    )

    shared_rows = int(
        shared_mask.sum()
    )

    session_only_rows = int(
        session_only_mask.sum()
    )

    unexplained_rows = int(
        unexplained_mask.sum()
    )

    if (
        shared_rows
        + session_only_rows
        + unexplained_rows
        != full29_incomplete
    ):
        raise RuntimeError(
            "Missingness component reconciliation "
            "is internally inconsistent."
        )

    session_status_values = (
        frame.loc[
            session_only_mask,
            status_column,
        ]
        .astype(
            "string"
        )
    )

    session_status_valid = bool(
        (
            session_status_values
            == "SESSION_VWAP_INPUT_INVALID"
        ).all()
    )

    return {
        "full29_incomplete_row_count": (
            full29_incomplete
        ),
        "shared_240m_incomplete_row_count": (
            shared_rows
        ),
        (
            "session_to_date_vwap_only_"
            "incomplete_row_count"
        ): (
            session_only_rows
        ),
        (
            "unexplained_full29_"
            "incomplete_row_count"
        ): (
            unexplained_rows
        ),
        "shared_240m_missingness_summary": {
            "features": tuple(
                shared_240m_features
            ),
            "feature_count": int(
                len(
                    shared_240m_features
                )
            ),
            "row_count": (
                shared_rows
            ),
        },
        (
            "session_to_date_vwap_only_"
            "status_validation"
        ): (
            session_status_valid
        ),
        "component_reconciliation_valid": (
            unexplained_rows == 0
            and session_status_valid
        ),
    }


def _compute_intercept_rank_diagnostic(
    *,
    standardized_matrix: np.ndarray,
) -> dict[str, object]:
    """
    Report rank/deficiency for Z and [1, Z].

    This is the locked descriptive affine/intercept
    diagnostic. It does not make feature decisions.
    """

    matrix = np.asarray(
        standardized_matrix,
        dtype=np.float64,
    )

    if matrix.ndim != 2:
        raise ValueError(
            "standardized_matrix must be 2-dimensional."
        )

    n_rows, n_features = (
        matrix.shape
    )

    if n_rows < 1:
        raise ValueError(
            "standardized_matrix must contain rows."
        )

    if n_features < 1:
        raise ValueError(
            "standardized_matrix must contain features."
        )

    if not np.isfinite(
        matrix
    ).all():
        raise ValueError(
            "standardized_matrix must be finite."
        )

    feature_diag = (
        compute_svd_diagnostics(
            matrix
        )
    )

    augmented = np.column_stack(
        [
            np.ones(
                n_rows,
                dtype=np.float64,
            ),
            matrix,
        ]
    )

    augmented_diag = (
        compute_svd_diagnostics(
            augmented
        )
    )

    return {
        "feature_space_shape": (
            n_rows,
            n_features,
        ),
        "feature_space_rank": int(
            feature_diag[
                "rank"
            ]
        ),
        "feature_space_deficiency": int(
            feature_diag[
                "deficiency"
            ]
        ),
        "feature_space_rank_tolerance": float(
            feature_diag[
                "rank_tolerance"
            ]
        ),
        "augmented_design_shape": (
            n_rows,
            n_features + 1,
        ),
        "augmented_design_rank": int(
            augmented_diag[
                "rank"
            ]
        ),
        "augmented_design_deficiency": int(
            augmented_diag[
                "deficiency"
            ]
        ),
        "augmented_design_rank_tolerance": float(
            augmented_diag[
                "rank_tolerance"
            ]
        ),
        "diagnostic_only": True,
    }


def _resolve_stage_b_condition_number(
    *,
    svd_diagnostics: dict[str, object],
    diagnostic_scope: str,
) -> dict[str, object]:
    """
    Resolve the locked Stage B condition-number policy.

    FULL_SET:
      rank deficient -> infinity.

    POST_PHASE_A_CANDIDATE_SET:
      rank deficiency -> infinity plus generic discovery required.

    A full-rank condition number is sigma_max / sigma_min.
    Condition number never independently drops a feature.
    """

    if not isinstance(
        svd_diagnostics,
        dict,
    ):
        raise TypeError(
            "svd_diagnostics must be a dict."
        )

    if diagnostic_scope not in {
        "FULL_SET",
        "POST_PHASE_A_CANDIDATE_SET",
    }:
        raise ValueError(
            "diagnostic_scope must be FULL_SET or "
            "POST_PHASE_A_CANDIDATE_SET."
        )

    required = {
        "matrix_shape",
        "singular_values",
        "rank",
        "deficiency",
    }

    missing = sorted(
        required.difference(
            svd_diagnostics
        )
    )

    if missing:
        raise RuntimeError(
            "Missing SVD diagnostic fields: "
            f"{missing}"
        )

    shape = svd_diagnostics[
        "matrix_shape"
    ]

    if (
        not isinstance(
            shape,
            (
                tuple,
                list,
            ),
        )
        or len(shape) != 2
    ):
        raise ValueError(
            "matrix_shape must contain "
            "(n_rows, n_features)."
        )

    n_rows = int(
        shape[0]
    )

    n_features = int(
        shape[1]
    )

    if (
        n_rows < 1
        or n_features < 1
    ):
        raise ValueError(
            "matrix_shape must be positive."
        )

    rank = int(
        svd_diagnostics[
            "rank"
        ]
    )

    deficiency = int(
        svd_diagnostics[
            "deficiency"
        ]
    )

    if (
        rank < 0
        or deficiency < 0
        or rank + deficiency
        != n_features
    ):
        raise RuntimeError(
            "SVD rank/deficiency is inconsistent "
            "with matrix_shape."
        )

    singular_values = np.asarray(
        svd_diagnostics[
            "singular_values"
        ],
        dtype=np.float64,
    )

    if (
        singular_values.ndim != 1
        or singular_values.size < 1
    ):
        raise ValueError(
            "singular_values must be "
            "a non-empty vector."
        )

    if not np.isfinite(
        singular_values
    ).all():
        raise ValueError(
            "singular_values must be finite."
        )

    if (
        singular_values < 0.0
    ).any():
        raise ValueError(
            "singular_values must be non-negative."
        )

    sigma_max = float(
        singular_values[0]
    )

    sigma_min = float(
        singular_values[-1]
    )

    if deficiency > 0:
        condition_number = float(
            "inf"
        )
    else:
        if sigma_min <= 0.0:
            raise RuntimeError(
                f"Full-rank {diagnostic_scope} has "
                "non-positive sigma_min."
            )

        condition_number = (
            sigma_max
            / sigma_min
        )

    return {
        "diagnostic_scope": (
            diagnostic_scope
        ),
        "rank": (
            rank
        ),
        "deficiency": (
            deficiency
        ),
        "sigma_max": (
            sigma_max
        ),
        "sigma_min": (
            sigma_min
        ),
        "condition_number": float(
            condition_number
        ),
        "decision_effect": "REPORT_ONLY",
        "generic_rank_discovery_required": (
            diagnostic_scope
            == "POST_PHASE_A_CANDIDATE_SET"
            and deficiency > 0
        ),
    }


def _build_stage_c_feature_masks(
    *,
    base_features: list[str],
    linear_removed_features: list[str],
    tree_removed_features: list[str],
    protected_features: set[str],
    canonical_order: list[str],
) -> dict[str, object]:
    """
    Build deterministic BASE / LINEAR / TREE masks.

    Overlay removals may only remove members of BASE.
    They may not reintroduce a BASE-dropped feature.

    Protected BASE removals by overlays are allowed only
    as explicitly recorded evidence, as required by the
    locked contract.

    Identical masks are deterministically deduplicated.
    """

    list_inputs = {
        "base_features": (
            base_features
        ),
        "linear_removed_features": (
            linear_removed_features
        ),
        "tree_removed_features": (
            tree_removed_features
        ),
        "canonical_order": (
            canonical_order
        ),
    }

    for name, values in (
        list_inputs.items()
    ):
        if not isinstance(
            values,
            list,
        ):
            raise TypeError(
                f"{name} must be a list."
            )

        if len(
            values
        ) != len(
            set(values)
        ):
            raise ValueError(
                f"{name} contains duplicates."
            )

        if any(
            (
                not isinstance(
                    value,
                    str,
                )
                or not value
            )
            for value in values
        ):
            raise ValueError(
                f"{name} must contain "
                "non-empty strings."
            )

    if not isinstance(
        protected_features,
        set,
    ):
        raise TypeError(
            "protected_features must be a set."
        )

    if any(
        (
            not isinstance(
                value,
                str,
            )
            or not value
        )
        for value in protected_features
    ):
        raise ValueError(
            "protected_features must contain "
            "non-empty strings."
        )

    canonical_set = set(
        canonical_order
    )

    base_set = set(
        base_features
    )

    linear_removed = set(
        linear_removed_features
    )

    tree_removed = set(
        tree_removed_features
    )

    if not base_set.issubset(
        canonical_set
    ):
        raise RuntimeError(
            "BASE contains a feature outside "
            "canonical_order."
        )

    if not protected_features.issubset(
        canonical_set
    ):
        raise RuntimeError(
            "protected_features contains a "
            "non-canonical feature."
        )

    if not linear_removed.issubset(
        base_set
    ):
        invalid = sorted(
            linear_removed.difference(
                base_set
            )
        )

        raise RuntimeError(
            "LINEAR overlay may remove only BASE "
            f"features: {invalid}"
        )

    if not tree_removed.issubset(
        base_set
    ):
        invalid = sorted(
            tree_removed.difference(
                base_set
            )
        )

        raise RuntimeError(
            "TREE overlay may remove only BASE "
            f"features: {invalid}"
        )

    def _ordered(
        members: set[str],
    ) -> tuple[str, ...]:
        return tuple(
            feature
            for feature in canonical_order
            if feature in members
        )

    base_mask = _ordered(
        base_set
    )

    linear_mask = _ordered(
        base_set.difference(
            linear_removed
        )
    )

    tree_mask = _ordered(
        base_set.difference(
            tree_removed
        )
    )

    ordered_candidates = (
        base_mask,
        linear_mask,
        tree_mask,
    )

    unique_masks_list = []

    for mask in (
        ordered_candidates
    ):
        if mask not in (
            unique_masks_list
        ):
            unique_masks_list.append(
                mask
            )

    unique_masks = tuple(
        unique_masks_list
    )

    if len(
        unique_masks
    ) > 3:
        raise RuntimeError(
            "Stage C produced more than "
            "three unique masks."
        )

    protected_linear = _ordered(
        protected_features.intersection(
            linear_removed
        )
    )

    protected_tree = _ordered(
        protected_features.intersection(
            tree_removed
        )
    )

    return {
        "base_mask": (
            base_mask
        ),
        "linear_overlay_mask": (
            linear_mask
        ),
        "tree_overlay_mask": (
            tree_mask
        ),
        "unique_masks": (
            unique_masks
        ),
        "unique_stage_c_mask_count": int(
            len(
                unique_masks
            )
        ),
        "base_feature_count": int(
            len(
                base_mask
            )
        ),
        "linear_overlay_feature_count": int(
            len(
                linear_mask
            )
        ),
        "tree_overlay_feature_count": int(
            len(
                tree_mask
            )
        ),
        "protected_overlay_removals": {
            "LINEAR_OVERLAY": (
                protected_linear
            ),
            "TREE_OVERLAY": (
                protected_tree
            ),
        },
        "overlay_count": 2,
    }




# STEP_14G3A_GATED_SOLE_PRODUCTION_READER_BOUNDARY



# STEP_14G3B1_PROVENANCE_CONTROL_FIREWALL


def _validate_stage_b_release_manifest_binding(
    *,
    release_manifest: dict[str, object],
) -> dict[str, object]:
    """
    Bind Stage B to the canonical target-independent
    Cell 14 / Cell 8 provenance chain.

    Cell 8 assignments remain hash/path bound as an upstream
    provenance authority, but are not a Stage B runtime-readable
    artifact. Runtime fold roles are carried by the canonical
    Cell 14 Development feature artifact.
    """

    from pathlib import PurePosixPath

    from . import contract as _contract

    if not isinstance(
        release_manifest,
        dict,
    ):
        raise TypeError(
            "release_manifest must be a dict."
        )

    try:
        canonical_artifacts = (
            release_manifest[
                "runs"
            ][
                "canonical"
            ][
                "artifacts"
            ]
        )

        upstream_inputs = (
            release_manifest[
                "upstream_inputs"
            ]
        )

    except (
        KeyError,
        TypeError,
    ) as exc:
        raise RuntimeError(
            "Cell14 release manifest is missing "
            "required Stage B binding structure."
        ) from exc

    specifications = (
        (
            "cell14_features",
            canonical_artifacts,
            "features",
            _contract.CELL14_FEATURE_FILE_SHA256,
        ),
        (
            "cell14_registry",
            canonical_artifacts,
            "registry",
            _contract.CELL14_REGISTRY_FILE_SHA256,
        ),
        (
            "cell14_audit",
            canonical_artifacts,
            "audit",
            _contract.CELL14_AUDIT_FILE_SHA256,
        ),
        (
            "cell8_assignments",
            upstream_inputs,
            "cell8_assignments",
            _contract.CELL8_ASSIGNMENTS_FILE_SHA256,
        ),
        (
            "cell8_audit",
            upstream_inputs,
            "cell8_audit",
            _contract.CELL8_AUDIT_FILE_SHA256,
        ),
    )

    def _valid_sha256(
        value: object,
    ) -> bool:
        return bool(
            isinstance(
                value,
                str,
            )
            and len(value) == 64
            and all(
                char
                in "0123456789abcdef"
                for char
                in value.lower()
            )
        )

    def _safe_relative_repo_path(
        value: object,
    ) -> bool:
        if (
            not isinstance(
                value,
                str,
            )
            or not value
            or "\\" in value
        ):
            return False

        path = PurePosixPath(
            value
        )

        if path.is_absolute():
            return False

        if any(
            part
            in {
                "",
                ".",
                "..",
            }
            for part
            in path.parts
        ):
            return False

        return True

    bindings = {}

    for (
        artifact_id,
        parent,
        source_id,
        expected_sha256,
    ) in specifications:

        try:
            source = parent[
                source_id
            ]

        except (
            KeyError,
            TypeError,
        ) as exc:
            raise RuntimeError(
                "Release manifest is missing "
                f"required artifact {artifact_id}."
            ) from exc

        if not isinstance(
            source,
            dict,
        ):
            raise RuntimeError(
                f"{artifact_id} binding must be a dict."
            )

        file_value = source.get(
            "file"
        )

        hash_value = source.get(
            "sha256"
        )

        if not _safe_relative_repo_path(
            file_value
        ):
            raise RuntimeError(
                "Unsafe or escaping canonical "
                f"artifact path for {artifact_id}: "
                f"{file_value!r}"
            )

        if not _valid_sha256(
            hash_value
        ):
            raise RuntimeError(
                f"Invalid SHA256 for {artifact_id}."
            )

        if (
            hash_value
            != expected_sha256
        ):
            raise RuntimeError(
                "Frozen release hash mismatch for "
                f"{artifact_id}."
            )

        bindings[
            artifact_id
        ] = {
            "file": file_value,
            "sha256": hash_value,
        }

    bound_artifact_ids = tuple(
        bindings
    )

    expected_bound_artifact_ids = (
        "cell14_features",
        "cell14_registry",
        "cell14_audit",
        "cell8_assignments",
        "cell8_audit",
    )

    if (
        bound_artifact_ids
        != expected_bound_artifact_ids
    ):
        raise RuntimeError(
            "Stage B bound artifact order "
            "is not canonical."
        )

    provenance_only_artifact_ids = (
        "cell8_assignments",
    )

    readable_artifact_ids = (
        "cell14_features",
        "cell14_registry",
        "cell14_audit",
        "cell8_audit",
    )

    if (
        set(
            provenance_only_artifact_ids
        )
        & set(
            readable_artifact_ids
        )
    ):
        raise RuntimeError(
            "Stage B readable and provenance-only "
            "artifact sets overlap."
        )

    if (
        set(
            provenance_only_artifact_ids
        )
        | set(
            readable_artifact_ids
        )
        != set(
            bound_artifact_ids
        )
    ):
        raise RuntimeError(
            "Stage B readable/provenance artifact "
            "classification does not cover every "
            "bound artifact exactly once."
        )

    return {
        "readable_artifact_ids": (
            readable_artifact_ids
        ),
        "provenance_only_artifact_ids": (
            provenance_only_artifact_ids
        ),
        "bound_artifact_ids": (
            bound_artifact_ids
        ),
        "artifact_bindings": bindings,
        "release_manifest_binding_valid": True,
    }




def _phase_a_canonical_metadata(
    *,
    phase0,
):
    """Read the immutable canonical metadata already validated by Phase 0."""

    canonical_features = phase0.get(
        "canonical_features"
    )
    registry_validation = phase0.get(
        "registry_validation"
    )

    if not isinstance(
        canonical_features,
        tuple,
    ):
        raise TypeError(
            "Phase 0 canonical_features must be an immutable tuple."
        )

    if not isinstance(
        registry_validation,
        dict,
    ):
        raise TypeError(
            "Phase 0 registry validation is unavailable."
        )

    metadata_snapshot = registry_validation.get(
        "canonical_feature_metadata"
    )

    if not isinstance(
        metadata_snapshot,
        tuple,
    ):
        raise TypeError(
            "Phase 0 canonical metadata snapshot is unavailable."
        )

    if len(metadata_snapshot) != len(canonical_features):
        raise RuntimeError(
            "Phase 0 canonical metadata length mismatch."
        )

    field_names = _CANONICAL_METADATA_FIELDS
    metadata_by_feature: dict[str, dict[str, object]] = {}

    for index, metadata_row in enumerate(
        metadata_snapshot
    ):
        if (
            not isinstance(metadata_row, tuple)
            or len(metadata_row) != len(field_names)
        ):
            raise RuntimeError(
                "Phase 0 canonical metadata row is invalid."
            )

        row = dict(
            zip(
                field_names,
                metadata_row,
                strict=True,
            )
        )
        feature = row[
            "feature"
        ]

        if feature != canonical_features[index]:
            raise RuntimeError(
                "Phase 0 canonical metadata order mismatch."
            )

        if feature in metadata_by_feature:
            raise RuntimeError(
                "Phase 0 canonical metadata contains duplicates."
            )

        metadata_by_feature[
            feature
        ] = row

    return (
        canonical_features,
        metadata_snapshot,
        metadata_by_feature,
    )


def _minimum_train_fold_availability(
    *,
    feature_frame,
    features,
    fold_role_columns,
):
    """Compute point-in-time availability from TRAIN rows in every fold."""

    availability_by_fold: dict[
        str,
        dict[str, float],
    ] = {}

    for fold_role_column in fold_role_columns:
        train_mask = get_train_mask(
            feature_frame,
            fold_role_column,
        )

        if not bool(train_mask.any()):
            raise RuntimeError(
                "Phase A requires non-empty TRAIN rows in every fold."
            )

        train_frame = feature_frame.loc[
            train_mask,
            list(features),
        ]
        fold_availability = train_frame.notna().mean(
            axis=0
        )
        availability_by_fold[
            fold_role_column
        ] = {
            feature: float(
                fold_availability[
                    feature
                ]
            )
            for feature in features
        }

    minimum_availability = {
        feature: min(
            availability_by_fold[fold][feature]
            for fold in fold_role_columns
        )
        for feature in features
    }

    return (
        minimum_availability,
        availability_by_fold,
    )


def _order_phase_a_semantic_basis_candidates(
    *,
    features,
    canonical_features,
    protected_features,
    minimum_availability,
    metadata_by_feature,
):
    """Order members for a registry-authorized Phase-A semantic basis."""

    feature_set = set(
        features
    )
    canonical_group = [
        feature
        for feature in canonical_features
        if feature in feature_set
    ]

    if (
        len(canonical_group) != len(features)
        or set(canonical_group) != feature_set
    ):
        raise RuntimeError(
            "Exact semantic group is not canonical."
        )

    protected_set = set(
        protected_features
    )
    partitions = (
        [
            feature
            for feature in canonical_group
            if feature in protected_set
        ],
        [
            feature
            for feature in canonical_group
            if feature not in protected_set
        ],
    )
    ordered: list[str] = []
    canonical_position = {
        feature: index
        for index, feature in enumerate(
            canonical_features
        )
    }

    for partition in partitions:
        availability_levels = sorted(
            {
                minimum_availability[
                    feature
                ]
                for feature in partition
            },
            reverse=True,
        )

        for availability in availability_levels:
            block = [
                feature
                for feature in partition
                if minimum_availability[feature]
                == availability
            ]
            reordered_block = list(
                block
            )
            comparable_groups: dict[
                tuple[object, ...],
                list[str],
            ] = {}

            for feature in block:
                metadata = metadata_by_feature[
                    feature
                ]
                mode = metadata[
                    "lookback_mode"
                ]

                if mode == "FIXED":
                    comparable_key = (
                        mode,
                    )
                elif mode == "SESSION_TO_DATE":
                    comparable_key = (
                        mode,
                        metadata[
                            "lookback_start_rule"
                        ],
                    )
                else:
                    raise RuntimeError(
                        "Unsupported canonical lookback mode."
                    )

                comparable_groups.setdefault(
                    comparable_key,
                    [],
                ).append(
                    feature
                )

            for comparable_features in (
                comparable_groups.values()
            ):
                positions = [
                    index
                    for index, feature in enumerate(
                        block
                    )
                    if feature in comparable_features
                ]
                ranked_features = sorted(
                    comparable_features,
                    key=lambda feature: (
                        metadata_by_feature[feature][
                            "lookback_bars"
                        ],
                        metadata_by_feature[feature][
                            "lookback_minutes"
                        ],
                        canonical_position[
                            feature
                        ],
                    ),
                )

                for position, feature in zip(
                    positions,
                    ranked_features,
                    strict=True,
                ):
                    reordered_block[
                        position
                    ] = feature

            ordered.extend(
                reordered_block
            )

    if (
        len(ordered) != len(features)
        or set(ordered) != feature_set
    ):
        raise RuntimeError(
            "Exact semantic retention order is incomplete."
        )

    return tuple(
        ordered
    )


def _resolve_phase_a_undirected_semantic_basis(
    *,
    feature_frame,
    entry,
    canonical_features,
    protected_features,
    metadata_by_feature,
    fold_role_columns,
):
    """Resolve one registry-authorized Phase-A basis in every TRAIN fold."""

    if (
        entry.get("check_type")
        != "EXACT_AFFINE_DEPENDENCY"
        or entry.get("decision_effect")
        != "DROP_ONE_DETERMINISTIC_REFERENCE_KEEP_FOUR_DIMENSIONS"
    ):
        raise RuntimeError(
            "Phase-A semantic-basis selection requires explicit locked "
            "registry authority."
        )

    features = tuple(
        entry[
            "features"
        ]
    )
    required_drop_count = entry[
        "required_drop_count"
    ]

    if (
        not isinstance(required_drop_count, int)
        or isinstance(required_drop_count, bool)
        or required_drop_count <= 0
    ):
        raise RuntimeError(
            "Undirected exact basis requires a positive drop count."
        )

    (
        minimum_availability,
        availability_by_fold,
    ) = _minimum_train_fold_availability(
        feature_frame=feature_frame,
        features=features,
        fold_role_columns=fold_role_columns,
    )
    semantic_reference_order = _order_phase_a_semantic_basis_candidates(
        features=features,
        canonical_features=canonical_features,
        protected_features=protected_features,
        minimum_availability=minimum_availability,
        metadata_by_feature=metadata_by_feature,
    )

    train_union = pd.Series(
        False,
        index=feature_frame.index,
        dtype="bool",
    )

    for fold_role_column in fold_role_columns:
        train_union = (
            train_union
            | get_train_mask(
                feature_frame,
                fold_role_column,
            )
        )

    global_train_frame = feature_frame.loc[
        train_union,
        list(features),
    ]

    try:
        basis = _select_phase_a_semantic_rank_basis(
            frame=global_train_frame,
            feature_columns=list(features),
            semantic_reference_order=list(
                semantic_reference_order
            ),
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            "Global exact semantic basis is invalid."
        ) from exc

    information_dimension = int(
        len(features)
        - required_drop_count
    )

    if (
        basis[
            "original_rank"
        ] != information_dimension
        or basis[
            "final_retained_rank"
        ] != information_dimension
        or len(
            basis[
                "excluded_features"
            ]
        ) != required_drop_count
    ):
        raise RuntimeError(
            "Global exact semantic basis has the wrong dimension."
        )

    retained_features = tuple(
        basis[
            "retained_features"
        ]
    )
    fold_rank_diagnostics: dict[
        str,
        dict[str, object],
    ] = {}

    for fold_role_column in fold_role_columns:
        train_mask = get_train_mask(
            feature_frame,
            fold_role_column,
        )
        train_frame = feature_frame.loc[
            train_mask
        ]

        try:
            original_matrix = build_standardized_matrix(
                frame=train_frame,
                feature_columns=list(
                    features
                ),
            )
            original_diagnostics = compute_svd_diagnostics(
                original_matrix
            )
            retained_matrix = build_standardized_matrix(
                frame=train_frame,
                feature_columns=list(
                    retained_features
                ),
            )
            retained_diagnostics = compute_svd_diagnostics(
                retained_matrix
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise RuntimeError(
                "Exact semantic basis failed in a TRAIN fold."
            ) from exc

        original_rank = int(
            original_diagnostics[
                "rank"
            ]
        )
        retained_rank = int(
            retained_diagnostics[
                "rank"
            ]
        )

        if (
            original_rank != information_dimension
            or retained_rank != information_dimension
        ):
            raise RuntimeError(
                "Exact semantic basis does not preserve TRAIN-fold rank."
            )

        fold_rank_diagnostics[
            fold_role_column
        ] = {
            "retained_features": retained_features,
            "original_rank": original_rank,
            "retained_rank": retained_rank,
            "original_svd_diagnostics": (
                original_diagnostics
            ),
            "retained_svd_diagnostics": (
                retained_diagnostics
            ),
        }

    canonical_lookback_metadata = {
        feature: (
            metadata_by_feature[feature][
                "lookback_mode"
            ],
            metadata_by_feature[feature][
                "lookback_bars"
            ],
            metadata_by_feature[feature][
                "lookback_minutes"
            ],
            metadata_by_feature[feature][
                "lookback_start_rule"
            ],
        )
        for feature in features
    }

    return {
        "retained_features": retained_features,
        "dropped_features": tuple(
            basis[
                "excluded_features"
            ]
        ),
        "information_dimension": (
            information_dimension
        ),
        "fold_rank_diagnostics": (
            fold_rank_diagnostics
        ),
        "retention_priority_evidence": {
            "explicit_semantic_direction": False,
            "protected_features": tuple(
                feature
                for feature in semantic_reference_order
                if feature in set(
                    protected_features
                )
            ),
            "minimum_train_fold_availability": (
                minimum_availability
            ),
            "train_fold_availability": (
                availability_by_fold
            ),
            "canonical_lookback_metadata": (
                canonical_lookback_metadata
            ),
            "canonical_feature_order": tuple(
                feature
                for feature in canonical_features
                if feature in set(features)
            ),
            "ordered_features": semantic_reference_order,
        },
    }


def _resolve_phase_a_relationship(
    *,
    feature_frame,
    entry,
    canonical_features,
    protected_features,
    metadata_by_feature,
    fold_role_columns,
):
    """Resolve one relationship solely from its registry decision effect."""

    features = tuple(
        entry[
            "features"
        ]
    )
    dependent_features = tuple(
        entry[
            "dependent_features"
        ]
    )
    determining_features = tuple(
        entry[
            "determining_features"
        ]
    )
    decision_effect = entry[
        "decision_effect"
    ]
    required_drop_count = entry[
        "required_drop_count"
    ]
    retained_features: tuple[str, ...]
    dropped_features: tuple[str, ...]
    unresolved_features: tuple[str, ...] = ()
    extra_evidence: dict[str, object] = {}

    if decision_effect == "DROP_DEPENDENT_KEEP_DETERMINING":
        if set(features) != (
            set(dependent_features)
            | set(determining_features)
        ):
            raise RuntimeError(
                "Directed semantic relationship is incomplete."
            )

        retained_features = determining_features
        dropped_features = dependent_features
    elif decision_effect == "RETAIN_DERIVED_NONLINEAR_REPRESENTATION":
        retained_features = features
        dropped_features = ()
    elif decision_effect == "DROP_ONE_DETERMINISTIC_REFERENCE_KEEP_FOUR_DIMENSIONS":
        semantic_basis = _resolve_phase_a_undirected_semantic_basis(
            feature_frame=feature_frame,
            entry=entry,
            canonical_features=canonical_features,
            protected_features=protected_features,
            metadata_by_feature=metadata_by_feature,
            fold_role_columns=fold_role_columns,
        )
        retained_features = tuple(
            semantic_basis[
                "retained_features"
            ]
        )
        dropped_features = tuple(
            semantic_basis[
                "dropped_features"
            ]
        )
        extra_evidence = {
            key: value
            for key, value in semantic_basis.items()
            if key not in {
                "retained_features",
                "dropped_features",
            }
        }
    elif decision_effect == "RETAIN_BOTH_PAIRED_REPRESENTATION":
        retained_features = features
        dropped_features = ()
    elif decision_effect == "PHASE_C_HARD_MAY_DROP_ONLY_UNPROTECTED_MEMBER":
        retained_features = features
        dropped_features = ()
        unresolved_features = tuple(
            feature
            for feature in features
            if feature not in set(
                protected_features
            )
        )
        extra_evidence = {
            "phase_c_executed": False,
        }
    else:
        raise RuntimeError(
            "Unsupported Phase A decision_effect: "
            f"{decision_effect!r}"
        )

    if required_drop_count is None:
        if dropped_features:
            raise RuntimeError(
                "Evidence-only relationship attempted a Phase A drop."
            )
    elif (
        not isinstance(required_drop_count, int)
        or isinstance(required_drop_count, bool)
        or len(dropped_features)
        != required_drop_count
    ):
        raise RuntimeError(
            "Resolved relationship violates required_drop_count."
        )

    if set(dropped_features) & set(protected_features):
        raise RuntimeError(
            "Phase A attempted to drop a protected semantic basis feature."
        )

    if (
        set(retained_features)
        | set(dropped_features)
    ) != set(features):
        raise RuntimeError(
            "Resolved relationship does not cover all participating features."
        )

    feature_states: dict[str, str] = {}

    for feature in features:
        if feature in set(dropped_features):
            state = "SEMANTIC_DROPPED"
        elif feature in set(protected_features):
            state = "SEMANTIC_BASIS_PROTECTED"
        elif feature in set(unresolved_features):
            state = "EMPIRICAL_UNRESOLVED_UNTIL_PHASE_C"
        else:
            state = "SEMANTIC_RETAINED"

        feature_states[
            feature
        ] = state

    return {
        "check_id": entry[
            "check_id"
        ],
        "dependency_group": entry[
            "dependency_group"
        ],
        "check_type": entry[
            "check_type"
        ],
        "decision_effect": decision_effect,
        "required_drop_count": (
            required_drop_count
        ),
        "features": features,
        "retained_features": retained_features,
        "dropped_features": dropped_features,
        "unresolved_features": unresolved_features,
        "feature_states": feature_states,
        **extra_evidence,
    }


# STEP_14G3B3F5_PHASE0_ORCHESTRATOR

def _run_stage_b_phase_a(
    *,
    feature_frame,
    semantic_registry,
    phase0,
):
    """Run locked semantic checks on TRAIN rows in each fold only."""

    from . import contract as _contract

    if not isinstance(
        feature_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "feature_frame must be a pandas DataFrame."
        )

    if not isinstance(phase0, dict):
        raise TypeError(
            "phase0 must be a dict."
        )

    if not phase0.get(
        "phase0_boundary_valid",
        False,
    ):
        raise RuntimeError(
            "Stage B Phase A requires GREEN Phase 0."
        )

    if phase0.get(
        "final_test_rows_opened",
    ) != 0:
        raise RuntimeError(
            "Stage B Phase A Final Test firewall failed."
        )

    validate_semantic_registry(
        semantic_registry
    )

    protected_features = derive_protected_features(
        semantic_registry
    )
    (
        canonical_features,
        _,
        metadata_by_feature,
    ) = _phase_a_canonical_metadata(
        phase0=phase0
    )

    exact_check_types = {
        'EXACT_LINEAR_DERIVED_IDENTITY',
        'EXACT_NONLINEAR_DERIVED_REPRESENTATION',
        'EXACT_AFFINE_DERIVED_IDENTITY',
        'EXACT_AFFINE_DEPENDENCY',
        'PAIRED_NONLINEAR_REPRESENTATION',
    }

    semantic_results_by_fold = {}

    for fold_role_column in (
        _contract.FOLD_ROLE_COLUMNS
    ):
        train_mask = get_train_mask(
            feature_frame,
            fold_role_column,
        )

        train_frame = feature_frame.loc[
            train_mask
        ]

        fold_results = []

        for entry in semantic_registry[
            "semantic_checks"
        ]:
            implementation_key = entry["implementation_key"]

            implementation = globals().get(
                implementation_key
            )

            if not callable(implementation):
                raise RuntimeError(
                    "Stage B semantic implementation "
                    f"is unavailable: {implementation_key!r}"
                )

            result = implementation(
                train_frame,
                entry,
            )

            check_type = entry[
                "check_type"
            ]

            if check_type in exact_check_types:
                if result.get(
                    "identity_pass"
                ) is not True:
                    raise RuntimeError(
                        "Stage B Phase A exact semantic "
                        f"check failed: {entry['check_id']} "
                        f"in {fold_role_column}."
                    )
            elif check_type == 'EMPIRICAL_NEAR_IDENTITY':
                if (
                    result.get("automatic_decision")
                    is not None
                    or result.get("classification")
                    != "EMPIRICAL_EVIDENCE_ONLY"
                ):
                    raise RuntimeError(
                        "Stage B Phase A empirical check "
                        "attempted an automatic decision."
                    )
            else:
                raise RuntimeError(
                    "Stage B Phase A encountered an "
                    f"unsupported check type: {check_type!r}"
                )

            fold_results.append(result)

        semantic_results_by_fold[
            fold_role_column
        ] = tuple(fold_results)

    relationship_decisions = tuple(
        _resolve_phase_a_relationship(
            feature_frame=feature_frame,
            entry=entry,
            canonical_features=canonical_features,
            protected_features=protected_features,
            metadata_by_feature=metadata_by_feature,
            fold_role_columns=tuple(
                _contract.FOLD_ROLE_COLUMNS
            ),
        )
        for entry in semantic_registry[
            "semantic_checks"
        ]
    )
    dropped_feature_set = {
        feature
        for relationship in relationship_decisions
        for feature in relationship[
            "dropped_features"
        ]
    }
    dropped_features = tuple(
        feature
        for feature in canonical_features
        if feature in dropped_feature_set
    )
    retained_features = tuple(
        feature
        for feature in canonical_features
        if feature not in dropped_feature_set
    )

    if dropped_feature_set.difference(
        canonical_features
    ):
        raise RuntimeError(
            "Phase A resolved a non-canonical dropped feature."
        )

    if set(dropped_features) & set(protected_features):
        raise RuntimeError(
            "Phase A resolved a protected feature as dropped."
        )

    return {
        "phase_a_semantic_valid": True,
        "phase_a_exact_decisions_complete": True,
        "phase_a_retained_features": (
            retained_features
        ),
        "phase_a_dropped_features": (
            dropped_features
        ),
        "phase_a_relationship_decisions": (
            relationship_decisions
        ),
        "semantic_results_by_fold": (
            semantic_results_by_fold
        ),
        "protected_features": protected_features,
        "final_test_rows_opened": 0,
    }


def _run_stage_b_phase0(
    *,
    feature_frame,
    registry_frame,
    opened_fields,
    opened_cells,
    final_test_rows_opened,
    yearly_review_acknowledged,
):
    """
    Pure Stage B Phase-0 orchestration boundary.

    Locked execution order:

    Final Test firewall
    -> canonical registry validation
    -> forbidden-input validation
    -> TRAIN/full-29 coverage
    -> yearly concentration review
    -> missingness reconciliation
    -> dual zero-variance diagnostics per TRAIN fold.

    No artifact I/O, imputation, or row deletion occurs here.
    """

    from . import contract as _contract

    # --------------------------------------------------------
    # 1. FINAL TEST FIREWALL
    # --------------------------------------------------------

    if (
        not isinstance(
            final_test_rows_opened,
            int,
        )
        or isinstance(
            final_test_rows_opened,
            bool,
        )
        or final_test_rows_opened < 0
    ):
        raise ValueError(
            "final_test_rows_opened must be "
            "a non-negative int."
        )

    if final_test_rows_opened != 0:
        raise RuntimeError(
            "Stage B Phase 0 Final Test firewall failed: "
            f"{final_test_rows_opened} rows opened."
        )

    if not isinstance(
        feature_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "feature_frame must be a pandas DataFrame."
        )

    if not isinstance(
        registry_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "registry_frame must be a pandas DataFrame."
        )

    if not isinstance(
        opened_fields,
        (list, tuple, set),
    ):
        raise TypeError(
            "opened_fields must be a list/tuple/set."
        )

    if not isinstance(
        opened_cells,
        (list, tuple, set),
    ):
        raise TypeError(
            "opened_cells must be a list/tuple/set."
        )

    if not isinstance(
        yearly_review_acknowledged,
        bool,
    ):
        raise TypeError(
            "yearly_review_acknowledged must be bool."
        )

    opened_fields_list = list(
        opened_fields
    )

    opened_cells_list = list(
        opened_cells
    )

    # --------------------------------------------------------
    # 2. CANONICAL REGISTRY
    #
    # The frozen registry itself determines the canonical
    # candidate names/order. The existing validator remains
    # the sole implementation authority for the 29-feature
    # membership/order/lookback contract.
    # --------------------------------------------------------

    registry_rows = (
        registry_frame
        .to_dict(
            orient="records"
        )
    )

    if "feature" not in registry_frame.columns:
        raise RuntimeError(
            "Canonical registry lacks feature column."
        )

    registry_feature_order = (
        registry_frame[
            "feature"
        ]
        .astype(
            "string"
        )
        .tolist()
    )

    registry_feature_set = set(
        registry_feature_order
    )

    artifact_feature_order = [
        column
        for column in feature_frame.columns
        if column in registry_feature_set
    ]

    registry_validation = (
        _validate_canonical_feature_registry(
            registry_rows=registry_rows,
            artifact_feature_order=(
                artifact_feature_order
            ),
        )
    )

    canonical_features = list(
        registry_validation[
            "canonical_feature_order"
        ]
    )

    # --------------------------------------------------------
    # 3. FORBIDDEN INPUT FIREWALL
    # --------------------------------------------------------

    forbidden_input_validation = (
        _validate_forbidden_inputs(
            opened_fields=opened_fields_list,
            opened_cells=opened_cells_list,
            final_test_rows_opened=(
                final_test_rows_opened
            ),
        )
    )

    # --------------------------------------------------------
    # 4. COVERAGE
    #
    # Full Decision Universe denominators remain intact.
    # Incomplete TRAIN rows remain in coverage denominators.
    # --------------------------------------------------------

    coverage = _compute_stage_b_phase0_coverage(
        feature_frame=feature_frame,
        canonical_features=canonical_features,
        fold_role_columns=list(
            _contract.FOLD_ROLE_COLUMNS
        ),
    )

    coverage_validation = _validate_fold_coverage(
        fold_complete_rows=(
            coverage[
                "fold_complete_rows"
            ]
        ),
        fold_train_rows=(
            coverage[
                "fold_train_rows"
            ]
        ),
        yearly_coverage=(
            coverage[
                "yearly_coverage"
            ]
        ),
        yearly_review_acknowledged=(
            yearly_review_acknowledged
        ),
    )

    # --------------------------------------------------------
    # 5. MISSINGNESS RECONCILIATION
    #
    # These names are the frozen canonical Cell14 availability
    # components already established by the Stage B contract
    # evidence and existing reconciliation tests.
    # --------------------------------------------------------

    shared_240m_features = [
        'momentum_log_240m',
        'realized_vol_240m',
        'volume_ratio_prev_240m',
        'return_autocorr_lag1_240m',
        'sign_entropy_240m',
    ]

    session_to_date_feature = (
        'session_vwap_proxy_deviation'
    )

    status_column = (
        'feature_status'
    )

    missingness_reconciliation = (
        _reconcile_full29_missingness(
            frame=feature_frame,
            canonical_features=(
                canonical_features
            ),
            shared_240m_features=(
                shared_240m_features
            ),
            session_to_date_feature=(
                session_to_date_feature
            ),
            status_column=(
                status_column
            ),
        )
    )

    if not missingness_reconciliation[
        "component_reconciliation_valid"
    ]:
        raise RuntimeError(
            "Stage B Phase 0 missingness "
            "reconciliation is not valid."
        )

    # --------------------------------------------------------
    # 6. DUAL ZERO-VARIANCE DIAGNOSTICS
    #
    # compute_zero_variance_diagnostics reports BOTH:
    # - full TRAIN zero variance
    # - common complete-case TRAIN zero variance
    #
    # It is executed independently for the exact three locked
    # expanding TRAIN folds.
    # --------------------------------------------------------

    zero_variance_diagnostics = {}

    for fold_role_column in (
        _contract.FOLD_ROLE_COLUMNS
    ):
        zero_variance_diagnostics[
            fold_role_column
        ] = compute_zero_variance_diagnostics(
            feature_frame,
            fold_role_column,
            canonical_features,
        )

    if tuple(
        zero_variance_diagnostics
    ) != tuple(
        _contract.FOLD_ROLE_COLUMNS
    ):
        raise RuntimeError(
            "Stage B Phase 0 zero-variance fold "
            "coverage is not canonical."
        )

    # --------------------------------------------------------
    # 7. PHASE0 RESULT
    # --------------------------------------------------------

    return {
        "phase0_boundary_valid": True,
        "final_test_rows_opened": 0,
        "opened_cells": tuple(
            opened_cells_list
        ),
        "opened_fields": tuple(
            opened_fields_list
        ),
        "canonical_features": tuple(
            canonical_features
        ),
        "registry_validation": (
            registry_validation
        ),
        "forbidden_input_validation": (
            forbidden_input_validation
        ),
        "coverage": coverage,
        "coverage_validation": (
            coverage_validation
        ),
        "missingness_reconciliation": (
            missingness_reconciliation
        ),
        "zero_variance_diagnostics": (
            zero_variance_diagnostics
        ),
    }


# STEP_14G3B3F4_PHASE0_COVERAGE

def _compute_stage_b_phase0_coverage(
    *,
    feature_frame: pd.DataFrame,
    canonical_features: list[str],
    fold_role_columns: list[str],
) -> dict[str, object]:
    """
    Recompute locked Stage B Phase-0 coverage directly from
    canonical Cell 14 Development rows and their embedded
    Cell 8 walk-forward roles.

    Fold coverage is calculated separately within each
    TRAIN fold.

    Yearly concentration uses the union of decisions that
    belong to TRAIN in at least one locked fold. Each
    decision is counted once. Validation-only decisions are
    excluded, while incomplete TRAIN decisions remain in
    the denominator.
    """

    if not isinstance(
        feature_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "feature_frame must be a pandas DataFrame."
        )

    if not isinstance(
        canonical_features,
        list,
    ):
        raise TypeError(
            "canonical_features must be a list."
        )

    if not isinstance(
        fold_role_columns,
        list,
    ):
        raise TypeError(
            "fold_role_columns must be a list."
        )

    if not canonical_features:
        raise ValueError(
            "canonical_features cannot be empty."
        )

    if not fold_role_columns:
        raise ValueError(
            "fold_role_columns cannot be empty."
        )

    if len(
        canonical_features
    ) != len(
        set(
            canonical_features
        )
    ):
        raise ValueError(
            "canonical_features contains duplicates."
        )

    if len(
        fold_role_columns
    ) != len(
        set(
            fold_role_columns
        )
    ):
        raise ValueError(
            "fold_role_columns contains duplicates."
        )

    required_columns = [
        "decision_id",
        "decision_time",
        *fold_role_columns,
        *canonical_features,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column
        not in feature_frame.columns
    ]

    if missing_columns:
        raise RuntimeError(
            "Phase0 coverage input is missing "
            f"required columns: {missing_columns}"
        )

    decision_ids = feature_frame[
        "decision_id"
    ]

    if decision_ids.isna().any():
        raise RuntimeError(
            "Phase0 coverage input contains "
            "null decision_id."
        )

    if decision_ids.duplicated().any():
        raise RuntimeError(
            "Phase0 coverage input contains "
            "duplicate decision_id."
        )

    decision_times = pd.to_datetime(
        feature_frame[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    if decision_times.isna().any():
        raise RuntimeError(
            "Phase0 coverage input contains "
            "null decision_time."
        )

    if (
        feature_frame[
            fold_role_columns
        ]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Phase0 coverage input contains "
            "null fold-role values."
        )

    # --------------------------------------------------------
    # FULL-29 COMPLETENESS
    #
    # No imputation and no silent row deletion. A row is
    # complete only when every canonical feature is finite.
    # --------------------------------------------------------

    try:
        feature_values = (
            feature_frame[
                canonical_features
            ]
            .astype(
                "float64"
            )
            .to_numpy()
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            "Canonical feature matrix cannot be "
            "evaluated as float64."
        ) from exc

    complete_mask = np.isfinite(
        feature_values
    ).all(
        axis=1
    )

    # --------------------------------------------------------
    # PER-FOLD TRAIN COVERAGE
    # --------------------------------------------------------

    fold_train_rows = {}
    fold_complete_rows = {}
    fold_coverage = {}

    train_masks = []

    for fold in fold_role_columns:

        roles = (
            feature_frame[
                fold
            ]
            .astype(
                "string"
            )
        )

        train_mask = (
            roles.eq(
                "TRAIN"
            )
            .to_numpy(
                dtype=bool
            )
        )

        train_masks.append(
            train_mask
        )

        train_rows = int(
            train_mask.sum()
        )

        if train_rows <= 0:
            raise RuntimeError(
                f"{fold}: TRAIN row count "
                "must be positive."
            )

        complete_rows = int(
            (
                train_mask
                & complete_mask
            ).sum()
        )

        fold_train_rows[
            fold
        ] = train_rows

        fold_complete_rows[
            fold
        ] = complete_rows

        fold_coverage[
            fold
        ] = float(
            complete_rows
            / train_rows
        )

    # --------------------------------------------------------
    # YEARLY CONCENTRATION SCOPE
    #
    # Applicable TRAIN history = union of rows that are TRAIN
    # in at least one locked expanding fold.
    #
    # Each decision_id occurs once in feature_frame, therefore
    # overlapping expanding folds do not multiply observations.
    # --------------------------------------------------------

    applicable_train_mask = np.logical_or.reduce(
        train_masks
    )

    if not applicable_train_mask.any():
        raise RuntimeError(
            "No applicable TRAIN history is available "
            "for yearly concentration reporting."
        )

    train_years = (
        decision_times[
            applicable_train_mask
        ]
        .dt.year
        .to_numpy()
    )

    train_complete = complete_mask[
        applicable_train_mask
    ]

    yearly_train_rows = {}
    yearly_complete_rows = {}
    yearly_coverage = {}

    for year_value in sorted(
        set(
            int(year)
            for year in train_years
        )
    ):

        year_mask = (
            train_years
            == year_value
        )

        denominator = int(
            year_mask.sum()
        )

        numerator = int(
            (
                year_mask
                & train_complete
            ).sum()
        )

        if denominator <= 0:
            raise RuntimeError(
                f"{year_value}: yearly TRAIN "
                "denominator must be positive."
            )

        yearly_train_rows[
            year_value
        ] = denominator

        yearly_complete_rows[
            year_value
        ] = numerator

        yearly_coverage[
            year_value
        ] = float(
            numerator
            / denominator
        )

    return {
        "fold_train_rows": (
            fold_train_rows
        ),
        "fold_complete_rows": (
            fold_complete_rows
        ),
        "fold_coverage": (
            fold_coverage
        ),
        "yearly_train_rows": (
            yearly_train_rows
        ),
        "yearly_complete_rows": (
            yearly_complete_rows
        ),
        "yearly_coverage": (
            yearly_coverage
        ),
        "applicable_train_row_count": int(
            applicable_train_mask.sum()
        ),
        "full29_complete_applicable_train_row_count": int(
            (
                applicable_train_mask
                & complete_mask
            ).sum()
        ),
    }

# STEP_14G3B3F1_EMBEDDED_ROLE_PROJECTION

def _validate_stage_b_embedded_role_projection(
    *,
    feature_frame: pd.DataFrame,
    cell14_audit: dict[str, object],
    expected_cell8_assignments_sha256: str,
    fold_role_columns: list[str],
    final_test_start_year: int,
) -> dict[str, object]:
    """
    Validate that canonical Cell 14 Development rows carry
    the frozen Cell 8 walk-forward role projection without
    reopening the full Cell 8 assignment artifact.

    Cell 8 remains provenance-bound. Runtime fold authority
    comes from the embedded Development-only role columns
    already carried by canonical Cell 14.
    """

    if not isinstance(
        feature_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "feature_frame must be a pandas DataFrame."
        )

    if not isinstance(
        cell14_audit,
        dict,
    ):
        raise TypeError(
            "cell14_audit must be a dict."
        )

    if (
        not isinstance(
            expected_cell8_assignments_sha256,
            str,
        )
        or len(
            expected_cell8_assignments_sha256
        ) != 64
    ):
        raise ValueError(
            "expected_cell8_assignments_sha256 "
            "must be a 64-character SHA256 string."
        )

    if not isinstance(
        fold_role_columns,
        list,
    ):
        raise TypeError(
            "fold_role_columns must be a list."
        )

    if not fold_role_columns:
        raise ValueError(
            "fold_role_columns cannot be empty."
        )

    if (
        not isinstance(
            final_test_start_year,
            int,
        )
        or isinstance(
            final_test_start_year,
            bool,
        )
    ):
        raise TypeError(
            "final_test_start_year must be int."
        )

    required_columns = [
        "decision_id",
        "decision_time",
        "outer_partition",
        *fold_role_columns,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in feature_frame.columns
    ]

    if missing_columns:
        raise RuntimeError(
            "Cell14 feature artifact is missing "
            "embedded-role projection columns: "
            f"{missing_columns}"
        )

    decision_ids = feature_frame[
        "decision_id"
    ]

    if decision_ids.isna().any():
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null decision_id."
        )

    if decision_ids.duplicated().any():
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "duplicate decision_id."
        )

    if (
        feature_frame[
            fold_role_columns
        ]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null embedded fold-role assignments."
        )

    partitions = (
        feature_frame[
            "outer_partition"
        ]
        .astype(
            "string"
        )
    )

    allowed_partitions = {
        "TRAIN",
        "VALIDATION",
    }

    observed_partitions = set(
        partitions.dropna().tolist()
    )

    if not observed_partitions:
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "no Development partitions."
        )

    if not observed_partitions.issubset(
        allowed_partitions
    ):
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "non-Development outer_partition values: "
            f"{sorted(observed_partitions)}"
        )

    if partitions.isna().any():
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null outer_partition."
        )

    decision_times = pd.to_datetime(
        feature_frame[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    if decision_times.isna().any():
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null decision_time."
        )

    final_test_boundary = pd.Timestamp(
        year=final_test_start_year,
        month=1,
        day=1,
        tz="UTC",
    )

    final_test_row_count = int(
        decision_times.ge(
            final_test_boundary
        ).sum()
    )

    if final_test_row_count != 0:
        raise RuntimeError(
            "Cell14 embedded role projection crossed "
            "the Final Test boundary."
        )

    try:
        upstream_binding = cell14_audit[
            "upstream_binding"
        ]

        audit_cell8_sha256 = upstream_binding[
            "cell8_assignments_sha256"
        ]

        feature_contract = cell14_audit[
            "feature_contract"
        ]

        physical_reads = cell14_audit[
            "physical_development_reads"
        ][
            "cell8_assignments"
        ]

        audit_counts = cell14_audit[
            "counts"
        ]

    except (
        KeyError,
        TypeError,
    ) as exc:
        raise RuntimeError(
            "Cell14 audit is missing required "
            "embedded-role provenance evidence."
        ) from exc

    if (
        audit_cell8_sha256
        != expected_cell8_assignments_sha256
    ):
        raise RuntimeError(
            "Cell14 embedded roles are not bound "
            "to the expected frozen Cell8 "
            "assignment SHA256."
        )

    physical_filter = physical_reads.get(
        "physical_filter"
    )

    if not isinstance(
        physical_filter,
        dict,
    ):
        raise RuntimeError(
            "Cell14 audit lacks Cell8 physical "
            "Development filter evidence."
        )

    filter_partitions = physical_filter.get(
        "outer_partition_in"
    )

    if (
        not isinstance(
            filter_partitions,
            list,
        )
        or set(
            filter_partitions
        )
        != allowed_partitions
    ):
        raise RuntimeError(
            "Cell14 Cell8 physical read was not "
            "restricted to TRAIN/VALIDATION."
        )

    physical_partitions = physical_reads.get(
        "partitions"
    )

    if (
        not isinstance(
            physical_partitions,
            list,
        )
        or set(
            physical_partitions
        )
        != allowed_partitions
    ):
        raise RuntimeError(
            "Cell14 audit reports unexpected Cell8 "
            "Development partitions."
        )

    physical_row_count = physical_reads.get(
        "rows"
    )

    if (
        not isinstance(
            physical_row_count,
            int,
        )
        or isinstance(
            physical_row_count,
            bool,
        )
        or physical_row_count
        != len(
            feature_frame
        )
    ):
        raise RuntimeError(
            "Cell14 embedded-role row count does not "
            "match the physically filtered Cell8 "
            "Development read."
        )

    audit_development_rows = audit_counts.get(
        "development_rows"
    )

    if (
        not isinstance(
            audit_development_rows,
            int,
        )
        or isinstance(
            audit_development_rows,
            bool,
        )
        or audit_development_rows
        != len(
            feature_frame
        )
    ):
        raise RuntimeError(
            "Cell14 audit Development row count does "
            "not match the canonical feature artifact."
        )

    feature_contract_final_test_rows = (
        feature_contract.get(
            "final_test_feature_rows"
        )
    )

    audit_final_test_rows = audit_counts.get(
        "final_test_feature_rows"
    )

    if (
        feature_contract_final_test_rows != 0
        or audit_final_test_rows != 0
    ):
        raise RuntimeError(
            "Cell14 audit does not assert zero "
            "Final Test feature rows."
        )

    physical_max_raw = physical_reads.get(
        "decision_time_max_utc"
    )

    try:
        physical_max = pd.to_datetime(
            physical_max_raw,
            utc=True,
            errors="raise",
        )
    except Exception as exc:
        raise RuntimeError(
            "Cell14 audit contains invalid Cell8 "
            "Development maximum decision time."
        ) from exc

    if physical_max >= final_test_boundary:
        raise RuntimeError(
            "Cell14 audit Cell8 Development read "
            "crossed the Final Test boundary."
        )

    return {
        "embedded_role_projection_valid": True,
        "feature_row_count": int(
            len(
                feature_frame
            )
        ),
        "fold_role_columns": tuple(
            fold_role_columns
        ),
        "cell8_assignments_sha256": (
            expected_cell8_assignments_sha256
        ),
        "cell8_assignment_rows_opened": 0,
        "final_test_rows_opened": 0,
    }

# STEP_14G3B2_CANONICAL_DATA_OPEN_RECONCILIATION


def _validate_stage_b_canonical_data_reconciliation(
    *,
    feature_frame: pd.DataFrame,
    cell8_assignments: pd.DataFrame,
    fold_role_columns: list[str],
) -> dict[str, object]:
    """
    Reconcile canonical Cell 14 Development rows against
    canonical Cell 8 fold assignments by decision_id.

    Row position is not an identity mechanism.

    Both artifacts must contain one unique decision_id per
    row, identical decision-id membership, and exactly
    matching fold-role assignments after key alignment.
    """

    from . import contract as _contract

    if not isinstance(
        feature_frame,
        pd.DataFrame,
    ):
        raise TypeError(
            "feature_frame must be a pandas DataFrame."
        )

    if not isinstance(
        cell8_assignments,
        pd.DataFrame,
    ):
        raise TypeError(
            "cell8_assignments must be a pandas DataFrame."
        )

    if not isinstance(
        fold_role_columns,
        list,
    ):
        raise TypeError(
            "fold_role_columns must be a list."
        )

    if tuple(
        fold_role_columns
    ) != tuple(
        _contract.FOLD_ROLE_COLUMNS
    ):
        raise RuntimeError(
            "Stage B fold-role columns do not match "
            "the locked canonical fold mapping."
        )

    required_columns = [
        "decision_id",
        *fold_role_columns,
    ]

    feature_missing = [
        column
        for column in required_columns
        if column
        not in feature_frame.columns
    ]

    assignment_missing = [
        column
        for column in required_columns
        if column
        not in cell8_assignments.columns
    ]

    if feature_missing:
        raise RuntimeError(
            "Cell14 feature artifact is missing "
            f"reconciliation columns: {feature_missing}"
        )

    if assignment_missing:
        raise RuntimeError(
            "Cell8 assignment artifact is missing "
            f"reconciliation columns: {assignment_missing}"
        )

    feature_ids = (
        feature_frame[
            "decision_id"
        ]
    )

    assignment_ids = (
        cell8_assignments[
            "decision_id"
        ]
    )

    if feature_ids.isna().any():
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null decision_id."
        )

    if assignment_ids.isna().any():
        raise RuntimeError(
            "Cell8 assignment artifact contains "
            "null decision_id."
        )

    if feature_ids.duplicated().any():
        raise RuntimeError(
            "Duplicate decision_id in "
            "Cell14 feature artifact."
        )

    if assignment_ids.duplicated().any():
        raise RuntimeError(
            "Duplicate decision_id in "
            "Cell8 assignment artifact."
        )

    feature_index = pd.Index(
        feature_ids
    )

    assignment_index = pd.Index(
        assignment_ids
    )

    membership_exact = bool(
        feature_index.isin(
            assignment_index
        ).all()
        and assignment_index.isin(
            feature_index
        ).all()
        and len(feature_index)
        == len(assignment_index)
    )

    if not membership_exact:
        feature_only = tuple(
            feature_index[
                ~feature_index.isin(
                    assignment_index
                )
            ].tolist()
        )

        assignment_only = tuple(
            assignment_index[
                ~assignment_index.isin(
                    feature_index
                )
            ].tolist()
        )

        raise RuntimeError(
            "Cell14 and Cell8 decision_id membership "
            "does not reconcile one-to-one. "
            f"Cell14-only={feature_only}; "
            f"Cell8-only={assignment_only}"
        )

    order_exact = bool(
        feature_ids.tolist()
        == assignment_ids.tolist()
    )

    # Fold-role nulls are not valid evidence.
    if (
        feature_frame[
            fold_role_columns
        ]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Cell14 feature artifact contains "
            "null fold-role assignments."
        )

    if (
        cell8_assignments[
            fold_role_columns
        ]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Cell8 assignment artifact contains "
            "null fold-role assignments."
        )

    feature_roles = (
        feature_frame[
            [
                "decision_id",
                *fold_role_columns,
            ]
        ]
        .set_index(
            "decision_id",
            verify_integrity=True,
        )
        .loc[
            :,
            fold_role_columns,
        ]
        .astype(
            "string"
        )
    )

    assignment_roles = (
        cell8_assignments[
            [
                "decision_id",
                *fold_role_columns,
            ]
        ]
        .set_index(
            "decision_id",
            verify_integrity=True,
        )
        .reindex(
            feature_roles.index
        )
        .loc[
            :,
            fold_role_columns,
        ]
        .astype(
            "string"
        )
    )

    role_comparison = (
        feature_roles.eq(
            assignment_roles
        )
    )

    fold_role_exact = bool(
        role_comparison
        .all()
        .all()
    )

    if not fold_role_exact:
        mismatch_rows = (
            ~role_comparison
            .all(
                axis=1
            )
        )

        mismatch_ids = tuple(
            feature_roles.index[
                mismatch_rows
            ].tolist()
        )

        raise RuntimeError(
            "Cell14 and Cell8 fold-role assignments "
            "do not match by decision_id. "
            f"Mismatch decision_ids={mismatch_ids}"
        )

    return {
        "feature_row_count": int(
            len(
                feature_frame
            )
        ),
        "cell8_assignment_row_count": int(
            len(
                cell8_assignments
            )
        ),
        "decision_id_membership_exact": (
            membership_exact
        ),
        "decision_id_order_exact": (
            order_exact
        ),
        "fold_role_columns": tuple(
            fold_role_columns
        ),
        "fold_role_assignment_exact": (
            fold_role_exact
        ),
        "canonical_data_reconciliation_valid": True,
    }


def run_stage_b(
    *,
    project_root,
    output_dir,
    yearly_review_acknowledged,
    phase_c_rank_loss_review_acknowledged,
):
    """
    Sole Stage B V1.2 production artifact-reading boundary.

    Cell 8 assignments are provenance-bound only and are not
    physically opened by Stage B. Runtime fold authority comes
    from the canonical Cell 14 Development artifact's embedded
    walk-forward role projection.

    Phase 0 -> A executes, then production remains fail-closed before
    unimplemented Phase B. Issue #9 does not authorize later phases.
    """

    # --------------------------------------------------------
    # 1. ABSOLUTE FIRST ACTION: POLICY GATE
    # --------------------------------------------------------

    assert_stage_b_contract_locked(
        project_root=project_root,
    )

    # --------------------------------------------------------
    # 2. ARGUMENT NORMALIZATION AFTER GATE
    # --------------------------------------------------------

    from pathlib import Path
    import io
    import json

    from . import contract as _contract

    root = Path(
        project_root
    )

    destination = Path(
        output_dir
    )

    if not isinstance(
        yearly_review_acknowledged,
        bool,
    ):
        raise TypeError(
            "yearly_review_acknowledged must be bool."
        )

    if not isinstance(
        phase_c_rank_loss_review_acknowledged,
        bool,
    ):
        raise TypeError(
            "phase_c_rank_loss_review_acknowledged "
            "must be bool."
        )

    # --------------------------------------------------------
    # 3. CANONICAL CONTROL PATHS
    # --------------------------------------------------------

    release_manifest_path = (
        root
        / _contract.CELL14_RELEASE_MANIFEST_PATH
    )

    markdown_path = (
        root
        / _contract.MARKDOWN_CONTRACT_PATH
    )

    semantic_registry_path = (
        root
        / _contract.SEMANTIC_REGISTRY_PATH
    )

    # --------------------------------------------------------
    # 4. RELEASE-MANIFEST RAW HASH FIREWALL
    # --------------------------------------------------------

    release_manifest_bytes = (
        release_manifest_path.read_bytes()
    )

    actual_release_sha256 = (
        _sha256_bytes(
            release_manifest_bytes
        )
    )

    if (
        actual_release_sha256
        != _contract.CELL14_RELEASE_MANIFEST_SHA256
    ):
        raise RuntimeError(
            "Stage B release manifest SHA256 mismatch."
        )

    try:
        release_manifest = json.loads(
            release_manifest_bytes.decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Stage B release manifest could not "
            "be decoded as canonical JSON."
        ) from exc

    release_binding = (
        _validate_stage_b_release_manifest_binding(
            release_manifest=release_manifest,
        )
    )

    # --------------------------------------------------------
    # 5. MARKDOWN RAW HASH FIREWALL
    # --------------------------------------------------------

    markdown_bytes = (
        markdown_path.read_bytes()
    )

    actual_markdown_sha256 = (
        _sha256_bytes(
            markdown_bytes
        )
    )

    if (
        actual_markdown_sha256
        != _contract.MARKDOWN_CONTRACT_SHA256
    ):
        raise RuntimeError(
            "Stage B Markdown contract SHA256 mismatch."
        )

    # --------------------------------------------------------
    # 6. SEMANTIC REGISTRY RAW HASH FIREWALL
    # --------------------------------------------------------

    semantic_registry_bytes = (
        semantic_registry_path.read_bytes()
    )

    actual_semantic_sha256 = (
        _sha256_bytes(
            semantic_registry_bytes
        )
    )

    if (
        actual_semantic_sha256
        != _contract.SEMANTIC_REGISTRY_SHA256
    ):
        raise RuntimeError(
            "Stage B semantic registry SHA256 mismatch."
        )

    try:
        semantic_registry = json.loads(
            semantic_registry_bytes.decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Stage B semantic registry could not "
            "be decoded as canonical JSON."
        ) from exc

    # --------------------------------------------------------
    # 7. RUNTIME-READABLE VS PROVENANCE-ONLY ARTIFACTS
    # --------------------------------------------------------

    bindings = (
        release_binding[
            "artifact_bindings"
        ]
    )

    readable_ids = tuple(
        release_binding[
            "readable_artifact_ids"
        ]
    )

    provenance_only_ids = tuple(
        release_binding[
            "provenance_only_artifact_ids"
        ]
    )

    expected_readable_ids = (
        "cell14_features",
        "cell14_registry",
        "cell14_audit",
        "cell8_audit",
    )

    expected_provenance_only_ids = (
        "cell8_assignments",
    )

    if (
        readable_ids
        != expected_readable_ids
    ):
        raise RuntimeError(
            "Stage B canonical runtime-readable "
            "artifact set changed unexpectedly."
        )

    if (
        provenance_only_ids
        != expected_provenance_only_ids
    ):
        raise RuntimeError(
            "Stage B provenance-only artifact "
            "set changed unexpectedly."
        )

    root_resolved = (
        root.resolve()
    )

    artifact_paths = {}

    # Only runtime-readable artifacts are physically resolved.
    # Provenance-only Cell8 assignments are never opened here.
    for artifact_id in readable_ids:

        relative_path = (
            bindings[
                artifact_id
            ][
                "file"
            ]
        )

        candidate = (
            root
            / relative_path
        ).resolve()

        try:
            candidate.relative_to(
                root_resolved
            )
        except ValueError as exc:
            raise RuntimeError(
                "Canonical runtime artifact resolved "
                "outside project_root: "
                f"{artifact_id}"
            ) from exc

        artifact_paths[
            artifact_id
        ] = candidate

    # --------------------------------------------------------
    # 8. READ/HASH ONLY RUNTIME-READABLE ARTIFACTS
    #
    # Cell8 assignments remain provenance-bound but no bytes
    # or rows from that artifact are physically opened.
    # --------------------------------------------------------

    artifact_bytes = {}

    for artifact_id in readable_ids:

        raw = artifact_paths[
            artifact_id
        ].read_bytes()

        actual_sha256 = (
            _sha256_bytes(
                raw
            )
        )

        expected_sha256 = (
            bindings[
                artifact_id
            ][
                "sha256"
            ]
        )

        if (
            actual_sha256
            != expected_sha256
        ):
            raise RuntimeError(
                f"Stage B {artifact_id} "
                "SHA256 mismatch."
            )

        artifact_bytes[
            artifact_id
        ] = raw

    # --------------------------------------------------------
    # 9. PARSE ONLY ALREADY-HASHED RUNTIME BYTES
    # --------------------------------------------------------

    try:
        feature_frame = (
            pd.read_parquet(
                io.BytesIO(
                    artifact_bytes[
                        "cell14_features"
                    ]
                )
            )
        )
    except Exception as exc:
        raise RuntimeError(
            "Stage B could not parse canonical "
            "Cell14 feature Parquet bytes."
        ) from exc

    try:
        registry_frame = (
            pd.read_csv(
                io.BytesIO(
                    artifact_bytes[
                        "cell14_registry"
                    ]
                )
            )
        )
    except Exception as exc:
        raise RuntimeError(
            "Stage B could not parse canonical "
            "Cell14 registry CSV bytes."
        ) from exc

    try:
        cell14_audit = json.loads(
            artifact_bytes[
                "cell14_audit"
            ].decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Stage B could not parse canonical "
            "Cell14 audit JSON bytes."
        ) from exc

    try:
        cell8_audit = json.loads(
            artifact_bytes[
                "cell8_audit"
            ].decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Stage B could not parse canonical "
            "Cell8 audit JSON bytes."
        ) from exc

    # --------------------------------------------------------
    # 10. VALIDATE CELL14 EMBEDDED CELL8 ROLE PROJECTION
    #
    # No Cell8 assignment DataFrame is opened or reconciled.
    # --------------------------------------------------------

    embedded_role_projection = (
        _validate_stage_b_embedded_role_projection(
            feature_frame=feature_frame,
            cell14_audit=cell14_audit,
            expected_cell8_assignments_sha256=(
                bindings[
                    "cell8_assignments"
                ][
                    "sha256"
                ]
            ),
            fold_role_columns=list(
                _contract.FOLD_ROLE_COLUMNS
            ),
            final_test_start_year=(
                _contract.FINAL_TEST_START_YEAR
            ),
        )
    )

    # --------------------------------------------------------
    # 11. PHASE 0 ? DEVELOPMENT-ONLY FIREWALL / COVERAGE
    # --------------------------------------------------------

    opened_fields = tuple(
        feature_frame.columns
    )

    opened_cells = tuple(
        _contract.ALLOWED_INPUT_CELLS
    )

    phase0 = _run_stage_b_phase0(
        feature_frame=feature_frame,
        registry_frame=registry_frame,
        opened_fields=opened_fields,
        opened_cells=opened_cells,
        final_test_rows_opened=(
            embedded_role_projection[
                "final_test_rows_opened"
            ]
        ),
        yearly_review_acknowledged=(
            yearly_review_acknowledged
        ),
    )

    # --------------------------------------------------------
    # 12. PHASE A - TRAIN-ONLY SEMANTIC INTEGRATION
    # --------------------------------------------------------

    phase_a = _run_stage_b_phase_a(
        feature_frame=feature_frame,
        semantic_registry=semantic_registry,
        phase0=phase0,
    )

    # --------------------------------------------------------
    # 13. KEEP TARGET-INDEPENDENT PARSED INPUTS AVAILABLE
    # --------------------------------------------------------

    _ = (
        destination,
        markdown_bytes,
        semantic_registry,
        registry_frame,
        cell14_audit,
        cell8_audit,
        embedded_role_projection,
        phase0,
        phase_a,
        yearly_review_acknowledged,
        phase_c_rank_loss_review_acknowledged,
    )

    # --------------------------------------------------------
    # 14. FAIL CLOSED AFTER PHASE A
    # --------------------------------------------------------

    raise RuntimeError(
        "Stage B Phase B boundary is not yet "
        "implemented after Phase A validation."
    )








def assert_stage_b_contract_locked(
    *,
    project_root,
) -> None:
    """Fail closed unless the live constitutional controls agree."""

    import hashlib
    import json
    from pathlib import Path

    from . import contract as _contract

    if _contract.POLICY_STATUS != "LOCKED_EXECUTABLE":
        raise RuntimeError(
            "Stage B policy must be LOCKED_EXECUTABLE, got "
            f"{_contract.POLICY_STATUS!r}"
        )

    root = Path(project_root).resolve()

    markdown_bytes = (
        root
        / _contract.MARKDOWN_CONTRACT_PATH
    ).read_bytes()

    registry_bytes = (
        root
        / _contract.SEMANTIC_REGISTRY_PATH
    ).read_bytes()

    if (
        hashlib.sha256(markdown_bytes).hexdigest()
        != _contract.MARKDOWN_CONTRACT_SHA256
    ):
        raise RuntimeError(
            "Stage B Markdown contract SHA256 mismatch."
        )

    if (
        hashlib.sha256(registry_bytes).hexdigest()
        != _contract.SEMANTIC_REGISTRY_SHA256
    ):
        raise RuntimeError(
            "Stage B semantic registry SHA256 mismatch."
        )

    try:
        markdown = markdown_bytes.decode("utf-8")
        registry = json.loads(
            registry_bytes.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Stage B constitutional controls are not valid UTF-8/JSON."
        ) from exc

    expected_version_line = (
        f"Policy version: `{_contract.POLICY_VERSION}`"
    )

    if expected_version_line not in markdown:
        raise RuntimeError(
            "Stage B policy version mismatch."
        )

    if (
        "Policy status: **LOCKED_EXECUTABLE**"
        not in markdown
    ):
        raise RuntimeError(
            "Stage B Markdown policy status is not LOCKED_EXECUTABLE."
        )

    if (
        registry.get("registry_status")
        != "LOCKED_EXECUTABLE"
    ):
        raise RuntimeError(
            "Stage B semantic registry status is not LOCKED_EXECUTABLE."
        )

    if (
        registry.get("policy_version")
        != _contract.POLICY_VERSION
    ):
        raise RuntimeError(
            "Stage B semantic registry policy version mismatch."
        )

    if (
        registry.get("source_contract")
        != _contract.MARKDOWN_CONTRACT_PATH
    ):
        raise RuntimeError(
            "Stage B semantic registry source-contract mismatch."
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
    *,
    project_root,
) -> pd.DataFrame:
    """Run the locked Stage B redundancy analysis for one TRAIN fold."""

    assert_stage_b_contract_locked(
        project_root=project_root,
    )

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
    *,
    project_root,
) -> pd.DataFrame:
    """Run Stage B redundancy analysis across all locked TRAIN folds."""

    fold_results = []

    for fold_role_column in FOLD_ROLE_COLUMNS:
        fold_result = analyze_one_fold(
            df=df,
            fold_role_column=fold_role_column,
            feature_columns=feature_columns,
            project_root=project_root,
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

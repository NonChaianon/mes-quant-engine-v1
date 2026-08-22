from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from mes_quant.exploration.l1_lr001 import _standardize
from mes_quant.exploration.test2_evaluation import (
    CONSUMER_ORDER,
    INCONCLUSIVE_UNDERPOWERED,
    INTERESTING_ENOUGH_TO_CONTINUE,
    NOT_INTERESTING_ENOUGH,
    READY_FOR_SYNTHETIC_FIT,
    ConsumerRetainedIndex,
    FoldEvaluationData,
    ImprovementMetrics,
    decide_continuation,
    preflight_evaluation,
    run_authorized_train_evaluation,
    run_synthetic_evaluation,
    standardize_fold,
)
from mes_quant.exploration.test2_evaluation import (
    Test2EvaluationContractError as EvaluationError,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    L1_ACCESS_LEVEL,
    L1_HARNESS_STATUS,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
)
from mes_quant.exploration.test2_run_context import (
    VERIFIED_SOURCE_STATUS,
    CoverageEvidence,
    EvaluationRunContext,
    SourceIdentityEvidence,
)
from mes_quant.exploration.test2_stats import SupportGateResult
from mes_quant.exploration.test2_target import Disposition, PathTargetRow, PolicyAction
from mes_quant.features.contract import FEATURE_COLUMNS


def _fold(
    fold_id: str,
    *,
    holdout_rows: int = 1_000,
    design_pattern: bool = False,
    rows_per_session: int = 4,
) -> FoldEvaluationData:
    fold_year = 2022 if fold_id == "WF_2022" else 2023
    train_rows = 80
    train_ids = tuple(f"{fold_id}-T-{index:04d}" for index in range(train_rows))
    holdout_ids = tuple(f"{fold_id}-H-{index:04d}" for index in range(holdout_rows))
    train_start = datetime(fold_year - 2, 1, 3, 14, 30, tzinfo=UTC)
    holdout_start = datetime(fold_year, 1, 3, 14, 30, tzinfo=UTC)
    train_times = tuple(train_start + timedelta(minutes=15 * index) for index in range(train_rows))
    holdout_times = tuple(
        holdout_start
        + timedelta(
            days=index // rows_per_session,
            minutes=15 * (index % rows_per_session),
        )
        for index in range(holdout_rows)
    )
    if design_pattern:
        labels = np.asarray(([0, 0, 1, 1] * ((holdout_rows + 3) // 4))[:holdout_rows])
        gross = np.asarray(([0.0, 1.0, 0.0, 1.0] * ((holdout_rows + 3) // 4))[:holdout_rows])
    else:
        rng = np.random.default_rng(2022 if fold_id == "WF_2022" else 2023)
        labels = rng.integers(0, 2, size=holdout_rows)
        gross = rng.normal(size=holdout_rows)
    sessions = tuple(
        f"{fold_id}-S-{index // rows_per_session:04d}" for index in range(holdout_rows)
    )
    retained = ConsumerRetainedIndex(train_ids, holdout_ids)
    return FoldEvaluationData(
        fold_id=fold_id,
        train_features=np.zeros((train_rows, len(FEATURE_COLUMNS))),
        train_labels=np.arange(train_rows) % 2,
        train_row_ids=train_ids,
        train_decision_times=train_times,
        holdout_features=np.zeros((holdout_rows, len(FEATURE_COLUMNS))),
        holdout_labels=labels,
        holdout_gross_move_points_60m=gross,
        holdout_row_ids=holdout_ids,
        holdout_decision_times=holdout_times,
        holdout_session_ids=sessions,
        consumer_indices={consumer: retained for consumer in CONSUMER_ORDER},
    )


def _with_retained_targets(fold: FoldEvaluationData) -> FoldEvaluationData:
    targets = tuple(
        PathTargetRow(
            decision_identity=row_id,
            disposition=(
                Disposition.FAVORABLE_FIRST if int(label) == 1 else Disposition.NEITHER_TOUCH
            ),
            retained=True,
            policy_action=PolicyAction.SCORED,
            path_long=int(label),
            first_touch_offset_minutes=5 if int(label) == 1 else None,
            gross_move_points_60m=float(gross_move),
            no_score_reason=None,
            instrument_id="MES",
            entry_reference_ticks=20_000,
        )
        for row_id, label, gross_move in zip(
            fold.holdout_row_ids,
            fold.holdout_labels,
            fold.holdout_gross_move_points_60m,
            strict=True,
        )
    )
    return replace(fold, holdout_target_rows=targets)


def _real_run_context() -> EvaluationRunContext:
    return EvaluationRunContext(
        access_level=L1_ACCESS_LEVEL,
        harness_status=L1_HARNESS_STATUS,
        authorization_identity="OWNER_TEST2_L1",
        authorization_record_sha256="a" * 64,
        source_identity=SourceIdentityEvidence(
            raw_dbn_sha256=RAW_DBN_SHA256,
            decoded_mes_1m_sha256=DECODED_MES_1M_SHA256,
            feature_artifact_sha256=FEATURE_ARTIFACT_SHA256,
            ordered_feature_content_sha256=ORDERED_FEATURE_CONTENT_SHA256,
            evidence_status=VERIFIED_SOURCE_STATUS,
            content_sha256_evidence="SYNTHETIC_TEST_OF_REAL_RECORD_PATH",
            release_manifest_sha256="b" * 64,
        ),
        role_assignment_identity=CELL8_SPLIT_ASSIGNMENT_SHA256,
        request_set_sha256="c" * 64,
        real_train_target_path_rows_read=240_000,
        validation_rows_read=0,
        final_test_rows_read=0,
        feature_max_source_time_asserted=True,
        coverage=CoverageEvidence(4_000, 0, 0, 0, "ALL_OOF_ROWS", {}),
        economic_diagnostics={},
        is_synthetic=False,
        is_test_fixture=False,
        missing_path_bar_keys=7,
        native_instrument_mismatch_keys=3,
    )


def test_width_agnostic_standardizer_matches_test1_on_29_features() -> None:
    rng = np.random.default_rng(17)
    train = rng.normal(size=(30, len(FEATURE_COLUMNS)))
    holdout = rng.normal(size=(12, len(FEATURE_COLUMNS)))
    train[:, 7] = 4.0
    holdout[:, 7] = 5.0
    expected_train, expected_holdout, expected_zero = _standardize(train, holdout)
    actual = standardize_fold(train, holdout, feature_names=FEATURE_COLUMNS)
    assert actual.train == pytest.approx(expected_train)
    assert actual.holdout == pytest.approx(expected_holdout)
    assert actual.zero_variance_features == expected_zero == (FEATURE_COLUMNS[7],)


def test_standardizer_supports_pinned_width_four_and_rejects_nonfinite() -> None:
    names = ("a", "b", "c", "d")
    result = standardize_fold(np.ones((3, 4)), np.ones((2, 4)), feature_names=names)
    assert result.zero_variance_features == names
    broken = np.ones((3, 4))
    broken[0, 0] = np.nan
    with pytest.raises(EvaluationError, match="non-finite"):
        standardize_fold(broken, np.ones((2, 4)), feature_names=names)


@pytest.mark.parametrize("consumer_side", ["train", "holdout", "holdout_order"])
def test_retained_divergence_fails_closed_on_both_sides(consumer_side: str) -> None:
    first = _fold("WF_2022")
    second = _fold("WF_2023")
    consumers = dict(first.consumer_indices)
    original = consumers[CONSUMER_ORDER[-1]]
    if consumer_side == "train":
        changed = replace(original, train_row_ids=original.train_row_ids[:-1])
    elif consumer_side == "holdout":
        changed = replace(original, holdout_row_ids=original.holdout_row_ids[:-1])
    else:
        changed = replace(
            original,
            holdout_row_ids=(original.holdout_row_ids[1], original.holdout_row_ids[0], *original.holdout_row_ids[2:]),
        )
    consumers[CONSUMER_ORDER[-1]] = changed
    with pytest.raises(EvaluationError, match="retained rows diverged"):
        preflight_evaluation((replace(first, consumer_indices=consumers), second))


def test_fold_identity_order_and_disjoint_oof_are_sealed() -> None:
    first = _fold("WF_2022")
    second = _fold("WF_2023")
    with pytest.raises(EvaluationError, match="fold order"):
        preflight_evaluation((second, first))
    repeated = replace(second, holdout_row_ids=first.holdout_row_ids)
    repeated_index = ConsumerRetainedIndex(repeated.train_row_ids, repeated.holdout_row_ids)
    repeated = replace(
        repeated,
        consumer_indices={consumer: repeated_index for consumer in CONSUMER_ORDER},
    )
    with pytest.raises(EvaluationError, match="repeat across folds"):
        preflight_evaluation((first, repeated))


def test_boundary_gap_below_60_raises_and_valid_gap_is_recorded() -> None:
    first = _fold("WF_2022")
    second = _fold("WF_2023")
    holdout_start = min(first.holdout_decision_times)
    broken_times = (*first.train_decision_times[:-1], holdout_start - timedelta(minutes=59))
    with pytest.raises(EvaluationError, match="below 60"):
        preflight_evaluation((replace(first, train_decision_times=broken_times), second))
    result = preflight_evaluation((first, second))
    assert all(fold.boundary_gap_minutes >= 60.0 for fold in result.folds)


def test_preflight_recomputes_pooled_ess_and_returns_underpowered_before_fit() -> None:
    folds = (_fold("WF_2022", design_pattern=True), _fold("WF_2023", design_pattern=True))
    result = preflight_evaluation(folds)
    assert result.status == INCONCLUSIVE_UNDERPOWERED
    assert result.real_models_fitted == 0
    assert result.validation_rows_read == 0
    assert result.final_test_rows_read == 0
    assert result.folds[0].ess_support.path_long.design_effect == pytest.approx(2.0)
    assert result.folds[0].ess_support.gross_move_points_60m.design_effect == pytest.approx(3.0)
    assert result.pooled_ess_support.row_count == 2_000
    assert result.pooled_ess_support.governing_effective_sample_size == pytest.approx(2_000 / 3)
    assert not result.support_gate.passed


def test_ready_preflight_records_stable_retained_hashes() -> None:
    first = _fold("WF_2022", holdout_rows=2_000, rows_per_session=40)
    second = _fold("WF_2023", holdout_rows=2_000, rows_per_session=40)
    result = preflight_evaluation((first, second))
    repeated = preflight_evaluation((first, second))
    assert result.status == READY_FOR_SYNTHETIC_FIT
    assert result.pooled_retained_sha256 == repeated.pooled_retained_sha256
    assert len(result.pooled_retained_sha256) == 64
    assert all(len(fold.train_retained_sha256) == 64 for fold in result.folds)
    assert all(len(fold.holdout_retained_sha256) == 64 for fold in result.folds)


def test_bootstrap_session_floor_fails_closed_instead_of_shrinking_block() -> None:
    first = _fold("WF_2022", holdout_rows=76)
    second = _fold("WF_2023", holdout_rows=80)
    with pytest.raises(EvaluationError, match="at least 20 sessions"):
        preflight_evaluation((first, second))


def test_strict_continuation_gate_passes_only_when_every_component_exceeds_floor() -> None:
    passing = ImprovementMetrics(0.008, 0.009)
    support = SupportGateResult(passed=True, failures=())
    result = decide_continuation(
        {"WF_2022": passing, "WF_2023": passing},
        passing,
        lower_bound_vs_prior=0.001,
        lower_bound_vs_nuisance=0.001,
        support_gate=support,
        governance_gates_passed=True,
    )
    assert result.passed
    assert result.disposition == INTERESTING_ENOUGH_TO_CONTINUE


def test_gate_equality_single_fold_and_zero_bound_all_fail() -> None:
    support = SupportGateResult(passed=True, failures=())
    result = decide_continuation(
        {
            "WF_2022": ImprovementMetrics(0.0075, 0.02),
            "WF_2023": ImprovementMetrics(0.02, 0.02),
        },
        ImprovementMetrics(0.02, 0.02),
        lower_bound_vs_prior=0.0,
        lower_bound_vs_nuisance=0.01,
        support_gate=support,
        governance_gates_passed=True,
    )
    assert not result.passed
    assert result.disposition == NOT_INTERESTING_ENOUGH
    assert len(result.failures) == 2


def test_underpowered_evaluation_stops_before_any_fitter(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "mes_quant.exploration.test2_evaluation.fit_frozen_logistic",
        lambda *args: calls.append(args),
    )
    result = run_synthetic_evaluation(
        (_fold("WF_2022", design_pattern=True), _fold("WF_2023", design_pattern=True)),
        timestamp_utc=datetime(2026, 8, 23, tzinfo=UTC),
        code_identity="synthetic-code",
        governance_gates_passed=True,
    )
    assert result.preflight.status == INCONCLUSIVE_UNDERPOWERED
    assert result.synthetic_fitter_calls == 0
    assert len(result.experiment_records) == 1
    assert result.experiment_records[0]["fit_status"] == (
        "SKIPPED_INCONCLUSIVE_UNDERPOWERED"
    )
    assert result.experiment_records[0]["real_models_fitted"] == 0
    assert calls == []


def test_degenerate_prior_raises_before_any_fitter(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "mes_quant.exploration.test2_evaluation.fit_frozen_logistic",
        lambda *args: calls.append(args),
    )
    first = _fold("WF_2022", holdout_rows=2_000, rows_per_session=40)
    second = _fold("WF_2023", holdout_rows=2_000, rows_per_session=40)
    first = replace(first, train_labels=np.zeros(len(first.train_row_ids), dtype=int))
    with pytest.raises(EvaluationError, match="prior is degenerate"):
        run_synthetic_evaluation(
            (first, second),
            timestamp_utc=datetime(2026, 8, 23, tzinfo=UTC),
            code_identity="synthetic-code",
        )
    assert calls == []


def test_happy_path_uses_four_fold_fits_and_two_unique_records(monkeypatch) -> None:
    calls: list[int] = []

    def fake_fit(train, labels):
        calls.append(train.shape[1])
        return np.zeros(train.shape[1] + 1), {"iterations": 0}

    monkeypatch.setattr(
        "mes_quant.exploration.test2_evaluation.fit_frozen_logistic", fake_fit
    )
    result = run_synthetic_evaluation(
        (
            _fold("WF_2022", holdout_rows=2_000, rows_per_session=40),
            _fold("WF_2023", holdout_rows=2_000, rows_per_session=40),
        ),
        timestamp_utc=datetime(2026, 8, 23, tzinfo=UTC),
        code_identity="synthetic-code",
        governance_gates_passed=True,
    )
    assert calls == [4, 29, 4, 29]
    assert result.synthetic_fitter_calls == 4
    assert len(result.fold_runs) == 2
    assert [bootstrap.block_length for bootstrap in result.bootstraps] == [5, 1, 20]
    assert len(result.experiment_records) == 2
    assert len({record["EXPERIMENT_ID"] for record in result.experiment_records}) == 2
    assert result.experiment_records[0]["disposition"] == "BASELINE_NOT_ELIGIBLE"
    assert result.experiment_records[1]["disposition"] == result.decision.disposition
    assert all(record["validation_rows_read"] == 0 for record in result.experiment_records)
    assert all(record["final_test_rows_read"] == 0 for record in result.experiment_records)
    assert all(record["real_models_fitted"] == 0 for record in result.experiment_records)
    for record in result.experiment_records:
        assert record["timestamp_utc"] == "2026-08-23T00:00:00Z"
        assert record["primary_metric"] == "OOF_BINARY_LOG_LOSS"
        assert record["retained_set_sha256"] == result.preflight.pooled_retained_sha256
        assert set(record["fold_preflight"]) == {"WF_2022", "WF_2023"}
        assert record["pooled_ess_support"]["governing_ess"] >= 2_000
        assert record["mde_vs_prior"] == 0.0075
        assert record["mde_vs_nuisance"] == 0.0075
        assert [item["block_length_sessions"] for item in record["bootstrap"]] == [5, 1, 20]
        assert record["release_policy_id"] == "RELEASE_AT_FIRST_TOUCH"
        assert record["capacity_policy_id"] == "RESERVE_CAPACITY_TO_60M"
        assert record["identity_block"]["authorization_identity"] == (
            "L0_SYNTHETIC_ONLY_NO_L1_TOKEN"
        )
        assert record["fixed_parameters"]["l2_lambda"] == 0.001
        assert all(len(item["draw_identity_sha256"]) == 64 for item in record["bootstrap"])
        assert all(
            item["comparison_scope"] == "PATHFULL001_VS_PRIOR_AND_PATHNUISANCE001"
            for item in record["bootstrap"]
        )
        assert record["governance_gates_passed"] is True
        assert set(record["effective_events_per_non_intercept_coefficient"]) == {
            "WF_2022",
            "WF_2023",
        }
    nuisance_features = result.experiment_records[0]["features"]
    assert nuisance_features == (
        "realized_vol_60m",
        "realized_vol_120m",
        "realized_vol_240m",
        "bar_log_range_15m",
    )
    full_primary = result.experiment_records[1]["primary_results"]
    assert full_primary["scope"] == "PATHFULL001_CONTINUATION_GATE"
    for fold_id in ("WF_2022", "WF_2023"):
        fold_result = full_primary["folds"][fold_id]
        assert fold_result["improvement_vs_prior"] == pytest.approx(
            fold_result["prior_log_loss"] - fold_result["full_log_loss"]
        )
        assert fold_result["improvement_vs_nuisance"] == pytest.approx(
            fold_result["nuisance_log_loss"] - fold_result["full_log_loss"]
        )


def test_full_model_probabilities_drive_predeclared_economic_policies(monkeypatch) -> None:
    def fake_fit(train, labels):
        return np.zeros(train.shape[1] + 1), {"iterations": 0}

    monkeypatch.setattr(
        "mes_quant.exploration.test2_evaluation.fit_frozen_logistic", fake_fit
    )
    result = run_synthetic_evaluation(
        (
            _with_retained_targets(_fold("WF_2022", holdout_rows=2_000, rows_per_session=40)),
            _with_retained_targets(_fold("WF_2023", holdout_rows=2_000, rows_per_session=40)),
        ),
        timestamp_utc=datetime(2026, 8, 23, tzinfo=UTC),
        code_identity="synthetic-economic-diagnostic",
    )
    economic = result.experiment_records[1]["economic_diagnostics"]
    assert result.experiment_records[0]["economic_diagnostics"] == {
        "status": "NOT_COMPUTED_BASELINE_RECORD",
        "source_model_id": None,
    }
    assert economic["source_model_id"] == "PATHFULL001"
    assert economic["primary"]["policy_id"] == "RELEASE_AT_FIRST_TOUCH"
    assert economic["capacity_sensitivity"]["policy_id"] == "RESERVE_CAPACITY_TO_60M"
    assert economic["primary"]["executed_trades"] > 0


def test_authorized_train_entrypoint_records_two_models_and_four_fold_fits(monkeypatch) -> None:
    def fake_fit(train, labels):
        return np.zeros(train.shape[1] + 1), {"iterations": 0}

    monkeypatch.setattr(
        "mes_quant.exploration.test2_evaluation.fit_frozen_logistic", fake_fit
    )
    result = run_authorized_train_evaluation(
        (
            _with_retained_targets(_fold("WF_2022", holdout_rows=2_000, rows_per_session=40)),
            _with_retained_targets(_fold("WF_2023", holdout_rows=2_000, rows_per_session=40)),
        ),
        timestamp_utc=datetime(2026, 8, 23, tzinfo=UTC),
        code_identity="synthetic-test-of-real-entrypoint",
        run_context=_real_run_context(),
        governance_gates_passed=True,
    )
    for record in result.experiment_records:
        assert record["real_models_fitted"] == 2
        assert record["run_real_fold_fitter_calls"] == 4
        assert record["model_real_fold_fitter_calls"] == 2
        assert record["missing_path_bar_keys"] == 7
        assert record["native_instrument_mismatch_keys"] == 3

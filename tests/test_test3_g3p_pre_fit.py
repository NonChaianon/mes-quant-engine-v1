from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mes_quant.exploration import test3_g3p_pre_fit as g3p
from mes_quant.exploration.test2_request_set import ParentDecision, build_streaming_request_set
from mes_quant.exploration.test3_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    FailureReason,
    RowStatus,
)
from mes_quant.exploration.test3_design import PredictorStatusRow
from mes_quant.exploration.test3_target import TargetStatusRow


def _control(
    identity: str,
    timestamp: datetime,
    *,
    session_id: str = "2023-01-03",
    role_2022: str = "TRAIN",
    role_2023: str = "TRAIN",
) -> g3p.ControlRow:
    return g3p.ControlRow(
        identity,
        timestamp,
        session_id,
        "12345",
        role_2022,
        role_2023,
    )


def _bars(closes: tuple[float, ...]) -> tuple[g3p.ObservedBar, ...]:
    return tuple(
        g3p.ObservedBar(offset, close, close + 0.25, close - 0.25, close)
        for offset, close in enumerate(closes)
    )


def _flat_cell12(*, usable: bool = True) -> g3p.Cell12Expectation:
    return g3p.Cell12Expectation(
        entry=100.0,
        endpoint=100.0,
        path_status="USABLE" if usable else "PATH_INTEGRITY_FAILURE",
        path_usable=usable,
        path_1m_present=60 if usable else 59,
        path_instrument_changed=False,
        path_high=100.25 if usable else None,
        path_low=99.75 if usable else None,
        long_mfe=0.25 if usable else None,
        long_mae=0.25 if usable else None,
    )


def test_pipe_identity_is_preserved_and_cr_lf_fail_closed() -> None:
    assert g3p._identity("2023-01-03T15:00:00Z|instrument_id=12345") == (
        "2023-01-03T15:00:00Z|instrument_id=12345"
    )
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError):
        g3p._identity("bad\nidentity")
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError):
        g3p._identity("bad\ridentity")


def test_local_cell2_hash_contract_is_order_and_index_sensitive() -> None:
    index = pd.DatetimeIndex(
        [datetime(2023, 1, 3, 15, 0, tzinfo=UTC)],
        name="ts_event",
    )
    frame = pd.DataFrame(
        {
            "instrument_id": [12345],
            "close": [100.0],
            "low": [99.75],
            "high": [100.25],
            "open": [100.0],
        },
        index=index,
    )
    normalized = g3p._normalize_decoded_frame(frame)
    assert tuple(normalized.columns) == g3p.CELL2_HASH_COLUMNS
    first = g3p._decoded_content_sha256(normalized)
    changed = normalized.copy()
    changed.iloc[0, 3] = 100.25
    assert g3p._decoded_content_sha256(changed) != first


def test_target_uses_exact_sixty_post_decision_returns() -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    closes = tuple(100.0 * math.exp(0.001 * (index + 1)) for index in range(60))
    row = g3p._target_row(
        _control("id", timestamp),
        g3p.TargetReference(100.0, closes[-1]),
        _bars(closes),
    )
    assert row.status == RowStatus.TARGET_USABLE.value
    assert row.rv_fwd_60 == pytest.approx(60 * 0.001**2)
    assert row.log_rv_fwd_60 == pytest.approx(math.log(60 * 0.001**2))


def test_missing_path_is_unusable_and_zero_variance_is_terminal_code() -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    missing = g3p._target_row(
        _control("missing", timestamp),
        g3p.TargetReference(100.0, 100.0),
        _bars((100.0,) * 59),
    )
    zero = g3p._target_row(
        _control("zero", timestamp),
        g3p.TargetReference(100.0, 100.0),
        _bars((100.0,) * 60),
    )
    assert missing.status == RowStatus.TARGET_UNUSABLE.value
    assert zero.status == FailureReason.TARGET_ZERO_VARIANCE.value
    assert zero.rv_fwd_60 == 0.0


def test_endpoint_and_nonpositive_close_fail_closed() -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="ENDPOINT"):
        g3p._target_row(
            _control("id", timestamp),
            g3p.TargetReference(100.0, 101.0),
            _bars((100.0,) * 60),
        )
    closes = [100.0] * 60
    closes[12] = 0.0
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="NONPOSITIVE"):
        g3p._target_row(
            _control("id", timestamp),
            g3p.TargetReference(100.0, 100.0),
            _bars(tuple(closes)),
        )


def test_cell12_usable_reconciliation_is_exact_on_tick_grid() -> None:
    bars = tuple(g3p.ObservedBar(index, 100.0, 101.0, 99.0, 100.0) for index in range(60))
    expected = g3p.Cell12Expectation(
        100.0,
        100.0,
        "USABLE",
        True,
        60,
        False,
        101.0,
        99.0,
        1.0,
        1.0,
    )
    assert g3p._reconcile_cell12(g3p.TargetReference(100.0, 100.0), expected, bars) == (
        "EXACT_TICK_RECONCILIATION_PASS"
    )
    wrong = g3p.Cell12Expectation(
        100.0,
        100.0,
        "USABLE",
        True,
        60,
        False,
        101.25,
        99.0,
        1.0,
        1.0,
    )
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="RECONCILIATION"):
        g3p._reconcile_cell12(g3p.TargetReference(100.0, 100.0), wrong, bars)


def test_cell12_path_integrity_failure_requires_exact_incomplete_count() -> None:
    bars = tuple(g3p.ObservedBar(index, 100.0, 100.25, 99.75, 100.0) for index in range(60))
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="PRESENT_COUNT"):
        g3p._reconcile_cell12(
            g3p.TargetReference(100.0, 100.0),
            _flat_cell12(usable=False),
            bars,
        )
    assert g3p._reconcile_cell12(
        g3p.TargetReference(100.0, 100.0),
        _flat_cell12(usable=False),
        bars[:-1],
    ) == "EXACT_PATH_INTEGRITY_FAILURE_COUNT_RECONCILIATION_PASS"
    wrong_count = g3p.Cell12Expectation(
        100.0,
        100.0,
        "PATH_INTEGRITY_FAILURE",
        False,
        58,
        False,
        None,
        None,
        None,
        None,
    )
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="PRESENT_COUNT"):
        g3p._reconcile_cell12(
            g3p.TargetReference(100.0, 100.0),
            wrong_count,
            bars[:-1],
        )


def test_cell12_label_unusable_does_not_override_test3_target_contract() -> None:
    bars = tuple(g3p.ObservedBar(index, 100.0, 100.25, 99.75, 100.0) for index in range(60))
    expectation = g3p.Cell12Expectation(
        100.0,
        None,
        "LABEL_UNUSABLE",
        False,
        60,
        False,
        None,
        None,
        None,
        None,
    )
    assert g3p._reconcile_cell12(
        g3p.TargetReference(100.0, None),
        expectation,
        bars,
    ) == "LABEL_UNUSABLE_NOT_USED_AS_TEST3_PATH_ATTESTATION"
    target = g3p._target_row(
        _control("label-unusable", datetime(2023, 1, 3, 15, 0, tzinfo=UTC)),
        g3p.TargetReference(100.0, None),
        bars,
    )
    assert target.status == RowStatus.TARGET_UNUSABLE.value


def test_cell12_label_unusable_accepts_canonical_nullable_instrument_flag() -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    control = _control("label-null", timestamp)
    table = g3p.pa.table(
        {
            "decision_id": [control.identity],
            "decision_time": [timestamp],
            "nyse_session_date": [date(2023, 1, 3)],
            "instrument_id": [12345],
            "outer_partition": ["TRAIN"],
            "role_wf_2022": ["TRAIN"],
            "role_wf_2023": ["TRAIN"],
            "entry_reference_close": [100.0],
            "exit_reference_close_60m": [None],
            "path_status": ["LABEL_UNUSABLE"],
            "path_usable": [False],
            "path_1m_present": [None],
            "path_instrument_changed": [None],
            "path_high_60m": [None],
            "path_low_60m": [None],
            "long_mfe_points_60m": [None],
            "long_mae_points_60m": [None],
        }
    )
    expectation = g3p._cell12_expectations(table, (control,))[control.identity]
    assert expectation.path_status == "LABEL_UNUSABLE"
    assert expectation.path_instrument_changed is None


def test_provider_raises_on_instrument_mismatch_instead_of_dropping_bar() -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    sealed = build_streaming_request_set(
        (ParentDecision("id", timestamp, "TRAIN"),),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    index = pd.DatetimeIndex([timestamp], name="ts_event")
    frame = pd.DataFrame(
        {
            "open": [100.0],
            "high": [100.25],
            "low": [99.75],
            "close": [100.0],
            "instrument_id": [99999],
        },
        index=index,
    )
    provider = g3p.SealedFrameProvider(frame, sealed=sealed, instruments={"id": "12345"})
    key = g3p.RequestKey("id", 0, timestamp)
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError, match="INSTRUMENT"):
        provider.fetch_path_bar_batch((key,), request_set_sha256=sealed.request_set_sha256)


def test_target_builder_completes_zero_variance_ledger_across_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_time = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    controls = (
        _control("flat", first_time),
        _control("moving", first_time + timedelta(days=1), session_id="2023-01-04"),
    )
    sealed = build_streaming_request_set(
        tuple(ParentDecision(row.identity, row.timestamp, "TRAIN") for row in controls),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    closes = {
        "flat": (100.0,) * 60,
        "moving": (100.0,) * 59 + (100.25,),
    }

    class SyntheticProvider:
        rows_examined = 0
        missing_keys = 0
        instrument_mismatch_keys = 0

        def fetch_path_bar_batch(self, request_keys, *, request_set_sha256):
            assert request_set_sha256 == sealed.request_set_sha256
            self.rows_examined += len(request_keys)
            return {
                key: g3p.ObservedBar(
                    key.minute_offset,
                    closes[key.decision_identity][key.minute_offset],
                    closes[key.decision_identity][key.minute_offset] + 0.25,
                    closes[key.decision_identity][key.minute_offset] - 0.25,
                    closes[key.decision_identity][key.minute_offset],
                )
                for key in request_keys
            }

    references = {
        "flat": g3p.TargetReference(100.0, 100.0),
        "moving": g3p.TargetReference(100.0, 100.25),
    }
    expectations = {
        "flat": _flat_cell12(),
        "moving": g3p.Cell12Expectation(
            100.0,
            100.25,
            "USABLE",
            True,
            60,
            False,
            100.5,
            99.75,
            0.5,
            0.25,
        ),
    }
    monkeypatch.setattr(g3p, "G3P_BATCH_SIZE", 60)
    result = g3p._build_targets(
        sealed,
        controls,
        references,
        expectations,
        SyntheticProvider(),
    )
    assert len(result.rows) == 2
    assert result.status_counts[FailureReason.TARGET_ZERO_VARIANCE.value] == 1
    assert result.status_counts[RowStatus.TARGET_USABLE.value] == 1
    assert result.provider_rows_examined == 120
    assert result.usable_cell12_rows == 2


def test_fit_guard_blocks_fit_equivalents_and_leaves_rank_surface_available() -> None:
    matrix = np.asarray([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0]])
    with g3p.pre_fit_only_guard() as guard:
        assert np.linalg.matrix_rank(matrix) == 2
        assert np.linalg.svd(matrix, compute_uv=False).shape == (2,)
        with pytest.raises(g3p.Test3G3PBoundaryError, match="lstsq"):
            np.linalg.lstsq(matrix, np.ones(3), rcond=None)
        assert guard.blocked_fit_calls == 1
    beta, *_ = np.linalg.lstsq(matrix, np.ones(3), rcond=None)
    assert beta.shape == (2,)


def test_every_declared_guard_symbol_exists() -> None:
    for owner, name, _label in g3p._BLOCKED_SYMBOLS:
        assert hasattr(owner, name)


def test_request_and_target_space_witnesses_are_create_once(tmp_path: Path) -> None:
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    sealed = build_streaming_request_set(
        (ParentDecision("id", timestamp, "TRAIN"),),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    git_context = g3p.GitContext("a" * 40, "b" * 40, g3p.G3P_BRANCH, "a" * 40)
    authorization = g3p.ObservedAuthorization(tmp_path / "auth", "c" * 64)
    request = g3p._persist_request_set_witness(
        tmp_path,
        sealed=sealed,
        git_context=git_context,
        authorization=authorization,
    )
    target = g3p._consume_target_space(
        tmp_path,
        sealed=sealed,
        git_context=git_context,
        authorization_reservation_sha256=authorization.reservation_sha256,
        request_witness_sha256=request[1],
    )
    assert request[0].is_file() and target[0].is_file()
    with pytest.raises(g3p.Test3G3PBoundaryError, match="already consumed"):
        g3p._consume_target_space(
            tmp_path,
            sealed=sealed,
            git_context=git_context,
            authorization_reservation_sha256=authorization.reservation_sha256,
            request_witness_sha256=request[1],
        )


def test_authorization_reservation_is_bound_and_create_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = tmp_path / "authorization.md"
    document.write_text("synthetic authorization\n", encoding="utf-8")
    document_sha = hashlib.sha256(document.read_bytes()).hexdigest()
    monkeypatch.setattr(g3p, "G3P_AUTHORIZATION_DOCUMENT", "authorization.md")
    monkeypatch.setattr(g3p, "G3P_AUTHORIZATION_DOCUMENT_SHA256", document_sha)
    monkeypatch.setattr(g3p, "AUTHORIZATION_RESERVATION_PATH", "evidence/auth.json")
    git_context = g3p.GitContext("a" * 40, "b" * 40, g3p.G3P_BRANCH, "a" * 40)
    observed = g3p._consume_authorization(
        tmp_path,
        git_context=git_context,
        authorization_token=g3p.G3P_AUTHORIZATION_TOKEN,
    )
    payload = json.loads(observed.reservation_path.read_text(encoding="utf-8"))
    assert payload["execution_commit"] == git_context.commit
    assert payload["authorization_document_sha256"] == document_sha
    with pytest.raises(g3p.Test3G3PBoundaryError, match="already consumed"):
        g3p._consume_authorization(
            tmp_path,
            git_context=git_context,
            authorization_token=g3p.G3P_AUTHORIZATION_TOKEN,
        )


def test_git_context_requires_exact_origin_direct_child_and_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "c" * 40
    tree = "d" * 40

    def output(_root: Path, *arguments: str) -> str:
        responses = {
            ("rev-parse", "HEAD"): commit,
            ("rev-parse", "HEAD^{tree}"): tree,
            ("branch", "--show-current"): g3p.G3P_BRANCH,
            ("rev-list", "--parents", "-n", "1", commit): (
                f"{commit} {g3p.G3P_BASE_COMMIT}"
            ),
            ("rev-parse", f"{g3p.G3P_BASE_COMMIT}^{{tree}}"): g3p.G3P_BASE_TREE,
            ("diff", "--name-only", g3p.G3P_BASE_COMMIT, "HEAD"): "\n".join(
                sorted(g3p.G3P_ALLOWED_CHANGED_FILES)
            ),
            ("status", "--porcelain", "--untracked-files=no"): "",
            ("ls-files", "--", "src", "tests", "tools"): "",
            (
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                "src",
                "tests",
                "tools",
            ): "",
            (
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "--",
                "src",
                "tests",
                "tools",
            ): "",
            ("rev-parse", "@{upstream}"): commit,
            ("rev-parse", "--symbolic-full-name", "@{upstream}"): (
                f"refs/remotes/origin/{g3p.G3P_BRANCH}"
            ),
        }
        return responses[arguments]

    monkeypatch.setattr(g3p, "_git_output", output)
    assert g3p._git_context(tmp_path) == g3p.GitContext(
        commit,
        tree,
        g3p.G3P_BRANCH,
        commit,
    )

    original = output

    def forged_origin(root: Path, *arguments: str) -> str:
        if arguments == ("rev-parse", "--symbolic-full-name", "@{upstream}"):
            return "refs/remotes/fork/research/test3-g3p-pre-fit-v1"
        return original(root, *arguments)

    monkeypatch.setattr(g3p, "_git_output", forged_origin)
    with pytest.raises(g3p.Test3G3PBoundaryError, match="upstream must be exactly"):
        g3p._git_context(tmp_path)


def test_failure_state_distinguishes_before_and_after_target_consumption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g3p, "EXPECTED_OUTER_TRAIN_ROWS", 1)
    git_context = g3p.GitContext("a" * 40, "b" * 40, g3p.G3P_BRANCH, "a" * 40)

    def reserve(root: Path) -> g3p.ObservedAuthorization:
        path = root / g3p.AUTHORIZATION_RESERVATION_PATH
        digest = g3p._atomic_create_json(
            path,
            {
                "authorization_id": g3p.G3P_AUTHORIZATION_ID,
                "authorization_document_sha256": g3p.G3P_AUTHORIZATION_DOCUMENT_SHA256,
                "authorization_token_sha256": hashlib.sha256(
                    g3p.G3P_AUTHORIZATION_TOKEN.encode("utf-8")
                ).hexdigest(),
                "base_commit": g3p.G3P_BASE_COMMIT,
                "execution_commit": git_context.commit,
                "execution_tree": git_context.tree,
                "branch": g3p.G3P_BRANCH,
                "g2p_evidence_commit": g3p.G2P_EVIDENCE_COMMIT,
                "status": "CONSUMED_BEFORE_ANY_SOURCE_ARTIFACT_ACCESS",
                "consumed_utc": "2026-08-25T00:00:00Z",
                "retry_authorized": False,
                "merge_authorized": False,
            },
        )
        return g3p.ObservedAuthorization(path, digest)

    reserve(tmp_path)
    before = g3p.write_failure_summary_if_reserved(
        project_root=tmp_path,
        error=g3p.Test3G3PInvalidEvidenceError("SYNTHETIC"),
    )
    assert before is not None
    payload = json.loads(before.read_text(encoding="utf-8"))
    assert payload["target_space_state"] == "LOCKED / RESERVED"
    assert payload["retry_authorized"] is False

    second_root = tmp_path / "second"
    authorization = reserve(second_root)
    timestamp = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    sealed = build_streaming_request_set(
        (ParentDecision("id", timestamp, "TRAIN"),),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    request = g3p._persist_request_set_witness(
        second_root,
        sealed=sealed,
        git_context=git_context,
        authorization=authorization,
    )
    g3p._consume_target_space(
        second_root,
        sealed=sealed,
        git_context=git_context,
        authorization_reservation_sha256=authorization.reservation_sha256,
        request_witness_sha256=request[1],
    )
    after = g3p.write_failure_summary_if_reserved(
        project_root=second_root,
        error=RuntimeError("synthetic"),
    )
    assert after is not None
    payload = json.loads(after.read_text(encoding="utf-8"))
    assert payload["target_space_state"] == "CONSUMED"
    assert payload["terminal_disposition"] == "EXECUTION_FAILURE"
    assert payload["validation_status"] == "ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED"
    assert payload["test3_status"] == "TERMINAL_NO_RETRY"


def test_forged_failure_witness_chain_is_not_attested(tmp_path: Path) -> None:
    g3p._atomic_create_json(
        tmp_path / g3p.AUTHORIZATION_RESERVATION_PATH,
        {"status": "forged"},
    )
    g3p._atomic_create_json(
        tmp_path / g3p.TARGET_SPACE_WITNESS_PATH,
        {"status": "forged"},
    )
    output = g3p.write_failure_summary_if_reserved(
        project_root=tmp_path,
        error=RuntimeError("synthetic"),
    )
    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["witness_chain_integrity"].startswith("NOT_ATTESTED")
    assert payload["target_space_state"] == "CONSUMED_OR_NOT_ATTESTED_FAIL_CLOSED"
    assert payload["target_space_consumption_witness_present"] is False
    assert "BEFORE_TARGET_ACCESS" not in payload["status"]
    assert "NOT_ATTESTED" in payload["status"]


def _support_fixture(*, duplicate_session: bool = False):
    controls: list[g3p.ControlRow] = []
    predictor_rows: list[PredictorStatusRow] = []
    target_rows: list[TargetStatusRow] = []
    values: dict[str, tuple[float, float, float]] = {}
    calendar: dict[str, tuple[float, float, bool]] = {}
    variances: dict[str, float] = {}

    specs: list[tuple[date, str, str]] = []
    specs.extend((date(2020, 1, 2) + timedelta(days=index), "TRAIN", "TRAIN") for index in range(12))
    specs.extend(
        (date(2022, 1, 3) + timedelta(days=index), "VALIDATION", "TRAIN")
        for index in range(20)
    )
    specs.extend(
        (date(2023, 1, 3) + timedelta(days=index), "UNUSED", "VALIDATION")
        for index in range(20)
    )
    for index, (session_date, role_2022, role_2023) in enumerate(specs):
        slot = index % 10
        market_open = datetime.combine(session_date, datetime.min.time(), tzinfo=UTC) + timedelta(
            hours=14, minutes=30
        )
        timestamp = market_open + timedelta(minutes=15 * (slot + 1))
        identity = f"id-{index}|instrument_id=12345"
        session_id = session_date.isoformat()
        if duplicate_session and role_2022 == "VALIDATION" and index == 31:
            session_id = controls[-1].session_id
        controls.append(
            _control(
                identity,
                timestamp,
                session_id=session_id,
                role_2022=role_2022,
                role_2023=role_2023,
            )
        )
        predictor_rows.append(
            PredictorStatusRow(identity, timestamp, RowStatus.PREDICTOR_USABLE.value)
        )
        variance = 0.01 + index * 0.0001
        target_rows.append(
            TargetStatusRow(
                identity,
                timestamp,
                timestamp + timedelta(minutes=60),
                RowStatus.TARGET_USABLE.value,
                variance,
                math.log(variance),
            )
        )
        values[identity] = (
            1.0 + index * 0.017,
            1.2 + (index % 7) * 0.11 + index * 0.003,
            1.5 + (index % 5) * 0.13 + index * index * 0.0002,
        )
        minutes_since = float(15 * (slot + 1))
        calendar[identity] = (minutes_since, 330.0 - minutes_since, False)
        variances[identity] = variance
    predictor = g3p.PredictorData(
        tuple(predictor_rows),
        values,
        calendar,
        {
            RowStatus.PREDICTOR_USABLE.value: len(controls),
            RowStatus.PREDICTOR_UNUSABLE.value: 0,
            FailureReason.PREDICTOR_NONFINITE.value: 0,
            FailureReason.PREDICTOR_NONPOSITIVE.value: 0,
        },
        "a" * 64,
        "b" * 64,
    )
    targets = g3p.TargetBuildResult(
        tuple(target_rows),
        variances,
        {
            RowStatus.TARGET_USABLE.value: len(controls),
            RowStatus.TARGET_UNUSABLE.value: 0,
            FailureReason.TARGET_ZERO_VARIANCE.value: 0,
        },
        "c" * 64,
        len(controls),
        0,
        len(controls) * 60,
        0,
        0,
    )
    return tuple(controls), predictor, targets


def test_support_gate_uses_frozen_folds_rank_harmonic_and_dependence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g3p, "FROZEN_HOLDOUT_COUNTS", {"WF_2022": 20, "WF_2023": 20})
    controls, predictor, targets = _support_fixture()
    harmonics, pre_target = g3p._pre_target_support_contract(controls, predictor)
    assert pre_target["status"] == "PASS_BEFORE_TARGET_SPACE_CONSUMPTION"
    evidence, disposition, g3f_status = g3p._support_evidence(
        controls,
        predictor,
        targets,
        harmonics,
    )
    assert evidence["support_gate_status"] == "G3P_SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED"
    assert disposition == "DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION"
    assert g3f_status == "NOT_AUTHORIZED_OWNER_DECISION_REQUIRED"
    assert set(evidence["folds"]) == {"WF_2022", "WF_2023"}
    assert evidence["pooled_disjoint_oof_dependence"]["row_count"] == 40
    for fold in evidence["folds"].values():
        assert fold["holdout_session_count"] == 20
        assert all(model["full_rank"] for model in fold["models"].values())


def test_nineteen_holdout_sessions_is_underpowered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g3p, "FROZEN_HOLDOUT_COUNTS", {"WF_2022": 20, "WF_2023": 20})
    controls, predictor, targets = _support_fixture(duplicate_session=True)
    harmonics, _pre_target = g3p._pre_target_support_contract(controls, predictor)
    evidence, disposition, g3f_status = g3p._support_evidence(
        controls,
        predictor,
        targets,
        harmonics,
    )
    assert disposition == "UNDERPOWERED_STOP"
    assert g3f_status == "TERMINAL"
    assert "WF_2022:HOLDOUT_SESSIONS_LT_20" in evidence["structural_failures"]


def test_frozen_holdout_counts_and_early_close_harmonic_are_pre_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert dict(g3p.FROZEN_HOLDOUT_COUNTS) == {"WF_2022": 5_510, "WF_2023": 5_476}
    timestamp = datetime(2023, 11, 24, 17, 0, tzinfo=UTC)
    control = _control(
        "early|instrument_id=12345",
        timestamp,
        session_id="2023-11-24",
        role_2022="VALIDATION",
    )
    predictor = g3p.PredictorData(
        (PredictorStatusRow(control.identity, timestamp, RowStatus.PREDICTOR_USABLE.value),),
        {control.identity: (1.0, 1.1, 1.2)},
        {control.identity: (150.0, 0.0, True)},
        {RowStatus.PREDICTOR_USABLE.value: 1},
        "a" * 64,
        "b" * 64,
    )
    monkeypatch.setattr(g3p, "FROZEN_HOLDOUT_COUNTS", {"WF_2022": 1, "WF_2023": 0})
    harmonics, evidence = g3p._pre_target_support_contract((control,), predictor)
    assert harmonics[control.identity].n_slots == 10
    assert evidence["harmonic_n_slots_all_outer_train"] == {"10": 1}


def test_synthetic_assembled_record_is_schema_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(g3p, "FROZEN_HOLDOUT_COUNTS", {"WF_2022": 20, "WF_2023": 20})
    controls, predictor, targets = _support_fixture()
    monkeypatch.setattr(g3p, "EXPECTED_OUTER_TRAIN_ROWS", len(controls))
    harmonics, pre_target = g3p._pre_target_support_contract(controls, predictor)
    sealed = build_streaming_request_set(
        tuple(ParentDecision(row.identity, row.timestamp, "TRAIN") for row in controls),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    documents = {
        path: {"expected": sha, "observed": sha, "size_bytes": 1, "match": True}
        for path, sha in g3p._DOCUMENT_BINDINGS.items()
    }
    g2p_binding = {
        "evidence_commit": "1" * 40,
        "execution_commit": "2" * 40,
        "execution_tree": "3" * 40,
        "record_path": "${REPOSITORY}/record.json",
        "record_file_sha256": "4" * 64,
        "record_semantic_sha256": "5" * 64,
        "reservation_path": "${REPOSITORY}/reservation.json",
        "reservation_sha256": "6" * 64,
        "predictor_status_ledger": {
            "hash_projection_id": "SYNTHETIC",
            "hash_serialization": "SYNTHETIC",
            "ordered_identity_sha256": predictor.ordered_identity_sha256,
            "ordered_identity_status_sha256": predictor.ordered_identity_status_sha256,
            "per_row_identities_persisted": False,
            "raw_predictor_values_persisted": False,
            "row_count": len(controls),
            "status_counts": dict(predictor.status_counts),
        },
        "outer_train_control_binding_sha256": "7" * 64,
        "binding_status": "SYNTHETIC",
    }
    artifact_binding = {
        "filename": "synthetic",
        "byte_sha256": "8" * 64,
        "size_bytes": 1,
        "schema_names": [],
        "total_rows": 1,
        "row_groups": 1,
        "numeric_rows_read_during_preflight": 0,
    }
    source_bindings = {
        **{
            artifact_id: dict(artifact_binding)
            for artifact_id in ("raw_dbn", "cell8", "cell10", "cell12", "cell14")
        },
        "pre_target_support_contract": dict(pre_target),
    }
    runtime_binding = {
        "python_executable": "${REPOSITORY}/.venv/bin/python",
        "python_isolated": True,
        "python_safe_path": True,
        "dependency_versions": {
            "numpy": "2.0.2",
            "pandas": "2.2.2",
            "pyarrow": "18.1.0",
            "databento": "0.83.0",
            "databento-dbn": "0.65.0",
        },
        "repository_module_origins_verified": ["g3p"],
        "site_package_origins_verified": ["numpy"],
    }
    record = g3p._assemble_record_with_controls(
        controls=controls,
        git_context=g3p.GitContext("a" * 40, "b" * 40, g3p.G3P_BRANCH, "a" * 40),
        authorization=g3p.ObservedAuthorization(tmp_path / "auth", "c" * 64),
        documents=documents,
        g2p_binding=g2p_binding,
        source_bindings=source_bindings,
        runtime_binding=runtime_binding,
        sealed=sealed,
        request_witness=(tmp_path / "request", "d" * 64),
        target_witness=(tmp_path / "target", "e" * 64),
        decoded_evidence=g3p.DecodedIdentityEvidence(
            "f" * 64,
            100,
            "2019-01-01T00:00:00+00:00",
            "2026-07-31T00:00:00+00:00",
            ("databento",),
        ),
        predictor=predictor,
        targets=targets,
        guard=g3p._MutableFitGuard(),
        harmonic_by_identity=harmonics,
    )
    assert frozenset(record) == g3p._RECORD_TOP_LEVEL_KEYS
    assert record["safety_counters"]["outer_train_target_rows_read"] == len(controls)
    g3p._assert_closed_record(record)
    with pytest.raises(g3p.Test3G3PBoundaryError, match="top-level schema"):
        g3p._assert_closed_record({**record, "raw_rows": [1.0]})


def test_closed_record_rejects_raw_target_or_identity_keys() -> None:
    base = {
        "safety_counters": {
            "outer_validation_target_rows_read": 0,
            "final_test_target_rows_read": 0,
            "real_fold_fit_calls": 0,
            "real_models_fitted": 0,
            "real_coefficients_computed": 0,
            "real_forecasts_computed": 0,
            "qlike_evaluations": 0,
            "duan_factors_computed": 0,
            "real_bootstrap_replicates": 0,
            "economic_diagnostic_calls": 0,
            "blocked_fit_calls": 0,
            "outer_validation_predictor_rows_read": 0,
            "final_test_predictor_rows_read": 0,
        }
    }
    g3p._assert_closed_record(base)
    with pytest.raises(g3p.Test3G3PBoundaryError, match="forbidden"):
        g3p._assert_closed_record({**base, "nested": {"rv_fwd_60": [1.0]}})
    with pytest.raises(g3p.Test3G3PBoundaryError, match="forbidden"):
        g3p._assert_closed_record({**base, "nested": {"decision_identity": "secret"}})


def test_atomic_record_write_and_semantic_hash_are_create_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(g3p, "_assert_success_record_schema", lambda _record: None)
    counters = {
        "outer_validation_target_rows_read": 0,
        "final_test_target_rows_read": 0,
        "real_fold_fit_calls": 0,
        "real_models_fitted": 0,
        "real_coefficients_computed": 0,
        "real_forecasts_computed": 0,
        "qlike_evaluations": 0,
        "duan_factors_computed": 0,
        "real_bootstrap_replicates": 0,
        "economic_diagnostic_calls": 0,
        "blocked_fit_calls": 0,
        "outer_validation_predictor_rows_read": 0,
        "final_test_predictor_rows_read": 0,
    }
    record = {key: None for key in g3p._RECORD_TOP_LEVEL_KEYS - {"record_sha256"}}
    record.update(
        {
            "gate_id": g3p.G3P_GATE_ID,
            "run_id": "MES_T3_G3P_" + "A" * 16,
            "safety_counters": counters,
        }
    )
    record["record_sha256"] = g3p._record_sha256(record)
    output = g3p.write_g3p_record(record, output_root=tmp_path)
    assert output.is_file()
    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed["record_sha256"] == g3p._record_sha256(parsed)
    with pytest.raises(FileExistsError):
        g3p.write_g3p_record(record, output_root=tmp_path)


def test_sha256_helpers_do_not_confuse_file_hash_and_semantic_hash(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    payload = {"a": 1, "b": [2, 3]}
    g3p._atomic_create_json(path, payload)
    file_sha, _size = g3p._hash_file(path)
    assert file_sha == hashlib.sha256(path.read_bytes()).hexdigest()
    assert file_sha != g3p._record_sha256(payload)

from __future__ import annotations

import ast
import functools
import hashlib
import inspect
import json
import math
import sys
import textwrap
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

_V19_PACKAGE_PARTS = ("mes_quant", "exploration")


def _prepend_v19_source_path() -> None:
    """Select this worktree's ``src`` tree before importing ``mes_quant``.

    The V19 consumer repair exists only in this worktree, so an editable install that points at
    another checkout must not win. This module therefore selects its own candidate source
    independently of collection order, using the standard library only and no hard-coded Git
    identity.
    """

    candidate = Path(__file__).resolve().parents[1] / "src"
    if not (candidate / "mes_quant" / "__init__.py").is_file():
        return

    entry = str(candidate)
    sys.path[:] = [item for item in sys.path if item != entry]
    sys.path.insert(0, entry)

    # If an ancestor package was already imported from another source tree, extend only that
    # package's search path; no sys.modules entry is removed.
    for depth in range(1, len(_V19_PACKAGE_PARTS) + 1):
        module = sys.modules.get(".".join(_V19_PACKAGE_PARTS[:depth]))
        search_path = getattr(module, "__path__", None)
        package_directory = candidate.joinpath(*_V19_PACKAGE_PARTS[:depth])
        if not isinstance(search_path, list) or not package_directory.is_dir():
            continue
        location = str(package_directory)
        if location not in search_path:
            search_path.insert(0, location)


_prepend_v19_source_path()

from mes_quant.exploration import test3_g3f_one_shot as g3f
from mes_quant.exploration import test3_g3p_pre_fit as g3p
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    build_streaming_request_set,
)
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


def _cell14_calendar_table(early_close: pa.Array) -> pa.Table:
    """Minimal Cell14-like projection carrying only the columns `_predictor_data` reads."""

    rows = len(early_close)
    return pa.table(
        {
            "realized_vol_60m": pa.array([0.5] * rows, type=pa.float64()),
            "realized_vol_120m": pa.array([0.6] * rows, type=pa.float64()),
            "realized_vol_240m": pa.array([0.7] * rows, type=pa.float64()),
            "minutes_since_nyse_open": pa.array([30.0] * rows, type=pa.float64()),
            "minutes_to_horizon_safe_close": pa.array([120.0] * rows, type=pa.float64()),
            "early_close_session": early_close,
        }
    )


def _usable_predictor_ledger(controls: tuple[g3p.ControlRow, ...]) -> dict[str, object]:
    """Recompute the expected G2-P predictor ledger for all-usable synthetic rows."""

    status = RowStatus.PREDICTOR_USABLE.value
    identity_payload = "".join(
        f"{control.identity}|{control.timestamp.isoformat()}\n" for control in controls
    ).encode("utf-8")
    status_payload = "".join(
        f"{control.identity}|{control.timestamp.isoformat()}|{status}\n"
        for control in controls
    ).encode("utf-8")
    counts = {entry: 0 for entry in g3p._STATUS_ORDER}
    counts[status] = len(controls)
    return {
        "row_count": len(controls),
        "status_counts": counts,
        "ordered_identity_sha256": hashlib.sha256(identity_payload).hexdigest(),
        "ordered_identity_status_sha256": hashlib.sha256(status_payload).hexdigest(),
    }


def test_predictor_data_accepts_producer_int8_flags_and_preserves_failure_category() -> None:
    base = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    two_controls = (
        _control("2023-01-03T15:00:00Z|instrument_id=12345", base),
        _control(
            "2023-01-03T15:01:00Z|instrument_id=12345", base + timedelta(minutes=1)
        ),
    )
    one_control = two_controls[:1]
    two_ledger = _usable_predictor_ledger(two_controls)
    one_ledger = _usable_predictor_ledger(one_control)

    # The Cell14 producer emits an integral 0/1 flag; the consumer must normalize it.
    integral = g3p._predictor_data(
        _cell14_calendar_table(pa.array([0, 1], type=pa.int8())),
        two_controls,
        expected_ledger=two_ledger,
    )
    assert integral.calendar[two_controls[0].identity][2] is False
    assert integral.calendar[two_controls[1].identity][2] is True

    # The pre-existing native-boolean producer contract is unchanged.
    boolean = g3p._predictor_data(
        _cell14_calendar_table(pa.array([False, True], type=pa.bool_())),
        two_controls,
        expected_ledger=two_ledger,
    )
    assert boolean.calendar == integral.calendar

    # The shared boundary normalizer also covers NumPy integral producer scalars.
    assert g3p.normalize_integral_flag(np.int8(0)) is False
    assert g3p.normalize_integral_flag(np.int8(1)) is True

    # Out-of-domain integral, non-integral, and null flags keep the one local category.
    for invalid_flag in (
        pa.array([2], type=pa.int8()),
        pa.array([1.0], type=pa.float64()),
        pa.array([None], type=pa.int8()),
    ):
        with pytest.raises(g3p.Test3G3PInvalidEvidenceError) as failure:
            g3p._predictor_data(
                _cell14_calendar_table(invalid_flag),
                one_control,
                expected_ledger=one_ledger,
            )
        assert failure.value.category == "EARLY_CLOSE_SESSION_TYPE_INVALID"


def test_early_close_session_accepts_bool_numpy_bool_and_integral_zero_one() -> None:
    """Native bool, ``numpy.bool_`` and integral 0/1 producers are exactly equivalent."""

    for false_flag, true_flag in (
        (False, True),
        (np.bool_(False), np.bool_(True)),
        (0, 1),
        (np.int8(0), np.int8(1)),
        (np.int64(0), np.int64(1)),
    ):
        assert g3p._normalize_early_close_session(false_flag) is False
        assert g3p._normalize_early_close_session(true_flag) is True


def test_early_close_session_invalid_inputs_map_to_the_single_local_category() -> None:
    """Invalid integral, float, string, null and missing flags all fail closed identically."""

    for rejected in (2, -1, np.int8(2), 0.0, 1.0, np.float64(1.0), "0", "1", "true", None):
        with pytest.raises(g3p.Test3G3PInvalidEvidenceError) as failure:
            g3p._normalize_early_close_session(rejected)
        assert failure.value.category == "EARLY_CLOSE_SESSION_TYPE_INVALID"


def test_predictor_data_rejects_string_and_absent_early_close_session() -> None:
    base = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    one_control = (_control("2023-01-03T15:00:00Z|instrument_id=12345", base),)
    one_ledger = _usable_predictor_ledger(one_control)

    string_flags = (
        pa.array(["0"], type=pa.string()),
        pa.array(["1"], type=pa.string()),
    )
    for string_flag in string_flags:
        with pytest.raises(g3p.Test3G3PInvalidEvidenceError) as failure:
            g3p._predictor_data(
                _cell14_calendar_table(string_flag),
                one_control,
                expected_ledger=one_ledger,
            )
        assert failure.value.category == "EARLY_CLOSE_SESSION_TYPE_INVALID"

    absent = _cell14_calendar_table(pa.array([0], type=pa.int8())).drop_columns(
        ["early_close_session"]
    )
    with pytest.raises(g3p.Test3G3PInvalidEvidenceError) as missing:
        g3p._predictor_data(absent, one_control, expected_ledger=one_ledger)
    assert missing.value.category == "EARLY_CLOSE_SESSION_TYPE_INVALID"


def _handoff_fixture() -> tuple[
    tuple[g3p.ControlRow, ...],
    g3p.PredictorData,
    g3p.TargetBuildResult,
    dict[str, object],
]:
    """Build one tiny synthetic in-memory G3-P result set; no file or provider is involved."""

    base = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    controls = (_control("2023-01-03T15:00:00Z|instrument_id=12345", base),)
    identity = controls[0].identity
    calendar = (30.0, 120.0, False)
    predictor = g3p.PredictorData(
        (PredictorStatusRow(identity, base, RowStatus.PREDICTOR_USABLE.value),),
        {identity: (0.5, 0.6, 0.7)},
        {identity: calendar},
        {status: 0 for status in g3p._STATUS_ORDER},
        "",
        "",
    )
    targets = g3p.TargetBuildResult(
        (
            TargetStatusRow(
                identity,
                base,
                base + timedelta(minutes=60),
                RowStatus.TARGET_USABLE.value,
                1.5,
                math.log(1.5),
            ),
        ),
        {identity: 1.5},
        {status: 0 for status in g3p._TARGET_STATUS_ORDER},
        "",
        1,
        0,
        0,
        0,
        0,
    )
    harmonics = {identity: g3p._harmonic_for(controls[0], calendar)}
    return controls, predictor, targets, harmonics


def test_no_caller_supplied_handoff_callback_or_payload_type_remains() -> None:
    parameters = inspect.signature(g3p.run_g3p).parameters
    assert "handoff" not in parameters
    assert not hasattr(g3p, "G3PInMemoryHandoff")
    assert "G3PInMemoryHandoff" not in g3p.__all__

    flag = parameters["deliver_to_g3f"]
    assert flag.kind is inspect.Parameter.KEYWORD_ONLY
    assert flag.default is False
    assert flag.annotation == "bool"

    delivery = inspect.signature(g3p._deliver_in_memory_handoff).parameters
    assert set(delivery) == {"controls", "predictor", "targets", "harmonic_by_identity"}
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in delivery.values()
    )

    # The one-shot activation is separate: the G3-P CLI wires no delivery and no consumer.
    cli_source = inspect.getsource(g3p.main)
    assert "handoff" not in cli_source
    assert "deliver_to_g3f" not in cli_source


def test_no_arbitrary_or_metadata_based_receiver_boundary_remains() -> None:
    """There is no receiver global to patch and no metadata predicate left to spoof."""

    for name in (
        "_G3F_ROW_HANDOFF_RECEIVER",
        "_G3F_EXPECTED_HANDOFF_ID",
        "G3P_IN_MEMORY_HANDOFF_RECEIVER_MODULE",
        "G3P_IN_MEMORY_HANDOFF_RECEIVER_QUALNAME",
        "_bind_reviewed_g3f_delivery",
    ):
        assert not hasattr(g3p, name), name
        assert name not in g3p.__all__, name

    source = inspect.getsource(g3p._deliver_in_memory_handoff)
    assert "__module__" not in source
    assert "__qualname__" not in source

    # The handle and the module-instance marker are captured in a closure at import, so no
    # module attribute can redirect them. A closure is not secret, but it is not a patch point.
    closure = g3p._deliver_in_memory_handoff.__closure__
    assert closure is not None and len(closure) >= 3

    # G3-P already holds the single one-time handle, so nothing else can ever claim it.
    with pytest.raises(g3f.Test3G3FOneShotError, match="already claimed"):
        g3f._claim_g3p_delivery_handle()


def test_hostile_old_callback_cannot_be_invoked_persisted_logged_or_serialized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    controls, predictor, targets, harmonics = _handoff_fixture()
    monkeypatch.chdir(tmp_path)

    class _HostileCallback:
        def __init__(self) -> None:
            self.calls = 0
            self.captured: list[object] = []

        def __call__(self, *args: object, **kwargs: object) -> object:
            self.calls += 1
            self.captured.append((args, kwargs))
            return "captured"

    hostile = _HostileCallback()

    with pytest.raises(TypeError):
        g3p._deliver_in_memory_handoff(
            hostile,
            controls=controls,
            predictor=predictor,
            targets=targets,
            harmonic_by_identity=harmonics,
        )
    with pytest.raises(TypeError):
        g3p.run_g3p(
            root=tmp_path,
            paths=None,
            git_context=None,
            authorization=None,
            documents={},
            g2p_binding={},
            runtime_binding={},
            handoff=hostile,
        )

    assert hostile.calls == 0
    assert hostile.captured == []
    # Nothing was delivered, printed, logged, written or serialized on the hostile path.
    assert capsys.readouterr() == ("", "")
    assert list(tmp_path.rglob("*")) == []


class _TripwireBundle:
    """Any attribute access on a refused delivery path is an immediate test failure."""

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"G3-P read {name!r} on a refused delivery path")


class _TripwireMapping(Mapping):
    """A row mapping whose contents may never be read on a refused delivery path."""

    def __getitem__(self, key: object) -> object:
        raise AssertionError(f"G3-P read mapping key {key!r} on a refused delivery path")

    def __iter__(self):
        raise AssertionError("G3-P iterated a row mapping on a refused delivery path")

    def __len__(self) -> int:
        raise AssertionError("G3-P measured a row mapping on a refused delivery path")


def _tripwire_delivery_arguments() -> dict[str, object]:
    return {
        "controls": (_TripwireBundle(),),
        "predictor": _TripwireBundle(),
        "targets": _TripwireBundle(),
        "harmonic_by_identity": _TripwireMapping(),
    }


def test_a_reloaded_or_replaced_g3f_instance_refuses_before_any_row_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A replaced module-instance marker fails closed before any row or field is touched."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(g3f, "_MODULE_INSTANCE_MARKER", object(), raising=True)

    with pytest.raises(g3p.Test3G3PBoundaryError, match="module instance"):
        g3p._deliver_in_memory_handoff(**_tripwire_delivery_arguments())

    # The refusal spent nothing: no handoff was created inside the reviewed G3-F stage.
    assert g3f._local_state_report()["handoffs_created"] == 0
    assert g3f._local_state_report()["delivery_handle_armed"] is True
    assert list(tmp_path.rglob("*")) == []


def test_a_metadata_spoof_wrapper_or_callable_object_can_never_be_delivered_to(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: list[object] = []

    class _CallableSpoof:
        """A callable carrying the retired receiver's exact module and qualified name."""

        __module__ = "mes_quant.exploration.test3_g3f_one_shot"
        __qualname__ = "deliver_g3p_row_handoff"

        def __call__(self, *args: object, **kwargs: object) -> object:
            captured.append((args, kwargs))
            return ()

    spoof = _CallableSpoof()

    @functools.wraps(spoof.__call__)
    def wrapper(*args: object, **kwargs: object) -> object:
        captured.append((args, kwargs))
        return ()

    # There is no receiver global, so a spoof or wrapper has nothing to be installed into; it
    # can only be offered as a positional argument, which the keyword-only delivery refuses.
    for hostile in (spoof, wrapper):
        with pytest.raises(TypeError):
            g3p._deliver_in_memory_handoff(hostile, **_tripwire_delivery_arguments())

    assert captured == []
    assert g3f._local_state_report()["handoffs_created"] == 0
    assert list(tmp_path.rglob("*")) == []


def test_delivery_uses_the_captured_handle_once_and_refuses_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controls, predictor, targets, harmonics = _handoff_fixture()
    monkeypatch.chdir(tmp_path)

    assert g3p.G3P_IN_MEMORY_HANDOFF_ID == g3f.EXPECTED_HANDOFF_ID

    assert (
        g3p._deliver_in_memory_handoff(
            controls=controls,
            predictor=predictor,
            targets=targets,
            harmonic_by_identity=harmonics,
        )
        is None
    )
    # Strictly in-memory: no handoff file, temporary spill, cache or IPC artifact is created.
    assert list(tmp_path.rglob("*")) == []
    report = g3f._local_state_report()
    assert report["handoffs_created"] == 1
    assert report["handoffs_spent"] == 1
    assert report["delivery_handle_armed"] is False

    # A second delivery or replay is refused at first-stage entry, before G3-P evaluates any
    # predictor/target/harmonic field expression: every tripwire attribute access and every
    # tripwire mapping read below would fail this test outright.
    with pytest.raises(
        g3f.Test3G3FPreActivationStop,
        match="one-time G3-P delivery handle is already spent",
    ):
        g3p._deliver_in_memory_handoff(**_tripwire_delivery_arguments())
    assert g3f._local_state_report()["handoffs_created"] == 1
    assert list(tmp_path.rglob("*")) == []


def test_delivery_runs_outside_the_pre_fit_only_guard() -> None:
    lines = inspect.getsource(g3p.run_g3p).splitlines()

    def indent(line: str) -> int:
        return len(line) - len(line.lstrip())

    guard = next(index for index, line in enumerate(lines) if "with pre_fit_only_guard()" in line)
    delivery = next(index for index, line in enumerate(lines) if "if deliver_to_g3f:" in line)
    assert delivery > guard
    assert indent(lines[delivery]) == indent(lines[guard])


def test_delivery_source_opens_no_persistence_or_logging_surface() -> None:
    source = inspect.getsource(g3p._deliver_in_memory_handoff)
    for forbidden in ("open(", ".write(", "json", "pickle", "tempfile", "socket", "print("):
        assert forbidden not in source


# ---------------------------------------------------------------------------------------------
# Fresh capability-bound recovery entrypoint.
#
# These tests stay strictly before every protected surface. None of them supplies a real artifact
# path, reaches a provider, consumes the real target space, creates a reservation or runs a fit.
# ---------------------------------------------------------------------------------------------


def _reservation_binding(**overrides: object) -> dict[str, object]:
    """A synthetic stand-in for the reviewed G3-F reservation binding; never real authority."""

    binding: dict[str, object] = {
        "recovery_lineage_id": "SYNTHETIC-PLACEHOLDER-LINEAGE-001",
        "override_id": "SYNTHETIC-PLACEHOLDER-OVERRIDE-001",
        "protocol_id": g3p.PROTOCOL_ID,
        "protocol_sha256": g3p.PROTOCOL_SHA256,
        "target_space_id": g3p.TARGET_SPACE_ID,
        "reservation_name": "synthetic-placeholder-reservation",
        "reservation_sha256": "0" * 64,
        "reservation_status": g3f.RESERVATION_STATUS,
    }
    binding.update(overrides)
    return binding


class _TripwireArtifactPaths:
    """Any artifact-path access before the reservation is verified fails the test."""

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"G3-P touched artifact path {name!r} before its reservation")


def test_recovery_refuses_every_unreserved_authority_before_any_source_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    for hostile in (None, object(), "authority", {"reservation_sha256": "0" * 64}):
        with pytest.raises(g3f.Test3G3FPreActivationStop):
            g3p.run_g3p_recovery(
                root=tmp_path,
                paths=_TripwireArtifactPaths(),
                execution_authority=hostile,
            )
    # Nothing was read, sealed, consumed or written on any refused path.
    assert list(tmp_path.rglob("*")) == []


@pytest.mark.parametrize(
    ("label", "overrides"),
    (
        ("spent_authorization_identity", {"recovery_lineage_id": g3p.G3P_AUTHORIZATION_ID}),
        ("spent_gate_identity", {"recovery_lineage_id": g3p.G3P_GATE_ID}),
        ("spent_branch_identity", {"recovery_lineage_id": g3p.G3P_BRANCH}),
        ("empty_lineage", {"recovery_lineage_id": ""}),
        ("path_separator_lineage", {"recovery_lineage_id": "lineage/with/separator"}),
        ("wrong_protocol_bytes", {"protocol_sha256": "9" * 64}),
        ("wrong_target_space", {"target_space_id": "TARGET_SPACE_999"}),
    ),
)
def test_recovery_refuses_a_drifted_or_spent_binding_before_any_source_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    label: str,
    overrides: dict,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        g3f,
        "assert_execution_authority_reserved",
        lambda _authority: _reservation_binding(**overrides),
    )

    with pytest.raises(g3p.Test3G3PBoundaryError):
        g3p.run_g3p_recovery(
            root=tmp_path,
            paths=_TripwireArtifactPaths(),
            execution_authority=object(),
        )
    assert list(tmp_path.rglob("*")) == []


def test_recovery_takes_no_historical_reservation_topology_or_witness_credit() -> None:
    """The fresh lineage may not call any spent-authority or repository-topology helper."""

    source = inspect.getsource(g3p.run_g3p_recovery)
    tree = ast.parse(textwrap.dedent(source))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    for forbidden in (
        "_consume_authorization",
        "_git_context",
        "_verify_documents",
        "_verify_g2p_evidence",
        "_assert_runtime_module_origins",
        "write_failure_summary_if_reserved",
        "write_g3p_record",
        "run_g3p",
    ):
        assert forbidden not in called, forbidden

    # The historical witness constants are never used as write or read destinations here.
    read = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    for forbidden in (
        "AUTHORIZATION_RESERVATION_PATH",
        "REQUEST_SET_WITNESS_PATH",
        "TARGET_SPACE_WITNESS_PATH",
        "FAILURE_RECORD_PATH",
        "G3P_OUTPUT_SUBPATH",
        "G3P_BASE_COMMIT",
        "G2P_RECORD_PATH",
    ):
        assert forbidden not in read, forbidden

    # The predecessor ledger cross-check is explicitly disclaimed rather than silently reused.
    assert "expected_ledger=None" in source


def test_recovery_consumes_the_target_space_before_the_first_numeric_target_read() -> None:
    lines = inspect.getsource(g3p.run_g3p_recovery).splitlines()

    def index_of(fragment: str) -> int:
        return next(index for index, line in enumerate(lines) if fragment in line)

    consumption = index_of("G3P_RECOVERY_TARGET_WITNESS")
    for later in ("paths.cell10", "paths.cell12", "decode_canonical_dbn(", "_build_targets("):
        assert index_of(later) > consumption
    # The request set is sealed and witnessed before the target space is consumed at all.
    assert index_of("G3P_RECOVERY_REQUEST_WITNESS") < consumption
    # Delivery is the very last action and is guarded by the support gate.
    assert index_of("if not support_passed:") < index_of("_deliver_in_memory_handoff(")
    assert index_of("bind_source_evidence") < index_of("_deliver_in_memory_handoff(")


def test_recovery_flags_every_undefined_required_acf_lag() -> None:
    def profile(defined_through: int) -> dict[str, object]:
        return {
            "lags": [
                {
                    "lag": lag,
                    "pairs": 10 if lag <= defined_through else 0,
                    "rho_observed": 0.4 if lag <= defined_through else None,
                    "rho_null": 0.0,
                    "excess": 0.4 if lag <= defined_through else None,
                }
                for lag in range(1, 9)
            ]
        }

    complete = {
        "folds": {"WF_2022": {"dependence": profile(8)}, "WF_2023": {"dependence": profile(8)}},
        "pooled_disjoint_oof_dependence": profile(8),
    }
    assert g3p._recovery_required_lags_defined(complete) == ()

    partial = {
        "folds": {"WF_2022": {"dependence": profile(5)}, "WF_2023": {"dependence": profile(8)}},
        "pooled_disjoint_oof_dependence": profile(8),
    }
    failures = g3p._recovery_required_lags_defined(partial)
    assert failures == (
        "WF_2022:REQUIRED_ACF_LAG_6_UNDEFINED",
        "WF_2022:REQUIRED_ACF_LAG_7_UNDEFINED",
        "WF_2022:REQUIRED_ACF_LAG_8_UNDEFINED",
    )

    pooled = {
        "folds": {"WF_2022": {"dependence": profile(8)}, "WF_2023": {"dependence": profile(8)}},
        "pooled_disjoint_oof_dependence": profile(7),
    }
    assert g3p._recovery_required_lags_defined(pooled) == (
        "pooled_disjoint_oof:REQUIRED_ACF_LAG_8_UNDEFINED",
    )

    assert g3p._recovery_required_lags_defined({}) == (
        "pooled_disjoint_oof:DEPENDENCE_ABSENT",
    )


def test_recovery_flags_a_holdout_row_outside_its_frozen_fold_year() -> None:
    good = (
        _control(
            "a|instrument_id=12345",
            datetime(2022, 6, 1, 15, 0, tzinfo=UTC),
            role_2022="VALIDATION",
            role_2023="UNUSED",
        ),
        _control(
            "b|instrument_id=12345",
            datetime(2023, 6, 1, 15, 0, tzinfo=UTC),
            role_2022="UNUSED",
            role_2023="VALIDATION",
        ),
    )
    assert g3p._recovery_holdout_year_failures(good) == ()

    drifted = (
        good[0],
        _control(
            "c|instrument_id=12345",
            datetime(2022, 6, 2, 15, 0, tzinfo=UTC),
            role_2022="UNUSED",
            role_2023="VALIDATION",
        ),
    )
    assert g3p._recovery_holdout_year_failures(drifted) == ("WF_2023:HOLDOUT_YEAR_NOT_2023",)


def test_recovery_support_gate_failure_is_underpowered_and_delivers_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-pass G3-P support gate can never reach the fit stage."""

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
    structural = tuple(evidence["structural_failures"])
    structural += g3p._recovery_required_lags_defined(evidence)
    structural += g3p._recovery_holdout_year_failures(controls)
    assert "WF_2022:HOLDOUT_SESSIONS_LT_20" in structural
    # The recovery gate composes the frozen support failures with its own additional minima, so
    # a support-gate failure can only produce a non-delivering UNDERPOWERED_STOP.
    assert not (disposition != "UNDERPOWERED_STOP" and not structural)


def test_recovery_predictor_ledger_stays_frozen_without_predecessor_credit() -> None:
    signature = inspect.signature(g3p._predictor_data).parameters
    assert signature["expected_ledger"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature["expected_ledger"].default is inspect.Parameter.empty

    recovery = inspect.signature(g3p.run_g3p_recovery).parameters
    assert set(recovery) == {"root", "paths", "execution_authority"}
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in recovery.values()
    )
    assert "handoff" not in recovery
    assert "fit_callback" not in recovery

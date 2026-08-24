from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mes_quant.exploration import test3_g2p_preflight as g2p
from mes_quant.exploration.test3_contract import FailureReason, RowStatus
from mes_quant.exploration.test3_design import (
    SyntheticPredictorRequest,
    build_synthetic_predictor_ledger,
)

_TEST_TEMP_ROOT = "/private/tmp"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _control_rows(count: int, *, start: datetime) -> dict[str, list[object]]:
    return {
        "decision_id": [f"D{index:04d}" for index in range(count)],
        "decision_time": [start + timedelta(minutes=15 * index) for index in range(count)],
        "instrument_id": [12345] * count,
        "outer_partition": ["TRAIN"] * count,
        "role_wf_2022": ["TRAIN", "VALIDATION", "UNUSED", "TRAIN"][:count],
        "role_wf_2023": ["TRAIN", "TRAIN", "VALIDATION", "UNUSED"][:count],
    }


def _fixture(
    root: Path,
    *,
    train_values: tuple[tuple[float | None, float | None, float | None], ...] | None = None,
    invert_train_order: bool = False,
) -> tuple[Path, Path]:
    train_values = train_values or (
        (1.0, 2.0, 3.0),
        (None, 2.0, 3.0),
        (1.5, 2.5, 3.5),
        (2.0, 3.0, 4.0),
    )
    train_count = len(train_values)
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    controls = _control_rows(train_count, start=start)
    if invert_train_order:
        controls["decision_time"][1], controls["decision_time"][2] = (
            controls["decision_time"][2],
            controls["decision_time"][1],
        )

    cell8_data = {key: list(values) for key, values in controls.items()}
    cell8_data["decision_id"].extend(["V", "F"])
    cell8_data["decision_time"].extend(
        [
            datetime(2024, 1, 2, 15, 0, tzinfo=UTC),
            datetime(2025, 1, 2, 15, 0, tzinfo=UTC),
        ]
    )
    cell8_data["instrument_id"].extend([12345, 12345])
    cell8_data["outer_partition"].extend(["VALIDATION", "FINAL_TEST"])
    cell8_data["role_wf_2022"].extend(["UNUSED", "UNUSED"])
    cell8_data["role_wf_2023"].extend(["UNUSED", "UNUSED"])

    cell14_data = {key: list(values) for key, values in controls.items()}
    cell14_data["decision_id"].append("V")
    cell14_data["decision_time"].append(datetime(2024, 1, 2, 15, 0, tzinfo=UTC))
    cell14_data["instrument_id"].append(12345)
    cell14_data["outer_partition"].append("VALIDATION")
    cell14_data["role_wf_2022"].append("UNUSED")
    cell14_data["role_wf_2023"].append("UNUSED")
    for column_index, column in enumerate(g2p.PREDICTOR_COLUMNS):
        cell14_data[column] = [values[column_index] for values in train_values] + [
            float("-inf")
        ]
    cell14_data["feature_row_usable"] = [False] * (train_count + 1)
    cell14_data["unrelated_feature"] = [float("nan")] * (train_count + 1)

    cell8_path = root / g2p.CELL8_FILENAME
    cell14_path = root / g2p.CELL14_FILENAME
    pq.write_table(pa.table(cell8_data), cell8_path, row_group_size=len(cell8_data["decision_id"]))
    pq.write_table(
        pa.table(cell14_data),
        cell14_path,
        row_group_size=len(cell14_data["decision_id"]),
    )
    return cell8_path, cell14_path


def _authorization(root: Path) -> g2p._ObservedAuthorization:
    return g2p._ObservedAuthorization(
        authorization_id=g2p.G2P_AUTHORIZATION_ID,
        document_sha256=g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256,
        code_identity="a" * 40,
        tree_identity="b" * 40,
        reservation_path=root / "authorization.consumed.json",
        reservation_file_sha256="c" * 64,
        _verification_key=g2p._AUTHORIZATION_KEY,
    )


def _git_context() -> g2p._GitContext:
    return g2p._GitContext("a" * 40, "b" * 40, g2p.G2P_BRANCH, "a" * 40)


def _build(
    root: Path,
    *,
    train_values: tuple[tuple[float | None, float | None, float | None], ...] | None = None,
    invert_train_order: bool = False,
    audit_written_utc: str = "2026-08-24T00:00:00Z",
) -> dict[str, object]:
    cell8, cell14 = _fixture(
        root,
        train_values=train_values,
        invert_train_order=invert_train_order,
    )
    count = len(train_values) if train_values is not None else 4
    with (
        patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", count),
        patch.object(g2p, "CELL8_SPLIT_ASSIGNMENT_SHA256", _sha(cell8)),
        patch.object(g2p, "CELL14_FEATURE_FILE_SHA256", _sha(cell14)),
        patch.object(g2p, "_assert_forbidden_modules_absent"),
    ):
        return g2p.build_g2p_record(
            cell8_path=cell8,
            cell14_path=cell14,
            git_context=_git_context(),
            authorization=_authorization(root),
            document_bindings={"synthetic": {"match": True}},
            g2_evidence_binding={"synthetic": {"match": True}},
            runtime_binding={"synthetic": {"match": True}},
            audit_written_utc=audit_written_utc,
        )


def test_projection_is_train_filtered_exact_and_validation_sentinel_is_unexposed() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        cell8, cell14 = _fixture(root)
        calls: list[tuple[tuple[str, ...], object]] = []
        real_read_table = pq.read_table

        def spy(source, *, columns, filters, use_threads):
            calls.append((tuple(columns), filters))
            return real_read_table(
                source,
                columns=columns,
                filters=filters,
                use_threads=use_threads,
            )

        with (
            patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
            patch.object(g2p, "CELL8_SPLIT_ASSIGNMENT_SHA256", _sha(cell8)),
            patch.object(g2p, "CELL14_FEATURE_FILE_SHA256", _sha(cell14)),
            patch.object(g2p.pq, "read_table", side_effect=spy),
            patch.object(g2p, "_assert_forbidden_modules_absent"),
        ):
            record = g2p.build_g2p_record(
                cell8_path=cell8,
                cell14_path=cell14,
                git_context=_git_context(),
                authorization=_authorization(root),
                document_bindings={},
                g2_evidence_binding={},
                runtime_binding={},
            )
    assert calls == [
        (g2p.CONTROL_COLUMNS, [("outer_partition", "==", "TRAIN")]),
        (
            (*g2p.CONTROL_COLUMNS, *g2p.PREDICTOR_COLUMNS),
            [("outer_partition", "==", "TRAIN")],
        ),
    ]
    ledger = record["predictor_status_ledger"]
    assert ledger["status_counts"] == {
        "PREDICTOR_USABLE": 3,
        "PREDICTOR_UNUSABLE": 1,
        "PREDICTOR_NONFINITE": 0,
        "PREDICTOR_NONPOSITIVE": 0,
    }
    assert record["stage_status"] == "G2P_PREDICTOR_PREFLIGHT_PASS"
    assert record["terminal_disposition"] == "NOT_COMPUTED_STAGE_NOT_AUTHORIZED"
    assert record["safety_counters"]["g2p_validation_predictor_rows_read"] == 0


def test_null_bitmap_and_failure_precedence_match_l0_contract() -> None:
    cases = (
        (None, 2.0, 3.0),
        (None, float("nan"), 3.0),
        (None, -1.0, 3.0),
        (1.0, 2.0, 3.0),
    )
    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    expected = build_synthetic_predictor_ledger(
        SyntheticPredictorRequest(
            f"D{index:04d}",
            start + timedelta(minutes=15 * index),
            *values,
        )
        for index, values in enumerate(cases)
    )
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary), train_values=cases)
    counts = record["predictor_status_ledger"]["status_counts"]
    assert counts == dict(expected.status_counts)
    assert counts[FailureReason.PREDICTOR_NONFINITE.value] == 1
    assert counts[FailureReason.PREDICTOR_NONPOSITIVE.value] == 1
    assert record["stage_status"] == "G2P_INVALID_EVIDENCE_SEALED"
    assert record["terminal_disposition"] == "INVALID_EVIDENCE"
    assert record["cause_audit_status"] == "REQUIRED_BEFORE_TARGET_SPACE_STATE_TRANSITION"
    assert record["safety_counters"]["g2p_target_or_path_rows_read"] == 0


def test_source_order_inversion_fails_instead_of_sorting() -> None:
    with (
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary,
        pytest.raises(
            g2p.Test3G2PInvalidEvidenceError,
            match="TRAIN_CONTROL_SOURCE_ORDER_INVERSION",
        ),
    ):
        _build(Path(temporary), invert_train_order=True)


def test_cell8_cell14_control_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        cell8, cell14 = _fixture(root)
        table = pq.read_table(cell14)
        changed = table.set_column(
            table.schema.get_field_index("instrument_id"),
            "instrument_id",
            pa.array([54321, 12345, 12345, 12345, 12345]),
        )
        pq.write_table(changed, cell14, row_group_size=5)
        with (
            patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
            patch.object(g2p, "CELL8_SPLIT_ASSIGNMENT_SHA256", _sha(cell8)),
            patch.object(g2p, "CELL14_FEATURE_FILE_SHA256", _sha(cell14)),
            patch.object(g2p, "_assert_forbidden_modules_absent"),
            pytest.raises(
                g2p.Test3G2PInvalidEvidenceError,
                match="CELL8_CELL14_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH",
            ),
        ):
            g2p.build_g2p_record(
                cell8_path=cell8,
                cell14_path=cell14,
                git_context=_git_context(),
                authorization=_authorization(root),
                document_bindings={},
                g2_evidence_binding={},
                runtime_binding={},
            )


def test_aggregate_record_contains_no_rows_values_or_source_identities() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary))
    encoded = json.dumps(record, sort_keys=True)
    assert "D0000" not in encoded
    assert '"decision_id"' not in encoded
    assert '"decision_time"' not in encoded
    assert "unrelated_feature" not in encoded
    assert "feature_row_usable" not in encoded
    assert '"minimum"' not in encoded
    assert record["predictor_status_ledger"]["raw_predictor_values_persisted"] is False


def test_record_semantic_identity_is_root_and_audit_time_stable() -> None:
    with (
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as first,
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as second,
    ):
        one = _build(Path(first), audit_written_utc="2026-08-24T00:00:00Z")
        two = _build(Path(second), audit_written_utc="2026-08-25T00:00:00Z")
    assert one["run_id"] == two["run_id"]
    assert one["record_sha256"] == two["record_sha256"]


def test_record_writer_is_create_once_and_reverifies_semantic_hash() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        record = _build(root)
        output_root = root / "evidence"
        with patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4):
            output, file_sha = g2p.write_g2p_record(record, output_root=output_root)
            assert output.is_file()
            assert _sha(output) == file_sha
            with pytest.raises(FileExistsError):
                g2p.write_g2p_record(record, output_root=output_root)


def test_forged_authorization_fails_before_opening_artifacts() -> None:
    forged = g2p._ObservedAuthorization(
        g2p.G2P_AUTHORIZATION_ID,
        g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256,
        "a" * 40,
        "b" * 40,
        Path("reservation"),
        "c" * 64,
        object(),
    )
    with (
        patch.object(g2p, "_open_regular_file") as opened,
        pytest.raises(g2p.Test3G2PBoundaryError, match="verified consumed"),
    ):
        g2p.build_g2p_record(
            cell8_path=g2p.CELL8_FILENAME,
            cell14_path=g2p.CELL14_FILENAME,
            git_context=_git_context(),
            authorization=forged,
            document_bindings={},
            g2_evidence_binding={},
            runtime_binding={},
        )
    opened.assert_not_called()


def test_new_and_consumed_authorization_identities_are_distinct() -> None:
    assert (
        g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256
        != g2p.G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256
    )
    assert g2p.G2P_AUTHORIZATION_DOCUMENT in g2p._DOCUMENT_BINDINGS
    assert (
        g2p._DOCUMENT_BINDINGS[g2p.G2P_AUTHORIZATION_DOCUMENT]
        == g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256
    )
    assert g2p.G2_METADATA_AUTHORIZATION_DOCUMENT_SHA256 in g2p.G2_RESERVATION_RECORD


def test_current_document_pins_and_committed_g2_predecessor_are_exact() -> None:
    project_root = Path(g2p.__file__).parents[3]
    assert _sha(project_root / g2p.G2P_AUTHORIZATION_DOCUMENT) == (
        g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256
    )
    assert _sha(project_root / g2p.G2P_PACKAGE_DOCUMENT) == (
        g2p.G2P_PACKAGE_DOCUMENT_SHA256
    )
    predecessor = g2p._verify_g2_evidence(project_root)
    assert predecessor["evidence_commit"] == g2p.G2P_BASE_COMMIT
    assert predecessor["binding_status"] == (
        "EXACT_COMMITTED_G2_EVIDENCE_VERIFIED_BEFORE_G2P_ACCESS"
    )


def test_failure_summary_is_scrubbed_and_create_once() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        auth_root = root / "artifacts/exploration/test3/g2p/authorization"
        auth_root.mkdir(parents=True)
        reservation = auth_root / f"{g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
        reservation.write_text("{}\n", encoding="utf-8")
        first = g2p.write_failure_summary_if_consumed(
            project_root=root,
            error=RuntimeError("secret predictor value 123"),
        )
        second = g2p.write_failure_summary_if_consumed(
            project_root=root,
            error=ValueError("different secret"),
        )
        assert first == second
        payload = json.loads(first.read_text(encoding="utf-8"))
        assert payload["error_class"] == "RuntimeError"
        assert "secret" not in first.read_text(encoding="utf-8")


def test_source_ledger_mismatch_gets_typed_invalid_evidence_summary() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        auth_root = root / "artifacts/exploration/test3/g2p/authorization"
        auth_root.mkdir(parents=True)
        reservation = auth_root / f"{g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
        reservation.write_text("{}\n", encoding="utf-8")
        failure = g2p.write_failure_summary_if_consumed(
            project_root=root,
            error=g2p.Test3G2PInvalidEvidenceError(
                "CELL8_CELL14_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH"
            ),
        )
        payload = json.loads(failure.read_text(encoding="utf-8"))
    assert payload["terminal_disposition"] == "INVALID_EVIDENCE"
    assert payload["invalid_evidence_category"] == (
        "CELL8_CELL14_OUTER_TRAIN_CONTROL_LEDGER_MISMATCH"
    )
    assert payload["target_space_state"] == "LOCKED / RESERVED"
    assert payload["target_space_consumption_status"] == (
        "NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT"
    )
    assert all(value == 0 for value in payload["protected_surface_counters"].values())
    assert payload["validation_status"] == "UNOPENED"
    assert payload["final_test_status"] == "SEALED"


def test_invalid_projection_never_claims_unverified_exposure_zeros() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        auth_root = root / "artifacts/exploration/test3/g2p/authorization"
        auth_root.mkdir(parents=True)
        reservation = auth_root / f"{g2p.G2P_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
        reservation.write_text("{}\n", encoding="utf-8")
        failure = g2p.write_failure_summary_if_consumed(
            project_root=root,
            error=g2p.Test3G2PInvalidEvidenceError(
                "CELL14_PREDICTOR_PROJECTION_NON_TRAIN_ROW_EXPOSED",
                projection_access_attested=False,
            ),
        )
        payload = json.loads(failure.read_text(encoding="utf-8"))
    counters = payload["protected_surface_counters"]
    assert counters["outer_validation_target_rows_read"] == 0
    assert counters["real_models_fitted"] == 0
    assert counters["g2p_validation_predictor_rows_read"] == (
        "NOT_ATTESTED_DUE_TO_INVALID_PROJECTION"
    )
    assert counters["non_allowlisted_cell14_value_columns_read"] == (
        "NOT_ATTESTED_DUE_TO_INVALID_PROJECTION"
    )
    assert payload["projection_access_attested"] is False
    assert payload["validation_status"] == "ACCESS_BREACH_FAIL_CLOSED"
    assert payload["final_test_status"] == "ACCESS_BREACH_FAIL_CLOSED"


def test_runtime_source_has_no_forbidden_reader_imports_or_all_features() -> None:
    source_path = Path(g2p.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden = {
        "mes_quant.exploration.test2_l1_harness",
        "mes_quant.exploration.test2_g3_pre_fit",
        "mes_quant.exploration.test3_target",
        "mes_quant.exploration.test3_design",
        "mes_quant.exploration.test3_stats",
        "mes_quant.exploration.test3_evaluation",
    }
    assert not imported.intersection(forbidden)
    assert not any(
        alias.name == "pandas" or alias.name.startswith("pandas.")
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert "feature_row_usable" not in source
    assert "feature_status" not in source
    assert set(g2p.G2P_ALLOWED_CHANGED_FILES) == {
        g2p.G2P_AUTHORIZATION_DOCUMENT,
        g2p.G2P_PACKAGE_DOCUMENT,
        "src/mes_quant/exploration/test3_g2p_preflight.py",
        "tests/test_test3_g2p_preflight.py",
        "tools/run_test3_g2p_preflight.py",
    }


def test_nonfinite_and_nonpositive_do_not_stop_ledger_completion() -> None:
    values = (
        (float("nan"), 1.0, 1.0),
        (0.0, 1.0, 1.0),
        (1.0, 1.0, 1.0),
        (None, 1.0, 1.0),
    )
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary), train_values=values)
    ledger = record["predictor_status_ledger"]
    assert ledger["row_count"] == len(values)
    assert sum(ledger["status_counts"].values()) == len(values)
    assert record["safety_counters"]["targets_constructed"] == 0


def test_counter_semantics_are_explicit_and_no_physical_decode_claim_is_made() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary))
    assert record["counter_semantics"] == {
        "rows_read": "APPLICATION_EXPOSED_ROWS",
        "validation_predictor_values_exposed_to_python": 0,
        "parquet_compressed_byte_or_internal_page_decode_exclusion_claimed": False,
    }
    assert record["target_space_consumption_status"] == (
        "NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT"
    )
    assert record["validation_status"] == "UNOPENED"
    assert record["final_test_status"] == "SEALED"


def test_closed_record_rejects_negative_or_extra_status_counts() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary))
    changed = json.loads(json.dumps(record))
    changed["predictor_status_ledger"]["status_counts"]["EXTRA"] = 0
    with (
        patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
        pytest.raises(g2p.Test3G2PBoundaryError, match="key set"),
    ):
        g2p._assert_closed_record(changed)
    changed = json.loads(json.dumps(record))
    changed["predictor_status_ledger"]["status_counts"][RowStatus.PREDICTOR_USABLE] = -1
    with (
        patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
        pytest.raises(g2p.Test3G2PBoundaryError, match="nonnegative"),
    ):
        g2p._assert_closed_record(changed)


def test_open_regular_file_rejects_final_symlink() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        target = root / "target"
        target.write_bytes(b"x")
        link = root / "link"
        link.symlink_to(target)
        with (
            pytest.raises(g2p.Test3G2PBoundaryError, match="symlink"),
            g2p._open_regular_file(link),
        ):
            pass


def test_ledger_hash_projection_matches_l0_and_is_status_sensitive() -> None:
    usable_one = (
        (1.0, 2.0, 3.0),
        (1.5, 2.5, 3.5),
        (2.0, 3.0, 4.0),
        (2.5, 3.5, 4.5),
    )
    usable_two = tuple(tuple(value * 10.0 for value in row) for row in usable_one)
    changed_status = (usable_one[0], (0.0, 2.5, 3.5), *usable_one[2:])
    with (
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as first,
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as second,
        tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as third,
    ):
        one = _build(Path(first), train_values=usable_one)
        two = _build(Path(second), train_values=usable_two)
        three = _build(Path(third), train_values=changed_status)

    start = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    expected = build_synthetic_predictor_ledger(
        SyntheticPredictorRequest(
            f"D{index:04d}",
            start + timedelta(minutes=15 * index),
            *values,
        )
        for index, values in enumerate(usable_one)
    )
    one_ledger = one["predictor_status_ledger"]
    two_ledger = two["predictor_status_ledger"]
    three_ledger = three["predictor_status_ledger"]
    assert one_ledger["hash_projection_id"] == g2p.LEDGER_HASH_PROJECTION_ID
    assert one_ledger["ordered_identity_status_sha256"] == expected.ordered_status_sha256
    assert one_ledger["ordered_identity_sha256"] == two_ledger["ordered_identity_sha256"]
    assert one_ledger["ordered_identity_status_sha256"] == (
        two_ledger["ordered_identity_status_sha256"]
    )
    assert one_ledger["ordered_identity_sha256"] == three_ledger["ordered_identity_sha256"]
    assert one_ledger["ordered_identity_status_sha256"] != (
        three_ledger["ordered_identity_status_sha256"]
    )


def test_non_train_and_protected_surface_counters_are_explicit_zero() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        record = _build(Path(temporary))
    expected_zero = {
        "cell8_validation_control_rows_read",
        "cell8_final_test_control_rows_read",
        "cell14_validation_control_rows_read",
        "cell14_final_test_control_rows_read",
        "cell10_rows_read",
        "cell12_rows_read",
        "raw_dbn_messages_decoded",
        "non_allowlisted_cell14_value_columns_read",
        *g2p._ZERO_COUNTERS.keys(),
    }
    counters = record["safety_counters"]
    assert all(counters[key] == 0 for key in expected_zero)
    assert counters["g2p_train_predictor_rows_read"] == 4
    assert counters["g2p_predictor_cells_inspected"] == 12
    with patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4):
        witness = "\n".join(g2p._terminal_witness_lines(record))
    for literal in (
        "CELL8_VALIDATION_CONTROL_ROWS_READ=0",
        "CELL8_FINAL_TEST_CONTROL_ROWS_READ=0",
        "CELL14_VALIDATION_CONTROL_ROWS_READ=0",
        "CELL14_FINAL_TEST_CONTROL_ROWS_READ=0",
        "CELL10_ROWS_READ=0",
        "CELL12_ROWS_READ=0",
        "RAW_DBN_MESSAGES_DECODED=0",
        "NON_ALLOWLISTED_CELL14_VALUE_COLUMNS_READ=0",
    ):
        assert literal in witness


def test_input_and_output_ancestor_symlinks_fail_closed() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        real = root / "real"
        real.mkdir()
        source = real / "source.bin"
        source.write_bytes(b"source")
        linked = root / "linked"
        linked.symlink_to(real, target_is_directory=True)
        with (
            pytest.raises(g2p.Test3G2PBoundaryError, match="symlink"),
            g2p._open_regular_file(linked / source.name),
        ):
            pass
        with pytest.raises(g2p.Test3G2PBoundaryError, match="symlink"):
            g2p._atomic_create_json(linked / "evidence.json", {"status": "forbidden"})


def test_same_descriptor_post_scan_hash_detects_mutation() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        cell8, cell14 = _fixture(root)
        real_read_table = pq.read_table
        calls = 0

        def mutate_after_read(source, *, columns, filters, use_threads):
            nonlocal calls
            table = real_read_table(
                source,
                columns=columns,
                filters=filters,
                use_threads=use_threads,
            )
            calls += 1
            if calls == 1:
                with cell8.open("r+b") as stream:
                    stream.seek(8)
                    original = stream.read(1)
                    stream.seek(8)
                    stream.write(bytes([original[0] ^ 1]))
                    stream.flush()
            return table

        with (
            patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
            patch.object(g2p, "CELL8_SPLIT_ASSIGNMENT_SHA256", _sha(cell8)),
            patch.object(g2p, "CELL14_FEATURE_FILE_SHA256", _sha(cell14)),
            patch.object(g2p.pq, "read_table", side_effect=mutate_after_read),
            patch.object(g2p, "_assert_forbidden_modules_absent"),
            pytest.raises(g2p.Test3G2PBoundaryError, match="bytes changed"),
        ):
            g2p.build_g2p_record(
                cell8_path=cell8,
                cell14_path=cell14,
                git_context=_git_context(),
                authorization=_authorization(root),
                document_bindings={},
                g2_evidence_binding={},
                runtime_binding={},
            )


def test_record_writer_rejects_run_id_traversal() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        record = _build(root)
        record["run_id"] = "MES_T3_G2P_../../ESCAPE"
        record["record_sha256"] = g2p._record_sha256(record)
        with (
            patch.object(g2p, "EXPECTED_OUTER_TRAIN_ROWS", 4),
            pytest.raises(g2p.Test3G2PBoundaryError, match="run_id"),
        ):
            g2p.write_g2p_record(record, output_root=root / "evidence")
        assert not (root / "ESCAPE").exists()


def test_consume_authorization_is_create_once_and_binds_git_context() -> None:
    with tempfile.TemporaryDirectory(dir=_TEST_TEMP_ROOT) as temporary:
        root = Path(temporary)
        document = root / g2p.G2P_AUTHORIZATION_DOCUMENT
        document.parent.mkdir(parents=True)
        document.write_text("synthetic authorization\n", encoding="utf-8")
        output_root = root / "artifacts/exploration/test3/g2p"
        context = _git_context()
        with patch.object(g2p, "G2P_AUTHORIZATION_DOCUMENT_SHA256", _sha(document)):
            observed = g2p._consume_authorization(
                project_root=root,
                output_root=output_root,
                git_context=context,
                authorization_token=g2p.G2P_AUTHORIZATION_TOKEN,
            )
            payload = json.loads(observed.reservation_path.read_text(encoding="utf-8"))
            assert payload["execution_commit"] == context.code_identity
            assert payload["execution_tree"] == context.tree_identity
            assert payload["branch"] == context.branch
            assert payload["status"] == "CONSUMED_BEFORE_PREDICTOR_ACCESS"
            with pytest.raises(g2p.Test3G2PBoundaryError, match="already consumed"):
                g2p._consume_authorization(
                    project_root=root,
                    output_root=output_root,
                    git_context=context,
                    authorization_token=g2p.G2P_AUTHORIZATION_TOKEN,
                )


def test_git_context_requires_direct_child_allowlist_and_exact_upstream() -> None:
    head = "a" * 40
    tree = "b" * 40

    def answers(_project_root: Path, *args: str) -> str:
        values = {
            ("branch", "--show-current"): g2p.G2P_BRANCH,
            ("rev-parse", "HEAD"): head,
            ("rev-parse", "HEAD^{tree}"): tree,
            ("rev-list", "--parents", "-n", "1", head): (
                f"{head} {g2p.G2P_BASE_COMMIT}"
            ),
            ("diff", "--name-only", f"{g2p.G2P_BASE_COMMIT}..{head}"): "\n".join(
                sorted(g2p.G2P_ALLOWED_CHANGED_FILES)
            ),
            ("status", "--porcelain=v1", "--untracked-files=no"): "",
            ("rev-parse", "@{upstream}"): head,
            ("rev-parse", "--symbolic-full-name", "@{upstream}"): (
                f"refs/remotes/origin/{g2p.G2P_BRANCH}"
            ),
        }
        return values[args]

    with (
        patch.object(g2p, "_git_output", side_effect=answers),
        patch.object(g2p, "_assert_no_untracked_import_surface"),
    ):
        observed = g2p._git_execution_context(Path("/private/tmp"))
    assert observed == g2p._GitContext(head, tree, g2p.G2P_BRANCH, head)

    def wrong_parent(project_root: Path, *args: str) -> str:
        if args[:4] == ("rev-list", "--parents", "-n", "1"):
            return f"{head} {'c' * 40}"
        return answers(project_root, *args)

    with (
        patch.object(g2p, "_git_output", side_effect=wrong_parent),
        pytest.raises(g2p.Test3G2PBoundaryError, match="direct-child"),
    ):
        g2p._git_execution_context(Path("/private/tmp"))


def test_thin_runner_rejects_nonisolated_python_and_accepts_isolated_help() -> None:
    project_root = Path(g2p.__file__).parents[3]
    runner = project_root / "tools/run_test3_g2p_preflight.py"
    nonisolated = subprocess.run(
        [sys.executable, str(runner), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert nonisolated.returncode != 0
    assert "requires .venv/bin/python -I -B" in nonisolated.stderr
    isolated = subprocess.run(
        [sys.executable, "-I", "-B", str(runner), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert isolated.returncode == 0
    assert "Owner-authorized Test 3 G2-P" in isolated.stdout


def test_real_isolated_import_graph_keeps_forbidden_gate_runnable() -> None:
    project_root = Path(g2p.__file__).parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            (
                "import sys; "
                "from mes_quant.exploration import test3_g2p_preflight as g; "
                "print('PANDAS_AMBIENT={}'.format('pandas' in sys.modules)); "
                "g._assert_forbidden_modules_absent(phase='real-import-graph-test'); "
                "print('FORBIDDEN_MODULE_GATE_PASS')"
            ),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "PANDAS_AMBIENT=True" in result.stdout
    assert "FORBIDDEN_MODULE_GATE_PASS" in result.stdout


def test_wrong_or_relative_cli_artifact_path_fails_before_consumption() -> None:
    project_root = Path(g2p.__file__).parents[3]
    common = [
        "--gate",
        g2p.G2P_GATE_LITERAL,
        "--authorization-token",
        g2p.G2P_AUTHORIZATION_TOKEN,
    ]
    with (
        patch.object(g2p, "_assert_isolated_runtime"),
        patch.object(g2p, "_consume_authorization") as consume,
        pytest.raises(g2p.Test3G2PBoundaryError, match="must be absolute"),
    ):
        g2p.main(
            [
                *common,
                "--cell8",
                g2p.CELL8_FILENAME,
                "--cell14-features",
                f"/private/tmp/{g2p.CELL14_FILENAME}",
            ],
            project_root=project_root,
        )
    consume.assert_not_called()

    with (
        patch.object(g2p, "_assert_isolated_runtime"),
        patch.object(g2p, "_consume_authorization") as consume,
        pytest.raises(g2p.Test3G2PBoundaryError, match="pinned canonical path"),
    ):
        g2p.main(
            [
                *common,
                "--cell8",
                "/private/tmp/wrong-cell8.parquet",
                "--cell14-features",
                f"/private/tmp/{g2p.CELL14_FILENAME}",
            ],
            project_root=project_root,
        )
    consume.assert_not_called()


def test_only_exact_pinned_cli_artifact_paths_are_accepted() -> None:
    project_root = Path(g2p.__file__).parents[3]
    cell8 = project_root / g2p.CELL8_CANONICAL_RELATIVE_PATH
    cell14 = project_root / g2p.CELL14_CANONICAL_RELATIVE_PATH
    assert g2p._validate_cli_artifact_paths(
        cell8,
        cell14,
        project_root=project_root,
    ) == (cell8, cell14)

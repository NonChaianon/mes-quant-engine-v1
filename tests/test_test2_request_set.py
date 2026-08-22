from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    DECODED_MES_1M_SHA256,
    EXPLORATION_SCOPE_ID,
    FEATURE_ARTIFACT_SHA256,
    FINAL_TEST_BOUNDARY_UTC,
    ORDERED_FEATURE_CONTENT_SHA256,
    OUTER_VALIDATION_BOUNDARY_UTC,
    PATH_OFFSETS,
    RAW_DBN_SHA256,
    STOP_TICKS,
    TAKE_PROFIT_TICKS,
)
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    RequestKey,
    RequestSetContractError,
    build_and_fetch_path_bars,
    build_request_set,
    build_streaming_request_set,
    fetch_path_bars,
    hash_request_set,
    hash_request_set_incremental,
    iter_path_bar_batches,
    iter_request_key_batches,
    iter_request_keys,
)


def _decision(
    identity: str,
    decision_time: datetime,
    role: str = "TRAIN",
) -> ParentDecision:
    return ParentDecision(identity, decision_time, role)


class RecordingProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.hash_was_ready = False
        self.returned: dict[RequestKey, object] = {}

    def fetch_path_bars(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> dict[RequestKey, object]:
        self.calls += 1
        self.hash_was_ready = bool(request_set_sha256) and request_set_sha256 == hash_request_set(
            request_keys
        )
        return self.returned


class StreamingRecordingProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[RequestKey, ...]] = []
        self.hashes: list[str] = []
        self.extra_key: RequestKey | None = None

    def fetch_path_bar_batch(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> dict[RequestKey, object]:
        self.calls.append(request_keys)
        self.hashes.append(request_set_sha256)
        if self.extra_key is not None:
            return {self.extra_key: object()}
        return {}


class Test2PathContractTests(unittest.TestCase):
    def test_frozen_request_contract_constants(self) -> None:
        self.assertEqual(EXPLORATION_SCOPE_ID, "MES_TEST2_PATH60_LONG_FLAT_FEATURE29_V1")
        self.assertEqual(PATH_OFFSETS, tuple(range(60)))
        self.assertEqual((TAKE_PROFIT_TICKS, STOP_TICKS), (16, 8))
        self.assertEqual(
            OUTER_VALIDATION_BOUNDARY_UTC,
            datetime(2024, 1, 2, 14, 45, tzinfo=UTC),
        )
        self.assertEqual(
            FINAL_TEST_BOUNDARY_UTC,
            datetime(2025, 1, 2, 14, 45, tzinfo=UTC),
        )
        self.assertEqual(
            CELL8_SPLIT_ASSIGNMENT_SHA256,
            "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035",
        )
        self.assertEqual(
            FEATURE_ARTIFACT_SHA256,
            "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452",
        )
        self.assertEqual(
            ORDERED_FEATURE_CONTENT_SHA256,
            "dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d",
        )
        self.assertEqual(
            DECODED_MES_1M_SHA256,
            "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584",
        )
        self.assertEqual(
            RAW_DBN_SHA256,
            "49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0",
        )


class Test2RequestSetTests(unittest.TestCase):
    def test_hash_exists_before_injected_provider_lookup(self) -> None:
        provider = RecordingProvider()
        sealed, rows = build_and_fetch_path_bars(
            [_decision("D1", datetime(2023, 6, 1, 15, 0, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
            provider=provider,
        )
        self.assertEqual(rows, {})
        self.assertEqual(provider.calls, 1)
        self.assertTrue(provider.hash_was_ready)
        self.assertEqual(sealed.request_set_sha256, hash_request_set(sealed.keys))

    def test_non_train_parent_roles_fail_before_provider_lookup(self) -> None:
        for role in ("VALIDATION", "FINAL_TEST"):
            with self.subTest(role=role):
                provider = RecordingProvider()
                with self.assertRaisesRegex(RequestSetContractError, "outer TRAIN"):
                    build_and_fetch_path_bars(
                        [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC), role)],
                        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
                        provider=provider,
                    )
                self.assertEqual(provider.calls, 0)

    def test_validation_timestamp_boundary_fails_before_provider_lookup(self) -> None:
        provider = RecordingProvider()
        last_offset_reaches_boundary = OUTER_VALIDATION_BOUNDARY_UTC - timedelta(minutes=59)
        with self.assertRaisesRegex(RequestSetContractError, "Validation=1"):
            build_and_fetch_path_bars(
                [_decision("D1", last_offset_reaches_boundary)],
                split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
                provider=provider,
            )
        self.assertEqual(provider.calls, 0)

    def test_final_test_timestamp_boundary_fails_before_provider_lookup(self) -> None:
        provider = RecordingProvider()
        with self.assertRaisesRegex(RequestSetContractError, "Final-Test=1"):
            build_and_fetch_path_bars(
                [_decision("D1", FINAL_TEST_BOUNDARY_UTC - timedelta(minutes=59))],
                split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
                provider=provider,
            )
        self.assertEqual(provider.calls, 0)

    def test_split_identity_is_required_and_exact(self) -> None:
        decisions = [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC))]
        with self.assertRaisesRegex(RequestSetContractError, "split-assignment"):
            build_request_set(decisions, split_assignment_sha256="0" * 64)
        with self.assertRaises(TypeError):
            build_request_set(decisions)  # type: ignore[call-arg]

    def test_order_and_hash_are_deterministic(self) -> None:
        timestamp = datetime(2023, 6, 1, 15, 0, tzinfo=UTC)
        decisions = [_decision("B", timestamp), _decision("A", timestamp)]
        first = build_request_set(
            decisions,
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        second = build_request_set(
            reversed(decisions),
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        self.assertEqual(first.keys, second.keys)
        self.assertEqual(first.request_set_sha256, second.request_set_sha256)
        self.assertEqual(len(first.keys), 120)
        self.assertEqual(first.keys[0].decision_identity, "A")
        self.assertEqual(first.keys[59].minute_offset, 59)
        self.assertEqual(first.keys[60].decision_identity, "B")
        self.assertNotEqual(hash_request_set(reversed(first.keys)), first.request_set_sha256)
        self.assertEqual(hash_request_set_incremental(first.keys), first.request_set_sha256)

    def test_streaming_seal_preserves_exact_hash_without_expanded_key_tuple(self) -> None:
        timestamp = datetime(2023, 6, 1, 15, 0, tzinfo=UTC)
        decisions = [_decision("B", timestamp), _decision("A", timestamp)]
        materialized = build_request_set(
            decisions,
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        streaming = build_streaming_request_set(
            decisions,
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        self.assertEqual(streaming.request_set_sha256, materialized.request_set_sha256)
        self.assertEqual(streaming.key_count, 120)
        self.assertEqual(tuple(iter_request_keys(streaming)), materialized.keys)
        self.assertFalse(hasattr(streaming, "keys"))

    def test_streaming_provider_is_called_only_after_whole_set_hash_is_valid(self) -> None:
        sealed = build_streaming_request_set(
            [_decision("D1", datetime(2023, 6, 1, 15, 0, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        provider = StreamingRecordingProvider()
        batches = tuple(iter_path_bar_batches(sealed, provider, batch_size=17))
        self.assertEqual(batches, ({}, {}, {}, {}))
        self.assertEqual([len(batch) for batch in provider.calls], [17, 17, 17, 9])
        self.assertEqual(set(provider.hashes), {sealed.request_set_sha256})

        provider = StreamingRecordingProvider()
        invalid = replace(sealed, request_set_sha256="0" * 64)
        with self.assertRaisesRegex(RequestSetContractError, "hashed before"):
            tuple(iter_path_bar_batches(invalid, provider, batch_size=17))
        self.assertEqual(provider.calls, [])

    def test_streaming_provider_rejects_unsealed_batch_key(self) -> None:
        sealed = build_streaming_request_set(
            [_decision("D1", datetime(2023, 6, 1, 15, 0, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        provider = StreamingRecordingProvider()
        provider.extra_key = RequestKey(
            "EXTRA",
            0,
            datetime(2023, 6, 1, 15, 0, tzinfo=UTC),
        )
        with self.assertRaisesRegex(RequestSetContractError, "unsealed key"):
            tuple(iter_path_bar_batches(sealed, provider, batch_size=60))

    def test_streaming_validator_recomputes_boundary_counters(self) -> None:
        safe = build_streaming_request_set(
            [_decision("A", datetime(2023, 1, 2, 14, 30, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        crossing_decision = ParentDecision(
            "A",
            OUTER_VALIDATION_BOUNDARY_UTC - timedelta(minutes=30),
            "TRAIN",
        )
        crossing = replace(
            safe,
            decisions=(crossing_decision,),
            parent_roles=(("A", "TRAIN"),),
            request_set_sha256=hash_request_set_incremental(
                RequestKey(
                    "A",
                    offset,
                    crossing_decision.decision_time_utc + timedelta(minutes=offset),
                )
                for offset in PATH_OFFSETS
            ),
            validation_path_bar_lookup_count=0,
            final_test_path_bar_lookup_count=0,
        )
        provider = StreamingRecordingProvider()
        with self.assertRaisesRegex(RequestSetContractError, "Validation lookup counter"):
            tuple(iter_path_bar_batches(crossing, provider, batch_size=60))
        self.assertEqual(provider.calls, [])

    def test_streaming_batch_size_fails_closed(self) -> None:
        sealed = build_streaming_request_set(
            [_decision("D1", datetime(2023, 6, 1, 15, 0, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        for invalid in (0, -1, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                RequestSetContractError, "batch_size"
            ):
                tuple(iter_request_key_batches(sealed, batch_size=invalid))  # type: ignore[arg-type]

    def test_streaming_seal_scales_past_one_million_keys_without_retaining_keys(self) -> None:
        start = datetime(2019, 5, 6, 13, 45, tzinfo=UTC)
        decisions = (
            _decision(f"D{index:05d}", start + timedelta(minutes=15 * index))
            for index in range(16_667)
        )
        sealed = build_streaming_request_set(
            decisions,
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        self.assertEqual(sealed.key_count, 1_000_020)
        self.assertEqual(len(sealed.decisions), 16_667)
        self.assertFalse(hasattr(sealed, "keys"))
        self.assertEqual(len(sealed.request_set_sha256), 64)

    def test_train_request_counts_are_zero_and_offsets_are_complete(self) -> None:
        sealed = build_request_set(
            [
                _decision("D1", datetime(2022, 6, 1, 15, 0, tzinfo=UTC)),
                _decision("D2", datetime(2023, 6, 1, 15, 0, tzinfo=UTC)),
            ],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        self.assertEqual(sealed.validation_path_bar_lookup_count, 0)
        self.assertEqual(sealed.final_test_path_bar_lookup_count, 0)
        self.assertEqual(len(sealed.keys), 2 * 60)
        for identity in ("D1", "D2"):
            self.assertEqual(
                tuple(key.minute_offset for key in sealed.keys if key.decision_identity == identity),
                PATH_OFFSETS,
            )

    def test_missing_or_mismatched_hash_blocks_before_provider_lookup(self) -> None:
        sealed = build_request_set(
            [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        for invalid in ("", "0" * 64):
            with self.subTest(invalid=invalid):
                provider = RecordingProvider()
                with self.assertRaisesRegex(RequestSetContractError, "hashed before"):
                    fetch_path_bars(replace(sealed, request_set_sha256=invalid), provider)
                self.assertEqual(provider.calls, 0)

    def test_provider_gate_revalidates_split_boundary_and_parent_roles(self) -> None:
        sealed = build_request_set(
            [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        provider = RecordingProvider()
        with self.assertRaisesRegex(RequestSetContractError, "split-assignment"):
            fetch_path_bars(replace(sealed, split_assignment_sha256="0" * 64), provider)
        self.assertEqual(provider.calls, 0)

        validation_key = RequestKey("D1", 59, OUTER_VALIDATION_BOUNDARY_UTC)
        validation_keys = sealed.keys + (validation_key,)
        with self.assertRaisesRegex(RequestSetContractError, "Validation lookup counter"):
            fetch_path_bars(
                replace(
                    sealed,
                    keys=validation_keys,
                    request_set_sha256=hash_request_set(validation_keys),
                ),
                provider,
            )
        self.assertEqual(provider.calls, 0)

        with self.assertRaisesRegex(RequestSetContractError, "outer TRAIN"):
            fetch_path_bars(
                replace(sealed, parent_roles=(("D1", "VALIDATION"),)),
                provider,
            )
        self.assertEqual(provider.calls, 0)

    def test_provider_cannot_return_unsealed_key(self) -> None:
        sealed = build_request_set(
            [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC))],
            split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
        )
        provider = RecordingProvider()
        provider.returned = {
            RequestKey("EXTRA", 0, datetime(2023, 6, 1, tzinfo=UTC)): object()
        }
        with self.assertRaisesRegex(RequestSetContractError, "unsealed key"):
            fetch_path_bars(sealed, provider)

    def test_naive_timestamp_and_duplicate_identity_fail_closed(self) -> None:
        with self.assertRaisesRegex(RequestSetContractError, "timezone-aware"):
            build_request_set(
                [_decision("D1", datetime(2023, 6, 1, tzinfo=UTC).replace(tzinfo=None))],
                split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
            )
        with self.assertRaisesRegex(RequestSetContractError, "unique"):
            build_request_set(
                [
                    _decision("D1", datetime(2023, 6, 1, tzinfo=UTC)),
                    _decision("D1", datetime(2023, 6, 2, tzinfo=UTC)),
                ],
                split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
            )


if __name__ == "__main__":
    unittest.main()

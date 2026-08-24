from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from mes_quant.core.hashing import sha256_file
from mes_quant.exploration.test2_decode import (
    CELL2_HASH_COLUMNS,
    CELL2_INDEX_NAME,
    databento_modules_loaded,
    decode_canonical_dbn,
    normalize_cell2_hash_frame,
)
from mes_quant.exploration.test2_decode import (
    Test2DecodeContractError as DecodeContractError,
)
from mes_quant.exploration.test2_l1_harness import (
    Test2HarnessContractError as HarnessContractError,
)
from mes_quant.exploration.test2_l1_harness import decoded_frame_content_sha256

# Column order as a Databento `DBNStore.to_df()` frame presents it: the OHLC
# block does not directly follow `instrument_id`, and extra columns surround it.
DECODED_COLUMN_ORDER = (
    "rtype",
    "publisher_id",
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "symbol",
)


def _decoded_like_frame(rows: int = 8) -> pd.DataFrame:
    index = pd.DatetimeIndex(
        pd.date_range("2022-06-01T14:30:00Z", periods=rows, freq="1min"),
        name=CELL2_INDEX_NAME,
    )
    closes = 5_000.0 + 0.25 * np.arange(rows, dtype=np.float64)
    return pd.DataFrame(
        {
            "rtype": np.full(rows, 34, dtype=np.uint8),
            "publisher_id": np.full(rows, 1, dtype=np.uint16),
            "instrument_id": np.full(rows, 123, dtype=np.uint32),
            "open": closes,
            "high": closes + 0.25,
            "low": closes - 0.25,
            "close": closes,
            "volume": np.arange(rows, dtype=np.uint64),
            "symbol": ["MESM2"] * rows,
        },
        index=index,
        columns=list(DECODED_COLUMN_ORDER),
    )


def _cell2_reference_sha256(frame: pd.DataFrame) -> str:
    """Recompute the Cell 2 addendum hash exactly as the frozen cell writes it."""

    row_hashes = pd.util.hash_pandas_object(
        frame[list(CELL2_HASH_COLUMNS)],
        index=True,
        categorize=False,
    ).to_numpy(dtype="uint64", copy=False)
    return hashlib.sha256(row_hashes.tobytes()).hexdigest()


class NormalizeCell2FrameTests(unittest.TestCase):
    def test_decoded_column_order_must_be_normalized_before_verification(self) -> None:
        frame = _decoded_like_frame()
        # The raw decoded order places instrument_id before the OHLC block, so
        # the frozen hash contract rejects it until it is projected.
        with self.assertRaisesRegex(HarnessContractError, "column order"):
            decoded_frame_content_sha256(frame)
        normalized = normalize_cell2_hash_frame(frame)
        self.assertEqual(tuple(normalized.columns), CELL2_HASH_COLUMNS)
        self.assertEqual(normalized.index.name, CELL2_INDEX_NAME)
        self.assertEqual(
            decoded_frame_content_sha256(normalized),
            _cell2_reference_sha256(frame),
        )

    def test_normalization_preserves_values_dtypes_and_row_order(self) -> None:
        frame = _decoded_like_frame()
        normalized = normalize_cell2_hash_frame(frame)
        for column in CELL2_HASH_COLUMNS:
            self.assertEqual(normalized[column].dtype, frame[column].dtype)
            self.assertTrue(normalized[column].equals(frame[column]))
        self.assertTrue(normalized.index.equals(frame.index))

    def test_ts_event_column_is_promoted_to_the_index(self) -> None:
        frame = _decoded_like_frame().reset_index()
        normalized = normalize_cell2_hash_frame(frame)
        self.assertEqual(tuple(normalized.columns), CELL2_HASH_COLUMNS)
        self.assertEqual(
            decoded_frame_content_sha256(normalized),
            _cell2_reference_sha256(_decoded_like_frame()),
        )

    def test_missing_hash_column_fails_closed(self) -> None:
        frame = _decoded_like_frame().drop(columns=["low"])
        with self.assertRaisesRegex(DecodeContractError, "lacks Cell 2 hash columns"):
            normalize_cell2_hash_frame(frame)

    def test_timezone_naive_index_fails_closed(self) -> None:
        frame = _decoded_like_frame()
        frame.index = frame.index.tz_localize(None)
        frame.index.name = CELL2_INDEX_NAME
        with self.assertRaisesRegex(DecodeContractError, "timezone-naive"):
            normalize_cell2_hash_frame(frame)

    def test_non_utc_index_fails_closed(self) -> None:
        frame = _decoded_like_frame()
        frame.index = frame.index.tz_convert("America/New_York")
        frame.index.name = CELL2_INDEX_NAME
        with self.assertRaisesRegex(DecodeContractError, "not UTC"):
            normalize_cell2_hash_frame(frame)

    def test_duplicate_and_unordered_timestamps_fail_closed(self) -> None:
        duplicated = _decoded_like_frame()
        duplicated.index = pd.DatetimeIndex(
            [duplicated.index[0]] * len(duplicated), name=CELL2_INDEX_NAME
        )
        with self.assertRaisesRegex(DecodeContractError, "duplicate timestamps"):
            normalize_cell2_hash_frame(duplicated)
        unordered = _decoded_like_frame().iloc[::-1]
        with self.assertRaisesRegex(DecodeContractError, "monotonic"):
            normalize_cell2_hash_frame(unordered)

    def test_wrong_index_name_is_not_silently_renamed(self) -> None:
        frame = _decoded_like_frame()
        frame.index = frame.index.rename("timestamp")
        with self.assertRaisesRegex(DecodeContractError, "index must be named"):
            normalize_cell2_hash_frame(frame)

    def test_missing_value_in_a_hash_column_fails_closed(self) -> None:
        frame = _decoded_like_frame()
        frame.loc[frame.index[2], "close"] = np.nan
        with self.assertRaisesRegex(DecodeContractError, "missing values"):
            normalize_cell2_hash_frame(frame)

    def test_empty_and_non_frame_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(DecodeContractError, "pandas DataFrame"):
            normalize_cell2_hash_frame(object())
        with self.assertRaisesRegex(DecodeContractError, "zero rows"):
            normalize_cell2_hash_frame(_decoded_like_frame().iloc[:0])


class DecodeCanonicalDbnTests(unittest.TestCase):
    def test_raw_byte_mismatch_stops_before_the_decoder_runs(self) -> None:
        calls: list[Path] = []

        def loader(source: Path) -> pd.DataFrame:
            calls.append(source)
            return _decoded_like_frame()

        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "MES_2019_2026_1m.dbn.zst"
            archive.write_bytes(b"synthetic archive bytes")
            with self.assertRaisesRegex(DecodeContractError, "byte SHA-256 mismatch"):
                decode_canonical_dbn(
                    archive,
                    expected_raw_sha256="0" * 64,
                    expected_decoded_sha256="1" * 64,
                    loader=loader,
                )
        self.assertEqual(calls, [])

    def test_decode_verifies_raw_bytes_then_normalized_content(self) -> None:
        frame = _decoded_like_frame()
        expected_content = _cell2_reference_sha256(frame)
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "MES_2019_2026_1m.dbn.zst"
            archive.write_bytes(b"synthetic archive bytes")
            decoded, evidence = decode_canonical_dbn(
                archive,
                expected_raw_sha256=sha256_file(archive),
                expected_decoded_sha256=expected_content,
                loader=lambda _source: _decoded_like_frame(),
            )
        self.assertEqual(tuple(decoded.columns), CELL2_HASH_COLUMNS)
        self.assertEqual(evidence.content_sha256, expected_content)
        self.assertEqual(evidence.row_count, len(frame))
        self.assertEqual(
            evidence.hash_scope,
            "FULL_CANONICAL_DECODED_FRAME_IDENTITY_ONLY_NOT_PATH_LOOKUP",
        )

    def test_decoded_content_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "MES_2019_2026_1m.dbn.zst"
            archive.write_bytes(b"synthetic archive bytes")
            with self.assertRaisesRegex(
                HarnessContractError, "content SHA-256 mismatch"
            ):
                decode_canonical_dbn(
                    archive,
                    expected_raw_sha256=sha256_file(archive),
                    expected_decoded_sha256="2" * 64,
                    loader=lambda _source: _decoded_like_frame(),
                )

    def test_missing_archive_fails_closed(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(DecodeContractError, "missing"),
        ):
            decode_canonical_dbn(
                Path(temporary) / "absent.dbn.zst",
                loader=lambda _source: _decoded_like_frame(),
            )


class LazyDecoderImportTests(unittest.TestCase):
    def test_importing_the_wrapper_does_not_load_a_dbn_decoder(self) -> None:
        self.assertIn("mes_quant.exploration.test2_decode", sys.modules)
        self.assertEqual(databento_modules_loaded(), ())


if __name__ == "__main__":
    unittest.main()

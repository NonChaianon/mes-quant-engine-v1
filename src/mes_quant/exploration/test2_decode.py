"""Canonical lazy Databento decode wrapper for the Test 2 G3 gate.

Cell 2 of the frozen Colab reference decodes the whole DBN archive with
``databento.DBNStore.from_file(path).to_df()`` and then fingerprints the exact
decoded object in memory:

```text
CELL2_MEMORY_HASH_COLUMNS = ["open", "high", "low", "close", "instrument_id"]
pd.util.hash_pandas_object(mes_1m[CELL2_MEMORY_HASH_COLUMNS], index=True,
                           categorize=False)
```

Two properties of that snippet are easy to lose and expensive to get wrong:

1. Cell 2 **selects** the five hash columns in that exact order. The decoded
   frame's own column order is different (`instrument_id` precedes the OHLC
   block), so a decoded frame must be normalized to the Cell 2 hash projection
   before its content hash can be recomputed or compared.
2. The hash includes the index, so the `ts_event` UTC index contract is part of
   the identity, not incidental metadata.

`databento` is already a pinned project dependency; it is imported lazily inside
the decoder so that importing this module never loads a DBN decoder. That keeps
the frozen G2 metadata-only module-absence witness valid.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from mes_quant.core.hashing import sha256_file
from mes_quant.exploration import test2_l1_harness as _harness
from mes_quant.exploration.test2_path_contract import (
    DECODED_MES_1M_SHA256,
    RAW_DBN_SHA256,
)

CELL2_HASH_COLUMNS = ("open", "high", "low", "close", "instrument_id")
CELL2_INDEX_NAME = "ts_event"
CELL2_HASH_ALGORITHM = "SHA256_OVER_PANDAS_UINT64_ROW_HASHES"
CELL2_HASH_INCLUDES_INDEX = True
CELL2_HASH_PROJECTION_ID = "CELL2_MEMORY_HASH_COLUMNS_ORDERED_UTC_TS_EVENT_INDEX_V1"

DECODED_CONTENT_STATUS_RECOMPUTED = "RECOMPUTED_FULL_CANONICAL_CELL2_DECODE"
DECODE_SCOPE = "FULL_CANONICAL_DECODED_FRAME_IDENTITY_ONLY_NOT_PATH_LOOKUP"

DBN_DECODER_MODULE_PREFIXES = ("databento", "databento_dbn")


class Test2DecodeContractError(RuntimeError):
    """Raised when a decode would misstate the canonical Cell 2 identity."""


def databento_modules_loaded() -> tuple[str, ...]:
    """Report currently imported DBN decoder modules for boundary witnesses."""

    return tuple(
        sorted(
            name
            for name in sys.modules
            if any(
                name == prefix or name.startswith(prefix + ".")
                for prefix in DBN_DECODER_MODULE_PREFIXES
            )
        )
    )


def _datetime_index(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.index, pd.DatetimeIndex):
        return frame
    if CELL2_INDEX_NAME not in frame.columns:
        raise Test2DecodeContractError(
            f"decoded frame needs a DatetimeIndex or a {CELL2_INDEX_NAME} column"
        )
    candidate = frame.set_index(CELL2_INDEX_NAME)
    if not isinstance(candidate.index, pd.DatetimeIndex):
        raise Test2DecodeContractError(
            f"{CELL2_INDEX_NAME} column is not a datetime index"
        )
    return candidate


def normalize_cell2_hash_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Project a decoded frame onto the exact Cell 2 hash column/index contract.

    The returned frame carries exactly `CELL2_HASH_COLUMNS` in Cell 2 order over
    the original tz-aware UTC `ts_event` index. Column order is normalized;
    values, dtypes, row order, and the index object are not altered.
    """

    if not isinstance(frame, pd.DataFrame):
        raise Test2DecodeContractError("decoded object must be a pandas DataFrame")
    if frame.columns.has_duplicates:
        raise Test2DecodeContractError("decoded frame contains duplicate columns")
    indexed = _datetime_index(frame)
    missing = [name for name in CELL2_HASH_COLUMNS if name not in indexed.columns]
    if missing:
        raise Test2DecodeContractError(
            "decoded frame lacks Cell 2 hash columns: " + ", ".join(missing)
        )
    if len(indexed) == 0:
        raise Test2DecodeContractError("decoded frame contains zero rows")

    index = indexed.index
    if index.name != CELL2_INDEX_NAME:
        raise Test2DecodeContractError(
            f"decoded frame index must be named {CELL2_INDEX_NAME}"
        )
    if index.tz is None:
        raise Test2DecodeContractError("decoded frame index is timezone-naive")
    if str(index.tz).upper() != "UTC":
        raise Test2DecodeContractError(
            f"decoded frame index timezone is not UTC: {index.tz}"
        )
    if index.has_duplicates:
        raise Test2DecodeContractError("decoded frame contains duplicate timestamps")
    if not index.is_monotonic_increasing:
        raise Test2DecodeContractError(
            "decoded frame timestamps are not monotonic increasing"
        )

    projected = indexed.loc[:, list(CELL2_HASH_COLUMNS)]
    if projected.isna().to_numpy().any():
        raise Test2DecodeContractError(
            "decoded frame exposes missing values in a Cell 2 hash column"
        )
    projected.attrs["test2_cell2_hash_projection"] = CELL2_HASH_PROJECTION_ID
    return projected


def _databento_to_df(source: Path) -> pd.DataFrame:
    # Imported lazily: importing this module must never load a DBN decoder.
    try:
        import databento as _databento
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise Test2DecodeContractError(
            "the pinned databento dependency is required to decode the canonical DBN"
        ) from exc
    return _databento.DBNStore.from_file(source).to_df()


def decode_canonical_dbn(
    path: str | Path,
    *,
    expected_raw_sha256: str = RAW_DBN_SHA256,
    expected_decoded_sha256: str = DECODED_MES_1M_SHA256,
    loader: Callable[[Path], pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, _harness.DecodedFrameIdentityEvidence]:
    """Reproduce the Cell 2 decode and verify both raw and decoded identities.

    The raw byte hash is checked before any decode is attempted, the decoded
    frame is normalized onto the Cell 2 hash projection, and only then is the
    frozen decoded content SHA-256 recomputed and compared. Any mismatch fails
    closed before a single path bar can be looked up.
    """

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise Test2DecodeContractError(f"canonical raw DBN is missing: {source}")
    observed_raw = sha256_file(source)
    if observed_raw != expected_raw_sha256:
        raise Test2DecodeContractError("canonical raw DBN byte SHA-256 mismatch")

    decoder = loader if loader is not None else _databento_to_df
    decoded = decoder(source)
    frame = normalize_cell2_hash_frame(decoded)
    evidence = _harness.verify_decoded_frame_identity(
        frame,
        expected_sha256=expected_decoded_sha256,
    )
    return frame, evidence


__all__ = [
    "CELL2_HASH_ALGORITHM",
    "CELL2_HASH_COLUMNS",
    "CELL2_HASH_INCLUDES_INDEX",
    "CELL2_HASH_PROJECTION_ID",
    "CELL2_INDEX_NAME",
    "DECODED_CONTENT_STATUS_RECOMPUTED",
    "DECODE_SCOPE",
    "Test2DecodeContractError",
    "databento_modules_loaded",
    "decode_canonical_dbn",
    "normalize_cell2_hash_frame",
]

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

VOLATILE_AUDIT_KEYS = frozenset({"audit_written_utc", "manifest_written_utc"})


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def canonicalize_audit(
    value: Any,
    *,
    artifact_roots: Iterable[str] = (),
    remove_keys: frozenset[str] = VOLATILE_AUDIT_KEYS,
) -> Any:
    """Remove only allowlisted volatile metadata and normalize artifact roots."""

    roots = tuple(str(root).replace("\\", "/").rstrip("/") for root in artifact_roots)

    def visit(item: Any) -> Any:
        if isinstance(item, dict):
            return {
                key: visit(child)
                for key, child in sorted(item.items())
                if key not in remove_keys
            }
        if isinstance(item, list):
            return [visit(child) for child in item]
        if isinstance(item, str):
            normalized = item.replace("\\", "/")
            for root in roots:
                if normalized == root or normalized.startswith(root + "/"):
                    return "${MES_ARTIFACT_ROOT}" + normalized[len(root) :]
            return normalized
        return item

    return visit(value)


def canonical_audit_sha256(path: str | Path, *, artifact_roots: Iterable[str] = ()) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    canonical = canonicalize_audit(payload, artifact_roots=artifact_roots)
    return sha256_bytes(canonical_json_bytes(canonical))


def dataframe_content_sha256(frame: Any, *, index: bool = False) -> str:
    """Hash ordered schema plus pandas row hashes; intended as cross-writer evidence."""

    import pandas as pd

    schema = [
        {
            "name": str(name),
            "dtype": str(frame[name].dtype),
        }
        for name in frame.columns
    ]
    digest = hashlib.sha256(canonical_json_bytes({"schema": schema, "index": index}))
    row_hashes = pd.util.hash_pandas_object(frame, index=index).to_numpy(dtype="uint64")
    digest.update(row_hashes.tobytes(order="C"))
    return digest.hexdigest()


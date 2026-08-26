from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from mes_quant.governance.execution_hardening import executed_frozen

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _minimal_registry(document_sha256: str) -> dict[str, object]:
    return {
        "schema_version": executed_frozen.REGISTRY_SCHEMA,
        "registry_id": executed_frozen.REGISTRY_ID,
        "status": executed_frozen.REGISTRY_STATUS,
        "entries": [
            {
                "path": executed_frozen.MANDATORY_FIRST_PATH,
                "authoritative_sha256": document_sha256,
                "authority_evidence": [
                    {
                        "role": "UNREAD_IDENTITY_ONLY",
                        "path": "artifacts/never-opened/evidence.json",
                        "sha256": "9" * 64,
                    }
                ],
            }
        ],
    }


def _write_checkout(root: Path, document: bytes) -> None:
    document_path = root / executed_frozen.MANDATORY_FIRST_PATH
    document_path.parent.mkdir(parents=True)
    document_path.write_bytes(document)
    registry_path = root / executed_frozen.REGISTRY_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(_minimal_registry(executed_frozen.MANDATORY_FIRST_SHA256)),
        encoding="utf-8",
    )


def test_repository_registry_verifies_exact_executed_frozen_bytes() -> None:
    result = executed_frozen.verify_executed_frozen_registry(PROJECT_ROOT)

    assert result.registry_id == executed_frozen.REGISTRY_ID
    assert result.checked_paths == (executed_frozen.MANDATORY_FIRST_PATH,)
    assert result.observed_sha256 == (executed_frozen.MANDATORY_FIRST_SHA256,)


def test_one_byte_registered_document_drift_fails_deterministically(tmp_path: Path) -> None:
    frozen_bytes = (PROJECT_ROOT / executed_frozen.MANDATORY_FIRST_PATH).read_bytes()
    _write_checkout(tmp_path, frozen_bytes)
    document_path = tmp_path / executed_frozen.MANDATORY_FIRST_PATH
    document_path.write_bytes(document_path.read_bytes() + b"X")

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="byte drift"):
        executed_frozen.verify_executed_frozen_registry(tmp_path)


def test_authority_evidence_identity_is_parsed_but_never_opened(tmp_path: Path) -> None:
    frozen_bytes = (PROJECT_ROOT / executed_frozen.MANDATORY_FIRST_PATH).read_bytes()
    _write_checkout(tmp_path, frozen_bytes)

    result = executed_frozen.verify_executed_frozen_registry(tmp_path)

    assert result.checked_paths == (executed_frozen.MANDATORY_FIRST_PATH,)
    assert not (tmp_path / "artifacts/never-opened/evidence.json").exists()


def test_registry_closed_field_sets_and_mandatory_first_entry() -> None:
    valid = _minimal_registry(executed_frozen.MANDATORY_FIRST_SHA256)
    assert executed_frozen.parse_executed_frozen_registry(valid).entries[0].path == (
        executed_frozen.MANDATORY_FIRST_PATH
    )

    extra = copy.deepcopy(valid)
    extra["unknown"] = True
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="field set"):
        executed_frozen.parse_executed_frozen_registry(extra)

    wrong_first = copy.deepcopy(valid)
    wrong_first["entries"][0]["path"] = "docs/research/OTHER.md"
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="mandatory first"):
        executed_frozen.parse_executed_frozen_registry(wrong_first)


def test_registry_rejects_duplicate_paths_and_unsafe_paths() -> None:
    valid = _minimal_registry(executed_frozen.MANDATORY_FIRST_SHA256)
    duplicate = copy.deepcopy(valid)
    duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="duplicate"):
        executed_frozen.parse_executed_frozen_registry(duplicate)

    unsafe = copy.deepcopy(valid)
    unsafe["entries"][0]["authority_evidence"][0]["path"] = "../artifact.json"
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="canonical"):
        executed_frozen.parse_executed_frozen_registry(unsafe)

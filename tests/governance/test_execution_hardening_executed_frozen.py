from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from mes_quant.governance.execution_hardening import executed_frozen

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _copy_companions(root: Path) -> None:
    for spec in executed_frozen.PHASE_A_COMPANION_SPECS:
        destination = root / spec.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / spec.path, destination)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), *args),
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _init_git_fixture(root: Path) -> tuple[str, str]:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "tier1@example.invalid")
    _git(root, "config", "user.name", "Tier1 Fixture")
    _copy_companions(root)
    protected = root / "docs/governance/PROTECTED_FIXTURE.md"
    protected.parent.mkdir(parents=True, exist_ok=True)
    protected.write_text("protected-v1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "synthetic fixture base")
    commit = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    return commit, tree


def _commit_file(root: Path, path: str, content: str, message: str) -> str:
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    _git(root, "add", "--", path)
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


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


def test_all_four_phase_a_companions_verify_fixed_path_hash_and_identity() -> None:
    result = executed_frozen.verify_phase_a_companions(PROJECT_ROOT)

    assert result.checked_paths == tuple(
        spec.path.as_posix() for spec in executed_frozen.PHASE_A_COMPANION_SPECS
    )
    assert result.observed_sha256 == tuple(
        spec.sha256 for spec in executed_frozen.PHASE_A_COMPANION_SPECS
    )
    assert result.observed_identities == tuple(
        spec.identity_value for spec in executed_frozen.PHASE_A_COMPANION_SPECS
    )


@pytest.mark.parametrize("companion_index", range(4))
def test_each_phase_a_companion_missing_fails_closed(
    tmp_path: Path,
    companion_index: int,
) -> None:
    _copy_companions(tmp_path)
    missing = tmp_path / executed_frozen.PHASE_A_COMPANION_SPECS[companion_index].path
    missing.unlink()

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="COMPANION_MISSING"):
        executed_frozen.verify_phase_a_companions(tmp_path)


@pytest.mark.parametrize("companion_index", range(4))
def test_each_phase_a_companion_one_byte_mismatch_fails_closed(
    tmp_path: Path,
    companion_index: int,
) -> None:
    _copy_companions(tmp_path)
    changed = tmp_path / executed_frozen.PHASE_A_COMPANION_SPECS[companion_index].path
    changed.write_bytes(changed.read_bytes() + b"X")

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="HASH_MISMATCH"):
        executed_frozen.verify_phase_a_companions(tmp_path)


def test_companion_identity_is_checked_after_exact_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_companions(tmp_path)
    original = executed_frozen.PHASE_A_COMPANION_SPECS[0]
    changed = tmp_path / original.path
    payload = json.loads(changed.read_text(encoding="utf-8"))
    payload[original.identity_field] = "WRONG_IDENTITY"
    changed.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    changed_spec = replace(original, sha256=hashlib.sha256(changed.read_bytes()).hexdigest())
    monkeypatch.setattr(
        executed_frozen,
        "PHASE_A_COMPANION_SPECS",
        (changed_spec, *executed_frozen.PHASE_A_COMPANION_SPECS[1:]),
    )

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="IDENTITY_MISMATCH"):
        executed_frozen.verify_phase_a_companions(tmp_path)


def test_protected_surface_actual_file_snapshot_is_stable(tmp_path: Path) -> None:
    _base, activation_tree = _init_git_fixture(tmp_path)

    before = executed_frozen.capture_protected_surface_snapshot(
        tmp_path,
        activation_tree=activation_tree,
    )
    after = executed_frozen.capture_protected_surface_snapshot(
        tmp_path,
        activation_tree=activation_tree,
    )

    assert "docs/governance/PROTECTED_FIXTURE.md" in before.paths
    assert before == after
    assert len(before.paths) == len(before.observed_sha256)
    assert len(before.canonical_sha256) == 64
    assert executed_frozen.compare_protected_surface_snapshots(before, after) is None


def test_protected_surface_committed_byte_delta_stops_comparison(tmp_path: Path) -> None:
    _base, activation_tree = _init_git_fixture(tmp_path)
    before = executed_frozen.capture_protected_surface_snapshot(
        tmp_path,
        activation_tree=activation_tree,
    )
    _commit_file(
        tmp_path,
        "docs/governance/PROTECTED_FIXTURE.md",
        "protected-v2\n",
        "mutate protected fixture",
    )
    after = executed_frozen.capture_protected_surface_snapshot(
        tmp_path,
        activation_tree=activation_tree,
    )

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="BYTE_HASH_CHANGED"):
        executed_frozen.compare_protected_surface_snapshots(before, after)


def test_protected_surface_missing_and_added_tracked_paths_fail_closed(tmp_path: Path) -> None:
    _base, activation_tree = _init_git_fixture(tmp_path)
    protected = tmp_path / "docs/governance/PROTECTED_FIXTURE.md"
    protected.unlink()
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="MISSING"):
        executed_frozen.capture_protected_surface_snapshot(
            tmp_path,
            activation_tree=activation_tree,
            require_clean_worktree=False,
        )

    protected.write_text("protected-v1\n", encoding="utf-8")
    _commit_file(
        tmp_path,
        "docs/governance/ADDED_PROTECTED.md",
        "extra\n",
        "add protected path",
    )
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="PATH_SET_CHANGED"):
        executed_frozen.capture_protected_surface_snapshot(
            tmp_path,
            activation_tree=activation_tree,
        )


def test_protected_surface_untracked_extra_and_symlink_fail_closed(tmp_path: Path) -> None:
    _base, activation_tree = _init_git_fixture(tmp_path)
    extra = tmp_path / "docs/governance/UNTRACKED_PROTECTED.md"
    extra.write_text("untracked\n", encoding="utf-8")
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="UNTRACKED_EXTRA"):
        executed_frozen.capture_protected_surface_snapshot(
            tmp_path,
            activation_tree=activation_tree,
            require_clean_worktree=False,
        )

    extra.unlink()
    protected = tmp_path / "docs/governance/PROTECTED_FIXTURE.md"
    protected.unlink()
    protected.symlink_to(tmp_path / executed_frozen.SURFACE_MAP_PATH)
    _git(tmp_path, "add", "--", protected.relative_to(tmp_path).as_posix())
    _git(tmp_path, "commit", "-qm", "replace protected path with symlink")
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="SYMLINK"):
        executed_frozen.capture_protected_surface_snapshot(
            tmp_path,
            activation_tree=activation_tree,
        )


def test_phase_a_and_phase_b_firewalls_accept_only_own_partition(tmp_path: Path) -> None:
    base, _tree = _init_git_fixture(tmp_path)
    phase_a_path = "src/mes_quant/governance/execution_hardening/boundary.py"
    phase_a_head = _commit_file(tmp_path, phase_a_path, "# phase a\n", "phase a path")

    phase_a = executed_frozen.verify_git_change_firewall(
        tmp_path,
        phase=executed_frozen.PHASE_A,
        base_commit=base,
        head_commit=phase_a_head,
    )
    assert phase_a.changed_paths == (phase_a_path,)
    assert phase_a.staged_paths == ()

    other_root = tmp_path / "phase-b-repo"
    other_root.mkdir()
    phase_b_base, _tree = _init_git_fixture(other_root)
    phase_b_path = "configs/governance/execution_hardening_attestation_ready_v1.json"
    phase_b_head = _commit_file(other_root, phase_b_path, "{}\n", "phase b path")
    phase_b = executed_frozen.verify_git_change_firewall(
        other_root,
        phase=executed_frozen.PHASE_B,
        base_commit=phase_b_base,
        head_commit=phase_b_head,
    )
    assert phase_b.changed_paths == (phase_b_path,)


def test_change_firewall_rejects_out_of_phase_and_staged_paths(tmp_path: Path) -> None:
    base, _tree = _init_git_fixture(tmp_path)
    phase_b_path = "configs/governance/execution_hardening_attestation_ready_v1.json"
    head = _commit_file(tmp_path, phase_b_path, "{}\n", "wrong phase")
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="OUT_OF_PHASE"):
        executed_frozen.verify_git_change_firewall(
            tmp_path,
            phase=executed_frozen.PHASE_A,
            base_commit=base,
            head_commit=head,
        )

    staged = tmp_path / phase_b_path
    staged.write_text('{"staged":true}\n', encoding="utf-8")
    _git(tmp_path, "add", "--", phase_b_path)
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="STAGED_NOT_EMPTY"):
        executed_frozen.verify_git_change_firewall(
            tmp_path,
            phase=executed_frozen.PHASE_B,
            base_commit=base,
            head_commit=head,
        )


def test_change_firewall_rejects_reciprocal_phase_and_outside_union(tmp_path: Path) -> None:
    base, _tree = _init_git_fixture(tmp_path)
    phase_a_path = "src/mes_quant/governance/execution_hardening/boundary.py"
    head = _commit_file(tmp_path, phase_a_path, "# phase a\n", "phase a path")
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="OUT_OF_PHASE"):
        executed_frozen.verify_git_change_firewall(
            tmp_path,
            phase=executed_frozen.PHASE_B,
            base_commit=base,
            head_commit=head,
        )

    outside_root = tmp_path / "outside-repo"
    outside_root.mkdir()
    outside_base, _tree = _init_git_fixture(outside_root)
    outside_head = _commit_file(
        outside_root,
        "src/outside_authorized_union.py",
        "# outside\n",
        "outside union",
    )
    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="OUT_OF_PHASE"):
        executed_frozen.verify_git_change_firewall(
            outside_root,
            phase=executed_frozen.PHASE_A,
            base_commit=outside_base,
            head_commit=outside_head,
        )


def test_change_firewall_rejects_head_other_than_checked_out_head(tmp_path: Path) -> None:
    base, _tree = _init_git_fixture(tmp_path)
    first_head = _commit_file(
        tmp_path,
        "src/mes_quant/governance/execution_hardening/boundary.py",
        "# first\n",
        "first head",
    )
    _commit_file(
        tmp_path,
        "src/mes_quant/governance/execution_hardening/records.py",
        "# second\n",
        "second head",
    )

    with pytest.raises(executed_frozen.ExecutedFrozenIntegrityError, match="HEAD_MISMATCH"):
        executed_frozen.verify_git_change_firewall(
            tmp_path,
            phase=executed_frozen.PHASE_A,
            base_commit=base,
            head_commit=first_head,
        )


@pytest.mark.parametrize("operation", ["delete", "rename"])
def test_change_firewall_rejects_deletion_and_rename(
    tmp_path: Path,
    operation: str,
) -> None:
    _base, _tree = _init_git_fixture(tmp_path)
    old_path = "src/mes_quant/governance/execution_hardening/boundary.py"
    _commit_file(tmp_path, old_path, "# original\n", "add allowed path")
    base = _git(tmp_path, "rev-parse", "HEAD")
    if operation == "delete":
        _git(tmp_path, "rm", "--", old_path)
    else:
        new_path = "src/mes_quant/governance/execution_hardening/records.py"
        _git(tmp_path, "mv", old_path, new_path)
    _git(tmp_path, "commit", "-qm", operation)
    head = _git(tmp_path, "rev-parse", "HEAD")

    with pytest.raises(
        executed_frozen.ExecutedFrozenIntegrityError,
        match="DELETION_OR_RENAME_FORBIDDEN",
    ):
        executed_frozen.verify_git_change_firewall(
            tmp_path,
            phase=executed_frozen.PHASE_A,
            base_commit=base,
            head_commit=head,
        )

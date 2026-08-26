from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUANT_CI = ROOT / ".github/workflows/quant-ci-v1.yml"
HARDENING_CI = ROOT / ".github/workflows/execution-hardening-attestation-v1.yml"
SURFACE_MAP = ROOT / "configs/governance/rehearsal_surface_map_v5.json"

QUANT_CI_PRE_CHANGE_SHA256 = (
    "ad685ad05c0da20b0f93f8477ee1e5939aea7f985ecf21bfc5b1abd9e136e071"
)
EXECUTED_FROZEN_STEP = """
      - name: Enforce executed-frozen byte integrity
        run: >-
          python -m pytest -p no:cacheprovider
          tests/governance/test_execution_hardening_executed_frozen.py
"""
PHASE_A_PATHS = (
    ".github/workflows/quant-ci-v1.yml",
    ".github/workflows/execution-hardening-attestation-v1.yml",
    "configs/governance/executed_frozen_registry_v1.json",
    "configs/governance/execution_hardening_attempt_ledger_schema_v1.json",
    "src/mes_quant/governance/execution_hardening/__init__.py",
    "src/mes_quant/governance/execution_hardening/boundary.py",
    "src/mes_quant/governance/execution_hardening/records.py",
    "src/mes_quant/governance/execution_hardening/attestation.py",
    "src/mes_quant/governance/execution_hardening/registry.py",
    "src/mes_quant/governance/execution_hardening/executed_frozen.py",
    "src/mes_quant/governance/execution_hardening/rehearsal.py",
    "tools/build_execution_hardening_review_report.py",
    "tools/run_execution_hardening_rehearsal.py",
    "tools/verify_execution_hardening_attestation.py",
    "tests/governance/test_execution_hardening_boundary.py",
    "tests/governance/test_execution_hardening_records.py",
    "tests/governance/test_execution_hardening_attestation.py",
    "tests/governance/test_execution_hardening_registry.py",
    "tests/governance/test_execution_hardening_executed_frozen.py",
    "tests/governance/test_execution_hardening_rehearsal.py",
    "tests/governance/test_execution_hardening_ci_spec.py",
    "docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_OWNER_AUTHORIZATION_V1.md",
    "docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1.md",
    (
        "docs/governance/clause_packets/"
        "CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_DISPATCH_RECEIPT.md"
    ),
    (
        "docs/governance/clause_packets/"
        "CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_RESPONSE.md"
    ),
    (
        "docs/governance/clause_packets/"
        "CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_OWNER_CLOSEOUT.md"
    ),
    (
        "docs/governance/clause_packets/"
        "CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_CLOSEOUT_RECEIPT.md"
    ),
    "docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_CLOSEOUT_MANIFEST_V1.json",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_quant_ci_change_is_only_executed_frozen_integrity() -> None:
    current = _read(QUANT_CI)
    assert current.count(EXECUTED_FROZEN_STEP) == 1
    reconstructed = current.replace(EXECUTED_FROZEN_STEP, "", 1)
    assert _sha256_text(reconstructed) == QUANT_CI_PRE_CHANGE_SHA256
    assert "id-token: write" not in current
    assert "attestations: write" not in current
    assert "pull_request_target" not in current


def test_hardening_workflow_is_non_authoritative_on_pull_requests() -> None:
    workflow = _read(HARDENING_CI)
    assert "pull_request_target" not in workflow
    assert "auto-merge" not in workflow.lower()
    assert "gh api" not in workflow.lower()
    assert "git push" not in workflow.lower()
    assert "curl " not in workflow.lower()
    assert "MES_EXECUTION_HARDENING_MODE: TIER1_ONLY_NON_AUTHORITATIVE" in workflow
    assert "if: github.event_name == 'pull_request'" in workflow
    assert workflow.count("contents: read") >= 4


def test_signer_is_unreachable_without_separate_phase_b_readiness() -> None:
    workflow = _read(HARDENING_CI)
    assert "if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'" in workflow
    assert "needs: phase-b-readiness" in workflow
    assert "if: needs.phase-b-readiness.outputs.ready == 'true'" in workflow
    assert "configs/governance/execution_hardening_attestation_ready_v1.json" in workflow
    assert "configs/governance/sigstore_trusted_root_v1.jsonl" in workflow
    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in workflow
    assert "predicate-type: https://slsa.dev/provenance/v1" in workflow


def test_hardening_workflow_runs_only_the_exact_tier1_test_set() -> None:
    workflow = _read(HARDENING_CI)
    for path in PHASE_A_PATHS[14:21]:
        assert workflow.count(path) >= 1
    assert "tests/test_test3" not in workflow
    assert "tools/run_test3" not in workflow


def test_surface_map_phase_a_partition_is_exact() -> None:
    surface_map = json.loads(_read(SURFACE_MAP))
    all_paths = tuple(surface_map["implementation_source_paths"])
    phase_a = tuple(all_paths[index - 1] for index in (1, 2, 3, *range(6, 25), *range(26, 32)))
    phase_b = tuple(all_paths[index - 1] for index in (4, 5, 25, *range(32, 38)))
    assert phase_a == PHASE_A_PATHS
    assert len(phase_a) == len(set(phase_a)) == 28
    assert len(phase_b) == len(set(phase_b)) == 9
    assert set(phase_a).isdisjoint(phase_b)
    assert set(phase_a) | set(phase_b) == set(all_paths)

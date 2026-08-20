from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.frozen_inputs import (
    load_frozen_inputs,
)
from mes_quant.governance.classification.git_delta import (
    canonical_git_tree_delta,
)
from mes_quant.governance.classification.relation import (
    validate_candidate_relation,
)
from mes_quant.governance.sentinel.orchestrator import (
    GovernanceSentinelOrchestrationError,
    evaluate_governance_candidate,
)
from tests.governance._frozen_fixture import (
    FROZEN_INPUT_PATHS,
    read_frozen_bytes,
)

MANIFEST_PATH = Path(
    "configs/governance/PROTECTED_SURFACE_MANIFEST_V1.json"
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class CandidateRepo:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)

        subprocess.run(
            ["git", "init", "-q", str(self.repo)],
            check=True,
        )

        git(self.repo, "config", "user.name", "MES Test")
        git(
            self.repo,
            "config",
            "user.email",
            "mes-test@example.invalid",
        )

        for relative_path in FROZEN_INPUT_PATHS:
            destination = self.repo / relative_path
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_bytes(
                read_frozen_bytes(
                    PROJECT_ROOT,
                    relative_path,
                )
            )

        ordinary = (
            self.repo
            / "src/mes_quant/features/builder.py"
        )
        ordinary.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        ordinary.write_text(
            "VALUE = 1\n",
            encoding="utf-8",
            newline="\n",
        )

        git(self.repo, "add", ".")
        git(
            self.repo,
            "commit",
            "-q",
            "-m",
            "sentinel test base",
        )

        self.base = git(
            self.repo,
            "rev-parse",
            "HEAD",
        )

    def commit(self, message: str) -> str:
        git(self.repo, "add", "-A")
        git(
            self.repo,
            "commit",
            "-q",
            "-m",
            message,
        )
        return git(
            self.repo,
            "rev-parse",
            "HEAD",
        )

    def close(self) -> None:
        self.temp.cleanup()


def evaluate_candidate(
    fixture: CandidateRepo,
    head: str,
):
    relation = validate_candidate_relation(
        fixture.repo,
        base_commit_sha1=fixture.base,
        head_commit_sha1=head,
    )
    frozen = load_frozen_inputs(
        fixture.repo,
        authority_commit_sha1=(
            relation.base_commit_sha1
        ),
    )
    delta = canonical_git_tree_delta(
        fixture.repo,
        base_commit_sha1=(
            relation.base_commit_sha1
        ),
        head_commit_sha1=(
            relation.head_commit_sha1
        ),
        max_tree_delta_entries=(
            frozen.analyzer_limits[
                "max_tree_delta_entries"
            ]
        ),
    )
    return evaluate_governance_candidate(
        fixture.repo,
        canonical_tree_delta=delta,
        predecessor_manifest=(
            frozen.protected_surface_manifest
        ),
        analyzer_limits=(
            frozen.analyzer_limits
        ),
    )


class GovernanceSentinelOrchestratorTests(unittest.TestCase):
    def make_repo(self) -> CandidateRepo:
        fixture = CandidateRepo()
        self.addCleanup(fixture.close)
        return fixture

    def test_ordinary_candidate_allows_classifier_routing(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = (
            fixture.repo
            / "src/mes_quant/features/builder.py"
        )
        path.write_text(
            "VALUE = 2\n",
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit("ordinary candidate")

        result = evaluate_candidate(
            fixture,
            head,
        )

        self.assertFalse(
            result.bootstrap_surface_hit
        )
        self.assertFalse(
            result.manifest_weakening_detected
        )

    def test_governance_spec_change_is_left_to_path_classification(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = (
            fixture.repo
            / "docs/governance/"
            "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
        )

        path.write_bytes(
            path.read_bytes()
            + b"\nUNTRUSTED CANDIDATE CHANGE\n"
        )

        head = fixture.commit(
            "candidate governance change"
        )

        result = evaluate_candidate(
            fixture,
            head,
        )

        self.assertFalse(
            result.bootstrap_surface_hit
        )
        self.assertFalse(
            result.manifest_weakening_detected
        )

    def test_manifest_shrink_is_detected_from_candidate_blob(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH

        payload = json.loads(
            path.read_text(encoding="utf-8")
        )

        payload[
            "governance_control_exact_paths"
        ].remove(
            "docs/governance/"
            "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
        )

        path.write_text(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "candidate manifest shrink"
        )

        result = evaluate_candidate(
            fixture,
            head,
        )

        self.assertTrue(
            result.manifest_weakening_detected
        )
        self.assertIn(
            "removed:governance_control_exact_paths:"
            "docs/governance/"
            "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md",
            result.weakening_details,
        )

    def test_malformed_candidate_manifest_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH
        path.write_bytes(b"{broken-json\n")

        head = fixture.commit(
            "malformed manifest"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            evaluate_candidate(
                fixture,
                head,
            )

    def test_deleted_candidate_manifest_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        (fixture.repo / MANIFEST_PATH).unlink()

        head = fixture.commit(
            "delete manifest"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            evaluate_candidate(
                fixture,
                head,
            )

    def test_invalid_predecessor_authority_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = (
            fixture.repo
            / "src/mes_quant/features/builder.py"
        )
        path.write_text(
            "VALUE = 3\n",
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "ordinary candidate"
        )

        relation = validate_candidate_relation(
            fixture.repo,
            base_commit_sha1=fixture.base,
            head_commit_sha1=head,
        )
        frozen = load_frozen_inputs(
            fixture.repo,
            authority_commit_sha1=fixture.base,
        )
        delta = canonical_git_tree_delta(
            fixture.repo,
            base_commit_sha1=(
                relation.base_commit_sha1
            ),
            head_commit_sha1=(
                relation.head_commit_sha1
            ),
            max_tree_delta_entries=(
                frozen.analyzer_limits[
                    "max_tree_delta_entries"
                ]
            ),
        )
        invalid_manifest = dict(
            frozen.protected_surface_manifest
        )
        invalid_manifest["schema"] = (
            "UNTRUSTED_SCHEMA"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            evaluate_governance_candidate(
                fixture.repo,
                canonical_tree_delta=delta,
                predecessor_manifest=(
                    invalid_manifest
                ),
                analyzer_limits=(
                    frozen.analyzer_limits
                ),
            )


if __name__ == "__main__":
    unittest.main()

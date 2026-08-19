from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.relation import (
    CandidateRelationError,
    validate_candidate_relation,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class CandidateRelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        _git(self.repo, "config", "user.name", "MES Test")
        _git(self.repo, "config", "user.email", "mes-test@example.invalid")

        (self.repo / "a.txt").write_text("a\n", encoding="utf-8")
        _git(self.repo, "add", "a.txt")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = _git(self.repo, "rev-parse", "HEAD")

        (self.repo / "a.txt").write_text("b\n", encoding="utf-8")
        _git(self.repo, "commit", "-qam", "head")
        self.head = _git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_single_commit_relation(self) -> None:
        relation = validate_candidate_relation(
            self.repo, base_commit_sha1=self.base, head_commit_sha1=self.head
        )
        self.assertEqual(relation.parent_count, 1)
        self.assertEqual(relation.merge_base_sha1, self.base)
        self.assertEqual(relation.base_commit_sha1, self.base)
        self.assertEqual(relation.head_commit_sha1, self.head)

    def test_two_commit_distance_is_rejected(self) -> None:
        (self.repo / "b.txt").write_text("c\n", encoding="utf-8")
        _git(self.repo, "add", "b.txt")
        _git(self.repo, "commit", "-q", "-m", "third")
        third = _git(self.repo, "rev-parse", "HEAD")
        with self.assertRaises(CandidateRelationError):
            validate_candidate_relation(
                self.repo, base_commit_sha1=self.base, head_commit_sha1=third
            )

    def test_replace_ref_cannot_change_candidate_relation(self) -> None:
        head_tree = _git(self.repo, "rev-parse", f"{self.head}^{{tree}}")
        replacement = subprocess.check_output(
            ["git", "-C", str(self.repo), "commit-tree", head_tree, "-m", "replacement"],
            text=True,
        ).strip()
        _git(self.repo, "replace", self.head, replacement)

        replaced_parent_tokens = _git(
            self.repo, "rev-list", "--parents", "-n", "1", self.head
        ).split()
        self.assertEqual(len(replaced_parent_tokens), 1)

        relation = validate_candidate_relation(
            self.repo, base_commit_sha1=self.base, head_commit_sha1=self.head
        )
        self.assertEqual(relation.parent_count, 1)
        self.assertEqual(relation.merge_base_sha1, self.base)


if __name__ == "__main__":
    unittest.main()

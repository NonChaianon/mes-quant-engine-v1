from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.git_delta import (
    GitDeltaError,
    canonical_git_tree_delta,
)

MAX_TREE_DELTA_ENTRIES = 50_000


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _entries_by_path(repo: Path, base: str, head: str) -> dict[str, object]:
    entries = canonical_git_tree_delta(
        repo,
        base_commit_sha1=base,
        head_commit_sha1=head,
        max_tree_delta_entries=MAX_TREE_DELTA_ENTRIES,
    )
    return {
        (entry.new_path_bytes or entry.old_path_bytes).decode("ascii"): entry
        for entry in entries
    }


class GitDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        _git(self.repo, "config", "user.name", "MES Test")
        _git(self.repo, "config", "user.email", "mes-test@example.invalid")

        (self.repo / "delete.txt").write_text("delete\n", encoding="utf-8")
        (self.repo / "modify.txt").write_text("old\n", encoding="utf-8")
        (self.repo / "mode.txt").write_text("mode\n", encoding="utf-8")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = _git(self.repo, "rev-parse", "HEAD")

        (self.repo / "delete.txt").unlink()
        (self.repo / "modify.txt").write_text("new\n", encoding="utf-8")
        (self.repo / "add.txt").write_text("add\n", encoding="utf-8")
        os.chmod(self.repo / "mode.txt", 0o755)
        (self.repo / "link.txt").symlink_to("modify.txt")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "head")
        self.head = _git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_delta_operations_and_raw_path_encoding(self) -> None:
        by_path = _entries_by_path(self.repo, self.base, self.head)

        self.assertEqual(by_path["add.txt"].operation, "ADD")
        self.assertEqual(by_path["delete.txt"].operation, "DELETE")
        self.assertEqual(by_path["modify.txt"].operation, "MODIFY")
        self.assertEqual(by_path["mode.txt"].operation, "FILE_MODE_CHANGE")
        self.assertEqual(by_path["link.txt"].operation, "ADD")
        self.assertEqual(by_path["link.txt"].new_mode, "120000")
        self.assertIsNone(by_path["add.txt"].old_path_bytes)
        self.assertIsNone(by_path["delete.txt"].new_path_bytes)

        record = by_path["modify.txt"].to_record()
        self.assertEqual(record["operation"], "MODIFY")
        self.assertIsInstance(record["new_path_bytes_base64"], str)

    def test_symlink_target_change_is_explicit(self) -> None:
        base = self.head
        (self.repo / "link.txt").unlink()
        (self.repo / "link.txt").symlink_to("mode.txt")
        _git(self.repo, "add", "link.txt")
        _git(self.repo, "commit", "-q", "-m", "change symlink target")
        head = _git(self.repo, "rev-parse", "HEAD")

        by_path = _entries_by_path(self.repo, base, head)
        self.assertEqual(by_path["link.txt"].operation, "SYMLINK_CHANGE")
        self.assertEqual(by_path["link.txt"].old_mode, "120000")
        self.assertEqual(by_path["link.txt"].new_mode, "120000")

    def test_submodule_pointer_change_is_explicit(self) -> None:
        old_cacheinfo = f"160000,{self.base},vendor/submodule"
        _git(self.repo, "update-index", "--add", "--cacheinfo", old_cacheinfo)
        _git(self.repo, "commit", "-q", "-m", "add gitlink")
        base = _git(self.repo, "rev-parse", "HEAD")

        new_cacheinfo = f"160000,{self.head},vendor/submodule"
        _git(self.repo, "update-index", "--cacheinfo", new_cacheinfo)
        _git(self.repo, "commit", "-q", "-m", "move gitlink")
        head = _git(self.repo, "rev-parse", "HEAD")

        by_path = _entries_by_path(self.repo, base, head)
        entry = by_path["vendor/submodule"]
        self.assertEqual(entry.operation, "SUBMODULE_POINTER_CHANGE")
        self.assertEqual(entry.old_object_type, "commit")
        self.assertEqual(entry.new_object_type, "commit")

    def test_tree_delta_entry_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            GitDeltaError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            canonical_git_tree_delta(
                self.repo,
                base_commit_sha1=self.base,
                head_commit_sha1=self.head,
                max_tree_delta_entries=2,
            )

    def test_tree_delta_entry_limit_must_be_positive_integer(self) -> None:
        for invalid_limit in (0, -1, True):
            with self.subTest(invalid_limit=invalid_limit):
                with self.assertRaises(GitDeltaError):
                    canonical_git_tree_delta(
                        self.repo,
                        base_commit_sha1=self.base,
                        head_commit_sha1=self.head,
                        max_tree_delta_entries=invalid_limit,
                    )

    def test_replace_ref_cannot_change_tree_delta(self) -> None:
        base_tree = _git(self.repo, "rev-parse", f"{self.base}^{{tree}}")
        replacement = subprocess.check_output(
            [
                "git",
                "-C",
                str(self.repo),
                "commit-tree",
                base_tree,
                "-p",
                self.base,
                "-m",
                "replacement",
            ],
            text=True,
        ).strip()
        _git(self.repo, "replace", self.head, replacement)

        by_path = _entries_by_path(self.repo, self.base, self.head)
        self.assertEqual(by_path["modify.txt"].operation, "MODIFY")
        self.assertEqual(by_path["mode.txt"].operation, "FILE_MODE_CHANGE")


if __name__ == "__main__":
    unittest.main()

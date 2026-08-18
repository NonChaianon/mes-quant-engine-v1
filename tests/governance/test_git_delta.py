from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.git_delta import canonical_git_tree_delta


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


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
        entries = canonical_git_tree_delta(
            self.repo, base_commit_sha1=self.base, head_commit_sha1=self.head
        )
        by_path = {
            (entry.new_path_bytes or entry.old_path_bytes).decode("ascii"): entry
            for entry in entries
        }

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


if __name__ == "__main__":
    unittest.main()

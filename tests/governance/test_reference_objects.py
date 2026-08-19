from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.reference_objects import (
    ReferenceObjectError,
    list_tracked_objects,
    read_blob_bytes,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class ReferenceObjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)

        subprocess.run(
            ["git", "init", "-q", str(self.repo)],
            check=True,
        )
        _git(self.repo, "config", "user.name", "MES Test")
        _git(
            self.repo,
            "config",
            "user.email",
            "mes-test@example.invalid",
        )

        (self.repo / "module.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        (self.repo / "config.json").write_text(
            '{"enabled":true}\n',
            encoding="utf-8",
        )
        (self.repo / "target.txt").write_text(
            "target\n",
            encoding="utf-8",
        )
        (self.repo / "link.txt").symlink_to("target.txt")

        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "base")

        self.head = _git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_enumerates_exact_tree_without_checkout_execution(self) -> None:
        objects = list_tracked_objects(
            self.repo,
            commit_sha1=self.head,
            max_tracked_objects=100,
        )

        by_path = {
            item.path_bytes: item
            for item in objects
        }

        self.assertEqual(
            set(by_path),
            {
                b"config.json",
                b"link.txt",
                b"module.py",
                b"target.txt",
            },
        )
        self.assertEqual(
            by_path[b"module.py"].mode,
            "100644",
        )
        self.assertEqual(
            by_path[b"module.py"].object_type,
            "blob",
        )
        self.assertEqual(
            by_path[b"link.txt"].mode,
            "120000",
        )

    def test_symlink_is_read_only_as_target_blob_bytes(self) -> None:
        objects = list_tracked_objects(
            self.repo,
            commit_sha1=self.head,
            max_tracked_objects=100,
        )

        link = next(
            item
            for item in objects
            if item.path_bytes == b"link.txt"
        )

        content = read_blob_bytes(
            self.repo,
            blob_sha1=link.object_sha1,
            max_blob_bytes=1024,
        )

        self.assertEqual(content, b"target.txt")

    def test_tracked_object_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceObjectError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            list_tracked_objects(
                self.repo,
                commit_sha1=self.head,
                max_tracked_objects=2,
            )

    def test_blob_limit_fails_before_blob_read(self) -> None:
        objects = list_tracked_objects(
            self.repo,
            commit_sha1=self.head,
            max_tracked_objects=100,
        )

        module = next(
            item
            for item in objects
            if item.path_bytes == b"module.py"
        )

        with self.assertRaisesRegex(
            ReferenceObjectError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            read_blob_bytes(
                self.repo,
                blob_sha1=module.object_sha1,
                max_blob_bytes=1,
            )

    def test_replace_ref_does_not_change_enumerated_tree(self) -> None:
        original_paths = tuple(
            item.path_bytes
            for item in list_tracked_objects(
                self.repo,
                commit_sha1=self.head,
                max_tracked_objects=100,
            )
        )

        tree = _git(self.repo, "rev-parse", f"{self.head}^{{tree}}")

        replacement = subprocess.check_output(
            [
                "git",
                "-C",
                str(self.repo),
                "commit-tree",
                tree,
                "-p",
                self.head,
                "-m",
                "replacement",
            ],
            text=True,
        ).strip()

        _git(
            self.repo,
            "replace",
            self.head,
            replacement,
        )

        observed_paths = tuple(
            item.path_bytes
            for item in list_tracked_objects(
                self.repo,
                commit_sha1=self.head,
                max_tracked_objects=100,
            )
        )

        self.assertEqual(observed_paths, original_paths)


if __name__ == "__main__":
    unittest.main()

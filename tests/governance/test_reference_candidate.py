from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.git_delta import (
    canonical_git_tree_delta,
)
from mes_quant.governance.classification.reference_candidate import (
    ReferenceCandidateError,
    analyze_reference_candidate,
)
from mes_quant.governance.classification.reference_analysis import (
    analyze_reference_snapshot as real_analyze_reference_snapshot,
)


LIMITS = {
    "max_tracked_objects": 10_000,
    "max_blob_bytes": 1_000_000,
    "max_ast_nodes": 100_000,
    "max_parse_depth": 128,
    "max_config_nesting_depth": 128,
    "max_scalar_bytes": 100_000,
    "max_collection_cardinality": 10_000,
    "max_graph_nodes": 100_000,
    "max_graph_edges": 100_000,
    "max_unresolved_nodes": 10_000,
    "max_unsupported_reference_file_types": 100,
}


def _manifest(
    *,
    protected_modules=("mes_quant.features",),
    protected_symbols=(),
):
    return {
        "protected_quant_exact_paths": [],
        "protected_quant_prefixes": [],
        "protected_artifact_prefixes": [],
        "protected_schema_prefixes": [],
        "protected_quant_modules": list(
            protected_modules
        ),
        "protected_symbols": list(
            protected_symbols
        ),
    }


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class ReferenceCandidateTests(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(
        self,
        relative_path: str,
        content: str,
    ) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            content,
            encoding="utf-8",
        )

    def _commit(self, message: str) -> str:
        _git(self.repo, "add", "-A")
        _git(
            self.repo,
            "commit",
            "-q",
            "-m",
            message,
        )
        return _git(
            self.repo,
            "rev-parse",
            "HEAD",
        )

    def _delta(
        self,
        base: str,
        head: str,
    ):
        return canonical_git_tree_delta(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            max_tree_delta_entries=10_000,
        )

    def _write_protected_package(self) -> None:
        self._write(
            "lib/mes_quant/__init__.py",
            "",
        )
        self._write(
            "lib/mes_quant/features/__init__.py",
            "",
        )
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )

    def test_deleted_file_cannot_hide_base_reference_to_protected(self) -> None:
        self._write_protected_package()
        self._write(
            "app/__init__.py",
            "",
        )
        self._write(
            "app/view.py",
            "import mes_quant.features.builder\n",
        )

        base = self._commit("base")

        (self.repo / "app/view.py").unlink()
        head = self._commit("delete view")

        result = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=self._delta(
                base,
                head,
            ),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertEqual(
            result.base_changed_nodes,
            (b"app/view.py",),
        )
        self.assertEqual(
            result.head_changed_nodes,
            (),
        )
        self.assertIsNotNone(
            result.base_snapshot
        )
        self.assertIsNone(
            result.head_snapshot
        )
        self.assertTrue(
            result.combined.graph_analysis
            .forward.reachable_protected
        )

    def test_added_file_is_analyzed_from_head_snapshot(self) -> None:
        self._write_protected_package()
        base = self._commit("base")

        self._write(
            "app/__init__.py",
            "",
        )
        self._write(
            "app/view.py",
            "import mes_quant.features.builder\n",
        )
        head = self._commit("add view")

        result = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=self._delta(
                base,
                head,
            ),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertEqual(
            result.base_changed_nodes,
            (),
        )
        self.assertIn(
            b"app/view.py",
            result.head_changed_nodes,
        )
        self.assertIsNone(
            result.base_snapshot
        )
        self.assertIsNotNone(
            result.head_snapshot
        )
        self.assertTrue(
            result.combined.graph_analysis
            .forward.reachable_protected
        )

    def test_base_unresolved_behavior_survives_clean_head(self) -> None:
        self._write_protected_package()
        self._write(
            "app/__init__.py",
            "",
        )
        self._write(
            "app/view.py",
            (
                "import importlib\n"
                "name = 'mes_quant.' + 'features'\n"
                "importlib.import_module(name)\n"
            ),
        )

        base = self._commit("base")

        self._write(
            "app/view.py",
            "VALUE = 1\n",
        )
        head = self._commit("remove dynamic import")

        result = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=self._delta(
                base,
                head,
            ),
            manifest=_manifest(),
            limits=LIMITS,
        )

        unresolved = {
            (
                item.path_bytes,
                item.reason_code,
                item.reference_kind,
            )
            for item in result.combined.unresolved_nodes
        }

        self.assertIn(
            (
                b"app/view.py",
                "DYNAMIC_IMPORT",
                "DYNAMIC",
            ),
            unresolved,
        )
        self.assertEqual(
            result.combined.graph_analysis
            .forward.unresolved_count,
            1,
        )

    def test_modified_path_is_analyzed_in_both_epochs(self) -> None:
        self._write(
            "config.json",
            '{"module":"old.value"}\n',
        )
        base = self._commit("base")

        self._write(
            "config.json",
            '{"module":"new.value"}\n',
        )
        head = self._commit("modify")

        result = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=self._delta(
                base,
                head,
            ),
            manifest=_manifest(
                protected_modules=(),
            ),
            limits=LIMITS,
        )

        self.assertEqual(
            result.base_changed_nodes,
            (b"config.json",),
        )
        self.assertEqual(
            result.head_changed_nodes,
            (b"config.json",),
        )
        self.assertIsNotNone(
            result.base_snapshot
        )
        self.assertIsNotNone(
            result.head_snapshot
        )
        self.assertEqual(
            result.combined.reference_scan_summary
            .scanned_tracked_objects,
            2,
        )

    def test_tracked_object_budget_is_shared_across_epochs(self) -> None:
        self._write(
            "config.json",
            '{"value":"base"}\n',
        )
        base = self._commit("base")

        self._write(
            "config.json",
            '{"value":"head"}\n',
        )
        head = self._commit("head")

        limits = dict(LIMITS)
        limits["max_tracked_objects"] = 1

        with self.assertRaisesRegex(
            ReferenceCandidateError,
            "max_tracked_objects",
        ):
            analyze_reference_candidate(
                self.repo,
                base_commit_sha1=base,
                head_commit_sha1=head,
                canonical_tree_delta=self._delta(
                    base,
                    head,
                ),
                manifest=_manifest(
                    protected_modules=(),
                ),
                limits=limits,
            )

    def test_candidate_result_is_deterministic_under_delta_reordering(
        self,
    ) -> None:
        self._write(
            "a.json",
            '{"value":"base-a"}\n',
        )
        self._write(
            "b.json",
            '{"value":"base-b"}\n',
        )
        base = self._commit("base")

        self._write(
            "a.json",
            '{"value":"head-a"}\n',
        )
        self._write(
            "b.json",
            '{"value":"head-b"}\n',
        )
        head = self._commit("head")

        delta = self._delta(
            base,
            head,
        )

        first = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=delta,
            manifest=_manifest(
                protected_modules=(),
            ),
            limits=LIMITS,
        )

        second = analyze_reference_candidate(
            self.repo,
            base_commit_sha1=base,
            head_commit_sha1=head,
            canonical_tree_delta=tuple(
                reversed(delta)
            ),
            manifest=_manifest(
                protected_modules=(),
            ),
            limits=LIMITS,
        )

        self.assertEqual(
            first,
            second,
        )

    def test_remaining_graph_budgets_are_passed_to_head_epoch(self) -> None:
        self._write_protected_package()
        self._write(
            "app/__init__.py",
            "",
        )
        self._write(
            "app/view.py",
            (
                "import importlib\n"
                "import mes_quant.features.builder\n"
                "name = 'mes_quant.' + 'features'\n"
                "importlib.import_module(name)\n"
            ),
        )
        base = self._commit("base")

        self._write(
            "app/view.py",
            "VALUE = 1\n",
        )
        head = self._commit("head")

        observed_limits: list[dict[str, int]] = []

        def observe(*args, **kwargs):
            observed_limits.append(
                dict(kwargs["limits"])
            )
            return real_analyze_reference_snapshot(
                *args,
                **kwargs,
            )

        with mock.patch(
            (
                "mes_quant.governance.classification."
                "reference_candidate."
                "analyze_reference_snapshot"
            ),
            side_effect=observe,
        ):
            result = analyze_reference_candidate(
                self.repo,
                base_commit_sha1=base,
                head_commit_sha1=head,
                canonical_tree_delta=self._delta(
                    base,
                    head,
                ),
                manifest=_manifest(),
                limits=LIMITS,
            )

        self.assertEqual(
            len(observed_limits),
            2,
        )

        base_snapshot = result.base_snapshot

        self.assertIsNotNone(base_snapshot)

        head_limits = observed_limits[1]

        self.assertEqual(
            head_limits["max_graph_nodes"],
            (
                LIMITS["max_graph_nodes"]
                - base_snapshot.graph_node_count
            ),
        )
        self.assertEqual(
            head_limits["max_graph_edges"],
            (
                LIMITS["max_graph_edges"]
                - base_snapshot.graph_edge_count
            ),
        )
        self.assertEqual(
            head_limits["max_unresolved_nodes"],
            (
                LIMITS["max_unresolved_nodes"]
                - len(base_snapshot.unresolved_nodes)
            ),
        )

    def test_empty_candidate_delta_fails_closed(self) -> None:
        self._write(
            "config.json",
            '{"value":"base"}\n',
        )
        commit = self._commit("base")

        with self.assertRaisesRegex(
            ReferenceCandidateError,
            "tree delta must not be empty",
        ):
            analyze_reference_candidate(
                self.repo,
                base_commit_sha1=commit,
                head_commit_sha1=commit,
                canonical_tree_delta=(),
                manifest=_manifest(
                    protected_modules=(),
                ),
                limits=LIMITS,
            )


if __name__ == "__main__":
    unittest.main()

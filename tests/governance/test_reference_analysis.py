from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.reference_analysis import (
    ReferenceAnalysisError,
    analyze_reference_snapshot,
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
        "protected_quant_modules": list(protected_modules),
        "protected_symbols": list(protected_symbols),
    }


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class ReferenceAnalysisTests(unittest.TestCase):
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

    def _write(self, relative_path: str, content: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _commit(self) -> str:
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "snapshot")
        return _git(self.repo, "rev-parse", "HEAD")

    def _base_packages(self) -> None:
        self._write(
            "lib/mes_quant/__init__.py",
            "",
        )
        self._write(
            "lib/mes_quant/features/__init__.py",
            "",
        )
        self._write(
            "app/__init__.py",
            "",
        )

    def test_forward_changed_node_reaches_protected_module(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            "import mes_quant.features.builder\n",
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertTrue(
            result.graph_analysis.forward.reachable_protected
        )
        self.assertFalse(
            result.graph_analysis.reverse.reachable_protected
        )
        self.assertIn(
            b"lib/mes_quant/features/builder.py",
            result.protected_nodes,
        )
        self.assertTrue(
            result.reference_scan_summary.scan_complete
        )
        self.assertEqual(
            result.reference_scan_summary.failed_reference_files,
            0,
        )

    def test_protected_module_can_reach_changed_node(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "import app.view\n",
        )
        self._write(
            "app/view.py",
            "VALUE = 1\n",
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertFalse(
            result.graph_analysis.forward.reachable_protected
        )
        self.assertTrue(
            result.graph_analysis.reverse.reachable_protected
        )

    def test_literal_dynamic_import_keeps_edge_and_dynamic_fact(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            (
                "import importlib\n"
                "importlib.import_module("
                "'mes_quant.features.builder')\n"
            ),
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        unresolved = {
            (
                item.path_bytes,
                item.reason_code,
                item.reference_kind,
            )
            for item in result.unresolved_nodes
        }

        self.assertTrue(
            result.graph_analysis.forward
            .reachable_protected
        )
        self.assertIn(
            (
                b"app/view.py",
                "DYNAMIC_IMPORT",
                "DYNAMIC",
            ),
            unresolved,
        )

    def test_dynamic_import_is_reported_as_unresolved(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            (
                "import importlib\n"
                "name = 'mes_quant.' + 'features'\n"
                "importlib.import_module(name)\n"
            ),
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        unresolved = {
            (
                item.path_bytes,
                item.reason_code,
                item.reference_kind,
            )
            for item in result.unresolved_nodes
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
            result.graph_analysis.forward.unresolved_count,
            1,
        )

    def test_yaml_possible_consumer_is_explicitly_unsupported(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "configs/view.yaml",
            "module: mes_quant.features.builder\n",
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"configs/view.yaml",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertEqual(
            result.reference_scan_summary.unsupported_reference_files,
            1,
        )
        self.assertIn(
            "yaml",
            result.unsupported_reference_file_types,
        )

    def test_protected_symbol_resolves_through_real_module_path(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            (
                "class FeatureContract:\n"
                "    pass\n"
            ),
        )
        self._write(
            "app/view.py",
            (
                "from mes_quant.features.builder "
                "import FeatureContract\n"
            ),
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(
                protected_modules=(),
                protected_symbols=(
                    "mes_quant.features.builder:FeatureContract",
                ),
            ),
            limits=LIMITS,
        )

        self.assertIn(
            b"lib/mes_quant/features/builder.py",
            result.protected_nodes,
        )
        self.assertTrue(
            result.graph_analysis.forward.reachable_protected
        )

    def test_relative_import_resolves_from_actual_source_package(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "lib/mes_quant/features/view.py",
            "from . import builder\n",
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(
                b"lib/mes_quant/features/view.py",
            ),
            manifest=_manifest(
                protected_modules=(
                    "mes_quant.features.builder",
                ),
            ),
            limits=LIMITS,
        )

        self.assertTrue(
            result.graph_analysis.forward
            .reachable_protected
        )

    def test_absolute_from_import_can_resolve_child_submodule(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            (
                "from mes_quant.features "
                "import builder\n"
            ),
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(
                protected_modules=(
                    "mes_quant.features.builder",
                ),
            ),
            limits=LIMITS,
        )

        self.assertTrue(
            result.graph_analysis.forward
            .reachable_protected
        )

    def test_source_relative_config_path_resolves_repository_node(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "configs/view.json",
            (
                '{"path":"../lib/mes_quant/'
                'features/builder.py"}\n'
            ),
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"configs/view.json",),
            manifest=_manifest(
                protected_modules=(
                    "mes_quant.features.builder",
                ),
            ),
            limits=LIMITS,
        )

        self.assertTrue(
            result.graph_analysis.forward
            .reachable_protected
        )

    def test_relative_symlink_target_resolves_without_dereference(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )

        link = self.repo / "links/view"
        link.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        link.symlink_to(
            "../lib/mes_quant/features/builder.py"
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"links/view",),
            manifest=_manifest(
                protected_modules=(
                    "mes_quant.features.builder",
                ),
            ),
            limits=LIMITS,
        )

        self.assertTrue(
            result.graph_analysis.forward
            .reachable_protected
        )

    def test_snapshot_reports_actual_graph_resource_usage(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            "import mes_quant.features.builder\n",
        )

        head = self._commit()

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"app/view.py",),
            manifest=_manifest(),
            limits=LIMITS,
        )

        self.assertEqual(
            result.graph_node_count,
            result.reference_scan_summary
            .scanned_tracked_objects,
        )
        self.assertGreaterEqual(
            result.graph_edge_count,
            1,
        )

    def test_zero_runtime_edge_and_unresolved_budgets_allow_clean_snapshot(
        self,
    ) -> None:
        self._write(
            "config.json",
            '{"value":"clean"}\n',
        )
        head = self._commit()

        limits = dict(LIMITS)
        limits["max_graph_edges"] = 0
        limits["max_unresolved_nodes"] = 0

        result = analyze_reference_snapshot(
            str(self.repo),
            commit_sha1=head,
            changed_nodes=(b"config.json",),
            manifest=_manifest(
                protected_modules=(),
            ),
            limits=limits,
        )

        self.assertEqual(
            result.graph_edge_count,
            0,
        )
        self.assertEqual(
            result.unresolved_nodes,
            (),
        )

    def test_invalid_or_unresolvable_protected_identity_fails_scan(
        self,
    ) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/view.py",
            "VALUE = 1\n",
        )

        head = self._commit()

        with self.subTest(
            case="invalid-symbol"
        ):
            with self.assertRaisesRegex(
                ReferenceAnalysisError,
                "invalid protected symbol identity",
            ):
                analyze_reference_snapshot(
                    str(self.repo),
                    commit_sha1=head,
                    changed_nodes=(b"app/view.py",),
                    manifest=_manifest(
                        protected_modules=(),
                        protected_symbols=(
                            "mes_quant.features.builder:"
                            "Bad-Name",
                        ),
                    ),
                    limits=LIMITS,
                )

        with self.subTest(
            case="unresolvable-module"
        ):
            with self.assertRaisesRegex(
                ReferenceAnalysisError,
                "protected module resolution failed",
            ):
                analyze_reference_snapshot(
                    str(self.repo),
                    commit_sha1=head,
                    changed_nodes=(b"app/view.py",),
                    manifest=_manifest(
                        protected_modules=(
                            "mes_quant.missing",
                        ),
                    ),
                    limits=LIMITS,
                )

    def test_graph_edge_limit_fails_before_graph_materialization(
        self,
    ) -> None:
        self._write(
            "files/a.txt",
            "a\n",
        )
        self._write(
            "files/b.txt",
            "b\n",
        )
        self._write(
            "config.json",
            (
                '{"paths":['
                '"files/a.txt",'
                '"files/b.txt"'
                ']}\n'
            ),
        )

        head = self._commit()

        limits = dict(LIMITS)
        limits["max_graph_edges"] = 1

        with mock.patch(
            (
                "mes_quant.governance.classification."
                "reference_analysis."
                "analyze_bidirectional_graph"
            )
        ) as graph_analyzer:
            with self.assertRaisesRegex(
                ReferenceAnalysisError,
                "max_graph_edges=1",
            ):
                analyze_reference_snapshot(
                    str(self.repo),
                    commit_sha1=head,
                    changed_nodes=(b"config.json",),
                    manifest=_manifest(
                        protected_modules=(),
                    ),
                    limits=limits,
                )

        graph_analyzer.assert_not_called()

    def test_mandatory_python_parse_failure_fails_scan(self) -> None:
        self._base_packages()
        self._write(
            "lib/mes_quant/features/builder.py",
            "VALUE = 1\n",
        )
        self._write(
            "app/broken.py",
            "def broken(:\n",
        )

        head = self._commit()

        with self.assertRaisesRegex(
            ReferenceAnalysisError,
            "mandatory reference parse failed",
        ):
            analyze_reference_snapshot(
                str(self.repo),
                commit_sha1=head,
                changed_nodes=(b"app/broken.py",),
                manifest=_manifest(),
                limits=LIMITS,
            )


if __name__ == "__main__":
    unittest.main()

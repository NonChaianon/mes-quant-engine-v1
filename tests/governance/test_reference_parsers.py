from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.reference_parsers import (
    ReferenceParseError,
    parse_reference_file,
    reference_file_type,
)


LIMITS = {
    "max_ast_nodes": 10_000,
    "max_parse_depth": 128,
    "max_config_nesting_depth": 128,
    "max_scalar_bytes": 4096,
    "max_collection_cardinality": 10_000,
}


def _parse(path: bytes, data: bytes):
    return parse_reference_file(
        path,
        data,
        **LIMITS,
    )


class ReferenceParserTests(unittest.TestCase):
    def test_file_type_detection_uses_raw_path_suffix(self) -> None:
        self.assertEqual(reference_file_type(b"a.py"), "PYTHON")
        self.assertEqual(reference_file_type(b"a.json"), "JSON")
        self.assertEqual(reference_file_type(b"a.toml"), "TOML")
        self.assertEqual(reference_file_type(b"a.yaml"), "YAML")
        self.assertEqual(reference_file_type(b"a.yml"), "YAML")
        self.assertEqual(reference_file_type(b"Dockerfile"), "UNSUPPORTED")

    def test_python_static_imports_are_resolved_as_inert_references(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"import mes_quant.features.builder\n"
                b"from mes_quant.labels.contract import LabelContract\n"
            ),
        )

        references = {
            (item.reference_kind, item.value)
            for item in parsed.references
        }

        self.assertTrue(parsed.supported)
        self.assertEqual(parsed.parser_kind, "PYTHON")
        self.assertIn(
            ("MODULE_NAME", "mes_quant.features.builder"),
            references,
        )
        self.assertIn(
            ("MODULE_NAME", "mes_quant.labels.contract"),
            references,
        )
        self.assertIn(
            (
                "SYMBOL_NAME",
                "mes_quant.labels.contract:LabelContract",
            ),
            references,
        )
        self.assertEqual(parsed.unresolved, ())

    def test_literal_dynamic_import_resolves_edge_but_remains_dynamic(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"import importlib\n"
                b"importlib.import_module("
                b"'mes_quant.features.builder')\n"
            ),
        )

        references = {
            (item.reference_kind, item.value)
            for item in parsed.references
        }
        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            (
                "MODULE_NAME",
                "mes_quant.features.builder",
            ),
            references,
        )
        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_python_constructed_dynamic_import_fails_narrow_proof(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"import importlib\n"
                b"name = 'mes_quant.' + 'features'\n"
                b"importlib.import_module(name)\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_builtin_import_is_resolved_but_marked_dynamic(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"module = __import__("
                b"'mes_quant.features.builder')\n"
            ),
        )

        references = {
            (item.reference_kind, item.value)
            for item in parsed.references
        }
        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            (
                "MODULE_NAME",
                "mes_quant.features.builder",
            ),
            references,
        )
        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_entry_point_apis_are_plugin_loading(self) -> None:
        parsed = _parse(
            b"plugins.py",
            (
                b"from importlib.metadata "
                b"import entry_points\n"
                b"import pkg_resources\n"
                b"entry_points()\n"
                b"pkg_resources.load_entry_point("
                b"'dist', 'group', 'name')\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "PLUGIN_LOADING"),
            unresolved,
        )

    def test_runtime_module_loaders_are_plugin_loading(self) -> None:
        parsed = _parse(
            b"plugins.py",
            (
                b"import importlib.util\n"
                b"import ctypes\n"
                b"importlib.util.spec_from_file_location("
                b"'plugin', 'plugin.py')\n"
                b"ctypes.CDLL('plugin.so')\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "PLUGIN_LOADING"),
            unresolved,
        )

    def test_runpy_and_reload_are_dynamic_behavior(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"import importlib\n"
                b"import runpy\n"
                b"runpy.run_module("
                b"'mes_quant.features.builder')\n"
                b"importlib.reload(importlib)\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            (
                "DYNAMIC",
                "UNSUPPORTED_DYNAMIC_BEHAVIOR",
            ),
            unresolved,
        )
        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_eval_and_exec_are_unresolved_dynamic_behavior(self) -> None:
        parsed = _parse(
            b"module.py",
            b"eval('1 + 1')\nexec('x = 1')\n",
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "EVAL_OR_EXEC"),
            unresolved,
        )

    def test_json_and_toml_strings_expose_static_references(self) -> None:
        json_parsed = _parse(
            b"config.json",
            (
                b'{"module":"mes_quant.features.builder",'
                b'"path":"src/mes_quant/features/builder.py"}'
            ),
        )
        toml_parsed = _parse(
            b"config.toml",
            (
                b'module = "mes_quant.labels.contract"\n'
                b'path = "src/mes_quant/labels/contract.py"\n'
            ),
        )

        json_refs = {
            (item.reference_kind, item.value)
            for item in json_parsed.references
        }
        toml_refs = {
            (item.reference_kind, item.value)
            for item in toml_parsed.references
        }

        self.assertIn(
            ("MODULE_NAME", "mes_quant.features.builder"),
            json_refs,
        )
        self.assertIn(
            ("PATH_LITERAL", "src/mes_quant/features/builder.py"),
            json_refs,
        )
        self.assertIn(
            ("MODULE_NAME", "mes_quant.labels.contract"),
            toml_refs,
        )
        self.assertIn(
            ("PATH_LITERAL", "src/mes_quant/labels/contract.py"),
            toml_refs,
        )

    def test_yaml_and_unknown_types_are_explicitly_unsupported(self) -> None:
        yaml_parsed = _parse(
            b"workflow.yaml",
            b"module: mes_quant.features.builder\n",
        )
        unknown_parsed = _parse(
            b"Dockerfile",
            b"FROM python:3.12\n",
        )

        self.assertFalse(yaml_parsed.supported)
        self.assertEqual(yaml_parsed.parser_kind, "YAML")
        self.assertFalse(unknown_parsed.supported)
        self.assertEqual(
            unknown_parsed.parser_kind,
            "UNSUPPORTED",
        )

    def test_relative_import_is_preserved_for_context_resolution(self) -> None:
        parsed = _parse(
            b"package/view.py",
            (
                b"from .builder import FeatureContract\n"
                b"from ..labels import LabelContract\n"
            ),
        )

        references = {
            (item.reference_kind, item.value)
            for item in parsed.references
        }

        self.assertIn(
            ("IMPORT", ".builder"),
            references,
        )
        self.assertIn(
            (
                "SYMBOL_NAME",
                ".builder:FeatureContract",
            ),
            references,
        )
        self.assertIn(
            ("IMPORT", "..labels"),
            references,
        )
        self.assertIn(
            (
                "SYMBOL_NAME",
                "..labels:LabelContract",
            ),
            references,
        )
        self.assertEqual(
            parsed.unresolved,
            (),
        )

    def test_literal_reflection_still_prevents_narrow_proof(self) -> None:
        parsed = _parse(
            b"module.py",
            (
                b"class Item:\n"
                b"    value = 1\n"
                b"item = Item()\n"
                b"result = getattr(item, 'value')\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "REFLECTION"),
            unresolved,
        )

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(
            ReferenceParseError,
            "JSON_REFERENCE_PARSE_FAILURE",
        ):
            _parse(
                b"config.json",
                (
                    b'{"module":"mes_quant.features.builder",'
                    b'"module":"harmless"}'
                ),
            )

    def test_python_syntax_failure_is_mandatory_scan_failure(self) -> None:
        with self.assertRaisesRegex(
            ReferenceParseError,
            "PYTHON_REFERENCE_PARSE_FAILURE",
        ):
            _parse(
                b"broken.py",
                b"def broken(:\n",
            )

    def test_config_nesting_depth_is_governed_separately(self) -> None:
        with self.assertRaisesRegex(
            ReferenceParseError,
            "max_config_nesting_depth=2",
        ):
            parse_reference_file(
                b"config.json",
                b'{"a":{"b":{"c":"value"}}}',
                max_ast_nodes=10_000,
                max_parse_depth=128,
                max_config_nesting_depth=2,
                max_scalar_bytes=4096,
                max_collection_cardinality=10_000,
            )

    def test_python_depth_is_independent_from_config_depth(self) -> None:
        parsed = parse_reference_file(
            b"module.py",
            b"x = 1\n",
            max_ast_nodes=10_000,
            max_parse_depth=128,
            max_config_nesting_depth=1,
            max_scalar_bytes=4096,
            max_collection_cardinality=10_000,
        )

        self.assertTrue(parsed.supported)
        self.assertEqual(parsed.parser_kind, "PYTHON")

    def test_resource_limits_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            ReferenceParseError,
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED",
        ):
            parse_reference_file(
                b"module.py",
                b"x = 'this string is deliberately too large'\n",
                max_ast_nodes=10_000,
                max_parse_depth=128,
                max_config_nesting_depth=128,
                max_scalar_bytes=4,
                max_collection_cardinality=10_000,
            )


    def test_imported_dynamic_callable_alias_is_detected(self) -> None:
        parsed = _parse(
            b"alias_import.py",
            (
                b"from importlib import import_module as im\n"
                b"name = 'mes_quant.' + 'features'\n"
                b"im(name)\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_chained_dynamic_callable_alias_is_detected(self) -> None:
        parsed = _parse(
            b"alias_chain.py",
            (
                b"import importlib\n"
                b"loader = importlib.import_module\n"
                b"second = loader\n"
                b"name = 'mes_quant.' + 'features'\n"
                b"second(name)\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "DYNAMIC_IMPORT"),
            unresolved,
        )

    def test_other_dangerous_callable_aliases_remain_fail_safe(self) -> None:
        parsed = _parse(
            b"dangerous_aliases.py",
            (
                b"from importlib.metadata import entry_points as ep\n"
                b"from runpy import run_module as rm\n"
                b"import builtins\n"
                b"execute = builtins.eval\n"
                b"ep()\n"
                b"rm('mes_quant.features.builder')\n"
                b"execute('1 + 1')\n"
            ),
        )

        unresolved = {
            (item.reference_kind, item.reason_code)
            for item in parsed.unresolved
        }

        self.assertIn(
            ("DYNAMIC", "PLUGIN_LOADING"),
            unresolved,
        )
        self.assertIn(
            (
                "DYNAMIC",
                "UNSUPPORTED_DYNAMIC_BEHAVIOR",
            ),
            unresolved,
        )
        self.assertIn(
            ("DYNAMIC", "EVAL_OR_EXEC"),
            unresolved,
        )


if __name__ == "__main__":
    unittest.main()

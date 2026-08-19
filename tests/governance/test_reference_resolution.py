from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.reference_objects import TrackedObject
from mes_quant.governance.classification.reference_resolution import (
    ReferenceResolutionError,
    build_python_module_index,
    protected_module_nodes,
    resolve_module_reference,
)


def _blob(path: bytes) -> TrackedObject:
    return TrackedObject(
        path_bytes=path,
        mode="100644",
        object_type="blob",
        object_sha1="0" * 40,
    )


class ReferenceResolutionTests(unittest.TestCase):
    def test_module_identity_comes_from_actual_package_markers(self) -> None:
        objects = (
            _blob(b"lib/mes_quant/__init__.py"),
            _blob(b"lib/mes_quant/features/__init__.py"),
            _blob(b"lib/mes_quant/features/builder.py"),
        )

        index = build_python_module_index(objects)

        self.assertEqual(
            resolve_module_reference(
                "mes_quant.features.builder",
                index,
            ),
            (b"lib/mes_quant/features/builder.py",),
        )

    def test_src_layout_is_not_required(self) -> None:
        objects = (
            _blob(b"engine/mes_quant/__init__.py"),
            _blob(b"engine/mes_quant/labels/__init__.py"),
            _blob(b"engine/mes_quant/labels/contract.py"),
        )

        index = build_python_module_index(objects)

        self.assertEqual(
            index.path_to_module[
                b"engine/mes_quant/labels/contract.py"
            ],
            "mes_quant.labels.contract",
        )

    def test_unpackaged_python_file_is_not_claimed_as_module(self) -> None:
        objects = (
            _blob(b"scripts/tool.py"),
        )

        index = build_python_module_index(objects)

        self.assertEqual(index.module_to_paths, {})
        self.assertEqual(index.path_to_module, {})

    def test_protected_module_expands_exact_and_descendants(self) -> None:
        objects = (
            _blob(b"pkg/mes_quant/__init__.py"),
            _blob(b"pkg/mes_quant/features/__init__.py"),
            _blob(b"pkg/mes_quant/features/builder.py"),
            _blob(b"pkg/mes_quant/labels/__init__.py"),
            _blob(b"pkg/mes_quant/labels/contract.py"),
        )

        index = build_python_module_index(objects)

        protected = protected_module_nodes(
            ("mes_quant.features",),
            index,
        )

        self.assertEqual(
            protected,
            (
                b"pkg/mes_quant/features/__init__.py",
                b"pkg/mes_quant/features/builder.py",
            ),
        )

    def test_duplicate_module_identity_across_roots_is_deterministic(self) -> None:
        objects = (
            _blob(b"a/mes_quant/__init__.py"),
            _blob(b"a/mes_quant/features/__init__.py"),
            _blob(b"a/mes_quant/features/builder.py"),
            _blob(b"z/mes_quant/__init__.py"),
            _blob(b"z/mes_quant/features/__init__.py"),
            _blob(b"z/mes_quant/features/builder.py"),
        )

        index = build_python_module_index(reversed(objects))

        self.assertEqual(
            resolve_module_reference(
                "mes_quant.features.builder",
                index,
            ),
            (
                b"a/mes_quant/features/builder.py",
                b"z/mes_quant/features/builder.py",
            ),
        )

    def test_invalid_module_identity_fails_closed(self) -> None:
        index = build_python_module_index(())

        for value in (
            "",
            "mes_quant..features",
            "mes-quant.features",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ReferenceResolutionError):
                    resolve_module_reference(value, index)

    def test_unresolvable_protected_module_fails_closed(self) -> None:
        objects = (
            _blob(b"pkg/mes_quant/__init__.py"),
            _blob(
                b"pkg/mes_quant/features/__init__.py"
            ),
        )

        index = build_python_module_index(
            objects
        )

        with self.assertRaisesRegex(
            ReferenceResolutionError,
            "protected module cannot be resolved",
        ):
            protected_module_nodes(
                ("mes_quant.missing",),
                index,
            )

    def test_invalid_protected_module_fails_closed(self) -> None:
        index = build_python_module_index(())

        with self.assertRaises(ReferenceResolutionError):
            protected_module_nodes(
                ("mes_quant..features",),
                index,
            )


if __name__ == "__main__":
    unittest.main()

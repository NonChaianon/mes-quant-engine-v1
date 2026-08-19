from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import re
import tomllib
from typing import Any

_MODULE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
_SYMBOL_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*:"
    r"[A-Za-z_][A-Za-z0-9_.]*$"
)

_PYTHON_SUFFIX = b".py"
_JSON_SUFFIX = b".json"
_TOML_SUFFIX = b".toml"
_YAML_SUFFIXES = (b".yaml", b".yml")


class ReferenceParseError(RuntimeError):
    """Raised when a mandatory inert reference parse cannot complete safely."""


@dataclass(frozen=True, order=True)
class StaticReference:
    reference_kind: str
    value: str


@dataclass(frozen=True, order=True)
class UnresolvedReference:
    reference_kind: str
    reason_code: str


@dataclass(frozen=True)
class ParsedReferenceFile:
    parser_kind: str
    supported: bool
    references: tuple[StaticReference, ...]
    unresolved: tuple[UnresolvedReference, ...]


def _positive_integer(value: int, name: str) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise ReferenceParseError(
            f"{name} must be a positive integer"
        )


def reference_file_type(path_bytes: bytes) -> str:
    """Return the governed parser category without filesystem decoding."""

    if path_bytes.endswith(_PYTHON_SUFFIX):
        return "PYTHON"

    if path_bytes.endswith(_JSON_SUFFIX):
        return "JSON"

    if path_bytes.endswith(_TOML_SUFFIX):
        return "TOML"

    if path_bytes.endswith(_YAML_SUFFIXES):
        return "YAML"

    return "UNSUPPORTED"


def _string_references(
    value: str,
    *,
    kind: str,
    max_scalar_bytes: int,
) -> tuple[StaticReference, ...]:
    encoded = value.encode("utf-8")

    if len(encoded) > max_scalar_bytes:
        raise ReferenceParseError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_scalar_bytes={max_scalar_bytes}"
        )

    references: set[StaticReference] = {
        StaticReference(kind, value)
    }

    if "/" in value or value.startswith(("./", "../")):
        references.add(
            StaticReference("PATH_LITERAL", value)
        )

    if _MODULE_RE.fullmatch(value):
        references.add(
            StaticReference("MODULE_NAME", value)
        )

    if _SYMBOL_RE.fullmatch(value):
        references.add(
            StaticReference("SYMBOL_NAME", value)
        )

    return tuple(sorted(references))


def _python_ast(
    data: bytes,
    *,
    max_ast_nodes: int,
    max_parse_depth: int,
) -> ast.AST:
    try:
        tree = compile(
            data,
            "<candidate-git-blob>",
            "exec",
            flags=ast.PyCF_ONLY_AST,
            dont_inherit=True,
        )
    except (SyntaxError, UnicodeError, ValueError) as exc:
        raise ReferenceParseError(
            "PYTHON_REFERENCE_PARSE_FAILURE"
        ) from exc

    stack: list[tuple[ast.AST, int]] = [(tree, 1)]
    visited = 0

    while stack:
        node, depth = stack.pop()
        visited += 1

        if visited > max_ast_nodes:
            raise ReferenceParseError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_ast_nodes={max_ast_nodes}"
            )

        if depth > max_parse_depth:
            raise ReferenceParseError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                f"max_parse_depth={max_parse_depth}"
            )

        children = tuple(ast.iter_child_nodes(node))
        stack.extend(
            (child, depth + 1)
            for child in reversed(children)
        )

    return tree


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.AST = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))

    return None


def _parse_python(
    data: bytes,
    *,
    max_ast_nodes: int,
    max_parse_depth: int,
    max_scalar_bytes: int,
) -> ParsedReferenceFile:
    tree = _python_ast(
        data,
        max_ast_nodes=max_ast_nodes,
        max_parse_depth=max_parse_depth,
    )

    references: set[StaticReference] = set()
    unresolved: set[UnresolvedReference] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                references.add(
                    StaticReference("IMPORT", alias.name)
                )
                references.add(
                    StaticReference("MODULE_NAME", alias.name)
                )

        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                relative_module = (
                    "." * node.level
                    + (node.module or "")
                )

                references.add(
                    StaticReference(
                        "IMPORT",
                        relative_module,
                    )
                )

                for alias in node.names:
                    if alias.name != "*":
                        references.add(
                            StaticReference(
                                "SYMBOL_NAME",
                                (
                                    f"{relative_module}:"
                                    f"{alias.name}"
                                ),
                            )
                        )

            elif node.module is None:
                unresolved.add(
                    UnresolvedReference(
                        "IMPORT",
                        "UNRESOLVED_MODULE",
                    )
                )

            else:
                references.add(
                    StaticReference("IMPORT", node.module)
                )
                references.add(
                    StaticReference(
                        "MODULE_NAME",
                        node.module,
                    )
                )

                for alias in node.names:
                    if alias.name != "*":
                        references.add(
                            StaticReference(
                                "SYMBOL_NAME",
                                f"{node.module}:{alias.name}",
                            )
                        )

        elif isinstance(node, ast.Constant) and isinstance(
            node.value,
            str,
        ):
            references.update(
                _string_references(
                    node.value,
                    kind="PATH_LITERAL",
                    max_scalar_bytes=max_scalar_bytes,
                )
            )

        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            tail = (
                name.rsplit(".", 1)[-1]
                if name is not None
                else None
            )

            if tail in {"eval", "exec"}:
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "EVAL_OR_EXEC",
                    )
                )

            elif tail == "__import__":
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "DYNAMIC_IMPORT",
                    )
                )

                if (
                    node.args
                    and isinstance(
                        node.args[0],
                        ast.Constant,
                    )
                    and isinstance(
                        node.args[0].value,
                        str,
                    )
                    and _MODULE_RE.fullmatch(
                        node.args[0].value
                    )
                ):
                    references.add(
                        StaticReference(
                            "MODULE_NAME",
                            node.args[0].value,
                        )
                    )

            elif (
                name == "importlib.import_module"
                or tail == "import_module"
            ):
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "DYNAMIC_IMPORT",
                    )
                )

                if (
                    node.args
                    and isinstance(
                        node.args[0],
                        ast.Constant,
                    )
                    and isinstance(
                        node.args[0].value,
                        str,
                    )
                    and _MODULE_RE.fullmatch(
                        node.args[0].value
                    )
                ):
                    references.add(
                        StaticReference(
                            "MODULE_NAME",
                            node.args[0].value,
                        )
                    )

            elif (
                name in {
                    "importlib.reload",
                    "importlib.util.find_spec",
                    "pkgutil.resolve_name",
                    "pydoc.locate",
                }
                or tail in {
                    "reload",
                    "find_spec",
                    "resolve_name",
                    "locate",
                }
            ):
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "DYNAMIC_IMPORT",
                    )
                )

            elif (
                name in {
                    "importlib.metadata.entry_points",
                    "pkg_resources.iter_entry_points",
                    "pkg_resources.load_entry_point",
                    "importlib.util.spec_from_file_location",
                    "importlib.util.module_from_spec",
                    "importlib.machinery.SourceFileLoader",
                    "importlib.machinery.SourcelessFileLoader",
                    "importlib.machinery.ExtensionFileLoader",
                    "zipimport.zipimporter",
                    "ctypes.CDLL",
                    "ctypes.PyDLL",
                }
                or tail in {
                    "entry_points",
                    "iter_entry_points",
                    "load_entry_point",
                    "load_setuptools_entrypoints",
                    "spec_from_file_location",
                    "module_from_spec",
                    "SourceFileLoader",
                    "SourcelessFileLoader",
                    "ExtensionFileLoader",
                    "zipimporter",
                    "exec_module",
                    "load_module",
                    "CDLL",
                    "PyDLL",
                    "ExtensionManager",
                    "DriverManager",
                    "NamedExtensionManager",
                }
            ):
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "PLUGIN_LOADING",
                    )
                )

            elif (
                name in {
                    "runpy.run_module",
                    "runpy.run_path",
                    "pickle.load",
                    "pickle.loads",
                    "dill.load",
                    "dill.loads",
                    "cloudpickle.loads",
                }
                or tail in {
                    "run_module",
                    "run_path",
                }
            ):
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "UNSUPPORTED_DYNAMIC_BEHAVIOR",
                    )
                )

            elif (
                tail
                in {
                    "getattr",
                    "setattr",
                    "delattr",
                    "hasattr",
                    "vars",
                    "globals",
                    "locals",
                }
            ):
                unresolved.add(
                    UnresolvedReference(
                        "DYNAMIC",
                        "REFLECTION",
                    )
                )

    return ParsedReferenceFile(
        parser_kind="PYTHON",
        supported=True,
        references=tuple(sorted(references)),
        unresolved=tuple(sorted(unresolved)),
    )


def _walk_structured(
    value: Any,
    *,
    reference_kind: str,
    max_config_nesting_depth: int,
    max_scalar_bytes: int,
    max_collection_cardinality: int,
) -> tuple[StaticReference, ...]:
    references: set[StaticReference] = set()
    stack: list[tuple[Any, int]] = [(value, 1)]
    cardinality = 0

    while stack:
        current, depth = stack.pop()

        if depth > max_config_nesting_depth:
            raise ReferenceParseError(
                "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                "max_config_nesting_depth="
                f"{max_config_nesting_depth}"
            )

        if isinstance(current, dict):
            cardinality += len(current)

            if cardinality > max_collection_cardinality:
                raise ReferenceParseError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    "max_collection_cardinality="
                    f"{max_collection_cardinality}"
                )

            for key in sorted(current, reverse=True):
                if not isinstance(key, str):
                    raise ReferenceParseError(
                        "structured configuration key must be string"
                    )

                references.update(
                    _string_references(
                        key,
                        kind=reference_kind,
                        max_scalar_bytes=max_scalar_bytes,
                    )
                )

                stack.append(
                    (current[key], depth + 1)
                )

        elif isinstance(current, list):
            cardinality += len(current)

            if cardinality > max_collection_cardinality:
                raise ReferenceParseError(
                    "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                    "max_collection_cardinality="
                    f"{max_collection_cardinality}"
                )

            stack.extend(
                (item, depth + 1)
                for item in reversed(current)
            )

        elif isinstance(current, str):
            references.update(
                _string_references(
                    current,
                    kind=reference_kind,
                    max_scalar_bytes=max_scalar_bytes,
                )
            )

        elif current is None or isinstance(
            current,
            (bool, int, float),
        ):
            continue

        else:
            raise ReferenceParseError(
                "unsupported structured scalar type"
            )

    return tuple(sorted(references))


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(
                f"duplicate JSON key: {key}"
            )

        result[key] = value

    return result


def _parse_json(
    data: bytes,
    *,
    max_config_nesting_depth: int,
    max_scalar_bytes: int,
    max_collection_cardinality: int,
) -> ParsedReferenceFile:
    try:
        payload = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(value)
            ),
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise ReferenceParseError(
            "JSON_REFERENCE_PARSE_FAILURE"
        ) from exc

    return ParsedReferenceFile(
        parser_kind="JSON",
        supported=True,
        references=_walk_structured(
            payload,
            reference_kind="JSON",
            max_config_nesting_depth=max_config_nesting_depth,
            max_scalar_bytes=max_scalar_bytes,
            max_collection_cardinality=max_collection_cardinality,
        ),
        unresolved=(),
    )


def _parse_toml(
    data: bytes,
    *,
    max_config_nesting_depth: int,
    max_scalar_bytes: int,
    max_collection_cardinality: int,
) -> ParsedReferenceFile:
    try:
        payload = tomllib.loads(data.decode("utf-8"))
    except (
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        RecursionError,
    ) as exc:
        raise ReferenceParseError(
            "TOML_REFERENCE_PARSE_FAILURE"
        ) from exc

    return ParsedReferenceFile(
        parser_kind="TOML",
        supported=True,
        references=_walk_structured(
            payload,
            reference_kind="TOML",
            max_config_nesting_depth=max_config_nesting_depth,
            max_scalar_bytes=max_scalar_bytes,
            max_collection_cardinality=max_collection_cardinality,
        ),
        unresolved=(),
    )


def parse_reference_file(
    path_bytes: bytes,
    data: bytes,
    *,
    max_ast_nodes: int,
    max_parse_depth: int,
    max_config_nesting_depth: int,
    max_scalar_bytes: int,
    max_collection_cardinality: int,
) -> ParsedReferenceFile:
    """Parse candidate bytes as inert data only; never import or execute them."""

    for value, name in (
        (max_ast_nodes, "max_ast_nodes"),
        (max_parse_depth, "max_parse_depth"),
        (
            max_config_nesting_depth,
            "max_config_nesting_depth",
        ),
        (max_scalar_bytes, "max_scalar_bytes"),
        (
            max_collection_cardinality,
            "max_collection_cardinality",
        ),
    ):
        _positive_integer(value, name)

    if not isinstance(path_bytes, bytes) or not path_bytes:
        raise ReferenceParseError(
            "path_bytes must be non-empty raw Git path bytes"
        )

    if not isinstance(data, bytes):
        raise ReferenceParseError(
            "data must be immutable Git blob bytes"
        )

    file_type = reference_file_type(path_bytes)

    if file_type == "PYTHON":
        return _parse_python(
            data,
            max_ast_nodes=max_ast_nodes,
            max_parse_depth=max_parse_depth,
            max_scalar_bytes=max_scalar_bytes,
        )

    if file_type == "JSON":
        return _parse_json(
            data,
            max_config_nesting_depth=max_config_nesting_depth,
            max_scalar_bytes=max_scalar_bytes,
            max_collection_cardinality=max_collection_cardinality,
        )

    if file_type == "TOML":
        return _parse_toml(
            data,
            max_config_nesting_depth=max_config_nesting_depth,
            max_scalar_bytes=max_scalar_bytes,
            max_collection_cardinality=max_collection_cardinality,
        )

    if file_type == "YAML":
        return ParsedReferenceFile(
            parser_kind="YAML",
            supported=False,
            references=(),
            unresolved=(),
        )

    return ParsedReferenceFile(
        parser_kind="UNSUPPORTED",
        supported=False,
        references=(),
        unresolved=(),
    )

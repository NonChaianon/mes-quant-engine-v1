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


_DYNAMIC_IMPORT_EXACT = frozenset(
    {
        "importlib.import_module",
        "importlib.reload",
        "importlib.util.find_spec",
        "pkgutil.resolve_name",
        "pydoc.locate",
    }
)

_DYNAMIC_IMPORT_TAILS = frozenset(
    {
        "__import__",
        "import_module",
        "reload",
        "find_spec",
        "resolve_name",
        "locate",
    }
)

_PLUGIN_LOADING_EXACT = frozenset(
    {
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
)

_PLUGIN_LOADING_TAILS = frozenset(
    {
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
)

_UNSUPPORTED_DYNAMIC_EXACT = frozenset(
    {
        "runpy.run_module",
        "runpy.run_path",
        "pickle.load",
        "pickle.loads",
        "dill.load",
        "dill.loads",
        "cloudpickle.loads",
    }
)

_UNSUPPORTED_DYNAMIC_TAILS = frozenset(
    {
        "run_module",
        "run_path",
    }
)

_REFLECTION_TAILS = frozenset(
    {
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
    }
)


def _dynamic_reason_for_callable_name(
    name: str,
) -> str | None:
    tail = name.rsplit(".", 1)[-1]

    if tail in {"eval", "exec"}:
        return "EVAL_OR_EXEC"

    if (
        name in _DYNAMIC_IMPORT_EXACT
        or tail in _DYNAMIC_IMPORT_TAILS
    ):
        return "DYNAMIC_IMPORT"

    if (
        name in _PLUGIN_LOADING_EXACT
        or tail in _PLUGIN_LOADING_TAILS
    ):
        return "PLUGIN_LOADING"

    if (
        name in _UNSUPPORTED_DYNAMIC_EXACT
        or tail in _UNSUPPORTED_DYNAMIC_TAILS
    ):
        return "UNSUPPORTED_DYNAMIC_BEHAVIOR"

    if tail in _REFLECTION_TAILS:
        return "REFLECTION"

    return None


def _assignment_target_names(
    node: ast.AST,
) -> tuple[str, ...]:
    names: set[str] = set()

    stack: list[ast.AST] = [node]

    while stack:
        current = stack.pop()

        if isinstance(current, ast.Name):
            names.add(current.id)

        elif isinstance(
            current,
            (ast.Tuple, ast.List),
        ):
            stack.extend(current.elts)

        elif isinstance(current, ast.Starred):
            stack.append(current.value)

    return tuple(sorted(names))


def _alias_source_names(
    node: ast.AST,
) -> tuple[str, ...]:
    sources: set[str] = set()
    stack: list[ast.AST] = [node]

    while stack:
        current = stack.pop()

        if isinstance(current, ast.Name):
            sources.add(current.id)

        elif isinstance(current, ast.Attribute):
            name = _call_name(current)

            if (
                name is not None
                and _dynamic_reason_for_callable_name(
                    name
                )
                is not None
            ):
                sources.add(name)

        elif isinstance(
            current,
            (ast.Tuple, ast.List, ast.Set),
        ):
            stack.extend(current.elts)

        elif isinstance(current, ast.Dict):
            stack.extend(
                item
                for item in (
                    *current.keys,
                    *current.values,
                )
                if item is not None
            )

        elif isinstance(current, ast.IfExp):
            stack.append(current.body)
            stack.append(current.orelse)

        elif isinstance(current, ast.NamedExpr):
            stack.append(current.value)

        elif isinstance(current, ast.Starred):
            stack.append(current.value)

        elif isinstance(current, ast.Subscript):
            stack.append(current.value)

    return tuple(sorted(sources))


def _dangerous_callable_aliases(
    tree: ast.AST,
) -> dict[str, tuple[str, ...]]:
    resolved: dict[str, set[str]] = {}
    dependencies: dict[str, set[str]] = {}

    def seed(
        local_name: str,
        canonical_name: str,
    ) -> None:
        resolved.setdefault(
            local_name,
            set(),
        ).add(canonical_name)

    def depend(
        source_name: str,
        target_name: str,
    ) -> None:
        dependencies.setdefault(
            source_name,
            set(),
        ).add(target_name)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module is not None
        ):
            for imported in node.names:
                if imported.name == "*":
                    continue

                canonical_name = (
                    f"{node.module}.{imported.name}"
                )

                if (
                    _dynamic_reason_for_callable_name(
                        canonical_name
                    )
                    is None
                ):
                    continue

                local_name = (
                    imported.asname
                    or imported.name
                )

                seed(
                    local_name,
                    canonical_name,
                )

        assignment_targets: tuple[str, ...] = ()
        assignment_value: ast.AST | None = None

        if isinstance(node, ast.Assign):
            assignment_targets = tuple(
                sorted(
                    {
                        target_name
                        for target in node.targets
                        for target_name
                        in _assignment_target_names(
                            target
                        )
                    }
                )
            )
            assignment_value = node.value

        elif isinstance(node, ast.AnnAssign):
            assignment_targets = (
                _assignment_target_names(
                    node.target
                )
            )
            assignment_value = node.value

        elif isinstance(node, ast.NamedExpr):
            assignment_targets = (
                _assignment_target_names(
                    node.target
                )
            )
            assignment_value = node.value

        if (
            not assignment_targets
            or assignment_value is None
        ):
            continue

        for source_name in _alias_source_names(
            assignment_value
        ):
            reason = (
                _dynamic_reason_for_callable_name(
                    source_name
                )
            )

            for target_name in assignment_targets:
                if reason is not None:
                    seed(
                        target_name,
                        source_name,
                    )
                else:
                    depend(
                        source_name,
                        target_name,
                    )

    pending = sorted(resolved)
    index = 0

    while index < len(pending):
        source_name = pending[index]
        index += 1

        source_values = resolved.get(
            source_name,
            set(),
        )

        if not source_values:
            continue

        for target_name in sorted(
            dependencies.get(
                source_name,
                (),
            )
        ):
            target_values = resolved.setdefault(
                target_name,
                set(),
            )

            before = len(target_values)
            target_values.update(source_values)

            if len(target_values) != before:
                pending.append(target_name)

    return {
        alias_name: tuple(
            sorted(canonical_names)
        )
        for alias_name, canonical_names
        in sorted(resolved.items())
    }


def _resolved_callable_names(
    node: ast.AST,
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    names: set[str] = set()

    if isinstance(node, ast.Name):
        names.add(node.id)
        names.update(
            aliases.get(
                node.id,
                (),
            )
        )

    elif isinstance(node, ast.Attribute):
        name = _call_name(node)

        if name is not None:
            names.add(name)

    elif isinstance(node, ast.Subscript):
        names.update(
            _resolved_callable_names(
                node.value,
                aliases,
            )
        )

    elif isinstance(node, ast.IfExp):
        names.update(
            _resolved_callable_names(
                node.body,
                aliases,
            )
        )
        names.update(
            _resolved_callable_names(
                node.orelse,
                aliases,
            )
        )

    elif isinstance(node, ast.BoolOp):
        for value in node.values:
            names.update(
                _resolved_callable_names(
                    value,
                    aliases,
                )
            )

    elif isinstance(node, ast.NamedExpr):
        names.update(
            _resolved_callable_names(
                node.value,
                aliases,
            )
        )

    return tuple(sorted(names))


def _is_literal_module_loader(
    name: str,
) -> bool:
    tail = name.rsplit(".", 1)[-1]

    return tail in {
        "__import__",
        "import_module",
    }


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
    callable_aliases = _dangerous_callable_aliases(tree)

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

        elif isinstance(
            node,
            (
                ast.Name,
                ast.Attribute,
                ast.Subscript,
            ),
        ):
            for callable_name in (
                _resolved_callable_names(
                    node,
                    callable_aliases,
                )
            ):
                reason_code = (
                    _dynamic_reason_for_callable_name(
                        callable_name
                    )
                )

                if reason_code is not None:
                    unresolved.add(
                        UnresolvedReference(
                            "DYNAMIC",
                            reason_code,
                        )
                    )

        elif isinstance(node, ast.Call):
            callable_names = (
                _resolved_callable_names(
                    node.func,
                    callable_aliases,
                )
            )

            if (
                any(
                    _is_literal_module_loader(
                        callable_name
                    )
                    for callable_name
                    in callable_names
                )
                and node.args
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

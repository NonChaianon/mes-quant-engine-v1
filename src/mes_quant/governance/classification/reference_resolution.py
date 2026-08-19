from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .reference_objects import TrackedObject

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MODULE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)


class ReferenceResolutionError(RuntimeError):
    """Raised when static repository reference identities cannot be resolved safely."""


@dataclass(frozen=True)
class PythonModuleIndex:
    module_to_paths: dict[str, tuple[bytes, ...]]
    path_to_module: dict[bytes, str]


def _python_paths(
    tracked_objects: Iterable[TrackedObject],
) -> frozenset[bytes]:
    return frozenset(
        item.path_bytes
        for item in tracked_objects
        if item.object_type == "blob"
        and item.mode in {"100644", "100755"}
        and item.path_bytes.endswith(b".py")
    )


def _ascii_component(value: bytes) -> str | None:
    try:
        decoded = value.decode("ascii")
    except UnicodeDecodeError:
        return None

    if _IDENTIFIER_RE.fullmatch(decoded) is None:
        return None

    return decoded


def _module_for_python_path(
    path: bytes,
    python_paths: frozenset[bytes],
) -> str | None:
    """Derive a real importable module from package markers in the Git tree.

    No fixed repository source-root convention is assumed. Package ancestry is
    derived from tracked __init__.py objects.
    """

    parts = path.split(b"/")

    if not parts or not parts[-1].endswith(b".py"):
        return None

    filename = parts[-1]

    if filename == b"__init__.py":
        directory_parts = parts[:-1]

        if not directory_parts:
            return None

        package_parts: list[str] = []
        index = len(directory_parts) - 1

        while index >= 0:
            package_component = _ascii_component(
                directory_parts[index]
            )

            if package_component is None:
                break

            init_path = b"/".join(
                directory_parts[: index + 1]
                + [b"__init__.py"]
            )

            if init_path not in python_paths:
                break

            package_parts.append(package_component)
            index -= 1

        if not package_parts:
            return None

        return ".".join(reversed(package_parts))

    stem = filename[:-3]
    module_component = _ascii_component(stem)

    if module_component is None:
        return None

    package_parts: list[str] = []
    directory_parts = parts[:-1]
    index = len(directory_parts) - 1

    while index >= 0:
        package_component = _ascii_component(
            directory_parts[index]
        )

        if package_component is None:
            break

        init_path = b"/".join(
            directory_parts[: index + 1]
            + [b"__init__.py"]
        )

        if init_path not in python_paths:
            break

        package_parts.append(package_component)
        index -= 1

    if not package_parts:
        return None

    return ".".join(
        [
            *reversed(package_parts),
            module_component,
        ]
    )


def build_python_module_index(
    tracked_objects: Iterable[TrackedObject],
) -> PythonModuleIndex:
    """Build deterministic module identities from the actual immutable Git tree."""

    objects = tuple(tracked_objects)
    python_paths = _python_paths(objects)

    module_paths: dict[str, list[bytes]] = {}
    path_to_module: dict[bytes, str] = {}

    for path in sorted(python_paths):
        module = _module_for_python_path(
            path,
            python_paths,
        )

        if module is None:
            continue

        if path in path_to_module:
            raise ReferenceResolutionError(
                "duplicate Python path identity"
            )

        path_to_module[path] = module
        module_paths.setdefault(module, []).append(path)

    canonical_module_paths = {
        module: tuple(sorted(paths))
        for module, paths in sorted(module_paths.items())
    }

    return PythonModuleIndex(
        module_to_paths=canonical_module_paths,
        path_to_module=dict(
            sorted(path_to_module.items())
        ),
    )


def resolve_module_reference(
    module_name: str,
    module_index: PythonModuleIndex,
) -> tuple[bytes, ...]:
    """Resolve one exact dotted module reference to actual Git-tree paths."""

    if (
        not isinstance(module_name, str)
        or _MODULE_RE.fullmatch(module_name) is None
    ):
        raise ReferenceResolutionError(
            f"invalid dotted module reference: {module_name!r}"
        )

    return module_index.module_to_paths.get(
        module_name,
        (),
    )


def protected_module_nodes(
    protected_modules: Iterable[str],
    module_index: PythonModuleIndex,
) -> tuple[bytes, ...]:
    """Resolve every frozen protected root and all dotted descendants."""

    roots = tuple(
        sorted(
            set(protected_modules)
        )
    )

    for root in roots:
        if (
            not isinstance(root, str)
            or _MODULE_RE.fullmatch(root) is None
        ):
            raise ReferenceResolutionError(
                f"invalid protected module: {root!r}"
            )

    protected: set[bytes] = set()

    for root in roots:
        matched = False

        for module, paths in (
            module_index.module_to_paths.items()
        ):
            if (
                module == root
                or module.startswith(root + ".")
            ):
                protected.update(paths)
                matched = True

        if not matched:
            raise ReferenceResolutionError(
                "protected module cannot be resolved: "
                f"{root}"
            )

    return tuple(sorted(protected))

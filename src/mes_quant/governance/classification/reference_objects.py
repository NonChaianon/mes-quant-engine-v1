from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Iterator

_SHA1_TEXT_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA1_BYTES_RE = re.compile(rb"^[0-9a-f]{40}$")
_ALLOWED_MODES = {b"100644", b"100755", b"120000", b"160000"}


class ReferenceObjectError(RuntimeError):
    """Raised when trusted Git-object reference inputs cannot be read safely."""


@dataclass(frozen=True)
class TrackedObject:
    path_bytes: bytes
    mode: str
    object_type: str
    object_sha1: str


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


def _git_argv(repo: str | Path, *args: str) -> list[str]:
    return ["git", "--no-replace-objects", "-C", str(repo), *args]


def _require_positive_limit(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ReferenceObjectError(f"{name} must be a positive integer")


def _resolve_commit(repo: str | Path, commit_sha1: str) -> str:
    if _SHA1_TEXT_RE.fullmatch(commit_sha1) is None:
        raise ReferenceObjectError(
            "commit_sha1 must be a lowercase 40-hex Git SHA-1"
        )

    try:
        completed = subprocess.run(
            _git_argv(
                repo,
                "rev-parse",
                "--verify",
                f"{commit_sha1}^{{commit}}",
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise ReferenceObjectError(
            "cannot resolve reference-scan commit"
        ) from exc

    resolved = completed.stdout.strip()

    if resolved != commit_sha1:
        raise ReferenceObjectError(
            "reference-scan commit resolution changed identity"
        )

    return resolved


def _iter_nul_fields(stream: object) -> Iterator[bytes]:
    buffer = bytearray()

    while True:
        chunk = stream.read(65536)

        if not chunk:
            break

        buffer.extend(chunk)

        while True:
            separator = buffer.find(b"\0")

            if separator < 0:
                break

            field = bytes(buffer[:separator])
            del buffer[: separator + 1]

            yield field

    if buffer:
        raise ReferenceObjectError(
            "unterminated NUL-delimited Git output"
        )


def list_tracked_objects(
    repo: str | Path,
    *,
    commit_sha1: str,
    max_tracked_objects: int,
) -> tuple[TrackedObject, ...]:
    """Enumerate one exact Git tree as raw-path inert object identities."""

    _require_positive_limit(
        max_tracked_objects,
        "max_tracked_objects",
    )

    commit = _resolve_commit(repo, commit_sha1)

    try:
        process = subprocess.Popen(
            _git_argv(
                repo,
                "ls-tree",
                "-r",
                "-z",
                "--full-tree",
                commit,
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
    except OSError as exc:
        raise ReferenceObjectError(
            f"cannot start git ls-tree: {exc}"
        ) from exc

    objects: list[TrackedObject] = []

    try:
        with process:
            if process.stdout is None or process.stderr is None:
                raise ReferenceObjectError(
                    "git ls-tree pipes unavailable"
                )

            for field in _iter_nul_fields(process.stdout):
                if len(objects) >= max_tracked_objects:
                    raise ReferenceObjectError(
                        "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
                        f"max_tracked_objects={max_tracked_objects}"
                    )

                try:
                    header, path = field.split(b"\t", 1)
                    mode, object_type, sha1 = header.split(b" ", 2)
                except ValueError as exc:
                    raise ReferenceObjectError(
                        f"invalid git ls-tree entry: {field!r}"
                    ) from exc

                if mode not in _ALLOWED_MODES:
                    raise ReferenceObjectError(
                        f"unsupported Git mode: {mode!r}"
                    )

                if object_type not in {b"blob", b"commit"}:
                    raise ReferenceObjectError(
                        f"unsupported Git object type: {object_type!r}"
                    )

                if _SHA1_BYTES_RE.fullmatch(sha1) is None:
                    raise ReferenceObjectError(
                        f"invalid Git object SHA-1: {sha1!r}"
                    )

                if not path:
                    raise ReferenceObjectError(
                        "empty Git path is invalid"
                    )

                if mode == b"160000" and object_type != b"commit":
                    raise ReferenceObjectError(
                        "gitlink must reference a commit"
                    )

                if mode != b"160000" and object_type != b"blob":
                    raise ReferenceObjectError(
                        "tracked file must reference a blob"
                    )

                objects.append(
                    TrackedObject(
                        path_bytes=path,
                        mode=mode.decode("ascii"),
                        object_type=object_type.decode("ascii"),
                        object_sha1=sha1.decode("ascii"),
                    )
                )

            stderr = process.stderr.read()
            return_code = process.wait()

            if return_code != 0:
                raise ReferenceObjectError(
                    "git ls-tree failed: "
                    + stderr.decode("utf-8", "replace").strip()
                )

    except BaseException:
        if process.poll() is None:
            process.kill()

        process.communicate()
        raise

    objects.sort(key=lambda item: item.path_bytes)

    return tuple(objects)


def read_blob_bytes(
    repo: str | Path,
    *,
    blob_sha1: str,
    max_blob_bytes: int,
) -> bytes:
    """Read one immutable blob with a frozen pre-read byte ceiling."""

    _require_positive_limit(
        max_blob_bytes,
        "max_blob_bytes",
    )

    if _SHA1_TEXT_RE.fullmatch(blob_sha1) is None:
        raise ReferenceObjectError(
            "blob_sha1 must be a lowercase 40-hex Git SHA-1"
        )

    try:
        size_result = subprocess.run(
            _git_argv(
                repo,
                "cat-file",
                "-s",
                blob_sha1,
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise ReferenceObjectError(
            "cannot read Git object size"
        ) from exc

    try:
        size = int(size_result.stdout.strip())
    except ValueError as exc:
        raise ReferenceObjectError(
            "invalid Git object size"
        ) from exc

    if size > max_blob_bytes:
        raise ReferenceObjectError(
            "ANALYZER_RESOURCE_LIMIT_EXCEEDED: "
            f"max_blob_bytes={max_blob_bytes}"
        )

    try:
        completed = subprocess.run(
            _git_argv(
                repo,
                "cat-file",
                "blob",
                blob_sha1,
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise ReferenceObjectError(
            "cannot read Git blob"
        ) from exc

    if len(completed.stdout) != size:
        raise ReferenceObjectError(
            "Git blob size changed while reading"
        )

    return completed.stdout

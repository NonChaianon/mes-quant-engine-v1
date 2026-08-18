from __future__ import annotations

import base64
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

_SHA1_RE = re.compile(rb"^[0-9a-f]{40}$")
_ALLOWED_MODES = {b"100644", b"100755", b"120000", b"160000"}


class GitDeltaError(RuntimeError):
    """Raised when the canonical Git tree delta cannot be derived safely."""


@dataclass(frozen=True)
class DeltaEntry:
    operation: str
    old_path_bytes: bytes | None
    new_path_bytes: bytes | None
    old_blob_sha1: str | None
    new_blob_sha1: str | None
    old_mode: str | None
    new_mode: str | None
    old_object_type: str | None
    new_object_type: str | None

    def to_record(self) -> dict[str, object]:
        def path_b64(value: bytes | None) -> str | None:
            if value is None:
                return None
            return base64.b64encode(value).decode("ascii")

        return {
            "operation": self.operation,
            "old_path_bytes_base64": path_b64(self.old_path_bytes),
            "new_path_bytes_base64": path_b64(self.new_path_bytes),
            "old_blob_sha1": self.old_blob_sha1,
            "new_blob_sha1": self.new_blob_sha1,
            "old_mode": self.old_mode,
            "new_mode": self.new_mode,
            "old_object_type": self.old_object_type,
            "new_object_type": self.new_object_type,
        }


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


def _git_argv(repo: str | Path, *args: str) -> list[str]:
    return ["git", "--no-replace-objects", "-C", str(repo), *args]


def _normalize_mode(raw: bytes) -> str | None:
    if raw == b"000000":
        return None
    if raw not in _ALLOWED_MODES:
        raise GitDeltaError(f"unsupported Git mode: {raw!r}")
    return raw.decode("ascii")


def _normalize_sha(raw: bytes) -> str | None:
    if raw == b"0" * 40:
        return None
    if not _SHA1_RE.fullmatch(raw):
        raise GitDeltaError(f"invalid Git object SHA-1: {raw!r}")
    return raw.decode("ascii")


def _object_type(mode: str | None) -> str | None:
    if mode is None:
        return None
    return "commit" if mode == "160000" else "blob"


def _operation(status: bytes, old_mode: str | None, new_mode: str | None) -> str:
    code = status[:1]
    if code == b"A":
        return "ADD"
    if code == b"D":
        return "DELETE"
    if old_mode == "160000" or new_mode == "160000":
        return "SUBMODULE_POINTER_CHANGE"
    if old_mode == "120000" or new_mode == "120000":
        return "SYMLINK_CHANGE"
    if old_mode != new_mode:
        return "FILE_MODE_CHANGE"
    if code in {b"M", b"T"}:
        return "MODIFY"
    raise GitDeltaError(f"unsupported canonical Git status: {status!r}")


def canonical_git_tree_delta(
    repo: str | Path,
    *,
    base_commit_sha1: str,
    head_commit_sha1: str,
) -> tuple[DeltaEntry, ...]:
    """Derive a rename-disabled, raw-path-byte canonical tree delta."""

    try:
        completed = subprocess.run(
            _git_argv(
                repo,
                "diff-tree",
                "--no-commit-id",
                "--full-index",
                "-r",
                "--raw",
                "-z",
                "--no-renames",
                base_commit_sha1,
                head_commit_sha1,
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise GitDeltaError(
            f"git diff-tree failed: {exc.stderr.decode('utf-8', 'replace').strip()}"
        ) from exc

    fields = completed.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()

    entries: list[DeltaEntry] = []
    index = 0
    while index < len(fields):
        header = fields[index]
        index += 1
        if not header.startswith(b":"):
            raise GitDeltaError(f"invalid raw diff header: {header!r}")

        parts = header[1:].split()
        if len(parts) != 5:
            raise GitDeltaError(f"unexpected raw diff header field count: {header!r}")
        raw_old_mode, raw_new_mode, raw_old_sha, raw_new_sha, status = parts

        if status[:1] in {b"R", b"C"}:
            raise GitDeltaError("rename/copy status is forbidden by --no-renames authority")

        if index >= len(fields):
            raise GitDeltaError("raw diff path missing")
        path = fields[index]
        index += 1
        if not path:
            raise GitDeltaError("empty Git path is invalid")

        old_mode = _normalize_mode(raw_old_mode)
        new_mode = _normalize_mode(raw_new_mode)
        old_sha = _normalize_sha(raw_old_sha)
        new_sha = _normalize_sha(raw_new_sha)
        operation = _operation(status, old_mode, new_mode)

        old_path = None if operation == "ADD" else path
        new_path = None if operation == "DELETE" else path

        entries.append(
            DeltaEntry(
                operation=operation,
                old_path_bytes=old_path,
                new_path_bytes=new_path,
                old_blob_sha1=old_sha,
                new_blob_sha1=new_sha,
                old_mode=old_mode,
                new_mode=new_mode,
                old_object_type=_object_type(old_mode),
                new_object_type=_object_type(new_mode),
            )
        )

    entries.sort(
        key=lambda item: (
            item.new_path_bytes if item.new_path_bytes is not None else item.old_path_bytes or b"",
            item.operation.encode("ascii"),
        )
    )
    return tuple(entries)

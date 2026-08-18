from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class CandidateRelationError(RuntimeError):
    """Raised when the V1 single-commit candidate relation is not satisfied."""


@dataclass(frozen=True)
class CandidateRelation:
    base_commit_sha1: str
    head_commit_sha1: str
    merge_base_sha1: str
    base_tree_sha1: str
    head_tree_sha1: str
    parent_count: int


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


def _git_argv(repo: str | Path, *args: str) -> list[str]:
    return ["git", "--no-replace-objects", "-C", str(repo), *args]


def _git(repo: str | Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            _git_argv(repo, *args),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise CandidateRelationError(
            f"git command failed: {' '.join(args)}: {exc.stderr.strip()}"
        ) from exc
    return completed.stdout.strip()


def _require_full_sha1(value: str, label: str) -> None:
    if not _SHA1_RE.fullmatch(value):
        raise CandidateRelationError(f"{label} must be a lowercase 40-hex Git SHA-1")


def validate_candidate_relation(
    repo: str | Path,
    *,
    base_commit_sha1: str,
    head_commit_sha1: str,
) -> CandidateRelation:
    """Validate the frozen V1 SINGLE_COMMIT_CANDIDATE_ONLY relation."""

    _require_full_sha1(base_commit_sha1, "base_commit_sha1")
    _require_full_sha1(head_commit_sha1, "head_commit_sha1")

    resolved_base = _git(repo, "rev-parse", "--verify", f"{base_commit_sha1}^{{commit}}")
    resolved_head = _git(repo, "rev-parse", "--verify", f"{head_commit_sha1}^{{commit}}")
    if resolved_base != base_commit_sha1 or resolved_head != head_commit_sha1:
        raise CandidateRelationError("base/head commit resolution changed identity")

    parent_tokens = _git(repo, "rev-list", "--parents", "-n", "1", head_commit_sha1).split()
    parent_count = len(parent_tokens) - 1
    if parent_count != 1:
        raise CandidateRelationError(
            f"MULTI_COMMIT_CANDIDATE_UNSUPPORTED_V1: parent_count={parent_count}"
        )
    if parent_tokens[1] != base_commit_sha1:
        raise CandidateRelationError("CANDIDATE_RELATION_FAILURE: head.parent != base")

    merge_base = _git(repo, "merge-base", base_commit_sha1, head_commit_sha1)
    if merge_base != base_commit_sha1:
        raise CandidateRelationError("CANDIDATE_RELATION_FAILURE: merge_base != base")

    try:
        subprocess.run(
            _git_argv(
                repo,
                "merge-base",
                "--is-ancestor",
                base_commit_sha1,
                head_commit_sha1,
            ),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_env(),
        )
    except subprocess.CalledProcessError as exc:
        raise CandidateRelationError(
            "CANDIDATE_RELATION_FAILURE: base is not ancestor of head"
        ) from exc

    base_tree = _git(repo, "rev-parse", f"{base_commit_sha1}^{{tree}}")
    head_tree = _git(repo, "rev-parse", f"{head_commit_sha1}^{{tree}}")

    return CandidateRelation(
        base_commit_sha1=base_commit_sha1,
        head_commit_sha1=head_commit_sha1,
        merge_base_sha1=merge_base,
        base_tree_sha1=base_tree,
        head_tree_sha1=head_tree,
        parent_count=parent_count,
    )

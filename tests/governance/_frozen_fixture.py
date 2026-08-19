from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile


FROZEN_JSON_PATHS = (
    Path("configs/governance/PROTECTED_SURFACE_MANIFEST_V1.json"),
    Path("configs/governance/ANALYZER_LIMITS_V1.json"),
    Path("configs/governance/CLASSIFICATION_RECORD_SCHEMA_V1.json"),
)

FROZEN_INPUT_PATHS = (
    Path(
        "docs/governance/"
        "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
    ),
    *FROZEN_JSON_PATHS,
)


def read_frozen_bytes(source_root: Path, relative_path: Path) -> bytes:
    """Read exact frozen bytes from a normal repo or standalone audit package."""

    candidates = (
        source_root / relative_path,
        source_root / "frozen_authority" / relative_path,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_bytes()

    raise FileNotFoundError(
        f"frozen test input unavailable: {relative_path.as_posix()}"
    )


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        env=merged,
    ).strip()


class FrozenAuthorityFixture:
    """Temporary Git authority containing exact frozen Phase-1 authority bytes."""

    def __init__(self, source_root: Path) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.repo = Path(self._temp.name)

        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        _git(self.repo, "config", "user.name", "MES Test")
        _git(self.repo, "config", "user.email", "mes-test@example.invalid")

        for relative_path in FROZEN_INPUT_PATHS:
            destination = self.repo / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read_frozen_bytes(source_root, relative_path))

        _git(self.repo, "add", ".")

        deterministic_env = {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
        }
        _git(
            self.repo,
            "commit",
            "-q",
            "-m",
            "frozen test authority",
            env=deterministic_env,
        )
        self.authority_commit = _git(self.repo, "rev-parse", "HEAD")

    def close(self) -> None:
        self._temp.cleanup()

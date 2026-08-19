from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.classification.classifier import (
    ClassifierOrchestrationError,
    TrustedAnalyzerIdentities,
    classify_candidate,
)
from mes_quant.governance.classification.reference_analysis import (
    ReferenceAnalysisError,
)
from mes_quant.governance.classification.relation import (
    CandidateRelationError,
)
from tests.governance._frozen_fixture import (
    FROZEN_INPUT_PATHS,
    read_frozen_bytes,
)

SPEC_PATH = Path(
    "docs/governance/"
    "CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md"
)
MANIFEST_PATH = Path(
    "configs/governance/"
    "PROTECTED_SURFACE_MANIFEST_V1.json"
)

IDENTITIES = TrustedAnalyzerIdentities(
    classifier_implementation_sha256="A" * 64,
    analyzer_config_sha256="B" * 64,
    analyzer_toolchain_digest=(
        "sha256:" + ("c" * 64)
    ),
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class ClassifierOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)

        subprocess.run(
            ["git", "init", "-q", str(self.repo)],
            check=True,
        )
        _git(
            self.repo,
            "config",
            "user.name",
            "MES Test",
        )
        _git(
            self.repo,
            "config",
            "user.email",
            "mes-test@example.invalid",
        )

        # Build one exact authority/base commit containing all frozen
        # inputs and real package markers for every protected module.
        for relative_path in FROZEN_INPUT_PATHS:
            destination = self.repo / relative_path
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_bytes(
                read_frozen_bytes(
                    PROJECT_ROOT,
                    relative_path,
                )
            )

        manifest = json.loads(
            read_frozen_bytes(
                PROJECT_ROOT,
                MANIFEST_PATH,
            ).decode("utf-8")
        )

        protected_modules = tuple(
            sorted(
                manifest["protected_quant_modules"]
            )
        )

        self.assertTrue(protected_modules)

        # Use one real protected module for positive reachability tests.
        self.protected_module = next(
            (
                module
                for module in protected_modules
                if module != "mes_quant"
            ),
            protected_modules[0],
        )

        # Create actual immutable Git-tree package markers. The resolver
        # derives module identities from these files, not from a hard-coded
        # source-root declaration.
        for module_name in protected_modules:
            parts = module_name.split(".")

            for depth in range(
                1,
                len(parts) + 1,
            ):
                init_path = (
                    self.repo
                    / "src"
                    / Path(*parts[:depth])
                    / "__init__.py"
                )
                init_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                if not init_path.exists():
                    init_path.write_text(
                        "",
                        encoding="utf-8",
                    )

        self.base = self._commit(
            "frozen authority base"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _commit(self, message: str) -> str:
        _git(self.repo, "add", "-A")
        _git(
            self.repo,
            "commit",
            "-q",
            "-m",
            message,
        )
        return _git(
            self.repo,
            "rev-parse",
            "HEAD",
        )

    def _make_head(
        self,
        files: dict[str, str],
    ) -> str:
        for relative_path, content in files.items():
            path = self.repo / relative_path
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            path.write_text(
                content,
                encoding="utf-8",
            )

        return self._commit("candidate")

    def _run(
        self,
        head: str,
        *,
        authority: str | None = None,
        identities: TrustedAnalyzerIdentities = IDENTITIES,
    ):
        return classify_candidate(
            self.repo,
            authority_commit_sha1=(
                authority or self.base
            ),
            base_commit_sha1=self.base,
            head_commit_sha1=head,
            trusted_identities=identities,
        )

    def test_successful_run_binds_all_exact_facts(self) -> None:
        head = self._make_head(
            {
                "app/__init__.py": "",
                "app/view.py": (
                    f"import {self.protected_module}\n"
                ),
            }
        )

        result = self._run(head)

        expected_spec_sha256 = (
            hashlib.sha256(
                read_frozen_bytes(
                    PROJECT_ROOT,
                    SPEC_PATH,
                )
            )
            .hexdigest()
            .upper()
        )

        self.assertEqual(
            result.relation.base_commit_sha1,
            self.base,
        )
        self.assertEqual(
            result.relation.head_commit_sha1,
            head,
        )
        self.assertEqual(
            result.frozen_inputs.authority_commit_sha1,
            self.base,
        )
        self.assertEqual(
            result.record[
                "classifier_spec_sha256"
            ],
            expected_spec_sha256,
        )
        self.assertEqual(
            result.record[
                "classifier_implementation_sha256"
            ],
            "A" * 64,
        )
        self.assertEqual(
            result.record[
                "analyzer_config_sha256"
            ],
            "B" * 64,
        )
        self.assertIn(
            "QUANT_ENGINE",
            result.decision.detected_classes,
        )
        self.assertIn(
            "CROSS_BOUNDARY",
            result.decision.detected_classes,
        )
        self.assertEqual(
            result.decision.classification_outcome,
            "CLASSIFIED",
        )
        self.assertEqual(
            result.record["failure_state"],
            "NONE",
        )
        self.assertEqual(
            json.loads(
                result.canonical_record_bytes
            ),
            result.record,
        )
        self.assertTrue(
            result.canonical_record_bytes.endswith(
                b"\n"
            )
        )

    def test_dynamic_behavior_produces_ambiguous_record(self) -> None:
        head = self._make_head(
            {
                "app/__init__.py": "",
                "app/view.py": (
                    "import importlib\n"
                    "name = 'mes_quant.' + 'features'\n"
                    "importlib.import_module(name)\n"
                ),
            }
        )

        result = self._run(head)

        self.assertEqual(
            result.decision.classification_outcome,
            "AMBIGUOUS",
        )
        self.assertIn(
            "CROSS_BOUNDARY",
            result.decision.detected_classes,
        )
        self.assertTrue(
            result.record["unresolved_nodes"]
        )
        self.assertEqual(
            result.record[
                "classification_outcome"
            ],
            "AMBIGUOUS",
        )

    def test_candidate_top_level_code_is_never_executed(self) -> None:
        marker = (
            self.repo
            / "CANDIDATE_EXECUTED_MARKER"
        )

        source = (
            "from pathlib import Path\n"
            f"Path({marker.as_posix()!r}).write_text("
            "'executed', encoding='utf-8')\n"
            "raise RuntimeError('candidate was executed')\n"
            f"import {self.protected_module}\n"
        )

        head = self._make_head(
            {
                "candidate/conftest.py": source,
            }
        )

        result = self._run(head)

        self.assertFalse(marker.exists())
        self.assertIn(
            "QUANT_ENGINE",
            result.decision.detected_classes,
        )

    def test_worktree_tamper_cannot_change_committed_result(self) -> None:
        head = self._make_head(
            {
                "app/__init__.py": "",
                "app/view.py": (
                    f"import {self.protected_module}\n"
                ),
            }
        )

        first = self._run(head)

        # Tamper with candidate and frozen-authority files only in the
        # working tree. Exact Git-object analysis must remain unchanged.
        (self.repo / "app/view.py").write_text(
            "def broken(:\n",
            encoding="utf-8",
        )
        (self.repo / SPEC_PATH).write_text(
            "TAMPERED WORKTREE ONLY\n",
            encoding="utf-8",
        )

        second = self._run(head)

        self.assertEqual(
            first.canonical_record_bytes,
            second.canonical_record_bytes,
        )
        self.assertEqual(
            first.record,
            second.record,
        )

    def test_repeated_run_is_deterministic_and_does_not_write(self) -> None:
        head = self._make_head(
            {
                "app/__init__.py": "",
                "app/view.py": (
                    f"import {self.protected_module}\n"
                ),
            }
        )

        status_before = _git(
            self.repo,
            "status",
            "--porcelain=v1",
        )

        first = self._run(head)
        second = self._run(head)

        status_after = _git(
            self.repo,
            "status",
            "--porcelain=v1",
        )

        self.assertEqual(
            first.canonical_record_bytes,
            second.canonical_record_bytes,
        )
        self.assertEqual(status_before, "")
        self.assertEqual(status_after, "")

    def test_wrong_authority_commit_fails_closed(self) -> None:
        head = self._make_head(
            {
                "app/view.py": "VALUE = 1\n",
            }
        )

        with self.assertRaisesRegex(
            ClassifierOrchestrationError,
            "authority commit must equal candidate base",
        ):
            self._run(
                head,
                authority=head,
            )

    def test_invalid_trusted_identity_fails_before_analysis(self) -> None:
        head = self._make_head(
            {
                "app/view.py": "VALUE = 1\n",
            }
        )

        invalid = TrustedAnalyzerIdentities(
            classifier_implementation_sha256=(
                "a" * 64
            ),
            analyzer_config_sha256="B" * 64,
            analyzer_toolchain_digest=(
                "sha256:" + ("c" * 64)
            ),
        )

        with self.assertRaisesRegex(
            ClassifierOrchestrationError,
            "uppercase 64-hex",
        ):
            self._run(
                head,
                identities=invalid,
            )

    def test_relation_failure_produces_no_run(self) -> None:
        with self.assertRaises(
            CandidateRelationError
        ):
            self._run(self.base)

    def test_mandatory_parse_failure_produces_no_record(self) -> None:
        head = self._make_head(
            {
                "app/broken.py": "def broken(:\n",
            }
        )

        status_before = _git(
            self.repo,
            "status",
            "--porcelain=v1",
        )

        with self.assertRaises(
            ReferenceAnalysisError
        ):
            self._run(head)

        status_after = _git(
            self.repo,
            "status",
            "--porcelain=v1",
        )

        self.assertEqual(status_before, "")
        self.assertEqual(status_after, "")


if __name__ == "__main__":
    unittest.main()

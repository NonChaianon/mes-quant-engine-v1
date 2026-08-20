from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mes_quant.governance.sentinel.orchestrator import (
    GovernanceSentinelOrchestrationError,
    run_governance_sentinel,
)
from tests.governance.test_sentinel_orchestrator import (
    CandidateRepo,
    MANIFEST_PATH,
    git,
)


class GovernanceSentinelOrchestratorAdversarialTests(
    unittest.TestCase
):
    def make_repo(self) -> CandidateRepo:
        fixture = CandidateRepo()
        self.addCleanup(fixture.close)
        return fixture

    def test_candidate_manifest_symlink_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH
        path.unlink()
        path.symlink_to("untrusted-manifest.json")

        head = fixture.commit(
            "candidate manifest symlink"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            run_governance_sentinel(
                str(fixture.repo),
                authority_commit_sha1=fixture.base,
                base_commit_sha1=fixture.base,
                head_commit_sha1=head,
            )

    def test_noncanonical_candidate_manifest_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH

        payload = json.loads(
            path.read_text(encoding="utf-8")
        )

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=True,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "noncanonical candidate manifest"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            run_governance_sentinel(
                str(fixture.repo),
                authority_commit_sha1=fixture.base,
                base_commit_sha1=fixture.base,
                head_commit_sha1=head,
            )

    def test_duplicate_candidate_json_key_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH

        text = path.read_text(
            encoding="utf-8"
        )

        needle = (
            '"schema":'
            '"PROTECTED_SURFACE_MANIFEST_V1"'
        )

        if needle not in text:
            raise AssertionError(
                "expected schema field not found"
            )

        replacement = (
            needle
            + ","
            + needle
        )

        path.write_text(
            text.replace(
                needle,
                replacement,
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "duplicate candidate manifest key"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            run_governance_sentinel(
                str(fixture.repo),
                authority_commit_sha1=fixture.base,
                base_commit_sha1=fixture.base,
                head_commit_sha1=head,
            )

    def test_candidate_manifest_blob_limit_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = fixture.repo / MANIFEST_PATH

        # Frozen max_blob_bytes = 10,485,760.
        # This candidate blob exceeds that authority
        # before JSON parsing can become privileged.
        oversized = (
            b'{"payload":"'
            + (b"a" * 10_485_761)
            + b'"}\n'
        )

        path.write_bytes(oversized)

        head = fixture.commit(
            "oversized candidate manifest"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            run_governance_sentinel(
                str(fixture.repo),
                authority_commit_sha1=fixture.base,
                base_commit_sha1=fixture.base,
                head_commit_sha1=head,
            )

    def test_multi_commit_candidate_relation_fails_closed(
        self,
    ) -> None:
        fixture = self.make_repo()

        path = (
            fixture.repo
            / "src/mes_quant/features/builder.py"
        )

        path.write_text(
            "VALUE = 2\n",
            encoding="utf-8",
            newline="\n",
        )

        fixture.commit(
            "candidate commit one"
        )

        path.write_text(
            "VALUE = 3\n",
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "candidate commit two"
        )

        with self.assertRaises(
            GovernanceSentinelOrchestrationError
        ):
            run_governance_sentinel(
                str(fixture.repo),
                authority_commit_sha1=fixture.base,
                base_commit_sha1=fixture.base,
                head_commit_sha1=head,
            )

    def test_candidate_is_not_checked_out_or_executed(
        self,
    ) -> None:
        fixture = self.make_repo()

        marker = (
            fixture.repo
            / "CANDIDATE_EXECUTED_MARKER"
        )

        path = (
            fixture.repo
            / "src/mes_quant/features/builder.py"
        )

        candidate_code = (
            "from pathlib import Path\n"
            f"Path({str(marker)!r})."
            "write_text('executed')\n"
            "VALUE = 2\n"
        )

        path.write_text(
            candidate_code,
            encoding="utf-8",
            newline="\n",
        )

        head = fixture.commit(
            "hostile executable candidate"
        )

        # Put the physical working tree back on BASE.
        # Sentinel receives HEAD only as immutable Git identity.
        git(
            fixture.repo,
            "checkout",
            "-q",
            "--detach",
            fixture.base,
        )

        before_head = git(
            fixture.repo,
            "rev-parse",
            "HEAD",
        )

        before_bytes = path.read_bytes()

        self.assertEqual(
            before_head,
            fixture.base,
        )

        self.assertEqual(
            before_bytes,
            b"VALUE = 1\n",
        )

        self.assertFalse(
            marker.exists()
        )

        result = run_governance_sentinel(
            str(fixture.repo),
            authority_commit_sha1=fixture.base,
            base_commit_sha1=fixture.base,
            head_commit_sha1=head,
        )

        after_head = git(
            fixture.repo,
            "rev-parse",
            "HEAD",
        )

        after_bytes = path.read_bytes()

        self.assertFalse(
            result.sentinel_result.intercepted
        )

        self.assertTrue(
            result.sentinel_result
            .ordinary_classifier_allowed
        )

        self.assertEqual(
            after_head,
            fixture.base,
        )

        self.assertEqual(
            after_bytes,
            before_bytes,
        )

        self.assertFalse(
            marker.exists()
        )


if __name__ == "__main__":
    unittest.main()

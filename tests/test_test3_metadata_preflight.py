from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from mes_quant.exploration import test3_metadata_preflight as g2
from tools import run_test3_g2_metadata_preflight as g2_tool


class Test3G2MetadataPreflightTests(unittest.TestCase):
    maxDiff = None

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _fixture(self, root: Path):
        paths: dict[str, Path] = {}
        specs: list[g2.ArtifactSpec] = []
        for original in g2._ARTIFACT_SPECS:
            path = root / original.artifact_id / original.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if original.required_columns:
                table = pa.table({name: pa.array([1, 2]) for name in original.required_columns})
                pq.write_table(table, path, row_group_size=1)
            else:
                path.write_bytes(b"synthetic opaque dbn bytes\n")
            paths[original.artifact_id] = path
            specs.append(
                g2.ArtifactSpec(
                    original.artifact_id,
                    original.filename,
                    self._sha(path),
                    original.manifest_artifact_id,
                    original.required_columns,
                )
            )

        decoded_hash = "d" * 64
        manifest_root = root / "manifests/releases"
        manifest_root.mkdir(parents=True, exist_ok=True)
        frozen = manifest_root / "frozen_colab_manifest_v1.json"
        frozen.write_text(
            json.dumps(
                {
                    "artifacts": [
                        {
                            "id": spec.manifest_artifact_id,
                            "file": spec.filename,
                            "sha256": spec.expected_sha256,
                        }
                        for spec in specs[:4]
                    ]
                    + [
                        {
                            "id": "decoded_memory_content",
                            "file": None,
                            "sha256": decoded_hash,
                        }
                    ],
                    "golden_counts": {"raw_rows": g2.DECODED_MES_1M_ROW_COUNT},
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        frozen_hash = self._sha(frozen)
        ordered_hash = "e" * 64
        release = manifest_root / "cell14_local_release_v1.json"
        runs = {}
        for role, run_id in (("canonical", "synthetic-canonical"), ("replay", "synthetic-replay")):
            runs[role] = {
                "run_id": run_id,
                "artifacts": {
                    "features": {
                        "file": (
                            f"artifacts/runs/{run_id}/"
                            "cell14_development_point_in_time_features_v1.parquet"
                        ),
                        "sha256": specs[4].expected_sha256,
                        "content_sha256": ordered_hash,
                    }
                },
            }
        release.write_text(
            json.dumps(
                {
                    "canonical_run_id": "synthetic-canonical",
                    "replay_run_id": "synthetic-replay",
                    "controls": {
                        "frozen_colab_manifest": {"sha256": frozen_hash}
                    },
                    "runs": runs,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "paths": paths,
            "specs": tuple(specs),
            "frozen": frozen,
            "frozen_hash": frozen_hash,
            "release": release,
            "release_hash": self._sha(release),
            "decoded_hash": decoded_hash,
            "ordered_hash": ordered_hash,
            "feature_hash": specs[4].expected_sha256,
        }

    @staticmethod
    def _git_context() -> g2._GitContext:
        return g2._GitContext("a" * 40, "b" * 40, g2.G2_BRANCH, "a" * 40)

    @staticmethod
    def _authorization(root: Path) -> g2._ObservedAuthorization:
        return g2._ObservedAuthorization(
            authorization_id=g2.G2_AUTHORIZATION_ID,
            document_sha256=g2.G2_AUTHORIZATION_DOCUMENT_SHA256,
            code_identity="a" * 40,
            tree_identity="b" * 40,
            reservation_path=root / "authorization.consumed.json",
            reservation_file_sha256="c" * 64,
            _verification_key=g2._AUTHORIZATION_KEY,
        )

    def _build(self, root: Path, *, timestamp: str = "2026-08-24T00:00:00Z"):
        fixture = self._fixture(root)
        patches = (
            patch.object(g2, "_ARTIFACT_SPECS", fixture["specs"]),
            patch.object(g2, "FROZEN_COLAB_MANIFEST_SHA256", fixture["frozen_hash"]),
            patch.object(g2, "CELL14_RELEASE_MANIFEST_SHA256", fixture["release_hash"]),
            patch.object(g2, "DECODED_MES_1M_SHA256", fixture["decoded_hash"]),
            patch.object(g2, "CELL14_ORDERED_FEATURE_SHA256", fixture["ordered_hash"]),
            patch.object(g2, "CELL14_FEATURE_FILE_SHA256", fixture["feature_hash"]),
            patch.object(g2, "_assert_forbidden_modules_absent"),
        )
        with ExitStack() as stack:
            for context in patches:
                stack.enter_context(context)
            record = g2.build_g2_metadata_preflight_record(
                fixture["paths"],
                project_root=root,
                cell14_release_manifest_path=fixture["release"],
                frozen_colab_manifest_path=fixture["frozen"],
                cell14_run_id="synthetic-canonical",
                git_context=self._git_context(),
                authorization=self._authorization(root),
                document_bindings={"synthetic": {"match": True}},
                audit_written_utc=timestamp,
            )
        return fixture, record

    def test_record_is_exactly_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _fixture, record = self._build(Path(temporary))
        self.assertEqual(record["status"], "PASS")
        self.assertEqual(record["safety_counters"], g2._SAFETY_COUNTERS)
        self.assertEqual(record["not_computed"], g2._NOT_COMPUTED)
        self.assertTrue(record["local_upstream_equal"])
        self.assertEqual(record["repository_strategy"]["source_pr_number"], 47)
        self.assertEqual(
            record["repository_strategy"]["execution_strategy"],
            "DIRECT_DESCENDANT_BRANCH_NO_MERGE",
        )
        self.assertFalse(record["repository_strategy"]["merge_authorized"])
        self.assertEqual(len(record["artifacts"]), 5)
        self.assertEqual(record["allowed_metadata_counters"]["parquet_footers_opened"], 4)
        self.assertNotIn("request_set_sha256", json.dumps(record, sort_keys=True))
        self.assertEqual(record["validation_status"], "UNOPENED")
        self.assertEqual(record["final_test_status"], "SEALED")
        self.assertEqual(record["g2p_status"], "NOT_AUTHORIZED")

    def test_record_identity_is_stable_across_roots_and_audit_times(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            _fixture_one, one = self._build(
                Path(first), timestamp="2026-08-24T00:00:00Z"
            )
            _fixture_two, two = self._build(
                Path(second), timestamp="2026-08-25T00:00:00Z"
            )
        self.assertEqual(one["run_id"], two["run_id"])
        self.assertEqual(one["record_sha256"], two["record_sha256"])

    def test_wrong_or_forged_authorization_fails_before_artifact_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = self._fixture(root)
            forged = g2._ObservedAuthorization(
                g2.G2_AUTHORIZATION_ID,
                g2.G2_AUTHORIZATION_DOCUMENT_SHA256,
                "a" * 40,
                "b" * 40,
                root / "reservation",
                "c" * 64,
                object(),
            )
            with (
                patch.object(g2, "_inspect_artifact") as inspect,
                self.assertRaisesRegex(g2.Test3G2BoundaryError, "verified, consumed"),
            ):
                g2.build_g2_metadata_preflight_record(
                    fixture["paths"],
                    project_root=root,
                    cell14_release_manifest_path=fixture["release"],
                    frozen_colab_manifest_path=fixture["frozen"],
                    cell14_run_id="synthetic-canonical",
                    git_context=self._git_context(),
                    authorization=forged,
                    document_bindings={},
                )
            inspect.assert_not_called()

    def test_wrong_filename_and_hash_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = self._fixture(root)
            spec = fixture["specs"][0]
            wrong_name = root / "wrong.dbn.zst"
            wrong_name.write_bytes(fixture["paths"]["raw_dbn"].read_bytes())
            with self.assertRaisesRegex(g2.Test3G2BoundaryError, "requires filename"):
                g2._inspect_artifact(wrong_name, spec)
            fixture["paths"]["raw_dbn"].write_bytes(b"changed")
            with self.assertRaisesRegex(g2.Test3G2BoundaryError, "SHA-256 mismatch"):
                g2._inspect_artifact(fixture["paths"]["raw_dbn"], spec)

    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.write_bytes(b"x")
            link = root / "link"
            link.symlink_to(target)
            with (
                self.assertRaisesRegex(g2.Test3G2BoundaryError, "symlink"),
                g2._open_regular_file(link),
            ):
                self.fail("symlink must not open")

    def test_footer_reader_never_accesses_row_groups_or_statistics(self) -> None:
        class Metadata:
            num_rows = 2
            num_row_groups = 1

            def row_group(self, _index: int):
                raise AssertionError("row_group must not be accessed")

        fake = SimpleNamespace(
            schema_arrow=SimpleNamespace(names=("required",)),
            metadata=Metadata(),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.parquet"
            path.write_bytes(b"opaque")
            spec = g2.ArtifactSpec(
                "fixture", path.name, self._sha(path), "fixture", ("required",)
            )
            with patch.object(g2.pq, "ParquetFile", return_value=fake):
                record = g2._inspect_artifact(path, spec)
        self.assertEqual(record["parquet_total_rows"], 2)
        self.assertEqual(record["parquet_total_row_groups"], 1)

    def test_duplicate_manifest_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text('{"a":1,"a":2}\n', encoding="utf-8")
            expected = self._sha(path)
            with self.assertRaisesRegex(g2.Test3G2BoundaryError, "duplicate key"):
                g2._read_manifest(path, expected_sha256=expected)

    def test_forbidden_module_import_is_detected(self) -> None:
        with (
            patch.dict(sys.modules, {"databento": SimpleNamespace()}),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "forbidden modules"),
        ):
            g2._assert_forbidden_modules_absent(phase="synthetic")

    def test_source_has_no_forbidden_experiment_import_or_row_reader(self) -> None:
        source = Path(g2.__file__).read_text(encoding="utf-8")
        forbidden = (
            "import test2_l1_harness",
            "from mes_quant.exploration.test3_target import",
            "from mes_quant.exploration.test3_design import",
            "from mes_quant.exploration.test3_stats import",
            "read_table(",
            "read_parquet(",
            ".row_group(",
            ".statistics",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_authorization_reservation_is_create_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / g2.G2_AUTHORIZATION_DOCUMENT
            document.parent.mkdir(parents=True)
            document.write_bytes(b"synthetic authorization")
            observed = self._sha(document)
            output = root / "artifacts/exploration/test3/g2"
            with patch.object(g2, "G2_AUTHORIZATION_DOCUMENT_SHA256", observed):
                first = g2._consume_authorization(
                    project_root=root,
                    output_root=output,
                    git_context=self._git_context(),
                    authorization_token=g2.G2_AUTHORIZATION_TOKEN,
                )
                self.assertTrue(first.reservation_path.is_file())
                with self.assertRaisesRegex(g2.Test3G2BoundaryError, "already consumed"):
                    g2._consume_authorization(
                        project_root=root,
                        output_root=output,
                        git_context=self._git_context(),
                        authorization_token=g2.G2_AUTHORIZATION_TOKEN,
                    )

    def test_record_publish_is_create_once_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _fixture, record = self._build(root / "fixture")
            output_root = root / "evidence"
            output, file_sha = g2.write_g2_metadata_preflight_record(
                record, output_root=output_root
            )
            self.assertEqual(file_sha, self._sha(output))
            with self.assertRaises(FileExistsError):
                g2.write_g2_metadata_preflight_record(record, output_root=output_root)

    def test_git_context_requires_branch_ancestry_allowlist_clean_and_upstream(self) -> None:
        code = "a" * 40
        tree = "b" * 40
        changed = "\n".join(sorted(g2.G2_ALLOWED_CHANGED_FILES))

        def values(_root: Path, *args: str) -> str:
            mapping = {
                ("branch", "--show-current"): g2.G2_BRANCH,
                ("rev-parse", "HEAD"): code,
                ("rev-parse", "HEAD^{tree}"): tree,
                (
                    "rev-list",
                    "--count",
                    f"{g2.G2_BASE_COMMIT}..{code}",
                ): "1",
                (
                    "rev-list",
                    "--parents",
                    "-n",
                    "1",
                    code,
                ): f"{code} {g2.G2_BASE_COMMIT}",
                (
                    "diff",
                    "--name-only",
                    f"{g2.G2_BASE_COMMIT}..{code}",
                ): changed,
                ("status", "--porcelain=v1", "--untracked-files=no"): "",
                (
                    "ls-files",
                    "--",
                    "src",
                    "tests",
                    "tools",
                ): "src/mes_quant/exploration/test3_metadata_preflight.py",
                (
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                    "--",
                    "src",
                    "tests",
                    "tools",
                ): "",
                (
                    "ls-files",
                    "--others",
                    "--ignored",
                    "--exclude-standard",
                    "--",
                    "src",
                    "tests",
                    "tools",
                ): "",
                ("rev-parse", "@{upstream}"): code,
                (
                    "rev-parse",
                    "--symbolic-full-name",
                    "@{upstream}",
                ): f"refs/remotes/origin/{g2.G2_BRANCH}",
            }
            return mapping[args]

        with (
            patch.object(g2, "_git_output", side_effect=values),
            patch.object(g2.subprocess, "run", return_value=SimpleNamespace(returncode=0)),
        ):
            context = g2._git_execution_context(Path("synthetic"))
        self.assertEqual(context.code_identity, code)
        self.assertEqual(context.tree_identity, tree)

        with (
            patch.object(g2, "_git_output", side_effect=lambda _root, *args: (
                "wrong" if args == ("branch", "--show-current") else values(_root, *args)
            )),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "must execute on branch"),
        ):
            g2._git_execution_context(Path("synthetic"))

        cases = (
            (
                "two commits",
                {
                    (
                        "rev-list",
                        "--count",
                        f"{g2.G2_BASE_COMMIT}..{code}",
                    ): "2"
                },
                "single direct child",
            ),
            (
                "merge parent",
                {
                    (
                        "rev-list",
                        "--parents",
                        "-n",
                        "1",
                        code,
                    ): f"{code} {g2.G2_BASE_COMMIT} {'c' * 40}"
                },
                "exactly the authorized base",
            ),
            (
                "wrong diff",
                {
                    (
                        "diff",
                        "--name-only",
                        f"{g2.G2_BASE_COMMIT}..{code}",
                    ): "unexpected.py"
                },
                "firewall mismatch",
            ),
            (
                "dirty",
                {("status", "--porcelain=v1", "--untracked-files=no"): " M tracked.py"},
                "clean tracked",
            ),
            (
                "upstream mismatch",
                {("rev-parse", "@{upstream}"): "c" * 40},
                "identities must match",
            ),
            (
                "wrong upstream remote",
                {
                    (
                        "rev-parse",
                        "--symbolic-full-name",
                        "@{upstream}",
                    ): f"refs/remotes/fork/{g2.G2_BRANCH}"
                },
                "upstream must be exactly",
            ),
        )
        for label, overrides, expected in cases:
            with self.subTest(case=label):
                def overridden(
                    _root: Path,
                    *args: str,
                    case_overrides: dict[tuple[str, ...], str] = overrides,
                ) -> str:
                    return case_overrides.get(args, values(_root, *args))

                with (
                    patch.object(g2, "_git_output", side_effect=overridden),
                    patch.object(
                        g2.subprocess,
                        "run",
                        return_value=SimpleNamespace(returncode=0),
                    ),
                    self.assertRaisesRegex(g2.Test3G2BoundaryError, expected),
                ):
                    g2._git_execution_context(Path("synthetic"))

        with (
            patch.object(g2, "_git_output", side_effect=values),
            patch.object(
                g2.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=1),
            ),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "ancestry"),
        ):
            g2._git_execution_context(Path("synthetic"))

        def missing_upstream(_root: Path, *args: str) -> str:
            if args == ("rev-parse", "@{upstream}"):
                raise subprocess.CalledProcessError(128, ["git", *args])
            return values(_root, *args)

        with (
            patch.object(g2, "_git_output", side_effect=missing_upstream),
            patch.object(
                g2.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0),
            ),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "pushed upstream"),
        ):
            g2._git_execution_context(Path("synthetic"))

    def test_untracked_importable_code_is_rejected(self) -> None:
        with (
            patch.object(
                g2,
                "_git_output",
                side_effect=("", "src/mes_quant/evil.py", ""),
            ),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "importable code"),
        ):
            g2._assert_no_untracked_import_surface(Path("synthetic"))

    def test_tracked_source_cache_is_allowed_but_sourceless_bytecode_is_rejected(self) -> None:
        tracked = "src/mes_quant/safe.py"
        safe_cache = "src/mes_quant/__pycache__/safe.cpython-312.pyc"

        def safe_values(_root: Path, *args: str) -> str:
            if args == ("ls-files", "--", "src", "tests", "tools"):
                return tracked
            if "--ignored" in args:
                return safe_cache
            return ""

        with patch.object(g2, "_git_output", side_effect=safe_values):
            g2._assert_no_untracked_import_surface(Path("synthetic"))

        def rogue_values(_root: Path, *args: str) -> str:
            if args == ("ls-files", "--", "src", "tests", "tools"):
                return tracked
            if "--ignored" in args:
                return "src/mes_quant/__pycache__/rogue.cpython-312.pyc"
            return ""

        with (
            patch.object(g2, "_git_output", side_effect=rogue_values),
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "importable code"),
        ):
            g2._assert_no_untracked_import_surface(Path("synthetic"))

    def test_post_reservation_failure_summary_is_scrubbed_and_create_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authorization_root = root / "artifacts/exploration/test3/g2/authorization"
            authorization_root.mkdir(parents=True)
            reservation = authorization_root / (
                f"{g2.G2_AUTHORIZATION_DOCUMENT_SHA256}.consumed.json"
            )
            reservation.write_text("{}\n", encoding="utf-8")
            error = RuntimeError("secret /literal/artifact/path")
            failure = g2.write_failure_summary_if_consumed(
                project_root=root,
                error=error,
            )
            self.assertIsNotNone(failure)
            payload = json.loads(failure.read_text(encoding="utf-8"))
            self.assertEqual(payload["error_class"], "RuntimeError")
            self.assertFalse(payload["raw_error_message_committed"])
            self.assertNotIn("literal", failure.read_text(encoding="utf-8"))
            self.assertEqual(
                failure,
                g2.write_failure_summary_if_consumed(
                    project_root=root,
                    error=RuntimeError("different"),
                ),
            )

    def test_thin_runner_preserves_unexpected_post_reservation_failure(self) -> None:
        with (
            patch.object(g2_tool, "main", side_effect=RuntimeError("unexpected")),
            patch.object(
                g2_tool,
                "write_failure_summary_if_consumed",
                return_value=Path("failure.json"),
            ) as preserve,
        ):
            self.assertEqual(g2_tool.run(), 1)
        preserve.assert_called_once()

    def test_wrong_token_stops_main_before_git_or_paths(self) -> None:
        arguments = [
            "--gate",
            g2.G2_GATE_LITERAL,
            "--authorization-token",
            "WRONG",
            "--raw-dbn",
            "missing",
            "--cell8",
            "missing",
            "--cell10",
            "missing",
            "--cell12",
            "missing",
            "--cell14-features",
            "missing",
            "--cell14-run-id",
            "missing",
        ]
        with (
            patch.object(g2, "_git_execution_context") as git_context,
            self.assertRaisesRegex(g2.Test3G2BoundaryError, "token mismatch"),
        ):
            g2.main(arguments, project_root="synthetic")
        git_context.assert_not_called()

    def test_terminal_witness_is_derived_from_record(self) -> None:
        record = {
            "safety_counters": dict(g2._SAFETY_COUNTERS),
            "validation_status": "UNOPENED",
            "final_test_status": "SEALED",
            "live_execution_status": "DISABLED",
            "g2p_status": "NOT_AUTHORIZED",
            "g3p_status": "NOT_AUTHORIZED",
            "g3f_status": "NOT_AUTHORIZED",
        }
        witness = "\n".join(g2._terminal_witness_lines(record))
        self.assertIn("NUMERIC_ROW_VALUES_READ=0", witness)
        self.assertIn("PARQUET_COLUMN_STATISTICS_ACCESSED=0", witness)
        self.assertIn("FINAL_TEST_STATUS=SEALED", witness)
        invalid = {**record, "safety_counters": {**g2._SAFETY_COUNTERS, "real_models_fitted": 1}}
        with self.assertRaisesRegex(g2.Test3G2BoundaryError, "exact zero"):
            g2._terminal_witness_lines(invalid)

    def test_main_prints_only_validated_record_witness(self) -> None:
        record = {
            "record_sha256": "d" * 64,
            "safety_counters": dict(g2._SAFETY_COUNTERS),
            "validation_status": "UNOPENED",
            "final_test_status": "SEALED",
            "live_execution_status": "DISABLED",
            "g2p_status": "NOT_AUTHORIZED",
            "g3p_status": "NOT_AUTHORIZED",
            "g3f_status": "NOT_AUTHORIZED",
        }
        authorization = SimpleNamespace(
            reservation_path=Path("reservation.json"),
            reservation_file_sha256="e" * 64,
        )
        args = [
            "--gate",
            g2.G2_GATE_LITERAL,
            "--authorization-token",
            g2.G2_AUTHORIZATION_TOKEN,
            "--raw-dbn",
            "raw",
            "--cell8",
            "cell8",
            "--cell10",
            "cell10",
            "--cell12",
            "cell12",
            "--cell14-features",
            "cell14",
            "--cell14-run-id",
            "run",
        ]
        stream = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch.object(g2, "_git_execution_context", return_value=self._git_context()),
                patch.object(g2, "_verify_document_bindings", return_value={}),
                patch.object(g2, "_assert_forbidden_modules_absent"),
                patch.object(g2, "_consume_authorization", return_value=authorization),
                patch.object(g2, "build_g2_metadata_preflight_record", return_value=record),
                patch.object(
                    g2,
                    "write_g2_metadata_preflight_record",
                    return_value=(root / "record.json", "f" * 64),
                ),
                redirect_stdout(stream),
            ):
                self.assertEqual(g2.main(args, project_root=root), 0)
        self.assertIn("TEST3_G2_METADATA_PREFLIGHT_PASS", stream.getvalue())
        self.assertIn("REAL_MODELS_FITTED=0", stream.getvalue())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mes_quant.exploration import test2_l1_harness as _harness
from mes_quant.exploration import test2_metadata_preflight as g2
from mes_quant.exploration.test2_l1_harness import (
    ArtifactMetadataEvidence,
    CanonicalArtifactPaths,
    MetadataIdentityPreflight,
)
from mes_quant.exploration.test2_l1_harness import (
    Test2HarnessContractError as HarnessContractError,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_RELEASE_MANIFEST_SHA256,
    FEATURE_ARTIFACT_SHA256,
    FROZEN_COLAB_MANIFEST_SHA256,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
)


class G2MetadataPreflightTests(unittest.TestCase):
    maxDiff = None

    def _fixture(self, root: Path) -> tuple[CanonicalArtifactPaths, Path, Path]:
        locations = {
            "raw_dbn": root / "raw" / _harness.CANONICAL_RAW_DBN_FILENAME,
            "cell8_assignments": root / "cell8" / _harness.CANONICAL_CELL8_FILENAME,
            "cell10_labels": root / "cell10" / _harness.CANONICAL_CELL10_FILENAME,
            "cell12_paths": root / "cell12" / _harness.CANONICAL_CELL12_FILENAME,
            "cell14_features": root / "cell14" / _harness.CANONICAL_FEATURE_FILENAME,
        }
        for path in locations.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic-metadata-fixture\n")
        cell14_manifest = root / "cell14_release.json"
        cell14_manifest.write_text(
            json.dumps(
                {
                    "canonical_run_id": "cell14-canonical",
                    "replay_run_id": "cell14-replay",
                    "runs": {
                        "canonical": {
                            "run_id": "cell14-canonical",
                            "artifacts": {
                                "features": {
                                    "file": (
                                        "artifacts/runs/canonical/"
                                        + _harness.CANONICAL_FEATURE_FILENAME
                                    ),
                                    "sha256": FEATURE_ARTIFACT_SHA256,
                                }
                            },
                        },
                        "replay": {
                            "run_id": "cell14-replay",
                            "artifacts": {
                                "features": {
                                    "file": (
                                        "artifacts/runs/replay/"
                                        + _harness.CANONICAL_FEATURE_FILENAME
                                    ),
                                    "sha256": FEATURE_ARTIFACT_SHA256,
                                }
                            },
                        },
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        frozen_manifest = root / "frozen_manifest.json"
        frozen_manifest.write_text("{}\n", encoding="utf-8")
        return CanonicalArtifactPaths(**locations), cell14_manifest, frozen_manifest

    @staticmethod
    def _preflight(paths: CanonicalArtifactPaths) -> MetadataIdentityPreflight:
        hashes = {
            "raw_dbn": RAW_DBN_SHA256,
            "cell8_assignments": CELL8_SPLIT_ASSIGNMENT_SHA256,
            "cell10_labels": CELL10_LABEL_SHA256,
            "cell12_paths": CELL12_PATH_SHA256,
            "cell14_features": FEATURE_ARTIFACT_SHA256,
        }
        locations = {
            "raw_dbn": paths.raw_dbn,
            "cell8_assignments": paths.cell8_assignments,
            "cell10_labels": paths.cell10_labels,
            "cell12_paths": paths.cell12_paths,
            "cell14_features": paths.cell14_features,
        }
        manifest_ids = {
            "raw_dbn": "raw_dbn",
            "cell8_assignments": "cell8_assignments",
            "cell10_labels": "cell10_labels",
            "cell12_paths": "cell12_paths",
            "cell14_features": "features",
        }
        artifacts = tuple(
            ArtifactMetadataEvidence(
                artifact_id=artifact_id,
                path=str(locations[artifact_id]),
                byte_sha256=hashes[artifact_id],
                parquet_row_count=None if artifact_id == "raw_dbn" else 7,
                parquet_schema=() if artifact_id == "raw_dbn" else ("synthetic",),
                manifest_artifact_id=manifest_ids[artifact_id],
            )
            for artifact_id in hashes
        )
        return MetadataIdentityPreflight(
            release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
            artifacts=artifacts,
            control_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
            ordered_feature_content_sha256_declared=ORDERED_FEATURE_CONTENT_SHA256,
        )

    def _build(self, root: Path, *, timestamp: str = "2026-08-23T00:00:00Z"):
        paths, cell14_manifest, frozen_manifest = self._fixture(root)
        with patch.object(
            _harness,
            "canonical_metadata_preflight",
            return_value=self._preflight(paths),
        ):
            record = g2.build_g2_metadata_preflight_record(
                paths,
                cell14_release_manifest_path=cell14_manifest,
                frozen_colab_manifest_path=frozen_manifest,
                cell14_run_id="cell14-canonical",
                code_identity="a" * 40,
                branch=g2.G2_BRANCH,
                audit_written_utc=timestamp,
            )
        return paths, record

    def test_record_is_metadata_only_and_exactly_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _paths, record = self._build(Path(temporary))
        self.assertEqual(record["status"], "PASS")
        self.assertEqual(record["access_level"], "L0_METADATA_ONLY_NO_ROW_VALUES")
        self.assertEqual(record["base_commit"], g2.G2_BASE_COMMIT)
        self.assertEqual(record["branch"], g2.G2_BRANCH)
        self.assertEqual(record["validation_status"], "UNOPENED")
        self.assertEqual(record["final_test_status"], "SEALED")
        self.assertEqual(record["g3_status"], "NOT_AUTHORIZED")
        self.assertEqual(record["counters"], g2._ZERO_COUNTERS)
        self.assertGreaterEqual(
            len(record["forbidden_module_witness"]["installed_guard_symbols"]),
            20,
        )
        self.assertNotIn("request_set_sha256", json.dumps(record, sort_keys=True))
        artifacts = record["preflight"]["artifacts"]
        self.assertEqual(
            [artifact["artifact_id"] for artifact in artifacts],
            list(g2._EXPECTED_HASHES),
        )
        self.assertTrue(
            all(
                artifact["path"].startswith("${MES_G2_ARTIFACTS}/")
                for artifact in artifacts
            )
        )
        self.assertTrue(
            all(
                artifact["footer_scope"]
                == "SCHEMA_NAMES_AND_NUM_ROWS_ONLY_NO_STATISTICS"
                for artifact in artifacts
            )
        )

    def test_record_identity_is_stable_across_roots_and_audit_times(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            _paths_one, one = self._build(
                Path(first), timestamp="2026-08-23T00:00:00Z"
            )
            _paths_two, two = self._build(
                Path(second), timestamp="2026-08-24T00:00:00Z"
            )
        self.assertEqual(one["run_id"], two["run_id"])
        self.assertEqual(one["record_sha256"], two["record_sha256"])

    def test_wrong_filename_fails_before_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, cell14_manifest, frozen_manifest = self._fixture(root)
            wrong = root / "raw" / "wrong.dbn.zst"
            wrong.write_bytes(paths.raw_dbn.read_bytes())
            paths = CanonicalArtifactPaths(
                raw_dbn=wrong,
                cell8_assignments=paths.cell8_assignments,
                cell10_labels=paths.cell10_labels,
                cell12_paths=paths.cell12_paths,
                cell14_features=paths.cell14_features,
            )
            with (
                patch.object(_harness, "canonical_metadata_preflight") as preflight,
                self.assertRaisesRegex(g2.G2BoundaryError, "requires filename"),
            ):
                g2.build_g2_metadata_preflight_record(
                    paths,
                    cell14_release_manifest_path=cell14_manifest,
                    frozen_colab_manifest_path=frozen_manifest,
                    cell14_run_id="cell14-canonical",
                    code_identity="a" * 40,
                    branch=g2.G2_BRANCH,
                )
            preflight.assert_not_called()

    def test_wrong_branch_fails_before_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths, cell14_manifest, frozen_manifest = self._fixture(Path(temporary))
            with (
                patch.object(_harness, "canonical_metadata_preflight") as preflight,
                self.assertRaisesRegex(g2.G2BoundaryError, "must execute on branch"),
            ):
                g2.build_g2_metadata_preflight_record(
                    paths,
                    cell14_release_manifest_path=cell14_manifest,
                    frozen_colab_manifest_path=frozen_manifest,
                    cell14_run_id="cell14-canonical",
                    code_identity="a" * 40,
                    branch="wrong-branch",
                )
            preflight.assert_not_called()

    def test_numeric_reader_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, cell14_manifest, frozen_manifest = self._fixture(root)

            def forbidden(*_args: object, **_kwargs: object):
                return _harness.pd.read_parquet(paths.cell8_assignments)

            with patch.object(
                _harness,
                "canonical_metadata_preflight",
                side_effect=forbidden,
            ), self.assertRaisesRegex(g2.G2BoundaryError, "pandas.read_parquet"):
                g2.build_g2_metadata_preflight_record(
                    paths,
                    cell14_release_manifest_path=cell14_manifest,
                    frozen_colab_manifest_path=frozen_manifest,
                    cell14_run_id="cell14-canonical",
                    code_identity="a" * 40,
                    branch=g2.G2_BRANCH,
                )

    def test_parquet_statistics_access_is_blocked(self) -> None:
        class OriginalMetadata:
            num_rows = 7

            @staticmethod
            def row_group(_index: int):
                raise AssertionError("original statistics accessor must not run")

        class OriginalSchema:
            names = ("synthetic",)

        class OriginalParquet:
            schema_arrow = OriginalSchema()
            metadata = OriginalMetadata()

        with (
            patch.object(_harness.pq, "ParquetFile", return_value=OriginalParquet()),
            g2._metadata_only_read_guard(),
        ):
            guarded = _harness.pq.ParquetFile("synthetic.parquet")
            self.assertEqual(guarded.schema_arrow.names, ("synthetic",))
            self.assertEqual(guarded.metadata.num_rows, 7)
            with self.assertRaisesRegex(g2.G2BoundaryError, "metadata.row_group"):
                guarded.metadata.row_group(0)

    def test_other_parquet_metadata_entry_points_are_blocked(self) -> None:
        with g2._metadata_only_read_guard():
            for reader in (
                _harness.pq.read_metadata,
                _harness.pq.read_schema,
                _harness.pq.ParquetDataset,
                g2.pads.dataset,
            ):
                with self.subTest(reader=reader), self.assertRaises(g2.G2BoundaryError):
                    reader("synthetic.parquet")

    def test_missing_required_guard_symbol_fails_closed(self) -> None:
        original = _harness.pq.read_metadata
        original_parquet_file = _harness.pq.ParquetFile
        original_read_table = _harness.pq.read_table
        delattr(_harness.pq, "read_metadata")
        try:
            with (
                self.assertRaisesRegex(g2.G2BoundaryError, "required guard symbol"),
                g2._metadata_only_read_guard(),
            ):
                self.fail("guard must not enter with a missing required symbol")
        finally:
            _harness.pq.read_metadata = original
        self.assertIs(_harness.pq.ParquetFile, original_parquet_file)
        self.assertIs(_harness.pq.read_table, original_read_table)

    def test_write_is_create_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _paths, record = self._build(root / "fixture")
            output_root = root / "output"
            output = g2.write_g2_metadata_preflight_record(
                record,
                output_root=output_root,
            )
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                g2.write_g2_metadata_preflight_record(
                    record,
                    output_root=output_root,
                )
            self.assertEqual(output.read_bytes(), original)

    def test_partial_json_write_leaves_no_record_or_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _paths, record = self._build(root / "fixture")
            output_root = root / "output"

            def fail_after_partial_write(_record: object, stream, **_kwargs: object):
                stream.write("{\n")
                stream.flush()
                raise OSError("synthetic interrupted write")

            with (
                patch.object(g2.json, "dump", side_effect=fail_after_partial_write),
                self.assertRaisesRegex(OSError, "interrupted write"),
            ):
                g2.write_g2_metadata_preflight_record(
                    record,
                    output_root=output_root,
                )
            self.assertFalse((output_root / record["run_id"]).exists())
            self.assertEqual(list(output_root.rglob("*.json")), [])

    def test_preflight_contract_error_propagates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, cell14_manifest, frozen_manifest = self._fixture(root)
            with patch.object(
                _harness,
                "canonical_metadata_preflight",
                side_effect=HarnessContractError("byte mismatch"),
            ), self.assertRaisesRegex(HarnessContractError, "byte mismatch"):
                g2.build_g2_metadata_preflight_record(
                    paths,
                    cell14_release_manifest_path=cell14_manifest,
                    frozen_colab_manifest_path=frozen_manifest,
                    cell14_run_id="cell14-canonical",
                    code_identity="a" * 40,
                    branch=g2.G2_BRANCH,
                )

    def test_git_execution_context_passes_only_exact_pushed_firewall(self) -> None:
        code_identity = "b" * 40
        changed = "\n".join(sorted(g2.G2_ALLOWED_CHANGED_FILES))

        def git_output(_root: Path, *args: str) -> str:
            values = {
                ("branch", "--show-current"): g2.G2_BRANCH,
                ("rev-parse", "HEAD"): code_identity,
                (
                    "diff",
                    "--name-only",
                    f"{g2.G2_BASE_COMMIT}..{code_identity}",
                ): changed,
                ("status", "--porcelain=v1", "--untracked-files=no"): "",
                ("rev-parse", "@{upstream}"): code_identity,
            }
            return values[args]

        with (
            patch.object(g2, "_git_output", side_effect=git_output),
            patch.object(
                g2.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0),
            ),
        ):
            self.assertEqual(
                g2._git_execution_context(Path("synthetic-root")),
                (code_identity, g2.G2_BRANCH),
            )

    def test_git_execution_context_refuses_each_firewall_failure(self) -> None:
        code_identity = "b" * 40
        changed = "\n".join(sorted(g2.G2_ALLOWED_CHANGED_FILES))
        cases = (
            ("wrong branch", {"branch": "wrong"}, 0, "must execute on branch"),
            ("wrong base", {}, 1, "does not descend"),
            ("wrong diff", {"changed": "unexpected.py"}, 0, "firewall mismatch"),
            ("dirty", {"status": " M tracked.py"}, 0, "clean tracked"),
            ("un-pushed", {"upstream": "c" * 40}, 0, "identities must match"),
        )
        for label, overrides, ancestor_returncode, expected in cases:
            with self.subTest(case=label):
                def git_output(
                    _root: Path,
                    *args: str,
                    case_overrides: dict[str, str] = overrides,
                ) -> str:
                    values = {
                        ("branch", "--show-current"): case_overrides.get(
                            "branch", g2.G2_BRANCH
                        ),
                        ("rev-parse", "HEAD"): code_identity,
                        (
                            "diff",
                            "--name-only",
                            f"{g2.G2_BASE_COMMIT}..{code_identity}",
                        ): case_overrides.get("changed", changed),
                        ("status", "--porcelain=v1", "--untracked-files=no"): (
                            case_overrides.get("status", "")
                        ),
                        ("rev-parse", "@{upstream}"): case_overrides.get(
                            "upstream", code_identity
                        ),
                    }
                    return values[args]

                with (
                    patch.object(g2, "_git_output", side_effect=git_output),
                    patch.object(
                        g2.subprocess,
                        "run",
                        return_value=SimpleNamespace(returncode=ancestor_returncode),
                    ),
                    self.assertRaisesRegex(g2.G2BoundaryError, expected),
                ):
                    g2._git_execution_context(Path("synthetic-root"))

        def missing_upstream(_root: Path, *args: str) -> str:
            if args == ("rev-parse", "@{upstream}"):
                raise subprocess.CalledProcessError(128, ["git", *args])
            values = {
                ("branch", "--show-current"): g2.G2_BRANCH,
                ("rev-parse", "HEAD"): code_identity,
                (
                    "diff",
                    "--name-only",
                    f"{g2.G2_BASE_COMMIT}..{code_identity}",
                ): changed,
                ("status", "--porcelain=v1", "--untracked-files=no"): "",
            }
            return values[args]

        with (
            patch.object(g2, "_git_output", side_effect=missing_upstream),
            patch.object(
                g2.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0),
            ),
            self.assertRaisesRegex(g2.G2BoundaryError, "pushed upstream"),
        ):
            g2._git_execution_context(Path("synthetic-root"))

    def test_terminal_witness_is_validated_and_derived_from_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = {
                "record_sha256": "d" * 64,
                "counters": dict(g2._ZERO_COUNTERS),
                "preflight": {
                    "decoded_content_status": "NOT_RECOMPUTED_METADATA_ONLY",
                    "ordered_feature_content_status": "NOT_RECOMPUTED_METADATA_ONLY",
                },
                "final_test_status": "SEALED",
                "g3_status": "NOT_AUTHORIZED",
            }
            arguments = [
                "--gate",
                g2.G2_GATE_LITERAL,
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
            with (
                patch.object(g2, "_git_execution_context", return_value=("a" * 40, g2.G2_BRANCH)),
                patch.object(g2, "build_g2_metadata_preflight_record", return_value=record),
                patch.object(
                    g2,
                    "write_g2_metadata_preflight_record",
                    return_value=root / "record.json",
                ),
                redirect_stdout(stream),
            ):
                self.assertEqual(g2.main(arguments, project_root=root), 0)
        witness = stream.getvalue()
        self.assertIn("NUMERIC_VALUES_READ=0", witness)
        self.assertIn("PARQUET_ROW_GROUPS_READ=0", witness)
        self.assertIn("PARQUET_COLUMN_STATISTICS_READ=0", witness)
        self.assertIn("TARGETS_CONSTRUCTED=0", witness)
        self.assertIn("REAL_MODELS_FITTED=0", witness)
        self.assertIn("VALIDATION_ROWS_READ=0", witness)
        self.assertIn(
            "DECODED_CONTENT_STATUS=NOT_RECOMPUTED_METADATA_ONLY",
            witness,
        )
        self.assertIn("FINAL_TEST=SEALED", witness)
        self.assertIn("G3_STATUS=NOT_AUTHORIZED", witness)

        invalid = dict(record)
        invalid["counters"] = {**g2._ZERO_COUNTERS, "numeric_values_read": 1}
        with self.assertRaisesRegex(g2.G2BoundaryError, "exact zero counters"):
            g2._terminal_witness_lines(invalid)


if __name__ == "__main__":
    unittest.main()

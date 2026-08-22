from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from mes_quant.core.hashing import sha256_file
from mes_quant.exploration.test2_l1_harness import (
    ArtifactMetadataEvidence,
    ArtifactPreflightSpec,
    CanonicalArtifactPaths,
    Cell12PathExpectation,
    DataFramePathBarProvider,
    DecodedFrameIdentityEvidence,
    MetadataIdentityPreflight,
    PathMetricReconciliation,
    PathTargetBuildResult,
    assemble_fold_evaluation_data,
    build_real_l1_run_context,
    build_train_path_targets,
    canonical_metadata_preflight,
    decoded_frame_content_sha256,
    preflight_artifact_metadata,
    prepare_train_inputs,
    read_train_only_parquet,
    verify_decoded_frame_identity,
)
from mes_quant.exploration.test2_l1_harness import (
    Test2HarnessContractError as HarnessContractError,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_RELEASE_MANIFEST_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    FROZEN_COLAB_MANIFEST_SHA256,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
    VOLATILITY_DECILE_POLICY_ID,
)
from mes_quant.exploration.test2_request_set import (
    ParentDecision,
    RequestKey,
    build_streaming_request_set,
)
from mes_quant.exploration.test2_run_context import CoverageEvidence
from mes_quant.exploration.test2_target import (
    Disposition,
    PathTargetRow,
    PolicyAction,
    TargetCoverage,
)
from mes_quant.features.contract import FEATURE_COLUMNS, METADATA_COLUMNS


def _feature_and_label_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    decision_time = pd.Timestamp("2022-06-01T14:30:00Z")
    feature_row: dict[str, object] = {
        "decision_id": "A",
        "decision_time": decision_time,
        "nyse_session_date": decision_time.date(),
        "instrument_id": 123,
        "outer_partition": "TRAIN",
        "role_wf_2022": "VALIDATION",
        "role_wf_2023": "TRAIN",
        "role_wf_2024": "UNUSED",
        "feature_row_usable": True,
        "feature_status": "USABLE",
        "feature_lookback_start_utc": decision_time - pd.Timedelta(days=2),
        "feature_max_source_time_utc": decision_time,
    }
    for index, name in enumerate(FEATURE_COLUMNS):
        feature_row[name] = float(index)
    label_row = {
        "decision_id": "A",
        "decision_time": decision_time,
        "instrument_id": 123,
        "outer_partition": "TRAIN",
        "role_wf_2022": "VALIDATION",
        "role_wf_2023": "TRAIN",
        "entry_reference_close": 5_000.0,
        "exit_reference_close_60m": 5_001.0,
    }
    return pd.DataFrame([feature_row]), pd.DataFrame([label_row])


def _sealed_and_path_frame(
    *,
    mismatch_offset: int | None = None,
) -> tuple[object, pd.DataFrame]:
    decision_time = datetime(2022, 6, 1, 14, 30, tzinfo=UTC)
    sealed = build_streaming_request_set(
        (ParentDecision("A", decision_time, "TRAIN"),),
        split_assignment_sha256=CELL8_SPLIT_ASSIGNMENT_SHA256,
    )
    rows = []
    for offset in range(60):
        close = 5_001.0 if offset == 59 else 5_000.0
        high = 5_004.0 if offset == 5 else max(5_000.0, close)
        rows.append(
            {
                "ts_event": decision_time + timedelta(minutes=offset),
                "open": 5_000.0,
                "high": high,
                "low": 5_000.0,
                "close": close,
                "instrument_id": 999 if offset == mismatch_offset else 123,
            }
        )
    frame = pd.DataFrame(rows).set_index("ts_event")
    return sealed, frame


class MetadataPreflightTests(unittest.TestCase):
    def test_byte_manifest_and_footer_checks_read_zero_numeric_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.bin"
            raw.write_bytes(b"synthetic raw")
            table = root / "table.parquet"
            pd.DataFrame(
                {"outer_partition": ["TRAIN"], "decision_id": ["A"]}
            ).to_parquet(table, index=False)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "artifacts": [
                            {"id": "raw", "sha256": sha256_file(raw)},
                            {"id": "table", "sha256": sha256_file(table)},
                        ]
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            result = preflight_artifact_metadata(
                (
                    ArtifactPreflightSpec(
                        "raw", raw, sha256_file(raw), manifest_artifact_id="raw"
                    ),
                    ArtifactPreflightSpec(
                        "table",
                        table,
                        sha256_file(table),
                        ("outer_partition", "decision_id"),
                        "table",
                    ),
                ),
                release_manifest_path=manifest,
                expected_release_manifest_sha256=sha256_file(manifest),
            )
            self.assertEqual(result.numeric_values_read, 0)
            self.assertEqual(result.ordered_feature_content_status, "NOT_RECOMPUTED_METADATA_ONLY")
            self.assertEqual(result.artifacts[1].parquet_row_count, 1)

    def test_hash_mismatch_fails_before_footer_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "not_parquet.bin"
            artifact.write_bytes(b"bad")
            manifest = root / "manifest.json"
            manifest.write_text('{"artifacts": []}', encoding="utf-8")
            with self.assertRaisesRegex(HarnessContractError, "SHA-256 mismatch"):
                preflight_artifact_metadata(
                    (
                        ArtifactPreflightSpec(
                            "artifact", artifact, "0" * 64, ("decision_id",)
                        ),
                    ),
                    release_manifest_path=manifest,
                    expected_release_manifest_sha256=sha256_file(manifest),
                )

    def test_cell14_canonical_and_replay_audits_may_have_distinct_byte_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "features.parquet"
            pd.DataFrame({"decision_id": ["A"]}).to_parquet(feature, index=False)
            manifest = root / "cell14.json"
            manifest.write_text(
                json.dumps(
                    {
                        "runs": {
                            "canonical": {
                                "artifacts": {
                                    "features": {"sha256": sha256_file(feature)},
                                    "audit": {"sha256": "a" * 64},
                                }
                            },
                            "replay": {
                                "artifacts": {
                                    "features": {"sha256": sha256_file(feature)},
                                    "audit": {"sha256": "b" * 64},
                                }
                            },
                        }
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            result = preflight_artifact_metadata(
                (
                    ArtifactPreflightSpec(
                        "feature",
                        feature,
                        sha256_file(feature),
                        ("decision_id",),
                        "features",
                    ),
                ),
                release_manifest_path=manifest,
                expected_release_manifest_sha256=sha256_file(manifest),
            )
            self.assertEqual(result.artifacts[0].byte_sha256, sha256_file(feature))

    def test_canonical_preflight_binds_both_tracked_manifests(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        paths = CanonicalArtifactPaths(
            *(Path("/synthetic") / name for name in ("raw", "cell8", "cell10", "cell12", "features"))
        )
        upstream_hashes = (
            ("raw_dbn", RAW_DBN_SHA256),
            ("cell8_assignments", CELL8_SPLIT_ASSIGNMENT_SHA256),
            ("cell10_labels", CELL10_LABEL_SHA256),
            ("cell12_paths", CELL12_PATH_SHA256),
        )
        upstream = MetadataIdentityPreflight(
            release_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
            artifacts=tuple(
                ArtifactMetadataEvidence(name, str(paths.raw_dbn), sha256, None, (), None)
                for name, sha256 in upstream_hashes
            ),
        )
        feature = MetadataIdentityPreflight(
            release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
            artifacts=(
                ArtifactMetadataEvidence(
                    "cell14_features",
                    str(paths.cell14_features),
                    FEATURE_ARTIFACT_SHA256,
                    None,
                    (),
                    "features",
                ),
            ),
        )
        with patch(
            "mes_quant.exploration.test2_l1_harness.preflight_artifact_metadata",
            side_effect=(upstream, feature),
        ):
            result = canonical_metadata_preflight(
                paths,
                cell14_release_manifest_path=(
                    project_root / "manifests/releases/cell14_local_release_v1.json"
                ),
                frozen_colab_manifest_path=(
                    project_root / "manifests/releases/frozen_colab_manifest_v1.json"
                ),
            )
        self.assertEqual(result.control_manifest_sha256, FROZEN_COLAB_MANIFEST_SHA256)
        self.assertEqual(
            result.ordered_feature_content_sha256_declared,
            ORDERED_FEATURE_CONTENT_SHA256,
        )


class DecodedIdentityTests(unittest.TestCase):
    def test_decoded_content_hash_is_value_sensitive(self) -> None:
        index = pd.DatetimeIndex(["2022-01-01T00:00:00Z"], name="ts_event")
        frame = pd.DataFrame(
            {
                "open": [1.0],
                "high": [2.0],
                "low": [0.5],
                "close": [1.5],
                "instrument_id": [123],
            },
            index=index,
        )
        expected = decoded_frame_content_sha256(frame)
        evidence = verify_decoded_frame_identity(frame, expected_sha256=expected)
        self.assertEqual(evidence.content_sha256, expected)
        self.assertEqual(evidence.row_count, 1)
        changed = frame.copy()
        changed.loc[index[0], "close"] = 1.75
        with self.assertRaisesRegex(HarnessContractError, "content SHA-256 mismatch"):
            verify_decoded_frame_identity(changed, expected_sha256=expected)


class TrainInputTests(unittest.TestCase):
    def test_parquet_reader_physically_filters_outer_train(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.parquet"
            pd.DataFrame(
                {
                    "outer_partition": ["TRAIN", "VALIDATION", "FINAL_TEST"],
                    "decision_id": ["A", "B", "C"],
                }
            ).to_parquet(path, index=False)
            frame = read_train_only_parquet(
                path,
                columns=("outer_partition", "decision_id"),
            )
            self.assertEqual(frame["decision_id"].tolist(), ["A"])
            self.assertEqual(
                frame.attrs["test2_physical_outer_partition_filter"],
                "TRAIN",
            )

    def test_prepare_asserts_pit_and_exact_role_binding(self) -> None:
        features, labels = _feature_and_label_frames()
        result = prepare_train_inputs(features, labels)
        self.assertTrue(result.feature_max_source_time_asserted)
        self.assertFalse(result.physical_train_predicate_asserted)
        self.assertEqual(result.path_decisions[0].expected_native_instrument, 123)
        self.assertEqual(
            tuple(column for column in features.columns if column in FEATURE_COLUMNS),
            FEATURE_COLUMNS,
        )
        self.assertEqual(tuple(column for column in features.columns if column in METADATA_COLUMNS), METADATA_COLUMNS)

    def test_prepare_rejects_future_feature_source_time(self) -> None:
        features, labels = _feature_and_label_frames()
        features.loc[0, "feature_max_source_time_utc"] += pd.Timedelta(minutes=1)
        with self.assertRaisesRegex(HarnessContractError, "exceeds decision_time"):
            prepare_train_inputs(features, labels)

    def test_prepare_rejects_feature_label_role_mismatch(self) -> None:
        features, labels = _feature_and_label_frames()
        labels.loc[0, "role_wf_2022"] = "TRAIN"
        with self.assertRaisesRegex(HarnessContractError, "role_wf_2022 mismatch"):
            prepare_train_inputs(features, labels)

    def test_fold_assembly_fits_deciles_before_target_retention(self) -> None:
        features, labels = _feature_and_label_frames()
        rows = []
        label_rows = []
        roles = (
            ("A", "2021-06-01T14:30:00Z", "TRAIN", "TRAIN", 0.1, 0),
            ("B", "2022-06-01T14:30:00Z", "VALIDATION", "TRAIN", 0.2, 1),
            ("C", "2023-06-01T14:30:00Z", "UNUSED", "VALIDATION", 0.3, 0),
        )
        for identity, timestamp, role_2022, role_2023, volatility, label in roles:
            feature_row = features.iloc[0].copy()
            feature_row["decision_id"] = identity
            feature_row["decision_time"] = pd.Timestamp(timestamp)
            feature_row["feature_max_source_time_utc"] = pd.Timestamp(timestamp)
            feature_row["nyse_session_date"] = pd.Timestamp(timestamp).date()
            feature_row["role_wf_2022"] = role_2022
            feature_row["role_wf_2023"] = role_2023
            feature_row["realized_vol_60m"] = volatility
            rows.append(feature_row)
            label_row = labels.iloc[0].copy()
            label_row["decision_id"] = identity
            label_row["decision_time"] = pd.Timestamp(timestamp)
            label_row["role_wf_2022"] = role_2022
            label_row["role_wf_2023"] = role_2023
            label_rows.append(label_row)
        prepared = prepare_train_inputs(pd.DataFrame(rows), pd.DataFrame(label_rows))
        target_rows = tuple(
            PathTargetRow(
                decision_identity=identity,
                disposition=(
                    Disposition.FAVORABLE_FIRST if label else Disposition.NEITHER_TOUCH
                ),
                retained=True,
                policy_action=PolicyAction.SCORED,
                path_long=label,
                first_touch_offset_minutes=5 if label else None,
                gross_move_points_60m=1.0,
                no_score_reason=None,
                instrument_id="MES",
                entry_reference_ticks=20_000,
            )
            for identity, _, _, _, _, label in roles
        )
        targets = PathTargetBuildResult(
            target_rows=target_rows,
            coverage=TargetCoverage(3, 1, 0, 2, 0, 0, 3, 0),
            path_metrics=(),
            request_set_sha256="a" * 64,
            real_train_target_path_rows_read=180,
            missing_path_bar_keys=0,
            native_instrument_mismatch_keys=0,
            validation_path_bar_lookup_count=0,
            final_test_path_bar_lookup_count=0,
        )
        assembly = assemble_fold_evaluation_data(prepared, targets)
        self.assertEqual([fold.fold_id for fold in assembly.folds], ["WF_2022", "WF_2023"])
        self.assertEqual(assembly.folds[0].holdout_row_ids, ("B",))
        self.assertEqual(assembly.folds[1].holdout_row_ids, ("C",))
        self.assertEqual(assembly.coverage.total_rows, 2)
        self.assertEqual(assembly.volatility_grids[0].training_row_count, 1)
        self.assertEqual(assembly.volatility_grids[1].training_row_count, 2)


class PathAdapterTests(unittest.TestCase):
    def test_verified_native_instrument_is_normalized_and_reconciled(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        result = build_train_path_targets(
            sealed,
            prepared.path_decisions,
            provider,
            batch_size=17,
            cell12_expectations={
                "A": Cell12PathExpectation("A", 5_004.0, 5_000.0, 4.0, 0.0)
            },
        )
        self.assertEqual(result.target_rows[0].disposition, Disposition.FAVORABLE_FIRST)
        self.assertEqual(result.target_rows[0].instrument_id, "MES")
        self.assertEqual(result.path_metrics[0].cell12_status, "EXACT_TICK_RECONCILIATION_PASS")
        self.assertEqual(result.real_train_target_path_rows_read, 60)
        self.assertEqual(result.validation_path_bar_lookup_count, 0)
        self.assertEqual(result.final_test_path_bar_lookup_count, 0)

        with self.assertRaisesRegex(HarnessContractError, "outside the seal"):
            provider.fetch_path_bar_batch(
                (
                    RequestKey(
                        "A",
                        0,
                        datetime(2025, 1, 2, 14, 45, tzinfo=UTC),
                    ),
                ),
                request_set_sha256=sealed.request_set_sha256,
            )

    def test_native_instrument_mismatch_fails_closed_to_no_score(self) -> None:
        sealed, frame = _sealed_and_path_frame(mismatch_offset=9)
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        result = build_train_path_targets(
            sealed,
            prepared.path_decisions,
            provider,
            batch_size=60,
        )
        self.assertEqual(result.target_rows[0].disposition, Disposition.NO_SCORE)
        self.assertEqual(result.native_instrument_mismatch_keys, 1)
        self.assertEqual(result.missing_path_bar_keys, 0)

    def test_cell12_difference_fails_closed(self) -> None:
        sealed, frame = _sealed_and_path_frame()
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        provider = DataFramePathBarProvider(
            frame,
            sealed=sealed,
            expected_native_instruments={"A": 123},
        )
        with self.assertRaisesRegex(HarnessContractError, "differ from Cell 12"):
            build_train_path_targets(
                sealed,
                prepared.path_decisions,
                provider,
                batch_size=60,
                cell12_expectations={
                    "A": Cell12PathExpectation("A", 5_003.75, 5_000.0, 3.75, 0.0)
                },
            )

    def test_real_context_requires_canonical_metadata_and_cell12_reconciliation(self) -> None:
        features, labels = _feature_and_label_frames()
        prepared = prepare_train_inputs(features, labels)
        hashes = {
            "raw_dbn": RAW_DBN_SHA256,
            "cell8_assignments": CELL8_SPLIT_ASSIGNMENT_SHA256,
            "cell10_labels": CELL10_LABEL_SHA256,
            "cell12_paths": CELL12_PATH_SHA256,
            "cell14_features": FEATURE_ARTIFACT_SHA256,
        }
        metadata = MetadataIdentityPreflight(
            release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
            artifacts=tuple(
                ArtifactMetadataEvidence(
                    artifact_id=artifact_id,
                    path=f"/synthetic/{artifact_id}",
                    byte_sha256=sha256,
                    parquet_row_count=None,
                    parquet_schema=(),
                    manifest_artifact_id=None,
                )
                for artifact_id, sha256 in hashes.items()
            ),
            control_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
            ordered_feature_content_sha256_declared=ORDERED_FEATURE_CONTENT_SHA256,
        )
        row = PathTargetRow(
            decision_identity="A",
            disposition=Disposition.FAVORABLE_FIRST,
            retained=True,
            policy_action=PolicyAction.SCORED,
            path_long=1,
            first_touch_offset_minutes=5,
            gross_move_points_60m=1.0,
            no_score_reason=None,
            instrument_id="MES",
            entry_reference_ticks=20_000,
        )
        targets = PathTargetBuildResult(
            target_rows=(row,),
            coverage=TargetCoverage(1, 1, 0, 0, 0, 0, 1, 0),
            path_metrics=(
                PathMetricReconciliation(
                    "A", 5_004.0, 5_000.0, 4.0, 0.0, "EXACT_TICK_RECONCILIATION_PASS"
                ),
            ),
            request_set_sha256="c" * 64,
            real_train_target_path_rows_read=60,
            missing_path_bar_keys=0,
            native_instrument_mismatch_keys=0,
            validation_path_bar_lookup_count=0,
            final_test_path_bar_lookup_count=0,
        )
        coverage = CoverageEvidence(
            1,
            0,
            0,
            0,
            "ALL_OOF_ROWS_PRETARGET_FOLD_TRAIN_DECILES",
            {
                "policy_id": VOLATILITY_DECILE_POLICY_ID,
                "folds": {
                    "WF_2022": {"total_rows": 1},
                    "WF_2023": {"total_rows": 0},
                },
            },
        )
        context = build_real_l1_run_context(
            metadata,
            replace(prepared, physical_train_predicate_asserted=True),
            targets,
            coverage,
            decoded_identity=DecodedFrameIdentityEvidence(
                DECODED_MES_1M_SHA256,
                2_551_123,
                "2019-05-05T22:00:00+00:00",
                "2026-07-31T20:59:00+00:00",
            ),
            authorization_identity="OWNER_TEST2_L1",
            authorization_record_sha256="d" * 64,
        )
        self.assertEqual(context.access_level, "L1_TRAIN_ONLY")
        self.assertIn(
            "NOT_RECOMPUTED",
            context.source_identity.content_sha256_evidence,
        )
        with self.assertRaisesRegex(HarnessContractError, "counter scope"):
            build_real_l1_run_context(
                metadata,
                replace(prepared, physical_train_predicate_asserted=True),
                targets,
                replace(coverage, scope="ALL_FEATURE_VALID_OOF_ROWS"),
                decoded_identity=DecodedFrameIdentityEvidence(
                    DECODED_MES_1M_SHA256,
                    2_551_123,
                    "2019-05-05T22:00:00+00:00",
                    "2026-07-31T20:59:00+00:00",
                ),
                authorization_identity="OWNER_TEST2_L1",
                authorization_record_sha256="d" * 64,
            )
        unreconciled = replace(
            targets,
            path_metrics=(
                replace(
                    targets.path_metrics[0],
                    cell12_status="NOT_PERFORMED_CELL12_NOT_SUPPLIED",
                ),
            ),
        )
        with self.assertRaisesRegex(HarnessContractError, "Cell 12 reconciliation"):
            build_real_l1_run_context(
                metadata,
                replace(prepared, physical_train_predicate_asserted=True),
                unreconciled,
                coverage,
                decoded_identity=DecodedFrameIdentityEvidence(
                    DECODED_MES_1M_SHA256,
                    2_551_123,
                    "2019-05-05T22:00:00+00:00",
                    "2026-07-31T20:59:00+00:00",
                ),
                authorization_identity="OWNER_TEST2_L1",
                authorization_record_sha256="d" * 64,
            )


if __name__ == "__main__":
    unittest.main()

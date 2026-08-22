from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from mes_quant.core.hashing import sha256_file
from mes_quant.exploration.test2_diagnostics import (
    CoverageObservation,
    VolatilityDecileGrid,
    build_coverage_evidence,
    fit_volatility_decile_grid,
)
from mes_quant.exploration.test2_evaluation import (
    CONSUMER_ORDER,
    ConsumerRetainedIndex,
    FoldEvaluationData,
)
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    CELL10_LABEL_SHA256,
    CELL12_PATH_SHA256,
    CELL14_RELEASE_MANIFEST_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    FEATURE_AVAILABILITY_POLICY_ID,
    FROZEN_COLAB_MANIFEST_SHA256,
    ORDERED_FEATURE_CONTENT_SHA256,
    OUTER_TRAIN_ROLE,
    OUTER_VALIDATION_BOUNDARY_UTC,
    RAW_DBN_SHA256,
    VOLATILITY_DECILE_POLICY_ID,
)
from mes_quant.exploration.test2_request_set import (
    RequestKey,
    StreamingSealedRequestSet,
    iter_path_bar_batches,
)
from mes_quant.exploration.test2_run_context import (
    VERIFIED_SOURCE_STATUS,
    CoverageEvidence,
    EvaluationRunContext,
    SourceIdentityEvidence,
)
from mes_quant.exploration.test2_stats import FOLD_ORDER
from mes_quant.exploration.test2_target import (
    PathBar,
    PathTargetRequest,
    PathTargetRow,
    TargetCoverage,
    build_path_target_rows,
    price_to_ticks,
)
from mes_quant.features.contract import FEATURE_COLUMNS, METADATA_COLUMNS

CANONICAL_RAW_DBN_FILENAME = "MES_2019_2026_1m.dbn.zst"
CANONICAL_CELL8_FILENAME = "cell8_purged_split_assignments_v1.parquet"
CANONICAL_CELL10_FILENAME = "cell10_point_in_time_economic_labels_v1.parquet"
CANONICAL_CELL12_FILENAME = "cell12_development_path_outcomes_v1.parquet"
CANONICAL_FEATURE_FILENAME = "cell14_development_point_in_time_features_v1.parquet"

DECODED_COLUMNS = ("open", "high", "low", "close", "instrument_id")
CELL8_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
)
CELL10_REQUIRED_COLUMNS = (
    "decision_id",
    "decision_time",
    "instrument_id",
    "outer_partition",
    "role_wf_2022",
    "role_wf_2023",
    "entry_reference_close",
    "exit_reference_close_60m",
)
CELL12_REQUIRED_COLUMNS = (
    "decision_id",
    "outer_partition",
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
)
FEATURE_REQUIRED_COLUMNS = tuple(METADATA_COLUMNS) + tuple(FEATURE_COLUMNS)


class Test2HarnessContractError(RuntimeError):
    """Raised before Test 2 could misstate identity, access, or reconciliation."""


def _lower_sha256(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise Test2HarnessContractError(f"{field} must be a lowercase SHA-256")
    return value


def _path(value: str | Path, *, field: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    if not candidate.is_file():
        raise Test2HarnessContractError(f"{field} is missing: {candidate}")
    return candidate


@dataclass(frozen=True)
class ArtifactPreflightSpec:
    artifact_id: str
    path: Path
    expected_sha256: str
    required_parquet_columns: tuple[str, ...] = ()
    manifest_artifact_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, str) or not self.artifact_id:
            raise Test2HarnessContractError("artifact_id must be non-empty")
        object.__setattr__(self, "path", Path(self.path).expanduser().resolve())
        _lower_sha256(self.expected_sha256, field=f"{self.artifact_id} expected_sha256")
        if len(set(self.required_parquet_columns)) != len(self.required_parquet_columns):
            raise Test2HarnessContractError("required parquet columns must be unique")


@dataclass(frozen=True)
class ArtifactMetadataEvidence:
    artifact_id: str
    path: str
    byte_sha256: str
    parquet_row_count: int | None
    parquet_schema: tuple[str, ...]
    manifest_artifact_id: str | None

    def as_record(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "byte_sha256": self.byte_sha256,
            "parquet_row_count": self.parquet_row_count,
            "parquet_schema": self.parquet_schema,
            "manifest_artifact_id": self.manifest_artifact_id,
        }


@dataclass(frozen=True)
class MetadataIdentityPreflight:
    release_manifest_sha256: str
    artifacts: tuple[ArtifactMetadataEvidence, ...]
    control_manifest_sha256: str | None = None
    ordered_feature_content_sha256_declared: str | None = None
    numeric_values_read: int = 0
    ordered_feature_content_status: str = "NOT_RECOMPUTED_METADATA_ONLY"
    decoded_content_status: str = "NOT_RECOMPUTED_METADATA_ONLY"

    def __post_init__(self) -> None:
        _lower_sha256(self.release_manifest_sha256, field="release_manifest_sha256")
        if self.control_manifest_sha256 is not None:
            _lower_sha256(self.control_manifest_sha256, field="control_manifest_sha256")
        if self.ordered_feature_content_sha256_declared is not None:
            _lower_sha256(
                self.ordered_feature_content_sha256_declared,
                field="ordered_feature_content_sha256_declared",
            )
        if self.numeric_values_read != 0:
            raise Test2HarnessContractError("metadata preflight cannot claim numeric reads")

    def as_record(self) -> dict[str, object]:
        return {
            "release_manifest_sha256": self.release_manifest_sha256,
            "control_manifest_sha256": self.control_manifest_sha256,
            "ordered_feature_content_sha256_declared": (
                self.ordered_feature_content_sha256_declared
            ),
            "artifacts": tuple(artifact.as_record() for artifact in self.artifacts),
            "numeric_values_read": self.numeric_values_read,
            "ordered_feature_content_status": self.ordered_feature_content_status,
            "decoded_content_status": self.decoded_content_status,
        }


def _manifest_artifact_hashes(manifest: Mapping[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}

    def add(artifact_id: object, sha256: object) -> None:
        if not isinstance(artifact_id, str) or not isinstance(sha256, str):
            raise Test2HarnessContractError("release manifest artifact identity is malformed")
        normalized = _lower_sha256(sha256, field=f"manifest {artifact_id} sha256")
        if artifact_id in result and result[artifact_id] != normalized:
            raise Test2HarnessContractError("release manifest has conflicting artifact IDs")
        result[artifact_id] = normalized

    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise Test2HarnessContractError("release manifest artifact is malformed")
            add(artifact.get("id"), artifact.get("sha256"))
    upstream = manifest.get("upstream_inputs")
    if isinstance(upstream, dict):
        for artifact_id, artifact in upstream.items():
            if not isinstance(artifact, dict):
                raise Test2HarnessContractError("release upstream artifact is malformed")
            add(artifact_id, artifact.get("sha256"))
    runs = manifest.get("runs")
    if isinstance(runs, dict):
        canonical_run = runs.get("canonical")
        if not isinstance(canonical_run, dict) or not isinstance(
            canonical_run.get("artifacts"), dict
        ):
            raise Test2HarnessContractError(
                "release canonical-run artifact mapping is malformed"
            )
        for artifact_id, artifact in canonical_run["artifacts"].items():
            if not isinstance(artifact, dict):
                raise Test2HarnessContractError("release canonical artifact is malformed")
            add(artifact_id, artifact.get("sha256"))
    if not result:
        raise Test2HarnessContractError("release manifest exposes no artifact identities")
    return result


def preflight_artifact_metadata(
    specs: Sequence[ArtifactPreflightSpec],
    *,
    release_manifest_path: str | Path,
    expected_release_manifest_sha256: str,
) -> MetadataIdentityPreflight:
    """Verify bytes, manifest bindings, and Parquet footers without reading row values."""

    materialized = tuple(specs)
    if not materialized or len({spec.artifact_id for spec in materialized}) != len(
        materialized
    ):
        raise Test2HarnessContractError("artifact specs must be non-empty and unique")
    manifest_path = _path(release_manifest_path, field="release manifest")
    expected_manifest = _lower_sha256(
        expected_release_manifest_sha256,
        field="expected_release_manifest_sha256",
    )
    actual_manifest = sha256_file(manifest_path)
    if actual_manifest != expected_manifest:
        raise Test2HarnessContractError("release manifest SHA-256 mismatch")

    actual_hashes: dict[str, str] = {}
    for spec in materialized:
        artifact_path = _path(spec.path, field=spec.artifact_id)
        actual = sha256_file(artifact_path)
        if actual != spec.expected_sha256:
            raise Test2HarnessContractError(f"{spec.artifact_id} SHA-256 mismatch")
        actual_hashes[spec.artifact_id] = actual

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise Test2HarnessContractError("release manifest root must be an object")
    manifest_hashes = _manifest_artifact_hashes(manifest)
    for spec in materialized:
        if spec.manifest_artifact_id is None:
            continue
        if manifest_hashes.get(spec.manifest_artifact_id) != actual_hashes[spec.artifact_id]:
            raise Test2HarnessContractError(
                f"{spec.artifact_id} is not bound to release manifest "
                f"artifact {spec.manifest_artifact_id}"
            )

    evidence: list[ArtifactMetadataEvidence] = []
    for spec in materialized:
        row_count: int | None = None
        schema: tuple[str, ...] = ()
        if spec.required_parquet_columns:
            parquet = pq.ParquetFile(spec.path)
            schema = tuple(parquet.schema_arrow.names)
            missing = sorted(set(spec.required_parquet_columns).difference(schema))
            if missing:
                raise Test2HarnessContractError(
                    f"{spec.artifact_id} Parquet footer lacks: {', '.join(missing)}"
                )
            row_count = int(parquet.metadata.num_rows)
        evidence.append(
            ArtifactMetadataEvidence(
                artifact_id=spec.artifact_id,
                path=str(spec.path),
                byte_sha256=actual_hashes[spec.artifact_id],
                parquet_row_count=row_count,
                parquet_schema=schema,
                manifest_artifact_id=spec.manifest_artifact_id,
            )
        )
    return MetadataIdentityPreflight(actual_manifest, tuple(evidence))


@dataclass(frozen=True)
class CanonicalArtifactPaths:
    raw_dbn: Path
    cell8_assignments: Path
    cell10_labels: Path
    cell12_paths: Path
    cell14_features: Path

    def __post_init__(self) -> None:
        for field in (
            "raw_dbn",
            "cell8_assignments",
            "cell10_labels",
            "cell12_paths",
            "cell14_features",
        ):
            object.__setattr__(
                self,
                field,
                Path(getattr(self, field)).expanduser().resolve(),
            )


def canonical_metadata_specs(
    paths: CanonicalArtifactPaths,
) -> tuple[ArtifactPreflightSpec, ...]:
    return (
        ArtifactPreflightSpec(
            "raw_dbn",
            paths.raw_dbn,
            RAW_DBN_SHA256,
            manifest_artifact_id="raw_dbn",
        ),
        ArtifactPreflightSpec(
            "cell8_assignments",
            paths.cell8_assignments,
            CELL8_SPLIT_ASSIGNMENT_SHA256,
            CELL8_REQUIRED_COLUMNS,
            "cell8_assignments",
        ),
        ArtifactPreflightSpec(
            "cell10_labels",
            paths.cell10_labels,
            CELL10_LABEL_SHA256,
            CELL10_REQUIRED_COLUMNS,
            "cell10_labels",
        ),
        ArtifactPreflightSpec(
            "cell12_paths",
            paths.cell12_paths,
            CELL12_PATH_SHA256,
            CELL12_REQUIRED_COLUMNS,
            "cell12_paths",
        ),
        ArtifactPreflightSpec(
            "cell14_features",
            paths.cell14_features,
            FEATURE_ARTIFACT_SHA256,
            FEATURE_REQUIRED_COLUMNS,
            "features",
        ),
    )


def canonical_metadata_preflight(
    paths: CanonicalArtifactPaths,
    *,
    cell14_release_manifest_path: str | Path,
    frozen_colab_manifest_path: str | Path,
) -> MetadataIdentityPreflight:
    specs = canonical_metadata_specs(paths)
    upstream = preflight_artifact_metadata(
        specs[:4],
        release_manifest_path=frozen_colab_manifest_path,
        expected_release_manifest_sha256=FROZEN_COLAB_MANIFEST_SHA256,
    )
    feature = preflight_artifact_metadata(
        specs[4:],
        release_manifest_path=cell14_release_manifest_path,
        expected_release_manifest_sha256=CELL14_RELEASE_MANIFEST_SHA256,
    )
    cell14_manifest = json.loads(
        _path(cell14_release_manifest_path, field="Cell 14 release manifest").read_text(
            encoding="utf-8"
        )
    )
    bound_control = (
        cell14_manifest.get("controls", {})
        .get("frozen_colab_manifest", {})
        .get("sha256")
    )
    if bound_control != upstream.release_manifest_sha256:
        raise Test2HarnessContractError(
            "Cell 14 release is not bound to the frozen Colab manifest"
        )
    runs = cell14_manifest.get("runs", {})
    canonical_content = (
        runs.get("canonical", {}).get("artifacts", {}).get("features", {}).get(
            "content_sha256"
        )
    )
    replay_content = (
        runs.get("replay", {}).get("artifacts", {}).get("features", {}).get(
            "content_sha256"
        )
    )
    if (
        canonical_content != ORDERED_FEATURE_CONTENT_SHA256
        or replay_content != ORDERED_FEATURE_CONTENT_SHA256
    ):
        raise Test2HarnessContractError(
            "Cell 14 release does not declare the pinned ordered feature-content hash"
        )
    return MetadataIdentityPreflight(
        release_manifest_sha256=feature.release_manifest_sha256,
        artifacts=upstream.artifacts + feature.artifacts,
        control_manifest_sha256=upstream.release_manifest_sha256,
        ordered_feature_content_sha256_declared=canonical_content,
    )


def decoded_frame_content_sha256(frame: pd.DataFrame) -> str:
    """Reproduce the frozen Cell 2 value hash; this is a G3 numeric operation."""

    if tuple(column for column in frame.columns if column in DECODED_COLUMNS) != DECODED_COLUMNS:
        raise Test2HarnessContractError("decoded frame column order does not match Cell 2")
    if frame.index.name != "ts_event" or frame.index.has_duplicates:
        raise Test2HarnessContractError("decoded frame requires a unique ts_event index")
    hashed = pd.util.hash_pandas_object(
        frame.loc[:, DECODED_COLUMNS],
        index=True,
        categorize=False,
    ).to_numpy(dtype=np.uint64, copy=False)
    return hashlib.sha256(hashed.tobytes()).hexdigest()


@dataclass(frozen=True)
class DecodedFrameIdentityEvidence:
    content_sha256: str
    row_count: int
    timestamp_min_utc: str
    timestamp_max_utc: str
    hash_scope: str = "FULL_CANONICAL_DECODED_FRAME_IDENTITY_ONLY_NOT_PATH_LOOKUP"

    def __post_init__(self) -> None:
        _lower_sha256(self.content_sha256, field="decoded evidence content SHA-256")
        if self.row_count <= 0:
            raise Test2HarnessContractError("decoded evidence row count must be positive")


def verify_decoded_frame_identity(
    frame: pd.DataFrame,
    *,
    expected_sha256: str = DECODED_MES_1M_SHA256,
) -> DecodedFrameIdentityEvidence:
    expected = _lower_sha256(expected_sha256, field="expected decoded content SHA-256")
    actual = decoded_frame_content_sha256(frame)
    if actual != expected:
        raise Test2HarnessContractError("decoded Cell 2 content SHA-256 mismatch")
    timestamps = pd.DatetimeIndex(frame.index).tz_convert("UTC")
    return DecodedFrameIdentityEvidence(
        content_sha256=actual,
        row_count=len(frame),
        timestamp_min_utc=timestamps.min().isoformat(),
        timestamp_max_utc=timestamps.max().isoformat(),
    )


def read_train_only_parquet(
    path: str | Path,
    *,
    columns: Sequence[str],
) -> pd.DataFrame:
    """Push the outer-TRAIN predicate into Parquet before exposing row values."""

    requested = tuple(columns)
    if "outer_partition" not in requested:
        raise Test2HarnessContractError("TRAIN reader must request outer_partition")
    frame = pd.read_parquet(
        _path(path, field="TRAIN parquet"),
        columns=list(requested),
        filters=[("outer_partition", "==", OUTER_TRAIN_ROLE)],
    )
    if frame.empty or not frame["outer_partition"].eq(OUTER_TRAIN_ROLE).all():
        raise Test2HarnessContractError("physical Parquet read was not outer-TRAIN only")
    frame.attrs["test2_physical_outer_partition_filter"] = OUTER_TRAIN_ROLE
    return frame


@dataclass(frozen=True)
class TrainPathDecision:
    decision_identity: str
    decision_time_utc: datetime
    expected_native_instrument: object
    entry_reference_close: float | None
    endpoint_close_60m: float | None


@dataclass(frozen=True)
class PreparedTrainInputs:
    frame: pd.DataFrame
    path_decisions: tuple[TrainPathDecision, ...]
    feature_max_source_time_asserted: bool
    physical_train_predicate_asserted: bool
    availability_policy_id: str = FEATURE_AVAILABILITY_POLICY_ID


def _utc_series(values: pd.Series, *, field: str) -> pd.Series:
    try:
        result = pd.to_datetime(values, utc=True, errors="raise")
    except (TypeError, ValueError) as exc:
        raise Test2HarnessContractError(f"{field} must be valid UTC timestamps") from exc
    if result.isna().any():
        raise Test2HarnessContractError(f"{field} contains missing timestamps")
    return result


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], *, field: str) -> None:
    if frame.columns.has_duplicates:
        raise Test2HarnessContractError(f"{field} contains duplicate columns")
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise Test2HarnessContractError(f"{field} lacks: {', '.join(missing)}")


def prepare_train_inputs(
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> PreparedTrainInputs:
    """Join caller-supplied physical TRAIN reads and assert PIT/role identity."""

    _require_columns(features, FEATURE_REQUIRED_COLUMNS, field="feature frame")
    _require_columns(labels, CELL10_REQUIRED_COLUMNS, field="label frame")
    feature_order = tuple(column for column in features.columns if column in FEATURE_COLUMNS)
    if feature_order != tuple(FEATURE_COLUMNS):
        raise Test2HarnessContractError("feature frame does not preserve the pinned 29-column order")
    for field, frame in (("feature frame", features), ("label frame", labels)):
        if frame.empty:
            raise Test2HarnessContractError(f"{field} is empty")
        if not frame["outer_partition"].eq(OUTER_TRAIN_ROLE).all():
            raise Test2HarnessContractError(f"{field} contains non-TRAIN rows")
        if frame["decision_id"].isna().any() or frame["decision_id"].duplicated().any():
            raise Test2HarnessContractError(f"{field} decision IDs are missing or duplicated")

    feature_times = _utc_series(features["decision_time"], field="feature decision_time")
    feature_source_times = _utc_series(
        features["feature_max_source_time_utc"],
        field="feature_max_source_time_utc",
    )
    label_times = _utc_series(labels["decision_time"], field="label decision_time")
    if feature_times.ge(OUTER_VALIDATION_BOUNDARY_UTC).any() or label_times.ge(
        OUTER_VALIDATION_BOUNDARY_UTC
    ).any():
        raise Test2HarnessContractError("TRAIN inputs cross the outer-Validation boundary")
    if feature_source_times.gt(feature_times).any():
        raise Test2HarnessContractError(
            "feature_max_source_time_utc exceeds decision_time"
        )

    feature_copy = features.copy()
    label_copy = labels.copy()
    feature_copy["decision_time"] = feature_times
    feature_copy["feature_max_source_time_utc"] = feature_source_times
    label_copy["decision_time"] = label_times
    joined = feature_copy.merge(
        label_copy.loc[
            :,
            [
                "decision_id",
                "decision_time",
                "instrument_id",
                "outer_partition",
                "role_wf_2022",
                "role_wf_2023",
                "entry_reference_close",
                "exit_reference_close_60m",
            ],
        ],
        on="decision_id",
        how="inner",
        validate="one_to_one",
        suffixes=("_feature", "_label"),
    )
    if len(joined) != len(feature_copy) or len(joined) != len(label_copy):
        raise Test2HarnessContractError("feature/label TRAIN decision sets differ")
    exact_fields = ("decision_time", "outer_partition", "role_wf_2022", "role_wf_2023")
    for field in exact_fields:
        left = joined[f"{field}_feature"]
        right = joined[f"{field}_label"]
        if not left.equals(right):
            raise Test2HarnessContractError(f"feature/label {field} mismatch")
    if not all(
        _same_native_instrument(feature_instrument, label_instrument)
        for feature_instrument, label_instrument in zip(
            joined["instrument_id_feature"],
            joined["instrument_id_label"],
            strict=True,
        )
    ):
        raise Test2HarnessContractError("feature/label instrument_id mismatch")

    joined = joined.sort_values(
        ["decision_time_feature", "decision_id"], kind="stable"
    ).reset_index(drop=True)
    decisions = tuple(
        TrainPathDecision(
            decision_identity=str(row.decision_id),
            decision_time_utc=row.decision_time_feature.to_pydatetime(),
            expected_native_instrument=row.instrument_id_feature,
            entry_reference_close=(
                None if pd.isna(row.entry_reference_close) else float(row.entry_reference_close)
            ),
            endpoint_close_60m=(
                None
                if pd.isna(row.exit_reference_close_60m)
                else float(row.exit_reference_close_60m)
            ),
        )
        for row in joined.itertuples(index=False)
    )
    physical_train_predicate_asserted = all(
        frame.attrs.get("test2_physical_outer_partition_filter") == OUTER_TRAIN_ROLE
        for frame in (features, labels)
    )
    return PreparedTrainInputs(
        joined,
        decisions,
        True,
        physical_train_predicate_asserted,
    )


def _same_native_instrument(observed: object, expected: object) -> bool:
    if pd.isna(observed) or pd.isna(expected):
        return False
    if isinstance(observed, (int, float, np.integer, np.floating)) and isinstance(
        expected, (int, float, np.integer, np.floating)
    ):
        left = float(observed)
        right = float(expected)
        return math.isfinite(left) and math.isfinite(right) and left == right
    return str(observed) == str(expected)


class DataFramePathBarProvider:
    """G1 adapter: lookup only sealed keys and normalize verified native IDs to MES."""

    def __init__(
        self,
        frame: pd.DataFrame,
        *,
        sealed: StreamingSealedRequestSet,
        expected_native_instruments: Mapping[str, object],
        timestamp_column: str | None = None,
    ) -> None:
        _require_columns(frame, DECODED_COLUMNS, field="decoded path frame")
        expected_ids = {decision.decision_identity for decision in sealed.decisions}
        if set(expected_native_instruments) != expected_ids:
            raise Test2HarnessContractError(
                "native instrument map must exactly cover sealed decisions"
            )
        if timestamp_column is None:
            timestamps = pd.DatetimeIndex(frame.index)
        else:
            if timestamp_column not in frame.columns:
                raise Test2HarnessContractError("decoded path timestamp column is missing")
            timestamps = pd.DatetimeIndex(frame[timestamp_column])
        if timestamps.tz is None:
            raise Test2HarnessContractError("decoded path timestamps must be timezone-aware")
        normalized = pd.DatetimeIndex(timestamps).tz_convert("UTC")
        if normalized.has_duplicates:
            raise Test2HarnessContractError("decoded path timestamps must be unique")
        self._frame = frame.copy(deep=False)
        self._frame.index = normalized
        self._request_set_sha256 = sealed.request_set_sha256
        self._expected = MappingProxyType(dict(expected_native_instruments))
        self._decision_times = MappingProxyType(
            {
                decision.decision_identity: decision.decision_time_utc.astimezone(UTC)
                for decision in sealed.decisions
            }
        )
        self.rows_examined = 0
        self.missing_keys = 0
        self.instrument_mismatch_keys = 0

    def fetch_path_bar_batch(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> Mapping[RequestKey, PathBar]:
        if request_set_sha256 != self._request_set_sha256:
            raise Test2HarnessContractError("provider received the wrong sealed request hash")
        result: dict[RequestKey, PathBar] = {}
        for key in request_keys:
            decision_time = self._decision_times.get(key.decision_identity)
            if (
                decision_time is None
                or key.minute_offset not in range(60)
                or key.requested_timestamp_utc.astimezone(UTC)
                != decision_time + timedelta(minutes=key.minute_offset)
            ):
                raise Test2HarnessContractError("provider received a key outside the seal")
            timestamp = pd.Timestamp(key.requested_timestamp_utc).tz_convert("UTC")
            try:
                row = self._frame.loc[timestamp]
            except KeyError:
                self.missing_keys += 1
                continue
            self.rows_examined += 1
            if not _same_native_instrument(
                row["instrument_id"], self._expected[key.decision_identity]
            ):
                self.instrument_mismatch_keys += 1
                continue
            result[key] = PathBar(
                minute_offset=key.minute_offset,
                instrument_id="MES",
                open_price=float(row["open"]),
                high_price=float(row["high"]),
                low_price=float(row["low"]),
                close_price=float(row["close"]),
            )
        return result


@dataclass(frozen=True)
class Cell12PathExpectation:
    decision_identity: str
    path_high_60m: float
    path_low_60m: float
    long_mfe_points_60m: float
    long_mae_points_60m: float


@dataclass(frozen=True)
class PathMetricReconciliation:
    decision_identity: str
    path_high_60m: float
    path_low_60m: float
    long_mfe_points_60m: float
    long_mae_points_60m: float
    cell12_status: str


@dataclass(frozen=True)
class PathTargetBuildResult:
    target_rows: tuple[PathTargetRow, ...]
    coverage: TargetCoverage
    path_metrics: tuple[PathMetricReconciliation, ...]
    request_set_sha256: str
    real_train_target_path_rows_read: int
    missing_path_bar_keys: int
    native_instrument_mismatch_keys: int
    validation_path_bar_lookup_count: int
    final_test_path_bar_lookup_count: int


@dataclass(frozen=True)
class FoldAssembly:
    folds: tuple[FoldEvaluationData, ...]
    volatility_grids: tuple[VolatilityDecileGrid, ...]
    coverage: CoverageEvidence


def _metric_ticks(value: float, *, field: str) -> int:
    return price_to_ticks(float(value), field=field)


def _path_metrics(
    decision: TrainPathDecision,
    bars: tuple[PathBar, ...],
    expectation: Cell12PathExpectation | None,
) -> PathMetricReconciliation | None:
    if len(bars) != 60 or decision.entry_reference_close is None:
        return None
    path_high_ticks = max(_metric_ticks(bar.high_price, field="path high") for bar in bars)
    path_low_ticks = min(_metric_ticks(bar.low_price, field="path low") for bar in bars)
    entry_ticks = _metric_ticks(decision.entry_reference_close, field="entry reference")
    mfe_ticks = max(path_high_ticks - entry_ticks, 0)
    mae_ticks = max(entry_ticks - path_low_ticks, 0)
    observed_ticks = (path_high_ticks, path_low_ticks, mfe_ticks, mae_ticks)
    status = "NOT_PERFORMED_CELL12_NOT_SUPPLIED"
    if expectation is not None:
        if expectation.decision_identity != decision.decision_identity:
            raise Test2HarnessContractError("Cell 12 expectation identity mismatch")
        expected_ticks = (
            _metric_ticks(expectation.path_high_60m, field="Cell 12 path high"),
            _metric_ticks(expectation.path_low_60m, field="Cell 12 path low"),
            _metric_ticks(expectation.long_mfe_points_60m, field="Cell 12 long MFE"),
            _metric_ticks(expectation.long_mae_points_60m, field="Cell 12 long MAE"),
        )
        if observed_ticks != expected_ticks:
            raise Test2HarnessContractError("recomputed TRAIN path metrics differ from Cell 12")
        status = "EXACT_TICK_RECONCILIATION_PASS"
    return PathMetricReconciliation(
        decision_identity=decision.decision_identity,
        path_high_60m=path_high_ticks / 4.0,
        path_low_60m=path_low_ticks / 4.0,
        long_mfe_points_60m=mfe_ticks / 4.0,
        long_mae_points_60m=mae_ticks / 4.0,
        cell12_status=status,
    )


def build_train_path_targets(
    sealed: StreamingSealedRequestSet,
    decisions: Sequence[TrainPathDecision],
    provider: DataFramePathBarProvider,
    *,
    batch_size: int,
    cell12_expectations: Mapping[str, Cell12PathExpectation] | None = None,
) -> PathTargetBuildResult:
    materialized = tuple(decisions)
    by_identity = {decision.decision_identity: decision for decision in materialized}
    if len(by_identity) != len(materialized):
        raise Test2HarnessContractError("TRAIN path decision identities must be unique")
    sealed_identity_times = {
        decision.decision_identity: decision.decision_time_utc.astimezone(UTC)
        for decision in sealed.decisions
    }
    if set(by_identity) != set(sealed_identity_times):
        raise Test2HarnessContractError("TRAIN path decisions must exactly match sealed parents")
    for identity, decision in by_identity.items():
        if decision.decision_time_utc.astimezone(UTC) != sealed_identity_times[identity]:
            raise Test2HarnessContractError("TRAIN path decision time differs from sealed parent")
    if cell12_expectations is not None and set(cell12_expectations) != set(by_identity):
        raise Test2HarnessContractError(
            "supplied Cell 12 expectations must exactly cover sealed TRAIN decisions"
        )

    bars_by_identity: dict[str, list[PathBar]] = defaultdict(list)
    for batch in iter_path_bar_batches(sealed, provider, batch_size=batch_size):
        for key, bar in batch.items():
            bars_by_identity[key.decision_identity].append(bar)

    requests: list[PathTargetRequest] = []
    reconciliations: list[PathMetricReconciliation] = []
    for decision in materialized:
        bars = tuple(
            sorted(
                bars_by_identity.get(decision.decision_identity, ()),
                key=lambda bar: bar.minute_offset,
            )
        )
        requests.append(
            PathTargetRequest(
                decision_identity=decision.decision_identity,
                entry_reference_close=decision.entry_reference_close,
                endpoint_close_60m=decision.endpoint_close_60m,
                bars=bars,
            )
        )
        metrics = _path_metrics(
            decision,
            bars,
            None
            if cell12_expectations is None
            else cell12_expectations[decision.decision_identity],
        )
        if metrics is not None:
            reconciliations.append(metrics)

    target_rows, coverage = build_path_target_rows(requests)
    return PathTargetBuildResult(
        target_rows=target_rows,
        coverage=coverage,
        path_metrics=tuple(reconciliations),
        request_set_sha256=sealed.request_set_sha256,
        real_train_target_path_rows_read=provider.rows_examined,
        missing_path_bar_keys=provider.missing_keys,
        native_instrument_mismatch_keys=provider.instrument_mismatch_keys,
        validation_path_bar_lookup_count=sealed.validation_path_bar_lookup_count,
        final_test_path_bar_lookup_count=sealed.final_test_path_bar_lookup_count,
    )


def assemble_fold_evaluation_data(
    prepared: PreparedTrainInputs,
    targets: PathTargetBuildResult,
) -> FoldAssembly:
    """Build the exact retained fold surface while preserving pre-exclusion coverage."""

    frame = prepared.frame.copy(deep=False)
    target_by_id = {row.decision_identity: row for row in targets.target_rows}
    if len(target_by_id) != len(targets.target_rows):
        raise Test2HarnessContractError("target rows contain duplicate identities")
    frame_ids = frame["decision_id"].astype(str)
    if set(frame_ids) != set(target_by_id):
        raise Test2HarnessContractError("prepared TRAIN and target decision sets differ")
    feature_values = frame.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    finite_features = np.isfinite(feature_values).all(axis=1)
    declared_usable = frame["feature_row_usable"].astype(bool).to_numpy()
    if np.any(declared_usable & ~finite_features):
        raise Test2HarnessContractError("feature-usable row contains a non-finite feature")
    feature_valid = declared_usable & finite_features

    folds: list[FoldEvaluationData] = []
    grids: dict[str, VolatilityDecileGrid] = {}
    coverage_observations: list[CoverageObservation] = []
    for fold_id in FOLD_ORDER:
        role_column = f"role_{fold_id.lower()}_feature"
        if role_column not in frame.columns:
            raise Test2HarnessContractError(f"prepared TRAIN frame lacks {role_column}")
        roles = frame[role_column].astype(str).to_numpy()
        train_partition = roles == "TRAIN"
        holdout_partition = roles == "VALIDATION"
        if np.any(~np.isin(roles, ("TRAIN", "VALIDATION", "UNUSED"))):
            raise Test2HarnessContractError(f"{fold_id} contains an unexpected role")
        pretarget_grid_mask = train_partition
        volatility_values = frame.loc[
            pretarget_grid_mask,
            "realized_vol_60m",
        ].to_numpy(dtype=np.float64)
        volatility_values = volatility_values[np.isfinite(volatility_values)]
        grid = fit_volatility_decile_grid(fold_id, volatility_values)
        grids[fold_id] = grid

        for row_index in np.flatnonzero(holdout_partition):
            identity = frame_ids.iloc[row_index]
            volatility = frame.iloc[row_index]["realized_vol_60m"]
            coverage_observations.append(
                CoverageObservation(
                    fold_id=fold_id,
                    decision_identity=identity,
                    realized_vol_60m=(
                        float(volatility)
                        if pd.notna(volatility) and math.isfinite(float(volatility))
                        else None
                    ),
                    target_row=target_by_id[identity],
                    feature_valid=bool(feature_valid[row_index]),
                )
            )

        retained = np.asarray(
            [target_by_id[identity].retained for identity in frame_ids],
            dtype=bool,
        )
        train_mask = train_partition & feature_valid & retained
        holdout_mask = holdout_partition & feature_valid & retained
        train_indices = np.flatnonzero(train_mask)
        holdout_indices = np.flatnonzero(holdout_mask)
        train_ids = tuple(frame_ids.iloc[train_indices])
        holdout_ids = tuple(frame_ids.iloc[holdout_indices])
        retained_index = ConsumerRetainedIndex(train_ids, holdout_ids)
        holdout_targets = tuple(target_by_id[identity] for identity in holdout_ids)
        folds.append(
            FoldEvaluationData(
                fold_id=fold_id,
                train_features=feature_values[train_indices],
                train_labels=tuple(
                    int(target_by_id[identity].path_long) for identity in train_ids
                ),
                train_row_ids=train_ids,
                train_decision_times=tuple(
                    frame.iloc[index]["decision_time_feature"].to_pydatetime()
                    for index in train_indices
                ),
                holdout_features=feature_values[holdout_indices],
                holdout_labels=tuple(
                    int(target_by_id[identity].path_long) for identity in holdout_ids
                ),
                holdout_gross_move_points_60m=tuple(
                    float(target_by_id[identity].gross_move_points_60m)
                    for identity in holdout_ids
                ),
                holdout_row_ids=holdout_ids,
                holdout_decision_times=tuple(
                    frame.iloc[index]["decision_time_feature"].to_pydatetime()
                    for index in holdout_indices
                ),
                holdout_session_ids=tuple(
                    str(frame.iloc[index]["nyse_session_date"])
                    for index in holdout_indices
                ),
                consumer_indices={
                    consumer: retained_index for consumer in CONSUMER_ORDER
                },
                holdout_target_rows=holdout_targets,
            )
        )

    coverage = build_coverage_evidence(coverage_observations, grids)
    return FoldAssembly(
        folds=tuple(folds),
        volatility_grids=tuple(grids[fold_id] for fold_id in FOLD_ORDER),
        coverage=coverage,
    )


def build_real_l1_run_context(
    metadata: MetadataIdentityPreflight,
    prepared: PreparedTrainInputs,
    targets: PathTargetBuildResult,
    coverage: CoverageEvidence,
    *,
    decoded_identity: DecodedFrameIdentityEvidence,
    authorization_identity: str,
    authorization_record_sha256: str,
) -> EvaluationRunContext:
    """Construct a truthful G3 context only after all separately authorized evidence exists."""

    artifacts = {artifact.artifact_id: artifact.byte_sha256 for artifact in metadata.artifacts}
    expected = {
        "raw_dbn": RAW_DBN_SHA256,
        "cell8_assignments": CELL8_SPLIT_ASSIGNMENT_SHA256,
        "cell10_labels": CELL10_LABEL_SHA256,
        "cell12_paths": CELL12_PATH_SHA256,
        "cell14_features": FEATURE_ARTIFACT_SHA256,
    }
    if artifacts != expected:
        raise Test2HarnessContractError("metadata evidence is not the exact canonical set")
    if metadata.release_manifest_sha256 != CELL14_RELEASE_MANIFEST_SHA256:
        raise Test2HarnessContractError("Cell 14 release-manifest identity mismatch")
    if metadata.control_manifest_sha256 != FROZEN_COLAB_MANIFEST_SHA256:
        raise Test2HarnessContractError("frozen Colab control-manifest identity mismatch")
    if decoded_identity.content_sha256 != DECODED_MES_1M_SHA256:
        raise Test2HarnessContractError("decoded content identity is not canonical")
    if decoded_identity.hash_scope != (
        "FULL_CANONICAL_DECODED_FRAME_IDENTITY_ONLY_NOT_PATH_LOOKUP"
    ):
        raise Test2HarnessContractError("decoded identity evidence has the wrong scope")
    if (
        metadata.ordered_feature_content_sha256_declared
        != ORDERED_FEATURE_CONTENT_SHA256
    ):
        raise Test2HarnessContractError(
            "ordered feature-content identity lacks Cell 14 release binding"
        )
    if targets.validation_path_bar_lookup_count or targets.final_test_path_bar_lookup_count:
        raise Test2HarnessContractError("target build crossed a sealed outer boundary")
    if targets.real_train_target_path_rows_read <= 0:
        raise Test2HarnessContractError("target build recorded no real TRAIN path rows")
    if not prepared.feature_max_source_time_asserted:
        raise Test2HarnessContractError("prepared TRAIN inputs lack the PIT assertion")
    if not prepared.physical_train_predicate_asserted:
        raise Test2HarnessContractError(
            "prepared inputs lack physical outer-TRAIN predicate evidence"
        )
    if {decision.decision_identity for decision in prepared.path_decisions} != {
        row.decision_identity for row in targets.target_rows
    }:
        raise Test2HarnessContractError("prepared and targeted TRAIN decision sets differ")
    reconciled_rows = sum(row.instrument_id == "MES" for row in targets.target_rows)
    if len(targets.path_metrics) != reconciled_rows or any(
        row.cell12_status != "EXACT_TICK_RECONCILIATION_PASS"
        for row in targets.path_metrics
    ):
        raise Test2HarnessContractError(
            "complete TRAIN paths lack exact Cell 12 reconciliation"
        )
    if coverage.scope != "ALL_OOF_ROWS_PRETARGET_FOLD_TRAIN_DECILES":
        raise Test2HarnessContractError("coverage evidence has the wrong counter scope")
    coverage_payload = coverage.by_fold_decile
    folds_payload = coverage_payload.get("folds")
    if (
        coverage_payload.get("policy_id") != VOLATILITY_DECILE_POLICY_ID
        or not isinstance(folds_payload, Mapping)
        or set(folds_payload) != set(FOLD_ORDER)
    ):
        raise Test2HarnessContractError("coverage evidence lacks exact fold/decile identity")
    try:
        reconciled_coverage_rows = sum(
            int(folds_payload[fold_id]["total_rows"]) for fold_id in FOLD_ORDER
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise Test2HarnessContractError("coverage fold totals are malformed") from exc
    if reconciled_coverage_rows != coverage.total_rows:
        raise Test2HarnessContractError("coverage fold totals do not reconcile")
    return EvaluationRunContext(
        access_level="L1_TRAIN_ONLY",
        harness_status="L1_TRAIN_ONLY_AUTHORIZED_HARNESS",
        authorization_identity=authorization_identity,
        authorization_record_sha256=authorization_record_sha256,
        source_identity=SourceIdentityEvidence(
            raw_dbn_sha256=RAW_DBN_SHA256,
            decoded_mes_1m_sha256=DECODED_MES_1M_SHA256,
            feature_artifact_sha256=FEATURE_ARTIFACT_SHA256,
            ordered_feature_content_sha256=ORDERED_FEATURE_CONTENT_SHA256,
            evidence_status=VERIFIED_SOURCE_STATUS,
            content_sha256_evidence=(
                "FULL_CANONICAL_CELL2_DECODED_VALUE_HASH_RECOMPUTED_"
                "IDENTITY_ONLY_NOT_PATH_LOOKUP;"
                "CELL14_ORDERED_CONTENT_RELEASE_MANIFEST_DECLARED_NOT_RECOMPUTED"
            ),
            release_manifest_sha256=metadata.release_manifest_sha256,
        ),
        role_assignment_identity=CELL8_SPLIT_ASSIGNMENT_SHA256,
        request_set_sha256=targets.request_set_sha256,
        real_train_target_path_rows_read=targets.real_train_target_path_rows_read,
        validation_rows_read=targets.validation_path_bar_lookup_count,
        final_test_rows_read=targets.final_test_path_bar_lookup_count,
        feature_max_source_time_asserted=prepared.feature_max_source_time_asserted,
        coverage=coverage,
        economic_diagnostics={},
        is_synthetic=False,
        is_test_fixture=False,
        missing_path_bar_keys=targets.missing_path_bar_keys,
        native_instrument_mismatch_keys=targets.native_instrument_mismatch_keys,
    )

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    L0_ACCESS_LEVEL,
    L0_HARNESS_STATUS,
    L1_ACCESS_LEVEL,
    L1_HARNESS_STATUS,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
    TEST_FIXTURE_ACCESS_LEVEL,
    TEST_FIXTURE_HARNESS_STATUS,
)

SYNTHETIC_AUTHORIZATION_ID = "L0_SYNTHETIC_ONLY_NO_L1_TOKEN"
SYNTHETIC_SOURCE_STATUS = "SYNTHETIC_DECLARED_IDENTITIES_NOT_ARTIFACT_VERIFIED"
VERIFIED_SOURCE_STATUS = "ARTIFACT_IDENTITIES_VERIFIED"
TEST_FIXTURE_SOURCE_STATUS = "SYNTHETIC_G1_CONTRACT_FIXTURE"


class RunContextContractError(ValueError):
    """Raised when a record context could misstate access or source provenance."""


def _sha256(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RunContextContractError(f"{field} must be a lowercase SHA-256")
    return value


def _nonempty(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunContextContractError(f"{field} must be non-empty")
    return value.strip()


@dataclass(frozen=True)
class SourceIdentityEvidence:
    raw_dbn_sha256: str
    decoded_mes_1m_sha256: str
    feature_artifact_sha256: str
    ordered_feature_content_sha256: str
    evidence_status: str
    content_sha256_evidence: str
    release_manifest_sha256: str | None = None

    def __post_init__(self) -> None:
        _sha256(self.raw_dbn_sha256, field="raw_dbn_sha256")
        _sha256(self.decoded_mes_1m_sha256, field="decoded_mes_1m_sha256")
        _sha256(self.feature_artifact_sha256, field="feature_artifact_sha256")
        _sha256(
            self.ordered_feature_content_sha256,
            field="ordered_feature_content_sha256",
        )
        _nonempty(self.evidence_status, field="evidence_status")
        _nonempty(self.content_sha256_evidence, field="content_sha256_evidence")
        if self.release_manifest_sha256 is not None:
            _sha256(self.release_manifest_sha256, field="release_manifest_sha256")

    def as_record(self) -> dict[str, object]:
        return {
            "raw_dbn_sha256": self.raw_dbn_sha256,
            "decoded_mes_1m_sha256": self.decoded_mes_1m_sha256,
            "feature_artifact_sha256": self.feature_artifact_sha256,
            "ordered_feature_content_sha256": self.ordered_feature_content_sha256,
            "evidence_status": self.evidence_status,
            "content_sha256_evidence": self.content_sha256_evidence,
            "release_manifest_sha256": self.release_manifest_sha256,
        }


@dataclass(frozen=True)
class CoverageEvidence:
    total_rows: int
    ambiguity_rows: int
    missing_rows: int
    excluded_rows: int
    scope: str
    by_fold_decile: Mapping[str, object]

    def __post_init__(self) -> None:
        values = (
            self.total_rows,
            self.ambiguity_rows,
            self.missing_rows,
            self.excluded_rows,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise RunContextContractError("coverage counts must be non-negative integers")
        if self.ambiguity_rows + self.missing_rows > self.excluded_rows:
            raise RunContextContractError("coverage exclusions undercount ambiguity/missing rows")
        if self.excluded_rows > self.total_rows:
            raise RunContextContractError("coverage exclusions exceed total rows")
        _nonempty(self.scope, field="coverage scope")
        object.__setattr__(
            self,
            "by_fold_decile",
            MappingProxyType(dict(self.by_fold_decile)),
        )

    def as_record(self) -> dict[str, object]:
        return {
            "total_rows": self.total_rows,
            "ambiguity_rows": self.ambiguity_rows,
            "missing_rows": self.missing_rows,
            "excluded_rows": self.excluded_rows,
            "coverage_counter_scope": self.scope,
            "coverage_by_fold_decile": dict(self.by_fold_decile),
        }


@dataclass(frozen=True)
class EvaluationRunContext:
    access_level: str
    harness_status: str
    authorization_identity: str
    authorization_record_sha256: str | None
    source_identity: SourceIdentityEvidence
    role_assignment_identity: str
    request_set_sha256: str | None
    real_train_target_path_rows_read: int
    validation_rows_read: int
    final_test_rows_read: int
    feature_max_source_time_asserted: bool
    coverage: CoverageEvidence
    economic_diagnostics: Mapping[str, object]
    is_synthetic: bool
    is_test_fixture: bool
    missing_path_bar_keys: int = 0
    native_instrument_mismatch_keys: int = 0

    def __post_init__(self) -> None:
        _nonempty(self.access_level, field="access_level")
        _nonempty(self.harness_status, field="harness_status")
        _nonempty(self.authorization_identity, field="authorization_identity")
        _sha256(self.role_assignment_identity, field="role_assignment_identity")
        if self.authorization_record_sha256 is not None:
            _sha256(
                self.authorization_record_sha256,
                field="authorization_record_sha256",
            )
        if self.request_set_sha256 is not None:
            _sha256(self.request_set_sha256, field="request_set_sha256")
        counters = (
            self.real_train_target_path_rows_read,
            self.validation_rows_read,
            self.final_test_rows_read,
            self.missing_path_bar_keys,
            self.native_instrument_mismatch_keys,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in counters
        ):
            raise RunContextContractError("access counters must be non-negative integers")
        object.__setattr__(
            self,
            "economic_diagnostics",
            MappingProxyType(dict(self.economic_diagnostics)),
        )
        self._validate_mode()

    def _validate_mode(self) -> None:
        if self.is_synthetic:
            if self.is_test_fixture:
                raise RunContextContractError("synthetic L0 context cannot be an L1 fixture")
            if self.access_level != L0_ACCESS_LEVEL:
                raise RunContextContractError("synthetic context must record L0 access")
            if self.harness_status != L0_HARNESS_STATUS:
                raise RunContextContractError("synthetic context has the wrong harness status")
            if self.authorization_identity != SYNTHETIC_AUTHORIZATION_ID:
                raise RunContextContractError("synthetic context cannot carry an L1 token")
            if self.authorization_record_sha256 is not None or self.request_set_sha256 is not None:
                raise RunContextContractError("synthetic context cannot claim L1 evidence")
            if any(
                (
                    self.real_train_target_path_rows_read,
                    self.validation_rows_read,
                    self.final_test_rows_read,
                )
            ):
                raise RunContextContractError("synthetic context cannot claim real row access")
            return

        if self.validation_rows_read != 0 or self.final_test_rows_read != 0:
            raise RunContextContractError("L1 context must keep Validation/Final Test at zero")
        if self.real_train_target_path_rows_read <= 0:
            raise RunContextContractError("L1 context must record positive TRAIN path access")
        if self.authorization_record_sha256 is None:
            raise RunContextContractError("L1 context requires an authorization record SHA")
        if self.request_set_sha256 is None:
            raise RunContextContractError("L1 context requires the sealed request-set SHA")
        if not self.feature_max_source_time_asserted:
            raise RunContextContractError("L1 context requires the availability assertion")
        if self.role_assignment_identity != CELL8_SPLIT_ASSIGNMENT_SHA256:
            raise RunContextContractError("L1 role-assignment identity mismatch")
        if self.is_test_fixture:
            if self.access_level != TEST_FIXTURE_ACCESS_LEVEL:
                raise RunContextContractError("fixture context has the wrong access level")
            if self.harness_status != TEST_FIXTURE_HARNESS_STATUS:
                raise RunContextContractError("fixture context has the wrong harness status")
            if self.source_identity.evidence_status != TEST_FIXTURE_SOURCE_STATUS:
                raise RunContextContractError("fixture context has the wrong source status")
        else:
            if self.access_level != L1_ACCESS_LEVEL:
                raise RunContextContractError("real L1 context has the wrong access level")
            if self.harness_status != L1_HARNESS_STATUS:
                raise RunContextContractError("real L1 context has the wrong harness status")
            if self.source_identity.evidence_status != VERIFIED_SOURCE_STATUS:
                raise RunContextContractError("real L1 context requires verified source evidence")
            if self.source_identity.raw_dbn_sha256 != RAW_DBN_SHA256:
                raise RunContextContractError("real L1 raw DBN identity mismatch")
            if self.source_identity.decoded_mes_1m_sha256 != DECODED_MES_1M_SHA256:
                raise RunContextContractError("real L1 decoded frame identity mismatch")
            if self.source_identity.feature_artifact_sha256 != FEATURE_ARTIFACT_SHA256:
                raise RunContextContractError("real L1 feature artifact identity mismatch")
            if (
                self.source_identity.ordered_feature_content_sha256
                != ORDERED_FEATURE_CONTENT_SHA256
            ):
                raise RunContextContractError("real L1 feature content identity mismatch")

    @classmethod
    def synthetic(cls) -> EvaluationRunContext:
        return cls(
            access_level=L0_ACCESS_LEVEL,
            harness_status=L0_HARNESS_STATUS,
            authorization_identity=SYNTHETIC_AUTHORIZATION_ID,
            authorization_record_sha256=None,
            source_identity=SourceIdentityEvidence(
                raw_dbn_sha256=RAW_DBN_SHA256,
                decoded_mes_1m_sha256=DECODED_MES_1M_SHA256,
                feature_artifact_sha256=FEATURE_ARTIFACT_SHA256,
                ordered_feature_content_sha256=ORDERED_FEATURE_CONTENT_SHA256,
                evidence_status=SYNTHETIC_SOURCE_STATUS,
                content_sha256_evidence="FROZEN_CONSTANTS_ONLY_NOT_ARTIFACT_VERIFIED",
            ),
            role_assignment_identity=CELL8_SPLIT_ASSIGNMENT_SHA256,
            request_set_sha256=None,
            real_train_target_path_rows_read=0,
            validation_rows_read=0,
            final_test_rows_read=0,
            feature_max_source_time_asserted=False,
            coverage=CoverageEvidence(
                total_rows=0,
                ambiguity_rows=0,
                missing_rows=0,
                excluded_rows=0,
                scope="SYNTHETIC_RETAINED_INPUT_ONLY",
                by_fold_decile={},
            ),
            economic_diagnostics={},
            is_synthetic=True,
            is_test_fixture=False,
        )

    def as_record(
        self,
        *,
        real_models_fitted: int,
        fit_status: str = "COMPLETED",
    ) -> dict[str, object]:
        if (
            isinstance(real_models_fitted, bool)
            or not isinstance(real_models_fitted, int)
            or real_models_fitted < 0
        ):
            raise RunContextContractError("real_models_fitted must be non-negative")
        if self.is_synthetic and real_models_fitted != 0:
            raise RunContextContractError("synthetic context cannot record real model fits")
        allowed_zero_fit = fit_status == "SKIPPED_INCONCLUSIVE_UNDERPOWERED"
        if (
            not self.is_synthetic
            and not self.is_test_fixture
            and real_models_fitted <= 0
            and not allowed_zero_fit
        ):
            raise RunContextContractError("completed real L1 record must count real fold fits")
        if real_models_fitted > 0 and fit_status != "COMPLETED":
            raise RunContextContractError("non-completed fit status cannot record real fits")
        return {
            "access_level": self.access_level,
            "harness_status": self.harness_status,
            "authorization_identity": self.authorization_identity,
            "authorization_record_sha256": self.authorization_record_sha256,
            "source_identity": self.source_identity.as_record(),
            "role_assignment_identity": self.role_assignment_identity,
            "request_set_sha256": self.request_set_sha256,
            "real_train_target_path_rows_read": self.real_train_target_path_rows_read,
            "validation_rows_read": self.validation_rows_read,
            "final_test_rows_read": self.final_test_rows_read,
            "missing_path_bar_keys": self.missing_path_bar_keys,
            "native_instrument_mismatch_keys": self.native_instrument_mismatch_keys,
            "feature_max_source_time_asserted": self.feature_max_source_time_asserted,
            "real_models_fitted": real_models_fitted,
            "fit_status": fit_status,
            **self.coverage.as_record(),
            "economic_diagnostics": dict(self.economic_diagnostics),
        }

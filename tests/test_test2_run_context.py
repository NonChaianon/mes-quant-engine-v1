from __future__ import annotations

import unittest

from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    DECODED_MES_1M_SHA256,
    FEATURE_ARTIFACT_SHA256,
    L1_ACCESS_LEVEL,
    L1_HARNESS_STATUS,
    ORDERED_FEATURE_CONTENT_SHA256,
    RAW_DBN_SHA256,
)
from mes_quant.exploration.test2_run_context import (
    VERIFIED_SOURCE_STATUS,
    CoverageEvidence,
    EvaluationRunContext,
    RunContextContractError,
    SourceIdentityEvidence,
)


def _real_context(**overrides: object) -> EvaluationRunContext:
    values: dict[str, object] = {
        "access_level": L1_ACCESS_LEVEL,
        "harness_status": L1_HARNESS_STATUS,
        "authorization_identity": "OWNER_TEST2_L1_TOKEN",
        "authorization_record_sha256": "a" * 64,
        "source_identity": SourceIdentityEvidence(
            raw_dbn_sha256=RAW_DBN_SHA256,
            decoded_mes_1m_sha256=DECODED_MES_1M_SHA256,
            feature_artifact_sha256=FEATURE_ARTIFACT_SHA256,
            ordered_feature_content_sha256=ORDERED_FEATURE_CONTENT_SHA256,
            evidence_status=VERIFIED_SOURCE_STATUS,
            content_sha256_evidence="RECOMPUTED_FROM_DECODED_FRAME_AFTER_AUTHORIZATION",
            release_manifest_sha256="b" * 64,
        ),
        "role_assignment_identity": CELL8_SPLIT_ASSIGNMENT_SHA256,
        "request_set_sha256": "c" * 64,
        "real_train_target_path_rows_read": 120,
        "validation_rows_read": 0,
        "final_test_rows_read": 0,
        "feature_max_source_time_asserted": True,
        "coverage": CoverageEvidence(2, 0, 0, 0, "ALL_ROWS", {}),
        "economic_diagnostics": {},
        "is_synthetic": False,
        "is_test_fixture": False,
    }
    values.update(overrides)
    return EvaluationRunContext(**values)


class EvaluationRunContextTests(unittest.TestCase):
    def test_synthetic_record_cannot_claim_l1_access_or_real_fits(self) -> None:
        context = EvaluationRunContext.synthetic()
        record = context.as_record(real_models_fitted=0)
        self.assertEqual(record["real_train_target_path_rows_read"], 0)
        self.assertFalse(record["feature_max_source_time_asserted"])
        with self.assertRaisesRegex(RunContextContractError, "real model"):
            context.as_record(real_models_fitted=1)

    def test_real_context_requires_verified_sources_and_positive_train_access(self) -> None:
        context = _real_context()
        self.assertEqual(context.as_record(real_models_fitted=4)["real_models_fitted"], 4)
        skipped = context.as_record(
            real_models_fitted=0,
            fit_status="SKIPPED_INCONCLUSIVE_UNDERPOWERED",
        )
        self.assertEqual(skipped["real_models_fitted"], 0)
        with self.assertRaisesRegex(RunContextContractError, "positive TRAIN"):
            _real_context(real_train_target_path_rows_read=0)

    def test_validation_or_final_test_access_is_rejected(self) -> None:
        with self.assertRaisesRegex(RunContextContractError, "Validation/Final"):
            _real_context(validation_rows_read=1)
        with self.assertRaisesRegex(RunContextContractError, "Validation/Final"):
            _real_context(final_test_rows_read=1)

    def test_real_context_rejects_declared_but_unverified_source_status(self) -> None:
        unverified = SourceIdentityEvidence(
            raw_dbn_sha256=RAW_DBN_SHA256,
            decoded_mes_1m_sha256=DECODED_MES_1M_SHA256,
            feature_artifact_sha256=FEATURE_ARTIFACT_SHA256,
            ordered_feature_content_sha256=ORDERED_FEATURE_CONTENT_SHA256,
            evidence_status="DECLARED_ONLY",
            content_sha256_evidence="NOT_RECOMPUTED",
        )
        with self.assertRaisesRegex(RunContextContractError, "verified source"):
            _real_context(source_identity=unverified)

    def test_real_context_requires_availability_assertion(self) -> None:
        with self.assertRaisesRegex(RunContextContractError, "availability"):
            _real_context(feature_max_source_time_asserted=False)


if __name__ == "__main__":
    unittest.main()

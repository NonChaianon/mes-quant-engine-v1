from __future__ import annotations

import unittest
from unittest.mock import patch

from mes_quant.exploration import l1_tree001
from mes_quant.exploration.l1_lr001 import L1AccessError
from mes_quant.exploration.tree001_authorization import (
    TREE001_AUTHORIZATION_REFERENCE,
    TREE001_AUTHORIZATION_STATUS,
    TREE001_AUTHORIZATION_TOKEN,
    TREE001_AUTHORIZED_EXPERIMENT_ID,
    activate_tree001_execution,
)


class TREE001ExecutionAuthorizationTests(unittest.TestCase):
    def test_authorization_metadata_is_exact_and_bounded(self) -> None:
        self.assertEqual(TREE001_AUTHORIZATION_STATUS, "ENABLED")
        self.assertEqual(TREE001_AUTHORIZATION_TOKEN, "OWNER_AUTHORIZED_TREE001_20260816")
        self.assertEqual(
            TREE001_AUTHORIZATION_REFERENCE,
            "Owner chat authorization 2026-08-16 / Issue #28",
        )
        self.assertEqual(
            TREE001_AUTHORIZED_EXPERIMENT_ID,
            "MES_S1_TREE001_20260815T192900Z",
        )

    def test_importing_authorization_does_not_activate_core_gate(self) -> None:
        self.assertEqual(
            l1_tree001.TREE001_EXECUTION_STATUS,
            "DISABLED_PENDING_OWNER_AUTHORIZATION",
        )
        self.assertEqual(l1_tree001.TREE001_AUTHORIZATION_TOKEN, "")

    def test_activation_sets_only_the_frozen_tree001_gate(self) -> None:
        with (
            patch.object(
                l1_tree001,
                "TREE001_EXECUTION_STATUS",
                "DISABLED_PENDING_OWNER_AUTHORIZATION",
            ),
            patch.object(l1_tree001, "TREE001_AUTHORIZATION_TOKEN", ""),
        ):
            activate_tree001_execution()
            self.assertEqual(l1_tree001.TREE001_EXECUTION_STATUS, "ENABLED")
            self.assertEqual(
                l1_tree001.TREE001_AUTHORIZATION_TOKEN,
                "OWNER_AUTHORIZED_TREE001_20260816",
            )
            self.assertEqual(
                l1_tree001.TREE001_EXPERIMENT_ID,
                TREE001_AUTHORIZED_EXPERIMENT_ID,
            )

    def test_wrong_token_blocks_before_artifact_path_access(self) -> None:
        with (
            patch.object(
                l1_tree001,
                "TREE001_EXECUTION_STATUS",
                "DISABLED_PENDING_OWNER_AUTHORIZATION",
            ),
            patch.object(l1_tree001, "TREE001_AUTHORIZATION_TOKEN", ""),
        ):
            activate_tree001_execution()
            with self.assertRaisesRegex(L1AccessError, "authorization token mismatch"):
                l1_tree001.run_tree001(
                    features_path="definitely_missing_features.parquet",
                    labels_path="definitely_missing_labels.parquet",
                    output_root="unused",
                    authorization_token="WRONG",
                    code_identity="synthetic-authorization-test",
                )

    def test_correct_token_reaches_preflight_but_not_real_data_in_test(self) -> None:
        with (
            patch.object(
                l1_tree001,
                "TREE001_EXECUTION_STATUS",
                "DISABLED_PENDING_OWNER_AUTHORIZATION",
            ),
            patch.object(l1_tree001, "TREE001_AUTHORIZATION_TOKEN", ""),
        ):
            activate_tree001_execution()
            with self.assertRaisesRegex(L1AccessError, "artifact does not exist"):
                l1_tree001.run_tree001(
                    features_path="definitely_missing_features.parquet",
                    labels_path="definitely_missing_labels.parquet",
                    output_root="unused",
                    authorization_token=TREE001_AUTHORIZATION_TOKEN,
                    code_identity="synthetic-authorization-test",
                )


if __name__ == "__main__":
    unittest.main()

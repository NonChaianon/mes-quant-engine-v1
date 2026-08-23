from __future__ import annotations

import json
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import Mock, patch

from mes_quant.exploration import test2_evaluation as evaluation
from mes_quant.exploration.test2_g3_contract import (
    DISPOSITION_DEFERRED_PENDING_G3F,
    G3F_GATE_LITERAL,
    SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
    G3FNotAuthorizedError,
    assert_g3f_not_authorized,
)
from mes_quant.exploration.test2_g3f_contract import (
    EXPECTED_FOLD_FIT_PAIRS,
    FROZEN_FOLD_IDS,
    FROZEN_MODEL_IDS,
    G3F_ALLOWED_CHANGED_FILES,
    G3F_CODE_ONLY_BASE_COMMIT,
    G3F_CODE_ONLY_BRANCH,
    G3F_CODE_ONLY_GATE_LITERAL,
    G3F_CODE_ONLY_STATUS,
    G3F_EXECUTION_STATUS,
    MAX_REAL_FOLD_FIT_CALLS,
    MAX_REAL_MODELS,
    PINNED_G3P_FILE_SHA256,
    PINNED_G3P_RECORD_SHA256,
    PINNED_G3P_RUN_ID,
    FoldFitBudget,
    G3FContractError,
    VerifiedG3PBinding,
    aggregate_record_sha256,
    changed_file_firewall_failures,
    mint_fold_fit_budget,
    protected_surface_failures,
    scientific_contract_witness,
    validate_aggregate_record,
    validate_g3p_binding,
    verify_pinned_g3p_record_file,
)
from mes_quant.exploration.test2_path_contract import FULL_MODEL_ID, NUISANCE_MODEL_ID
from mes_quant.exploration.test2_run_context import EvaluationRunContext

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _identity(seed: int) -> str:
    return f"{seed:064x}"


@lru_cache(maxsize=1)
def _verified_g3p_binding() -> VerifiedG3PBinding:
    record = _passing_g3p_record()
    with (
        patch.object(Path, "is_file", return_value=True),
        patch.object(Path, "read_text", return_value=json.dumps(record)),
        patch(
            "mes_quant.exploration.test2_g3f_contract.sha256_file",
            return_value=PINNED_G3P_FILE_SHA256,
        ),
        patch(
            "mes_quant.exploration.test2_g3f_contract.g3p_record_semantic_sha256",
            return_value=PINNED_G3P_RECORD_SHA256,
        ),
    ):
        return verify_pinned_g3p_record_file("/synthetic/g3p_record.json")


def _mint(seed: int):
    return mint_fold_fit_budget(
        gate_literal=G3F_GATE_LITERAL,
        authorization_identity_sha256=_identity(seed),
        g3p_binding=_verified_g3p_binding(),
    )


def _complete_budget(seed: int):
    budget = _mint(seed)
    for ordinal, (model_id, fold_id) in enumerate(EXPECTED_FOLD_FIT_PAIRS, start=1):
        permit = budget.consume(model_id=model_id, fold_id=fold_id)
        budget.complete_fit(
            permit,
            model_id=model_id,
            fold_id=fold_id,
            beta_sha256=f"{ordinal:064x}",
            coefficient_dimension=5 if model_id == NUISANCE_MODEL_ID else 30,
            optimizer_converged=True,
        )
    budget.seal()
    return budget


def _passing_g3p_record() -> dict[str, object]:
    return {
        "run_id": PINNED_G3P_RUN_ID,
        "record_sha256": PINNED_G3P_RECORD_SHA256,
        "status": "PASS",
        "disposition": DISPOSITION_DEFERRED_PENDING_G3F,
        "support_gate": {
            "passed": True,
            "status": SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
        },
        "counters": {
            "real_models_fitted": 0,
            "real_fold_fit_calls": 0,
            "bootstrap_replicates": 0,
            "economic_diagnostic_calls": 0,
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        },
    }


def _aggregate_record(seed: int = 100) -> dict[str, object]:
    budget = _complete_budget(seed).witness()
    completed = budget["completed_fits"]
    assert isinstance(completed, list)
    return {
        "gate_literal": G3F_GATE_LITERAL,
        "status": "PASS",
        "audit_written_utc": "2026-08-23T00:00:00Z",
        "branch": G3F_CODE_ONLY_BRANCH,
        "code_identity": "1" * 40,
        "run_id": "MES_T2_G3F_0123456789ABCDEF",
        "disposition": "NOT_INTERESTING_ENOUGH",
        "fit_budget": budget,
        "authorization_binding": {"identity_sha256": _identity(seed)},
        "g3p_binding": {
            "run_id": PINNED_G3P_RUN_ID,
            "record_sha256": PINNED_G3P_RECORD_SHA256,
            "disposition": DISPOSITION_DEFERRED_PENDING_G3F,
        },
        "scientific_contract": scientific_contract_witness(),
        "validation_status": "UNOPENED",
        "final_test_status": "SEALED",
        "access_counters": {
            "validation_rows_read": 0,
            "final_test_rows_read": 0,
        },
        "fold_metrics": {
            "WF_2022": {
                "row_count": 5_336,
                "prior_log_loss": 0.69,
                "nuisance_log_loss": 0.68,
                "full_log_loss": 0.67,
                "improvement_vs_prior": 0.02,
                "improvement_vs_nuisance": 0.01,
                "retained_sha256": "d" * 64,
            },
            "WF_2023": {
                "row_count": 5_437,
                "prior_log_loss": 0.69,
                "nuisance_log_loss": 0.68,
                "full_log_loss": 0.67,
                "improvement_vs_prior": 0.02,
                "improvement_vs_nuisance": 0.01,
                "retained_sha256": "e" * 64,
            },
        },
        "pooled_metrics": {
            "row_count": 10_773,
            "prior_log_loss": 0.69,
            "nuisance_log_loss": 0.68,
            "full_log_loss": 0.67,
            "improvement_vs_prior": 0.02,
            "improvement_vs_nuisance": 0.01,
            "retained_sha256": "f" * 64,
        },
        "bootstrap_summary": {
            "primary_lower_bound_vs_prior": 0.001,
            "primary_lower_bound_vs_nuisance": 0.001,
            "draw_identity_sha256": "a" * 64,
            "repetitions": 2_000,
            "primary_block_length": 5,
            "diagnostic_block_lengths": [1, 20],
        },
        "optimizer_summary": {
            "converged_fit_count": 4,
            "beta_sha256": [item["beta_sha256"] for item in completed],
            "coefficient_dimensions": [
                item["coefficient_dimension"] for item in completed
            ],
        },
        "support_summary": {
            "status": SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
            "floors_relaxed": False,
            "folds": {
                "WF_2022": {
                    "row_count": 5_336,
                    "governing_ess": 1_332.9,
                    "effective_negative_support": 919.0,
                    "effective_positive_support": 413.9,
                },
                "WF_2023": {
                    "row_count": 5_437,
                    "governing_ess": 1_284.7,
                    "effective_negative_support": 851.1,
                    "effective_positive_support": 433.6,
                },
            },
            "pooled": {
                "row_count": 10_773,
                "governing_ess": 2_642.9,
                "effective_negative_support": 1_786.2,
                "effective_positive_support": 856.6,
            },
        },
    }


class G3FCodeOnlyIdentityTests(unittest.TestCase):
    def test_identity_and_exact_additive_allowlist_are_frozen(self) -> None:
        self.assertEqual(
            G3F_CODE_ONLY_BASE_COMMIT,
            "7d66c43765c3a2c7f7acc772d8861490c70d6894",
        )
        self.assertEqual(G3F_CODE_ONLY_BRANCH, "research/test2-g3f-code-only-v1")
        self.assertEqual(G3F_CODE_ONLY_GATE_LITERAL, "G3F_CODE_ONLY_PREPARATION")
        self.assertEqual(G3F_CODE_ONLY_STATUS, "OWNER_AUTHORIZED_CODE_ONLY_PREPARATION")
        self.assertEqual(G3F_EXECUTION_STATUS, "NOT_AUTHORIZED")
        self.assertEqual(
            G3F_ALLOWED_CHANGED_FILES,
            {
                "docs/research/TEST2_G3F_PACKAGE_V1.md",
                "src/mes_quant/exploration/test2_g3f_contract.py",
                "tests/test_test2_g3f_contract.py",
            },
        )
        self.assertEqual(changed_file_firewall_failures(G3F_ALLOWED_CHANGED_FILES), ())
        self.assertTrue(changed_file_firewall_failures(set()))
        self.assertTrue(changed_file_firewall_failures({"tools/run_test2_g3f_fit.py"}))

    def test_every_guarded_and_fit_surface_is_byte_identical(self) -> None:
        self.assertEqual(protected_surface_failures(PROJECT_ROOT), ())

    def test_frozen_scientific_witness_has_no_knobs(self) -> None:
        witness = scientific_contract_witness()
        self.assertEqual(witness["model_ids"], ["PATHNUISANCE001", "PATHFULL001"])
        self.assertEqual(witness["fold_ids"], ["WF_2022", "WF_2023"])
        self.assertEqual(witness["full_feature_count"], 29)
        self.assertEqual(len(witness["nuisance_features"]), 4)
        self.assertEqual(witness["tick_size_points"], 0.25)
        self.assertEqual(witness["take_profit_ticks"], 16)
        self.assertEqual(witness["stop_ticks"], 8)
        self.assertEqual(witness["path_bar_count"], 60)
        self.assertEqual(witness["mde_vs_prior"], 0.0075)
        self.assertEqual(witness["mde_vs_nuisance"], 0.0075)
        self.assertEqual(witness["ess_floor_per_fold"], 1_000)
        self.assertEqual(witness["ess_floor_pooled"], 2_000)
        self.assertEqual(witness["effective_class_support_floor"], 200)
        self.assertEqual(witness["bootstrap_repetitions"], 2_000)
        self.assertEqual(witness["primary_block_length_sessions"], 5)
        self.assertEqual(witness["diagnostic_block_lengths"], [1, 20])
        self.assertEqual(witness["master_seed"], 20260809)
        self.assertEqual(witness["pooled_seed_offset"], 90_000)
        self.assertEqual(witness["fold_seed_stride"], 1_000)
        self.assertEqual(
            witness["numerical_policy"],
            {
                "l2_lambda": 0.001,
                "max_iterations": 50,
                "gradient_tolerance": 1e-8,
                "armijo_constant": 1e-4,
                "backtrack_shrink": 0.5,
                "minimum_step": 2.0**-20,
            },
        )


class FoldFitBudgetTests(unittest.TestCase):
    def test_exact_four_pair_cross_product_is_required(self) -> None:
        self.assertEqual(
            EXPECTED_FOLD_FIT_PAIRS,
            (
                (NUISANCE_MODEL_ID, "WF_2022"),
                (FULL_MODEL_ID, "WF_2022"),
                (NUISANCE_MODEL_ID, "WF_2023"),
                (FULL_MODEL_ID, "WF_2023"),
            ),
        )
        budget = _complete_budget(1)
        witness = budget.witness()
        self.assertEqual(witness["model_ids"], list(FROZEN_MODEL_IDS))
        self.assertEqual(witness["fold_ids"], list(FROZEN_FOLD_IDS))
        self.assertEqual(witness["real_models_fitted"], MAX_REAL_MODELS)
        self.assertEqual(witness["real_fold_fit_calls"], MAX_REAL_FOLD_FIT_CALLS)
        self.assertEqual(witness["search_budget_models_consumed"], 2)

    def test_constructor_cannot_be_called_directly(self) -> None:
        with self.assertRaisesRegex(G3FContractError, "must be minted"):
            FoldFitBudget(authorization_identity_sha256=_identity(2), _key=object())

    def test_wrong_order_or_duplicate_poison_budget(self) -> None:
        budget = _mint(3)
        with self.assertRaisesRegex(G3FContractError, "pair/order"):
            budget.consume(model_id=FULL_MODEL_ID, fold_id="WF_2022")
        self.assertTrue(budget.poisoned)
        with self.assertRaisesRegex(G3FContractError, "sealed or poisoned"):
            budget.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")

    def test_unknown_model_and_fold_fail_closed(self) -> None:
        bad_model = _mint(4)
        with self.assertRaises(G3FContractError):
            bad_model.consume(model_id="PATHGBM001", fold_id="WF_2022")
        bad_fold = _mint(5)
        with self.assertRaises(G3FContractError):
            bad_fold.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2024")

    def test_incomplete_seal_is_irreversible(self) -> None:
        budget = _mint(6)
        budget.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        with self.assertRaisesRegex(G3FContractError, "incomplete"):
            budget.seal()
        self.assertTrue(budget.sealed)
        self.assertTrue(budget.poisoned)
        with self.assertRaises(G3FContractError):
            budget.witness()

    def test_fifth_call_and_call_after_seal_are_refused(self) -> None:
        completed = _complete_budget(7)
        with self.assertRaisesRegex(G3FContractError, "sealed or poisoned"):
            completed.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")

        unsealed = _mint(8)
        for ordinal, (model_id, fold_id) in enumerate(EXPECTED_FOLD_FIT_PAIRS, start=1):
            permit = unsealed.consume(model_id=model_id, fold_id=fold_id)
            unsealed.complete_fit(
                permit,
                model_id=model_id,
                fold_id=fold_id,
                beta_sha256=f"{ordinal:064x}",
                coefficient_dimension=5 if model_id == NUISANCE_MODEL_ID else 30,
                optimizer_converged=True,
            )
        with self.assertRaisesRegex(G3FContractError, "fifth"):
            unsealed.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        self.assertTrue(unsealed.poisoned)

    def test_permit_must_come_from_same_live_budget_and_match_pair(self) -> None:
        first = _mint(9)
        first_permit = first.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        second = _mint(10)
        second.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        with self.assertRaisesRegex(G3FContractError, "without a permit"):
            second.complete_fit(
                first_permit,
                model_id=NUISANCE_MODEL_ID,
                fold_id="WF_2022",
                beta_sha256="1" * 64,
                coefficient_dimension=5,
                optimizer_converged=True,
            )
        self.assertTrue(second.poisoned)

    def test_permit_is_single_use_and_next_pair_requires_prior_use(self) -> None:
        reused = _mint(12)
        permit = reused.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        reused.complete_fit(
            permit,
            model_id=NUISANCE_MODEL_ID,
            fold_id="WF_2022",
            beta_sha256="1" * 64,
            coefficient_dimension=5,
            optimizer_converged=True,
        )
        with self.assertRaisesRegex(G3FContractError, "single-use"):
            reused.complete_fit(
                permit,
                model_id=NUISANCE_MODEL_ID,
                fold_id="WF_2022",
                beta_sha256="1" * 64,
                coefficient_dimension=5,
                optimizer_converged=True,
            )
        self.assertTrue(reused.poisoned)

        skipped = _mint(13)
        skipped.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        with self.assertRaisesRegex(G3FContractError, "no completed"):
            skipped.consume(model_id=FULL_MODEL_ID, fold_id="WF_2022")
        self.assertTrue(skipped.poisoned)

    def test_completion_requires_exact_dimension_convergence_and_hash(self) -> None:
        bad_dimension = _mint(14)
        permit = bad_dimension.consume(
            model_id=NUISANCE_MODEL_ID,
            fold_id="WF_2022",
        )
        with self.assertRaisesRegex(G3FContractError, "dimension"):
            bad_dimension.complete_fit(
                permit,
                model_id=NUISANCE_MODEL_ID,
                fold_id="WF_2022",
                beta_sha256="1" * 64,
                coefficient_dimension=30,
                optimizer_converged=True,
            )

        non_converged = _mint(15)
        permit = non_converged.consume(
            model_id=NUISANCE_MODEL_ID,
            fold_id="WF_2022",
        )
        with self.assertRaisesRegex(G3FContractError, "non-converged"):
            non_converged.complete_fit(
                permit,
                model_id=NUISANCE_MODEL_ID,
                fold_id="WF_2022",
                beta_sha256="1" * 64,
                coefficient_dimension=5,
                optimizer_converged=False,
            )

        bad_hash = _mint(16)
        permit = bad_hash.consume(model_id=NUISANCE_MODEL_ID, fold_id="WF_2022")
        with self.assertRaisesRegex(G3FContractError, "SHA-256"):
            bad_hash.complete_fit(
                permit,
                model_id=NUISANCE_MODEL_ID,
                fold_id="WF_2022",
                beta_sha256="not-a-hash",
                coefficient_dimension=5,
                optimizer_converged=True,
            )

    def test_one_owner_authorization_cannot_mint_twice_in_process(self) -> None:
        authorization = _identity(11)
        mint_fold_fit_budget(
            gate_literal=G3F_GATE_LITERAL,
            authorization_identity_sha256=authorization,
            g3p_binding=_verified_g3p_binding(),
        )
        with self.assertRaisesRegex(G3FContractError, "already minted"):
            mint_fold_fit_budget(
                gate_literal=G3F_GATE_LITERAL,
                authorization_identity_sha256=authorization,
                g3p_binding=_verified_g3p_binding(),
            )

    def test_wrong_gate_or_forged_g3p_binding_cannot_mint(self) -> None:
        with self.assertRaisesRegex(G3FContractError, "exact G3-F"):
            mint_fold_fit_budget(
                gate_literal=G3F_CODE_ONLY_GATE_LITERAL,
                authorization_identity_sha256=_identity(20),
                g3p_binding=_verified_g3p_binding(),
            )

        forged = VerifiedG3PBinding(
            run_id=PINNED_G3P_RUN_ID,
            record_sha256=PINNED_G3P_RECORD_SHA256,
            file_sha256=PINNED_G3P_FILE_SHA256,
            disposition=DISPOSITION_DEFERRED_PENDING_G3F,
            _verification_key=object(),
        )
        with self.assertRaisesRegex(G3FContractError, "verified G3-P"):
            mint_fold_fit_budget(
                gate_literal=G3F_GATE_LITERAL,
                authorization_identity_sha256=_identity(21),
                g3p_binding=forged,
            )


class BindingAndRecordTests(unittest.TestCase):
    def test_passing_g3p_aggregate_binding_is_accepted(self) -> None:
        validate_g3p_binding(_passing_g3p_record())
        binding = _verified_g3p_binding()
        self.assertEqual(binding.run_id, PINNED_G3P_RUN_ID)
        self.assertEqual(binding.record_sha256, PINNED_G3P_RECORD_SHA256)
        self.assertEqual(binding.file_sha256, PINNED_G3P_FILE_SHA256)

    def test_g3p_file_verifier_requires_byte_and_semantic_identity(self) -> None:
        record = _passing_g3p_record()
        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "read_text", return_value=json.dumps(record)),
            patch(
                "mes_quant.exploration.test2_g3f_contract.sha256_file",
                return_value="0" * 64,
            ),self.assertRaisesRegex(G3FContractError, "byte SHA-256")
        ):
            verify_pinned_g3p_record_file("/synthetic/g3p_record.json")

        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "read_text", return_value=json.dumps(record)),
            patch(
                "mes_quant.exploration.test2_g3f_contract.sha256_file",
                return_value=PINNED_G3P_FILE_SHA256,
            ),
            patch(
                "mes_quant.exploration.test2_g3f_contract.g3p_record_semantic_sha256",
                return_value="0" * 64,
            ),self.assertRaisesRegex(G3FContractError, "semantic")
        ):
            verify_pinned_g3p_record_file("/synthetic/g3p_record.json")

    def test_g3p_binding_fails_closed_on_each_governing_field(self) -> None:
        mutations = (
            ("run_id", "WRONG"),
            ("record_sha256", "0" * 64),
            ("status", "FAIL"),
            ("disposition", "INCONCLUSIVE_UNDERPOWERED"),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                record = _passing_g3p_record()
                record[key] = value
                with self.assertRaises(G3FContractError):
                    validate_g3p_binding(record)

        support_fail = _passing_g3p_record()
        support_fail["support_gate"] = {"passed": False, "status": "FAIL"}
        with self.assertRaises(G3FContractError):
            validate_g3p_binding(support_fail)

        fitted = _passing_g3p_record()
        fitted["counters"]["real_models_fitted"] = 1  # type: ignore[index]
        with self.assertRaises(G3FContractError):
            validate_g3p_binding(fitted)

        false_counter = _passing_g3p_record()
        false_counter["counters"]["real_models_fitted"] = False  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "integer 0"):
            validate_g3p_binding(false_counter)

        float_counter = _passing_g3p_record()
        float_counter["counters"]["real_models_fitted"] = 0.0  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "integer 0"):
            validate_g3p_binding(float_counter)

    def test_aggregate_record_accepts_metrics_but_rejects_row_or_beta_payloads(self) -> None:
        validate_aggregate_record(_aggregate_record(30))
        forbidden_keys = (
            "decision_ids",
            "decision_time",
            "session_ids",
            "probabilities",
            "row_losses",
            "decile_cut_points",
            "coefficients",
            "beta",
            "trade_ledger",
        )
        for offset, key in enumerate(forbidden_keys, start=31):
            with self.subTest(key=key):
                record = _aggregate_record(offset)
                record["fold_metrics"]["WF_2022"][key] = [1, 2, 3]  # type: ignore[index]
                with self.assertRaisesRegex(G3FContractError, "forbidden"):
                    validate_aggregate_record(record)

    def test_exact_schema_rejects_benign_key_row_payload_and_non_integer_counters(
        self,
    ) -> None:
        row_payload = _aggregate_record(45)
        row_payload["fold_metrics"]["WF_2022"]["values"] = [0.1] * 10  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "non-aggregate"):
            validate_aggregate_record(row_payload)

        float_counter = _aggregate_record(46)
        float_counter["fit_budget"]["real_fold_fit_calls"] = 4.0  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "integer 4"):
            validate_aggregate_record(float_counter)

        boolean_zero = _aggregate_record(47)
        boolean_zero["access_counters"]["validation_rows_read"] = False  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "integer 0"):
            validate_aggregate_record(boolean_zero)

        optional_blob = _aggregate_record(48)
        optional_blob["code_identity"] = {"detail": [0.1] * 100}
        with self.assertRaisesRegex(G3FContractError, "Git SHA"):
            validate_aggregate_record(optional_blob)

    def test_record_requires_all_primary_metric_and_bootstrap_evidence(self) -> None:
        missing_fold = _aggregate_record(49)
        del missing_fold["fold_metrics"]["WF_2022"]["improvement_vs_prior"]  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "missing required evidence"):
            validate_aggregate_record(missing_fold)

        missing_pooled = _aggregate_record(53)
        del missing_pooled["pooled_metrics"]["full_log_loss"]  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "missing required evidence"):
            validate_aggregate_record(missing_pooled)

        missing_bootstrap = _aggregate_record(54)
        del missing_bootstrap["bootstrap_summary"][  # type: ignore[index]
            "primary_lower_bound_vs_nuisance"
        ]
        with self.assertRaisesRegex(G3FContractError, "missing required evidence"):
            validate_aggregate_record(missing_bootstrap)

    def test_record_rejects_validation_final_or_budget_counter_mismatch(self) -> None:
        validation = _aggregate_record(50)
        validation["access_counters"]["validation_rows_read"] = 1  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "validation_rows_read"):
            validate_aggregate_record(validation)

        final = _aggregate_record(51)
        final["access_counters"]["final_test_rows_read"] = 1  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "final_test_rows_read"):
            validate_aggregate_record(final)

        wrong_budget = _aggregate_record(52)
        wrong_budget["fit_budget"]["real_fold_fit_calls"] = 5  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "real_fold_fit_calls"):
            validate_aggregate_record(wrong_budget)

    def test_record_hash_is_deterministic_modulo_audit_time_and_self_hash(self) -> None:
        first = _aggregate_record(60)
        second = dict(first)
        second["audit_written_utc"] = "2099-01-01T00:00:00Z"
        second["record_sha256"] = "f" * 64
        self.assertEqual(aggregate_record_sha256(first), aggregate_record_sha256(second))

    def test_record_governance_bindings_fail_closed(self) -> None:
        mutations = (
            ("gate_literal", "WRONG"),
            ("validation_status", "OPEN"),
            ("final_test_status", "OPEN"),
            ("status", "FAIL"),
        )
        for offset, (key, value) in enumerate(mutations, start=70):
            with self.subTest(key=key):
                record = _aggregate_record(offset)
                record[key] = value
                with self.assertRaises(G3FContractError):
                    validate_aggregate_record(record)

        for offset, (key, value) in enumerate(
            (
                ("run_id", "WRONG"),
                ("record_sha256", "0" * 64),
                ("disposition", "WRONG"),
            ),
            start=80,
        ):
            with self.subTest(g3p_key=key):
                record = _aggregate_record(offset)
                record["g3p_binding"][key] = value  # type: ignore[index]
                with self.assertRaises(G3FContractError):
                    validate_aggregate_record(record)

        science = _aggregate_record(83)
        science["scientific_contract"] = {"mde_vs_prior": 0.0}
        with self.assertRaisesRegex(G3FContractError, "scientific"):
            validate_aggregate_record(science)

        unsealed = _aggregate_record(84)
        unsealed["fit_budget"]["sealed"] = False  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "sealed"):
            validate_aggregate_record(unsealed)

        divergent = _aggregate_record(85)
        divergent["authorization_binding"]["identity_sha256"] = "f" * 64  # type: ignore[index]
        with self.assertRaisesRegex(G3FContractError, "diverged"):
            validate_aggregate_record(divergent)


class ExistingBarrierRegressionTests(unittest.TestCase):
    def test_existing_g3f_barrier_still_raises(self) -> None:
        with self.assertRaises(G3FNotAuthorizedError):
            assert_g3f_not_authorized()

    def test_real_evaluation_rejects_synthetic_context_before_any_fit(self) -> None:
        fitter = Mock(side_effect=AssertionError("fitter must not be called"))
        with (
            patch.object(evaluation, "fit_frozen_logistic", fitter),
            self.assertRaisesRegex(
                evaluation.Test2EvaluationContractError,
                "real non-fixture",
            ),
        ):
            evaluation.run_authorized_train_evaluation(
                (),
                timestamp_utc=Mock(),
                code_identity="1" * 40,
                run_context=EvaluationRunContext.synthetic(),
                governance_gates_passed=True,
            )
        fitter.assert_not_called()


if __name__ == "__main__":
    unittest.main()

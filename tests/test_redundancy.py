from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from mes_quant.redundancy import contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sha256_raw(path: Path) -> str:
    """Hash exact file bytes without text/newline normalization."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StageBLockedControlTests(unittest.TestCase):
    def test_v12_lock_and_prior_v11_provenance_are_pinned(self) -> None:
        self.assertEqual(
            contract.POLICY_VERSION,
            "MES_V1_REDUNDANCY_1.2",
        )
        self.assertEqual(
            contract.REMEDIATION_BASE_COMMIT,
            "a5d3f40e7edc26d950010401654ce4d6b7822e86",
        )
        self.assertEqual(
            contract.PRIOR_V1_1_LOCKED_CONTROL_COMMIT,
            "bd9e38c11e01bae18a5ffa0a6a0405a008273d27",
        )
        self.assertEqual(
            contract.LOCKED_CONTROL_COMMIT,
            "a60d2498754df641e9c8a3308d330f3c4e05fb74",
        )
        self.assertEqual(
            contract.MARKDOWN_CONTRACT_PATH,
            "docs/STAGE_B_REDUNDANCY_CONTRACT.md",
        )
        self.assertEqual(
            contract.SEMANTIC_REGISTRY_PATH,
            "configs/v1/stage_b_semantic_registry_v1.json",
        )

    def test_raw_locked_control_bytes_match_python_pins(self) -> None:
        markdown = PROJECT_ROOT / contract.MARKDOWN_CONTRACT_PATH
        registry = PROJECT_ROOT / contract.SEMANTIC_REGISTRY_PATH

        self.assertTrue(markdown.is_file())
        self.assertTrue(registry.is_file())

        self.assertEqual(
            sha256_raw(markdown),
            contract.MARKDOWN_CONTRACT_SHA256,
        )
        self.assertEqual(
            sha256_raw(registry),
            contract.SEMANTIC_REGISTRY_SHA256,
        )

    def test_locked_policy_controls_and_disabled_execution_agree(self) -> None:
        markdown = (
            PROJECT_ROOT / contract.MARKDOWN_CONTRACT_PATH
        ).read_text(encoding="utf-8")

        registry = json.loads(
            (
                PROJECT_ROOT / contract.SEMANTIC_REGISTRY_PATH
            ).read_text(encoding="utf-8")
        )

        self.assertIn(
            "Policy status: **LOCKED_EXECUTABLE**",
            markdown,
        )
        self.assertEqual(
            registry["registry_status"],
            "LOCKED_EXECUTABLE",
        )
        self.assertEqual(
            contract.POLICY_STATUS,
            "PROVISIONAL",
        )
        self.assertEqual(
            registry["policy_version"],
            contract.POLICY_VERSION,
        )
        self.assertEqual(
            registry["source_contract"],
            contract.MARKDOWN_CONTRACT_PATH,
        )

    def test_repository_byte_policy_disables_text_normalization(self) -> None:
        attributes = (
            PROJECT_ROOT / ".gitattributes"
        ).read_text(encoding="utf-8")

        lines = [
            line.strip()
            for line in attributes.splitlines()
            if line.strip()
            and not line.lstrip().startswith("#")
        ]

        self.assertIn("* -text", lines)

    def test_stale_duplicate_policy_constants_do_not_return(self) -> None:
        self.assertFalse(
            hasattr(contract, "REPRESENTATIVE_TIE_BREAK")
        )
        self.assertFalse(
            hasattr(contract, "PAIRWISE_COVERAGE_POLICY")
        )


class StageBConstitutionalPolicyGateDirectTests(
    unittest.TestCase
):
    """Exercise locked policy controls with execution disabled by default."""

    @staticmethod
    def _call_gate() -> None:
        from mes_quant.redundancy import analyzer

        analyzer.assert_stage_b_contract_locked(
            project_root=PROJECT_ROOT,
        )

    def test_execution_disabled_python_status_fails_closed(
        self,
    ) -> None:
        self.assertEqual(
            contract.POLICY_STATUS,
            "PROVISIONAL",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "LOCKED_EXECUTABLE",
        ):
            self._call_gate()

    def test_explicit_execution_status_patch_accepts_locked_controls(
        self,
    ) -> None:
        from unittest.mock import patch

        with patch.object(
            contract,
            "POLICY_STATUS",
            "LOCKED_EXECUTABLE",
        ):
            self._call_gate()

    def test_wrong_policy_version_fails_closed(
        self,
    ) -> None:
        from unittest.mock import patch

        with (
            patch.object(
                contract,
                "POLICY_STATUS",
                "LOCKED_EXECUTABLE",
            ),
            patch.object(
                contract,
                "POLICY_VERSION",
                "MES_V1_REDUNDANCY_WRONG",
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "policy version",
            ):
                self._call_gate()

    def test_wrong_markdown_hash_fails_closed(
        self,
    ) -> None:
        from unittest.mock import patch

        with (
            patch.object(
                contract,
                "POLICY_STATUS",
                "LOCKED_EXECUTABLE",
            ),
            patch.object(
                contract,
                "MARKDOWN_CONTRACT_SHA256",
                "0" * 64,
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Markdown contract SHA256 mismatch",
            ):
                self._call_gate()

    def test_wrong_semantic_registry_hash_fails_closed(
        self,
    ) -> None:
        from unittest.mock import patch

        with (
            patch.object(
                contract,
                "POLICY_STATUS",
                "LOCKED_EXECUTABLE",
            ),
            patch.object(
                contract,
                "SEMANTIC_REGISTRY_SHA256",
                "0" * 64,
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "semantic registry SHA256 mismatch",
            ):
                self._call_gate()

    def test_wrong_python_status_fails_closed(
        self,
    ) -> None:
        from unittest.mock import patch

        with patch.object(
            contract,
            "POLICY_STATUS",
            "OPEN",
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "LOCKED_EXECUTABLE",
            ):
                self._call_gate()


class StageBProjectRootGateSpecificationTests(
    unittest.TestCase
):
    """Lock one caller-supplied root for the constitutional gate."""

    @staticmethod
    def _build_control_root(
        root: Path,
    ) -> None:
        for relative_path in (
            contract.MARKDOWN_CONTRACT_PATH,
            contract.SEMANTIC_REGISTRY_PATH,
        ):
            source = PROJECT_ROOT / relative_path
            destination = root / relative_path
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_bytes(
                source.read_bytes()
            )

    @staticmethod
    def _hash_locked_controls_for_gate_test(
        root: Path,
    ) -> tuple[str, str]:
        """Hash isolated copies of the locked policy controls."""

        markdown_path = root / contract.MARKDOWN_CONTRACT_PATH
        registry_path = root / contract.SEMANTIC_REGISTRY_PATH

        markdown = markdown_path.read_text(encoding="utf-8")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        if "Policy status: **LOCKED_EXECUTABLE**" not in markdown:
            raise AssertionError(
                "copied Markdown policy control is not locked"
            )
        if registry["registry_status"] != "LOCKED_EXECUTABLE":
            raise AssertionError(
                "copied semantic registry is not locked"
            )

        return (
            sha256_raw(markdown_path),
            sha256_raw(registry_path),
        )

    def test_gate_requires_explicit_keyword_only_project_root(
        self,
    ) -> None:
        import inspect

        from mes_quant.redundancy import analyzer

        signature = inspect.signature(
            analyzer.assert_stage_b_contract_locked
        )

        self.assertEqual(
            tuple(signature.parameters),
            ("project_root",),
        )
        self.assertEqual(
            signature.parameters[
                "project_root"
            ].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

    def test_real_gate_rejects_tampered_control_under_supplied_root(
        self,
    ) -> None:
        import tempfile
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer

        with tempfile.TemporaryDirectory() as temp_dir:
            alternate_root = Path(temp_dir)
            self._build_control_root(
                alternate_root
            )

            markdown_path = (
                alternate_root
                / contract.MARKDOWN_CONTRACT_PATH
            )
            markdown_path.write_bytes(
                markdown_path.read_bytes()
                + b"\nTAMPERED_ALTERNATE_ROOT\n"
            )

            with (
                patch.object(
                    contract,
                    "POLICY_STATUS",
                    "LOCKED_EXECUTABLE",
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "Markdown contract SHA256 mismatch",
                ),
            ):
                analyzer.assert_stage_b_contract_locked(
                    project_root=alternate_root,
                )

    def test_real_gate_accepts_exact_controls_under_supplied_root(
        self,
    ) -> None:
        import tempfile
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer

        with tempfile.TemporaryDirectory() as temp_dir:
            alternate_root = Path(temp_dir)
            self._build_control_root(
                alternate_root
            )

            markdown_hash, registry_hash = (
                self._hash_locked_controls_for_gate_test(
                    alternate_root
                )
            )

            with (
                patch.object(
                    contract,
                    "POLICY_STATUS",
                    "LOCKED_EXECUTABLE",
                ),
                patch.object(
                    contract,
                    "MARKDOWN_CONTRACT_SHA256",
                    markdown_hash,
                ),
                patch.object(
                    contract,
                    "SEMANTIC_REGISTRY_SHA256",
                    registry_hash,
                ),
            ):
                analyzer.assert_stage_b_contract_locked(
                    project_root=alternate_root,
                )

    def test_run_stage_b_first_action_routes_caller_project_root_to_gate(
        self,
    ) -> None:
        import ast
        import inspect
        import textwrap

        from mes_quant.redundancy import analyzer

        source = textwrap.dedent(
            inspect.getsource(
                analyzer.run_stage_b
            )
        )
        function = ast.parse(source).body[0]

        executable = list(function.body)
        if (
            executable
            and isinstance(executable[0], ast.Expr)
            and isinstance(
                executable[0].value,
                ast.Constant,
            )
            and isinstance(
                executable[0].value.value,
                str,
            )
        ):
            executable = executable[1:]

        first_action = executable[0]
        self.assertIsInstance(
            first_action,
            ast.Expr,
        )
        self.assertIsInstance(
            first_action.value,
            ast.Call,
        )
        self.assertIsInstance(
            first_action.value.func,
            ast.Name,
        )
        self.assertEqual(
            first_action.value.func.id,
            "assert_stage_b_contract_locked",
        )
        self.assertEqual(
            first_action.value.args,
            [],
        )
        self.assertEqual(
            len(first_action.value.keywords),
            1,
        )
        keyword = first_action.value.keywords[0]
        self.assertEqual(
            keyword.arg,
            "project_root",
        )
        self.assertIsInstance(
            keyword.value,
            ast.Name,
        )
        self.assertEqual(
            keyword.value.id,
            "project_root",
        )


class StageBSemanticRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (
                PROJECT_ROOT / contract.SEMANTIC_REGISTRY_PATH
            ).read_text(encoding="utf-8")
        )
        cls.checks = cls.registry["semantic_checks"]

    def test_registry_schema_uniqueness_and_required_fields(self) -> None:
        required_top_level = {
            "policy_version",
            "registry_status",
            "source_contract",
            "semantic_checks",
        }

        self.assertTrue(
            required_top_level.issubset(self.registry)
        )
        self.assertEqual(len(self.checks), 6)

        required_fields = {
            "check_id",
            "check_type",
            "features",
            "dependent_features",
            "determining_features",
            "scope",
            "decision_effect",
            "implementation_key",
            "dependency_group",
            "required_drop_count",
            "protect_determining_features",
            "rationale",
        }

        check_ids = []
        implementation_keys = []
        dependency_groups = []

        for entry in self.checks:
            with self.subTest(
                check_id=entry.get("check_id")
            ):
                self.assertTrue(
                    required_fields.issubset(entry)
                )

                self.assertIsInstance(
                    entry["features"],
                    list,
                )
                self.assertGreater(
                    len(entry["features"]),
                    0,
                )

                self.assertIsInstance(
                    entry["dependent_features"],
                    list,
                )
                self.assertIsInstance(
                    entry["determining_features"],
                    list,
                )
                self.assertIsInstance(
                    entry["protect_determining_features"],
                    bool,
                )

                self.assertNotIn(
                    "|",
                    entry["dependency_group"],
                )

                self.assertTrue(
                    set(entry["dependent_features"])
                    .issubset(entry["features"])
                )
                self.assertTrue(
                    set(entry["determining_features"])
                    .issubset(entry["features"])
                )

                self.assertIsInstance(
                    entry["decision_effect"],
                    str,
                )
                self.assertTrue(
                    entry["decision_effect"]
                )

                self.assertIsInstance(
                    entry["rationale"],
                    str,
                )
                self.assertTrue(
                    entry["rationale"]
                )

                check_ids.append(
                    entry["check_id"]
                )
                implementation_keys.append(
                    entry["implementation_key"]
                )
                dependency_groups.append(
                    entry["dependency_group"]
                )

        self.assertEqual(
            len(check_ids),
            len(set(check_ids)),
        )
        self.assertEqual(
            len(implementation_keys),
            len(set(implementation_keys)),
        )
        self.assertEqual(
            len(dependency_groups),
            len(set(dependency_groups)),
        )

    def test_check_type_structural_invariants(self) -> None:
        # This table verifies ?13.2 structure.
        # It is test expectation, not analyzer/runtime policy.
        invariants = {
            "EXACT_LINEAR_DERIVED_IDENTITY": (
                True,
                True,
                1,
            ),
            "EXACT_NONLINEAR_DERIVED_REPRESENTATION": (
                True,
                True,
                0,
            ),
            "EXACT_AFFINE_DERIVED_IDENTITY": (
                True,
                True,
                1,
            ),
            "EXACT_AFFINE_DEPENDENCY": (
                False,
                False,
                1,
            ),
            "PAIRED_NONLINEAR_REPRESENTATION": (
                False,
                False,
                0,
            ),
            "EMPIRICAL_NEAR_IDENTITY": (
                False,
                False,
                None,
            ),
        }

        for entry in self.checks:
            check_type = entry["check_type"]

            with self.subTest(
                check_id=entry["check_id"],
                check_type=check_type,
            ):
                self.assertIn(
                    check_type,
                    invariants,
                )

                (
                    dependent_nonempty,
                    determining_nonempty,
                    required_drop_count,
                ) = invariants[check_type]

                self.assertEqual(
                    bool(entry["dependent_features"]),
                    dependent_nonempty,
                )
                self.assertEqual(
                    bool(entry["determining_features"]),
                    determining_nonempty,
                )
                self.assertEqual(
                    entry["required_drop_count"],
                    required_drop_count,
                )

    def test_every_semantic_check_is_train_per_fold(self) -> None:
        for entry in self.checks:
            with self.subTest(
                check_id=entry["check_id"]
            ):
                self.assertEqual(
                    entry["scope"],
                    "TRAIN_PER_FOLD",
                )

    def test_protected_set_derivation_matches_v11_safety_sentinel(self) -> None:
        protected = []

        for entry in self.checks:
            if entry["protect_determining_features"]:
                for feature in entry["determining_features"]:
                    if feature not in protected:
                        protected.append(feature)

        expected = [
            "ret_log_15m_lag0",
            "ret_log_15m_lag1",
            "ret_log_15m_lag2",
            "ret_log_15m_lag3",
            "minutes_since_nyse_open",
            "early_close_session",
        ]

        self.assertEqual(
            protected,
            expected,
        )

        forbidden = {
            "weekday_0",
            "weekday_1",
            "weekday_2",
            "weekday_3",
            "weekday_4",
            "momentum_log_60m",
            "realized_vol_60m",
            "minutes_to_horizon_safe_close",
        }

        self.assertTrue(
            forbidden.isdisjoint(protected)
        )


# STEP_13C_SEMANTIC_RUNTIME_SPEC_V1

class StageBSemanticRuntimeSpecificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from mes_quant.redundancy import analyzer

        cls.analyzer = analyzer

        cls.registry = json.loads(
            (
                PROJECT_ROOT
                / contract.SEMANTIC_REGISTRY_PATH
            ).read_text(encoding="utf-8")
        )

        cls.checks = cls.registry["semantic_checks"]

    def test_registry_implementation_keys_resolve_to_callables(self) -> None:
        for entry in self.checks:
            implementation_key = entry["implementation_key"]

            with self.subTest(
                check_id=entry["check_id"],
                implementation_key=implementation_key,
            ):
                implementation = getattr(
                    self.analyzer,
                    implementation_key,
                    None,
                )

                self.assertTrue(
                    callable(implementation),
                    (
                        "Missing callable analyzer implementation for "
                        f"{implementation_key}"
                    ),
                )

    def test_unknown_check_type_fails_closed(self) -> None:
        import copy

        validator = getattr(
            self.analyzer,
            "validate_semantic_registry",
            None,
        )

        self.assertTrue(
            callable(validator),
            "analyzer.validate_semantic_registry must exist",
        )

        candidate = copy.deepcopy(self.registry)

        candidate["semantic_checks"][0][
            "check_type"
        ] = "UNKNOWN_STAGE_B_CHECK_TYPE"

        try:
            validator(candidate)
        except (ValueError, RuntimeError):
            pass
        else:
            self.fail(
                "Unknown check_type must fail closed."
            )

    def test_reserved_dependency_group_delimiter_is_rejected(self) -> None:
        import copy

        validator = getattr(
            self.analyzer,
            "validate_semantic_registry",
            None,
        )

        self.assertTrue(
            callable(validator),
            "analyzer.validate_semantic_registry must exist",
        )

        candidate = copy.deepcopy(self.registry)

        candidate["semantic_checks"][0][
            "dependency_group"
        ] = "INVALID|GROUP"

        try:
            validator(candidate)
        except (ValueError, RuntimeError):
            pass
        else:
            self.fail(
                "Reserved dependency_group delimiter must fail closed."
            )

    def test_check_type_drop_count_violation_is_rejected(self) -> None:
        import copy

        validator = getattr(
            self.analyzer,
            "validate_semantic_registry",
            None,
        )

        self.assertTrue(
            callable(validator),
            "analyzer.validate_semantic_registry must exist",
        )

        candidate = copy.deepcopy(self.registry)

        momentum = next(
            entry
            for entry in candidate["semantic_checks"]
            if entry["check_id"] == "SEM_MOMENTUM_60M"
        )

        momentum["required_drop_count"] = 0

        try:
            validator(candidate)
        except (ValueError, RuntimeError):
            pass
        else:
            self.fail(
                "Invalid check-type structural invariant must fail closed."
            )

    def test_protected_features_are_derived_from_registry(self) -> None:
        import copy

        derive = getattr(
            self.analyzer,
            "derive_protected_features",
            None,
        )

        self.assertTrue(
            callable(derive),
            "analyzer.derive_protected_features must exist",
        )

        protected = list(
            derive(self.registry)
        )

        expected = [
            "ret_log_15m_lag0",
            "ret_log_15m_lag1",
            "ret_log_15m_lag2",
            "ret_log_15m_lag3",
            "minutes_since_nyse_open",
            "early_close_session",
        ]

        self.assertEqual(
            protected,
            expected,
        )

        # Prove runtime derivation is registry-driven rather
        # than an independent hard-coded protected list.
        candidate = copy.deepcopy(self.registry)

        safe_close = next(
            entry
            for entry in candidate["semantic_checks"]
            if entry["check_id"]
            == "SEM_HORIZON_SAFE_CLOSE"
        )

        safe_close[
            "protect_determining_features"
        ] = False

        mutated = list(
            derive(candidate)
        )

        self.assertEqual(
            mutated,
            [
                "ret_log_15m_lag0",
                "ret_log_15m_lag1",
                "ret_log_15m_lag2",
                "ret_log_15m_lag3",
            ],
        )



# STEP_13D1_ZERO_VARIANCE_AND_SVD_SPEC_V1

class StageBZeroVarianceAndSVDSpecificationTests(unittest.TestCase):
    def test_dual_zero_variance_scopes_are_not_conflated(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "compute_zero_variance_diagnostics",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer.compute_zero_variance_diagnostics must exist",
        )

        df = pd.DataFrame(
            {
                "role_wf_2022": [
                    "TRAIN",
                    "TRAIN",
                    "TRAIN",
                    "TRAIN",
                ],
                "x": [1.0, 2.0, 1.0, 4.0],
                "z": [10.0, None, 20.0, None],
            }
        )

        result = compute(
            df=df,
            fold_role_column="role_wf_2022",
            feature_columns=["x", "z"],
        )

        x = result.loc[
            result["feature"].eq("x")
        ].iloc[0]

        self.assertEqual(
            int(x["full_train_available_rows"]),
            4,
        )

        self.assertFalse(
            bool(x["full_train_zero_variance"])
        )

        self.assertEqual(
            int(x["common_cohort_rows"]),
            2,
        )

        self.assertTrue(
            bool(x["common_cohort_zero_variance"])
        )

    def test_zero_variance_drop_uses_full_train_only(self) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "resolve_zero_variance_base_decision",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer.resolve_zero_variance_base_decision must exist",
        )

        keep = resolve(
            full_train_zero_by_fold={
                "role_wf_2022": False,
                "role_wf_2023": False,
                "role_wf_2024": False,
            },
            common_cohort_zero_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            semantic_basis_protected=False,
        )

        self.assertEqual(
            keep["base_decision"],
            "KEEP",
        )

        drop = resolve(
            full_train_zero_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            common_cohort_zero_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            semantic_basis_protected=False,
        )

        self.assertEqual(
            drop["base_decision"],
            "DROP_REDUNDANT",
        )

        self.assertEqual(
            drop["decision_basis"],
            "ZERO_VARIANCE_NO_INFORMATION",
        )

    def test_protected_feature_cannot_be_zero_variance_auto_dropped(self) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "resolve_zero_variance_base_decision",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer.resolve_zero_variance_base_decision must exist",
        )

        result = resolve(
            full_train_zero_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            common_cohort_zero_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            semantic_basis_protected=True,
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

    def test_standardized_matrix_is_float64_and_uses_ddof_zero(self) -> None:
        import numpy as np
        import pandas as pd

        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "build_standardized_matrix",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer.build_standardized_matrix must exist",
        )

        frame = pd.DataFrame(
            {
                "a": [1.0, 2.0, 3.0, 4.0],
                "b": [10.0, 20.0, 30.0, 40.0],
            }
        )

        z = build(
            frame=frame,
            feature_columns=["a", "b"],
        )

        self.assertEqual(
            z.dtype,
            np.dtype("float64"),
        )

        np.testing.assert_allclose(
            z.mean(axis=0),
            np.zeros(2),
            atol=1e-12,
        )

        np.testing.assert_allclose(
            z.std(axis=0, ddof=0),
            np.ones(2),
            atol=1e-12,
        )

    def test_svd_detects_exact_linear_rank_deficiency(self) -> None:
        import numpy as np
        import pandas as pd

        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "build_standardized_matrix",
            None,
        )

        diagnose = getattr(
            analyzer,
            "compute_svd_diagnostics",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer.build_standardized_matrix must exist",
        )

        self.assertTrue(
            callable(diagnose),
            "analyzer.compute_svd_diagnostics must exist",
        )

        frame = pd.DataFrame(
            {
                "a": [1.0, 2.0, 4.0, 8.0, 16.0],
                "b": [2.0, 5.0, 3.0, 9.0, 7.0],
            }
        )

        frame["c"] = (
            frame["a"]
            + frame["b"]
        )

        z = build(
            frame=frame,
            feature_columns=["a", "b", "c"],
        )

        result = diagnose(z)

        self.assertEqual(
            tuple(result["matrix_shape"]),
            (5, 3),
        )

        self.assertEqual(
            result["rank"],
            2,
        )

        self.assertEqual(
            result["deficiency"],
            1,
        )

        singular_values = np.asarray(
            result["singular_values"],
            dtype="float64",
        )

        sigma_max = float(
            singular_values[0]
        )

        expected_tol = (
            max(5, 3)
            * np.finfo(np.float64).eps
            * sigma_max
        )

        self.assertAlmostEqual(
            result["rank_tolerance"],
            expected_tol,
            places=20,
        )




# STEP_13D2_GROUP_RANK_AND_PHASE_C_SPEC_V1

class StageBGroupRankAndPhaseCSensitivitySpecificationTests(
    unittest.TestCase
):
    def test_generic_c_equals_a_plus_b_opens_entire_component(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        frame = pd.DataFrame(
            {
                "a": [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0],
                "b": [2.0, -1.0, 4.0, 0.5, -3.0, 1.5, 5.0, -2.0],
            },
            dtype="float64",
        )
        frame["c"] = frame["a"] + frame["b"]

        diagnostics = analyzer.compute_svd_diagnostics(
            analyzer.build_standardized_matrix(
                frame=frame,
                feature_columns=["a", "b", "c"],
            )
        )
        self.assertEqual(diagnostics["deficiency"], 1)

        result = analyzer.classify_generic_rank_discovery(
            component_features=["a", "b", "c"],
            discovery_status=(
                "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY"
            ),
        )

        self.assertEqual(result["decision_class"], "OPEN")
        self.assertEqual(
            result["component_dispositions"],
            {"a": "OPEN", "b": "OPEN", "c": "OPEN"},
        )
        self.assertEqual(result["dropped_features"], ())
        self.assertFalse(result["direct_drop_authorized"])
        self.assertFalse(result["environment_change_resolves_open"])
        self.assertFalse(result["stage_c_release_allowed"])

    def test_cohort_conditional_localized_dependency_opens_component(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        result = analyzer.classify_generic_rank_discovery(
            component_features=["a", "b", "c"],
            discovery_status=(
                "COHORT_CONDITIONAL_LOCALIZED_EXACT_DEPENDENCY"
            ),
        )

        self.assertEqual(result["decision_class"], "OPEN")
        self.assertEqual(
            set(result["component_dispositions"].values()),
            {"OPEN"},
        )
        self.assertFalse(result["stage_c_release_allowed"])

    def test_inconsistent_generic_evidence_hard_fails_without_drop(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        statuses = (
            "UNSTABLE_EXACT_DEPENDENCY",
            "UNLOCALIZABLE_EXACT_DEPENDENCY",
            "TOLERANCE_INCONSISTENT_EXACT_DEPENDENCY",
            "NUMERICALLY_INCONSISTENT_EXACT_DEPENDENCY",
        )

        for status in statuses:
            with self.subTest(status=status):
                result = analyzer.classify_generic_rank_discovery(
                    component_features=["a", "b", "c"],
                    discovery_status=status,
                )
                self.assertEqual(result["decision_class"], "HARD_FAIL")
                self.assertEqual(result["dropped_features"], ())
                self.assertNotIn("base_decision", result)
                self.assertFalse(result["direct_drop_authorized"])
                self.assertFalse(result["stage_c_release_allowed"])

    def test_old_generic_drop_resolver_is_retired(self) -> None:
        from mes_quant.redundancy import analyzer

        self.assertFalse(
            hasattr(analyzer, "resolve_generic_group_rank_verification")
        )
        for retired_helper in (
            "_prefer_retention_candidate",
            "_minimum_fold_availability",
            "_compare_lookback_preference",
        ):
            self.assertFalse(hasattr(analyzer, retired_helper))

    def test_environment_change_cannot_be_enabled_as_open_resolution(
        self,
    ) -> None:
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer, contract

        with (
            patch.object(
                contract,
                "GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN",
                True,
            ),
            self.assertRaisesRegex(
                RuntimeError,
                "Environment change must not resolve generic rank OPEN",
            ),
        ):
            analyzer.classify_generic_rank_discovery(
                component_features=["a", "b", "c"],
                discovery_status=(
                    "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY"
                ),
            )

    def test_generic_direct_drop_authority_fails_closed_if_enabled(
        self,
    ) -> None:
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer, contract

        with (
            patch.object(
                contract,
                "GENERIC_RANK_DIRECT_DROP_AUTHORIZED",
                True,
            ),
            self.assertRaisesRegex(
                RuntimeError,
                "direct DROP authority must remain disabled",
            ),
        ):
            analyzer.classify_generic_rank_discovery(
                component_features=["a", "b", "c"],
                discovery_status=(
                    "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY"
                ),
            )

    def test_primary_hard_plus_sensitivity_hard_is_supported(self) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "classify_cohort_sensitivity",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer.classify_cohort_sensitivity must exist",
        )

        result = classify(
            primary_hard_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            pairwise_stats_by_fold={
                "role_wf_2022": {
                    "pairwise_available_rows": 100,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.97,
                    "spearman": 0.96,
                },
                "role_wf_2023": {
                    "pairwise_available_rows": 120,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.98,
                    "spearman": 0.97,
                },
                "role_wf_2024": {
                    "pairwise_available_rows": 140,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.96,
                    "spearman": 0.95,
                },
            },
        )

        self.assertEqual(
            result["cohort_sensitivity_status"],
            "COHORT_SENSITIVITY_SUPPORTED",
        )

        self.assertTrue(
            result["empirical_drop_eligible"]
        )

    def test_primary_hard_with_sensitivity_failure_is_conflict(self) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "classify_cohort_sensitivity",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer.classify_cohort_sensitivity must exist",
        )

        result = classify(
            primary_hard_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
            pairwise_stats_by_fold={
                "role_wf_2022": {
                    "pairwise_available_rows": 100,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.97,
                    "spearman": 0.97,
                },
                "role_wf_2023": {
                    "pairwise_available_rows": 100,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.96,
                    "spearman": 0.94,
                },
                "role_wf_2024": {
                    "pairwise_available_rows": 100,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.98,
                    "spearman": 0.98,
                },
            },
        )

        self.assertEqual(
            result["cohort_sensitivity_status"],
            "COHORT_SENSITIVITY_CONFLICT",
        )

        self.assertFalse(
            result["empirical_drop_eligible"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertEqual(
            result["decision_basis"],
            "EMPIRICAL_DROP_VETOED_COHORT_SENSITIVITY",
        )

    def test_sensitivity_unavailable_is_machine_detected(self) -> None:
        import math

        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "classify_cohort_sensitivity",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer.classify_cohort_sensitivity must exist",
        )

        base = {
            "pairwise_available_rows": 100,
            "feature_a_zero_variance": False,
            "feature_b_zero_variance": False,
            "pearson": 0.99,
            "spearman": 0.99,
        }

        mutations = [
            {
                "pairwise_available_rows": 1,
            },
            {
                "feature_a_zero_variance": True,
            },
            {
                "feature_b_zero_variance": True,
            },
            {
                "pearson": math.nan,
            },
            {
                "spearman": math.nan,
            },
        ]

        for mutation in mutations:
            with self.subTest(
                mutation=mutation
            ):
                stats = {
                    fold: dict(
                        base,
                        **mutation,
                    )
                    for fold in [
                        "role_wf_2022",
                        "role_wf_2023",
                        "role_wf_2024",
                    ]
                }

                result = classify(
                    primary_hard_by_fold={
                        "role_wf_2022": True,
                        "role_wf_2023": True,
                        "role_wf_2024": True,
                    },
                    pairwise_stats_by_fold=stats,
                )

                self.assertEqual(
                    result["cohort_sensitivity_status"],
                    "COHORT_SENSITIVITY_UNAVAILABLE",
                )

                self.assertFalse(
                    result["empirical_drop_eligible"]
                )

                self.assertEqual(
                    result["base_decision"],
                    "KEEP",
                )

    def test_sensitivity_alone_cannot_create_empirical_drop(self) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "classify_cohort_sensitivity",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer.classify_cohort_sensitivity must exist",
        )

        result = classify(
            primary_hard_by_fold={
                "role_wf_2022": True,
                "role_wf_2023": False,
                "role_wf_2024": True,
            },
            pairwise_stats_by_fold={
                fold: {
                    "pairwise_available_rows": 100,
                    "feature_a_zero_variance": False,
                    "feature_b_zero_variance": False,
                    "pearson": 0.99,
                    "spearman": 0.99,
                }
                for fold in [
                    "role_wf_2022",
                    "role_wf_2023",
                    "role_wf_2024",
                ]
            },
        )

        self.assertFalse(
            result["empirical_drop_eligible"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

    def test_protected_candidate_cannot_be_phase_c_drop_target(self) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "resolve_phase_c_direct_substitute",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer.resolve_phase_c_direct_substitute must exist",
        )

        result = resolve(
            candidate="protected_a",
            retained_features=["retained_b"],
            protected_features={"protected_a"},
            pair_status_by_retained={
                "retained_b": "COHORT_SENSITIVITY_SUPPORTED",
            },
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertIsNone(
            result["direct_substitute"]
        )

    def test_protected_retained_feature_may_directly_substitute_candidate(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "resolve_phase_c_direct_substitute",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer.resolve_phase_c_direct_substitute must exist",
        )

        result = resolve(
            candidate="bar_body",
            retained_features=[
                "ret_log_15m_lag0",
            ],
            protected_features={
                "ret_log_15m_lag0",
            },
            pair_status_by_retained={
                "ret_log_15m_lag0": (
                    "COHORT_SENSITIVITY_SUPPORTED"
                ),
            },
        )

        self.assertEqual(
            result["base_decision"],
            "DROP_REDUNDANT",
        )

        self.assertEqual(
            result["direct_substitute"],
            "ret_log_15m_lag0",
        )

    def test_nonretained_transitive_feature_cannot_create_substitution(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "resolve_phase_c_direct_substitute",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer.resolve_phase_c_direct_substitute must exist",
        )

        # A is retained.
        #
        # B is NOT retained but has a supported relation to C.
        # That cannot be used to infer that retained A substitutes C.
        result = resolve(
            candidate="feature_c",
            retained_features=[
                "feature_a",
            ],
            protected_features=set(),
            pair_status_by_retained={
                "feature_a": "DISTINCT",
                "feature_b": (
                    "COHORT_SENSITIVITY_SUPPORTED"
                ),
            },
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertIsNone(
            result["direct_substitute"]
        )




# STEP_13E1_PHASE0_FIREWALL_SPEC_V1

class StageBPhase0FirewallSpecificationTests(
    unittest.TestCase
):
    @staticmethod
    def _registry_rows():
        rows = []

        for i in range(29):
            rows.append(
                {
                    "feature": f"feature_{i:02d}",
                    "lookback_mode": "FIXED",
                    "lookback_bars": 1,
                    "lookback_minutes": 15,
                    "lookback_start_rule": None,
                }
            )

        # Canonical zero-lookback semantics are valid.
        rows[0] = {
            "feature": "ret_log_15m_lag0",
            "lookback_mode": "FIXED",
            "lookback_bars": 0,
            "lookback_minutes": 0,
            "lookback_start_rule": None,
        }

        # Exercise the only other allowed V1.1 mode.
        rows[1] = {
            "feature": "session_vwap_proxy_deviation",
            "lookback_mode": "SESSION_TO_DATE",
            "lookback_bars": 22,
            "lookback_minutes": 330,
            "lookback_start_rule": "NYSE_SESSION_START",
        }

        return rows

    def test_markdown_raw_byte_hash_mismatch_fails(self) -> None:
        import hashlib

        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_control_binding",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_control_binding must exist",
        )

        markdown = b"locked markdown bytes\r\n"
        registry = b'{"locked":true}\n'

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                markdown_bytes=markdown + b"DRIFT",
                semantic_registry_bytes=registry,
                expected_markdown_sha256=hashlib.sha256(
                    markdown
                ).hexdigest(),
                expected_registry_sha256=hashlib.sha256(
                    registry
                ).hexdigest(),
                python_policy_version=contract.POLICY_VERSION,
                python_policy_status="LOCKED_EXECUTABLE",
                markdown_policy_version=contract.POLICY_VERSION,
                markdown_policy_status="LOCKED_EXECUTABLE",
                registry_policy_version=contract.POLICY_VERSION,
                registry_status="LOCKED_EXECUTABLE",
                registry_source_contract=(
                    "docs/STAGE_B_REDUNDANCY_CONTRACT.md"
                ),
            )

    def test_semantic_registry_raw_byte_hash_mismatch_fails(self) -> None:
        import hashlib

        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_control_binding",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_control_binding must exist",
        )

        markdown = b"locked markdown bytes\r\n"
        registry = b'{"locked":true}\n'

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                markdown_bytes=markdown,
                semantic_registry_bytes=registry + b"DRIFT",
                expected_markdown_sha256=hashlib.sha256(
                    markdown
                ).hexdigest(),
                expected_registry_sha256=hashlib.sha256(
                    registry
                ).hexdigest(),
                python_policy_version=contract.POLICY_VERSION,
                python_policy_status="LOCKED_EXECUTABLE",
                markdown_policy_version=contract.POLICY_VERSION,
                markdown_policy_status="LOCKED_EXECUTABLE",
                registry_policy_version=contract.POLICY_VERSION,
                registry_status="LOCKED_EXECUTABLE",
                registry_source_contract=(
                    "docs/STAGE_B_REDUNDANCY_CONTRACT.md"
                ),
            )

    def test_policy_version_and_status_mismatches_fail_closed(self) -> None:
        import hashlib

        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_control_binding",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_control_binding must exist",
        )

        markdown = b"markdown"
        registry = b"registry"

        base = {
            "markdown_bytes": markdown,
            "semantic_registry_bytes": registry,
            "expected_markdown_sha256": hashlib.sha256(
                markdown
            ).hexdigest(),
            "expected_registry_sha256": hashlib.sha256(
                registry
            ).hexdigest(),
            "python_policy_version": contract.POLICY_VERSION,
            "python_policy_status": "LOCKED_EXECUTABLE",
            "markdown_policy_version": contract.POLICY_VERSION,
            "markdown_policy_status": "LOCKED_EXECUTABLE",
            "registry_policy_version": contract.POLICY_VERSION,
            "registry_status": "LOCKED_EXECUTABLE",
            "registry_source_contract": (
                "docs/STAGE_B_REDUNDANCY_CONTRACT.md"
            ),
        }

        mutations = [
            {
                "python_policy_version": "MES_V1_REDUNDANCY_BAD",
            },
            {
                "python_policy_status": "PROVISIONAL",
            },
            {
                "markdown_policy_status": "PROVISIONAL",
            },
            {
                "registry_status": "PROVISIONAL",
            },
            {
                "registry_policy_version": "MES_V1_REDUNDANCY_BAD",
            },
            {
                "registry_source_contract": "wrong.md",
            },
        ]

        for mutation in mutations:
            with self.subTest(
                mutation=mutation
            ):
                args = dict(base)
                args.update(mutation)

                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    validate(**args)

    def test_exactly_29_membership_and_order_are_enforced(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_canonical_feature_registry",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_canonical_feature_registry must exist",
        )

        registry = self._registry_rows()

        canonical_order = [
            row["feature"]
            for row in registry
        ]

        result = validate(
            registry_rows=registry,
            artifact_feature_order=canonical_order,
        )

        self.assertEqual(
            result["candidate_count"],
            29,
        )

        bad_order = list(
            canonical_order
        )

        bad_order[2], bad_order[3] = (
            bad_order[3],
            bad_order[2],
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                registry_rows=registry,
                artifact_feature_order=bad_order,
            )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                registry_rows=registry[:-1],
                artifact_feature_order=canonical_order[:-1],
            )

    def test_prototype_alias_is_rejected_by_exact_membership(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_canonical_feature_registry",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_canonical_feature_registry must exist",
        )

        registry = self._registry_rows()

        artifact_order = [
            row["feature"]
            for row in registry
        ]

        artifact_order[0] = "log_return_lag_0"

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                registry_rows=registry,
                artifact_feature_order=artifact_order,
            )

    def test_canonical_zero_lookback_metadata_is_valid(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_canonical_feature_registry",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_canonical_feature_registry must exist",
        )

        registry = self._registry_rows()

        result = validate(
            registry_rows=registry,
            artifact_feature_order=[
                row["feature"]
                for row in registry
            ],
        )

        self.assertTrue(
            result["lookback_metadata_valid"]
        )

    def test_missing_required_lookback_metadata_fails(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_canonical_feature_registry",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_canonical_feature_registry must exist",
        )

        registry = self._registry_rows()

        del registry[5][
            "lookback_minutes"
        ]

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                registry_rows=registry,
                artifact_feature_order=[
                    row["feature"]
                    for row in registry
                ],
            )

    def test_forbidden_fields_cells_and_final_test_are_rejected(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_forbidden_inputs",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_forbidden_inputs must exist",
        )

        clean = validate(
            opened_fields=[
                "ts_event",
                "ret_log_15m_lag0",
                "weekday_0",
            ],
            opened_cells=[8, 14],
            final_test_rows_opened=0,
        )

        self.assertEqual(
            clean["final_test_rows_opened"],
            0,
        )

        for field in [
            "label",
            "future_return_60m",
            "future_price",
            "gross_pnl",
            "net_pnl",
            "execution_outcome",
        ]:
            with self.subTest(
                field=field
            ):
                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    validate(
                        opened_fields=[field],
                        opened_cells=[8, 14],
                        final_test_rows_opened=0,
                    )

        for cell in [9, 10, 11, 12, 13]:
            with self.subTest(
                cell=cell
            ):
                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    validate(
                        opened_fields=["ts_event"],
                        opened_cells=[8, 14, cell],
                        final_test_rows_opened=0,
                    )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                opened_fields=["ts_event"],
                opened_cells=[8, 14],
                final_test_rows_opened=1,
            )

    def test_exact_three_folds_and_90_percent_floor_are_enforced(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_fold_coverage",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_fold_coverage must exist",
        )

        result = validate(
            fold_complete_rows={
                "role_wf_2022": 95,
                "role_wf_2023": 96,
                "role_wf_2024": 97,
            },
            fold_train_rows={
                "role_wf_2022": 100,
                "role_wf_2023": 100,
                "role_wf_2024": 100,
            },
            yearly_coverage={
                2019: 0.95,
                2020: 0.96,
                2021: 0.97,
                2022: 0.98,
                2023: 0.99,
                2024: 1.00,
            },
            yearly_review_acknowledged=False,
        )

        self.assertTrue(
            result["fold_coverage_gate_pass"]
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                fold_complete_rows={
                    "role_wf_2022": 89,
                    "role_wf_2023": 96,
                    "role_wf_2024": 97,
                },
                fold_train_rows={
                    "role_wf_2022": 100,
                    "role_wf_2023": 100,
                    "role_wf_2024": 100,
                },
                yearly_coverage={
                    2019: 0.95,
                },
                yearly_review_acknowledged=False,
            )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                fold_complete_rows={
                    "role_wf_2022": 95,
                    "role_wf_2023": 96,
                },
                fold_train_rows={
                    "role_wf_2022": 100,
                    "role_wf_2023": 100,
                },
                yearly_coverage={
                    2019: 0.95,
                },
                yearly_review_acknowledged=False,
            )

    def test_yearly_below_90_requires_review_acknowledgment(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_fold_coverage",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_fold_coverage must exist",
        )

        kwargs = {
            "fold_complete_rows": {
                "role_wf_2022": 95,
                "role_wf_2023": 96,
                "role_wf_2024": 97,
            },
            "fold_train_rows": {
                "role_wf_2022": 100,
                "role_wf_2023": 100,
                "role_wf_2024": 100,
            },
            "yearly_coverage": {
                2019: 0.81,
                2020: 0.96,
                2021: 0.98,
            },
        }

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                **kwargs,
                yearly_review_acknowledged=False,
            )

        result = validate(
            **kwargs,
            yearly_review_acknowledged=True,
        )

        self.assertTrue(
            result[
                "YEARLY_CONCENTRATION_REVIEW_REQUIRED"
            ]
        )

        self.assertEqual(
            result[
                "YEARLY_CONCENTRATION_REVIEW_STATUS"
            ],
            "ACKNOWLEDGED",
        )

    def test_pair_orientation_follows_canonical_registry_order(self) -> None:
        from mes_quant.redundancy import analyzer

        orient = getattr(
            analyzer,
            "_canonical_orient_pair",
            None,
        )

        self.assertTrue(
            callable(orient),
            "analyzer._canonical_orient_pair must exist",
        )

        canonical = [
            "feature_a",
            "feature_b",
            "feature_c",
        ]

        self.assertEqual(
            orient(
                feature_x="feature_c",
                feature_y="feature_a",
                canonical_order=canonical,
            ),
            (
                "feature_a",
                "feature_c",
            ),
        )

        self.assertEqual(
            orient(
                feature_x="feature_a",
                feature_y="feature_c",
                canonical_order=canonical,
            ),
            (
                "feature_a",
                "feature_c",
            ),
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            orient(
                feature_x="unknown_feature",
                feature_y="feature_a",
                canonical_order=canonical,
            )




# STEP_13E2_RETENTION_AND_DECISION_REGISTRY_SPEC_V1

class StageBRetentionAndDecisionRegistrySpecificationTests(
    unittest.TestCase
):
    def test_generic_retention_candidate_authority_is_retired(self) -> None:
        from mes_quant.redundancy import analyzer

        self.assertFalse(
            hasattr(analyzer, "_prefer_retention_candidate")
        )

    def test_relationship_id_serialization_is_deterministic(self) -> None:
        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_relationship_ids",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_relationship_ids must exist",
        )

        ordered_universe = [
            "GROUP_A",
            "GROUP_B",
            "GROUP_C",
        ]

        self.assertEqual(
            serialize(
                identifiers=[
                    "GROUP_C",
                    "GROUP_A",
                ],
                ordered_universe=ordered_universe,
            ),
            "GROUP_A|GROUP_C",
        )

        self.assertEqual(
            serialize(
                identifiers=[],
                ordered_universe=ordered_universe,
            ),
            "",
        )

        for identifiers in [
            ["GROUP_A", "GROUP_A"],
            ["UNKNOWN"],
            ["INVALID|GROUP"],
        ]:
            with self.subTest(
                identifiers=identifiers
            ):
                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    serialize(
                        identifiers=identifiers,
                        ordered_universe=ordered_universe,
                    )

    def test_feature_decision_registry_requires_locked_schema(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_feature_decision_registry_row",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_feature_decision_registry_row must exist",
        )

        row = {
            "feature": "feature_a",
            "base_decision": "KEEP",
            "decision_basis": "NO_LOCKED_DROP_RULE",
            "semantic_dependency_groups": "",
            "exact_set_dependency_groups": "",
            "empirical_pair_ids": "",
            "semantic_basis_protected": False,
            "chosen_representative_or_basis": "feature_a",
            "direct_substitute": None,
            "group_cohort_rank_status": None,
            "cohort_sensitivity_status": None,
            "linear_overlay_decision": "KEEP",
            "tree_overlay_decision": "KEEP",
            "reason": "Retained by locked target-blind procedure.",
        }

        result = validate(
            row=row,
        )

        self.assertTrue(
            result["decision_registry_row_valid"]
        )

        # required_drop_count must NOT be required
        # as a feature-level scalar.
        self.assertNotIn(
            "required_drop_count",
            result["required_fields"],
        )

        for bad_state in [
            "DROP",
            "REVIEW",
            "UNKNOWN",
        ]:
            with self.subTest(
                bad_state=bad_state
            ):
                bad = dict(row)
                bad[
                    "base_decision"
                ] = bad_state

                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    validate(
                        row=bad,
                    )

    def test_feature_decision_registry_rejects_bad_multi_id_strings(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_feature_decision_registry_row",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_feature_decision_registry_row must exist",
        )

        base = {
            "feature": "feature_a",
            "base_decision": "KEEP",
            "decision_basis": "NO_LOCKED_DROP_RULE",
            "semantic_dependency_groups": "",
            "exact_set_dependency_groups": "",
            "empirical_pair_ids": "",
            "semantic_basis_protected": False,
            "chosen_representative_or_basis": "feature_a",
            "direct_substitute": None,
            "group_cohort_rank_status": None,
            "cohort_sensitivity_status": None,
            "linear_overlay_decision": "KEEP",
            "tree_overlay_decision": "KEEP",
            "reason": "Target-blind retention.",
        }

        for value in [
            "|GROUP_A",
            "GROUP_A|",
            "GROUP_A||GROUP_B",
            "GROUP_A|GROUP_A",
        ]:
            with self.subTest(
                value=value
            ):
                row = dict(
                    base
                )

                row[
                    "semantic_dependency_groups"
                ] = value

                with self.assertRaises(
                    (ValueError, RuntimeError)
                ):
                    validate(
                        row=row,
                    )

    def test_generic_exact_set_rows_cannot_encode_keep_drop_or_basis(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        generic_open = {
            "feature": "feature_a",
            "base_decision": "OPEN",
            "decision_basis": (
                "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY"
            ),
            "semantic_dependency_groups": "",
            "exact_set_dependency_groups": "GENERIC_COMPONENT_1",
            "empirical_pair_ids": "",
            "semantic_basis_protected": False,
            "chosen_representative_or_basis": None,
            "direct_substitute": None,
            "group_cohort_rank_status": (
                "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY"
            ),
            "cohort_sensitivity_status": None,
            "linear_overlay_decision": "BLOCKED_BY_OPEN",
            "tree_overlay_decision": "BLOCKED_BY_OPEN",
            "reason": "Generic rank discovery opened the whole component.",
        }

        result = analyzer._validate_feature_decision_registry_row(
            row=generic_open,
        )
        self.assertTrue(result["decision_registry_row_valid"])

        for forbidden_decision in ("KEEP", "DROP_REDUNDANT"):
            with self.subTest(base_decision=forbidden_decision):
                row = dict(generic_open)
                row["base_decision"] = forbidden_decision
                with self.assertRaisesRegex(
                    RuntimeError,
                    "direct KEEP/DROP is forbidden",
                ):
                    analyzer._validate_feature_decision_registry_row(
                        row=row,
                    )

        for forbidden_field in (
            "chosen_representative_or_basis",
            "direct_substitute",
        ):
            with self.subTest(field=forbidden_field):
                row = dict(generic_open)
                row[forbidden_field] = "feature_b"
                with self.assertRaisesRegex(
                    RuntimeError,
                    forbidden_field,
                ):
                    analyzer._validate_feature_decision_registry_row(
                        row=row,
                    )

    def test_stage_c_is_blocked_by_open_decisions(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_c_readiness",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_c_readiness must exist",
        )

        decisions = [
            {
                "feature": "a",
                "base_decision": "KEEP",
            },
            {
                "feature": "b",
                "base_decision": "OPEN",
            },
        ]

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                decision_rows=decisions,
                yearly_review_required=False,
                yearly_review_status="NOT_REQUIRED",
                phase_c_rank_loss_review_required=False,
                phase_c_rank_loss_review_status="NOT_REQUIRED",
            )

    def test_cohort_conditional_generic_component_blocks_stage_c(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_c_readiness",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_c_readiness must exist",
        )

        disposition = analyzer.classify_generic_rank_discovery(
            component_features=["a", "b"],
            discovery_status=(
                "COHORT_CONDITIONAL_LOCALIZED_EXACT_DEPENDENCY"
            ),
        )
        decisions = [
            {
                "feature": feature,
                "base_decision": decision,
            }
            for feature, decision in disposition[
                "component_dispositions"
            ].items()
        ]

        with self.assertRaises((ValueError, RuntimeError)):
            validate(
                decision_rows=decisions,
                yearly_review_required=False,
                yearly_review_status="NOT_REQUIRED",
                phase_c_rank_loss_review_required=False,
                phase_c_rank_loss_review_status="NOT_REQUIRED",
            )

    def test_generic_exact_set_drop_cannot_pass_stage_c_readiness(self) -> None:
        from mes_quant.redundancy import analyzer

        with self.assertRaisesRegex(
            RuntimeError,
            "forbidden generic Phase-B direct KEEP/DROP state",
        ):
            analyzer._validate_stage_c_readiness(
                decision_rows=[
                    {
                        "feature": "c",
                        "base_decision": "DROP_REDUNDANT",
                        "exact_set_dependency_groups": "GENERIC_COMPONENT_1",
                    },
                ],
                yearly_review_required=False,
                yearly_review_status="NOT_REQUIRED",
                phase_c_rank_loss_review_required=False,
                phase_c_rank_loss_review_status="NOT_REQUIRED",
            )

    def test_required_target_blind_acknowledgments_gate_stage_c(self) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_c_readiness",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_c_readiness must exist",
        )

        decisions = [
            {
                "feature": "a",
                "base_decision": "KEEP",
            },
        ]

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                decision_rows=decisions,
                yearly_review_required=True,
                yearly_review_status="PENDING",
                phase_c_rank_loss_review_required=False,
                phase_c_rank_loss_review_status="NOT_REQUIRED",
            )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                decision_rows=decisions,
                yearly_review_required=False,
                yearly_review_status="NOT_REQUIRED",
                phase_c_rank_loss_review_required=True,
                phase_c_rank_loss_review_status="PENDING",
            )

        result = validate(
            decision_rows=decisions,
            yearly_review_required=True,
            yearly_review_status="ACKNOWLEDGED",
            phase_c_rank_loss_review_required=True,
            phase_c_rank_loss_review_status="ACKNOWLEDGED",
        )

        self.assertTrue(
            result["stage_c_ready"]
        )




# STEP_13F1_PRIMARY_EMPIRICAL_SPEC_V1

class StageBPrimaryEmpiricalSpecificationTests(
    unittest.TestCase
):
    @staticmethod
    def _stats(
        pearson,
        spearman,
        rows=100,
    ):
        return {
            "pairwise_available_rows": rows,
            "feature_a_zero_variance": False,
            "feature_b_zero_variance": False,
            "pearson": pearson,
            "spearman": spearman,
        }

    def test_empirical_pair_stats_compute_complete_case_correlations(
        self,
    ) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "_compute_empirical_pair_stats",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer._compute_empirical_pair_stats must exist",
        )

        frame = pd.DataFrame(
            {
                "feature_a": [
                    1.0,
                    2.0,
                    3.0,
                    4.0,
                    5.0,
                ],
                "feature_b": [
                    10.0,
                    20.0,
                    30.0,
                    40.0,
                    50.0,
                ],
            }
        )

        result = compute(
            frame=frame,
            feature_a="feature_a",
            feature_b="feature_b",
        )

        self.assertEqual(
            result["pairwise_available_rows"],
            5,
        )

        self.assertFalse(
            result["feature_a_zero_variance"]
        )

        self.assertFalse(
            result["feature_b_zero_variance"]
        )

        self.assertAlmostEqual(
            result["pearson"],
            1.0,
            places=12,
        )

        self.assertAlmostEqual(
            result["spearman"],
            1.0,
            places=12,
        )

    def test_empirical_pair_stats_use_only_pair_complete_rows(
        self,
    ) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "_compute_empirical_pair_stats",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer._compute_empirical_pair_stats must exist",
        )

        frame = pd.DataFrame(
            {
                "feature_a": [
                    1.0,
                    2.0,
                    None,
                    4.0,
                ],
                "feature_b": [
                    2.0,
                    4.0,
                    6.0,
                    None,
                ],
            }
        )

        result = compute(
            frame=frame,
            feature_a="feature_a",
            feature_b="feature_b",
        )

        self.assertEqual(
            result["pairwise_available_rows"],
            2,
        )

        self.assertAlmostEqual(
            result["pearson"],
            1.0,
            places=12,
        )

        self.assertAlmostEqual(
            result["spearman"],
            1.0,
            places=12,
        )

    def test_primary_hard_requires_both_metrics_in_every_fold(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_primary_empirical_pair",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_primary_empirical_pair must exist",
        )

        stats = {
            "role_wf_2022": self._stats(
                0.97,
                0.97,
            ),
            "role_wf_2023": self._stats(
                0.98,
                0.94,
            ),
            "role_wf_2024": self._stats(
                0.96,
                0.96,
            ),
        }

        result = classify(
            stats_by_fold=stats,
        )

        self.assertEqual(
            result["primary_classification"],
            "REVIEW",
        )

        self.assertFalse(
            result["primary_hard_all_folds"]
        )

        self.assertFalse(
            result["empirical_drop_eligible"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

    def test_primary_hard_uses_absolute_correlation(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_primary_empirical_pair",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_primary_empirical_pair must exist",
        )

        stats = {
            "role_wf_2022": self._stats(
                -0.97,
                -0.96,
            ),
            "role_wf_2023": self._stats(
                -0.98,
                -0.97,
            ),
            "role_wf_2024": self._stats(
                -0.96,
                -0.95,
            ),
        }

        result = classify(
            stats_by_fold=stats,
        )

        self.assertEqual(
            result["primary_classification"],
            "HARD",
        )

        self.assertTrue(
            result["primary_hard_all_folds"]
        )

        self.assertEqual(
            result["primary_hard_by_fold"],
            {
                "role_wf_2022": True,
                "role_wf_2023": True,
                "role_wf_2024": True,
            },
        )

        # Primary HARD alone is not sufficient to DROP.
        self.assertFalse(
            result["empirical_drop_eligible"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertEqual(
            result["decision_basis"],
            "PRIMARY_HARD_REQUIRES_PAIRWISE_SENSITIVITY",
        )

    def test_primary_review_uses_either_metric_on_any_fold(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_primary_empirical_pair",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_primary_empirical_pair must exist",
        )

        stats = {
            "role_wf_2022": self._stats(
                0.40,
                0.40,
            ),
            "role_wf_2023": self._stats(
                0.91,
                0.50,
            ),
            "role_wf_2024": self._stats(
                0.30,
                0.30,
            ),
        }

        result = classify(
            stats_by_fold=stats,
        )

        self.assertEqual(
            result["primary_classification"],
            "REVIEW",
        )

        self.assertFalse(
            result["primary_hard_all_folds"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

    def test_primary_distinct_when_all_metrics_below_review_threshold(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_primary_empirical_pair",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_primary_empirical_pair must exist",
        )

        stats = {
            "role_wf_2022": self._stats(
                0.89,
                0.88,
            ),
            "role_wf_2023": self._stats(
                0.50,
                0.60,
            ),
            "role_wf_2024": self._stats(
                -0.89,
                -0.89,
            ),
        }

        result = classify(
            stats_by_fold=stats,
        )

        self.assertEqual(
            result["primary_classification"],
            "DISTINCT",
        )

        self.assertFalse(
            result["primary_hard_all_folds"]
        )

        self.assertFalse(
            result["empirical_drop_eligible"]
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

    def test_hard_and_review_threshold_boundaries_are_inclusive(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_primary_empirical_pair",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_primary_empirical_pair must exist",
        )

        hard_stats = {
            fold: self._stats(
                0.95,
                -0.95,
            )
            for fold in [
                "role_wf_2022",
                "role_wf_2023",
                "role_wf_2024",
            ]
        }

        hard = classify(
            stats_by_fold=hard_stats,
        )

        self.assertEqual(
            hard["primary_classification"],
            "HARD",
        )

        review_stats = {
            "role_wf_2022": self._stats(
                0.90,
                0.20,
            ),
            "role_wf_2023": self._stats(
                0.20,
                0.20,
            ),
            "role_wf_2024": self._stats(
                0.20,
                0.20,
            ),
        }

        review = classify(
            stats_by_fold=review_stats,
        )

        self.assertEqual(
            review["primary_classification"],
            "REVIEW",
        )




# STEP_13F2_SPEARMAN_COMPLETE_LINKAGE_CLUSTERING_SPEC_V1

class StageBSpearmanCompleteLinkageClusteringSpecificationTests(
    unittest.TestCase
):
    def test_spearman_distance_is_one_minus_absolute_rho(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "_spearman_distance_matrix",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer._spearman_distance_matrix must exist",
        )

        corr = pd.DataFrame(
            [
                [1.00, 0.95, -0.80],
                [0.95, 1.00, -0.50],
                [-0.80, -0.50, 1.00],
            ],
            index=["a", "b", "c"],
            columns=["a", "b", "c"],
        )

        distance = compute(
            spearman_correlation=corr,
            canonical_order=["a", "b", "c"],
        )

        self.assertAlmostEqual(
            float(distance.loc["a", "b"]),
            0.05,
            places=12,
        )

        self.assertAlmostEqual(
            float(distance.loc["a", "c"]),
            0.20,
            places=12,
        )

        self.assertAlmostEqual(
            float(distance.loc["a", "a"]),
            0.0,
            places=12,
        )

    def test_perfect_negative_spearman_has_zero_distance(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "_spearman_distance_matrix",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer._spearman_distance_matrix must exist",
        )

        corr = pd.DataFrame(
            [
                [1.0, -1.0],
                [-1.0, 1.0],
            ],
            index=["a", "b"],
            columns=["a", "b"],
        )

        distance = compute(
            spearman_correlation=corr,
            canonical_order=["a", "b"],
        )

        self.assertAlmostEqual(
            float(distance.loc["a", "b"]),
            0.0,
            places=12,
        )

    def test_complete_linkage_prevents_transitive_chain_merge(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        cluster = getattr(
            analyzer,
            "_complete_linkage_clusters",
            None,
        )

        self.assertTrue(
            callable(cluster),
            "analyzer._complete_linkage_clusters must exist",
        )

        # A-B = 0.05
        # B-C = 0.05
        # A-C = 0.20
        #
        # Single linkage could chain A-B-C together.
        # Complete linkage must NOT because the maximum
        # distance inside A-B-C would exceed 0.10.
        distance = pd.DataFrame(
            [
                [0.00, 0.05, 0.20],
                [0.05, 0.00, 0.05],
                [0.20, 0.05, 0.00],
            ],
            index=["a", "b", "c"],
            columns=["a", "b", "c"],
        )

        result = cluster(
            distance_matrix=distance,
            canonical_order=["a", "b", "c"],
            cut_distance=0.10,
        )

        self.assertEqual(
            result,
            (
                ("a", "b"),
                ("c",),
            ),
        )

    def test_complete_linkage_cut_boundary_is_inclusive(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        cluster = getattr(
            analyzer,
            "_complete_linkage_clusters",
            None,
        )

        self.assertTrue(
            callable(cluster),
            "analyzer._complete_linkage_clusters must exist",
        )

        distance = pd.DataFrame(
            [
                [0.00, 0.10],
                [0.10, 0.00],
            ],
            index=["a", "b"],
            columns=["a", "b"],
        )

        result = cluster(
            distance_matrix=distance,
            canonical_order=["a", "b"],
            cut_distance=0.10,
        )

        self.assertEqual(
            result,
            (
                ("a", "b"),
            ),
        )

    def test_cluster_output_is_deterministic_in_canonical_order(self) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        cluster = getattr(
            analyzer,
            "_complete_linkage_clusters",
            None,
        )

        self.assertTrue(
            callable(cluster),
            "analyzer._complete_linkage_clusters must exist",
        )

        canonical = [
            "feature_a",
            "feature_b",
            "feature_c",
            "feature_d",
        ]

        distance = pd.DataFrame(
            [
                [0.00, 0.04, 0.80, 0.80],
                [0.04, 0.00, 0.80, 0.80],
                [0.80, 0.80, 0.00, 0.03],
                [0.80, 0.80, 0.03, 0.00],
            ],
            index=canonical,
            columns=canonical,
        )

        result = cluster(
            distance_matrix=distance,
            canonical_order=canonical,
            cut_distance=0.10,
        )

        self.assertEqual(
            result,
            (
                ("feature_a", "feature_b"),
                ("feature_c", "feature_d"),
            ),
        )

    def test_cluster_evidence_is_review_only_and_never_auto_drop(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_cluster_review_evidence",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_cluster_review_evidence must exist",
        )

        result = classify(
            cluster_members=(
                "feature_a",
                "feature_b",
                "feature_c",
            ),
        )

        self.assertTrue(
            result["review_required"]
        )

        self.assertEqual(
            result["classification"],
            "CLUSTER_REVIEW",
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertFalse(
            result["drop_allowed"]
        )

        self.assertFalse(
            result["empirical_drop_eligible"]
        )

    def test_singleton_cluster_does_not_require_cluster_review(self) -> None:
        from mes_quant.redundancy import analyzer

        classify = getattr(
            analyzer,
            "_classify_cluster_review_evidence",
            None,
        )

        self.assertTrue(
            callable(classify),
            "analyzer._classify_cluster_review_evidence must exist",
        )

        result = classify(
            cluster_members=(
                "feature_a",
            ),
        )

        self.assertFalse(
            result["review_required"]
        )

        self.assertEqual(
            result["classification"],
            "CLUSTER_SINGLETON",
        )

        self.assertEqual(
            result["base_decision"],
            "KEEP",
        )

        self.assertFalse(
            result["drop_allowed"]
        )




# STEP_13G1_PRODUCTION_OUTPUT_SERIALIZATION_SPEC_V1

class StageBProductionOutputSerializationSpecificationTests(
    unittest.TestCase
):
    EXPECTED_OUTPUTS = (
        "stage_b_feature_coverage_v1.csv",
        "stage_b_semantic_dependency_ledger_v1.csv",
        "stage_b_fold_correlations_v1.parquet",
        "stage_b_set_level_diagnostics_v1.csv",
        "stage_b_redundancy_clusters_v1.csv",
        "stage_b_feature_decision_registry_v1.csv",
        "stage_b_redundancy_audit.json",
    )

    def test_required_output_artifact_names_are_exact_and_ordered(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        get_names = getattr(
            analyzer,
            "_required_stage_b_output_filenames",
            None,
        )

        self.assertTrue(
            callable(get_names),
            "analyzer._required_stage_b_output_filenames must exist",
        )

        self.assertEqual(
            get_names(),
            self.EXPECTED_OUTPUTS,
        )

    def test_serialization_policy_identifiers_are_explicit(
        self,
    ) -> None:
        from mes_quant.redundancy import contract

        self.assertTrue(
            hasattr(
                contract,
                "STAGE_B_CSV_SERIALIZATION_POLICY_ID",
            ),
            "CSV serialization policy identifier must exist",
        )

        self.assertTrue(
            hasattr(
                contract,
                "STAGE_B_JSON_SERIALIZATION_POLICY_ID",
            ),
            "JSON serialization policy identifier must exist",
        )

        self.assertTrue(
            hasattr(
                contract,
                "STAGE_B_AUDIT_HASH_POLICY_ID",
            ),
            "Audit hash policy identifier must exist",
        )

        for name in [
            "STAGE_B_CSV_SERIALIZATION_POLICY_ID",
            "STAGE_B_JSON_SERIALIZATION_POLICY_ID",
            "STAGE_B_AUDIT_HASH_POLICY_ID",
        ]:
            value = getattr(
                contract,
                name,
            )

            self.assertIsInstance(
                value,
                str,
            )

            self.assertTrue(
                value,
            )

    def test_csv_serialization_is_utf8_lf_schema_and_row_deterministic(
        self,
    ) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_stage_b_csv_bytes",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_stage_b_csv_bytes must exist",
        )

        frame = pd.DataFrame(
            [
                {
                    "feature": "feature_b",
                    "base_decision": "KEEP",
                },
                {
                    "feature": "feature_a",
                    "base_decision": "DROP_REDUNDANT",
                },
            ]
        )

        first = serialize(
            frame=frame,
            field_order=[
                "feature",
                "base_decision",
            ],
            row_sort_by=[
                "feature",
            ],
        )

        second = serialize(
            frame=frame.iloc[::-1].copy(),
            field_order=[
                "feature",
                "base_decision",
            ],
            row_sort_by=[
                "feature",
            ],
        )

        self.assertIsInstance(
            first,
            bytes,
        )

        self.assertEqual(
            first,
            second,
        )

        self.assertNotIn(
            b"\r\n",
            first,
        )

        self.assertTrue(
            first.endswith(
                b"\n"
            )
        )

        decoded = first.decode(
            "utf-8"
        )

        self.assertEqual(
            decoded,
            (
                "feature,base_decision\n"
                "feature_a,DROP_REDUNDANT\n"
                "feature_b,KEEP\n"
            ),
        )

    def test_csv_multi_value_pipe_string_is_preserved_exactly(
        self,
    ) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_stage_b_csv_bytes",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_stage_b_csv_bytes must exist",
        )

        frame = pd.DataFrame(
            [
                {
                    "feature": "feature_a",
                    "semantic_dependency_groups": (
                        "GROUP_A|GROUP_B"
                    ),
                }
            ]
        )

        data = serialize(
            frame=frame,
            field_order=[
                "feature",
                "semantic_dependency_groups",
            ],
            row_sort_by=[
                "feature",
            ],
        )

        self.assertIn(
            b"GROUP_A|GROUP_B",
            data,
        )

        self.assertNotIn(
            b"GROUP_B|GROUP_A",
            data,
        )

    def test_json_serialization_is_canonical_utf8_lf(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_stage_b_json_bytes",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_stage_b_json_bytes must exist",
        )

        payload_a = {
            "z": 3,
            "a": {
                "beta": 2,
                "alpha": 1,
            },
        }

        payload_b = {
            "a": {
                "alpha": 1,
                "beta": 2,
            },
            "z": 3,
        }

        first = serialize(
            payload=payload_a,
        )

        second = serialize(
            payload=payload_b,
        )

        self.assertEqual(
            first,
            second,
        )

        self.assertNotIn(
            b"\r\n",
            first,
        )

        self.assertTrue(
            first.endswith(
                b"\n"
            )
        )

        self.assertEqual(
            first.decode("utf-8"),
            '{"a":{"alpha":1,"beta":2},"z":3}\n',
        )

    def test_sha256_uses_exact_serialized_bytes(
        self,
    ) -> None:
        import hashlib

        from mes_quant.redundancy import analyzer

        digest = getattr(
            analyzer,
            "_sha256_bytes",
            None,
        )

        self.assertTrue(
            callable(digest),
            "analyzer._sha256_bytes must exist",
        )

        raw = (
            b"line1\r\n"
            b"line2\n"
        )

        self.assertEqual(
            digest(raw),
            hashlib.sha256(
                raw
            ).hexdigest(),
        )

        normalized = raw.replace(
            b"\r\n",
            b"\n",
        )

        self.assertNotEqual(
            digest(raw),
            digest(normalized),
        )

    def test_output_bundle_requires_exact_seven_artifacts(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_output_bundle",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_output_bundle must exist",
        )

        bundle = {
            name: b"x"
            for name in self.EXPECTED_OUTPUTS
        }

        result = validate(
            artifacts=bundle,
        )

        self.assertTrue(
            result[
                "output_bundle_valid"
            ]
        )

        self.assertEqual(
            result[
                "artifact_count"
            ],
            7,
        )

        missing = dict(
            bundle
        )

        missing.pop(
            self.EXPECTED_OUTPUTS[0]
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                artifacts=missing,
            )

        extra = dict(
            bundle
        )

        extra[
            "cell14_feature_registry_v1.csv"
        ] = b"forbidden"

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                artifacts=extra,
            )

    def test_output_hash_manifest_covers_all_seven_raw_artifacts(
        self,
    ) -> None:
        import hashlib

        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "_build_stage_b_output_hash_manifest",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer._build_stage_b_output_hash_manifest must exist",
        )

        artifacts = {
            name: (
                f"bytes::{index}::{name}\n"
            ).encode(
                "utf-8"
            )
            for index, name in enumerate(
                self.EXPECTED_OUTPUTS
            )
        }

        manifest = build(
            artifacts=artifacts,
            policy_version=contract.POLICY_VERSION,
            control_hashes={
                "markdown_sha256": "a" * 64,
                "semantic_registry_sha256": "b" * 64,
            },
            upstream_hashes={
                "cell14_feature_artifact_sha256": "c" * 64,
                "cell14_registry_sha256": "d" * 64,
            },
        )

        self.assertEqual(
            tuple(
                manifest[
                    "output_hashes"
                ].keys()
            ),
            self.EXPECTED_OUTPUTS,
        )

        for name in self.EXPECTED_OUTPUTS:
            self.assertEqual(
                manifest[
                    "output_hashes"
                ][
                    name
                ],
                hashlib.sha256(
                    artifacts[
                        name
                    ]
                ).hexdigest(),
            )

        self.assertEqual(
            manifest[
                "policy_version"
            ],
            contract.POLICY_VERSION,
        )

    def test_audit_self_hash_policy_is_explicitly_non_recursive(
        self,
    ) -> None:
        from mes_quant.redundancy import contract

        policy = getattr(
            contract,
            "STAGE_B_AUDIT_HASH_POLICY_ID",
            None,
        )

        self.assertTrue(
            isinstance(
                policy,
                str,
            )
            and policy
        )

        self.assertIn(
            "NON_RECURSIVE",
            policy,
        )




# STEP_13G1B_PARQUET_AND_AUDIT_SCHEMA_SPEC_V1

class StageBParquetAndAuditSchemaSpecificationTests(
    unittest.TestCase
):
    REQUIRED_OUTPUTS = (
        "stage_b_feature_coverage_v1.csv",
        "stage_b_semantic_dependency_ledger_v1.csv",
        "stage_b_fold_correlations_v1.parquet",
        "stage_b_set_level_diagnostics_v1.csv",
        "stage_b_redundancy_clusters_v1.csv",
        "stage_b_feature_decision_registry_v1.csv",
        "stage_b_redundancy_audit.json",
    )

    SIBLING_OUTPUTS = REQUIRED_OUTPUTS[:-1]

    EXPECTED_AUDIT_FIELDS = (
        "policy_version",
        "markdown_sha256",
        "semantic_registry_sha256",
        "locked_markdown_git_commit",
        "python_policy_status",
        "cell14_artifact_hashes",
        "cell14_registry_hash",
        "canonical_candidate_count",
        "feature_order_validation",
        "lookback_metadata_validation",
        "common_cohort_coverage_by_fold",
        "full29_yearly_coverage",
        "yearly_low_coverage_flags",
        "yearly_concentration_review_required",
        "yearly_concentration_review_status",
        "shared_240m_missingness_summary",
        "full29_incomplete_row_count",
        "shared_240m_incomplete_row_count",
        "session_to_date_vwap_only_incomplete_row_count",
        "unexplained_full29_incomplete_row_count",
        "fold_coverage_gate_result",
        "final_test_rows_opened",
        "forbidden_inputs_opened",
        "empirical_threshold_provenance",
        "coverage_threshold_provenance",
        "semantic_registry_completeness",
        "semantic_registry_structural_invariant_result",
        "markdown_json_joint_audit_status",
        "prelock_identity_validation_result",
        "prelock_final_test_firewall_result",
        "protected_semantic_basis_features",
        "derived_protected_set_feature_list",
        "protected_set_sentinel_result",
        "full_train_zero_variance_diagnostics",
        "common_cohort_zero_variance_diagnostics",
        "phase_a_decisions",
        "generic_phase_b_group_available_verification_results",
        "generic_phase_b_component_dispositions",
        "generic_phase_b_open_component_count",
        "generic_phase_b_hard_fail_count",
        "generic_phase_b_direct_drop_count",
        "phase_b_rank",
        "phase_c_rank",
        "phase_c_rank_loss",
        "phase_c_rank_loss_review_required",
        "phase_c_rank_loss_review_status",
        "primary_hard_pair_count",
        "cohort_sensitivity_supported_count",
        "cohort_sensitivity_conflict_count",
        "cohort_sensitivity_unavailable_count",
        "empirical_drops_vetoed_by_cohort_sensitivity",
        "full_set_condition_number",
        "post_phase_a_condition_number",
        "clustering_metric",
        "clustering_linkage",
        "clustering_cut",
        "open_count",
        "base_feature_count",
        "linear_overlay_feature_count",
        "tree_overlay_feature_count",
        "unique_stage_c_mask_count",
        "multi_value_serialization_policy_id",
        "output_hashes",
    )

    @classmethod
    def _complete_audit_payload(
        cls,
    ):
        payload = {
            field: None
            for field in cls.EXPECTED_AUDIT_FIELDS
        }

        payload.update(
            {
                "policy_version": contract.POLICY_VERSION,
                "markdown_sha256": "a" * 64,
                "semantic_registry_sha256": "b" * 64,
                "locked_markdown_git_commit": "c" * 40,
                "python_policy_status": "LOCKED_EXECUTABLE",
                "cell14_artifact_hashes": {
                    "feature_artifact_sha256": "d" * 64,
                },
                "cell14_registry_hash": "e" * 64,
                "canonical_candidate_count": 29,
                "feature_order_validation": True,
                "lookback_metadata_validation": True,
                "common_cohort_coverage_by_fold": {
                    "role_wf_2022": 0.95,
                    "role_wf_2023": 0.96,
                    "role_wf_2024": 0.97,
                },
                "full29_yearly_coverage": {
                    "2019": 0.81,
                    "2020": 0.95,
                    "2021": 0.98,
                    "2022": 1.0,
                    "2023": 0.99,
                    "2024": 0.99,
                },
                "yearly_low_coverage_flags": [
                    2019,
                ],
                "yearly_concentration_review_required": True,
                "yearly_concentration_review_status": "ACKNOWLEDGED",
                "shared_240m_missingness_summary": {
                    "shared_rows": 983,
                },
                "full29_incomplete_row_count": 996,
                "shared_240m_incomplete_row_count": 983,
                "session_to_date_vwap_only_incomplete_row_count": 13,
                "unexplained_full29_incomplete_row_count": 0,
                "fold_coverage_gate_result": True,
                "final_test_rows_opened": 0,
                "forbidden_inputs_opened": 0,
                "empirical_threshold_provenance": {
                    "hard_pearson_abs": 0.95,
                    "hard_spearman_abs": 0.95,
                    "review_abs": 0.90,
                },
                "coverage_threshold_provenance": {
                    "fold_floor": 0.90,
                },
                "semantic_registry_completeness": True,
                "semantic_registry_structural_invariant_result": True,
                "markdown_json_joint_audit_status": "PASS",
                "prelock_identity_validation_result": "PASS",
                "prelock_final_test_firewall_result": "PASS",
                "protected_semantic_basis_features": [
                    "ret_log_15m_lag0",
                ],
                "derived_protected_set_feature_list": [
                    "ret_log_15m_lag0",
                    "ret_log_15m_lag1",
                    "ret_log_15m_lag2",
                    "ret_log_15m_lag3",
                    "minutes_since_nyse_open",
                    "early_close_session",
                ],
                "protected_set_sentinel_result": True,
                "full_train_zero_variance_diagnostics": {},
                "common_cohort_zero_variance_diagnostics": {},
                "phase_a_decisions": [],
                "generic_phase_b_group_available_verification_results": [],
                "generic_phase_b_component_dispositions": [],
                "generic_phase_b_open_component_count": 0,
                "generic_phase_b_hard_fail_count": 0,
                "generic_phase_b_direct_drop_count": 0,
                "phase_b_rank": 20,
                "phase_c_rank": 19,
                "phase_c_rank_loss": 1,
                "phase_c_rank_loss_review_required": True,
                "phase_c_rank_loss_review_status": "ACKNOWLEDGED",
                "primary_hard_pair_count": 1,
                "cohort_sensitivity_supported_count": 1,
                "cohort_sensitivity_conflict_count": 0,
                "cohort_sensitivity_unavailable_count": 0,
                "empirical_drops_vetoed_by_cohort_sensitivity": 0,
                "full_set_condition_number": 100.0,
                "post_phase_a_condition_number": 20.0,
                "clustering_metric": "1-ABS_SPEARMAN",
                "clustering_linkage": "COMPLETE",
                "clustering_cut": 0.10,
                "open_count": 0,
                "base_feature_count": 20,
                "linear_overlay_feature_count": 20,
                "tree_overlay_feature_count": 20,
                "unique_stage_c_mask_count": 1,
                "multi_value_serialization_policy_id": (
                    "MES_V1_MULTI_ID_PIPE_ORDERED_V1"
                ),
                "output_hashes": {
                    name: (
                        f"{index + 1:x}" * 64
                    )[:64]
                    for index, name in enumerate(
                        cls.SIBLING_OUTPUTS
                    )
                },
            }
        )

        return payload

    def test_parquet_and_multi_value_policy_identifiers_are_explicit(
        self,
    ) -> None:
        from mes_quant.redundancy import contract

        self.assertTrue(
            hasattr(
                contract,
                "STAGE_B_PARQUET_SERIALIZATION_POLICY_ID",
            ),
            "Parquet serialization policy identifier must exist",
        )

        self.assertTrue(
            hasattr(
                contract,
                "STAGE_B_MULTI_VALUE_SERIALIZATION_POLICY_ID",
            ),
            "Multi-value serialization policy identifier must exist",
        )

        for name in [
            "STAGE_B_PARQUET_SERIALIZATION_POLICY_ID",
            "STAGE_B_MULTI_VALUE_SERIALIZATION_POLICY_ID",
        ]:
            value = getattr(
                contract,
                name,
            )

            self.assertIsInstance(
                value,
                str,
            )

            self.assertTrue(
                value,
            )

    def test_parquet_serialization_is_schema_row_deterministic(
        self,
    ) -> None:
        import io
        import pandas as pd

        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_stage_b_parquet_bytes",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_stage_b_parquet_bytes must exist",
        )

        frame = pd.DataFrame(
            [
                {
                    "fold": "role_wf_2023",
                    "feature_a": "b",
                    "feature_b": "c",
                    "pearson": 0.91,
                    "spearman": 0.92,
                },
                {
                    "fold": "role_wf_2022",
                    "feature_a": "a",
                    "feature_b": "b",
                    "pearson": 0.97,
                    "spearman": 0.96,
                },
            ]
        )

        fields = [
            "fold",
            "feature_a",
            "feature_b",
            "pearson",
            "spearman",
        ]

        sort_by = [
            "fold",
            "feature_a",
            "feature_b",
        ]

        first = serialize(
            frame=frame,
            field_order=fields,
            row_sort_by=sort_by,
        )

        second = serialize(
            frame=(
                frame.iloc[::-1]
                .loc[
                    :,
                    list(reversed(fields)),
                ]
                .copy()
            ),
            field_order=fields,
            row_sort_by=sort_by,
        )

        self.assertIsInstance(
            first,
            bytes,
        )

        self.assertEqual(
            first,
            second,
        )

        self.assertTrue(
            first.startswith(
                b"PAR1"
            )
        )

        self.assertTrue(
            first.endswith(
                b"PAR1"
            )
        )

        restored = pd.read_parquet(
            io.BytesIO(first)
        )

        self.assertEqual(
            list(restored.columns),
            fields,
        )

        self.assertEqual(
            list(restored["fold"]),
            [
                "role_wf_2022",
                "role_wf_2023",
            ],
        )

    def test_parquet_serializer_requires_exact_declared_schema(
        self,
    ) -> None:
        import pandas as pd

        from mes_quant.redundancy import analyzer

        serialize = getattr(
            analyzer,
            "_serialize_stage_b_parquet_bytes",
            None,
        )

        self.assertTrue(
            callable(serialize),
            "analyzer._serialize_stage_b_parquet_bytes must exist",
        )

        frame = pd.DataFrame(
            [
                {
                    "a": 1,
                    "b": 2,
                    "unexpected": 3,
                }
            ]
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            serialize(
                frame=frame,
                field_order=[
                    "a",
                    "b",
                ],
                row_sort_by=[
                    "a",
                ],
            )

    def test_required_audit_fields_match_v12_minimum_contract(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        required = getattr(
            analyzer,
            "_required_stage_b_audit_fields",
            None,
        )

        self.assertTrue(
            callable(required),
            "analyzer._required_stage_b_audit_fields must exist",
        )

        result = required()

        self.assertEqual(
            result,
            self.EXPECTED_AUDIT_FIELDS,
        )

        self.assertEqual(
            len(result),
            len(set(result)),
        )

    def test_complete_minimum_audit_payload_is_valid(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_audit_payload",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_audit_payload must exist",
        )

        result = validate(
            payload=self._complete_audit_payload(),
        )

        self.assertTrue(
            result[
                "audit_payload_valid"
            ]
        )

        self.assertEqual(
            result[
                "required_field_count"
            ],
            len(
                self.EXPECTED_AUDIT_FIELDS
            ),
        )

    def test_audit_rejects_any_generic_phase_b_direct_drop(self) -> None:
        from mes_quant.redundancy import analyzer

        payload = self._complete_audit_payload()
        payload["generic_phase_b_direct_drop_count"] = 1

        with self.assertRaisesRegex(
            RuntimeError,
            "forbidden generic Phase-B direct DROP authority",
        ):
            analyzer._validate_stage_b_audit_payload(
                payload=payload,
            )

    def test_missing_any_required_audit_field_fails_closed(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_audit_payload",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_audit_payload must exist",
        )

        payload = self._complete_audit_payload()

        payload.pop(
            "final_test_rows_opened"
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                payload=payload,
            )

    def test_audit_hashes_are_non_recursive_six_sibling_hashes(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_audit_payload",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_audit_payload must exist",
        )

        payload = self._complete_audit_payload()

        result = validate(
            payload=payload,
        )

        self.assertEqual(
            result[
                "audit_output_hash_names"
            ],
            self.SIBLING_OUTPUTS,
        )

        self.assertNotIn(
            "stage_b_redundancy_audit.json",
            payload[
                "output_hashes"
            ],
        )

        invalid = self._complete_audit_payload()

        invalid[
            "output_hashes"
        ][
            "stage_b_redundancy_audit.json"
        ] = "f" * 64

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                payload=invalid,
            )

    def test_audit_minimum_schema_allows_additional_metadata(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_audit_payload",
            None,
        )

        self.assertTrue(
            callable(validate),
            "analyzer._validate_stage_b_audit_payload must exist",
        )

        payload = self._complete_audit_payload()

        payload[
            "runtime_library_versions"
        ] = {
            "pandas": "synthetic",
            "pyarrow": "synthetic",
        }

        result = validate(
            payload=payload,
        )

        self.assertTrue(
            result[
                "audit_payload_valid"
            ]
        )




# STEP_13G2C_MINIMAL_V1_1_PREREQUISITE_SPEC


class StageBMinimalV11PrerequisiteSpecificationTests(
    unittest.TestCase
):
    SHARED_240M = (
        "momentum_log_240m",
        "realized_vol_240m",
        "volume_ratio_prev_240m",
        "return_autocorr_lag1_240m",
        "sign_entropy_240m",
    )

    @classmethod
    def _missingness_frame(
        cls,
    ):
        import numpy as np
        import pandas as pd

        features = list(
            cls.SHARED_240M
        ) + [
            "session_vwap_proxy_deviation",
            "ret_log_15m_lag0",
        ]

        rows = []

        # Row 0:
        # shared 240m component only.
        row = {
            feature: 1.0
            for feature in features
        }

        for feature in cls.SHARED_240M:
            row[feature] = np.nan

        row["feature_status"] = (
            "PARTIAL_LOOKBACK"
        )

        rows.append(row)

        # Row 1:
        # shared 240m component AND VWAP unavailable.
        # Still counts once inside shared component.
        row = {
            feature: 1.0
            for feature in features
        }

        for feature in cls.SHARED_240M:
            row[feature] = np.nan

        row[
            "session_vwap_proxy_deviation"
        ] = np.nan

        row["feature_status"] = (
            "PARTIAL_LOOKBACK|SESSION_VWAP_INPUT_INVALID"
        )

        rows.append(row)

        # Row 2:
        # VWAP-only residual.
        row = {
            feature: 1.0
            for feature in features
        }

        row[
            "session_vwap_proxy_deviation"
        ] = np.nan

        row["feature_status"] = (
            "SESSION_VWAP_INPUT_INVALID"
        )

        rows.append(row)

        # Row 3:
        # complete.
        row = {
            feature: 1.0
            for feature in features
        }

        row["feature_status"] = "OK"

        rows.append(row)

        return (
            pd.DataFrame(rows),
            features,
        )

    def test_full29_missingness_reconciliation_is_component_based(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        reconcile = getattr(
            analyzer,
            "_reconcile_full29_missingness",
            None,
        )

        self.assertTrue(
            callable(reconcile),
            "analyzer._reconcile_full29_missingness must exist",
        )

        frame, features = (
            self._missingness_frame()
        )

        result = reconcile(
            frame=frame,
            canonical_features=features,
            shared_240m_features=list(
                self.SHARED_240M
            ),
            session_to_date_feature=(
                "session_vwap_proxy_deviation"
            ),
            status_column="feature_status",
        )

        self.assertEqual(
            result[
                "full29_incomplete_row_count"
            ],
            3,
        )

        self.assertEqual(
            result[
                "shared_240m_incomplete_row_count"
            ],
            2,
        )

        self.assertEqual(
            result[
                "session_to_date_vwap_only_incomplete_row_count"
            ],
            1,
        )

        self.assertEqual(
            result[
                "unexplained_full29_incomplete_row_count"
            ],
            0,
        )

    def test_shared_240m_missingness_is_not_counted_as_five_events(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        reconcile = getattr(
            analyzer,
            "_reconcile_full29_missingness",
            None,
        )

        self.assertTrue(
            callable(reconcile),
            "analyzer._reconcile_full29_missingness must exist",
        )

        frame, features = (
            self._missingness_frame()
        )

        result = reconcile(
            frame=frame,
            canonical_features=features,
            shared_240m_features=list(
                self.SHARED_240M
            ),
            session_to_date_feature=(
                "session_vwap_proxy_deviation"
            ),
            status_column="feature_status",
        )

        summary = result[
            "shared_240m_missingness_summary"
        ]

        self.assertEqual(
            summary[
                "feature_count"
            ],
            5,
        )

        self.assertEqual(
            summary[
                "row_count"
            ],
            2,
        )

        self.assertEqual(
            tuple(
                summary[
                    "features"
                ]
            ),
            self.SHARED_240M,
        )

    def test_unexplained_missingness_remains_explicit(
        self,
    ) -> None:
        import numpy as np

        from mes_quant.redundancy import analyzer

        reconcile = getattr(
            analyzer,
            "_reconcile_full29_missingness",
            None,
        )

        self.assertTrue(
            callable(reconcile),
            "analyzer._reconcile_full29_missingness must exist",
        )

        frame, features = (
            self._missingness_frame()
        )

        frame.loc[
            3,
            "ret_log_15m_lag0",
        ] = np.nan

        result = reconcile(
            frame=frame,
            canonical_features=features,
            shared_240m_features=list(
                self.SHARED_240M
            ),
            session_to_date_feature=(
                "session_vwap_proxy_deviation"
            ),
            status_column="feature_status",
        )

        self.assertEqual(
            result[
                "full29_incomplete_row_count"
            ],
            4,
        )

        self.assertEqual(
            result[
                "unexplained_full29_incomplete_row_count"
            ],
            1,
        )

    def test_intercept_rank_diagnostic_reports_feature_and_augmented_rank(
        self,
    ) -> None:
        import numpy as np

        from mes_quant.redundancy import analyzer

        compute = getattr(
            analyzer,
            "_compute_intercept_rank_diagnostic",
            None,
        )

        self.assertTrue(
            callable(compute),
            "analyzer._compute_intercept_rank_diagnostic must exist",
        )

        x = np.asarray(
            [
                -1.0,
                -0.5,
                0.5,
                1.0,
            ],
            dtype=np.float64,
        )

        z = np.column_stack(
            [
                x,
                2.0 * x,
            ]
        )

        result = compute(
            standardized_matrix=z,
        )

        self.assertEqual(
            result[
                "feature_space_rank"
            ],
            1,
        )

        self.assertEqual(
            result[
                "feature_space_deficiency"
            ],
            1,
        )

        self.assertEqual(
            result[
                "augmented_design_rank"
            ],
            2,
        )

        self.assertEqual(
            result[
                "augmented_design_deficiency"
            ],
            1,
        )

    def test_full_set_rank_deficiency_maps_condition_number_to_infinity(
        self,
    ) -> None:
        import math

        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "_resolve_stage_b_condition_number",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer._resolve_stage_b_condition_number must exist",
        )

        result = resolve(
            svd_diagnostics={
                "matrix_shape": (
                    100,
                    3,
                ),
                "singular_values": [
                    10.0,
                    2.0,
                    0.0,
                ],
                "rank": 2,
                "deficiency": 1,
            },
            diagnostic_scope="FULL_SET",
        )

        self.assertTrue(
            math.isinf(
                result[
                    "condition_number"
                ]
            )
        )

        self.assertEqual(
            result[
                "diagnostic_scope"
            ],
            "FULL_SET",
        )

    def test_post_phase_a_rank_deficiency_requires_generic_discovery(
        self,
    ) -> None:
        import math

        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "_resolve_stage_b_condition_number",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer._resolve_stage_b_condition_number must exist",
        )

        result = resolve(
            svd_diagnostics={
                "matrix_shape": (
                    100,
                    3,
                ),
                "singular_values": [
                    10.0,
                    2.0,
                    0.0,
                ],
                "rank": 2,
                "deficiency": 1,
            },
            diagnostic_scope="POST_PHASE_A_CANDIDATE_SET",
        )

        self.assertTrue(math.isinf(result["condition_number"]))
        self.assertTrue(result["generic_rank_discovery_required"])
        self.assertEqual(result["decision_effect"], "REPORT_ONLY")

    def test_post_phase_a_full_rank_condition_number_is_sigma_ratio(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        resolve = getattr(
            analyzer,
            "_resolve_stage_b_condition_number",
            None,
        )

        self.assertTrue(
            callable(resolve),
            "analyzer._resolve_stage_b_condition_number must exist",
        )

        result = resolve(
            svd_diagnostics={
                "matrix_shape": (
                    100,
                    2,
                ),
                "singular_values": [
                    10.0,
                    2.0,
                ],
                "rank": 2,
                "deficiency": 0,
            },
            diagnostic_scope="POST_PHASE_A_CANDIDATE_SET",
        )

        self.assertAlmostEqual(
            result[
                "condition_number"
            ],
            5.0,
        )
        self.assertFalse(result["generic_rank_discovery_required"])

    def test_stage_c_masks_are_deterministic_and_deduplicated(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "_build_stage_c_feature_masks",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer._build_stage_c_feature_masks must exist",
        )

        result = build(
            base_features=[
                "c",
                "a",
                "b",
            ],
            linear_removed_features=[
                "c",
            ],
            tree_removed_features=[],
            protected_features=set(),
            canonical_order=[
                "a",
                "b",
                "c",
            ],
        )

        self.assertEqual(
            result[
                "base_mask"
            ],
            (
                "a",
                "b",
                "c",
            ),
        )

        self.assertEqual(
            result[
                "linear_overlay_mask"
            ],
            (
                "a",
                "b",
            ),
        )

        self.assertEqual(
            result[
                "tree_overlay_mask"
            ],
            (
                "a",
                "b",
                "c",
            ),
        )

        self.assertEqual(
            result[
                "unique_masks"
            ],
            (
                (
                    "a",
                    "b",
                    "c",
                ),
                (
                    "a",
                    "b",
                ),
            ),
        )

        self.assertEqual(
            result[
                "unique_stage_c_mask_count"
            ],
            2,
        )

        self.assertLessEqual(
            result[
                "unique_stage_c_mask_count"
            ],
            3,
        )

    def test_overlay_removal_of_protected_base_feature_is_recorded(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "_build_stage_c_feature_masks",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer._build_stage_c_feature_masks must exist",
        )

        result = build(
            base_features=[
                "a",
                "b",
                "c",
            ],
            linear_removed_features=[
                "b",
            ],
            tree_removed_features=[],
            protected_features={
                "b",
            },
            canonical_order=[
                "a",
                "b",
                "c",
            ],
        )

        self.assertEqual(
            result[
                "protected_overlay_removals"
            ][
                "LINEAR_OVERLAY"
            ],
            (
                "b",
            ),
        )

        self.assertEqual(
            result[
                "protected_overlay_removals"
            ][
                "TREE_OVERLAY"
            ],
            (),
        )

    def test_overlay_cannot_remove_feature_outside_base(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        build = getattr(
            analyzer,
            "_build_stage_c_feature_masks",
            None,
        )

        self.assertTrue(
            callable(build),
            "analyzer._build_stage_c_feature_masks must exist",
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            build(
                base_features=[
                    "a",
                    "b",
                ],
                linear_removed_features=[
                    "dropped_derived_feature",
                ],
                tree_removed_features=[],
                protected_features=set(),
                canonical_order=[
                    "a",
                    "b",
                    "dropped_derived_feature",
                ],
            )




# STEP_13G3A_RUN_STAGE_B_PRODUCTION_BOUNDARY_SPEC


class StageBProductionBoundarySpecificationTests(
    unittest.TestCase
):
    EXPECTED_PARAMETERS = (
        "project_root",
        "output_dir",
        "yearly_review_acknowledged",
        "phase_c_rank_loss_review_acknowledged",
    )

    FORBIDDEN_CALLER_PROVENANCE_PARAMETERS = {
        "release_manifest_path",
        "cell14_features_path",
        "cell14_registry_path",
        "cell8_assignments_path",
        "markdown_sha256",
        "semantic_registry_sha256",
        "cell14_registry_hash",
        "cell14_feature_hash",
        "cell8_assignments_hash",
        "upstream_hashes",
        "opened_fields",
        "opened_cells",
        "final_test_rows_opened",
        "feature_frame",
        "features_df",
        "registry_rows",
        "fold_assignments",
    }

    LEGACY_HIGH_LEVEL_PATHS = {
        "get_train_mask",
        "get_common_complete_case_train_mask",
        "compute_fold_correlations",
        "classify_pair_redundancy",
        "build_pairwise_redundancy_table",
        "analyze_one_fold",
        "analyze_all_folds",
        "build_fold_coverage_summary",
        "build_all_fold_coverage_summary",
        "build_feature_missingness_summary",
        "build_all_fold_feature_missingness_summary",
        "check_momentum_60m_identity",
        "check_weekday_dummy_identity",
    }

    @staticmethod
    def _run_stage_b():
        from mes_quant.redundancy import analyzer

        obj = getattr(
            analyzer,
            "run_stage_b",
            None,
        )

        if not callable(obj):
            raise AssertionError(
                "analyzer.run_stage_b must exist"
            )

        return obj

    def test_run_stage_b_has_exact_keyword_only_boundary_signature(
        self,
    ) -> None:
        import inspect

        run_stage_b = (
            self._run_stage_b()
        )

        signature = (
            inspect.signature(
                run_stage_b
            )
        )

        parameters = tuple(
            signature.parameters
        )

        self.assertEqual(
            parameters,
            self.EXPECTED_PARAMETERS,
        )

        for name in (
            self.EXPECTED_PARAMETERS
        ):
            parameter = (
                signature.parameters[
                    name
                ]
            )

            self.assertEqual(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
                (
                    "run_stage_b production arguments "
                    "must be keyword-only"
                ),
            )

        self.assertFalse(
            any(
                parameter.kind
                in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }
                for parameter
                in signature.parameters.values()
            ),
            (
                "run_stage_b must not expose "
                "*args or **kwargs"
            ),
        )

    def test_run_stage_b_does_not_accept_caller_supplied_provenance(
        self,
    ) -> None:
        import inspect

        run_stage_b = (
            self._run_stage_b()
        )

        parameters = set(
            inspect.signature(
                run_stage_b
            ).parameters
        )

        overlap = sorted(
            parameters.intersection(
                self.FORBIDDEN_CALLER_PROVENANCE_PARAMETERS
            )
        )

        self.assertEqual(
            overlap,
            [],
            (
                "run_stage_b must derive production "
                "provenance from canonical controls "
                "instead of trusting caller-supplied "
                f"provenance: {overlap}"
            ),
        )

    def test_production_gate_runs_before_any_artifact_io(
        self,
    ) -> None:
        from pathlib import Path
        from unittest.mock import patch

        run_stage_b = (
            self._run_stage_b()
        )

        def unexpected_io(
            *args,
            **kwargs,
        ):
            raise AssertionError(
                "artifact I/O occurred before "
                "the production policy gate"
            )

        with (
            patch.object(
                Path,
                "read_bytes",
                side_effect=unexpected_io,
            ),
            patch.object(
                Path,
                "read_text",
                side_effect=unexpected_io,
            ),
            patch.object(
                Path,
                "write_bytes",
                side_effect=unexpected_io,
            ),
            patch.object(
                Path,
                "write_text",
                side_effect=unexpected_io,
            ),
            patch.object(
                Path,
                "mkdir",
                side_effect=unexpected_io,
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                (
                    "Stage B policy must be "
                    "LOCKED_EXECUTABLE"
                ),
            ):
                run_stage_b(
                    project_root=Path(
                        "synthetic_project_root"
                    ),
                    output_dir=Path(
                        "synthetic_output"
                    ),
                    yearly_review_acknowledged=False,
                    phase_c_rank_loss_review_acknowledged=False,
                )

    def test_run_stage_b_is_sole_redundancy_package_artifact_reader(
        self,
    ) -> None:
        import ast
        from pathlib import Path

        package_dir = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "mes_quant"
            / "redundancy"
        )

        reader_call_names = {
            "open",
            "read_csv",
            "read_parquet",
            "read_json",
            "read_pickle",
            "read_bytes",
            "read_text",
        }

        readers = []

        for py_path in sorted(
            package_dir.glob(
                "*.py"
            )
        ):
            tree = ast.parse(
                py_path.read_text(
                    encoding="utf-8"
                )
            )

            for node in tree.body:
                if not isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    continue

                calls = []

                for child in ast.walk(
                    node
                ):
                    if not isinstance(
                        child,
                        ast.Call,
                    ):
                        continue

                    if isinstance(
                        child.func,
                        ast.Name,
                    ):
                        name = (
                            child.func.id
                        )

                    elif isinstance(
                        child.func,
                        ast.Attribute,
                    ):
                        name = (
                            child.func.attr
                        )

                    else:
                        continue

                    if name in reader_call_names:
                        calls.append(
                            name
                        )

                if calls:
                    readers.append(
                        (
                            py_path.name,
                            node.name,
                        )
                    )

        self.assertEqual(
            readers,
            [
                (
                    "analyzer.py",
                    "run_stage_b",
                ),
                (
                    "analyzer.py",
                    "assert_stage_b_contract_locked",
                ),
            ],
            (
                "Expected Stage B production data access to remain in "
                "analyzer.run_stage_b and locked-control byte access "
                "to remain in analyzer.assert_stage_b_contract_locked, got "
                f"{readers}"
            ),
        )

    def test_run_stage_b_does_not_call_legacy_high_level_paths(
        self,
    ) -> None:
        import ast
        import inspect
        import textwrap

        run_stage_b = (
            self._run_stage_b()
        )

        source = textwrap.dedent(
            inspect.getsource(
                run_stage_b
            )
        )

        tree = ast.parse(
            source
        )

        called_names = set()

        for node in ast.walk(
            tree
        ):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            if isinstance(
                node.func,
                ast.Name,
            ):
                called_names.add(
                    node.func.id
                )

            elif isinstance(
                node.func,
                ast.Attribute,
            ):
                called_names.add(
                    node.func.attr
                )

        forbidden_used = sorted(
            called_names.intersection(
                self.LEGACY_HIGH_LEVEL_PATHS
            )
        )

        self.assertEqual(
            forbidden_used,
            [],
            (
                "run_stage_b must use the bounded V1.2 Phase 0/A "
                "runtime instead of legacy "
                f"decision paths: {forbidden_used}"
            ),
        )

    def test_run_stage_b_remains_fail_closed_before_phase_b(self) -> None:
        import inspect

        source = inspect.getsource(self._run_stage_b())

        phase_a_call = source.index("_run_stage_b_phase_a(")
        fail_closed = source.index(
            'raise RuntimeError(\n        "Stage B Phase B boundary is not yet "'
        )

        self.assertLess(phase_a_call, fail_closed)
        self.assertNotIn("classify_generic_rank_discovery(", source)

    def test_run_stage_b_boundary_has_no_label_aware_input_parameters(
        self,
    ) -> None:
        import inspect

        run_stage_b = (
            self._run_stage_b()
        )

        parameters = tuple(
            inspect.signature(
                run_stage_b
            ).parameters
        )

        forbidden_tokens = (
            "label",
            "target",
            "pnl",
            "future_return",
            "auc",
            "validation_performance",
            "final_test",
        )

        violations = [
            name
            for name in parameters
            if any(
                token in name.lower()
                for token in forbidden_tokens
            )
        ]

        self.assertEqual(
            violations,
            [],
            (
                "Stage B production boundary must "
                "remain target-blind: "
                f"{violations}"
            ),
        )




# STEP_13G3B1_PROVENANCE_CONTROL_FIREWALL_SPEC


class StageBProductionProvenanceFirewallSpecificationTests(
    unittest.TestCase
):
    EXPECTED_READABLE_ARTIFACT_IDS = (
        "cell14_features",
        "cell14_registry",
        "cell14_audit",
        "cell8_assignments",
        "cell8_audit",
    )

    @staticmethod
    def _repo_root():
        from pathlib import Path

        return (
            Path(__file__)
            .resolve()
            .parents[1]
        )

    @classmethod
    def _frozen_release_manifest(
        cls,
    ):
        import json

        path = (
            cls._repo_root()
            / "manifests"
            / "releases"
            / "cell14_local_release_v1.json"
        )

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    def test_stage_b_contract_contains_frozen_provenance_pins(
        self,
    ) -> None:
        from mes_quant.redundancy import contract
        from tools.verify_cell14_release import (
            EXPECTED_RELEASE_MANIFEST_SHA256,
        )

        required = (
            "CELL14_RELEASE_MANIFEST_PATH",
            "CELL14_RELEASE_MANIFEST_SHA256",
            "CELL14_REGISTRY_FILE_SHA256",
            "CELL14_AUDIT_FILE_SHA256",
            "CELL8_ASSIGNMENTS_FILE_SHA256",
            "CELL8_AUDIT_FILE_SHA256",
        )

        for name in required:
            self.assertTrue(
                hasattr(
                    contract,
                    name,
                ),
                (
                    "Missing Stage B provenance pin: "
                    f"{name}"
                ),
            )

        manifest = (
            self._frozen_release_manifest()
        )

        self.assertEqual(
            contract.CELL14_RELEASE_MANIFEST_PATH,
            (
                "manifests/releases/"
                "cell14_local_release_v1.json"
            ),
        )

        self.assertEqual(
            contract.CELL14_RELEASE_MANIFEST_SHA256,
            EXPECTED_RELEASE_MANIFEST_SHA256,
        )

        self.assertEqual(
            contract.CELL14_REGISTRY_FILE_SHA256,
            manifest[
                "runs"
            ][
                "canonical"
            ][
                "artifacts"
            ][
                "registry"
            ][
                "sha256"
            ],
        )

        self.assertEqual(
            contract.CELL14_AUDIT_FILE_SHA256,
            manifest[
                "runs"
            ][
                "canonical"
            ][
                "artifacts"
            ][
                "audit"
            ][
                "sha256"
            ],
        )

        self.assertEqual(
            contract.CELL8_ASSIGNMENTS_FILE_SHA256,
            manifest[
                "upstream_inputs"
            ][
                "cell8_assignments"
            ][
                "sha256"
            ],
        )

        self.assertEqual(
            contract.CELL8_AUDIT_FILE_SHA256,
            manifest[
                "upstream_inputs"
            ][
                "cell8_audit"
            ][
                "sha256"
            ],
        )

    def test_release_manifest_binding_exposes_only_stage_b_allowed_artifacts(
        self,
    ) -> None:
        import inspect

        from mes_quant.redundancy import analyzer

        source = inspect.getsource(
            analyzer._validate_stage_b_release_manifest_binding
        )

        self.assertIn(
            "provenance_only_artifact_ids",
            source,
        )

        self.assertIn(
            "cell8_assignments",
            source,
        )

        self.assertIn(
            "readable_artifact_ids",
            source,
        )

    def test_release_manifest_binding_rejects_critical_hash_mutation(
        self,
    ) -> None:
        import copy

        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_release_manifest_binding",
            None,
        )

        self.assertTrue(
            callable(validate),
            (
                "analyzer."
                "_validate_stage_b_release_manifest_binding "
                "must exist"
            ),
        )

        manifest = copy.deepcopy(
            self._frozen_release_manifest()
        )

        manifest[
            "upstream_inputs"
        ][
            "cell8_assignments"
        ][
            "sha256"
        ] = "0" * 64

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                release_manifest=manifest,
            )

    def test_release_manifest_binding_rejects_path_escape(
        self,
    ) -> None:
        import copy

        from mes_quant.redundancy import analyzer

        validate = getattr(
            analyzer,
            "_validate_stage_b_release_manifest_binding",
            None,
        )

        self.assertTrue(
            callable(validate),
            (
                "analyzer."
                "_validate_stage_b_release_manifest_binding "
                "must exist"
            ),
        )

        manifest = copy.deepcopy(
            self._frozen_release_manifest()
        )

        manifest[
            "runs"
        ][
            "canonical"
        ][
            "artifacts"
        ][
            "features"
        ][
            "file"
        ] = "../escape.parquet"

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            validate(
                release_manifest=manifest,
            )

    def test_run_stage_b_rejects_tampered_release_manifest_before_dataframe_io(
        self,
    ) -> None:
        import tempfile

        from pathlib import Path
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer

        repo_root = (
            self._repo_root()
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = (
                Path(tmp)
                / "project"
            )

            (
                root
                / "manifests"
                / "releases"
            ).mkdir(
                parents=True
            )

            (
                root
                / "docs"
            ).mkdir(
                parents=True
            )

            (
                root
                / "configs"
                / "v1"
            ).mkdir(
                parents=True
            )

            # Valid JSON but deliberately not the frozen
            # Cell14 release-manifest bytes.
            (
                root
                / "manifests"
                / "releases"
                / "cell14_local_release_v1.json"
            ).write_text(
                '{"tampered":true}\n',
                encoding="utf-8",
            )

            (
                root
                / "docs"
                / "STAGE_B_REDUNDANCY_CONTRACT.md"
            ).write_bytes(
                (
                    repo_root
                    / "docs"
                    / "STAGE_B_REDUNDANCY_CONTRACT.md"
                ).read_bytes()
            )

            (
                root
                / "configs"
                / "v1"
                / "stage_b_semantic_registry_v1.json"
            ).write_bytes(
                (
                    repo_root
                    / "configs"
                    / "v1"
                    / "stage_b_semantic_registry_v1.json"
                ).read_bytes()
            )

            def forbidden_dataframe_io(
                *args,
                **kwargs,
            ):
                raise AssertionError(
                    "DataFrame artifact I/O occurred "
                    "before release-manifest firewall"
                )

            with (
                patch.object(
                    analyzer,
                    "assert_stage_b_contract_locked",
                    return_value=None,
                ),
                patch.object(
                    analyzer.pd,
                    "read_parquet",
                    side_effect=forbidden_dataframe_io,
                ),
                patch.object(
                    analyzer.pd,
                    "read_csv",
                    side_effect=forbidden_dataframe_io,
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    (
                        "release manifest SHA256 mismatch"
                    ),
                ):
                    analyzer.run_stage_b(
                        project_root=root,
                        output_dir=(
                            root
                            / "stage_b_output"
                        ),
                        yearly_review_acknowledged=False,
                        phase_c_rank_loss_review_acknowledged=False,
                    )

    def test_run_stage_b_rejects_tampered_markdown_before_dataframe_io(
        self,
    ) -> None:
        import tempfile

        from pathlib import Path
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer

        repo_root = (
            self._repo_root()
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = (
                Path(tmp)
                / "project"
            )

            (
                root
                / "manifests"
                / "releases"
            ).mkdir(
                parents=True
            )

            (
                root
                / "docs"
            ).mkdir(
                parents=True
            )

            (
                root
                / "configs"
                / "v1"
            ).mkdir(
                parents=True
            )

            (
                root
                / "manifests"
                / "releases"
                / "cell14_local_release_v1.json"
            ).write_bytes(
                (
                    repo_root
                    / "manifests"
                    / "releases"
                    / "cell14_local_release_v1.json"
                ).read_bytes()
            )

            (
                root
                / "docs"
                / "STAGE_B_REDUNDANCY_CONTRACT.md"
            ).write_bytes(
                b"TAMPERED MARKDOWN\n"
            )

            (
                root
                / "configs"
                / "v1"
                / "stage_b_semantic_registry_v1.json"
            ).write_bytes(
                (
                    repo_root
                    / "configs"
                    / "v1"
                    / "stage_b_semantic_registry_v1.json"
                ).read_bytes()
            )

            def forbidden_dataframe_io(
                *args,
                **kwargs,
            ):
                raise AssertionError(
                    "DataFrame artifact I/O occurred "
                    "before Markdown firewall"
                )

            with (
                patch.object(
                    analyzer,
                    "assert_stage_b_contract_locked",
                    return_value=None,
                ),
                patch.object(
                    analyzer.pd,
                    "read_parquet",
                    side_effect=forbidden_dataframe_io,
                ),
                patch.object(
                    analyzer.pd,
                    "read_csv",
                    side_effect=forbidden_dataframe_io,
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Markdown contract SHA256 mismatch",
                ):
                    analyzer.run_stage_b(
                        project_root=root,
                        output_dir=(
                            root
                            / "stage_b_output"
                        ),
                        yearly_review_acknowledged=False,
                        phase_c_rank_loss_review_acknowledged=False,
                    )

    def test_run_stage_b_rejects_tampered_semantic_registry_before_dataframe_io(
        self,
    ) -> None:
        import tempfile

        from pathlib import Path
        from unittest.mock import patch

        from mes_quant.redundancy import analyzer

        repo_root = (
            self._repo_root()
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = (
                Path(tmp)
                / "project"
            )

            (
                root
                / "manifests"
                / "releases"
            ).mkdir(
                parents=True
            )

            (
                root
                / "docs"
            ).mkdir(
                parents=True
            )

            (
                root
                / "configs"
                / "v1"
            ).mkdir(
                parents=True
            )

            (
                root
                / "manifests"
                / "releases"
                / "cell14_local_release_v1.json"
            ).write_bytes(
                (
                    repo_root
                    / "manifests"
                    / "releases"
                    / "cell14_local_release_v1.json"
                ).read_bytes()
            )

            (
                root
                / "docs"
                / "STAGE_B_REDUNDANCY_CONTRACT.md"
            ).write_bytes(
                (
                    repo_root
                    / "docs"
                    / "STAGE_B_REDUNDANCY_CONTRACT.md"
                ).read_bytes()
            )

            # Valid JSON with byte-level tampering.
            (
                root
                / "configs"
                / "v1"
                / "stage_b_semantic_registry_v1.json"
            ).write_text(
                '{"tampered":true}\n',
                encoding="utf-8",
            )

            def forbidden_dataframe_io(
                *args,
                **kwargs,
            ):
                raise AssertionError(
                    "DataFrame artifact I/O occurred "
                    "before semantic-registry firewall"
                )

            with (
                patch.object(
                    analyzer,
                    "assert_stage_b_contract_locked",
                    return_value=None,
                ),
                patch.object(
                    analyzer.pd,
                    "read_parquet",
                    side_effect=forbidden_dataframe_io,
                ),
                patch.object(
                    analyzer.pd,
                    "read_csv",
                    side_effect=forbidden_dataframe_io,
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    (
                        "semantic registry SHA256 mismatch"
                    ),
                ):
                    analyzer.run_stage_b(
                        project_root=root,
                        output_dir=(
                            root
                            / "stage_b_output"
                        ),
                        yearly_review_acknowledged=False,
                        phase_c_rank_loss_review_acknowledged=False,
                    )




# STEP_13G3B2_CANONICAL_DATA_OPEN_RECONCILIATION_SPEC


class StageBEmbeddedRoleProjectionBoundarySpecificationTests(
    unittest.TestCase
):
    @staticmethod
    def _fold_columns():
        return (
            "role_wf_2022",
            "role_wf_2023",
            "role_wf_2024",
        )

    @classmethod
    def _feature_frame(cls):
        import pandas as pd

        return pd.DataFrame(
            {
                "decision_id": [
                    "D1",
                    "D2",
                    "D3",
                ],
                "decision_time": pd.to_datetime(
                    [
                        "2024-01-02T15:00:00Z",
                        "2024-06-03T15:00:00Z",
                        "2024-12-31T20:00:00Z",
                    ],
                    utc=True,
                ),
                "outer_partition": [
                    "TRAIN",
                    "TRAIN",
                    "VALIDATION",
                ],
                "role_wf_2022": [
                    "TRAIN",
                    "TRAIN",
                    "VALIDATION",
                ],
                "role_wf_2023": [
                    "TRAIN",
                    "TRAIN",
                    "VALIDATION",
                ],
                "role_wf_2024": [
                    "TRAIN",
                    "TRAIN",
                    "VALIDATION",
                ],
            }
        )

    @staticmethod
    def _cell8_sha():
        return (
            "2e13ee7d1e7de321411604c3500c73e6"
            "8a080b02fa2983288d41d399aeb43035"
        )

    @classmethod
    def _cell14_audit(
        cls,
        *,
        cell8_sha=None,
        rows=3,
        final_test_rows=0,
    ):
        if cell8_sha is None:
            cell8_sha = cls._cell8_sha()

        return {
            "upstream_binding": {
                "cell8_assignments_sha256": (
                    cell8_sha
                ),
            },
            "feature_contract": {
                "final_test_feature_rows": (
                    final_test_rows
                ),
            },
            "physical_development_reads": {
                "cell8_assignments": {
                    "physical_filter": {
                        "outer_partition_in": [
                            "TRAIN",
                            "VALIDATION",
                        ],
                    },
                    "rows": rows,
                    "decision_time_min_utc": (
                        "2024-01-02T15:00:00+00:00"
                    ),
                    "decision_time_max_utc": (
                        "2024-12-31T20:00:00+00:00"
                    ),
                    "partitions": [
                        "TRAIN",
                        "VALIDATION",
                    ],
                },
            },
            "counts": {
                "development_rows": rows,
                "final_test_feature_rows": (
                    final_test_rows
                ),
            },
        }

    def _validator(self):
        from mes_quant.redundancy import analyzer

        validator = getattr(
            analyzer,
            "_validate_stage_b_embedded_role_projection",
            None,
        )

        self.assertTrue(
            callable(
                validator
            ),
            (
                "analyzer."
                "_validate_stage_b_embedded_role_projection "
                "must exist"
            ),
        )

        return validator

    def test_embedded_role_validator_has_exact_keyword_only_signature(
        self,
    ):
        import inspect

        validator = self._validator()

        signature = inspect.signature(
            validator
        )

        self.assertEqual(
            tuple(
                signature.parameters
            ),
            (
                "feature_frame",
                "cell14_audit",
                "expected_cell8_assignments_sha256",
                "fold_role_columns",
                "final_test_start_year",
            ),
        )

        for parameter in (
            signature.parameters.values()
        ):
            self.assertEqual(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

    def test_valid_embedded_development_role_projection_passes(
        self,
    ):
        validator = self._validator()

        result = validator(
            feature_frame=(
                self._feature_frame()
            ),
            cell14_audit=(
                self._cell14_audit()
            ),
            expected_cell8_assignments_sha256=(
                self._cell8_sha()
            ),
            fold_role_columns=list(
                self._fold_columns()
            ),
            final_test_start_year=2025,
        )

        self.assertTrue(
            result[
                "embedded_role_projection_valid"
            ]
        )

        self.assertEqual(
            result[
                "feature_row_count"
            ],
            3,
        )

        self.assertEqual(
            result[
                "cell8_assignment_rows_opened"
            ],
            0,
        )

        self.assertEqual(
            result[
                "final_test_rows_opened"
            ],
            0,
        )

    def test_embedded_projection_rejects_duplicate_decision_id(
        self,
    ):
        frame = self._feature_frame()

        frame.loc[
            2,
            "decision_id",
        ] = "D2"

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            self._validator()(
                feature_frame=frame,
                cell14_audit=(
                    self._cell14_audit()
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_embedded_projection_rejects_missing_fold_role_column(
        self,
    ):
        frame = (
            self._feature_frame()
            .drop(
                columns=[
                    "role_wf_2023",
                ]
            )
        )

        with self.assertRaises(
            (ValueError, RuntimeError)
        ):
            self._validator()(
                feature_frame=frame,
                cell14_audit=(
                    self._cell14_audit()
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_embedded_projection_rejects_final_test_feature_row(
        self,
    ):
        frame = self._feature_frame()

        frame.loc[
            2,
            "decision_time",
        ] = "2025-01-02T15:00:00Z"

        with self.assertRaises(
            RuntimeError
        ):
            self._validator()(
                feature_frame=frame,
                cell14_audit=(
                    self._cell14_audit()
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_embedded_projection_rejects_non_development_partition(
        self,
    ):
        frame = self._feature_frame()

        frame.loc[
            2,
            "outer_partition",
        ] = "FINAL_TEST"

        with self.assertRaises(
            RuntimeError
        ):
            self._validator()(
                feature_frame=frame,
                cell14_audit=(
                    self._cell14_audit()
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_embedded_projection_rejects_cell8_provenance_hash_mismatch(
        self,
    ):
        with self.assertRaises(
            RuntimeError
        ):
            self._validator()(
                feature_frame=(
                    self._feature_frame()
                ),
                cell14_audit=(
                    self._cell14_audit(
                        cell8_sha=(
                            "f" * 64
                        )
                    )
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_embedded_projection_rejects_physical_development_row_count_mismatch(
        self,
    ):
        with self.assertRaises(
            RuntimeError
        ):
            self._validator()(
                feature_frame=(
                    self._feature_frame()
                ),
                cell14_audit=(
                    self._cell14_audit(
                        rows=2,
                    )
                ),
                expected_cell8_assignments_sha256=(
                    self._cell8_sha()
                ),
                fold_role_columns=list(
                    self._fold_columns()
                ),
                final_test_start_year=2025,
            )

    def test_run_stage_b_uses_embedded_role_projection_not_cell8_reconciliation(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        source = inspect.getsource(
            analyzer.run_stage_b
        )

        self.assertIn(
            "_validate_stage_b_embedded_role_projection(",
            source,
        )

        self.assertNotIn(
            "_validate_stage_b_canonical_data_reconciliation(",
            source,
        )

        self.assertNotIn(
            "Cell8 assignment Parquet bytes",
            source,
        )

    def test_release_binding_marks_cell8_assignments_provenance_only(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        source = inspect.getsource(
            analyzer._validate_stage_b_release_manifest_binding
        )

        self.assertIn(
            "provenance_only_artifact_ids",
            source,
        )

        self.assertIn(
            "cell8_assignments",
            source,
        )





# STEP_13G3B3B_CANONICAL_REGISTRY_COMPATIBILITY_SPEC


class StageBCanonicalRegistryCompatibilitySpecificationTests(
    unittest.TestCase
):
    @staticmethod
    def _canonical_registry_frame():
        import io
        import json

        import pandas as pd

        from pathlib import Path

        root = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        release = json.loads(
            (
                root
                / "manifests"
                / "releases"
                / "cell14_local_release_v1.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        registry_path = (
            root
            / release[
                "runs"
            ][
                "canonical"
            ][
                "artifacts"
            ][
                "registry"
            ][
                "file"
            ]
        )

        return pd.read_csv(
            io.BytesIO(
                registry_path.read_bytes()
            )
        )

    def test_frozen_canonical_cell14_registry_is_accepted_without_metadata_rewrite(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        registry = (
            self._canonical_registry_frame()
        )

        self.assertEqual(
            len(
                registry
            ),
            29,
        )

        self.assertIn(
            "feature_name",
            registry.columns,
        )

        fixed = registry.loc[
            registry[
                "lookback_mode"
            ].eq(
                "FIXED"
            )
        ]

        self.assertTrue(
            fixed[
                "lookback_start_rule"
            ]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
            .any(),
            (
                "The canonical control must exercise "
                "the FIXED non-empty start-rule case."
            ),
        )

        # Faithful schema adaptation only:
        # feature_name -> feature.
        #
        # No canonical lookback metadata is rewritten,
        # nulled, normalized away, or invented.
        rows = (
            registry.rename(
                columns={
                    "feature_name": "feature",
                }
            )
            .to_dict(
                orient="records"
            )
        )

        artifact_order = (
            registry[
                "feature_name"
            ]
            .tolist()
        )

        result = (
            analyzer._validate_canonical_feature_registry(
                registry_rows=rows,
                artifact_feature_order=artifact_order,
            )
        )

        self.assertEqual(
            result[
                "candidate_count"
            ],
            29,
        )

        self.assertTrue(
            result[
                "membership_exact"
            ]
        )

        self.assertTrue(
            result[
                "order_exact"
            ]
        )

        self.assertTrue(
            result[
                "lookback_metadata_valid"
            ]
        )

        self.assertEqual(
            result[
                "canonical_feature_order"
            ],
            tuple(
                artifact_order
            ),
        )

    def test_fixed_lookback_may_preserve_nonempty_canonical_start_rule(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        rows = []

        for index in range(
            29
        ):
            rows.append(
                {
                    "feature": (
                        f"synthetic_feature_{index:02d}"
                    ),
                    "lookback_mode": "FIXED",
                    "lookback_bars": 1,
                    "lookback_minutes": 15,
                    "lookback_start_rule": (
                        "DECISION_TIME_MINUS_LOOKBACK"
                    ),
                }
            )

        order = [
            row[
                "feature"
            ]
            for row in rows
        ]

        result = (
            analyzer._validate_canonical_feature_registry(
                registry_rows=rows,
                artifact_feature_order=order,
            )
        )

        self.assertTrue(
            result[
                "lookback_metadata_valid"
            ]
        )

        self.assertEqual(
            result[
                "canonical_feature_order"
            ],
            tuple(
                order
            ),
        )




# STEP_13G3B3_PHASE0_PRODUCTION_ORCHESTRATION_RED_SPEC


class StageBPhaseASemanticIntegrationSpecificationTests(
    unittest.TestCase
):
    @staticmethod
    def _helper():
        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase_a",
            None,
        )

        return helper

    @staticmethod
    def _source():
        import inspect

        helper = (
            StageBPhaseASemanticIntegrationSpecificationTests
            ._helper()
        )

        if not callable(helper):
            raise AssertionError(
                "analyzer._run_stage_b_phase_a must exist"
            )

        return inspect.getsource(
            helper
        )

    def test_phase_a_boundary_exists_with_keyword_only_inputs(
        self,
    ):
        import inspect

        helper = self._helper()

        self.assertTrue(
            callable(helper),
            "analyzer._run_stage_b_phase_a must exist",
        )

        signature = inspect.signature(
            helper
        )

        self.assertEqual(
            list(
                signature.parameters
            ),
            [
                "feature_frame",
                "semantic_registry",
                "phase0",
            ],
        )

        for parameter in (
            signature.parameters.values()
        ):
            self.assertEqual(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

    def test_phase_a_validates_semantic_registry_before_dispatch(
        self,
    ):
        source = self._source()

        validate_pos = source.find(
            "validate_semantic_registry("
        )

        dispatch_pos = source.find(
            '["implementation_key"]'
        )

        if dispatch_pos < 0:
            dispatch_pos = source.find(
                "['implementation_key']"
            )

        self.assertGreaterEqual(
            validate_pos,
            0,
        )

        self.assertGreater(
            dispatch_pos,
            validate_pos,
        )

    def test_phase_a_derives_protected_features_from_registry(
        self,
    ):
        source = self._source()

        self.assertEqual(
            source.count(
                "derive_protected_features("
            ),
            1,
        )

        self.assertIn(
            '"protected_features"',
            source,
        )

    def test_phase_a_executes_train_per_fold_only(
        self,
    ):
        source = self._source()

        self.assertIn(
            "_contract.FOLD_ROLE_COLUMNS",
            source,
        )

        self.assertIn(
            "get_train_mask(",
            source,
        )

        self.assertIn(
            "for fold_role_column in",
            source,
        )

    def test_phase_a_dispatches_from_registry_implementation_key(
        self,
    ):
        source = self._source()

        self.assertTrue(
            (
                'entry["implementation_key"]'
                in source
            )
            or (
                "entry['implementation_key']"
                in source
            )
        )

        self.assertIn(
            "callable",
            source,
        )

        self.assertIn(
            "raise RuntimeError",
            source,
        )

    def test_phase_a_requires_exact_semantic_checks_to_pass(
        self,
    ):
        source = self._source()

        exact_types = (
            "EXACT_LINEAR_DERIVED_IDENTITY",
            "EXACT_NONLINEAR_DERIVED_REPRESENTATION",
            "EXACT_AFFINE_DERIVED_IDENTITY",
            "EXACT_AFFINE_DEPENDENCY",
            "PAIRED_NONLINEAR_REPRESENTATION",
        )

        for check_type in exact_types:
            self.assertIn(
                repr(check_type),
                source,
            )

        self.assertIn(
            "identity_pass",
            source,
        )

        self.assertIn(
            "raise RuntimeError",
            source,
        )

    def test_phase_a_empirical_near_identity_is_evidence_only(
        self,
    ):
        source = self._source()

        self.assertIn(
            repr(
                "EMPIRICAL_NEAR_IDENTITY"
            ),
            source,
        )

        self.assertIn(
            "automatic_decision",
            source,
        )

        self.assertIn(
            "EMPIRICAL_EVIDENCE_ONLY",
            source,
        )

    def test_phase_a_returns_fold_results_and_protected_set(
        self,
    ):
        source = self._source()

        required_tokens = (
            '"phase_a_semantic_valid"',
            '"semantic_results_by_fold"',
            '"protected_features"',
        )

        for token in required_tokens:
            self.assertIn(
                token,
                source,
            )

    def test_phase_a_contains_no_data_io_imputation_or_row_drop(
        self,
    ):
        source = self._source()

        forbidden = (
            "read_parquet",
            "read_csv",
            "read_bytes",
            "read_text",
            "to_parquet",
            "to_csv",
            "fillna(",
            "ffill(",
            "bfill(",
            "interpolate(",
            "dropna(",
            ".drop(",
            "open(",
        )

        for operation in forbidden:
            self.assertNotIn(
                operation,
                source,
            )

    def test_phase_a_requires_green_phase0_and_sealed_final_test(
        self,
    ):
        source = self._source()

        self.assertIn(
            "phase0_boundary_valid",
            source,
        )

        self.assertIn(
            "final_test_rows_opened",
            source,
        )

        self.assertIn(
            "raise RuntimeError",
            source,
        )

class StageBPhase0FullOrchestrationSpecificationTests(
    unittest.TestCase
):
    SHARED_240M = (
        "momentum_log_240m",
        "realized_vol_240m",
        "volume_ratio_prev_240m",
        "return_autocorr_lag1_240m",
        "sign_entropy_240m",
    )

    @staticmethod
    def _phase0_source():
        import inspect

        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase0",
            None,
        )

        if not callable(
            helper
        ):
            raise AssertionError(
                "analyzer._run_stage_b_phase0 must exist"
            )

        return inspect.getsource(
            helper
        )

    def test_phase0_calls_canonical_registry_validator(
        self,
    ):
        source = self._phase0_source()

        self.assertEqual(
            source.count(
                "_validate_canonical_feature_registry("
            ),
            1,
        )

    def test_phase0_calls_forbidden_input_validator(
        self,
    ):
        source = self._phase0_source()

        self.assertEqual(
            source.count(
                "_validate_forbidden_inputs("
            ),
            1,
        )

    def test_phase0_locked_order_registry_then_forbidden_then_coverage(
        self,
    ):
        source = self._phase0_source()

        registry_pos = source.find(
            "_validate_canonical_feature_registry("
        )

        forbidden_pos = source.find(
            "_validate_forbidden_inputs("
        )

        coverage_pos = source.find(
            "_compute_stage_b_phase0_coverage("
        )

        self.assertGreaterEqual(
            registry_pos,
            0,
        )

        self.assertGreater(
            forbidden_pos,
            registry_pos,
        )

        self.assertGreater(
            coverage_pos,
            forbidden_pos,
        )

    def test_phase0_missingness_runs_after_coverage(
        self,
    ):
        source = self._phase0_source()

        coverage_pos = source.find(
            "_compute_stage_b_phase0_coverage("
        )

        missingness_pos = source.find(
            "_reconcile_full29_missingness("
        )

        self.assertGreaterEqual(
            coverage_pos,
            0,
        )

        self.assertGreater(
            missingness_pos,
            coverage_pos,
        )

    def test_phase0_uses_locked_missingness_feature_authorities(
        self,
    ):
        source = self._phase0_source()

        for feature in self.SHARED_240M:
            self.assertIn(
                repr(
                    feature
                ),
                source,
            )

        self.assertIn(
            repr(
                "session_vwap_proxy_deviation"
            ),
            source,
        )

        self.assertIn(
            repr(
                "feature_status"
            ),
            source,
        )

    def test_phase0_computes_zero_variance_for_exact_three_folds(
        self,
    ):
        source = self._phase0_source()

        self.assertEqual(
            source.count(
                "compute_zero_variance_diagnostics("
            ),
            1,
        )

        self.assertIn(
            "for fold_role_column in",
            source,
        )

        self.assertIn(
            "_contract.FOLD_ROLE_COLUMNS",
            source,
        )

    def test_phase0_fails_closed_on_invalid_missingness_reconciliation(
        self,
    ):
        source = self._phase0_source()

        self.assertIn(
            "component_reconciliation_valid",
            source,
        )

        self.assertIn(
            "raise RuntimeError",
            source,
        )

    def test_phase0_returns_missingness_and_zero_variance_diagnostics(
        self,
    ):
        source = self._phase0_source()

        required_return_tokens = (
            '"missingness_reconciliation"',
            '"zero_variance_diagnostics"',
        )

        for token in required_return_tokens:
            self.assertIn(
                token,
                source,
            )

    def test_phase0_full_orchestration_contains_no_imputation_or_row_drop(
        self,
    ):
        source = self._phase0_source()

        forbidden_operations = (
            "fillna(",
            "ffill(",
            "bfill(",
            "interpolate(",
            "dropna(",
            ".drop(",
        )

        for operation in forbidden_operations:
            self.assertNotIn(
                operation,
                source,
            )

class StageBPhase0ProductionOrchestrationSpecificationTests(
    unittest.TestCase
):
    CANONICAL_FEATURES = (
        "ret_log_15m_lag0",
        "ret_log_15m_lag1",
        "ret_log_15m_lag2",
        "ret_log_15m_lag3",
        "momentum_log_60m",
        "momentum_log_120m",
        "momentum_log_240m",
        "realized_vol_60m",
        "realized_vol_120m",
        "realized_vol_240m",
        "bar_log_range_15m",
        "bar_log_body_15m",
        "bar_close_location",
        "log1p_volume_15m",
        "volume_ratio_prev_60m",
        "volume_ratio_prev_240m",
        "session_vwap_proxy_deviation",
        "return_autocorr_lag1_240m",
        "sign_entropy_240m",
        "minutes_since_nyse_open",
        "minutes_to_horizon_safe_close",
        "decision_slot_sin",
        "decision_slot_cos",
        "weekday_0",
        "weekday_1",
        "weekday_2",
        "weekday_3",
        "weekday_4",
        "early_close_session",
    )

    FOLD_COLUMNS = (
        "role_wf_2022",
        "role_wf_2023",
        "role_wf_2024",
    )

    @classmethod
    def _coverage_frame(
        cls,
        *,
        low_2019=False,
    ):
        import numpy as np
        import pandas as pd

        rows = 10

        data = {
            feature: np.arange(
                rows,
                dtype="float64",
            )
            + index
            for index, feature in enumerate(
                cls.CANONICAL_FEATURES
            )
        }

        frame = pd.DataFrame(
            data
        )

        frame[
            "decision_id"
        ] = [
            f"D{i:02d}"
            for i in range(
                rows
            )
        ]

        frame[
            "decision_time"
        ] = pd.to_datetime(
            (
                [
                    "2019-06-03T15:00:00Z",
                    "2019-06-04T15:00:00Z",
                    "2019-06-05T15:00:00Z",
                    "2019-06-06T15:00:00Z",
                    "2019-06-07T15:00:00Z",
                ]
                + [
                    "2024-06-03T15:00:00Z",
                    "2024-06-04T15:00:00Z",
                    "2024-06-05T15:00:00Z",
                    "2024-06-06T15:00:00Z",
                    "2024-06-07T15:00:00Z",
                ]
            ),
            utc=True,
        )

        for fold in cls.FOLD_COLUMNS:
            frame[
                fold
            ] = (
                ["TRAIN"] * 5
                + ["VALIDATION"] * 5
            )

        if low_2019:
            frame.loc[
                0,
                cls.CANONICAL_FEATURES[
                    0
                ],
            ] = np.nan

        frame[
            "feature_row_usable"
        ] = (
            frame[
                list(
                    cls.CANONICAL_FEATURES
                )
            ]
            .notna()
            .all(
                axis=1
            )
        )

        frame[
            "feature_status"
        ] = np.where(
            frame[
                "feature_row_usable"
            ],
            "PASS",
            "PARTIAL_LOOKBACK_BAR",
        )

        return frame

    def _coverage_helper(self):
        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_compute_stage_b_phase0_coverage",
            None,
        )

        self.assertTrue(
            callable(
                helper
            ),
            (
                "analyzer."
                "_compute_stage_b_phase0_coverage "
                "must exist"
            ),
        )

        return helper

    def test_phase0_coverage_helper_has_exact_keyword_only_signature(
        self,
    ):
        import inspect

        helper = self._coverage_helper()

        signature = inspect.signature(
            helper
        )

        self.assertEqual(
            tuple(
                signature.parameters
            ),
            (
                "feature_frame",
                "canonical_features",
                "fold_role_columns",
            ),
        )

        for parameter in (
            signature.parameters.values()
        ):
            self.assertEqual(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

    def test_fold_coverage_is_recomputed_from_embedded_roles(
        self,
    ):
        result = self._coverage_helper()(
            feature_frame=(
                self._coverage_frame(
                    low_2019=True,
                )
            ),
            canonical_features=list(
                self.CANONICAL_FEATURES
            ),
            fold_role_columns=list(
                self.FOLD_COLUMNS
            ),
        )

        self.assertEqual(
            result[
                "fold_train_rows"
            ],
            {
                fold: 5
                for fold
                in self.FOLD_COLUMNS
            },
        )

        self.assertEqual(
            result[
                "fold_complete_rows"
            ],
            {
                fold: 4
                for fold
                in self.FOLD_COLUMNS
            },
        )

    def test_yearly_coverage_uses_only_applicable_train_history(
        self,
    ):
        result = self._coverage_helper()(
            feature_frame=(
                self._coverage_frame(
                    low_2019=True,
                )
            ),
            canonical_features=list(
                self.CANONICAL_FEATURES
            ),
            fold_role_columns=list(
                self.FOLD_COLUMNS
            ),
        )

        self.assertEqual(
            result[
                "yearly_coverage"
            ],
            {
                2019: 0.8,
            },
        )

        self.assertNotIn(
            2024,
            result[
                "yearly_coverage"
            ],
        )

    def test_yearly_denominator_keeps_unusable_train_decisions(
        self,
    ):
        result = self._coverage_helper()(
            feature_frame=(
                self._coverage_frame(
                    low_2019=True,
                )
            ),
            canonical_features=list(
                self.CANONICAL_FEATURES
            ),
            fold_role_columns=list(
                self.FOLD_COLUMNS
            ),
        )

        self.assertEqual(
            result[
                "yearly_train_rows"
            ],
            {
                2019: 5,
            },
        )

        self.assertEqual(
            result[
                "yearly_complete_rows"
            ],
            {
                2019: 4,
            },
        )

        self.assertAlmostEqual(
            result[
                "yearly_coverage"
            ][
                2019
            ],
            4 / 5,
        )

    def test_phase0_private_orchestrator_signature_has_no_assignments_frame(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase0",
            None,
        )

        self.assertTrue(
            callable(
                helper
            )
        )

        signature = inspect.signature(
            helper
        )

        self.assertEqual(
            tuple(
                signature.parameters
            ),
            (
                "feature_frame",
                "registry_frame",
                "opened_fields",
                "opened_cells",
                "final_test_rows_opened",
                "yearly_review_acknowledged",
            ),
        )

        self.assertNotIn(
            "assignments_frame",
            signature.parameters,
        )

    def test_phase0_orchestrator_contains_no_artifact_io_or_assignment_frame(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase0",
            None,
        )

        self.assertTrue(
            callable(
                helper
            )
        )

        source = inspect.getsource(
            helper
        )

        self.assertNotIn(
            "assignments_frame",
            source,
        )

        for forbidden in (
            "read_parquet",
            "read_csv",
            "read_bytes",
            "read_text",
            "write_bytes",
            "write_text",
            "to_parquet",
            "to_csv",
            "open(",
        ):
            self.assertNotIn(
                forbidden,
                source,
            )

    def test_phase0_orchestrator_consumes_embedded_role_coverage_helper(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase0",
            None,
        )

        self.assertTrue(
            callable(
                helper
            )
        )

        source = inspect.getsource(
            helper
        )

        self.assertEqual(
            source.count(
                "_compute_stage_b_phase0_coverage("
            ),
            1,
        )

    def test_final_test_firewall_precedes_coverage_computation(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        helper = getattr(
            analyzer,
            "_run_stage_b_phase0",
            None,
        )

        self.assertTrue(
            callable(
                helper
            )
        )

        source = inspect.getsource(
            helper
        )

        firewall_position = source.find(
            "final_test_rows_opened"
        )

        coverage_position = source.find(
            "_compute_stage_b_phase0_coverage("
        )

        self.assertGreaterEqual(
            firewall_position,
            0,
        )

        self.assertGreater(
            coverage_position,
            firewall_position,
        )

    def test_run_stage_b_validates_embedded_projection_before_phase0(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        source = inspect.getsource(
            analyzer.run_stage_b
        )

        projection = source.find(
            "_validate_stage_b_embedded_role_projection("
        )

        phase0 = source.find(
            "_run_stage_b_phase0("
        )

        self.assertGreaterEqual(
            projection,
            0,
        )

        self.assertGreater(
            phase0,
            projection,
        )

    def test_run_stage_b_has_no_old_cell8_dataframe_reconciliation_path(
        self,
    ):
        import inspect

        from mes_quant.redundancy import analyzer

        source = inspect.getsource(
            analyzer.run_stage_b
        )

        self.assertNotIn(
            "_validate_stage_b_canonical_data_reconciliation(",
            source,
        )

        self.assertNotIn(
            "cell8_assignments=",
            source,
        )

        self.assertNotIn(
            "Cell8 assignment Parquet bytes",
            source,
        )

class StageBPhaseADecisionBridgeRedSpecificationTests(
    unittest.TestCase
):
    """Issue #2 RED contract for the missing Phase-A decision bridge."""

    FOLD_COLUMNS = (
        "role_wf_2022",
        "role_wf_2023",
        "role_wf_2024",
    )

    METADATA_FIELDS = (
        "feature",
        "lookback_mode",
        "lookback_bars",
        "lookback_minutes",
        "lookback_start_rule",
    )

    @classmethod
    def setUpClass(cls) -> None:
        from mes_quant.redundancy import analyzer

        cls.analyzer = analyzer
        cls.semantic_registry = json.loads(
            (
                PROJECT_ROOT
                / contract.SEMANTIC_REGISTRY_PATH
            ).read_text(
                encoding="utf-8"
            )
        )

        canonical = (
            StageBCanonicalRegistryCompatibilitySpecificationTests
            ._canonical_registry_frame()
            .rename(
                columns={
                    "feature_name": "feature",
                }
            )
        )

        cls.canonical_rows = canonical.to_dict(
            orient="records"
        )
        cls.canonical_features = tuple(
            canonical["feature"].tolist()
        )
        cls.canonical_metadata = tuple(
            tuple(
                row[field]
                for field in cls.METADATA_FIELDS
            )
            for row in cls.canonical_rows
        )

    @classmethod
    def _phase0_state(cls):
        validation = dict(
            cls.analyzer._validate_canonical_feature_registry(
                registry_rows=cls.canonical_rows,
                artifact_feature_order=list(
                    cls.canonical_features
                ),
            )
        )

        # Model the Group-A GREEN output so the remaining RED specs
        # isolate the still-missing Phase-A decision bridge.
        validation[
            "canonical_feature_metadata"
        ] = cls.canonical_metadata

        return {
            "phase0_boundary_valid": True,
            "final_test_rows_opened": 0,
            "canonical_features": cls.canonical_features,
            "registry_validation": validation,
        }

    @classmethod
    def _semantic_frame(
        cls,
        *,
        one_fold_lacks_weekday_dimension=False,
    ):
        import numpy as np
        import pandas as pd

        rows = 50
        index = np.arange(
            rows,
            dtype="float64",
        )
        lag0 = (
            np.sin(index / 5.0)
            / 100.0
        )
        lag1 = (
            np.cos(index / 7.0)
            / 120.0
        )
        lag2 = (
            ((index % 11.0) - 5.0)
            / 900.0
        )
        lag3 = (
            ((index % 7.0) - 3.0)
            / 700.0
        )
        weekday = (
            index.astype("int64")
            % 5
        )
        slot_angle = (
            2.0
            * np.pi
            * (
                index % 22.0
            )
            / 22.0
        )
        minutes_since_open = (
            index.astype("int64")
            % 20
        ) * 15
        early_close = (
            index.astype("int64")
            % 13
            == 0
        ).astype("int64")

        data = {
            feature: (
                index
                + float(position)
            )
            for position, feature in enumerate(
                cls.canonical_features
            )
        }
        data.update(
            {
                "ret_log_15m_lag0": lag0,
                "ret_log_15m_lag1": lag1,
                "ret_log_15m_lag2": lag2,
                "ret_log_15m_lag3": lag3,
                "momentum_log_60m": (
                    lag0
                    + lag1
                    + lag2
                    + lag3
                ),
                "realized_vol_60m": np.sqrt(
                    lag0**2
                    + lag1**2
                    + lag2**2
                    + lag3**2
                ),
                "bar_log_body_15m": (
                    lag0
                    + np.sin(index / 3.0)
                    / 100000.0
                ),
                "minutes_since_nyse_open": (
                    minutes_since_open
                ),
                "early_close_session": early_close,
                "minutes_to_horizon_safe_close": (
                    330
                    - minutes_since_open
                    - 180 * early_close
                ),
                "decision_slot_sin": np.sin(
                    slot_angle
                ),
                "decision_slot_cos": np.cos(
                    slot_angle
                ),
            }
        )

        for category in range(5):
            data[
                f"weekday_{category}"
            ] = (
                weekday == category
            ).astype("int64")

        frame = pd.DataFrame(
            data,
            columns=list(
                cls.canonical_features
            ),
        )

        for fold in cls.FOLD_COLUMNS:
            frame[fold] = "TRAIN"

        if one_fold_lacks_weekday_dimension:
            frame.loc[
                frame["weekday_4"].eq(1),
                cls.FOLD_COLUMNS[0],
            ] = "VALIDATION"

        return frame

    @classmethod
    def _run_phase_a(
        cls,
        *,
        semantic_registry=None,
        one_fold_lacks_weekday_dimension=False,
    ):
        registry = (
            cls.semantic_registry
            if semantic_registry is None
            else semantic_registry
        )

        return cls._run_phase_a_with_frame(
            feature_frame=cls._semantic_frame(
                one_fold_lacks_weekday_dimension=(
                    one_fold_lacks_weekday_dimension
                ),
            ),
            semantic_registry=registry,
        )

    @classmethod
    def _run_phase_a_with_frame(
        cls,
        *,
        feature_frame,
        semantic_registry=None,
    ):
        registry = (
            cls.semantic_registry
            if semantic_registry is None
            else semantic_registry
        )

        return cls.analyzer._run_stage_b_phase_a(
            feature_frame=feature_frame,
            semantic_registry=registry,
            phase0=cls._phase0_state(),
        )

    def _relationship(
        self,
        result,
        check_id,
    ):
        self.assertIn(
            "phase_a_relationship_decisions",
            result,
            "Phase A does not expose relationship decisions.",
        )
        matches = [
            relationship
            for relationship in result[
                "phase_a_relationship_decisions"
            ]
            if relationship["check_id"] == check_id
        ]
        self.assertEqual(
            len(matches),
            1,
            f"Expected one relationship record for {check_id}.",
        )
        return matches[0]

    def test_phase0_exposes_exact_immutable_canonical_metadata(
        self,
    ):
        import inspect

        result = (
            self.analyzer._validate_canonical_feature_registry(
                registry_rows=self.canonical_rows,
                artifact_feature_order=list(
                    self.canonical_features
                ),
            )
        )

        self.assertIn(
            "canonical_feature_metadata",
            result,
            (
                "Phase 0 validation does not expose the "
                "canonical downstream metadata snapshot."
            ),
        )
        snapshot = result[
            "canonical_feature_metadata"
        ]
        self.assertIsInstance(
            snapshot,
            tuple,
        )
        self.assertEqual(
            snapshot,
            self.canonical_metadata,
        )
        self.assertTrue(
            any(
                mode == "FIXED"
                and bars == 0
                and minutes == 0
                for (
                    _,
                    mode,
                    bars,
                    minutes,
                    _,
                ) in snapshot
            )
        )
        self.assertIn(
            (
                "session_vwap_proxy_deviation",
                "SESSION_TO_DATE",
                22,
                330,
                "NYSE_SESSION_OPEN",
            ),
            snapshot,
        )

        source = inspect.getsource(
            self.analyzer._validate_canonical_feature_registry
        )
        for feature in self.canonical_features:
            self.assertNotIn(
                repr(feature),
                source,
                (
                    "Canonical metadata must flow from the "
                    "validated rows, not a duplicated feature-name table."
                ),
            )

    def test_unknown_decision_effect_fails_closed(
        self,
    ):
        import copy

        candidate = copy.deepcopy(
            self.semantic_registry
        )
        candidate["semantic_checks"][0][
            "decision_effect"
        ] = "UNKNOWN_PHASE_A_DECISION_EFFECT"

        with self.assertRaises(
            (ValueError, RuntimeError),
            msg=(
                "An unknown semantic decision_effect must "
                "fail closed before Phase A releases state."
            ),
        ):
            self._run_phase_a(
                semantic_registry=candidate
            )

    def test_known_decision_effect_mutation_changes_resolution(
        self,
    ):
        import copy

        candidate = copy.deepcopy(
            self.semantic_registry
        )
        momentum = candidate[
            "semantic_checks"
        ][0]
        momentum[
            "check_type"
        ] = "EXACT_NONLINEAR_DERIVED_REPRESENTATION"
        momentum[
            "decision_effect"
        ] = "RETAIN_DERIVED_NONLINEAR_REPRESENTATION"
        momentum[
            "required_drop_count"
        ] = 0

        relationship = self._relationship(
            self._run_phase_a(
                semantic_registry=candidate
            ),
            "SEM_MOMENTUM_60M",
        )

        self.assertIn(
            "momentum_log_60m",
            relationship["retained_features"],
        )
        self.assertNotIn(
            "momentum_log_60m",
            relationship["dropped_features"],
        )
        self.assertEqual(
            relationship["decision_effect"],
            momentum["decision_effect"],
        )

    def test_phase_a_state_is_complete_canonical_and_registry_ordered(
        self,
    ):
        result = self._run_phase_a()

        self.assertTrue(
            result[
                "phase_a_semantic_valid"
            ]
        )
        self.assertTrue(
            result[
                "phase_a_exact_decisions_complete"
            ]
        )
        retained = tuple(
            result[
                "phase_a_retained_features"
            ]
        )
        dropped = tuple(
            result[
                "phase_a_dropped_features"
            ]
        )
        relationships = tuple(
            result[
                "phase_a_relationship_decisions"
            ]
        )
        expected_check_ids = tuple(
            entry["check_id"]
            for entry in self.semantic_registry[
                "semantic_checks"
            ]
        )
        expected_effects = tuple(
            entry["decision_effect"]
            for entry in self.semantic_registry[
                "semantic_checks"
            ]
        )

        self.assertEqual(
            tuple(
                relationship["check_id"]
                for relationship in relationships
            ),
            expected_check_ids,
        )
        self.assertEqual(
            tuple(
                relationship["decision_effect"]
                for relationship in relationships
            ),
            expected_effects,
        )

        required_fields = {
            "check_id",
            "dependency_group",
            "check_type",
            "decision_effect",
            "required_drop_count",
            "features",
            "retained_features",
            "dropped_features",
        }
        for entry, relationship in zip(
            self.semantic_registry[
                "semantic_checks"
            ],
            relationships,
            strict=True,
        ):
            self.assertTrue(
                required_fields.issubset(
                    relationship
                )
            )
            self.assertEqual(
                tuple(
                    relationship["features"]
                ),
                tuple(entry["features"]),
            )
            self.assertEqual(
                relationship[
                    "required_drop_count"
                ],
                entry["required_drop_count"],
            )

        relationship_drops = {
            feature
            for relationship in relationships
            for feature in relationship[
                "dropped_features"
            ]
        }
        expected_dropped = tuple(
            feature
            for feature in self.canonical_features
            if feature in relationship_drops
        )
        expected_retained = tuple(
            feature
            for feature in self.canonical_features
            if feature not in relationship_drops
        )
        self.assertEqual(
            dropped,
            expected_dropped,
        )
        self.assertEqual(
            retained,
            expected_retained,
        )
        self.assertEqual(
            set(retained).intersection(dropped),
            set(),
        )
        self.assertEqual(
            result["final_test_rows_opened"],
            0,
        )

    def test_relationship_order_follows_mutated_registry_order(
        self,
    ):
        import copy

        candidate = copy.deepcopy(
            self.semantic_registry
        )
        candidate[
            "semantic_checks"
        ] = list(
            reversed(
                candidate[
                    "semantic_checks"
                ]
            )
        )
        result = self._run_phase_a(
            semantic_registry=candidate
        )

        self.assertEqual(
            tuple(
                relationship["check_id"]
                for relationship in result[
                    "phase_a_relationship_decisions"
                ]
            ),
            tuple(
                entry["check_id"]
                for entry in candidate[
                    "semantic_checks"
                ]
            ),
        )

    def test_momentum_decision_drops_derived_and_protects_basis(
        self,
    ):
        result = self._run_phase_a()
        relationship = self._relationship(
            result,
            "SEM_MOMENTUM_60M",
        )
        determining = (
            "ret_log_15m_lag0",
            "ret_log_15m_lag1",
            "ret_log_15m_lag2",
            "ret_log_15m_lag3",
        )

        self.assertEqual(
            tuple(
                relationship["dropped_features"]
            ),
            ("momentum_log_60m",),
        )
        self.assertEqual(
            tuple(
                relationship["retained_features"]
            ),
            determining,
        )
        self.assertEqual(
            relationship["required_drop_count"],
            1,
        )
        self.assertTrue(
            set(determining).issubset(
                result["protected_features"]
            )
        )
        self.assertTrue(
            all(
                relationship["feature_states"][feature]
                == "SEMANTIC_BASIS_PROTECTED"
                for feature in determining
            )
        )

    def test_realized_vol_decision_keeps_nonlinear_representation(
        self,
    ):
        relationship = self._relationship(
            self._run_phase_a(),
            "SEM_REALIZED_VOL_60M",
        )

        self.assertIn(
            "realized_vol_60m",
            relationship["retained_features"],
        )
        self.assertNotIn(
            "realized_vol_60m",
            relationship["dropped_features"],
        )
        self.assertEqual(
            relationship["required_drop_count"],
            0,
        )

    def test_horizon_decision_drops_derived_and_protects_basis(
        self,
    ):
        result = self._run_phase_a()
        relationship = self._relationship(
            result,
            "SEM_HORIZON_SAFE_CLOSE",
        )
        determining = (
            "minutes_since_nyse_open",
            "early_close_session",
        )

        self.assertEqual(
            tuple(
                relationship["dropped_features"]
            ),
            ("minutes_to_horizon_safe_close",),
        )
        self.assertEqual(
            tuple(
                relationship["retained_features"]
            ),
            determining,
        )
        self.assertEqual(
            relationship["required_drop_count"],
            1,
        )
        self.assertTrue(
            set(determining).issubset(
                result["protected_features"]
            )
        )

    def test_weekday_decision_keeps_four_dimensions_by_locked_priority(
        self,
    ):
        result = self._run_phase_a()
        relationship = self._relationship(
            result,
            "SEM_WEEKDAY_ONEHOT",
        )
        weekdays = tuple(
            f"weekday_{index}"
            for index in range(5)
        )
        retained = tuple(
            relationship["retained_features"]
        )
        dropped = tuple(
            relationship["dropped_features"]
        )

        self.assertEqual(
            len(retained),
            4,
        )
        self.assertEqual(
            len(dropped),
            1,
        )
        self.assertEqual(
            set(retained).union(dropped),
            set(weekdays),
        )
        self.assertEqual(
            relationship[
                "information_dimension"
            ],
            4,
        )
        self.assertTrue(
            set(weekdays).isdisjoint(
                result["protected_features"]
            )
        )

        priority = relationship[
            "retention_priority_evidence"
        ]
        self.assertEqual(
            tuple(
                priority["ordered_features"]
            ),
            weekdays,
        )
        self.assertIn(
            "minimum_train_fold_availability",
            priority,
        )
        self.assertIn(
            "canonical_lookback_metadata",
            priority,
        )
        self.assertIn(
            "canonical_feature_order",
            priority,
        )

    def test_decision_slot_cycle_keeps_both_components(
        self,
    ):
        relationship = self._relationship(
            self._run_phase_a(),
            "SEM_DECISION_SLOT_CYCLE",
        )
        pair = (
            "decision_slot_sin",
            "decision_slot_cos",
        )

        self.assertEqual(
            tuple(
                relationship["retained_features"]
            ),
            pair,
        )
        self.assertEqual(
            tuple(
                relationship["dropped_features"]
            ),
            (),
        )
        self.assertEqual(
            relationship["required_drop_count"],
            0,
        )

    def test_empirical_relation_remains_evidence_only_until_phase_c(
        self,
    ):
        result = self._run_phase_a()
        relationship = self._relationship(
            result,
            "EMP_LAG0_BAR_BODY",
        )

        self.assertEqual(
            tuple(
                relationship["dropped_features"]
            ),
            (),
        )
        self.assertEqual(
            relationship["required_drop_count"],
            None,
        )
        self.assertIn(
            "bar_log_body_15m",
            relationship["unresolved_features"],
        )
        self.assertIn(
            "ret_log_15m_lag0",
            result["protected_features"],
        )
        self.assertFalse(
            relationship.get(
                "phase_c_executed",
                False,
            )
        )

    def test_weekday_releases_one_basis_robust_in_all_train_folds(
        self,
    ):
        relationship = self._relationship(
            self._run_phase_a(),
            "SEM_WEEKDAY_ONEHOT",
        )
        retained = tuple(
            relationship["retained_features"]
        )
        diagnostics = relationship[
            "fold_rank_diagnostics"
        ]

        self.assertEqual(
            tuple(diagnostics),
            self.FOLD_COLUMNS,
        )
        self.assertEqual(
            len(retained),
            4,
        )
        for fold in self.FOLD_COLUMNS:
            self.assertEqual(
                tuple(
                    diagnostics[fold][
                        "retained_features"
                    ]
                ),
                retained,
            )
            self.assertEqual(
                diagnostics[fold][
                    "original_rank"
                ],
                4,
            )
            self.assertEqual(
                diagnostics[fold][
                    "retained_rank"
                ],
                4,
            )

    def test_weekday_fails_closed_if_any_train_fold_loses_dimension(
        self,
    ):
        with self.assertRaises(
            RuntimeError,
            msg=(
                "One global weekday basis must fail closed "
                "when any required TRAIN fold cannot preserve "
                "the four-dimensional semantic group."
            ),
        ):
            self._run_phase_a(
                one_fold_lacks_weekday_dimension=True
            )

    def test_validation_rows_cannot_influence_phase_a_basis_choice(
        self,
    ):
        import numpy as np

        baseline = self._semantic_frame()
        validation_rows = baseline.index[-10:]
        for fold in self.FOLD_COLUMNS:
            baseline.loc[
                validation_rows,
                fold,
            ] = "VALIDATION"

        mutated_validation = baseline.copy()
        mutated_validation.loc[
            validation_rows,
            [
                "weekday_0",
                "weekday_1",
                "weekday_2",
                "weekday_3",
            ],
        ] = np.nan

        baseline_relationship = self._relationship(
            self._run_phase_a_with_frame(
                feature_frame=baseline
            ),
            "SEM_WEEKDAY_ONEHOT",
        )
        mutated_relationship = self._relationship(
            self._run_phase_a_with_frame(
                feature_frame=mutated_validation
            ),
            "SEM_WEEKDAY_ONEHOT",
        )

        for field in (
            "retained_features",
            "dropped_features",
            "retention_priority_evidence",
        ):
            self.assertEqual(
                baseline_relationship[field],
                mutated_relationship[field],
                (
                    "Validation-only values must not influence "
                    "Phase-A semantic basis decisions."
                ),
            )


class StageBGenericRankAuthorityV12SpecificationTests(
    unittest.TestCase
):
    """Issue #9 proof that generic rank discovery has no DROP authority."""

    def test_generic_classifier_is_target_blind_and_has_no_basis_selector(
        self,
    ) -> None:
        import inspect

        from mes_quant.redundancy import analyzer

        classifier = analyzer.classify_generic_rank_discovery
        signature = inspect.signature(classifier)

        self.assertEqual(
            tuple(signature.parameters),
            (
                "component_features",
                "discovery_status",
            ),
        )
        self.assertTrue(
            all(
                parameter.kind
                is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

        source = inspect.getsource(classifier).lower()
        self.assertNotIn("retention_order", source)
        self.assertNotIn("selected_basis", source)
        self.assertFalse(
            hasattr(analyzer, "resolve_generic_group_rank_verification")
        )
        self.assertFalse(
            hasattr(analyzer, "_prefer_retention_candidate")
        )

        forbidden = (
            "read_parquet",
            "read_csv",
            "read_bytes",
            "read_text",
            "to_parquet",
            "to_csv",
            "open(",
            "get_train_mask(",
            "role_wf_",
            "fillna(",
            "ffill(",
            "bfill(",
            "interpolate(",
            "dropna(",
            "target",
            "label",
            "future_return",
            "pnl",
            "model_score",
        )
        for operation in forbidden:
            self.assertNotIn(operation, source)

    def test_phase_a_basis_primitive_emits_evidence_not_drop_decision(
        self,
    ) -> None:
        import numpy as np
        import pandas as pd

        from mes_quant.redundancy import analyzer

        categories = np.tile(
            np.arange(5),
            10,
        )
        features = [
            f"weekday_{index}"
            for index in range(5)
        ]
        frame = pd.DataFrame(
            {
                feature: (
                    categories == index
                ).astype("float64")
                for index, feature in enumerate(
                    features
                )
            }
        )

        result = analyzer._select_phase_a_semantic_rank_basis(
            frame=frame,
            feature_columns=features,
            semantic_reference_order=features,
        )

        self.assertEqual(result["original_rank"], 4)
        self.assertEqual(
            tuple(result["retained_features"]),
            tuple(features[:4]),
        )
        self.assertEqual(
            tuple(result["excluded_features"]),
            (features[4],),
        )
        self.assertNotIn("dropped_features", result)
        self.assertNotIn("base_decision", result)
        self.assertEqual(
            result["final_retained_rank"],
            result["original_rank"],
        )

    def test_phase_a_basis_requires_explicit_registry_authority(
        self,
    ) -> None:
        from mes_quant.redundancy import analyzer

        with self.assertRaisesRegex(
            RuntimeError,
            "requires explicit locked registry authority",
        ):
            analyzer._resolve_phase_a_undirected_semantic_basis(
                feature_frame=None,
                entry={
                    "check_type": "EXACT_AFFINE_DEPENDENCY",
                    "decision_effect": "KEEP_ALL",
                },
                canonical_features=(),
                protected_features=(),
                metadata_by_feature={},
                fold_role_columns=(),
            )


if __name__ == "__main__":
    unittest.main()

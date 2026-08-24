from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType
from typing import NoReturn

from mes_quant.exploration.test2_run_context import (
    FIT_STATUS_BLOCKED_FIT_NOT_AUTHORIZED,
    FIT_STATUS_SKIPPED_INCONCLUSIVE_UNDERPOWERED,
)

# ---------------------------------------------------------------------------
# Frozen G3 gate identity
# ---------------------------------------------------------------------------

G3_AUTHORIZED_BASE_COMMIT = "17925958fd1efcb6c9c1c52558656b951d27c850"
G3_BRANCH = "research/test2-g3-pre-fit-v1"

G3I_GATE_LITERAL = "G3I_CODE_ONLY"
G3P_GATE_LITERAL = "G3P_PRE_FIT_EVIDENCE_ONLY"
G3F_GATE_LITERAL = "G3F_CONDITIONAL_FIT"

G3I_STATUS = "OWNER_AUTHORIZED_CODE_ONLY"
G3P_STATUS = "OWNER_AUTHORIZATION_REQUIRED_BEFORE_EXECUTION"
G3F_STATUS = "NOT_AUTHORIZED"

EXPECTED_DECODED_ROW_COUNT = 2_551_123
EXPECTED_DECODED_TIMESTAMP_MIN_UTC = "2019-05-05T22:00:00+00:00"
EXPECTED_DECODED_TIMESTAMP_MAX_UTC = "2026-07-31T20:59:00+00:00"

# The complete G3-I patch surface measured against `G3_AUTHORIZED_BASE_COMMIT`.
# Every other tracked file — including `test2_target.py`, `test2_stats.py`,
# `test2_evaluation.py`, and `test2_metadata_preflight.py` — must stay
# byte-identical to the authorized base.
G3I_ALLOWED_CHANGED_FILES = frozenset(
    {
        "docs/research/TEST2_G3_PACKAGE_V1.md",
        "src/mes_quant/exploration/test2_decode.py",
        "src/mes_quant/exploration/test2_g3_contract.py",
        "src/mes_quant/exploration/test2_g3_pre_fit.py",
        "src/mes_quant/exploration/test2_l1_harness.py",
        "src/mes_quant/exploration/test2_run_context.py",
        "tests/test_test2_decode.py",
        "tests/test_test2_g3_pre_fit.py",
        "tests/test_test2_l1_harness.py",
        "tests/test_test2_run_context.py",
        "tools/run_test2_g3p_pre_fit.py",
    }
)

# ---------------------------------------------------------------------------
# Tracked documentation bindings
# ---------------------------------------------------------------------------

TEST2_PROTOCOL_V1_PATH = "docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md"
TEST2_PROTOCOL_REVIEW_RECORD_PATH = (
    "docs/research/TEST2_PATH_AWARE_PROTOCOL_V1_REVIEW_RECORD.md"
)
TEST2_G1_PACKAGE_PATH = "docs/research/TEST2_G1_ADAPTER_HARNESS_PACKAGE_V1.md"
TEST2_G2_PACKAGE_PATH = "docs/research/TEST2_G2_METADATA_PREFLIGHT_PACKAGE_V1.md"
TEST2_G3_PACKAGE_PATH = "docs/research/TEST2_G3_PACKAGE_V1.md"

PINNED_DOC_SHA256 = MappingProxyType(
    {
        TEST2_PROTOCOL_V1_PATH: (
            "7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105"
        ),
        TEST2_PROTOCOL_REVIEW_RECORD_PATH: (
            "f05658314f62c84755077e8b34e3e6c96703d336d5372d1681ab3472160b7b3c"
        ),
        TEST2_G1_PACKAGE_PATH: (
            "20795c338258662ecbc26236292ef312e30f7d039f64eaf4fa375e56fb37da1d"
        ),
        TEST2_G2_PACKAGE_PATH: (
            "66263581113e37b70a8574ee1b75178573e8ac03069a3953ca5f81998dbb8ac0"
        ),
        TEST2_G3_PACKAGE_PATH: (
            "244873337f219ffac9334b81b463c22ade2e53f7c447bbcac13d777c15f64608"
        ),
    }
)

PINNED_DOC_BINDING_STATUS = "PINNED_BEFORE_EXECUTION"

# ---------------------------------------------------------------------------
# Support-gate and disposition literals
# ---------------------------------------------------------------------------

SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED = "SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED"
SUPPORT_GATE_FAIL_UNDERPOWERED = "SUPPORT_GATE_FAIL_INCONCLUSIVE_UNDERPOWERED"

DISPOSITION_DEFERRED_PENDING_G3F = "DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION"
DISPOSITION_INCONCLUSIVE_UNDERPOWERED = "INCONCLUSIVE_UNDERPOWERED"

# Support outcome -> (support gate status, disposition, fit status).
SUPPORT_OUTCOMES = MappingProxyType(
    {
        True: (
            SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
            DISPOSITION_DEFERRED_PENDING_G3F,
            FIT_STATUS_BLOCKED_FIT_NOT_AUTHORIZED,
        ),
        False: (
            SUPPORT_GATE_FAIL_UNDERPOWERED,
            DISPOSITION_INCONCLUSIVE_UNDERPOWERED,
            FIT_STATUS_SKIPPED_INCONCLUSIVE_UNDERPOWERED,
        ),
    }
)

# ---------------------------------------------------------------------------
# Cell 12 reconciliation contract
# ---------------------------------------------------------------------------

CELL12_STATUS_USABLE = "USABLE"
CELL12_STATUS_PATH_INTEGRITY_FAILURE = "PATH_INTEGRITY_FAILURE"
CELL12_STATUS_LABEL_UNUSABLE = "LABEL_UNUSABLE"
CELL12_STATUS_SEALED_FINAL_TEST = "SEALED_FINAL_TEST"
CELL12_UNUSABLE_STATUSES = frozenset(
    {CELL12_STATUS_PATH_INTEGRITY_FAILURE, CELL12_STATUS_LABEL_UNUSABLE}
)

CELL12_TRAIN_REQUIRED_COLUMNS = (
    "decision_id",
    "outer_partition",
    "path_status",
    "path_usable",
    "path_1m_present",
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
)
CELL12_NUMERIC_PATH_FIELDS = (
    "path_high_60m",
    "path_low_60m",
    "long_mfe_points_60m",
    "long_mae_points_60m",
)

CELL12_RECONCILIATION_NOT_PERFORMED = "NOT_PERFORMED_CELL12_NOT_SUPPLIED"
CELL12_RECONCILIATION_USABLE_PASS = "EXACT_TICK_RECONCILIATION_PASS"
CELL12_RECONCILIATION_UNUSABLE_PASS = (
    "EXACT_UNUSABLE_ABSENT_NUMERIC_FIELD_RECONCILIATION_PASS"
)
CELL12_RECONCILIATION_PASS_STATUSES = frozenset(
    {CELL12_RECONCILIATION_USABLE_PASS, CELL12_RECONCILIATION_UNUSABLE_PASS}
)
CELL12_FULL_COVERAGE_PASS = "EXACT_FULL_TRAIN_COVERAGE_RECONCILIATION_PASS"

# There is no absent-row floor and no intersection policy: every sealed
# outer-TRAIN decision must carry exactly one physically read Cell 12 row.
CELL12_COVERAGE_POLICY_ID = "EXACT_SEALED_TRAIN_IDENTITY_EQUALITY_NO_INTERSECTION_V1"


class G3AuthorizationError(RuntimeError):
    """Raised when a Test 2 G3 boundary would be exceeded or misstated."""


class G3FNotAuthorizedError(G3AuthorizationError):
    """Raised whenever G3-F fitting is requested; G3-F remains unimplemented."""


def assert_g3f_not_authorized(*_args: object, **_kwargs: object) -> NoReturn:
    """Fail closed for every conditional-fit entry point.

    G3-F requires a separate Owner authorization after a passing G3-P record.
    No code path in this package may fit `PATHNUISANCE001` or `PATHFULL001`.
    """

    raise G3FNotAuthorizedError(
        f"{G3F_GATE_LITERAL} is {G3F_STATUS}: no Test 2 model fit, bootstrap, or "
        "economic diagnostic may execute inside the G3-I/G3-P scope"
    )


def support_outcome(support_gate_passed: bool) -> tuple[str, str, str]:
    """Map the frozen support gate onto its pre-fit status triple."""

    if not isinstance(support_gate_passed, bool):
        raise G3AuthorizationError("support_gate_passed must be a boolean")
    return SUPPORT_OUTCOMES[support_gate_passed]


def changed_file_firewall_failures(changed_files: Iterable[str]) -> tuple[str, ...]:
    """Return the exact allowlist deviations for a G3-I diff."""

    observed = frozenset(str(path) for path in changed_files)
    failures: list[str] = []
    unexpected = sorted(observed.difference(G3I_ALLOWED_CHANGED_FILES))
    missing = sorted(G3I_ALLOWED_CHANGED_FILES.difference(observed))
    if unexpected:
        failures.append(f"unexpected={unexpected}")
    if missing:
        failures.append(f"missing={missing}")
    return tuple(failures)


__all__ = [
    "CELL12_COVERAGE_POLICY_ID",
    "CELL12_FULL_COVERAGE_PASS",
    "CELL12_NUMERIC_PATH_FIELDS",
    "CELL12_RECONCILIATION_NOT_PERFORMED",
    "CELL12_RECONCILIATION_PASS_STATUSES",
    "CELL12_RECONCILIATION_UNUSABLE_PASS",
    "CELL12_RECONCILIATION_USABLE_PASS",
    "CELL12_STATUS_LABEL_UNUSABLE",
    "CELL12_STATUS_PATH_INTEGRITY_FAILURE",
    "CELL12_STATUS_SEALED_FINAL_TEST",
    "CELL12_STATUS_USABLE",
    "CELL12_TRAIN_REQUIRED_COLUMNS",
    "CELL12_UNUSABLE_STATUSES",
    "DISPOSITION_DEFERRED_PENDING_G3F",
    "DISPOSITION_INCONCLUSIVE_UNDERPOWERED",
    "EXPECTED_DECODED_ROW_COUNT",
    "EXPECTED_DECODED_TIMESTAMP_MAX_UTC",
    "EXPECTED_DECODED_TIMESTAMP_MIN_UTC",
    "G3F_GATE_LITERAL",
    "G3F_STATUS",
    "G3I_ALLOWED_CHANGED_FILES",
    "G3I_GATE_LITERAL",
    "G3P_GATE_LITERAL",
    "G3_AUTHORIZED_BASE_COMMIT",
    "G3_BRANCH",
    "PINNED_DOC_SHA256",
    "SUPPORT_GATE_FAIL_UNDERPOWERED",
    "SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED",
    "TEST2_G3_PACKAGE_PATH",
    "G3AuthorizationError",
    "G3FNotAuthorizedError",
    "assert_g3f_not_authorized",
    "changed_file_firewall_failures",
    "support_outcome",
]

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from numbers import Integral, Real
from pathlib import Path
from types import MappingProxyType
from typing import Any

from mes_quant.core.hashing import (
    canonical_json_bytes,
    canonicalize_audit,
    sha256_bytes,
    sha256_file,
)
from mes_quant.exploration.l1_lr001 import (
    ARMIJO_CONSTANT,
    BACKTRACK_SHRINK,
    GRADIENT_TOL,
    L2_LAMBDA,
    MAX_ITERATIONS,
    MINIMUM_STEP,
)
from mes_quant.exploration.test2_diagnostics import (
    DIAGNOSTIC_THRESHOLD,
    MES_MULTIPLIER_USD_PER_POINT,
    ROUND_TRIP_COST_USD,
)
from mes_quant.exploration.test2_g3_contract import (
    DISPOSITION_DEFERRED_PENDING_G3F,
    G3F_GATE_LITERAL,
    SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED,
)
from mes_quant.exploration.test2_path_contract import (
    BOOTSTRAP_REPETITIONS,
    CAPACITY_POLICY_ID,
    DIAGNOSTIC_BLOCK_LENGTHS,
    EFFECTIVE_CLASS_SUPPORT_FLOOR,
    ESS_FLOOR_PER_FOLD,
    ESS_FLOOR_POOLED,
    EXPLORATION_SCOPE_ID,
    FOLD_SEED_STRIDE,
    FULL_MODEL_ID,
    MASTER_SEED,
    MDE_VS_NUISANCE,
    MDE_VS_PRIOR,
    NUISANCE_FEATURES,
    NUISANCE_MODEL_ID,
    PATH_BAR_COUNT,
    POOLED_SEED_OFFSET,
    PRIMARY_BLOCK_LENGTH_SESSIONS,
    RELEASE_POLICY_ID,
    STOP_TICKS,
    TAKE_PROFIT_TICKS,
    TICK_SIZE_POINTS,
)
from mes_quant.exploration.test2_stats import (
    BOOTSTRAP_REPETITIONS as STATS_BOOTSTRAP_REPETITIONS,
)
from mes_quant.exploration.test2_stats import (
    DIAGNOSTIC_BLOCK_LENGTHS as STATS_DIAGNOSTIC_BLOCK_LENGTHS,
)
from mes_quant.exploration.test2_stats import FOLD_ORDER, REQUIRED_BLOCK_LENGTHS
from mes_quant.exploration.test2_stats import (
    MASTER_SEED as STATS_MASTER_SEED,
)
from mes_quant.exploration.test2_stats import (
    PRIMARY_BLOCK_LENGTH as STATS_PRIMARY_BLOCK_LENGTH,
)
from mes_quant.features.contract import FEATURE_COLUMNS

# ---------------------------------------------------------------------------
# G3-F code-only boundary
# ---------------------------------------------------------------------------

G3F_CODE_ONLY_BASE_COMMIT = "7d66c43765c3a2c7f7acc772d8861490c70d6894"
G3F_CODE_ONLY_BRANCH = "research/test2-g3f-code-only-v1"
G3F_CODE_ONLY_GATE_LITERAL = "G3F_CODE_ONLY_PREPARATION"
G3F_CODE_ONLY_STATUS = "OWNER_AUTHORIZED_CODE_ONLY_PREPARATION"
G3F_EXECUTION_STATUS = "OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY"
G3F_EXECUTION_BASE_COMMIT = "d3d0455a4299f0dc881974029d457a4197ef321d"
G3F_EXECUTION_BRANCH = "research/test2-g3f-real-execution-v1"
PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256 = (
    "8d70e05b12466faa2860b3d810cf74d2c7fe0320e420b4147900ae9f1dc6c129"
)
PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256: str | None = (
    "ef93a00bd6d7619db6193bcad7cc1ed8241159032fd6528bbf4979d72e4d6a1c"
)
G3F_SUPPORT_STATUS = "SUPPORT_GATE_PASS_RECOMPUTED_G3F_TRAIN_ONLY"
G3F_ECONOMIC_SEMANTICS = (
    "TOUCH_DEFINED_CURRENT_DEPLOYMENT_COUNTERFACTUAL_NOT_HISTORICAL_FILL"
)
G3F_THRESHOLD_SEMANTICS = "COVERAGE_ONLY_NOT_ECONOMIC_BREAK_EVEN"
G3F_OMITTED_LEDGER_PREIMAGE = (
    "CANONICAL_JSON_ORDERED_LIST_V1:decision_identity,fold_id,session_id,"
    "entry_time_utc,release_time_utc,net_usd"
)

PINNED_G3P_RECORD_SHA256 = (
    "a6906cf0a1392c76065c3e98cee0f48ad431af0d043d4d65749b03644704e32e"
)
PINNED_G3P_FILE_SHA256 = (
    "ce71ddf99e110e12b8469d91b9d2509ccd9f24c22ee4274217273b17ba31e28c"
)
PINNED_G3P_RUN_ID = "MES_T2_G3P_F39C31C0900A1D35"

G3F_ALLOWED_CHANGED_FILES = frozenset(
    {
        "docs/research/TEST2_G3F_PACKAGE_V1.md",
        "src/mes_quant/exploration/test2_g3f_contract.py",
        "tests/test_test2_g3f_contract.py",
    }
)

G3F_EXECUTION_ALLOWED_CHANGED_FILES = frozenset(
    {
        "docs/research/TEST2_G3F_EXECUTION_PACKAGE_V1.md",
        "docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md",
        "docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md",
        "src/mes_quant/exploration/test2_evaluation.py",
        "src/mes_quant/exploration/test2_g3f_contract.py",
        "src/mes_quant/exploration/test2_g3f_execution.py",
        "tests/test_test2_evaluation.py",
        "tests/test_test2_g3f_contract.py",
        "tests/test_test2_g3f_execution.py",
        "tools/run_test2_g3f_conditional_fit.py",
    }
)

G3F_PROTECTED_SURFACE_SHA256 = MappingProxyType(
    {
        "src/mes_quant/exploration/l1_lr001.py": (
            "e749dc5934e2ae3442e4d0affd40f483af411b99f397f29b33a25b88dc160d19"
        ),
        "src/mes_quant/exploration/l1_tree001.py": (
            "26068239193ed41d45e3183f4957d30fec6136265ae88a0ea8bfac661a21d2b7"
        ),
        "src/mes_quant/exploration/test2_evaluation.py": (
            "957b0598c99a810cbe32f412248028a398a15817f40cf762fff2a0d18fc9b129"
        ),
        "src/mes_quant/exploration/test2_g3f_execution.py": (
            "2691968d04fc8f21ad29d4f09e4169a8776c122c0349279449186c4d86775bb4"
        ),
        "tools/run_test2_g3f_conditional_fit.py": (
            "2ac3b9e5939ea98a80fd0cba9d4d5b6e9f39292830c7cc1d7d15edb61c37637d"
        ),
        "tests/test_test2_g3f_contract.py": (
            "e75b8bd0c0d3c057f2bf85f05a9fce6057998adf613978bd5d7b87fea6a2092b"
        ),
        "tests/test_test2_g3f_execution.py": (
            "9009caa645e075a9bd5af59ae0b7727be1b7b9782a7c47a8099a02219f12d006"
        ),
        "src/mes_quant/exploration/test2_stats.py": (
            "ea7d784cad2e5cb287e8831d04142894cba9bc749a71153bee3275b064ea2236"
        ),
        "src/mes_quant/exploration/test2_diagnostics.py": (
            "d04198268ba3af02b24dde8d670b4a0601e5e9952ce12b91757a73efae5f58f8"
        ),
        "src/mes_quant/exploration/test2_l1_harness.py": (
            "2263b4394d16c67a12a1e1b03d887952332d58ecee5e3298a2ea47ca3df8f65d"
        ),
        "src/mes_quant/exploration/test2_g3_contract.py": (
            "ef17988469d4c0cda3a3a453eef6a5e443d3f8ae553bc33d23116638821a3e43"
        ),
        "src/mes_quant/exploration/test2_g3_pre_fit.py": (
            "73e0f84003961f27df050571f6d0eee70a067e143b41a9245290b3a10982fabb"
        ),
        "src/mes_quant/exploration/test2_path_contract.py": (
            "d7b12fd99cdf9c45cd872abed5a042f3626d33d9d88b8c89f1d6ed7e1c209041"
        ),
        "src/mes_quant/exploration/test2_target.py": (
            "ff0b463cb034fe60e8cff5d620a5a5349b17299744f5dfadb15da67d6e74c82f"
        ),
        "src/mes_quant/exploration/test2_request_set.py": (
            "0eb8f02b929d28f26e2195412eb52f39feec1c5f8835d951154d6419e294b9ca"
        ),
        "src/mes_quant/exploration/test2_run_context.py": (
            "c0d7969539ea24a29b91c1665d507c0109fc20321573b810f766f93dd5532d1d"
        ),
        "src/mes_quant/exploration/test2_metadata_preflight.py": (
            "14d84b8c4ad11cf2c6bf8fb326473f4da70f30e9ba0f1884d1b3929dbe8e64be"
        ),
        "src/mes_quant/exploration/test2_decode.py": (
            "d537346b84905523fec1d18f4af11f7e7c74ffafe7f5f3186202ebeb5c2bffe9"
        ),
        "src/mes_quant/features/contract.py": (
            "23b89e78a3658d5cf8809a7ca78cf99071efef66fadb0ce92c301cc57c07f05e"
        ),
    }
)

FROZEN_MODEL_IDS = (NUISANCE_MODEL_ID, FULL_MODEL_ID)
FROZEN_FOLD_IDS = tuple(FOLD_ORDER)
EXPECTED_FOLD_FIT_PAIRS = tuple(
    (model_id, fold_id)
    for fold_id in FROZEN_FOLD_IDS
    for model_id in FROZEN_MODEL_IDS
)
MAX_REAL_MODELS = len(FROZEN_MODEL_IDS)
MAX_REAL_FOLD_FIT_CALLS = len(EXPECTED_FOLD_FIT_PAIRS)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_G3F_RUN_ID_RE = re.compile(r"^MES_T2_G3F_[0-9A-F]{16}$")
_MINT_KEY = object()
_G3P_VERIFY_KEY = object()
_MINTED_AUTHORIZATION_IDENTITIES: set[str] = set()


class G3FContractError(RuntimeError):
    """Raised when code attempts to exceed the frozen G3-F boundary."""


def _coefficient_dimension(model_id: str) -> int:
    if model_id == NUISANCE_MODEL_ID:
        return 1 + len(NUISANCE_FEATURES)
    if model_id == FULL_MODEL_ID:
        return 1 + len(FEATURE_COLUMNS)
    raise G3FContractError(f"unknown frozen model ID: {model_id}")


@dataclass(frozen=True)
class VerifiedG3PBinding:
    """Opaque witness minted only after byte and semantic record verification."""

    run_id: str
    record_sha256: str
    file_sha256: str
    disposition: str
    _verification_key: object


def assert_verified_g3p_binding(binding: VerifiedG3PBinding) -> None:
    """Reject bindings not minted by the pinned byte-and-semantic verifier."""

    if (
        not isinstance(binding, VerifiedG3PBinding)
        or binding._verification_key is not _G3P_VERIFY_KEY
        or binding.run_id != PINNED_G3P_RUN_ID
        or binding.record_sha256 != PINNED_G3P_RECORD_SHA256
        or binding.file_sha256 != PINNED_G3P_FILE_SHA256
        or binding.disposition != DISPOSITION_DEFERRED_PENDING_G3F
    ):
        raise G3FContractError("G3-P binding was not minted by the pinned verifier")


@dataclass(frozen=True)
class FoldFitPermit:
    """Single-use witness for one exact model/fold fit call."""

    authorization_identity_sha256: str
    model_id: str
    fold_id: str
    ordinal: int
    _budget_nonce: object


class FoldFitBudget:
    """Fail-closed, ordered, single-run budget for the four frozen fold fits."""

    __slots__ = (
        "_authorization_identity_sha256",
        "_completed",
        "_consumed",
        "_nonce",
        "_poisoned",
        "_sealed",
        "_used_permit_ordinals",
    )

    def __init__(
        self,
        *,
        authorization_identity_sha256: str,
        _key: object,
    ) -> None:
        if _key is not _MINT_KEY:
            raise G3FContractError("FoldFitBudget must be minted by the contract")
        self._authorization_identity_sha256 = authorization_identity_sha256
        self._completed: list[dict[str, object]] = []
        self._consumed: list[tuple[str, str]] = []
        self._nonce = object()
        self._poisoned = False
        self._sealed = False
        self._used_permit_ordinals: set[int] = set()

    @property
    def consumed_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._consumed)

    @property
    def sealed(self) -> bool:
        return self._sealed

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    def _fail(self, message: str) -> None:
        self._poisoned = True
        self._sealed = True
        raise G3FContractError(message)

    def consume(self, *, model_id: str, fold_id: str) -> FoldFitPermit:
        """Consume the next exact pair before its fitter is invoked."""

        if self._sealed or self._poisoned:
            raise G3FContractError("fold-fit budget is sealed or poisoned")
        if len(self._completed) != len(self._consumed):
            self._fail("the preceding fold-fit permit has no completed fit outcome")
        if len(self._consumed) >= MAX_REAL_FOLD_FIT_CALLS:
            self._fail("fifth fold-fit call is forbidden")
        expected = EXPECTED_FOLD_FIT_PAIRS[len(self._consumed)]
        observed = (model_id, fold_id)
        if observed != expected:
            self._fail(
                f"unexpected fold-fit pair/order: expected={expected}, observed={observed}"
            )
        if observed in self._consumed:
            self._fail(f"duplicate fold-fit pair is forbidden: {observed}")
        self._consumed.append(observed)
        return FoldFitPermit(
            authorization_identity_sha256=self._authorization_identity_sha256,
            model_id=model_id,
            fold_id=fold_id,
            ordinal=len(self._consumed),
            _budget_nonce=self._nonce,
        )

    def complete_fit(
        self,
        permit: FoldFitPermit,
        *,
        model_id: str,
        fold_id: str,
        beta_sha256: str,
        coefficient_dimension: int,
        optimizer_converged: bool,
    ) -> None:
        """Bind one successful fitter outcome to its exact single-use permit."""

        if self._sealed or self._poisoned:
            raise G3FContractError("fold-fit permit cannot be used after budget closure")
        if not isinstance(permit, FoldFitPermit) or permit._budget_nonce is not self._nonce:
            self._fail("fit attempted without a permit from this budget")
        if (permit.model_id, permit.fold_id) != (model_id, fold_id):
            self._fail("fold-fit permit does not match the requested model/fold")
        if permit.ordinal != len(self._consumed):
            self._fail("fold-fit permit is stale or out of sequence")
        if permit.ordinal in self._used_permit_ordinals:
            self._fail("fold-fit permit is single-use")
        expected_dimension = _coefficient_dimension(model_id)
        if coefficient_dimension != expected_dimension:
            self._fail(
                "fitted coefficient dimension does not match the frozen model definition"
            )
        if optimizer_converged is not True:
            self._fail("a non-converged optimizer cannot complete a fold-fit permit")
        fitted_identity = _sha256(beta_sha256, field="beta_sha256")
        self._used_permit_ordinals.add(permit.ordinal)
        self._completed.append(
            {
                "model_id": model_id,
                "fold_id": fold_id,
                "ordinal": permit.ordinal,
                "beta_sha256": fitted_identity,
                "coefficient_dimension": coefficient_dimension,
                "optimizer_converged": True,
            }
        )

    def seal(self) -> None:
        """Irreversibly close the budget; incomplete budgets fail closed."""

        if self._sealed or self._poisoned:
            raise G3FContractError("fold-fit budget is already sealed or poisoned")
        self._sealed = True
        if (
            tuple(self._consumed) != EXPECTED_FOLD_FIT_PAIRS
            or self._used_permit_ordinals != set(range(1, MAX_REAL_FOLD_FIT_CALLS + 1))
            or tuple(
                (str(item["model_id"]), str(item["fold_id"]))
                for item in self._completed
            )
            != EXPECTED_FOLD_FIT_PAIRS
        ):
            self._poisoned = True
            raise G3FContractError("cannot seal an incomplete fold-fit cross-product")

    def witness(self) -> dict[str, object]:
        """Return counters derived only from a complete sealed token."""

        if not self._sealed or self._poisoned:
            raise G3FContractError("a fit-budget witness requires a complete sealed budget")
        if (
            tuple(self._consumed) != EXPECTED_FOLD_FIT_PAIRS
            or self._used_permit_ordinals != set(range(1, MAX_REAL_FOLD_FIT_CALLS + 1))
            or tuple(
                (str(item["model_id"]), str(item["fold_id"]))
                for item in self._completed
            )
            != EXPECTED_FOLD_FIT_PAIRS
        ):
            raise G3FContractError("fit-budget witness cross-product mismatch")
        return {
            "authorization_identity_sha256": self._authorization_identity_sha256,
            "model_ids": list(FROZEN_MODEL_IDS),
            "fold_ids": list(FROZEN_FOLD_IDS),
            "consumed_pairs": [list(pair) for pair in self._consumed],
            "completed_fits": [dict(item) for item in self._completed],
            "search_budget_models_consumed": len(
                {str(item["model_id"]) for item in self._completed}
            ),
            "real_models_fitted": len(
                {str(item["model_id"]) for item in self._completed}
            ),
            "real_fold_fit_calls": len(self._completed),
            "sealed": True,
        }


def _sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise G3FContractError(f"{field} must be a lowercase SHA-256")
    return value


def mint_fold_fit_budget(
    *,
    gate_literal: str,
    authorization_identity_sha256: str,
    g3p_binding: VerifiedG3PBinding,
) -> FoldFitBudget:
    """Mint at most one budget for an exact external Owner authorization."""

    if gate_literal != G3F_GATE_LITERAL:
        raise G3FContractError("the exact G3-F conditional-fit gate is required")
    identity = _sha256(
        authorization_identity_sha256,
        field="authorization_identity_sha256",
    )
    if (
        not isinstance(g3p_binding, VerifiedG3PBinding)
        or g3p_binding._verification_key is not _G3P_VERIFY_KEY
    ):
        raise G3FContractError("G3-F requires a verified G3-P record binding token")
    if (
        g3p_binding.run_id != PINNED_G3P_RUN_ID
        or g3p_binding.record_sha256 != PINNED_G3P_RECORD_SHA256
        or g3p_binding.file_sha256 != PINNED_G3P_FILE_SHA256
        or g3p_binding.disposition != DISPOSITION_DEFERRED_PENDING_G3F
    ):
        raise G3FContractError("verified G3-P binding does not match the pinned pass")
    if identity in _MINTED_AUTHORIZATION_IDENTITIES:
        raise G3FContractError("this Owner authorization already minted a fit budget")
    _MINTED_AUTHORIZATION_IDENTITIES.add(identity)
    return FoldFitBudget(
        authorization_identity_sha256=identity,
        _key=_MINT_KEY,
    )


def changed_file_firewall_failures(changed_files: Iterable[str]) -> tuple[str, ...]:
    """Return deviations from the exact additive G3-F code-only allowlist."""

    observed = frozenset(str(path) for path in changed_files)
    failures: list[str] = []
    unexpected = sorted(observed.difference(G3F_ALLOWED_CHANGED_FILES))
    missing = sorted(G3F_ALLOWED_CHANGED_FILES.difference(observed))
    if unexpected:
        failures.append(f"unexpected={unexpected}")
    if missing:
        failures.append(f"missing={missing}")
    return tuple(failures)


def execution_changed_file_firewall_failures(
    changed_files: Iterable[str],
) -> tuple[str, ...]:
    """Return deviations from the exact G3-F execution-package allowlist."""

    observed = frozenset(str(path) for path in changed_files)
    failures: list[str] = []
    unexpected = sorted(observed.difference(G3F_EXECUTION_ALLOWED_CHANGED_FILES))
    missing = sorted(G3F_EXECUTION_ALLOWED_CHANGED_FILES.difference(observed))
    if unexpected:
        failures.append(f"unexpected={unexpected}")
    if missing:
        failures.append(f"missing={missing}")
    return tuple(failures)


def protected_surface_failures(project_root: str | Path) -> tuple[str, ...]:
    """Verify exact execution-package pins, including the authorized evaluator."""

    root = Path(project_root).resolve()
    failures: list[str] = []
    for relative, expected in G3F_PROTECTED_SURFACE_SHA256.items():
        path = root / relative
        if not path.is_file():
            failures.append(f"missing={relative}")
            continue
        observed = sha256_file(path)
        if observed != expected:
            failures.append(f"sha256={relative}:{observed}")
    return tuple(failures)


def validate_g3p_binding(record: Mapping[str, object]) -> None:
    """Validate only the aggregate fields needed to bind a future G3-F run."""

    if record.get("run_id") != PINNED_G3P_RUN_ID:
        raise G3FContractError("G3-P run identity mismatch")
    if record.get("record_sha256") != PINNED_G3P_RECORD_SHA256:
        raise G3FContractError("G3-P semantic record SHA-256 mismatch")
    if record.get("status") != "PASS":
        raise G3FContractError("G3-P status is not PASS")
    if record.get("disposition") != DISPOSITION_DEFERRED_PENDING_G3F:
        raise G3FContractError("G3-P disposition is not deferred for G3-F")
    support = record.get("support_gate")
    if not isinstance(support, Mapping):
        raise G3FContractError("G3-P support gate is missing")
    if support.get("passed") is not True:
        raise G3FContractError("G3-P support gate did not pass")
    if support.get("status") != SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED:
        raise G3FContractError("G3-P support status mismatch")
    counters = record.get("counters")
    if not isinstance(counters, Mapping):
        raise G3FContractError("G3-P counters are missing")
    required_zero = (
        "real_models_fitted",
        "real_fold_fit_calls",
        "bootstrap_replicates",
        "economic_diagnostic_calls",
        "validation_rows_read",
        "final_test_rows_read",
    )
    for key in required_zero:
        _require_integer(counters.get(key), 0, field=f"G3-P {key}")


def g3p_record_semantic_sha256(record: Mapping[str, object]) -> str:
    """Recompute the G3-P semantic hash without trusting its self-hash field."""

    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


def verify_pinned_g3p_record_file(path: str | Path) -> VerifiedG3PBinding:
    """Mint an opaque prerequisite token from the exact immutable G3-P file."""

    record_path = Path(path).expanduser().resolve()
    if not record_path.is_file():
        raise G3FContractError("pinned G3-P record file is missing")
    observed_file_sha256 = sha256_file(record_path)
    if observed_file_sha256 != PINNED_G3P_FILE_SHA256:
        raise G3FContractError("G3-P record file byte SHA-256 mismatch")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise G3FContractError("G3-P record file cannot be parsed") from error
    if not isinstance(record, Mapping):
        raise G3FContractError("G3-P record file must contain a JSON object")
    validate_g3p_binding(record)
    observed_semantic_sha256 = g3p_record_semantic_sha256(record)
    if observed_semantic_sha256 != PINNED_G3P_RECORD_SHA256:
        raise G3FContractError("G3-P semantic record SHA-256 recomputation mismatch")
    return VerifiedG3PBinding(
        run_id=PINNED_G3P_RUN_ID,
        record_sha256=observed_semantic_sha256,
        file_sha256=observed_file_sha256,
        disposition=DISPOSITION_DEFERRED_PENDING_G3F,
        _verification_key=_G3P_VERIFY_KEY,
    )


def scientific_contract_witness() -> dict[str, object]:
    """Expose the frozen constants without adding a command-line knob."""

    if STATS_MASTER_SEED != MASTER_SEED:
        raise G3FContractError("stats/path master seeds diverged")
    if STATS_BOOTSTRAP_REPETITIONS != BOOTSTRAP_REPETITIONS:
        raise G3FContractError("stats/path bootstrap repetitions diverged")
    if STATS_PRIMARY_BLOCK_LENGTH != PRIMARY_BLOCK_LENGTH_SESSIONS:
        raise G3FContractError("stats/path primary block lengths diverged")
    if tuple(STATS_DIAGNOSTIC_BLOCK_LENGTHS) != tuple(DIAGNOSTIC_BLOCK_LENGTHS):
        raise G3FContractError("stats/path diagnostic block lengths diverged")
    if set(REQUIRED_BLOCK_LENGTHS) != {
        PRIMARY_BLOCK_LENGTH_SESSIONS,
        *DIAGNOSTIC_BLOCK_LENGTHS,
    }:
        raise G3FContractError("required bootstrap block lengths diverged")
    return {
        "exploration_scope_id": EXPLORATION_SCOPE_ID,
        "model_ids": list(FROZEN_MODEL_IDS),
        "fold_ids": list(FROZEN_FOLD_IDS),
        "expected_fold_fit_pairs": [list(pair) for pair in EXPECTED_FOLD_FIT_PAIRS],
        "nuisance_features": list(NUISANCE_FEATURES),
        "full_feature_count": len(FEATURE_COLUMNS),
        "tick_size_points": TICK_SIZE_POINTS,
        "take_profit_ticks": TAKE_PROFIT_TICKS,
        "stop_ticks": STOP_TICKS,
        "path_bar_count": PATH_BAR_COUNT,
        "mde_vs_prior": MDE_VS_PRIOR,
        "mde_vs_nuisance": MDE_VS_NUISANCE,
        "ess_floor_per_fold": ESS_FLOOR_PER_FOLD,
        "ess_floor_pooled": ESS_FLOOR_POOLED,
        "effective_class_support_floor": EFFECTIVE_CLASS_SUPPORT_FLOOR,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "primary_block_length_sessions": PRIMARY_BLOCK_LENGTH_SESSIONS,
        "diagnostic_block_lengths": list(DIAGNOSTIC_BLOCK_LENGTHS),
        "master_seed": MASTER_SEED,
        "pooled_seed_offset": POOLED_SEED_OFFSET,
        "fold_seed_stride": FOLD_SEED_STRIDE,
        "numerical_policy": {
            "l2_lambda": L2_LAMBDA,
            "max_iterations": MAX_ITERATIONS,
            "gradient_tolerance": GRADIENT_TOL,
            "armijo_constant": ARMIJO_CONSTANT,
            "backtrack_shrink": BACKTRACK_SHRINK,
            "minimum_step": MINIMUM_STEP,
        },
    }


_FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "beta",
        "betas",
        "coefficients",
        "decision_id",
        "decision_ids",
        "decision_time",
        "decision_times",
        "decile_cut_points",
        "path_values",
        "probabilities",
        "probability",
        "raw_coefficients",
        "row_loss",
        "row_losses",
        "session_id",
        "session_ids",
        "trade_id",
        "trade_ids",
        "trades",
    }
)
_FORBIDDEN_RECORD_KEY_FRAGMENTS = (
    "decision_identity",
    "per_row",
    "raw_coefficient",
    "row_ids",
    "session_identity",
    "trade_ledger",
)


def _walk_keys(value: object) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


_ALLOWED_TOP_LEVEL_RECORD_KEYS = frozenset(
    {
        "access_counters",
        "audit_written_utc",
        "authorization_binding",
        "bootstrap_summary",
        "branch",
        "code_identity",
        "disposition",
        "economic_summary",
        "final_test_status",
        "fit_budget",
        "fold_metrics",
        "g3p_binding",
        "gate_literal",
        "optimizer_summary",
        "pooled_metrics",
        "record_sha256",
        "run_id",
        "scientific_contract",
        "status",
        "support_summary",
        "validation_status",
    }
)
_ALLOWED_FOLD_METRIC_KEYS = frozenset(
    {
        "full_average_precision",
        "full_log_loss",
        "improvement_vs_nuisance",
        "improvement_vs_prior",
        "nuisance_average_precision",
        "nuisance_log_loss",
        "prior_log_loss",
        "retained_sha256",
        "row_count",
    }
)
_ALLOWED_POOLED_METRIC_KEYS = frozenset(
    {
        "full_log_loss",
        "improvement_vs_nuisance",
        "improvement_vs_prior",
        "nuisance_log_loss",
        "prior_log_loss",
        "retained_sha256",
        "row_count",
    }
)
_ALLOWED_BOOTSTRAP_SUMMARY_KEYS = frozenset(
    {
        "diagnostic_block_lengths",
        "diagnostic_lower_bounds",
        "draw_identity_sha256",
        "primary_block_length",
        "primary_lower_bound_vs_nuisance",
        "primary_lower_bound_vs_prior",
        "repetitions",
    }
)
_ALLOWED_OPTIMIZER_SUMMARY_KEYS = frozenset(
    {"beta_sha256", "coefficient_dimensions", "converged_fit_count"}
)


def _require_exact_keys(
    value: Mapping[str, object],
    expected: frozenset[str],
    *,
    field: str,
) -> None:
    if any(not isinstance(key, str) for key in value):
        raise G3FContractError(f"{field} keys must be strings")
    observed = frozenset(value)
    if observed != expected:
        raise G3FContractError(
            f"{field} schema mismatch: expected={sorted(expected)}, "
            f"observed={sorted(observed)}"
        )


def _require_allowed_keys(
    value: Mapping[str, object],
    allowed: frozenset[str],
    *,
    field: str,
) -> None:
    if any(not isinstance(key, str) for key in value):
        raise G3FContractError(f"{field} keys must be strings")
    unexpected = sorted(frozenset(value).difference(allowed))
    if unexpected:
        raise G3FContractError(f"{field} contains non-aggregate fields: {unexpected}")


def _require_integer(value: object, expected: int, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) != expected:
        raise G3FContractError(f"{field} must be integer {expected}")


def _require_finite_number(value: object, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise G3FContractError(f"{field} must be a numeric scalar")
    if not math.isfinite(float(value)):
        raise G3FContractError(f"{field} must be finite")


def _require_nonnegative_integer(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise G3FContractError(f"{field} must be a non-negative integer")
    return int(value)


def _validate_metric_mapping(
    value: object,
    allowed: frozenset[str],
    *,
    field: str,
) -> None:
    if not isinstance(value, Mapping) or not value:
        raise G3FContractError(f"{field} must be a non-empty aggregate mapping")
    _require_allowed_keys(value, allowed, field=field)
    for key, item in value.items():
        if key == "retained_sha256":
            _sha256(item, field=f"{field}.{key}")
        elif key == "row_count":
            if isinstance(item, bool) or not isinstance(item, Integral) or int(item) <= 0:
                raise G3FContractError(f"{field}.row_count must be a positive integer")
        else:
            _require_finite_number(item, field=f"{field}.{key}")


def _validate_economic_policy(
    value: object,
    *,
    field: str,
    expected_policy_id: str,
) -> tuple[int, int, float]:
    if not isinstance(value, Mapping):
        raise G3FContractError(f"{field} must be an aggregate mapping")
    _require_exact_keys(
        value,
        frozenset(
            {
                "candidate_long_signals",
                "capacity_rejected_signals",
                "diagnostic_probability_threshold",
                "executed_trades",
                "net_usd",
                "omitted_ledger_sha256",
                "per_fold",
                "policy_id",
                "round_trip_cost_usd",
                "trade_net_dispersion",
            }
        ),
        field=field,
    )
    if value.get("policy_id") != expected_policy_id:
        raise G3FContractError(f"{field}.policy_id mismatch")
    candidates = _require_nonnegative_integer(
        value.get("candidate_long_signals"), field=f"{field}.candidate_long_signals"
    )
    executed = _require_nonnegative_integer(
        value.get("executed_trades"), field=f"{field}.executed_trades"
    )
    rejected = _require_nonnegative_integer(
        value.get("capacity_rejected_signals"),
        field=f"{field}.capacity_rejected_signals",
    )
    if candidates != executed + rejected:
        raise G3FContractError(f"{field} candidate/executed/rejected counts diverged")
    _require_finite_number(value.get("net_usd"), field=f"{field}.net_usd")
    net_usd = float(value["net_usd"])
    if value.get("round_trip_cost_usd") != ROUND_TRIP_COST_USD:
        raise G3FContractError(f"{field}.round_trip_cost_usd mismatch")
    if value.get("diagnostic_probability_threshold") != DIAGNOSTIC_THRESHOLD:
        raise G3FContractError(f"{field}.diagnostic_probability_threshold mismatch")
    _sha256(
        value.get("omitted_ledger_sha256"),
        field=f"{field}.omitted_ledger_sha256",
    )

    per_fold = value.get("per_fold")
    if not isinstance(per_fold, Mapping):
        raise G3FContractError(f"{field}.per_fold must be a mapping")
    _require_exact_keys(per_fold, frozenset(FROZEN_FOLD_IDS), field=f"{field}.per_fold")
    fold_executed = 0
    fold_net_usd = 0.0
    for fold_id in FROZEN_FOLD_IDS:
        fold = per_fold[fold_id]
        if not isinstance(fold, Mapping):
            raise G3FContractError(f"{field}.per_fold.{fold_id} is invalid")
        _require_exact_keys(
            fold,
            frozenset({"executed_trades", "net_usd"}),
            field=f"{field}.per_fold.{fold_id}",
        )
        fold_executed += _require_nonnegative_integer(
            fold.get("executed_trades"),
            field=f"{field}.per_fold.{fold_id}.executed_trades",
        )
        _require_finite_number(
            fold.get("net_usd"), field=f"{field}.per_fold.{fold_id}.net_usd"
        )
        fold_net_usd += float(fold["net_usd"])
    if fold_executed != executed or not math.isclose(
        fold_net_usd, net_usd, rel_tol=1e-12, abs_tol=1e-9
    ):
        raise G3FContractError(f"{field}.per_fold does not reconcile")

    dispersion = value.get("trade_net_dispersion")
    if not isinstance(dispersion, Mapping):
        raise G3FContractError(f"{field}.trade_net_dispersion must be a mapping")
    _require_exact_keys(
        dispersion,
        frozenset(
            {
                "maximum_net_usd",
                "minimum_net_usd",
                "negative_count",
                "positive_count",
                "zero_count",
            }
        ),
        field=f"{field}.trade_net_dispersion",
    )
    sign_total = sum(
        _require_nonnegative_integer(
            dispersion.get(key), field=f"{field}.trade_net_dispersion.{key}"
        )
        for key in ("positive_count", "negative_count", "zero_count")
    )
    if sign_total != executed:
        raise G3FContractError(f"{field}.trade_net_dispersion counts do not reconcile")
    minimum = dispersion.get("minimum_net_usd")
    maximum = dispersion.get("maximum_net_usd")
    if executed == 0:
        if minimum is not None or maximum is not None:
            raise G3FContractError(f"{field} zero-trade extrema must be null")
    else:
        _require_finite_number(minimum, field=f"{field}.minimum_net_usd")
        _require_finite_number(maximum, field=f"{field}.maximum_net_usd")
        if float(minimum) > float(maximum):
            raise G3FContractError(f"{field} dispersion extrema are reversed")
    return candidates, executed, net_usd


def _validate_economic_summary(value: object) -> None:
    if not isinstance(value, Mapping):
        raise G3FContractError("economic_summary must be an aggregate mapping")
    _require_exact_keys(
        value,
        frozenset(
            {
                "capacity_sensitivity",
                "economic_diagnostic_calls",
                "economic_policy_evaluations",
                "mes_multiplier_usd_per_point",
                "omitted_ledger_preimage",
                "primary",
                "semantics",
                "source_model_id",
                "threshold_semantics",
            }
        ),
        field="economic_summary",
    )
    if value.get("source_model_id") != FULL_MODEL_ID:
        raise G3FContractError("economic_summary source model mismatch")
    if value.get("semantics") != G3F_ECONOMIC_SEMANTICS:
        raise G3FContractError("economic_summary semantics mismatch")
    if value.get("threshold_semantics") != G3F_THRESHOLD_SEMANTICS:
        raise G3FContractError("economic_summary threshold semantics mismatch")
    if value.get("omitted_ledger_preimage") != G3F_OMITTED_LEDGER_PREIMAGE:
        raise G3FContractError("economic_summary ledger preimage mismatch")
    if value.get("mes_multiplier_usd_per_point") != MES_MULTIPLIER_USD_PER_POINT:
        raise G3FContractError("economic_summary multiplier mismatch")
    _require_integer(
        value.get("economic_diagnostic_calls"),
        1,
        field="economic_summary.economic_diagnostic_calls",
    )
    _require_integer(
        value.get("economic_policy_evaluations"),
        2,
        field="economic_summary.economic_policy_evaluations",
    )
    primary_candidates, _, _ = _validate_economic_policy(
        value.get("primary"),
        field="economic_summary.primary",
        expected_policy_id=RELEASE_POLICY_ID,
    )
    sensitivity_candidates, _, _ = _validate_economic_policy(
        value.get("capacity_sensitivity"),
        field="economic_summary.capacity_sensitivity",
        expected_policy_id=CAPACITY_POLICY_ID,
    )
    if primary_candidates != sensitivity_candidates:
        raise G3FContractError("economic policy candidate counts diverged")


def validate_aggregate_record(record: Mapping[str, object]) -> None:
    """Reject row-level or coefficient-level content from a G3-F record."""

    if not isinstance(record, Mapping) or not record:
        raise G3FContractError("G3-F record must be a non-empty mapping")
    _require_allowed_keys(
        record,
        _ALLOWED_TOP_LEVEL_RECORD_KEYS,
        field="record",
    )
    required_top_level = {
        "access_counters",
        "audit_written_utc",
        "authorization_binding",
        "bootstrap_summary",
        "branch",
        "code_identity",
        "disposition",
        "economic_summary",
        "final_test_status",
        "fit_budget",
        "fold_metrics",
        "g3p_binding",
        "gate_literal",
        "optimizer_summary",
        "pooled_metrics",
        "run_id",
        "scientific_contract",
        "status",
        "support_summary",
        "validation_status",
    }
    missing_top_level = sorted(required_top_level.difference(record))
    if missing_top_level:
        raise G3FContractError(f"record is missing required fields: {missing_top_level}")
    forbidden: list[str] = []
    for key in _walk_keys(record):
        normalized = key.lower()
        if normalized in _FORBIDDEN_RECORD_KEYS or any(
            fragment in normalized for fragment in _FORBIDDEN_RECORD_KEY_FRAGMENTS
        ):
            forbidden.append(key)
    if forbidden:
        raise G3FContractError(
            "G3-F record contains forbidden row/coefficient fields: "
            + ", ".join(sorted(set(forbidden)))
        )
    if record.get("gate_literal") != G3F_GATE_LITERAL:
        raise G3FContractError("G3-F aggregate record gate mismatch")
    if record.get("status") != "PASS":
        raise G3FContractError("G3-F aggregate record status must be PASS")
    if "audit_written_utc" in record:
        audit_time = record["audit_written_utc"]
        if not isinstance(audit_time, str):
            raise G3FContractError("audit_written_utc must be an ISO-8601 string")
        try:
            parsed_audit_time = datetime.fromisoformat(audit_time)
        except ValueError as error:
            raise G3FContractError("audit_written_utc is not valid ISO-8601") from error
        if parsed_audit_time.tzinfo is None:
            raise G3FContractError("audit_written_utc must be timezone-aware")
    if "branch" in record and record["branch"] != G3F_EXECUTION_BRANCH:
        raise G3FContractError("G3-F aggregate record branch mismatch")
    if "code_identity" in record and (
        not isinstance(record["code_identity"], str)
        or _GIT_SHA_RE.fullmatch(record["code_identity"]) is None
    ):
        raise G3FContractError("code_identity must be a lowercase Git SHA")
    if "run_id" in record and (
        not isinstance(record["run_id"], str)
        or _G3F_RUN_ID_RE.fullmatch(record["run_id"]) is None
    ):
        raise G3FContractError("G3-F aggregate record run_id mismatch")
    if "record_sha256" in record:
        _sha256(record["record_sha256"], field="record_sha256")
    if "disposition" in record and (
        not isinstance(record["disposition"], str)
        or record["disposition"]
        not in {"INTERESTING_ENOUGH_TO_CONTINUE", "NOT_INTERESTING_ENOUGH"}
    ):
        raise G3FContractError("G3-F aggregate record disposition mismatch")
    if record.get("validation_status") != "UNOPENED":
        raise G3FContractError("G3-F aggregate record must keep Validation unopened")
    if record.get("final_test_status") != "SEALED":
        raise G3FContractError("G3-F aggregate record must keep Final Test sealed")
    g3p_binding = record.get("g3p_binding")
    if not isinstance(g3p_binding, Mapping):
        raise G3FContractError("G3-F aggregate record requires a G3-P binding")
    _require_exact_keys(
        g3p_binding,
        frozenset({"disposition", "record_sha256", "run_id"}),
        field="g3p_binding",
    )
    if g3p_binding.get("run_id") != PINNED_G3P_RUN_ID:
        raise G3FContractError("G3-F aggregate record G3-P run mismatch")
    if g3p_binding.get("record_sha256") != PINNED_G3P_RECORD_SHA256:
        raise G3FContractError("G3-F aggregate record G3-P hash mismatch")
    if g3p_binding.get("disposition") != DISPOSITION_DEFERRED_PENDING_G3F:
        raise G3FContractError("G3-F aggregate record G3-P disposition mismatch")
    if record.get("scientific_contract") != scientific_contract_witness():
        raise G3FContractError("G3-F aggregate record scientific contract mismatch")
    counters = record.get("access_counters")
    if not isinstance(counters, Mapping):
        raise G3FContractError("G3-F aggregate record requires access_counters")
    _require_exact_keys(
        counters,
        frozenset({"final_test_rows_read", "validation_rows_read"}),
        field="access_counters",
    )
    _require_integer(
        counters.get("validation_rows_read"),
        0,
        field="validation_rows_read",
    )
    _require_integer(
        counters.get("final_test_rows_read"),
        0,
        field="final_test_rows_read",
    )
    budget = record.get("fit_budget")
    if not isinstance(budget, Mapping):
        raise G3FContractError("G3-F aggregate record requires a fit_budget witness")
    _require_exact_keys(
        budget,
        frozenset(
            {
                "authorization_identity_sha256",
                "completed_fits",
                "consumed_pairs",
                "fold_ids",
                "model_ids",
                "real_fold_fit_calls",
                "real_models_fitted",
                "sealed",
                "search_budget_models_consumed",
            }
        ),
        field="fit_budget",
    )
    if budget.get("model_ids") != list(FROZEN_MODEL_IDS):
        raise G3FContractError("G3-F record model set mismatch")
    if budget.get("fold_ids") != list(FROZEN_FOLD_IDS):
        raise G3FContractError("G3-F record fold set mismatch")
    if budget.get("consumed_pairs") != [list(pair) for pair in EXPECTED_FOLD_FIT_PAIRS]:
        raise G3FContractError("G3-F record fold-fit cross-product mismatch")
    completed = budget.get("completed_fits")
    if not isinstance(completed, list) or len(completed) != MAX_REAL_FOLD_FIT_CALLS:
        raise G3FContractError("G3-F record completed-fit evidence mismatch")
    completed_pairs = [
        [item.get("model_id"), item.get("fold_id")]
        for item in completed
        if isinstance(item, Mapping)
    ]
    if completed_pairs != [list(pair) for pair in EXPECTED_FOLD_FIT_PAIRS]:
        raise G3FContractError("G3-F record completed-fit pair mismatch")
    if any(
        not isinstance(item, Mapping)
        or _SHA256_RE.fullmatch(str(item.get("beta_sha256"))) is None
        or item.get("optimizer_converged") is not True
        for item in completed
    ):
        raise G3FContractError("G3-F record completed-fit identity/convergence mismatch")
    for ordinal, item in enumerate(completed, start=1):
        assert isinstance(item, Mapping)
        _require_exact_keys(
            item,
            frozenset(
                {
                    "beta_sha256",
                    "coefficient_dimension",
                    "fold_id",
                    "model_id",
                    "optimizer_converged",
                    "ordinal",
                }
            ),
            field=f"fit_budget.completed_fits[{ordinal}]",
        )
        _require_integer(item.get("ordinal"), ordinal, field="completed_fit.ordinal")
        expected_dimension = _coefficient_dimension(str(item.get("model_id")))
        _require_integer(
            item.get("coefficient_dimension"),
            expected_dimension,
            field="completed_fit.coefficient_dimension",
        )
    authorization = record.get("authorization_binding")
    if not isinstance(authorization, Mapping):
        raise G3FContractError("G3-F aggregate record requires authorization_binding")
    _require_exact_keys(
        authorization,
        frozenset({"identity_sha256", "status"}),
        field="authorization_binding",
    )
    _sha256(authorization.get("identity_sha256"), field="authorization.identity_sha256")
    if authorization.get("identity_sha256") != (
        PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256
    ):
        raise G3FContractError("G3-F real-execution authorization hash mismatch")
    if authorization.get("status") != G3F_EXECUTION_STATUS:
        raise G3FContractError("G3-F real-execution authorization status mismatch")
    if authorization.get("identity_sha256") != budget.get(
        "authorization_identity_sha256"
    ):
        raise G3FContractError("G3-F authorization and fit-budget identities diverged")
    _require_integer(
        budget.get("real_models_fitted"),
        MAX_REAL_MODELS,
        field="real_models_fitted",
    )
    _require_integer(
        budget.get("real_fold_fit_calls"),
        MAX_REAL_FOLD_FIT_CALLS,
        field="real_fold_fit_calls",
    )
    _require_integer(
        budget.get("search_budget_models_consumed"),
        MAX_REAL_MODELS,
        field="search_budget_models_consumed",
    )
    if budget.get("sealed") is not True:
        raise G3FContractError("G3-F record fit budget is not sealed")

    fold_metrics = record.get("fold_metrics")
    if not isinstance(fold_metrics, Mapping):
        raise G3FContractError("G3-F record requires fold_metrics")
    _require_exact_keys(fold_metrics, frozenset(FROZEN_FOLD_IDS), field="fold_metrics")
    for fold_id in FROZEN_FOLD_IDS:
        fold_value = fold_metrics[fold_id]
        assert isinstance(fold_value, Mapping)
        required_fold_metrics = {
            "full_log_loss",
            "improvement_vs_nuisance",
            "improvement_vs_prior",
            "nuisance_log_loss",
            "prior_log_loss",
            "retained_sha256",
            "row_count",
        }
        missing_fold_metrics = sorted(required_fold_metrics.difference(fold_value))
        if missing_fold_metrics:
            raise G3FContractError(
                f"fold_metrics.{fold_id} missing required evidence: "
                f"{missing_fold_metrics}"
            )
        _validate_metric_mapping(
            fold_value,
            _ALLOWED_FOLD_METRIC_KEYS,
            field=f"fold_metrics.{fold_id}",
        )
    pooled_metrics = record.get("pooled_metrics")
    if not isinstance(pooled_metrics, Mapping):
        raise G3FContractError("G3-F record requires pooled_metrics")
    required_pooled_metrics = {
        "full_log_loss",
        "improvement_vs_nuisance",
        "improvement_vs_prior",
        "nuisance_log_loss",
        "prior_log_loss",
        "retained_sha256",
        "row_count",
    }
    missing_pooled_metrics = sorted(required_pooled_metrics.difference(pooled_metrics))
    if missing_pooled_metrics:
        raise G3FContractError(
            f"pooled_metrics missing required evidence: {missing_pooled_metrics}"
        )
    _validate_metric_mapping(
        pooled_metrics,
        _ALLOWED_POOLED_METRIC_KEYS,
        field="pooled_metrics",
    )

    _validate_economic_summary(record.get("economic_summary"))

    bootstrap = record.get("bootstrap_summary")
    if not isinstance(bootstrap, Mapping) or not bootstrap:
        raise G3FContractError("G3-F record requires bootstrap_summary")
    _require_allowed_keys(
        bootstrap,
        _ALLOWED_BOOTSTRAP_SUMMARY_KEYS,
        field="bootstrap_summary",
    )
    required_bootstrap = {
        "diagnostic_block_lengths",
        "diagnostic_lower_bounds",
        "draw_identity_sha256",
        "primary_block_length",
        "primary_lower_bound_vs_nuisance",
        "primary_lower_bound_vs_prior",
        "repetitions",
    }
    missing_bootstrap = sorted(required_bootstrap.difference(bootstrap))
    if missing_bootstrap:
        raise G3FContractError(
            f"bootstrap_summary missing required evidence: {missing_bootstrap}"
        )
    for key, item in bootstrap.items():
        if key == "draw_identity_sha256":
            _sha256(item, field="bootstrap_summary.draw_identity_sha256")
        elif key == "diagnostic_block_lengths":
            if item != list(DIAGNOSTIC_BLOCK_LENGTHS):
                raise G3FContractError("diagnostic bootstrap block lengths mismatch")
        elif key == "diagnostic_lower_bounds":
            if not isinstance(item, list) or len(item) != len(
                DIAGNOSTIC_BLOCK_LENGTHS
            ):
                raise G3FContractError("diagnostic bootstrap lower bounds mismatch")
            observed_blocks: list[int] = []
            for ordinal, row in enumerate(item):
                if not isinstance(row, list) or len(row) != 3:
                    raise G3FContractError(
                        "diagnostic bootstrap lower-bound row mismatch"
                    )
                block, vs_prior, vs_nuisance = row
                expected_block = DIAGNOSTIC_BLOCK_LENGTHS[ordinal]
                _require_integer(
                    block,
                    expected_block,
                    field=f"bootstrap.diagnostic_lower_bounds[{ordinal}].block",
                )
                _require_finite_number(
                    vs_prior,
                    field=f"bootstrap.diagnostic_lower_bounds[{ordinal}].vs_prior",
                )
                _require_finite_number(
                    vs_nuisance,
                    field=f"bootstrap.diagnostic_lower_bounds[{ordinal}].vs_nuisance",
                )
                observed_blocks.append(int(block))
            if observed_blocks != list(DIAGNOSTIC_BLOCK_LENGTHS):
                raise G3FContractError("diagnostic bootstrap order mismatch")
        elif key == "repetitions":
            _require_integer(item, BOOTSTRAP_REPETITIONS, field="bootstrap.repetitions")
        elif key == "primary_block_length":
            _require_integer(
                item,
                PRIMARY_BLOCK_LENGTH_SESSIONS,
                field="bootstrap.primary_block_length",
            )
        else:
            _require_finite_number(item, field=f"bootstrap_summary.{key}")

    optimizer = record.get("optimizer_summary")
    if not isinstance(optimizer, Mapping):
        raise G3FContractError("G3-F record requires optimizer_summary")
    _require_exact_keys(
        optimizer,
        _ALLOWED_OPTIMIZER_SUMMARY_KEYS,
        field="optimizer_summary",
    )
    _require_integer(
        optimizer.get("converged_fit_count"),
        MAX_REAL_FOLD_FIT_CALLS,
        field="optimizer.converged_fit_count",
    )
    beta_hashes = optimizer.get("beta_sha256")
    dimensions = optimizer.get("coefficient_dimensions")
    if beta_hashes != [item["beta_sha256"] for item in completed]:
        raise G3FContractError("optimizer beta identities diverged from completed fits")
    if dimensions != [item["coefficient_dimension"] for item in completed]:
        raise G3FContractError("optimizer dimensions diverged from completed fits")

    support = record.get("support_summary")
    if not isinstance(support, Mapping):
        raise G3FContractError("G3-F record requires support_summary")
    _require_exact_keys(
        support,
        frozenset({"floors_relaxed", "folds", "pooled", "status"}),
        field="support_summary",
    )
    if support.get("status") != G3F_SUPPORT_STATUS:
        raise G3FContractError("G3-F support summary status mismatch")
    if support.get("floors_relaxed") is not False:
        raise G3FContractError("G3-F support floors must remain frozen")
    support_folds = support.get("folds")
    if not isinstance(support_folds, Mapping):
        raise G3FContractError("G3-F support fold summary is missing")
    _require_exact_keys(
        support_folds,
        frozenset(FROZEN_FOLD_IDS),
        field="support_summary.folds",
    )
    support_fields = frozenset(
        {
            "effective_negative_support",
            "effective_positive_support",
            "governing_ess",
            "row_count",
        }
    )
    for fold_id in FROZEN_FOLD_IDS:
        fold_support = support_folds[fold_id]
        if not isinstance(fold_support, Mapping):
            raise G3FContractError(f"support_summary.folds.{fold_id} is missing")
        _require_exact_keys(
            fold_support,
            support_fields,
            field=f"support_summary.folds.{fold_id}",
        )
        for key, item in fold_support.items():
            if key == "row_count":
                if isinstance(item, bool) or not isinstance(item, Integral) or item <= 0:
                    raise G3FContractError("support row_count must be a positive integer")
            else:
                _require_finite_number(item, field=f"support.{fold_id}.{key}")
    pooled_support = support.get("pooled")
    if not isinstance(pooled_support, Mapping):
        raise G3FContractError("G3-F pooled support summary is missing")
    _require_exact_keys(pooled_support, support_fields, field="support_summary.pooled")
    for key, item in pooled_support.items():
        if key == "row_count":
            if isinstance(item, bool) or not isinstance(item, Integral) or item <= 0:
                raise G3FContractError("pooled support row_count must be a positive integer")
        else:
            _require_finite_number(item, field=f"support.pooled.{key}")


def aggregate_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash an aggregate record excluding its self-hash and volatile audit time."""

    validate_aggregate_record(record)
    without_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json_bytes(canonicalize_audit(without_hash)))


__all__ = [
    "EXPECTED_FOLD_FIT_PAIRS",
    "FROZEN_FOLD_IDS",
    "FROZEN_MODEL_IDS",
    "G3F_ALLOWED_CHANGED_FILES",
    "G3F_CODE_ONLY_BASE_COMMIT",
    "G3F_CODE_ONLY_BRANCH",
    "G3F_CODE_ONLY_GATE_LITERAL",
    "G3F_CODE_ONLY_STATUS",
    "G3F_EXECUTION_ALLOWED_CHANGED_FILES",
    "G3F_EXECUTION_BASE_COMMIT",
    "G3F_EXECUTION_BRANCH",
    "G3F_EXECUTION_STATUS",
    "G3F_PROTECTED_SURFACE_SHA256",
    "G3F_SUPPORT_STATUS",
    "MAX_REAL_FOLD_FIT_CALLS",
    "MAX_REAL_MODELS",
    "PINNED_G3F_CODE_ONLY_AUTHORIZATION_DOC_SHA256",
    "PINNED_G3F_REAL_EXECUTION_AUTHORIZATION_DOC_SHA256",
    "PINNED_G3P_FILE_SHA256",
    "PINNED_G3P_RECORD_SHA256",
    "PINNED_G3P_RUN_ID",
    "FoldFitBudget",
    "FoldFitPermit",
    "G3FContractError",
    "VerifiedG3PBinding",
    "aggregate_record_sha256",
    "assert_verified_g3p_binding",
    "changed_file_firewall_failures",
    "execution_changed_file_firewall_failures",
    "g3p_record_semantic_sha256",
    "mint_fold_fit_budget",
    "protected_surface_failures",
    "scientific_contract_witness",
    "validate_aggregate_record",
    "validate_g3p_binding",
    "verify_pinned_g3p_record_file",
]

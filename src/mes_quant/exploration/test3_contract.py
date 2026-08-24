from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from types import MappingProxyType

PROTOCOL_ID = "MES_TEST3_RV60_HAR_RISK_EDGE_V1"
PROJECT_BUDGET_ID = "MES_PROJECT_TARGET_SPACE_BUDGET_V1"
RATIFIED_COMMIT = "7c17b292958aeb8252f9c0911ef7028b6071cdbb"
RATIFICATION_RECORD_COMMIT = "05f569f3ee2093461b5330e8069cb2fd0099d3b1"
L0_AUTHORIZED_BASE_COMMIT = "5d5ec4a67648cbc5be4b3d2d8fceedea07caa01b"
L0_AUTHORIZATION_ID = "AUTH_TEST3_L0_CODE_ONLY_20260824"
L0_ACCESS_LEVEL = "L0_SYNTHETIC_IN_MEMORY_ONLY"
TARGET_SPACE_ID = "TARGET_SPACE_003"
TARGET_SPACE_STATE = "LOCKED / RESERVED"

PROTOCOL_SHA256 = "974ff7942f17174a2fbd855e42b591b2c0dad123ddae62d4436b418e68d4c826"
PROJECT_BUDGET_SHA256 = "4e939608d0753c608675510c4e449cdac7d452022b0ec9d632fd989f045f58ed"

RAW_DBN_SHA256 = "49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0"
DECODED_MES_1M_SHA256 = "e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584"
CELL8_SPLIT_ASSIGNMENT_SHA256 = (
    "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035"
)
CELL10_LABEL_SHA256 = "1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0"
CELL12_PATH_SHA256 = "8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941"
CELL14_FEATURE_FILE_SHA256 = (
    "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452"
)
CELL14_ORDERED_FEATURE_SHA256 = (
    "dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d"
)

TARGET_BAR_COUNT = 60
TARGET_OFFSETS = tuple(range(TARGET_BAR_COUNT))
TARGET_HORIZON_MINUTES = 60
TARGET_INSTRUMENT_ID = "MES"
FOLD_ORDER = ("WF_2022", "WF_2023")
FROZEN_HOLDOUT_COUNTS = MappingProxyType({"WF_2022": 5_510, "WF_2023": 5_476})
MODEL_ORDER = ("RVBASE001", "RVHAR001")
MODEL_COLUMNS = MappingProxyType(
    {
        "RVBASE001": ("intercept", "X60", "SESSION_SIN", "SESSION_COS"),
        "RVHAR001": (
            "intercept",
            "X60",
            "X120",
            "X240",
            "SESSION_SIN",
            "SESSION_COS",
        ),
    }
)
REAL_FOLD_FIT_BUDGET = 4
MASTER_SEED = 20260809
BOOTSTRAP_REPETITIONS = 2_000
PRIMARY_BLOCK_LENGTH = 5
DIAGNOSTIC_BLOCK_LENGTHS = (1, 20)
REQUIRED_BLOCK_LENGTHS = (PRIMARY_BLOCK_LENGTH, *DIAGNOSTIC_BLOCK_LENGTHS)
RELATIVE_QLIKE_REDUCTION_FLOOR = 0.10


class Test3ContractError(ValueError):
    """Raised when an input violates the ratified Test 3 contract."""

    __test__ = False


class Stage(StrEnum):
    L0_CODE_ONLY = "L0 code-only"
    G2_METADATA_ONLY = "G2 metadata-only"
    G2P_PREDICTOR_PREFLIGHT = "G2-P TRAIN predictor-domain preflight"
    G3P_PREFIT = "G3-P TRAIN pre-fit"
    G3F_ONE_SHOT = "G3-F one-shot"


class TerminalDisposition(StrEnum):
    INTERESTING = "INTERESTING_ENOUGH_FOR_CONFIRMATORY_PROTOCOL"
    NOT_INTERESTING = "NOT_INTERESTING_ENOUGH"
    UNDERPOWERED = "UNDERPOWERED_STOP"
    INVALID = "INVALID_EVIDENCE"


class RowStatus(StrEnum):
    TARGET_USABLE = "TARGET_USABLE"
    TARGET_UNUSABLE = "TARGET_UNUSABLE"
    PREDICTOR_USABLE = "PREDICTOR_USABLE"
    PREDICTOR_UNUSABLE = "PREDICTOR_UNUSABLE"


class FailureReason(StrEnum):
    TARGET_ZERO_VARIANCE = "TARGET_ZERO_VARIANCE"
    PREDICTOR_NONFINITE = "PREDICTOR_NONFINITE"
    PREDICTOR_NONPOSITIVE = "PREDICTOR_NONPOSITIVE"


@dataclass(frozen=True)
class L0SafetyCounters:
    metadata_values_read: int = 0
    numeric_artifact_rows_read: int = 0
    real_target_or_path_rows_read: int = 0
    real_targets_constructed: int = 0
    real_fold_fit_calls: int = 0
    real_models_fitted: int = 0
    real_bootstrap_replicates: int = 0
    validation_rows_read: int = 0
    final_test_rows_read: int = 0


def assert_l0_safety(counters: L0SafetyCounters) -> None:
    if not isinstance(counters, L0SafetyCounters):
        raise Test3ContractError("counters must be L0SafetyCounters")
    nonzero = {name: value for name, value in asdict(counters).items() if value != 0}
    if nonzero:
        raise Test3ContractError(f"L0 safety counters must all be zero: {sorted(nonzero)}")


def frozen_contract_payload() -> Mapping[str, object]:
    return MappingProxyType(
        {
            "protocol_id": PROTOCOL_ID,
            "project_budget_id": PROJECT_BUDGET_ID,
            "ratified_commit": RATIFIED_COMMIT,
            "l0_authorized_base_commit": L0_AUTHORIZED_BASE_COMMIT,
            "target_space_id": TARGET_SPACE_ID,
            "target_space_state": TARGET_SPACE_STATE,
            "stages": tuple(stage.value for stage in Stage),
            "models": MODEL_ORDER,
            "model_columns": tuple((key, MODEL_COLUMNS[key]) for key in MODEL_ORDER),
            "folds": FOLD_ORDER,
            "fit_budget": REAL_FOLD_FIT_BUDGET,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_blocks": REQUIRED_BLOCK_LENGTHS,
            "master_seed": MASTER_SEED,
        }
    )


def frozen_contract_sha256() -> str:
    payload = dict(frozen_contract_payload())
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

from __future__ import annotations

import pytest

from mes_quant.exploration.test3_contract import (
    FOLD_ORDER,
    L0_AUTHORIZED_BASE_COMMIT,
    MODEL_COLUMNS,
    MODEL_ORDER,
    PROJECT_BUDGET_ID,
    PROTOCOL_ID,
    RATIFIED_COMMIT,
    REAL_FOLD_FIT_BUDGET,
    TARGET_SPACE_STATE,
    L0SafetyCounters,
    RowStatus,
    Stage,
    Test3ContractError,
    assert_l0_safety,
    frozen_contract_payload,
    frozen_contract_sha256,
)


def test_ratified_contract_identities_and_order_are_exact() -> None:
    assert PROTOCOL_ID == "MES_TEST3_RV60_HAR_RISK_EDGE_V1"
    assert PROJECT_BUDGET_ID == "MES_PROJECT_TARGET_SPACE_BUDGET_V1"
    assert RATIFIED_COMMIT == "7c17b292958aeb8252f9c0911ef7028b6071cdbb"
    assert L0_AUTHORIZED_BASE_COMMIT == "5d5ec4a67648cbc5be4b3d2d8fceedea07caa01b"
    assert TARGET_SPACE_STATE == "LOCKED / RESERVED"
    assert tuple(stage.value for stage in Stage) == (
        "L0 code-only",
        "G2 metadata-only",
        "G2-P TRAIN predictor-domain preflight",
        "G3-P TRAIN pre-fit",
        "G3-F one-shot",
    )
    assert FOLD_ORDER == ("WF_2022", "WF_2023")
    assert MODEL_ORDER == ("RVBASE001", "RVHAR001")
    assert MODEL_COLUMNS["RVBASE001"] == (
        "intercept",
        "X60",
        "SESSION_SIN",
        "SESSION_COS",
    )
    assert MODEL_COLUMNS["RVHAR001"] == (
        "intercept",
        "X60",
        "X120",
        "X240",
        "SESSION_SIN",
        "SESSION_COS",
    )
    assert REAL_FOLD_FIT_BUDGET == 4


def test_only_exact_usable_statuses_have_usable_suffix() -> None:
    assert RowStatus.TARGET_USABLE.value == "TARGET_USABLE"
    assert RowStatus.PREDICTOR_USABLE.value == "PREDICTOR_USABLE"
    assert RowStatus.TARGET_UNUSABLE.value == "TARGET_UNUSABLE"
    assert RowStatus.PREDICTOR_UNUSABLE.value == "PREDICTOR_UNUSABLE"


def test_l0_safety_is_zero_only_and_contract_hash_is_stable() -> None:
    assert_l0_safety(L0SafetyCounters())
    with pytest.raises(Test3ContractError, match="all be zero"):
        assert_l0_safety(L0SafetyCounters(real_targets_constructed=1))
    payload = frozen_contract_payload()
    assert payload["fit_budget"] == 4
    assert len(frozen_contract_sha256()) == 64
    assert frozen_contract_sha256() == frozen_contract_sha256()
    with pytest.raises(TypeError):
        payload["fit_budget"] = 5  # type: ignore[index]

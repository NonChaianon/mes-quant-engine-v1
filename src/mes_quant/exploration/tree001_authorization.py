from __future__ import annotations

from mes_quant.exploration import l1_tree001

TREE001_AUTHORIZATION_STATUS = "ENABLED"
TREE001_AUTHORIZATION_TOKEN = "OWNER_AUTHORIZED_TREE001_20260816"
TREE001_AUTHORIZATION_REFERENCE = "Owner chat authorization 2026-08-16 / Issue #28"
TREE001_AUTHORIZED_EXPERIMENT_ID = "MES_S1_TREE001_20260815T192900Z"


def activate_tree001_execution() -> None:
    """Activate the separately authorized one-shot TREE001 execution gate."""
    if l1_tree001.TREE001_EXPERIMENT_ID != TREE001_AUTHORIZED_EXPERIMENT_ID:
        raise RuntimeError("TREE001 authorization experiment identity mismatch")
    l1_tree001.TREE001_EXECUTION_STATUS = TREE001_AUTHORIZATION_STATUS
    l1_tree001.TREE001_AUTHORIZATION_TOKEN = TREE001_AUTHORIZATION_TOKEN

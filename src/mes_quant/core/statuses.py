from __future__ import annotations

from enum import StrEnum


class ContractStatus(StrEnum):
    LOCKED = "LOCKED"
    PROVISIONAL = "PROVISIONAL"
    OPEN = "OPEN"
    REJECTED = "REJECTED"


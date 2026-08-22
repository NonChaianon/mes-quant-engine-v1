from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from mes_quant.core.hashing import canonical_json_bytes, sha256_bytes
from mes_quant.exploration.test2_path_contract import (
    CELL8_SPLIT_ASSIGNMENT_SHA256,
    FINAL_TEST_BOUNDARY_UTC,
    FINAL_TEST_ROLE,
    OUTER_TRAIN_ROLE,
    OUTER_VALIDATION_BOUNDARY_UTC,
    OUTER_VALIDATION_ROLE,
    PATH_OFFSETS,
)


class RequestSetContractError(ValueError):
    """Raised when a Test 2 path request would violate the frozen access contract."""


@dataclass(frozen=True)
class ParentDecision:
    decision_identity: str
    decision_time_utc: datetime
    outer_partition: str


@dataclass(frozen=True, order=True)
class RequestKey:
    decision_identity: str
    minute_offset: int
    requested_timestamp_utc: datetime


@dataclass(frozen=True)
class SealedRequestSet:
    keys: tuple[RequestKey, ...]
    request_set_sha256: str
    split_assignment_sha256: str
    parent_roles: tuple[tuple[str, str], ...]
    validation_path_bar_lookup_count: int
    final_test_path_bar_lookup_count: int


class PathBarProvider[PathBarT](Protocol):
    def fetch_path_bars(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> Mapping[RequestKey, PathBarT]: ...


def _normalize_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RequestSetContractError("decision_time_utc must be timezone-aware")
    return value.astimezone(UTC)


def _timestamp_text(value: datetime) -> str:
    return _normalize_utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def hash_request_set(keys: Iterable[RequestKey]) -> str:
    payload = [
        [
            key.decision_identity,
            key.minute_offset,
            _timestamp_text(key.requested_timestamp_utc),
        ]
        for key in keys
    ]
    return sha256_bytes(canonical_json_bytes(payload))


def _lookup_counts(
    keys: tuple[RequestKey, ...],
    parent_roles: tuple[tuple[str, str], ...],
) -> tuple[int, int]:
    role_by_identity = dict(parent_roles)
    if len(role_by_identity) != len(parent_roles):
        raise RequestSetContractError("parent role identities must be unique")
    key_identities = {key.decision_identity for key in keys}
    if set(role_by_identity) != key_identities:
        raise RequestSetContractError("parent roles must exactly cover request identities")
    if any(role != OUTER_TRAIN_ROLE for role in role_by_identity.values()):
        raise RequestSetContractError("only outer TRAIN parent decisions are permitted")

    validation_count = sum(
        role_by_identity[key.decision_identity] == OUTER_VALIDATION_ROLE
        or (
            OUTER_VALIDATION_BOUNDARY_UTC
            <= key.requested_timestamp_utc
            < FINAL_TEST_BOUNDARY_UTC
        )
        for key in keys
    )
    final_test_count = sum(
        role_by_identity[key.decision_identity] == FINAL_TEST_ROLE
        or key.requested_timestamp_utc >= FINAL_TEST_BOUNDARY_UTC
        for key in keys
    )
    return validation_count, final_test_count


def build_request_set(
    decisions: Iterable[ParentDecision],
    *,
    split_assignment_sha256: str,
) -> SealedRequestSet:
    if split_assignment_sha256 != CELL8_SPLIT_ASSIGNMENT_SHA256:
        raise RequestSetContractError("Cell 8 split-assignment SHA-256 mismatch")

    normalized: list[ParentDecision] = []
    seen_identities: set[str] = set()
    for decision in decisions:
        if not isinstance(decision.decision_identity, str) or not decision.decision_identity:
            raise RequestSetContractError("decision_identity must be a non-empty string")
        if decision.decision_identity in seen_identities:
            raise RequestSetContractError("decision_identity must be unique")
        seen_identities.add(decision.decision_identity)
        if decision.outer_partition != OUTER_TRAIN_ROLE:
            raise RequestSetContractError("only outer TRAIN parent decisions are permitted")
        normalized.append(
            ParentDecision(
                decision_identity=decision.decision_identity,
                decision_time_utc=_normalize_utc(decision.decision_time_utc),
                outer_partition=decision.outer_partition,
            )
        )

    ordered_decisions = sorted(
        normalized,
        key=lambda decision: (decision.decision_time_utc, decision.decision_identity),
    )
    keys = tuple(
        RequestKey(
            decision_identity=decision.decision_identity,
            minute_offset=minute_offset,
            requested_timestamp_utc=decision.decision_time_utc
            + timedelta(minutes=minute_offset),
        )
        for decision in ordered_decisions
        for minute_offset in PATH_OFFSETS
    )
    parent_roles = tuple(
        (decision.decision_identity, decision.outer_partition)
        for decision in ordered_decisions
    )
    validation_count, final_test_count = _lookup_counts(keys, parent_roles)
    if validation_count != 0 or final_test_count != 0:
        raise RequestSetContractError(
            "sealed boundary violation: "
            f"Validation={validation_count}, Final-Test={final_test_count}"
        )

    request_set_sha256 = hash_request_set(keys)
    return SealedRequestSet(
        keys=keys,
        request_set_sha256=request_set_sha256,
        split_assignment_sha256=split_assignment_sha256,
        parent_roles=parent_roles,
        validation_path_bar_lookup_count=validation_count,
        final_test_path_bar_lookup_count=final_test_count,
    )


def fetch_path_bars[PathBarT](
    sealed: SealedRequestSet,
    provider: PathBarProvider[PathBarT],
) -> dict[RequestKey, PathBarT]:
    if sealed.split_assignment_sha256 != CELL8_SPLIT_ASSIGNMENT_SHA256:
        raise RequestSetContractError("Cell 8 split-assignment SHA-256 mismatch")
    validation_count, final_test_count = _lookup_counts(sealed.keys, sealed.parent_roles)
    if validation_count != sealed.validation_path_bar_lookup_count:
        raise RequestSetContractError("Validation lookup counter does not match sealed keys")
    if final_test_count != sealed.final_test_path_bar_lookup_count:
        raise RequestSetContractError("Final-Test lookup counter does not match sealed keys")
    expected_hash = hash_request_set(sealed.keys)
    if not sealed.request_set_sha256 or sealed.request_set_sha256 != expected_hash:
        raise RequestSetContractError("request set must be hashed before provider lookup")
    if validation_count != 0:
        raise RequestSetContractError("Validation path-bar lookup count must be zero")
    if final_test_count != 0:
        raise RequestSetContractError("Final-Test path-bar lookup count must be zero")

    result = dict(
        provider.fetch_path_bars(
            sealed.keys,
            request_set_sha256=sealed.request_set_sha256,
        )
    )
    unsealed_keys = set(result).difference(sealed.keys)
    if unsealed_keys:
        raise RequestSetContractError("provider returned path bars for an unsealed key")
    return result


def build_and_fetch_path_bars[PathBarT](
    decisions: Iterable[ParentDecision],
    *,
    split_assignment_sha256: str,
    provider: PathBarProvider[PathBarT],
) -> tuple[SealedRequestSet, dict[RequestKey, PathBarT]]:
    sealed = build_request_set(
        decisions,
        split_assignment_sha256=split_assignment_sha256,
    )
    return sealed, fetch_path_bars(sealed, provider)

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator, Mapping
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


@dataclass(frozen=True)
class StreamingSealedRequestSet:
    """A sealed request set whose 60x expansion is generated rather than retained."""

    decisions: tuple[ParentDecision, ...]
    request_set_sha256: str
    split_assignment_sha256: str
    parent_roles: tuple[tuple[str, str], ...]
    key_count: int
    validation_path_bar_lookup_count: int
    final_test_path_bar_lookup_count: int


class PathBarProvider[PathBarT](Protocol):
    def fetch_path_bars(
        self,
        request_keys: tuple[RequestKey, ...],
        *,
        request_set_sha256: str,
    ) -> Mapping[RequestKey, PathBarT]: ...


class StreamingPathBarProvider[PathBarT](Protocol):
    def fetch_path_bar_batch(
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


def hash_request_set_incremental(keys: Iterable[RequestKey]) -> str:
    """Reproduce the materialized hash without retaining the canonical payload."""

    digest = hashlib.sha256()
    digest.update(b"[")
    first = True
    for key in keys:
        if not isinstance(key, RequestKey):
            raise RequestSetContractError("request set contains a non-RequestKey value")
        if not first:
            digest.update(b",")
        item = canonical_json_bytes(
            [
                key.decision_identity,
                key.minute_offset,
                _timestamp_text(key.requested_timestamp_utc),
            ]
        )
        digest.update(item[:-1])
        first = False
    digest.update(b"]\n")
    return digest.hexdigest()


def _normalized_ordered_decisions(
    decisions: Iterable[ParentDecision],
    *,
    split_assignment_sha256: str,
) -> tuple[ParentDecision, ...]:
    if split_assignment_sha256 != CELL8_SPLIT_ASSIGNMENT_SHA256:
        raise RequestSetContractError("Cell 8 split-assignment SHA-256 mismatch")

    normalized: list[ParentDecision] = []
    seen_identities: set[str] = set()
    for decision in decisions:
        if not isinstance(decision, ParentDecision):
            raise RequestSetContractError("each decision must be a ParentDecision")
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
    return tuple(
        sorted(
            normalized,
            key=lambda decision: (decision.decision_time_utc, decision.decision_identity),
        )
    )


def _iter_decision_keys(decisions: Iterable[ParentDecision]) -> Iterator[RequestKey]:
    for decision in decisions:
        for minute_offset in PATH_OFFSETS:
            yield RequestKey(
                decision_identity=decision.decision_identity,
                minute_offset=minute_offset,
                requested_timestamp_utc=decision.decision_time_utc
                + timedelta(minutes=minute_offset),
            )


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
    ordered_decisions = _normalized_ordered_decisions(
        decisions,
        split_assignment_sha256=split_assignment_sha256,
    )
    keys = tuple(_iter_decision_keys(ordered_decisions))
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


def build_streaming_request_set(
    decisions: Iterable[ParentDecision],
    *,
    split_assignment_sha256: str,
) -> StreamingSealedRequestSet:
    """Seal the full ordered key identity while retaining only parent decisions."""

    ordered_decisions = _normalized_ordered_decisions(
        decisions,
        split_assignment_sha256=split_assignment_sha256,
    )
    parent_roles = tuple(
        (decision.decision_identity, decision.outer_partition)
        for decision in ordered_decisions
    )
    validation_count = 0
    final_test_count = 0
    key_count = 0

    def validated_keys() -> Iterator[RequestKey]:
        nonlocal validation_count, final_test_count, key_count
        for key in _iter_decision_keys(ordered_decisions):
            key_count += 1
            if (
                OUTER_VALIDATION_BOUNDARY_UTC
                <= key.requested_timestamp_utc
                < FINAL_TEST_BOUNDARY_UTC
            ):
                validation_count += 1
            if key.requested_timestamp_utc >= FINAL_TEST_BOUNDARY_UTC:
                final_test_count += 1
            yield key

    request_set_sha256 = hash_request_set_incremental(validated_keys())
    if validation_count != 0 or final_test_count != 0:
        raise RequestSetContractError(
            "sealed boundary violation: "
            f"Validation={validation_count}, Final-Test={final_test_count}"
        )
    return StreamingSealedRequestSet(
        decisions=ordered_decisions,
        request_set_sha256=request_set_sha256,
        split_assignment_sha256=split_assignment_sha256,
        parent_roles=parent_roles,
        key_count=key_count,
        validation_path_bar_lookup_count=validation_count,
        final_test_path_bar_lookup_count=final_test_count,
    )


def iter_request_keys(sealed: StreamingSealedRequestSet) -> Iterator[RequestKey]:
    if not isinstance(sealed, StreamingSealedRequestSet):
        raise RequestSetContractError("streaming request set type mismatch")
    yield from _iter_decision_keys(sealed.decisions)


def iter_request_key_batches(
    sealed: StreamingSealedRequestSet,
    *,
    batch_size: int,
) -> Iterator[tuple[RequestKey, ...]]:
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise RequestSetContractError("batch_size must be a positive integer")
    batch: list[RequestKey] = []
    for key in iter_request_keys(sealed):
        batch.append(key)
        if len(batch) == batch_size:
            yield tuple(batch)
            batch.clear()
    if batch:
        yield tuple(batch)


def _validate_streaming_seal(sealed: StreamingSealedRequestSet) -> None:
    if sealed.split_assignment_sha256 != CELL8_SPLIT_ASSIGNMENT_SHA256:
        raise RequestSetContractError("Cell 8 split-assignment SHA-256 mismatch")
    if any(role != OUTER_TRAIN_ROLE for _, role in sealed.parent_roles):
        raise RequestSetContractError("only outer TRAIN parent decisions are permitted")
    expected_roles = tuple(
        (decision.decision_identity, decision.outer_partition)
        for decision in sealed.decisions
    )
    if sealed.parent_roles != expected_roles:
        raise RequestSetContractError("parent roles must exactly cover request identities")
    expected_key_count = len(sealed.decisions) * len(PATH_OFFSETS)
    if sealed.key_count != expected_key_count:
        raise RequestSetContractError("streaming request-key count mismatch")
    expected_hash = hash_request_set_incremental(iter_request_keys(sealed))
    if not sealed.request_set_sha256 or sealed.request_set_sha256 != expected_hash:
        raise RequestSetContractError("request set must be hashed before provider lookup")
    validation_count = 0
    final_test_count = 0
    for key in iter_request_keys(sealed):
        if (
            OUTER_VALIDATION_BOUNDARY_UTC
            <= key.requested_timestamp_utc
            < FINAL_TEST_BOUNDARY_UTC
        ):
            validation_count += 1
        if key.requested_timestamp_utc >= FINAL_TEST_BOUNDARY_UTC:
            final_test_count += 1
    if validation_count != sealed.validation_path_bar_lookup_count:
        raise RequestSetContractError("Validation lookup counter does not match sealed keys")
    if final_test_count != sealed.final_test_path_bar_lookup_count:
        raise RequestSetContractError("Final-Test lookup counter does not match sealed keys")
    if validation_count != 0:
        raise RequestSetContractError("Validation path-bar lookup count must be zero")
    if final_test_count != 0:
        raise RequestSetContractError("Final-Test path-bar lookup count must be zero")


def iter_path_bar_batches[PathBarT](
    sealed: StreamingSealedRequestSet,
    provider: StreamingPathBarProvider[PathBarT],
    *,
    batch_size: int,
) -> Iterator[dict[RequestKey, PathBarT]]:
    """Fetch validated batches only after the whole ordered request identity is sealed."""

    _validate_streaming_seal(sealed)
    for request_batch in iter_request_key_batches(sealed, batch_size=batch_size):
        result = dict(
            provider.fetch_path_bar_batch(
                request_batch,
                request_set_sha256=sealed.request_set_sha256,
            )
        )
        unsealed_keys = set(result).difference(request_batch)
        if unsealed_keys:
            raise RequestSetContractError("provider returned path bars for an unsealed key")
        yield result


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

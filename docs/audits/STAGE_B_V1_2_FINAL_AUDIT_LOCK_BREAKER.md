# Stage B V1.2 — Final Audit Lock-Breaker Record

Baseline audited: `a5d3f40e7edc26d950010401654ce4d6b7822e86`

## Verdict

`V1_2_LOCK_BREAKER_FOUND`

## Breaker categories

- `V1_2_LOCK_BREAKER_4`
- `V1_2_LOCK_BREAKER_5`

## Minimal contradiction

Frozen V1.2 architecture requires:

```text
GENERIC SVD / RANK DISCOVERY -> NEVER DIRECT DROP
```

Stable unexplained exact numerical dependency must not create semantic deletion authority; it must OPEN the whole localized component. Unstable, unlocalizable, or numerically inconsistent evidence must fail closed.

The current Stage-B contract at the audited baseline still specifies generic automatic exact-rank deletion after Phase-A semantic resolution, removing exactly `k-r` dimensions via deterministic retention priority. The tests also encode this older behavior, including an example with `c = a + b` that expects `c` to be dropped.

Therefore one compliant implementation cannot simultaneously satisfy the frozen V1.2 generic-discovery firewall and the current V1.1 exact-basis deletion contract.

## Scope / safety observations

- `run_stage_b()` remains fail-closed after Phase A, so no real-data Phase-B generic misdrop occurred at the audited baseline.
- Final Test was not opened.
- Cell 8 assignment rows were not opened.
- No production Stage-B run was executed.
- No repository methodology or production code was patched during the audit.

## Required disposition

V1.2 must not lock until this contradiction is remediated.

The remediation is bounded: align the Stage-B authoritative contract, tests, and eventual Phase-B implementation with the already-frozen V1.2 architecture rule. This is not authorization to redesign V1.2 or introduce new methodology.

After remediation, Issue #8 should resume/continue its same final integration / contradiction / preservation audit from a new remediation commit. New non-lock-breaker improvements belong to V1.3 backlog.

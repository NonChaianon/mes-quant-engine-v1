# Stage B V1.2 lock-breaker 4/5 remediation

- Audit date: 2026-08-15
- Issue: `NonChaianon/mes-quant-engine-v1#9`
- Required baseline: `a5d3f40e7edc26d950010401654ce4d6b7822e86`
- Remediation commit: `8930c4f2b74aff02f190dd563c7657ce119e6ec8`

## Scope and state

This is the bounded remediation of `V1_2_LOCK_BREAKER_4` and
`V1_2_LOCK_BREAKER_5`. It does not redesign methodology, create Architecture
v2.3, implement full Phase B/C/D production execution, or authorize a V1.2
lock. Markdown, JSON, and Python controls remain
`MES_V1_REDUNDANCY_1.2 / PROVISIONAL`.

No real Stage-B production run was performed. Final Test, Validation outcomes,
labels, future returns, P&L, costs, and Cell 8 assignment rows were not opened
or used.

## Exact files changed

The remediation commit changes exactly:

- `.github/workflows/quant-ci-v1.yml`
- `configs/v1/stage_b_semantic_registry_v1.json`
- `docs/STAGE_B_REDUNDANCY_CONTRACT.md`
- `src/mes_quant/redundancy/analyzer.py`
- `src/mes_quant/redundancy/contract.py`
- `tests/test_redundancy.py`

This report is added as the only file in the following audit-documentation
commit:

- `docs/audits/STAGE_B_V1_2_LOCK_BREAKER_4_5_REMEDIATION.md`

## Remediation proof

Generic Phase-B numerical rank/SVD evidence now has discovery authority only:

- stable, localized, unexplained exact dependency -> `OPEN` for every member;
- cohort-conditional but localized dependency -> `OPEN` for every member;
- unstable, unlocalizable, tolerance-inconsistent, or numerically inconsistent
  evidence -> `HARD_FAIL`;
- generic direct-DROP authority is a fail-closed constant set to `False`;
- environment changes cannot resolve generic `OPEN`;
- generic exact-set decision rows reject `KEEP`, `DROP_REDUNDANT`, a chosen
  basis, and a direct substitute;
- Stage-C readiness independently rejects generic exact-set KEEP/DROP rows and
  blocks `OPEN`;
- the former generic group-rank DROP resolver, generic retention chooser, and
  its orphan retention/lookback utilities were removed;
- post-Phase-A condition-number output is `REPORT_ONLY`; rank deficiency
  requests generic discovery and does not select a retained basis.

The isolated generic classifier is not wired into `run_stage_b()`. The sole
production boundary still executes Phase 0 and Phase A, then raises before
unimplemented Phase B work. A static reachability review found no reachable
`DROP_REDUNDANT` literal from that boundary.

Phase-A semantic authority is preserved:

- existing semantic-registry decisions were not changed;
- the baseline and remediation `semantic_checks` objects are exactly equal;
- their canonical SHA256 is
  `53f37c14b3e2b7da2e39ad9a27fe287b1b3a3f362aeca375a2adc02f28a74cff`;
- weekday reference selection remains behind an explicit
  `EXACT_AFFINE_DEPENDENCY` plus
  `DROP_ONE_DETERMINISTIC_REFERENCE_KEEP_FOUR_DIMENSIONS` registry guard;
- Phase-A integration and protected-basis tests remain green.

Current provisional control-byte bindings:

- Markdown SHA256:
  `173afa7e26717795abb88eef1880af1ce8e3cecca133604840942fa8c6d12a96`
- semantic-registry SHA256:
  `056ba7639960c8dd9c65d7e6a7a6a383e432a069651503def8bf05e3cafed861`

## Verification results

All commands ran from the Issue #9 branch at the remediation contents. Exit
codes are exact.

| Verification | Result | Exit code |
|---|---:|---:|
| `git diff --check` | PASS | 0 |
| `python -m compileall -q src tests tools` | PASS | 0 |
| `python -m ruff check --select E9,F401,F63,F7,F82 src tests tools` | PASS (`All checks passed!`) | 0 |
| raw SHA / version / status / baseline `semantic_checks` audit | PASS | 0 |
| direct constitutional + project-root gate tests | 10 passed | 0 |
| focused Phase 0/A + generic-rank + production-boundary tests | 63 passed | 0 |
| checkout-safe full `tests/test_redundancy.py` | 161 passed, 15 deselected | 0 |
| `tests/test_manifest.py tests/test_feature_builder.py tests/test_reference_freeze.py` | 26 passed, 1 skipped | 0 |

The focused run used these exact classes:

- `StageBPhase0FirewallSpecificationTests`
- `StageBPhase0FullOrchestrationSpecificationTests`
- `StageBPhase0ProductionOrchestrationSpecificationTests`
- `StageBPhaseASemanticIntegrationSpecificationTests`
- `StageBGenericRankAuthorityV12SpecificationTests`
- `StageBGroupRankAndPhaseCSensitivitySpecificationTests`
- `StageBProductionBoundarySpecificationTests`

The separate 10-test gate run used
`StageBConstitutionalPolicyGateDirectTests` and
`StageBProjectRootGateSpecificationTests`.

The 15 deselections are the frozen canonical Cell14 registry compatibility test
and `StageBPhaseADecisionBridgeRedSpecificationTests`. They require
`artifacts/runs/cell14_20260809T175203Z/cell14_feature_registry_v1.csv`, which is
not present in this checkout. This matches the repository's checkout-safe CI
branch; the absence is recorded as an environmental exclusion, not a pass.

## Independent-audit handoff

Issue #8 may resume from remediation commit
`8930c4f2b74aff02f190dd563c7657ce119e6ec8` only after this PR receives
independent review. This PR must not be merged or used to lock V1.2 by the
remediation author.

`LOCK_BREAKER_4_5_REMEDIATED`

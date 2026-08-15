# TREE001 Execution Authorization

Status: `AUTHORIZED_PENDING_MERGE`

Recorded after canonical preflight and before any TREE001 realized-label execution.

## Owner authorization

Owner chat authorization on 2026-08-16 (UTC+07):

`อนุมัติ TREE001 real TRAIN-only execution`

Authorization reference: Issue #28.

## Authorized experiment

- Experiment ID: `MES_S1_TREE001_20260815T192900Z`
- Candidate ID: `TREE001`
- Candidate number: `2 / 2`
- Model: `BOUNDED_SHALLOW_DECISION_TREE`
- Frozen implementation baseline before this authorization PR: `ec6633de4f4b7b1a0f246c8ccabebb859bfe01c7`
- Execution token marker: `OWNER_AUTHORIZED_TREE001_20260816`

## Scope

This authorization permits exactly one real target-aware TREE001 execution using the already-frozen Issue #28 specification.

Allowed:

- canonical Cell14 locked29 features;
- canonical Cell10 realized labels restricted to `outer_partition == TRAIN`;
- `WF_2022` and `WF_2023` target-aware holdouts only;
- immutable experiment record under the frozen experiment ID.

Forbidden:

- `WF_2024` target-aware holdout;
- outer Validation outcomes;
- Final Test;
- model tuning, calibration changes, threshold changes, pruning, hyperparameter search, rescue rerun, or overwrite;
- any TREE002, ensemble follow-up, SMALL_FEATURE_RULE, or other additional Sprint-1 target-aware candidate after TREE001.

## One-shot consequence

If TREE001 fails the frozen primary rule, Sprint 1 closes with:

`NO_USABLE_EDGE_IDENTIFIED_IN_TESTED_SPRINT_1_SCOPE`

If TREE001 passes, it is exploratory promotion only. It does not confirm an edge. Exactly one confirmatory hypothesis and a separate Validation protocol/budget must be frozen before any Validation opening.

Validation remains unopened and Final Test remains sealed by this authorization.

# MES Quant Engine — Architecture Progress

**Architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `Exploratory Lane — first authorized L1 experiment implementation`

**Current milestone:** `MES_S1_LR001_20260815T095100Z`

**Current gate:** `Issue #26 — build/test/merge the TRAIN-only LR001 adapter before first realized-label execution`

> This file is the project-level progress source of truth. Mathematical/methodological authority remains in the applicable locked contract or research protocol; the target architecture explains where we are going.

---

## Current position

```text
Architecture:                   v2.2 — BASELINE_ACCEPTED / DESIGN_CLOSED
Current plane:                  PLANE A — RESEARCH / OFFLINE
A6 / Stage B V1.2:              LOCKED on main
Stage-B policy controls:        LOCKED
Stage-B artifact execution:     DISABLED / pre-I/O gate
A6 lock merge:                  99b5f3302e28523293d31e7df49eb03cff466e2c
LABEL_EXPOSURE_PRE_FIREWALL_V1: COMPLETE
Acknowledgment merge:           1c6512615a40dbc35a394ed241fde30d18b5dede
Exploratory Lane V1 charter:    COMPLETE / FROZEN
Charter merge:                  ed2980c7fc50cf936494e6f750bbea8d0d78926a
Sprint 1 protocol:              COMPLETE / FROZEN
Protocol merge:                 17f9fb08c5e5f1e8d672b7f36747b726e1c212a3
Sprint 1 dry-run harness:       COMPLETE / MERGED
Harness merge:                  a03eac7485389e4774ce31b1b8c93c4428b0d4f3
L1 owner authorization:         GRANTED 2026-08-15
First experiment ID:            MES_S1_LR001_20260815T095100Z
Current implementation issue:   #26
Current observed data access:   L0 during code authoring / synthetic tests only
Authorized next data access:    L1 TRAIN realized labels only
Validation:                     UNOPENED
Final Test:                     SEALED
Live trading:                   DISABLED
Real Stage B production runs:   0
Sprint 1 real-data runs:        0
```

Authorization and observed access are deliberately separated. The owner has authorized L1, but branch/CI authoring remains L0 until an accepted local runner actually deserializes TRAIN realized labels.

---

## A6 / Stage B V1.2 closure

Stage B V1.2 is locked on `main` by PR #17 at:

`99b5f3302e28523293d31e7df49eb03cff466e2c`

Locked machine state:

```text
POLICY_STATUS                    LOCKED
Markdown policy status           LOCKED
Semantic-registry status         LOCKED
EXECUTION_STATUS                 DISABLED
```

Policy lock does not imply execution enablement. Stage-B execution remains disabled before control/artifact I/O. Locked methodology is reopened only for a documented defect/version bump.

---

## Accepted exploratory authorities

### Exploratory Lane V1

Accepted charter:

`docs/research/EXPLORATORY_LANE_V1_CHARTER.md`

merge:

`ed2980c7fc50cf936494e6f750bbea8d0d78926a`

Key boundary: L1 is TRAIN-only; Validation is forbidden during exploration; Final Test remains sealed; every label-aware execution requires a unique `EXPERIMENT_ID`; canonical upstream artifacts remain read-only; exploratory evidence has no Release-Gate authority.

### Edge Discovery Sprint 1 protocol

Accepted protocol:

`docs/research/EDGE_DISCOVERY_SPRINT_1_PROTOCOL.md`

merge:

`17f9fb08c5e5f1e8d672b7f36747b726e1c212a3`

Frozen scope:

```text
EXPLORATION_SCOPE_ID        MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M
market                      MES
spacing                     15m
horizon                     +60m
features                    locked Cell 14 V1 universe only
research action             LONG / FLAT
Sprint target               LONG=1; SHORT/NO_TRADE=0
cost                        CONSERVATIVE / USD 4.97 RT / 0.994 points
required baselines          ALWAYS_FLAT + fold-correct TRAIN_PRIOR_PROBABILITY
primary metric              OOF_BINARY_LOG_LOSS
primary improvement         baseline log loss - candidate log loss
continuation                overall improvement > 0 AND median fold improvement > 0
Validation                  FORBIDDEN
Final Test                  SEALED
```

### Dry-run harness

Issue #24 / PR #25 is complete and merged as:

`a03eac7485389e4774ce31b1b8c93c4428b0d4f3`

The accepted harness provides protocol constants, experiment-spec validation, fold-correct prior evaluation, binary log loss, Brier score, strict continuation logic, and experiment-history construction using synthetic arrays only.

---

## Current L1 gate — Issue #26 / LR001

Owner authorization has been recorded before any new target-aware run.

```text
EXPERIMENT_ID              MES_S1_LR001_20260815T095100Z
EXPLORATION_SCOPE_ID       MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M
candidate family           REGULARIZED_LOGISTIC_REGRESSION
feature set                all 29 locked Cell 14 V1 features
outer partition            TRAIN only
OOF folds                  WF_2022 + WF_2023 only
WF_2024                    FORBIDDEN (2024 is outer Validation)
primary metric             OOF_BINARY_LOG_LOSS
Validation                 UNOPENED / FORBIDDEN
Final Test                 SEALED
```

The strongest existing Cell 8 purged chronological folds wholly contained inside outer TRAIN are reused:

- `WF_2022`: expanding TRAIN through 2021 -> 2022 holdout;
- `WF_2023`: expanding TRAIN through 2022 -> 2023 holdout.

Both retain the frozen +60m purge semantics. `WF_2024` is excluded because its holdout is 2024, the outer Validation partition.

The LR001 numerical policy was frozen on Issue #26 before target-aware execution: fold-local z-score; no imputation; L2 lambda `0.001`; unpenalized intercept; deterministic Newton/IRLS with frozen convergence/backtracking settings; no hyperparameter search; diagnostic action threshold `0.5` only.

Implementation under the current branch may add the TRAIN-only reader, exact artifact-identity gates, deterministic candidate, diagnostics, and experiment logger. GitHub CI and local dry-run must remain synthetic-only. Real L1 access occurs only in the separately executed accepted runner.

---

## Architecture-stage tracker

| Stage | Scope | Status | Evidence / current position | Exit gate / next action |
|---|---|---|---|---|
| Plane 0 | Governance & provenance foundation | IN_PROGRESS | Controls added only as required by active research | Avoid institutional overbuild |
| A1 | Data Foundation | LOCKED | Canonical MES history and PIT controls established | Reopen only for documented defect/version bump |
| A2 | Decision Universe | LOCKED | Purged chronological assignments frozen | Reopen only for documented defect/version bump |
| A3 | Cost & Impact Model | DEFERRED | Full production stack deferred; Sprint uses frozen conservative reference | Do not retune Sprint cost |
| A4 | Label / Target Contract | IN_PROGRESS | Cell 10 canonical labels preserved; Sprint binary mapping frozen | Authorized TRAIN-only use under LR001 |
| A5 | Feature Construction | LOCKED | Cell 14 V1 / 29 candidate features; BL-30 exact reproduction accepted | Reopen only for documented defect/version bump |
| **A6** | **Target-Blind Redundancy / Stage B** | **LOCKED** | Policy locked; execution disabled | **Reopen only for documented defect/version bump** |
| A7 | Regime / Context | DEFERRED | Outside Sprint 1 | Do not build before evidence |
| **A8** | **Label Materialization / Access Control** | **IN_PROGRESS** | L0/L1/L2/L3 boundary frozen; L1 owner authorization granted | Execute only accepted LR001 TRAIN-only path |
| **Exploratory Lane** | **TRAIN-only edge discovery** | **IN_PROGRESS** | Charter/protocol/harness frozen; LR001 adapter candidate in Issue #26 | **GREEN CI + local synthetic dry-run + owner merge -> run LR001** |
| A9 | Predictive Model Layer | NOT_STARTED | Confirmatory layer not built | Start only after Sprint continuation evidence |
| A10 | Validation & Model Selection | NOT_STARTED | Validation unopened | Freeze confirmatory protocol + opening budget before L2 |
| A11 | Calibration | NOT_STARTED | Architecture only | After confirmatory path |
| A12 | Net EV | NOT_STARTED | Architecture only | After confirmatory evidence |
| A13 | Risk & Sizing Simulation | NOT_STARTED | Architecture only | After confirmatory evidence |
| A14 | Execution Simulation / Parity | NOT_STARTED | Architecture only | Before production promotion |
| Release Gate | Research -> production | NOT_STARTED | No release candidate | Implement later |
| Plane B | Production / Online | NOT_STARTED | Live disabled | No production promotion yet |
| Plane C | Feedback & Control | NOT_STARTED | Architecture only | Build with production readiness |
| Watchdog | Independent safety | NOT_STARTED | Required before meaningful live trading | Implement/test before live |

---

## Frozen next sequence

```text
1. Implement LR001 TRAIN-only adapter/model/logger under Issue #26 using synthetic tests only
2. GitHub CI GREEN
3. Local VS Code compile/Ruff/synthetic LR001 tests + preflight
4. Owner merge authorization for LR001 implementation PR
5. Merge accepted LR001 runner
6. Sync local main and execute MES_S1_LR001_20260815T095100Z once
7. Persist/report experiment record and frozen disposition
8. If INTERESTING_ENOUGH_TO_CONTINUE: freeze confirmatory hypothesis + Validation protocol before any L2 access
9. If not: record NO_USABLE_EDGE_IDENTIFIED_IN_SPRINT_1_SCOPE for the governed scope
```

No Validation or Final-Test opening is authorized by Issue #26.

---

## Label-access roadmap

| Level | Access | Project use |
|---|---|---|
| L0 | governance/contracts/synthetic arrays only | current branch/CI authoring |
| L1 | TRAIN realized labels | authorized LR001 and logged Sprint exploration |
| L2 | Validation labels/results | still forbidden; future frozen confirmatory protocol only |
| L3 | Final Test | sealed one-time final confirmation |

Work classification is derived from observed access. Permission to use L1 does not make synthetic implementation work L1; actual row access does.

---

## Evidence discipline

- `BLOCKED` means a proven gate failure prevents advancement.
- `READY_FOR_AUDIT` means candidate work exists but required acceptance is pending.
- `LOCKED` means the applicable exit gate is frozen.
- GitHub CI verifies engineering/test invariants; it does not authorize merge or L2/L3 access.
- Update this dashboard only when the answer to “where are we now?” materially changes.

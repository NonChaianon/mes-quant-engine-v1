# MES Quant Engine — Architecture Progress

**Architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `Exploratory Lane — Sprint 1 harness build`

**Current milestone:** `SPRINT_1_DRY_RUN_HARNESS`

**Current gate:** `SPRINT_1_DRY_RUN_HARNESS — owner review + local dry-run confirmation required`

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
Current milestone:              SPRINT_1_DRY_RUN_HARNESS
Current work access:            L0 / synthetic-only
L1 TRAIN-label exploration:     NOT STARTED / NOT AUTHORIZED
Validation:                     UNOPENED
Final Test:                     SEALED
Live trading:                   DISABLED
Real Stage B production runs:   0
Sprint 1 real-data runs:        0
```

The Sprint-1 protocol is now frozen on `main`. The current candidate work builds only the synthetic/dry-run evaluation and experiment-governance harness. It deliberately contains no realized-label reader or project-data adapter.

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

## Pre-firewall label exposure boundary

`LABEL_EXPOSURE_PRE_FIREWALL_V1` is complete and committed in:

`docs/audits/LABEL_EXPOSURE_PRE_FIREWALL_V1.md`

It records historical exposure conservatively without reopening realized-label rows and preserves unknown historical facts as unknown.

---

## Exploratory Lane V1 charter

Issue #20 is complete. The accepted charter is:

`docs/research/EXPLORATORY_LANE_V1_CHARTER.md`

merged as:

`ed2980c7fc50cf936494e6f750bbea8d0d78926a`

The charter freezes lane-level rules: future L1 access is TRAIN-only; Validation is forbidden during exploration; Final Test remains sealed; every label-aware run requires a unique `EXPERIMENT_ID`; search history must be preserved; canonical upstream artifacts remain read-only; exploratory evidence has no Release-Gate authority.

---

## Edge Discovery Sprint 1 protocol

Issue #22 is complete. The accepted protocol is:

`docs/research/EDGE_DISCOVERY_SPRINT_1_PROTOCOL.md`

merged as:

`17f9fb08c5e5f1e8d672b7f36747b726e1c212a3`

Frozen Sprint-1 decisions include:

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

Allowed model families remain deliberately simple: regularized logistic regression, bounded shallow trees/ensemble, and predeclared small-feature rules. HMM/GARCH/deep learning/stacking/model-zoo/macro-regime expansion remain outside Sprint 1.

Protocol freeze did not authorize a label read or Sprint run by itself.

---

## Current dry-run harness gate

Issue #24 builds a minimal synthetic-testable harness under:

`src/mes_quant/exploration/`

Current candidate boundary:

```text
HARNESS_EXECUTION_STATUS            DRY_RUN_ONLY_L0
realized TRAIN label I/O            NOT IMPLEMENTED
project-data path knowledge         NOT IMPLEMENTED
Validation reader                   NOT IMPLEMENTED
Final-Test reader                   NOT IMPLEMENTED
real model fit on project data      0
Sprint 1 real-data runs             0
```

The dry-run harness may encode the frozen protocol constants, validate experiment metadata and feature subsets against the locked Cell 14 universe, evaluate caller-supplied synthetic arrays, compute fold-correct prior/log-loss/Brier results, apply the frozen continuation rule, and construct an in-memory experiment-history record.

It may not open project label artifacts. The actual TRAIN-only data adapter is a separate next gate after this harness is accepted and the owner explicitly authorizes first L1 access.

---

## Architecture-stage tracker

| Stage | Scope | Status | Evidence / current position | Exit gate / next action |
|---|---|---|---|---|
| Plane 0 | Governance & provenance foundation | IN_PROGRESS | Controls added only as required by active research | Avoid institutional overbuild |
| A1 | Data Foundation | LOCKED | Canonical MES history and PIT controls established | Reopen only for documented defect/version bump |
| A2 | Decision Universe | LOCKED | Decision/session/horizon-safe universe established | Reopen only for documented defect/version bump |
| A3 | Cost & Impact Model | DEFERRED | Full production cost stack deferred | Sprint 1 uses frozen conservative cost reference only |
| A4 | Label / Target Contract | IN_PROGRESS | Historical Cell 10 labels preserved; Sprint-1 binary mapping frozen by protocol | L1 use only after explicit authorization |
| A5 | Feature Construction | LOCKED | Canonical Cell 14 V1, 29 candidate features; BL-30 exact reproduction accepted | Reopen only for documented defect/version bump |
| **A6** | **Target-Blind Redundancy / Stage B** | **LOCKED** | Final audit accepted; breakers remediated; policy locked; execution disabled | **Reopen only for documented defect/version bump** |
| A7 | Regime / Context | DEFERRED | Not required for Sprint 1 | Do not build before Sprint evidence justifies continuation |
| **A8** | **Label Materialization / Access Control** | **IN_PROGRESS** | Pre-firewall acknowledgment complete; L0/L1/L2/L3 boundary established | Explicit first L1 authorization remains pending |
| **Exploratory Lane** | **TRAIN-only edge discovery** | **IN_PROGRESS** | Charter + Sprint-1 protocol frozen; dry-run harness candidate under Issue #24 | **Accept harness -> explicitly authorize first L1 adapter/run** |
| A9 | Predictive Model Layer | NOT_STARTED | Confirmatory layer intentionally not built ahead of edge evidence | Start only after Sprint yields lockable hypothesis |
| A10 | Validation & Model Selection | NOT_STARTED | Validation remains unopened | Freeze confirmatory protocol + opening budget before first L2 access |
| A11 | Calibration | NOT_STARTED | Architecture only | After confirmatory hypothesis survives appropriate path |
| A12 | Net EV | NOT_STARTED | Architecture only | After model/calibration/cost evidence exists |
| A13 | Risk & Sizing Simulation | NOT_STARTED | Architecture only | After edge survives confirmatory research |
| A14 | Execution Simulation / Parity | NOT_STARTED | Architecture only | Required before production promotion |
| Release Gate | Research -> production | NOT_STARTED | Architecture only | Implement when release candidate exists |
| Plane B | Production / Online | NOT_STARTED | Live disabled | No production promotion before Release Gate |
| Plane C | Feedback & Control | NOT_STARTED | Architecture only | Build with production readiness |
| Watchdog | Independent safety | NOT_STARTED | Required before meaningful live trading | Implement/test before live enablement |

---

## Frozen next sequence

```text
1. Build + synthetic-test SPRINT_1_DRY_RUN_HARNESS at L0
2. Owner review + local VS Code dry-run confirmation
3. Merge accepted harness
4. Explicit owner authorization for first L1 TARGET_AWARE_EXPERIMENT
5. Implement/use the minimal TRAIN-only data adapter + candidate path under that authorization
6. RUN EDGE DISCOVERY SPRINT 1
7. Apply the frozen continuation/no-edge criterion
8. If interesting enough: freeze confirmatory hypothesis + Validation protocol before any L2 access
```

Do not build A7/A9+ institutional machinery ahead of this empirical proof point unless a concrete Sprint requirement forces it.

---

## Label-access roadmap

| Level | Access | Project use |
|---|---|---|
| L0 | contract/governance/synthetic arrays only; no new realized-label rows | current dry-run harness build |
| L1 | TRAIN realized labels | Exploratory Lane; every run is `TARGET_AWARE_EXPERIMENT` with `EXPERIMENT_ID` |
| L2 | Validation labels/results | frozen confirmatory protocol; budgeted openings only |
| L3 | Final Test | sealed one-time final confirmation |

Work classification is derived from observed access. Human labels cannot downgrade an L1/L2/L3 run.

---

## Evidence discipline

- `BLOCKED` means a proven gate failure prevents advancement.
- `READY_FOR_AUDIT` means candidate work exists but required acceptance is pending.
- `LOCKED` means the applicable exit gate is frozen.
- A local/chat result alone cannot promote a project stage.
- Update this dashboard only when the answer to “where are we now?” materially changes.

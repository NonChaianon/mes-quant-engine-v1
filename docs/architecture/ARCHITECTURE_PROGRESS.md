# MES Quant Engine — Architecture Progress

**Architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `Exploratory Lane — Sprint 1 protocol freeze`

**Current milestone:** `EDGE_DISCOVERY_SPRINT_1_PROTOCOL`

**Current gate:** `EDGE_DISCOVERY_SPRINT_1_PROTOCOL — owner review and accepted merge required`

> This file is the project-level progress source of truth. Mathematical/methodological authority remains in the applicable stage contract; the target architecture explains where we are going.

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
Current milestone:              EDGE_DISCOVERY_SPRINT_1_PROTOCOL
Current work access:            L0 governance-only
L1 TRAIN-label exploration:     NOT STARTED / NOT YET AUTHORIZED
Validation:                     UNOPENED
Final Test:                     SEALED
Live trading:                   DISABLED
Real Stage B production runs:   0
Sprint 1 runs:                  0
```

The accepted charter defines the future L1 lane. The current protocol candidate freezes Sprint 1 scope, target mapping, cost assumption, baselines, primary metric, diagnostics, candidate families, and continuation/no-edge criteria before any realized TRAIN-label run.

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

The charter freezes lane-level rules:

- future L1 access is TRAIN data + TRAIN realized labels only;
- Validation is forbidden during exploration;
- Final Test remains sealed;
- every label-aware run requires a unique `EXPERIMENT_ID`;
- search history must be logged;
- canonical upstream artifacts remain read-only;
- exploratory evidence has no Release-Gate authority;
- no L2 opening before confirmatory hypothesis + Validation protocol freeze;
- no Exploratory Lane V2 before Sprint 1 runs.

The charter merge did not itself exercise L1.

---

## Current Sprint 1 protocol gate

Candidate artifact:

`docs/research/EDGE_DISCOVERY_SPRINT_1_PROTOCOL.md`

Frozen candidate decisions include:

```text
EXPLORATION_SCOPE_ID
MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M

market                  MES
spacing                 15m
horizon                 +60m
features                locked Cell 14 V1 universe only
research action         LONG / FLAT
Sprint target           LONG=1; SHORT/NO_TRADE=0
cost                    CONSERVATIVE / USD 4.97 round trip / 0.994 points
required baselines      ALWAYS_FLAT + fold-correct TRAIN_PRIOR_PROBABILITY
primary metric          OOF_BINARY_LOG_LOSS
primary improvement     baseline log loss - candidate log loss
continuation            overall improvement > 0 AND median fold improvement > 0
Validation              FORBIDDEN
Final Test              SEALED
```

Allowed model families are deliberately simple: regularized logistic regression, bounded shallow trees/ensemble, and predeclared small-feature rules. HMM/GARCH/deep learning/stacking/model-zoo/macro-regime expansion are outside Sprint 1.

Protocol authoring remains L0. No Sprint result has been observed.

---

## Architecture-stage tracker

| Stage | Scope | Status | Evidence / current position | Exit gate / next action |
|---|---|---|---|---|
| Plane 0 | Governance & provenance foundation | IN_PROGRESS | Controls added only as required by active research | Avoid institutional overbuild |
| A1 | Data Foundation | LOCKED | Canonical MES history and PIT controls established | Reopen only for documented defect/version bump |
| A2 | Decision Universe | LOCKED | Decision/session/horizon-safe universe established | Reopen only for documented defect/version bump |
| A3 | Cost & Impact Model | DEFERRED | Full production cost stack deferred | Sprint 1 freezes only existing conservative cost assumption |
| A4 | Label / Target Contract | IN_PROGRESS | Historical Cell 10 labels preserved; Sprint-1 Long/Flat mapping proposed separately | Accept protocol before first L1 use |
| A5 | Feature Construction | LOCKED | Canonical Cell 14 V1, 29 candidate features; BL-30 exact reproduction accepted | Reopen only for documented defect/version bump |
| **A6** | **Target-Blind Redundancy / Stage B** | **LOCKED** | Final audit accepted; breakers remediated; policy locked; execution disabled | **Reopen only for documented defect/version bump** |
| A7 | Regime / Context | DEFERRED | Not required for Sprint 1 | Do not build before Sprint evidence justifies continuation |
| **A8** | **Label Materialization / Access Control** | **IN_PROGRESS** | Pre-firewall acknowledgment complete; L0/L1/L2/L3 boundary established | First L1 access only after protocol acceptance and explicit run authorization |
| **Exploratory Lane** | **TRAIN-only edge discovery** | **IN_PROGRESS** | V1 charter frozen; Sprint 1 protocol candidate created at L0 | **Owner acceptance/merge of protocol -> build minimal experiment harness -> explicit first L1 run** |
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
1. Owner-review and merge EDGE_DISCOVERY_SPRINT_1_PROTOCOL
2. Build minimal Sprint-1 experiment harness without opening labels during build where avoidable
3. Verify experiment logging + L1 access boundary
4. Explicitly authorize first TARGET_AWARE_EXPERIMENT / L1 TRAIN-label run
5. RUN EDGE DISCOVERY SPRINT 1
6. Apply frozen continuation/no-edge criterion
7. If interesting enough: freeze confirmatory hypothesis + Validation protocol before any L2 access
```

Do not build A7/A9+ institutional machinery ahead of this empirical proof point unless a concrete Sprint requirement forces it.

---

## Label-access roadmap

| Level | Access | Project use |
|---|---|---|
| L0 | contract/governance evidence only; no new realized-label rows | current protocol authoring |
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

# MES Quant Engine — Architecture Progress

**Architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `Exploratory Lane — governance setup`

**Current milestone:** `EXPLORATORY_LANE_V1_CHARTER`

**Current gate:** `EXPLORATORY_LANE_V1_CHARTER — owner review and accepted merge required`

> This file is the project-level progress source of truth. It tracks **where we are**. Mathematical/methodological authority remains in the applicable stage contract; the target architecture explains **where we are going**.

---

## Status vocabulary

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_AUDIT`
- `LOCKED`
- `DEFERRED`
- `REJECTED`

Do not use a fake project-completion percentage.

---

## Current position

```text
Architecture:                   v2.2 — BASELINE_ACCEPTED / DESIGN_CLOSED
Current plane:                  PLANE A — RESEARCH / OFFLINE
A6 / Stage B V1.2:              LOCKED on main
Stage-B policy controls:        LOCKED
Stage-B artifact execution:     DISABLED / pre-I/O gate
A6 lock merge:                  99b5f3302e28523293d31e7df49eb03cff466e2c
LABEL_EXPOSURE_PRE_FIREWALL_V1: COMPLETE / Issue #18 CLOSED
Acknowledgment merge:           1c6512615a40dbc35a394ed241fde30d18b5dede
Current milestone:              EXPLORATORY_LANE_V1_CHARTER
Current work access:            L0 governance-only
L1 TRAIN-label exploration:     NOT STARTED / NOT YET AUTHORIZED
Validation:                     UNOPENED for current research path
Final Test:                     SEALED
Live trading:                   DISABLED
Real Stage B production runs:   0
```

The current charter PR describes the future L1 boundary but does not itself exercise L1. Sprint 1 may not begin until both the charter and the separate Sprint 1 protocol have been accepted.

---

## A6 / Stage B V1.2 closure

Stage B V1.2 was independently accepted and locked on `main` by PR #17:

`99b5f3302e28523293d31e7df49eb03cff466e2c`

Locked machine state:

```text
POLICY_STATUS                    LOCKED
Markdown policy status           LOCKED
Semantic-registry status         LOCKED
EXECUTION_STATUS                 DISABLED
```

Policy lock does not imply execution enablement. Stage-B execution remains disabled before control/artifact I/O. Phase B/C/D production execution remains unimplemented/not authorized by the lock.

Accepted control provenance:

- locked-control commit: `bb68e6d8be9244564c2d06179cffde775041c8f3`
- non-self-referential Python pin commit: `131cf7a37d0beb41bf258ffa9beaf942c443985d`
- final audit: `SAFE_TO_LOCK_V1_2`
- Issue #9 generic-rank breaker remediation: accepted/merged
- Issue #15 policy/execution separation remediation: accepted/merged
- rejected PR #14: closed unmerged; no authority

Audit/lock records remain under `docs/audits/` and locked methodology is reopened only for a documented defect/version bump.

---

## Pre-firewall label exposure boundary

Issue #18 / `LABEL_EXPOSURE_PRE_FIREWALL_V1` is complete and merged as:

`1c6512615a40dbc35a394ed241fde30d18b5dede`

Artifact:

`docs/audits/LABEL_EXPOSURE_PRE_FIREWALL_V1.md`

It conservatively records historical exposure without reopening realized-label rows. It distinguishes known historical facts, repository-corroborated aggregate evidence, and unknown/not-reconstructable exposure.

The acknowledgment itself used L0 governance-only access. Validation and Final Test were not opened.

---

## Architecture-stage tracker

| Stage | Scope | Status | Evidence / current position | Exit gate / next action |
|---|---|---|---|---|
| Plane 0 | Governance & provenance foundation | IN_PROGRESS | Required controls are added only as needed by the active research stage | Avoid institutional overbuild before empirical evidence |
| A1 | Data Foundation | LOCKED | Canonical MES historical data, PIT controls, gap/roll/session audits established | Reopen only for documented defect/version bump |
| A2 | Decision Universe | LOCKED | Eligibility/session/horizon-safe decision universe established | Reopen only for documented defect/version bump |
| A3 | Cost & Impact Model | DEFERRED | Historical cost assumptions exist; full production stack intentionally deferred | Freeze the Sprint-specific cost assumption in Sprint 1 protocol |
| A4 | Label / Target Contract | IN_PROGRESS | Historical Cell 10 target logic exists; label access is now governed separately | Freeze Sprint target/cost references before L1 execution |
| A5 | Feature Construction | LOCKED | Canonical Cell 14 V1 feature build, 29 candidate features; BL-30 exact reproduction accepted | Reopen only for documented defect/version bump |
| **A6** | **Target-Blind Redundancy / Stage B** | **LOCKED** | Final audit accepted; breaker remediations merged; PR #17 lock accepted; execution independently disabled | **Reopen only for documented defect/version bump** |
| A7 | Regime / Context | DEFERRED | Not required before first Edge Sprint | Do not build before Sprint evidence justifies continuation |
| **A8** | **Label Materialization / Access Control** | **IN_PROGRESS** | `LABEL_EXPOSURE_PRE_FIREWALL_V1` complete; L0/L1/L2/L3 boundary defined | Complete charter + Sprint protocol before first new L1 run |
| **Exploratory Lane** | **TRAIN-only edge discovery** | **READY_FOR_AUDIT** | V1 charter candidate created under Issue #20; no L1 experiment has begun | **Owner acceptance/merge of charter -> freeze Sprint 1 protocol** |
| A9 | Predictive Model Layer | NOT_STARTED | Intentionally not built ahead of edge evidence | Confirmatory work only after Sprint produces a lockable hypothesis |
| A10 | Validation & Model Selection | NOT_STARTED | Validation remains clean during L1 exploration | Freeze validation protocol and opening budget before first L2 access |
| A11 | Calibration | NOT_STARTED | Architecture only | Build after predictive hypothesis survives validation path |
| A12 | Net EV | NOT_STARTED | Architecture only | Build after model/calibration/cost evidence exists |
| A13 | Risk & Sizing Simulation | NOT_STARTED | Architecture only | Build after edge survives confirmatory research |
| A14 | Execution Simulation / Parity | NOT_STARTED | Architecture only | Required before production promotion |
| Release Gate | Research -> production | NOT_STARTED | Gate categories defined in v2.2 | Implement when a release candidate exists |
| Plane B | Production / Online | NOT_STARTED | Live trading disabled | No production promotion before Release Gate evidence |
| Plane C | Feedback & Control | NOT_STARTED | Architecture only | Build with production readiness |
| Watchdog | Independent safety process | NOT_STARTED | Required before meaningful live trading | Implement/test before live enablement |

---

## Current Exploratory Lane gate

Current artifact under review:

`docs/research/EXPLORATORY_LANE_V1_CHARTER.md`

Current work boundary:

```text
charter-authoring observed access     L0
new realized TRAIN labels             0
Validation outcomes                   0 / FORBIDDEN
Final Test                            SEALED
Sprint 1 runs                         0
```

The charter freezes the lane-level rules only. It deliberately does not choose the Sprint 1 primary metric, cost assumption, continuation threshold, baselines, or no-edge criterion.

Acceptance of the charter authorizes only the next governance step: create and freeze the Sprint 1 protocol.

---

## Frozen next sequence

```text
1. Accept / merge EXPLORATORY_LANE_V1 charter
2. Freeze Edge Discovery Sprint 1 protocol:
   - EXPLORATION_SCOPE_ID
   - project continuation / falsification policy
   - baseline(s), including ALWAYS_FLAT
   - exactly one primary decision metric
   - diagnostic secondary metrics
   - frozen cost assumption
   - predeclared interesting-enough continuation criterion
   - current-scope no-edge criterion
3. Accept / merge Sprint 1 protocol
4. Begin explicitly authorized L1 TRAIN-label experiments
5. RUN EDGE DISCOVERY SPRINT 1
```

Do not build A7/A9+ institutional machinery ahead of the empirical proof point unless a concrete Sprint requirement forces it.

---

## Label-access roadmap

| Level | Access | Project use |
|---|---|---|
| L0 | target contract / governance evidence only; no new realized-label rows | governance and charter/protocol authoring |
| L1 | TRAIN realized labels | Exploratory Lane; every accessing run is `TARGET_AWARE_EXPERIMENT` with `EXPERIMENT_ID` |
| L2 | Validation labels/results | frozen confirmatory protocol; budgeted openings only |
| L3 | Final Test | sealed one-time final confirmation |

Work classification is derived from observed access. Human labels cannot downgrade an L1/L2/L3 run.

---

## Evidence discipline

- `BLOCKED` means a predefined gate failure is proven and must be resolved before advancement.
- `READY_FOR_AUDIT` means the required candidate is complete but acceptance has not completed.
- `LOCKED` means the applicable exit gate has passed and the versioned authority is frozen.
- A local result or chat statement alone is insufficient to mark a stage `LOCKED`.
- Update this dashboard when a milestone materially changes the answer to “where are we now?”, not for every small task or refactor.

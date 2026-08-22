# MES Quant Engine — Architecture Changelog

This file records **why the architecture changed**. It is not the detailed stage-policy authority and it is not the current progress tracker.

---

## v1 — Original quant pipeline

Original architecture was a mostly linear research-to-production flow:

```text
Point-in-Time Data
→ Market Features
→ Market Dynamics / Statistical Models
→ Signal Independence / Redundancy
→ Probability Model
→ Calibration
→ Regime / Context
→ Risk Engine
→ Position Size
→ Cost Model
→ Execution
→ IBKR
→ Fills / P&L
→ Monitoring
→ Drift / Kill Switch
```

Strengths retained:

- PIT/vintage discipline
- feature/dynamics separation concept
- redundancy before model promotion
- explicit calibration
- macro as context/regime
- risk/cost/execution/monitoring chain

Main limitation: lifecycle/governance and feedback were not explicit enough; the flow looked like a one-way pipe.

---

## v2 — System/lifecycle architecture proposal

Major additions:

- Plane 0 — Governance & Provenance
- Plane A — Research / Offline
- Release Gate
- Plane B — Production / Online
- Plane C — Feedback & Control
- Decision Universe as its own layer
- Formal Validation layer
- State Reconciliation before new broker risk
- Production risk-state machine
- Independent watchdog
- Feedback loops from realized cost/performance back to research

Accepted direction: the system must be a closed loop, not a one-way model-to-broker chain.

---

## v2.1 — Hybrid correction

v2.1 combined the strong lifecycle structure of v2 with the original Quant Logic and corrected several ordering/leakage issues.

Key corrections:

1. **Cost before net-of-cost target.** The cost model cannot be referenced from a later stage when the target already depends on it.
2. **Target Contract separated from Label Materialization.** Target-blind work may know the target definition while remaining unable to read realized answers.
3. **Incremental Predictive Value moved out of redundancy into target-aware Validation / model selection.**
4. **Feature construction split:** deterministic PIT features vs train-fitted dynamics/state features.
5. **Regime must be causal / OOF when fitted.** No hindsight-smoothed state in live-parity research.
6. **Global calibration is the mandatory baseline; regime-conditional calibration is a challenger requiring evidence.**
7. **Kelly is a V1 sizing ceiling/component, not the primary unconstrained sizing authority.**
8. **Execution parity uses a shared policy core with separate simulation and IBKR adapters.**

Result: current Stage B maps cleanly to `A6 — Target-Blind Redundancy` without discarding the work already completed.

---

## v2.2 — Edge-discovery and access-governance closure

v2.2 is the current accepted architecture baseline.

### Exploratory Lane

Added a TRAIN-only Exploratory Lane so the project can answer whether the current MES research scope contains a usable edge before building every institutional contract.

Rules:

- TRAIN labels allowed
- Validation forbidden
- Final Test forbidden
- label-accessing runs require Experiment ID
- exploration results have no Release-Gate authority
- disposable code allowed
- all search history logged sufficiently for later multiple-testing interpretation
- no Exploratory Lane V2 before Sprint 1 has run

### Label-access levels

Replaced a binary target firewall with observed access levels:

```text
L0 — target contract only
L1 — TRAIN label access
L2 — Validation access
L3 — Final Test access
```

Work classification is derived from observed access, not a human label. L0 is target-blind work; any L1+ run is a target-aware experiment and requires an Experiment ID.

### Edge-thesis lifecycle

Replaced a rigid A0-before-data requirement with:

```text
Research Question
→ TRAIN-only exploratory hypotheses
→ Confirmatory Hypothesis Lock
→ Validation
```

The economic story/falsification rule must be sufficiently explicit before L2 Validation, not invented after seeing confirmatory outcomes.

### Invariants vs V1 scope decisions

Separated permanent principles from current implementation choices.

Examples of invariants:

- no look-ahead
- no Final-Test tuning
- no silent feature mutation
- no label leakage into target-blind stages
- no production self-modification
- bad required data / unreconciled broker state blocks new risk

Examples of V1 scope choices:

- MES only
- 15-minute decisions
- initial +60-minute horizon
- Long/Flat first
- no Full Kelly in V1

### Validation budget and dependence

Validation access, not repeated TRAIN exploration, is treated as scarce evidence. Before the first L2 opening, the project must freeze a Validation opening budget and interpretation protocol.

Raw rows are not assumed IID. `N_raw / overlap_layers` is only a useful non-overlap scale, not a proven effective sample size.

### Risk-state clarification

`DEFENSIVE` became the default emergency posture: no new positions while existing exposure follows a pre-authorized management policy. `FLAT` is controlled liquidation, not a universal emergency response.

### Machine-qualified operational fast recovery

Fast recovery eligibility is derived from machine predicates (unchanged model/feature/risk artifacts, healthy data, reconciled state, no active validity gate failures). Humans may veto an eligible recovery but may not force an ineligible one.

### Stage-B V1.2 convergence rule

After BL-30, Stage B receives exactly one final integration / contradiction / preservation audit. New findings after that audit go to V1.3 unless they satisfy a predefined V1.2 lock-breaker:

1. authoritative Phase-B math can be wrong;
2. wrong feature/member identity can change the analyzed ground set;
3. target/Validation/Final-Test information can influence target-blind Phase B;
4. KEEP/DROP/OPEN/HARD_FAIL can differ from the frozen methodology;
5. two locked requirements cannot be satisfied simultaneously.

### Sprint 1 protocol

Before Edge Discovery Sprint 1, freeze:

- exploration scope
- project continuation policy
- baseline(s), including always-flat
- one primary decision metric
- diagnostic secondary metrics
- cost assumption
- interesting-enough continuation criterion

A failed Sprint 1 establishes only that no usable edge was found **inside the predeclared scope**. It does not establish that MES has no edge in other features, horizons, directions, datasets, or regimes.

---

## Current architecture authority

Current baseline:

```text
MES_QUANT_TARGET_ARCHITECTURE_v2.2
STATUS = BASELINE_ACCEPTED / DESIGN_CLOSED
```

No v2.3 should be created before Edge Discovery Sprint 1 runs unless a genuine architecture contradiction is discovered.

See:

- `MES_QUANT_TARGET_ARCHITECTURE_v2.2.md` — where the system is going
- `ARCHITECTURE_PROGRESS.md` — where the project is now
- stage contracts such as `../STAGE_B_REDUNDANCY_CONTRACT.md` — how the active stage is governed

---

## VNext — Test 2+ research architecture design candidate

VNext was created after the bounded Sprint 1 LR001/TREE001 research record. It does not
rewrite that history and does not change v2.2's status as the accepted, design-closed Test 1
baseline.

The current design candidate adds:

- four explicit research pillars: Market Dynamics/Physics, Statistics/ML,
  Economics/Regime, and Microstructure/Flow;
- an exact-decision-time constitutional data rule and explicit PIT/vintage semantics;
- Economics/Regime as numerical point-in-time context only;
- Microstructure/Flow as exchange-observed numerical state for short-horizon alpha quality
  and execution, not a mandatory equal-weight vote;
- hypothesis-first microstructure research and raw feature-fishing controls;
- a controlled six-family ML challenger stack with ensemble/calibration support;
- champion–challenger and multiple-testing/search-budget controls;
- LangGraph as research orchestration only, including an Alpha-Killer/Skeptic role;
- a repeatable edge-factory model spanning information, modeling, structural, execution,
  and risk edges;
- explicit Test 1 historical-baseline versus Test 2 design-candidate separation.

Current candidate:

```text
MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT
STATUS = CURRENT_DESIGN_CANDIDATE / TEST2+ / RESEARCH_ONLY
EXECUTION AUTHORITY = NONE
```

See `README.md` in this directory for the current pointer and authority map.

---

## VNext amendment — LangGraph retired by Owner decision

**Date:** 2026-08-22

The Owner removed LangGraph from the MES project direction. VNext now defines research
proposal, critique, and adversarial review as human-directed and framework-neutral. No
graph runtime or orchestration framework is part of the active architecture.

The local historical branches remain preserved for audit/history only:

- `architecture/langgraph-boundary-v1` at `42cda10559b7b7ab9ffeb4fb4263a6d2e8bb5af3`;
- `research/langgraph-prototype-v0` at `8d5befba64627c170ae97e1193be028b53ca7857`.

Their status is `ABANDONED / DO NOT USE / DO NOT MERGE`. They grant no architecture,
implementation, dependency, experiment, data-access, merge, execution, or trading
authority. Historical governance statements that say a LangGraph runtime did not exist or
was not authorized remain untouched because they are frozen evidence/non-claims, not active
design dependencies.

Decision record:

`LANGGRAPH_RETIREMENT_DECISION_20260822.md`

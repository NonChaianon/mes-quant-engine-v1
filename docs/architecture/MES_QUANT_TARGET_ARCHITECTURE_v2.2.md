# MES QUANT ENGINE — TARGET ARCHITECTURE v2.2

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Purpose:** North-star architecture for the MES Quant Engine. This document defines where each responsibility belongs and which boundaries may not be crossed. It is a target state, not a requirement to build every component before the first edge-discovery sprint.

---

## 1. System shape

The engine is a closed-loop decision system with governance around every plane.

```text
                    PLANE 0 — GOVERNANCE & PROVENANCE
                              (covers all planes)
                                       │
                                       ▼
                    PLANE A — RESEARCH / OFFLINE
                                       │
                                       ▼
                              RELEASE GATE
                                       │
                                       ▼
                    PLANE B — PRODUCTION / ONLINE
                                       │
                                       ▼
                    PLANE C — FEEDBACK & CONTROL
                                       │
                                       └──────────→ back to Plane A / Plane 0

                    + INDEPENDENT HARD WATCHDOG
```

Plane C may change runtime state only within pre-authorized policy. It may not modify model, feature, target, cost, regime, risk methodology, or production policy and bypass Plane A / the Release Gate.

---

## 2. Plane 0 — Governance & Provenance

Plane 0 does not create alpha. It determines what is allowed to count as evidence and what is allowed to run.

Core responsibilities:

- Policy and contract versioning
- Canonical feature registry
- Semantic registry
- Artifact provenance / SHA chain
- Label-access and Final-Test firewall
- Experiment / hypothesis ledger
- Reproducibility and environment evidence
- Change control and approval
- Release / rollback governance
- Incident and audit trail

### Constitutional invariants

1. Historical facts are never recomputed under a newer policy and then presented as the old fact.
2. Human-authored policy intent is allowed; release-affecting factual predicates must be machine-derived or machine-reconciled from evidence.
3. No silent candidate addition, removal, or redefinition.
4. Target-blind stages may not read realized labels, future returns, P&L, Validation outcomes, or Final-Test outcomes.
5. Missing required information fails closed; in production this means no new risk / no trade according to the applicable policy.
6. Final Test is sealed and may be opened only under the predeclared protocol.
7. `POLICY_STATUS` and `EXECUTION_STATUS` are independent. A policy may be locked while execution remains disabled.
8. Production models may not self-modify or self-promote.
9. Every production artifact must be traceable to source data, code, config, policy, environment, evidence, and approval.
10. Explanatory text cannot by itself turn a failed machine predicate into a pass.
11. Emergency authority is asymmetric: humans and watchdogs may make the system more conservative immediately, but may not create eligibility to increase risk when machine predicates do not allow it.

### V1.2 convergence rule

For `STAGE_B_REDUNDANCY_V1.2`:

```text
BL-30 evidence
→ one final integration / contradiction / preservation audit
→ V1.2 freeze
```

After that final audit, new improvement findings go to V1.3 by default. V1.2 may reopen only for a predefined `V1_2_LOCK_BREAKER`:

1. Phase-B authoritative mathematical result can be wrong.
2. Feature/member identity can be wrong such that the wrong ground set is analyzed.
3. Target / Validation / Final-Test information can influence a target-blind Phase-B result.
4. KEEP / DROP / OPEN / HARD_FAIL can differ from the frozen methodology.
5. Two locked requirements are internally inconsistent and cannot both be satisfied by one compliant implementation/run.

Better logging, stronger tamper resistance, naming improvements, new metadata, and future scalability are V1.3 backlog unless they satisfy one of the five lock-breakers above.

---

## 3. Label-access levels

Work classification is derived from **observed access**, not from a human label.

```text
L0 — TARGET_CONTRACT_ONLY
     No realized label values accessed.

L1 — TRAIN_LABEL_ACCESS
     TRAIN labels may be accessed.

L2 — VALIDATION_LABEL_ACCESS
     Validation labels/results may be accessed under a frozen confirmatory protocol.

L3 — FINAL_TEST_ACCESS
     Sealed Final Test may be opened under its one-time protocol.
```

Derived work class:

```text
observed access = L0   → TARGET_BLIND_WORK
observed access >= L1  → TARGET_AWARE_EXPERIMENT and EXPERIMENT_ID required
```

Names such as `governance`, `research`, or `experiment` have no authority over this classification.

---

## 4. Edge-thesis lifecycle

The architecture does not require a fully formed economic story before basic market-data inspection. Edge logic matures in stages:

```text
RESEARCH QUESTION
→ TRAIN-ONLY EXPLORATORY HYPOTHESES
→ CONFIRMATORY HYPOTHESIS LOCK
→ VALIDATION
```

Before L2 Validation, the confirmatory hypothesis must state enough to be falsifiable: expected mechanism, direction, horizon, conditions/regimes if relevant, and a predeclared rejection rule. Counterparty/capacity/decay reasoning should become stronger before production promotion, but must not be invented retroactively to explain a result already seen.

---

# PLANE A — RESEARCH / OFFLINE

## A1 — Data Foundation

Point-in-time market and macro data with:

- Point-in-Time / vintage controls
- Survivorship and look-ahead control where applicable
- MES contract identity and roll policy
- Session calendar / holiday / early close
- Timezone alignment
- Gap / partial-bar / zero-volume / alignment integrity checks
- Raw source-of-truth provenance hash

Macro/economic data must be vintage-aware when revisions exist.

Output: canonical market data + provenance + integrity audit.

---

## A2 — Decision Universe

Not every bar is allowed to produce a decision.

Each candidate row must derive:

- `decision_eligible`
- `eligibility_reason`
- valid session / decision time
- complete-bar requirement
- horizon-safe close
- roll-crossing eligibility
- required-data availability

Ineligible rows are not repaired by arbitrary imputation.

---

## A3 — Cost & Impact Model

Single source of truth for research and production cost assumptions:

- Commission
- Exchange / regulatory fees
- Bid-ask spread
- Slippage
- Market impact where relevant
- Implementation shortfall

Scenario families may include `FEES_ONLY`, `BASE`, `CONSERVATIVE`, `STRESS` and may condition on time, volatility, liquidity, and size when justified.

A3 is referenced by target definition, Net-EV, execution simulation, production, and realized-cost monitoring. Stages may not create private conflicting cost constants.

---

## A4 — Label / Target Contract

A4 defines the target **contract**, not realized target values.

It declares:

- Horizon
- Direction / class definitions
- Exit rule
- Cost treatment
- Margin of safety if used
- Roll-crossing rule
- Overlap / purging metadata

Target-blind stages may know the formula but not the realized answers.

---

## A5 — Feature Construction

### A5a — Deterministic PIT features

Examples:

- Returns
- Momentum
- Realized volatility
- Bar range/body/location
- Volume ratio
- VWAP deviation
- Autocorrelation
- Entropy
- Time-of-day / weekday / session position
- Cross-market deterministic transforms

Each canonical feature declares formula, source columns, lookback, lookback mode, availability rule, max source time, missingness rule, and provenance.

Invariant: `feature_max_source_time <= decision_time`.

### A5b — Train-fitted dynamics / state features

Examples may include fitted GARCH state, OU parameters, Kalman state, latent/fitted transforms.

If fitting is required:

```text
FIT TRAIN
→ transform Validation / OOS causally
```

No full-development fit may be projected backward into Validation as if known historically.

---

## A6 — Target-Blind Redundancy / Independence

This is the home of the current Stage-B work.

```text
Phase A — Exact semantic relationships
Phase B — Generic exact-rank / SVD discovery firewall
Phase C — Empirical target-blind association
Phase D — Clustering + review
```

Key rule for V1.2:

```text
GENERIC SVD / RANK DISCOVERY → NEVER DIRECT DROP
```

Phase A may have explicit semantic KEEP/DROP authority when the versioned semantic policy proves direction. Phase B detects exact numerical dependence but does not invent semantic direction. Stable unexplained dependence may OPEN a whole component; unstable/numerically inconsistent behavior fails closed. Phase C/D remain target-blind.

`Incremental Predictive Value` does **not** belong here; it belongs in target-aware validation/model selection.

---

## A7 — Regime / Context Layer

Regime is context, not an equal-frequency macro vote.

Candidate regimes:

- Volatility
- Liquidity
- Macro risk-on/risk-off
- Event regime (FOMC, CPI, NFP, expiry, roll week)
- Change-point / HMM state where justified

If a regime model is fitted:

```text
FIT TRAIN ONLY
→ Validation uses causal / filtered / OOF state
```

No hindsight-smoothed state may be used in a live-parity simulation.

---

## A8 — Label Materialization / Firewall Opening

Actual target values are materialized only under the allowed label-access level.

```text
A4 Target Contract
+ A3 Cost Model
+ A2 Decision Universe
→ realized TRAIN labels (L1)
```

Validation remains unopened until L2. Final Test remains sealed at L3.

---

## Exploratory Lane — TRAIN-only Edge Discovery

Purpose: answer quickly whether the current research scope contains empirical structure worth carrying into confirmatory research.

**One-page charter (frozen until Sprint 1 completes):**

- TRAIN data + TRAIN labels allowed (`L1`).
- Validation forbidden.
- Final Test forbidden.
- Every label-accessing run requires `EXPERIMENT_ID` by machine-enforced access classification.
- Each run records hypothesis/rule/features/parameters/cost/result sufficiently to preserve search history.
- Disposable code is allowed; production-quality contracts are not required for exploration code.
- Exploratory results have no Release-Gate authority.
- Canonical upstream artifacts may not be silently modified.
- Before any L2 opening, freeze the confirmatory hypothesis and validation protocol.
- No Exploratory Lane V2 before Sprint 1 has actually run.

L1 run count is not a release statistic by itself, but search history must be logged. The scarce clean evidence is L2 Validation access, not repeated TRAIN exploration.

Before Sprint 1 begins, freeze:

- `EXPLORATION_SCOPE_ID`
- project continuation policy for the sprint
- baseline(s)
- **one primary decision metric**
- diagnostic secondary metrics
- cost assumption used by the sprint
- predeclared `interesting-enough` continuation criterion

Metrics may not be changed after results are seen without creating a new experiment/hypothesis path.

If Sprint 1 finds no usable edge, the allowed conclusion is scope-limited, e.g.:

> No usable edge was identified within the predefined exploration scope using the current 29-feature universe, selected edge families, MES 15-minute decision grid, +60-minute target framework, and the specified cost assumptions.

It does not establish that MES has no edge outside that scope.

---

## A9 — Predictive Model Layer

Begin with simple baselines before model complexity.

Mandatory comparison baselines should include always-flat and other predeclared simple challengers when relevant. Candidate models may include regularized linear models, tree ensembles, Bayesian/state-space methods, and ensembles.

Stacking/blending must use out-of-fold predictions only.

---

## A10 — Validation & Model Selection

Confirmatory validation may use:

- Walk-forward evaluation
- Purging for overlapping labels
- Embargo where required
- Multiple-testing controls
- Stability across folds/years/regimes
- Horizon / threshold / window sensitivity
- Incremental Predictive Value

### Validation-access budget

Before the first L2 opening, pre-register:

- maximum number of L2 Validation openings
- what counts as one opening
- what information may be inspected
- pass/fail interpretation
- whether a reformulated hypothesis consumes a new opening

TRAIN exploration may continue, but each new L2 opening consumes the predeclared validation budget.

### Overlapping-label dependence

Raw row count is not independent sample size. For +60m labels on a 15m decision grid, roughly four overlapping layers exist, but `N_raw / 4` is only a non-overlap scale / heuristic, **not** a proven ESS.

Validation must report at least:

- `N_raw`
- `N_sessions`
- label horizon
- decision spacing
- overlap layers
- `N_nonoverlap_scale`
- a dependence-aware uncertainty / ESS approach appropriate to the final protocol

Inference may not assume all raw rows are IID.

A single Validation year, such as 2024, is evidence about that predefined environment; PASS does not prove universality and FAIL does not prove that MES contains no edge anywhere. A failed confirmatory hypothesis may not be tuned on the same Validation result and then called unchanged.

---

## A11 — Calibration

Required baseline: global calibration.

Possible challenger: regime-conditional calibration, promoted only if OOF evidence and sample size justify it.

Methods may include reliability curves, Brier score, log loss, Platt scaling, and isotonic regression. Calibrator fitting stays inside the relevant training fold.

---

## A12 — Net Expected Value Engine

Net EV is computed once from calibrated probability, payoff assumptions, and A3 cost/impact assumptions.

```text
EV_net = calibrated expected payoff - cost - impact
```

If EV does not exceed the predeclared decision margin, the result is no trade. EV uncertainty should reflect probability, payoff, cost, and estimation uncertainty where practical.

---

## A13 — Risk & Position-Sizing Simulation

Prediction answers what may happen; risk answers how much can be lost if it is wrong.

V1 sizing hierarchy:

```text
Hard position limits
→ Risk budget
→ Volatility / liquidity cap
→ EV / confidence constraints
→ Fractional-Kelly ceiling
```

Full Kelly is a **V1 scope decision**, not a constitutional impossibility.

---

## A14 — Execution Simulation / Parity

Use a shared execution-policy core with separate adapters:

```text
             SHARED EXECUTION POLICY CORE
                 /                       \
        Simulation Adapter          IBKR Live Adapter
```

Shared policy includes order type, timeout, cancel/replace, duplicate guard, sizing, max order rate, idempotency, and lifecycle rules. The simulated fill engine is not the broker network adapter.

Simulation should cover latency, partial fills, rejections, cancellation, missed fills, spread, and slippage where relevant.

---

# RELEASE GATE

A research artifact does not become production merely because backtest P&L is positive.

Promotion path:

```text
Research
→ Release Candidate
→ Release Gate
→ Shadow
→ Limited Live
→ Scale only after evidence
```

Release evidence categories:

- Research integrity / provenance
- No leakage / no Final-Test misuse
- OOS performance versus frozen baseline after cost
- Multiple-testing discipline
- Calibration quality
- Risk/stress acceptance
- Execution parity
- State-reconciliation readiness
- Broker reconnect plan
- Watchdog readiness
- Shadow-mode evidence
- Minimum-size live ramp plan

---

# PLANE B — PRODUCTION / ONLINE

## B1 — Live Ingest & Integrity

Check staleness, duplicates, schema, range, timestamp alignment, missingness, and latency. Bad required data means no new risk.

## B2 — State Reconciliation

Reconcile broker position vs internal position, cash/margin/buying power, open orders, orphan orders, fills, and pending cancels. Unreconciled state blocks new risk.

## B3 — Live Feature Compute

Uses the same canonical feature definitions as research.

## B4 — Live Regime Classification

Causal information only; no hindsight state.

## B5 — Prediction

Approved model artifact only.

## B6 — Calibration

Approved calibrator only.

## B7 — Net EV

Uses the approved A3 cost model; insufficient EV means no trade.

## B8 — Risk Engine / Risk State Machine

States:

```text
NORMAL
CAUTION
DEFENSIVE
FLAT
HALT
```

`DEFENSIVE` is the default emergency posture: no new positions, while existing risk follows a pre-authorized position-management policy. `FLAT` is controlled liquidation, not the automatic answer to every incident. `HALT` stops the trading engine from creating new risk while still allowing pre-authorized risk-reducing, cancellation, and reconciliation actions.

## B9 — Position Sizing

Approved base size × risk budget × volatility/liquidity constraints × calibration/EV constraints × risk-state multiplier × Kelly ceiling, always subject to absolute limits.

## B10 — Order Policy / Execution

Market/limit rules, price protection, timeout, cancel/replace, retry, max order rate, idempotency, duplicate prevention.

## B11 — Broker / IBKR

Connection health, heartbeat, acknowledgements/errors, reconnect, and resync procedure. Outage behavior must be predeclared.

## B12 — Fills / P&L / Attribution

Separate signal contribution, cost, slippage, timing, regime, execution, and sizing effects where feasible.

---

# PLANE C — FEEDBACK & CONTROL

## C1 — Monitoring

Monitor data, feature drift, model performance, calibration, realized cost vs assumed cost, execution, exposure, drawdown, and loss limits.

## C2 — Diagnosis Router

Before retraining, diagnose whether degradation comes from data, feature, regime, calibration, cost, execution, broker, or model behavior.

## C3 — Fast Risk-Control Loop

Monitoring may move the system to a more conservative state under frozen policy. It may not rewrite thresholds/methodology during live operation.

## C4 — Cost Feedback

Realized cost may trigger review of A3. Production may not silently auto-update the canonical cost model.

## C5 — Retrain Trigger

A trigger opens a new research cycle; it does not authorize auto-deployment.

## C6 — Restart / Recovery Policy

### Machine-qualified operational fast recovery

Fast recovery eligibility is derived from machine predicates, not from a human declaration that an incident is "operational".

Illustrative required conditions include:

- model artifact hash unchanged
- calibrator hash unchanged
- feature-definition hash unchanged
- risk-policy hash unchanged
- data integrity passing
- broker/internal positions reconciled
- open orders reconciled
- unmatched fill count zero
- no model-validity, feature-integrity, or cost-assumption invalidation predicate active
- all incident-specific remediation predicates passing

Humans may **reject** an eligible fast recovery but may not override an ineligible one into eligibility.

Recovery is bounded and conservative, e.g.:

```text
HALT → DEFENSIVE → observation/health checks → CAUTION → NORMAL
```

If model validity, feature definition, target/cost assumptions, data correctness affecting signals, or risk methodology changed, the fast path is unavailable and the change returns to Plane A / the Release Gate.

## C7 — Incident / Post-Mortem

Material incidents return to Plane 0 and may trigger versioned policy/research changes.

---

# INDEPENDENT HARD WATCHDOG

A separate process should eventually be able to enforce emergency controls independently of the predictive-model process, such as heartbeat timeout, position-limit breach, daily loss, drawdown, runaway-order conditions, and unreconciled broker state.

The V1 threat model is explicit: repository hash chains and protected refs defend ordinary workflow integrity when enforced; they do not claim to withstand a malicious repository administrator capable of rewriting all trusted history/anchors.

---

## 5. System loops

### Fast loop

```text
Production → Monitoring → Risk State → Size/Halt
```

Seconds to hours.

### Medium loop

```text
Fills → Actual Cost → Cost Drift → Research Review
```

Days to weeks.

### Slow loop

```text
Performance/Regime Drift → Diagnosis → Research → Retrain → Validate → Release Gate
```

Weeks to months.

Forbidden loop:

```text
Poor P&L → Auto retrain → Auto deploy
```

---

## 6. Invariants vs V1 scope decisions

### Constitutional invariants

Examples:

- No look-ahead
- No Final-Test tuning
- No silent feature/candidate mutation
- No label leakage into target-blind stages
- No production self-modification
- Bad required data → no new risk
- Broker/internal state mismatch → no new risk

### V1 scope decisions

Current V1 direction includes:

- MES only
- 15-minute decisions
- initial +60-minute horizon
- Long / Flat first
- IBKR production broker later
- no Full Kelly in V1; Fractional Kelly only as a cap if/when sizing reaches that stage

### Recommended defaults, not invariants

Examples:

- Global calibration before regime-conditional calibration
- Simple/linear models before complex model zoo
- Minimum-size live deployment before scaling

---

## 7. Contracts / single sources of truth

Target architecture expects versioned contracts where they become necessary, including data, decision universe, feature, cost, target, redundancy, regime, model, calibration, risk, execution, monitoring, and release policy.

This is **not** an instruction to build all contracts before proving an edge. After current A6 work is closed, the next major objective is Edge Discovery Sprint 1 before building the rest of the institutional infrastructure.

---

## 8. Architecture governance

Three concepts are distinct:

```text
ARCHITECTURE_BASELINE
MES_QUANT_TARGET_ARCHITECTURE_v2.2

STAGE_POLICY
example: STAGE_B_REDUNDANCY_V1.2

EXECUTION_STATUS
RESEARCH_ONLY / SHADOW_ENABLED / PAPER_ENABLED / LIVE_DISABLED / LIVE_ENABLED
```

Architecture acceptance does not mean live trading is enabled.

---

## 9. Master flow

```text
GOVERNANCE / PROVENANCE
        ↓
POINT-IN-TIME DATA
        ↓
DECISION UNIVERSE
        ↓
COST & IMPACT MODEL
        ↓
TARGET CONTRACT (definition only)
        ↓
FEATURE CONSTRUCTION
        ↓
TARGET-BLIND REDUNDANCY
        ↓
REGIME / CONTEXT (causal / OOF)
        ↓
──────── LABEL ACCESS BOUNDARY ────────
        ↓
TRAIN-ONLY EXPLORATORY LANE (L1)
        ↓
CONFIRMATORY HYPOTHESIS LOCK
        ↓
VALIDATION (L2; budgeted)
        ↓
PREDICTIVE MODEL / CALIBRATION / NET EV
        ↓
RISK & SIZING SIMULATION
        ↓
EXECUTION PARITY SIMULATION
        ↓
RELEASE GATE
        ↓
SHADOW
        ↓
LIMITED LIVE
        ↓
PRODUCTION
        ↓
LIVE INTEGRITY
        ↓
STATE RECONCILIATION
        ↓
FEATURES → REGIME → PREDICTION → CALIBRATION → NET EV
        ↓
RISK STATE → SIZING → EXECUTION → IBKR
        ↓
FILLS / P&L / ATTRIBUTION
        ↓
MONITORING → DIAGNOSIS
        ↓
Risk loop / Cost review / Retrain trigger
        ↓
back to Research / Governance

+ INDEPENDENT HARD WATCHDOG
```

---

## 10. Immediate project sequencing

The architecture is design-closed. The current project sequence is:

```text
BL-30 Genesis Reproduction Evidence
→ independent review
→ one final Stage-B V1.2 integration / contradiction / preservation audit
→ V1.2 LOCK unless a predefined V1_2_LOCK_BREAKER exists
→ LABEL_EXPOSURE_PRE_FIREWALL acknowledgment
→ freeze the one-page Exploratory Lane charter
→ define Edge Discovery Sprint 1 scope + continuation policy + baseline + primary metric + interesting-enough criterion
→ RUN EDGE DISCOVERY SPRINT 1
```

No architecture v2.3 and no Exploratory Lane v2 should be created before Sprint 1 runs unless a genuine architecture contradiction is discovered.
# MES Quant Engine — Research Architecture VNext

**Architecture status:** `CURRENT_DESIGN_CANDIDATE / TEST2+ / RESEARCH_ONLY`

**Execution authority:** `NONE`

**Live status:** `LIVE_DISABLED`

**Historical baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2` remains the immutable
`TEST1 / SPRINT1 / BASELINE_ACCEPTED / DESIGN_CLOSED` record.

**Design rationale:**
`../proposals/MES_RESEARCH_ARCHITECTURE_TEST2_PROPOSAL_V1.md`

**Research coordination:** `HUMAN_DIRECTED / FRAMEWORK_NEUTRAL`

**LangGraph status:** `RETIRED / NOT IN PROJECT SCOPE`

**Owner decision:**
`LANGGRAPH_RETIREMENT_DECISION_20260822.md`

---

## 1. Authority and succession

This document is the canonical architecture design candidate for Test 2 and later research.
It supersedes Architecture v2.2 only as the proposed design direction for Test 2+. It does
not rewrite, replace, or invalidate v2.2 as the historical authority for Test 1/Sprint 1.

```text
Architecture v2.2
  = HISTORICAL / TEST1 BASELINE / DESIGN_CLOSED
  = immutable provenance for Sprint 1, LR001, and TREE001

Architecture VNext
  = CURRENT DESIGN CANDIDATE FOR TEST2+
  = no experiment, label-access, deployment, or trading authority by itself
```

This candidate inherits the existing governance, provenance, label-access, Validation,
Final-Test, Release-Gate, risk, and live-safety boundaries unless a separately accepted and
versioned control changes them. Acceptance of this document would still not authorize a
Test 2 run. Test 2 requires a separate frozen protocol and explicit Owner authorization.

The six static `SPEC_FREEZE` controls, frozen Sprint 1 evidence, immutable LR001/TREE001
results, and governance audit evidence remain outside this document's mutation authority.

---

## 2. Constitutional principles

### 2.1 Exact-decision-time information

> The engine may consume only information that was objectively observable or available at
> the exact decision time.

The machine-verifiable decision rule is:

```text
AVAILABLE_TIME <= DECISION_TIME
```

This rule applies to market data, exchange events, economic releases, consensus estimates,
features, regime states, model inputs, calibrators, execution context, and every historical
backtest decision.

The corresponding prohibitions are:

```text
NO OPINION
NO HINDSIGHT
NO FUTURE DATA
NO LATEST-REVISION LEAKAGE
```

Human-authored research hypotheses and policy intent are allowed. Subjective human or LLM
interpretation is not an eligible numerical input to a prediction or trade decision.

### 2.2 Evidence outranks sophistication

Technology sophistication does not imply edge. A complex model has no priority over a
simple model unless it survives the same predeclared, cost-aware, time-aware, out-of-sample
tests. Model novelty, agent confidence, explanatory prose, and in-sample fit have no
promotion authority.

### 2.3 Pillars are not equal-weight voters

The four research pillars organize hypotheses, data, and review. They are not four fixed
directional votes and are never forced into 25% weights. A pillar may produce a feature,
condition a model, veto an invalid assumption, change permission/sizing under an approved
risk rule, or improve execution. Its role must be earned and declared for each hypothesis.

### 2.4 Fail closed

If source provenance, event order, release availability, vintage identity, or a required
timestamp cannot be established, the input is ineligible. Research may quarantine it for
diagnosis; the engine may not assume it was known earlier.

---

## 3. Four research pillars

### 3.1 Market Dynamics / Physics

**Definition:** numerical behavior of prices and measurable market state through time.

Research domains include:

- returns, momentum, acceleration, and persistence;
- realized and conditional volatility;
- range, path, gap, and price-location behavior;
- mean reversion and trend continuation;
- autocorrelation, entropy, and state-transition behavior;
- cross-market relationships when their point-in-time availability is proven.

**Role:** generate falsifiable alpha hypotheses about how measurable market state evolves.
All transforms must be causal, timestamped, and reproducible. A physical analogy is a
hypothesis aid, not evidence.

### 3.2 Statistics / Machine Learning

**Definition:** empirical estimation of probabilities, uncertainty, interactions, and
generalization from controlled samples.

Research domains include:

- transparent statistical baselines;
- conditional-probability estimation;
- nonlinear interaction discovery;
- temporal and cross-regime stability;
- out-of-sample comparison;
- calibration and reliability;
- dependence-aware uncertainty and multiple-testing control.

**Role:** convert eligible numerical inputs into reproducible estimates and challenge them
against frozen baselines. Complexity is a challenger property, not evidence of edge.

### 3.3 Economics / Regime

**Definition:** `POINT-IN-TIME NUMERICAL CONTEXT ONLY`.

Eligible examples, when exact historical availability is proven, include:

- CPI, PPI, unemployment, GDP, and other official releases;
- policy rates and market-observed rate curves;
- Treasury yield-curve measures and real-rate measures;
- credit spreads and other numerical credit conditions;
- VIX and other timestamped market-implied context;
- official release calendars and event-time distance;
- causal regime/state estimates fitted only within allowed training windows.

Prohibited inputs include:

- subjective analyst opinion;
- Wall Street gossip;
- political gossip or political-insider information;
- manually interpreted narrative sentiment;
- discretionary labels such as "hawkish", "fearful", or "recessionary";
- retrospective macro explanations written after the decision;
- present-day latest revisions substituted for what was known historically.

**Role:** provide context, interaction terms, state conditioning, and—only under an approved
policy—permission or sizing constraints. Economics/Regime is not automatically a
directional signal and is not an equal-weight voter.

### 3.4 Microstructure / Flow

**Definition:** `EXCHANGE-OBSERVED NUMERICAL STATE`.

Eligible source events and derived state may include:

- bid, ask, spread, and quote updates;
- displayed depth and depth imbalance;
- trades and defensibly classified aggressor flow;
- add, cancel, modify, and trade events;
- signed volume and order-flow imbalance;
- cancellation/addition ratios and liquidity withdrawal;
- absorption, refill behavior, and book resiliency;
- queue and fill context when the source data supports it.

Microstructure has at least two distinct roles:

1. **Short-horizon signal quality / alpha context** — test whether immediate exchange state
   strengthens, weakens, or invalidates a predeclared short-horizon hypothesis.
2. **Execution quality** — control order timing, spread crossing, fill probability,
   slippage, latency sensitivity, impact, and cancel/replace behavior.

Directional alpha use requires its own governed hypothesis. Execution use does not convert
microstructure into a 25% model vote.

---

## 4. Point-in-time and vintage-data architecture

### 4.1 Time semantics

Every eligible observation must distinguish, where applicable:

| Time | Meaning |
|---|---|
| `observation_time` | When the measured event or period occurred |
| `release_time` | When the publisher released the value |
| `available_time` | Earliest defensible time the engine could consume it |
| `vintage_time` | Identity/time of the published or revised vintage |
| `decision_time` | Time at which the engine makes the decision |
| `retrieval_time` | When the research system obtained the source artifact |

`observation_time` is not a substitute for `available_time`. A CPI value describing an
earlier month remains unavailable until its actual release. A vendor date without adequate
time precision or latency semantics does not prove intraday availability.

### 4.2 Minimum PIT record

Economic and contextual records require at minimum:

```text
series_id
observation_time_or_period
release_time
available_time
vintage_time
value
source_and_vendor_identity
timezone_and_timestamp_precision
retrieval_time
revision_or_supersession_link
immutable_source_hash_or_equivalent_identity
```

The backtest joins the latest eligible vintage satisfying:

```text
available_time <= decision_time
```

It does not join by observation date alone. Later revisions remain new vintages and never
overwrite the historical information set.

### 4.3 Revision handling

For revised series, the data layer must preserve release and revision history. Backtests
must demonstrate that:

- a decision cannot see a later vintage;
- a corrected vendor history cannot silently replace the original vintage;
- release delays, embargoes, and timezone conversions are explicit;
- uncertain latency is conservatively delayed or rejected;
- the same PIT join can be reproduced from immutable source identity.

Latest-revision databases may support current descriptive analysis, but they are ineligible
for historical signal simulation unless their historical vintages are separately available.

### 4.4 Consensus and economic surprise

Consensus/expectations data may be used only when historical point-in-time provenance is
trustworthy. The research record must establish the exact consensus value, collection
cutoff, publication time, vendor history, and correction/backfill policy. Constituent and
methodology changes must be retained when material.

If the repository cannot prove what consensus was available before the release, the
consensus or derived surprise is prohibited for the initial Test 2 path.

---

## 5. Microstructure historical reconstruction and overfit control

### 5.1 Reconstruction contract

When a hypothesis requires historical book or order-flow state, reconstruction should use
ordered exchange event data with explicit controls for:

- contract/instrument identity and roll boundaries;
- exchange timestamps, receive timestamps where available, and sequence order;
- event schema for add/cancel/modify/trade and quote semantics;
- duplicate, out-of-order, correction, and reset handling;
- feed gaps, packet loss, depth truncation, and unavailable levels;
- session, maintenance, halt, and recovery boundaries;
- aggressor classification method and uncertainty;
- latency assumed between observable event and decision availability;
- deterministic replay and source provenance.

Aggregate trade/bar data must not be presented as full order-book history. A feature may use
only the granularity and event semantics actually present in the source.

### 5.2 Hypothesis-first funnel

Microstructure research follows this funnel:

```text
Hypothesis-first
→ Limited feature family
→ Purged walk-forward
→ Out-of-sample evaluation
→ Transaction-cost stress
→ Latency/slippage stress
→ Redundancy test
→ Survive or reject
```

Each feature family must declare its mechanism, source events, formula, horizon,
availability rule, missingness rule, cost exposure, and expected failure conditions before
target-aware evaluation.

### 5.3 Initial interpretable feature families

The initial starting set should remain bounded and interpretable, for example:

- spread and quoted depth;
- depth imbalance;
- signed trade volume;
- aggressor imbalance;
- cancel/add ratio or liquidity withdrawal;
- absorption and book-resiliency measures.

These are families, not permission to enumerate thousands of windows, levels, transforms,
and thresholds. Every expansion consumes a declared hypothesis and search budget.

### 5.4 Prohibited feature fishing

The project must not generate a massive raw order-book feature library and select whichever
features or windows maximize TRAIN Sharpe, AUC, or P&L. Deep raw-L2/L3 representations are
later challengers, not the default starting point. They become eligible only after data
quality, sample sufficiency, mechanism, compute budget, and evaluation discipline are
demonstrated.

---

## 6. Controlled machine-learning research stack

Test 2 may admit six model families through staged challenger authorization:

| Family | Representative methods | Primary role | Entry posture |
|---|---|---|---|
| 1. Linear / probabilistic | Logistic regression, regularized GLM | Interpretable probability baseline | First-line baseline |
| 2. Tree / gradient boosting | Shallow tree, XGBoost, LightGBM, CatBoost | Nonlinear tabular interactions | Controlled challenger |
| 3. Regime / state | HMM, change-point, Kalman/state-space | Causal context/state estimation | After state hypothesis |
| 4. Classical time series | AR/ARIMA where appropriate, GARCH, OU | Serial dynamics, volatility, mean reversion | Mechanism-specific challenger |
| 5. Neural sequence | TCN, LSTM, GRU | Multi-scale temporal representation | After simpler challengers |
| 6. Transformer / deep microstructure | TFT/PatchTST-style, DeepLOB-style models | Long dependencies or structured LOB representation | Data- and hypothesis-gated challenger |

The list is an allowed research map, not authorization to run all families. Each family
requires a bounded experiment proposal, an explicit model budget, and a reason it can test
something materially different from already rejected candidates.

### 6.1 Supporting layer A — Ensemble / stacking

Ensembling is not a seventh independent edge family. It may combine independently useful
components only after their evidence exists. Training must use out-of-fold component
predictions, and meta-model fitting must remain inside the applicable training boundary.
An ensemble may not hide weak components or silently multiply the search budget.

### 6.2 Supporting layer B — Calibration

Calibration is required when model output is consumed as probability. Global calibration
is the simple baseline; regime-conditional calibration is a challenger requiring adequate
sample size and evidence. Platt, isotonic, or other methods must be fitted within the
training fold and evaluated with log loss, Brier score, and reliability diagnostics.

### 6.3 What the stack does not authorize

The architecture prohibits this pattern:

```text
40 models × hundreds of hyperparameters
→ inspect the same outcomes repeatedly
→ report the highest Sharpe
```

That is model shopping, not controlled evidence. Compute scale does not convert repeated
selection into out-of-sample confirmation.

---

## 7. Champion–challenger research method

### 7.1 Historical champion/baseline

`LR001` and `TREE001` are immutable Test 1/Sprint 1 baseline evidence. Their historical
specifications, runs, metrics, and dispositions must not be relabeled, rerun under the same
identity, or rewritten to fit VNext.

They are the comparison history, not presumed production champions and not evidence that a
more complex Test 2 model will work.

### 7.2 Controlled challenger sequence

For every challenger:

1. state one falsifiable hypothesis and mechanism;
2. identify the pillar(s) and the exact role of each input;
3. freeze eligible data, features, target, horizon, and costs;
4. freeze parameter/search bounds and the model-family budget;
5. freeze time-aware folds, purge/embargo, and fitting boundaries;
6. freeze one primary decision metric and the rejection rule;
7. fit preprocessing, model, state, calibration, and ensemble components inside folds;
8. retain every attempt and negative result under an immutable experiment identity;
9. run Skeptic / Alpha-Killer review;
10. promote only through separately governed confirmation and the Release Gate.

### 7.3 Multiple-testing control

Before Test 2 begins, governance must set:

- a hypothesis budget;
- a candidate/model-family budget;
- bounded hyperparameter degrees of freedom;
- rules for related variants and what counts as a new attempt;
- false-discovery or family-wise interpretation appropriate to the final design;
- a Validation-opening budget;
- stop conditions after success or failure.

Search history is append-only. Validation and the sealed Final Test cannot be used as tuning
surfaces. A failed hypothesis cannot be changed after seeing its confirmatory result and
represented as unchanged.

---

## 8. Human-directed research and review

The research process is human-directed and has no graph-runtime or orchestration-framework
dependency. The Owner may ask people or bounded AI tools to perform tasks such as:

- hypothesis generation and formalization;
- specialist debate and critique;
- experiment proposal drafting;
- required-field and evidence checks;
- redundancy and alternative-explanation challenges;
- economic-regime rationale challenges;
- microstructure hypotheses and data-requirement checks;
- model-family recommendation within a declared budget;
- experiment-design review and routing.

The governing identity remains:

```text
LLM = RESEARCHER
LLM != TRADER
```

Research assistants and reviewers must not:

- issue BUY/SELL authority directly;
- become an uncalibrated signal input;
- convert subjective news interpretation into a trading signal;
- bypass the probability model, machine validation, governance, or risk engine;
- open TRAIN labels, Validation, or Final Test without the applicable authorization;
- self-promote a model or modify production artifacts;
- size positions, send broker orders, or execute through IBKR.

Human-directed debate produces proposals and critiques. Machine-reproducible evidence
determines experiment outcomes, and the existing human/governance gates determine
authorization.

No workflow engine, graph runtime, or orchestration framework is part of this architecture.
Introducing one would require a new Owner decision and a separately reviewed architecture
change; the retired LangGraph branches grant no precedent or authority.

### 8.1 Skeptic / Alpha-Killer review

Every candidate must receive an adversarial review whose goal is to reject weak
alpha rather than improve its story. It asks at minimum:

- Is the result overfit?
- Is there timestamp, label, revision, or selection leakage?
- How much multiple testing preceded this candidate?
- Does the result exist in only one fold, period, or regime?
- Is it a transaction-cost artifact?
- Is it sensitive to slippage, latency, or execution delay?
- Is the feature redundant with a simpler observable?
- Is sample size and dependence-aware uncertainty adequate?
- Does it survive purged walk-forward and untouched out-of-sample evidence?
- Is there a simpler explanation for the apparent effect?

The Skeptic / Alpha-Killer may recommend rejection, redesign, or additional governed tests.
It has no trading, risk-override, data-access, promotion, or deployment authority.

---

## 9. Repeatable edge-discovery factory

The project does not seek one secret formula. It builds a repeatable factory:

```text
Public Knowledge
  + Proprietary Research
  + Proprietary PIT Data Construction
  + Proprietary Features
  + Microstructure
  + Execution Edge
  + Risk Edge
        ↓
Repeated Controlled Experiments
        ↓
Surviving Edges
```

Candidate edge categories are:

- **Information Edge** — cleaner, earlier, or more faithful PIT reconstruction of legally
  available objective information;
- **Modeling Edge** — better conditional estimation, interaction handling, calibration, or
  uncertainty control;
- **Structural Edge** — repeatable market-mechanism behavior with defensible persistence;
- **Execution Edge** — better timing, fill quality, spread/slippage/impact control, or
  implementation parity;
- **Risk Edge** — better permission, sizing, state control, and survival through adverse
  conditions.

Public knowledge supplies hypotheses and priors. The potential moat is the proprietary
combination of data provenance, disciplined research, features, execution, risk, and the
ability to kill false edges quickly.

---

## 10. Pipeline role separation

The research-to-execution chain is:

```text
Human-Directed Research and Review
        ↓
Experiment Proposal
        ↓
Governed Data Access
        ↓
Machine Validation
        ↓
Probability Model
        ↓
Calibration
        ↓
Regime / Numerical Context
        ↓
Net Expected Value / Permission
        ↓
Risk Engine
        ↓
Position Size
        ↓
Execution Policy
        ↓
Broker Adapter / IBKR
```

Roles and boundaries:

- **Human-directed research and review** proposes and critiques; it does not emit executable
  authority and has no graph-runtime dependency.
- **Machine Validation** calculates reproducible outcomes under the frozen protocol.
- **Probability/Calibration** estimates and qualifies probability; it does not size risk.
- **Economics/Regime** may provide causal context, interaction, permission, or sizing inputs
  when approved; it is not forced into a directional vote.
- **Microstructure** may feed short-horizon alpha-quality context and the execution layer;
  those two uses are declared and evaluated separately.
- **Risk Engine** applies approved limits, permissions, and state controls independently of
  model enthusiasm.
- **Execution** transforms an approved, sized decision into orders under cost, latency,
  idempotency, and broker-state controls.
- **IBKR** is an adapter and external execution venue, never the research authority.

No layer may silently bypass the layer below it or appropriate another layer's authority.

---

## 11. Test 1 and Test 2

### 11.1 Test 1

```text
Status: HISTORICAL / IMMUTABLE BASELINE
Architecture: MES_QUANT_TARGET_ARCHITECTURE_v2.2
Research coordination: human-directed / no graph runtime
Baseline model evidence: LR001 + TREE001
```

Test 1/Sprint 1 remains exactly as recorded. VNext may cite it but may not modify its
features, search budget, metrics, costs, results, access history, or interpretation limits.

### 11.2 Test 2

```text
Status: DESIGN CANDIDATE ONLY
Architecture: MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT
Research coordination: human-directed proposals and adversarial critique
Outcome authority: machine tests under a separately frozen protocol
Execution: NOT AUTHORIZED
```

Test 2 may introduce new PIT data, feature families, model challengers, calibration, and
microstructure research only through the new governed scope. It does not inherit permission
from Test 1 or from this architecture document.

---

## 12. Minimum gate before Test 2 execution

Before any target-aware Test 2 execution, a separate governed protocol must freeze at
least:

- Test 2 scope, experiment identity, and exact objective;
- permitted label-access level and explicit Owner authorization;
- source datasets, licenses where applicable, and immutable provenance;
- PIT/vintage schema and `AVAILABLE_TIME <= DECISION_TIME` tests;
- hypothesis, mechanism, pillar, expected direction, and horizon;
- feature family and bounded hypothesis/model/hyperparameter budgets;
- target, cost, impact, and decision-universe contracts;
- purged walk-forward folds, embargo, and all fit/transform boundaries;
- primary metric, diagnostics, dependence-aware uncertainty, and rejection rule;
- transaction-cost, latency, slippage, and regime-stability stress;
- calibration and ensemble nesting when applicable;
- Skeptic / Alpha-Killer checklist and resolution record;
- stop conditions and the separately governed path to confirmation.

Until that protocol is accepted:

```text
TEST2_STATUS = DESIGN_ONLY
TARGET_AWARE_EXECUTION = NOT_AUTHORIZED
VALIDATION = UNOPENED
FINAL_TEST = SEALED
LIVE_TRADING = DISABLED
```

---

## 13. Architecture invariants retained from v2.2

VNext retains these boundaries:

- governance and provenance cover research and production;
- observed label access determines work classification;
- canonical inputs and experiment history are immutable under their controls;
- fitted state, preprocessing, models, ensembles, and calibration remain causal/OOF;
- no Final-Test tuning or production self-modification;
- research promotion passes through confirmation and the Release Gate;
- bad required data or unreconciled broker state creates no new risk;
- monitoring may become more conservative under frozen policy but may not create new
  eligibility or silently rewrite methodology;
- model changes return to research; they do not auto-retrain and auto-deploy;
- an independent watchdog remains required before meaningful live trading.

This architecture is a design candidate, not an instruction to implement an orchestration
framework, open Test 2, build deep models, access new data, or connect to IBKR.

# MES Research Architecture — Test 2 Proposal V1

**Document status:** `RETAINED_DESIGN_RATIONALE / NON-AUTHORITATIVE / RESEARCH_ONLY`

**Promoted design candidate:**
[`MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT.md`](../architecture/MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT.md)

This file preserves the decision proposal that led to Architecture VNext. It is not the
current architecture pointer and grants no implementation or execution authority.

**Baseline relationship:** This proposal extends the research direction without modifying
`MES_QUANT_TARGET_ARCHITECTURE_v2.2`, the locked Test 1/Sprint 1 record, any canonical
artifact, or any frozen governance control. It grants no data access, experiment execution,
Validation opening, Final-Test opening, production release, or live-trading authority.

## 1. Purpose and boundary

This document records the proposed research architecture for the next governed research
cycle ("Test 2"). It separates objective data from human narrative, broadens the candidate
model stack in a controlled way, and defines LangGraph as a research-control tool rather
than a trading authority.

The following remain unchanged:

- Test 1 is the locked baseline and historical evidence; it must not be edited or
  reinterpreted retroactively.
- The existing Sprint 1 record remains frozen. `LR001` and `TREE001` remain the simple
  baseline families already tested under that bounded protocol.
- Existing label-access levels, canonical-artifact read-only rules, Validation controls,
  the sealed Final Test, Release Gate, and live-disabled state remain in force.
- Test 2 requires its own predeclared scope, experiment identities, access authorization,
  search budget, continuation/falsification rules, and approval path before execution.

## 2. Constitutional information boundary

The engine may consume only information that was objectively observable and available at
the exact decision time.

For every input used to make a historical or live decision, the system must be able to
establish:

```text
available_time <= decision_time
```

The relevant time is when the information became available to the decision process, not
merely the period it describes or a date later assigned by a vendor. Backtests must recreate
the information set available then. They may not substitute present-day corrected data,
latest revisions, hindsight labels, or narratives written after the decision.

Human opinion, discretionary interpretation, gossip, political-insider information,
analyst narrative, and manually assigned sentiment are not eligible signal inputs. A market
state associated with fear, urgency, or disagreement is eligible only when represented by
an objective, timestamped numerical observation under the same point-in-time rule.

Missing provenance or uncertain availability fails closed for research eligibility. It may
not be repaired by assuming the value was known earlier.

## 3. Four research pillars

The research program is organized into four complementary pillars. They are sources of
hypotheses and evidence, not automatically four equal-weight model votes.

### 3.1 Market Dynamics / Physics

Study measurable price, volatility, path, liquidity, and temporal behavior: momentum,
mean reversion, volatility clustering, range/path structure, state transitions, and other
causal transforms of information available by decision time.

### 3.2 Statistics / Machine Learning

Estimate conditional probabilities and nonlinear relationships, quantify uncertainty,
compare candidates out of sample under time-aware splits, and calibrate predictions. Model
complexity is justified by repeatable evidence, not by novelty.

### 3.3 Economics / Regime

This pillar is **point-in-time numerical context only**. Eligible examples include a
latest-known macro release, yield-curve value, rate, volatility index, or credit-spread
measure with trustworthy publication and availability provenance.

It excludes subjective news interpretation, Wall Street gossip, political-insider
information, analyst opinions, discretionary labels such as "hawkish" or "recession fear",
and manual sentiment scoring. Economics/Regime may condition or challenge an alpha thesis;
it does not receive voting authority merely because it is a separate pillar.

### 3.4 Microstructure / Flow

This pillar is **exchange-observed numerical state only**: timestamped trades, quotes,
book updates, aggressor-side measures when defensibly derived, spread, depth, imbalance,
cancellations, liquidity withdrawal, and resiliency.

Its primary role is short-horizon alpha-quality assessment and execution: determine whether
an apparent edge is tradable, whether liquidity supports it, and how timing, spread,
slippage, impact, and fill risk alter expected value. It is not automatically an
equal-weight voter alongside slower pillars. Any use as a directional alpha input must be
separately hypothesized, tested, and governed.

## 4. Point-in-time and vintage-data contract

Reconstructable economic and contextual observations require, at minimum:

```text
series_id
observation_period
release_timestamp
availability_timestamp
vintage_timestamp
value
source/vendor identity
retrieval timestamp
timezone and timestamp precision
revision/supersession relationship
provenance hash or equivalent immutable source identity
```

The backtest join selects the value actually available at `decision_time`; it must not join
by observation period alone. When embargo, vendor latency, or timestamp precision is
uncertain, the availability rule must use a conservative delay or reject the observation.

Consensus/expectations data are eligible only when their historical point-in-time
provenance is trustworthy: the exact consensus value, constituent/methodology policy where
material, collection cutoff, publication timestamp, later corrections, and vendor history
must be reproducible. A current consensus-history table that may have been backfilled or
rewritten is not sufficient.

Revised series must preserve vintages rather than overwrite history. Test 2 must include
explicit leakage tests demonstrating that later releases or latest revisions cannot enter
earlier decisions.

## 5. Microstructure historical reconstruction

Historical microstructure research should reconstruct state from ordered exchange event
data whenever the hypothesis requires it. Required controls include instrument/contract
identity, exchange sequence and timestamp handling, trade/quote or book event semantics,
session and reset boundaries, duplicate/out-of-order policy, feed gaps, depth availability,
and the latency/availability assumption at decision time.

Research must be hypothesis-first and limited to predeclared feature families. Examples of
bounded families are spread/depth, order-flow imbalance, cancellation/liquidity withdrawal,
and post-event book resiliency. Each family needs a mechanism, horizon, formula, source
events, availability rule, missingness rule, and expected failure conditions before
target-aware testing.

Raw massive feature shopping is prohibited. The engine should not generate thousands of
book transforms and select whichever correlates with TRAIN outcomes. Expansion requires a
new governed hypothesis and consumes an explicit multiple-testing/search budget.

## 6. Controlled machine-learning research stack

Test 2 may research six model families, introduced by staged authorization rather than as
one simultaneous model zoo:

| Family | Representative methods | Intended research role |
|---|---|---|
| 1. Linear / probabilistic | Logistic regression, regularized GLM | Transparent probability baseline |
| 2. Tree / gradient boosting | Bounded trees, XGBoost, LightGBM, CatBoost | Controlled nonlinear interactions in tabular data |
| 3. Regime / state | HMM, change-point, Kalman/state-space | Latent or changing market-state representation |
| 4. Classical time series | AR/ARIMA, GARCH, OU | Serial dynamics, volatility, and mean reversion |
| 5. Neural sequence | TCN, LSTM, GRU | Bounded multi-horizon temporal representations |
| 6. Transformer / microstructure deep model | TFT, PatchTST, DeepLOB-style models | Long dependencies or structured order-book research after data sufficiency is proven |

Two supporting layers are separate from the six candidate families:

- **Ensemble / stacking:** combine independently useful candidates only after component
  evidence exists; it must not conceal weak components or expand the search budget silently.
- **Calibration:** Platt, isotonic, or other predeclared calibration methods evaluated with
  proper nested/time-aware fitting, Brier score, log loss, and reliability diagnostics.

`LR001` and `TREE001` remain the historical baseline evidence; Test 2 does not relabel or
rerun them silently. More advanced families are challengers, not presumed improvements.

Use champion-challenger governance:

1. Freeze the incumbent champion and comparison metric before evaluating a challenger.
2. Predeclare hypothesis, features, parameter/search bounds, folds, costs, and rejection
   rule for each challenger.
3. Fit preprocessing, state, calibration, and ensembles strictly inside the applicable
   training window; use nested/time-aware evaluation where selection occurs.
4. Record every attempted candidate, including failures, under an immutable experiment
   identity.
5. Promote only through the existing confirmatory and Release-Gate path; complexity or
   in-sample performance confers no authority.

Model shopping and repeated testing are explicit risks. Test 2 must set a finite search
budget by hypothesis and model family, distinguish exploration from confirmation, control
selection inside folds, preserve negative results, and avoid tuning on Validation or the
sealed Final Test. Trying many architectures and reporting only the winner is prohibited.

## 7. Test 1 and Test 2 relationship

```text
Test 1
  = locked baseline and immutable historical evidence
  = LR001/TREE001 remain baseline model evidence
  = no retrospective scope, rule, metric, or narrative change

Test 2
  = LangGraph-assisted candidate research proposal
  = broader pillars and controlled challenger stack
  = new governance scope; no authority inherited merely from this document
```

Test 2 must compare against the locked baseline without rewriting it. Any new data family,
target, horizon, feature, model, calibration method, or ensemble is a declared Test 2
candidate and must follow the applicable access and multiple-testing controls.

## 8. LangGraph authority boundary

LangGraph may orchestrate the research workflow: create structured proposals, route work to
specialist reviewers, check required fields, request evidence, compare candidate records,
and coordinate critique. It may help enforce that a hypothesis and search budget exist
before an experiment is proposed.

LangGraph is never:

- a trader;
- a direct signal source or signal authority;
- an execution authority;
- a risk-limit override;
- a model self-promotion path;
- permission to open TRAIN labels, Validation, Final Test, production, or live trading.

All numerical claims must resolve to reproducible data/code/config evidence. Agent prose,
consensus, confidence, or debate outcome is not evidence and cannot override a failed
machine predicate or human approval gate.

## 9. Edge factory and adversarial review

The proposed edge factory treats public knowledge as a starting prior, not a moat:

```text
public knowledge
  + proprietary research process
  + trustworthy point-in-time data
  + disciplined features
  + microstructure and execution evidence
  + cost and risk controls
  = candidate edge, subject to falsification and governance
```

The durable advantage is expected to come from the quality of proprietary hypotheses,
clean historical reconstruction, reproducible feature definitions, execution realism, risk
control, and fast rejection of false discoveries—not from merely using a more complex
model.

Every candidate path must include an independent **Skeptic / Alpha-Killer** review. Its job
is to search for leakage, timestamp errors, revision leakage, regime dependence, unstable
folds, multiple-testing effects, capacity/impact problems, cost sensitivity, calibration
failure, and simpler explanations. It may recommend rejection or further tests; it cannot
approve deployment or manufacture a replacement signal.

## 10. Minimum gate before any Test 2 execution

Before a Test 2 target-aware run, a separate governed protocol must freeze at least:

- Test 2 scope and experiment identifier;
- exact data sources and point-in-time/vintage provenance;
- hypothesis, pillar, mechanism, horizon, and expected direction;
- feature family and bounded candidate/model search budget;
- time-aware folds, purge/embargo rules, and all fitting boundaries;
- cost, slippage, and microstructure assumptions where applicable;
- primary metric, diagnostics, challenger comparison, and falsification rule;
- calibration/ensemble nesting rules if used;
- permitted information-access level and explicit authorization;
- Skeptic / Alpha-Killer review checklist;
- stop conditions and the path, if any, to separately governed confirmation.

Until that protocol is accepted, Test 2 remains `PROPOSAL_ONLY / EXECUTION_NOT_AUTHORIZED`.

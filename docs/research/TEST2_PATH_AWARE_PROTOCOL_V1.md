# MES Test 2 — Path-Aware LONG/FLAT Protocol V1

**Document status:** `DRAFT_FOR_OWNER_REVIEW / L0_AUTHORING_ONLY`

**Execution status:** `NOT_AUTHORIZED`

**Exploration scope ID:** `MES_TEST2_PATH60_LONG_FLAT_FEATURE29_V1`

**Authoring base:** `793f11aab29148b13c2f41629ffdbd250b4b8d03`

**Authoring branch:** `research/test2-path-protocol-v1`

**Architecture relationship:** Test 1 remains immutable under
`MES_QUANT_TARGET_ARCHITECTURE_v2.2`. This is a bounded Test 2 draft under
`MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT`, with LangGraph retired and research review
remaining human-directed.

This document does not authorize code changes, artifact access, target construction,
model training, Validation, Final Test, production, push, or merge. The Owner authorized
only this docs-only drafting and adversarial-review package. That authorization may not be
reused for implementation or a target-aware run.

---

## 1. Research question and material novelty

Test 1 asked whether the 29 Cell 14 point-in-time feature candidates could predict the
binary `LONG` versus `FLAT` mapping at the fixed `+60m` endpoint. It tested one
regularized linear model and one bounded shallow nonlinear tree. Both lost to the
fold-correct TRAIN prior on overall and median per-fold binary log loss.

Test 2 must not respond by placing a larger model on the same information, target, folds,
and metric. The material change proposed here is the target: use the ordered 60-minute
price path to distinguish a favorable-first LONG path from an adverse-first or no-touch
path while preserving the `LONG / FLAT` action space.

The research question is:

> Beyond the trivial effect of current volatility/range on barrier reachability, can the
> full point-in-time feature state identify a LONG path that reaches one predeclared
> favorable barrier before one predeclared adverse barrier during the next 60 minutes,
> with stable TRAIN-only out-of-fold probability quality?

The proposed mechanism is that recent path, volatility, trading-activity proxies, session
position, and other available-at-decision state may contain more information about the
quality and risk of the next 60-minute path than about its endpoint sign alone.

This is falsifiable. A model that merely learns that higher volatility reaches barriers
more often is not a Test 2 success.

---

## 2. Immutable Test 1 baseline and evidence limit

Test 1 and its spent search budget are not reopened.

| Candidate | Model family | Candidate OOF log loss | Prior OOF log loss | Improvement | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| `MES_S1_LR001_20260815T095100Z` | regularized logistic regression | `0.6959965499073583` | `0.6933619512442667` | `-0.0026345986630915696` | failed |
| `MES_S1_TREE001_20260815T192900Z` | bounded shallow tree | `0.6948528055752081` | `0.6933619512442667` | `-0.0014908543309414268` | failed |

The local experiment records are external observed evidence, not tracked canonical Git
objects and not machine-established at Test 1 integration time:

| Record | Observed SHA-256 |
| --- | --- |
| LR001 `experiment_record.json` | `093ff155b2ac77172acdd99c0f5b4ffd713c7c4ea9556bcb18170480d68e58b9` |
| TREE001 `experiment_record.json` | `fad9367ff353671ccf42739a02ece5178ddd60ce973917bc118ba8e54e77f7a6` |

They may support draft rationale, subject to this evidence limit. They may not be silently
copied into Git, rewritten, rerun under their old identities, or treated as release or
champion evidence.

The failed Test 1 disposition remains valid because binary log loss was the deciding
metric. Before any Test 2 execution, separate forward remediation must address:

- the shared trapezoidal PR-AUC implementation, which can overstate coarse-score results;
- the stale `DRY_RUN_ONLY_L0` field recorded beside observed L1 access;
- a Test 2 record schema that cannot reproduce that access-status contradiction.

These defects do not convert Test 1 primary failure into a pass.

---

## 3. Scope held fixed

Unless the Owner approves an explicit amendment before target-aware access, Test 2 holds
these boundaries fixed:

- instrument: CME Micro E-mini S&P 500 futures (`MES`);
- canonical source: Databento `GLBX.MDP3 / ohlcv-1m` lineage;
- decision grid: completed 15-minute bars;
- horizon: 60 one-minute bars starting at offsets `0..59` from decision time;
- entry reference: frozen Cell 10/12 `entry_reference_close`, the completed 15-minute
  close at decision time;
- action space: `LONG / FLAT`; `SHORT` remains diagnostic, not executable;
- input feature artifact SHA-256:
  `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452`;
- ordered 29-feature content SHA-256:
  `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`;
- input catalog status remains globally `PROVISIONAL`; Test 2 freezes membership from the
  two exact identities above for this scope only, with no feature addition, removal, or
  subset search and no claim that the catalog became globally locked;
- canonical upstream artifacts: read-only;
- outer Validation: unopened, with proposed lifetime opening budget `1` and no automatic
  opening from a TRAIN result;
- Final Test: sealed;
- live trading and broker connectivity: disabled.

Observed Stage B V1.2 status is policy `LOCKED` and execution `DISABLED`; full Phase B/C/D
production execution is not implemented. This draft proposes that Stage B execution and
a reduced feature set are not Test 2 prerequisites, but the Owner must ratify that proposal
before protocol acceptance. Test 2 does not enable or modify Stage B.

No macro-vintage, quote, order-book, aggressor, depth, or external alternative data is in
scope. Gradient boosting, neural sequence, Transformer, DeepLOB-style, ensemble, and
stacking candidates are excluded from this Test 2 V1 scope.

---

## 4. Data, source, and access contract

### 4.1 Model inputs

The only model inputs are the 29 Cell 14 candidates. Every input must pass a
machine-verifiable assertion of the canonical invariant:

```text
feature_max_source_time_utc <= decision_time
```

No target, future return, path high/low, MFE, MAE, drawdown, barrier result, Validation
outcome, Final-Test value, or execution outcome may enter a feature, imputation rule,
transform, candidate definition, or threshold fit.

The four `PATHNUISANCE001` inputs — `realized_vol_60m`, `realized_vol_120m`,
`realized_vol_240m`, and `bar_log_range_15m` — must be verified as exact members of the
pinned 29-feature content before fitting. Their membership and ordering may not be supplied
from a later catalog or an unpinned list.

### 4.2 True target source and Cell 12 reconciliation role

First-touch order cannot be recovered from the aggregate Cell 12 path-outcome parquet.
That artifact stores path high/low, extrema timestamps, MFE/MAE, and drawdown; it does not
persist every minute or the first touch of an arbitrary barrier.

Any later authorized target builder must therefore read the exact decoded Cell 2 one-minute
frame used by Cell 12:

```text
raw DBN SHA-256             49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0
decoded mes_1m SHA-256      e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584
decoded rows                2,551,123
decoded timestamp range     2019-05-05T22:00:00Z .. 2026-07-31T20:59:00Z
```

Because this frame physically spans the sealed Final-Test period, the future target builder
must construct the allowed timestamp request set before any path lookup:

1. bind the exact Cell 8 split-assignment identity
   `2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035`;
2. admit outer-`TRAIN` rows only;
3. exclude every outer-`VALIDATION` row and every `FINAL_TEST` row before exposing any
   numeric path field;
4. construct every requested path-bar key as
   `(decision_identity, minute_offset, requested_timestamp_utc)`;
5. assert the parent decision role of every key is outer-`TRAIN`;
6. assert every requested timestamp is earlier than the outer-Validation boundary
   `2024-01-02T14:45:00Z`;
7. define `validation_path_bar_lookup_count` as the number of requested keys whose parent
   role is outer-`VALIDATION` or whose timestamp is at or after
   `2024-01-02T14:45:00Z` and before `2025-01-02T14:45:00Z`, then assert it is `0`;
8. define `final_test_path_bar_lookup_count` as the number of requested keys whose parent
   role is `FINAL_TEST` or whose timestamp is at or after `2025-01-02T14:45:00Z`, then
   assert it is `0`;
9. hash and persist the ordered request-key set before numeric lookup;
10. request exactly offsets `0..59` for the remaining TRAIN decisions only.

Masking after target construction is forbidden. A target may never be constructed for a
non-TRAIN row.

For every allowed row, later execution must require:

- exactly 60 present one-minute bars;
- the same instrument throughout the path;
- the close at offset `59` reconciles to the Cell 10 `+60m` endpoint;
- no target/path field is exposed as a feature;
- source hashes and request-set hashes are recorded before numeric target access.

Cell 12 is reconciliation evidence, not the first-touch source. Its declared observed state
is:

```text
usable Development paths       31,165  (TRAIN + outer Validation; not the Test 2 sample)
path outcome SHA-256            8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941
path status SHA-256             0aae7ac729663991b3bb806942b44da05bb02fb3a29216ad491c1de896c413db
recorded Final-Test lookups     0
```

If the Cell 12 artifact is available later under an authorized filtered read, recomputed
TRAIN path high/low and MFE/MAE must match it exactly. Protocol authoring opens neither the
decoded path data nor the Cell 12 target parquet.

### 4.3 Actual exploratory surface and dependence

The frozen OOF holdouts remain:

- `WF_2022`: 5,510 rows before feature/target eligibility;
- `WF_2023`: 5,474 rows before feature/target eligibility;
- pooled maximum before eligibility: 10,984 rows.

Cell 13 records descriptive effective sample sizes of approximately `1,290–1,370` per
fold and lag-1 return autocorrelation of approximately `0.756–0.769`. Row count is not an
independent sample size.

For the `WF_2022` and `WF_2023` OOF boundaries only, the existing 60-minute purge remains
valid; recorded purged rows are `0` because the natural calendar-year gaps exceed the
horizon. The outer TRAIN set ends on `2023-12-29`, before the outer-Validation boundary on
`2024-01-02`; the Final-Test boundary is later on `2025-01-02` and is outside the entire
Test 2 request set. These outer boundaries are enforced by the timestamp-keyed assertions
in Section 4.2, not inferred from the OOF purge count. Recorded embargo is `0 / OPEN`. The
Owner must ratify the embargo rule before protocol acceptance.

### 4.4 Missingness, ambiguity, and retained-set rules

- no arbitrary imputation;
- rows without a valid decision-time feature vector or complete authorized path become
  `NO_SCORE / FLAT` for policy coverage;
- same-bar ambiguity is target-derived and cannot enter model inputs;
- the fold prior, nuisance benchmark, and full candidate must be fit and scored on exactly
  the same retained row set;
- ambiguous/excluded rows remain in total coverage accounting and map to `FLAT`;
- ambiguity and exclusion counts/rates must be reported overall, by fold, and by
  predeclared volatility decile;
- exclusion is acknowledged as non-random and feature-correlated;
- no barrier may be changed after observing prevalence, ambiguity, exclusion, class
  support, metric, economic, or any other target-derived statistic.

---

## 5. One path-aware target parameterization

Exactly one barrier parameterization is permitted in Test 2 V1:

```text
ENTRY_PRICE                    entry_reference_close
TAKE_PROFIT_GROSS_POINTS       OWNER_DECISION_REQUIRED
STOP_GROSS_POINTS              OWNER_DECISION_REQUIRED
CONSERVATIVE_ROUND_TRIP_COST   0.994 index points / USD 4.97
ONE_MINUTE_BAR_OFFSETS         0..59
```

The favorable gross barrier must exceed the frozen conservative break-even cost:

```text
TAKE_PROFIT_GROSS_POINTS - 0.994 > 0
```

The Owner must freeze the exact take-profit and stop values before access. Values must be
economically justified; target prevalence or apparent balance may not select them.

For each allowed TRAIN row, process the authorized one-minute OHLC bars chronologically:

- favorable touch: bar high reaches `ENTRY_PRICE + TAKE_PROFIT_GROSS_POINTS`;
- adverse touch: bar low reaches `ENTRY_PRICE - STOP_GROSS_POINTS`;
- `PATH_LONG = 1` only when the favorable barrier is observed first;
- `PATH_LONG = 0` when the adverse barrier is observed first or neither is reached;
- if both barriers are reachable inside the same one-minute OHLC bar before a prior touch,
  the order is unobservable and disposition is `AMBIGUOUS_SAME_BAR`.

Draft fail-closed default for `AMBIGUOUS_SAME_BAR` is: exclude from fitting/scoring, report
under Section 4.4, and map to `FLAT` for policy coverage. The Owner must ratify or replace
this rule before acceptance.

This target is a touch-defined research counterfactual, not historical actual P&L and not
an executable fill claim. A favorable high may not receive a limit fill; an adverse stop
may gap through and fill worse. Latency and fill realism remain `OPEN`. Historical-vintage
cost coverage remains `0.0`; USD views are current-deployment/stress counterfactuals only.

---

## 6. Fixed target-aware evaluation budget

Exactly one barrier set and two fixed target-aware fitted models are permitted:

```text
target-aware evaluations = 1 barrier set x 2 fitted models = 2
```

1. `PATHNUISANCE001` — a fixed regularized logistic reachability benchmark using only:
   `realized_vol_60m`, `realized_vol_120m`, `realized_vol_240m`, and
   `bar_log_range_15m`.
2. `PATHFULL001` — one fixed regularized logistic candidate using the complete 29-feature
   catalog with fold-local preprocessing and no feature selection.

Both definitions must be frozen before the same authorized run package. Neither model may
be selected, revised, or gated using the other's observed result. `PATHFULL001` is the only
candidate eligible for an interesting-enough disposition; it must beat both the fold prior
and `PATHNUISANCE001`. Nuisance-model success alone is not a path-quality edge.

Gradient boosting, a third model, a second barrier set, feature-subset search, threshold
search, neural networks, Transformers, calibration-method search, ensembles, and stacking
are forbidden.

The models' native logistic outputs are exploratory probability scores only and have no
action or release authority. One fixed fold-local calibration method, if required for a
later confirmatory package, must be separately frozen before Validation; it may not rescue
Test 2 failure or be chosen from Test 2 results.

Each fitted model consumes one unique `EXPERIMENT_ID`. The record must include at least:

- `EXPERIMENT_ID`, timestamp, and `EXPLORATION_SCOPE_ID`;
- exact source, role-assignment, feature, target, cost, code, environment, and authorization
  identities;
- model family, features, fixed parameters, preprocessing, folds, and retained-set hash;
- primary metric, diagnostics, result, and disposition;
- accurate harness status and observed access level;
- TRAIN/Validation/Final-Test lookup counters;
- ambiguity, missingness, exclusion, and search-budget counters.

---

## 7. Evaluation and continuation rule

### 7.1 Folds and baselines

Reuse `WF_2022` and `WF_2023` with the existing chronological 60-minute boundary policy.
`WF_2024` is outer Validation and remains forbidden.

Required baselines:

1. fold-correct TRAIN prior for `PATH_LONG` on the exact retained set;
2. `PATHNUISANCE001` on the same retained set.

### 7.2 Primary metric

Primary metric: out-of-fold binary log loss.

```text
IMPROVEMENT_VS_PRIOR = prior_oof_log_loss - PATHFULL001_oof_log_loss
IMPROVEMENT_VS_NUISANCE = PATHNUISANCE001_oof_log_loss - PATHFULL001_oof_log_loss
```

`PATHFULL001` is `INTERESTING_ENOUGH_TO_CONTINUE` only if all are true:

1. overall and median per-fold `IMPROVEMENT_VS_PRIOR` exceed a predeclared minimum effect;
2. overall and median per-fold `IMPROVEMENT_VS_NUISANCE` exceed the same or separately
   predeclared minimum effect;
3. the session-block dependence-aware lower confidence bound for both improvements is
   greater than `0`;
4. effective sample size and per-class support meet predeclared floors;
5. all source, role, availability, ambiguity, access, and search-budget gates pass.

The Owner must freeze the minimum effects, confidence level/block rule, effective-sample
floor, and class-support floor before protocol acceptance. Equality is not a pass.
Diagnostics cannot rescue primary failure.

### 7.3 Diagnostics and economic view

- Brier score and improvement versus both baselines;
- tie-safe ROC-AUC;
- average precision using a correct stepwise estimator, not the known trapezoidal PR-AUC;
- calibration/reliability views;
- target prevalence, probability distribution, and action coverage;
- per-fold and per-session stability;
- ambiguity, missingness, and `NO_SCORE / FLAT` rates;
- paired five-session block-bootstrap counterfactuals;
- Cell 13's non-overlapping 60-minute LONG/FLAT position policy;
- the USD `4.97` conservative round-trip charge once per executed trade;
- only predeclared stress values, never used to select a winner.

### 7.4 Cross-test interpretation

Test 1 and Test 2 reuse the same TRAIN years and feature catalog but ask different targets.
All four fitted attempts across the two tests remain visible. Test 2 is exploratory and no
family-wise confirmatory claim is permitted from TRAIN. A Test 2 pass may nominate at most
one exact `PATHFULL001` candidate for one separately frozen confirmatory protocol. Proposed
Validation-opening budget over the full Test 2 scope is `1`; opening remains separately
authorized and may not occur automatically.

---

## 8. Stop conditions and bounded interpretation

Stop and return to the Owner if:

- source identity, role binding, availability, or target construction is missing/stale;
- any Validation or Final-Test target/path lookup would occur;
- the single barrier set is not frozen before access;
- effective sample or class support is below the frozen floor;
- either fitted-model definition or retained set would change after access;
- implementation requires a new dependency, target, feature, fold, calibration search, or
  budget expansion not approved in the exact task;
- a reviewer finds leakage, hidden multiple testing, or an unresolved contradiction.

A pass would mean only that `PATHFULL001` found incremental TRAIN-only path-order
information beyond the exact volatility/range nuisance benchmark under the one frozen
barrier set. It would not confirm profitability, open Validation, authorize SHORT,
authorize deployment, or justify live trading.

If the primary rule fails, the allowed statement about the full candidate is limited to:

> `PATHFULL001` did not establish incremental usable path-order information beyond the
> fixed volatility/range nuisance benchmark under the exact Test 2 V1 barrier set,
> retained rows, folds, metrics, and cost counterfactual.

The observed nuisance-versus-prior result must be reported separately as a diagnostic. No
null or edge claim about `PATHNUISANCE001` is implied by `PATHFULL001` failure.

It makes no claim about nonlinear models, other barriers, targets, horizons, datasets,
features, regimes, or information sources.

---

## 9. Independent Skeptic / Alpha-Killer review

Before protocol acceptance and before any later target-aware run, an independent written
review and resolution record must challenge at least:

- whether the target is genuinely new rather than post-hoc relabeling;
- barrier economics, first-touch construction, fill limitations, and same-bar ambiguity;
- construct-never-mask-later enforcement and zero Validation/Final-Test lookups;
- path fields leaking into features or selection;
- whether `PATHFULL001` adds information beyond the volatility/range nuisance model;
- dependence, effective sample size, class support, and target-conditioned exclusion;
- metric implementation, including the existing PR-AUC defect;
- cross-test and within-test search-budget accounting;
- cost semantics, missingness, crisis-session loss, and fold stability;
- whether simpler explanations defeat the claimed mechanism.

Codex/Claude agreement is review input only. It does not grant acceptance, execution
authority, evidence status, or merge authority.

---

## 10. Implementation ownership gate

Before any code is written or changed for source loading, target construction, model
training, evaluation, or experiment logging, Codex must stop and ask the Owner:

> Will the Owner implement this package, or does the Owner authorize Codex to implement
> the exact bounded code scope?

No answer may be inferred from approval of this document. If Codex is authorized later,
implementation requires a new exact base SHA, one scoped branch, allowed-file list, test
plan, data-access level, forbidden actions, independent review, and separate run
authorization. Code implementation and target-aware execution are distinct approvals.

---

## 11. Owner decisions required before protocol acceptance

1. Ratify the path-aware first-touch direction and unchanged `LONG / FLAT` action space.
2. Ratify that Stage B execution is not a Test 2 prerequisite.
3. Freeze exactly one take-profit/stop barrier set, economically anchored net of the
   `0.994`-point conservative break-even.
4. Ratify the `AMBIGUOUS_SAME_BAR` fail-closed rule.
5. Ratify the two-evaluation budget: `PATHNUISANCE001` plus `PATHFULL001`, with no GBM.
6. Freeze minimum effects, confidence/block rule, effective-sample floor, class-support
   floor, and the `0 / OPEN` embargo disposition.
7. Ratify the proposed Test 2 lifetime Validation-opening budget of at most one, still
   requiring a separate confirmatory protocol and explicit authorization.
8. Decide whether external Test 1 records remain SHA-observed rationale or enter a separate
   governed evidence-reconciliation package before later champion comparison.
9. Decide implementation ownership before any training-code work.
10. Issue separate explicit L1 authorization before any TRAIN target/path access.

---

## 12. Safety counters at revision 2 draft

```text
protocol authoring access                  L0
new realized TRAIN target/path rows read   0
Validation target/path rows read           0
Final Test target/path rows read           0
models trained                             0
training-code files changed                0
Stage B executions                         0
live/broker actions                        0
```

## Draft verdict

`TEST2_PATH_AWARE_PROTOCOL_V1_REV2_READY_FOR_ADVERSARIAL_REVIEW`

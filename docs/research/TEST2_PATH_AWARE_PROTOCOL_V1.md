# MES Test 2 — Path-Aware LONG/FLAT Protocol V1

**Document status:** `OWNER_ACCEPTED / L0_PROTOCOL_FROZEN`

**Execution status:** `NOT_AUTHORIZED`

**Exploration scope ID:** `MES_TEST2_PATH60_LONG_FLAT_FEATURE29_V1`

**Authoring base:** `793f11aab29148b13c2f41629ffdbd250b4b8d03`

**Authoring branch:** `research/test2-path-protocol-v1`

**Architecture relationship:** Test 1 remains immutable under
`MES_QUANT_TARGET_ARCHITECTURE_v2.2`. This is a bounded Test 2 draft under
`MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT`, with LangGraph retired and research review
remaining human-directed.

This document does not authorize code changes, artifact access, target construction,
model training, Validation, Final Test, production, push, or merge. On `2026-08-22`, the
Owner accepted the Section 11 scientific and statistical package for a docs-only protocol
freeze and checkpoint. That acceptance may not be reused for implementation or a
target-aware run.

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
- outer Validation: unopened, with frozen lifetime opening budget at most `1` and no
  automatic opening from a TRAIN result;
- Final Test: sealed;
- live trading and broker connectivity: disabled.

Observed Stage B V1.2 status is policy `LOCKED` and execution `DISABLED`; full Phase B/C/D
production execution is not implemented. The Owner ratified that Stage B execution and a
reduced feature set are not Test 2 prerequisites. Test 2 does not enable or modify Stage B,
and a Test 2 pass creates no Stage B entitlement.

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
- `WF_2023`: 5,476 rows before feature/target eligibility;
- pooled maximum before eligibility: 10,986 rows.

Cell 13 records descriptive effective sample sizes of approximately `1,290–1,370` per
fold and lag-1 return autocorrelation of approximately `0.756–0.769`. Row count is not an
independent sample size. The exact inherited diagnostic implementation is
`reference/colab_v1_cells_0_13/cell13.py`, SHA-256
`481d96a2689cfbf4bd6e82c51704d78c32437aa1b2fb6afedf5bc6bac699e954`. For ordered rows
within each session it uses exact `15 * lag`-minute pairs at lags `1..3` and computes:

```text
DESIGN_EFFECT = max(1, 1 + 2 * sum(max(rho_lag, 0) for lag in 1..3))
ESS           = N / DESIGN_EFFECT
```

Test 2 must apply that formula separately to `PATH_LONG` and
`gross_move_points_60m` on the exact retained rows, per fold and on the pooled disjoint OOF
holdouts. The governing ESS is the lower of the two ESS values, equivalently the result
from the larger design effect. Pooled ESS must be computed on pooled retained rows and may
not be obtained by summing fold ESS values. This Test 2 adaptation must be labeled
descriptive and may not be confused with the session-block confidence method.

For the `WF_2022` and `WF_2023` OOF boundaries only, the existing 60-minute purge remains
valid; recorded purged rows are `0` because the natural calendar-year gaps exceed the
horizon. The outer TRAIN set ends on `2023-12-29`, before the outer-Validation boundary on
`2024-01-02`; the Final-Test boundary is later on `2025-01-02` and is outside the entire
Test 2 request set. These outer boundaries are enforced by the timestamp-keyed assertions
in Section 4.2, not inferred from the OOF purge count. The Owner ratified
`EMBARGO_MINUTES = 0` for these two boundaries only because their natural calendar gaps
exceed the 60-minute horizon. Before fitting, the implementation must assert and record a
minimum wall-clock boundary gap of at least `60` minutes for both folds. A future fold with
a smaller gap requires a new embargo decision; zero embargo is not a claim of independence.

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

## 5. Frozen path-aware target parameterization

Exactly one barrier parameterization is frozen for Test 2 V1:

```text
ENTRY_PRICE                    entry_reference_close
TAKE_PROFIT_GROSS_POINTS       4.00  (16 ticks)
STOP_GROSS_POINTS              2.00  (8 ticks)
TICK_SIZE_POINTS               0.25
CONSERVATIVE_ROUND_TRIP_COST   0.994 index points / USD 4.97
ONE_MINUTE_BAR_OFFSETS         0..59
```

The favorable gross barrier must exceed the frozen conservative break-even cost:

```text
TAKE_PROFIT_GROSS_POINTS - 0.994 > 0
```

The Owner froze this set before access without observing target prevalence, balance,
ambiguity, support, or performance. It is economically coherent for touched outcomes:

```text
favorable touch net of cost    +4.000 - 0.994 = +3.006 points / USD 15.03
adverse touch net of cost      -2.000 - 0.994 = -2.994 points / USD 14.97
conditional-touch reward:risk   3.006 : 2.994 = 1.004 : 1
```

The `4 / 2` gross set is tick-aligned and is the rounded tick-grid result of the
predeclared design constraints `TP = 2 * SL` and `TP - cost = SL + cost`. The resulting
conditional-on-touch break-even favorable rate is approximately `0.499`; that number is a
diagnostic for the touched subset only. It is not a decision threshold or a profitability
claim because `PATH_LONG = 0` also includes neither-touch outcomes.

All barrier and price comparisons must be performed in integer `0.25`-point ticks. A
floating-point epsilon, sub-tick barrier, or post-access barrier change is forbidden.

For each allowed TRAIN row, process the authorized one-minute OHLC bars chronologically:

- favorable touch: bar high reaches `ENTRY_PRICE + TAKE_PROFIT_GROSS_POINTS`;
- adverse touch: bar low reaches `ENTRY_PRICE - STOP_GROSS_POINTS`;
- `PATH_LONG = 1` only when the favorable barrier is observed first;
- `PATH_LONG = 0` when the adverse barrier is observed first or neither is reached;
- if both barriers are reachable inside the same one-minute OHLC bar before a prior touch,
  the order is unobservable and disposition is `AMBIGUOUS_SAME_BAR`.

The Owner-ratified fail-closed rule for `AMBIGUOUS_SAME_BAR` is: exclude from
fitting/scoring, report under Section 4.4, and map to `FLAT` with zero cost for policy
coverage. Test 2 claims are conditional on the non-ambiguous retained set; no positive or
null claim is made about the ambiguous subpopulation.

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

Both fits reuse the frozen Test 1 numerical logistic policy exactly, except that the input
width must be parameterized to admit the fixed four-feature nuisance model:

```text
loss normalization             mean binary log loss
L2 penalty                     0.5 * 0.001 * ||beta_non_intercept||^2
L2_LAMBDA                      0.001
fold-local standardization     TRAIN mean / population SD (ddof=0)
zero-variance guard            scale = 1.0 and record feature
intercept                      fitted / unpenalized
class weighting                none
inner CV or parameter search   none
maximum Newton iterations      50
gradient infinity tolerance    1e-8
Armijo constant                1e-4
backtracking shrink            0.5
minimum step                   2^-20
non-convergence                hard fail
```

No sklearn-style `C`, alternative penalty, optimizer, solver, or tuning rule may be
substituted. Parameterizing input width is an implementation requirement, not authority to
change code under this protocol acceptance.

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
- ambiguity, missingness, exclusion, and search-budget counters;
- barrier points/ticks, cost, numerical policy, and decision-threshold semantics;
- minimum effects, bootstrap method/block/repetitions/bound/seed, and draw identity;
- both ESS diagnostics, governing ESS, raw/effective class support, and boundary gap;
- release-at-touch primary and fixed-60-minute-capacity sensitivity policy identities.

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

The frozen materiality floors are:

```text
MDE_VS_PRIOR       0.0075 nats
MDE_VS_NUISANCE    0.0075 nats
```

`PATHFULL001` is `INTERESTING_ENOUGH_TO_CONTINUE` only if all are true:

1. pooled and **each** fold `IMPROVEMENT_VS_PRIOR` are strictly greater than `0.0075`;
2. pooled and **each** fold `IMPROVEMENT_VS_NUISANCE` are strictly greater than `0.0075`;
3. the pooled paired session-block one-sided 95% lower confidence bound for both
   improvements is strictly greater than `0`;
4. governing ESS is at least `1,000` in each fold and at least `2,000` when computed on
   pooled retained rows;
5. effective support for **each** target class is at least `200` in each fold, where
   effective class support is raw class count divided by the governing design effect;
6. all source, role, availability, ambiguity, access, and search-budget gates pass.

Equality is not a materiality or confidence pass. Equality meets the ESS/support floor.
Effective events per fitted non-intercept coefficient must be reported; a value below `10`
requires explicit disclosure but cannot rescue or relax any gate.

The confidence method reuses the Cell 13 family: non-circular consecutive-session moving
blocks, `2,000` repetitions, five sessions per primary block, and master seed `20260809`.
Within a replicate, prior, nuisance, and full losses use the same session draws; blocks may
not cross fold boundaries. For a fold containing `N_sessions`, set
`blocks_needed = ceil(N_sessions / block_length)`, sample block-start indices uniformly
with replacement from the inclusive range `0..N_sessions-block_length`, concatenate each
non-circular consecutive block, and truncate the final sampled sequence to exactly the
fold's original `N_sessions`. Never pad, wrap, or drop the remainder.

For each pooled replicate, resample `WF_2022` and `WF_2023` independently to their own
original session counts, then concatenate their sampled session aggregates. For each
model, pooled log loss is the sum of sampled row losses across both folds divided by the
sum of sampled row counts; it is row-weighted and is not the mean of the two fold losses.
The paired improvement is then the sampled pooled baseline loss minus the sampled pooled
`PATHFULL001` loss. Session tables must therefore contain row count and summed prior,
nuisance, and full log loss, and all three use the identical draw indices.

The inherited seed schedule is also frozen. For block length `L`, set
`pooled_seed = 20260809 + 90000 + L`; in fold order `WF_2022`, `WF_2023`, initialize the
fold generators with `pooled_seed + 1000 * (fold_index + 1)`. The primary lower bound is
the fifth percentile of paired loss-improvement replicates. Block lengths `1` and `20` are
required diagnostics only; a sign change at `20` sessions must be disclosed and cannot
itself pass or fail the result. No reseeding, seed search, redraw, or best-of-seeds is
permitted. A demonstrated code repair must reuse the identical seed and be recorded as a
repair.

The `0.0075` floors are conservative materiality rules, not estimated power or guaranteed
detectability. No economic quantity, thresholded P&L, coverage, or USD stress view is a
continuation gate. Diagnostics cannot rescue primary failure.

### 7.3 Diagnostics and economic view

- Brier score and improvement versus both baselines;
- tie-safe ROC-AUC;
- average precision using a correct stepwise estimator, not the known trapezoidal PR-AUC;
- calibration/reliability views;
- target prevalence, probability distribution, and diagnostic action coverage at the
  fixed `0.5` probability threshold; this threshold is not an economic break-even claim;
- per-fold and per-session stability;
- ambiguity, missingness, and `NO_SCORE / FLAT` rates;
- paired five-session block-bootstrap counterfactuals;
- a primary LONG/FLAT counterfactual that exits a scored LONG at the first observable
  favorable/adverse touch and releases capacity at that touch; a neither-touch trade exits
  at offset `59`, reconciled to the Cell 10 `+60m` endpoint;
- a required sensitivity that reserves capacity until the original `+60m` release time
  even when the position touched a barrier earlier;
- `AMBIGUOUS_SAME_BAR` and `NO_SCORE` map to `FLAT`, zero P&L, and zero cost;
- exit-then-entry at the same timestamp follows the existing Cell 13 convention;
- the USD `4.97` conservative round-trip charge applies once per executed trade;
- only predeclared stress values, never used to select a winner.

These are touch-defined current-deployment counterfactuals, not historical fills. A
favorable high does not prove a limit fill and a stop may fill worse after a gap. The
economic views are diagnostics and can neither rescue nor veto the primary information
test.

### 7.4 Cross-test interpretation

Test 1 and Test 2 reuse the same TRAIN years and feature catalog but ask different targets.
All four fitted attempts across the two tests remain visible. Test 2 is exploratory and no
family-wise confirmatory claim is permitted from TRAIN. A Test 2 pass may nominate at most
one exact `PATHFULL001` candidate for one separately frozen confirmatory protocol. The
Owner ratified a lifetime Validation-opening budget of at most `1` over the full Test 2
scope. The budget is consumed when Validation is opened, regardless of the result. A TRAIN
failure leaves it unspent and may not trigger a "check Validation anyway" opening. Opening
remains separately authorized and may not occur automatically.

---

## 8. Stop conditions and bounded interpretation

Stop under the declared disposition below if:

- source identity, role binding, availability, or target construction is missing/stale;
- any Validation or Final-Test target/path lookup would occur;
- the single barrier set is not frozen before access;
- effective sample or class support is below the frozen floor;
- either fitted-model definition or retained set would change after access;
- implementation requires a new dependency, target, feature, fold, calibration search, or
  budget expansion not approved in the exact task;
- a reviewer finds leakage, hidden multiple testing, or an unresolved contradiction.

If governing ESS or class support is below its frozen floor after authorized target
construction, Test 2 V1 terminates before either model fit as
`INCONCLUSIVE_UNDERPOWERED`. The floors may not be relaxed, and the barrier, horizon,
decision grid, retained-set rule, or ambiguity rule may not be changed inside this scope.
Any alternative requires a new `EXPLORATION_SCOPE_ID`, a newly approved search budget, and
an explicit record that Test 2 V1 target-derived support evidence was already observed.
`INCONCLUSIVE_UNDERPOWERED` is neither a model failure nor evidence of edge.

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

Because both fits use one frozen penalty, failure also cannot distinguish absence of
incremental path-order information from insufficient effective sample size to estimate
the additional coefficients under that penalty.

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

The pre-acceptance L0 review rounds, findings, and resolution matrix are recorded in
`docs/research/TEST2_PATH_AWARE_PROTOCOL_V1_REVIEW_RECORD.md`, SHA-256
`f05658314f62c84755077e8b34e3e6c96703d336d5372d1681ab3472160b7b3c`. That record carries
the required final `PASS / NO BLOCKER OR HIGH`. The human Owner's decision remains the
source of acceptance authority.

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

## 11. Owner decision record and remaining gates

The Owner accepted Decisions 1–8 on `2026-08-22`:

1. **FROZEN:** path-aware first-touch direction and unchanged `LONG / FLAT` action space.
2. **FROZEN:** Stage B execution is not a Test 2 prerequisite.
3. **FROZEN:** one `4.00`-point take-profit / `2.00`-point stop barrier set.
4. **FROZEN:** `AMBIGUOUS_SAME_BAR` fail-closed rule.
5. **FROZEN:** exactly `PATHNUISANCE001` plus `PATHFULL001`, with no GBM, parameter search,
   or third fit.
6. **FROZEN:** `0.0075` materiality floors, Cell 13 session-block confidence family,
   governing ESS and class-support floors, and boundary-specific zero embargo.
7. **FROZEN:** Test 2 lifetime Validation-opening budget of at most one, still requiring a
   separately frozen confirmatory protocol and explicit authorization.
8. **FROZEN:** external Test 1 records remain SHA-observed rationale only. They may not be
   copied into Git, rerun under old identities, or used as release/champion evidence. The
   access-record and PR-AUC defects in Section 2 remain forward-remediation preconditions.

The remaining gates are intentionally open and separate from protocol acceptance:

9. **OWNER_DECISION_REQUIRED:** implementation ownership before any source-loader, target,
   training, evaluation, or experiment-record code work.
10. **SEPARATE_EXPLICIT_L1_AUTHORIZATION_REQUIRED:** before any TRAIN target/path access.

---

## 12. Safety counters at protocol freeze

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

## Protocol verdict

`TEST2_PATH_AWARE_PROTOCOL_V1_OWNER_ACCEPTED_FROZEN`

`IMPLEMENTATION_NOT_AUTHORIZED / L1_NOT_AUTHORIZED / EXECUTION_NOT_AUTHORIZED`

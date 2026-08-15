# EDGE_DISCOVERY_SPRINT_1_PROTOCOL

## Authority and scope

- GitHub authority: Issue #22.
- Baseline: `ed2980c7fc50cf936494e6f750bbea8d0d78926a`.
- Architecture: `MES_QUANT_TARGET_ARCHITECTURE_v2.2`, unchanged.
- Exploratory Lane V1 charter: accepted and frozen on baseline.
- Protocol-authoring observed access: `L0`.
- Sprint 1 run status at protocol freeze: `NOT STARTED`.

This protocol freezes the Sprint 1 research decisions before any new realized TRAIN-label access. It does not itself open L1, Validation, Final Test, P&L, or future-return rows.

## 1. Exploration scope

`EXPLORATION_SCOPE_ID = MES_V1_EDGE_SPRINT_1_LOCKED29_LONG_FLAT_60M`

Sprint 1 is limited to:

- MES only;
- 15-minute decision grid;
- +60-minute horizon;
- canonical locked Cell 14 V1 feature universe only;
- TRAIN partition only;
- V1 action interpretation: `LONG` or `FLAT`;
- no new feature engineering, macro inputs, regime layer, or external data expansion.

Sprint 1 research target mapping:

```text
Cell 10 LONG      -> 1
Cell 10 SHORT     -> 0
Cell 10 NO_TRADE  -> 0
```

This mapping is Sprint-1 research authority only. It does not rewrite the historical Cell 10 artifact.

## 2. Frozen cost assumption

Use the existing Cell 10 primary `CONSERVATIVE` round-trip cost assumption:

```text
round_trip_cost_usd        4.97
break_even_index_points    0.994
MES_multiplier_usd_point   5.0
```

The cost assumption may not be changed after Sprint results are observed. A different cost assumption requires a new governed experiment/scope path.

## 3. Required baselines

### ALWAYS_FLAT

Action/economic baseline: never enter a long position.

### TRAIN_PRIOR_PROBABILITY

Probabilistic baseline: estimate long-label prevalence from the training side of each fold only and predict that constant probability on the corresponding holdout.

No full-TRAIN or holdout prevalence may influence a holdout prediction.

## 4. Allowed candidate families

Sprint 1 is intentionally simple and bounded. Allowed families are:

1. regularized logistic regression;
2. shallow tree model or tightly bounded shallow tree ensemble;
3. predeclared univariate or small-feature rules using only existing locked features.

Not allowed in Sprint 1:

- HMM;
- GARCH;
- deep learning;
- stacking/blending;
- large model zoo;
- macro/regime model;
- external feature expansion.

All preprocessing, state fitting, and model fitting must occur only inside the training side of each time split.

## 5. Evaluation structure

Use time-ordered out-of-fold evaluation entirely inside TRAIN. Random-shuffle cross-validation is forbidden.

Prefer the strongest existing purged/time-aware TRAIN fold structure already present in the repository if compatible with the +60-minute horizon. If an inner TRAIN-only split must be introduced, it must preserve chronology and purge overlapping +60-minute targets at split boundaries without consulting Validation.

Each Sprint result must report:

- `N_raw`;
- `N_sessions`;
- horizon = `60m`;
- decision spacing = `15m`;
- overlap scale = approximately `4` layers, explicitly labeled a heuristic rather than proven ESS;
- fold boundaries;
- train/holdout row counts by fold.

## 6. One primary decision metric

The sole Sprint continuation metric is:

`OOF_BINARY_LOG_LOSS`

Lower is better.

Define:

```text
LOG_LOSS_IMPROVEMENT = baseline_oof_log_loss - candidate_oof_log_loss
```

where the baseline is the fold-correct `TRAIN_PRIOR_PROBABILITY` baseline.

Positive improvement is better. The primary metric cannot be replaced after results are seen within Sprint 1.

## 7. Diagnostic metrics

Record at minimum:

- Brier score and improvement versus prior baseline;
- ROC-AUC;
- PR-AUC;
- calibration/reliability summary;
- predicted-long rate / action coverage under any diagnostic rule;
- per-fold log loss and per-fold improvement;
- TRAIN-only session/year stability views where available;
- ALWAYS_FLAT economic reference statistics when computable from authorized TRAIN-only evidence.

Diagnostics do not decide Sprint continuation and cannot rescue failure of the primary criterion.

## 8. Interesting-enough continuation criterion

Sprint 1 is `INTERESTING_ENOUGH_TO_CONTINUE` only if at least one allowed simple candidate satisfies both:

1. overall `LOG_LOSS_IMPROVEMENT > 0`; and
2. median per-fold `LOG_LOSS_IMPROVEMENT > 0`.

Equality to zero is not a pass. No post-result epsilon or threshold adjustment is allowed.

Passing means only that the current TRAIN scope contains enough predictive structure to justify a separately frozen confirmatory hypothesis and Validation protocol. It is not evidence of live profitability or release readiness.

## 9. Current-scope no-edge criterion

If no allowed Sprint-1 candidate satisfies the frozen continuation criterion, the Sprint disposition is:

`NO_USABLE_EDGE_IDENTIFIED_IN_SPRINT_1_SCOPE`

This conclusion is limited to the current scope: locked 29-feature universe, MES 15m/+60m, Long/Flat mapping, allowed simple model families, TRAIN period, and frozen target/cost assumptions. It does not establish that MES has no edge outside this scope.

## 10. Experiment governance

Every realized-label-accessing execution after protocol acceptance is a `TARGET_AWARE_EXPERIMENT` and requires a unique `EXPERIMENT_ID` before the run.

Minimum experiment history fields:

- `EXPERIMENT_ID`;
- UTC timestamp;
- `EXPLORATION_SCOPE_ID`;
- hypothesis/rule;
- feature subset;
- target mapping/version;
- cost assumption reference;
- model family;
- parameters / bounded search space;
- fold/split definition;
- primary metric;
- diagnostics;
- result;
- disposition;
- code/commit identity where available.

Repeated TRAIN exploration is permitted only inside this frozen scope and must remain logged. Exploratory results have no Release-Gate authority.

## 11. Information-access boundary during Sprint 1

After explicit Sprint-run authorization:

```text
TRAIN realized labels     ALLOWED / L1
Validation outcomes       FORBIDDEN / L2 UNOPENED
Final Test                FORBIDDEN / L3 SEALED
canonical upstream data   READ-ONLY
```

Before any L2 opening, the confirmatory hypothesis and Validation protocol must be frozen separately.

## 12. Protocol freeze rule

This protocol is frozen through Sprint 1. Changing the scope, target mapping, primary metric, cost assumption, continuation criterion, or allowed model families after seeing Sprint results creates a new governed path rather than rewriting this protocol.

No Exploratory Lane V2 may be opened before Sprint 1 has actually run.

## Safety counters at protocol creation

```text
OBSERVED_ACCESS_LEVEL_FOR_PROTOCOL_WORK  L0
new realized TRAIN label rows opened     0
Validation outcome rows opened           0
Final Test rows/outcomes opened           0
Sprint 1 experiment runs                  0
real Stage B production runs              0
```

## Final verdict

`EDGE_DISCOVERY_SPRINT_1_PROTOCOL_READY_FOR_OWNER_REVIEW`

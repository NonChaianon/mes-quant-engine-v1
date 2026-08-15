# EDGE DISCOVERY SPRINT 1 — SEARCH BUDGET ADDENDUM

## Status and authority

- Governing issue: GitHub Issue #29.
- Baseline before this addendum: `e797c0bf816c17348698a9dd4c3eca98e07e292f`.
- Governing Sprint protocol remains `docs/research/EDGE_DISCOVERY_SPRINT_1_PROTOCOL.md`.
- Exploratory Lane V1 charter remains unchanged.
- This addendum is created **after LR001 completed** and **before any real TREE001 target access**.
- Validation outcomes remain **UNOPENED**.
- Final Test remains **SEALED**.

This document narrows the remaining Sprint-1 search budget. It does not rewrite the historical Sprint-1 protocol and must not be represented as having existed before LR001.

## 1. Why this addendum exists

The frozen Sprint-1 protocol permits more than one simple candidate family. Repeated target-aware evaluation on the same TRAIN-only OOF structure creates accumulated multiple-comparison / look-elsewhere risk: the more candidate families are tried, the greater the chance that at least one appears to pass by chance.

Sprint-1 exploratory success is not confirmatory evidence, and untouched Validation remains the required confirmatory boundary. Even so, the exploratory search itself should be kept intentionally small so that a later Validation opening is not spent on a winner produced mainly by repeated search.

This addendum therefore places a conservative cap on remaining Sprint-1 target-aware candidate search.

## 2. Timing and observed history

At the moment this addendum is authored:

- `LR001` has already executed against authorized TRAIN-only realized labels.
- `LR001` failed the frozen continuation criterion.
- `TREE001` has already been specified in Issue #28 as a distinct bounded shallow-tree family.
- `TREE001` has **not** executed on real Cell10 labels.
- No 2024 Validation outcome has been opened.
- Final Test remains sealed.

The search-budget restriction is therefore a conservative post-LR001 scope reduction, not a pre-LR001 rule retroactively inserted into history.

## 3. Frozen Sprint-1 target-aware candidate budget

The total permitted real target-aware candidate executions in Sprint 1 are capped at exactly **2**:

1. `LR001` — `REGULARIZED_LOGISTIC_REGRESSION` — completed / failed.
2. `TREE001` — `BOUNDED_SHALLOW_DECISION_TREE` — final permitted Sprint-1 candidate.

After TREE001, no additional Sprint-1 target-aware candidate may execute.

Forbidden after TREE001 includes, without limitation:

- `TREE002`;
- shallow-tree ensemble follow-up;
- altered depth / leaf-size / threshold versions;
- `SMALL_FEATURE_RULE` candidate;
- additional logistic variants;
- feature-subset search;
- any other model-family substitution inside Sprint 1.

## 4. Why the cap is 2 rather than 1

TREE001 is retained as one final candidate because it asks a materially different, already-permitted simple-model question from LR001.

LR001 asks:

> Can a single regularized linear-logit surface over the locked29 feature universe identify stable TRAIN-only predictive structure beyond the fold-correct prior?

TREE001 asks:

> Can a very shallow nonlinear partition of the same locked29 feature universe identify stable TRAIN-only predictive structure that a single linear-logit surface cannot represent?

This distinction is functional rather than cosmetic. TREE001 is not a retune of LR001 and may not modify LR001 parameters, feature universe, target mapping, folds, primary metric, or continuation rule.

One nonlinear candidate is therefore retained as a bounded complementary test, while the overall search remains deliberately small.

## 5. Intentional exclusion of SMALL_FEATURE_RULE

The original Sprint-1 protocol also permits predeclared univariate or small-feature rules.

This addendum intentionally chooses **not** to exercise that permission after LR001 failure.

Sprint 1 will not run a `SMALL_FEATURE_RULE` target-aware candidate after TREE001. This is a deliberate reduction of the search space to limit accumulated search degrees of freedom and false-positive risk. It is not an accidental omission, missing implementation, or statement that the small-feature-rule family has been tested.

If TREE001 fails, Sprint 1 ends without evaluating that third permitted family.

## 6. Interpretation if TREE001 passes

TREE001 passes only if the unchanged Sprint-1 continuation rule is satisfied:

1. overall `LOG_LOSS_IMPROVEMENT > 0`; and
2. median per-fold `LOG_LOSS_IMPROVEMENT > 0`.

If TREE001 passes:

- do not claim a confirmed edge;
- do not execute another Sprint-1 candidate;
- do not tune TREE001 after seeing the result;
- freeze exactly one confirmatory hypothesis;
- freeze the Validation protocol and permitted information budget separately;
- open Validation only under separate explicit owner authorization.

A TREE001 pass means only that TRAIN-only exploration produced one candidate worth confirmatory testing.

## 7. Interpretation if TREE001 fails

If TREE001 fails the frozen continuation criterion, Sprint 1 closes with:

`NO_USABLE_EDGE_IDENTIFIED_IN_TESTED_SPRINT_1_SCOPE`

This statement is intentionally narrower than a project-wide no-edge claim.

It applies only to the tested search path:

- MES;
- 15-minute decision grid;
- +60-minute horizon;
- locked29 Cell14 feature universe;
- frozen Long/Flat target mapping;
- frozen Sprint cost and primary metric assumptions;
- TRAIN-only period;
- LR001 linear-logit family;
- TREE001 bounded shallow nonlinear-tree family.

It does not claim that MES has no edge generally and does not claim that `SMALL_FEATURE_RULE` was tested.

## 8. Diagnostic dimensions must remain distinct

Target-aware experiment records should distinguish at least four diagnostic dimensions:

1. **Discrimination / ranking** — e.g. ROC-AUC and PR-AUC.
2. **Probabilistic calibration / reliability** — e.g. Brier score and calibration bins.
3. **Thresholded action coverage** — e.g. predicted-long rate at the predeclared `p >= 0.5` diagnostic threshold.
4. **Temporal / fold stability** — comparison of the above across authorized TRAIN-only folds.

Coverage at one threshold is not itself a calibration metric.

## 9. LR001 diagnostic clarification

The persisted LR001 evidence supports the following observations:

- pooled discrimination was approximately random;
- fold-level ranking behavior differed between WF_2022 and WF_2023;
- the distribution of predictions around the `p >= 0.5` diagnostic threshold changed materially across those folds;
- the optimizer converged normally and is not identified as the cause of LR001 failure.

The project therefore records LR001 as exhibiting temporal instability in predictive ranking and predicted-probability distribution.

The project does **not** claim that LR001 coefficients themselves were unstable, because per-fold coefficient vectors were not persisted in the immutable LR001 experiment record.

LR001 must not be silently rerun under the same experiment ID to backfill coefficients. Any later coefficient-recovery analysis that reads realized TRAIN labels requires a separately governed target-aware diagnostic identity and may not rewrite LR001 history.

## 10. TREE001 model-structure persistence

TREE001 must persist sufficient fold-local fitted structure in its immutable experiment record for later temporal-stability comparison, including at minimum:

- selected feature index and canonical feature name for every split;
- split threshold;
- quantile candidate identity/order where applicable;
- split improvement;
- root-fold TRAIN count used for the minimum-child rule;
- child row counts;
- terminal leaf row counts;
- terminal leaf long counts;
- terminal leaf probabilities;
- resulting fold tree structure.

These are TRAIN-only model diagnostics and do not authorize Validation or Final-Test access.

## 11. WF_2024 clarification

Sprint-1 target-aware candidates use only `WF_2022` and `WF_2023` OOF holdouts because `WF_2024` holdout corresponds to outer Validation year 2024.

Using the `WF_2024` TRAIN-side history in a target-blind Stage-B analysis is a different access pattern from opening the `WF_2024` realized holdout outcomes in target-aware exploration.

This addendum does not change the existing fold boundary:

- `WF_2022` target-aware holdout: allowed inside outer TRAIN;
- `WF_2023` target-aware holdout: allowed inside outer TRAIN;
- `WF_2024` target-aware holdout: forbidden because it would open outer Validation.

The two authorized OOF holdouts provide limited temporal replication and must not be described as three independent folds or as full independent-sample evidence.

## 12. Access boundary

The existing boundary is unchanged:

```text
TRAIN realized labels     ALLOWED only for an explicitly authorized target-aware run
TRAIN features            ALLOWED
Validation outcomes       FORBIDDEN / L2 UNOPENED
Final Test                FORBIDDEN / L3 SEALED
canonical upstream        READ-ONLY
```

No gross-P&L, future-return, Validation, or Final-Test access is authorized by this addendum.

## 13. Governance sequence after merge

After this addendum is reviewed and merged:

1. implement TREE001 from its already-frozen Issue #28 specification;
2. use synthetic tests first;
3. review code and obtain green CI;
4. merge TREE001 implementation only with separate owner authorization;
5. run canonical preflight;
6. execute TREE001 on real TRAIN labels only with separate explicit authorization;
7. stop Sprint-1 target-aware candidate search permanently after TREE001, regardless of pass or fail.

`SPRINT_1_SEARCH_BUDGET_ADDENDUM_READY_FOR_REVIEW`

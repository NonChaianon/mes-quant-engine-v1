# EXPLORATORY LANE V1 — TRAIN-Only Edge Discovery Charter

## Status and authority

- Architecture authority: `MES_QUANT_TARGET_ARCHITECTURE_v2.2`
- Governance authority: GitHub Issue #20
- Baseline: `1c6512615a40dbc35a394ed241fde30d18b5dede`
- A6 / Stage B V1.2: `LOCKED`
- Stage-B artifact execution: `DISABLED`
- Final Test: `SEALED`
- Charter version: `EXPLORATORY_LANE_V1`

This charter defines the minimum governance boundary for TRAIN-only exploratory edge discovery. It does not itself open realized labels or authorize Sprint 1 execution.

## Purpose

Answer quickly and honestly whether the current predefined research scope contains empirical structure worth carrying into confirmatory research.

Exploration is allowed to be lightweight and disposable. It is not allowed to consume clean Validation or Final-Test evidence, silently mutate canonical upstream artifacts, or present exploratory findings as production/release evidence.

## Access boundary

When a later experiment is explicitly authorized under this lane:

```text
TRAIN data / TRAIN realized labels     ALLOWED — L1
Validation labels / outcomes           FORBIDDEN — L2 UNOPENED
Final Test                              FORBIDDEN — L3 SEALED
P&L / execution outcomes outside
approved experiment definition         FORBIDDEN
```

Any run that observes realized TRAIN labels is automatically `TARGET_AWARE_EXPERIMENT`. Human naming cannot downgrade such a run to governance work or target-blind work.

Creating or reviewing this charter remains L0; L1 begins only when an explicitly authorized experiment actually reads realized TRAIN labels.

## Experiment identity and search-history record

Every label-accessing run must have a unique `EXPERIMENT_ID` before label access. At minimum, the search-history record must preserve:

- `EXPERIMENT_ID`;
- run timestamp;
- hypothesis / trading rule being tested;
- feature set or feature-family reference;
- target-contract reference;
- cost-assumption reference;
- model / method / edge family;
- material parameters;
- predeclared primary metric used by the governing Sprint protocol;
- diagnostic metrics actually inspected;
- result and disposition: continue / reject / reformulate / inconclusive.

The record exists to preserve the real search path. Failed experiments are not deleted from history merely because they are uninteresting.

## Allowed exploration behavior

- TRAIN-only feature/label analysis under the accepted Sprint protocol.
- Simple statistical or model baselines before unnecessary complexity.
- Disposable notebooks/scripts and temporary analysis artifacts.
- Reformulation of hypotheses inside TRAIN, provided the experiment history records the change.
- Diagnostic analysis needed to understand TRAIN behavior, subject to the Sprint protocol and access boundary.

Exploration code does not need production-quality interfaces or full production governance. That exception applies only to disposable exploration code; it does not weaken locked upstream contracts or data boundaries.

## Prohibited behavior

- Opening or using Validation outcomes during Exploratory Lane V1.
- Opening Final Test for any exploratory purpose.
- Tuning, feature selection, threshold selection, model selection, or narrative selection using Validation or Final Test.
- Silently modifying canonical A1/A2/A5/A6 artifacts or locked Stage-B policy.
- Rewriting or deleting experiment history after seeing results.
- Treating exploratory metrics, backtests, or P&L as Release-Gate authority.
- Claiming a project-wide absence of edge from a scope-limited negative Sprint result.
- Creating `EXPLORATORY_LANE_V2` before Sprint 1 has actually run.

## Canonical-artifact rule

Canonical upstream artifacts are read-only inputs to exploration unless a separately governed defect/version-bump process explicitly reopens them. Disposable derived artifacts must be clearly separated from canonical inputs and must not overwrite them.

## Relationship to Sprint 1 protocol

This charter intentionally does **not** choose the Sprint 1 numerical decision rule. Before Sprint 1 begins, a separate frozen protocol must define at least:

- `EXPLORATION_SCOPE_ID`;
- continuation / falsification policy;
- baseline(s), including `ALWAYS_FLAT`;
- exactly one primary decision metric;
- diagnostic secondary metrics;
- frozen cost assumption;
- predeclared `interesting-enough` continuation criterion;
- current-scope no-edge criterion.

Metrics or decision criteria may not be changed after results are seen and still be called the same experiment/hypothesis path.

## Confirmatory boundary

Exploratory results have no Release-Gate authority. Before any L2 Validation opening:

1. freeze the confirmatory hypothesis;
2. freeze the validation protocol and permitted information to inspect;
3. pre-register the Validation-opening budget under the applicable governance.

A failed confirmatory hypothesis may not be tuned on the same Validation result and then represented as unchanged.

## Scope-limited negative conclusion

If Sprint 1 finds no usable edge, the strongest allowed conclusion is limited to the predefined scope. A valid formulation is:

> No usable edge was identified within the predefined exploration scope using the current feature universe, selected edge families, MES 15-minute decision grid, +60-minute target framework, and frozen Sprint cost assumptions.

This does not establish that MES has no edge outside the tested scope.

## Freeze rule

After acceptance/merge, this charter is frozen through Sprint 1. If a material charter rule must change after Sprint results are observed, preserve this V1 record and create a new governed path rather than editing history in place.

## Current safety counters for Issue #20

```text
OBSERVED_ACCESS_LEVEL_FOR_CHARTER_WORK   L0
new realized TRAIN label rows opened     0
Validation outcome rows opened           0
Final Test rows/outcomes opened           0
real Stage B production runs              0
Sprint 1 experiment runs                  0
```

## Exit gate

Acceptance of this charter permits only the **next governance step**: freeze the Edge Discovery Sprint 1 protocol. It does not yet authorize L1 access or Sprint execution.

`EXPLORATORY_LANE_V1_CHARTER_READY_FOR_OWNER_REVIEW`

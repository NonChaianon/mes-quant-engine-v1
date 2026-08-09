# Stage B — Feature redundancy and stability contract

Policy status: **PROVISIONAL — lock this contract before producing Stage B artifacts**  
Upstream status: **Cell 14 computation/data artifact LOCKED; candidate catalog PROVISIONAL**

## Objective

Reduce the 29 Cell 14 candidates to a small, stable, explainable set without using Final Test,
without selecting on outer-validation outcomes, and without silently filling missing values. This
stage diagnoses redundancy and stability; it does not declare a profitable model.

## Allowed inputs

- Canonical Cell 14 Development feature artifact, content SHA256
  `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`.
- Cell 8 fold roles for `WF_2022`, `WF_2023`, and `WF_2024`.

Cells 9–13, every label/P&L/cost/path field, every 2025–2026 outcome/feature, and any full-period
statistic are forbidden inputs. Stage B is target-blind. Label-aware incremental value begins only
after the candidate mask freezes and belongs to Stage C.

## Missingness policy

- Full-29 complete cases are an availability diagnostic, not yet the sole modeling cohort. Current
  coverage is `30,197 / 31,193 = 96.807%`, but missingness is strongly non-random.
- Report excluded rows by year, partition, fold, feature, and missing reason before computing any
  association statistic. Missingness is concentrated in early history and is not MCAR.
- A shorter-lookback coverage sensitivity may be reported, but it must not be chosen using target
  performance. Predeclare the compared feature cohorts before inspecting redundancy results.
- Lock a common-cohort and operational fallback policy before correlation analysis. In later
  economic evaluation, every unusable/no-score decision must map to FLAT/zero P&L and remain in
  full-universe coverage metrics; it must not silently disappear.
- Median fill, forward fill, pooled scaling, and missingness learned from future periods are
  **REJECTED**. Any future imputation proposal requires its own point-in-time contract and
  training-fold-only fit.

## Train-only procedure

Run each analysis separately inside the training history of the three expanding walk-forward
folds. Outer-validation rows are reporting-only and cannot choose thresholds, representatives,
hyperparameters, or feature count.

1. Build coverage and distribution diagnostics on each fold's TRAIN rows.
2. Create a semantic-dependency ledger before empirical correlations. Resolve exact algebraic,
   dummy, and rank identities at tolerance `<= 1e-12` separately for linear and tree branches.
3. Compute Pearson and Spearman matrices plus pairwise sample counts on TRAIN rows.
4. Use absolute Spearman distance `1 - |rho|` for hierarchical clustering. PCA may be reported as
   a diagnostic only and must not become a production transform in this stage.
5. Proposed `HARD_REDUNDANCY`: both `|Pearson| >= 0.95` and `|Spearman| >= 0.95` in every TRAIN
   fold, or an exact semantic identity. Proposed `REVIEW`: either metric reaches `0.90` in any TRAIN
   fold. `REVIEW` never causes an automatic drop. Freeze thresholds before execution.
6. Choose a label-free cluster representative by this fixed priority: higher causal availability,
   shorter/simple formula, stability across folds, then lexical feature name as deterministic
   tie-break. Do not use label association, validation AUC, or P&L for this choice.
7. Audit distribution/availability stability within TRAIN history by year and rolling window.
   VIF/condition number applies only to the linear branch. Freeze the Stage B candidate mask and
   reasons before Stage C opens labels.

Known semantic checks that the implementation must reproduce:

- `momentum_log_60m` equals the sum of return lags 0–3 within floating tolerance.
- `minutes_to_horizon_safe_close` is exactly determined by minutes since open and early-close flag.
- weekday dummies sum to one; a linear model with intercept must drop a reference weekday.
- slot sine/cosine lie on the unit circle and are a paired representation.
- lag-0 close return and current-bar log body are empirically near-identical in every TRAIN fold.
- the two volume ratios require review, not automatic deletion: Pearson is high but Spearman is not.

## Required artifacts

- `stage_b_feature_coverage_v1.csv`
- `stage_b_semantic_dependency_ledger_v1.csv`
- `stage_b_fold_correlations_v1.parquet`
- `stage_b_redundancy_clusters_v1.csv`
- `stage_b_feature_decision_registry_v1.csv`
- `stage_b_redundancy_audit.json`

The decision registry must mark every candidate `KEEP`, `DROP_REDUNDANT`, or `OPEN`, name its
cluster/representative, and record a human-readable reason. No artifact may overwrite Cell 14.

## Acceptance gates

- Exact Cell 14 release/control hashes pass before reading features.
- Exactly three expanding TRAIN scopes are analyzed; outer-validation values never affect choices.
- Final Test rows and outcomes opened = `0`.
- No target column or Cells 9–13 artifact enters any Stage B input.
- Deterministic row order, seeds, thresholds, clusters, decisions, and hashes.
- Coverage and missingness reported before empirical redundancy choices.
- Correlation/cluster results are stable enough to explain every retained/dropped candidate.
- An independent audit reproduces the selected set and all artifact hashes.

## Implementation handoff

Create the locked constants/config first in `src/mes_quant/redundancy/contract.py`, then pure
calculations in `src/mes_quant/redundancy/analyzer.py`, thin orchestration in
`src/mes_quant/pipelines/redundancy_pipeline.py`, and tests in `tests/test_redundancy.py`.
Do not add a new monolithic Colab cell.

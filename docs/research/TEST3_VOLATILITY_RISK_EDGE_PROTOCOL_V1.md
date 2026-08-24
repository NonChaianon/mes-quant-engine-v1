# Test 3 Volatility-First / Risk Edge Protocol V1

Protocol ID: `MES_TEST3_RV60_HAR_RISK_EDGE_V1`

Status: **DRAFT COMPLETE — OWNER RATIFICATION REQUIRED**

Lane: exploratory, outer-TRAIN only

Base commit: `fe10fb1497e5df919702cf4ff294c4ebf8669b95`

This document freezes the proposed Test 3 scientific question and execution boundary. It
does not authorize implementation, numeric target access, a real fit, outer Validation, or
Final Test. The Owner must ratify this document and separately authorize each later gate.

## 1. Scientific question and claim boundary

Test 3 asks one narrow question:

> Does 120/240-minute volatility memory improve the next-60-minute realized-variance
> forecast beyond a 60-minute volatility state plus one deterministic intraday harmonic?

The null and alternative are:

```text
H0: RVHAR001 does not improve OOF QLIKE relative to RVBASE001.
H1: RVHAR001 improves OOF QLIKE relative to RVBASE001 by the frozen gates in Section 11.
```

The possible claim is **Risk Edge only**: conditional variance forecast quality on the two
outer-TRAIN walk-forward holdouts. Test 3 makes no directional, execution, trading, P&L,
Sharpe, portfolio, production, or live-deployment claim.

The hypothesis budget is one instrument, one target, one horizon, one sampling rule, one
baseline, one challenger, two folds, and exactly four real fits. No rescue hypothesis is
available after target-aware access.

The project search ledger records Test 3 as `TARGET_SPACE_003`, the third and final
OHLCV-only target-space hypothesis. Ratification of this protocol must co-ratify the
companion `TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md`; neither document grants execution
authority by itself.

## 2. Frozen upstream identities

Later authorized execution must bind all of these identities before any numeric target
lookup:

```text
instrument                         CME Micro E-mini S&P 500 futures (MES)
canonical source                   Databento GLBX.MDP3 / ohlcv-1m
raw DBN SHA-256                    49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0
decoded mes_1m content SHA-256     e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584
decoded row count                  2,551,123
Cell 8 split-assignment SHA-256    2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035
Cell 10 label SHA-256              1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0
Cell 12 path-outcome SHA-256       8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941
Cell 14 feature-file SHA-256       aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452
Cell 14 ordered-feature SHA-256    dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d
```

No new data purchase is required. Test 3 does require a new variance-label contract and
new bounded research code after separate Owner authorization.

## 3. Partition and access inheritance

Test 3 inherits the existing partition map without reinterpretation:

- outer `TRAIN`: through 2023; the only partition eligible for target construction or fit;
- outer `VALIDATION`: calendar 2024; unopened, lifetime opening budget remains at most one;
- `FINAL_TEST`: 2025-01-02 through 2026-07-31; sealed;
- live trading and broker connectivity: disabled.

The decoded one-minute frame physically spans all partitions. A future target builder must
therefore construct and seal an ordered request-key set from outer-TRAIN parent decisions
before any numeric lookup. It must use the Test 2 firewall rules:

1. bind the exact Cell 8 assignment identity;
2. admit outer-TRAIN parents only;
3. create keys `(decision_identity, minute_offset, requested_timestamp_utc)` for offsets
   `0..59`;
4. require `requested_timestamp_utc = decision_time + minute_offset`;
5. hash and persist the ordered request-key set before provider access;
6. assert Validation and Final-Test request counts are both zero before provider access;
7. read only the requested TRAIN keys.

Masking a Validation or Final-Test target after construction is forbidden. No Test 3 result
automatically opens either protected partition.

## 4. Forward realized-variance target

For a decision at timestamp `t`:

- `p_0` is the frozen Cell 10 `entry_reference_close`, the completed 15-minute close
  available at `t`;
- `c_j` is the close of the decoded one-minute bar indexed `t + j minutes`, for
  `j = 0..59`;
- the bar indexed `t` is the first one-minute interval after the decision reference;
- Cell 12 establishes that `c_59` is the `t+60m` endpoint close.

Define exactly 60 strictly post-decision one-minute log returns:

```text
r_0 = ln(c_0 / p_0)
r_j = ln(c_j / c_(j-1))                  for j = 1..59
RV_FWD_60(t) = sum(r_j^2 for j = 0..59)
Y(t) = ln(RV_FWD_60(t))
label_end_time = t + 60 minutes
```

One target-status record must exist for every outer-TRAIN parent decision. A usable target
requires:

- exactly 60 present one-minute bars at offsets `0..59`;
- positive, finite `p_0` and closes;
- the same native instrument throughout the path;
- `c_59` exactly equal to the frozen Cell 10 `+60m` endpoint;
- finite `RV_FWD_60(t) > 0`.

A target satisfying every requirement above must emit `TARGET_USABLE`.

A missing path bar or missing reference must emit `TARGET_UNUSABLE` for the later common
mask; it does not permit imputation or a shortened window. Instrument mismatch, endpoint
mismatch, duplicate key, unordered key, nonpositive price, or nonfinite arithmetic fails
closed immediately as a contract defect; unlike `TARGET_ZERO_VARIANCE`, those defects do
not require completion of the remaining target ledger. No epsilon floor, winsorization,
annualization, square root, jump-robust replacement, or alternate sampling rule is allowed.

A finite `RV_FWD_60(t) == 0` must emit the exact reason code
`TARGET_ZERO_VARIANCE` and stop the entire run before common eligibility or any fit. It may
not be excluded, floored, or converted into a positive target.

The builder must not abort at the first `TARGET_ZERO_VARIANCE`. It must complete and seal
the target-status ledger for every key in the already authorized outer-TRAIN request set,
then halt before common eligibility, fit permits, forecasts, or scientific evaluation.

Cell 12 reconciliation must be exact for every row for which the corresponding Cell 12
path is present. Target construction must record counts and hashes before any model
eligibility mask is applied.

## 5. Frozen predictors and common eligibility

Before any target request set is opened against the decoded one-minute provider, a separate
Owner-authorized **G2-P target-blind predictor-domain preflight** must read only the three
pinned Cell 14 volatility columns for outer-TRAIN rows. It must bind the Cell 8/14
identities, distinguish declared Cell 14 missingness from present values, and seal a complete
status ledger without reading or constructing any target. Its persisted output contains
status counts and ordered identity/status hashes, not raw predictor values or distributions.

Declared missing values must emit `PREDICTOR_UNUSABLE` for the later common mask. A
present nonfinite value emits `PREDICTOR_NONFINITE`; a present finite value less than or
equal to zero emits `PREDICTOR_NONPOSITIVE`. Those two failure codes halt before
target-aware access, so they do not consume `TARGET_SPACE_003`. A later source/ledger
mismatch fails closed as `INVALID_EVIDENCE`; it is repair-eligible only if synthetic
evidence proves implementation nonconformance under the companion budget.

A present finite positive value must emit `PREDICTOR_USABLE`.

The volatility predictors reuse only these exact pinned Cell 14 values:

```text
V60(t)  = realized_vol_60m(t)^2
V120(t) = realized_vol_120m(t)^2
V240(t) = realized_vol_240m(t)^2
X60(t)  = 2 * ln(realized_vol_60m(t))
X120(t) = 2 * ln(realized_vol_120m(t))
X240(t) = 2 * ln(realized_vol_240m(t))
```

`V60/V120/V240` document the variance-scale meaning only. The actual ordered model design
uses `X60/X120/X240` exactly as specified in Section 7.

Cell 14 defines each `realized_vol_Hm` as the square root of the sum of squared completed
15-minute log returns over the fixed `H`-minute lookback. Using a 15-minute realized-state
predictor for a one-minute-sampled future target is deliberate: the hypothesis is whether
coarse, already-locked volatility memory adds forward risk information. Test 3 does not
claim the predictor and target are identical estimators.

The G2-P status ledger governs these three exact predictor columns. A row may not be
dropped, floored, or imputed after inspection except for the predeclared common-mask
exclusion of `PREDICTOR_UNUSABLE`. The global Cell 14 `feature_row_usable` flag may not
exclude a row merely because an unrelated one of the 29 candidates is missing.

Baseline and challenger use one identical common eligible set, defined only after:

1. the complete outer-TRAIN request set and target-status ledger are sealed;
2. target and exact predictor statuses are joined by decision identity and timestamp;
3. fold roles and time boundaries are verified;
4. no outcome-dependent filtering occurs.

A row belongs to that common set if and only if its target status is `TARGET_USABLE` and
all three exact predictor statuses are `PREDICTOR_USABLE`, subject to the already frozen
TRAIN partition and fold/time assertions. No other status, reason, or row-level discretion
may add or remove a row.

## 6. One early-close-aware intraday harmonic

Test 3 does not reuse the fixed 22-slot Cell 14 `decision_slot_sin/cos` values. It derives
one deterministic harmonic from locked, target-independent calendar metadata so early-close
sessions have the correct horizon-safe decision count.

For each row:

```text
minutes_since_open = (decision_time - nyse_market_open_utc) / 1 minute
slot                = (minutes_since_open - 15) / 15
n_slots             = (nyse_market_close_utc - nyse_market_open_utc - 60 minutes)
                      / 15 minutes
angle               = 2 * pi * slot / n_slots
SESSION_SIN          = sin(angle)
SESSION_COS          = cos(angle)
```

`slot` and `n_slots` must be exact integers, `n_slots > 0`, and
`0 <= slot < n_slots`. The formula gives `n_slots = 22` for a normal NYSE session and
`n_slots = 10` for the standard 13:00 New York early close. The same two values enter both
models. Exactly one harmonic is allowed; no weekday, early-close flag, extra phase, or
alternative period may be added.

## 7. Frozen model pair and numerical policy

Model IDs and ordered design columns are:

```text
RVBASE001 = [intercept, X60, SESSION_SIN, SESSION_COS]
RVHAR001  = [intercept, X60, X120, X240, SESSION_SIN, SESSION_COS]
```

Both models use ordinary least squares on `Y = ln(RV_FWD_60)`. Later code must use
float64, the ordered columns above, and `numpy.linalg.lstsq(..., rcond=None)`. It must record
NumPy/LAPACK identity, design rank, singular values, condition number, coefficient dimension,
coefficients, and coefficient SHA-256. Full column rank and finite outputs are mandatory.

There is no scaling, regularization, intercept penalty, hyperparameter, early stopping,
coefficient constraint, feature selection, pooled refit, or third model.

For each model and fold, back-transform with the same fold-local Duan method:

```text
training_residual_i = Y_i - fitted_log_variance_i
smearing_factor     = mean(exp(training_residual_i))
forecast_variance   = exp(predicted_log_variance) * smearing_factor
```

The method is identical but the factor is model-specific because residuals are
model-specific. Only fold-TRAIN residuals may determine it. The factor and all forecasts
must be positive and finite. No clipping or shared factor selected after comparison is
allowed.

## 8. Walk-forward folds, purge, and fit budget

Reuse the exact Cell 8 roles:

```text
WF_2022: role_wf_2022, holdout year 2022
WF_2023: role_wf_2023, holdout year 2023
```

Before feature/target eligibility the frozen holdout counts are 5,510 and 5,476 rows,
respectively. For each fold:

- fold `TRAIN` rows fit the model;
- fold `VALIDATION` rows are the transparent outer-TRAIN OOF holdout;
- no 2024 outer-Validation row is involved;
- `max(train.label_end_time) < min(holdout.decision_time)` must hold;
- the wall-clock boundary gap must be at least 60 minutes;
- `EMBARGO_MINUTES = 0` is allowed only because the natural year boundary exceeds the
  60-minute horizon; any other boundary requires a new protocol decision.

Each holdout must contain at least 20 ordered NYSE sessions so the frozen 20-session
sensitivity can be computed. Each training design must have more eligible rows than fitted
coefficients and full column rank.

The lifetime Test 3 fit budget is exactly:

```text
2 model definitions x 2 folds = 4 real fold-fit calls
```

No fit occurs during protocol, code-only, metadata-only, or pre-fit support gates. A failed
or nonconvergent fit consumes its permit and may not be replaced. A code defect proven with
synthetic evidence requires a separate Owner repair authorization and qualifies only under
the companion budget's single-successor boundary before any fit permit/call, forecast,
coefficient, QLIKE result, or bootstrap replicate. It does not silently reset the scientific
budget, and no post-fit defect permits repair execution.

## 9. Dependence and support audit

Before any fit, later authorized TRAIN-only execution must report the level
`RV_FWD_60` autocorrelation profile within NYSE session at exact 15-minute spacings for
lags `k = 1..8`.

Under an IID squared-one-minute-return null, two 60-minute windows separated by `k`
decision steps share `max(4-k, 0)` of four 15-minute quarters. The precomputed mechanical
overlap reference is therefore:

```text
rho_null(k) = max(1 - k/4, 0)
lags 1..8   = [0.75, 0.50, 0.25, 0, 0, 0, 0, 0]
excess(k)   = rho_observed(k) - rho_null(k)
```

This is a null reference, not an acceptance threshold. Positive excess after overlap ends
is evidence of volatility clustering to describe, not a reason to alter the protocol.

For each fold and for pooled disjoint OOF rows, compute descriptive:

```text
DESIGN_EFFECT = max(1, 1 + 2 * sum(max(rho_observed(k), 0) for k in 1..8))
ESS           = eligible_row_count / DESIGN_EFFECT
```

Pooled ESS must be computed on pooled within-session pairs and may not be obtained by
summing fold ESS values. ESS is mandatory disclosure but is not a borrowed 1,000/2,000
pass gate. Statistical inference is governed by the paired session-block procedure below.

## 10. Loss and confidence method

For positive actual variance `a` and forecast `f`:

```text
QLIKE(a, f) = a / f - ln(a / f) - 1
d_i         = QLIKE(a_i, f_BASE_i) - QLIKE(a_i, f_HAR_i)
```

Positive `d_i` favors `RVHAR001`. For any set of rows, loss is row-weighted mean QLIKE.
Define the pooled materiality statistic exactly as:

```text
RELATIVE_QLIKE_REDUCTION =
    (POOLED_MEAN_QLIKE_BASE - POOLED_MEAN_QLIKE_HAR)
    / POOLED_MEAN_QLIKE_BASE
```

The baseline denominator must be positive and finite.

The confidence method adapts the Cell 13/Test 2 family:

- paired, non-circular consecutive-session moving blocks;
- 2,000 repetitions;
- five sessions per primary block;
- one and 20 sessions as required diagnostics only;
- master seed `20260809`;
- identical session draws for both models;
- blocks never cross fold boundaries.

The consecutive-session moving-block family originates in Cell 13. The one-sided fifth
percentile and the `+90000` pooled-seed namespace are inherited specifically from the
frozen Test 2 implementation in `test2_stats.py`; they are intentional Test 3 choices and
are not a claim of byte-identical Cell 13 two-sided `p025/p975` output.

For block length `L`, use:

```text
pooled_seed = 20260809 + 90000 + L
fold_seed   = pooled_seed + 1000 * (fold_index + 1)
fold order  = [WF_2022, WF_2023]
```

For a fold with `N_sessions`, use
`blocks_needed = ceil(N_sessions / L)`, sample starts uniformly with replacement from
`0..N_sessions-L`, concatenate non-circular consecutive blocks, and truncate to exactly
`N_sessions`. Resample the two folds independently, then pool sampled session sums and row
counts. The replicate statistic is pooled sampled `sum(d_i) / row_count`, not the mean of
fold means. The primary one-sided 95% lower bound is the fifth percentile of the 2,000
paired improvement replicates. No redraw, reseed, or best-of-seeds is permitted.

A sign change at 20 sessions is mandatory disclosure but does not independently pass or
fail Test 3.

## 11. Frozen pass gate

`RVHAR001` is `INTERESTING_ENOUGH_FOR_CONFIRMATORY_PROTOCOL` only if all conditions hold:

1. every source, request, partition, timestamp, target, predictor, rank, numerical, access,
   and fit-budget assertion passes;
2. mean paired QLIKE improvement is strictly greater than zero in `WF_2022`;
3. mean paired QLIKE improvement is strictly greater than zero in `WF_2023`;
4. pooled `RELATIVE_QLIKE_REDUCTION >= 0.10`;
5. the primary five-session paired-bootstrap one-sided 95% lower bound of pooled mean
   QLIKE improvement is strictly greater than zero;
6. all four and only four authorized real fold fits are observed by the fit-budget hook.

Equality fails conditions 2, 3, and 5. Equality passes the materiality boundary in
condition 4. No diagnostic can rescue a failed primary gate.

A pass authorizes only a separate discussion and protocol for confirmatory Validation. It
does not authorize that opening.

## 12. Dispositions

The terminal disposition must be exactly one of:

- `INTERESTING_ENOUGH_FOR_CONFIRMATORY_PROTOCOL`: every Section 11 gate passes;
- `NOT_INTERESTING_ENOUGH`: valid four-fit evidence exists but a scientific gate fails;
- `UNDERPOWERED_STOP`: a pre-fit structural minimum such as fewer than 20 holdout sessions,
  insufficient training rows, or rank impossibility fails before any fit;
- `INVALID_EVIDENCE`: source identity, access, request, reconciliation, numerical,
  `TARGET_ZERO_VARIANCE`, `PREDICTOR_NONFINITE`, `PREDICTOR_NONPOSITIVE`, fit-budget, or
  record integrity fails.

`TARGET_USABLE`, `TARGET_UNUSABLE`, `PREDICTOR_USABLE`, and `PREDICTOR_UNUSABLE` are
non-terminal row-status codes. Only the two exact `*_USABLE` statuses enter the frozen
common eligibility mask; the other two are excluded. None may be reclassified, imputed,
floored, or converted into a whole-run failure after inspection.

An `UNDERPOWERED_STOP` caused by too few rows after applying that frozen mask does not
reclassify any row status; it is a separate aggregate structural disposition.

`NOT_INTERESTING_ENOUGH` is a valid scientific result and ends this Test 3 hypothesis. It
does not permit a same-target model swap.

## 13. Required execution stages and records

Each stage requires separate Owner authorization:

1. **L0 code-only:** contracts, synthetic tests, no real artifact read;
2. **G2 metadata-only:** identities/schema/row-group metadata, zero numeric row values;
3. **G2-P TRAIN predictor-domain preflight:** only the three pinned Cell 14 predictor
   columns; complete status ledger; no target/path value and zero fits;
4. **G3-P TRAIN pre-fit:** sealed request set, target construction, Cell 12 reconciliation,
   common eligibility, fold boundaries, ACF/ESS and structural support; zero fits;
5. **G3-F one-shot:** exactly four fits, OOF forecasts, QLIKE, bootstrap, diagnostics, and
   immutable evidence.

Every record must include protocol/base/source identities, branch and commit equality,
ordered feature/model definitions, target and eligibility counts/reasons, fold/session
counts, target/request hashes, fit permits and completions, coefficient identities, Duan
factors, QLIKE results, dependence results, bootstrap seeds/draw identity, protected-row
counters, terminal disposition, and record SHA-256.

Minimum safety counters are:

```text
G2P_TRAIN_PREDICTOR_ROWS_READ
G2P_VALIDATION_PREDICTOR_ROWS_READ = 0
G2P_FINAL_TEST_PREDICTOR_ROWS_READ = 0
G2P_TARGET_OR_PATH_ROWS_READ       = 0
OUTER_TRAIN_TARGET_ROWS_READ       = 0 until G3-P
OUTER_VALIDATION_TARGET_ROWS_READ = 0
FINAL_TEST_TARGET_ROWS_READ       = 0
REAL_FOLD_FIT_CALLS               = 0 until G3-F; exactly 4 at completion
REAL_MODELS_FITTED                = 0 until G3-F; exactly 2 definitions at completion
VALIDATION_STATUS                 = UNOPENED
FINAL_TEST_STATUS                 = SEALED
LIVE_EXECUTION_STATUS             = DISABLED
```

Artifacts must be create-once and fail if the destination already exists. Raw execution
logs may remain local; semantic evidence and its hash must be committed promptly after a
successful one-shot run.

## 14. Explicitly forbidden actions

Without a new Owner-ratified protocol, Test 3 forbids:

- any target other than the exact 60-return `RV_FWD_60`;
- bipower variation, jump-robust RV, range estimators, annualization, alternate sampling,
  or another horizon;
- more harmonics, weekday/calendar additions, early-close dummy, or phase search;
- EWMA, GARCH, HAR variants, ridge/lasso, trees, boosting, HMM, neural networks,
  ensembles, or third-model rescue;
- feature search, coefficient constraints, hyperparameter search, tuning, or thresholding;
- row imputation, variance floors, clipping, winsorization, outcome-based exclusion, or
  post-result transform changes;
- re-fit, pooled fit, seed search, redraw, or repeated execution after seeing the result;
- economic/P&L claims, database work, UI coupling, LangGraph, live data, broker connection,
  Validation access, or Final-Test access.

## 15. Test 4 dependency

The current Test 4 concept assumes the winning Test 3 risk model as its baseline. If Test 3
ends `NOT_INTERESTING_ENOUGH`, `UNDERPOWERED_STOP`, or `INVALID_EVIDENCE`, Test 4 in that
form is void. A differently framed Test 4 would require a new hypothesis and protocol; it
cannot reinterpret or rescue Test 3. A repair-eligible `INVALID_EVIDENCE` run keeps Test 4
void unless and until an exact same-slot successor is separately ratified, executed, and
passes every Test 3 continuation gate.

## 16. Ratification and next authority

Owner ratification freezes this protocol together with
`TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md`. It also acknowledges that a present nonpositive
or nonfinite Cell 14 volatility predictor stops G2-P before target access, while a zero
forward realized-variance target completes its already authorized ledger and then stops
before fit. Neither may be excluded as a scientific rescue. The only possible successor is
the narrow, same-slot defect-repair path defined by the companion budget. Before a successor
can be ratified, synthetic evidence must prove that the implementation failed to conform to
the frozen protocol; an observed source or real-data state alone is not proof. A genuine
source/data state that triggers whole-run `INVALID_EVIDENCE` is terminal with no successor,
including zero variance, nonfinite, nonpositive, or mismatch. Non-terminal
`TARGET_UNUSABLE` and `PREDICTOR_UNUSABLE` retain only their frozen common-mask treatment.
The successor requires new exact Owner ratification and authorization and may amend only the
minimum implementation handling causally required to restore conformance with the frozen
protocol.

The successor may not change the frozen source lineage, target or horizon, predictor set,
harmonic, folds, transform/back-transform, common-eligibility or row-status/reason-code
dispositions, `RVBASE001`/`RVHAR001` model pair, four-fit budget, QLIKE contract, bootstrap
seed/repetitions/block lengths/sidedness, numerical policy, dependence-audit/ESS contract,
or continuation gates; it is never a model, predictor, metric, or row-selection rescue.
The companion budget governs slot consumption, reuse, and successor eligibility. After
ratification, the next eligible request is **Test 3 L0 code-only implementation**. Before
any code is written, the Owner must choose
whether to implement personally or authorize Codex. Claude remains the read-only
adversarial reviewer unless the Owner expands its authority.

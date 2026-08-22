# Test 2 Path-Aware — L0 Implementation Package V1

**Status:** `OWNER_APPROVED / L0_SYNTHETIC_ONLY`

**Implementation owner:** Human Owner

**Codex / Claude role:** read-only design and adversarial review

## Exact identity

```text
base commit  9a6f24add7efeb4594397fcd6fcd593641be4eba
base tree    8b49af26f84fcec8d4d8c6a782803292a8f27193
branch       research/test2-l0-implementation-v1
access       L0 / SYNTHETIC_ONLY
```

This package does not authorize real data, L1, Validation, or Final Test.

## Allowed files

All allowed files are new; existing files remain byte-identical.

- `docs/research/TEST2_L0_IMPLEMENTATION_PACKAGE_V1.md`
- `src/mes_quant/exploration/test2_path_contract.py`
- `src/mes_quant/exploration/test2_request_set.py`
- `src/mes_quant/exploration/test2_target.py`
- `src/mes_quant/exploration/test2_stats.py`
- `src/mes_quant/exploration/test2_evaluation.py`
- `tests/test_test2_request_set.py`
- `tests/test_test2_target.py`
- `tests/test_test2_stats.py`
- `tests/test_test2_evaluation.py`

No `__init__.py`, CLI, dependency, manifest, reference, pipeline, feature,
label, Sprint 1, or Test 1 file may change.

## Frozen implementation requirements

- reuse width-agnostic `l1_lr001.fit_frozen_logistic` and frozen numerics;
- do not reuse Sprint 1 record builders, median-fold gate, `_pr_auc`, or
  width-locked `_standardize`;
- implement fold-local TRAIN-only standardization as the width-agnostic
  equivalent of `_standardize`: TRAIN mean, population SD (`ddof=0`), and a
  zero-variance guard of `scale = 1.0` with affected feature names recorded;
- derive one retained-row index before prior/nuisance/full evaluation, require
  all three to consume the byte-identical index, persist its SHA-256, and raise
  before fit or scoring if any retained set diverges;
- before any fit, assert and record a minimum wall-clock boundary gap of at
  least 60 minutes for each fold;
- hash the ordered TRAIN-only request set before injected-provider lookup;
- enforce zero Validation/Final-Test lookups and reject unsealed keys;
- use integer ticks: TP 16, SL 8, offsets 0..59, and reject off-grid prices
  before conversion rather than rounding them;
- preserve favorable-first, adverse-first, neither, ambiguity, and no-score;
- require 60 bars, one instrument, and offset-59 endpoint reconciliation;
- implement stepwise average precision, Cell 13 ESS/support, and the frozen
  paired session-block bootstrap with row-weighted pooled loss;
- compute ESS for both `PATH_LONG` and `gross_move_points_60m`, let the lower
  value govern, compute pooled ESS from pooled retained rows rather than by
  summing folds, and compute effective class support as raw count divided by
  the governing design effect;
- fit only nuisance-4 and full-29 logistics with frozen numerics;
- enforce strict pooled-and-each-fold MDE/confidence gates at `0.0075` versus
  both prior and nuisance, with equality failing;
- stop `INCONCLUSIVE_UNDERPOWERED` before fitting when support fails;
- emit internally consistent experiment records.

## Required synthetic tests

Tests must prove request-before-lookup, boundary sealing, tick/first-touch
semantics, ambiguity/neither/no-score accounting, completeness and endpoint
checks, and off-grid-price rejection. They must also prove:

- the replacement standardizer reproduces `_standardize` element-wise on a
  29-wide synthetic matrix, including zero variance and its recorded name;
- prior, nuisance, and full consume byte-identical retained-row indices, the
  retained-set hash is recorded, and any divergence raises before fitting;
- a fold with a boundary gap below 60 minutes raises before fitting and valid
  per-fold gaps are recorded;
- both-outcome governing ESS, pooled-not-summed ESS, effective class support,
  and the `1000` per-fold / `2000` pooled / `200` support floors;
- bootstrap seeds/blocks/truncation/row-weighting, correct stepwise average
  precision, exactly two fixed fits, strict gate equality failure,
  underpowered pre-fit stop, and unchanged Test 1/full-suite behavior.

Only synthetic in-memory fixtures and temporary directories are permitted.

## L0 deferral and forbidden actions

Real-data adapters and economic arithmetic are outside L0. Freeze policy
identities `RELEASE_AT_FIRST_TOUCH`, `RESERVE_CAPACITY_TO_60M`, and
`first_touch_offset_minutes`.

No DBN/parquet/artifact reader, real-data path, target/label access, real fit,
new dependency, tuning, third model, second barrier, L1 token, Validation,
Final Test, push, merge, rebase, LangGraph reuse, or `.DS_Store` staging.

## Exit gate

L0 completes only after all new tests, the full suite, and lint pass; allowed
files are exact; Claude reports no blocker/high; and the Owner commits the
implementation. L1 still requires separate explicit Owner authorization.

```text
real TRAIN target/path rows read   0
Validation rows read               0
Final Test rows read               0
real models fitted                 0
implementation code files changed  0
```

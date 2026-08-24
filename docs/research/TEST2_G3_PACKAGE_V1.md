# Test 2 G3 — Pre-Fit Evidence Package V1

**Status:** `G3I_CODE_ONLY_PREPARED / G3P_EXECUTION_NOT_YET_AUTHORIZED / G3F_NOT_AUTHORIZED`

**Implementation owner:** Human Owner

**Patch preparation and adversarial review:** Codex + Claude Code

## 1. Exact base and boundary

```text
authorized base                     17925958fd1efcb6c9c1c52558656b951d27c850
implementation branch               research/test2-g3-pre-fit-v1
G3-I gate literal                   G3I_CODE_ONLY
G3-P gate literal                   G3P_PRE_FIT_EVIDENCE_ONLY
G3-F gate literal                   G3F_CONDITIONAL_FIT  (NOT_AUTHORIZED)
access during G3-I                  L0 / SYNTHETIC_ONLY
real TRAIN target/path rows read    0
Validation rows read                0
Final Test                          SEALED
real models fitted                  0
targets constructed                 0
decoded DBN messages read           0
new dependency introduced           no
database introduced                 no
```

G3-I is patch preparation only. It adds and modifies code plus synthetic tests.
It does not decode the canonical DBN, read any Parquet row, construct a target,
reconcile Cell 12, or fit a model. Applying and reviewing the G3-I patch does not
execute G3-P, and a passing G3-P execution does not open G3-F.

## 2. Gate split

```text
G3-I  code only
      production runner, adapters, contract, and synthetic tests
      zero real reads, zero fits

G3-P  pre-fit evidence, separately authorized
      canonical decode identity, physical TRAIN-only reads,
      Cell 8/10/14 cross-binding, sealed request set, frozen target,
      exact Cell 12 reconciliation, frozen support gate
      then STOP — zero fits under both support outcomes

G3-F  conditional fit, NOT AUTHORIZED and unimplemented
      would run only PATHNUISANCE001 and PATHFULL001 across two folds
      (four fold-fit calls) after a passing G3-P record and a separate,
      explicit Owner authorization
```

No G3-P result may be used to change a model definition, barrier set, fold, MDE
floor, ESS floor, or class-support floor. The G3-P record exists to prove that
the pre-fit evidence chain is intact, not to inform the science.

## 3. Changed-file firewall — exactly eleven files

Added:

- `docs/research/TEST2_G3_PACKAGE_V1.md`
- `src/mes_quant/exploration/test2_g3_contract.py`
- `src/mes_quant/exploration/test2_decode.py`
- `src/mes_quant/exploration/test2_g3_pre_fit.py`
- `tools/run_test2_g3p_pre_fit.py`
- `tests/test_test2_g3_pre_fit.py`
- `tests/test_test2_decode.py`

Modified:

- `src/mes_quant/exploration/test2_l1_harness.py`
- `src/mes_quant/exploration/test2_run_context.py`
- `tests/test_test2_l1_harness.py`
- `tests/test_test2_run_context.py`

`test2_target.py`, `test2_stats.py`, `test2_evaluation.py`,
`test2_metadata_preflight.py`, `test2_diagnostics.py`, `test2_request_set.py`,
`test2_path_contract.py`, Test 1, feature generation, manifests, references,
configs, dependencies, pipelines, Validation, and Final-Test files remain
byte-identical to `1792595`. The allowlist is machine-enforced by
`G3I_ALLOWED_CHANGED_FILES` and `changed_file_firewall_failures`, and the G3-P
runner refuses to execute if the diff from the authorized base is not exactly
these eleven paths.

## 4. Corrected Cell 12 reconciliation rule

The G1 rule reconciled only rows whose recomputed path happened to be complete.
That silently tolerated a Cell 12 artifact that did not cover the sealed TRAIN
set, and it could not detect a row that Cell 12 declared unusable while the
recomputation produced a scored path. The corrected rule is:

1. **Physical read.** Cell 12 outer-TRAIN rows are read with the
   `outer_partition == TRAIN` predicate pushed into Parquet, including
   `path_status`, `path_usable`, and `path_1m_present` alongside the four
   numeric path fields.
2. **Exact identity coverage.** The set of Cell 12 TRAIN decision identities must
   equal the sealed TRAIN decision set exactly. There is no absent-row floor and
   no intersection policy: `CELL12_ABSENT_ROWS` must be `0`, and an unexpected
   Cell 12 identity is equally fatal.
3. **Expected usable rows.** The recomputed path must be a complete 60-bar priced
   path, and recomputed path high, path low, long MFE, and long MAE must equal
   the Cell 12 values exactly on the integer `0.25`-point tick grid.
4. **Expected unusable rows.** The recomputation must be unusable in the same
   way: the row must fail closed to `NO_SCORE` and must not produce a complete
   priced path. Cell 12's numeric path fields must be absent for that row — they
   are never defaulted, imputed, or compared against a substituted value.
5. **Verdict coverage.** Every sealed TRAIN decision carries exactly one
   reconciliation verdict, and every verdict is either
   `EXACT_TICK_RECONCILIATION_PASS` or
   `EXACT_UNUSABLE_ABSENT_NUMERIC_FIELD_RECONCILIATION_PASS`.

A sealed Final-Test Cell 12 status appearing in an outer-TRAIN read is a hard
failure, not a filtered row.

## 5. Physical Cell 8 cross-assertion

`read_train_cell8_assignments` performs a predicate-pushed outer-TRAIN read of
the Cell 8 split assignments. `prepare_train_inputs` then cross-asserts, for the
exact same decision set as the Cell 10/Cell 14 join:

- identical decision-identity sets and row counts;
- exact `decision_time` equality;
- exact `role_wf_2022` and `role_wf_2023` equality;
- exact `outer_partition` equality;
- native `instrument_id` equality under the shared comparison rule;
- every Cell 8 TRAIN timestamp strictly before the outer-Validation boundary.

`build_real_l1_run_context` refuses to produce a real L1 context unless this
binding was asserted, so a run cannot claim Cell 8 role identity it never read.

## 6. Canonical decode wrapper

`test2_decode` reproduces Cell 2 and normalizes the frame before verification.
Cell 2 hashes `mes_1m[["open", "high", "low", "close", "instrument_id"]]` with
`index=True, categorize=False` — a *selection* in that order, not the decoded
frame's own column order. `normalize_cell2_hash_frame` therefore:

- promotes a `ts_event` column to the index when needed;
- requires a tz-aware UTC `ts_event` index that is unique and monotonic;
- projects onto the five Cell 2 hash columns in Cell 2 order;
- rejects any missing value in a hash column;
- leaves values, dtypes, row order, and the index object untouched.

`decode_canonical_dbn` verifies the raw DBN byte SHA-256 **before** attempting a
decode, decodes through the already-pinned `databento` dependency, normalizes,
then recomputes and compares the frozen decoded content SHA-256. The
`databento` import is lazy, so importing the wrapper never loads a DBN decoder
and the frozen G2 module-absence witness stays valid. No new dependency is
introduced.

## 7. Vectorized batch provider

`VectorizedDataFramePathBarProvider` subclasses the G1 provider and replaces the
per-key `.loc` lookup with one vectorized `get_indexer` per batch. It is
element-equivalent by construction: identical seal validation and error,
identical `rows_examined` / `missing_keys` / `instrument_mismatch_keys`
accounting, and identical `PathBar` values. Row values are materialized through
`DataFrame.to_numpy`, which resolves the same common dtype a `.loc[timestamp]`
row Series would, so native instrument comparison cannot drift between the two
providers.

`build_train_path_targets` finalizes each decision as soon as all 60 sealed
requests for that decision have crossed the provider. Completed `PathBar`
objects are released before the next batch proceeds, so the canonical run does
not retain the full ~1.54 million-object path expansion in memory.

## 8. G3-P orchestration and the zero-fit guarantee

`run_g3p_pre_fit` executes the whole collection and record assembly inside
`pre_fit_only_guard`, which mechanically replaces every fit, bootstrap, and
economic-diagnostic entry point across `l1_lr001`, `l1_tree001`,
`test2_evaluation`, `test2_stats`, and `test2_diagnostics`. Each blocked symbol
must exist when the guard installs, so a moved fit surface fails the run instead
of silently escaping coverage. Any blocked call raises immediately and is
recorded in the guard witness; a record cannot be assembled with a non-zero
`blocked_fit_calls`.

The record binds branch, authorized base, clean tracked worktree, pushed
upstream identity, the eleven-file firewall, pinned document hashes including
this exact G3 authorization package, the
canonical metadata identity, the recomputed decoded identity, the sealed request
identity, and the zero counters. The authorization record SHA-256 is the hash of
the canonical authorization binding block, not an unrelated token.

Both support outcomes stop before fitting:

```text
support gate fails   ->  SUPPORT_GATE_FAIL_INCONCLUSIVE_UNDERPOWERED
                         disposition  INCONCLUSIVE_UNDERPOWERED
                         fit_status   SKIPPED_INCONCLUSIVE_UNDERPOWERED

support gate passes  ->  SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED
                         disposition  DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION
                         fit_status   BLOCKED_FIT_NOT_AUTHORIZED_G3P_PRE_FIT
```

`real_models_fitted` is `0` in both, and the passing branch states the support
result truthfully without implying that a fit ran or that G3-F opened.

## 9. Record content and output

Records are aggregate and hash-only. They carry counts, rates, ESS/design-effect
summaries, retained-set hashes, decile grid hashes, and identity hashes. They
never carry decision identities, decision times, per-row path values, decile cut
points, model coefficients, losses, improvements, bootstrap bounds, or economic
trades; a closed-record assertion rejects those keys anywhere in the payload.

The only output location is ignored runtime evidence beneath:

```text
artifacts/exploration/test2/g3p/<run_id>/pre_fit_support_record.json
```

The write is create-once: a fresh run directory, an atomic temporary file linked
into place, and a fatal error if the directory already exists. The canonical
`record_sha256` excludes only the volatile audit timestamp.

## 10. No CLI knobs for frozen science

The runner accepts only the gate literal, the five read-only artifact paths, the
Cell 14 run ID, the two tracked manifest paths, and the fixed output root.
Barriers, tick size, the 60 offsets, folds, MDE floors, ESS and class-support
floors, bootstrap seeds and block lengths, and the two model definitions are
read from the frozen contract modules and cannot be overridden from the command
line. The path-bar batch size is an implementation constant that controls only
how the sealed expansion is streamed, never what is requested.

## 11. Two separate Owner steps

### A. Apply and preserve the G3-I patch

Create the exact branch from `1792595`, apply the reviewed patch, run the
targeted and full synthetic suites plus Ruff, then commit and push. The G3-P
runner refuses to execute unless the branch name is exact, the authorized base
is an ancestor, the diff from the base is exactly the eleven allowlisted files,
the tracked worktree is clean, and local `HEAD` equals its pushed upstream.

### B. Execute G3-P only after A is committed, pushed, and separately authorized

```bash
.venv/bin/python tools/run_test2_g3p_pre_fit.py \
  --gate G3P_PRE_FIT_EVIDENCE_ONLY \
  --raw-dbn "/absolute/read-only/path/MES_2019_2026_1m.dbn.zst" \
  --cell8 "/absolute/read-only/path/cell8_purged_split_assignments_v1.parquet" \
  --cell10 "/absolute/read-only/path/cell10_point_in_time_economic_labels_v1.parquet" \
  --cell12 "/absolute/read-only/path/cell12_development_path_outcomes_v1.parquet" \
  --cell14-features "/absolute/read-only/path/cell14_development_point_in_time_features_v1.parquet" \
  --cell14-run-id "<canonical-or-replay-run-id-from-manifest>"
```

## 12. Required passing witness

```text
G3P_PRE_FIT_PASS_NO_FIT_EXECUTED
REAL_TRAIN_TARGET_PATH_ROWS_READ=<n>
TARGETS_CONSTRUCTED=<n>
MISSING_PATH_BAR_KEYS=<n>
NATIVE_INSTRUMENT_MISMATCH_KEYS=<n>
CELL12_RECONCILED_ROWS=<n>
BARRIER_SETS_CONSTRUCTED=1
SEARCH_BUDGET_MODELS_CONSUMED=0
REAL_MODELS_FITTED=0
REAL_FOLD_FIT_CALLS=0
BOOTSTRAP_REPLICATES=0
ECONOMIC_DIAGNOSTIC_CALLS=0
BLOCKED_FIT_CALLS=0
DECODED_CONTENT_STATUS=RECOMPUTED_FULL_CANONICAL_CELL2_DECODE
CELL12_RECONCILIATION_STATUS=EXACT_FULL_TRAIN_COVERAGE_RECONCILIATION_PASS
CELL12_ABSENT_ROWS=0
VALIDATION_ROWS_READ=0
FINAL_TEST=SEALED
SUPPORT_GATE_STATUS=<SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED|SUPPORT_GATE_FAIL_INCONCLUSIVE_UNDERPOWERED>
DISPOSITION=<DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION|INCONCLUSIVE_UNDERPOWERED>
G3F_STATUS=NOT_AUTHORIZED
```

Any missing input, byte mismatch, manifest mismatch, decoded-identity mismatch,
Cell 8 cross-binding failure, Cell 12 coverage or tick mismatch, boundary
crossing, blocked fit attempt, wrong branch, dirty tracked worktree, unpushed
commit, or firewall mismatch stops G3-P before a record is written.

## 13. Exit gate for the G3-I patch

- targeted G3-I tests pass;
- the full existing suite passes;
- Ruff passes on the changed files;
- changed files equal the eleven-file allowlist;
- Claude Code returns no blocker/high on the exact final diff;
- the Owner applies, tests, commits, and pushes the reviewed patch.

Passing this gate does not execute G3-P. Passing a later G3-P execution does not
authorize G3-F, either model fit, Validation opening, Final Test, database work,
deployment, or broker connectivity.

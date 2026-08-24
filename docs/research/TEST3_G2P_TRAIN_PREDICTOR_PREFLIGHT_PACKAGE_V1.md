# Test 3 G2-P TRAIN Predictor-Domain Preflight Package V1

Package ID: MES_TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_PACKAGE_V1

Status: OWNER AUTHORIZED / IMPLEMENTATION AND EXECUTION PENDING

Authorization: AUTH_TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_20260824

Authorized base: 21c42de47deeb8fac1da9208fdbc8ad4fa6369ca

Branch: research/test3-g2p-predictor-preflight-v1

## 1. Purpose

This package performs the separately authorized, target-blind G2-P stage from the ratified
Test 3 protocol. It authenticates the committed G2 evidence, cross-binds outer-TRAIN Cell 8
and Cell 14 control identities, and inspects exactly three Cell 14 volatility predictors to
seal the complete predictor-status ledger before any target-aware access.

## 2. Authority chain

The durable record binds:

`MES_TEST3_RV60_HAR_RISK_EDGE_V1`
→ frozen protocol `7c17b292958aeb8252f9c0911ef7028b6071cdbb`
→ ratification record `05f569f3ee2093461b5330e8069cb2fd0099d3b1`
→ L0 `b16d025dd84b590a8a441c05232e6f761ee7f9bf`
→ G2 package `4572b97c577f4445641f2b0e0b84549b0ae1b78c`
→ G2 evidence/base `21c42de47deeb8fac1da9208fdbc8ad4fa6369ca`
→ exact pushed G2-P implementation commit/tree observed at runtime.

## 3. Read firewall

The reader opens only canonical Cell 8 and Cell 14 files. Each single projection call carries
`outer_partition == TRAIN` before requesting values. Python receives exactly 25,685 rows:
six Cell 8 control fields, the same Cell 14 controls, and the ordered predictor tuple
`realized_vol_60m`, `realized_vol_120m`, `realized_vol_240m`. Cell 8 and Cell 14 decision
set, time, instrument, fold roles, order, and partition must match row-for-row before status
sealing. The implementation must reject source order inversion; it may not sort it away.

`*_ROWS_READ` counts application-exposed rows. Because the canonical Cell 14 file has one
mixed Parquet row group, this package does not claim that the engine avoided compressed-byte
reads or internal page decoding. It proves instead that no Validation predictor value is
returned to or inspected by Python application code.

Pinned source totals remain Cell 14 `31,193 = 25,685 TRAIN + 5,508 VALIDATION` and Cell 8
`39,847 = 25,685 TRAIN + 5,508 VALIDATION + 8,654 FINAL_TEST`. Application-exposed TRAIN
rows must preserve the frozen strict chronological source order and end before 2024
outer Validation.

The implementation does not import a DBN decoder, target/path builder, fitter, evaluation,
bootstrap, Cell 10, or Cell 12 reader. It never requests any of the other 26 Cell 14 feature
values or the global feature usability/status fields.

## 4. Ledger and disposition

Rows must already be strictly ordered by UTC decision time and decision identity. Status
precedence is frozen to match L0: among present values, nonfinite precedes nonpositive;
otherwise any Arrow-null is `PREDICTOR_UNUSABLE`; only three present finite positive values are
`PREDICTOR_USABLE`. The aggregate record stores fixed-key status counts plus ordered identity
and ordered identity/status SHA-256 values. No per-row identity/status or predictor value is
persisted. A later separately authorized G3-P must reconstruct the complete ledger from the
same pinned bytes and reproduce both sealed hashes before common-mask use.

The hash projection ID is `MES_TEST3_PREDICTOR_LEDGER_PIPE_UTF8_V1`. It exactly mirrors L0:
normalize time with `astimezone(UTC).isoformat()` (`+00:00` for UTC), preserve verified source
order, encode UTF-8 without header/BOM, separate fields with `|`, and terminate each row with
LF. Identity rows are `decision_id|decision_time\n`; identity/status rows are
`decision_id|decision_time|status\n`. IDs containing `|`, CR, or LF fail closed.

Missing predictor values are non-terminal `PREDICTOR_UNUSABLE`. Any present nonfinite or
nonpositive predictor seals the exact terminal disposition `INVALID_EVIDENCE` and stops
before target access. A separate cause-audit field remains pending; G2-P itself does not
decide repair eligibility or close the target slot. Otherwise it seals
`G2P_PREDICTOR_PREFLIGHT_PASS`. Neither outcome opens G3-P automatically.

## 5. Repository and one-shot gates

Before artifact access, the runner requires the exact branch, one direct-child package
commit, exact five-file allowlist, clean tracked worktree, no rogue import surface, exact
origin upstream equality, frozen document hashes, and the committed G2 record/reservation
bytes and semantic bindings. It then consumes one create-once authorization reservation.

Execution uses exactly:

```text
.venv/bin/python -I -B tools/run_test3_g2p_preflight.py \
  --gate G2P_TEST3_TARGET_BLIND_TRAIN_PREDICTOR_PREFLIGHT \
  --authorization-token OWNER_AUTHORIZED_TEST3_G2P_TARGET_BLIND_TRAIN_PREFLIGHT_20260824 \
  --cell8 "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/cache/source_v1/cell8_purged_split_assignments_v1.parquet" \
  --cell14-features "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/runs/cell14_20260809T175203Z/cell14_development_point_in_time_features_v1.parquet"
```

The runtime rejects any other artifact path before consumption. Isolation is checked before
project/third-party imports and again by the main runner. Runtime module origins, PyArrow
`18.1.0`, callable provenance, forbidden scientific/execution modules, same-descriptor
pre/post source hashes plus inode/size/mtime/ctime, and no-follow dir-FD path traversal are
fail-closed. Tracked package initialization imports `pandas` transitively, but the G2-P module
may neither import nor call it; the AST/projection and module-origin firewalls enforce this
boundary. All input and evidence path components must be non-symlink. Reservation and
evidence writes are exclusive-create and fsynced.

Technical failure after reservation produces a scrubbed create-once failure summary and no
retry. Successful or protocol-terminal completion publishes one create-once aggregate record.

Pinned source/ledger mismatches use a distinct create-once typed terminal summary with exact
`INVALID_EVIDENCE`, a bounded mismatch category, cause audit required, target space still
locked/reserved and unconsumed, and Final Test sealed. Structurally unreachable target/fit/
Cell 10/Cell 12/DBN counters remain zero. A row-count, returned-projection, or TRAIN-only
projection breach must instead mark affected exposure counters
`NOT_ATTESTED_DUE_TO_INVALID_PROJECTION` and both Validation and Final Test
`ACCESS_BREACH_FAIL_CLOSED`; it may not assert an unverified zero, unopened, or sealed state.
These cases must not be mislabeled as generic technical failures.

## 6. Required witness

The record and terminal witness must include:

```text
G2P_TRAIN_PREDICTOR_ROWS_READ=<complete outer-TRAIN count>
CELL8_VALIDATION_CONTROL_ROWS_READ=0
CELL8_FINAL_TEST_CONTROL_ROWS_READ=0
CELL14_VALIDATION_CONTROL_ROWS_READ=0
CELL14_FINAL_TEST_CONTROL_ROWS_READ=0
CELL10_ROWS_READ=0
CELL12_ROWS_READ=0
RAW_DBN_MESSAGES_DECODED=0
NON_ALLOWLISTED_CELL14_VALUE_COLUMNS_READ=0
G2P_VALIDATION_PREDICTOR_ROWS_READ=0
G2P_FINAL_TEST_PREDICTOR_ROWS_READ=0
G2P_TARGET_OR_PATH_ROWS_READ=0
OUTER_TRAIN_TARGET_ROWS_READ=0
OUTER_VALIDATION_TARGET_ROWS_READ=0
FINAL_TEST_TARGET_ROWS_READ=0
TARGETS_CONSTRUCTED=0
REAL_FOLD_FIT_CALLS=0
REAL_MODELS_FITTED=0
REAL_BOOTSTRAP_REPLICATES=0
VALIDATION_STATUS=UNOPENED
FINAL_TEST_STATUS=SEALED
LIVE_EXECUTION_STATUS=DISABLED
TARGET_SPACE_CONSUMPTION_STATUS=NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT
G3P_STATUS=NOT_AUTHORIZED
G3F_STATUS=NOT_AUTHORIZED
```

## 7. Evidence lifecycle

After targeted/full tests, Ruff, firewalls, and independent Claude Code read-only
adversarial review pass, commit and push the exact package. Requested model alias/effort and
actual runtime model metadata, when returned by the CLI, are recorded separately from this
scientific package. Only then execute once. Commit and push the
reservation plus aggregate record (or scrubbed post-consumption failure) immediately.
Raw logs remain local. G2-P completion grants no target access, fit, later-stage, or merge
authority.

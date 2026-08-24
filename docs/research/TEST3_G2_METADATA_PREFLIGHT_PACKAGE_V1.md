# Test 3 G2 Metadata-Only Preflight Package V1

Package ID: MES_TEST3_G2_METADATA_PREFLIGHT_PACKAGE_V1

Status: OWNER AUTHORIZED / IMPLEMENTATION AND EXECUTION PENDING

Authorization: AUTH_TEST3_G2_METADATA_ONLY_20260824

Authorized base: b16d025dd84b590a8a441c05232e6f761ee7f9bf

Branch: research/test3-g2-metadata-preflight-v1

## 1. Purpose

This package authenticates the frozen Test 3 upstream files before any numeric-domain
stage. It is deliberately smaller than the Test 2 harness: the implementation is a
standalone metadata reader and imports no Test 2 experiment harness, target builder,
Test 3 target/design/statistics module, fitter, or DBN decoder.

## 2. Authority chain

The execution record must bind this chain:

MES_TEST3_RV60_HAR_RISK_EDGE_V1
→ frozen protocol commit 7c17b292958aeb8252f9c0911ef7028b6071cdbb
→ ratification record commit 05f569f3ee2093461b5330e8069cb2fd0099d3b1
→ authorized L0 base b16d025dd84b590a8a441c05232e6f761ee7f9bf
→ exact pushed G2 execution commit and Git tree observed at runtime.

Draft PR #47 remains unmerged. The runner executes directly from the G2 branch and grants
no merge authority.

## 3. Metadata firewall

The five canonical artifacts and two manifests are byte-hashed. Parquet exposure is limited
to schema names, total row count, and total row-group count. Serialized footer bytes may
contain statistics, but the implementation never accesses row-group objects, column chunks,
statistics, key-value metadata, data pages, or decoded values. Therefore the canonical
witness says COLUMN_STATISTICS_ACCESSED=0, not that such bytes are absent from the footer.

Files are opened read-only without following a final symlink. The implementation requires a
regular file, hashes and inspects from the same descriptor, and compares descriptor identity
before and after inspection. JSON manifests reject duplicate keys and expose only explicit
binding fields.

## 4. Repository and one-consumption gates

Before artifact access, the runner requires the exact branch, ancestor chain, five-file
allowlist, clean tracked worktree, no untracked or ignored importable code, and local HEAD
equal to the pushed upstream. It verifies the frozen protocol, budget, ratification, and L0
document bytes plus this authorization document.

It then creates one exclusive authorization reservation. A post-reservation failure consumes
the authorization. The record and reservation are create-once and may not overwrite an
existing destination.

## 5. Required witness

The passing witness must state:

TEST3_G2_METADATA_PREFLIGHT_PASS_NO_NUMERIC_ROW_VALUES_READ
NUMERIC_ROW_VALUES_READ=0
PARQUET_DATA_ROW_GROUPS_READ=0
PARQUET_ROW_GROUP_OBJECTS_ACCESSED=0
PARQUET_COLUMN_STATISTICS_ACCESSED=0
G2P_TRAIN_PREDICTOR_ROWS_READ=0
G2P_TARGET_OR_PATH_ROWS_READ=0
OUTER_TRAIN_TARGET_ROWS_READ=0
REAL_FOLD_FIT_CALLS=0
REAL_MODELS_FITTED=0
VALIDATION_STATUS=UNOPENED
FINAL_TEST_STATUS=SEALED
LIVE_EXECUTION_STATUS=DISABLED
G2P_STATUS=NOT_AUTHORIZED

Target, eligibility, fold, forecast, and metric fields that do not belong to G2 are recorded
as NOT_COMPUTED_STAGE_NOT_AUTHORIZED rather than fabricated as measured results.

## 6. Evidence lifecycle

After tests, lint, allowlist checks, and independent review pass, commit and push the package.
Only then may the Owner-authorized runner consume the reservation and inspect canonical
metadata. After consumption, force-add the reservation plus either the aggregate success
record or a scrubbed post-reservation failure summary in a separate evidence commit. Raw logs
stay local.

G2 does not consume TARGET_SPACE_003 and opens no later stage automatically.

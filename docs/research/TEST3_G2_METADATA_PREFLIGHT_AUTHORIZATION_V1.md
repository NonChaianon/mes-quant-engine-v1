# Test 3 G2 Metadata-Only Owner Authorization V1

Authorization ID: AUTH_TEST3_G2_METADATA_ONLY_20260824

Authorization token: OWNER_AUTHORIZED_TEST3_G2_METADATA_ONLY_20260824

Status: OWNER AUTHORIZED / METADATA-ONLY / ONE CONSUMPTION

Owner decision date: 2026-08-24 (Asia/Bangkok)

Protocol ID: MES_TEST3_RV60_HAR_RISK_EDGE_V1

Frozen protocol commit: 7c17b292958aeb8252f9c0911ef7028b6071cdbb

Ratification record commit: 05f569f3ee2093461b5330e8069cb2fd0099d3b1

Authorized base: b16d025dd84b590a8a441c05232e6f761ee7f9bf

Execution branch: research/test3-g2-metadata-preflight-v1

## Owner instruction and repository stance

The Owner authorizes Codex to prepare, test, commit, push, adversarially review, and execute
the bounded Test 3 G2 metadata-only preflight. The exact pushed commit observed by the
runner is the execution identity and must be recorded together with its Git tree and
local/upstream equality.

Draft PR #47 remains open and unmerged. G2 executes from a direct descendant branch of the
authorized base. This authorization grants no merge authority.

## Authorized metadata surface

Only these existing identities may be inspected:

1. raw MES DBN archive: opaque byte hash, filename, and size only;
2. Cell 8 split assignments: opaque byte hash, filename, size, schema names, total rows,
   and total row groups;
3. Cell 10 labels: the same metadata fields only;
4. Cell 12 path outcomes: the same metadata fields only;
5. Cell 14 feature file: the same metadata fields only;
6. frozen Colab manifest and Cell 14 release manifest: byte identity and the exact binding
   fields required to authenticate the five artifacts and the selected canonical/replay run.

Hashing opaque file bytes is allowed. The implementation may instantiate the Parquet footer
objects required to obtain the allowlisted names and aggregate counts, but it may not access
or record a data page, row-group object, column chunk, column statistic, key-value metadata,
or numeric row value.

## One-consumption boundary

After all repository, authorization-document, and cheap deterministic checks pass, the
runner must create an authorization-SHA-scoped reservation with exclusive create before
opening any artifact. Any failure after that reservation consumes this authorization and
must not be retried. A new attempt requires a new Owner authorization.

## Exact additive allowlist

Only these five files may differ from the authorized base before execution:

1. docs/research/TEST3_G2_METADATA_PREFLIGHT_AUTHORIZATION_V1.md
2. docs/research/TEST3_G2_METADATA_PREFLIGHT_PACKAGE_V1.md
3. src/mes_quant/exploration/test3_metadata_preflight.py
4. tests/test_test3_metadata_preflight.py
5. tools/run_test3_g2_metadata_preflight.py

No pre-existing file or dependency may change.

## Required zero boundary

G2-P predictor reads, target/path reads, target construction, fold fits, fitted models,
bootstrap, outer Validation, and Final Test must all remain zero or unopened. Live execution
remains disabled and TARGET_SPACE_003 remains locked/reserved but unconsumed.

## Evidence and next authority

The package must be committed and pushed before execution. After authorization consumption,
the create-once reservation plus either the successful aggregate record or a scrubbed failure
summary must be force-added in a separate evidence commit and pushed promptly. This duty also
applies to a post-reservation failure. Raw execution logs stay local. G2 success opens no
G2-P, G3-P, G3-F, Validation, Final Test, database, UI, live, or broker authority.

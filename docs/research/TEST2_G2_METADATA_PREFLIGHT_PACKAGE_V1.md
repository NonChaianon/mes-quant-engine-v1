# Test 2 G2 — Canonical Metadata-Only Preflight Package V1

**Status:** `OWNER_AUTHORIZED / IMPLEMENTATION_PATCH_NOT_YET_APPLIED`

**Implementation owner:** Human Owner

**Patch preparation and adversarial review:** Codex + Claude Code

## Authorization and exact boundary

```text
authorized base                     99daf97e4f7cb1a1d1d0e02f743cf1b164b49201
implementation branch               research/test2-g2-metadata-preflight-v1
authorization literal               G2_CANONICAL_METADATA_ONLY
authorized access                   byte hashes + manifest fields + Parquet footer
Parquet footer fields exposed        schema names + num_rows only
numeric row values read              0
Parquet row groups read              0
Parquet column statistics read       0
decoded DBN messages read            0
targets constructed                  0
real models fitted                   0
Validation rows read                 0
Final Test                           SEALED
G3                                   NOT_AUTHORIZED
database introduced                  no
```

G2 invokes the already-frozen G1 canonical metadata preflight through an additional
runtime guard. It may hash complete files as bytes, parse the two release manifests, and
inspect only Parquet schema names and footer row counts. It may not expose any row value,
row group, column statistic, decoded DBN content, target, request-set identity, or model.

## Changed-file firewall

The patch adds exactly four files and modifies no existing file:

- `docs/research/TEST2_G2_METADATA_PREFLIGHT_PACKAGE_V1.md`
- `src/mes_quant/exploration/test2_metadata_preflight.py`
- `tests/test_test2_metadata_preflight.py`
- `tools/run_test2_g2_metadata_preflight.py`

Manifests, configs, dependencies, Test 1, the G1 harness, target/statistical/evaluation
code, feature generation, Validation, and Final-Test files remain byte-identical to
`99daf97`.

## Canonical input set

Execution requires all five canonical artifacts with their frozen filename and byte
SHA-256 identity:

1. raw DBN archive;
2. Cell 8 split assignments;
3. Cell 10 point-in-time economic labels;
4. Cell 12 development path outcomes;
5. Cell 14 development point-in-time features.

The frozen Colab and Cell 14 release manifests must also match their pinned byte hashes.
The selected Cell 14 run must be either the manifest's canonical or replay run and must
declare the same feature filename and byte hash.

The repository working tree does not contain the canonical raw DBN archive or Cell 12
Parquet artifact. The Owner must supply their existing read-only locations at execution.
They must not be copied into Git. A missing or mismatched artifact is an expected
fail-closed result and creates no evidence record.

Do not use `tools/verify_cell14_release.py` for G2: that verifier deserializes numeric
rows and therefore exceeds this authorization.

## Two separate Owner steps

### A. Apply and preserve the implementation patch

The Owner creates the exact G2 branch from `99daf97`, applies the reviewed patch, runs the
targeted and full synthetic test suites plus Ruff, then commits and pushes. The G2 runner
will refuse to execute unless:

- the branch name is exact;
- the authorized base is an ancestor;
- the complete diff from the base contains exactly the four allowlisted files;
- the tracked worktree is clean; and
- local `HEAD` equals its pushed upstream.

This keeps local and Git code identities together before any canonical metadata access.

### B. Execute G2 only after A is committed and pushed

The Owner supplies literal paths without opening the artifacts manually:

```bash
.venv/bin/python tools/run_test2_g2_metadata_preflight.py \
  --gate G2_CANONICAL_METADATA_ONLY \
  --raw-dbn "/absolute/read-only/path/MES_2019_2026_1m.dbn.zst" \
  --cell8 "/absolute/read-only/path/cell8_purged_split_assignments_v1.parquet" \
  --cell10 "/absolute/read-only/path/cell10_point_in_time_economic_labels_v1.parquet" \
  --cell12 "/absolute/read-only/path/cell12_development_path_outcomes_v1.parquet" \
  --cell14-features "/absolute/read-only/path/cell14_development_point_in_time_features_v1.parquet" \
  --cell14-run-id "<canonical-or-replay-run-id-from-manifest>"
```

The only output location is ignored runtime evidence beneath:

```text
artifacts/exploration/test2/g2/<run_id>/metadata_preflight_record.json
```

The record is create-only. Its canonical `record_sha256` excludes the volatile audit
timestamp and normalizes artifact locations, so equivalent inputs have a stable identity.
Generated evidence is not automatically staged or committed. Codex and Claude review the
Owner-returned terminal witness and record structure before any separate preservation
decision.

## Required passing witness

```text
G2_METADATA_PREFLIGHT_PASS_NO_NUMERIC_ROW_VALUES_READ
NUMERIC_VALUES_READ=0
PARQUET_ROW_GROUPS_READ=0
PARQUET_COLUMN_STATISTICS_READ=0
DECODED_CONTENT_STATUS=NOT_RECOMPUTED_METADATA_ONLY
ORDERED_FEATURE_CONTENT_STATUS=NOT_RECOMPUTED_METADATA_ONLY
TARGETS_CONSTRUCTED=0
REAL_MODELS_FITTED=0
VALIDATION_ROWS_READ=0
FINAL_TEST=SEALED
G3_STATUS=NOT_AUTHORIZED
```

Any missing input, byte mismatch, manifest mismatch, forbidden reader call, DBN decoder
module import, wrong branch, dirty tracked worktree, unpushed commit, or changed-file
firewall mismatch stops G2 before a successful record is written.

## Exit gate for the implementation patch

- targeted G2 tests pass;
- the full existing suite passes;
- Ruff passes;
- changed files equal the four-file allowlist;
- Claude Code returns no blocker/high on the exact final diff;
- the Owner applies, tests, commits, and pushes the reviewed implementation patch.

Passing this implementation gate does not execute G2. Passing a later G2 execution does
not authorize G3, numeric TRAIN access, target construction, either model fit, Validation,
Final Test, database work, deployment, or broker connectivity.

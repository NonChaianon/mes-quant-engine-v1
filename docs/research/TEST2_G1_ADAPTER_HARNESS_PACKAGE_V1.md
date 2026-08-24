# Test 2 G1 — Adapter and Harness Package V1

**Status:** `OWNER_APPROVED_IMPLEMENTATION / SYNTHETIC_TESTS_ONLY`

**Implementation owner:** Human Owner

**Patch authorship and adversarial review:** Codex + Claude Code

## Exact base and boundary

```text
base commit                         29d95a97814c60413b0b13cfee61155b43552ba9
branch                              research/test2-l0-implementation-v1
observed access during G0/G1        L0 / SYNTHETIC_ONLY
real TRAIN target/path rows read    0
Validation rows read                0
Final Test rows read                0
real models fitted                  0
database introduced                 no
```

G1 prepares code for later separately authorized gates. It does not execute canonical
artifact preflight, decode DBN, read real Parquet rows, construct a real target, or fit a
real model.

## Allowed files

- `docs/research/TEST2_G0_FORWARD_REMEDIATION_RECORD_V1.md`
- `docs/research/TEST2_G1_ADAPTER_HARNESS_PACKAGE_V1.md`
- `src/mes_quant/exploration/test2_path_contract.py`
- `src/mes_quant/exploration/test2_request_set.py`
- `src/mes_quant/exploration/test2_evaluation.py`
- `src/mes_quant/exploration/test2_diagnostics.py`
- `src/mes_quant/exploration/test2_l1_harness.py`
- `src/mes_quant/exploration/test2_run_context.py`
- `tests/test_test2_request_set.py`
- `tests/test_test2_evaluation.py`
- `tests/test_test2_diagnostics.py`
- `tests/test_test2_l1_harness.py`
- `tests/test_test2_run_context.py`

`test2_target.py`, `test2_stats.py`, Test 1, feature-generation, manifests, references,
dependencies, CLI, pipeline, Validation, and Final-Test files remain byte-identical.

## G1 guarantees

1. The complete ordered request identity is hashed incrementally before a provider may
   expose any numeric path bar. The 60-times expansion is streamed rather than retained as
   roughly 1.54 million Python objects.
2. Only outer-TRAIN parents and timestamps before the outer-Validation boundary can be
   sealed. Validation and Final-Test lookup counters are recomputed from the sealed
   decisions before every provider call and must remain zero.
3. TRAIN Parquet readers push the `outer_partition == TRAIN` predicate into the physical
   read. Prepared frames reject role, time, instrument, decision-set, and availability
   mismatches.
4. A native decoded instrument must match the decision's expected instrument before it is
   normalized to the target contract's `MES` identifier. A mismatch withholds that minute,
   becomes `NO_SCORE / FLAT`, and is persisted separately from an absent timestamp.
5. Target construction still uses the frozen 60 offsets, integer ticks, endpoint
   reconciliation, one barrier set, and existing first-touch implementation.
6. If filtered Cell 12 TRAIN evidence is supplied later, recomputed path high/low and long
   MFE/MAE must reconcile exactly on the tick grid.
7. Volatility grids use fold-TRAIN, pre-target, finite `realized_vol_60m`, linear quantiles,
   retained duplicate edges, and `searchsorted(..., side="right")`. Empty buckets and a
   missing-decile bucket remain visible.
8. Coverage is recorded before ambiguity/no-score exclusion over all OOF rows. A row with
   an invalid feature vector is counted as `NO_SCORE / FLAT` (and placed in the missing
   volatility bucket when that value is unavailable). Prior, nuisance, and full models
   then receive one identical retained index.
9. The two fixed economic policies are diagnostics only: release at first touch and reserve
   capacity to +60 minutes. A touch is observable at the close of its one-minute bar;
   threshold 0.5 applies and USD 4.97 is charged once per executed trade.
   Ambiguous/no-score rows are never executed.
10. Metadata identity preflight distinguishes byte hashes and Parquet-footer schema from
    numeric content hashes. It may not call a file hash or footer result a recomputed
    ordered-feature or decoded-frame value hash.

## Later gates remain separate

```text
G2  canonical metadata preflight
    byte SHA-256 + Parquet footer + Cell14/frozen-manifest binding only
    no numeric row values and no model fit

G3  explicit Owner authorization required again
    decode canonical DBN and recompute its value hash; preserve the Cell 14
    release-manifest declaration of the ordered feature-content hash without
    mislabeling it as a G2 numeric recomputation;
    physical TRAIN-only reads; target construction; Cell12 reconciliation;
    support gate; then at most the two frozen fits if support passes
```

No G1 pass automatically invokes G2 or G3. No database, dependency, third model, tuning,
second barrier, Validation opening, Final-Test opening, deployment, or broker connection is
within this package.

## Exit gate

- targeted and full tests pass;
- Ruff passes;
- the changed-file firewall matches this allowlist;
- no `.DS_Store` is staged;
- Claude Code returns no blocker/high on the exact final diff;
- the Owner applies, tests, commits, and pushes the reviewed patch.

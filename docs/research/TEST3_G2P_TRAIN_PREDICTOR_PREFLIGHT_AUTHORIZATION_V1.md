# Test 3 G2-P TRAIN Predictor-Domain Preflight Owner Authorization V1

Authorization ID: AUTH_TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_20260824

Authorization token: OWNER_AUTHORIZED_TEST3_G2P_TARGET_BLIND_TRAIN_PREFLIGHT_20260824

Status: OWNER AUTHORIZED / TARGET-BLIND TRAIN PREDICTOR READ / ONE CONSUMPTION

Owner decision date: 2026-08-24 (Asia/Bangkok)

Protocol ID: MES_TEST3_RV60_HAR_RISK_EDGE_V1

Frozen protocol commit: 7c17b292958aeb8252f9c0911ef7028b6071cdbb

Ratification record commit: 05f569f3ee2093461b5330e8069cb2fd0099d3b1

Authorized base and G2 evidence commit: 21c42de47deeb8fac1da9208fdbc8ad4fa6369ca

Execution branch: research/test3-g2p-predictor-preflight-v1

## Owner instruction and repository stance

The Owner authorizes Codex to prepare, test, commit, push, adversarially review, and execute
the bounded Test 3 G2-P target-blind TRAIN predictor-domain preflight. Claude Code must be
used heavily as a read-only adversarial reviewer. The exact pushed implementation commit
observed by the runner is the execution identity and must be recorded with its Git tree and
local/upstream equality.

Draft PR #47 and the L0/G2 branches remain unmerged. This authorization grants no merge or
CI-remediation authority.

## Authorized row-value surface

Only the following canonical artifacts may be opened after authorization consumption:

1. Cell 8 split assignments: byte identity plus outer-TRAIN control fields
   `decision_id`, `decision_time`, `instrument_id`, `outer_partition`, `role_wf_2022`, and
   `role_wf_2023` for exact cross-binding only;
2. Cell 14 point-in-time features: byte identity plus the same outer-TRAIN control fields
   and exactly `realized_vol_60m`, `realized_vol_120m`, and `realized_vol_240m`.

The Parquet reader must receive `outer_partition == TRAIN` in the same projection call that
requests the allowlisted columns. Python application code may receive only the frozen 25,685
TRAIN rows and must then assert their partition, order, uniqueness, time boundary, and exact
Cell 8/14 cross-binding. Cell 10, Cell 12, the raw DBN, decoded data, target/path columns,
all other Cell 14 feature values, and outer-Validation/Final-Test rows are forbidden.

The required `*_ROWS_READ` counters mean rows exposed by the application-level projection.
They do not claim that a Parquet engine avoided reading compressed bytes or internally
decoding pages within the single mixed row group. That lower-level property is not
observable from the current canonical artifact. The implementation must make this counter
semantics explicit and must never expose a Validation predictor value to Python code.

Pinned source totals are exhaustive: Cell 14 `31,193 = 25,685 TRAIN + 5,508 VALIDATION`;
Cell 8 `39,847 = 25,685 TRAIN + 5,508 VALIDATION + 8,654 FINAL_TEST`. Application-exposed
TRAIN rows must preserve the frozen strict chronological source order and end before the
2024 outer-Validation boundary.

The complete ordered G2-P ledger must classify every exposed TRAIN identity as exactly one
of `PREDICTOR_USABLE`, `PREDICTOR_UNUSABLE`, `PREDICTOR_NONFINITE`, or
`PREDICTOR_NONPOSITIVE`. Arrow validity/null bitmaps must be inspected before numeric
conversion. A null in any exact predictor is declared missingness and emits
`PREDICTOR_UNUSABLE`; a present NaN or infinity remains present and emits
`PREDICTOR_NONFINITE`. Among present values, nonfinite takes precedence over nonpositive;
otherwise a present finite value less than or equal to zero emits `PREDICTOR_NONPOSITIVE`.
The global `feature_row_usable` flag must not be read or used. No value may be imputed,
floored, clipped, transformed for fitting, or persisted.

The durable aggregate record may contain status counts, row counts, ordered identity and
identity/status hashes, source identities, counters, and stage disposition only. It must not
persist a per-row identity/status ledger, raw predictor value, distribution, quantile,
minimum, maximum, mean, or variance. A later separately authorized G3-P must reconstruct the
ledger from the same pinned source and reproduce the sealed hashes before common-mask use.

The named hash projection is `MES_TEST3_PREDICTOR_LEDGER_PIPE_UTF8_V1`, identical to the L0
synthetic contract pinned at `b16d025dd84b590a8a441c05232e6f761ee7f9bf`. Normalize each decision time with
`astimezone(UTC).isoformat()` (therefore UTC is rendered with `+00:00`), preserve the verified
strict source order, encode UTF-8 with no header or BOM, use `|` separators, and terminate
every row with LF. The identity hash consumes `decision_id|decision_time\n`; the
identity/status hash consumes `decision_id|decision_time|status\n`. Decision IDs containing
`|`, CR, or LF are invalid.

## One-consumption boundary

Repository, authorization-document, G2-evidence, and cheap deterministic checks occur before
artifact access. The runner then creates an authorization-SHA-scoped reservation with
exclusive create. Any subsequent technical failure consumes this authorization and may not
be retried without new Owner authorization. A completed predictor ledger is durable whether
it passes or contains a frozen terminal predictor failure code.

A pinned source-byte, TRAIN identity/control, order, row-count, Arrow-null-contract, or ledger
cross-binding mismatch is protocol-invalid evidence, not a generic technical failure. After
reservation it must publish a scrubbed create-once typed terminal summary with exact
`terminal_disposition=INVALID_EVIDENCE`, a bounded mismatch category, required Owner cause
audit, `TARGET_SPACE_003` still `LOCKED / RESERVED` and unconsumed, and Final Test `SEALED`.
Structurally unreachable target/fit/Cell 10/Cell 12/DBN counters remain zero. If the projection
itself violates row-count, requested-column, or TRAIN-only assertions, affected non-TRAIN and
nonallowlisted-column counters must read `NOT_ATTESTED_DUE_TO_INVALID_PROJECTION` and
Validation and Final Test must read `ACCESS_BREACH_FAIL_CLOSED`; the record must never claim
an unverified zero, `UNOPENED`, or `SEALED`. Unexpected I/O/runtime faults remain the separate
generic consumed technical-failure path.

The exact Owner execution command is pinned below. It uses the repository interpreter with
isolated safe-path and bytecode-disabled flags and the canonical repository-local artifacts;
the runner must reject every other artifact path before authorization consumption.

```text
.venv/bin/python -I -B tools/run_test3_g2p_preflight.py \
  --gate G2P_TEST3_TARGET_BLIND_TRAIN_PREDICTOR_PREFLIGHT \
  --authorization-token OWNER_AUTHORIZED_TEST3_G2P_TARGET_BLIND_TRAIN_PREFLIGHT_20260824 \
  --cell8 "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/cache/source_v1/cell8_purged_split_assignments_v1.parquet" \
  --cell14-features "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/runs/cell14_20260809T175203Z/cell14_development_point_in_time_features_v1.parquet"
```

The thin runner must verify isolation before importing project or third-party modules. The
main runner must recheck isolation, exact repository/venv module origins, PyArrow `18.1.0`,
forbidden scientific/execution modules, and no-follow dir-FD path traversal before reservation
and throughout artifact use. `pandas` is imported transitively by the tracked
`mes_quant.exploration` package initializer but is not called or referenced by the G2-P module;
the AST/projection firewalls and exact tracked-module origins enforce that boundary. Input and
evidence paths may not contain symlink components; evidence is create-once and fsynced.

## Exact additive allowlist

Only these five files may differ from the authorized base before execution:

1. `docs/research/TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_AUTHORIZATION_V1.md`
2. `docs/research/TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_PACKAGE_V1.md`
3. `src/mes_quant/exploration/test3_g2p_preflight.py`
4. `tests/test_test3_g2p_preflight.py`
5. `tools/run_test3_g2p_preflight.py`

No pre-existing file or dependency may change.

## Required zero boundary

Target/path rows, target construction, fold fits, fitted models, bootstrap, outer Validation,
Final Test, Cell 10/12 rows, raw DBN messages, and non-allowlisted Cell 14 value columns must
remain zero or unopened. Both Cell 8 and Cell 14 must expose zero non-TRAIN control rows to
Python. Live execution remains disabled.
`TARGET_SPACE_003` remains `LOCKED / RESERVED` and is not consumed because G2-P reads no
numeric target or path value.

## Evidence and next authority

The package must be committed and pushed before the one-shot execution. After consumption,
the create-once reservation plus either the aggregate G2-P record or a scrubbed technical
failure summary must be force-added in a separate evidence commit and pushed promptly. Raw
logs stay local. Completion opens no G3-P, G3-F, Validation, Final Test, database, UI, live,
broker, retry, repair, or merge authority.

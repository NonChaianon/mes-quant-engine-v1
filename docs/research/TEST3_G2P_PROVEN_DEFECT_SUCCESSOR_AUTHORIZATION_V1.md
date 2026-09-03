# Test 3 G2-P Proven-Defect Successor Owner Authorization V1

Authorization ID: `AUTH_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824`

Authorization token: `OWNER_AUTHORIZED_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824`

Gate literal: `G2P_TEST3_SINGLE_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT`

Repair-lineage ID: `MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1`

Status: `OWNER AUTHORIZED / ONE SAME-SLOT SUCCESSOR / TARGET-BLIND TRAIN ONLY`

Owner decision date: 2026-08-24 (Asia/Bangkok)

Proof/amendment commit/tree: `2d4fccf4ac2040e8e908bfadda27b81b3663afad` / `9b07390a40a4720fe0a64c97cb982cf0345a8207`

Execution branch: `research/test3-g2p-proven-defect-successor-v1`

## Owner instruction

The Owner authorizes the Test 3 G2-P single proven-defect repair lineage from exact evidence
commit `f0a3387f077ac30c99287601adeb81014068ff08`: create synthetic proof and an additive
amendment, change only the minimum delimiter handling, issue a new authorization, and run
one successor one-shot. Target/path access, fit, Validation, Final Test, and merge remain
forbidden before the repaired preflight passes.

The synthetic proof and additive amendment were committed and pushed first at `2d4fccf`.
That commit is the exact authorized base for this successor package. This authorization is
effective only for one direct-child package of that proof commit satisfying every gate below.

## Proven defect and minimum repair

The predecessor package `485bfa1` rejected an internal `|` in `decision_id`, although frozen
L0 accepts every non-empty identity, canonical Cell 7 constructs identities containing
`|instrument_id=`, and the frozen protocol did not add a delimiter ban. The predecessor
one-shot stopped at evidence commit `f0a3387` with
`DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT` before target/path/common-mask/fit access.

The only causal code change is to stop rejecting `|`. CR and LF remain rejected. The raw
identity, hash projection ID, UTF-8 serialization, pipe separators, UTC time rendering,
status strings, LF row termination, source order, and every scientific contract remain
byte-semantically unchanged. No identity split, escape, rewrite, or new hash version is
authorized.

## Predecessor evidence binding

Before consuming the successor authorization, the runner must verify all of the following:

- predecessor package commit/tree `485bfa16a6567b5c54e91b7cc72e7f1be58775a9` /
  `86e7f382586d0155ec058a148a83be858768cf4d`;
- predecessor evidence commit/tree `f0a3387f077ac30c99287601adeb81014068ff08` /
  `ac415152ba6eca60c50907c7fe1dc42460bf7a4b`;
- predecessor authorization/package SHA-256 `2651c917a1480a74dfa7300cc6b11a3208828b41b74f726240224dcb783cce98` /
  `584cd0623463e79803b69df15646e9e30db1a78944e067d0bff87d69409b11c2`;
- predecessor reservation/failure SHA-256 `2cf1ce922a012045af9959265b613df662727e268c8797f9555ee19072c9c68c` /
  `9b9f7f7824c89af2fa32de3cda00cfa38a519795a6c88bae6a6201d89717a439`;
- exact invalid-evidence category, zero protected counters, unconsumed target space,
  Validation `UNOPENED`, and Final Test `SEALED`.

The original files are immutable and may not be overwritten, amended in place, deleted, or
republished as a different fact.

## Authorized value surface

The successor retains the predecessor G2-P boundary verbatim: after reservation it may read
only the pinned Cell 8 outer-TRAIN control projection and pinned Cell 14 outer-TRAIN control
plus `realized_vol_60m`, `realized_vol_120m`, and `realized_vol_240m`. It may not read any
target/path value, Cell 10/12 row, raw DBN message, non-allowlisted Cell 14 value column,
outer Validation predictor value, or Final-Test value. It may not construct `RV_FWD_60`, a
common mask, a fit design, a forecast, coefficient, QLIKE result, or bootstrap result.

## Exact one-successor reservation

Before either Parquet file is opened, the runner must exclusively create:

```text
artifacts/exploration/test3/g2p/repair/
MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1.consumed.json
```

The record binds this authorization document/token, proof commit, execution commit/tree,
branch, predecessor evidence hashes, `successor_ordinal=1`, and `successor_limit=1`.
Existing-file collision fails before artifact access. No later authorization or token may
mint another reservation for this lineage.

## Exact package allowlist

The execution commit must be one direct child of `2d4fccf` and differ in exactly these four
paths:

1. `docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_AUTHORIZATION_V1.md`
2. `docs/research/TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_PACKAGE_V1.md`
3. `src/mes_quant/exploration/test3_g2p_preflight.py`
4. `tests/test_test3_g2p_preflight.py`

The proof/amendment files, frozen protocol/budget/L0, predecessor documents/evidence, and
`tools/run_test3_g2p_preflight.py` must remain byte-identical to the proof commit.

## Exact Owner command

```text
.venv/bin/python -I -B tools/run_test3_g2p_preflight.py \
  --gate G2P_TEST3_SINGLE_PROVEN_DEFECT_SUCCESSOR_PREFLIGHT \
  --authorization-token OWNER_AUTHORIZED_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824 \
  --cell8 "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/cache/source_v1/cell8_purged_split_assignments_v1.parquet" \
  --cell14-features "/Users/nonchaianon/Documents/Codex/MES_Quant_Engine_V1/artifacts/runs/cell14_20260809T175203Z/cell14_development_point_in_time_features_v1.parquet"
```

The package must pass targeted/full tests, Ruff, exact ancestry/allowlist/source firewalls,
local/upstream equality, and independent Claude Opus exact-package review before this command.

## Terminal rule and next authority

If the successor passes, `TARGET_SPACE_003` remains `LOCKED / RESERVED` and unconsumed;
G3-P remains separately unauthorized. If the successor fails for any reason, Test 3 becomes
terminal with no retry, repair, replacement, or additional successor. Attested protected
counters remain zero; projection breaches must use the existing fail-closed not-attested
states rather than invent zeroes.

This authorization grants no target/path access, target construction, fit, bootstrap,
economic diagnostic, Validation, Final Test, database, UI, live, broker, PR merge, or Issue
#48 implementation authority.

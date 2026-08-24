# Test 3 G2-P Proven-Defect Repair Amendment V1

Amendment ID: `MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1`

Status: `OWNER AUTHORIZED / SYNTHETIC PROOF REQUIRED / SAME-SLOT SUCCESSOR ONLY`

Owner decision date: 2026-08-24 (Asia/Bangkok)

Frozen protocol ID: `MES_TEST3_RV60_HAR_RISK_EDGE_V1`

Frozen protocol/budget commit: `7c17b292958aeb8252f9c0911ef7028b6071cdbb`

Failed predecessor package commit/tree: `485bfa16a6567b5c54e91b7cc72e7f1be58775a9` / `86e7f382586d0155ec058a148a83be858768cf4d`

Immutable predecessor evidence commit/tree: `f0a3387f077ac30c99287601adeb81014068ff08` / `ac415152ba6eca60c50907c7fe1dc42460bf7a4b`

## 1. Owner authorization incorporated without expansion

The Owner authorized this exact bounded lineage from `f0a3387`: create synthetic proof and
an additive amendment, repair only the minimum delimiter handling, issue a new
authorization, and execute at most one successor one-shot. Target/path access, fitting,
Validation, Final Test, and merge remain forbidden before the repaired predictor preflight
passes.

This amendment does not authorize any new target, predictor, model, row disposition, hash
scheme, search slot, or scientific choice. The original authorization, reservation, failure
summary, package, and execution evidence remain immutable.

## 2. Exact observed failure

The predecessor one-shot consumed
`AUTH_TEST3_G2P_TRAIN_PREDICTOR_PREFLIGHT_20260824` and stopped with:

```text
terminal_disposition=INVALID_EVIDENCE
invalid_evidence_category=DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT
target_space_state=LOCKED / RESERVED
target_space_consumption_status=NOT_CONSUMED_TARGET_BLIND_PREDICTOR_PREFLIGHT
validation_status=UNOPENED
final_test_status=SEALED
```

The predecessor reservation file SHA-256 is
`2cf1ce922a012045af9959265b613df662727e268c8797f9555ee19072c9c68c`; the typed failure
file SHA-256 is `9b9f7f7824c89af2fa32de3cda00cfa38a519795a6c88bae6a6201d89717a439`.
Every protected target/path/fit/bootstrap counter in that failure is zero.

## 3. Synthetic proof of implementation nonconformance

The proof is target-blind and data-free. It is implemented in
`tests/test_test3_g2p_proven_defect.py` and must pass before a successor package exists.

It binds these exact historical bytes:

- frozen L0 `src/mes_quant/exploration/test3_design.py @ b16d025`, SHA-256
  `44e398497c57559fd8700daa33f087ce290aa5264cbd143d7ea4cd2311581ae9`;
- predecessor G2-P `src/mes_quant/exploration/test3_g2p_preflight.py @ 485bfa1`, SHA-256
  `015c35dc3673c2741b2cd2eaedb295e129f3f4b45ae382f1b2e5e83e248cf935`.

For the synthetic identity `SYNTH|ID`, frozen L0 accepts the non-empty identity and hashes
the raw identity under the frozen pipe serialization. The predecessor G2-P function rejects
the same identity with `DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT`. Canonical source code
also constructs decision identities with the literal `|instrument_id=` component. Therefore
the stop is an implementation failure to conform to the frozen identity contract, not an
observed predictor, target, or source-data state.

## 4. Minimum causal amendment

The only scientific-path change permitted is:

```text
predecessor delimiter rejection: |, CR, LF
successor delimiter rejection:      CR, LF
```

An internal pipe remains part of the decision identity byte-for-byte. The successor must not
split, trim, escape, normalize, re-encode, or otherwise transform the identity. The hash
projection ID, UTF-8 payload, pipe separators, UTC ISO formatting, LF row terminator, source
order, and status order remain unchanged. CR and LF remain fail-closed because changing them
is not causally required by the proven defect.

## 5. One-successor mechanics

The successor must use a new authorization ID/token and one fixed repair-lineage reservation:

```text
artifacts/exploration/test3/g2p/repair/
  MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1.consumed.json
```

Exclusive creation of that fixed file occurs before predictor-artifact opening and binds
`successor_ordinal=1` and `successor_limit=1`. Its existence bars every later attempt,
including an attempt carrying a different token. The runner must verify the exact predecessor
reservation/failure bytes and semantics before consuming the successor authorization.

If the successor passes, `TARGET_SPACE_003` remains `LOCKED / RESERVED` and unconsumed;
G3-P still needs separate authorization. If the successor fails for any reason, Test 3 is
terminal with no retry or further successor. Validation remains unopened and Final Test
remains sealed whenever the projection boundary is attested.

## 6. Authority boundary

This proof/amendment commit authorizes preparation only. Execution requires the separately
bound successor authorization/package, exact tests and firewalls, pushed local/upstream
equality, and independent Claude Opus exact-package GO. It grants no target/path read,
`RV_FWD_60` construction, fit, bootstrap, economic diagnostic, Validation, Final Test,
database, live, broker, PR merge, or Issue #48 implementation authority.

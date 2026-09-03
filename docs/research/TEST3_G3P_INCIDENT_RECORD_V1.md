# Test 3 G3-P Procedural Incident Record V1

Incident ID: `MES_INCIDENT_TEST3_G3P_20260825`

Status: **DRAFT / OWNER REVIEW / ADDITIVE / NO AUTHORITY**

Incident evidence commit/tree: `b89a5453a63c06122001e849469fb9a106d94acd` /
`e8983458167af7420a7929fb9bbc7522966d74b2`

Code-only execution commit/tree: `573b8c93244dd823fbe12bced87ce930005e0dcb` /
`f38728ff355112c3027821d4982cb80dd2799f34`

Companion hardening protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1` at
`docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md`

Companion Clause Packet template: `MES_CLAUSE_PACKET_TEMPLATE_V1` at
`docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md`

This record is additive. It does not rewrite, relabel, repair, or supersede the
execution-authorization reservation evidence, failure evidence, ratified Test 3 protocol,
project hypothesis budget, or G3-P authorization.
It grants no implementation, CI, data, target, fit, Validation, Final Test, merge, or new
research authority.

## 1. Exact conclusion

Test 3 produced **no scientific result**. The volatility-memory hypothesis remains untested.
The attempted G3-P execution was procedurally nonconforming and stopped on an implementation
contract mismatch at a stage that the verified witness chain places before target access
(Section 2.2, derived). Closure reflects execution-engineering defects and a governance
nonconformance, not evidence about volatility predictability on MES.

Canonical future-facing wording (reuse verbatim, including the derivation qualifier):

> Closed procedurally; hypothesis untested; no target consumption witness was produced and
> the verified witness chain supports the derived conclusion that zero numeric target values
> were read (see Section 2.2 — derived from witness ordering, not from a direct counter).
> Closure reflects execution defects and a governance nonconformance, not evidence about
> volatility predictability.

No record, summary, research register, or downstream presentation may describe Test 3 as a
negative volatility forecast result, `NOT_INTERESTING_ENOUGH`, underpowered science, or a
failed TRAIN continuation gate.

## 2. Immutable machine facts and bounded derivations

### 2.1 Bound machine facts (`F_MACHINE`)

Every row below is emitted by the governed attempt or observed from its committed bytes. All
digests are SHA-256 of complete file bytes at evidence commit
`b89a5453a63c06122001e849469fb9a106d94acd`.

In this table, **execution-authorization reservation file** means
`artifacts/exploration/test3/g3p/authorization/5be7e82b904c9057639ff17af39b4c0627c0c937cecd84f979eb1b37bc1653eb.consumed.json`;
**failure file** means the same path stem ending in `.failure.json`.

| Fact | Exact observation | Bound evidence source |
| --- | --- | --- |
| Branch at evidence close | `research/test3-g3p-pre-fit-v1` | execution-authorization reservation field `branch` |
| Authorization document SHA-256 | `5be7e82b904c9057639ff17af39b4c0627c0c937cecd84f979eb1b37bc1653eb` | `docs/research/TEST3_G3P_TRAIN_PREFIT_AUTHORIZATION_V1.md` |
| Reservation file SHA-256 | `4c83a52f053974e148febd61471101e17439f5366b247166f55f0f45547ce092` | `artifacts/exploration/test3/g3p/authorization/5be7e82b904c9057639ff17af39b4c0627c0c937cecd84f979eb1b37bc1653eb.consumed.json` |
| Typed failure file SHA-256 | `e623a4c9becd8c5fa7f84c59b994588e883337c7b4ff2c6e1d061cdf18239deb` | `artifacts/exploration/test3/g3p/authorization/5be7e82b904c9057639ff17af39b4c0627c0c937cecd84f979eb1b37bc1653eb.failure.json` |
| Committed G3-P authorization evidence file set | exactly the execution-authorization reservation and typed failure JSON files bound above | Git tree at the bound evidence directory / commit |
| Failure category | `EARLY_CLOSE_SESSION_TYPE_INVALID` | failure field `invalid_evidence_category` |
| Failure status | `PROTOCOL_INVALID_EVIDENCE_BEFORE_TARGET_ACCESS_NO_RETRY` | failure field `status` |
| Request-set witness | absent | failure field `request_set_witness_present=false` |
| Target-space consumption witness | absent | failure field `target_space_consumption_witness_present=false` |
| Witness-chain integrity | `VERIFIED` | failure field `witness_chain_integrity` |
| Real model/fold fits | `0 / 0` | failure fields `real_models_fitted` / `real_fold_fit_calls` |
| Bootstrap/economic calls | `0 / 0` | failure fields `real_bootstrap_replicates` / `economic_diagnostic_calls` |
| Validation / Final | `ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED` / same | failure fields `validation_status` / `final_test_status` |
| Raw error message committed | `false` | failure field `raw_error_message_committed` |
| Target-space state string | `LOCKED / RESERVED` | failure field `target_space_state` |
| Execution-authorization reservation status string | `CONSUMED_BEFORE_ANY_SOURCE_ARTIFACT_ACCESS` | execution-authorization reservation field `status` |
| Test 3 status string | `TERMINAL_NO_RETRY` | failure field `test3_status` |

### 2.2 Deterministic derivations (`D_DERIVED`)

The failure artifact does not contain direct `target_values_read` or `targets_constructed`
counters. The following bounded conclusion is derived from the verified witness ordering:

1. the execution-authorization reservation status is
   `CONSUMED_BEFORE_ANY_SOURCE_ARTIFACT_ACCESS`;
2. `witness_chain_integrity` is `VERIFIED`;
3. both `request_set_witness_present` and `target_space_consumption_witness_present` are
   `false`;
4. the terminal status is `PROTOCOL_INVALID_EVIDENCE_BEFORE_TARGET_ACCESS_NO_RETRY`;
5. the committed evidence directory contains only the bound execution-authorization
   reservation and typed failure JSON files, neither of which contains a raw target/path
   value or identity.

Therefore, within the governed Test 3 witness model, numeric target/path access and target
construction did not occur. This is a deterministic evidence-chain conclusion, not a direct
counter claim. It assumes the verified runner witness ordering and absence flags are sound
despite the separate consumer-contract defect; the committed evidence cannot independently
prove that emitter assumption. Absence of target consumption does not restore execution
authority.

## 3. Two orthogonal ledgers

The incident exposed a category error between two independent state machines:

| Ledger | Question | Incident state |
| --- | --- | --- |
| Target-access ledger | Were numeric target/path values read or `RV_FWD_60` targets constructed? | `LOCKED_RESERVED_NOT_CONSUMED` |
| Execution-authority ledger | Does any valid authorization lineage remain available? | `TERMINAL_NO_RETRY` |

Two-ledger draft-schema mapping (illustrative; not a Section 7.1-conformant record instance):

```text
schema_version = MES_EXECUTION_RECORD_SCHEMA_V1
record_kind = STAGE_TERMINAL
target_access_state = LOCKED_RESERVED_NOT_CONSUMED
execution_authority_state = TERMINAL_NO_RETRY
execution_authorization_reservation_consumed = true
```

`LOCKED / RESERVED` answers only the first question. It is not a retry, repair, replacement,
or execution entitlement. The ratified budget's single repair-lineage consumption reached
`1/1` through the G2-P successor. The G3-P authorization created no new repair. No Test 3b or
other same-slot execution is authorized by the current documents.

The normalized ledger values in the Section 3 table are later governance mappings under
draft schema `MES_EXECUTION_RECORD_SCHEMA_V1`; those field roles are not present in the
historical evidence schema. `LOCKED_RESERVED_NOT_CONSUMED` is mapped from the exact machine
state plus absent consumption witness. `TERMINAL_NO_RETRY` byte-matches the historical
`test3_status`, but assigning it to the new `execution_authority_state` field remains a later
schema mapping.

The target-access mapping carries the complete Section 2.2 derivation qualifier, including
the unproven emitter-soundness assumption. The table or mapping must never be quoted as a
direct counter fact or separated from that qualifier.

Historical `ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED` and draft-schema
`ACCESS_NOT_ATTESTED_FAIL_CLOSED` are different exact values in different schemas. They must
never be normalized into one another by token similarity.

## 4. Incident chronology and classes

### 4.1 Downstream validation drift — pipe delimiter

Frozen L0 accepted non-empty decision identities, including pipe-bearing values. Original
G2-P added a pipe rejection that the frozen contract did not impose. The original G2-P run
stopped at commit `f0a3387f077ac30c99287601adeb81014068ff08`, tree
`ac415152ba6eca60c50907c7fe1dc42460bf7a4b`; synthetic proof and the sole authorized
defect-repair lineage produced the bounded successor and PASS evidence at commit
`a1ea24445f575c5d267d6bfe410cc7acd034b74f`, tree
`ce20f1ecafb3a58fece522cb04048ffef9b628a8`.

Root cause: a downstream stage strengthened a shared identity invariant outside the frozen
validator and outside L0 coverage.

### 4.2 Schema-depth gap — `int8` versus boolean

The frozen Cell 14 feature registry specifies `early_close_session` as `int8`, and the
canonical builder materializes integral `0/1`. Test 3 G2 verified schema names but not the
ordered Arrow type/nullability contract. G3-P then accepted only `bool`/`np.bool_` scalars.
Its synthetic tests passed normalized booleans directly and did not rehearse an Arrow
`int8` consumer boundary.

Root cause: the producer contract was correct, but metadata verification was too shallow
and the real consumer adapter had no type-correct synthetic rehearsal.

### 4.3 Unenforced release predicate — reviewer verdict

The G3-P authorization required an independent Claude Opus exact-package review before
execution. The exact-byte Claude run returned no verdict after read-only tool denials and a
timeout. Two Codex reviewer GO reports did not satisfy the explicitly named predicate, yet
execution began and consumed the execution-authorization reservation.

Root cause: the reviewer prerequisite existed only as human-readable text. The runner did
not require a trusted, package-bound verdict attestation before execution-authorization
reservation consumption. Codex advanced the execution path and failed to stop or escalate
the unmet named prerequisite; the Owner initiated execution before the missing verdict was
resolved. This was a joint procedural nonconformance. The Owner remains accountable for the
execution decision, and Codex remains accountable for orchestration and enforcing the agreed
gate; neither responsibility displaces the other.

## 5. Impact and non-impact

- Scientific impact: none may be inferred because the target, fit, loss, and inference
  surfaces were never reached.
- Search-accounting impact: `TARGET_SPACE_003` remains unconsumed, but Test 3 is
  procedurally terminal under its current authorization and budget lineage.
- Safety impact: the verified witness order supports the bounded derived conclusion that
  target access did not occur, and no raw target/path value, identity, or protected output
  was committed. Validation and Final access remain
  `ACCESS_STATUS_NOT_ATTESTED_FAIL_CLOSED`; this record makes no broader non-access or
  non-leakage claim.
- Governance impact: the execution must be described as nonconforming; the missing review
  gate requires a machine-enforced control before any future scientific execution.
- Historical impact: the committed execution-authorization reservation and failure evidence
  remain immutable.

## 6. Corrective-action boundary

The drafted no-data hardening design — not yet authorized for implementation — covers:

1. one versioned, hash-bound shared boundary validator for true cross-stage invariants;
2. ordered logical schema type/nullability checks and type-correct synthetic consumer
   rehearsal before a numeric stage;
3. a trusted reviewer attestation checked before execution-authorization reservation
   consumption;
4. separate target-access and execution-authority fields in every terminal record;
5. fast regression and full synthetic-ladder rehearsals, including a successful happy path.

These actions harden future execution infrastructure. They do not repair, reopen, rerun, or
reinterpret Test 3 and do not consume a target-space hypothesis slot.

## 7. Current authorization and next gate

Owner instruction, 2026-08-25:

> อนุมัติ Steps 1–2 แบบ docs-only: จัดทำ additive incident record, hardening protocol และ
> Clause Packet template; ห้ามแก้ code, CI, Issue #48, PR #47, อ่าน data, fit, Validation,
> Final Test หรือ merge

Implementation requires a later exact Owner authorization after these documents are
reviewed and ratified. Step 5 or any Test 3b decision is deliberately outside this record.

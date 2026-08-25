# Clause Packet Template V1

Template ID: `MES_CLAUSE_PACKET_TEMPLATE_V1`

Status: **DRAFT / OWNER REVIEW / ADDITIVE / NO AUTHORITY**

Draft base commit/tree: `b89a5453a63c06122001e849469fb9a106d94acd` /
`e8983458167af7420a7929fb9bbc7522966d74b2`

Canonical repository path: `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md`

Companion incident record: `MES_INCIDENT_TEST3_G3P_20260825` at
`docs/research/TEST3_G3P_INCIDENT_RECORD_V1.md`

Companion hardening protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1` at
`docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md`

Purpose: bind every clause-dependent external review question to exact repository text so a
reviewer working from a snapshot cannot silently substitute memory, paraphrase, or another
version. A completed packet is evidence context, not an authorization or trusted reviewer
attestation.

---

## 0. Operating mode

Every completed packet must declare exactly one closed mode:

- `LIGHT_ADVISORY`: non-authoritative advice only;
- `FULL_GOVERNED`: any review that can affect authorization, execution, source/target access,
  budget or hypothesis accounting, evidence classification/disposition, protocol
  ratification/change, CI, release, merge, or an execution-hardening exit criterion.

If impact is uncertain, use `FULL_GOVERNED`. A `LIGHT_ADVISORY` packet or response can never
authorize an action, satisfy a trusted-attestation gate, ratify text, close a governed
finding, or be upgraded in place. If its subject later becomes authority-affecting, create a
new `FULL_GOVERNED` packet.

`LIGHT_ADVISORY` uses exactly two create-once artifacts:

1. the completed packet, frozen before review and hashed only after its bytes are final;
2. exactly one separate response-or-attempt-outcome artifact that binds the packet
   ID/SHA-256 and is marked `UNTRUSTED_CONTEXT_ONLY`.

It requires no dispatch receipt, Owner closeout, closeout receipt, or external anchor.
`FULL_GOVERNED` uses the complete Sections 8–11 chain. Combining a question and its later
response in one file is forbidden in both modes because it destroys proof of the reviewed
input bytes.

## 1. Packet identity

| Field | Required value |
| --- | --- |
| Packet ID | `CLAUSE_PACKET_<SUBJECT>_<YYYYMMDD>_<ORDINAL>` |
| Operating mode | `<LIGHT_ADVISORY or FULL_GOVERNED>` |
| Prepared UTC | `<ISO-8601 UTC>` |
| Prepared by | `<identity and role>` |
| Repository | `<owner/repository or absolute local identity>` |
| Branch/ref observed | `<exact ref>` |
| Commit | `<40-hex SHA>` |
| Tree | `<40-hex SHA>` |
| Working-tree state | `<CLEAN or exact disclosure>` |
| Question boundary | `<one sentence>` |
| Authority statement | `CONTEXT ONLY / NO AUTHORITY` |
| Expected reviewer identity/role | `<exact expected identity and role>` |
| Attempt ID | `<exact unique identity>` |
| Attempt-ledger entry ID | `<FULL_GOVERNED: exact identity; LIGHT_ADVISORY: NOT_APPLICABLE>` |
| Prior/superseded packet ID and SHA-256 | `<exact identity/hash or NONE>` |
| Expected dispatch-receipt ID/path | `<FULL_GOVERNED: create-once identity; LIGHT_ADVISORY: NOT_APPLICABLE>` |
| Expected response artifact ID/path | `<create-once additive artifact identity>` |
| Expected closeout artifact ID/path | `<FULL_GOVERNED: create-once identity; LIGHT_ADVISORY: NOT_APPLICABLE>` |
| Expected closeout-receipt ID/path | `<FULL_GOVERNED: create-once identity; LIGHT_ADVISORY: NOT_APPLICABLE>` |
| Expected external-anchor ID/path | `<FULL_GOVERNED: evidence-manifest identity; LIGHT_ADVISORY: NOT_APPLICABLE>` |

## 2. Bound source files

List every file needed to answer the question. Do not cite a summary when an original
clause exists.

| Label | Repository path | File SHA-256 | Status at commit |
| --- | --- | --- | --- |
| `<label>` | `<path>` | `<64-hex SHA-256>` | `<frozen/draft/executed/etc.>` |

## 3. Verbatim clauses

Copy only the minimum complete clause needed for interpretation. Preserve wording,
punctuation, list numbering, and defined terms. Keep each source excerpt within applicable
quotation limits when the source is not project-owned.

### Clause A — `<short name>`

- Source label: `<label from Section 2>`
- Section/heading: `<exact heading>`
- Observed lines: `<start-end at bound commit>`
- Precedence: `<what this clause governs and what can override it>`

```text
<verbatim clause>
```

### Clause B — `<short name, if required>`

- Source label: `<label>`
- Section/heading: `<heading>`
- Observed lines: `<start-end>`
- Precedence: `<relationship to Clause A>`

```text
<verbatim clause>
```

## 4. Machine facts and counters

Every fact must identify its evidence source. Do not mix inference into this table.

| Fact ID | Exact fact/counter | Value | Evidence path/commit/hash | Class |
| --- | --- | --- | --- | --- |
| `F-01` | `<fact>` | `<value>` | `<source>` | `F_MACHINE` |
| `F-02` | `<fact>` | `<value>` | `<source>` | `F_DOCUMENT` |

Allowed classes:

- `F_MACHINE`: immutable machine-generated or hash-verified fact;
- `F_DOCUMENT`: verbatim fact from the bound governing document;
- `D_DERIVED`: deterministic derivation whose formula is shown;
- `E_JUDGMENT`: interpretation, prediction, or recommendation.

## 5. Known history and conflicts

- Prior decision or amendment: `<identity or NONE>`
- Superseded clause: `<exact identity or NONE>`
- Known conflicting text: `<identity or NONE>`
- Governing precedence rule: `<verbatim-bound rule or UNKNOWN>`
- Missing evidence: `<explicit list or NONE>`

If precedence is unknown, the reviewer must not infer it from recency, filename, branch, or
status summary.

## 6. Exact questions for the reviewer

1. `<question requiring textual interpretation>`
2. `<question requiring fact reconciliation>`
3. `<recommendation request, explicitly marked E_JUDGMENT>`

The packet must state whether the reviewer is asked to decide textual meaning, identify a
conflict, assess evidence sufficiency, or offer policy advice. These are different tasks.

## 7. Required response format

The reviewer must return:

1. `CLAUSE_BASE_USED`: commit, tree, file path, and SHA-256 for every relied-on source;
2. `TEXTUAL_FINDINGS`: each labeled `F_DOCUMENT` with clause citation;
3. `MACHINE_FACTS`: each labeled `F_MACHINE` with evidence identity;
4. `DERIVATIONS`: each labeled `D_DERIVED` with formula;
5. `JUDGMENTS`: each labeled `E_JUDGMENT`, including uncertainty and incentives/conflicts;
6. `CONTRADICTIONS_OR_GAPS`: exact unresolved items;
7. `VERDICT`: bounded to the question and never treated as Owner authority.

The reviewer must say `INSUFFICIENT_BOUND_TEXT` rather than fill a missing clause from
memory. A snapshot-based reviewer must disclose that limitation.

## 8. Dispatch freeze

The completed packet is frozen create-once at dispatch. After it is written and durably
synced, compute its SHA-256. In `LIGHT_ADVISORY`, the separate response records that hash. In
`FULL_GOVERNED`, a separate create-once dispatch receipt records it.

The following dispatch receipt is required only in `FULL_GOVERNED`:

| Field | Required value |
| --- | --- |
| Dispatch receipt artifact ID | `<exact identity>` |
| Packet ID and SHA-256 | `<identity; 64-hex>` |
| Dispatched UTC | `<ISO-8601 UTC>` |
| Durable-sync and dispatch mechanism | `<exact evidence>` |
| Attempt ID and attempt-ledger entry ID | `<exact identities>` |
| Attempt ordinal and bounded deadline | `<ordinal; ISO-8601 UTC>` |

After dispatch, never edit this packet to add the response, verdict, findings, or Owner
decision. A changed question, clause, package byte, reviewer identity, or deadline requires a
terminal attempt-outcome artifact for the old attempt, followed by a new packet ID/hash and
new attempt ID that binds the prior/superseded packet ID/SHA-256.

## 9. Separate additive response or attempt-outcome artifact

Every review attempt produces exactly one terminal create-once artifact:

- a response artifact when a verdict completes before the bounded deadline; or
- an attempt-outcome artifact whenever the attempt terminates without a completed verdict,
  including timeout, `NO_VERDICT`, cancellation, supersession, reviewer/package change, or
  verification-side invalidation.

It must bind:

| Field | Required value |
| --- | --- |
| Response/attempt-outcome artifact ID | `<exact identity>` |
| Attempt ID and terminal outcome class | `<identity; VERDICT or NO_VERDICT or TIMEOUT or CANCELLED or SUPERSEDED or INVALIDATED>` |
| Packet ID and packet SHA-256 | `<identity; 64-hex>` |
| Dispatch-receipt ID and SHA-256 | `<FULL_GOVERNED: identity; 64-hex — LIGHT_ADVISORY: NOT_APPLICABLE>` |
| Reviewed commit/tree and ordered file hashes | `<exact values>` |
| Reviewer-claimed identity/provider/model/role | `<exact claims>` |
| Outcome sealed UTC | `<ISO-8601 UTC>` |
| Verdict and BLOCKER/HIGH counts | `<exact values>` |
| Trust receipt/signature | `<identity or UNTRUSTED_CONTEXT_ONLY>` |

In `LIGHT_ADVISORY`, `Trust receipt/signature` must equal `UNTRUSTED_CONTEXT_ONLY` and
`Dispatch-receipt ID and SHA-256` must equal `NOT_APPLICABLE`; the response plus bound packet
SHA-256 closes the light-mode record. A further attempt requires a new packet and attempt ID.
In `FULL_GOVERNED`, every field and downstream artifact in Sections 8–11 is required.

A reviewer response arriving at or after the bounded deadline, or after an attempt-outcome
has been sealed, is not part of that closed attempt and must not create a second terminal
artifact for it. It may be retained only as `LATE_RESPONSE_UNTRUSTED_CONTEXT`; obtaining a
governed verdict requires a new packet and attempt ID.

Reviewer identity fields are claims unless authenticated by the governing trust mechanism.
The packet preparer may not infer or upgrade them.

## 10. Separate additive Owner closeout artifact — `FULL_GOVERNED` only

The closeout is a separate create-once artifact prepared only after the response or
attempt-outcome artifact is sealed:

| Field | Required value |
| --- | --- |
| Closeout artifact ID | `<exact identity>` |
| Packet ID and packet SHA-256 | `<identity; 64-hex>` |
| Dispatch-receipt ID and dispatch-receipt SHA-256 | `<identity; 64-hex>` |
| Response/attempt-outcome ID and SHA-256 | `<identity; 64-hex>` |
| Authenticated response/receipt identity | `<verified identity or NOT_VERIFIED>` |
| Findings incorporated | `<identities or NONE>` |
| Owner identity and decision | `<authenticated identity; exact decision>` |
| Authorization created | `<identity or NONE>` |
| Closeout UTC | `<ISO-8601 UTC>` |

The preparer and reviewer may not infer Owner identity, Owner approval, or authorization.
Those fields require authenticated Owner evidence.

After the closeout is written and durably synced, a separate create-once closeout receipt
must record its SHA-256. The external evidence manifest then anchors the closeout-receipt
SHA-256.

A completed Clause Packet, reviewer response, and Owner closeout remain additive. Never edit
the bound source or historical evidence to make a later interpretation appear
contemporaneous.

## 11. Trust boundary

The packet, response/attempt outcome, their hashes, and the Owner closeout do not by
themselves satisfy
`MES_EXECUTION_HARDENING_PROTOCOL_V1` Section 6. They become a trusted reviewer attestation
only if a later Owner-ratified mechanism verifies the required external signature/service
receipt, trust root, exact package binding, reviewer role, expiry, and replay protection. An
Owner-signed acceptance receipt proves Owner acceptance but does not prove provider/model
identity unless the provider also binds those claims cryptographically.

`LIGHT_ADVISORY` terminates after its separately sealed response-or-attempt-outcome and is
always `UNTRUSTED_CONTEXT_ONLY`. It may never be cited as an authorization prerequisite,
execution gate, ratification basis, governed closeout, or evidence-disposition authority.

A trusted-attestation verifier must parse the bound packet and accept only exact
`Operating mode = FULL_GOVERNED`; `LIGHT_ADVISORY`, missing, or unknown mode fails closed
before execution-authorization reservation consumption.

A light-mode response has no governed evidentiary weight. Unless a repository commit/tree or
other content-addressed store later anchors its bytes, its create-once property is operational
rather than independently verifiable; this does not weaken a gate because light mode is
forbidden from every gate.

No packet, response, closeout, or receipt may contain the SHA-256 of its own complete bytes.
In `FULL_GOVERNED`, each complete-artifact SHA-256 must be recorded by the next additive
artifact or by a separate create-once receipt. In `LIGHT_ADVISORY`, the packet SHA-256 is
recorded in the response; the response may remain unanchored only under the explicit
no-evidentiary-weight rule above. If a future design retains an internal digest field, it must
define canonical hashing that excludes that exact field; this V1 template defines no such
exception.

In `FULL_GOVERNED`, the hash chain must be unbroken and forward-only: the dispatch receipt
records the packet SHA-256; the response/attempt outcome records both the packet and
dispatch-receipt SHA-256;
the closeout records the response/attempt-outcome SHA-256; and the closeout receipt records
the closeout SHA-256. The terminal closeout-receipt SHA-256 must be anchored in an external
evidence manifest outside this artifact set. Any artifact not committed to by a later artifact
or external anchor is not verifiably create-once and may not be relied on as evidence.

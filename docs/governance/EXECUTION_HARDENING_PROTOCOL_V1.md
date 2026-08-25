# MES Execution Hardening Protocol V1

Protocol ID: `MES_EXECUTION_HARDENING_PROTOCOL_V1`

Status: **DRAFT / OWNER REVIEW / ADDITIVE / NO AUTHORITY**

Draft base commit/tree: `b89a5453a63c06122001e849469fb9a106d94acd` /
`e8983458167af7420a7929fb9bbc7522966d74b2`

Companion incident: `docs/research/TEST3_G3P_INCIDENT_RECORD_V1.md`

Companion Clause Packet template: `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md`

This is an engineering-control protocol, not a scientific hypothesis, model proposal, or
target-space amendment. Drafting it consumes no target-space slot. It grants no code, CI,
data, target, fit, Validation, Final Test, live, merge, Test 3b, or other execution authority.

## 1. Objective and scope

The protocol must prove two properties before any future scientific execution is eligible
for Owner consideration:

1. known-invalid states stop at the exact intended stage with the exact declared reason;
2. one fully synthetic happy path traverses the complete governed ladder and seals evidence
   successfully without becoming confusable with real scientific evidence.

The future implementation is divided into:

- **Tier 1 — fast contract regression:** deterministic, synthetic-only tests suitable for
  every commit in CI;
- **Tier 2 — full synthetic dress rehearsal:** one complete L0 -> G2 -> G2-P -> G3-P ->
  G3-F lifecycle, including preconditions, reservations, bounded synthetic fits, evidence
  sealing, and registry rejection controls.

Both tiers must use the same versioned boundary contracts and production consumer adapters.
Test-only code may supply synthetic inputs and rehearsal authority but may not bypass the
predicate or serialization code being tested.

## 2. Non-goals and prohibitions

This protocol does not:

- reopen, repair, rerun, or reinterpret Test 3;
- authorize Test 3b, Test 4, a new evidence class, or a budget override;
- read any real DBN/Parquet numeric value, row group, statistics, key-value metadata, target,
  path, Validation, or Final-Test content;
- fit on real data or produce a real coefficient, forecast, QLIKE, bootstrap, economic, or
  continuation result;
- mutate frozen protocols, budgets, executed evidence, Issue #48, or PR #47;
- authorize a dependency, database, broker, live path, merge, push, or release.

## 3. Closed two-ledger execution-record schema

Every future governed execution record must carry these required fields:

```text
schema_version = MES_EXECUTION_RECORD_SCHEMA_V1
record_kind = <closed value below>
target_access_state = <closed value below>
execution_authority_state = <closed value below>
execution_authorization_reservation_consumed = <true or false>
```

Neither ledger field may be inferred from the other or compressed into one overloaded
status. “Include at least,” open-ended extension, and unknown-value acceptance are forbidden.

Qualified terms are mandatory in future records and prose:

- **target-slot reservation:** a governing budget/Owner action that reserves a scientific
  target-space slot;
- **execution-authorization reservation consumption:** create-once consumption of authority
  to execute one governed attempt;
- **target-slot consumption:** any numeric target/path value read or target constructed,
  authorized or unauthorized;
- **repair-lineage consumption:** expenditure of an explicitly bounded defect-repair right.

The unqualified words “reservation” and “consumed” may not substitute for these distinct
events.

### 3.1 `record_kind`

The exact closed values are:

- production: `PRECONDITION_STOP`, `STAGE_SUCCESS`, `STAGE_TERMINAL`;
- rehearsal: `REHEARSAL`.

Production schemas must reject `REHEARSAL`; rehearsal schemas must require it.

### 3.2 `target_access_state`

The exact closed production values are:

- `LOCKED_UNRESERVED`
- `LOCKED_RESERVED_NOT_CONSUMED`
- `CONSUMED`
- `CLOSED_UNCONSUMED`
- `ACCESS_NOT_ATTESTED_FAIL_CLOSED`

Rehearsal records must instead use `NOT_APPLICABLE_SYNTHETIC_REHEARSAL`. Production record
schemas must reject this rehearsal value.

### 3.3 `execution_authority_state`

The exact closed production values are:

- `NOT_AUTHORIZED`
- `REVIEW_PENDING`
- `AUTHORIZED_UNUSED`
- `RESERVATION_CONSUMED`
- `COMPLETED_SEALED`
- `TERMINAL_NO_RETRY`
- `NOT_ATTESTED_FAIL_CLOSED`

Rehearsal records must instead use `REHEARSAL_ONLY_NO_SCIENTIFIC_AUTHORITY`. Production
record schemas must reject this rehearsal value.

### 3.4 Closed transitions

Target-access transitions:

| From | Event | To |
| --- | --- | --- |
| `LOCKED_UNRESERVED` | governing target-space budget or authenticated Owner decision reserves the scientific slot | `LOCKED_RESERVED_NOT_CONSUMED` |
| `LOCKED_UNRESERVED` | terminal closure before target-slot reservation | `CLOSED_UNCONSUMED` |
| `LOCKED_RESERVED_NOT_CONSUMED` | first numeric target/path value read or target constructed, whether authorized or unauthorized | `CONSUMED` |
| `LOCKED_UNRESERVED` | numeric target/path value read or target constructed with no target-slot reservation | `CONSUMED` |
| `CLOSED_UNCONSUMED` or `ACCESS_NOT_ATTESTED_FAIL_CLOSED` | numeric target/path value read or target constructed after closure or non-attestation | `CONSUMED` |
| `LOCKED_RESERVED_NOT_CONSUMED` | terminal closure without access, while slot remains reserved | `LOCKED_RESERVED_NOT_CONSUMED` |
| `LOCKED_RESERVED_NOT_CONSUMED` | governing budget or authenticated Owner decision closes the target slot unconsumed | `CLOSED_UNCONSUMED` |
| `LOCKED_UNRESERVED`, `LOCKED_RESERVED_NOT_CONSUMED`, or `ACCESS_NOT_ATTESTED_FAIL_CLOSED` | required access evidence is unavailable | `ACCESS_NOT_ATTESTED_FAIL_CLOSED` |
| `CONSUMED` or `CLOSED_UNCONSUMED` | required access evidence is unavailable | unchanged; record missing evidence in the reason code |
| `LOCKED_UNRESERVED` | later record in the same lineage with no target-slot reservation or access | `LOCKED_UNRESERVED` |
| `LOCKED_RESERVED_NOT_CONSUMED` | later record in the same lineage with no access | `LOCKED_RESERVED_NOT_CONSUMED` |
| `ACCESS_NOT_ATTESTED_FAIL_CLOSED` | later record with no new access evidence | `ACCESS_NOT_ATTESTED_FAIL_CLOSED` |
| `CONSUMED` | later record in the same lineage | `CONSUMED` |
| `CLOSED_UNCONSUMED` | later record in the same closed lineage | `CLOSED_UNCONSUMED` |

Execution-authority transitions:

| From | Event | To |
| --- | --- | --- |
| `NOT_AUTHORIZED` | later record in the same lineage with no review request | `NOT_AUTHORIZED` |
| `NOT_AUTHORIZED` | exact review requested | `REVIEW_PENDING` |
| `REVIEW_PENDING` | valid, unexpired, exact-package PASS with BLOCKER/HIGH = 0 and authenticated Owner authorization | `AUTHORIZED_UNUSED` |
| `REVIEW_PENDING` | valid, unexpired, exact-package PASS with BLOCKER/HIGH = 0, but no authenticated Owner authorization yet and no execution-authorization reservation/source access | `REVIEW_PENDING` |
| `REVIEW_PENDING` | invalid attestation, or attestation absent, timeout, `NO_VERDICT`, or expiry of an otherwise valid PASS, with no explicitly authorized review attempt and no explicitly authorized new review lineage remaining | `NOT_ATTESTED_FAIL_CLOSED` |
| `REVIEW_PENDING` | an otherwise valid PASS expires while an explicitly authorized new packet/attempt-ledger/review lineage is open or remaining and no execution-authorization reservation/source access occurred | `REVIEW_PENDING` |
| `REVIEW_PENDING` | attestation absent, timeout, or `NO_VERDICT` with an explicitly authorized review attempt open or remaining and no execution-authorization reservation/source access | `REVIEW_PENDING` |
| `REVIEW_PENDING` | package/packet-mode/signature/signer/reviewer/report/replay-invalid attempt with an explicitly authorized review attempt remaining and no execution-authorization reservation/source access | `REVIEW_PENDING`; individual attempt stops |
| `REVIEW_PENDING` | valid attested verdict with BLOCKER/HIGH > 0 | `TERMINAL_NO_RETRY` |
| `NOT_AUTHORIZED`, `REVIEW_PENDING`, or `NOT_ATTESTED_FAIL_CLOSED` | execution-authorization reservation consumed without valid authority | `TERMINAL_NO_RETRY`; reason `UNAUTHORIZED_EXECUTION_RESERVATION_CONSUMPTION` |
| `TERMINAL_NO_RETRY` | later unauthorized execution-authorization reservation consumption in the same lineage | `TERMINAL_NO_RETRY`; same unauthorized-reservation reason |
| `AUTHORIZED_UNUSED` | later record in the same lineage before execution-authorization reservation, within validity | `AUTHORIZED_UNUSED` |
| `AUTHORIZED_UNUSED` | create-once execution-authorization reservation consumed | `RESERVATION_CONSUMED` |
| `AUTHORIZED_UNUSED` | authority expires or is revoked unused | `TERMINAL_NO_RETRY` |
| `RESERVATION_CONSUMED` | later `STAGE_SUCCESS` or `PRECONDITION_STOP` record before sealing or terminal stop | `RESERVATION_CONSUMED` |
| `RESERVATION_CONSUMED` | complete valid evidence sealed | `COMPLETED_SEALED` |
| `RESERVATION_CONSUMED` | terminal stop without retry authority | `TERMINAL_NO_RETRY` |
| `COMPLETED_SEALED` | later record in the same lineage | `COMPLETED_SEALED` |
| `TERMINAL_NO_RETRY` | later record in the same lineage | `TERMINAL_NO_RETRY` |
| `NOT_ATTESTED_FAIL_CLOSED` | same commit/package lineage | `NOT_ATTESTED_FAIL_CLOSED` |

Any unlisted transition fails closed. `CONSUMED` is reachable from every target-access state:
access recording is never gated on authorization, order, closure, or attestation. An
unauthorized or post-closure read is still target-slot consumption; its governance violation
is recorded independently on the execution-authority ledger and terminal reason code. A
validator may never reject a record solely because the access it reports was unauthorized.
`CONSUMED` is absorbing. `CLOSED_UNCONSUMED` remains closed unless a later actual access
forces the conservative transition to `CONSUMED`; missing evidence alone does not do so.

`ACCESS_NOT_ATTESTED_FAIL_CLOSED` is sticky within the same lineage: it may remain unchanged
or move conservatively to `CONSUMED` if actual access is later established, but late evidence
may not move it back to any determinate unconsumed state. A separately authorized forensic
lineage may document late evidence additively; it cannot mutate the closed historical state.
A new execution lineage begins under its own exact commit, schema, and Owner authority.

`CLOSED_UNCONSUMED` remains determinate when a later record merely lacks new access evidence
because its earlier authenticated closure already attested the complete access window. If a
post-closure event creates a new possible access window, that interval must be represented as
a separate lineage and fail closed independently when its evidence is unavailable; it cannot
silently overwrite the historical closure.

An unauthorized additional execution-authorization reservation after `COMPLETED_SEALED`
must open a separate incident lineage beginning `NOT_AUTHORIZED`; it cannot mutate or
reinterpret the sealed lineage.

File presence alone never proves either state. A new schema version is required to add a
state or transition; historical versions remain frozen.

Every transition must also preserve the exact boolean
`execution_authorization_reservation_consumed`. It changes from `false` to `true` on any
actual execution-authorization reservation consumption, authorized or unauthorized, and can
never return to `false`. A terminal authority state therefore cannot erase the reservation
fact that caused it.

These transition tables validate representation only. They do not create, reserve, release,
retry, close, or replace scientific authority. The exact governing budget, stage protocol,
and authenticated Owner authorization determine whether an event is permitted and which
disposition applies. An execution-authorization reservation changes only
`execution_authority_state` and its monotone reservation-consumed boolean; it never changes
`target_access_state` by itself.

## 4. Versioned shared boundary validator

Cross-stage invariants must live in one immutable versioned contract whose exact bytes and
SHA-256 are pinned by every consuming package. A downstream stage may not strengthen or
reinterpret those invariants locally.

The first bounded validator may centralize only true shared boundaries:

- raw identity grammar and byte-semantic serialization;
- timestamp/time-zone form;
- finite numeric scalar classification;
- integral boolean-flag normalization with accepted domain exactly `{0, 1}`;
- field presence, ordered logical type, and nullability.

Stage-specific access authority, disposition, reason-code mapping, target rules, and model
rules remain in thin stage adapters. Centralization must not turn one mutable helper into a
single point that silently changes historical experiments. Any new validator version is a
new artifact; historical versions remain addressable and byte-identical.

## 5. Artifact schema conformance gate

Before any stage may request numeric values, its preceding metadata gate must verify the
ordered logical schema for every field that the stage will read:

- field name and order;
- logical Arrow type;
- nullability;
- frozen semantic/domain rule;
- producer-contract version and SHA.

Only columns in the authorized consumer projection participate. Unrelated columns must not
create false blockers. Physical encoding, compression, dictionary layout, row-group data,
statistics, and key-value metadata remain out of scope unless separately authorized. DBN
sources use their own header/schema identity and are not described as Arrow dtypes.

Schema-name-only verification is insufficient. The gate must produce an aggregate schema
contract hash without opening numeric values.

### 5.1 Consumer rehearsal

The same consumer adapter intended for a later stage must be exercised with type-correct
synthetic Arrow rows constructed from the observed metadata contract. A zero-row table is
insufficient because it does not test scalar types after conversion.

Required boundary values include:

- `early_close_session` as Arrow `int8` values `0` and `1`, normalized to boolean;
- integral flag values `-1` and `2`, rejected with an exact reason code;
- declared nullable Cell 12 fields with both null and non-null synthetic values;
- a valid identity containing `|`;
- CR/LF identity values rejected by the frozen identity grammar.

## 6. Trusted reviewer attestation gate

A release-affecting reviewer predicate must be machine-derived. A runner may not create an
authorization reservation until it verifies a trusted create-once attestation bound to the
exact reviewed package.

Under this V1 protocol, the attestation's authorization-relevant field set is closed and must
bind exactly:

- repository identity, branch, commit, tree, diff base, exact allowlist, and ordered file
  SHA-256 values;
- reviewer identity, provider, model, tool/runtime version, and review role;
- prompt/Clause-Packet SHA-256, exact
  `clause_packet_operating_mode=FULL_GOVERNED`, and report SHA-256;
- verdict, explicit BLOCKER count, explicit HIGH count, and completion status;
- issued timestamp, bounded expiry, trusted time-source identity, and a trusted signature or
  service receipt.

Any additional authorization-relevant field requires an explicitly ratified successor schema
version; V1 does not accept open-ended extensions.

An unsigned JSON file that any repository process can write is not a trusted attestation.
The attestation should be external/create-once and keyed to the reviewed code commit so that
committing it cannot change the commit that was reviewed. A later evidence commit may
preserve its receipt and hash without retroactively satisfying the gate.

The current repository has no ratified trusted signer or verifier. A future implementation
authorization must name one exact trust mechanism and its verification key/root, such as a
provider-signed review receipt, an external CI/control-plane signature, or an Owner-signed
acceptance receipt. An Owner signature proves only that the Owner/control plane accepted the
review; it does not prove provider, model, or runtime identity unless those claims are also
cryptographically bound by the review provider.

A Clause Packet, reviewer prose response, local JSON, report hash, or packet closeout is not
a trusted attestation and cannot satisfy this gate by itself.

### 6.1 Exact pre-reservation outcomes

| Condition | Required outcome |
| --- | --- |
| attestation absent, attempt budget open or remaining | `REVIEW_ATTESTATION_MISSING_STOP_BEFORE_RESERVATION`; package stays `REVIEW_PENDING` |
| attestation absent, attempt budget exhausted or none authorized | `REVIEW_ATTESTATION_MISSING_STOP_BEFORE_RESERVATION`; package moves to `NOT_ATTESTED_FAIL_CLOSED` |
| commit/tree/file hash mismatch | `REVIEW_ATTESTATION_PACKAGE_MISMATCH_STOP_BEFORE_RESERVATION` |
| timeout or `NO_VERDICT`, attempt budget open or remaining | `REVIEW_ATTESTATION_NO_VERDICT_STOP_BEFORE_RESERVATION`; package stays `REVIEW_PENDING` |
| timeout or `NO_VERDICT`, attempt budget exhausted or none authorized | `REVIEW_ATTESTATION_NO_VERDICT_STOP_BEFORE_RESERVATION`; package moves to `NOT_ATTESTED_FAIL_CLOSED` |
| valid attestation with BLOCKER/HIGH > 0 | `REVIEW_ATTESTATION_REJECTED_STOP_BEFORE_RESERVATION` |
| expired attestation, explicitly authorized new review lineage open or remaining | `REVIEW_ATTESTATION_EXPIRED_STOP_BEFORE_RESERVATION`; package stays `REVIEW_PENDING` |
| expired attestation, no new review lineage authorized or remaining | `REVIEW_ATTESTATION_EXPIRED_STOP_BEFORE_RESERVATION`; package moves to `NOT_ATTESTED_FAIL_CLOSED` |
| invalid/unknown signer or trust root | `REVIEW_ATTESTATION_SIGNER_INVALID_STOP_BEFORE_RESERVATION` |
| wrong provider/model/review role | `REVIEW_ATTESTATION_REVIEWER_IDENTITY_MISMATCH_STOP_BEFORE_RESERVATION` |
| Clause-Packet/report hash mismatch | `REVIEW_ATTESTATION_REPORT_BINDING_MISMATCH_STOP_BEFORE_RESERVATION` |
| Clause Packet mode absent, unknown, or not exactly `FULL_GOVERNED` | `REVIEW_ATTESTATION_PACKET_MODE_INVALID_STOP_BEFORE_RESERVATION` |
| receipt/attempt replay | `REVIEW_ATTESTATION_REPLAY_STOP_BEFORE_RESERVATION` |
| valid, unexpired, exact-package PASS with BLOCKER/HIGH = 0 | reviewer gate passes; package stays `REVIEW_PENDING` until authenticated Owner authorization; no other authority is implied |

Every attempt must create an append-only attempt-ledger entry bound to the packet, package,
review role, expected signer/model, start time, bounded timeout, and outcome receipt. A future
Owner authorization may permit a finite review-attempt budget only before
execution-authorization reservation consumption and governed source access. While that
budget remains, timeout or `NO_VERDICT` closes the
individual attempt but leaves the package state `REVIEW_PENDING`. Exhaustion changes it to
`NOT_ATTESTED_FAIL_CLOSED`. This draft authorizes no attempt or retry.

For every package/signature/signer/reviewer/report/packet-mode/replay-invalid outcome in
Section 6.1, the individual attempt stops. If an explicitly authorized attempt remains and no
execution-authorization reservation/source access occurred, the package stays
`REVIEW_PENDING`; otherwise it moves to `NOT_ATTESTED_FAIL_CLOSED`. Tier 1 must test both
attempt-budget states for every such outcome.

The first completed valid verdict binds that exact commit/package. A completed rejected
verdict cannot be retried against unchanged bytes; remediation requires a code change, new
commit/tree, new frozen packet, and new review lineage. Timeout never permits silent
reviewer/model substitution. Any fallback reviewer must be named by the governing protocol
or separately authorized by the Owner before execution-authorization reservation
consumption.

Expiry is not a scientific or code defect. A new Owner authorization may permit a new packet,
attempt ledger, and review lineage against unchanged bytes after an otherwise valid PASS
expires only if that authority exists while the package remains `REVIEW_PENDING` and no
execution-authorization reservation or governed source access occurred. Once
`NOT_ATTESTED_FAIL_CLOSED` is recorded for a commit/package, no new review lineage against
those bytes can restore `REVIEW_PENDING`; only a new commit/tree begins a new lineage. The
expired attestation remains immutable and cannot be refreshed in place.

Expiry-lineage availability is evaluated once using the trusted time source at the expiry
gate, before any later Owner grant can be considered. A post-expiry grant cannot revive a
package already recorded as `NOT_ATTESTED_FAIL_CLOSED`. A new commit/tree starts a distinct
lineage at `NOT_AUTHORIZED`; it is not a transition out of the closed lineage.

## 7. Synthetic evidence isolation

Synthetic rehearsal output must be unable to masquerade as real evidence. Isolation is
mandatory at three layers.

### 7.1 Record schema

Every rehearsal record requires:

```text
schema_version = MES_EXECUTION_RECORD_SCHEMA_V1
record_kind = REHEARSAL
evidence_class = SYNTHETIC_REHEARSAL
synthetic = true
scientific_inference_authorized = false
target_access_state = NOT_APPLICABLE_SYNTHETIC_REHEARSAL
execution_authority_state = REHEARSAL_ONLY_NO_SCIENTIFIC_AUTHORITY
execution_authorization_reservation_consumed = <false before isolated rehearsal reservation; true after>
rehearsal_stage = CONTRACT | METADATA | PRE_TARGET | TARGET_PREFIT | FIT | SEALED
rehearsal_surface_map_id = REHEARSAL_SURFACE_MAP_V<n>
rehearsal_surface_map_path = <exact repository path>
rehearsal_surface_map_sha256 = <64-hex>
sealing_trust_root = <rehearsal trust-root identity>
```

The rehearsal boolean refers exclusively to the isolated rehearsal authorization ledger. It
is monotone `false -> true` when the rehearsal reservation mechanism consumes the isolated
create-once reservation and can never describe or mutate production authority. The closed
`rehearsal_stage` plus `record_kind`, the monotone boolean, and create-once witnesses express
the Tier 2 lifecycle while `execution_authority_state` remains explicitly non-scientific.
Production schemas must reject `rehearsal_stage` and every rehearsal-surface-map field.

Every production evidence schema must reject `synthetic=true`, a rehearsal evidence class,
or a rehearsal-only ledger state.

Rejection of rehearsal markers is necessary but not sufficient because markers can be
removed. Every production record also requires all of these positive, non-defaultable
bindings:

```text
record_kind = PRECONDITION_STOP | STAGE_SUCCESS | STAGE_TERMINAL
evidence_class = REAL_GOVERNED_EXECUTION
synthetic = false
source_binding = <non-empty SHA-256 of the real source-artifact schema contract, or exact closed sentinel NO_SOURCE_ARTIFACT_ACCESSED>
source_access_guard = PRE_SOURCE_NO_ACCESS_VERIFIED | SOURCE_CONTRACT_BOUND
sealing_trust_root = <production trust-root identity>
```

`NO_SOURCE_ARTIFACT_ACCESSED` is a closed sentinel, never an empty, absent, defaulted, or
unknown value. It is permitted only with machine-attested
`source_access_guard=PRE_SOURCE_NO_ACCESS_VERIFIED`, zero source-artifact reads, and
`target_access_state` exactly one of `LOCKED_UNRESERVED`,
`LOCKED_RESERVED_NOT_CONSUMED`, or `CLOSED_UNCONSUMED`. It is forbidden with
`ACCESS_NOT_ATTESTED_FAIL_CLOSED` or `CONSUMED`, and a record carrying it may not also report
a schema-contract hash. A schema-contract hash requires
`source_access_guard=SOURCE_CONTRACT_BOUND`. Any empty, absent, inconsistent, or unrecognized
value for `source_binding`, `source_access_guard`, or `sealing_trust_root` fails closed.

Production evidence is valid only when sealed under the production trust root. A rehearsal
trust root can never satisfy that predicate, regardless of removed markers. Absence of a
marker is never interpreted as production.

### 7.2 Namespace

- protocol/run IDs must begin with `REHEARSAL_`;
- artifacts must live only under `artifacts/rehearsal/<protocol-id>/<run-id>/`;
- production authorization, evidence, and registry paths must reject a `REHEARSAL_` ID or
  any path below `artifacts/rehearsal/`.

### 7.3 Registry firewall

The production evidence registry must parse and reject rehearsal records mechanically. It
must not rely on filenames, directories, UI labels, or human review alone. Tier 1 must prove
cross-registration rejection in both directions.

## 8. Tier 1 fast regression matrix

Tier 1 must be deterministic, in-memory, free of real artifact access, and eligible to run
on every commit after separate CI authorization.

| Case | Earliest required stop/pass | Exact assertion |
| --- | --- | --- |
| valid identity containing `\|` | boundary validator PASS | byte-semantic identity preserved |
| CR/LF identity | L0/shared validator STOP | frozen identity reason code |
| Arrow `int8` flag `0/1` | metadata rehearsal PASS | exact boolean normalization |
| Arrow integral flag outside `{0,1}` | metadata rehearsal STOP | domain reason code |
| declared nullable field | schema/consumer rehearsal PASS | nullability preserved |
| nonpositive predictor | G2-P STOP | `PREDICTOR_NONPOSITIVE`; no target access |
| zero-variance target | G3-P STOP after complete synthetic ledger | `TARGET_ZERO_VARIANCE`; zero fit |
| missing reviewer attestation, attempt budget remaining | pre-reservation STOP | exact missing code; state remains `REVIEW_PENDING` |
| missing reviewer attestation, attempt budget exhausted | pre-reservation STOP | exact missing code; state becomes `NOT_ATTESTED_FAIL_CLOSED` |
| mismatched attestation hashes | pre-reservation STOP | exact mismatch code |
| reviewer timeout / no verdict, attempt budget remaining | pre-reservation STOP | exact no-verdict code; state remains `REVIEW_PENDING` |
| reviewer timeout / no verdict, attempt budget exhausted | pre-reservation STOP | exact no-verdict code; state becomes `NOT_ATTESTED_FAIL_CLOSED` |
| reviewer BLOCKER/HIGH > 0 | pre-reservation STOP | exact rejected code; new commit required |
| expired attestation, new review lineage remaining | pre-reservation STOP | exact expired code; state remains `REVIEW_PENDING` |
| expired attestation, no new review lineage remaining | pre-reservation STOP | exact expired code; state becomes `NOT_ATTESTED_FAIL_CLOSED` |
| invalid/unknown signer or trust root | pre-reservation STOP | exact signer code |
| wrong provider/model/review role | pre-reservation STOP | exact reviewer-identity code |
| wrong Clause-Packet/report hash | pre-reservation STOP | exact packet/report mismatch code |
| attestation binds `LIGHT_ADVISORY`, missing, or unknown packet mode | pre-reservation STOP | exact packet-mode-invalid code; never reaches `AUTHORIZED_UNUSED` |
| reused receipt or attempt identity | pre-reservation STOP | exact replay code |
| exact valid reviewer attestation, no Owner authorization yet | pre-reservation gate PASS | state remains `REVIEW_PENDING`; no authority inferred beyond the gate |
| execution-authorization reservation consumed without valid authority | runner terminal STOP | boolean becomes `true`; state `TERMINAL_NO_RETRY`; exact unauthorized-reservation code |
| rehearsal record offered to production registry | registry STOP | synthetic contamination code |
| production record offered to rehearsal registry | registry STOP | production contamination code |
| each rehearsal marker removed or mutated singly | production registry STOP | contamination code remains fail-closed |
| all rehearsal markers/IDs/namespace removed together while rehearsal trust root remains | production registry STOP | trust-root/source-binding rejection code |
| production record with any positive production binding absent, empty, or unrecognized | production registry STOP | exact missing-production-binding code |
| production record uses `NO_SOURCE_ARTIFACT_ACCESSED` without the exact pre-source guard, with a source read/schema hash, or with `target_access_state` equal to `CONSUMED`/`ACCESS_NOT_ATTESTED_FAIL_CLOSED` | production registry STOP | exact invalid-sentinel code |
| canonical production-schema fixture | production registry PASS in memory only | exact production markers preserved |
| canonical rehearsal fixture before/after isolated reservation | rehearsal registry PASS | stage advances; rehearsal boolean changes monotonically `false -> true`; production boolean/ledger unchanged |
| every listed two-ledger transition | state validator PASS | exact declared next state |
| every unlisted two-ledger transition | state validator STOP | exact invalid-transition code |
| rehearsal surface map absent, mutable, or SHA-mismatched | before Tier 2 | exact surface-map-binding stop code |
| clean synthetic happy-path fixture | all fast contract gates PASS | eligible for Tier 2 only |

Tests must assert both ledger fields, all protected counters, and absence of output on every
pre-output stop.

Tier 1 must also cover these exact scientific boundaries:

- every nullable/non-null Cell 12 combination consumed by the stage, including
  `LABEL_UNUSABLE`, nullable `path_instrument_changed`, and path-count/path-metric fields;
- a predictor value of exactly `0` and a negative predictor as separate fixtures; each must
  stop with a complete predictor ledger/count/hash, unchanged target ledger, and no target
  access;
- a zero-variance target only after a complete synthetic target ledger/count/hash; it must
  stop before common-mask creation or fit and may emit only the authorized ledger and
  terminal record;
- one-at-a-time mutation of `evidence_class`, `synthetic`, both rehearsal ledger states,
  `REHEARSAL_` protocol/run identities, and rehearsal namespace.

## 9. Tier 2 full synthetic dress rehearsal

Tier 2 does not assume that a Test 3b, Test 4, or other future production scientific runner
already exists. Every dress rehearsal must name one exact `REHEARSAL_PROTOCOL_ID` and one
create-once, byte-addressable `REHEARSAL_SURFACE_MAP_V<n>` artifact for the generic contract,
metadata, pre-target, target/pre-fit, fit, sealing, ledger, attestation, and registry machinery
it exercises. The surface-map path and SHA-256 must be pinned before rehearsal and recorded
in every Tier 2 sealed record. Historical map versions remain addressable and byte-identical.

A later scientific protocol must cite the exact surface-map ID/SHA-256 and map every intended
runner surface to it, or explicitly extend the map and rerun the rehearsal before its own
execution. No future protocol may silently inherit a Test-3-shaped runner by similarity. The
generic closed `rehearsal_stage` enum is intentional; historical Test 3 stage names appear
only as mapped regression sources, not as future-runner assumptions.

Tier 2 must run the complete governed lifecycle with no real data:

1. shared contracts and synthetic proof fixtures;
2. full metadata schema/type/nullability conformance;
3. pre-target predictor-domain and identity checks;
4. synthetic request, target, common-mask, fold, harmonic, rank, and support checks;
5. bounded synthetic fit, loss, bootstrap, economic-diagnostic, and every other surface named
   by the exact rehearsal-protocol surface map;
6. create-once reservation, success/failure witness, record sealing, reread, and hashes;
7. production-registry rejection of every rehearsal artifact.

The happy path must finish successfully through the same core predicate and serialization
paths used by production. Failure fixtures must embed every historical landmine and stop at
the stage/reason declared in Tier 1. Rehearsal counters must distinguish synthetic calls
from real calls; every real-data, real-target, Validation, and Final-Test counter remains
zero.

The rehearsal may replace only the source adapter with an in-memory synthetic adapter, the
artifact namespace with the rehearsal namespace, the production trust root with a separate
rehearsal trust root, and production state-store handles with isolated rehearsal-ledger
handles. It may not monkeypatch, mock, bypass, or substitute the validator, consumer adapter,
stage predicate, reason mapping, serializer, attestation verifier, reservation mechanism,
sealing logic, reread/hash check, or registry predicate.

Tier 2 must be state-isolated from all production governance ledgers. The rehearsal runner
must use a rehearsal target-slot reservation ledger, execution-authorization attempt ledger,
and evidence registry addressed only under the rehearsal namespace. It may not create,
mutate, lock, release, or increment any production reservation record, target-space slot,
hypothesis/repair budget counter, authorization record, attempt ordinal, or registry entry,
including transiently. Production ledger handles must be unreachable from the rehearsal
runner by construction, as must the production trust root, private signing material, and
signing-service credentials. Before and after every rehearsal, machine checks must prove the
byte hashes of all production governance ledgers unchanged.

No rehearsal token, attestation, record, permit, or success witness may be accepted by a
production runner. No production authorization token may be accepted by the rehearsal
runner.

## 10. Issue #48 and PR #47 boundary

Observed 2026-08-25:

- GitHub Issue #48, `CI: enforce executed-frozen document integrity on every PR`, is OPEN;
- Draft PR #47, `Freeze Test 3 volatility Risk Edge protocol`, is OPEN/DRAFT with Quant CI
  V1 PASS, `mergeStateStatus=BLOCKED`, and `mergeable=MERGEABLE`; it is outside this
  protocol's current authority. These are distinct GitHub fields and neither grants merge.

Class: `F_MACHINE`, observed read-only through authenticated GitHub CLI/API as
`NonChaianon` on 2026-08-25. These facts are volatile and must be re-observed for any later
authorization decision that depends on them.

The current docs-only authorization does not modify CI or Issue #48. Only the executed-frozen
registry/integrity subset of Tier 1 overlaps Issue #48. The broader Tier 1 matrix is outside
Issue #48 unless a later authenticated Owner authorization explicitly expands that issue's
scope.

A future Step 3 implementation authorization must separately state:

1. whether the exact Issue #48 acceptance work is implemented, activated in live CI, and
   eligible for closeout under that authorization; and
2. which additional Tier 1 controls, if any, are authorized to enter CI.

If Issue #48 is excluded, its executed-frozen integrity requirement remains incomplete and
open. A Step 3 authorization may permit a bounded local partial implementation while
excluding Issue #48, but that package cannot satisfy this protocol's exit criteria or become
eligible for Step 5 until live-CI enforcement is separately authorized and proven.

PR #47 remains outside both paths unless separately authorized. No hardening document or
test result grants merge authority.

## 11. Clause Packet rule

Every external or snapshot-based reviewer question whose answer depends on a clause must use
`docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md` in either `LIGHT_ADVISORY` or
`FULL_GOVERNED` mode. `LIGHT_ADVISORY` is allowed only for non-authoritative advice and uses
one frozen packet plus one separately sealed response marked `UNTRUSTED_CONTEXT_ONLY`.
`FULL_GOVERNED` is mandatory for any question touching authorization, execution, access,
budget, evidence classification/disposition, protocol ratification or change, CI, release,
merge, or an execution-hardening exit criterion. Uncertainty about classification selects
`FULL_GOVERNED`.

Both modes bind verbatim text to an exact commit/tree and file SHA, state precedence and
counters, and require the reviewer to label textual facts separately from interpretation or
recommendation.

The completed packet must be frozen create-once at dispatch. No response may be inserted by
editing it. In `FULL_GOVERNED`, the dispatch receipt, reviewer response, Owner closeout, and
closeout receipt plus external anchor remain separate additive artifacts with their own
identities and hashes.
No summary, memory, or paraphrase may override the bound clause text. Neither mode is a
trusted review attestation unless the separate requirements in Section 6 are satisfied;
`LIGHT_ADVISORY` can never satisfy Section 6 or be upgraded in place to do so.

## 12. Exit criteria

Step 3 implementation is not complete until all of the following are machine-observed:

1. every historical landmine stops or passes at its declared stage/reason;
2. the executed-frozen integrity subset runs on every PR in live CI under explicit Owner
   authorization covering Issue #48, and every broader Tier 1 control entering CI is
   separately enumerated;
3. one Tier 2 happy path completes and seals isolated synthetic evidence;
4. each registry accepts its canonical own-class fixture, rejects the opposite class,
   rejects every single-marker/namespace/protocol mutation, and the production registry
   rejects combined marker removal, missing positive production bindings, and invalid
   `NO_SOURCE_ARTIFACT_ACCESSED` use;
5. the reviewer gate proves every Section 6.1 outcome, including mechanical rejection of any
   Clause Packet mode other than exact `FULL_GOVERNED`;
6. every terminal record carries separate target-access and execution-authority states plus
   the monotone execution-authorization-reservation-consumed boolean;
7. all real-data/target/fit/Validation/Final counters remain zero;
8. before/after hashes prove every production governance ledger unchanged by Tier 2, and the
   rehearsal process cannot reach production ledger handles or signing authority; the
   isolated rehearsal reservation alone changes its rehearsal boolean monotonically;
9. every Tier 2 sealed record binds the exact `REHEARSAL_SURFACE_MAP_V<n>` ID/path/SHA-256,
   and any later scientific protocol cites that digest or proves an extended map was
   rehearsed and resealed before execution;
10. a fresh-eyes reviewer returns a completed verdict with BLOCKER = 0 and HIGH = 0 against
   the exact fixes, counters, and package. The Step 3 authorization must state whether this
   requires (a) a Section 6 trusted attestation or (b) an untrusted prose/Clause-Packet review
   using `FULL_GOVERNED` mode whose response is recorded as `UNTRUSTED_CONTEXT_ONLY`. Form (b)
   satisfies only the engineering-completeness judgment; it never satisfies Section 6 or
   permits execution-authorization reservation consumption. Owner ratification is separate
   from either form.

Meeting these criteria grants no Test 3b or scientific execution authority. It gives the
Owner an engineering evidence base for a later decision.

## 13. Ratification and next authority

The Owner must review and ratify these exact three IDs/paths together against one commit:

1. `MES_INCIDENT_TEST3_G3P_20260825` —
   `docs/research/TEST3_G3P_INCIDENT_RECORD_V1.md`;
2. `MES_EXECUTION_HARDENING_PROTOCOL_V1` —
   `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md`;
3. `MES_CLAUSE_PACKET_TEMPLATE_V1` —
   `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md`.

Reviewer PASS is necessary evidence when required but is not ratification. A later Step 3
authorization must name the exact base, branch, file allowlist, CI/Issue #48 choice,
synthetic fit budget, trusted-attestation mechanism, trusted time source, reviewer role,
surface-map ID/path/SHA-256, tests, and explicit forbidden surfaces.

Until that authorization exists, all implementation and execution remain forbidden.

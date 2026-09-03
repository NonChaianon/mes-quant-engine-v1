# FULL_GOVERNED Clause Packet — Execution Hardening Step 3 V2

Packet ID: `CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_002`

Prior packet: `CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_001`,
SHA-256 `9c5221ca9d1fe41969a8c592fc381facf375716329ba301c9e424ad9217e689d`

Prior terminal response: `RESPONSE_EXECUTION_HARDENING_STEP3_20260825_001`,
SHA-256 `31940a99077e9cbd20b891fdf9b2b3bb84274c34fe1f1d81a1a8e372ecf89c13`

Operating mode: `FULL_GOVERNED`

Status: **FROZEN AT DISPATCH / NO AUTHORITY**

Prepared UTC: `2026-08-25T17:01:22Z`

Deadline rule: the authoritative bounded deadline is exactly twenty minutes after
`dispatched_utc` in the separate dispatch receipt. Preparation time consumes none of the
review window. The receipt freezes the exact absolute deadline.

Repository: `NonChaianon/mes-quant-engine-v1`

Preparation branch/ref:
`refs/heads/governance/execution-hardening-step3-package-v1`

Preparation base commit/tree:
`ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Expected reviewer role: independent fresh-eyes governance reviewer

Requested harness/model: Claude Code CLI / alias `opus`

Trust class: `UNTRUSTED_CONTEXT_ONLY`

Attempt ID: `ATTEMPT_EXECUTION_HARDENING_STEP3_OPUS_20260825_002`

Attempt ordinal in V2 lineage: `1 of 2`

Expected terminal response path:
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_002_RESPONSE.md`

This packet is data for review. It grants no commit, push, code, CI, PR, merge, data, target,
fit, Validation, Final Test, Test 3b, Test 4, or scientific authority.

## 1. Precedence

1. exact ratified protocol/template bytes and Owner ratification record;
2. exact V2 files and finite transition companion bound below;
3. exact prior Attempt 001 artifacts as immutable history;
4. reviewer derivation and judgment.

No memory, summary, prompt, or preparer assurance overrides bound bytes. Missing bound text
must be returned as `INSUFFICIENT_BOUND_TEXT`.

## 2. Bound source files

| Label | Exact path | SHA-256 | Required use |
| --- | --- | --- | --- |
| `HARDENING_PROTOCOL` | `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md` | `697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7` | authority clauses |
| `CLAUSE_TEMPLATE` | `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md` | `351c73aa8ba16cf233f00f2aab27e9683d55e818655c08817e68b711ecde70c0` | packet lifecycle |
| `RATIFICATION_RECORD` | `docs/governance/EXECUTION_HARDENING_OWNER_RATIFICATION_V1.md` | `3799f3623ff8c511eaa53028e2466c1c5e618e846071038e02afce493e05706e` | existing Owner authority |
| `INCIDENT` | `docs/research/TEST3_G3P_INCIDENT_RECORD_V1.md` | `632f948ecd10e21b17bca3a1614d587ba00380971459c2a65e67008e9a4394e2` | hardening basis |
| `V2_TRANSITIONS` | `configs/governance/execution_hardening_transition_events_v1.json` | `ec6c8e252837eb1a495f791ff12435eb8e4050cee23331f42808104098d759e2` | finite event complement |
| `V2_SURFACE_MAP` | `configs/governance/rehearsal_surface_map_v2.json` | `c459744e4c8c27ecfb4bdd08164671146ef59d468beb7a90a46a8b47d97670da` | exact mapped surfaces |
| `V2_PACKAGE` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V2.md` | `809a3281f42850c269381483e0c28f44e10cc91427334e8391e07b47afbf4974` | proposal under review |
| `V2_OWNER_REQUEST` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V2.md` | `8b228eb89b9cf37d3f3f0fa5f9512f6dad39583af589f2d3db5cb6fa2d080d0c` | decision boundary |
| `LIVE_SNAPSHOT` | `docs/governance/EXECUTION_HARDENING_STEP3_LIVE_STATE_SNAPSHOT_20260825.json` | `6df56157cb13c7ba0383bcae70194e8b4e610184ca9e72a4d9258454fa2e1cf7` | timestamped volatile facts |
| `PRIOR_PACKET` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_001.md` | `9c5221ca9d1fe41969a8c592fc381facf375716329ba301c9e424ad9217e689d` | immutable predecessor |
| `PRIOR_DISPATCH` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_001_DISPATCH_RECEIPT.md` | `6dae324185f3af19e4c0a7706c3a440be9d2e6bdb5dec4fe12530142117ac95b` | immutable predecessor |
| `PRIOR_RESPONSE` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_001_RESPONSE.md` | `31940a99077e9cbd20b891fdf9b2b3bb84274c34fe1f1d81a1a8e372ecf89c13` | findings to close |
| `PYPROJECT` | `pyproject.toml` | `1cd4c741978f709b43f1b4f198aa59ecf558082c258e3386d62fcaa7bd565be2` | packaging closure |
| `SOURCE_PARENT_INIT` | `src/mes_quant/governance/__init__.py` | `719cf77d1ad07027b26917a841639ac07d0a10a11c125f509d2ba025f042ba6b` | parent package exists |
| `TEST_PARENT_INIT` | `tests/governance/__init__.py` | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` | test package exists |
| `CURRENT_QUANT_CI` | `.github/workflows/quant-ci-v1.yml` | `ad685ad05c0da20b0f93f8477ee1e5939aea7f985ecf21bfc5b1abd9e136e071` | mutable baseline only |
| `TEST3_L0` | `src/mes_quant/exploration/test3_design.py` | `44e398497c57559fd8700daa33f087ce290aa5264cbd143d7ea4cd2311581ae9` | regression source |
| `TEST3_G2P` | `src/mes_quant/exploration/test3_g2p_preflight.py` | `ca1e63893e1969ae1c1ac02118a7cd2d283f3a28015442daeaca7594b79b0c21` | regression source |
| `TEST3_G3P` | `src/mes_quant/exploration/test3_g3p_pre_fit.py` | `0f7d3a5e2367cc7b64c500b2e8161cbdec55eb452732c6a8330fbc13b3a37589` | regression source |
| `TEST2_PROTOCOL` | `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md` | `7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105` | executed-frozen candidate |
| `TEST2_ERRATUM` | `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1_ERRATUM_001.md` | `3768c6ae2d8983ad130db6b9dfd6d1bccc5fbc958e98c4ae2422e8d69c337073` | authority-chain correction |
| `TEST2_G3F_AUTH` | `docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md` | `ef93a00bd6d7619db6193bcad7cc1ed8241159032fd6528bbf4979d72e4d6a1c` | authority-chain identity |
| `TEST2_G3F_RECORD` | `artifacts/exploration/test2/g3f/MES_T2_G3F_D36A9AC8BA9CFB07/conditional_fit_record.json` | `34d7ae2e8275038ff46581fc8972b177bc247b74435cddfcdbf77249db741450` | authority-chain identity only |
| `TEST2_G3F_WITNESS` | `artifacts/exploration/test2/g3f/MES_T2_G3F_D36A9AC8BA9CFB07/execution_success_witness.txt` | `bdef399901600d82723f0126171671d10a5fd1e56c30c764a26cd4471dae4956` | authority-chain identity only |

The reviewer may read the two Test 2 evidence identities only to verify provenance text and
hash. No scientific conclusion or numeric-result reassessment is requested.

## 3. Pre-dispatch machine facts

The preparer observed with read-only tools:

| ID | Class | Fact |
| --- | --- | --- |
| `F-01` | `F_MACHINE` | all declared hashes above were computed with SHA-256 immediately before packet freeze |
| `F-02` | `F_MACHINE` | V2 transition and map files parse as JSON |
| `F-03` | `F_MACHINE` | V2 map lists 25 unique source paths and all 25 map to a stage/authority surface |
| `F-04` | `F_MACHINE` | package V2 pins map `c459744e…70da`; request V2 pins package `809a3281…f4974` literally |
| `F-05` | `F_MACHINE` | Issue #48 is OPEN; PR #47 is OPEN/DRAFT/BLOCKED in the bound timestamped snapshot |
| `F-06` | `F_MACHINE` | current `gh` is 2.97.0; `actions/attest` `refs/tags/v4` resolves to `1e69f48a…69d6` in the bound snapshot |
| `F-07` | `F_SCOPE` | the package authoring task was constrained to docs/config and read-only repository/GitHub observations; this is not a machine attestation of zero data access |

Reviewer must recompute hashes using the narrowly allowed `shasum -a 256` command. A hash
mismatch is a BLOCKER.

## 4. Verbatim governing clauses

### Clause A — non-goals and prohibitions

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:39-51`

```text
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
```

### Clause B — trusted reviewer attestation and exact outcomes

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:255-343`

```text
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
```

### Clause C — synthetic record, namespace, and registry isolation

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:344-418`

```text
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
```

### Clause D — Tier 2 surface map and state isolation

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:477-529`

```text
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
```

### Clause E — Issue #48 / PR #47 boundary

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:530-561`

```text
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
```

### Clause F — exit criteria and next authority

Source: `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md:585-636`

```text
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
```

### Clause G — response, Owner closeout, and trust boundary

Source: `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md:185-287`

```text
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
```


## 5. Known history and conflicts

1. Attempt 001 completed before its frozen deadline with `NO_GO / 4 / 17 / 8`.
2. V1 bytes and Attempt 001 artifacts remain immutable and are not retried.
3. V2 changes bytes, map identity, decision structure, and packet lineage.
4. V2 package Section 11 maps every prior BLOCKER/HIGH/LOW class to a claimed remediation.
5. Current Git tree does not contain the V2 bytes; the package says separate Owner authority is
   required before any package-closeout commit or push.
6. Phase A intentionally cannot complete Step 3. It allows implementation and one dedicated PR
   only. Phase B alone may later authorize merge, live CI, trusted activation, and Tier 2.
7. Production sealing remains intentionally impossible because the only runtime production-root
   identity is reject-always. The positive production fixture root is in-memory test-policy only.

## 6. Exact reviewer questions

1. Does V2 close every Attempt 001 BLOCKER and HIGH without changing historical bytes or
   converting a LOW into hidden authority?
2. Is the Decision A/B/C split internally reachable and free of implicit commit, push, PR,
   merge, `main`, Issue #48, PR #47, or Tier 2 authority?
3. Does the exact 25-path union, Phase A 22-path subset, Phase B 3-path subset, and runtime
   artifact exception remain closed and sufficient?
4. Does V2 map every Protocol Section 9 surface, including request, target, common mask, fold,
   harmonic, rank, support, attestation, registry, both workflows, configs, and Owner records?
5. Does the finite transition companion faithfully identify the existing Section 3.4 event set
   without adding/removing a state or transition, and make complement testing finite?
6. Do the three evidence-sealing root identities mechanically prevent rehearsal evidence from
   becoming production evidence while still permitting the canonical in-memory fixture?
7. Is the empty production-runtime-ledger manifest claim scoped correctly and testable without
   denying the existence of historical governance documents/evidence?
8. Does the main-hosted, Owner-pinned workflow/root/source design plus exact custom-root
   verification satisfy Protocol Section 6 without trusting workflow-controlled predicate
   content beyond the Owner-pinned deterministic workflow?
9. Is `MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1` adequate for signed issuance time and trusted
   current time at expiry, or is any exact missing primitive still a BLOCKER/HIGH?
10. Are Issue #48 and live-CI claims now honest: dedicated PR evidence in Phase A, every-PR
    enforcement and Step 3 completion only after separately authorized Phase B merge?
11. Is the exact Tier 1 enumeration complete relative to the ratified matrix?
12. Is V2 eligible for presentation to the Owner for Decision A only, without silently making
    Decision B or C eligible?

Return `INSUFFICIENT_BOUND_TEXT` rather than infer any answer from an unbound file or live
state.

## 7. Required response format

The response must:

- declare `CLAUSE_BASE_USED` with every reviewed path and independently computed SHA-256;
- bind this packet SHA-256 and the dispatch-receipt SHA-256 supplied at invocation;
- disclose actual provider, model, tool/runtime version, reviewer role, and limitations;
- label `F_MACHINE`/`F_REPO`, `D_DERIVED`, and `E_JUDGMENT` separately;
- enumerate contradictions and every `BLOCKER`, `HIGH`, and `LOW` finding;
- answer all twelve questions;
- finish with exactly one `GO` or `NO_GO` verdict and exact finding counts;
- state `UNTRUSTED_CONTEXT_ONLY` and that it cannot satisfy Protocol Section 6 or grant
  Decision A, B, or C;
- return no recommendation to implement, merge, close Issue #48, open Test 3b, or open Test 4.

A response at or after the receipt's absolute deadline is retained only as
`LATE_RESPONSE_UNTRUSTED_CONTEXT`. No response becomes Owner authority.

## 8. Dispatch and tooling freeze

At invocation the reviewer receives:

- this frozen packet path and SHA-256;
- the separate dispatch receipt path and SHA-256;
- read-only `Read`, `Grep`, and `Glob`;
- narrowly allowed shell commands only for `shasum -a 256 <bound-path>` and `date -u`.

No write/edit command, Git mutation, network mutation, data reader, Python, model fit, CI
mutation, PR mutation, or merge command is allowed. The reviewer must read
`/Users/nonchaianon/Documents/Codex/MES_OBSIDIAN_MEMORY/CRASH_MEMORY.md` first as
non-authoritative context.

The packet is frozen when written. The receipt, response/outcome, Owner closeout, and
closeout receipt are separate additive artifacts. Attempt 002 can never modify or replace
Attempt 001.


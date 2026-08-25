# MES Execution Hardening Step 3 — Implementation Package V2

Package ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V2`

Status: **DRAFT COMPLETE / REVIEW REQUIRED / NO IMPLEMENTATION AUTHORITY**

Prepared date: `2026-08-25` (`Asia/Bangkok`)

Preparation base commit/tree: `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Preparation branch: `governance/execution-hardening-step3-package-v1`

Governing protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1` at
`docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md`, SHA-256
`697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7`

Surface map: `REHEARSAL_SURFACE_MAP_V2` at
`configs/governance/rehearsal_surface_map_v2.json`, SHA-256
`c459744e4c8c27ecfb4bdd08164671146ef59d468beb7a90a46a8b47d97670da`

Finite transition companion: `MES_EXECUTION_TRANSITION_EVENT_ENUM_V1` at
`configs/governance/execution_hardening_transition_events_v1.json`, SHA-256
`ec6c8e252837eb1a495f791ff12435eb8e4050cee23331f42808104098d759e2`

Live-state snapshot: `docs/governance/EXECUTION_HARDENING_STEP3_LIVE_STATE_SNAPSHOT_20260825.json`,
SHA-256 `6df56157cb13c7ba0383bcae70194e8b4e610184ca9e72a4d9258454fa2e1cf7`,
observed read-only at `2026-08-25T16:55:29Z`.

Superseded candidate: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V1`, SHA-256
`1c880624bdcbce3b65bc633b4f9fc9f735d34935278fd454fd4ba028e86008ca`.
Its Attempt 001 response is sealed at
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260825_001_RESPONSE.md`,
SHA-256 `31940a99077e9cbd20b891fdf9b2b3bb84274c34fe1f1d81a1a8e372ecf89c13`,
with `NO_GO / BLOCKER=4 / HIGH=17 / LOW=8`.

This V2 is additive. It does not change or reinterpret Attempt 001. It is an engineering
proposal, not Owner authorization, trusted attestation, CI permission, execution reservation,
scientific protocol, target-space action, push permission, PR permission, or merge permission.

## 1. Exact bounded outcome

Step 3 proves the two ratified engineering properties only:

1. known-invalid states stop at the intended stage and exact reason; and
2. one isolated synthetic happy path traverses the generic ladder and seals rehearsal evidence
   that cannot be accepted as scientific evidence.

Historical Test 2/Test 3 files remain byte-identical. No Test 3 repair, retry, Test 3b, Test 4,
real data, target/path access, production fit, Validation, or Final Test is opened.

## 2. Authority is deliberately split into three decisions

### 2.1 Package anchoring decision — docs/config only

Before an implementation decision, the Owner must separately authorize one create-once
package-closeout commit and one push to
`refs/heads/governance/execution-hardening-step3-package-v1`. That commit may contain only the
V1/Attempt-001 chain plus the V2 package, V2 map, transition companion, live-state snapshot,
V2 decision request, V2 Clause Packet, dispatch receipt, terminal response, and later Owner
package-closeout artifacts. The exact commit/tree then becomes eligible to be named as a
Phase A base. Creating the local preparation branch did not create a commit, push, PR, or
implementation authority.

### 2.2 Phase A — implementation and dedicated PR, no merge and no Tier 2

Phase A requires a later Owner statement bound to the exact package-closeout commit/tree. It
may implement the exact source allowlist, run Tier 1 locally and in the dedicated PR, push only
the exact implementation branch, and open exactly one new PR from that branch to `main`.

Phase A does **not** authorize merge, `main` mutation, the ready sentinel, a trusted-root file,
Section 6 acceptance, any Tier 2 reservation, Issue #48 mutation, or Step 3 completion. PR #47
is untouched. Issue #48 remains OPEN. A passing executed-frozen test on the dedicated PR proves
checkout safety only; it does not yet prove “every PR in live CI.”

### 2.3 Phase B — separate activation/merge/Tier 2 authority

Only a later Phase B Owner statement may authorize the exact reviewed Phase A PR head for
merge, the exact Phase B activation record, a frozen trusted-root file, the ready sentinel,
and at most two GitHub-hosted Tier 2 attempts. Phase B must pin the exact workflow blob
SHA-256, source tree, post-change Quant CI digest, trusted-root digest, and activation diff.

Step 3 remains incomplete until the executed-frozen test is merged to the default branch and
machine-observed on every later PR. A failed Phase B gate consumes its declared attempt when
applicable, stops closed, and requires new exact Owner authority for any repair commit or merge.
There is no implicit repair or success-only commit allowance.

## 3. Frozen inputs and packaging closure

Implementation may read but may not modify:

- the three co-ratified hardening documents and Owner ratification record;
- this V2 package, its review chain, V2 map, transition companion, and live-state snapshot;
- every historical Test 2/Test 3 source, protocol, evidence, budget, authorization, amendment,
  and ratification record;
- `pyproject.toml` SHA-256
  `1cd4c741978f709b43f1b4f198aa59ecf558082c258e3386d62fcaa7bd565be2`;
- `src/mes_quant/governance/__init__.py` SHA-256
  `719cf77d1ad07027b26917a841639ac07d0a10a11c125f509d2ba025f042ba6b`;
- `tests/governance/__init__.py` SHA-256
  `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`.

Hatch already packages `src/mes_quant`; the parent source and test packages already exist.
No dependency or packaging change is needed or authorized.

## 4. Exact two-phase source allowlist

These exact 25 paths, and no others, are the union of both future phases:

1. `.github/workflows/quant-ci-v1.yml`
2. `.github/workflows/execution-hardening-attestation-v1.yml`
3. `configs/governance/executed_frozen_registry_v1.json`
4. `configs/governance/execution_hardening_attestation_ready_v1.json`
5. `configs/governance/sigstore_trusted_root_v1.jsonl`
6. `configs/governance/execution_hardening_attempt_ledger_schema_v1.json`
7. `src/mes_quant/governance/execution_hardening/__init__.py`
8. `src/mes_quant/governance/execution_hardening/boundary.py`
9. `src/mes_quant/governance/execution_hardening/records.py`
10. `src/mes_quant/governance/execution_hardening/attestation.py`
11. `src/mes_quant/governance/execution_hardening/registry.py`
12. `src/mes_quant/governance/execution_hardening/executed_frozen.py`
13. `src/mes_quant/governance/execution_hardening/rehearsal.py`
14. `tools/build_execution_hardening_review_report.py`
15. `tools/run_execution_hardening_rehearsal.py`
16. `tools/verify_execution_hardening_attestation.py`
17. `tests/governance/test_execution_hardening_boundary.py`
18. `tests/governance/test_execution_hardening_records.py`
19. `tests/governance/test_execution_hardening_attestation.py`
20. `tests/governance/test_execution_hardening_registry.py`
21. `tests/governance/test_execution_hardening_executed_frozen.py`
22. `tests/governance/test_execution_hardening_rehearsal.py`
23. `tests/governance/test_execution_hardening_ci_spec.py`
24. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_OWNER_AUTHORIZATION_V1.md`
25. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_OWNER_ACTIVATION_V1.md`

Phase A may change paths 1–3, 6–24. Path 24 must be the sole path in its first commit. Path 1
may add only the Issue #48 checkout-safe executed-frozen integrity test; existing jobs and
gates may not weaken. Paths 4, 5, and 25 are reserved for Phase B and forbidden in Phase A.

Phase B may change only paths 4, 5, and 25 unless its later exact Owner statement explicitly
authorizes a reviewed repair path from the same union. Path 25 must be the sole path in the
first Phase B commit. Runtime artifacts are not source changes and may exist only below the
V2 map's isolated relative rehearsal namespace; they may not be committed without later
authority.

## 5. Component and runtime boundaries

### 5.1 Boundary, records, and finite transitions

`boundary.py` owns byte-semantic identity, finite scalar classification, integral `{0,1}`
normalization, ordered projected Arrow schema/type/nullability, and non-empty consumer
rehearsal. `records.py` owns the exact V1 states and reads the finite event/transition companion
without extending it. A tuple not present in the companion fails `INVALID_TRANSITION`.

### 5.2 Attempt ledger and exact runtime path

Path 6 defines the closed append-only attempt-ledger schema. Every Tier 2 run writes only:

```text
artifacts/rehearsal/REHEARSAL_EXECUTION_HARDENING_V1/<run-id>/attempt_ledger.jsonl
```

under its isolated artifact root. The entry binds attempt ID, ordinal, packet/package/report
hashes, reviewer role, expected signer/model, issued time, bounded expiry, reservation state,
outcome, and receipt hash. Exclusive creation prevents attempt-ID replay. A cancelled or rerun
job that has passed the atomic reservation step consumes one attempt; a job that stops before
that step does not. A rerun is always a new attempt identity.

### 5.3 Evidence sealing and the two exact root identities

Rehearsal records require
`sealing_trust_root=MES_REHEARSAL_EPHEMERAL_SHA256_SEAL_ROOT_V1`. That identity is accepted by
the rehearsal policy only and means exclusive-create seal, reread, SHA-256, V2-map binding,
and rehearsal registry acceptance.

The production runtime policy recognizes
`sealing_trust_root=NOT_YET_RATIFIED_PRODUCTION_TRUST_ROOT` only as a closed **reject-always**
sentinel. No production record can seal or register under this package. The canonical
production-schema positive fixture uses
`MES_TEST_FIXTURE_PRODUCTION_TRUST_ROOT_V1` only through an injected in-memory test policy;
the runtime production policy rejects that identity and the fixture cannot be emitted,
persisted, sealed, or registered.

The relative namespace is materialized under a temporary local root for local preflight and
under the GitHub Actions workspace for Phase B. The Phase B run uploads the same relative
tree as the durable attested workflow artifact. No runtime record is committed to Git.

### 5.4 Production governance ledger set

At the preparation base there is no runtime production-ledger implementation or handle. The
closed set is therefore exactly empty and is bound by canonical empty-manifest SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Tier 2 constructors accept rehearsal handles only; any attempted non-empty production handle
injection stops before reservation. Before/after checks must reproduce the same empty-manifest
hash. This does not claim that historical governance documents or evidence are nonexistent;
it states only that they are immutable files, not writable runtime ledger handles.

## 6. Synthetic budgets and deterministic seed

Phase A permits no Tier 2 reservation. Phase B may permit at most two GitHub-hosted Tier 2
reservation consumptions. Per reservation:

```text
synthetic_models = 2
synthetic_folds = 2
synthetic_fold_fit_calls <= 4
bootstrap_blocks <= 3
bootstrap_repetitions_per_block = 64
synthetic_bootstrap_replicates_total <= 192
economic_diagnostic_calls <= 1
economic_policy_evaluations <= 2
real_data_or_target_reads = 0
real_fits = 0
real_bootstraps = 0
validation_reads = 0
final_test_reads = 0
seed_namespace = REHEARSAL_EXECUTION_HARDENING_V1
seed = 2026082501
```

Tier 1 unit fixtures consume no Tier 2 reservation and emit no sealed evidence.

## 7. Section 6 trusted-attestation design

### 7.1 Bootstrap and activation boundary

Phase A workflow output is CI evidence only and is not Section 6 trusted. After a separately
authorized merge places the exact workflow bytes on protected `main`, Phase B must pin the
exact workflow Git blob and SHA-256 in its Owner activation record before the ready sentinel
can activate Tier 2. The attested subject commit and source digest must equal the exact
activation merge commit. This removes branch-local self-attestation as an authority source.

### 7.2 Exact signer and verification roots

```text
reviewer_identity = EXECUTION_HARDENING_DETERMINISTIC_REVIEWER_V1
provider = GitHub Actions OIDC / Sigstore
model = NONE_DETERMINISTIC_RULE_ENGINE
tool_runtime_version = gh 2.97.0
review_role = SECTION6_DETERMINISTIC_RELEASE_REVIEWER
signer_workflow = NonChaianon/mes-quant-engine-v1/.github/workflows/execution-hardening-attestation-v1.yml
source_ref = refs/heads/main
oidc_issuer = https://token.actions.githubusercontent.com
action = actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6
predicate_type = https://slsa.dev/provenance/v1
trust_root_path = configs/governance/sigstore_trusted_root_v1.jsonl
trust_root_bootstrap = Sigstore public-good TUF root chain initialized from metadata/root_history/10.root.json
trusted_time_policy = MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1
```

The Phase B record must pin the exact trust-root file SHA-256, signer workflow SHA-256/Git
blob, source commit/tree, and `gh` version. Verification uses `gh attestation verify` with
`--custom-trusted-root`, exact repo, signer workflow, `--signer-digest`, source ref,
`--source-digest`, OIDC issuer, predicate type, and `--deny-self-hosted-runners`.

Only certificate identity and `verifiedTimestamps` are external Sigstore facts. The trusted
time-policy identity uses the verified Sigstore timestamp as issuance time and a newly minted,
issuer-verified GitHub Actions OIDC token `iat` as current time at the expiry gate. Both claims
must validate under the pinned roots; the current-time claim must be earlier than bounded
expiry. A stale or absent claim stops before reservation.

The new attestation workflow explicitly requires only:

```text
contents: read
id-token: write
attestations: write
```

This privilege delta is limited to path 2 and is explicitly part of the later Owner decision.
Existing `Quant CI V1` remains `contents: read` and receives no OIDC or attestation permission.

### 7.3 Closed report field set — exact one-to-one transcription

The deterministic report and signed predicate must bind exactly:

1. repository identity;
2. branch/ref;
3. commit;
4. tree;
5. diff base;
6. exact allowlist;
7. ordered file SHA-256 values;
8. reviewer identity;
9. provider;
10. model;
11. tool/runtime version;
12. review role;
13. prompt/Clause-Packet SHA-256;
14. exact `clause_packet_operating_mode=FULL_GOVERNED`;
15. report SHA-256;
16. verdict;
17. explicit BLOCKER count;
18. explicit HIGH count;
19. completion status;
20. issued timestamp;
21. bounded expiry;
22. trusted time-source policy identity;
23. trusted signature/service receipt.

The predicate additionally carries the signer-workflow blob/SHA-256 and subject source digest
as non-authorization diagnostic bindings; the verifier must compare them, but they do not
silently extend the closed authorization field set.

Claude Opus remains only Exit Criterion 10(b) fresh-eyes judgment under `FULL_GOVERNED`, with
`UNTRUSTED_CONTEXT_ONLY`; it cannot satisfy Section 6 or authorize a reservation.

## 8. Issue #48, CI, and PR boundary

The live snapshot records Issue #48 OPEN and PR #47 OPEN/DRAFT/BLOCKED at
`2026-08-25T16:55:29Z`; these facts must be re-observed immediately before any Owner decision.

Phase A proposes to subsume the exact Issue #48 code change and permits opening one dedicated
new PR. It does not permit editing or closing Issue #48, touching PR #47, or merging. Phase B
must separately authorize merge. Issue #48 becomes eligible for later closeout only after the
executed-frozen test is live on default-branch CI and observed on a subsequent PR.

The only control added to existing `Quant CI V1` is:

- `EXECUTED_FROZEN_BYTE_INTEGRITY_V1` — registry path existence, SHA-256 equality, and a
  one-byte drift negative fixture.

The new execution-hardening workflow separately enumerates these Tier 1 control groups:

1. identity pipe preservation and CR/LF rejection;
2. finite scalar and integral `{0,1}` flag normalization/rejection;
3. ordered Arrow schema/type/nullability and non-empty consumer rehearsal;
4. predictor positive/zero/negative/nonfinite stage outcomes;
5. synthetic request, target, common-mask, fold, harmonic, rank, and support outcomes;
6. zero-variance target exact stop before common mask/fit;
7. every finite target-access transition triple and every finite complement tuple;
8. every finite execution-authority transition triple and every finite complement tuple;
9. missing, mismatched, timeout/NO_VERDICT, rejected, expired, signer-invalid,
   reviewer-identity-invalid, packet/report-invalid, packet-mode-invalid, and replay
   attestation outcomes, each with attempt budget remaining and exhausted where applicable;
10. unauthorized reservation consumption and monotone boolean behavior;
11. production/rehearsal own-class positive fixtures and bidirectional rejection;
12. every single and combined rehearsal-marker mutation;
13. missing production binding and invalid `NO_SOURCE_ARTIFACT_ACCESSED` use;
14. V2 surface-map absence/mutation/hash mismatch;
15. clean Tier 1 happy-path eligibility;
16. protected-counter, no-output-on-stop, and empty production-handle manifest assertions.

## 9. Exact gates and phase completion

### 9.1 Phase A gates

1. all ratified Tier 1 rows and the enumerated groups above pass;
2. full `pytest` and Ruff pass;
3. exact changed-file firewall passes;
4. historical Test 2/Test 3 hashes remain unchanged;
5. all real counters remain zero;
6. dedicated PR Quant CI passes the executed-frozen test;
7. new hardening workflow passes in non-authoritative Tier 1 mode;
8. a final `FULL_GOVERNED` fresh-eyes review returns BLOCKER=0/HIGH=0.

Phase A completion still does not satisfy Protocol Exit Criteria 2, 3, or Section 6.

### 9.2 Phase B gates

1. exact Phase A PR head and Phase B activation diff receive separate Owner authority;
2. merge/default-branch source and workflow digests equal the activation bindings;
3. pinned trust root and exact `gh` verifier policy pass;
4. Section 6 report/attestation passes before reservation;
5. one Tier 2 happy path seals, rereads, hashes, uploads, and attests the V2 namespace;
6. every real counter remains zero and the empty production-handle manifest is unchanged;
7. production registry rejects every rehearsal artifact;
8. executed-frozen integrity runs in live default-branch CI on a subsequent PR;
9. final exact-code Clause Packet review returns BLOCKER=0/HIGH=0.

Only then may the Owner consider Step 3 complete. Issue #48 closeout still requires separate
authority.

## 10. Commit, push, attempt, and failure posture

Package anchoring: one docs/config-only closeout commit and one push, only after exact Owner
authority.

Phase A proposal: one authorization-record commit plus at most seven implementation/repair
commits; one ordinary push after each; one dedicated PR may be opened; no merge. The ready
sentinel is forbidden. Findings or test failures may be repaired only while commit budget
remains; exhaustion stops closed and requires new Owner authority.

Phase B proposal: one activation-record commit, then at most two bounded activation commits
for the trusted-root file and ready sentinel, with exact later Owner authority. At most two
GitHub Tier 2 reservation consumptions are allowed. Cancellation or rerun after the atomic
reservation step consumes an attempt. Failure after budget exhaustion stops closed; any repair
commit, new PR, or merge requires a new Owner statement.

No force-push, amend, rebase, squash, tag, release, PR #47 mutation, hidden Issue #48 mutation,
or unapproved `main` mutation is permitted.

## 11. Attempt 001 remediation ledger

| Finding | V2 disposition |
| --- | --- |
| BLOCKER-01 | Sections 2, 8, and 9 split PR evidence from later merge/live-CI authority |
| BLOCKER-02 | V2 map and Section 5.3 name rehearsal, reject-always production, and fixture-only roots |
| BLOCKER-03 | Quant CI moved from immutable regression source to mutable pre/post baseline |
| BLOCKER-04 | V2 map adds request, fold, harmonic, and maps all 25 paths |
| HIGH-01 | V2 decision request must pin the final V2 package digest literally |
| HIGH-02 | path 6 plus Section 5.2 names the exact append-only runtime ledger path |
| HIGH-03 | V2 map and Section 5.4 close the production runtime-ledger set as empty |
| HIGH-04 | Section 7.2 discloses exact workflow permission escalation |
| HIGH-05 | Phase B pins main-hosted workflow blob, source digest, and Owner activation before Tier 2 |
| HIGH-06 | Section 7.2 names one combined signed issuance/current-time policy |
| HIGH-07 | Section 10 gives bounded repair capacity and explicit stop/new-authority behavior |
| HIGH-08 | Phase A has zero Tier 2; Phase B defines exactly two reachable attempts and cancellation/rerun semantics |
| HIGH-09 | V2 map binds the Test 2 authorization, execution record, witness, and Erratum authority chain |
| HIGH-10 | Section 2 requires separate package anchoring authority before commit/push |
| HIGH-11 | Section 8 enumerates all CI control groups |
| HIGH-12 | V2 map and Section 5.3 define relative temp/workspace namespace and durable upload |
| HIGH-13 | Section 7.3 enumerates the closed Section 6 field set one-to-one |
| HIGH-14 | Section 7.2 pins `gh`, custom trusted-root path/bootstrap, and later exact root digest |
| HIGH-15 | additive finite event companion makes the complement finite without changing transitions |
| HIGH-16 | Section 3 binds packaging and existing parent-package bytes |
| HIGH-17 | the next dispatch supplies packet and receipt hashes and permits hash/time commands only |
| LOW-01..03 | next packet uses exact, contiguous clause ranges and binds Sections 7.2/7.3 |
| LOW-04 | no scope assertion is labeled `F_MACHINE` without an evidence artifact |
| LOW-05 | live facts moved to a timestamped hash-bound snapshot |
| LOW-06 | package commit/tree is explicitly preparation base; anchoring requires separate Owner authority |
| LOW-07 | operational trust uses exact action commit, verifier version, and custom root; URLs are informational |
| LOW-08 | decision request supplies fields/checklists, not an adopt-by-default Owner statement; seed is exact |

## 12. Forbidden actions

- no implementation, CI edit, push, PR opening, merge, or Tier 2 before the exact phase authority;
- no historical Test 2/Test 3 mutation or execution;
- no Test 3 repair/retry, Test 3b, Test 4, hypothesis, or target-space action;
- no real DBN/Parquet/artifact metadata, row group, statistics, numeric value, target, or path access;
- no production fit, loss, bootstrap, diagnostic, evidence, Validation, or Final Test;
- no production runtime ledger or production trust/signing credential;
- no dependency, database, broker, live, release, tag, force-push, amend, rebase, or squash;
- no Issue #48 mutation or PR #47 mutation;
- no permission beyond the exact two workflows and permission set in Section 7.2.

## 13. Decision boundary

This V2 may become eligible for Owner consideration only after a new `FULL_GOVERNED` review
returns BLOCKER=0/HIGH=0 and its exact bytes are anchored under separate authority. Review
PASS, hashes, branch existence, or silence grants nothing. Phase A, Phase B, Issue #48 closeout,
Test 3b, Test 4, data, fit, Validation, Final Test, and merge each retain their stated separate
Owner gates.

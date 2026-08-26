# MES Execution Hardening Step 3 — Implementation Package V6

Package ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V6`

Status: **DRAFT COMPLETE / REVIEW REQUIRED / NO IMPLEMENTATION AUTHORITY**

Prepared date: `2026-08-26` (`Asia/Bangkok`)

Preparation base commit/tree: `ae3048cc8a58d8eec7cc42f99146c91e579d6582` /
`4f7aa3a719dcd781411d91166de82a4d4ffa573f`

Preparation branch: `governance/execution-hardening-step3-package-v1`

Governing protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1`, SHA-256
`697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7`.

Bound companions:

- `REHEARSAL_SURFACE_MAP_V5` — `configs/governance/rehearsal_surface_map_v5.json` —
  SHA-256 `87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a`;
- `MES_EXECUTION_TRANSITION_ROW_ENUM_V3` —
  `configs/governance/execution_hardening_transition_rows_v3.json` — SHA-256
  `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1`;
- `MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1` —
  `configs/governance/execution_hardening_time_policy_v1.json` — SHA-256
  `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e`;
- `EXECUTION_HARDENING_PRODUCTION_SURFACE_MANIFEST_V2` —
  `configs/governance/execution_hardening_production_surface_manifest_v2.json` — SHA-256
  `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a`.

Superseded candidates remain immutable:

- package V1 `1c880624…08ca`, Attempt 001 response `31940a99…9c13`;
- package V2 `809a3281…f4974`, Attempt 002 response `536dd97c…3c4b`, whose verdict was
  `NO_GO / BLOCKER=2 / HIGH=7 / LOW=7`;
- package V3 `ff8db968…911a9`, Attempt 003 response `6c702ccd…bc05`, whose verdict was
  `NO_GO / BLOCKER=0 / HIGH=2 / LOW=7`;
- package V4 `fc088c631a1db0370eb2920d7749eac502d17aac613caac2e9e57e95555dd8e5`,
  Request V4 `6425a2c762c542e89cdb3a6672ff5309d71989c38cc732c77811e7aab84979eb`,
  and Surface Map V4 `32bb79e444d18aa89993a50c3e102137eecb41b61996f8fd859ea807a472d51b`
  remain immutable at package-closeout commit
  `ae3048cc8a58d8eec7cc42f99146c91e579d6582` / tree
  `4f7aa3a719dcd781411d91166de82a4d4ffa573f`;
- package V5 `3c63a4b3e18aeaee29512954d7d04d99020fe9190d47d539ade67ab06ff28916`,
  Request V5 `7d1693a8e7882e6cd411f56be076617a11072733dc49587f20dbdb0d210bfbed`,
  Packet 005 `808f4b21dcd09200f29fb3434b4948d7eec94474f29a89bfb60575cdd1c7bd98`,
  receipt `5d1bf9802be5a6b66dc0e330661ecf1d8d783443ae94d60a63966f277f0cf7c4`,
  and terminal response `6cf62c251c6a4a78f66717e705988e98275b9e1f6ace6d2e84cc117eb24c6471`
  remain immutable NO_GO history (`BLOCKER=0 / HIGH=1 / LOW=2`; no retry).

V6 is an additive successor proposal that preserves every V4 and V5 byte plus the complete
Attempt 005 NO_GO chain. It corrects the V5 package-anchor collision and clarifies the Tier 1
live-reservation boundary without changing Surface Map V5 or any implementation path. It grants
no commit, push, implementation, CI, PR,
ruleset, merge, data, target, fit, Validation, Final Test, Test 3b, Test 4, or scientific
authority.

## 1. Exact bounded outcome

Step 3 proves only:

1. every known-invalid state stops at its ratified stage/reason; and
2. one generic synthetic happy path completes and seals rehearsal evidence that cannot become
   scientific evidence.

Historical Test 2/Test 3 bytes remain frozen. Step 3 consumes no hypothesis slot.

## 2. Three decisions with reachable ordering

### 2.1 Decision A — package anchoring only

After one clean V6 `FULL_GOVERNED` response exists, the Owner may decide whether to authorize one
docs/config-only package-closeout commit and one push to
`refs/heads/governance/execution-hardening-step3-package-v6`.

The Owner statement must bind every **already-existing V6** reviewed path and SHA-256 through the
terminal response. It must **not** bind the future Owner closeout, closeout-receipt, or external-
manifest hash. After the Owner statement is received, the closeout records the exact decision,
the closeout receipt records the complete closeout SHA-256, and
`docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json` records the
terminal closeout-receipt SHA-256 outside the Clause-Packet artifact set. The resulting commit
then anchors the manifest and all earlier bytes. This is the only valid ordering:

```text
packet -> dispatch receipt -> terminal response -> Owner statement
-> Owner closeout -> closeout receipt -> external closeout manifest
-> package-closeout commit -> one push
```

Decision A grants no Phase A implementation authority.

### 2.2 Decision B — Phase A implementation and one dedicated PR

After Decision A is executed, a separate Owner statement may co-ratify the four companion
artifacts at the exact package-closeout commit and authorize Phase A from that exact base.
Phase A may implement Tier 1, push only the implementation branch, and open one dedicated PR.
It permits zero Tier 2 reservations and no merge, `main`, ruleset, Issue #48, or PR #47 mutation.

### 2.3 Decision C — Phase B merge, required-workflow ruleset, and Tier 2

After Phase A completes with a clean fresh-eyes review, a separate Owner statement may bind the
exact PR head, merge diff, workflow/root/source hashes, and repository ruleset payload. Only
Decision C may authorize merge, exact ruleset mutation, trusted activation, and at most two
GitHub-hosted Tier 2 attempts.

Step 3 remains incomplete until the required workflow is active with no bypass actor and a
rule-suite observation proves that the default-branch workflow runs for a subsequent PR.

## 3. Frozen inputs and co-ratification boundary

The four current companions above are frozen inputs. Decision B must explicitly co-ratify their exact
IDs, paths, and SHA-256 values before code may read them as governing configuration. In
particular, the transition companion is not authority merely because it parses as JSON.

The transition-equivalence test must parse only the exact Markdown data rows 123–136 and
142–161. Under the companion's closed extraction rule it excludes header/delimiter rows,
removes only Markdown backtick delimiters from inline-code spans, preserves every enclosed
character and all other punctuation, requires `event_text` to equal only the normalized Event
cell, expands From/To states, and separately asserts the ratified To-cell reason qualifiers at
lines 131, 149, 151, and 152. It then proves equality of the complete triple sets. `records.py`
rejects any companion whose protocol hash, event-text equivalence, reason mapping, or triple
proof fails.

Packaging closure is already bound by:

- `pyproject.toml` SHA-256 `1cd4c741…65be2`;
- `src/mes_quant/governance/__init__.py` SHA-256 `719cf77d…ba6b`;
- `tests/governance/__init__.py` SHA-256 `01ba4719…546b`.

No dependency or packaging edit is authorized.

## 4. Exact 37-path two-phase change union

Only these paths may change under later exact phase authority:

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
26. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1.md`
27. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_DISPATCH_RECEIPT.md`
28. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_RESPONSE.md`
29. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_OWNER_CLOSEOUT.md`
30. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_CLOSEOUT_RECEIPT.md`
31. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_CLOSEOUT_MANIFEST_V1.json`
32. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1.md`
33. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_DISPATCH_RECEIPT.md`
34. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_RESPONSE.md`
35. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_OWNER_CLOSEOUT.md`
36. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_CLOSEOUT_RECEIPT.md`
37. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_CLOSEOUT_MANIFEST_V1.json`

Phase A subset is paths 1–3, 6–24, and 26–31: exactly 28 paths. Path 24 must be its sole first
commit. Paths 26–31 are created only after implementation bytes freeze and in forward order;
path 31 records path 30's complete SHA-256 before the final Phase A evidence-chain commit.

Phase B subset is paths 4, 5, 25, and 32–37: exactly 9 paths. Path 25 must be its sole first
commit. Paths 32–37 are created in forward order; path 37 records path 36's complete SHA-256
before the final Phase B evidence-chain commit. A Phase B repair may change only these nine
paths while its exact later Owner budget remains; any source/CI repair requires a new Decision B
lineage and Owner statement. Runtime rehearsal artifacts remain outside source Git and only
under the mapped isolated namespace.

## 5. Transition, time, and production-surface controls

### 5.1 Finite transitions

The `MES_EXECUTION_TRANSITION_ROW_ENUM_V3` companion has 14 target rows and 20 execution rows, one per selected ratified Markdown
data row under its exact extraction rule. The
mechanical expansion yields 18 target triples and 22 execution triples. Complement counts are
`5*14-18=52` and `7*20-22=118`. Every complement tuple rejects. Phase A Owner co-ratification
and the independent equivalence test are both mandatory.

### 5.2 Time policy

`MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1` is the complete defining artifact. It freezes:

- verified Sigstore timestamp as issuance time;
- issuer- and audience-verified GitHub OIDC `iat` as current time;
- maximum token age `300s`, clock skew `60s`, attestation age `1800s`;
- exact expiry relation, evaluation order, and stop codes.

No prose-only meaning or unspecified “stale” test is accepted.

### 5.3 Production surface discovery

The production-surface manifest discovers every Git-tracked file under its exact governance,
authorization, budget, and ratification patterns at the exact Phase B activation tree. Its
before snapshot occurs only after all authorized Phase B setup paths are committed and the
working tree is clean; its after snapshot occurs immediately after Tier 2 seals and rereads,
before any Phase B final review-chain or closeout-manifest artifact is created. During that
window Tier 2 may write only below its isolated temporary rehearsal root. The manifest requires
identical ordered path and actual-byte digest lists, clean Git firewalls, and no untracked file
under a protected root. Separately allowlisted post-window review-chain writes cannot excuse or
redefine a Tier 2 mutation. This is not the V2 constant-empty-manifest check.

The constructor separately accepts only `REHEARSAL_ONLY_HANDLE_SET_V1`; injecting a production
target-slot, authorization, attempt, repair, evidence-registry, or signing handle stops before
reservation.

## 6. Evidence roots and canonical fixture

Rehearsal runtime root:
`MES_REHEARSAL_EPHEMERAL_SHA256_SEAL_ROOT_V1 / REHEARSAL_ONLY`.

Production runtime root:
`NOT_YET_RATIFIED_PRODUCTION_TRUST_ROOT / REJECT_ALWAYS`.

Canonical in-memory fixture root:
`MES_TEST_FIXTURE_PRODUCTION_TRUST_ROOT_V1 / IN_MEMORY_TEST_POLICY_ONLY`.

There is one production-registry core predicate with a mandatory injected trust policy and no
global/default policy. The canonical fixture runs through that same core predicate—no mock,
monkeypatch, or alternate validator—and must PASS under the exact fixture policy. The same
record must STOP under the runtime reject-always policy. The fixture cannot be emitted,
persisted, sealed, or registered. This directly satisfies the protocol's “PASS in memory only”
row while keeping production sealing impossible.

Both PASS and STOP directions are explicit Phase A and Phase B gates.

## 7. Synthetic budget

Phase A mode is `TIER1_ONLY_NON_AUTHORITATIVE`. It permits exactly zero live Tier 2
reservations created or consumed, zero Tier 2 attempts, zero runtime rehearsal-runner
executions, zero persisted attempt ledgers, and zero emitted, persisted, sealed, uploaded,
attested, or registered rehearsal-evidence records.

Tier 1 may construct only deterministic in-memory fixtures or fixtures below a pytest-owned
temporary directory with identity `NON_EVIDENTIARY_TIER1_FIXTURE`. They may cover synthetic
Arrow rows, predictors, targets, masks, folds, harmonics, and reservation-state behavior required
by the ratified Tier 1 matrix. Temporary fixtures remain outside `artifacts/rehearsal/` and every
production namespace. Each fixture may exercise serialization, exclusive-create, reread, and
SHA-256 only. It may not upload, attest, register, create evidence or authority, or create or
consume a live Tier 2 reservation. The same-core canonical production
fixture may PASS only under the exact in-memory test policy and must STOP under the runtime
reject-always policy.

The following Phase A real/scientific counters are exactly zero: real artifact-metadata, row-group,
statistics, numeric-value, target, and path reads; real target constructions; real models and fold
fits; real bootstrap replicates; real economic-diagnostic calls; Validation and Final-Test reads;
production scientific outputs; and hypothesis slots consumed. Synthetic target fixtures required by
Tier 1 are not real target access and need not have zero in-memory construction counters.

Phase A Tier 2 reservations: exactly `0`.

Phase B: at most two GitHub-hosted reservations. Per reservation:

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

A cancellation or rerun consumes only after the atomic reservation step; every rerun gets a
new attempt identity. Exhaustion stops closed.

## 8. Section 6 trust without extending its closed field set

The deterministic report binds exactly the ratified 23 fields, one-to-one and no more. The
workflow file SHA-256 is already one entry in the ratified “ordered file SHA-256 values” field.
The attested source commit is already the ratified `commit` field. `--signer-digest` and
`--source-digest` compare certificate/service metadata to those existing values; neither is a
new predicate/report field.

Exact mechanism:

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
trusted_time_policy = MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1
```

Phase B pins the exact custom-root hash, workflow file hash/Git blob, source commit/tree, and
post-change Quant CI hash. Verification uses exact repo/workflow/ref, `--signer-digest`,
`--source-digest`, OIDC issuer, predicate type, `--custom-trusted-root`, and
`--deny-self-hosted-runners`.

Quant CI remains `contents: read` and may gain only
`EXECUTED_FROZEN_BYTE_INTEGRITY_V1`. Broader Tier 1 controls enter only the new hardening
workflow. `pull_request_target`, workflow-level write permission, automatic merge, and GitHub
mutation APIs are forbidden. All PR and Tier 1 jobs remain `contents: read`.

Only a signer job may declare job-scoped `id-token: write` and `attestations: write`. It must be
guarded by exact `github.event_name == workflow_dispatch` and
`github.ref == refs/heads/main`. Its OIDC and `actions/attest` steps additionally require the
Phase B ready sentinel, exact custom-root hash, activation commit/tree, and separate Decision C.
Those prerequisites are absent in Phase A, so signer jobs and signing steps are mechanically
unreachable. Phase A forbids OIDC minting, `actions/attest` invocation, attestation issuance or
acceptance, Section 6 activation, production trust, and every reservation.

Claude Opus remains `UNTRUSTED_CONTEXT_ONLY` under Exit Criterion 10(b).

## 9. Issue #48 and enforce-every-PR mechanism

Phase A may add only `EXECUTED_FROZEN_BYTE_INTEGRITY_V1` to Quant CI and open one dedicated PR.
The PR may not enable auto-merge and no workflow may use `pull_request_target`.
It proves checkout safety, not enforcement.

Decision C must separately authorize one external repository-ruleset mutation:

```text
ruleset_id = MES_EXECUTION_HARDENING_REQUIRED_WORKFLOW_RULESET_V1
repository_id = 1329447686
target = ~DEFAULT_BRANCH
rule_type = workflows
workflow.repository_id = 1329447686
workflow.path = .github/workflows/quant-ci-v1.yml
workflow.ref = refs/heads/main
workflow.sha = RESOLVE_AT_DECISION_C_TO_EXACT_PHASE_B_ACTIVATION_MAIN_SHA
enforcement = active
bypass_actors = []
do_not_enforce_on_create = false
```

The symbolic `workflow.sha` is not an authorized literal or placeholder accepted by a gate.
Decision C must replace it with and bind the exact 40-hex `main` SHA observed after the
authorized merge and before ruleset activation.

This uses GitHub's required-workflow ruleset primitive, not only a status-check observation.
The Phase B gate must read the ruleset and rule-suite API back, prove exact field equality and
no bypass, and observe a subsequent PR rule suite requiring and passing the workflow. A PR that
removes or changes the workflow cannot bypass the default-branch required workflow.

Issue #48 remains OPEN until separate closeout authority. PR #47 remains untouched.

## 10. Complete Tier 1 control enumeration

The new workflow runs these exact groups:

1. identity pipe preservation and CR/LF rejection;
2. finite scalar and integral `{0,1}` flag behavior;
3. ordered Arrow schema/type/nullability and non-empty consumer rehearsal;
4. every Cell 12 null/non-null combination, including `LABEL_UNUSABLE`, nullable
   `path_instrument_changed`, and path-count/path-metric fields;
5. predictor positive/zero/negative/nonfinite outcomes;
6. request, target, common mask, fold, harmonic, rank, and support outcomes;
7. zero-variance target stop before common mask/fit;
8. all 18/22 allowed transition triples and all 52/118 complement tuples;
9. every Section 6.1 failure outcome with remaining/exhausted attempts where applicable;
10. exact valid, unexpired, exact-package PASS with BLOCKER/HIGH=0, no Owner authority yet:
    gate PASS, state remains `REVIEW_PENDING`, no authority inferred;
11. unauthorized reservation and monotone boolean behavior;
12. both registries' own-class positive fixtures and opposite-class rejection;
13. same production core predicate fixture PASS under test policy and STOP under runtime policy;
14. every single and combined rehearsal-marker mutation;
15. missing production binding and invalid `NO_SOURCE_ARTIFACT_ACCESSED` use;
16. surface-map/companion/time-policy/production-manifest absence or hash mismatch;
17. transition companion versus protocol Markdown equivalence;
18. clean Tier 1 happy path, protected counters, no output on stop, handle-injection stop;
19. protected production-surface before/after actual-file hashes;
20. Phase A and Phase B exact changed-file/staged-file firewalls.

Existing Quant CI receives only the executed-frozen integrity control. The required-workflow
ruleset later makes that exact default-branch workflow mandatory for every PR.

## 11. Gates and failure posture

The V6 preparation lineage has exactly one fresh `FULL_GOVERNED` review attempt. A timeout,
`NO_VERDICT`, invalid packet, or BLOCKER/HIGH finding against unchanged V6 bytes stops the
lineage; it creates no retry or fallback reviewer authority. Phase A likewise has exactly one
create-once final fresh-eyes review chain at its six exact paths; a failed or late response
requires new Owner authority and new additive paths.

Phase A requires: all Tier 1 controls, full pytest, Ruff, allowlist firewall, historical hashes,
real counters zero, dedicated-PR CI, non-authoritative hardening CI, and exact six-artifact
fresh-eyes chain—packet, dispatch receipt, response, Owner closeout, closeout receipt, and
external closeout manifest—with BLOCKER=0/HIGH=0. The external manifest records the complete
closeout-receipt SHA-256 before the final evidence-chain commit. Phase A cannot claim Step 3
completion.

Phase B requires: exact Owner activation, merge/source equality, custom-root/time verification,
Section 6 PASS before reservation, canonical production fixture PASS and runtime-policy STOP,
one Tier 2 happy path, production-surface hashes unchanged inside the exact comparison window,
production registry rejection, active no-bypass required-workflow ruleset, subsequent PR
rule-suite PASS, exact changed/staged firewalls, and exact six-artifact final review chain with
BLOCKER=0/HIGH=0. The Phase B external manifest records the complete closeout-receipt SHA-256
before the final evidence-chain commit.

Package anchoring permits one commit/push only after Decision A. Phase A proposes one Owner
record commit plus at most seven implementation/repair commits and one final evidence-chain
commit, with one ordinary push after each and one dedicated PR. Phase B proposes one Owner
activation commit, at most two activation commits, and one evidence-chain commit, plus at most
two Tier 2 reservations. Any exhausted budget or out-of-subset repair stops closed and requires
new Owner authority.

No force-push, amend, rebase, squash, tag, release, auto-merge, hidden issue/PR mutation, or unapproved
external ruleset/main mutation is permitted.

## 12. Attempt 003 remediation ledger

| Attempt 003 finding | Historical V4 closure preserved by V6 |
| --- | --- |
| HIGH-01 | §2.1 names the package external manifest; paths 31 and 37 add one external closeout manifest per phase; §11 gates each terminal receipt hash before commit |
| HIGH-02 | V3 transition companion makes Event-cell extraction single-valued, fixes `TARGET_ROW_131`, and asserts To-cell reason qualifiers |
| LOW-01 | the equivalence range is exactly data rows 123–136 and 142–161 everywhere |
| LOW-02 | the companion defines backtick-delimiter normalization exactly |
| LOW-03 | reason mappings at lines 131, 149, 151, and 152 are explicit equivalence assertions |
| LOW-04 | 10(b) timing remains explicitly untrusted and has no release authority |
| LOW-05 | Decision C must resolve and bind the exact 40-hex activation SHA; the symbolic value is never accepted as authority |
| LOW-06 | production-surface V2 freezes the comparison window before review-chain writes |
| LOW-07 | external/live GitHub claims remain re-observation requirements, not trusted packet facts |

### 12.1 V5 pre-Decision-B repair ledger

| Fresh finding | V5 disposition |
| --- | --- |
| Surface Map V4 stale path count `thirty-five` | Surface Map V5 binds the unchanged exact 37-path array and states `thirty-seven` |
| Surface Map V4 stale review-chain count `ten` | V5 states five Clause-Packet paths plus one external manifest per phase: six per phase, twelve total |
| Fresh review-loop ambiguity | V5 permits exactly one fresh `FULL_GOVERNED` attempt; timeout or BLOCKER/HIGH stops with no retry on unchanged bytes |
| Phase A synthetic boundary ambiguity | V5 permits only deterministic in-memory/pytest-temp non-evidentiary fixtures; live Tier 2, persistent/sealed outputs, and real counters remain zero |
| Phase A attestation reachability ambiguity | signer jobs/steps are mechanically unreachable; OIDC minting, `actions/attest`, issuance/acceptance, and Section 6 activation are forbidden |
| PR trigger/merge ambiguity | `pull_request_target`, workflow-level write permission, automatic merge, and GitHub mutation APIs are forbidden |

### 12.2 Attempt 005 NO_GO closure ledger

| Attempt 005 finding | V6 disposition |
| --- | --- |
| `HIGH-06` — V5 package reused the immutable unversioned V4 external anchor | V6 names only `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json` for the current package-closeout chain; V4/V5 paths remain immutable history |
| `LOW-02` — stage arrays contain 45 references over 37 unique paths | V6 discloses 45 stage/test entries, 37 unique paths, eight repeated stage memberships, zero orphan paths, and zero paths outside the union; repetition grants no extra path |
| `LOW-03` — Attempt 003 table column said `V4 disposition` | the historical table header now reads `Historical V4 closure preserved by V6` |
| Tier 1 reservation wording | fixtures may not create or consume a live Tier 2 reservation |

Surface Map V5 remains byte-identical at SHA-256
`87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a`.

The current package-closeout external-anchor path must occur identically in Package V6, Request
V6, Packet 006, and any later Owner-authorized closeout chain. Any unversioned or V5 path used as
the current V6 anchor is a HIGH and stops the lineage.

## 13. Forbidden actions and decision boundary

- no inference of authority across Decisions A/B/C;
- no implementation, CI, PR, ruleset, merge, or Tier 2 before its exact decision;
- no historical Test 2/Test 3 mutation/execution, Test 3 retry, Test 3b, Test 4, or hypothesis;
- no real data/artifact metadata/row/statistics/value/target/path, production fit, Validation,
  Final Test, production runtime ledger, or production signing credential;
- no dependency, database, broker, live, release, or hidden permission;
- no Issue #48 or PR #47 mutation;
- no merge or external ruleset mutation except exact Decision C authority.

A clean V6 review makes only a new V6 package-anchoring Decision A eligible for Owner consideration. It grants nothing by
itself. Decision B requires the exact package-closeout commit/tree and companion
co-ratification. Decision C requires exact Phase A evidence and separate Owner authority.

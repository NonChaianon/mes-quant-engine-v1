# MES Execution Hardening Step 3 — Implementation Package V3

Package ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V3`

Status: **DRAFT COMPLETE / REVIEW REQUIRED / NO IMPLEMENTATION AUTHORITY**

Prepared date: `2026-08-26` (`Asia/Bangkok`)

Preparation base commit/tree: `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Preparation branch: `governance/execution-hardening-step3-package-v1`

Governing protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1`, SHA-256
`697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7`.

Bound companions:

- `REHEARSAL_SURFACE_MAP_V3` — `configs/governance/rehearsal_surface_map_v3.json` —
  SHA-256 `971f31dfe31904e74862b9296ab1d6a83e52661f13b5b6013d8249e34cc12152`;
- `MES_EXECUTION_TRANSITION_ROW_ENUM_V2` —
  `configs/governance/execution_hardening_transition_rows_v2.json` — SHA-256
  `56b1b66e653f5d883129a299c730b9f5d2f268c8567af9e9d7751027db7b8f8d`;
- `MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1` —
  `configs/governance/execution_hardening_time_policy_v1.json` — SHA-256
  `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e`;
- `EXECUTION_HARDENING_PRODUCTION_SURFACE_MANIFEST_V1` —
  `configs/governance/execution_hardening_production_surface_manifest_v1.json` — SHA-256
  `5fafa2312f0275713ae69fec843910cb887d41b161dbaeeb070e362176d5695f`.

Superseded candidates remain immutable:

- package V1 `1c880624…08ca`, Attempt 001 response `31940a99…9c13`;
- package V2 `809a3281…f4974`, Attempt 002 response `536dd97c…3c4b`, whose verdict was
  `NO_GO / BLOCKER=2 / HIGH=7 / LOW=7`.

V3 is an additive engineering proposal. It grants no commit, push, implementation, CI, PR,
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

After a clean V3 `FULL_GOVERNED` response exists, the Owner may decide whether to authorize one
docs/config-only package-closeout commit and one push to
`refs/heads/governance/execution-hardening-step3-package-v1`.

The Owner statement must bind every **already-existing** reviewed path and SHA-256 through the
terminal response. It must **not** bind the future Owner closeout or closeout-receipt hash.
After the Owner statement is received, those two additive artifacts record the decision and
forward-bind the statement, response, packet, receipt, and exact file set. The resulting commit
anchors them all. This is the only valid ordering:

```text
packet -> dispatch receipt -> terminal response -> Owner statement
-> Owner closeout -> closeout receipt -> package-closeout commit
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

The four V3 companions above are frozen inputs. Decision B must explicitly co-ratify their exact
IDs, paths, and SHA-256 values before code may read them as governing configuration. In
particular, the transition companion is not authority merely because it parses as JSON.

The transition-equivalence test must parse the exact Markdown rows at protocol lines 123–161,
compare one companion row per Markdown data row, compare exact source line/event text, expand
From/To cells, and prove equality of the complete triple sets. `records.py` rejects any
companion whose protocol hash or equivalence proof fails.

Packaging closure is already bound by:

- `pyproject.toml` SHA-256 `1cd4c741…65be2`;
- `src/mes_quant/governance/__init__.py` SHA-256 `719cf77d…ba6b`;
- `tests/governance/__init__.py` SHA-256 `01ba4719…546b`.

No dependency or packaging edit is authorized.

## 4. Exact 35-path two-phase change union

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
31. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1.md`
32. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_DISPATCH_RECEIPT.md`
33. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_RESPONSE.md`
34. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_OWNER_CLOSEOUT.md`
35. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_CLOSEOUT_RECEIPT.md`

Phase A subset is paths 1–3, 6–24, and 26–30: exactly 27 paths. Path 24 must be its sole first
commit. Paths 26–30 are created only after implementation bytes freeze and in forward order.

Phase B subset is paths 4, 5, 25, and 31–35: exactly 8 paths. Path 25 must be its sole first
commit. Paths 31–35 are created in forward order. A Phase B repair may change only these eight
paths while its exact later Owner budget remains; any source/CI repair requires a new Decision B
lineage and Owner statement. Runtime rehearsal artifacts remain outside source Git and only
under the mapped isolated namespace.

## 5. Transition, time, and production-surface controls

### 5.1 Finite transitions

The V2 companion has 14 target rows and 20 execution rows, one per ratified Markdown row. The
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
authorization, budget, and ratification patterns at the exact Phase B activation tree. It
hashes actual working-tree files before and after Tier 2 and requires identical ordered path
and digest lists, clean Git firewalls, and no untracked file under a protected root. This is
not the V2 constant-empty-manifest check.

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

Only the attestation workflow receives `contents: read`, `id-token: write`, and
`attestations: write`. Quant CI remains `contents: read`.

Claude Opus remains `UNTRUSTED_CONTEXT_ONLY` under Exit Criterion 10(b).

## 9. Issue #48 and enforce-every-PR mechanism

Phase A may add only `EXECUTED_FROZEN_BYTE_INTEGRITY_V1` to Quant CI and open one dedicated PR.
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
workflow.sha = exact Phase B activation main SHA
enforcement = active
bypass_actors = []
do_not_enforce_on_create = false
```

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

Phase A requires: all Tier 1 controls, full pytest, Ruff, allowlist firewall, historical hashes,
real counters zero, dedicated-PR CI, non-authoritative hardening CI, and exact five-artifact
fresh-eyes review chain with BLOCKER=0/HIGH=0. Phase A cannot claim Step 3 completion.

Phase B requires: exact Owner activation, merge/source equality, custom-root/time verification,
Section 6 PASS before reservation, canonical production fixture PASS and runtime-policy STOP,
one Tier 2 happy path, production-surface hashes unchanged, production registry rejection,
active no-bypass required-workflow ruleset, subsequent PR rule-suite PASS, exact changed/staged
firewalls, and exact five-artifact final review chain with BLOCKER=0/HIGH=0.

Package anchoring permits one commit/push only after Decision A. Phase A proposes one Owner
record commit plus at most seven implementation/repair commits and one final evidence-chain
commit, with one ordinary push after each and one dedicated PR. Phase B proposes one Owner
activation commit, at most two activation commits, and one evidence-chain commit, plus at most
two Tier 2 reservations. Any exhausted budget or out-of-subset repair stops closed and requires
new Owner authority.

No force-push, amend, rebase, squash, tag, release, hidden issue/PR mutation, or unapproved
external ruleset/main mutation is permitted.

## 12. Attempt 002 remediation ledger

| Attempt 002 finding | V3 disposition |
| --- | --- |
| BLOCKER-01 | §2.1 removes future closeout hash from the Owner statement and fixes forward order |
| BLOCKER-02 | §9 adds exact active/no-bypass required-workflow ruleset plus readback/rule-suite gates |
| HIGH-01 | §5.3 replaces empty constant with activation-tree discovery and real before/after hashes |
| HIGH-02 | Decision B co-ratifies V2 row companion; §3/§5.1 add Markdown equivalence proof |
| HIGH-03 | §10 group 10 adds the missing attestation PASS row |
| HIGH-04 | §8 maps signer/source comparisons onto existing closed fields, adds no predicate field |
| HIGH-05 | bound time-policy artifact defines ages, skew, relation, order, and stop codes |
| HIGH-06 | paths 26–35 give each phase's five-artifact review chain an exact anchored home |
| HIGH-07 | §6/§10/§11 gate same-core fixture PASS under test policy and STOP under runtime policy |
| LOW-01 | transition rows are one-to-one with source-line/event-text back-references |
| LOW-02 | Phase B repair scope is exactly eight paths in package and request |
| LOW-03 | no package review attempt capacity is asserted absent Owner authority |
| LOW-04 | 10(b) timing remains explicitly untrusted and has no release authority |
| LOW-05 | §10 group 4 enumerates exact Cell 12 combinations |
| LOW-06 | §10/§11 add Phase B changed/staged firewalls |
| LOW-07 | companion status is pending Owner ratification, not simultaneously proposed/ratified |

## 13. Forbidden actions and decision boundary

- no inference of authority across Decisions A/B/C;
- no implementation, CI, PR, ruleset, merge, or Tier 2 before its exact decision;
- no historical Test 2/Test 3 mutation/execution, Test 3 retry, Test 3b, Test 4, or hypothesis;
- no real data/artifact metadata/row/statistics/value/target/path, production fit, Validation,
  Final Test, production runtime ledger, or production signing credential;
- no dependency, database, broker, live, release, or hidden permission;
- no Issue #48 or PR #47 mutation;
- no merge or external ruleset mutation except exact Decision C authority.

A clean V3 review makes only Decision A eligible for Owner consideration. It grants nothing by
itself. Decision B requires the exact package-closeout commit/tree and companion
co-ratification. Decision C requires exact Phase A evidence and separate Owner authority.

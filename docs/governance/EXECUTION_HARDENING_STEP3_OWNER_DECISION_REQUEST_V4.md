# MES Execution Hardening Step 3 — Owner Decision Request V4

Request ID: `REQUEST_EXECUTION_HARDENING_STEP3_V4_20260826`

Status: **DRAFT REQUEST / REVIEW REQUIRED / NO AUTHORITY**

Package: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V4` at
`docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V4.md`, SHA-256
`fc088c631a1db0370eb2920d7749eac502d17aac613caac2e9e57e95555dd8e5`.

Bound companions:

- map `32bb79e444d18aa89993a50c3e102137eecb41b61996f8fd859ea807a472d51b`;
- transition rows `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1`;
- time policy `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e`;
- production-surface manifest `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a`.

Preparation base: commit `ad6b7f1a4427f720cfadba71f74f0d025f306add`, tree
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`.

This is a checklist, not an Owner statement. It grants no authority. The Owner must write each
decision explicitly; review PASS, a hash, branch, PR, ruleset, or silence is never approval.

## 1. Decision A — package anchoring only

After the V4 response is sealed with BLOCKER=0/HIGH=0, the Owner may decide whether to
authorize one package-closeout commit and one push to
`refs/heads/governance/execution-hardening-step3-package-v1`.

The Owner statement must bind every then-existing V4 package/map/companion/request/snapshot/
packet/receipt/response path and SHA-256 plus the exact parent commit/tree. It must not and
cannot bind the not-yet-created Owner closeout, closeout receipt, or external closeout
manifest.

The exact external path is
`docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_CLOSEOUT_MANIFEST_V1.json`. It records the
complete closeout-receipt SHA-256 outside the Clause-Packet artifact set.

The forward order is mandatory:

```text
terminal response -> Owner statement -> closeout -> closeout receipt
-> external closeout manifest -> one commit -> one push
```

Decision A forbids code, CI, implementation, PR, ruleset, merge, data, fit, Validation, Final
Test, Test 3b, and Test 4.

## 2. Decision B — Phase A only

Decision B is ineligible until Decision A produces an exact package-closeout commit/tree. The
Owner statement must:

1. bind that exact base and package SHA `fc088c63…d8e5`;
2. co-ratify the exact four companion IDs/paths/hashes above;
3. authorize branch `governance/execution-hardening-step3-v1`;
4. authorize only the 28 paths in Section 3;
5. authorize Tier 1 and exactly zero Tier 2 reservations;
6. authorize one dedicated PR to `main`, but no merge or ruleset/main mutation;
7. bind the complete Tier 1 groups and CI permissions in the package;
8. bind commit/push/review-chain budgets and forbidden surfaces.

## 3. Exact Phase A 28-path subset

1. `.github/workflows/quant-ci-v1.yml`
2. `.github/workflows/execution-hardening-attestation-v1.yml`
3. `configs/governance/executed_frozen_registry_v1.json`
4. `configs/governance/execution_hardening_attempt_ledger_schema_v1.json`
5. `src/mes_quant/governance/execution_hardening/__init__.py`
6. `src/mes_quant/governance/execution_hardening/boundary.py`
7. `src/mes_quant/governance/execution_hardening/records.py`
8. `src/mes_quant/governance/execution_hardening/attestation.py`
9. `src/mes_quant/governance/execution_hardening/registry.py`
10. `src/mes_quant/governance/execution_hardening/executed_frozen.py`
11. `src/mes_quant/governance/execution_hardening/rehearsal.py`
12. `tools/build_execution_hardening_review_report.py`
13. `tools/run_execution_hardening_rehearsal.py`
14. `tools/verify_execution_hardening_attestation.py`
15. `tests/governance/test_execution_hardening_boundary.py`
16. `tests/governance/test_execution_hardening_records.py`
17. `tests/governance/test_execution_hardening_attestation.py`
18. `tests/governance/test_execution_hardening_registry.py`
19. `tests/governance/test_execution_hardening_executed_frozen.py`
20. `tests/governance/test_execution_hardening_rehearsal.py`
21. `tests/governance/test_execution_hardening_ci_spec.py`
22. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_OWNER_AUTHORIZATION_V1.md`
23. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1.md`
24. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_DISPATCH_RECEIPT.md`
25. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_RESPONSE.md`
26. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_OWNER_CLOSEOUT.md`
27. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_CLOSEOUT_RECEIPT.md`
28. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_CLOSEOUT_MANIFEST_V1.json`

Path 22 is the sole first Phase A commit. Paths 23–28 occur only after implementation freeze,
in forward order; path 28 records path 27's complete SHA-256 before the final Phase A
evidence-chain commit.

## 4. Decision C — Phase B only

Decision C is ineligible until Phase A's exact review chain returns BLOCKER=0/HIGH=0. The
Owner statement must bind:

- exact Phase A PR head, tree, allowed merge diff, and `main` target;
- exact workflow SHA-256/Git blob, post-change Quant CI SHA-256/Git blob, trusted-root digest,
  activation tree, and `gh 2.97.0`;
- exact time policy and Section 6 verifier flags;
- exact nine paths in Section 5;
- exact external ruleset payload in Section 6;
- at most two Tier 2 reservations and seed `2026082501`;
- exact Phase B changed/staged firewalls, review-chain budget, and failure posture;
- no Issue #48 or PR #47 mutation.

## 5. Exact Phase B 9-path subset

1. `configs/governance/execution_hardening_attestation_ready_v1.json`
2. `configs/governance/sigstore_trusted_root_v1.jsonl`
3. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_OWNER_ACTIVATION_V1.md`
4. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1.md`
5. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_DISPATCH_RECEIPT.md`
6. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_RESPONSE.md`
7. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_OWNER_CLOSEOUT.md`
8. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_B_FINAL_V1_CLOSEOUT_RECEIPT.md`
9. `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_CLOSEOUT_MANIFEST_V1.json`

Path 3 is the sole first Phase B commit. Paths 4–9 occur in forward order; path 9 records path
8's complete SHA-256 before the final Phase B evidence-chain commit. Any repair outside these
nine paths requires a new Decision B lineage; V4 contains no broader repair escape.

## 6. Exact external Phase B ruleset mutation

```text
ruleset_id = MES_EXECUTION_HARDENING_REQUIRED_WORKFLOW_RULESET_V1
repository_id = 1329447686
repository = NonChaianon/mes-quant-engine-v1
target = branch
target_ref = ~DEFAULT_BRANCH
rule_type = workflows
workflow.repository_id = 1329447686
workflow.path = .github/workflows/quant-ci-v1.yml
workflow.ref = refs/heads/main
workflow.sha = RESOLVE_AT_DECISION_C_TO_EXACT_PHASE_B_ACTIVATION_MAIN_SHA
enforcement = active
bypass_actors = []
do_not_enforce_on_create = false
```

The symbolic SHA is not authorized verbatim. Decision C must replace it with and bind the exact
40-hex `main` SHA observed after the authorized merge and before activation, then authorize
the fully resolved external mutation. Phase B must read back the ruleset
and rule-suite API, verify every field/no bypass, and observe a subsequent PR where the required
workflow runs and passes. Merge alone is not proof of every-PR enforcement.

## 7. Exact trust/time/budget choices

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
rehearsal_sealing_root = MES_REHEARSAL_EPHEMERAL_SHA256_SEAL_ROOT_V1
production_runtime_root = NOT_YET_RATIFIED_PRODUCTION_TRUST_ROOT / REJECT_ALWAYS
fixture_root = MES_TEST_FIXTURE_PRODUCTION_TRUST_ROOT_V1 / IN_MEMORY_TEST_POLICY_ONLY
Tier_2_reservations <= 2
synthetic_models = 2
synthetic_folds = 2
synthetic_fold_fit_calls <= 4
bootstrap_blocks <= 3
bootstrap_repetitions_per_block = 64
synthetic_bootstrap_replicates_total <= 192
economic_diagnostic_calls <= 1
economic_policy_evaluations <= 2
all_real_and_sealed_scientific_counters = 0
seed = 2026082501
```

Signer/source comparisons use the already-closed ordered-file-hash and commit fields; V4 adds
no predicate field. The time policy binds token age `300s`, skew `60s`, attestation age `1800s`,
expiry relation, order, and exact stop codes.

## 8. Exact gates

Phase A: complete Tier 1 including the attestation PASS row and exact Cell 12 combinations;
transition Markdown equivalence including the exact extraction/reason rules; same-core
production fixture PASS/test-policy and STOP/runtime-policy; full tests/lint; firewalls; real
counters zero; dedicated PR CI; and exact six-artifact chain with BLOCKER=0/HIGH=0 whose
external manifest records the terminal closeout-receipt SHA-256.

Phase B: exact activation bindings; merge/source equality; custom-root/time PASS; Section 6
PASS before reservation; same-core fixture directions; one Tier 2 happy path; discovered
production-surface before/after hashes equal inside the exact comparison window; production
registry rejection; exact changed/staged firewalls; active no-bypass required-workflow ruleset;
subsequent PR rule-suite PASS; and exact six-artifact final chain with BLOCKER=0/HIGH=0 whose
external manifest records the terminal closeout-receipt SHA-256.

## 9. Commit/push and failure posture

Decision A: one docs/config closeout commit and one push.

Decision B: one Owner-record commit, at most seven implementation/repair commits, one final
evidence-chain commit, one ordinary push after each, and one dedicated PR; no merge.

Decision C: one Owner-activation commit, at most two activation commits, one evidence-chain
commit, exact resolved ruleset mutation, and at most two Tier 2 reservations. Any exhausted budget or
out-of-subset repair stops closed and needs a new Owner statement.

No force-push, amend, rebase, squash, tag, release, Issue #48 mutation, or PR #47 mutation.

## 10. Forbidden surfaces and next eligible decision

No historical Test 2/Test 3 mutation/execution; Test 3 retry; Test 3b; Test 4; hypothesis;
real data/artifact metadata/row/statistics/value/target/path; production fit; Validation;
Final Test; production signing credential; dependency; database; broker; live; hidden CI;
or unapproved ruleset/main mutation.

After a clean V4 review, only Decision A becomes eligible. Decision B requires the exact
package-closeout commit/tree and companion co-ratification. Decision C requires exact Phase A
evidence and a separate Owner statement. This request grants none of them.

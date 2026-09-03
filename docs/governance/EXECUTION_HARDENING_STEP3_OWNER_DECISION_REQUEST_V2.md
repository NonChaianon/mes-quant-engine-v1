# MES Execution Hardening Step 3 — Owner Decision Request V2

Request ID: `REQUEST_EXECUTION_HARDENING_STEP3_V2_20260825`

Status: **DRAFT REQUEST / REVIEW REQUIRED / NO AUTHORITY**

Prepared date: `2026-08-25` (`Asia/Bangkok`)

Preparation base commit/tree: `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Package: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V2` at
`docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V2.md`, SHA-256
`809a3281f42850c269381483e0c28f44e10cc91427334e8391e07b47afbf4974`.

Surface map: `REHEARSAL_SURFACE_MAP_V2` at
`configs/governance/rehearsal_surface_map_v2.json`, SHA-256
`c459744e4c8c27ecfb4bdd08164671146ef59d468beb7a90a46a8b47d97670da`.

Transition companion: `MES_EXECUTION_TRANSITION_EVENT_ENUM_V1` at
`configs/governance/execution_hardening_transition_events_v1.json`, SHA-256
`ec6c8e252837eb1a495f791ff12435eb8e4050cee23331f42808104098d759e2`.

Live-state snapshot: `docs/governance/EXECUTION_HARDENING_STEP3_LIVE_STATE_SNAPSHOT_20260825.json`,
SHA-256 `6df56157cb13c7ba0383bcae70194e8b4e610184ca9e72a4d9258454fa2e1cf7`.

This file requests decisions in sequence. It is not an Owner statement, authorization,
attestation, commit permission, push permission, CI permission, PR permission, merge permission,
or scientific authority. The Owner must supply their own statement; no preparer-authored prose
below may be treated as adopted by silence or partial quotation.

## 1. Decision A — package anchoring only

After the V2 `FULL_GOVERNED` review returns BLOCKER=0/HIGH=0, the first eligible Owner decision
is whether to authorize exactly one docs/config-only package-closeout commit and one ordinary
push to `refs/heads/governance/execution-hardening-step3-package-v1`.

The Owner's own statement must explicitly bind:

- exact reviewed package, map, transition-companion, request, live-snapshot, packet, receipt,
  response, and closeout paths with SHA-256 values;
- exact parent commit/tree `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
  `4f8e674dea4e70cf93e80c4d392f4ac505da377b`;
- the one exact package branch/ref;
- one commit and one push only;
- no implementation, code, CI, PR, merge, Issue #48 mutation, PR #47 mutation, data, fit,
  Validation, Final Test, Test 3b, or Test 4 authority.

Until Decision A is granted, no package commit or push is authorized.

## 2. Decision B — later Phase A implementation only

Decision B is ineligible until Decision A is executed and the Owner can name the resulting
package-closeout commit/tree exactly. A Phase A Owner statement must bind all of these fields:

1. exact package-closeout commit/tree and package SHA-256 `809a3281…f4974`;
2. exact implementation branch `governance/execution-hardening-step3-v1`;
3. exact Phase A allowlist in Section 3;
4. Tier 1 only; Tier 2 reservations exactly `0`;
5. one dedicated new PR may be opened from the implementation branch to `main`;
6. PR #47 and Issue #48 may not be mutated;
7. no merge or `main` mutation;
8. exact test groups and CI permissions in Sections 6 and 7;
9. commit/push budget in Section 8;
10. the exact forbidden surfaces in Section 9.

Phase A review or CI PASS does not imply Decision C.

## 3. Exact Phase A allowlist

Phase A may change only these 22 paths:

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

Path 22 must be the sole path in the first Phase A commit. Path 1 may add only the Issue #48
executed-frozen test. Paths
`configs/governance/execution_hardening_attestation_ready_v1.json`,
`configs/governance/sigstore_trusted_root_v1.jsonl`, and
`docs/governance/EXECUTION_HARDENING_STEP3_PHASE_B_OWNER_ACTIVATION_V1.md` are Phase B-only.

## 4. Decision C — later Phase B activation/merge/Tier 2

Decision C is ineligible until Phase A is complete and fresh-eyes review returns
BLOCKER=0/HIGH=0. The Owner must then decide separately whether to authorize the exact Phase A
PR head for merge and activate Tier 2. The Owner statement must bind:

- exact PR head, reviewed tree, merge target, and allowed activation diff;
- exact signer-workflow SHA-256 and Git blob after merge;
- exact post-change Quant CI SHA-256 and Git blob;
- exact `configs/governance/sigstore_trusted_root_v1.jsonl` SHA-256;
- exact source/activation commit and `refs/heads/main`;
- `gh 2.97.0`, `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`,
  exact custom-root verification flags, GitHub OIDC issuer, and
  `MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1`;
- at most two GitHub-hosted Tier 2 reservations under the budget in Section 5;
- exact Phase B paths only: ready sentinel, trusted-root file, and Phase B activation record;
- merge scope and failure/remediation posture explicitly;
- no Issue #48 mutation or closeout without another decision.

## 5. Exact Phase B synthetic budget

```text
Tier 2 reservations <= 2
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

A cancelled or rerun job consumes a reservation only if it passed the atomic reservation step.
Every rerun receives a new attempt identity. Exhaustion stops closed.

## 6. Exact trust and time choices for Decision C

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
trust_root_bootstrap = Sigstore public-good TUF root chain from metadata/root_history/10.root.json
trusted_time_policy = MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1
rehearsal_sealing_trust_root = MES_REHEARSAL_EPHEMERAL_SHA256_SEAL_ROOT_V1
production_sealing_trust_root = NOT_YET_RATIFIED_PRODUCTION_TRUST_ROOT / REJECT_ALWAYS
```

The Section 6 predicate/report must bind the exact closed 23-field set enumerated in package
V2 Section 7.3. Verification uses the frozen custom root and exact repo/workflow/signer/source
digests. The workflow alone receives `contents: read`, `id-token: write`, and
`attestations: write`; Quant CI remains `contents: read`.

Claude Opus is only the separate Exit Criterion 10(b) reviewer with
`UNTRUSTED_CONTEXT_ONLY`.

## 7. Exact Tier 1 controls entering CI

Existing Quant CI receives only `EXECUTED_FROZEN_BYTE_INTEGRITY_V1`. The new hardening
workflow receives only the sixteen enumerated control groups in package V2 Section 8. No
blanket “all tests” phrase expands CI authority.

The dedicated Phase A PR may prove checkout safety. Only a separately authorized Phase B merge
can make executed-frozen integrity live on every future PR and satisfy Protocol Exit
Criterion 2.

## 8. Exact commit/push/PR posture proposed

Decision A: one docs/config closeout commit plus one ordinary push to the package branch.

Decision B / Phase A: one authorization-record commit plus at most seven implementation or
repair commits; one ordinary push after each; exactly one new dedicated PR may be opened;
no merge, force-push, amend, rebase, squash, tag, release, Issue #48 mutation, or PR #47
mutation.

Decision C / Phase B: one activation-record commit plus at most two activation commits for the
trusted-root file and ready sentinel, under exact later authority. Any additional repair
commit, PR, or merge after a failed gate requires a new Owner statement.

## 9. Forbidden surfaces preserved

- no authority may be inferred across Decision A, B, or C;
- no historical Test 2/Test 3 mutation or execution;
- no Test 3 retry, Test 3b, Test 4, hypothesis, target-space, or repair-budget action;
- no real DBN/Parquet/artifact metadata, row group, statistics, value, target, or path read;
- no production fit, loss, bootstrap, economic result, Validation, or Final Test;
- no production runtime ledger or production trust/signing credential;
- no dependency, database, broker, live, release, or hidden CI permission;
- no Issue #48 or PR #47 mutation;
- no merge except the exact later Decision C scope.

## 10. Decision boundary

The next eligible decision after a clean Attempt 002 is **Decision A only**. Decision B cannot
be granted until the exact package-closeout commit/tree exists. Decision C cannot be granted
until Phase A is complete and exact workflow/trust-root/source digests exist. The Owner must
write each statement explicitly; review PASS, a hash, a branch, a PR, or silence is never an
authorization.

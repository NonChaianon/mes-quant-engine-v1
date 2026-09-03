# MES Execution Hardening Step 3 — Owner Decision Request V1

Request ID: `REQUEST_EXECUTION_HARDENING_STEP3_20260825`

Status: **DRAFT REQUEST / REVIEW REQUIRED / NO AUTHORITY**

Prepared date: `2026-08-25` (`Asia/Bangkok`)

Preparation base commit/tree: `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Package: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V1` at
`docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V1.md`, SHA-256
`1c880624bdcbce3b65bc633b4f9fc9f735d34935278fd454fd4ba028e86008ca`

Surface map: `REHEARSAL_SURFACE_MAP_V1` at
`configs/governance/rehearsal_surface_map_v1.json`, SHA-256
`a4ea3e7110bdcc60d4893ac440fbb2d375e158956e425b795917791a96077370`

This request asks for a later Owner decision. It is not itself an authorization, review
attestation, target-space action, CI permission, push permission, or implementation permit.

## 1. Decision requested

After the `FULL_GOVERNED` review chain is complete and anchored in an exact
package-closeout commit/tree, the Owner will be asked to decide whether to authorize Codex to
implement `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V1` from that exact base.

The decision has these inseparable components:

1. authorize the exact 22-path allowlist in Section 2;
2. authorize synthetic-only Tier 1 and Tier 2 behavior under the exact budget in Section 3;
3. subsume Issue #48 implementation and CI activation without authorizing issue mutation;
4. authorize the deterministic GitHub Actions/Sigstore trust mechanism in Section 4;
5. select Exit Criterion 10(b) for the separate Claude fresh-eyes judgment;
6. authorize the bounded commit/push posture in Section 5;
7. preserve every forbidden surface in Section 6.

The Owner may accept or reject the package. Partial acceptance requires changed package
bytes, a new governed packet, and a new review lineage; no preparer may silently narrow or
expand an Owner statement.

## 2. Exact proposed implementation allowlist

The later authorization must bind these exact paths and no others:

1. `.github/workflows/quant-ci-v1.yml`
2. `.github/workflows/execution-hardening-attestation-v1.yml`
3. `configs/governance/executed_frozen_registry_v1.json`
4. `configs/governance/execution_hardening_attestation_ready_v1.json`
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
22. `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_AUTHORIZATION_V1.md`

Path 1 may be modified only to add the Issue #48 executed-frozen integrity test. Paths 2–22
are additive. Path 22 must be the sole path in the first commit after the exact base.

## 3. Exact synthetic budget proposed

The later authorization will permit no more than four isolated Tier 2 reservation
consumptions. Each reservation has these hard ceilings:

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
```

Every Tier 2 attempt consumes one isolated rehearsal reservation before fit. Tier 1 unit
fixtures may not consume a Tier 2 reservation or emit sealed evidence.

## 4. Exact trust and reviewer choices proposed

### 4.1 Section 6 deterministic reviewer

```text
reviewer_role = EXECUTION_HARDENING_DETERMINISTIC_REVIEWER_V1
provider = GitHub Actions OIDC / Sigstore
model = NONE_DETERMINISTIC_RULE_ENGINE
signer_workflow = NonChaianon/mes-quant-engine-v1/.github/workflows/execution-hardening-attestation-v1.yml
source_ref = refs/heads/governance/execution-hardening-step3-v1
oidc_issuer = https://token.actions.githubusercontent.com
action = actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6
predicate_type = https://slsa.dev/provenance/v1
trusted_time_source = Sigstore verifiedTimestamps
verification = gh attestation verify with exact repo/workflow/ref/digest policy and self-hosted runners denied
```

The workflow and deterministic report are the reviewer. No LLM claim is elevated into this
trust mechanism.

### 4.2 Fresh-eyes judgment

Exit Criterion 10 uses form **10(b)**: Claude Code Opus reviews the exact implementation
package through a new `FULL_GOVERNED` Clause Packet. Its response is recorded as
`UNTRUSTED_CONTEXT_ONLY`. It may satisfy only the engineering-completeness judgment and can
never satisfy Section 6 or permit execution-authorization reservation consumption.

## 5. Exact commit and push posture proposed

- exact implementation branch: `governance/execution-hardening-step3-v1`;
- exact base: the future package-closeout commit named verbatim by the Owner;
- commit 1: Owner authorization record only;
- at most five later bounded implementation commits;
- at most one ordinary push after each commit to the exact implementation branch;
- no force-push, amend, rebase, squash, merge commit, tag, release, or `main` mutation;
- local and remote SHA equality required after every push.

The attestation workflow remains inert until the additive ready sentinel exists. Its presence
activates the full hardening suite and attestation on the exact branch; every later push must
rerun it.

## 6. Forbidden surfaces preserved

- no modification, repair, rerun, or execution of historical Test 3 code;
- no Test 3b, Test 4, hypothesis, target-space, or repair-budget action;
- no real DBN/Parquet/artifact metadata, row group, statistics, value, target, or path read;
- no production fit, loss, bootstrap, economic result, Validation, or Final Test;
- no production governance ledger, trust-root, signing key, credential, database, broker, or
  live handle;
- no dependency or `pyproject.toml` change;
- no PR #47 mutation or merge;
- no Issue #48 edit, comment, label, assignment, or closeout without later Owner authority;
- no CI change outside the two exact workflow paths and tests enumerated by the package.

## 7. Proposed later Owner statement skeleton

This skeleton is intentionally incomplete until the governed review/closeout bytes are
committed. No one may fill the placeholders from memory.

```text
ผมอนุมัติ `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V1` ที่ exact package-closeout commit
`<40-HEX>`, tree `<40-HEX>`, package SHA-256 `<64-HEX>` และ
`REHEARSAL_SURFACE_MAP_V1` SHA-256
`a4ea3e7110bdcc60d4893ac440fbb2d375e158956e425b795917791a96077370`
โดยให้ Codex เป็น implementer บน branch `governance/execution-hardening-step3-v1`
ภายใต้ exact 22-path allowlist, synthetic budget, Issue #48/CI choice,
GitHub Actions/Sigstore trust mechanism, reviewer roles, tests, commit/push posture และ
forbidden surfaces ใน package ฉบับที่ hash-bound ข้างต้น

อนุมัติให้ commit แรกบันทึกข้อความนี้แบบ verbatim ที่
`docs/governance/EXECUTION_HARDENING_STEP3_OWNER_AUTHORIZATION_V1.md` เพียงไฟล์เดียว
ก่อนเริ่ม code การอนุมัตินี้ไม่เปิด Test 3b, Test 4, real data, target/path access,
production fit, Validation, Final Test, Issue #48 mutation, PR #47 mutation หรือ merge
```

## 8. Decision boundary

This request remains `NO AUTHORITY` until the packet review is complete, all artifacts are
anchored, placeholders are replaced with machine-derived exact values, and the Owner adopts
the resulting statement verbatim. Silence, review PASS, a package hash, or a Git commit is not
Owner authorization.

# FULL_GOVERNED Clause Packet — Execution Hardening Phase A Final Review V1

Packet ID: `CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1`

Operating mode: `FULL_GOVERNED`

Status: **FROZEN AT DISPATCH / CONTEXT ONLY / NO AUTHORITY**

Prepared UTC: `2026-08-27T16:34:37Z`

Prepared by: `OpenAI Codex / packet preparer and non-Owner auditor`

Repository: `NonChaianon/mes-quant-engine-v1`

Branch/ref observed: `refs/heads/governance/execution-hardening-step3-v1`

Reviewed commit: `d647320f5ce4e4081b9f87996cb0f32939905324`

Reviewed tree: `22eda03675b47a585dac9e84c06cc493af8abc58`

Diff base: `f2bf04ba2976bce6118472ffcb2e5492336e2aaa`

Working-tree state before packet creation: `CLEAN`; packet creation adds only this create-once
path 23. Index diff was zero.

Question boundary: determine only whether the exact Phase A implementation at the reviewed
commit is engineering-complete under the exact Owner authorization, including all twenty Tier 1
groups, CI, protected-surface, review-boundary, and prohibition gates.

Authority statement: `CONTEXT ONLY / NO AUTHORITY`

Expected reviewer: `Claude Code CLI 2.1.239 / opus / independent fresh-eyes governance reviewer`

Expected review role: `INDEPENDENT_ADVERSARIAL_PHASE_A_ENGINEERING_REVIEWER`

Attempt ID: `ATTEMPT_EXECUTION_HARDENING_PHASE_A_FINAL_OPUS_20260827_001`

Attempt-ledger entry ID: `ATTEMPT_LEDGER_EXECUTION_HARDENING_PHASE_A_FINAL_20260827_001`

Attempt ordinal: `1`; authorized attempts: `1`; unchanged-byte retry: `FORBIDDEN`; fallback:
`NOT_AUTHORIZED`.

Prior/superseded final-review packet: `NONE`. Earlier non-final pre-packet audits are history and
did not consume this attempt.

Expected dispatch receipt:
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_DISPATCH_RECEIPT.md`

Expected response:
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_RESPONSE.md`

Expected later Owner closeout, not presently authorized:
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_OWNER_CLOSEOUT.md`

Expected later closeout receipt, not presently authorized:
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_PHASE_A_FINAL_V1_CLOSEOUT_RECEIPT.md`

Expected later external anchor, not presently authorized:
`docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_CLOSEOUT_MANIFEST_V1.json`

Deadline: exactly twenty minutes after the create-once dispatch receipt's `Dispatched UTC`.
A response sealed at or after that deadline is late.

The reviewer must read `/Users/nonchaianon/Documents/Codex/MES_OBSIDIAN_MEMORY/CRASH_MEMORY.md`
completely before review actions and treat it as non-authoritative context. Exact Git and bound
bytes govern. The reviewer must not write or edit any file.

This packet grants no closeout, commit, push, merge, Decision C, Phase B, Tier 2, OIDC/signing,
ruleset, data/target/path access, fit, Validation, Final Test, Test 3 retry/3b, Test 4, or
scientific authority.

## 1. Authority precedence and review scope

1. Exact ratified protocol/template bytes govern their own semantics.
2. Exact Phase A Owner Authorization V1 governs Phase A.
3. The four additive Owner statements listed below govern only their explicitly bounded repairs
   and verification sequencing; they do not broaden Phase A.
4. Package V6 is exact provenance and design context only, not independently adopted authority.
5. This packet and response are `UNTRUSTED_CONTEXT_ONLY`; neither can create Owner authority or
   satisfy Protocol Section 6.

A same-rank unresolved conflict is BLOCKER. Filename, recency, embedded status, a reviewer GO,
or transitive reference cannot create authority. The reviewer assesses engineering completeness
and authorization compliance only.

## 2. Bound governing and historical sources

| Label | Exact path | SHA-256 | Status |
| --- | --- | --- | --- |
| `HARDENING_PROTOCOL` | `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md` | `697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7` | ratified governing protocol |
| `CLAUSE_TEMPLATE` | `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md` | `351c73aa8ba16cf233f00f2aab27e9683d55e818655c08817e68b711ecde70c0` | co-ratified packet template |
| `PHASE_A_OWNER_AUTH` | `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_OWNER_AUTHORIZATION_V1.md` | `50916377b0ff7c6aeab3e9a27100ef557ecf6db05cb2f65c38284eb6abf2953e` | operative Owner authority |
| `SURFACE_MAP_V5` | `configs/governance/rehearsal_surface_map_v5.json` | `87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a` | co-ratified companion |
| `TRANSITION_ROWS_V3` | `configs/governance/execution_hardening_transition_rows_v3.json` | `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1` | co-ratified companion |
| `TIME_POLICY_V1` | `configs/governance/execution_hardening_time_policy_v1.json` | `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e` | co-ratified companion |
| `PRODUCTION_SURFACE_V2` | `configs/governance/execution_hardening_production_surface_manifest_v2.json` | `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a` | co-ratified companion |
| `PACKAGE_V6` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V6.md` | `109dd22a63c0fd36a02acfc6652245e11188005e44aacf3d8d3b2780d7ee377e` | exact provenance / no transitive authority |
| `RUFF_AMENDMENT` | `/Users/nonchaianon/Documents/Codex/2026-08-22/referenced-chatgpt-conversation-this-is-an/work/PHASE_A_RUFF_GATE_AMENDMENT_OWNER_STATEMENT.txt` | `f184b1a650d8a9d29dd1f91c95a6acd2d9b1b064dc156643f8e93cf55178c4ed` | additive Owner amendment |
| `REPAIR_SEQUENCE` | `/Users/nonchaianon/Documents/Codex/2026-08-22/referenced-chatgpt-conversation-this-is-an/work/PHASE_A_REPAIR_SEQUENCING_CLARIFICATION_OWNER_STATEMENT.txt` | `5b86c1a02b2cc84716b7471bb0300d7cd13a5b0158c7425f550a351c7caf9398` | additive Owner clarification |
| `PYCACHE_CLEANUP` | `/Users/nonchaianon/Documents/Codex/2026-08-22/referenced-chatgpt-conversation-this-is-an/work/PHASE_A_PYCACHE_CLEANUP_RERUN_OWNER_STATEMENT.txt` | `98919aafc0ddb0017ae2d8844929453646fd59921041d506675584faeed9c07e` | narrow cleanup/rerun authority |
| `GROUP19_REPAIR` | `/Users/nonchaianon/Documents/Codex/2026-08-22/referenced-chatgpt-conversation-this-is-an/work/PHASE_A_GROUP19_TEST_ONLY_REPAIR_OWNER_STATEMENT.txt` | `316ad3d0de6006e32e0d5ecc636c39eaa287e5b7b6d5b2117fe303990ee478ab` | narrow test-only repair authority |

The reviewer must recompute every listed hash. An external statement path is review context and
does not become repository authority merely because it is listed here.

## 3. Exact reviewed implementation bytes — paths 1–22

| # | Exact repository path | SHA-256 |
| ---: | --- | --- |
| 1 | `.github/workflows/quant-ci-v1.yml` | `a74ce4f6f343c947f2ec24b6d95defed713d9f0680b43dd83dc86f25835df8a6` |
| 2 | `.github/workflows/execution-hardening-attestation-v1.yml` | `6588878c25e31904d9dbbdae0ebd7ec0c15aa00622e653f2186d9f599869bdb9` |
| 3 | `configs/governance/executed_frozen_registry_v1.json` | `52900e7811c32895d4b7a1c1784c49610629eb2cecdb1ac777b3eca3620f69b3` |
| 4 | `configs/governance/execution_hardening_attempt_ledger_schema_v1.json` | `94e2f4ab48207851793cad1d57fa73203b79603119ab0757f9b7102f9ee19387` |
| 5 | `src/mes_quant/governance/execution_hardening/__init__.py` | `369d7a749f256ca3b216509c90c5744a92132a1507df5659531fd533509f8605` |
| 6 | `src/mes_quant/governance/execution_hardening/boundary.py` | `54972004be1acf839fc604f37e15aee74f65054c47816f72f3633cba4198ed0d` |
| 7 | `src/mes_quant/governance/execution_hardening/records.py` | `8db541c327f52eaba6be06897b6e3ef1853121c28769f2cfbc39d784bbe2ed19` |
| 8 | `src/mes_quant/governance/execution_hardening/attestation.py` | `2abf91bff99569bdbefacc9e1ba883579585a4125eafd5956c7f791eec5eb214` |
| 9 | `src/mes_quant/governance/execution_hardening/registry.py` | `e83c0320f95db790767f30b097cb81ca7e862f8f6f6e12cedfdb1354cae565ed` |
| 10 | `src/mes_quant/governance/execution_hardening/executed_frozen.py` | `bf7022128a0cb2a849f91db8f31cdf959ebf09bb410bac959c0918f6adca04a7` |
| 11 | `src/mes_quant/governance/execution_hardening/rehearsal.py` | `f87b6f27d09f0bf7153412edc9e796441cb62d67885f1ec0dad5c38a0ad38dc9` |
| 12 | `tools/build_execution_hardening_review_report.py` | `3a984fd7931433c6110ac315c459645635d69d38f193a9fb00f2917a0c71cba4` |
| 13 | `tools/run_execution_hardening_rehearsal.py` | `cfa576ab689695aead0e51b79c622c0fc0a6477786851cb84c0bc837c86eeb01` |
| 14 | `tools/verify_execution_hardening_attestation.py` | `59db00c961411304548e9f83ba93a571908d32822ca24a97ff15fb2151887cb7` |
| 15 | `tests/governance/test_execution_hardening_boundary.py` | `0cfaa4d0cd1fd12718c5e1909c6d7e6fd5fd7a0ad7c2928ab760e8c248fb75d8` |
| 16 | `tests/governance/test_execution_hardening_records.py` | `ace284dfe38d93bf972e77abee1e287f7b133569d6da03ece46818b218272956` |
| 17 | `tests/governance/test_execution_hardening_attestation.py` | `93c30cd90e92d774e135fae327bf19bb692eaa9190027321ae093123f11aeb79` |
| 18 | `tests/governance/test_execution_hardening_registry.py` | `46082a07ab78155bdd6afa4ce79126fcc41ab4599e1482db018dfd7b46c52fa2` |
| 19 | `tests/governance/test_execution_hardening_executed_frozen.py` | `33aba7d7258aa580a1df46f03fab498b31a6a786bb5b294d61f468dddf1a3e32` |
| 20 | `tests/governance/test_execution_hardening_rehearsal.py` | `ac3437bc8bb8bbded2f996d39b49104bbeacfb5a89ae1774bbcd5d619797121e` |
| 21 | `tests/governance/test_execution_hardening_ci_spec.py` | `d9f177ae61ff9d3912dd76a0ed6ff5758908d8f1a21accd90b174589d9fde931` |
| 22 | `docs/governance/EXECUTION_HARDENING_STEP3_PHASE_A_OWNER_AUTHORIZATION_V1.md` | `50916377b0ff7c6aeab3e9a27100ef557ecf6db05cb2f65c38284eb6abf2953e` |

Any mismatch, duplicate, missing path, extra committed Phase A path, rename, copy, or deletion is
BLOCKER.

## 4. Verbatim governing clauses

### Clause A — create-once Phase A final-review chain

- Source: `PHASE_A_OWNER_AUTH`, lines 67–73 at the reviewed commit.
- Precedence: governs path order, retry, fallback, and closeout eligibility.

```text
Path 22 ต้องเป็นไฟล์เดียวใน commit แรกของ Phase A Paths 23–28 เป็น create-once final review/closeout chain และต้องเกิดตามลำดับเท่านั้นหลัง implementation bytes freeze โดย path 28 ต้อง bind complete SHA-256 ของ path 27

คำอนุมัตินี้อนุญาตให้สร้าง paths 23–25 เพื่อ dispatch และรับ fresh review หลัง implementation freeze แต่ยังไม่อนุญาตให้สร้าง paths 26–28 จนกว่า Owner จะให้ separate closeout statement หลังเห็น exact Response ที่ timely, exact-package, exact `FULL_GOVERNED`, packet/tool-conforming, free of verification-side invalidation และ `BLOCKER=0 / HIGH=0`

Exact chain คือ path 23 Packet → path 24 dispatch receipt bind complete path-23 SHA-256 → path 25 response bind complete path-23/path-24 SHA-256 → separate Owner closeout statement → path 26 Owner closeout bind exact Owner statement และ complete path-25 SHA-256 → path 27 closeout receipt bind complete path-26 SHA-256 → path 28 external manifest bind complete path-27 SHA-256 การตอบช้า, invalid response หรือ `BLOCKER>0 / HIGH>0` ให้ STOP โดยไม่มี retry ต่อ unchanged bytes และไม่มี fallback reviewer

การเปลี่ยน path นอก allowlist, dependency, packaging metadata หรือไฟล์ historical Test 2/Test 3 ให้ STOP และต้องขอ Owner authorization ใหม่
```

### Clause B — final reviewer identity and trust boundary

- Source: `PHASE_A_OWNER_AUTH`, lines 150–152.
- Precedence: governs this attempt's identity, independence, deadline, and evidentiary limit.

```text
แต่ใน Phase A กลไกและ time source ข้างต้นมีสถานะ `IMPLEMENTATION_UNDER_TEST / NOT_ACTIVE / NOT_TRUSTED_FOR_AUTHORITY` เท่านั้น OIDC minting, `actions/attest` invocation, attestation issuance/acceptance, custom trusted-root activation, Section 6 trusted-attestation activation, production signing credential และ execution-authority reservation consumption เท่ากับศูนย์

Phase A final engineering review ใช้ exactly one create-once `FULL_GOVERNED` Clause-Packet attempt โดย `Claude Code CLI 2.1.239 / opus / independent fresh-eyes governance reviewer` ในบทบาท `INDEPENDENT_ADVERSARIAL_PHASE_A_ENGINEERING_REVIEWER` Reviewer นี้ต้องทำงานใน fresh session แยกต่างหากและต้องไม่เคย author, modify หรือช่วยตัดสิน implementation bytes ของ Phase A ก่อนรับ Packet มี deadline 20 นาทีหลัง dispatch, ไม่มี retry ต่อ unchanged bytes และไม่มี fallback reviewer Response ต้อง timely, exact-package, packet/tool-conforming, free of verification-side invalidation และ classify เป็น `UNTRUSTED_CONTEXT_ONLY` ตาม Exit Criterion 10(b) Form นี้ตัดสิน engineering completeness ได้เท่านั้น ไม่ satisfy Section 6 และไม่สร้าง Owner authority หรือ execution authority
```

### Clause C — twenty required Tier 1 groups and acceptance

- Source: `PHASE_A_OWNER_AUTH`, lines 154–191.
- Precedence: defines engineering-completeness coverage.

```text
ต้อง implement และ verify Tier 1 ครบ 20 groups:

1. identity pipe preservation และ CR/LF rejection
2. finite scalar และ integral `{0,1}` flag behavior
3. ordered Arrow schema/type/nullability และ non-empty consumer rehearsal
4. ทุก Cell 12 null/non-null combination รวม `LABEL_UNUSABLE`, nullable `path_instrument_changed`, path-count/path-metric fields
5. predictor positive/zero/negative/nonfinite outcomes
6. request, target, common mask, fold, harmonic, rank และ support outcomes
7. zero-variance target stop before common mask/fit
8. allowed transition triples 18/22 และ complement tuples 52/118 ทั้งหมด
9. ทุก Section 6.1 outcome พร้อม remaining/exhausted attempt states ที่เกี่ยวข้อง
10. valid exact-package PASS ที่ BLOCKER/HIGH=0 แต่ไม่มี Owner authority ต้องคง `REVIEW_PENDING`
11. unauthorized reservation และ monotone boolean behavior
12. positive own-class fixtures และ opposite-class rejection ของทั้งสอง registries
13. same production core predicate PASS ด้วย in-memory test policy และ STOP ด้วย runtime reject-always policy
14. single และ combined rehearsal-marker mutations
15. missing production binding และ invalid `NO_SOURCE_ARTIFACT_ACCESSED` use
16. surface-map/transition/time-policy/production-manifest absence หรือ hash mismatch
17. transition companion versus ratified protocol Markdown exact equivalence
18. clean Tier 1 happy path, protected counters, no output on stop, handle-injection stop
19. protected production-surface before/after actual-file hashes
20. Phase A/Phase B exact changed-file และ staged-file firewalls

ทุก command ต้อง return code 0 Test counts ให้ machine-derive และบันทึกจาก exact implementation commit; ไม่ pin จำนวนล่วงหน้าและห้ามลด scope ด้วย manual test enumeration Full-suite pytest ต้องใช้ normal repository discovery

นอกจากนี้ต้องผ่าน transition-companion/protocol exact equivalence, historical/companion SHA integrity, changed/staged allowlist firewall, exact zero-counter assertions, dedicated-PR Quant CI และ non-authoritative hardening CI Any failure stops closed
```

### Clause D — response, deadline, and forward-only hashes

- Source: `CLAUSE_TEMPLATE`, lines 185–219 and 272–286.
- Precedence: governs response sealing and hash-chain validity.

```text
Every review attempt produces exactly one terminal create-once artifact:

- a response artifact when a verdict completes before the bounded deadline; or
- an attempt-outcome artifact whenever the attempt terminates without a completed verdict,
  including timeout, `NO_VERDICT`, cancellation, supersession, reviewer/package change, or
  verification-side invalidation.

A reviewer response arriving at or after the bounded deadline, or after an attempt-outcome
has been sealed, is not part of that closed attempt and must not create a second terminal
artifact for it. It may be retained only as `LATE_RESPONSE_UNTRUSTED_CONTEXT`; obtaining a
governed verdict requires a new packet and attempt ID.

Reviewer identity fields are claims unless authenticated by the governing trust mechanism.
The packet preparer may not infer or upgrade them.

No packet, response, closeout, or receipt may contain the SHA-256 of its own complete bytes.

In `FULL_GOVERNED`, the hash chain must be unbroken and forward-only: the dispatch receipt
records the packet SHA-256; the response/attempt outcome records both the packet and
dispatch-receipt SHA-256; the closeout records the response/attempt-outcome SHA-256; and the
closeout receipt records the closeout SHA-256. The terminal closeout-receipt SHA-256 must be
anchored in an external evidence manifest outside this artifact set.
```

## 5. Machine facts and counters

| Fact | Exact value | Evidence | Class |
| --- | --- | --- | --- |
| `F-01` | local HEAD = origin Phase A ref = PR #49 head = `d647320f5ce4e4081b9f87996cb0f32939905324` | Git/GitHub readback at `2026-08-27T16:27:27Z` | `F_MACHINE` |
| `F-02` | reviewed tree `22eda03675b47a585dac9e84c06cc493af8abc58` | `git rev-parse HEAD^{tree}` | `F_MACHINE` |
| `F-03` | exactly 22 committed changed paths from base; staged paths 0; deletions/renames/copies 0 | Phase A firewall plus Git diff | `F_MACHINE` |
| `F-04` | exactly 7 commits after base; maximum allowed 7 | Git ancestry count | `F_MACHINE` |
| `F-05` | exact seven Phase A modules: 163 tests pass; changed-source Ruff pass | fresh local audit and CI | `F_MACHINE` |
| `F-06` | full repository suite: 908 tests pass / return code 0 | fresh local normal discovery at exact HEAD | `F_MACHINE` |
| `F-07` | replacement Ruff baseline: 339 rows, 53 unique paths, canonical SHA-256 `1fe283d564881623b007894739446b5f43ab7d26e85b7304345265717e37c268`; no changed-path intersection; targeted 17-path Ruff return code 0 | bounded Owner amendment and post-commit gate evidence | `F_MACHINE` |
| `F-08` | four companions exact and identity-valid | recomputed SHA-256 table in Section 2 | `F_MACHINE` |
| `F-09` | protected surface 127 paths; before/after canonical SHA-256 `7063f30ddb75f6ee9ba28d8d771c28a2c765e90a6421d10a543d883da0c3f8d9` | actual-file snapshot gate before and after fresh tests | `F_MACHINE` |
| `F-10` | all exact Phase A zero counters remain 0; production evidence/authority/scientific inference false | direct Tier 1 assertions and fresh audit | `F_MACHINE` |
| `F-11` | fresh Quant CI run `33093224493` completed `success`, job `98591313812`, exact head | GitHub Actions readback | `F_MACHINE` |
| `F-12` | fresh Execution Hardening run `33093224050` completed `success`; Tier 1 job `98591311941` success; readiness/signer jobs skipped | GitHub Actions readback | `F_MACHINE` |
| `F-13` | stale incident run `32984699801` remains queued/jobs=0, but fresh PR-event run `33093224493` independently completed successfully at the same exact SHA | GitHub Actions readback | `F_MACHINE` |
| `F-14` | prior pre-packet gap was one missing direct duplicate-path snapshot test; commit `d647320f5ce4e4081b9f87996cb0f32939905324` changed only path 19 and added that proof | Git commit/diff and `GROUP19_REPAIR` | `F_MACHINE` |
| `F-15` | paths 23–25 were absent before this packet; the sole final attempt was unused | filesystem/Git check | `F_MACHINE` |
| `F-16` | Claude Code runtime reports `2.1.239 (Claude Code)` | local runtime readback | `F_MACHINE` |

The `RuntimeWarning` rows emitted by pre-existing LR001 synthetic regression tests are disclosed
baseline warnings, not Phase A hardening runtime activity or test failures.

## 6. Twenty-group closure map requiring reviewer verification

The reviewer must independently map every group to implementation and direct tests. At minimum,
verify these previously disputed groups in detail:

- Group 4: all eight nullable Cell 12 combinations plus `LABEL_UNUSABLE` are direct tests.
- Group 16: each of four companions is tested both missing and one-byte mismatched.
- Group 19: actual-file stable snapshot, duplicate paths, byte delta, missing/added tracked path,
  untracked extra, and symlink each fail or pass with exact reason behavior.
- Group 20: Phase A and Phase B partitions accept only their own paths; staged, reciprocal-phase,
  outside-union, wrong-HEAD, deletion, rename, and copy cases fail closed.
- Separate Decision C: workflow input, fixed repository path, SHA-256, sentinel binding, checkout
  commit/tree, main ref, readiness output, and signer dependency must all be mechanical. Missing,
  symlink/unsafe, hash mismatch, sentinel mismatch, and checkout mismatch are direct tests.

A test with a similar name or covering a different object class does not satisfy a group. Every
group requires behaviorally direct proof.

## 7. Known history and conflicts

- An initial non-final audit found Groups 4, 16, 19, 20 and Decision C incomplete. Bounded repairs
  at later exact commits addressed them.
- A later non-final audit found only Group 19 duplicate-path snapshot proof missing. The narrow
  Owner repair changed exactly one test path at `d647320...`.
- GitHub incident run `32984699801` became state-corrupted. One authorized cancel/rerun did not
  create jobs. One authorized PR close/reopen cycle generated fresh runs, both successful. The
  stale run is preserved and must not be presented as a pass.
- The original global Ruff command remains a historical failure with 339 diagnostics. The bounded
  additive Owner amendment replaces only that acceptance predicate with exact base-versus-HEAD
  canonical equality and targeted Ruff. It must never be described as global Ruff PASS.
- No path 26–28 or separate Owner closeout is authorized now.
- Missing evidence: `NONE` known to the preparer. The reviewer must report any discovered gap.

## 8. Closed reviewer tool and command grammar

Available built-in tools are exactly `Read`, `Grep`, `Glob`, and `Bash`. Permission mode is
`dontAsk`; safe mode, strict empty MCP configuration, and no session persistence are required.
No write/edit/notebook/browser/agent tool is available.

Bash is limited to these command forms only:

- `shasum -a 256 <one-or-more literal bound paths>`;
- `git status --short --branch`;
- `git status --porcelain=v1`;
- `git rev-parse HEAD`;
- `git rev-parse HEAD^{tree}`;
- `git rev-parse --abbrev-ref HEAD`;
- `git log --oneline -n 8`;
- `git diff --name-status f2bf04ba2976bce6118472ffcb2e5492336e2aaa d647320f5ce4e4081b9f87996cb0f32939905324`;
- `git diff --cached --name-status`;
- `gh api repos/NonChaianon/mes-quant-engine-v1/actions/runs/33093224493`;
- `gh api repos/NonChaianon/mes-quant-engine-v1/actions/runs/33093224493/jobs`;
- `gh api repos/NonChaianon/mes-quant-engine-v1/actions/runs/33093224050`;
- `gh api repos/NonChaianon/mes-quant-engine-v1/actions/runs/33093224050/jobs`;
- `test -e <one exact path 23, 24, or 25>`;
- `date -u +%Y-%m-%dT%H:%M:%SZ`.

No pipeline, redirection, separator, command substitution, environment read, wildcard path, or
command not listed above is permitted. Python, tests, `cat`, `sed`, `find`, `ls`, `rg` through
Bash, network beyond the four exact `gh api` reads, mutation, and permission bypass are forbidden.

Requesting an out-of-grammar Bash command is verification-side invalidation even if runtime denies
it. Codex must audit the stream output. Any nonconforming request or execution sets
`REVIEW_TOOL_ALLOWLIST_NONCONFORMANCE=1` and terminates the attempt as `INVALIDATED`.

## 9. Exact reviewer questions

1. Do the reviewed commit/tree/ref, all Section 2 and Section 3 hashes, Git diff, and path counts
   match exactly?
2. Did Phase A remain within the exact 22-path implementation set, seven-commit budget, synthetic
   Tier 1 mode, zero counters, and all explicit prohibitions?
3. Does each of the twenty groups have direct implementation plus behaviorally direct tests, with
   special scrutiny of Groups 4, 16, 19, and 20?
4. Is the trusted-attestation production predicate shared by test and runtime policy while Phase A
   remains non-authoritative and unable to reserve/issue/accept production evidence?
5. Is Phase B signer execution mechanically unreachable without workflow dispatch on main, ready
   sentinel, trusted-root binding, activation commit/tree, and separately fixed Decision C bytes?
6. Are companion integrity, transition/protocol equivalence, actual protected-file hashing,
   changed/staged firewalls, and executed-frozen CI coverage fail-closed?
7. Does the Ruff amendment preserve the original global failure as history while proving no new
   diagnostic or changed-path finding?
8. Do the two fresh exact-head CI successes satisfy the dedicated-PR CI requirement despite the
   separately preserved stale incident run?
9. Is this packet/receipt/reviewer attempt exact, timely, tool-conforming, one-of-one, and free of
   verification-side invalidation?
10. If and only if `BLOCKER=0 / HIGH=0`, is the only next eligible action separate Owner
    consideration of paths 26–28 closeout—not Decision C, merge, Phase B, Tier 2, or science?

The reviewer is asked to assess evidence sufficiency and engineering completeness. Policy advice
must be labeled `E_JUDGMENT`; textual claims must cite exact bound bytes.

## 10. Required terminal response

Return exactly these nine top-level sections:

1. `CLAUSE_BASE_USED`
2. `TEXTUAL_FINDINGS`
3. `MACHINE_FACTS`
4. `DERIVATIONS`
5. `JUDGMENTS`
6. `TWENTY_GROUP_CLOSURE_MATRIX`
7. `CONTRADICTIONS_OR_GAPS`
8. `VERDICT` — exact `GO` or `NO_GO` plus explicit BLOCKER/HIGH/LOW counts
9. `NEXT_ELIGIBLE_ACTION` — `SEPARATE_OWNER_PHASE_A_CLOSEOUT_CONSIDERATION_ONLY` or `NONE`

The response must bind:

- packet ID/path/SHA-256;
- dispatch receipt ID/path/SHA-256;
- attempt and attempt-ledger IDs;
- dispatch UTC, deadline UTC, and completion UTC;
- reviewed commit/tree and the ordered Section 3 file hashes;
- reviewer-claimed identity/provider/model/runtime/role;
- outcome class `VERDICT`, `TIMEOUT`, `NO_VERDICT`, `CANCELLED`, or `INVALIDATED`;
- all requested tools and Bash commands;
- `REVIEW_TOOL_ALLOWLIST_NONCONFORMANCE` exactly `0` or `1`;
- trust exactly `UNTRUSTED_CONTEXT_ONLY`.

If bound text is insufficient, return `INSUFFICIENT_BOUND_TEXT`; do not fill from memory. Do not
include a SHA-256 of the response's own complete bytes.

## 11. Severity and terminal rule

- `BLOCKER`: authority/identity/commit/tree/hash/path/packet/receipt/deadline/tool-chain conflict,
  missing closed-world evidence, or unresolved same-rank precedence.
- `HIGH`: missing or indirect required group proof, unauthorized surface, non-zero protected
  counter, reachable Phase B/production authority in Phase A, CI not exact-head success, or an
  implementation defect that can defeat a required gate.
- `LOW`: bounded editorial or maintainability matter that cannot affect machine interpretation,
  authority, coverage, or security.

`GO` requires `BLOCKER=0`, `HIGH=0`, timely completion, and
`REVIEW_TOOL_ALLOWLIST_NONCONFORMANCE=0`.

After response sealing, stop regardless of result. This attempt is one of one; no retry or fallback
is authorized. No response can grant Owner, execution, merge, Phase B, Tier 2, or scientific
authority.

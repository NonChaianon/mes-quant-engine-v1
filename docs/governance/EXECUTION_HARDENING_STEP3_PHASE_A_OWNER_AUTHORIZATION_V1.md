# Owner Authorization Draft — Execution Hardening Step 3 Decision B / Phase A

ผมอนุมัติ `Decision B — Execution Hardening Step 3 Phase A implementation only` จาก exact anchored base ต่อไปนี้:

- source ref `refs/heads/governance/execution-hardening-step3-package-v9`
- base commit `f2bf04ba2976bce6118472ffcb2e5492336e2aaa`
- base tree `8e0d6e27c33ffa3a03cb07e25a7238d0d040caad`
- V9 closeout manifest `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V9_CLOSEOUT_MANIFEST_V1.json` SHA-256 `1f505f8265f7e3e7ef3255c1ae771e2cf1ddb18b01a356c7dc3054a447c354b0`
- implementation ref `refs/heads/governance/execution-hardening-step3-v1`

implementation ref ต้องสร้างจาก exact base ข้างต้นเท่านั้น และ commit แรกต้องมี sole parent เป็น `f2bf04ba2976bce6118472ffcb2e5492336e2aaa` ห้าม infer authority จาก branch, filename, prior review GO หรือ package รุ่นก่อน

## 1. Governing bytes and precedence

ผม bind governing protocol และระบุ implementation-package bytes ต่อไปนี้เป็น exact provenance เท่านั้น:

- `MES_EXECUTION_HARDENING_PROTOCOL_V1` — `docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md` — SHA-256 `697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7`
- `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V4` — `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V4.md` — SHA-256 `fc088c631a1db0370eb2920d7749eac502d17aac613caac2e9e57e95555dd8e5`
- `REQUEST_EXECUTION_HARDENING_STEP3_V4_20260826` — `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V4.md` — SHA-256 `6425a2c762c542e89cdb3a6672ff5309d71989c38cc732c77811e7aab84979eb`
- `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V5` — `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V5.md` — SHA-256 `3c63a4b3e18aeaee29512954d7d04d99020fe9190d47d539ade67ab06ff28916`
- `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V6` — `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V6.md` — SHA-256 `109dd22a63c0fd36a02acfc6652245e11188005e44aacf3d8d3b2780d7ee377e`

Package/Request V4–V6 มีสถานะ `EXACT_PROVENANCE_OR_IMMUTABLE_REVIEW_HISTORY / NO_AUTHORITY / NOT_ADOPTED_WHOLESALE` ไม่ถูก co-ratify หรือ adopt ทั้งฉบับ และไม่มี clause ใดได้ authority จาก transitive reference ข้อกำหนด operative ของ Phase A มีเฉพาะสิ่งที่ Owner statement นี้ระบุซ้ำอย่างชัดแจ้งเท่านั้น ข้อความเกี่ยวกับ Decision A, Decision C, Phase B, Tier 2, merge, ruleset, OIDC/signing activation หรือ scientific execution ในเอกสารเหล่านั้นไม่ได้รับ authority จากการอนุมัตินี้ หากเกิดความขัดแย้ง ข้อห้ามและขอบเขตที่แคบกว่าใน Owner statement นี้ควบคุม

ผม co-ratify companion bytes ต่อไปนี้สำหรับ Phase A:

1. `REHEARSAL_SURFACE_MAP_V5` — `configs/governance/rehearsal_surface_map_v5.json` — SHA-256 `87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a`; V5 supersedes Surface Map V4 สำหรับ authorization นี้
2. `MES_EXECUTION_TRANSITION_ROW_ENUM_V3` — `configs/governance/execution_hardening_transition_rows_v3.json` — SHA-256 `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1`
3. `MES_GITHUB_OIDC_SIGSTORE_TIME_POLICY_V1` — `configs/governance/execution_hardening_time_policy_v1.json` — SHA-256 `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e`
4. `EXECUTION_HARDENING_PRODUCTION_SURFACE_MANIFEST_V2` — `configs/governance/execution_hardening_production_surface_manifest_v2.json` — SHA-256 `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a`

Final Phase A review chain ใช้ `MES_CLAUSE_PACKET_TEMPLATE_V1` — `docs/governance/CLAUSE_PACKET_TEMPLATE_V1.md` — SHA-256 `351c73aa8ba16cf233f00f2aab27e9683d55e818655c08817e68b711ecde70c0`

## 2. Exact Phase A path allowlist

อนุญาต additive creation หรือ bounded modification เฉพาะ 28 paths ต่อไปนี้:

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

Path 22 ต้องเป็นไฟล์เดียวใน commit แรกของ Phase A Paths 23–28 เป็น create-once final review/closeout chain และต้องเกิดตามลำดับเท่านั้นหลัง implementation bytes freeze โดย path 28 ต้อง bind complete SHA-256 ของ path 27

คำอนุมัตินี้อนุญาตให้สร้าง paths 23–25 เพื่อ dispatch และรับ fresh review หลัง implementation freeze แต่ยังไม่อนุญาตให้สร้าง paths 26–28 จนกว่า Owner จะให้ separate closeout statement หลังเห็น exact Response ที่ timely, exact-package, exact `FULL_GOVERNED`, packet/tool-conforming, free of verification-side invalidation และ `BLOCKER=0 / HIGH=0`

Exact chain คือ path 23 Packet → path 24 dispatch receipt bind complete path-23 SHA-256 → path 25 response bind complete path-23/path-24 SHA-256 → separate Owner closeout statement → path 26 Owner closeout bind exact Owner statement และ complete path-25 SHA-256 → path 27 closeout receipt bind complete path-26 SHA-256 → path 28 external manifest bind complete path-27 SHA-256 การตอบช้า, invalid response หรือ `BLOCKER>0 / HIGH>0` ให้ STOP โดยไม่มี retry ต่อ unchanged bytes และไม่มี fallback reviewer

การเปลี่ยน path นอก allowlist, dependency, packaging metadata หรือไฟล์ historical Test 2/Test 3 ให้ STOP และต้องขอ Owner authorization ใหม่

## 3. Phase A mode and budgets

`phase_a_mode = TIER1_ONLY_NON_AUTHORITATIVE`

Phase A อนุญาตเฉพาะ deterministic synthetic fixtures ใน memory หรือใต้ pytest-owned temporary directory ที่มี identity `NON_EVIDENTIARY_TIER1_FIXTURE` เท่านั้น fixture เหล่านี้อาจทดสอบ schema, predictors, targets, masks, folds, harmonics, serialization, exclusive-create, reread, SHA-256 และ reservation-state simulation แต่ห้ามกลายเป็น evidence หรือ authority

Exact Phase A execution budgets:

```text
live_tier2_reservations_created = 0
live_tier2_reservations_consumed = 0
tier2_attempts = 0
runtime_rehearsal_runner_executions = 0
persisted_attempt_ledgers = 0
emitted_or_persisted_or_sealed_or_uploaded_or_attested_or_registered_rehearsal_records = 0
phase_a_hardening_runtime_synthetic_models_fitted = 0
phase_a_hardening_runtime_synthetic_fold_fit_calls = 0
phase_a_hardening_runtime_synthetic_bootstrap_replicates = 0
phase_a_hardening_runtime_synthetic_economic_diagnostic_calls = 0
phase_a_hardening_runtime_synthetic_economic_policy_evaluations = 0
real_artifact_metadata_reads = 0
real_row_group_or_statistics_or_numeric_value_reads = 0
real_target_or_path_reads = 0
real_targets_constructed = 0
real_models_or_fold_fits = 0
real_bootstrap_replicates = 0
real_economic_diagnostic_calls = 0
validation_reads = 0
final_test_reads = 0
production_scientific_outputs = 0
hypothesis_slots_consumed = 0
```

Paths 1–21 ห้าม import หรือ call actual fitter, bootstrap หรือ economic-diagnostic implementation; pure state-machine tests may simulate counter values and reservation outcomes but may not create or consume a live Tier 2 reservation

Full existing pytest discovery may execute only pre-existing synthetic regression-fit tests already present at exact base `f2bf04ba2976bce6118472ffcb2e5492336e2aaa` as baseline regression verification Those calls are outside the new hardening runtime namespace, create no rehearsal evidence/authority, and may not be edited through this authorization Their machine-derived observation must be recorded separately as `preexisting_baseline_regression_fit_surface_observed` and must never be merged into or used to weaken the exact zero hardening counters above

## 4. CI and GitHub boundary

สำหรับ Issue #48 ผมเลือกอย่างชัดแจ้ง:

- implement exact `EXECUTED_FROZEN_BYTE_INTEGRITY_V1` addition in `.github/workflows/quant-ci-v1.yml` on the Phase A branch: `YES`
- run that addition in the one dedicated Phase A PR CI: `YES`
- activate or prove default-branch every-PR enforcement in Phase A: `NO`
- close, edit, comment on, label, assign, or otherwise mutate Issue #48: `NO`
- mutate, comment on, label, update, merge, or close PR #47: `NO`
- required-workflow ruleset activation: `NO`

Quant CI may gain only `EXECUTED_FROZEN_BYTE_INTEGRITY_V1` and must remain `contents: read` Broader Tier 1 controls may enter only `.github/workflows/execution-hardening-attestation-v1.yml` as a non-authoritative Phase A hardening workflow All PR/Tier 1 jobs remain `contents: read`

ห้าม `pull_request_target`, workflow-level write permission, GitHub mutation API, auto-merge หรือ hidden CI mutation

Phase A may declare a signer job only if it is job-scoped and mechanically unreachable behind all of these absent prerequisites: exact `workflow_dispatch`, `refs/heads/main`, Phase B ready sentinel, exact trusted-root hash, activation commit/tree, and separate Decision C No signer job or signing step may execute in Phase A

## 5. Trust, time, and reviewer posture

Future mechanism under implementation and test only:

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

Trusted time semantics are exactly those in the co-ratified time-policy bytes: verified Sigstore timestamp as issuance time; issuer/audience/signature-verified GitHub OIDC `iat` as current time; token age `300s`, clock skew `60s`, attestation age `1800s`, exact expiry relation/order/stop codes

แต่ใน Phase A กลไกและ time source ข้างต้นมีสถานะ `IMPLEMENTATION_UNDER_TEST / NOT_ACTIVE / NOT_TRUSTED_FOR_AUTHORITY` เท่านั้น OIDC minting, `actions/attest` invocation, attestation issuance/acceptance, custom trusted-root activation, Section 6 trusted-attestation activation, production signing credential และ execution-authority reservation consumption เท่ากับศูนย์

Phase A final engineering review ใช้ exactly one create-once `FULL_GOVERNED` Clause-Packet attempt โดย `Claude Code CLI 2.1.239 / opus / independent fresh-eyes governance reviewer` ในบทบาท `INDEPENDENT_ADVERSARIAL_PHASE_A_ENGINEERING_REVIEWER` Reviewer นี้ต้องทำงานใน fresh session แยกต่างหากและต้องไม่เคย author, modify หรือช่วยตัดสิน implementation bytes ของ Phase A ก่อนรับ Packet มี deadline 20 นาทีหลัง dispatch, ไม่มี retry ต่อ unchanged bytes และไม่มี fallback reviewer Response ต้อง timely, exact-package, packet/tool-conforming, free of verification-side invalidation และ classify เป็น `UNTRUSTED_CONTEXT_ONLY` ตาม Exit Criterion 10(b) Form นี้ตัดสิน engineering completeness ได้เท่านั้น ไม่ satisfy Section 6 และไม่สร้าง Owner authority หรือ execution authority

## 6. Exact tests and gates

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

Required verification commands and acceptance:

```text
.venv/bin/python -m pytest -q tests/governance
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
git diff --check
git diff --check f2bf04ba2976bce6118472ffcb2e5492336e2aaa...HEAD
```

ทุก command ต้อง return code 0 Test counts ให้ machine-derive และบันทึกจาก exact implementation commit; ไม่ pin จำนวนล่วงหน้าและห้ามลด scope ด้วย manual test enumeration Full-suite pytest ต้องใช้ normal repository discovery

นอกจากนี้ต้องผ่าน transition-companion/protocol exact equivalence, historical/companion SHA integrity, changed/staged allowlist firewall, exact zero-counter assertions, dedicated-PR Quant CI และ non-authoritative hardening CI Any failure stops closed

## 7. Git, commit, push, PR, and review budgets

อนุญาต:

- one Owner-authorization-record commit containing only path 22
- at most seven implementation/repair commits touching only currently eligible paths 1–21
- one final evidence-chain commit after its later closeout authority
- at most one ordinary non-force push after each authorized commit to `refs/heads/governance/execution-hardening-step3-v1`
- exactly one dedicated PR from that branch to `main`, without auto-merge
- Codex and Claude may divide implementation and non-final adversarial review work within these same limits แต่ Claude session ที่สงวนเป็น final `INDEPENDENT_ADVERSARIAL_PHASE_A_ENGINEERING_REVIEWER` ห้ามมีส่วน author หรือ modify implementation bytes

Out-of-allowlist repair, exhausted commit/review budget, failed/late final response หรือ need for additional paths requires STOP and a new Owner statement

ห้าม force-push, amend, rebase, squash, tag, release, second PR, hidden issue/PR mutation หรือ merge

## 8. Explicit prohibitions

การอนุมัตินี้ไม่อนุญาต Decision C, Phase B, Tier 2, ready sentinel, trusted-root file creation, OIDC minting, `actions/attest`, trusted signing/activation, production attestation acceptance, ruleset mutation, `main` mutation, merge, auto-merge, Issue #48 mutation/closeout, PR #47 mutation, production runtime ledger, production evidence registry mutation, dependency, database, broker, live/release path, real artifact metadata/data/row-group/statistics/value/target/path access, target construction from real data, real model fit/bootstrap/economic diagnostics, actual synthetic fit/bootstrap/economic diagnostics from any newly authorized Phase A hardening path, Validation, Final Test, Test 3 retry/repair, Test 3b, Test 4 หรือ scientific execution Pre-existing base synthetic regression-fit tests remain allowed only under the separately disclosed full-suite baseline rule above

Phase A completion grants no Test 3b or scientific authority It may only make separate Decision C consideration eligible after exact evidence and a separate Owner authorization

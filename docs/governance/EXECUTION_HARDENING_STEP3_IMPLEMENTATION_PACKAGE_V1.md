# MES Execution Hardening Step 3 — Implementation Package V1

Package ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V1`

Status: **DRAFT COMPLETE / OWNER AUTHORIZATION REQUIRED / NO IMPLEMENTATION AUTHORITY**

Prepared date: `2026-08-25` (`Asia/Bangkok`)

Preparation base commit/tree: `ad6b7f1a4427f720cfadba71f74f0d025f306add` /
`4f8e674dea4e70cf93e80c4d392f4ac505da377b`

Preparation branch: `governance/execution-hardening-step3-package-v1`

Proposed implementation branch: `governance/execution-hardening-step3-v1`

Governing protocol: `MES_EXECUTION_HARDENING_PROTOCOL_V1` at
`docs/governance/EXECUTION_HARDENING_PROTOCOL_V1.md`, SHA-256
`697358653fd8958c87bbec2e29f83946fd814293f271ba64620fef90afbcfdf7`

Ratification record: `MES_EXECUTION_HARDENING_OWNER_RATIFICATION_V1` at
`docs/governance/EXECUTION_HARDENING_OWNER_RATIFICATION_V1.md`, SHA-256
`3799f3623ff8c511eaa53028e2466c1c5e618e846071038e02afce493e05706e`

Rehearsal surface map: `REHEARSAL_SURFACE_MAP_V1` at
`configs/governance/rehearsal_surface_map_v1.json`, SHA-256
`a4ea3e7110bdcc60d4893ac440fbb2d375e158956e425b795917791a96077370`

This package is an engineering implementation proposal. It is not an Owner authorization,
scientific protocol, target-space amendment, trusted attestation, or execution reservation.
It creates no implementation, CI, push, data, target, fit, Validation, Final Test, merge,
Test 3b, or Test 4 authority.

## 1. Exact outcome

Step 3 will implement and prove the two properties ratified in the governing protocol:

1. every known-invalid state stops at the declared stage and reason; and
2. one isolated synthetic happy path traverses the complete generic governed ladder and
   seals evidence that cannot be accepted as real scientific evidence.

Historical Test 3 files remain byte-identical and are used only as hash-bound regression
sources. Step 3 creates generic future infrastructure; it does not repair, reopen, rerun, or
reinterpret Test 3 and does not consume a target-space hypothesis slot.

## 2. Exact base and lineage rule

The governed package review and closeout must first be anchored in one exact local commit.
That package-closeout commit becomes the exact implementation base named by the later Owner
statement. The first descendant commit may add only the verbatim Owner authorization record;
code begins only after that record commit exists. All later implementation commits remain in
that direct lineage.

No amend, rebase, squash, cherry-pick substitution, merge, or content-equivalent replacement
may change the reviewed/authorized lineage. Every implementation commit must remain a
descendant of the exact authorization-record commit.

## 3. Frozen inputs protected during implementation

The implementation may read but may not modify:

- the three co-ratified execution-hardening documents at commit `bd9a0ae8`;
- `docs/governance/EXECUTION_HARDENING_OWNER_RATIFICATION_V1.md`;
- this implementation package and its governed review chain;
- `configs/governance/rehearsal_surface_map_v1.json` at SHA-256
  `a4ea3e7110bdcc60d4893ac440fbb2d375e158956e425b795917791a96077370`;
- every historical Test 2/Test 3 protocol, code file, evidence record, budget, amendment, and
  ratification record;
- every real-data, Validation, Final-Test, production-ledger, database, live, and broker path.

## 4. Exact implementation allowlist

Only these 22 paths may change after the future exact Owner authorization. One existing file
may be modified; the other 21 paths are additive.

### 4.1 Existing file permitted to change

1. `.github/workflows/quant-ci-v1.yml`

Its only authorized semantic change is adding the checkout-safe executed-frozen registry
integrity test required by Issue #48. Existing jobs, exclusions, and protected gates may not
be weakened, removed, renamed, or reinterpreted.

### 4.2 Additive workflow and registry controls

2. `.github/workflows/execution-hardening-attestation-v1.yml`
3. `configs/governance/executed_frozen_registry_v1.json`
4. `configs/governance/execution_hardening_attestation_ready_v1.json`

### 4.3 Additive implementation package

5. `src/mes_quant/governance/execution_hardening/__init__.py`
6. `src/mes_quant/governance/execution_hardening/boundary.py`
7. `src/mes_quant/governance/execution_hardening/records.py`
8. `src/mes_quant/governance/execution_hardening/attestation.py`
9. `src/mes_quant/governance/execution_hardening/registry.py`
10. `src/mes_quant/governance/execution_hardening/executed_frozen.py`
11. `src/mes_quant/governance/execution_hardening/rehearsal.py`

### 4.4 Additive tools

12. `tools/build_execution_hardening_review_report.py`
13. `tools/run_execution_hardening_rehearsal.py`
14. `tools/verify_execution_hardening_attestation.py`

### 4.5 Additive tests

15. `tests/governance/test_execution_hardening_boundary.py`
16. `tests/governance/test_execution_hardening_records.py`
17. `tests/governance/test_execution_hardening_attestation.py`
18. `tests/governance/test_execution_hardening_registry.py`
19. `tests/governance/test_execution_hardening_executed_frozen.py`
20. `tests/governance/test_execution_hardening_rehearsal.py`
21. `tests/governance/test_execution_hardening_ci_spec.py`

### 4.6 Additive Owner authorization record

22. `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_AUTHORIZATION_V1.md`

This record must be the only changed path in the first commit after the exact implementation
base. It preserves the later Owner statement verbatim and creates no authority beyond it.

No dependency, `pyproject.toml`, historical Test 2/Test 3 source, evidence, protocol, budget,
authorization, or ratification file is in the implementation allowlist.

## 5. Component boundary

### 5.1 Shared boundary and record contracts

`boundary.py` owns only true cross-stage invariants: byte-semantic identity validation,
finite scalar classification, integral `{0,1}` boolean normalization, ordered projected
Arrow schema/type/nullability conformance, and type-correct non-empty consumer rehearsal.

`records.py` owns the exact V1 closed record kinds, two ledger enums and transitions,
monotone execution-authorization-reservation-consumed boolean, sticky fail-closed semantics,
and rejection of every unknown state/transition. Neither module imports or accesses data
providers, artifact paths, or production ledgers.

### 5.2 Attestation and evidence isolation

`attestation.py` validates the exact Section 6 field set, attempt budget and replay ledger,
packet mode, package/report identities, reviewer identity, expiry, trusted timestamp, signer
workflow, and deterministic verdict. It must fail closed on every Section 6.1 outcome.

`registry.py` owns separate production and rehearsal record validators, trust-root isolation,
positive production bindings, the closed `NO_SOURCE_ARTIFACT_ACCESSED` sentinel, namespace
firewalls, create-once sealing, reread/hash verification, and bidirectional registry
rejection. It must never expose a production ledger or signing handle to rehearsal code.

### 5.3 Executed-frozen registry

`executed_frozen.py` reads only the checkout-safe path/SHA/evidence identities in
`configs/governance/executed_frozen_registry_v1.json`. The first mandatory entry is:

```text
path = docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md
authoritative_sha256 = 7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105
authority = Test 2 G3-P execution evidence + Erratum 001
```

The registry check is independent of ignored numeric artifacts and requires no data access.
A one-byte registered-file mutation must fail deterministically.

### 5.4 Tier 2 rehearsal

`rehearsal.py` consumes only in-memory synthetic adapters and isolated temporary directories.
It traverses the generic stages `CONTRACT`, `METADATA`, `PRE_TARGET`, `TARGET_PREFIT`, `FIT`,
and `SEALED`, using the exact surfaces pinned by `REHEARSAL_SURFACE_MAP_V1`.

The implementation may replace only source, namespace, trust root, and state-store handles
with isolated rehearsal variants. It may not monkeypatch or substitute validators, stage
predicates, reason mapping, serializers, attestation verification, reservation logic,
sealing/reread checks, or registry predicates.

## 6. Exact synthetic computation and run budget

This is an engineering budget, not a scientific hypothesis or search budget.

Per Tier 2 rehearsal reservation:

- synthetic models: exactly `2`;
- synthetic folds: exactly `2`;
- synthetic fold-fit calls: maximum `4`;
- bootstrap blocks: maximum `3`;
- bootstrap repetitions per block: exactly `64`;
- total synthetic bootstrap replicates: maximum `192`;
- economic diagnostic calls: maximum `1`;
- economic policy evaluations: maximum `2`;
- real data/target/path reads, real fits, real bootstraps, Validation reads, and Final-Test
  reads: exactly `0`.

The implementation authorization may permit at most four isolated Tier 2 reservation
consumptions: two local implementer runs and two GitHub Actions runs. Every attempted Tier 2
run consumes one isolated rehearsal reservation before any fit. Unit-level Tier 1 fixtures do
not consume a Tier 2 reservation and may not emit sealed rehearsal evidence.

The deterministic seed namespace is `REHEARSAL_EXECUTION_HARDENING_V1`; implementation must
freeze one exact integer seed before the first Tier 2 run and report it in every record.

## 7. Trusted-attestation mechanism

The production-facing deterministic reviewer is not Claude or another LLM. It is:

```text
reviewer_role = EXECUTION_HARDENING_DETERMINISTIC_REVIEWER_V1
provider = GitHub Actions OIDC / Sigstore
model = NONE_DETERMINISTIC_RULE_ENGINE
signer_workflow = NonChaianon/mes-quant-engine-v1/.github/workflows/execution-hardening-attestation-v1.yml
oidc_issuer = https://token.actions.githubusercontent.com
source_ref = refs/heads/governance/execution-hardening-step3-v1
action = actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6
predicate_type = https://slsa.dev/provenance/v1
trusted_time_source = Sigstore transparency-log or timestamp-authority verifiedTimestamps
```

The workflow produces a deterministic review-report artifact bound to the exact commit,
tree, diff base, allowlist, ordered file SHA-256 values, packet/report identities, reviewer
role, explicit verdict, BLOCKER/HIGH counts, completion state, attempt identity, and expiry.
`actions/attest` signs the report digest with a short-lived certificate issued from GitHub's
OIDC identity through Sigstore. Verification must use `gh attestation verify` with exact
repository, signer workflow, source ref, signer/source digest where available, GitHub OIDC
issuer, public-good Sigstore allowed, and self-hosted runners denied.

Only certificate identity and verified timestamps are trusted external facts. Predicate and
report content remain workflow-controlled and are accepted only because the signer workflow
itself is allowlisted, hash-reviewed, deterministic, and protected by exact commit binding.
Any workflow-path, commit, ref, package, report, packet-mode, attempt, expiry, or replay
mismatch fails closed.

This mechanism proves the deterministic workflow and report provenance. It does not prove a
Claude provider/model identity. Claude Code remains a separate fresh-eyes reviewer under a
`FULL_GOVERNED` Clause Packet whose response is `UNTRUSTED_CONTEXT_ONLY`, as permitted by
Exit Criterion 10(b). That response cannot satisfy Section 6 or authorize execution.

Official mechanism references observed on 2026-08-25:

- `https://github.com/actions/attest`;
- `https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations`;
- `https://cli.github.com/manual/gh_attestation_verify`.

## 8. Review and attempt budgets

The pre-implementation `FULL_GOVERNED` Clause Packet review permits at most two Claude Opus
attempts against unchanged package bytes. Each attempt has a 20-minute bounded deadline.
Timeout, `NO_VERDICT`, cancellation, invalidation, or supersession produces exactly one
terminal attempt-outcome artifact. A response at or after the deadline is retained only as
`LATE_RESPONSE_UNTRUSTED_CONTEXT`.

Any BLOCKER/HIGH verdict requires changed package bytes, a new commit/tree, a new packet, and
a new attempt lineage. A completed PASS with BLOCKER/HIGH = 0 may be presented to the Owner;
it creates no authority by itself.

The final implementation fresh-eyes review has the same two-attempt ceiling but requires a
new Clause Packet bound to the implementation commit/package.

## 9. Issue #48 and CI decision

This package proposes to **subsume the exact acceptance work of Issue #48** and activate only
the executed-frozen registry integrity test inside existing `Quant CI V1` on every pull
request. The implementation may make Issue #48 eligible for later closeout after CI evidence,
but may not edit, comment on, label, assign, or close the issue without a separate Owner
authorization.

All other execution-hardening Tier 1 tests enter only the new
`execution-hardening-attestation-v1.yml` workflow. The workflow remains inert until the exact
attestation-ready sentinel exists. Once present, every later push to the exact implementation
branch reruns the complete hardening suite and attests a newly generated deterministic report.

Draft PR #47 remains entirely outside authority. No PR #47 mutation or merge is permitted.

## 10. Required tests and gates

Before any implementation commit is eligible for Owner closeout:

1. every Tier 1 row in the ratified protocol passes its exact stop/pass and reason code;
2. the Test 3 historical landmines are reproduced only as synthetic regression fixtures;
3. every declared and unlisted two-ledger transition is tested;
4. attestation outcomes are tested with attempt budget remaining and exhausted;
5. production/rehearsal registry positive and negative fixtures pass;
6. every single and combined rehearsal-marker mutation remains rejected by production;
7. executed-frozen mutation test fails on one-byte drift;
8. one local Tier 2 happy path seals, rereads, and hash-verifies rehearsal evidence;
9. all protected real counters remain zero and production governance hashes remain unchanged;
10. `python -m pytest -q` passes in full;
11. `python -m ruff check .` passes;
12. changed-file allowlist and protected-surface firewalls pass;
13. the existing `Quant CI V1` checkout-safe executed-frozen test passes on a pull request;
14. the GitHub attestation workflow completes on the exact implementation commit;
15. `gh attestation verify` passes the exact signer/ref/repository/time policy;
16. a final `FULL_GOVERNED` fresh-eyes review returns BLOCKER = 0 and HIGH = 0.

The implementation may use synthetic in-memory fixtures and temporary directories only.
No test may discover or open a real project artifact path.

## 11. Commit and push posture proposed for Owner decision

To keep local and origin state close, the implementation authorization may permit one
authorization-record commit followed by at most five bounded implementation commits, with
one push after each commit to the exact implementation branch. Intermediate workflow runs
may remain skipped while the attestation-ready sentinel is absent. The final sentinel commit
activates the complete workflow.

No force-push, tag, release, merge, `main` mutation, PR #47 mutation, or Issue #48 mutation is
permitted. The final local and remote SHA must match exactly.

## 12. Forbidden actions

- no modification or execution of historical Test 3 stages;
- no Test 3 repair, retry, Test 3b, Test 4, budget override, or new hypothesis;
- no real DBN/Parquet/artifact metadata, row group, statistics, numeric value, target, or path
  access;
- no production model fit, forecast, loss, bootstrap, diagnostic, or evidence;
- no Validation or Final-Test access;
- no production target-space, authorization, repair, attempt, or evidence ledger mutation;
- no production trust-root, signing material, or credentials in code, tests, logs, or Git;
- no dependency, database, broker, live path, release, merge, tag, or force-push;
- no hidden CI broadening beyond the two workflows and exact tests declared here.

## 13. Exit and next authority

Step 3 completion proves engineering controls only. It grants no scientific authority and
does not reopen Test 3. After all exit gates and evidence are sealed, the Owner may separately
decide whether to close Issue #48 and whether any Step 5/Test 3b decision is eligible for
consideration. Test 3b, Test 4, real data, target access, production fit, Validation, Final
Test, and merge always require separate exact Owner authority.

# Stage B V1.2 Lock-Breaker 5 Policy/Execution Separation Remediation

## Authority and bounded scope

- GitHub authority: Issue #15, `Stage B V1.2 — remediate lock-breaker 5: separate policy and execution status`
- Authorized baseline: `e64c6d3602f747d24ebbfe57cfafc12beb2189fd`
- Remediation branch: `agent/stage-b-v1-2-policy-execution-separation`
- Archived-audit commit: `bfb249433052d3d7cfddab008b13bd9a9d59ae80`
- Remediation implementation commit: `d912a8acc4a3b86c4a6ee61f14db0e17d2e8621f`
- Frozen architecture: V2.2, unchanged

This is the bounded `V1_2_LOCK_BREAKER_5` remediation authorized by Issue #15.
It is not a new design cycle, does not perform the V1.2 mechanical lock, does
not enable Stage B execution, and does not implement Phase B, C, or D.

Draft PR #14 remains Draft and unmerged. Its mechanical-lock candidate is not
accepted and supplies no A6 lock authority. The accepted Issue #8 final-audit
result remains evidence for the repository state it audited; it is not
reinterpreted as authority to merge or lock in this remediation.

## Exact files changed from the authorized baseline

| Path | Bounded purpose |
|---|---|
| `.github/workflows/quant-ci-v1.yml` | Report both independent Python machine states during CI import verification. |
| `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | State the independent policy-lock and artifact-execution predicates and their pre-I/O gate order. |
| `docs/architecture/ARCHITECTURE_PROGRESS.md` | Record the proven blocker, PR #14 disposition, and Issue #15 independent-review gate without advancing A6. |
| `docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md` | Preserve the exact accepted Issue #8 audit evidence from Draft PR #14. |
| `docs/audits/STAGE_B_V1_2_LOCK_BREAKER_5_POLICY_EXECUTION_SEPARATION_REMEDIATION.md` | Record this bounded remediation and its verification. |
| `src/mes_quant/redundancy/__init__.py` | Export the independent execution status. |
| `src/mes_quant/redundancy/analyzer.py` | Enforce execution and policy as distinct pre-I/O predicates; retain all existing downstream controls and the Phase-B stop. |
| `src/mes_quant/redundancy/contract.py` | Add the machine-authoritative execution field and pin the amended provisional Markdown bytes. |
| `tests/test_redundancy.py` | Prove the status truth table, pre-I/O failure, exact semantic preservation, and synthetic-only Phase-B boundary. |

The semantic registry, frozen architecture, release manifest, feature
methodology, thresholds, tolerances, and production orchestration beyond the
entry predicate were not changed.

## Machine predicates before and after

Before remediation:

```text
POLICY_STATUS = PROVISIONAL
EXECUTION_STATUS = <not represented>

future entry predicate:
POLICY_STATUS == LOCKED_EXECUTABLE
```

One field therefore represented both policy authority and execution
eligibility.

After remediation:

```text
current POLICY_STATUS    = PROVISIONAL
current EXECUTION_STATUS = DISABLED

future policy predicate:    POLICY_STATUS == LOCKED
future execution predicate: EXECUTION_STATUS == ENABLED

entry authority:
(EXECUTION_STATUS == ENABLED)
AND (POLICY_STATUS == LOCKED)
AND exact Markdown/registry/version/hash/source controls
```

`contract.EXECUTION_STATUS` is specifically the Stage-B artifact-entry
predicate. It does not replace or change the project deployment state
`RESEARCH_ONLY / LIVE_DISABLED`.

No current policy control was promoted: Python, Markdown, and registry remain
`PROVISIONAL`; Python execution remains `DISABLED`.

## Truth table and pre-I/O proof

| Policy state | Execution state | Result |
|---|---|---|
| `PROVISIONAL` | `DISABLED` | Stop on execution predicate before path resolution or file reads. |
| `LOCKED` | `DISABLED` | Stop on execution predicate before path resolution or file reads; policy lock alone cannot execute. |
| `PROVISIONAL` | `ENABLED` | Stop on policy predicate before path resolution or file reads; execution alone has no policy authority. |
| `LOCKED` | `ENABLED` | May inspect exact constitutional controls; any version/hash/status/source mismatch still stops. |
| `LOCKED` with exact synthetic locked controls | `ENABLED` | Isolated test reaches mocked Phase 0/A and then the unchanged unimplemented Phase-B boundary. |

The source order in `assert_stage_b_contract_locked()` is:

```text
EXECUTION_STATUS predicate
-> POLICY_STATUS predicate
-> Path(project_root).resolve()
-> control read_bytes()
-> existing exact control validation
```

`run_stage_b()` still invokes this gate as its absolute first executable action.
The current `DISABLED` state therefore stops before control or artifact I/O.

The both-enabled test is synthetic and isolated: it uses a temporary directory,
synthetic bytes, patched parsers, and patched Phase 0/A functions. It is not a
real Stage B run and opens no external artifact or Cell 8 assignment file.

## Policy, methodology, and provenance preservation

- Issue #8 audit archive raw SHA-256:
  `3faadd5217e99e2baa5c7d1772532a43e91525221b7d5b6a0b41bc6b28f0c438`
- Current provisional Markdown raw SHA-256 and Python pin:
  `77d512801f245601f169c667d6b6d9516522a4717d78d23cdbfe2e1fa890c03c`
- Semantic registry raw SHA-256, byte-identical to baseline:
  `056ba7639960c8dd9c65d7e6a7a6a383e432a069651503def8bf05e3cafed861`
- Canonical `semantic_checks` SHA-256 before and after:
  `53f37c14b3e2b7da2e39ad9a27fe287b1b3a3f362aeca375a2adc02f28a74cff`
- Frozen Architecture V2.2 raw SHA-256, unchanged:
  `e2fcf97142bf340e8462003787dd6ec90dc4971444d492388ec2d07ec2271eaf`
- `GENERIC_RANK_DIRECT_DROP_AUTHORIZED = False`, unchanged.
- `GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN = False`, unchanged.
- Every pre-existing literal Python contract value is equal to baseline except
  the required Markdown byte pin; `EXECUTION_STATUS = DISABLED` is the sole new
  authority field.
- Phase-A semantic KEEP/DROP authority, formulas, thresholds, tolerances,
  BL-30 evidence, Cell 14 identity, and all upstream provenance pins are
  unchanged.
- The only active V1.2 policy-lock token is `LOCKED`; remaining
  `LOCKED_EXECUTABLE` text is explicitly historical V1.0/V1.1 evidence.

No Architecture V2.3, methodology redesign, Phase B/C/D production logic,
label logic, Validation outcome, Final Test outcome, future-return access, P&L
logic, or Cell 8 assignment-row access was added.

## Verification results

All Python commands below used checkout-local imports by setting
`PYTHONPATH` to this branch's `src` directory and asserting that imported module
paths were descendants of this checkout. An unrelated editable installation
points to another worktree and was not used as candidate evidence.

| Verification | Result | Exit |
|---|---:|---:|
| `python -m compileall -q src tests tools` plus checkout-origin import and current-state assertions | PASS | 0 |
| `python -m ruff check --select E9,F401,F63,F7,F82 src tests tools` | `All checks passed!` | 0 |
| `git diff --check` | clean | 0 |
| `StageBLockedControlTests` | 6 passed | 0 |
| `StageBConstitutionalPolicyGateDirectTests` | 7 passed | 0 |
| `StageBProjectRootGateSpecificationTests` | 4 passed | 0 |
| Lock/control/root/production-boundary matrix | 25 passed | 0 |
| CI-focused Phase 0/A, generic-rank, group-rank, and production-boundary classes | 64 passed | 0 |
| Checkout-safe full `tests/test_redundancy.py` | 164 passed, 15 deselected | 0 |
| `tests/test_manifest.py tests/test_feature_builder.py tests/test_reference_freeze.py` | 26 passed, 1 skipped | 0 |
| Static baseline/hash/AST preservation proof | `STATIC_PRESERVATION_PROOF_PASS` | 0 |

Environmental exclusions are not passes:

- The external Cell 14 feature-registry artifact is absent. The one frozen
  canonical-registry compatibility method and the 14-test Phase-A decision
  bridge class were intentionally deselected: 15 deselections total.
- One repository test skipped because its optional local large-artifact cache
  is absent.
- `tests/test_cell14_release.py` was not run in checkout-only verification
  because the complete ignored Cell 14 release artifacts are absent.

## Safety counters

```text
real Stage B production runs                 0
labels / future returns opened               0
Validation outcomes opened                   0
Final Test outcomes opened                   0
P&L opened                                   0
Cell 8 assignment rows opened                0
Phase B/C/D production implementations added 0
mechanical V1.2 lock actions                 0
merge actions                                0
```

## Independent-review handoff

This remediation candidate must remain a Draft PR. It must not be merged by the
implementing agent. Independent review should verify the two machine fields,
the pre-I/O conjunction, exact semantic-registry preservation, the unchanged
Phase-B boundary, and the recorded environmental exclusions. Only after this
remediation is independently accepted and separately merged may Issue #13
resume as the same mechanical lock workflow from the new `main`.

## Final verdict

LOCK_BREAKER_5_POLICY_EXECUTION_SEPARATION_REMEDIATED

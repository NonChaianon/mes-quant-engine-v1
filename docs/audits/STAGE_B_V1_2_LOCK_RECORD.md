# Stage B V1.2 Mechanical Policy Lock Record

## Authority and scope

- GitHub authority: Issue #13, resumed after accepted Issue #15 remediation.
- User-authorized baseline: `bd6611b040ee94b8c73f800d4d157eec3bf9cf0a`.
- Baseline identity: merge of PR #16, `separate Stage B policy and execution status`.
- Branch: `agent/stage-b-v1-2-mechanical-lock-post-issue15`.
- Architecture: `MES_QUANT_TARGET_ARCHITECTURE_v2.2`, unchanged.
- Operation: mechanical Stage B V1.2 policy lock only.

The Issue #13 body retains its original pre-Issue-15 baseline. The explicit
continuation instruction authorizes the exact post-Issue-15 `main` commit above;
remote `main`, local `origin/main`, branch parent, and merge base were verified
against that SHA before editing.

PR #14 was not reopened or reused. GitHub records it as closed and unmerged,
with no merge commit and no lock authority. This candidate uses a new branch,
fresh control commit, fresh provenance pins, and a new Draft PR.

This lock does not redesign methodology, enable artifact execution, implement
Phase B/C/D production execution, or perform a real Stage B run.

## Step 0 — accepted final-audit archive

Step 0 completed before any policy/status/hash mutation.

| Evidence | Exact value |
|---|---|
| Path | `docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md` |
| Required raw SHA-256 | `3faadd5217e99e2baa5c7d1772532a43e91525221b7d5b6a0b41bc6b28f0c438` |
| Observed raw SHA-256 | `3faadd5217e99e2baa5c7d1772532a43e91525221b7d5b6a0b41bc6b28f0c438` |
| Git blob | `778c01d0cddb642c9a4c24a00638767e3f691bd0` |
| Archive commit | `bfb249433052d3d7cfddab008b13bd9a9d59ae80` |
| Archive commit parent | `e64c6d3602f747d24ebbfe57cfafc12beb2189fd` |
| Baseline/current byte equality | exact |

The archive already existed as committed evidence in the authorized baseline,
so it was not copied again, reformatted, reinterpreted, or modified. It remains
audit evidence and is not policy authority.

## Non-self-referential locked-control provenance

The established two-step procedure was used with fresh post-Issue-15 commits:

1. Commit `bb68e6d8be9244564c2d06179cffde775041c8f3` has exact parent
   `bd6611b040ee94b8c73f800d4d157eec3bf9cf0a` and changes only:
   - Markdown `Policy status: **PROVISIONAL**` to `**LOCKED**`;
   - semantic-registry `registry_status` from `PROVISIONAL` to `LOCKED`.
2. Raw hashes were computed from those committed blobs.
3. Later commit `131cf7a37d0beb41bf258ffa9beaf942c443985d` pins the first
   commit and those raw hashes in Python, changes Python policy to `LOCKED`,
   leaves execution `DISABLED`, and mechanically aligns tests.
4. The pin commit does not point to or hash itself.
5. Final candidate Markdown and registry bytes remain byte-identical to the
   first control commit.

Historical V1.1 provenance remains separately pinned as
`PRIOR_V1_1_LOCKED_CONTROL_COMMIT = bd9e38c11e01bae18a5ffa0a6a0405a008273d27`.

## Pre/post machine state

| Layer | Baseline | Lock candidate |
|---|---|---|
| Python `POLICY_STATUS` | `PROVISIONAL` | `LOCKED` |
| Markdown policy status | `PROVISIONAL` | `LOCKED` |
| Semantic-registry status | `PROVISIONAL` | `LOCKED` |
| Python `EXECUTION_STATUS` | `DISABLED` | `DISABLED` |
| Policy version | `MES_V1_REDUNDANCY_1.2` | unchanged |
| Registry `source_contract` | `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | unchanged |

Policy authority and Stage-B artifact execution remain independent. The policy
lock does not change execution state and cannot by itself enable I/O.

## Final locked control bytes

| Control | Baseline raw SHA-256 | Locked raw SHA-256 |
|---|---|---|
| Markdown contract | `77d512801f245601f169c667d6b6d9516522a4717d78d23cdbfe2e1fa890c03c` | `7db2abd3e7fd6ee3e7bde2e0509a9141046067d82f97dd1cce85af66f047e334` |
| Semantic registry | `056ba7639960c8dd9c65d7e6a7a6a383e432a069651503def8bf05e3cafed861` | `88912eb49b10a3437ccf3ace3cf48ca76200f9e808a558fe3ca00a91f3737561` |

Python pins match the exact locked bytes. `git show` bytes at the locked-control
commit match the final candidate bytes for both files.

## Semantic and methodology preservation

- `semantic_checks` deep equality is exact against both the authorized baseline
  and the pre-lock Issue #8 baseline.
- Ordered semantic-check count remains `6`.
- Canonical `semantic_checks` SHA-256 before and after is
  `53f37c14b3e2b7da2e39ad9a27fe287b1b3a3f362aeca375a2adc02f28a74cff`.
- Registry `policy_version`, `source_contract`, ordering, decision effects,
  required-drop counts, protection flags, implementation keys, feature
  membership, and rationales are unchanged.
- `GENERIC_RANK_DIRECT_DROP_AUTHORIZED = False`, unchanged.
- `GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN = False`, unchanged.
- Every common literal Python contract constant is unchanged except the four
  authorized policy/provenance/hash values; the added prior-V1.1 constant
  preserves the displaced historical value.
- All thresholds, tolerances, Phase-A semantic authority, BL-30 pins, Cell 14
  pins, Cell 8 provenance pins, and target-blind boundaries are unchanged.
- Issue #15 remediation report remains byte-identical at SHA-256
  `a355a2392f6929409a8d753e8133e217270be52193daa59621f2b2d66ecf0d15`.
- `src/mes_quant/redundancy/analyzer.py` remains byte-identical to baseline at
  SHA-256 `357204ff43683f97dab8d1e610a3d4d48945a8d02cb16b27b98b94492c01cad0`.
- Architecture V2.2 remains byte-identical at SHA-256
  `e2fcf97142bf340e8462003787dd6ec90dc4971444d492388ec2d07ec2271eaf`.

No Architecture V2.3, methodology redesign, formula, threshold, tolerance,
feature decision, or production execution logic was added or changed.

## Execution-disabled and fail-closed proof

The unchanged machine gate order is:

```text
EXECUTION_STATUS == ENABLED
-> POLICY_STATUS == LOCKED
-> Path(project_root).resolve()
-> control read_bytes()
-> exact constitutional validation
```

The candidate's real state is `LOCKED / DISABLED`; therefore it stops on the
first predicate before path resolution and before control or artifact reads.
An explicit checkout-local verification intercepts `Path.resolve`,
`read_bytes`, and `read_text` and confirms none is reached. Policy lock alone
cannot enable execution.

`run_stage_b()` still calls the constitutional gate as its absolute first
executable action. Static AST proof confirms the Phase-A call remains present,
no Phase-B implementation call exists, and the final top-level action remains
the unconditional `Phase B boundary is not yet implemented` exception.

The both-enabled boundary test is synthetic only: it uses temporary synthetic
bytes and mocks, never production artifacts, and proves the existing stop after
mocked Phase 0/A. It is not a real Stage B production run.

## Exact files changed from the authorized baseline

| Path | Mechanical purpose |
|---|---|
| `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | Promote the single authoritative Markdown policy-status line. |
| `configs/v1/stage_b_semantic_registry_v1.json` | Promote only the top-level registry status. |
| `src/mes_quant/redundancy/contract.py` | Set policy `LOCKED`, retain execution `DISABLED`, and pin fresh control provenance/hashes. |
| `tests/test_redundancy.py` | Align lock/status/provenance assertions and preserve independent execution tests. |
| `docs/architecture/ARCHITECTURE_PROGRESS.md` | Record the conditional post-merge A6 lock state and unchanged disabled execution. |
| `docs/audits/STAGE_B_V1_2_LOCK_RECORD.md` | Record this mechanical lock candidate and its evidence. |

The accepted Issue #8 audit, Issue #15 remediation report, analyzer/runtime,
Architecture V2.2, workflow, production artifacts, and all other files are
unchanged.

## Local verification

Every Python command set `PYTHONPATH` to this checkout's `src` directory and
verified module paths were descendants of this worktree. The global editable
installation points to another worktree and was not used as candidate evidence.

| Command / selection | Exact result | Exit |
|---|---:|---:|
| `python -m compileall -q src tests tools` plus checkout-origin/status import assertions | PASS (`LOCKED / DISABLED`) | 0 |
| `python -m ruff check --select E9,F401,F63,F7,F82 src tests tools` | `All checks passed!` | 0 |
| `git diff --check bd6611b040ee94b8c73f800d4d157eec3bf9cf0a..HEAD` | clean | 0 |
| Static baseline/control/hash/AST preservation proof | `STATIC_LOCK_PRESERVATION_PROOF_PASS` | 0 |
| Locked-policy/disabled-execution `Path.resolve` and read intercept | `LOCKED_POLICY_DISABLED_EXECUTION_PRE_IO=PASS` | 0 |
| `StageBLockedControlTests` | 6 passed | 0 |
| `StageBConstitutionalPolicyGateDirectTests` | 7 passed | 0 |
| `StageBProjectRootGateSpecificationTests` | 4 passed | 0 |
| Lock/gate/root/production-boundary matrix | 25 passed | 0 |
| CI-focused Phase 0/A, generic-rank, group-rank, and production-boundary classes | 64 passed | 0 |
| Checkout-safe full `tests/test_redundancy.py` | 164 passed, 15 deselected | 0 |
| `tests/test_manifest.py tests/test_feature_builder.py tests/test_reference_freeze.py` | 26 passed, 1 skipped | 0 |

Environmental exclusions are not passes:

- The external Cell 14 feature-registry artifact is absent. The frozen
  canonical-registry compatibility method and the 14-test Phase-A decision
  bridge class were intentionally deselected: 15 deselections total.
- One reference-freeze test skipped because its optional local large-artifact
  cache is absent.
- `tests/test_cell14_release.py` was not run because it requires the complete
  ignored Cell 14 release artifacts. This is not a pass or waiver.
- Remote `Quant CI V1` must complete on the new Draft PR before handoff; local
  results do not substitute for that check.

## Safety counters

```text
real Stage B production runs                 0
labels / future returns opened               0
Validation outcomes opened                   0
Final Test outcomes opened                   0
P&L opened                                   0
Cell 8 assignment rows opened                0
Phase B/C/D production implementations added 0
execution enablement actions                 0
merge actions                                0
```

## Progress and independent-review boundary

`ARCHITECTURE_PROGRESS.md` expresses the proposed post-merge A6 state as
`LOCKED`, while explicitly stating that Draft/branch state has no mainline lock
authority. A6 becomes locked on `main` only after independent acceptance and an
explicitly authorized merge. Stage-B artifact execution and live execution
remain disabled.

Only after that accepted merge may the next sequence begin:

```text
LABEL_EXPOSURE_PRE_FIREWALL acknowledgment
-> Exploratory Lane V1 charter
-> Edge Discovery Sprint 1 protocol
```

No next-stage action begins in this candidate. The implementing agent must open
a new Draft PR, must not reuse PR #14, and must not merge.

## Final verdict

V1_2_LOCK_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW

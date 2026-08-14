# Stage B V1.2 mechanical lock record

## Authority and disposition

This record covers the mechanical policy-control lock authorized by
[GitHub Issue #13](https://github.com/NonChaianon/mes-quant-engine-v1/issues/13).

- Authorized baseline: `e64c6d3602f747d24ebbfe57cfafc12beb2189fd`
- Issue #9 remediation merge: `e16bb5a432bcc98052b6a19167c396af0167ba86`
- Accepted Issue #8 disposition: `SAFE_TO_LOCK_V1_2`
- Branch: `agent/stage-b-v1-2-mechanical-lock`
- Lock-control commit: `a60d2498754df641e9c8a3308d330f3c4e05fb74`
- Pin/test/progress commit: `5531a17f3f82cbe1786e63c551ae39ac9091ffee`
- `origin/main` at verification: `e64c6d3602f747d24ebbfe57cfafc12beb2189fd` (unchanged)
- PR disposition: Draft only; independent review required; no merge performed

This work did not reopen design, change methodology, implement Phase B/C/D
production execution, or authorize a real Stage B run.

## Step 0 — final-audit archival before lock mutation

Before any policy status or hash field changed, the existing final-audit report
was copied byte-for-byte to:

`docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md`

| Check | Required | Observed | Result |
|---|---|---|---|
| Raw SHA-256 | `3faadd5217e99e2baa5c7d1772532a43e91525221b7d5b6a0b41bc6b28f0c438` | `3faadd5217e99e2baa5c7d1772532a43e91525221b7d5b6a0b41bc6b28f0c438` | Exact |
| Archive-only commit | parent must be the authorized baseline | `e0e00ca27740c8b8580238f12873e809d06d4a53`, parent `e64c6d3602f747d24ebbfe57cfafc12beb2189fd` | Exact |
| Archive commit scope | only the final-audit report | exactly one added path | Exact |
| Final candidate recheck | working bytes must equal archived bytes | raw bytes equal `git show e0e00ca:docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md` | Exact |

The archived report is audit evidence. It is not policy authority.

## Mechanical status transition

| Layer | Baseline | Lock candidate | Meaning |
|---|---|---|---|
| Markdown policy status | `PROVISIONAL` | `LOCKED_EXECUTABLE` | Approved policy document locked |
| Semantic-registry status | `PROVISIONAL` | `LOCKED_EXECUTABLE` | Approved semantic authority locked |
| Python `POLICY_STATUS` sentinel | `PROVISIONAL` | `PROVISIONAL` | Production execution remains disabled |
| Policy version | `MES_V1_REDUNDANCY_1.2` | unchanged | No version or methodology change |
| Registry `source_contract` | `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | unchanged | Binding preserved |

The Python name is existing status machinery and was not redesigned. Under the
repository's established procedure, locked Markdown/registry policy controls
and the Python execution sentinel have distinct operational roles. Promoting
the Python sentinel would let the first constitutional gate pass and permit
artifact I/O plus Phase 0/A. Issue #13 requires execution to remain disabled,
so that sentinel intentionally remains `PROVISIONAL`.

## Exact changed files

| Path | Mechanical purpose |
|---|---|
| `docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md` | Archive the accepted Issue #8 evidence unchanged before lock mutation |
| `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | Promote the single policy-status line |
| `configs/v1/stage_b_semantic_registry_v1.json` | Promote only top-level `registry_status` |
| `src/mes_quant/redundancy/contract.py` | Pin exact locked bytes and V1.2 control provenance while keeping execution disabled |
| `tests/test_redundancy.py` | Align only lock/provenance/status tests with locked controls and the disabled execution sentinel |
| `docs/architecture/ARCHITECTURE_PROGRESS.md` | Record A6 locked, execution disabled, accepted final audit, and the frozen next sequence |
| `docs/audits/STAGE_B_V1_2_LOCK_RECORD.md` | Record the mechanical lock evidence and verification |

`src/mes_quant/redundancy/analyzer.py` and
`docs/architecture/MES_QUANT_TARGET_ARCHITECTURE_v2.2.md` were not changed.

## Locked bytes and non-self-referential Git provenance

| Control | Baseline raw SHA-256 | Locked raw SHA-256 |
|---|---|---|
| Markdown | `173afa7e26717795abb88eef1880af1ce8e3cecca133604840942fa8c6d12a96` | `b672124603d6f4057c3aa54dc98b04ac056ccf9bbf3d82fb31b4d856f729e33f` |
| Semantic registry | `056ba7639960c8dd9c65d7e6a7a6a383e432a069651503def8bf05e3cafed861` | `9c50ed834bf82d66115ab54757d1d04d0a03c2afab1fe7a81d9fcaf8293f91e1` |

The established two-step procedure was followed:

1. Commit `a60d2498754df641e9c8a3308d330f3c4e05fb74` committed the exact locked
   Markdown and registry bytes. Its diff contains only the two authorized
   status changes.
2. The later commit `5531a17f3f82cbe1786e63c551ae39ac9091ffee` pinned that predecessor commit
   and both raw hashes in Python. The commit does not attempt to hash or name
   itself.

Final-candidate control bytes are byte-identical to the two blobs in
`a60d2498754df641e9c8a3308d330f3c4e05fb74`, and the Python pins equal their
raw SHA-256 values. Historical V1.1 control provenance remains separately
preserved as `bd9e38c11e01bae18a5ffa0a6a0405a008273d27`.

## Semantic and provenance preservation

The ordered registry `semantic_checks` object was compared directly with the
authorized pre-lock baseline. It is deeply equal. Its canonical JSON SHA-256
before and after is:

`53f37c14b3e2b7da2e39ad9a27fe287b1b3a3f362aeca375a2adc02f28a74cff`

The only semantic-registry top-level value changed was `registry_status`.
Policy version, source contract, Phase-A decisions, required-drop counts,
protection flags, implementation keys, feature membership, and rationales are
unchanged.

Static constant comparison against the baseline also proved that all common
Python controls are unchanged except the three authorized current-provenance
values: locked-control commit, Markdown SHA-256, and registry SHA-256. In
particular:

- `GENERIC_RANK_DIRECT_DROP_AUTHORIZED = False`
- `GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN = False`
- BL-30, Cell 14, and Cell 8 provenance bindings are unchanged
- thresholds and tolerances are unchanged
- Final Test and target-blind boundaries are unchanged

## Execution-disabled and fail-closed proof

- Architecture v2.2 is byte-identical to the baseline and keeps policy status
  independent from execution status.
- `analyzer.py` is byte-identical to the baseline.
- The committed Python execution sentinel remains `PROVISIONAL`.
- `run_stage_b()` still calls `assert_stage_b_contract_locked()` as its first
  executable action; the committed sentinel makes that gate raise before any
  artifact I/O.
- Static AST inspection also proves the structural path still calls Phase A
  and ends in an unconditional `RuntimeError` at the unimplemented Phase B
  boundary. There is no Phase-B call, generic-rank-classifier call, or return
  path from `run_stage_b()`.
- No Phase B/C/D production execution was implemented or invoked.

Safety counters for this task:

| Counter | Value |
|---|---:|
| Final Test rows opened | `0` |
| Cell 8 assignment rows opened | `0` |
| Real Stage B production runs | `0` |

No labels, Validation outcomes, Final Test outcomes, P&L, future returns,
execution outcomes, or Cell 8 assignment rows were opened.

## Verification results

All commands used the current checkout explicitly via
`$env:PYTHONPATH=(Resolve-Path 'src').Path`; import sanity verified that
`contract.__file__` resolves inside this branch. This avoids a pre-existing
editable installation in a sibling worktree.

| Verification | Exact command or selection | Result | Exit |
|---|---|---|---:|
| Worktree diff integrity | `git diff --check` | Pass | `0` |
| Baseline-to-candidate diff integrity | `git diff --check e64c6d3602f747d24ebbfe57cfafc12beb2189fd..HEAD` | Pass | `0` |
| Compile | `python -m compileall -q src tests tools` | Pass | `0` |
| Import and disabled-gate sanity | checkout-local import; assert V1.2; assert Python sentinel `PROVISIONAL`; call only constitutional gate and require fail-closed | Pass | `0` |
| Critical Ruff | `python -m ruff check --select E9,F401,F63,F7,F82 src tests tools` | All checks passed | `0` |
| Lock controls | `python -m pytest -p no:cacheprovider tests/test_redundancy.py::StageBLockedControlTests` | `5 passed` | `0` |
| Direct constitutional gate | `python -m pytest -p no:cacheprovider tests/test_redundancy.py::StageBConstitutionalPolicyGateDirectTests` | `6 passed` | `0` |
| Project-root gate | `python -m pytest -p no:cacheprovider tests/test_redundancy.py::StageBProjectRootGateSpecificationTests` | `4 passed` | `0` |
| Focused Phase 0/A and generic firewall | seven checkout-safe CI classes | `63 passed` | `0` |
| Full checkout-safe redundancy | `pytest tests/test_redundancy.py` with the two documented external-fixture selections deselected | `161 passed, 15 deselected` | `0` |
| Other checkout-safe tests | `pytest tests/test_manifest.py tests/test_feature_builder.py tests/test_reference_freeze.py` | `26 passed, 1 skipped` | `0` |
| Archive/control/semantic/static proof | raw hashes, commit scopes, blob equality, semantic deep equality, constants, AST, unchanged analyzer/architecture | `STATIC_LOCK_PROOF=PASS` | `0` |

The focused seven-class selection was:

- `StageBPhase0FirewallSpecificationTests`
- `StageBPhase0FullOrchestrationSpecificationTests`
- `StageBPhase0ProductionOrchestrationSpecificationTests`
- `StageBPhaseASemanticIntegrationSpecificationTests`
- `StageBGenericRankAuthorityV12SpecificationTests`
- `StageBGroupRankAndPhaseCSensitivitySpecificationTests`
- `StageBProductionBoundarySpecificationTests`

Its command was `python -m pytest -p no:cacheprovider` followed by the seven
fully qualified `tests/test_redundancy.py::<class>` selections above. The full
checkout-safe command was `python -m pytest -p no:cacheprovider
tests/test_redundancy.py` with these exact deselections:

- `tests/test_redundancy.py::StageBCanonicalRegistryCompatibilitySpecificationTests::test_frozen_canonical_cell14_registry_is_accepted_without_metadata_rewrite`
- `tests/test_redundancy.py::StageBPhaseADecisionBridgeRedSpecificationTests`

The other checkout-safe command was `python -m pytest -p no:cacheprovider
tests/test_manifest.py tests/test_feature_builder.py
tests/test_reference_freeze.py`.

## Environmental exclusions — not passes

The external Cell 14 feature-registry artifact is absent from this checkout.
Accordingly, the following 15 tests were deselected and are not counted as
passes:

- one frozen canonical-registry compatibility test;
- all 14 tests in `StageBPhaseADecisionBridgeRedSpecificationTests`.

`tests/test_cell14_release.py` was not run because its complete ignored Cell 14
release artifacts are absent. This is not a pass. One
`tests/test_reference_freeze.py` test skipped because the optional local
large-artifact cache is absent; that skip is not a pass.

## Scope conclusion

The lock candidate contains only the authorized archival, status promotion,
hash/provenance pinning, mechanically required test alignment, progress update,
and this record. It does not change Quant methodology or production analyzer
logic. It does not merge itself, enable execution, or begin the next research
stage. Independent review remains mandatory.

## Final verdict

V1_2_LOCK_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW

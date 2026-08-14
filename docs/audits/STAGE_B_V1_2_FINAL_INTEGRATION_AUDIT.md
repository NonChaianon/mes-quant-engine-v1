# Stage B V1.2 final integration / contradiction / preservation audit

Audit date: `2026-08-15` (`Asia/Bangkok`)

Repository: `NonChaianon/mes-quant-engine-v1`

Issue: `#8 — Stage B V1.2 — ONE FINAL integration / contradiction / preservation audit`

Exact audited commit: `e64c6d3602f747d24ebbfe57cfafc12beb2189fd`

Substantive Issue #9 remediation merge: `e16bb5a432bcc98052b6a19167c396af0167ba86`

Audit mode: `STRICT_AUDIT_ONLY`

This is the resumed and final pass of the same Issue #8 audit. The audited
commit was both local `HEAD` and `origin/main` before this evidence-only report
was created. The only delta after the remediation merge was
`docs/architecture/ARCHITECTURE_PROGRESS.md`; no Quant logic or methodology
changed after the remediation.

No policy, production code, methodology, or threshold was changed by this
audit. No label, Validation outcome, Final Test data, or P&L was opened. This
report does not promote any control to `LOCKED_EXECUTABLE`, does not run Stage B
against real artifacts, and does not merge a lock action.

## 1. Scope and method

The audit cross-checked the integrated repository as one system, including:

- `docs/STAGE_B_REDUNDANCY_CONTRACT.md`
- `configs/v1/stage_b_semantic_registry_v1.json`
- `src/mes_quant/redundancy/contract.py`
- `src/mes_quant/redundancy/analyzer.py`
- `tests/test_redundancy.py`
- `.github/workflows/quant-ci-v1.yml`
- `docs/DEVELOPMENT_WORKFLOW.md`
- `docs/architecture/MES_QUANT_TARGET_ARCHITECTURE_v2.2.md`
- `docs/architecture/ARCHITECTURE_PROGRESS.md`
- the BL-30 summary and independent attestation
- the Issue #9 remediation report
- the Cell 14 release manifest and its frozen upstream controls

The review used raw-byte hashes, a baseline-to-current semantic-registry
comparison, source inspection, a recursive static call graph rooted at
`run_stage_b()`, synthetic checkout-safe tests, and the repository's CI-equivalent
test paths. No external/raw feature artifact was opened.

## 2. Load-bearing hashes

| File | SHA-256 at audited commit |
|---|---|
| `docs/STAGE_B_REDUNDANCY_CONTRACT.md` | `173afa7e26717795abb88eef1880af1ce8e3cecca133604840942fa8c6d12a96` |
| `configs/v1/stage_b_semantic_registry_v1.json` | `056ba7639960c8dd9c65d7e6a7a6a383e432a069651503def8bf05e3cafed861` |
| `src/mes_quant/redundancy/contract.py` | `4c4ac25b8703dbfa0ad4b068d366c7aa2abc986519fa5ed4a3d290fcd71fd8ed` |
| `src/mes_quant/redundancy/analyzer.py` | `01fe8edba02cf7269c9724c8b2455d5b4c19aec979ffc1f832dd4f84d9c0fa90` |
| `tests/test_redundancy.py` | `fbc8477ae5471a25db7240dec361f70ba52d81b1d456d0f3d33e9e529e3f23e5` |
| `.github/workflows/quant-ci-v1.yml` | `cbeea3fea663a39f65d7dffe872ed401f9bd3c3c5392bdacdaa88c9a5c404579` |
| `docs/DEVELOPMENT_WORKFLOW.md` | `86d7ebac700dd912f12fbc04343dbc5a4110b3d3ea87ee26ace9f04fccbb9125` |
| `docs/architecture/MES_QUANT_TARGET_ARCHITECTURE_v2.2.md` | `e2fcf97142bf340e8462003787dd6ec90dc4971444d492388ec2d07ec2271eaf` |
| `docs/architecture/ARCHITECTURE_PROGRESS.md` | `4aa97a918855462a4a68b6380e6fdad5da4b79a644d1386c84cce5eff4432a9e` |
| `docs/audits/BL30_GENESIS_REPRODUCTION_AUDIT_SUMMARY.md` | `254c3c41de789ea041e6e4619a5f6ac3d3771709c1945bbde43484014ac1a973` |
| `docs/audits/BL30_INDEPENDENT_ATTESTATION.md` | `bc5e35019c035fd28892a4cca87eae297f9fbd8916759003194bea0537ab23e7` |
| `docs/audits/STAGE_B_V1_2_LOCK_BREAKER_4_5_REMEDIATION.md` | `b74f835e010f16360662b7381e146e02463815af47cface29de023c1207c0e2f` |
| `manifests/releases/cell14_local_release_v1.json` | `74bd9d009cca43368488eea245b7b3b64918edc354091ba82172aaab6803a197` |
| `manifests/releases/frozen_colab_manifest_v1.json` | `6f174e27ef6ccff9ce53d233469a47b0b1d12cb1c3fd23c263585935cc6eb15f` |

The Markdown, semantic-registry, and Cell 14 release-manifest raw hashes equal
their Python pins. The three active Stage B control layers agree on
`MES_V1_REDUNDANCY_1.2 / PROVISIONAL` and the registry binds to the governing
Markdown path.

The `semantic_checks` array is semantically identical to baseline
`a5d3f40e7edc26d950010401654ce4d6b7822e86`; its canonical SHA-256 is
`53f37c14b3e2b7da2e39ad9a27fe287b1b3a3f362aeca375a2adc02f28a74cff`.
The Phase-A protected set remains exactly the six previously authorized
features.

## 3. Authority hierarchy and architecture alignment

The integrated authority hierarchy is coherent:

1. Architecture v2.2 supplies the accepted constitutional boundary.
2. The Markdown contract governs methodology, constraints, rationale, and
   interpretation.
3. The semantic registry is the executable authority for Phase-A semantic
   parameters.
4. The Python contract binds version, status, hashes, thresholds, and frozen
   controls.
5. The analyzer enforces those controls; tests validate but do not create
   policy.

Architecture v2.2 and the Stage B contract now encode the same frozen Phase-B
rule: generic exact-rank/SVD discovery never directly chooses a retained basis
or a feature to DROP. A stable localized unexplained dependency and a localized
cohort-conditional dependency both make every component member `OPEN`.
Unstable, unlocalizable, tolerance-inconsistent, or numerically inconsistent
evidence yields run-level `HARD_FAIL`.

The isolated classifier maps generic evidence only to whole-component OPEN or
run-level HARD_FAIL and blocks Stage-C release for either class. The feature-row
validator rejects generic KEEP/DROP, a selected basis, or a direct substitute;
the audit validator requires generic direct-DROP count zero; and the Stage-C
readiness gate rejects generic KEEP/DROP and blocks OPEN. HARD_FAIL releases no
feature-level BASE decision. Environment or BLAS changes cannot resolve OPEN or
authorize DROP.

Phase-A authority is preserved. The only rank-basis helper reachable from the
Phase-A resolver is guarded by both:

- `check_type = EXACT_AFFINE_DEPENDENCY`, and
- `decision_effect = DROP_ONE_DETERMINISTIC_REFERENCE_KEEP_FOUR_DIMENSIONS`.

The registry—not generic numerical discovery—therefore authorizes the weekday
reference reduction. No existing Phase-A semantic decision or protected feature
changed in Issue #9.

## 4. Mathematical preservation

The numerical definitions remain the frozen definitions:

- complete-case input is converted to finite `float64`;
- standardization uses per-column mean and standard deviation with `ddof=0`;
- SVD is computed once for the applicable matrix;
- `rank_tol = max(n_rows, n_features) * eps_float64 * sigma_max`;
- numerical rank counts singular values strictly greater than `rank_tol`;
- deficiency is `n_features - rank`;
- condition number is reporting-only and cannot independently DROP a feature.

Post-Phase-A rank deficiency requests generic discovery but does not select a
basis. The isolated generic classifier has only the frozen OPEN/HARD_FAIL
dispositions, returns an empty dropped-feature set, and blocks Stage-C release
for both classes.

Zero-variance handling remains separate at full-TRAIN and full-29 common-cohort
scopes. Only all-fold full-TRAIN zero variance may invoke the separately frozen
unprotected no-information rule; common-cohort-only degeneracy is diagnostic,
and semantic-basis protection takes precedence. Missing values are not imputed
or silently forward-filled.

All Phase-A semantic identities execute separately on TRAIN rows for the exact
three frozen expanding folds. Validation values do not determine semantic
outcomes, dependency direction, retained members, thresholds, or feature count.

A recursive directly resolvable static call graph rooted at `run_stage_b()`
found 27 reachable helpers. Registry-dispatched semantic implementations were
inspected separately. The generic classifier and legacy Cell 8 reconciliation
helper are not reachable. No reachable function contains a generic
`DROP_REDUNDANT` authority. The authoritative order remains:

`constitutional gate -> provenance/hash binding -> embedded-role validation -> Phase 0 -> Phase A -> unconditional fail-closed stop before Phase B`.

The remediation therefore preserves Phase-A mathematical outcomes and removes
the former generic `k-r` deletion obligation without introducing a replacement
selection rule.

## 5. Ground-set identity and provenance

The release manifest is raw-hash pinned and binds the authoritative inputs:

| Bound item | SHA-256 |
|---|---|
| Cell 14 Development feature artifact | `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452` |
| Cell 14 canonical content fingerprint | `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d` |
| Cell 14 feature registry | `7df68538d3e4a1447f1bca01396e3e141389decd196ba32faf04e34913107d95` |
| Cell 14 audit | `2adca2642c423ff634cb99de50f8fb5d0fc5f49d70188213021b9ee006ffdcd3` |
| Cell 8 assignments, provenance only | `2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035` |
| Cell 8 audit | `add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a` |

The runtime requires exactly 29 unique registry members and exact artifact
membership/order. A mismatch fails before analysis. It does not infer feature
identity from aliases or row position.

BL-30 remains internally consistent and was not rerun or reinterpreted. Its
accepted disposition is `EXACT_BYTES`; evidence SHA-256 is
`20f4e2150e5ad49ef4e75b576b4e9b859a6aa3979764f2f80bbbc70d76eca29a`,
and both clean scratch reproductions matched the frozen Cell 14 artifact. The
BL-30 control-source Git blobs remain unchanged at the audited commit.

## 6. Leakage and safety preservation

`run_stage_b()` is the sole artifact-reading entry point. It reads only the
hash-bound Cell 14 feature artifact, Cell 14 registry, Cell 14 audit, and Cell 8
audit. The full Cell 8 assignment artifact is path/hash bound but never opened;
fold authority is the frozen embedded Development-only projection in Cell 14.

The embedded projection rejects non-Development partitions, duplicate/null
decision IDs, null fold roles, a Cell 8 provenance mismatch, or any row at or
after the 2025 Final Test boundary. Phase 0 enforces the forbidden field/cell
firewall, and Phase A constructs every decision input through an explicit TRAIN
mask. Validation feature rows may contribute only to frozen Development
integrity/reconciliation facts; they do not select a target-blind decision.

Audit-activity counters:

| Counter | Observed |
|---|---:|
| Final Test rows opened | `0` |
| Cell 8 assignment rows opened | `0` |
| label/target/future-return/P&L/execution-outcome rows opened | `0` |
| real Stage B production runs | `0` |
| Phase B/C/D production implementations added | `0` |
| policy/methodology/production files modified by this audit | `0` |

## 7. Lock feasibility

One compliant implementation/run can satisfy all frozen V1.2 requirements
simultaneously:

- semantic Phase A has explicit registry authority;
- generic Phase B has discovery and OPEN/HARD_FAIL authority only;
- OPEN/HARD_FAIL prevents downstream release;
- no rule simultaneously requires generic direct deletion;
- ground-set and upstream identities are hash bound;
- target-blind and sealed-data boundaries are enforceable;
- while controls are provisional, execution stops at the first constitutional
  gate; after a separately authorized locked gate passes, the structural path
  executes Phase 0 and Phase A and then stops before Phase B, while later phases
  remain intentionally unimplemented.

The current controls correctly remain `PROVISIONAL`. The constitutional and
project-root tests construct an isolated future status-only promotion with
recomputed raw-byte pins and demonstrate that the three-layer
`LOCKED_EXECUTABLE` gate is mechanically satisfiable. This audit did not perform
that promotion.

## 8. Explicit V1_2_LOCK_BREAKER evaluation

| Breaker | Result | Minimal evidence |
|---|---|---|
| 1 — authoritative Phase-B mathematical result can be wrong | Not found | Frozen SVD/rank formulas agree across policy/runtime; generic deficiency is evidence-only and cannot select a member. |
| 2 — member identity can make Phase B analyze the wrong ground set | Not found | Raw-hash release binding plus exact 29-member membership/order checks fail closed on mismatch. |
| 3 — target, Validation, or Final-Test information can influence the target-blind result | Not found | Sole runtime path has no outcome inputs, uses TRAIN masks for decisions, opens zero Cell 8 assignment rows, and rejects Final Test rows. |
| 4 — KEEP/DROP/OPEN/HARD_FAIL can differ from the frozen methodology | Not found | Architecture, Markdown, constants, classifier, decision/audit validators, readiness gate, and tests encode the same whole-component OPEN/run-level HARD_FAIL mapping and zero generic direct drops. |
| 5 — two locked requirements cannot be satisfied by one implementation/run | Not found | The former generic OPEN-versus-`k-r` DROP contradiction is absent; the future status-only lock gate and the frozen execution order are jointly satisfiable. |

## 9. Verification evidence

Audit environment:

- Windows `10.0.26200`
- PowerShell `7.6.4`
- Python `3.12.10`
- pytest `8.4.2`
- NumPy `2.0.2`
- pandas `2.2.2`
- PyArrow `18.1.0`
- Ruff `0.16.2`
- Git `2.55.0.windows.3`

| Verification | Result | Exit code |
|---|---|---:|
| active imports plus policy/version sanity | PASS | `0` |
| `python -m compileall -q src tests tools` | PASS | `0` |
| critical Ruff `E9,F401,F63,F7,F82` | `All checks passed!` | `0` |
| direct constitutional + project-root gates | `10 passed` | `0` |
| checkout-safe Phase 0/A + generic authority + group-rank + production-boundary focused set | `63 passed` | `0` |
| checkout-safe full `tests/test_redundancy.py` | `161 passed, 15 deselected` | `0` |
| `test_manifest.py`, `test_feature_builder.py`, `test_reference_freeze.py` | `26 passed, 1 skipped` | `0` |
| raw-hash/pin, baseline semantic equality, release binding, and static reachability audit | PASS | `0` |
| `git diff --check` before report creation | PASS | `0` |

GitHub corroboration:

- Issue #9 remediation PR CI run `31823509663`: `success`.
- documentation-only progress PR CI run `31825233762`: `success`.

### Environmental exclusions

The ignored external Cell 14 release artifacts are absent from the clean
checkout. Accordingly, the canonical frozen-registry compatibility test and the
14-test `StageBPhaseADecisionBridgeRedSpecificationTests` class were explicitly
deselected, exactly as the checkout-safe CI workflow requires. These 15
exclusions are not counted as passes. `tests/test_cell14_release.py` was not run
because it requires the complete ignored Cell 14 release outputs. The one
repository-test skip reports: `Optional local large-artifact cache is absent`.

The absence is environmental and does not alter the frozen hashes, the accepted
BL-30 exact-byte evidence, or the fail-closed runtime boundary. Artifact-enabled
validation remains a prerequisite before any later real-data execution.

## 10. V1.3_BACKLOG

These observations do not meet any V1.2 lock-breaker definition and do not
change the frozen outcome:

1. Add the mechanical production adapter from the frozen registry's
   `feature_name` column to the analyzer's internal `feature` schema before any
   real run. The current mismatch fails closed; it cannot analyze a wrong member
   set.
2. When full Phase B is separately implemented, strengthen audit-payload
   validation by reconciling component disposition contents/counts and rejecting
   downstream release whenever the generic hard-fail count is nonzero.
3. Add the standard-deviation values requested by the zero-variance reporting
   contract to the future output payload; current counts/unique-value/zero flags
   preserve the decision rule but do not yet implement that output detail.
4. Archive the machine-readable BL-30 reproduction evidence alongside its
   independently accepted recorded hash when repository evidence-packaging work
   is next authorized.
5. Retire unreachable legacy pure helpers and historical V1.1 naming/comments
   when their surrounding implementation is next touched, without changing
   authority or methodology.

## Final verdict

SAFE_TO_LOCK_V1_2

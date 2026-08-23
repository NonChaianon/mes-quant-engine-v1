# Test 2 G3-F — Conditional-Fit Code-Only Contract V1

**Status:** `G3F_CODE_ONLY_PREPARED / G3F_EXECUTION_NOT_AUTHORIZED`

**Implementation owner:** Human Owner

**Patch preparation and adversarial review:** Codex + Claude Code

## 1. Authorization boundary

```text
authorized base                 7d66c43765c3a2c7f7acc772d8861490c70d6894
implementation branch           research/test2-g3f-code-only-v1
code-only gate                  G3F_CODE_ONLY_PREPARATION
future execution gate           G3F_CONDITIONAL_FIT (NOT_AUTHORIZED)
pinned G3-P run                 MES_T2_G3P_F39C31C0900A1D35
pinned G3-P semantic SHA-256     a6906cf0a1392c76065c3e98cee0f48ad431af0d043d4d65749b03644704e32e
real TRAIN rows read            0
real fold-fit calls             0
bootstrap replicates            0
economic diagnostics            0
Validation rows read            0
Final Test                      SEALED
```

This patch prepares only the positive authorization contract that a later
Owner-authorized runner would have to obey. It does not contain a runner, does
not lift `assert_g3f_not_authorized`, does not alter any fit/evaluation surface,
and cannot execute a model merely by being applied or tested.

## 2. Exact additive changed-file firewall

Exactly three files may differ from `7d66c43`:

1. `src/mes_quant/exploration/test2_g3f_contract.py`
2. `tests/test_test2_g3f_contract.py`
3. `docs/research/TEST2_G3F_PACKAGE_V1.md`

There are no modified files. In particular, `l1_lr001.py`, `l1_tree001.py`,
`test2_evaluation.py`, `test2_stats.py`, `test2_diagnostics.py`,
`test2_l1_harness.py`, `test2_g3_contract.py`, and `test2_g3_pre_fit.py` remain
byte-identical to `7d66c43`. The path, target, request-set, and 29-feature
contracts are also byte-pinned. Their SHA-256 identities are tested. Manifests,
configs, dependencies, Validation, Final Test, and all tools/runners remain
unchanged.

After a future G3-F commit, G3-P is not re-runnable on that branch: G3-P's own
changed-file firewall remains intentionally measured from `1792595` and must not
be weakened to accommodate G3-F.

## 3. Why a positive fit budget is required

The existing evaluator performs two fixed logistic fits inside each of the two
frozen folds. Without a positive budget, “four calls” is only an incidental
result of the current loop shape; a second evaluator invocation could spend four
more calls. The G3-P pre-fit guard correctly blocks every fit, bootstrap, and
economic diagnostic, but simply removing that guard would change zero authority
into unbounded authority.

G3-F therefore requires a minted, single-authorization `FoldFitBudget`. The
budget is not an optimization/search budget and exposes no hyperparameter knobs.
Its exact ordered cross-product is:

```text
1  PATHNUISANCE001 × WF_2022
2  PATHFULL001     × WF_2022
3  PATHNUISANCE001 × WF_2023
4  PATHFULL001     × WF_2023
```

Each pair must consume a permit before its fitter call and complete that permit
only after a converged outcome supplies the exact coefficient dimension and a
`beta_sha256`. Counters derive from completed outcomes, not merely issued
permits. Unknown models/folds, wrong order, a duplicate pair, a fifth call, a
permit from another budget, a permit without a completed outcome, an incomplete
seal, reuse after seal, or a second mint for the same Owner authorization
irreversibly poisons the budget. No passing record can be built from a poisoned
or incomplete budget. Record counters come from the sealed token; they are never
literals and never inferred from a synthetic/real context flag.

Process-local single minting is necessary but not sufficient. A later runner
must also require an immutable Owner authorization identity, exact clean
branch/upstream equality, an exact changed-file firewall, and create-once output
bound to that authorization. Those execution mechanics are deliberately absent
from this code-only patch.

## 4. Frozen science — no CLI knobs

The contract imports and witnesses, rather than redefines:

- models: `PATHNUISANCE001` with four frozen volatility/range features and
  `PATHFULL001` with the pinned 29-feature order;
- folds: `WF_2022`, `WF_2023`; `WF_2024` remains outer Validation;
- one barrier: tick `0.25`, take-profit `16` ticks (`4.00` points), stop `8`
  ticks (`2.00` points), 60 one-minute path offsets;
- strict MDE floors `0.0075` nats versus prior and nuisance;
- governing ESS floors `1,000` per fold and `2,000` pooled, effective class
  support floor `200` per fold;
- paired non-circular consecutive-session bootstrap: 2,000 repetitions,
  primary block length 5, diagnostic lengths 1 and 20, master seed `20260809`,
  pooled offset `90000`, fold stride `1000`;
- the existing frozen Test 1 Newton/logistic numerical policy.

No value above may be supplied through a command line or changed after observing
G3-P or later G3-F results. No tuning, seed search, third model, GBM, second
barrier, alternative fold, threshold selection, or result-driven repair is in
scope.

## 5. Pinned G3-P prerequisite

A future G3-F execution must bind the exact passing aggregate record. The fit
budget does not accept caller-declared hashes: it requires an opaque verified
binding token minted only after the record file's byte SHA, parsed aggregate
gates, strict zero counters, and recomputed semantic SHA all match:

```text
run_id       MES_T2_G3P_F39C31C0900A1D35
record SHA   a6906cf0a1392c76065c3e98cee0f48ad431af0d043d4d65749b03644704e32e
status       PASS
support      SUPPORT_GATE_PASS_FIT_NOT_AUTHORIZED
disposition  DEFERRED_PENDING_SEPARATE_G3F_AUTHORIZATION
```

The prerequisite record must retain zero real models/fold-fit calls, bootstrap
replicates, economic diagnostics, Validation reads, and Final-Test reads. The
G3-P file byte SHA is independently pinned as
`ce71ddf99e110e12b8469d91b9d2509ccd9f24c22ee4274217273b17ba31e28c`.

`INCONCLUSIVE_UNDERPOWERED` remains a terminal G3-P disposition and cannot mint
a G3-F budget. Because this package is bound to the exact passing G3-P support
record, a fitted G3-F record represents only a mechanically completed fit run
and therefore uses `PASS` plus one of the two frozen scientific dispositions:
`INTERESTING_ENOUGH_TO_CONTINUE` or `NOT_INTERESTING_ENOUGH`. A support mismatch
during a future G3-F run is an authorization/integrity failure: it stops before
or invalidates the run and writes no fitted-result record; it does not relabel
the already-passed G3-P support decision.

## 6. Separate G3-F aggregate record schema

G3-P's pre-fit closed-record schema must not be relaxed because G3-F must report
aggregate loss/improvement and confidence results that G3-P correctly forbids.
A future G3-F record may contain only aggregate/hash-level evidence, including:

- fold and pooled prior/nuisance/full log loss;
- fold and pooled improvement versus prior and nuisance;
- paired-bootstrap lower bounds, fixed seeds/block lengths, repetition count,
  and draw-identity SHA-256;
- ESS/design-effect and raw/effective class support;
- retained-set, source, role, authorization, and pooled-identity hashes;
- effective events per non-intercept coefficient and optimizer convergence
  summaries;
- coefficient dimension and `beta_sha256`, never coefficient values;
- the sealed fit-budget witness and zero Validation/Final counters;
- exact continuation failures/disposition.

Forbidden anywhere in the record are decision/session identities or times,
row IDs, per-row probabilities/losses/path values, decile cut points, raw fitted
coefficients, per-trade economics, or a trade ledger. The code-only contract
uses exact top-level and nested aggregate key allowlists, scalar metric checks,
strict integer counters, bounded fit/hash lists, and cross-binding between
authorization, completed outcomes, optimizer identities, and the sealed budget.
Unknown benign-looking keys are rejected. Output must later be create-once below
ignored `artifacts/exploration/test2/g3f/<run_id>/` and use a semantic
`record_sha256` that excludes its self-hash and volatile audit time.

## 7. Synthetic test gate

The code-only suite uses no real DBN/Parquet rows and performs no real fit,
bootstrap, or economic diagnostic. It proves:

1. exact identity/three-file allowlist and protected-surface byte hashes;
2. exact four-pair order, complete seal, and counters derived from consumption;
3. fail-closed behavior for wrong gate/hash/disposition, duplicate/unknown/extra
   pair, fifth call, cross-budget permit, incomplete seal, reuse, and in-process
   remint; cross-process reuse remains a create-once runner responsibility;
4. G3-P aggregate prerequisite binding;
5. G3-P byte/semantic file verification before minting a prerequisite token;
6. aggregate record acceptance plus rejection of row/coefficient leakage,
   benign-key blobs, incomplete primary evidence, and non-zero/weakly typed
   Validation/Final counters;
7. deterministic semantic hashing modulo audit time/self-hash;
8. frozen scientific constant witnesses;
9. the existing `assert_g3f_not_authorized` barrier and real-evaluation
   synthetic-context rejection remain active before any fitter call.

## 8. Exit gate for this patch

The patch is ready for Owner delivery only if:

- the exact three-file diff is additive-only from `7d66c43`;
- targeted synthetic tests and the complete existing suite pass;
- Ruff passes;
- protected-surface hashes match;
- source scans show no runner, artifact read, or direct fitter/bootstrap/economic
  call in either new Python file;
- Claude Code returns no BLOCKER/HIGH on the exact final diff;
- the Human Owner applies, tests, commits, and pushes the reviewed patch.

Passing this code-only gate does not authorize a G3-F execution, model fit,
bootstrap, economic diagnostic, Validation opening, Final Test, database work,
deployment, or broker connection. A later execution package and exact Owner
authorization remain mandatory.

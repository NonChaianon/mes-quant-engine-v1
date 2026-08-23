# Test 2 G3-F — Execution-Package Code-Only V1

**Status:** `PREPARED_FOR_OWNER_APPLY / REAL_EXECUTION_NOT_AUTHORIZED`

**Authorized base:** `d3d0455a4299f0dc881974029d457a4197ef321d`

**Expected branch:** `research/test2-g3f-execution-package-v1`

**Implementation owner:** Human Owner

**Preparation/review:** Codex + Claude Code

## Authorization boundary

This package prepares the exact execution mechanics required by the already
reviewed G3-F contract. Applying, testing, committing, or pushing it does not
authorize a real fit, bootstrap, economic diagnostic, Validation access, or
Final-Test access. Real execution requires a later separate Owner decision.

The immutable authorization document in this patch is a **code-only preparation
token**:
`docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md`, pinned by SHA-256 in
`test2_g3f_contract.py`. It cannot mint a fit budget.

The separate real-execution authorization path is
`docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md`. That document is
deliberately absent and its pinned hash is `None`, so the runner fails closed
before reading scientific artifacts. A later Owner-authorized activation patch
must add and pin that second document before any real execution is possible.

## Exact changed-file allowlist from `d3d0455`

1. `src/mes_quant/exploration/test2_evaluation.py` — bounded protected edit
2. `src/mes_quant/exploration/test2_g3f_contract.py`
3. `tests/test_test2_evaluation.py`
4. `tests/test_test2_g3f_contract.py`
5. `src/mes_quant/exploration/test2_g3f_execution.py` — new
6. `tests/test_test2_g3f_execution.py` — new
7. `tools/run_test2_g3f_conditional_fit.py` — new
8. `docs/research/TEST2_G3F_EXECUTION_PACKAGE_V1.md` — new
9. `docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md` — new

No dependency, manifest, configuration, feature, target, statistics,
diagnostics, numerical-policy, Validation, or Final-Test file may change.

## Bounded evaluator observation hook

The evaluator remains the single implementation of the frozen scientific
logic. A real non-fixture run must supply a fold-fit authority; omission raises
before fitting. Synthetic evaluation remains available without a real budget.

At each existing fitter call site the evaluator:

1. sends `(model_id, fold_id)` to `consume()` before the fitter runs;
2. keeps the raw fitted `beta` local;
3. hashes model ID, fold ID, coefficient dimension, and canonical little-endian
   coefficient bytes inside the evaluator;
4. sends only `beta_sha256`, dimension, and convergence status to
   `complete_fit()`;
5. propagates every authority exception and terminates the run.

There is no monkeypatch, call-order inference, second evaluator, or coefficient
export. The four-fit budget remains exactly nuisance/full × WF_2022/WF_2023.

## Runner preconditions

Before any artifact read or fit, the future runner must verify:

- exact gate literal `G3F_CONDITIONAL_FIT`;
- current branch and descendant relationship from `d3d0455`;
- fully clean worktree, including untracked non-ignored files, and
  `HEAD == upstream`;
- exact nine-file changed-file allowlist;
- every protected-surface SHA-256, including the explicitly re-pinned evaluator;
- the byte-pinned code-only preparation document; and
- a distinct byte-pinned real-execution authorization document, which this
  package intentionally does not contain;
- the exact byte and semantic identities of the passing G3-P record.

The runner then reconstructs the canonical TRAIN-only evidence and context,
mints one budget, invokes the evaluator once, seals exactly four completed
outcomes, and writes a create-once aggregate record. G3-P remains non-rerunnable
on this branch; its pushed `7d66c43` branch remains the rerun anchor and its
firewall is not weakened.

## Record boundary

The G3-F artifact contains only aggregate metrics, support, bootstrap hashes,
optimizer convergence summaries, coefficient hashes, authorization/G3-P
bindings, and zero Validation/Final counters. It never serializes raw
coefficients, row IDs, decision/session identities, probabilities, per-row
losses, paths, trades, or the evaluator's economic ledger.

After a future real authorization is verified and TRAIN-only pre-fit evidence
passes, the runner derives the run ID and atomically reserves its create-once
directory **before** minting a budget or calling a fitter. The reservation is
not removed after failure, so the same authorized identity cannot spend fits a
second time. A record is written only after the evaluator counters, real run
context, sealed fit budget, aggregate schema, and semantic record hash all
cross-bind.

## Code-only verification

All preparation tests use synthetic/in-memory objects or mocks. They must prove:

- real evaluation without an authority stops before fitter access;
- the hook observes the exact four pairs and never exports `beta`;
- authority errors propagate and stop the run;
- a synthetic or fixture witness cannot produce a real record;
- evaluator and budget counters cross-bind;
- aggregate-only validation and create-once output fail closed;
- targeted tests, full pytest, changed-file Ruff, allowlist, protected hashes,
  and a source firewall pass;
- Claude Code reports no BLOCKER/HIGH on the exact final diff.

Passing these checks authorizes nothing to execute.

# Test 2 G3-F — One-Shot TRAIN-Only Execution Package V1

**Status:** `OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY / ACTIVATION_CODE_ONLY`

**Activation branch point:** `52e652d2671001729bb6f4ebcba37fb1f6b5086a`

**Changed-file firewall base:** `d3d0455a4299f0dc881974029d457a4197ef321d`

**Expected branch:** `research/test2-g3f-real-execution-v1`

**Implementation owner:** Human Owner

**Preparation/review:** Codex + Claude Code

## Authorization boundary

This activation patch implements the Owner's separate one-shot authorization.
Applying, testing, committing, and pushing the patch still do not themselves
execute a fit. Only the Human Owner may invoke the runner after exact local and
upstream equality. The authorization covers at most four frozen TRAIN fold fits,
the frozen bootstrap set, and one aggregate economic-diagnostic call. It does
not authorize Validation or Final-Test access.

The immutable authorization document in this patch is a **code-only preparation
token**:
`docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md`, pinned by SHA-256 in
`test2_g3f_contract.py`. It cannot mint a fit budget.

The separate real-execution authorization is
`docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md`. That document is
present, byte-pinned, status-pinned, and mechanically single-use. Its exact
status is `OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY`.

## Exact changed-file allowlist from `d3d0455`

1. `src/mes_quant/exploration/test2_evaluation.py` — bounded protected edit
2. `src/mes_quant/exploration/test2_g3f_contract.py`
3. `tests/test_test2_evaluation.py`
4. `tests/test_test2_g3f_contract.py`
5. `src/mes_quant/exploration/test2_g3f_execution.py` — new
6. `tests/test_test2_g3f_execution.py` — new
7. `tools/run_test2_g3f_conditional_fit.py` — new
8. `docs/research/TEST2_G3F_EXECUTION_PACKAGE_V1.md` — new
9. `docs/research/TEST2_G3F_OWNER_AUTHORIZATION_V1.md` — code-only token
10. `docs/research/TEST2_G3F_REAL_EXECUTION_AUTHORIZATION_V1.md` — one-shot token

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

Before any artifact read or fit, the runner must verify:

- exact gate literal `G3F_CONDITIONAL_FIT`;
- current branch and descendant relationship from `d3d0455`;
- fully clean worktree, including untracked non-ignored files, and
  `HEAD == upstream`;
- exact ten-file cumulative changed-file allowlist from `d3d0455`;
- every protected-surface SHA-256, including the explicitly re-pinned evaluator;
- the byte-pinned code-only preparation document; and
- the distinct byte- and status-pinned real-execution authorization document;
- the exact byte and semantic identities of the passing G3-P record.

The runner then reconstructs the canonical TRAIN-only evidence and context,
consumes the authorization through an exclusive-create sentinel, reserves the
run, mints one budget, invokes the evaluator once, seals exactly four completed
outcomes, and writes a create-once aggregate record. A post-sentinel failure
consumes the authorization and must never be retried. G3-P remains non-rerunnable
on this branch; its pushed `7d66c43` branch remains the rerun anchor and its
firewall is not weakened.

## Record boundary

The G3-F artifact contains only aggregate metrics, support, all predeclared
bootstrap lower bounds and hashes,
optimizer convergence summaries, coefficient hashes, authorization/G3-P
bindings, aggregate economic counts/net/per-fold/dispersion witnesses, hashes
of omitted ordered ledgers, and zero Validation/Final counters. It never serializes raw
coefficients, row IDs, decision/session identities, probabilities, per-row
losses, paths, trades, or the evaluator's economic ledger.

After authorization and TRAIN-only pre-fit evidence pass, the runner creates
and durably syncs a sentinel keyed only by authorization SHA-256 **before**
reservation, budget minting, or fitting. The sentinel is a local mechanical
stop, not an adversary-proof claim. Immediately after success or post-sentinel
failure, the Owner must force-add the sentinel, reservation, aggregate record,
and a whitelisted success witness or scrubbed failure summary into a Git
evidence commit. Raw logs are forbidden.

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

Passing these checks prepares the activation commit only. Real execution remains
a separate, explicit Human Owner command after that commit is pushed and exact
local/upstream equality is observed.

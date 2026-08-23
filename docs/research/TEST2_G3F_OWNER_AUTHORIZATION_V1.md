# Test 2 G3-F Execution-Package Code-Only Owner Authorization V1

**Owner decision date:** 2026-08-23

**Authorized base:** `d3d0455a4299f0dc881974029d457a4197ef321d`

**Implementation owner:** Human Owner

**Preparation/review:** Codex + Claude Code

The Owner authorizes preparation and adversarial review of a bounded G3-F
execution-package **code-only** patch from the exact base above.

The patch may make a bounded change to the protected file
`src/mes_quant/exploration/test2_evaluation.py` solely to add an explicit
`FoldFitBudget` observation boundary. For every real non-fixture fit, the
evaluator must expose `(model_id, fold_id)` to the authority before the fitter
call and only `beta_sha256`, coefficient dimension, and convergence status
afterward. Raw fitted coefficients must never leave the evaluator through this
boundary. Any authority failure must raise and terminate the complete run.
Real non-fixture evaluation without an authority must fail before fitting;
synthetic evaluation remains outside the real-fit budget.

The patch may re-pin the exact changed-file allowlist and protected-surface
hashes from `d3d0455`, and may add a runner, synthetic tests, package documents,
and a thin tool entry point. Future runner code may wire the already-frozen
bootstrap and economic-diagnostic paths, but this authorization does not permit
executing them.

The Owner explicitly accepts that `test2_evaluation.py` will no longer be
byte-identical to `7d66c43` on the new execution-package branch and that G3-P
must not be re-run there. The pushed branch at `7d66c43` remains the immutable
G3-P rerun anchor; its firewall must not be weakened.

Forbidden during preparation, testing, and review:

- real model fit or real fold-fit call;
- bootstrap execution on real data;
- economic-diagnostic execution on real data;
- Validation or Final-Test access;
- monkeypatching or duplicating the evaluator;
- changing model definitions, feature sets, folds, barriers, seeds, MDEs,
  support floors, numerical policy, or search budget;
- tuning, a third model, a new dependency, database work, deployment, or broker
  connectivity.

The Human Owner will apply, test, commit, and push the reviewed patch. A later
real G3-F execution requires a separate exact Owner authorization after the
code-only patch passes all tests, firewalls, and adversarial review.

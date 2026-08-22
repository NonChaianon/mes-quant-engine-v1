# Test 2 G0 — Forward Remediation Record V1

**Status:** `IMPLEMENTED_IN_CANDIDATE / NO_L1_EXECUTION`

**Base commit:** `29d95a97814c60413b0b13cfee61155b43552ba9`

**Scope:** forward remediation required by Section 2 of
`TEST2_PATH_AWARE_PROTOCOL_V1.md`. This record does not rewrite Test 1 evidence and does
not authorize TRAIN target/path access.

## Test 1 disposition remains unchanged

The two Test 1 candidates failed on the deciding primary metric, binary log loss. The
known diagnostic defects below neither convert those failures into passes nor invalidate
the primary result.

## G0-1 — trapezoidal PR-AUC

The shared historical helper `l1_lr001._pr_auc` integrates a precision-recall curve with
the trapezoidal rule. That diagnostic can overstate ranking quality when a model emits a
small number of distinct scores.

Forward resolution for Test 2:

- Test 2 never invokes `_pr_auc`;
- Test 2 uses its own tie-safe, stepwise average-precision implementation;
- synthetic tests distinguish the stepwise result from trapezoidal integration and cover
  tied scores, no positives, and invalid inputs;
- the historical Test 1 implementation and experiment identities remain byte-unchanged;
- repair of the shared historical helper is a separate maintenance item and may not be
  back-propagated into old experiment records.

## G0-2 — stale L0 harness status beside observed L1 access

The Test 1 record builder inherited `DRY_RUN_ONLY_L0` even after an accepted runner had
observed TRAIN labels. The field therefore described the original harness rather than the
observed run.

Forward resolution for Test 2:

- every Test 2 evaluation receives an explicit validated run context;
- synthetic context can record only L0, zero real rows, zero real fits, and no L1 token;
- a real context requires L1 status, an authorization-record hash, verified source
  identities, a sealed request-set hash, positive TRAIN path access, the point-in-time
  feature assertion, and zero Validation/Final-Test access;
- records derive access, source, counter, and fit fields from that context rather than
  from a hard-coded L0 constant;
- contradictory synthetic/L1 combinations fail before a record can be emitted.

## G0-3 — forward gate

This remediation is satisfied for Test 2 only when the G1 tests and full existing suite
remain green and an independent Claude review reports no blocker/high. It creates no
authority to rerun Test 1, open real Test 2 data, modify a barrier, or fit a model.

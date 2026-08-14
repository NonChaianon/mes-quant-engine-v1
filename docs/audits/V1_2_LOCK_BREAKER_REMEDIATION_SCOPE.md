# Stage B V1.2 — Lock-Breaker Remediation Scope

This file records the bounded remediation scope for the lock-breaker discovered by the final V1.2 integration audit.

Authorized change only:

- remove generic Phase-B automatic exact-rank deletion authority from the V1.1 contract/test expectations;
- align contract/tests/implementation boundary with the frozen V1.2 rule that generic SVD/rank discovery never directly drops a feature;
- stable localized unexplained exact dependency => OPEN the entire component;
- unstable/unlocalizable/numerically inconsistent evidence => HARD FAIL;
- Phase A semantic authority remains unchanged and may still direct KEEP/DROP where the locked semantic registry proves direction;
- no label, Validation, Final Test, P&L, cost outcome, or future-return access;
- no Phase C/D implementation;
- no methodology additions beyond the already-frozen V1.2 architecture.

After remediation, resume Issue #8 as continuation of the same final audit. Do not treat the remediation as authorization for a new design/audit cycle.

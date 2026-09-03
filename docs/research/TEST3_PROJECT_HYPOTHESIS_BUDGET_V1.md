# Test 3 Project-Level Hypothesis Budget V1

Budget ID: `MES_PROJECT_TARGET_SPACE_BUDGET_V1`

Status: **DRAFT COMPLETE — OWNER CO-RATIFICATION REQUIRED**

Companion protocol: `MES_TEST3_RV60_HAR_RISK_EDGE_V1`

Base commit: `fe10fb1497e5df919702cf4ff294c4ebf8669b95`

This artifact preserves the project-level search commitment separately from the Test 3
model and statistical contract. It does not authorize code, data access, target
construction, fitting, Validation, Final Test, or live execution.

## 1. Target-space search ledger

| Slot | Governed target-space question | Terminal history / state |
| --- | --- | --- |
| `TARGET_SPACE_001` | Test 1 endpoint directional/economic classification | completed; LR001/TREE001 continuation failed; model-family budget spent |
| `TARGET_SPACE_002` | Test 2 first-touch path-aware `LONG/FLAT` classification | completed at `c6e0281`; `NOT_INTERESTING_ENOUGH`; no retry |
| `TARGET_SPACE_003` | Test 3 next-60-minute realized-variance Risk Edge | draft-introduction commit `531f0ee`; amended candidate reserved pending co-ratification |

These slots record changes in the scientific target, not individual algorithms inside a
target. The model-fit budget inside Test 3 remains the stricter four-fit contract in the
companion protocol.

## 2. Final OHLCV-only target commitment

`TARGET_SPACE_003` is the third and final target-space hypothesis whose evidentiary inputs
are limited to the existing governed OHLCV lineage and deterministic calendar metadata.
After co-ratification:

- no competing Test 3 target, horizon, sampling rule, or label may be drafted as a rescue;
- no `TARGET_SPACE_004` using only the same OHLCV/calendar evidence may be opened after the
  Test 3 result;
- a Test 3 pass may advance the same frozen target to a separately authorized confirmatory
  protocol; this is confirmation, not a new target-space slot;
- the current Test 4 concept may proceed only if Test 3 has a winner, retains the same
  target, and receives its own feature/model budget; it creates no new target entitlement;
- a scientifically new post-Test-3 direction must either introduce a genuinely new,
  governed evidence class under a new Owner decision or stop the search. It may not rename
  an OHLCV-only rescue as a new research pillar.

This budget limits **hypothesis search**, not downstream **application**. After a Test 3
pass and the required confirmation, separately authorized integration of the same frozen
target/model into governed B8/B9, risk-control, or UI research artifacts does not consume
or open a target-space slot. This accounting statement grants no downstream authority.

## 3. Reservation and consumption

Co-ratification changes `TARGET_SPACE_003` from `DRAFT` to `LOCKED / RESERVED`. The slot is
irreversibly `CONSUMED` when any authorized execution first reads a numeric target value or
constructs `RV_FWD_60`, regardless of whether fitting later occurs or the run stops before
fit.

The target-blind G2-P predictor-domain preflight in the companion protocol does not consume
the slot because it reads no target/path value. If it ends with any whole-run
`INVALID_EVIDENCE`, including `PREDICTOR_NONFINITE`, `PREDICTOR_NONPOSITIVE`, or a
source/ledger mismatch, the slot remains `LOCKED / RESERVED` while the cause is audited and
any change still requires an Owner-ratified amendment before target access. If the observed
source/data state is genuine rather than implementation nonconformance, the slot becomes
`CLOSED_UNCONSUMED`; Test 3 has no successor or replacement target.

Abandoning Test 3 before any G2-P numeric predictor read or target-aware access does not
silently release the slot. Any administrative cancellation requires an explicit
Owner-ratified amendment before that access and creates no new post-Test-3 OHLCV-only search
entitlement. Except for the sole defect-repair carve-out below, a `CLOSED_UNCONSUMED` or
`CONSUMED` slot cannot be released, retried, replaced, or exchanged.

There is exactly one defect-repair carve-out and it permits at most one successor execution.
If an authorized stage terminates before any fit permit/call, forecast, coefficient, QLIKE
result, or bootstrap replicate, the Owner may ratify a successor protocol on the **same
target within `TARGET_SPACE_003`** only after synthetic evidence proves that the
implementation failed to conform to the frozen protocol. The observed source or real-data
state alone is not defect evidence. The successor must retain the identical source lineage,
target and horizon, predictor set, harmonic, folds, transform/back-transform,
common-eligibility and row-status/reason-code dispositions, `RVBASE001`/`RVHAR001` model
pair, four-fit budget, QLIKE contract, bootstrap contract including seed, repetitions, block
lengths and sidedness, numerical policy, dependence-audit/ESS contract, and continuation
gates. It may amend only the minimum implementation handling causally required to restore
conformance; every scientific choice remains frozen, and this path is never a model,
predictor, metric, or row-selection rescue.

A genuine source/data state that triggers whole-run `INVALID_EVIDENCE` is terminal and has
no successor, including zero variance, nonfinite, nonpositive, or mismatch. Non-terminal
`TARGET_UNUSABLE` and `PREDICTOR_UNUSABLE` retain only their frozen common-mask treatment.
The defect-repair carve-out is not an automatic retry: the original ledgers remain immutable,
the anomaly and access are disclosed, and new exact authorization is mandatory. If target
access already occurred, the slot remains `CONSUMED`; otherwise a proven implementation
defect leaves it `LOCKED / RESERVED` only for the single authorized repair lineage. That
lineage never permits release, exchange, a new target, or a new search slot. If its successor
execution fails for any reason, Test 3 is terminal.

For project-level slot consumption, reuse, and successor eligibility, this budget takes
precedence over the companion protocol. The protocol governs mechanics inside an authorized
run. Its phrase "without a new Owner-ratified protocol" cannot override the no-new-slot
rule; only the explicit defect-repair carve-out above permits same-slot continuation.

## 4. Relationship to Test 4 and Validation

This budget does not authorize Test 4 or outer Validation. If Test 3 fails its TRAIN gate,
the currently conceived Test 4 is void. If Test 3 passes, any confirmatory Validation or
same-target Test 4 proposal remains a separate decision with its own exact protocol and
budget. Final Test remains sealed until all prior gates independently authorize it.

## 5. Co-ratification rule

The Owner must ratify this artifact and
`TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md` together against the same exact commit. A
ratification of only one is incomplete and grants no implementation or access authority.

`fe10fb1` is the repository base and `531f0ee` is only the first Git commit that introduced
the Test 3 draft. Because a tracked file cannot self-reference the commit that contains its
own final bytes, the separate Owner ratification record must pin the exact co-ratified
commit containing both artifacts; that ratification identity governs later execution.

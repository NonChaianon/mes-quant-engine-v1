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
| `TARGET_SPACE_003` | Test 3 next-60-minute realized-variance Risk Edge | draft established at `531f0ee`; amended candidate reserved pending co-ratification |

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

## 3. Reservation and consumption

Co-ratification changes `TARGET_SPACE_003` from `DRAFT` to `LOCKED / RESERVED`. The slot is
irreversibly `CONSUMED` when any authorized execution first reads a numeric target value or
constructs `RV_FWD_60`, regardless of whether fitting later occurs or the run stops before
fit.

Abandoning Test 3 before target-aware access does not silently release the slot. Any release
or replacement requires an explicit Owner-ratified amendment to this artifact before data
access. Once consumed, the slot cannot be released, retried, or exchanged.

## 4. Relationship to Test 4 and Validation

This budget does not authorize Test 4 or outer Validation. If Test 3 fails its TRAIN gate,
the currently conceived Test 4 is void. If Test 3 passes, any confirmatory Validation or
same-target Test 4 proposal remains a separate decision with its own exact protocol and
budget. Final Test remains sealed until all prior gates independently authorize it.

## 5. Co-ratification rule

The Owner must ratify this artifact and
`TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md` together against the same exact commit. A
ratification of only one is incomplete and grants no implementation or access authority.

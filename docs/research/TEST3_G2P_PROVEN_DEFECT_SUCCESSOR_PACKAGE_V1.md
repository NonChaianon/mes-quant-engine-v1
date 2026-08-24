# Test 3 G2-P Proven-Defect Successor Package V1

Package ID: `MES_TEST3_G2P_PROVEN_DEFECT_SUCCESSOR_PACKAGE_V1`

Repair-lineage ID: `MES_TEST3_G2P_SINGLE_PROVEN_DEFECT_REPAIR_V1`

Authorization: `AUTH_TEST3_G2P_SINGLE_PROVEN_DEFECT_SUCCESSOR_20260824`

Status: `OWNER AUTHORIZED / CODE-ONLY PACKAGE PENDING REVIEW AND ONE-SHOT`

Exact base: `2d4fccf4ac2040e8e908bfadda27b81b3663afad`

Branch: `research/test3-g2p-proven-defect-successor-v1`

## 1. Purpose

This package implements the one permitted same-slot successor after synthetic proof showed
that predecessor G2-P rejected the canonical internal pipe in `decision_id` even though the
frozen L0/protocol identity contract accepts it. The package does not alter any scientific
surface and does not retry the consumed predecessor authorization.

## 2. Exact change

`_normalized_identity` continues to require a non-empty string and continues to reject CR
and LF. It no longer rejects `|`. The identity is returned unchanged. No hash payload,
projection ID, row ordering, time/status serialization, predictor classification, common
eligibility, source binding, counter, target, model, metric, bootstrap, or continuation rule
changes.

The synthetic repair test must prove all of the following:

- predecessor `485bfa1` rejects `SYNTH|ID` with the committed failure category;
- frozen L0 accepts and hashes `SYNTH|ID`;
- successor accepts the same identity byte-for-byte;
- successor ordered identity/status hashes equal frozen L0 for pipe-containing identities;
- CR and LF still fail closed;
- hash projection and serialization constants are unchanged.

## 3. Additive evidence and ancestry

The additive proof/amendment and its machine test live in parent commit `2d4fccf`. The
execution commit must be its single direct child and change exactly the four files listed in
the authorization. Original protocol/budget/L0, predecessor authorization/package,
reservation/failure evidence, proof files, and thin runner remain unchanged.

Before successor consumption, the runtime verifies the exact predecessor package/evidence
commits, trees, files, hashes, semantic failure category, protected zeros, and unopened/sealed
boundaries. Those bindings are emitted into the successor aggregate record.

## 4. Mechanical one-successor firewall

The successor uses the fixed repair-lineage reservation path rather than an authorization-
hash-specific retry path. Exclusive creation occurs before artifact opening and records
ordinal one of limit one. A second attempt or alternate token collides with the same file
before predictor access. The predecessor reservation/failure paths are never reused.

## 5. Verification before execution

Required package gates are:

1. exact proof-parent ancestry and exact four-file diff;
2. clean tracked tree and no untracked/ignored import surface;
3. exact pushed upstream equality;
4. all document/proof/predecessor evidence hashes;
5. targeted predecessor-proof and G2-P tests;
6. full existing pytest suite and changed-file Ruff;
7. source/reader/protected-surface firewalls;
8. independent Claude Opus exact-package GO.

Only after all eight pass may the exact command in the successor authorization execute once.

## 6. Outcome boundary

On pass, the aggregate record remains target-blind and opens no later authority. On any
failure, the fixed lineage is spent and Test 3 is terminal. The record/failure summary must
never contain predictor values or per-row identities. Raw logs remain local. Reservation
plus aggregate record or typed failure are committed and pushed in a separate evidence
commit without merge.

Typed invalid-evidence failures retain their exact protocol category and boundary
attestations. A generic runtime or infrastructure failure is instead recorded as
`EXECUTION_FAILURE` with non-invariant access counters and Validation/Final access status
explicitly not attested; it must never be mislabeled as scientific `INVALID_EVIDENCE` or
invent exposure zeroes. Either failure class spends the fixed lineage and permits no retry.

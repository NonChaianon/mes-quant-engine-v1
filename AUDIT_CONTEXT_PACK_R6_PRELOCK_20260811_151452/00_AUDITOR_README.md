# MES Quant Engine ? Auditor Context Pack

## Purpose

This folder is a read-only audit-context snapshot for reviewing new
MES Quant Engine code against the project's existing methodology and
controls.

It does not create new methodology.

## Authority hierarchy

### 1. Governing human-readable policy

`docs/STAGE_B_REDUNDANCY_CONTRACT.md`

The Markdown contract governs:

- research methodology
- constraints
- rationale
- interpretation
- Stage B sequencing and audit requirements

### 2. Machine-readable semantic policy

`configs/v1/stage_b_semantic_registry_v1.json`

The semantic registry is authoritative for executable semantic-check
parameters, subject to successful Markdown <-> JSON consistency audit
and formal lock.

### 3. Canonical upstream definitions/evidence

The Cell 14 feature registry and upstream control/audit artifacts define
canonical feature identity, metadata, fold/data controls, and factual
evidence where supplied.

They must not be silently rewritten by Stage B code.

### 4. Implementation

Files such as:

- `contract.py`
- `analyzer.py`
- `tests/test_redundancy.py`

are implementation or enforcement artifacts.

They are NOT competing methodology authorities.

If implementation conflicts with governing policy, flag the implementation.

### 5. Audit evidence

Diffs, hashes, manifests, and factual audit artifacts are evidence.

They do not create policy.

## Auditor rules

Audit new code for compliance with supplied governing contracts and
registries.

Do NOT:

- redesign methodology merely because different code seems convenient
- relax locked/provisional controls
- infer missing policy from implementation code
- use tests as a third policy authority
- open or use Final Test 2025-2026
- use labels, future return, P&L, or cost outcomes during target-blind Stage B
- revive explicitly rejected procedures

If governing documents themselves are inconsistent, report the
inconsistency rather than guessing which behavior was intended.

Status semantics must remain distinct:

- LOCKED
- PROVISIONAL
- OPEN
- REJECTED

This pack is PRE-LOCK unless the governing files explicitly state otherwise.

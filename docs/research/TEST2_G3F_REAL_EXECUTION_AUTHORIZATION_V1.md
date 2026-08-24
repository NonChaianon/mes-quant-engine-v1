# Test 2 G3-F Real-Execution Owner Authorization V1

**Owner decision date:** 2026-08-23

**Execution status:** `OWNER_AUTHORIZED_ONE_SHOT_TRAIN_ONLY`

**Activation branch point:** `52e652d2671001729bb6f4ebcba37fb1f6b5086a`

**Changed-file firewall base:** `d3d0455a4299f0dc881974029d457a4197ef321d`

**Expected activation/execution branch:** `research/test2-g3f-real-execution-v1`

**Implementation and execution owner:** Human Owner

**Preparation/review:** Codex + Claude Code

## Authorized operation

The Owner authorizes a bounded code-only activation patch from the exact branch
point above, followed only after review, tests, commit, push, and local/upstream
equality by one G3-F conditional run over the frozen TRAIN-only artifacts.

The run is limited to the already-frozen one barrier set, the model definitions
`PATHNUISANCE001` and `PATHFULL001`, and folds `WF_2022` and `WF_2023`: at most
four real fold-fit calls in the frozen order. It must perform the already-frozen
paired bootstrap set and aggregate economic diagnostics without tuning or a
second run.

This document explicitly authorizes the activation patch to:

- pin this document's exact byte SHA-256 and the active execution status;
- change the expected branch to the activation branch above;
- expand the cumulative changed-file firewall from nine to exactly ten paths
  by adding only this authorization document;
- add a second bounded observation to protected `test2_evaluation.py` that
  counts the actual `build_economic_diagnostics` entry-point invocation without
  changing its inputs, outputs, formulas, policies, or call order;
- project only aggregate economic witnesses and diagnostic bootstrap lower
  bounds into the sealed G3-F record while omitting every trade/row identity;
- add an authorization-SHA-scoped create-once consumption sentinel before any
  fit and bind the record to the verifier-minted authorization token;
- re-pin the exact evaluator, runner, thin tool, and both G3-F test files after
  these bounded changes; and
- update the existing package document and synthetic/code-only tests required
  to prove the activation boundary.

## Frozen artifact and prerequisite bindings

| Binding | Exact identity |
| --- | --- |
| G3-P run ID | `MES_T2_G3P_F39C31C0900A1D35` |
| G3-P semantic record SHA-256 | `a6906cf0a1392c76065c3e98cee0f48ad431af0d043d4d65749b03644704e32e` |
| G3-P file SHA-256 | `ce71ddf99e110e12b8469d91b9d2509ccd9f24c22ee4274217273b17ba31e28c` |
| Raw DBN SHA-256 | `49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0` |
| Cell 8 SHA-256 | `2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035` |
| Cell 10 SHA-256 | `1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0` |
| Cell 12 SHA-256 | `8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941` |
| Cell 14 SHA-256 | `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452` |
| Cell 14 run ID | `cell14_20260809T175203Z` |

All prerequisite, manifest, source-role, request-set, retained-set, support, and
protected-surface checks in the reviewed runner remain mandatory and fail
closed.

## Single-use and evidence boundary

The authorization sentinel must be created with exclusive create and durable
file/parent-directory sync after all cheap deterministic pre-fit checks but
strictly before reservation, budget minting, or fitting. Its identity depends
only on this document's SHA-256, not on the code commit.

The Owner accepts that any failure after sentinel creation consumes this
authorization. It must never be retried. Recovery requires a new authorization
document, branch, patch, and adversarial review.

The sentinel is a mechanical local stop while the contract bytes remain
unchanged; it is not claimed to resist an adversarial rewrite of the contract.
Immediately after the run or a post-sentinel failure, the Owner must force-add
the sentinel, a whitelisted success witness or scrubbed failure summary, and
any reservation/aggregate record into a post-run evidence commit and push it.
Raw execution logs must never be committed. The resulting unexpected evidence
paths are the durable Git changed-file-firewall tripwire against reuse.

## Forbidden

- any fifth fold-fit call, second invocation, retry, tuning, third model, new
  barrier, changed seed, or changed numerical/scientific policy;
- Validation or Final-Test access;
- raw coefficient, probability, trade ledger, decision/session identity,
  per-row loss, path, or target serialization in the aggregate record;
- an unfiltered execution log in Git;
- new dependency, database work, deployment, broker connectivity, live trading,
  or execution enablement beyond this research run; and
- merge, reuse, or promotion of retired LangGraph artifacts.

Passing G3-F does not authorize Validation. A positive result can only open a
separate Owner decision to prepare a confirmatory/Validation protocol. A
negative result closes this Test 2 path without opening Validation.

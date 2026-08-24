# Test 2 Repository Closeout V1

**Date:** 2026-08-24

**Status:** `COMPLETE / MERGED / QUEUE RECONCILED`

**Authority created by this document:** `NONE`

## Purpose

Reconcile the accepted governance state on the default branch with the completed Test 2
research/evidence state, while preserving exact historical identities and keeping GitHub,
repository navigation, and the human-readable project dashboard consistent.

## Exact source identities

```text
Common base
083008ce64c3b008911b86bbd7586242508eeb60

Default-branch integration base
a732236c6b8da77111ad89ddaf7fb373fde26580
tree cf4fe7ded9f2d3a4bacd95513980434921daa16c

Preserved Test 2 evidence source
branch research/test2-g3f-real-execution-v1
commit c6e02818443c7a538e04053a14aa7ab0fe765248
tree d3bd9a31cdbb6b608e333fea7c8cc77c522a5df9

Integration candidate
branch integration/test2-repository-closeout-v1
commit b4a2aa539d03e0baacd084beb68fa54ae79955ac

Default-branch closeout result
pull request 45
commit 9778b9bd5c87ea177473b4ee7cb3cf27efd17110
```

Before integration, `origin/main` had three commits not in the Test 2 branch and the Test 2
branch had seventeen commits not in `origin/main`. A read-only merge-tree check reported no
content conflicts.

## Integration method

The repository requires linear history and forbids non-fast-forward updates. Rebase would
rewrite the reviewed Test 2 commit identities. This closeout therefore:

1. creates a new integration branch from exact `origin/main @ a732236`;
2. imports the `c6e0281` snapshot with squash semantics;
3. preserves every original remote research/evidence branch and SHA;
4. records source and integration identities separately;
5. uses a reviewed pull request and passing CI before any default-branch update.

The imported snapshot does not claim that `c6e0281` becomes an ancestor of main. It remains
the canonical historical Test 2 evidence identity on its preserved branch.

## Scientific disposition preserved

```text
Run ID                         MES_T2_G3F_D36A9AC8BA9CFB07
Real fold-fit calls            4
Real models fitted             2
Bootstrap replicates           6000
Disposition                    NOT_INTERESTING_ENOUGH
Validation rows read           0
Validation status              UNOPENED
Final-Test rows read           0
Final-Test status              SEALED
Semantic record SHA-256        630b7f86638fe0a844920107768784942a49b12ad505727f4f5e4adf87fd5aed
```

The original one-shot authorization is consumed and sealed. Closeout cannot mint a retry,
additional fit, third model, changed barrier, Validation opening, or Final-Test opening.

## GitHub queue reconciliation

At closeout start, the only open items were:

- Issue #28 — historical TREE001 specification, subsequently completed and failed;
- Draft PR #43 — VNext ancestor commit `17b169e`, subsequently superseded by the LangGraph
  retirement amendment and the completed Test 2 chain.

Final dispositions after PR #45 merged:

- Issue #28 — `CLOSED / COMPLETED-BUT-FAILED`; its closing note records the negative
  continuation result and grants no follow-on authority;
- PR #43 — `CLOSED / SUPERSEDED WITHOUT MERGE`; its branch remains preserved.

Live GitHub observation after reconciliation reported zero open Issues and zero open pull
requests. Closing either historical item created no new research or execution authority.

## Files intentionally current after closeout

- `README.md`
- `START_HERE_TH.md`
- `docs/architecture/README.md`
- `docs/architecture/ARCHITECTURE_PROGRESS.md`
- `docs/architecture/ARCHITECTURE_CHANGELOG.md`
- this closeout record

Of these six files, three also existed in the imported Test 2 delta and are intentionally
different from their `c6e0281` blobs: `README.md`, `docs/architecture/README.md`, and
`docs/architecture/ARCHITECTURE_CHANGELOG.md`. `START_HERE_TH.md` and
`docs/architecture/ARCHITECTURE_PROGRESS.md` came from the current main baseline and are
updated as navigation/status surfaces. This closeout record is new. Every other imported
Test 2 protocol, implementation, test, tool, and evidence blob must match `c6e0281` exactly.

Frozen architecture, protocol, implementation, and evidence files are not rewritten to make
their historical future-tense statements look current. Current status belongs in the
navigation/progress/closeout layer.

## Verification completed before commit

- source branch equals its upstream at `c6e0281`;
- original Test 2 evidence files are byte-identical to the source branch;
- governance files outside the imported/status-doc scope remain unchanged from `a732236`;
- full repository pytest passes;
- CI-equivalent critical Ruff scope passes;
- all 29 imported/changed active Python files pass the full Ruff rule set;
- the broader repository-wide full-rule scan has 339 pre-existing legacy findings in frozen
  notebooks and older Stage-B test surfaces; they are outside this closeout and are not hidden
  or mechanically rewritten;
- `git diff --check` passes;
- no force-push, evidence-branch deletion, Validation/Final access, fit, bootstrap, or economic
  diagnostic occurs during closeout.

## Integration gates completed

- live `origin/main` equaled `a732236` immediately before integration push;
- branch `integration/test2-repository-closeout-v1 @ b4a2aa5` was pushed without force;
- PR #45 passed Quant CI V1 and merged by squash to `main @ 9778b9b`;
- `research/test2-g3f-real-execution-v1` remained exactly `c6e0281` after merge;
- default-branch history remained linear;
- Issue #28 and PR #43 received the exact historical dispositions above;
- open Issue/PR queue was empty after reconciliation.

Obsidian and `CRASH_MEMORY.md` must use `main @ 9778b9b` (or a later explicitly observed
documentation-only successor) as the integrated repository checkpoint while continuing to
cite `c6e0281` as the canonical Test 2 source evidence identity.

## Next gate

The next work package is a separately reviewed and Owner-approved Test 3 protocol. No Test 3
implementation, new data access, or model training is authorized by this closeout.

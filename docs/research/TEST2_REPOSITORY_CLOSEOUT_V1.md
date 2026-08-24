# Test 2 Repository Closeout V1

**Date:** 2026-08-24

**Status:** `INTEGRATION CANDIDATE / RESEARCH STATE RECONCILIATION`

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

Their correct dispositions are `CLOSED / COMPLETED` for Issue #28 and
`CLOSED / SUPERSEDED WITHOUT MERGE` for PR #43. Closing either item creates no new research
or execution authority.

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

## Pending integration gates

- re-fetch and confirm live `origin/main @ a732236` immediately before push;
- push only `integration/test2-repository-closeout-v1` without force;
- open a reviewed integration pull request and obtain passing CI;
- preserve `research/test2-g3f-real-execution-v1 @ c6e0281` before and after merge;
- keep default-branch history linear;
- reconcile Issue #28 as completed-but-failed and PR #43 as superseded without merge;
- update Obsidian and `CRASH_MEMORY.md` to the final main integration identity.

## Next gate

After repository and human-memory identities are reconciled, the next work package is a
separately reviewed and Owner-approved Test 3 protocol. No Test 3 implementation, new data
access, or model training is authorized by this closeout.

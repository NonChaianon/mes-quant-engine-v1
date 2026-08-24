# MES Quant Engine — Architecture Progress

**Historical architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Research design direction:** `MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT / HUMAN-DIRECTED / FRAMEWORK-NEUTRAL`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `REPOSITORY CLOSEOUT BEFORE TEST 3 PROTOCOL FREEZE`

**Current gate:** `integrate verified Test 2 state -> reconcile GitHub queue -> freeze Test 3 before implementation`

> This file is the project-level progress source of truth. It describes observed state but
> grants no merge, data-access, model-fit, Validation, Final-Test, broker, or trading authority.

---

## Current position

```text
Default branch before closeout:         origin/main @ a732236
Preserved Test 2 evidence branch:       research/test2-g3f-real-execution-v1
Preserved Test 2 evidence HEAD:         c6e02818443c7a538e04053a14aa7ab0fe765248
Preserved Test 2 evidence tree:         d3bd9a31cdbb6b608e333fea7c8cc77c522a5df9

Test 1 / Sprint 1:                      CLOSED / SEARCH BUDGET 2 OF 2 SPENT
LR001:                                  COMPLETE / FAILED CONTINUATION RULE
TREE001:                                COMPLETE / FAILED CONTINUATION RULE

Test 2:                                 COMPLETE / CLOSED
Test 2 run:                             MES_T2_G3F_D36A9AC8BA9CFB07
Test 2 disposition:                     NOT_INTERESTING_ENOUGH
Test 2 real fold-fit calls:             4 OF 4
Test 2 real models fitted:              2
Test 2 bootstrap replicates:            6000
Test 2 authorization:                   CONSUMED / SEALED / NOT REUSABLE

Test 3:                                 PROTOCOL DECISION ONLY
Test 3 implementation/data/training:    NOT AUTHORIZED
Validation:                             UNOPENED
Final Test:                             SEALED
Live trading / broker execution:        DISABLED
LangGraph:                              RETIRED / DO NOT USE / DO NOT MERGE
```

## Why GitHub appeared behind Obsidian

The repository had two linear histories after common commit `083008c`:

- `origin/main` contained three accepted governance commits through `a732236`;
- the Test 2 evidence branch contained seventeen architecture/research/evidence commits
  through `c6e0281`.

Obsidian summarized the latter, while the default GitHub branch still showed the former.
No Test 2 commit or evidence was missing: the exact source branch was pushed and local/upstream
were equal. Repository closeout imports the verified Test 2 snapshot onto the current main
baseline without rebasing, force-pushing, deleting, or rewriting the original evidence refs.

See `../research/TEST2_REPOSITORY_CLOSEOUT_V1.md`.

---

## Completed research

### Test 1 / Sprint 1

| Candidate | Family | Result | Continuation |
| --- | --- | --- | --- |
| `LR001` | regularized logistic regression | log-loss improvement `-0.0026346` | failed |
| `TREE001` | bounded shallow decision tree | log-loss improvement `-0.0014909` | failed |

The frozen target-aware search budget is exhausted. No third Sprint 1 candidate is allowed.
Validation remained unopened and Final Test remained sealed.

### Test 2

Frozen question: whether locked path-aware features improve the first-touch `LONG/FLAT`
outcome beyond nuisance/time structure under TP `4.00`, SL `2.00`, and a 60-minute path.

| Model | Features | Pooled improvement vs prior | Disposition contribution |
| --- | ---: | ---: | --- |
| `PATHNUISANCE001` | 4 | `-0.0006737` | did not beat prior |
| `PATHFULL001` | 29 | `-0.0020563` | did not beat prior or nuisance |

All four authorized fold fits converged. Required support/ESS checks passed without relaxed
floors, and bootstrap lower bounds remained negative. This is a clean negative result inside
the frozen Test 2 scope, not an underpowered result and not evidence that every MES hypothesis
is false.

Committed evidence:

- run `MES_T2_G3F_D36A9AC8BA9CFB07`;
- semantic record SHA-256
  `630b7f86638fe0a844920107768784942a49b12ad505727f4f5e4adf87fd5aed`;
- evidence commit `c6e02818443c7a538e04053a14aa7ab0fe765248`;
- Validation rows read `0`; Final-Test rows read `0`.

The read-only MES Research Companion is a separate presentation layer over committed aggregate
evidence. It is not a database, research runtime, execution surface, or source of authority.

---

## Governance and architecture position

- Governance work accepted on main through `a732236` remains preserved by repository closeout.
- Architecture v2.2 remains the immutable historical Test 1 baseline.
- VNext remains the research design direction and does not itself authorize an experiment.
- The frozen Test 2 protocol and immutable result remain historical evidence after closeout.
- LangGraph was removed from active project direction by Owner decision; historical branches
  remain recoverable but must not be used, merged, or promoted.

---

## Current next sequence

```text
1. Complete repository closeout and reconcile GitHub Issue/PR status
2. Confirm Git main, remote evidence branch, and Obsidian identities
3. Draft and adversarially review one Test 3 hypothesis/protocol
4. Freeze exact source, target, partitions, model budget, metrics, gates, and stop rule
5. Request separate Owner authorization for implementation
6. Implement synthetic/code-only layer before any newly authorized data access or fit
```

Test 3 direction under discussion is not a frozen protocol. In particular, no target formula,
model family, data source, fit budget, or metric described in conversation becomes authoritative
until an exact protocol is reviewed and Owner-approved.

---

## Access levels

| Level | Meaning | Current position |
| --- | --- | --- |
| L0 | governance/contracts/synthetic-only implementation | next Test 3 code cannot begin before protocol authorization |
| L1 | TRAIN realized labels | historical Test 1/Test 2 authorizations are consumed; no Test 3 authority |
| L2 | Validation | unopened / forbidden until a separately frozen confirmatory protocol |
| L3 | Final Test | sealed one-time final confirmation |

Permission and observed access are separate. A successful test, CI run, PR, design document,
or prior experiment never grants the next access level.

---

## Evidence discipline

- Preserve exact original research/evidence branches and commit identities.
- Keep default-branch history linear; never force-push protected evidence refs.
- Distinguish source evidence SHA from repository integration SHA.
- `PASS` applies only to the exact reviewed identity and scope.
- `NOT_INTERESTING_ENOUGH` closes only the frozen experiment scope.
- Update this dashboard whenever the answer to “where are we now?” materially changes.

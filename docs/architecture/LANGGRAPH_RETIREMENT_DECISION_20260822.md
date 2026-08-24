# MES Quant Engine — LangGraph Retirement Decision

**Decision date:** 2026-08-22

**Decision owner:** Project Owner

**Status:** `OWNER_DECISION / ACTIVE`

**Scope:** MES project direction, Architecture VNext, Test 2 proposal, active research
coordination, and future implementation planning.

## Decision

LangGraph is removed from the MES project direction and will not be used.

Active research proposal, debate, critique, and adversarial review remain human-directed
and framework-neutral. They may use bounded tools or AI reviewers when the Owner asks, but
the project will not build, depend on, or plan around a graph runtime or orchestration
framework.

## Required disposition of existing work

The following local historical branches are retained only so Git history remains
recoverable and auditable:

```text
architecture/langgraph-boundary-v1
42cda10559b7b7ab9ffeb4fb4263a6d2e8bb5af3

research/langgraph-prototype-v0
8d5befba64627c170ae97e1193be028b53ca7857
```

Their disposition is:

```text
ABANDONED
DO NOT USE
DO NOT MERGE
DO NOT CHERRY-PICK
DO NOT PROMOTE
```

They grant no architecture, implementation, dependency, experiment, label-access, merge,
execution, deployment, or trading authority. Their open reviews/findings no longer block
the active MES track because the subject has been retired; they remain historical records,
not resolved findings.

## What this decision does not change

- `MES_QUANT_TARGET_ARCHITECTURE_v2.2` remains the immutable Test 1 baseline.
- LR001/TREE001 and the spent Sprint 1 search budget remain unchanged.
- Architecture VNext remains a Test 2+ design candidate only.
- Test 2 still requires a separate frozen protocol and explicit Owner authorization.
- Validation remains `UNOPENED`.
- Final Test remains `SEALED`.
- Live trading remains `DISABLED`.
- Git governance, evidence, risk, and execution boundaries remain in force.

## Historical-reference rule

Frozen governance documents and immutable evidence may retain the word `LangGraph` where
they record that no runtime existed, no authority was granted, or a historical artifact was
observed. Those references are not active dependencies and must not be rewritten merely to
erase history.

Any future proposal to reintroduce LangGraph or another orchestration framework requires a
new explicit Owner decision and a separately reviewed architecture package. Nothing in the
retired branches provides precedent or grandfathered authority.

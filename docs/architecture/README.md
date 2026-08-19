# MES Quant Engine — Architecture Index

This index separates the historical accepted baseline from the current Test 2+ design
candidate and its non-authoritative rationale.

## Current design candidate

- [`MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT.md`](MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT.md)
  — `CURRENT_DESIGN_CANDIDATE / TEST2+ / RESEARCH_ONLY`; no experiment or execution
  authority.

## Historical accepted baseline

- [`MES_QUANT_TARGET_ARCHITECTURE_v2.2.md`](MES_QUANT_TARGET_ARCHITECTURE_v2.2.md)
  — `BASELINE_ACCEPTED / DESIGN_CLOSED`; retained as immutable Test 1/Sprint 1 historical
  provenance and superseded only as the proposed design direction for Test 2+.

## Design rationale and project tracking

- [`../proposals/MES_RESEARCH_ARCHITECTURE_TEST2_PROPOSAL_V1.md`](../proposals/MES_RESEARCH_ARCHITECTURE_TEST2_PROPOSAL_V1.md)
  — retained proposal and design rationale; not the current architecture pointer.
- [`ARCHITECTURE_CHANGELOG.md`](ARCHITECTURE_CHANGELOG.md) — architecture history and the
  reasons for major changes.
- [`ARCHITECTURE_PROGRESS.md`](ARCHITECTURE_PROGRESS.md) — existing project progress record;
  it does not grant Test 2 authority.

## Authority rule

Architecture documents describe system boundaries and design direction. They do not by
themselves authorize label access, an experiment, Validation or Final-Test opening,
deployment, broker execution, or live trading. The applicable frozen protocol, governance
control, and explicit authorization remain required.

# Stage B constitutional project-root gate hardening

This file is safety-hardening evidence only. It is not a constitutional,
methodology, semantic-registry, or feature-decision authority.

## Scope and base

- Branch: `stage-b-project-root-gate-hardening`
- Authorized base: `0f8e5f160a69b0f2b9562fac08809867713b6492`
- Python policy status remains `PROVISIONAL`.
- Phase B was not implemented or executed.

## Finding

The absolute-first constitutional gate previously resolved Markdown and
semantic-registry controls relative to `analyzer.py`, while `run_stage_b()`
resolved its later canonical paths relative to the caller-supplied
`project_root`. That created two definitions of the constitutional root.

## Hardened behavior

`assert_stage_b_contract_locked()` now requires an explicit keyword-only
`project_root`. `run_stage_b()` passes its own caller-supplied value to the
gate as its absolute first executable action. The gate resolves both locked
constitutional controls from that supplied root and has no package-location
fallback.

The live `_contract` lookup, version/status validation, raw-byte hashes,
Markdown status, registry status/version, and source-contract binding remain
fail-closed. The unused import-time `POLICY_STATUS` binding was removed.

## RED evidence

Before the production change, the focused class
`StageBProjectRootGateSpecificationTests` produced `4 failed` with exit code
`1`, without syntax, import, collection, or indentation errors:

- `test_gate_requires_explicit_keyword_only_project_root`
- `test_real_gate_accepts_exact_controls_under_supplied_root`
- `test_real_gate_rejects_tampered_control_under_supplied_root`
- `test_run_stage_b_first_action_routes_caller_project_root_to_gate`

## GREEN evidence

- Focused project-root gate tests: `4 passed`
- Direct constitutional policy-gate tests: `6 passed`
- Phase 0 + Phase A focused tests: `19 passed`
- Full `tests/test_redundancy.py`: `159 passed`
- Full repository tests: `192 passed`
- Python source compilation: `PASS`
- Ruff comparison on active production/test files: no new rule/count versus
  the authorized base; analyzer `F401` count changed from `1` to `0`.

## SHA256 before and after

```text
src/mes_quant/redundancy/analyzer.py
before  6cf9d524e5e48e135e667a51588834003d2be1ddc66e59847e0eb5ea14bc7162
after   68a1b9d276b97cb346938b35838b6d6d0592da093b4b3329b925248306098da0

src/mes_quant/redundancy/contract.py
before  30809315b19a0d7c5de21c98e130e0d1ef2fd6ad68ed862660d0d42b39efa8b4
after   30809315b19a0d7c5de21c98e130e0d1ef2fd6ad68ed862660d0d42b39efa8b4

tests/test_redundancy.py
before  a33cd74d3bbf1adbd9d4c0b4aa523a630b4b7d992391ed1d2d76de23012115a5
after   6caf2931402c9ba6976e9ac6ec2b10175ebee3b2bdbdf79dd4f318211d4e76ff

docs/STAGE_B_REDUNDANCY_CONTRACT.md
before  4d7df08de288858003bba1e59e78197d647c822355918678c9991f45cf6f2229
after   4d7df08de288858003bba1e59e78197d647c822355918678c9991f45cf6f2229

configs/v1/stage_b_semantic_registry_v1.json
before  b91e173de834592292a13d1d69f5ef32f264189a6b83ef18512527c4af46b186
after   b91e173de834592292a13d1d69f5ef32f264189a6b83ef18512527c4af46b186
```

## Data-boundary evidence

- Cell8 full assignment rows opened: `0`
- Final Test rows opened: `0`
- Real Stage B production runs: `0`
- Labels/P&L/future returns/target fields opened: `0`
- Imputation, forward fill, median fill, or silent row deletion added: `NO`
- Runtime state after Phase A: still fail-closed before Phase B

## Known items deliberately deferred

### KNOWN_ITEM_1

Other analyzer constants retain import-time binding. No current correctness
failure is established. Any normalization is deferred to a separately scoped
architectural task with its own tests.

### KNOWN_ITEM_2

`run_stage_b()` currently reads and hashes the constitutional Markdown and
semantic registry again after the absolute-first gate. This is duplicate
validation, not a current correctness failure. It remains unchanged until a
separately specified and tested production-boundary refactor.

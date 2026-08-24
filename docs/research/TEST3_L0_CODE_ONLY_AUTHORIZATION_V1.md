# Test 3 L0 Code-Only Authorization V1

Authorization ID: `AUTH_TEST3_L0_CODE_ONLY_20260824`

Status: **OWNER AUTHORIZED / CODEX IMPLEMENTER / L0 SYNTHETIC ONLY**

Authorization date: `2026-08-24` (`Asia/Bangkok`)

Exact base: `5d5ec4a67648cbc5be4b3d2d8fceedea07caa01b`

Frozen protocol commit: `7c17b292958aeb8252f9c0911ef7028b6071cdbb`

Branch: `research/test3-l0-implementation-v1`

## Owner instruction and interpretation

After being asked to choose personal implementation or authorize Codex for Test 3 L0, the
Owner instructed Codex to proceed in a token-efficient form. This record binds that
instruction to Codex implementation of the bounded L0 package below. It grants no later
stage and does not authorize merge.

The exact base was renewed after the separately authorized evidence-repair commit restored
the executed Test 2 protocol identity and added Erratum 001. The repair changes no Test 3
scientific text: the ratified protocol and budget retain their exact frozen hashes.

## Exact allowlist

Only these ten additive files may be created:

1. `docs/research/TEST3_L0_CODE_ONLY_AUTHORIZATION_V1.md`
2. `docs/research/TEST3_L0_IMPLEMENTATION_PACKAGE_V1.md`
3. `src/mes_quant/exploration/test3_contract.py`
4. `src/mes_quant/exploration/test3_target.py`
5. `src/mes_quant/exploration/test3_design.py`
6. `src/mes_quant/exploration/test3_stats.py`
7. `tests/test_test3_contract.py`
8. `tests/test_test3_target.py`
9. `tests/test_test3_design.py`
10. `tests/test_test3_stats.py`

No pre-existing file may change. No dependency may be added.

## Authorized behavior

- encode the frozen identities, stages, statuses, counters, target arithmetic, predictor
  domain rules, common mask, harmonic, model-column order, QLIKE, Duan transform,
  dependence/null arithmetic, session bootstrap, and pass gate;
- use only synthetic in-memory fixtures and temporary directories in tests;
- run targeted tests, the existing full test suite, Ruff, allowlist/protected-surface checks,
  and a final Claude read-only adversarial review;
- commit and push the bounded branch after all gates pass.

## Forbidden behavior

- no DBN/Parquet/artifact adapter, filesystem data reader, provider, CLI runner, or database;
- no real metadata or numeric artifact access;
- no real target/path construction or `TARGET_SPACE_003` consumption;
- no fitter or real/synthetic model-fit entrypoint in this package;
- no Validation or Final-Test access, bootstrap on real data, live/broker action, or merge;
- no modification of the frozen protocol, budget, ratification record, Test 2 code/evidence,
  repository configuration, or dependency files.

## Exit gate

Completion requires exact allowlist equality, zero protected-file changes, targeted/full
pytest pass, Ruff pass, Claude review with no blocker/high, one implementation commit pushed,
and all L0 safety counters remaining zero. Completion opens no G2, G2-P, G3-P, or G3-F
authority.

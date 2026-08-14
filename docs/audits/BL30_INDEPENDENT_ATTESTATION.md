# BL-30 Independent Attestation

**Disposition:** `ACCEPT_GENESIS_ATTESTATION`

**Reviewer scope:** Independent review of the supplied `GENESIS_REPRODUCTION_EVIDENCE_V1` and its handoff summary against the locked BL-30 state machine. This attestation does **not** lock Stage B V1.2; it only closes BL-30 and advances the project to the one final V1.2 integration / contradiction / preservation audit.

## Evidence identity verified

- Supplied machine-readable evidence SHA-256: `20f4e2150e5ad49ef4e75b576b4e9b859a6aa3979764f2f80bbbc70d76eca29a`
- Independently recomputed SHA-256 from the uploaded evidence bytes: `20f4e2150e5ad49ef4e75b576b4e9b859a6aa3979764f2f80bbbc70d76eca29a`
- Evidence version: `GENESIS_REPRODUCTION_EVIDENCE_V1`
- Overall classification: `EXACT_BYTES`
- Acceptance thresholds introduced: `false`
- Scratch replay determinism: `PASS`

## Independent checks

Both clean runs independently report and machine evidence confirms:

- frozen reference raw SHA-256 = reproduction raw SHA-256 = `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452`;
- canonical content fingerprint equality;
- `31,193` rows in both frozen and reproduced artifacts;
- canonical row-key equality;
- column membership/order equality;
- dtype equality;
- null-mask equality for every column;
- Parquet metadata equality;
- exact mismatch count = `0` for every column;
- max absolute deviation = `0` for every float feature;
- max relative deviation = `0` for every float feature;
- max ULP distance = `0` for every float feature.

The evidence also reports that every provenance-bound upstream input SHA-256 matched its expected value before execution, with no required upstream artifact missing.

## Git control identity cross-check

The evidence binds reconstruction to repository commit `58d1c171acbaa9ea974874983928a5f58c51d8bc`. Independent GitHub lookup at that exact commit confirmed the recorded Git blob identities:

- `src/mes_quant/features/builder.py` → `3e1f36afeb1e801d8c434be3b3b4f212eaa70ef3`
- `src/mes_quant/features/contract.py` → `50b8bcd6c04bdf7616ac5b52d84a219934416620`
- `configs/v1/features_v1.json` → `effe8a2977a80d6bd470f14c1e45712af5b630b6`
- `src/mes_quant/pipelines/feature_pipeline.py` → `e942a5318c96bdd905b9c93ad0cc9f3fde9e4c38`

These identities match the machine-readable evidence.

## Environment interpretation

The reproduction environment used Python `3.12.10`, NumPy `2.0.2`, pandas `2.2.2`, and PyArrow `18.1.0`. The frozen manifest recorded Python `3.12.13` with the same NumPy/pandas/PyArrow versions. Because both current clean-process reproductions are byte-exact, the observed Python patch-version difference did not alter this artifact in these runs.

This finding is deliberately bounded: it does **not** claim general cross-environment equivalence and does **not** reconstruct the original process's complete historical syscall/resource-access trace.

## BL-30 decision

The locked BL-30 state machine allows `EXACT_BYTES` evidence to be accepted after independent review. No contradiction was found in the supplied evidence, its SHA identity, per-column equality diagnostics, provenance hashes, or independently cross-checked Git blob identities.

Therefore:

```text
BL-30 = CLOSED
GENESIS_ATTESTATION = ACCEPTED
CLASSIFICATION = EXACT_BYTES
```

Next gate:

```text
ONE FINAL STAGE-B V1.2
INTEGRATION / CONTRADICTION / PRESERVATION AUDIT
```

Stage B V1.2 remains `PROVISIONAL` until that final audit passes and no predefined `V1_2_LOCK_BREAKER` is present.
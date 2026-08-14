# MES Quant Engine V1 — BL-30 Genesis Reproduction Audit Summary

## Verdict

**Classification: `EXACT_BYTES`**

Two scratch-only clean-process reproductions generated feature artifacts that are byte-identical to the frozen canonical Cell 14 feature artifact and byte-identical to each other. No frozen artifact was overwritten. No acceptance tolerance was introduced or applied.

This result supports the bounded statement that the presently committed reconstruction controls and the six provenance-bound upstream inputs are sufficient to reproduce the frozen Cell 14 feature artifact exactly under the observed current environment. It does not reconstruct the original process's complete historical syscall/resource-access trace.

## Frozen reference

- Canonical run: `cell14_20260809T175203Z`
- Feature artifact SHA-256: `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452`
- Canonical content fingerprint: `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`
- Rows: `31,193`
- Columns: `41` total, including `29` feature columns per release provenance

## Committed reconstruction controls

- Repository commit: `58d1c171acbaa9ea974874983928a5f58c51d8bc`
- Worktree at evidence time: clean
- `builder.py`: SHA-256 `1971dcffb580aadac8292cf482b00608d2778f8b06e40cadc1fef149cb9976cc`; Git blob `3e1f36afeb1e801d8c434be3b3b4f212eaa70ef3`
- `contract.py`: SHA-256 `23b89e78a3658d5cf8809a7ca78cf99071efef66fadb0ce92c301cc57c07f05e`; Git blob `50b8bcd6c04bdf7616ac5b52d84a219934416620`
- `features_v1.json`: SHA-256 `ff1c1033a3b645a98e967441dd2fef01968ab8d33ce76d07415e3d8e1ecc480c`; Git blob `effe8a2977a80d6bd470f14c1e45712af5b630b6`
- `feature_pipeline.py`: SHA-256 `71a377b758df8a8aeea5cd5b7914a602c864f65d9a57eeccde02a160566d38d1`; Git blob `e942a5318c96bdd905b9c93ad0cc9f3fde9e4c38`

Each observed SHA-256 matched the Cell 14 release manifest before execution.

## Provenance-bound upstream inputs

| Artifact | SHA-256 |
|---|---|
| Cell 5 15-minute bars | `558723ed6965c23fb93a7abc61d65eee405dd9eb5f41a36a96c7b66bbc806dad` |
| Cell 5 audit | `0fd7aba3cca2f3ae88d24b048708517e4829302275ab25f90821ef2af2621c73` |
| Cell 7 decision universe | `f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7` |
| Cell 7 audit | `3e5f76d3ea3c91fe37bfb7f58235dc4c616da88b299a1d370a8a3c67653abf7e` |
| Cell 8 split assignments | `2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035` |
| Cell 8 audit | `add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a` |

All observed hashes matched the release provenance before execution. No required upstream artifact was missing.

## Reproduction results

| Check | Clean run 1 | Clean run 2 |
|---|---:|---:|
| Classification | `EXACT_BYTES` | `EXACT_BYTES` |
| Raw SHA-256 equals frozen reference | Yes | Yes |
| Canonical content fingerprint equals reference | Yes | Yes |
| Row count/key equality | Yes | Yes |
| Column membership/order equality | Yes | Yes |
| Dtype equality | Yes | Yes |
| Null-mask equality, every column | Yes | Yes |
| Parquet metadata equality | Yes | Yes |
| Exact mismatch count, all columns combined | 0 | 0 |
| Max absolute deviation, every float column | 0 | 0 |
| Max relative deviation, every float column | 0 | 0 |
| Max ULP distance, every float column | 0 | 0 |

Scratch replay determinism: **PASS (`EXACT_BYTES`)**.

## Observed environment

- Python `3.12.10`
- NumPy `2.0.2`
- pandas `2.2.2`
- PyArrow `18.1.0`
- Platform, CPU, NumPy/BLAS build configuration, thread-related environment variables, and SHA-256 hashes of loaded Python extension binaries are recorded in the machine-readable evidence.

The original frozen manifest records Python `3.12.13` with the same NumPy, pandas, and PyArrow versions. The byte-exact result therefore shows that the observed Python patch-version difference did not alter this artifact in these two reproductions; it is not a general cross-environment equivalence claim.

## Independent-audit disposition

Under the locked BL-30 state machine, `EXACT_BYTES` is eligible for independent attestation approval. The independent reviewer should verify the machine-readable evidence hash and may choose `ACCEPT_GENESIS_ATTESTATION` or `REJECT_GENESIS_ATTESTATION`; this run does not itself grant policy-lock authority.

Machine-readable evidence SHA-256 at handoff: `20f4e2150e5ad49ef4e75b576b4e9b859a6aa3979764f2f80bbbc70d76eca29a`.
# Cell-to-module migration map

| Frozen Colab cell | Repository ownership | Migration status |
|---|---|---|
| 0 Environment | `core/environment.py` + `pyproject.toml` | OPEN parity module; frozen source retained |
| 1 Provenance | `data/provenance.py`, manifests | OPEN parity module; frozen source retained |
| 2 Decode/integrity | `data/dbn.py`, `data/integrity.py`, `core/hashing.py` | Hash utility started |
| 3 Gaps | `data/gaps.py` | OPEN parity module |
| 4 Availability registry | `data/availability.py` | OPEN parity module |
| 5 15m resample | `data/resample.py` | Consumed as frozen input by Cell 14 |
| 6 Gap attribution | `data/gap_attribution.py` | OPEN parity module |
| 7 Decision Universe | `universe/decision_universe.py` | Consumed as frozen input by Cell 14 |
| 8 Split/purge | `validation/splits.py`, `validation/purging.py` | Consumed as frozen input by Cell 14 |
| 9 Costs | `costs/contract.py`, `costs/scenarios.py` | Frozen; forbidden Cell 14 input |
| 10 Endpoint labels | `labels/endpoint.py`, `labels/economic.py`, `labels/sealing.py` | Seal utility started; forbidden Cell 14 input |
| 11 Cost temporality | `costs/vintages.py`, `costs/semantics.py` | Frozen; forbidden Cell 14 input |
| 12 Path outcomes | `labels/paths.py` | Frozen; forbidden Cell 14 input |
| 13 Baselines/dependence | `validation/dependence.py`, `evaluation/*` | Frozen; forbidden Cell 14 input |
| 14 Features | `features/contract.py`, `features/builder.py`, `pipelines/build_features.py` | LOCKED computation/artifact; candidate catalog PROVISIONAL |
| Stage B Redundancy | `redundancy/contract.py` then `redundancy/analyzer.py` | NEXT; contract PROVISIONAL_NOT_EXECUTABLE |

Pipeline files may orchestrate I/O and write artifacts but must contain no feature formula. Production
modules must not hardcode `/content/drive/...`, depend on notebook globals, or write on import.

# MES Quant / Auto-Trading Engine - Living Project Handoff

**Evidence cut-off:** 2026-08-10 00:55 Asia/Bangkok  
**Canonical notebook:** `MES_Quant_Pipeline_V1_CANONICAL_DEV`  
**Notebook URL:** `https://colab.research.google.com/drive/1U3KJQJmTnt2bQyeQPfPybgZa9_VllMjG`  
**Canonical Drive artifact root:** `/content/drive/MyDrive/Quant_Lab/Data/MES_Clean_Pipeline_V1/`  
**Purpose:** Source-of-truth handoff for continuing the project in ChatGPT Work or Codex.

Status vocabulary:

- **LOCKED:** Accepted contract or result. Change only after a documented defect, impact analysis, dependent rerun, and audit.
- **PROVISIONAL:** Valid for current research use, but evidence or policy is not complete enough to freeze.
- **OPEN:** Not decided, not sourced, or not implemented.
- **REJECTED:** Known-invalid method that must not return as active logic.

## 1. Executive state

The project is building an auditable MES probability and auto-trading engine whose production destination is Interactive Brokers (IBKR). It now has a clean Colab research foundation through Cell 13 and a deterministic repository-native point-in-time feature foundation through Cell 14.

The canonical notebook completed a clean top-to-bottom run in the correct order:

`Cell 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13`

Execution counts were consecutive `37 -> 50`. All cells passed. The previous `jupyter_client` warning flood was absent (`0` matching warnings), the notebook was saved, and Cell 9 no longer contains two active implementations.

Current stage:

- Data provenance, raw integrity, resampling, gap attribution, and the Decision Universe are complete.
- Chronological partitions and walk-forward validation folds are complete.
- A current-deployment cost counterfactual exists, but historical fee vintages and historical spread/slippage are still OPEN.
- Fixed-horizon +60m endpoint labels and development-only 1m path outcomes are complete.
- Naive LONG/FLAT baselines, non-overlapping position simulation, dependence diagnostics, and session-block confidence intervals are complete.
- Cell 14 produced 29 point-in-time candidate features for all 31,193 Development decisions. The build contract and artifacts are LOCKED; feature retention remains PROVISIONAL until redundancy analysis.
- The VS Code migration gate is complete. Colab Cells 0-13 are frozen evidence; repository code is authoritative from Cell 14 forward.
- No predictive model has been fitted. Final Test 2025-2026 remains SEALED.

The next implementation is Stage B redundancy and stability analysis, followed by transparent out-of-fold models. It must not open Final Test or claim historical realized P&L.

## 2. Objective and target architecture

Objective: build a production-capable MES system that converts only information available at decision time into calibrated probabilities, applies explicit economic and risk gates, executes through IBKR, and records enough evidence to reproduce every decision and halt trading safely.

Target architecture:

`Canonical Data -> Data Quality / Provenance -> Decision Universe -> Point-in-Time Features -> Market Dynamics / Regime -> Redundancy Control -> Candidate Models -> OOF Probabilities -> Calibration -> Macro Context -> Risk Engine -> Position Sizing -> Cost Gate -> Execution Simulator -> Server / State / Monitoring -> IBKR Paper -> IBKR Live -> Attribution / Drift / Kill Switch`

ChatGPT Work is the decision and audit headquarters. Colab is the immutable evidence authority for Cells 0-13. Codex/VS Code is now the primary implementation environment from Cell 14 forward.

## 3. Non-negotiable research principles

- Point-in-time only: no future information in data eligibility, features, labels, splits, tuning, calibration, model selection, or cost-tier selection.
- Raw Databento DBN is canonical. Derived Parquet is a reproducibility and cross-check artifact.
- No forward fill, synthetic OHLCV, arbitrary imputation, or deletion of raw observations merely because a time gap exists.
- NYSE calendar rules are a V1 research-policy filter, not evidence that CME/MES was untradable.
- Partial 15m bars may remain context but are never decision-eligible.
- Final Test is sealed before any aggregation, class count, price lookup, model selection, or P&L calculation.
- Costs must state their temporal meaning. Current fees applied to historical dates are a deployment counterfactual, not historical actual P&L.
- Overlapping +60m outcomes invalidate row-IID confidence intervals. Primary uncertainty must resample consecutive trading sessions.
- A new model must beat predeclared baselines out of fold and must be compared using paired session-block differences.
- Probabilities must be calibrated out of sample before probability-based sizing or gating.
- Every cell/module must declare inputs, outputs, hashes, counts, policies, hard gates, failures, and open items.

## 4. Market and data contract

- Instrument: CME Micro E-mini S&P 500 futures, continuous symbol `MES.v.0`.
- Dataset/schema: Databento `GLBX.MDP3`, `ohlcv-1m`.
- Symbology: `stype_in=continuous`, `stype_out=instrument_id`.
- Requested range: `2019-04-15` to `2026-08-01` exclusive.
- Observed raw range: `2019-05-05 22:00:00+00:00` to `2026-07-31 20:59:00+00:00`.
- Canonical raw DBN: `/content/drive/MyDrive/Quant_Lab/Data/MES_2019_2026_1m.dbn.zst`.
- Raw size: `40,078,487` bytes.
- Raw DBN SHA256: `49f243a443abd199607bb51ce8d6c82928e2ba2a0ebb4a11ede10e7e0a0a46d0`.
- Raw rows: `2,551,123`.
- Decision frequency: 15 minutes.
- V1 decision clock: 09:45-15:00 America/New_York.
- Initial holding/label horizon: +60 minutes.
- 15m convention: source index is bar start; `decision_time = index + 15 minutes`; resampling is left-labeled and left-closed.
- V1 action space: LONG / FLAT. SHORT outcome remains a diagnostic class; a short position is not permitted in V1.
- V1 position policy: hold for 60 minutes, maximum one open position, and allow a new entry exactly when the prior position exits.
- MES mechanics: USD 5.00 per index point, 0.25-point tick, USD 1.25 per tick.

## 5. Decision register

### LOCKED

- Raw DBN identity, metadata, row count, observed range, and SHA256.
- Exact DBN-to-legacy-Parquet equality for index and `instrument_id, open, high, low, close, volume`.
- UTC raw time; America/New_York policy time.
- No raw-data fill, invented bar, automatic gap deletion, or automatic degraded-date deletion.
- Real-observation 1m-to-15m aggregation and removal of empty resample bins.
- Partial 15m bar is context-only and decision-ineligible.
- Corrected Cell 6 gap classification; no short-gap or weekend causal overclaim.
- Cell 7 Decision Universe policy version `MES_V1_DECISION_UNIVERSE_1.0` and its frozen universe hash.
- Cell 8 chronological split and boundary-purge contract. Zero purged rows is valid because year boundaries already exceed the +60m horizon; this contract does not claim to remove within-fold label dependence.
- Fixed endpoint label reference: completed 15m close to +60m close, same instrument, four future 15m bars, no roll crossing.
- Final Test 2025-2026 sealing.
- Cell 12 exact 60-row 1m path contract for Development only.
- V1 LONG/FLAT action space and non-overlapping 60m position simulator.
- OOF validation years 2022, 2023, and 2024.
- Consecutive-session moving-block bootstrap: 2,000 repetitions; 5 sessions primary; 1 and 20 sessions sensitivity.

### PROVISIONAL

- Cell 9 direct fee snapshot observed on 2026-08-09.
- `CONSERVATIVE` current-deployment counterfactual: USD 4.97 round trip and 0.994 index-point break-even.
- Cell 10 economic labels created with that current-deployment counterfactual. They are valid research labels but not historical-actual P&L labels.
- Current spread/slippage assumptions. They are scenario assumptions, not reconstructed historical bid/ask evidence.
- The +60m endpoint is the primary V1 target while stop/target policy remains undecided.

### OPEN

- Effective-dated CME and IBKR historical fee sources covering every Development date.
- The user's IBKR legal entity, pricing plan, taxes, and causal month-to-date volume tier.
- Historical bid/ask or a sourced historical execution-cost proxy.
- Stop and target distances, triple-barrier use, and same-bar ambiguity policy. Cell 12 deliberately did not invent these.
- Point-in-time feature catalog, feature availability timestamps, transformations, and missingness policy.
- Redundancy thresholds, incremental-value rules, and feature stability gates.
- Candidate model family, hyperparameter governance, and paired baseline acceptance thresholds.
- Calibration method and probability decision threshold.
- Macro vintages and release-time contracts, including ALFRED-style vintages where applicable.
- Risk limits, sizing, execution assumptions, server topology, paper-trading acceptance period, and live promotion criteria.

### REJECTED

- Two active Cell 9 implementations in one cell and two contradictory hashes from one run.
- Calling current 2026 fees the historically realized cost of 2019-2024 trades.
- Fabricating historical fee values or effective dates when evidence is missing.
- Row-level IID confidence intervals for 15m decisions with +60m overlapping outcomes.
- Treating 31,165 outcome rows as 31,165 independent observations.
- Treating boundary purging as a remedy for within-fold dependence.
- Allowing every 15m LONG signal to create an overlapping 60m position.
- Trading SHORT in V1 merely because a SHORT diagnostic label exists.
- Replacing the fixed endpoint label in place with triple barrier before stop/target and ambiguity policies are locked.
- Guessing which barrier was touched first when both occur inside the same 1m OHLC bar.
- Treating any weekend-touching gap as a weekend closure or a short gap as multiday closure.
- Treating NYSE closure as proof that MES was not tradable.
- Training against Final Test, reporting its label balance, or performing its price lookup.

## 6. Cell-by-cell status and findings

### Cell 0 - Environment validation - LOCKED / PASS

Pinned versions passed: `databento 0.83.0`, `databento-dbn 0.65.0`, `pandas-market-calendars 5.4.0`, and `exchange-calendars 4.13.2`. Runtime observed Python 3.12.13, pandas 2.2.2, NumPy 2.0.2, and PyArrow 18.1.0. Two pre-existing global conflicts were recorded; Cell 0 introduced no new conflict. The narrow warning guard stopped the prior Jupyter `utcnow` flood without globally silencing data warnings.

### Cell 1 - Raw identity and provenance - LOCKED / PASS

Verified path, size, raw SHA256, DBN metadata, mapping intervals, environment snapshot, and frozen baseline. Metadata has 30 `MES.v.0` mapping intervals.

### Cell 2 - Decode and raw integrity - LOCKED / PASS

Decoded `2,551,123` rows. UTC index is monotonic with zero duplicate timestamps. OHLCV NaNs, OHLC structure violations, and negative-volume rows are all zero. There are 30 unique instrument IDs and 29 roll transitions. DBN-to-Parquet equality passed.

The provenance addendum upgrades the audit to `MES_V1_RAW_INTEGRITY_1.1` and fingerprints the exact decoded in-memory frame consumed downstream. Content SHA256 over index plus `open, high, low, close, instrument_id` is `e5ef411831c26d5f6975da33c1ffa0891d40c483d20e5b12bc95a73e73193584`.

### Cell 3 - Supplemental raw/gap audit - LOCKED / PASS

Of `2,551,122` timestamp transitions, `2,543,191` are exactly one minute and `7,931` exceed one minute. There are zero minute-alignment violations and zero non-integer-minute gaps. Two gap events cross a roll boundary. No gap is automatically declared a data error.

### Cell 4 - Dataset condition registry - LOCKED / PASS

The cached Databento registry contains `2,319` dates: `2,302 available`, `17 degraded`, `0 pending`, and `0 missing`. Degraded dates are retained as context and are not automatically excluded.

### Cell 5 - 1m to 15m resample - LOCKED / PASS

From `2,551,123` raw rows, resampling produced `253,820` clock bins; `83,234` empty bins were removed; `170,586` observed 15m bars remain. `167,030` are complete and `3,556` partial. No 15m bar crosses a roll. The V1 clock has `40,621` candidates, including `47` partial bars.

### Cell 6 - Corrected raw-gap attribution - LOCKED / PASS

Cell 6 is now LOCKED because the corrected code passed again inside the canonical Cell 0-13 Run All. It binds all `7,931` Cell 3 gap events and explains every V1 partial bar (`47 explained`, `0 unexplained`). Findings:

- `531` exact CME 16:15-16:30 halt patterns.
- `1,436` exact CME 17:00-18:00 daily-closed patterns.
- `134` gap events overlap V1 input bars.
- `383` weekend/multiday candidates with median gap `2,941` minutes.
- `26` degraded-date overlap events and `2` roll-boundary gap events.
- `0` unclassified events; no automatic deletion or imputation.

The earlier counts (`486` V1 overlap, `944` weekend candidates, median 3 minutes) are REJECTED and must never be reused.

### Cell 7 - Point-in-time Decision Universe - LOCKED / PASS

Policy version `MES_V1_DECISION_UNIVERSE_1.0`. From `40,621` clock candidates, `39,847` are eligible and `774` excluded across `1,820` eligible NYSE sessions. Primary exclusions are `686 NO_NYSE_POLICY_SESSION`, `75 AFTER_HORIZON_SAFE_CLOSE`, and `13 INPUT_BAR_PARTIAL`. All `47` partial clock bars are resolved: 34 occur on excluded NYSE-policy dates and 13 are explicitly excluded by the integrity gate. Eligible partial bars = 0. Degraded eligible rows retained = 230. Universe SHA256: `f86024c7a36780e6a559cc0eec15a7a52a851b24cb453a50136b609c440f2ca7`.

### Cell 8 - Chronological splits and boundary purging - LOCKED / PASS

Outer partitions:

- TRAIN: `25,685` rows, `1,173` sessions, 2019-05-06 to 2023-12-29.
- VALIDATION: `5,508` rows, `252` sessions, 2024-01-02 to 2024-12-31.
- FINAL_TEST: `8,654` rows, `395` sessions, 2025-01-02 to 2026-07-31.

Walk-forward validation rows are `5,510` for 2022, `5,476` for 2023, and `5,508` for 2024. Boundary overlap after purge is zero. `purged_train_rows=0` is expected because calendar-year boundaries leave more than 60 minutes. Embargo is zero. Cell 8 creates no economic label. Assignment SHA256: `2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035`.

### Cell 9 - Research cost model - LOCKED mechanics / PROVISIONAL costs / PASS

The duplicated first implementation was removed. The cell now writes each artifact once and emits one scenario hash. Current snapshot:

- Direct fee: USD 0.61 per side, USD 1.22 round trip.
- FEES_ONLY: USD 1.22 / 0.244 points.
- BASE: USD 3.095 / 0.619 points.
- CONSERVATIVE primary: USD 4.97 / 0.994 points.
- STRESS: USD 8.72 / 1.744 points.

Scenario SHA256: `2248d59ff32361dff9c5df94bfdf8d7ad6942ee50ef3d6e1c6a3731779aeff4f`.

### Cell 10 - Fixed +60m endpoint economic labels - PROVISIONAL / PASS

Cell 10 binds the exact Cell 8 assignment hash and Cell 9 scenario hash. Of `31,193` Development rows, `31,165` labels are usable and `28` are unusable because of `HORIZON_BAR_PARTIAL`. Development counts are `15,188 LONG`, `13,147 SHORT`, and `2,830 NO_TRADE`. The `8,654` Final Test rows are SEALED; price lookup and outcome calculation are false. Labels SHA256: `1f73f06d92bc54ccceff637503ef9cbece0c2b0c6b2018802923ef51d7352bd0`.

Interpretation: the label is an endpoint outcome after the current-deployment conservative counterfactual. It is not proof that the same fee, spread, or slippage existed historically. SHORT is diagnostic; the V1 action remains LONG/FLAT.

### Cell 11 - Cost temporality registry - PROVISIONAL / PASS

Cell 11 verifies both Cell 9 scenario and parameter hashes, reconciles every direct fee component, and separates semantic views:

- `CURRENT_DEPLOYMENT_COUNTERFACTUAL`: PROVISIONAL.
- `STRESS_COUNTERFACTUAL`: PROVISIONAL.
- `HISTORICAL_VINTAGE`: OPEN, coverage ratio 0.0, historical labels disabled.

No historical numeric fee was invented. A current snapshot cannot match historical dates. Future volume-tier selection must use causal cumulative month-to-date contracts. Semantic cost SHA256: `7b3c619f1a8c4612d9a6b3df40f86136030baae616c4b0cd160e1651c2db0302`.

### Cell 12 - Development-only 1m path outcomes - LOCKED computation / PASS

Cell 12 verifies the Cell 2 decoded-memory SHA, Cell 10 audit, and Cell 10 label hash before any path calculation. It requests exact 1m bars from `t` through `t+59m` for usable TRAIN/VALIDATION rows only. Results:

- `31,165` usable Development paths.
- Exactly 60 one-minute bars per usable path.
- Endpoint mismatches: 0.
- Final Test price lookups: 0.
- Final Test numeric and timestamp path fields: SEALED / null.
- True path high/low, LONG/SHORT MFE/MAE, and close-path drawdown are retained.
- Triple barrier: OPEN and not created.

Path outcome SHA256: `8e1a9bc263e2dab5e1588d0797cdaa2fa0038a6bcfd6ac1ec9433fa35c253941`.

### Cell 13 - Dependence audit and naive baselines - LOCKED evaluation contract / PASS

Cell 13 uses only Development data and validates all lineage across Cells 8, 10, 11, and 12. It evaluates four OOF baselines on 2022-2024, applies the V1 LONG/FLAT non-overlapping 60m position policy, and charges the USD 4.97 current-deployment counterfactual once per executed trade.

Dependence findings confirm the audit concern. +60m returns at 15m spacing have lag-1 autocorrelation about `0.756-0.769`, maximum available label concurrency `4`, and descriptive effective sample sizes about `1,290-1,370` per fold versus roughly `5,500` rows. Therefore, row count is not the independent sample size.

Pooled OOF point results:

- ALWAYS_FLAT: accuracy `50.497%`, 0 trades, net P&L USD `0`.
- ALWAYS_LONG: accuracy `49.503%`, `4,500` executed trades, `11,994` overlapping LONG signals ignored, net P&L USD `-21,226.25`, Sharpe `-2.417`.
- STRATIFIED_RANDOM_ACTION: accuracy `50.133%`, `3,449` executed trades, net P&L USD `-15,371.53`, Sharpe `-2.000`.
- TRAIN_PRIOR_PROBABILITY chooses FLAT in all three folds because each training LONG prior is below 0.5; point result equals ALWAYS_FLAT for action/P&L while retaining probabilistic Brier/log-loss outputs.

Primary 5-session block-bootstrap pooled intervals:

- ALWAYS_LONG mean session P&L: USD `-27.42`; 95% interval `[-40.08, -15.10]`; Sharpe interval `[-3.40, -1.31]`.
- STRATIFIED_RANDOM mean session P&L: USD `-19.94`; 95% interval `[-30.76, -8.92]`; Sharpe interval `[-2.96, -0.90]`.
- ALWAYS_FLAT and TRAIN_PRIOR Sharpe are explicitly `UNDEFINED_ZERO_VARIANCE`, not silently averaged or displayed as a numeric value.

All `751` canonical validation sessions are represented: 251 in 2022, 250 in 2023, and 252 in 2024. Final Test rows used = 0. Baselines are established; model fitted = false.

Cell 13 artifact hashes:

- Baseline events: `a745ad7dd8f39f9c4b90cafedb8ab6cd8242c0991c177698e86dbfad68bc7df4`.
- Dependence audit: `113412d42ac08bd87c18cec014924252f9e53a0762fa061ca887598681344ded`.
- Baseline metrics: `08d79380c2c8c78110089fa7e79946117dd3c22d12438ad52b8d53421299c541`.
- Block-bootstrap intervals: `4725180e69e64a43b71a082e8f0b85e9b4238f81b98d892468060b71d394ed44`.

## 7. What the project now knows

1. The raw and resampled data foundation is internally consistent, traceable, and reproducible.
2. Every V1 partial bar has an explanation, and none enters the Decision Universe.
3. The Decision Universe is frozen at `39,847` rows, while `8,654` rows in 2025-2026 remain sealed Final Test.
4. Year-boundary label leakage is absent; within-fold dependence is real and large.
5. A naive claim such as "49.5% accuracy is near 50%, so it is acceptable" is economically wrong. Always-LONG loses heavily after the current conservative cost and non-overlap rules.
6. Current fees do not create hidden feature leakage because they are not used as market information. The remaining problem is semantic and economic: they cannot be called historical actual costs.
7. The +60m endpoint label alone cannot answer intrahorizon drawdown or barrier-touch questions. Cell 12 now preserves path outcomes so risk and auxiliary-label policies can be designed without reopening Final Test.
8. A model must beat FLAT, LONG, and train-prior baselines using paired session-block comparisons. A small row-level accuracy improvement is not sufficient.

## 8. Source-of-truth files

Primary notebook:

- `https://colab.research.google.com/drive/1U3KJQJmTnt2bQyeQPfPybgZa9_VllMjG`

Verified pre-methodology backup:

- `https://colab.research.google.com/drive/1ZAzEakwv7HGdvAWdQjx3uhU06HlIjfbo`

Canonical artifact directory:

- `/content/drive/MyDrive/Quant_Lab/Data/MES_Clean_Pipeline_V1/`

Core artifacts in execution order:

- `runtime_source_audit.json`
- `raw_source_baseline.json`
- `cell2_raw_integrity_audit.json`
- `cell3_supplemental_raw_audit.json`
- `cell4_dataset_condition_audit.json`
- `MES_2019_2026_15m_clean.parquet`
- `cell5_15m_resample_audit.json`
- `cell6_gap_attribution_audit.json`
- `cell7_decision_universe_v1.parquet`
- `cell7_decision_universe_ledger.parquet`
- `cell7_decision_universe_audit.json`
- `cell8_purged_split_assignments_v1.parquet`
- `cell8_walk_forward_folds_v1.csv`
- `cell8_purge_boundaries_v1.csv`
- `cell8_purged_split_audit.json`
- `cell9_cost_parameters_v1.csv`
- `cell9_cost_scenarios_v1.csv`
- `cell9_cost_model_audit.json`
- `cell10_point_in_time_economic_labels_v1.parquet`
- `cell10_development_label_summary_v1.csv`
- `cell10_economic_label_audit.json`
- `cell11_cost_scenarios_semantic_v1.csv`
- `cell11_fee_vintage_registry_v1.csv`
- `cell11_cost_temporality_audit.json`
- `cell12_development_path_outcomes_v1.parquet`
- `cell12_path_status_summary_v1.csv`
- `cell12_path_outcomes_audit.json`
- `cell13_development_oof_baseline_events_v1.parquet`
- `cell13_dependence_ess_audit_v1.csv`
- `cell13_naive_baseline_metrics_v1.csv`
- `cell13_block_bootstrap_ci_v1.csv`
- `cell13_development_baseline_audit.json`

Repository authority from Cell 14 forward:

- `MES_Quant_Engine_V1.code-workspace`
- `reference/colab_v1_cells_0_13/` — immutable notebook and extracted Cells 0-13.
- `manifests/releases/frozen_colab_manifest_v1.json` — frozen migration checkpoint.
- `configs/v1/features_v1.json` — Cell 14 locked configuration.
- `src/mes_quant/features/contract.py` and `src/mes_quant/features/builder.py` — locked feature contract/computation.
- `src/mes_quant/pipelines/feature_pipeline.py` — audited Development-only orchestration/firewall.
- `manifests/releases/cell14_local_release_v1.json` — canonical/replay Cell 14 release evidence.
- `docs/STAGE_B_REDUNDANCY_CONTRACT.md` — next development contract.

Authority rule: raw DBN plus frozen baseline plus per-cell artifacts and their hashes outrank notebook display text. Notebook output is evidence only when it agrees with saved artifacts.

## 9. Notebook health and known issues

Resolved:

- Cell order is canonical `0 -> 13`.
- Clean Run All completed with consecutive execution counts `37 -> 50`.
- Warning flood is absent.
- Cell 9 duplicate implementation is removed.
- Cell 2 now binds downstream path calculations to exact decoded in-memory content.
- Cell 10/11/12/13 lineage gaps are closed.
- Final Test path and outcome lookup count is mechanically zero.

Still OPEN, not runtime defects:

- Cell 0 records two pre-existing Colab dependency conflicts. It introduced no new conflict and all critical packages passed.
- Historical cost evidence is incomplete.
- Mutable web fee sources should be archived and hashed before historical claims.
- Triple-barrier policy is not locked.
- The project remains a research notebook; modules, tests, server state, and IBKR integration do not exist yet.

## 10. Working protocol

1. One contract or cell at a time.
2. Builder implements; Auditor independently checks source, output, saved artifacts, hashes, and leakage boundaries.
3. Use a Drive copy before any material notebook rewrite.
4. Every active cell must have one implementation only.
5. Run dependent cells top to bottom after a contract change; never reuse stale outputs as proof.
6. Explain every exclusion, label status, and economic assumption to the project owner in plain language.
7. Do not promote PROVISIONAL to LOCKED merely because code ran without an exception.
8. A LOCKED change requires: defect statement, impact analysis, version bump where needed, dependent rerun, new hashes, and handoff update.
9. Never put API keys, IBKR credentials, or private account identifiers in notebooks, artifacts, repositories, or this handoff.
10. Do not inspect Final Test until the full feature, model, calibration, risk, and acceptance protocol is frozen.

## 11. Roadmap from the current point

### Stage A - Point-in-time feature foundation - COMPLETE / LOCKED COMPUTATION

Cell 14 is implemented as repository modules, not another monolithic notebook cell. It records source, exact availability time, fixed/session lookback, missingness, transformation, partition scope, and formula for 29 transparent MES-only features. It opens only Cells 5/7/8 inputs and never Cells 9-13 target/cost/path artifacts.

Gate result: two byte-identical real-data builds, 31,193 Development rows, 30,197 fully usable rows, 996 explicitly unusable rows, 5,703 one-to-one missingness ledger entries, zero 2025+ rows, zero forbidden artifacts opened, 33/33 tests, lint PASS, and independent recomputation of all 29 formulas with zero difference. Feature content SHA256: `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`.

### Stage B - Redundancy and incremental value

Use Pearson/Spearman correlation, mutual information computed only on allowed training data, clustering/PCA as diagnostics, and incremental OOF predictive value. Do not keep a large correlated feature pile merely because individual p-values look interesting.

Gate: predeclared redundancy thresholds and a stable reduced feature set per fold.

### Stage C - Transparent candidate models

Start with logistic regression and a simple regularized nonlinear/tree benchmark only after features are frozen. Produce fold-specific OOF probabilities for 2022-2024. Hyperparameters must be selected inside allowed training history, never on 2024 pooled outcomes or Final Test.

Gate: paired 5-session block-bootstrap differences versus ALWAYS_FLAT, ALWAYS_LONG, and TRAIN_PRIOR_PROBABILITY. Report both opportunity-row classification and executable-policy economics.

### Stage D - Probability calibration

Compare uncalibrated, Platt, and isotonic calibration using only allowed OOF/nested validation predictions. Evaluate Brier score, log loss, reliability curves, probability-bin sample size, and stability by year/regime.

Gate: calibration improves or preserves predeclared probability metrics without degrading economic robustness.

### Stage E - Cost evidence and economic labels

Collect effective-dated CME/IBKR fee evidence and archive/hash source documents. Confirm account entity and pricing plan. Add causal month-to-date tier logic. Add historical spread/slippage evidence or a sourced regime proxy. Until coverage reaches 100%, continue labeling P&L as current-deployment or stress counterfactual.

Gate: historical-vintage labels remain disabled unless every Development decision date has exactly one sourced, non-overlapping vintage.

### Stage F - Macro/regime layer

Add only release-time point-in-time macro vintages: rates, yield curve, CPI/PCE, employment, GDP, financial conditions, and VIX. Record publication time, revision/vintage, timezone, and market availability delay. Use macro as context/regime, not a license to leak revised data.

### Stage G - Risk and sizing

Use Cell 12 path outcomes for MFE/MAE, drawdown, scenario analysis, and future stop/target research. Define exposure cap, daily loss, max drawdown, volatility/liquidity scaling, stale-data gate, and kill switch before Kelly-style sizing. If Kelly is used, use conservative fractional Kelly with estimation-error caps.

### Stage H - Execution simulator

Implement event-driven order state, fills, slippage, rejections, partial fills, cancellation, latency, duplicate-order prevention, position reconciliation, and implementation shortfall. No live trading from a vectorized notebook backtest.

### Stage I - Repository and server

Migrate frozen contracts into modules such as `data`, `features`, `labels`, `validation`, `costs`, `models`, `calibration`, `risk`, `execution`, `monitoring`, and `tests`. Add immutable manifests, configuration validation, CI, structured logs, metrics, alerts, a state store, secrets, clock synchronization, backups, and restart-safe idempotency.

### Stage J - IBKR

Paper account first. Implement contract qualification, market-data subscription checks, pacing/reconnect logic, order-ID and state recovery, position/order reconciliation, and manual/automatic kill switches. Promote to live only after a predeclared paper-trading duration and operational/economic acceptance criteria.

## 12. VS Code migration and Cell 14 release

**Migration gate: COMPLETE for primary development.** Open `MES_Quant_Engine_V1.code-workspace`. The exact Python 3.12.13 / NumPy 2.0.2 / pandas 2.2.2 / PyArrow 18.1.0 environment is installed in `.venv`. The six required Cells 5/7/8 inputs are cached locally and match the frozen Drive sizes and SHA256 values.

Cell 14 policy `MES_V1_FEATURES_1.0` is **LOCKED for computation and artifacts**:

- Canonical run: `cell14_20260809T175203Z`; deterministic replay: `cell14_20260809T175217Z`.
- Development rows: `31,193` = `25,685 TRAIN + 5,508 VALIDATION`; Final Test rows: `0`.
- Candidate features: `29`; fully usable rows: `30,197` (`96.807%`); explicitly unusable rows: `996`.
- Missing feature cells: `5,703`, each with exactly one ledger record. Reasons: `5,393 PARTIAL_LOOKBACK_BAR`, `227 MISSING_LOOKBACK_BAR`, `83 SESSION_VWAP_INPUT_INVALID`.
- Unusable rows are concentrated in early history: 2019 `677`, 2020 `235`, 2021 `67`, 2023 `2`, 2024 `15`. Modeling missingness policy remains OPEN; no value was imputed.
- Full-29 complete-case modeling remains PROVISIONAL because 8 sessions have zero usable rows and several March 2020 crisis sessions disappear entirely. Later economic evaluation must map every unusable/no-score decision to FLAT/zero P&L and retain it in coverage metrics.
- Longest fixed lookback: `240m`; session VWAP proxy maximum: `22 bars / 330 elapsed minutes`; source maximum never exceeds decision time.
- Forbidden Cell 9-13 artifacts opened: `0`; market rows at/after the 2025 Final Test boundary returned: `0`.
- Feature file SHA256: `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452`.
- Ordered feature-content SHA256: `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`.
- Registry SHA256: `7df68538d3e4a1447f1bca01396e3e141389decd196ba32faf04e34913107d95`.
- Status-summary SHA256: `fbbe4574e74d80675b60e0e9f3131168fb48383ff0214a30fba8d3910aef5155`.
- Missingness-ledger SHA256: `edd3c8269a62b4b2806bfb0ebe6aeb1a71e40e0306637d696a6d1a2298fbf461`.

The 29-feature catalog is still **PROVISIONAL**: Stage B may remove redundant or unstable candidates. Exact-close execution is **OPEN** because the completed bar at `t` is available only after finalization and does not guarantee a live fill at that same close.

## 13. Immediate continuation instruction

Continue with Stage B redundancy in the VS Code repository. Do not reopen or redesign Cells 0-14 unless an audit identifies a concrete defect. Treat the Decision Universe, validation contract, and Cell 14 feature computation as frozen. Treat current-deployment cost labels as PROVISIONAL counterfactuals, not historical actual P&L. Keep Final Test 2025-2026 sealed. Freeze the redundancy protocol before transparent OOF models with paired 5-session block-bootstrap comparisons.

## 14. Copy-ready continuation prompt

> Continue MES Quant Engine V1 from the VS Code repository and this handoff. Colab Cells 0-13 and repository Cell 14 are frozen and passed independent audits. Preserve all LOCKED contracts and the Final Test seal. Start Stage B redundancy using the canonical Cell 14 Development feature artifact. Fit every statistic on allowed walk-forward training history only; keep validation reporting separate; do not open Final Test; do not silently impute; and freeze thresholds, missingness policy, and a stable reduced feature set before model fitting. Current costs are deployment counterfactuals; historical fee reconstruction remains OPEN.

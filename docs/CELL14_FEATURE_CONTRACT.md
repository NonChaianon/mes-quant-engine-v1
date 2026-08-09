# Cell 14 — Development-only point-in-time feature contract

Policy version: `MES_V1_FEATURES_1.0`

Overall implementation status: **LOCKED computation and deterministic Development artifact / PROVISIONAL candidate catalog**.
The repository builder ran twice against the exact Cells 5/7/8 artifacts. Both runs produced the
same bytes, reconciled all 31,193 Development decisions, and passed independent formula, lineage,
missingness, source-time, and Final Test audits.

## Status register

- **LOCKED:** Target-independent inputs: Cell 5 bars, Cell 7 Decision Universe, Cell 8 assignments.
- **LOCKED:** Build TRAIN/VALIDATION only (31,193 rows); create no Final Test feature row.
- **LOCKED:** Completed bar ending at decision time may be used; maximum source time must be `<= t`.
- **LOCKED:** Exact 15-minute grid, complete bars, one instrument, and roll reset.
- **LOCKED:** No fill, imputation, pooled scaling, winsorization, PCA, or target encoding.
- **LOCKED:** Raw deterministic features and explicit missingness/status only.
- **LOCKED:** Canonical Cell 14 feature content SHA256
  `dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d`.
- **PROVISIONAL:** Candidate feature catalog; redundancy/stability audit may remove candidates later.
- **OPEN:** Execution delay and achievable fill price after the bar close finalizes.
- **OPEN:** Fold-specific transforms and model missing-value policy.
- **REJECTED:** Any Cell 10–13 label, cost, path, baseline, class-count, or P&L input.
- **REJECTED:** Gating feature rows by future label/path usability.
- **REJECTED:** Computing or inspecting features for 2025–2026 before model protocol freeze.

## Time semantics

For decision timestamp `t`, OHLCV with suffix `t` is the completed 15-minute bar ending at `t`.
The longest **fixed rolling** V1 lookback is 16 returns / 240 minutes. The separate session VWAP
proxy is session-to-date: it starts from the NYSE 09:30 bar source and may span 22 completed
15-minute bars / 330 elapsed minutes at the regular-session 15:00 decision. Every expected
timestamp in either window must exist, contain 15 active one-minute observations, and belong to
the same instrument.

`feature_lookback_start_utc` records the earliest source boundary used by any candidate on that
row: the earlier of `t-240m` and the NYSE session open. `feature_max_source_time_utc` must never be
later than `t`.

Using a completed bar at `t` is not predictive leakage. However, the close at `t` is a research
reference and not a guaranteed live fill; execution latency/fill realism remains OPEN.

## Candidate families

- Returns: 15-minute log return lags 0–3; momentum over 60, 120, and 240 minutes.
- Volatility: square-root sum of squared log returns over 60, 120, and 240 minutes.
- Bar shape: log range, log body, close location.
- Volume: `log1p` current volume and ratios versus strictly previous 60/240-minute means.
- VWAP_PROXY: session cumulative typical-price-by-volume proxy; never call it exact VWAP.
- Dynamics: lag-1 autocorrelation and normalized three-state sign entropy over 16 returns.
- Context: minutes since NYSE open, minutes to horizon-safe close, decision-slot cycle,
  weekday one-hot, and early-close flag.

Identifiers, partitions, fold roles, instrument ID, data-quality flags, and feature status fields
remain audit metadata and are not model-eligible features.

## Required artifacts

- `cell14_development_point_in_time_features_v1.parquet`
- `cell14_feature_registry_v1.csv`
- `cell14_feature_status_summary_v1.csv`
- `cell14_feature_missingness_ledger_v1.csv`
- `cell14_feature_audit.json`

Acceptance requires deterministic hashes, prefix/future-perturbation invariance, zero target input,
zero 2025+ rows, exact ID reconciliation with Cell 8 Development, and a recorded reason for every
missing feature.

Acceptance result: `31,193` rows, `29` candidate features, `30,197` fully usable rows, `996`
explicitly unusable rows, and `5,703` missing feature values with exactly one ledger record each.
No value is imputed. The canonical and replay runs are
`cell14_20260809T175203Z` and `cell14_20260809T175217Z`.

The synthetic acceptance suite must cover hand-calculated formulas, multi-decision session VWAP,
true prefix reconstruction, future append/perturbation, missing/partial/roll windows, regular and
early-close calendar rules, DST-aware UTC schedules, deterministic output hashes, and the Final
Test row firewall. The repository suite has `33/33` passing tests; real-data acceptance also
passed. Feature retention, scaling, missing-value treatment for modeling, and redundancy remain
separate downstream decisions.

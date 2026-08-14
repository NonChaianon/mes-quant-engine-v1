# LABEL_EXPOSURE_PRE_FIREWALL_V1

## Authority and scope

- GitHub authority: Issue #18.
- Baseline: `99b5f3302e28523293d31e7df49eb03cff466e2c`.
- Architecture: `MES_QUANT_TARGET_ARCHITECTURE_v2.2`, unchanged.
- A6 / Stage B V1.2 policy on baseline: `LOCKED`.
- Stage-B artifact execution: `DISABLED`.
- Observed label-access level for this acknowledgment: `L0`.
- Work classification: `TARGET_BLIND_WORK` / governance-evidence only.

This acknowledgment records historical exposure conservatively. It does not authorize a new realized-label read, Validation opening, Final-Test opening, model fit, feature selection, P&L inspection, or Edge Discovery Sprint execution.

For this task, the only label-related repository evidence inspected was an already-committed audit summary:

`reference/drive_evidence_v1/cell10_economic_label_audit.json`

at baseline `99b5f3302e28523293d31e7df49eb03cff466e2c` (Git blob `60162a2da84964d2da3b95b808e5c0a60806c075`). The underlying realized-label Parquet, Development label CSV, unusable-event Parquet, Validation outcomes, and Final-Test outcomes were not opened or recomputed.

## 1. Known historical facts

Project handoff/history records that realized-label information existed and had been exposed before the current formal label-access firewall/governance model. The historical discussion included the Cell 10 economic-label definition and aggregate Development label counts.

The exact time at which those facts were first viewed is not established here. This acknowledgment does not infer a timestamp that cannot be reconstructed from existing evidence.

The historical exposure means later research must not pretend the project began from a perfectly label-naive state. It does **not** grant any current L1/L2/L3 access and does not authorize reuse of realized outcomes outside their approved lane.

## 2. Repository-corroborated facts

The committed Cell 10 audit reports the following target contract:

- instrument: MES continuous active contract;
- decision price: close of the completed 15-minute bar at `decision_time`;
- exit price: close of the completed 15-minute bar at `decision_time + 60m`;
- horizon: 60 minutes / four future 15-minute bars;
- roll crossing through the horizon: not allowed;
- primary economic label rule: `LONG` if gross points exceed cost points, `SHORT` if gross points are below negative cost points, otherwise `NO_TRADE`;
- primary cost scenario: `CONSERVATIVE`, round-trip cost USD `4.97`, break-even `0.994` index points.

The same committed audit reports these Development-only aggregate counts:

```text
usable Development labels: 31,165
unusable Development labels: 28
LONG:     15,188
SHORT:    13,147
NO_TRADE:  2,830
```

It also records `25,685` TRAIN rows and `5,508` Validation rows in the Development partition, while `8,654` Final-Test rows remained sealed.

For the Cell 10 process, that audit reports:

```text
final_test_price_lookup_performed = false
final_test_outcomes_computed = false
final_test_label_distribution_inspected = false
model_fitted = false
```

These are repository-corroborated facts about the committed Cell 10 audit/process. They are not expanded into a claim about every historical human action outside the evidence actually preserved.

## 3. Unknown or not reconstructable without prohibited access

The following remain unknown and are not converted into PASS statements or inferred facts:

- whether individual row-level realized labels were historically viewed by a human;
- exactly which historical rows, if any, were visually inspected;
- the exact first-view timestamp of the aggregate label distribution;
- whether any historical exposure existed outside the evidence and handoff facts already preserved;
- any Validation outcome values not already present in allowed governance evidence;
- any Final-Test outcome or label distribution.

No underlying label dataset is reopened merely to reduce these unknowns.

## 4. Effect on accepted Stage B evidence

Historical pre-firewall exposure does not retroactively invalidate the accepted target-blind Stage B V1.2 evidence.

The reason is scope-specific: the accepted Stage B audit/lock path was performed under its target-blind firewall and recorded zero new realized-label rows, zero Validation outcome rows, zero Final-Test rows, zero Cell 8 assignment rows, and zero real Stage B production runs. Stage B V1.2 policy is now locked while execution remains disabled.

This statement is not a claim that the project was historically label-naive. It is a claim that the accepted Stage B target-blind result was produced without using those realized outcomes in the Stage B decision path.

## 5. Access classification and safety counters for Issue #18

Reading the already-committed aggregate audit above is allowed governance evidence under Issue #18 and does not reopen the underlying realized-label rows.

```text
OBSERVED_LABEL_ACCESS_LEVEL              L0
new realized TRAIN label rows opened     0
Validation outcome rows opened           0
Final Test rows/outcomes opened          0
P&L / future-return rows opened           0
Cell 8 assignment rows opened            0
real Stage B production runs              0
Phase B/C/D production implementations    0
```

No L1, L2, or L3 access was exercised by this acknowledgment.

## 6. Governance consequence

After independent acceptance and merge of this acknowledgment:

1. the historical exposure record is frozen as the pre-firewall baseline;
2. the next task is the one-page `EXPLORATORY LANE V1` charter;
3. only after that charter is accepted should the Edge Discovery Sprint 1 protocol be frozen;
4. realized TRAIN-label access for exploration, when explicitly begun later, will be L1 and must be logged as `TARGET_AWARE_EXPERIMENT` with an experiment ID;
5. Validation and Final Test remain unopened until their separately governed gates.

This document does not begin the Exploratory Lane or Edge Sprint.

## Final verdict

`LABEL_EXPOSURE_PRE_FIREWALL_V1_READY_FOR_INDEPENDENT_REVIEW`

# Test 3 Protocol and Project Budget — Owner Co-Ratification Record V1

Record ID: `MES_TEST3_PROTOCOL_BUDGET_RATIFICATION_V1`

Status: **OWNER CO-RATIFIED / TEXT FROZEN / NO IMPLEMENTATION OR DATA AUTHORITY**

Owner decision date: `2026-08-24` (`Asia/Bangkok`)

Ratified commit: `7c17b292958aeb8252f9c0911ef7028b6071cdbb`

Repository base at ratification: `fe10fb1497e5df919702cf4ff294c4ebf8669b95`

## 1. Co-ratified artifacts

The Owner co-ratified both artifacts together at the same exact commit:

| Identity | Path | SHA-256 at ratified commit |
| --- | --- | --- |
| `MES_TEST3_RV60_HAR_RISK_EDGE_V1` | `docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md` | `974ff7942f17174a2fbd855e42b591b2c0dad123ddae62d4436b418e68d4c826` |
| `MES_PROJECT_TARGET_SPACE_BUDGET_V1` | `docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md` | `4e939608d0753c608675510c4e449cdac7d452022b0ec9d632fd989f045f58ed` |

This additive record supplies the external commit identity required by the project-budget
co-ratification rule. It does not modify either frozen artifact. Their internal
status lines read exactly `DRAFT COMPLETE — OWNER RATIFICATION REQUIRED` and
`DRAFT COMPLETE — OWNER CO-RATIFICATION REQUIRED`; those status lines are superseded for
these exact bytes only by this record.

## 2. Owner statement

The Owner stated:

> ผม co-ratify `MES_TEST3_RV60_HAR_RISK_EDGE_V1`
> (`docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md`) และ
> `MES_PROJECT_TARGET_SPACE_BUDGET_V1`
> (`docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md`) พร้อมกันที่ exact commit
> `7c17b292958aeb8252f9c0911ef7028b6071cdbb` วันที่ 2026-08-24 โดยยอมรับอย่างชัดแจ้ง:
> final OHLCV target-space budget, [ชื่อ stage/disposition ตามเอกสาร], genuine-data
> fail-closed rule และ single proven-defect repair boundary — การ ratify นี้ freeze
> ข้อความเท่านั้น ไม่อนุญาต implementation, target access, fit, Validation หรือ Final Test
> ขั้นถัดไปที่มีสิทธิ์ขอคือ Test 3 L0 code-only ภายใต้ authorization แยก

## 3. Canonical resolution of the incorporated names

The bracketed reference in the Owner statement incorporates the exact names and semantics
from the two co-ratified artifacts; it does not create a new choice or amend them:

- the newly introduced target-blind stage is `G2-P TRAIN predictor-domain preflight`;
- the full separately authorized stage sequence is `L0 code-only`, `G2 metadata-only`,
  `G2-P TRAIN predictor-domain preflight`, `G3-P TRAIN pre-fit`, and `G3-F one-shot`;
- the terminal dispositions are `INTERESTING_ENOUGH_FOR_CONFIRMATORY_PROTOCOL`,
  `NOT_INTERESTING_ENOUGH`, `UNDERPOWERED_STOP`, and `INVALID_EVIDENCE`;
- the non-terminal row statuses are `TARGET_USABLE`, `TARGET_UNUSABLE`,
  `PREDICTOR_USABLE`, and `PREDICTOR_UNUSABLE`; only the exact `*_USABLE` statuses enter
  the frozen common eligibility mask;
- the fail-closed domain reason codes include `TARGET_ZERO_VARIANCE`,
  `PREDICTOR_NONFINITE`, and `PREDICTOR_NONPOSITIVE`;
- the `TARGET_SPACE_003` state becomes `LOCKED / RESERVED` upon this co-ratification; later
  valid states are `CONSUMED` or `CLOSED_UNCONSUMED` exactly as defined by the budget;
- outer Validation remains `UNOPENED`, Final Test remains `SEALED`, and live execution
  remains `DISABLED`. Fold-level OOF `VALIDATION` roles inside `WF_2022` and `WF_2023` are
  not outer Validation access.

## 4. Frozen effect and authority boundary

This co-ratification freezes the exact scientific question, source lineage, target/horizon,
predictors, harmonic, folds, transform/back-transform, common eligibility and reason-code
dispositions, `RVBASE001`/`RVHAR001`, four-fit budget, QLIKE contract, bootstrap contract,
numerical policy, dependence/ESS contract, continuation gates, final OHLCV-only target-space
budget, genuine-data fail-closed rule, and single proven-defect repair boundary contained in
the two ratified artifacts.

It authorizes none of the following:

- implementation or repository code changes;
- metadata or numeric data access;
- target/path reads or `RV_FWD_60` construction;
- model fit, forecast, QLIKE evaluation, bootstrap, or scientific output;
- outer Validation or Final-Test access;
- merge of Draft PR #47, live execution, database work, or broker connection.

The next eligible request is **Test 3 L0 code-only** under a separate exact Owner
authorization. Before code is written, the Owner must choose personal implementation or
authorize Codex. Claude remains read-only unless the Owner explicitly changes that role.

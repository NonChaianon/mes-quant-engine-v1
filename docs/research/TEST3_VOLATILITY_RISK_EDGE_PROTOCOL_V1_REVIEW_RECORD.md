# Test 3 Volatility-First / Risk Edge Protocol V1 — Review Record

Status: **REVIEW COMPLETE — OWNER RATIFICATION PENDING**

Protocol: `docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md`

Base commit: `fe10fb1497e5df919702cf4ff294c4ebf8669b95`

## 1. Review roles and boundary

- Owner: approved the volatility-first / Risk Edge direction and retained implementation
  authority.
- Codex: evidence extraction, protocol author, and chair.
- Claude Code: independent read-only adversarial reviewer.

Both reviewers read `CRASH_MEMORY.md` before project work. Review was documentation-only.
No real numeric artifact was opened, no target was constructed, and no model was fit.

## 2. Evidence checked

The review reconciled the proposal against:

- `docs/CELL14_FEATURE_CONTRACT.md`;
- `docs/handoff/MES_V1_HANDOFF.md`;
- `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md`;
- `src/mes_quant/features/builder.py`;
- `src/mes_quant/exploration/test2_request_set.py`;
- `src/mes_quant/exploration/test2_stats.py`;
- `src/mes_quant/exploration/l1_lr001.py`.

## 3. Material challenges and resolutions

### 3.1 One-minute source and target off-by-one

Claude initially concluded that no frozen one-minute source existed and that bar index `t`
was already known at decision time. That conclusion was rejected after direct evidence
review:

- Test 2 protocol Section 4.2 pins the decoded Cell 2 one-minute content and its SHA;
- Cell 12 requests raw one-minute bars at offsets `0..59` after the decision reference;
- Cell 12 proves offset-59 close equals the frozen `+60m` endpoint with zero mismatches;
- the completed 15-minute Cell 10 close at `t` is a separate entry reference.

Claude withdrew both objections. The resolved target uses the entry-reference close plus
60 future minute closes to create exactly 60 post-decision returns.

### 3.2 Early-close harmonic

The initial idea of reusing Cell 14 `decision_slot_sin/cos` was rejected. Its implementation
uses a fixed `decision_slot_count = 22`, which is not a session-specific early-close period.
The protocol now freezes one deterministic harmonic derived from locked open/close calendar
metadata, yielding 22 normal-session and 10 standard early-close horizon-safe slots.

### 3.3 Eligibility and purge ordering

The review required an explicit ordering. The protocol now seals all outer-TRAIN request
keys and target statuses before the common model eligibility mask, forbids non-TRAIN target
construction, uses one identical eligible set for both models, and asserts
`max(train.label_end_time) < min(holdout.decision_time)` at each walk-forward boundary.

### 3.4 Dependence audit and ESS

The proposed 1,000-per-fold / 2,000-pooled ESS gate was rejected as a Test 2 threshold
borrowed without a Test 3-specific power derivation. It was removed. The final protocol:

- derives the IID-overlap null `max(1-k/4, 0)` for lags `1..8`;
- reports observed excess and descriptive ESS;
- uses paired session-block inference for the scientific confidence gate.

The overlap values are null references, not acceptance floors.

### 3.5 Metric unification and Jensen correction

QLIKE is the sole gate loss for materiality and confidence. The materiality formula is
written explicitly and uses a 10% pooled row-weighted reduction. Both models use the same
fold-local Duan smearing method, with model-specific factors derived only from their own
fold-TRAIN residuals.

### 3.6 Scope and downstream dependency

Risk Edge is the only allowed claim; economic and directional claims are excluded. The
current Test 4 concept is void if Test 3 has no winner, preventing a failed Test 3 from being
reframed after result inspection.

### 3.7 WF_2023 upstream count reconciliation

Final file review found that the Test 2 protocol described `5,474` as the WF_2023 count
before eligibility, while the authoritative Cell 8 audit, handoff, and fold CSV record
`5,476`. The value `5,474` is the separate full-29-feature usable count documented in the
Stage B redundancy contract. This branch corrects the Test 2 transcription and its pooled
pre-eligibility maximum from `10,984` to `10,986`; no experiment result or artifact changes.

### 3.8 Owner adversarial read and ratification amendments

The Owner read both draft files section by section and reported five non-blocking findings.
The ratification candidate resolves all five:

1. finite zero forward variance now has exact code `TARGET_ZERO_VARIANCE` and stops the
   complete run before eligibility or fit rather than being silently excluded;
2. source inspection confirmed Test 2 uses `np.quantile(..., 0.05)` and seed namespace
   `MASTER_SEED + 90000 + L`; the protocol now distinguishes those Test 2 choices from
   Cell 13's two-sided `p025/p975` outputs;
3. project-level target-space finality is preserved in the separate companion
   `TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md` and must be co-ratified;
4. the protocol records `TARGET_SPACE_003` explicitly in the project search ledger;
5. `V60/V120/V240` are labeled scale documentation, while only the `X` transforms enter
   the ordered model designs.

The Owner also surfaced the deliberate fail-closed predictor rule: any present nonpositive
Cell 14 volatility stops G3-P before a fit rather than dropping a row. The ratification
clause now makes acceptance of both zero-variance stop rules explicit. Claude's amendment
review found that the predictor rule still lacked symmetric machine codes; the final text
therefore adds `PREDICTOR_NONFINITE` and `PREDICTOR_NONPOSITIVE`, both mapped explicitly to
whole-run `INVALID_EVIDENCE` before eligibility or fit.

Claude re-read the amended zero-target, predictor, disposition, ratification, and companion
budget sections and returned `APPROVE_AMENDMENTS`; no blocker/high remained.

## 4. Claude final position

After the factual correction and design amendments, Claude reported that the only remaining
blocker was the absence of a written protocol in the repository. Final file review then found
the WF_2023 transcription described in Section 3.7. The source audit governs, and the count
is corrected to `5,476`. Technical review found no remaining blocker/high issue after that
correction.

The amended protocol and companion project-budget artifact are complete enough for Owner
ratification. They remain unauthorized for implementation or data access until that
ratification is explicit.

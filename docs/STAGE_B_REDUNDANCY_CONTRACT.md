# Stage B — Feature redundancy and stability contract

Policy version: `MES_V1_REDUNDANCY_1.2`

Policy status: **PROVISIONAL**

Upstream status:

- Cell 14 computation/data artifact: **LOCKED**
- Cell 14 29-feature candidate catalog: **PROVISIONAL**
- Final Test 2025–2026: **SEALED**

---

## 1. Why v1.2 exists

Stage B V1.0 was reopened after audit identified a policy-enforcement defect:

- the Python contract reported `LOCKED_EXECUTABLE`,
- while the governing Markdown contract still reported `PROVISIONAL`.

Therefore executable policy could pass even though the governing research
contract had not actually been locked.

V1.1 corrected both:

1. the research methodology, and
2. the mechanism that binds executable policy to the governing document.

No Stage B result produced under the incomplete V1.0 implementation may be
used to KEEP or DROP a feature.

V1.2 is the bounded remediation of `V1_2_LOCK_BREAKER_4` and
`V1_2_LOCK_BREAKER_5` proven at baseline
`a5d3f40e7edc26d950010401654ce4d6b7822e86`.

It removes generic numerical rank/SVD deletion authority. Phase-A semantic
KEEP/DROP authority remains unchanged. This provisional remediation does not
lock V1.2 and does not implement the Phase-B production execution path.

---

## 2. Objective

Stage B reduces the 29 Cell 14 candidate features to a stable, explainable,
target-blind candidate set without:

- using Final Test,
- using labels,
- using P&L,
- using cost outcomes,
- using future path outcomes,
- selecting on outer-validation performance,
- silently filling missing values,
- treating low pairwise correlation as proof of independence.

Stage B diagnoses:

- exact semantic/algebraic redundancy,
- exact set-level linear dependency,
- deterministic representation relationships,
- empirical pairwise redundancy,
- clustering structure,
- feature availability,
- cohort sensitivity,
- descriptive stability.

Stage B does **not** claim profitability.

Stage B also does not claim that absence of linear, rank, correlation, or
monotonic redundancy proves general statistical independence.

---

## 3. Contract-document integrity gate

After this policy is formally locked, the executable Python contract must pin
the SHA256 of this exact Markdown document.

Stage B production execution is allowed only when all are true:

1. Python policy version equals the policy version in this document.
2. Python policy status is `LOCKED_EXECUTABLE`.
3. This Markdown document's `Policy status` is `LOCKED_EXECUTABLE`.
4. The semantic registry top-level `registry_status` is `LOCKED_EXECUTABLE`.
5. The semantic registry top-level `policy_version` equals the policy version
   in this document.
6. The semantic registry top-level `source_contract` equals
   `docs/STAGE_B_REDUNDANCY_CONTRACT.md`.
7. SHA256 of the committed Markdown bytes equals the SHA256 pinned in Python.
8. Required upstream control artifacts and hashes pass.
9. Required semantic-registry SHA256 equals the SHA256 pinned in Python.
10. Dedicated Stage B tests pass.

Any post-lock policy change requires:

- documented defect/change reason,
- policy version bump,
- updated Markdown contract as applicable,
- updated semantic registry as applicable,
- repeated independent Markdown ↔ JSON joint consistency audit,
- new committed Markdown SHA256,
- new committed semantic-registry SHA256,
- Python-contract update,
- dependent-test rerun.

The document hash is an accidental-drift and reproducibility control.

It is not claimed to be a security control against intentional coordinated
modification of both policy and pinned hash.

### 3.1 Contract hash byte policy

The contract hash is computed from the exact committed bytes of:

`docs/STAGE_B_REDUNDANCY_CONTRACT.md`

The repository currently declares:

`* -text`

in `.gitattributes`.

Git line-ending normalization is therefore disabled for tracked files under
the current repository byte policy.

Stage B V1.2 does not alter this repository-wide policy.

Changing `.gitattributes` belongs to a separate repository-policy migration
because existing frozen/source hashes are byte-sensitive.

The implementation must hash raw committed file bytes.

It must not perform:

- newline normalization,
- whitespace normalization,
- Unicode normalization,
- text re-encoding

before hashing.

Never pin a hash calculated from:

- an uncommitted draft,
- copied chat text,
- an editor-transformed representation.

A clean-checkout hash must reproduce the pinned hash before real-data
execution.

### 3.2 Cross-control authority and semantic consistency

The Stage B controls have distinct responsibilities.

The Markdown contract:

`docs/STAGE_B_REDUNDANCY_CONTRACT.md`

is the governing human-readable source for:

- research methodology,
- methodological constraints,
- rationale,
- interpretation.

The machine-readable semantic registry:

`configs/v1/stage_b_semantic_registry_v1.json`

is the authoritative executable source for semantic-check parameters.

Those executable semantic parameters include at minimum:

- `check_id`
- `check_type`
- `features`
- `dependent_features`
- `determining_features`
- `scope`
- `decision_effect`
- `implementation_key`
- `dependency_group`
- `required_drop_count`
- `protect_determining_features`

Analyzer/runtime code must consume these semantic parameters from the locked
semantic registry.

It must not maintain an independent duplicate semantic-policy table.

`tests/test_redundancy.py` is not a third policy authority.

Tests validate:

- schema,
- structural invariants,
- implementation behavior,
- control consistency,
- safety-critical policy sentinels.

A test may contain an explicitly identified safety sentinel where required to
detect an accidental safety-critical registry change, but analyzer/runtime
policy must still be derived from the locked registry.

SHA256 controls prove that exact committed bytes have not changed.

They do not prove that the Markdown contract and semantic registry express the
same policy.

Therefore an independent:

`MARKDOWN_JSON_JOINT_CONSISTENCY_AUDIT`

is mandatory:

1. before the first V1.2 lock, and
2. after every later Stage B policy version bump before new hashes are pinned.

The joint audit must verify that the executable semantic parameters in the
registry are consistent with the governing methodology and decisions in the
Markdown contract.

If the Markdown and semantic registry disagree:

- Stage B remains non-executable,
- new locked hashes must not be pinned,
- real-data Stage B execution is forbidden.

This control closes the failure class where two individually valid hashed
policy files disagree semantically.

---

## 4. Allowed inputs

Stage B may read only target-independent Development inputs required for
redundancy analysis:

- canonical Cell 14 Development point-in-time feature artifact,
- canonical Cell 14 feature registry,
- Cell 8 walk-forward fold-role assignments,
- upstream release/control hashes required to validate those artifacts.

Cells 9–13 are forbidden inputs.

Every field containing any of the following is forbidden:

- target,
- label,
- future return,
- future price,
- gross P&L,
- net P&L,
- cost outcome,
- execution outcome,
- future path outcome.

No 2025–2026 feature or outcome row may be opened or analyzed.

Required audit count:

`Final Test rows opened = 0`

---

## 5. Canonical feature identity and order

The canonical Cell 14 feature registry is the **single source of truth** for:

- candidate feature names,
- candidate count,
- canonical feature order,
- formula metadata,
- lookback metadata,
- feature-family metadata required by Stage B.

Canonical candidate count:

`29`

Stage B must not define an independent hard-coded 29-feature list.

The production feature artifact must match the canonical registry in:

- membership,
- count,
- order.

Any mismatch is a hard failure.

Every feature pair written to an artifact uses canonical orientation:

`feature_a` precedes `feature_b` in canonical registry order.

Prototype aliases and historical names are forbidden in production policy.

Canonical 15-minute return-lag names are:

- `ret_log_15m_lag0`
- `ret_log_15m_lag1`
- `ret_log_15m_lag2`
- `ret_log_15m_lag3`

Canonical weekday names are:

- `weekday_0`
- `weekday_1`
- `weekday_2`
- `weekday_3`
- `weekday_4`

---

## 6. Train-only rule

Every empirical Stage B analysis runs separately inside TRAIN history for
exactly these expanding walk-forward folds:

- `WF_2022`
- `WF_2023`
- `WF_2024`

implemented through:

- `role_wf_2022`
- `role_wf_2023`
- `role_wf_2024`

Outer-validation rows are reporting-only.

Outer-validation values may not select:

- thresholds,
- dependencies,
- substitutes,
- representatives,
- clusters,
- feature count,
- KEEP/DROP decisions,
- overlay definitions.

Semantic/algebraic verification is also TRAIN-scoped.

There is no all-Development semantic-check exception.

---

## 7. Expanding-fold dependence warning

The three TRAIN folds are expanding windows.

Conceptually:

`WF_2022 ⊂ WF_2023 ⊂ WF_2024`

Therefore they are not three independent replications.

The folds share substantial historical observations.

Statements such as:

- "stable across three folds",
- "passes every fold"

mean robustness across expanding histories, not three independent pieces of
evidence.

The same interpretation applies to later all-fold consistency requirements,
including empirical redundancy and zero-variance checks.

---

## 8. Missingness and common-cohort policy

Primary empirical redundancy statistics use:

`FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD`

Within each TRAIN fold, this cohort contains rows where all 29 canonical
candidate features are available.

It is a controlled research comparison cohort.

It is **not automatically the future production/modeling cohort**.

Rejected methods:

- median fill,
- forward fill,
- silent row deletion,
- pooled future-aware scaling,
- future-fitted imputation.

Any future imputation proposal requires a separate point-in-time policy.

---

## 9. Observed Development missingness context

Before V1.1 lock, canonical Development coverage was inspected explicitly.

Overall full-29 coverage:

`30,197 / 31,193 = 96.807%`

Missingness is not uniformly distributed through history and must not be
assumed MCAR.

### 9.1 Full-29 coverage by year

Observed canonical Development coverage:

- 2019: `2,955 / 3,632 = 81.360132%`
- 2020: `5,300 / 5,535 = 95.754291%`
- 2021: `5,465 / 5,532 = 98.788865%`
- 2022: `5,510 / 5,510 = 100.000000%`
- 2023: `5,474 / 5,476 = 99.963477%`
- 2024: `5,493 / 5,508 = 99.727669%`

The project therefore records explicitly that missingness is concentrated
disproportionately in earlier history.

### 9.2 Shared 240-minute availability condition

The following five 240-minute features each contain exactly 983 missing rows:

- `momentum_log_240m`
- `realized_vol_240m`
- `sign_entropy_240m`
- `return_autocorr_lag1_240m`
- `volume_ratio_prev_240m`

Those 983 missing rows are the same rows for all five features:

- ANY 240m feature missing = `983`
- ALL five 240m features missing = `983`
- partial disagreement = `0`

Observed 240-minute missing rows by year:

- 2019: `677`
- 2020: `222`
- 2021: `67`
- 2022: `0`
- 2023: `2`
- 2024: `15`

Observed feature-status composition on those 983 rows:

- `PARTIAL_LOOKBACK_BAR`: `908`
- `PARTIAL_LOOKBACK_BAR|SESSION_VWAP_INPUT_INVALID`: `50`
- `MISSING_LOOKBACK_BAR|SESSION_VWAP_INPUT_INVALID`: `20`
- `MISSING_LOOKBACK_BAR`: `5`

These 983 rows are interpreted as one shared FIXED 240-minute-window
availability condition across the five listed 240-minute features, not five
independent missingness events.

Stage B must preserve that distinction in its coverage audit.

Canonical target-blind factual validation also found shorter-window
missingness overlapping this same 983-row component.

Observed missing-row counts are:

- `momentum_log_60m`: `59`
- `realized_vol_60m`: `59`
- `ret_log_15m_lag0`: `13`
- `ret_log_15m_lag1`: `24`
- `ret_log_15m_lag2`: `33`
- `ret_log_15m_lag3`: `48`

The union of rows where at least one of the four 15-minute return lags is
unavailable is `59`; this exceeds the largest individual lag missing count of
`48` because the four lag-level missingness masks are not strictly nested.

For both the momentum 60-minute identity and the realized-volatility
60-minute identity, the complete-case identity-availability mask excludes
exactly the same `59` Development rows.

All `59` identity-unavailable rows are contained within the shared `983`
240-minute incomplete rows:

- identity-unavailable rows intersecting the shared 240-minute set: `59`
- identity-unavailable rows outside the shared 240-minute set: `0`

These are overlapping feature-level missingness counts inside the already
identified 983-row component.

They are not an additional third group of full-29 incomplete Development
rows.

These observations do not authorize Stage B to:

- delete early history,
- rewrite Cell 7/8,
- forward-fill missing windows,
- create an arbitrary warm-up exclusion.

Such upstream changes would require a separate versioned upstream review.

### 9.3 Complete full-29 missingness reconciliation

Canonical target-blind pre-lock factual validation reconciled every
Development row excluded from the full-29 complete-case cohort.

Total full-29 incomplete Development rows:

`996`

The observed decomposition is exactly:

- shared FIXED 240-minute-window incomplete rows: `983`
- SESSION_TO_DATE session-VWAP-only incomplete rows: `13`

Therefore:

`996 = 983 + 13`

The `59` rows unavailable to both 60-minute identity validations are a subset
of the same `983`-row component.

They therefore overlap the first component of this decomposition and do not
add a third component or increase the total beyond `996`.

The 983-row component is the shared availability condition already documented
in §9.2.

The remaining 13 rows:

- all occur in calendar year `2020`,
- have only `session_vwap_proxy_deviation` missing,
- all have canonical Cell 14 feature status
  `SESSION_VWAP_INPUT_INVALID`.

`session_vwap_proxy_deviation` is the only canonical
`SESSION_TO_DATE` candidate among the 29 Cell 14 candidate features.

Therefore:

`UNEXPLAINED_FULL_29_INCOMPLETE_ROWS = 0`

Observed full-29 missingness is fully reconciled by the feature-availability
structures actually observed:

1. the shared FIXED 240-minute-window availability condition, and
2. SESSION_TO_DATE VWAP-input validity.

Stage B does not infer from row-count equality alone that the 13 rows were
caused by degraded-day classification or any other upstream condition whose
causal relationship has not been established.

The 13 rows are 13 individual decision slots.

They must not be described as evidence that an entire market regime or an
entire trading period is missing.

---

## 10. Fold-level coverage gate

Minimum common-cohort coverage required for automatic empirical Stage B
decisions is:

`MIN_COMMON_COHORT_COVERAGE_PER_FOLD = 0.90`

This threshold is explicitly data-informed.

Before V1.1 lock, canonical TRAIN-only coverage was measured:

- `WF_2022`: `13,720 / 14,699 = 93.339683%`
- `WF_2023`: `19,230 / 20,209 = 95.155624%`
- `WF_2024`: `24,704 / 25,685 = 96.180650%`

All canonical TRAIN folds pass.

The project does not claim that the 90% threshold was selected without prior
knowledge of Development coverage.

Provenance classification:

`DATA_INFORMED_BEFORE_FORMAL_V1_1_EXECUTION`

Production Stage B must recompute coverage from canonical inputs.

If any canonical TRAIN fold unexpectedly falls below 90%:

- Stage B fails before final decisions are released,
- the condition is treated as upstream/reproducibility drift,
- it is not converted into OPEN,
- automatic empirical deletion does not continue.

Because the TRAIN folds are nested, passing all three folds must not be
described as three independent confirmations.

---

## 11. Within-fold yearly concentration review

Fold-level coverage alone does not detect historical concentration of
missingness.

Stage B therefore also reports full-29 common-cohort coverage by calendar year
within applicable TRAIN history.

Review threshold:

`LOW_YEAR_COMMON_COHORT_COVERAGE_REVIEW = 0.90`

This uses the same 90% value as a **review threshold only**.

It is not a yearly hard failure gate.

A year below 90% must be flagged:

`LOW_YEAR_COMMON_COHORT_COVERAGE_REVIEW`

Canonical pre-lock Development evidence indicates that 2019 triggers this
review flag.

The flag:

- does not remove the year,
- does not change the Decision Universe,
- does not authorize imputation,
- does not automatically block Stage B,
- does not automatically cause a feature DROP.

Its purpose is to make cohort concentration visible before empirical
compression decisions are accepted.

### 11.1 Required yearly concentration acknowledgment

A yearly concentration flag must not become an alert that is produced and
ignored.

If any TRAIN-history calendar year triggers:

`LOW_YEAR_COMMON_COHORT_COVERAGE_REVIEW`

the Stage B audit must set:

`YEARLY_CONCENTRATION_REVIEW_REQUIRED = true`

Before Stage C may open labels, an independent target-blind Stage B review
must acknowledge:

- which year or years triggered the flag,
- observed full-29 coverage,
- major missingness source groups,
- whether missingness is concentrated in a known shared availability
  condition,
- that no year was silently deleted,
- that no imputation or upstream rewrite was introduced.

Required audit state:

`YEARLY_CONCENTRATION_REVIEW_STATUS = ACKNOWLEDGED`

when review is required.

This acknowledgment may not use:

- labels,
- validation performance,
- P&L,
- Final Test,
- future-return information.

The acknowledgment records awareness of the cohort limitation.

It does not permit discretionary feature selection.

---

## 12. Redundancy evidence hierarchy

Stage B must never equate pairwise low correlation with feature independence.

Evidence precedence is:

1. explicit exact semantic/algebraic dependency,
2. exact set-level linear dependency,
3. locked empirical pairwise HARD redundancy,
4. clustering / REVIEW evidence,
5. descriptive stability evidence.

Higher-precedence evidence governs interpretation of lower-precedence evidence.

Lower-precedence evidence remains visible.

Evidence precedence does not itself grant member-level KEEP/DROP authority.
Generic exact set-level evidence is dispositioned only by the §22 firewall.

A pair may legitimately be:

`PAIRWISE_DISTINCT`

while its containing group is:

`SEMANTIC_HARD_REDUNDANCY`

This is not an artifact contradiction.

---

## 13. Machine-readable semantic dependency registry

Required semantic checks must exist in:

`configs/v1/stage_b_semantic_registry_v1.json`

They may not exist only as prose.

The Markdown contract remains the governing human-readable research
methodology and rationale.

The semantic registry is the authoritative executable source for
semantic-check parameters.

Analyzer/runtime code must consume those semantic parameters from the locked
registry and may not maintain an independent duplicate semantic-policy table.

The top-level semantic-registry object must contain at minimum:

- `policy_version`
- `registry_status`
- `source_contract`
- `semantic_checks`

For V1.2:

- before lock, `registry_status` must equal `PROVISIONAL`,
- after a later, separately authorized status-only promotion under §46.1
  step 9,
  `registry_status` must equal `LOCKED_EXECUTABLE`,
- `policy_version` must equal `MES_V1_REDUNDANCY_1.2`,
- `source_contract` must equal
  `docs/STAGE_B_REDUNDANCY_CONTRACT.md`.

A mismatch in any of these control fields is a production-gate failure.

Every semantic-check entry must contain at minimum:

- `check_id`
- `check_type`
- `features`
- `dependent_features`
- `determining_features`
- `scope`
- `decision_effect`
- `implementation_key`
- `dependency_group`
- `required_drop_count`
- `protect_determining_features`
- `rationale`

### 13.1 Registry field rules

`features`:

- must be a JSON array,
- must be non-empty.

`dependent_features`:

- must always be a JSON array,
- may be empty,
- must not use null to represent absence of a directional dependent feature.

`determining_features`:

- must always be a JSON array,
- may be empty,
- must not use null to represent absence of a directional determining basis.

`required_drop_count`:

- must be an integer greater than or equal to zero for locked exact or
  representation checks according to the check-type invariant table,
- may be null only for a permitted empirical check type whose outcome is
  determined later by locked empirical evidence.

`protect_determining_features`:

- must be boolean.

`dependency_group`:

- is one check-level group identifier,
- must not contain the reserved delimiter `|`.

### 13.2 Check-type structural invariants

The following table is governing V1.2 structural policy:

| `check_type` | `dependent_features` | `determining_features` | `required_drop_count` |
|---|---|---|---:|
| `EXACT_LINEAR_DERIVED_IDENTITY` | non-empty | non-empty | `1` |
| `EXACT_NONLINEAR_DERIVED_REPRESENTATION` | non-empty | non-empty | `0` |
| `EXACT_AFFINE_DERIVED_IDENTITY` | non-empty | non-empty | `1` |
| `EXACT_AFFINE_DEPENDENCY` | empty | empty | `1` |
| `PAIRED_NONLINEAR_REPRESENTATION` | empty | empty | `0` |
| `EMPIRICAL_NEAR_IDENTITY` | empty | empty | `null` |

Any registry entry whose `check_type` has no governing row above must fail
closed.

It may not silently inherit behavior from another type.

### 13.3 Test responsibility

Tests must read semantic parameters from the registry rather than recreate an
independent executable parameter table.

Tests must verify:

- registry schema,
- check-type structural invariants,
- every required check has an implementation,
- every implementation is callable,
- every feature name resolves to the canonical Cell 14 registry,
- every required check appears in the semantic ledger,
- no required check silently disappears,
- registry SHA matches the Python contract,
- unknown `check_type` fails closed.

Tests are not a third policy authority.

An explicitly identified safety-critical sentinel is permitted where required
to make an accidental registry change fail loudly, while analyzer/runtime
policy remains registry-derived.

---

## 14. Semantic-basis protection

A feature may become:

`SEMANTIC_BASIS_PROTECTED`

only through the locked semantic registry.

The protected BASE set is derived mechanically as:

the union of `determining_features` from only those registry entries where:

`protect_determining_features = true`

Protection must not be inferred from every `determining_features` field.

Analyzer/runtime code must not maintain an independent hard-coded protected
feature list.

Protected BASE features may:

- participate in correlations,
- appear in clustering,
- act as retained empirical substitutes,

but may **not** be automatically removed later by:

- Phase-C empirical HARD reduction,
- the BASE zero-variance deletion rule.

This prevents a later approximate or degeneracy rule from silently undoing the
information basis deliberately selected by an earlier exact semantic rule.

Protection applies to BASE Stage B reduction.

A future model-specific overlay may impose an additional restriction only
under its separately locked overlay policy and must record explicitly that it
removes a BASE-protected feature.

### 14.1 V1.2 protected-set safety sentinel

V1.2 preserves the approved V1.1 semantic policy. Registry derivation is
therefore expected to
produce exactly these six canonical protected features:

- `ret_log_15m_lag0`
- `ret_log_15m_lag1`
- `ret_log_15m_lag2`
- `ret_log_15m_lag3`
- `minutes_since_nyse_open`
- `early_close_session`

The safety sentinel must also verify that the protected set does **not**
contain:

- `weekday_0`
- `weekday_1`
- `weekday_2`
- `weekday_3`
- `weekday_4`
- `momentum_log_60m`
- `realized_vol_60m`
- `minutes_to_horizon_safe_close`

For V1.2:

- §15.1 has `protect_determining_features = true`,
- §15.3 has `protect_determining_features = true`,
- §15.2 has `protect_determining_features = false`,
- §15.4 has `protect_determining_features = false`,
- §15.5 has `protect_determining_features = false`,
- §15.6 has `protect_determining_features = false`.

The weekday dependency must remain unprotected because §15.4 explicitly
authorizes one registry-directed Phase-A semantic reference dummy to be
removed. That Phase-A authority does not grant generic Phase-B rank/SVD
deletion authority.

The sentinel is a safety control.

It does not replace registry-derived analyzer/runtime policy.

---

## 15. Required semantic checks

### 15.1 Momentum 60-minute telescoping identity

Check type:

`EXACT_LINEAR_DERIVED_IDENTITY`

Canonical identity:

`momentum_log_60m`

equals:

`ret_log_15m_lag0 + ret_log_15m_lag1 + ret_log_15m_lag2 + ret_log_15m_lag3`

within locked floating-point identity tolerance.

Semantic direction:

dependent feature:

`momentum_log_60m`

determining features:

- `ret_log_15m_lag0`
- `ret_log_15m_lag1`
- `ret_log_15m_lag2`
- `ret_log_15m_lag3`

For this dependency:

- k = 5
- retained information dimension = 4
- required drop count = 1

V1.2 preserves the V1.1 semantic resolution:

- KEEP all four canonical 15-minute return lags,
- `DROP_REDUNDANT` `momentum_log_60m`.

All four determining return lags are:

`SEMANTIC_BASIS_PROTECTED`

for BASE reduction.

No generic representative tie-break is used.

---

### 15.2 Realized-volatility 60-minute deterministic representation

Check type:

`EXACT_NONLINEAR_DERIVED_REPRESENTATION`

Canonical Cell 14 definition:

`realized_vol_60m`

equals:

`sqrt(ret_log_15m_lag0^2 + ret_log_15m_lag1^2 + ret_log_15m_lag2^2 + ret_log_15m_lag3^2)`

within locked floating-point tolerance.

There is:

- no division by 4,
- no sample-standard-deviation divisor,
- no ddof adjustment,
- no annualization factor

in the canonical V1 formula.

This feature contains no new raw information beyond the four return lags, but
it is a nonlinear representation.

V1.2 does not automatically drop it in BASE because representation usefulness
can depend on later model class.

Therefore:

`required_drop_count = 0`

The ledger must classify it as a retained deterministic nonlinear
representation, not independent raw information.

### Known estimator limitation

`realized_vol_60m` is constructed from only four completed 15-minute return
observations.

It is therefore a coarse 60-minute volatility representation compared with a
higher-frequency realized-variance construction.

Stage B does not redesign this LOCKED Cell 14 feature.

Estimator quality and incremental predictive usefulness belong to later
label-aware research.

The same principle applies to the longer V1 realized-volatility windows using
their locked 15-minute-return inputs.

---

### 15.3 Horizon-safe-close affine identity

Check type:

`EXACT_AFFINE_DERIVED_IDENTITY`

Canonical Cell 14 definitions imply:

`minutes_to_horizon_safe_close = 330 - minutes_since_nyse_open - 180 * early_close_session`

for every valid TRAIN decision.

Determining features:

- `minutes_since_nyse_open`
- `early_close_session`

Derived feature:

- `minutes_to_horizon_safe_close`

`early_close_session` is a canonical model-eligible candidate feature.

Therefore the identity is information-preserving inside the canonical
candidate set.

For this dependency:

- k = 3
- retained information dimension = 2
- required drop count = 1

V1.2 preserves the V1.1 semantic resolution:

- KEEP `minutes_since_nyse_open`
- KEEP `early_close_session`
- `DROP_REDUNDANT` `minutes_to_horizon_safe_close`

Both determining features are:

`SEMANTIC_BASIS_PROTECTED`

for BASE reduction.

This is an exact affine/functional identity.

When exact integer-minute reconstruction is available, floating tolerance is
not used as a substitute for exact functional validation.

---

### 15.4 Weekday one-hot affine dependency

Check type:

`EXACT_AFFINE_DEPENDENCY`

Canonical weekday candidates:

- `weekday_0`
- `weekday_1`
- `weekday_2`
- `weekday_3`
- `weekday_4`

They sum to one for every valid TRAIN row.

Five dummies contain four categorical dimensions.

Therefore:

- k = 5
- information dimension = 4
- required drop count = 1

Stage B keeps four weekday dimensions and drops exactly one deterministic
reference dummy.

It must not collapse all five to one representative.

No weekday member is predeclared as the semantic determining basis.

The reference category is resolved through registry-authorized Phase-A
semantic reference selection and canonical ordering. This explicit semantic
authority does not grant generic Phase-B rank/SVD deletion authority.

---

### 15.5 Decision-slot cyclical representation

Check type:

`PAIRED_NONLINEAR_REPRESENTATION`

Canonical pair:

- `decision_slot_sin`
- `decision_slot_cos`

must satisfy:

`decision_slot_sin^2 + decision_slot_cos^2 = 1`

within floating-point tolerance.

The pair is a deterministic nonlinear representation of decision-slot/session
time.

Neither component alone replaces the other.

Therefore:

`required_drop_count = 0`

V1.2 preserves the V1.1 decision to retain both components in BASE.

The ledger must not describe the pair as independent raw information.

---

### 15.6 Lag-0 versus current-bar log body

Check type:

`EMPIRICAL_NEAR_IDENTITY`

Compare:

- `ret_log_15m_lag0`
- `bar_log_body_15m`

inside each TRAIN fold.

This is not declared exact.

Its evidence is subject to:

- TRAIN-only procedure,
- common-cohort rules,
- coverage gate,
- cohort-sensitivity rule,
- empirical threshold provenance.

`ret_log_15m_lag0` is protected by §15.1.

Therefore Phase C may not remove `ret_log_15m_lag0`.

If this pair satisfies all empirical HARD requirements, the only automatic
BASE compression direction preserved under V1.2 is to remove the unprotected
candidate if all other Phase-C gates pass.

---

## 16. Prior expectations are not semantic gates

Previous exploratory work noted that the two volume-ratio candidates appeared
to have relatively high Pearson association without equally high Spearman
association.

Classification:

`PRIOR_EXPECTATION_ONLY`

This is:

- not a semantic check,
- not a gate,
- not a forced REVIEW result.

V1.2 recomputes evidence under locked procedure.

New locked evidence is reported as-is even if it differs from the prior
expectation.

---

## 17. Numeric identity tolerance

Floating-point exact semantic identities use:

`ABSOLUTE_TOLERANCE = 1e-12`

This applies only to floating-point numeric identity checks.

It does not automatically apply to:

- exact integer functional identities,
- categorical identities,
- empirical near-identities.

Changing the tolerance after lock requires a policy version bump.

### 17.1 Canonical pre-lock factual validation

Target-blind pre-lock validation was performed against the canonical Cell 14
Development artifact before policy lock.

Final-Test firewall evidence:

- minimum Development year: `2019`
- maximum Development year: `2024`
- `final_test_rows_opened = 0`
- `FINAL_TEST_FIREWALL_PASS = true`

For the two 60-minute identities below, `rows checked` means
Development rows where every feature required to evaluate the identity is
non-missing.

Both checks use the same `31,134` available Development rows and exclude the
same `59` rows from the `31,193`-row Decision Universe.

Those `59` excluded rows are fully reconciled by the missingness accounting in
Section 9: all are contained within the shared `983`-row component, with `0`
identity-unavailable rows outside that component.

Momentum 60-minute identity:

- rows checked: `31,134`
- maximum absolute error: `4.631711680858075e-16`
- tolerance: `1e-12`
- fail count: `0`
- non-finite count: `0`
- result: `PASS`

Realized-volatility 60-minute identity:

- rows checked: `31,134`
- maximum absolute error: `6.938893903907228e-18`
- tolerance: `1e-12`
- fail count: `0`
- non-finite count: `0`
- result: `PASS`

Horizon-safe-close affine identity:

- rows checked: `31,193`
- maximum absolute error: `0.0`
- tolerance: `1e-12`
- fail count: `0`
- non-finite count: `0`
- result: `PASS`

Therefore the recorded pre-lock factual states are:

- `IDENTITY_VALIDATION_PASS = true`
- `FINAL_TEST_FIREWALL_PASS = true`
- `PHASE_0_PRELOCK_DRY_RUN = PASS`
- `PRELOCK_FACT_VALIDATION = PASS`

These are factual validation records.

They do not create or modify feature-selection methodology.

Production semantic checks must still recompute required identities rather
than trust the recorded prose values.

---

## 18. Scope limitation of numerical diagnostics

Pairwise correlation cannot identify every multi-feature dependency.

Set-level diagnostics are therefore mandatory.

However:

- SVD,
- numerical rank,
- condition number,
- Pearson correlation,
- Spearman correlation

do not identify every possible form of information redundancy.

SVD/rank primarily diagnose linear dependence.

Spearman primarily diagnoses monotonic association.

Nonlinear deterministic relationships require semantic knowledge or later
model-aware investigation.

For example:

- realized volatility is a nonlinear function of return lags,
- decision-slot sine/cosine jointly represent one cyclical variable.

Stage B must not interpret full rank or low correlation as proof of general
feature independence.

---

## 19. Dual zero-variance diagnostics

Zero variance is measured at two different scopes and they must not be
conflated.

### 19.1 FULL_TRAIN_ZERO_VARIANCE

For each feature and TRAIN fold, compute variance using all non-missing values
available for that feature in the full TRAIN fold.

No imputation is permitted.

Report:

- available row count,
- unique-value count,
- standard deviation.

This diagnostic describes the feature itself in full TRAIN history.

### 19.2 COMMON_COHORT_ZERO_VARIANCE

Also compute variance on:

`FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD`

This diagnostic describes the feature after the common-cohort filter.

A feature may become constant on the common cohort even when it is not
constant in full TRAIN.

Such a condition is a property of the cohort filter and must not be
misreported as an intrinsic no-information feature.

### 19.3 Automatic zero-variance BASE rule

Automatic no-information deletion may rely only on:

`FULL_TRAIN_ZERO_VARIANCE`

A non-protected feature that has zero variance in **all three full TRAIN
folds** may receive:

`DROP_REDUNDANT`

with decision basis:

`ZERO_VARIANCE_NO_INFORMATION`

The reason must state explicitly that this is degeneracy/no-information, not
redundancy with another feature.

A feature zero-variance only on the common cohort may not be automatically
dropped by this rule.

A feature zero-variance in only a subset of full TRAIN folds may not be
automatically dropped by this rule.

A `SEMANTIC_BASIS_PROTECTED` determining feature may not be automatically
dropped by this BASE zero-variance rule.

Its zero-variance condition remains visible as diagnostic evidence.

### 19.4 Expanding-fold interpretation

Because the TRAIN folds are nested expanding histories, the requirement that a
feature be zero-variance in all three full TRAIN folds is not interpreted as
three independent confirmations.

Subject to non-empty observable values, a feature that is constant throughout
the largest `WF_2024` TRAIN history will necessarily remain constant in its
earlier nested TRAIN subsets.

The all-three-fold rule is retained as a deterministic consistency check.

It must not be described as evidence multiplied across three independent
samples.

### 19.5 Canonical pre-lock zero-variance observation

The target-blind canonical pre-lock dry-run found no zero-variance candidate
feature at either diagnostic scope in any TRAIN fold.

For `role_wf_2022`:

- `FULL_TRAIN_ZERO_VAR = []`
- `COMMON_ZERO_VAR = []`

For `role_wf_2023`:

- `FULL_TRAIN_ZERO_VAR = []`
- `COMMON_ZERO_VAR = []`

For `role_wf_2024`:

- `FULL_TRAIN_ZERO_VAR = []`
- `COMMON_ZERO_VAR = []`

Therefore no canonical real-data feature currently exercises the automatic
zero-variance DROP branch.

The zero-variance machinery nevertheless remains mandatory as:

1. a general no-information policy rule,
2. a defensive integrity control, and
3. a future drift detector.

If a future canonical input makes either diagnostic unexpectedly non-empty,
that change must remain visible in Stage B audit output.

Because current canonical real data does not exercise the automatic
zero-variance DROP path, that behavior must be verified with controlled
synthetic tests.

This factual observation does not weaken §19.3.

Automatic zero-variance BASE deletion still relies only on
`FULL_TRAIN_ZERO_VARIANCE`, never common-cohort-only zero variance.

---

## 20. Standardized numerical representation

Set-level numerical diagnostics operate inside each TRAIN-fold common cohort.

After common-cohort zero-variance columns are identified and excluded from
inter-feature rank counting, let the remaining matrix be:

`X`

For each included feature:

1. compute TRAIN common-cohort mean,
2. center,
3. divide by common-cohort standard deviation,
4. use float64 arithmetic.

Result:

`Z`

Diagnostic standard deviation uses:

`ddof = 0`

No labels or validation information may enter this transform.

This standardization is for numerical diagnosis only.

It does not automatically become a production model transform.

---

## 21. SVD shared rank/conditioning engine

Compute SVD directly on applicable `Z`.

Use the same singular spectrum for:

- numerical rank,
- rank deficiency,
- condition number.

Numerical-rank tolerance:

`rank_tol = max(n_rows, n_features) * eps_float64 * sigma_max`

Numerical rank is the number of singular values strictly greater than
`rank_tol`.

Record:

- matrix shape,
- singular values,
- `sigma_max`,
- tolerance,
- rank,
- deficiency.

Numerical rank and deficiency are evidence only. They do not authorize a
generic Phase-B member selection or direct DROP.

---

## 22. Generic exact-rank discovery firewall

Full-set SVD is reported first.

Generic Phase-B rank/SVD evidence has **no direct KEEP/DROP authority**.

Phase A first resolves only the exact semantic relationships whose direction
is explicitly authorized by the locked semantic registry. Phase B then detects
and localizes any remaining exact numerical dependency without selecting a
retained basis or redundant member.

For a remaining Phase-B dependency component:

- k = remaining features
- r = numerical rank

the observed exact rank deficiency is:

`k - r`

`k - r` is diagnostic evidence only. It is not a deletion obligation and may
not be converted into member-level KEEP/DROP decisions through retention
priority, canonical order, availability, lookback, or environment choice.

The frozen V1.2 disposition is:

- stable, localized, unexplained exact dependency -> `OPEN` every member of the
  localized component;
- cohort-conditional but localized exact dependency -> `OPEN` every member of
  the localized component;
- unstable, unlocalizable, tolerance-inconsistent, or numerically inconsistent
  dependency -> `HARD_FAIL`.

No generic Phase-B finding may produce `DROP_REDUNDANT`.
`HARD_FAIL` is a run disposition; it releases no feature-level BASE decision.

### No generic retention-basis construction

Where semantic direction is absent, Stage B must not:

- choose one representative or basis,
- order component members to select a DROP target,
- classify a non-rank-increasing member as `DROP_REDUNDANT`,
- use a BLAS/runtime/environment change to resolve an `OPEN` component.

Deterministic ordering remains permitted only for evidence serialization. It
does not confer decision direction.

### 22.1 Group-available re-verification

A generic Phase-B dependency first discovered on the full-29 common cohort may
not be called globally exact solely because it is exact on that restricted
cohort.

For each proposed generic Phase-B dependency group `G`, Stage B must construct:

`GROUP_AVAILABLE_TRAIN_ROWS`

separately inside every TRAIN fold.

This cohort contains every TRAIN row where all features in `G` are non-missing,
regardless of whether unrelated canonical features are missing.

No imputation is allowed.

Using the same locked float64 standardization and SVD tolerance, Stage B must
recompute numerical rank for `G` on this wider group-available cohort.

The group-available result classifies the discovery; it never authorizes a
generic DROP.

For each fold, record:

- group-available row count,
- group numerical rank,
- group rank deficiency,
- singular values,
- rank tolerance.

If the localized dependency persists consistently on the group-available
cohort in every required TRAIN fold, classify the entire component:

`STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY -> OPEN`

If a dependency appears on the full-29 common cohort but does not persist on
the group-available cohort, classify:

`COHORT_CONDITIONAL_LOCALIZED_EXACT_DEPENDENCY`

and classify the entire localized component `OPEN`.

If the component cannot be localized consistently, or if fold/tolerance/
numerical evidence is inconsistent, classify `HARD_FAIL` and release no
feature decision.

This re-verification rule is not required to rediscover predeclared exact
semantic identities whose algebraic form is independently defined and verified
row-by-row in Phase A.

---

## 23. Ordered reduction procedure

Reduction executes in this fixed order.

### Phase 0 — Firewall and diagnostics

Before feature decisions:

- validate document hash where applicable,
- validate semantic-registry hash where applicable,
- validate upstream hashes,
- validate canonical 29-feature membership/order,
- validate lookback metadata,
- enforce Final Test firewall,
- enforce forbidden-input firewall,
- compute fold coverage,
- compute yearly concentration report,
- compute dual zero-variance diagnostics.

No deletion occurs before Phase 0 passes.

### Phase A — Exact semantic resolution

Resolve predeclared exact semantic/algebraic dependencies.

Semantic direction takes precedence when explicitly locked.

Phase A may also classify retained nonlinear deterministic representations.

Only exact information-preserving BASE reductions occur here.

Phase-A determining features marked protected become:

`SEMANTIC_BASIS_PROTECTED`

### Phase B — Generic exact-rank / SVD discovery firewall

After Phase A, detect and localize remaining exact numerical dependencies using
SVD/rank.

Every generic dependency must pass §22.1 group-available re-verification and
receive exactly one frozen disposition:

- whole localized component `OPEN`, or
- `HARD_FAIL`.

Phase B does not select a basis and cannot produce a direct DROP.

### Phase C — Empirical HARD pairwise reduction

Phase C cannot proceed while any Phase-B component is `OPEN` or Phase B is in
`HARD_FAIL`. Otherwise the candidates remaining after Phase A proceed without
generic Phase-B deletion.

Phase C is explicitly:

`EMPIRICAL_APPROXIMATE_COMPRESSION`

A HARD empirical pair may remain algebraically full-rank.

Therefore Phase C is not required to preserve Phase-B numerical rank.

However:

- protected features may not be dropped,
- every deletion needs a direct retained substitute,
- cohort-sensitivity rules must pass,
- no transitive-chain substitution is allowed.

Record:

- rank before Phase C,
- rank after Phase C,
- rank loss,
- number of empirical deletions,
- direct substitute for every deletion.

Any Phase-C rank loss must be classified:

`EMPIRICAL_APPROXIMATE_COMPRESSION`

not exact redundancy.

### Phase D — REVIEW / clustering / descriptive stability

Phase D is evidence/reporting only.

It cannot independently DROP a feature.

---

## 24. Phase-C rank-loss review

There is no arbitrary numerical cap on permitted Phase-C rank loss in V1.2.

A cap invented after observing results would create another data-informed
selection threshold without established justification.

Instead:

If:

`phase_c_rank_after < phase_b_rank_before`

the audit must set:

`PHASE_C_RANK_LOSS_REVIEW_REQUIRED = true`

Before Stage C opens labels, independent Stage B review must confirm that:

- every Phase-C deletion satisfied locked HARD rules,
- every deletion had a direct retained substitute,
- every cohort-sensitivity gate passed,
- no semantic-basis-protected feature was removed,
- rank loss is labeled approximate rather than exact.

Required audit status:

`PHASE_C_RANK_LOSS_REVIEW_STATUS = ACKNOWLEDGED`

when rank loss occurred.

This review may not use labels, validation performance, P&L, or Final Test.

It is an audit acknowledgment of an already locked deterministic procedure,
not a discretionary opportunity to optimize the selected set.

---

## 25. Affine/intercept diagnostic

Because `Z` is centered, affine dependencies can appear as linear
dependencies.

Stage B additionally reports rank for:

`[1, Z]`

where `1` is an intercept column.

Report:

- feature-space rank,
- augmented-design rank,
- deficiencies.

This is descriptive model-design evidence.

It does not override locked semantic rules.

---

## 26. Condition number

Stage B reports at least:

### Full-set condition number

Before Phase-A semantic resolution, after handling common-cohort zero-variance
columns separately.

If rank deficient:

`full_set_condition_number = infinity`

This may be expected when known exact dependencies remain.

### Post-Phase-A candidate-set condition number

After Phase-A semantic resolution and before any generic Phase-B disposition:

`post_phase_a_condition_number = sigma_max / sigma_min`

using SVD of the Phase-A retained candidate set.

Rank deficiency here is generic Phase-B discovery evidence and must route to
the §22 `OPEN`/`HARD_FAIL` firewall. It does not authorize basis selection.

If this diagnostic is numerically inconsistent:

Stage B fails.

Condition number alone does not DROP features in V1.2.

An optional:

`post_empirical_condition_number`

may also be reported after Phase C but may not replace the required two
diagnostics.

---

## 27. VIF

Variance Inflation Factor is:

`LINEAR_OVERLAY_DIAGNOSTIC`

only.

VIF is not a universal BASE drop rule.

Any VIF threshold affecting the LINEAR overlay must be separately locked before
Stage C opens labels.

Otherwise VIF remains reporting-only.

---

## 28. Primary pairwise Pearson / Spearman rules

Primary empirical correlations use:

`FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD`

for each TRAIN fold.

Correlations are computed for all 29 canonical candidates so semantic-dropped
features remain auditable.

Phase-C deletion is applied only to candidates retained after Phases A and B.

### HARD_REDUNDANCY

Primary HARD requires:

`|Pearson| >= 0.95`

AND:

`|Spearman| >= 0.95`

in **all three TRAIN folds**.

Because folds are nested, this all-fold requirement is a robustness consistency
condition across expanding histories, not three independent confirmations.

### REVIEW

REVIEW occurs when either:

`|Pearson| >= 0.90`

OR:

`|Spearman| >= 0.90`

in any TRAIN fold.

REVIEW never independently drops a feature.

---

## 29. Empirical-threshold provenance

HARD and REVIEW thresholds are not pristine pre-data thresholds.

They existed after prior Development/TRAIN exploratory characteristics had
already been inspected.

Provenance:

`LEGACY_DATA_INFORMED_BEFORE_FORMAL_V1_1_EXECUTION`

The project must not claim otherwise.

Known provenance sources include:

- Stage B V1.0 contract,
- pre-V1.1 Development/TRAIN exploratory work.

If the precise first historical introduction cannot be reconstructed, the
audit records that provenance as incomplete rather than inventing history.

---

## 30. Cohort-sensitivity analysis

The full-29 common cohort is the primary comparison cohort because every
feature is evaluated on the same TRAIN observations.

However, observed historical missingness is concentrated and largely driven
by shared 240-minute availability.

Therefore every pair that would otherwise cause a Phase-C automatic DROP must
also undergo a pairwise-available sensitivity calculation.

Sensitivity cohort:

`PAIRWISE_AVAILABLE_TRAIN_ROWS`

For a candidate pair, this cohort contains all TRAIN rows where both pair
members are non-missing, regardless of whether unrelated features are missing.

No imputation is allowed.

For each fold report:

- primary common-cohort Pearson,
- primary common-cohort Spearman,
- primary common-cohort rows,
- pairwise-available Pearson,
- pairwise-available Spearman,
- pairwise-available rows.

### 30.1 Sensitivity support

A primary Phase-C HARD relation receives:

`COHORT_SENSITIVITY_SUPPORTED`

only if the pairwise-available sensitivity cohort also satisfies:

`|Pearson| >= 0.95 AND |Spearman| >= 0.95`

in all three TRAIN folds.

### 30.2 Sensitivity conflict

If primary common-cohort evidence satisfies HARD but pairwise-available
evidence fails the complete all-fold HARD requirement, classify:

`COHORT_SENSITIVITY_CONFLICT`

Automatic Phase-C DROP is vetoed.

The unprotected candidate remains:

`KEEP`

with decision basis:

`EMPIRICAL_DROP_VETOED_COHORT_SENSITIVITY`

This is deterministic.

No human discretionary feature choice is introduced.

Sensitivity evidence does not create a DROP when the primary common cohort
does not already satisfy HARD.

Sensitivity is therefore a robustness veto, not an alternative
feature-selection search.

### 30.3 Mathematically unavailable sensitivity statistic

A required pairwise sensitivity statistic is considered mathematically
unavailable in a TRAIN fold only when at least one of these machine-detectable
conditions is true:

1. `pairwise_available_rows < 2`,
2. either pair member has zero variance on the pairwise-available cohort,
3. Pearson returns a non-finite value,
4. Spearman returns a non-finite value.

No qualitative category such as:

`insufficiently variable`

is permitted in V1.2.

No minimum unique-value threshold, mode-share threshold, or other discretionary
empirical variability threshold is introduced.

If any required TRAIN fold has an unavailable sensitivity statistic under the
rules above, classify:

`COHORT_SENSITIVITY_UNAVAILABLE`

The pair cannot qualify for automatic Phase-C empirical deletion.

Automatic DROP is vetoed.

Sensitivity unavailability may not itself create a DROP.

---

## 31. Correlation sample-count semantics

Primary correlation artifact uses:

`common_cohort_rows`

for the actual primary correlation cohort.

Sensitivity rows use:

`pairwise_available_rows`

Group-level rank re-verification uses:

`group_available_rows`

These counts must not be conflated.

The ambiguous field name:

`sample_count`

is forbidden unless its cohort definition is explicit.

---

## 32. Hierarchical clustering

Clustering runs separately inside each TRAIN fold.

Input:

`Spearman rho`

Distance:

`1 - |rho|`

Linkage:

`complete`

Cut distance:

`0.10`

The 0.10 cut corresponds specifically to:

`|Spearman| >= 0.90`

which is only the Spearman arm of REVIEW.

It is not the complete REVIEW set because REVIEW uses:

`Pearson OR Spearman`

A Pearson-only REVIEW pair may therefore be absent from clustering.

That is intentional.

Clustering is:

`REVIEW_EVIDENCE_ONLY`

and cannot independently DROP features.

---

## 33. Deterministic empirical pairwise reduction

Phase-C candidates are processed in deterministic retention order.

`SEMANTIC_BASIS_PROTECTED` features are retained before unprotected candidates
and cannot be empirical-drop targets.

Protected features may serve as direct substitutes for an unprotected
candidate.

For every unprotected candidate:

- if no already-retained feature is directly HARD with it under all locked
  primary and sensitivity rules, retain it;
- if a direct retained substitute satisfies all rules, candidate may receive
  `DROP_REDUNDANT`;
- record the exact direct substitute.

Transitive chaining is forbidden.

A HARD B and B HARD C does not imply A HARD C.

---

## 34. Retention priority

This target-blind deterministic priority is authorized only for:

- registry-directed Phase-A undirected semantic reference selection, and
- locked Phase-C empirical direct-substitute processing.

It is forbidden as a generic Phase-B rank/SVD KEEP/DROP selector.

Within those authorized scopes, deterministic priority is:

1. explicit semantic dependency direction,
2. `SEMANTIC_BASIS_PROTECTED` status,
3. higher point-in-time availability,
4. shorter canonical lookback where modes are comparable,
5. canonical feature order.

Canonical order is the final total-order tie-break.

### 34.1 Point-in-time availability

For each feature:

`fold_availability = non-missing TRAIN rows / total TRAIN rows`

before the full-29 common-cohort filter.

Availability score:

`minimum fold_availability across the three TRAIN folds`

Higher minimum availability wins.

### 34.2 Lookback metadata

Lookback comes only from canonical Cell 14 metadata:

- `lookback_bars`
- `lookback_minutes`
- `lookback_mode`
- `lookback_start_rule`

Missing required metadata is a Stage B failure.

Do not infer lookback from feature names.

### 34.2A Canonical zero-lookback semantics

The canonical Cell 14 registry represents non-rolling current/context features
using valid machine-readable metadata rather than null lookback metadata.

Under the locked upstream Cell 14 registry, such features may have:

- `lookback_mode = FIXED`
- `lookback_bars = 0`
- `lookback_minutes = 0`

For these features, zero lookback means:

`NO HISTORICAL ROLLING LOOKBACK REQUIRED`

It does not mean:

- missing metadata,
- zero-quality metadata,
- undefined lookback mode.

Calendar/context candidates such as weekday indicators and session-time
transforms therefore pass the metadata firewall when their canonical
zero-lookback fields are present and valid.

Stage B must not invent a third lookback mode merely because a feature is
calendar-derived.

Stage B consumes canonical upstream metadata exactly as defined.

Missing required metadata remains a hard failure.

Canonical zero-valued metadata does not.

### 34.3 Locked lookback-mode comparability

V1.2 uses these deterministic rules within the authorized §34 scopes:

| Mode A | Mode B | Comparison rule |
|---|---|---|
| `FIXED` | `FIXED` | lower canonical `lookback_minutes` is preferred |
| `SESSION_TO_DATE` | `SESSION_TO_DATE` | compare canonical `lookback_minutes` only when `lookback_start_rule` is identical; otherwise NON_COMPARABLE |
| `FIXED` | `SESSION_TO_DATE` | NON_COMPARABLE |
| `SESSION_TO_DATE` | `FIXED` | NON_COMPARABLE |

For:

`NON_COMPARABLE`

the lookback criterion makes no decision and the procedure moves directly to
canonical feature order.

No implementation discretion is permitted.

A `FIXED` feature with `lookback_minutes = 0` is a valid canonical
zero-lookback feature and participates in FIXED-vs-FIXED comparison as zero.

### 34.4 Stability

TRAIN-history stability is descriptive in V1.2.

It is not an automatic retention tie-break because no sufficiently precise
stability metric has been locked.

### 34.5 Protected-basis priority is intentional

`SEMANTIC_BASIS_PROTECTED` status deliberately precedes empirical availability
and lookback criteria.

This means an exact determining feature may be retained over an empirically
more available approximate substitute.

That behavior is intentional.

V1.2 prioritizes preservation of the explicitly selected exact semantic basis
over later approximate empirical compression.

This consequence must not be described as an accidental side effect of the
tie-break order.

---

## 35. Evidence versus final decision

Evidence and final decisions remain separate.

A feature may participate in more than one redundancy or representation
relationship.

The feature decision registry must therefore not use one singular
feature-level `dependency_group` field as the complete relationship record.

Required decision-registry fields include at minimum:

- `feature`
- `base_decision`
- `decision_basis`
- `semantic_dependency_groups`
- `exact_set_dependency_groups`
- `empirical_pair_ids`
- `semantic_basis_protected`
- `chosen_representative_or_basis`
- `direct_substitute`
- `group_cohort_rank_status`
- `cohort_sensitivity_status`
- `linear_overlay_decision`
- `tree_overlay_decision`
- `reason`

For generic Phase-B rank/SVD relationships,
`chosen_representative_or_basis` must be empty and non-authoritative. It may be
populated only by a registry-authorized Phase-A semantic decision or an
applicable locked Phase-C rule.

Any released feature row with a non-empty `exact_set_dependency_groups` field
must have `base_decision = OPEN`; its `chosen_representative_or_basis` and
`direct_substitute` fields must both be empty. A generic `HARD_FAIL` releases no
feature-level decision row.

`required_drop_count` is relationship-level evidence, not one singular
feature-level decision-registry value.

For semantic relationships, the governing value is carried by the semantic
registry and corresponding semantic-ledger record.

For generic exact-set relationships, component membership, rank-deficiency,
localization evidence, cohort classification, and `OPEN`/`HARD_FAIL`
disposition belong in the set-level diagnostics. No supported generic
drop-count field exists in V1.2.

Stage B must not collapse multiple relationship-specific drop counts into one
ambiguous feature-level scalar.

### 35.1 Multi-value identifier serialization

For CSV artifacts, the following multi-value identifier fields:

- `semantic_dependency_groups`
- `exact_set_dependency_groups`
- `empirical_pair_ids`

must serialize as deterministic `|`-delimited strings.

Example:

`GROUP_A|GROUP_B`

Rules:

- identifier values themselves must not contain `|`,
- duplicate identifiers are forbidden,
- empty collections serialize as an empty string,
- no leading delimiter is permitted,
- no trailing delimiter is permitted,
- each multi-value field may contain only identifiers from its own relationship class;
- semantic, exact-set, and empirical identifiers must not be mixed inside one field;
- unordered Python set iteration must not determine output order.

Ordering policy:

- `semantic_dependency_groups` follows semantic-registry check order,
- `exact_set_dependency_groups` follows deterministic Phase-B
  component-discovery order only,
- `empirical_pair_ids` follows canonical pair-processing order.

Allowed BASE decisions:

- `KEEP`
- `DROP_REDUNDANT`
- `OPEN`

Decision basis must distinguish:

- exact semantic redundancy,
- generic exact numerical dependency classified `OPEN` or `HARD_FAIL`,
- zero-variance/no-information degeneration,
- empirical approximate compression,
- empirical drop vetoed by cohort sensitivity,
- localized cohort-conditional generic dependency classified `OPEN`.

---

## 36. OPEN gate

`OPEN` means target-blind policy is insufficient to produce a reproducible
KEEP/DROP decision.

Stage C may not open labels until:

`OPEN count = 0`

OPEN may not be resolved using:

- labels,
- AUC,
- validation performance,
- P&L,
- Final Test,
- future-return association.

Upstream hash, coverage, firewall, or integrity failure is not converted into
OPEN.

It stops Stage B before decisions are released.

A localized cohort-conditional generic rank dependency requires `OPEN` for
every component member. Unstable, unlocalizable, tolerance-inconsistent, or
numerically inconsistent generic evidence requires `HARD_FAIL`.

Changing BLAS, thread configuration, runtime, or environment does not itself
resolve a generic `OPEN`, authorize a basis, or authorize a DROP. A separately
approved policy resolution would be required.

Phase-C-only vetoes such as `COHORT_SENSITIVITY_CONFLICT` and
`COHORT_SENSITIVITY_UNAVAILABLE` retain their separately locked behavior.

---

## 37. BASE and overlays

Stage B produces one model-agnostic:

`BASE`

Only two model-specific overlays are permitted:

- `LINEAR_OVERLAY`
- `TREE_OVERLAY`

Maximum unique Stage-C feature masks:

`3`

namely:

1. BASE,
2. BASE + LINEAR restrictions,
3. BASE + TREE restrictions.

Identical masks are deduplicated.

No additional mask may be created after labels are visible.

Any overlay removal of a `SEMANTIC_BASIS_PROTECTED` BASE feature must be
explicitly recorded.

An overlay may not reintroduce a BASE `DROP_REDUNDANT` derived feature as a
substitute without a new predeclared mask policy.

---

## 38. Stability and serial dependence

Stage B observations are time-series observations containing:

- serial dependence,
- overlapping rolling windows,
- expanding-fold overlap.

Raw row count is not iid effective sample size.

V1.2 does not use naive iid:

- p-values,
- confidence intervals,
- significance tests

to select features.

Primary stability evidence is descriptive.

Any later inferential uncertainty method must be separately predeclared and
serial-dependence aware.

The +60-minute label-overlap problem belongs to later label-aware stages.

Stage B remains target-blind.

---

## 39. Production gate boundary

Production artifact-reading entry point:

`run_stage_b(...)`

All production Stage B artifact access must pass through this entry point.

Issue #9 does not implement Phase-B production execution. The authoritative
entry point must continue to execute Phase 0 and Phase A only, then fail closed
before Phase B. The isolated V1.2 generic-discovery classifier is specification
evidence, not an alternative artifact-reading or production path.

Mathematical analyzer helpers must:

- not independently read production artifacts,
- remain pure calculations,
- be private/internal where practical,
- not provide alternative public production entry paths.

Tests must verify that no public artifact-reading path bypasses the Stage B
firewall.

The pre-lock Phase-0 dry-run defined later is a separate target-blind
validation procedure and is not a production feature-selection entry point.

---

## 40. Gate coverage

Before production analysis, the firewall validates:

- Markdown SHA,
- semantic-registry SHA,
- policy version,
- Python policy status,
- Markdown policy status,
- semantic-registry status,
- semantic-registry policy-version/source-contract binding,
- upstream hashes,
- canonical registry hash,
- exactly 29 candidates,
- feature membership,
- feature order,
- required lookback metadata,
- allowed input cells,
- forbidden fields,
- Final Test firewall,
- fold definitions,
- fold coverage floor.

The gated production run then governs:

- coverage,
- yearly concentration reporting,
- missingness,
- semantic checks,
- dual zero-variance diagnostics,
- SVD/rank,
- group-available rank re-verification,
- condition numbers,
- primary correlations,
- pairwise cohort sensitivity,
- clustering,
- BASE decisions,
- overlays.

---

## 41. Required policy/control files

Stage B V1.2 requires:

- `docs/STAGE_B_REDUNDANCY_CONTRACT.md`
- `configs/v1/stage_b_semantic_registry_v1.json`
- `src/mes_quant/redundancy/contract.py`

Their responsibilities are distinct.

The Markdown contract is the governing source for:

- research methodology,
- rationale,
- methodological constraints,
- interpretation.

The semantic registry is the authoritative executable source for
semantic-check parameters.

The Python contract is the enforcement gate that pins:

- locked Markdown SHA256,
- locked semantic-registry SHA256,
- policy version,
- policy status,
- required control constants.

Analyzer/runtime code must consume semantic parameters from the locked
semantic registry.

It may not maintain an independent second semantic-policy table.

Tests validate:

- consistency,
- structural invariants,
- safety sentinels,
- implementation behavior.

Tests are not an additional policy authority.

No real-data Stage B production execution may occur while any required control
disagrees.

Before the first lock and after every later policy version bump, an independent
Markdown ↔ JSON joint semantic consistency audit is required before new hashes
are pinned.

---

## 42. Required output artifacts

Required outputs:

- `stage_b_feature_coverage_v1.csv`
- `stage_b_semantic_dependency_ledger_v1.csv`
- `stage_b_fold_correlations_v1.parquet`
- `stage_b_set_level_diagnostics_v1.csv`
- `stage_b_redundancy_clusters_v1.csv`
- `stage_b_feature_decision_registry_v1.csv`
- `stage_b_redundancy_audit.json`

No Stage B artifact may overwrite Cell 14.

Artifacts require:

- deterministic ordering,
- policy version,
- upstream/control hashes,
- output hash.

The correlation artifact must contain both:

- primary common-cohort evidence,
- required pairwise-available sensitivity evidence

with explicit cohort names and row counts.

Set-level diagnostics must distinguish:

- full-29 common cohort,
- group-available verification cohort,
- Phase-A retained candidate set,
- localized generic dependency components and their `OPEN`/`HARD_FAIL`
  dispositions.

### 42.1 Deterministic artifact serialization

Stage B artifact serialization must not depend silently on operating-system or
unordered-container defaults.

For CSV artifacts, implementation and tests must explicitly control at least:

- UTF-8 encoding,
- field/schema order,
- row order,
- line-termination behavior,
- multi-value identifier order,
- multi-value delimiter behavior.

Multi-value identifier fields defined in §35 use the reserved delimiter:

`|`

and must follow the deterministic ordering rules in §35.1.

Stage B V1.2 does not change the repository-wide:

`* -text`

policy.

If an exact byte-level CSV writer/newline profile is not already locked by an
upstream repository control, Stage B implementation must define one explicit
deterministic writer profile and record its policy identifier before final
artifact-hash freeze.

The implementation must not silently rely on OS defaults.

---

## 43. Required audit metadata

`stage_b_redundancy_audit.json` includes at minimum:

- Stage B policy version,
- Markdown SHA256,
- semantic-registry SHA256,
- locked Markdown Git commit,
- Python policy status,
- Cell 14 artifact hashes,
- Cell 14 registry hash,
- canonical candidate count,
- feature-order validation,
- lookback metadata validation,
- common-cohort coverage by fold,
- full-29 yearly coverage,
- yearly low-coverage flags,
- `YEARLY_CONCENTRATION_REVIEW_REQUIRED`,
- `YEARLY_CONCENTRATION_REVIEW_STATUS`,
- shared 240m missingness summary,
- full-29 incomplete row count,
- shared 240m incomplete row count,
- SESSION_TO_DATE VWAP-only incomplete row count,
- unexplained full-29 incomplete row count,
- fold coverage-gate result,
- Final Test rows opened,
- forbidden inputs opened,
- empirical-threshold provenance,
- coverage-threshold provenance,
- semantic-registry completeness,
- semantic-registry structural invariant result,
- Markdown ↔ JSON joint-audit status,
- pre-lock identity-validation result,
- pre-lock Final-Test firewall result,
- protected semantic-basis features,
- derived protected-set feature list,
- protected-set sentinel result,
- full-TRAIN zero-variance diagnostics,
- common-cohort zero-variance diagnostics,
- Phase-A decisions,
- generic Phase-B group-available verification results,
- generic component membership and localization status,
- generic component `OPEN` count,
- generic `HARD_FAIL` status/count,
- generic direct-DROP count, which must equal zero,
- Phase-B rank,
- Phase-C rank,
- Phase-C rank loss,
- Phase-C rank-loss review requirement/status,
- primary HARD pair count,
- cohort-sensitivity supported count,
- cohort-sensitivity conflict count,
- cohort-sensitivity unavailable count,
- empirical drops vetoed by cohort sensitivity,
- full-set condition number,
- post-Phase-A candidate-set condition number,
- clustering metric,
- clustering linkage,
- clustering cut,
- OPEN count,
- BASE feature count,
- LINEAR overlay feature count,
- TREE overlay feature count,
- unique Stage-C mask count,
- multi-value serialization policy identifier,
- hashes of every output artifact.

---

## 44. Required tests before real-data execution

Real Stage B production execution is forbidden until
`tests/test_redundancy.py`
covers at minimum:

### Contract / firewall

- Markdown SHA mismatch fails.
- Semantic-registry SHA mismatch fails.
- Policy-version mismatch fails.
- Python policy-status mismatch fails.
- Markdown policy-status mismatch fails.
- Semantic-registry status mismatch fails.
- Semantic-registry policy-version/source-contract binding mismatch fails.
- Hashing uses raw bytes.
- Final Test rejected.
- Forbidden input rejected.
- Alternate production entry bypass rejected.

### Canonical feature control

- exactly 29 features,
- membership enforced,
- order enforced,
- prototype aliases rejected,
- required lookback metadata enforced,
- canonical zero-lookback metadata accepted,
- deterministic pair orientation.

### TRAIN scope

- exactly three TRAIN folds,
- semantic checks TRAIN-only,
- outer-validation cannot affect decisions,
- nested folds not treated as independent replications.

### Coverage and missingness

- canonical fold coverage recomputed,
- 90% fold floor enforced,
- below-floor production run stops,
- yearly coverage reported,
- yearly below-90 condition creates REVIEW flag,
- required yearly review acknowledgment enforced,
- shared 240m missingness not counted as five independent missingness events.

### Semantic registry

- registry completeness,
- all implementations callable,
- all names canonical,
- momentum telescoping identity,
- `momentum_log_60m` dropped,
- four return lags protected,
- four return lags still retained after Phase C,
- realized-vol exact nonlinear identity,
- realized-vol BASE drop count = 0,
- horizon-safe-close affine identity,
- safe-close derived feature dropped,
- `minutes_since_nyse_open` protected,
- `early_close_session` protected,
- weekday affine dependency,
- exactly one weekday reference dropped,
- slot unit-circle identity,
- slot pair retained,
- empirical near-identity not classified exact.

### Dual zero variance

- full-TRAIN zero variance computed independently,
- common-cohort zero variance computed independently,
- common-cohort-only zero variance cannot trigger BASE drop,
- all-fold full-TRAIN zero variance can trigger no-information drop for an
  unprotected feature,
- protected determining feature cannot be zero-variance auto-dropped,
- nested-fold zero-variance result is not labeled independent replication.

### Rank / SVD

- deterministic `Z` construction,
- `ddof=0`,
- deterministic rank tolerance,
- exact rank deficiency detected,
- `k-r` recorded as evidence only after Phase A,
- generic `c = a + b` evidence cannot create a direct DROP,
- stable localized unexplained dependency opens every component member,
- cohort-conditional localized dependency opens every component member,
- unstable/unlocalizable/tolerance-inconsistent/numerically inconsistent
  evidence hard-fails,
- generic retention priority cannot select a basis or DROP target,
- intercept diagnostic,
- full-set condition number,
- post-Phase-A candidate-set condition number.

### Generic Phase-B group verification

- generic dependency discovered on common cohort is recomputed on
  `GROUP_AVAILABLE_TRAIN_ROWS`,
- group-available row count is explicit,
- dependency persisting in all folds may remain exact evidence,
- localized cohort-conditional dependency opens the whole component,
- no group-verification outcome authorizes a generic Phase-B DROP,
- unlocalizable or inconsistent group evidence hard-fails.

### Ordered phases

- Phase 0 precedes decisions,
- Phase A before B,
- B before C,
- C before D,
- protected Phase-A basis cannot be removed by Phase C,
- Phase-C rank reduction labeled approximate,
- rank-loss review required when rank decreases,
- Phase D cannot DROP.

### Pairwise and cohort sensitivity

- HARD = Pearson AND Spearman,
- REVIEW = Pearson OR Spearman,
- HARD required in all folds,
- primary cohort is full-29 common cohort,
- pairwise sensitivity uses only pairwise-available TRAIN rows,
- primary HARD + sensitivity HARD permits eligible compression,
- primary HARD + sensitivity failure creates
  `COHORT_SENSITIVITY_CONFLICT`,
- conflict vetoes DROP,
- conflict leaves candidate KEEP,
- sensitivity alone cannot create DROP,
- `pairwise_available_rows < 2` creates sensitivity unavailable,
- pairwise zero variance creates sensitivity unavailable,
- non-finite Pearson creates sensitivity unavailable,
- non-finite Spearman creates sensitivity unavailable,
- no qualitative `insufficiently variable` rule exists,
- protected lag cannot be empirical-drop target,
- unprotected direct substitute can be dropped against protected retained
  feature,
- chain correlation cannot create unsupported substitution.

### Clustering

- distance = `1 - |Spearman|`,
- complete linkage,
- cut = 0.10,
- Pearson-only REVIEW need not cluster,
- clustering cannot independently DROP.

### Registry-authorized Phase-A / locked Phase-C retention and lookback

- these checks apply only within the §34-authorized Phase-A and Phase-C scopes,
- availability deterministic,
- canonical `FIXED / 0 minutes` accepted,
- fixed-vs-fixed shorter lookback deterministic,
- fixed-vs-session-to-date NON_COMPARABLE,
- session-to-date comparison rule deterministic,
- protected status precedes availability intentionally,
- canonical order final tie-break.

### Decisions / overlays

- allowed BASE states exactly KEEP/DROP_REDUNDANT/OPEN,
- decision basis distinguishes exact/degenerate/empirical/veto mechanisms,
- Stage C blocked when OPEN > 0,
- max overlays = 2,
- max unique masks = 3,
- no label-aware overlay construction.

### R6 control and structural additions

#### Control consistency

- Markdown ↔ JSON joint-audit requirement represented in control policy,
- semantic registry is runtime semantic-parameter authority,
- analyzer does not maintain an independent semantic-parameter table,
- tests are not treated as a third executable policy authority.

#### Semantic-registry structure

- `dependent_features` is always an array,
- `determining_features` is always an array,
- empty arrays accepted where the invariant table requires them,
- null dependent/determining arrays rejected,
- check-type invariant table enforced,
- unknown `check_type` fails closed,
- `required_drop_count = null` accepted only for the permitted empirical type,
- `dependency_group` containing `|` rejected.

#### Protected-set derivation

- protected set derived only from `determining_features` where
  `protect_determining_features = true`,
- expected V1.2 safety sentinel preserves exactly the six V1.1 features,
- all five weekday features excluded from the protected set,
- `momentum_log_60m` excluded,
- `realized_vol_60m` excluded,
- `minutes_to_horizon_safe_close` excluded,
- weekday semantic check has protection false,
- protected BASE features remain protected against both Phase-C and
  BASE zero-variance deletion.

#### Complete missingness reconciliation

- canonical 996 full-29 incomplete rows reconcile exactly to `983 + 13`,
- the 13 residual rows all occur in 2020,
- only `session_vwap_proxy_deviation` is missing on those 13 rows,
- all 13 carry `SESSION_VWAP_INPUT_INVALID`,
- unexplained incomplete-row count equals zero,
- degraded-day causation is not inferred from row-count equality alone.

#### Factual identity validation

- the three recorded pre-lock identity results are consistent with the
  recorded `1e-12` tolerance and PASS states,
- production semantic checks recompute identities rather than trusting
  recorded prose values.

#### Canonical zero-variance observation

- canonical pre-lock zero-variance diagnostics are empty at both scopes in all
  three TRAIN folds,
- automatic zero-variance DROP behavior is exercised synthetically,
- future non-empty diagnostics remain visible as drift/integrity evidence.

#### Multi-group decision registry

- one feature may belong to multiple relationship identifiers,
- `|` inside an identifier is rejected,
- duplicate identifiers are rejected,
- deterministic identifier ordering enforced,
- empty collection serializes as empty string,
- unordered-set serialization is forbidden.
- feature decision registry does not contain one ambiguous singular
  feature-level `required_drop_count`,
- each multi-value relationship field contains only identifiers from its own
  relationship class.

### Reproducibility

- deterministic multi-value serialization,
- explicit deterministic CSV writer/newline behavior,
- deterministic row ordering,
- deterministic artifact ordering,
- equivalent locked inputs reproduce identical artifact hashes.

---

## 45. Acceptance gates

Real-data Stage B decisions may be released only when:

- V1.2 policy controls are formally locked by a later authorized lock action,
- Markdown hash passes,
- semantic-registry hash passes,
- locked Git commit recorded,
- Cell 14 hashes pass,
- exactly 29 features pass,
- canonical order passes,
- canonical zero-lookback metadata is accepted correctly,
- required lookback metadata passes,
- three TRAIN folds verified,
- all fold coverage >= 90%,
- yearly concentration report produced,
- yearly concentration review acknowledged when required,
- full-29 missingness reconciliation complete,
- canonical pre-lock evidence records
  `UNEXPLAINED_FULL_29_INCOMPLETE_ROWS = 0`,
- pre-lock factual identity validation PASS recorded,
- pre-lock Final-Test firewall PASS recorded,
- Final Test rows opened = 0,
- forbidden target/outcome inputs opened = 0,
- semantic registry complete,
- semantic-registry structural invariant checks pass,
- Markdown ↔ JSON joint consistency audit passes before lock,
- protected basis identified,
- protected-set derivation/sentinel passes,
- dual zero-variance diagnostics complete,
- Phase A exact decisions complete,
- every generic Phase-B dependency is localized and classified from
  `GROUP_AVAILABLE_TRAIN_ROWS` evidence,
- every localized generic dependency is `OPEN` for the whole component,
- every unstable/unlocalizable/tolerance-inconsistent/numerically inconsistent
  dependency is `HARD_FAIL`,
- generic Phase-B direct-DROP count = 0,
- Phase C cohort-sensitivity gates complete,
- no subjective empirical variability criterion is used,
- no protected feature removed in Phase C,
- every empirical deletion has a direct substitute,
- Phase-C rank loss recorded,
- Phase-C rank-loss review acknowledged when required,
- clustering policy passes,
- deterministic tests pass,
- multi-value serialization policy tests pass,
- Stage B dedicated tests pass,
- OPEN count = 0,
- independent audit reproduces decisions and hashes.

---

## 46. Final pre-lock, lock, and implementation order

### 46.1 V1.2 lock-breaker 4/5 remediation sequence

1. Preserve remediation baseline
   `a5d3f40e7edc26d950010401654ce4d6b7822e86`.
2. Change only the proven generic rank/SVD direct-DROP contradiction.
3. Preserve every existing Phase-A semantic decision and protected-basis rule.
4. Keep Markdown, semantic registry, and Python policy status `PROVISIONAL`.
5. Keep `run_stage_b()` fail-closed after Phase A; do not implement full Phase
   B, C, or D production execution.
6. Run the Issue #9 checkout-safe verification and publish the bounded
   remediation report.
7. Obtain independent review of the remediation PR.
8. If accepted, resume Issue #8 from the remediation commit as continuation of
   the same final integration audit.
9. Do not lock V1.2 in Issue #9. Any later status promotion is a separate,
   explicitly authorized action after independent review.

### 46.2 Historical V1.1 R6 lock sequence

1. Preserve the R5 baseline commit:

   `2ad2784b8cbaf468284010b95efe768af8e90e41`

2. Construct this R6 contract while it remains:

   `PROVISIONAL_V1_1_DRAFT_R6 — FINAL PRE-LOCK CANDIDATE — NOT EXECUTABLE`

3. Mechanically inspect the Git diff from the R5 baseline to R6.

4. Run the R5 preservation checklist and verify that no previously required
   control silently disappears.

5. Confirm the already completed target-blind factual states:

   - `PHASE_0_PRELOCK_DRY_RUN = PASS`
   - `PRELOCK_FACT_VALIDATION = PASS`
   - `IDENTITY_VALIDATION_PASS = true`
   - `FINAL_TEST_FIREWALL_PASS = true`
   - `final_test_rows_opened = 0`
   - `UNEXPLAINED_FULL_29_INCOMPLETE_ROWS = 0`

6. Keep:

   `configs/v1/stage_b_semantic_registry_v1.json`

   provisional and unlocked until it has been rebuilt or corrected against
   approved R6 policy.

7. Build or correct the provisional semantic registry from this R6 contract.

8. Perform an independent joint:

   `MARKDOWN_JSON_JOINT_CONSISTENCY_AUDIT`

   covering methodology, semantic parameters, structural invariants,
   protection derivation, and required decision effects.

9. Only if the joint audit passes, perform the status-only promotion:

   - Markdown `Policy status` becomes `LOCKED_EXECUTABLE`,
   - semantic-registry `registry_status` becomes `LOCKED_EXECUTABLE`.

   During this status-only promotion:

   - semantic-registry `policy_version` remains
     `MES_V1_REDUNDANCY_1.1`,
   - semantic-registry `source_contract` remains
     `docs/STAGE_B_REDUNDANCY_CONTRACT.md`,
   - no semantic-check parameter may change.

   If any semantic-check parameter changes during promotion, the independent
   Markdown <-> JSON joint consistency audit must be repeated before lock.

10. Commit the exact locked Markdown and semantic-registry bytes.

11. Compute SHA256 from those exact committed bytes.

12. Update:

    `src/mes_quant/redundancy/contract.py`

    to V1.1 and pin both committed hashes.

13. Build or expand:

    `tests/test_redundancy.py`

    to enforce the locked contract, registry invariants, safety sentinels, and
    required behavior.

14. Correct:

    `src/mes_quant/redundancy/analyzer.py`

    so analyzer/runtime semantic policy is consumed from the locked registry
    rather than an independent duplicate semantic table.

15. Add or verify the thin production orchestration entry point:

    `run_stage_b(...)`

16. Run controlled synthetic Stage B tests.

17. Run the complete repository test and lint suite.

18. Verify contract/control hashes and required behavior from a clean checkout.

19. Only then execute Stage B on canonical real Development data.

20. Produce the final Stage B artifact set twice.

21. Verify deterministic artifact bytes and hashes.

22. Perform an independent Stage B output audit and confirm:

    - `OPEN count = 0`
    - yearly concentration review acknowledged when required
    - Phase-C rank-loss review acknowledged when required
    - generic Phase-B direct-DROP count equals zero
    - localized generic dependencies route to whole-component `OPEN`
    - unstable/unlocalizable/tolerance-inconsistent/numerically inconsistent
      generic evidence routes to `HARD_FAIL`
    - cohort-sensitivity conflicts handled deterministically
    - protected-set derivation/sentinel passes
    - no protected semantic-basis feature was removed improperly
    - multi-value identifier serialization is deterministic.

23. Only then permit Stage C to open labels.

Every later Stage B policy version bump must repeat:

Markdown update as applicable
→ semantic-registry update as applicable
→ independent Markdown ↔ JSON joint consistency audit
→ locked commit
→ new committed-byte hashes
→ Python-contract update
→ dependent tests.

Do not return to a new monolithic Colab cell.

Do not use any incomplete Stage B V1.0 result for feature selection.

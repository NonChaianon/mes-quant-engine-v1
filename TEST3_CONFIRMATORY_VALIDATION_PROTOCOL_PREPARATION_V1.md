# TEST3 CONFIRMATORY VALIDATION PROTOCOL — PREPARATION V1

**Label:** `PROPOSED / NON_RATIFIED / DATA_FREE / NO_EXECUTION_AUTHORITY`

## 0. Standing

This is a **proposed** protocol. It is **non-ratified**: it is not in force, it binds nothing, and
it is not evidence. It is **data-free**: it was written without reading any data, target, provider,
row, log or runtime artifact. It carries **no execution authority**: it does not permit a fit, a
Validation opening, an implementation, a test run, a commit or a push.

Ratification is a separate Owner act. Implementation is a further separate Owner act after review.
Execution is a further separate Owner act after that. This document is only the first of those.

The V2 originals remain local and immutable. No raw evidence is committed to this repository.

## 0.1 `INHERITED_SCIENTIFIC_CONTRACT` — controlling parent contract

This section controls. It sits before the readability index of Section 1 and takes precedence over
every later summary in this document.

### 0.1.1 Definition

`INHERITED_SCIENTIFIC_CONTRACT` is the **exact co-ratified bytes** of the two parent artifacts
identified by the preamble and Section 1 of the Owner co-ratification record
`docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md`:

- protocol `MES_TEST3_RV60_HAR_RISK_EDGE_V1` at
  `docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md`; together with
- budget `MES_PROJECT_TARGET_SPACE_BUDGET_V1` at
  `docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md`.

The two are one contract, co-ratified together against the same exact commit. Neither is inherited
alone, and neither may be resolved without the other.

The record preamble and Section 1 carry the ratified commit, exact IDs, paths and recorded digests.
Its Sections 3 and 4 carry ratification, stage-sequence and budget semantics; they are not the
location of the commit/ID/path/digest fields.
Section 2 repeats semantic Owner text and remains bound as exact semantic bytes, but is deliberately
not a structured parse source. The parser uses only the preamble and Section 1 for structured
identity fields.

**The exact ratification-record bytes, not this proposal or a mutable code constant, are the
historical trust root.** The record itself is an exact-byte bounded input to the verifier, not a
current-worktree citation. No digest, checksum, commit, tree, blob or any other Git or object
identifier is transcribed into this document, and none may ever be. A hash typed by hand into this
proposal would identify nothing; only the exact record bytes and their deterministic historical
resolution identify the parent bytes.

### 0.1.2 Mandatory machine verification before any future act

Any future confirmatory ratification, implementation acceptance, activation or execution must first
run an **authorized deterministic verifier** that treats
`docs/research/TEST3_PROTOCOL_AND_BUDGET_OWNER_RATIFICATION_V1.md` as exact-byte bounded input and:

1. parses from the record preamble and Section 1, by exact field and table-row identity, exactly one
   complete `Ratified commit` field,
   exactly one protocol row whose ID and path exactly equal the protocol ID/path in Section 0.1.1,
   and exactly one budget row whose ID and path exactly equal the budget ID/path in Section 0.1.1;
2. parses exactly one recorded SHA-256 value from each of those two exact rows and rejects every
   missing, duplicate, abbreviated, malformed, extra or mismatched field, row, ID, path, commit or
   recorded value;
3. resolves each exact named path as a Git object at the parsed historical commit directly from
   repository objects, never from the current worktree, requires each resolved object to be a blob,
   hashes the exact blob bytes, and requires equality with the corresponding value parsed from the
   ratification record; and
4. emits one complete machine-generated parent-binding block containing the exact
   ratification-record byte binding and the full parse, historical resolution, object-type and
   exact-blob-byte verification output.

The future confirmatory ratification must machine-bind the exact parent ratification-record bytes
and that complete historical-resolution output. Later activation must rerun the verifier, bind the
future confirmatory-ratification bytes, and compare its machine-generated parent-binding block with
the block bound by the future ratification before implementation acceptance, permit issuance, fit,
protected read or Validation opening. A path citation, current-worktree contents, prose assertion or
mutable code constant is insufficient.

The `frozen_contract_payload()` and `frozen_contract_sha256()` surfaces exposed by
`src/mes_quant/exploration/test3_contract.py` are checked only by machine-recomputing that module's
own frozen payload bytes, recomputing the digest from those bytes, and requiring internal
payload/digest self-consistency. This supplementary check covers historical exploratory vocabulary
only, including its historical `LOCKED`/`RESERVED` vocabulary and mutable ratified-commit constant.
Those surfaces explicitly omit parent document hashes, express no current confirmatory state and
are neither a trust root nor a replacement for the exact-byte historical verification above. These
outputs and all generated bindings are deliberately **not printed here**, and no agent may type,
copy, shorten or repair them. Absence, ambiguity, mismatch or nonconformance stops the lineage
before any permit, fit, protected read or Validation opening.

### 0.1.3 `BIND_UNCHANGED` — inherited unchanged, with controlling parent clause

Every item below is inherited **unchanged**. The citation after each item is its controlling parent
clause; where this summary and the parent bytes differ in any degree, **the parent bytes control**.

- **Scientific question and Risk-Edge claim boundary** — parent protocol Section 1. The one narrow
  volatility-memory question, its `H0`/`H1` statement, and the Risk-Edge-only claim: no directional,
  execution, trading, P&L, Sharpe, portfolio, production or live-deployment claim.
- **Exact upstream source lineage and identities** — parent protocol Section 2. The instrument, the
  canonical source, and every frozen upstream identity in that section, bound mechanically before
  any numeric lookup and never retyped by an agent.
- **Partition and access request firewall** — parent protocol Section 3. The partition map, the
  ordered request-key construction and sealing rules, the zero-count assertions for protected
  partitions before provider access, and the prohibition on masking a protected target after
  construction. All remain unchanged except the three exact clauses narrowly and conditionally
  superseded by Section 4 after its create-once Validation-opening witness exists.
- **Exact `RV_FWD_60` timing, horizon, log target, statuses and reason codes** — parent protocol
  Section 4. The 60 strictly post-decision one-minute log returns, `Y = ln(RV_FWD_60)`,
  `label_end_time`, the usability requirements, `TARGET_USABLE`/`TARGET_UNUSABLE`, the
  `TARGET_ZERO_VARIANCE` complete-the-ledger-then-halt rule, and the prohibition on epsilon floors,
  winsorization, annualization, square roots, jump-robust replacement and alternate sampling.
- **Exact `X60`/`X120`/`X240` transforms** — parent protocol Section 5. The pinned log-variance
  transforms exactly as written, with `V60`/`V120`/`V240` documenting variance-scale meaning only.
- **Common eligibility and row-status rules** — parent protocol Section 5. The ordered definition
  steps; the rule that a row is common-eligible if and only if its target status is `TARGET_USABLE`
  and all three predictor statuses are `PREDICTOR_USABLE`; the `PREDICTOR_NONFINITE` and
  `PREDICTOR_NONPOSITIVE` fail-closed codes; and the prohibition on outcome-dependent filtering and
  post-inspection row discretion.
- **Complete early-close-aware harmonic formula and slot constraints** — parent protocol Section 6.
  The full derivation of `minutes_since_open`, `slot`, `n_slots`, `angle`, `SESSION_SIN` and
  `SESSION_COS`; the exact-integer, `n_slots > 0` and `0 <= slot < n_slots` constraints; and exactly
  one harmonic, with no weekday term, early-close dummy, extra phase or alternative period.
- **Model IDs and ordered design columns** — parent protocol Section 7. `RVBASE001` and `RVHAR001`
  with their ordered columns exactly as written, and no third model.
- **float64 OLS with `numpy.linalg.lstsq(..., rcond=None)`** — parent protocol Section 7, including
  the mandatory recording of rank, singular values, condition number and coefficient identity, the
  full-column-rank and finite-output requirements, and the prohibition on scaling, regularization,
  intercept penalties, hyperparameters, early stopping, coefficient constraints and feature
  selection.
- **Historical fold-local Duan transformation** — parent protocol Section 7. The exploratory
  fold-local factors and their fold-TRAIN samples remain immutable historical rules and results.
  They are not deployment factors and are not reused. The distinct confirmatory deployment rule is
  an explicit conditional Section 7 supersession in Sections 0.1.4 and 0.1.5, not an unchanged
  inheritance claim.
- **Fit discipline and permit-at-attempt accounting** — parent protocol Section 8. A failed or
  nonconvergent fit consumes its permit and may not be replaced; no fit occurs at a protocol,
  code-only, metadata-only or pre-fit gate.
- **Dependence and ESS definitions** — parent protocol Section 9. `rho_null(k) = max(1 - k/4, 0)`,
  `excess(k)`, `DESIGN_EFFECT`, `ESS`, computation on pooled within-session pairs rather than by
  summing component ESS values, and ESS as mandatory disclosure that is never a pass gate.
- **QLIKE definition, sign convention and row weighting** — parent protocol Section 10.
  `QLIKE(a, f) = a / f - ln(a / f) - 1`; `d_i` as BASE minus HAR so that a positive value favours
  `RVHAR001`; row-weighted mean loss; and a positive, finite baseline denominator.
- **No tuning and no rescue** — the parent protocol Section 14 chapeau, **"Without a new
  Owner-ratified protocol"**, remains controlling. Every prohibition remains inherited except only
  the exact Section 0.1.5 item 8 supersession of re-fit, pooled-fit, repeated-execution and
  Validation-access bars for the two predeclared deployment fits and one opening. No alternate
  target, horizon, sampling rule, harmonic, calendar term, model family, rescue, feature search,
  coefficient constraint, hyperparameter search, thresholding, imputation, floor, clipping,
  winsorization, outcome-based exclusion, seed search or redraw is displaced.
- **Validation and Final-Test protection** — parent protocol Sections 3, 13 and 14 remain controlling
  except the stage-specific confirmatory counters and one opening exactly displaced by Sections
  0.1.5 and 4. Final Test remains `SEALED`, and every Final-Test request, read and other surface
  counter remains zero throughout.
- **Target-space rules** — parent **budget** Sections 2, 3 and 4. The final OHLCV-only commitment
  and the no-`TARGET_SPACE_004` rule; the reservation, consumption, `CLOSED_UNCONSUMED` and single
  defect-repair carve-out rules; the budget's precedence over the companion protocol for slot
  consumption, reuse and successor eligibility; and the rule that outer Validation and Test 4 remain
  separate decisions with their own exact protocol and budget. Budget Section 2 is also the clause
  that expressly permits advancing the same frozen target to a separately authorized confirmatory
  protocol as confirmation rather than as a new slot.

This enumeration is written to be comprehensive, but **the exact parent bytes, not this summary, are
the completeness root**. If an inherited element is missing from this list, it remains inherited
unchanged regardless.

### 0.1.4 `CONFIRMATORY_EXTENSION` — the only permitted additions

Exactly the following are proposed as additions to the inherited contract, and nothing else:

1. **One future full-outer-TRAIN fit for each frozen model**, in BASE then HAR order — `RVBASE001`
   first, then `RVHAR001` — on the complete common-eligible outer-TRAIN sample through 2023, under
   the **distinct** fit-attempt budget `CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1` at 2/2. That
   budget is separate from, and never borrows against, the parent Section 8 lifetime four-fit
   budget, which remains 4/4 spent and closed.
2. **The exact sealed coefficient/Duan pair** — the BASE coefficient vector with its BASE Duan
   identity and the HAR coefficient vector with its HAR Duan identity, both sealed and verifiable
   before any Validation access. For this confirmatory lineage only, apply the exact Duan formula
   written in parent protocol Section 7 to all and only each model's common-eligible full-outer-TRAIN
   residuals from that model's one deployment fit. Each result is one positive finite model-specific
   factor, never an exploratory factor, never shared, never computed from Validation, never clipped
   and never recomputed. This sampling change is part of the explicit Section 7 supersession below;
   it is not described as unchanged.
3. **One separately authorized outer-Validation opening** over 2024, evaluation only, consistent
   with the parent's lifetime budget of at most one opening and governed by the narrow Section 4
   firewall. Only the parent Section 3 TRAIN-only admission, zero-Validation-request and
   read-TRAIN-only clauses are conditionally superseded; every other parent clause remains
   unchanged.
4. **This proposal's explicitly written Validation aggregation, bootstrap, gate and terminal rules**
   — Sections 5, 6 and 7 of this document, which specify a single-partition Validation stage where
   the parent specified two outer-TRAIN walk-forward folds.

### 0.1.5 `CONDITIONAL_CONFIRMATORY_EXECUTION_SUPERSESSION`

This is a second, conditional confirmatory-execution supersession anchored **solely** in the
same-target confirmatory route recognized by parent budget Sections 2 and 4. It is non-operative
unless the Owner separately ratifies this exact block. Its complete displaced footprint is:

1. **Parent protocol Section 5, solely** its outer-TRAIN predictor-read scope, to permit the exact
   Section 4 predictor firewall for frozen 2024 Validation parents. Predictor formulas, the three
   pinned columns, status vocabulary, common eligibility and every other Section 5 rule remain
   inherited.
2. **Parent protocol Section 7, solely** its fold-local, fold-TRAIN and no-pooled wording, to permit
   one common-eligible full-outer-TRAIN BASE deployment fit followed by one HAR deployment fit, and
   the model-local deployment Duan rule of Section 0.1.4 item 2. Model IDs, columns, estimator,
   diagnostics and all other Section 7 requirements remain inherited.
3. **Parent protocol Section 8, solely** its exploratory-fold extent, lifetime-four-fit and
   no-pooled wording, to create the distinct, nontransferable
   `CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1` 2/2 attempt budget. The historical exploratory
   budget remains 4/4 spent; cumulative maximum fits are exactly four exploratory plus two
   confirmatory. There is no refund, retry, repair or transfer.
4. **Parent protocol Section 10, solely** its fold-specific bootstrap mechanics, replaced for the
   confirmatory stage only by Section 5. The QLIKE definition and sign, row weighting, frozen master
   seed, no-redraw rule and every other Section 10 surface remain inherited; the historical
   exploratory mechanics remain authoritative for V2.
5. **Parent protocol Section 11, solely** its exploratory pass gate and four-fit observation,
   replaced for the confirmatory stage only by Sections 6 and 7. The historical gate and observation
   remain authoritative for V2.
6. **Parent protocol Section 12, solely** its exploratory disposition and pre-fit-underpowered
   wording, replaced for the confirmatory stage only by Sections 6 and 7. Historical V2 disposition
   vocabulary and outcome remain unchanged.
7. **Parent protocol Section 13, solely** to append confirmatory runtime preflights, two ordered
   deployment fits and seals, and the later single Validation evaluation, with stage-specific
   create-once records and counters. Historical records and counters are never rewritten.
8. **Parent protocol Section 14, solely** its re-fit, pooled-fit, repeated-execution and
   Validation-access bars to the minimum necessary for the two predeclared deployment fits and one
   separately granted opening. No tuning, rescue, redraw, new target or additional execution is
   admitted.
9. **Owner co-ratification record Section 3, solely** its canonical stage sequence, exploratory
   disposition vocabulary and historical `UNOPENED` wording, prospectively and only after the unique
   Validation-opening witness, to append the confirmatory stages above. Those historical statements
   remain true for V2 and are never retroactively changed.

The historical V2 lineage remains immutable, 4/4 spent and no-retry; `TARGET_SPACE_003` remains
consumed; no new target slot exists; and Final Test remains `SEALED`. Every parent clause outside
the exact displaced footprint above and the separate Section 4 request-firewall supersession is
inherited. Grant 1 and Grant 2 are invalid unless each cites and binds this exact block.

**Everything not expressly displaced by Sections 0.1.5 and 4 remains inherited.** Any additional
conflict, omission, normalization, paraphrase, rounding or "equivalent" restatement is
nonconforming. Neither supersession is operative without separate Owner ratification.

### 0.1.6 No authority

This section binds nothing now. Naming, defining, enumerating and citing the inherited contract
creates **no** authority: no ratification, no implementation, no fit permit, no target, path, data or
provider access, no Validation opening, no Final-Test access, no staging, no commit and no push. The
verifier described in Section 0.1.2 has not been written, authorized or run, and this preparation
slice does not run it.

## 1. Frozen scientific choices carried forward unchanged

**This section is a non-authoritative readability index only.** The bullets below are a short
human-readable pointer into the `INHERITED_SCIENTIFIC_CONTRACT` of Section 0.1. They **cannot
replace, narrow, normalize, reword or supersede the exact parent bytes**, and they are not the
completeness root. Where a bullet here and the parent bytes differ in any degree, the parent bytes
control and the difference is a defect in this index, never an amendment. A future implementation
must bind Section 0.1 and the parent bytes, never this list.

A confirmatory stage is only confirmatory if it re-uses the exploratory specification without
alteration. The following choices are carried forward **unchanged and unnegotiable**. Changing any
of them converts the stage back into exploration and voids its confirmatory status.

- **Target:** `RV_FWD_60`. Exactly one target.
- **Horizon:** exactly one horizon. No multi-horizon sweep, no horizon selection.
- **Predictors:** `X60`, `X120`, `X240`.
- **Seasonal adjustment:** the early-close-aware harmonic. Early-close sessions are handled by the
  same early-close-aware harmonic construction used in the exploratory stage. The known
  `early_close_session` typing hazard must be honoured by any future implementation, not silently
  re-introduced.
- **BASE model:** `RVBASE001`.
- **HAR model:** `RVHAR001`.
- **Estimator:** ordered `float64` OLS. Row order and dtype are part of the specification, not an
  implementation detail.
- **Retransformation:** the exploratory fold-local Duan rule remains historical. Conditionally for
  confirmatory execution only, Sections 0.1.4 and 0.1.5 define one full-outer-TRAIN model-local Duan
  factor for BASE and one for HAR. Factors are never shared, averaged or substituted.
- **Eligibility:** common eligibility. BASE and HAR are estimated and evaluated on exactly the same
  eligible rows, so that no comparison is contaminated by differing sample coverage.
- **No clipping, no flooring, no imputation.** Ineligible or missing observations are excluded by
  the eligibility rule, never repaired, filled, winsorised or bounded.
- **Loss:** QLIKE. Exactly one loss function, fixed in advance.

## 2. Target-space and budget separation

### 2.1 Target-space accounting

- `TARGET_SPACE_003` is **CONSUMED**, and that consumption is **irreversible**.
- This protocol is **same-target downstream confirmation** of the frozen `RV_FWD_60` target under
  that already-consumed slot. It is **not** a new target-space hypothesis and **not** a new slot.
- It creates, opens, reserves, releases, exchanges, replenishes and renames **zero** target-space
  entitlement. It does **not** create `TARGET_SPACE_004`.
- The V2 exploratory lineage remains **4/4 spent, immutable and no-retry**, and every terminal and
  `TERMINAL_NO_RETRY` record in it remains unchanged. This protocol does not reopen, retry, repair,
  replace, extend, relabel or supersede V2. If it is later separately ratified and authorized, it
  begins a **distinct downstream confirmatory lineage on the same frozen target**.
- Consistent with the ratified project hypothesis budget, stating that no target-space entitlement
  remains must **not** be read as forbidding this separately authorized downstream confirmation
  route. The budget expressly allows advancing the same frozen target to a separately authorized
  confirmatory protocol and classifies that as confirmation rather than a new target-space slot.

### 2.2 Fit-budget accounting

The **original exploratory fit budget remains 4/4 spent**. It is closed. Nothing in this protocol
reopens it, refunds it, reinterprets it, or borrows against it. The exploratory fits are not
re-usable as confirmatory fits, and the exploratory coefficients are not re-usable as deployment
coefficients.

If and only if the Section 0.1.5 supersession is separately ratified, the cumulative maximum is
exactly four historical exploratory fits plus two confirmatory deployment attempts. The budgets are
nontransferable; neither can refund, borrow from, repair or retry the other.

This protocol proposes a **distinct future budget**, separately named:

> `CONFIRMATORY_OUTER_TRAIN_DEPLOYMENT_FITS_V1` — budget **2/2**

That 2/2 extent is a **fit-attempt budget only**. It counts attempts, not successes. It is not
target-space entitlement, not a target-space reservation, and not a licence to read any target,
path, partition, provider or data beyond what a separate Owner grant names explicitly.

This budget does not exist yet. It would come into existence only if the Owner ratifies this
protocol and then separately grants it.

### 2.3 No authority created by this accounting

This accounting and this proposal grant no current fit, no target, path, data or provider access,
no Validation, no Final Test, no implementation, no staging, no commit and no push authority.

## 3. Proposed confirmatory outer-TRAIN deployment fits

Grant 1 must cite and bind the exact Section 0.1.5 supersession. No fit is conforming without it.

### 3.0 Data-free `C0` execution preflight

Before any confirmatory reservation or either fit permit, a separately authorized data-free `C0`
preflight create-once binds the current execution runtime identity, then immediately re-records the
identity before reservation or either permit and requires exact equality with the sealed `C0`
identity. It bytewise replays the frozen reviewed golden fixture with the ratification-bound tools
and schema. Refusal, mismatch or replay failure consumes 0/2 permits, performs zero fits, keeps
Validation `UNOPENED` and occurs before scientific terminal-class closure: it is a pre-start
procedural refusal, not one of the four scientific terminal classes. A later attempt to qualify a
runtime requires fresh Owner authority.

### 3.1 Extent and order

- Exactly **two** fits, in this fixed order: **BASE first, then HAR**.
- Each fit is performed on the **complete common-eligible outer TRAIN sample through 2023**.
- Both fits occur **before any Validation access whatsoever**. Validation data is not read, sampled,
  counted, inspected or previewed during the fit stage.
- These are deployment fits: they produce the exact coefficient vectors and Duan factors that will
  later be evaluated. They are not a search, not a tuning pass, and not a model-selection step.

### 3.2 Permit semantics

- Each fit consumes exactly one permit from the 2/2 budget. Permits are consumed at attempt, not at
  success.
- **A failed fit consumes its permit.** A failure — error, non-convergence, eligibility violation,
  dtype or ordering violation, integrity mismatch — terminates the stage at
  `INVALID_EVIDENCE`, with **Validation unopened**.
- There is no third fit, no repair fit, no re-fit and no retry. The budget cannot be extended by
  reclassifying a failure.

### 3.3 Sealing

Before any Validation access, **both** model artifacts must be sealed: the BASE coefficient vector
and BASE Duan identity, and the HAR coefficient vector and HAR Duan identity. Sealing must occur
for both models and must be verifiable afterwards. If either seal is absent, incomplete or fails
verification, Validation must not open and the stage ends `INVALID_EVIDENCE`.

Each sealed Duan factor is produced by applying the exact parent Section 7 formula to all and only
that model's common-eligible full-outer-TRAIN residuals from its single deployment fit. It must be
positive and finite, is sealed with that model's coefficients, and is never an exploratory factor,
shared, Validation-derived, clipped or recomputed.

## 4. Proposed Validation opening

This section proposes one narrow firewall transition. It supersedes **only** the parent protocol
Section 3 clauses that admit TRAIN parents only, require zero Validation requests, and permit reads
from TRAIN only. It does not supersede any source identity, request-before-provider ordering,
anti-masking rule, target contract, predictor contract, key identity, offset, formula, ordering,
counter, seal or Final-Test protection.

Grant 2 must cite and bind both this exact request-firewall supersession and the exact Section 0.1.5
confirmatory-execution supersession.

The supersession cannot occur unless the confirmatory protocol has been ratified with the Section
0.1 parent binding, both ordered deployment fits have completed and been sealed, both seals have
verified, and the Owner has issued a separate explicit Grant 2. A separately authorized data-free
`C0V` preflight must then create-once bind the current scoring runtime identity, immediately
re-record it before the witness, and require exact equality both with the sealed `C0` identity and
with its own immediate pre-witness re-record. It bytewise replays the same frozen reviewed golden
fixture. Refusal, mismatch or replay failure creates no witness, causes no Validation access, occurs
before scientific terminal-class closure as a pre-start procedural refusal, and does not authorize
a refit. Any later runtime requalification requires fresh Owner authority and must reuse the same
sealed coefficients with zero new fits. Only after `C0V` passes may an authorized create-once
deterministic mechanism durably create exactly one Validation-opening witness **before any**
Validation metadata, parent, predictor, target, path, provider or value is accessed. The opening is
never inferred from, bundled with, or implied by fit authority.

Before that witness exists, the parent Section 3 rules apply in full: no Validation request or read
is admissible. After the unique witness exists, and exactly once:

1. admit only the frozen outer-Validation 2024 parents;
2. construct the Validation request keys with the same ordered request tuple, offsets, formula,
   identity and ordering required by the parent contract;
3. seal the complete Validation request set before any lookup;
4. require this Validation stage's TRAIN request count to equal zero and its Final-Test request
   count to equal zero before provider invocation;
5. read only keys in that sealed Validation target set, through the inherited source and provider
   surfaces;
6. before any predictor lookup, mechanically bind the exact Cell 8 and Cell 14 identities; freeze
   and seal the complete ordered 2024 Validation predictor-row identity set and exactly the three
   pinned Cell 14 predictor columns; read only those columns for the frozen parents; require both
   TRAIN and Final-Test predictor request counters and read counters to equal zero before provider
   invocation, with every Final-Test predictor counter remaining zero throughout; create once a
   complete predictor-status ledger under the inherited `PREDICTOR_USABLE`,
   `PREDICTOR_UNUSABLE`, `PREDICTOR_NONFINITE` and `PREDICTOR_NONPOSITIVE` rules; classify a
   declared-missing predictor as unusable, but any present nonfinite or nonpositive predictor as
   `INVALID_EVIDENCE` for this stage; and join the complete target and predictor ledgers only by
   exact decision identity and timestamp to form the common mask, with no row discretion; and
7. evaluate only, with no fit, refit, recalibration, threshold adjustment, tuning or specification
   change. Every Final-Test surface counter must remain zero and Final Test must remain `SEALED`.

The inherited source identities, request-before-provider sequence, prohibition on masking a
protected target after construction, complete target contract and Final-Test firewall remain in
force throughout. A missing or duplicate witness, witness replay, extra key or parent, incomplete
request set, lookup before sealing, lookup outside the sealed set, or any nonzero Final-Test counter
is `INVALID_EVIDENCE`, terminal and no-retry. This is preparation only: no witness, request set,
counter, access or authority exists now.

## 5. Proposed evaluation procedure

### 5.1 Per-row Validation statistics

For each common-eligible Validation row `i`, with positive finite actual variance `a_i` and
positive finite forecasts `f_BASE_i` and `f_HAR_i`:

```text
L_BASE_i = a_i / f_BASE_i - ln(a_i / f_BASE_i) - 1
L_HAR_i  = a_i / f_HAR_i  - ln(a_i / f_HAR_i)  - 1
d_i      = L_BASE_i - L_HAR_i
```

A positive `d_i` favours `RVHAR001`, so that a positive aggregate means HAR improves on BASE.

### 5.2 Equal-row-weighted aggregation

Let `N` be the number of common-eligible Validation rows. The aggregates are defined **exactly**
as equal-row-weighted means over those `N` rows:

```text
M_BASE = sum(L_BASE_i for i = 1..N) / N
M_HAR  = sum(L_HAR_i  for i = 1..N) / N
D      = sum(d_i      for i = 1..N) / N
```

Every eligible row carries the same weight. **Mean-of-session-means aggregation and any other
equal-session weighting are explicitly prohibited** as the aggregation rule — for `M_BASE`, for
`M_HAR`, for `D`, for the relative reduction, and for every bootstrap replicate at every block
length, primary and diagnostic alike.

Mathematically `D = M_BASE - M_HAR`, but that identity is not a bitwise assertion. The authoritative
stored `D` is the direct reduction of `d_i` specified in Section 5.5.

### 5.3 Relative QLIKE reduction

```text
RELATIVE_QLIKE_REDUCTION = (M_BASE - M_HAR) / M_BASE
```

`M_BASE` must be finite and strictly greater than 0, and `M_HAR` must be finite and greater than
or equal to 0. If either requirement fails, the quantity is undefined and the stage does not
score. The threshold is `RELATIVE_QLIKE_REDUCTION >= 0.10`, and exact equality at 0.10 **passes**.

### 5.4 Frozen Validation bootstrap

- **Session table.** Build one strict chronological table of unique Validation sessions. For each
  session `s`, store its row count `n_s` and its improvement sum `S_s = sum(d_i for i in s)`.
- **Block order and replications.** Exactly three runs, in this exact order: block lengths **5**,
  then **1**, then **20**, with exactly **2,000** replications each. Block length 5 is the
  **primary**; 1 and 20 are **diagnostics only**.
- **Seeds.** `master_seed = 20260809`, frozen. For block length `L`:

```text
pooled_seed     = master_seed + 90000 + L
validation_seed = pooled_seed + 1000
```

  Validation is the sole partition of this stage and sits at zero-based partition index `0`, which
  is exactly why its offset is one `1000` step. Draws are generated by
  `numpy.random.default_rng(validation_seed)` and by nothing else.
  The frozen Validation seed schedule is deliberately reused for byte-identical replay. A replay is
  not an independent Monte Carlo experiment, and neither the repeated deterministic stream nor the
  two diagnostic block lengths receive multiplicity or independent-evidence credit.
- **Draw construction.** With `N_sessions` unique Validation sessions, require
  `N_sessions >= L`. Then `blocks_needed = ceil(N_sessions / L)`. Sample `blocks_needed` starts
  independently and uniformly **with replacement** from the inclusive range `0..N_sessions - L`.
  Expand each start into `L` non-circular consecutive session indices, concatenate them in draw
  order, and truncate to exactly `N_sessions` indices. There is **no wrapping** and **no
  cross-partition** sampling of any kind.
- **Replicate statistic.** For each replication, over the selected sessions:

```text
D_star = sum(S_s for selected s) / sum(n_s for selected s)
```

  This is the pooled row-weighted improvement, **not** the mean of session means. BASE and HAR are
  evaluated on **identical paired draws**; the two models are never resampled separately.
- **Primary lower bound.** The one-sided 95 percent lower bound is
  `numpy.quantile(D_star replicates, 0.05, method="linear")` over the 2,000 primary replicates.
  Every replicate must be finite. The bound must be **strictly greater than 0**; exact equality at
  0 **fails**.
- **No rescue.** No redraw, no reseed, no best-of-seeds. The 1-session and 20-session diagnostics
  report robustness only. They never override, replace or rescue the primary 5-session result and
  are never promoted to primary after seeing results.

### 5.5 Exact bitwise decision semantics and runtime binding

The following is the sole authoritative numerical materialization for the Section 5 decision
statistics. Equivalent mathematics is not an implementation substitute.

1. **Row losses.** Materialize C-contiguous `numpy.float64` arrays `a`, `f_BASE` and `f_HAR` once,
   together, in one strict chronological row order. Within one exact
   `numpy.errstate(over='raise', divide='raise', invalid='raise', under='ignore')` context, perform
   exactly these NumPy ufunc operations in this order:

```text
r_BASE = a / f_BASE
L_BASE = r_BASE - numpy.log(r_BASE) - numpy.float64(1.0)
r_HAR  = a / f_HAR
L_HAR  = r_HAR - numpy.log(r_HAR) - numpy.float64(1.0)
d      = L_BASE - L_HAR
```

   Each input, intermediate and output is `float64`; every authoritative output is finite.
2. **Authoritative reductions.** Every sum is a left-to-right traversal of stored order with
   `acc = numpy.float64(acc + value)`. Reduce `L_BASE`, `L_HAR` and `d` separately, then divide each
   accumulator by `numpy.float64(N)` to obtain `M_BASE`, `M_HAR` and `D`. The `D` gate uses the
   direct reduction of `d`, while relative reduction is exactly
   `numpy.float64(numpy.float64(M_BASE - M_HAR) / M_BASE)`. Parallel, BLAS, tree, pairwise,
   reordered or compensated summation, `Decimal`, and higher precision are prohibited. The
   mathematical identity `D = M_BASE - M_HAR` is not a bitwise assertion. Gate comparisons use the
   raw stored values against `numpy.float64(0.0)` and `numpy.float64(0.10)`, with no rounding or
   tolerance.
3. **Session aggregates.** Session order is order of first chronological occurrence and row order
   within each session is preserved. Each `n_s` is a positive integer. Each `S_s` is formed by the
   same stored-order `float64` left fold over that session's `d` values.
4. **Draw matrices.** Use block lengths in the exact order `(5, 1, 20)`. For each `L`, create one
   fresh `rng = numpy.random.default_rng(validation_seed)` using the pre-bound PCG64 bit-generator
   module/class. For each replicate `r = 0..1999`, make exactly one call
   `rng.integers(low=0, high=N_sessions-L+1, size=ceil(N_sessions/L), dtype=numpy.int64,
   endpoint=False)`. Expand returned starts in returned order, each with
   `numpy.arange(start, start+L, dtype=numpy.int32)`; concatenate in that order, truncate to
   `N_sessions`, and store row `r` in one C-contiguous `numpy.int32` draw matrix. Bulk generation,
   shared RNG state between block lengths, reseeding, skipping, redrawing and every other RNG call
   are prohibited.
5. **Replicate vector and quantile.** Traverse replicates in index order. Within each replicate,
   traverse selected sessions in draw order, including repeats. Form `num` by the prescribed
   `float64` left fold over `S_s`, form `den` by the prescribed `float64` left fold over
   `numpy.float64(n_s)`, and store `D_star[r] = numpy.float64(num / den)` in a C-contiguous
   `numpy.float64` vector. The denominator and result must be positive and finite. For each `L`,
   exactly one call `numpy.quantile(D_star, numpy.float64(0.05), method='linear')` is authoritative;
   no alternate or second calculation is permitted.

Before protocol ratification, separate exact code-only Owner authority must create and review the
historical verifier, runtime-identity generator and verifier, golden-fixture generator and verifier,
and synthetic tests. Ratification binds their exact reviewed code and schema bytes, the frozen
golden-fixture bytes, and their machine outputs. It does **not** bind a live execution or scoring
runtime identity that cannot yet exist.

At `C0` and again at `C0V`, the authorized generator records the then-current identity: Python
implementation and full version; NumPy full version; OS, kernel, CPU architecture and byte order;
`float64` dtype and `finfo`; RNG bit-generator module/class; and NumPy compiler, libc, SIMD, CPU,
math, BLAS and LAPACK identities. `C0` immediately re-records before reservation or permit and must
equal its create-once sealed identity. `C0V` immediately re-records before the witness and must equal
both the sealed `C0` identity and its own create-once sealed identity. Exact equality is checked at
each named boundary.
The same frozen golden fixture bytewise replays draw matrices, row losses and means, session
aggregates, `D_star` vectors and quantile output. `C0` or `C0V` refusal occurs before scientific
terminal-class closure and is a pre-start procedural refusal, not one of the four scientific
terminal classes. `C0` refusal consumes no fit permits; `C0V` refusal creates no witness or access
and cannot authorize refitting. Every digest or hash-bearing block is machine-generated only; no
agent may type, copy, shorten or repair it.

## 6. Proposed PASS criteria

A `PASS` requires **all** of the following, jointly, on the primary 5-session configuration:

1. `D`, the equal-row-weighted mean BASE-minus-HAR QLIKE difference of Section 5.2, is **greater
   than 0** (strict).
2. `RELATIVE_QLIKE_REDUCTION`, computed exactly as in Section 5.3 with finite `M_BASE > 0` and
   finite `M_HAR >= 0`, is **greater than or equal to 0.10**.
3. The primary 5-session one-sided 95 percent bootstrap lower bound of Section 5.4 is **greater
   than 0** (strict).
4. Exact counters, integrity checks and budget accounting all reconcile: two fits attempted, two
   fits succeeded, both seals verified, one Validation opening, no extra access.

**Equality handling is fixed in advance and asymmetric by design:**

- Equality **fails** criterion 1 (a mean of exactly 0 is not an improvement).
- Equality **fails** criterion 3 (a lower bound of exactly 0 does not exclude no-effect).
- Equality **passes** criterion 2 (a relative reduction of exactly 10 percent meets the threshold).

Any failure of any criterion is a failure of the whole. Criteria are never relaxed, reweighted or
re-derived after seeing the result.

## 7. Terminal classes

The confirmatory stage ends in exactly one of four terminal classes:

- `CONFIRMED_ON_OUTER_VALIDATION_FINAL_TEST_PROTOCOL_ELIGIBLE` — all PASS criteria met. This makes
  the lineage *eligible to have a Final Test protocol written*. It does not open the Final Test.
- `NOT_CONFIRMED_ON_OUTER_VALIDATION_TEST3_TERMINAL` — the evaluation ran correctly and did not meet
  the criteria. Test 3 ends here. This outcome is a real scientific result and must be recorded as
  such.
- `UNDERPOWERED_STOP` — exactly one of the exhaustive, measurable structural triggers in Section
  7.1 fired. This is a stop, not a licence to gather more data, extend the window or try again.
- `INVALID_EVIDENCE` — a fit failed, a seal was missing or unverifiable, a counter or integrity check
  did not reconcile, or the budget was violated. Validation remains unopened, or its result is
  discarded. No claim of any kind may be made from an `INVALID_EVIDENCE` stage.

Every terminal class is **no-retry**.

The four classes apply only after the relevant scientific stage starts. `C0` and `C0V` refusal,
mismatch or replay failure occurs before scientific terminal-class closure and is recorded solely
as a pre-start procedural refusal, never as one of these four classes.

### 7.1 Exhaustive `UNDERPOWERED_STOP` triggers

`UNDERPOWERED_STOP` has exactly the two structural trigger groups below and no others. Every
trigger is measurable, and each is evaluated before the quantity it protects is computed. No
discretionary, qualitative or "not informative enough" judgement may declare this class.

**Trigger group A — deployment pre-fit, before either confirmatory permit is consumed.**

- The count of common-eligible outer-TRAIN rows is **not greater than** the number of fitted
  columns, for `RVBASE001` or for `RVHAR001`; or
- either ordered float64 training design is **rank deficient** relative to its fitted column count.

A group A stop occurs with Validation **UNOPENED**, **0/2** permits consumed, and **zero**
confirmatory fits performed.

**Trigger group B — after the single Validation opening and after complete valid ledgers and the
common mask, but strictly before any Validation forecast, QLIKE or bootstrap scoring.**

- The common-eligible Validation set is **empty**; or
- there are **fewer than 20** unique chronological eligible Validation sessions; or
- the exact finite-support state defined in Section 7.1.1 occurs at any lag `k` in `1..8`, recorded
  as the non-numeric structural reason `ACF_LAG_SUPPORT_UNDEFINED`.

A group B stop occurs after the sealed **2/2** deployment fits and after the one Validation
opening, but before any forecast, QLIKE or bootstrap computation, and is recorded with truthful
counters.

Design effect and ESS remain **disclosure only** in both groups. Neither carries a threshold, and
neither can trigger, prevent or modify any terminal class.

A failure of `max(outer-TRAIN label_end_time) < min(Validation decision_time)`, any purge or
chronological-order violation, and a wall-clock decision boundary gap below 60 minutes are
partition/purge integrity failures. They are always `INVALID_EVIDENCE`, even if discovered after
the Validation witness; they are never group B and never `UNDERPOWERED_STOP`.

### 7.1.1 Exact within-session `RV_FWD_60` ACF algorithm

The ACF trigger in group B is defined by exactly the following algorithm. No other computation,
ordering, pairing, approximation or fallback may be substituted for it.

**Precondition.** The ACF runs **only after** source, request, partition, ledger and common-mask
integrity have all passed. If any of those has not passed, the class is `INVALID_EVIDENCE` and the
ACF is not computed at all.

**Materialization.** Materialize the common-eligible Validation rows exactly once, in strict
chronological order. Require:

- unique `(session_id, decision_time)` keys;
- timezone-aware `decision_time` values; and
- finite, strictly positive `RV_FWD_60` for every materialized row.

Any duplicate key, naive timestamp, nonfinite value or nonpositive value is `INVALID_EVIDENCE`.

**Pairing.** For each lag `k = 1..8`:

1. group rows by **exact NYSE session identity**;
2. within a session, pair row `i` with row `i - k` **only when**
   `decision_time_i - decision_time_(i-k)` equals **exactly** `15 * k` minutes;
3. never pair across sessions, and never substitute a nearest, rounded or approximate spacing;
4. pool the accepted pairs across sessions in deterministic session-then-chronological order.

Session-level correlations are **never** averaged. Pairs are pooled, and the correlation is computed
once on the pooled vectors.

**Vectors.** Convert the pooled current values and prior values to `float64`, and record the pair
count.

**Finite-support test.** If the pair count is **less than 2**, or if either vector has
`numpy.std(..., ddof=0) == 0`:

- do **not** call `numpy.corrcoef`;
- record `rho_observed(k)` as **absent/null** — never `NaN`, never infinity, never a sentinel
  number; and
- record the non-numeric structural reason `ACF_LAG_SUPPORT_UNDEFINED`.

This exact finite-support state, and only this state, is `UNDERPOWERED_STOP`, declared **before** any
Validation forecast, QLIKE or bootstrap computation.

**Computation.** Otherwise compute exactly:

```text
rho_observed(k) = float(numpy.corrcoef(current_values, prior_values)[0, 1])
```

Any exception raised at this step, and any nonfinite result at this step, is `INVALID_EVIDENCE` —
**not** underpowered — because sufficient nonzero-spread support was present and the numerical step
nevertheless failed.

**Recording.** A finite result is recorded together with:

```text
rho_null(k) = max(1 - k/4, 0)
excess(k)   = rho_observed(k) - rho_null(k)
```

**Sufficiency.** All eight lags `k = 1..8` must yield finite `rho_observed(k)` values before scoring
may proceed.

**Disclosure only.** With `N_rows` the common-eligible Validation row count:

```text
DESIGN_EFFECT = max(1, 1 + 2 * sum(max(rho_observed(k), 0) for k = 1..8))
ESS           = N_rows / DESIGN_EFFECT
```

Both are **disclosure only**. Neither carries a threshold, and neither can trigger, prevent or
modify any terminal class.

### 7.2 Exact precedence — non-overlapping by construction

Classification follows this fixed order and never departs from it. The tiers are mutually exclusive:
a condition matching a tier 1 description is tier 1 even if it superficially resembles tier 2.

1. **Integrity first — always `INVALID_EVIDENCE`, never underpowered.** Any defect of input, domain,
   identity, ordering, duplication, partition, request, common mask, purge, counter or seal; target
   zero variance; nonfinite or nonpositive `RV_FWD_60` input; any conversion or arithmetic
   exception; a wrong ACF lag, wrong pairing, wrong ordering or wrong formula relative to Section
   7.1.1; any use of `NaN` or infinity to represent missing support; and a nonfinite `corrcoef`
   result obtained **after** sufficient nonzero-spread support was present — each of these is
   `INVALID_EVIDENCE`. None may ever be relabelled `UNDERPOWERED_STOP`.
   This expressly includes a non-strict TRAIN-label/Validation-decision boundary and a boundary gap
   below 60 minutes, regardless of when either defect is discovered.
2. **Structural support second — only after integrity passes.** At the ACF, exactly one condition
   yields `UNDERPOWERED_STOP`: a pooled pair count **less than 2**, or a `ddof=0` spread of
   **exactly zero** in either pooled vector, recorded as the non-numeric reason
   `ACF_LAG_SUPPORT_UNDEFINED`. The remaining Section 7.1 group A and group B triggers are evaluated
   in this same tier. No numerical failure and no implementation defect may enter this tier.
3. **Scoring third — only after all eight finite ACF values and every other structural gate have
   passed.** Only then may forecasts, QLIKE and the bootstrap be computed. Any numerical, runtime or
   record failure occurring after scoring has started is `INVALID_EVIDENCE` — never
   `UNDERPOWERED_STOP`, and never a scored result.
4. A valid scored result that misses any Section 6 criterion is
   `NOT_CONFIRMED_ON_OUTER_VALIDATION_TEST3_TERMINAL`.
5. A valid scored result that meets every Section 6 criterion is
   `CONFIRMED_ON_OUTER_VALIDATION_FINAL_TEST_PROTOCOL_ELIGIBLE`.

**Exhaustive trichotomy.** For the ACF and every gate governed by it, exactly one of three states
holds:

- **finite supported ACF** — sufficient support and a finite correlation: the stage proceeds;
- **exact finite insufficient support** — pair count below 2, or zero `ddof=0` spread:
  `UNDERPOWERED_STOP` via `ACF_LAG_SUPPORT_UNDEFINED`;
- **any implementation, input or numerical defect** — `INVALID_EVIDENCE`.

There is no fourth state and no overlap. **If two descriptions could both appear to apply, integrity
wins** and the class is `INVALID_EVIDENCE`.

Every terminal class reached under this precedence is terminal and **no-retry**.

## 8. Prohibitions

- **No tuning.** No hyperparameter, window, eligibility, transformation or loss adjustment at any
  point in the confirmatory stage.
- **No rescue.** A failing result may not be salvaged by switching to a diagnostic block length, a
  different loss, a subsample, a different horizon, or a re-specification.
- **No retry.** Neither the fit stage nor the Validation opening may be repeated. A terminal class
  is terminal.
- **The Final Test remains SEALED** throughout. Nothing in this protocol opens it, prepares access
  to it, or creates a path toward it. Test 3b and Test 4 likewise remain unauthorized.

## 9. What still must happen before anything runs

1. Before ratification, separate exact code-only Owner authority creates and reviews the historical
   verifier, runtime-identity generator/verifier, golden-fixture generator/verifier and synthetic
   tests. No scientific access or fit is part of that authority.
2. The reviewed historical verifier resolves the exact parent bytes under Section 0.1.2. Separate
   Owner ratification then binds the exact reviewed tool/schema/golden bytes and machine outputs,
   the historical parent-binding block, and both exact supersession blocks. It binds no live runtime
   identity.
3. Independent cross-family review accepts the implementation that claims to realise the ratified
   protocol, including Duan sampling, both supersessions, integrity precedence and golden replay.
4. Activation reruns historical verification, binds the future ratification and matches the
   machine-generated parent-binding block before any scientific action.
5. A separate Owner Grant 1 cites Section 0.1.5. Before reservation or either permit, separately
   authorized data-free `C0` creates/binds the current execution identity, checks exact equality and
   replays the golden fixture. Failure consumes 0/2, performs zero fits, keeps Validation unopened
   and creates no scientific terminal result.
6. Only after `C0` passes may the two ordered deployment fits occur and seal their coefficients and
   full-outer-TRAIN model-local Duan factors.
7. A separate Owner Grant 2 cites Sections 0.1.5 and 4 and may issue only after both seals verify.
   Before the witness, separately authorized data-free `C0V` creates/binds the current scoring
   identity, checks exact equality and replays the same golden fixture. Failure creates no witness
   or access and authorizes no refit; later requalification needs fresh Owner authority and reuses
   the same sealed coefficients with zero new fits.
8. Only after `C0V` passes may the create-once durable Validation-opening witness precede any
   Validation metadata, parent, predictor, target, path or provider access.

None of those eight has occurred. Until all apply in order, this document is a proposal only.

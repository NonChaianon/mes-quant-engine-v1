# Owner Co-Ratification — Test 3 Confirmatory Validation Protocol V1 and Signed Bootstrap Erratum V1

**Label:** `UPLOAD_READY_SCRATCH / NON_OPERATIVE_UNTIL_AUTHENTICATED_OWNER_COMMIT / NO_AUTHORITY`

## 1. Standing of this file

- This file currently exists only in the local review scratch area. It is not in the repository, it is not tracked, and it binds nothing.
- Claude mechanically prepared these bytes under explicit Owner instruction. Preparation is a drafting act only. Claude holds no ratification authority, exercised none, and does not review or attest this file.
- Authority arises only when the Owner personally uploads these exact bytes, without editing, reformatting, re-wrapping or any normalization, through the authenticated GitHub action described in Section 3, and every post-commit machine-verification predicate in Section 4 passes.
- Until that moment, this document is a proposal carrier. It is not ratification, not implementation acceptance, not activation, not `C0`, not `C0V`, not a grant, not a permit, not a Validation opening and not scientific execution.
- No digest, checksum, commit identifier, tree identifier, blob identifier or any other Git object identifier appears anywhere in this document, and none may ever be typed, copied, abbreviated, repaired or approximated into it. Identities below are stated relationally and by exact path only.

## 2. Exact future repository destination

- Destination path once uploaded: `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_V1.md`
- Exact ref: `refs/heads/governance/test3-confirmatory-validation-preparation-v2`
- These bytes are ratification only at that exact path on that exact ref. The same bytes committed to any other path, any other ref, or any other repository are `NO_AUTHORITY`.

## 3. The exact Owner GitHub commit

The Owner must produce exactly one commit on the exact ref whose sole additions, in this declared order, are:

1. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md`
2. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md`
3. `tools/prepare_test3_confirmatory_validation_prerequisites.py`
4. `tests/test_prepare_test3_confirmatory_validation_prerequisites.py`
5. `docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json`
6. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_V1.md`

Required structural properties of that commit:

- It must be the **direct child** of the already authenticated V2 Owner Source commit on the exact ref — that is, the commit that added `docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_SLICE_OWNER_SOURCE_V2.md` as its sole delta and passed its own post-commit verification.
- There must be **no intervening commit** of any kind between that authenticated V2 Owner Source commit and this ratification commit on the exact ref.
- It must contain **no modification, no deletion, no rename and no move** of any existing tracked path.
- It must contain **no addition other than the six ordered paths above**, and no fewer than those six.
- Its committer must be the Owner acting through the authenticated GitHub account, with valid provider commit verification.

## 4. Mandatory post-commit machine verification

An independent machine check must confirm all of the following after the commit exists. Until every predicate passes, the commit is `NO_AUTHORITY` and nothing in Section 5 has any effect.

- **Exact ref.** The commit is on `refs/heads/governance/test3-confirmatory-validation-preparation-v2` and on no substituted or renamed ref.
- **Direct parent.** The commit has exactly one parent, and that parent is the authenticated V2 Owner Source commit described in Section 3, with no intervening commit.
- **Sole ordered path delta.** The complete delta is exactly the six additions of Section 3 in that declared order, with zero modifications, zero deletions and zero renames.
- **Exact equality of the five pre-reviewed local artifacts.** Each of the committed blobs for items 1 through 5 is byte-identical to the corresponding pre-reviewed local artifact. No reformatting, whitespace change, line-ending change, encoding change or regeneration is tolerated.
- **Exact equality of this source.** The committed blob for item 6 is byte-identical to these scratch bytes.
- **Pre-pinned Owner actor and provider verification.** The push/commit actor equals the Owner principal already pinned by the authenticated V2 Owner Source lineage, and provider commit verification reports valid.
- **Unchanged excluded local candidates.** The three excluded local candidate files named in Section 6 remain byte-identical and remain outside the commit.

Any mismatch, ambiguity, missing predicate or unverifiable field stops the lineage at `NO_AUTHORITY`. A failed verification is not repairable by a follow-up commit under this document; it requires fresh exact Owner authority.

## 5. Ratification semantics on success

### 5.1 One inseparable co-ratified contract

- The Owner co-ratifies **Protocol V1** and **Signed Bootstrap Erratum V1** as **one inseparable contract**. Neither is ratified alone, and neither may be cited, bound, implemented or executed without the other.
- Erratum V1 supersedes **only** Protocol V1 Section 5.5 item 5, and within it only the positivity requirement as applied to `D_star`. After co-ratification the requirement is: the **denominator must be positive and finite**, and **every stored `D_star[r]` must be finite with its sign unconstrained**.
- Every other clause, sentence and requirement of Protocol V1 and of Erratum V1 remains **unchanged**, including the strict primary fifth-percentile one-sided 95 percent lower-bound greater-than-zero gate with equality failing, the no-rescue and no-redraw rules, the frozen seed schedule and block order, the integrity-first precedence, and the four terminal classes.
- A negative or zero finite replicate is a valid scored outcome and never becomes `INVALID_EVIDENCE` by sign alone. A nonfinite replicate, a nonpositive or nonfinite denominator, and every other integrity, domain, ordering, counter or seal defect remain `INVALID_EVIDENCE`.

### 5.2 Tooling binding — capability only

- The Owner binds the **exact reviewed bytes** of the tool at `tools/prepare_test3_confirmatory_validation_prerequisites.py`, its tests at `tests/test_prepare_test3_confirmatory_validation_prerequisites.py`, and the **existing** binding artifact at `docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json` under the exact classification:

  `TOOLING_CAPABILITY_ONLY / NOT_ACTIVATION / NOT_C0 / NOT_C0V`

- The existing binding's machine outputs bind exactly four things and nothing more: historical parent resolution from repository objects at the parsed historical commit; the tooling-runtime identity; the frozen-contract self-consistency self-check; and the deterministic synthetic golden fixture with its bytewise replay.
- Those outputs **do not** bind any live `C0` execution runtime, any live `C0V` scoring runtime, any scoring execution, any fit, any permit, any reservation or any Validation access. The runtime identity recorded there is tooling-runtime only and is not a `C0` or `C0V` identity.
- Binding these bytes is not implementation acceptance. An implementation that claims to realise the ratified protocol still requires separate independent cross-family review and separate Owner acceptance.

### 5.3 The erratum postdates the existing binding inventory

- The existing tooling binding artifact and its candidate inventory were produced **before** Signed Bootstrap Erratum V1 existed. The erratum is therefore **not contained in, not covered by and not verified by** that earlier binding or its candidate inventory.
- The erratum is bound **separately, by this same authenticated ratification commit**, as item 2 of the Section 3 ordered additions.
- The erratum must never be described, cited or recorded as having been machine-verified, inventoried or hash-bound by the earlier tooling binding. Any such statement is nonconforming and voids reliance on it.

### 5.4 Truthful disclosure of the tooling slice record

- Focused pytest passed **161 of 161**.
- Ruff passed.
- The single `check` command **was invoked**, but its PASS token was **unavailable due to response transport**. It must **not** be claimed as observed. No observed-`check`-PASS claim is made anywhere in this ratification.
- `create` returned `CREATE_PASS`.
- `verify-existing` returned `VERIFY_EXISTING_PASS`.
- The exact-scope firewall passed.
- A fresh final Codex Governance review returned `GO` with zero blocker, zero high and zero low findings.
- Later targeted re-votes by Codex Ultra and by Claude Fable Max both approved the corrected co-ratification.
- All reviewer outputs above are **context and evidence only**. They are not Owner authority, and they do not ratify, activate or accept anything. Only the authenticated Owner commit plus passing post-commit verification confers authority.

### 5.5 Invocation budgets are consumed

- The `check`, `create` and `verify-existing` invocation budgets are **consumed**.
- No rerun, no overwrite, no regeneration and no post-ratification `verify-existing` is permitted or required.
- The reason is structural: a ratification commit necessarily changes `HEAD`, while the existing binding is and must remain an **immutable pre-ratification snapshot**. Re-running a deterministic mode against a moved `HEAD` would not validate the snapshot; it would corrupt the record it is supposed to preserve.
- Absence of a post-ratification rerun is therefore conforming, expected and required, not a gap.

### 5.6 Preserved scientific and budget state

- `TARGET_SPACE_003` remains **CONSUMED**, irreversibly. No new target-space slot is created, opened, reserved, exchanged, replenished or renamed, and `TARGET_SPACE_004` is not created.
- The exploratory lineage remains **four of four spent, closed, terminal and no-retry**.
- The confirmatory deployment fit budget remains **two of two and non-operative**. It does not exist as a usable entitlement until a separate Owner **Grant 1** that cites and binds the exact Section 0.1.5 supersession block.
- A separate **Grant 2**, a separate data-free `C0V`, and the single create-once Validation-opening witness are all required before any Validation access. None exists.
- The **Final Test remains SEALED**. **Test 3b** and **Test 4** remain **unauthorized**.

### 5.7 What this ratification does not create

This ratification creates none of the following, expressly and without implication:

- implementation acceptance, activation, `C0`, `C0V`, a grant, a reservation or a permit;
- any model fit, forecast, retransformation, scoring or bootstrap execution;
- any Validation-opening witness or Validation opening;
- any data, provider, target, path or evidence access;
- any staging, commit or push authority for any agent;
- any merge authority;
- any scientific execution of any kind.

Agents remain read-only with respect to the repository. Every subsequent step named in Protocol V1 Section 9 remains a separate, explicit Owner act in its stated order.

## 6. Excluded existing local candidate files

The following three existing local candidate files are **not** part of this ratification commit and are **not** part of this semantic ratification in any degree:

- `docs/research/TEST3_ONE_SHOT_REAL_TRAIN_V2_REDACTED_CLOSEOUT_V1.md`
- `docs/research/TEST3_ONE_SHOT_REAL_TRAIN_V2_OWNER_DECISION_REQUEST_V1.md`
- `docs/research/TEST3_CONFIRMATORY_VALIDATION_OWNER_AUTHORIZATION_REQUEST_V1.md`

Requirements for these three:

- They are neither added, modified, deleted, renamed nor moved by the Section 3 commit.
- They remain **local candidates** with no ratified status and no authority.
- They must remain **byte-identical** during post-commit verification, and that unchanged state is an explicit verification predicate under Section 4.
- Nothing in this document ratifies, adopts, endorses, supersedes or closes them.

## 7. Owner upload instructions

- Do not edit, reformat, re-wrap, re-encode, re-indent or otherwise normalize these bytes. Upload them exactly as they are.
- Ensure the exact ref `refs/heads/governance/test3-confirmatory-validation-preparation-v2` currently points at the already authenticated V2 Owner Source commit, with no intervening commit added since.
- Using your authenticated GitHub account, prepare **one** commit on that exact ref that adds exactly the six paths of Section 3, in that declared order, and changes nothing else.
- Place these bytes at exactly `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_V1.md`, and place each of the other five artifacts at its exact declared path.
- Commit through the authenticated GitHub action so that provider commit verification is valid and the actor matches the pre-pinned Owner principal.
- After committing, have the independent machine check run every Section 4 predicate. Treat any single failure as terminal `NO_AUTHORITY` and stop; do not repair by follow-up commit under this document.
- Do not run any deterministic tooling mode, any test, any lint, any fit, any scoring or any Validation step as part of this upload. The upload is a governance act only.

## 8. Status

`SCRATCH_ONLY / MECHANICALLY_PREPARED_BY_CLAUDE_UNDER_OWNER_INSTRUCTION / NOT_IN_REPOSITORY / NOT_RATIFIED / NOT_ACTIVATION / NOT_C0 / NOT_C0V / BUDGETS_CONSUMED_NO_RERUN / FINAL_TEST_SEALED / NO_AUTHORITY_UNTIL_AUTHENTICATED_OWNER_COMMIT_AND_FULL_POST_COMMIT_VERIFICATION_PASS`

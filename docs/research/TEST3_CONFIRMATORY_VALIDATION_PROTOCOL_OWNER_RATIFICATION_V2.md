# Test 3 Confirmatory Validation Protocol — Owner Ratification V2

Repository destination path (sixth addition):
`docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_V2.md`

## 0. Status of this document

This document is **scratch and non-operative**. It creates no authority, no ref, no commit and no
scientific permission by existing.

It becomes operative only when **both** of the following have happened, in this order:

1. The Owner explicitly adopts the exact current bytes of this file **and** of the launcher
   `RUN_TEST3_CONFIRMATORY_RATIFICATION_V2_OWNER_ONCE.py`, using the adoption sentence in Section 10.
2. The Owner **personally** runs that launcher under the authenticated GitHub Owner account
   `NonChaianon`.

Until both have happened, no agent and no automation may act on it. This document does not itself
authorize execution; Section 10 adoption is a separate, later Owner act.

## 1. Frozen predecessor — the invalid V2 upload

The current head of `refs/heads/governance/test3-confirmatory-validation-preparation-v2` is
permanently frozen as:

`NO_AUTHORITY / INVALID_ROOT_PATH_PLACEMENT`

It is a provider-verified, Owner-authored direct child of the authenticated V2 Owner Source commit,
but it added all six files at the **repository root** instead of their governed nested paths. Root
placement is a structural defect, not a cosmetic one.

Therefore, permanently and without exception:

- It **must not** be repaired, amended, rebased, reworded or force-updated.
- It **must not** be deleted, reverted, or followed by a cleanup commit.
- Its ref **must not** be retried, reused, extended, or renamed.
- It **must not** be cited as authority, evidence, ratification, or precedent by any agent or human.
- Its six root-placed files **must not** be read as the ratified artifacts.

The invalid ref and its head are preserved untouched as immutable history. Leaving them in place is
the intended terminal disposition.

## 2. Successor ref and mechanically derived base

The successor is the fresh ref
`refs/heads/governance/test3-confirmatory-validation-preparation-v3`, which must not exist before the
single authorized run.

Its base is **not** transcribed by any agent or human. It is derived mechanically at run time as:

> the **sole parent** of the current head of
> `refs/heads/governance/test3-confirmatory-validation-preparation-v2`.

Before that parent may be used, the launcher must independently confirm, from the provider, that it
is the authenticated V2 Owner Source commit — that is, the Owner-authored, provider-committed,
provider-verified commit whose **sole** delta added
`docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_SLICE_OWNER_SOURCE_V2.md`, and whose blob at
that path equals, byte for byte, the locally tracked copy of that same file.

No hash, object ID or abbreviated identifier appears anywhere in this document by design. If the
mechanical derivation cannot be completed and confirmed, the run stops.

## 3. Authorized mutation budget

Exactly two remote mutations, in this order, once each, with **no retries**:

1. Exactly one GraphQL `createRef` creating the full fresh V3 ref at the mechanically derived base.
2. Exactly one GraphQL `createCommitOnBranch` on that ref, using `expectedHeadOid` as a
   compare-and-swap guard against the same derived base.

No third mutation of any kind is authorized: no additional commit, no ref update, no ref deletion, no
tag, no pull request, no merge, no branch protection change, no repository setting change, no
workflow dispatch, and no `main` mutation.

**Ref naming.** `createRef` and every ref query use the **fully qualified** V3 ref. The
`createCommitOnBranch` committable-branch input takes the **unqualified branch name** instead,
because that input field is a branch name and not a qualified ref. Passing the qualified ref there
would either fail or address a different branch, so the two forms are never interchanged.

**Pinned transport.** Both mutations and every read go through a single pinned `gh` entrypoint whose
real target must be a regular, executable file that is not group- or world-writable, and every call
is explicitly pinned to the provider host `github.com`, so no ambient host setting can redirect the
transport. The Owner's own machine and account are trusted; this introduces no binary signing,
checksum or attestation infrastructure.

## 4. Exact required delta — six additions and nothing else

The single authorized commit must add exactly these six paths, in this declared order, and must
produce no other change:

1. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md`
2. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md`
3. `tools/prepare_test3_confirmatory_validation_prerequisites.py`
4. `tests/test_prepare_test3_confirmatory_validation_prerequisites.py`
5. `docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json`
6. `docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_V2.md`

## 5. Exact-form requirements

The commit is acceptable only if **all** of the following hold, verified read-only after the fact:

- **Exact byte equality.** Each uploaded path's remote bytes equal, byte for byte, the exact local
  source bytes retained for the whole run. No normalization, re-encoding, line-ending change,
  trimming or reformatting.
- **No root aliases.** None of the six basenames may exist at the repository root, before or after.
- **Additions only.** No modification, deletion, rename, move or mode change of any existing path.
- **No seventh path.** The delta is exactly six added paths; a seventh path of any kind invalidates
  the commit.
- **Direct parent.** The new commit has exactly one parent, and that parent is the derived base.
- **Owner-authenticated author and provider committer.** The author is the authenticated GitHub
  Owner account and the committer is the provider's own web-commit identity. The same author and
  committer identity is required of the frozen invalid head and of the Owner Source parent.
- **Valid provider signature.** The provider reports signature verification as valid, with
  verification reason `valid`, for the frozen invalid head, the Owner Source parent, and the new
  commit.
- **Predecessor byte identity.** The locally tracked V2 Owner Source file equals, byte for byte, the
  sole-parent blob at its governed path.
- **Reviewed-byte identity.** The five reviewed payload sources, and the scratch source of the older
  V1 ratification file, each equal byte for byte their corresponding root-placed blob in the frozen
  invalid V2 commit. Current payload bytes therefore cannot have drifted from the bytes already
  reviewed and already uploaded. Those root paths are read as **byte witnesses only**; they remain
  `NO_AUTHORITY` and are never evidence, ratification or precedent.
- **Final ref identity.** The last postcheck step re-reads the V3 ref and requires it to point at
  exactly the new commit that the postcheck just verified. The same requirement applies when a
  commit response is lost and the outcome is reconstructed by the single permitted probe.
- **Carrier continuity.** The launcher's own bytes and all six local source bytes are retained at
  invocation start, then re-read and required to be unchanged immediately before `createRef` and
  again in the terminal postcheck. Before any provider action the launcher also fails closed
  unless the resolved absolute path of its executing module equals the fixed launcher source path,
  so a copied or substituted launcher cannot rely on the approved carrier retained at that path.
- **No pull request.** The launcher creates no pull request. No pull request in any state — open,
  closed or merged — may be associated with the V3 ref, as base or as head, at preflight or at the
  terminal postcheck. Those are observations at two defined moments; this document claims no control
  over any later human action. This upload is a direct ref write, not a review workflow.
- **Commit headline.** Exactly `governance: ratify Test 3 confirmatory validation protocol V2`.

## 6. What this ratifies

- **Co-ratification.** `TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md` and
  `TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_SIGNED_BOOTSTRAP_ERRATUM_V1.md` are ratified together as
  **one inseparable contract**. Neither may be cited, applied, amended, superseded or relied upon
  without the other. The Erratum is a corrective part of the Protocol, not an optional annex.
- **Tooling capability only.** `tools/prepare_test3_confirmatory_validation_prerequisites.py`, its
  test `tests/test_prepare_test3_confirmatory_validation_prerequisites.py`, and the existing binding
  `docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json` are bound as
  **`TOOLING_CAPABILITY_ONLY`**. Publishing them records that the capability exists and is
  reviewable. It does not authorize running them, does not grant any execution budget, and does not
  create any scientific or activation authority.

## 7. Preserved prior reviewer decisions and disclosures

- All prior cross-family reviewer decisions on these artifacts stand unchanged. This ratification
  neither reopens, re-litigates, upgrades nor downgrades them. Reviewer outcomes recorded outside the
  repository remain operational context, not repository authority.
- **Disclosure — old check-mode PASS token not captured.** In the earlier tooling slice, the tool's
  `check` mode ran but its PASS token was **not captured**. It is therefore not available as
  evidence and must not be reconstructed, restated or inferred. The `create` and `verify-existing`
  modes passed and were captured.
- **Disclosure — old budgets consumed, no rerun.** All budgets for all old tool modes, including the
  uncaptured `check` mode, remain **consumed**. No mode may be rerun to recover the missing token.
  The gap is disclosed and preserved rather than repaired.

## 8. Preserved prohibitions

This ratification preserves, and does not weaken, every existing prohibition. It creates **no**:

- activation of any kind, and no `C0` or `C0V` authority;
- data access, provider access, target access, or evidence access;
- model fit, scoring, backtest, bootstrap, or economic evaluation;
- Validation, Final Test, Test 3 retry, Test 3b, or Test 4 authority;
- scientific execution of any kind;
- Decision C, Phase B, Tier 2, merge, or `main` mutation authority.

Publishing a protocol is not permission to run it. Every one of the above remains an independent,
later, explicit Owner decision.

## 9. Partial-state terminal rules

Every outcome below is **terminal**. In every case: no cleanup, no repair, no deletion, no retry, and
no successor run without fresh explicit Owner authorization.

- **Stop before `createRef` is dispatched.** Nonzero stop code, zero mutation, repository untouched.
  The V3 ref was not created. A zero-mutation classification is emitted **only** here, where no
  mutation has yet been dispatched.
- **Dispatched, outcome unknown.** Each mutation records that it has been dispatched immediately
  before the call is made, and transport failure or interruption at the moment of dispatch is caught
  at that call. Any later failure — including an unexpected internal error or an interrupt —
  therefore reports a stable *dispatched / state-unknown* terminal classification requiring
  independent verification. An accepted-but-response-lost mutation can never be reported as zero
  mutation.
- **Ambiguous or failed `createRef`.** The fresh ref is queried exactly once to record whether it
  exists. Regardless of the answer, the run stops. No commit is attempted, and the ref is never
  deleted.
- **Ref created, commit not dispatched.** Terminal state `REF_CREATED_NO_COMMIT`, claimed only
  while `createCommitOnBranch` has not yet been dispatched. The empty V3 ref is left in place,
  unused and unmerged. It must not be deleted, committed to, or reused.
- **Ambiguous or failed commit.** Once `createCommitOnBranch` has been dispatched, every failure or
  ambiguous path that does not positively verify the intended committed state classifies as
  `COMMIT_DISPATCHED_STATE_UNKNOWN` — including the single probe returning the derived base commit,
  which is never classified `REF_CREATED_NO_COMMIT`, because a lost response can make the true
  outcome unknowable. The V3 ref is queried exactly once. If it changed, a read-only full postcheck
  runs; `COMMIT_CREATED_RESPONSE_LOST` may be reported **only** if that postcheck passes in full.
  Otherwise the run stops in a stable dispatched/state-unknown classification. Never retry, delete
  or repair.
- **Any failed postcheck.** Nonzero `NO_AUTHORITY`. Whatever exists remains untouched and unratified.
- **Successful postcheck.** The launcher prints a terminal token. That token records a passing
  mechanical postcheck only. It does **not** by itself establish authority; independent Codex
  cross-family verification is still required before this ratification may be relied upon.

**Ambiguity rule.** Any ambiguity, unexpected response, transport failure, timeout, drift, unlisted
path, or unverifiable condition stops the run immediately, with no cleanup and no retry. A stop is
always preferred to a guess.

**One-shot semantics, stated honestly.** An invocation without the confirmation flag makes no
provider call at all and does not consume the run. The launcher keeps no durable local attempt
marker at any point. Before `createRef` is dispatched, "exactly once" is an explicit **Owner
covenant**, not a machine guarantee: nothing in the launcher could block a second pre-dispatch
start. After any mutation dispatch, every repeat invocation is prohibited by the Owner's one-shot
covenant. The fresh remote ref is a durable, machine-visible consumed marker **only when it
actually exists**: a later invocation then stops on finding it present, but when `createRef` was
dispatched and the single probe shows the ref absent, a repeat invocation cannot be
machine-prevented and remains prohibited by the covenant alone. There is no automatic retry at any
point.

**Carrier continuity window.** Continuity of these two files *before* the launcher starts is an Owner
no-write covenant and is not machine-checked. From invocation start through the terminal postcheck it
**is** mechanically checked: before any provider action the launcher fails closed unless the
resolved absolute path of its executing module equals the fixed launcher source path, so a copied
or substituted launcher cannot rely on the approved carrier retained at that path; the launcher's
own bytes and the six local source bytes are then retained at start and re-compared before
`createRef` and again in the postcheck, and any difference is terminal. The executing-path gate and
the no-confirmation guard make no network call. No hash artifact is produced, published or required
by this mechanism.

## 10. Owner adoption

Adoption is a separate, later Owner act. This document authorizes nothing until the Owner states the
following sentence exactly, and adoption alone still does not run anything — the Owner must then
personally run the launcher once.

I adopt the exact current bytes of `TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_OWNER_RATIFICATION_UPLOAD_V2.md` and `RUN_TEST3_CONFIRMATORY_RATIFICATION_V2_OWNER_ONCE.py`, and I will personally run that launcher exactly once under my authenticated GitHub Owner account.

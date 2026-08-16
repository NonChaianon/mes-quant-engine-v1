# Repository Protection Architecture V1

Document role: PRE-ACTIVATION GOVERNED SPECIFICATION

Repository-setting activation is not performed by committing this specification.

Declared change class: GOVERNANCE_AMENDMENT

Classification authority at this stage: E/P only.
The machine classifier does not yet exist.

## 1. Purpose

This candidate defines the first repository-protection baseline after
the T1 Integration Governance Genesis.

It grants no Quant or research authority.

## 2. Observation V2

The new time-bound repository observation is:

`artifacts/governance/repository_protection_observation_v2.json`

Observation V2 is a new post-T1 observation.

It does not rewrite, backfill, or promote the historical T1 observation.

## 3. Single control plane

Repository Protection V1 uses:

`GITHUB_REPOSITORY_RULESETS_ONLY`

Classic branch protection must remain unconfigured in V1.

The project must not operate overlapping Classic Branch Protection and
Repository Rulesets as parallel protection control planes in this phase.

## 4. Exact reviewed identity

During bootstrap, the governed review identity remains the exact Git
commit SHA.

The authorized integration method is:

`EXACT_FAST_FORWARD_TO_REVIEWED_COMMIT`

GitHub-generated merge, squash, and rebase commit identities do not
inherit approval merely because they contain equivalent-looking changes.

Any reviewed identity change makes the prior approval stale.

## 5. Two-layer Ruleset architecture

### 5.1 MES Main Integrity V1

Bypass actors:

`NONE`

Rules:

- deletion protection;
- non-fast-forward protection;
- required linear history.

Target refs:

- the default branch;
- `refs/heads/governance/tree001-execution-authorization`;
- `refs/heads/governance/protection-canary-*`.

The historical TREE001 branch is included to mechanically preserve
reachability of the committed authorization evidence against deletion or
non-fast-forward replacement.

Fast-forward extension of that historical branch remains technically
possible; V1 protects evidence reachability, not absolute ref immutability.

The canary pattern provides dedicated refs for negative functional tests.

Canary refs are not treated as disposable after activation because the
same Integrity ruleset intentionally applies deletion protection to them.

Canonical naming convention:

`governance/protection-canary-YYYYMMDD-NN`

A canary that successfully demonstrates deletion rejection is retained as
functional protection evidence by default.

Its later retirement or ruleset exclusion requires a separately governed
action.

Destructive negative probes must not be aimed directly at `main` when a
misconfiguration could mutate or delete the canonical branch.

This Integrity layer has no configured bypass actor.

### 5.2 MES Main Integration Authority V1

Rule:

- restrict updates to the default branch.

Temporary bypass actor:

- Owner user identity;
- bypass mode: always.

This bypass exists only on the Update Authority ruleset.

It does not bypass MES Main Integrity V1.

## 6. Why the temporary Owner bypass exists

Bootstrap still requires exact reviewed-SHA fast-forward integration.

GitHub's normal merge, squash, and rebase paths do not preserve the
reviewed commit identity as the new main head in the required way.

Until an authenticated integration actor and machine gate exist, the
Owner remains the temporary integration actor.

This is a known bootstrap limitation, not T2 enforcement.

The Update Authority rule sets:

`update_allows_fetch_and_merge = false`

V1 does not rely on any fetch-and-merge update path for exact integration.
This parameter does not itself establish review or exact-SHA enforcement.

The authenticated GitHub push actor is the Owner account. Git commit
author metadata, including historical `codex@local.invalid` author fields,
is not treated as repository push authority.

The temporary bypass does not establish authenticated independent review.

## 7. Residual bootstrap risk

Repository Protection V1 deliberately does not claim more enforcement
than the remote rules can provide.

The temporary Owner integration actor remains technically capable of
pushing a linear fast-forward commit that has not passed the procedural
review process.

Therefore:

`EXACT_REVIEWED_SHA_NOT_REPOSITORY_ENFORCED`

The exact-reviewed-SHA requirement remains a bootstrap governance
procedure until later machine gates exist.

Required linear history blocks merge commits. It does not by itself block
squash-merge or rebase-merge paths, both of which can produce linear
history while changing the reviewed commit identity.

Therefore:

`SQUASH_OR_REBASE_MERGE_MAY_REMAIN_TECHNICALLY_POSSIBLE`

Those identity-substitution paths remain procedurally prohibited during
bootstrap.

The repository Owner is also a repository administrator and can
technically edit or delete repository-level rulesets.

Therefore:

`RULESET_CONFIGURATION_MUTABLE_BY_REPOSITORY_ADMIN`

Repository Protection V1 is designed to prevent accidental or ordinary
integration failures. It does not claim protection against a malicious
repository administrator with authority to rewrite the control plane.

Independent review also remains:

`INDEPENDENT_REVIEW_NOT_REPOSITORY_ENFORCED`

These limitations are reasons that Repository Protection V1 alone does
not establish:

`T2_MACHINE_INTEGRATION_GATES_ACTIVE`

## 8. TREE001 historical authorization evidence hold

The branch:

`governance/tree001-execution-authorization`

must remain a reachable repository ref carrying historical TREE001
authorization evidence, including commit:

`309bb1af5e6c4cc7098cefc2ae6ea7b8d239fd3e`

Repository Protection V1 therefore includes the exact branch ref in
MES Main Integrity V1.

The Integrity ruleset must mechanically reject deletion and
non-fast-forward replacement of that branch.

This protects reachability of the authorization commit.

The required historical condition is that:

`309bb1af5e6c4cc7098cefc2ae6ea7b8d239fd3e`

remains an ancestor of the protected evidence branch.

The historical branch head is not required to remain permanently equal to
its current head if a separately governed fast-forward extension occurs.

It does not make the branch absolutely immutable because future
fast-forward extension may remain technically possible.

Creation of a durable annotated evidence tag remains an optional separate
governed provenance improvement and is not required to activate this V1
baseline once the branch protection is machine verified.

## 9. Deferred controls

The following remain deferred to their ordered bootstrap phases:

- required status checks;
- authenticated independent-review enforcement;
- change classifier;
- governance sentinel;
- CODEOWNERS enforcement;
- required commit signatures.

No classifier implementation may precede its frozen specification.

## 10. Candidate review gate

Before this candidate may be committed:

1. exact candidate bytes must be staged and machine-bound;
2. machine/static checks must pass;
3. ChatGPT architecture/governance review must pass;
4. Independent Auditor review must return GO;
5. Owner must authorize the exact reviewed candidate.

Changed identity after review makes approval stale.

## 11. Integration gate

After a reviewed candidate is committed, integration must separately
bind:

- exact commit identity;
- exact parent;
- exact changed-path scope;
- exact reviewed content identity;
- remote branch identity;
- main identity.

No squash, rebase, merge-commit substitution, or unrelated commit may
inherit the prior approval.

## 12. Activation gate

Committing this architecture does not activate GitHub Rulesets.

Ruleset activation is a separate repository mutation.

Activation may occur only after the frozen architecture and ruleset spec
are integrated into main and the required bootstrap activation review
and Owner authorization are satisfied.

## 13. Post-activation verification

An API success response alone does not establish protection.

Machine verification must re-observe:

- main identity;
- repository ruleset inventory;
- each expected ruleset;
- enforcement = active;
- exact target conditions;
- bypass actor configuration;
- expected rule types and parameters;
- active rules applying to main;
- mechanical protection of the TREE001 evidence ref;
- classic branch protection still unconfigured.

### Safe negative functional verification

Direct destructive negative probes against `main` are prohibited when a
failed protection configuration could mutate or delete the canonical
default branch.

MES Main Integrity V1 therefore also targets:

`refs/heads/governance/protection-canary-*`

A dedicated canary ref must be used to functionally test rejection of:

- non-fast-forward / forced replacement;
- a pushed merge commit;
- branch deletion.

Machine evidence must also establish that `main` and the canary are
targeted by the same exact active Integrity ruleset identity.

Rule-type equality alone is insufficient.

The verification procedure must:

1. query the active rules applying to `main`;
2. query the active rules applying to the concrete canary ref;
3. extract the Integrity `ruleset_id` contributing those rules;
4. require the same active Integrity `ruleset_id` for both refs;
5. fetch that exact ruleset by ID;
6. verify `enforcement = active`;
7. verify its bypass actor list is empty; and
8. verify its exact Integrity rule-type set is deletion,
   non-fast-forward, and required linear history.

If these identity checks do not match:

`CANARY_EVIDENCE_NOT_TRANSFERABLE_TO_MAIN`

A same-looking rule set from a different ruleset identity must not pass
this gate.

If a non-bypass repository actor is unavailable in this single-actor
repository, that specific Update Authority negative test must be recorded
as:

`UNTESTABLE_SINGLE_ACTOR_REPOSITORY`

It must not be represented as tested.

### Exact-fast-forward witness without circular verification

The final verification record must not attempt to prove the successful
integration of its own commit.

After ruleset activation and negative canary testing, a dedicated
Section-8-reviewed functional witness commit must be created.

Canonical witness artifact:

`artifacts/governance/repository_protection_functional_witness_v1.json`

The exact reviewed witness commit must then be fast-forwarded to `main`
under the active rulesets.

Only after remote observation confirms that exact witness SHA as the new
main identity may the final post-activation verification record be
created.

Canonical final verification artifact:

`artifacts/governance/repository_protection_post_activation_verification_v1.json`

The final record may derive:

`BRANCH_PROTECTION_VERIFIED = TRUE`

only from events and machine evidence that already exist before that
final record is created.

The `main` identity recorded for the functional witness is therefore a
time-bound pre-final-record observation.

When the exact final verification-record commit is later fast-forwarded
to `main`, the branch head is expected to advance from the witness SHA to
the final verification-record commit SHA.

That later head movement is not a mismatch in the historical witness
observation.

The final verification-record commit must itself receive separate exact
integration verification.

Its own later integration is not the functional witness used to derive
the marker.

### Step-2 required protection checks

Repository Protection Step 2 is not complete until machine evidence
establishes all of the following:

1. the frozen protection architecture and ruleset specification are
   present on the default branch;
2. GitHub Repository Rulesets are the single protection control plane
   for this phase;
3. both reviewed rulesets exist remotely with exact expected
   configuration and `enforcement = active`;
4. the Integrity ruleset has no bypass actor;
5. the Update Authority ruleset has only the reviewed temporary Owner
   bypass;
6. the Integrity ruleset targets main, the historical TREE001 evidence
   branch, and the functional canary pattern;
7. deletion and non-fast-forward protection of the TREE001 evidence ref
   are remotely established;
8. the expected rules are active on `main`;
9. classic branch protection remains unconfigured;
10. main and the canary are machine-established as receiving their
    Integrity controls from the same active Integrity ruleset ID, whose
    bypass list is empty and whose exact rule set is verified;
11. canary non-fast-forward rejection is functionally verified;
12. canary merge-commit rejection is functionally verified;
13. canary deletion rejection is functionally verified;
14. non-bypass update rejection is either functionally verified or
    explicitly recorded as untestable because no independent repository
    actor exists;
15. an exact reviewed functional witness commit is successfully
    fast-forwarded to main under the active rulesets;
16. remote main is re-observed at that exact witness identity;
17. main history remains fast-forward and linear;
18. all Repository Protection Auditor findings are dispositioned and
    recorded;
19. the final verification-record commit is separately exact-integrated
    and machine-verified on the default branch.

Only the final committed post-activation verification record, based on
those prior machine observations, may establish:

`BRANCH_PROTECTION_VERIFIED = TRUE`

### Distinction from Step-3 CI status checks

The Step-2 protection checks above are not GitHub CI required status
checks.

Required CI/status-check enforcement depends on the later frozen
machine-classification and merge-gate design and therefore remains a
later T1 Section 31 control.

Repository Protection Step 2 must not implement Machine Classification,
LangGraph, or Multi-Agent Constitution Section 3.

## 14. Research authority

This architecture does not authorize:

- Sprint 2;
- new target-aware candidates;
- new realized-label research;
- Validation access;
- Final Test access.

Validation remains unopened.

Final Test remains sealed.

## 15. Specification disposition

Protection baseline specification:

`RULESET_BASELINE_V1`

Committing or integrating this specification:

`DOES_NOT_ACTIVATE_REPOSITORY_SETTINGS`

Protection activation authority:

`SEPARATE_GOVERNED_ACTION_REQUIRED`

Repository Protection verification:

`REQUIRES_POST_ACTIVATION_MACHINE_RECORD`

T2 activation:

`NOT_ESTABLISHED_BY_THIS_SPECIFICATION`

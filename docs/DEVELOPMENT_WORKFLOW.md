# MES Quant Engine V1 Development Workflow

## Purpose and non-negotiable merge path

This is the canonical engineering workflow guide for OpenAI Codex / Code X,
Claude Code, human developers, and future AI development agents. Read it before
making any code change.

Every change follows this path:

```text
APPROVED QUANT SPEC
        -> FEATURE BRANCH FROM THE EXACT AUTHORIZED SHA
        -> LOCAL VALIDATION
        -> PUSH ASSIGNED BRANCH
        -> PULL REQUEST
        -> GITHUB ACTIONS CI
        -> CI GREEN
        -> QUANT UAT / INDEPENDENT REVIEW
        -> EXPLICIT APPROVAL
        -> MERGE MAIN
```

CI GREEN alone never authorizes a merge. Jenkins is not part of this V1
workflow.

## Authority and roles

### User + ChatGPT Quant/CIO layer

The user and the ChatGPT Quant/CIO layer own Quant Logic, constitutional and
methodology decisions, acceptance criteria, and Quant UAT. They approve any
change to feature definitions, information boundaries, thresholds, numerical
methods, feature decisions, labels, calibration, risk, sizing, costs, or
execution policy.

An approved issue or specification defines the implementation scope. Locked
constitutional controls and approved Quant specifications remain authoritative
over implementation convenience.

### Developers and coding agents

Codex / Code X, Claude Code, human developers, and future coding agents
implement the approved specification. They must not invent Quant policy,
reinterpret an ambiguous policy in production code, or independently change
methodology or thresholds. If a required choice is absent or inconsistent, stop
and return it to the Quant/CIO layer for review.

### Tests and CI

Tests verify invariants and approved behavior. Tests are not policy authority.
Changing a test to accept an unapproved behavior does not make that behavior
valid. CI provides reproducible engineering evidence; it does not approve Quant
methodology.

### Claude Code and UX/UI work

Claude Code is expected to handle UX/UI when assigned. A UI normally remains
read-only and observational: it consumes approved artifacts and schemas and
does not become a policy authority, an artifact writer, or a safeguard bypass.
The same rules apply to any developer implementing UI.

## Before editing: fail-closed checkpoint

Never start from an assumed branch and never rebuild active work from stale
`main`. Before writing, record and compare all of the following with the task:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

Verify that:

- the working tree state is exactly what the task permits;
- the current branch is the authorized source branch;
- `HEAD` equals the exact authorized base SHA;
- the recorded `origin/main` SHA is the expected one; and
- the proposed task branch does not already contain unrelated work.

If any required value differs, stop and report the evidence. Do not reset,
rebase, delete, overwrite, or discard another developer's work without explicit
authorization. Do not "repair" a mismatch by silently moving to another commit.

## Branch rules

- Never develop directly on `main`.
- Create one scoped branch per approved task.
- Create it from the exact branch and commit SHA named in the task, not from the
  most convenient or newest-looking branch.
- Keep one logical task per branch. A follow-up finding receives a separately
  authorized branch unless the current task explicitly includes it.
- Do not merge, rebase, or cherry-pick other work unless the task explicitly
  authorizes that action.

## Editing, commit, and push rules

- Make the minimum changes required by the approved specification.
- Use scoped commits and do not bundle unrelated cleanup or refactors.
- Do not modify locked controls, frozen references, methodology documents, or
  semantic registries unless their change is explicitly authorized.
- Do not change thresholds, numerical tolerances, feature decisions, labels,
  risk rules, or execution policy on a developer's own authority.
- Never open Final Test data or provenance-only Cell8 full assignments to make
  a test pass.
- Never copy raw MES data, credentials, generated production runs, or large
  local artifacts into Git or CI.
- Push only the assigned branch. Never push directly to `main`.
- Do not merge to `main` without explicit acceptance after CI and Quant UAT.

Before committing, review `git diff`, run the relevant validation, check locked
file hashes when applicable, and confirm that the diff contains no unrelated or
generated files.

## Pull Request flow

The required sequence is exact:

1. Receive an approved Issue/specification and exact authorized base SHA.
2. Verify the prewrite checkpoint and create the assigned branch.
3. Implement only the approved scope.
4. Run and record local tests and safety counters.
5. Commit intentionally and push only the assigned branch.
6. Open a Pull Request using `.github/pull_request_template.md`.
7. Obtain a GREEN `Quant CI V1` check.
8. Complete independent Quant UAT against the approved specification.
9. Obtain explicit acceptance and merge authorization.
10. Merge to `main` only through the authorized PR process.

A PR is not merge-ready merely because automated tests pass. The PR author must
record missing environmental fixtures and skipped tests rather than hiding them
or substituting data.

## CI and checkout-only test scope

The GitHub Actions workflow is `.github/workflows/quant-ci-v1.yml`.

- Workflow name: `MES Quant CI V1`
- Stable job/check name: `Quant CI V1`

The check compiles and imports active Python code, runs critical Ruff checks,
runs direct constitutional and project-root gates, runs focused Phase 0 and
Phase A tests, runs the checkout-safe Stage B redundancy suite, and runs other
safe repository tests.

Generated and large artifacts under `artifacts/cache/` and `artifacts/runs/`
are intentionally absent from a clean GitHub checkout. CI therefore follows
these explicit environmental rules:

- It never fetches or copies raw MES data, Final Test data, or provenance-only
  Cell8 full assignment data.
- It runs all of `tests/test_redundancy.py` when the frozen Cell14 feature
  registry is present. That external fixture supports both the frozen canonical
  registry compatibility boundary and the Phase-A Decision Bridge specification
  boundary.
- In a clean checkout where that ignored feature-registry artifact is absent,
  it emits visible environmental-exclusion notices and does not execute either
  `StageBCanonicalRegistryCompatibilitySpecificationTests::test_frozen_canonical_cell14_registry_is_accepted_without_metadata_rewrite`
  or the external-fixture-dependent
  `StageBPhaseADecisionBridgeRedSpecificationTests` class. These exclusions are
  environmental absences, not test passes. All other checkout-safe redundancy
  tests continue to execute.
- It does not run `tests/test_cell14_release.py` because that module's shared
  setup requires the complete ignored Cell14 release outputs, including the
  development feature parquet. This is an environmental limitation, not a
  test pass or a methodology waiver.
- `tests/test_reference_freeze.py` transparently skips its optional local
  large-artifact verification when `artifacts/cache/source_v1` is absent; its
  checkout-safe reference and missing-artifact gate tests still run.

Do not make unavailable-data tests green by weakening them. An approved
artifact-enabled environment may run those tests separately and report the
results for both external-fixture boundaries as additional evidence.

## CI versus Quant UAT

CI verifies engineering and test invariants: syntax/import viability, selected
static checks, deterministic test behavior, constitutional gate behavior, and
known checkout-safe regression coverage.

Quant UAT verifies fidelity to the approved methodology and specification. It
asks questions that automated CI cannot authorize, including:

- Did the implementation use only information explicitly authorized by the
  approved phase/specification?
- Were TRAIN-only rules obeyed wherever the approved phase requires TRAIN-only?
- Was Validation excluded wherever the approved phase/specification prohibits
  its use?
- Did future information, labels, targets, or P&L leak into any decision?
- Were locked SVD construction, rank tolerance, thresholds, and retention
  priority followed exactly?
- Were protected features preserved?
- Does every feature DROP have the correct constitutional or registry authority?
- Were artifact schemas and provenance bindings preserved where required?
- Are Final Test rows opened still exactly `0`?
- Are Cell8 full assignment rows opened still exactly `0`?
- Did production remain fail-closed at every boundary required by the approved
  phase?

Every implementation may use only information explicitly authorized by the
approved phase/specification. For current Stage B, Validation must not influence
Phase A, B, C, or D feature-reduction decisions. A later, separately approved
methodology/specification may permit Validation for a defined purpose such as
model selection or calibration; this guide does not define or authorize that
future methodology.

Final Test is different: it remains sealed unless a separately approved stage
explicitly authorizes opening it. After evaluation, Final Test must never be
used to tune, reselect, or redesign the system.

`CI GREEN != Quant approval`. Both CI GREEN and explicit Quant UAT acceptance
are required before merge.

## Claude Code UX/UI rules

Claude Code, when assigned UX/UI work, must:

- use its own task branch from the exact authorized base;
- follow the same local validation, PR, CI, Quant UAT, and approval process;
- consume approved artifacts and schemas;
- keep dashboards and readers read-only unless a separate approved
  specification explicitly authorizes writes;
- never change thresholds, feature decisions, labels, Final Test boundaries,
  risk/execution policy, or Quant methodology because a UI implementation is
  inconvenient; and
- never hide a schema or logic mismatch with a silent UI adaptation.

If UI work discovers a schema/logic mismatch, stop and surface the exact
mismatch to the Quant/CIO layer. Do not adapt Quant policy silently.

## Required completion report

Every developer or agent must return all of the following:

- branch name;
- authorized base SHA;
- resulting commit SHA and remote branch tip;
- files changed and their purpose;
- exact test commands/selections and exact results;
- known environmental limitations and tests not run;
- locked-control status and hashes when required;
- Final Test rows opened;
- Cell8 full assignment rows opened;
- real production run count;
- `origin/main` SHA and whether `main` changed; and
- `git status --short` after push.

Report a failure separately from environmental data that is not present. Never
label a skipped, unavailable-data test as passing.

## CODEOWNERS decision

`CODEOWNERS = DEFERRED`.

The repository currently has a single practical owner/reviewer and branch
protection is not being changed in this task. A CODEOWNERS file would not add a
distinct, enforceable review boundary today and could imply protection that is
not actually configured. Reassess when a separate Quant reviewer account or
GitHub team exists; then map locked controls and Quant production paths to that
review authority and enable required code-owner review deliberately.

## Recommended current branch protection

Branch protection is not enabled or changed by this workflow task. After
independent review, configure `main` with:

- require a Pull Request before merge;
- require the stable status check `Quant CI V1` to pass;
- block force pushes to `main`;
- block deletion of `main`;
- require conversation resolution when review comments are used;
- require Quant UAT evidence to be recorded before merge;
- allow no merge without explicit User + ChatGPT Quant/CIO acceptance; and
- do not permit CI GREEN to substitute for explicit Quant UAT approval.

The current single-account workflow has no genuinely independent GitHub
reviewer identity. Do not currently require a GitHub approving-review count;
that setting could deadlock the workflow or falsely imply independent review.
When a distinct Quant reviewer GitHub account/team exists, enable at least one
required approving review and reassess CODEOWNERS.

Keep administrator bypass and dismissal permissions narrow. These settings are
recommendations; enabling them requires separate explicit authorization.

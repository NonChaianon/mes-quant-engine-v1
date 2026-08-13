# Pull Request — Engineering CI + Quant UAT

## Approved issue / specification

- Issue or approved specification:
- Authorized source branch:
- Authorized base SHA:
- Quant/CIO owner or approver:

## Scope

- What this PR implements:
- Why the change is required:

## Explicit non-goals

- [ ] No work outside the approved issue/specification is included.
- Non-goals for this PR:

## Changed files

List every changed file and its purpose:

-

## Local validation evidence

List the exact commands and exact results. Do not write only "tests pass."

| Command / test selection | Result |
| --- | --- |
|  |  |

## CI status

- Stable required-check-ready check: `Quant CI V1`
- CI result:
- Any skipped check and the exact environmental reason:

CI GREEN verifies engineering/test invariants. It does **not** authorize merge.

## Quant UAT / independent review

To be completed by the authorized Quant/CIO reviewer, not assumed by the PR author:

- [ ] Implementation matches the approved Quant specification.
- [ ] Information usage matches the approved phase/specification.
- [ ] TRAIN-only rules were obeyed wherever the approved phase requires TRAIN-only.
- [ ] Validation was not used where prohibited by the approved phase/specification.
- [ ] Final Test remained sealed unless its opening was separately authorized.
- [ ] Final Test was not used for tuning/reselection.
- [ ] Locked methods, tolerances, thresholds, and retention priorities are unchanged or explicitly authorized.
- [ ] Protected features and DROP authority are correct.
- [ ] Artifact schemas and provenance boundaries are preserved where required.
- [ ] Production remains fail-closed at every boundary required by the specification.
- [ ] Independent Quant UAT approval is recorded before merge.

Quant UAT result / reviewer evidence:

## Safety counters

- Final Test rows opened: `0` / other (explain):
- Cell8 full assignment rows opened: `0` / other (explain):
- Real production runs: `0` / other (explain):

## Locked controls and Quant Logic

- Locked-control files changed: `NONE` / list explicit authorization:
- [ ] No unauthorized Quant Logic, methodology, threshold, label, risk, or execution-policy change.
- [ ] No raw MES, Final Test, credentials, provenance-only Cell8 assignments, or generated production artifacts were added.

## Known limitations

Record missing environmental data, tests not run, and follow-up items. Use `NONE` only after checking:

-

## Merge authorization

- [ ] `Quant CI V1` is GREEN.
- [ ] Review conversations are resolved where required.
- [ ] Explicit Quant UAT approval has been given.
- [ ] Merge to `main` is separately authorized.

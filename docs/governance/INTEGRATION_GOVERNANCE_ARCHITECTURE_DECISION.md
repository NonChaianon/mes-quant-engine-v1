# Integration Governance Architecture Decision

## Lifecycle

Effective condition:

`EFFECTIVE_AT_T1_GENESIS_COMMIT`

This document is not an implemented machine control merely because the text exists.

It becomes the governing Integration Governance Architecture Decision when it is committed together with the canonical pre-genesis repository snapshot under the T1 genesis rule defined below.

Marker:

`INTEGRATION_GOVERNANCE_GENESIS`

---

## 1. Purpose

This Architecture Decision establishes the integration-governance architecture for the MES Quant Engine.

It separates:

- machine-observed facts;
- human/model evaluation;
- change classification;
- independent review;
- repository enforcement;
- governance amendments;
- owner exceptions;
- transition/bootstrap semantics.

It does not authorize new target-aware research.

It does not reopen Sprint 1.

It does not authorize Validation access.

It does not authorize Final Test access.

---

## 2. Research-state evidence boundary

This section deliberately distinguishes operational research-state
judgments from machine-observed repository facts.

Section evidence class for the overall research-state interpretation:

`OWNER_DECLARED_RESEARCH_STATE (E/P)`

No statement in this section becomes a default-branch machine fact merely
because it appears in this Architecture Decision.

### Machine-observed Search Budget evidence

The Sprint-1 Search Budget Addendum is present at the default-branch head
recorded in the canonical T1 snapshot.

Path:

`docs/research/EDGE_DISCOVERY_SPRINT_1_SEARCH_BUDGET_ADDENDUM.md`

Recorded add/last-touch commit:

`c1c7cbbf87652df62191e61740a9b52de49aa39a`

Content SHA-256:

`6436F9EA66DDC9D6702C814788A70A77370F7E5F53A09475BAACE10A6E9F2535`

Evidence classification:

`MACHINE_ESTABLISHED_ON_SNAPSHOT_DEFAULT_BRANCH`

### Sprint-1 closure record

Path:

`docs/research/EDGE_DISCOVERY_SPRINT_1_CLOSURE.md`

The closure record is:

`NOT_PRESENT_ON_SNAPSHOT_DEFAULT_BRANCH`

It is machine-observed in the pre-genesis local history at:

`c5757d0a682dd46e8ad4b923d8867df9a80ebfaa`

Content SHA-256:

`1A90E8F0176D0F55B1C4CA8E8884E326CC1F7F325901555DE391186F93E3F617`

Therefore the existence of that closure record in local Git history is
machine-observed, but its integration into the snapshot default branch is:

`NOT_MACHINE_ESTABLISHED_AT_T1`

The T1 genesis must not silently import that unmerged history.

### LR001 immutable experiment record

Observed local filesystem path:

`artifacts/exploration/sprint1/MES_S1_LR001_20260815T095100Z/experiment_record.json`

Observed local SHA-256:

`093FF155B2AC77172ACDD99C0F5B4FFD713C7C4EA9556BCB18170480D68E58B9`

The record is not present in the examined Git revisions at:

- snapshot default-branch head;
- PR #34 head;
- old pre-genesis local HEAD.

Repository integration state:

`NOT_MACHINE_ESTABLISHED_AT_T1`

### TREE001 immutable experiment record

Observed local filesystem path:

`artifacts/exploration/sprint1/MES_S1_TREE001_20260815T192900Z/experiment_record.json`

Observed local SHA-256:

`FAD9367FF353671CCF42739A02ECE5178DDD60CE973917BC118BA8E54E77F7A6`

Observed experiment ID:

`MES_S1_TREE001_20260815T192900Z`

Observed disposition:

`NO_USABLE_EDGE_IDENTIFIED_IN_TESTED_SPRINT_1_SCOPE`

The record is not present in the examined Git revisions at:

- snapshot default-branch head;
- PR #34 head;
- old pre-genesis local HEAD.

Repository integration state:

`NOT_MACHINE_ESTABLISHED_AT_T1`

### Operational research state

The Owner's current operational research state is:

- Edge Discovery Sprint 1: `CLOSED`;
- Search budget: `2/2 EXHAUSTED`;
- LR001: completed;
- TREE001: completed;
- TREE001 did not satisfy Sprint-1 acceptance;
- no TREE002 is authorized;
- no third Sprint-1 candidate is authorized;
- Validation: `UNOPENED`;
- Final Test: `SEALED`.

These operational statements remain `E/P` except where a more specific
machine observation above establishes a narrower fact.

TREE001 created no confirmatory-hypothesis obligation associated with a
Sprint-1 PASS.

TREE001 created no Validation-protocol obligation associated with a
Sprint-1 PASS.

None of these statements authorizes Validation access or Final Test access.

The unmerged historical research records must not be smuggled into the T1
genesis commit. Any later integration or reconciliation of those records
requires its own governed change after T1.

---

## 3. Canonical pre-genesis repository snapshot

Canonical snapshot:

`artifacts/governance/integration_governance_t1_repository_snapshot_v1.json`

Snapshot schema:

`INTEGRATION_GOVERNANCE_T1_REPOSITORY_SNAPSHOT_V1`

SHA-256:

`8A6B6E9125AAB9F329115BC45016AB12A4AA2F4BC229E6FF6888350639F78846`

The snapshot is the machine-derived repository-state input for this Architecture Decision.

Human memory must not add machine-fact claims that are absent from the snapshot.

Unknown state must remain explicitly unknown.

---

## 4. Machine-observed pre-genesis repository state

The canonical snapshot establishes the following repository observations.

Repository:

`NonChaianon/mes-quant-engine-v1`

Default branch:

`main`

Snapshot-time local branch:

`governance/tree001-execution-authorization`

Snapshot-time local HEAD:

`dc782d18f9dfe6c9388eafc6329b538a4aead509`

Snapshot-time remote head of that branch:

`f211e5458739af9033cad03c2e6026f6c3e657a9`

Observed relationship:

`LOCAL_AHEAD_OF_REMOTE`

Open pull-request count:

`1`

Open PR:

`#34`

PR #34 state:

`OPEN / DRAFT`

PR #34 base:

`main`

PR #34 GitHub head OID:

`f211e5458739af9033cad03c2e6026f6c3e657a9`

The PR #34 head and the snapshot-time local branch head were not identical.

No review of PR #34 at the recorded remote identity may be represented as
review of the later local HEAD.

Snapshot default-branch head:

`ec6633de4f4b7b1a0f246c8ccabebb859bfe01c7`

### Repository-protection observation

The classic GitHub branch-protection endpoint for `main` returned:

`HTTP_404_BRANCH_NOT_PROTECTED`

The precise machine fact established by that observation is:

`NO_CLASSIC_BRANCH_PROTECTION_OBSERVED`

GitHub repository rulesets are a separate control plane and were not
observed by the canonical T1 snapshot.

Ruleset state:

`RULESET_STATE_NOT_OBSERVED_AT_T1`

Therefore the broader claim that repository protection sufficient for
canonical Stage B is active is:

`NOT_MACHINE_ESTABLISHED_AT_T1`

The Architecture Decision must not collapse the classic-protection
observation and unobserved ruleset state into a stronger historical claim.

---

## 5. In-flight transition enumeration

The transition inventory is derived from machine-observed repository state,
not from human memory.

### IF-LOCAL-001 — snapshot-time local history

Snapshot-time branch:

`governance/tree001-execution-authorization`

Snapshot-time local identity:

`dc782d18f9dfe6c9388eafc6329b538a4aead509`

Snapshot-time remote identity:

`f211e5458739af9033cad03c2e6026f6c3e657a9`

Relation:

`LOCAL_AHEAD_OF_REMOTE`

Legacy grandfather merge authority:

`NOT_GRANTED`

This history contains multiple post-PR-34 local commits that are not part
of the snapshot default branch.

Their existence does not authorize them to enter T1 by ancestry.

### IF-PR-034 — open Draft TREE001 authorization PR

PR:

`#34`

State:

`OPEN / DRAFT`

Base:

`main`

Recorded PR head:

`f211e5458739af9033cad03c2e6026f6c3e657a9`

Legacy grandfather merge authority:

`NOT_GRANTED`

PR #34 contains the following machine-observed authorization chain,
including:

`daa4b7075d8ee8954c629257030bcb9d95af83db`

`Add explicit TREE001 execution authorization gate`

and:

`309bb1af5e6c4cc7098cefc2ae6ea7b8d239fd3e`

`Record TREE001 one-shot execution authorization`

The authorization document at commit `309bb1af...` has SHA-256:

`5897F6A612B0ED2FFC4674E45B94712CAE79D096B7B38E055D64DFB461B9F0A6`

The document records:

`Status: AUTHORIZED_PENDING_MERGE`

and an Owner authorization for exactly one real TRAIN-only TREE001
execution.

### Recorded authorization chronology

Machine-observed Git history records authorization commit
`309bb1af...` at:

`2026-08-16T03:37:38+07:00`

The later execution-code identity recorded by the TREE001 local immutable
artifact is:

`202cda22d5316d690b30d016e6bb60371b4b237d`

That commit is observed in the descendant local history after PR #34 and
has recorded commit time:

`2026-08-16T04:22:08+07:00`

The TREE001 immutable experiment record has recorded timestamp:

`2026-08-15T21:28:18.047027Z`

which corresponds to approximately:

`2026-08-16T04:28:18+07:00`

The TREE001 pre-access manifest has SHA-256:

`858DD435DC01B56C06B6395864D990B2CF450A5E2D369181B6187C8F7F7D47F0`

and records:

`authorization_status = ENABLED`

Therefore the repository/artifact chronology supports the narrower finding:

`RECORDED_AUTHORIZATION_COMMIT_PRECEDES_RECORDED_TREE001_ARTIFACT_TIMESTAMP`

A committed authorization control input is therefore machine-observed in
the branch history before the recorded TREE001 artifact timestamp.

This finding does **not** establish that the authorization was merged into
the default branch before execution.

Default-branch integration of PR #34 authorization before execution is:

`NOT_ESTABLISHED`

The Architecture Decision does not retroactively change the historical
authorization semantics.

### Historical status-field limitation

The same immutable TREE001 experiment record contains:

`harness_execution_status = DRY_RUN_ONLY_L0`

T1 does not rewrite, reinterpret, or backfill that historical field.

Any future determination about inconsistency between that historical field
and other execution evidence requires a separately authorized audit.

### PR #34 authority after genesis

The fact that PR #34 remains open does not itself confer additional
execution authority.

PR #34 confers:

`NO_NEW_EXECUTION_AUTHORITY`

at or after T1.

It must not be merged later as a fresh authorization for another TREE001
execution.

Required post-T1 bootstrap disposition:

`PR_34_CLOSE_OR_CONVERT_TO_RECORD_ONLY`

PR #34 must be closed or otherwise converted to a clearly record-only
historical artifact before ordinary Quant integration resumes.

Its disposition must not reopen TREE001, Sprint 1, or the exhausted
Sprint-1 search budget.

### Other remote branches

Remote branch presence alone does not establish active in-flight work.

No additional legacy-grandfathered integration authority exists merely
because another remote branch is present.

---

## 6. T0 pre-genesis freeze

The repository is currently in:

`T0_PRE_GENESIS`

Until T1 genesis:

- no new Quant/Engine merge is authorized;
- no ordinary governance/control-plane merge is authorized;
- no merge may be accelerated merely to gain legacy grandfather status.

Development may remain on branches.

The only authorized control-plane work during T0 is work necessary to construct and review the T1 integration-governance genesis.

This prevents:

`GRANDFATHER_BY_SPEED`

---

## 7. T1 genesis

The T1 genesis is explicitly authorized by the Owner under pre-T1
governance authority.

This authorization covers only:

1. creation of the exact T1 genesis commit; and
2. integration of that exact genesis commit into the recorded default
   branch state under the constraints below.

The T1 commit is the genesis of the new integration-governance control
chain.

The amendment procedure established by T1 applies after T1 and does not
recursively require T1 itself to have passed a procedure that did not yet
exist.

Canonical marker:

`INTEGRATION_GOVERNANCE_GENESIS`

### Dedicated genesis parent

The T1 genesis commit must be created on a dedicated branch whose single
parent is the default-branch head recorded in the canonical snapshot:

`ec6633de4f4b7b1a0f246c8ccabebb859bfe01c7`

Dedicated branch:

`governance/integration-governance-genesis`

T1 must not be committed onto:

`governance/tree001-execution-authorization`

or any branch carrying unmerged non-genesis history.

Immediately before the T1 commit and immediately before its integration,
the remote `main` head must still equal:

`ec6633de4f4b7b1a0f246c8ccabebb859bfe01c7`

If the observed default-branch identity changes:

`T1_CANDIDATE_STALE → STOP`

A moved default branch requires a newly governed T1 candidate decision.

### Exact integration scope

The T1 genesis commit must change exactly these two canonical paths:

`artifacts/governance/integration_governance_t1_repository_snapshot_v1.json`

`docs/governance/INTEGRATION_GOVERNANCE_ARCHITECTURE_DECISION.md`

No Quant implementation, experiment result, research artifact, model code,
feature code, target code, historical local research record, or unrelated
documentation may be included.

Integration scope authority is the diff between the T1 genesis commit tree
and the recorded default-branch head, not merely the number of files
reported for the final commit.

Required condition:

`REQUIRED_T1_INTEGRATION_DIFF_SCOPE = EXACTLY_TWO_CANONICAL_PATHS`

The T1 candidate must be a single-parent commit whose parent is the
recorded default-branch head.

A merge/rebase/squash/conflict-resolution operation that changes this
identity makes the reviewed T1 candidate stale.

The T1 commit SHA is intentionally not embedded in this document because
that would create circular identity.

Its observed commit and tree identities must be recorded immediately after
the genesis is integrated, using the mandatory post-T1 root-identity record
defined below.

---

## 8. Post-T1 bootstrap control plane

After the exact T1 genesis is integrated, the project enters:

`GENESIS_BOOTSTRAP_CONTROL_PLANE`

T1 establishes the architecture but does not falsely claim that the new
machine controls are already active.

### Mandatory first post-T1 committed item

The first committed bootstrap control input after T1 must be:

`artifacts/governance/integration_governance_t1_genesis_commit_record_v1.json`

That record must machine-observe and persist at least:

- T1 genesis commit SHA;
- T1 genesis tree SHA;
- parent commit SHA;
- observed default-branch identity containing T1;
- exact changed-path set;
- observation method;
- observation timestamp;
- verification that the integration diff against the frozen T1 parent is
  exactly the two canonical genesis paths.

The record must not be generated before T1 because the T1 commit identity
does not yet exist.

It must be committed as the first post-T1 bootstrap item.

### Temporary bootstrap review procedure

Until `T2_MACHINE_INTEGRATION_GATES_ACTIVE`, every bootstrap control-plane
change requires all of the following procedural inputs:

1. explicit Owner authorization (`E/P`);
2. exact machine-observed change scope (`F`);
3. ChatGPT architecture/governance review (`E/P`);
4. Independent Auditor advisory review (`E/P`);
5. machine-derived tests/static checks appropriate to the change (`F`);
6. an exact-scope branch or PR whose identity is bound before integration;
7. stale-review invalidation after any governed identity change.

Neither ChatGPT nor the Independent Auditor may represent its judgment as
authenticated machine fact.

An Auditor `RETURN` or unresolved required review disagreement blocks the
bootstrap change unless a pre-existing committed governance exception
validly applies.

### Permitted bootstrap subjects

Only control-plane work required to establish this Architecture Decision is
permitted through the bootstrap lane, including:

- T1 genesis root-identity recording;
- repository branch/ruleset protection;
- governance-amendment sentinel specification and implementation;
- change-classification specification;
- change-classifier implementation;
- CI merge-gate implementation;
- CODEOWNERS or authenticated reviewer controls;
- review-identity binding controls;
- stale-approval controls;
- governance-exception schema, ledger, and enforcement;
- machine evidence capture;
- repository-enforcement verification;
- PR #34 close-or-record-only disposition.

Bootstrap authority does **not** authorize ordinary Quant research
integration.

It does not authorize:

- Sprint 2;
- new target-aware experiments;
- new realized-label research;
- Validation access;
- Final Test access.

Unmerged historical Quant/research records are not automatically
grandfathered into this bootstrap lane.

Any such later integration requires its own governed classification and
authorization.

Bootstrap work exists specifically under this T1 genesis and must not be
silently represented as legacy work.

---

## 9. Evidence classes

The existing declared-vs-derived constitution remains authoritative.

### Machine fact

`F`

A fact may be represented as machine-observed only when it is derived by an appropriate machine/repository observation.

Examples include:

- commit identity;
- tree identity;
- diff identity;
- changed-file set;
- GitHub PR state;
- authenticated repository state;
- test execution result;
- lint/static-check result;
- artifact hash;
- repository protection state;
- machine access detector result.

### Evaluation / policy judgment

`E/P`

Human or model judgments remain evaluative or policy evidence.

Examples include:

- architecture suitability;
- methodology judgment;
- code-review judgment;
- Auditor `APPROVE`;
- Auditor `RETURN`;
- ChatGPT review judgment;
- Owner authorization.

An `E/P` statement must not be promoted to `F` merely because it is written into a repository record.

CI may establish as `F` that a review record exists.

That does not establish as `F` that the reviewer inspected the claimed bytes or that the review judgment was correct.

---

## 10. Known review limitations

The architecture explicitly accepts the following current limitations.

### LLM review binding

`LLM_REVIEW_BINDING_NOT_MACHINE_VERIFIABLE`

A chat-based LLM Auditor may state that a particular package, diff, or hash was reviewed.

The current architecture cannot machine-prove that the model actually inspected exactly those bytes.

Deterministic review bundles may reduce risk by containing:

- base identity;
- head identity;
- exact diff;
- manifest;
- file hashes;
- package SHA-256.

Such bundles do not eliminate the limitation.

### Repository enforcement of independent review

`INDEPENDENT_REVIEW_NOT_REPOSITORY_ENFORCED`

At T1, no machine evidence establishes that independent LLM review is an authenticated repository requirement.

Independent review is therefore not represented as repository-enforced fact.

### Auditor self-governance independence

`AUDITOR_SELF_GOVERNANCE_INDEPENDENCE_NOT_ESTABLISHED`

The current Independent Auditor must not be treated as fully independent when reviewing amendments that alter the Auditor's own authority or review semantics.

This limitation must not be hidden by terminology.

---

## 11. Change-routing precedence

Governance/control-plane changes are intercepted before the ordinary classifier.

Precedence:

`GOVERNANCE_AMENDMENT`

before:

`UX_ONLY / QUANT_ENGINE / CROSS_BOUNDARY`

The ordinary classifier must never classify changes to the rules that define or authorize the ordinary classifier itself.

---

## 12. GOVERNANCE_AMENDMENT

The following subjects are governance/control-plane changes by default:

- governance constitutions;
- integration-governance decisions;
- governance-amendment sentinel rules;
- governance-amendment sentinel implementation;
- classifier rules;
- classifier implementation;
- CI gate semantics;
- CODEOWNERS/reviewer controls;
- branch/ruleset protection configuration;
- audit-gate semantics;
- override/exception mechanisms;
- exception ledger/counter semantics;
- protected-access enforcement;
- evidence-classification rules;
- stale-review identity rules.

The governance-amendment sentinel is itself a protected governance subject.

The ordinary classifier must never be allowed to classify a change to the
sentinel that determines whether the ordinary classifier may run.

Governance-change detection therefore has higher precedence than ordinary
classification.

During `GENESIS_BOOTSTRAP_CONTROL_PLANE`, changes in this class use the
temporary bootstrap review procedure defined in Section 8.

After machine-enforceable amendment governance becomes active, the frozen
successor amendment procedure applies.

---

## 13. Ordinary change classes

After the governance-amendment sentinel, ordinary changes may be classified as:

`UX_ONLY`

`QUANT_ENGINE`

or:

`CROSS_BOUNDARY`

Any ambiguity or unresolved classification must fail closed to:

`CROSS_BOUNDARY`

---

## 14. UX_ONLY

`UX_ONLY` is capability-proven, not path-declared.

A path allowlist alone must never establish `UX_ONLY`.

A change may be classified `UX_ONLY` only when machine evidence can conservatively establish that the affected closure remains within the presentation boundary and cannot alter protected Quant/research semantics or state.

The future classifier specification must consider at least:

- dependency/import closure;
- reference closure;
- access to protected Quant packages;
- protected artifact write capability;
- execution/risk/model mutation capability;
- research-contract/schema mutation;
- semantic transformation of protected research values;
- unresolved dynamic behavior.

Failure to establish the required non-interference evidence results in:

`CROSS_BOUNDARY`

---

## 15. Research presentation adapter

Read-only is not equivalent to semantically safe.

A presentation adapter may misrepresent research results without mutating the Quant Engine.

Operations capable of altering research interpretation include:

- unit conversion;
- rounding policy;
- scaling;
- aggregation;
- metric renaming;
- fold/session identity mapping;
- probability transformation;
- loss transformation;
- sign inversion;
- threshold transformation;
- missing-value interpretation;
- label presentation semantics.

A change affecting such behavior defaults to:

`CROSS_BOUNDARY`

unless a future frozen specification establishes a stricter machine-verifiable semantic contract.

Pure visual presentation performed after semantic values are already frozen may remain eligible for `UX_ONLY`.

Examples include layout, typography, spacing, and styling that do not alter the data or its meaning.

---

## 16. Static closure and dynamic behavior

Static dependency/reference closure is a risk-control mechanism.

It is not treated as mathematical proof of non-interference in a dynamic language.

If the relevant closure contains unresolved:

- dynamic import;
- reflection;
- eval;
- exec;
- runtime plugin loading;
- dynamically constructed protected references;

classification must fail closed unless an independently frozen control establishes safety.

Default:

`CROSS_BOUNDARY`

---

## 17. Preferred long-term UI boundary

The preferred architecture is:

Quant artifacts/contracts

→ read-only adapter or ViewModel

→ UI

The longer-term deployment goal is stronger isolation in which the UI process has:

- no Quant write credential;
- no protected-artifact write path;
- no command authority over protected Quant execution;
- read-only access to explicitly exported presentation contracts.

Deployment isolation is preferred over repeatedly attempting to prove complete non-interference from source inspection alone.

---

## 18. QUANT_ENGINE

Changes affecting Quant/Engine behavior fall into `QUANT_ENGINE`.

This includes, as applicable:

- data pipeline behavior;
- feature engineering;
- statistical models;
- economic/context logic;
- target construction;
- calibration;
- risk;
- position sizing;
- cost model;
- execution;
- experiment infrastructure;
- target-aware diagnostics;
- research governance embedded in Quant execution.

Quant/Engine implementation is normally performed by Codex under Owner/ChatGPT architecture and governance direction.

Independent Auditor review remains required procedurally unless a later amendment changes that rule.

---

## 19. CROSS_BOUNDARY

`CROSS_BOUNDARY` applies when a change crosses presentation and protected Quant/research semantics or when safety cannot be established.

Examples include:

- UI changes to Quant contracts;
- UI changes to shared schemas;
- presentation adapters that transform research meaning;
- mixed UI and Quant changes;
- unresolved dependency closure;
- dynamic behavior preventing conservative classification;
- ambiguous classification.

Both UX review and Quant/governance review are required procedurally for this class.

---

## 20. Review roles

### Quant / Engine

Workflow intent:

Owner + ChatGPT architecture/specification/governance

→ Codex implementation

→ machine-derived checks

→ Independent Auditor review

→ authorized repository actor integrates

The Independent Auditor is a review gate, not the mechanical Git merge actor.

### UX_ONLY

Workflow intent:

Owner + ChatGPT requirements

→ Claude Code implementation

→ machine classification

→ ChatGPT review

→ authorized repository actor integrates

### CROSS_BOUNDARY

Both ChatGPT UX/architecture review and Independent Auditor Quant/governance review are required procedurally.

### Repository actor

The mechanical merge/commit actor must possess actual repository authority.

It may be the Owner, authorized Codex operation, or approved automation.

Review authority and repository write authority are distinct concepts.

---

## 21. Governance amendments affecting reviewer power

A reviewer must not receive unilateral power to entrench or redefine its own authority.

Until an independently authenticated governance reviewer architecture exists, amendments that alter reviewer authority or reviewer semantics require:

- explicit Owner authorization;
- ChatGPT architecture review;
- Independent Auditor advisory review.

Neither ChatGPT nor the Independent Auditor may represent its own review as machine-established independence.

The Owner remains final authority for such self-governance amendments.

This temporary procedure exists under:

`AUDITOR_SELF_GOVERNANCE_INDEPENDENCE_NOT_ESTABLISHED`

and must be reconsidered if authenticated independent governance review becomes available.

---

## 22. Stale review

Review applies only to the exact governed identity.

Any identity-changing modification invalidates prior approval for the changed identity unless a frozen rule explicitly establishes otherwise.

Examples include:

- new commit;
- amend;
- rebase;
- squash;
- conflict resolution;
- changed base identity;
- changed head identity;
- changed merge candidate;
- changed reviewed diff.

No `materiality` exception exists.

The qualifier is identity change, not a human judgment that a change is small.

---

## 23. Review identity

The future merge-gate specification must define a deterministic review identity.

It should bind machine-observed inputs such as:

- base commit;
- head commit;
- merge base where relevant;
- exact diff or patch identity;
- changed-file set;
- review-package SHA-256 where applicable.

A later base movement that changes the governed merge candidate must not silently retain approval.

---

## 24. Independent-review authorship

At T1, chat-based Auditor authorship is not machine-authenticated repository fact.

Auditor `APPROVE/RETURN` remains `E/P`.

A future architecture may make reviewer authorship machine-observable through a genuinely distinct authenticated repository identity, such as an appropriate GitHub PR reviewer account combined with repository controls.

Until then, CI must not claim:

`INDEPENDENT_AUDITOR_AUTHENTICATED = TRUE`

unless such authentication is actually machine established.

---

## 25. Governance exceptions

A governance exception is a committed control input, not a retrospective
explanation.

An Owner override must exist before the affected governed action.

It must be committed before the merge or execution it authorizes.

It must identify, as applicable:

- unique exception identifier;
- exact governed identity;
- exact scope;
- reason;
- gate being overridden;
- one-time or bounded applicability;
- expiration or terminal condition;
- predecessor/sequence identity where applicable.

The future exception mechanism must maintain an append-only exception
ledger or equivalent machine-countable sequence.

Repeated one-time exceptions must therefore remain visible as repeated
exceptions rather than silently behaving like a blanket policy bypass.

Required future control concept:

`GOVERNANCE_EXCEPTION_SEQUENCE`

An exception must not:

- become a silent reusable bypass;
- be created at runtime after the governed action;
- be backfilled after the action;
- retroactively make an already non-compliant action appear compliant.

Any amendment to exception counting, ledger semantics, or bypass scope is
itself:

`GOVERNANCE_AMENDMENT`

---

## 26. Repository enforcement

The intended repository architecture includes machine-enforced controls.

Target controls include:

- protected primary branch or equivalent GitHub ruleset;
- no ordinary direct push;
- PR-based integration;
- required machine-derived CI checks;
- review-identity freshness;
- change classification;
- governance-amendment interception;
- explicit exception handling.

At the canonical T1 snapshot, full repository protection is not established.

Observed classic branch-protection fact:

`NO_CLASSIC_BRANCH_PROTECTION_OBSERVED`

Observed GitHub ruleset state:

`RULESET_STATE_NOT_OBSERVED_AT_T1`

Therefore:

`REPOSITORY_INTEGRATION_PROTECTION_SUFFICIENT = NOT_MACHINE_ESTABLISHED`

T1 must not state that repository integration governance is already
machine-enforced.

A future T2 activation probe must inspect all protection mechanisms relied
upon by the project, including relevant rulesets where used.

---

## 27. Canonical Stage B boundary

Where Stage B V1.2 requires machine-verified remote append-only or
repository-protection enforcement for canonical execution, that requirement
remains a precondition.

At T1:

`CLASSIC_BRANCH_PROTECTION = NO_CLASSIC_BRANCH_PROTECTION_OBSERVED`

and:

`RULESET_STATE = NOT_OBSERVED_AT_T1`

Therefore:

`REQUIRED_REPOSITORY_PROTECTION_FOR_CANONICAL_STAGE_B = NOT_MACHINE_ESTABLISHED`

No new canonical Stage B execution requiring that protection may proceed
until the required repository-enforcement condition is positively
machine-established.

This does not retroactively invalidate completed Sprint-1 L1 exploratory
evidence.

Any historical-invalidity claim requires a separate evidence-based
governance determination.

---

## 28. Enforcement activation phases

T1 establishes architecture and bootstrap authority.

It does not assert complete enforcement.

A later state may establish:

`T2_MACHINE_INTEGRATION_GATES_ACTIVE`

when the required branch/ruleset protection, classifier, governance sentinel, stale-identity handling, CI checks, and control-input mechanisms are machine verified.

Authenticated independent-review enforcement is a separate capability.

Until it is machine established, the limitation remains:

`INDEPENDENT_REVIEW_NOT_REPOSITORY_ENFORCED`

A later architecture may define an authenticated-review activation state without rewriting historical T1 facts.

---

## 29. No retroactive promotion

Later controls must not rewrite historical evidence classes.

A previously declarative Auditor judgment does not become historical machine fact merely because authenticated review is introduced later.

A previously unprotected branch does not become historically protected because protection is enabled later.

Historical repository observations remain historical observations.

---

## 30. No retroactive invalidation by default

Strengthening integration governance does not automatically invalidate completed research or audit evidence.

Historical invalidity requires a separately authorized evidence-based determination tied to the governance requirements actually applicable to the historical action.

---

## 31. Next implementation sequence

After T1 genesis, the intended sequence is:

repository protection establishment and verification

→ change-classification and merge-gate specification

→ machine-gate implementation

→ independent implementation review

→ machine verification

→ enforcement activation

No classifier implementation should precede its frozen specification.

---

## 32. Immediate post-T1 restrictions

Until the control-plane bootstrap reaches the required enforcement state:

- Sprint 2 is not authorized;
- new target-aware candidates are not authorized;
- new realized-label research is not authorized;
- Validation remains unopened;
- Final Test remains sealed;
- canonical Stage B execution requiring branch protection remains blocked.

Target-blind architecture/design work may continue when separately permitted by existing research governance.

---

## 33. Genesis disposition

Transition blocker:

`CLOSED`

Canonical pre-genesis snapshot:

`BOUND`

T1 self-bootstrap recursion:

`RESOLVED_BY_OWNER_AUTHORIZED_GENESIS`

Grandfather-by-speed:

`PROHIBITED`

PR #34 automatic legacy grandfathering:

`NOT_GRANTED`

Machine-derived repository protection:

`NO_CLASSIC_BRANCH_PROTECTION_OBSERVED`

Ruleset state:

`NOT_OBSERVED_AT_T1`

Repository protection sufficient for canonical Stage B:

`NOT_MACHINE_ESTABLISHED`

LLM review binding:

`NOT_MACHINE_VERIFIABLE`

Independent review repository enforcement:

`NOT_ESTABLISHED`

Auditor self-governance independence:

`NOT_ESTABLISHED`

Validation:

`UNOPENED`

Final Test:

`SEALED`

Final marker:

`INTEGRATION_GOVERNANCE_GENESIS`

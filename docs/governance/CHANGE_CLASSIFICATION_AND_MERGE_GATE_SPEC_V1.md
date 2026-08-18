# CHANGE CLASSIFICATION AND MERGE GATE SPEC V1

Status: `SPEC_FREEZE_CANDIDATE`  
Freeze phase: `SPEC_FREEZE`  
Implementation authority: `NOT_AUTHORIZED_UNTIL_OWNER_AUTHORIZES_EXACT_SPEC_FREEZE_IDENTITY`  
Repository: `NonChaianon/mes-quant-engine-v1`  
Default branch: `main`

This document is the consolidated V1 specification produced from Step 3 Drafts 0-7, CFC-1, CFC-2, and internal findings B through L. It supersedes those drafts as the proposed normative text while preserving their audit history as evidence. It does not claim that the classifier, merge gate, Integration Actor, repository enforcement, MAC-V1, or LangGraph runtime exists or is operational.

## 0. Authority, scope, and non-claims

The role of this document is `GOVERNANCE_AMENDMENT_CANDIDATE`.

At `SPEC_FREEZE`, the following remain false:

- `CLASSIFIER_IMPLEMENTED`
- `CLASSIFIER_DEPLOYED`
- `MERGE_GATE_IMPLEMENTED`
- `MERGE_GATE_REPOSITORY_ENFORCED`
- `ADMIN_PREVENTION_ESTABLISHED`
- `INTEGRATION_CREDENTIAL_INDEPENDENCE_ESTABLISHED`
- `LEVEL_2_ESTABLISHED`
- `INDEPENDENT_REVIEW_MACHINE_AUTHENTICATED`
- `MAC_V1_OPERATIONAL`
- `T2_MACHINE_INTEGRATION_GATES_ACTIVE`

`MERGE_GATE_PASS` is impossible before `IMPLEMENTATION_FREEZE`.

Repository enforcement activation after implementation is a separate `GOVERNANCE_AMENDMENT`.

## 1. V1 genesis anchor

The static artifact `docs/governance/CONTROL_PLANE_GENESIS_ANCHOR_V1.json` is the sole V1 genesis-anchor source.

Its exact canonical bytes are part of `SPEC_FREEZE`.

For V1:

- `GENESIS_ANCHOR_SHA256` is derived from the exact anchor bytes.
- `GENESIS_DOMAIN = ASCII("MES-CP-GENESIS-V1") || 0x00`.
- `O_GENESIS_V1 = SHA256(GENESIS_DOMAIN || raw_32_bytes(GENESIS_ANCHOR_SHA256))`.
- `O_GENESIS_V1` becomes an immutable literal constant only when the exact `SPEC_FREEZE` package is Owner-authorized.
- A new genesis is not an ordinary V1 amendment. It requires a new major governance version or refoundation.

The anchor intentionally records the historical Step-2 repository identity by name and Git object identities. Runtime repository-scope identity is separately verified by stable GitHub repository identifiers under Section 35.

## 2. Static SPEC_FREEZE artifacts

`SPEC_FREEZE` consists of exactly these six static artifacts:

1. `docs/governance/CHANGE_CLASSIFICATION_AND_MERGE_GATE_SPEC_V1.md`
2. `docs/governance/CONTROL_PLANE_GENESIS_ANCHOR_V1.json`
3. `configs/governance/PROTECTED_SURFACE_MANIFEST_V1.json`
4. `configs/governance/ANALYZER_LIMITS_V1.json`
5. `configs/governance/REMOTE_OBSERVATION_SETTLE_POLICY_V1.json`
6. `configs/governance/CLASSIFICATION_RECORD_SCHEMA_V1.json`

Runtime/generated objects whose schemas are governed by this specification include:

- `CLASSIFICATION_RECORD_V1`
- `CONTROL_PLANE_EXPECTATION_INTENT_V1`
- `CONTROL_PLANE_ACTIVATION_BINDING_V1`
- `TRANSITION_EXECUTION_JOURNAL_V1`
- transition disposition records
- review bundles and merge-gate evidence

A runtime record instance is not a seventh static `SPEC_FREEZE` artifact.

## 3. Two freeze phases

V1 has two distinct freeze phases.

### 3.1 SPEC_FREEZE

`SPEC_FREEZE` freezes:

- policy semantics,
- protected-surface manifest,
- record schema,
- analyzer resource limits,
- remote observation settle policy,
- genesis anchor.

At this phase there is no classifier implementation identity and no analyzer implementation/toolchain identity that can authorize a merge.

### 3.2 IMPLEMENTATION_FREEZE

`IMPLEMENTATION_FREEZE` occurs only after Codex implementation, implementation review, machine verification, and a governance amendment that binds exact implementation identities.

`IMPLEMENTATION_FREEZE` MUST bind:

- classifier implementation path and hash,
- governance sentinel implementation path and hash,
- merge-gate implementation path and hash,
- privileged verifier/workflow paths and identities,
- analyzer configuration identity,
- analyzer toolchain digest,
- any Integration Actor identity required by the chosen enforcement mode,
- an amended `PROTECTED_SURFACE_MANIFEST_V1` successor that protects every implementation control path.

Until those implementation paths are protected by the active successor manifest, `IMPLEMENTATION_FREEZE` is prohibited.

This requirement closes the bootstrap self-protection gap: implementation files do not exist at `SPEC_FREEZE`, therefore they cannot be listed as existing implementation paths yet; they MUST be added by a governed manifest amendment before implementation authority is activated.

## 4. Governed candidate relation

V1 supports `SINGLE_COMMIT_CANDIDATE_ONLY`.

Mandatory relation:

- `parent_count(head) == 1`
- `head.parent == base`
- `merge_base == base`
- `base` is an ancestor of `head`

Violation is `CANDIDATE_RELATION_FAILURE -> BLOCK`.

Multi-commit candidate history is `MULTI_COMMIT_CANDIDATE_UNSUPPORTED_V1 -> BLOCK`.

Squash, rebase, amend, conflict resolution, or commit replacement MUST occur before classification and review identity are created.

Any change to base, head, merge base, tree delta, classifier identity, manifest identity, schema identity, analyzer identity, or toolchain identity makes prior classification/review evidence `STALE`. There is no materiality exception.

## 5. Canonical repository facts

Classifier inputs are repository/machine facts only.

Required inputs include:

- base commit SHA-1,
- head commit SHA-1,
- merge-base SHA-1,
- base tree SHA-1,
- head tree SHA-1,
- complete canonical tree delta,
- old/new Git object identities,
- old/new file modes,
- raw Git path bytes.

Canonical tree operations are:

- `ADD`
- `MODIFY`
- `DELETE`
- `FILE_MODE_CHANGE`
- `SYMLINK_CHANGE`
- `SUBMODULE_POINTER_CHANGE`

Rename heuristics are non-authoritative. A rename may be represented canonically as delete plus add.

Developer prose, PR title, Codex statement, Claude statement, ChatGPT opinion, review verdict, claimed risk, and review-package identity are forbidden classifier predicates.

## 6. Governance Sentinel and self-protection

Governance interception runs before ordinary classification.

A candidate touching governance-control paths or governance semantics adds `GOVERNANCE_AMENDMENT` to the detected class set.

Governance precedence controls process order; it does not erase ordinary classes.

The sentinel MUST protect:

- this specification,
- the genesis anchor,
- the protected-surface manifest,
- classification-record schema,
- analyzer limits,
- remote settle policy,
- classifier implementation once it exists,
- sentinel implementation once it exists,
- merge-gate implementation once it exists,
- privileged workflow/verifier controls once they exist,
- exception semantics,
- review semantics,
- stale-identity semantics,
- control-plane expectation lifecycle.

Manifest anti-shrink uses the predecessor manifest and candidate-manifest diff. Candidate manifest bytes never become authority for their own amendment.

Removing or narrowing protected paths/modules/symbols/schema surfaces, removing the sentinel, or weakening a governed boundary adds `GOVERNANCE_AMENDMENT`.

## 7. Class universe and classification outcomes

V1 class universe is exactly:

- `GOVERNANCE_AMENDMENT`
- `UX_ONLY`
- `QUANT_ENGINE`
- `CROSS_BOUNDARY`

`detected_classes` is a set.

Multiple classes may coexist. Required gates are the union of all detected-class gates.

Classifier execution outcome is one of:

- `CLASSIFIED`
- `AMBIGUOUS`
- `CLASSIFIER_FAILURE`

`AMBIGUOUS` means the trusted classifier completed normally under the frozen schema but machine evidence cannot establish a narrower safe ordinary classification. It adds `CROSS_BOUNDARY`.

An unfrozen or invalid class token is not ambiguity. It is `CLASSIFICATION_SCHEMA_VIOLATION -> CLASSIFIER_FAILURE -> BLOCK`.

`CLASSIFIER_FAILURE` includes crash, timeout, corrupt input, unavailable trusted toolchain, parser failure, resource exhaustion, incomplete mandatory scan, missing manifest/schema, or version mismatch.

Classifier failure does not produce a canonical `CLASSIFICATION_RECORD_V1`; therefore the canonical record field `failure_state` is deliberately constrained to `NONE`.

## 8. Deterministic manifest category-to-class mapping

The active `PROTECTED_SURFACE_MANIFEST_V1` is authoritative for what is protected. This section is authoritative for how each manifest category contributes to classes.

### 8.1 Governance categories

A change matching any of:

- `governance_control_exact_paths`
- `governance_control_prefixes`
- `byte_policy_exact_paths`

adds `GOVERNANCE_AMENDMENT`.

A change matching `ci_control_prefixes` adds both:

- `GOVERNANCE_AMENDMENT`
- `CROSS_BOUNDARY`

because CI is both governance-sensitive and execution-boundary-sensitive.

### 8.2 Quant categories

A change matching any of:

- `protected_quant_exact_paths`
- `protected_quant_prefixes`
- `protected_quant_modules`
- `protected_symbols`
- `protected_artifact_prefixes`
- `protected_schema_prefixes`

adds `QUANT_ENGINE`.

If the same change also matches a dependency/CI/execution-sensitive category, class union applies.

### 8.3 Execution/dependency categories

A change matching `execution_sensitive_prefixes` but not otherwise proven to be a directly protected Quant or governance surface adds `CROSS_BOUNDARY`.

A change matching `dependency_manifest_exact_paths` adds `CROSS_BOUNDARY`. If it also matches a protected Quant path, it also adds `QUANT_ENGINE`.

### 8.4 Presentation categories

A change can be eligible for `UX_ONLY` only if it lies within an active frozen presentation boundary represented by `presentation_roots` or `read_only_adapter_modules` and passes Sections 9-10.

At initial `SPEC_FREEZE`:

- `presentation_roots = []`
- `read_only_adapter_modules = []`

Therefore `UX_ONLY` is intentionally unreachable at initial V1 `SPEC_FREEZE`.

This is a deliberate fail-safe state, not an implementation defect. Until a later `GOVERNANCE_AMENDMENT` freezes a real presentation/read-only boundary, candidate UI-like changes cannot be classified `UX_ONLY`; they default to `CROSS_BOUNDARY` unless another class also applies.

An implementation MUST still implement the `UX_ONLY` enum and proof logic, but tests at initial `SPEC_FREEZE` MUST assert that no candidate can reach `UX_ONLY` while both presentation-boundary lists remain empty.

## 9. Manifest matching semantics

Path matching uses raw Git path bytes.

- exact path: raw Git path bytes equal the ASCII manifest path bytes.
- prefix path: raw Git path bytes start with the ASCII manifest prefix bytes.
- no NFC normalization.
- no NFD normalization.
- no filesystem normalization.
- no case folding.

Module matching uses `exact_or_descendant_dotted_module_match`.

If protected module is `mes_quant.features`, then both `mes_quant.features` and `mes_quant.features.builder` match; `mes_quant.feature` does not.

Symbol matching uses exact fully-qualified `module:qualname` identity.

Example: `mes_quant.features.contract:FeatureContract`.

An empty `protected_symbols` array means no symbol-level entries are independently protected beyond module/path protections. It does not weaken path/module protection.

## 10. Bidirectional capability and reference analysis

`UX_ONLY` is capability-proven, never path-declared.

The trusted analyzer performs both:

- forward closure: changed executable/reference node -> reachable dependencies/capabilities;
- reverse protected reachability: protected Quant roots -> whether protected side can reach the changed node.

For `UX_ONLY`, all of the following MUST hold:

1. forward closure cannot reach protected capability;
2. no protected module/symbol can reach the changed node;
3. the changed node is within the frozen presentation/read-only boundary;
4. no unresolved dynamic behavior exists;
5. no protected semantic transformation exists.

If protected-side dynamic behavior prevents reverse reachability proof, add `CROSS_BOUNDARY`.

### REFERENCE_SCAN_SCOPE_V1

Bidirectional analysis MUST NOT be limited to Python import edges.

Where applicable, the trusted analyzer MUST inspect:

- Python imports and from-imports,
- literal repository-path references,
- dotted module-name references,
- protected symbol-name references where statically resolvable,
- YAML references,
- JSON references,
- TOML references,
- shell/script path and command references as static data only,
- GitHub Actions workflow references,
- build-system references,
- package/configuration references,
- declared local dependency references.

Reference scanning has three non-overlapping outcomes.

#### A. Supported and resolved

If the supported reference is resolved, ordinary closure/class rules apply.

If it reaches a protected or cross-boundary capability, add the appropriate class.

#### B. Unsupported-but-readable possible consumer

If a tracked file is readable as inert bytes but V1 has no governed semantic analyzer for that file/reference type, the analyzer MUST:

- record the file/reference type in `unsupported_reference_file_types`,
- increment `unsupported_reference_files`,
- treat narrower separation as unproven,
- add `CROSS_BOUNDARY`.

Examples may include an unsupported Dockerfile dialect, Makefile construct, `.env`-style configuration, or opaque-but-readable configuration format.

This condition is not by itself `CLASSIFIER_FAILURE`, because the analyzer successfully established that the consumer type is unsupported and conservatively classified the candidate.

#### C. Mandatory scan failure

Parser failure, hostile-input handling failure, resource-limit exhaustion, incomplete required scan, missing required object, or inability to enumerate the required repository scope is `CLASSIFIER_FAILURE -> BLOCK`.

Absence of an import edge MUST NOT be interpreted as absence of a reference or capability edge.

## 11. Dynamic and semantic fail-safe rules

Dynamic import, reflection, `eval`, `exec`, runtime plugins, constructed protected references, unresolved module references, and unresolved dynamic protected references prevent narrower capability proof and add `CROSS_BOUNDARY` when analysis completes normally.

A parser/tool failure is not semantic ambiguity. It is classifier failure.

Read-only is not automatically semantically safe.

Changes to:

- units,
- scaling,
- rounding semantics,
- aggregation,
- probability transformation,
- loss transformation,
- sign,
- thresholds,
- missing-value meaning,
- metric identity,
- fold/session mapping

add at least `CROSS_BOUNDARY` unless a future frozen machine-verifiable presentation contract explicitly permits them.

Pure layout, spacing, typography, color, and non-semantic visual changes may become UX-eligible only after a non-empty frozen presentation boundary exists.

`PROVEN_INERT`, `INERT_FAST_PATH`, and `REDUCED_INERT_GATE` are out of scope for V1.

## 12. Candidate treated as hostile data

Hard invariants:

- `ANALYZER_CREDENTIALS = NONE`
- `ANALYZER_NETWORK = DENIED`
- `CANDIDATE_EXECUTION = PROHIBITED`
- `CANDIDATE_CHECKOUT = PROHIBITED_V1`

Candidate content is read from Git tree/blob object bytes.

Mode handling:

- `100644`: parse bytes only;
- `100755`: parse bytes only, never execute;
- `120000`: treat blob as symlink-target bytes, never dereference;
- `160000`: treat as submodule pointer, never initialize.

Forbidden in privileged classification:

- importing candidate modules,
- running candidate `__init__.py`,
- running `setup.py`,
- running `conftest.py`,
- resolving candidate plugin entry points,
- installing candidate or candidate dependencies,
- sourcing candidate shell scripts,
- executing candidate build hooks,
- checking out candidate as executable working tree,
- initializing candidate submodules.

Preferred V1 object access is `git cat-file` or equivalent direct immutable object access.

## 13. Analyzer toolchain and limits

Every classification binds:

- classifier-spec identity,
- classifier-implementation identity,
- protected-surface-manifest identity,
- classification-record-schema identity,
- analyzer-configuration identity,
- analyzer-toolchain digest,
- analyzer-limits identity.

At `SPEC_FREEZE`, implementation/toolchain identities are not yet operationally bound. They become mandatory at `IMPLEMENTATION_FREEZE`.

The analyzer toolchain MUST be reproducible, for example by exact OCI image digest plus pinned parser/runtime package identities. `latest`, `ubuntu-latest`, `python 3.x`, or similar floating identifiers are prohibited authority identities.

`ANALYZER_LIMITS_V1.json` is a governed control input.

No analyzer or record output may be truncated.

If any governed limit is exceeded, emit a named classifier failure and `BLOCK`.

The record-level cardinality limits are intentionally below the total record-byte ceiling so normal cardinality enforcement is reachable before the aggregate byte ceiling in ordinary minimum-size records. Aggregate `max_record_bytes` remains an independent fail-closed upper bound.

## 14. Deterministic CLASSIFICATION_RECORD_V1

A canonical record contains no nondeterministic execution metadata.

Forbidden canonical fields include wall clock, timestamp, PID, hostname, random value, temporary path, filesystem enumeration order, thread scheduling order, and network response order.

Canonical record binds:

- repository stable ID and node ID,
- base/head/merge-base,
- base/head trees,
- canonical tree delta,
- classifier spec/implementation identities,
- manifest identity,
- record-schema identity,
- analyzer config/toolchain/limits identities,
- classification outcome,
- detected classes,
- forward/reverse closure summaries,
- reference scan summary,
- unresolved nodes,
- unsupported reference file types,
- required gate union,
- `failure_state = NONE`.

Classifier re-execution establishes determinism, identity binding, and re-derivability. It does not establish policy correctness.

Explicit limitation:

`CLASSIFIER_REEXECUTION_DOES_NOT_ESTABLISH_POLICY_CORRECTNESS`.

## 15. Canonical serialization

Canonical JSON rules for governed JSON artifacts/records are:

- UTF-8;
- no BOM;
- LF line ending;
- exactly one final LF;
- `ensure_ascii = true`;
- no duplicate object keys;
- no insignificant whitespace;
- canonical object key order as defined by the frozen serialization procedure;
- JSON integers only for numeric authority fields;
- no float, exponent form, NaN, or Infinity.

Decimal/floating semantics MUST use schema-defined canonical strings.

Git path authority is raw Git path bytes.

Path authority in the record is base64 of raw bytes. Human-readable decoded paths, if emitted diagnostically, are non-authoritative.

No Unicode normalization is allowed for path identity.

## 16. Classification-record schema and privilege boundary

`configs/governance/CLASSIFICATION_RECORD_SCHEMA_V1.json` is the machine-readable frozen authority for `CLASSIFICATION_RECORD_V1`.

Unknown fields are prohibited.

The privileged orchestrator MUST treat record `R` as hostile structured data.

Before persistence, review-bundle construction, gate routing, or any privileged use, validate against the exact frozen schema and governed resource limits.

Forbidden executable-control field names include:

- `command`
- `script`
- `shell`
- `callback`
- `url_to_execute`
- `plugin`
- `entry_point`
- `dynamic_expression`
- `code`

The orchestrator MUST NOT dynamically interpret record values, shell-expand them, import modules named by them, load plugins named by them, invoke URLs supplied by them, or instantiate arbitrary classes from them.

At classifier-output stage, invalid enum/schema output is primarily `CLASSIFICATION_SCHEMA_VIOLATION -> CLASSIFIER_FAILURE -> BLOCK`.

At serialized-record privilege boundary, any schema/type/unknown-field/resource defect is `CLASSIFICATION_RECORD_PRIVILEGE_BOUNDARY_VALIDATION_FAILURE -> CLASSIFIER_FAILURE -> BLOCK`.

If the same underlying defect is observed at both layers, logs MUST mark the classifier-output schema violation as primary and the privilege-boundary rejection as defense-in-depth, not as two independent root causes.

## 17. Verify before canonical evidence write

Derive record `R`.

Independently re-derive `R'` using the exact same frozen policy/toolchain identities but an independent trusted verifier execution.

Require byte equality.

If `R != R'`:

- `BLOCK`;
- no canonical evidence write.

If equal:

1. validate `R` under Section 16;
2. compute external record SHA-256;
3. append only the validated record to the canonical evidence ref.

The canonical record MUST NOT embed its own hash.

Rejected/provisional records may exist only in a non-authoritative diagnostic system, not in the canonical evidence namespace.

## 18. Evidence ref is storage, not trust root

Canonical records are not committed into the candidate tree they classify.

Conceptual evidence ref:

`refs/heads/governance/classification-evidence-v1`.

Conceptual path:

`records/<classification_record_sha256>.json`.

Evidence ref semantics:

- content-addressed;
- append-only;
- single-parent;
- fast-forward only;
- no deletion;
- no modification of an existing content-addressed record;
- JSON record mode `100644`;
- no symlink;
- no submodule.

The evidence ref uses a separate future ruleset, conceptually `MES Classification Evidence Integrity V1`. It MUST NOT be added to Step-2 Integrity Ruleset `20913443` merely for evidence storage.

Presence on the evidence ref is not sufficient merge authority. The merge gate MUST re-establish current identity/freshness and trusted re-derivation.

## 19. Review bundle and evidence classes

Order is:

repository facts -> classification -> verified canonical record -> review bundle -> human/model review.

Review bundle binds:

- base/head/merge-base,
- exact diff/tree identity,
- classification record SHA-256,
- classifier identities,
- manifest/schema/toolchain identities,
- machine checks.

Review package identity is never classifier input.

Human/model review remains E/P.

Machine evidence may establish that a review record exists and claims a particular bundle reference; it MUST NOT overclaim actual LLM byte inspection or independent reviewer authentication.

Retained limitations:

- `LLM_REVIEW_BINDING_NOT_MACHINE_VERIFIABLE`
- `INDEPENDENT_REVIEW_NOT_REPOSITORY_ENFORCED`
- `AUDITOR_SELF_GOVERNANCE_INDEPENDENCE_NOT_ESTABLISHED`

ChatGPT review of this co-drafted specification is `CREATOR_SIDE / SAME_FAMILY_REVIEW`, not independent review.

## 20. Required gate union

Routing:

- `GOVERNANCE_AMENDMENT` -> governance/bootstrap gate;
- `UX_ONLY` -> machine checks + ChatGPT UX/architecture review;
- `QUANT_ENGINE` -> machine checks + Independent Auditor review + Owner authorization;
- `CROSS_BOUNDARY` -> machine checks + ChatGPT architecture review + Independent Auditor review + Owner authorization;
- multiple classes -> union of all applicable gates.

The classifier routes; it never approves merge.

An LLM severity judgment cannot remove a machine-derived gate.

## 21. Pre-integration merge gate

`MERGE_GATE_PASS` requires all of:

1. candidate relation valid;
2. trusted classifier success;
3. canonical record exists;
4. trusted re-derivation matches exact record;
5. privilege-boundary record validation passes;
6. canonical record persisted correctly;
7. spec/manifest/schema/implementation/toolchain identities match active frozen versions;
8. classification and reviews are fresh;
9. required gate union re-derived;
10. required deterministic checks pass;
11. required procedural reviews are present and claim the exact review identity;
12. no unresolved required `RETURN`;
13. any exception is pre-existing, valid, bounded, and identity-bound;
14. reviewed candidate identity remains unchanged;
15. current applicable control-plane predicate passes;
16. expected integration mechanism is healthy.

Before `IMPLEMENTATION_FREEZE`, conditions requiring implementation/toolchain identities cannot pass; therefore `MERGE_GATE_PASS` is impossible.

`MERGE_GATE_PASS` means only `AUTHORIZED_TO_ATTEMPT_INTEGRATION`.

It is not post-integration proof.

## 22. Post-integration verification

After integration, machine verification observes:

- old main SHA,
- new main SHA,
- reviewed head SHA,
- parent/history relation,
- tree relation,
- current control-plane observation.

Require:

`new_main_sha == exact_reviewed_head_sha`.

Only then derive `EXACT_INTEGRATION_VERIFIED`.

Commit author/committer metadata MUST NOT be treated as pusher identity.

Pusher/actor identity is F only when captured from a sufficiently authenticated machine source with preserved provenance.

## 23. Repository enforcement claims

Separate:

- `SPECIFIED`
- `IMPLEMENTED`
- `REPOSITORY_ENFORCED`

Enforcement levels:

- `LEVEL_0 = PROCEDURAL_ONLY`
- `LEVEL_1 = MACHINE_GATE_IMPLEMENTED_NOT_REPOSITORY_REQUIRED`
- `LEVEL_2 = REPOSITORY_REQUIRED_EXTERNALLY_ANCHORED_TAMPER_EVIDENT`
- `LEVEL_3 = ADMIN_INDEPENDENT_PREVENTION`

Current single-admin architecture MUST NOT claim Level 2 without an external liveness/expectation anchor, and MUST NOT claim Level 3 without actual admin-independent prevention.

Retained limitations:

- `RULESET_ADMIN_MUTABILITY_PREVENTION_NOT_ESTABLISHED`
- `INTEGRATION_ACTOR_CREDENTIAL_INDEPENDENCE_NOT_ESTABLISHED`
- `REPOSITORY_INTERNAL_MONITOR_LIVENESS_NOT_SELF_ESTABLISHING`

## 24. Integration Actor

Target architecture may use an authenticated Integration Actor to provide:

- identity-separated audit trail,
- narrow normal integration path,
- exact fast-forward integration.

It MUST NOT be described as cryptographically independent from the Owner if Owner/admin can control installation or credentials.

Target ordinary configuration may state:

`ORDINARY_OWNER_BYPASS_NOT_CONFIGURED`.

It MUST NOT state:

`OWNER_BYPASS_PREVENTED`.

If an Integration Actor cannot meet V1 requirements because of a named platform limitation, fallback consideration requires a separate governance amendment. No time/fatigue-triggered downgrade is permitted.

## 25. Control-plane expectation lifecycle

Step-2 closure remains immutable historical evidence.

Current operational expectations evolve prospectively:

`Operational O_n -> successor Intent I_(n+1) -> Authorized Transition -> Activation Binding B_(n+1) -> Operational O_(n+1)`.

Intent predecessor is the exact prior operational composite identity, never merely the prior intent hash.

There is no Recovery Lane in V1.

## 26. Expectation Intent

`CONTROL_PLANE_EXPECTATION_INTENT_V1` contains only precommittable semantics:

- predecessor operational identity;
- closed-world logical resource set;
- target refs;
- conditions;
- rule semantics;
- bypass semantics;
- actor requirements;
- privileged workflow identities;
- required permission semantics;
- ordered transition plan.

Future server-assigned resource IDs, `created_at`, `updated_at`, and GitHub-composed derived active-rule payloads are `BIND_AT_ACTIVATION`.

## 27. Activation Binding and operational identity

`CONTROL_PLANE_ACTIVATION_BINDING_V1` captures actual machine-observed server state after an authorized transition.

Normal binding enum:

`binding_type = NORMAL_ACTIVATION`.

Operational domain:

`OP_DOMAIN = ASCII("MES-CP-OPERATIONAL-V1") || 0x00`.

Operational identity:

`O_n = SHA256(OP_DOMAIN || raw_32_bytes(INTENT_SHA256) || raw_32_bytes(ACTIVATION_BINDING_SHA256))`.

Ordinal epoch labels are display metadata, not machine identity.

## 28. Expectation chain invariants and withdrawal

Genesis is `O_GENESIS_V1`.

For each operational node:

`MAX_NON_WITHDRAWN_SUCCESSOR_INTENTS = 1`.

For each non-withdrawn Intent:

`MAX_VALID_ACTIVATION_BINDINGS = 1`.

A pending Intent occupies the successor slot until it is activated or validly withdrawn.

A `WITHDRAWN` Intent remains permanently discoverable in chain history but does not occupy the predecessor's successor slot.

A new successor Intent may be admitted only after the withdrawal disposition that releases the prior slot is durably integrated and discoverable by the resolver.

Two non-withdrawn successor Intents from the same operational node are `OPERATIONAL_SUCCESSOR_FORK -> BLOCK`.

Two valid activation bindings for one Intent are `MULTIPLE_ACTIVATION_BINDINGS -> BLOCK`.

An activation without a matching precommitted Intent is `ORPHAN_ACTIVATION -> INVALID`.

## 29. Canonical chain scan scope

Resolver scans main ancestry from current main back to fixed genesis and scans only the frozen canonical expectation-storage prefixes.

It records:

- repository stable identifiers;
- default branch;
- genesis commit;
- current main;
- history range;
- canonical paths scanned;
- commit count;
- object count.

Code search is not authority for absence.

Partial/truncated/paginated-incomplete traversal, missing Git object, unresolved path scan, or non-linear governed history is `EXPECTATION_SCAN_INCOMPLETE -> BLOCK`.

## 30. Closed-world control-plane expectation

The active expectation declares the exact governed control-plane universe.

Actual governed resources targeting main MUST equal the expected bound set, not merely contain it.

An unenumerated extra governed resource is drift.

Exact closed-world dimensions include:

- governed main-targeting resource set,
- rule contribution per resource,
- conditions,
- target refs,
- bypass actor sets,
- Integration Actor expectations,
- privileged workflow identities,
- classifier/verifier identities after implementation freeze,
- classic protection expectation,
- repository scope predicate.

## 31. Repository scope predicate

Runtime repository authority uses stable GitHub identifiers:

- repository database ID = `1329447686`;
- repository node ID = `R_kgDOTz3DBg`.

Repository `full_name` is display metadata and is non-authoritative for stable identity.

Before every canonical control-plane verification and every Authorized Transition mutation, trusted repository metadata observation MUST establish:

- database ID matches;
- node ID matches;
- default branch is `main`;
- `owner.type == "User"`.

If repository metadata cannot be observed, `REPOSITORY_SCOPE_OBSERVATION_FAILURE -> BLOCK`.

If stable identity changes, default-branch governance assumption changes, or owner type ceases to be `User`, emit `REPOSITORY_SCOPE_ASSUMPTION_INVALIDATED -> BLOCK -> GOVERNANCE_AMENDMENT / REFOUNDATION REQUIRED`.

This V1 closed-world design MUST NOT be generalized automatically to organization/enterprise repositories with inherited organization-level rulesets.

## 32. Observation schema closed-world rule

Raw remote payloads are hostile external data.

Frozen observation projections MUST define exact accepted fields.

If a raw governed payload includes a field outside the frozen observation schema:

`OBSERVATION_SCHEMA_UNKNOWN_FIELD`.

Unknown fields MUST NOT be silently dropped.

If no mutation is in flight, observation becomes unusable and the applicable read-only observation state is blocked.

If a mutation is in flight and its outcome cannot be established, control plane becomes compromised.

Accepting a new behavior-affecting remote field requires a governance amendment.

Raw payload evidence and canonical projection evidence MUST both be preserved.

## 33. Observation settling

`SETTLED` means only:

two consecutive identical canonical observations.

Settlement is independent of expectation matching.

After settlement:

- satisfies predicate -> `SETTLED_MATCH`;
- fails predicate -> `SETTLED_MISMATCH`.

No settlement within bounded attempts -> `OBSERVATION_INCONCLUSIVE`.

One observation cycle follows the frozen delays in `REMOTE_OBSERVATION_SETTLE_POLICY_V1.json`.

A stable mismatch MUST NOT be retried until it appears to match.

## 34. Observation-cycle budgets

Transition budget:

`MAX_OBSERVATION_CYCLES_PER_TRANSITION_STEP = 2`.

The counter is keyed by exact transition Intent identity plus transition step ID.

New workflow run, process restart, API invocation, or authorization does not reset it.

Cycle 2 is permitted only if Cycle 1 was inconclusive.

A third transition cycle is prohibited by V1.

Normal verification uses:

`MAX_OBSERVATION_CYCLES_PER_NORMAL_VERIFICATION = 2`.

A normal verification invocation is read-only. A later new normal verification may be executed because it causes no remote mutation; stable mismatch from any verification still immediately becomes drift. Re-running a read-only verification cannot turn an already settled mismatch into a match by retry policy because settled mismatch is terminal for that observation event.

## 35. Observation blocked versus compromised

### NORMAL_OBSERVATION_BLOCKED

If normal verification exhausts two cycles and remains inconclusive:

- ordinary integration is blocked;
- remote mutation is not authorized by this state;
- the system does not claim compromise.

A later read-only normal verification may be attempted.

### TRANSITION_OBSERVATION_BLOCKED

If a transition step exhausts its two-cycle budget, remains inconclusive, and `MUTATION_IN_FLIGHT = FALSE`:

- transition cannot advance;
- new remote mutation is blocked;
- ordinary integration is blocked;
- observation counter does not reset.

Exit requires named `TRANSITION_OBSERVATION_GOVERNANCE_DISPOSITION` under at least the T1 temporary bootstrap review procedure.

The disposition cannot silently reset the counter, authorize mutation, or resume the transition.

Its allowed outcomes are exactly:

1. `ABANDON_TRANSITION`;
2. `AMEND_BUDGET_OR_PLAN`;
3. `REFOUNDATION`.

`AMEND_BUDGET_OR_PLAN` is a governance amendment. It is not a runtime retry.

`REFOUNDATION` is outside ordinary Step-3 V1 machinery.

### CONTROL_PLANE_COMPROMISED

If a remote mutation attempt is in flight or has occurred and its result cannot be established, or if a settled state mismatches the authorized transition predicate, V1 enters `CONTROL_PLANE_COMPROMISED`.

No Recovery Lane exists.

## 36. ABANDON_TRANSITION

`ABANDON_TRANSITION` exists solely to prevent a no-mutation dead Intent from consuming the predecessor successor slot forever.

It is permitted only when all conditions are machine-established:

1. the Intent has no valid Activation Binding;
2. the transition journal proves zero remote mutating API attempts for the entire Intent;
3. `MUTATION_IN_FLIGHT = FALSE`;
4. a fresh governance-disposition observation establishes that the remote control plane still exactly matches the predecessor operational expectation;
5. there is no orphaned transition resource;
6. no unauthorized control-plane drift is observed;
7. the disposition is reviewed and authorized under at least the T1 temporary bootstrap review procedure.

The governance-disposition observation in condition 4 is not a third V1 transition observation cycle. It belongs to the external bootstrap disposition procedure and cannot authorize transition continuation. Its sole purpose is to prove that withdrawal is safe because the abandoned Intent made no remote mutation.

The original Intent bytes are immutable.

A separate append-only disposition record marks the Intent `WITHDRAWN`.

The disposition record binds:

- Intent SHA-256;
- predecessor operational identity;
- transition journal head hash;
- transition journal entry count;
- proof of zero remote mutation attempts;
- fresh predecessor-state observation identity;
- Owner authorization identity/reference;
- review evidence references.

After the disposition is durably integrated and resolver-visible:

- the abandoned Intent's observation counters die permanently with that Intent;
- the predecessor successor slot is released;
- a new successor Intent may later be proposed.

A withdrawn Intent can never be reactivated.

If any remote mutating API attempt exists in the journal, `ABANDON_TRANSITION` is prohibited.

## 37. Transition execution journal

Before every mutating API call, append and durably persist a `MUTATION_ATTEMPT` journal entry.

Only after that append does `MUTATION_IN_FLIGHT = TRUE`.

Journal entries bind at least:

- sequence number,
- previous-entry hash,
- transition Intent identity,
- transition step ID,
- operation class,
- observation hashes,
- provisional resource bindings,
- result state.

No journal append -> no next mutation.

Sequence gaps -> `TRANSITION_JOURNAL_SEQUENCE_GAP -> BLOCK`.

Activation Binding MUST bind the final journal head hash and journal entry count.

The journal is machine-captured execution evidence. V1 does not claim admin-independent immutable external storage unless separately established.

## 38. Authorized Transition state machine

A successor Intent contains an ordered transition plan:

`S0, S1, ... Sn`.

Each step defines:

- allowed mutation;
- exact fields permitted to change;
- exact fields prohibited from changing;
- expected semantic state after the step.

Remote state must settle to exactly one authorized intermediate-state predicate.

Settled mismatch is `AUTHORIZED_TRANSITION_STATE_MISMATCH -> CONTROL_PLANE_COMPROMISED`.

No rollback/recovery mutation exists inside V1.

## 39. Provisional resource binding

When an authorized step creates a GitHub resource:

Before create, establish the pre-create inventory and absence of ambiguous same-logical-name resource unless the Intent explicitly targets an existing exact ID.

After create, bounded observation must establish inventory delta exactly:

- added = 1;
- deleted = 0;
- unrelated modified = 0.

Capture the server-assigned stable resource ID immediately into a `PROVISIONAL_RESOURCE_BINDING`.

Persist that binding in the transition journal before any subsequent mutation.

Resource name alone is not identity.

A process failure after resource creation but before successful transition completion may create `ORPHANED_TRANSITION_RESOURCE -> CONTROL_PLANE_COMPROMISED`.

V1 does not delete, adopt, or repair such orphan resources.

## 40. Transition mode persists until chain catches up

Remote mutation success does not end transition mode.

Transition mode remains active until:

- final server state is settled and semantically validated;
- Activation Binding is created;
- activation record is governed and integrated;
- resolver derives exact successor operational identity.

Before that:

- ordinary integration is blocked;
- canonical Stage B is blocked.

This prevents remote E(n+1) state from being misread under predecessor E(n) normal predicate.

## 41. Fail-stop and refoundation

V1 operational modes are:

- `NORMAL`;
- `AUTHORIZED_TRANSITION`.

Fail-stop states include:

- `NORMAL_OBSERVATION_BLOCKED`;
- `TRANSITION_OBSERVATION_BLOCKED`;
- `CONTROL_PLANE_COMPROMISED`.

There is no V1 Recovery Lane, Restoration Binding, auto-repair, or rollback lane.

`CONTROL_PLANE_COMPROMISED` is terminal for Step-3 V1 machinery.

Minimum named manual exit is `CONTROL_PLANE_REFOUNDATION`, using at least the T1 temporary bootstrap review procedure:

- explicit Owner authorization;
- exact machine-observed scope where obtainable;
- ChatGPT governance/architecture review;
- Independent Auditor advisory review where available;
- machine/static checks appropriate to the action;
- exact identity-bound candidate;
- stale-review invalidation.

Refoundation is not V1 recovery and cannot retroactively normalize unauthorized mutation.

Historical incident evidence remains historical.

## 42. Step-2 to Step-3 coordinated activation

Phase-3 enforcement changes the live main control plane and therefore cannot retain Step-2 remote expectations as the forever-current operational state.

Sequence:

1. precommit successor Intent;
2. governance review and authorization;
3. enter Authorized Transition;
4. mutate remote control plane under ordered plan;
5. observe and provisionally bind server-assigned resources;
6. validate closed-world final semantics;
7. create Activation Binding;
8. integrate activation record;
9. successor operational expectation becomes current.

Step-2 closure bytes remain immutable historical evidence.

No post-hoc expectation creation is permitted.

## 43. Control-plane drift scope

Current-state verification includes:

- ruleset IDs and semantics;
- ruleset conditions;
- bypass actors;
- enforcement state;
- Integration Actor app/install identity where observable;
- Integration Actor permissions where observable;
- repository installation state;
- privileged workflow identities;
- classifier/verifier identities after implementation freeze;
- manifest/schema/toolchain identities;
- repository stable identity and ownership-model predicate.

Credential possession or other platform-invisible facts remain unknown/limitations and are not promoted to F.

## 44. Privileged workflow invariant

Privileged classifier, verifier, gate, and integration workflow logic MUST come from a trusted frozen/default-branch or externally pinned authority identity.

Candidate-controlled workflow bytes cannot authorize their own integration.

Hard invariant:

`CANDIDATE_CONTROLLED_WORKFLOW_CANNOT_AUTHORIZE_ITS_OWN_INTEGRATION`.

If a privileged GitHub event such as `pull_request_target` is used, it MUST NOT execute untrusted candidate content.

## 45. Evidence and expectation pagination/truncation

GitHub API tree/list responses MUST NOT be assumed complete.

If a response is truncated or paginated, implementation MUST continue using an exact supported lookup/traversal mechanism.

A `truncated=true` result MUST NOT be interpreted as evidence that an object does not exist.

Incomplete required traversal is failure/blocked according to the applicable machine predicate.

## 46. Remote settle observations are preserved incrementally

Observation evidence MUST be appended incrementally to the transition journal or an equivalently bound machine evidence sequence.

The final assembler cannot choose only favorable attempts.

Observation entries have contiguous sequence numbers.

A gap is `OBSERVATION_SEQUENCE_GAP -> BLOCK`.

Activation Binding binds the final journal head and entry count, preventing unnoticed substitution with a newly assembled observation sequence without changing activation identity.

## 47. Exceptions

Any governance exception MUST be:

- pre-existing before the governed action;
- committed as a control input;
- bounded in scope;
- bound to exact candidate/control identity;
- bound to exact gate or rule being excepted;
- bound to a terminal condition;
- authorized under the applicable governance procedure.

Merge first, reason later is non-compliant.

A post-hoc exception cannot retroactively make an unauthorized action compliant.

## 48. Review staleness

Any identity-changing modification invalidates relevant review:

- new commit;
- amend;
- rebase;
- squash;
- conflict resolution;
- base change;
- head change;
- diff/tree change;
- classifier spec change;
- classifier implementation change;
- manifest change;
- schema change;
- analyzer config/toolchain change;
- analyzer-limits change;
- expectation/transition identity change.

No "small change", "typo", or materiality exception exists in V1.

## 49. Bootstrap before classifier deployment

Before classifier deployment:

- `CLASSIFIER_DEPLOYED = FALSE`;
- `ORDINARY_MERGE_AUTHORITY = NONE`.

Step-3 control-plane work uses the existing T1 temporary bootstrap review procedure.

The first classifier implementation cannot self-classify.

Candidate classifier changes are governed by predecessor/frozen authority, never candidate authority.

## 50. Implementation-freeze self-protection condition

This is mandatory for M-4.

Before `IMPLEMENTATION_FREEZE` can be declared, a successor protected-surface manifest MUST enumerate or prefix-cover the exact implementation locations for at least:

- classifier;
- governance sentinel;
- merge gate;
- privileged classification verifier;
- privileged integration workflow/driver;
- evidence writer/verifier implementation;
- transition resolver/journal verifier;
- implementation configuration files.

The implementation-freeze machine check MUST prove that each implementation control path is covered by an active governance-control exact path or prefix under the predecessor-authorized manifest transition.

If any implementation authority file is unprotected:

`IMPLEMENTATION_CONTROL_PATH_UNPROTECTED -> IMPLEMENTATION_FREEZE_BLOCKED`.

No implementation may rely on path secrecy or developer convention for self-protection.

## 51. UX_ONLY initial reachability condition

This is the explicit M-2 disposition.

At initial `SPEC_FREEZE`, `presentation_roots` and `read_only_adapter_modules` are both empty.

Therefore:

`UX_ONLY_REACHABLE = FALSE`.

This is an intentional conservative bootstrap state.

An implementation test MUST prove that all candidates that would otherwise appear presentation-only fail UX eligibility and receive `CROSS_BOUNDARY` while both boundary lists are empty.

A future non-empty presentation boundary requires a `GOVERNANCE_AMENDMENT`, manifest identity change, stale invalidation, and appropriate implementation tests before `UX_ONLY_REACHABLE` can become true.

## 52. Freeze disposition

### SPEC_FREEZE

`SPEC_FREEZE` freezes the exact six static artifacts in Section 2.

It does not authorize ordinary merge-gate operation.

### IMPLEMENTATION_FREEZE

`IMPLEMENTATION_FREEZE` is later and separately identity-bound.

It requires implementation code, implementation paths, toolchain identity, machine tests, implementation review, and the self-protection condition in Section 50.

Until then:

- `MERGE_GATE_PASS = IMPOSSIBLE`;
- repository enforcement remains false.

### Repository enforcement activation

Repository-required gate/ruleset activation is a further separate `GOVERNANCE_AMENDMENT`.

## 53. Failure-state destinations

Named V1 outcomes have these destinations:

- `CANDIDATE_RELATION_FAILURE` -> BLOCK
- `CLASSIFICATION_SCHEMA_VIOLATION` -> CLASSIFIER_FAILURE -> BLOCK
- `CLASSIFIER_FAILURE` -> BLOCK
- `CLASSIFICATION_RECORD_PRIVILEGE_BOUNDARY_VALIDATION_FAILURE` -> CLASSIFIER_FAILURE -> BLOCK
- `EXPECTATION_SCAN_INCOMPLETE` -> BLOCK
- `REPOSITORY_SCOPE_OBSERVATION_FAILURE` -> BLOCK
- `REPOSITORY_SCOPE_ASSUMPTION_INVALIDATED` -> BLOCK + governance amendment/refoundation
- `NORMAL_OBSERVATION_BLOCKED` -> read-only normal re-verification permitted, mutation/integration blocked
- `TRANSITION_OBSERVATION_BLOCKED` -> named governance disposition required
- `SETTLED_MISMATCH` in normal state -> control-plane drift -> CONTROL_PLANE_COMPROMISED
- `AUTHORIZED_TRANSITION_STATE_MISMATCH` -> CONTROL_PLANE_COMPROMISED
- unresolved mutation outcome -> CONTROL_PLANE_COMPROMISED
- orphaned transition resource -> CONTROL_PLANE_COMPROMISED
- chain fork -> BLOCK
- orphan activation -> INVALID/BLOCK
- implementation control path unprotected -> IMPLEMENTATION_FREEZE_BLOCKED
- unknown observation field -> applicable observation failure/block; if mutation outcome unknown -> CONTROL_PLANE_COMPROMISED
- resource/record/parser limit exceeded -> CLASSIFIER_FAILURE -> BLOCK

Unknown/unresolved/error/missing/stale/unbound/untrusted is never PASS.

## 54. Finding register

This register is normative coverage metadata, not independent proof of correctness.

### B findings

- B-1 Protected Surface Manifest -> Sections 2, 6, 8-10, static manifest
- B-2 Capability closure -> Sections 10-11
- B-3 Sentinel self-protection / anti-shrink -> Sections 3, 6, 50
- B-4 Governance precedence vs gate union -> Sections 6-7, 20
- B-5 Classification Record -> Sections 14-18 plus frozen `CLASSIFICATION_RECORD_SCHEMA_V1`
- B-6 Ambiguity vs classifier failure -> Section 7

### C findings

- C-1 Reverse reachability -> Section 10
- C-2 Merge-gate/ruleset bypass architecture -> Sections 23-24, 42
- C-3 Non-recursive record persistence -> Sections 17-18

### D findings

- D-1 Admin mutability / false prevention claim -> Sections 23-24, 43
- D-2 Step-2 expectation collision -> Sections 25-30, 42
- D-3 Trusted record re-derivation -> Sections 17, 21

### E findings

- E-1 Control-plane expectation lifecycle -> Sections 25-30, 42
- E-2 Candidate execution by verifier -> Sections 12-13, 44
- E-3 Rejected canonical-record pollution -> Section 17

### F findings

- F-1 Precommit vs server-assigned binding -> Sections 26-27, 39
- F-2 Transition self-deadlock -> Sections 33-40
- F-3 Genesis root / scan scope -> Sections 1, 28-29

### G findings

- G-1 Recovery laundering -> Sections 35-41; recovery removed
- G-2 Composite identity ambiguity/forks -> Sections 1, 27-29
- G-3 Derived/provisional server state -> Sections 26-27, 39

### H findings

- H-1 Open-world control-plane acceptance -> Sections 30-32
- H-2 Settling contradiction -> Sections 33-35
- H-3 Genesis/fork instability -> Sections 1, 28-29

### I findings

- I-1 Fail-stop exit + unknown vs compromised -> Sections 35-41
- I-2 Unknown observation fields -> Section 32

### J findings

- J-1 PROVEN_INERT had no effect -> Section 11; removed from V1
- J-2 Unknown vs ambiguous contradiction -> Section 7
- J-3 Observation cap unit regression -> Sections 34-35
- J-4 Hostile-R privilege-boundary validation -> Section 16

### K findings

- K-1 Reference-scan surface lost during consolidation -> Section 10
- K-2 Observation-blocked name had two meanings -> Sections 35-36
- K-3 Failure naming/schema precedence/register maintenance -> Sections 16, 53-54

### L findings

- L-1 Abandoned Intent successor-slot deadlock -> Sections 28, 35-36
- L-2 Machine-readable record schema missing -> Sections 2, 16 and frozen schema artifact
- L-3 Repository full_name unstable -> Section 31
- L-4 Unsupported-but-readable reference consumer missing -> Section 10
- L minor .gitattributes byte-policy protection -> static manifest + Section 6
- L minor two freeze phases -> Sections 3, 50, 52

### M dispositions folded before exact-byte audit

- M-2 UX_ONLY initially unreachable -> Sections 8.4 and 51
- M-3 Manifest category-to-class and module/symbol matching semantics -> Sections 8-10
- M-4 Implementation paths absent at SPEC_FREEZE -> Sections 3 and 50
- M minor record-limit/cardinality consistency -> Section 13 + updated limits/schema
- M minor `failure_state = NONE` rationale -> Sections 7 and 14

## 55. Final non-claims and Owner boundary

This exact-byte candidate does not freeze itself merely by existing.

Freeze requires Owner authorization of the exact package identity after byte-level re-derivation.

Until that authorization:

- `SPEC_FREEZE = CANDIDATE_ONLY`;
- Codex implementation remains prohibited.

After Owner authorization of exact `SPEC_FREEZE` identity:

- specification implementation work may begin;
- ordinary classifier/gate operation remains prohibited until `IMPLEMENTATION_FREEZE`;
- repository enforcement remains prohibited until its later governance amendment.

Evidence remains stronger than AI consensus. No AI participant may self-certify machine facts it did not establish.

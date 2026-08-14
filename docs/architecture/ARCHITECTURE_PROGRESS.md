# MES Quant Engine — Architecture Progress

**Architecture baseline:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2`

**Architecture status:** `BASELINE_ACCEPTED / DESIGN_CLOSED`

**Execution status:** `RESEARCH_ONLY / LIVE_DISABLED`

**Current project stage:** `A6 — Target-Blind Redundancy / Stage B`

**Current milestone:** `STAGE_B_REDUNDANCY_V1.2`

**Current gate:** `ISSUE #13 LOCK CANDIDATE — independent review and accepted merge required`

> This file is the project-level progress source of truth. It tracks **where we are**. Detailed mathematical/methodological authority remains in the applicable stage contract; the target architecture explains **where we are going**.

> The `LOCKED` A6 state proposed in this Draft branch becomes mainline project authority only through independent acceptance and an explicitly authorized merge. Draft/branch state alone does not advance A6 or begin the next research stage.

---

## Status vocabulary

Use these states; do not use a fake project-completion percentage.

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_AUDIT`
- `LOCKED`
- `DEFERRED`
- `REJECTED`

---

## Current position

```text
Architecture:       v2.2 — BASELINE_ACCEPTED / DESIGN_CLOSED
Current plane:      PLANE A — RESEARCH / OFFLINE
Current stage:      A6 — Target-Blind Redundancy
Current policy:     Stage B Redundancy V1.2 — LOCKED, effective on main only through accepted merge
Policy controls:    Python / Markdown / semantic registry — LOCKED
Stage-B artifact execution: DISABLED / gate fails before artifact I/O
BL-30:              CLOSED / ACCEPT_GENESIS_ATTESTATION / EXACT_BYTES
Issue #9 breakers:  REMEDIATED / independently reviewed / Issue #9 CLOSED
Remediation merge:  e16bb5a432bcc98052b6a19167c396af0167ba86
Final audit:        COMPLETE / independently accepted / SAFE_TO_LOCK_V1_2
PR #14 lock:        CLOSED / unmerged / NOT ACCEPTED / supplies no lock authority
Issue #15:          COMPLETE / independently accepted / PR #16 merged as bd6611b040ee94b8c73f800d4d157eec3bf9cf0a
Current breaker:    NONE / V1_2_LOCK_BREAKER_5 remediated by independent policy/execution authority
Issue #13 lock:     CANDIDATE COMPLETE / independent review and accepted merge required
Current action:     independent review; only after accepted merge begin LABEL_EXPOSURE_PRE_FIREWALL acknowledgment
Live trading:       DISABLED
Final Test:         SEALED
```

### BL-30 accepted evidence

- Independent disposition: `ACCEPT_GENESIS_ATTESTATION`
- Classification: `EXACT_BYTES`
- Machine-readable evidence SHA-256: `20f4e2150e5ad49ef4e75b576b4e9b859a6aa3979764f2f80bbbc70d76eca29a`
- Frozen Cell 14 feature artifact SHA-256: `aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452`
- Two clean-process reproductions: byte-identical to frozen reference and to each other
- Exact mismatches: `0`
- Max absolute / relative / ULP deviation: `0`
- Required upstream provenance hashes: all matched
- No new acceptance tolerance introduced

Audit records:

- `docs/audits/BL30_GENESIS_REPRODUCTION_AUDIT_SUMMARY.md`
- `docs/audits/BL30_INDEPENDENT_ATTESTATION.md`

BL-30 acceptance closes the genesis reproduction blocker only. It does **not** by itself lock Stage B V1.2.

### Final-audit lock-breaker and remediation

The one final V1.2 integration / contradiction / preservation audit started at baseline:

`a5d3f40e7edc26d950010401654ce4d6b7822e86`

It stopped under its predefined STOP rule after proving a contradiction between:

```text
Frozen V1.2 architecture:
GENERIC SVD / RANK DISCOVERY -> NEVER DIRECT DROP
```

and the then-current Stage-B V1.1 contract/test authority, which still required generic automatic exact-rank deletion of `k-r` dimensions through retention-priority basis selection.

Minimal reproducer:

```text
stable unexplained exact dependency {a,b,c}
c = a + b

V1.2 frozen methodology -> OPEN whole component; no generic direct DROP
V1.1 contract/test       -> DROP c via exact-basis reduction
```

The finding was classified as:

- `V1_2_LOCK_BREAKER_4` — KEEP / DROP / OPEN / HARD_FAIL could differ from the frozen methodology.
- `V1_2_LOCK_BREAKER_5` — one compliant implementation/run could not satisfy both requirements simultaneously.

Issue #9 performed the bounded remediation only. Independent review accepted the remediation with verdict:

`LOCK_BREAKER_4_5_REMEDIATED`

PR #11 was merged to `main` as:

`e16bb5a432bcc98052b6a19167c396af0167ba86`

The remediation preserved Phase-A semantic KEEP/DROP authority while removing generic Phase-B SVD/rank direct-DROP authority. At the Issue #9 remediation merge, Stage B V1.2 remained `PROVISIONAL`, and `run_stage_b()` remained fail-closed before unimplemented Phase B execution.

The resumed Issue #8 final audit completed and was independently accepted with `SAFE_TO_LOCK_V1_2`. Draft PR #14 then attempted the separate Issue #13 mechanical lock; independent review of Draft PR #14 proved a new `V1_2_LOCK_BREAKER_5`: one Python status field simultaneously represented policy lock and execution eligibility. PR #14 is closed and unmerged; its lock candidate is not accepted and supplies no A6 `LOCKED` authority. Its exact archived Issue #8 report is preserved as evidence without reinterpretation.

Issue #15 introduced distinct machine-authoritative policy and execution fields and a conjunctive pre-I/O gate. Independent review accepted that bounded remediation, and PR #16 merged it to `main` as `bd6611b040ee94b8c73f800d4d157eec3bf9cf0a`.

The resumed Issue #13 candidate performs only the mechanical policy lock under that accepted model. Python, Markdown, and semantic-registry policy states are `LOCKED`; artifact execution remains independently `DISABLED`, so policy lock alone stops before path resolution or control/artifact I/O. The lock candidate does not implement or run Phase B/C/D. Its A6 `LOCKED` status becomes mainline authority only if independent review accepts this new Draft PR and an explicitly authorized merge occurs.

Audit/remediation records:

- `docs/audits/STAGE_B_V1_2_FINAL_AUDIT_LOCK_BREAKER.md`
- `docs/audits/V1_2_LOCK_BREAKER_REMEDIATION_SCOPE.md`
- `docs/audits/STAGE_B_V1_2_LOCK_BREAKER_4_5_REMEDIATION.md`
- `docs/audits/STAGE_B_V1_2_FINAL_INTEGRATION_AUDIT.md`
- `docs/audits/STAGE_B_V1_2_LOCK_BREAKER_5_POLICY_EXECUTION_SEPARATION_REMEDIATION.md`
- `docs/audits/STAGE_B_V1_2_LOCK_RECORD.md`
- GitHub Issue #8 — final integration audit complete / independently accepted
- GitHub Issue #9 — bounded remediation, completed
- GitHub Issue #15 — bounded policy/execution separation remediation
- PR #16 — Issue #15 remediation accepted and merged as `bd6611b040ee94b8c73f800d4d157eec3bf9cf0a`
- Draft PR #14 — closed and unmerged; independent disposition `V1_2_LOCK_CANDIDATE_NOT_ACCEPTED`
- GitHub Issue #13 — resumed mechanical lock candidate from post-Issue-15 `main`

---

## Architecture-stage tracker

| Stage | Scope | Status | Evidence / current position | Exit gate / next action |
|---|---|---|---|---|
| Plane 0 | Governance & provenance foundation | IN_PROGRESS | Stage-B governance, provenance, target firewall and audit discipline are substantially developed; system-wide governance is not yet complete | Continue only as required by active stage; do not build institutional layers ahead of Edge Sprint |
| A1 | Data Foundation | LOCKED | Canonical MES historical data, PIT controls, gap/roll/session audits established | Reopen only for documented defect/version bump |
| A2 | Decision Universe | LOCKED | Eligibility, session, early-close, horizon-safe and decision-universe logic established | Reopen only for documented defect/version bump |
| A3 | Cost & Impact Model | DEFERRED | Cost assumptions exist historically but the v2.2 single-source canonical cost contract is not yet formalized | Define only to the level required for Edge Sprint protocol; do not build full production cost stack first |
| A4 | Label / Target Contract | IN_PROGRESS | Historical label logic exists; v2.2 separates target contract from realized-label access | Before Edge Sprint, record pre-firewall exposure and freeze sprint target/cost assumptions |
| A5 | Feature Construction | LOCKED | Canonical Cell 14 V1 feature build: 29 candidate features, PIT-safe Development output; BL-30 independently reproduced exact bytes | Reopen only for documented defect/version bump |
| **A6** | **Target-Blind Redundancy / Stage B** | **LOCKED** | Post-merge state proposed by the new Issue #13 Draft candidate: Issue #8 final audit accepted; Issue #9 methodology preserved; Issue #15 separation accepted in PR #16; policy controls locked in `bb68e6d8be9244564c2d06179cffde775041c8f3`; execution remains disabled. This `LOCKED` state is effective on `main` only through independent acceptance and explicitly authorized merge of this candidate | **Before merge: independent review only. After accepted merge: reopen only for documented defect/version bump; policy lock does not mean Phase B/C/D execution is complete or enabled** |
| A7 | Regime / Context | DEFERRED | Not required before first Edge Sprint | Do not build before Edge Sprint evidence justifies continuation |
| A8 | Label Materialization / access control | IN_PROGRESS | Historical labels exist; new L0/L1/L2/L3 governance not yet formalized | Create `LABEL_EXPOSURE_PRE_FIREWALL` acknowledgment; enforce access levels before Sprint/Validation |
| Exploratory Lane | TRAIN-only edge discovery | NOT_STARTED | One-page charter design closed | Freeze one-page charter + Sprint 1 protocol only after A6 lock |
| A9 | Predictive Model Layer | NOT_STARTED | Intentionally not built ahead of edge evidence | Start confirmatory model work only after Sprint produces a lockable hypothesis |
| A10 | Validation & Model Selection | NOT_STARTED | Validation must remain clean during L1 exploration | Before first L2 opening, freeze validation protocol and opening budget |
| A11 | Calibration | NOT_STARTED | Global calibration baseline / regime challenger architecture defined only | Build after predictive hypothesis survives validation path |
| A12 | Net EV | NOT_STARTED | Architecture defined only | Build after model/calibration/cost evidence exists |
| A13 | Risk & Sizing Simulation | NOT_STARTED | Architecture defined only | Build after edge survives confirmatory research |
| A14 | Execution Simulation / Parity | NOT_STARTED | Architecture defined only | Required before production promotion |
| Release Gate | Research -> production promotion | NOT_STARTED | Gate categories defined in v2.2 | Implement only when a release candidate exists |
| Plane B | Production / Online | NOT_STARTED | Live trading disabled | No production build/promotion before Release Gate evidence |
| Plane C | Feedback & Control | NOT_STARTED | Architecture defined only | Build with production readiness, not before edge evidence |
| Watchdog | Independent safety process | NOT_STARTED | Required before meaningful live trading | Implement/test before live enablement |

---

## Current A6 / Stage-B exit gate

V1.2 methodology convergence is complete. The mechanical lock candidate remains subject to independent review and accepted merge:

```text
BL-30 reproduction evidence                    COMPLETE
-> independent BL-30 audit                     COMPLETE / ACCEPT
-> ONE final integration / contradiction /
   preservation audit                          STARTED
   -> V1_2_LOCK_BREAKER_4 + 5                  PROVEN / STOP
-> bounded breaker remediation                 COMPLETE
-> independent remediation review              COMPLETE / ACCEPT
-> PR #11 remediation merge                    COMPLETE
-> resume the SAME final audit (Issue #8)      COMPLETE / ACCEPT
-> Issue #13 mechanical lock / Draft PR #14    ATTEMPTED
   -> V1_2_LOCK_BREAKER_5 policy/execution     PROVEN / STOP
-> PR #14                                      CLOSED / UNMERGED / NOT ACCEPTED
-> Issue #15 bounded separation remediation    COMPLETE / ACCEPT
-> PR #16 remediation merge                    COMPLETE / bd6611b040ee94b8c73f800d4d157eec3bf9cf0a
-> resume the SAME Issue #13 from new main     COMPLETE
-> mechanical policy-lock candidate            COMPLETE
   -> policy status                             LOCKED
   -> artifact execution                       DISABLED / PRE-I/O STOP
-> independent review + explicit merge         CURRENT GATE
-> A6 LOCKED on main                           EFFECTIVE ONLY AFTER ACCEPTED MERGE
-> LABEL_EXPOSURE_PRE_FIREWALL acknowledgment  NEXT GATE
```

This sequence does **not** reopen architecture design and does not create an unlimited new audit cycle. The Issue #8 audit result remains accepted. Issue #15 removed the policy/execution coupling, and the resumed Issue #13 uses that accepted machine model. The Draft candidate itself grants no mainline lock or next-stage authority before independent acceptance and an explicitly authorized merge.

V1.2 may be blocked only by a predefined `V1_2_LOCK_BREAKER`:

1. authoritative Phase-B mathematical result can be wrong;
2. feature/member identity can make Phase B analyze the wrong ground set;
3. target/Validation/Final-Test information can influence a target-blind result;
4. KEEP/DROP/OPEN/HARD_FAIL can differ from the frozen methodology;
5. two locked requirements cannot be satisfied simultaneously by one compliant implementation/run.

Everything else goes to V1.3 backlog.

---

## Frozen next sequence after accepted A6 lock merge

```text
1. Record LABEL_EXPOSURE_PRE_FIREWALL acknowledgment
2. Freeze Exploratory Lane V1 one-page charter
3. Freeze Edge Discovery Sprint 1 protocol:
   - EXPLORATION_SCOPE_ID
   - project continuation policy
   - baseline(s), including ALWAYS_FLAT
   - one primary decision metric
   - diagnostic secondary metrics
   - cost assumption
   - interesting-enough continuation criterion
4. RUN EDGE DISCOVERY SPRINT 1
```

None of this sequence begins in the lock-candidate PR. Independent acceptance and an explicitly authorized merge are the mandatory precondition.

Do **not** build the remaining institutional contracts merely because they appear in the target architecture. Sprint 1 remains the next major business/research proof point after A6.

---

## Label-access roadmap

| Level | Access | Project use |
|---|---|---|
| L0 | target contract only; no realized labels | current Stage B / target-blind governance |
| L1 | TRAIN labels | Exploratory Lane / model fitting |
| L2 | Validation labels/results | frozen confirmatory protocol; budgeted openings |
| L3 | Final Test | sealed one-time final confirmation |

Work classification is derived from observed access. Human labels cannot downgrade an L1/L2/L3 run into governance work.

---

## Evidence discipline

Progress status is evidence-based:

- `BLOCKED` means a predefined gate failure is proven and must be remediated before advancement.
- `READY_FOR_AUDIT` means the required remediation/build work is complete but the next independent/final acceptance gate has not yet completed.
- `LOCKED` means the applicable exit gate has passed and the versioned authority is frozen.
- A local result or chat statement alone is not enough to mark a stage `LOCKED`.

When a milestone changes, update this file in the same PR/commit series that supplies the corresponding evidence or policy transition whenever practical.

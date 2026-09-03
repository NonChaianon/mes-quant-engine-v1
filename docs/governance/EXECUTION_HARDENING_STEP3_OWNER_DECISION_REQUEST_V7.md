# MES Execution Hardening Step 3 — Owner Decision Request V7

Request ID: `REQUEST_EXECUTION_HARDENING_STEP3_V7_20260826`

Status: **DRAFT REQUEST / FRESH REVIEW REQUIRED / NO AUTHORITY**

Package:

- ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V7`
- literal path:
  `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V7.md`
- SHA-256:
  `7a4cf9d2b0224e282dc0ad1fdd25b4f236b1971dc99ff5f869d2a955a065e3f2`

Preparation base:

- commit `ae3048cc8a58d8eec7cc42f99146c91e579d6582`
- tree `4f7aa3a719dcd781411d91166de82a4d4ffa573f`

Current authority permits only additive docs/config preparation and one fresh review. This request
is not an Owner statement and grants no closeout, staging, commit, push, code, implementation, CI,
PR, issue, merge, ruleset, `main` mutation, Decision B/C, Phase A/B, Tier 2, OIDC/signing, data,
target/path access, fit, Validation, Final Test, Test 3 retry, Test 3b, Test 4, or scientific
authority.

## 1. Exact governing companions

| Role | Literal repository path | SHA-256 |
| --- | --- | --- |
| `SURFACE_MAP_V5` | `configs/governance/rehearsal_surface_map_v5.json` | `87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a` |
| `TRANSITION_ROWS_V3` | `configs/governance/execution_hardening_transition_rows_v3.json` | `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1` |
| `TIME_POLICY_V1` | `configs/governance/execution_hardening_time_policy_v1.json` | `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e` |
| `PRODUCTION_SURFACE_V2` | `configs/governance/execution_hardening_production_surface_manifest_v2.json` | `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a` |

Surface Map V5 remains byte-identical. V7 changes no implementation surface, transition rule,
time policy, production surface, code, or CI.

## 2. V6 stopped-chain disposition

V6 review evidence remains:

- literal path:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_RESPONSE.md`
- SHA-256:
  `00641b38145993e8d3e1890bf60398358e6caa120f73b62faaba410314f007eb`
- result: `GO / BLOCKER=0 / HIGH=0 / LOW=2 / UNTRUSTED_CONTEXT_ONLY`.

V6 package anchoring is independently `NO_GO / BLOCKER=0 / HIGH=1` because the prior Owner
statement omitted five literal paths. No V6 stage, commit, push, or remote ref occurred.

The following exact artifacts are immutable and non-operative:

| Role | Literal repository path | SHA-256 | Required status |
| --- | --- | --- | --- |
| `INVALID_V6_OWNER_CLOSEOUT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md` | `c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58` | `STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED` |
| `INVALID_V6_CLOSEOUT_RECEIPT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md` | `a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42` | `STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED` |
| `INVALID_V6_EXTERNAL_MANIFEST` | `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json` | `f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff` | `STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED` |

They may not be repaired, supplemented, adopted, deleted, reused, or interpreted as authority.

## 3. Fresh Attempt 007

V7 requires one fresh `FULL_GOVERNED` review:

- Packet:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007.md`
- Dispatch Receipt:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_DISPATCH_RECEIPT.md`
- Response:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md`
- attempt ordinal: `1`
- authorized attempts: `1`
- retry against unchanged V7 bytes: `FORBIDDEN`
- fallback reviewer: `NOT_AUTHORIZED`.

The response deadline is exactly twenty minutes after dispatch. Timeout, `NO_VERDICT`, invalid
artifact, BLOCKER, or HIGH stops V7 and creates no retry. Review evidence is
`UNTRUSTED_CONTEXT_ONLY` and never Owner authority.

## 4. Closed future Owner binding set

A future Decision A Owner statement is valid only if it contains exactly one block delimited by
the literal LF-terminated sentinel lines `OWNER_BINDING_TSV_V1_BEGIN` and
`OWNER_BINDING_TSV_V1_END`. Between them it must enumerate every required row as the complete
ordered tuple:

```text
ordinal<TAB>role<TAB>literal_repo_relative_path<TAB>full_lowercase_64_hex_sha256<LF>
```

Every path must be literal and every hash must recompute against that path. Artifact label,
basename, version shorthand, `above`/`below`, Section reference, packet table, transitive
reference, inferred mapping, preparer table, or hash without its literal path is invalid.

The future terminal reviewed state has exactly twenty-two required Owner binding paths:

| # | Role | Required literal repository path | Hash source |
| ---: | --- | --- | --- |
| 1 | `SURFACE_MAP_V5` | `configs/governance/rehearsal_surface_map_v5.json` | exact hash in Section 1 |
| 2 | `TRANSITION_ROWS_V3` | `configs/governance/execution_hardening_transition_rows_v3.json` | exact hash in Section 1 |
| 3 | `TIME_POLICY_V1` | `configs/governance/execution_hardening_time_policy_v1.json` | exact hash in Section 1 |
| 4 | `PRODUCTION_SURFACE_V2` | `configs/governance/execution_hardening_production_surface_manifest_v2.json` | exact hash in Section 1 |
| 5 | `PACKAGE_V5` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V5.md` | `3c63a4b3e18aeaee29512954d7d04d99020fe9190d47d539ade67ab06ff28916` |
| 6 | `PACKAGE_V6` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V6.md` | `109dd22a63c0fd36a02acfc6652245e11188005e44aacf3d8d3b2780d7ee377e` |
| 7 | `REQUEST_V5` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V5.md` | `7d1693a8e7882e6cd411f56be076617a11072733dc49587f20dbdb0d210bfbed` |
| 8 | `REQUEST_V6` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V6.md` | `c5313435c2301ef35a431baf2ec3f2f52d361b15e44b3f2f27e5d3f16fee166a` |
| 9 | `PACKET_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005.md` | `808f4b21dcd09200f29fb3434b4948d7eec94474f29a89bfb60575cdd1c7bd98` |
| 10 | `DISPATCH_RECEIPT_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005_DISPATCH_RECEIPT.md` | `5d1bf9802be5a6b66dc0e330661ecf1d8d783443ae94d60a63966f277f0cf7c4` |
| 11 | `RESPONSE_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005_RESPONSE.md` | `6cf62c251c6a4a78f66717e705988e98275b9e1f6ace6d2e84cc117eb24c6471` |
| 12 | `PACKET_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006.md` | `8527385010fa8b544f6384ac7a88b9bcdd0ac9b3b5cea168242b9b554e4bd56e` |
| 13 | `DISPATCH_RECEIPT_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_DISPATCH_RECEIPT.md` | `c851cbbbca8d189c4cf7f9e04ea9b6932f11cc5da3630645315ac973323eb9ac` |
| 14 | `RESPONSE_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_RESPONSE.md` | `00641b38145993e8d3e1890bf60398358e6caa120f73b62faaba410314f007eb` |
| 15 | `INVALID_V6_OWNER_CLOSEOUT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md` | `c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58` |
| 16 | `INVALID_V6_CLOSEOUT_RECEIPT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md` | `a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42` |
| 17 | `INVALID_V6_EXTERNAL_MANIFEST` | `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json` | `f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff` |
| 18 | `PACKAGE_V7` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V7.md` | `7a4cf9d2b0224e282dc0ad1fdd25b4f236b1971dc99ff5f869d2a955a065e3f2` |
| 19 | `REQUEST_V7` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V7.md` | recompute after this request is frozen |
| 20 | `PACKET_007` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007.md` | recompute after packet freeze |
| 21 | `DISPATCH_RECEIPT_007` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_DISPATCH_RECEIPT.md` | recompute after receipt freeze |
| 22 | `RESPONSE_007` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md` | recompute after response seal |

The future Owner statement must enumerate all twenty-two rows literally with complete hashes. It
cannot refer back to this table instead of repeating them.

Before any Owner closeout, a mechanical verifier must establish equality over the complete
ordered `(ordinal, role, literal_repo_relative_path, sha256)` rows, not merely over paths:

```text
required_owner_binding_row_count = 22
actual_owner_binding_row_count = 22
required_owner_binding_rows == actual_owner_binding_rows
duplicate_role_count = 0
duplicate_path_count = 0
missing_role_count = 0
extra_role_count = 0
missing_path_count = 0
extra_path_count = 0
role_path_sha_mismatch_count = 0
abbreviated_hash_count = 0
OWNER_LITERAL_PATH_BINDING_SET_EXACT_PASS
```

The Owner block is UTF-8 with no BOM. `ordinal` is decimal `1` through `22` with no leading zero;
fields use exactly one horizontal-tab byte (`0x09`); paths use `/`; hashes are lowercase 64-hex;
every row including the final row ends with exactly one LF byte (`0x0a`). The row bytes contain no
Markdown fence, header, blank line, CR, quoting, escaping, surrounding whitespace, or extra byte.
The sentinels are excluded from the hashed row bytes. Immediately after the end sentinel, the
Owner statement must state `OWNER_BINDING_TSV_V1_SHA256=<lowercase full 64-hex>` on its own
LF-terminated line. The verifier independently materializes
the required rows from the frozen artifacts and records `required_binding_rows_sha256`, extracts
exactly one Owner block and records `actual_binding_rows_sha256`, and requires both digests and
the Owner-stated digest to be equal.

The Owner statement must also contain exactly one block delimited by the literal LF-terminated
sentinel lines `INVALID_V6_DISPOSITION_TSV_V1_BEGIN` and
`INVALID_V6_DISPOSITION_TSV_V1_END`, with these three exact rows in ordinal order:

```text
15<TAB>INVALID_V6_OWNER_CLOSEOUT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md<TAB>c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58<TAB>STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED<LF>
16<TAB>INVALID_V6_CLOSEOUT_RECEIPT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md<TAB>a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42<TAB>STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED<LF>
17<TAB>INVALID_V6_EXTERNAL_MANIFEST<TAB>docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json<TAB>f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff<TAB>STOPPED / INVALID_OWNER_PATH_BINDING / NO_AUTHORITY / NOT_ADOPTED<LF>
```

`<TAB>` and `<LF>` denote literal bytes `0x09` and `0x0a`, not angle-bracket text. This block has
the same UTF-8/no-BOM/LF-only/no-fence/no-header/no-blank-line rules. Its sentinels are excluded
from the hashed row bytes. Immediately after its end sentinel, the Owner statement must state
`INVALID_V6_DISPOSITION_TSV_V1_SHA256=<lowercase full 64-hex>` on its own LF-terminated line. The
verifier must establish:

```text
invalid_v6_disposition_exact_pass = 1
invalid_v6_adopted_count = 0
invalid_v6_authority_count = 0
```

The closeout must record the two required/actual Owner-row digests, both disposition-block
digests, every counter, and both PASS results. Failure stops before closeout. No supplement,
commit message, or later artifact may cure it.

## 5. Unique future V7 chain

Only a future path-complete Owner statement issued after a timely clean Response 007 may name:

1. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_OWNER_CLOSEOUT.md`
2. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_CLOSEOUT_RECEIPT.md`
3. `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V7_CLOSEOUT_MANIFEST_V1.json`.

It may name those three future paths but must not bind their not-yet-existing hashes.

The sole active future anchor is
`docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V7_CLOSEOUT_MANIFEST_V1.json`.
The sole future target ref is
`refs/heads/governance/execution-hardening-step3-package-v7`.

The mandatory order is:

```text
Packet 007 -> Dispatch Receipt 007 -> Response 007
-> path-complete Owner statement
-> OWNER_LITERAL_PATH_BINDING_SET_EXACT_PASS
-> Owner Closeout 007 -> Closeout Receipt 007
-> V7 external manifest
-> one direct-child commit -> one non-force push
```

## 6. Exact path and commit arithmetic

```text
current immutable additive history                       14
+ Package V7 + Request V7                                2
= Packet 007 preparation state                           16
+ Packet 007 + Dispatch Receipt 007 + Response 007       3
= terminal reviewed state                                19
+ future Owner Closeout 007 + Closeout Receipt 007
  + V7 external manifest                                 3
= future package-anchoring commit                        22
```

The two twenty-two-path sets in this request are intentionally different and must never be
asserted equal:

- Owner binding set (`22`) = terminal nineteen additions plus the three tracked governing
  companions `TRANSITION_ROWS_V3`, `TIME_POLICY_V1`, and `PRODUCTION_SURFACE_V2`;
- future commit-addition set (`22`) = terminal nineteen additions plus future Owner Closeout 007,
  Closeout Receipt 007, and the V7 external manifest.

Any future external manifest must freeze the future commit-addition set:

- ordered anchored artifacts excluding itself: `21`
- expected commit paths including itself: `22`
- additions: `22`
- modifications: `0`
- deletions: `0`.

The future commit must have exactly one parent,
`ae3048cc8a58d8eec7cc42f99146c91e579d6582`, and one non-force push may create only
`refs/heads/governance/execution-hardening-step3-package-v7`. V1 remains at the exact base and no
V6 ref may be pushed.

This is a future proposal, not current authority.

## 7. Failure posture and decision boundary

Any missing/extra/duplicate literal path, hash mismatch, abbreviated hash, inferred mapping,
set-equality failure, invalid V6 artifact described as operative, anchor/ref mismatch, path-count
drift, wrong order, retry/fallback expansion, or authority leak is HIGH and stops before closeout.

A clean Attempt 007 makes only V7 package anchoring eligible for separate Owner consideration.
It grants no closeout, commit, push, Decision B/C, Phase A/B, code, implementation, CI, PR,
Issue #48, PR #47, merge, ruleset, `main`, Tier 2, OIDC/signing, data, target/path access, fit,
Validation, Final Test, Test 3 retry, Test 3b, Test 4, or scientific authority.

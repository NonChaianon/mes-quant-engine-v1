# Owner Decision Request — Execution Hardening Step 3 Package V9

Request ID: `MES_EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V9`

Status: **PREPARATION AND FRESH REVIEW ONLY / NO OWNER DECISION REQUESTED YET**

Exact base: commit `ae3048cc8a58d8eec7cc42f99146c91e579d6582`, tree
`4f7aa3a719dcd781411d91166de82a4d4ffa573f`.

Bound V9 artifacts:

- authorization `docs/governance/EXECUTION_HARDENING_STEP3_V9_PREPARATION_AUTHORIZATION_V1.md`
  SHA-256 `6711a8bd7e0373267225a150f11609d66e30b0e1b390d26fdb8f9c7762363491`;
- Package `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V9.md`
  SHA-256 `b7e40c5d9f1f53897b4e1face60f7ff68513f547f12a9ba1d0c4ab4779496b37`.

Response 008 remains immutable at SHA-256
`12605c0f4eea1de88498d4c04446dd6a5febcf448baf6ba55779ec54018d28a2`
with embedded `GO / BLOCKER=0 / HIGH=0 / LOW=2`, but its controlling disposition is
`STOPPED / VERIFICATION_SIDE_INVALIDATION / NO_AUTHORITY`. It is not a clean prerequisite.

## 1. Fresh Attempt 009 only

- packet `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009.md`
- receipt `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_DISPATCH_RECEIPT.md`
- response `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_RESPONSE.md`
- ordinal `1 of 1`; unchanged-byte retry `FORBIDDEN`; fallback `NOT_AUTHORIZED`;
- deadline exactly twenty minutes after dispatch;
- tool requests and executions mechanically audited against the frozen allowlist.

Any out-of-allowlist tool request or execution is `VERIFICATION_SIDE_INVALIDATION`, whether
denied or successful. Timeout, `NO_VERDICT`, invalidation, BLOCKER, or HIGH stops V9.

## 2. Closed future Owner-binding set

A future package-anchoring Owner statement, if separately requested after a conforming Response
009, must itself repeat all thirty-four ordered rows with literal paths and complete hashes.
Reference to this request is not a substitute.

| # | Role | Required literal repository path | Hash source |
| ---: | --- | --- | --- |
| 1 | `SURFACE_MAP_V5` | `configs/governance/rehearsal_surface_map_v5.json` | `87530dac557952256305591f45edf49a5776346af636b5ff4501604136b7162a` |
| 2 | `TRANSITION_ROWS_V3` | `configs/governance/execution_hardening_transition_rows_v3.json` | `00112c1ce1393758ade8ecfc187fd5e49f6220afd8320b417beebc1b5dc683d1` |
| 3 | `TIME_POLICY_V1` | `configs/governance/execution_hardening_time_policy_v1.json` | `e27e38123e35d4aece86ef3299708cec976ff48c25cad8ee38459f0e6eb48b0e` |
| 4 | `PRODUCTION_SURFACE_V2` | `configs/governance/execution_hardening_production_surface_manifest_v2.json` | `3b3a9b63adb61344a9fa573b945ac1d35849caeb7bc245395a0a61db05f4800a` |
| 5 | `PACKAGE_V5` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V5.md` | `3c63a4b3e18aeaee29512954d7d04d99020fe9190d47d539ade67ab06ff28916` |
| 6 | `PACKAGE_V6` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V6.md` | `109dd22a63c0fd36a02acfc6652245e11188005e44aacf3d8d3b2780d7ee377e` |
| 7 | `PACKAGE_V7` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V7.md` | `7a4cf9d2b0224e282dc0ad1fdd25b4f236b1971dc99ff5f869d2a955a065e3f2` |
| 8 | `REQUEST_V5` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V5.md` | `7d1693a8e7882e6cd411f56be076617a11072733dc49587f20dbdb0d210bfbed` |
| 9 | `REQUEST_V6` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V6.md` | `c5313435c2301ef35a431baf2ec3f2f52d361b15e44b3f2f27e5d3f16fee166a` |
| 10 | `REQUEST_V7` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V7.md` | `ae6f1ca52b7c60376186374f644b01551a4000801934446f7f9bd012280c120e` |
| 11 | `INVALID_V6_EXTERNAL_MANIFEST` | `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json` | `f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff` |
| 12 | `PACKET_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005.md` | `808f4b21dcd09200f29fb3434b4948d7eec94474f29a89bfb60575cdd1c7bd98` |
| 13 | `DISPATCH_RECEIPT_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005_DISPATCH_RECEIPT.md` | `5d1bf9802be5a6b66dc0e330661ecf1d8d783443ae94d60a63966f277f0cf7c4` |
| 14 | `RESPONSE_005` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_005_RESPONSE.md` | `6cf62c251c6a4a78f66717e705988e98275b9e1f6ace6d2e84cc117eb24c6471` |
| 15 | `PACKET_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006.md` | `8527385010fa8b544f6384ac7a88b9bcdd0ac9b3b5cea168242b9b554e4bd56e` |
| 16 | `INVALID_V6_CLOSEOUT_RECEIPT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md` | `a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42` |
| 17 | `DISPATCH_RECEIPT_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_DISPATCH_RECEIPT.md` | `c851cbbbca8d189c4cf7f9e04ea9b6932f11cc5da3630645315ac973323eb9ac` |
| 18 | `INVALID_V6_OWNER_CLOSEOUT` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md` | `c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58` |
| 19 | `RESPONSE_006` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_RESPONSE.md` | `00641b38145993e8d3e1890bf60398358e6caa120f73b62faaba410314f007eb` |
| 20 | `PACKET_007` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007.md` | `4bbd96dd926ef9bfb4e150c22307d821b2b91eb7a4d2536eea2f1e49f9c339fb` |
| 21 | `DISPATCH_RECEIPT_007` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_DISPATCH_RECEIPT.md` | `37cb55cf2b7725e4f6959b87725ce84a96ef42b15bdfa87ea7cd655124050c3c` |
| 22 | `RESPONSE_007_STOPPED` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md` | `2ceea25782e0d6ba63150d5629d5adf1a63b7b6909ac4d92b7b9187c67f870ab` |
| 23 | `V8_PREPARATION_AUTHORIZATION` | `docs/governance/EXECUTION_HARDENING_STEP3_V8_PREPARATION_AUTHORIZATION_V1.md` | `ffb148483067f2fa3d243e5829331ea2a1df2f841db93ac33d0eba0cbd1c760f` |
| 24 | `PACKAGE_V8` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V8.md` | `d967eae2862a8e9a2980fb054d1ca8dd567c3f94582e8a7a938c8031cae491e3` |
| 25 | `REQUEST_V8` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V8.md` | `f3b51c7cddae5e438269cc60d1fa38706a4a6bdcae3fc99a97d5724beef7824c` |
| 26 | `PACKET_008` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008.md` | `bf17c0bc3946c05938faa440f1757a0074308f58f55d4e43cc1ae58e19b6ead2` |
| 27 | `DISPATCH_RECEIPT_008` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_DISPATCH_RECEIPT.md` | `caad67eb568acd2b99da2efc1080523aca656f0b1f609a39b7bca2f1d0cf0a43` |
| 28 | `RESPONSE_008_STOPPED` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_RESPONSE.md` | `12605c0f4eea1de88498d4c04446dd6a5febcf448baf6ba55779ec54018d28a2` |
| 29 | `V9_PREPARATION_AUTHORIZATION` | `docs/governance/EXECUTION_HARDENING_STEP3_V9_PREPARATION_AUTHORIZATION_V1.md` | `6711a8bd7e0373267225a150f11609d66e30b0e1b390d26fdb8f9c7762363491` |
| 30 | `PACKAGE_V9` | `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V9.md` | `b7e40c5d9f1f53897b4e1face60f7ff68513f547f12a9ba1d0c4ab4779496b37` |
| 31 | `REQUEST_V9` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V9.md` | recompute after request freeze |
| 32 | `PACKET_009` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009.md` | recompute after packet freeze |
| 33 | `DISPATCH_RECEIPT_009` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_DISPATCH_RECEIPT.md` | recompute after receipt freeze |
| 34 | `RESPONSE_009` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_RESPONSE.md` | recompute after response seal |

Required canonical owner-binding bytes are UTF-8/no BOM, fields
`ordinal<TAB>role<TAB>literal_path<TAB>full_sha256<LF>`, one LF after every row including the
last, no header/fence/CR/blank/quote/escape/extra byte, and unique role/path values. Before any
future closeout the exact 34-row actual and Owner-stated byte streams and SHA-256 values must
match.

## 3. Exact invalid-history disposition gate

The same future Owner statement must contain the exact five-row
`V9_INVALID_HISTORY_DISPOSITION_TSV_V1` block below:

```text
V9_INVALID_HISTORY_DISPOSITION_TSV_V1_BEGIN
11<TAB>INVALID_V6_EXTERNAL_MANIFEST<TAB>docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json<TAB>f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff<TAB>SELF_ASSERTED_DECISION_A_AUTHORITY_AND_APPROVED_OWNER_AUTHORIZATION<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
16<TAB>INVALID_V6_CLOSEOUT_RECEIPT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md<TAB>a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42<TAB>SELF_ASSERTED_APPROVED_DECISION_A_RECEIPT<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
18<TAB>INVALID_V6_OWNER_CLOSEOUT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md<TAB>c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58<TAB>SELF_ASSERTED_APPROVE_AND_AUTHORIZATION_CREATED<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
22<TAB>RESPONSE_007_STOPPED<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md<TAB>2ceea25782e0d6ba63150d5629d5adf1a63b7b6909ac4d92b7b9187c67f870ab<TAB>EMBEDDED_GO_WITH_REVIEW_SEVERITY_NONCONFORMANCE<TAB>STOPPED_REVIEW_SEVERITY_NONCONFORMANCE_NO_AUTHORITY<LF>
28<TAB>RESPONSE_008_STOPPED<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_RESPONSE.md<TAB>12605c0f4eea1de88498d4c04446dd6a5febcf448baf6ba55779ec54018d28a2<TAB>EMBEDDED_GO_WITH_UNAUTHORIZED_GIT_STASH_LIST<TAB>STOPPED_VERIFICATION_SIDE_INVALIDATION_NO_AUTHORITY<LF>
V9_INVALID_HISTORY_DISPOSITION_TSV_V1_END
V9_INVALID_HISTORY_DISPOSITION_TSV_V1_SHA256=2a1fa0f771c1409aa258ea05df325d3f54f531ef4d9c5cd0a94fd5469b435647
```

`<TAB>` and `<LF>` are byte markers as defined in Package V9 Section 4. The block SHA-256 is
`2a1fa0f771c1409aa258ea05df325d3f54f531ef4d9c5cd0a94fd5469b435647`.
Required ordinals are `11,16,18,22,28`. Required and actual rows must be identical; Owner-stated
rows must be identical to both; duplicate/missing/extra counts must be zero.

The highest applicable authority rank controls. Same-rank conflict or non-unique disposition is
BLOCKER. Invalid-history operative adoption is HIGH. Response 008 GO cannot be used as clean
review.

## 4. Possible future V9 chain — not authorized

- Owner Closeout `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_OWNER_CLOSEOUT.md`
- Closeout Receipt `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_009_CLOSEOUT_RECEIPT.md`
- External manifest `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V9_CLOSEOUT_MANIFEST_V1.json`
- ref `refs/heads/governance/execution-hardening-step3-package-v9`

Mandatory order is Response 009, separate path-complete Owner statement, exact 34-row binding
PASS, exact five-row disposition PASS, Owner Closeout 009, Closeout Receipt 009, external
manifest, one direct-child commit, one non-force push. None is currently authorized.

## 5. Decision boundary

A conforming, timely, tool-audited Attempt 009 with `BLOCKER=0 / HIGH=0` makes only V9 package
anchoring eligible for separate Owner consideration. This request is not Owner authority and
does not authorize closeout, staging, commit, push, implementation, CI, or science.

# MES Execution Hardening Step 3 — Owner Decision Request V8

Request ID: `REQUEST_EXECUTION_HARDENING_STEP3_V8_20260826`

Status: **DRAFT REQUEST / FRESH REVIEW REQUIRED / NO AUTHORITY**

Package:

- ID: `MES_EXECUTION_HARDENING_STEP3_PACKAGE_V8`
- literal path:
  `docs/governance/EXECUTION_HARDENING_STEP3_IMPLEMENTATION_PACKAGE_V8.md`
- SHA-256:
  `d967eae2862a8e9a2980fb054d1ca8dd567c3f94582e8a7a938c8031cae491e3`

Owner preparation authorization:

- literal path:
  `docs/governance/EXECUTION_HARDENING_STEP3_V8_PREPARATION_AUTHORIZATION_V1.md`
- SHA-256:
  `ffb148483067f2fa3d243e5829331ea2a1df2f841db93ac33d0eba0cbd1c760f`

Preparation base:

- commit `ae3048cc8a58d8eec7cc42f99146c91e579d6582`
- tree `4f7aa3a719dcd781411d91166de82a4d4ffa573f`

This request is a proposal only. Current authority permits additive docs/config preparation and
one fresh review. It grants no closeout, staging, commit, push, implementation, CI, or scientific
authority.

## 1. Controlling precedence and V7 disposition

Authority-semantic conflicts use this exact order:

1. exact Owner-ratified protocol/template/ratification bytes;
2. exact V8 Owner preparation authorization record bound above;
3. exact V8 review-chain artifacts;
4. anchored valid historical evidence;
5. stopped/invalid historical bytes.

Lower ranks cannot restore authority denied by a higher rank. Conflicting applicable texts at
the same highest rank, a missing tiebreaker, or more than one possible disposition sets
`UNRESOLVED_AUTHORITY_CONFLICT=1` and is BLOCKER.

Response 007 at
`docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md`,
SHA-256 `2ceea25782e0d6ba63150d5629d5adf1a63b7b6909ac4d92b7b9187c67f870ab`,
is immutable `STOPPED / REVIEW_SEVERITY_NONCONFORMANCE / NO_AUTHORITY` history. Its embedded GO
is evidence of the review output, not a clean prerequisite and not authority.

The three invalid V6 artifacts remain byte-identical. Their internal approval/authority strings
are disclosed historical defect evidence, not operative authority. Any V8 artifact that adopts,
activates, relies on, or presents those claims as authority is HIGH.

## 2. Fresh Attempt 008

Required new review paths:

- Packet:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008.md`
- Dispatch Receipt:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_DISPATCH_RECEIPT.md`
- Response:
  `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_RESPONSE.md`
- attempt ordinal `1`;
- authorized attempts `1`;
- unchanged-byte retry `FORBIDDEN`;
- fallback reviewer `NOT_AUTHORIZED`;
- deadline exactly twenty minutes after dispatch.

Review evidence is `UNTRUSTED_CONTEXT_ONLY`. Timeout, `NO_VERDICT`, invalid artifact, BLOCKER, or
HIGH stops V8 and creates no retry.

## 3. Closed future Owner binding set

A future package-anchoring Owner statement is valid only if it contains exactly one canonical
block delimited by LF-terminated sentinel lines `V8_OWNER_BINDING_TSV_V1_BEGIN` and
`V8_OWNER_BINDING_TSV_V1_END`. Between them it must enumerate the complete ordered tuple:

```text
ordinal<TAB>role<TAB>literal_repo_relative_path<TAB>full_lowercase_64_hex_sha256<LF>
```

The exact twenty-eight required rows are:

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
| 25 | `REQUEST_V8` | `docs/governance/EXECUTION_HARDENING_STEP3_OWNER_DECISION_REQUEST_V8.md` | recompute after request freeze |
| 26 | `PACKET_008` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008.md` | recompute after packet freeze |
| 27 | `DISPATCH_RECEIPT_008` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_DISPATCH_RECEIPT.md` | recompute after receipt freeze |
| 28 | `RESPONSE_008` | `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_RESPONSE.md` | recompute after response seal |

The Owner statement must repeat every row literally; reference to this table is not a substitute.
Before closeout, a verifier must establish complete ordered row equality, role/path uniqueness,
full hash recomputation, zero missing/extra/duplicate rows, and three-way digest equality among
required, actual, and Owner-stated canonical row bytes.

Canonical bytes use UTF-8/no BOM, exact TAB fields, exact LF after each row including the last,
no CR/header/fence/blank/quote/escape/extra byte, and sentinels excluded from the digest. The line
immediately after the end sentinel must be
`V8_OWNER_BINDING_TSV_V1_SHA256=<lowercase full 64-hex>`.

## 4. Exact invalid-history disposition block

The same future Owner statement must include the exact four-row
`V8_INVALID_HISTORY_DISPOSITION_TSV_V1` block specified by Package V8 Section 4. It must disclose
each internal claim and bind these controlling statuses:

```text
V8_INVALID_HISTORY_DISPOSITION_TSV_V1_BEGIN
11<TAB>INVALID_V6_EXTERNAL_MANIFEST<TAB>docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V6_CLOSEOUT_MANIFEST_V1.json<TAB>f7a1517e2ada0ef3412c077a03cd4c2bf04b1d0aadf45fd1143ecb386ea6a6ff<TAB>SELF_ASSERTED_DECISION_A_AUTHORITY_AND_APPROVED_OWNER_AUTHORIZATION<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
16<TAB>INVALID_V6_CLOSEOUT_RECEIPT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_CLOSEOUT_RECEIPT.md<TAB>a1f12ba54a46f52bc69889ab7129e49169be41d4ba2829e7d1416a2ab6426c42<TAB>SELF_ASSERTED_APPROVED_DECISION_A_RECEIPT<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
18<TAB>INVALID_V6_OWNER_CLOSEOUT<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_006_OWNER_CLOSEOUT.md<TAB>c51f5e1cf681e7da9cdc67c71e276eba060ada83183b2ee089c2bec4add56f58<TAB>SELF_ASSERTED_APPROVE_AND_AUTHORIZATION_CREATED<TAB>STOPPED_INVALID_OWNER_PATH_BINDING_NO_AUTHORITY_NOT_ADOPTED<LF>
22<TAB>RESPONSE_007_STOPPED<TAB>docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_007_RESPONSE.md<TAB>2ceea25782e0d6ba63150d5629d5adf1a63b7b6909ac4d92b7b9187c67f870ab<TAB>EMBEDDED_GO_WITH_REVIEW_SEVERITY_NONCONFORMANCE<TAB>STOPPED_REVIEW_SEVERITY_NONCONFORMANCE_NO_AUTHORITY<LF>
V8_INVALID_HISTORY_DISPOSITION_TSV_V1_END
V8_INVALID_HISTORY_DISPOSITION_TSV_V1_SHA256=9370da77c35c70eb18564efce1c47817a2632662ddd7f1f54210410218bc0de8
```

`<TAB>` and `<LF>` denote literal bytes `0x09` and `0x0a`. The exact row order is `11, 16, 18,
22`; every role, path, hash, internal-claim token, and disposition token is closed. The required
canonical row digest is
`9370da77c35c70eb18564efce1c47817a2632662ddd7f1f54210410218bc0de8`.

The Owner-level disposition outranks the historical self-description. The historical claim is
preserved but cannot grant authority. Unresolved conflict is BLOCKER; operative adoption is HIGH.

## 5. Unique future chain and arithmetic

Possible future chain paths, not authorized now:

1. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_OWNER_CLOSEOUT.md`
2. `docs/governance/clause_packets/CLAUSE_PACKET_EXECUTION_HARDENING_STEP3_20260826_008_CLOSEOUT_RECEIPT.md`
3. `docs/governance/EXECUTION_HARDENING_STEP3_PACKAGE_V8_CLOSEOUT_MANIFEST_V1.json`

Sole possible future target ref:
`refs/heads/governance/execution-hardening-step3-package-v8`.

Mandatory future order:

```text
Packet 008 -> Dispatch Receipt 008 -> Response 008
-> path-complete Owner statement
-> V8_OWNER_BINDING_SET_EXACT_PASS
-> V8_INVALID_HISTORY_DISPOSITION_EXACT_PASS
-> Owner Closeout 008 -> Closeout Receipt 008
-> V8 external manifest -> one direct-child commit -> one non-force push
```

Exact arithmetic:

```text
19 + authorization 1 = 20
20 + Package/Request V8 2 = 22
22 + Packet/Receipt/Response 008 3 = 25
25 + future Closeout/Receipt/Manifest 3 = 28
```

Owner-binding 28 and commit-addition 28 are distinct sets as defined in Package V8. Any future
manifest must freeze 27 artifacts excluding itself, 28 additions including itself, zero
modifications, and zero deletions.

## 6. Decision boundary

A timely Attempt 008 with `BLOCKER=0 / HIGH=0` makes only V8 package anchoring eligible for a
separate Owner decision. It does not authorize closeout, commit, push, implementation, CI, or
science.

Any BLOCKER/HIGH makes `NEXT_ELIGIBLE_ACTION=NONE`. Attempt 008 has no retry or fallback.

Current authorization forbids closeout, staging, commit, push, PR, Issue #48, PR #47, code,
implementation, CI, merge, ruleset, `main`, Decision B/C, Phase A/B, Tier 2, OIDC/signing,
data/target/path access, fit, Validation, Final Test, Test 3 retry, Test 3b, Test 4, and scientific
execution. After review, stop and return exact verdict/hashes regardless of result.

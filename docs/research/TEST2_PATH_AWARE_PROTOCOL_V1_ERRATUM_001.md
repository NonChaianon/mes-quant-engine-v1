# Test 2 Path-Aware Protocol V1 — Erratum 001

Status: **ADDITIVE ERRATUM / CREATE-ONCE / HISTORICAL V1 UNCHANGED**

Erratum date: `2026-08-24` (`Asia/Bangkok`)

## 1. Historical-document identity

The executed frozen document remains:

- path: `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md`;
- pre-edit source commit: `fe10fb1497e5df919702cf4ff294c4ebf8669b95`;
- Git blob: `555f31f55b657a0c621156de5f44d69e58261c82`;
- execution-authoritative SHA-256:
  `7048b848770304fa67ff75e7b4baa9e836bf83e5bbb17d08b2b92a61cc0ba105`.

Authority for that SHA is the Test 2 G3-P execution evidence record at
`artifacts/exploration/test2/g3p/MES_T2_G3P_F39C31C0900A1D35/pre_fit_support_record.json`.
Its `authorization_binding.document_bindings` records the protocol SHA above as both
`expected` and `observed`, with `match=true` and binding status
`PINNED_BEFORE_EXECUTION`. The record has semantic `record_sha256`
`a6906cf0a1392c76065c3e98cee0f48ad431af0d043d4d65749b03644704e32e` and local file
SHA-256 `ce71ddf99e110e12b8469d91b9d2509ccd9f24c22ee4274217273b17ba31e28c`.

## 2. Transcription correction

Section 4 of the historical protocol contains two transcription values. Their corrections
are additive and are not written into the executed frozen bytes:

| Field | Historical text | Correct value |
|---|---:|---:|
| `WF_2023` rows before feature/target eligibility | `5,474` | `5,476` |
| pooled maximum before feature/target eligibility | `10,984` | `10,986` |

The value `5,474` belongs to a separate full-29-feature usable-row fact. It is not the
pre-eligibility Cell 8 fold count.

## 3. Authority chain for the corrected values

The correction is cross-supported by these existing sources:

1. `reference/drive_evidence_v1/cell8_purged_split_audit.json`, SHA-256
   `add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a`, records
   `WF_2023.validation_rows=5476`;
2. `docs/handoff/MES_V1_HANDOFF.md`, SHA-256
   `94b13aa151d724481ef7f8d55a430d9462b0331692385598ab18c3f5f43fe791`, records
   walk-forward validation rows `5,510 / 5,476 / 5,508` for 2022/2023/2024;
3. `reference/drive_evidence_v1/cell8_walk_forward_folds_v1.csv`, SHA-256
   `93ef0978b17857f07d5df34b95253fe4ba998f7d6df3142e43474811a6bb761d`, records
   the `WF_2023` validation row count as `5476`.

## 4. Discovery and scope

The mismatch was discovered during Test 3 protocol review and is recorded contemporaneously
in `docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1_REVIEW_RECORD.md` Section 3.7,
SHA-256 `e90a6b294cfa8f3e8beb775da968b7b670705eded00ca4594f6fd7a74c5f43d9`.
That historical review record is not rewritten.

This erratum corrects a transcription in documentation. It does **not** change, recompute,
or reinterpret Test 2 data, targets, fits, metrics, bootstrap results, disposition,
authorization consumption, Validation status, or Final-Test status.

## 5. Immutability resolution and Test 3 non-impact

The Test 2 V1 file is restored byte-for-byte from its pre-edit Git blob and is not given an
in-file pointer to this erratum. Discoverability comes from the adjacent filename and the
architecture index.

The two ratified Test 3 artifacts remained byte-identical before and after this repair:

- `docs/research/TEST3_VOLATILITY_RISK_EDGE_PROTOCOL_V1.md`:
  `974ff7942f17174a2fbd855e42b591b2c0dad123ddae62d4436b418e68d4c826`;
- `docs/research/TEST3_PROJECT_HYPOTHESIS_BUDGET_V1.md`:
  `4e939608d0753c608675510c4e449cdac7d452022b0ec9d632fd989f045f58ed`.

No Test 3 re-ratification is triggered by this additive historical repair.

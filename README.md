# MES Quant Engine V1

สถานะ: **RESEARCH ONLY / TEST 2 CLOSED NEGATIVE / TEST 3 PROTOCOL DECISION / LIVE DISABLED**

## Project status

- **Historical Test 1 architecture:** `MES_QUANT_TARGET_ARCHITECTURE_v2.2` —
  `BASELINE_ACCEPTED / DESIGN_CLOSED`
- **Research design direction:** `MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT` —
  human-directed and framework-neutral; it is design guidance, not execution authority
- **Test 1 / Sprint 1:** `CLOSED / SEARCH BUDGET 2 OF 2 SPENT`; both `LR001` and
  `TREE001` failed the frozen continuation rule
- **Test 2:** one-shot TRAIN evaluation complete on preserved evidence branch
  `research/test2-g3f-real-execution-v1 @ c6e0281`; disposition
  `NOT_INTERESTING_ENOUGH`
- **Repository closeout:** complete on `main @ 9778b9b` via PR #45; open Issues = `0`,
  open PRs = `0` at closeout
- **Current gate:** freeze the Test 3 hypothesis/protocol before any implementation, new
  data access, or model training
- **Validation:** `UNOPENED`
- **Final Test:** `SEALED`
- **Live trading / broker execution:** `DISABLED`
- **LangGraph:** `RETIRED / DO NOT USE / DO NOT MERGE`

The Test 2 result is a clean negative result inside its frozen first-touch path scope. It
does not authorize a retry, a third Test 2 model, Validation access, Final-Test access, or
Test 3 work. The consumed Test 2 authorization cannot be reused.

## Source of truth and project navigation

Git and immutable evidence are the technical source of truth. Obsidian is the human-readable
Project Headquarters and must not be treated as merge, data-access, execution, or trading
authority.

- Architecture index — `docs/architecture/README.md`
- Current repository/research position — `docs/architecture/ARCHITECTURE_PROGRESS.md`
- Test 2 repository closeout — `docs/research/TEST2_REPOSITORY_CLOSEOUT_V1.md`
- Test 2 frozen protocol — `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md`
- Research architecture direction — `docs/architecture/MES_QUANT_RESEARCH_ARCHITECTURE_VNEXT.md`
- LangGraph retirement — `docs/architecture/LANGGRAPH_RETIREMENT_DECISION_20260822.md`
- Historical Test 1 baseline — `docs/architecture/MES_QUANT_TARGET_ARCHITECTURE_v2.2.md`
- Architecture history — `docs/architecture/ARCHITECTURE_CHANGELOG.md`

Architecture บอกว่า **ระบบควรมีขอบเขตอย่างไร**, Progress บอกว่า **ตอนนี้อยู่ตรงไหน**,
ส่วน protocol/evidence บอกว่า **การทดลองใดได้รับอนุญาตและเกิดอะไรขึ้นจริง**

## นักพัฒนาควรเริ่มที่ไหน

1. อ่าน `START_HERE_TH.md`
2. อ่าน `docs/architecture/ARCHITECTURE_PROGRESS.md`
3. อ่าน protocol ของ task ที่ได้รับอนุมัติเท่านั้น
4. ตรวจ branch, upstream, worktree และ exact evidence identity ก่อนเปลี่ยน project state
5. รัน tests และ Ruff ตามขอบเขตความเสี่ยงก่อน commit/push
6. ห้ามเปิด Validation, Final Test, broker execution หรือ live trading จากสถานะใน README

Test 3 ยังอยู่ในขั้นล็อก research question, source, target, model-family budget,
evaluation gate และ stop rule ไม่มี Test 3 implementation/data/train authorization ใน
repository closeout นี้

## Stable historical foundation

โครงการนี้ย้ายงาน MES Quant / Auto-Trading จาก Colab Cells 0–13 มาเป็น repository เพื่อ
แยกโค้ดออกจาก notebook globals, เพิ่มการทดสอบ point-in-time และรักษา Final Test ปี
2025–2026 ให้ปิดผนึกอยู่

Cell 14 สร้างข้อมูลจริงแบบ deterministic แล้ว: `31,193` Development rows, `29`
candidate features, `30,197` usable rows, Final Test rows = `0`, และ artifacts สองรอบ
ตรงกันแบบ byte-for-byte การคำนวณ Cell 14 จึง locked; frozen reference files ใต้
`reference/colab_v1_cells_0_13/` เป็นหลักฐานและห้ามแก้ตามปกติ

## Local requirements

- Python 3.12 (full parity uses 3.12.13)
- canonical input/artifact identities must match the applicable frozen contract
- no Databento key is needed for accepted local artifacts already present
- IBKR credentials are neither required nor authorized for current research
- large data, environments, generated runs, and credentials remain outside normal Git tracking

## Core checks

```bash
python -m pytest -q
python -m ruff check --select E9,F401,F63,F7,F82 src tests tools
python tools/verify_migration.py --artifact-root artifacts/cache/source_v1
python tools/verify_cell14_release.py
```

Artifact-dependent checks must be interpreted honestly when their ignored external fixtures
are absent. Apply the full Ruff rules to changed active Python files. The repository-wide
full-rule scan also reports known legacy findings in frozen notebooks and older Stage-B test
surfaces; do not rewrite historical evidence merely to make that broader scan green. Never
change an expected hash merely to make a new output pass.

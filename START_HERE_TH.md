# เริ่มงานต่อจากตรงนี้

## สถานะสั้นที่สุด

- Test 1 / Sprint 1: **ปิดแล้ว; LR001 และ TREE001 ไม่ผ่าน; budget 2/2 ถูกใช้ครบ**
- Test 2: **ปิดแล้วที่ evidence branch `c6e0281`; ผล `NOT_INTERESTING_ENOUGH`**
- Validation: **ยังไม่เปิด**
- Final Test ปี 2025–2026: **SEALED**
- Live trading / broker execution: **DISABLED**
- LangGraph: **RETIRED / ห้ามนำกลับมาใช้หรือ merge**
- ขั้นถัดไป: **ล็อก Test 3 protocol ก่อน code, data access หรือ training**

ผล Test 2 เป็นผลลบที่ชัดภายใน scope ที่กำหนด ไม่ใช่สิทธิ์ให้ rerun, เพิ่มโมเดลตัวที่สาม,
เปิด Validation หรือเริ่ม Test 3 โดยอัตโนมัติ

## เปิดไฟล์ไหน

1. `README.md` — ภาพรวมสั้น
2. `docs/architecture/ARCHITECTURE_PROGRESS.md` — ตำแหน่งปัจจุบันและ next gate
3. `docs/research/TEST2_REPOSITORY_CLOSEOUT_V1.md` — การผูก main/governance กับ Test 2
4. `docs/research/TEST2_PATH_AWARE_PROTOCOL_V1.md` — frozen Test 2 protocol
5. `docs/architecture/README.md` — แผนที่ architecture และสถานะเอกสาร

เมื่อเริ่ม Test 3 ให้เปิดเฉพาะ protocol ที่ Owner อนุมัติและตรวจ `CRASH_MEMORY.md` ใน
Obsidian ก่อนทุก project action ตาม workflow ปัจจุบัน

## สิ่งที่ต้องตรวจทุกครั้งก่อนเปลี่ยน repository

```bash
git fetch origin --prune
git status --short --branch
git log --oneline -3
python -m pytest -q
python -m ruff check --select E9,F401,F63,F7,F82 src tests tools
```

จากนั้นรัน full Ruff เฉพาะ Python files ที่เปลี่ยน ห้ามแก้ frozen notebook หรือ legacy
surface นอก scope เพียงเพื่อกำจัด baseline lint findings

ต้องแยกให้ชัดระหว่าง:

- code/test ผ่าน;
- protocol หรือ authorization อนุญาต;
- real-data execution เกิดขึ้นจริง;
- evidence ถูก commit/push;
- Validation/Final Test ถูกเปิดหรือยัง

อย่างหนึ่งไม่ทำให้อีกอย่างเป็นจริงโดยอัตโนมัติ

## Stable historical foundation

- Colab Cells 0–13: `LOCKED / historical evidence`
- Cell 14 computation: `LOCKED / deterministic`
- 29 candidate features: historical Test 1/Test 2 inputs; ไม่ใช่คำสั่งให้ใช้ต่อทุก Test
- Final Test rows opened: `0`

ไม่ต้องส่ง API key หรือ IBKR credentials สำหรับ repository closeout หรือ Test 3 protocol
design และห้ามแก้ frozen reference/hash เพื่อให้ผลใหม่ผ่าน

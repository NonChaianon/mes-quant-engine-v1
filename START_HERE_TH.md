# เริ่มงานต่อจากตรงนี้

## สถานะสั้นที่สุด

- Colab Cells 0–13: **LOCKED / เก็บเป็นหลักฐาน ห้ามแก้ตามปกติ**
- VS Code Cell 14: **LOCKED computation + deterministic feature artifact**
- 29 candidate features: **PROVISIONAL** จนกว่าจะผ่านการตรวจ redundancy
- Final Test ปี 2025–2026: **SEALED**
- ขั้นถัดไป: **Stage B — Redundancy and stability**

ตอนนี้คุณไม่ต้องส่ง API key, IBKR credentials หรือดาวน์โหลดข้อมูลเพิ่ม ไฟล์ Cells 5/7/8 ที่
ต้องใช้ถูกดาวน์โหลดและตรวจ SHA256 ตรงกับ Google Drive แล้ว

## เปิดไฟล์ไหน

1. เปิด `MES_Quant_Engine_V1.code-workspace` ด้วย VS Code.
2. อ่าน `docs/handoff/MES_V1_HANDOFF.md` เมื่อต้องการภาพรวมทั้งโครงการ.
3. อ่าน `docs/CELL14_FEATURE_CONTRACT.md` เมื่อต้องการตรวจสิ่งที่ Cell 14 ทำ.
4. ให้ developer เริ่มต่อที่ `docs/STAGE_B_REDUNDANCY_CONTRACT.md`.
5. ไฟล์โค้ดแรกของ Stage B คือ `src/mes_quant/redundancy/contract.py` แล้วจึงสร้าง
   `analyzer.py`; อย่ากลับไปเพิ่ม Cell ใหม่ใน Colab.

## สิ่งที่ Cell 14 ให้เรา

- 31,193 จุดตัดสินใจใน TRAIN/VALIDATION เท่านั้น.
- 29 features ที่ใช้ข้อมูลไม่เกินเวลาตัดสินใจ.
- 30,197 แถวพร้อมใช้ครบทุก feature (`96.807%`).
- 996 แถวมีบริบทย้อนหลังไม่สมบูรณ์ จึงถูกทำเครื่องหมาย ไม่เติมค่าหรือทิ้งแบบเงียบ ๆ.
- 5,703 ค่าที่หายมีเหตุผลกำกับแบบหนึ่งต่อหนึ่ง.
- Final Test rows = 0 และ forbidden Cell 9–13 inputs opened = 0.
- รันจริงสองรอบแล้วได้ไฟล์เหมือนกัน byte-for-byte.

## คำสั่งตรวจสุขภาพ

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
ruff check src pipelines tools tests
python tools\verify_migration.py --artifact-root artifacts\cache\source_v1
python tools\verify_cell14_release.py
```

ถ้าทั้งหมด PASS จึงเริ่ม Stage B ได้ หากมี hash ใดเปลี่ยน ให้หยุดและ audit ก่อน ไม่ควรแก้ตัวเลข
expected ให้ผ่านตาม output ใหม่โดยไม่มี defect statement และ version bump.

## หลักคิดง่าย ๆ

Cell 14 ตอบว่า “ก่อนตัดสินใจ เรารู้อะไรได้บ้าง” ส่วน Stage B จะตอบว่า “ข้อมูล 29 อย่างนี้มีอะไร
ซ้ำกัน และควรเก็บตัวแทนอะไรไว้” หลังจากนั้นจึงเริ่มโมเดลแบบโปร่งใสใน Stage C.

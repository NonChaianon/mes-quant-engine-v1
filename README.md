# MES Quant Engine V1

สถานะ: **VS CODE CUTOVER COMPLETE / CELL 14 BUILD LOCKED / STAGE B NEXT**

โครงการนี้เป็นเวอร์ชัน repository ของงาน MES Quant / Auto-Trading ที่ผ่าน Colab
Cells 0–13 แล้ว จุดประสงค์ของการย้ายคือแยกโค้ดจริงออกจาก notebook globals,
เพิ่มการทดสอบ point-in-time และรักษา Final Test ปี 2025–2026 ให้ปิดผนึกอยู่

## นักพัฒนาควรเริ่มที่ไหน

1. อ่าน `START_HERE_TH.md`
2. อ่านสถานะเต็มที่ `docs/MIGRATION_STATUS.md`
3. ตรวจสัญญา feature ที่ `docs/CELL14_FEATURE_CONTRACT.md`
4. งานถัดไปเริ่มที่ `docs/STAGE_B_REDUNDANCY_CONTRACT.md`
5. ห้ามแก้ Cell 14 ที่ LOCKED โดยไม่มี defect/version bump
6. รัน tests และตัวตรวจ release ก่อนสร้าง artifact ทุกครั้ง

Cell 14 รันกับข้อมูลจริงสองรอบแล้ว: `31,193` Development rows, `29` candidate features,
`30,197` แถว usable, Final Test rows = `0`, และ artifact ทั้งสองรอบตรงกันแบบ byte-for-byte
การคำนวณจึง **LOCKED** แต่การคัดเลือกว่าจะเก็บ feature ใดไว้ในโมเดลยัง **PROVISIONAL**

ห้ามพัฒนาโดยแก้ไฟล์ `reference/colab_v1_cells_0_13/cellNN.py` เพราะไฟล์เหล่านั้น
เป็นหลักฐาน frozen เท่านั้น

## สิ่งที่ต้องมีในเครื่อง

- Python 3.12 (parity เต็มใช้ 3.12.13)
- โฟลเดอร์ input ที่ hash ตรง; เครื่องนี้เตรียมไว้แล้วที่ `artifacts/cache/source_v1`
- ไม่ต้องใช้ Databento API key สำหรับ Cell 14 หากมี artifacts Cells 5/7/8 ครบ
- ยังไม่ต้องใช้ IBKR credentials

ไฟล์ข้อมูลใหญ่, `.venv`, generated runs และ credentials ถูกกันออกจาก Git ไว้แล้ว

## คำสั่งหลัก

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
ruff check src pipelines tools tests
python tools\verify_migration.py --artifact-root artifacts\cache\source_v1
python tools\verify_cell14_release.py
python pipelines\build_features.py --artifact-root artifacts\cache\source_v1
```

หน้าต่าง rolling แบบคงที่ยาวที่สุดคือ 240 นาที ส่วน `session_vwap_proxy_deviation` เป็น
session-to-date และอาจใช้ช่วงตั้งแต่ NYSE เปิด 09:30 ถึง decision 15:00 รวมเวลา 330 นาที
ทั้งสองแบบอนุญาตเฉพาะข้อมูลที่สิ้นสุดไม่เกิน decision time เท่านั้น

การสร้าง feature จริงจะหยุดทันทีถ้า hash ต้นทางไม่ตรง, พบ Final Test ในผลลัพธ์,
หรือมี target/cost/path artifact ถูกนำมาใช้

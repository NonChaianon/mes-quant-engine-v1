# Migration status

## สถานะปัจจุบัน

**MIGRATION GATE: PRIMARY DEVELOPMENT CUTOVER COMPLETE — ใช้ VS Code ตั้งแต่ Cell 14 เป็นต้นไป**

- **LOCKED:** Canonical Colab Cells 0–13, execution order 0–13, execution counts 37–50.
- **LOCKED:** Decision Universe, split contract, Development labels/path outcomes, baseline evaluation, and Final Test seal.
- **LOCKED:** Canonical notebook export and extracted source are reference-only.
- **LOCKED:** Exact local Cells 5/7/8 input bytes and Cell 14 point-in-time computation/artifacts.
- **LOCKED:** Cell 14 produced 31,193 rows twice with byte-identical outputs; Final Test rows used = 0.
- **PROVISIONAL:** Current-deployment cost counterfactual and the 29-feature candidate catalog.
- **OPEN:** Independent Linux/container regeneration parity; Windows/Colab-version local parity passed.
- **OPEN:** Dependency lock file; `pyproject.toml` pins the Colab-critical runtime first.
- **REJECTED:** Adding another independent monolithic Cell 14 implementation to Colab.

## Cutover gates

1. **Repository scaffold — COMPLETE.**
2. **Frozen notebook/source reference — COMPLETE.**
3. **Small Drive audit evidence copy — COMPLETE.**
4. **Cell 14 pure module, release verifier, and acceptance tests — COMPLETE; 33/33 tests and lint PASS.**
5. **Local large-artifact cache — COMPLETE; all 6/6 required input files are byte-exact.**
6. **Cell 14 real-data regeneration — COMPLETE; two deterministic runs and independent audit PASS.**
7. **Primary development cutover — COMPLETE. Stage B redundancy work now belongs in VS Code.**

Colab remains the immutable evidence authority for Cells 0–13. The repository is the development
authority from Cell 14 forward. Reopen a frozen Cell only after a documented defect, impact audit,
version bump, and dependent rerun.

The older frozen migration manifest intentionally retains its historical PROVISIONAL status. The
new Cell 14 release evidence records the later local-input parity and deterministic real-data PASS.

## Final Test firewall

Cell 14 may consume only Cell 5, Cell 7, and Cell 8 artifacts/audits. It must create exactly
31,193 Development rows and zero rows from 2025 onward. Cells 10–13 are forbidden inputs.

The longest fixed rolling feature window is 240 minutes. The session-to-date VWAP proxy is a
separate window that can span from the 09:30 NYSE open to the 15:00 decision (330 elapsed minutes).

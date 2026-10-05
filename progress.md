# Progress — Object Detection Streamlit

## Session Log
- 2026-10-04: Project initialized, plan created
- 2026-10-05: Phase 7 OCR accuracy improvement — implemented + verified

## Actions Taken
- Created project folder
- Created task_plan.md, findings.md, progress.md
- Decided stack: Streamlit + SQLite + OpenCV + EasyOCR
- Reason: Render free tier OOM (512MB) untuk EasyOCR
- 2026-10-05: Delegated OCR fix to OpenCode (fledge-alpha-free), Programmer review, applied review fixes

## Files Changed (Phase 7)
- ocr.py — added upscale_roi(), generate_variants(); rewrote ocr_plate() (allowlist, multi-variant, fallback, dedup)
- app.py — ocr_plate(roi, full_image=image_bgr); updated DEMO_NOTICE
- test_ocr.py — synthetic plate test (new)
- verify_ocr.py — end-to-end verification (new)

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Render OOM 512MB | 1 | Optimasi resize+GC — masih OOM |
| Render OOM 512MB | 2 | Pindah Fly.io — tidak ada free tier |
| Oracle capacity error | 1 | Region Batam penuh, tidak bisa tambah region |
| Railway 0.5GB | 1 | Terlalu ketat untuk EasyOCR |
| OpenCode edit tool missing path arg | 1 | Retried with correct args — succeeded |
| git status timeout (FUSE) | 1 | Skipped — not needed for verification |

## Next Steps
1. Commit + push ke GitHub
2. Streamlit Cloud auto-redeploy
3. Verify live with real photo

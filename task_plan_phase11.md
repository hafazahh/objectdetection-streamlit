# Phase 11 — YOLO Plate Detection + Similarity Scoring

## Goal
Perbaiki akurasi ANPR dengan mengganti deteksi contour OpenCV → YOLO, dan tampilkan
persentase kemiripan match member di dashboard.

## Keputusan arsitektur: Opsi A (YOLO + Tesseract)

| Tahap | Sebelum | Sesudah |
|---|---|---|
| 1. Deteksi plat | `detect_plate_contour` (OpenCV, tebak rasio 2:1–5:1) | **YOLOv8** (belajar bentuk plat) |
| 2. Isolasi ROI | crop dari contour | crop dari YOLO bbox |
| 3. Skor prediksi | EasyOCR conf, 5 varian | Tesseract conf, multi-PSM |
| 4. Banding DB | SequenceMatcher ≥0.85, tanpa persen | **persentase kemiripan ditampilkan** |
| 5. Dashboard | ✅/🟡/❌ | plat + conf OCR + **match sekian %** |

### Kenapa buang EasyOCR → Tesseract
- YOLO memperbaiki **akar masalah**: cropping buruk. Dengan crop presisi, ROI bersih & besar.
- RAM: EasyOCR reader peak 1253 MB. YOLO+Tesseract ~690 MB → hemat ~500 MB
- Cold start membaik (masalah "Server Error" 45-120s)
- Streamlit Cloud **mendukung `packages.txt`** untuk apt-get (beda dari Render yang tidak punya sudo)

## Phases
- [ ] 11.1 Install ultralytics + pytesseract, UKUR RAM nyata
- [ ] 11.2 Unduh model YOLO plat Indonesia
- [ ] 11.3 Implementasi `detect_plate_yolo()` di ocr.py
- [ ] 11.4 Implementasi Tesseract OCR multi-PSM
- [ ] 11.5 Expose persentase kemiripan match member
- [ ] 11.6 Update dashboard app.py
- [ ] 11.7 `packages.txt` untuk Streamlit Cloud
- [ ] 11.8 Verifikasi independen + test suite
- [ ] 11.9 Commit + deploy + verifikasi live

## Acceptance Criteria
- [ ] YOLO deteksi bbox plat dengan confidence ditampilkan
- [ ] Tesseract baca teks dari ROI YOLO
- [ ] Dashboard tampilkan persentase kemiripan match
- [ ] RAM puncak < 1.5 GB (target ~690 MB)
- [ ] Semua test suite lama masih lolos
- [ ] Live di vision.choirulhaq.com

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| — | — | — |

## Status
IN PROGRESS — mulai 2026-10-05

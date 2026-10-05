# Progress — Object Detection Streamlit

## Session Log
- 2026-10-04: Project initialized, plan created
- 2026-10-05: Phase 7 OCR accuracy improvement — implemented + verified
- 2026-10-05: Phase 8 format correction + fuzzy matching — implemented, verified, LIVE
- 2026-10-05: Phase 9 (YOLO) — **ON HOLD**, awaiting user review

## Actions Taken
- Created project folder
- Created task_plan.md, findings.md, progress.md
- Decided stack: Streamlit + SQLite + OpenCV + EasyOCR
- Reason: Render free tier OOM (512MB) untuk EasyOCR
- 2026-10-05: Delegated OCR fix to OpenCode (fledge-alpha-free), Programmer review, applied review fixes
- 2026-10-05: Removed phone number field (demo privacy) — commit fffe466 + a6dd798
- 2026-10-05: Cloudflare Worker custom domain (embed wrapper) — commit 1069675
- 2026-10-05: Phase 8 — Indonesian plate format correction + fuzzy member matching — commit 97be7e9

## Files Changed (Phase 7 — OCR accuracy)
- ocr.py — added upscale_roi(), generate_variants(); rewrote ocr_plate() (allowlist, multi-variant, fallback, dedup)
- app.py — ocr_plate(roi, full_image=image_bgr); updated DEMO_NOTICE
- test_ocr.py — synthetic plate test (new)
- verify_ocr.py — end-to-end verification (new)

## Files Changed (Phase 8 — format correction + fuzzy match)
- ocr.py — added PLATE_PATTERN, DIGIT_TO_LETTER, LETTER_TO_DIGIT, correct_plate_format(), _try_repair(); match_member() now returns (member, match_type)
- app.py — raw_plate vs plat_text display, fuzzy status indicator (🟡 "Periksa kembali")
- test_correction_fuzzy.py — 13 cases (new)
- verify_independent.py — 17 independent cases incl. false-positive hunt (new)
- measure_memory.py — RSS/peak measurement harness (new)

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Render OOM 512MB | 1 | Optimasi resize+GC — masih OOM |
| Render OOM 512MB | 2 | Pindah Fly.io — tidak ada free tier |
| Oracle capacity error | 1 | Region Batam penuh, tidak bisa tambah region |
| Railway 0.5GB | 1 | Terlalu ketat untuk EasyOCR |
| OpenCode edit tool missing path arg | 1 | Retried with correct args — succeeded |
| git status timeout (FUSE) | 1 | Skipped — not needed for verification |
| Streamlit auth redirect_uri rejected | 1 | `{}` response — Streamlit validates redirect_uri, proxy impossible |
| Streamlit embed hang | 1 | Diagnosed as WebSocket block (client-side) — not a server/app bug |
| Own fix attempt broke correct case | 1 | Digit-run guard rejected '81234A8C'->'B1234ABC'; REVERTED |

## Phase 8 — Independent verification result
17 checks, all pass. Two findings worth remembering:
1. **Guard ambiguity WORKS** — 'B1234ABE' (1 char from TWO members) correctly returns None instead of guessing.
2. **ACCEPTED trade-off** — 'B12345AB' (5 digits) repairs to 'B1234SAB', turning digit 5 into letter S.
   An attempt to block this (reject digit-runs > 4) ALSO blocked the main correct case
   '81234A8C' -> 'B1234ABC' (its run is also 5 digits). Reverted.
   **The two cases are indistinguishable without extra context.** Aggressive correction
   catches more true plates but can corrupt non-standard ones. Documented, not "fixed".

## Phase 9 — YOLO plate detection: ON HOLD (2026-10-05)

### Memory measurement (measure_memory.py, real RSS from /proc/self/status)
| Stage | RSS | Peak |
|---|---|---|
| bare interpreter | 8 MB | 8 MB |
| + opencv | 44 MB | 44 MB |
| + torch | 530 MB | 530 MB |
| + easyocr (module) | 721 MB | 721 MB |
| + EasyOCR Reader (models loaded) | 871 MB | **1253 MB** |
| + 1x readtext pass | 925 MB | 1253 MB |

**Key finding: torch alone = 486 MB. EasyOCR Reader peaks at 1.25 GB — 1.8x above the
documented 690 MB floor.** The app runs, so Streamlit Cloud is granting ~1.5-2 GB.
Budget is real but the exact ceiling is UNKNOWN.

### Why YOLO is on hold
- ultralytics reuses the SAME torch — no double load. Estimated added cost:
  ~50-100 MB (ultralytics + deps) + ~100-200 MB (model inference) => peak ~1.4-1.6 GB.
- Fits under 2.7 GB but headroom is thin, and concurrent visitors raise RSS further.
- We already hit OOM once (Render 512 MB). Risk is unmeasured, not zero.

### Three candidate paths (decide after review)
- **A. Drop easyocr -> pytesseract** — saves ~500 MB (no torch). Costs plate accuracy.
- **B. YOLO via hosted API (e.g. Roboflow, 1000 credits/mo free)** — zero added RAM,
  needs API key + network dependency. Pragmatic for a portfolio demo.
- **C. Split into two services** — YOLO elsewhere (Kaggle/Colab/VM) called over HTTP.
  Most work, no RAM ceiling.

### Ready-to-use model identified
- `wuriyanto/yolo8-indonesian-license-plate-detection` — YOLOv8, 1 class, MIT license,
  trained on Indonesian plates (dataset: linkgish/indonesian-plate-number-from-multi-sources)
- Alternative `morsetechlab/yolov11-license-plate-detection` (mAP@50 0.98) BUT its upstream
  Roboflow dataset has train/test contamination — do not trust that metric.

### Training path (if needed)
Kaggle: free GPU (T4x2 / P100, ~30h/week), Indonesian plate dataset already on Kaggle.
Export `best.pt` -> put in repo. Realistic, no local GPU needed.

## Current live state
- **URL:** https://vision.choirulhaq.com (Cloudflare Worker embed wrapper)
- **Origin:** https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app/?embed=true
- **Repo:** https://github.com/hafazahh/objectdetection-streamlit (branch master)
- **Last commit:** 97be7e9 — format correction + fuzzy matching

## Next Steps (resume here)
1. **USER IS REVIEWING** — no work in flight.
2. Decide Phase 9 path (A / B / C above).
3. If B: get Roboflow API key, add as Streamlit secret, wire detection call.
4. If A: benchmark pytesseract accuracy vs easyocr on the same plate photos before committing.
5. If training: build Kaggle notebook, export best.pt, measure RAM again with measure_memory.py.
6. **Cold start fix (cheap, independent of Phase 9):** UptimeRobot monitor pinging the ORIGIN
   health endpoint `https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app/healthz`
   every 5 minutes so the container never sleeps.
   **Do NOT point the monitor at `https://vision.choirulhaq.com`** — the Cloudflare Worker only
   serves a static HTML iframe wrapper (verified: 0 server-side fetches to Streamlit) and always
   returns 200, so it neither prevents sleep nor detects a sleeping app.
   Diagnosed 2026-10-05: the "Server Error" / hang is cold start, not traffic or a Streamlit outage.

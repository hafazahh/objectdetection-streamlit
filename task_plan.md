# Object Detection Streamlit — ANPR (Automatic Number Plate Recognition)

## Project
- **Path:** `/home/choirulhaq/GoogleDrive/AhliPemrograman/objectdetection-streamlit/`
- **Stack:** Streamlit + SQLite + OpenCV + EasyOCR
- **Deploy:** Streamlit Community Cloud (free, 690MB-2.7GB RAM, sleep 12 jam)
- **Goal:** Lightweight web app — upload/camera → deteksi plat → OCR → match member database

## Konsep (sama dengan versi Flask)
Aplikasi deteksi plat nomor kendaraan:
1. Input gambar (upload file atau camera)
2. Preprocessing OpenCV → deteksi area plat
3. OCR (EasyOCR) → baca teks plat
4. Match dengan database member
5. Simpan riwayat deteksi

## Perbedaan dari versi Flask
| Aspek | Flask | Streamlit |
|-------|-------|-----------|
| UI | HTML/Jinja2 templates | Python-only (st.* API) |
| Routing | Flask routes | Multipage (`pages/`) atau sidebar |
| State | Flask session | `st.session_state` |
| Database | SQLite file | SQLite file (reset on redeploy) |
| Deploy | Render/Fly.io/Docker | Streamlit Community Cloud (GitHub) |
| RAM | 512MB (Render) | 690MB-2.7GB |

## Struktur Project
```
objectdetection-streamlit/
├── app.py                  # Main app (deteksi + upload/camera)
├── db.py                   # Database helpers (SQLite)
├── ocr.py                  # OpenCV preprocessing + EasyOCR
├── pages/
│   ├── 1_Member.py         # CRUD member
│   └── 2_Riwayat.py        # Detection history
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Theme + server config
└── README.md
```

## Database Schema

### `members` table
```sql
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    plat_nomor TEXT NOT NULL UNIQUE,
    jenis_kendaraan TEXT DEFAULT 'Mobil',
    no_hp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `detections` table
```sql
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plat_nomor TEXT NOT NULL,
    member_id INTEGER,
    match_status TEXT NOT NULL,  -- 'matched' | 'unmatched'
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id)
);
```

## Phases

### Phase 1: Setup + Database
- [ ] `db.py` — SQLite helpers + schema init + seed sample members
- [ ] `requirements.txt` — streamlit, opencv-python-headless, easyocr, pillow, numpy
- [ ] `.streamlit/config.toml` — theme

### Phase 2: OCR Module
- [ ] `ocr.py` — OpenCV preprocessing (grayscale, blur, threshold, contour)
- [ ] EasyOCR reader (lazy load, cache via `@st.cache_resource`)
- [ ] `normalize_plate()` — uppercase, strip invalid chars
- [ ] `match_member()` — fuzzy match ke database

### Phase 3: Main App (Deteksi)
- [ ] `app.py` — halaman utama
- [ ] Upload file input (`st.file_uploader`)
- [ ] Camera input (`st.camera_input`)
- [ ] Tampilkan hasil: gambar + plat terdeteksi + status match
- [ ] Simpan ke `detections` table

### Phase 4: Member CRUD (pages/1_Member.py)
- [ ] List members (`st.dataframe`)
- [ ] Add member (form)
- [ ] Edit member
- [ ] Delete member

### Phase 5: Riwayat (pages/2_Riwayat.py)
- [ ] List detections
- [ ] Filter by match status
- [ ] Delete record

### Phase 6: UI Enhancement
- [ ] `.streamlit/config.toml` — purple theme (konsisten dengan profile site)
- [ ] Custom CSS via `st.markdown(unsafe_allow_html=True)`:
  - Card container untuk hasil deteksi
  - Gradient header
  - Custom button styling + hover
  - Rounded corners, shadow
- [ ] `st.metric()` — dashboard KPI (total member, total deteksi, match rate)
- [ ] `st.tabs()` — tabbed interface (Upload / Camera)
- [ ] `st.expander()` — detail section
- [ ] Ikon/emoji pada judul dan label
- [ ] Responsive layout (`st.columns()`)

### Phase 7: Deploy
- [ ] Push ke GitHub (repo public)
- [ ] Connect ke Streamlit Community Cloud
- [ ] Set secrets (kalau perlu)
- [ ] Verify live

## Acceptance Criteria

### Deteksi
- [ ] Upload gambar → deteksi plat → OCR → hasil tampil
- [ ] Camera input → deteksi → hasil tampil
- [ ] Match dengan member database
- [ ] Simpan ke riwayat

### Member CRUD
- [ ] List, add, edit, delete member
- [ ] Plat nomor unique
- [ ] Validasi form

### Riwayat
- [ ] List detections
- [ ] Filter matched/unmatched
- [ ] Delete record

### UI
- [ ] Navigasi sidebar (multipage)
- [ ] Responsive
- [ ] Demo notice: EasyOCR model ringan, akurasi terbatas

## Important Rules
- venv at `/home/choirulhaq/venvProject` (SOP)
- Use `python3` (not `python`)
- Google Drive FUSE mount — use short timeouts
- OpenCode: `/home/choirulhaq/.opencode/bin/opencode` (default free model, no --model flag)
- Streamlit: `@st.cache_resource` untuk EasyOCR reader (jangan reload tiap rerun)
- SQLite di Streamlit Cloud bersifat ephemeral — reset saat redeploy (untuk demo OK)
- Repo harus public untuk Streamlit Community Cloud free tier

## Status
- [x] Phase 1: Setup + Database
- [x] Phase 2: OCR Module
- [x] Phase 3: Main App (Deteksi)
- [x] Phase 4: Member CRUD
- [x] Phase 5: Riwayat
- [x] Phase 6: Deploy
- [x] Phase 7: OCR Accuracy Improvement (upscale, multi-variant, allowlist, fallback)
- [x] Phase 8: Format Correction + Fuzzy Matching
- [ ] Phase 9: YOLO Plate Detection — **ON HOLD (user reviewing)**
- [ ] Phase 10: Custom Domain (Cloudflare Worker embed wrapper) — DONE, see note below

## Phase 8: Format Correction + Fuzzy Matching — COMPLETE (commit 97be7e9)

### Implemented
1. `correct_plate_format(text)` — Indonesian pattern `^[A-Z]{1,2}[0-9]{1,4}[A-Z]{1,3}$`
   - Confusion pairs: digit→letter {0:O, 1:I, 8:B, 5:S, 2:Z, 6:G}
   - Confusion pairs: letter→digit {O:0, I:1, B:8, S:5, Z:2, G:6, D:0, Q:0}
   - `_try_repair()` tries all (lead, digit, trail) splits, scores by fewest corrections
   - Conservative: returns original unchanged if no confident repair
2. `match_member(plat)` → `(member, match_type)` where type ∈ {'exact', 'fuzzy', None}
   - Exact first (fast path), then `difflib.SequenceMatcher`
   - Accept only if ratio ≥ 0.85 AND length diff ≤ 1 AND strictly better than second-best
3. `app.py` — shows OCR raw vs corrected when they differ; fuzzy match gets
   🟡 "MATCHED (mirip) — Periksa kembali" instead of ✅

### Verification — 2 independent suites
**Agent suite (test_correction_fuzzy.py, 13 cases): ALL PASSED**
**Independent suite (verify_independent.py, 17 cases): ALL PASSED**

Independent suite specifically hunted false positives:
- 'B1234ABE' (1 char from TWO members) → **None** (ambiguity guard works)
- 'X9999XXX' → None; 'B9999ABC' (3 chars off) → None
- 'AB1234CD', 'A1234B', 'B1C' → valid, untouched
- 'B1234ABCD', 'ABC1234AB' → invalid, untouched

### Known accepted trade-off (NOT a bug to fix)
`'B12345AB'` (5 digits) → `'B1234SAB'` — digit 5 becomes letter S.
An attempt to block this (reject digit-runs > 4) **also blocked the main correct case**
`'81234A8C' → 'B1234ABC'` (its run is also 5 digits) and broke the agent suite. Reverted.
**The two cases are indistinguishable without extra context.** Aggressive correction
catches more true plates but can corrupt non-standard ones.

## Phase 9: YOLO Plate Detection — ON HOLD

### Memory measurement (measure_memory.py — real RSS from /proc/self/status)
| Stage | RSS | Peak |
|---|---|---|
| bare interpreter | 8 MB | 8 MB |
| + opencv | 44 MB | 44 MB |
| + torch | 530 MB | 530 MB |
| + easyocr (module) | 721 MB | 721 MB |
| + EasyOCR Reader | 871 MB | **1253 MB** |
| + 1x readtext | 925 MB | 1253 MB |

torch alone = 486 MB. Reader peak 1.25 GB = 1.8x the documented 690 MB floor.
App runs, so the real grant is ~1.5-2 GB — exact ceiling UNKNOWN.

### Decision pending — three paths
- **A.** easyocr → pytesseract: saves ~500 MB (drops torch), costs plate accuracy
- **B.** YOLO via hosted API (Roboflow, 1000 credits/mo free): zero added RAM, needs API key
- **C.** Split services: YOLO elsewhere (Kaggle/Colab/VM) called over HTTP

### Model candidates
- `wuriyanto/yolo8-indonesian-license-plate-detection` — YOLOv8, 1 class, MIT, Indonesian plates ✓
- `morsetechlab/yolov11-license-plate-detection` — mAP@50 0.98 BUT upstream dataset has
  train/test contamination → metric untrustworthy

### Training option
Kaggle free GPU (T4x2/P100, ~30h/week) + Indonesian plate dataset already on Kaggle.
Export `best.pt` into repo. No local GPU needed.

## Phase 10: Custom Domain — COMPLETE (commit 1069675)
Cloudflare Worker at `vision.choirulhaq.com` serves an HTML wrapper embedding the app
with `?embed=true`. Reverse proxy is IMPOSSIBLE: Streamlit validates `redirect_uri` at
`share.streamlit.io/-/auth/app` and only accepts its own `*.streamlit.app` origin
(rewriting it returns `{}` instead of 303). Skill: `streamlit-custom-domain`.

## Phase 7: OCR Accuracy Improvement — COMPLETE

### Root Cause Analysis
1. ROI kecil (~100-200px) → EasyOCR butuh teks lebih besar
2. Tidak ada preprocessing ROI (contrast, sharpening, threshold)
3. Tidak ada allowlist → EasyOCR coba semua karakter
4. Hanya SATU OCR attempt pada satu variant

### Implemented (2026-10-05)
1. `upscale_roi(image, min_width=400, max_width=1000)` — INTER_CUBIC up, INTER_AREA down (memory cap)
2. `generate_variants(image)` — 5 variants: original, CLAHE, Otsu, Otsu-inv, sharpened (unsharp mask)
3. Allowlist `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 `
4. `ocr_plate(image, full_image=None)` — fallback to full image only when ROI empty AND different image
5. Dedup by normalize_plate, keep max confidence, sort desc

### Verification (actual output)
- Full app flow synthetic scene: detect bbox (264,264,246,86), OCR read 'B 2301 PZX' conf=0.993
- Member match: 'B 1234 ABC' conf=0.997 → matched Budi Santoso
- Edge cases (None/empty/tiny): no crash, return []
- upscale_roi bounds: 150px→400px, 4000px→1000px
- ALL TESTS PASSED

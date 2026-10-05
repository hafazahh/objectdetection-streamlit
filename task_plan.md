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
- [ ] Phase 1: Setup + Database
- [ ] Phase 2: OCR Module
- [ ] Phase 3: Main App (Deteksi)
- [ ] Phase 4: Member CRUD
- [ ] Phase 5: Riwayat
- [ ] Phase 6: Deploy

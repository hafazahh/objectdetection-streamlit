# RESUME POINT — Object Detection Streamlit (ANPR)

> Baca ini dulu kalau melanjutkan project setelah jeda atau restart.
> Terakhir diperbarui: 2026-10-05

## Status: ON HOLD — user sedang review

Tidak ada pekerjaan yang sedang berjalan. Phase 9 (YOLO) belum dimulai.

## Live State
- **URL:** https://vision.choirulhaq.com
- **Origin:** https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app/?embed=true
- **Repo:** https://github.com/hafazahh/objectdetection-streamlit (branch `master`)
- **Last commit:** `97be7e9` — format correction + fuzzy matching
- **Project dir:** `/home/choirulhaq/GoogleDrive/AhliPemrograman/objectdetection-streamlit/`
- **venv:** `/home/choirulhaq/venvProject` (activate dulu, selalu pakai `python3`)

## Cara Verifikasi Cepat (health check)
```bash
# Origin hidup?
curl -s -o /dev/null -w "%{http_code}\n" --max-time 25 \
  "https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app/healthz"
# Harus: 200

# Custom domain?
curl -s -o /dev/null -w "%{http_code}\n" --max-time 25 https://vision.choirulhaq.com
# Harus: 200

# Test suite lokal
cd /home/choirulhaq/GoogleDrive/AhliPemrograman/objectdetection-streamlit
/home/choirulhaq/venvProject/bin/python3 test_correction_fuzzy.py   # 13 kasus
/home/choirulhaq/venvProject/bin/python3 verify_independent.py      # 17 kasus
/home/choirulhaq/venvProject/bin/python3 measure_memory.py          # ukur RAM
```

## Yang Sudah Selesai
| Phase | Isi | Commit |
|---|---|---|
| 1-6 | Setup, DB, OCR, deteksi, member CRUD, riwayat, deploy | — |
| 7 | OCR accuracy: upscale ROI, 5 varian preprocessing, allowlist, fallback | — |
| 8 | Koreksi format plat Indonesia + fuzzy match member | `97be7e9` |
| — | Hapus field nomor telepon (privasi demo) | `fffe466`, `a6dd798` |
| 10 | Custom domain via Cloudflare Worker embed wrapper | `1069675` |

## Yang Belum: Phase 9 (YOLO)

**Keputusan tertunda — pilih satu:**

- **A.** `easyocr` → `pytesseract` — hemat ~500 MB (buang torch), akurasi plat turun
- **B.** YOLO via API hosted (Roboflow free 1000 kredit/bulan) — nol RAM tambahan,
  butuh API key + bergantung jaringan. **Paling pragmatis untuk portofolio.**
- **C.** Pisah service — YOLO di Kaggle/Colab/VM, dipanggil via HTTP — paling ribet, tanpa batas RAM

**Model siap pakai:** `wuriyanto/yolo8-indonesian-license-plate-detection`
(YOLOv8, 1 class, MIT, dilatih plat Indonesia)

**Kalau training sendiri:** Kaggle GPU gratis (T4x2/P100 ~30 jam/minggu),
dataset plat Indonesia sudah ada di Kaggle. Export `best.pt` → taruh di repo.

## Angka RAM (hasil pengukuran nyata)
```
interpreter kosong        8 MB
+ opencv                 44 MB
+ torch                 530 MB   <- torch sendiri 486 MB
+ easyocr (modul)       721 MB
+ EasyOCR Reader        871 MB  (peak 1253 MB)
+ 1x OCR                925 MB
```
Streamlit Cloud memberi ~1.5-2 GB (app jalan di atas lantai 690 MB).
**Estimasi YOLO: puncak ~1.4-1.6 GB** — muat, tapi headroom tipis.

## Phase 11: YOLO + Tesseract — IN PROGRESS (mulai 2026-10-05)

**Keputusan user: Opsi A — YOLO deteksi plat + Tesseract OCR, EasyOCR dibuang.**

### Sudah dikerjakan
| Item | Status |
|---|---|
| `ultralytics 8.4.173` + `pytesseract 0.3.13` terpasang | ✅ |
| Model YOLO plat Indonesia (`models/plate_yolov8.pt`, 6.0 MB, MIT) | ✅ |
| `measure_memory_yolo.py` — RAM nyata terukur | ✅ |
| `ocr.py` ditulis ulang: YOLO + Tesseract + voting | ✅ |
| `app.py` diperbarui: bbox YOLO, persentase kemiripan, detail pipeline | ✅ |
| `requirements.txt` — easyocr dibuang, ultralytics + pytesseract ditambah | ✅ |
| `packages.txt` — `tesseract-ocr` untuk apt Streamlit Cloud | ✅ |

### RAM — hasil pengukuran nyata (measure_memory_yolo.py)
```
bare interpreter        8.4 MB
+ numpy                25.9 MB
+ opencv               54.6 MB
+ torch               541.6 MB
+ ultralytics         554.4 MB
+ pytesseract         628.8 MB
+ YOLO model loaded   646.5 MB
+ 1 inference         856.4 MB   <- peak
+ 1 Tesseract pass    857.0 MB
```
**Peak 857 MB vs EasyOCR 1253 MB → hemat 396 MB.** Cold start harusnya membaik.

### Akurasi pada 4 foto plat Indonesia asli (Wikimedia Commons)
| Foto | Ground truth | Hasil | Status |
|---|---|---|---|
| plat1 | `B1051TMW` | `B1051TMW` | ✅ EXACT |
| plat2 | `B1481TUB` | `21281TUBI` | ❌ |
| plat3 | `KT3344LA` | `KE3344LA` | ❌ (1 huruf) |
| plat4 | `B2156T0R` | `B2156TORI` | ❌ (nol bergaris + huruf ekstra) |

**1/4 exact.** Pipeline lama (contour + EasyOCR) = **0/4**.

### Temuan diagnostik penting
1. **YOLO deteksi berhasil 4/4** (confidence 0.42–0.86) — jauh lebih baik dari contour yang sering salah area
2. **Tesseract `gray psm7` dapat EXACT untuk plat1 & plat3** — mesin OCR-nya sanggup
3. **Penyebab utama kesalahan: fungsi skor memilih varian yang salah.** Satu varian bisa memberi confidence tinggi tapi salah, sementara yang benar ada di varian lain
4. **Solusi: voting lintas varian** (bukan ambil confidence tertinggi) — ini yang menaikkan plat1 & plat3
5. **plat2 sulit**: Tesseract konsisten membaca `21281...` bukan `B1481...` — kemungkinan kualitas crop/karakter
6. **plat4 sulit**: ada angka nol bergaris (slashed zero) + Tesseract menambah `I` di akhir
7. Inversi gambar membantu plat gelap (plat3) tapi merusak yang terang → karena itu **kedua polaritas dicoba**

### ⚠️ Temuan: ultralytics menarik opencv-python FULL
`pip install ultralytics` memasang **`opencv-python` 5.0.0.93** (versi full, bukan
headless) di samping `opencv-python-headless`. Versi full butuh library GUI
(Qt/GTK) yang tidak ada di server headless → **berisiko error impor dan menambah
RAM** di Streamlit Cloud.

**Yang harus dilakukan:** tambahkan `opencv-python-headless` **setelah** ultralytics
di requirements.txt agar pip memilih versi headless, atau pin eksplisit.
Cek di deploy apakah `import cv2` berhasil — kalau gagal, ini penyebabnya.

### Sedang berjalan
Eksperimen 8 kombinasi (4 strategi skor × 2 sumber kandidat) untuk cari konfigurasi terbaik secara empiris, bukan menebak.

### Yang belum
- [ ] Pilih strategi skor terbaik dari hasil eksperimen
- [x] Jalankan test suite lama (`test_correction_fuzzy.py` 3/3, `verify_independent.py` 17/17) — **LOLOS**
- [ ] Pastikan opencv headless menang atas opencv full di deploy
- [ ] Verifikasi independen pipeline baru (end-to-end)
- [x] Commit `f6f8be8`
- [ ] Deploy + verifikasi live di vision.choirulhaq.com

## Isu Terbuka (belum tuntas)
1. **Cold start lambat = "Server Error" / hang (TERDIAGNOSA 2026-10-05)**
   - Gejala: `Error: Server Error — The server encountered a temporary error and could not
     complete your request. Please try again in 30 seconds.` Muncul t+45s, bertahan sampai
     t+120s, lalu hilang sendiri. Setelahnya app render normal
     (`data-test-connection-state="CONNECTED"`).
   - **Bukan gangguan Streamlit global** — status page saat kejadian: All Systems Operational,
     0 insiden aktif.
   - **BUKAN karena trafik tinggi** — analytics menunjukkan 9 viewer dalam ~4 jam (sangat
     sedikit). Pesan errornya khas cold start, bukan overload.
   - **Penyebab: container butuh waktu lama boot karena app berat.** EasyOCR Reader memuncak
     1.25 GB RAM. Streamlit Cloud tidur setelah 12 jam idle; setiap bangun = 45-120 detik
     error/hang.
   - Catatan: viewer tercatat saat request MASUK, bukan saat app selesai render — jadi
     angka analytics termasuk yang gagal lihat.
   - **Mitigasi: UptimeRobot ping ORIGIN, bukan domain Worker.**
     - **BENAR** → `https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app/healthz`
       (balas `{"status":"ok"}`, tidak butuh login, request MASUK ke container → mencegah sleep)
     - **SALAH** → `https://vision.choirulhaq.com`
       (Cloudflare Worker hanya mengirim HTML statis berisi iframe; **0 server-side fetch**
       ke Streamlit — sudah diverifikasi dengan grep. Worker selalu balas 200, jadi monitor
       akan bilang "up" walaupun Streamlit tidur total. Tidak berguna untuk mencegah sleep.)
     - Boleh pasang DUA monitor: origin `/healthz` untuk cegah sleep, dan domain Worker
       untuk memantau Worker+domain itu sendiri.
     - Interval 5 menit sudah tepat (Streamlit sleep setelah 12 jam idle).
   - Mitigasi lain: buang EasyOCR → Tesseract (boot lebih cepat, RAM -500 MB) — lihat Phase 9 jalur A.
2. **Trade-off koreksi plat** — `'B12345AB'` → `'B1234SAB'` (angka jadi huruf).
   Sudah didokumentasikan sebagai trade-off yang diterima, bukan bug.

## SOP yang Dipakai
- Delegasi ke leadengineer → OpenCode di `/home/choirulhaq/.opencode/bin/opencode`
  (v2.0.20, **model default free**, tanpa flag `--model`, bungkus dengan `timeout`)
- Kalau OpenCode timeout → fallback: patch/write_file langsung
- RTK wajib untuk semua perintah terminal
- Google Drive FUSE lambat — pakai timeout pendek, hindari loop shell

## Pelajaran Penting
1. **Streamlit Cloud tidak bisa pakai reverse proxy** — validasi `redirect_uri`.
   Pakai Worker embed wrapper (`?embed=true`). Skill: `streamlit-custom-domain`
2. **Pin torch ke CPU wheel** — kalau tidak, build timeout (~2.5 GB).
   `torch==2.14.1+cpu` + `--extra-index-url https://download.pytorch.org/whl/cpu`
3. **Selalu verifikasi independen** — test buatan agen bisa overfit. Verifikasi independen
   menemukan 1 masalah dari 17 kasus di Phase 8.
4. **Perbaikan bisa lebih buruk dari masalah** — guard digit-run saya merusak kasus utama.
   Revert. Ukur dampak sebelum commit.
5. **JANGAN jalankan dua `git push` bersamaan ke repo yang sama.** Push pertama menaikkan
   ref remote; push kedua masih memegang ref lama dan ditolak dengan
   `cannot lock ref ... is at X but expected Y`. Ref lokal jadi basi, dan status
   "belum sinkron" yang dibaca setelahnya MENYESATKAN — sebenarnya push pertama berhasil.
   **Selalu `git fetch origin` dulu** untuk melihat keadaan sebenarnya sebelum melaporkan status.
6. **Jangan percaya `pgrep -f <nama>` untuk cek proses.** Perintah `pgrep` sendiri cocok
   dengan polanya, sehingga selalu melaporkan "masih jalan". Pakai `ps -eo pid,etime,cmd`
   dan filter, atau cek `ps -o etime= -p <pid>`.
7. **Dump semua varian sebelum menyimpulkan "alatnya lemah".** Kesimpulan awal saya
   ("Tesseract tidak sanggup") salah — ternyata fungsi skor yang salah memilih varian.
   Diagnostik lengkap mengubah arah perbaikan.
8. **Cek dependensi transitif.** `ultralytics` diam-diam menarik `opencv-python` versi GUI
   (butuh Qt/GTK) di samping versi headless — berisiko gagal impor di server headless.
   Deklarasikan versi headless SETELAH ultralytics di requirements.txt.

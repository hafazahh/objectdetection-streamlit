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
   - **Mitigasi termurah: UptimeRobot ping `https://vision.choirulhaq.com` tiap 5 menit** —
     app tidak pernah tidur, nol perubahan kode. (Sudah dipakai untuk Render.)
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

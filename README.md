# 🚗 ANPR — Deteksi Plat Nomor

Aplikasi web deteksi plat nomor kendaraan otomatis (Automatic Number Plate Recognition) menggunakan Streamlit, OpenCV, dan EasyOCR. Cocokkan plat terdeteksi dengan database member.

## Fitur

- 📤 Upload gambar atau 📷 ambil foto via kamera
- 🔍 Deteksi area plat dengan OpenCV (contour + aspect ratio)
- 🔠 OCR teks plat dengan EasyOCR
- ✅ Pencocokan dengan database member (SQLite)
- 📋 Riwayat deteksi + manajemen member (CRUD)
- 🎨 Tema ungu (`#6C5CE7`), responsif

## Setup Lokal

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Community Cloud

1. Push project ke GitHub (repo public).
2. Buka [share.streamlit.io](https://share.streamlit.io) dan login dengan GitHub.
3. Klik **New app**, pilih repo, branch, dan file utama `app.py`.
4. Klik **Deploy** — tunggu proses install dependensi selesai.

> ⚠️ Catatan: SQLite di Streamlit Cloud bersifat ephemeral — database akan reset saat redeploy/restart.

## Demo Notice

EasyOCR adalah model ringan; akurasinya terbatas pada gambar yang buram, kurang cahaya, sudut miring, atau plat yang tidak standar.

## Struktur

```
app.py                 # Aplikasi utama
db.py                  # Modul database SQLite
ocr.py                 # Modul OpenCV + EasyOCR
pages/1_Member.py      # Manajemen member
pages/2_Riwayat.py     # Riwayat deteksi
requirements.txt
.streamlit/config.toml
```

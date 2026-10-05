# Findings — Object Detection Streamlit

## Kenapa Streamlit (bukan Flask)
| Aspek | Flask + Render | Streamlit Cloud |
|-------|----------------|-----------------|
| RAM | 512MB → OOM | 690MB-2.7GB → aman |
| Sleep | 15 menit | 12 jam |
| Deploy | Docker/GitHub Actions | GitHub langsung |
| Kode UI | HTML/Jinja2 | Python saja |
| Persistent storage | Tidak | Tidak |

Render free tier OOM saat EasyOCR load (~400-500MB dari 512MB limit).

## EasyOCR di Streamlit
- Wajib `@st.cache_resource` untuk reader — kalau tidak, model reload tiap rerun (lambat + memory)
- Model download ~100MB saat first run — cache di container
- CPU mode cukup

## OpenCV Preprocessing Strategy
1. Resize max 800px width (memory)
2. Grayscale → Gaussian blur
3. Adaptive threshold / Canny
4. Find contours → filter aspect ratio plat (2:1 - 5:1)
5. Extract ROI → EasyOCR

## Streamlit Limitations (diterima untuk demo)
- SQLite ephemeral — reset saat redeploy/restart
- No custom domain di free tier
- Repo harus public
- Sleep 12 jam (visitor click to wake, ~30-60s)

## Alternatif yang Dipertimbangkan
- **Hugging Face Spaces** — free tier sekarang terbatas (Gradio/Docker Spaces butuh paid plan)
- **Railway free** — 0.5GB RAM, terlalu ketat
- **Oracle Cloud** — capacity error di region Batam, tidak bisa tambah region
- **Fly.io** — tidak ada free tier ($5/bulan Hobby)

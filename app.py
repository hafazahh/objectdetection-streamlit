import cv2
import numpy as np
import streamlit as st
from PIL import Image

import db
import ocr

st.set_page_config(page_title='ANPR Deteksi Plat', page_icon='🚗', layout='wide')

st.markdown('''
<style>
    .stApp { background-color: #0F0E17; }
    h1, h2, h3 { color: #6C5CE7 !important; }
    .result-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border: 2px solid #6C5CE7;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(108, 92, 231, 0.25);
        text-align: center;
    }
    .plate-text {
        font-size: 3rem;
        font-weight: 800;
        color: #E0E0E0;
        letter-spacing: 6px;
        background-color: #0F0E17;
        padding: 12px 24px;
        border-radius: 8px;
        display: inline-block;
        border: 3px dashed #6C5CE7;
    }
    .status-matched { color: #2ECC71; font-weight: 700; font-size: 1.4rem; }
    .status-unmatched { color: #E74C3C; font-weight: 700; font-size: 1.4rem; }
    .member-info { color: #E0E0E0; font-size: 1.1rem; margin-top: 8px; }
    .sim-bar {
        height: 10px; border-radius: 5px; background-color: #2A2A3E;
        margin: 10px auto 4px auto; max-width: 320px; overflow: hidden;
    }
    .sim-fill { height: 100%; border-radius: 5px; }
    div.stButton > button {
        background-color: #6C5CE7;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    div.stButton > button:hover { background-color: #5A4BD1; color: white; }
</style>
''', unsafe_allow_html=True)

# Initialize database and seed sample members
db.init_db()
db.seed_members()

# Sidebar
with st.sidebar:
    st.markdown('## 🚗 ANPR Deteksi Plat')
    st.info('Deteksi plat otomatis: **YOLO** menemukan area plat, **Tesseract** '
            'membaca teksnya, lalu hasilnya dibandingkan dengan database member.')
    st.warning(
        '⚠️ **Demo Notice:** Pipeline memakai YOLOv8 untuk deteksi area plat dan '
        'Tesseract OCR dengan voting lintas varian preprocessing. Akurasi tetap '
        'bergantung pada kualitas gambar.'
    )
    stats = db.get_detection_stats()
    st.metric('Total Member', stats['total_members'])
    st.metric('Total Deteksi', stats['total_detections'])
    if stats['total_detections']:
        rate = stats['matched_count'] / stats['total_detections'] * 100
        st.metric('Match Rate', f'{rate:.0f}%')

st.title('🚗 ANPR — Deteksi Plat Nomor')
st.markdown('Upload gambar atau ambil foto kendaraan untuk mendeteksi plat nomor.')

tab_upload, tab_camera = st.tabs(['📤 Upload Gambar', '📷 Camera'])

image_file = None
with tab_upload:
    image_file = st.file_uploader('Pilih gambar...', type=['jpg', 'jpeg', 'png', 'bmp'])

camera_file = None
with tab_camera:
    camera_file = st.camera_input('Ambil foto')

source = image_file if image_file is not None else camera_file

if source is not None:
    try:
        pil_image = Image.open(source).convert('RGB')
        image = np.array(pil_image)
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader('🖼️ Gambar Asli')
            st.image(image, use_container_width=True)

        with st.spinner('Mendeteksi plat nomor...'):
            # --- Step 1: YOLO plate detection -------------------------------
            bbox, yolo_conf = ocr.detect_plate_yolo(image_bgr)
            detector_used = 'YOLO'

            # Fallback to the legacy contour method if YOLO finds nothing
            if bbox is None:
                bbox = ocr.detect_plate_contour(image_bgr)
                yolo_conf = 0.0
                detector_used = 'contour (fallback)' if bbox else None

            if bbox is None:
                st.warning('⚠️ Area plat tidak terdeteksi. Mencoba OCR pada seluruh gambar...')
                roi = image_bgr
            else:
                # Compute the ROI FIRST, then display that exact image — the UI
                # must show the same crop OCR receives, not the raw YOLO box.
                roi = ocr.extract_plate_roi(image_bgr, bbox)
                with col2:
                    st.subheader('🔍 Area Plat')
                    if roi is not None and roi.size:
                        st.image(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB),
                                 use_container_width=True)
                    if detector_used == 'YOLO':
                        st.caption(f'Deteksi YOLO — confidence {yolo_conf * 100:.1f}%')
                    else:
                        st.caption(f'Deteksi {detector_used} — YOLO tidak menemukan plat')

            # --- Step 2 & 3: OCR with cross-variant voting -------------------
            # Pass the registered plates so the vote can prefer a read that
            # matches a known member, not just the most popular OCR string.
            known_plates = [m['plat_nomor'] for m in db.get_all_members()]
            ocr_results = ocr.ocr_plate(roi, full_image=image_bgr,
                                        db_plates=known_plates)

        if not ocr_results:
            st.error('❌ Tidak ada teks yang terbaca oleh OCR.')
        else:
            # --- Step 4: winner + format correction --------------------------
            best_text, best_score = ocr_results[0]
            raw_plate = ocr.normalize_plate(best_text)
            plat_text, was_corrected = ocr.correct_plate_format(raw_plate)

            # --- Step 5: compare with the member database --------------------
            member, match_type, similarity, runner_up = ocr.match_member(plat_text)
            match_status = 'matched' if member else 'unmatched'

            db.add_detection(
                plat_nomor=plat_text,
                member_id=member['id'] if member else None,
                match_status=match_status,
                image_path=getattr(source, 'name', 'camera.jpg'),
            )

            with col2:
                if match_status == 'matched':
                    if match_type == 'fuzzy':
                        status_html = ('<p class="status-matched" style="color:#F39C12;">'
                                       '🟡 MATCHED (mirip) — Periksa kembali</p>')
                    else:
                        status_html = '<p class="status-matched">✅ MATCHED — Member Terdaftar</p>'
                else:
                    status_html = ('<p class="status-unmatched">'
                                   '❌ UNMATCHED — Tidak Terdaftar</p>')

                member_html = ''
                if member:
                    member_html = (f'<p class="member-info"><b>Nama:</b> {member["nama"]}<br>'
                                   f'<b>Kendaraan:</b> {member["jenis_kendaraan"]}</p>')

                bar_color = ('#2ECC71' if similarity >= 90
                             else '#F39C12' if similarity >= 70 else '#E74C3C')
                sim_html = f'''
                <div class="sim-bar">
                    <div class="sim-fill" style="width:{min(similarity, 100):.1f}%;background-color:{bar_color};"></div>
                </div>
                <p style="color:#A0A0B0;margin:0;font-size:0.9rem;">
                    Kemiripan dengan database:
                    <b style="color:{bar_color};">{similarity:.1f}%</b>
                    {f' &middot; runner-up {runner_up:.1f}%' if runner_up else ''}
                </p>
                '''

                correction_html = ''
                if was_corrected and raw_plate != plat_text:
                    correction_html = (f'<p style="color:#A0A0B0;margin-top:8px;font-size:0.9rem;">'
                                       f'OCR membaca: <b>{raw_plate}</b> &rarr; '
                                       f'Dikoreksi: <b>{plat_text}</b></p>')

                st.markdown(f'''
                <div class="result-card">
                    <p style="color:#A0A0B0;">Plat Terdeteksi</p>
                    <div class="plate-text">{plat_text}</div>
                    {status_html}
                    {member_html}
                    {sim_html}
                    {correction_html}
                </div>
                ''', unsafe_allow_html=True)

            # --- Pipeline transparency ---------------------------------------
            with st.expander('🔬 Detail Pipeline'):
                st.markdown('**1. Deteksi area plat**')
                if bbox:
                    st.write(f'Detektor: `{detector_used}` — bbox `{bbox}`'
                             + (f', confidence {yolo_conf * 100:.1f}%' if yolo_conf else ''))
                else:
                    st.write('Tidak ada area plat terdeteksi — OCR dijalankan pada seluruh gambar.')

                st.markdown('**2. Kandidat OCR (diurutkan skor voting)**')
                for i, (text, score) in enumerate(ocr_results[:8], 1):
                    corr, _ = ocr.correct_plate_format(text)
                    st.write(f'{i}. `{text}` → `{corr}` — skor {score:.2f}')

                st.markdown('**3. Perbandingan dengan database member**')
                st.write(f'Plat hasil OCR: `{plat_text}`')
                st.write(f'Kemiripan tertinggi: **{similarity:.1f}%**'
                         + (f' (runner-up {runner_up:.1f}%)' if runner_up else ''))
                st.write(f'Keputusan: **{match_status}**'
                         + (f' — {member["nama"]}' if member else ''))

    except Exception as e:
        st.error(f'Terjadi kesalahan: {e}')

with st.expander('📖 Cara Penggunaan'):
    st.markdown('''
    1. **Upload gambar** kendaraan atau **ambil foto** menggunakan kamera.
    2. **YOLO** mendeteksi letak area plat nomor pada gambar.
    3. Area plat dipotong, lalu **Tesseract OCR** membacanya melalui beberapa
       varian preprocessing (grayscale, inversi, Otsu, CLAHE) dan beberapa mode
       pembacaan. Hasilnya di-**voting** — teks yang paling sering muncul menang,
       bukan yang confidence-nya paling tinggi.
    4. Teks dikoreksi ke format plat Indonesia (mis. `0`↔`O`, `1`↔`I`).
    5. Hasil dibandingkan dengan database member dan ditampilkan sebagai
       **persentase kemiripan**.

    **Tips:** Gunakan gambar yang jelas, plat terlihat tegak, dan pencahayaan cukup.
    ''')

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
    st.info('Aplikasi deteksi plat nomor kendaraan otomatis menggunakan OpenCV dan EasyOCR.')
    st.warning("⚠️ **Demo Notice:** Akurasi OCR ditingkatkan dengan upscale, multi-variant preprocessing, allowlist, koreksi format plat Indonesia, dan fuzzy matching. Hasil lebih akurat tetapi mungkin tetap tidak sempurna pada gambar buram atau sudut ekstrem.")
    stats = db.get_detection_stats()
    st.metric('Total Member', stats['total_members'])
    st.metric('Total Deteksi', stats['total_detections'])

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
            bbox = ocr.detect_plate_contour(image_bgr)

            if bbox is None:
                st.warning('⚠️ Area plat tidak terdeteksi. Mencoba OCR pada seluruh gambar...')
                roi = image_bgr
            else:
                x, y, w, h = bbox
                with col2:
                    st.subheader('🔍 Area Plat')
                    roi_display = image[y:y + h, x:x + w]
                    st.image(roi_display, use_container_width=True)
                roi = ocr.extract_plate_roi(image_bgr, bbox)

            ocr_results = ocr.ocr_plate(roi, full_image=image_bgr)

        if not ocr_results:
            st.error('❌ Tidak ada teks yang terbaca oleh OCR.')
        else:
            # Pick the best confidence result
            best_text, best_conf = max(ocr_results, key=lambda r: r[1])
            raw_plate = ocr.normalize_plate(best_text)

            # Apply format correction
            plat_text, was_corrected = ocr.correct_plate_format(raw_plate)

            # Match against member database
            member, match_type = ocr.match_member(plat_text)
            match_status = 'matched' if member else 'unmatched'

            # Save to detections table
            db.add_detection(
                plat_nomor=plat_text,
                member_id=member['id'] if member else None,
                match_status=match_status,
                image_path=getattr(source, 'name', 'camera.jpg'),
            )

            with col2:
                if match_status == 'matched':
                    if match_type == 'fuzzy':
                        status_html = '<p class="status-matched" style="color:#F39C12;">🟡 MATCHED (mirip) — Periksa kembali</p>'
                    else:
                        status_html = '<p class="status-matched">✅ MATCHED — Member Terdaftar</p>'
                else:
                    status_html = '<p class="status-unmatched">❌ UNMATCHED — Tidak Terdaftar</p>'

                member_html = ''
                if member:
                    member_html = f'''
                    <p class="member-info"><b>Nama:</b> {member['nama']}<br>
                    <b>Kendaraan:</b> {member['jenis_kendaraan']}</p>
                    '''

                # Show correction info if raw differs from corrected
                correction_html = ''
                if was_corrected and raw_plate != plat_text:
                    correction_html = f'''
                    <p style="color:#A0A0B0; margin-top:8px; font-size:0.9rem;">
                        OCR membaca: <b>{raw_plate}</b> → Dikoreksi: <b>{plat_text}</b>
                    </p>
                    '''

                st.markdown(f'''
                <div class="result-card">
                    <p style="color:#A0A0B0;">Plat Terdeteksi</p>
                    <div class="plate-text">{plat_text}</div>
                    {status_html}
                    {member_html}
                    {correction_html}
                    <p style="color:#A0A0B0; margin-top:12px;">Confidence: {best_conf * 100:.1f}%</p>
                </div>
                ''', unsafe_allow_html=True)

            with st.expander('📄 Detail OCR'):
                for text, conf in ocr_results:
                    st.write(f'**{text}** — {conf * 100:.1f}%')

    except Exception as e:
        st.error(f'Terjadi kesalahan: {e}')

with st.expander('📖 Cara Penggunaan'):
    st.markdown('''
    1. **Upload gambar** kendaraan atau **ambil foto** menggunakan kamera.
    2. Sistem akan mendeteksi area plat nomor menggunakan OpenCV.
    3. EasyOCR membaca teks pada area plat.
    4. Teks plat di-normalisasi dan dicocokkan dengan database member.
    5. Hasil ditampilkan dan dicatat ke riwayat deteksi.

    **Tips:** Gunakan gambar yang jelas, plat terlihat tegak, dan pencahayaan cukup.
    ''')

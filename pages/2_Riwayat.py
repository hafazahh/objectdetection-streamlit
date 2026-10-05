import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

st.set_page_config(page_title='Riwayat Deteksi', page_icon='📋', layout='wide')

st.markdown('''
<style>
    .stApp { background-color: #0F0E17; }
    h1, h2, h3 { color: #6C5CE7 !important; }
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

db.init_db()

st.title('📋 Riwayat Deteksi')

filter_status = st.selectbox('Filter Status', ['Semua', 'Matched', 'Unmatched'])

detections = db.get_all_detections()
if filter_status == 'Matched':
    detections = [d for d in detections if d['match_status'] == 'matched']
elif filter_status == 'Unmatched':
    detections = [d for d in detections if d['match_status'] == 'unmatched']

if detections:
    st.dataframe(detections, use_container_width=True)
else:
    st.info('Belum ada riwayat deteksi.')

st.subheader('🗑️ Kelola Riwayat')
for det in detections:
    with st.expander(f"#{det['id']} — {det['plat_nomor']} ({det['match_status']}) — {det['created_at']}"):
        st.write(f"**Plat Nomor:** {det['plat_nomor']}")
        st.write(f"**Member ID:** {det['member_id']}")
        st.write(f"**Status:** {det['match_status']}")
        st.write(f"**File:** {det['image_path']}")
        st.write(f"**Waktu:** {det['created_at']}")
        if st.button('🗑️ Hapus', key=f"del_{det['id']}"):
            if db.delete_detection(det['id']):
                st.success('✅ Riwayat dihapus.')
                st.rerun()
            else:
                st.error('❌ Gagal menghapus riwayat.')

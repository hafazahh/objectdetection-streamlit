import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

st.set_page_config(page_title='Data Member', page_icon='👥', layout='wide')

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
db.seed_members()

st.title('👥 Data Member')

members = db.get_all_members()
if members:
    st.dataframe(members, use_container_width=True)
else:
    st.info('Belum ada data member.')

st.subheader('➕ Tambah Member Baru')
with st.form('Tambah Member'):
    nama = st.text_input('Nama')
    plat_nomor = st.text_input('Plat Nomor')
    jenis_kendaraan = st.selectbox('Jenis Kendaraan', ['Mobil', 'Motor', 'Truk', 'Lainnya'])
    no_hp = st.text_input('No HP')
    submitted = st.form_submit_button('➕ Tambah Member')
    if submitted:
        if not nama or not plat_nomor:
            st.error('❌ Nama dan Plat Nomor wajib diisi!')
        else:
            new_id = db.add_member(nama, plat_nomor, jenis_kendaraan, no_hp)
            if new_id is not None:
                st.success(f'✅ Member "{nama}" berhasil ditambahkan (ID: {new_id}).')
                st.rerun()
            else:
                st.error('❌ Gagal menambahkan member. Plat nomor mungkin sudah terdaftar.')

st.subheader('✏️ Edit / 🗑️ Hapus Member')
for member in members:
    with st.expander(f"{member['id']} — {member['nama']} ({member['plat_nomor']})"):
        with st.form(f"edit_{member['id']}"):
            e_nama = st.text_input('Nama', value=member['nama'], key=f"en_{member['id']}")
            e_plat = st.text_input('Plat Nomor', value=member['plat_nomor'], key=f"ep_{member['id']}")
            jenis_list = ['Mobil', 'Motor', 'Truk', 'Lainnya']
            e_jenis = st.selectbox(
                'Jenis Kendaraan',
                jenis_list,
                index=jenis_list.index(member['jenis_kendaraan']) if member['jenis_kendaraan'] in jenis_list else 0,
                key=f"ej_{member['id']}",
            )
            e_hp = st.text_input('No HP', value=member['no_hp'] or '', key=f"eh_{member['id']}")
            if st.form_submit_button('💾 Simpan Perubahan'):
                if db.update_member(member['id'], e_nama, e_plat, e_jenis, e_hp):
                    st.success('✅ Member berhasil diperbarui.')
                    st.rerun()
                else:
                    st.error('❌ Gagal memperbarui member.')

        if st.button('🗑️ Hapus Member', key=f"del_{member['id']}"):
            st.session_state[f'confirm_del_{member["id"]}'] = True

        if st.session_state.get(f'confirm_del_{member["id"]}'):
            st.warning(f'⚠️ Yakin ingin menghapus "{member["nama"]}"?')
            c1, c2 = st.columns(2)
            with c1:
                if st.button('✅ Ya, Hapus', key=f"yes_{member['id']}"):
                    if db.delete_member(member['id']):
                        st.success('✅ Member dihapus.')
                        del st.session_state[f'confirm_del_{member["id"]}']
                        st.rerun()
                    else:
                        st.error('❌ Gagal menghapus member.')
            with c2:
                if st.button('❌ Batal', key=f"no_{member['id']}"):
                    del st.session_state[f'confirm_del_{member["id"]}']
                    st.rerun()

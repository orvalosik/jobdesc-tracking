import streamlit as st
from database import fetch_all, fetch_one, execute_query

def show_manage_users():
    # Mengadopsi CSS dari monitoring.py agar konsisten
    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
            padding: 25px; border-radius: 15px; color: white; margin-bottom: 25px;
        }
        
        /* 1. Tombol Simpan/Edit (Primary) - Warna Navy */
        section.main button[kind="primary"] {
            background-color: #1B263B !important;
            color: white !important;
            border: none !important;
        }

        /* 2. Tombol Batal / Hapus (Secondary) - Warna Abu-abu (Match Monitoring) */
        /* Menargetkan tombol yang bukan primary di area konten utama */
        section.main .stButton > button:not([kind="primary"]) {
            background-color: #6c757d !important;
            color: white !important;
            border: none !important;
        }
        
        /* Maksa teks di dalam tombol secondary tetap putih */
        section.main .stButton > button:not([kind="primary"]) p {
            color: white !important;
        }

        /* Efek Hover */
        button:hover { 
            opacity: 0.8; 
        }
        </style>
    """, unsafe_allow_html=True)

    # Proteksi Akses
    allowed_roles = ["Direktur Utama","Direktur","Promosi & CS","Business Development","Sekretaris Direksi","Manager Marketing", "Manager Umum & Personalia", "Manager Keuangan", "Manager Teknik"]
    if st.session_state["user"]["role"] not in allowed_roles:
        st.error("Akses Ditolak.")
        st.stop()

    if "manage_msg" in st.session_state:
        st.toast(st.session_state.pop("manage_msg"), icon="✅")

    if "edit_user_id" not in st.session_state:
        st.session_state["edit_user_id"] = None

    if st.session_state["edit_user_id"] is None:
        render_user_list()
    else:
        render_edit_form()

def render_user_list():
    st.markdown('<div class="header-card"><h2>👥 Kelola Data Pengguna</h2><p>Perbarui posisi atau divisi karyawan sesuai struktur organisasi.</p></div>', unsafe_allow_html=True)
    
    current_user = st.session_state["user"]
    
    # Cek apakah user yang login memiliki hak hapus & melihat seluruh divisi
    is_admin_div = current_user["divisi"] in ["Dewan Direksi", "Umum & Personalia", "Business Development"]

    # =========================================================
    # HAK AKSES DATA USER
    # =========================================================
    if is_admin_div:
        # Bisa lihat semua data
        query = """
            SELECT u1.id, u1.nama, u1.role, u1.divisi, u2.nama as nama_atasan 
            FROM users u1 
            LEFT JOIN users u2 ON u1.atasan_id = u2.id
            ORDER BY u1.divisi, u1.role, u1.nama
        """
        users = fetch_all(query)
    else:
        # Manager hanya lihat bawahan 1 divisi
        query = """
            SELECT u1.id, u1.nama, u1.role, u1.divisi, u2.nama as nama_atasan 
            FROM users u1 
            LEFT JOIN users u2 ON u1.atasan_id = u2.id
            WHERE u1.divisi = ?
            ORDER BY u1.role, u1.nama
        """
        users = fetch_all(query, (current_user["divisi"],))

    if not users:
        st.info("Belum ada data karyawan.")
        return

    # Atur lebar kolom aksi agar lebih proporsional saat ada 2 tombol
    if is_admin_div:
        cols = st.columns([2, 2, 1.5, 2, 1.8])
    else:
        cols = st.columns([2, 2, 1.5, 2, 1])

    for col, field in zip(cols, ["Nama", "Posisi", "Divisi", "Atasan", "Aksi"]):
        col.markdown(f"**{field}**")
    st.divider()

    for u in users:
        if is_admin_div:
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2, 1.8])
        else:
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2, 1])
            
        c1.text(u["nama"])
        c2.caption(f"📍 {u['role']}") 
        c3.text(u["divisi"])
        c4.text(u["nama_atasan"] if u["nama_atasan"] else "-")
        
        # LOGIKA TOMBOL AKSI
        if is_admin_div:
            # Pecah kolom aksi menjadi 2 sub-kolom berdampingan
            btn_col1, btn_col2 = c5.columns(2)
            
            # 1. Tombol Edit
            if btn_col1.button("Edit", key=f"edit_{u['id']}", type="primary", use_container_width=True):
                st.session_state["edit_user_id"] = u["id"]
                st.rerun()
                
            # 2. Tombol Hapus
            if btn_col2.button("Hapus", key=f"del_{u['id']}", use_container_width=True):
                # Proteksi agar tidak menghapus akun sendiri
                if u["id"] == current_user["id"]:
                    st.error("⚠️ Anda tidak bisa menghapus akun Anda sendiri.")
                else:
                    execute_query("DELETE FROM users WHERE id = ?", (u["id"],))
                    st.session_state["manage_msg"] = f"Data {u['nama']} berhasil dihapus!"
                    st.rerun()
        else:
            # Tombol Edit tunggal untuk Manager divisi biasa
            if c5.button("Edit", key=f"btn_{u['id']}", type="primary", use_container_width=True):
                st.session_state["edit_user_id"] = u["id"]
                st.rerun()

def render_edit_form():
    target_id = st.session_state["edit_user_id"]
    user_to_edit = fetch_one("SELECT * FROM users WHERE id = ?", (target_id,))
    
    current_user = st.session_state["user"]

    # =========================================================
    # VALIDASI HAK AKSES EDIT
    # =========================================================
    if current_user["divisi"] not in ["Dewan Direksi", "Umum & Personalia", "Business Development"]:
        if user_to_edit["divisi"] != current_user["divisi"]:
            st.error("Anda tidak memiliki akses untuk mengedit data divisi lain.")
            st.stop()
    
    st.markdown(f"### ⚙️ Perbarui Data: {user_to_edit['nama']}")
    
    list_role = ["Direktur Utama","Direktur","Promosi & CS","Business Development","Sekretaris Direksi","Manager Marketing", "Manager Umum & Personalia", "Manager Keuangan", "Manager Teknik", "Kabag. Seminar","Kabag. Personalia", "Kabag. Administrasi Keuangan", "Kabag. Penagihan", "Kabag. Akunting & Pajak","Kabag. Teknik","Kabag. Promosi & CS", "Supervisor ME","Supervisor Civil & Architectural", "Staff Administrasi Marketing","Staff Administrasi Seminar","Staff JDC Business Center","Staff Security","Staff Personalia/Spv. Security & Parkir","Staff Legal & Umum","Staff Fungsional Umum","Staff Receptionist","Staff Fungsional Penagihan","Staff Keuangan","Staff Kasir","Staff Invoice","Staff Admin Teknik"]
    list_divisi = ["Dewan Direksi", "Promosi & CS", "Business Development", "Sekretaris Direksi", "Marketing", "Umum & Personalia", "Keuangan", "Teknik"]
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_nama = st.text_input("Nama Lengkap", value=user_to_edit["nama"])
            try:
                role_idx = list_role.index(user_to_edit["role"])
            except:
                role_idx = 18 
            new_role = st.selectbox("Pilih Posisi Baru", list_role, index=role_idx)
            
        with col2:
            try:
                divisi_idx = list_divisi.index(user_to_edit["divisi"])
            except:
                divisi_idx = 7 
            new_divisi = st.selectbox("Pilih Divisi Baru", list_divisi, index=divisi_idx)
            
            # Logika Atasan
            if "Direktur" in new_role:
                new_atasan_id = None
            else:
                current_user = st.session_state["user"]
                if current_user["divisi"] in ["Dewan Direksi", "Umum & Personalia"]:
                    atasan_data = fetch_all("""
                        SELECT id, nama 
                        FROM users 
                        WHERE id != ?
                    """, (target_id,))
                else:
                    atasan_data = fetch_all("""
                        SELECT id, nama 
                        FROM users 
                        WHERE id != ?
                        AND divisi = ?
                    """, (target_id, current_user["divisi"]))
    
                atasan_options = {a["nama"]: a["id"] for a in atasan_data}
                atasan_list = ["-"] + list(atasan_options.keys())
                
                current_atasan_name = "-"
                for name, id_ in atasan_options.items():
                    if id_ == user_to_edit["atasan_id"]:
                        current_atasan_name = name
                
                try:
                    atasan_idx = atasan_list.index(current_atasan_name)
                except:
                    atasan_idx = 0

                selected_atasan = st.selectbox("Pilih Atasan", atasan_list, index=atasan_idx)
                new_atasan_id = atasan_options.get(selected_atasan)

        st.markdown("---")
        # Layout tombol
        b1, b2 = st.columns([1, 1])
        
        # Simpan (Navy)
        if b1.button("Simpan Perubahan", type="primary", use_container_width=True):
            execute_query(
                "UPDATE users SET nama=?, role=?, divisi=?, atasan_id=? WHERE id=?",
                (new_nama, new_role, new_divisi, new_atasan_id, target_id)
            )
            st.session_state["edit_user_id"] = None
            st.session_state["manage_msg"] = f"Data {new_nama} berhasil diperbarui!"
            st.rerun()
            
        # Batal (Abu-abu)
        if b2.button("Batal", use_container_width=True):
            st.session_state["edit_user_id"] = None
            st.rerun()
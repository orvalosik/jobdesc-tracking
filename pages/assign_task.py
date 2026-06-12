import streamlit as st
from database import execute_query, fetch_all, fetch_one
from datetime import datetime

def show_assign_task():

    # ============================================================
    # VALIDASI LOGIN & ROLE UTAMA
    # ============================================================
    user = st.session_state.get("user")

    if not user:
        st.warning("Silakan login terlebih dahulu.")
        return

    # 1. Cek apakah dia Direksi
    is_direksi = user.get("divisi") == "Dewan Direksi"
    
    # 2. Cek apakah dia Manager atau divisi non-struktural yang setara Manager
    user_role = user.get("role", "").lower()
    user_divisi = user.get("divisi", "")
    
    divisi_setara_manager = ["Business Development", "Sekretaris Direksi", "Promosi & CS"]
    
    is_setara_manager = ("manager" in user_role) or (user_divisi in divisi_setara_manager)

    # ============================================================
    # CSS TERMASUK TOMBOL NAVY (PRIMARY)
    # ============================================================
    st.markdown("""
    <style>
    div[data-testid="stForm"] {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: none;
    }

    .card-jobdesc {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1B263B;
        margin-bottom: 10px;
    }
    
    /* Memaksa tombol st.form_submit_button(type="primary") menjadi Biru Navy */
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    button[kind="primary"] {
        background-color: #1B263B !important;
        color: white !important;
        border: 1px solid #1B263B !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        background-color: #415A77 !important;
        border-color: #778DA9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # HEADER
    # ============================================================
    st.markdown("""
    <div class="header-card">
        <h2>🎯 Menu Kontrol & Delegasi Tugas Atasan</h2>
        <p>
            Kelola master tugas rutin dan delegasikan
            tugas proyek khusus kepada bawahan atau rekan sejawat.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # FUNGSI INTERN: FORM TUGAS NON-RUTIN (Supaya tidak duplikat kode)
    # ============================================================
    def render_non_routine_form(subordinates_list, info_message):
        st.subheader("🚀 Delegasi Tugas Non-Rutinitas")
        st.info(info_message)
        
        # Bentuk dropdown label: Nama (Role - Divisi)
        options = {f"{u['nama']} ({u['role']} - {u['divisi']})": u["id"] for u in subordinates_list}

        if not options:
            st.warning("⚠️ Tidak ada personil target yang tersedia saat ini.")
            return

        if "success_assign_nr" not in st.session_state:
            st.session_state["success_assign_nr"] = False

        with st.form("form_assign_non_routine"):
            target_display = st.selectbox("👤 Pilih Penerima Tugas", list(options.keys()))
            judul = st.text_input("📝 Judul Tugas Non-Rutin", placeholder="Masukkan judul tugas/proyek...")
            deskripsi = st.text_area("📋 Deskripsi Instruksi", placeholder="Jelaskan detail instruksi pekerjaannya...")
            deadline = st.date_input("📅 Deadline Target")

            st.markdown("<br>", unsafe_allow_html=True)
            submit_task = st.form_submit_button("🚀 Kirim Tugas", type="primary", use_container_width=True)

            if submit_task:
                if not judul.strip() or not deskripsi.strip():
                    st.error("⚠️ Judul dan deskripsi wajib diisi.")
                else:
                    target_id = options[target_display]
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Simpan data ke Database
                    execute_query(
                        """
                        INSERT INTO tasks (
                            judul, deskripsi, assigned_to, assigned_by, 
                            deadline, status_task, tanggal_assign
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (judul.strip(), deskripsi.strip(), target_id, user["id"], str(deadline), "assigned", now)
                    )

                    st.session_state["success_assign_nr"] = True
                    st.rerun()

        if st.session_state["success_assign_nr"]:
            st.balloons()
            st.success("🎉 Tugas non-rutin berhasil dikirim!")
            st.session_state["success_assign_nr"] = False

    # ============================================================
    # LOGIKA KONDISIONAL TAMPILAN (DIREKSI VS LEVEL MANAGER/NON-STRUKTURAL)
    # ============================================================
    
    if is_direksi:
        # --------------------------------------------------------
        # JIKA DIREKSI: TAMPILKAN 2 TAB
        # --------------------------------------------------------
        tab1, tab2 = st.tabs([
            "📋 Tugas Rutinitas",
            "🚀 Tugas Khusus (Non-Rutinitas)"
        ])

        # TAB 1 - MASTER TUGAS RUTIN (KHUSUS DIREKSI)
        with tab1:
            st.subheader("⚙️ Delegasi Tugas Rutinitas")
            st.info("💡 Anda memiliki akses penuh untuk seluruh divisi.")
            
            divisi_rows = fetch_all("""
                SELECT DISTINCT divisi FROM users 
                WHERE divisi IS NOT NULL AND divisi != 'Dewan Direksi'
            """)
            list_divisi = [d["divisi"] for d in divisi_rows]
            selected_divisi = st.selectbox("🏢 Pilih Divisi Target", list_divisi)

            role_rows = fetch_all(
                "SELECT DISTINCT role FROM users WHERE divisi = ? AND role IS NOT NULL", 
                (selected_divisi,)
            )
            list_role = [r["role"] for r in role_rows if r["role"]]

            if not list_role:
                st.warning("⚠️ Tidak ditemukan jabatan pada divisi ini.")
            else:
                if "edit_id" not in st.session_state:
                    st.session_state["edit_id"] = None

                # FORM TAMBAH TEMPLATE
                with st.form("form_master_tugas", clear_on_submit=True):
                    st.markdown("### ➕ Tambah Template Baru")
                    nama_tugas = st.text_input("📝 Nama Tugas Rutin", value="")
                    col1, col2 = st.columns(2)
                    with col1:
                        target_role = st.selectbox("🎯 Jabatan Target", list_role, index=0)
                    with col2:
                        kategori_periodik = st.selectbox("📅 Kategori Periodik", ["Harian", "Mingguan", "Bulanan", "Tahunan"], index=0)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit_btn = st.form_submit_button("💾 Simpan Template", type="primary")

                    if submit_btn:
                        if not nama_tugas.strip():
                            st.error("⚠️ Nama tugas tidak boleh kosong.")
                        else:
                            execute_query(
                                """
                                INSERT INTO jobdesc_templates (nama_tugas, divisi, role, kategori_periodik, assigned_by_id)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (nama_tugas.strip(), selected_divisi, target_role, kategori_periodik, user["id"])
                            )
                            st.success("✅ Template tugas rutin berhasil ditambahkan.")
                            st.rerun()

                st.markdown("---")
                st.markdown("### 📋 Daftar Template Tugas")
                filter_options = ["Semua Jabatan"] + list_role
                selected_filter = st.selectbox("🔍 Filter Jabatan", filter_options)

                if selected_filter == "Semua Jabatan":
                    existing_routines = fetch_all("SELECT * FROM jobdesc_templates WHERE divisi = ? ORDER BY role, kategori_periodik", (selected_divisi,))
                else:
                    existing_routines = fetch_all("SELECT * FROM jobdesc_templates WHERE divisi = ? AND role = ? ORDER BY kategori_periodik", (selected_divisi, selected_filter))

                if not existing_routines:
                    st.info("Belum ada template tugas.")
                else:
                    for r in existing_routines:
                        outer_col1, outer_col2 = st.columns([8, 2])
                        with outer_col1:
                            st.markdown(f"""
                            <div class="card-jobdesc" style="padding:14px 18px; border-radius:12px; background:#F8F9FA; border-left:5px solid #1B263B; margin-bottom:10px;">
                                <div style="margin-bottom:8px;">
                                    <span style="background:#1B263B; color:white; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:600;">{r['role']}</span>
                                    <span style="background:#E0E1DD; color:#1B263B; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:bold; margin-left:6px;">{r['kategori_periodik']}</span>
                                </div>
                                <div style="font-size:15px; font-weight:600; color:#1B263B; line-height:1.5;">{r['nama_tugas']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with outer_col2:
                            btn_edit = st.button("✏️ Edit", key=f"edit_{r['id']}", use_container_width=True)
                            btn_delete = st.button("🗑️ Hapus", key=f"hapus_{r['id']}", use_container_width=True)
                            if btn_edit:
                                st.session_state["edit_id"] = r["id"]
                                st.rerun()
                            if btn_delete:
                                execute_query("DELETE FROM jobdesc_templates WHERE id = ?", (r["id"],))
                                st.success("✅ Template berhasil dihapus.")
                                st.rerun()

                        if st.session_state.get("edit_id") == r["id"]:
                            with st.container():
                                st.markdown(f"##### ✏️ Mode Edit: Template #{r['id']}")
                                with st.form(f"edit_form_{r['id']}"):
                                    edit_nama = st.text_input("📝 Nama Tugas", value=r["nama_tugas"])
                                    col_e1, col_e2 = st.columns(2)
                                    with col_e1:
                                        edit_role = st.selectbox("🎯 Jabatan", list_role, index=list_role.index(r["role"]) if r["role"] in list_role else 0, key=f"role_edit_{r['id']}")
                                    with col_e2:
                                        kategori_list = ["Harian", "Mingguan", "Bulanan", "Tahunan"]
                                        edit_periodik = st.selectbox("📅 Kategori", kategori_list, index=kategori_list.index(r["kategori_periodik"]) if r["kategori_periodik"] in kategori_list else 0, key=f"periodik_edit_{r['id']}")
                                    cbtn1, cbtn2 = st.columns([1, 3])
                                    with cbtn1: cancel_edit = st.form_submit_button("❌ Batal")
                                    with cbtn2: save_edit = st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True)
                                    if cancel_edit: st.session_state["edit_id"] = None; st.rerun()
                                    if save_edit:
                                        if not edit_nama.strip(): st.error("⚠️ Nama tugas tidak boleh kosong.")
                                        else:
                                            execute_query("UPDATE jobdesc_templates SET nama_tugas = ?, role = ?, kategori_periodik = ? WHERE id = ?", (edit_nama.strip(), edit_role, edit_periodik, r["id"]))
                                            st.success("✅ Template berhasil diperbarui."); st.session_state["edit_id"] = None; st.rerun()
                                st.markdown("---")

        # TAB 2 - NON RUTIN UNTUK DIREKSI
        with tab2:
            div_rows = fetch_all("SELECT DISTINCT divisi FROM users WHERE divisi != 'Dewan Direksi' AND divisi IS NOT NULL")
            list_div_non_rutin = ["Semua Divisi"] + [d["divisi"] for d in div_rows]
            selected_divisi_nr = st.selectbox("🏢 Filter Divisi Target", list_div_non_rutin, key="div_nr")
            
            # Ambil semua Manager, Supervisor, dan staff divisi non-struktural
            if selected_divisi_nr == "Semua Divisi":
                subordinates = fetch_all("""
                    SELECT id, nama, role, divisi FROM users 
                    WHERE id != ? AND (
                        LOWER(role) LIKE '%manager%' 
                        OR LOWER(role) LIKE '%supervisor%'
                        OR divisi IN ('Business Development', 'Sekretaris Direksi', 'Promosi & CS')
                    )
                    ORDER BY divisi, role
                """, (user["id"],))
            else:
                subordinates = fetch_all("""
                    SELECT id, nama, role, divisi FROM users 
                    WHERE divisi = ? AND id != ? AND (
                        LOWER(role) LIKE '%manager%' 
                        OR LOWER(role) LIKE '%supervisor%'
                        OR divisi IN ('Business Development', 'Sekretaris Direksi', 'Promosi & CS')
                    )
                    ORDER BY role
                """, (selected_divisi_nr, user["id"]))

            render_non_routine_form(subordinates, "💡 Sebagai Direksi, Anda bebas menugaskan tugas non-rutin ke seluruh jajaran Manager, Supervisor, & Divisi Khusus.")

    elif is_setara_manager:
        # --------------------------------------------------------
        # JIKA JABATAN MANAGER ATAU DIVISI NON-STRUKTURAL: TANPA TAB (LANGSUNG FORM)
        # --------------------------------------------------------
        
        # Target penugasan adalah sesama kelompok manager & divisi non-struktural dari divisi mana saja
        subordinates = fetch_all("""
            SELECT id, nama, role, divisi FROM users 
            WHERE id != ? AND (
                LOWER(role) LIKE '%manager%'
                OR divisi IN ('Business Development', 'Sekretaris Direksi', 'Promosi & CS')
            )
            ORDER BY divisi, role
        """, (user["id"],))
        
        msg_info = f"📍 **Akses Koordinasi:** Sebagai {user['role']} ({user['divisi']}), Anda dapat mendelegasikan tugas non-rutin ke sesama level Manager atau Tim Non-Struktural lainnya lintas divisi."
        render_non_routine_form(subordinates, msg_info)
        
    else:
        # Jika ada role/divisi di luar aturan (Misal Supervisor mencoba buka menu ini)
        st.warning("⚠️ Anda tidak memiliki hak akses untuk memberikan tugas.")
        return
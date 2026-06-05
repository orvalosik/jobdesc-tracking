import streamlit as st
from database import execute_query, fetch_all, fetch_one
from datetime import datetime

def show_assign_task():

    # ============================================================
    # VALIDASI LOGIN
    # ============================================================
    user = st.session_state.get("user")

    if not user:
        st.warning("Silakan login terlebih dahulu.")
        return

    is_direksi = user.get("divisi") == "Dewan Direksi"

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
            tugas proyek khusus kepada bawahan.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # TAB
    # ============================================================
    tab1, tab2 = st.tabs([
        "📋 Tugas Rutinitas",
        "🚀 Tugas Khusus (Non-Rutinitas)"
    ])

    # ============================================================
    # TAB 1 - MASTER TUGAS RUTIN
    # ============================================================
    with tab1:
        st.subheader("⚙️ Delegasi Tugas Rutinitas")

        if is_direksi:
            st.info("💡 Anda memiliki akses penuh untuk seluruh divisi.")
            divisi_rows = fetch_all("""
                SELECT DISTINCT divisi
                FROM users
                WHERE divisi IS NOT NULL
            """)
            list_divisi = [d["divisi"] for d in divisi_rows if d["divisi"] != "Dewan Direksi"]
            selected_divisi = st.selectbox("🏢 Pilih Divisi", list_divisi)
        else:
            selected_divisi = user["divisi"]
            st.info(f"💡 Template tugas rutin akan digunakan oleh bawahan divisi {selected_divisi} saat mengisi logbook.")

        role_rows = fetch_all(
            """
            SELECT DISTINCT role
            FROM users
            WHERE divisi = ?
            """,
            (selected_divisi,)
        )

        blocked_keywords = ["Direksi", "Manager", "Head", "Supervisor", "Kepala", "Koordinator"]

        if is_direksi:
            list_role = [r["role"] for r in role_rows if r["role"]]
        else:
            list_role = [
                r["role"] for r in role_rows
                if r["role"] and not any(keyword.lower() in r["role"].lower() for keyword in blocked_keywords)
            ]
            if not list_role:
                list_role = [r["role"] for r in role_rows if r["role"] and r["role"] != user["role"]]

        if not list_role:
            st.warning("⚠️ Tidak ditemukan jabatan bawahan.")
            return

        # Inisialisasi state edit jika belum ada
        if "edit_id" not in st.session_state:
            st.session_state["edit_id"] = None

        # ============================================================
        # FORM TAMBAH TEMPLATE (Selalu Statis untuk Tambah Baru)
        # ============================================================
        with st.form("form_master_tugas", clear_on_submit=True):
            st.markdown("### ➕ Tambah Template Baru")
            
            nama_tugas = st.text_input("📝 Nama Tugas Rutin", value="")
            col1, col2 = st.columns(2)

            with col1:
                target_role = st.selectbox("🎯 Jabatan", list_role, index=0)

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

                # =====================================================
                # VISUALISASI CARD JOBDESC
                # =====================================================
                outer_col1, outer_col2 = st.columns([8, 2])

                with outer_col1:
                    st.markdown(f"""
                    <div class="card-jobdesc" style="padding:14px 18px; border-radius:12px; background:#F8F9FA; border-left:5px solid #1B263B; margin-bottom:10px;">
                        <div style="margin-bottom:8px;">
                            <span style="background:#1B263B; color:white; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:600;">
                                {r['role']}
                            </span>
                            <span style="background:#E0E1DD; color:#1B263B; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:bold; margin-left:6px;">
                                {r['kategori_periodik']}
                            </span>
                        </div>
                        <div style="font-size:15px; font-weight:600; color:#1B263B; line-height:1.5;">
                            {r['nama_tugas']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with outer_col2:
                    btn_edit = st.button(
                        "✏️ Edit",
                        key=f"edit_{r['id']}",
                        use_container_width=True
                    )

                    btn_delete = st.button(
                        "🗑️ Hapus",
                        key=f"hapus_{r['id']}",
                        use_container_width=True
                    )

                    if btn_edit:
                        st.session_state["edit_id"] = r["id"]
                        st.rerun()

                    if btn_delete:
                        execute_query("DELETE FROM jobdesc_templates WHERE id = ?", (r["id"],))
                        st.success("✅ Template berhasil dihapus.")
                        st.rerun()

                # =====================================================
                # FORM EDIT (MUNCUL TEPAT DI BAWAH ITEM YANG DI-KLIK)
                # =====================================================
                if st.session_state.get("edit_id") == r["id"]:
                    with st.container():
                        st.markdown(f"##### ✏️ Mode Edit: Template #{r['id']}")
                        with st.form(f"edit_form_{r['id']}"):

                            edit_nama = st.text_input(
                                "📝 Nama Tugas",
                                value=r["nama_tugas"]
                            )

                            col_e1, col_e2 = st.columns(2)

                            with col_e1:
                                edit_role = st.selectbox(
                                    "🎯 Jabatan",
                                    list_role,
                                    index=list_role.index(r["role"]) if r["role"] in list_role else 0,
                                    key=f"role_edit_{r['id']}"
                                )

                            with col_e2:
                                kategori_list = ["Harian", "Mingguan", "Bulanan", "Tahunan"]
                                edit_periodik = st.selectbox(
                                    "📅 Kategori",
                                    kategori_list,
                                    index=kategori_list.index(r["kategori_periodik"]) if r["kategori_periodik"] in kategori_list else 0,
                                    key=f"periodik_edit_{r['id']}"
                                )

                            cbtn1, cbtn2 = st.columns([1, 3])

                            with cbtn1:
                                cancel_edit = st.form_submit_button("❌ Batal")
                            with cbtn2:
                                save_edit = st.form_submit_button(
                                    "💾 Simpan Perubahan",
                                    type="primary",
                                    use_container_width=True
                                )

                            if cancel_edit:
                                st.session_state["edit_id"] = None
                                st.rerun()

                            if save_edit:
                                if not edit_nama.strip():
                                    st.error("⚠️ Nama tugas tidak boleh kosong.")
                                else:
                                    execute_query(
                                        """
                                        UPDATE jobdesc_templates
                                        SET nama_tugas = ?, role = ?, kategori_periodik = ?
                                        WHERE id = ?
                                        """,
                                        (edit_nama.strip(), edit_role, edit_periodik, r["id"])
                                    )
                                    st.success("✅ Template berhasil diperbarui.")
                                    st.session_state["edit_id"] = None
                                    st.rerun()
                        st.markdown("---") # Pembatas visual penutup form edit

    # ============================================================
    # TAB 2 - TUGAS NON RUTIN
    # ============================================================
    with tab2:
        st.subheader("🚀 Delegasi Tugas Non-Rutinitas")

        # 1. FILTER DIVISI KHUSUS DIREKSI
        if is_direksi:
            div_rows = fetch_all("SELECT DISTINCT divisi FROM users WHERE divisi != 'Dewan Direksi' AND divisi IS NOT NULL")
            list_div_non_rutin = [d["divisi"] for d in div_rows]
            
            selected_divisi_nr = st.selectbox("🏢 Pilih Divisi", list_div_non_rutin, key="div_nr")
            raw_staff = fetch_all("SELECT id, nama, role FROM users WHERE divisi = ? AND id != ?", (selected_divisi_nr, user["id"]))
            
            subordinates = raw_staff 
        else:
            st.info(f"📍 Divisi Anda: **{user['divisi']}** (Anda hanya dapat memberikan tugas kepada tim Anda)")
            selected_divisi_nr = user["divisi"]
            raw_staff = fetch_all("SELECT id, nama, role FROM users WHERE divisi = ? AND id != ?", (selected_divisi_nr, user["id"]))
            
            blocked_keywords = ["Direksi", "Manager", "Head"]
            subordinates = [
                u for u in raw_staff 
                if u["role"] and not any(kw.lower() in u["role"].lower() for kw in blocked_keywords)
            ]

        # 2. BENTUK DROPDOWN NAMA ORANG-ORANG
        options = {f"{u['nama']} ({u['role']})": u["id"] for u in subordinates}

        if not options:
            st.warning("⚠️ Tidak ada bawahan yang tersedia di divisi ini.")
        else:
            # Inisialisasi state untuk animasi/notifikasi sukses jika belum ada
            if "success_assign_nr" not in st.session_state:
                st.session_state["success_assign_nr"] = False

            with st.form("form_assign_non_routine"):
                target_display = st.selectbox("👤 Pilih Penerima Tugas", list(options.keys()))
                judul = st.text_input("📝 Judul Tugas", placeholder="Masukkan judul tugas...")
                deskripsi = st.text_area("📋 Deskripsi Instruksi", placeholder="Jelaskan detail pekerjaannya...")
                deadline = st.date_input("📅 Deadline")

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

                        # AKTIFKAN FLAG BERHASIL & LANGSUNG RERUN
                        st.session_state["success_assign_nr"] = True
                        st.rerun()

            # JIKA FLAG AKTIF, TAMPILKAN BALON & NOTIFIKASI DI LUAR FORM SETELAH RERUN
            if st.session_state["success_assign_nr"]:
                st.balloons()
                st.success("🎉 Tugas berhasil dikirim.")
                # Matikan kembali flag-nya agar balon tidak muncul terus-menerus saat klik menu lain
                st.session_state["success_assign_nr"] = False
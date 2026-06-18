import streamlit as st
from database import execute_query, fetch_all, fetch_one
from datetime import datetime
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")

def show_assign_task():

    user = st.session_state.get("user")
    if not user:
        st.warning("Silakan login terlebih dahulu.")
        return

    is_direksi       = user.get("divisi") == "Dewan Direksi"
    user_role        = user.get("role", "").lower()
    user_divisi      = user.get("divisi", "")
    divisi_setara    = ["Business Development", "Sekretaris Direksi", "Promosi & CS"]
    is_setara_manager = ("manager" in user_role) or (user_divisi in divisi_setara)

    # ── CSS ──
    st.markdown("""
        <style>
        /* Header card — disamakan dengan dashboard */
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px;
            border-radius: 16px;
            margin-bottom: 24px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .header-card h2 {
            margin: 0 0 4px 0;
            font-size: 22px;
            font-weight: 600;
            color: white !important;
        }
        .header-card p {
            margin: 0;
            font-size: 13px;
            color: #94A3B8 !important;
        }

        /* Form container */
        div[data-testid="stForm"] {
            background: white;
            padding: 28px;
            border-radius: 14px;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04);
            margin-bottom: 16px;
        }

        /* Card template jobdesc */
        .card-jobdesc {
            background: white;
            padding: 14px 18px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #10B981;
            margin-bottom: 10px;
        }

        /* Badge role & periodik */
        .badge-role {
            background: #0F172A;
            color: white;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-periodik {
            background: #D1FAE5;
            color: #065F46;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 6px;
        }

        /* Tombol primary — emerald */
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        button[kind="primary"] {
            background: linear-gradient(135deg, #10B981, #059669) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
        }
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
        button[kind="primary"]:hover {
            opacity: 0.9 !important;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: #F1F5F9;
            padding: 4px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 6px 18px;
            font-size: 13px;
        }
        .stTabs [aria-selected="true"] {
            background: white !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }

        /* Section subheader */
        .section-title {
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
            margin: 16px 0 8px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # ── Header ──
    st.markdown("""
        <div class="header-card">
            <h2>Delegasi & Kelola Tugas</h2>
            <p>Atur template tugas rutin dan delegasikan instruksi khusus kepada anggota tim.</p>
        </div>
    """, unsafe_allow_html=True)

    # ── Helper: form non-rutinitas ──
    def render_non_routine_form(subordinates_list, info_message):
        st.markdown('<p class="section-title">Delegasi Tugas Non-Rutinitas</p>', unsafe_allow_html=True)
        st.info(info_message)

        options = {f"{u['nama']}  ·  {u['role']} — {u['divisi']}": u["id"] for u in subordinates_list}

        if not options:
            st.warning("Tidak ada personil target yang tersedia saat ini.")
            return

        if "success_assign_nr" not in st.session_state:
            st.session_state["success_assign_nr"] = False

        with st.form("form_assign_non_routine"):
            target_display = st.selectbox(
                "Penerima Tugas",
                list(options.keys()),
                help="Pilih anggota tim yang akan menerima tugas ini"
            )
            judul     = st.text_input("Judul Tugas", placeholder="Contoh: Riset segmen pasar Q3 2026")
            deskripsi = st.text_area("Deskripsi & Instruksi", placeholder="Jelaskan detail pekerjaan, output yang diharapkan, dan referensi bila ada...", height=120)
            deadline  = st.date_input("Deadline Target")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            submit_task = st.form_submit_button(
                ":material/send: Kirim Tugas",
                type="primary",
                use_container_width=True
            )

            if submit_task:
                if not judul.strip() or not deskripsi.strip():
                    st.error("Judul dan deskripsi wajib diisi.")
                else:
                    target_id = options[target_display]
                    now = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                    execute_query(
                        "INSERT INTO tasks (judul, deskripsi, assigned_to, assigned_by, deadline, status_task, tanggal_assign) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (judul.strip(), deskripsi.strip(), target_id, user["id"], str(deadline), "assigned", now)
                    )
                    st.session_state["success_assign_nr"] = True
                    st.rerun()

        if st.session_state["success_assign_nr"]:
            st.balloons()
            st.success("Tugas berhasil dikirim!")
            st.session_state["success_assign_nr"] = False

    # ================================================================
    # DIREKSI
    # ================================================================
    if is_direksi:
        tab1, tab2 = st.tabs(["Tugas Rutinitas", "Tugas Khusus (Non-Rutinitas)"])

        # ── TAB 1: Master Template Rutin ──
        with tab1:
            st.markdown('<p class="section-title">Kelola Template Tugas Rutin</p>', unsafe_allow_html=True)
            st.info("Anda memiliki akses penuh untuk seluruh divisi.")

            divisi_rows   = fetch_all("SELECT DISTINCT divisi FROM users WHERE divisi IS NOT NULL AND divisi != 'Dewan Direksi'")
            list_divisi   = [d["divisi"] for d in divisi_rows]
            selected_divisi = st.selectbox(":material/apartment: Divisi Target", list_divisi)

            role_rows = fetch_all("SELECT DISTINCT role FROM users WHERE divisi = ? AND role IS NOT NULL", (selected_divisi,))
            list_role = [r["role"] for r in role_rows if r["role"]]

            if not list_role:
                st.warning("Tidak ditemukan jabatan pada divisi ini.")
            else:
                if "edit_id" not in st.session_state:
                    st.session_state["edit_id"] = None

                # Form tambah template
                with st.form("form_master_tugas", clear_on_submit=True):
                    st.markdown('<p class="section-title">Tambah Template Baru</p>', unsafe_allow_html=True)
                    nama_tugas = st.text_input("Nama Tugas Rutin", placeholder="Contoh: Rekap absensi harian")
                    col1, col2 = st.columns(2)
                    with col1:
                        target_role = st.selectbox("Jabatan Target", list_role)
                    with col2:
                        kategori_periodik = st.selectbox("Kategori Periodik", ["Harian", "Mingguan", "Bulanan", "Tahunan"])

                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    submit_btn = st.form_submit_button(":material/save: Simpan Template", type="primary")

                    if submit_btn:
                        if not nama_tugas.strip():
                            st.error("Nama tugas tidak boleh kosong.")
                        else:
                            execute_query(
                                "INSERT INTO jobdesc_templates (nama_tugas, divisi, role, kategori_periodik, assigned_by_id) VALUES (?, ?, ?, ?, ?)",
                                (nama_tugas.strip(), selected_divisi, target_role, kategori_periodik, user["id"])
                            )
                            st.success("Template berhasil ditambahkan.")
                            st.rerun()

                st.markdown("<hr style='border-color:#E2E8F0; margin:20px 0'>", unsafe_allow_html=True)
                st.markdown('<p class="section-title">Daftar Template Tugas</p>', unsafe_allow_html=True)

                filter_options  = ["Semua Jabatan"] + list_role
                selected_filter = st.selectbox("Filter Jabatan", filter_options)

                if selected_filter == "Semua Jabatan":
                    existing_routines = fetch_all("SELECT * FROM jobdesc_templates WHERE divisi = ? ORDER BY role, kategori_periodik", (selected_divisi,))
                else:
                    existing_routines = fetch_all("SELECT * FROM jobdesc_templates WHERE divisi = ? AND role = ? ORDER BY kategori_periodik", (selected_divisi, selected_filter))

                if not existing_routines:
                    st.info("Belum ada template tugas untuk divisi ini.")
                else:
                    for r in existing_routines:
                        col_card, col_btn = st.columns([8, 2])
                        with col_card:
                            st.markdown(f"""
                                <div class="card-jobdesc">
                                    <div style="margin-bottom:6px;">
                                        <span class="badge-role">{r['role']}</span>
                                        <span class="badge-periodik">{r['kategori_periodik']}</span>
                                    </div>
                                    <div style="font-size:14px; font-weight:600; color:#1E293B;">{r['nama_tugas']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col_btn:
                            if st.button(":material/edit: Edit", key=f"edit_{r['id']}", use_container_width=True):
                                st.session_state["edit_id"] = r["id"]
                                st.rerun()
                            if st.button(":material/delete: Hapus", key=f"hapus_{r['id']}", use_container_width=True):
                                execute_query("DELETE FROM jobdesc_templates WHERE id = ?", (r["id"],))
                                st.success("Template dihapus.")
                                st.rerun()

                        if st.session_state.get("edit_id") == r["id"]:
                            with st.container(border=True):
                                st.markdown(f'<p class="section-title">Edit Template #{r["id"]}</p>', unsafe_allow_html=True)
                                with st.form(f"edit_form_{r['id']}"):
                                    edit_nama = st.text_input("Nama Tugas", value=r["nama_tugas"])
                                    ce1, ce2  = st.columns(2)
                                    with ce1:
                                        edit_role = st.selectbox("Jabatan", list_role, index=list_role.index(r["role"]) if r["role"] in list_role else 0, key=f"role_edit_{r['id']}")
                                    with ce2:
                                        kat_list   = ["Harian","Mingguan","Bulanan","Tahunan"]
                                        edit_periodik = st.selectbox("Kategori", kat_list, index=kat_list.index(r["kategori_periodik"]) if r["kategori_periodik"] in kat_list else 0, key=f"periodik_edit_{r['id']}")
                                    cb1, cb2 = st.columns([1,3])
                                    with cb1: cancel = st.form_submit_button(":material/close: Batal")
                                    with cb2: save   = st.form_submit_button(":material/save: Simpan", type="primary", use_container_width=True)
                                    if cancel:
                                        st.session_state["edit_id"] = None; st.rerun()
                                    if save:
                                        if not edit_nama.strip():
                                            st.error("Nama tugas tidak boleh kosong.")
                                        else:
                                            execute_query("UPDATE jobdesc_templates SET nama_tugas=?, role=?, kategori_periodik=? WHERE id=?", (edit_nama.strip(), edit_role, edit_periodik, r["id"]))
                                            st.success("Template diperbarui.")
                                            st.session_state["edit_id"] = None; st.rerun()

        # ── TAB 2: Non-Rutin Direksi ──
        with tab2:
            div_rows = fetch_all("SELECT DISTINCT divisi FROM users WHERE divisi != 'Dewan Direksi' AND divisi IS NOT NULL")
            list_div_nr = ["Semua Divisi"] + [d["divisi"] for d in div_rows]
            selected_divisi_nr = st.selectbox(":material/apartment: Filter Divisi", list_div_nr, key="div_nr")

            if selected_divisi_nr == "Semua Divisi":
                subordinates = fetch_all("""
                    SELECT id, nama, role, divisi FROM users
                    WHERE id != ? AND (
                        LOWER(role) LIKE '%manager%' OR LOWER(role) LIKE '%supervisor%'
                        OR divisi IN ('Business Development','Sekretaris Direksi','Promosi & CS')
                    ) ORDER BY divisi, role
                """, (user["id"],))
            else:
                subordinates = fetch_all("""
                    SELECT id, nama, role, divisi FROM users
                    WHERE divisi = ? AND id != ? AND (
                        LOWER(role) LIKE '%manager%' OR LOWER(role) LIKE '%supervisor%'
                        OR divisi IN ('Business Development','Sekretaris Direksi','Promosi & CS')
                    ) ORDER BY role
                """, (selected_divisi_nr, user["id"]))

            render_non_routine_form(subordinates, "Sebagai Direksi, Anda dapat menugaskan ke seluruh jajaran Manager, Supervisor, dan Divisi Khusus.")

    # ================================================================
    # LEVEL MANAGER / NON-STRUKTURAL
    # ================================================================
    elif is_setara_manager:
        subordinates = fetch_all("""
            SELECT id, nama, role, divisi FROM users
            WHERE id != ? AND (
                LOWER(role) LIKE '%manager%'
                OR divisi IN ('Business Development','Sekretaris Direksi','Promosi & CS')
            ) ORDER BY divisi, role
        """, (user["id"],))

        render_non_routine_form(
            subordinates,
            f"Sebagai **{user['role']}**, Anda dapat mendelegasikan tugas non-rutin ke sesama Manager atau Tim Non-Struktural lintas divisi."
        )

    else:
        st.warning("Anda tidak memiliki hak akses untuk halaman ini.")
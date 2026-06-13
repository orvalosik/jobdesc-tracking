import streamlit as st
from database import fetch_all, fetch_one, execute_query

LIST_ROLE   = ["Direktur Utama","Direktur","Promosi & CS","Business Development",
               "Sekretaris Direksi","Manager Marketing","Manager Umum & Personalia",
               "Manager Keuangan","Manager Teknik","Kabag. Promosi & CS",
               "Supervisor Civil & Architectural"]
LIST_DIVISI = ["Dewan Direksi","Promosi & CS","Business Development","Sekretaris Direksi",
               "Marketing","Umum & Personalia","Keuangan","Teknik"]

ALLOWED_ROLES = [
    "Direktur Utama", "Direktur",
    "Business Development",
    "Manager Umum & Personalia",
]

def show_manage_users():
    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px; border-radius: 16px; margin-bottom: 24px;
            border: 1px solid rgba(16,185,129,0.2);
        }
        .header-card h2 { margin:0 0 4px 0; font-size:22px; font-weight:600; color:white !important; }
        .header-card p  { margin:0; font-size:13px; color:#94A3B8 !important; }

        /* Tabel header */
        .tbl-header {
            display: grid;
            gap: 8px;
            padding: 8px 12px;
            background: #F1F5F9;
            border-radius: 8px;
            margin-bottom: 6px;
            font-size: 12px;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .tbl-header.admin { grid-template-columns: 2fr 2fr 1.5fr 2fr 1.8fr; }
        .tbl-header.mgr   { grid-template-columns: 2fr 2fr 1.5fr 2fr 1fr;   }

        /* Row user */
        .user-row {
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            background: white;
            margin-bottom: 6px;
            transition: box-shadow .15s;
        }
        .user-row:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

        /* Badge divisi */
        .div-badge {
            display: inline-block;
            background: #F1F5F9;
            color: #475569;
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
        }

        /* Tombol primary emerald */
        section.main button[kind="primary"] {
            background: linear-gradient(135deg,#10B981,#059669) !important;
            color: white !important; border: none !important;
            font-weight: 600 !important; border-radius: 8px !important;
        }
        /* Tombol hapus — merah subtle */
        .st-key-del_btn button {
            background: transparent !important;
            color: #EF4444 !important;
            border: 1px solid rgba(239,68,68,.3) !important;
            border-radius: 8px !important;
        }
        .st-key-del_btn button:hover {
            background: rgba(239,68,68,.06) !important;
        }

        /* Edit form container */
        .edit-container {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 24px;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.session_state["user"]["role"] not in ALLOWED_ROLES:
        st.error(":material/lock: Akses ditolak.")
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
    current = st.session_state["user"]
    is_admin = current["divisi"] in ["Dewan Direksi", "Umum & Personalia", "Business Development"]

    st.markdown("""
        <div class="header-card">
            <h2>Kelola Pengguna</h2>
            <p>Perbarui data, posisi, atau divisi karyawan sesuai struktur organisasi.</p>
        </div>
    """, unsafe_allow_html=True)

    if is_admin:
        users = fetch_all("""
            SELECT u1.id, u1.nama, u1.role, u1.divisi, u2.nama as nama_atasan
            FROM users u1 LEFT JOIN users u2 ON u1.atasan_id = u2.id
            ORDER BY u1.divisi, u1.role, u1.nama
        """)
    else:
        users = fetch_all("""
            SELECT u1.id, u1.nama, u1.role, u1.divisi, u2.nama as nama_atasan
            FROM users u1 LEFT JOIN users u2 ON u1.atasan_id = u2.id
            WHERE u1.divisi = ?
            ORDER BY u1.role, u1.nama
        """, (current["divisi"],))

    if not users:
        st.info("Belum ada data karyawan.")
        return

    # Ringkasan singkat
    total = len(users)
    divisi_unik = len(set(u["divisi"] for u in users))
    s1, s2 = st.columns(2)
    s1.metric(":material/group: Total Pengguna", total)
    s2.metric(":material/apartment: Divisi", divisi_unik)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Filter cepat
    divisi_filter_opts = ["Semua"] + sorted(set(u["divisi"] for u in users))
    sel_div = st.selectbox(":material/filter_list: Filter Divisi", divisi_filter_opts, label_visibility="collapsed")
    filtered = users if sel_div == "Semua" else [u for u in users if u["divisi"] == sel_div]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Header kolom
    cls = "admin" if is_admin else "mgr"
    st.markdown(f"""
        <div class="tbl-header {cls}">
            <span>Nama</span><span>Posisi</span><span>Divisi</span>
            <span>Atasan</span><span>Aksi</span>
        </div>
    """, unsafe_allow_html=True)

    for u in filtered:
        if is_admin:
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2, 1.8])
        else:
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2, 1])

        c1.markdown(f"**{u['nama']}**")
        c2.caption(u["role"])
        c3.markdown(f'<span class="div-badge">{u["divisi"]}</span>', unsafe_allow_html=True)
        c4.caption(u["nama_atasan"] if u["nama_atasan"] else "—")

        if is_admin:
            b1, b2 = c5.columns(2)
            if b1.button(":material/edit:", key=f"edit_{u['id']}", type="primary", use_container_width=True):
                st.session_state["edit_user_id"] = u["id"]
                st.rerun()
            # Pakai key unik biar bisa di-style
            if b2.button(":material/delete:", key=f"del_btn_{u['id']}", use_container_width=True):
                if u["id"] == current["id"]:
                    st.error("Tidak bisa menghapus akun sendiri.")
                else:
                    uid = u["id"]
                    execute_query("DELETE FROM feedback WHERE submission_id IN (SELECT id FROM submissions WHERE task_id IN (SELECT id FROM tasks WHERE assigned_to=? OR assigned_by=?))", (uid, uid))
                    execute_query("DELETE FROM submissions WHERE task_id IN (SELECT id FROM tasks WHERE assigned_to=? OR assigned_by=?)", (uid, uid))
                    execute_query("DELETE FROM deadline_history WHERE task_id IN (SELECT id FROM tasks WHERE assigned_to=? OR assigned_by=?) OR changed_by=?", (uid, uid, uid))
                    execute_query("DELETE FROM tasks WHERE assigned_to=? OR assigned_by=?", (uid, uid))
                    execute_query("DELETE FROM routine_logbooks WHERE user_id=?", (uid,))
                    execute_query("DELETE FROM users WHERE id=?", (uid,))
                    st.session_state["manage_msg"] = f"Akun {u['nama']} berhasil dihapus."
                    st.rerun()
        else:
            if c5.button(":material/edit:", key=f"edit_{u['id']}", type="primary", use_container_width=True):
                st.session_state["edit_user_id"] = u["id"]
                st.rerun()


def render_edit_form():
    target_id    = st.session_state["edit_user_id"]
    user_to_edit = fetch_one("SELECT * FROM users WHERE id = ?", (target_id,))
    current      = st.session_state["user"]

    if current["divisi"] not in ["Dewan Direksi", "Umum & Personalia", "Business Development"]:
        if user_to_edit["divisi"] != current["divisi"]:
            st.error("Tidak bisa mengedit data dari divisi lain.")
            st.stop()

    st.markdown("""
        <div class="header-card">
            <h2>Edit Data Pengguna</h2>
            <p>Perbarui informasi akun karyawan di bawah ini.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"Mengedit akun: **{user_to_edit['nama']}**")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            new_nama = st.text_input("Nama Lengkap", value=user_to_edit["nama"])
            try:   role_idx = LIST_ROLE.index(user_to_edit["role"])
            except: role_idx = 0
            new_role = st.selectbox("Posisi / Jabatan", LIST_ROLE, index=role_idx)

        with col2:
            try:   div_idx = LIST_DIVISI.index(user_to_edit["divisi"])
            except: div_idx = 0
            new_divisi = st.selectbox("Divisi", LIST_DIVISI, index=div_idx)

            # Atasan
            if "Direktur" in new_role:
                new_atasan_id = None
                st.caption("Jabatan Direktur tidak memiliki atasan.")
            else:
                if current["divisi"] in ["Dewan Direksi", "Umum & Personalia", "Business Development"]:
                    atasan_data = fetch_all("SELECT id, nama FROM users WHERE id != ?", (target_id,))
                else:
                    atasan_data = fetch_all("SELECT id, nama FROM users WHERE id != ? AND divisi = ?", (target_id, current["divisi"]))

                atasan_options = {a["nama"]: a["id"] for a in atasan_data}
                atasan_list    = ["-"] + list(atasan_options.keys())

                current_atasan = "-"
                for name, id_ in atasan_options.items():
                    if id_ == user_to_edit["atasan_id"]:
                        current_atasan = name
                try:   atasan_idx = atasan_list.index(current_atasan)
                except: atasan_idx = 0

                sel_atasan    = st.selectbox("Atasan Langsung", atasan_list, index=atasan_idx)
                new_atasan_id = atasan_options.get(sel_atasan)

        st.markdown("<hr style='border-color:#E2E8F0; margin:16px 0'>", unsafe_allow_html=True)

        b1, b2 = st.columns([3, 1])
        if b1.button(":material/save: Simpan Perubahan", type="primary", use_container_width=True):
            execute_query(
                "UPDATE users SET nama=?, role=?, divisi=?, atasan_id=? WHERE id=?",
                (new_nama, new_role, new_divisi, new_atasan_id, target_id)
            )
            st.session_state["edit_user_id"] = None
            st.session_state["manage_msg"]   = f"Data {new_nama} berhasil diperbarui."
            st.rerun()

        if b2.button(":material/close: Batal", use_container_width=True):
            st.session_state["edit_user_id"] = None
            st.rerun()
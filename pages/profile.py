import streamlit as st
from database import execute_query

LIST_ROLE   = ["Direktur Utama","Direktur","Promosi & CS","Business Development",
               "Sekretaris Direksi","Manager Marketing","Manager Umum & Personalia",
               "Manager Keuangan","Manager Teknik","Kabag. Promosi & CS",
               "Supervisor Civil & Architectural"]
LIST_DIVISI = ["Dewan Direksi","Promosi & CS","Business Development","Sekretaris Direksi",
               "Marketing","Umum & Personalia","Keuangan","Teknik"]

ADMIN_ROLES = ["Direktur Utama","Direktur","Manager Umum & Personalia","Business Development"]

def show_profile():
    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px; border-radius: 16px; margin-bottom: 24px;
            border: 1px solid rgba(16,185,129,0.2);
        }
        .header-card h2 { margin:0 0 4px 0; font-size:22px; font-weight:600; color:white !important; }
        .header-card p  { margin:0; font-size:13px; color:#94A3B8 !important; }

        .avatar {
            width:64px; height:64px; border-radius:50%;
            background:linear-gradient(135deg,#10B981,#059669);
            display:flex; align-items:center; justify-content:center;
            font-size:24px; font-weight:700; color:white; margin-bottom:12px;
        }
        .info-chip {
            display:inline-block; background:#F1F5F9; color:#475569;
            padding:4px 12px; border-radius:20px;
            font-size:12px; font-weight:500; margin:2px 0;
        }
        section.main .stButton > button {
            background:linear-gradient(135deg,#10B981,#059669) !important;
            color:white !important; border:none !important;
            font-weight:600 !important; border-radius:10px !important;
        }
        section.main .stButton > button:hover { opacity:0.9 !important; }
        </style>
    """, unsafe_allow_html=True)

    user     = st.session_state["user"]
    is_admin = user["role"] in ADMIN_ROLES

    if "success_msg" in st.session_state:
        st.success(st.session_state.pop("success_msg"))

    initials = "".join([w[0].upper() for w in user["nama"].split()[:2]])

    st.markdown("""
        <div class="header-card">
            <h2>Profil Saya</h2>
            <p>Kelola informasi akun dan keamanan login Anda.</p>
        </div>
    """, unsafe_allow_html=True)

    # ── Info card ──
    with st.container(border=True):
        av_col, info_col = st.columns([1, 5])
        with av_col:
            st.markdown(f'<div class="avatar">{initials}</div>', unsafe_allow_html=True)
        with info_col:
            st.markdown(f"### {user['nama']}")
            st.markdown(f"""
                <span class="info-chip">{user['role']}</span>
                <span class="info-chip">{user['divisi']}</span>
                <span class="info-chip">@{user['username']}</span>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Form edit ──
    with st.container(border=True):
        st.markdown("**Edit Informasi**")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            new_nama = st.text_input("Nama Lengkap", value=user["nama"])
            st.text_input("Username", value=user["username"], disabled=True,
                          help="Username bersifat permanen dan tidak dapat diubah.")

        with c2:
            if is_admin:
                try:   role_idx = LIST_ROLE.index(user["role"])
                except: role_idx = 0
                new_role = st.selectbox("Posisi / Jabatan", LIST_ROLE, index=role_idx)

                try:   div_idx = LIST_DIVISI.index(user["divisi"])
                except: div_idx = 0
                new_divisi = st.selectbox("Divisi", LIST_DIVISI, index=div_idx)
            else:
                st.text_input("Posisi / Jabatan", value=user["role"], disabled=True,
                              help="Jabatan hanya dapat diubah oleh admin.")
                st.text_input("Divisi", value=user["divisi"], disabled=True,
                              help="Divisi hanya dapat diubah oleh admin.")
                new_role   = user["role"]
                new_divisi = user["divisi"]

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown("**Keamanan**")
        st.caption("Biarkan kosong jika tidak ingin mengganti password.")

        p1, p2 = st.columns(2)
        with p1: new_password     = st.text_input("Password Baru", type="password", placeholder="Masukkan password baru...")
        with p2: confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password baru...")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button(":material/save: Simpan Perubahan", use_container_width=True):
            if new_password and new_password != confirm_password:
                st.error("Password baru dan konfirmasi tidak cocok.")
            else:
                try:
                    if new_password:
                        execute_query(
                            "UPDATE users SET nama=?, password=?, role=?, divisi=? WHERE id=?",
                            (new_nama, new_password, new_role, new_divisi, user["id"])
                        )
                    else:
                        execute_query(
                            "UPDATE users SET nama=?, role=?, divisi=? WHERE id=?",
                            (new_nama, new_role, new_divisi, user["id"])
                        )
                    st.session_state["user"]["nama"]   = new_nama
                    st.session_state["user"]["role"]   = new_role
                    st.session_state["user"]["divisi"] = new_divisi
                    st.session_state["success_msg"]    = "Profil berhasil diperbarui!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
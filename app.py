import streamlit as st
from database import init_db
from login import show_login
from register import show_register

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Tracking Jobdesc", layout="wide", page_icon="📋")

init_db()

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state["user"] = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# =========================
# MAIN APP
# =========================
def show_main_app():
    st.markdown("""
        <style>
            /* ── Sidebar base ── */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
                border-right: 1px solid rgba(148, 163, 184, 0.08) !important;
            }

            /* Sembunyikan navigasi bawaan */
            [data-testid="stSidebarNav"] { display: none !important; }

            /* ── Tombol menu sidebar ── */
            [data-testid="stSidebar"] .stButton > button {
                width: 100%;
                border-radius: 10px;
                border: 1px solid transparent;
                background-color: transparent;
                color: #94A3B8 !important;
                text-align: left;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 400;
                transition: all 0.2s ease;
            }

            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: rgba(148, 163, 184, 0.08) !important;
                color: #F1F5F9 !important;
                border-color: transparent !important;
            }

            /* Tombol aktif — emerald accent */
            [data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background-color: rgba(16, 185, 129, 0.12) !important;
                color: #10B981 !important;
                border: 1px solid rgba(16, 185, 129, 0.25) !important;
                font-weight: 500 !important;
            }

            /* ── Tombol Logout ── */
            [data-testid="stSidebar"] .st-key-btn_logout button {
                background-color: transparent !important;
                color: #64748B !important;
                border: 1px solid rgba(148, 163, 184, 0.15) !important;
                margin-top: 8px;
            }

            [data-testid="stSidebar"] .st-key-btn_logout button:hover {
                background-color: rgba(239, 68, 68, 0.08) !important;
                color: #FCA5A5 !important;
                border-color: rgba(239, 68, 68, 0.25) !important;
            }

            /* ── User info card ── */
            .user-info-box {
                background: rgba(16, 185, 129, 0.06);
                padding: 14px 16px;
                border-radius: 12px;
                border: 1px solid rgba(16, 185, 129, 0.15);
                margin-bottom: 12px;
            }

            /* ── Main content area ── */
            [data-testid="stAppViewContainer"] > .main {
                background-color: #F8FAFC;
            }

            /* Divider sidebar */
            .sidebar-divider {
                border: none;
                border-top: 1px solid rgba(148, 163, 184, 0.1);
                margin: 12px 0;
            }
        </style>
    """, unsafe_allow_html=True)

    user = st.session_state["user"]
    role = user["role"]

    # --- MENU PER ROLE ---
    if role in ["Business Development", "Manager Umum & Personalia"]:
        menu_items = [
            ("Dashboard",       "dashboard"),
            ("Tugas Saya",      "task"),
            ("Buat Tugas",      "assignment_add"),
            ("Kelola Pengguna", "group"),
            ("Profil",          "person"),
        ]
    elif role in ["Direktur Utama", "Direktur"]:
        menu_items = [
            ("Dashboard",  "dashboard"),
            ("Buat Tugas", "assignment_add"),
            ("Monitoring", "monitoring"),
            ("Kelola Pengguna", "group"),
            ("Profil",     "person"),
        ]
    else:
        menu_items = [
            ("Dashboard",  "dashboard"),
            ("Tugas Saya", "task"),
            ("Buat Tugas", "assignment_add"),
            ("Profil",     "person"),
        ]

    # ── SIDEBAR ──
    with st.sidebar:
        # Header
        st.markdown("""
            <div style='padding: 8px 4px 16px 4px;'>
                <p style='margin:0; font-size:11px; font-weight:600;
                          letter-spacing:0.1em; color:#475569;'>TRACKING JOBDESC</p>
            </div>
        """, unsafe_allow_html=True)

        # Navigasi
        for name, icon in menu_items:
            is_active = st.session_state.current_page == name
            if st.button(
                name,
                icon=f":material/{icon}:",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"nav_{name}"
            ):
                st.session_state.current_page = name
                st.rerun()

        # Spacer fleksibel
        st.markdown("<div style='flex:1; min-height: 40px;'></div>", unsafe_allow_html=True)

        # Divider
        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        # User info
        initials = "".join([w[0].upper() for w in user['nama'].split()[:2]])
        st.markdown(f"""
            <div class="user-info-box">
                <div style='display:flex; align-items:center; gap:10px;'>
                    <div style='width:36px; height:36px; border-radius:50%;
                                background: linear-gradient(135deg, #10B981, #059669);
                                display:flex; align-items:center; justify-content:center;
                                font-size:13px; font-weight:600; color:white; flex-shrink:0;'>
                        {initials}
                    </div>
                    <div style='overflow:hidden;'>
                        <p style='margin:0; font-size:13px; font-weight:600;
                                  color:#F1F5F9; white-space:nowrap;
                                  overflow:hidden; text-overflow:ellipsis;'>{user['nama']}</p>
                        <p style='margin:0; font-size:11px; color:#64748B;
                                  white-space:nowrap; overflow:hidden;
                                  text-overflow:ellipsis;'>{role}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Keluar", icon=":material/logout:", use_container_width=True, key="btn_logout"):
            st.session_state["user"] = None
            st.session_state.current_page = "Dashboard"
            st.rerun()

    # ── RENDER HALAMAN ──
    choice = st.session_state.current_page

    if choice == "Dashboard":
        from pages.dashboard import show_dashboard
        show_dashboard()
    elif choice == "Tugas Saya":
        from pages.my_task import show_my_task
        show_my_task()
    elif choice == "Buat Tugas":
        from pages.assign_task import show_assign_task
        show_assign_task()
    elif choice == "Monitoring":
        from pages.monitoring import show_monitoring
        show_monitoring()
    elif choice == "Profil":
        from pages.profile import show_profile
        show_profile()
    elif choice == "Kelola Pengguna":
        from pages.manage_users import show_manage_users
        show_manage_users()

# ── ROUTER ──
if st.session_state.user is None:
    if st.session_state.auth_mode == "login":
        show_login()
    else:
        show_register()
else:
    show_main_app()
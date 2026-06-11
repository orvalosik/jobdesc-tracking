import streamlit as st
from database import init_db
from login import show_login
from register import show_register

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Tracking Jobdesc", layout="wide")

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
# MAIN APP (SETELAH LOGIN)
# =========================
def show_main_app():
    # 🎨 Custom CSS for Navy Gradient Sidebar & Uniform Buttons (SCOPED)
    st.markdown("""
        <style>
            /* 1. Background Sidebar Navy Gradient */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0D1B2A 0%, #1B263B 100%) !important;
                color: white;
            }

            /* 2. Sembunyikan Navigasi Bawaan Streamlit */
            [data-testid="stSidebarNav"] { display: none !important; }

            /* 3. Styling Tombol Menu AGAR HANYA BERAKSI DI SIDEBAR */
            [data-testid="stSidebar"] .stButton > button {
                width: 100%;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.1);
                background-color: rgba(255,255,255,0.05);
                color: white !important;
                text-align: left;
                padding: 10px 20px;
                transition: all 0.3s ease;
            }

            /* 4. Efek Hover & Active HANYA DI SIDEBAR (Warna Biru Navy Terang / Abu) */
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: #415A77 !important;
                border-color: #778DA9 !important;
            }
            
            /* Warna saat tombol terpilih (Active) HANYA DI SIDEBAR */
            [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(button[kind="primary"]) > div {
                background: transparent !important;
            }
            
            [data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background-color: #415A77 !important;
                border: 1px solid #778DA9 !important;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
            }

            /* 5. Styling Teks User di Bawah */
            .user-info-box {
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #E0E1DD;
                margin-top: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    user = st.session_state["user"]
    role = user["role"]

    # --- LOGIKA OTORISASI & ICON ---
    if role in ["Business Development", "Manager Umum & Personalia"]:
        menu_items = [("Dashboard", "dashboard"), ("Tugas Saya", "task"), ("Kelola Pengguna", "group"), ("Profil", "person")]
    elif role in ["Direktur Utama", "Direktur"]:
        menu_items = [("Dashboard", "dashboard"), ("Buat Tugas", "assignment_add"), ("Monitoring", "monitoring"), ("Kelola Pengguna", "group"), ("Profil", "person")]
    else:
        menu_items = [("Dashboard", "dashboard"), ("Tugas Saya", "task"), ("Profil", "person")]

    # ✅ SIDEBAR CONTENT
    with st.sidebar:
        st.markdown("<h2 style='color:white; text-align:center;'>📋 Menu Utama</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Loop Tombol Navigasi
        for name, icon in menu_items:
            is_active = st.session_state.current_page == name
            if st.button(name, icon=f":material/{icon}:", use_container_width=True, 
                         type="primary" if is_active else "secondary"):
                st.session_state.current_page = name
                st.rerun()

        # Spacer agar info user nempel di bawah
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # INFO USER (Paling Bawah)
        st.markdown(f"""
            <div class="user-info-box">
                <p style='margin:0; font-size:12px; color:#778DA9;'>LOGGED IN AS</p>
                <p style='margin:0; font-size:16px; font-weight:bold; color:white;'>{user['nama']}</p>
                <p style='margin:0; font-size:13px; color:#E0E1DD;'>{role}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", icon=":material/logout:", use_container_width=True):
            st.session_state["user"] = None
            st.session_state.current_page = "Dashboard"
            st.rerun()

    # =========================
    # RENDER CONTENT
    # =========================
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

# --- ROUTER ---
if st.session_state.user is None:
    if st.session_state.auth_mode == "login":
        show_login()
    else:
        show_register()
else:
    show_main_app()
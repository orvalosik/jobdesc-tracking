import streamlit as st
import base64
from database import execute_query, fetch_all
import sqlite3

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def show_register():
    try:
        bg_str = get_base64_of_bin_file('bg_rubang.png')
        logo_str = get_base64_of_bin_file('jdc_logo.png')
    except FileNotFoundError:
        bg_str = ""
        logo_str = ""

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{display: none;}}

        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{bg_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            z-index: 0;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            position: relative;
            z-index: 1;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: rgba(30, 41, 59, 0.75) !important;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px !important;
            padding: 36px !important;
            border: 1px solid rgba(148, 163, 184, 0.15) !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
        }}

        label, .stMarkdown p {{
            color: #CBD5E1 !important;
            font-size: 14px !important;
        }}

        h2 {{
            color: #F1F5F9 !important;
            font-weight: 600 !important;
        }}

        /* Input & Selectbox */
        .stTextInput input {{
            background-color: rgba(15, 23, 42, 0.6) !important;
            color: #F1F5F9 !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            border-radius: 10px !important;
            padding: 10px 14px !important;
        }}

        .stTextInput input::placeholder {{
            color: #64748B !important;
        }}

        .stTextInput input:focus {{
            border-color: #10B981 !important;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
        }}

        /* Selectbox */
        .stSelectbox > div > div {{
            background-color: rgba(15, 23, 42, 0.6) !important;
            color: #F1F5F9 !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            border-radius: 10px !important;
        }}

        /* Tombol Daftar — emerald */
        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            background: linear-gradient(135deg, #10B981, #059669) !important;
            color: white !important;
            width: 100% !important;
            height: 3.2rem !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            border: none !important;
            letter-spacing: 0.5px;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {{
            opacity: 0.9 !important;
        }}

        /* Tombol Kembali — outline */
        .st-key-btn_back button {{
            background-color: transparent !important;
            color: #94A3B8 !important;
            width: 100% !important;
            height: 2.8rem !important;
            border-radius: 10px !important;
            border: 1px solid rgba(148, 163, 184, 0.3) !important;
            font-size: 14px !important;
            margin-top: 8px !important;
            transition: all 0.2s ease;
        }}

        .st-key-btn_back button:hover {{
            background-color: rgba(148, 163, 184, 0.08) !important;
            border-color: rgba(148, 163, 184, 0.5) !important;
            color: #F1F5F9 !important;
        }}
        
        /* Sembunyikan toolbar atas (Fork, GitHub, dll) */
        [data-testid="stToolbar"] {{ display: none !important; }}

        /* Sembunyikan footer bawah (Made with Streamlit) */
        footer {{ display: none !important; }}

        /* Sembunyikan header Streamlit */
        [data-testid="stHeader"] {{ display: none !important; }}

        /* Sembunyikan decoration atas */
        [data-testid="stDecoration"] {{ display: none !important; }}
        </style>
    """, unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 2.5, 1])

    with col_mid:
        with st.container(border=True):
            if logo_str:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 16px;">
                        <img src="data:image/png;base64,{logo_str}" width="100"
                             style="border-radius: 12px; opacity: 0.95;">
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("""
                <h2 style='text-align: center; margin-top: 0; margin-bottom: 4px;'>
                    Buat Akun Baru
                </h2>
                <p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 20px;'>
                    Lengkapi data di bawah untuk mendaftar
                </p>
            """, unsafe_allow_html=True)

            nama     = st.text_input("Nama Lengkap", placeholder="Masukkan nama lengkap Anda")
            username = st.text_input("Username", placeholder="Buat username")
            password = st.text_input("Password", type="password", placeholder="Buat password")

            c1, c2 = st.columns(2)
            with c1:
                role = st.selectbox("Posisi / Jabatan", [
                    "Direktur Utama", "Direktur", "Promosi & CS",
                    "Business Development", "Sekretaris Direksi",
                    "Manager Marketing", "Manager Umum & Personalia",
                    "Manager Keuangan", "Manager Teknik",
                    "Kabag. Promosi & CS", "Supervisor Civil & Architectural"
                ])
            with c2:
                divisi = st.selectbox("Divisi", [
                    "Dewan Direksi", "Promosi & CS", "Business Development",
                    "Sekretaris Direksi", "Marketing", "Umum & Personalia",
                    "Keuangan", "Teknik"
                ])

            atasan_list = fetch_all("SELECT id, nama FROM users")
            atasan_dict = {"-": None}
            for a in atasan_list:
                atasan_dict[a["nama"]] = a["id"]

            selected_atasan = st.selectbox(
                "Atasan Langsung",
                list(atasan_dict.keys()),
                disabled=(divisi == "Dewan Direksi"),
                help="Kosongkan jika tidak memiliki atasan (Dewan Direksi)"
            )
            atasan_id = None if divisi == "Dewan Direksi" else atasan_dict[selected_atasan]

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            if st.button("Daftar Sekarang", use_container_width=True):
                if not nama or not username or not password:
                    st.warning("Semua field wajib diisi.")
                else:
                    try:
                        execute_query(
                            "INSERT INTO users (nama, username, password, role, divisi, atasan_id) VALUES (?, ?, ?, ?, ?, ?)",
                            (nama, username, password, role, divisi, atasan_id)
                        )
                        st.success("Akun berhasil dibuat! Silakan login.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username sudah digunakan, coba yang lain.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")

        st.markdown("""
            <p style='text-align: center; margin-top: 20px; color: #64748B; font-size: 13px;'>
                Sudah punya akun?
            </p>
        """, unsafe_allow_html=True)

        if st.button("Kembali ke Login", key="btn_back", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
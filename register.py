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

        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 25px !important;
            padding: 40px !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        }}

        label, .stMarkdown p, h2 {{
            color: white !important;
        }}

        /* Tombol Daftar Sekarang */
        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            background-color: #28a745 !important;
            color: white !important;
            width: 100% !important;
            height: 3.5rem !important;
            border-radius: 10px !important;
            font-weight: bold !important;
        }}

        /* Tombol Kembali ke Login */
        .st-key-btn_back button {{
            background-color: #415A77 !important;
            color: white !important;
            width: 100% !important;
            height: 3rem !important;
            border-radius: 10px !important;
            margin-top: 10px !important;
        }}

        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #1B263B !important;
            border-radius: 10px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 2.5, 1])

    with col_mid:
        with st.container(border=True):
            # Tampilkan Logo Perusahaan
            if logo_str:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 10px;">
                        <img src="data:image/png;base64,{logo_str}" width="120">
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<h2 style='text-align: center; margin-top: 0;'>Register</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #f0f0f0;'>Buat akun baru</p>", unsafe_allow_html=True)
            
            nama = st.text_input("Nama", placeholder="Masukkan nama lengkap Anda")
            username = st.text_input("Username", placeholder="Buat username")
            password = st.text_input("Password", type="password", placeholder="Buat password")
            
            c1, c2 = st.columns(2)
            with c1:
                role = st.selectbox("Posisi", ["Direktur Utama","Direktur","Promosi & CS","Business Development","Sekretaris Direksi","Manager Marketing", "Manager Umum & Personalia", "Manager Keuangan", "Manager Teknik", "Kabag. Seminar","Kabag. Personalia", "Kabag. Administrasi Keuangan", "Kabag. Penagihan", "Kabag. Akunting & Pajak","Kabag. Teknik","Kabag. Promosi & CS", "Supervisor ME","Supervisor Civil & Architectural", "Staff Administrasi Marketing","Staff Administrasi Seminar","Staff JDC Business Center","Staff Security","Staff Personalia/Spv. Security & Parkir","Staff Legal & Umum","Staff Fungsional Umum","Staff Receptionist","Staff Fungsional Penagihan","Staff Keuangan","Staff Kasir","Staff Invoice","Staff Admin Teknik"])
            with c2:
                divisi = st.selectbox("Divisi", ["Dewan Direksi", "Promosi & CS", "Business Development", "Sekretaris Direksi", "Marketing", "Umum & Personalia", "Keuangan", "Teknik"])

            atasan_list = fetch_all("SELECT id, nama FROM users")
            atasan_dict = {"-": None}
            for a in atasan_list:
                atasan_dict[a["nama"]] = a["id"]

            selected_atasan = st.selectbox("Pilih Atasan", list(atasan_dict.keys()), disabled=(divisi == "Dewan Direksi"))
            atasan_id = None if divisi == "Dewan Direksi" else atasan_dict[selected_atasan]

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Daftar Sekarang"):
                if not nama or not username or not password:
                    st.warning("Mohon lengkapi data Anda!")
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
                        # Ini khusus kalau username duplikat (Unique Constraint)
                        st.error("Username sudah digunakan, silakan pilih yang lain.")
                    except Exception as e:
                        # Ini untuk menangkap error database lainnya secara umum
                        st.error(f"Terjadi kesalahan database: {e}")

        st.markdown("<p style='text-align: center; margin-top:20px; font-weight:bold;'>Sudah memiliki akun?</p>", unsafe_allow_html=True)
        if st.button("Kembali ke Login", key="btn_back"):
            st.session_state.auth_mode = "login"
            st.rerun()
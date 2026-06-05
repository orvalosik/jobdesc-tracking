import streamlit as st
import base64
from auth import login_user
from database import fetch_one

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def show_login():
    # Load background & logo
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

        /* Glassmorphism Card */
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
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}

        /* Tombol Login */
        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            background-color: #28a745 !important;
            color: white !important;
            width: 100% !important;
            height: 3.5rem !important;
            border-radius: 10px !important;
            font-weight: bold !important;
        }}

        /* Tombol Daftar Akun */
        .st-key-btn_reg button {{
            background-color: #415A77 !important;
            color: white !important;
            width: 100% !important;
            height: 3rem !important;
            border-radius: 10px !important;
            margin-top: 10px !important;
        }}

        .stTextInput input {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #1B263B !important;
            border-radius: 10px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 2, 1])

    with col_mid:
        with st.container(border=True):
            # Tampilkan Logo Perusahaan
            if logo_str:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 10px;">
                        <img src="data:image/png;base64,{logo_str}" width="120">
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<h2 style='text-align: center; margin-top: 0;'>Sistem Informasi Tracking Jobdesc</h2>", unsafe_allow_html=True)
                        
            username = st.text_input("Username", placeholder="Masukkan Username Anda")
            password = st.text_input("Password", type="password", placeholder="Masukkan Password Anda")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("LOGIN"):
                user_check = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
                if not user_check:
                    st.error("Username belum terdaftar!")
                else:
                    user = login_user(username, password)
                    if user:
                        st.session_state.user = dict(user)
                        st.success("Login berhasil!")
                        st.rerun()
                    else:
                        st.error("Password salah!")

        st.markdown("<p style='text-align: center; margin-top:20px; font-weight:bold;'>Belum memiliki akun? Daftar di sini</p>", unsafe_allow_html=True)
        if st.button("REGISTER", key="btn_reg"):
            st.session_state.auth_mode = "register"
            st.rerun()
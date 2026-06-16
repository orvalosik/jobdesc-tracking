import streamlit as st
import base64
from auth import login_user
from database import fetch_one

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def show_login():
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

        /* Dark overlay supaya card lebih pop */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            z-index: 0;
        }}

        /* Pastikan konten di atas overlay */
        [data-testid="stAppViewBlockContainer"] {{
            position: relative;
            z-index: 1;
        }}

        /* Card glassmorphism — slate tone */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: rgba(30, 41, 59, 0.75) !important;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px !important;
            padding: 36px !important;
            border: 1px solid rgba(148, 163, 184, 0.15) !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
        }}

        /* Label & teks */
        label, .stMarkdown p {{
            color: #CBD5E1 !important;
            font-size: 14px !important;
        }}

        h2 {{
            color: #F1F5F9 !important;
            font-weight: 600 !important;
        }}

        /* Input field */
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

        /* Tombol LOGIN — emerald */
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
            transition: opacity 0.2s ease;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {{
            opacity: 0.9 !important;
        }}

        /* Tombol REGISTER — slate outline */
        .st-key-btn_reg button {{
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

        .st-key-btn_reg button:hover {{
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

    _, col_mid, _ = st.columns([1, 2, 1])

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
                    Tracking Jobdesc
                </h2>
                <p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 24px;'>
                    Masuk untuk melanjutkan
                </p>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", placeholder="Masukkan username Anda")
            password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            if st.button("Masuk", use_container_width=True):
                if not username or not password:
                    st.warning("Username dan password wajib diisi.")
                else:
                    user_check = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
                    if not user_check:
                        st.error("Username tidak ditemukan.")
                    else:
                        user = login_user(username, password)
                        if user:
                            st.session_state.user = dict(user)
                            st.rerun()
                        else:
                            st.error("Password salah.")

        st.markdown("""
            <p style='text-align: center; margin-top: 20px; color: #64748B; font-size: 13px;'>
                Belum punya akun?
            </p>
        """, unsafe_allow_html=True)

        if st.button("Daftar Sekarang", key="btn_reg", use_container_width=True):
            st.session_state.auth_mode = "register"
            st.rerun()
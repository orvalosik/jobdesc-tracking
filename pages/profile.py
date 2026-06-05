import streamlit as st
from database import execute_query

def show_profile():
    # 🎨 Custom CSS untuk UI yang lebih dewasa & profesional
    st.markdown("""
        <style>
        .main {
            background-color: #f8f9fa;
        }
        .profile-card {
            background: linear-gradient(135deg, #1B263B 0%, #415A77 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .stButton>button {
            background-color: #1B263B;
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #778DA9;
            color: white;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("👤 Pengaturan Profil")
    
    # Ambil data user dari session state 
    user = st.session_state["user"]

    # 🏢 Card Header
    st.markdown(f"""
        <div class="profile-card">
            <h3>{user['nama']}</h3>
            <p style='margin-bottom:0;'>Role: <b>{user['role'].upper()}</b> | Divisi: {user['divisi']}</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.subheader("Informasi Personal")
        col1, col2 = st.columns(2)

        with col1:
            # Pastikan semua kolom membawa value terakhir dari database 
            new_nama = st.text_input("Nama Lengkap", value=user["nama"])
            # Username biasanya unik, kita tampilkan sebagai read-only untuk keamanan
            st.text_input("Username", value=user["username"], disabled=True, help="Username tidak dapat diubah.")
        
        with col2:
            list_divisi = ["Dewan Direksi", "Promosi & CS", "Business Development", "Sekretaris Direksi", "Marketing", "Umum & Personalia", "Keuangan", "Teknik"]
            
            # Cari index divisi user saat ini di dalam list
            try:
                current_index = list_divisi.index(user["divisi"])
            except ValueError:
                # Jika divisi lama tidak ada di list baru, default ke index 0
                current_index = 0
            
            new_divisi = st.selectbox("Divisi", list_divisi, index=current_index)
            new_password = st.text_input("Password Baru (Biarkan jika tidak ingin ganti)", value=user["password"], type="password")

    st.markdown("---")
    
# Tombol Update
    if st.button("Simpan Perubahan"):
        try:
            if new_password:
                execute_query(
                    "UPDATE users SET nama=?, password=?, divisi=? WHERE id=?",
                    (new_nama, new_password, new_divisi, user["id"])
                )
            else:
                execute_query(
                    "UPDATE users SET nama=?, divisi=? WHERE id=?",
                    (new_nama, new_divisi, user["id"])
                )

            # Update session state user agar UI langsung berubah
            st.session_state["user"]["nama"] = new_nama
            st.session_state["user"]["divisi"] = new_divisi
            
            # 2. Simpan pesan ke session state sebelum rerun
            st.session_state["success_msg"] = "Profil berhasil diperbarui! ✅"
            
            # 3. Rerun untuk memperbarui seluruh tampilan UI
            st.rerun()
            
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
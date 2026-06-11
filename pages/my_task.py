import streamlit as st
import os
import pandas as pd
from database import fetch_all, execute_query
from datetime import datetime, date, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# =========================================================================
# 🤖 FUNGSI PEMBANTU: UPLOAD KE GOOGLE DRIVE (AUTO-SWITCH SIMULASI LOKAL)
# =========================================================================
def upload_to_google_drive(uploaded_file, filename_on_drive, divisi_name):
    """
    Upload file ke Google Drive dan otomatis membuat folder divisi jika belum ada.
    """

    ROOT_FOLDER_ID = "11sU-BVtM-VLhKPKYChDyXwgeaHcWG0xg"

    try:
        SCOPES = ["https://www.googleapis.com/auth/drive.file"]

        creds = Credentials(
            token=None,
            refresh_token=st.secrets["gdrive_oauth"]["refresh_token"],
            token_uri=st.secrets["gdrive_oauth"]["token_uri"],
            client_id=st.secrets["gdrive_oauth"]["client_id"],
            client_secret=st.secrets["gdrive_oauth"]["client_secret"],
            scopes=SCOPES
        )

        creds.refresh(Request())

        service = build(
            "drive",
            "v3",
            credentials=creds
        )

        def get_or_create_folder(folder_name, parent_folder_id=None):
            query = (
                f"name='{folder_name}' "
                f"and mimeType='application/vnd.google-apps.folder' "
                f"and trashed=false"
            )

            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            results = service.files().list(
                q=query,
                fields="files(id,name)"
            ).execute()

            folders = results.get("files", [])

            if folders:
                return folders[0]["id"]

            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id]
            }

            folder = service.files().create(
                body=folder_metadata,
                fields="id"
            ).execute()

            return folder["id"]

        divisi_folder_id = get_or_create_folder(
            divisi_name,
            ROOT_FOLDER_ID
        )

        file_metadata = {
            "name": filename_on_drive,
            "parents": [divisi_folder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getvalue()),
            mimetype=uploaded_file.type
        )

        uploaded_drive_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink"
        ).execute()

        service.permissions().create(
            fileId=uploaded_drive_file["id"],
            body={
                "type": "anyone",
                "role": "reader"
            }
        ).execute()

        return uploaded_drive_file["webViewLink"]

    except Exception as e:
        st.error(f"❌ Gagal mengunggah berkas ke Google Drive Server: {e}")
        return None


# =========================================================================
# 📋 UTAMA: HALAMAN TUGAS SAYA
# =========================================================================
def show_my_task():
    if st.session_state.get("trigger_success_balloons", False):
        st.balloons()
        st.session_state["trigger_success_balloons"] = False

    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
            padding: 20px; border-radius: 12px; color: white; margin-bottom: 25px;
        }
        .task-card {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1B263B; box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        
        section.main div[data-testid="stFormSubmitButton"] > button,
        section.main button[kind="primary"] {
            background-color: #1B263B !important; color: white !important;
            border: 1px solid #1B263B !important; border-radius: 6px !important;
        }
        section.main div[data-testid="stFormSubmitButton"] > button:hover,
        section.main button[kind="primary"]:hover {
            background-color: #415A77 !important; border-color: #778DA9 !important;
        }
        section.main div.stButton > button:not([kind="primary"]):not([key^="cancel_"]) {
            background-color: #1B263B !important; color: white !important;
            border: 1px solid #1B263B !important; border-radius: 6px !important;
        }
        section.main div.stButton > button:not([kind="primary"]):not([key^="cancel_"]):hover {
            background-color: #415A77 !important; border-color: #778DA9 !important;
        }
        section.main div.stButton > button[key^="cancel_"] {
            background-color: #E63946 !important; color: white !important;
            border: 1px solid #E63946 !important; border-radius: 6px !important;
        }
        section.main div.stButton > button[key^="cancel_"] p { color: white !important; }
        section.main div.stButton > button[key^="cancel_"]:hover { 
            background-color: #C1121F !important; border-color: #C1121F !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.warning("Silakan login terlebih dahulu!")
        st.stop()

    user = st.session_state["user"]

    st.markdown(f"""
        <div class="header-card">
            <h1>📋 Tugas Saya</h1>
            <p>Kelola laporan aktivitas rutin harian dan instruksi khusus dari atasan.</p>
        </div>
    """, unsafe_allow_html=True)

    tab_rutin, tab_non_rutin = st.tabs(["📅 Tugas Rutinitas (Logbook)", "🚀 Tugas Non-Rutinitas (Instruksi Atasan)"])

    # =========================================================================
    # TAB 1: TUGAS RUTINITAS (LOGBOOK)
    # =========================================================================
    with tab_rutin:
        st.subheader("Form Input Logbook")

        col_tgl, col_kategori, col_job = st.columns([1, 1, 2])

        with col_tgl:
            tgl_logbook = st.date_input("Tanggal Aktivitas", value=date.today(), key="input_tgl_logbook")

        with col_kategori:
            kategori_periodik = st.selectbox("Kategori Periodik", ["Harian", "Bulanan", "Tahunan"], key="input_kategori_periodik")

        # Ambil template yang ada di DB
        query_template = """
            SELECT id, nama_tugas FROM jobdesc_templates
            WHERE role = ? AND divisi = ? AND kategori_periodik = ?
            ORDER BY nama_tugas ASC
        """
        templates = fetch_all(query_template, (user["role"], user["divisi"], kategori_periodik))

        # Petakan opsi template yang ada 
        template_options = {t["nama_tugas"]: t["id"] for t in templates}
        options_list = list(template_options.keys())

        with col_job:
            pilihan_tugas = st.selectbox("Judul Pekerjaan", options_list, key="input_pilihan_tugas")

        # Form tetap dirender agar bawahan bisa selalu mengisi secara mandiri
        with st.form(key="form_logbook_rutin", clear_on_submit=True):
            

            keterangan = st.text_area("Keterangan Progres / Hasil Kerja", placeholder="Detailkan aktivitas yang Anda kerjakan...", height=120)
            uploaded_file = st.file_uploader("📎 Lampiran Hasil Kerja (Opsional)", type=["pdf", "xlsx", "xls", "png", "jpg", "jpeg"])

            btn_submit_logbook = st.form_submit_button("💾 Simpan Logbook", use_container_width=True)

            if btn_submit_logbook:
                if not keterangan.strip():
                    st.error("⚠️ Kolom keterangan tidak boleh kosong!")
                else:
                    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # jobdesc_id = None

                    jobdesc_id = template_options[pilihan_tugas]

                    if jobdesc_id:
                        # --- PROSES UPLOAD FILE ---
                        final_link = None
                        if uploaded_file is not None:
                            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename_to_drive = f"Logbook_{user['id']}_{timestamp_str}_{uploaded_file.name}"
                            with st.spinner("Mengunggah lampiran ke Google Drive..."):
                                final_link = upload_to_google_drive(uploaded_file, filename_to_drive, user["divisi"])

                        # --- SIMPAN DATA LOGBOOK ---
                        query_insert = """
                            INSERT INTO routine_logbooks (user_id, tanggal_logbook, jobdesc_id, keterangan_progres, link_file, tanggal_input)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """
                        execute_query(query_insert, (user["id"], str(tgl_logbook), jobdesc_id, keterangan, final_link, now_timestamp))

                        st.success(f"🎉 Logbook {kategori_periodik.lower()} berhasil disimpan!")
                        st.rerun()

        # ============================================================
        # ⏳ RIWAYAT LOGBOOK DENGAN FILTER REAL-TIME
        # ============================================================
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.subheader("⏳ Riwayat Logbook Anda")

        query_job_list = """
            SELECT DISTINCT jt.nama_tugas FROM routine_logbooks rl
            JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id WHERE rl.user_id = ?
        """
        user_jobs_data = fetch_all(query_job_list, (user["id"],))
        job_filter_options = ["Semua Pekerjaan"] + [j["nama_tugas"] for j in user_jobs_data]

        l_col1, l_col2, l_col3 = st.columns([1.2, 1.0, 1.0])
        with l_col1:
            filter_job_logbook = st.selectbox("📌 Filter Judul Pekerjaan", job_filter_options, key="filter_job_lb")
        with l_col2:
            start_date_lb = st.date_input("📅 Dari Tanggal", value=date.today() - timedelta(days=30), key="start_date_lb")
        with l_col3:
            end_date_lb = st.date_input("📅 Sampai Tanggal", value=date.today(), key="end_date_lb")

        query_history = """
            SELECT
                rl.id,
                rl.jobdesc_id,
                rl.tanggal_logbook,
                rl.keterangan_progres,
                rl.link_file,
                rl.tanggal_input,
                jt.nama_tugas,
                jt.kategori_periodik
            FROM routine_logbooks rl
            JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id
            WHERE rl.user_id = ?
            ORDER BY rl.tanggal_logbook DESC, rl.tanggal_input DESC
        """
        history_data = fetch_all(query_history, (user["id"],))

        if history_data:
            if filter_job_logbook != "Semua Pekerjaan":
                history_data = [item for item in history_data if item["nama_tugas"] == filter_job_logbook]
            
            if start_date_lb and end_date_lb:
                filtered_history = []
                for item in history_data:
                    if item["tanggal_logbook"]:
                        try:
                            if isinstance(item["tanggal_logbook"], str):
                                log_date = datetime.strptime(item["tanggal_logbook"][:10], "%Y-%m-%d").date()
                            else:
                                log_date = item["tanggal_logbook"]
                            if start_date_lb <= log_date <= end_date_lb:
                                filtered_history.append(item)
                        except ValueError:
                            continue
                history_data = filtered_history

        # TAMPILKAN RIWAYAT LOGBOOK
        if not history_data:
            st.info("💡 Tidak ada riwayat logbook yang sesuai dengan kriteria filter.")

        else:

            # TABEL RIWAYAT
            table_data = []

            for item in history_data:
                table_data.append({
                    "ID": item["id"],
                    "Tanggal": item["tanggal_logbook"],
                    "Pekerjaan": item["nama_tugas"],
                    "Kategori": item["kategori_periodik"],
                    "Keterangan": (
                        item["keterangan_progres"][:60] + "..."
                        if len(item["keterangan_progres"]) > 60
                        else item["keterangan_progres"]
                    ),
                    "Lampiran": "📎" if item["link_file"] else "-"
                })

            df_history = pd.DataFrame(table_data)

            st.dataframe(
                df_history.drop(columns=["ID"]),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # ==========================
            # PILIH LOGBOOK
            # ==========================
            selected_logbook = st.selectbox(
                "📌 Pilih Logbook",
                history_data,
                format_func=lambda x:
                    f"{x['tanggal_logbook']} | {x['nama_tugas']}"
            )

            st.markdown("### Detail Logbook")

            st.write(
                f"**Tanggal Aktivitas:** {selected_logbook['tanggal_logbook']}"
            )

            st.write(
                f"**Pekerjaan:** {selected_logbook['nama_tugas']}"
            )

            st.write(
                f"**Kategori:** {selected_logbook['kategori_periodik']}"
            )

            st.write("**Keterangan Progres:**")
            st.write(selected_logbook["keterangan_progres"])

            if selected_logbook["link_file"]:
                st.markdown(
                    f"📎 [Buka Lampiran]({selected_logbook['link_file']})"
                )

            st.markdown("")

            # ==========================
            # TOMBOL AKSI
            # ==========================
            col_edit, col_delete = st.columns(2)

            with col_edit:
                if st.button(
                    "✏️ Edit Logbook",
                    use_container_width=True
                ):
                    st.session_state["edit_logbook_id"] = selected_logbook["id"]

            with col_delete:
                if st.button(
                    "🗑️ Hapus Logbook",
                    use_container_width=True
                ):
                    st.session_state["delete_logbook_id"] = selected_logbook["id"]

        # ============================================================
        # KONFIRMASI HAPUS
        # ============================================================

        delete_id = st.session_state.get("delete_logbook_id")

        if delete_id:

            st.warning("⚠️ Yakin ingin menghapus logbook ini?")

            col_yes, col_no = st.columns(2)

            with col_yes:
                if st.button(
                    "✅ Ya, Hapus",
                    key="confirm_delete_logbook"
                ):

                    execute_query(
                        "DELETE FROM routine_logbooks WHERE id = ?",
                        (delete_id,)
                    )

                    del st.session_state["delete_logbook_id"]

                    st.success("Logbook berhasil dihapus.")

                    st.rerun()

            with col_no:
                if st.button(
                    "❌ Batal",
                    key="cancel_delete_logbook"
                ):

                    del st.session_state["delete_logbook_id"]

                    st.rerun()

        # ============================================================
        # FORM EDIT LOGBOOK
        # ============================================================

        edit_id = st.session_state.get("edit_logbook_id")

        if edit_id:

            edit_data = fetch_all(
                """
                SELECT *
                FROM routine_logbooks
                WHERE id = ?
                """,
                (edit_id,)
            )

            if edit_data:

                edit_data = edit_data[0]

                st.markdown("---")
                st.subheader("✏️ Edit Logbook")

                try:
                    tanggal_awal = datetime.strptime(
                        edit_data["tanggal_logbook"][:10],
                        "%Y-%m-%d"
                    ).date()
                except:
                    tanggal_awal = date.today()

                with st.form("form_edit_logbook"):

                    tanggal_baru = st.date_input(
                        "Tanggal Aktivitas",
                        value=tanggal_awal
                    )

                    ket_baru = st.text_area(
                        "Keterangan Progres",
                        value=edit_data["keterangan_progres"]
                    )

                    col_save, col_cancel = st.columns(2)

                    with col_save:
                        simpan = st.form_submit_button(
                            "💾 Simpan Perubahan",
                            use_container_width=True
                        )

                    with col_cancel:
                        batal = st.form_submit_button(
                            "❌ Batal",
                            use_container_width=True
                        )

                    if simpan:

                        execute_query(
                            """
                            UPDATE routine_logbooks
                            SET
                                tanggal_logbook = ?,
                                keterangan_progres = ?
                            WHERE id = ?
                            """,
                            (
                                str(tanggal_baru),
                                ket_baru,
                                edit_id
                            )
                        )

                        del st.session_state["edit_logbook_id"]

                        st.success("Logbook berhasil diperbarui.")

                        st.rerun()

                    if batal:

                        del st.session_state["edit_logbook_id"]

                        st.rerun()
                
    # =========================================================================
    # TAB 2: TUGAS NON-RUTINITAS (INSTRUKSI ATASAN)
    # =========================================================================
    with tab_non_rutin:
        st.subheader("Daftar Instruksi & Proyek dari Atasan")
        
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.2, 1.0, 1.0, 1.0])
        with f_col1:
            search_query = st.text_input("🔍 Cari Judul Tugas", placeholder="Ketik kata kunci...", key="filter_search_nr")
        with f_col2:
            status_options = ["Semua Status", "Assigned", "Submitted", "Revision", "Approved"]
            selected_status = st.selectbox("📌 Filter Status", status_options, key="filter_status_nr")
        with f_col3:
            start_date = st.date_input("📅 Dari Tanggal", value=date.today() - timedelta(days=30), key="start_date_nr")
        with f_col4:
            end_date = st.date_input("📅 Sampai Tanggal", value=date.today(), key="end_date_nr")
            
        st.markdown("<hr style='margin-top:5px; margin-bottom:20px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
        
        query_non_rutin = "SELECT t.*, u.nama as nama_atasan FROM tasks t JOIN users u ON t.assigned_by = u.id WHERE t.assigned_to = ? ORDER BY t.id DESC"
        assigned_tasks = fetch_all(query_non_rutin, (user["id"],))
        
        if assigned_tasks:
            if search_query:
                assigned_tasks = [t for t in assigned_tasks if search_query.lower() in t["judul"].lower()]
            if selected_status != "Semua Status":
                assigned_tasks = [t for t in assigned_tasks if t["status_task"].lower() == selected_status.lower()]
            if start_date and end_date:
                filtered_by_range = []
                for t in assigned_tasks:
                    if t["tanggal_assign"]: 
                        try:
                            task_date_str = t["tanggal_assign"][:10]
                            task_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
                            if start_date <= task_date <= end_date:
                                filtered_by_range.append(t)
                        except ValueError:
                            continue
                assigned_tasks = filtered_by_range
        
        if not assigned_tasks:
            st.info("👍 **Informasi:** Tidak ada tugas non-rutinitas khusus yang cocok dengan kriteria pencarian/filter Anda saat ini.")
        else:
            for task in assigned_tasks:
                status = task["status_task"].lower()
                
                if status == "assigned": color, text = "#E0E1DD", "Assigned"
                elif status == "submitted": color, text = "#F4A261", "Submitted"
                elif status == "revision": color, text = "#E63946", "Revision"
                elif status == "approved": color, text = "#2A9D8F", "Approved"
                else: color, text = "#999", status
                
                st.markdown(f"""
                    <div class="task-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #1B263B;">📌 {task['judul']}</h3>
                            <span class="status-badge" style="background-color: {color}; color: {'white' if status != 'assigned' else '#1B263B'};">{text.upper()}</span>
                        </div>
                        <p style="margin: 8px 0; color: #555;">{task['deskripsi']}</p>
                        <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
                        <small style="color: #777;">👨‍💼 Pemberi Tugas: {task['nama_atasan']} | 📅 Deadline: {task['deadline']}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                boleh_isi = status in ["assigned", "revision"]
                
                query_sub = "SELECT * FROM submissions WHERE task_id = ? ORDER BY id DESC LIMIT 1"
                res_sub = fetch_all(query_sub, (task["id"],))
                existing_sub = res_sub[0] if res_sub else None
                
                if status == "submitted" and existing_sub:
                    st.markdown(f"📎 **Tautan saat ini:** [{existing_sub['link_drive']}]({existing_sub['link_drive']})")
                    if existing_sub['keterangan']:
                        st.markdown(f"💬 **Keterangan Anda:** *{existing_sub['keterangan']}*")
                    if st.button("✏️ Ubah Pengumpulan Berkas", key=f"btn_edit_{task['id']}"):
                        st.session_state[f"editing_{task['id']}"] = True
                
                is_editing = st.session_state.get(f"editing_{task['id']}", False)

                if boleh_isi or is_editing:
                    label_expander = f"📥 Kirim Hasil Pengerjaan untuk '{task['judul']}'" if not is_editing else f"🔄 Perbarui Hasil Pengerjaan untuk '{task['judul']}'"
                    
                    with st.expander(label_expander, expanded=is_editing):
                        metode = st.radio("Pilih Metode Dokumen:", ["🔗 Salin Tautan Teks URL", "📁 Unggah Berkas Langsung (PDF / Excel)"], horizontal=True, key=f"metode_{task['id']}")
                        
                        with st.form(key=f"form_submit_{task['id']}", clear_on_submit=True):
                            final_link = ""
                            uploaded_file = None
                            
                            if metode == "🔗 Salin Tautan Teks URL":
                                default_val = existing_sub['link_drive'] if (is_editing and existing_sub) else ""
                                final_link = st.text_input("Link URL Hasil Kerja:", value=default_val, placeholder="https://drive.google.com/...")
                            else:
                                uploaded_file = st.file_uploader("Pilih Berkas Tugas (Maksimal 10MB):", type=["pdf", "xlsx", "xls"], key=f"file_{task['id']}")
                            
                            default_ket = existing_sub['keterangan'] if (is_editing and existing_sub) else ""
                            ket_submit = st.text_area("Keterangan Tambahan / Catatan (Opsional):", value=default_ket, placeholder="Tulis catatan atau pesan singkat...", key=f"ket_submit_{task['id']}", height=100)
                            
                            label_tombol = "🚀 Kirim Hasil Tugas" if not is_editing else "💾 Simpan Perubahan"
                            submit_btn = st.form_submit_button(label_tombol, use_container_width=True)
                            
                            if submit_btn:
                                is_valid = True
                                if metode == "🔗 Salin Tautan Teks URL" and not final_link.strip():
                                    st.error("⚠️ Mohon masukkan tautan URL hasil pekerjaan Anda!")
                                    is_valid = False
                                elif metode == "📁 Unggah Berkas Langsung (PDF / Excel)" and uploaded_file is None:
                                    st.error("⚠️ Silakan pilih berkas dokumen fisik terlebih dahulu!")
                                    is_valid = False
                                
                                if is_valid:
                                    if metode == "📁 Unggah Berkas Langsung (PDF / Excel)" and uploaded_file is not None:
                                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        filename_to_drive = f"Tugas_{task['id']}_{timestamp_str}_{uploaded_file.name}"
                                        with st.spinner("Sedang memperbarui berkas..."):
                                            final_link = upload_to_google_drive(uploaded_file, filename_to_drive, user["divisi"])
                                    
                                    if final_link:
                                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        if is_editing and existing_sub:
                                            execute_query("UPDATE submissions SET link_drive = ?, keterangan = ?, tanggal_submit = ? WHERE id = ?", (final_link, ket_submit, now, existing_sub['id']))
                                            st.session_state[f"editing_{task['id']}"] = False
                                        else:
                                            execute_query("INSERT INTO submissions (task_id, link_drive, keterangan, tanggal_submit) VALUES (?, ?, ?, ?)", (task["id"], final_link, ket_submit, now))
                                            execute_query("UPDATE tasks SET status_task = 'submitted' WHERE id = ?", (task["id"],))
                                        
                                        st.session_state["trigger_success_balloons"] = True
                                        st.rerun()

                        if is_editing:
                            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                            if st.button("❌ Batal Mengubah", key=f"cancel_{task['id']}", use_container_width=True):
                                st.session_state[f"editing_{task['id']}"] = False
                                st.rerun()
                
                if status == "revision":
                    feedback_items = fetch_all(
                        "SELECT komentar, tanggal_ditulis FROM feedback WHERE submission_id IN (SELECT id FROM submissions WHERE task_id = ?) ORDER BY id DESC LIMIT 1",
                        (task["id"],)
                    )
                    if feedback_items:
                        st.error(f"🔴 **Catatan Revisi Atasan ({feedback_items[0]['tanggal_ditulis']}):** {feedback_items[0]['komentar']}")
                
                st.markdown("<br>", unsafe_allow_html=True)
import streamlit as st
import pandas as pd
from database import fetch_all, execute_query, get_secret
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")

# =========================================================================
# UPLOAD KE GOOGLE DRIVE
# =========================================================================
def upload_to_google_drive(uploaded_file, filename_on_drive, divisi_name):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import io
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    ROOT_FOLDER_ID = "11sU-BVtM-VLhKPKYChDyXwgeaHcWG0xg"
    try:
        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        creds = Credentials(
            token=None,
            refresh_token=get_secret("gdrive_oauth", "refresh_token"),
            token_uri=get_secret("gdrive_oauth", "token_uri"),
            client_id=get_secret("gdrive_oauth", "client_id"),
            client_secret=get_secret("gdrive_oauth", "client_secret"),
            scopes=SCOPES
        )
        creds.refresh(Request())
        service = build("drive", "v3", credentials=creds)

        def get_or_create_folder(folder_name, parent_folder_id=None):
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            results = service.files().list(q=query, fields="files(id,name)").execute()
            folders = results.get("files", [])
            if folders:
                return folders[0]["id"]
            folder = service.files().create(
                body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_folder_id]},
                fields="id"
            ).execute()
            return folder["id"]

        divisi_folder_id = get_or_create_folder(divisi_name, ROOT_FOLDER_ID)
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        uploaded_drive_file = service.files().create(
            body={"name": filename_on_drive, "parents": [divisi_folder_id]},
            media_body=media, fields="id,webViewLink"
        ).execute()
        service.permissions().create(
            fileId=uploaded_drive_file["id"],
            body={"type": "anyone", "role": "reader"}
        ).execute()
        return uploaded_drive_file["webViewLink"]
    except Exception as e:
        st.error(f"Gagal mengunggah berkas ke Google Drive: {e}")
        return None


# =========================================================================
# QUERY HELPERS
# =========================================================================
@st.cache_data(ttl=30)
def get_jobdesc_templates(role, divisi, kategori):
    return fetch_all(
        "SELECT id, nama_tugas FROM jobdesc_templates WHERE role=? AND divisi=? AND kategori_periodik=? ORDER BY nama_tugas",
        (role, divisi, kategori)
    )

@st.cache_data(ttl=30)
def get_logbook_job_list(user_id):
    return fetch_all(
        "SELECT DISTINCT jt.nama_tugas FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id=jt.id WHERE rl.user_id=?",
        (user_id,)
    )

@st.cache_data(ttl=15)
def get_logbook_history(user_id):
    return fetch_all("""
        SELECT rl.id, rl.tanggal_logbook, rl.keterangan_progres, rl.link_file,
               rl.tanggal_input, jt.nama_tugas, jt.kategori_periodik
        FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id=jt.id
        WHERE rl.user_id=? ORDER BY rl.tanggal_logbook DESC, rl.tanggal_input DESC
    """, (user_id,))

@st.cache_data(ttl=15)
def get_assigned_tasks(user_id):
    return fetch_all(
        "SELECT t.*, u.nama as nama_atasan FROM tasks t JOIN users u ON t.assigned_by=u.id WHERE t.assigned_to=? ORDER BY t.id DESC",
        (user_id,)
    )

@st.cache_data(ttl=10)
def get_all_submissions(task_id):
    """Ambil semua riwayat submission untuk satu task, terbaru di atas."""
    return fetch_all(
        "SELECT * FROM submissions WHERE task_id=? ORDER BY id DESC",
        (task_id,)
    )

@st.cache_data(ttl=10)
def get_all_feedback(task_id):
    """Ambil semua riwayat feedback untuk satu task, terbaru di atas."""
    return fetch_all("""
        SELECT f.komentar, f.tanggal_ditulis, s.tanggal_submit, s.link_drive
        FROM feedback f
        JOIN submissions s ON f.submission_id = s.id
        WHERE s.task_id=?
        ORDER BY f.id DESC
    """, (task_id,))


# =========================================================================
# HALAMAN TUGAS SAYA
# =========================================================================
def show_my_task():
    if st.session_state.get("trigger_success_balloons", False):
        st.balloons()
        st.session_state["trigger_success_balloons"] = False

    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px; border-radius: 16px; margin-bottom: 24px;
            border: 1px solid rgba(16,185,129,0.2);
        }
        .header-card h2 { margin:0 0 4px 0; font-size:22px; font-weight:600; color:white !important; }
        .header-card p  { margin:0; font-size:13px; color:#94A3B8 !important; }

        .task-card {
            background: white; padding: 18px 20px; border-radius: 12px;
            border: 1px solid #E2E8F0; border-left: 4px solid #10B981;
            margin-bottom: 12px;
        }
        .task-card-approved {
            background: white; padding: 18px 20px; border-radius: 12px;
            border: 1px solid #D1FAE5; border-left: 4px solid #10B981;
            margin-bottom: 12px;
        }

        .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
        .badge-assigned  { background:#EFF6FF; color:#1D4ED8; }
        .badge-submitted { background:#FFF7ED; color:#C2410C; }
        .badge-revision  { background:#FEF2F2; color:#DC2626; }
        .badge-approved  { background:#DCFCE7; color:#15803D; }

        .submission-item {
            background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
        }
        .submission-item-latest {
            background: #F0FDF4; border: 1px solid #BBF7D0;
            border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
        }
        .feedback-item {
            background: #FFF7ED; border: 1px solid #FED7AA;
            border-left: 3px solid #F97316;
            border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
        }
        .timeline-label {
            font-size: 11px; color: #94A3B8; font-weight: 500;
            text-transform: uppercase; letter-spacing: 0.05em;
            margin-bottom: 6px;
        }

        section.main button[kind="primary"],
        section.main div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"],
        section.main div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg,#10B981,#059669) !important;
            color: white !important; border: none !important;
            font-weight: 600 !important; border-radius: 10px !important;
        }

        .st-key-btn_batal_edit button,
        .st-key-btn_batal_hapus button,
        .st-key-confirm_no button {
            background: transparent !important;
            color: #EF4444 !important;
            border: 1px solid rgba(239,68,68,.35) !important;
            border-radius: 10px !important;
        }
        .st-key-confirm_yes button {
            background: #EF4444 !important;
            color: white !important; border: none !important;
            border-radius: 10px !important; font-weight: 600 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px; background:#F1F5F9; padding:4px; border-radius:10px;
        }
        .stTabs [data-baseweb="tab"] { border-radius:8px; padding:6px 16px; font-size:13px; }
        .stTabs [aria-selected="true"] {
            background:white !important; font-weight:600 !important;
            box-shadow:0 1px 4px rgba(0,0,0,.08);
        }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.warning("Silakan login terlebih dahulu.")
        st.stop()

    user = st.session_state["user"]

    st.markdown("""
        <div class="header-card">
            <h2>Tugas Saya</h2>
            <p>Kelola laporan aktivitas rutin harian dan instruksi khusus dari atasan.</p>
        </div>
    """, unsafe_allow_html=True)

    tab_rutin, tab_non_rutin, tab_selesai = st.tabs([
        "Rutinitas (Logbook)",
        "Non-Rutinitas (Instruksi Aktif)",
        "Selesai & Disetujui",
    ])

    # =========================================================================
    # TAB 1: LOGBOOK RUTINITAS
    # =========================================================================
    with tab_rutin:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1E293B;margin-bottom:12px;">Form Input Logbook</p>', unsafe_allow_html=True)

        col_tgl, col_kat, col_job = st.columns([1, 1, 2])
        with col_tgl:
            tgl_logbook = st.date_input("Tanggal Aktivitas", value=date.today(), key="input_tgl_logbook")
        with col_kat:
            kategori_periodik = st.selectbox("Kategori Periodik", ["Harian", "Bulanan", "Tahunan"], key="input_kategori_periodik")

        templates = get_jobdesc_templates(user["role"], user["divisi"], kategori_periodik)
        template_options = {t["nama_tugas"]: t["id"] for t in templates}

        with col_job:
            pilihan_tugas = st.selectbox("Judul Pekerjaan", list(template_options.keys()), key="input_pilihan_tugas")

        with st.form(key="form_logbook_rutin", clear_on_submit=True):
            keterangan    = st.text_area("Keterangan Progres / Hasil Kerja", placeholder="Detailkan aktivitas yang Anda kerjakan...", height=120)
            uploaded_file = st.file_uploader(":material/attach_file: Lampiran Hasil Kerja (Opsional)", type=["pdf","xlsx","xls","png","jpg","jpeg"])

            if st.form_submit_button(":material/save: Simpan Logbook", use_container_width=True):
                if not keterangan.strip():
                    st.error("Keterangan tidak boleh kosong.")
                else:
                    now_ts     = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                    jobdesc_id = template_options.get(pilihan_tugas)
                    if jobdesc_id:
                        final_link = None
                        if uploaded_file:
                            ts  = datetime.now(WIB).strftime("%Y%m%d_%H%M%S")
                            fn  = f"Logbook_{user['id']}_{ts}_{uploaded_file.name}"
                            with st.spinner("Mengunggah lampiran..."):
                                final_link = upload_to_google_drive(uploaded_file, fn, user["divisi"])
                        execute_query(
                            "INSERT INTO routine_logbooks (user_id, tanggal_logbook, jobdesc_id, keterangan_progres, link_file, tanggal_input) VALUES (?,?,?,?,?,?)",
                            (user["id"], str(tgl_logbook), jobdesc_id, keterangan, final_link, now_ts)
                        )
                        get_logbook_history.clear()
                        get_logbook_job_list.clear()
                        st.success(f"Logbook {kategori_periodik.lower()} berhasil disimpan!")
                        st.rerun()

        st.markdown("<hr style='border-color:#E2E8F0; margin:20px 0'>", unsafe_allow_html=True)
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1E293B;margin-bottom:12px;">Riwayat Logbook</p>', unsafe_allow_html=True)

        job_list = get_logbook_job_list(user["id"])
        job_opts = ["Semua Pekerjaan"] + [j["nama_tugas"] for j in job_list]

        lc1, lc2, lc3 = st.columns([1.2, 1, 1])
        with lc1: filter_job = st.selectbox("Filter Pekerjaan", job_opts, key="filter_job_lb")
        with lc2: start_lb   = st.date_input("Dari Tanggal", value=date.today()-timedelta(days=30), key="start_date_lb")
        with lc3: end_lb     = st.date_input("Sampai Tanggal", value=date.today(), key="end_date_lb")

        history = get_logbook_history(user["id"])

        if history:
            if filter_job != "Semua Pekerjaan":
                history = [h for h in history if h["nama_tugas"] == filter_job]
            filtered_h = []
            for h in history:
                try:
                    ld = datetime.strptime(h["tanggal_logbook"][:10], "%Y-%m-%d").date()
                    if start_lb <= ld <= end_lb:
                        filtered_h.append(h)
                except: continue
            history = filtered_h

        if not history:
            st.info("Tidak ada riwayat logbook sesuai filter.")
        else:
            df = pd.DataFrame([{
                "Tanggal": h["tanggal_logbook"], "Pekerjaan": h["nama_tugas"],
                "Kategori": h["kategori_periodik"],
                "Keterangan": h["keterangan_progres"][:60]+"..." if len(h["keterangan_progres"])>60 else h["keterangan_progres"],
                "Lampiran": "✓" if h["link_file"] else "—"
            } for h in history])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            sel_log = st.selectbox("Pilih Logbook untuk Detail / Aksi", history,
                                   format_func=lambda x: f"{x['tanggal_logbook']} — {x['nama_tugas']}")

            with st.container(border=True):
                st.markdown(f"**Tanggal:** {sel_log['tanggal_logbook']}")
                st.markdown(f"**Pekerjaan:** {sel_log['nama_tugas']}  ·  *{sel_log['kategori_periodik']}*")
                st.markdown(f"**Keterangan:**")
                st.write(sel_log["keterangan_progres"])
                if sel_log["link_file"]:
                    st.markdown(f":material/open_in_new: [Buka Lampiran]({sel_log['link_file']})")

            ca, cb = st.columns(2)
            with ca:
                if st.button(":material/edit: Edit Logbook", use_container_width=True, key="btn_edit_log"):
                    st.session_state["edit_logbook_id"] = sel_log["id"]
            with cb:
                if st.button(":material/delete: Hapus Logbook", use_container_width=True, key="btn_hapus_log"):
                    st.session_state["delete_logbook_id"] = sel_log["id"]

        if st.session_state.get("delete_logbook_id"):
            del_id = st.session_state["delete_logbook_id"]
            st.warning("Yakin ingin menghapus logbook ini?")
            cy, cn = st.columns(2)
            with cy:
                if st.button(":material/check: Ya, Hapus", key="confirm_yes", use_container_width=True):
                    execute_query("DELETE FROM routine_logbooks WHERE id=?", (del_id,))
                    get_logbook_history.clear()
                    get_logbook_job_list.clear()
                    del st.session_state["delete_logbook_id"]
                    st.success("Logbook dihapus.")
                    st.rerun()
            with cn:
                if st.button(":material/close: Batal", key="confirm_no", use_container_width=True):
                    del st.session_state["delete_logbook_id"]
                    st.rerun()

        if st.session_state.get("edit_logbook_id"):
            edit_id   = st.session_state["edit_logbook_id"]
            edit_rows = fetch_all("SELECT * FROM routine_logbooks WHERE id=?", (edit_id,))
            if edit_rows:
                ed = edit_rows[0]
                st.markdown("<hr style='border-color:#E2E8F0'>", unsafe_allow_html=True)
                st.markdown('<p style="font-size:15px;font-weight:600;">:material/edit: Edit Logbook</p>', unsafe_allow_html=True)
                try:    tgl_awal = datetime.strptime(ed["tanggal_logbook"][:10], "%Y-%m-%d").date()
                except: tgl_awal = date.today()

                with st.form("form_edit_logbook"):
                    tgl_baru = st.date_input("Tanggal Aktivitas", value=tgl_awal)
                    ket_baru = st.text_area("Keterangan Progres", value=ed["keterangan_progres"])
                    cs, cc   = st.columns(2)
                    with cs: simpan = st.form_submit_button(":material/save: Simpan", use_container_width=True)
                    with cc: batal  = st.form_submit_button(":material/close: Batal", use_container_width=True)
                    if simpan:
                        execute_query("UPDATE routine_logbooks SET tanggal_logbook=?, keterangan_progres=? WHERE id=?",
                                      (str(tgl_baru), ket_baru, edit_id))
                        get_logbook_history.clear()
                        del st.session_state["edit_logbook_id"]
                        st.success("Logbook diperbarui.")
                        st.rerun()
                    if batal:
                        del st.session_state["edit_logbook_id"]
                        st.rerun()

    # =========================================================================
    # HELPER: render detail submission + feedback history (expander)
    # =========================================================================
    def render_detail_expander(task, show_submit_form=True):
        """Expander berisi riwayat semua submission dan feedback untuk satu task."""
        submissions = get_all_submissions(task["id"])
        feedbacks   = get_all_feedback(task["id"])
        status      = task["status_task"].lower()

        sub_count = len(submissions)
        fb_count  = len(feedbacks)
        label     = f":material/history: Riwayat Pengumpulan ({sub_count}) & Feedback ({fb_count})"

        with st.expander(label, expanded=(status == "revision")):

            # ── Feedback dari atasan ──────────────────────────────────────
            if feedbacks:
                st.markdown('<p class="timeline-label">💬 Feedback dari Atasan</p>', unsafe_allow_html=True)
                for fb in feedbacks:
                    st.markdown(f"""
                        <div class="feedback-item">
                            <p style="margin:0 0 4px 0;font-size:13px;color:#9A3412;font-weight:600;">
                                {fb['tanggal_ditulis']}
                            </p>
                            <p style="margin:0;font-size:14px;color:#1E293B;">{fb['komentar']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Belum ada feedback dari atasan.")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Riwayat semua pengumpulan ─────────────────────────────────
            if submissions:
                st.markdown('<p class="timeline-label">📎 Riwayat Pengumpulan</p>', unsafe_allow_html=True)
                for i, sub in enumerate(submissions):
                    is_latest = (i == 0)
                    card_cls  = "submission-item-latest" if is_latest else "submission-item"
                    tag       = " <span style='font-size:10px;background:#10B981;color:white;padding:2px 6px;border-radius:10px;'>Terbaru</span>" if is_latest else ""
                    st.markdown(f"""
                        <div class="{card_cls}">
                            <p style="margin:0 0 4px 0;font-size:12px;color:#64748B;">
                                Pengumpulan ke-{sub_count - i}{tag}
                                &nbsp;·&nbsp; {sub['tanggal_submit']}
                            </p>
                            <a href="{sub['link_drive']}" target="_blank"
                               style="font-size:13px;color:#0EA5E9;text-decoration:none;">
                               Buka Dokumen
                            </a>
                            {"<p style='margin:4px 0 0 0;font-size:12px;color:#64748B;'>📝 " + sub['keterangan'] + "</p>" if sub.get('keterangan') else ""}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Belum ada pengumpulan.")

            # ── Form kirim / ubah (hanya jika status memungkinkan) ────────
            if show_submit_form and status in ["assigned", "revision", "submitted"]:
                st.markdown("<hr style='border-color:#E2E8F0;margin:12px 0'>", unsafe_allow_html=True)
                latest_sub = submissions[0] if submissions else None
                is_editing = st.session_state.get(f"editing_{task['id']}", False)

                if status == "submitted" and latest_sub and not is_editing:
                    if st.button(":material/edit: Ubah Pengumpulan", key=f"btn_edit_{task['id']}", use_container_width=True):
                        st.session_state[f"editing_{task['id']}"] = True
                        st.rerun()
                else:
                    lbl_section = "Perbarui Pengumpulan" if is_editing else "Kirim Hasil Kerja"
                    st.markdown(f'<p style="font-size:13px;font-weight:600;color:#1E293B;margin-bottom:8px;"> {lbl_section}</p>', unsafe_allow_html=True)

                    metode = st.radio("Metode:", ["Tautan URL", "Unggah Berkas (PDF/Excel)"],
                                      horizontal=True, key=f"metode_{task['id']}")

                    with st.form(key=f"form_submit_{task['id']}", clear_on_submit=True):
                        final_link = ""
                        if metode == "Tautan URL":
                            default_v  = latest_sub["link_drive"] if (is_editing and latest_sub) else ""
                            final_link = st.text_input("Link URL Hasil Kerja:", value=default_v,
                                                       placeholder="https://drive.google.com/...")
                        else:
                            uf = st.file_uploader("Pilih Berkas (maks 10MB):", type=["pdf","xlsx","xls"],
                                                  key=f"file_{task['id']}")

                        default_k  = latest_sub["keterangan"] if (is_editing and latest_sub) else ""
                        ket_submit = st.text_area("Catatan Tambahan (Opsional):", value=default_k,
                                                  placeholder="Tulis catatan...", key=f"ket_{task['id']}", height=80)

                        lbl_btn = ":material/save: Simpan Perubahan" if is_editing else ":material/send: Kirim Tugas"
                        if st.form_submit_button(lbl_btn, use_container_width=True):
                            valid = True
                            if metode == "Tautan URL" and not final_link.strip():
                                st.error("Masukkan tautan URL terlebih dahulu."); valid = False
                            elif metode == "Unggah Berkas (PDF/Excel)" and 'uf' in dir() and uf is None:
                                st.error("Pilih berkas terlebih dahulu."); valid = False

                            if valid:
                                if metode == "Unggah Berkas (PDF/Excel)" and 'uf' in dir() and uf:
                                    ts = datetime.now(WIB).strftime("%Y%m%d_%H%M%S")
                                    with st.spinner("Mengunggah berkas..."):
                                        final_link = upload_to_google_drive(
                                            uf, f"Tugas_{task['id']}_{ts}_{uf.name}", user["divisi"]
                                        )
                                if final_link:
                                    now = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                                    # Selalu INSERT row baru — riwayat terjaga
                                    execute_query(
                                        "INSERT INTO submissions (task_id, link_drive, keterangan, tanggal_submit) VALUES (?,?,?,?)",
                                        (task["id"], final_link, ket_submit, now)
                                    )
                                    execute_query(
                                        "UPDATE tasks SET status_task='submitted' WHERE id=?",
                                        (task["id"],)
                                    )
                                    st.session_state[f"editing_{task['id']}"] = False
                                    get_all_submissions.clear()
                                    get_assigned_tasks.clear()
                                    st.session_state["trigger_success_balloons"] = True
                                    st.rerun()

                    if is_editing:
                        if st.button(":material/close: Batal", key=f"btn_batal_edit_{task['id']}", use_container_width=True):
                            st.session_state[f"editing_{task['id']}"] = False
                            st.rerun()

    # =========================================================================
    # HELPER: render task card header
    # =========================================================================
    def render_task_card(task, show_actions=True):
        status = task["status_task"].lower()
        badge_map = {
            "assigned":  ("badge-assigned",  "Assigned"),
            "submitted": ("badge-submitted", "Submitted"),
            "revision":  ("badge-revision",  "Revision"),
            "approved":  ("badge-approved",  "Approved"),
        }
        badge_cls, badge_txt = badge_map.get(status, ("badge-assigned", status.capitalize()))
        card_cls = "task-card-approved" if status == "approved" else "task-card"

        # Banner revisi di atas card jika ada feedback terbaru
        if status == "revision":
            fb_list = get_all_feedback(task["id"])
            if fb_list:
                latest_fb = fb_list[0]
                st.markdown(f"""
                    <div style="background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid #F97316;
                                border-radius:10px;padding:10px 14px;margin-bottom:8px;">
                        <p style="margin:0 0 2px 0;font-size:12px;color:#9A3412;font-weight:600;">
                            ⚠️ Perlu Revisi · {latest_fb['tanggal_ditulis']}
                        </p>
                        <p style="margin:0;font-size:13px;color:#1E293B;">{latest_fb['komentar']}</p>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="{card_cls}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                    <div>
                        <p style="margin:0;font-size:15px;font-weight:600;color:#1E293B;">{task['judul']}</p>
                        <p style="margin:4px 0 0 0;font-size:13px;color:#64748B;">{task['deskripsi']}</p>
                    </div>
                    <span class="badge {badge_cls}" style="white-space:nowrap">{badge_txt}</span>
                </div>
                <hr style="border:none;border-top:1px solid #F1F5F9;margin:12px 0 8px 0">
                <small style="color:#94A3B8;">
                    Dari: <strong style="color:#475569">{task['nama_atasan']}</strong>
                    &nbsp;·&nbsp; Deadline: <strong style="color:#475569">{task['deadline']}</strong>
                </small>
            </div>
        """, unsafe_allow_html=True)

        # Expander detail — selalu tampil di semua status
        render_detail_expander(task, show_submit_form=show_actions)
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: NON-RUTINITAS AKTIF
    # =========================================================================
    with tab_non_rutin:
        fc1, fc2, fc3, fc4 = st.columns([1.5, 1, 1, 1])
        with fc1: search_q   = st.text_input(":material/search: Cari Judul", placeholder="Kata kunci...", key="search_nr")
        with fc2: sel_status = st.selectbox("Status", ["Semua","Assigned","Submitted","Revision"], key="status_nr")
        with fc3: start_nr   = st.date_input("Dari", value=date.today()-timedelta(days=30), key="start_nr")
        with fc4: end_nr     = st.date_input("Sampai", value=date.today(), key="end_nr")

        st.markdown("<hr style='border-color:#E2E8F0;margin:8px 0 16px 0'>", unsafe_allow_html=True)

        all_tasks    = get_assigned_tasks(user["id"])
        active_tasks = [t for t in all_tasks if t["status_task"].lower() != "approved"]

        if search_q:
            active_tasks = [t for t in active_tasks if search_q.lower() in t["judul"].lower()]
        if sel_status != "Semua":
            active_tasks = [t for t in active_tasks if t["status_task"].lower() == sel_status.lower()]

        filtered_active = []
        for t in active_tasks:
            try:
                td = datetime.strptime(t["tanggal_assign"][:10], "%Y-%m-%d").date()
                if start_nr <= td <= end_nr:
                    filtered_active.append(t)
            except: continue

        if not filtered_active:
            st.info("Tidak ada tugas aktif yang sesuai filter.")
        else:
            for task in filtered_active:
                render_task_card(task, show_actions=True)

    # =========================================================================
    # TAB 3: TUGAS SELESAI & DISETUJUI
    # =========================================================================
    with tab_selesai:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1E293B;margin-bottom:4px;">Arsip tugas yang telah disetujui atasan.</p>', unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns([2, 1, 1])
        with sc1: search_ap = st.text_input(":material/search: Cari Judul", placeholder="Kata kunci...", key="search_ap")
        with sc2: start_ap  = st.date_input("Dari", value=date(2026,1,1), key="start_ap")
        with sc3: end_ap    = st.date_input("Sampai", value=date.today(), key="end_ap")

        st.markdown("<hr style='border-color:#E2E8F0;margin:8px 0 16px 0'>", unsafe_allow_html=True)

        all_tasks      = get_assigned_tasks(user["id"])
        approved_tasks = [t for t in all_tasks if t["status_task"].lower() == "approved"]

        if search_ap:
            approved_tasks = [t for t in approved_tasks if search_ap.lower() in t["judul"].lower()]

        filtered_ap = []
        for t in approved_tasks:
            try:
                td = datetime.strptime(t["tanggal_assign"][:10], "%Y-%m-%d").date()
                if start_ap <= td <= end_ap:
                    filtered_ap.append(t)
            except: continue

        if not filtered_ap:
            st.info("Belum ada tugas yang disetujui dalam periode ini.")
        else:
            st.metric(":material/check_circle: Total Disetujui", len(filtered_ap))
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            for task in filtered_ap:
                render_task_card(task, show_actions=False)
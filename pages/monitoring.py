import streamlit as st
from database import fetch_all, fetch_one, execute_query
from datetime import datetime, date

def show_monitoring():
    # 🎨 CSS Styling bawaanmu + Tambahan kosmetik baris logbook
    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
            padding: 25px; border-radius: 15px; color: white; margin-bottom: 25px;
        }
        
        /* Tombol Review (Warna Navy) */
        [data-testid="stHorizontalBlock"] div:nth-child(1) > div > button {
            background-color: #1B263B !important;
            color: white !important;
            border: none !important;
        }

        /* Tombol Hapus (Warna Merah) */
        [data-testid="stHorizontalBlock"] div:nth-child(2) > div > button {
            background-color: #dc3545 !important;
            color: white !important;
            border: none !important;
        }

        /* Tombol Simpan Keputusan (Primary) */
        section.main button[kind=\"primary\"] {
            background-color: #1B263B !important;
            color: white !important;
            border: none !important;
        }

        /* Tombol Kembali */
        section.main div.stColumn + button, 
        section.main .stButton > button:not([kind="primary"]) {
            background-color: #6c757d !important;
            color: white !important;
            border: none !important;
        }
        
        section.main .stButton > button:not([kind="primary"]) p {
            color: white !important;
        }
        
        button:hover { opacity: 0.8; }
        
        /* Timeline Log Card Style */
        .log-card {
            background-color: #f1f3f5;
            padding: 10px 15px;
            border-left: 4px solid #1B263B;
            border-radius: 4px;
            margin-bottom: 10px;
        }

        /* Style Baru untuk Baris Logbook Aktivitas */
        .logbook-row {
            background-color: #f8f9fa; padding: 12px; border-radius: 6px;
            margin-bottom: 8px; border-left: 4px solid #2A9D8F;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
        }
        </style>
    """, unsafe_allow_html=True)

    user = st.session_state["user"]
    
    if "mon_view" not in st.session_state:
        st.session_state["mon_view"] = "list"

    # Jika sedang dalam mode edit/review detail tugas, kunci tampilan penuh ke sana
    if st.session_state["mon_view"] == "edit":
        render_edit_action(user)
    else:
        # Jika berada di luar, tampilkan navigasi pecahan dua rumpun kerja utama
        tab_non_rutin, tab_rutin = st.tabs(["🚀 Monitoring Tugas Non-Rutinitas", "📅 Pantau Logbook Rutinitas"])
        
        with tab_non_rutin:
            render_list(user)
            
        with tab_rutin:
            render_logbook_monitoring(user)

def render_list(user):
    st.markdown("""
        <div class="header-card">
            <h2 style='margin:0;'>📊 Monitoring & Review Tugas</h2>
            <p style='margin:0; opacity:0.8;'>Evaluasi hasil kerja instruksi khusus tim dan berikan keputusan.</p>
        </div>
    """, unsafe_allow_html=True)

    # 🛠️ PERUBAHAN 1: Sekretaris Direksi diberi akses melihat seluruh tugas layaknya Dewan Direksi
    if user["divisi"] == "Dewan Direksi" or user["role"] == "Sekretaris Direksi":
        tasks = fetch_all("""
            SELECT t.*, u.nama as nama_karyawan, u.role as role_karyawan, u.divisi as divisi_karyawan 
            FROM tasks t 
            JOIN users u ON t.assigned_to = u.id 
            ORDER BY t.tanggal_assign DESC
        """)
    else:
        # Kabag/Supervisor memantau apa yang mereka tugaskan
        tasks = fetch_all("""
            SELECT t.*, u.nama as nama_karyawan, u.role as role_karyawan, u.divisi as divisi_karyawan 
            FROM tasks t 
            JOIN users u ON t.assigned_to = u.id 
            WHERE t.assigned_by = ? 
            ORDER BY t.tanggal_assign DESC
        """, (user["id"],))

    if not tasks:
        st.info("Belum ada tugas non-rutinitas yang Anda berikan untuk dimonitor.")
        return

    st.markdown("##### 🔍 Filter Data Tugas")
    f1, f2, f3 = st.columns(3)
    
    with f1:
        all_divisi = sorted(list(set(t["divisi_karyawan"] for t in tasks if t["divisi_karyawan"] is not None)))
        divisi_options = ["Semua Divisi"] + all_divisi
        selected_divisi = st.selectbox("Pilih Divisi", divisi_options, key="filter_divisi")
        tasks_filtered_stage1 = [t for t in tasks if t["divisi_karyawan"] == selected_divisi] if selected_divisi != "Semua Divisi" else tasks

    with f2:
        all_posisi = sorted(list(set(t["role_karyawan"] for t in tasks_filtered_stage1 if t["role_karyawan"] is not None)))
        posisi_options = ["Semua Posisi"] + all_posisi
        selected_posisi = st.selectbox("Pilih Posisi/Role", posisi_options, key="filter_posisi")
        tasks_filtered_stage2 = [t for t in tasks_filtered_stage1 if t["role_karyawan"] == selected_posisi] if selected_posisi != "Semua Posisi" else tasks_filtered_stage1

    with f3:
        all_nama = sorted(list(set(t["nama_karyawan"] for t in tasks_filtered_stage2 if t["nama_karyawan"] is not None)))
        nama_options = ["Semua Nama"] + all_nama
        selected_nama = st.selectbox("Pilih Karyawan", nama_options, key="filter_nama")
        final_tasks = [t for t in tasks_filtered_stage2 if t["nama_karyawan"] == selected_nama] if selected_nama != "Semua Nama" else tasks_filtered_stage2

    st.markdown("---")

    if not final_tasks:
        st.warning("Tidak ada tugas yang cocok dengan kombinasi filter di atas.")
        return

    h1, h2, h3, h4 = st.columns([2.5, 1.5, 1.5, 2])
    h1.caption("DETAIL TUGAS")
    h2.caption("KARYAWAN")
    h3.caption("STATUS")
    h4.caption("AKSI")
    st.write("")

    for t in final_tasks:
        status = t["status_task"].lower()
        badge_styles = {
            "assigned": ("#E0E1DD", "#1B263B"),
            "submitted": ("#FFF3CD", "#856404"),
            "revision": ("#F8D7DA", "#721C24"),
            "approved": ("#D4EDDA", "#155724")
        }
        bg, txt = badge_styles.get(status, ("#E0E1DD", "#1B263B"))

        # 🛠️ PERUBAHAN 2: Validasi aksi khusus Sekretaris Direksi
        can_action = True
        tooltip_msg = None
        if user["role"] == "Sekretaris Direksi" and t["divisi_karyawan"] != user["divisi"]:
            can_action = False
            tooltip_msg = "Anda tidak memiliki akses modifikasi pada divisi lain."

        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 2])
            
            with c1:
                st.markdown(f"**{t['judul']}**")
                st.caption(f"📅 Deadline: {t['deadline']}")
            
            with c2:
                st.markdown(f"**{t['nama_karyawan']}**")
                st.caption(f"💼 {t['divisi_karyawan']} - {t['role_karyawan']}")
            
            with c3:
                st.markdown(f"""<span class="status-badge" style="background-color:{bg}; color:{txt}; font-size:11px; padding:4px 10px; border-radius:10px;">{status.upper()}</span>""", unsafe_allow_html=True)
            
            with c4:
                b_col1, b_col2 = st.columns(2)
                
                # Gunakan parameter disabled dan help untuk UX yang rapi
                if b_col1.button("Review", key=f"rev_{t['id']}", disabled=not can_action, help=tooltip_msg):
                    st.session_state["selected_task_id"] = t["id"]
                    st.session_state["mon_view"] = "edit"
                    st.rerun()
                
                if b_col2.button("Hapus", key=f"del_{t['id']}", disabled=not can_action, help=tooltip_msg):
                    execute_query("DELETE FROM tasks WHERE id = ?", (t["id"],))
                    st.toast(f"Tugas '{t['judul']}' dihapus.")
                    st.rerun()
            st.divider()

def render_edit_action(user):
    task_id = st.session_state["selected_task_id"]
    
    task = fetch_one("""
        SELECT t.*, u.nama as nama_karyawan, u.role as role_karyawan 
        FROM tasks t 
        JOIN users u ON t.assigned_to = u.id 
        WHERE t.id = ?
    """, (task_id,))
    
    sub = fetch_one("SELECT * FROM submissions WHERE task_id = ? ORDER BY id DESC LIMIT 1", (task_id,))

    st.markdown(f"### 🔍 Review Tugas: {task['judul']}")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        with st.container(border=True):
            st.markdown("##### 📄 Dokumen Terakhir")
            st.write(f"**Karyawan:** {task['nama_karyawan']}")
            if sub:
                st.info(f"📅 Dikirim pada: {sub['tanggal_submit']}")
                st.link_button("📂 Buka Dokumen Terbaru", sub['link_drive'], use_container_width=True)
            else:
                st.warning("⚠️ Belum ada file yang dikirim.")
        
        with st.expander("⏳ Lihat Timeline Perjalanan & Riwayat Tugas", expanded=True):
            all_subs = fetch_all("""
                SELECT s.id as sub_id, s.tanggal_submit, s.link_drive, f.komentar, f.tanggal_ditulis
                FROM submissions s
                LEFT JOIN feedback f ON s.id = f.submission_id
                WHERE s.task_id = ?
                ORDER BY s.tanggal_submit ASC
            """, (task_id,))
            
            all_dl_hist = fetch_all("""
                SELECT dh.*, u.nama as nama_pengubah 
                FROM deadline_history dh
                JOIN users u ON dh.changed_by = u.id
                WHERE dh.task_id = ?
                ORDER BY dh.changed_at ASC
            """, (task_id,))
            
            timeline_events = []
            for s_data in all_subs:
                timeline_events.append({
                    "timestamp": datetime.strptime(s_data["tanggal_submit"], "%Y-%m-%d %H:%M:%S"),
                    "type": "submission",
                    "data": s_data
                })
            
            for dl_data in all_dl_hist:
                timeline_events.append({
                    "timestamp": datetime.strptime(dl_data["changed_at"], "%Y-%m-%d %H:%M:%S"),
                    "type": "deadline_change",
                    "data": dl_data
                })
                
            timeline_events.sort(key=lambda x: x["timestamp"])
            
            if not timeline_events:
                st.caption("Belum ada riwayat aktivitas pada tugas ini.")
            else:
                for idx, event in enumerate(timeline_events):
                    time_str = event["timestamp"].strftime("%d %b %Y %H:%M")
                    
                    if event["type"] == "submission":
                        s_val = event["data"]
                        st.markdown(f"""
                            <div class="log-card" style="border-left-color: #2a9d8f;">
                                <strong>📥 Pengumpulan Tugas ke-{idx+1}</strong><br>
                                <span style="font-size:12px; color:gray;">Waktu: {time_str}</span><br>
                                <a href="{s_val['link_drive']}" target="_blank" style="font-size:12px; color:#1B263B;">🔗 Lihat Dokumen Ini</a>
                            </div>
                        """, unsafe_allow_html=True)
                        if s_val["komentar"]:
                            st.markdown(f"""
                                <div style="margin-left: 20px; padding: 5px 10px; background: #fff; border-left: 2px dashed #dc3545; font-size:13px; margin-bottom:10px;">
                                    <strong>💬 Feedback Atasan:</strong> {s_val['komentar']}<br>
                                    <span style="font-size:11px; color:gray;">Ditulis pada: {s_val['tanggal_ditulis']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                    elif event["type"] == "deadline_change":
                        d_val = event["data"]
                        st.markdown(f"""
                            <div class="log-card" style="border-left-color: #e76f51; background-color: #fff5f2;">
                                <strong>🔄 Perpanjangan Deadline oleh {d_val['nama_pengubah']}</strong><br>
                                <span style="font-size:12px; color:gray;">Waktu Perubahan: {time_str}</span><br>
                                <span style="font-size:13px; color:#b70909;">📅 {d_val['old_deadline']} ➡️ {d_val['new_deadline']}</span>
                            </div>
                        """, unsafe_allow_html=True)

    with col_b:
        options = ["assigned", "submitted", "revision", "approved"]
        current_status = task["status_task"].lower()
        idx_status = options.index(current_status) if current_status in options else 0
        
        with st.container(border=True):
            st.markdown("##### ⚖️ Keputusan Atasan")
            selected_status = st.selectbox("Ubah Status Menjadi:", options, index=idx_status, key="status_selector")
            
            with st.form("form_review_execution"):
                feedback = st.text_area("Catatan Feedback / Revisi", placeholder="Tulis instruksi revisi atau evaluasi di sini...")
                
                if selected_status == "revision":
                    st.markdown("---")
                    st.markdown("⚠️ **Pengaturan Tenggat Waktu Revisi**")
                    current_deadline_obj = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                    new_dl_input = st.date_input("Tentukan Deadline Baru:", value=current_deadline_obj)
                else:
                    new_dl_input = None

                if st.form_submit_button("Simpan Keputusan", type="primary"):
                    # 1. Update Status Tugas
                    execute_query("UPDATE tasks SET status_task = ? WHERE id = ?", (selected_status, task_id))
                    
                    # 2. Perpanjangan Deadline jika revisi
                    if selected_status == "revision" and new_dl_input:
                        old_dl_str = task["deadline"]
                        new_dl_str = new_dl_input.strftime("%Y-%m-%d")
                        
                        if old_dl_str != new_dl_str:
                            execute_query("UPDATE tasks SET deadline = ? WHERE id = ?", (new_dl_str, task_id))
                            
                            execute_query("""
                                INSERT INTO deadline_history (task_id, old_deadline, new_deadline, changed_by, changed_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (task_id, old_dl_str, new_dl_str, user["id"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    # 3. Simpan Pesan Komentar
                    if sub and feedback:
                        execute_query("""
                            INSERT INTO feedback (submission_id, komentar, written_by, tanggal_ditulis) 
                            VALUES (?, ?, ?, ?)
                        """, (sub["id"], feedback, user["id"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    st.toast("Evaluasi dan riwayat berhasil disimpan!")
                    st.session_state["mon_view"] = "list"
                    st.rerun()
        
        if st.button("⬅️ Kembali ke Daftar"):
            st.session_state["mon_view"] = "list"
            st.rerun()


# =========================================================================
# 📅 MODUL: MONITORING LOGBOOK RUTINITAS HARIAN TIM
# =========================================================================
def render_logbook_monitoring(user):
    st.markdown("""
        <div class="header-card" style="background: linear-gradient(135deg, #1B263B 0%, #0D1B2A 100%);">
            <h2 style='margin:0;'>📅 Pantau Logbook Rutinitas</h2>
            <p style='margin:0; opacity:0.8;'>Audit rekaman produktivitas aktivitas harian mandiri dari staf Anda.</p>
        </div>
    """, unsafe_allow_html=True)

    # 🛠️ PERUBAHAN 3: Sekretaris Direksi diberi akses memantau seluruh logbook karyawan layaknya Dewan Direksi
    if user["divisi"] == "Dewan Direksi" or user["role"] == "Sekretaris Direksi":
        query_staff = "SELECT id, nama, role, divisi FROM users WHERE divisi != 'Dewan Direksi' ORDER BY nama ASC"
        daftar_bawahan = fetch_all(query_staff)
    else:
        # Supervisor Teknik & Kabag otomatis menarik staff di bawah naungannya
        query_staff = "SELECT id, nama, role, divisi FROM users WHERE atasan_id = ? ORDER BY nama ASC"
        daftar_bawahan = fetch_all(query_staff, (user["id"],))

    if not daftar_bawahan:
        st.info("💡 Tidak ada daftar bawahan langsung yang terikat dengan akun Anda.")
        return

    # Render Dropdown filter orang di atas area logbook
    staff_options = {f"{b['nama']} ({b['role']} - {b['divisi']})": b["id"] for b in daftar_bawahan}
    selected_display = st.selectbox("Pilih Anggota Tim yang Ingin Diaudit:", list(staff_options.keys()), key="sb_logbook_staff")
    target_user_id = staff_options[selected_display]

    st.markdown("---")

    # Jalankan Query pencarian records logbook milik target karyawan terpilih
    query_log = """
        SELECT rl.tanggal_input, jt.nama_tugas, rl.keterangan_progres, rl.tanggal_input
        FROM routine_logbooks rl
        JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id
        WHERE rl.user_id = ?
        ORDER BY rl.tanggal_input DESC, rl.tanggal_input DESC
    """
    records = fetch_all(query_log, (target_user_id,))

    if not records:
        st.warning("Karyawan ini belum memiliki catatan logbook tugas rutinitas.")
    else:
        # Hitung kalkulasi metrik hari kerja aktif secara kuantitatif
        total_hari = len(set([r["tanggal_input"] for r in records]))
        st.metric(label="Total Hari Mengisi Logbook", value=f"{total_hari} Hari")
        st.write("")
        
        # Render deretan baris logbook bergaya rapi
        for r in records:
            st.markdown(f"""
                <div class="logbook-row">
                    <div style="display:flex; justify-content:space-between; font-weight:bold; color:#1B263B; font-size:14px;">
                        <span>📅 Tanggal Kerja: {r['tanggal_input']}</span>
                        <span style="font-size:11px; color:gray; font-weight:normal;">Waktu Input: {r['tanggal_input']}</span>
                    </div>
                    <div style="margin-top: 6px; font-size:13px; color:#2A9D8F; font-weight:600;">📋 Kategori Pekerjaan: {r['nama_tugas']}</div>
                    <p style="margin: 6px 0 0 0; color:#444; font-size: 13.5px; line-height:1.4;">📝 <b>Hasil Kerja:</b> {r['keterangan_progres']}</p>
                </div>
            """, unsafe_allow_html=True)
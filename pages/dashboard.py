import streamlit as st
from database import fetch_all
from datetime import datetime, date
import matplotlib.pyplot as plt

def show_dashboard():
    # 🎨 UI Styling
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .header-card {
            background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
            padding: 20px; border-radius: 12px; color: white; margin-bottom: 25px;
        }
        [data-testid="stMetricValue"] { font-size: 28px; color: #1B263B; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.warning("Harus login dulu!")
        st.stop()

    user = st.session_state["user"]
    st.markdown('<div class="header-card"><h1>📊 Dashboard</h1><p>Analisis progres pengerjaan tugas & logbook aktivitas secara akurat.</p></div>', unsafe_allow_html=True)

    # =========================================================================
    # ⚙️ FILTER UTAMA: CAKUPAN DATA (BAHASA INDONESIA)
    # =========================================================================
    with st.container(border=True):
        if user["divisi"] == "Dewan Direksi":
            cakupan = "Tugas Tim"
        elif "Staff" in user["role"]:
            cakupan = "Tugas Saya"
        else:
            cakupan = st.radio("Cakupan Data:", ["Tugas Saya", "Tugas Tim"], horizontal=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # SPLIT HALAMAN UTAMA BERDASARKAN TAB RUTINITAS & NON-RUTINITAS
    # =========================================================================
    tab_non_rutin, tab_rutin = st.tabs(["🚀 Non-Rutinitas (Instruksi)", "📅 Rutinitas (Logbook Harian)"])

    # -------------------------------------------------------------------------
    # TAB 1: DASHBOARD NON-RUTINITAS (SISTEM TUGAS)
    # -------------------------------------------------------------------------
    with tab_non_rutin:
        st.subheader("Analisis Instruksi & Proyek Khusus")
        
        # Filter Rentang Tanggal Khusus Tugas
        with st.container(border=True):
            st.write("📅 **Periode Pembagian Tugas**")
            c1, c2 = st.columns(2)
            with c1:
                start_dt = st.date_input("Dari Tanggal (Tugas)", value=date(2026, 1, 1), key="start_task")
            with c2:
                end_dt = st.date_input("Sampai Tanggal (Tugas)", value=date.today(), key="end_task")

            sel_karyawan = "Semua"
            sel_divisi = "Semua"
            
            if cakupan == "Tugas Tim":
                st.markdown("<br>", unsafe_allow_html=True)
                f1, f2 = st.columns(2)
                with f1:
                    # Ambil daftar user sesuai hak akses
                    if user["divisi"] == "Dewan Direksi":
                        db_users = fetch_all("""
                            SELECT id, nama, role 
                            FROM users
                            ORDER BY role ASC, nama ASC
                        """)
                    else:
                        db_users = fetch_all("""
                            SELECT id, nama, role 
                            FROM users
                            WHERE atasan_id = ?
                            ORDER BY role ASC, nama ASC
                        """, (user["id"],))

                    # Format dropdown: Role - Nama
                    karyawan_options = ["Semua"]
                    karyawan_map = {}

                    for u in db_users:
                        label = f"{u['role']} - {u['nama']}"
                        karyawan_options.append(label)
                        karyawan_map[label] = u["id"]

                    sel_karyawan = st.selectbox(
                        "Pilih Karyawan",
                        karyawan_options,
                        key="karyawan_task"
                    )

                with f2:
                    if user["divisi"] == "Dewan Direksi":
                        divisi_list = ["Semua", "Promosi & CS", "Business Development", "Sekretaris Direksi", "Marketing", "Umum & Personalia", "Keuangan", "Teknik"]
                        sel_divisi = st.selectbox("Filter Divisi (Tugas)", divisi_list, key="div_task")
                    else:
                        st.info(f"📍 Divisi Dipantau: **{user['divisi']}**")
                        sel_divisi = user["divisi"]

        # DATA PROCESSING TASK
        if cakupan == "Tugas Saya":
            query = "SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id WHERE t.assigned_to = ?"
            raw_tasks = fetch_all(query, (user["id"],))
        else:
            if user["divisi"] == "Dewan Direksi":
                query = "SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id"
                raw_tasks = fetch_all(query)
            else:
                query = "SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id WHERE u.atasan_id = ?"
                raw_tasks = fetch_all(query, (user["id"],))

        tasks = []
        for t in raw_tasks:
            try:
                raw_assign = t["tanggal_assign"]
                if not raw_assign: continue
                assign_date_str = raw_assign.split(" ")[0]
                created_date = datetime.strptime(assign_date_str, "%Y-%m-%d").date()
                
                if start_dt <= created_date <= end_dt:
                    match_divisi = (sel_divisi == "Semua" or t["divisi"] == sel_divisi)
                if sel_karyawan == "Semua":
                    match_karyawan = True
                else:
                    selected_user_id = karyawan_map.get(sel_karyawan)
                    match_karyawan = (t["assigned_to"] == selected_user_id)

                if match_divisi and match_karyawan:
                    tasks.append(t)
            except: continue

        if not tasks:
            st.warning("⚠️ Tidak ada data tugas khusus yang ditemukan untuk kriteria ini.")
        else:
            # HITUNG METRIK KINERJA TUGAS
            completed = [t for t in tasks if t["status_task"].lower() == "approved"]
            not_completed = len(tasks) - len(completed)
            today = date.today()
            on_time, late = 0, 0
            
            # Hitung tugas yang approved per orang untuk keperluan fitur barumu
            approved_per_karyawan = {}
            
            for t in tasks:
                try:
                    task_id = t["id"]
                    nama_karyawan = t["nama_karyawan"]
                    status_task = t["status_task"].lower()
                    
                    # Catat ke dictionary jika statusnya approved
                    if status_task == "approved":
                        approved_per_karyawan[nama_karyawan] = approved_per_karyawan.get(nama_karyawan, 0) + 1
                    elif nama_karyawan not in approved_per_karyawan:
                        # Tetap daftarkan nama orang tersebut dengan nilai 0 agar muncul di grafik
                        approved_per_karyawan[nama_karyawan] = 0

                    subs = fetch_all("SELECT tanggal_submit FROM submissions WHERE task_id = ? ORDER BY tanggal_submit ASC", (task_id,))
                    dl_history = fetch_all("SELECT new_deadline, changed_at FROM deadline_history WHERE task_id = ? ORDER BY changed_at ASC", (task_id,))
                    
                    if subs:
                        first_submit_str = subs[0]["tanggal_submit"].split(" ")[0]
                        submit_date = datetime.strptime(first_submit_str, "%Y-%m-%d").date()
                        target_deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
                        
                        for hist in dl_history:
                            change_date_str = hist["changed_at"].split(" ")[0]
                            change_date = datetime.strptime(change_date_str, "%Y-%m-%d").date()
                            if change_date <= submit_date:
                                target_deadline = datetime.strptime(hist["new_deadline"], "%Y-%m-%d").date()
                        
                        if submit_date <= target_deadline: on_time += 1
                        else: late += 1
                    else:
                        current_deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
                        if current_deadline >= today: on_time += 1
                        else: late += 1
                except: on_time += 1

            # RENDER VISUALISASI TUGAS NON-RUTIN
            m1, m2 = st.columns([1, 1.5], gap="large")
            with m1:
                st.write("**Persentase Kelayakan Selesai (Approved)**")
                fig, ax = plt.subplots(figsize=(4, 4))
                sizes = [len(completed), not_completed] if (len(completed) + not_completed) > 0 else [0, 1]
                ax.pie(sizes, labels=["Disetujui", "Pending"], autopct='%1.1f%%', startangle=90, colors=['#1B263B', '#E0E1DD'])
                ax.axis('equal')
                st.pyplot(fig)

            with m2:
                st.write("**Ringkasan Angka Kunci**")
                sm1, sm2 = st.columns(2)
                sm1.metric("Total Tugas Instruksi", len(tasks))
                sm1.metric("Selesai Tepat Waktu", on_time)
                sm2.metric("Status Approved", len(completed))
                sm2.metric("Terlambat / Lewat Deadline", late, delta=late if late > 0 else None, delta_color="inverse")

            # 🚀 GRAFIK BARU: JUMlAH TUGAS APPROVED PER KARYAWAN (Hanya untuk Tugas Tim)
            if cakupan == "Tugas Tim" and approved_per_karyawan:
                st.markdown("---")
                st.write("**🎯 Jumlah Tugas Khusus yang Berhasil Disetujui (Approved) per Anggota Tim:**")
                
                karyawan_tugas = list(approved_per_karyawan.keys())
                skor_tugas = list(approved_per_karyawan.values())
                
                fig_user_task, ax_user_task = plt.subplots(figsize=(8, 3.5))
                bars_ut = ax_user_task.bar(karyawan_tugas, skor_tugas, color='#1B263B', width=0.4)
                ax_user_task.spines['top'].set_visible(False)
                ax_user_task.spines['right'].set_visible(False)
                ax_user_task.set_ylabel("Jumlah Tugas")
                ax_user_task.bar_label(bars_ut, padding=3, weight='bold')
                plt.tight_layout()
                st.pyplot(fig_user_task)

            st.markdown("---")
            st.write("**Detail Distribusi Status Saat Ini:**")
            status_cols = st.columns(4)
            for i, s in enumerate(["assigned", "submitted", "revision", "approved"]):
                count = len([t for t in tasks if t["status_task"].lower() == s])
                status_cols[i].metric(s.capitalize(), count)


    # -------------------------------------------------------------------------
    # TAB 2: DASHBOARD RUTINITAS (MODUL LOGBOOK HARIAN)
    # -------------------------------------------------------------------------
    with tab_rutin:
        st.subheader("Analisis Beban Kerja Harian (Logbook)")
        
        # Filter Rentang Tanggal Khusus Logbook
        with st.container(border=True):
            st.write("📅 **Periode Pengisian Aktivitas Karyawan**")
            lr1, lr2 = st.columns(2)
            with lr1:
                start_log_dt = st.date_input("Dari Tanggal (Logbook)", value=date(2026, 1, 1), key="start_log")
            with lr2:
                end_log_dt = st.date_input("Sampai Tanggal (Logbook)", value=date.today(), key="end_log")

            sel_div_log = "Semua"
            if cakupan == "Tugas Tim":
                st.markdown("<br>", unsafe_allow_html=True)
                if user["divisi"] == "Dewan Direksi":
                    divisi_list_log = ["Semua", "Promosi & CS", "Business Development", "Sekretaris Direksi", "Marketing", "Umum & Personalia", "Keuangan", "Teknik"]
                    sel_div_log = st.selectbox("Filter Divisi (Logbook)", divisi_list_log, key="div_log")
                else:
                    st.info(f"📍 Memantau Logbook Divisi: **{user['divisi']}**")
                    sel_div_log = user["divisi"]

        # DATA PROCESSING LOGBOOK
        if cakupan == "Tugas Saya":
            query_log = """
                SELECT rl.*, jt.nama_tugas, u.nama, u.divisi 
                FROM routine_logbooks rl
                JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id
                JOIN users u ON rl.user_id = u.id
                WHERE rl.user_id = ?
            """
            raw_logs = fetch_all(query_log, (user["id"],))
        else:
            if user["divisi"] == "Dewan Direksi":
                query_log = """
                    SELECT rl.*, jt.nama_tugas, u.nama, u.divisi 
                    FROM routine_logbooks rl
                    JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id
                    JOIN users u ON rl.user_id = u.id
                """
                raw_logs = fetch_all(query_log)
            else:
                query_log = """
                    SELECT rl.*, jt.nama_tugas, u.nama, u.divisi 
                    FROM routine_logbooks rl
                    JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id
                    JOIN users u ON rl.user_id = u.id
                    WHERE u.atasan_id = ?
                """
                raw_logs = fetch_all(query_log, (user["id"],))

        # Terapkan filter rentang waktu dan divisi logbook
        valid_logs = []
        for log in raw_logs:
            try:
                log_date = datetime.strptime(log["tanggal_input"], "%Y-%m-%d").date()
                if start_log_dt <= log_date <= end_log_dt:
                    if sel_div_log == "Semua" or log["divisi"] == sel_div_log:
                        valid_logs.append(log)
            except: continue

        if not valid_logs:
            st.warning("⚠️ Tidak ada data rekaman logbook rutin yang cocok pada periode ini.")
        else:
            # LOGIKA HITUNG METRIK UTAMA LOGBOOK
            total_log_entries = len(valid_logs)
            
            karyawan_counts = {}
            kategori_counts = {}
            for log in valid_logs:
                nama = log["nama"]
                kat = log["nama_tugas"]
                karyawan_counts[nama] = karyawan_counts.get(nama, 0) + 1
                kategori_counts[kat] = kategori_counts.get(kat, 0) + 1
            
            karyawan_teraktif = max(karyawan_counts, key=karyawan_counts.get) if karyawan_counts else "Tidak Ada"
            kategori_terbanyak = max(kategori_counts, key=kategori_counts.get) if kategori_counts else "Tidak Ada"

            # Tampilkan 3 Metric Cards Sejajar
            lm1, lm2, lm3 = st.columns(3)
            lm1.metric("Total Laporan Rutin", f"{total_log_entries} Record")
            
            if cakupan == "Tugas Tim":
                lm2.metric("Karyawan Paling Aktif", karyawan_teraktif, f"{karyawan_counts.get(karyawan_teraktif, 0)}x Isi")
            else:
                total_hari_aktif = len(set([l["tanggal_input"] for l in valid_logs]))
                lm2.metric("Jumlah Hari Kerja Efektif", f"{total_hari_aktif} Hari")
                
            lm3.metric("Kategori Kerja Terbanyak", 
                       kategori_terbanyak if len(kategori_terbanyak) <= 15 else kategori_terbanyak[:15]+"...", 
                       f"{kategori_counts.get(kategori_terbanyak, 0)} Aktivitas")

            st.markdown("---")

            # 📊 SEKSI VISUALISASI DUA GRAFIK UNTUK RUTINITAS
            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.write("**📋 Distribusi Kategori Pekerjaan (Jobdesc):**")
                categories = list(kategori_counts.keys())
                counts = list(kategori_counts.values())
                clean_categories = [c if len(c) <= 20 else c[:17]+"..." for c in categories]

                fig_bar, ax_bar = plt.subplots(figsize=(5, 4))
                bars = ax_bar.barh(clean_categories, counts, color='#2A9D8F', height=0.5)
                ax_bar.spines['top'].set_visible(False)
                ax_bar.spines['right'].set_visible(False)
                ax_bar.set_xlabel("Jumlah Aktivitas")
                ax_bar.bar_label(bars, padding=3, fontname='sans-serif', weight='bold')
                plt.tight_layout()
                st.pyplot(fig_bar)

            with col_graph2:
                if cakupan == "Tugas Tim" and karyawan_counts:
                    st.write("**👥 Jumlah Pengisian Logbook per Anggota Tim:**")
                    list_nama_karyawan = list(karyawan_counts.keys())
                    list_jumlah_logbook = list(karyawan_counts.values())

                    fig_user_log, ax_user_log = plt.subplots(figsize=(5, 4))
                    # Warna jingga coral khas audit logbook agar beda dari grafik kategori
                    bars_ul = ax_user_log.barh(list_nama_karyawan, list_jumlah_logbook, color='#E76F51', height=0.5)
                    ax_user_log.spines['top'].set_visible(False)
                    ax_user_log.spines['right'].set_visible(False)
                    ax_user_log.set_xlabel("Total Hari Melapor")
                    ax_user_log.bar_label(bars_ul, padding=3, fontname='sans-serif', weight='bold')
                    plt.tight_layout()
                    st.pyplot(fig_user_log)
                else:
                    # Tampilan alternatif jika melihat dashboard milik sendiri
                    st.info("ℹ️ Grafik performa per orang hanya tersedia pada menu peninjauan Tugas Tim.")
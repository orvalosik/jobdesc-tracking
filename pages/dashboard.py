import streamlit as st
from database import fetch_all
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px

def show_dashboard():
    st.markdown("""
        <style>
        /* Header card */
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px;
            border-radius: 16px;
            color: white;
            margin-bottom: 24px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .header-card h2 {
            margin: 0 0 4px 0;
            font-size: 22px;
            font-weight: 600;
            color: white !important;
        }
        .header-card p {
            margin: 0;
            font-size: 13px;
            color: #94A3B8 !important;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 20px;
        }
        [data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748B !important; }
        [data-testid="stMetricValue"] { font-size: 26px !important; color: #1E293B !important; font-weight: 700 !important; }

        /* Status badge */
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-assigned  { background:#EFF6FF; color:#1D4ED8; }
        .badge-submitted { background:#FFF7ED; color:#C2410C; }
        .badge-revision  { background:#FEF9C3; color:#A16207; }
        .badge-approved  { background:#DCFCE7; color:#15803D; }

        /* Filter container */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border-color: #E2E8F0 !important;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: #F1F5F9;
            padding: 4px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 6px 18px;
            font-size: 13px;
        }
        .stTabs [aria-selected="true"] {
            background: white !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.warning("Harus login dulu!")
        st.stop()

    user = st.session_state["user"]

    # Header
    now = datetime.now()
    greeting = "Selamat pagi" if now.hour < 12 else ("Selamat siang" if now.hour < 15 else ("Selamat sore" if now.hour < 18 else "Selamat malam"))
    st.markdown(f"""
        <div class="header-card">
            <h2>Dashboard</h2>
            <p>{greeting}, <strong style="color:#10B981;">{user['nama']}</strong> — {now.strftime('%A, %d %B %Y')}</p>
        </div>
    """, unsafe_allow_html=True)

    cakupan = "Tugas Tim" if user["divisi"] == "Dewan Direksi" else "Tugas Saya"

    tab_non_rutin, tab_rutin = st.tabs([
        "Non-Rutinitas (Instruksi)",
        "Rutinitas (Logbook Harian)"
    ])

    # =========================================================================
    # TAB 1: NON-RUTINITAS
    # =========================================================================
    with tab_non_rutin:
        with st.container(border=True):
            st.markdown(":material/calendar_month: **Periode Pembagian Tugas**")
            c1, c2 = st.columns(2)
            with c1:
                start_dt = st.date_input("Dari Tanggal", value=date(2026, 1, 1), key="start_task")
            with c2:
                end_dt = st.date_input("Sampai Tanggal", value=date.today(), key="end_task")

            sel_karyawan = "Semua"
            sel_divisi   = "Semua"
            karyawan_map = {}

            if cakupan == "Tugas Tim":
                st.markdown("<br>", unsafe_allow_html=True)
                f1, f2 = st.columns(2)
                with f1:
                    if user["divisi"] == "Dewan Direksi":
                        db_users = fetch_all("SELECT id, nama, role FROM users ORDER BY role, nama")
                    else:
                        db_users = fetch_all("SELECT id, nama, role FROM users WHERE atasan_id = ? ORDER BY role, nama", (user["id"],))

                    karyawan_options = ["Semua"]
                    for u in db_users:
                        label = f"{u['role']} — {u['nama']}"
                        karyawan_options.append(label)
                        karyawan_map[label] = u["id"]

                    sel_karyawan = st.selectbox(":material/person: Karyawan", karyawan_options, key="karyawan_task")

                with f2:
                    if user["divisi"] == "Dewan Direksi":
                        divisi_list = ["Semua","Promosi & CS","Business Development","Sekretaris Direksi","Marketing","Umum & Personalia","Keuangan","Teknik"]
                        sel_divisi = st.selectbox(":material/apartment: Divisi", divisi_list, key="div_task")
                    else:
                        st.info(f"Divisi dipantau: **{user['divisi']}**")
                        sel_divisi = user["divisi"]

        # Fetch & filter tasks
        if cakupan == "Tugas Saya":
            raw_tasks = fetch_all("SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id WHERE t.assigned_to = ?", (user["id"],))
        elif user["divisi"] == "Dewan Direksi":
            raw_tasks = fetch_all("SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id")
        else:
            raw_tasks = fetch_all("SELECT t.*, u.divisi, u.role, u.nama as nama_karyawan FROM tasks t JOIN users u ON t.assigned_to = u.id WHERE u.atasan_id = ?", (user["id"],))

        tasks = []
        for t in raw_tasks:
            try:
                raw_assign = t["tanggal_assign"]
                if not raw_assign: continue
                created_date = datetime.strptime(raw_assign.split(" ")[0], "%Y-%m-%d").date()
                if not (start_dt <= created_date <= end_dt): continue
                match_divisi   = (sel_divisi == "Semua" or t["divisi"] == sel_divisi)
                match_karyawan = (sel_karyawan == "Semua" or t["assigned_to"] == karyawan_map.get(sel_karyawan))
                if match_divisi and match_karyawan:
                    tasks.append(t)
            except: continue

        if not tasks:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(":material/search_off: Tidak ada data tugas untuk kriteria ini.")
        else:
            completed     = [t for t in tasks if t["status_task"].lower() == "approved"]
            not_completed = len(tasks) - len(completed)
            today         = date.today()
            on_time, late = 0, 0
            approved_per_karyawan = {}

            for t in tasks:
                try:
                    nama_k  = t["nama_karyawan"]
                    status  = t["status_task"].lower()
                    task_id = t["id"]

                    if status == "approved":
                        approved_per_karyawan[nama_k] = approved_per_karyawan.get(nama_k, 0) + 1
                    elif nama_k not in approved_per_karyawan:
                        approved_per_karyawan[nama_k] = 0

                    subs       = fetch_all("SELECT tanggal_submit FROM submissions WHERE task_id = ? ORDER BY tanggal_submit ASC", (task_id,))
                    dl_history = fetch_all("SELECT new_deadline, changed_at FROM deadline_history WHERE task_id = ? ORDER BY changed_at ASC", (task_id,))

                    if subs:
                        submit_date     = datetime.strptime(subs[0]["tanggal_submit"].split(" ")[0], "%Y-%m-%d").date()
                        target_deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
                        for hist in dl_history:
                            change_date = datetime.strptime(hist["changed_at"].split(" ")[0], "%Y-%m-%d").date()
                            if change_date <= submit_date:
                                target_deadline = datetime.strptime(hist["new_deadline"], "%Y-%m-%d").date()
                        if submit_date <= target_deadline: on_time += 1
                        else: late += 1
                    else:
                        if datetime.strptime(t["deadline"], "%Y-%m-%d").date() >= today: on_time += 1
                        else: late += 1
                except: on_time += 1

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Metrik ──
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(":material/assignment: Total Tugas", len(tasks))
            m2.metric(":material/check_circle: Approved", len(completed))
            m3.metric(":material/schedule: Tepat Waktu", on_time)
            m4.metric(":material/warning: Terlambat", late, delta=late if late > 0 else None, delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Chart baris 1 ──
            ch1, ch2 = st.columns(2)

            with ch1:
                st.markdown("**Kelayakan Penyelesaian Tugas**")
                labels = ["Disetujui", "Pending"]
                values = [len(completed), not_completed]
                colors = ["#10B981", "#E2E8F0"]

                fig_donut = go.Figure(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.65,
                    marker=dict(colors=colors, line=dict(color="white", width=2)),
                    textinfo="percent",
                    textfont=dict(size=13),
                    hovertemplate="%{label}: %{value} tugas<extra></extra>"
                ))
                fig_donut.add_annotation(
                    text=f"<b>{len(completed)}</b><br><span style='font-size:11px'>Approved</span>",
                    x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#1E293B"),
                    align="center"
                )
                fig_donut.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=260,
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=12)),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with ch2:
                st.markdown("**Status Distribusi Tugas**")
                status_labels = ["Assigned", "Submitted", "Revision", "Approved"]
                status_colors = ["#3B82F6", "#F97316", "#EAB308", "#10B981"]
                status_values = [len([t for t in tasks if t["status_task"].lower() == s.lower()]) for s in status_labels]

                fig_bar = go.Figure(go.Bar(
                    x=status_labels,
                    y=status_values,
                    marker=dict(color=status_colors, line=dict(color="white", width=1)),
                    text=status_values,
                    textposition="outside",
                    hovertemplate="%{x}: %{y} tugas<extra></extra>"
                ))
                fig_bar.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=260,
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
                    xaxis=dict(showgrid=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    bargap=0.35
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── Chart approved per karyawan ──
            if cakupan == "Tugas Tim" and approved_per_karyawan:
                st.markdown("**Tugas Approved per Anggota Tim**")
                sorted_items  = sorted(approved_per_karyawan.items(), key=lambda x: x[1], reverse=True)
                names_sorted  = [i[0] for i in sorted_items]
                values_sorted = [i[1] for i in sorted_items]

                fig_team = go.Figure(go.Bar(
                    y=names_sorted,
                    x=values_sorted,
                    orientation="h",
                    marker=dict(
                        color=values_sorted,
                        colorscale=[[0, "#D1FAE5"], [1, "#059669"]],
                        line=dict(color="white", width=1)
                    ),
                    text=values_sorted,
                    textposition="outside",
                    hovertemplate="%{y}: %{x} tugas approved<extra></extra>"
                ))
                fig_team.update_layout(
                    margin=dict(t=10, b=10, l=10, r=80),
                    height=max(200, len(names_sorted) * 44),
                    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
                    yaxis=dict(showgrid=False, autorange="reversed"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_team, use_container_width=True)

    # =========================================================================
    # TAB 2: RUTINITAS (LOGBOOK)
    # =========================================================================
    with tab_rutin:
        with st.container(border=True):
            st.markdown(":material/calendar_month: **Periode Pengisian Aktivitas**")
            lr1, lr2 = st.columns(2)
            with lr1:
                start_log_dt = st.date_input("Dari Tanggal", value=date(2026, 1, 1), key="start_log")
            with lr2:
                end_log_dt = st.date_input("Sampai Tanggal", value=date.today(), key="end_log")

            sel_div_log = "Semua"
            if cakupan == "Tugas Tim":
                st.markdown("<br>", unsafe_allow_html=True)
                if user["divisi"] == "Dewan Direksi":
                    divisi_list_log = ["Semua","Promosi & CS","Business Development","Sekretaris Direksi","Marketing","Umum & Personalia","Keuangan","Teknik"]
                    sel_div_log = st.selectbox(":material/apartment: Divisi", divisi_list_log, key="div_log")
                else:
                    st.info(f"Memantau logbook divisi: **{user['divisi']}**")
                    sel_div_log = user["divisi"]

        # Fetch & filter logbook
        if cakupan == "Tugas Saya":
            raw_logs = fetch_all("SELECT rl.*, jt.nama_tugas, u.nama, u.divisi FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id JOIN users u ON rl.user_id = u.id WHERE rl.user_id = ?", (user["id"],))
        elif user["divisi"] == "Dewan Direksi":
            raw_logs = fetch_all("SELECT rl.*, jt.nama_tugas, u.nama, u.divisi FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id JOIN users u ON rl.user_id = u.id")
        else:
            raw_logs = fetch_all("SELECT rl.*, jt.nama_tugas, u.nama, u.divisi FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id = jt.id JOIN users u ON rl.user_id = u.id WHERE u.atasan_id = ?", (user["id"],))

        valid_logs = []
        for log in raw_logs:
            try:
                log_date = datetime.strptime(log["tanggal_input"], "%Y-%m-%d").date()
                if start_log_dt <= log_date <= end_log_dt:
                    if sel_div_log == "Semua" or log["divisi"] == sel_div_log:
                        valid_logs.append(log)
            except: continue

        if not valid_logs:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(":material/search_off: Tidak ada data logbook untuk periode ini.")
        else:
            karyawan_counts = {}
            kategori_counts = {}
            for log in valid_logs:
                karyawan_counts[log["nama"]]       = karyawan_counts.get(log["nama"], 0) + 1
                kategori_counts[log["nama_tugas"]] = kategori_counts.get(log["nama_tugas"], 0) + 1

            karyawan_teraktif   = max(karyawan_counts, key=karyawan_counts.get)
            kategori_terbanyak  = max(kategori_counts, key=kategori_counts.get)
            total_hari_aktif    = len(set([l["tanggal_input"] for l in valid_logs]))

            st.markdown("<br>", unsafe_allow_html=True)

            lm1, lm2, lm3 = st.columns(3)
            lm1.metric(":material/description: Total Laporan", f"{len(valid_logs)} record")
            if cakupan == "Tugas Tim":
                lm2.metric(":material/emoji_events: Paling Aktif", karyawan_teraktif, f"{karyawan_counts[karyawan_teraktif]}x")
            else:
                lm2.metric(":material/today: Hari Kerja Efektif", f"{total_hari_aktif} hari")
            label_kat = kategori_terbanyak if len(kategori_terbanyak) <= 18 else kategori_terbanyak[:16]+"…"
            lm3.metric(":material/work: Aktivitas Terbanyak", label_kat, f"{kategori_counts[kategori_terbanyak]}x")

            st.markdown("<br>", unsafe_allow_html=True)

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("**Distribusi Kategori Pekerjaan**")
                cats   = list(kategori_counts.keys())
                cnts   = list(kategori_counts.values())
                labels_clean = [c if len(c) <= 22 else c[:20]+"…" for c in cats]

                fig_hbar = go.Figure(go.Bar(
                    y=labels_clean,
                    x=cnts,
                    orientation="h",
                    marker=dict(
                        color=cnts,
                        colorscale=[[0, "#D1FAE5"], [1, "#059669"]],
                    ),
                    text=cnts,
                    textposition="outside",
                    hovertemplate="%{y}: %{x} aktivitas<extra></extra>"
                ))
                fig_hbar.update_layout(
                    margin=dict(t=10, b=10, l=10, r=50),
                    height=max(200, len(cats) * 40),
                    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
                    yaxis=dict(showgrid=False, autorange="reversed"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_hbar, use_container_width=True)

            with col_g2:
                if cakupan == "Tugas Tim":
                    st.markdown("**Pengisian Logbook per Anggota**")
                    names = list(karyawan_counts.keys())
                    vals  = list(karyawan_counts.values())

                    fig_ul = go.Figure(go.Bar(
                        y=names,
                        x=vals,
                        orientation="h",
                        marker=dict(
                            color=vals,
                            colorscale=[[0, "#FED7AA"], [1, "#EA580C"]],
                        ),
                        text=vals,
                        textposition="outside",
                        hovertemplate="%{y}: %{x} laporan<extra></extra>"
                    ))
                    fig_ul.update_layout(
                        margin=dict(t=10, b=10, l=10, r=50),
                        height=max(200, len(names) * 40),
                        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
                        yaxis=dict(showgrid=False, autorange="reversed"),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_ul, use_container_width=True)
                else:
                    st.info("Grafik perbandingan per orang tersedia di tampilan Tugas Tim.")
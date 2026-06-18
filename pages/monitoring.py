import streamlit as st
from database import fetch_all, fetch_one, execute_query
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")

# =========================================================================
# KONSTANTA ROLE
# =========================================================================
ROLE_DIREKSI = ["Direktur Utama", "Direktur"]

ROLE_MANAGER_NONSTRUKTURAL = [
    "Manager Umum & Personalia",
    "Manager Marketing",
    "Manager Keuangan",
    "Manager Teknik",
    "Business Development",
    "Sekretaris Direksi",
    "Promosi & CS",
]

# Role yang bisa dipantau oleh Sekretaris Direksi
ROLE_SEKRETARIS_DAPAT_PANTAU = [
    "Manager Marketing",
    "Manager Umum & Personalia",
    "Manager Keuangan",
    "Manager Teknik",
    "Business Development",
    "Promosi & CS",
    "Kabag. Promosi & CS",
    "Supervisor Civil & Architectural",
]

def is_direksi(role):
    return role in ROLE_DIREKSI

def is_sekretaris(role):
    return role == "Sekretaris Direksi"

def is_manager_or_nonstruktural(role):
    return role in ROLE_MANAGER_NONSTRUKTURAL


# =========================================================================
# SHOW MONITORING
# =========================================================================
def show_monitoring():
    st.markdown("""
        <style>
        .header-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 24px 28px; border-radius: 16px; margin-bottom: 24px;
            border: 1px solid rgba(16,185,129,0.2);
        }
        .header-card h2 { margin:0 0 4px 0; font-size:22px; font-weight:600; color:white !important; }
        .header-card p  { margin:0; font-size:13px; color:#94A3B8 !important; }

        .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
        .badge-assigned  { background:#EFF6FF; color:#1D4ED8; }
        .badge-submitted { background:#FFF7ED; color:#C2410C; }
        .badge-revision  { background:#FEF2F2; color:#DC2626; }
        .badge-approved  { background:#DCFCE7; color:#15803D; }

        .task-row {
            background: white; padding: 16px 20px; border-radius: 12px;
            border: 1px solid #E2E8F0; margin-bottom: 8px;
        }
        .task-row-approved {
            background: #F0FDF4; padding: 16px 20px; border-radius: 12px;
            border: 1px solid #D1FAE5; border-left: 4px solid #10B981;
            margin-bottom: 8px;
        }

        .log-card {
            background: #F8FAFC; padding: 12px 16px;
            border-left: 4px solid #10B981; border-radius: 8px; margin-bottom: 10px;
        }
        .log-card-dl {
            background: #FFF7ED; padding: 12px 16px;
            border-left: 4px solid #F97316; border-radius: 8px; margin-bottom: 10px;
        }
        .log-card-fb {
            margin-left: 20px; padding: 8px 12px;
            background: white; border-left: 2px dashed #EF4444;
            border-radius: 0 8px 8px 0; font-size: 13px; margin-bottom: 10px;
        }

        .logbook-row {
            background: white; padding: 14px 18px; border-radius: 12px;
            border: 1px solid #E2E8F0; border-left: 4px solid #10B981;
            margin-bottom: 8px;
        }

        .readonly-banner {
            background: #EFF6FF; border: 1px solid #BFDBFE;
            border-left: 4px solid #3B82F6; border-radius: 10px;
            padding: 10px 14px; margin-bottom: 16px;
            font-size: 13px; color: #1D4ED8;
        }

        section.main button[kind="primary"],
        section.main div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg,#10B981,#059669) !important;
            color: white !important; border: none !important;
            font-weight: 600 !important; border-radius: 10px !important;
        }
        .st-key-del_task button {
            background: transparent !important; color: #EF4444 !important;
            border: 1px solid rgba(239,68,68,.3) !important; border-radius: 8px !important;
        }
        .st-key-del_task button:hover { background: rgba(239,68,68,.06) !important; }

        .stTabs [data-baseweb="tab-list"] {
            gap:4px; background:#F1F5F9; padding:4px; border-radius:10px;
        }
        .stTabs [data-baseweb="tab"] { border-radius:8px; padding:6px 16px; font-size:13px; }
        .stTabs [aria-selected="true"] {
            background:white !important; font-weight:600 !important;
            box-shadow:0 1px 4px rgba(0,0,0,.08);
        }
        </style>
    """, unsafe_allow_html=True)

    user = st.session_state["user"]
    role = user["role"]

    if "mon_view" not in st.session_state:
        st.session_state["mon_view"] = "list"

    if st.session_state["mon_view"] == "edit":
        render_edit_action(user)
        return

    # Direktur & Direktur Utama: 3 tab (termasuk logbook)
    if is_direksi(role):
        tab_non_rutin, tab_approved, tab_rutin = st.tabs([
            "Non-Rutinitas (Aktif)",
            "Selesai & Disetujui",
            "Pantau Logbook Rutinitas",
        ])
        with tab_non_rutin:
            render_list(user, only_approved=False)
        with tab_approved:
            render_list(user, only_approved=True)
        with tab_rutin:
            render_logbook_monitoring(user)

    # Sekretaris Direksi: 2 tab, bisa lihat semua tapi review/hapus terbatas
    elif is_sekretaris(role):
        tab_non_rutin, tab_approved = st.tabs([
            "Non-Rutinitas (Aktif)",
            "Selesai & Disetujui",
        ])
        with tab_non_rutin:
            render_list(user, only_approved=False)
        with tab_approved:
            render_list(user, only_approved=True)

    # Manager & Nonstruktural lainnya: 2 tab
    elif is_manager_or_nonstruktural(role):
        tab_non_rutin, tab_approved = st.tabs([
            "Non-Rutinitas (Aktif)",
            "Selesai & Disetujui",
        ])
        with tab_non_rutin:
            render_list(user, only_approved=False)
        with tab_approved:
            render_list(user, only_approved=True)

    else:
        st.warning("Anda tidak memiliki akses ke halaman ini.")


# =========================================================================
# QUERY TUGAS BERDASARKAN ROLE
# =========================================================================
def get_tasks_for_user(user):
    role = user["role"]

    if is_direksi(role):
        placeholders = ",".join("?" * len(ROLE_MANAGER_NONSTRUKTURAL))
        tasks = fetch_all(f"""
            SELECT t.*,
                   ua.nama  as nama_assigner,  ua.role  as role_assigner,  ua.divisi as divisi_assigner,
                   ub.nama  as nama_karyawan,  ub.role  as role_karyawan,  ub.divisi as divisi_karyawan
            FROM tasks t
            JOIN users ua ON t.assigned_by  = ua.id
            JOIN users ub ON t.assigned_to  = ub.id
            WHERE ua.role IN ({placeholders})
               OR ub.role IN ({placeholders})
            ORDER BY t.tanggal_assign DESC
        """, ROLE_MANAGER_NONSTRUKTURAL * 2)

    elif is_sekretaris(role):
        # Sekretaris bisa lihat:
        # 1. Tugas yang dia sendiri assign (ke siapapun)
        # 2. Tugas antar sesama ROLE_SEKRETARIS_DAPAT_PANTAU (read-only)
        all_roles = ROLE_SEKRETARIS_DAPAT_PANTAU
        placeholders = ",".join("?" * len(all_roles))
        tasks = fetch_all(f"""
            SELECT t.*,
                   ua.nama  as nama_assigner,  ua.role  as role_assigner,  ua.divisi as divisi_assigner,
                   ub.nama  as nama_karyawan,  ub.role  as role_karyawan,  ub.divisi as divisi_karyawan
            FROM tasks t
            JOIN users ua ON t.assigned_by = ua.id
            JOIN users ub ON t.assigned_to = ub.id
            WHERE t.assigned_by = ?
               OR (
                   (ua.role IN ({placeholders}) OR ub.role IN ({placeholders}))
               )
            ORDER BY t.tanggal_assign DESC
        """, [user["id"]] + all_roles + all_roles)

    elif is_manager_or_nonstruktural(role):
        tasks = fetch_all("""
            SELECT t.*,
                   ua.nama  as nama_assigner,  ua.role  as role_assigner,  ua.divisi as divisi_assigner,
                   ub.nama  as nama_karyawan,  ub.role  as role_karyawan,  ub.divisi as divisi_karyawan
            FROM tasks t
            JOIN users ua ON t.assigned_by = ua.id
            JOIN users ub ON t.assigned_to = ub.id
            WHERE t.assigned_by = ?
            ORDER BY t.tanggal_assign DESC
        """, [user["id"]])

    else:
        tasks = []

    return tasks


# =========================================================================
# CEK APAKAH USER BOLEH REVIEW/HAPUS TUGAS INI
# =========================================================================
def can_modify_task(user, task):
    """
    Sekretaris Direksi hanya boleh review/hapus tugas yang dia sendiri assign.
    Direksi dan Manager/Nonstruktural lainnya boleh semua.
    """
    role = user["role"]
    if is_sekretaris(role):
        return task["assigned_by"] == user["id"]
    return True


# =========================================================================
# DAFTAR TUGAS
# =========================================================================
def render_list(user, only_approved=False):
    role = user["role"]

    if not only_approved:
        st.markdown("""
            <div class="header-card">
                <h2>Monitoring & Review Tugas</h2>
                <p>Evaluasi hasil kerja instruksi khusus tim dan berikan keputusan.</p>
            </div>
        """, unsafe_allow_html=True)
        if is_sekretaris(role):
            st.markdown("""
                <div class="readonly-banner">
                    ℹ️ Anda dapat memantau semua tugas di bawah ini.
                    Aksi <strong>Review</strong> dan <strong>Hapus</strong> hanya tersedia
                    untuk tugas yang Anda assign sendiri.
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="header-card">
                <h2>Arsip Tugas Disetujui</h2>
                <p>Daftar seluruh tugas yang telah selesai dan mendapat persetujuan.</p>
            </div>
        """, unsafe_allow_html=True)

    tasks = get_tasks_for_user(user)

    if not tasks:
        st.info("Belum ada tugas untuk dimonitor.")
        return

    if only_approved:
        tasks = [t for t in tasks if t["status_task"].lower() == "approved"]
    else:
        tasks = [t for t in tasks if t["status_task"].lower() != "approved"]

    # ── Filter UI ──
    with st.container(border=True):
        if not only_approved:
            f1, f2, f3 = st.columns(3)
            with f1:
                divisi_opts = ["Semua Divisi"] + sorted(set(t["divisi_karyawan"] for t in tasks if t["divisi_karyawan"]))
                sel_div = st.selectbox("Divisi", divisi_opts, key="f_div_act")
                stage1  = [t for t in tasks if t["divisi_karyawan"] == sel_div] if sel_div != "Semua Divisi" else tasks
            with f2:
                posisi_opts = ["Semua Posisi"] + sorted(set(t["role_karyawan"] for t in stage1 if t["role_karyawan"]))
                sel_pos = st.selectbox("Posisi", posisi_opts, key="f_pos_act")
                stage2  = [t for t in stage1 if t["role_karyawan"] == sel_pos] if sel_pos != "Semua Posisi" else stage1
            with f3:
                nama_opts = ["Semua Karyawan"] + sorted(set(t["nama_karyawan"] for t in stage2 if t["nama_karyawan"]))
                sel_nama  = st.selectbox("Karyawan", nama_opts, key="f_nama_act")
                final     = [t for t in stage2 if t["nama_karyawan"] == sel_nama] if sel_nama != "Semua Karyawan" else stage2
        else:
            f1, f2, f3 = st.columns(3)
            with f1:
                divisi_opts = ["Semua Divisi"] + sorted(set(t["divisi_karyawan"] for t in tasks if t["divisi_karyawan"]))
                sel_div = st.selectbox("Divisi", divisi_opts, key="f_div_ap")
                stage1  = [t for t in tasks if t["divisi_karyawan"] == sel_div] if sel_div != "Semua Divisi" else tasks
            with f2:
                c_start, c_end = st.columns(2)
                with c_start:
                    sel_start = st.date_input("Dari Tanggal", value=date.today() - timedelta(days=30), key="f_start_ap")
                with c_end:
                    sel_end = st.date_input("Sampai Tanggal", value=date.today(), key="f_end_ap")
                stage2 = []
                for t in stage1:
                    try:
                        td = datetime.strptime(t["tanggal_assign"][:10], "%Y-%m-%d").date()
                        if sel_start <= td <= sel_end:
                            stage2.append(t)
                    except:
                        continue
            with f3:
                nama_opts = ["Semua Karyawan"] + sorted(set(t["nama_karyawan"] for t in stage2 if t["nama_karyawan"]))
                sel_nama  = st.selectbox("Karyawan", nama_opts, key="f_nama_ap")
                final     = [t for t in stage2 if t["nama_karyawan"] == sel_nama] if sel_nama != "Semua Karyawan" else stage2

    if not final:
        st.warning("Tidak ada tugas yang cocok dengan filter.")
        return

    st.markdown(f"<p style='font-size:13px;color:#64748B;margin:12px 0 8px 0'>{len(final)} tugas ditemukan</p>", unsafe_allow_html=True)

    badge_map = {
        "assigned":  "badge-assigned",
        "submitted": "badge-submitted",
        "revision":  "badge-revision",
        "approved":  "badge-approved",
    }

    for t in final:
        status    = t["status_task"].lower()
        badge_cls = badge_map.get(status, "badge-assigned")
        boleh     = can_modify_task(user, t)

        c1, c2, c3, c4 = st.columns([3, 2, 1.5, 2])
        with c1:
            st.markdown(f"**{t['judul']}**")
            st.caption(f"Deadline: {t['deadline']}")
        with c2:
            st.markdown(f"**{t['nama_karyawan']}**")
            st.caption(f"{t['divisi_karyawan']} · {t['role_karyawan']}")
        with c3:
            st.markdown(f'<span class="badge {badge_cls}">{status.upper()}</span>', unsafe_allow_html=True)
        with c4:
            if not only_approved:
                if boleh:
                    b1, b2 = st.columns(2)
                    if b1.button(":material/rate_review: Review", key=f"rev_{t['id']}",
                                 use_container_width=True, type="primary"):
                        st.session_state["selected_task_id"] = t["id"]
                        st.session_state["mon_view"] = "edit"
                        st.rerun()
                    if b2.button(":material/delete: Hapus", key=f"del_task_{t['id']}",
                                 use_container_width=True):
                        execute_query("DELETE FROM tasks WHERE id=?", (t["id"],))
                        st.toast(f"Tugas '{t['judul']}' dihapus.")
                        st.rerun()
                else:
                    # Read-only: hanya tombol detail
                    if st.button(":material/search: Detail", key=f"det_ro_{t['id']}",
                                 use_container_width=True):
                        st.session_state["selected_task_id"] = t["id"]
                        st.session_state["mon_view"] = "edit"
                        st.rerun()
            else:
                if st.button(":material/search: Detail", key=f"det_{t['id']}",
                             use_container_width=True, type="primary"):
                    st.session_state["selected_task_id"] = t["id"]
                    st.session_state["mon_view"] = "edit"
                    st.rerun()

        st.markdown("<hr style='border-color:#F1F5F9;margin:4px 0 8px 0'>", unsafe_allow_html=True)


# =========================================================================
# DETAIL / REVIEW
# =========================================================================
def render_edit_action(user):
    task_id = st.session_state["selected_task_id"]
    task = fetch_one("""
        SELECT t.*, u.nama as nama_karyawan, u.role as role_karyawan
        FROM tasks t JOIN users u ON t.assigned_to = u.id WHERE t.id=?
    """, (task_id,))
    sub = fetch_one("SELECT * FROM submissions WHERE task_id=? ORDER BY id DESC LIMIT 1", (task_id,))

    if st.button(":material/arrow_back: Kembali ke Daftar", key="btn_back_mon"):
        st.session_state["mon_view"] = "list"
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="header-card">
            <h2>Review: {task['judul']}</h2>
            <p>Karyawan: <strong style="color:#10B981">{task['nama_karyawan']}</strong>
               &nbsp;·&nbsp; Deadline: {task['deadline']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Cek apakah user boleh melakukan aksi di halaman detail ini
    boleh_aksi = can_modify_task(user, task)

    if is_sekretaris(user["role"]) and not boleh_aksi:
        st.markdown("""
            <div class="readonly-banner">
                👁️ Anda melihat tugas ini dalam mode <strong>read-only</strong>.
                Hanya pemberi tugas yang dapat memberikan review atau feedback.
            </div>
        """, unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])

    with col_a:
        with st.container(border=True):
            st.markdown("**Dokumen Terakhir**")
            if sub:
                st.caption(f"Dikirim: {sub['tanggal_submit']}")
                st.link_button(":material/open_in_new: Buka Dokumen", sub["link_drive"], use_container_width=True)
            else:
                st.warning("Belum ada dokumen yang dikirim.")

        with st.expander("Riwayat & Timeline Tugas", expanded=True):
            all_subs = fetch_all("""
                SELECT s.id as sub_id, s.tanggal_submit, s.link_drive, f.komentar, f.tanggal_ditulis
                FROM submissions s LEFT JOIN feedback f ON s.id=f.submission_id
                WHERE s.task_id=? ORDER BY s.tanggal_submit ASC
            """, (task_id,))
            all_dl = fetch_all("""
                SELECT dh.*, u.nama as nama_pengubah FROM deadline_history dh
                JOIN users u ON dh.changed_by=u.id WHERE dh.task_id=? ORDER BY dh.changed_at ASC
            """, (task_id,))

            events = []
            for s in all_subs:
                events.append({"ts": datetime.strptime(s["tanggal_submit"], "%Y-%m-%d %H:%M:%S"), "type": "sub", "data": s})
            for d in all_dl:
                events.append({"ts": datetime.strptime(d["changed_at"], "%Y-%m-%d %H:%M:%S"), "type": "dl", "data": d})
            events.sort(key=lambda x: x["ts"])

            if not events:
                st.caption("Belum ada riwayat aktivitas.")
            else:
                for i, ev in enumerate(events):
                    ts = ev["ts"].strftime("%d %b %Y %H:%M")
                    if ev["type"] == "sub":
                        s = ev["data"]
                        st.markdown(f"""
                            <div class="log-card">
                                <strong>Pengumpulan ke-{i+1}</strong><br>
                                <span style="font-size:12px;color:#64748B">{ts}</span><br>
                                <a href="{s['link_drive']}" target="_blank" style="font-size:12px;color:#10B981;">Lihat Dokumen</a>
                            </div>
                        """, unsafe_allow_html=True)
                        if s["komentar"]:
                            st.markdown(f"""
                                <div class="log-card-fb">
                                    <strong>Feedback Atasan:</strong> {s['komentar']}<br>
                                    <span style="font-size:11px;color:#94A3B8">{s['tanggal_ditulis']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        d = ev["data"]
                        st.markdown(f"""
                            <div class="log-card-dl">
                                <strong>Perpanjangan Deadline oleh {d['nama_pengubah']}</strong><br>
                                <span style="font-size:12px;color:#64748B">{ts}</span><br>
                                <span style="font-size:13px;color:#EA580C">{d['old_deadline']} &rarr; {d['new_deadline']}</span>
                            </div>
                        """, unsafe_allow_html=True)

    with col_b:
        if boleh_aksi:
            options = ["assigned", "submitted", "revision", "approved"]
            cur     = task["status_task"].lower()
            idx     = options.index(cur) if cur in options else 0

            with st.container(border=True):
                st.markdown("**Keputusan Atasan**")
                sel_status = st.selectbox("Ubah Status:", options, index=idx, key="status_sel")

                with st.form("form_review"):
                    feedback = st.text_area("Catatan Feedback / Revisi", placeholder="Tulis instruksi atau evaluasi...")
                    new_dl   = None
                    if sel_status == "revision":
                        st.markdown("<hr style='border-color:#E2E8F0'>", unsafe_allow_html=True)
                        st.caption("Atur deadline baru jika diperlukan")
                        cur_dl = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                        new_dl = st.date_input("Deadline Baru:", value=cur_dl)

                    if st.form_submit_button(":material/save: Simpan Keputusan", type="primary", use_container_width=True):
                        execute_query("UPDATE tasks SET status_task=? WHERE id=?", (sel_status, task_id))
                        if sel_status == "revision" and new_dl:
                            old_dl     = task["deadline"]
                            new_dl_str = new_dl.strftime("%Y-%m-%d")
                            if old_dl != new_dl_str:
                                execute_query("UPDATE tasks SET deadline=? WHERE id=?", (new_dl_str, task_id))
                                execute_query("""
                                    INSERT INTO deadline_history (task_id,old_deadline,new_deadline,changed_by,changed_at)
                                    VALUES (?,?,?,?,?)
                                """, (task_id, old_dl, new_dl_str, user["id"], datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")))
                        if sub and feedback:
                            execute_query("""
                                INSERT INTO feedback (submission_id,komentar,written_by,tanggal_ditulis)
                                VALUES (?,?,?,?)
                            """, (sub["id"], feedback, user["id"], datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")))
                        st.toast("Keputusan berhasil disimpan!")
                        st.session_state["mon_view"] = "list"
                        st.rerun()
        else:
            # Read-only: tampilkan info status saja tanpa form aksi
            with st.container(border=True):
                st.markdown("**Informasi Tugas**")
                status = task["status_task"].lower()
                badge_map = {
                    "assigned":  ("badge-assigned",  "Assigned"),
                    "submitted": ("badge-submitted", "Submitted"),
                    "revision":  ("badge-revision",  "Revision"),
                    "approved":  ("badge-approved",  "Approved"),
                }
                badge_cls, badge_txt = badge_map.get(status, ("badge-assigned", status.capitalize()))
                st.markdown(f"""
                    <p>Status saat ini:</p>
                    <span class="badge {badge_cls}" style="font-size:13px;padding:5px 14px;">{badge_txt}</span>
                    <p style="margin-top:12px;font-size:13px;color:#64748B;">
                        Deadline: <strong>{task['deadline']}</strong>
                    </p>
                """, unsafe_allow_html=True)


# =========================================================================
# LOGBOOK MONITORING (Direktur & Direktur Utama only)
# =========================================================================
def render_logbook_monitoring(user):
    st.markdown("""
        <div class="header-card">
            <h2>Pantau Logbook Rutinitas</h2>
            <p>Audit rekaman produktivitas aktivitas harian mandiri dari staf Anda.</p>
        </div>
    """, unsafe_allow_html=True)

    bawahan = fetch_all(
        "SELECT id,nama,role,divisi FROM users WHERE role NOT IN (?,?) ORDER BY nama",
        tuple(ROLE_DIREKSI)
    )

    if not bawahan:
        st.info("Tidak ada karyawan yang terdaftar.")
        return

    staff_opts = {f"{b['nama']}  ·  {b['role']} — {b['divisi']}": b["id"] for b in bawahan}
    sel       = st.selectbox("Pilih anggota tim yang ingin diaudit:", list(staff_opts.keys()), key="sb_logbook")
    target_id = staff_opts[sel]

    records = fetch_all("""
        SELECT rl.tanggal_logbook, rl.keterangan_progres, rl.tanggal_input, rl.link_file,
               jt.nama_tugas, jt.kategori_periodik
        FROM routine_logbooks rl JOIN jobdesc_templates jt ON rl.jobdesc_id=jt.id
        WHERE rl.user_id=? ORDER BY rl.tanggal_logbook DESC, rl.tanggal_input DESC
    """, (target_id,))

    st.markdown("<hr style='border-color:#E2E8F0;margin:12px 0'>", unsafe_allow_html=True)

    if not records:
        st.warning("Karyawan ini belum memiliki catatan logbook.")
        return

    total_hari = len(set(r["tanggal_logbook"] for r in records))
    m1, m2 = st.columns(2)
    m1.metric("Total Entri Logbook", len(records))
    m2.metric("Hari Kerja Aktif", f"{total_hari} hari")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for r in records:
        st.markdown(f"""
            <div class="logbook-row">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-size:13px;font-weight:600;color:#1E293B;">{r['tanggal_logbook']}</span>
                    <span style="font-size:11px;color:#94A3B8;">{r['tanggal_input']}</span>
                </div>
                <span style="background:#D1FAE5;color:#065F46;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;">{r['nama_tugas']}</span>
                <span style="background:#F1F5F9;color:#475569;padding:2px 8px;border-radius:20px;font-size:11px;margin-left:4px;">{r['kategori_periodik']}</span>
                <p style="margin:8px 0 0 0;font-size:13px;color:#475569;line-height:1.5;">{r['keterangan_progres']}</p>
                {'<a href="' + r["link_file"] + '" target="_blank" style="font-size:12px;color:#10B981;">Lihat Lampiran</a>' if r.get("link_file") else ""}
            </div>
        """, unsafe_allow_html=True)
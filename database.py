import libsql
import streamlit as st

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_NAME = os.path.join(BASE_DIR, "tracking.db")

def get_connection():
    return libsql.connect(
        database=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"]
    )

def fetch_all(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query, params)

    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    result = [
        dict(zip(columns, row))
        for row in rows
    ]

    conn.close()
    return result

def fetch_one(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query, params)

    row = cursor.fetchone()

    if row:
        columns = [desc[0] for desc in cursor.description]
        row = dict(zip(columns, row))

    conn.close()
    return row

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. TABEL USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        divisi TEXT NOT NULL,
        role TEXT NOT NULL,
        atasan_id INTEGER,
        FOREIGN KEY (atasan_id) REFERENCES users(id)
    )
    """)

    # 2. TABEL TASKS (TUGAS NON-RUTIN / PROYEK KHUSUS)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judul TEXT NOT NULL,
        deskripsi TEXT NOT NULL,
        assigned_to INTEGER NOT NULL,
        assigned_by INTEGER NOT NULL,
        deadline TEXT NOT NULL,
        status_task TEXT DEFAULT 'assigned',
        tanggal_assign TEXT NOT NULL,
        FOREIGN KEY (assigned_to) REFERENCES users(id),
        FOREIGN KEY (assigned_by) REFERENCES users(id)
    )
    """)

    # 3. TABEL SUBMISSIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        link_drive TEXT NOT NULL,
        keterangan TEXT,
        tanggal_submit TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """)

    # 4. TABEL FEEDBACK
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        komentar TEXT NOT NULL,
        tanggal_ditulis TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    )
    """)

    # 5. TABEL JOBDESC / MASTER TUGAS RUTIN
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobdesc_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_tugas TEXT NOT NULL,
        divisi TEXT NOT NULL,
        role TEXT NOT NULL,
        kategori_periodik TEXT NOT NULL,
        assigned_by_id INTEGER,
        created_by_staff_id INTEGER,
        FOREIGN KEY (assigned_by_id) REFERENCES users(id),
        FOREIGN KEY (created_by_staff_id) REFERENCES users(id)
    )
    """)

    # 6. TABEL LOGBOOK RUTIN (Sudah ditambahkan tanggal_logbook)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routine_logbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        jobdesc_id INTEGER NOT NULL,
        keterangan_progres TEXT NOT NULL,
        link_file TEXT,
        tanggal_logbook TEXT,
        tanggal_input TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (jobdesc_id) REFERENCES jobdesc_templates(id)
    )
    """)

    # 7. TABEL DEADLINE HISTORY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadline_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        old_deadline TEXT NOT NULL,
        new_deadline TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        changed_at TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (changed_by) REFERENCES users(id)
    )
    """)
    
    # ========================================================
    # SINKRONISASI ALTER TABEL AMAN
    # ========================================================
    
    # Cek & Sinkronisasi tabel jobdesc_templates
    cursor.execute("PRAGMA table_info(jobdesc_templates)")
    template_columns = [col[1] for col in cursor.fetchall()]

    if "role" not in template_columns:
        cursor.execute("ALTER TABLE jobdesc_templates ADD COLUMN role TEXT")

    # Cek & Sinkronisasi tabel routine_logbooks 
    cursor.execute("PRAGMA table_info(routine_logbooks)")
    logbook_columns = [col[1] for col in cursor.fetchall()]

    if "tanggal_logbook" not in logbook_columns:
        cursor.execute("ALTER TABLE routine_logbooks ADD COLUMN tanggal_logbook TEXT")
        
    # Cek & Sinkronisasi tabel submissions
    cursor.execute("PRAGMA table_info(submissions)")
    submission_columns = [col[1] for col in cursor.fetchall()]
    if "keterangan" not in submission_columns:
        cursor.execute("ALTER TABLE submissions ADD COLUMN keterangan TEXT")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
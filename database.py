import libsql
import streamlit as st
import os

# =========================================================================
# HELPER SECRET — BISA JALAN DI STREAMLIT CLOUD & RAILWAY
# =========================================================================
def get_secret(key, subkey=None):
    try:
        if subkey:
            return st.secrets[key][subkey]
        return st.secrets[key]
    except:
        if subkey:
            return os.environ[f"{key}__{subkey}"]
        return os.environ[key]


# =========================================================================
# KONEKSI — TTL 10 MENIT SUPAYA STREAM TURSO TIDAK EXPIRED
# =========================================================================
@st.cache_resource(ttl=600)
def get_connection():
    return libsql.connect(
        database=get_secret("TURSO_DATABASE_URL"),
        auth_token=get_secret("TURSO_AUTH_TOKEN")
    )


def _get_cursor():
    try:
        conn = get_connection()
        return conn, conn.cursor()
    except Exception:
        st.cache_resource.clear()
        conn = get_connection()
        return conn, conn.cursor()


def fetch_all(query, params=()):
    conn, cursor = _get_cursor()
    cursor.execute(query, list(params) if params else [])
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def fetch_one(query, params=()):
    conn, cursor = _get_cursor()
    cursor.execute(query, list(params) if params else [])
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        row = dict(zip(columns, row))
    return row


def execute_query(query, params=()):
    conn, cursor = _get_cursor()
    cursor.execute(query, list(params) if params else [])
    conn.commit()


# =========================================================================
# INIT DB
# =========================================================================
def init_db():
    conn, cursor = _get_cursor()

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        komentar TEXT NOT NULL,
        tanggal_ditulis TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    )
    """)

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

    conn.commit()


if __name__ == "__main__":
    init_db()
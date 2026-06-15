import libsql

url = "libsql://jobdesc-tracking-jktdesigncenter.aws-ap-northeast-1.turso.io"
auth_token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODA1ODM0NDksImlkIjoiMDE5ZTkyZTUtYWEwMS03ZGE0LWI2M2YtZGUzNGExMDNiM2EzIiwicmlkIjoiM2JmNTc0ODMtN2JiOS00OTRlLTllODMtNTIxMmJjNmRhZjY2In0.h8n80wJfADb2d8v9O1xpohH0idZloViaC3JpIRnO3spEWRNHsWvORoz0aG16OcO3k437jMclLasziUFufu4nDw"

conn = libsql.connect(
    database=url,
    auth_token=auth_token
)

cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nama TEXT NOT NULL,
    divisi TEXT NOT NULL,
    role TEXT NOT NULL,
    atasan_id INTEGER,
    FOREIGN KEY (atasan_id) REFERENCES users(id)
);

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
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    link_drive TEXT NOT NULL,
    keterangan TEXT,
    tanggal_submit TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    komentar TEXT NOT NULL,
    tanggal_ditulis TEXT NOT NULL,
    FOREIGN KEY (submission_id) REFERENCES submissions(id)
);

CREATE TABLE IF NOT EXISTS jobdesc_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_tugas TEXT NOT NULL,
    divisi TEXT NOT NULL,
    role TEXT NOT NULL,
    kategori_periodik TEXT NOT NULL,
    assigned_by_id INTEGER,
    created_by_staff_id INTEGER
);

CREATE TABLE IF NOT EXISTS routine_logbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    jobdesc_id INTEGER NOT NULL,
    keterangan_progres TEXT NOT NULL,
    link_file TEXT,
    tanggal_logbook TEXT,
    tanggal_input TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deadline_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    old_deadline TEXT NOT NULL,
    new_deadline TEXT NOT NULL,
    changed_by INTEGER NOT NULL,
    changed_at TEXT NOT NULL
);
""")

conn.commit()
print("Schema berhasil dibuat!")
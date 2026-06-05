CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        divisi TEXT NOT NULL,
        role TEXT NOT NULL,
        atasan_id INTEGER,
        FOREIGN KEY (atasan_id) REFERENCES users(id)
    );

CREATE TABLE tasks (
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

CREATE TABLE submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        link_drive TEXT NOT NULL,
        tanggal_submit TEXT NOT NULL, keterangan TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    );

CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        komentar TEXT NOT NULL,
        tanggal_ditulis TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    );

CREATE TABLE jobdesc_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_tugas TEXT NOT NULL,
        divisi TEXT NOT NULL,
        kategori_periodik TEXT NOT NULL,
        assigned_by_id INTEGER,
        created_by_staff_id INTEGER, role TEXT,
        FOREIGN KEY (assigned_by_id) REFERENCES users(id),
        FOREIGN KEY (created_by_staff_id) REFERENCES users(id)
    );

CREATE TABLE routine_logbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        jobdesc_id INTEGER NOT NULL,
        keterangan_progres TEXT NOT NULL,
        link_file TEXT,
        tanggal_input TEXT NOT NULL, tanggal_logbook TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (jobdesc_id) REFERENCES jobdesc_templates(id)
    );

CREATE TABLE deadline_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        old_deadline TEXT NOT NULL,
        new_deadline TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        changed_at TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (changed_by) REFERENCES users(id)
    );


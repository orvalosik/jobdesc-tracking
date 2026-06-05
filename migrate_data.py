import sqlite3
import libsql

# SQLite lama
sqlite_conn = sqlite3.connect("tracking.db")
sqlite_cur = sqlite_conn.cursor()

# Turso
turso_conn = libsql.connect(
    database="libsql://jobdesc-tracking-jktdesigncenter.aws-ap-northeast-1.turso.io",
    auth_token="eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODA1ODM0NDksImlkIjoiMDE5ZTkyZTUtYWEwMS03ZGE0LWI2M2YtZGUzNGExMDNiM2EzIiwicmlkIjoiM2JmNTc0ODMtN2JiOS00OTRlLTllODMtNTIxMmJjNmRhZjY2In0.h8n80wJfADb2d8v9O1xpohH0idZloViaC3JpIRnO3spEWRNHsWvORoz0aG16OcO3k437jMclLasziUFufu4nDw"
)
turso_cur = turso_conn.cursor()

# =====================
# USERS
# =====================

sqlite_cur.execute("SELECT * FROM users")
users = sqlite_cur.fetchall()

for row in users:
    turso_cur.execute("""
        INSERT INTO users
        (id, username, password, nama, divisi, role, atasan_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

print(f"{len(users)} users berhasil dipindahkan")

# =====================
# ROUTINE LOGBOOKS
# =====================

sqlite_cur.execute("SELECT * FROM routine_logbooks")
logbooks = sqlite_cur.fetchall()

for row in logbooks:
    turso_cur.execute("""
        INSERT INTO routine_logbooks
        (id, user_id, jobdesc_id, keterangan_progres,
         link_file, tanggal_input, tanggal_logbook)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

print(f"{len(logbooks)} logbook berhasil dipindahkan")

turso_conn.commit()

sqlite_conn.close()
turso_conn.close()

print("Migrasi selesai!")
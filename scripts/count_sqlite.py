import sqlite3

conn = sqlite3.connect("tracking.db")
cur = conn.cursor()

tables = [
    "users",
    "tasks",
    "submissions",
    "feedback",
    "jobdesc_templates",
    "routine_logbooks",
    "deadline_history"
]

for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(table, cur.fetchone()[0])

conn.close()
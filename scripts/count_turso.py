import libsql

conn = libsql.connect(
    database="libsql://jobdesc-tracking-jktdesigncenter.aws-ap-northeast-1.turso.io",
    auth_token="eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODA1ODM0NDksImlkIjoiMDE5ZTkyZTUtYWEwMS03ZGE0LWI2M2YtZGUzNGExMDNiM2EzIiwicmlkIjoiM2JmNTc0ODMtN2JiOS00OTRlLTllODMtNTIxMmJjNmRhZjY2In0.h8n80wJfADb2d8v9O1xpohH0idZloViaC3JpIRnO3spEWRNHsWvORoz0aG16OcO3k437jMclLasziUFufu4nDw"
)

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
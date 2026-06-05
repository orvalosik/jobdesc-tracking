import libsql

conn = libsql.connect(
    database="libsql://jobdesc-tracking-jktdesigncenter.aws-ap-northeast-1.turso.io",
    auth_token="eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODA1ODM0NDksImlkIjoiMDE5ZTkyZTUtYWEwMS03ZGE0LWI2M2YtZGUzNGExMDNiM2EzIiwicmlkIjoiM2JmNTc0ODMtN2JiOS00OTRlLTllODMtNTIxMmJjNmRhZjY2In0.h8n80wJfADb2d8v9O1xpohH0idZloViaC3JpIRnO3spEWRNHsWvORoz0aG16OcO3k437jMclLasziUFufu4nDw"
)

cur = conn.cursor()

with open("schema.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

# pisahkan per statement
for stmt in sql_script.split(";"):
    stmt = stmt.strip()
    if stmt:
        cur.execute(stmt)

conn.commit()

print("Schema berhasil dibuat di Turso!")
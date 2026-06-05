import sqlite3

conn = sqlite3.connect("tracking.db")

cursor = conn.cursor()

cursor.execute("""
SELECT sql
FROM sqlite_master
WHERE type='table'
AND name NOT LIKE 'sqlite_%'
""")

schema = ""

for row in cursor.fetchall():
    if row[0]:
        schema += row[0] + ";\n\n"

with open("schema.sql", "w", encoding="utf-8") as f:
    f.write(schema)

print("Schema berhasil diexport ke schema.sql")

conn.close()
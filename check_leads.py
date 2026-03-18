import psycopg2

conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="test",
    password="Pervin21@"
)

cur = conn.cursor()
cur.execute("SELECT * FROM chapter_leads")
leads = cur.fetchall()
print(f"Chapter leads in database: {len(leads)}")
for lead in leads:
    print(f"  - {lead}")

conn.close()

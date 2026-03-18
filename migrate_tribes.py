import psycopg2

conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="test",
    password="Pervin21@"
)
conn.autocommit = True
cur = conn.cursor()

# Update tribe priorities
print("Updating tribe priorities...")
cur.execute("UPDATE tribes SET priority = 'BUSINESS_CRITICAL' WHERE priority IN ('CRITICAL', 'HIGH')")
print(f"  Updated {cur.rowcount} tribes to BUSINESS_CRITICAL")

cur.execute("UPDATE tribes SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'")
print(f"  Updated {cur.rowcount} tribes to MISSION_CRITICAL")

cur.execute("UPDATE tribes SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'")
print(f"  Updated {cur.rowcount} tribes to BUSINESS_OPERATION")

# Check results
cur.execute("SELECT priority, COUNT(*) FROM tribes GROUP BY priority")
print("\nTribe priorities after migration:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} tribes")

conn.close()

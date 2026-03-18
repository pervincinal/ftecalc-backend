import psycopg2

conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="postgres",
    password="Pervin21@"
)

cur = conn.cursor()

# Check the actual enum values in the database
cur.execute("""
    SELECT enumlabel 
    FROM pg_enum 
    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'priorityenum')
""")

print("Current enum values in database:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

# Check current priority values in tables
cur.execute("SELECT DISTINCT priority FROM squads")
print("\nCurrent squad priorities:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.execute("SELECT DISTINCT priority FROM tribes")
print("\nCurrent tribe priorities:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()

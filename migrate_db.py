import psycopg2

# Use the credentials that were working
conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="postgres",
    password="Pervin21@"
)

cur = conn.cursor()

print("Starting migration...")

try:
    # Update squads
    cur.execute("UPDATE squads SET priority = 'BUSINESS_CRITICAL' WHERE priority = 'CRITICAL'")
    print(f"Updated {cur.rowcount} CRITICAL squads")
    
    cur.execute("UPDATE squads SET priority = 'BUSINESS_CRITICAL' WHERE priority = 'HIGH'")
    print(f"Updated {cur.rowcount} HIGH squads")
    
    cur.execute("UPDATE squads SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'")
    print(f"Updated {cur.rowcount} MEDIUM squads")
    
    cur.execute("UPDATE squads SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'")
    print(f"Updated {cur.rowcount} LOW squads")
    
    # Update tribes
    cur.execute("UPDATE tribes SET priority = 'BUSINESS_CRITICAL' WHERE priority = 'CRITICAL'")
    print(f"Updated {cur.rowcount} CRITICAL tribes")
    
    cur.execute("UPDATE tribes SET priority = 'BUSINESS_CRITICAL' WHERE priority = 'HIGH'")
    print(f"Updated {cur.rowcount} HIGH tribes")
    
    cur.execute("UPDATE tribes SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'")
    print(f"Updated {cur.rowcount} MEDIUM tribes")
    
    cur.execute("UPDATE tribes SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'")
    print(f"Updated {cur.rowcount} LOW tribes")
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT priority, COUNT(*) FROM squads GROUP BY priority")
    print("\nSquads after migration:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
        
    cur.execute("SELECT priority, COUNT(*) FROM tribes GROUP BY priority")
    print("\nTribes after migration:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    print("\n✅ Migration successful!")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

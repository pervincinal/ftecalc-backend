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

try:
    # Add new enum values if they don't exist
    print("Adding new enum values...")
    
    # PostgreSQL requires special handling for enum types
    cur.execute("ALTER TYPE priorityenum ADD VALUE IF NOT EXISTS 'BUSINESS_CRITICAL'")
    cur.execute("ALTER TYPE priorityenum ADD VALUE IF NOT EXISTS 'MISSION_CRITICAL'")
    cur.execute("ALTER TYPE priorityenum ADD VALUE IF NOT EXISTS 'BUSINESS_OPERATION'")
    
    print("✓ New enum values added")
    
    # Now migrate the data
    print("\nMigrating data...")
    
    cur.execute("UPDATE squads SET priority = 'BUSINESS_CRITICAL' WHERE priority IN ('CRITICAL', 'HIGH')")
    print(f"  Updated {cur.rowcount} squads to BUSINESS_CRITICAL")
    
    cur.execute("UPDATE squads SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'")
    print(f"  Updated {cur.rowcount} squads to MISSION_CRITICAL")
    
    cur.execute("UPDATE squads SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'")
    print(f"  Updated {cur.rowcount} squads to BUSINESS_OPERATION")
    
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()

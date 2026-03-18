import os
from sqlalchemy import create_engine, text

# Try different password formats
passwords = [
    'R&"Z<L2|0F|HHitl',
    r'R&"Z<L2|0F|HHitl',
    'Pervin21@'
]

conn = None
for pwd in passwords:
    try:
        url = f'postgresql://qacalculator:{pwd}@34.147.188.76:5432/ftecalc'
        engine = create_engine(url)
        conn = engine.connect()
        print(f"✓ Connected with password option")
        break
    except:
        continue

if not conn:
    try:
        # Try with test user
        url = 'postgresql://test:Pervin21@@34.147.188.76:5432/ftecalc'
        engine = create_engine(url)
        conn = engine.connect()
        print("✓ Connected with test user")
    except Exception as e:
        print(f"Failed to connect: {e}")
        exit(1)

print("Starting priority migration...")

# Update squads
updates = [
    ("UPDATE squads SET priority = 'BUSINESS_CRITICAL' WHERE priority IN ('CRITICAL', 'HIGH')", "BUSINESS_CRITICAL"),
    ("UPDATE squads SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'", "MISSION_CRITICAL"),
    ("UPDATE squads SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'", "BUSINESS_OPERATION")
]

for query, prio in updates:
    result = conn.execute(text(query))
    conn.commit()
    print(f"Updated {result.rowcount} squads to {prio}")

# Update tribes
updates = [
    ("UPDATE tribes SET priority = 'BUSINESS_CRITICAL' WHERE priority IN ('CRITICAL', 'HIGH')", "BUSINESS_CRITICAL"),
    ("UPDATE tribes SET priority = 'MISSION_CRITICAL' WHERE priority = 'MEDIUM'", "MISSION_CRITICAL"),
    ("UPDATE tribes SET priority = 'BUSINESS_OPERATION' WHERE priority = 'LOW'", "BUSINESS_OPERATION")
]

for query, prio in updates:
    result = conn.execute(text(query))
    conn.commit()
    print(f"Updated {result.rowcount} tribes to {prio}")

# Verify
result = conn.execute(text("SELECT priority, COUNT(*) FROM squads GROUP BY priority"))
print("\nSquad priorities after migration:")
for row in result:
    print(f"  - {row[0]}: {row[1]} squads")

result = conn.execute(text("SELECT priority, COUNT(*) FROM tribes GROUP BY priority"))
print("\nTribe priorities after migration:")
for row in result:
    print(f"  - {row[0]}: {row[1]} tribes")

conn.close()
print("\n✅ Migration complete!")

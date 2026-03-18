import psycopg2
from psycopg2.extras import RealDictCursor
import json

conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="test",
    password="Pervin21@"
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# Check calculations with duplicate platforms
cur.execute("""
    SELECT id, squad_id, inputs
    FROM calculations
    WHERE inputs::text LIKE '%PLATFORMS_TESTED%'
    ORDER BY id DESC
    LIMIT 10
""")

for calc in cur.fetchall():
    inputs = json.loads(calc['inputs']) if isinstance(calc['inputs'], str) else calc['inputs']
    platforms = inputs.get('PLATFORMS_TESTED', [])
    if len(platforms) > 0:
        print(f"Calc ID: {calc['id']}, Squad: {calc['squad_id']}, Platforms: {platforms}")

conn.close()

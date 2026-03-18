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

# Check last 5 calculations for squad 14
cur.execute("""
    SELECT id, created_at, needed_fte, inputs
    FROM calculations 
    WHERE squad_id = 14 
    ORDER BY created_at DESC NULLS LAST, id DESC
    LIMIT 5
""")

print("Last 5 calculations for squad 14:")
for calc in cur.fetchall():
    inputs = json.loads(calc['inputs']) if isinstance(calc['inputs'], str) else calc['inputs']
    dev = inputs.get('DEV_COUNT', 0)
    cr = inputs.get('CR_PER_MONTH', inputs.get('STORIES_PER_SPRINT', 0))
    print(f"  ID: {calc['id']}, Created: {calc['created_at']}, DEV: {dev}, CR: {cr}")

conn.close()

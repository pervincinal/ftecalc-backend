import psycopg2
from sqlalchemy import create_engine, text
import urllib.parse

# Method 1: Direct psycopg2 connection
try:
    conn = psycopg2.connect(
        host="34.147.188.76",
        port=5432,
        database="postgres",
        user="test",
        password="Pervin21@"
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM squads")
    count = cur.fetchone()[0]
    print(f"✓ psycopg2 connected! Found {count} squads")
    conn.close()
except Exception as e:
    print(f"psycopg2 failed: {e}")

# Method 2: SQLAlchemy with URL encoding
try:
    password = urllib.parse.quote_plus("Pervin21@")
    db_url = f"postgresql://test:{password}@34.147.188.76:5432/postgres"
    print(f"Using encoded URL: {db_url}")
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM squads"))
        count = result.fetchone()[0]
        print(f"✓ SQLAlchemy connected! Found {count} squads")
        
        result = conn.execute(text("SELECT id, name, priority FROM squads LIMIT 3"))
        print("\nSample squads:")
        for row in result:
            print(f"  - {row}")
except Exception as e:
    print(f"SQLAlchemy failed: {e}")

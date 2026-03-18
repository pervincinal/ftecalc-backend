import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time

# Configuration
DB_CONFIG = {
    "host": "34.147.188.76",
    "port": 5432,
    "database": "postgres",
    "user": "test",
    "password": "Pervin21@"
}
API_URL = "http://localhost:8000"

def recalculate_all():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("="*60)
    print("Starting recalculation of all squads")
    print("="*60)
    
    # Get all active squads with their last calculation
    cur.execute("""
        SELECT 
            s.id,
            s.name,
            t.name as tribe_name,
            c.inputs
        FROM squads s
        LEFT JOIN tribes t ON s.tribe_id = t.id
        LEFT JOIN LATERAL (
            SELECT inputs 
            FROM calculations 
            WHERE squad_id = s.id 
            ORDER BY created_at DESC NULLS LAST, id DESC 
            LIMIT 1
        ) c ON true
        WHERE s.status = 'ACTIVE'
        ORDER BY t.name, s.name
    """)
    
    squads = cur.fetchall()
    print(f"Found {len(squads)} active squads\n")
    
    success_count = 0
    skipped_count = 0
    error_count = 0
    current_tribe = None
    
    for squad in squads:
        # Print tribe header when it changes
        if squad['tribe_name'] != current_tribe:
            current_tribe = squad['tribe_name']
            print(f"\n{'-'*40}")
            print(f"Tribe: {current_tribe or 'Unassigned'}")
            print(f"{'-'*40}")
        
        if not squad['inputs']:
            print(f"  ⚠ {squad['name']}: No previous calculation")
            skipped_count += 1
            continue
        
        try:
            # Parse inputs
            inputs = json.loads(squad['inputs']) if isinstance(squad['inputs'], str) else squad['inputs']
            
            # Make API call to recalculate
            response = requests.post(
                f"{API_URL}/api/v1/calculate",
                json={
                    "squad_id": squad['id'],
                    "inputs": inputs
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ {squad['name']}: Gap={result['fte_gap']:.2f}, Risk={result['gap_risk_level']}")
                success_count += 1
            else:
                print(f"  ✗ {squad['name']}: HTTP {response.status_code}")
                error_count += 1
                
        except Exception as e:
            print(f"  ✗ {squad['name']}: Error - {str(e)}")
            error_count += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.05)
    
    print("\n" + "="*60)
    print("RECALCULATION COMPLETE")
    print("="*60)
    print(f"✓ Success: {success_count} squads")
    print(f"⚠ Skipped: {skipped_count} squads (no previous calculation)")
    print(f"✗ Errors:  {error_count} squads")
    print(f"─ Total:   {len(squads)} squads")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    recalculate_all()

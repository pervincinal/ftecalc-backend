import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time

# Database connection
conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="test",
    password="Pervin21@"
)

# API URL
API_URL = "http://localhost:8000"

def recalculate_squad(squad_id, last_calc_inputs):
    """Recalculate a single squad using its last calculation inputs"""
    
    if not last_calc_inputs:
        print(f"  Squad {squad_id}: No previous calculation found, skipping")
        return None
    
    try:
        # Call the calculate API with the existing inputs
        response = requests.post(
            f"{API_URL}/api/v1/calculate",
            json={
                "squad_id": squad_id,
                "inputs": last_calc_inputs
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Squad {squad_id}: Success - Gap: {result['fte_gap']}, Risk: {result['gap_risk_level']}")
            return result
        else:
            print(f"  Squad {squad_id}: API Error - {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Squad {squad_id}: Error - {e}")
        return None

def main():
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all squads with their last calculations
    print("Fetching all squads...")
    cur.execute("""
        SELECT s.id, s.name, t.name as tribe_name,
               (SELECT inputs FROM calculations 
                WHERE squad_id = s.id 
                ORDER BY created_at DESC NULLS LAST, id DESC 
                LIMIT 1) as last_inputs
        FROM squads s
        LEFT JOIN tribes t ON s.tribe_id = t.id
        WHERE s.status = 'ACTIVE'
        ORDER BY t.name, s.name
    """)
    
    squads = cur.fetchall()
    print(f"Found {len(squads)} active squads\n")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    current_tribe = None
    
    for squad in squads:
        # Print tribe header if changed
        if squad['tribe_name'] != current_tribe:
            current_tribe = squad['tribe_name']
            print(f"\n{current_tribe or 'No Tribe'}:")
            print("-" * 40)
        
        print(f"\n{squad['name']}:")
        
        if squad['last_inputs']:
            # Parse the inputs
            inputs = json.loads(squad['last_inputs']) if isinstance(squad['last_inputs'], str) else squad['last_inputs']
            
            # Recalculate
            result = recalculate_squad(squad['id'], inputs)
            
            if result:
                success_count += 1
                time.sleep(0.1)  # Small delay to not overload the API
            else:
                error_count += 1
        else:
            print(f"  No previous calculation to recalculate")
            skip_count += 1
    
    print("\n" + "=" * 50)
    print(f"Recalculation Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Skipped (no data): {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(squads)}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

import psycopg2
import json

conn = psycopg2.connect(
    host="34.147.188.76",
    port=5432,
    database="postgres",
    user="test",
    password="Pervin21@"
)

cur = conn.cursor()

# Get all calculations
cur.execute("SELECT id, inputs FROM calculations")
calculations = cur.fetchall()

for calc_id, inputs in calculations:
    if inputs:
        data = json.loads(inputs) if isinstance(inputs, str) else inputs
        
        if 'PLATFORMS_TESTED' in data:
            # Remove duplicates and normalize
            platforms = data['PLATFORMS_TESTED']
            
            # Create a set to track unique platforms (case-insensitive)
            seen = set()
            clean_platforms = []
            
            # Define the standard names
            standard_names = {
                'IOS': 'IOS',
                'ANDROID': 'ANDROID',
                'WEB': 'WEB',
                'API': 'API',
                'PL/SQL': 'PL/SQL',
                'KAFKA': 'KAFKA',
                'REDIS': 'REDIS',
                'DATABASE': 'DATABASE'
            }
            
            for platform in platforms:
                upper = platform.upper()
                if upper not in seen:
                    seen.add(upper)
                    # Use standard name if available
                    clean_platforms.append(standard_names.get(upper, platform))
            
            # Update if changed
            if clean_platforms != platforms:
                data['PLATFORMS_TESTED'] = clean_platforms
                cur.execute(
                    "UPDATE calculations SET inputs = %s WHERE id = %s",
                    (json.dumps(data), calc_id)
                )
                print(f"Updated calculation {calc_id}: {platforms} -> {clean_platforms}")

conn.commit()
print("Cleanup complete!")
conn.close()

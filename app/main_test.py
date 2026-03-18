from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        host="34.147.188.76",
        port=5432,
        database="postgres",
        user="test",
        password="Pervin21@"
    )

@app.post("/api/v1/calculate")
def calculate_fte(data: dict):
    inputs = data.get("inputs", {})
    squad_id = data.get("squad_id")
    
    # Get CR count (ONLY CR_PER_MONTH now)
    cr_count = inputs.get("CR_PER_MONTH", 0)
    
    # Calculate FTE
    dev_count = inputs.get("DEV_COUNT", 0)
    platforms_tested = len(inputs.get("PLATFORMS_TESTED", []))
    
    # Base calculation
    needed_fte = dev_count * 0.3
    
    # Add FTE based on CRs (1 FTE per 50 CRs per month)
    needed_fte += cr_count / 50
    
    # Platform adjustment
    needed_fte += platforms_tested * 0.2
    
    needed_fte = round(needed_fte, 2)
    current_fte = sum([inputs.get(f"CURR_L{i}", 0) for i in range(1, 6)])
    fte_gap = round(needed_fte - current_fte, 2)
    
    return {
        "squad_id": squad_id,
        "needed_fte": needed_fte,
        "current_fte": current_fte,
        "fte_gap": fte_gap,
        "gap_risk_level": "HIGH" if fte_gap > 2 else "MEDIUM" if fte_gap > 1 else "LOW"
    }

@app.post("/api/v1/calculate/save")
def save_calculation(data: dict):
    return calculate_fte(data)

@app.get("/api/v1/squads/{squad_id}/last-calculation")
def get_last_calculation(squad_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT * FROM calculations 
        WHERE squad_id = %s 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (squad_id,))
    
    calculation = cur.fetchone()
    cur.close()
    conn.close()
    
    if calculation:
        if isinstance(calculation.get('inputs'), str):
            inputs = json.loads(calculation['inputs'])
            # Convert old field to new field if exists
            if 'STORIES_PER_SPRINT' in inputs:
                inputs['CR_PER_MONTH'] = inputs.pop('STORIES_PER_SPRINT')
            calculation['inputs'] = inputs
    
    return calculation if calculation else {}

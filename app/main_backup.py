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

@app.get("/")
def root():
    return {"message": "QA FTE Calculator API", "status": "running"}

# SQUADS ENDPOINTS
@app.get("/api/v1/squads")
def get_squads(limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"""
        SELECT s.*, 
               t.name as tribe_name,
               s.last_calculation::json as last_calculation_data
        FROM squads s
        LEFT JOIN tribes t ON s.tribe_id = t.id
        LIMIT {limit}
    """)
    squads = cur.fetchall()
    
    for squad in squads:
        if isinstance(squad.get('platforms'), str):
            squad['platforms'] = json.loads(squad['platforms'])
        # Parse last_calculation if it exists
        if squad.get('last_calculation_data'):
            squad['fte_gap'] = squad['last_calculation_data'].get('fte_gap', 0)
            squad['gap_risk_level'] = squad['last_calculation_data'].get('gap_risk_level', 'N/A')
    
    cur.close()
    conn.close()
    return {"items": squads, "total": len(squads)}

@app.get("/api/v1/squads/{squad_id}")
def get_squad(squad_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT s.*, t.name as tribe_name 
        FROM squads s
        LEFT JOIN tribes t ON s.tribe_id = t.id
        WHERE s.id = %s
    """, (squad_id,))
    squad = cur.fetchone()
    cur.close()
    conn.close()
    
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    
    if isinstance(squad.get('platforms'), str):
        squad['platforms'] = json.loads(squad['platforms'])
    return squad

@app.post("/api/v1/squads")
def create_squad(squad: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO squads (name, priority, tribe_id, platforms, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """, (
        squad["name"],
        squad["priority"],
        squad["tribe_id"],
        json.dumps(squad.get("platforms", [])),
        squad.get("status", "ACTIVE")
    ))
    new_squad = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_squad

@app.put("/api/v1/squads/{squad_id}")
def update_squad(squad_id: int, squad: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        UPDATE squads 
        SET name = %s, priority = %s, tribe_id = %s, platforms = %s, status = %s
        WHERE id = %s
        RETURNING *
    """, (
        squad["name"],
        squad["priority"],
        squad["tribe_id"],
        json.dumps(squad.get("platforms", [])),
        squad.get("status", "ACTIVE"),
        squad_id
    ))
    updated_squad = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated_squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    return updated_squad

@app.delete("/api/v1/squads/{squad_id}")
def delete_squad(squad_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM squads WHERE id = %s RETURNING id", (squad_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Squad not found")
    return {"message": "Deleted"}

# TRIBES ENDPOINTS
@app.get("/api/v1/tribes")
def get_tribes(limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"""
        SELECT t.*, 
               COUNT(s.id) as squads,
               COALESCE(SUM(CASE 
                   WHEN s.last_calculation IS NOT NULL 
                   THEN (s.last_calculation->>'fte_gap')::float 
                   ELSE 0 
               END), 0) as total_fte_gap,
               MAX(s.last_calculation->>'gap_risk_level') as highest_risk_level
        FROM tribes t
        LEFT JOIN squads s ON t.id = s.tribe_id
        GROUP BY t.id
        LIMIT {limit}
    """)
    tribes = cur.fetchall()
    cur.close()
    conn.close()
    return {"items": tribes, "total": len(tribes)}

@app.get("/api/v1/tribes/{tribe_id}")
def get_tribe(tribe_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT t.*,
               COUNT(s.id) as squads,
               COALESCE(SUM((s.last_calculation->>'fte_gap')::float), 0) as total_fte_gap
        FROM tribes t
        LEFT JOIN squads s ON t.id = s.tribe_id
        WHERE t.id = %s
        GROUP BY t.id
    """, (tribe_id,))
    tribe = cur.fetchone()
    cur.close()
    conn.close()
    
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")
    return tribe

@app.post("/api/v1/tribes")
def create_tribe(tribe: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO tribes (name, priority, chapter_lead_id)
        VALUES (%s, %s, %s)
        RETURNING *
    """, (
        tribe["name"],
        tribe["priority"],
        tribe.get("chapter_lead_id")
    ))
    new_tribe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_tribe

@app.put("/api/v1/tribes/{tribe_id}")
def update_tribe(tribe_id: int, tribe: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        UPDATE tribes 
        SET name = %s, priority = %s, chapter_lead_id = %s
        WHERE id = %s
        RETURNING *
    """, (
        tribe["name"],
        tribe["priority"],
        tribe.get("chapter_lead_id"),
        tribe_id
    ))
    updated_tribe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated_tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")
    return updated_tribe

@app.delete("/api/v1/tribes/{tribe_id}")
def delete_tribe(tribe_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tribes WHERE id = %s RETURNING id", (tribe_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Tribe not found")
    return {"message": "Deleted"}

# CHAPTER LEADS ENDPOINTS
@app.get("/api/v1/chapter-leads")
def get_chapter_leads():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM chapter_leads ORDER BY name")
    leads = cur.fetchall()
    cur.close()
    conn.close()
    return {"items": leads, "total": len(leads)}

@app.post("/api/v1/chapter-leads")
def create_chapter_lead(lead: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO chapter_leads (name, email)
        VALUES (%s, %s)
        RETURNING *
    """, (lead["name"], lead.get("email", "")))
    new_lead = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_lead

@app.put("/api/v1/chapter-leads/{lead_id}")
def update_chapter_lead(lead_id: int, lead: dict):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        UPDATE chapter_leads 
        SET name = %s, email = %s
        WHERE id = %s
        RETURNING *
    """, (lead["name"], lead.get("email", ""), lead_id))
    updated_lead = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated_lead:
        raise HTTPException(status_code=404, detail="Chapter lead not found")
    return updated_lead

@app.delete("/api/v1/chapter-leads/{lead_id}")
def delete_chapter_lead(lead_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Unassign from tribes first
    cur.execute("UPDATE tribes SET chapter_lead_id = NULL WHERE chapter_lead_id = %s", (lead_id,))
    
    # Delete the chapter lead
    cur.execute("DELETE FROM chapter_leads WHERE id = %s RETURNING id", (lead_id,))
    deleted = cur.fetchone()
    
    conn.commit()
    cur.close()
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Chapter lead not found")
    return {"message": "Deleted"}

# CALCULATIONS ENDPOINTS
@app.post("/api/v1/calculate")
def calculate_fte(data: dict):
    inputs = data.get("inputs", {})
    squad_id = data.get("squad_id")
    
    # Calculate FTE
    dev_count = inputs.get("DEV_COUNT", 0)
    platforms_tested = len(inputs.get("PLATFORMS_TESTED", []))
    third_party_count = inputs.get("THIRD_PARTY_COUNT", 0)
    prod_bugs = inputs.get("PROD_BUGS_Q", 0)
    
    # Base calculation
    needed_fte = dev_count * 0.3
    
    # Adjustments
    needed_fte += platforms_tested * 0.2
    needed_fte += third_party_count * 0.1
    if prod_bugs > 10:
        needed_fte += 0.5
    
    needed_fte = round(needed_fte, 2)
    
    # Current FTE
    current_fte = sum([inputs.get(f"CURR_L{i}", 0) for i in range(1, 6)])
    fte_gap = round(needed_fte - current_fte, 2)
    
    # Risk level
    if fte_gap > 3:
        gap_risk_level = "CRITICAL"
    elif fte_gap > 2:
        gap_risk_level = "HIGH"
    elif fte_gap > 1:
        gap_risk_level = "MEDIUM"
    elif fte_gap > 0:
        gap_risk_level = "LOW"
    else:
        gap_risk_level = "NO RISK"
    
    result = {
        "squad_id": squad_id,
        "needed_fte": needed_fte,
        "current_fte": current_fte,
        "fte_gap": fte_gap,
        "gap_risk_level": gap_risk_level
    }
    
    # Save to database
    if squad_id:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Save calculation
        cur.execute("""
            INSERT INTO calculations (squad_id, needed_fte, current_fte, fte_gap, total_weight, inputs, effects)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            squad_id,
            needed_fte,
            current_fte,
            fte_gap,
            needed_fte,
            json.dumps(inputs),
            json.dumps({})
        ))
        
        # Update squad's last_calculation
        cur.execute("""
            UPDATE squads 
            SET last_calculation = %s
            WHERE id = %s
        """, (
            json.dumps(result),
            squad_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
    
    return result

@app.post("/api/v1/calculate/save")
def save_calculation(data: dict):
    return calculate_fte(data)

@app.get("/api/v1/calculations/trend")
def get_trend():
    return {"trend": []}

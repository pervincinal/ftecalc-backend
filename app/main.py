from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pip._internal.utils import datetime
from psycopg2.extras import RealDictCursor
from datetime import datetime
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
        host="aws-1-eu-central-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.ybpjyutscwzhlkrzoltz",
        password="Ad8gt,b?g9GR_bC"
    )

# Configuration storage
config_storage = {
    "weights": {
        "dev_ratio": 0.2,
        "cr_factor": 0.01,
        "platform_factor": 0.1,
        "third_party_factor": 0.01,
        "bug_threshold": 10,
        "bug_addition": 0.02,
        "incident_threshold": 4,
        "incident_addition": 0.2,
        "test_type_factor": 0.05,  # Added for test types
        "release_freq_daily": 0.4,  # Added for release frequency
        "release_freq_weekly": 0.3,
        "release_freq_biweekly": 0.2,
        "release_freq_monthly": 0.1,
        "shared_support_max": 0.25  # Added for shared support limit
    }
}

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

@app.get("/api/v1/squads/{squad_id}/last-calculation")
def get_last_calculation(squad_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
                SELECT * FROM calculations
                WHERE squad_id = %s
                ORDER BY created_at DESC NULLS LAST, id DESC
                    LIMIT 1
                """, (squad_id,))

    calculation = cur.fetchone()
    cur.close()
    conn.close()

    if calculation:
        if isinstance(calculation.get('inputs'), str):
            inputs = json.loads(calculation['inputs'])
            # Convert old field name to new one
            if 'STORIES_PER_SPRINT' in inputs and 'CR_PER_MONTH' not in inputs:
                inputs['CR_PER_MONTH'] = inputs.pop('STORIES_PER_SPRINT')
            calculation['inputs'] = inputs
        if isinstance(calculation.get('effects'), str):
            calculation['effects'] = json.loads(calculation['effects'])

    return calculation if calculation else {}

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

    try:
        # Delete related calculations first
        cur.execute("DELETE FROM calculations WHERE squad_id = %s", (squad_id,))

        # Delete the squad
        cur.execute("DELETE FROM squads WHERE id = %s RETURNING id", (squad_id,))
        deleted = cur.fetchone()

        conn.commit()

        if not deleted:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Squad not found")

        cur.close()
        conn.close()
        return {"message": "Deleted"}
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# TRIBES ENDPOINTS
@app.get("/api/v1/tribes")
def get_tribes(limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"""
        SELECT t.*, 
               cl.name as chapter_lead_name,
               COUNT(s.id) as squads,
               COALESCE(SUM(CASE 
                   WHEN s.last_calculation IS NOT NULL 
                   THEN (s.last_calculation->>'fte_gap')::float 
                   ELSE 0 
               END), 0) as total_fte_gap
        FROM tribes t
        LEFT JOIN chapter_leads cl ON t.chapter_lead_id = cl.id
        LEFT JOIN squads s ON t.id = s.tribe_id
        GROUP BY t.id, cl.name
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
    cur.execute("UPDATE tribes SET chapter_lead_id = NULL WHERE chapter_lead_id = %s", (lead_id,))
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
    try:
        inputs = data.get("inputs", {})
        squad_id = data.get("squad_id")
        weights = config_storage.get("weights", {})

        # Check if squad has a Chapter Lead through their tribe
        has_chapter_lead = False
        if squad_id:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                        SELECT t.chapter_lead_id
                        FROM squads s
                                 LEFT JOIN tribes t ON s.tribe_id = t.id
                        WHERE s.id = %s
                        """, (squad_id,))
            result = cur.fetchone()
            if result and result.get('chapter_lead_id'):
                has_chapter_lead = True
            cur.close()
            conn.close()

        # Get CR count - handle both field names
        cr_count = inputs.get("CR_PER_MONTH", inputs.get("STORIES_PER_SPRINT", 0))

        # Get all inputs
        dev_count = inputs.get("DEV_COUNT", 0)
        platforms_tested = len(inputs.get("PLATFORMS_TESTED", []))
        third_party_count = inputs.get("THIRD_PARTY_COUNT", 0)
        prod_bugs = inputs.get("PROD_BUGS_Q", 0)
        incidents = inputs.get("INCIDENTS_Q", 0)
        automation_coverage = inputs.get("AUTOMATION_COVERAGE", 0)
        test_types = len(inputs.get("TEST_TYPES", []))
        release_freq = inputs.get("RELEASE_FREQ", "MONTHLY")

        # Base calculation
        needed_fte = dev_count * weights.get("dev_ratio", 0.2)

        # Add FTE based on CRs
        needed_fte += cr_count * weights.get("cr_factor", 0.01)

        # Platform adjustment
        needed_fte += platforms_tested * weights.get("platform_factor", 0.1)

        # Third party adjustment
        needed_fte += third_party_count * weights.get("third_party_factor", 0.01)

        # Release frequency adjustment
        release_freq_factor = {
            "DAILY": weights.get("release_freq_daily", 0.4),      # Highest - daily releases need most QA
            "WEEKLY": weights.get("release_freq_weekly", 0.3),
            "BIWEEKLY": weights.get("release_freq_biweekly", 0.2),
            "MONTHLY": weights.get("release_freq_monthly", 0.1)   # Lowest - monthly releases need least QA
        }
        needed_fte += release_freq_factor.get(release_freq, 0.1)

        # Test types adjustment (more test types = more FTE)
        needed_fte += test_types * weights.get("test_type_factor", 0.05)

        # Bug adjustment
        if prod_bugs > weights.get("bug_threshold", 10):
            needed_fte += weights.get("bug_addition", 0.02)

        # Incident adjustment
        if incidents > weights.get("incident_threshold", 4):
            needed_fte += weights.get("incident_addition", 0.2)

        # Chapter Lead reduction - squads with Chapter Leads need slightly less FTE
        if has_chapter_lead:
            needed_fte -= 0.01
            print(f"Chapter lead reduction: -0.01")

        needed_fte = max(0, round(needed_fte, 2))  # Ensure it doesn't go negative

        # Apply level multipliers for current FTE
        level_multipliers = {
            "L1": 0.8,
            "L2": 1.0,
            "L3": 1.2,
            "L4": 1.4,
            "L5": 1.6
        }

        current_fte = (
                inputs.get("CURR_L1", 0) * level_multipliers["L1"] +
                inputs.get("CURR_L2", 0) * level_multipliers["L2"] +
                inputs.get("CURR_L3", 0) * level_multipliers["L3"] +
                inputs.get("CURR_L4", 0) * level_multipliers["L4"] +
                inputs.get("CURR_L5", 0) * level_multipliers["L5"]
        )

        # Add shared support (max 0.25 each)
        shared_auto = 0.25 if inputs.get("HAS_AUTO_SUPPORT", False) else 0
        shared_perf = 0.25 if inputs.get("HAS_PERF_SUPPORT", False) else 0
        current_fte += shared_auto + shared_perf

        current_fte = round(current_fte, 2)
        fte_gap = round(needed_fte - current_fte, 2)

        # Risk level
        if fte_gap > 1.4:
            gap_risk_level = "CRITICAL"
        elif fte_gap > 1:
            gap_risk_level = "HIGH"
        elif fte_gap > 0.5:
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

        # Debug logging
        print(f"Base from devs: {dev_count * weights.get('dev_ratio', 0.2)}")
        print(f"From CRs: {cr_count * weights.get('cr_factor', 0.01)}")
        print(f"From platforms: {platforms_tested * weights.get('platform_factor', 0.1)}")
        print(f"From release freq: {release_freq_factor.get(release_freq, 0.1)}")
        print(f"From test types: {test_types * weights.get('test_type_factor', 0.05)}")
        if has_chapter_lead:
            print(f"Chapter Lead reduction: -0.01")
        print(f"Total needed FTE: {needed_fte}")

        # Save to database if squad_id provided
        if squad_id:
            conn = get_db_connection()
            cur = conn.cursor()

            # Normalize field names for saving
            save_inputs = inputs.copy()
            if 'STORIES_PER_SPRINT' in save_inputs:
                save_inputs['CR_PER_MONTH'] = save_inputs.pop('STORIES_PER_SPRINT')

            from datetime import datetime

            cur.execute("""
                        INSERT INTO calculations (squad_id, needed_fte, current_fte, fte_gap, total_weight, inputs, effects, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            squad_id,
                            needed_fte,
                            current_fte,
                            fte_gap,
                            needed_fte,
                            json.dumps(save_inputs),
                            json.dumps({"config": weights, "cr_count": cr_count, "has_chapter_lead": has_chapter_lead}),
                            datetime.utcnow()
                        ))

            cur.execute("""
                        UPDATE squads
                        SET last_calculation = %s
                        WHERE id = %s
                        """, (json.dumps({
                **result,
                "inputs": save_inputs
            }), squad_id))

            conn.commit()
            cur.close()
            conn.close()

        return result

    except Exception as e:
        print(f"Error in calculate: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calculate/save")
def save_calculation(data: dict):
    return calculate_fte(data)

@app.get("/api/v1/calculations")
def get_calculations(squad_id: int = None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if squad_id:
        cur.execute("""
            SELECT * FROM calculations 
            WHERE squad_id = %s 
            ORDER BY created_at DESC
        """, (squad_id,))
    else:
        cur.execute("""
            SELECT * FROM calculations 
            ORDER BY created_at DESC 
            LIMIT 100
        """)
    
    calculations = cur.fetchall()
    cur.close()
    conn.close()
    
    return {"items": calculations, "total": len(calculations)}

@app.get("/api/v1/calculations/trend")
def get_trend():
    return {"trend": []}

@app.get("/api/v1/config")
def get_config():
    return config_storage

@app.put("/api/v1/config")
def update_config(config: dict):
    global config_storage
    config_storage = config
    return config_storage

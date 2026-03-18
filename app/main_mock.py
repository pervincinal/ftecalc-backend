from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
tribes = [
    {"id": 1, "name": "Digital Banking", "priority": "BUSINESS_CRITICAL"},
    {"id": 6, "name": "Personal", "priority": "MISSION_CRITICAL"}
]

squads = [
    {"id": 1, "name": "Personal Cabinet", "tribe_id": 6, "priority": "BUSINESS_CRITICAL", "platforms": ["IOS", "ANDROID"], "status": "ACTIVE"}
]

chapter_leads = [
    {"id": 1, "name": "John Doe", "email": "john@example.com"}
]

@app.get("/api/v1/tribes")
def get_tribes(limit: int = 100):
    return {"items": tribes[:limit], "total": len(tribes)}

@app.get("/api/v1/squads")
def get_squads(limit: int = 100):
    return {"items": squads[:limit], "total": len(squads)}

@app.get("/api/v1/chapter-leads")
def get_chapter_leads():
    return {"items": chapter_leads, "total": len(chapter_leads)}

@app.post("/api/v1/tribes")
def create_tribe(tribe: dict):
    new_tribe = {"id": len(tribes) + 1, **tribe}
    tribes.append(new_tribe)
    return new_tribe

@app.post("/api/v1/squads")
def create_squad(squad: dict):
    new_squad = {"id": len(squads) + 1, **squad}
    squads.append(new_squad)
    return new_squad

@app.put("/api/v1/squads/{squad_id}")
def update_squad(squad_id: int, squad: dict):
    for s in squads:
        if s["id"] == squad_id:
            s.update(squad)
            return s
    raise HTTPException(status_code=404, detail="Squad not found")

@app.put("/api/v1/tribes/{tribe_id}")
def update_tribe(tribe_id: int, tribe: dict):
    for t in tribes:
        if t["id"] == tribe_id:
            t.update(tribe)
            return t
    raise HTTPException(status_code=404, detail="Tribe not found")

@app.delete("/api/v1/squads/{squad_id}")
def delete_squad(squad_id: int):
    global squads
    squads = [s for s in squads if s["id"] != squad_id]
    return {"message": "Deleted"}

@app.delete("/api/v1/tribes/{tribe_id}")
def delete_tribe(tribe_id: int):
    global tribes
    tribes = [t for t in tribes if t["id"] != tribe_id]
    return {"message": "Deleted"}

@app.get("/api/v1/calculations/trend")
def get_trend():
    return {"trend": []}

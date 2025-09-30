# server/routes/cpu.py (REGENERATED FOR SERVER-SIDE ALERTS)
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from server.modules import CpuProcess, AlertPayload
from server.database import get_conn
from server.auth.dependencies import get_current_user
from threading import Lock
from datetime import datetime, timedelta
from typing import List
from server.auth.api_key_dep import verify_api_key

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

latest_processes = {} # Store data per agent UUID
system_stats = {}   # Store stats per agent UUID
data_lock = Lock()

@router.get("/dashboard/cpu", response_class=HTMLResponse)
async def cpu_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_cpu.html", {"request": request, "user": user})

@router.post("/api/v1/cpu_processes", dependencies=[Depends(verify_api_key)])
def receive_cpu_processes(procs: List[CpuProcess], request: Request):
    agent_uuid = request.headers.get("X-Agent-UUID")
    if not agent_uuid: return {"status": "error", "detail": "Missing agent UUID"}
    with data_lock:
        latest_processes[agent_uuid] = {"data": [p.dict() for p in procs], "timestamp": datetime.now()}
    return {"status": "ok"}

@router.get("/api/v1/dashboard/cpu")
def get_cpu_processes(user: dict = Depends(get_current_user)):
    # This now returns data for all agents, assuming one main view.
    # Can be adapted to return data for a specific agent if needed.
    all_procs = []
    with data_lock:
        for agent_id, data in latest_processes.items():
            if datetime.now() - data["timestamp"] < timedelta(seconds=90):
                all_procs.extend(data["data"])
    return {"data": all_procs}

@router.post("/api/v1/system_stats", dependencies=[Depends(verify_api_key)])
def post_system_stats(payload: dict, request: Request):
    agent_uuid = request.headers.get("X-Agent-UUID")
    if not agent_uuid: return {"status": "error", "detail": "Missing agent UUID"}
    with data_lock:
        system_stats[agent_uuid] = {"data": payload, "timestamp": datetime.now()}
    return {"status": "ok"}

@router.get("/api/v1/dashboard/system_stats")
def get_system_stats(user: dict = Depends(get_current_user)):
    # For simplicity, returning stats from the most recently seen agent
    with data_lock:
        latest_agent = max(system_stats, key=lambda k: system_stats[k]['timestamp'], default=None)
        if latest_agent and datetime.now() - system_stats[latest_agent]["timestamp"] < timedelta(seconds=90):
             return system_stats[latest_agent].get("data", {})
    return JSONResponse(status_code=503, content={"error": "Client agent is offline."})

# --- NEW ALERT ENDPOINTS ---
@router.post("/api/v1/alerts", dependencies=[Depends(verify_api_key)], status_code=201)
def receive_alert(payload: AlertPayload):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Check for an existing active alert for this source
                cur.execute("SELECT id FROM alerts WHERE source = %s AND status = 'Active'", (payload.source,))
                if cur.fetchone():
                    # If it exists, just update its timestamp to keep it alive
                    cur.execute("UPDATE alerts SET timestamp = NOW() WHERE source = %s AND status = 'Active'", (payload.source,))
                else:
                    # Otherwise, insert a new alert
                    cur.execute(
                        "INSERT INTO alerts (agent_uuid, alert_type, value, source) VALUES (%s, %s, %s, %s)",
                        (payload.agent_uuid, payload.alert_type, payload.value, payload.source)
                    )
                conn.commit()
    except Exception as e:
        print(f"DATABASE ERROR receiving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to store alert.")
    return {"status": "alert received"}

@router.get("/api/v1/dashboard/alerts")
def get_all_alerts(user: dict = Depends(get_current_user)):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Update status of old alerts to 'Terminated'
                cur.execute("UPDATE alerts SET status = 'Terminated' WHERE status = 'Active' AND timestamp < NOW() - INTERVAL '15 seconds'")
                conn.commit()
                
                # Fetch all alerts
                cur.execute("""
                    SELECT a.id, a.agent_uuid, ag.hostname, a.alert_type, a.value, a.source, a.timestamp, a.status 
                    FROM alerts a JOIN agents ag ON a.agent_uuid = ag.agent_uuid
                    ORDER BY a.timestamp DESC LIMIT 100
                """)
                colnames = [desc[0] for desc in cur.description]
                rows = [dict(zip(colnames, row)) for row in cur.fetchall()]
        return {"data": rows}
    except Exception as e:
        print(f"DATABASE ERROR fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts.")
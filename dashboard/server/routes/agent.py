# server/routes/agent.py (CORRECTED AND FINAL VERSION)
import uuid
import secrets
import hashlib
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone

from server.database import get_conn
from server.modules import AgentEnrollmentPayload
from server.auth.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

# --- HTML Page Route ---
@router.get("/dashboard/agents", response_class=HTMLResponse)
async def agents_dashboard_page(request: Request, user: dict = Depends(get_current_user)):
    """Serves the main agent management dashboard page."""
    # This assumes your template is named 'dashboard_agents.html'
    return templates.TemplateResponse("dashboard_agents.html", {"request": request, "user": user})

# --- API Route to LIST all agents (Corrected SELECT) ---
@router.get("/api/v1/agents")
def get_all_agents(user: dict = Depends(get_current_user)):
    """Provides a JSON list of all registered agents and their status."""
    agents = []
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # ✅ FIX: This SELECT query now matches your database schema precisely.
                cur.execute("""
                    SELECT agent_uuid, hostname, ip_address, os_name, last_seen, is_active 
                    FROM agents 
                    ORDER BY last_seen DESC NULLS LAST, hostname
                """)
                rows = cur.fetchall()
        
        now = datetime.now(timezone.utc)
        
        for row in rows:
            # The unpacking now matches the SELECT statement
            agent_uuid, hostname, ip_address, os_name, last_seen, is_active = row
            
            status = "Disconnected"
            if not is_active:
                status = "Revoked"
            # Agent is considered connected if seen in the last 90 seconds
            # This logic is correct for timezone-aware datetimes
            elif last_seen and (now - last_seen) < timedelta(seconds=90):
                status = "Connected"
            
            agents.append({
                "agent_uuid": agent_uuid,
                "hostname": hostname,
                "ip_address": ip_address,
                "os_name": os_name,
                "last_seen": last_seen.isoformat() if last_seen else None,
                "status": status
            })
    except Exception as e:
        # This is where the error happens. Check your server logs for the exact error.
        print(f"!!! DATABASE ERROR FETCHING AGENTS: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent data due to a server error.")
        
    return agents

# --- Agent Enrollment Route (Corrected INSERT) ---
@router.post("/api/v1/agents/enroll", status_code=201)
def enroll_agent(payload: AgentEnrollmentPayload):
    """Enroll a new agent."""
    agent_uuid = str(uuid.uuid4())
    new_api_key = secrets.token_hex(32)
    api_key_hash = hashlib.sha256(new_api_key.encode()).hexdigest()

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # ✅ FIX: This INSERT is now explicit and matches your database schema.
                # It no longer relies on defaults and explicitly sets initial values.
                cur.execute(
                    """
                    INSERT INTO agents (agent_uuid, api_key_hash, hostname, ip_address, os_name, is_active, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        agent_uuid,
                        api_key_hash,
                        payload.hostname,
                        payload.ip_address,
                        payload.os_name,
                        True,       # Default for is_active
                        None        # Default for last_seen
                    )
                )
                conn.commit()
    except Exception as e:
        print(f"!!! DATABASE ERROR DURING ENROLLMENT: {e}")
        raise HTTPException(status_code=500, detail=f"An internal database error occurred: {e}")

    return {"agent_uuid": agent_uuid, "api_key": new_api_key}
# Add this entire function to the end of server/routes/agent.py

@router.get("/dashboard/agent/{agent_uuid}", response_class=HTMLResponse)
async def single_agent_dashboard_page(request: Request, agent_uuid: str, user: dict = Depends(get_current_user)):
    """Serves the dashboard page for a single, specific agent."""
    agent_details = None
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM agents WHERE agent_uuid = %s", (agent_uuid,))
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Agent not found")
                
                # Convert the database row into a dictionary
                colnames = [desc[0] for desc in cur.description]
                agent_details = dict(zip(colnames, result))

                # You can add status calculation here if needed
                # For now, we'll just pass the raw data
                
    except Exception as e:
        print(f"Error fetching single agent details: {e}")
        # You could render an error page here if you wanted
        raise HTTPException(status_code=500, detail="Could not fetch agent details.")

    return templates.TemplateResponse("dashboard_single_agent.html", {
        "request": request,
        "user": user,
        "agent": agent_details
    })
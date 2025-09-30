# server/routes/dashboard.py 

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from server.database import get_conn
from server.auth.dependencies import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

# --- API: GLOBAL DASHBOARD SUMMARY ---
@router.get("/api/v1/dashboard/summary", tags=["Dashboard API"])
def get_dashboard_summary(user: dict = Depends(get_current_user)):
    """Computes a robust summary of ALL agent data for the main dashboard."""
    summary_data = {
        "top_process": "N/A", "active_sessions": 0, "last_command": "N/A",
        "changed_files_count": 0, "failed_logins_count": 0, "audit_events_count": 0,
    }
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Active Sessions (Global): Correctly finds the last event for each session and counts active ones.
                cur.execute("""
                    WITH latest_events AS (
                        SELECT DISTINCT ON (session_id) event
                        FROM login_sessions
                        ORDER BY session_id, timestamp DESC
                    )
                    SELECT count(*) FROM latest_events WHERE event != 'logout';
                """)
                res = cur.fetchone()
                if res: summary_data["active_sessions"] = res[0]

                # Top CPU Process (Global): Robustly finds the top process from the last 5 minutes.
                cur.execute("""
                    SELECT command, cpu_percent FROM cpu_processes 
                    WHERE timestamp > NOW() - INTERVAL '5 minutes'
                    ORDER BY cpu_percent DESC, timestamp DESC LIMIT 1;
                """)
                res = cur.fetchone()
                if res: summary_data["top_process"] = f"{res[0][:30]} ({res[1]}%)"

                # Last Command (Global)
                cur.execute("SELECT commands FROM command_history ORDER BY timestamp DESC LIMIT 1;")
                res = cur.fetchone()
                if res: summary_data["last_command"] = (res[0][:30] + '...') if len(res[0]) > 30 else res[0]

                # Files Changed Today (Global)
                cur.execute("SELECT count(*) FROM file_integrity WHERE timestamp >= date_trunc('day', NOW());")
                res = cur.fetchone()
                if res: summary_data["changed_files_count"] = res[0]

                # Failed Logins Today (Global)
                cur.execute("SELECT count(*) FROM security_logs WHERE event_type = 'failed_login' AND received_at >= date_trunc('day', NOW());")
                res = cur.fetchone()
                if res: summary_data["failed_logins_count"] = res[0]
                
                # Active Alerts (Global)
                cur.execute("SELECT count(*) FROM alerts WHERE status = 'Active';")
                res = cur.fetchone()
                if res: summary_data["audit_events_count"] = res[0]


    except Exception as e:
        print(f"Error fetching global dashboard summary: {e}")
    
    return JSONResponse(content=summary_data)


# --- API: AGENT-SPECIFIC DASHBOARD SUMMARY ---
@router.get("/api/v1/dashboard/summary/{agent_uuid}", tags=["Dashboard API"])
def get_agent_specific_summary(agent_uuid: str, user: dict = Depends(get_current_user)):
    """Computes a robust summary of data for ONLY a single, specific agent."""
    summary_data = {
        "top_process": "N/A", "active_sessions": 0, "last_command": "N/A",
        "changed_files_count": 0, "failed_logins_count": 0, "audit_events_count": 0,
    }
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Verify the agent exists
                cur.execute("SELECT hostname FROM agents WHERE agent_uuid = %s", (agent_uuid,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Agent not found")
                
                # Active Sessions for this agent
                cur.execute("""
                    WITH latest_events AS (
                        SELECT DISTINCT ON (session_id) event
                        FROM login_sessions
                        WHERE agent_uuid = %s
                        ORDER BY session_id, timestamp DESC
                    )
                    SELECT count(*) FROM latest_events WHERE event != 'logout';
                """, (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["active_sessions"] = res[0]
                
                # Top Process in the last 5 minutes for this agent
                cur.execute("""
                    SELECT command, cpu_percent FROM cpu_processes 
                    WHERE agent_uuid = %s AND timestamp > NOW() - INTERVAL '5 minutes'
                    ORDER BY cpu_percent DESC, timestamp DESC LIMIT 1;
                """, (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["top_process"] = f"{res[0][:30]} ({res[1]}%)"

                # Last command for this specific agent
                cur.execute("SELECT commands FROM command_history WHERE agent_uuid = %s ORDER BY timestamp DESC LIMIT 1;", (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["last_command"] = (res[0][:30] + '...') if len(res[0]) > 30 else res[0]

                # Files Changed Today for this specific agent
                cur.execute("SELECT count(*) FROM file_integrity WHERE agent_uuid = %s AND timestamp >= date_trunc('day', NOW());", (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["changed_files_count"] = res[0]

                # Failed Logins Today for this specific agent
                cur.execute("SELECT count(*) FROM security_logs WHERE agent_uuid = %s AND event_type = 'failed_login' AND received_at >= date_trunc('day', NOW());", (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["failed_logins_count"] = res[0]
                
                # Active Alerts for this specific agent
                cur.execute("SELECT count(*) FROM alerts WHERE agent_uuid = %s AND status = 'Active';", (agent_uuid,))
                res = cur.fetchone()
                if res: summary_data["audit_events_count"] = res[0]

    except Exception as e:
        print(f"Error fetching agent-specific summary for UUID {agent_uuid}: {e}")
    
    return JSONResponse(content=summary_data)
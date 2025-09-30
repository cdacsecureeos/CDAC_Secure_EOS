# server/routes/monitor_login.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from server.database import get_conn
from server.modules import SessionEvent
from server.auth.dependencies import get_current_user
from server.auth.api_key_dep import verify_api_key

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

# (HTML and POST endpoints are unchanged)
# ...
@router.get("/dashboard/sessions", response_class=HTMLResponse)
async def sessions_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_sessions.html", {
        "request": request,
        "user": user
    })

@router.post("/api/v1/sessions", dependencies=[Depends(verify_api_key)])
def receive_session(session: SessionEvent):
    # ... (this function is correct and unchanged)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO login_sessions
                (session_id, username, tty, from_ip, login_time, idle, jcpu, pcpu, command, event, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session.session_id, session.username, session.tty, session.from_ip,
                session.login_time, session.idle, session.jcpu, session.pcpu,
                session.command, session.event, session.timestamp
            ))
            conn.commit()
    return {"status": "ok"}


# 🔐 API endpoint for frontend DataTable (main view)
@router.get("/api/v1/sessions")
def get_sessions():
    with get_conn() as conn:
        with conn.cursor() as cur:
        
            
            query = """
                WITH latest_sessions AS (
                    SELECT DISTINCT ON (session_id) *
                    FROM login_sessions
                    ORDER BY session_id, timestamp DESC
                )
                SELECT * FROM latest_sessions
                ORDER BY timestamp DESC
                LIMIT 50;
            """
            cur.execute(query)
          

            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            
            data = []
            for row in rows:
                row_dict = dict(zip(colnames, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                data.append(row_dict)
        
    return JSONResponse(content={"data": data})

# API endpoint for session-specific analytics (drill-down view)
@router.get("/api/v1/sessions/{session_id}")
def get_session_details(session_id: str):
    # ... (this function is correct and unchanged)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM login_sessions
                WHERE session_id = %s
                ORDER BY timestamp ASC
            """, (session_id,))

            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            data = []
            for row in rows:
                row_dict = dict(zip(colnames, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                data.append(row_dict)

    return JSONResponse(content={"data": data})
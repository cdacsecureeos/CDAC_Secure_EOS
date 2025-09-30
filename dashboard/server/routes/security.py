# server/routes/security.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from server.auth.dependencies import get_current_user
from server.database import get_conn
from server.modules import SecurityEvent
from datetime import datetime
from server.auth.api_key_dep import verify_api_key

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")


# ========================
# 🔐 Dashboard: Security Events
# ========================
@router.get("/dashboard/security", response_class=HTMLResponse)
async def security_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_security.html", {"request": request, "user": user})


# 📤 API: Get latest SSH/Brute-force Security Events
@router.get("/api/v1/dashboard/security")
def get_security_logs():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT username, from_ip, event, description, received_at
                FROM security_logs
                ORDER BY received_at DESC
                LIMIT 100
            """)
            rows = cur.fetchall()

    return JSONResponse(content={
        "data": [
            {
                "username": r[0],
                "from_ip": r[1],
                "event": r[2],
                "description": r[3],
                "received_at": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else None

            } for r in rows
        ]
    })


# 📥 API: Receive Security Event
@router.post("/api/v1/security_logs", dependencies=[Depends(verify_api_key)])
def receive_security_event(payload: SecurityEvent):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO security_logs (username, from_ip,  event, description, received_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                payload.username,
                payload.source_ip,
                payload.event_type,
                payload.description,
                datetime.now()
            ))
            conn.commit()
    return {"status": "ok"}

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from server.database import get_conn
from datetime import datetime
from server.auth.dependencies import get_current_user
from fastapi.templating import Jinja2Templates
from server.auth.api_key_dep import verify_api_key

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

class CommandHistoryEntry(BaseModel):
    username: str
    from_ip: str
    session_id: str
    commands: str
    timestamp: str



@router.get("/dashboard/command_history", response_class=HTMLResponse)
def command_history_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_command_history.html", {"request": request, "user": user})

@router.get("/api/v1/dashboard/command_history")
def get_command_history():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, from_ip, session_id, commands, timestamp
                FROM command_history
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            rows = cur.fetchall()

    return {
        "data": [
            {
                "id": row[0],
                "username": row[1],
                "from_ip": row[2],
                "session_id": row[3],
                "commands": row[4],
                "timestamp": row[5].strftime("%Y-%m-%d %H:%M:%S")
            }
            for row in rows
        ]
    }

@router.post("/api/v1/command_history", dependencies=[Depends(verify_api_key)])
def receive_command_history(entry: CommandHistoryEntry):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO command_history (username, from_ip, session_id, commands, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                entry.username,
                entry.from_ip,
                entry.session_id,
                entry.commands,
                datetime.strptime(entry.timestamp, "%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    return {"status": "success"} 
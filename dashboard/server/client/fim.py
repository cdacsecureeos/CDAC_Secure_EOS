# server/routes/fim.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from server.modules import FileChange
from server.database import get_conn
from server.auth.dependencies import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

@router.get("/dashboard/file_integrity", response_class=HTMLResponse)
async def file_integrity_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_file_integrity.html", {"request": request, "user": user})

@router.post("/api/v1/file_integrity")
def receive_file_change(change: FileChange):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO file_integrity
                (file_path, checksum, change_type, from_ip, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                change.file_path,
                change.checksum,
                change.change_type,
                change.from_ip,
                change.timestamp
            ))
            conn.commit()
    return {"status": "ok"}

@router.get("/api/v1/dashboard/file_integrity")
def get_file_changes():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, file_path, checksum, change_type, from_ip, timestamp
                    FROM file_integrity
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                rows = cur.fetchall()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    return {
        "data": [
            {
                "id": row[0],
                "file_path": row[1],
                "checksum": row[2],
                "change_type": row[3],
                "from_ip": row[4],
                "timestamp": row[5].strftime("%Y-%m-%d %H:%M:%S")
            } for row in rows
        ]
    }

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from server.database import get_conn
from server.auth.dependencies import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

@router.get("/dashboard/charts", response_class=HTMLResponse)
async def charts_dashboard(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard_charts.html", {"request": request, "user": user})

@router.get("/api/v1/charts/top-files")
def top_modified_files():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT file_path, COUNT(*) as changes
                FROM file_integrity
                GROUP BY file_path
                ORDER BY changes DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
    return [{"file": r[0], "count": r[1]} for r in rows]

@router.get("/api/v1/charts/active-users")
def most_active_users():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT username, COUNT(*) FROM login_sessions
                GROUP BY username
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
    return [{"user": r[0], "count": r[1]} for r in rows]

@router.get("/api/v1/charts/login-trends")
def login_logout_trend():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DATE(timestamp) as day, event, COUNT(*)
                FROM login_sessions
                GROUP BY day, event
                ORDER BY day
            """)
            rows = cur.fetchall()
    return [{"date": str(r[0]), "event": r[1], "count": r[2]} for r in rows]

@router.get("/api/v1/charts/top-commands")
def top_commands():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT commands, COUNT(*) FROM command_history
                GROUP BY commands
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
    return [{"command": r[0], "count": r[1]} for r in rows]

#123

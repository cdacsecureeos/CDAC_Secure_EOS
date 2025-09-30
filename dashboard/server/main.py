from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
#from server.routes import audit_router
import os

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

#  FastAPI app initialization
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#  Mount static files and templates
app.mount("/static", StaticFiles(directory="server/static"), name="static")
templates = Jinja2Templates(directory="server/templates")

# OAuth2 token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Import authentication logic
from server.auth.jwt_handler import decode_token
from server.auth.dependencies import get_current_user

#  Import routers
from server.auth import auth_routes
from server.routes import cpu, cmd, dashboard, fim, charts, monitor_login, security,dashboard,agent
#from server.routes import audit_router

#  CORS middleware (for dev/local access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Publicly accessible paths
EXCLUDE_PATHS = {
    "/login", "/token", "/static", "/favicon.ico",
      "/api/v1/sessions", 
    "/api/v1/cpu_processes",
    "/api/v1/command_history", 
    "/api/v1/file_integrity",
    "/api/v1/security_logs",
    "/api/v1/system_stats",
    "/api/v1/audit",
    "/api/v1/sessions/active_count", "/api/v1/agents/enroll","/api/v1/alerts",
}

# Global authentication middleware
@app.middleware("http")
async def enforce_authentication(request: Request, call_next):
    path = request.url.path
    if any(path.startswith(p) for p in EXCLUDE_PATHS):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token or not decode_token(token):
        return RedirectResponse(url="/login")

    request.state.user = decode_token(token)
    return await call_next(request)

# Register routers
app.include_router(auth_routes.router)
app.include_router(cpu.router)
app.include_router(cmd.router)
app.include_router(fim.router)
app.include_router(monitor_login.router)
app.include_router(charts.router)
app.include_router(security.router)
app.include_router(dashboard.router)
app.include_router(agent.router)
app.include_router(dashboard.router, tags=["Dashboard"])



#app.include_router(audit_router.router)

#  Dashboard routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user": request.state.user,"agent": None,"Dashboard": None})

@app.get("/dashboard/charts", response_class=HTMLResponse)
async def charts_page(request: Request):
    return templates.TemplateResponse("dashboard_charts.html", {"request": request, "user": request.state.user})

#  Swagger & ReDoc (protected)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(request: Request):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Secure API Docs")

@app.get("/redoc", include_in_schema=False)
async def custom_redoc(request: Request):
    return get_redoc_html(openapi_url="/openapi.json", title="Secure ReDoc")

@app.get("/openapi.json", include_in_schema=False)
async def openapi_endpoint(request: Request):
    return JSONResponse(
        status_code=200,
        content=get_openapi(
            title="IoT Secure Dashboard",
            version="1.0.0",
            routes=app.routes,
        ),
    )

#  Error handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(get_current_user)):
    # This route now correctly serves the GLOBAL dashboard.
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "agent": None})
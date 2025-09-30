# server/auth/auth_routes.py (REGENERATED - SERVER-SIDE REDIRECT)

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from dotenv import load_dotenv
import os

from server.auth.jwt_handler import create_access_token
from server.auth.utils import verify_password

# Load environment variables
load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="server/templates")

VALID_USERNAME = os.getenv("VALID_USERNAME")
HASHED_ADMIN_PASSWORD = os.getenv("HASHED_ADMIN_PASSWORD")


# --- Route to SERVE the login page (Unchanged) ---
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Serves the HTML login page to the user's browser."""
    return templates.TemplateResponse("login.html", {"request": request})


# --- Route to PROCESS the login form from the browser ---
@router.post("/login")
async def handle_login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    This function now handles the login directly from the HTML form.
    It verifies credentials and sets the cookie on the server-side before redirecting.
    """
    if username != VALID_USERNAME or not verify_password(password, HASHED_ADMIN_PASSWORD):
        # If login fails, show the login page again with an error message
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

    # If login is successful, create the token
    token = create_access_token({"sub": username, "role": username})

    # Create a redirect response to the AGENTS dashboard
    response = RedirectResponse(url="/dashboard/agents", status_code=HTTP_302_FOUND)
    
    # Set the cookie directly on the response object
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        # IMPORTANT: We DO NOT use the 'secure=True' flag for local HTTP development
        secure=False,
        samesite="Lax"
    )
    
    return response


# --- Route to LOGOUT (Unchanged) ---
@router.get("/logout")
async def logout():
    """Clears the authentication cookie and redirects to the login page."""
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
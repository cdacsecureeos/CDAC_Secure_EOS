# server/auth/dependencies.py

from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from server.auth.jwt_handler import decode_token
import os
from dotenv import load_dotenv

load_dotenv()
ALLOWED_ROLE = os.getenv("VALID_USERNAME", "m@dh@v@n")  # You can set ADMIN_ROLE in .env

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )

    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # ✅ Role-based access control (RBAC)
    if payload.get("role") != ALLOWED_ROLE:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient privileges"
        )

    return payload

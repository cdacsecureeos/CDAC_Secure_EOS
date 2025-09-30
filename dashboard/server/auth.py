# server/auth.py
import bcrypt
import os
from dotenv import load_dotenv
from fastapi import Request, HTTPException

load_dotenv()
HASHED_ADMIN_PASSWORD = os.getenv("HASHED_ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def authenticate_user(username: str, password: str):
    if username == "admin" and verify_password(password, HASHED_ADMIN_PASSWORD):
        return username  # return just the string
    return None

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

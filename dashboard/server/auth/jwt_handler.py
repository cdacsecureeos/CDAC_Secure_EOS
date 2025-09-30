# server/auth/jwt_handler.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

with open("server/auth/keys/private.pem", "rb") as f:
    PRIVATE_KEY = f.read()
with open("server/auth/keys/public.pem", "rb") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = os.getenv("ALGORITHM", "RS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", ))
ISSUER = os.getenv("ISSUER", "iot-secure-api")
AUDIENCE = os.getenv("AUDIENCE", "iot-dashboard-client")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "jti": str(uuid.uuid4())
    })

    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE
        )
    except JWTError:
        return None

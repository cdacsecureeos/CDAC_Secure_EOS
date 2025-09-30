# server/auth/api_key_dep.py
import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import Security, HTTPException, status, Header
from server.database import get_conn

# We now expect TWO headers from the client
HEADER_AGENT_UUID = "X-Agent-UUID"
HEADER_API_KEY = "X-API-Key"

async def verify_api_key(
    agent_uuid: str = Header(None, alias=HEADER_AGENT_UUID),
    api_key: str = Header(None, alias=HEADER_API_KEY)
):
    """
    Dependency function to verify a per-agent API key.
    1. Checks for presence of both UUID and Key headers.
    2. Looks up the agent by its UUID in the database.
    3. Hashes the incoming API key.
    4. Compares the new hash with the stored hash in a secure way.
    5. Updates the 'last_seen' timestamp for the agent.
    """
    if not agent_uuid or not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required headers: '{HEADER_AGENT_UUID}' and '{HEADER_API_KEY}'",
        )

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT api_key_hash, is_active FROM agents WHERE agent_uuid = %s",
                    (agent_uuid,)
                )
                result = cur.fetchone()

                if not result:
                    raise HTTPException(status_code=401, detail="Invalid Agent UUID")

                stored_key_hash, is_active = result
                if not is_active:
                    raise HTTPException(status_code=403, detail="Agent has been deactivated")

                # Hash the API key provided by the agent
                incoming_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

                # Use secrets.compare_digest to prevent timing attacks
                if not secrets.compare_digest(incoming_key_hash, stored_key_hash):
                    raise HTTPException(status_code=401, detail="Invalid API Key")

                # If authentication succeeds, update the last_seen timestamp
                cur.execute(
                    "UPDATE agents SET last_seen = %s WHERE agent_uuid = %s",
                    (datetime.now(timezone.utc), agent_uuid)
                )
                conn.commit()

    except HTTPException as e:
        raise e  # Re-raise HTTPException to send the correct response
    except Exception as e:
        # Log this error for debugging
        print(f"Database error during API key verification: {e}")
        raise HTTPException(status_code=500, detail="Server error during authentication")

    # If we reach here, the agent is authenticated.
    return True
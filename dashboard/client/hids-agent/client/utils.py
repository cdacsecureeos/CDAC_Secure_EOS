import socket
import hashlib
import json
import requests
import os
import sys
from datetime import datetime

# --- Core Configuration ---
SERVER_URL = "https://10.182.0.73:8443"
CERT_PATH = "/root/hids-agent/client/cert.pem"
CONFIG_PATH = "/etc/hids-agent/agent.json" # Secure location for agent identity

# --- Security Enforcement ---
# 1. Enforce HTTPS: The agent will refuse to start if the server URL is insecure.
if not SERVER_URL.startswith("https://"):
    print("="*60)
    print("!! FATAL SECURITY ERROR: SERVER_URL must use https://. !!")
    print("!! Agent is configured to connect insecurely. Aborting. !!")
    print("="*60 + "\n")
    sys.exit(1)

# --- Agent Identity Loading ---
AGENT_CONFIG = {}

def load_agent_config():
    """
    Loads the agent's unique identity (UUID and API Key) from its config file.
    This function is called once at startup. If it fails, the agent cannot run.
    """
    global AGENT_CONFIG
    try:
        with open(CONFIG_PATH, "r") as f:
            AGENT_CONFIG = json.load(f)
        # Validate that the config file has the keys we need
        if "agent_uuid" not in AGENT_CONFIG or "api_key" not in AGENT_CONFIG:
            raise ValueError("Configuration file is missing required keys ('agent_uuid', 'api_key').")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print("\n" + "="*60)
        print("!! FATAL ERROR: Agent configuration is missing or invalid. !!")
        print(f"!! Reason: {e} !!")
        print(f"!! Could not load identity from: {CONFIG_PATH} !!")
        print("!! Please run the 'enroll_agent.py' script on this machine first. !!")
        print("="*60 + "\n")
        sys.exit(1)

# Load the agent's identity as soon as the module is imported.
load_agent_config()

# --- Network and System Utilities ---
HTTP_SESSION = requests.Session()

def get_local_ip():
    """Gets the primary local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # This doesn't actually send data, it just determines the outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

MY_IP = get_local_ip()

def compute_checksum(file_path):
    """Computes the SHA256 checksum of a file."""
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (IOError, OSError):
        return "unreadable"

def append_log(filename, data):
    """Appends a JSON line to a local log file for resilience."""
    try:
        with open(filename, "a", buffering=1) as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")
    except Exception as e:
        # Using print here for critical log-writing failures
        print(f"[CRITICAL] Failed to write to local log {filename}: {e}")

# --- Core Secure Communication Function ---
def post_data_securely(endpoint_path: str, payload: dict):
    """
    Sends data to the server API, authenticating with the agent's unique
    UUID and API Key in the headers.
    """
    url = f"{SERVER_URL}{endpoint_path}"
    
    # 2. Per-Agent Authentication: Headers now include the agent's unique identity
    #    loaded from the secure config file. This replaces the old shared API key.
    headers = {
        "Content-Type": "application/json",
        "X-Agent-UUID": AGENT_CONFIG.get("agent_uuid"),
        "X-API-Key": AGENT_CONFIG.get("api_key")
    }
    
    try:
        response = HTTP_SESSION.post(
            url,
            json=payload,
            headers=headers,
            verify=CERT_PATH, # Enforces TLS certificate validation
            timeout=15
        )
        response.raise_for_status() # Raises an exception for 4xx or 5xx status codes
        # This print is useful for debugging but can be commented out in production
        # for less console noise.
        # print(f"[{datetime.now()}] Successfully sent data to {endpoint_path}")
    except requests.exceptions.RequestException as e:
        # If sending fails, log the error and save the payload to a local file
        print(f"[{datetime.now()}] ERROR: Failed to send data to {endpoint_path}. Details: {e}")
        append_log(f"failed_{endpoint_path.replace('/', '_')}.jsonl", payload)

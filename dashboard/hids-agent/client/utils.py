# client/utils.py
import socket
import hashlib
import json
import requests
import os
import sys
from datetime import datetime

SERVER_URL = "https://10.182.0.73:8443"
CERT_PATH = "/root/hids-agent/client/cert.pem"
CONFIG_PATH = "/etc/hids-agent/agent.json"

if not SERVER_URL.startswith("https://"):
    print("FATAL SECURITY ERROR: SERVER_URL must use https://. Aborting.")
    sys.exit(1)

AGENT_CONFIG = {}
AGENT_UUID = None  # Global variable to hold the agent's UUID

def load_agent_config():
    global AGENT_CONFIG, AGENT_UUID
    try:
        with open(CONFIG_PATH, "r") as f:
            AGENT_CONFIG = json.load(f)
        if "agent_uuid" not in AGENT_CONFIG or "api_key" not in AGENT_CONFIG:
            raise ValueError("Config file is missing required keys ('agent_uuid', 'api_key').")
        AGENT_UUID = AGENT_CONFIG["agent_uuid"]
    except Exception as e:
        print(f"\nFATAL ERROR: Agent configuration is missing or invalid: {e}")
        print(f"Could not load identity from: {CONFIG_PATH}")
        print("Please run 'enroll_agent.py' on this machine first.\n")
        sys.exit(1)

load_agent_config()

HTTP_SESSION = requests.Session()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"

MY_IP = get_local_ip()

def append_log(filename, data):
    try:
        with open(filename, "a", buffering=1) as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")
    except Exception as e:
        print(f"[CRITICAL] Failed to write to local log {filename}: {e}")

def post_data_securely(endpoint_path: str, payload: dict, silent: bool = False):
    url = f"{SERVER_URL}{endpoint_path}"
    headers = {
        "Content-Type": "application/json",
        "X-Agent-UUID": AGENT_UUID,
        "X-API-Key": AGENT_CONFIG.get("api_key")
    }
    try:
        response = HTTP_SESSION.post(url, json=payload, headers=headers, verify=CERT_PATH, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if not silent:
            print(f"[{datetime.now()}] ERROR sending data to {endpoint_path}. Details: {e}")
        append_log(f"failed_{endpoint_path.replace('/', '_')}.jsonl", payload)

def compute_checksum(file_path: str, hash_algo: str = 'sha256'):
    """
    Computes the checksum of a file. Returns None if the file cannot be read.
    Reads the file in chunks to handle large files efficiently.
    """
    if not os.path.isfile(file_path):
        return None

    h = hashlib.new(hash_algo)
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, PermissionError) as e:
        print(f"[CHECKSUM_ERROR] Could not read file {file_path}: {e}")
        return None

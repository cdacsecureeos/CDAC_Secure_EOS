# client/utils.py (FINAL SECURE VERSION)

import socket
import hashlib
import json
import requests
import os
from datetime import datetime

SERVER_URL = "https://10.182.0.73:8443"
CERT_PATH = "/root/hids-agent/client/cert.pem" # Adjusted path for new location

# Retrieve the API Key from the environment, using VALID_API_KEY
API_KEY = os.getenv("VALID_API_KEY", "default-insecure-key-change-me")
if API_KEY == "default-insecure-key-change-me":
    print("\n" + "="*60)
    print("!! SECURITY WARNING: Using default insecure API key. !!")
    print("!! Set the VALID_API_KEY environment variable. !!")
    print("="*60 + "\n")

HTTP_SESSION = requests.Session()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

MY_IP = get_local_ip()

def compute_checksum(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb", buffering=65536) as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return "unreadable"

def append_log(filename, data):
    try:
        with open(filename, "a", buffering=1) as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")
    except Exception as e:
        print(f"[LOG ERROR] Failed to write {filename}: {e}")

def post_data_securely(endpoint_path: str, payload: dict):
    url = f"{SERVER_URL}{endpoint_path}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY 
    }
    try:
        response = HTTP_SESSION.post(
            url,
            json=payload,
            headers=headers,
            verify=CERT_PATH,
            timeout=15
        )
        response.raise_for_status()
        print(f"[{datetime.now()}] Successfully sent data to {endpoint_path}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ERROR: Failed to send data to {endpoint_path}. Details: {e}")
        append_log(f"failed_{endpoint_path.replace('/', '_')}.jsonl", payload)

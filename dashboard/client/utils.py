# client/utils.py
import socket, hashlib, json
from datetime import datetime
import requests

SERVER_URL = "https://10.182.0.73:8443"
CERT_PATH = "/root/client/client/cert.pem"

# 🧠 Cached session to reuse TCP connections (important for embedded OS)
HTTP_SESSION = requests.Session()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

MY_IP = get_local_ip()

def compute_checksum(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb", buffering=65536) as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return "unreadable"

def append_log(filename, data):
    try:
        with open(filename, "a", buffering=1) as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")
    except Exception as e:
        print(f"[LOG] Append error ({filename}): {e}")

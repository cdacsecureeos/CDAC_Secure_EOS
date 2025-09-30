# client/utils.py
import socket
import hashlib
import json
from datetime import datetime

# 🔗 API Endpoint (HTTPS with self-signed cert)
SERVER_URL = "https://10.182.0.73:8443"

# ✅ Path to the server's trusted certificate (copied from server)
CERT_PATH = "/root/client/client/cert.pem"

# 🌐 Get device IP address
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Using Google DNS to get outbound interface IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ✅ Store global IP once at startup
MY_IP = get_local_ip()

# 🔒 Compute SHA256 checksum of a file
def compute_checksum(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return "unreadable"

# 📝 Append structured log data to a .jsonl file
def append_log(filename, data):
    try:
        with open(filename, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"[LOG] Append error ({filename}): {e}")

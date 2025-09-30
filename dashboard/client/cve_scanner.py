# client/cve_scanner.py

import subprocess, time, requests, socket
from utils import SERVER_URL, append_log, CERT_PATH
from datetime import datetime
import socket
import re 
def scan_cve():
    try:
        hostname = socket.gethostname()
        result = subprocess.check_output("debsecan --format report", shell=True).decode()

        for line in result.splitlines():
            parts = line.strip().split(None, 3)
            if len(parts) < 4:
                continue  # Skip malformed lines

            package, cve_id, severity, description = parts

            # ✅ Strict validation
            if not re.match(r"^CVE-\d{4}-\d{4,7}$", cve_id):
                continue  # Not a real CVE, skip

            if severity.lower() not in ["low", "medium", "high", "critical"]:
                continue  # Invalid severity

            payload = {
                "host": hostname,
                "cve_id": cve_id,
                "package": package,
                "severity": severity.upper(),
                "description": description,
                "fixed_version": "-",
                "current_version": "-",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            requests.post(f"{SERVER_URL}/api/v1/cve_scan", json=payload, verify=CERT_PATH)
            append_log("cve_log.jsonl", payload)
            print(f"[CVE] Reported: {cve_id} in {package} ({severity})")

    except Exception as e:
        print(f"[CVE] Error: {e}")

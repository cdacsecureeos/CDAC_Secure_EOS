# client/cpu.py (accurate & lightweight using psutil)
import time
import psutil
import requests
from datetime import datetime
from utils import SERVER_URL, MY_IP , CERT_PATH

def monitor_cpu():
    while True:
        try:
            top = []
            for proc in psutil.process_iter(attrs=["pid", "username", "cpu_percent", "memory_percent", "cmdline"]):
                try:
                    info = proc.info
                    if not info["cmdline"] or "psutil" in info["cmdline"][0] or "cpu.py" in info["cmdline"][0]:
                        continue  # Skip self
                    top.append({
                        "pid": info["pid"],
                        "username": info["username"] or "unknown",
                        "cpu_percent": info["cpu_percent"],
                        "mem_percent": info["memory_percent"],
                        "command": " ".join(info["cmdline"])[:100],  # truncate for dashboard
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage and take top 5
            top = sorted(top, key=lambda x: x["cpu_percent"], reverse=True)[:5]

            for proc in top:
                payload = {
                    "pid": proc["pid"],
                    "username": proc["username"],
                    "cpu_percent": round(proc["cpu_percent"], 1),
                    "mem_percent": round(proc["mem_percent"], 1),
                    "time_used": "-",  # optional, we skip for now
                    "command": proc["command"],
                    "from_ip": MY_IP,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                requests.post(f"{SERVER_URL}/api/v1/cpu_processes", json=payload, verify=CERT_PATH)
            print("[CPU] Top 5 real processes sent")
        except Exception as e:
            print(f"[CPU] Error: {e}")
        time.sleep(30)

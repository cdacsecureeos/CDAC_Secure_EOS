# client/cpu.py (silent & optimized)

import time
import psutil
import requests
from datetime import datetime
from utils import SERVER_URL, MY_IP, CERT_PATH

def monitor_cpu():
    while True:
        try:
            top = []
            for proc in psutil.process_iter(attrs=["pid", "username", "cpu_percent", "memory_percent", "cmdline"]):
                try:
                    info = proc.info

                    if not info["cmdline"]:
                        continue
                    if "psutil" in info["cmdline"][0] or "cpu.py" in info["cmdline"][0]:
                        continue  # Skip self

                    if info["cpu_percent"] < 0.5:
                        continue  # Skip idle processes

                    try:
                        created = psutil.Process(info["pid"]).create_time()
                        time_used = str(datetime.now() - datetime.fromtimestamp(created)).split('.')[0]
                    except:
                        time_used = "-"

                    top.append({
                        "pid": info["pid"],
                        "username": info["username"] or "unknown",
                        "cpu_percent": round(info["cpu_percent"], 1),
                        "mem_percent": round(info["memory_percent"], 1),
                        "command": " ".join(info["cmdline"])[:100],
                        "time_used": time_used,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            top = sorted(top, key=lambda x: x["cpu_percent"], reverse=True)[:5]

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for proc in top:
                proc["from_ip"] = MY_IP
                proc["timestamp"] = now
                try:
                    requests.post(f"{SERVER_URL}/api/v1/cpu_processes", json=proc, verify=CERT_PATH)
                except:
                    pass  # Silent failure
        except:
            pass  # Silent failure

        time.sleep(30)

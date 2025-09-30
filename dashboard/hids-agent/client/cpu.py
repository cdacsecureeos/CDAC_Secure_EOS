# client/cpu.py (Production Version)
import time
import psutil
from datetime import datetime
from utils import MY_IP, AGENT_UUID, post_data_securely
from typing import List, Dict

STATE_MAP = {'R': 'Running', 'S': 'Sleeping', 'D': 'Waiting', 'Z': 'Zombie', 'T': 'Stopped', 'I': 'Idle'}
HIGH_CPU_THRESHOLD = 30.0

def collect_processes() -> List[Dict]:
    procs = []
    
    # --- MODIFIED: Generate ONE timestamp for the entire batch ---
    # This is the key to ensuring data consistency for a snapshot.
    # We use isoformat() as it's a standard that's easily parsed.
    timestamp_now_iso = datetime.now().isoformat()
    
    for p in psutil.process_iter(['pid', 'ppid', 'username', 'memory_percent', 'cmdline', 'nice', 'status', 'create_time']):
        try:
            if not p.info['cmdline']:
                continue
            with p.oneshot():
                mem_info = p.memory_info()
                cpu_percent = p.cpu_percent(interval=None) 
                
                process_data = {
                    "pid": p.info['pid'], "ppid": p.info['ppid'],
                    "username": p.info['username'] or "unknown",
                    "cpu_percent": round(cpu_percent, 1),
                    "mem_percent": round(p.info['memory_percent'], 1),
                    "command": " ".join(p.info['cmdline'])[:200],
                    "time_used": str(datetime.now() - datetime.fromtimestamp(p.info['create_time'])).split('.')[0],
                    "virt": mem_info.vms // 1024, "res": mem_info.rss // 1024,
                    "shr": getattr(mem_info, 'shared', 0) // 1024,
                    "priority": p.info['nice'], "nice": p.info['nice'],
                    "state": STATE_MAP.get(p.info['status'][0].upper(), p.info['status']),
                    "from_ip": MY_IP,
                    # --- MODIFIED: Use the SAME timestamp for every process in this batch ---
                    "timestamp": timestamp_now_iso
                }
                procs.append(process_data)
                
                if cpu_percent > HIGH_CPU_THRESHOLD:
                    alert_payload = {
                        "agent_uuid": AGENT_UUID,
                        "alert_type": "High CPU Usage",
                        "value": f"{cpu_percent:.1f}%",
                        "source": f"PID {p.info['pid']} ({process_data['command']})"
                    }
                    post_data_securely("/api/v1/alerts", payload=alert_payload, silent=True)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs

# ... (the rest of your client/cpu.py file remains the same) ...
# ... (collect_system_stats and monitor functions are unchanged) ...
def collect_system_stats() -> Dict:
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_times_percent(interval=0.5)
    try:
        load1, load5, load15 = psutil.getloadavg()
    except (OSError, AttributeError):
        load1, load5, load15 = (0, 0, 0)
    return {
        "mem_total": round(mem.total / (1024**2), 1), "mem_used": round(mem.used / (1024**2), 1),
        "mem_free": round(mem.free / (1024**2), 1), "mem_buff_cache": round((mem.buffers + mem.cached) / (1024**2), 1),
        "mem_available": round(mem.available / (1024**2), 1),
        "cpu_user": cpu.user, "cpu_system": cpu.system, "cpu_idle": cpu.idle,
        "load1": round(load1, 2), "load5": round(load5, 2), "load15": round(load15, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def monitor():
    print("Initializing CPU monitor (please wait a second)...")
    psutil.cpu_percent(interval=1)
    print("CPU monitor started.")
    
    while True:
        try:
            processes_batch = collect_processes()
            system_stats_data = collect_system_stats()
            if processes_batch:
                post_data_securely("/api/v1/cpu_processes", payload=processes_batch, silent=True)
            post_data_securely("/api/v1/system_stats", payload=system_stats_data, silent=True)
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRITICAL Error in CPU monitoring cycle: {e}")
        time.sleep(3)

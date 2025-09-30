# client/cpu.py
import time
import psutil
import os
from datetime import datetime
from utils import MY_IP, post_data_securely
from typing import List, Dict

STATE_MAP = {
    'R': 'Running', 'S': 'Sleeping', 'D': 'Waiting (Uninterruptible)',
    'Z': 'Zombie', 'T': 'Stopped', 'X': 'Dead', 'I': 'Idle', 'W': 'Paging'
}

def collect_processes() -> List[Dict]:
    procs = []
    psutil.cpu_percent(interval=1.0, percpu=True)
    for p in psutil.process_iter(['pid', 'ppid', 'username', 'memory_percent', 'cmdline', 'nice', 'status', 'create_time']):
        try:
            if not p.info['cmdline']:
                continue
            with p.oneshot():
                mem_info = p.memory_info()
                data = {
                    "pid": p.info['pid'], "ppid": p.info['ppid'],
                    "username": p.info['username'] or "unknown",
                    "cpu_percent": round(p.cpu_percent(interval=None), 1),
                    "mem_percent": round(p.info['memory_percent'], 1),
                    "command": " ".join(p.info['cmdline'])[:200],
                    "time_used": str(datetime.now() - datetime.fromtimestamp(p.info['create_time'])).split('.')[0],
                    "virt": mem_info.vms // 1024, "res": mem_info.rss // 1024,
                    "shr": getattr(mem_info, 'shared', 0) // 1024,
                    "priority": p.info['nice'], "nice": p.info['nice'],
                    "state": STATE_MAP.get(p.info['status'][0].upper(), p.info['status']),
                    "from_ip": MY_IP,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                procs.append(data)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs

def collect_system_stats() -> Dict:
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_times_percent(interval=1.0)
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1, load5, load15 = (0, 0, 0)
    return {
        "mem_total": round(mem.total / 1024 / 1024, 1),
        "mem_used": round(mem.used / 1024 / 1024, 1),
        "mem_free": round(mem.free / 1024 / 1024, 1),
        "mem_buff_cache": round((mem.buffers + mem.cached) / 1024 / 1024, 1),
        "mem_available": round(mem.available / 1024 / 1024, 1),
        "cpu_user": cpu.user, "cpu_system": cpu.system, "cpu_idle": cpu.idle,
        "load1": round(load1, 2), "load5": round(load5, 2), "load15": round(load15, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def monitor():
    while True:
        try:
            processes_batch = collect_processes()
            system_stats = collect_system_stats()
            if processes_batch:
                post_data_securely("/api/v1/cpu_processes", payload=processes_batch)
            post_data_securely("/api/v1/system_stats", payload=system_stats)
        except Exception as e:
            print(f"[{datetime.now()}] Error in CPU monitoring cycle: {e}")
        time.sleep(30)

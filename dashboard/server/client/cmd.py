# client/cmd.py (final version with active TTY detection)

import os, json, time, subprocess, requests
from datetime import datetime
from utils import SERVER_URL, append_log, CERT_PATH

SESSION_MAP_PATH = "session_map.json"
HISTORY_CACHE_PATH = "history_cache.json"
HISTORY_CACHE = {}

def load_session_map():
    try:
        with open(SESSION_MAP_PATH) as f:
            return json.load(f)
    except:
        return {}

def load_history_cache():
    global HISTORY_CACHE
    try:
        with open(HISTORY_CACHE_PATH) as f:
            HISTORY_CACHE = json.load(f)
    except:
        HISTORY_CACHE = {}

def save_history_cache():
    try:
        with open(HISTORY_CACHE_PATH, "w") as f:
            json.dump(HISTORY_CACHE, f)
    except Exception as e:
        print(f"[CMD] Failed to save history cache: {e}")

def flush_user_history(user):
    shell = f"su - {user} -c 'history -a'" if user != "root" else "history -a"
    try:
        subprocess.run(shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def get_idle_seconds(idle_str):
    try:
        if idle_str.endswith("s"):
            return int(float(idle_str.strip("s")))
        elif ":" in idle_str:
            parts = idle_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        elif "m" in idle_str:
            return int(float(idle_str.strip("m"))) * 60
        elif "h" in idle_str:
            return int(float(idle_str.strip("h"))) * 3600
        return 0
    except:
        return 99999

def monitor_command_history():
    load_history_cache()

    while True:
        try:
            session_map = load_session_map()

            for user in session_map:
                hist_file = f"/home/{user}/.bash_history" if user != "root" else "/root/.bash_history"
                if not os.path.exists(hist_file):
                    continue

                flush_user_history(user)

                stat = os.stat(hist_file)
                key = f"{user}:{hist_file}"
                prev = HISTORY_CACHE.get(key, {"inode": None, "size": 0, "offset": 0})

                if prev["inode"] != stat.st_ino or stat.st_size < prev["size"]:
                    print(f"[CMD] Reset history for {user}")
                    prev = {"inode": stat.st_ino, "size": 0, "offset": 0}

                with open(hist_file) as f:
                    f.seek(prev["offset"])
                    new_cmds = [line.strip() for line in f.readlines() if line.strip()]
                    new_offset = f.tell()

                # Pick the session with lowest idle time for accuracy
                user_sessions = session_map.get(user, {})
                session_to_use = None
                min_idle = float('inf')

                for tty, sid in user_sessions.items():
                    if sid.count("-") < 2:
                        continue
                    ip = sid.rsplit("-", 1)[-1]
                    if ip == "-" or ip.startswith("127.") or ip == "localhost":
                        continue
                    try:
                        output = subprocess.check_output(f"w -h | grep {tty}", shell=True, text=True).strip()
                        idle_str = output.split()[4] if len(output.split()) >= 5 else "9999"
                        idle_sec = get_idle_seconds(idle_str)
                        if idle_sec < min_idle:
                            min_idle = idle_sec
                            session_to_use = (sid, ip)
                    except:
                        continue

                if not session_to_use:
                    continue

                session_id, ip = session_to_use

                for cmd in new_cmds:
                    payload = {
                        "username": user,
                        "from_ip": ip,
                        "commands": cmd,
                        "session_id": session_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    try:
                        requests.post(f"{SERVER_URL}/api/v1/command_history", json=payload, verify=CERT_PATH)
                        append_log("command_log.jsonl", payload)
                        print(f"[CMD] Sent: {cmd} from {ip} ({session_id.split('-')[1]})")
                    except Exception as e:
                        print(f"[CMD] POST error: {e}")

                HISTORY_CACHE[key] = {
                    "inode": stat.st_ino,
                    "size": stat.st_size,
                    "offset": new_offset
                }

            save_history_cache()
        except Exception as e:
            print(f"[CMD] Error: {e}")
        time.sleep(10)

# Entry point
if __name__ == "__main__":
    monitor_command_history()

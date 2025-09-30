

# client/cmd.py (auto per-TTY .bash_history logic)

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
    try:
        shell = f"su - {user} -c 'history -a'" if user != "root" else "history -a"
        subprocess.run(shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def monitor_command_history():
    load_history_cache()

    while True:
        try:
            session_map = load_session_map()

            for user, ttys in session_map.items():
                flush_user_history(user)

                for tty, session_id in ttys.items():
                    if "-" not in session_id:
                        continue
                    ip = session_id.split("-")[-1]

                    # Determine correct history file path
                    hist_file = f"/home/{user}/.bash_history.{tty}" if user != "root" else f"/root/.bash_history.{tty}"
                    if not os.path.exists(hist_file):
                        continue

                    try:
                        stat = os.stat(hist_file)
                        mtime = os.path.getmtime(hist_file)
                    except:
                        continue

                    key = f"{user}:{tty}:{hist_file}"
                    prev = HISTORY_CACHE.get(key, {"inode": None, "size": 0, "offset": 0, "mtime": None})

                    if prev.get("mtime") == mtime:
                        continue  # unchanged file

                    if prev["inode"] != stat.st_ino or stat.st_size < prev["size"]:
                        print(f"[CMD] Reset history for {user} on {tty}")
                        prev = {"inode": stat.st_ino, "size": 0, "offset": 0, "mtime": None}

                    with open(hist_file) as f:
                        f.seek(prev["offset"])
                        new_cmds = [line.strip() for line in f.readlines() if line.strip()]
                        new_offset = f.tell()

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
                            print(f"[CMD] Sent: {cmd} from {ip} ({tty})")
                        except Exception as e:
                            print(f"[CMD] POST error: {e}")

                    HISTORY_CACHE[key] = {
                        "inode": stat.st_ino,
                        "size": stat.st_size,
                        "offset": new_offset,
                        "mtime": mtime
                    }

            save_history_cache()
        except Exception as e:
            print(f"[CMD] Error: {e}")
        time.sleep(30)

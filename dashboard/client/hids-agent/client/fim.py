# client/fim.py
import os, pyinotify, json, pwd
from datetime import datetime
from utils import compute_checksum, append_log, post_data_securely

FIM_PATHS = ["/root", "/etc", "/home"]
EXCLUDE_EXT = (".json", ".jsonl", ".swp", ".tmp", ".log")
FIM_EXCLUDE = ["/proc", "/sys", "/run", "/dev", "/tmp"]
SESSION_MAP_PATH = "session_map.json"

def resolve_username_from_path(path):
    try:
        uid = os.stat(path).st_uid
        return pwd.getpwuid(uid).pw_name
    except Exception:
        return "unknown"

def resolve_ip_and_tty(user):
    try:
        with open(SESSION_MAP_PATH) as f:
            session_map = json.load(f)
        ttys = session_map.get(user, {})
        latest_tty = "?"
        latest_time = 0
        for tty, sess in ttys.items():
            hist = f"/root/.bash_history.{tty}" if user == "root" else f"/home/{user}/.bash_history.{tty}"
            if os.path.exists(hist):
                mtime = os.path.getmtime(hist)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_tty = tty
        ip = ttys.get(latest_tty, "-").split("-")[-1]
        return ip, latest_tty
    except:
        return "-", "?"

class FIMHandler(pyinotify.ProcessEvent):
    def process_default(self, event):
        path = event.pathname
        if ".bash_history" in path: return
        if path.endswith(EXCLUDE_EXT): return
        if any(path.startswith(e) for e in FIM_EXCLUDE): return
        
        is_delete = "DELETE" in event.maskname.upper()
        if not os.path.exists(path) and not is_delete:
            return
        
        change_type = event.maskname.lower().replace("in_", "")
        
        if not is_delete and os.path.exists(path):
            who = resolve_username_from_path(path)
        else:
            who = "unknown"
        
        from_ip, tty = resolve_ip_and_tty(who)
        checksum = "deleted" if is_delete else compute_checksum(path)

        payload = {
            "from_ip": from_ip, "tty": tty, "file_path": path, "checksum": checksum,
            "change_type": change_type, "username": who,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            post_data_securely("/api/v1/file_integrity", payload=payload)
            append_log("fim_log.jsonl", payload)
        except Exception as e:
            print(f"[FIM] Error processing event for {path}: {e}")

def start_fim_monitor():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE
    notifier = pyinotify.ThreadedNotifier(wm, FIMHandler())
    notifier.daemon = True
    notifier.start()
    for path in FIM_PATHS:
        for root, _, _ in os.walk(path):
            if any(root.startswith(e) for e in FIM_EXCLUDE): continue
            try:
                wm.add_watch(root, mask, rec=False, auto_add=True)
            except Exception as e:
                print(f"[FIM] Watch error on {root}: {e}")

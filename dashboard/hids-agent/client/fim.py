# client/fim.py
import os
import pyinotify
import json
import pwd
from datetime import datetime

# --- THIS IS THE CRITICAL FIX ---
# We must import AGENT_UUID so post_data_securely can create the required header.
from utils import compute_checksum, append_log, post_data_securely, AGENT_UUID

# Paths to monitor
FIM_PATHS = ["/root", "/etc", "/home"]
EXCLUDE_EXT = (".json", ".jsonl", ".swp", ".tmp", ".log")
FIM_EXCLUDE = ["/proc", "/sys", "/run", "/dev", "/tmp"]

# Session mapping file (built by session tracker)
SESSION_MAP_PATH = "session_map.json"


def resolve_username_from_path(path):
    """Try resolving username from file path ownership."""
    try:
        uid = os.stat(path).st_uid
        return pwd.getpwuid(uid).pw_name
    except Exception:
        try:
            parent = os.path.dirname(path)
            if parent and os.path.exists(parent):
                uid = os.stat(parent).st_uid
                return pwd.getpwuid(uid).pw_name
        except Exception:
            pass
        return "unknown"


def resolve_ip_and_tty(user):
    """Resolve last known IP and TTY for a given user using session_map.json."""
    try:
        with open(SESSION_MAP_PATH) as f:
            session_map = json.load(f)
        ttys = session_map.get(user, {})
        if not ttys:
            return "-", "?"

        latest_tty = "?"
        latest_time = 0
        for tty, sess in ttys.items():
            hist = (
                f"/root/.bash_history.{tty}"
                if user == "root"
                else f"/home/{user}/.bash_history.{tty}"
            )
            if os.path.exists(hist):
                mtime = os.path.getmtime(hist)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_tty = tty

        # Fallback: pick first tty if no .bash_history timestamps
        if latest_tty == "?" and ttys:
            latest_tty = list(ttys.keys())[0]

        ip = ttys.get(latest_tty, "-").split("-")[-1]
        return ip, latest_tty
    except Exception:
        return "-", "?"


class FIMHandler(pyinotify.ProcessEvent):
    """Handles filesystem events."""

    def process_default(self, event):
        path = event.pathname
        if ".bash_history" in path:
            return
        if path.endswith(EXCLUDE_EXT):
            return
        if any(path.startswith(e) for e in FIM_EXCLUDE):
            return

        is_delete = "DELETE" in event.maskname.upper()
        who = resolve_username_from_path(path)
        from_ip, tty = resolve_ip_and_tty(who)
        checksum = "deleted" if is_delete else compute_checksum(path)

        payload = {
            "from_ip": from_ip,
            "tty": tty,
            "file_path": path,
            "checksum": checksum,
            "change_type": event.maskname.lower().replace("in_", ""),
            "username": who,
            # MODIFIED: Use isoformat for consistency
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

        try:
            # This call will now work correctly because AGENT_UUID is imported
            post_data_securely("/api/v1/file_integrity", payload=payload)
            append_log("fim_log.jsonl", payload)
        except Exception as e:
            print(f"[FIM] Error processing event for {path}: {e}")


def start_fim_monitor():
    """Start pyinotify monitor for file integrity tracking."""
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE
    notifier = pyinotify.ThreadedNotifier(wm, FIMHandler())
    notifier.daemon = True
    notifier.start()
    print("[FIM] 🟢 File Integrity Monitor started.")

    for path in FIM_PATHS:
        for root, _, _ in os.walk(path):
            if any(root.startswith(e) for e in FIM_EXCLUDE):
                continue
            try:
                wm.add_watch(root, mask, rec=False, auto_add=True)
            except Exception as e:
                print(f"[FIM] Watch error on {root}: {e}")

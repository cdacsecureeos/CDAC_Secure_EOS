# client/fim.py

import os, pyinotify, requests, getpass, json
from datetime import datetime
from utils import SERVER_URL, compute_checksum, append_log, CERT_PATH

FIM_PATHS = ["/root", "/etc"]
EXCLUDE_EXT = (".json", ".jsonl", ".swp", ".tmp", ".log", ".bak")
FIM_EXCLUDE = ["/proc", "/sys", "/run", "/dev", "/tmp", "/root/.bash_history"]
SESSION_MAP_PATH = "session_map.json"

def get_from_ip(user):
    """Maps current user+TTY to remote IP from session_map.json"""
    try:
        tty = os.popen("tty").read().strip().replace("/dev/", "")
        with open(SESSION_MAP_PATH) as f:
            session_map = json.load(f)
        return session_map.get(user, {}).get(tty, "-").split("-")[-1]
    except Exception as e:
        print(f"[FIM] Could not get from_ip: {e}")
        return "-"

class FIMHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        self._handle_event(event, "create")

    def process_IN_MODIFY(self, event):
        self._handle_event(event, "modify")

    def process_IN_DELETE(self, event):
        self._handle_event(event, "delete")

    def _handle_event(self, event, change_type):
        path = event.pathname
        if path.endswith(EXCLUDE_EXT): return
        if any(path.startswith(e) for e in FIM_EXCLUDE): return

        who = getpass.getuser()
        from_ip = get_from_ip(who)

        if change_type == "delete":
            checksum = "deleted"
        else:
            if not os.path.isfile(path): return
            checksum = compute_checksum(path)
            if not checksum: return

        payload = {
            "file_path": path,
            "checksum": checksum,
            "change_type": change_type,
            "from_ip": from_ip,
            "who": who,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            requests.post(f"{SERVER_URL}/api/v1/file_integrity", json=payload, verify=CERT_PATH)
            append_log("fim_log.jsonl", payload)
            print(f"[FIM] {change_type.upper()}: {path} by {who} from {from_ip}")
        except Exception as e:
            print(f"[FIM] Error: {e}")

def start_fim_monitor():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE
    notifier = pyinotify.ThreadedNotifier(wm, FIMHandler())
    notifier.daemon = True
    notifier.start()

    for base in FIM_PATHS:
        for root, _, _ in os.walk(base):
            if any(root.startswith(e) for e in FIM_EXCLUDE): continue
            try:
                wm.add_watch(root, mask, rec=False, auto_add=True)
            except Exception as e:
                print(f"[FIM] Watch error: {e}")

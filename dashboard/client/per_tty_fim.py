# client/per_tty_fim.py

import os
import json

BASHRC_PATH = "/etc/bash.bashrc"
SESSION_MAP_PATH = "session_map.json"
AUTO_RUN_LINE = 'python3 /root/client/client/per_tty_fim.py 2>/dev/null'

def get_active_tty():
    return os.popen("tty").read().strip().replace("/dev/", "")

def get_current_user():
    return os.environ.get("USER") or os.getlogin() or "root"

def get_ip_from_who_or_ssh(tty):
    try:
        who_output = os.popen("who").read()
        for line in who_output.strip().splitlines():
            if tty in line:
                parts = line.split()
                if len(parts) >= 5:
                    return parts[4].strip("()")
    except:
        pass

    try:
        ssh_info = os.environ.get("SSH_CLIENT") or os.environ.get("SSH_CONNECTION")
        if ssh_info:
            return ssh_info.split()[0]
    except:
        pass

    return "-"

def update_session_map():
    try:
        tty = get_active_tty()
        user = get_current_user()
        ip = get_ip_from_who_or_ssh(tty)
        session_id = f"{user}-{tty}-{ip}"

        session_map = {}
        if os.path.exists(SESSION_MAP_PATH):
            with open(SESSION_MAP_PATH, "r") as f:
                session_map = json.load(f)

        if user not in session_map:
            session_map[user] = {}
        session_map[user][tty] = session_id

        with open(SESSION_MAP_PATH, "w") as f:
            json.dump(session_map, f, indent=4)
    except:
        pass  # Silent fail

def ensure_auto_injection_in_bashrc():
    try:
        with open(BASHRC_PATH, "r") as f:
            if AUTO_RUN_LINE not in f.read():
                with open(BASHRC_PATH, "a") as fa:
                    fa.write(f"\n# Auto-run per-TTY FIM mapping\n{AUTO_RUN_LINE}\n")
    except:
        pass  # Silent fail

if __name__ == "__main__":
    ensure_auto_injection_in_bashrc()
    update_session_map()

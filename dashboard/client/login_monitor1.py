# client/login_monitor.py

import os, subprocess, time, json
from datetime import datetime
from utils import SERVER_URL, MY_IP, append_log, CERT_PATH, HTTP_SESSION

SESSION_MAP_FILE = "session_map.json"
prev_sessions = {}

def save_session_map(data):
    try:
        with open(SESSION_MAP_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[LOGIN] Failed to save session map: {e}")

def get_tty_command_map():
    tty_cmd = {}
    try:
        ps_out = subprocess.check_output(
            "ps -eo tty,args --sort=start_time | grep -v '?' | grep -v 'ps -eo'",
            shell=True, text=True
        ).splitlines()
        for line in ps_out:
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                tty, cmd = parts
                tty_cmd[tty.replace('/dev/', '')] = cmd
    except Exception as e:
        print(f"[LOGIN] TTY map error: {e}")
    return tty_cmd

def monitor_logins():
    global prev_sessions

    while True:
        try:
            output = subprocess.check_output(["w", "-h"], text=True).splitlines()
            tty_cmd_map = get_tty_command_map()

            current_sessions = {}
            session_map = {}

            for line in output:
                parts = line.split(None, 7)
                if len(parts) < 8:
                    continue

                username, tty, from_ip, login_time, idle, jcpu, pcpu, _ = parts
                tty = tty.strip()
                from_ip = from_ip.strip()
                command = tty_cmd_map.get(tty, "-bash")
                session_id = f"{username}-{tty}-{from_ip}"

                is_new = session_id not in prev_sessions
                event_type = "login" if is_new else "active"

                session_data = {
                    "session_id": session_id,
                    "username": username,
                    "tty": tty,
                    "from_ip": from_ip,
                    "login_time": login_time,
                    "idle": idle,
                    "jcpu": jcpu,
                    "pcpu": pcpu,
                    "command": command.strip(),
                    "event": event_type,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                if is_new or event_type == "logout":
                    try:
                        HTTP_SESSION.post(f"{SERVER_URL}/api/v1/sessions", json=session_data, verify=CERT_PATH)
                    except Exception as e:
                        print(f"[LOGIN] POST error (login): {e}")
                    append_log("session_log.jsonl", session_data)

                current_sessions[session_id] = session_data
                session_map.setdefault(username, {})[tty] = session_id

            save_session_map(session_map)

            # Detect logout sessions
            for old_id in prev_sessions:
                if old_id not in current_sessions:
                    u, tty, ip = old_id.split("-", 2)
                    logout_data = {
                        "session_id": old_id,
                        "username": u,
                        "tty": tty,
                        "from_ip": ip,
                        "login_time": "-", "idle": "-", "jcpu": "-", "pcpu": "-",
                        "command": "-",
                        "event": "logout",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    try:
                        HTTP_SESSION.post(f"{SERVER_URL}/api/v1/sessions", json=logout_data, verify=CERT_PATH)
                    except Exception as e:
                        print(f"[LOGIN] POST error (logout): {e}")
                    append_log("session_log.jsonl", logout_data)

            prev_sessions = current_sessions
            print("[LOGIN] Sessions updated")

        except Exception as e:
            print(f"[LOGIN] Error: {e}")

        time.sleep(15)

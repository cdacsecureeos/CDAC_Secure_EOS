# client/login_monitor.py

import os
import subprocess
import time
import json
from datetime import datetime
from utils import SERVER_URL, CERT_PATH, HTTP_SESSION, append_log

SESSION_MAP_FILE = "session_map.json"
prev_sessions = {}

def save_session_map(data):
    try:
        with open(SESSION_MAP_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass  # Silent fail

def get_tty_command_map():
    tty_cmd = {}
    try:
        output = subprocess.check_output(
            "ps -eo tty,args --sort=start_time | grep -v '?' | grep -v 'ps -eo'",
            shell=True, text=True
        ).splitlines()
        for line in output:
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                tty, cmd = parts
                tty_cmd[tty.replace("/dev/", "")] = cmd
    except:
        pass  # Silent fail
    return tty_cmd

def monitor_logins():
    global prev_sessions

    while True:
        try:
            # Get current active sessions via `w -h`
            raw_sessions = subprocess.check_output(["w", "-h"], text=True).splitlines()
            tty_cmd_map = get_tty_command_map()

            current_sessions = {}
            session_map = {}
            new_events = []

            for line in raw_sessions:
                parts = line.split(None, 7)
                if len(parts) < 8:
                    continue

                username, tty, from_ip, login_time, idle, jcpu, pcpu, _ = parts
                tty = tty.strip()
                from_ip = from_ip.strip()
                command = tty_cmd_map.get(tty, "-bash")
                session_id = f"{username}-{tty}-{from_ip}"

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
                    "event": "login" if session_id not in prev_sessions else "active",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                if session_id not in prev_sessions:
                    new_events.append(session_data)

                current_sessions[session_id] = session_data
                session_map.setdefault(username, {})[tty] = session_id

            # Detect logout events
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
                    new_events.append(logout_data)

            # Only send actual new events (login/logout)
            for event in new_events:
                try:
                    HTTP_SESSION.post(f"{SERVER_URL}/api/v1/sessions", json=event, verify=CERT_PATH)
                except:
                    pass  # Silent fail
                append_log("session_log.jsonl", event)

            save_session_map(session_map)
            prev_sessions = current_sessions

        except Exception:
            pass  # Silent fail

        time.sleep(15)

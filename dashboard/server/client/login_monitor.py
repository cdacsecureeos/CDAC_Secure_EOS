# client/login.py

import os
import subprocess
import requests
import time
import json
from datetime import datetime
from utils import SERVER_URL, MY_IP, append_log, CERT_PATH

prev_sessions = {}
SESSION_MAP_FILE = "session_map.json"

def save_session_map(data):
    try:
        with open(SESSION_MAP_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[LOGIN] Failed to save session map: {e}")

def get_tty_command_map():
    tty_cmd = {}
    try:
        # Get command per TTY from oldest to newest (most likely interactive sessions)
        ps_out = subprocess.check_output(
            "ps -eo tty,args --sort=start_time | grep -v '?' | grep -v 'ps -eo'",
            shell=True, text=True
        ).splitlines()

        for line in ps_out:
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                tty, cmd = parts
                tty = tty.replace('/dev/', '')  # normalize
                tty_cmd[tty] = cmd
    except Exception as e:
        print(f"[LOGIN] Error getting TTY commands: {e}")
    return tty_cmd

def monitor_logins():
    global prev_sessions
    while True:
        try:
            output = subprocess.check_output(["w", "-h"], text=True).splitlines()
            current_sessions = {}
            session_map = {}

            tty_cmd_map = get_tty_command_map()

            for line in output:
                parts = line.split(None, 7)  # max 8 fields
                if len(parts) < 8:
                    continue

                username, tty, from_ip, login_time, idle, jcpu, pcpu, _ = parts
                command = tty_cmd_map.get(tty, "-bash")  # fallback to bash if unknown
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

                # Send to server and log locally
                try:
                    requests.post(f"{SERVER_URL}/api/v1/sessions", json=session_data, verify=CERT_PATH)
                except Exception as e:
                    print(f"[LOGIN] POST error: {e}")

                append_log("session_log.jsonl", session_data)
                current_sessions[session_id] = session_data

                if username not in session_map:
                    session_map[username] = {}
                session_map[username][tty] = session_id

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
                        "event": "logout",
                        "login_time": "-", "idle": "-",
                        "jcpu": "-", "pcpu": "-", "command": "-",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    try:
                        requests.post(f"{SERVER_URL}/api/v1/sessions", json=logout_data,verify=CERT_PATH)
                    except Exception as e:
                        print(f"[LOGIN] POST error: {e}")

                    append_log("session_log.jsonl", logout_data)

            prev_sessions = current_sessions
            print("[LOGIN] Sessions updated")
        except Exception as e:
            print(f"[LOGIN] Error: {e}")
        time.sleep(10)

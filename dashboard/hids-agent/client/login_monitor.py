# client/login_monitor.py (FINAL, RESILIENT VERSION)
import os
import subprocess
import time
import json
import re
from datetime import datetime, timezone
from utils import append_log, post_data_securely

PREV_SESSIONS_FILE = "previous_sessions.json"
SESSION_MAP_FILE = "session_map.json"
IP_MAP_FILE = "ip_map.json"

IP_REGEX = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

def load_from_json(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_to_json(filepath, data):
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[SESH] Critical error saving to {filepath}: {e}")

def get_current_sessions():
    """
    This function now returns a success flag. If the 'w' command fails or gives
    unexpected output, it returns success=False.
    """
    sessions = {}
    session_map = {}
    ip_map = load_from_json(IP_MAP_FILE)
    
    try:
        w_output = subprocess.check_output(["w", "-h"], text=True, stderr=subprocess.DEVNULL, timeout=5)
        
        # If w_output is empty, treat it as a transient error
        if not w_output.strip():
            print("[SESH] Warning: 'w -h' returned empty output. Assuming transient error.")
            return {}, {}, False

        # First pass: update our master IP map with any real IPs found
        for line in w_output.strip().splitlines():
            parts = line.split(maxsplit=7)
            if len(parts) < 8: continue
            username, _, from_ip, _, _, _, _, _ = parts
            if IP_REGEX.match(from_ip):
                ip_map[username] = from_ip
        
        # Second pass: build the session dictionary using the enriched IP map
        for line in w_output.strip().splitlines():
            parts = line.split(maxsplit=7)
            if len(parts) < 8: continue
            username, tty, from_ip, login_time, idle, jcpu, pcpu, command = parts
            
            enriched_ip = from_ip
            if not IP_REGEX.match(from_ip):
                enriched_ip = ip_map.get(username, '-')
            
            db_session_id = f"{username}-{tty}-{enriched_ip}"
            internal_key = f"{username}-{tty}"

            sessions[internal_key] = {
                "session_id": db_session_id,
                "username": username,
                "tty": tty,
                "from_ip": enriched_ip,
                "login_time": login_time,
                "idle": idle,
                "jcpu": jcpu,
                "pcpu": pcpu,
                "command": command.strip(),
            }
            session_map.setdefault(username, {})[tty] = db_session_id

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"[SESH] Error executing 'w -h': {e}. Skipping this cycle.")
        return {}, {}, False # ✅ FIX: Return failure
    except Exception as e:
        print(f"[SESH] Error parsing 'w' command output: {e}")
        return {}, {}, False # ✅ FIX: Return failure
    
    save_to_json(IP_MAP_FILE, ip_map)
    return sessions, session_map, True # ✅ FIX: Return success

def monitor_logins():
    prev_sessions = load_from_json(PREV_SESSIONS_FILE)
    print(f"[SESH] 🟢 Session monitor started. Loaded {len(prev_sessions)} previous session(s).")

    while True:
        try:
            # ✅ FIX: Check the success flag returned from the function
            current_sessions, session_map, was_successful = get_current_sessions()

            # If the command failed, do not update state. Just wait for the next cycle.
            # This prevents the "mass logout illusion".
            if not was_successful:
                time.sleep(15)
                continue

            current_keys = set(current_sessions.keys())
            prev_keys = set(prev_sessions.keys())

            logins = current_keys - prev_keys
            logouts = prev_keys - current_keys
            
            new_events = []
            if logins:
                for key in logins:
                    event_data = current_sessions[key].copy()
                    event_data["event_type"] = "login"
                    event_data["timestamp"] = datetime.now(timezone.utc).isoformat()
                    new_events.append(event_data)
                    print(f"[SESH] New LOGIN for TTY {key} (ID: {event_data['session_id']})")

            if logouts:
                for key in logouts:
                    event_data = prev_sessions[key].copy()
                    event_data["event_type"] = "logout"
                    event_data["timestamp"] = datetime.now(timezone.utc).isoformat()
                    new_events.append(event_data)
                    print(f"[SESH] New LOGOUT for TTY {key} (ID: {event_data['session_id']})")

            if new_events:
                for event in new_events:
                    post_data_securely("/api/v1/sessions", payload=event, silent=False)
                append_log("session_log.jsonl", json.dumps(new_events))
            
            # CRITICAL: Only update the previous state if the data fetch was successful
            prev_sessions = current_sessions
            save_to_json(PREV_SESSIONS_FILE, current_sessions)
            save_to_json(SESSION_MAP_FILE, session_map)
            
        except Exception as e:
            print(f"[SESH] ❌ Error in main monitoring loop: {e}")
            
        time.sleep(15)

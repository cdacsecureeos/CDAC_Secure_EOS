# client/brute_force.py (FINAL VERSION with CORRECTED PARSING)
import os
import time
import json
from datetime import datetime, timedelta, timezone
from systemd import journal
from utils import append_log, post_data_securely, AGENT_UUID

CURSOR_FILE = "journal_cursor.json"
SEC_LOG = "security_log.jsonl"

def get_journal_events():
    """
    (CORRECTED) Queries the systemd journal and correctly parses sshd log messages.
    """
    try:
        j = journal.Reader()
        j.this_boot()
        j.log_level(journal.LOG_INFO)
        j.add_match(SYSLOG_IDENTIFIER="sshd")

        if os.path.exists(CURSOR_FILE):
            try:
                with open(CURSOR_FILE) as f:
                    cursor = json.load(f).get("cursor")
                    if cursor:
                        j.seek_cursor(cursor)
                        j.get_next() 
            except Exception:
                j.seek_realtime(datetime.now(timezone.utc) - timedelta(minutes=5))
        else:
            j.seek_realtime(datetime.now(timezone.utc) - timedelta(minutes=5))

        events = []
        brute_force_counter = {}
        last_cursor = None

        for entry in j:
            message = entry.get('MESSAGE', '')
            ts_utc = entry['__REALTIME_TIMESTAMP']
            ts_iso = ts_utc.replace(tzinfo=timezone.utc).isoformat()

            ip, user = None, None
            if "Accepted password for" in message:
                parts = message.split()
                try:
                    # --- THIS IS THE CRITICAL PARSING FIX ---
                    user = parts[3] # Correct index for username
                    ip = parts[5]   # Correct index for IP address
                    event_type = "successful_login"
                    description = f"Successful login for '{user}' from {ip}"
                except IndexError:
                    continue
            elif "Failed password for" in message:
                parts = message.split()
                try:
                    # --- AND THE FIX FOR FAILED LOGINS ---
                    user_index = 5 if parts[4] != "invalid" else 6
                    user = parts[user_index]
                    ip = parts[user_index + 2]
                    event_type = "failed_login"
                    description = f"Failed login for '{user}' from {ip}"
                    brute_force_counter.setdefault(ip, []).append(ts_utc)
                except IndexError:
                    continue
            else:
                continue

            events.append({
                "username": user, "source_ip": ip, "event_type": event_type,
                "description": description, "timestamp": ts_iso
            })
            last_cursor = entry['__CURSOR']

        for ip, timestamps in brute_force_counter.items():
            recent_failures = [t for t in timestamps if (datetime.now(timezone.utc) - t) < timedelta(minutes=2)]
            if len(recent_failures) >= 5:
                events.append({
                    "event_type": "brute_force_detected", "username": "-", "source_ip": ip,
                    "description": f"Brute force: {len(recent_failures)} failed logins from {ip}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        if events:
            for ev in events:
                post_data_securely("/api/v1/security_logs", payload=ev)
                append_log(SEC_LOG, ev)

        if last_cursor:
            with open(CURSOR_FILE, "w") as f:
                json.dump({"cursor": last_cursor}, f)
    except Exception as e:
        print(f"[SEC] CRITICAL ERROR processing journal: {e}")

def monitor_security():
    print("[SEC] 🟢 SSH security monitor started (using systemd journal).")
    while True:
        get_journal_events()
        time.sleep(30)

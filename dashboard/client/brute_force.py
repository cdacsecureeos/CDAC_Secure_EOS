# client/brute_force.py

import os, time, json, re, requests
from datetime import datetime, timedelta
from utils import append_log, SERVER_URL, CERT_PATH

AUTH_LOG = "/var/log/auth.log"
OFFSET_FILE = "auth_log_offset.json"
SEC_LOG = "security_log.jsonl"

def parse_auth_log():
    offset = 0
    if os.path.exists(OFFSET_FILE):
        try:
            offset = json.load(open(OFFSET_FILE)).get("offset", 0)
        except:
            offset = 0

    events = []
    brute_force_counter = {}

    try:
        log_size = os.path.getsize(AUTH_LOG)
        if offset > log_size:
            print("[SEC] Offset reset due to log rotation.")
            offset = 0

        with open(AUTH_LOG, "r") as f:
            f.seek(offset)
            lines = f.readlines()
            offset = f.tell()

        for line in lines:
            raw = line.strip()

            # Debian log timestamp: e.g., "Jul 31 11:12:23"
            ts_match = re.match(r"^(\w{3})\s+(\d{1,2})\s([\d:]{8})", raw)
            if ts_match:
                month_str, day, time_str = ts_match.groups()
                try:
                    ts_str = f"{month_str} {day} {time_str} {datetime.now().year}"
                    ts = datetime.strptime(ts_str, "%b %d %H:%M:%S %Y")
                except:
                    ts = datetime.now()
            else:
                ts = datetime.now()

            # Failed login
            if "Failed password" in raw:
                ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", raw)
                user_match = re.search(r"for (invalid user )?(\w+)", raw)

                if ip_match and user_match:
                    ip = ip_match.group(1)
                    user = user_match.group(2)

                    ev = {
                        "event_type": "failed_login",
                        "username": user,
                        "source_ip": ip,
                        "description": f"❌ Failed login attempt for '{user}' from {ip}",
                        "timestamp": ts.isoformat(),
                        #"tty": "-"
                    }
                    events.append(ev)
                    brute_force_counter.setdefault(ip, []).append(ts)

            # Successful login
            elif "Accepted password" in raw:
                ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", raw)
                user_match = re.search(r"for (\w+)", raw)
                tty_match = re.search(r"tty(\w+)", raw)

                if ip_match and user_match:
                    ip = ip_match.group(1)
                    user = user_match.group(1)

                    ev = {
                        "event_type": "successful_login",
                        "username": user,
                        "source_ip": ip,
                        "description": f"✅ Successful login for '{user}' from {ip}",
                        "timestamp": ts.isoformat(),
                        #"tty": tty_match.group(1) if tty_match else "-"
                    }
                    events.append(ev)

            # Session closed/disconnect
            elif "session closed" in raw.lower() or "disconnected" in raw.lower():
                ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", raw)
                user_match = re.search(r"session closed for user (\w+)", raw)

                if ip_match and user_match:
                    ip = ip_match.group(1)
                    user = user_match.group(1)

                    ev = {
                        "event_type": "logout",
                        "username": user,
                        "source_ip": ip,
                        "description": f"🔚 Logout for '{user}' from {ip}",
                        "timestamp": ts.isoformat(),
                        #"tty": "-"
                    }
                    events.append(ev)

        # Brute-force detection
        for ip, timestamps in brute_force_counter.items():
            recent = [t for t in timestamps if (datetime.now() - t) < timedelta(minutes=2)]
            if len(recent) >= 5:
                ev = {
                    "event_type": "brute_force_detected",
                    "username": "-",
                    "source_ip": ip,
                    "description": f"🚨 Brute force: {len(recent)} failed logins from {ip}",
                    "timestamp": datetime.now().isoformat(),
                    #"tty": "-"
                }
                events.append(ev)

        # Send and persist events
        for ev in events:
            try:
                requests.post(f"{SERVER_URL}/api/v1/security_logs", json=ev, verify=CERT_PATH)
                append_log(SEC_LOG, ev)
                print(f"[SEC] ✅ Sent {ev['event_type']} from {ev['source_ip']}")
            except Exception as e:
                print(f"[SEC] ❌ Send failed: {e}")

        with open(OFFSET_FILE, "w") as f:
            json.dump({"offset": offset}, f)

    except Exception as e:
        print(f"[SEC] ❌ Error: {e}")

def monitor_security():
    print("[SEC] 🟢 SSH security monitor started.")
    while True:
        parse_auth_log()
        time.sleep(30)

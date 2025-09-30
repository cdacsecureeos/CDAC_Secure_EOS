# client/brute_force.py
import os, time, json, re
from datetime import datetime, timedelta
from utils import append_log, post_data_securely

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
            offset = 0
        with open(AUTH_LOG, "r") as f:
            f.seek(offset)
            lines = f.readlines()
            offset = f.tell()
        for line in lines:
            raw = line.strip()
            ts_match = re.match(r"^(\w{3})\s+(\d{1,2})\s([\d:]{8})", raw)
            ts = datetime.now()
            if ts_match:
                try:
                    ts_str = f"{ts_match.group(1)} {ts_match.group(2)} {ts_match.group(3)} {datetime.now().year}"
                    ts = datetime.strptime(ts_str, "%b %d %H:%M:%S %Y")
                except: pass
            
            # Simplified parsing logic
            ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", raw)
            user_match = re.search(r"for (?:invalid user )?(\S+)", raw)
            if not ip_match or not user_match: continue
            ip = ip_match.group(1)
            user = user_match.group(1)

            ev = {"username": user, "source_ip": ip, "timestamp": ts.isoformat()}
            if "Failed password" in raw:
                ev["event_type"] = "failed_login"
                ev["description"] = f"Failed login for '{user}' from {ip}"
                brute_force_counter.setdefault(ip, []).append(ts)
            elif "Accepted password" in raw:
                ev["event_type"] = "successful_login"
                ev["description"] = f"Successful login for '{user}' from {ip}"
            else:
                continue
            events.append(ev)
        
        for ip, timestamps in brute_force_counter.items():
            recent = [t for t in timestamps if (datetime.now() - t) < timedelta(minutes=2)]
            if len(recent) >= 5:
                events.append({
                    "event_type": "brute_force_detected", "username": "-", "source_ip": ip,
                    "description": f"Brute force: {len(recent)} failed logins from {ip}",
                    "timestamp": datetime.now().isoformat()
                })
        for ev in events:
            post_data_securely("/api/v1/security_logs", payload=ev)
            append_log(SEC_LOG, ev)
        with open(OFFSET_FILE, "w") as f:
            json.dump({"offset": offset}, f)
    except Exception as e:
        print(f"[SEC] Error: {e}")

def monitor_security():
    print("[SEC] 🟢 SSH security monitor started.")
    while True:
        parse_auth_log()
        time.sleep(30)

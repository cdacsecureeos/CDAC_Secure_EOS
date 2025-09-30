# client/enroll_agent.py
import requests
import json
import os
import socket
import sys

# --- Configuration ---
# You should move these to a central config file later
SERVER_URL = "https://10.182.0.73:8443"
CERT_PATH = "/root/hids-agent/client/cert.pem"  # IMPORTANT: Use the correct path to your server's cert
CONFIG_DIR = "/etc/hids-agent"
CONFIG_PATH = os.path.join(CONFIG_DIR, "agent.json")

def get_local_ip():
    # Helper to get the primary IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def enroll():
    print("Attempting to enroll agent...")

    if os.path.exists(CONFIG_PATH):
        print(f"Error: Agent configuration already exists at {CONFIG_PATH}.")
        print("If you want to re-enroll, please remove this file first.")
        sys.exit(1)

    hostname = socket.gethostname()
    ip_address = get_local_ip()
    os_name = os.uname().sysname 
    payload = {"hostname": hostname, "ip_address": ip_address, "os_name": os_name }

    try:
        print(f"Sending enrollment request for '{hostname}' to {SERVER_URL}...")
        response = requests.post(
            f"{SERVER_URL}/api/v1/agents/enroll",
            json=payload,
            verify=CERT_PATH,  # Enforces TLS
            timeout=15
        )
        response.raise_for_status()
        config = response.json()

        # Create the config directory securely
        os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
        
        # Write the credentials to the config file
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        
        # IMPORTANT: Set file permissions so only root can read it
        os.chmod(CONFIG_PATH, 0o600)
        
        print("-" * 50)
        print("✅ Agent enrolled successfully!")
        print(f"   UUID: {config['agent_uuid']}")
        print(f"   Config saved to: {CONFIG_PATH}")
        print("-" * 50)

    except requests.exceptions.RequestException as e:
        print("\n" + "="*50)
        print("❌ Enrollment failed.")
        print(f"   Error: {e}")
        print("   Please check:")
        print(f"   1. Is the server running at {SERVER_URL}?")
        print(f"   2. Is the server certificate path correct? (CERT_PATH: {CERT_PATH})")
        print("   3. Is there a firewall blocking the connection?")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root to write the configuration to /etc.")
        sys.exit(1)
    enroll()

# client/main.py

import os
import time
from threading import Thread
from cpu import monitor_cpu
from fim import start_fim_monitor
from login_monitor import monitor_logins
from cmd import monitor_command_history
from per_tty_history import ensure_per_tty_history_enabled, ensure_bash_history_dirs
from brute_force import monitor_security
#from cve_scanner import scan_cve
#Thread(target=monitor_cves, daemon=True).start()

if __name__ == "__main__":
    ensure_per_tty_history_enabled()
    ensure_bash_history_dirs()

    os.nice(10)  # Lower CPU priority on embedded systems

    Thread(target=monitor_cpu, daemon=True).start()
    Thread(target=start_fim_monitor, daemon=True).start()
    Thread(target=monitor_logins, daemon=True).start()
    Thread(target=monitor_command_history, daemon=True).start()
    Thread(target=monitor_security, daemon=True).start()
 #   Thread(target=scan_cve, daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping agent...")

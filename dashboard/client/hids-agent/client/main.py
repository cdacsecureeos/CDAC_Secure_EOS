# client/main.py

import os
import time
from threading import Thread
from fim import start_fim_monitor
from login_monitor import monitor_logins
from cmd import monitor_command_history
from per_tty_history import ensure_per_tty_history_enabled
from brute_force import monitor_security
from cpu import monitor

def main():
    ensure_per_tty_history_enabled()
    os.nice(10)

    # Start monitoring threads
    Thread(target=monitor, daemon=True).start()
    Thread(target=start_fim_monitor, daemon=True).start()
    Thread(target=monitor_logins, daemon=True).start()
    Thread(target=monitor_command_history, daemon=True).start()
    Thread(target=monitor_security, daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("🔌 Stopping client agent...")

if __name__ == "__main__":
    main()

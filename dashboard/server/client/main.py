# client/main.py
from threading import Thread
from cpu import monitor_cpu
from fim import start_fim_monitor
from login_monitor import monitor_logins
from cmd import monitor_command_history
import time

if __name__ == "__main__":
    Thread(target=monitor_cpu, daemon=True).start()
    Thread(target=start_fim_monitor, daemon=True).start()
    Thread(target=monitor_logins, daemon=True).start()
    Thread(target=monitor_command_history, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping agent...")

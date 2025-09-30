# spike.py
import multiprocessing
import time
import math

def cpu_worker():
    """Busy loop with short sleep to target ~70% CPU."""
    while True:
        # Burn CPU
        for _ in range(10_000_000):
            math.sqrt(12345)  # arbitrary math operation
        # Small sleep to reduce load (tune this for ~70%)
        time.sleep(0.03)

if __name__ == "__main__":
    num_workers = max(1, multiprocessing.cpu_count() - 1)  # leave 1 core free
    print(f"Starting {num_workers} CPU workers...")
    workers = []
    for _ in range(num_workers):
        p = multiprocessing.Process(target=cpu_worker)
        p.start()
        workers.append(p)

    try:
        for p in workers:
            p.join()
    except KeyboardInterrupt:
        print("Stopping workers...")
        for p in workers:
            p.terminate()

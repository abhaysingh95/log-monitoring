import subprocess
import os
import signal
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(BASE_DIR, "generators")

processes = []

def shutdown(signum, frame):
    print("\n🛑 Stopping all log generators...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    print("✅ All generators stopped cleanly.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

print("🚀 Starting all log generators...\n")

scripts = sorted([
    f for f in os.listdir(GEN_DIR)
    if f.endswith(".py")
])

if not scripts:
    print("❌ No generator scripts found.")
    sys.exit(1)

for script in scripts:
    script_path = os.path.join(GEN_DIR, script)
    print(f"▶ Starting {script}")

    p = subprocess.Popen(
        ["python3", script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    processes.append(p)

    # slight stagger – looks more real, avoids burst
    time.sleep(0.4)

print("\n✅ All log generators are running.")
print("ℹ️  Press CTRL+C to stop all generators.\n")

while True:
    time.sleep(1)

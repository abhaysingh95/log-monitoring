import random
import json
import uuid
import time
import os
from datetime import datetime

LOG_FILE = "logs/mta-txn-valid-gl.log"
CLASS = "org.fin.acc.ser.ValidateGlStatusImpl"
THREADS = [f"executor-thread-{i}" for i in range(180, 260)]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def log(level, thread, exch, msg):
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{ts()} {level:<5} [{CLASS}] ({thread}) exchangeId : '{exch}' - {msg}\n"
        )

def exchange_id():
    return str(uuid.uuid4())

def gl_number(valid=True):
    if valid:
        return str(random.randint(3233000100, 3233000199))
    return str(random.randint(3233000500, 3233000999))

# ---------------- SUCCESS FLOW ----------------
def run_success(ex, th):
    gl = gl_number(True)

    log("INFO", th, ex,
        f"Validating Gl Account for LegId : 0,AccountNo : {gl}")

    log("INFO", th, ex,
        f"Gl Account Received : {gl}")

    success = {
        "returnCode": "0",
        "responseCode": "0",
        "responseMessage": "SUCCESS",
        "data": {
            "glNumber": gl,
            "glType": "Liability",
            "isActive": "TRUE",
            "includeInSettlement": "TRUE"
        }
    }

    log("INFO", th, ex,
        f"Response received From Ldap : {json.dumps(success)}")

    log("INFO", th, ex,
        f"GL Account {gl} passed restriction Check")

# ---------------- FAILURE FLOW ----------------
def run_failure(ex, th):
    gl = gl_number(False)

    log("INFO", th, ex,
        f"Validating Gl Account for LegId : 0,AccountNo : {gl}")

    log("INFO", th, ex,
        f"Gl Account Received : {gl}")

    error = {
        "returnCode": "1",
        "responseCode": "19",
        "responseMessage": "Provide a valid GLNumber."
    }

    log("INFO", th, ex,
        f"Response received From Ldap : {json.dumps(error)}")

    log("ERROR", th, ex,
        "Failed with message GL Account Not Found")

# ---------------- MAIN LOOP ----------------
def run():
    os.makedirs("logs", exist_ok=True)

    while True:
        th = random.choice(THREADS)
        ex = exchange_id()

        # 🔑 SINGLE DECISION POINT (same as walking-status)
        is_success = random.random() < 0.98

        log("INFO", th, ex,
            f"Request Received {{\"exchangeId\":\"{ex}\"}}")

        if is_success:
            run_success(ex, th)
        else:
            run_failure(ex, th)

        time.sleep(random.uniform(0.7, 1.6))

if __name__ == "__main__":
    run()

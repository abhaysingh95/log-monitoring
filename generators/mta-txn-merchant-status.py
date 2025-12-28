import random
import time
import json
from datetime import datetime

LOG_FILE = "logs/mta-txn-merchant-status.log"
THREADS = [f"executor-thread-{i}" for i in range(1, 6)]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def thread():
    return random.choice(THREADS)

def exchange_id():
    return f"{random.randint(1000000000,9999999999)}_{datetime.now().strftime('%m%d%Y%H%M%S')}{random.randint(100,999)}"

def acct():
    return str(random.randint(20000000000, 30000000000))

def ref():
    return str(random.randint(10**20, 10**21-1))

def log(level, clazz, th, ex, msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts()} {level}  [{clazz}] ({th}) exchangeId : '{ex}' - {msg}\n")

def request_received(th, ex):
    payload = {
        "exchangeId": ex,
        "referenceNo": ref(),
        "transactionType": "CASHWD1",
        "tranCategory": "CASH"
    }
    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        f"Request Received {json.dumps(payload)}")

def validate_leg(th, ex, leg, account):
    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        f"Validating Merchant Account for LegId : {leg},AccountNo : {account}")
    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        f"Merchant Account Received : {account}")
    log("INFO","org.fin.acc.dat.CacheOperations",th,ex,
        f"Searching Key {account}")

def cache_hit(th, ex, status="Active"):
    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        f"Account Status Found, Account Status AccountStatusDto "
        f"[debitFreeze=false, creditFreeze=false, accountStatus={status}]")

def ldap_flow(th, ex, account):
    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        "Merchant Status Not Cached. Checking in LDAP.")
    time.sleep(random.uniform(0.2, 0.5))

    ldap_resp = {
        "returnCode": "0",
        "responseCode": "0",
        "responseMessage": "SUCCESS",
        "data": {
            "accountNumber": account,
            "accountType": "DISTRIBUTOR",
            "customerName": "RandomUser",
            "accountStatus": "InActive",
            "debitFreeze": "FALSE",
            "creditFreeze": "FALSE"
        }
    }

    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        f"Response received From Ldap : {json.dumps(ldap_resp)}")

    log("INFO","org.fin.acc.ser.AccountStatusService",th,ex,
        "Account Status Found, Account Status AccountStatusDto "
        "[debitFreeze=false, creditFreeze=false, accountStatus=InActive]")

    log("ERROR","org.fin.acc.ser.AccountStatusService",th,ex,
        "Invalid Merchant Status.")
    log("ERROR","org.fin.acc.ser.AccountStatusService",th,ex,
        "Failed with message Invalid Merchant Status")

def run_success(th, ex):
    acc1 = acct()
    acc2 = acct()

    validate_leg(th, ex, 0, acc1)
    cache_hit(th, ex, "Active")

    validate_leg(th, ex, 1, acc2)
    cache_hit(th, ex, "Active")

def run_failure(th, ex):
    acc = acct()
    validate_leg(th, ex, 0, acc)
    ldap_flow(th, ex, acc)

def run():
    while True:
        th = thread()
        ex = exchange_id()

        request_received(th, ex)

        if random.random() < 0.98:
            run_success(th, ex)
        else:
            run_failure(th, ex)

        time.sleep(random.uniform(1.5, 3.0))

if __name__ == "__main__":
    run()

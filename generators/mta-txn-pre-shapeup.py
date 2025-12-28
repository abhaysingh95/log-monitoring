import random
import time
import json
import uuid
import os
from datetime import datetime

LOG_FILE = "logs/mta-txn-pre-shapeup.log"
THREADS = [f"executor-thread-{i}" for i in range(1, 6)]

CLASSES = {
    "resource": "com.fin.mta.TransactionServiceResource",
    "service": "com.fin.mta.pro.ServiceOperations",
    "set_null": "com.fin.mta.ope.SetNullGls",
    "validate": "com.fin.mta.ope.ValidateAccounts",
    "post": "com.fin.mta.ope.PostTransaction"
}

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def log(level, clazz, thread, exchange, msg):
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{ts()} {level:<5} [{clazz}] ({thread}) exchangeId : '{exchange}' - {msg}\n"
        )

def exchange_id():
    return str(uuid.uuid4())

def txn_body():
    return {
        "uniqueTransactionId": f"M-99-{random.randint(10**12,10**13)}",
        "appId": "FINOMER",
        "referenceNo": str(random.randint(10**10,10**14)),
        "acctFundTransferLegs": [
            {
                "legId": 0,
                "accountNumber": "",
                "amount": random.choice([1.0, 100.0, 10000.0]),
                "creditDebitFlag": "D",
                "transactionType": random.choice(["CASHWD1","CASHD539"]),
                "isAccount": False,
                "isMerchantAccount": False
            },
            {
                "legId": 1,
                "accountNumber": str(random.randint(20000000000,29999999999)),
                "amount": random.choice([1.0, 100.0]),
                "creditDebitFlag": "C",
                "transactionType": random.choice(["CASHWD1","CASHD539"]),
                "isAccount": True,
                "isMerchantAccount": True
            }
        ]
    }

# ---------------- SUCCESS FLOW ----------------
def run_success(thread, exch):
    txn = txn_body()

    log("INFO", CLASSES["resource"], thread, exch,
        f"Received '{json.dumps(txn)}'")

    log("INFO", CLASSES["service"], thread, exch,
        "In Operations Loop. Performing Operation - 'SET_BOTH_NULL_GL'")

    log("INFO", CLASSES["set_null"], thread, exch,
        f"mtaTransactionRequest before SET_BOTH_NULL_GL : {json.dumps(txn)}")

    txn["acctFundTransferLegs"][0]["accountNumber"] = str(random.randint(3200000000,3299999999))

    log("INFO", CLASSES["set_null"], thread, exch,
        f"mtaTransactionRequest after SET_BOTH_NULL_GL : {json.dumps(txn)}")

    log("INFO", CLASSES["service"], thread, exch,
        "Result of Operation Request 'SET_BOTH_NULL_GL' is ' added GL account.'")

    log("INFO", CLASSES["service"], thread, exch,
        "In Operations Loop. Performing Operation - 'VALIDATE_ACCOUNT'")

    log("INFO", CLASSES["validate"], thread, exch,
        "Validation Check passed")

    log("INFO", CLASSES["service"], thread, exch,
        "In Operations Loop. Performing Operation - 'POST_TRANSACTION'")

    log("INFO", CLASSES["post"], thread, exch,
        "'POST_TRANSACTION' Response => '{\"returnCode\":\"0\",\"responseMessage\":\"SUCCESS\"}'")

    log("INFO", CLASSES["service"], thread, exch,
        "Result of Operation Request 'POST_TRANSACTION' is SUCCESS")

# ---------------- ERROR FLOW ----------------
def run_failure(thread, exch):
    txn = txn_body()

    log("INFO", CLASSES["resource"], thread, exch,
        f"Received '{json.dumps(txn)}'")

    log("INFO", CLASSES["service"], thread, exch,
        "In Operations Loop. Performing Operation - 'POST_TRANSACTION'")

    err = {
        "returnCode": "1",
        "responseCode": "1",
        "responseMessage": "Posting amounts mismatch. Error occurred in fund transfer leg"
    }

    log("INFO", CLASSES["post"], thread, exch,
        f"'POST_TRANSACTION' Response => '{json.dumps(err)}'")

    log("INFO", CLASSES["service"], thread, exch,
        f"Operation POST_TRANSACTION failed. returning response {err}")

# ---------------- MAIN LOOP ----------------
def run():
    os.makedirs("logs", exist_ok=True)

    while True:
        exch = exchange_id()
        thread = random.choice(THREADS)

        # 🔑 SINGLE CONTROL POINT
        if random.random() < 0.98:
            run_success(thread, exch)
        else:
            run_failure(thread, exch)

        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    run()

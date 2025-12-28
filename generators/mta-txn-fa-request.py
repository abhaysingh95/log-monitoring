import random
import time
import uuid
from datetime import datetime
import json
import os

LOG_FILE = "logs/mta-txn-fa-request.log"

EXECUTOR_THREADS = [f"executor-thread-{i}" for i in range(10, 200)]

CLASSES = {
    "resource": "com.fin.mta.TransactionServiceResource",
    "set_req": "com.fin.mta.ope.SetMTATransactionRequest",
    "duplicate": "com.fin.mta.ope.CheckDuplicateTransaction",
    "allowed": "com.fin.mta.ope.CheckAllowedTransaction",
    "shapeup": "com.fin.mta.ope.ShapeUpTransaction",
    "service": "com.fin.mta.pro.ServiceOperations",
    "finalize": "com.fin.mta.ope.FinalizeTransaction",
}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def random_thread():
    return random.choice(EXECUTOR_THREADS)

def log(level, clazz, thread, message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{now()} {level:<5} [{clazz}] ({thread}) {message}\n")

def random_transaction():
    return {
        "appId": "FINOMER",
        "referenceNo": str(random.randint(10**14, 10**16)),
        "amount": random.choice([100, 500, 1000, 5000]),
        "transactionType": random.choice(["CASHD021", "CASHWD1"]),
        "userId": str(random.randint(4000000000, 4999999999))
    }

def generate_fa_request():
    os.makedirs("logs", exist_ok=True)

    exchange_id = str(uuid.uuid4())
    thread = random_thread()
    txn = random_transaction()

    # REQUEST RECEIVED
    log(
        "INFO",
        CLASSES["resource"],
        thread,
        f"Received new Transaction Request '{json.dumps(txn)}'"
    )

    log(
        "INFO",
        CLASSES["set_req"],
        thread,
        f"exchangeId : '{exchange_id}' - Current exchange : "
        f"{json.dumps({'exchangeId': exchange_id, 'body': txn})}"
    )

    log(
        "INFO",
        CLASSES["service"],
        thread,
        f"exchangeId : '{exchange_id}' - Result of Operation Request 'SET_TRANSACTION_REQUEST'"
    )

    time.sleep(random.uniform(0.01, 0.1))

    # DUPLICATE CHECK (95% pass)
    log(
        "INFO",
        CLASSES["duplicate"],
        thread,
        f"exchangeId : '{exchange_id}' - Checking duplicate transaction"
    )

    if random.random() < 0.98:
        log(
            "INFO",
            CLASSES["duplicate"],
            thread,
            f"exchangeId : '{exchange_id}' - 'DUPLICATE_CHECK' Response => "
            f"'{{\"returnCode\":\"0\",\"responseMessage\":\"Not Duplicate\"}}'"
        )
    else:
        log(
            "INFO",
            CLASSES["duplicate"],
            thread,
            f"exchangeId : '{exchange_id}' - 'DUPLICATE_CHECK' Response => "
            f"'{{\"returnCode\":\"1\",\"responseMessage\":\"Duplicate Transaction\"}}'"
        )
        log(
            "INFO",
            CLASSES["service"],
            thread,
            f"exchangeId : '{exchange_id}' - Operation DUPLICATE_CHECK failed"
        )
        return

    time.sleep(random.uniform(0.01, 0.1))

    # ALLOWED TRANSACTION
    log(
        "INFO",
        CLASSES["allowed"],
        thread,
        f"exchangeId : '{exchange_id}' - Transaction allowed"
    )

    time.sleep(random.uniform(0.01, 0.1))

    # POST TRANSACTION (95% success)
    if random.random() < 0.98:
        log(
            "INFO",
            CLASSES["shapeup"],
            thread,
            f"exchangeId : '{exchange_id}' - 'POST_TRANSACTION' Response => "
            f"'{{\"returnCode\":\"0\",\"txnReferenceNo\":\"{txn['referenceNo']}\"}}'"
        )
        log(
            "INFO",
            CLASSES["finalize"],
            thread,
            f"exchangeId : '{exchange_id}' - Exchange Finalized Successfully"
        )
    else:
        log(
            "INFO",
            CLASSES["shapeup"],
            thread,
            f"exchangeId : '{exchange_id}' - 'POST_TRANSACTION' Response => "
            f"'{{\"returnCode\":\"1\",\"responseMessage\":\"Posting amounts mismatch\"}}'"
        )
        log(
            "INFO",
            CLASSES["finalize"],
            thread,
            f"exchangeId : '{exchange_id}' - Exchange Finalized with ERROR"
        )

def run():
    while True:
        generate_fa_request()
        time.sleep(random.uniform(0.2, 1.0))

if __name__ == "__main__":
    run()

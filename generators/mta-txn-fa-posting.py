import time
import random
import uuid
from datetime import datetime, timedelta

OUTPUT_FILE = "logs/mta-txn-fa-posting.log"

EXECUTOR_THREADS = [f"executor-thread-{i}" for i in range(1, 8)]

CLASSES = [
    "co.fi.mt.se.MTATransactionPostingServiceImpl",
    "co.fi.mt.pr.PostTransactionService",
    "co.fi.mt.ut.PostTransactionMapper",
    "co.fi.mt.ut.DateUtil",
    "io.qu.ht.access-log"
]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def thread():
    return random.choice(EXECUTOR_THREADS)

def exchange_id():
    return f"{uuid.uuid4()}"

def reference_no():
    return str(random.randint(10**11, 10**12 - 1))

def log(level, clazz, th, ex, msg):
    with open(OUTPUT_FILE, "a") as f:
        f.write(
            f"{ts()} {level:<5} [{clazz}] ({th}) exchangeId : '{ex}' - {msg}\n"
        )

# ---------------- SUCCESS FLOW ----------------
def run_success(ex, th):

    log(
        "INFO",
        CLASSES[0],
        th,
        ex,
        f'Request Received {{"exchangeId":"{ex}","referenceNo":"{reference_no()}"}}'
    )

    log(
        "INFO",
        CLASSES[1],
        th,
        ex,
        "Values for Properties, checkValueDateSettingsFrom=11:30:00 ,checkValueDateSettingsUntil=12:30:00, Eod Offset=00:30:00"
    )

    log(
        "INFO",
        CLASSES[2],
        th,
        ex,
        "Mapper=PostTransactionMapper|Method=mapFromDto|Eod Offset=EoDOffsetSpec(...)"
    )

    log(
        "INFO",
        CLASSES[3],
        th,
        ex,
        f"Util=DateUtil|Method=getValueDate|Value Date={datetime.now() + timedelta(minutes=30)}"
    )

    log(
        "INFO",
        CLASSES[1],
        th,
        ex,
        "INITIATING A DMT TRANSACTION"
    )

    log(
        "INFO",
        CLASSES[4],
        th,
        ex,
        f'127.0.0.1 - - [{datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")}] '
        f'"POST /post-transaction/api/v1/transaction HTTP/1.1" 200 312'
    )

    log(
        "INFO",
        CLASSES[1],
        th,
        ex,
        "Result of Operation Request 'FA_POSTING' is SUCCESS"
    )

# ---------------- ERROR FLOW ----------------
def run_failure(ex, th):

    log(
        "ERROR",
        CLASSES[0],
        th,
        ex,
        "Error occurred @ PostTransactionResource::saveTransaction | "
        "Exception=Insufficient balance"
    )

    log(
        "INFO",
        CLASSES[1],
        th,
        ex,
        "Operation FA_POSTING failed. returning response "
        "{returnCode=1, responseCode=MTA-402, responseMessage=Insufficient balance}"
    )

# ---------------- MAIN LOOP ----------------
def run():
    while True:
        ex = exchange_id()
        th = thread()

        if random.random() < 0.98:
            run_success(ex, th)
        else:
            run_failure(ex, th)

        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    run()

import time
import random
import uuid
from datetime import datetime

OUTPUT_FILE = "logs/mta-txn-nfa-posting.log"

EXECUTOR_THREADS = [f"executor-thread-{i}" for i in range(1, 5)]

CLASSES = {
    "service": "co.fi.mt.se.MTATransactionPostingServiceImpl",
    "post": "co.fi.mt.pr.PostTransactionService",
    "mapper": "co.fi.mt.ut.PostTransactionMapper",
    "dateutil": "co.fi.mt.ut.DateUtil",
    "sql_warn": "or.hi.en.jd.sp.SqlExceptionHelper",
    "access": "io.qu.ht.access-log",
}

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def trace():
    return uuid.uuid4().hex

def span():
    return uuid.uuid4().hex[:16]

def write(level, clazz, thread, msg):
    line = (
        f"{ts()} {level:<5} "
        f"traceId={trace()}, parentId={span()}, spanId={span()}, sampled=true "
        f"[{clazz}] ({thread}) {msg}\n"
    )
    with open(OUTPUT_FILE, "a") as f:
        f.write(line)

def access_log(thread, code):
    line = (
        f"{ts()} INFO  "
        f"traceId={trace()}, parentId={span()}, spanId={span()}, sampled=true "
        f"[{CLASSES['access']}] ({thread}) "
        f'127.0.0.6 - - [{datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0530")}] '
        f'"POST /post-transaction/api/v1/transaction/nfa HTTP/1.1" {code} {random.randint(100,300)}\n'
    )
    with open(OUTPUT_FILE, "a") as f:
        f.write(line)

# ---------------- SUCCESS FLOW ----------------
def run_success():
    t = random.choice(EXECUTOR_THREADS)

    write("INFO", CLASSES["service"], t,
          f'Request Received {{"uniqueTransactionId":"M-{random.randint(10,99)}-{int(time.time()*1000)}","transCategory":"NFA"}}')

    write("INFO", CLASSES["post"], t,
          "Values for Properties, checkValueDateSettingsFrom=11:30:00 ,checkValueDateSettingsUntil=12:30:00, Eod Offset=00:30:00")

    write("INFO", CLASSES["mapper"], t,
          "Mapper=PostTransactionMapper|Method=mapFromDto|Eod Offset=EoDOffsetSpec(...)")

    write("INFO", CLASSES["dateutil"], t,
          "Util=DateUtil|Method=isValidEoDOffsetSpec|EoDOffsetSpec=EoDOffsetSpec(...)")

    write("INFO", CLASSES["dateutil"], t,
          "Util=DateUtil|Method=getValueDate|Message=Returning current time")

    write("INFO", CLASSES["post"], t,
          "PostTransaction DB Entity {...}")

    write("INFO", CLASSES["post"], t,
          "INITIATING A DMT TRANSACTION")

    access_log(t, 200)

# ---------------- ERROR FLOW ----------------
def run_failure():
    t = random.choice(EXECUTOR_THREADS)

    write("WARN", CLASSES["sql_warn"], t,
          "SQL Error: 0, SQLState: 23505")

    write("ERROR", CLASSES["sql_warn"], t,
          'ERROR: duplicate key value violates unique constraint "unique_trans_reference_num"')

    write("ERROR", CLASSES["service"], t,
          "Error occurred @ PostTransactionResource::saveTransaction|Exception=: "
          "java.lang.RuntimeException: ConstraintViolationException")

    access_log(t, 400)

# ---------------- MAIN LOOP ----------------
def run():
    while True:
        # 🔑 SINGLE CONTROL POINT (same pattern everywhere)
        if random.random() < 0.98:
            run_success()
        else:
            run_failure()

        time.sleep(random.uniform(0.5, 1.4))

if __name__ == "__main__":
    run()

import time
import random
import uuid
from datetime import datetime

LOG_FILE = "logs/mta-comm-posting.log"

EXEC_THREADS = ["executor-thread-1", "executor-thread-2", "executor-thread-5"]
VERTX_THREAD = "vert.x-eventloop-thread-8"

# ---------- helpers ----------
def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def et():
    return random.choice(EXEC_THREADS)

def txn_ref():
    return str(random.randint(10**11, 10**12 - 1))

def acct():
    return str(random.randint(20000000000, 20999999999))

def agent():
    return str(random.randint(1000000000, 9999999999))

def amount():
    return round(random.uniform(1.5, 15.0), 2)

def write(line):
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ---------- common logs ----------
def grpc_severe():
    write(
        f"{ts()} SEVERE [io.qua.ope.run.exp.otl.VertxGrpcExporter] ({VERTX_THREAD}) "
        "Failed to export spans. The request could not be executed. "
        "Full error message: Connection refused: localhost/127.0.0.1:4317"
    )

# ---------- SUCCESS FLOW ----------
def run_success():
    ref = txn_ref()

    for _ in range(random.randint(2, 3)):
        rid = str(uuid.uuid4())
        acc = acct()
        amt = amount()
        tds = round(amt * 0.25, 2)

        write(
            f"{ts()} INFO  [com.fin.mta.CommissionPostingImpl] ({et()}) "
            f"Request Received for Commission Posting: CommPostingRequest("
            f"txnReferenceNo={ref}, txnDate=2025-11-27, commissionRid={rid}, "
            f"isDeffered=false, toBePostedOn=2025-11-27, accountNumber={acc}, "
            f"commissionAmount={amt}, transactionType=DMTIMPSP2A, "
            f"transactionDescription=Commission Amount for Agent {agent()} "
            f"Plan Id MTA_IMPS_COM_002 RefID: {ref})"
        )

        write(
            f"{ts()} INFO  [com.fin.mta.CommissionPostingImpl] ({et()}) "
            "Request validation succeeded."
        )

        write(
            f"{ts()} INFO  [com.fin.mta.CommissionPostingImpl] ({et()}) "
            f"Requesting commission posting with request CommissionLegAddRequest("
            f"txnReferenceNo={ref}, accountNumber={acc}, "
            f"commissionAmount={amt}, tdsAmount={tds}, transactionType=DMTIMPSP2A)"
        )

        time.sleep(random.uniform(0.3, 0.7))

        write(
            f"{ts()} INFO  [com.fin.mta.CommissionPostingImpl] ({et()}) "
            "Response Received from legAdder MTAReturnResponse(returnCode=0, responseMessage=SUCCESS, data=null)"
        )

        write(
            f"{ts()} INFO  [com.fin.mta.CommissionPostingImpl] ({et()}) "
            f"Persisting CommissionLegNonAmt: CommissionLegNonAmt("
            f"id=null, txnReferenceNo={ref}, commissionRid={rid}, "
            f"accountNumber={acc}, commissionAmount={amt}, "
            f"createdAt={datetime.now().strftime('%a %b %d %H:%M:%S IST %Y')}, "
            f"isCommissionPosted=true)"
        )

# ---------- ERROR FLOW ----------
def run_failure():
    write(
        f"{ts()} WARN  [org.hib.eng.jdb.spi.SqlExceptionHelper] ({et()}) "
        "SQL Error: 0, SQLState: 23505"
    )

    write(
        f"{ts()} ERROR [org.hib.eng.jdb.spi.SqlExceptionHelper] ({et()}) "
        "ERROR: duplicate key value violates unique constraint \"commission_leg_non_amt_un\""
    )

    write(
        f"{ts()} ERROR [com.fin.mta.CommissionPostingImpl] ({et()}) "
        "DatabaseException Message ERROR: duplicate key value violates unique constraint "
        "\"commission_leg_non_amt_un\""
    )

# ---------- MAIN LOOP ----------
def run():
    while True:
        # 🔑 SINGLE CONTROL POINT (same everywhere)
        if random.random() < 0.95:
            run_success()
        else:
            run_failure()

        # occasional infra noise (very rare)
        if random.random() < 0.03:
            grpc_severe()

        time.sleep(random.uniform(1.5, 3.5))

if __name__ == "__main__":
    run()

import random
import time
import json
from datetime import datetime

LOG_FILE = "logs/mta-txn-walking-status.log"
THREADS = [f"executor-thread-{i}" for i in range(1, 8)]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def thread():
    return random.choice(THREADS)

def exchange_id():
    return f"{random.randint(1000000000,9999999999)}_{datetime.now().strftime('%m%d%Y%H%M%S')}{random.randint(100,999)}"

def mobile():
    return str(random.randint(6000000000, 9999999999))

def ref():
    return str(random.randint(10**18, 10**19-1))

def log(level, clazz, th, ex, msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts()} {level}  [{clazz}] ({th}) exchangeId : '{ex}' - {msg}\n")

def run_success(ex, th):
    acct = mobile()
    log("INFO","com.fin.mta.ope.SearchWalkinOperation",th,ex,f"Checking For Walkin Account. accountNo: {acct}")

    log(
        "INFO",
        "com.fin.mta.ope.SearchWalkinOperation",
        th,
        ex,
        f"Response Received From Walkin Search Operation : "
        f"{json.dumps({'returnCode':'0','searchWalkinCustomerList':[{'mobileNumber':acct,'walkinStatus':'Active'}]})}"
    )

    log("INFO","com.fin.mta.pro.ServiceOperations",th,ex,"Result of Operation Request 'SEARCH_WALKING' is 'Walkin Search and Status Check passed.'")

    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"In Operations Loop. Performing Operation - 'WALKING_LIMIT'")
    log("INFO","com.fin.mta.ope.WalkinLimitOperation",th,ex,f"Checking WalkinLimit for account: {acct} and tranGroup: DMTREMIT")

    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"Result of Operation Request 'WALKING_LIMIT' is '{\"returnCode\":\"0\"}'")

    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"In Operations Loop. Performing Operation - 'BENE_LIMIT'")
    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"Result of Operation Request 'BENE_LIMIT' is '{\"returnCode\":\"0\"}'")

    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"In Operations Loop. Performing Operation - 'POST_WALKING_LIMIT'")
    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"Result of Operation Request 'POST_WALKING_LIMIT' is '{\"responseMessage\":\"SUCCESS\"}'")

    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"In Operations Loop. Performing Operation - 'POST_BENE_LIMIT'")
    log("INFO","com.fin.mta.ope.ValidateLimits",th,ex,"Result of Operation Request 'POST_BENE_LIMIT' is '{\"responseMessage\":\"SUCCESS\"}'")

    log("INFO","com.fin.mta.pro.ServiceOperations",th,ex,"Result of Operation Request 'VALIDATE_LIMITS' is '{\"responseMessage\":\"SUCCESS\"}'")

def run_failure(ex, th):
    acct = mobile()
    log("INFO","com.fin.mta.ope.SearchWalkinOperation",th,ex,f"Checking For Walkin Account. accountNo: {acct}")
    log("INFO","com.fin.mta.ope.SearchWalkinOperation",th,ex,"Response Received From Walkin Search Operation : {\"returnCode\":\"1\",\"searchWalkinCustomerList\":null}")
    log("ERROR","com.fin.mta.ope.SearchWalkinOperation",th,ex,"Walkin Account Not Found.")
    log("ERROR","com.fin.mta.ope.SearchWalkinOperation",th,ex,"Failed with message Walkin Account Not Found")
    log("INFO","com.fin.mta.pro.ServiceOperations",th,ex,"Operation SEARCH_WALKING failed. returning response MTAReturnResponse(returnCode=1, responseCode=MTA-101, responseMessage=Walkin Account Not Found, data=null)")

def run():
    while True:
        ex = exchange_id()
        th = thread()

        log(
            "INFO",
            "com.fin.mta.WalkingStatusResource",
            th,
            ex,
            f"Received '{{\"referenceNo\":\"{ref()}\",\"appId\":\"FINOMER\"}}'"
        )

        log("INFO","com.fin.mta.pro.ServiceOperations",th,ex,"In Operations Loop. Performing Operation - 'SEARCH_WALKING'")

        if random.random() < 0.95:
            run_success(ex, th)
        else:
            run_failure(ex, th)

        time.sleep(random.uniform(1.1, 2.5))

if __name__ == "__main__":
    run()

import random
import time
import uuid
import json
import os
from datetime import datetime

LOG_FILE = "logs/mta-txn-imps-shapeup.log"

THREADS = [f"executor-thread-{i}" for i in range(10, 30)]

CLASSES = {
    "resource": "com.fin.mta.TransactionServiceResource",
    "service": "com.fin.mta.pro.ServiceOperations",
    "charges": "com.fin.mta.ope.GetChargesOperation",
    "refire": "com.fin.mta.ope.ValidateRefire",
    "fa": "com.fin.mta.ope.FaPostingOperation"
}

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def log(level, clazz, thread, exchange_id, msg):
    line = f"{ts()} {level:<5} [{clazz}] ({thread}) exchangeId : '{exchange_id}' - {msg}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)

def random_exchange_id():
    return f"{random.randint(4000000000,4999999999)}_{random.randint(10**14,10**15)}_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"

def random_request():
    return {
        "appId": "FINOMER",
        "referenceNo": str(random.randint(10**14, 10**16)),
        "transactionType": random.choice(["DMTIMPSP2A", "GOLDSUBS", "SILVSUBS"]),
        "amount": random.choice([0, 105, 2999]),
        "accountNumber": str(random.randint(20000000000, 30000000000))
    }

def generate_flow():
    os.makedirs("logs", exist_ok=True)

    thread = random.choice(THREADS)
    exchange_id = random_exchange_id()
    req = random_request()

    # RECEIVED
    log("INFO", CLASSES["resource"], thread, exchange_id,
        f"Received '{json.dumps(req)}'")

    # GET_CHARGES
    log("INFO", CLASSES["service"], thread, exchange_id,
        "In Operations Loop. Performing Operation - 'GET_CHARGES'")

    log("INFO", CLASSES["charges"], thread, exchange_id,
        f"Requesting Charges for Phase phase3. Request : {json.dumps(req)}")

    time.sleep(random.uniform(0.05, 0.15))

    charges_success = random.choice([True, True, False])

    if charges_success:
        charges_resp = {
            "returnCode": "0",
            "charge": round(random.uniform(10, 50), 2),
            "tax": round(random.uniform(1, 5), 2)
        }

        log("INFO", CLASSES["charges"], thread, exchange_id,
            f"Response Received From Charges Service {json.dumps(charges_resp)}")

        log("INFO", CLASSES["service"], thread, exchange_id,
            "Result of Operation Request 'GET_CHARGES' is "
            f"'{json.dumps(charges_resp)}'")
    else:
        err_resp = {
            "returnCode": "1",
            "responseCode": random.choice(["MTA-504", "1"]),
            "responseMessage": random.choice([
                "Charge Validation Failed",
                "Null value encountered while fetching property"
            ])
        }

        log("INFO", CLASSES["charges"], thread, exchange_id,
            f"'GET_CHARGES' Response => '{json.dumps(err_resp)}'")

        log("INFO", CLASSES["service"], thread, exchange_id,
            f"Operation GET_CHARGES failed. returning response {err_resp}")
        return

    # VALIDATE_REFIRE
    log("INFO", CLASSES["service"], thread, exchange_id,
        "In Operations Loop. Performing Operation - 'VALIDATE_REFIRE'")

    log("INFO", CLASSES["refire"], thread, exchange_id,
        "Not a Refire Transaction.")

    # FA_POSTING
    log("INFO", CLASSES["service"], thread, exchange_id,
        "In Operations Loop. Performing Operation - 'FA_POSTING'")

    log("INFO", CLASSES["fa"], thread, exchange_id,
        f"DBRequest {json.dumps(req)}")

    time.sleep(random.uniform(0.05, 0.2))

    fa_success = random.choice([True, True, False])

    if fa_success:
        fa_resp = {
            "returnCode": "0",
            "txnReferenceNo": req["referenceNo"],
            "balancesList": [
                {
                    "accountNo": req["accountNumber"],
                    "availableBalance": round(random.uniform(1e6, 1e7), 2)
                }
            ]
        }

        log("INFO", CLASSES["fa"], thread, exchange_id,
            f"'FA_POSTING' Response => '{json.dumps(fa_resp)}'")

        log("INFO", CLASSES["service"], thread, exchange_id,
            "Result of Operation Request 'FA_POSTING' is "
            f"'{json.dumps(fa_resp)}'")
    else:
        err = {
            "returnCode": "1",
            "responseMessage": "CBS Posting Failed"
        }

        log("INFO", CLASSES["fa"], thread, exchange_id,
            f"'FA_POSTING' Response => '{json.dumps(err)}'")

        log("INFO", CLASSES["service"], thread, exchange_id,
            f"Operation FA_POSTING failed. returning response {err}")

def run():
    while True:
        generate_flow()
        time.sleep(random.uniform(0.3, 1.2))

if __name__ == "__main__":
    run()

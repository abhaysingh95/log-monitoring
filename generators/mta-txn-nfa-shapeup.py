
import time
import random
import uuid
from datetime import datetime

LOG_FILE = "logs/mta-txn-nfa-shapeup.log"

THREADS = [
    "executor-thread-1",
    "executor-thread-2",
    "executor-thread-5"
]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def rand_thread():
    return random.choice(THREADS)

def rand_ref():
    return str(random.randint(10**17, 10**18 - 1))

def rand_user():
    return str(random.randint(10**9, 10**10 - 1))

def rand_exchange(user):
    return f"{user}_{random.randint(10**16,10**17)}_{int(time.time()*1000)}"

def write(line):
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def success_flow():
    user = rand_user()
    ref = rand_ref()
    exch = rand_exchange(user)
    th = rand_thread()

    write(f'{ts()} INFO  [com.fin.mta.TransactionServiceResource] ({th}) Received \'{{"exchangeId":"{exch}"}}\'')
    write(f'{ts()} INFO  [com.fin.mta.pro.ServiceOperations] ({th}) exchangeId : \'{exch}\' - In Operations Loop. Performing Operation - \'NFA_SHAPEUP\'')
    write(f'{ts()} INFO  [com.fin.mta.ope.NFaPostingOperation] ({th}) exchangeId : \'{exch}\' - Current exchange : {{...}}')
    write(f'{ts()} INFO  [com.fin.mta.ope.NFaPostingOperation] ({th}) exchangeId : \'{exch}\' - \'NFA_SHAPEUP\' Response => \'{{"returnCode":"0","txnReferenceNo":"{ref}","cbsTxnReferenceNo":"M-{random.randint(10,99)}-{int(time.time()*1000)}"}}\'')
    write(f'{ts()} INFO  [com.fin.mta.pro.ServiceOperations] ({th}) exchangeId : \'{exch}\' - Result of Operation Request \'NFA_SHAPEUP\' is \'{{"returnCode":"0"}}\'')

def error_flow():
    user = rand_user()
    ref = rand_ref()
    exch = rand_exchange(user)
    th = rand_thread()

    write(f'{ts()} INFO  [com.fin.mta.TransactionServiceResource] ({th}) Received \'{{"exchangeId":"{exch}"}}\'')
    write(f'{ts()} INFO  [com.fin.mta.pro.ServiceOperations] ({th}) exchangeId : \'{exch}\' - In Operations Loop. Performing Operation - \'NFA_SHAPEUP\'')
    write(f'{ts()} INFO  [com.fin.mta.ope.NFaPostingOperation] ({th}) exchangeId : \'{exch}\' - Current exchange : {{...}}')
    write(f'{ts()} INFO  [com.fin.mta.ope.NFaPostingOperation] ({th}) exchangeId : \'{exch}\' - failed, failed while fetching nfa posting service.')
    write(
        f'{ts()} INFO  [com.fin.mta.pro.ServiceOperations] ({th}) exchangeId : \'{exch}\' - Result of Operation Request \'NFA_SHAPEUP\' is '
        f'\'{{"returnCode":"1","responseCode":"1","responseMessage":"ERROR: duplicate key value violates unique constraint \\"unique_trans_reference_num\\" '
        f'Detail: Key (txn_reference_no)=({ref}) already exists."}}\''
    )

def run():
    while True:
        if random.random() < 0.90:
            success_flow()
        else:
            error_flow()
        time.sleep(random.uniform(0.8, 2.5))

if __name__ == "__main__":
    run()

import bjoern
import os
import signal
from pyDMON import app

host = '0.0.0.0'
port = 5001
NUM_WORKERS = 2
worker_pids = []


bjoern.listen(app, host, port)
for _ in xrange(NUM_WORKERS):
    pid = os.fork()
    if pid > 0:
        # in master
        worker_pids.append(pid)
    elif pid == 0:
        # in worker
        try:
            bjoern.run()
        except KeyboardInterrupt:
            pass
        exit()

try:
    for _ in xrange(NUM_WORKERS):
        os.wait()
except KeyboardInterrupt:
    for pid in worker_pids:
        os.kill(pid, signal.SIGINT)
# networkapps
Network Applications

Sample usage of the ciscoping suite.
Mainly used for testing full mesh connectivity between branches, usually cisco edge routers and/or core switches

```
import logging
import os
import Queue
from threading import Thread
from network_utils.cisco_ssh import CiscoSSH
from networkapps.ciscoping import PingSwitch, ProcessPingOutput
        
def main():
    log = os.path.join(os.path.expanduser("~"), "log")
    creds = (("admin", "P455w0rd"), ("cisco", "cisco"))
    core_sws = ["10.0.1.254", "10.0.2.254", "10.0.3.254", "10.16.0.254", "10.32.0.254"]
    swq = Queue.Queue()
    outq = Queue.Queue()
    num_switch_threads = 3
    num_out_threads = 1
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(filename="ciscoping.log")
    formatter = logging.Formatter('%(asctime)s %(threadName)s %(message)s')
    fh.setFormatter(formatter)    
    logger.addHandler(fh)
    
    output = logging.getLogger("%s output" % __name__)
    output.setLevel(logging.INFO)
    fho = logging.FileHandler(filename="ciscoping.out")
    output.addHandler(fho)
    

    for i in core_sws:
        swq.put(i)

    for i in range(num_switch_threads):
        t = PingSwitch(swq=swq, targets=core_sws, outq=outq, timeout=16, logger=logger, creds=creds)
        t.setDaemon(True)
        t.start()

    for i in range(num_out_threads):
        t = ProcessPingOutput(outq=outq, logger=logger, output=output)
        t.setDaemon(True)
        t.start()

    swq.join()
    outq.join()
    
main()
```

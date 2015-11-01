import re
import pprint
import json
import logging
import os
import Queue
from threading import Thread
from network_utils.cisco_ssh import CiscoSSH

class PingSwitch(Thread):
    def __init__(self, swq=None, targets=None, outq=None, timeout=8, logger=None, creds=None):
        Thread.__init__(self)
        self.swq = swq
        self.targets = targets
        self.outq = outq
        self.timeout = timeout
        self.logger = logger
        self.creds = creds
        self.name = self.getName()
        self.status = lambda x: x[0] and "OK" or "FAIL: %s" % str(x[1])
        
    def connect(self, ip):
        self.logger.debug("Connecting to %s" % ip)
        sw = CiscoSSH(ip=ip, creds=self.creds, timeout=self.timeout)
        status = sw.authenticate(pre_cmds=["terminal length 0"])
        self.logger.debug("Connection status to %s - %s" % (ip, bool(status)))
        return status, sw
    
    def ping_command(self, sw, target):
        targets = self.targets or []
        self.logger.debug("Sending ping command to %s" % target)
        ret = sw.send_cmd(["ping %s" % target], delay_factor=3) # need to set delay_factor as a class attribute
        pat = re.compile("percent \((?P<percent>.*)\)")
        pct = pat.search(ret).group("percent").split("/")
        return int(pct[0]) / int(pct[1]) == 1, tuple(map(int,pct))
    
    def run(self):
        while True:
            self.logger.debug("Entering ping_switch")
            sw_ip = self.swq.get()
            self.logger.debug("Acquired %s from swq" % sw_ip)
            stat, sw = self.connect(ip=sw_ip)
            targets = self.targets[:]
            targets.remove(sw_ip)
            if stat[0]:
                for target in targets:
                    ret = self.ping_command(sw=sw, target=target)
                    out = "Ping from %s to %s: %s" % (sw_ip, target, self.status(ret))
                    self.outq.put(out)
                sw.close()
            else:
                out = "Cannot connect to %s" % sw
                #self.logger.info(out)
                self.outq.put(out)
            self.swq.task_done()
            
        self.logger.debug("Exiting PingSwitch")
        

        
class ProcessPingOutput(Thread):
    def __init__(self, outq=None, logger=None, output=None):
        Thread.__init__(self)
        self.logger = logger
        self.outq = outq
        self.name = self.getName()
        self.output = output
        
    def run(self):
        while True:
            self.logger.debug("Entering process_output queue")
            out = self.outq.get()
            self.logger.debug("Acquired from outq: %s" % out)
            self.logger.info(out)
            self.output.info(out)
            self.outq.task_done()
        self.logger.info("Exiting ProcessPingOutput")


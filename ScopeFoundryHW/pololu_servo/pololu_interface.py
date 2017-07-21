"""
Polulu Micro Maestro ScopeFoundry module
Created on Jul 18, 2017

@author: Alan Buckley
"""


from __future__ import division, absolute_import, print_function
import serial
import time
import logging

logger = logging.getLogger(__name__)

class PololuDev(object):
    
    name="pololu_servo_device"
    
    def __init__(self, port, device_addr=0x0C, debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("PololuDev.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, timeout=0.5
                                 )
        self.polulu_header = chr(0xAA) + chr(device_addr)
        self.ser.flush()
        time.sleep(0.2)
        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = self.polulu_header + cmd
        self.ser.write(bytes(message, 'latin-1'))
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        self.ser.flush()
        return resp
    
    
    def write_position(self, chan, target):
        base_qty = target * 4 
        cmd_hex = 0x84
        cl_hex = cmd_hex & 0x7F
        lsb = base_qty & 0x7F
        msb = (base_qty >> 7) & 0x7F
        cmd = chr(cl_hex) + chr(chan) + chr(lsb) + chr(msb)
        self.ask_cmd(cmd)
        
    def read_position(self, chan):
        cmd_hex = 0x10
        cmd = chr(cmd_hex) + chr(chan)
        resp = self.ask_cmd(cmd)
#         return resp
        lsb = resp[0]
        msb = resp[1]
        data = (msb << 8) + lsb
        return data
        
    def close(self):
        self.ser.close()
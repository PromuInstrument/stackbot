'''
Created on Feb 6, 2017

@author: Alan Buckley
'''

from __future__ import division, absolute_import, print_function
import serial
import time
import logging

logger = logging.getLogger(__name__)

class RelayArduinoInterface(object):
    
    name="relay_arduino_interface"
    
    def __init__(self, port="COM3", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("RelayArduino.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout = 0.1)
        # Store relay values
        self.ser.flush()
        time.sleep(1.7)
        
        self.relays = None
        self.poll()
        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+b'\n'
        self.ser.write(message)
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        return resp
    
    def send_cmd(self, cmd):
        if self.debug:
            logger.debug("send: {}".format(cmd))
        message = cmd+b'\n'
        self.ser.write(message)
        if self.debug:
            logger.debug("message: {}".format(message))
        
    def write_state(self, pin, value):
        assert (pin in (1,2,3,4)), "Please enter a relay number in range 1 to 4"
        if value:
            cmd = "c{}".format(pin).encode()
        else:
            cmd = "o{}".format(pin).encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("state_cmd: {}".format(cmd))


    def poll(self):
        resp = self.ask_cmd(b"?")
        print("resp:", resp)
        data = resp.strip().decode()
        print("data:", data)
        self.relays = poll = [bool(int(x)) for x in data]
        print("poll:", poll)
        if self.debug:
            logger.debug("stored val: {}".format(self.relays))
        return poll
           
    def close(self):
        self.ser.close()
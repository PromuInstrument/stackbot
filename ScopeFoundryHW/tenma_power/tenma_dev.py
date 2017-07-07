'''
Created on Jul 6, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
'''
import serial
import time
import logging

logger = logging.getLogger(__name__)

class TenmaDev(object):
    
    name = 'tenma_dev'
    
    def __init__(self, port="COM5", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("ButtonBoardInterface.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=9600, 
                                    bytesize=serial.EIGHTBITS, 
                                    parity=serial.PARITY_NONE, 
                                    stopbits=serial.STOPBITS_ONE, 
                                    timeout = 0.1)

        self.ser.flush()
        time.sleep(0.2)
        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+b'\n'
        self.ser.write(message)
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        self.ser.flush()
        return resp
    
    def write_voltage(self, chan=1, voltage):
        resp = self.ask_cmd("VSET{}:{:1.3f}".format(chan, voltage))
        return resp
    def read_set_voltage(self, chan=1):
        resp = self.ask_cmd("VSET{}?".format(chan))
        return resp
    
    def read_actual_voltage(self, chan=1):
        resp = self.ask_cmd("VOUT{}?".format(chan))
        return resp
    
    def write_current(self, chan=1, current):
        resp = self.ask_cmd("ISET{}:{:1.3f}".format(chan, current))
        return resp 
    
    def read_set_current(self, chan=1):
        resp = self.ask_cmd("ISET{}?".format(chan))
        return resp
    
    def read_actual_current(self, chan=1):
        resp = self.ask_cmd("IOUT{}?".format(chan))
        return resp
    
    
    def read_actual_current(self, chan=1):
        pass
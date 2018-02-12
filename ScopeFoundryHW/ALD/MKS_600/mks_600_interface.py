'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

import serial
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class MKS_600_Interface(object):
        
    name = 'mks_600_interface'
    
    def __init__(self, port="COM5", debug=False):
        self.port = port
        self.debug = debug
        
        self.lock = Lock()
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.EIGHTBITS, timeout=1,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.ser.flush()
        
        time.sleep(1)
    
        #Below variables store values temporarily in order to account for serial timing issues.
    
        self.units = None 
        self.float = None
        self.prtemp = None
        self.valve_open = None
        self.valve_thresholds = (0.08, 99.90)
        self.sensor_range = None
        self.error_count = 0
        
    def ask_cmd(self, cmd):
        with self.lock:
            self.ser.flush()
            message = cmd+'\r\n'
            self.ser.write(message)
            resp = self.ser.readline()
        return resp
    
    def read_sensor_range(self):
        resp = self.ask_cmd("R33")[1:-2]
        if resp != b'':
            value = int(resp)
            ranges = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1,
                      4: 2, 5: 5, 6: 10, 7: 50, 8: 100,
                      9: 500, 10: 1000, 11: 5000, 12:10000,
                      13: 1.33, 14: 2.66, 15: 13.33, 16: 133.3,
                      17: 1333, 18: 6666, 19: 13332
                    }
            resp = ranges[value]
            ## Store successfully retrieved value
            self.sensor_range = resp
            return resp
        else:            
            self.error_count += 1
            ## Read failed, return last stored value
            return self.sensor_range
        

    def read_pressure_units(self):
        resp = self.ask_cmd("R34")[1:-2]
        if resp != b'':
            value = int(resp)
            units = {0: "Torr",
                    1: "mTorr",
                    2: "mbar",
                    3: u"\u03bc"+"bar",
                    4: "kPa",
                    5: "Pa",
                    6: "cmH2O",
                    7: "inH2O"}
            resp = units[value]
            ## Store successfully retrieved value
            self.units = resp
            return resp
        else: 
            print("Pressure misread, using last stored temp value.")
            self.error_count += 1
            self.ser.flush()
            ## Read failed, return last stored value
            return self.units
    
    def read_pressure(self):
        resp = self.ask_cmd("R5")[1:-2]
        if resp != b'':
            fl = float(resp)
            pct = fl/100
            fs = self.read_sensor_range()
            self.prtemp = pct*fs
            return pct*fs
        else:
            print("Pressure misread, using last stored temp value.")
            self.error_count += 1
            self.ser.flush()
            ## Read failed, return last stored value
            return self.prtemp
            
        
    def read_valve(self):
        resp = self.ask_cmd("R6")[2:-2]
        return float(resp)
        
    def open_valve(self):
        """Command valve to move to full open"""
        self.ask_cmd("O")
    
    def halt_valve(self):
        """Halt valve at current position"""
        self.ask_cmd("H")
    
    def close_valve(self):
        """Command valve to move to full close"""
        self.ask_cmd("C")
        
    
    def close(self):
        self.ser.close()
        del self.ser
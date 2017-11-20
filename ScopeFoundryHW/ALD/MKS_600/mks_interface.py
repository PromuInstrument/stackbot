'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

import serial
import time
import logging

logger = logging.getLogger(__name__)


class mks_controller_interface(object):
        
    name = 'mks_pc_interface'
    
    def __init__(self, port="COM9", debug=False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.EIGHTBITS, timeout=0.1,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.ser.flush()
        
        time.sleep(1)
    
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+'\r\n'
        self.ser.write(message.encode())
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        return resp
    
    def read_sensor_range(self):
        if self.debug:
            print("sensresp", self.ask_cmd("R33")[1:-2])
        value = int(self.ask_cmd("R33")[1:-2])
        if self.debug:
            print("sensor range",value)
        ranges = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1,
                  4: 2, 5: 5, 6: 10, 7: 50, 8: 100,
                  9: 500, 10: 1000, 11: 5000, 12:10000,
                  13: 1.33, 14: 2.66, 15: 13.33, 16: 133.3,
                  17: 1333, 18: 6666, 19: 13332
                }
        resp = ranges[value]
        return resp
    
    def read_pressure_units(self):
        resp = self.ask_cmd("R34")[1:-2]
        if self.debug:
            print("resp", resp)
        value = int(resp)
        if self.debug:
            print("value:", value)
        units = {0: "Torr",
                1: "mTorr",
                2: "mbar",
                3: u"\u03bc"+"bar",
                4: "kPa",
                5: "Pa",
                6: "cmH2O",
                7: "inH2O"}
        resp = units[value]
        if self.debug:
            print("units:", resp)
        return resp
    
    def read_pressure(self):
        resp = self.ask_cmd("R5")[1:-2]
        if self.debug:
            print(resp)
        fl = float(resp)
        if self.debug:
            print("fl:", fl)
        pct = fl/100
        if self.debug:
            print("resp:", resp, "fl:", fl, "pct:", pct)
        fs = self.read_sensor_range()
        if self.debug:
            print("fs:", fs)
        return pct*fs
        
    def read_valve(self):
        resp = float(self.ask_cmd("R6")[2:-2])
        return resp
    
    def open_valve(self):
        self.ask_cmd("O")
    
    def close_valve(self):
        self.ask_cmd("C")
        
    
    def close(self):
        self.ser.close()
        del self.ser
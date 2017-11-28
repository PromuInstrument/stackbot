'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

import serial
import time
import logging

logger = logging.getLogger(__name__)

class Pfeiffer_VGC_Interface(object):
        
    name = 'pfeiffer_vgc_interface'
    
    def __init__(self, port="COM3", debug=False):
        self.port = port
        self.debug = debug
        if self.debug:
            pass
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.EIGHTBITS, timeout=0.1,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.ser.flush()
        
        time.sleep(1)
        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+b'\r\n'
        self.ser.write(message)
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        self.ser.flush()
        if resp == b"\x06\r\n":
            self.ser.write(b"\x05"+b"\r\n")
            resp = self.ser.readline()
        else: 
            print("Acknowledgement not received:{}".format(resp))
        return resp
    
    def read_sensor(self, sensor):
        status = {0: "Measurement data okay.",
                  1: "Underrange.",
                  2: "Overrange.",
                  3: "Sensor error.",
                  4: "Sensor off.",
                  5: "No sensor.",
                  6: "Identification error."}
        selection = "{}".format(sensor).encode()
        byte_array = self.ask_cmd(b"PR"+selection)
        resp = byte_array[:-2].decode().split(",")
        op_status = status[int(resp[0])]
        value = float(resp[1])
        if self.debug:
            return (op_status, value)
        else: 
            return value
        
    def sensor_type(self):
        resp = self.ask_cmd(b"TID")
        sensor_list = resp[:-2].decode().split(",")
        return sensor_list
#         return resp

    def read_units(self):
        resp = self.ask_cmd(b"UNI")
        return resp
    
    def write_units(self, unit_string):
        "Writes the units to be shown on controller display. Does not affect RS232 readout."
        unit_dict = {"mbar": 0,
                     "Torr": 1,
                     "Pascal": 2}
        unit_value = unit_dict[unit_string]
        message = b"UNI,"+"{}".format(unit_value).encode()
        print(message)
        resp = self.ask_cmd(message)
        return resp
    
    def close(self):
        self.ser.close()
        del self.ser
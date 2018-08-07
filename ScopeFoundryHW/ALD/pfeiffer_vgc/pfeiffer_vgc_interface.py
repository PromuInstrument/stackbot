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

class Pfeiffer_VGC_Interface(object):
        
    name = 'pfeiffer_vgc_interface'
    
    def __init__(self, port="COM3", debug=False):
        self.port = port
        self.debug = debug
        if self.debug:
            pass
        
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.EIGHTBITS, timeout=1,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.lock = Lock()
        self.ser.flush()
        
        time.sleep(1)
        
    def ask_cmd(self, cmd):
        """Issues correctly formatted commands/inquiries to Pfeiffer VGC.
        :returns: str. Response to original inquiry."""
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        
        message = cmd+'\r\n'
        
        with self.lock:
            self.ser.write(message)
            resp = self.ser.readline()
        
        if self.debug:
            logger.debug("readout: {}".format(cmd))
            print("ask_cmd resp:", resp)
        if resp == b"\x06\r\n":
            with self.lock:
                self.ser.write(b"\x05".decode()+"\r\n")
                resp = self.ser.readline()
            return resp
        else: 
            print("Acknowledgement not received:{}".format(resp))
        
    
    def read_sensor(self, sensor):
        """
        Reads pressure from specified sensor/channel number.
        
        =============  ===============  =========================================
        **Arguments**  **Type**         **Description**
        sensor         int              Channel number assigned to pressure 
                                        sensor by vacuum gauge controller
        =============  ===============  =========================================
        """
        status = {0: "Measurement data okay.",
                  1: "Underrange.",
                  2: "Overrange.",
                  3: "Sensor error.",
                  4: "Sensor off.",
                  5: "No sensor.",
                  6: "Identification error."}
        selection = "{}".format(sensor)#.encode()
        byte_array = self.ask_cmd("PR"+selection)
        if byte_array is not None:
            resp = byte_array[:-2].decode().split(",")
        else:
            print(type(byte_array))
        op_status = status[int(resp[0])]
        value = float(resp[1])
        if self.debug:
            return (op_status, value)
        else: 
            return value
        
    def sensor_type(self):
        """
        :returns: A list of sensor types detected on each VGC channel.
        """
        resp = self.ask_cmd("TID")
        sensor_list = resp.strip().decode().split(",")
        return sensor_list


    def read_units(self):
        """
        :returns: Units which are currently displayed on the VGC controller display.
        """
        resp = self.ask_cmd("UNI")
        return resp
    
    def write_units(self, unit_string):
        """
        Writes the units to be shown on controller display. Does not affect RS232 readout.
        """
        unit_dict = {"mbar": 0,
                     "Torr": 1,
                     "Pascal": 2}
        unit_value = unit_dict[unit_string]
        message = "UNI,"+"{}".format(unit_value)
        self.ask_cmd(message)
        
    def close(self):
        """
        Properly closes host serial connection to VGC controller.
        """
        self.ser.close()
        del self.ser
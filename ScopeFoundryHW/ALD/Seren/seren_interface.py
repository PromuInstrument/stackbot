'''
Created on Jan 4, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

import serial
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class Seren_Interface(object):
    
    name='seren_interface'
    
    def __init__(self, port="COM6", debug=False):
        self.port = port
        self.debug = debug
        self.lock = Lock()
        
        self.ser = serial.Serial(port=self.port, baudrate=19200, bytesize=serial.EIGHTBITS, timeout=2,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        
        
        self.ser.flush()
        
        time.sleep(1)
        
        self.set_serial_control()
        

    def cr_readline(self):
        """
        Custom readline function which reads from the serial port 
        until the carriage return character is found. This function 
        is called by 
        :meth:`write_cmd`
        
        :returns: str. Decoded byte string ending in carriage return
        """
        eol = b'\r'
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.ser.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line).decode()
    
    def write_cmd(self, cmd):
        """Sends command to Seren and queries the device for a response.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        cmd            str         Command to be sent to the power supply over serial
        =============  ==========  ==========================================================
        
        :returns: str. Response from the Seren PSU (Power Supply Unit).
        """
        message = str(cmd)+'\r'
        with self.lock:
            self.ser.flush()
            self.ser.write(message)
            _resp = self.cr_readline()
        if _resp != (b'\r' or b'N\r'):
            return _resp
        else:
            print("write resp: ",_resp)
        
    def emitter_on(self):
        """Enables the RF Output."""
        self.write_cmd("G")
        
    def emitter_off(self):
        """Disables the RF Output."""
        self.write_cmd("S")
    
    def write_forward(self, power):
        """
        Sets the Power Setpoint.
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        power          int         Setpoint power in Watts
        =============  ==========  ==========================================================
        """
        self.write_cmd("{} W".format(int(power))) 
    
    def read_forward(self):
        """
        :returns: String. Forward power output, in Watts, 
        1 to 5 digits, 1-Watt increments.
        """
        resp = self.write_cmd("W?")
        return resp
    
    def read_reflected(self):
        """
        Queries Reflected Power
        :returns: str. Reflected power, where XXXX is the current reflected 
        power, in Watts; length: 4 characters, fixed. Leading zeros are replaced with 
        the blank space character.
        """
        resp = self.write_cmd("R?")
        return resp
    
    def set_serial_control(self):
        """
        Allows PSU to accepts commands via its serial connection
        """
        self.write_cmd("SERIAL")

    def set_front_panel_control(self):
        """
        Allows PSU to accept commands via its physical front panel interface.
        """
        self.write_cmd("PANEL")

    def set_analog_control(self):
        """
        Allows PSU to accept commands via its analog interface.
        
        """ 
        self.write_cmd("ANALOG")

    def close(self):
        """
        Closes serial connection to Seren PSU.
        """
        self.ser.close()
        del self.ser
        
        
        
        
        
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
        

    def cr_readline(self):
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
        message = str(cmd)+'\r'
        with self.lock:
            self.ser.flush()
            self.ser.write(message.encode())
            _resp = self.cr_readline()
        if _resp != (b'\r' or b'N\r'):
            return _resp
        else:
            print(_resp)
        
    def emitter_on(self):
        self.write_cmd("G")
        
    def emitter_off(self):
        self.write_cmd("S")
    
    def write_forward_sp(self, power):
        self.write_cmd("{} W".format(int(power)))
    
    def read_forward(self):
        return self.write_cmd("W?")
    
    def read_reflected(self):
        return self.write_cmd("R?")

    
    def set_serial_control(self):
        self.write_cmd("SERIAL")

    def set_front_panel_control(self):
        self.write_cmd("PANEL")

    def set_analog_control(self):
        self.write_cmd("ANALOG")

    def close(self):
        self.ser.close()
        del self.ser
        
        
        
        
        
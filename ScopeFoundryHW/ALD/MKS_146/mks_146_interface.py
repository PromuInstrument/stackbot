'''
Created on Dec 6, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

import serial
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class MKS_146_Interface(object):
            
    def __init__(self, port="COM3", debug=False):
        self.port = port
        self.debug = debug
        self.lock = Lock()
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.SEVENBITS, timeout=2,
                                 parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
        
        
        self.ser.flush()
        
        time.sleep(1)

#         self.valve_settings={-1: "N",
#                               0: "C", 
#                               1: "O"}

        self.error_messages = {'E111': "Unrecognized Command",
                                'E112': "Inappropriate Command",
                                'E122': "Invalid data field",
                                'E131': "Bad checksum"}
        
    def _readline(self):
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
    
    def read_cmd(self, cmd, param):
        """Formats messages sent to MKS146 as inquiries."""
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        if cmd < 100:
            cmd_header = "0"+str(cmd)
        else:
            cmd_header = str(cmd)
        message = '@'+cmd_header+str(param)+'?\r'
        with self.lock:
            self.ser.flush()
            self.ser.write(message.encode())
            resp = self._readline().split(':')
        print("read_cmd resp:", resp)
        if len(resp) > 1:
            if resp[1].strip()[0:1] == '+':
                value = resp[1].strip()[1:]
            else:
                value = resp[1]
            return value
        else: 
            return resp

    def write_cmd(self, cmd, param, data=None):
        """Formats messages sent to MKS146 as setting writes."""
        if cmd < 100:
            cmd_head = "0"+str(cmd)
        else:
            cmd_head = str(cmd)
        
        if data is not None:
            message = '@'+cmd_head+str(param)+':'+str(data)+'\r'
        else: 
            message = '@'+cmd_head+str(param)+'\r'
        with self.lock:
            self.ser.flush()
            self.ser.write(message.encode())
            _resp = self._readline()

        print("wr_resp", _resp)

    
    def MFC_write_SP(self, param, SP):
        '''Adjusts set point. Param in this function represents the channel number'''
        assert (0.0002 <= SP <= 1.E5)
        self.write_cmd(102, param, SP)

    
    def MFC_read_SP(self, param):
        '''Param is channel number. Note: Original setpoint set to +5 when found.'''
        resp = self.read_cmd(102,param)
        return float(resp)
    
    def MFC_read_flow(self, param):
        """Reads current flow magnitude from MFC flow sensor"""
        resp = self.read_cmd(601,param)
        if self.debug: print("flow stripped", resp[0:6].strip())
        return float(resp)
    
    def MFC_write_valve_status(self, param, valve_status="C"):
        """Sets the valve to Open/Closed/"""
        self.write_cmd(104,param,valve_status)

    
    def MFC_read_valve_status(self, param):
        '''Initially set to 'N' when found.'''
        resp = self.read_cmd(104,param)
        return resp
    
    def _reverse(self, _dict):
        return dict(map(reversed, _dict.items()))
    
    def close(self):
        self.ser.close()
        del self.ser
        

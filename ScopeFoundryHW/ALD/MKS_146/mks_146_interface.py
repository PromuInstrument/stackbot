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
        
    name = 'mks_146_interface'
    
    def __init__(self, port="COM8", debug=False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.SEVENBITS, timeout=1,
                                 parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
        self.ser.flush()
        
        time.sleep(1)
        self.valve_settings={-1: "N",
                              0: "C", 
                              1: "O"}
        self.error_messages = {'E111': "Unrecognized Command",
                                'E112': "Inappropriate Command",
                                'E122': "Invalid data field",
                                'E131': "Bad checksum"}

    def read_cmd_nd(self, cmd, param):
        if self.ser.in_waiting > 0:
            self.ser.flush()
        if cmd < 100:
            cmd_header = "0"+str(cmd)
        else:
            cmd_header = str(cmd)
        message = '@'+cmd_header+str(param)+'?\r'
        self.ser.write(message)
        resp = self.ser.readline().decode()
        if self.debug:
            print("read_cmd sent: {}".format(message))
            if resp[0] == 'E':
                error = resp.strip()
                print(error, self.error_messages)
        return resp.strip()
    
    def read_cmd(self, cmd, param):
        if self.ser.in_waiting > 0:
            self.ser.flush()
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        if cmd < 100:
            cmd_header = "0"+str(cmd)
        else:
            cmd_header = str(cmd)
        message = '@'+cmd_header+str(param)+'?\r'
        self.ser.write(message)
#         cmd_r, resp = self.ser.readline().decode().split(':')
        resp = self.ser.readline()
        print(resp)
        if self.debug:
            print("read_cmd sent: {}".format(message))
            print("cmd_r:", cmd_r, "resp:", resp)
            if resp[0] == 'E':
                error = resp[:-1]
                print(error, self.error_messages)
        return resp.strip()
    
    def write_cmd(self, cmd, param, data=None):
        if self.ser.in_waiting > 0:
            self.ser.flush()
        if cmd < 100:
            cmd_head = "0"+str(cmd)
        else:
            cmd_head = str(cmd)
        
        if data is not None:
            message = '@'+cmd_head+str(param)+':'+str(data)+'\r'
        else: 
            message = '@'+cmd_head+str(param)+'\r'
        self.ser.write(message)
        cmd_r, resp = self.ser.readline().decode().split(':')
        if self.debug:
            print("write_cmd sent: {}".format(message))
            print("cmd_r:", cmd_r, "resp:", resp)
            if resp[0] == 'E':
                error = resp[:-1]
                print(error, self.error_messages)
#         return resp.strip()
    

    def MFC_read_SP(self, param):
        '''Param is channel number. Note: Original setpoint set to +5 when found.'''
        resp = self.read_cmd(102,param)
        return resp
    
    def MFC_write_SP(self, param, SP):
        '''Adjusts set point. Param in this function represents the channel number'''
        assert (0.0002 <= SP <= 1.E5)
        resp = self.write_cmd(102, param, SP)
        if resp != '':
            pass
    
    def MFC_read_flow(self, param):
        resp = self.read_cmd(601,param)
        if resp[0] == "+":
            return float(resp[1:])
        else:
            return float(resp)
        
    def CM_read_pressure(self,param):
        resp = self.read_cmd(601, param)
        if resp[0] == "+":
            return float(resp[1:])
        else: return float(resp)
    
    def MFC_write_valve_status(self, param, valve_open=False):
        data = self.valve_settings[valve_open]
        self.write_cmd(104,param,data)
    
    def MFC_read_valve_status(self, param):
        '''Initially set to 'N' when found.'''
        settings_r = self._reverse(self.valve_settings)
        resp = self.read_cmd(104,param)
        return settings_r[resp]
    
    def autodetect(self):
        config = {'CC': "Cold Cathode",
                'CLN': 'Linear Cap. Man.',
                'C107': 'Type 107 Cap. Man.',
                'C120': 'Type 120 Cap. Man.',
                'CNCN': 'Convection, dual channel',
                'PRCN': 'Pirani/Convection',
                'C': 'Cap. Man. board, no sensor',
                'CN': 'Convection, single channel',
                'CNPR': 'Convection/Pirani',
                'CNTL': 'Control board',
                'AUXO': 'Auxiliary Output board',
                '----': 'Empty slot',
                'PR': 'Pirani, single channel',
                'PRPR': 'Pirani, dual channel',
                'MFC': 'Mass Flow Controller',
                'HCL': 'Hot Cathode, low power',
                'HCH': 'Hot Cathode, high power',
                '1A': 'Thermocouple board'}
        resp = self.read_cmd_nd(704,1)
        sensors = []
        data = resp.strip().split(":")
        for d in data[1:]:
            sensors.append(d)
        for i in range(4):
            resp = self.ser.readline()
            data = resp.strip().split(b":")
            for d in data:
                sensors.append(d.decode())
        while sensors[0] != ('S1' or ''):
            mks.ser.readline()
        output = []
        for i in range(5):
            output.append(config[sensors[2*i+1]])
        return output
    
    def _reverse(self, _dict):
        return dict(map(reversed, _dict.items()))
    
    def close(self):
        self.ser.close()
        del self.ser
        

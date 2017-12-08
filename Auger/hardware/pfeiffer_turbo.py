'''
Created on 10/9/17

@author: Frank Ogletree and Ed Barnard
Controls Pfeiffer turbo pumps through the serial interface
using 'Pfeiffer Vacuum Protocol for "RS-485"'
'''
import serial
import numpy as np
import time
from ScopeFoundry.hardware import HardwareComponent

class TC110Turbo(object):
    
    def __init__(self, port='COM9',debug=False):
        self.debug = debug
        self.timeout = 0.5    
        self.port=port
        self.ser = serial.Serial(port=self.port, baudrate=9600, 
                                    bytesize= serial.EIGHTBITS, parity=serial.PARITY_NONE, 
                                    stopbits=serial.STOPBITS_ONE, timeout=self.timeout)
        

    def close(self):
        self.ser.close()
        
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
        return bytes(line)
        
    def send_recieve_telegram(self,address,action,parameter,data):
        '''
        sends bytestring terminated by \r to 110 Turbo controller, parses return telegram
        and returns response data
        '''
        
        #format command
        length = len(data)

        text = '{address:03d}{action:d}0{parameter:03d}{length:02d}{data}'.format(**locals())
        text = text.encode('ascii')
        chksum = sum(text)&0xFF
        chktext = '{:03d}'.format(chksum)
        chktext = chktext.encode('ascii') + b'\r'
        
        out_telegram = text+chktext
        if self.debug: print("Send to turbo:", repr(out_telegram))
        self.ser.write(out_telegram)
        
        # read back response
        resp_telegram = resp = self._readline()
        if self.debug: print("Receive from turbo:", repr(resp_telegram))
        
        resp_addr = int(resp[0:3])
        resp_parameter = int(resp[5:8])
        resp_data_len = int(resp[8:10])
        resp_data = resp[10:-4]
        
        # check for errors
        if resp_data in [b'NO DEF', b' RANGE', b' LOGIC']:
            raise IOError("Turbo Command Error: {} {}".format(repr(out_telegram), repr(resp_data)))
        
        return resp_data.decode()
 
 
    def read_actual_speed(self, address):
        """309 ActualSpd Active rotation speed (Hz) 1 R Hz 0 999999"""
        resp = self.send_recieve_telegram(address, action=0, parameter=309, data="=?")
        speed = int(resp)
        return speed
        
    def read_drive_power(self, address):
        """316 DrvPower Drive power 1 R W 0 999999"""
        resp = self.send_recieve_telegram(address, action=0, parameter=316, data="=?")
        power = int(resp)
        return power
        

    def read_temp_motor(self, address):
        """346 TempMotor Temperature motor 1 R degC 0 999999"""
        resp = self.send_recieve_telegram(address, action=0, parameter=346, data="=?")
        temp = int(resp)
        return temp
        

class TC110TurboHW(HardwareComponent):
    
    name = 'tc110_turbo'
    
    def setup(self):
        
        self.settings.New('port', dtype=str, initial='COM9')
        
        for turbo_name in ['prep', 'ion', 'nano']:
            #self.settings.New(turbo_name + '_addr', dtype=int)
            self.settings.New(turbo_name + '_speed', dtype=int, ro=True, unit='Hz')
            self.settings.New(turbo_name + '_power', dtype=int, ro=True, unit='W')
            self.settings.New(turbo_name + '_temp', dtype=int, ro=True,  unit='C')
        
        self.channel_lut = dict(
            nano=1,
            prep=2,
            ion=3)
        
        
    def connect(self):
        S = self.settings
        self.dev = TC110Turbo(port=S['port'], debug=S['debug_mode'])
        
        
        for turbo_name, addr in self.channel_lut.items():
            
            self.settings.get_lq(turbo_name + '_speed').connect_to_hardware(
                read_func=lambda address=addr: self.dev.read_actual_speed(address)
                )
            self.settings.get_lq(turbo_name + '_power').connect_to_hardware(
                read_func=lambda address=addr: self.dev.read_drive_power(address)
                )
            self.settings.get_lq(turbo_name + '_temp').connect_to_hardware(
                read_func=lambda address=addr: self.dev.read_temp_motor(address)
                )
            
        self.read_from_hardware()
            
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
    

if __name__ == '__main__':
    
    turbo = TC110Turbo(port='COM9', debug=True)
    
    for i in range(1,4):
        print(i, "Speed", turbo.read_actual_speed(i))
        print(i, "Power", turbo.read_drive_power(i))
        print(i, "Temp", turbo.read_temp_motor(i))
        
    turbo.send_recieve_telegram(2,1, 2, "111111") # standby
    
    turbo.close()
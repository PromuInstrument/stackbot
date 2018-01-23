"""Written by Nick Borys 6/22/2017

"""
from __future__ import division, print_function
import serial
import time
import struct
import io


class LinkamController(object):

    def __init__(self, port="COM7", debug=False, dummy=False): #change port according to device listing in windows.
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:

            #NOTE: Linkam controller uses rtscts flow control, but pySerial does not seem 
            #to properly support it.  When it is enabled, the port just locks up and the
            #computer needs to be restarted.  Eveyrthing seems to work fine with it turned 
            #off, though.
            self.ser = ser = serial.Serial(port=self.port, baudrate=19200, 
                                           bytesize=serial.EIGHTBITS,
                                           parity=serial.PARITY_NONE, 
                                           stopbits=serial.STOPBITS_ONE, 
                                           xonxoff=False, 
                                           timeout=1.0,
                                           rtscts=False)
            
            ser.flush()
            
            # Initialize the controller with default settings
            self.write_pump_mode(False)
            self.write_rate(10)
            self.write_pump_speed(0)
            self.write_limit(25)
            self.update_status()
            
    def close(self):
        self.ser.close()

    def write_cmd(self, cmd):
        self.ser.write(cmd+"\r")
        if self.debug:
            print ('write:', cmd)
        response = self._readline()
        if self.debug:
            print ('response:', repr(response))
        if 'Error' in response:
            raise IOError('Linkam Controller command error: ' + repr(response))
        return response.strip()

    def update_status(self):
        res = self.write_cmd('T')
        if self.debug:
            print(len(res))
        
        # First byte is the status
        status_val = res[0]
        if self.debug:
            print(type(status_val), status_val)
        if status_val == b"\x01":
            self.status = "Stopped"
        elif status_val == b"\x10":
            self.status = "Heating"
        elif status_val == b"\x20":
            self.status = "Cooling"
        elif status_val == b"\x30":
            self.status = "Holding at the limit"
        elif status_val == b"\x40":
            self.status = "Holding the limit time"
        elif status_val == b"\x50":
            self.status = "Holding the current temperature"
        else:            
            self.status = "unknown: " + hex(struct.unpack('>B', res[0])[0])

        # Second byte is the error byte
        eb = struct.unpack('>B', res[1])[0]
        self.error = ""
        if eb & 0x01:
            self.error += 'Cooling rate too fast;'
        if eb & 0x02:
            self.error += 'Open circuit;'
        if eb & 0x04:
            self.error += 'Power surge;'
        if eb & 0x08:
            self.error += 'No exit 300;'
        if eb & 0x10: 
            self.error += 'Both stages;'
        if eb & 0x20:
            self.error += 'Link error;'
        if eb & 0x40:
            self.error += 'NC;'
                
        # Pump speed
        #  < 128: pump speed
        # == 128: pump off
        self.pump_speed = struct.unpack('>B', res[2])[0] - 128
        if self.debug:
            print('pump speed:', self.pump_speed)
        # in auto mode, the speed is offset by 64...must be an extra bit is set;
        # not mentioned in the manual!
        if self.pump_speed >= 64:
            self.pump_speed = self.pump_speed-64
        
        self.general_status = res[3]
        
        # Temperature
        temp_string = res[6:10].decode("utf-8")
        temp = int(temp_string, 16)
        if temp > 15000:
            temp -= 0x00010000
        temp = temp/10
        
        self.temperature =  temp
        
        if self.debug:
            print(temp_string, self.temperature, self.status, self.error)
                
        return res
    
    def read_temperature(self):
        #self.update_status()
        return self.temperature
    
    def read_pump_speed(self):
        #self.update_status()
        return self.pump_speed
    
    def read_status(self):
        #self.update_status()
        return self.status
    
    def read_error(self):
        #self.update_status()
        return self.error
    
    def write_rate(self, rate):  
        # rate in C/min
        
        if rate < 0.01:
            raise ValueError("Rate must be larger than 0.01 C/min")
        
        cmd = "R1{0:.0f}".format(rate*100)
        self.write_cmd(cmd)
        
        self.rate = rate
        return self.rate
    
    def read_rate(self):
        return self.rate
    
    def write_limit(self, limit):
        # limit in C
        
        cmd = "L1{0:.0f}".format(limit*10)
        self.write_cmd(cmd)
        
        self.limit = limit
        return self.limit
    
    def read_limit(self):
        return self.limit
    
        
    def start(self):
        self.write_cmd('S')
    
    def stop(self):
        self.write_cmd('E')
        
    def hold(self):
        self.write_cmd('O')
        
    def write_pump_mode(self, manual_mode):
        if manual_mode:
            self.write_cmd('Pm0')
        else:
            self.write_cmd('Pa0')
        
        self.manual_mode = manual_mode
        return self.manual_mode
    
    def read_pump_mode(self):
        return self.manual_mode
    
    def write_pump_speed(self, pump_speed):
        # pump speed from 0 - 30;
        # 0 --> off;
        # 30 --> max
        
        if pump_speed < 0:
            raise ValueError("Pump speed must be larger than 0")
        elif pump_speed > 30:
            raise ValueError("Pump speed must be smaller than 30")

        speed_char = chr(48+int(pump_speed))
        self.write_cmd('P'+speed_char)
    
    # custom readline to trigger on '\r'
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

if __name__ == '__main__':

    linkam = LinkamController(port='COM7', debug=True)
    
    try:        
        #print('port opened...')
        #time.sleep(10)
        #status = linkam.update_status()
        linkam.write_rate(10.0)
        linkam.write_limit(32.0)
        
        linkam.start()
        
        for i in range(90):
            linkam.update_status()
            time.sleep(1)
        
        linkam.stop()
        
        for i in range(90):
            linkam.update_status()
            time.sleep(1)
    
    except Exception as err:
        print(err)
    finally:
        linkam.close()
        print('port closed')
    

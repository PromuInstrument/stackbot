import serial
import time
import threading

class SierraMFC(object):
    
    def __init__(self, port='COM1', debug=False):
        
        self.port = port
        self.debug = debug
        self.lock = threading.RLock()
        
        self.ser = serial.Serial(self.port, 9600, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE, timeout=5)
        
        self.send_message('!StrmOff')
        # Steam command echos, so we read and dump the echo
        with self.lock:
            resp  = self.ser.read_until(b'\r') 
        
    def close(self):
        self.ser.close()
        
    def send_message(self, message):
        """ Computes CRC and sends message with CRC + CR"""
        crc = calcCRC(message.encode())
        M = message.encode() + (crc) + b'\r'
        if self.debug: print("send_message:", M)
        with self.lock:
            self.ser.write(M)

        
    def read_value(self, cmd):
        with self.lock:
            self.send_message("?"+cmd)
            resp  = self.ser.read_until(b'\r')
        if self.debug: print("resp: " + repr(resp))
        
        resp_crc = resp[-3:-1]
        expected_crc = calcCRC(resp[:-3])
        assert resp_crc == expected_crc
        
        resp = resp[:-3].decode()
        assert resp.startswith(cmd)
        return resp[4:]

    

    def read_serial_number(self):
        return self.read_value("Srnm")
    
    def read_version_number(self):
        return self.read_value("Vern")
    
    def read_flow(self):
        return float(self.read_value("Flow"))
    
    def read_setpoint_flash(self):
        return float(self.read_value("Setf"))
    
    def read_setpoint_ram(self):
        return float(self.read_value("Setr"))
    
    def write_setpoint_ram(self, sp):
        with self.lock:
            self.send_message("!Setr{:.3f}".format(sp))
            # if another command comes faster than 250ms,
            # it will ignore the new set-point
            time.sleep(0.250) 

    
    def read_unit(self):
        i = int(self.read_value("Unti"))
        return UNIT_LIST[i-1]
    
    def read_valve_state(self):
        i = int(self.read_value("Vlvi"))
        return ["Automatic", "Closed", "Purge" ][i-1]
    
    def read_gas(self):
        i = int(self.read_value("Gasi"))
        return GAS_LIST[i-1]


UNIT_LIST = ["scc/s", "scc/m", "scc/H", "Ncc/s", "Ncc/m", "Ncc/H", "SCF/s","SCF/m", "SCF/H", "NM3/s",
             "NM3/m", "NM3/H", "SM3/s", "SM3/m", "SM3/H", "sl/s",  "sl/m", "sl/H",  "NL/s",  "NL/m",
             "NL/H",  "g/s",   "g/m",   "g/H",    "kg/s", "kg/m",  "kg/H", "lb/s",  "lb/m",  "lb/H",]
    
GAS_LIST = ["Air", "Argon", "CO2", "CO", "He", "H", "CH4", "N", "NO", "O"]
        
def calcCRC(cmnd):
    # cmnd is a byte array containing the command ASCII string; example: cmnd=b"Sinv2.000"
    # an unsigned 32 bit integer is returned to the calling program
    # only the lower 16 bits contain the crc
    # (python version returns a byte array with MSB,LSB of CRC

    crc = 0xffff # initialize crc to hex value 0xffff
    
    for char_i in cmnd: # this for loop starts with ASCCII 'S' and loops through to the last ASCII '0'
        #hex_char = (int(ord(character)))
        #hex_char = character
        crc=crc^(char_i*0x0100) # the ASCII value is times by 0x0100 first then XORED to the current crc value
        #for(j=0; j<8; j++) # the crc is hashed 8 times with this for loop
        for j in range(8):
            # if the 15th bit is set (tested by ANDING with hex 0x8000 and testing for 0x8000 result) 
            # then crc is shifted left one bit (same as times 2) XORED with hex 0x1021 and ANDED to 
            # hex 0xffff to limit the crc to lower 16 bits. If the 15th bit is not set then the crc 
            # is shifted left one bit and ANDED with hex 0xffff to limit the crc to lower 16 bits.
            if((crc&0x8000)==0x8000):
                crc=((crc<<1)^0x1021)&0xffff
            else:
                crc=(crc<<1)&0xffff
    # There are some crc values that are not allowed, 0x00 and 0x0d
    # These are byte values so the high byte and the low byte of the crc must be checked and incremented if 
        # the bytes are either 0x00 0r 0x0d
    if((crc&0xff00)==0x0d00):        crc +=0x0100
    if((crc&0x00ff)==0x000d):        crc +=0x0001
    if((crc&0xff00)==0x0000):        crc +=0x0100
    if((crc&0x00ff)==0x0000):        crc +=0x0001
    
    #print(hex(crc))
    return crc.to_bytes(2, 'big')

    # If the string Sinv2.000 is sent through this routine the crc = 0x8f55
    # The complete command "Sinv2.000" will look like this in hex: 
        # 0x53 0x69 0x6E 0x76 0x32 0x2e 0x30 0x30 0x30 0x8f 0x55 0x0d
        
        
if __name__ == '__main__':
    
    mfc = SierraMFC(port='COM4', debug=True)
    print("read_serial_number", mfc.read_serial_number())
    print("read_version_number", mfc.read_version_number())
    print("read_flow", mfc.read_flow())
    print("read_setpoint_flash", mfc.read_setpoint_flash())
    print("read_setpoint_ram", mfc.read_setpoint_ram())
    #mfc.send_message("!Setr23.0")
    #mfc.write_setpoint_ram(23.2343234)
    mfc.write_setpoint_ram(0)
    print("read_setpoint_ram", mfc.read_setpoint_ram())


    print("read_unit", mfc.read_unit())
    
    print("read_valve_state", mfc.read_valve_state())
    
    print("read_gas", mfc.read_gas())
    
    mfc.close()
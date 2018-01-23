import numpy as np
from serial import Serial

class AugerElectronAnalyzer(object):
    
    "Controls Omicron EAC2200 NanoSAM 570 energy analyzer power supply" 
 
    #class constants
    
    #analyzer physical property
    quad_cmds = dict(X1=0x81, Y1=0x82, X2=0x83, Y2=0x84)
    dispersion = 0.02 
    chan_shift = np.array([0.0,-1.0+0.025, +1.0+0.025, -2.0+0.100, +2.0+0.050, -3.0+0.150, +3.0+0.150])
    dead_time = 70.0e-9 #estimate
   
    # State Variables
    work_function = 4.5 #must be defined to calc KE
    CAE_mode=True
    last_mode = None
    KE = 200.0
    pass_energy = 50.0
    crr_ratio = 5.0
    resolution = dispersion * pass_energy
    multiplier_state = False
    quad_value = dict(X1=0.0, Y1=0.0, X2=0.0, Y2=0.0)
            
    def __init__(self, debug=False):        
        self.debug=debug
               
        # prologix usb-gpib
        self.gpib = PrologixGPIB_Omicron("COM8", debug=self.debug)
        
        # Initialize to known state
        self.write_KE(self.KE)
        self.write_state(self.multiplier_state,self.CAE_mode)
        self.write_crr_ratio(self.crr_ratio)
        self.write_pass_energy(self.pass_energy)
        for quad in ['X1', 'Y1', 'X2', 'Y2']:
            self.write_quad(quad, self.quad_value[quad])

    def close(self):
        self.gpib.close()
        
        
        
    def omicron_cmd_encode(self, cmd, val ):
        '''cmd is command number, val is uint 16, format for omicron '''
        # GPIB commands of the form:
        # 0x83|00|1A
        # 3 bytes:
        # first byte is command
        # commands of form with 0b 100x xxxx
        # 2nd,3d bytes contain value
        # except for 0x80 and 0x8000 bits (8, 16)
        # These bits get moved to MSB of the command byte
        # 0000 0000 | p000 0000 | q000 0000
        # to
        # 0pq0 0000 | 0000 0000 | 0000 0000

        cmd &= 0x8f #commands are 0x8#
        v1 = (val & 0xff00)>>8
        v2 = val & 0xff
        if v1 & 0x80:
            cmd |= 0x40
            v1  &= 0x7f
        if v2 & 0x80:
            cmd |= 0x20
            v2  &= 0x7f
        s = b'' + bytes( [cmd, v1, v2])
        return s    
    
    def write_cmd(self, address, cmd_num, value):
        '''cmd is command number, val is uint 16'''
        # prologix usb-gpib
        self.gpib.set_address(address)
        s = self.omicron_cmd_encode(cmd_num, value)
        self.gpib.write(s)
        
    def get_work_function(self):
        return self.work_function
    
    def set_work_function(self, wf):
        self.work_function = float(wf)
    
    def write_KE(self, ke):
        ke = min( max( self.work_function, ke), 2200 + self.work_function)
        self.KE = float(ke)
        ke_int = int( ((ke-self.work_function)/2200.)*65535)
        self.write_cmd(1, 0x82, ke_int)
        self.get_resolution() #depends on KE in CRR mode
    
    def write_KE_binary(self, ke):
        ke_int = int(ke)
        self.write_cmd(1, 0x82, ke_int)

    def get_KE(self):
        return self.KE
    
            
    def dead_time_correct(self, data, period):
        scale = self.dead_time / period
        return data / (1.0 - scale*data)
    
    def get_chan_ke(self, ke, CAE_mode):
        if CAE_mode:
            epass = self.pass_energy
        else:
            epass = ke / self.crr_ratio
        return ke + epass * self.dispersion * np.copy(self.chan_shift)
    
    def write_multiplier(self, state):
        return self.write_state(state, self.CAE_mode)

    def get_multiplier(self):
        return self.multiplier_state

    def write_retarding_mode(self, CAE_mode):
        return self.write_state(self.multiplier_state, CAE_mode)
    
    def get_retarding_mode(self):
        return self.CAE_mode

        #retarding modes
        #command to set CRR ratio and to set pass energy is 'overloaded',
        #only set pass energy in CAE, only set retarding ratio in CRR
        #also one command sets mode switch and multiplier switch
        
    def write_pass_energy(self, epass):
        epass = float(min( 500.0, max( 5.0, epass)))
        self.pass_energy = epass
        if self.CAE_mode:
            val = int(epass*44.69)
            self.write_cmd(1, 0x84, val)
            self.get_resolution()
             
    def current_pass_energy(self):
        if self.CAE_mode:
            return self.pass_energy
        else:
            return self.KE/self.crr_ratio

    def get_resolution(self):
        self.resolution = self.current_pass_energy() * self.dispersion
        return self.resolution

    def get_pass_energy(self):
        return self.pass_energy   

    def write_crr_ratio(self, crr_ratio):
        crr_ratio = min( 20.0, max( 1.5, crr_ratio ))
        self.crr_ratio = crr_ratio
        if not self.CAE_mode:
            val = int(crr_ratio*3276.8)
            self.write_cmd(1, 0x84, val)
            self.get_resolution() 
    
    def get_crr_ratio(self):
        return self.crr_ratio
    
    def write_state(self, multiplier_state, CAE_mode=True):
        # update crr_ratio or pass_energy when retarding mode changes...
        self.multiplier_state = bool(multiplier_state)
        self.CAE_mode = bool(CAE_mode)
        val = 0x0400*bool(self.multiplier_state) + 0x0200*bool(not self.CAE_mode)
        self.write_cmd(1, 0x85, val)
        
        if self.CAE_mode != self.last_mode:
            self.last_mode = self.CAE_mode
            #make sure overloaded resolution command is correct
            self.write_crr_ratio(self.crr_ratio)
            self.write_pass_energy(self.pass_energy)
            self.get_resolution()
        
        
    ####  Quadrupole
    
    quad_cmds = dict(X1=0x81, Y1=0x82, X2=0x83, Y2=0x84)
    quad_index = dict(X1=0, Y1=1, X2=2, Y2=3)
    
    def write_quad(self, quad, val):
        #electronics run 0 to 100, 50 neutral, software -100 to +100 %
        assert quad in self.quad_cmds.keys()
        val = min( 100, max( -100, val ))
        val_int = int((val + 100)*655.35*0.5)
        #print( 'cmd {} val {}'.format(self.quad_cmds[quad],val_int))
        self.write_cmd(3,self.quad_cmds[quad], val_int)
        self.quad_value[quad] = val
        
    # setup procedure
    """
    write multipliers and mode
    set epass or crr_ratio
    set quadrupoles
    set KE
    set Fraction (for sweeps)
    set span (for sweeps)
    """
    
class PrologixGPIB_Omicron(object):
    
    '''>>> import serial
        >>> ser = serial.Serial('/dev/ttyUSB0')  # open serial port'''
    
    
    def __init__(self, port, address=1, debug=False):
        self.port = port
        self.ser = Serial(port, timeout=1.0, writeTimeout = 0)
        self.debug = debug
        self.write_config_gpib()
        self.set_address(address)
        if self.debug:
            self.read_print_config_gpib()
        
    def close(self):
        return self.ser.close()

    def set_address(self, address=1):
        cmd_str = '++addr {:d}\n'.format(address).encode()
        #if self.debug: print("prologix set_addr", repr(cmd_str))
        self.ser.write(cmd_str)

    def write_config_gpib(self):
        '''configure prologix usb GPIB for Omicron'''
        ser = self.ser
        #no automatic read after write
        ser.write(b"++auto 0\n")
        #assert gpib EOI after write
        ser.write(b"++eoi 1\n")
        #no CR, LF after write
        ser.write(b"++eos 3\n")
        #be controller, send to omicron
        ser.write(b"++mode 1\n")
        #no CR, LF with read
        ser.write(b"++eos 3\n")

    def read_print_config_gpib(self):
        ''' get prologix gpib configuration'''
        self.ser.write(b'++ver\n')
        print( self.ser.readline().decode())
        self.ser.write(b"++auto\n")
        print( 'auto '+self.ser.readline().decode())
        self.ser.write(b"++eoi\n")
        print( 'eoi '+self.ser.readline().decode())
        self.ser.write(b"++eos\n")
        print( 'eos '+self.ser.readline().decode())
        self.ser.write(b"++mode\n")
        print( 'mode '+self.ser.readline().decode())
        self.ser.write(b"++addr\n")
        print( 'address '+self.ser.readline().decode())

    def binary_escape_gpib_string( self, s ):
        ''' prevent binary data from being interpreted
        as prologix configuration commands, add lf'''
        #print('binary_escape_gpib_string', repr(s))
        esc = bytes([27])
        lf = b'\n'
        cr = bytes([0xd])
        plus = b'+'
        
        out = bytearray()
        for c in s:
            if bytes([c]) in (esc, lf, cr, plus ):
                out += esc
            out.append(c)
        out += lf
        return out
    
    def write(self, s):
        #s = s.encode()
        #print('write', repr(s))
        out = self.binary_escape_gpib_string(s)
        if self.debug:
            str = "prologix gpib \t" + " ".join(["{:02x}".format(c) for c in s])
            print(str)
            #print("\t", " ".join(["{:08b}".format(c) for c in s]))            
            
        return self.ser.write(out)
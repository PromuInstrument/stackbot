from __future__ import division, print_function
from serial import Serial
import numpy as np
import struct
import time
from _ast import Add

class AugerElectronAnalyzer(object):
    
    "Controls Omicron EAC2200 NanoSAM 570 energy analyzer power supply" 
 
    #class constants
    
    #analyzer physical property
    quad_cmds = dict(X1=0x81, Y1=0x82, X2=0x83, Y2=0x84)
    dispersion = 0.02 
    chan_shift = np.array([0.0,-1.0, +1.0, -2.0, +2.0, -3.0, +3.0])
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
        assert quad in self.quad_cmds.keys()
        val = min( 50, max( -50, val ))
        val_int = int((val + 50)*655.35)
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
 
from ScopeFoundry import HardwareComponent

class AugerElectronAnalyzerHW(HardwareComponent):
    
    name = 'auger_electron_analyzer'

    def setup(self):
        self.settings.New("CAE_mode", dtype=bool, initial = True    )
        self.settings.New("multiplier", dtype=bool, initial = False)
        self.settings.New("KE", dtype=float, unit='eV', vmin=0, vmax=2200, initial = 200)
        self.settings.New("work_function", dtype=float, unit='eV', vmin=0, vmax=10, initial=4.5)
        self.settings.New("pass_energy", dtype=float, unit='V', vmin=5, vmax=500, initial = 100)
        self.settings.New("crr_ratio", dtype=float, vmin=1.5, vmax=20, initial = 5.0)
        self.settings.New("resolution", dtype=float, ro=True, unit='eV')
        quad_lq_settings = dict( dtype=float, vmin=-50, vmax=+50, initial=0, unit='%', si=False)
        self.settings.New("quad_X1", **quad_lq_settings)
        self.settings.New("quad_Y1", **quad_lq_settings)
        self.settings.New("quad_X2", **quad_lq_settings)
        self.settings.New("quad_Y2", **quad_lq_settings)
                          
    def connect(self):
        E = self.analyzer = AugerElectronAnalyzer(debug=self.debug_mode.val)
                
        self.settings.CAE_mode.hardware_read_func = E.get_retarding_mode
        self.settings.CAE_mode.hardware_set_func = E.write_retarding_mode
        
        self.settings.multiplier.hardware_read_func = E.get_multiplier
        self.settings.multiplier.hardware_set_func = E.write_multiplier
        
        self.settings.KE.hardware_read_func = E.get_KE
        self.settings.KE.hardware_set_func  = E.write_KE

        self.settings.work_function.hardware_read_func = E.get_work_function
        self.settings.work_function.hardware_set_func = E.set_work_function
        
        self.settings.pass_energy.hardware_read_func = E.get_pass_energy
        self.settings.pass_energy.hardware_set_func = E.write_pass_energy
        
        self.settings.crr_ratio.hardware_read_func = E.get_crr_ratio
        self.settings.crr_ratio.hardware_set_func = E.write_crr_ratio

        self.settings.resolution.hardware_read_func = E.get_resolution
        
        self.settings.quad_X1.hardware_set_func = lambda val, E=E: E.write_quad('X1', val) 
        self.settings.quad_Y1.hardware_set_func = lambda val, E=E: E.write_quad('Y1', val) 
        self.settings.quad_X2.hardware_set_func = lambda val, E=E: E.write_quad('X2', val) 
        self.settings.quad_Y2.hardware_set_func = lambda val, E=E: E.write_quad('Y2', val)        
        
        for lqname in ['KE', 'pass_energy', 'crr_ratio']:
            getattr(self.settings, lqname).add_listener(self.settings.resolution.read_from_hardware)
    
    def disconnect(self):

        
        # disconnect lq's
        # TODO

        if hasattr(self, 'analyzer'):
            self.analyzer.close()        
            del self.analyzer
        


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
            if c in (esc, lf, cr, plus ):
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

from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class AugerElectronAnalyzerTestApp(BaseMicroscopeApp):
    
    name = 'AugerElectronAnalyzerTestApp'
    
    def setup(self):
        
        AEA = self.add_hardware_component(AugerElectronAnalyzerHW(self))

        self.ui.show()
        
        self.ui_analyzer = load_qt_ui_file(sibling_path(__file__, "auger_electron_analyzer_viewer.ui"))
                
        widget_connections = [
         ('CAE_mode', 'cae_checkBox'),
         ('multiplier', 'multiplier_checkBox'),
         ('KE', 'KE_doubleSpinBox'),
         ('work_function', 'work_func_doubleSpinBox'),
         ('pass_energy', 'pass_energy_doubleSpinBox'),
         ('crr_ratio', 'crr_ratio_doubleSpinBox'),
         ('resolution', 'resolution_doubleSpinBox'),
         ('quad_X1', 'qX1_doubleSpinBox'),
         ('quad_Y1', 'qY1_doubleSpinBox'),
         ('quad_X2', 'qX2_doubleSpinBox'),
         ('quad_Y2', 'qY2_doubleSpinBox'),
         ]
        for lq_name, widget_name in widget_connections:
            AEA.settings.get_lq(lq_name).connect_bidir_to_widget(getattr(self.ui_analyzer, widget_name))
        
        #self.ui_analyzer.show()
        self.ui.centralwidget.layout().addWidget(self.ui_analyzer)
        self.ui.setWindowTitle(self.name)
        AEA.settings['debug_mode'] = True
        AEA.settings.connected.update_value(True)
        
if __name__ == '__main__':
    app = AugerElectronAnalyzerTestApp([])
    app.exec_()
    

    
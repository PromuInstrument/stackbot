from __future__ import division, print_function
from serial import Serial
import struct
import time
from _ast import Add

class AugerElectronAnalyzer(object):
    
    "Omicron EAC2200 NanoSAM 570" "Electron Analyser Control"
    "Omicron Multiplier Supplies 1127"
    "Omicron Mulit-channel receiver 538"
    
    def __init__(self, debug=False):
        
        self.debug=debug
        
        
        # prologix usb-gpib
        self.gpib = PrologixGPIB_Omicron("COM8", debug=self.debug)

        # Initialize to known state
        self.retarding_mode='CAE'
        self.KE_V = 0.0
        self.set_work_function(4.5)
        self.write_multiplier_state(False)
        self.write_crr_ratio(1.5)
        self.write_pass_energy(5.0)
        self.write_KE(0.0)
        for quad in ['X1', 'Y1', 'X2', 'Y2']:
            self.write_Quad(quad, 0.0)
        
        
        
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
    
    def write_KE(self, ke_v):
        assert 0 <= ke_v <= 2200
        self.KE_V = float(ke_v)
        ke_int = int( ((ke_v-self.work_function)/2200.)*65535)
        if self.retarding_mode == 'CRR':
            self.resolution_eV = self.KE_V/self.crr_ratio * 0.02
        self.write_cmd(1, 0x82, ke_int)
    
    def get_KE(self):
        return self.KE_V
    
    retarding_modes = dict(CAE=0, CRR=1)

    def write_state(self, multiplier_state, retarding_mode='CAE'):
        self.multiplier_state = bool(multiplier_state)
        assert retarding_mode in self.retarding_modes.keys()
        self.retarding_mode = retarding_mode
        val = 0x0400*bool(multiplier_state) + 0x0200*self.retarding_modes[retarding_mode]
        self.write_cmd(1, 0x85, val)
        
        # Alternate method
        # state is a special command that can be only 2 bytes long (instead of 3)
        #val = 0x04*bool(multiplier_state) + 0x02*self.retarding_modes[retarding_mode]
        #self.gpib.set_address(1)
        #self.gpib.write(b"\x85" + chr(val))


    def write_multiplier_state(self, state):
        return self.write_state(state, self.retarding_mode)

    def get_multiplier_state(self):
        return self.multiplier_state

    def write_retarding_mode(self, retarding_mode):
        return self.write_state(self.multiplier_state, retarding_mode)
    
    def get_retarding_mode(self):
        return self.retarding_mode


    # CAE 
    def write_pass_energy(self, epass):
        assert 5.0 <= epass <= 500
        self.pass_energy = float(epass)
        val = int(float(epass)*44.69)
        self.resolution_eV = 0.02*epass
        self.write_cmd(1, 0x84, val)
    
    def get_pass_energy(self):
        return self.pass_energy
    
    # CRR
    def write_crr_ratio(self, crr_ratio):
        assert 1.5 <= crr_ratio <= 20.0
        self.crr_ratio = crr_ratio
        val = int(crr_ratio*3276.8)
        self.resolution_eV = self.KE_V/self.crr_ratio * 0.02
        self.write_cmd(1, 0x84, val)
    
    def get_crr_ratio(self):
        return self.crr_ratio
    
    def get_resolution(self):
        return self.resolution_eV
 
    ####  Quadrupole
    
    quad_cmds = dict(X1=0x81, Y1=0x82, X2=0x83, Y2=0x84)
    
    def write_Quad(self, quad, val):
        assert quad in self.quad_cmds.keys()
        assert -50 <= val <= 50
        val_int = int((val + 50)*655.35)
        self.write_cmd(3,self.quad_cmds[quad], val_int)
        
    def write_Quad_X1(self,val):
        return self.write_Quad('X1', val)
    
    def close(self):
        self.gpib.close()
        
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
        self.settings.New("mode", dtype=str, choices=('CAE', 'CRR'))
        self.settings.New("multiplier", dtype=bool)
        self.settings.New("KE", dtype=float, unit='eV', vmin=0, vmax=2200)
        self.settings.New("work_function", dtype=float, unit='eV', vmin=0, vmax=10, initial=4.5)
        self.settings.New("pass_energy", dtype=float, unit='V', vmin=5, vmax=500)
        self.settings.New("crr_ratio", dtype=float, vmin=1.5, vmax=20)
        self.settings.New("resolution", dtype=float, ro=True, unit='eV')
        quad_lq_settings = dict( dtype=float, vmin=-50, vmax=+50, initial=0, unit='%%', si=False)
        self.settings.New("quad_X1", **quad_lq_settings)
        self.settings.New("quad_Y1", **quad_lq_settings)
        self.settings.New("quad_X2", **quad_lq_settings)
        self.settings.New("quad_Y2", **quad_lq_settings)
                          
    def connect(self):
        E = self.e_analyzer = AugerElectronAnalyzer(debug=self.debug_mode.val)
        
        self.settings.mode.hardware_read_func = E.get_retarding_mode
        self.settings.mode.hardware_set_func = E.write_retarding_mode
        
        self.settings.multiplier.hardware_read_func = E.get_multiplier_state
        self.settings.multiplier.hardware_set_func = E.write_multiplier_state
        
        self.settings.KE.hardware_read_func = E.get_KE
        self.settings.KE.hardware_set_func  = E.write_KE

        self.settings.work_function.hardware_read_func = E.get_work_function
        self.settings.work_function.hardware_set_func = E.set_work_function
        
        self.settings.pass_energy.hardware_read_func = E.get_pass_energy
        self.settings.pass_energy.hardware_set_func = E.write_pass_energy
        
        self.settings.crr_ratio.hardware_read_func = E.get_crr_ratio
        self.settings.crr_ratio.hardware_set_func = E.write_crr_ratio

        self.settings.resolution.hardware_read_func = E.get_resolution
        
        print("setting quad hardware_set_funcs")
        self.settings.quad_X1.hardware_set_func = lambda val, E=E: E.write_Quad('X1', val) 
        self.settings.quad_Y1.hardware_set_func = lambda val, E=E: E.write_Quad('Y1', val) 
        self.settings.quad_X2.hardware_set_func = lambda val, E=E: E.write_Quad('X2', val) 
        self.settings.quad_Y2.hardware_set_func = lambda val, E=E: E.write_Quad('Y2', val) 
        print("done quad hardware_set_funcs")
        
        
        for lqname in ['KE', 'pass_energy', 'crr_ratio']:
            getattr(self.settings, lqname).add_listener(self.settings.resolution.read_from_hardware)
    
    def disconnect(self):
        self.settings['multiplier'] = False
        self.e_analyzer.close()
        
        # disconnect lq's
        # TODO
        
        del self.e_analyzer
        


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
        if self.debug: print("prologix set_addr", repr(cmd_str))
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
        print('binary_escape_gpib_string', repr(s))
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
        print('write', repr(s))
        out = self.binary_escape_gpib_string(s)
        if self.debug:
            print("prologix write")
            print("\t", " ".join(["{:02x}".format(c) for c in s]))
            print("\t", " ".join(["{:08b}".format(c) for c in s]))            
            print("\n")
            
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
         ('mode', 'retarding_mode_comboBox'),
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
    
    """a = AugerElectronAnalyzer(debug=True)
    
    a.write_state(True, 'CAE')
    a.write_KE(2200)
    time.sleep(10)
    a.write_multiplier_state(False)
    
    a.close()
    """
    
    """
    write_gpib( port, set_mode_omicron(True, False) )
    write_gpib( port, set_omicron_volts( 1500 ))
    write_gpib( port, set_omicron_volts( 37.5 ))
    write_gpib( port, set_omicron_volts( 137.5 ))
    write_gpib( port, set_omicron_volts( 2200 ))
    time.sleep(10)
    write_gpib( port, set_mode_omicron(mult=False) )
    
    port.close()
    """
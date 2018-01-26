'''
Created on Jan 26, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''
from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ALD.Seren import seren_interface

class Seren_HW(HardwareComponent):
    
    name = 'seren_hw'
    
    def setup(self):
        self.settings.New(name="port", initial="COM7", dtype=str, ro=False)
        self.settings.New(name="enable_serial", initial=True, dtype=bool, ro=False)
        self.settings.New(name="forward_power", initial=0, dtype=int, ro=False)
        self.settings.New(name="reflected_power", initial=0, dtype=int, ro=True)
        self.settings.New(name="RF_enable", initial=False, dtype=bool, ro=False)
        
        self.seren = None
        
    def connect(self):
        self.seren = seren_interface(port=self.settings.port.val, debug=self.settings['debug'])
        
        self.settings.enable_serial.connect_to_hardware(write_func=lambda x: self.serial_toggle(x))
        
        self.settings.RF_enable.connect_to_hardware(write_func=lambda x: self.RF_toggle(x))
        
        self.settings.forward_power.connect_to_hardware(write_func=lambda x: self.write_fp_sp(x),
                                                        read_func=self.read_fp_sp)

        self.settings.reflected_power.connect_to_hardware(read_func=self.read_rp_sp)

    def serial_toggle(self, status):
        if status:
            self.seren.set_serial_control()
        else:
            self.seren.set_front_panel_control()
    
    def RF_toggle(self, status):
        if status:
            self.seren.emitter_on()
        else:
            self.seren.emitter_off()
    
    def write_fp_sp(self, power):
        self.seren.write_forward_sp(power)
    
    def read_fp_sp(self):
        self.seren.read_forward()
    
    def read_rp_sp(self):
        self.seren.read_reflected()
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if self.seren is not None:
            self.seren.close()
        del self.seren
    
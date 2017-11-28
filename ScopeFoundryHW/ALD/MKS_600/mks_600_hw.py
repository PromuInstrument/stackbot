'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ALD.MKS_600.mks_600_interface import MKS_600_Interface

class MKS_600_Hardware(HardwareComponent):
    
    name = "mks_600_hw"
    
    def setup(self):
        self.settings.New(name="port", initial="COM9", dtype=str, ro=False)
        self.settings.New(name="pressure", initial=0.0, fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="units", initial="mbar", dtype=str, ro=True)
        self.settings.New(name="valve_position", initial=0.0, dtype=float, ro=True)
        self.settings.New(name="valve_open", initial=False, dtype=bool, ro=False)
        self.mks = None
    
    def connect(self):
        self.mks = MKS_600_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.pressure.connect_to_hardware(read_func=self.read_pressure)
        self.settings.units.connect_to_hardware(read_func=self.read_units)
        self.settings.valve_position.connect_to_hardware(read_func=self.read_valve)
        self.settings.valve_open.connect_to_hardware(write_func=lambda x: self.set_valve(x))
        
    def read_pressure(self):
        return self.mks.read_pressure()
    
    def read_units(self):
        return self.mks.read_pressure_units()
    
    def read_valve(self):
        return self.mks.read_valve()
    
    def set_valve(self, valve):
        if valve:
            return self.mks.open_valve()
        else:
            return self.mks.close_valve()

    
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if self.mks is not None:
            self.mks.close()
        del self.mks
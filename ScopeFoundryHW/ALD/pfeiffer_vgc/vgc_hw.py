'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ALD.pfeiffer_vgc.vgc_interface import vgc_interface

class VGC_Hardware(HardwareComponent):
    
    name = "vgc_hw"
    
    def setup(self):
        self.settings.New(name="port", initial="COM3", dtype=str, ro=False)
        self.settings.New(name="ch1_pressure", initial=0.0, dtype=float, ro=True)
        self.settings.New(name="ch1_units", initial="mbar", dtype=str, ro=True)
        self.settings.New(name="ch1_sensor_type", initial="None", dtype=str,  ro=True)
        
        self.vgc = None
        
    def connect(self):
        self.vgc = vgc_interface(port=self.settings.port.val, debug=self.settings['debug_mode'])

        self.settings.ch1_pressure.connect_to_hardware(read_func=getattr(self,'read_ch1_pressure'))
        
        self.settings.ch1_sensor_type.connect_to_hardware(read_func=getattr(self, 'read_ch1_sensor_type'))
        
        
        
    def read_ch1_pressure(self):
        sensor = 1
        return self.vgc.read_sensor(sensor)
    
    def read_ch1_sensor_type(self):
        channel = 0
        return self.vgc.sensor_type()[channel]
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if self.vgc is not None:
            self.vgc.close()
        del self.vgc
        
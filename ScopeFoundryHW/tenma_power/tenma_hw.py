'''
Created on Jul 7, 2017

@author: Alan Buckley
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.tenma_power.tenma_dev import TenmaDev

class TenmaHW(HardwareComponent):
    
    name = 'tenma_hw'
    
    def setup(self):
        self.settings.New(name='port', initial='COM5', dtype=str, ro=False)
        
        self.settings.New(name='actual_voltage', initial=0, dtype=float, ro=True)
        
        self.settings.New(name='reported_set_voltage', initial=0, dtype=float, ro=True)
        
        self.settings.New(name='set_voltage', initial=0, dtype=float, ro=False)
        
        self.settings.New(name='actual_current', initial=0, dtype=float, ro=True)
        
        self.settings.New(name='reported_set_current', initial=0, dtype=float, ro=True)
        
        self.settings.New(name='set_current', initial=0, dtype=float, ro=False)
        
        self.settings.New(name='device_name', initial='', dtype=str, ro=True)
        
        self.settings.New(name='OCP', initial=False, dtype=bool, ro=True)
        
        self.settings.New(name='CV_mode', initial=False, dtype=bool, ro=True)
        
        self.settings.New(name='CC_mode', initial=False, dtype=bool, ro=True)
        
        self.settings.New(name='lock', initial=False, dtype=bool, ro=False)
        
        self.settings.New(name='output', initial=False, dtype=bool, ro=True)
        
    def connect(self):
        self.tenma = TenmaDev(port=self.settings['port'], debug=self.settings['debug_mode'])
        
        self.settings.actual_voltage.connect_to_hardware(read_func=self.tenma.read_actual_voltage)
        self.settings.reported_set_voltage.connect_to_hardware(read_func=self.tenma.read_set_voltage)
        self.settings.set_voltage.connect_to_hardware(write_func=lambda x: self.tenma.write_voltage(x))
        self.settings.actual_current.connect_to_hardware(read_func=self.tenma.read_actual_current)
        self.settings.reported_set_current.connect_to_hardware(read_func=self.tenma.read_set_voltage)
        self.settings.set_current.connect_to_hardware(write_func=lambda x: self.tenma.write_current(x))
        self.settings.device_name.connect_to_hardware(read_func=self.tenma.read_device_name)
        self.settings.OCP.connect_to_hardware(write_func=lambda x: self.tenma.write_ocp(x))
        self.settings.lock.connect_to_hardware(write_func=lambda x: self.tenma.lock(x))
        
    def parse_status(self):
        resp = self.tenma.get_status()
        for i, j in self.tenma.status_dict:
            if resp & i:
                self.settings['{}'.format(j)] = True
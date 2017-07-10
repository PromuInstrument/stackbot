'''
Created on Jul 7, 2017

@author: Alan Buckley
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.tenma_power.tenma_dev import TenmaDev
import time


class TenmaHW(HardwareComponent):
    
    name = 'tenma_hw'
    
    def setup(self):
        self.settings.New(name='port', initial='COM5', dtype=str, ro=False)
        
        self.settings.New(name='actual_voltage', initial=0, dtype=float, fmt='%5.2f', ro=True)
        
        self.settings.New(name='set_voltage', initial=0, dtype=float, fmt='%5.2f', ro=False)
        
        self.settings.New(name='actual_current', initial=0, dtype=float, fmt='%1.3f', spinbox_decimals=3, ro=True)
        
        self.settings.New(name='set_current', initial=0, dtype=float, fmt='%1.3f', spinbox_decimals=3, ro=False)
        
        self.settings.New(name='device_name', initial='', dtype=str, ro=True)
        
#         self.settings.New(name='OCP', initial=False, dtype=bool, ro=False)
        
        self.settings.New(name='CV_mode', initial=False, dtype=bool, ro=True)
        
        self.settings.New(name='CC_mode', initial=False, dtype=bool, ro=True)
        
        self.settings.New(name='lock', initial=False, dtype=bool, ro=False)
        
        self.settings.New(name='output', initial=False, dtype=bool, ro=True)
    
        self.add_operation(name='zero_current', op_func=self.zero_current)
        self.add_operation(name='zero_voltage', op_func=self.zero_voltage)
        self.add_operation(name='zero_both', op_func=self.zero_both)


    def connect(self):
        self.tenma = TenmaDev(port=self.settings['port'], debug=self.settings['debug_mode'])
        
        self.settings.actual_voltage.connect_to_hardware(read_func=self.tenma.read_actual_voltage)
        
        self.settings.set_voltage.connect_to_hardware(write_func=lambda x: self.tenma.write_voltage(x),
                                                      read_func=self.tenma.read_set_voltage)
        
        
        self.settings.actual_current.connect_to_hardware(read_func=self.tenma.read_actual_current)
        
        self.settings.set_current.connect_to_hardware(write_func=lambda x: self.tenma.write_current(x),
                                                      read_func=self.tenma.read_set_current)
        
        self.settings.device_name.connect_to_hardware(read_func=self.tenma.read_device_name)

        self.settings.CV_mode.connect_to_hardware(read_func=self.read_cv)
        
        self.settings.CC_mode.connect_to_hardware(read_func=self.read_cc)
        
        self.settings.output.connect_to_hardware(read_func=self.read_output)
        
        self.settings.lock.connect_to_hardware(write_func=lambda x: self.tenma.lock(x))



#         self.settings.OCP.connect_to_hardware(write_func=lambda x: self.tenma.write_ocp(x))

    def zero_current(self):
        self.tenma.write_current(0)
        time.sleep(0.2)
        self.read_from_hardware()
        
    def zero_voltage(self):
        self.tenma.write_voltage(0)
        time.sleep(0.35)
        self.read_from_hardware()
        
    def zero_both(self):
        self.tenma.write_voltage(0)
        self.tenma.write_current(0)
        time.sleep(0.25)
        self.read_from_hardware()

    def read_cv(self):
        resp = self.tenma.get_status()
        return bool(0b0000001 & ord(resp))

        
    def read_cc(self):
        resp = self.tenma.get_status()
        return not bool(0b0000001 & ord(resp))

    def read_output(self):
        resp = self.tenma.get_status()
        return bool(0b1000000 & ord(resp))
        
    def disconnect(self):
        self.tenma.close()
        
    
'''
Created on 31.08.2014

@author: Benedikt
'''
from ScopeFoundry import HardwareComponent

try:
    from .keithley_sourcemeter_interface import KeithleySourceMeter
except Exception as err:
    print("Cannot load required modules for Keithley SourceMeter:", err)


class KeithleySourceMeterComponent(HardwareComponent): #object-->HardwareComponent
    
    name = 'keithley_sourcemeter'
    debug = False
    
    def setup(self):
        self.debug = True
        
        self.port = self.settings.New('port', dtype=str, initial='COM21')
        
        
        self.voltage = self.V_a = self.settings.New('V_a', unit='V', ro=True, si=True)
        self.current = self.I_a = self.settings.New('I_a', unit='A', ro=True, si=True)
        
        self.source_V_a = self.settings.New('source_V_a', unit='V', spinbox_decimals = 6)
        self.source_I_a = self.settings.New('source_I_a', unit='A', spinbox_decimals = 6)
        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        self.keithley = KeithleySourceMeter(port=self.port.val, debug=True)
        
        # connect logged quantities
        self.V_a.connect_to_hardware(lambda:self.keithley.read_I('a'),None)
        self.I_a.connect_to_hardware(lambda:self.keithley.read_I('a'),None)
        
        self.source_I_a.connect_to_hardware(None,lambda I:self.keithley.source_I(I,'a'),)
        self.source_V_a.connect_to_hardware(None,lambda V:self.keithley.source_V(V,'a'),)
        
        print('connected to ',self.name)
    

    def disconnect(self):
        #disconnect hardware
        if hasattr(self, 'keithley'):
            self.keithley.write_output_on(False, channel='a')
            self.keithley.write_output_on(False, channel='b')
            self.keithley.close()
        
            # clean up hardware object
            del self.keithley
        
        print('disconnected ',self.name)

 
        

        


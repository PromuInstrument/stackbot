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
        
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM21')
        
        self.voltage = self.add_logged_quantity('v', dtype=float, unit='V', ro=True, si=True)
        self.current = self.add_logged_quantity('i', dtype=float, unit='A', ro=True, si=True)
        
        
    def connect(self):
        if self.debug: print("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        self.keithley = KeithleySourceMeter(port=self.port.val, debug=True)
        
        # connect logged quantities
        self.voltage.hardware_read_func = \
            self.keithley.getV_A
        self.current.hardware_read_func = \
            self.keithley.getI_A
        
        print('connected to ',self.name)
    

    def disconnect(self):

        # disconnect logged quantities from hardware
        # ///\
    
        #disconnect hardware
        self.keithley.close()
        
        # clean up hardware object
        del self.keithley
        
        print('disconnected ',self.name)
        
        
        
        

        


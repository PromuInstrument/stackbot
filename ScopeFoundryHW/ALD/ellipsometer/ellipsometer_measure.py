'''
Created on Jul 17, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''
from ScopeFoundry import Measurement
import time

class Ellipsometer_Measure(Measurement):
    
    name = "ellipsometer_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):

        self.ui_enabled = False
        if self.ui_enabled:
            self.ui_setup()   
            
        if hasattr(self.app.hardware, 'ellipsometer_hw'):
            self.ellipsometer = self.app.hardware['ellipsometer_hw']
        else:
            print('Ellipsometer hardware object not created.')
    
    def ui_setup(self): 
        pass       
    
    def run(self):
        dt=0.2
        while not self.interrupt_measurement_called:
            self.ellipsometer.poll()
            time.sleep(dt)
'''
Created on Aug 31, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
import time 

class NI_MFC_Measure(Measurement):
    
    name = "ni_mfc_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        self.adc = self.app.hardware['ni_mfc']
        
    def run(self):
        dt=0.1
        while not self.interrupt_measurement_called:
            time.sleep(dt)
            self.adc.read_from_hardware()
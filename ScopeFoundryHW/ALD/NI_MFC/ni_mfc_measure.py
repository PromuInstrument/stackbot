'''
Created on Aug 31, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
import time 

class NI_MFC_Measure(Measurement):
    
    """
    Measurement module for use with National Instruments USB-6001 DAQ card.
    
    This measurement module:
    
    * Connects to lower level hardware component
    * Runs a loop responsible for refreshing hardware component \
        data such that the user can read updated values in realtime.
    """
    
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
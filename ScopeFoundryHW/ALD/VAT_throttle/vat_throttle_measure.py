'''
Created on Dec 19, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
import time

class VAT_Throttle_Measure(Measurement):
    """
    VAT Throttle measurement module.
    
    This module refreshes *LoggedQuantities* at a regular interval when started.
    
    """
    name = "vat_throttle_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        """
        Establishes link to Hardware level component.
        """
        if hasattr(self.app.hardware, 'vat_throttle_hw'):
            self.vat_hw = self.app.hardware['vat_throttle_hw']
        else:
            print('VAT Throttle hardware object not created.')
    
    def run(self):
        dt=0.2
        while not self.interrupt_measurement_called:
            self.vat_hw.read_from_hardware()
            time.sleep(dt)
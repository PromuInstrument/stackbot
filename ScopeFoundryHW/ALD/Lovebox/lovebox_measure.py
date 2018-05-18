'''
Created on Feb 6, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
                        
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time 

class LoveboxMeasure(Measurement):
    
    name = "lovebox"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        self.lovebox = self.app.hardware['lovebox']
        
    def run(self):
        dt=0.1
        while not self.interrupt_measurement_called:
            time.sleep(dt)
            self.lovebox.read_from_hardware()
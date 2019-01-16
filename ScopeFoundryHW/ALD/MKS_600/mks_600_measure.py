'''
Created on Nov 21, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time 

class MKS_600_Measure(Measurement):
    
    name = "mks_600_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):

        self.ui_enabled = False
        if self.ui_enabled:        
            self.ui = QtWidgets.QWidget()
            self.layout = QtWidgets.QVBoxLayout()
            self.ui.setLayout(self.layout)
    
        self.mks = self.app.hardware['mks_600_hw']
        
    def run(self):
        dt=0.25
        while not self.interrupt_measurement_called:
            time.sleep(dt)
            self.mks.read_from_hardware()
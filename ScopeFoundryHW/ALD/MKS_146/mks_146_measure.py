'''
Created on Dec 7, 2017

@author: Alan Buckley    <alanbuckley@lbl.gov>
                         <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time 

class MKS_146_Measure(Measurement):
    
    name = "mks_146_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.setLayout(self.layout)
    
        self.mks = self.app.hardware['mks_146_hw']
        
    def run(self):
        dt=0.05
        while not self.interrupt_measurement_called:
            self.mks.settings.MFC1_flow.read_from_hardware()
            time.sleep(dt)
            self.mks.settings.MFC2_flow.read_from_hardware()
            time.sleep(dt)
            self.mks.settings.MFC1_SP.read_from_hardware()
            time.sleep(dt)
            self.mks.settings.MFC2_SP.read_from_hardware()
            time.sleep(dt)
'''
Created on Feb 6, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
                        
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time 

class OmegaMeasure(Measurement):
    
    name = "omega"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.setLayout(self.layout)
    
        self.omega = self.app.hardware['omega']
        
    def run(self):
        dt=0.1
        while not self.interrupt_measurement_called:
            time.sleep(dt)
            self.omega.read_from_hardware()
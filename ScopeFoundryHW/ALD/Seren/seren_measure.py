'''
Created on Jan 26, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time

class Seren_Measure(Measurement):
    
    name = "seren_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.setLayout(self.layout)
    
        self.seren_hw = self.app.hardware['seren_hw']
        
    def run(self):
        dt = 0.05
        while not self.interrupt_measurement_called:
            self.seren_hw.settings.forward_power.read_from_hardware()
            time.sleep(dt)
            self.seren_hw.settings.reflected_power.read_from_hardware()
            time.sleep(dt)
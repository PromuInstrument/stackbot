'''
Created on Jan 26, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import time

class Seren(Measurement):
    
    name = "seren"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.psu_connected = None
        if hasattr(self.app.hardware, 'seren'):
            self.seren = self.app.hardware['seren_hw']
            self.psu_check()
        else:
            print('Seren hardware component not connected.')
        
        self.ui_enabled = False
        
        if self.ui_enabled:
            self.ui = QtWidgets.QWidget()
            self.layout = QtWidgets.QVBoxLayout()
            self.ui.setLayout(self.layout)
    
    def psu_check(self):
        if hasattr(self.seren, 'seren'):
            resp = self.seren.seren.write_cmd('R')
            if resp == '':
                self.psu_connected = False
            else:
                self.psu_connected = True
        else:
            print('Seren serial object not created. Try connecting HW component.')
        
        
    def run(self):
        dt = 0.1
        while not self.interrupt_measurement_called:
            if self.psu_connected:
                self.seren_hw.settings.forward_power.read_from_hardware()
                time.sleep(dt)
                self.seren_hw.settings.reflected_power.read_from_hardware()
                time.sleep(dt)
            else:
                break
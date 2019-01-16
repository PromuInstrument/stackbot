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
        if hasattr(self.app.hardware, 'seren_hw'):
            self.seren = self.app.hardware['seren_hw']
        else:
            print('Seren hardware component not connected.')
        
        self.ui_enabled = False
        
        if self.ui_enabled:
            self.ui = QtWidgets.QWidget()
            self.layout = QtWidgets.QVBoxLayout()
            self.ui.setLayout(self.layout)
    
    def psu_check(self):
        """
        Checks for connectivity between host computer and Seren Power Supply Unit.
        """
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
            self.seren.settings.forward_power_readout.read_from_hardware()
            time.sleep(dt)
            self.seren.settings.reflected_power.read_from_hardware()
            time.sleep(dt)

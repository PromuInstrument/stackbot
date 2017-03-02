'''
Created on Feb 8, 2017

@author: Alan Buckley
'''
from __future__ import absolute_import, print_function, division
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time

class RelayArduinoOptimizer(Measurement):
    
    name = "relay_arduino_optimizer"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "relay_widget.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        Measurement.__init__(self, app)
        self.dt = 0.1
    
    def setup(self):
        self.app
        self.hw = self.app.hardware['relay_arduino_hw']
        
        self.hw.relay1.connect_to_widget(self.ui.relay1_cbox)
        
        self.hw.relay2.connect_to_widget(self.ui.relay2_cbox)
        
        self.hw.relay3.connect_to_widget(self.ui.relay3_cbox)
        
        self.hw.relay4.connect_to_widget(self.ui.relay4_cbox)
        
    def run(self):
#         while not self.interrupt_measurement_called:
#             time.sleep(self.dt)
        pass

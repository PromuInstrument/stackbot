'''
Created on Jan 31, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                         <alanbuckley@berkeley.edu>

'''
from __future__ import absolute_import, print_function, division
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time

class ALDRelayMeasure(Measurement):
    
    name = "ald_relay_measure"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "relay_widget.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        Measurement.__init__(self, app)
        self.dt = 0.1
    
    def setup(self):

        self.hw = self.app.hardware['ald_relay_hw']
        
        self.hw.settings.relay1.connect_to_widget(self.ui.relay1_cbox)
        
        self.hw.settings.relay2.connect_to_widget(self.ui.relay2_cbox)
        
        self.hw.settings.relay3.connect_to_widget(self.ui.relay3_cbox)
        
        self.hw.settings.relay4.connect_to_widget(self.ui.relay4_cbox)
        
    def run(self):
        while not self.interrupt_measurement_called:
            self.hw.populate()
            time.sleep(self.dt)
'''
Created on Feb 2, 2018

@author: Alan Buckley     <alanbuckley@lbl.gov>
                            <alanbuckley@berkeley.edu>
                            
'''

from ScopeFoundryHW.ALD.CN7500.omega_pid_controller import OmegaPIDController
from ScopeFoundry import HardwareComponent

class OmegaHW(HardwareComponent):
    
    name = 'omega_hw'
    
    def setup(self):
        self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
        self.settings.New(name='pv_temp', initial=0.0, dtype=float, spinbox_decimals=1)
        self.settings.New(name='sv_set_point', initial=0.0, dtype=float, spinbox_decimals=1)
        
    def connect(self):
        self.omega = OmegaPIDController(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'omega'):
            self.omega.close()
            del self.omega
        
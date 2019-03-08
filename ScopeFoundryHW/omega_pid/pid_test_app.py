from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.omega_pid.omega_pid_hw import OmegaPIDHW


class OmegaPIDTestApp(BaseMicroscopeApp):
    
    name = 'omega_pid_test_app'
    
    
    def setup(self):
        
        pid1 = self.add_hardware(OmegaPIDHW(self))
        pid2 = self.add_hardware(OmegaPIDHW(self, name='pid_2'))
        
        pid2.settings['port'] = 'hw:' + pid1.name
        pid2.settings['address'] = 2
        

if __name__ == '__main__':
    
    app = OmegaPIDTestApp()
    app.exec_()
from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.sierra_mfc.sierra_mfc import SierraMFC
import time

class SierraMFC_HW(HardwareComponent):
    
    name = 'sierra_mfc'
    
    def setup(self):
        
        self.settings.New("flow", dtype=float, ro=True)
        self.settings.New("setpoint", dtype=float, ro=False)
        self.settings.New("valve_state", dtype=str, ro=True)#, choices=("Automatic", "Closed", "Purge" ))
        self.settings.New("unit", dtype=str, ro=True)
        self.settings.New("gas", dtype=str, ro=True)
        self.settings.New("port", dtype=str, initial='COM3')
        
    def connect(self):
        S = self.settings
        mfc = self.dev  = SierraMFC(port=S['port'], debug=S['debug_mode'])
        
        S['valve_state'] = mfc.read_valve_state()
        S['unit']  = mfc.read_unit()
        S['gas'] = mfc.read_gas()
        
        S.flow.connect_to_hardware(
            read_func = mfc.read_flow)
        
        S.setpoint.connect_to_hardware(
            read_func = mfc.read_setpoint_ram,
            write_func = mfc.write_setpoint_ram)
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    def threaded_update(self):
        #t0 = time.time()
        self.settings.flow.read_from_hardware()
        #print("read flow time", time.time() -t0)
        time.sleep(0.25)
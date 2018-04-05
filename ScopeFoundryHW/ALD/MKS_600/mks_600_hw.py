'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ALD.MKS_600.mks_600_interface import MKS_600_Interface

class MKS_600_Hardware(HardwareComponent):
    
    name = "mks_600_hw"
    
    assign = {'A': 1,
              'B': 2,
              'C': 3,
              'D': 4, 
              'E': 5,
              'Open': 6,
              'Close': 7}
    
    def setup(self):
        self.settings.New(name="port", initial="COM5", dtype=str, ro=False)
        self.settings.New(name="pressure", initial=0.0, fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="units", initial="torr", dtype=str, ro=False, choices=(('mbar'), ('torr'), ('mtorr')))
        self.settings.New(name="sp_channel", initial="Open", dtype=str, ro=False, choices=(('A'), ('B'), ('C'), ('D'), ('E'), ('Open'), ('Close')))
        self.settings.New(name="sp_readout", initial=0.0, spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="sp_set_value", initial=0.0, spinbox_decimals=4, dtype=float, ro=False)
        self.settings.New(name="valve_position", initial=0.0, dtype=float, spinbox_decimals=4, ro=True)
        self.mks = None
    
    def connect(self):
        self.mks = MKS_600_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.pressure.connect_to_hardware(read_func=self.read_pressure)
        self.settings.valve_position.connect_to_hardware(read_func=self.read_valve)

        self.settings.sp_set_value.connect_to_hardware(write_func=lambda x: self.write_sp(x))
        self.settings.sp_readout.connect_to_hardware(read_func=self.read_sp)
        
        self.settings.sp_channel.add_listener(self.switch_sp, str)
        set = self.settings['sp_channel']
        print('set', set)
        self.switch_sp(set)
        
    def read_pressure(self):
        choice = self.settings['units']
        if choice == 'torr':
            c = 1
        elif choice == 'mbar':
            c = (101325/76000)
        elif choice == 'mtorr':
            c=1000
        return c*self.mks.read_pressure()
    
    def read_sp(self):
        choice = self.settings['sp_channel']
        channel = self.assign[choice]
        resp = self.mks.read_sp(channel)
        return resp 
    
    def switch_sp(self, choice):
        channel = self.assign[choice]
        assert channel in range(0,8)
        if channel in range(0,6):
            self.mks.switch_sp(channel)
        else:
            self.mks.set_valve(channel)
    
    def write_sp(self, p):
        choice = self.settings['sp_channel']
        channel = self.assign[choice]
        print(p)
        self.mks.write_sp(channel, p)
        print(self.mks.read_sp(channel))
    

    def read_valve(self):
        return self.mks.read_valve()
    
    def set_valve(self, valve):
        if valve:
            return self.mks.open_valve()
        else:
            return self.mks.close_valve()

    
    
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        if self.mks is not None:
            self.mks.close()
        del self.mks
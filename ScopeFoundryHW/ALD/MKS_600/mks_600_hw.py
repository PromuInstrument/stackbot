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
    
    sp_defaults = {'A': 1.5e-2,
                   'B': 2e-4,
                   'C': 0,
                   'D': 0, 
                   'E': 0}
    
    def setup(self):
        self.settings.New(name="port", initial="COM5", dtype=str, ro=False)
        self.settings.New(name="pressure", initial=0.0, fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="units", initial="torr", dtype=str, ro=False, choices=(('mbar'), ('torr'), ('mtorr')))
        self.settings.New(name="sp_channel", initial="Open", dtype=str, ro=False, choices=(('A'), ('B'), ('C'), ('D'), ('E'), ('Open'), ('Close')))
        self.settings.New(name="sp_readout", initial=0.0, spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="sp_set_value", initial=0.0, spinbox_decimals=4, dtype=float, ro=False)
        self.settings.New(name="control_mode", initial='Pressure', dtype=str, ro=False, choices=(('Pressure'),('Position')))
        self.settings.New(name="set_valve_position", initial=0.0, dtype=float, spinbox_decimals=4, ro=True)
        self.settings.New(name="read_valve_position", initial=0.0, dtype=float, spinbox_decimals=4, ro=True)

        self.add_operation('Force SP defaults', self.set_sp_defaults)
        self.mks = None
    
    def connect(self):
        self.mks = MKS_600_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.pressure.connect_to_hardware(read_func=self.read_pressure)

        self.settings.sp_set_value.connect_to_hardware(write_func=lambda x: self.write_sp(x))
        self.settings.sp_readout.connect_to_hardware(read_func=self.read_sp)
        
        self.settings.set_valve_position.connect_to_hardware(write_func=lambda x: self.set_position(x))
        self.settings.read_valve_position.connect_to_hardware(read_func=self.read_position)

        
        self.settings.sp_channel.add_listener(self.switch_sp, str)
        self.settings.control_mode.add_listener(self.set_control_mode, str)
        
        self.settings['sp_channel'] = 'Open'
        self.set_valve(True)
        
    
    def set_sp_defaults(self):
        for channel, value in self.sp_defaults.items():
            self.switch_sp(channel)
            self.write_sp(value)
        self.settings.sp_channel.update_value('Open')
    
    def set_control_mode(self, control):
        channel = self.settings['sp_channel']
        if control == 'Pressure':
            self.mks.enable_pressure_mode(channel)
            self.settings.get_lq('set_valve_position').change_readonly(ro=True)
            self.settings.get_lq('sp_set_value').change_readonly(ro=False)
            print('Pressure')
        elif control == 'Position':
            self.mks.enable_position_mode(channel)
            self.settings.get_lq('set_valve_position').change_readonly(ro=False)    
            self.settings.get_lq('sp_set_value').change_readonly(ro=True)
            print('Position')
            
    def set_position_sp(self, pct):
        channel = self.settings['sp_channel']
        self.mks.write_set_point(channel, pct)
    
    def read_position_sp(self):
        channel = self.settings['sp_channel']
        return self.mks.read_set_point(channel)
    
    
    def read_pressure(self):
        choice = self.settings['units']
        if choice == 'torr':
            c = 1
        elif choice == 'mbar':
            c = (101325/76000)
        elif choice == 'mtorr':
            c=1000
        return c*self.mks.read_pressure()
    

    
    def switch_sp(self, choice):
        channel = self.assign[choice]
        assert channel in range(1,8)
        if channel in range(1,6):
            self.mks.switch_sp(channel)
        else:
            table = {6: True,
                     7: False}
            self.mks.valve_open(table[channel])
    
    def read_sp(self):
        "Reads set point value from active/selected preset channel"
        choice = self.settings['sp_channel']
        channel = self.assign[choice]
        resp = self.mks.read_sp(channel)
        return resp 
    
    def write_sp(self, p):
        "Writes set point value to active/selected preset channel"
        choice = self.settings['sp_channel']
        channel = self.assign[choice]
        print(p)
        self.mks.write_sp(channel, p)
        print(self.mks.read_sp(channel))
    
    
    def valve_open(self, valve):
        """Sets valve to full open/close."""
        return self.mks.valve_full_open(valve)

    def read_valve(self):
        """
        Reads valve percentage open.
        """
        return self.mks.read_valve()
    
    
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        if self.mks is not None:
            self.mks.close()
        del self.mks
'''
Created on Jan 30, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                         <alanbuckley@berkeley.edu>
'''

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

from ScopeFoundryHW.ALD.ALD_relay.ald_relay_interface import ALDRelayInterface

class ALDRelayHW(HardwareComponent):
    
    name = 'ald_relay_hw'
    
    def setup(self):
        self.ENABLED_PORTS = 2
        self.settings.New(name='port', initial='COM9', dtype=str, ro=False)
        self.create_pulse_lq()
    
    def connect(self):
        self.relay = ALDRelayInterface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        self.enable_pulse()

    def create_pulse_lq(self):
        for relay in range(1,self.ENABLED_PORTS+1,1):
            self.settings.New(name="pulse{}".format(relay), initial=False, dtype=bool, ro=False)
            self.settings.New(name="pulse_width{}".format(relay), initial=10, dtype=int, ro=False)

    def enable_pulse(self):
        for relay in range(1,self.ENABLED_PORTS+1,1):
            self.settings.get_lq('pulse{}'.format(relay)).connect_to_hardware(
                                    write_func=getattr(self,'write_pulse{}'.format(relay)))

    def create_toggle_lq(self):
        for relay in range(1,self.ENABLED_PORTS+1,1):
            self.settings.New(name="relay{}".format(relay), initial=False, dtype=bool, ro=False)
        
    def enable_toggle(self):
        for relay in range(1,self.ENABLED_PORTS+1,1):
            self.settings.get_lq('relay{}'.format(relay)).connect_to_hardware(
                                    write_func=getattr(self, 'write_relay{}'.format(relay)))
        

    def populate(self):
        "Populate logged quantities to reflect changes in self.relay.relay_array"
        for i in range(1,5,1):
            self.settings['pulse{}'.format(i)] = self.relay.relay_array[:,self.relay.pulse_running][i-1]

    
    
    def write_relay1(self, value):
        self.relay.write_state(0, value)
        
    def write_relay2(self, value):
        self.relay.write_state(1, value)
    
    def write_relay3(self, value):
        self.relay.write_state(2, value)
        
    def write_relay4(self, value):
        self.relay.write_state(3, value)                       

    def write_pulse1(self, value):
        if value:
            duration = self.settings['pulse_width1']
            self.relay.send_pulse(0, duration)
            self.settings['pulse1'] = False

    def write_pulse2(self, value):
        if value:
            duration = self.settings['pulse_width2']
            self.relay.send_pulse(1, duration)
            self.settings['pulse2'] = False

    def write_pulse3(self, value):
        if value:
            duration = self.settings['pulse_width3']
            self.relay.send_pulse(2, duration)

    def write_pulse4(self, value):
        if value:
            duration = self.settings['pulse_width4']
            self.relay.send_pulse(3, duration)
    

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'relay'):
            self.relay.close()
            del self.relay
        
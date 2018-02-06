'''
Created on Dec 6, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ALD.MKS_146.mks_146_interface import MKS_146_Interface

class MKS_146_Hardware(HardwareComponent):
    
    name = "mks_146_hw"
    
    def setup(self):
        self.settings.New(name="port", initial="COM6", dtype=str, ro=False)
        self.settings.New(name="MFC1_flow", initial=0.0, fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="MFC2_flow", initial=0.0, fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        self.settings.New(name="MFC1_valve", initial="C", dtype=str, choices = [
                                                                ("Open", "O"),
                                                                ("Closed", "C"),
                                                                ("Cancel", "N")])
        
        self.settings.New(name="MFC2_valve", initial="C", dtype=str, choices = [
                                                                ("Open", "O"),
                                                                ("Closed", "C"),
                                                                ("Cancel", "N")])
        
        self.settings.New(name="MFC1_SP", initial=0.0, fmt="%1.3f", spinbox_decimals=3, dtype=float, ro=False)
        self.settings.New(name="MFC2_SP", initial=0.0, fmt="%1.3f", spinbox_decimals=3, dtype=float, ro=False)
        
        self.MFC1_chan = 2
        self.MFC2_chan = 3
        
        self.mks = None
        
    def connect(self):
        self.mks = MKS_146_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        self.settings.MFC1_flow.connect_to_hardware(read_func=self.MFC1_read_flow)
        self.settings.MFC2_flow.connect_to_hardware(read_func=self.MFC2_read_flow)
        self.settings.MFC1_valve.connect_to_hardware(write_func=lambda x: self.MFC1_write_valve(x),
                                                     read_func=self.MFC1_read_valve)
        self.settings.MFC2_valve.connect_to_hardware(write_func=lambda x: self.MFC2_write_valve(x),
                                                     read_func=self.MFC2_read_valve)
        self.settings.MFC1_SP.connect_to_hardware(write_func=lambda x: self.MFC1_write_SP(x),
                                                  read_func=self.MFC1_read_SP)
        self.settings.MFC2_SP.connect_to_hardware(write_func=lambda x: self.MFC2_write_SP(x),
                                                  read_func=self.MFC2_read_SP)
        
        self.read_from_hardware()
        
    def MFC1_read_flow(self):
        channel = self.MFC1_chan
        return self.mks.MFC_read_flow(channel)
    
    def MFC2_read_flow(self):
        channel = self.MFC2_chan
        return self.mks.MFC_read_flow(channel)
    

    def MFC1_read_SP(self):
        channel = self.MFC1_chan
        return self.mks.MFC_read_SP(channel)
    
    def MFC2_read_SP(self):
        channel = self.MFC2_chan
        return self.mks.MFC_read_SP(channel)
    
    def MFC1_write_SP(self, SP):
        channel = self.MFC1_chan
        return self.mks.MFC_write_SP(channel, SP)
    
    def MFC2_write_SP(self, SP):
        channel = self.MFC2_chan
        return self.mks.MFC_write_SP(channel, SP)
    
    
    def MFC1_write_valve(self, status):
        channel = self.MFC1_chan
        return self.mks.MFC_write_valve_status(channel, status)
    
    def MFC2_write_valve(self, status):
        channel = self.MFC2_chan
        return self.mks.MFC_write_valve_status(channel, status)
    
    def MFC1_read_valve(self):
        channel = self.MFC1_chan
        return self.mks.MFC_read_valve_status(channel)
    
    def MFC2_read_valve(self):
        channel = self.MFC2_chan
        return self.mks.MFC_read_valve_status(channel)
    
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if self.mks is not None:
            self.mks.close()
        del self.mks
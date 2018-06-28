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
        
        self.MFC_count = 1
        
        self.settings.New(name="port", initial="COM8", dtype=str, ro=False)
        self.settings.New(name="MFC0_flow", fmt="%1.3f", spinbox_decimals=4, dtype=float, ro=True)
        

        self.settings.New(name="set_MFC0_valve", initial="N", dtype=str, choices = [
                                                                ("Open", "O"),
                                                                ("Closed", "C"),
                                                                ("Manual", "N")], ro=False)
        
        self.settings.New(name="read_MFC0_valve", initial="N", dtype=str, choices = [
                                                                ("Open", "O"),
                                                                ("Closed", "C"),
                                                                ("Manual", "N")], ro=True)
         


        self.settings.New(name="set_MFC0_SP", initial=0.0002, fmt="%1.4f", spinbox_decimals=4, dtype=float, vmin=0.0002, vmax=20, ro=False)

        if self.MFC_count > 1:
            self.settings.New(name="MFC1_flow", fmt="%1.4f", spinbox_decimals=4, dtype=float, ro=True)
            self.settings.New(name="set_MFC1_SP", initial=0.0002, fmt="%1.4f", spinbox_decimals=4, dtype=float, vmin=0.0002, vmax=20, ro=False)
            
            self.settings.New(name="set_MFC1_valve", initial="C", dtype=str, choices = [
                                                                    ("Open", "O"),
                                                                    ("Closed", "C"),
                                                                    ("Cancel", "N")], ro=False)
            self.settings.New(name="read_MFC1_valve", initial="C", dtype=str, choices = [
                                                                    ("Open", "O"),
                                                                    ("Closed", "C"),
                                                                    ("Cancel", "N")], ro=True)

                
        self.mks = None
        
        
    def chan_assign(self):            
        skip = True
        slot = 0
        for i, sensor_type in enumerate(self.assignment):
            if (sensor_type == "Mass Flow Controller") and skip:
                '''Skip first instrument, flag next for LQ assignment'''
                skip = not True
                if self.debug_mode:
                    print('Skipped assignment of channel {}'.format(i))
            elif (sensor_type == "Mass Flow Controller") and (not skip):
                
                setattr(self, 'MFC{}_chan'.format(slot), i)
                if self.debug_mode:
                    print(getattr(self, 'MFC{}_chan'.format(slot)))
                
                self.settings.get_lq('MFC{}_flow'.format(slot)).connect_to_hardware(
                                                    read_func=getattr(self,'MFC{}_read_flow'.format(slot)))
                if self.debug_mode:
                    print('MFC{}_flow'.format(slot))
                
                self.settings.get_lq('set_MFC{}_valve'.format(slot)).connect_to_hardware(
                                                    write_func=getattr(self,'MFC{}_write_valve'.format(slot)))
                self.settings.get_lq('read_MFC{}_valve'.format(slot)).connect_to_hardware(
                                                    read_func=getattr(self, 'MFC{}_read_valve'.format(slot)))
                    
                
                self.settings.get_lq('set_MFC{}_SP'.format(slot)).connect_to_hardware(
                                                    write_func=getattr(self,'MFC{}_write_SP'.format(slot)))
                

                slot += 1
                if self.MFC_count == 1:
                    skip = True
            else: pass
    
    
    def connect(self):
        self.mks = MKS_146_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])

        self.assignment = self.mks.autodetect()
        
        self.chan_assign()
        
        self.settings.get_lq('set_MFC0_valve').update_value('C')
        
        self.read_from_hardware()
        
        
                
    def MFC0_read_flow(self):
        if hasattr(self, 'MFC0_chan'):
            channel = self.MFC0_chan
            return self.mks.MFC_read_flow(channel)
        
    def MFC1_read_flow(self):
        if hasattr(self, 'MFC1_chan'):
            channel = self.MFC1_chan
            return self.mks.MFC_read_flow(channel)
    

    def MFC0_read_SP(self):
        if hasattr(self, 'MFC0_chan'):
            channel = self.MFC0_chan
            return self.mks.MFC_read_SP(channel)
    
    def MFC1_read_SP(self):
        if hasattr(self, 'MFC1_chan'):
            channel = self.MFC1_chan
            return self.mks.MFC_read_SP(channel)
    
    def MFC0_write_SP(self, SP):
        if hasattr(self, 'MFC0_chan'):
            channel = self.MFC0_chan
            return self.mks.MFC_write_SP(channel, SP)
    
    def MFC1_write_SP(self, SP):
        if hasattr(self, 'MFC1_chan'):
            channel = self.MFC1_chan
            return self.mks.MFC_write_SP(channel, SP)
        
    
    def MFC0_write_valve(self, status):
        if hasattr(self, 'MFC0_chan'):
            channel = self.MFC0_chan
            if self.debug_mode:
                print('MFC0_write_valve_status:', status)
            return self.mks.MFC_write_valve_status(channel, status)
    
    def MFC1_write_valve(self, status):
        if hasattr(self, 'MCF1_chan'):
            channel = self.MFC1_chan
            if self.debug_mode:
                print('MFC1_write_valve_status:', status)
            try:
                resp = self.mks.MFC_write_valve_status(channel, status)
                return resp
            except ValueError:
                print(resp)
                
    def MFC0_read_valve(self):
        if hasattr(self, 'MFC0_chan'):
            channel = self.MFC0_chan
            return self.mks.MFC_read_valve_status(channel)
        
    def MFC1_read_valve(self):
        if hasattr(self, 'MFC1_chan'):
            channel = self.MFC1_chan
            return self.mks.MFC_read_valve_status(channel)
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if self.mks is not None:
            self.mks.close()
        del self.mks
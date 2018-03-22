'''
Created on Feb 21, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
import time

class ALD_routine(Measurement):
    
    name = 'ALD_routine'
    
    def __init__(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
        self.seren.serial_toggle(True)
    
    
    
    
    def precursor_1_dose(self, width=0.8):
        """argument 'width' has units of seconds"""
        relay = 0
        chamber_pressure = 15 #mtorr
        
        def pressure_and_flow():
            measure = self.vgc.read_ch1_pressure()
            pressure = (1000*measure)/(101325/76000) #mtorr
            flow = self.mks146.MFC0_read_flow()
            return pressure, flow
        
        pressure, flow = pressure_and_flow()
        while not (chamber_pressure-1 < pressure < chamber_pressure+1) \
                and not (100 <= flow <= 200):
            pressure, flow = pressure_and_flow()
        else:
            if self.debug_mode:
                print("Pulse sending--", "pressure:", pressure, "> chamber:", chamber_pressure)
            self.relay.relay.send_pulse(relay, 1e3*width)

    def precursor_purge(self, pressure_sp, temp_sp):
        
        def read_temp_and_pressure():
            temp = self.lovebox.lovebox.read_temp()
#             pressure = self.vgc.
            return temp
    
    def plasma_dose(self, width, power):
        """Argument 'width' has units of seconds
        power has units of Watts
        """
        self.seren.write_fp(power)
        self.seren.RF_toggle(True)
        time.sleep(width)
        self.seren.RF_toggle(False)
        self.seren.write_fp(0)

    def run(self):
        while not self.interrupt_measurement_called:
            pass
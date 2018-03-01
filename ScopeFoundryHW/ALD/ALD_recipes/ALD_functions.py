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
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
        self.seren.serial_toggle(True)
    
    def precursor_1_dose(self, width=0.8):
        """argument 'width' has units of seconds"""
        relay = 0
        chamber_pressure = 15 #mtorr 
        pressure = (1000*self.vgc.read_ch1_pressure())/(101325/76000) #mtorr
        while not (chamber_pressure-1 < pressure < chamber_pressure+1):
            pressure = (1000*self.vgc.read_ch1_pressure())/(101325/76000)
        else: 
            print("Pulse sending--", "pressure:", pressure, "> chamber:", chamber_pressure)
            self.relay.relay.send_pulse(relay, 1e3*width)
            break
    
    
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
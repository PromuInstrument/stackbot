'''
Created on May 25, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
import time

class ALD_Recipe(Measurement):
    
    name = 'ALD_Recipe'
    
    def setup(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.mks600 = self.app.hardware['mks_600_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
    
        if hasattr(self.app.hardware, 'ald_shutter'):
            self.shutter = self.app.hardware.ald_shutter
        else:
            print('Connect ALD shutter HW component first.')
        self.settings.New('cycles_elapsed', dtype=int, initial=0, ro=True)
        
    def load_times(self):
        self.times = self.app.measurements.ALD_params.settings['time']
    
    def plasma_dose(self, width, power):
        """Argument 'width' has units of seconds
        power has units of Watts
        """
        print('Start plasma dose.')
        self.seren.write_fp(power)
        self.seren.RF_toggle(True)
        time.sleep(width)
        self.seren.RF_toggle(False)
        self.seren.write_fp(0)
        print('Plasma dose finished.')
        
    def valve_pulse(self, width):
        self.relay.write_pulse1(width)
    
    def purge(self, width):
        time.sleep(width)    
    
    def shutter_pulse(self, width):
        self.shutter['shutter_open'] = True
        time.sleep(width)
        self.shutter['shutter_open'] = False

    def routine(self):
        _, t1, t2, t3, t4, _, _  = self.times[0]
        self.valve_pulse(t1)
        self.purge(t2)
        self.shutter_pulse(t3)
        self.purge(t4)
    
    def prepurge(self):
        width = self.times[0][0]
        time.sleep(width)
    
    def postpurge(self):
        width = self.times[5][0]
        time.sleep(width)
        
    def shutdown(self):
        print('Shutdown initiated.')
        self.ramp_throttle_open()
        if self.shutdown_ready:
            state = self.MFC_valve_states['Closed']
            self.mks146.settings['MFC0_valve'] = state
    
    def ramp_throttle_open(self):
        print('Ramping down.')
        self.shutdown_ready = False
        pressure = self.vgc.settings['ch2_pressure_scaled']
        if pressure < 1e-2:
            self.mks600.settings['sp_channel'] = 'B'
            self.mks600.write_sp(0.0002)
            time.sleep(10)
            self.mks600.write_sp(0.0001)
            time.sleep(20)
            self.mks600.settings['sp_channel']= 'Open'
            self.shutdown_ready = True
        else:
            print('Disable pump before equalizing chamber pressures. Don\'t dump that pump!')
            pass
    
    def run(self):
        cycles = self.app.measurements.ALD_params.settings['cycles']    
        self.times = self.app.measurements.ALD_params.settings['time']
        while not self.interrupt_measurement_called:
            self.prepurge()
            for i in range(cycles):
                self.routine()
                self.settings['cycles_elapsed'] = i
            self.postpurge()
        else:
            self.shutdown()

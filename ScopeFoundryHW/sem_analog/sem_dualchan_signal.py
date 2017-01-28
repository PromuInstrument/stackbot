'''
Created on Jul 18, 2016

@author: NIuser
'''
from ScopeFoundry import HardwareComponent
try:
    from equipment.NI_Daq import NI_AdcTask
except Exception as err:
    print "Cannot load NI_Daq NI_AdcTask:", err
    
import time
import random
import numpy as np

class SEMDualChanSignal(HardwareComponent):

    name = "sem_dualchan_signal"

    def setup(self):

        # Create logged quantities
        self.inLens_signal = self.add_logged_quantity(
                                name = 'inLens_signal', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="V",
                                vmin=-100, vmax=100)
        self.signal_nsamples = self.add_logged_quantity(
                                name = 'signal_nsamples',
                                initial=1,
                                dtype=int, ro=False,
                                unit = "",
                                vmin = 1, vmax=10000)
        
        self.se2_signal = self.add_logged_quantity(
                                name = 'se2_signal', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="V",
                                vmin=-100, vmax=100)


        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        
    def connect(self):
        if self.debug_mode.val: print "Connecting to NI_Dac NI_AdcTask"
        
        # Open connection to hardware

        if not self.dummy_mode.val:
            self.adc = NI_AdcTask('X-6368/ai0:1')
            #self.adc_InLens = NI_AdcTask('X-6368/ai1')
            #self.adc_SE2 = NI_AdcTask('X-6368/ai0')
        else:
            if self.debug_mode.val: print "Connecting to NI_Dac NI_AdcTask (Dummy Mode)"

        # connect logged quantities
        self.inLens_signal.hardware_read_func = self.read_inlens_signal
        self.se2_signal.hardware_read_func = self.read_se2_signal


    def disconnect(self):
        #disconnect hardware
        self.adc.close()
        #self.adc_InLens.close()
        #self.adc_SE2.close()
        
        #disconnect logged quantities from hardware
        for lq in self.settings.as_dict().values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        del self.adc
        
    def read_inlens_signal(self):        
        return self.read_signals()[1]
        
    def read_se2_signal(self):        
        return self.read_signals()[0]
    
    
    def read_signals(self):
        t0 = time.time()
        if not self.dummy_mode.val:
            X = np.zeros(2, dtype=float)
            for i in range(self.signal_nsamples.val):          
                X += self.adc.get()
            print "read_signals", time.time() - t0, "sec", "nsamples", self.signal_nsamples.val
            return X / self.signal_nsamples.val
        else:
            time.sleep(self.inLens_signal_nsamples.val * 20e-6)
            signal = np.random.random(2)*100.
            if self.debug_mode.val: print self.name, "dummy read_count_rate", signal
            return signal            

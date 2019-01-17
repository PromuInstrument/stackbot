'''
Created on Dec 11, 2018

@author: Benedikt
'''

import time
from ScopeFoundry import Measurement, h5_io
import numpy as np


class CalibrationSweep(Measurement):
    
    name = 'calibration_sweep'

    def __init__(self, app, name=None, 
                 camera_readout_measure_name = 'winspec_readout', 
                 spectrometer_hw_name = 'acton_spectrometer'):
        
        
        self.camera_readout_measure_name = camera_readout_measure_name
        self.spectrometer_hw_name = spectrometer_hw_name

        Measurement.__init__(self, app, name)

        print(self.camera_readout_measure_name)
        
        
    def setup(self):
        self.center_wl_range = self.settings.New_Range('center_wls')      
              
    
    def run(self):
        self.spec_readout = self.app.measurements[self.camera_readout_measure_name]
        self.spec_center_wl = self.app.hardware[self.spectrometer_hw_name].settings.center_wl     
        
        self.t0 = time.time()      
        
        self.spec_readout.settings['continuous'] = False
        
        self.spectra = []
        self.center_wls = [] #center wls read from spectrometer
        
        N = len(self.center_wl_range.array)
        i = 0
        
        for center_wl in self.center_wl_range.array:
            i += 1
            self.set_progress(100*(i+1)/N)
            
            self.spec_center_wl.update_value(center_wl)
            self.spec_center_wl.write_to_hardware()
            time.sleep(1.)
            
            self.start_nested_measure_and_wait(self.spec_readout, polling_time=0.1, start_time=0.1)
            
            time.sleep(0.1)
            
            self.spectra.append(self.spec_readout.spec)
            self.center_wls.append(self.spec_center_wl.val)


        self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        H['spectra'] = np.array(self.spectra)
        H['center_wls'] = np.array(self.center_wls)
        self.h5_file.close()
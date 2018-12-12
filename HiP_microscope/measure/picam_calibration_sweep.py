'''
Created on Dec 11, 2018

@author: Benedikt
'''

import time
from ScopeFoundry import Measurement, h5_io
import numpy as np


class PicamCalibrationSweep(Measurement):

    name = 'picam_calibration_sweep'
    
    def setup(self):
        self.center_wl_range = self.settings.New_Range('center_wls')
        
        self.spec_readout = self.app.measurements['picam_readout']
        self.spec_center_wl = self.app.hardware['acton_spectrometer'].settings.center_wl             
              
    
    def run(self):
        self.t0 = time.time()      
        
        self.spec_readout.settings['continuous'] = False
        
        self.spectra = []
        self.center_wls = [] #center wls read from spectrometer
        
        for center_wl in self.center_wl_range.array:
            self.spec_center_wl.update_value(center_wl)
            time.sleep(1)
            self.start_nested_measure_and_wait(self.spec_readout, polling_time=0.1, start_time=0.1)
            self.spectra.append(self.spec_readout.spec)
            self.center_wls.append(self.spec_center_wl.val)


        self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        H['spectra'] = np.array(self.spectra)
        H['center_wls'] = np.array(self.center_wls)
        self.h5_file.close()
'''
Created on Sep 7, 2017

@author: Benedikt Ursprung
'''
from ir_microscope.measurements.ir_microscope_base_scans import IRMicroscopeBase2DScan
from confocal_measure.andor_hyperspec_scan import AndorHyperSpec2DScanBase

class AndorHyperSpec2DScan(IRMicroscopeBase2DScan):
    
    name = "andor_hyperspec_scan"
    
    def setup(self):
        IRMicroscopeBase2DScan.setup(self)
    
    def scan_specific_setup(self):
        AndorHyperSpec2DScanBase.scan_specific_setup(self)
        
    def pre_scan_setup(self):
        AndorHyperSpec2DScanBase.pre_scan_setup(self)
        IRMicroscopeBase2DScan.pre_scan_setup(self)
        
    def post_scan_cleanup(self):
        AndorHyperSpec2DScanBase.post_scan_cleanup(self)
        IRMicroscopeBase2DScan.post_scan_cleanup(self)
        
    def collect_pixel(self, pixel_num, k, j, i):
        IRMicroscopeBase2DScan.collect_pixel(self, pixel_num, k, j, i)
        AndorHyperSpec2DScanBase.collect_pixel(self, pixel_num, k, j, i)

    def update_display(self):
        IRMicroscopeBase2DScan.update_display(self)
        


import numpy as np
import time as time
#Was used to with PI InGaAs / winspec readout
class Hyperspectral2DScan_old_with_winspec(IRMicroscopeBase2DScan):
    
    name = 'hyperspectral_2d_scan'
    
    def __init__(self, app):
        IRMicroscopeBase2DScan.__init__(self, app)

    def setup(self):
        IRMicroscopeBase2DScan.setup(self)
        #print(self.name, "setup() called")
        self.ccd_measure = self.app.measurements['winspec_readout']
    
    def setup_figure(self):
        IRMicroscopeBase2DScan.setup_figure(self)
        self.graph_layout.nextRow()
        self.spec_plot = self.graph_layout.addPlot(title='Current Spectrum', left='Intensity', bottom='Wavelength (nm)') 
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])

    def pre_run(self):
        IRMicroscopeBase2DScan.pre_run(self)
        self.ccd_measure.pre_run()
    
    def pre_scan_setup(self):
        IRMicroscopeBase2DScan.pre_scan_setup(self)

        # Based on winspec_readout measurement
        self.ccd_measure.interrupt()
        
        #Reconnect to winspec (Clears Server Buffer)
        self.ccd_measure.winspec_hc.settings['connected'] = False
        time.sleep(0.2)
        self.ccd_measure.winspec_hc.settings['connected'] = True
        time.sleep(0.2)
        
        # Setup data structures
        self.map_shape = (*self.scan_shape, 1024)
        self.px_index = np.arange(self.map_shape[-1])
        self.wls = self.px_index
       
        if self.settings['save_h5']:
            self.hyperspectral_map_h5 = self.h5_meas_group.create_dataset('hyperspectral_map', 
                                                                       shape=self.map_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')
            self.integrated_count_map_h5 = self.h5_meas_group.create_dataset('integrated_count_map', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')
            self.wls_h5 = self.h5_meas_group.create_dataset('wls', shape=(1024,), dtype = float, compression ='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        self.ccd_measure.interrupt_measurement_called = self.interrupt_measurement_called
        IRMicroscopeBase2DScan.collect_pixel(self, pixel_num, k, j, i)                
        #calculate time remaining, there is almost 0.72 second overhead per pixel.
        #sec_remaining = (self.Npixels-(pixel_num+1))*(self.app.hardware['winspec_remote_client'].settings['acq_time']+0.72)
        #print(self.name, "collecting pixel: (",k,j,i, ") number:", pixel_num+1,"of",self.Npixels,
        #      'estimated time remaining:',datetime.timedelta(seconds=sec_remaining) )

        #acquire ccd data
        counter=0 
        retry = True
        while(retry):
            try:
                counter +=1
                hdr,data = self.ccd_measure.acquire_data(debug=False)
                #1print(counter)
                retry = False
            except:
                print('An error occurred while aquire_data(), try', counter, '/4')
                retry = True
            finally:
                if counter > 3:
                    retry = False
                    #self.measurement_sucessfully_completed = False
        if hdr is None or data is None:
            raise IOError("Failed to acquire Data (probably interrupted)")
        self.hdr = hdr
        self.data = data[0,0,:]        

        if pixel_num == 0:
            self.wls = self.ccd_measure.evaluate_wls_acton_spectrometer(self.hdr, self.px_index) 
            
        intensity  = self.data.sum()
        self.display_image_map[k,j,i] = intensity
        
        # save spectral data
        if self.settings['save_h5']:
            self.hyperspectral_map_h5[k,j,i,:]  = self.data  
            self.integrated_count_map_h5[k,j,i] = intensity
            if pixel_num == 0:
                self.wls_h5[:] = self.wls            
        
    def update_display(self):
        if not hasattr(self, 'data'):
            return
        self.spec_plot_line.setData(self.wls, self.data)
        IRMicroscopeBase2DScan.update_display(self)

'''
Created on Sep 7, 2017

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
import numpy as np
import time as time
from ScopeFoundry import h5_io


class M4Hyperspectral2DScan(AttoCube2DSlowScan):
    
    name = 'm4_hyperspectral_2d_scan'
        
    def setup(self):
        AttoCube2DSlowScan.setup(self)
        #print(self.name, "setup() called")
        self.ccd_measure = self.app.measurements['winspec_readout']
    
    def setup_figure(self):
        AttoCube2DSlowScan.setup_figure(self)
        self.graph_layout.nextRow()
        self.spec_plot = self.graph_layout.addPlot(title='Current Spectrum', left='Intensity', bottom='Wavelength (nm)') 
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])

    def pre_run(self):
        AttoCube2DSlowScan.pre_run(self)
        self.ccd_measure.pre_run()
    
    def pre_scan_setup(self):
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

    def collect_pixel(self, pixel_num, k, j, i):
        
        #print(self.name, "collecting pixel (k,j,i):",k,j,i, "pixel:", pixel_num+1,"of",self.Npixels)  
        self.ccd_measure.interrupt_measurement_called = self.interrupt_measurement_called
        hdr,data = self.ccd_measure.acquire_data(debug=False)
        
        if hdr is None or data is None:
            raise IOError("Failed to acquire Data (probably interrupted)")
        self.hdr = hdr
        self.data = data[0,0,:]
        
        if pixel_num == 0:
            self.wls = self.ccd_measure.evaluate_wls_acton_spectrometer(self.hdr, self.px_index)
            self.h5_meas_group['wls'] = self.wls            
            time.sleep(0.01)
            
        self.display_image_map[k,j,i] = self.data.sum()
        
        if self.settings['save_h5']:
            self.hyperspectral_map_h5[k,j,i,:] = self.data
    
    def post_scan_cleanup(self):
        if self.settings['save_h5']:
            self.h5_file.close()
        
    def update_display(self):
        if not hasattr(self, 'data'):
            return
        self.spec_plot_line.setData(self.wls, self.data)
        AttoCube2DSlowScan.update_display(self)

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
        print(self.name, "setup() called")
        self.ccd_measure = self.app.measurements['winspec_readout']
    
    def setup_figure(self):
        AttoCube2DSlowScan.setup_figure(self)
        self.graph_layout.nextRow()
        self.spec_plot = self.graph_layout.addPlot(title='Current Spectrum', left='Intensity', bottom='wavelengths (ns)') 
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])
        
        #self.spec_plot.set_labels(title='Current Spectrum', left='Intensity', bottom='wavelengths (ns)')       

    def pre_run(self):
        AttoCube2DSlowScan.pre_run(self)
        self.ccd_measure.pre_run()

    
    def pre_scan_setup(self):
        '''Steal as much as possible from WinSpecRemoteMeasure'''
        
        print(self.name, "pre_scan_setup()" ,"called")
        
        
        self.map_shape = (*self.scan_shape, 1024)
        
        if self.settings['save_h5']:
            self.hyperspectral_map_h5 = self.h5_meas_group.create_dataset('hyperspectral_map', 
                                                                       shape=self.map_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')
            

                
    def post_scan_cleanup(self):
        if self.settings['save_h5']:
            self.h5_meas_group['wls'] = self.wls
            #create h5 data arrays
            self.h5_file.close()


    def collect_pixel(self, pixel_num, k, j, i):
        #print(self.stage.settings['debug_mode'])
        if self.stage.settings['debug_mode']:
            print(self.name, "collecting pixel (k,j,i):",k,j,i, "pixel:", pixel_num+1,"of",self.Npixels)  
               
        self.hdr,self.data = self.ccd_measure.acquire_data(debug=True)
        self.display_image_map[k,j,i] = self.data.sum()
        
        if pixel_num == 0:
            self.wls = self.ccd_measure.evaluate_wls(self.hdr,self.stage.settings['debug_mode'])
             
        
        if self.settings['save_h5']:
            self.hyperspectral_map_h5[k,j,i,:] = self.data
            
            

            
            
        
    def update_display(self):
        if not hasattr(self, 'data'):
            return
        self.spec_plot_line.setData(self.wls, np.average(self.data[0,:,:], axis=0))
        AttoCube2DSlowScan.update_display(self)

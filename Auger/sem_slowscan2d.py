from ScopeFoundry.scanning import BaseRaster2DSlowScan
import numpy as np
import time

class SEMVoutSlowScan(BaseRaster2DSlowScan):
    
    name = "SEMVoutSlowScan"
    
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-10,10), v_limits=(-10,10), h_unit="V", v_unit="V")        
        self.stage = self.app.hardware['sem_slowscan_vout_stage']


    def move_position_start(self, x,y):
        self.stage.settings['x_position'] = x
        self.stage.settings['y_position'] = y
        
    def move_position_slow(self, x,y, dx,dy):
        self.stage.settings['x_position'] = x
        self.stage.settings['y_position'] = y
        
    def move_position_fast(self, x,y, dx,dy):
        #self.stage.settings['x_position'] = x
        #self.stage.settings['y_position'] = y
        self.stage.dac.set((x,-1*y))

class SEMVoutDelaySlowScan(SEMVoutSlowScan):
    name = "SEMVoutSlowScan"
    
    def scan_specific_setup(self):
        self.settings.New('pixel_time', dtype=float, initial=0.1, unit='s')
        
    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(self.settings['pixel_time'])

class SEMSlowScan(SEMVoutSlowScan):
    
    name = "SEMSlowScan"

    def scan_specific_setup(self):
        #Hardware
        self.sem_dualchan_signal = self.app.hardware['sem_dualchan_signal']
    
    def pre_scan_setup(self):
        #Adding hdf5 datasets
        if self.settings['save_h5']:
            H = self.h5_meas_group
            self.se_data_h5 = H.create_dataset('SE_data', self.scan_shape, dtype=np.float)
        

        #self.spec_map = np.zeros(self.scan_shape + (1340,), dtype=np.float)
        #self.spec_map_h5 = self.h5_meas_group.create_dataset('spec_map', self.scan_shape + (1340,), dtype=np.float)
        #pass

    def collect_pixel(self, pixel_num, k, j, i):
        # collect data
        # store in arrays        
        #dat = self.picam.cam.acquire(readout_count=1, readout_timeout=-1)
            
        #self.roi_data = self.picam.cam.reshape_frame_data(dat)
        #self.spec_map[k,j,i, :] = spec =  self.roi_data[0].sum(axis=0)
        
        #self.spec_map_h5[k,j,i,:] = spec
        
        sig = self.app.hardware['sem_dualchan_signal'].settings.inLens_signal.read_from_hardware()
        
        self.display_image_map[k,j,i] = sig
        if self.settings['save_h5']:
            self.se_data_h5[k,j,i] = sig

    def post_scan_cleanup(self):
        #print(self.name, "post_scan_cleanup")
        #import scipy.io
        #scipy.io.savemat(file_name="%i_%s.mat" % (self.t0, self.name), mdict=dict(spec_map=self.spec_map))
        pass
    
    def update_display(self):
        BaseRaster2DSlowScan.update_display(self)
        
        #self.app.measurements.picam_readout.roi_data = self.roi_data
        #self.app.measurements.picam_readout.update_display()
    
    
    
    

    

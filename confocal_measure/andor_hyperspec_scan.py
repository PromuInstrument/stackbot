import numpy as np
from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage2DSlowScan
import time

class AndorHyperSpec2DScan(MCLStage2DSlowScan):
    
    name = "andor_hyperspec_scan"
    
    def scan_specific_setup(self):
        #Hardware
        self.stage = self.app.hardware['mcl_xyz_stage']

        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']


        #self.andor_ccd_hw = self.gui.andor_ccd_hc
        #ccd = self.andor_ccd = self.andor_ccd_hw.andor_ccd


    def pre_scan_setup(self):
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        #self.andor_ccd_readout.settings['activation'] = True
        # wait until done
        #while self.andor_ccd_readout.is_measuring():
        #    self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called
        #    time.sleep(0.01)
        self.andor_ccd_readout.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.andor_ccd_readout.spectra_data.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                 'spec_map', spec_map_shape, dtype=np.float)

            self.wls = np.array(self.andor_ccd_readout.wls)
            self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k,j,i,:] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
  
        self.display_image_map[k,j,i] = spec.sum()


    def post_scan_cleanup(self):
        self.andor_ccd_readout.settings['save_h5'] = True
        
    def update_display(self):
        MCLStage2DSlowScan.update_display(self)
        self.andor_ccd_readout.update_display()
        

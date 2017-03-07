from .sem_sync_raster_measure import SemSyncRasterScan
import time
import numpy as np


class AugerSyncRasterScan(SemSyncRasterScan):
    
    name = "auger_sync_raster_scan"
    
    def scan_specific_setup(self):
        self.display_update_period = 0.1
        SemSyncRasterScan.scan_specific_setup(self)
    
    def pre_scan_setup(self):
        # Hardware
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()

        self.auger_fpga_hw.settings['trigger_mode'] = 'pxi'

        # Data Arrays
        self.auger_chan_pixels = np.zeros((self.Npixels, 10), dtype=np.uint32)
        self.auger_i = 0
        # figure?
        
    def every_n_callback_func(self):
        i = self.auger_i
        new_auger_data = self.auger_fpga_hw.read_fifo()
        n = new_auger_data.shape[0]
        self.auger_chan_pixels[i:i+n] = new_auger_data
        self.auger_i += n
        
        return SemSyncRasterScan.every_n_callback_func(self)
    
    def handle_new_data(self):
        """ Called during measurement thread wait loop"""
        SemSyncRasterScan.handle_new_data(self)
    
    def post_scan_cleanup(self):
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'

    def update_display(self):
        self.display_pixels = self.auger_chan_pixels[:,0:8].sum(axis=1)
        SemSyncRasterScan.update_display(self)
    
        
        
from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
import numpy as np


class FiberPowerMeterScan(AttoCube2DSlowScan):
    
    name = 'fiber_powermeter_scan'
    
    def scan_specific_setup(self):
        self.pm = self.app.hardware['thorlabs_powermeter']  
        self.pm.read_from_hardware()
    
    def collect_pixel(self, pixel_num, k, j, i):
        print(self.name, "collect_pixel")
        
        power = self.pm.settings.power.read_from_hardware()
        
        self.display_image_map[k,j,i] = power
        
        
class FiberAPDScan(AttoCube2DSlowScan):
    
    name = 'fiber_apd_scan'

    def pre_scan_setup(self):
        self.apd = self.app.hardware['apd_counter']

        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')

        
        
    def collect_pixel(self, pixel_num, k, j, i):
        count_rate = self.apd.settings.apd_count_rate.read_from_hardware()
        
        self.display_image_map[k,j,i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k,j,i] = count_rate


from confocal_measure import Picoharp_MCL_2DSlowScan
class FiberPicoharpScan(AttoCube2DSlowScan):
    
    name = 'fiber_picoharp_scan'

    def pre_scan_setup(self):
        Picoharp_MCL_2DSlowScan.pre_scan_setup(self)

    def collect_pixel(self, pixel_num, k, j, i):
        Picoharp_MCL_2DSlowScan.collect_pixel(self, pixel_num, k, j, i)

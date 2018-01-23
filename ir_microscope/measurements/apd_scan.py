from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan

class M4APDScanMeasure(AttoCube2DSlowScan):
    
    name = 'm4_apd_2d_scan'

    def pre_scan_setup(self):
        self.apd = self.app.hardware['apd_counter']

        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')


    def collect_pixel(self, pixel_num, k, j, i):
        count_rate = self.apd.settings.count_rate.read_from_hardware()
        
        self.display_image_map[k,j,i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k,j,i] = count_rate
            
class M4APDScanPhMeasure(AttoCube2DSlowScan):
    
    name = 'm4_apd_2d_scan_ph'

    def pre_scan_setup(self):
        self.ph = self.app.hardware['picoharp']

        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map_ph', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')


    def collect_pixel(self, pixel_num, k, j, i):
        if self.ph.settings.debug_mode.val:
            print(self.name, "collecting pixel_num:",pixel_num)
        count_rate = self.ph.settings.count_rate1.read_from_hardware()
        self.display_image_map[k,j,i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_ph_h5[k,j,i] = count_rate
            
            
    def post_scan_cleanup(self):
        del self.count_rate_map_h5
            
        
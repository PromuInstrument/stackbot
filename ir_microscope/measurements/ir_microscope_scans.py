'''
Created on May 10, 2018

@author: Benedikt Ursprung
'''

from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
import time

class IRMicroscope2DScan(AttoCube2DSlowScan):
    
    name = 'ir_microscope_2D_scan'
    
    def setup(self):
        AttoCube2DSlowScan.setup(self)
        self.use_power_feedback_control = self.settings.New("use_power_feedback_control", 
                                                            dtype=bool, initial=False)
        self.save_power_map = self.settings.New('save_power_map', dtype=bool, initial=True)
    
    def pre_scan_setup(self):
        if self.save_power_map.val:
            self.powermeter = self.app.hardware['thorlabs_powermeter']
            self.power_meter_map_h5 = self.h5_meas_group.create_dataset('power_meter_map',
                                                                  shape=self.scan_shape,
                                                                  dtype=float)
        if self.use_power_feedback_control.val:
            self.lpfc = self.app.measurements['laser_power_feedback_control']
            self.lpfc_activation_current_val = self.lpfc.settings.activation.val
            
            self.lpfc.settings.activation.update_value(True)   
            time.sleep(0.1)
            
    def collect_pixel(self, pixel_num, k, j, i):
        if self.save_power_map.val:
            pow_reading = self.powermeter.settings.power.read_from_hardware()
            self.power_meter_map_h5[k,j,i] = pow_reading
    
    def post_scan_cleanup(self):
        if self.use_power_feedback_control.val:
            self.lpfc.settings.activation.update_value(self.lpfc_activation_current_val)
        if hasattr(self, 'h5_file'):
            self.h5_file.close()
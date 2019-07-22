'''
Created on May 10, 2018

@author: Benedikt Ursprung
'''

from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
import time
import datetime


class IRMicroscopeBase2DScan(AttoCube2DSlowScan):
    
    name = 'ir_microscope_base_2D_scan'
    
    def __init__(self, app):
        AttoCube2DSlowScan.__init__(self, app, use_external_range_sync=True, circ_roi_size=0.001,)
        
    def setup(self):
        AttoCube2DSlowScan.setup(self,)
        self.save_power_map = self.settings.New('save_power_map', dtype=bool, initial=False)
        self.save_temperature_map = self.settings.New('save_temperature_map', dtype=bool, initial=False)
        self.save_time_map = self.settings.New('save_time_map', dtype=bool, initial=True)
        self.use_power_feedback_control = self.settings.New("use_power_feedback_control", 
                                                            dtype=bool, initial=False)
        self.use_shutter = self.settings.New('use_shutter', dtype=bool, initial=False)
        self.shutter_open = self.app.lq_path('hardware/shutter/open')
        self.auto_focus_period = self.settings.New('auto_focus_period', int, initial=-1, unit='px')
        
        
    def pre_scan_setup(self):
        if self.save_power_map.val:
            self.powermeter = self.app.hardware['thorlabs_powermeter']
            self.power_meter_map_h5 = self.h5_meas_group.create_dataset('power_meter_map',
                                                                  shape=self.scan_shape,
                                                                  dtype=float,
                                                                  compression ='gzip')
            
        if self.save_temperature_map.val:
            self.tc4 = self.app.hardware['arduino_tc4']
            self.temperature_map_h5 = self.h5_meas_group.create_dataset('temperature_map',
                                                                  shape=self.scan_shape,
                                                                  dtype=float,
                                                                  compression ='gzip')
        if self.save_time_map.val:           
            self.time_map_h5 = self.h5_meas_group.create_dataset('time_map',
                                                                  shape=self.scan_shape,
                                                                  dtype=float,
                                                                  compression ='gzip')
        if self.use_power_feedback_control.val:
            self.lpfc = self.app.measurements['laser_power_feedback_control']
            self.lpfc_activation_current_val = self.lpfc.settings.activation.val
            
            self.lpfc.settings.activation.update_value(True)   
            time.sleep(0.1)
            
        if self.use_shutter.val:   
            self.shutter_open.update_value(True)
            
        self.auto_focus_measure = self.app.measurements['auto_focus']

            
    def collect_pixel(self, pixel_num, k, j, i):
        S = self.settings
        if S['auto_focus_period'] > 0 and pixel_num%S['auto_focus_period'] == 0:
            h_ = self.stage.settings[S['h_axis'] + "_target_position"]
            v_ = self.stage.settings[S['v_axis'] + "_target_position"]
            self.move_position_slow(S['h_center'], S['v_center'], 0, 0)            
            self.start_nested_measure_and_wait(self.auto_focus_measure)
            self.move_position_slow(h_, v_, 0, 0)
        
        t = time.time()-self.t0
        if pixel_num == 1:
            self.dt = t
        if pixel_num > 0:
            sec_remaining = (self.Npixels-(pixel_num+1))*self.dt
            print(self.name, "collecting pixel",
                  "({},{},{})".format(k,j,i),
                  "number:", pixel_num+1,"of",self.Npixels,
                  'estimated time remaining:',datetime.timedelta(seconds=sec_remaining))            

        if self.save_power_map.val:
            pow_reading = self.powermeter.settings.power.read_from_hardware()
            self.power_meter_map_h5[k,j,i] = pow_reading
        if self.save_temperature_map.val:
            self.temperature_map_h5[k,j,i] = self.tc4.read_temp()
        if self.save_time_map.val:           
            self.time_map_h5[k,j,i] = t
            
        
        
    def post_scan_cleanup(self):
        if self.use_power_feedback_control.val:
            self.lpfc.settings.activation.update_value(self.lpfc_activation_current_val)
        if hasattr(self, 'h5_file'):
            self.h5_file.close()
        if self.use_shutter.val:   
            self.shutter_open.update_value(True)
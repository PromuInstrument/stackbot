'''
Created on Aug 31, 2018

@author: Benedikt Ursprung

Just a bunch of small random measurements.
'''
import time
from ScopeFoundry import Measurement



class NestedMeasurements(Measurement):

    name = 'nested_measurements'
    
    
    def run(self):
        print(self.name)
        
        #self.filter_sweep()
        #self.nested_trpl_scans()
        self.timed_toupcam_series(dt=1 , rep=180)
        
        
    def timed_toupcam_series(self, dt=1, rep=10):
        measure = self.app.measurements['toupcam_spot_optimizer']
        auto_focus = self.app.measurements['auto_focus']
        MS = measure.settings
                
        MS['fit_gaus'] = False
        MS['activation'] = False
        
        for i in range(rep):
            self.set_progress((i+1.0)/rep *100.0)
            if self.interrupt_measurement_called:
                break
            #measure.snap_h5()
            print(self.name,  'acquired', i+1, 'of', rep, 'with', measure)
            
            self.start_nested_measure_and_wait(auto_focus)
            
            
            #time.sleep(dt)
        
        
    def nested_trpl_and_hyperspec(self):
        trpl_2d_scan_measure = self.app.measurements['trpl_2d_scan']
        flip_mirror_pos = self.app.hardware_components['thorlabs_MFF'].settings['pos']
        hyperspectral_2d_scan_measure = self.app.measurements['hyperspectral_2d_scan']
        
        flip_mirror_pos.update_value('apd')
        self.start_nested_measure_and_wait(trpl_2d_scan_measure, start_time=1)
        flip_mirror_pos.update_value('spectrometer')
        time.sleep(1)
        self.start_nested_measure_and_wait(hyperspectral_2d_scan_measure, start_time=1)
        
                
    def nested_trpl_scans(self):
        
        picoharp_hist_measure = self.app.measurements['picoharp_histogram']
        trpl_2d_scan_measure = self.app.measurements['trpl_2d_scan']
        
        attocube_xyz_stage_hw = self.app.hardware_components['attocube_xyz_stage']
        

        '''
                    #(z_poition,(x_center,y_center))
        positions = [(4.095906, (12.,5) ),       #5915 
                     (4.004000, (-4.,8) ),       #5916 
                     (4.055940, (2.,-8) ),       #5917 
                     ]    
                    #(z_poition,(x_center,y_center))
        '''
        positions = [(3.885380, (10.,8) ),       #5915
                     
                     (4.135020, (-7.,8) ),       #5918 Voc
                     (4.164720, (-12,8) ),       #5918 Isc
                     
                     (3.987831, (10.,-12) ),     #5916
                     
                     (4.082706, (-8,-12) ),      #5920 Voc
                     (4.086957, (-12,-12) ),     #5920 Isc
                     ]    

        
        '''
        
                    #(z_poition,(x_center,y_center))
        positions = [(5.496982, (12.,8) ),       #5921
                     (4.651930, (2.,8) ),        #5922
                     (5.545881, (-8,5) ),        #5923 
                     (5.401981, (4,-12.4) ),     #5924
                     ]      
        '''
        
        SAVE_Z_POSITION = 0
        
        for j,(z_poition, (x_center,y_center)) in enumerate(positions):
            if self.interrupt_measurement_called:
                break
            self.set_progress( 100*(j+1)/(len(positions)) )
            
            print('prepare moving to next location, moving to z', SAVE_Z_POSITION)
            attocube_xyz_stage_hw.move_and_wait(axis_name='z', new_pos=1)
            self.start_nested_measure_and_wait(picoharp_hist_measure, start_time=1)
            
            print('moving to x,y', x_center, y_center)
            attocube_xyz_stage_hw.move_and_wait(axis_name='x', new_pos=x_center, timeout=70)
            attocube_xyz_stage_hw.move_and_wait(axis_name='y', new_pos=y_center, timeout=70)

            print('focusing: moving to z_position', z_poition)
            attocube_xyz_stage_hw.move_and_wait(axis_name='z', new_pos=z_poition)
            
            time.sleep(1) #probably not necessary anymore ..
            self.app.settings['h_center'] = x_center
            self.app.settings['v_center'] = y_center
            
            print('starting scan (x_center,y_center)',(x_center,y_center))
            self.start_nested_measure_and_wait(trpl_2d_scan_measure, start_time=1)
            time.sleep(1)
            
        
        
    def filter_sweep(self):
        picoharp_hist_measure = self.app.measurements['picoharp_histogram']
        trpl_2d_scan_measure = self.app.measurements['trpl_2d_scan']        
        
        fw = self.app.hardware['filter_wheel']
        pw = self.app.hardware['power_wheel']
        
        filter_nums         = [ 1,  2,  3,  ]
        power_wheel_encoder = [280, 280,280,260,260] #WARNING: use ASCENDING power only
        
        
        for j,_filter in enumerate(filter_nums):
            self.set_progress(100*(j+1)/(len(filter_nums)+1))

            if self.interrupt_measurement_called:
                break
            
            
            print('changing filter to', _filter)
            fw.settings.target_filter.update_value(_filter)

            pw.settings.position.update_value(power_wheel_encoder[j])
            
            time.sleep(2)
            self.start_nested_measure_and_wait(trpl_2d_scan_measure)
            
            self.set_progress( 100*(j+1)/(len(filter_nums)+1) )

            
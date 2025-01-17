from ScopeFoundry import Measurement
from ScopeFoundryHW.sync_raster_daq import SyncRasterScan
import time
import numpy as np
from Auger.auger_spectrum import AugerSpectrum

import configparser
from datetime import datetime
import os
'''
    Todo list
    Finish output scan callback low level **DONE**
    track per-frame offset due to rt drift correction or operator action in HDF **DONE**
    display per-frame offset
    track span and timestamp
        get display working in real distance units
    Should CTR be dropped since not used? 
    Implement shutdown of EHT, mult after acq  **DONE** ('eht_off_at_end' option, mult always turns off)
    Implement multi-peak hyperspectral acq, HDF, viewer...
        config-parser ini to save peak data [name, 
    Add area-integrated spectrum to RT display
    Save/load SEM params, requires manual gun align info
    
    Modify remcon32_hw so kV is only updated from HW if EHT is on (otherwise 
        saved value set to zero. kV control should remember target while EHT is off
'''

class AugerSyncRasterScan(SyncRasterScan):
    
    name = "auger_sync_raster_scan"
    
    def setup(self):
        SyncRasterScan.setup(self)
        self.display_update_period = 0.1
        
        self.disp_chan_choices +=  ['auger{}'.format(i) for i in range(10)] + ['sum_auger']
        self.settings.display_chan.change_choice_list(tuple(self.disp_chan_choices))
        
        self.settings.New('ke_start', dtype=float, initial=30,unit = 'V',vmin=5,vmax = 2200)
        self.settings.New('ke_end',   dtype=float, initial=600,unit = 'V',vmin=1,vmax = 2200)
        self.settings.New('ke_delta', dtype=float, initial=0.5,unit = 'V',vmin=0.02979,vmax = 2200,si=True)
        self.settings.New('pass_energy', dtype=float, initial=50,unit = 'V', vmin=5,vmax=500)
        self.settings.New('crr_ratio', dtype=float, initial=5, vmin=1.5,vmax=20)
        self.settings.New('CAE_mode', dtype=bool, initial=False)      

        for lq_name in ['ke_start', 'ke_end', 'ke_delta', 'CAE_mode']:
            self.settings.get_lq(lq_name).add_listener(self.compute_ke)
        
        self.settings.New('eht_off_at_end', dtype=bool, initial=False)
        
        self.ui.details_groupBox.layout().addWidget(self.settings.New_UI()) # comment out?

        self.settings.New('No_dispersion', dtype=bool, initial=False)
        self.settings.New('Chan_sum', dtype=bool, initial=True)
        
        self.settings.New('auto_focus', dtype=bool, initial=False)
        self.settings.New('frames_before_focus', dtype=int, initial=5, vmin=1)

        #self.ui.centralwidget.layout().addWidget(self.settings.New_UI(), 0,0)
        #self.testui = self.settings.New_UI()
        #self.testui.show()
        
    def compute_ke(self):
        '''
        calculate ke[i] for each channel over spectral region based on dispersion and
        analyzer parameters
        '''
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']

        CAE_mode = self.settings['CAE_mode']
        ke_start = self.settings['ke_start']
        low_ke = min( self.analyzer_hw.analyzer.get_chan_ke(ke_start,CAE_mode))
        ke_end = self.settings['ke_end']
        high_ke = max( self.analyzer_hw.analyzer.get_chan_ke(ke_end,CAE_mode))
        ke_delta = self.settings['ke_delta']
        self.npoints = int((high_ke-low_ke)/ke_delta)+1
        self.ke = np.zeros((7,self.npoints))
        self.ke[0,:] = np.linspace(low_ke,high_ke,num=self.npoints)
        for i in range(self.npoints):
            ke0 = self.ke[0,i]
            self.ke[:,i] = self.analyzer_hw.analyzer.get_chan_ke(ke0,CAE_mode)
        self.settings['n_frames'] = self.npoints
        return self.ke


    def on_start_of_run(self):
        # Hardware
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()

        self.auger_fpga_hw.settings['trigger_mode'] = 'pxi'
        
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        
        self.analyzer_hw.settings['multiplier'] = True
        self.analyzer_hw.settings['CAE_mode'] = self.settings['CAE_mode']
        self.analyzer_hw.settings['KE'] = self.settings['ke_start']
        self.analyzer_hw.settings['pass_energy'] = self.settings['pass_energy']
        self.analyzer_hw.settings['crr_ratio'] = self.settings['crr_ratio']
        
        
        time.sleep(3.0) #let electronics settle, multiplier ramp up finish

        # set up KE array
        self.compute_ke()
        
    def pre_scan_setup(self):
        # Data Arrays
        self.auger_queue = []
        self.auger_i = 0
        self.auger_total_i = 0
        self.auger_chan_pixels = np.zeros((self.Npixels, 10), dtype=np.uint32)
        self.auger_chan_map = np.zeros( self.scan_shape + (10,), dtype=np.uint32)
        if self.settings['save_h5']:
            self.auger_chan_map_h5 = self.create_h5_framed_dataset("auger_chan_map", self.auger_chan_map)            
            self.h5_m['ke'] = self.ke
        # figure?
        
        self.app.hardware['sem_remcon'].read_from_hardware()
        
    def handle_new_data(self):
        """ Called during measurement thread wait loop"""
        SyncRasterScan.handle_new_data(self)
        
        new_auger_data = self.auger_fpga_hw.read_fifo()
        self.auger_queue.append(new_auger_data)
        
        #ring_buf_index_array = (i + np.arange(n, dtype=int)) % self.Npixels
        #self.auger_chan_pixels[ring_buf_index_array] = new_auger_data
        
        while len(self.auger_queue) > 0:
            # grab the next available data chunk
            #print('new_adc_data_queue' + "[===] "*len(self.new_adc_data_queue))            
            new_data = self.auger_queue.pop(0)
            i = self.auger_i
            n = new_data.shape[0]

            # grab only up to end of frame, put the rest back in the queue
            if i + n > self.Npixels:
                split_index = (self.Npixels - i )
                print("split", i, n, split_index, self.Npixels)
                self.auger_queue.append(new_data[split_index: ])
                new_data = new_data[0:split_index]
                n = new_data.shape[0]
            
            # copy data to image shaped map
            self.auger_chan_pixels[i:i+n,:] = new_data
            x = self.scan_index_array[i:i+n,:].T
            self.auger_chan_map[x[0], x[1], x[2],:] = new_data
            
            # new frame
            if self.auger_i == 0:
                frame_num = (self.auger_total_i // self.Npixels) - 1
                if self.settings['save_h5']:
                    self.extend_h5_framed_dataset(self.auger_chan_map_h5, frame_num)
                    self.auger_chan_map_h5[frame_num,:,:,:,:] = self.auger_chan_map

            if self.interrupt_measurement_called:
                break
        
            self.auger_i += n
            self.auger_total_i += n 
            self.auger_i %= self.Npixels

        print(new_auger_data.shape)

    
    def post_scan_cleanup(self):
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'
        self.analyzer_hw.settings['multiplier'] = False
        self.analyzer_hw.settings['KE'] = self.ke[0,0]
        if self.settings['eht_off_at_end']:
            self.app.hardware['sem_remcon'].settings['eht_on'] = False
            
    def get_display_pixels(self):
        #SyncRasterScan.get_display_pixels(self)
        #self.display_pixels = self.auger_chan_pixels[:,0:8].sum(axis=1)
        #self.display_pixels[0] = 0
        #self.display_pixels = self._pixels[:,0]
        
        #DISPLAY_CHAN = 0
        #self.display_pixels = self.adc_pixels[:,DISPLAY_CHAN]
        #self.display_pixels[0] = 0
        
        chan = self.settings['display_chan']
        if 'auger' in chan:
            if chan == 'sum_auger':
                self.display_pixels = self.auger_chan_pixels[:,0:8].sum(axis=1)
            else:
                self.display_pixels = self.auger_chan_pixels[:,int(chan[-1])]
        else:
            return SyncRasterScan.get_display_pixels(self)


    
    def on_new_frame(self, frame_i):
        SyncRasterScan.on_new_frame(self, frame_i)
        
        self.analyzer_hw.settings['KE'] = self.ke[0,frame_i]
    
    def on_end_frame(self, frame_i):
        SyncRasterScan.on_end_frame(self, frame_i)
        
        # Need to figure out how to pause scanning for auto-focus
        
#         # Auto-focus -- Run auto-focus routine here
#         if np.mod(frame_i+1, self.settings['frames_before_focus']) == 0:
#             wd_cur = self.app.hardware['sem_remcon'].settings['WD'] # Gives value in mm
#             # Take images at working distances over a +- 50 um range with 5 um precision (20 images)
#             wd_range = np.arange(wd_cur-0.050,wd_cur+0.050,0.005)
#             # Need to perform the scans...
    

        
class MultiSpecAugerScan(Measurement):
    
    name = 'multi_spec_auger_scan'
    
    def setup(self):
        
        self.settings.New('multispec_setting_names', dtype=str)
        self.settings.New('settings_file', dtype='file', initial='auger_sync_scan_settings.ini')
        self.settings.New('eht_off_after_multispec', dtype=bool)
        
        self.auger_scan = self.app.measurements['auger_sync_raster_scan']
        
        
        
    def run(self):
        
        # Default configparser reads keys in lowercase, change so it's case sensitive
        self.config = configparser.RawConfigParser()
        self.config.optionxform = lambda option: option
        self.config.read(self.settings['settings_file'])
        
        
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(time.time()),
            ext='ini')
        fname = os.path.join(self.app.settings['save_dir'], f)        
        self.app.settings_save_ini(fname)
        
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        
        interrupted = False
        
        names_to_read = self.settings['multispec_setting_names'].split(',')
        names_to_read = [name.strip() for name in names_to_read]
        for i, name in enumerate(names_to_read):
            if self.interrupt_measurement_called:
                self.auger_scan.interrupt()
                interrupted = True
                break
            self.set_progress(100.*i/len(names_to_read))
            # Update measurement settings
            for key in self.config[name]:
                self.auger_scan.settings[key] = self.config[name][key]
            # Update analyzer hardware settings
            auger_hw_name = name + '/auger_electron_analyzer'
            for key in self.config[auger_hw_name]:
                self.analyzer_hw.settings[key] = self.config[auger_hw_name][key]
            # Start the measurement
            print('Start measurement', name)
            self.auger_scan.start()

            # Wait for measurement to finish before running next measurement
            while self.auger_scan.is_measuring():
                if self.interrupt_measurement_called:
                    self.auger_scan.interrupt()
                    interrupted = True
                    break
                #self.auger_scan.update_display()
                time.sleep(1.0)
        
        if not interrupted and self.settings['eht_off_after_multispec']:
            self.app.hardware['sem_remcon'].settings['eht_on'] = False
        
        
    def update_display(self):
        self.auger_scan.update_display()
        
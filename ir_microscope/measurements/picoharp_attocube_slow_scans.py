from __future__ import print_function, absolute_import, division
from ScopeFoundryHW.mcl_stage import MCLStage2DSlowScan
import ScopeFoundry
from ScopeFoundry.helper_funcs import sibling_path

import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan

class Picoharp_AttoCube_2DSlowScan(AttoCube2DSlowScan):
    
    name = 'trpl_scan'
    def setup(self):
        AttoCube2DSlowScan.setup(self)
        self.ph_hw = self.app.hardware['picoharp']
        
        dui_filename = sibling_path(__file__,"picoharp_hist_measure_details.ui")
        self.dui = self.set_details_widget(dui_filename)
        
        ph_hw = self.ph_hw

        S = self.settings
        S.New('use_calc_hist_chans', dtype=bool, initial=True)
        
        S.use_calc_hist_chans.connect_to_widget(self.dui.use_calc_hist_chans_checkBox)        
        ph_hw.settings.Tacq.connect_to_widget(self.dui.picoharp_tacq_doubleSpinBox)
        ph_hw.settings.Binning.connect_to_widget(self.dui.Binning_comboBox)
        ph_hw.settings.count_rate0.connect_to_widget(self.dui.ch0_doubleSpinBox)
        ph_hw.settings.count_rate1.connect_to_widget(self.dui.ch1_doubleSpinBox)
        ph_hw.settings.histogram_channels.connect_to_widget(self.dui.histogram_channels_doubleSpinBox)
        
    
    def pre_scan_setup(self):
        
        self.ph  = self.ph_hw.picoharp
        
        self.sleep_time = min((max(0.1*self.ph.Tacq*1e-3, 0.010), 0.100))
        if self.settings['use_calc_hist_chans']:
            self.ph_hw.settings['histogram_channels'] = self.ph_hw.calc_num_hist_chans() 
                    
        self.num_hist_chans=self.ph_hw.settings['histogram_channels']
        self.data_slice = slice(0,self.num_hist_chans)
        

        self.integrated_count_map_h5 = self.h5_meas_group.create_dataset('integrated_count_map', 
                                                                   shape=self.scan_shape,
                                                                   dtype=float, 
                                                                   compression='gzip')

        time_trace_map_shape = self.scan_shape + (self.num_hist_chans,)
       
        
        self.time_array = self.ph.time_array*1e-3
        self.h5_meas_group['time_array'] = self.time_array[self.data_slice]
        self.elapsed_time_h5 = self.h5_meas_group['elapsed_time'] = np.zeros(self.scan_shape, dtype=float)
        
        #self.app.settings_auto_save()
        

        # pyqt graph
        self.initial_scan_setup_plotting = True

    def post_scan_cleanup(self):
        pass
    
    def collect_pixel(self, pixel_num, k, j, i):
        
        # collect data
        print(self.name, 'collect_pixel', pixel_num, k, j, i)
        #t0 = time.time()

        #hist_data, elapsed_time = self.read_picoharp_histogram()
        
        ph = self.ph_hw.picoharp
        ph.start_histogram()
        while not ph.check_done_scanning():
            self.ph_hw.settings.count_rate0.read_from_hardware()
            self.ph_hw.settings.count_rate1.read_from_hardware()
            if self.ph_hw.settings['Tacq'] > 0.2:
                ph.read_histogram_data()
            time.sleep(0.005) #self.sleep_time)  
        ph.stop_histogram()
        #ta = time.time()
        ph.read_histogram_data()

        hist_data = ph.histogram_data[self.data_slice]
        elapsed_time = ph.read_elapsed_meas_time()

        self.time_trace_map_h5[k,j,i, :] = hist_data
        
        self.elapsed_time_h5[k,j,i] = elapsed_time

        # display count-AC_FRAMERATE
        self.integrated_count_map_h5[k,j,i] = hist_data.sum() * 1.0/elapsed_time
        self.display_image_map[k,j,i] = hist_data.sum() * 1.0/elapsed_time
        
        import datetime
        print('pixel',  datetime.timedelta(seconds=(self.Npixels - pixel_num)*elapsed_time*1e-3), 'left')
        
        print( 'pixel done' )
    
    def read_picoharp_histogram(self):

        ph = self.ph_hw.picoharp

        ph.start_histogram()

        while not ph.check_done_scanning():
            if self.ph_hw.settings['Tacq'] > 200:
                ph.read_histogram_data()
            time.sleep(0.005) #self.sleep_time)  
        ph.stop_histogram()
        #ta = time.time()
        ph.read_histogram_data()

        return ph.histogram_data, ph.read_elapsed_meas_time()
    
    def read_picoharp_timearray(self):
        return self.ph.time_array()

        
    def update_display(self):
        AttoCube2DSlowScan.update_display(self)
        
        # setup lifetime window
        if not hasattr(self, 'lifetime_graph_layout'):
            self.lifetime_graph_layout = pg.GraphicsLayoutWidget()
            self.lifetime_plot = self.lifetime_graph_layout.addPlot()
            self.lifetime_plotdata = self.lifetime_plot.plot()
            self.lifetime_plot.setLogMode(False, True)
            self.lifetime_plot.enableAutoRange('y',True)
        
        if not hasattr(self, 'infline'):
            self.infline = pg.InfiniteLine(movable=False, angle=90, label='stored_hist_chans', 
                labelOpts={'position':0.1, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True}) 
            self.lifetime_plot.addItem(self.infline)
            
            
                

        self.lifetime_graph_layout.show()
        pos_x = self.time_array[self.ph_hw.settings['histogram_channels']]
        self.lifetime_plot.setRange(xRange=(0,1.2*pos_x))
        self.lifetime_plot.enableAutoRange('y',True)
        
        self.infline.setPos([pos_x,0])
        
        self.infline.label.setPosition(0.8)        
        
        #kk, jj, ii = self.current_scan_index
        ph = self.ph_hw.picoharp
        self.lifetime_plotdata.setData(self.time_array,  1+ph.histogram_data)

'''        
class Picoharp_AttoCube_3DSlowScan(AttoCube3DStackSlowScan):
    
    name = 'Picoharp_AttoCube_3DSlowScan'
    
    def pre_scan_setup(self):
        #hardware 
        self.ph_hw = self.app.hardware['picoharp']
        ph = self.ph_hw.picoharp # low level hardware
        
        #scan specific setup
        
        # create data arrays
        
        cr0 = self.ph_hw.settings.count_rate0.read_from_hardware()
        rep_period_s = 1.0/cr0
        time_bin_resolution = self.ph_hw.settings['Resolution']*1e-12
        self.num_hist_chans = int(np.ceil(rep_period_s/time_bin_resolution))

        time_trace_map_shape = self.scan_shape + (self.num_hist_chans,)
        self.time_trace_map = np.zeros(time_trace_map_shape, dtype=float)
        
        
        self.time_trace_map_h5 = self.create_h5_framed_dataset(name='time_trace_map', single_frame_map=self.time_trace_map)
        
        self.time_array = self.h5_meas_group['time_array'] = ph.time_array[0:self.num_hist_chans]*1e-3
        
        self.elapsed_time = np.zeros(self.scan_shape, dtype=float)
        self.elapsed_time_h5 = self.create_h5_framed_dataset('elasped_time', self.elapsed_time)
        
        #self.app.settings_auto_save()
        
        # pyqt graph
        #self.initial_scan_setup_plotting = True

        
    def post_scan_cleanup(self):
        # close shutter 
        #self.gui.shutter_servo_hc.shutter_open.update_value(False)
        pass
    
    def collect_pixel(self, pixel_num, frame_i, k, j, i):
        
        # collect data
        print(pixel_num, frame_i, k, j, i)
        t0 = time.time()
        
        hist_data, elapsed_time = Picoharp_MCL_2DSlowScan.read_picoharp_histogram(self)

        # store in arrays
        self.time_trace_map[k,j,i, :] = hist_data[0:self.num_hist_chans]
        self.time_trace_map_h5[frame_i,k,j,i, :] = hist_data[0:self.num_hist_chans]
        
        self.elapsed_time[k,j,i] = elapsed_time
        self.elapsed_time_h5[frame_i, k,j,i] = elapsed_time

        # display count-rate
        self.display_image_map[k,j,i] = hist_data[0:self.num_hist_chans].sum() * 1.0/elapsed_time
        
        print( 'pixel done' )
        
    def on_new_frame(self, frame_i):
        AttoCube3DStackSlowScan.on_new_frame(self, frame_i)
        self.extend_h5_framed_dataset(self.time_trace_map_h5, frame_i)
        self.extend_h5_framed_dataset(self.elapsed_time_h5, frame_i)
        
    def on_end_frame(self, frame_i):
        AttoCube3DStackSlowScan.on_end_frame(self, frame_i)
        self.h5_file.flush()
        
    def update_display(self):
        AttoCube3DStackSlowScan.update_display(self)
    '''
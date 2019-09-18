from ScopeFoundry.helper_funcs import sibling_path

import time
import pyqtgraph as pg
from ir_microscope.measurements.ir_microscope_base_scans import IRMicroscopeBase2DScan
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase 
import datetime

class TRPL2DScan(IRMicroscopeBase2DScan, TRPL2DScanBase):
    
    name = 'trpl_2d_scan'
        
    def __init__(self, app):
        IRMicroscopeBase2DScan.__init__(self, app)
        TRPL2DScanBase.__init__(self, app, None)
    
    def setup(self):
        IRMicroscopeBase2DScan.setup(self)
        TRPL2DScanBase.setup(self)
    
    def setup_figure(self):
        TRPL2DScanBase.setup_figure(self)

    def pre_scan_setup(self):
        IRMicroscopeBase2DScan.pre_scan_setup(self)
        TRPL2DScanBase.pre_scan_setup(self)
    
    def collect_pixel(self, pixel_num, k, j, i):
        IRMicroscopeBase2DScan.collect_pixel(self, pixel_num, k, j, i)   
        TRPL2DScanBase.collect_pixel(self, pixel_num, k, j, i)

    def post_scan_cleanup(self):
        IRMicroscopeBase2DScan.post_scan_cleanup(self)
        TRPL2DScanBase.post_scan_cleanup(self)
        
    def update_display(self):
        IRMicroscopeBase2DScan.update_display(self)
        TRPL2DScanBase.update_display(self)

class TRPL2DScan_old(IRMicroscopeBase2DScan):
    
    name = 'trpl_2d_scan'
    
    def __init__(self, app, shutter_open_lq_path=None):
        IRMicroscopeBase2DScan.__init__(self, app)
        self.shutter_open_lq_path = shutter_open_lq_path

    
    def setup(self):
        IRMicroscopeBase2DScan.setup(self)
        self.ph_hw = self.app.hardware['picoharp']
        
        dui_filename = sibling_path(__file__,"picoharp_hist_measure_details.ui")
        self.dui = self.set_details_widget(ui_filename=dui_filename)
        
        ph_hw = self.ph_hw

        S = self.settings
        S.New('use_calc_hist_chans', dtype=bool, initial=True)
        
        S.use_calc_hist_chans.connect_to_widget(self.dui.use_calc_hist_chans_checkBox)        
        ph_hw.settings.Tacq.connect_to_widget(self.dui.picoharp_tacq_doubleSpinBox)
        ph_hw.settings.Binning.connect_to_widget(self.dui.Binning_comboBox)
        ph_hw.settings.count_rate0.connect_to_widget(self.dui.ch0_doubleSpinBox)
        ph_hw.settings.count_rate1.connect_to_widget(self.dui.ch1_doubleSpinBox)
        ph_hw.settings.histogram_channels.connect_to_widget(self.dui.histogram_channels_doubleSpinBox)
        
        self.settings.New('acq_mode', str, initial = 'const_time', choices = ('const_sig_counts','const_time'))
        self.settings.New('dark_counts', int, initial = 40000, unit = 'Hz')
        self.settings.New('total_signal_counts', int, initial = 90000, unit='cts')
        self.settings.New('dark_histograms_accumulations', int, initial=5)



    def pre_scan_setup(self):
        IRMicroscopeBase2DScan.pre_scan_setup(self)
        
        ph = self.ph  = self.ph_hw.picoharp
        S = self.settings
        
        
        self.sleep_time = min((max(0.1*self.ph.Tacq*1e-3, 0.010), 0.100))
        if S['use_calc_hist_chans']:
            self.ph_hw.settings['histogram_channels'] = self.ph_hw.calc_num_hist_chans() 
                    
        self.num_hist_chans=self.ph_hw.settings['histogram_channels']
        self.data_slice = slice(0,self.num_hist_chans)

        
        self.integrated_count_map_h5 = self.h5_meas_group.create_dataset('integrated_count_map', 
                                                                   shape=self.scan_shape,
                                                                   dtype=float, 
                                                                   compression='gzip')

        time_trace_map_shape = self.scan_shape + (self.num_hist_chans,)
        self.time_trace_map_h5 = self.h5_meas_group.create_dataset('time_trace_map',
                                                              shape=time_trace_map_shape,
                                                              dtype=float)
        
        self.elapsed_time_h5 = self.h5_meas_group.create_dataset('elaspsed_time',
                                                                   shape=self.scan_shape,
                                                                   dtype=float, 
                                                                   compression='gzip')
        
        self.time_array = self.ph.time_array*1e-3
        self.h5_meas_group['time_array'] = self.time_array[self.data_slice]

        # measure dark counts
        if self.shutter_open_lq_path is not None:
            self.shutter_open = self.app.lq_path(self.shutter_open_lq_path)
            if S['dark_histograms_accumulations'] != 0:
                self.shutter_open.update_value(False)
                time.sleep(2) #wait for shutter to open!
                hist_data = self.aquire_histogram()   
                print(type(hist_data) )
                i = 0
                while i < S['dark_histograms_accumulations'] and not self.interrupt_measurement_called:
                    hist_data += self.aquire_histogram()
                    i += 1
                hist_data = 1.0 * hist_data / (1.0*S['dark_histograms_accumulations'])
                self.h5_meas_group.create_dataset('dark_histogram', data=hist_data)
                S['dark_counts'] = hist_data.sum()
                
            if self.shutter_open.val == False:
                self.shutter_open.update_value(True)
                print(self.name, 'opening shutter')
                time.sleep(2)
 
        # pyqt graph
        self.initial_scan_setup_plotting = True

    def aquire_histogram(self):
        ph = self.ph_hw.picoharp
        
        if self.settings['acq_mode'] == 'const_time':
            ph.start_histogram()
            while not ph.check_done_scanning():
                self.ph_hw.settings.count_rate0.read_from_hardware()
                self.ph_hw.settings.count_rate1.read_from_hardware()
                if self.ph_hw.settings['Tacq'] > 0.2:
                    ph.read_histogram_data()
                time.sleep(0.005) #self.sleep_time)  
            ph.stop_histogram()
            
            
        if self.settings['acq_mode'] == 'const_sig_counts':
            t_start_pixel = time.time()
            ph.start_histogram()
            while not ph.check_done_scanning():
                ph.read_histogram_data()
                hist_data = ph.histogram_data[self.data_slice]
                t_measure = time.time()-t_start_pixel
                total_signal = hist_data.sum() - self.settings['dark_counts']*t_measure
                if total_signal >= self.settings['total_signal_counts']:
                    print(t_measure)
                    ph.stop_histogram()
                    break
            
        ph.read_histogram_data()        
        hist_data = ph.histogram_data[self.data_slice]
        return hist_data  
    

    def post_scan_cleanup(self):
        IRMicroscopeBase2DScan.post_scan_cleanup(self)

    
    def collect_pixel(self, pixel_num, k, j, i):
        IRMicroscopeBase2DScan.collect_pixel(self, pixel_num, k, j, i)
        # collect data
        print(self.name, 'collect_pixel', pixel_num, k, j, i)
        
        hist_data = self.aquire_histogram()
        self.time_trace_map_h5[k,j,i, :] = hist_data
        
        elapsed_time = self.ph_hw.picoharp.read_elapsed_meas_time()
        self.elapsed_time_h5[k,j,i] = elapsed_time

        # display count-AC_FRAMERATE
        self.integrated_count_map_h5[k,j,i] = hist_data.sum() * 1.0/elapsed_time
        self.display_image_map[k,j,i] = hist_data.sum() * 1.0/elapsed_time

        print('pixel',  datetime.timedelta(seconds=(self.Npixels - pixel_num)*elapsed_time*1e-3), 'left')
        
    
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
        IRMicroscopeBase2DScan.update_display(self)
        
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
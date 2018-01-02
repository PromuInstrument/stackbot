from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import numpy as np
import time
import pyqtgraph as pg
from winioctlcon import IOCTL_DISK_HISTOGRAM_DATA
from ScopeFoundry import h5_io

class PicoHarpHistogramMeasure(Measurement):    
    name = "picoharp_histogram"
    
    hardware_requirements = ['picoharp']
    
    def setup(self):
        self.display_update_period = 0.1 #seconds
        
        S = self.settings

        S.New('save_h5', dtype=bool, initial=True)
        S.New('continuous', dtype=bool, initial=False)
        S.New('use_calc_hist_chans', dtype=bool, initial=True)
        
        # hardware
        ph_hw = self.picoharp_hw = self.app.hardware['picoharp']

        
        # UI 
        self.ui_filename = sibling_path(__file__,"picoharp_hist_measure.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        
        #connect events
        S.progress.connect_to_widget(self.ui.progressBar)
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        S.continuous.connect_to_widget(self.ui.continuous_checkBox)
        
        S.use_calc_hist_chans.connect_to_widget(self.ui.use_calc_hist_chans_checkBox)
        ph_hw.settings.Tacq.connect_to_widget(self.ui.picoharp_tacq_doubleSpinBox)
        ph_hw.settings.Binning.connect_to_widget(self.ui.Binning_comboBox)
        ph_hw.settings.histogram_channels.connect_to_widget(self.ui.histogram_channels_doubleSpinBox)
        ph_hw.settings.count_rate0.connect_to_widget(self.ui.ch0_doubleSpinBox)
        ph_hw.settings.count_rate1.connect_to_widget(self.ui.ch1_doubleSpinBox)
        
        
        S.save_h5.connect_to_widget(self.ui.save_h5_checkBox)

    
    def setup_figure(self):
        self.graph_layout = pg.GraphicsLayoutWidget()    
        self.plot = self.graph_layout.addPlot()
        
        
        self.infline = pg.InfiniteLine(movable=False, angle=90, label='stored_hist_chans', 
                       labelOpts={'position':0.8, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True}) 
        self.plot.addItem(self.infline)
        
        self.plotdata = self.plot.plot(pen='r')
        self.plot.setLogMode(False, True)
        self.plot.enableAutoRange('y',True)
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
                
    def run(self):
        self.ph_hw = self.app.hardware['picoharp']
        self.ph = self.ph_hw.picoharp
        if self.settings['use_calc_hist_chans']:
            self.ph_hw.settings['histogram_channels'] = self.ph_hw.calc_num_hist_chans() 
        
        self.sleep_time = min((max(0.1*self.ph.Tacq*1e-3, 0.010), 0.100))
        self.t0 = time.time()
    
        while not self.interrupt_measurement_called:  
            self.ph.start_histogram()
            while not self.ph.check_done_scanning():
                self.set_progress( 100*(time.time() - self.t0)/self.ph_hw.settings['Tacq'] )
                if self.interrupt_measurement_called:
                    break
                self.ph.read_histogram_data()
                self.ph_hw.settings.count_rate0.read_from_hardware()
                self.ph_hw.settings.count_rate1.read_from_hardware()
                time.sleep(self.sleep_time)
    
            self.ph.stop_histogram()
            self.ph.read_histogram_data()
        
            if not self.settings['continuous']:
                break
            
    
        self.data_slice = slice(0,self.ph_hw.settings['histogram_channels'])
        histogram_data = self.ph.histogram_data[self.data_slice]
        time_array = self.ph.time_array[self.data_slice]
        elapsed_meas_time = self.ph.read_elapsed_meas_time()
        
        if self.settings['save_h5']:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
            self.h5_file.attrs['time_id'] = self.t0
            
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            H['time_histogram'] = histogram_data
            H['time_array'] = time_array
            H['elapsed_meas_time'] = elapsed_meas_time
            
            self.h5_file.close()

                   
    def update_display(self):
        ph = self.ph
        time_array = ph.time_array*1e-3
        pos_x = time_array[self.ph_hw.settings['histogram_channels']]
        self.plot.setRange(xRange=(0,1.2*pos_x))
        self.infline.setPos([pos_x,0])        
        self.plotdata.setData(time_array, ph.histogram_data+1)

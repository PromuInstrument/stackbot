from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundry import h5_io

class HydrHarpHistogramMeasure(Measurement):    
    name = "hydraharp_histogram"
    
    hardware_requirements = ['hydraharp']
    
    def setup(self):
        self.display_update_period = 0.1 #seconds
        
        S = self.settings

        S.New('save_h5', dtype=bool, initial=True)
        S.New('continuous', dtype=bool, initial=False)
        S.New('use_calc_hist_chans', dtype=bool, initial=True)
        
        # hardware
        hw = self.hw = self.app.hardware['hydraharp']

        
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
        hw.settings.Tacq.connect_to_widget(self.ui.picoharp_tacq_doubleSpinBox)
        hw.settings.Binning.connect_to_widget(self.ui.Binning_comboBox)
        #hw.settings.histogram_channels.connect_to_widget(self.ui.histogram_channels_doubleSpinBox)
        #hw.settings.count_rate0.connect_to_widget(self.ui.ch0_doubleSpinBox)
        #hw.settings.count_rate1.connect_to_widget(self.ui.ch1_doubleSpinBox)
        
        
        S.save_h5.connect_to_widget(self.ui.save_h5_checkBox)

    
    def setup_figure(self):
        self.graph_layout = pg.GraphicsLayoutWidget()    
        self.plot = self.graph_layout.addPlot()
        
        
        self.infline = pg.InfiniteLine(movable=False, angle=90, label='stored_hist_chans', 
                       labelOpts={'position':0.8, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True}) 
        self.plot.addItem(self.infline)
        
        #self.plotdata = self.plot.plot(pen='r')
        self.plot.setLogMode(False, True)
        self.plot.enableAutoRange('y',True)
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
                
    def run(self):
        
        self.display_ready = False
        
        self.hw = hw = self.app.hardware['hydraharp']
        Tacq = hw.settings['Tacq']

#         if self.settings['use_calc_hist_chans']:
#             self.ph_hw.settings['histogram_channels'] = self.hw.calc_num_hist_chans() 
        
        self.sleep_time = min((max(0.1*Tacq, 0.010), 0.100))
        self.t0 = time.time()
        
    
        while not self.interrupt_measurement_called:  
            hw.start_histogram()
            if Tacq < 0.1:
                time.sleep(Tacq+5e-3)
            else:
                while not hw.check_done_scanning():
                    self.set_progress( 100*(time.time() - self.t0)/Tacq )
                    if self.interrupt_measurement_called:
                        break
                    self.hist_data = hw.read_histogram_data(clear_after=False)
                    time.sleep(self.sleep_time)
            hw.stop_histogram()
            #self.hist_data = hw.read_histogram_data(clear_after=True)
        
            if not self.settings['continuous']:
                break
            
    
        #self.data_slice = slice(0,self.ph_hw.settings['histogram_channels'])
        #histogram_data = self.hist_data[:, self.data_slice]
        #time_array = self.ph.time_array[self.data_slice]
        elapsed_meas_time = hw.settings.ElapsedMeasTime.read_from_hardware()
        
        if self.settings['save_h5']:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
            self.h5_file.attrs['time_id'] = self.t0
            
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            #H['time_histogram'] = histogram_data
            #H['time_array'] = time_array
            H['elapsed_meas_time'] = elapsed_meas_time
            
            self.h5_file.close()

                   
    def update_display(self):
        
        if not self.display_ready:
            self.plot.clear()
            self.plot.setLabel('bottom', text="Time", units='s')
            self.plotlines = []
            for i in range(self.hw.n_channels):
                self.plotlines.append(self.plot.plot(label=i))
            self.display_ready = True
                        
        #pos_x = time_array[self.ph_hw.settings['histogram_channels']]
        #self.plot.setRange(xRange=(0,1.2*pos_x))
        #self.infline.setPos([pos_x,0])
        for i in range(self.hw.n_channels):      
            self.plotlines[i].setData(self.hw.time_array*1e-12, self.hist_data[i,:]+1)

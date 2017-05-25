'''Frank Ogletree'''

from __future__ import division
from ScopeFoundry import Measurement, h5_io
import pyqtgraph as pg
import numpy as np
from scipy import interpolate
import time
from qtpy import QtWidgets

class AugerSpectrum(Measurement):
    
    name = "auger_spectrum"
   
    
    def setup(self):
        
        self.settings.New('ke_start', dtype=float, initial=30,unit = 'V',vmin=0,vmax = 2200)
        self.settings.New('ke_end',   dtype=float, initial=600,unit = 'V',vmin=1,vmax = 2200)
        self.settings.New('ke_delta', dtype=float, initial=0.5,unit = 'V',vmin=0.02979,vmax = 2200,si=True)
        self.settings.New('dwell', dtype=float, initial=0.05,unit = 's', si=True,vmin=1e-4)
        self.settings.New('pass_energy', dtype=float, initial=50,unit = 'V', vmin=5,vmax=500)
        self.settings.New('crr_ratio', dtype=float, initial=5, vmin=1.5,vmax=20)
        self.settings.New('CAE_mode', dtype=bool, initial=False)
        self.settings.New('No_dispersion', dtype=bool, initial=False)
        self.settings.New('Chan_sum', dtype=bool, initial=True)       
       
        self.display_update_period = 0.01 
        
            #setup gui
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
        self.ui.setLayout(self.layout)
        self.control_widget = QtWidgets.QGroupBox(self.name)
        self.layout.addWidget(self.control_widget, stretch=0)
        self.control_widget.setLayout(QtWidgets.QVBoxLayout())
        
        self.start_button= QtWidgets.QPushButton("Start")
        self.control_widget.layout().addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.control_widget.layout().addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        ui_list = ('ke_start', 'ke_end', 'ke_delta', 'dwell', 'pass_energy', 'crr_ratio','CAE_mode')
        self.control_widget.layout().addWidget(self.settings.New_UI(include=ui_list))
        
       
        self.display_chans = 7        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.layout.addWidget(self.graph_layout, stretch=1)
        
        self.ui.show()
        self.ui.setWindowTitle("auger_spectrum")
        
            #hardware setup
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        self.sem_ = self.app.hardware['sem_remcon']
        #self.analyzer = self.analyzer_hw.analyzer
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        
        self.plot = self.graph_layout.addPlot(title="Auger Spectrum")
        self.plot_setup()
                    
    def plot_setup(self):
        ''' create plots for channels and/or sum'''
        self.plot_lines = []
        for i in range(self.display_chans):
            color = pg.intColor(i+1)
            plot_line = self.plot.plot([0], pen=color)
            self.plot_lines.append(plot_line)
            #channel average
        color = pg.intColor(0)
        plot_line = self.plot.plot([0], pen=color)
        self.plot_lines.append(plot_line)
        
     
    def reset_fpga(self):   
        self.auger_fpga_hw.settings['int_trig_sample_count'] = 0 
        self.auger_fpga_hw.settings['trigger_mode'] = 'off' 
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()
    
    def setup_analyzer(self):
        self.analyzer_hw.settings['multiplier'] = True
        self.analyzer_hw.settings['CAE_mode'] = self.settings['CAE_mode']
        self.analyzer_hw.settings['KE'] = self.settings['ke_start']
        self.analyzer_hw.settings['pass_energy'] = self.settings['pass_energy']
        self.analyzer_hw.settings['crr_ratio'] = self.settings['crr_ratio']
        
    def setup_data(self):
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        CAE_mode = self.settings['CAE_mode']
        #extend energy range to get all channels for specified range
        ke_start = self.settings['ke_start']
        low_ke = min( self.analyzer_hw.analyzer.get_chan_ke(ke_start,CAE_mode))
        ke_end = self.settings['ke_end']
        high_ke = max( self.analyzer_hw.analyzer.get_chan_ke(ke_end,CAE_mode))
        ke_delta = self.settings['ke_delta']
        self.dwell_time = self.settings['dwell']

        self.sample_block = 21
        self.npoints = int((high_ke-low_ke)/ke_delta)+1
        self.index = 0
        self.chan_data = np.zeros( (NUM_CHANS, self.npoints), dtype=np.uint32 )
        self.chan_Hz = np.zeros( (NUM_CHANS, self.npoints) )
        self.ke = np.zeros((self.display_chans,self.npoints))
        self.ke[0,:] = np.linspace(low_ke,high_ke,num=self.npoints)
        if self.settings['No_dispersion']: #diagnostic, to check analyzer performance
            for i in range(1,self.display_chans):
                self.ke[i,:] = self.ke[0,:]
        else:            
            for i in range(self.npoints):
                ke = self.ke[0,i]
                self.ke[:,i] = self.analyzer_hw.analyzer.get_chan_ke(ke,CAE_mode)
        self.timeout = 2.0 * self.dwell_time
    
    def chan_sum(self):
        self.sum_Hz = np.copy(self.chan_Hz[0,:])
        x0 = self.ke[0,:]
        for i in range(1,self.display_chans):
            x = self.ke[i,:]
            y=self.chan_Hz[i,:]
            ff = interpolate.interp1d(x,y,bounds_error=False)
            self.sum_Hz += ff(x0)
            
    def run(self):
        print(self.name, 'run')
        
        ##### HDF5 Data file
        #if self.settings['save_h5']:
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_m = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5_file)
        
        self.reset_fpga()
        self.setup_analyzer()
        self.setup_data()
        self.auger_fpga_hw.settings['period'] = self.dwell_time/(self.sample_block - 1)
        self.auger_fpga_hw.settings['trigger_mode'] = 'int'
        
        time.sleep(3.0) #let electronics settle
        
        try:            
            while not self.interrupt_measurement_called and (self.index < self.npoints):    

                    #waits for data, source of timing
                    #FIX check for extra data in buffer due to delays...
                if self.index == 0:
                    self.auger_fpga_hw.flush_fifo()
                remaining, buf_reshaped = self.auger_fpga_hw.read_fifo(n_transfers = self.sample_block,timeout = self.timeout, return_remaining=True)                
                depth = buf_reshaped.shape[0]
                buf_reshaped = buf_reshaped[1:] #discard first sample, transient
                data = np.sum(buf_reshaped,axis=0) 
                #print(self.ke[0,self.index], data, remaining)                   
                self.chan_data[:, self.index] = data
                self.chan_Hz[:,self.index] = self.analyzer_hw.analyzer.dead_time_correct(data,self.dwell_time) / self.dwell_time
                self.index += 1
                if self.index < self.npoints:
                    self.analyzer_hw.settings['KE'] = self.ke[0,self.index]
                self.settings['progress'] = 100 * self.index / self.npoints
        finally:
            self.h5_m['chan_data'] = self.chan_data
            self.h5_m['ke'] = self.ke
            self.h5_file.close()
            self.auger_fpga_hw.settings['trigger_mode'] = 'off'
            self.analyzer_hw.settings['multiplier'] = False
            self.analyzer_hw.settings['KE'] = self.ke[0,0]         
            
            
    def update_display(self):    
        for i in range(self.display_chans):
            self.plot_lines[i].setData(self.ke[i,:],self.chan_Hz[i,:])
        if self.settings['Chan_sum']:
            self.chan_sum()
            self.plot_lines[self.display_chans].setData(self.ke[0,:],self.sum_Hz/5)
        #else:
        #    self.plot_lines[self.display_chans].setData(None)
            
            
            

'''
Created on Sep 8, 2014

@author: Edward Barnard and Benedikt Ursprung
'''

from ScopeFoundry  import Measurement, LQRange, h5_io
import time
import numpy as np
import pyqtgraph as pg

class PhotocurrentIVMeasurement(Measurement):
    
    name = "photocurrrent_iv"
    
    def setup(self):

        # logged quantities
        V_lqs_params = dict(unit='V', vmin=-5, vmax=5, spinbox_decimals = 3)
        self.source_voltage_min = self.settings.New("source_voltage_min", initial = -1, **V_lqs_params)
        self.source_voltage_max = self.settings.New("source_voltage_max", initial = +1, **V_lqs_params)
        self.source_voltage_delta = self.settings.New("source_voltage_delta", initial=0.1, **V_lqs_params)
        self.source_voltage_steps = self.settings.New("source_voltage_steps", int, initial = 10, vmin=1, vmax=1000,)
        self.acquisition_time = self.settings.New("acquisition_time", initial = 0.0, unit='sec')
        
        self.voltage_range = LQRange(self.source_voltage_min, self.source_voltage_max, self.source_voltage_delta, self.source_voltage_steps)

    def setup_figure(self):
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.plot = self.graph_layout.addPlot(title="Photocurrent IV")
        self.plot_line = self.plot.plot()
        self.plot.setLabel('left', 'current', 'A')
        self.plot.setLabel('bottom', 'voltage', 'V')
        

    def run(self):
        
        #Hardware
        self.keithley_hc = self.app.hardware['keithley_sourcemeter']
        self.keithley = self.keithley_hc.keithley
        
        self.keithley.resetA()
        self.keithley.setAutoranges_A()
        self.keithley.switchV_A_on()
        
        #measure IV
        self.Iarray,self.Varray = self.keithley.measureIV_A(self.source_voltage_steps.val, 
                             Vmin=self.source_voltage_min.val, 
                             Vmax = self.source_voltage_max.val, 
                             KeithleyADCIntTime=1, delay=self.settings['acquisition_time'])
        
        self.keithley.switchV_A_off()
        
        self.plot_line.setData(self.Varray,self.Iarray)
        
                
        # h5 data file setup
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_filename = self.h5_file.filename
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)      
        H['V'] = self.Varray
        H['I'] = self.Iarray
        self.h5_file.close()
        print('run done')
        
    def update_display(self):
        self.plot_line.setData(self.Varray,self.Iarray)


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
        self.source_voltage_min = self.add_logged_quantity("source_voltage_min", dtype=float, initial = -5, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage_max = self.add_logged_quantity("source_voltage_max", dtype=float, initial = +5, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage_delta = self.add_logged_quantity("source_voltage_delta", dtype=float, initial=0.1, unit='V', vmin=-5, vmax=5, ro=False)
        self.source_voltage_steps = self.add_logged_quantity("source_voltage_steps", dtype=int, initial = 10, vmin=1, vmax=1000, ro=False)
        
        self.voltage_range = LQRange(self.source_voltage_min, self.source_voltage_max, self.source_voltage_delta, self.source_voltage_steps)
        '''
        try:              
            self.source_voltage_min.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_vmin_doubleSpinBox)
            self.source_voltage_max.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_vmax_doubleSpinBox)
            self.source_voltage_steps.connect_bidir_to_widget(self.gui.ui.photocurrent_iv_steps_doubleSpinBox)
            #connect events
            self.gui.ui.photocurrent_iv_start_pushButton.clicked.connect(self.start)
        except Exception as err:
            print self.name, "could not connect to custom gui", err
        '''
    
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
                             KeithleyADCIntTime=1, delay=0)
        
        self.keithley.switchV_A_off()
        
        
        # h5 data file setup
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_filename = self.h5_file.filename
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)      
        h5_io.h5_save_measurement_settings(self, H)
        h5_io.h5_save_hardware_lq(self.gui, H)
        H['V'] = self.Varray
        H['I'] = self.Iarray
        self.h5_file.close()
        
        
    def update_display(self):
        self.plot_line.setData(self.Varray,self.Iarray)
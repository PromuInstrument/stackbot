'''
Created on Feb 27, 2019

@author: Benedikt Ursprung, Brian Shevitski
'''

from ScopeFoundry  import Measurement, h5_io
import time
import numpy as np
import pyqtgraph as pg

class IVBaseMeasurement(Measurement):
    '''
    Sources voltage and measures (after a delay time) the voltage and current of channel A 
    of a Keithley sourcemeter unit.
    Can be used as a stand alone iv measurement or as a Base class.
    If used as a base class override collect_Vs(self, i, Vs, I_measured, V_measured) and note 
        that run() closes the self.h5_file.
    '''
    
    name = "iv_base_measurement"
    
    def setup(self):
        kwargs = {'unit':'V', 'vmin':-5, 'vmax':5, 'spinbox_decimals':6}
        self.voltage_range = self.settings.New_Range('source_voltage',  initials = [-0.2, 0.8, 0.1], include_sweep_type = True, **kwargs)
    
    def setup_figure(self):
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.plot.showGrid(True,True)
        self.plot_line = self.plot.plot()
        self.plot.setLabel('left', 'current', 'A')
        self.plot.setLabel('bottom', 'voltage', 'V')

    def run(self):
        #Hardware
        self.keithley_hw = self.app.hardware['keithley_sourcemeter']
        KS = self.keithley_hw.settings
        
        self.keithley = self.keithley_hw.keithley
        
        KS['output_a_on'] = True
        
        time.sleep(0.5)

        #initialize h5_file
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        self.h5_filename = self.h5_file.filename
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
        #measure IV        
        self.V_sources = self.voltage_range.sweep_array        
        self.I_array = np.zeros_like(self.V_sources, float)
        self.V_array = np.zeros_like(self.V_sources, float)
        
        for i,Vs in enumerate(self.V_sources):
            KS['source_V_a'] = Vs
            time.sleep(KS['delay_time_a'])
            self.keithley_hw.settings.I_a.read_from_hardware()
            self.keithley_hw.settings.V_a.read_from_hardware()
            self.I_array[i] = KS["I_a"]
            self.V_array[i] = KS["V_a"]
            self.collect_Vs(i, Vs, KS["I_a"], KS["V_a"])
        
        H['V_sourced'] = self.V_sources  
        H['V'] = np.array(self.V_array)
        H['I'] = np.array(self.I_array)
        self.h5_file.close()
        
        KS['output_a_on'] = False
        
        
    def collect_Vs(self, i, Vs, I_measured, V_measured):
        '''
        override me!
        '''
        print('sourced Voltage', i, Vs, I_measured, V_measured)
        
    def update_display(self):
        self.plot_line.setData(self.V_array,self.I_array)
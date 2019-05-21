'''
Created on Oct 27, 2016

@author: Edward Barnard
'''
from __future__ import absolute_import, division, print_function
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
from ScopeFoundry import h5_io
from math import nan, isnan


class OOSpecOptimizerMeasure(Measurement):

    name = "oo_spec_optimizer"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "oo_spec_optimizer.ui")
        super(OOSpecOptimizerMeasure, self).__init__(app)    

    def setup(self):        
        self.display_update_period = 0.1 #seconds

        # logged quantities
        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')
        self.pow_reading = self.settings.New(name='power_reading', dtype=float, si=True, initial=0.0, unit='au')

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500

        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0

        # hardware
        self.oo_spec = self.app.measurements['oo_spec_live']

        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.reset_pushButton.clicked.connect(self.reset)

        self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)
        
        self.ui.power_readout_PGSpinBox = replace_widget_in_layout(self.ui.power_readout_doubleSpinBox,
                                                                       pg.widgets.SpinBox.SpinBox())
        
        self.pow_reading.connect_bidir_to_widget(self.ui.power_readout_PGSpinBox)
        
        self.pow_reading.connect_bidir_to_widget(self.ui.power_readout_label)
        
        #self.spec.settings.wavelength.connect_bidir_to_widget(self.ui.wavelength_doubleSpinBox)
        
        
    def setup_figure(self):
        self.optimize_ii = 0
        
        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        
        # graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # history plot
        self.plot = self.graph_layout.addPlot(title="Ocean Optics Spectrometer Optimizer")
        self.optimize_plot_line = self.plot.plot([0])        


    def run(self):
        self.display_update_period = 0.02 #seconds

        #self.apd_counter_hc = self.gui.apd_counter_hc
        #self.apd_count_rate = self.apd_counter_hc.apd_count_rate
        #self.pm_hc = self.gui.thorlabs_powermeter_hc
        #self.pm_analog_readout_hc = self.gui.thorlabs_powermeter_analog_readout_hc

        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            self.t0 = time.time()
        
        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
            self.oo_spec.interrupt_measurement_called = self.interrupt_measurement_called

            self.oo_spec.settings['continuous'] = False
            self.oo_spec.settings['save_h5'] = False
            
#             if ~self.oo_spec.activation.val:
#                 self.oo_spec.activation.update_value(True)
            #self.oo_spec.run()
            self.start_nested_measure_and_wait(self.oo_spec)
            spec = self.oo_spec.hw.spectrum.copy()
            
            if self.oo_spec.settings['baseline_subtract']:
                new_value = (spec-self.oo_spec.settings['baseline_val']).sum()
            else:
                new_value = self.pow_reading.update_value(spec.sum())
            
            if isnan(new_value):
                print('spec sum nan', self.optimize_ii)
                self.pow_reading.update_value(self.optimize_history[self.optimize_ii-1])
            else:
                print('spec sum', self.optimize_ii, new_value)
                self.pow_reading.update_value(new_value)
            self.optimize_history[self.optimize_ii] = self.pow_reading.val
            
            time.sleep(self.settings['update_period'])
            #time.sleep(0.02)
            
        if self.settings['save_data']:
            try:
                self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
                self.h5_file.attrs['time_id'] = self.t0
                H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            
                #create h5 data arrays
                H['power_optimze_history'] = self.full_optimize_history
                H['optimze_history_time'] = self.full_optimize_history_time
            finally:
                self.h5_file.close()
    
    def reset(self):
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0
    
    def update_display(self):        
        self.optimize_plot_line.setData(self.optimize_history)
        self.oo_spec.update_display()
        
    def interrupt(self):
        Measurement.interrupt(self)
        self.oo_spec.interrupt()

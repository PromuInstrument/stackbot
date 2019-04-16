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


class LakeshoreMeasure(Measurement):

    name = "lakeshore_measure"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "lakeshore_measure.ui")
        Measurement.__init__(self,app)   

    def setup(self):        
        self.display_update_period = 1 #seconds

        # logged quantities
        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 1800

        self.optimize_history_A = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)
        self.optimize_history_B = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)            
        self.optimize_ii = 0

        # hardware
        self.ctrl = self.app.hardware['lakeshore331']

        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.reset_pushButton.clicked.connect(self.reset)

        self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)
        
        self.ui.T_A_PGSpinBox = replace_widget_in_layout(self.ui.T_A_doubleSpinBox,
                                                                       pg.widgets.SpinBox.SpinBox())
        self.ui.T_B_PGSpinBox = replace_widget_in_layout(self.ui.T_B_doubleSpinBox,
                                                                       pg.widgets.SpinBox.SpinBox())
        
        self.ctrl.settings.T_A.connect_bidir_to_widget(self.ui.T_A_PGSpinBox)
        self.ctrl.settings.T_B.connect_bidir_to_widget(self.ui.T_B_PGSpinBox)
        
        
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
        self.plot = self.graph_layout.addPlot(title="Lakeshore 331 Readout")
        self.optimize_plot_line_A = self.plot.plot(np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float),name='T_A',pen={'color': "r", 'width': 2}) 
        self.optimize_plot_line_B = self.plot.plot(np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float),name='T_B',pen={'color': "b", 'width': 2})
        self.plot.setLabel('left', text='T', units='K')
        self.plot.setLabel('bottom', text='time elapsed', units='s')
        self.plot.addLegend()     


    def run(self):
        self.display_update_period = 1 #seconds

        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            self.t0 = time.time()
        
        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
            
            self.optimize_history_A[self.optimize_ii] = self.ctrl.settings['T_A']
            self.optimize_history_B[self.optimize_ii] = self.ctrl.settings['T_B']
            
            time.sleep(self.display_update_period)
            
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
        self.optimize_history_A = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)
        self.optimize_history_B = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)            
        self.optimize_ii = 0
    
    def update_display(self):        
        self.optimize_plot_line_A.setData(self.optimize_history_A)
        self.optimize_plot_line_B.setData(self.optimize_history_B)


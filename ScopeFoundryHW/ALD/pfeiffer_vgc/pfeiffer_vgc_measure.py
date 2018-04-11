'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundryHW.ALD.pfeiffer_vgc.vgc_sqlite_core import SQLite_Wrapper
from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
import time 


class Pfeiffer_VGC_Measure(Measurement):
    
    name = "pfeiffer_vgc_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):

        self.settings.New('history_length', dtype=int, initial=1000, vmin=1)

        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()   
            
        
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
    
    def ui_setup(self):
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setLayout(self.layout)
        self.ui.setWindowTitle('Pfeiffer Controller Pressure History')
        self.control_widget = QtWidgets.QGroupBox('Pfeiffer VGC Measure')
        self.layout.addWidget(self.control_widget, stretch=0)
        self.control_widget.setLayout(QtWidgets.QHBoxLayout())

        ui_list = ('history_length',)
        self.control_widget.layout().addWidget(self.settings.New_UI(include=ui_list))
        self.start_button = QtWidgets.QPushButton('Start')
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.control_widget.layout().addWidget(self.start_button)
        self.control_widget.layout().addWidget(self.stop_button)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot = self.plot_widget.addPlot(title='Chamber Pressures')
        self.plot.setLogMode(y=True)
        self.plot.setYRange(-8,2)
        self.plot.showGrid(y=True)
        self.plot.addLegend()
        self.layout.addWidget(self.plot_widget)
        self.setup_buffers_constants()
        self.plot_names =  ['TKP_1', 'TKP_2', 'PKR_3', 'MAN_4']
        self.plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.plot.plot([1], pen = pg.mkPen(color, width=2),
                name = self.plot_names[i])
            self.plot_lines.append(plot_line)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vLine)
        
        
    
    def db_connect(self):
        self.database = SQLite_Wrapper()
        self.server_connected = True
        self.database.setup_table()
        self.database.setup_index()
    
    def setup_buffers_constants(self):
        self.HIST_LEN = 1000
        self.NUM_CHANS = 4
        self.history_i = 0
        self.index = 0
        self.pressure_history = np.zeros((self.NUM_CHANS, 
                self.HIST_LEN))
        
    def read_pressures(self):
#         def direct_read(sensor):
#             measure = self.vgc.vgc.read_sensor(sensor)
#             return measure/(101325/76000)
        measurements = []
        for i in (1,2,3):
#             _measure = direct_read(i)
            _measure = self.vgc.settings['ch{}_pressure_scaled'.format(i)]
            measurements.append(_measure)
        return measurements
    
    def routine(self):
        readout = self.read_pressures()
        man_readout = self.app.hardware['mks_600_hw'].settings['pressure'] 
#         self.database.data_entry(*readout)
        if self.history_i < self.HIST_LEN:
            self.index = self.history_i % self.HIST_LEN
        else:
            self.index = self.HIST_LEN
            self.pressure_history = np.roll(self.pressure_history, -1, axis=1)
        self.pressure_history[:3, self.index-1] = readout
        self.pressure_history[3, self.index-1] = man_readout + 1e-5
        self.history_i += 1
     
    def update_display(self):
        self.vLine.setPos(self.index)
        
        for i in range(self.NUM_CHANS):
            self.plot_lines[i].setData(
                self.pressure_history[i,:self.index])
    
    def reconnect_server(self):
        self.database.connect()

    def disconnect_server(self):
        self.database.closeout()
    
    def run(self):
        dt=0.1
        self.HIST_LEN = self.settings['history_length']
        try:
#             self.db_connect()
            while not self.interrupt_measurement_called:
#                 if self.server_connected:
                if True:
                    self.vgc.settings.ch1_pressure.read_from_hardware()
                    self.vgc.settings.ch2_pressure.read_from_hardware()
                    self.vgc.settings.ch3_pressure.read_from_hardware()
                    self.routine()
                    time.sleep(dt)
                else:
#                     self.reconnect_server()
                    self.server_connected = True
                    self.routine()
                    time.sleep(dt)
        finally:
#             self.disconnect_server()
#             self.server_connected = False
            pass
                        
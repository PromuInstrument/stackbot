'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundryHW.ALD.pfeiffer_vgc.vgc_sqlite_core import SQLite_Wrapper
from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea
import numpy as np
import datetime
import time 
import os

class Pfeiffer_VGC_Measure(Measurement):
    
    name = "pfeiffer_vgc_measure"
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):

        self.settings.New('display_window', dtype=int, initial=1e4, vmin=200)
        self.settings.New('history_length', dtype=int, initial=1e6, vmin=1000)
        self.setup_buffers_constants()
        self.settings.New('save_path', dtype=str, initial=self.full_file_path, ro=False)


        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()   
            
        if hasattr(self.app.hardware, 'pfeiffer_vgc_hw'):
            self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        else:
            print("Connect Pfeiffer HW component first.")
    
    def ui_setup(self):
#         self.ui = QtWidgets.QWidget()

        self.ui = DockArea()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setLayout(self.layout)
        self.ui.setWindowTitle('Pfeiffer Controller Pressure History')
        self.widget_setup()
        self.dockArea_setup()
    
    def dockArea_setup(self):
        self.ui.addDock(name='Pressure History', position='top', widget=self.group_widget)
        self.ui.addDock(name='NumPy Export', position='bottom', widget=self.export_widget)
        
    def widget_setup(self):
        self.setup_plot_group_widget()
        self.setup_export_widget()
        
        
    def setup_export_widget(self):
        self.export_widget = QtWidgets.QGroupBox('Pressure Export')
        self.export_widget.setLayout(QtWidgets.QHBoxLayout())
        self.export_widget.setMaximumHeight(100)
        self.export_button = QtWidgets.QPushButton('Export Pressure Data')
        self.save_field = QtWidgets.QLineEdit('Directory')
        self.export_widget.layout().addWidget(self.export_button)
        self.export_widget.layout().addWidget(self.save_field)
        self.export_button.clicked.connect(self.export_to_disk)
        self.settings.save_path.connect_to_widget(self.save_field)

        
        
    def setup_plot_group_widget(self):
        self.group_widget = QtWidgets.QGroupBox('Pfeiffer VGC Measure')
        self.group_widget.setLayout(QtWidgets.QVBoxLayout())
        
        self.control_widget = QtWidgets.QWidget()
        self.control_widget.setLayout(QtWidgets.QHBoxLayout())
        
        self.group_widget.layout().addWidget(self.control_widget, stretch=0)
        

        
        self.display_label = QtWidgets.QLabel('Display Window')
        self.history_label = QtWidgets.QLabel('History Length')
        self.display_field = QtWidgets.QLineEdit()
        self.history_field = QtWidgets.QLineEdit()
        
        self.control_widget.layout().addWidget(self.display_label)
        self.control_widget.layout().addWidget(self.display_field)
        self.control_widget.layout().addWidget(self.history_label)
        self.control_widget.layout().addWidget(self.history_field)
        
        self.settings.display_window.connect_to_widget(self.display_field)
        self.settings.history_length.connect_to_widget(self.history_field)
        
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
        self.plot_names =  ['TKP_1', 'TKP_2', 'PKR_3', 'MAN_4']
        self.plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.plot.plot([1], pen = pg.mkPen(color, width=2),
                name = self.plot_names[i])
            self.plot_lines.append(plot_line)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vLine)
        
        self.group_widget.layout().addWidget(self.plot_widget)

    
    def db_connect(self):
        self.database = SQLite_Wrapper()
        self.server_connected = True
        self.database.setup_table()
        self.database.setup_index()
    
    def setup_buffers_constants(self):
        home = os.path.expanduser("~")
        self.path = home+'\\Desktop\\'
        self.full_file_path = self.path+'np'
        self.HIST_LEN = self.settings.history_length.val
        self.WINDOW = self.settings.display_window.val
        self.NUM_CHANS = 4
        self.history_i = 0
        self.index = 0
        self.pressure_history = np.zeros((self.NUM_CHANS, 
                self.HIST_LEN))
        self.time_history = np.zeros((1, self.HIST_LEN), dtype='datetime64[s]')
        self.debug_mode = False
        
    def read_pressures(self):
        measurements = []
        for i in (1,2,3):
            _measure = self.vgc.settings['ch{}_pressure_scaled'.format(i)]
            measurements.append(_measure)
        return np.array(measurements)
    
    def routine(self):
        if self.debug_mode:
            readout = np.random.rand(3,)
            man_readout = np.random.rand(1,)
        else:
            readout = self.read_pressures()
            man_readout = np.array(self.app.hardware['mks_600_hw'].settings['pressure'])
        
        time_entry = datetime.datetime.now()
        if self.history_i < self.HIST_LEN-1:
            self.index = self.history_i % self.HIST_LEN
        else:
            self.index = self.HIST_LEN-1
            self.pressure_history = np.roll(self.pressure_history, -1, axis=1)
            self.time_history = np.roll(self.time_history, -1, axis=1)
        self.pressure_history[:3, self.index] = readout
        self.pressure_history[3, self.index] = man_readout + 1e-5
        self.history_i += 1
    
    def export_to_disk(self):
        path = self.settings['save_path']
        np.save(path+'_pressures.npy', self.pressure_history)
        np.save(path+'_times.npy', self.time_history)
    
    def update_display(self):
        self.WINDOW = self.settings.display_window.val
        self.vLine.setPos(self.WINDOW)
        
        lower = self.index-self.WINDOW

        for i in range(self.NUM_CHANS):
            if self.index >= self.WINDOW:
                self.plot_lines[i].setData(
                    self.pressure_history[i,lower:self.index+1])
            else:
                self.plot_lines[i].setData(
                    self.pressure_history[i,:self.index+1])
                self.vLine.setPos(self.index)
    
    def reconnect_server(self):
        self.database.connect()

    def disconnect_server(self):
        self.database.closeout()
    
    def run(self):
        dt=0.2
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
                        
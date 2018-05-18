'''
Created on Apr 11, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
from ScopeFoundry.ndarray_interactive import ArrayLQ_QTableModel
from PyQt5 import QtWidgets, QtGui, QtCore
from . import resources
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea
import numpy as np
import time
from PyQt5.Qt import QVBoxLayout

class ALD_params(Measurement):
    
    name = 'ALD_params'
    
    def __init__(self, app):
        Measurement.__init__(self, app)

        
        
    def setup(self):
        self.cb_stylesheet = '''
        QCheckBox::indicator {
            width: 100px;
            height: 100px;
        }
        QCheckBox::indicator:checked {
            image: url(://icons//green-led-on.png);
        }
        QCheckBox::indicator:unchecked {
            image: url(://icons//led-red-on.png);
        }
        '''

        self.settings.New('RF_pulse_duration', dtype=int, initial=1)
        self.settings.New('history_length', dtype=int, initial=10000, vmin=1)
        self.settings.New('shutter_open', dtype=bool, initial=False, ro=True)
        
        self.settings.New('time', dtype=float, array=True, initial=[[0.1,0.05,0.2,0.3,0.3]], fmt='%1.3f', ro=False)
        
        self.setup_buffers_constants()
        
        if hasattr(self.app.hardware, 'seren_hw'):
            self.seren = self.app.hardware.seren_hw
        else:
            print('Connect Seren HW component first.')

        if hasattr(self.app.hardware, 'ald_shutter'):
            self.shutter = self.app.hardware.ald_shutter
        else:
            print('Connect ALD shutter HW component first.')
        
        if hasattr(self.app.hardware, 'lovebox'):
            self.lovebox = self.app.hardware.lovebox
        
        if hasattr(self.app.hardware, 'mks_146_hw'):
            self.mks146 = self.app.hardware.mks_146_hw
        
        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()
        


    def ui_setup(self):
        
        self.ui = DockArea()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setWindowTitle('ALD Control Panel')
        self.ui.setLayout(self.layout)
        self.widget_setup()
        self.dockArea_setup()

    def dockArea_setup(self):
        self.ui.addDock(name="Shutter Controls", position='right', widget=self.shutter_control_widget)
        self.ui.addDock(name="Thermal History", position='top', widget=self.thermal_widget)
        self.ui.addDock(name="RF Settings", position='top', widget=self.rf_widget)
        self.ui.addDock(name="Recipe Controls", position='bottom', widget=self.recipe_control_widget)
    
    def load_ui_defaults(self):
        
        pass
    
    def save_ui_defaults(self):
        
        pass
    
    def widget_setup(self):
        self.setup_shutter_control_widget()
        self.setup_thermal_control_widget()
        self.setup_rf_flow_widget()
        self.setup_recipe_control_widget()

    def setup_thermal_control_widget(self):
        self.thermal_widget = QtWidgets.QGroupBox('Thermal Controller Overview')
        self.layout.addWidget(self.thermal_widget)
        self.thermal_widget.setLayout(QtWidgets.QVBoxLayout())
        self.thermal_channels = 1
        
        plot_ui_list = ('history_length',)
        self.thermal_widget.layout().addWidget(self.settings.New_UI(include=plot_ui_list))
        self.thermal_plot_widget = pg.GraphicsLayoutWidget()
        self.thermal_plot = self.thermal_plot_widget.addPlot(title='Temperature History')
        self.thermal_plot.showGrid(y=True)
        self.thermal_plot.addLegend()
        self.thermal_widget.layout().addWidget(self.thermal_plot_widget)
        self.thermal_plot_names = ['Heater Temperature']
        self.thermal_plot_lines = []
        for i in range(self.thermal_channels):
            color = pg.intColor(i)
            plot_line = self.thermal_plot.plot([1], pen=pg.mkPen(color, width=2),
                                                    name = self.thermal_plot_names[i])
            self.thermal_plot_lines.append(plot_line)
        self.vLine1 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine1 = pg.InfiniteLine(angle=0, movable=False)
        self.thermal_plot.addItem(self.vLine1)
        self.thermal_plot.addItem(self.hLine1)
    
    def setup_rf_flow_widget(self):
        self.rf_widget = QtWidgets.QGroupBox('RF Settings')
        self.layout.addWidget(self.rf_widget)
        self.rf_widget.setLayout(QtWidgets.QVBoxLayout())
        
        plot_ui_list = ('history_length',)
        self.rf_widget.layout().addWidget(self.settings.New_UI(include=plot_ui_list))
        
        self.rf_plot_widget = pg.GraphicsLayoutWidget()
        self.rf_plot = self.rf_plot_widget.addPlot(title='RF power and scaled MFC flow')
        self.rf_plot.showGrid(y=True)
        self.rf_plot.addLegend()
        self.rf_widget.layout().addWidget(self.rf_plot_widget)
        self.rf_plot_names = ['Forward', 'Reflected', 'MFC flow (scaled)']
        self.rf_plot_lines = []
        for i in range(self.RF_CHANS):
            color = pg.intColor(i)
            plot_line = self.rf_plot.plot([1], pen=pg.mkPen(color, width=2),
                                          name = self.rf_plot_names[i])
            self.rf_plot_lines.append(plot_line)
        self.vLine2 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine2 = pg.InfiniteLine(angle=0, movable=False)
        self.rf_plot.addItem(self.vLine2)
        self.rf_plot.addItem(self.hLine2)
        
        
    def setup_shutter_control_widget(self):
        self.shutter_control_widget = QtWidgets.QGroupBox('Shutter Controls')
        self.shutter_control_widget.setLayout(QtWidgets.QGridLayout())
        self.shutter_control_widget.setStyleSheet(self.cb_stylesheet)

        self.layout.addWidget(self.shutter_control_widget)        
        
        self.shutter_status = QtWidgets.QCheckBox(self.shutter_control_widget)
        self.shutter_control_widget.layout().addWidget(self.shutter_status, 0, 0)
        self.shutter.settings.shutter_open.connect_to_widget(self.shutter_status)

        self.shaul_shutter_toggle = QtWidgets.QPushButton('Shaul\'s Huge Shutter Button')
        self.shaul_shutter_toggle.setMinimumHeight(200)
        font = self.shaul_shutter_toggle.font()
        font.setPointSize(24)
        self.shaul_shutter_toggle.setFont(font)
        self.shutter_control_widget.layout().addWidget(self.shaul_shutter_toggle, 0, 1)
        if hasattr(self, 'shutter'):
            self.shaul_shutter_toggle.clicked.connect(self.shutter.shutter_toggle)

    def setup_recipe_control_widget(self):
        self.recipe_control_widget = QtWidgets.QGroupBox('Recipe Controls')
        self.layout.addWidget(self.recipe_control_widget)
        self.recipe_control_widget.setLayout(QtWidgets.QGridLayout())

        self.recipe_start_button = QtWidgets.QPushButton('Start Recipe')
        self.recipe_stop_button = QtWidgets.QPushButton('Stop Recipe')

        
        self.recipe_control_widget.layout().addWidget(self.recipe_start_button, 0, 0)
        self.recipe_control_widget.layout().addWidget(self.recipe_stop_button, 0, 1)
        self.recipe_start_button.clicked.connect(self.app.measurements['ALD_routine'].start)
        self.recipe_stop_button.clicked.connect(self.app.measurements['ALD_routine'].interrupt)
    
        self.pulse_label = QtWidgets.QLabel('RF Durations [s]')
        self.recipe_control_widget.layout().addWidget(self.pulse_label, 1, 0)
    
        self.pulse_table = QtWidgets.QTableView()
        self.pulse_table.setMaximumHeight(65)
        names = ['t1', 't2 (TiCl4 PV)', 't3', 't4 (Shutter)', 't5', 'sum']
        self.tableModel = ArrayLQ_QTableModel(self.settings.time, col_names=names)
        self.pulse_table.setModel(self.tableModel)
        self.recipe_control_widget.layout().addWidget(self.pulse_table, 1, 1)
#         self.settings.time.connect_bidir_to_widget(self.pulse_field)
    
        
    
    
    def setup_buffers_constants(self):
        self.HIST_LEN = self.settings.history_length.val
        self.RF_CHANS = 3
        self.T_CHANS = 1
        self.history_i = 0
        self.index = 0
        self.rf_history = np.zeros((self.RF_CHANS, self.HIST_LEN))
        self.thermal_history = np.zeros((self.T_CHANS, self.HIST_LEN))

    def plot_routine(self):
        rf_entry = np.array([self.seren.settings['forward_power_readout'], \
                         self.seren.settings['reflected_power'], \
                         self.mks146.settings['MFC0_flow']])
        t_entry = np.array([self.lovebox.settings['pv_temp']])
        
        if self.history_i < self.HIST_LEN:
            self.index = self.history_i % self.HIST_LEN
        else:
            self.index = self.HIST_LEN
            self.rf_history = np.roll(self.rf_history, -1, axis=1)
            self.thermal_history = np.roll(self.thermal_history, -1, axis=1)
        self.rf_history[:, self.index-1] = rf_entry
        self.thermal_history[:, self.index-1] = t_entry
        
        
        self.history_i += 1
        
        
    
    def update_display(self):
        lovebox_level = self.lovebox.settings['sv_setpoint']
        self.hLine1.setPos(lovebox_level)
        self.vLine1.setPos(self.index)
        
        flow_level = self.mks146.settings['MFC0_SP']
        self.hLine2.setPos(flow_level)
        self.vLine2.setPos(self.index)
        
        for i in range(self.RF_CHANS):
            self.rf_plot_lines[i].setData(
                self.rf_history[i, :self.index])

        for i in range(self.T_CHANS):
            self.thermal_plot_lines[i].setData(
                self.thermal_history[i, :self.index])
    
    
    def run(self):
        dt = 0.2
        self.HIST_LEN = self.settings['history_length']
        while not self.interrupt_measurement_called:
            self.seren.settings.forward_power_readout.read_from_hardware()
            self.seren.settings.reflected_power.read_from_hardware()
            self.lovebox.settings.pv_temp.read_from_hardware()
            self.lovebox.settings.sv_setpoint.read_from_hardware()
            self.mks146.settings.MFC0_flow.read_from_hardware()
            self.mks146.settings.MFC0_SP.read_from_hardware()
            self.plot_routine()
            time.sleep(dt)
            
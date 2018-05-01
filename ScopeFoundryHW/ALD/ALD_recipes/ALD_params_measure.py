'''
Created on Apr 11, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets, QtGui, QtCore
from . import resources
import pyqtgraph as pg
import numpy as np
import time
from PyQt5.Qt import QVBoxLayout

class ALD_params(Measurement):
    
    name = 'ALD_params'
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        self.settings.New('RF_pulse_duration', dtype=int, initial=1)
        self.settings.New('history_length', dtype=int, initial=1000, vmin=1)
        
        self.setup_buffers_constants()
        
        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()
        
        if hasattr(self.app.hardware, 'seren_hw'):
            self.seren = self.app.hardware.seren_hw
        else:
            print('Connect Seren HW component first.')

        

    def ui_setup(self):
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setWindowTitle('ALD Control Panel')
        self.ui.setLayout(self.layout)
        
        self.GREEN = '://icons//green-led-on.png'
        self.RED = "://icons//led-red-on.png"

        
        self.rf_widget = QtWidgets.QGroupBox('RF Settings')
        self.layout.addWidget(self.rf_widget)
        self.rf_widget.setLayout(QtWidgets.QVBoxLayout())
        
        plot_ui_list = ('history_length',)
        self.rf_widget.layout().addWidget(self.settings.New_UI(include=plot_ui_list))
        
        self.rf_plot_widget = pg.GraphicsLayoutWidget()
        self.rf_plot = self.rf_plot_widget.addPlot(title='RF Power')
        self.rf_plot.showGrid(y=True)
        self.rf_plot.addLegend()
        self.rf_widget.layout().addWidget(self.rf_plot_widget)
        self.rf_plot_names = ['Forward', 'Reflected']
        self.rf_plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.rf_plot.plot([1], pen=pg.mkPen(color, width=2),
                                          name = self.rf_plot_names[i])
            self.rf_plot_lines.append(plot_line)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.rf_plot.addItem(self.vLine)
        
        self.shutter_control_widget = QtWidgets.QGroupBox('Shutter Controls')
        self.shutter_status = QtWidgets.QLabel(self.shutter_control_widget)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.shutter_status.setFont(font)
        self.shutter_status.setText("")
        self.shutter_status.setPixmap(QtGui.QPixmap(self.GREEN))
        self.shutter_status.setScaledContents(True)
        self.shutter_status.setObjectName('shutter_status_label')
        self.shutter_status.setGeometry(QtCore.QRect(10,20,20,20))
        
        self.layout.addWidget(self.shutter_control_widget)
        self.shutter_control_widget.setLayout(QtWidgets.QGridLayout())
        
        self.shutter_control_widget.layout().addWidget(self.shutter_status, 0, 0)
        
        self.shaul_shutter_toggle = QtWidgets.QPushButton('Shaul\'s Huge Shutter Button')
        self.shaul_shutter_toggle.setMinimumHeight(200)
        font = self.shaul_shutter_toggle.font()
        font.setPointSize(24)
        self.shaul_shutter_toggle.setFont(font)
        self.shutter_control_widget.layout().addWidget(self.shaul_shutter_toggle, 0, 1)
        

        
        
        self.recipe_control_widget = QtWidgets.QGroupBox('Recipe Controls')
        self.layout.addWidget(self.recipe_control_widget)
        self.recipe_control_widget.setLayout(QtWidgets.QGridLayout())

        self.recipe_start_button = QtWidgets.QPushButton('Start Recipe')
        self.recipe_stop_button = QtWidgets.QPushButton('Stop Recipe')

        
        self.recipe_control_widget.layout().addWidget(self.recipe_start_button, 0, 0)
        self.recipe_control_widget.layout().addWidget(self.recipe_stop_button, 0, 1)
        self.recipe_start_button.clicked.connect(self.app.measurements['ALD_routine'].start)
        self.recipe_stop_button.clicked.connect(self.app.measurements['ALD_routine'].interrupt)
    
        self.rf_pulse_label = QtWidgets.QLabel('RF Pulse Duration [s]')
        self.recipe_control_widget.layout().addWidget(self.rf_pulse_label, 1, 0)
    
        self.rf_pulse_field = QtWidgets.QDoubleSpinBox()
        self.recipe_control_widget.layout().addWidget(self.rf_pulse_field, 1, 1)
        self.settings.RF_pulse_duration.connect_bidir_to_widget(self.rf_pulse_field)
    
        
    
    
    def setup_buffers_constants(self):
        self.HIST_LEN = 500
        self.NUM_CHANS = 2
        self.history_i = 0
        self.index = 0
        self.rf_history = np.zeros((self.NUM_CHANS, self.HIST_LEN))

    def routine(self):
        entry = np.array(self.seren.settings['forward_power'], \
                         self.seren.settings['reflected_power'])
        if self.history_i < self.HIST_LEN:
            self.index = self.history_i % self.HIST_LEN
        else:
            self.index = self.HIST_LEN
            self.pressure_history = np.roll(self.rf_history, -1, axis=1)
        self.pressure_history[:, self.index-1] = entry
        self.history_i += 1
    
    def update_display(self):
        self.vLine.setPos(self.index)
        for i in range(self.NUM_CHANS):
            self.plot_lines[i].setData(
                self.rf_history[i, :self.index])
    
    
    def run(self):
        dt = 0.2
        self.HIST_LEN = self.settings['history_length']
        while not self.interrupt_measurement_called:
            self.seren.settings.forward_power.read_from_hardware()
            self.seren.settings.reflected_power.read_from_hardware()
            self.routine()
            time.sleep(dt)
            
'''
@author: Alan Buckley
'''
from __future__ import absolute_import, print_function, division
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundryHW.ADS.sqlite_wrapper import SQLite_Wrapper
from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
import time

class ADS_Optimizer(Measurement):
	
	name = "ads_optimizer"
	
	def __init__(self, app):
		Measurement.__init__(self, app)

	def setup(self):
		self.settings.New('history_length', dtype=int, initial=1000, vmin=1)
		self.ads_hw = self.app.hardware['ads_hw']
		self.setup_ui()
		self.ui_created = False

	def setup_ui(self):		
		self.ui = QtWidgets.QWidget()
		self.layout = QtWidgets.QVBoxLayout()
		self.ui.setLayout(self.layout)
		self.ui.setWindowTitle("Auger Pressure History")
		self.control_widget = QtWidgets.QGroupBox(self.name)
		self.layout.addWidget(self.control_widget, stretch=0)
		self.control_widget.setLayout(QtWidgets.QHBoxLayout())

		ui_list=('history_length',)
		self.control_widget.layout().addWidget(self.settings.New_UI(include=ui_list))

		self.start_button = QtWidgets.QPushButton("Start")
		self.control_widget.layout().addWidget(self.start_button)
		self.stop_button = QtWidgets.QPushButton("Stop")
		self.control_widget.layout().addWidget(self.stop_button)

		self.start_button.clicked.connect(self.start)
		self.stop_button.clicked.connect(self.interrupt)
		

		self.plot_widget = pg.GraphicsLayoutWidget()
		self.plot = self.plot_widget.addPlot(title="Chamber Pressures")
		self.plot.setLogMode(y=True)
		self.plot.setYRange(-12,-6)
		self.plot.showGrid(y=True)
		self.plot.addLegend()
		self.layout.addWidget(self.plot_widget)
		self.setup_buffers_constants()
		self.plot_names = ('Prep', 'Nano')
		self.plot_lines = []
		for i in range(self.NUM_CHANS):
			color = pg.intColor(i)
			plot_line = self.plot.plot([1], pen=pg.mkPen(color, width=2), 
				name=self.plot_names[i])
			self.plot_lines.append(plot_line)
		self.vLine = pg.InfiniteLine(angle=90, movable=False)
		self.plot.addItem(self.vLine)
		
	def setup_buffers_constants(self):
		self.HIST_LEN= 1000
		self.NUM_CHANS = 2
		self.history_i = 0
		self.index = 0
		self.voltage_chan_history = np.zeros((self.NUM_CHANS, 
				self.HIST_LEN), dtype=float)
		self.pressure_chan_history = np.zeros((self.NUM_CHANS, 
				self.HIST_LEN))
			
		
	def db_connect(self):	
		self.database = SQLite_Wrapper()
		self.server_connected = True
		self.database.setup_table()
		self.database.setup_index()

	def log_voltage(self):
		readout = self.ads_hw.read_voltages()
		nano_v = readout[0]
		prep_v = readout[1]
		# self.database.data_entry(nano_v, prep_v)
		return readout

	def log_pressure(self):
		readout = self.ads_hw.read_pressure()
		nano_p = readout[0]
		prep_p = readout[1]
		# self.database.data_entry(nano_p, prep_p)
		return readout

	def reconnect_server(self):
		self.database.connect()

	def disconnect_server(self):
		self.database.closeout()

	def routine(self):
		nano_v, prep_v = self.log_voltage()
		nano_p, prep_p = self.log_pressure()
		self.database.data_entry(prep_v, nano_v, prep_p, nano_p)
		self.index = self.history_i % self.HIST_LEN
		volts = self.ads_hw.settings['voltages']
		pressure = self.ads_hw.settings['pressure']
		self.voltage_chan_history[:, self.index] = (volts[0],volts[1])
		self.pressure_chan_history[:, self.index] = (pressure[0], 
			pressure[1])
		self.history_i += 1

	def run(self):
		self.HIST_LEN = self.settings['history_length']

		try:
			self.db_connect()
			while not self.interrupt_measurement_called:
				if self.server_connected:
					self.update_display()
					self.routine()
					time.sleep(0.5)
				else:
					self.reconnect_server()
					self.server_connected = True
					self.routine()
					time.sleep(0.5)
		
		finally:
			self.disconnect_server()
			self.server_connected = False

	def update_display(self):
		self.vLine.setPos(self.index)
		for i in range(self.NUM_CHANS):
			self.plot_lines[i].setData(
				self.pressure_chan_history[i,:])

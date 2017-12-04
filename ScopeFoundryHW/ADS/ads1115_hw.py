'''
@author: Alan Buckley
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ADS.ads1115_interface import ADS_Interface

class ADS_HW(HardwareComponent):

	name = 'ads_hw'
	
	def setup(self):
		self.settings.New(name='adc', dtype=int, array=True, ro=True, initial=[0,0,0,0])
		self.settings.New(name='voltages', dtype=float, array=True, ro=True, initial=[0,0])
		self.settings.New(name='pressure', dtype=float, array=True, ro=True, initial=[0,0])

	def connect(self):
		# self.adc = Adafruit_ADS1x15.ADS1115()
		self.adc = ADS_Interface()
		# if self.adc:
		# 	self.server_connected = True
		# if self.server_connected == False and self.adc:
		# 	self.reconnect_to_server()
		self.GAIN = 1
		self.settings.adc.connect_to_hardware(
			read_func=self.adc.adc_readout)
		self.settings.voltages.connect_to_hardware(
			read_func=self.adc.adc_volts)
		self.settings.pressure.connect_to_hardware(
			read_func=self.adc.adc_pressure)
		print("connected")
		
	def read_adc(self):
		value = self.adc.adc_readout()
		self.settings.adc.update_value(value)
		return self.settings['adc']

	def read_voltages(self):
		readout = self.adc.adc_volts()
		self.settings.voltages.update_value(readout)
		return self.settings['voltages']

	def read_pressure(self):
		pressure = self.adc.adc_pressure()
		self.settings.pressure.update_value(pressure)
		return self.settings['pressure']

	# def reconnect_to_server(self):
	# 	self.adc.reconnect_server()
	# 	self.server_connected = True

	# def disconnect_server(self):
	# 	self.adc.disconnect_server()
	# 	self.server_connected = False

	def disconnect(self):
		self.settings.disconnect_all_from_hardware()
		# if self.server_connected:
		# 	self.adc.disconnect_server()
		# 	self.server_connected = False
		if hasattr(self, 'ads_interface'):
			del self.adc


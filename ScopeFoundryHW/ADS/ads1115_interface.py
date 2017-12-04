'''@author: Alan Buckley
Voltage to pressure conversion by Frank Ogletree'''

import time
from ScopeFoundryHW.ADS.Adafruit_ADS1x15 import ADS1115
import numpy as np
#from ScopeFoundryHW.ADS.sqlite_wrapper import SQLite_Wrapper

class ADS_Interface(object):

	name = 'ads_interface'

	def __init__(self):

		self.adc = ADS1115()
		# self.database = SQLite_Wrapper()
		# self.database.setup_table()
		# self.database.setup_index()
		self.GAIN = 1

	def volts_to_pressure(self, volts):
		'''convert log output of ion gauge into mBarr)
		'''
		vmin=np.array([0.0,0.078])
		vmax=np.array([10.0,2.89])
		vhi=np.array([1.0,1.0])
		vlo=np.array([0.0,0.0])
		pmin=np.array([1e-11,1e-12])
		pmax=np.array([1e-2,0.2])
		vr = (volts-vmin)/(vmax-vmin)
		vr = np.minimum(1.0,np.maximum(vr,0.0))
		pr=np.log(pmax/pmin)
		return pmin*np.exp(vr*pr)  

	def adc_readout(self):
		values = [0,0,0,0]
		for i in range(4):
			values[i] = self.adc.read_adc(i, gain=self.GAIN)
		return values

	def adc_volts(self):
		voltage = [0,0,0,0]
		v_c = (4.096/32768.0)
		for i in range(4):
			voltage[i] = v_c*self.adc.read_adc(i, gain=self.GAIN)
		return voltage[0:-2]

	def adc_pressure(self):
		readout = self.adc_volts()
		pressure = self.volts_to_pressure(readout)
		return pressure




	# def log_voltage(self):
	# 	readout = self.adc_volts()[0:-2]
	# 	nano_v = readout[0]
	# 	prep_v = readout[1]
	# 	self.database.data_entry(nano_v, prep_v)
	# 	return readout

	# def log_pressure(self):
	# 	readout = self.adc_volts()[0:-2]
	# 	pressure = self.volts_to_pressure()
	# 	nano_p = pressure[0]
	# 	prep_p = pressure[1]
	# 	self.database.data_entry(nano_p, prep_p)
	# 	return pressure

	# def reconnect_server(self):
	# 	self.database.connect()

	# def disconnect_server(self):
	# 	self.database.closeout()

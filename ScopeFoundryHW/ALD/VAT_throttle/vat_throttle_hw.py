'''
Created on Dec 19, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_interface import VAT_Throttle_Interface
import time

class VAT_Throttle_HW(HardwareComponent):

	name = 'vat_throttle_hw'

	def setup(self):
		self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
		self.settings.New(name='read_position', initial=1000, dtype=float, ro=True, vmin=0, vmax=1000)
		self.settings.New(name='write_position', initial=1000, dtype=float, ro=False, vmin=0, vmax=1000)
		self.settings.New(name='status', initial='', dtype=str, ro=True)
		self.settings.New(name='open_valve', initial=False, dtype=bool, ro=False)
	def connect(self):
		self.vat_throttle = VAT_Throttle_Interface(port=self.settings['port'], debug=self.settings['debug_mode'])
		self.settings.get_lq('status').connect_to_hardware(read_func=self.vat_throttle.read_status)
		self.settings.get_lq('open_valve').connect_to_hardware(write_func=lambda x: self.vat_throttle.valve_open(x))
		self.settings.get_lq('read_position').connect_to_hardware(read_func=self.vat_throttle.read_position)
		self.settings.get_lq('write_position').connect_to_hardware(write_func=self.vat_throttle.write_position)
		
		
		self.vat_throttle.set_local()



	def disconnect(self):
		self.settings.disconnect_all_from_hardware()
		self.vat_throttle.close()
		del self.vat_throttle
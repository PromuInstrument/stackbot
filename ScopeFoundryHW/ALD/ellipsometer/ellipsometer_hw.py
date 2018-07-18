from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ALD.ellipsometer.ellipsometer_interface import Ellipsometer_Interface
import time

class EllipsometerHW(HardwareComponent):

	name = 'ellipsometer_hw'

	def setup(self):
		self.choices = ('Thick Oxide, Fast Acq','Thin Oxide, Fast Acq','Polymer Layer, Slow Acq')
		self.settings.New(name='host', initial='192.168.0.1', dtype=str, ro=False)
		self.settings.New(name='port', initial=4444, dtype=int, ro=False)
		self.add_operation(name='trigger', op_func=self.trigger)		
		self.settings.New(name='acquiring', initial=False, dtype=bool, ro=True)
		self.settings.New(name='measuring', initial=False, dtype=bool, ro=True)

	def connect(self):
		self.ellipsometer = Ellipsometer_Interface(host=self.settings['host'], port=self.settings['port'], debug=self.settings['debug_mode'])
		try:
			self.ellipsometer.sock.connect((self.settings['host'], self.settings['port']))
		except (self.ellipsometer.socket.error, self.ellipsometer.socket.timeout):
			self.ellipsometer.sock.close()
			self.ellipsometer.sock = None
			print('Could not connect to host: ', self.settings['host'])
		
		
			

	def poll(self):
		resp = self.ellipsometer.write_cmd('Status()')
		if resp == (b'Acquiring Data\r\n'):
			self.settings['measuring'] = True
		else:
			self.settings['measuring'] = False
		return resp
	
	def start_acq(self):
		cmd = "StartAcq()"
		self.ellipsometer.write_cmd(cmd)
	
	def stop_acq(self):
		cmd = "StopAcq()"
		self.ellipsometer.write_cmd(cmd)
	
	def trigger(self):
		cmd = "Trigger()"
		self.ellipsometer.write_cmd(cmd)
	
	

	def disconnect(self):
		self.settings.disconnect_all_from_hardware()
		self.ellipsometer.close()
		del self.ellipsometer
from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ALD.ellipsometer.ellipsometer_interface import Ellipsometer
import time

class Ellipsometer(HardwareComponent):

	name = 'ellipsometer'

	def setup(self):
		self.choices = ('Thick Oxide, Fast Acq','Thin Oxide, Fast Acq','Polymer Layer, Slow Acq')
		self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
		self.settings.New(name='recipe', initial=self.choices[0], dtype=str, choices=self.choices, ro=False)
		self.add_operation(name='start_recipe', op_func=self.run_recipe)
		self.settings.New(name='ready', initial=False, dtype=bool, ro=True)
		self.settings.New(name='filename', initial='', dtype=str, ro=False)

	def connect(self):
		self.ellipsometer = Ellipsometer(port=self.settings['port'], debug=self.settings['debug_mode'])
		self.ready_check()

	def ready_check(self):
		while not self.settings['ready']:
			resp = self.ellipsometer.write_cmd('status()')
			time.sleep(0.5)
			if resp == 'Waiting to Acquire Data':
				self.settings['ready'] = True
				return
			elif resp == 'Initializing ...':
				pass
			else:
				print(resp)

	def run_recipe(self):
		recipe = self.settings['recipe']
		if self.settings['filename'] != '':
			ext = '/{}'.format(self.settings['filename'])
			arg = recipe+ext
		else:
			arg = recipe
		cmd = 'RunRecipe({})'.format(arg)
		resp = self.ellipsometer.write_cmd(cmd)
		return resp

	def disconnect(self):
		self.settings.disconnect_all_from_hardware()
		self.ellipsometer.close()
		del self.ellipsometer
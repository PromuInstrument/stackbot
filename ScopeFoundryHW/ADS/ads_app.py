'''
@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path
from PyQt5.QtWidgets import QApplication
import logging

class ADS_App(BaseMicroscopeApp):

	name = "ads_app"

	def setup(self):
		from ScopeFoundryHW.ADS.ads1115_hw import ADS_HW
		self.add_hardware(ADS_HW(self))

		from ScopeFoundryHW.ADS.ads1115_optimizer import ADS_Optimizer
		self.add_measurement(ADS_Optimizer(self))
		#self.ui.show()

if __name__ == '__main__':
	import sys
	app = ADS_App([])
	#app = QApplication(sys.argv)
	ads = ADS_App(sys.argv)
	sys.exit(app.exec_())
	

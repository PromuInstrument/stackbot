"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
from __future__ import absolute_import, print_function, division
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import XboxControllerTestMeasure
from ScopeFoundryHW.xbox_controller.xbox_controller_hw import XboxControllerHW
import logging

logging.basicConfig(level='DEBUG')

class XboxApp(BaseMicroscopeApp):
	"""This class loads ScopeFoundry modules into the ScopeFoundry app related to
	Xbox hardware and measurement modules."""
	def setup(self):
		"""Setup function attempts to load desired modules into ScopeFoundry app
		and activates its respective graphical user interface."""
		self.xbcontrol_hc = self.add_hardware_component(XboxControllerHW(self))
		self.xbcontrol_mc = self.add_measurement_component(XboxControllerTestMeasure(self))
		self.ui.show()
		self.ui.activateWindow()
		
import sys

app = XboxApp(sys.argv)

sys.exit(app.exec_())
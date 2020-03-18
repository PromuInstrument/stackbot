"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
from __future__ import absolute_import, print_function, division
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import XboxControllerTestMeasure
from ScopeFoundryHW.xbox_controller.xbox_controller_hw import XboxControllerHW
from ScopeFoundryHW.xbox_controller.xbox_controller_base_measure import XboxBaseMeasure
import logging

#logging.basicConfig(level='DEBUG')

class XboxApp(BaseMicroscopeApp):
	"""
	This class loads ScopeFoundry modules into the ScopeFoundry app related to
	Xbox hardware and measurement modules.
	
	+-------------------+----------------------------+-----------------------------------------------+
    | Module Type       | Module Name                | Description                        			 |
    +===================+============================+===============================================+
    | Device			| XboxControllerDevice		 | Creates initializes pygame objects needed to  |
	|					|							 | interface with hardware and autodetects 	 	 |
	|					|							 | hardware characteristics such as the number   |
	|					|							 | of buttons, hats, or sticks.				 	 |
	+-------------------+----------------------------+-----------------------------------------------+
    | Hardware 			| XboxControllerHW			 | Defines button maps and *LoggedQuantities*	 |
    |					|							 | used to interpret signals received by 		 |
	|    				|							 | pygame module from controller.				 |
    |					|							 |									  			 |
    +-------------------+----------------------------+-----------------------------------------------+
    | Measurement		| XboxControllerTestMeasure  | Description						  			 |
    |					|							 |									  			 |
    +-------------------+----------------------------+-----------------------------------------------+

	"""
	def setup(self):
		"""Setup function attempts to load desired modules into ScopeFoundry app
		and activates its respective graphical user interface."""
		self.stage1 = self.add_hardware(ASIStageHW(self, name='stage_top',  swap_xy=True))
		self.stage2 = self.add_hardware(ASIStageHW(self, name='stage_bottom',  swap_xy=True))
		
		self.xbcontrol_hc = self.add_hardware_component(XboxControllerHW(self))
# 		self.xbcontrol_mc = self.add_measurement_component(XboxControllerTestMeasure(self))
		self.xbcontrol_mc = self.add_measurement_component(XboxBaseMeasure(self))
		self.ui.show()
		self.ui.activateWindow()
		
import sys

app = XboxApp(sys.argv)

sys.exit(app.exec_())
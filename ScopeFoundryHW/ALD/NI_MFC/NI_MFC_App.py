'''
Created on Aug 29, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
						<alanbuckley@berkeley.edu>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging




class NI_MFC_App(BaseMicroscopeApp):
	
	"""Module which controls MKS 1479 Mass Flow Controller via its analog
	DA-15 connector with the use of a National Instruments USB-6001 
	Multifunction I/O device.
	
	This device regulates analog voltages needed to adjust or read MFC flow values 
	as well as opening or closing its valve.
	
	
	+-------------------+----------------------------+------------------------------------------------------+
	|	Module Type		|	Module Name				 |	Description											|
	+===================+============================+======================================================+
	|	Hardware		|	NI_MFC					 |	Establishes Read/Write *LoggedQuantities*			|
	|					|							 |	Wraps NI DAQ functions needed to carry out commands.|
	+-------------------+----------------------------+------------------------------------------------------+
	|	Measurement		|	NI_MFC_Measure			 |	Actively reads current flow rate in					|
	|					|							 |	MFC.												|
	+-------------------+----------------------------+------------------------------------------------------+
	"""
	
	name="ni_mfc_app"
	
	def setup(self):
		
		from ScopeFoundryHW.ALD.NI_MFC.ni_mfc_hardware import NI_MFC
		self.add_hardware(NI_MFC(self))
		
		from ScopeFoundryHW.ALD.NI_MFC.ni_mfc_measure import NI_MFC_Measure
		self.add_measurement(NI_MFC_Measure(self))
	
if __name__ == '__main__':
	import sys
	app = NI_MFC_App(sys.argv)
	sys.exit(app.exec_()) 
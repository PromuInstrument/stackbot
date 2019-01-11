'''
Created on Aug 29, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging




class NI_MFC_App(BaseMicroscopeApp):
    
    """
    * Module controls Digital and Analog ports on a National Instruments \
        USB-6001 DAQ controller.
    * This DAQ card provides the electrical interface needed to control connected \
        MKS 1479 Mass Flow Controller via its analog DA-15 connector 
    
    * This device regulates analog voltages needed to adjust or read MFC flow values 
    
    * Opening or closing the connected MFC valve involves toggling digital outputs on \
        National Instruments DAQ card. These are turned on one at a time and serve as \
        overrides to the default setpoint mode on the MFC.
    
    
    +-------------------+----------------------------+-----------------------------------------------------------------+
    |    Module Type    |    Module Name             |    Description                                                  |
    +===================+============================+=================================================================+
    |    Hardware       |    NI_MFC                  |    * Establishes Read/Write *LoggedQuantities* for              |
    |                   |                            |        setpoint mode operation.                                 |
    |                   |                            |    * Boolean *LoggedQuantities*, used to open and close         |
    |                   |                            |        the MFC valve are overrides to default setpoint mode.    |
    |                   |                            |    * Wraps NI DAQ functions needed to carry out commands.       |
    |                   |                            |                                                                 |
    +-------------------+----------------------------+-----------------------------------------------------------------+
    |    Measurement    |    NI_MFC_Measure          |    Actively reads current flow rate in                          |
    |                   |                            |    MFC.                                                         |
    +-------------------+----------------------------+-----------------------------------------------------------------+
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
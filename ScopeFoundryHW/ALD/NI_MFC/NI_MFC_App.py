'''
Created on Aug 29, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
						<alanbuckley@berkeley.edu>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging




class NI_MFC_App(BaseMicroscopeApp):
    
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
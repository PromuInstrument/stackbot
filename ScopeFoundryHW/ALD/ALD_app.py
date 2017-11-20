'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)


class ALD_App(BaseMicroscopeApp):
    
    name="ald_app"
    
    def setup(self):
        from ScopeFoundryHW.ALD.MKS_600.mks_hw import MKS_Hardware
        self.add_hardware(MKS_Hardware(self))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.vgc_hw import VGC_Hardware
        self.add_hardware(VGC_Hardware(self))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.vgc_measure import VGC_Measure
        self.add_measurement(VGC_Measure(self))
        
if __name__ == '__main__':
    import sys
    app = ALD_App(sys.argv)
    sys.exit(app.exec_()) 
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
        
        from ScopeFoundryHW.ALD.ALD_relay.ald_relay_hardware import ALDRelayHW
        self.add_hardware(ALDRelayHW(self))
        
        from ScopeFoundryHW.ALD.MKS_146.mks_146_hw import MKS_146_Hardware
        self.add_hardware(MKS_146_Hardware(self))
         
        from ScopeFoundryHW.ALD.MKS_600.mks_600_hw import MKS_600_Hardware
        self.add_hardware(MKS_600_Hardware(self))
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
        self.add_hardware(Pfeiffer_VGC_Hardware(self))
          
        from ScopeFoundryHW.ALD.Seren.seren_hw import Seren_HW
        self.add_hardware(Seren_HW(self))
        
        from ScopeFoundryHW.ALD.ALD_relay.ald_relay_measure import ALDRelayMeasure
        self.add_measurement(ALDRelayMeasure(self))
          
        from ScopeFoundryHW.ALD.MKS_146.mks_146_measure import MKS_146_Measure
        self.add_measurement(MKS_146_Measure(self))
          
        from ScopeFoundryHW.ALD.MKS_600.mks_600_measure import MKS_600_Measure
        self.add_measurement(MKS_600_Measure(self))
         
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_measure import Pfeiffer_VGC_Measure
        self.add_measurement(Pfeiffer_VGC_Measure(self))
        
        from ScopeFoundryHW.ALD.Seren.seren_measure import Seren_Measure
        self.add_measurement(Seren_Measure(self))
        
        
if __name__ == '__main__':
    import sys
    app = ALD_App(sys.argv)
    sys.exit(app.exec_()) 
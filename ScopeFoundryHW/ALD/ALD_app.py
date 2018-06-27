'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging
from qtpy import QtCore
from PyQt5 import QtWidgets

# logging.disable(50)



class ALD_App(BaseMicroscopeApp):
    
    name="ald_app"
    
    def setup(self):
        
        from ScopeFoundryHW.ALD.ALD_relay.ald_relay_hardware import ALDRelayHW
        relay = self.add_hardware(ALDRelayHW(self))
        relay.settings['connected'] = True
        
        from ScopeFoundryHW.ALD.ALD_shutter.ALD_shutter import ALD_Shutter
        self.add_hardware(ALD_Shutter(self)).settings['connected'] = True
        
        from ScopeFoundryHW.ALD.ellipsometer.ellipsometer_hw import Ellipsometer
        self.add_hardware(Ellipsometer(self))
        
        from ScopeFoundryHW.ALD.Lovebox.lovebox_hw import LoveboxHW
        self.add_hardware(LoveboxHW(self)).settings['connected'] = True
        
        from ScopeFoundryHW.ALD.MKS_146.mks_146_hw import MKS_146_Hardware
        self.add_hardware(MKS_146_Hardware(self)).settings['connected'] = True
         
        from ScopeFoundryHW.ALD.MKS_600.mks_600_hw import MKS_600_Hardware
        self.add_hardware(MKS_600_Hardware(self)).settings['connected'] = True
        
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_hw import Pfeiffer_VGC_Hardware
        self.add_hardware(Pfeiffer_VGC_Hardware(self)).settings['connected'] = True
          
        from ScopeFoundryHW.ALD.Seren.seren_hw import Seren_HW
        self.add_hardware(Seren_HW(self)).settings['connected'] = True
        
        from ScopeFoundryHW.ALD.ALD_relay.ald_relay_measure import ALDRelayMeasure
        self.add_measurement(ALDRelayMeasure(self)).start()
          
        from ScopeFoundryHW.ALD.Lovebox.lovebox_measure import LoveboxMeasure
        self.add_measurement(LoveboxMeasure(self)).start()
        
        from ScopeFoundryHW.ALD.MKS_146.mks_146_measure import MKS_146_Measure
        self.add_measurement(MKS_146_Measure(self)).start()
        
        from ScopeFoundryHW.ALD.MKS_600.mks_600_measure import MKS_600_Measure
        self.add_measurement(MKS_600_Measure(self)).start()
         
        from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_measure import Pfeiffer_VGC_Measure
        self.add_measurement(Pfeiffer_VGC_Measure(self)).start()
        
        from ScopeFoundryHW.ALD.Seren.seren_measure import Seren
        self.add_measurement(Seren(self)).start()

        from ScopeFoundryHW.ALD.ALD_recipes.ALD_recipe import ALD_Recipe
        self.add_measurement(ALD_Recipe(self))
        
        from ScopeFoundryHW.ALD.ALD_recipes.ALD_params_measure import ALD_params
        self.add_measurement(ALD_params(self)).start()
        





if __name__ == '__main__':
    import sys
    app = ALD_App(sys.argv)
    sys.exit(app.exec_()) 
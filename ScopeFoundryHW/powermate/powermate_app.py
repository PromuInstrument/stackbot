'''
Created on Jun 29, 2017

@author: Alan Buckley
'''
import sys
from ScopeFoundry import BaseMicroscopeApp

class PowermateApp(BaseMicroscopeApp):
    
    def setup(self):

        from ScopeFoundryHW.powermate.powermate_hw import PowermateHW
        self.add_hardware(PowermateHW(self))

        from ScopeFoundryHW.powermate.powermate_measure import PowermateMeasure
        self.add_measurement(PowermateMeasure(self))
        self.ui.show()
        self.ui.activateWindow()

        
if __name__ == '__main__':
    
    app = PowermateApp(sys.argv)
    
    sys.exit(app.exec_())
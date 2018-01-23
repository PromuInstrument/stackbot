'''
Created on Jul 10, 2017

@author: Alan Buckley
'''

from ScopeFoundry import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class TenmaApp(BaseMicroscopeApp):
    
    name = "tenma_app"
    
    def setup(self):
        from ScopeFoundryHW.tenma_power.tenma_hw import TenmaHW
        self.add_hardware(TenmaHW(self))
        
        self.ui.show()
        self.ui.activateWindow()
        
if __name__ == '__main__':
    import sys
    app = TenmaApp(sys.argv)
    sys.exit(app.exec_())

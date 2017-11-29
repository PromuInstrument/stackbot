'''
Created on Jun 29, 2017

@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class PicomotorApp(BaseMicroscopeApp):
    
    name = 'picomotor_app'
    
    def setup(self):
        
        from ScopeFoundryHW.picomotor.picomotor_hw import PicomotorHW
        self.add_hardware(PicomotorHW(self))
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
    import sys
    app = PicomotorApp(sys.argv)
    sys.exit(app.exec_())
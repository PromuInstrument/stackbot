'''
Created on Jul 20, 2017

@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class PololuApp(BaseMicroscopeApp):
    
    name = 'pololu_servo_app'
    
    def setup(self):
        
        from ScopeFoundryHW.pololu_servo.pololu_hw import PololuHW
        self.add_hardware(PololuHW(self))
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
    import sys
    app = PololuApp(sys.argv)
    sys.exit(app.exec_())
'''
Created on Feb 8, 2017

@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class RelayArduinoApp(BaseMicroscopeApp):
    
    name = 'relay_arduino_app'
    
    def setup(self):
        
        from ScopeFoundryHW.relay_arduino.relay_arduino_hw import RelayArduinoHW
        self.add_hardware(RelayArduinoHW(self))
        
        from ScopeFoundryHW.relay_arduino.relay_arduino_optimizer import RelayArduinoOptimizer
        self.add_measurement(RelayArduinoOptimizer(self))
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
    import sys
    app = RelayArduinoApp(sys.argv)
    sys.exit(app.exec_())
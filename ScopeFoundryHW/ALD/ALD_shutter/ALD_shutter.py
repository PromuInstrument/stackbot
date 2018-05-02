
'''
Created on Apr 28, 2018

@author: Alan Buckley
<alanbuckley@lbl.gov>
<alanbuckley@berkeley.edu>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_interface import ShutterServoArduino

class ALD_Shutter(HardwareComponent):
    
    name = 'ald_shutter'
    
    def setup(self):
        
        self.settings.New('port', dtype=str, initial='COM5', ro=False)
        self.settings.New('position', dtype=int, initial=0, ro=False)
        
    def connect(self):
        
        self.servo = ShutterServoArduino(port=self.settings['port'], debug=self.debug_mode.val)
        
        self.settings.position.connect_to_hardware(write_func=self.servo.write_position,
                                                   read_func=self.servo.read_position)
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'servo'):
            self.servo.close()
            del self.servo
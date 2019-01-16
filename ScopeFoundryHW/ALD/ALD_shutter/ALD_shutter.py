
'''
Created on Apr 28, 2018

@author: Alan Buckley
<alanbuckley@lbl.gov>
<alanbuckley@berkeley.edu>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_interface import ShutterServoArduino

class ALD_Shutter(HardwareComponent):
    
    """
    Uses
    :class:`ShutterServoArduino` library to control a rotary servo which moves 
    a shutter between closed and open positions.
    
    This shutter mechanism is meant to serve as an alternative to switching the 
    RF power supply on and off.
    """
    
    name = 'ald_shutter'
    
    def setup(self):
        """Creates *LoggedQuantities*."""
        self.settings.New('port', dtype=str, initial='COM10', ro=False)
        self.settings.New('position', dtype=int, initial=0, ro=False)
        self.settings.New('shutter_open', dtype=bool, initial=False, ro=False)
        
    def connect(self):
        """
        * Instantiates \
        :class:`ShutterServoArduino` library. 
        * Establishes hardware--:class:`LoggedQuantity` connections.
        """
        self.servo = ShutterServoArduino(port=self.settings['port'], debug=self.settings['debug_mode'])
        
        if self.settings['debug_mode']:
            print('Debug mode enabled. Bypassing connection')
        else:                                   
            self.settings.position.connect_to_hardware(write_func=self.servo.write_position,
                                               read_func=self.servo.read_position)
    
        self.settings.shutter_open.add_listener(self.shutter_cmd, bool)
    
    def shutter_cmd(self, x):
        """
        Sets the shutter position.
        
        =============  ==========  ==========================
        **Arguments**  **Type**    **Description**        
        x              bool        Shutter open/close
        =============  ==========  ==========================
        
        =============  ===============
        **Argument**   **Description**
        True (1)       Shutter Open
        False (0)      Shutter Close   
        =============  ===============
        """
        state = x
        self.settings['shutter_open'] = bool(x)
        if self.settings['shutter_open']:
            self.settings['position'] = 1
        else:
            self.settings['position'] = 166    
    
    def shutter_toggle(self):
        """
        Toggles shutter position between open and closed with each call.
        """
        self.settings['shutter_open'] = not self.settings['shutter_open']
        if self.settings['shutter_open']:
            self.settings['position'] = 1
        else:
            self.settings['position'] = 166 
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'servo') and not self.settings['debug_mode']:
            self.servo.close()
            del self.servo
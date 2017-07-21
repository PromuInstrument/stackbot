"""
Polulu Micro Maestro ScopeFoundry module
Created on Jul 19, 2017

@author: Alan Buckley

Logistical advice given by Ed Barnard.
"""

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try:
    from ScopeFoundryHW.pololu_servo.pololu_interface import PololuDev
except Exception as err:
    logger.error("Cannot load required modules for PololuDev, {}".format(err))

class PololuHW(HardwareComponent):
    
    name = 'pololu_servo_hw'
    
    servo_type_choices = ("Linear", "Rotary")
                        
    servo_type_limit = {'Rotary': (544,2544),
                    'Linear': (1008,2000)}
     
    
    def setup(self):
        """Sets up logged quantities. Sets presets and constants."""
        
        self.settings.New(name='port', initial='COM7', dtype=str, ro=False)
        
        ## Increase/decrease number of servo slots by modifying the below value.
        self.servo_range = 2
        
        
        for i in range(self.servo_range):
            self.settings.New(name="servo{}_type".format(i), dtype=str, initial='Linear', choices=self.servo_type_choices, ro=False)
            _vmin, _vmax = self.servo_type_limit[self.settings['servo{}_type'.format(i)]]
            self.settings.New(name="servo{}_position".format(i), dtype=int, 
                                            vmin=_vmin, vmax=_vmax, ro=False)
        
        ## In my particular setup, I want to override the default value set by the above for loop in the case of servo_0    
        self.settings.get_lq('servo0_type').update_value('Rotary')
        self.update_min_max(0)
        
    def connect(self):
        """
        Instantiates device class object, sets up read/write signals, sets up listeners which: update software servo limits, 
        and reinstantiates device object, should the port value be updated. Finally, the function reads all values from hardware.
        """
        self.dev = PololuDev(port=self.settings['port'])
        
        for i in range(self.servo_range):
            self.settings.get_lq('servo{}_position'.format(i)).connect_to_hardware(
                                                    write_func=getattr(self, 'write_position{}'.format(i)),
                                                    read_func=getattr(self, 'read_position{}'.format(i))
                                                    )

        for i in range(self.servo_range):
            self.settings.get_lq('servo{}_type'.format(i)).add_listener(
                    lambda servo_number=i: self.update_min_max(servo_number)
                    )
        
        self.read_from_hardware()
     
     
    
    def update_min_max(self, servo_number):
        servo_type = self.settings['servo{}_type'.format(servo_number)]
        vmin, vmax = self.servo_type_limit[servo_type]
        self.settings.get_lq("servo{}_position".format(servo_number)).change_min_max(vmin,vmax)

        
    def write_position0(self, position):
        self.dev.write_position(0, target=position)
    def write_position1(self, position):
        self.dev.write_position(1, target=position)
    def write_position2(self, position):
        self.dev.write_position(2, target=position)
    def write_position3(self, position):
        self.dev.write_position(3, target=position)
    def write_position4(self, position):
        self.dev.write_position(4, target=position)
    def write_position5(self, position):
        self.dev.write_position(5, target=position)
    
    
        
    def read_position0(self):
        return self.dev.read_position(0)/4
    def read_position1(self):
        return self.dev.read_position(1)/4
    def read_position2(self):
        return self.dev.read_position(2)/4
    def read_position3(self):
        return self.dev.read_position(3)/4
    def read_position4(self):
        return self.dev.read_position(4)/4
    def read_position5(self):
        return self.dev.read_position(5)/4
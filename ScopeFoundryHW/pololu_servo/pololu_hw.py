"""
Polulu Micro Maestro ScopeFoundry module
Created on Jul 19, 2017

@author: Alan Buckley
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
    
    servo_choices = ("Linear", "Rotary")
                        
    servo_limits = {'Rotary': (544,2544),
                    'Linear': (1008,2000)}
                    
    
    def setup(self):
        self.dev = PololuDev()
        
        self.settings.New(name="servo_0_type", dtype=str, initial='Rotary', choices=self.servo_choices, ro=False)
        self.settings.New(name="servo_1_type", dtype=str, initial='Linear', choices=self.servo_choices, ro=False)
        self.settings.New(name="servo_0_position", dtype=int, 
                                    vmin=self.servo_limits[self.settings['servo_0_type']][0], 
                                    vmax=self.servo_limits[self.settings['servo_0_type']][1],
                                    ro=False)
        self.settings.New(name="servo_1_position", dtype=int, 
                                    vmin=self.servo_limits[self.settings['servo_1_type']][0], 
                                    vmax=self.servo_limits[self.settings['servo_1_type']][1],
                                    ro=False)
        print(self.servo_limits[self.settings['servo_1_type']][0], self.servo_limits[self.settings['servo_1_type']][1])
        
    def connect(self):
        
        self.settings.get_lq('servo_0_position').connect_to_hardware(
                                                    write_func=self.write_position0,
                                                    read_func=self.read_position0
                                                    )
        
        self.settings.get_lq('servo_1_position').connect_to_hardware(
                                                    write_func=self.write_position1,
                                                    read_func=self.read_position1
                                                    )
        
        profile0 = {"lqname": "servo_0_position",
                    "servo_type": "servo_0_type"}
        profile1 = {"lqname": "servo_1_position",
                    "servo_type": "servo_1_type"}
        
        self.settings.get_lq('servo_0_type').add_listener(self.update_threshold, str, **profile0)
#    Traceback:
#>       self.settings.get_lq('servo_0_type').add_listener(self.update_threshold, str, **profile0)
#>       self.updated_value[argtype].connect(func, **kwargs)
#>       TypeError: 'lqname' is an invalid keyword argument for this function  

        self.settings.get_lq('servo_1_type').add_listener(self.update_threshold, str, **profile1)
     
    
    def update_threshold(self, lqname, servo_type):
        print(lqname, servo_type)
#         new_servo_type = self.settings.get_lq(servo_type).val
#         vmin, vmax = self.servo_limits[new_servo_type]
#         self.settings.get_lq(lqname).change_min_max(vmin,vmax)
         
        
    def write_position0(self, position):
        self.dev.write_position(0, target=position)
    def write_position1(self, position):
        self.dev.write_position(1, target=position)
        
    def read_position0(self):
        return self.dev.read_position(0)/4
    def read_position1(self):
        return self.dev.read_position(1)/4
            
'''
Created on Jun 28, 2017

@author: Alan Buckley
'''

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try:
    from ScopeFoundryHW.picomotor.picomotor_dev import PicomotorDev
except Exception as err:
    logger.error("Cannot load required modules for PicomotorDev, {}".format(err))
    
class PicomotorHW(HardwareComponent):
    
    name = "picomotor_hw"
    
    def setup(self):
        self.port = self.settings.New(name="port", initial="", dtype=str, ro=False)
        self.ip_address = self.settings.New(name="ip_address", initial="192.168.1.2", dtype=str, ro=False)
        self.ip_port = self.settings.New(name="ip_port", initial="23", dtype=str, ro=False)
        
        for i in range(4):
            self.settings.New(name="axis_{}_position".format(i+1), initial=0, dtype=int, ro=False)
            self.settings.New(name="axis_{}_velocity".format(i+1), initial=20, dtype=int, ro=False)
                
                   
    def connect(self):
        
        try:
            self.picomotor_dev = PicomotorDev(ip=self.ip_address.val, ip_port=self.ip_port.val, debug=self.debug_mode.val)
            if self.picomotor_dev:
                logger.debug("PicomotorDev connected.")
        finally:
            if not self.picomotor_dev:
                if len(self.port.val) > 0:
                    self.picomotor_dev = PicomotorDev(port=self.port.val)
                else:
                    logger.error("Neither IP information nor local serial port information have been provided.")
            
        for i in range(4):
            def position_set(x, n=i):
                self.picomotor_dev.write_pos(n+1, x)
            def position_get(n=i):
                self.picomotor_dev.read_pos(n+1)
            def velocity_set(x, n=i):
                self.picomotor_dev.write_velocity(n+1, x)
            def velocity_get(n=i):
                self.picomotor_dev.read_velocity(n+1)
            self.settings.get_lq('axis_{}_position'.format(i+1)).connect_to_hardware(
                                                        write_func = position_set,
                                                        read_func = position_get)
            self.settings.get_lq('axis_{}_velocity'.format(i+1)).connect_to_hardware(
                                                        write_func = velocity_set,
                                                        read_func = velocity_get)
            self.settings.get_lq('axis_{}_position'.format(i+1)).write_to_hardware()
            self.settings.get_lq('axis_{}_velocity'.format(i+1)).write_to_hardware()
            
            
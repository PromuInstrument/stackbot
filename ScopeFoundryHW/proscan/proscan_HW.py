'''
@author: Alan Buckley
'''

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try:
    from ScopeFoundryHW.proscan.proscan_interface import ProscanInterface
except Exception as err:
    logger.error("Cannot load required modules for ProScan, {}".format(err))
    
class Proscan_HW(HardwareComponent):
    
    name='proscan_hw'
    
    def setup(self):
        self.port = self.settings.New(name="port", initial="COM1", dtype=str, ro=False)
        self.settings.New(name='debug_mode', initial=False, dtype=bool, ro=False)
        self.settings.New(name="axes_limits", initial=[0,0,0,0,0,0,0,0], array=True, dtype=int, ro=True)
        self.settings.New(name="axes_motion", initial=[0,0,0,0,0,0], array=True, dtype=int, ro=True)
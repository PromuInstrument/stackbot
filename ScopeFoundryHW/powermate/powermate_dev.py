'''
Created on Jun 29, 2017

Xbox ScopeFoundry demonstration module upon which this module was based, 
was written by Alan Buckley with suggestions for improvement from Ed Barnard and Lev Lozhkin

@author: Alan Buckley
'''

from pywinusb import hid
import time
#from pygame.constants import JOYAXISMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP
import logging

logger = logging.getLogger(__name__)

class PowermateDev(object):
    
    name = 'powermate_dev'
    
    def detect_devices(self):
        self.filter = hid.HidDeviceFilter(vendor_id=0x077D)
        self.retrieve_addresses()
        print(self.dev_num)
            
    
    def retrieve_addresses(self):
        self.device_map = {}
        
        for j, v in enumerate(self.filter.get_devices_by_parent().items()):
            print(j, type(j))
            addr_hw_pair = tuple([v[0], v[1][0]])
            self.device_map[j] = addr_hw_pair
            self.dev_num = j

#             setattr(self, 'device{}'.format(j), v[1][0])

# 
#             
#     def open_device(self, i):
#         if not getattr(self, "device{}".format(i)).is_opened():
#             getattr(self, "device{}".format(i)).open()
# #         self.map_listeners()
# 
#     def close_device(self, i):
#         if getattr(self, "device{}".format(i)).is_opened():
#             getattr(self, "device{}".format(i)).close()
#         
    

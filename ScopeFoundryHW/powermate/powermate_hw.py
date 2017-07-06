'''
Created on Jun 29, 2017

@author: Alan Buckley
'''


from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.powermate.powermate_dev import PowermateDev


class PowermateHW(HardwareComponent):

    name = "powermate_hw"

    def setup(self):
        self.settings.New(name='devices', initial=None, dtype=str, choices = [], ro=True)
        self.settings.New(name='button', initial=True, dtype=bool, ro=True)
        self.settings.New(name='wheel_axis', initial=0, dtype=int, ro=True)

        
    def connect(self):
        """Connects to equipment level module, 
        loads the appropriate key map into memory,
        opens the selected device, sets data handler."""
        self.dev = PowermateDev()
        self.dev.detect_devices()
        
        self.choice_list = []
        for i in range(self.dev.dev_num+1):
            update = (self.dev.device_map[i][0])
            self.choice_list.append(update)
        
        self.settings.devices.change_choice_list(self.choice_list)
                
    def open_active_device(self):
           
        if hasattr(self, 'active_device'):
            if self.active_device.is_opened:
                self.active_device.close()
        else: pass
        device_addr = self.settings.devices.val
        print(device_addr, type(device_addr))
        self.active_device = self.dev.filter.get_devices_by_parent()[int(device_addr)][0]
        self.active_device.open()
        
    def set_data_handler(self):
        self.active_device.set_raw_data_handler(self.raw_data_handler)
            
    def raw_data_handler(self, data):
#         print(data)
        self.settings['button'] = bool(data[1])
        wheel = data[2]
        if wheel > 1:
            self.settings['wheel_axis'] -= 1
        elif wheel == 1:
            self.settings['wheel_axis'] += 1    
                        
    def disconnect(self):
        """Hardware disconnect and cleanup function."""
        self.dev.close_devices()
        del self.dev
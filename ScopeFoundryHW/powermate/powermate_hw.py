'''
Created on Jun 29, 2017

@author: Alan Buckley, Benedikt Ursprung, Edward Barnard
'''

from pywinusb import hid
from ScopeFoundry import HardwareComponent
from qtpy import QtCore

class PowermateHW(HardwareComponent):
    
    name = "powermate_hw"
    
    # Signals emitted on powermate events
    button_pressed  = QtCore.Signal(int) # channel
    button_released = QtCore.Signal(int) # channel
    moved = QtCore.Signal( (int, int, bool) ) # channel, direction, button
    moved_left = QtCore.Signal( (int, bool) ) # channel, button
    moved_right = QtCore.Signal( (int, bool) ) # channel, button
    
    # Use for example
    # self.app.hardware['powermate_hw'].moved.connect(callback_func)
    # where callback_func has (channel, direction, button) as arguments
        
    def data_handler(self, data, dev_num):
        """emit signals on powermate events"""        
        button_down = bool(data[1])
        wheel = data[2]
        
        if button_down:
            self.button_pressed.emit( dev_num )
        else:
            self.button_released.emit( dev_num )
        
        if wheel > 1:
            direction = -1
            self.moved_left.emit( dev_num, True )
        else:
            direction = +1
            self.moved_left.emit( dev_num, button_down )
        
        self.moved.emit( dev_num, direction, button_down )
        
    def connect(self):
        """creates list of devices, opens them, and set data handlers"""
        # get device addresses        
        self.filter = hid.HidDeviceFilter(vendor_id=0x077D, product_id = 0x0410)
        self.device_addrs = []
        for v in self.filter.get_devices_by_parent().items():
            self.device_addrs.append(v[0])
        
        # create devices
        self.devices = []
        for addr in self.device_addrs:
            dev = self.filter.get_devices_by_parent()[addr][0]           
            self.devices.append(dev)
    
        self.open_all_devices()
        self.set_data_handlers()
        
    def setup(self):
        self.settings.New('number_of_devices', dtype=int, initial = 2, ro=True)

    def set_data_handlers(self):
        for ii,dev in enumerate(self.devices):
            dev.set_raw_data_handler(lambda data, dev_num=ii:self.data_handler(data,dev_num))
        self.settings['number_of_devices'] = ii
            
    def open_all_devices(self):
        for dev in self.devices:
            dev.open()
            if not dev.is_opened:           
                dev.open()
        
    def close_all_devices(self):
        for dev in self.devices:
            if dev.is_opened():
                dev.close()     
        
    def disconnect(self):
        """Hardware disconnect and cleanup function."""
        if hasattr(self, 'devices'):
            self.close_all_devices()
            del self.devices
            
        if hasattr(self, 'device_addrs'):
            del self.device_addrs
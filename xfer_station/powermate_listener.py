from pywinusb import hid
from ScopeFoundry import Measurement
from qtpy import QtCore
import time

class PowermateListener(Measurement):
    
    name = 'powermate_listener'

    # Signals emitted on powermate events
    button_pressed  = QtCore.Signal(int) # channel
    button_released = QtCore.Signal(int) # channel
    moved = QtCore.Signal( (int, int, bool) ) # channel, direction, button
    moved_left = QtCore.Signal( (int, bool) ) # channel, button
    moved_right = QtCore.Signal( (int, bool) ) # channel, button
    

    def setup(self):
        
        self.axes = []
        
        for stage in ['stage_top', 'stage_bottom']:
            for ax in "xyz":
                A = {}
                self.axes.append(A)

                
                axname = stage + "_" + ax
                en = self.settings.New(axname+"_enable", dtype=bool, )
                dev = self.settings.New(axname+"_dev", dtype=int, )
                step = self.settings.New(axname+"_step", dtype=float, si=True, initial=1e-6, unit="m" )
                
                A['name'] = axname
                A['ax'] = ax
                A['stage'] = stage
                A['enable_lq'] = en
                A['dev_lq'] = dev
                A['step_lq'] = step
                
                
    
    def run(self):
        
        try:
            
            self.filter = hid.HidDeviceFilter(vendor_id=0x077D, product_id = 0x0410)
            self.devices = []
    
            ii = 0
            for dev in self.filter.get_devices():
                #assert len(v) = 1
                #dev = v[0]
                print(dev)
                self.devices.append(dev)
                dev.open()
                if not dev.is_opened:           
                    dev.open()            
                dev.set_raw_data_handler(lambda data, dev_num=ii:self.data_handler(data,dev_num))
                ii += 1
            
            while not self.interrupt_measurement_called:
                time.sleep(1.0)
                
        finally:
            for dev in self.devices:
                if dev.is_opened():
                    dev.close()     
            
            

    def data_handler(self, data, dev_num):
        """emit signals on powermate events"""
        
        print("Powermate data_handler",dev_num,  data)
            
        button_down = bool(data[1])
        wheel = data[2]
        
        if button_down:
            self.button_pressed.emit( dev_num )
        else:
            self.button_released.emit( dev_num )
        
        if wheel > 1:
            direction = -1
            #self.moved_left.emit( dev_num, True )
        else:
            direction = +1
            #self.moved_left.emit( dev_num, button_down )
        
        self.moved.emit( dev_num, direction, button_down )
        
        for A in self.axes:
            if A['dev_lq'].value == dev_num:
                if A['enable_lq'].value:
                    print(dev_num, A['name'], 'moving')
                    ax = A['ax']
                    S = self.app.hardware[A['stage']].settings
                    S[ax + "_target"] = S[ax+"_position"] + direction*A['step_lq'].value*1e3
                    
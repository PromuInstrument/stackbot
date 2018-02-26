from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.thorlabs_elliptec.elliptec_dev import ThorlabsElliptecDevice

class ThorlabsElliptecSingleHW(HardwareComponent):
    
    name = 'elliptec'
    
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM6')
        self.settings.New('addr', dtype=int, initial=0, vmin=0, vmax=15)
        self.settings.New('position', dtype=float, initial=0)
        
        self.add_operation('Home', self.home_device)
        
    def connect(self):
        S = self.settings
        self.dev = ThorlabsElliptecDevice(port=S['port'], addr=S['addr'], debug=S['debug_mode'])
        self.dev.get_information()
        
        self.settings.position.reread_from_hardware_after_write = True
        self.settings.position.connect_to_hardware(
            read_func= self.dev.get_position,
            write_func= self.dev.move_absolute
            )

        self.settings.position.read_from_hardware()

        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    def home_device(self):
        self.dev.home_device()
            
class ThorlabsElliptcMultiHW(HardwareComponent):
    
    name = 'elliptec_motors'
    
    def __init__(self, app, debug=False, name=None, motors=[(0, 'zero'), (1,'one')] ):
        self.motors = motors
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM6')

        for addr, name in self.motors:
            self.add_operation('Home '+name, lambda name=name: self.home_device(name) )
            self.settings.New(name + '_position', dtype=float, initial=0)


    def connect(self):
        S = self.settings
        self.dev = ThorlabsElliptecDevice(port=S['port'],  debug=S['debug_mode'])

        
        for addr, name in self.motors:
            pos = self.settings.get_lq(name + "_position")
            pos.reread_from_hardware_after_write = True
            pos.connect_to_hardware(
                read_func= lambda addr=addr: self.dev.get_position(addr),
                write_func=  lambda x, addr=addr: self.dev.move_absolute(x, addr)
                )
            
            self.dev.get_information(addr)
            pos.read_from_hardware()


    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    def home_device(self, name):
        for addr, motor_name in self.motors:
            if name == motor_name:
                self.dev.home_device(addr=addr)

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.pololu_servo.pololu_interface import PololuMaestroDevice

class PololuMaestroServoHW(HardwareComponent):
    
    name = 'pololu_maestro_servo'
    
    
    def setup(self):        
        self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
        self.settings.New(name='servo_num', dtype=int, initial=1, ro=False)
        self.settings.New(name="servo_position", dtype=int, 
                                        vmin=500, vmax=2500, ro=False)
        
    
    def connect(self):
        self.dev = PololuMaestroDevice(port=self.settings['port'])

        self.settings.servo_position.connect_to_hardware(
            read_func=lambda: self.dev.read_position(self.settings['servo_num']),
            write_func=lambda pos: self.dev.write_position(self.settings['servo_num'],pos)
            )
        
        self.settings.servo_position.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
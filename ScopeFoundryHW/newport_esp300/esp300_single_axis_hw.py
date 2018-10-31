from ScopeFoundry.hardware import HardwareComponent
from .esp300_dev import ESP300

class ESP300AxisHW(HardwareComponent):
    
    name = 'esp300'
    
    def setup(self):
        
        self.settings.New('port', str, initial='COM5')
        self.settings.New('axis', int, initial=1, vmin=1, vmax=3)
        self.settings.New('enabled', bool, initial=True)
        self.settings.New('is_moving', bool, ro=True)
        self.settings.New('pos', float, ro=True)
        self.settings.New('target_pos', float)
        
    def connect(self):
        
        self.esp = ESP300(port=self.settings['port'],
                          debug=self.settings['debug_mode'])
        
        
        self.settings.pos.connect_to_hardware(
            read_func=self.read_pos)
        
        self.settings.target_pos.connect_to_hardware(
            write_func=self.write_pos)
        
        self.settings.enabled.connect_to_hardware(
            read_func=self.read_enabled,
            write_func=self.write_enabled
            )
    
        self.settings.is_moving.connect_to_hardware(
            read_func=self.read_is_moving)

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'esp'):
            self.esp.close()
            del self.esp
    
    
        
    def read_pos(self):
        return self.esp.read_pos(self.settings['axis'])
    
    def write_pos(self, pos):
        self.esp.write_pos_abs(self.settings['axis'], pos)
    
    def read_enabled(self):
        return self.esp.read_enabled(self.settings['axis'])
    
    def read_is_moving(self):
        return self.esp.read_is_moving(self.settings['axis'])
    
    def write_enabled(self, enabled):
        self.esp.write_enabled(self.settings['axis'], enabled)


if __name__ == "__main__":
    
    from ScopeFoundry import BaseMicroscopeApp
    
    app = BaseMicroscopeApp([])
    
    app.add_hardware(ESP300AxisHW(app))
    
    app.exec_()
    
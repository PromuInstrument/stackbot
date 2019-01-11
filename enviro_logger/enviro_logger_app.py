from ScopeFoundry import BaseMicroscopeApp

class EnviroLoggerApp(BaseMicroscopeApp):
    
    name = 'enviro_logger'
    
    def setup(self):
        
        from accel_logger import AccelLogger
        self.add_measurement(AccelLogger(self))
        
        from magnetometer_logger import MagnetometerLogger
        self.add_measurement(MagnetometerLogger(self))
        
        
if __name__ == '__main__':
    
    app = EnviroLoggerApp()
    
    app.exec_()
        
from ScopeFoundry import BaseMicroscopeApp

class EnviroLoggerApp(BaseMicroscopeApp):
    
    name = 'enviro_logger'
    
    def setup(self):
        
        from power_spec_logger import PowerSpectrumLogger
        accel = self.add_measurement(PowerSpectrumLogger(self, name='accel_logger'))
        mag = self.add_measurement(PowerSpectrumLogger(self, name='mag_logger'))
        
    def setup_ui(self):
        mag = self.measurements['mag_logger']
        mag.settings['channel'] = '/Dev2/ai0:2'

        mag.settings['phys_unit'] = 'Gauss'
        mag.settings['scale'] = 0.2 # Gauss/V
        
        accel = self.measurements['accel_logger']
        accel.settings['channel'] = '/Dev2/ai3'
        accel.settings['phys_unit'] = 'g'
        accel.settings['scale'] = 1/0.494 # g/V
        accel.settings['IEPE_excitation'] = True
        
        accel.settings['log_freq_max'] = 4e3
        accel.settings['view_freq_max'] = 2e3
        
        
        #from magnetometer_logger import MagnetometerLogger
        #self.add_measurement(MagnetometerLogger(self))
        
        
if __name__ == '__main__':
    
    app = EnviroLoggerApp()
    
    app.exec_()
        
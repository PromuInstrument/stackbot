from ScopeFoundry import BaseMicroscopeApp

import logging
logging.basicConfig(level='DEBUG')
logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('traitlets').setLevel(logging.WARNING)

#logging.getLogger('ScopeFoundry.logged_quantity.LoggedQuantity').setLevel(logging.WARNING)

class PressureLogApp(BaseMicroscopeApp):
    '''
    stand alone app for pressure monitoring, now uses 9215A USB module for logging
    independent of x-series board
    '''
    name = 'PressureLogApp'
    
    def setup(self):
                 
        # Hardware Components
        from Auger.hardware.pfeiffer_turbo import TC110TurboHW
        self.add_hardware(TC110TurboHW(self))

        # Measurements
        from Auger.measurement.auger_pressure_history import AugerPressureHistory
        self.add_measurement_component(AugerPressureHistory(self))

        # Load default settings
        self.settings_load_ini('pressure_log_app_settings.ini')

        
        
if __name__ == '__main__':
    app = PressureLogApp([])
    app.exec_()

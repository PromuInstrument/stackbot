'''
Created on Jun 29, 2017

@author: Alan Buckley
'''

'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry.measurement import Measurement
import time


class PowermateMeasure(Measurement):

    name = "powermate_measure"

    def setup(self):
        """Loads UI into memory from file, connects **LoggedQuantities** to UI elements."""
        self.app
        
        self.dt = 0.05
        self.powermate = self.app.hardware['powermate_hw']
        self.powermate.settings.devices.add_listener(self.cycle)       

    def cycle(self):
        self.interrupt()
#         if self.interrupt_measurement_called:
#             self.start()
            
    def run(self):
        self.powermate.open_active_device()
        self.powermate.set_data_handler()
        try:
            while not self.interrupt_measurement_called:
                time.sleep(0.5)
        finally:
            self.powermate.active_device.close()

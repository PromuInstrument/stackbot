from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ni_daq.hw.ni_adc_hw import NI_ADC_HW
import time

class AnalogPressureGaugeHW(NI_ADC_HW):
    
    name = 'pressure_gauge'

    def setup(self):
        NI_ADC_HW.setup(self)

        pressure = self.settings.New('pressure', dtype=float, si=True, unit='Torr')
        
        pressure.connect_lq_math([self.settings.adc_val], self.pressure_calc)
    
    def pressure_calc(self, volts):
        return 10**(volts-5)
    
    def threaded_update(self):
        # t0 = time.time()
        self.settings.adc_val.read_from_hardware()
        #print(self.name, 'read time', time.time() - t0)
        time.sleep(0.100)
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.picoharp.hydraharp_hw import HydraHarpHW
from ScopeFoundryHW.picoharp.hydraharp_optimizer import HydraHarpOptimizerMeasure
from ScopeFoundryHW.picoharp.hydraharp_hist_measure import HydraHarpHistogramMeasure

class HydraHarpTestApp(BaseMicroscopeApp):
    
    name = 'hydraharp_test_app'
    
    def setup(self):
        
        self.add_hardware(HydraHarpHW(self))
        self.add_measurement(HydraHarpOptimizerMeasure(self))
        self.add_measurement(HydraHarpHistogramMeasure(self))

app = HydraHarpTestApp()
app.exec_()
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.oceanoptics_spec import OceanOpticsSpectrometerHW, OOSpecLive


class OOSpecTestApp(BaseMicroscopeApp):
    
    name = 'oospec_test_app'
    
    def setup(self):
        hw = self.add_hardware(OceanOpticsSpectrometerHW(self))
        #hw.settings['port'] = 'COM5'
        
        self.add_measurement(OOSpecLive(self))
                
if __name__ == '__main__':
    import sys
    app = OOSpecTestApp(sys.argv)
    app.exec_()
from ScopeFoundry import BaseMicroscopeApp
from thor_lsc_microscope.galvo_scanner import GalvoScannerHW
from thor_lsc_microscope.galvo_scanner_control import GalvoScannerControlMeasure


class ThorLSCMicroscopeApp(BaseMicroscopeApp):
    
    name='thor_lsc_app'
    
    def setup(self):
        self.add_hardware(GalvoScannerHW(self))
    
        self.add_measurement(GalvoScannerControlMeasure(self))
        
        
    
if __name__ =='__main__':
    import os
    for k,v in os.environ.items():
        print(k, '\t', v)
    
    app = ThorLSCMicroscopeApp([])
    
    app.exec_()
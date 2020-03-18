from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.sync_stream_scan.sync_stream_scan_image import SyncStreamScanImage


class SyncStreamTestAppImage(BaseMicroscopeApp):
    
    name = 'sync_stream_test'
    
    def setup(self):

        self.add_measurement(SyncStreamScanImage(self))
        
        
        
if __name__ == "__main__":
    #import cProfile
    #profile = cProfile.Profile()
    #profile.enable()
    app = SyncStreamTestAppImage([])
    app.exec_()
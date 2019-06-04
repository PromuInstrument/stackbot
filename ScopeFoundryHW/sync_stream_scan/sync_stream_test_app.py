from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.sync_stream_scan.sync_stream_scan import SyncStreamScan


class SyncStreamTestApp(BaseMicroscopeApp):
    
    name = 'sync_stream_test'
    
    def setup(self):

        self.add_measurement(SyncStreamScan(self))
        
        
        
if __name__ == "__main__":
    #import cProfile
    #profile = cProfile.Profile()
    #profile.enable()
    app = SyncStreamTestApp([])
    app.exec_()
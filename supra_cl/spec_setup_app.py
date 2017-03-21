from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
#from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

import logging
logging.basicConfig(level=logging.DEBUG)

class SpecApp(BaseMicroscopeApp):

    name = 'spec_app'
    
    def setup(self):
        
        from ScopeFoundryHW.andor_camera import AndorCCDHW
        self.add_hardware(AndorCCDHW(self))

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW)
                
        from ScopeFoundryHW.andor_camera import AndorCCDReadoutMeasure
        self.add_measurement(AndorCCDReadoutMeasure)
        
        from Auger.sem_sync_raster_hardware import SemSyncRasterDAQ
        self.add_hardware(SemSyncRasterDAQ(self))

        from Auger.sem_sync_raster_measure import SemSyncRasterScan
        self.add_measurement(SemSyncRasterScan(self))
        
        from supra_cl.sem_sync_raster_quad_measure import SemSyncRasterScanQuadView
        self.add_measurement(SemSyncRasterScanQuadView(self))



        

        self.settings_load_ini('supra_cl_defaults.ini')

        self.ui.show()

if __name__ == '__main__':
    import sys
    app = SpecApp(sys.argv)
    sys.exit(app.exec_())
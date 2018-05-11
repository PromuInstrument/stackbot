from ScopeFoundry import BaseMicroscopeApp
from collections import OrderedDict

class LaserScribeMicroscopeApp(BaseMicroscopeApp):

    name = "laser_scribe"

    def setup(self):

        from ScopeFoundryHW.ni_daq.hw.ni_digital_out import NIDigitalOutHW
        self.add_hardware(NIDigitalOutHW(self, name='shutter', line_names=['laser_shutter', '_', '_', '_', '_', '_', '_', '_']))

        

        from ScopeFoundryHW.pi_stage.pi_stage_hw import PIStage
        self.add_hardware(PIStage(self, name='pi_piezo_stage', 
                                  axes = OrderedDict([(1,'x'), (2,'y'), (3,'z')])))
        
        from laser_line_writer import LaserLineWriter
        self.add_measurement(LaserLineWriter(self))
        
        
        from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        self.add_hardware(ToupCamHW(self))
        from ScopeFoundryHW.toupcam.toupcam_live_measure import ToupCamLiveMeasure
        self.add_measurement(ToupCamLiveMeasure(self))
        

if __name__ == '__main__':
    import sys
    app = LaserScribeMicroscopeApp(sys.argv)
    sys.exit(app.exec_())
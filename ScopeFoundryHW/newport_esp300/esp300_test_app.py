from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.newport_esp300.esp300_xyz_control_measure import ESP300XYZStageControlMeasure

class ESP300TestApp(BaseMicroscopeApp):
    
    def setup(self):
        
        from esp300_xyz_stage_hw import ESP300XYZStageHW
        
        hw = self.add_hardware(ESP300XYZStageHW(self, ax_names='x__'))
        
        hw.settings['debug_mode'] = True
        hw.settings['port'] = 'COM4'
        
        self.add_measurement(ESP300XYZStageControlMeasure)

if __name__ == '__main__':
    import sys
    app = ESP300TestApp(sys.argv)
    sys.exit(app.exec_())
from ScopeFoundry.base_app import BaseMicroscopeApp

class ESP300TestApp(BaseMicroscopeApp):
    
    def setup(self):
        
        from esp300_xyz_stage_hw import ESP300XYZStageHW
        
        hw = self.add_hardware(ESP300XYZStageHW(self, ax_names='x__'))
        
        hw.settings['debug_mode'] = True
        hw.settings['port'] = 'COM4'

if __name__ == '__main__':
    import sys
    app = ESP300TestApp(sys.argv)
    sys.exit(app.exec_())
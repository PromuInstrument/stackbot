from ScopeFoundry import BaseMicroscopeApp


class CryoMicroscopeApp(BaseMicroscopeApp):

    name = 'cryo_microscope'
    
    def setup(self):
        
        
        from ScopeFoundryHW.andor_camera import AndorCCDHW, AndorCCDReadoutMeasure
        self.add_hardware(AndorCCDHW(self))
        self.add_measurement(AndorCCDReadoutMeasure)

        
        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))

if __name__ == '__main__':
    import sys
    app = CryoMicroscopeApp(sys.argv)
    sys.exit(app.exec_())
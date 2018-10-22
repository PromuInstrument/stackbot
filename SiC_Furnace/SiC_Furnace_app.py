from ScopeFoundry.base_app import BaseMicroscopeApp


class SiC_FurnaceApp(BaseMicroscopeApp):
    
    name = 'SiC_Furnace'
    
    def setup(self):
        
        from optris_pyrometer_hw import OptrisPyrometerHW
        self.add_hardware(OptrisPyrometerHW(self))
        
if __name__ == '__main__':
    import sys
    app = SiC_FurnaceApp(sys.argv)
    sys.exit(app.exec_())    
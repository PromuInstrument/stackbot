from ScopeFoundry import BaseMicroscopeApp


import logging
logging.basicConfig(level='DEBUG')
logging.getLogger('').setLevel(logging.DEBUG)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('traitlets').setLevel(logging.WARNING)

logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)


class SupraCLApp(BaseMicroscopeApp):
    
    name = 'supra_cl'
    
    def setup(self):
        
        # import pyqtgraph as pg
        #pg.setConfigOption('background', 'w')
        #pg.setConfigOption('foreground', 'k')

        
        from ScopeFoundryHW.sync_raster_daq import SyncRasterDAQ
        self.add_hardware(SyncRasterDAQ(self))

        from Auger.hardware.remcon32_hw import SEM_Remcon_HW
        self.add_hardware(SEM_Remcon_HW(self))
        
        from ScopeFoundryHW.sync_raster_daq import SyncRasterScan
        self.add_measurement(SyncRasterScan(self))
        
        from supra_cl.sync_raster_quad_measure import SyncRasterScanQuadView
        self.add_measurement(SyncRasterScanQuadView(self))
        
        from ScopeFoundryHW import andor_camera
        self.add_hardware(andor_camera.AndorCCDHW(self))
        self.add_measurement(andor_camera.AndorCCDReadoutMeasure(self))
        self.add_measurement(andor_camera.AndorCCDKineticMeasure(self))
        self.add_measurement(andor_camera.AndorSpecCalibMeasure(self))

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))
        
        from supra_cl.hyperspec_cl_measure import HyperSpecCLMeasure
        self.add_measurement(HyperSpecCLMeasure(self))
        
        from supra_cl.hyperspec_cl_quad_measure import HyperSpecCLQuadView
        self.add_measurement(HyperSpecCLQuadView(self))

        from ScopeFoundryHW.xbox_controller.xbcontrol_hc import XboxControlHW
        self.add_hardware(XboxControlHW(self))
        
        from ScopeFoundryHW.xbox_controller.xbcontrol_mc import XboxControlMeasure
        self.add_measurement(XboxControlMeasure(self))


        #self.hardware['xbox_controller'].settings.get_lq('connected').update_value(True)

        self.settings_load_ini('supra_cl_defaults.ini')

        self.ui.show()

        
if __name__ == '__main__':
    app = SupraCLApp([])
    app.exec_()

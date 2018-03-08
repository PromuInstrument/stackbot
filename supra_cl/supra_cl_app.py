from ScopeFoundry import BaseMicroscopeApp


import logging
# logging.basicConfig(level='DEBUG')
# logging.getLogger('').setLevel(logging.DEBUG)
# logging.getLogger("ipykernel").setLevel(logging.WARNING)
# logging.getLogger('PyQt4').setLevel(logging.WARNING)
# logging.getLogger('PyQt5').setLevel(logging.WARNING)
# logging.getLogger('traitlets').setLevel(logging.WARNING)
# 


class SupraCLApp(BaseMicroscopeApp):
    
    name = 'supra_cl'
    
    def setup(self):
        
        # import pyqtgraph as pg
        #pg.setConfigOption('background', 'w')
        #pg.setConfigOption('foreground', 'k')

#         from ScopeFoundryHW.xbox_controller.xbcontrol_hc import XboxControlHW
#         self.add_hardware(XboxControlHW(self))
#          
#         from ScopeFoundryHW.xbox_controller.xbcontrol_mc import XboxControlMeasure
#         self.add_measurement(XboxControlMeasure(self))

#         self.hardware['xbox_controller'].settings.get_lq('connected').update_value(True)

        
        ### SEM
        from ScopeFoundryHW.zeiss_sem.remcon32_hw import SEM_Remcon_HW
        self.add_hardware(SEM_Remcon_HW(self))

        from ScopeFoundryHW.zeiss_sem.sem_recipe_control import SEMRecipeControlMeasure
        self.add_measurement(SEMRecipeControlMeasure(self))
        
        from ScopeFoundryHW.zeiss_sem.stage_delta_control import SEMStageDeltaControl
        self.add_measurement(SEMStageDeltaControl(self))
        

        ######### CL Mirror
        from ScopeFoundryHW.attocube_ecc100 import AttoCubeXYZStageHW
        self.add_hardware(AttoCubeXYZStageHW(self, name='attocube_cl_xyz', ax_names='xyz'))
        self.add_hardware(AttoCubeXYZStageHW(self, name='attocube_cl_angle', ax_names=['o', 'pitch', 'yaw']))
        
        from supra_cl.cl_mirror_positioner.cl_mirror_hw import CLMirrorHW
        self.add_hardware(CLMirrorHW(self))
                
        from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        self.add_measurement(AttoCubeStageControlMeasure(self, name='attocube_cl_xyz', hw_name='attocube_cl_xyz'))
        self.add_measurement(AttoCubeStageControlMeasure(self,  name='attocube_cl_angle', hw_name='attocube_cl_angle'))
        
        from ScopeFoundryHW.attocube_ecc100.attocube_home_axis_measurement import AttoCubeHomeAxisMeasurement
        self.add_measurement(AttoCubeHomeAxisMeasurement(self))
        
        from supra_cl.cl_mirror_positioner.mirror_motion_measure import CLMirrorHomeAxesMeasure, CLMirrorParkMeasure, CLMirrorInsertMeasure
        self.add_measurement(CLMirrorHomeAxesMeasure(self))
        self.add_measurement(CLMirrorParkMeasure(self))
        self.add_measurement(CLMirrorInsertMeasure(self))
        
        from supra_cl.cl_mirror_positioner.mirror_position_measure import MirrorPositionMeasure
        self.add_measurement(MirrorPositionMeasure(self))

#         from supra_cl.cl_mirror_positioner.cl_mirror_remote_control import CLMirrorRemoteControlMeasure
#         self.add_measurement(CLMirrorRemoteControlMeasure)
        ######################


        ### Sync Raster
        from ScopeFoundryHW.sync_raster_daq import SyncRasterDAQ
        self.add_hardware(SyncRasterDAQ(self))

        from ScopeFoundryHW.sync_raster_daq import SyncRasterScan
        self.add_measurement(SyncRasterScan(self))
        
#         from supra_cl.sync_raster_quad_measure import SyncRasterScanQuadView
#         self.add_measurement(SyncRasterScanQuadView(self))


        
        #### Camera and Spectrometer
        from ScopeFoundryHW import andor_camera
        self.add_hardware(andor_camera.AndorCCDHW(self))
        self.add_measurement(andor_camera.AndorCCDReadoutMeasure(self))
        self.add_measurement(andor_camera.AndorCCDKineticMeasure(self))
        #self.add_measurement(andor_camera.AndorSpecCalibMeasure(self))

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))
        
        
        ### Hyperspec
        from supra_cl.hyperspec_cl_measure import HyperSpecCLMeasure
        self.add_measurement(HyperSpecCLMeasure(self))

        self.settings_load_ini('supra_cl_defaults.ini')
        
        from supra_cl.hyperspec_cl_quad_measure import HyperSpecCLQuadView
        self.add_measurement(HyperSpecCLQuadView(self))

        from supra_cl.cl_quad_measure import CLQuadView
        self.add_measurement(CLQuadView(self))

        self.settings_load_ini('supra_cl_defaults.ini')
        
        logging.getLogger('LoggedQuantity').setLevel(logging.DEBUG)


        
if __name__ == '__main__':
    app = SupraCLApp([])
    app.exec_()

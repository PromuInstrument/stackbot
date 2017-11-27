from ScopeFoundry.base_app import BaseMicroscopeApp
import logging
from supra_cl.mirror_stage.mirror_position_measure import MirrorPositionMeasure
from ScopeFoundryHW.attocube_ecc100.attocube_home_axis_measurement import AttoCubeHomeAxisMeasurement

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)
logging.getLogger('LoggedQuantity').setLevel(logging.WARN)

class MirrorStageApp(BaseMicroscopeApp):
    
    name="mirror_stage_app"
    
    def setup(self):
        from ScopeFoundryHW.attocube_ecc100 import AttoCubeXYZStageHW
        self.add_hardware(AttoCubeXYZStageHW(self, name='attocube_cl_xyz', ax_names='xyz'))
        self.add_hardware(AttoCubeXYZStageHW(self, name='attocube_cl_angle', ax_names=['o', 'pitch', 'yaw']))
        
        from supra_cl.mirror_stage.cl_mirror_hw import CLMirrorHW
        self.add_hardware(CLMirrorHW(self))
        
        
        self.hardware['attocube_cl_xyz'].settings['device_id'] = 94
        self.hardware['attocube_cl_angle'].settings['device_id'] = 199
        self.hardware['attocube_cl_xyz'].settings['connect_by'] = 'device_id'
        self.hardware['attocube_cl_angle'].settings['connect_by'] = 'device_id'
        
        from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        self.add_measurement(AttoCubeStageControlMeasure(self, name='attocube_cl_xyz', hw_name='attocube_cl_xyz'))
        self.add_measurement(AttoCubeStageControlMeasure(self,  name='attocube_cl_angle', hw_name='attocube_cl_angle'))
        
        
        self.add_measurement(AttoCubeHomeAxisMeasurement(self))
        
        from supra_cl.mirror_stage.mirror_motion_measure import CLMirrorHomeAxesMeasure, CLMirrorParkMeasure, CLMirrorInsertMeasure
        self.add_measurement(CLMirrorHomeAxesMeasure(self))
        self.add_measurement(CLMirrorParkMeasure(self))
        self.add_measurement(CLMirrorInsertMeasure(self))
        
        self.add_measurement(MirrorPositionMeasure(self))

        from supra_cl.mirror_stage.cl_mirror_remote_control import CLMirrorRemoteControlMeasure
        self.add_measurement(CLMirrorRemoteControlMeasure)

        #self.set_subwindow_mode()
        #self.tile_layout()
        
if __name__ == '__main__':
    import sys
    app = MirrorStageApp(sys.argv)
    sys.exit(app.exec_())    
        
"""
author Benedikt Ursprung
"""

from ScopeFoundryHW.xbox_controller.xbox_controller_base_measure import XboxBaseMeasure

class XboxControllerMeasure(XboxBaseMeasure):
    
    name = 'xbox_controller_measure'

    def setup(self):
        XboxBaseMeasure.setup(self)
        for ax in 'xyz':
            self.settings.New('{}_scale'.format(ax), dtype=float, initial=0.01, ro=False)
        self.stageHW = self.app.hardware['attocube_xyz_stage']
        self.set_specific_key_map()
        
    def set_specific_key_map(self):
        self.controller.settings.Axis_0.add_listener(lambda: self.move_stage(stage_axis='x', controller_axis = '0'))
        self.controller.settings.Axis_1.add_listener(lambda: self.move_stage(stage_axis='y', controller_axis = '1'))
        self.controller.settings.Axis_3.add_listener(lambda: self.move_stage(stage_axis='z', controller_axis = '3'))
    
    def move_stage(self, stage_axis, controller_axis):
        current_pos = self.stageHW.settings['{}_position'.format(stage_axis)]
        delta_pos = self.controller.settings['Axis_{}'.format(controller_axis)]*self.settings['{}_scale'.format(stage_axis)]
        target_pos = current_pos + delta_pos
        print(stage_axis,'move to target', target_pos)
        target_pos_lq = getattr(self.stageHW.settings, '{}_target_position'.format(stage_axis))
        target_pos_lq.update_value(target_pos)

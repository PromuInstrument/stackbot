"""
author Benedikt Ursprung
"""
import time
from ScopeFoundryHW.xbox_controller.xbox_controller_base_measure import XboxBaseMeasure

class XboxControllerMeasure(XboxBaseMeasure):
    
    name = 'xbox_controller_measure'

    def setup(self):
        XboxBaseMeasure.setup(self)
        
        for ax in 'xyz':
            self.settings.New('{}_scale'.format(ax), dtype=float, initial=0.1, ro=False)
        self.stageHW = self.app.hardware['attocube_xyz_stage']
        self.shutterHW = self.app.hardware['pololu_servo_hw']
        
        self.set_specific_key_map()
        
    def set_specific_key_map(self):
        self.controller.settings.Axis_0.add_listener(lambda: self.move_stage_cont(stage_axis='x', controller_axis = '0'))
        self.controller.settings.Axis_1.add_listener(lambda: self.move_stage_cont(stage_axis='y', controller_axis = '1'))
        self.controller.settings.Axis_3.add_listener(lambda: self.move_stage_cont(stage_axis='z', controller_axis = '3'))

        move_delta = 1
        self.controller.settings.E.add_listener(lambda: self.move_stage_delta(stage_axis='x', delta=move_delta))
        self.controller.settings.W.add_listener(lambda: self.move_stage_delta(stage_axis='x', delta=-move_delta))
        self.controller.settings.N.add_listener(lambda: self.move_stage_delta(stage_axis='y', delta=move_delta))
        self.controller.settings.S.add_listener(lambda: self.move_stage_delta(stage_axis='y', delta=-move_delta))        
        self.controller.settings.A.add_listener(lambda: self.move_stage_delta(stage_axis='z', delta=move_delta))
        self.controller.settings.B.add_listener(lambda: self.move_stage_delta(stage_axis='z', delta=-move_delta))
        
        #shutter
        self.controller.settings.Y.add_listener(self.toggle_shutter)
        
        
    def move_stage_cont(self, stage_axis, controller_axis):
        delta = self.controller.settings['Axis_{}'.format(controller_axis)]*self.settings['{}_scale'.format(stage_axis)]
        self.move_stage_delta(stage_axis,delta)
        time.sleep(0.1)
    
    def move_stage_delta(self, stage_axis, delta=1):
        self.stageHW.settings['{}_target_position'.format(stage_axis)] += 1.0*delta
        
    def toggle_shutter(self):
        servo_toggle = self.shutterHW.settings.servo2_toggle
        current_state = servo_toggle.val
        servo_toggle.update_value(not(current_state))
        
        
'''
    def move_stage_delta(self, stage_axis, delta=1):
        current_pos = self.stageHW.settings['{}_position'.format(stage_axis)]
        target_pos = current_pos + delta
        print(target_pos)
        target_pos_lq = getattr(self.stageHW.settings, '{}_target_position'.format(stage_axis))
        target_pos_lq.update_value(target_pos)
        
    def move_stage_cont_(self, stage_axis, controller_axis):
        current_pos = self.stageHW.settings['{}_position'.format(stage_axis)]
        delta_pos = self.controller.settings['Axis_{}'.format(controller_axis)]*self.settings['{}_scale'.format(stage_axis)]
        target_pos = current_pos + delta_pos
        target_pos_lq = getattr(self.stageHW.settings, '{}_target_position'.format(stage_axis))
        target_pos_lq.update_value(target_pos)
'''
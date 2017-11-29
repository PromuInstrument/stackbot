from ScopeFoundry.hardware import HardwareComponent
from collections import OrderedDict

class CLMirrorHW(HardwareComponent):
    
    name = 'cl_mirror'
    
    def setup(self):
        
        self.axes_hw = OrderedDict(
            [('x', 'attocube_cl_xyz'),
             ('y', 'attocube_cl_xyz'),
             ('z', 'attocube_cl_xyz'),
             ('pitch', 'attocube_cl_angle'),
             ('yaw', 'attocube_cl_angle'),
             ])
        
        for ax_name, hw_name in self.axes_hw.items():
            self.settings.Add(self.app.hardware[hw_name].settings.get_lq(ax_name + "_position"))

        for ax_name, hw_name in self.axes_hw.items():
            self.settings.New("park_" + ax_name, dtype=float, spinbox_decimals=6, ro=True)

        for ax_name, hw_name in self.axes_hw.items():
            self.settings.New("ref_" + ax_name, dtype=float, spinbox_decimals=6, ro=True)

        for ax_name, hw_name in self.axes_hw.items():
            self.settings.New("align_delta_" + ax_name, dtype=float, spinbox_decimals=6, ro=True)


        self.settings['park_x'] = - 4.5
        self.settings['park_y'] = -10.4
        self.settings['park_z'] = - 9.0
        self.settings['park_pitch'] = 0.0
        self.settings['park_yaw'] = 0.0
        
        
        self.settings['ref_x'] = +6.465000
        self.settings['ref_y'] = +6.895000
        self.settings['ref_z'] = -2.0
        self.settings['ref_pitch'] = 0.0
        self.settings['ref_yaw'] = 0.0
                        
        
        self.add_operation('Stop All Motion', self.stop_all_motion)
        
        self.auto_thread_lock = False
            
    def connect(self):
        self.hw_xyz = self.app.hardware['attocube_cl_xyz']
        self.hw_xyz.settings['connected'] = True
        self.hw_angle = self.app.hardware['attocube_cl_angle']
        self.hw_angle.settings['connected'] = True
        
        self.app.measurements['mirror_position'].settings['live'] = True
        

    def disconnect(self):
        self.app.measurements['mirror_position'].settings['live'] = False

        self.app.hardware['attocube_cl_xyz'].settings['connected'] = False
        self.app.hardware['attocube_cl_angle'].settings['connected'] = False
        
        
    def stop_all_motion(self):
        
        # stop all motion measurements
        self.app.measurements['cl_mirror_park'].interrupt()
        self.app.measurements['cl_mirror_insert'].interrupt()
        self.app.measurements['cl_mirror_home_axes'].interrupt()
        
        # turn off all axes open loop 
        self.hw_xyz.settings['x_enable_closedloop'] = False
        self.hw_xyz.settings['y_enable_closedloop'] = False
        self.hw_xyz.settings['z_enable_closedloop'] = False
        self.hw_angle.settings['pitch_enable_closedloop'] = False
        self.hw_angle.settings['yaw_enable_closedloop'] = False
    
        # turn off all axes continuous motion
        self.hw_xyz.settings['x_continuous_motion'] = 0
        self.hw_xyz.settings['y_continuous_motion'] = 0
        self.hw_xyz.settings['z_continuous_motion'] = 0
        self.hw_angle.settings['pitch_continuous_motion'] = 0
        self.hw_angle.settings['yaw_continuous_motion'] = 0
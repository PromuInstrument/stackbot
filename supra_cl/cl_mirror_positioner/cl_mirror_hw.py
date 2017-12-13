from ScopeFoundry.hardware import HardwareComponent
from collections import OrderedDict
import numpy as np

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
            self.settings.Add(self.app.hardware[hw_name].settings.get_lq(ax_name + "_target_position"))
            

        for ax_name, hw_name in self.axes_hw.items():
            self.settings.New("park_" + ax_name, dtype=float, spinbox_decimals=6, ro=True)

        for ax_name, hw_name in self.axes_hw.items():
            self.settings.New("ref_" + ax_name, dtype=float, spinbox_decimals=6, ro=True)

        S = self.settings
        for ax_name, hw_name in self.axes_hw.items():
            lq = self.settings.New("delta_" + ax_name +"_position", dtype=float, spinbox_decimals=6, ro=True)
            lq.connect_lq_math([S.get_lq('ref_'+ax_name), S.get_lq(ax_name + "_position")],
                               lambda ref, pos: pos - ref)
            lq = self.settings.New("delta_" + ax_name +"_target_position", dtype=float, spinbox_decimals=6, ro=True)
            lq.connect_lq_math([S.get_lq('ref_'+ax_name), S.get_lq(ax_name + "_target_position")],
                               lambda ref, pos: pos - ref)


        parked = self.settings.New('parked', dtype=bool, initial=False, ro=True)
        inserted = self.settings.New('inserted', dtype=bool, initial=False, ro=True)
        homed = self.settings.New('homed', dtype=bool, initial=False, ro=True)
        

        
        position_lqs = [ S.get_lq(ax_name + "_position") for ax_name in self.axes_hw.keys() ]
        park_lqs   = [ S.get_lq("park_" + ax_name) for ax_name in self.axes_hw.keys() ]
        ref_lqs   = [ S.get_lq("ref_" + ax_name) for ax_name in self.axes_hw.keys() ]

        
        def is_parked(x, y, z, pitch, yaw, park_x, park_y, park_z, park_pitch, park_yaw):
            park_tolerance = 10e-3 # in mm = 100um
            return (  (x - park_x)**2 
                    + (y - park_y)**2
                    + (z - park_z)**2
                    + (pitch - park_pitch)**2
                    + (yaw - park_yaw)**2 ) < park_tolerance**2

        parked.connect_lq_math( position_lqs + park_lqs, func=is_parked)

                    
        def is_inserted(x, y, z, pitch, yaw, ref_x, ref_y, ref_z, ref_pitch, ref_yaw):
            return (abs(x - ref_x) < 500e-3 and # mm
                    abs(y - ref_y) < 500e-3 and
                    -50e-3 < (z - ref_z) < 500e-3 and
                    abs(pitch - ref_pitch) <  0.01 and
                    abs(yaw - ref_yaw) < 0.01 )

        inserted.connect_lq_math( position_lqs + ref_lqs, func=is_inserted)

        ax_homed_lqs = [self.app.hardware[hw_name].settings.get_lq(ax_name + "_reference_found")
                         for ax_name, hw_name in self.axes_hw.items()]

        def is_homed(*vals):
            print("is_homed", vals, "-->", np.all(vals))
            return np.all(vals)

        homed.connect_lq_math(ax_homed_lqs, func=is_homed)
        homed.read_from_lq_math()

        self.settings['park_x'] = - 4.5
        self.settings['park_y'] = -10.4
        self.settings['park_z'] = - 6.0
        self.settings['park_pitch'] = 0.0
        self.settings['park_yaw'] = 0.0
        
        
        self.settings['ref_x'] = +6.110600
        self.settings['ref_y'] = +6.811600
        self.settings['ref_z'] = -3.2978
        self.settings['ref_pitch'] = 1.53
        self.settings['ref_yaw'] = 5.03
                        
        
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
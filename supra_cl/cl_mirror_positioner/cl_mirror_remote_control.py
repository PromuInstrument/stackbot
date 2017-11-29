from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class CLMirrorRemoteControlMeasure(Measurement):
    
    name = "cl_mirror_remote_control"
    
    def setup(self):
        
        self.ui_filename = sibling_path(__file__, 'cl_mirror_remote_control.ui')
        self.ui = load_qt_ui_file(self.ui_filename)
        
        self.settings.New("xy_step", dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        self.settings.New("z_step",  dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        
        self.settings.New("angle_step",  dtype=str, initial='0.10deg', choices=('0.01deg', '0.10deg', '1.00deg', 'Step'))

        
        hw_cl_mirror = self.app.hardware['cl_mirror']
        self.hw_xyz = self.app.hardware['attocube_cl_xyz']
        self.hw_angle = self.app.hardware['attocube_cl_angle']
        
        for ax in ['x', 'y','z', 'pitch', 'yaw']:
            widget = getattr(self.ui, ax + "_pos_doubleSpinBox")
            hw_cl_mirror.settings.get_lq(ax + "_position").connect_to_widget(widget)
            
        
        self.settings.xy_step.connect_to_widget(self.ui.xy_step_comboBox)
        self.settings.z_step.connect_to_widget(self.ui.z_step_comboBox)
        self.settings.angle_step.connect_to_widget(self.ui.angle_step_comboBox)
        
        
        for ax in ['x', 'y','z', 'pitch', 'yaw']:
            for direction in ['up', 'down']:
                button = getattr(self.ui, "{}_{}_pushButton".format(ax, direction))
                button.released.connect(lambda ax=ax, direction=direction: self.step_axis(ax, direction))
                
    def step_axis(self, ax, direction):
        print('step_axis', ax)
        if ax in 'xy':
            self.step_xy(ax, direction)
        elif ax == 'z':
            self.step_z(direction)
        elif ax in ['pitch', 'yaw']:
            self.step_angle(ax, direction)
        else:
            raise ValueError("unknown axis")


    def step_xy(self, ax, direction):
        
        step = self.settings['xy_step']
        
        int_dir = {'up':+1, 'down':-1}[direction]
        
        
        if step == "Step":
            self.hw_xyz.settings[ax + "_enable_closedloop"] = False
            # STEP
            self.hw_xyz.single_step(ax, int_dir)
        else:
            assert self.hw_xyz.settings[ax + "_enable_closedloop"]
            mm_step = {'1um':1e-3 , '10um': 10e-3, '100um': 100e-3}[step]
            self.hw_xyz.settings[ax + "_target_position"] += int_dir*mm_step
            
    def step_z(self, direction):
        
        ax = 'z'
        
        step = self.settings['z_step']
        int_dir = {'up':-1, 'down':+1}[direction] # NOTE FLIPPED so that up is towards objective / ceiling
        
        if step == "Step":
            self.hw_xyz.settings[ax + "_enable_closedloop"] = False
            # STEP
            self.hw_xyz.single_step(ax, int_dir)

        else:
            assert self.hw_xyz.settings[ax + "_enable_closedloop"]
            mm_step = {'1um':1e-3 , '10um': 10e-3, '100um': 100e-3}[step]
            self.hw_xyz.settings[ax + "_target_position"] += int_dir*mm_step
        
    def step_angle(self, ax, direction):
        
        step = self.settings['angle_step']
        
        int_dir = {'up':+1, 'down':-1}[direction]
        
        if step == "Step":
            self.hw_angle.settings[ax + "_enable_closedloop"] = False
            # STEP
            self.hw_angle.single_step(ax, int_dir)
        else:
            assert self.hw_angle.settings[ax + "_enable_closedloop"]
            deg_step = {'0.01deg':0.01 , '0.10deg': 0.1, '1.00deg': 1.0}[step]
            self.hw_angle.settings[ax + "_target_position"] += int_dir*deg_step
        

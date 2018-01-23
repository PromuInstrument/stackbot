from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from h5py.tests import old
from dask.tests.test_cache import flag

class CLMirrorRemoteControlMeasure(Measurement):
    
    name = "cl_position_remote_control"
    
    def setup(self):
        
        self.ui_filename = sibling_path(__file__, 'cl_position_remote_control.ui')
        self.ui = load_qt_ui_file(self.ui_filename)
        
        ########## CL Mirror
        self.settings.New("xy_step", dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        self.settings.New("z_step",  dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        
        self.settings.New("angle_step",  dtype=str, initial='0.02_deg', choices=('0.002_deg', '0.02_deg', '0.2_deg', 'Step'))

        
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
                
        ########## SEM Stage
        self.settings.New("sem_xy_step", dtype=str, unit='um', initial=1.0, choices=(1,10,100))
        self.settings.New("sem_z_step",  dtype=str, unit='um', initial=1.0, choices=(1,10,100))
        self.settings.New("sem_rot_step",  dtype=float, unit='deg', choices=(1,5,15))
        
        sem_hw = self.app.hardware['sem_remcon']
        
        sem_hw.settings.stage_x.connect_to_widget(self.ui.sem_x_pos_doubleSpinBox)
        sem_hw.settings.stage_y.connect_to_widget(self.ui.sem_y_pos_doubleSpinBox)
        sem_hw.settings.stage_z.connect_to_widget(self.ui.sem_z_pos_doubleSpinBox)
        
        for ax in ['x', 'y','z']:
            for direction in ['up', 'down']:
                button = getattr(self.ui, "sem_{}_{}_pushButton".format(ax, direction))
                button.released.connect(lambda ax=ax, direction=direction: self.sem_stage_delta_axis(ax, direction))

                
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
            deg_step = {'0.002_deg':0.002 , '0.02_deg': 0.02, '0.20_deg': 0.2}[step]
            self.hw_angle.settings[ax + "_target_position"] += int_dir*deg_step
            
    def sem_stage_delta_axis(self, ax, direction):
        
        Check if moving flag
        if moving flag: no op
        
        otherwise raise moving flag
        
        # verify 
        
        old_pos: dict(x=1, y=2)
        new_pos = copy of  old
        new_pos[ax] += delta
        
        # read current stage position
        
        # check tilt
        
        # fail if tilt !=0
        
        # move
        
        # wait till move is done
        # 
        
        finally:
            lower moving flag
            
        # is there a way to flush QT event queue? incase of a fast clicker

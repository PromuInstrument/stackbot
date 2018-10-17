from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,\
    groupbox_show_contents

class MirrorPositionMeasure(Measurement):
    
    name = "mirror_position"
    
    def setup(self):
        
        self.ui_filename = sibling_path(__file__, 'mirror_position_measure.ui')
        self.ui = load_qt_ui_file(self.ui_filename)


        red_green_checkbox_style_sheet = """
                QCheckBox::indicator::unchecked {
                    background-color: red;}
                QCheckBox::indicator::checked {
                    background-color: green;}"""
        
        self.ui.hw_groupBox.setStyleSheet(red_green_checkbox_style_sheet)
        self.ui.position_groupBox.setStyleSheet(red_green_checkbox_style_sheet)
        self.ui.motion_groupBox.setStyleSheet(red_green_checkbox_style_sheet)


        self.hw_cl_mirror = self.app.hardware['cl_mirror']
        self.hw_xyz   = self.app.hardware['attocube_cl_xyz']
        self.hw_angle = self.app.hardware['attocube_cl_angle']

        self.hw_cl_mirror.settings.connected.connect_to_widget(self.ui.hw_cl_mirror_connect_checkBox)
        self.hw_xyz.settings.connected.connect_to_widget(self.ui.hw_xyz_connect_checkBox)
        self.hw_angle.settings.connected.connect_to_widget(self.ui.hw_angle_connect_checkBox)

        self.hw_xyz.settings.x_position.connect_to_widget(self.ui.x_position_doubleSpinBox)
        self.hw_xyz.settings.y_position.connect_to_widget(self.ui.y_position_doubleSpinBox)
        self.hw_xyz.settings.z_position.connect_to_widget(self.ui.z_position_doubleSpinBox)
        self.hw_angle.settings.pitch_position.connect_to_widget(self.ui.pitch_position_doubleSpinBox)
        self.hw_angle.settings.yaw_position.connect_to_widget(self.ui.yaw_position_doubleSpinBox)
        
        self.hw_xyz.settings.x_target_position.connect_to_widget(self.ui.x_target_position_doubleSpinBox)
        self.hw_xyz.settings.y_target_position.connect_to_widget(self.ui.y_target_position_doubleSpinBox)
        self.hw_xyz.settings.z_target_position.connect_to_widget(self.ui.z_target_position_doubleSpinBox)
        self.hw_angle.settings.pitch_target_position.connect_to_widget(self.ui.pitch_target_position_doubleSpinBox)
        self.hw_angle.settings.yaw_target_position.connect_to_widget(self.ui.yaw_target_position_doubleSpinBox)

        for ax_name, hw_name in self.hw_cl_mirror.axes_hw.items():
            lq = self.hw_cl_mirror.settings.get_lq("delta_{}_position".format(ax_name))
            widget = getattr(self.ui, "delta_{}_position_doubleSpinBox".format(ax_name))
            lq.connect_to_widget(widget)

        for ax_name, hw_name in self.hw_cl_mirror.axes_hw.items():
            lq = self.hw_cl_mirror.settings.get_lq("delta_{}_target_position".format(ax_name))
            widget = getattr(self.ui, "delta_{}_target_position_doubleSpinBox".format(ax_name))
            lq.connect_to_widget(widget)


        self.hw_xyz.settings.x_reference_found.connect_to_widget(self.ui.x_home_checkBox)
        self.hw_xyz.settings.y_reference_found.connect_to_widget(self.ui.y_home_checkBox)
        self.hw_xyz.settings.z_reference_found.connect_to_widget(self.ui.z_home_checkBox)
        self.hw_angle.settings.pitch_reference_found.connect_to_widget(self.ui.pitch_home_checkBox)
        self.hw_angle.settings.yaw_reference_found.connect_to_widget(self.ui.yaw_home_checkBox)


        self.hw_xyz.settings.x_enable_closedloop.connect_to_widget(self.ui.x_closedloop_checkBox)
        self.hw_xyz.settings.y_enable_closedloop.connect_to_widget(self.ui.y_closedloop_checkBox)
        self.hw_xyz.settings.z_enable_closedloop.connect_to_widget(self.ui.z_closedloop_checkBox)
        self.hw_angle.settings.pitch_enable_closedloop.connect_to_widget(self.ui.pitch_closedloop_checkBox)
        self.hw_angle.settings.yaw_enable_closedloop.connect_to_widget(self.ui.yaw_closedloop_checkBox)



        #self.ui.read_current_position_pushButton.clicked.connect(self.read_current_position)
        self.ui.park_pushButton.clicked.connect(self.app.measurements['cl_mirror_park'].start)
        self.ui.insert_pushButton.clicked.connect(self.app.measurements['cl_mirror_insert'].start)
        self.ui.home_pushButton.clicked.connect(self.app.measurements['cl_mirror_home_axes'].start)
        
        self.ui.stop_pushButton.clicked.connect(self.app.hardware['cl_mirror'].stop_all_motion)
        
        self.settings.New("live", dtype=bool, initial=False)
        self.settings.live.connect_to_widget(self.ui.live_checkBox)
        self.settings.live.add_listener(self.set_livemode, argtype=(bool,))
        
        
        self.hw_cl_mirror.settings.parked.connect_to_widget(self.ui.parked_checkBox)
        self.hw_cl_mirror.settings.inserted.connect_to_widget(self.ui.inserted_checkBox)
        self.hw_cl_mirror.settings.homed.connect_to_widget(self.ui.homed_checkBox)
        
        adv_ctrl = self.settings.New('advanced_controls', dtype=bool, initial=False)
        
        adv_ctrl.connect_to_widget(self.ui.enable_advanced_controls_checkBox)
        adv_ctrl.add_listener(self.on_adv_ctrl)
        
        ############### Remote Control / Joystick
        self.settings.New("xy_step", dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        self.settings.New("z_step",  dtype=str, initial='10um', choices=('1um', '10um', '100um', 'Step'))
        
        self.settings.New("angle_step",  dtype=str, initial='0.02_deg', choices=('0.002_deg', '0.020_deg', '0.200_deg', 'Step'))

        
        hw_cl_mirror = self.app.hardware['cl_mirror']
        self.hw_xyz = self.app.hardware['attocube_cl_xyz']
        self.hw_angle = self.app.hardware['attocube_cl_angle']
        
        for ax in ['x', 'y','z', 'pitch', 'yaw']:
            widget = getattr(self.ui, ax + "_pos_doubleSpinBox")
            hw_cl_mirror.settings.get_lq("delta_" + ax + "_position").connect_to_widget(widget)
            widget.setDecimals(2)
            
        
        self.settings.xy_step.connect_to_widget(self.ui.xy_step_comboBox)
        self.settings.z_step.connect_to_widget(self.ui.z_step_comboBox)
        self.settings.angle_step.connect_to_widget(self.ui.angle_step_comboBox)
        
        
        for ax in ['x', 'y','z', 'pitch', 'yaw']:
            for direction in ['up', 'down']:
                button = getattr(self.ui, "{}_{}_pushButton".format(ax, direction))
                button.released.connect(lambda ax=ax, direction=direction: self.step_axis(ax, direction))
        
        
        #### Hideable sections
        self.ui.advanced_groupBox.toggled.connect(
            lambda show, gb=self.ui.advanced_groupBox:
                groupbox_show_contents(gb, show))

        self.ui.joystick_groupBox.toggled.connect(
            lambda show, gb=self.ui.joystick_groupBox:
                groupbox_show_contents(gb, show))


        
        
        
    def read_current_position(self):
        self.hw_xyz.read_from_hardware()
        self.hw_angle.read_from_hardware()
        
    def set_livemode(self, live):
        
        if live:
            self.app.measurements['attocube_cl_xyz'].start()
            self.app.measurements['attocube_cl_angle'].start()
        else:
            self.app.measurements['attocube_cl_xyz'].interrupt()
            self.app.measurements['attocube_cl_angle'].interrupt()

    def on_adv_ctrl(self):
        state = self.settings['advanced_controls']
        self.ui.delta_position_groupBox.setEnabled(state)
        self.ui.position_groupBox.setEnabled(state)

    #### Remote Control Methods
    
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
        
        # NOTE FLIPPED so that arrows match with SEM picture at 90deg scan rotation
        # Changed 2018-10-15
        int_dir = {'up':-1, 'down':+1}[direction] 
        
        
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
            deg_step = {'0.002_deg':0.002 , '0.020_deg': 0.02, '0.200_deg': 0.2}[step]
            self.hw_angle.settings[ax + "_target_position"] += int_dir*deg_step
        

        
        
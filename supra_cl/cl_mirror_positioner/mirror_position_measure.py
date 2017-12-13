from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


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



            
        
        
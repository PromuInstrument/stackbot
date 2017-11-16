from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class MirrorPositionMeasure(Measurement):
    
    name = "mirror_position"
    
    def setup(self):
        
        self.ui_filename = sibling_path(__file__, 'mirror_position_measure.ui')
        self.ui = load_qt_ui_file(self.ui_filename)


        self.hw_xyz   = self.app.hardware['attocube_cl_xyz']
        self.hw_angle = self.app.hardware['attocube_cl_angle']

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

        self.ui.read_current_position_pushButton.clicked.connect(self.read_current_position)
        
        self.settings.New("live", dtype=bool, initial=False)
        self.settings.live.connect_to_widget(self.ui.live_checkBox)
        self.settings.live.add_listener(self.set_livemode, argtype=(bool,))
        
        
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

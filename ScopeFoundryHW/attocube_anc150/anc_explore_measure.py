from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time
from qtpy import QtWidgets

class ANC_RemoteMeasure(Measurement):
    
    name = 'anc_remote'
    
    def setup(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, 'anc_remote.ui'))
        
        self.settings.New('steps_xy', initial=10,vmin=1,vmax=500)
        self.settings.New('x_pos', dtype=int, ro=True)
        self.settings.New('y_pos', dtype=int, ro=True)
        
        self.settings.New('steps_pitchyaw', initial=10,vmin=1,vmax=500)
        self.settings.New('pitch_pos', dtype=int, ro=True)
        self.settings.New('yaw_pos', dtype=int, ro=True)
        
        for lq_name in ['steps_xy', 'x_pos', 'y_pos',
                        'steps_pitchyaw', 'pitch_pos', 'yaw_pos']:
            
            self.settings.get_lq(lq_name).connect_to_widget(
                getattr(self.ui, lq_name + '_doubleSpinBox'))
        
        self.anc_hw = self.app.hardware['anc150']
        
        for axis_name in ['x', 'y', 'pitch', 'yaw']:
            for direction in ['up', 'down']:
                button = getattr(self.ui, "{}_{}_pushButton".format(axis_name, direction))
                func = getattr(self, "move_{}_{}".format(axis_name, direction))
                button.clicked.connect(func)
                
        self.anc_hw.settings.position.add_listener(self.on_new_positions)
        self.anc_hw.settings['connected'] = True
        time.sleep(1.7)
        if not self.anc_hw.connect_success:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(
            """
            Failed to connect to ANC150, Make sure it is turned on 
            and all channels switched to CCON mode.
            Check terminal for detailed error message.
            """)
            msgbox.show()
                  
    def move_x_up(self):
        self.anc_hw.move_axis_delta_by_name('x', self.settings['steps_xy'])
        
    def move_x_down(self):
        self.anc_hw.move_axis_delta_by_name('x', -self.settings['steps_xy'])
        
    def move_y_up(self):
        self.anc_hw.move_axis_delta_by_name('y', self.settings['steps_xy'])
        
    def move_y_down(self):
        self.anc_hw.move_axis_delta_by_name('y', -self.settings['steps_xy'])
        
    def move_pitch_up(self):
        self.anc_hw.move_axis_delta_by_name('pitch', self.settings['steps_pitchyaw'])
        
    def move_pitch_down(self):
        self.anc_hw.move_axis_delta_by_name('pitch', -self.settings['steps_pitchyaw'])

    def move_yaw_up(self):
        self.anc_hw.move_axis_delta_by_name('yaw', self.settings['steps_pitchyaw'])

    def move_yaw_down(self):
        self.anc_hw.move_axis_delta_by_name('yaw', -self.settings['steps_pitchyaw'])

    def on_new_positions(self):
        for axis_name in ['x', 'y', 'pitch', 'yaw']:
            self.settings[axis_name + '_pos'] = self.anc_hw.get_pos_by_name(axis_name)

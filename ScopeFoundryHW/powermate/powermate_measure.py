'''
Created on Jun 29, 2017

@author: Alan Buckley, Benedikt Ursprung, Edward Barnard
'''


from ScopeFoundry.measurement import Measurement
import time

class PowermateMeasure(Measurement):
    name = 'powermate_measure'

    def setup(self):
        self.powermate = self.app.hardware['powermate_hw']
        self.n_devs = 2
                
        self.dt = 0.05
        
        choices = ['hardware/attocube_xyz_stage/z_target_position',
                   'hardware/attocube_xyz_stage/x_target_position',
                   'hardware/attocube_xyz_stage/y_target_position',
                   '',
                   ]
        
        for channel in range(self.n_devs):
            self.settings.New(name='dev_{}_lq_path_moved'.format(channel), dtype=str, 
                              initial=choices[channel], choices = choices)
            self.settings.New(name='dev_{}_lq_path_toggle'.format(channel), dtype=str, initial='')
            self.settings.New(name='dev_{}_moved_released'.format(channel),initial=0.001, dtype=float, ro=False)
            self.settings.New(name='dev_{}_moved_pressed'.format(channel), initial=0.1, dtype=float, ro=False)
        
        self.connect_pm_signals_to_lqs()
        
    def disconnect_pm_signals_from_lqs(self):
        """"disconnect all signals"""
        for signal_name in ['moved', 'button_pressed', 'button_released', 'moved_left', 'moved_right']:
            try:
                signal = getattr(self.powermate, signal_name)
                signal.disconnect()
            except TypeError:
                pass

    def connect_pm_signals_to_lqs(self):
        self.powermate.moved.connect(self.increment_on_moved)
    
    # callback functions
    def increment_on_moved(self, channel, direction, button ):
        """callback_function: increments lq_path_moved by moved_released or moved_pressed"""
        lq_path = self.settings['dev_{}_lq_path_moved'.format(channel)]
        lq = self.app.lq_path(lq_path)
        old_val = lq.val
        if button:
            delta = self.settings['dev_{}_moved_pressed'.format(channel)]
        else:
            delta = self.settings['dev_{}_moved_released'.format(channel)]
        new_val = old_val + delta*direction
        lq.update_value(new_val)
    
    def toggle_on_button_pressed(self, channel):
        """callback_function: toggles the state of lq_path_press, UNTESTED"""
        lq_path = self.settings['dev_{}_lq_path_toggle'.format(channel)]
        lq = self.app.lq_path(lq_path)
        old_state = lq.val
        assert type(lq.val) == bool
        lq.update_value(not old_state)

    def run(self):
        try:
            self.connect_pm_signals_to_lqs()
            while not self.interrupt_measurement_called:
                time.sleep(0.1)
        finally:
            self.disconnect_pm_signals_from_lqs()
            
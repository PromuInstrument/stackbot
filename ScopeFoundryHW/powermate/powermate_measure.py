'''
Created on Jun 29, 2017

@author: Alan Buckley, Benedikt Ursprung, Edward Barnard
'''


from ScopeFoundry.measurement import Measurement
import time

choices = ['hardware/attocube_xyz_stage/z_target_position',
                   'hardware/attocube_xyz_stage/x_target_position',
                   'hardware/attocube_xyz_stage/y_target_position',
                   '',
                   ]

class PowermateMeasure(Measurement):
    name = 'powermate_measure'
    
    def __init__(self, app, name=None, n_devs=2, dev_lq_choices=choices):
        self.n_devs = n_devs
        self.dev_lq_choices=dev_lq_choices
        Measurement.__init__(self, app, name=name)

    def setup(self):
        self.powermate = self.app.hardware['powermate']
                
        self.dt = 0.05
        
        
        self.fine = self.settings.New(name = 'fine', dtype=bool, initial=False)
        
        choices=self.dev_lq_choices
        
        for channel in range(self.n_devs):
            self.settings.New(name='dev_{}_lq_path_moved'.format(channel), dtype=str, 
                              initial=choices[channel], choices = choices)
            self.settings.New(name='dev_{}_lq_path_toggle'.format(channel), dtype=str, initial='')
            self.settings.New(name='dev_{}_moved_released'.format(channel),initial=0.001, dtype=float, ro=False, spinbox_decimals=6)
            self.settings.New(name='dev_{}_moved_pressed'.format(channel), initial=0.1, dtype=float, ro=False, spinbox_decimals=6)
        
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
        
        if self.fine.val:
            new_val = old_val + delta*direction/4.0
        else:
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
            
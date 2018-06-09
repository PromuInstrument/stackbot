'''
Created on May 25, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from ScopeFoundryHW.ALD.ALD_recipes.log.ALD_sqlite import ALD_sqlite
import numpy as np
import time

class ALD_Recipe(Measurement):
    
    name = 'ALD_Recipe'
    
    def setup(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.mks600 = self.app.hardware['mks_600_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
    

    
        self.settings.New('cycles', dtype=int, initial=1, ro=False, vmin=1)
        self.settings.New('time', dtype=float, array=True, initial=[[0.3, 0.07, 2.5, 5, 0.3, 0.3, 0]], fmt='%1.3f', ro=False)

        
        self.settings.New('t3_method', dtype=str, initial='Shutter', ro=False, choices=(('PV'), ('Shutter')))
        self.settings.New('recipe_completed', dtype=bool, initial=False, ro=True)
        self.settings.New('cycles_completed', dtype=int, initial=0, ro=True)
    
        self.MFC_valve_states = {'Open': 'O',
                             'Closed': 'C',
                             'Manual': 'N'}
    
        if hasattr(self.app.hardware, 'ald_shutter'):
            self.shutter = self.app.hardware.ald_shutter
        else:
            print('Connect ALD shutter HW component first.')

        self.params_loaded = False
        
                    
    def load_times(self):
        self.times = self.settings['time']
    

    def connect_db(self):
        self.db = ALD_sqlite()
        self.db.connect()
        self.db.setup_table()
        self.db.setup_index()
        
    def db_poll(self):
        pass
    
    def load_params_module(self):
        if hasattr(self.app.measurements, 'ALD_params'):
            self.params = self.app.measurements.ALD_params
            self.params_loaded = True
            print("Params loaded:", self.params_loaded)
        # Sometimes.. :0
        self.settings.cycles.add_listener(self.sum_times)
        self.settings.time.add_listener(self.sum_times)
    
    def sum_times(self):
        if not self.params_loaded:
            self.load_params_module()
            
        prepurge = self.settings['time'][0][0]
        cycles = self.settings['cycles']
        total_loop_time = cycles*np.sum(self.settings['time'][0][1:5])
        print(total_loop_time)
        postpurge = self.settings['time'][0][5]
        sum_value = prepurge + total_loop_time + postpurge
        self.settings['time'][0][6] = sum_value
        if self.params_loaded:
            self.params.update_table()
    
    def plasma_dose(self, width, power):
        """Argument 'width' has units of seconds
        power has units of Watts
        """
        print('Start plasma dose.')
        self.seren.write_fp(power)
        self.seren.RF_toggle(True)
        time.sleep(width)
        self.seren.RF_toggle(False)
        self.seren.write_fp(0)
        print('Plasma dose finished.')
        
    def valve_pulse(self, channel, width):
        print('Valve pulse', width)
        assert channel in [1,2]
        self.relay.settings['pulse_width{}'.format(channel)] = 1e3*width
        width = self.relay.settings['pulse_width{}'.format(channel)]
        getattr(self.relay, 'write_pulse{}'.format(channel))(width)
    
    def purge(self, width):
        print('Purge', width)
        time.sleep(width)    
    
    def shutter_pulse(self, width):
        self.shutter.settings['shutter_open'] = True
        print('Shutter open')
        time.sleep(width)
        self.shutter.settings['shutter_open'] = False
        print('Shutter closed')
        
    def load_single_recipe(self):
        self.load_times()
        self.routine()
    
    def routine(self):
        _, t1, t2, t3, t4, _, _  = self.times[0]
        self.valve_pulse(1, t1)
        self.purge(t2)
        mode = self.settings['t3_method'] 
        if mode == 'Shutter':
            self.shutter_pulse(t3)
        elif mode == 'PV':
            self.valve_pulse(2, t3)
        self.purge(t4)
        
    
    def prepurge(self):
        width = self.times[0][0]
        print('Prepurge', width)
        time.sleep(width)
    
    def postpurge(self):
        print(self.times, self.times[0])
        width = self.times[0][5]
        print('Postpurge', width)
        time.sleep(width)
        
    def shutdown(self):
        print('Shutdown initiated.')
        self.ramp_throttle_open()
        if self.shutdown_ready:
            state = self.MFC_valve_states['Closed']
            self.mks146.settings['set_MFC0_valve'] = state
    

    
    def ramp_throttle_open(self):
        print('Ramping down.')
        self.shutdown_ready = False
        while self.shutdown_ready == False:
            pressure = self.vgc.settings['ch2_pressure_scaled']
            if pressure < 1e-2:
                self.mks600.settings['sp_channel'] = 'B'
                self.mks600.write_sp(0.0002)
                time.sleep(10)
                self.mks600.write_sp(0.0001)
                time.sleep(20)
                self.mks600.settings['sp_channel']= 'Open'
                self.shutdown_ready = True
                print('Shutdown ready')
            else:
                print('Disable pump before equalizing chamber pressures. Don\'t dump that pump!')
    
    def run_recipe(self):
        self.settings['recipe_completed'] = False
        self.settings['cycles_completed'] = 0
        cycles = self.settings['cycles']    
        self.times = self.settings['time']
        self.prepurge()
        for _ in range(cycles):
            self.routine()
            self.settings['cycles_completed'] += 1
            if self.interrupt_measurement_called:
                break
        self.postpurge()
        self.settings['recipe_completed'] = True

    def run(self):
        """LQ logging to db can occur here."""
        pass
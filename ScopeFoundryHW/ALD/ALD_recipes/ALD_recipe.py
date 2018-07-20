'''
Created on May 25, 2018

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from threading import Lock
import numpy as np
import datetime
import time
import csv
import os

class ALD_Recipe(Measurement):
    
    name = 'ALD_Recipe'
    
    MFC_valve_states = {'Open': 'O',
                         'Closed': 'C',
                         'Manual': 'N'}
    
    header = ['Time', 'Cycles Completed', 'Steps Taken', 'Step Name', 'Shutter Open', \
                       'PV1', 'PV2', 'CM Gauge (Torr)', 'Pirani Gauge (Torr)', 'Manometer (Torr)', \
                       'Valve Position (%)', 'Set Forward Power (W)', 'Read Forward Power (W)', \
                       'Reflected Power (W)', 'MFC Flow Rate (sccm)', 'SV Setpoint (C)', \
                       'PV Temperature (C)', 'Proportional', 'Integral', 'Derivative']
    
    def setup(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.shutter = self.app.hardware['ald_shutter']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.mks600 = self.app.hardware['mks_600_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
        if hasattr(self.app.hardware, 'ald_shutter'):
            self.shutter = self.app.hardware.ald_shutter
        else:
            print('Connect ALD shutter HW component first.')
        
        self.lock = Lock()
    
        self.PV_default_time = 1.
        self.default_times = [[0.3, 0.07, 2.5, 5, 0.3, 0.3, 0]]
        self.default_subroutine = [[3., 0.02, 1.]]
        self.settings.New('cycles', dtype=int, initial=1, ro=False, vmin=1)
        self.settings.New('time', dtype=float, array=True, initial=self.default_times, fmt='%1.3f', ro=False)
        self.settings.New('subroutine', dtype=float, array=True, initial=self.default_subroutine, fmt='%1.3f', ro=False)

        self.settings.New('PV1', dtype=int, initial=0, ro=True)
        self.settings.New('PV2', dtype=int, initial=0, ro=True)
        
        self.settings.New('t3_method', dtype=str, initial='Shutter', ro=False, choices=(('PV'), ('Shutter'),('PV/Purge')))
        self.settings.New('cycles_completed', dtype=int, initial=0, ro=True)
        self.settings.New('step', dtype=int, initial=0, ro=True)
        self.settings.New('steps_taken', dtype=int, initial=0, ro=True)

        self.create_indicator_lq_battery()
        
        self.settings.New('csv_save_path', dtype=str, initial='', ro=False)
        self.save_path_update()

        self.predep_complete = None
        self.dep_complete = None

        self.display_loaded = False

    
    def create_indicator_lq_battery(self):
        self.settings.New('pumping', dtype=bool, initial=False, ro=True)
        self.settings.New('predeposition', dtype=bool, initial=False, ro=True)
        self.settings.New('deposition', dtype=bool, initial=False, ro=True)
        self.settings.New('vent', dtype=bool, initial=False, ro=True)
        self.settings.New('pumped', dtype=bool, initial=False, ro=True)
        self.settings.New('gases_ready', dtype=bool, initial=False, ro=True)
        self.settings.New('substrate_hot', dtype=bool, initial=False, ro=True)
        self.settings.New('recipe_running', dtype=bool, initial=False, ro=True)
        self.settings.New('recipe_completed', dtype=bool, initial=False, ro=True)
     
    
    def save_path_update(self):
        home = os.path.expanduser("~")
        self.path = home+'\\Desktop\\'
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")+'.csv'
        self.full_file_path = self.path+filename
        self.settings['csv_save_path'] = self.full_file_path
        self.firstopened = True

        
    def db_poll(self, step='Placeholder'):
        entries = []
        entries.append(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        entries.append(self.settings['cycles_completed'])
        entries.append(self.settings['steps_taken'])
        entries.append(step)
        entries.append(int(self.shutter.settings['shutter_open']))
        entries.append(self.settings['PV1'])
        entries.append(self.settings['PV2'])
        entries.append(self.vgc.settings['ch3_pressure_scaled'])
        entries.append(self.vgc.settings['ch2_pressure_scaled'])
        entries.append(self.mks600.settings['pressure'])
        entries.append(self.mks600.settings['read_valve_position'])
        entries.append(self.seren.settings['set_forward_power'])
        entries.append(self.seren.settings['forward_power_readout'])
        entries.append(self.seren.settings['reflected_power'])
        entries.append(self.mks146.settings['MFC0_flow'])
        entries.append(self.lovebox.settings['sv_setpoint'])
        entries.append(self.lovebox.settings['pv_temp'])
        entries.append(self.lovebox.settings['Proportional_band'])
        entries.append(self.lovebox.settings['Integral_time'])
        entries.append(self.lovebox.settings['Derivative_time'])
        if self.firstopened == True:
            self.new_csv(entries)
        else:
            self.add_to_csv(entries)

    
    def new_csv(self, entry):
        self.save_path_update()
        file = self.settings['csv_save_path']
        with open(file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(self.header)
            writer.writerow(entry)
        self.firstopened = False
    
    def add_to_csv(self, entry):
        file = self.settings['csv_save_path']
        with open(file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(entry)
    
    def load_display_module(self):
        print('load_display')
        if hasattr(self.app.measurements, 'ALD_display'):
            self.display = self.app.measurements.ALD_display
            self.display_loaded = True
            print("Display loaded:", self.display_loaded)
            # Sometimes.. :0
            self.settings.cycles.add_listener(self.sum_times)
            self.settings.time.add_listener(self.sum_times)
            self.settings.subroutine.add_listener(self.sum_times)
            self.settings.t3_method.add_listener(self.t3_update)
        
    def t3_update(self):
        method = self.settings['t3_method']
        if method == 'PV':
            result = self.PV_default_time
        elif method == 'Shutter':
            result = self.default_times[0][3]
        elif method == 'PV/Purge':
            result = self.subroutine_sum()
            
        self.settings['time'][0][3] = result
        self.display.update_table()
    
    def subroutine_sum(self):
        data = self.settings['subroutine'][0]
        coeff = int(data[0])
        entries = data[1:]
        self.settings['subroutine'][0][0] = coeff
        self.display.update_subtable()

        return coeff*np.sum(entries)
    
    def sum_times(self):
        """Sometimes... :0"""
        if self.settings['t3_method'] == 'PV/Purge':
            self.settings['time'][0][3] = self.subroutine_sum()
        prepurge = self.settings['time'][0][0]
        cycles = self.settings['cycles']
        total_loop_time = cycles*np.sum(self.settings['time'][0][1:5])
        print(total_loop_time)
        postpurge = self.settings['time'][0][5]
        sum_value = prepurge + total_loop_time + postpurge
        self.settings['time'][0][6] = sum_value
        if self.display_loaded:
            self.display.update_table()



    def set_precursor(self):
        '''
            .7 < Argon MFC < 2 sccm
                    +
            X=Ar pressure < channel 3 pressure < Y=1
        '''
        pass

    def plasma_dose(self, width, power):
        """
        Turn on RF source for duration of time, 'width'
        Argument 'width' has units of seconds
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
        """Open one of the pulse valves for specified duration of time, 'width'
        Argument 'width' has units of seconds
        """
        print('Valve pulse', width)
        step_name = 'Valve Pulse'
        assert channel in [1,2]
        self.relay.settings['pulse_width{}'.format(channel)] = 1e3*width
        getattr(self.relay, 'write_pulse{}'.format(channel))(width)
        self.settings['PV{}'.format(channel)] = 1
        t0 = time.time()
        t_lastlog = t0
        while True:
            if self.interrupt_measurement_called:
                self.settings['PV{}'.format(channel)] = 0 
                break
            if time.time()-t0 > width:
                self.settings['PV{}'.format(channel)] = 0
                break
            time.sleep(0.001)
            if time.time() - t_lastlog > 0.005:
                # do some logging
                self.db_poll(step_name)
                t_lastlog = time.time()
        self.settings['steps_taken'] += 1
    
    def purge(self, width):
        """Duration of time for system to wait in order to allow for the purge of gases"""
        print('Purge', width)
        step_name = 'Purge'
        t0 = time.time()
        t_lastlog = t0
        while True:
            if self.interrupt_measurement_called:
                self.shutoff()
                break
            if time.time()-t0 > width:
                break
            time.sleep(0.001)
            if time.time() - t_lastlog > 0.2:
                # do some logging
                self.db_poll(step_name)
                t_lastlog = time.time()
        self.settings['steps_taken'] += 1
    
    def shutter_pulse(self, width):
        """Actuate (open, then close) shutter over interval 'width' """
        step_name = 'Shutter Pulse'
        self.shutter.settings['shutter_open'] = True
        self.db_poll(step_name)
        print('Shutter open')
        t0 = time.time()
        t_lastlog = t0
        while True:
            if self.interrupt_measurement_called:
                self.shutter.settings['shutter_open'] = False
                break
            if time.time()-t0 > width:
                break
            time.sleep(0.001)
            if time.time() - t_lastlog > 0.2:
                # do some logging
                self.db_poll(step_name)
                t_lastlog = time.time()
            
        self.shutter.settings['shutter_open'] = False
        self.settings['steps_taken'] += 1
        print('Shutter closed')

    def shutoff(self):
        self.display.ui_initial_defaults()
        self.settings['recipe_running'] = False

    
    def predeposition(self):
        """Sets MFC to manual open, sets flow to 0.7 sccm"""
        self.predep_complete = False
        status = self.mks146.settings['read_MFC0_valve']
        if status == 'O' or status == 'C':
            self.mks146.settings['set_MFC0_valve'] = 'N'
            time.sleep(1)
        self.mks146.settings['set_MFC0_SP'] = 0.7
        self.predep_complete = True
        
    def prepurge(self):
        width = self.times[0][0]
        step_name = 'Pre-purge'
        print('Prepurge', width)
        self.db_poll(step_name)
        time.sleep(width)
        self.settings['steps_taken'] += 1
    
    def routine(self):
        """This function carries out the looped part of our ALD routine.
        """
        # Read in time table data
        sub_cyc, sub_t0, sub_t1 = self.sub[0]
        _, t1, t2, t3, t4, _, _  = self.times[0]
        
        # Carry out routine
        self.valve_pulse(1, t1)
        if self.interrupt_measurement_called:
            self.shutoff()
            return
            #doo something to finish routine
        self.purge(t2)
        if self.interrupt_measurement_called:
            self.shutoff()
            return
            #doo something to finish routine
        
        ## Check selected method for t3 in main recipe table,
        ## Carry out an operation based on the selection
        mode = self.settings['t3_method'] 
        if mode == 'Shutter':
            self.shutter_pulse(t3)
            if self.interrupt_measurement_called:
                self.shutoff()
                return
                #doo something to finish routine
        elif mode == 'PV':
            self.valve_pulse(2, t3)
            if self.interrupt_measurement_called:
                self.shutoff()
                return
                #doo something to finish routine
        elif mode == 'PV/Pulse':
            '''Run sub_cyc number of subroutine cycles.
            Subroutine consists of a valve pulse and a purge period.'''
            for _ in range(sub_cyc):
                self.valve_pulse(2, sub_t0)
                self.purge(sub_t1)
        
        self.purge(t4)
        if self.interrupt_measurement_called:
            self.shutoff()
            return
            #doo something to finish routine
        
    
    def postpurge(self):
        step_name = 'Post-purge'
        print(self.times, self.times[0])
        width = self.times[0][5]
        print('Postpurge', width)
        self.db_poll(step_name)
        time.sleep(width)
        self.settings['steps_taken'] += 1
        
    def deposition(self):
        self.dep_complete = False
        cycles = self.settings['cycles']    
        for _ in range(cycles):
            self.routine()
            if self.interrupt_measurement_called:
                self.shutoff()
                break
                #doo something to finish routine
            
            self.settings['cycles_completed'] += 1
            print(self.settings['cycles_completed'])
            if self.interrupt_measurement_called:
                self.shutoff()
                break
        self.dep_complete = True
    
    def run_recipe(self):
        self.settings['recipe_running'] = True
        self.settings['recipe_completed'] = False
        self.settings['steps_taken'] = 0
        self.settings['cycles_completed'] = 0
        self.sub = self.settings['subroutine']
        self.times = self.settings['time']
        self.prepurge()
        if self.interrupt_measurement_called:
            self.shutoff()
            return
            #doo something to finish recipe

        self.deposition()

        self.postpurge()
        if self.interrupt_measurement_called:
            self.shutoff()
            return
            #doo something to finish recipe
        
        self.settings['recipe_running'] = False
        self.settings['recipe_completed'] = True
        print('recipe completed')

    def run(self):
        self.run_recipe()
        

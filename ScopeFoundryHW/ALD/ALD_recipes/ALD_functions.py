'''
Created on Feb 21, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
import time

class ALD_routine(Measurement):
    
    name = 'ALD_routine'
    
    def setup(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.mks600 = self.app.hardware['mks_600_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
        
        
        self.MFC_valve_states = {'Open': 'O',
                             'Closed': 'C',
                             'Manual': 'N'}
        
        self.mks600.settings.get_lq('sp_channel').update_value('Open')
        
        self.mks146.settings.get_lq('MFC0_SP').update_value(0)
        state = self.MFC_valve_states['Closed']
        self.mks146.settings.get_lq('MFC0_valve').update_value(state)
        
        self.mks600.settings.get_lq('sp_channel').update_value("A")
    
    def precursor_1_dose(self, flow_sp, width=0.008):
        """argument 'width' has units of seconds"""
        relay = 0
        chamber_pressure = 15e-3 #torr
        
        self.mks600.settings.get_lq('sp_set_value').update_value(chamber_pressure)
        self.mks146.settings.get_lq('MFC0_SP').update_value(flow_sp)
        state = self.MFC_valve_states['Manual']
        self.mks146.settings.get_lq('MFC0_valve').update_value(state)
        print('Changed?', self.mks146.settings['MFC0_SP'], self.mks146.settings['MFC0_valve'])
        
        def pressure_and_flow():
            pressure = self.read_pressure() #torr
            flow = self.mks146.MFC0_read_flow()
            return pressure, flow
        
        pressure, flow = pressure_and_flow()
        print('Waiting for temperature and pressure to reach desired settings.')
        while not (chamber_pressure-(2e-3) < pressure < chamber_pressure+(2e-3)) \
                and not (10 <= flow <= 20):
            pressure, flow = pressure_and_flow()
        else:

            self.relay.relay.send_pulse(relay, 1e3*width)
            print("Pulse sent: precursor dose complete")

    def precursor_purge(self, pressure_sp, temp_sp):
        '''Argument pressure_sp in units of torr,
            temp_sp is in units of degrees C.'''
        self.mks600.settings['sp_channel'] = 'A'
        self.mks600.settings.get_lq('sp_set_value').update_value(pressure_sp)
        self.lovebox.settings['sv_setpoint'] = temp_sp
        pressure = self.read_pressure()
        p_tolerance = 0.0025
        temp = self.lovebox.lovebox.read_temp()
        print('Waiting for temperature and pressure to reach desired settings.')
        while not (pressure_sp-p_tolerance <= pressure <= pressure_sp+p_tolerance) \
                and not (temp_sp+0.1 <= temp <= temp_sp+0.1):
            '''Check pressure and temp until conditions are within desired SP range.'''
            pressure = self.read_pressure()
            temp = self.lovebox.lovebox.read_temp()
        else:
            '''Close MFC if above conditions are met.'''
            state = self.MFC_valve_states['Closed']
            self.mks146.settings.get_lq('MFC0_valve').update_value(state)
            print("Precursor purge complete")
            
    def plasma_stabilization(self, pressure_sp):
        pressure = self.read_pressure()
        p_tolerance = 1e-3
        while not (pressure_sp - p_tolerance <= pressure < pressure + p_tolerance):
            time.sleep(0.5)
        else:
            print("Plasma stabilization complete")
            return
            
    def plasma_dose(self, width, power):
        """Argument 'width' has units of seconds
        power has units of Watts
        """
        print('Plasma dose.')
        self.seren.write_fp(power)
        self.seren.RF_toggle(True)
        time.sleep(width)
        self.seren.RF_toggle(False)
        self.seren.write_fp(0)
        print('Plasma dose finished.')
        
    def plasma_purge(self, pressure_sp=0.015):
        '''Enter pressure_sp in units of torr'''
        flow = self.mks146.MFC0_read_flow()
        self.mks600.settings.get_lq('sp_set_value').update_value(pressure_sp)
        p_tolerance = 0.003
        if flow <= .015:
            print('No flow. Proceeding with plasma purge.')
            pressure = self.read_pressure()
            while not (pressure_sp - p_tolerance <= pressure <= pressure_sp+p_tolerance):
                pressure = self.read_pressure()
                time.sleep(0.5)
            else:
                print('plasma purge while ended')
        else:
            print('Warning, non-zero flow')

    def select_gauge(self, val):
        gauge_range = {'TKP': (1e-3, 1e3),
                  'PKR': (1e-8, 9.999e-4)}
        gauge_select = {'TKP': self.vgc.settings['ch2_pressure_scaled'],
                            'PKR': self.vgc.settings['ch3_pressure_scaled']}
        for k,v in gauge_range.items():
            if (min(v) <= val <= max(v)):
                return gauge_select[k]
            else:   pass
    
    def read_pressure(self):
        '''Reads off PKR for ball park estimate, 
        then decides upon the gauge with the 
        more accurate reading'''
        read = self.vgc.settings['ch3_pressure_scaled']
        selection = self.select_gauge(read)
        return selection
    
    def shutdown(self):
        pass
    
    def ramp_throttle_open(self):
#         self.mks600.switch_sp()
#         self.mks600.write_sp()
        pass 
    
    def run(self):
#         self.seren.serial_toggle(True)

        self.run_count = 0
        self.loops_elapsed = 0
        self.loops = 10
        self.dt = 0.1
        
        ### Use single loop of N number of cycles.
        
        while (self.loops_elapsed <= self.loops) or not self.interrupt_measurement_called:
            self.precursor_1_dose(.8, 0.012) # flow = 10 sccm, pulse_width=0.008 s 
                
            self.precursor_purge(0.04, 25) #pressure = 0.04 torr, temp = 20 C
                
            self.plasma_stabilization(0.010) # pressure = 10 mtorr

            self.plasma_dose(3, 5) #time = 30 s, power = 5 W
            
            self.plasma_purge(0.015) # 15 mtorr
                
            self.run_count += 1
            time.sleep(self.dt)
            self.loops_elapsed += 1
            print("loops_elapsed:", self.loops_elapsed)
        else: 
            self.mks600.settings.get_lq('sp_channel').update_value('Open')
            print('All loops and cycles completed.')
            
        
        
        
        
        
        
        
        
        


















'''
Created on Feb 21, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
import time

class ALD_routine(Measurement):
    
    name = 'ALD_routine'
    
    def __init__(self):
        self.relay = self.app.hardware['ald_relay_hw']
        self.lovebox = self.app.hardware['lovebox']
        self.mks146 = self.app.hardware['mks_146_hw']
        self.mks600 = self.app.hardware['mks_600_hw']
        self.vgc = self.app.hardware['pfeiffer_vgc_hw']
        self.seren = self.app.hardware['seren_hw']
        self.seren.serial_toggle(True)
        
        
        self.MFC_valve_states = {'Open': 'O',
                             'Closed': 'C',
                             'Cancel': 'N'}

    def precursor_1_dose(self, width=0.8):
        """argument 'width' has units of seconds"""
        relay = 0
        chamber_pressure = 15 #mtorr
        
        def pressure_and_flow():
            measure = self.read_pressure()
            pressure = (1000*measure)/(101325/76000) #mtorr
            flow = self.mks146.MFC0_read_flow()
            return pressure, flow
        
        pressure, flow = pressure_and_flow()
        while not (chamber_pressure-1 < pressure < chamber_pressure+1) \
                and not (10 <= flow <= 20):
            pressure, flow = pressure_and_flow()
        else:
            if self.debug_mode:
                print("Pulse sending--", "pressure:", pressure, "> chamber:", chamber_pressure)
            self.relay.relay.send_pulse(relay, 1e3*width)

    def precursor_purge(self, pressure_sp=0.04, temp_sp):
        '''Argument pressure_sp in units of torr,
            temp_sp is in units of degrees C.'''
        self.mks600.write_sp(0.04)
        pressure = self.read_pressure()
        temp = self.lovebox.lovebox.read_temp()
        while not (pressure_sp-0.001 <= pressure <= pressure_sp+0.001) \
                and not (temp_sp+0.1 <= temp <= temp_sp+0.1):
            '''Check pressure and temp until conditions are within desired SP range.'''
            pressure = self.read_pressure()
            temp = self.lovebox.lovebox.read_temp()
        else:
            '''Close MFC if above conditions are met.'''
            state = 'C'
            assert state in self.MFC_valve_states.values()
            self.mks146.write_value(state)
            
    def plasma_stabilization(self, pressure_sp):
        pressure = self.read_pressure()
        p_tolerance = 1e-3
        while not (pressure_sp - p_tolerance <= pressure < pressure + p_tolerance):
            time.sleep(0.5)
        else:
            return
        
    
    def plasma_dose(self, width, power):
        """Argument 'width' has units of seconds
        power has units of Watts
        """
        self.seren.write_fp(power)
        self.seren.RF_toggle(True)
        time.sleep(width)
        self.seren.RF_toggle(False)
        self.seren.write_fp(0)
        
    def plasma_purge(self, pressure_sp=0.015):
        '''Enter pressure_sp in units of torr'''
        flow = self.mks146.MFC0_read_flow()
        p_tolerance = 0.001
        if flow >= .005:
            pressure = self.read_pressure()
            while not (pressure_sp - p_tolerance <= pressure <= pressure_sp+p_tolerance):
                time.sleep(0.5)
        else:
            print('No flow.')

    def select_gauge(self, val):
        gauge_range = {'TKP': (1e-3, 1e3),
                  'PKR': (1e-8, 9.999e-4)}
        gauge_select = {'TKP': self.vgc.vgc.read_ch2_pressure,
                  'PKR': self.vgc.vgc.read_ch3_pressure}
        for k,v in gauge_range.items():
            if (min(v) <= val <= max(v)):
                return gauge_select[k]()
            else:   pass
    
    def read_pressure(self):
        '''Reads off PKR for ball park estimate, 
        then decides upon the gauge with the 
        more accurate reading'''
        read = self.vgc.vgc.read_ch3_pressure()
        selection = self.select_gauge(read)
        return selection
            
        
    def run(self):
        self.run_count = 0
        self.loops_elapsed = 0
        self.loops = 1
        self.total_cycles = 10
        self.dt = 0.1
        while (self.loops_elapsed <= self.loops) or not self.interrupt_measurement_called:
            while not self.interrupt_measurement_called or \
                        (self.run_count <= self.total_cycles):
                self.precursor_1_dose(0.8)
                
                self.precursor_purge(0.04, 20) #temp = 20 C
                
                self.plasma_stabilization(0.010) # pressure = 10 mtorr
    
                self.plasma_dose(30, 5) #time = 30 s, power = 5 W
                
                self.plasma_purge(0.015) # 15 mtorr
                
                self.run_count += 1
                time.sleep(self.dt)
            self.loops_elapsed += 1
        else: 
            print('All loops and cycles completed.')
            
        
        
        
        
        
        
        
        
        


















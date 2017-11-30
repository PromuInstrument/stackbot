'''
Created on Jun 29, 2017

@author: Alan Buckley, Benedikt Ursprung (PowermateMeasureSimple)
'''

'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley
         Benedikt Ursprung (Simple Version)
        

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry.measurement import Measurement
import time



class PowermateMeasureSimple(Measurement):
    
    name = "powermate_measure"

    def setup(self):
        self.devices_num = 2        
        self.data_handler_map = {
                                'z_position': lambda data:self.raw_data_handler_position(data,axis='z'),
                                'y_position': lambda data:self.raw_data_handler_position(data,axis='y'),
                                'x_position': lambda data:self.raw_data_handler_position(data,axis='x'),
                                'shutter': self.raw_data_handler_toggle_shutter,
                                'LED': self.raw_data_handler_LED,
                                 }

        self.dt = 0.05
        self.powermate = self.app.hardware['powermate_hw']
        data_handler_choices = list(self.data_handler_map.keys())

        # LQs for device/datahandler assignment 
        for i in range(self.devices_num):
            self.settings.New(name='pm_{}_data_handler_selector'.format(i), initial=data_handler_choices[i], 
                              dtype=str, choices = data_handler_choices, ro=True)
            getattr(self.settings, 'pm_{}_data_handler_selector'.format(i)).add_listener(self.pm_assignment)      
        
        # Handler specific LQs
        for ax in 'xyz':
            self.settings.New(name='{}_position_scale'.format(ax), initial=10, dtype=float, ro=False)
            self.settings.New(name='{}_position_scale_button_pressed'.format(ax), initial=1, dtype=float, ro=False)
        
        # start/interrupt when powermate hardware is connected/disconnected
        #self.powermate.settings.connected.add_listener(self.cycle)
      
        
    def pm_assignment(self):
        for dev_num in range(self.devices_num):
            handler_func = self.data_handler_map[self.settings['pm_{}_data_handler_selector'.format(dev_num)]]
            self.powermate.set_data_handler(dev_num,handler_func)
            print('pm_assignment:', dev_num,handler_func)
        
        
    def cycle(self):
        if self.powermate.settings.connected.val:
            self.powermate.connect()
            time.sleep(0.05)
            self.start()
        else:
            self.powermate.disconnect()
            self.interrupt()
            
            
    def pre_run(self):
        self.pm_assignment()
        
        
    def run(self):
        try:
            while not self.interrupt_measurement_called:
                time.sleep(0.1)
        finally:
            pass


    def raw_data_handler_position(self, data, axis):
        buttom = bool(data[1])
        wheel = data[2]        
        stageHW = self.app.hardware['attocube_xyz_stage']

        if stageHW.settings.connected.val:
            buttom = bool(data[1])
            wheel = data[2]         
            if not buttom:
                scale = self.settings['{}_position_scale_button_pressed'.format(axis)]
            else:
                scale = self.settings['{}_position_scale'.format(axis)]
    
            if wheel > 1:
                stageHW.settings['{}_target_position'.format(axis)] -= 1*scale
            elif wheel == 1:
                stageHW.settings['{}_target_position'.format(axis)] += 1*scale  
                   
        else:
            print('Warning:', stageHW.settings.name.val, 'is not connected')
            

    def raw_data_handler_toggle_shutter(self,data):
        buttom = bool(data[1])
        #wheel = data[2] 
        if buttom is True:
            lq = self.app.hardware['pololu_servo_hw'].settings.servo2_toggle
            if lq.val:
                lq.update_value(False)
                time.sleep(0.1)
            else:
                lq.update_value(True)
                time.sleep(0.1)
                
                
    def raw_data_handler_LED(self,data):
        buttom = bool(data[1])
        #wheel = data[2] 
        if buttom is True:
            HW = self.app.hardware['tenma_powersupply']
            V = HW.settings['actual_voltage']
            I = HW.settings['actual_current']
            if (V*I)<0.001:
                HW.write_both()
                time.sleep(0.1)
            else:
                HW.zero_both()
                time.sleep(0.1)



            
class PowermateMeasure(Measurement):

    name = "powermate_measure"

    def setup(self):
        """Loads UI into memory from file, connects **LoggedQuantities** to UI elements."""
        self.app
        
        self.dt = 0.05
        self.powermate = self.app.hardware['powermate_hw']
        self.powermate.settings.devices.add_listener(self.cycle)       

    def cycle(self):
        self.interrupt()
        time.sleep(0.11)
        self.start()
            
    def run(self):
        self.powermate.open_active_device()
        self.powermate.set_data_handler()
        try:
            while not self.interrupt_measurement_called:
                time.sleep(0.1)
        finally:
            self.powermate.active_device.close()

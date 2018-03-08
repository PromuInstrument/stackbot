'''
Created on Mar 7, 2018

@author: lab
'''
from ScopeFoundry.hardware import HardwareComponent

from .thorlabs_integrated_stepper_motor_dev import ThorlabsIntegratedStepperMotorDev

class ThorlabsIntegratedStepperMottorHW(HardwareComponent):
    
    name = 'motorized_polarizer'
        
    def setup(self):
        self.settings.New('serial_num', dtype = int, initial = 55000231, ro=True)
        
        self.pos = self.settings.New('position', dtype=float, initial = 0, ro=True)
        self.target_pos = self.settings.New('target_position', dtype=float, initial = 0, ro=False)
        self.steps_per_deg = self.settings.New('steps_per_deg', initial = 12288000/90., dtype=float) #scales device units to deg
        
        self.add_operation('home', self.home)
   
    
    def connect(self):
        serial_number = self.settings['serial_num']
        self.dev = ThorlabsIntegratedStepperMotorDev(dev_num=0, serial_num=serial_number, debug=self.settings['debug_mode'])        
        
        self.pos.connect_to_hardware(read_func=self.read_position_scaled)        
        self.target_pos.connect_to_hardware(write_func = self.move_and_wait_scaled)                               
        self.target_pos.add_listener(self.read_from_hardware)
        
        self.read_from_hardware()
    
        
    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
        
        
    def home(self):
        self.dev.home_and_wait()
        
    def move_and_wait_scaled(self, new_pos):
        self.dev.move_and_wait(int(round(self.steps_per_deg.value*new_pos)))
        #self.read_from_hardware()   

    def read_position_scaled(self):
        return self.dev.read_position() / self.steps_per_deg.value